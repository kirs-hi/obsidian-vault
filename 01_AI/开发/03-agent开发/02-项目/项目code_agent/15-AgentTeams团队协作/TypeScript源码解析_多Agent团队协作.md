# TypeScript源码解析：多 Agent 团队协作

理论篇讲了 Agent Teams 如何把一次性的子任务升级为长期协作团队，这篇来走读 MewCode 的 `src/teams/` 目录，看「多个 Agent 组团协作」的通信、调度和执行是怎么实现的。

## 模块概览

| 文件 | 职责 |
| --- | --- |
| `team.ts` | Team / Member / TeamManager 定义，spawnTeammate 主循环，Lead 邮箱消费 |
| `file-mailbox.ts` | JSONL 文件邮箱 + `"wx"` 文件锁 + 已读游标 |
| `coordinator.ts` | Coordinator 模式工具白名单 + 动态过滤函数 |
| `tools.ts` | 五个协调工具：TeamCreate / SpawnTeammate / SendMessage / ListTeams / TeamDelete |
| `backend.ts` | 后端检测 + 外部进程 spawn（tmux / child_process） |
| `progress.ts` | 队友进度追踪：工具活动描述、token 统计、环形缓冲区 |
| `transcript.ts` | 队友对话记录持久化与反序列化 |

架构一句话概括： `team.ts` 定义数据结构和驱动队友执行循环， `file-mailbox.ts` 负责通信， `tools.ts` 暴露给 LLM 调用， `coordinator.ts` 约束 Lead 权限， `backend.ts` 、 `progress.ts` 和 `transcript.ts` 做辅助。

## 核心类型

### Member

```plain
export interface Member {
  name: string;
  active: boolean;
  cancel?: () => void;
  mailbox: FileMailbox;
  uiState?: TeammateUIState;
  conversation?: ConversationManager;
}
```

每个队友持有独享的 `mailbox` 实例，指向 `.mewcode/teams/{teamName}/{name}.jsonl` 文件。 `active` 是 bool， `true` 表示工作中， `false` 表示空闲或已停止。 `uiState` 运行时才有值，用于 TUI 展示进度。 `conversation` 可选，设置后退出时会持久化对话记录。 `cancel` 是取消函数，调用后能终止队友的执行。

### Team

```plain
export class Team {
  name: string;
  mode: TeamMode;
  members = new Map<string, Member>();
  leadMailbox: FileMailbox;
  private mailboxDir: string;
}
```

`members` 用名字做 key，查找和遍历都方便。 `leadMailbox` 是 Lead 专属的收件箱，队友完成任务后往这里发 idle 通知。所有收件箱文件存放在 `.mewcode/teams/{teamName}/` 目录下，in-process 和外部进程模式都读写同一个磁盘位置。团队没有持久化 config.json，纯内存管理，进程退出就消失。

### TeamManager

```plain
export class TeamManager {
  private teams = new Map<string, Team>();
  private workDir: string;
  create(name: string, mode?: TeamMode): Team { ... }
  async delete(name: string): Promise<void> { ... }
  drainLeads(): string[] { ... }
  getAllTeammateStates(): TeammateUIState[] { ... }
}
```

管理所有团队的生命周期：创建、查找、删除、全量清理。 `drainLeads` 收集所有团队的 lead 未读消息。 `getAllTeammateStates` 聚合所有队友的 UI 状态，TUI 层拿这些数据渲染 spinner 树。

## 三种执行后端

### detectBackend：自动选择

```plain
export function detectBackend(): TeamMode {
  return "in-process";
}

export function detectPaneBackend(): TeamMode {
  if (process.env.TMUX) return "tmux";
  try {
    execSync("which tmux", { stdio: ["pipe", "pipe", "pipe"] });
    return "tmux";
  } catch { /* tmux not found */ }
  return "in-process";
}
```

