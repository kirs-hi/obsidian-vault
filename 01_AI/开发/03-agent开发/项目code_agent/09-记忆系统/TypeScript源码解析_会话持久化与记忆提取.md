# TypeScript源码解析：会话持久化与记忆提取

走读 MewCode 的记忆系统代码，看三类长期记忆（项目指令、会话持久化、自动记忆）是怎么在文件系统上实现的。

## 模块概览

记忆系统的代码分布在三个目录下。 `src/memory/` 管自动记忆存储、提取和召回。 `src/session/` 管会话持久化。 `src/history/` 管输入历史。

| 文件 | 职责 |
| --- | --- |
| `memory/instructions.ts` | 项目指令加载（简化版） |
| `memory/manager.ts` | 记忆管理器：扫描、索引、召回、frontmatter 解析 |
| `memory/extractor.ts` | 记忆提取器：LLM 调用、结果解析、文件写入 |
| `session/session.ts` | JSONL 会话存储：写入、加载、列表、压缩边界 |
| `history/history.ts` | 输入历史：JSONL、连续去重、容量淘汰 |

文件数量精简，但核心功能都覆盖了。

## 核心类型

### MemoryFile / MemoryHeader

```plain
export interface MemoryFile {
 path: string;
 name: string;
 description: string;
 type: string;
 content: string;
}
```

`MemoryFile` 用于加载记忆的完整内容（包含 body），供展示和注入。另一个接口 `MemoryHeader` 只有元数据（filename、filePath、scope、mtimeMs、description、type），用于扫描和召回选择器，不读文件全文。

type 字段决定存储路径：user/feedback 存到 `~/.mewcode/memory/` ，project/reference 存到项目级 `.mewcode/memory/` 。

### SessionMessage

```plain
export interface SessionMessage {
 role: string;
 content: string;
 timestamp: string;
 type?: string;
}
```

的 SessionMessage 也是精简设计，没有 tool\_use\_id。 `type` 字段可选，普通消息不填，压缩边界记录填 `compact_boundary` 。 `timestamp` 用 ISO 字符串而不是 Unix 整数。

content 统一是字符串类型。assistant 消息里的工具调用信息在持久化时被拍平成文本。

### SessionInfo

```plain
export interface SessionInfo {
 id: string;
 firstMessage: string;
 messageCount: number;
 size: number;
 modTime: Date;
}
```

没有独立的 `.meta` 文件，元信息从 JSONL 文件里提取。

## 第一层记忆：项目指令

### 加载路径与优先级栈

```plain
const INSTRUCTION_FILES = ["MEWCODE.md", "mewcode.md"];
export function loadInstructions(workDir: string): string {
 // 先在当前目录找
 for (const name of INSTRUCTION_FILES) {
 const path = join(workDir, name);
 if (existsSync(path)) return readFileSync(path, "utf-8");
 }
 // 找不到就向上遍历，最多 10 层
 let dir = workDir;
 for (let i = 0; i < 10; i++) {
 dir = dirname(dir);
 for (const name of INSTRUCTION_FILES) { /* 同上 */ }
 }
 return "";
}
```

的指令加载做了最大幅度的简化。先在当前目录找 `MEWCODE.md` 或 `mewcode.md` （大小写兼容），找到就返回。找不到就向上遍历父目录，最多 10 层。策略是「找到即返回」，不做多层拼接。

关键特点：没有用户全局指令（不加载 `~/.mewcode/MEWCODE.md` ），没有 `.mewcode/INSTRUCTIONS.md` 兼容路径，没有 `AGENTS.md` 支持。向上遍历最多 10 层作为兜底。

### @include 递归展开

没有实现 @include。指令文件直接读取，不做预处理。

## 第二层记忆：会话持久化

### JSONL 格式选择

选 JSONL 格式：追加写入 O(1)，崩溃安全，增量恢复。

### 消息写入

```plain
export function saveMessage(
 workDir: string,
 sessionId: string,
 msg: SessionMessage
): void {
 const dir = sessionsDir(workDir);
 mkdirSync(dir, { recursive: true });
 const filePath = join(dir, `${sessionId}.jsonl`);
 const line = JSON.stringify(msg) + "\n";
 writeFileSync(filePath, line, { flag: "a", encoding: "utf-8" });
}
```

每次写入用 `writeFileSync` 配合 `flag: "a"` 追加。每次调用都重新打开文件写入，不持有长生命周期的文件句柄。

也没有自动生成标题的逻辑，列表时才去扫第一条 user 消息。

### 压缩边界

