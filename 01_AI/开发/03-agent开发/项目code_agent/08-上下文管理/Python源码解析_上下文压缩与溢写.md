理论篇讲了两层压缩的设计思路，这里走读 Python 版 MewCode 的真实代码。Python 版把两层都放在一个文件里，风格非常 Pythonic。

## 模块概览

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `mewcode/context/manager.py` | ~850 | 两层[[理论学习_上下文压缩与_Token_管理|上下文压缩]]全在这：Layer 1 三趟裁剪 + Layer 2 摘要旧消息、保留近期原文 + 恢复块渲染 |
| `mewcode/serialization.py` | ~100 | `build_anthropic_messages` ：消息序列化和连续 user 消息合并 |
| `mewcode/memory/session.py` | ~300 | 会话持久化：compact_boundary 记录的读写和 resume 重建 |
| `mewcode/agent.py` | ~1000 | [[07-Agent|Agent]] 主循环：调用 `apply_tool_result_budget` + `auto_compact` ，线程化 `transcript_path` |

两层逻辑全在 `context/manager.py` 一个文件里，约 850 行。

## 核心常量

```plain
SINGLE_RESULT_CHAR_LIMIT = 50_000
AGGREGATE_CHAR_LIMIT     = 200_000
OLD_RESULT_SNIP_CHARS    = 2_000
KEEP_RECENT_TURNS        = 10

SUMMARY_OUTPUT_RESERVE      = 20_000
AUTO_COMPACT_SAFETY_MARGIN  = 13_000
MANUAL_COMPACT_SAFETY_MARGIN = 3_000

KEEP_RECENT_TOKENS = 10_000
MIN_KEEP_MESSAGES  = 5
KEEP_MAX_TOKENS    = 40_000
```

上面四个管 Layer 1，中间三个管 Layer 2 的阈值，最后三个管「保留多少尾部原文」。

## 第一层：工具结果预算

### persist\_tool\_result：原子独占写入

```plain
def persist_tool_result(
    tool_use_id: str, content: str, session_dir: Path
) -> Path:
    file_path = session_dir / f"{tool_use_id}.txt"
    try:
        fd = os.open(str(file_path),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
    except FileExistsError:
        pass
    return file_path
```

`O_EXCL` 是 POSIX 的原子独占创建标志，文件已存在就抛 `FileExistsError` ，直接跳过。文件名用 tool\_use\_id，天然幂等。三个语言版本里 Python 最早用上这个做法。

### apply\_tool\_result\_budget

```plain
def apply_tool_result_budget(
    conversation, session_dir, state
) -> tuple[bool, list]:
```

函数接收一个 `ContentReplacementState` （ `seen_ids` + `replacements` 双账本，记录每个 tool\_use\_id 的替换决策），三趟处理：

**Pass 1** ：遍历所有 tool\_result，超过 `SINGLE_RESULT_CHAR_LIMIT = 50000` 字符的写盘留预览。已经在 `seen_ids` 里的跳过，不重新评估。

**Pass 2** ：同一条消息内所有 tool\_result 加起来超过 `AGGREGATE_CHAR_LIMIT = 200000` ，按大小降序逐个溢写，直到总量降到预算以内。

**Pass 3** ：过期裁剪。最近 10 轮以内的保留原样，更老的超过 2000 字符的截断，前面加 `<snipped>` 标签。检查时会跳过已经被 `<persisted-output>` 标记替换过的结果。

函数构建新的消息列表返回，不修改输入的 conversation。state 的冻结语义保证前缀稳定，Prompt Cache 命中。

## 第二层：摘要旧消息、保留近期原文

### auto\_compact

```plain
async def auto_compact(
    conversation, client, context_window,
    session_dir, protocol, manual, breaker,
    recovery, tool_schemas, transcript_path
):
```

流程：估算当前 token 数，跟 `effective_window - margin` 比较。超了就拆分 prefix 和 keep tail（从尾部往回走，按 token 预算选出要保留的近期消息），只把 prefix 发给 LLM 生成摘要。

