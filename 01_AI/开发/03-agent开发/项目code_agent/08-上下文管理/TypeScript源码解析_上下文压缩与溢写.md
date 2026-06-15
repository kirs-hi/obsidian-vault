# TypeScript源码解析：上下文压缩与溢写

走读 MewCode 的上下文管理代码，看「工具结果预算（Layer 1）」和「摘要旧消息、保留近期原文（Layer 2）」这两层压缩怎么实现。

## 模块概览

的上下文管理代码分布在两个目录里。Layer 1（工具结果预算）在 `src/toolresult/` ，Layer 2（摘要压缩）在 `src/compact/` 。两层各管各的，Agent Loop 先调 Layer 1 再调 Layer 2。

| 文件 | 职责 |
| --- | --- |
| `toolresult/state.ts` | 决策冻结状态：seenIds Set + replacements Map |
| `toolresult/budget.ts` | Layer 1 三趟处理：单条溢写、聚合溢写、过期裁剪 |
| `toolresult/record.ts` | 决策记录的批量持久化 |
| `toolresult/reconstruct.ts` | 从消息列表重建 ConversationManager |
| `compact/compact.ts` | Layer 2 主逻辑：阈值计算、token 估算、摘要生成、对话重建 |
| `compact/recovery.ts` | 恢复块：文件快照、Skill 定义、工具列表 |

辅助模块方面，连续 user 消息的合并放在 `src/llm/anthropic.ts` 的消息序列化逻辑里。会话持久化（compact boundary）由 `doCompact` 返回 `CompactResult` 里的 `boundary` 字段，session 层拿到后自行写盘。

整体最精简覆盖全部功能。

## 核心常量

### Layer 1 常量

```plain
const SINGLE_RESULT_LIMIT = 50000;
const MESSAGE_AGGREGATE_LIMIT = 200000;
const OLD_RESULT_SNIP_CHARS = 2000;
const KEEP_RECENT_TURNS = 10;
```

四个常量的含义：50000 是单条工具结果的存盘阈值，200000 是聚合上限，2000 是过期裁剪的保留长度，10 是保护窗口。

### Layer 2 常量

```plain
const SUMMARY_OUTPUT_RESERVE = 20000;
const AUTO_COMPACT_SAFETY_MARGIN = 13000;
const MANUAL_COMPACT_SAFETY_MARGIN = 3000;
const KEEP_RECENT_TOKENS = 10000;
const MIN_KEEP_MESSAGES = 5;
const KEEP_MAX_TOKENS = 40000;
```

有效窗口 = 上下文窗口 - min(maxOutput, 20000)，自动触发线 = 有效窗口 - 13000，手动 = 有效窗口 - 3000。尾部保留预算 10000 tokens / 5 条消息 / 上限 40000 tokens。

还定义了 `MIN_COMPACT_PREFIX = 2` ：如果待摘要的前缀不到 2 条消息，跳过压缩。

## 核心类型

### ContentReplacementState（决策冻结）

```plain
export class ContentReplacementState {
 private seenIds = new Set<string>();
 private replacements = new Map<string, string>();

 record(toolUseId: string, original: string, replaced: string): void {
 this.seenIds.add(toolUseId);
 if (original !== replaced) {
 this.replacements.set(toolUseId, replaced);
 }
 }
}
```

的实现思路是把操作封装进 state 的方法里。 `record` 方法同时处理「记录已见」和「记录替换」：如果 original 和 replaced 不同，就存入 replacements；相同则只加 seenIds。调用方不需要直接操作 seenIds 和 replacements，减少了出错的可能。

冻结语义相同：一旦某个 id 进了 seenIds，决策永远不变。

`has(toolUseId)` 检查是否见过， `getReplacement(toolUseId)` 获取替换内容（返回 undefined 表示未替换）。 `clone()` 创建独立副本用于 fork。

### UsageAnchor（Token 锚点）

```plain
export interface UsageAnchor {
 baselineTokens: number;
 anchorCount: number;
}
```

`baselineTokens` 是上次 API 返回的精确 token 数（input + cache\_read + cache\_creation + output）， `anchorCount` 是锚点时刻的消息数量。

锚定的意义：避免每轮全量估算。只对 anchorCount 之后新增的消息做字符估算，误差压缩在最后一小段增量上。

## 第一层：工具结果预算

### 入口函数

```plain
export function applyBudget(
 messages: Message[],
 workDir: string,
 state: ContentReplacementState
): Message[] {
```