```plain
export function saveCompactBoundary(
 workDir: string,
 sessionId: string,
 payload: CompactBoundaryPayload
): void {
 saveMessage(workDir, sessionId, {
 role: "system",
 content: JSON.stringify(payload),
 timestamp: new Date().toISOString(),
 type: COMPACT_BOUNDARY,
 });
}
```

CompactBoundaryPayload 包含 summary 和 keep（ `KeptMessage[]` ）。序列化成 JSON 字符串塞在 content 里，type 标记为 `compact_boundary` 。

### 消息链校验

没有消息链校验。SessionMessage 不含 tool\_use\_id，恢复时直接逐行解析。

### 会话恢复

```plain
export function rebuildFromSession(
 saved: SessionMessage[]
): RestoredMessage[] {
 let lastBoundary = -1;
 for (let i = saved.length - 1; i >= 0; i--) {
 if (saved[i].type === COMPACT_BOUNDARY) {
 lastBoundary = i;
 break;
 }
 }
 // 有 boundary：summary + keep + 后续消息
 // 无 boundary：全量回放
}
```

恢复逻辑是压缩感知的。从后往前找最后一个 boundary，如果找到就只恢复 boundary 之后的内容。boundary 内的 summary 展开为一条 user 消息，keep 尾部原样回放，再拼上 boundary 之后追加的消息。

没有 boundary 的旧会话走全量回放，兼容老数据。

`RestoredMessage` 接口只有 `role` 和 `content` 两个字段，严格限制为 user/assistant 角色。system 消息和空内容消息在恢复时被过滤掉。

### 会话管理器

```plain
export function newSessionId(): string {
 const ts = Date.now().toString(36);
 const rand = randomBytes(4).toString("hex");
 return `${ts}-${rand}`;
}
```

的会话 ID 格式：Unix 毫秒时间戳的 36 进制编码加 8 位 hex 随机后缀。类似 `m1abc3d4-1a2b3c4d` 这样的格式。时间信息被压缩成短字符串，不能一眼看出日期。

`listSessions` 扫描 `.jsonl` 文件，按修改时间倒序排列。没有过期清理逻辑。

## 第三层记忆：自动记忆

### 存储结构

用独立 .md 文件 + YAML frontmatter + MEMORY.md 索引。

双目录分层：用户级 `~/.mewcode/memory/` 、项目级 `<project>/.mewcode/memory/` 。

`MemoryManager` 在加载时自动重建索引：

```plain
rebuildIndex(): void {
 const entries = [];
 for (const dir of [this.userDir, this.projectDir]) {
 // 扫描 .md 文件，解析 frontmatter
 // 每个文件产出一条 {name, relPath, description}
 }
 entries.sort((a, b) => a.name.localeCompare(b.name, ...));
 // 截断到 MAX_ENTRYPOINT_LINES / MAX_ENTRYPOINT_BYTES
 writeFileSync(join(this.projectDir, MEMORY_INDEX_NAME),
 content + "\n", "utf-8");
}
```

`rebuildIndex` 扫描两个目录的所有 .md 文件，按名字字母序排列，生成 `- [name](path) — description` 格式的索引行，写入 MEMORY.md。有两层截断保护：200 行和 25KB，字节截断在最后一个换行处切断。

每次 `loadAll()` 都会自动调用 `rebuildIndex()` ，确保索引始终是最新的。

### 提取时机与触发

的提取由外部调用方触发， `MemoryExtractor.extract` 接收对话摘要文本作为输入。没有内置的触发间隔或合并策略。

### 提取 prompt 与 LLM 调用

```plain
async extract(conversationSummary: string): Promise<string[]> {
 conv.addUserMessage(
 "Based on the following conversation, extract any memories...\n" +
 "For each memory, output it in this format:\n" +
 "MEMORY_NAME: <kebab-case-name>\n" +
 "MEMORY_TYPE: <user|feedback|project|reference>\n" +
 "MEMORY_DESC: <one-line description>\n" +
 "MEMORY_BODY: <content>\n" +
 "---\n\n" +
 "If no memories are worth saving, output NONE.\n\n" +
 "Conversation:\n" + conversationSummary
 );
```

的提取 prompt 定义了一种结构化文本格式：每条记忆用 `MEMORY_NAME` / `MEMORY_TYPE` / `MEMORY_DESC` / `MEMORY_BODY` 四个字段声明，多条记忆之间用 `---` 分隔。没有值得保存的就输出 `NONE` 。

这种格式比子 Agent 模式简单（不需要工具调用），同时比 `### type` 分段格式更结构化。每条记忆有独立的 name、type、description、body，可以直接映射到 .md 文件的 frontmatter。

