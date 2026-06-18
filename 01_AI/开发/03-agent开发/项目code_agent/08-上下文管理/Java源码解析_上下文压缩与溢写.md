理论篇讲了两层压缩的设计思路，这里走读 Java 版 MewCode 的真实代码。Java 版把两层逻辑都放在一个类里，结构紧凑。

## 模块概览

| 文件 | 职责 |
| --- | --- |
| `compact/ContextCompactor.java` | 两层[[理论学习_上下文压缩与_Token_管理|上下文压缩]]全在这：Layer 1 溢写裁剪 + Layer 2 摘要旧消息、保留近期原文，外加熔断、手动入口和恢复块渲染 |
| `llm/AnthropicClient.java` | `buildMessages` + `mergeConsecutiveSameRole` ：消息序列化和连续同角色消息合并 |
| `session/SessionManager.java` | 会话持久化：保存 compact_boundary 记录，resume 时定位恢复点 |

`ContextCompactor` 一个类包办了两层逻辑，常量、溢写、裁剪、摘要、恢复块渲染都在里面。

## 核心常量

```plain
private static final int SINGLE_RESULT_LIMIT    = 50_000;
private static final int MESSAGE_AGGREGATE_LIMIT = 200_000;
private static final int OLD_RESULT_SNIP_CHARS   = 2_000;
private static final int KEEP_RECENT_TURNS       = 10;

private static final int SUMMARY_OUTPUT_RESERVE      = 20_000;
private static final int AUTO_COMPACT_SAFETY_MARGIN   = 13_000;
private static final int MANUAL_COMPACT_SAFETY_MARGIN = 3_000;
```

上面四个管 Layer 1（单条 50K、聚合 200K、过期截断 2K、最近 10 轮保护），下面三个管 Layer 2（摘要输出预留 20K、自动安全余量 13K、手动安全余量 3K）。

## 第一层：溢写与裁剪

### offloadAndSnip

```plain
static String offloadAndSnip(
    ConversationManager conv, String workDir)
```

Java 版的 Layer 1 **直接修改** `conv` 的消息列表（通过 `getMessagesMutable()` ），不构建新的 Manager。这意味着替换决策不跨轮持久化，每轮都是对当前对话重新扫一遍。

遍历所有消息的 tool\_result，两趟处理：

**单条溢写** ：结果超过 `SINGLE_RESULT_LIMIT = 50000` 字符，写磁盘留预览。

**聚合溢写** ：单条消息内所有 tool\_result 加起来超过 `MESSAGE_AGGREGATE_LIMIT = 200000` ，从最大的开始溢写（不过 Java 版用的是遍历而非排序，跳过 ≤200 字符的小结果）。

之后再跑一趟 **过期裁剪** ：最近 `KEEP_RECENT_TURNS * 3` 条消息之前的 tool\_result，超过 2000 字符的截断。

### writeSpill：原子独占创建

```plain
private static Path writeSpill(
    String spillDir, String toolUseId, String content) {
    try {
        Path dir = Path.of(spillDir);
        Files.createDirectories(dir);
        Path file = dir.resolve(toolUseId);
        Files.writeString(file, content,
            StandardOpenOption.CREATE_NEW,
            StandardOpenOption.WRITE);
        return file;
    } catch (FileAlreadyExistsException e) {
        return Path.of(spillDir).resolve(toolUseId);
    } catch (IOException e) {
        return null;
    }
}
```

`CREATE_NEW` 是 Java NIO 的原子独占创建，等价于 POSIX 的 `O_EXCL` 。文件已存在就抛 `FileAlreadyExistsException` ，捕获后直接返回路径。文件名用 toolUseId，天然幂等。

## 第二层：摘要旧消息、保留近期原文

### 阈值与入口

```plain
private static int computeCompactThreshold(
    int contextWindow, int maxOutput, boolean manual) {
    int reserve = SUMMARY_OUTPUT_RESERVE;
    if (maxOutput > 0 && maxOutput < reserve)
        reserve = maxOutput;
    int effectiveWindow = contextWindow - reserve;
    int margin = manual
        ? MANUAL_COMPACT_SAFETY_MARGIN
        : AUTO_COMPACT_SAFETY_MARGIN;
    return effectiveWindow - margin;
}
```

