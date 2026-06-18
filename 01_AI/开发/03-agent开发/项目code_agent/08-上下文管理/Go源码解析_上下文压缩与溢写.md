理论篇讲了两层压缩的设计思路，这里带你走读 Go 版的真实代码，看看每一层在源码里长什么样。

## 模块概览

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `internal/toolresult/state.go` | 56 | `ContentReplacementState` ：记录每个 tool_use_id 的替换决策，跨轮稳定 |
| `internal/toolresult/budget.go` | 372 | Layer 1 三趟裁剪：单条溢写 + 聚合溢写 + 过期裁剪 |
| `internal/toolresult/record.go` | 89 | 决策日志：把替换记录写到 JSONL 文件，resume 时可重建 state |
| `internal/toolresult/reconstruct.go` | 55 | 从磁盘日志重建 `ContentReplacementState` ，用于会话恢复 |
| `internal/compact/compact.go` | 472 | Layer 2 摘要旧消息、保留近期原文：阈值计算、摘要生成、对话重建 |
| `internal/compact/recovery.go` | 227 | 压缩后恢复块：文件快照 + 技能定义 + 工具列表，拼到摘要消息里 |
| `internal/session/session.go` | ~170 | 会话持久化：保存 compact_boundary 记录，resume 时定位恢复点 |
| `internal/llm/anthropic.go` | ~390 | `buildAnthropicMessages` ：连续 user 消息合并，维持 API 交替规则 |

两层代码分属不同的 package。Layer 1 在 `toolresult` ，Layer 2 在 `compact` ，由 [[07-Agent|Agent]] 主循环分别调用，互不依赖。

## 核心类型

### ContentReplacementState

```plain
type ContentReplacementState struct {
    SeenIDs      map[string]struct{}
    Replacements map[string]string
}
```

两本账本。 `SeenIDs` 记录所有见过的 tool\_use\_id（不管最后是替换还是保留）， `Replacements` 只记那些被决定「替换」的 id 和对应的 preview 字符串。一旦某个 id 进了 SeenIDs，决策就冻结了，后续轮次不再重新评估。这个冻结语义是 Prompt Cache 命中率的关键。

### UsageAnchor

```plain
type UsageAnchor struct {
    BaselineTokens int
    AnchorCount    int
    HasUsage       bool
}
```

锚定上一次真实的 API usage。 `BaselineTokens` 是 Anthropic 返回的 input + cache\_read + cache\_creation + output 四项之和， `AnchorCount` 是拿到这个 usage 时的对话长度。后续只对 AnchorCount 之后新增的消息做字符估算，把全局误差压缩到最后一小段增量上。

## 第一层：工具结果预算（toolresult 包）

### 入口函数 Apply

```plain
func Apply(
    conv        *conversation.Manager,
    state       *ContentReplacementState,
    spillDir    string,
    toolSchemas []map[string]any,
) (*conversation.Manager, []Record, error)
```

`Apply` 不修改输入的 conv，而是从头构建一个新的 `conversation.Manager` 返回。这样做有个好处：原始对话历史始终不变，每轮拿同一份原始数据重新跑决策，配合 state 里的冻结记录就能做到前缀稳定。

函数体分三趟（Pass）遍历消息。

### Pass 1：单条溢写

```plain
if len(tr.Content) > SingleResultLimit {
    path, err := writeSpill(spillDir, tr.ToolUseID, tr.Content)
    // ...
    replacement := buildSpillPreview(tr.Content, path)
    state.Replacements[tr.ToolUseID] = replacement
}
```

`SingleResultLimit = 50000` 字符（约 12,500 tokens）。超过这个值的工具结果，内容写磁盘，对话里只留一段预览加文件路径。预览通过 `buildSpillPreview` 生成：取前 1000 字符，加上完整路径，模型需要细节时可以自己 ReadFile。

### Pass 2：聚合溢写

单条都没超标，但一轮里并行调了多个工具，结果加起来超了 `MessageAggregateLimit = 200000` 字符。

```plain
sort.Slice(candidates, func(i, j int) bool {
    return len(candidates[i].content) > len(candidates[j].content)
})
for _, c := range candidates {
    if total <= MessageAggregateLimit { break }
    path, _ := writeSpill(spillDir, c.toolUseID, c.content)
    replacement := buildSpillPreview(c.content, path)
    state.Replacements[c.toolUseID] = replacement
    total -= len(c.content) - len(replacement)
}
```