### 提取结果的解析与持久化

```plain
const blocks = response.split("---")
 .filter((b) => b.includes("MEMORY_NAME:"));
for (const block of blocks) {
 const name = extractField(block, "MEMORY_NAME");
 const type = extractField(block, "MEMORY_TYPE") || "reference";
 const desc = extractField(block, "MEMORY_DESC");
 const body = extractField(block, "MEMORY_BODY");
 if (!name || !body) continue;
 const dir = type === "project" || type === "reference"
 ? projectDir : userDir;
 const content = `---\nname: ${name}\ndescription: ${desc}\n` +
 `metadata:\n type: ${type}\n---\n\n${body}\n`;
 writeFileSync(join(dir, `${name}.md`), content, "utf-8");
}
```

按 `---` 分割成块，用正则提取每个字段。type 字段决定写到哪个目录。写入时生成完整的 frontmatter（注意 type 嵌套在 `metadata.type` 下，不是顶层 `type` ），加上 body 内容。

写入后立即调用 `rebuildIndex()` 更新 MEMORY.md 索引。

未知类型默认回退到 `"reference"` 。name 或 body 为空的条目跳过。

### 记忆注入

```plain
buildSystemReminder(): string {
 const memories = this.loadAll();
 if (memories.length === 0) return "";
 const lines = memories.map(
 (m) => `- [${m.name}] (${m.type}): ${m.description}`
 );
 return `Active memories:\n${lines.join("\n")}`;
}
```

注入方式比较简洁：把所有记忆的 name + type + description 拼成一段文本，不注入完整的行为指令（四类定义、保存规则等），只是一个简单的清单。

### 记忆召回

有完整的记忆召回实现，作为 `MemoryManager` 的方法：

```plain
async findRelevantMemories(
 query: string,
 client: LLMClient,
 recentTools: string[] = [],
 alreadySurfaced: Set<string> = new Set()
): Promise<RelevantMemory[]> {
```

不用 `SelectorFn` 回调接口，而是直接接收 `LLMClient` 实例。选择器的 system prompt 作为 user 消息的前缀内联（因为 LLMClient 在构造时绑定 system prompt，不能临时切换）。

扫描用 `scanMemoryHeaders` ，格式化用 `formatMemoryManifest` ，解析 JSON 用 `extractJSONObject` 。

`alreadySurfaced` 过滤已展示的记忆，5 个名额不会浪费在重复召回上。

## 输入历史

```plain
export function append(dir: string, text: string): void {
 const entries = load(dir);
 if (entries.length > 0 && entries[entries.length - 1] === text) {
 return;
 }
 entries.push(text);
 while (entries.length > MAX_ENTRIES) {
 entries.shift();
 }
 const lines = entries.map((t) => JSON.stringify({ text: t }))
 .join("\n") + "\n";
 writeFileSync(filePath, lines, "utf-8");
}
```

存储在项目目录下的 `prompt_history.jsonl` ，每行一个 `{text}` 对象（没有 ts 时间戳字段）。容量上限 200 条，超过从头部用 `shift()` 淘汰。连续去重：和最后一条比较。

写入策略是全量重写。先 load 读出来，追加新的，截断，再整体写回。

序列化时只有 `text` 字段，没有时间戳。

## 小结

| 设计决策 | TS 实现方式 |
| --- | --- |
| 指令优先级 | 当前目录 → 向上遍历 10 层，找到即返回 |
| 会话存储格式 | JSONL，每次开关文件追加 |
| 会话 ID 生成 | Unix 毫秒 base36 + 8 位 hex 随机后缀 |
| 消息链校验 | 无（SessionMessage 不含 tool_use_id） |
| 记忆存储结构 | 独立 .md 文件 + YAML frontmatter + MEMORY.md 索引 |
| 提取触发方式 | 外部调用方触发，无内置间隔 |
| 提取合并策略 | 无合并策略 |
| 记忆召回 | LLMClient 直接调用，选最多 5 条 |
| 过期保护 | 无（缺失 MemoryAge / freshnessText） |
| 输入历史 | JSONL，200 条上限，全量重写，无时间戳 |

> 更新: 2026-06-08 16:08:03  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/qln83m2hevtvav7p](https://www.yuque.com/tianming-uvfnu/gmmfad/qln83m2hevtvav7p)

<!-- series-nav-start -->

---
**📚 记忆系统**（5/6）

⬅️ 上一篇：[[Python源码解析_会话持久化与记忆提取]] | ➡️ 下一篇：[[实战演练_动手实现记忆系统]]

<!-- series-nav-end -->
