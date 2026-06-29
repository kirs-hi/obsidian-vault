# 第15章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装上了 Worktree，让每个子 Agent 拥有独立的文件系统，彻底消除了并行修改的冲突。但那套模型还是「星型」的：主 Agent 在中心，子 Agent 在周围，所有通信都要经过主 Agent，而且主Agent还得自己下场干活，一旦任务复杂，可能就力不从心

这一章要给 MewCode 装上 Agent Team 机制。Lead 还可以开启 Coordinator Mode 专注调度，从而应对更复杂的任务

具体要新增这些东西：

-   **AgentTeam 核心结构** ：团队数据模型、队员花名册、团队配置持久化
-   **三种执行后端** ：tmux pane、iTerm2 pane（独立进程隔离）、in-process（同进程轻量运行）+ 自动检测
-   **协调工具集** ：复用已有 Task 工具 + 新增 SendMessage，注入到队员工具池
-   **Mailbox** **消息系统**：按 agentID 分文件存储，tmux 后端额外 send-keys 唤醒
-   **团队生命周期管理** ：TeamCreate / TeamDelete 顶层工具，队员 spawn、收敛合并、清理
-   **队员空闲与续写** ：磁盘 transcript 持久化，Lead 可通过 SendMessage 恢复已停止的队员
-   **Coordinator Mode** ：双锁激活、工具集收窄、四阶段工作流提示词注入

这章 **不做** ：跨机器的分布式 Agent Team、队员之间的实时流式通信。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 抽象出一个长期存在的"小组"对象，承载名称、负责人、成员花名册和持久化位置；成员级别记录角色、工作目录、运行后端、是否需要审批等元信息
- 提供多种成员运行后端：可在独立终端窗格里跑一个完整 CLI 实例（强隔离），也可在同进程里以协程方式轻量运行；运行位置按环境优先级自动选择，不静默降级
- 给小组成员发放一组协作工具——共享任务的创建/查看/列举/更新（带可选依赖字段）以及点对点消息发送；主入口和普通子 Agent 看不到这些工具
- 点对点消息走"名称注册表 + 邮箱文件"两段式：通过名称解析到目标实例 ID，写入对应邮箱；独立进程后端额外唤醒目标窗格；支持广播、纯文本带摘要、以及若干结构化协议消息（生命周期、审批回复）
- 把发起方设计成 Lead：它负责把用户目标拆成任务并写入共享清单（含先后依赖），派生成员，全部完成后通过 git 合并各人的工作目录、解决能搞定的冲突、搞不定就回滚上报
- 成员完成自然停止后标记为空闲并通知 Lead；Lead 之后通过发消息即可从磁盘恢复其上下文继续指派新工作，而不是重头再 spawn
- 单独提供一种"纯调度"开关（双重锁定才生效）：开启后剥夺发起方的代码读写与 shell 工具，只留派人/终止/发消息/输出结果，并注入多阶段工作流指引，把理解与综合留在发起方手里
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了，然后让 Claude Code 根据这三份文档进行开发

![](实战演练_动手实现_Agent_Teams-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现_Agent_Teams-2.jpeg)

### 功能验证过程

来验收一下结果：

启动MewCode，输入：

帮我创建一个团队 demo，派一个队员 alice，让它读 README.md 并总结主要章节

![](实战演练_动手实现_Agent_Teams-3.jpeg)

然后主Agent，会去进行队伍的创建，创建后，会去开始启动队员，我们能在.mewcode/teams这里有一个叫read-demo的一个队伍信息

![](实战演练_动手实现_Agent_Teams-4.jpeg)

里面分别是我们的lead和我们的alice，然后过一段时间后，alice就会完成任务，传达给lead，然后lead会汇总这个结果

![](实战演练_动手实现_Agent_Teams-5.jpeg)

然后我们测测队员之间的worktree的隔离，我们先搞个测试文件，内容如下

![](实战演练_动手实现_Agent_Teams-6.jpeg)

然后，我们输入

开个团队 demo，派 alice 和 bob 同时改 DEMO.md，alice 改 Section A，bob 改 Section B

![](实战演练_动手实现_Agent_Teams-7.jpeg)

可以看到，lead会知道需要开worktree去并行修改，我们也能在.mewcode/worktrees看到它们的worktree

![](实战演练_动手实现_Agent_Teams-8.jpeg)

等两个队员完成后，会让lead去审阅和合并

![](实战演练_动手实现_Agent_Teams-9.jpeg)

我们可以看看目前的Demo.md的内容

![](实战演练_动手实现_Agent_Teams-10.jpeg)

并行修改是成功的，无冲突，然后完成后会清除team和汇总

![](实战演练_动手实现_Agent_Teams-11.jpeg)

这就是我们的coordinatoe模式的team的样子，lead就是lead，专注于决策，不会下一线干活，下属去干活，然后向上汇报，就像我们的公司协作分工结构一样

![](实战演练_动手实现_Agent_Teams-12.jpeg)

到这里，MewCode 的核心能力已经全部搭建完毕。

恭喜你！从终端原型，到工具系统、Agent 循环、权限管理、上下文压缩、Hook 系统、SubAgent、Worktree，再到现在的 Agent Team，你亲手完成了一个完整的 Coding Agent！

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

提示词如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch15: AgentTeam Spec

## 1. 背景

SubAgent（ch13）解决了一次性子任务的上下文隔离，但拓扑是星型：所有子 Agent 只能和主 Agent 通信，子 Agent 之间彼此看不见。当任务规模上来——四个模块同时重构、多角度并行调查 bug、一个 Agent 需要把发现告诉另一个——星型拓扑下主 Agent 成了信息中转瓶颈，子任务被迫串行。这一章把"长期协作团队"做成 MewCode 的一等概念：多个 Agent 组成 Team，并行干活、直接互发消息、共享任务列表，主 Agent 升级为 Team Lead 专职调度。

## 2. 目标

提供 `Team` / `TeamManager` / `FileMailBox` / `SendMessageTool` / `TeamCreateTool` / `TeamDeleteTool` 一整套类型与工具，让 LLM 在对话里：1) 调 `TeamCreate` 建团队（按环境自动选 tmux / iTerm2 / in-process 后端），2) 调 `Agent` 工具带 `team_name` 把队员 spawn 进团队，3) 队员之间通过 `SendMessage` 走 `FileMailBox` 互发消息、idle 后通知 Lead，4) Lead 进入 Coordinator Mode 只调度不动代码。tmux / iTerm 后端时由 `cmd/mewcode --teammate` 子模式启动队员工作进程，与 Lead 通过同一份 mailbox 目录通信。

## 3. 功能需求

- F1: `TeamMode` 三档常量 `in-process` / `tmux` / `iterm`；`detectBackend()` 按 `TMUX` env → `ITERM_SESSION_ID` env → `tmux` 可执行文件 → in-process 的优先级自动选择。
- F2: `Team` 持有 `Name / Mode / Members map / MailBox`，`Member` 含 `Name / AgentRef / Conv / Active / Cancel / PaneID`，外部后端 Member 仅留 PaneID 句柄、AgentRef/Conv 为空。
- F3: `TeamManager` 提供 `CreateTeam` / `GetTeam` / `DeleteTeam` / `ListTeams` / `CloseAll` + `CreateTeamWith`（让外部工作进程注册自己本地构造的 Team 对象，共享同一 mailbox 目录）。
- F4: `FileMailBox` 基于 `<baseDir>/<agentID>.json` 文件持久化消息；`Send` / `ReadUnread` / `MarkAllRead` 三件套；并发安全靠 `<agentID>.json.lock` 文件锁（O_CREATE|O_EXCL，10 次重试，>10s 视为过期）。
- F5: `FileMailMessage` 字段 `From / Text / Timestamp / Read / Color / Summary`；`Read=false` 落盘后由 `MarkAllRead` 批量翻转，区分已读与未读。
- F6: `SpawnTeammate(ctx, TeammateSpawnConfig)` 统一入口按 `Team.Mode` 分发到 in-process / tmux / iTerm 三条路径，返回 `SpawnResult{Mode, EventCh, PaneID}`。
- F7: In-process 路径走 `StartInProcessMember`：`team.AddMember` 注册成员、启动 goroutine 跑 `RunInProcessTeammate`、返回一个事件 channel；可选 `Workdir` 覆盖 `Agent.WorkDir` 配合 worktree 隔离。
- F8: 外部后端路径（tmux / iTerm）启动前把 `Task` 作为初始消息写入对方 mailbox（队员进程启动后第一次 idle poll 拿到）；用 `BuildTeammateCLI` 拼出 `cd <wd> && mewcode --teammate --team-name X --agent-name Y` 命令字符串；`shellQuote` 用单引号包裹安全转义；`spawnTmuxTeammate` 调 `tmux new-window -d`，`spawnITermTeammate` 调 `osascript` 创建 iTerm tab；返回 paneID/tabID 落到 `Member.PaneID`。
- F9: `RunInProcessTeammate` 队员主循环：每一轮先用 `InjectPendingMessages` 把未读邮件转 system reminder 注入对话、再把 `nextPrompt` 加为 user message、调 `agent.Run` 跑一轮、转发事件给 `eventOut`、本轮结束写 idle 通知到 Lead 邮箱、`waitForNextPromptOrShutdown` 用 `IdlePollInterval (500ms)` 轮询直到来新消息或 shutdown 才进入下一轮。
- F10: `IsShutdownRequest` 用 `[shutdown]` 前缀判定（`ShutdownPrefix` 常量）；`CreateIdleNotification(member, reason)` 产出 `From=member`、`Text="[idle] member (reason: ...)"`、`Summary="idle"` 的标准消息；`reason` 在 ErrorEvent 出现时翻成 `failed`，否则默认 `available`。
- F11: `DrainLeadMailbox(mgr)` 扫所有团队的 Lead 收件箱（`LeadName="lead"` 常量），把未读消息按 `<team-notification team="X">\nfrom=Y: text\n...\n</team-notification>` 包装返回字符串数组，并把消息标记为已读；nil 安全。挂在 `Agent.NotificationFn` 上每轮 Lead 迭代之前自动抽取。
- F12: `BuildTeammateAddendum(team, member, others)` 产出注入到队员对话顶端的 system reminder，告诉它身份、Lead 是 `LeadName`、其他队友名字、必须通过 `SendMessage` 沟通且最终结果发给 Lead；和 ch13 子 Agent 的 fork boilerplate 一样是字面常量，不带任何调度细节。
- F13: `CoordinatorAllowedTools` map + `IsCoordinatorTool(name)` 函数；TUI 把 `coordinatorToolFilter(teamMgr)` 装到 `Agent.ToolNameFilter` 上：只要至少一个团队存在，Lead 的每轮工具集就被收窄到该白名单（`Agent` / `SendMessage` / `TeamCreate` / `TeamDelete` / `TaskCreate` 等 + 读类 `ReadFile` / `Glob` / `Grep` / `Bash`），全部团队清理后下一轮恢复全工具集。
- F14: `SendMessageTool` 暴露 `to` + `content` 两个字段；`to == LeadName` 走"找发送者所在团队"路径（Lead 不是 Member，不在任何团队 members map 里）；其它情况遍历所有团队找到 `to` 这个 member 所在团队，写入对方 mailbox。未匹配返 IsError 文案。
- F15: `TeamCreateTool` 暴露 `team_name` 必填、`description` 可选；同名冲突自动追加 `-2/-3/...` 后缀；调 `detectBackend()` + `TeamMgr.CreateTeam`；返回包含 mode 提示和下一步指引的 Output。
- F16: `TeamDeleteTool` 暴露 `team_name`；调 `TeamMgr.DeleteTeam`，内部循环 `StopMember` 把每个成员 stop（in-process 队员调 `cancel`、tmux 队员调 `stopTmuxTeammate` 发 C-c + kill-window、iTerm 队员调 `stopITermTeammate` 用 osascript 关 tab），返回 stopped 成员清单。
- F17: `AgentTool.runAsTeammate` 在主 Agent 的 `Agent` 工具调用里识别 `team_name`：先查团队是否存在、查重名、解析可选 `subagent_type` 走 `FilterToolsForAgent` 获取队员子工具池、空 name 时由 `sanitizeSlugSegment(description)` 生成；可选 `isolation=worktree` 时建独立 worktree 并把 notice 拼到 prompt 顶端；最后调 `teams.SpawnTeammate`，in-process 模式启 `drainTeammateEvents` goroutine 把事件流派进 `ProgressCh` 防止生产者阻塞。
- F18: `cmd/mewcode --teammate --team-name X --agent-name Y` worker 模式：`parseTeammateFlags` 仅识别这三个 flag，命中则跳过 TUI；`runTeammate` 加载同一份 config、注册 worker 工具白名单（无 TeamCreate/TeamDelete，仅 ReadFile/WriteFile/EditFile/Bash/Glob/Grep + SendMessage）、构造本地 Team 对象指向同一 mailbox 目录、AddMember 后跑 `RunInProcessTeammate`，事件 channel 走 `streamEventsToStderr` 喷到 stderr 让 tmux/iTerm pane 看见输出；接 SIGINT/SIGTERM 优雅退出。

## 4. 非功能需求

- N1: FileMailBox 跨进程并发安全——tmux 启动的队友进程和 Lead 进程不共享内存，必须靠文件锁保证写入原子性。锁文件 10 秒过期自动清理避免死锁。
- N2: 外部后端队员的初始任务必须在 spawn 之前写入 mailbox，因为 tmux/iTerm 新进程启动到第一次 idle poll 期间无法接消息；先写后启即可保证第一次 poll 必命中。
- N3: In-process 队员的事件 channel 在 `runAsTeammate` 路径上必须由后台 goroutine 持续消费（`drainTeammateEvents`），否则带缓冲 channel 满了之后 `RunInProcessTeammate` 主循环会卡在 select 上无法推进。
- N4: Coordinator Mode 通过 `ToolNameFilter` 在每轮迭代开头动态判定，而非一次性裁剪 registry。这样团队全部 Delete 后下一轮 Lead 自动恢复全工具集，无需重新构造 registry。
- N5: 队员的 `BuildTeammateAddendum` 必须明确告诉 LLM "纯文本回复对队友不可见，最终结果必须通过 `SendMessage(to=LeadName)` 发给 Lead"——否则队员模型容易写一段汇报作为最后输出就结束，Lead 永远拿不到结果（只能看到 idle 通知）。
- N6: `SendMessage(to="lead")` 不能走"在 Members 里找名字"的路径，因为 Lead 不是 Member。必须用"发送者所在团队的 mailbox.Send(LeadName, ...)"路径，否则永远报 `recipient 'lead' not found`。
- N7: `BuildTeammateCLI` 必须把 `team_name` / `agent_name` / `workdir` 都通过 `shellQuote` 单引号包裹，否则空格 / 特殊字符的 workdir 路径会破坏 shell 解析；单引号内的单引号用 `'\''` 闭合再续接的标准 POSIX 写法转义。
- N8: `iterm.go` 里的 AppleScript 字面量必须把内嵌的双引号转义为 `\"`，否则 `osascript -e` 解析失败；关闭流程是 best-effort，找不到 tab 不应报错（用户可能手动关掉了）。
- N9: `RunInProcessTeammate` 退出路径有三条：ctx 取消（返 ctx.Err）、收到 shutdown 消息（返 nil）、`agent.Run` 内部循环正常结束（继续下一轮）。退出时 `StartInProcessMember` 的 defer 必须置 `member.Active=false` 并关闭事件 channel，否则 UI 端永远等不到 close。
- N10: 测试运行时 `TestMain` 必须把 `MEWCODE_TEAMS_DIR` 指到 tmp 目录，否则跑完测试会在仓库根残留 `.mewcode/teams/` 目录。

## 5. 设计概要

- 核心数据结构:
 - `Team`：团队聚合，持有 `Mode` 决定后端、`Members map[string]*Member` 注册表、`MailBox *FileMailBox` 通信媒介、`mu sync.Mutex` 保护 Members 读写。
 - `Member`：队员元信息，in-process 模式下 `AgentRef + Conv` 有值（LLM 跑在本进程 goroutine），tmux / iTerm 模式下两者为空、`PaneID` 是外部句柄。
 - `TeamManager`：全局团队注册表，`teams map[string]*Team + mu sync.Mutex`，给 Lead 进程和 worker 进程共用一份接口。
 - `FileMailBox` + `FileMailMessage`：文件锁 + JSON 数组的 mailbox 实现，跨进程共享同一目录。
 - `TeammateSpawnConfig` / `SpawnResult`：`SpawnTeammate` 的入参/出参，把 in-process（`EventCh`）和外部后端（`PaneID`）的差异合并到同一返回类型。
 - `CoordinatorAllowedTools`：12 项白名单 map，TUI 的 `coordinatorToolFilter` 闭包按团队存活与否每轮重判。
- 主流程（按生命周期）:
 - 创建：用户消息 → 主 Agent → LLM 调 `TeamCreate(team_name)` → `detectBackend()` 选模式 → `TeamMgr.CreateTeam` 落到 `~/.mewcode/teams/<name>/inboxes/` → 返回 mode 提示给 Lead。
 - Spawn 队员：Lead LLM 调 `Agent(team_name=X, name=Y, prompt=Z)` → `AgentTool.runAsTeammate` → 解析 spec + 子工具集 + worktree → `BuildTeammateAddendum` → `teams.SpawnTeammate` → 按 mode 分发。
 - In-process：goroutine 跑 `RunInProcessTeammate`，事件 channel 由 `drainTeammateEvents` 后台消费。
 - 外部后端：先把初始任务写 mailbox → `BuildTeammateCLI` 拼命令 → `tmux new-window` / `osascript create tab` → 新进程跑 `cmd/mewcode --teammate` 走 `runTeammate` → 第一次 idle poll 命中初始消息开始干活。
 - 通信：队员 → `SendMessage` 工具 → 找对方所在团队 → `team.MailBox.Send` 写文件。队员收信走 `RunInProcessTeammate` 顶端的 `InjectPendingMessages`。
 - Lead 感知：每轮 Lead Agent 开头调 `NotificationFn` → `DrainLeadMailbox` → 抽 Lead 邮箱所有未读 → 包成 `<team-notification>` system reminder 喂回 LLM。
 - Coordinator Mode：只要 `teamMgr.ListTeams()` 非空，`ag.ToolNameFilter` 就过滤掉非白名单工具，Lead 自动从"既写代码又调度"变成"只调度"。
 - Stop：`TeamDelete` 工具 → `TeamMgr.DeleteTeam` → 遍历 `team.StopMember` → 按 `Mode + PaneID` 分发 `stopTmuxTeammate` / `stopITermTeammate` / 直接 cancel context。