两个函数，两套策略。 `detectBackend` 无条件返回 in-process，因为它能实时追踪进度，TUI 体验最好。 `detectPaneBackend` 是用户显式要求 pane 后端时的检测逻辑：先查 `TMUX` 环境变量（已在 tmux 会话里），再看 tmux 是否装了，都不满足就回退 in-process。没有 iTerm2 的自动检测，因为 iTerm 只在 macOS 上有。

### Tmux 后端

```plain
case "tmux": {
  const sessionName = `mewcode-${Date.now().toString(36)}`;
  const cmd = [config.command, ...config.args].join(" ");
  try {
    execSync(`tmux new-window -t "${sessionName}" -n teammate "${cmd}"`, { ... });
  } catch {
    // new-window 失败时降级为新 session
    execSync(`tmux new-session -d -s "${sessionName}" -n teammate "${cmd}"`, { ... });
  }
}
```

`spawnTeammate` 函数里按 mode 分发。tmux 模式用 `new-window` 在当前 session 里创建新窗口，失败就降级为 `new-session` 。会话名用时间戳的 base36 编码保证唯一。返回的 `cancel` 函数调用 `kill-session` 清理。

### In-process 后端

in-process 模式的执行逻辑直接嵌在 `Team.spawnTeammate` 里，不走 `backend.ts` 的 `spawnTeammate` 函数。用 `void (async () => { ... })()` 启动后台异步任务，这是「fire-and-forget」的标准写法。通信仍然走 FileMailbox，保持和外部后端一致的接口。

## FileMailBox：跨进程通信

### 数据结构

```plain
export interface FileMailMessage {
  from: string;
  text: string;
  timestamp: string;
}
```

字段精简：发送者、正文、时间戳。没有 `read` 标记字段，因为已读状态用游标方案追踪，不需要逐条标记。

### 存储格式

用 JSONL（每行一条 JSON）格式，每条消息追加写入 `{memberName}.jsonl` 。已读位置用独立的 `{memberName}.read` 文件记录行号，进程重启后从上次读到的地方继续。JSONL 的好处是写操作只需追加一行，不需要读-改-写整个文件。每个收件人独立文件，写不同收件人不冲突。

### 文件锁机制

```plain
function acquireLock(lockFile: string): void {
  for (let attempt = 0; attempt < LOCK_MAX_ATTEMPTS; attempt++) {
    try {
      const fd = openSync(lockFile, "wx"); // O_CREAT|O_EXCL
      closeSync(fd);
      return; // 拿到锁
    } catch (err) {
      // 超过 10 秒的锁文件视为 stale，强制删除
      if (Date.now() - info.mtimeMs > LOCK_STALE_MS) unlinkSync(lockFile);
      // 随机退避 5-100ms
      sleepSync(delayMs);
    }
  }
}
```

`"wx"` flag 等价于 `O_CREAT|O_EXCL|O_WRONLY` ，操作系统保证不会有两个进程同时成功。最多重试 10 次，每次随机退避 5-100ms 避免雪崩。超过 10 秒的锁文件认为是 stale（持有者崩溃了），强制删除后重试。 `sleepSync` 用 `Atomics.wait` 实现同步等待，因为 Node.js 没有原生的同步 sleep。用文件锁而不是内存锁，是因为 tmux 模式下队友在不同进程里，内存锁管不到。

### 读写操作

`send` 在 `withLock` 里追加一行 JSON 到文件。 `receiveSync` 读取全部行，用 `lastReadLines` 游标跳过已读部分，只返回新增的行，然后把游标持久化到 `.read` 文件。这比遍历所有消息检查 read 标记要高效得多。

还有一个 `poll` 异步生成器，外部进程模式下队友可以 `for await (const msg of mailbox.poll(500))` 持续接收任务。

## 队友的主循环（In-process 模式）

```plain
void (async () => {
  let nextPrompt = task;
  while (member.active) {
    uiState.status = "running";
    const result = await runAgent(nextPrompt, onEvent);
    // 向 lead 发送 idle 通知
    uiState.status = "idle";
    await this.leadMailbox.send(name, `[idle] ${name} (reason: ${idleReason})`);
    // 轮询信箱等待新消息或 shutdown
    const pollResult = await this.waitForNextPromptOrShutdown(member);
    if (pollResult.shutdown || !member.active) break;
    nextPrompt = pollResult.prompt;
  }
})();
```