把候选按大小降序排，从最大的开始存盘，直到总量降到预算以内。挑最大的存盘单位收益最高，能用最少的替换次数把总量压下来。

### Pass 3：过期裁剪

前两趟管的是「太大」，第三趟管的是「太旧」。

```plain
func snipStale(messages []conversation.Message,
    index map[string]ToolUseBlock)
```

从头扫消息，数 assistant 消息（不含 tool\_use 的那种，代表一个完整的对话轮次结束）。最近 `KeepRecentTurns = 10` 轮以内的工具结果保留原样，更老的如果超过 `OldResultSnipChars = 2000` 字符就截断，只留前 2000 字符。

这个裁剪是无状态的，不走 state 冻结。因为它只动「已经被冻结为保留」的结果的尾部，不改替换决策，也不影响前缀稳定性。

### 原子写入 writeSpill

```plain
func writeSpill(dir, toolUseID, content string) (string, error) {
    // ...
    f, err := os.OpenFile(path,
        os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o644)
    if err != nil {
        if os.IsExist(err) {
            return path, nil
        }
        return "", err
    }
    defer f.Close()
    f.WriteString(content)
    return path, nil
}
```

用 `O_EXCL` 原子独占创建。文件已存在就直接返回路径，不覆写。这比先 Stat 再 Write 的方式安全，没有 TOCTOU 竞态窗口。文件名直接用 tool\_use\_id，天然幂等。

## 第二层：摘要旧消息、保留近期原文（compact 包）

### 阈值计算

```plain
func computeCompactThreshold(
    contextWindow, maxOutput int, manual bool,
) int {
    reserve := summaryOutputReserve  // 20000
    if maxOutput > 0 && maxOutput < reserve {
        reserve = maxOutput
    }
    effectiveWindow := contextWindow - reserve
    margin := autoCompactSafetyMargin  // 13000
    if manual {
        margin = manualCompactSafetyMargin  // 3000
    }
    return effectiveWindow - margin
}
```

200K 窗口下：有效窗口 = 200000 − 20000 = 180000，自动触发线 = 180000 − 13000 = 167000。手动 /compact 的触发线更激进：180000 − 3000 = 177000。

### Token 估算：锚定 + 增量

```plain
func ComputeUsedTokens(
    messages []conversation.Message,
    anchor UsageAnchor,
) int {
    if !anchor.HasUsage {
        return EstimateTokens(messages)
    }
    if anchor.AnchorCount > len(messages) {
        return EstimateTokens(messages)
    }
    return anchor.BaselineTokens +
        EstimateTokens(messages[anchor.AnchorCount:])
}
```

有锚点时，历史的绝大部分用 API 返回的精确值，只对最后一小段增量做字符估算。没锚点（首轮）就全量估算。这让 13K 的安全余量足够覆盖估算误差。

### ManageContext：软硬双阈值

```plain
func ManageContext(
    ctx context.Context,
    conv *conversation.Manager,
    client llm.Client,
    workDir, sessionID string,
    contextWindow, maxOutput int,
    tracking *AutoCompactTrackingState,
    recovery *RecoveryState,
    toolSchemas []map[string]any,
    anchor UsageAnchor,
) (string, error) {
    tokens := ComputeUsedTokens(conv.GetMessages(), anchor)
    if tokens < computeCompactThreshold(
        contextWindow, maxOutput, false) {
        return "", nil  // 没到软阈值，不动
    }
    if tokens >= computeCompactThreshold(
        contextWindow, maxOutput, true) {
        return ForceCompact(...)  // 突破硬阈值，绕过熔断
    }
    if tracking.ConsecutiveFailures >= 3 {
        return "", nil  // 熔断
    }
    return autoCompact(...)
}
```

三层判断：先看有没有达到软阈值（167K），没达到就不动。达到了再看有没有突破硬阈值（177K），突破了就绕过熔断器强制压缩。在软硬之间的区域，走正常流程并受熔断器保护。

### 拆分前缀与尾部

```plain
keepStart := computeKeepStartIndex(messages)
prefix := messages[:keepStart]
keep := messages[keepStart:]
```