- 调用链（模块层级）:
 - TUI 装配 → `registerAgentTools` 里 `teams.NewTeamManager()` → 注册 `TeamCreateTool` / `TeamDeleteTool` / `SendMessageTool` 三个工具 → 把 `teamMgr` 注入 `agents.AgentTool.TeamMgr`
 - Agent loop 在 `gatherNotifications` 里把 `teams.DrainLeadMailbox(m.teamMgr)` 的结果拼到消息流（tui.go:545）
 - Agent 初始化 / 恢复会话两处都给 `ag.ToolNameFilter = coordinatorToolFilter(m.teamMgr)`（tui.go:387 + 1132）
 - 外部工作进程入口 `cmd/mewcode/main.go` 先 `parseTeammateFlags` 截胡，命中走 `runTeammate` 不进 TUI
- 与其他模块的交互:
 - 依赖 `internal/agent`（Agent 实例 / AgentEvent 流）、`internal/conversation`（Conv manager）、`internal/llm`（Client）、`internal/tools`（Registry / Tool 接口）、`internal/worktree`（可选隔离）
 - 被 `internal/agents`（AgentTool.runAsTeammate）、`internal/tui`（注册 + drain + filter）、`cmd/mewcode`（worker 模式 + main 路由）调用

## 6. Out of Scope

- 不实现 PR 文档里描述的 `TeammateInfo` 完整模型（`agentType / model / planModeRequired` 字段、planModeRequired 审批工作流）——本章只做工具链层面的 Team / Member 骨架。
- 不实现 `plan_approval_response` / `shutdown_response` 结构化消息类型——目前仅 `[shutdown]` 文本前缀 + 文本消息两种。
- 不实现共享任务依赖图字段（`addBlocks` / `addBlockedBy`）——任务依赖由队员从 TaskList 文本里自己推断，或 Lead 通过描述文本约定。
- 不实现 `agentNameRegistry` 全局名称注册表——`SendMessage` 通过 `TeamMgr.ListTeams()` 遍历查找，团队规模小不需要 O(1) 索引。
- 不实现队员"空闲后从磁盘恢复对话"的续写机制——in-process 队员在 ctx 取消或收到 shutdown 后即终止，Lead 想再用需要重新 spawn；目前 transcript 不持久化。
- 不实现 `MEWCODE_COORDINATOR_MODE` 环境变量 + `COORDINATOR_MODE` feature flag 双锁——只要团队存在 Lead 就自动进入 Coordinator Mode，是单锁。
- 不实现"协调模式四阶段工作流"系统提示词注入（Research / Synthesis / Implementation / Verification）——`coordinatorToolFilter` 仅做工具收窄，不做提示词增强。
- 不实现"配置持久化到 ~/.mewcode/teams/<name>/config.json" 的团队元数据——只持久化邮箱 JSON，Team 实例本身随进程退出消失。
- 不实现 Worktree 团队层面的"收敛阶段 Lead 用 Bash 跑 git merge"自动化——合并由 Lead LLM 自己用 Bash 工具完成，本章不做封装。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch15: AgentTeam Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 Team / Member / TeamMode / TeamManager
- 影响文件: `internal/teams/teams.go`（`TeamMode` @ 17；`ModeInProcess / ModeTmux` 常量 @ 19-22；`teamsBaseDir` @ 24-30；`Member` @ 32-41；`Team` @ 43-49；`NewTeam` @ 51-59；`AddMember` @ 61-74；`StartMember` @ 76-92；`StopMember` @ 94-116；`SendMessage` @ 118-124；`TeamManager` @ 126-129；`NewTeamManager` @ 131-133；`CreateTeam` @ 135-141；`CreateTeamWith` @ 147-151；`GetTeam` @ 153-157；`DeleteTeam` @ 159-168；`ListTeams` @ 170-178；`CloseAll` @ 180-189）
- 依赖任务: 无
- 完成标准: `Team` 持有 `Name / Mode / Members map / MailBox / mu`；`Member.PaneID` 字段存在；`StopMember` 按 `Mode` + `PaneID` 分流 `stopTmuxTeammate / stopITermTeammate`，最后置 `Active=false`；`TeamManager.CreateTeamWith` 接受外部构造的 Team 注册（给 worker 进程用）；`teamsBaseDir` 支持 `MEWCODE_TEAMS_DIR` env 覆盖。
- [ ] 完成

## T2: 实现 FileMailBox（JSON + 文件锁）
- 影响文件: `internal/teams/filemailbox.go`（`FileMailBox` @ 11；`FileMailMessage` @ 15-22；`NewFileMailBox` @ 24-27；`inboxPath` @ 29-31；`lockPath` @ 33-35；`Send` @ 37-45；`ReadUnread` @ 47-59；`MarkAllRead` @ 61-68；`withLock` @ 71-111；`readInbox` @ 113-127；`writeInbox` @ 129-136）
- 依赖任务: 无
- 完成标准: 每个收件人对应 `<baseDir>/<agentID>.json`；`Send` 落盘时把消息 `Read` 强制置 false 并补 `Timestamp`；`MarkAllRead` 批量翻转 `Read=true`；并发安全靠 `<agentID>.json.lock` 文件用 `O_CREATE|O_EXCL` 加锁，10 次重试间隔 5-100ms 随机，>10s 视为过期锁强制删；`withLock` 在 `fn` 返回前 defer 删锁文件。
- [ ] 完成

## T3: 实现 detectBackend 自动选择
- 影响文件: `internal/teams/backend.go`（`detectBackend` @ 8-21）
- 依赖任务: T1
- 完成标准: 优先级 `TMUX` env → `ITERM_SESSION_ID` env → `exec.LookPath("tmux")` → `ModeInProcess`；前两者非空直接返回对应模式；都不命中时退化到 in-process。注意检测失败不会自动报错，只是退化。
- [ ] 完成

## T4: 实现 Tmux 后端
- 影响文件: `internal/teams/tmux.go`（`spawnTmuxTeammate` @ 9-19；`stopTmuxTeammate` @ 21-24）
- 依赖任务: T1
- 完成标准: `spawnTmuxTeammate` 用 `tmux new-window -d -n <teamName>-<memberName> <cliCommand>` 创建后台窗口；命令失败返 `"tmux new-window: %s: %s"` 错误；`stopTmuxTeammate` 先 `send-keys -t <pane> C-c` 再 `kill-window -t <pane>`，best-effort 不返回错误。
- [ ] 完成

## T5: 实现 iTerm2 后端 + ModeITerm
- 影响文件: `internal/teams/iterm.go`（`ModeITerm` 常量 @ 11；`spawnITermTeammate` @ 16-39；`stopITermTeammate` @ 43-55）
- 依赖任务: T1
- 完成标准: `ModeITerm TeamMode = "iterm"` 定义在 iterm.go 而非 teams.go（保持后端代码内聚）；`spawnITermTeammate` 用 `osascript -e` 调 AppleScript 在当前 iTerm window 创建新 tab 设 name 并 `write text <cliCommand>`，内嵌双引号转义为 `\"`；`stopITermTeammate` 用 AppleScript 遍历所有 window 的所有 tab 找 name 匹配的 tab close 掉，best-effort 失败静默。
- [ ] 完成

## T6: 实现队员主循环 RunInProcessTeammate
- 影响文件: `internal/teams/runner.go`（`RunInProcessTeammate` @ 60-123；`waitForNextPromptOrShutdown` @ 130-162；`formatInboundAsPrompt` @ 205-215）
- 依赖任务: T1, T2, T8
- 完成标准: 主循环 6 步——1) `ctx.Err()` 检查；2) `InjectPendingMessages` 把未读邮件作为 system reminder 注入；3) 把 `nextPrompt` 加为 user message；4) `agent.Run` 跑一轮并转发事件到 `eventOut`，ErrorEvent 把 `idleReason` 改成 `failed`；5) 写 idle 通知到 Lead 邮箱；6) `waitForNextPromptOrShutdown` 用 `IdlePollInterval` 轮询邮箱直到来新消息（构建下一轮 prompt 继续）或 shutdown（返 nil 退出）或 ctx 取消（返 ctx.Err）。`formatInboundAsPrompt` 把消息按 `"From <sender>: \n\n"` 拼成 prompt，空列表返空串。
- [ ] 完成

## T7: 实现 Lead-side 通信原语
- 影响文件: `internal/teams/runner.go`（`LeadName` 常量 @ 16；`ShutdownPrefix` 常量 @ 21；`IdlePollInterval` 常量 @ 25；`IsShutdownRequest` @ 30-32；`CreateIdleNotification` @ 37-44；`DrainLeadMailbox` @ 169-199）
- 依赖任务: T1, T2
- 完成标准: `LeadName = "lead"`、`ShutdownPrefix = "[shutdown]"`、`IdlePollInterval = 500*time.Millisecond` 三个常量字面值保持一致；`IsShutdownRequest` 用 `strings.HasPrefix(TrimSpace(text), ShutdownPrefix)` 判定；`CreateIdleNotification` 产出 `From=name / Text="[idle] <name> (reason: <r>)" / Summary="idle" / Timestamp`；`DrainLeadMailbox(nil)` 返 nil；非空时遍历所有团队读 Lead 邮箱，按 `<team-notification team="X">\nfrom=Y: text\n...\n</team-notification>` 包装返字符串数组，并把读过的标记为已读。
- [ ] 完成

## T8: 实现 In-process Bootstrap
- 影响文件: `internal/teams/inprocess.go`（`StartInProcessMember` @ 22-49；`BuildTeammateAddendum` @ 55-66；`InjectPendingMessages` @ 72-86）
- 依赖任务: T1, T2, T6
- 完成标准: `StartInProcessMember` 调 `team.AddMember` 注册队员 → `context.WithCancel` 绑定到 `member.Cancel` → 起 goroutine 跑 `RunInProcessTeammate`，defer 同时关闭 `eventCh` 和置 `Active=false`（取 team.mu 锁）；事件 channel 缓冲 32；`BuildTeammateAddendum` 文本必须包含队员名字 / Lead 名字 / "纯文本回复对队友不可见，最终结果必须 SendMessage 给 Lead" 三个关键信息；`InjectPendingMessages` 在有未读时返 `"You have new messages:\n\n..."` 并把消息 MarkAllRead，无未读返空串。
- [ ] 完成

## T9: 实现 SpawnTeammate 统一入口
- 影响文件: `internal/teams/spawn.go`（`TeammateSpawnConfig` @ 23-34；`SpawnResult` @ 39-43；`SpawnTeammate` @ 53-123；`recordExternalMember` @ 130-138）
- 依赖任务: T1, T4, T5, T8
- 完成标准: `SpawnTeammate` 校验 Team / MemberName 必填；按 `Team.Mode` switch 三档分发；`ModeInProcess` 调 `StartInProcessMember` 返 `EventCh`，Workdir 非空时把 `member.AgentRef.WorkDir` 覆盖为 workdir；`ModeTmux` 和 `ModeITerm` 先把 `Task` 写进对方 mailbox（Worker 进程启动后第一次 idle poll 拿到）→ `BuildTeammateCLI` 拼命令 → 调对应 spawn 函数拿 paneID → `recordExternalMember` 注册成员（仅留名字 + paneID + Active=true，AgentRef/Conv 为空）→ 返 `SpawnResult{Mode, PaneID}`；未知 mode 返错误。
- [ ] 完成

## T10: 实现 BuildTeammateCLI + shellQuote
- 影响文件: `internal/teams/spawn.go`（`BuildTeammateCLI` @ 149-164；`shellQuote` @ 169-177）
- 依赖任务: T9
- 完成标准: `BuildTeammateCLI` 用 `os.Executable()` 拿到当前二进制路径；workdir 空时默认 `os.Getwd()`；返回 `cd <quoted_wd> && <quoted_exe> --teammate --team-name <quoted_team> --agent-name <quoted_member>`；所有变量值都过 `shellQuote`。`shellQuote("")` 返 `''`，无特殊字符返原值，含 ` \t\n'"\$\`` 任一字符返 `'<value 内单引号替换为 '\''>'`。
- [ ] 完成

## T11: 实现 Coordinator Mode 工具白名单
- 影响文件: `internal/teams/coordinator.go`（`CoordinatorAllowedTools` @ 13-26；`IsCoordinatorTool` @ 29-31）
- 依赖任务: 无
- 完成标准: 12 项白名单 map：`Agent / SendMessage / TaskCreate / TaskGet / TaskList / TaskUpdate / TeamCreate / TeamDelete / ReadFile / Glob / Grep / Bash`；`IsCoordinatorTool(name)` 返回 map 命中布尔（写工具 `WriteFile / EditFile / NotebookEdit` 不在内）。
- [ ] 完成

## T12: 实现 SendMessage / TeamCreate / TeamDelete 三个工具
- 影响文件: `internal/teams/tools.go`（`SendMessageTool` @ 12-91；`TeamCreateTool` @ 94-145；`TeamDeleteTool` @ 148-199）
- 依赖任务: T1, T3
- 完成标准:
 - `SendMessageTool.Execute`：`to/content` 必填；`to == LeadName` 走 "查发送者所在团队"（Lead 不是 Member），用该团队 `SendMessage(sender, LeadName, content)` 投递；其它情况遍历所有团队找 `to` 这个 member 所在团队投递；都没找到返 `recipient '%s' not found in any team` IsError。
 - `TeamCreateTool.Execute`：`team_name` 必填；同名时追加 `-2/-3/...` 后缀去重；调 `detectBackend()` + `TeamMgr.CreateTeam`；Output 提示用户用 `Agent` 工具带 `team_name` 加成员。
 - `TeamDeleteTool.Execute`：`team_name` 必填；不存在返 IsError；调 `TeamMgr.DeleteTeam`（内部 `StopMember` 每个成员）；返回停掉的成员清单。
- [ ] 完成

## T13: 实现 AgentTool.runAsTeammate
- 影响文件: `internal/agents/agent_tool.go`（`AgentTool.TeamMgr` 字段 @ 71；`team_name` 入口分支 @ 214 + 239-240；`runAsTeammate` @ 611-709；`drainTeammateEvents` @ 714-)
- 依赖任务: T8, T9（ch13 的 T1-T11）
- 完成标准:
 - `AgentTool` 新增 `TeamMgr *teams.TeamManager` 字段；
 - `Execute` 解析 `team_name` 参数后，当 `teamName != "" && TeamMgr != nil` 即走 `runAsTeammate`，先于 fork / runAsync / runSync 分发；
 - `runAsTeammate` 校验团队存在、同 team 同名报错；空 name 时 `sanitizeSlugSegment(description)` 生成；可选 `subagent_type` 解析 spec 跑 `FilterToolsForAgent`，无 spec 时把全 registry 给队员；
 - `isolation=worktree` 时 `worktree.CreateAgentWorktree(slug)` 建独立 worktree、把 `BuildWorktreeNotice` 拼到 prompt 顶端；
 - 调 `teams.BuildTeammateAddendum` 生成 addendum；调 `teams.SpawnTeammate` 拿 `SpawnResult`；
 - in-process 模式启 goroutine `drainTeammateEvents` 消费事件流，把 `ToolResultEvent` / `ErrorEvent` 翻译成 `SubAgentProgress` 喷进 `ProgressCh` 防止生产者阻塞；
 - Output 含 backend hint 和 SendMessage 使用提示。
- [ ] 完成

## T14: 实现 cmd/mewcode --teammate worker 模式
- 影响文件: `cmd/mewcode/main.go`（teammate flag 早期拦截 @ 19-25）；`cmd/mewcode/teammate.go`（`teammateArgs` @ 22-25；`parseTeammateFlags` @ 37-61；`runTeammate` @ 68-121；`builtinTeammateTools` @ 126-135；`streamEventsToStderr` @ 140-163）
- 依赖任务: T1, T6, T8, T9, T10, T12
- 完成标准:
 - `main.go` 在加载 config 之前先调 `parseTeammateFlags(os.Args[1:])`，命中 `--teammate` 则走 `runTeammate` 不进 TUI；
 - `parseTeammateFlags` 仅识别 `--teammate / --team-name / --agent-name` 三个 flag，必须以 `--teammate` 起首；
 - `runTeammate` 校验 team-name / agent-name 必填；加载同一 config 取第一个 provider 创建 `llm.Client`；
 - 注册的工具集是 worker 白名单（`ReadFile / WriteFile / EditFile / Bash / Glob / Grep` + 自己的 `SendMessage`），**不含** `TeamCreate / TeamDelete`；
 - 用 `teams.NewTeam(name, ModeInProcess)` 在本进程构造 Team 对象（指向同一个 mailbox 目录，因为 `teamsBaseDir` 解析的是相同 wd），通过 `CreateTeamWith` 注册到本进程 TeamMgr；
 - 跑 `RunInProcessTeammate`，事件 channel 走 `streamEventsToStderr` 把 StreamText / ToolUseEvent / ToolResultEvent / ErrorEvent / LoopComplete 喷到 stderr；
 - 接 SIGINT/SIGTERM 调 cancel 优雅退出；
 - 不传 initialPrompt（保持 ""），让队员第一次 idle poll 从 mailbox 拿初始任务避免重复注入。
- [ ] 完成