接收消息数组和 state，返回新的消息数组。原始 messages 不被修改（每条消息都 `{ ...msg }` 浅拷贝）。

的 `applyBudget` 比较紧凑，三趟处理揉在一个循环里，没有明确分成独立的 Pass 1/2/3。

### Pass 1：单条溢写

对每条消息的 toolResults 逐个检查。先看 state 里有没有： `getReplacement` 返回非 undefined 就直接用缓存的 preview。

```plain
const existing = state.getReplacement(tr.toolUseId);
if (existing !== undefined) {
 return { ...tr, content: existing };
}
if (content.length > SINGLE_RESULT_LIMIT) {
 const spillPath = writeSpill(workDir, tr.toolUseId, content);
 content = buildSpillPreview(content, spillPath);
 state.record(tr.toolUseId, tr.content, content);
}
```

超过 50000 字符的调 `writeSpill` 存盘，然后用 `buildSpillPreview` 生成预览。 `state.record` 同时标记已见和记录替换。

```plain
function buildSpillPreview(content: string, spillPath: string): string {
 const sizeKB = Math.floor(content.length / 1024);
 const preview = content.slice(0, PREVIEW_CHARS);
 // 格式：<persisted-output>...预览...</persisted-output>

}
```

预览格式是 `<persisted-output>` 标签包裹，包含大小、路径、前 2KB 内容。

### Pass 2：聚合溢写

的 Pass 2 在 Pass 1 和 Pass 3 之后执行（代码顺序上是 Pass 1 > Pass 3 > Pass 2）。先算这条消息所有 toolResult 的总长度，超过 200000 就按大小降序排，从最大的开始存盘。

```plain
let totalLen = newResults.reduce((sum, r) => sum + r.content.length, 0);
if (totalLen > MESSAGE_AGGREGATE_LIMIT) {
 const sorted = [...newResults].sort(
 (a, b) => b.content.length - a.content.length
 );
 for (const r of sorted) {
 if (totalLen <= MESSAGE_AGGREGATE_LIMIT) break;
 // 存盘并更新 totalLen
 }
}
```

策略一样：挑最大的存盘，单位收益最高。

### Pass 3：过期裁剪

把过期裁剪揉在 Pass 1 的循环里，通过 `isRecent` 标记判断当前消息是否在保护窗口内。

```plain
const isRecent = mi >= messages.length - KEEP_RECENT_TURNS * 2;
if (!isRecent && content.length > OLD_RESULT_SNIP_CHARS) {
 const snipped = `${content.slice(0, OLD_RESULT_SNIP_CHARS)}\n[Stale output snipped: ${content.length} chars]`;
 state.record(tr.toolUseId, tr.content, snipped);
 content = snipped;
}
```

一个值得注意的设计选择：把裁剪后的结果也存进了 state（ `state.record` ），裁剪决策一旦做出就被冻结。这样做更稳定，但也意味着一个结果一旦被裁剪就永远是裁剪状态，不会因为轮次推移而变化。

另一个值得注意的地方是 `isRecent` 的计算方式：TS 用 `messages.length - KEEP_RECENT_TURNS * 2` （消息数乘 2 近似为轮数），而不是按真实的 assistant 无 tool\_use 消息计数。这个近似在工具密集场景下会把更多消息标记为「recent」，保护窗口偏大。

### 原子写入 writeSpill

```plain
function writeSpill(workDir: string, toolUseId: string, content: string): string {
 const dir = spillDir(workDir);
 mkdirSync(dir, { recursive: true });
 const path = join(dir, toolUseId);
 try {
 writeFileSync(path, content, { encoding: "utf-8", flag: "wx" });
 } catch (e: any) {
 if (e.code !== "EEXIST") throw e;
 }
 return path;
}
```

Node.js 的 `flag: "wx"` 表示独占创建，文件已存在时抛出 EEXIST 错误。代码捕获 `e.code === "EEXIST"` 静默跳过。文件名用 tool\_use\_id，天然幂等。

## 第二层：摘要旧消息、保留近期原文（Auto-Compact）

### 阈值计算

```plain
export function computeCompactThreshold(
 contextWindow: number,
 maxOutput: number,
 manual = false
): number {
 const effective = contextWindow - Math.min(maxOutput, SUMMARY_OUTPUT_RESERVE);
 const margin = manual ? MANUAL_COMPACT_SAFETY_MARGIN : AUTO_COMPACT_SAFETY_MARGIN;
 return effective - margin;
}
```