循环跑在 `spawnTeammate` 启动的异步闭包里，步骤清晰：

1.  调用 `runAgent` 执行一轮 agent 任务

2.  向 lead 的 mailbox 发送 `[idle]` 通知，附带队友名和原因

3.  进入 `waitForNextPromptOrShutdown` 轮询信箱（间隔 500ms）

4.  拿到新消息就拼接成下一轮 prompt 继续循环，拿到 `[shutdown]` 前缀消息就退出

`runAgent` 是依赖注入的函数，类型签名 `(task: string, onEvent?: AgentEventCallback) => Promise<string>` ，Team 层完全不依赖 Agent/LLM 层的具体实现。事件回调 `onEvent` 在执行期间更新 `TeammateUIState` 的工具计数和 token 消耗，TUI 靠这些数据渲染实时进度。

循环退出时，如果 `member.conversation` 有值，会调用 `saveTranscript` 持久化对话记录。

## 协调工具

### SendMessage

```plain
export class SendMessageTool implements Tool {
  async execute(args: Record<string, unknown>): Promise<ToolResult> {
    const t = this.mgr.get(team);
    if (!t) return { output: `Team '${team}' not found.`, isError: true };
    await t.sendMessage("lead", to, message);
    return { output: `Message sent to '${to}'.`, isError: false };
  }
}
```

按名称在团队里查找成员，找到就往对应的 mailbox 写入。发送者固定是 `"lead"` 。没有广播功能，消息都是点对点的。

### TeamCreate

```plain
export class TeamCreateTool implements Tool {
  async execute(args: Record<string, unknown>): Promise<ToolResult> {
    const name = strArg(args, "name");
    if (this.mgr.get(name))
      return { output: `Team '${name}' already exists.`, isError: false };
    this.mgr.create(name);
    return { output: `Team '${name}' created.`, isError: false };
  }
}
```

流程简洁：检查同名团队是否存在，不存在就创建。 `create` 内部调用 `detectBackend` 自动选择后端模式。

### TeamDelete

```plain
export class TeamDeleteTool implements Tool {
  async execute(args: Record<string, unknown>): Promise<ToolResult> {
    const name = strArg(args, "name");
    await this.mgr.delete(name);
    return { output: `Team '${name}' deleted.`, isError: false };
  }
}
```

`delete` 内部先调用 `team.stopAll()` 遍历所有成员，把 `active` 设为 `false` 并调用 `cancel()` ，然后从 Map 中移除团队。

### SpawnTeammate

`SpawnTeammate` 是独立工具而非 Agent 工具的参数分支。如果指定的团队不存在，工具会自动创建：

```plain
const t = this.mgr.get(team) ?? this.mgr.create(team);
t.spawnTeammate(name, task, this.runAgent);
```

这个「自动创建」的便利设计让 LLM 不需要先 TeamCreate 再 SpawnTeammate，一步到位。

## Lead 感知队友状态

```plain
drainLeads(): string[] {
  const out: string[] = [];
  for (const team of this.teams.values()) {
    const msgs = team.leadMailbox.receiveSync();
    if (msgs.length === 0) continue;
    const lines: string[] = [];
    lines.push(`<team-notification team="${team.name}">`);
    for (const msg of msgs) {
      lines.push(`from=${msg.from}: ${msg.text}`);
    }
    lines.push("</team-notification>");
    out.push(lines.join("\n"));
  }
  return out;
}
```

挂在 Lead 的 `notificationFn` 上，每轮循环开头调用。遍历所有团队读取 lead 未读消息，格式化为 `<team-notification>` XML 标签注入对话。Lead 看到 `[idle] memberName (reason: available)` 就知道谁干完了，决定是派新任务还是收工。

## 队友 spawn 流程

完整的 spawn 流程集中在 `Team.spawnTeammate` 和 `SpawnTeammateTool.execute` 里：