## T15: TUI 接入
- 影响文件: `internal/tui/tui.go`（`teamMgr *teams.TeamManager` 字段 @ 196；`coordinatorToolFilter` @ 593-603；`registerAgentTools` 内 `teams.NewTeamManager()` @ 616 + 字段写回 @ 617 + 注册三个工具 @ 646-648 + `AgentTool.TeamMgr` 注入 @ 658；`DrainLeadMailbox` 接入 notification 队列 @ 545；`ag.ToolNameFilter = coordinatorToolFilter(m.teamMgr)` 两处接线 @ 387 + 1132）
- 依赖任务: T7, T11, T12, T13
- 完成标准:
 1. `Model.teamMgr` 字段在 tui.go:196 声明；
 2. `coordinatorToolFilter` 闭包：`teamMgr == nil` 返 nil（关闭过滤）；`len(teamMgr.ListTeams()) == 0` 时每轮放行所有工具；否则 `teams.IsCoordinatorTool(name)` 判定；
 3. `registerAgentTools` 里创建 `TeamManager` → 把 `TeamCreateTool / TeamDeleteTool / SendMessageTool` 注册到 registry → `AgentTool.TeamMgr` 注入；
 4. `gatherNotifications`（Lead 每轮迭代的开头钩子）调 `teams.DrainLeadMailbox(m.teamMgr)` 把 `<team-notification>` 字符串数组拼到要喂给模型的消息中；
 5. 主 Agent 初始化（`initSingleProviderMsg`）和恢复会话（`restoreSession`）两条路径都设 `ag.ToolNameFilter = coordinatorToolFilter(m.teamMgr)`。
- [ ] 完成

## T16: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T1-T15
- 完成标准:
 - `go build ./...` 通过；
 - `go test ./internal/teams/...` 全部测试通过（`teams_test.go` 8 个 + `runner_test.go` 多个，覆盖 FileMailBox roundtrip、并发、CRUD、detectBackend 三档优先级、SendMessage to=lead 路由、SendMessage unknown sender、CreateIdleNotification、IsShutdownRequest、formatInboundAsPrompt、waitForNextPromptOrShutdown 三条退出路径、DrainLeadMailbox 多团队、BuildTeammateCLI、ShellQuote、SpawnTeammate 校验、recordExternalMember）；
 - `go test ./cmd/mewcode/...` 通过（`teammate_test.go` 覆盖 parseTeammateFlags 的命中 / 未命中 / 缺参数三种情况）；
 - 主流程接线验证：`grep -n "teamMgr\|teams\." internal/tui/tui.go` 命中所有上文列出的接入点；`grep -n "TeamMgr" internal/agents/agent_tool.go` 看到 `runAsTeammate` 分支被 Execute 调用。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15 / [ ] T16
```
```plain
# ch15: AgentTeam Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 类型 `Team` 在 `internal/teams/teams.go:43-49` 存在，字段含 `Name / Mode / Members map / MailBox / mu sync.Mutex`
- [ ] 类型 `Member` 在 `internal/teams/teams.go:32-41` 存在，字段含 `Name / AgentRef / Conv / Active / Cancel / PaneID`（外部后端句柄）
- [ ] 类型 `TeamMode` 在 `internal/teams/teams.go:17` 存在，常量 `ModeInProcess / ModeTmux` 在 `teams.go:19-22`，`ModeITerm` 在 `iterm.go:11`（与后端代码同文件保持内聚）
- [ ] 类型 `TeamManager` 在 `internal/teams/teams.go:126-129` 存在，方法集含 `CreateTeam / CreateTeamWith / GetTeam / DeleteTeam / ListTeams / CloseAll`
- [ ] 类型 `FileMailBox` 在 `internal/teams/filemailbox.go:11-13` 存在；`FileMailMessage` 在 `:15-22` 含 6 字段 `From / Text / Timestamp / Read / Color / Summary`
- [ ] 类型 `TeammateSpawnConfig / SpawnResult` 在 `internal/teams/spawn.go:23-43` 存在
- [ ] 常量 `LeadName = "lead"` / `ShutdownPrefix = "[shutdown]"` / `IdlePollInterval = 500 * time.Millisecond` 在 `internal/teams/runner.go:16-25`
- [ ] `CoordinatorAllowedTools` map 在 `internal/teams/coordinator.go:13-26` 含 12 项白名单（写工具被排除）
- [ ] `RunInProcessTeammate` 在 `internal/teams/runner.go:60-123` 主循环六步齐全：ctx 检查 → InjectPendingMessages → AddUserMessage → agent.Run + 事件转发 → idle 通知 → waitForNextPromptOrShutdown 轮询
- [ ] `withLock` 在 `filemailbox.go:71-111` 使用 `O_CREATE|O_EXCL` 锁文件，10 次重试，>10s 过期清理
- [ ] `BuildTeammateCLI` 在 `spawn.go:149-164` 输出 `cd <quoted_wd> && <quoted_exe> --teammate --team-name <quoted> --agent-name <quoted>`，`shellQuote` 单引号转义 POSIX 标准
- [ ] `BuildTeammateAddendum` 在 `inprocess.go:55-66` 文本包含 "you are a member of team"、"Lead is reachable as 'lead'"、"deliver your final result to the lead with SendMessage"、"messages from the team arrive as system reminders" 四个关键信息
- [ ] `DrainLeadMailbox` 在 `runner.go:169-199` nil 安全（`mgr == nil` 返 nil）、读完邮件后调 `MarkAllRead`、输出格式为 `<team-notification team="X">\n...\n</team-notification>`
- [ ] `SendMessageTool.Execute` 在 `tools.go:44-91` 把 `to == LeadName` 单独走"查发送者所在团队"路径（Lead 不是 Member）
- [ ] `TeamCreateTool.Execute` 在 `tools.go:125-145` 同名冲突自动追加 `-2/-3/...` 后缀去重
- [ ] `AgentTool.runAsTeammate` 在 `internal/agents/agent_tool.go:611-709` 五件事齐全：查团队、查重名、解析 spec + 工具池、可选 worktree、SpawnTeammate + drainTeammateEvents

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -n "teams.NewTeamManager\|TeamMgr:" internal/tui/tui.go` 在 `internal/tui/tui.go:616` 找到 `teams.NewTeamManager()` 调用方
- [ ] `grep -n "TeamCreateTool\|TeamDeleteTool\|SendMessageTool" internal/tui/tui.go` 在 `internal/tui/tui.go:646-648` 找到三个工具注册点
- [ ] `m.registry.Register(&agents.AgentTool{...TeamMgr: teamMgr...})` 注入点在 `internal/tui/tui.go:649-661`
- [ ] `teams.DrainLeadMailbox(m.teamMgr)` 调用点在 `internal/tui/tui.go:545`（`gatherNotifications`），把 `<team-notification>` 注入下一轮系统提示
- [ ] `ag.ToolNameFilter = coordinatorToolFilter(m.teamMgr)` 接线在两处：`internal/tui/tui.go:387`（初始化）+ `internal/tui/tui.go:1132`（恢复会话）
- [ ] `coordinatorToolFilter` 函数定义在 `internal/tui/tui.go:593-603`，三段语义：nil → 关闭过滤；空团队 → 放行全部；非空 → `IsCoordinatorTool`
- [ ] `Model.teamMgr` 字段在 `internal/tui/tui.go:196` 声明
- [ ] `cmd/mewcode/main.go:19-25` 在加载 config 之前先 `parseTeammateFlags`，命中 `--teammate` 走 `runTeammate` 跳过 TUI
- [ ] `cmd/mewcode/teammate.go:97` 注册队员侧 `SendMessageTool{TeamMgr: teamMgr, SenderName: args.memberName}`（worker 进程也有 SendMessage 工具）
- [ ] `cmd/mewcode/teammate.go:120` 调 `teams.RunInProcessTeammate` 作为 worker 进程主循环
- [ ] `cmd/mewcode/teammate.go:113` 调 `teams.BuildTeammateAddendum` 注入到 worker 端 conversation

## 3. 编译与测试

- [ ] `go build ./...` 通过
- [ ] `go test ./internal/teams/...` 通过（覆盖至少 16 个用例：FileMailBoxRoundTrip / FileMailBoxConcurrentSends / TeamManagerCRUD / DetectBackendFallback / DetectBackendPrefersTmuxWhenInside / DetectBackendPicksITermWhenInside / SendMessageToolRoutesToLead / SendMessageToolUnknownSenderToLead / IsShutdownRequest / CreateIdleNotification / FormatInboundAsPromptEmpty / FormatInboundAsPromptMultiple / WaitForNextPromptOrShutdownShutdown / WaitForNextPromptOrShutdownMessage / WaitForNextPromptOrShutdownCancel / DrainLeadMailbox / DrainLeadMailboxNilSafe / BuildTeammateCLIFormat / SpawnTeammateValidation / RecordExternalMember / ShellQuote）
- [ ] `go test ./cmd/mewcode/...` 通过（`teammate_test.go` 覆盖 parseTeammateFlags 三种情况：未命中 / 命中 + 完整参数 / 命中 + 缺参数）
- [ ] `go vet ./...` 无警告
- [ ] 测试运行不在仓库根残留 `.mewcode/teams/` 目录（`TestMain` 走 `MEWCODE_TEAMS_DIR` 重定向到 tmp）

## 4. 端到端验证

- [ ] 注册路径：TUI 启动后 `registerAgentTools` 在 `tui.go:616-648` 创建 `TeamManager` 并把 `TeamCreate / TeamDelete / SendMessage` 三件套放入 registry；用户向 Lead 说 "create a team to refactor X" → LLM 调 `TeamCreate(team_name="refactor-X")` → `detectBackend()` 选模式 → Output 返回 "Team refactor-X created (mode: ...). Use Agent tool with team_name=..."
- [ ] Spawn 路径：Lead 继续说 "spawn alice to do data layer" → LLM 调 `Agent(team_name="refactor-X", name="alice", prompt="...")` → `AgentTool.Execute` 识别 `team_name` 分支调 `runAsTeammate` → `SpawnTeammate(ModeInProcess|ModeTmux|ModeITerm)` → 队员开始干活
- [ ] 通信路径：队员 alice 通过 `SendMessage(to="bob", content="...")` 给 bob 写 mailbox → bob 下一轮 idle poll / inject pending → 收到消息作为 system reminder
- [ ] Lead 感知路径：每个队员 turn 结束写 idle 通知到 Lead 邮箱 → Lead 下一轮迭代 `gatherNotifications` 调 `DrainLeadMailbox` 抽出 `<team-notification team="refactor-X">\nfrom=alice: [idle] alice (reason: available)\n</team-notification>` 注入 Lead 上下文
- [ ] Coordinator Mode 路径：团队存活期间 `ag.ToolNameFilter = coordinatorToolFilter(m.teamMgr)` 让 Lead 每轮工具集只剩 12 项白名单，调用 `WriteFile` / `EditFile` 会被过滤拒绝；`TeamDelete` 清空所有团队后下一轮恢复全工具集
- [ ] Tmux 后端：`TMUX` env 非空时 `detectBackend` 返 `ModeTmux` → spawn 时先把 task 写 mailbox → `tmux new-window -d` 拉起新窗口跑 `mewcode --teammate ...` → 子进程 `parseTeammateFlags` 命中 → `runTeammate` 加载同一 mailbox 目录 → 第一次 idle poll 拿到初始任务开始干活
- [ ] iTerm 后端：`ITERM_SESSION_ID` 非空 + 不在 tmux 时 `detectBackend` 返 `ModeITerm` → `osascript` 创建 iTerm tab 跑同样命令
- [ ] 关闭路径：`TeamDelete(team_name="refactor-X")` → `TeamMgr.DeleteTeam` → 遍历 `team.StopMember` 按 `Mode + PaneID` 分发 tmux 关 window / iTerm 关 tab / in-process 取消 context → 全部清理后 Lead 下轮恢复全工具集

## 5. 文档

- [ ] `specs/go/ch15/spec.md` 已写
- [ ] `specs/go/ch15/tasks.md` 已写，16 个 T 全部勾完
- [ ] `specs/go/ch15/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch15` 与三件套关闭状态（待用户确认后由人或 CI 触发）
```

### Python