200K 窗口下自动触发线 167000，手动 177000。安全余量是固定值不是百分比，因为它保护的是单轮波动，跟窗口总量无关。

### Token 估算：锚定 + 增量

```plain
export function currentContextTokens(
 conv: ConversationManager,
 anchor: UsageAnchor | null
): number {
 if (!anchor) return estimateTokens(conv);
 const messages = conv.getMessages();
 const start = Math.min(anchor.anchorCount, messages.length);
 return anchor.baselineTokens + estimateMessages(messages.slice(start));
}
```

有锚点时用精确基准加增量估算，没锚点时全量估算。字符估算用 `totalChars / 3.5` （ `CHARS_PER_TOKEN = 3.5` ）。

### ManageContext 入口：软硬双阈值 + 熔断

```plain
export async function manageContext(
 conv, client, contextWindow, maxOutput,
 trackingState, recoveryState, toolSchemaNames,
 anchor, sessionFilePath
): Promise<CompactResult> {
 const tokens = currentContextTokens(conv, anchor);
 const autoThreshold = computeCompactThreshold(contextWindow, maxOutput);
 const hardBlock = computeCompactThreshold(contextWindow, maxOutput, true);
 if (tokens < autoThreshold) {
 return { compacted: false, message: "" };
 }
 const forced = tokens >= hardBlock;
 if (!forced && trackingState.consecutiveFailures >= 3) {
 return { compacted: false, message: "... circuit breaker ..." };
 }
```

三层判断：没到软阈值不动；软硬之间检查熔断器（3 次连续失败就不再尝试）；突破硬阈值绕过熔断器强制压缩。

### 拆分前缀与尾部

```plain
export function computeKeepStartIndex(messages: Message[]): number {
 let keepTokens = 0, keepCount = 0, keepStart = messages.length;
 for (let i = messages.length - 1; i >= 0; i--) {
 const t = estimateOne(messages[i]);
 if (keepCount > 0 && keepTokens + t > KEEP_MAX_TOKENS) break;
 keepStart = i;
 keepTokens += t;
 keepCount++;
 if (keepTokens >= KEEP_RECENT_TOKENS || keepCount >= MIN_KEEP_MESSAGES) break;
 }
 keepStart = backUpPastToolUse(messages, keepStart);
 return keepStart;
}
```

从尾部往回走，满足 10000 tokens 或 5 条消息任一条件就停，上限 40000 tokens。

把配对保护逻辑抽成了独立函数 `backUpPastToolUse` ，实现更精确：它收集 keepStart 消息里的所有 tool\_use\_id，然后往前找到包含对应 tool\_use 的 assistant 消息。

```plain
function backUpPastToolUse(messages: Message[], keepStart: number): number {
 if (!hasToolResult(messages[keepStart])) return keepStart;
 const ids = new Set(
 (messages[keepStart].toolResults ?? []).map((tr) => tr.toolUseId)
 );
 for (let i = keepStart - 1; i >= 0; i--) {
 if (m.role === "assistant" && m.toolUses?.some(tu => ids.has(tu.toolUseId))) {
 return i;
 }
 }
 return keepStart;
}
```

### 摘要生成

只把 messages[0:keepStart] 序列化成文本发给 LLM。Prompt 要求先 `<analysis>` 再 `<summary>` 。调用时传空的 tools 数组（ `client.stream(summaryConv, [])` ），模型看不到工具定义。

用正则提取 `<summary>` 内容：

```plain
const summaryMatch = summaryText.match(/<summary>([\s\S]*?)<\/summary>/);
const summary = summaryMatch ? summaryMatch[1].trim() : summaryText;
```

没匹配到标签就退化为使用整个输出。

### 对话重建

```plain
let summaryContent = "本次会话延续自之前的对话，因上下文空间不足进行了压缩。" +
 "以下是早期对话的摘要：\n\n" + summary;
if (toKeep.length > 0) {
 summaryContent += "\n\n近期消息已原样保留。";
}
conv.replaceWithCompacted(summaryContent, toKeep);
```

压缩后的结构：一条 user 消息（摘要 + 近期消息提示 + 会话记录路径 + 恢复块）加上保留的尾部原文。没有 assistant 确认消息。

`replaceWithCompacted` 是 ConversationManager 上的方法，清空内部 history，加入摘要 user 消息，再追加 keep tail。

### 恢复块（Recovery Attachment）