1.  `SpawnTeammateTool` 接收 team、name、task 三个参数，找到或创建团队

2.  调用 `team.addMember(name)` 注册成员，创建独立的 FileMailbox

3.  创建 `TeammateUIState` （包含进度追踪器和随机 spinner 动词）

4.  注册 `AgentEventCallback` ，让 Team 层观察 agent 的工具调用和 token 消耗

5.  启动异步主循环（ `void (async () => { ... })()` ），执行 idle-poll-continue 模式

6.  `runAgent` 是通过构造函数注入的，Team 层不直接依赖 Agent/LLM 层

队友的协调附录（addendum）告诉队友文本回复对其他队友不可见，必须用 SendMessage 通信。

## 协调者模式（Coordinator Mode）

### 工具白名单

```plain
const COORDINATOR_ALLOWED_TOOLS = new Set([
  "Agent", "SendMessage",
  "TaskCreate", "TaskGet", "TaskList", "TaskUpdate",
  "TeamCreate", "TeamDelete", "ListTeams", "SpawnTeammate",
  "ReadFile", "Glob", "Grep", "Bash",
]);
```

白名单分两类：协调工具（Agent、SendMessage、Team 管理、Task 管理）和只读工具（ReadFile、Glob、Grep、Bash）。 `EditFile` 和 `WriteFile` 不在白名单里，设计意图是 Lead 只调度不动手，写操作都交给队友。

### 动态过滤

```plain
export function coordinatorToolFilter(
  teamMgr: TeamManager
): (name: string) => boolean {
  return (name: string): boolean => {
    if (teamMgr.list().length === 0) return true;
    if (name.startsWith("mcp__")) return true;
    return isCoordinatorTool(name);
  };
}
```

`coordinatorToolFilter` 返回一个谓词函数，动态判断是否限制工具。有团队存在时只放行白名单内的工具，所有团队都删除后自动恢复全部工具。MCP 工具（ `mcp__` 前缀）始终放行，不受白名单限制。

## 对话记录持久化（如有 Transcript）

```plain
export function saveTranscript(
  workDir: string, teamName: string,
  agentId: string, conv: ConversationManager,
): string {
  const dir = transcriptDir(workDir, teamName);
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${agentId}.json`);
  const data = serializeConversation(conv);
  writeFileSync(path, JSON.stringify(data, null, 2), "utf-8");
  return path;
}
```

队友退出时自动保存到 `.mewcode/teams/{team}/transcripts/{agentId}.json` 。序列化保留完整结构： `role` 、 `content` 、 `tool_uses` （包含 tool\_use\_id、tool\_name、arguments）、 `tool_results` （包含 content 和 is\_error）。 `loadTranscript` 能把 JSON 反序列化回来，用于调试时回放队友的完整对话历史。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 后端自动选择 | `detectBackend` 默认 in-process， `detectPaneBackend` 按环境变量选 |
| In-process 执行 | `void (async () => { ... })()` 启动异步闭包，idle-poll-continue 循环 |
| 外部进程执行 | tmux `new-window` ，失败降级 `new-session` |
| 跨进程通信 | FileMailbox，JSONL 追加 + `"wx"` 文件锁 + 行号游标 |
| 队友主循环 | runAgent → idle notify → poll inbox → 新消息继续 / shutdown 退出 |
| Lead 感知 | `drainLeads` 挂在 `notificationFn` ， `<team-notification>` XML 格式 |
| 工具暴露 | 五个 Tool 类，SpawnTeammate 自动创建不存在的团队 |
| 协调者模式 | `coordinatorToolFilter` 动态谓词，无团队时自动恢复全工具 |
| 优雅关闭 | `[shutdown]` 消息 + cancel 函数 + active 标志 |
| 对话持久化 | 退出时序列化为 JSON，保留完整 tool_uses/tool_results |

> 更新: 2026-06-08 16:41:24  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/ze6yy4bi96xz7ka9](https://www.yuque.com/tianming-uvfnu/gmmfad/ze6yy4bi96xz7ka9)