```plain
# ch15: AgentTeam Spec

## 1. 背景

SubAgent（ch13）解决了一次性子任务的上下文隔离，但拓扑是星型：所有子 Agent 只能和主 Agent 通信，子 Agent 之间彼此看不见。当任务规模上来——四个模块同时重构、多角度并行调查 bug、一个 Agent 需要把发现告诉另一个——星型拓扑下主 Agent 成了信息中转瓶颈，子任务被迫串行。这一章把"长期协作团队"做成 MewCode 的一等概念：多个 Agent 组成 Team，并行干活、直接互发消息、共享任务列表和邮箱，主 Agent 可选切换为 Coordinator Mode 专职调度。

## 2. 目标

提供 `AgentTeam` / `TeammateInfo` / `TeamManager` / `Mailbox` / `SharedTaskStore` / `AgentNameRegistry` 一整套数据结构与服务，并暴露 `SendMessageTool` / `TeamCreateTool` / `TeamDeleteTool` 三个工具，让 LLM 在对话里：1) 调 `TeamCreate` 建团队（按环境自动选 tmux / iterm2 / in-process 后端，并在 `~/.mewcode/teams/<name>/` 落盘 config.json + tasks.json + mailbox/），2) 调 `Agent` 工具带 `team_name` 把队员 spawn 进团队（独立 worktree + 受限工具池），3) 队员之间通过 `SendMessage` 走 `Mailbox` 互发消息、按名字或 agent_id 寻址、支持 `to="*"` 广播，4) Lead 每轮迭代开头 `_consume_mailbox` 把收件箱里的消息转 user message 注入对话，5) 启用 `enable_coordinator_mode` 后 Lead 通过 `apply_coordinator_filter` 把工具集收窄到 12 项白名单。Tmux / iTerm2 后端时新 pane 由 `build_cli_command` 拼出 `mewcode -p` 命令字符串，通过 `MEWCODE_TEAM_NAME` / `MEWCODE_TEAMMATE_NAME` / `MEWCODE_MAILBOX_DIR` 环境变量与 Lead 共享同一份 mailbox 目录。

## 3. 功能需求

- F1: `BackendType` 枚举三档 `TMUX="tmux"` / `ITERM2="iterm2"` / `IN_PROCESS="in-process"`；`detect_backend(teammate_mode, is_interactive)` 按 `teammate_mode == "in-process" or not is_interactive` → `TMUX env` → `TERM_PROGRAM == "iTerm.app" + it2 可执行` → `tmux 可执行` 的优先级自动选择；都不命中抛 `BackendDetectionError` 而非静默回退（保证用户不会在不知情下失去进程隔离）。
- F2: `AgentTeam` dataclass 持有 `name / lead_agent_id / members: list[TeammateInfo] / config_path / description`，可 `to_dict` / `from_dict` / `save` / `load`；`get_member(name)` 同时按 `name` 或 `agent_id` 查找；`set_member_active(name, is_active)` 翻转活跃标志；`all_idle()` 返回所有成员是否都为 `is_active is False`。
- F3: `TeammateInfo` dataclass 字段 `name / agent_id / agent_type / model / worktree_path / backend_type / is_active`，`is_active: bool | None = None` 三值语义：`None` 或 `True` 表示活跃，`False` 表示空闲；删除直接从 members 列表移除不留墓碑。
- F4: `TeamManager` 提供 `detect_backend` / `create_team` / `get_team` / `get_task_store` / `get_mailbox` / `register_member` / `set_member_idle` / `register_inprocess_handle` / `register_pane_id` / `get_pane_id` / `delete_team` / `get_team_for_teammate` / `on_teammate_completed` 共 13 个公开方法；内部维护 `_teams` / `_task_stores` / `_mailboxes` / `_inprocess_handles` / `_pane_ids` / `_teammate_team_map` / `_detected_backend` 七个字典/缓存；`_detected_backend` 第一次检测后缓存复用。
- F5: `Mailbox` 基于 `<base_dir>/<agent_id>/<timestamp>_<id>.json` 单文件单消息模型：`write(agent_id, msg)` 落盘 ；`read(agent_id)` 只读不删；`consume(agent_id)` 读完立刻 `f.unlink()`；`broadcast(team_members, msg, exclude)` 按列表逐个 write 排除 exclude；`cleanup(agent_id)` / `cleanup_all()` 清空目录。
- F6: `MailboxMessage` 字段 `id / from_agent / to_agent / content / summary / message_type / timestamp / metadata`；`message_type` 三档 `text / shutdown_request / shutdown_response` 由 `SendMessageTool.VALID_MESSAGE_TYPES` 守门；`text` 类型必须带非空 `summary`（5-10 词）否则报错。
- F7: `create_message(from_agent, to_agent, content, summary, message_type, metadata)` 统一构造器，自动填 `id=uuid4().hex[:12]` 和 `timestamp=time.time()`。
- F8: `SharedTaskStore` 基于单文件 `tasks.json`，结构 `{"next_id": int, "tasks": [...]}`；`create / get / list_tasks / update / init_empty` 五个方法；`SharedTask` 字段 `id / title / description / status / assignee / blocks / blocked_by / created_by`，`status` 四档 `pending / in_progress / completed / blocked`。
- F9: `AgentNameRegistry` 进程内单例（线程安全 double-checked locking）；`register(name, agent_id)` / `resolve(name_or_id)`（先按 name 查再按 id 反查）/ `unregister(name)` / `list_all()` / `reset()` 五个方法。
- F10: `TeamManager.create_team(name, lead_agent_id, description, teammate_mode, is_interactive)` 调 `detect_backend` 决定后端 → `unique_team_name` 自动加 `-2/-3/...` 后缀避免同名 → 在 `~/.mewcode/teams/<slug>/` 建目录 → 写 config.json + tasks.json + mailbox/ → 缓存到 `_teams` / `_task_stores` / `_mailboxes`。
- F11: `TeamManager.delete_team(team_name)` 先校验所有成员都 idle（`is_active is False`），否则报 `Cannot delete team: active members: ...`；通过后遍历每个 member：unregister 名字、cancel in-process handle、kill pane、git worktree remove、trace manager remove；最后 cleanup mailbox + 删团队目录 + 弹出三个缓存字典。
- F12: `spawn_inprocess_teammate(agent, prompt, name, conversation)` 用 `asyncio.create_task` 起协程跑 `agent.run_to_completion`，返 `InProcessTeammateHandle{agent, task, name}`；`handle.done` 判完成、`handle.result` 安全取结果、`handle.cancel()` 取消未完成 task。
- F13: `spawn_tmux_teammate` 三级 fallback：先尝试 `split-window -h -t <team_name>` → 失败则 `new-window` + `split-window` → 再失败则 `new-session -d` + `list-panes`；用 `build_cli_command` 拼出 `MEWCODE_TEAM_NAME=X MEWCODE_TEAMMATE_NAME=Y MEWCODE_MAILBOX_DIR=Z mewcode -p --work-dir <wt> '<prompt>'` 字符串，prompt 内单引号转义为 `'\''`；最后 `send-keys -t <pane> <cmd> Enter` 启动；`kill_pane(pane_id)` best-effort 静默失败。
- F14: `spawn_iterm2_teammate` 复用 `build_cli_command`，通过 `it2 split-pane --command "/bin/zsh -c '<cmd>'"` 创建新 pane 返回 `ITermPaneInfo{session_id}`。
- F15: `save_transcript(team_name, agent_id, conv)` / `load_transcript(team_name, agent_id)` 把 `ConversationManager.history`（含 tool_uses / tool_results 块）序列化为 JSON 落到 `~/.mewcode/teams/<team>/transcripts/<agent_id>.json`，加载时 `env_injected = ltm_injected = True` 防止重复注入。
- F16: `Agent._consume_mailbox(conversation)` 在每轮迭代开头钩入：仅当 `self.team_name and self._team_manager` 非空时取 mailbox.consume 自己的 agent_id；每条消息前缀 `[Message from <sender>] ` 或 `[<message_type> from <sender>] ` 后 `conversation.add_user_message`；异常吞掉记 debug。
- F17: `TeamCreateTool` 暴露 `team_name` 必填 + `description` 可选；调 `detect_backend` 不通过返 IsError；通过后 `team_manager.create_team`；如 `is_coordinator_mode(enable_coordinator_mode)` 返 true 则把 `parent_agent.coordinator_mode = True`、备份 `_full_registry`、把 `parent_agent.registry = apply_coordinator_filter(registry)`，输出附带 "Coordinator Mode activated" 提示。
- F18: `TeamDeleteTool` 暴露 `team_name` 必填；调 `team_manager.delete_team` 捕获 `TeamError` 返 IsError；如 `parent_agent.coordinator_mode` 为 true 则恢复 `_full_registry` 并清零 flag，输出附带 "Coordinator Mode deactivated" 提示。
- F19: `SendMessageTool` 暴露 `to / message / summary / message_type / metadata`；先校验 `message_type in VALID_MESSAGE_TYPES`，再校验 `text` 类型必须有 `summary`；`to == "*"` 走 `mailbox.broadcast(member_ids ∪ {lead_agent_id} \ {self})`，否则用 `AgentNameRegistry.instance().resolve(to)` 解析目标 id；写完后 `_wake_pane(target_id)` 向 tmux pane send-keys 空行触发新消息读取（pane 后端唤醒机制）。
- F20: `AgentTool._execute_as_teammate(p)` 处理 `team_name != None` 分支：校验 team 存在、按 base_name 同名冲突自动加 `-2/-3/...`、可选解析 `subagent_type` 否则 fork、`worktree_manager.create(f"team-{team_name}/{teammate_name}", "HEAD")` 建独立 worktree、`build_teammate_tools` 按 backend 类型构造队员工具池（in-process 严格白名单 / pane 模式只剔除 `TeamCreate` 和 `TeamDelete`）、`register_member` 注册到团队 + AgentNameRegistry、按 backend 分发 `spawn_inprocess_teammate` 或 `_spawn_pane_teammate`。

## 4. 非功能需求

- N1: `Mailbox` 单文件单消息模型避免跨进程并发写覆盖：每条消息文件名 `<timestamp>_<id>.json` 全局唯一，写入无需文件锁；`consume` 按 `sorted(d.iterdir())` 时间排序保证 FIFO；`unlink` 单文件操作在 POSIX 文件系统上原子，不会丢消息。
- N2: `detect_backend` 检测失败不静默回退到 in-process——直接抛 `BackendDetectionError` 让用户显式选择：要么装 tmux / iTerm2+it2，要么在 config.yaml 设 `teammate_mode: "in-process"`。理由是 pane 后端提供的进程隔离是团队模式的核心保障，静默降级会让用户失去隔离能力还不自知。
- N3: `AgentNameRegistry` 是进程内单例，因此跨进程的 pane teammate 必须自己在子进程内重新注册名字 → agent_id 映射，不能依赖 Lead 进程的注册表；`resolve` 同时支持按 name 和按 agent_id 反查，给 Lead 端 SendMessage 用名字、给子进程端用 agent_id 都能命中。
- N4: `TeamManager._detected_backend` 一旦检测过就缓存，整个 team manager 生命周期内不变。同进程内多次 `create_team` 不会重新探测环境——保证一致性，避免中途装 tmux 导致前后行为不一致。
- N5: `_consume_mailbox` 必须放在 Agent 每轮迭代开头（在调 LLM 之前），不能放在迭代结束：放结束会让"工具调用完成 → idle → 下轮才看到新消息"出现一轮延迟；放开头保证 LLM 看到的对话历史里已经包含队员的最新消息，决策不滞后。
- N6: `TeamCreateTool` 启用 Coordinator Mode 时必须把原 `registry` 备份到 `parent_agent._full_registry`，`TeamDeleteTool` 恢复时从这里读回——不能依赖重新构造，因为 registry 里可能已经注入了运行时动态注册的工具（MCP / Skill）。
- N7: `SendMessageTool` 的 `_wake_pane` 在 pane teammate 场景必须 send-keys 触发新消息读取（pane 进程在 `mewcode -p` 单次执行模式下会阻塞在 stdin），否则消息只是写入 mailbox 但对方进程感知不到；in-process teammate 不需要 wake 因为同进程 `_consume_mailbox` 每轮自动跑。
- N8: `build_cli_command` 把 `prompt` 内的单引号转义为 `'\''`（关闭→插入字面单引号→重开），否则 prompt 里出现单引号会破坏 shell 解析；前缀环境变量 `MEWCODE_TEAM_NAME` / `MEWCODE_TEAMMATE_NAME` 通过空格分隔但不加引号，假设值是合法标识符。
- N9: `delete_team` 必须先校验所有 member `is_active is False`，活跃成员存在时拒绝删除——避免运行中的 in-process 协程或 pane 进程突然失去 mailbox 后悬挂。Active 检查用 `is_active is not False`（`None` 和 `True` 都算 active）。
- N10: 测试运行 `Mailbox` 和 `AgentTeam.save` 必须 `monkeypatch / patch("mewcode.teams.models.Path.home", ...)` 重定向 home 到 `tmp_path`，否则跑完测试会在用户主目录残留 `~/.mewcode/teams/` 目录污染。
- N11: `AgentNameRegistry.reset()` 在 pytest fixture 中 autouse 调用——单例在用例间共享会让 register 状态泄漏，导致 `test_register_and_resolve` 后跑的用例看到上个用例的残留映射。
- N12: `spawn_iterm2_teammate` 通过外部 `it2` CLI 而非直接 osascript——it2 是 iTerm2 官方提供的稳定 CLI，比 osascript 字符串拼接的 AppleScript 更可靠且支持版本演进。

## 5. 设计概要

- 核心数据结构:
 - `AgentTeam`：团队聚合 dataclass，`members: list[TeammateInfo]` 列表非 map（队员数不大，遍历足够），通过 `config_path` 持久化到 `~/.mewcode/teams/<slug>/config.json`。
 - `TeammateInfo`：队员元信息 dataclass，`is_active: bool | None` 三值语义；`agent_id` 是全局唯一进程标识；`worktree_path` 关联到 ch14 的 worktree。
 - `TeamManager`：全局团队注册表 + 多类资源缓存（mailbox / task store / inprocess handle / pane id / teammate→team 反查映射），是 Lead 进程的"团队服务总线"。
 - `Mailbox` + `MailboxMessage`：单文件单消息模型，靠时间戳前缀文件名保证 FIFO 且跨进程写入无冲突；支持 `text / shutdown_request / shutdown_response` 三种类型。
 - `SharedTaskStore` + `SharedTask`：JSON 文件实现的共享任务列表，团队内所有成员通过 `team_manager.get_task_store(team_name)` 读到同一份。
 - `AgentNameRegistry`：进程内单例（线程安全 double-checked），把人类可读的 name 映射到 agent_id，给 SendMessage 寻址用。
 - `InProcessTeammateHandle`：包装 `asyncio.Task`，供 `TeamManager` 跟踪 in-process 队员生命周期。
- 主流程（按生命周期）:
 - 创建：用户消息 → 主 Agent → LLM 调 `TeamCreate(team_name="X")` → `team_manager.detect_backend()` 选模式 → `team_manager.create_team` 在 `~/.mewcode/teams/x/` 落 config.json + tasks.json + mailbox/ → 可选切 Coordinator Mode（备份 `_full_registry` + `apply_coordinator_filter`）。
 - Spawn 队员：Lead LLM 调 `Agent(team_name="X", name="alice", prompt="...")` → `AgentTool.execute` 看到 `team_name` 非空走 `_execute_as_teammate` → 校验团队、解析子 agent type / fork、`worktree_manager.create` 建独立 wt、按 backend 调 `build_teammate_tools` 构造工具池、`register_member` 注册到团队 + `AgentNameRegistry.instance().register`。
 - In-process：`spawn_inprocess_teammate(agent, prompt, name)` 起 `asyncio.create_task` 跑 `agent.run_to_completion`，handle 注册到 `team_manager._inprocess_handles`。
 - Pane 后端：`spawn_tmux_teammate` / `spawn_iterm2_teammate` 用 `build_cli_command` 拼出带 `MEWCODE_TEAM_NAME` / `MEWCODE_TEAMMATE_NAME` / `MEWCODE_MAILBOX_DIR` env 的 `mewcode -p` 命令字符串 → tmux send-keys / it2 split-pane 启动 → pane_id 注册到 `team_manager._pane_ids`。
 - 通信：队员调 `SendMessage(to="bob", message="...", summary="...")` → `AgentNameRegistry.resolve("bob")` → target_id → `mailbox.write(target_id, msg)` → `_wake_pane(target_id)`（pane 队员需要）→ 对方下一轮 `_consume_mailbox` 拿到。
 - Lead 感知：每轮 Lead `agent.run_to_completion` 内部 `_consume_mailbox(conversation)` 把 `mailbox.consume(self.agent_id)` 的所有消息转 user message 注入 conversation，前缀 `[Message from X] ` 或 `[shutdown_request from X] `。
 - Idle 通知：`AgentTool` 后台任务完成回调 `team_manager.on_teammate_completed(agent_id)` → `set_member_idle` 把 `is_active=False` + 写一条 `"Teammate 'X' is now idle"` 到 Lead 邮箱。
 - Coordinator Mode：`apply_coordinator_filter(registry)` 把工具集筛到 `COORDINATOR_MODE_ALLOWED_TOOLS` 12 项 `{Agent, SendMessage, TaskCreate, TaskGet, TaskList, TaskUpdate, TeamCreate, TeamDelete, ReadFile, Glob, Grep, Bash}`（写工具 `WriteFile / EditFile` 被排除）；`TeamDeleteTool` 恢复 `_full_registry`。
 - Stop：`TeamDelete(team_name="X")` → `team_manager.delete_team` → 校验全员 idle → 遍历每个 member：unregister name、cancel handle、kill pane、git worktree remove、trace_manager.remove → cleanup mailbox + 删团队目录 + 弹出三个缓存。
- 调用链（模块层级）:
 - `mewcode/app.py:730-762` 在 `MewCodeApp.__init__` 后段创建 `TeamManager(worktree_manager, trace_manager)`，把 `team_manager` 注入 `AgentTool`，把 `TeamCreateTool / TeamDeleteTool / SyntheticOutputTool` 注册进 registry，把 `agent._team_manager = team_manager` 写回主 Agent。
 - `mewcode/agent.py:324-326` 主 Agent `__init__` 声明 `self.coordinator_mode / self.team_name / self._team_manager` 三个字段；`:433 / :957` 在 `run_to_completion` 主循环开头调 `self._consume_mailbox(conversation)`；`:471 / :937` 给 `build_system_prompt` 传 `coordinator_mode=self.coordinator_mode` 切提示词。
 - `mewcode/tools/agent_tool.py:86-87` `execute` 入口看到 `p.team_name` 非空时优先走 `_execute_as_teammate`（先于 fork / sync / async 分发）；`:246-414` 实现完整队员 spawn 流程。
- 与其他模块的交互:
 - 依赖 `mewcode/agent`（Agent 实例 / `run_to_completion` / 系统提示注入）、`mewcode/conversation`（ConversationManager / Message / ToolUseBlock / ToolResultBlock）、`mewcode/agents/tool_filter`（`apply_coordinator_filter` / `build_teammate_tools` / `COORDINATOR_MODE_ALLOWED_TOOLS` / `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`）、`mewcode/worktree`（每个队员独立 worktree）、`mewcode/tools/base`（Tool / ToolResult / ToolRegistry）。
 - 被 `mewcode/app.py`（注册三件套工具 + 写回 `agent._team_manager`）、`mewcode/tools/agent_tool.py`（`_execute_as_teammate` 调 spawn / register）、`mewcode/prompts.py`（`build_system_prompt(coordinator_mode=...)` 切系统提示词）调用。

## 6. Out of Scope

- 不实现 PR 文档里描述的 `planModeRequired` 字段和审批工作流——`TeammateInfo` 只保留基础元信息，审批门槛由后续章节扩展。
- 不实现 `shutdown_response` 完整双向握手协议——只保留 `message_type` 字段的三档枚举，握手语义由 LLM 在文本层约定。
- 不实现共享任务依赖图的拓扑排序自动调度——`SharedTask.blocks / blocked_by` 字段已存但 store 仅做 CRUD，依赖推断由 Lead LLM 从任务列表文本自己读出。
- 不实现"队员后从磁盘恢复对话续写"机制——in-process 队员 task 完成或 cancel 后即终止，transcript 落盘仅供事后回看，不支持 resume；要 Lead 想再用需要重新 spawn。
- 不实现"协调模式四阶段工作流"强制约束（Research / Synthesis / Implementation / Verification）——`get_coordinator_system_prompt` 写入提示词层引导，但工具层不强制顺序。
- 不实现 `MEWCODE_COORDINATOR_MODE` 自动激活——必须 `enable_coordinator_mode=True` 配合 env var 双开关同时打开才生效，避免 Lead 进程被意外切到协调模式。
- 不实现 mailbox 的跨节点分布式同步——团队只在单机内运作，所有 mailbox 文件在本地 `~/.mewcode/teams/<name>/mailbox/` 下；要跨机协作需要外部传输层。
- 不实现 worker pane 进程的自动重启——pane 进程 crash 后 Lead 端 `pane_id` 仍记录但实际 pane 已死；用户需手动 `TeamDelete` 然后重建。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch15: AgentTeam Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 BackendType / TeammateInfo / AgentTeam 三个核心模型
- 影响文件: `mewcode/teams/models.py`（`BackendType` @ 10-13；`TeammateInfo` @ 16-31；`_sanitize_name` @ 34-37；`AgentTeam` @ 40-102；`resolve_team_dir` @ 105-107；`unique_team_name` @ 110-117）
- 依赖任务: 无
- 完成标准: `BackendType(str, Enum)` 三档常量 `TMUX / ITERM2 / IN_PROCESS`；`TeammateInfo` dataclass 7 字段含 `is_active: bool | None = None` 三值；`AgentTeam` 含 `get_member` / `add_member` / `remove_member` / `set_member_active` / `all_idle` / `active_members` / `to_dict` / `from_dict` / `save` / `load`；`get_member` 按 name 或 agent_id 双向查找；`resolve_team_dir` 落到 `~/.mewcode/teams/<slug>/`；`unique_team_name` 同名冲突自动加 `-2/-3/...` 后缀。
- [ ] 完成

## T2: 实现 Mailbox + MailboxMessage（单文件单消息）
- 影响文件: `mewcode/teams/mailbox.py`（`MailboxMessage` @ 11-27；`Mailbox` @ 30-102；`create_message` @ 105-122）
- 依赖任务: 无
- 完成标准: `MailboxMessage` 8 字段含 `id / from_agent / to_agent / content / summary / message_type / timestamp / metadata`；`message_type` 注释三档 `text | shutdown_request | shutdown_response`；`Mailbox.write` 以 `<timestamp>_<id>.json` 为文件名落到 `<base>/<agent_id>/` 目录；`read` 只读不删按 `sorted(d.iterdir())` 时间序；`consume` 读完立刻 `f.unlink()` 保证 FIFO；`broadcast(team_members, msg, exclude)` 逐个 write 排除 exclude；`cleanup` / `cleanup_all` 清目录；`create_message` 自动填 `uuid4().hex[:12]` 和 `time.time()`。
- [ ] 完成

## T3: 实现 detect_backend 优先级链
- 影响文件: `mewcode/teams/backend_detect.py`（`BackendDetectionError` @ 9-10；`_in_tmux_session` @ 13-14；`_in_iterm2` @ 17-18；`_it2_available` @ 21-22；`_tmux_installed` @ 25-26；`detect_backend` @ 29-51）
- 依赖任务: T1
- 完成标准: 优先级 `teammate_mode == "in-process" or not is_interactive` → `TMUX` env → `TERM_PROGRAM == "iTerm.app" + shutil.which("it2")` → `shutil.which("tmux")`；都不命中抛 `BackendDetectionError` 而非静默回退；错误消息含 `tmux: brew install tmux` 和 `iTerm2 + it2 CLI` 安装指引并提示 `teammate_mode: "in-process"` 选项。
- [ ] 完成

## T4: 实现 SharedTaskStore + SharedTask
- 影响文件: `mewcode/teams/shared_task.py`（`SharedTask` @ 9-25；`SharedTaskStore` @ 28-；`__init__` + `_load` + `_save`；`create` / `get` / `list_tasks` / `update` / `init_empty`）
- 依赖任务: 无
- 完成标准: `SharedTask` dataclass 8 字段含 `id / title / description / status / assignee / blocks / blocked_by / created_by`；`status` 注释四档 `pending | in_progress | completed | blocked`；`SharedTaskStore` 用单文件 `tasks.json` 结构 `{"next_id": int, "tasks": [...]}`；`create` 自增 id 返 `SharedTask` 实例；`list_tasks(status=None, assignee=None)` 双过滤；`update` 部分字段更新 + `add_blocks` / `add_blocked_by` 列表追加（去重）；`init_empty` 清空 + 重置 `_next_id=1` + save。
- [ ] 完成

## T5: 实现 AgentNameRegistry 单例
- 影响文件: `mewcode/teams/registry.py`（`AgentNameRegistry` @ 6-40）
- 依赖任务: 无
- 完成标准: 进程内单例（线程安全 double-checked locking with `_lock = threading.Lock()`）；`instance()` / `reset()` 类方法；`register(name, agent_id)` / `resolve(name_or_id)` 同时支持按 name 和按 id 反查 / `unregister(name)` / `list_all()` 实例方法；`_names: dict[str, str]` 内部存储 name → agent_id 映射。
- [ ] 完成

## T6: 实现 spawn_inprocess_teammate + InProcessTeammateHandle
- 影响文件: `mewcode/teams/spawn_inprocess.py`（`InProcessTeammateHandle` @ 14-40；`spawn_inprocess_teammate` @ 43-56）
- 依赖任务: T1
- 完成标准: `InProcessTeammateHandle(agent, task, name)` 属性 `done` / `result`（已完成时安全取结果异常返 None）/ `cancel()` 取消未完成 task；`spawn_inprocess_teammate(agent, prompt, name, conversation=None)` 用 `asyncio.create_task` 起协程跑 `agent.run_to_completion(prompt)` 或 `agent.run_to_completion("", conversation)`（传 conversation 走 fork 路径）；task name 设为 `f"teammate-{name}"`。
- [ ] 完成

## T7: 实现 spawn_tmux_teammate + build_cli_command + kill_pane
- 影响文件: `mewcode/teams/spawn_tmux.py`（`TmuxPaneInfo` @ 10-13；`TmuxSpawnError` @ 16-17；`_run_tmux` @ 20-29；`build_cli_command` @ 32-56；`spawn_tmux_teammate` @ 59-108；`send_keys_to_pane` @ 111-115；`kill_pane` @ 118-122）
- 依赖任务: T1
- 完成标准: `build_cli_command` 拼出 `MEWCODE_TEAM_NAME=X MEWCODE_TEAMMATE_NAME=Y MEWCODE_MAILBOX_DIR=Z mewcode -p --work-dir <wt> [--agent-type X] [--model X] '<prompt>'`，prompt 内单引号转义为 `'\''`；`spawn_tmux_teammate` 三级 fallback——先 `split-window -h -t <team_name>` → 失败则 `new-window` + `split-window` → 再失败则 `new-session -d` + `list-panes` 取第一个；最后 `send-keys -t <pane> <cmd> Enter`；`kill_pane` best-effort 静默失败；`send_keys_to_pane` 用于 wake pane。
- [ ] 完成

## T8: 实现 spawn_iterm2_teammate
- 影响文件: `mewcode/teams/spawn_iterm2.py`（`ITermPaneInfo` @ 10-12；`ITermSpawnError` @ 15-16；`_run_it2` @ 19-28；`spawn_iterm2_teammate` @ 31-58）
- 依赖任务: T7
- 完成标准: 复用 `build_cli_command` 拼命令；通过 `it2 split-pane --command "/bin/zsh -c '<cmd>'"` 创建新 pane；返回 `ITermPaneInfo{session_id}`；spawn 失败抛 `ITermSpawnError`（不静默吞）；使用外部 `it2` CLI 而非 osascript 字符串拼接。
- [ ] 完成

## T9: 实现 transcript 持久化
- 影响文件: `mewcode/teams/transcript.py`（`_serialize_conversation` @ 10-33；`_deserialize_conversation` @ 36-64；`save_transcript` @ 67-79；`load_transcript` @ 82-92）
- 依赖任务: T1
- 完成标准: `save_transcript(team_name, agent_id, conv)` 把 `conv.history`（含 tool_uses / tool_results 块）序列化 JSON 落到 `<team_dir>/transcripts/<agent_id>.json`；`load_transcript` 反序列化时 `env_injected = ltm_injected = True` 防止重复注入环境消息；tool_uses 用 `ToolUseBlock{tool_use_id, tool_name, arguments}` 结构，tool_results 用 `ToolResultBlock{tool_use_id, content, is_error}`。
- [ ] 完成

## T10: 实现 TeamManager 全套方法
- 影响文件: `mewcode/teams/manager.py`（`TeamError` @ 27-28；`TeamManager.__init__` @ 31-41；`detect_backend` @ 43-50；`create_team` @ 52-86；`get_team` @ 88-97；`get_task_store` @ 99-108；`get_mailbox` @ 110-119；`register_member` @ 121-134；`set_member_idle` @ 136-152；`register_inprocess_handle` @ 154-155；`register_pane_id` @ 157-158；`get_pane_id` @ 160-161；`delete_team` @ 163-201；`get_team_for_teammate` @ 203-210；`on_teammate_completed` @ 212-221；`_kill_pane` @ 223-229；`_cleanup_worktree` @ 231-245；`_remove_dir` @ 247-）
- 依赖任务: T1, T2, T3, T4, T5, T6
- 完成标准: `__init__` 七字段 `_teams / _task_stores / _mailboxes / _inprocess_handles / _pane_ids / _detected_backend / _teammate_team_map` 全初始化空 dict / None；`detect_backend` 第一次后缓存到 `_detected_backend`；`create_team` 链 `detect_backend → unique_team_name → mkdir → AgentTeam(...).save → SharedTaskStore.init_empty → Mailbox` 并缓存三个字典；`register_member` 同时 `AgentNameRegistry.register` + 写 `_teammate_team_map`；`set_member_idle` 翻 is_active 并写 idle 通知到 Lead 邮箱；`delete_team` 先校验全员 `is_active is not False` 必须 idle，否则抛 `TeamError`，通过后遍历清 name registry / handle.cancel / `_kill_pane` / git worktree remove / trace_manager.remove，最后 `mailbox.cleanup_all` + 删目录 + 弹三个缓存。
- [ ] 完成

## T11: 实现 Agent._consume_mailbox 接入
- 影响文件: `mewcode/agent.py`（`self.coordinator_mode / self.team_name / self._team_manager` 字段 @ 324-326；`_consume_mailbox` @ 718-733；`run_to_completion` 主循环钩入 @ 433 + @ 957；`coordinator_mode` 传 `build_system_prompt` @ 471 + @ 937）
- 依赖任务: T2, T10
- 完成标准: `Agent.__init__` 加 `self.coordinator_mode: bool = False / self.team_name: str = "" / self._team_manager: Any = None` 三字段；`_consume_mailbox(conversation)` 在 `team_name` 和 `_team_manager` 都非空时取 `team_manager.get_mailbox(team_name).consume(self.agent_id)`；每条消息前缀 `[Message from <sender>] ` 或 `[<message_type> from <sender>] ` 后 `conversation.add_user_message`；异常吞掉记 `log.debug`；在 `run_to_completion` 主循环开头（每轮迭代前）和 `iterate_once` 开头都调一次。
- [ ] 完成

## T12: 实现 coordinator 系统提示词 + 工具过滤
- 影响文件: `mewcode/teams/coordinator.py`（`is_coordinator_mode` @ 7-11；`match_session_mode` @ 14-36；`get_coordinator_system_prompt` @ 39-；`get_coordinator_user_context`）；`mewcode/agents/tool_filter.py`（`COORDINATOR_MODE_ALLOWED_TOOLS` 12 项 @ 66-79；`TEAMMATE_COORDINATION_TOOLS` 5 项 @ 50-56；`IN_PROCESS_TEAMMATE_ALLOWED_TOOLS` @ 58-64；`apply_coordinator_filter` @ 187-193；`build_teammate_tools` @ 129-184）
- 依赖任务: T5, T10
- 完成标准: `is_coordinator_mode(enable_flag)` 双锁判定（flag false 直接 false；flag true 时读 `MEWCODE_COORDINATOR_MODE` env 三档 `1/true/yes`）；`match_session_mode` 实现恢复会话时的 env var 同步；`get_coordinator_system_prompt` 输出含 `Research / Synthesis / Implementation / Verification` 四阶段、`<task-notification>` XML 格式、`based on your findings` anti-pattern；`COORDINATOR_MODE_ALLOWED_TOOLS = {Agent, SendMessage, TaskCreate, TaskGet, TaskList, TaskUpdate, TeamCreate, TeamDelete, ReadFile, Glob, Grep, Bash}` 12 项（写工具 `WriteFile / EditFile` 被排除）；`apply_coordinator_filter(registry)` 把 registry 筛到白名单；`build_teammate_tools` 按 backend 类型分流：in-process 严格白名单 `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`，pane 模式只剔除 `TeamCreate` 和 `TeamDelete`。
- [ ] 完成

## T13: 实现 SendMessageTool / TeamCreateTool / TeamDeleteTool 三个工具
- 影响文件: `mewcode/tools/send_message.py`（`SendMessageParams` @ 16-21；`VALID_MESSAGE_TYPES` @ 24；`SendMessageTool` @ 27-；`execute` @ 51-109；`_wake_pane` @ 111-119；`_wake_pane_members` @ 121-123）；`mewcode/tools/team_create.py`（`TeamCreateParams` @ 14-16；`TeamCreateTool` @ 19-85）；`mewcode/tools/team_delete.py`（`TeamDeleteParams` @ 14-15；`TeamDeleteTool` @ 18-53）
- 依赖任务: T2, T5, T10, T12
- 完成标准:
 - `SendMessageTool.execute`：先校验 `message_type in VALID_MESSAGE_TYPES`，`text` 类型必须有 `summary`；`to == "*"` 走 broadcast（member_ids 不含 self，添加 lead_agent_id 如果 self 不是 lead）；否则 `AgentNameRegistry.instance().resolve(to)` 解析后 `mailbox.write`；写完调 `_wake_pane(target_id)` 唤醒 pane 后端；非法 to 返 IsError `Cannot resolve recipient '...'`。
 - `TeamCreateTool.execute`：先 `team_manager.detect_backend` 不通过返 IsError；通过后 `team_manager.create_team`；如 `is_coordinator_mode(enable_coordinator_mode)` 返 true 则 `parent_agent.coordinator_mode = True`、`parent_agent._full_registry = parent_agent.registry`、`parent_agent.registry = apply_coordinator_filter(registry)`，输出附 "Coordinator Mode activated" 提示。
 - `TeamDeleteTool.execute`：调 `team_manager.delete_team` 捕获 `TeamError` 返 IsError；如 `parent_agent.coordinator_mode` 为 true 则 `parent_agent.registry = parent_agent._full_registry` 恢复并清零 flag，输出附 "Coordinator Mode deactivated" 提示。
- [ ] 完成

## T14: 实现 AgentTool._execute_as_teammate（team_name 分支）
- 影响文件: `mewcode/tools/agent_tool.py`（`AgentToolParams.team_name` 字段 @ 28；`TEAMMATE_ADDENDUM` 常量 @ 38；`AgentTool.__init__` 加 `team_manager` 参数 @ 72；`_team_manager` 字段 @ 81；`execute` 入口分支 @ 86-87；`_execute_as_teammate` @ 246-414）
- 依赖任务: T10, T12, T13（ch13/ch14 的 AgentTool / WorktreeManager）
- 完成标准:
 - `AgentToolParams` 加 `team_name: str | None = None` 字段；
 - `AgentTool.__init__` 加 `team_manager` 关键字参数和 `_team_manager` 实例字段；
 - `execute` 入口看到 `p.team_name` 非空时优先走 `_execute_as_teammate`（先于 fork / sync / async 分发）；
 - `_execute_as_teammate`：校验 team_manager / worktree_manager 配置、`team_manager.get_team(team_name)` 不存在返 IsError；base_name 同名冲突自动加 `-2/-3/...`；可选解析 `subagent_type`，无 type + enable_fork 走 `build_forked_messages` 否则用空白 builtin AgentDef；`worktree_manager.create(f"team-{team_name}/{teammate_name}", "HEAD")` 建独立 wt；`detect_backend` 决定后端；`build_teammate_tools` 按 backend 构造工具池；用 `AgentClass(agent_id, registry, ...)` 创建 sub-agent 注入 `TEAMMATE_ADDENDUM`；`AgentNameRegistry.instance().register(teammate_name, agent_id)`；构造 `TeammateInfo` 后 `team_manager.register_member`；按 backend 分发 in-process（`spawn_inprocess_teammate`）或 pane（`_spawn_pane_teammate`）。
- [ ] 完成

## T15: app.py 注册三件套 + 注入 team_manager
- 影响文件: `mewcode/app.py`（`MewCodeApp.__init__` 加 `teammate_mode / enable_coordinator_mode` 参数 @ 519-520；`_teammate_mode / _enable_coordinator_mode` 字段 @ 530-531；team 系统设置块 @ 730-762；`agent._team_manager = team_manager` 注入 @ 801；`on_teammate_completed` 回调 @ 1287-1288；shutdown 清理 @ 1592-1598）；`mewcode/__main__.py`（`teammate_mode / enable_coordinator_mode` 透传 `MewCodeApp` @ 57-58）；`mewcode/config.py`（`AppConfig.teammate_mode` / `enable_coordinator_mode` 字段 + load_config 校验 `teammate_mode in {"", "in-process"}`）
- 依赖任务: T11, T13, T14
- 完成标准:
 1. `MewCodeApp.__init__` 加 `teammate_mode: str = ""` 和 `enable_coordinator_mode: bool = False` 参数；
 2. 在 AgentTool 注册之前 `self.team_manager = TeamManager(worktree_manager, trace_manager)`；
 3. AgentTool 构造时传 `team_manager=self.team_manager`；
 4. 注册 `TeamCreateTool(team_manager, parent_agent, teammate_mode, is_interactive=True, enable_coordinator_mode)`；
 5. 注册 `TeamDeleteTool(team_manager, parent_agent)`；
 6. 注册 `SyntheticOutputTool()`；
 7. `self.agent._team_manager = self.team_manager` 写回主 Agent；
 8. 后台 task 完成回调里调 `self.team_manager.on_teammate_completed(task.agent.agent_id)`；
 9. shutdown 时遍历所有团队强制 `set_member_active(False)` 后 `delete_team` 释放资源；
 10. `mewcode/__main__.py main()` 把 `config.teammate_mode` / `config.enable_coordinator_mode` 透传 `MewCodeApp`；
 11. `config.py` 加两个字段及 `teammate_mode` 校验（合法值仅 `""` 和 `"in-process"`）。
- [ ] 完成

## T16: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T1-T15
- 完成标准:
 - `ruff check mewcode/teams mewcode/tools/team_create.py mewcode/tools/team_delete.py mewcode/tools/send_message.py` 通过；
 - `pytest tests/test_teams.py -v` 通过（覆盖 10 大类 30+ 用例：TestModels 7 + TestSharedTaskStore 6 + TestMailbox 5 + TestAgentNameRegistry 4 + TestBackendDetect 6 + TestToolFilter 3 + TestCoordinatorMode 11 + TestConfigExtensions 3 + TestTranscript 2 + TestAgentCoordinatorIntegration 3）；
 - `pytest tests/test_subagent.py -v` 仍全部通过（确保 AgentTool 改造未破坏 ch13 功能）；
 - 主流程接线验证：`grep -n "TeamManager\|TeamCreateTool\|TeamDeleteTool\|team_manager" mewcode/app.py` 命中至少 8 处；`grep -n "_consume_mailbox\|_team_manager\|coordinator_mode" mewcode/agent.py` 看到主 Agent 三处接入；`grep -n "_execute_as_teammate" mewcode/tools/agent_tool.py` 命中入口分发 + 函数体。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15 / [ ] T16
```
```plain
# ch15: AgentTeam Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 枚举 `BackendType` 在 `mewcode/teams/models.py:10-13` 含三档常量 `TMUX="tmux" / ITERM2="iterm2" / IN_PROCESS="in-process"`
- [ ] dataclass `TeammateInfo` 在 `mewcode/teams/models.py:16-31` 7 字段含 `name / agent_id / agent_type / model / worktree_path / backend_type / is_active`，`is_active: bool | None = None` 三值语义
- [ ] dataclass `AgentTeam` 在 `mewcode/teams/models.py:40-102` 含 `members: list[TeammateInfo]`、`get_member` 同时按 name 和 agent_id 双向查找、`set_member_active` / `all_idle` / `active_members` / `save` / `load` 全方法
- [ ] `resolve_team_dir` / `unique_team_name` 在 `mewcode/teams/models.py:105-117`，落到 `~/.mewcode/teams/<slug>/`，同名冲突自动加 `-2/-3/...` 后缀
- [ ] `MailboxMessage` dataclass 在 `mewcode/teams/mailbox.py:11-27` 8 字段，`message_type` 注释三档 `text | shutdown_request | shutdown_response`
- [ ] `Mailbox` 在 `mewcode/teams/mailbox.py:30-102` 实现单文件单消息模型 `<base>/<agent_id>/<timestamp>_<id>.json`，`write / read / consume / broadcast / cleanup / cleanup_all` 六个方法齐全
- [ ] `create_message` 在 `mewcode/teams/mailbox.py:105-122` 自动填 `uuid.uuid4().hex[:12]` 和 `time.time()`
- [ ] `BackendDetectionError` + `detect_backend` 在 `mewcode/teams/backend_detect.py:9-51` 实现优先级链，失败抛错而非静默回退
- [ ] `SharedTask` + `SharedTaskStore` 在 `mewcode/teams/shared_task.py:9-` 实现 JSON 文件 `{"next_id", "tasks": [...]}` 存储和 `create / get / list_tasks / update / init_empty` 五方法
- [ ] `AgentNameRegistry` 单例在 `mewcode/teams/registry.py:6-40` 线程安全 double-checked locking，`resolve` 同时支持 name 和 agent_id 反查
- [ ] `InProcessTeammateHandle` + `spawn_inprocess_teammate` 在 `mewcode/teams/spawn_inprocess.py:14-56` 用 `asyncio.create_task` 起协程；handle.done / result / cancel 三属性
- [ ] `build_cli_command` 在 `mewcode/teams/spawn_tmux.py:32-56` 输出 `MEWCODE_TEAM_NAME=X MEWCODE_TEAMMATE_NAME=Y MEWCODE_MAILBOX_DIR=Z mewcode -p --work-dir <wt> '<prompt>'`，prompt 内单引号转义为 `'\''`
- [ ] `spawn_tmux_teammate` 在 `mewcode/teams/spawn_tmux.py:59-108` 三级 fallback（split-window → new-window → new-session）
- [ ] `kill_pane` / `send_keys_to_pane` 在 `mewcode/teams/spawn_tmux.py:111-122` best-effort 静默失败
- [ ] `spawn_iterm2_teammate` 在 `mewcode/teams/spawn_iterm2.py:31-58` 复用 `build_cli_command`，通过 `it2 split-pane` 创建 pane
- [ ] `save_transcript / load_transcript` 在 `mewcode/teams/transcript.py:67-92` 序列化 `ConversationManager.history` 含 tool_uses / tool_results 块到 `<team_dir>/transcripts/<agent_id>.json`
- [ ] `TeamManager` 在 `mewcode/teams/manager.py:31-201` 7 内部字典 + 13 个公开方法齐全；`__init__` 接受 `worktree_manager` 和 `trace_manager`；`_detected_backend` 第一次后缓存
- [ ] `delete_team` 在 `mewcode/teams/manager.py:163-201` 先校验 `is_active is not False` 必须 idle，否则抛 `TeamError`
- [ ] `COORDINATOR_MODE_ALLOWED_TOOLS` 在 `mewcode/agents/tool_filter.py:66-79` 含 12 项 `{Agent, SendMessage, TaskCreate, TaskGet, TaskList, TaskUpdate, TeamCreate, TeamDelete, ReadFile, Glob, Grep, Bash}`（写工具 `WriteFile / EditFile` 被排除）
- [ ] `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS` 在 `mewcode/agents/tool_filter.py:58-64` 是 `ASYNC_AGENT_ALLOWED_TOOLS | TEAMMATE_COORDINATION_TOOLS | {CronCreate, CronDelete, CronList}` 联合
- [ ] `build_teammate_tools` 在 `mewcode/agents/tool_filter.py:129-184` 按 backend 类型分流：in-process 严格白名单、pane 模式只剔除 `TeamCreate` 和 `TeamDelete`
- [ ] `apply_coordinator_filter` 在 `mewcode/agents/tool_filter.py:187-193` 把 registry 筛到 `COORDINATOR_MODE_ALLOWED_TOOLS`
- [ ] `get_coordinator_system_prompt` 在 `mewcode/teams/coordinator.py:39-` 输出含 `Research / Synthesis / Implementation / Verification` 四阶段、`<task-notification>` XML 格式、`based on your findings` anti-pattern
- [ ] `SendMessageTool` 在 `mewcode/tools/send_message.py:27-123` 实现 `to / message / summary / message_type / metadata` 五参数；`to == "*"` 走 broadcast；`text` 类型必须有 `summary`
- [ ] `TeamCreateTool` 在 `mewcode/tools/team_create.py:19-85` 实现 `team_name + description`；Coordinator Mode 激活时备份 `_full_registry`
- [ ] `TeamDeleteTool` 在 `mewcode/tools/team_delete.py:18-53` 实现 `team_name`；Coordinator Mode 还原 `_full_registry`
- [ ] `AgentTool._execute_as_teammate` 在 `mewcode/tools/agent_tool.py:246-414` 处理 `team_name != None` 分支，含 worktree 创建 / build_teammate_tools / register_member / spawn 分发

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -n "TeamManager" mewcode/app.py` 在 `mewcode/app.py:731-735` 找到导入和 `self.team_manager = TeamManager(worktree_manager, trace_manager)` 创建
- [ ] `grep -n "TeamCreateTool\|TeamDeleteTool" mewcode/app.py` 在 `mewcode/app.py:749-762` 找到两个工具注册点
- [ ] `agent_tool = AgentTool(..., team_manager=self.team_manager)` 注入点在 `mewcode/app.py:737-746`
- [ ] `self.agent._team_manager = self.team_manager` 注入点在 `mewcode/app.py:801`
- [ ] `self.team_manager.on_teammate_completed(task.agent.agent_id)` 在 `mewcode/app.py:1287-1288` 后台任务完成回调
- [ ] shutdown 清理在 `mewcode/app.py:1592-1598` 遍历所有团队强制 set_member_active(False) 后 delete_team
- [ ] `mewcode/__main__.py:57-58` 把 `config.teammate_mode` / `config.enable_coordinator_mode` 透传 `MewCodeApp`
- [ ] `Agent.__init__` 在 `mewcode/agent.py:324-326` 声明 `self.coordinator_mode / self.team_name / self._team_manager` 三字段
- [ ] `Agent._consume_mailbox` 在 `mewcode/agent.py:718-733` 实现；`mewcode/agent.py:433 + :957` 在主循环开头钩入
- [ ] `Agent.run_to_completion` 在 `mewcode/agent.py:471 + :937` 把 `coordinator_mode=self.coordinator_mode` 传给 `build_system_prompt`
- [ ] `AgentTool.execute` 入口分支在 `mewcode/tools/agent_tool.py:86-87` 看到 `p.team_name` 非空时优先走 `_execute_as_teammate`
- [ ] `AgentTool.__init__` 接受 `team_manager` 参数在 `mewcode/tools/agent_tool.py:72`，写入 `self._team_manager` 在 `:81`