```plain
buildRecoveryAttachment(toolSchemaNames: string[]): string {
 const sections: string[] = [];
 const recentFiles = this.snapshotFiles();
 if (recentFiles.length > 0) {
 sections.push("## Recently Read Files\n");
 for (const f of recentFiles) {
 const preview = f.content.length > 2000
 ? f.content.slice(0, 2000) + "\n[truncated]" : f.content;
 sections.push(`### ${f.path}\n\`\`\`\n${preview}\n\`\`\``);
 }
 }
```

的恢复块嵌在 `RecoveryState` 类的方法里。三部分内容：文件快照、Skill 定义、工具列表。

的工具列表比较简化：只接收 `toolSchemaNames: string[]` （名称列表），而不是完整的 schema 对象。所以工具段落只有名称，没有描述。

文件截断比较简化：硬切 2000 字符加 `[truncated]` ，没有用 token 预算做精确控制。Skill 也是硬切 500 字符。这些简化不影响核心功能，但恢复的上下文细节会少一些。

`RecoveryState` 用 `Map` 存储文件和 Skill 记录，按 path/name 去重，只保留最新的。TS 是单线程的，不需要锁。

## 连续 User 消息合并

合并逻辑在 `src/llm/anthropic.ts` 的消息序列化里：

```plain
let canMerge = false;
if (result.length > 0) {
 const prev = result[result.length - 1];
 if (prev.role === "user" && Array.isArray(prev.content) &&
 prev.content[0].type !== "tool_result") {
 canMerge = true;
 }
}
if (canMerge) {
 (prev.content as Anthropic.TextBlockParam[]).push({
 type: "text", text: m.content,
 });
}
```

Anthropic API 要求 user/assistant 严格交替。压缩后摘要（user）和 keep tail 的首条消息（可能也是 user）会相邻，这段逻辑把它们合并。合并条件：前一条是 user，且首个 content block 不是 tool\_result 类型。只合并纯文本 user 消息。

## 被动自愈：紧急压缩

```plain
if (e instanceof ContextTooLongError) {
 try {
 const result = await forceCompact(
 this.conversation, this.client,
 this.recoveryState, toolSchemaNames, this.sessionFilePath
 );
 this.usageAnchor = null;
 yield {
 type: "compact",
 message: "Auto-compacted due to context length: " + result.message,
 boundary: result.boundary,
 };
 continue; // 重试原来的请求
 }
}
```

Agent Loop 在捕获 `ContextTooLongError` 后调用 `forceCompact` ，跳过所有阈值判定和熔断器直接压缩。压缩成功后把 `usageAnchor` 清零（旧锚点已经无意义），yield 一个 compact 事件，然后 continue 重试。

自动压缩是预防，紧急压缩是治疗。

## 会话边界持久化

`doCompact` 返回的 `CompactResult` 里带有 `boundary` 字段：

```plain
const keep = toKeep
 .filter(m => (m.role === "user" || m.role === "assistant") && m.content)
 .map(m => ({ role: m.role, content: m.content }));
return {
 compacted: true,
 message: `Compacted ${toSummarize.length} messages into summary...`,
 boundary: { summary, keep },
};
```

session 层拿到 boundary 后追加 compact\_boundary 记录到 JSONL 文件。keep tail 只保留有内容的 user/assistant 消息的 role + content，没有 tool blocks。

Resume 时找到最后一条 boundary，从它开始重建对话。把 session 写操作解耦出去了，compact 模块只负责生成 boundary payload，不直接写文件。

## 小结

| 设计决策 | TS 实现方式 |
| --- | --- |
| 两层架构 | toolresult 目录（Layer 1）和 compact 目录（Layer 2）分离 |
| 决策冻结 | ContentReplacementState class，Set + Map，record 方法封装 |
| 溢写原子性 | writeFileSync + flag "wx"（独占创建），EEXIST 静默跳过 |
| 阈值公式 | effectiveWindow - safetyMargin，固定值不是百分比 |
| Token 估算 | UsageAnchor interface + currentContextTokens 锚定增量 |
| 对话重建 | replaceWithCompacted 一步完成摘要 + keep tail |
| 连续消息合并 | anthropic.ts 序列化时合并连续纯文本 user 消息 |
| 边界持久化 | 返回 CompactResult.boundary 让 session 层自行写盘 |

> 更新: 2026-06-08 14:29:06  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/rg635tag1ultbhh6](https://www.yuque.com/tianming-uvfnu/gmmfad/rg635tag1ultbhh6)