`computeKeepStartIndex` 从尾部往回走，累积 token 数。满足 `keepRecentTokens = 10000` 或 `minKeepMessages = 5` 任一条件就停（取先到的那个），但不超过 `keepMaxTokens = 40000` 的上限。如果边界落在 tool\_result 上，往前退到对应的 tool\_use，确保不拆断配对。

prefix 交给 LLM 生成摘要，keep 原样保留。

### 摘要生成

只把 prefix 序列化给 LLM，用 `summarySystemPrompt` 要求两阶段输出（analysis + summary）。analysis 是草稿， `formatCompactSummary` 会剥掉它，只留 summary 正文。

### 对话重建

```plain
content := "本次会话延续自之前的对话，" +
    "因上下文空间不足进行了压缩。" +
    "以下是早期对话的摘要：\n\n" + finalSummary
if len(keep) > 0 {
    content += "\n\n近期消息已原样保留。"
}
if sessionID != "" && workDir != "" {
    content += fmt.Sprintf(
        "\n\n如果你需要压缩前的具体细节"+
        "（代码片段、报错信息等），"+
        "请用 ReadFile 读取完整会话记录：%s",
        session.SessionFilePath(workDir, sessionID))
}
if attachment := BuildRecoveryAttachment(
    recovery, toolSchemas); attachment != "" {
    content += "\n\n---\n\n" + attachment
}

compacted := conversation.NewManager()
compacted.AddUserMessage(content)
compacted.AppendMessages(keep)
```

整个压缩后的对话就两部分：一条 user 消息（摘要 + 会话记录路径 + 恢复块），加上保留的近期原文。没有 assistant 确认消息。

`BuildRecoveryAttachment` 拼接了三块恢复内容：最近读过的 5 个文件快照（每个最多 5000 tokens）、之前用过的 Skill 定义（总预算 25000 tokens）、当前可用工具列表。都在同一条 user 消息里，用 `---` 分隔。

由于没有 assistant 消息隔开，摘要（user）和 keep tail 的第一条（如果恰好也是 user）会形成连续 user 消息。这由 `buildAnthropicMessages` 在序列化时自动合并，不需要压缩模块操心。

### 会话边界持久化

```plain
session.SaveCompactBoundary(
    workDir, sessionID, finalSummary, keepRecords)
```

把纯文本摘要和 keep tail 写进 session JSONL 文件，角色标为 `system` ，type 标为 `compact_boundary` 。Resume 时 `FindLastCompactBoundary` 找到最后一条 boundary，从它开始重建对话，而不是回放全部历史。

## 连续 User 消息合并

```plain
// internal/llm/anthropic.go
} else {
    canMerge := false
    if n := len(result); n > 0 {
        prev := result[n-1]
        if prev.Role == "user" &&
            prev.Content[0].OfToolResult == nil {
            canMerge = true
        }
    }
    if canMerge {
        result[len(result)-1].Content = append(
            result[len(result)-1].Content,
            anthropic.NewTextBlock(m.Content))
    } else {
        result = append(result,
            anthropic.NewUserMessage(
                anthropic.NewTextBlock(m.Content)))
    }
}
```

Anthropic API 要求 user/assistant 严格交替。压缩后摘要（user）和 keep tail 的首条（可能也是 user）会相邻。这段逻辑在序列化时检查：如果前一条也是 user 且不是 tool\_result，就把当前消息的文本块追加到前一条里，而不是新建一条。合并后发给 API 的消息列表始终满足交替规则。

## 小结

| 设计要点 | Go 实现 |
| --- | --- |
| 两层架构 | Layer 1 在 `toolresult.Apply` （Agent 调用），Layer 2 在 `compact.ManageContext` （独立触发） |
| 决策冻结 | `ContentReplacementState` 的 SeenIDs + Replacements，一旦见过永不改判 |
| 溢写原子性 | `writeSpill` 用 `O_EXCL` 独占创建，文件名是 tool_use_id，天然幂等 |
| 阈值公式 | `effectiveWindow − margin` ，绝对值而非百分比，配合锚定增量估算 |
| 对话重建 | 一条 user（摘要 + 恢复块）+ 保留的尾部原文，无 assistant ack |
| 连续 user 合并 | `buildAnthropicMessages` 自动合并相邻纯文本 user 消息 |
| 边界持久化 | session JSONL 追加 compact_boundary 记录，resume 跳过已压缩前缀 |