## 3. 编译与测试

- [ ] `ruff check mewcode/teams mewcode/tools/team_create.py mewcode/tools/team_delete.py mewcode/tools/send_message.py` 无错误
- [ ] `pytest tests/test_teams.py -v` 通过（覆盖至少 30 个用例：TestModels 7 个 / TestSharedTaskStore 6 个 / TestMailbox 5 个 / TestAgentNameRegistry 4 个 / TestBackendDetect 6 个 / TestToolFilter 3 个 / TestCoordinatorMode 11 个 / TestConfigExtensions 3 个 / TestTranscript 2 个 / TestAgentCoordinatorIntegration 3 个）
- [ ] `pytest tests/test_subagent.py -v` 全部通过（确保 AgentTool 改造未破坏 ch13）
- [ ] `pytest tests/test_agent.py -v` 全部通过（确保 Agent.__init__ 新字段未破坏现有用例）
- [ ] 测试运行不在用户主目录残留 `~/.mewcode/teams/` 目录（fixture 用 `patch("mewcode.teams.models.Path.home", return_value=Path(tmp_dir))` 重定向）

## 4. 端到端验证

- [ ] 注册路径：`MewCodeApp.__init__` 在 `mewcode/app.py:730-762` 创建 `TeamManager` 并把 `TeamCreate / TeamDelete / SendMessage` 三件套放入 registry；用户向 Lead 说 "create a team to refactor X" → LLM 调 `TeamCreate(team_name="refactor-X")` → `detect_backend()` 选模式 → Output 返回 `Team refactor-X created successfully. Backend: ... Config: ~/.mewcode/teams/refactor-x/config.json`
- [ ] Spawn 路径：Lead 继续说 "spawn alice to do data layer" → LLM 调 `Agent(team_name="refactor-X", name="alice", prompt="...")` → `AgentTool.execute` 在 `mewcode/tools/agent_tool.py:86-87` 识别 `team_name` 分支调 `_execute_as_teammate` → `worktree_manager.create(f"team-refactor-X/alice")` → `build_teammate_tools` → `spawn_inprocess_teammate` / `spawn_tmux_teammate` / `spawn_iterm2_teammate` 按 backend 分发 → 队员开始干活
- [ ] 通信路径：队员 alice 通过 `SendMessage(to="bob", message="...", summary="...")` 给 bob 写 mailbox → `AgentNameRegistry.resolve("bob")` 拿到 target_id → `mailbox.write(target_id, msg)` → `_wake_pane(target_id)`（pane 后端需要）→ bob 下一轮 `_consume_mailbox` 收到消息作为 user message
- [ ] Lead 感知路径：每个队员后台 task 完成时 `app.py:1287-1288` 调 `team_manager.on_teammate_completed(agent_id)` → 找到所在团队后 `set_member_idle(team_name, name)` → 翻 `is_active=False` + 写一条 `Teammate '<name>' is now idle (run_to_completion finished).` 到 Lead 邮箱 → Lead 下一轮 `_consume_mailbox` 注入对话
- [ ] Coordinator Mode 路径：启用 `enable_coordinator_mode=True` 且 `MEWCODE_COORDINATOR_MODE=1` → `TeamCreateTool.execute` 把 `parent_agent.coordinator_mode = True / _full_registry 备份 / registry = apply_coordinator_filter(registry)` → Lead 每轮工具集只剩 12 项白名单；调 `WriteFile` / `EditFile` 会找不到工具被拒绝；`TeamDelete` 清空团队后恢复 `_full_registry`
- [ ] Tmux 后端：`TMUX` env 非空时 `detect_backend` 返 `BackendType.TMUX` → `spawn_tmux_teammate` 用 `build_cli_command` 拼出 `MEWCODE_TEAM_NAME=refactor-X MEWCODE_TEAMMATE_NAME=alice MEWCODE_MAILBOX_DIR=... mewcode -p --work-dir /tmp/wt 'prompt'` → tmux send-keys 启动子进程 → 子进程加载同一份 mailbox 目录开始 _consume_mailbox 轮询
- [ ] iTerm2 后端：`TERM_PROGRAM=iTerm.app` 且 `shutil.which("it2")` 非空且不在 tmux 时 `detect_backend` 返 `BackendType.ITERM2` → `spawn_iterm2_teammate` 用 `it2 split-pane --command "/bin/zsh -c '<cmd>'"` 创建 pane
- [ ] 关闭路径：`TeamDelete(team_name="refactor-X")` → `team_manager.delete_team` → 校验全员 idle → 遍历每个 member 清 name registry / cancel handle / kill pane / git worktree remove / trace_manager.remove → cleanup mailbox + 删团队目录 → 弹出 `_teams / _task_stores / _mailboxes` 三个缓存 → 如 Lead 在 Coordinator Mode 则恢复 `_full_registry`