### build\_compact\_messages

```plain
def build_compact_messages(
    summary: str,
    attachment: str = "",
    has_keep_tail: bool = False,
    transcript_path: str = "",
) -> list[Message]:
    content = ("本次会话延续自之前的对话，"
        "因上下文空间不足进行了压缩。"
        "以下是早期对话的摘要：\n\n" + summary)
    if has_keep_tail:
        content += "\n\n近期消息已原样保留。"
    if transcript_path:
        content += (f"\n\n如果你需要压缩前的具体细节"
            f"（代码片段、报错信息等），"
            f"请用 ReadFile 读取完整会话记录："
            f"{transcript_path}")
    if attachment:
        content += "\n\n---\n\n" + attachment
    return [Message(role="user", content=content)]
```

只返回一条 user 消息。摘要、「近期消息已原样保留」提示、会话记录路径、恢复块全拼在一起。没有 assistant 确认消息。

调用方这样用：

```plain
new_messages = build_compact_messages(
    summary,
    attachment=attachment,
    transcript_path=str(transcript_path) if transcript_path else "",
    has_keep_tail=len(keep_tail) > 0,
)
new_messages = new_messages + list(keep_tail)
```

摘要消息加上保留的尾部原文，替换掉原来的全部对话。

### 恢复块

`build_recovery_attachment` 拼接三块内容：最近 5 个文件快照（每个 5000 tokens）、Skill 定义（总预算 25000 tokens）、工具列表。用 `---` 分隔，全部在同一条 user 消息里。

### transcript\_path 的来源

`Agent` 类在初始化时从 `app.py` 接收 `session_id` ，通过一个 `_transcript_path` 属性计算出 `.mewcode/sessions/{session_id}.jsonl` 的完整路径，传给 `auto_compact` 。模型如果需要压缩前的原始细节，可以 ReadFile 这个文件。

## 连续 User 消息合并

```plain
# serialization.py — build_anthropic_messages
else:
    if (
        m.role == "user"
        and result
        and result[-1]["role"] == "user"
        and isinstance(result[-1]["content"], str)
    ):
        result[-1]["content"] += "\n" + m.content
    else:
        result.append({"role": m.role, "content": m.content})
```

压缩后摘要（user）和 keep tail 首条（可能也是 user）会相邻。这段逻辑检查：如果前一条也是 user 且是纯文本（不是 `list` 类型的 tool\_result），就用 `\n` 拼接。不会合并到 tool\_result 类型的 user 消息上。

## 会话边界持久化

session.py 里的 `records_to_messages` 在遇到 `COMPACT_BOUNDARY` 类型的记录时，用同样的中文 framing 重建摘要消息：

```plain
if record.type == RecordType.COMPACT_BOUNDARY:
    summary, keep = parse_compact_boundary(record)
    framing = ("本次会话延续自之前的对话，"
        "因上下文空间不足进行了压缩。"
        "以下是早期对话的摘要：\n\n" + summary)
    if keep:
        framing += "\n\n近期消息已原样保留。"
    messages.append(Message(role="user", content=framing))
    messages.extend(keep)
```

Resume 时找到最后一条 boundary，从它开始重建，不回放全部历史。

## 小结

| 设计要点 | Python 实现 |
| --- | --- |
| 两层架构 | 全在 `context/manager.py` ， `apply_tool_result_budget` + `auto_compact` |
| 决策冻结 | `ContentReplacementState` 的 `seen_ids` + `replacements` ，跨轮稳定 |
| 溢写原子性 | `persist_tool_result` 用 `O_EXCL` ， `FileExistsError` 跳过 |
| 阈值公式 | `effective_window − margin` ，绝对值而非百分比 |
| 对话重建 | `build_compact_messages` 返回一条 user，加 keep tail，无 assistant ack |
| 连续 user 合并 | `build_anthropic_messages` 合并相邻纯文本 user 消息 |
| 边界持久化 | session JSONL 追加 `COMPACT_BOUNDARY` 记录，resume 重建 |