`manage()` 方法是公共入口：先跑 Layer 1，再检查 token 数是否超过软阈值（167K）。超了就进 Layer 2，如果突破硬阈值（177K）则绕过熔断器强制压缩。

### 拆分前缀与尾部

```plain
int keepStartIndex = computeKeepStartIndex(messages);
List<Message> toSummarize = messages.subList(0, keepStartIndex);
List<Message> toKeep = messages.subList(keepStartIndex, messages.size());
```

`computeKeepStartIndex` 从尾部往回走，累积 token 数。满足 `KEEP_RECENT_TOKENS = 10000` 或 `MIN_KEEP_MESSAGES = 5` 任一条件就停，上限 `KEEP_MAX_TOKENS = 40000` 。边界落在 tool\_result 上时往前退到对应的 tool\_use，不拆配对。

### 对话重建

```plain
String content = "本次会话延续自之前的对话，"
    + "因上下文空间不足进行了压缩。"
    + "以下是早期对话的摘要：\n\n" + summaryText;
if (!toKeep.isEmpty()) {
    content += "\n\n近期消息已原样保留。";
}
if (workDir != null && sessionId != null) {
    content += "\n\n如果你需要压缩前的具体细节……"
        + "请用 ReadFile 读取完整会话记录："
        + Path.of(workDir, ".mewcode", "sessions",
            sessionId + ".jsonl");
}
String attachment = buildRecoveryAttachment(recovery, toolSchemas);
if (!attachment.isEmpty()) {
    content += "\n\n---\n\n" + attachment;
}

ConversationManager compacted = new ConversationManager();
compacted.addUserMessage(content);
for (Message m : toKeep) {
    appendMessage(compacted, m);
}
```

压缩后的对话就两部分：一条 user 消息（摘要 + 会话记录路径 + 恢复块），加上保留的尾部原文。没有 assistant 确认消息。

恢复块由 `buildRecoveryAttachment` 渲染：最近 5 个文件快照（每个 5000 tokens）、Skill 定义（总预算 25000 tokens）、工具列表。

### 会话边界持久化

```plain
SessionManager.saveCompactBoundary(
    workDir, sessionId, summaryText, keepRecords);
```

`SessionManager` 把摘要和 keep tail 序列化成 JSON，追加到 session JSONL 文件，角色标为 `system` ，type 标为 `compact_boundary` 。Resume 时扫描最后一条 boundary 重建对话。

## 连续同角色消息合并

```plain
private List<MessageParam> mergeConsecutiveSameRole(
    List<MessageParam> messages) {
    // ...
    if (prev.role().equals(curr.role())) {
        if (prevContent.isString() && currContent.isString()) {
            merged.set(merged.size() - 1, MessageParam.builder()
                .role(prev.role())
                .content(prevContent.asString()
                    + "\n\n" + currContent.asString())
                .build());
        } else {
            merged.add(curr);
        }
    }
}
```

`AnthropicClient.buildMessages()` 最后一步调用 `mergeConsecutiveSameRole` 。两条相邻消息角色相同且都是纯文本时，用 `\n\n` 拼接成一条。如果其中一条带 tool\_result 块参数，就不合并，原样保留。

压缩后摘要（user）和 keep tail 首条（可能也是 user）相邻时，就靠这个合并来维持 API 交替规则。

## 小结

| 设计要点 | Java 实现 |
| --- | --- |
| 两层架构 | 全在 `ContextCompactor` 一个类里， `offloadAndSnip` + `autoCompact` |
| Layer 1 特点 | 直接修改 conv（无独立 state），遍历式聚合溢写 |
| 溢写原子性 | `writeSpill` 用 `StandardOpenOption.CREATE_NEW` ， `FileAlreadyExistsException` 捕获跳过 |
| 阈值公式 | `effectiveWindow − margin` ，软硬双阈值 |
| 对话重建 | 一条 user（摘要 + 恢复块）+ 尾部原文，无 assistant ack |
| 连续消息合并 | `mergeConsecutiveSameRole` 合并相邻纯文本同角色消息 |
| 边界持久化 | `SessionManager.saveCompactBoundary` 追加 JSONL 记录 |