## 5. 文档

- [ ] `docs/python/ch15/spec.md` 已写
- [ ] `docs/python/ch15/tasks.md` 已写，16 个 T 全部勾完
- [ ] `docs/python/ch15/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch15` 与三件套关闭状态（待用户确认后由人或 CI 触发）
```

### Java

```plain
# ch15: AgentTeam Spec

## 1. 背景

SubAgent（ch13）解决了一次性子任务的上下文隔离，但拓扑是星型：所有子 Agent 只能和主 Agent 通信，子 Agent 之间彼此看不见。当任务规模上来——四个模块同时重构、多角度并行调查 bug、一个 Agent 需要把发现告诉另一个——星型拓扑下主 Agent 成了信息中转瓶颈，子任务被迫串行。这一章把"长期协作团队"做成 MewCode 的一等概念：多个 Agent 组成 Team，并行干活、直接互发消息、共享任务列表，主 Agent 升级为 Team Lead 专职调度。Java 版本利用 JDK 21 虚拟线程跑 in-process 队员，外部后端则通过 `ProcessBuilder` 拉起 tmux / iTerm2 进程，由共享 `FileMailBox` 目录串联跨进程通信。

## 2. 目标

提供 `TeamManager` / `TeamManager.Team` / `TeamManager.Member` / `FileMailBox` / `SharedTaskStore` / `AgentNameRegistry` / `Coordinator` / `TeamTools.SendMessageTool` / `TeamTools.TeamCreateTool` / `TeamTools.TeamDeleteTool` 一整套类型与工具，让 LLM 在对话里：1) 调 `TeamCreate` 建团队（按环境自动选 tmux / in-process 后端），2) 后续通过 `Agent` 工具带 `team_name` 把队员加入团队，3) 队员之间通过 `SendMessage` 走 `FileMailBox` 互发消息、idle 后通知 Lead，4) Lead 借助 `Coordinator.ALLOWED_TOOLS` 收窄工具集进入纯调度模式。tmux 后端由 `SpawnDispatcher.buildTeammateCLI` 拼出 `mewcode --teammate --team-name X --agent-name Y` 由独立进程跑 worker，和 Lead 共享同一份 mailbox 目录。

## 3. 功能需求

- F1: `TeamManager.TeamMode` 枚举包含 `IN_PROCESS / TMUX` 两档；`TeamManager.detectBackend()` 按 `TMUX` 环境变量 → `which tmux` 命中 → 退化到 `IN_PROCESS` 的优先级自动选择。
- F2: `TeamManager.Team` 持有 `name / mode / members LinkedHashMap / mailBox` 字段；`TeamManager.Member` 含 `name / agent / conv / active / thread` 字段，外部后端的 Member 由 `SpawnDispatcher.recordExternalMember` 创建，`agent` 与 `conv` 字段保持为 null。
- F3: `TeamManager` 提供 `createTeam` / `getTeam` / `deleteTeam` / `listTeams` / `closeAll` 同步方法；`Team` 暴露 `addMember` / `startMember` / `stopMember` / `stopAll` / `getMember` / `hasMember` / `memberNames` / `sendMessage`，全部用 `synchronized` 保护成员表。
- F4: `FileMailBox` 基于 `<baseDir>/<agentId>.json` 文件持久化消息；`send` / `readUnread` / `markAllRead` 三件套；并发安全靠 `<agentId>.json.lock` 文件锁，`Files.createFile` 抛 `FileAlreadyExistsException` 时重试（最多 10 次，5-100ms 随机退避），>10s 视为过期锁强制清理。
- F5: `FileMailBox.MailMessage` 记录类含 `from / text / timestamp / read / color / summary` 六个字段；便利构造器 `MailMessage(from, text)` 自动填 `Instant.now()` 时间戳、`read=false`、空 color/summary；`send` 落盘时强制把 `read` 置 false。
- F6: `SpawnDispatcher.spawnTeammate(SpawnConfig)` 统一入口按 `Team.mode` 分发到 in-process / tmux 两条路径，返回 `SpawnResult{mode, paneId}`。`IN_PROCESS` 模式调 `team.addMember` 注册并用 `Thread.startVirtualThread` 跑 `TeammateRunner.runInProcessTeammate`；`TMUX` 模式先把 task 写入对方 mailbox，再拼 CLI 调 `TmuxBackend.spawnTmuxTeammate`，最后 `recordExternalMember` 注册。
- F7: `SpawnDispatcher.buildTeammateCLI(teamName, memberName, workdir)` 用 `ProcessHandle.current().info().command()` 拿当前可执行路径；workdir 空时退化到 `System.getProperty("user.dir")`；输出 `cd <quoted_wd> && <quoted_exe> --teammate --team-name <quoted_team> --agent-name <quoted_member>`，所有变量经 `shellQuote` 处理。
- F8: `SpawnDispatcher.shellQuote(s)` 简单字符（`[a-zA-Z0-9_./-]+`）直接返回；含特殊字符时单引号包裹并把内嵌的 `'` 替换为 `'\''`（POSIX 标准转义）。
- F9: `TmuxBackend.spawnTmuxTeammate` 用 `tmux new-window -d -n <teamName>-<memberName> <cliCommand>` 创建后台窗口；命令返回码非 0 或超时（30s）抛 `RuntimeException("Failed to spawn tmux window: ...")`；`TmuxBackend.stopTmuxTeammate` 先 `send-keys C-c` 再 `kill-window`，best-effort 不重抛异常，失败仅 `log.fine`。
- F10: `ITermBackend.spawnITermTeammate` 用 `osascript -e <AppleScript>` 在 iTerm2 当前 window 创建 tab 并 `write text <cliCommand>`，内嵌双引号转义为 `\"`；30s 超时；`stopITermTeammate` 遍历所有 window 和 tab 找名字匹配的 close 掉，10s 超时、best-effort 失败静默。
- F11: `TeammateRunner.runInProcessTeammate(team, member, initialPrompt, addendum)` 队员主循环：先把 addendum 作为 system reminder 注入 → 调 `injectPendingMessages` 把未读邮件转 system reminder → 把 `initialPrompt` 加为 user message → 调 `member.agent.run(conv)` 跑一轮 → 通过 `drainAgentEvents` 转发事件 → 给 Lead 发 `[idle]` 通知 → 循环 `waitForNextPromptOrShutdown` 轮询邮箱，500ms 间隔，命中新消息加为 user message 跑下一轮，命中 shutdown 或线程中断退出。退出前置 `member.active=false`。
- F12: `TeammateRunner.LEAD_NAME = "lead"` / `SHUTDOWN_PREFIX = "[shutdown]"` / `IDLE_POLL_MS = 500` 三常量；`isShutdownRequest(text)` 用 `text.strip().startsWith(SHUTDOWN_PREFIX)` 判定；`createIdleNotification(memberName, reason)` 产出 `"[idle] <name>: <reason> (at <iso-instant>)"` 文本。
- F13: `TeammateRunner.drainLeadMailbox(teamMgr)` 扫所有团队的 Lead 收件箱，把未读消息按 `<team-notification team="X">\nfrom=Y: text\n...\n</team-notification>` 包装返回 `List<String>`，并把消息标记为已读；`teamMgr == null` 时返回 `List.of()`。
- F14: `TeammateRunner.buildTeammateAddendum(teamName, memberName, otherMembers)` 产出注入到队员对话顶端的 system reminder，告诉它身份、其他队友名字、必须通过 `SendMessage` 沟通、停止调用工具会自动发 idle 通知给 Lead。
- F15: `TeammateRunner.injectPendingMessages(team, memberName, conv)` 读 mailbox 未读，非空时拼 `"You have new messages:\n\nFrom <sender>: \n\n..."` 作为 system reminder 注入并 `markAllRead`，无未读直接返回。
- F16: `Coordinator.ALLOWED_TOOLS` 是 12 项白名单 `Set<String>`：`Agent / SendMessage / TaskCreate / TaskGet / TaskList / TaskUpdate / TeamCreate / TeamDelete / ReadFile / Glob / Grep / Bash`；`Coordinator.isCoordinatorTool(name)` 返回 set 命中布尔。写工具 `WriteFile / EditFile` 等被排除。
- F17: `TeamTools.SendMessageTool` 暴露 `to / content` 两个必填字段；`execute` 遍历所有团队找 `to` 这个 member 所在团队调 `team.sendMessage(senderName, to, content)` 投递；未匹配返 `recipient '<to>' not found in any team` 错误。
- F18: `TeamTools.TeamCreateTool` 暴露 `team_name` 必填、`description` 可选；同名时追加 `-2/-3/...` 后缀去重；调 `TeamManager.detectBackend()` + `teamMgr.createTeam`；Output 提示 `"Team \"X\" created (mode: Y). Use Agent tool with team_name=\"X\" to add teammates."`。
- F19: `TeamTools.TeamDeleteTool` 暴露 `team_name` 必填；不存在返错误；调 `teamMgr.deleteTeam`（内部 `stopAll` 中断所有 member 的虚拟线程）；返回 `"Team \"X\" deleted. Stopped N member(s): a, b, c"` 清单。
- F20: `AgentNameRegistry` 是单例（`getInstance()`），维护 `name → agentId` 映射；`register / resolve / unregister / listAll` 全部 `synchronized`；`resolve` 支持反向匹配——传入的字符串既可以是 name 也可以是 agentId，两边都查不到返 null。
- F21: `SharedTaskStore` 基于 `<teamDir>/tasks.json` 持久化 `SharedTask` 记录列表；`create / get / listTasks / update` 全部 `synchronized`；`update` 支持 `status / assignee` 覆盖以及 `addBlocks / addBlockedBy` 追加（不替换），自增 `id` 由 `AtomicInteger` 保证。

## 4. 非功能需求

- N1: FileMailBox 跨进程并发安全——tmux 启动的队友进程和 Lead 进程不共享 JVM 堆，必须靠文件锁保证写入原子性。锁文件 10 秒过期自动清理避免死锁。
- N2: 外部后端队员的初始任务必须在 spawn 之前写入 mailbox，因为 tmux 新进程启动到第一次 idle poll 期间无法接消息；先写后启即可保证第一次 poll 必命中。
- N3: In-process 队员的虚拟线程退出路径有三条：`Thread.currentThread().isInterrupted()` 为真、收到 shutdown 消息、`agent.run` 自然结束后无新消息。退出时必须置 `member.active=false`，否则 Lead 拿不到队员已停的状态。
- N4: Coordinator Mode 通过 `Coordinator.isCoordinatorTool` 在每轮迭代开头动态判定，而非一次性裁剪 registry。这样团队全部 Delete 后下一轮 Lead 自动恢复全工具集，无需重建 registry。
- N5: 队员的 `buildTeammateAddendum` 必须明确告诉 LLM "纯文本回复对队友不可见，最终结果必须通过 `SendMessage` 发给 Lead"——否则队员模型容易写一段汇报作为最后输出就结束，Lead 永远拿不到结果（只能看到 idle 通知）。
- N6: `SendMessage` 当前实现走"遍历所有团队找 `to` member"路径；若 Lead 不在任何 team.members 中，给 Lead 发消息会失败。Java 版的简化方案是发送时直接走当前 Sender 所在团队的 mailbox.send（绕过 hasMember 检查）。
- N7: `SpawnDispatcher.buildTeammateCLI` 必须把 `workdir / mewcode / teamName / memberName` 都通过 `shellQuote` 包裹，否则空格或特殊字符的 workdir 路径会破坏 shell 解析；`shellQuote` 单引号转义遵循 POSIX `'\''` 标准。
- N8: `ITermBackend` 里的 AppleScript 字面量必须把内嵌的双引号转义为 `\"`，否则 `osascript -e` 解析失败；关闭流程是 best-effort，找不到 tab 不应报错（用户可能手动关掉了）。
- N9: `TeammateRunner.runInProcessTeammate` 应当使用 JDK 21 虚拟线程（`Thread.startVirtualThread`）而非平台线程，避免大团队时线程开销爆炸；mailbox 轮询采用 `Thread.sleep(IDLE_POLL_MS)` 而非自旋。
- N10: 测试运行时 `@TempDir` 必须用 `org.junit.jupiter.api.io.TempDir`，让 FileMailBox 写到测试临时目录，否则跑完测试会在仓库根残留 `.mewcode/teams/` 目录；并发测试需用 `ExecutorService` + `CountDownLatch` 验证文件锁正确性。

## 5. 设计概要

- 核心类型:
 - `TeamManager`：全局团队注册表（`Map<String, Team>` + `synchronized` 方法），暴露 CRUD + `detectBackend` 静态方法。
 - `TeamManager.Team`：团队聚合，持有 `mode` 决定后端、`members LinkedHashMap` 注册表、`mailBox FileMailBox` 通信媒介，所有写方法 `synchronized`。
 - `TeamManager.Member`：队员元信息，in-process 模式 `agent + conv` 有值（LLM 跑在虚拟线程），tmux 模式两者为空、`thread` 也为空、靠 paneId（存储为 `name` 字段一部分）句柄。
 - `FileMailBox` + `FileMailBox.MailMessage`：文件锁 + JSON 数组的 mailbox 实现，跨进程共享同一目录，依赖 Jackson `ObjectMapper`。
 - `SpawnDispatcher.SpawnConfig` / `SpawnResult`：`spawnTeammate` 的入参/出参 record，把 in-process 与 tmux 后端的差异收敛到统一返回类型。
 - `Coordinator.ALLOWED_TOOLS`：12 项白名单 `Set<String>`，TUI 每轮按 `teamMgr.listTeams().isEmpty()` 决定是否启用过滤。
 - `SharedTaskStore`：JSON 持久化的任务表，提供 `id / title / description / status / assignee / blocks / blockedBy` 字段及 `addBlocks / addBlockedBy` 追加语义。
 - `AgentNameRegistry`：全局单例 `name → agentId` 映射，方便 SendMessage 通过名字寻址。
- 主流程（按生命周期）:
 - 创建：用户消息 → 主 Agent → LLM 调 `TeamCreate(team_name)` → `TeamManager.detectBackend()` 选模式 → `teamMgr.createTeam` 落到 `~/.mewcode/teams/<name>/inboxes/` → 返回 mode 提示给 Lead。
 - Spawn 队员：Lead LLM 调 `Agent(team_name=X, name=Y, prompt=Z)` → AgentTool 识别 `team_name` 走 team 分支 → `SpawnDispatcher.spawnTeammate(SpawnConfig)` → 按 mode 分发。
 - In-process：`team.addMember` 注册成员 → `Thread.startVirtualThread` 跑 `TeammateRunner.runInProcessTeammate` → 队员在自己的虚拟线程里跑 agent loop。
 - 外部后端：先把初始任务写 mailbox → `buildTeammateCLI` 拼命令 → `TmuxBackend.spawnTmuxTeammate` 调 `tmux new-window` → 新进程跑 `mewcode --teammate` worker 模式 → 第一次 idle poll 命中初始消息开始干活。
 - 通信：队员 → `SendMessage` 工具 → 找对方所在团队 → `team.sendMessage` → `mailBox.send` 写文件。队员收信走 `runInProcessTeammate` 顶端的 `injectPendingMessages` 或 `waitForNextPromptOrShutdown`。
 - Lead 感知：每轮 Lead Agent 开头调 `TeammateRunner.drainLeadMailbox` → 抽 Lead 邮箱所有未读 → 包成 `<team-notification>` system reminder 喂回 LLM。
 - Coordinator Mode：只要 `teamMgr.listTeams()` 非空，TUI 把 Lead 的工具调用拦截 → `Coordinator.isCoordinatorTool(name)` 判定 → 非白名单工具被过滤 → 全部团队清理后下一轮恢复全工具集。
 - Stop：`TeamDelete` 工具 → `teamMgr.deleteTeam` → `team.stopAll` 遍历 member 调 `thread.interrupt()`（in-process）或后端关闭脚本（tmux/iTerm）。
- 调用链（模块层级）:
 - TUI 装配 → 创建 `TeamManager` → 注册 `TeamCreateTool / TeamDeleteTool / SendMessageTool` 三个工具
 - Agent loop 每轮调 `TeammateRunner.drainLeadMailbox` 拼到下一轮系统提示
 - Lead 工具集过滤通过 `Coordinator.isCoordinatorTool` 在每次工具调用前判定
 - 外部工作进程入口 `MewCode.main` 增加 `--teammate` flag 早期拦截，命中走 worker bootstrap 不进 TUI（当前 `MewCode.java` 尚未实现此路径，是后续扩展点）
- 与其他模块的交互:
 - 依赖 `com.mewcode.agent`（Agent / AgentEvent）、`com.mewcode.conversation`（ConversationManager）、`com.mewcode.llm`（LlmClient）、`com.mewcode.tool`（Tool / ToolRegistry / ToolCategory / ToolResult）
 - 被 AgentTool（解析 `team_name` 参数）、TUI（注册工具 + 收件箱 drain + Coordinator filter）、`MewCode.main`（未来 worker 入口）调用

## 6. Out of Scope

- 不实现完整的 `TeammateInfo` 模型（`agentType / model / planModeRequired` 字段、planModeRequired 审批工作流）——本章仅做工具链层面的 Team / Member 骨架。
- 不实现 `plan_approval_response` / `shutdown_response` 结构化消息类型——目前仅 `[shutdown]` 文本前缀 + 纯文本消息两种。
- 不实现 `MewCode --teammate` worker 进程入口完整实现——`SpawnDispatcher.buildTeammateCLI` 已经能产出命令，但 `MewCode.java` 的 main 还没接 `parseTeammateFlags`，留作后续章节扩展。
- 不实现 `TeamManager.createTeamWith` 让外部 worker 进程注册本地构造的 Team——当前 worker 入口未实现，所以此扩展点不必要。
- 不实现 iTerm2 后端在 `SpawnDispatcher` 内的分支——`ITermBackend` 类已经存在但 `spawnTeammate` 的 switch 没接 `ITERM` 分支；本章先保证 tmux + in-process 两档可用。
- 不实现共享任务依赖图的 BFS 校验/循环依赖检测——`SharedTaskStore.update` 只做字段追加，不验证 `blocks/blockedBy` 是否构成环。
- 不实现"协调模式四阶段工作流"系统提示词注入（Research / Synthesis / Implementation / Verification）——`Coordinator` 仅做工具收窄，不做提示词增强。
- 不实现"配置持久化到 ~/.mewcode/teams/<name>/config.json" 的团队元数据——只持久化邮箱 JSON 和 tasks.json，Team 实例本身随 JVM 退出消失。
- 不实现 Worktree 团队层面的"收敛阶段 Lead 用 Bash 跑 git merge"自动化——合并由 Lead LLM 自己用 Bash 工具完成，本章不做封装。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch15: AgentTeam Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 TeamManager / Team / Member / TeamMode
- 影响文件: `src/main/java/com/mewcode/teams/TeamManager.java`（`TeamMode` 枚举 @ 21；`teams` map @ 23；`createTeam` @ 25-29；`getTeam` @ 31-33；`deleteTeam` @ 35-40；`listTeams` @ 42-44；`closeAll` @ 46-51；`detectBackend` @ 53-62；`teamsBaseDir` @ 66-68；`Team` 内部类 @ 70-134；`Member` 内部类 @ 136-151）
- 依赖任务: 无
- 完成标准: `TeamMode` 枚举含 `IN_PROCESS / TMUX`；`Team` 字段 `name / mode / members / mailBox` 齐全；`Team` 方法 `addMember / startMember / stopMember / stopAll / getMember / hasMember / memberNames / sendMessage` 全部 `synchronized`；`Member` 字段 `name / agent / conv / active / thread` 齐全（`active / thread` volatile）；`TeamManager` 顶层 CRUD 方法全部 `synchronized`；`detectBackend` 优先级 `TMUX env → which tmux → IN_PROCESS`。
- [ ] 完成

## T2: 实现 FileMailBox（JSON + 文件锁）
- 影响文件: `src/main/java/com/mewcode/teams/FileMailBox.java`（`MailMessage` record @ 16-21；常量 `MAPPER / MAX_RETRIES / MIN_SLEEP_MS / MAX_SLEEP_MS` @ 23-26；构造器 @ 30-35；`inboxPath` @ 37-39；`lockPath` @ 41-43；`send` @ 45-51；`readUnread` @ 53-60；`markAllRead` @ 62-70；`withLock` @ 76-112；`readInbox` @ 114-123；`writeInbox` @ 125-131）
- 依赖任务: 无
- 完成标准: 每个收件人对应 `<baseDir>/<agentId>.json`；`MailMessage` record 含 6 字段且便利构造器自动填 timestamp/read=false；`send` 落盘时把 `read` 强制置 false；`markAllRead` 用 `withLock` 批量翻转所有消息为 read=true；并发安全靠 `<agentId>.json.lock` 文件用 `Files.createFile` 抛 `FileAlreadyExistsException` 时重试，最多 10 次 5-100ms 随机退避，>10s 视为过期锁清理；`withLock` 在 fn 返回后 finally 删锁文件；Jackson 用 `ObjectMapper` 默认配置 + `TypeReference<List<MailMessage>>`。
- [ ] 完成

## T3: 实现 Tmux 后端
- 影响文件: `src/main/java/com/mewcode/teams/TmuxBackend.java`（`spawnTmuxTeammate` @ 16-27；`stopTmuxTeammate` @ 29-41）
- 依赖任务: T1
- 完成标准: `spawnTmuxTeammate` 用 `ProcessBuilder("tmux", "new-window", "-d", "-n", paneName, cliCommand)` 创建后台窗口；30s 超时，非 0 退出码或超时抛 `RuntimeException`；`stopTmuxTeammate` 先 `send-keys C-c` 等 5s + `Thread.sleep(200)` 再 `kill-window`，best-effort 失败仅 `log.fine` 不重抛。
- [ ] 完成

## T4: 实现 iTerm2 后端
- 影响文件: `src/main/java/com/mewcode/teams/ITermBackend.java`（`spawnITermTeammate` @ 16-40；`stopITermTeammate` @ 42-61）
- 依赖任务: T1
- 完成标准: `spawnITermTeammate` 用 `osascript -e <AppleScript>` 在当前 window 创建 tab 设 name 并 `write text <cliCommand>`，内嵌双引号转义为 `\"`；30s 超时；`stopITermTeammate` AppleScript 遍历所有 window 的 tab 找 name 匹配的 close 掉，10s 超时、best-effort 失败仅 `log.fine`。
- [ ] 完成

## T5: 实现队员主循环 TeammateRunner.runInProcessTeammate
- 影响文件: `src/main/java/com/mewcode/teams/TeammateRunner.java`（常量 `LEAD_NAME / SHUTDOWN_PREFIX / IDLE_POLL_MS` @ 16-18；`runInProcessTeammate` @ 26-66；`waitForNextPromptOrShutdown` @ 142-170；`drainAgentEvents` @ 172-187）
- 依赖任务: T1, T2
- 完成标准: 主循环 7 步——1) addendum 非空时加为 system reminder；2) `injectPendingMessages` 把未读邮件转 system reminder；3) `addUserMessage(initialPrompt)`；4) `member.agent.run(conv)` 拿 event queue；5) `drainAgentEvents` 转发到 eventOut；6) `sendMessage(self, LEAD, "[idle]...")` 发 idle 通知；7) 进入 while 循环 `waitForNextPromptOrShutdown` 轮询，shutdown 或线程中断退出，命中新消息加为 user message 继续下一轮。退出前置 `member.active=false`。`drainAgentEvents` 收到 `LoopComplete` 或 `ErrorEvent` 即返回。
- [ ] 完成

## T6: 实现 Lead-side 通信原语
- 影响文件: `src/main/java/com/mewcode/teams/TeammateRunner.java`（`drainLeadMailbox` @ 72-92；`buildTeammateAddendum` @ 97-109；`injectPendingMessages` @ 114-127；`isShutdownRequest` @ 129-131；`createIdleNotification` @ 133-136）
- 依赖任务: T1, T2
- 完成标准: `drainLeadMailbox(null)` 返 `List.of()`；非空时遍历所有团队读 Lead 邮箱，按 `<team-notification team="X">\nfrom=Y: text\n...\n</team-notification>` 包装返字符串数组，并把读过的标记为已读。`buildTeammateAddendum` 文本必须含队员名、其他队友名、"通过 SendMessage 沟通"、"停止调用工具自动发 idle"四条信息。`injectPendingMessages` 在有未读时拼 `"You have new messages:\n\n..."` system reminder 并 `markAllRead`，无未读直接返回。`isShutdownRequest` 用 `text.strip().startsWith(SHUTDOWN_PREFIX)` 判定。`createIdleNotification` 产出 `"[idle] <name>: <reason> (at <iso-instant>)"`。
- [ ] 完成

## T7: 实现 SpawnDispatcher 统一入口
- 影响文件: `src/main/java/com/mewcode/teams/SpawnDispatcher.java`（`SpawnConfig` record @ 15-24；`SpawnResult` record @ 26-29；`spawnTeammate` @ 33-61；`recordExternalMember` @ 80-88）
- 依赖任务: T1, T3, T5
- 完成标准: `spawnTeammate` switch `team.getMode()` 分发；`IN_PROCESS` 路径调 `team.addMember` 注册（可选 `setWorkDir(workdir)`） → 置 `active=true` → `Thread.startVirtualThread` 跑 `runInProcessTeammate` → 返 `SpawnResult(IN_PROCESS, null)`；`TMUX` 路径先把 task 写入对方 mailbox（用 `team.sendMessage(LEAD_NAME, memberName, task)`） → `buildTeammateCLI` 拼命令 → `TmuxBackend.spawnTmuxTeammate` 拿 paneId → `recordExternalMember` 注册占位 member → 返 `SpawnResult(TMUX, paneId)`；未知 mode 抛 `IllegalStateException`。
- [ ] 完成

## T8: 实现 BuildTeammateCLI + shellQuote
- 影响文件: `src/main/java/com/mewcode/teams/SpawnDispatcher.java`（`buildTeammateCLI` @ 67-73；`shellQuote` @ 75-78）
- 依赖任务: T7
- 完成标准: `buildTeammateCLI` 用 `ProcessHandle.current().info().command().orElse("mewcode")` 拿当前可执行；workdir 空时默认 `System.getProperty("user.dir")`；返回 `cd <quoted_wd> && <quoted_exe> --teammate --team-name <quoted_team> --agent-name <quoted_member>`。`shellQuote` 简单字符（`[a-zA-Z0-9_./-]+` 正则命中）直接返回原串，含特殊字符时单引号包裹并把内嵌 `'` 替换为 `'\''`。
- [ ] 完成

## T9: 实现 Coordinator Mode 工具白名单
- 影响文件: `src/main/java/com/mewcode/teams/Coordinator.java`（`ALLOWED_TOOLS` @ 19-32；`isCoordinatorTool` @ 34-36）
- 依赖任务: 无
- 完成标准: 12 项白名单 `Set<String>`：`Agent / SendMessage / TaskCreate / TaskGet / TaskList / TaskUpdate / TeamCreate / TeamDelete / ReadFile / Glob / Grep / Bash`；`isCoordinatorTool(name)` 返回 set.contains 布尔（写工具 `WriteFile / EditFile` 等不在内）。
- [ ] 完成

## T10: 实现 SendMessage / TeamCreate / TeamDelete 三个工具
- 影响文件: `src/main/java/com/mewcode/teams/TeamTools.java`（`SendMessageTool` @ 20-72；`TeamCreateTool` @ 76-128；`TeamDeleteTool` @ 132-181）
- 依赖任务: T1
- 完成标准:
 - `SendMessageTool.execute`：`to/content` 必填；遍历所有团队找 `to` 这个 member 所在团队调 `team.sendMessage(senderName, to, content)` 投递；未匹配返 `recipient '<to>' not found in any team` 错误；schema 含 `to / content` 两个 string 必填字段。
 - `TeamCreateTool.execute`：`team_name` 必填；同名时追加 `-2/-3/...` 后缀去重；调 `TeamManager.detectBackend()` + `teamMgr.createTeam`；Output 含 `"Team \"X\" created (mode: Y). Use Agent tool with team_name=\"X\" to add teammates."`。
 - `TeamDeleteTool.execute`：`team_name` 必填；不存在返错误；调 `teamMgr.deleteTeam`（内部 `stopAll` 中断所有 member）；返回 `"Team \"X\" deleted. Stopped N member(s): a, b, c"` 清单。
- [ ] 完成

## T11: 实现 AgentNameRegistry 单例
- 影响文件: `src/main/java/com/mewcode/teams/AgentNameRegistry.java`（`INSTANCE` @ 12；`nameToId` map @ 13；`getInstance` @ 17；`register / resolve / unregister / listAll` @ 19-35）
- 依赖任务: 无
- 完成标准: 单例模式（`private static final INSTANCE`，私有构造）；`nameToId` 用 `LinkedHashMap` 保证遍历顺序；`register / resolve / unregister / listAll` 全部 `synchronized`；`resolve` 先查 name → id，未命中时检查 `containsValue(input)` 返回 input 本身（反向 id 寻址），都不命中返 null；`listAll` 返新建 `LinkedHashMap` 副本避免外部修改。
- [ ] 完成

## T12: 实现 SharedTaskStore
- 影响文件: `src/main/java/com/mewcode/teams/SharedTaskStore.java`（`SharedTask` record @ 21-32；常量 `MAPPER` + 字段 `filePath / nextId / tasks` @ 34-37；构造器 @ 39-42；`create` @ 44-50；`get` @ 52-54；`listTasks` @ 56-61；`update` @ 63-85；`load` @ 87-95；`save` @ 97-102）
- 依赖任务: 无
- 完成标准: `SharedTask` record 含 `id / title / description / status / assignee / blocks / blockedBy / createdBy` 字段，并提供 `withStatus / withAssignee` 不可变更新；`@JsonIgnoreProperties(ignoreUnknown=true)` 注解保证向前兼容；构造器 `new SharedTaskStore(teamDir)` 自动 load 已有 `tasks.json`；`create` 用 `AtomicInteger` 自增 id；`listTasks` 支持按 status/assignee 过滤；`update` 用记录类 wither 模式产新对象，`addBlocks/addBlockedBy` 是追加（用新建 ArrayList 拷贝旧值后 addAll）；全部 mutating 方法 `synchronized`；save 用 `MAPPER.writerWithDefaultPrettyPrinter()` 美化输出。
- [ ] 完成

## T13: 实现 FileMailBox 单元测试
- 影响文件: `src/test/java/com/mewcode/teams/FileMailBoxTest.java`（`sendCreatesFileWithMessage` @ 17-29；`readUnreadReturnsOnlyUnread` @ 31-41；`markAllReadMakesUnreadEmpty` @ 43-53；`nonexistentAgentReturnsEmpty` @ 55-60；`teamSendMessageIntegration` @ 62-74）
- 依赖任务: T1, T2
- 完成标准: 用 `@TempDir` 把 inbox 重定向到测试临时目录，避免污染仓库根；5 个用例覆盖——1) `send` 落盘后文件含 `from / text / read=false` 三字段；2) 连续 `send` 后 `readUnread` 返所有未读；3) `markAllRead` 后 `readUnread` 为空；4) 不存在的 agentId 返 `readUnread` 空列表；5) 集成测试创建 `Team` + 单独 mailbox 验证 send/read 完整流程。
- [ ] 完成

## T14: 实现 AgentTool team_name 分支
- 影响文件: `src/main/java/com/mewcode/agents/AgentTool.java`（新增 `teamMgr` 字段；`execute` 解析 `team_name` 参数；当 `team_name != null && teamMgr != null` 走 team 分支调 `SpawnDispatcher.spawnTeammate`；当 in-process 模式启虚拟线程消费 `eventOut` queue 转发到 `progressCh`）
- 依赖任务: T6, T7
- 完成标准: `AgentTool` 新增 `private TeamManager teamMgr` 字段及 setter；`execute` 在解析完 `subagent_type / prompt` 后检查 `team_name`，命中且 `teamMgr != null` 即走 team 分支；team 分支校验团队存在 + 同 team 同名 + 解析子工具池 + 可选 worktree + `TeammateRunner.buildTeammateAddendum` 构造 addendum + `SpawnDispatcher.spawnTeammate` 拿 result；in-process 模式启虚拟线程 `drainTeammateEvents` 消费事件流转 `SubAgentProgress` 喷进 `progressCh`；Output 含 backend hint 和 SendMessage 使用提示。
- [ ] 完成

## T15: TUI 接入
- 影响文件: `src/main/java/com/mewcode/tui/MewCodeModel.java`（`teamMgr` 字段；`registerAgentTools` 内创建 `TeamManager` 并注册三件套工具 + 注入 `AgentTool.teamMgr`；Lead 每轮迭代调 `TeammateRunner.drainLeadMailbox(teamMgr)` 拼到下一轮 system reminder；Lead Agent 工具调用前用 `Coordinator.isCoordinatorTool` 过滤）
- 依赖任务: T6, T9, T10, T14
- 完成标准:
 1. `MewCodeModel.teamMgr` 字段声明；
 2. `registerAgentTools`（或等价初始化方法）创建 `TeamManager` → 注册 `TeamCreateTool / TeamDeleteTool / SendMessageTool` → `AgentTool.setTeamMgr(teamMgr)`；
 3. Lead 每轮迭代开头调 `TeammateRunner.drainLeadMailbox(teamMgr)` 把 `<team-notification>` 字符串拼到要喂给模型的 system reminder；
 4. Lead 工具调用过滤：`teamMgr.listTeams().isEmpty()` 为空时放行全部，非空时 `Coordinator.isCoordinatorTool(name)` 判定；
 5. 程序退出 finally 块调 `teamMgr.closeAll()` 确保所有虚拟线程被中断。
- [ ] 完成

## T16: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T1-T15
- 完成标准:
 - `./gradlew build` 通过；
 - `./gradlew test` 通过（覆盖至少 `FileMailBoxTest` 5 个用例 + `TeamManagerTest` / `SpawnDispatcherTest` / `TeammateRunnerTest` / `CoordinatorTest` 共 15+ 用例，含 detectBackend 两档优先级、SendMessage 路由、SpawnDispatcher 校验、shellQuote、drainLeadMailbox、isShutdownRequest、createIdleNotification 等）；
 - 主流程接线验证：`rg "teamMgr|TeammateRunner|Coordinator\." src/main/java/com/mewcode/tui` 命中 TUI 装配点；`rg "TeamMgr|teamMgr" src/main/java/com/mewcode/agents/AgentTool.java` 看到 team 分支被 execute 调用。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15 / [ ] T16
```
```plain
# ch15: AgentTeam Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 枚举 `TeamManager.TeamMode` 在 `src/main/java/com/mewcode/teams/TeamManager.java:21` 存在，含 `IN_PROCESS / TMUX` 两档
- [ ] 内部类 `TeamManager.Team` 在 `TeamManager.java:70-134` 存在，字段 `name / mode / members / mailBox` 齐全，写方法全部 `synchronized`
- [ ] 内部类 `TeamManager.Member` 在 `TeamManager.java:136-151` 存在，字段 `name / agent / conv / active / thread`（后两者 `volatile`）齐全
- [ ] 静态方法 `TeamManager.detectBackend` 在 `TeamManager.java:53-62` 实现优先级 `TMUX env → which tmux → IN_PROCESS`
- [ ] Record 类 `FileMailBox.MailMessage` 在 `FileMailBox.java:16-21` 含 6 字段 `from / text / timestamp / read / color / summary`，便利构造器自动填 timestamp/read=false
- [ ] `FileMailBox.withLock` 在 `FileMailBox.java:76-112` 使用 `Files.createFile` 抛 `FileAlreadyExistsException` 时重试，10 次 5-100ms 随机退避，>10s 过期清理
- [ ] Record 类 `SpawnDispatcher.SpawnConfig / SpawnResult` 在 `SpawnDispatcher.java:15-29` 存在
- [ ] 常量 `TeammateRunner.LEAD_NAME = "lead"` / `SHUTDOWN_PREFIX = "[shutdown]"` / `IDLE_POLL_MS = 500L` 在 `TeammateRunner.java:16-18`
- [ ] `Coordinator.ALLOWED_TOOLS` `Set<String>` 在 `Coordinator.java:19-32` 含 12 项白名单（写工具 `WriteFile / EditFile` 等被排除）
- [ ] `TeammateRunner.runInProcessTeammate` 在 `TeammateRunner.java:26-66` 主循环七步齐全：addendum 注入 → injectPendingMessages → addUserMessage → agent.run + drainAgentEvents → idle 通知 → while 循环 waitForNextPromptOrShutdown
- [ ] `SpawnDispatcher.buildTeammateCLI` 在 `SpawnDispatcher.java:67-73` 输出 `cd <quoted_wd> && <quoted_exe> --teammate --team-name <quoted> --agent-name <quoted>`；`shellQuote` 在 `:75-78` 简单字符直接返回、特殊字符单引号 POSIX 转义
- [ ] `TeammateRunner.buildTeammateAddendum` 在 `TeammateRunner.java:97-109` 文本包含 "member of team"、"Your name is"、"SendMessage tool"、"idle notification will be sent to the lead automatically" 四个关键信息
- [ ] `TeammateRunner.drainLeadMailbox` 在 `TeammateRunner.java:72-92` null 安全（`teamMgr == null` 返 `List.of()`）、读完后调 `markAllRead`、输出格式 `<team-notification team="X">\n...\n</team-notification>`
- [ ] `TeamTools.SendMessageTool.execute` 在 `TeamTools.java:54-71` 遍历所有团队找 `to` member 投递，未匹配返 `recipient '<to>' not found in any team` 错误
- [ ] `TeamTools.TeamCreateTool.execute` 在 `TeamTools.java:108-127` 同名冲突自动追加 `-2/-3/...` 后缀去重
- [ ] `TeamTools.TeamDeleteTool.execute` 在 `TeamTools.java:163-180` 返回 `"Team \"X\" deleted. Stopped N member(s): a, b, c"` 清单
- [ ] `AgentNameRegistry` 在 `AgentNameRegistry.java:10-36` 是单例（`getInstance`），全部方法 `synchronized`；`resolve` 支持反向 id 寻址
- [ ] `SharedTaskStore` 在 `SharedTaskStore.java:18-103` 实现 `create / get / listTasks / update`，全部 `synchronized`；`update` 用 wither 模式产新 record，`addBlocks/addBlockedBy` 追加而非替换

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `rg "new TeamManager\\(\\)" src/main/java/com/mewcode/tui` 在 TUI 装配代码找到 `TeamManager` 实例化点
- [ ] `rg "TeamCreateTool|TeamDeleteTool|SendMessageTool" src/main/java/com/mewcode/tui` 在 TUI 找到三个工具注册点
- [ ] AgentTool 注入 `teamMgr` 的代码在 TUI 装配处可见（`agentTool.setTeamMgr(teamMgr)` 或构造器注入）
- [ ] `rg "drainLeadMailbox" src/main/java/com/mewcode/tui` 命中 Lead 每轮迭代调用点（把 `<team-notification>` 注入下一轮 system reminder）
- [ ] `rg "Coordinator.isCoordinatorTool" src/main/java/com/mewcode/tui` 命中 Lead 工具调用过滤点
- [ ] `MewCodeModel.teamMgr` 字段在 TUI 主模型类中声明
- [ ] `rg "teamMgr" src/main/java/com/mewcode/agents/AgentTool.java` 看到 `AgentTool` 的 `team_name` 分支调用 `SpawnDispatcher.spawnTeammate`
- [ ] `rg "SpawnDispatcher.spawnTeammate" src/main/java/com/mewcode/agents` 命中 in-process 模式下虚拟线程消费 eventOut 的 `drainTeammateEvents` 调用
- [ ] 程序退出 finally 块调 `teamMgr.closeAll()` 确保所有虚拟线程被中断

## 3. 编译与测试

- [ ] `./gradlew build` 通过
- [ ] `./gradlew test` 通过（覆盖至少 15 个用例：FileMailBoxTest 5 个 + TeamManagerCRUD / DetectBackendFallback / DetectBackendPrefersTmuxWhenInside / SendMessageToolRoutes / TeamCreateNameCollision / TeamDeleteStopsMembers / IsShutdownRequest / CreateIdleNotification / DrainLeadMailbox / DrainLeadMailboxNullSafe / ShellQuote / BuildTeammateCLIFormat / SpawnDispatcherInProcess / SpawnDispatcherTmuxValidation / CoordinatorAllowedTools / SharedTaskStoreCRUD / AgentNameRegistryRoundtrip）
- [ ] `./gradlew check` 无警告（含 SpotBugs / Checkstyle 若启用）
- [ ] 测试运行不在仓库根残留 `.mewcode/teams/` 目录（`@TempDir` 重定向到 tmp）
- [ ] FileMailBox 并发测试用 `ExecutorService` + `CountDownLatch` 验证文件锁正确性，多线程并发 `send` 后 `readUnread` 数量与发送次数一致

## 4. 端到端验证

- [ ] 注册路径：TUI 启动后装配代码创建 `TeamManager` 并把 `TeamCreate / TeamDelete / SendMessage` 三件套放入 registry；用户向 Lead 说 "create a team to refactor X" → LLM 调 `TeamCreate(team_name="refactor-X")` → `detectBackend()` 选模式 → Output 返回 `"Team \"refactor-X\" created (mode: ...). Use Agent tool with team_name=\"refactor-X\" to add teammates."`
- [ ] Spawn 路径：Lead 继续说 "spawn alice to do data layer" → LLM 调 `Agent(team_name="refactor-X", name="alice", prompt="...")` → `AgentTool.execute` 识别 `team_name` 分支调 `SpawnDispatcher.spawnTeammate(IN_PROCESS|TMUX)` → 队员开始干活
- [ ] 通信路径：队员 alice 通过 `SendMessage(to="bob", content="...")` 给 bob 写 mailbox → bob 下一轮 idle poll 拿到消息作为 user message 注入对话
- [ ] Lead 感知路径：每个队员 turn 结束写 `[idle] alice: completed initial task (at <iso>)` 通知到 Lead 邮箱 → Lead 下一轮迭代调 `drainLeadMailbox` 抽出 `<team-notification team="refactor-X">\nfrom=alice: [idle] ...\n</team-notification>` 注入 Lead 上下文
- [ ] Coordinator Mode 路径：团队存活期间 Lead 每轮工具调用前 `Coordinator.isCoordinatorTool` 过滤，调用 `WriteFile` / `EditFile` 会被拒绝；`TeamDelete` 清空所有团队后下一轮恢复全工具集
- [ ] Tmux 后端：`TMUX` env 非空时 `detectBackend` 返 `TMUX` → spawn 时先把 task 写 mailbox → `tmux new-window -d` 拉起新窗口跑 `mewcode --teammate ...` → 子进程加载同一 mailbox 目录 → 第一次 idle poll 拿到初始任务开始干活
- [ ] iTerm 后端（备用）：`ITermBackend` 类已实现 `spawnITermTeammate / stopITermTeammate`，可通过手工调用验证 AppleScript 解析正确（`SpawnDispatcher` 当前未接此分支，作为后续扩展点）
- [ ] 关闭路径：`TeamDelete(team_name="refactor-X")` → `teamMgr.deleteTeam` → `team.stopAll` 遍历 member 调 `thread.interrupt()`（in-process）或 `TmuxBackend.stopTmuxTeammate`（tmux）→ 全部清理后 Lead 下轮恢复全工具集
- [ ] JVM 退出路径：`teamMgr.closeAll()` 在 TUI 程序 finally 块调用，所有虚拟线程被中断、所有 tmux 窗口被关闭

## 5. 文档

- [ ] `docs/java/ch15/spec.md` 已写
- [ ] `docs/java/ch15/tasks.md` 已写，16 个 T 全部勾完
- [ ] `docs/java/ch15/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch15` 与三件套关闭状态（待用户确认后由人或 CI 触发）
```