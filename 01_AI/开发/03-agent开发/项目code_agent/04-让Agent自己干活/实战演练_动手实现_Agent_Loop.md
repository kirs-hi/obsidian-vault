# 第4章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装了六个工具，实现了 [[01基础_12理解函数调用Function Call|Function Calling]]，它能读文件、写文件、搜代码、执行命令。但每次只能做一步——模型返回一个 tool\_ use，你执行完返回结果，模型给个最终回复，结束。你得一步步催它。

这一章要给 MewCode 装上 [[理论学习_ReAct_范式与_Agent_Loop|Agent Loop]]。做完之后，模型能自主循环执行多步操作：自己读代码、自己写代码、自己跑命令、自己根据结果决定下一步，直到任务完成。它从「一步一停的工具调用」变成了真正能自主干活的 [[07-Agent|Agent]]。

具体要新增这些东西：

-   **Agent 组件** ：持有 LLM 客户端、工具注册中心和配置，驱动核心循环
-   **Agent Loop 循环逻辑** ：ReAct 模式的 while 循环，五种停止条件
-   **AgentEvent 事件流** ：让 Agent 和 UI 完全解耦
-   **流式收集器** ：实时透传文本，积攒完整响应
-   **工具分批执行** ：partitionToolCalls，安全的并发、不安全的串行
-   **Plan Mode** ：/plan 只启用读工具输出计划，/do 切换回正常模式

这章 **不做** ：权限系统、[[理论学习_上下文压缩与_Token_管理|上下文压缩]]、用户确认机制（后续章节）。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 循环本体用 ReAct 范式：一轮 = 调 LLM → 拿到响应 → 有工具调用就执行 → 结果回填 → 下一轮；没有工具调用就结束。
- 对外用事件流（channel）暴露过程：用户消息、模型 thinking、模型文本、工具调用开始、工具结果、最终回复、错误都作为事件吐出，让上层（TUI / CLI）按需消费。
- 状态机思维：每轮结束判断"继续 / 终止"，终止情形包括模型显式 end_turn、无工具调用、达到最大轮数上限、用户取消。
- 工具分批执行：一轮响应里如果模型同时要调多个工具，按读类（安全）/ 写类（互斥）分组，读类可并发、写类串行。
- 只规划不执行的模式：用一个开关切进 plan-only 状态，进入后只允许读类工具，写类工具拦截并提示用户去掉开关；最终输出一份计划交还用户审批。
- 取消与超时：循环要能响应外部 cancel（context 一类），中途打断不能让状态错乱。

# 明确不做（留给后续章节）
- 复杂的系统提示词组装，本章用最小可用 system prompt 跑起来即可。
- 完整的权限策略，本章只在工具执行前后留拦截位，不实现具体规则。
- 把 Agent 当工具递归调用（子任务委派）。
- 其他后续章节能力一律不做。
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了 ，然后让 [[Claude Code 命令与最佳实践|Claude Code]] 根据这三份文档进行开发

![](实战演练_动手实现_Agent_Loop-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现_Agent_Loop-2.jpeg)

### 功能验证过程

来验收一下结果

启动 MewCode，给它一个需要多步完成的任务，比如「帮我创建一个 hello.txt 文件，写入 Hello World，然后读出来确认内容正确」。

如果 Agent Loop 正常工作，你会看到模型自主循环：先调 WriteFile 创建文件，再调 ReadFile 读取确认，最后给你一个总结回复，这就是典型的ReAct模式啦。

![](实战演练_动手实现_Agent_Loop-3.jpeg)

接着看看plan mode，我们切换到plan mode后，就会变成了只读，只能写Plan文件

![](实战演练_动手实现_Agent_Loop-4.jpeg)

这时可以看到只有可读工具，我们如果让他写入文件，是做不到的

帮我创建一个 hello.txt 文件，写入 Hello World，然后读出来确认内容正确

![](实战演练_动手实现_Agent_Loop-5.jpeg)

那我们再给它一个plan任务试试，我说

我要做个电商系统

![](实战演练_动手实现_Agent_Loop-6.jpeg)

可以看到，它会开始触发AskUserQuestion工具，来进行需求澄清，我们根据问题，一步步澄清需求

![](实战演练_动手实现_Agent_Loop-7.jpeg)

之后，会生成一个Plan文件，里面是我们的开发计划

![](实战演练_动手实现_Agent_Loop-8.jpeg)

可以看到，其中它遇到了一些麻烦，写入失败了，但是模型立刻就根据错误，来调整策略，然后成功写入了，这就是再一次的ReAct的体现之一

Plan计划在放在.mewcode/plans下面，我们可以看看这个计划的内容

![](实战演练_动手实现_Agent_Loop-9.jpeg)

然后我们就可以去让MewCode根据这个Plan去开发了

![](实战演练_动手实现_Agent_Loop-10.jpeg)

验收没问题，那么本章的主要任务就完成了。下一章，我们给它加上安全边界，让它在帮你干活的同时守护了你项目的边疆。

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

[[提示词]]如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch04: Agent Loop Spec

## 1. 背景

LLM 单次回复不能完成完整软件任务，必须把「调模型 → 拿工具调用 → 跑工具 → 把结果回灌」组成 ReAct 循环反复跑，直到模型不再请求工具。没有这层 Agent Loop，工具系统（ch03）和后续所有模块（ch05~ch15）都没有挂载点；流式 token、思考块、token 配额、用户中断、Plan Mode、HITL 权限请求都只能停留在工具层无法上浮到 UI。本章把这条循环、配套事件流和 Plan Mode 状态机做出来。

## 2. 目标

对外提供 `agent.Agent`：调用者构造好 LLM 客户端、Tool Registry、（可选）Permission Checker / Hooks / NotificationFn 后，调一次 `Run(ctx, conv)` 拿到一个 AgentEvent 通道；TUI 只负责把事件 fan-out 到屏幕，剩余的工具分发、流式拼接、回卷、Plan Mode reminder 注入、max_tokens 恢复全部由 Agent 在后台串好。Plan Mode 通过 Permission Checker 的模式字段切换；Plan 文件存档由 `internal/planfile` 承担；TodoList 工具由 `internal/todo` 提供并由 TUI 注册到 Registry。

## 3. 功能需求

- F1: `Agent.Run(ctx, conv)` 启动后台 goroutine 跑 ReAct 循环并返回事件 channel；循环退出后 channel 关闭。
- F2: 每一轮迭代先调上下文管理（ch08 两层压缩），再按需注入 Plan Mode reminder 和 NotificationFn 上报的提醒。
- F3: 通过 LLM 客户端流式拉取事件，把文本与思考流转成对应的 `StreamText` / `ThinkingText`，把工具调用三段（start / delta / complete）转成 `ToolUseEvent`。
- F4: 工具调用一边流式接收一边并行执行；本轮结束时收齐所有结果，按工具结果上限截断后回灌会话。
- F5: 主循环终止条件：本轮没有工具调用 → 写入 assistant 消息并发 `LoopComplete`；连续多次未知工具调用 → `ErrorEvent` 退出；ctx 取消 → 直接退出；超过 `MaxIterations`（若设置）→ `ErrorEvent` 退出。
- F6: 处理 `stop_reason == "max_tokens"`：首次升档放宽 max_tokens 上限，并在有限轮数内尝试恢复指令；超出预算仍未完成则错误退出。
- F7: 处理 stream 错误分流：`ContextTooLongError` → 调用强制压缩后重试；`RateLimitError` → 解析 retry-after 后 sleep 重试；其它错误 → `ErrorEvent` 退出。
- F8: 权限交互：Checker 返回 Deny 时给工具一个错误结果；返回 Ask 时发 `PermissionRequestEvent` 走 HITL，收到「Allow Always」时把工具规则 append 到本地规则文件。
- F9: 工具执行包夹 hooks：执行前走 `EventPreToolUse`（可阻断），执行后走 `EventPostToolUse`（不阻断）；从工具参数里提取代表性路径供 hook 的 glob 匹配。
- F10: 提供 `ToolNameFilter` 在每轮取 schema 时按 allowlist 过滤，支持 Coordinator Mode 动态切换可用工具集。
- F11: Plan Mode 文件状态：提供 plan slug 生成 + 单例 path + 存读 + Reset + Exists 查询，配合 TUI 的 `/plan` / `/do` / `ExitPlanMode` 流程维护当前 Plan 文件。
- F12: Todo 子系统：提供任务模型与 JSON 持久化 Store，外加四个标准工具（Create / Get / List / Update），由 TUI 在选好 session 后注册到 Registry。

## 4. 非功能需求

- N1: 工具并发安全：只读工具可并发执行，写 / 命令类工具串行执行，并发与顺序边界由专门的分区函数明确。
- N2: 事件 channel 有缓冲，避免短瞬突发事件阻塞产生 goroutine。
- N3: 工具结果回灌前按工具模块给出的上限截断并追加截断提示，防止单工具结果撑爆下一轮上下文。
- N4: 工具参数中的代表性路径提取顺序按常见 schema 字段优先（`file_path` / `path` / `pattern` / `target` 等），覆盖六个核心工具。
- N5: Plan Mode 的 slug 必须有可读形式（不能用纯 timestamp），便于人眼区分 Plan 文件。

## 5. 设计概要

- 核心数据结构:
 - `Agent`: Client / Registry / Protocol / WorkDir / MaxIterations / ContextWindow / Checker / Hooks / NotificationFn / ToolNameFilter / 压缩状态等字段。
 - `AgentEvent` sum type: StreamText / ThinkingText / ToolUseEvent / ToolResultEvent / TurnComplete / LoopComplete / UsageEvent / ErrorEvent / CompactEvent / RetryEvent / PermissionRequestEvent / AskUserQuestionEvent。
 - `StreamingExecutor`: 把流式产出的工具调用立刻起 goroutine 执行，主循环统一收齐结果。
 - `Task` / `TaskStatus` / `TaskList` / `Store`（todo 模块）：单文件 JSON 持久化，内含隐藏任务标记。
 - `planfile` 包级单例：当前进程内的 Plan 文件路径。
- 主流程（一次迭代）:
 1. 计入 iteration、检查 MaxIterations / ctx；
 2. 调上下文管理走两层压缩；
 3. ModePlan 时插入 Plan Mode reminder；
 4. 拉 NotificationFn 上报的提醒；
 5. 取 schemas（按 ToolNameFilter 过滤）；
 6. 调 `Client.Stream`，把增量 token / 思考 / 工具调用转 AgentEvent，工具调用即提交给 StreamingExecutor；
 7. 累计 token usage，处理 max_tokens 升档 / 恢复；
 8. 没有工具调用 → 落 assistant 消息 + `LoopComplete` 退出；
 9. 有工具调用 → 落 assistant 消息、收齐 tool 结果、截断后落 tool_result、发 `TurnComplete` 进入下一轮。
- 调用链:
 - 用户输入 → TUI 调 `Agent.Run` → 事件回灌 TUI 的事件处理函数。
 - `/plan` 命令 → TUI 把 Checker 切到 Plan Mode + 设置 PlanFilePath → 下一轮 Agent.Run 注入 reminder。
 - 工具执行 → `Agent.executeSingleTool` 调 `Checker.Check` → Ask 时回灌 `PermissionRequestEvent`，TUI 渲染选项并回应。
 - Todo 工具 → TUI 注册到 Registry → Agent 在工具循环中通过普通 Tool 接口调用。
- 与其他模块的交互:
 - 依赖 `internal/conversation`、`internal/llm`、`internal/tools`、`internal/compact`、`internal/permissions`、`internal/hooks`、`internal/prompt`（Plan Mode reminder）。
 - 被 `internal/tui`、`internal/agents`（SubAgent）、`internal/teams` 调用。

## 6. Out of Scope

- 本章不实现 SubAgent / Fork（属 ch13）；`Run` 只跑一个 Agent。
- 本章不实现 Worktree 隔离（属 ch14）；Plan 文件直接落本进程 cwd。
- Plan Mode 的 5-Phase Workflow / Reentry / Exit Reminder 文本已抄过来，但只有「进入 Plan → 写 plan → 退出 Plan」主路径必须通；Reentry / Exit reminder 的 TUI 接入留给下章或专门 PR。
- TodoList 的 Owner / Blocks / BlockedBy 字段已有数据模型，但不要求 UI 渲染依赖图。
- 除 max_tokens 以外的其他 stop_reason（pause_turn / refusal）不处理。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch04: Agent Loop Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。本章为验收，所有任务已经在仓库里落地，逐项标注真实文件 / 函数 / 行号。

## T1: 定义 AgentEvent 事件家族
- 影响文件: `internal/agent/events.go`（已新建）
- 依赖任务: 无
- 完成标准: `events.go` 定义 `AgentEvent` 接口，`StreamText` / `ThinkingText` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `ErrorEvent` / `CompactEvent` / `RetryEvent` / `PermissionRequestEvent` / `AskUserQuestionEvent`（agent.events.go:7-62）皆实现 `agentEvent`。`PermissionResponse` 三态常量 `PermAllow` / `PermDeny` / `PermAllowAlways` 在 events.go:33。

## T2: 实现 `Agent` 类型与 `New` 构造
- 影响文件: `internal/agent/agent.go:29-59`
- 依赖任务: T1
- 完成标准: `Agent` 拥有 `Client`/`Registry`/`Protocol`/`WorkDir`/`MaxIterations`/`ContextWindow`/`Checker`/`Hooks`/`NotificationFn`/`ToolNameFilter`/`compactTracking` 字段；`New(client, registry, protocol)` 给出默认 `MaxIterations=0` / `ContextWindow=200000` / `WorkDir=os.Getwd()`。

## T3: 实现 Run 主循环（ReAct）
- 影响文件: `internal/agent/agent.go:61-248`
- 依赖任务: T1, T2
- 完成标准: `Run` 返回 buffer 32 的 `<-chan AgentEvent`；后台 goroutine 用 `for iteration := 1; ; iteration++` 跑循环，结束时 `defer close(ch)`；每轮先 `compact.ManageContext`，再处理 Plan Mode reminder / Notification 注入；通过 `Client.Stream` 拿事件后扇出工具调用并并发执行；`stop_reason="max_tokens"` 走升档 + 多轮恢复（常量 `maxTokensCeiling=64000` / `maxOutputTokensRecoveries=3`，agent.go:24-27）；连续 3 次未知工具 → `ErrorEvent`+退出；无工具调用 → `LoopComplete`+退出。

## T4: 实现 `StreamingExecutor` 并发工具调度
- 影响文件: `internal/agent/streaming_executor.go`
- 依赖任务: T2
- 完成标准: `StreamingExecutor` 拥有 `registry`/`checker`/`eventCh`/`mu`/`pending`/`wg`；`Submit` 即提交即 goroutine 执行；`CollectResultswg.Wait` 后按 submit 顺序收集；提供 `HasPending`/`Reset` 给 SubAgent / Teams 复用。

## T5: 实现单工具执行 + 权限 + Hook 包夹
- 影响文件: `internal/agent/agent.go:300-446`
- 依赖任务: T2, T4
- 完成标准: `executeSingleTool`（agent.go:347）拿不到工具→ `isUnknown=true`；`Checker.Check` 拿 `Deny` 走错误结果，拿 `Ask` 通过 `PermissionRequestEvent` 走 HITL，拿 `PermAllowAlways` 调 `RuleEngine.AppendLocalRule` 把 `ToolName(content*)` 持久化；hook 调用 `EventPreToolUse`（可阻断）+ `EventPostToolUse`（不阻断），从参数提取 `extractFilePath`（agent.go:338，优先级 `file_path → path → pattern → target`）。

## T6: 实现 stream 错误恢复
- 影响文件: `internal/agent/agent.go:264-298`
- 依赖任务: T3
- 完成标准: `handleStreamError` 对 `*llm.ContextTooLongError` 调 `compact.ForceCompact` 后返回 true 重试；对 `*llm.RateLimitError` 调 `parseRetryAfter(rlErr.RetryAfter)` 后 sleep 重试；其他错误返回 false 让上层发 `ErrorEvent`。`parseRetryAfter` 解析整数秒；默认 5 秒。

## T7: 实现 `ToolNameFilter` schema 过滤
- 影响文件: `internal/agent/agent.go:101-104`、`agent.go:253-262`
- 依赖任务: T3
- 完成标准: 主循环每轮取 `Registry.GetAllSchemas` 后用 `filterSchemasByName` 跑一遍 allow 函数；`Agent.ToolNameFilter` 字段允许 Coordinator Mode 动态启停而不重启 Agent；`TestFilterSchemasByName` 覆盖（agent_test.go:897/917）。

## T8: 实现 Plan Mode reminder 单元
- 影响文件: `internal/prompt/plan_mode.go`
- 依赖任务: 无（独立模块）
- 完成标准: 完整 reminder 抄自目标实现（plan_mode.go:5-61，5 阶段 Workflow 完整保留）；稀疏 reminder（plan_mode.go:63）；`BuildPlanModeReminder(planFilePath, planExists, iteration)`：iteration==1 给完整版，否则按 `reminderInterval=5` 周期重发完整版，间隔时给稀疏版。`BuildPlanModeReentryReminder` / `BuildPlanModeExitReminder` 已抄但目前 TUI 未调用（记录为未来增强）。

## T9: 实现 planfile 存档单例
- 影响文件: `internal/planfile/planfile.go`
- 依赖任务: 无
- 完成标准: `PlansDir=".mewcode/plans"`；`generateSlug` 用 adjective+noun+`MMDD-HHMM` 生成可读 slug（planfile.go:19-34）；`GetOrCreatePlanPath` 单例懒加载；`GetPlanFilePath` / `ResetPlanPath` / `PlanExists` / `LoadPlan` / `SavePlan` 在 TUI `/plan/doExitPlanMode` 流程间维护进程内单例。`SetPlanFilePath` / `IsPlanFilePath` 已实现但当前无调用方（记录为预留 API）。

## T10: 实现 Todo 数据层与四工具
- 影响文件: `internal/todo/todo.go`、`internal/todo/store.go`、`internal/todo/tools.go`
- 依赖任务: 无
- 完成标准: `Task` 含 `ID`/`Subject`/`Description`/`ActiveForm`/`Status`/`Owner`/`Blocks`/`BlockedBy`/`Metadata`（todo.go:17-27）；`TaskList.Create/Get/List/Update` 加锁；`status="deleted"` 直接物理删除（todo.go:122-134）；`List` 跳过 `metadata._internal=true` 的项；`Store` 用 `.mewcode/tasks/<listID>.json` 保存。四个 Tool 实现 `Name/Category/Description/Schema/Execute` 接口。

## T11: 接入主流程（TUI）
- 影响文件: `internal/tui/tui.go:360-376` / `:722-738`（构造 Agent 与 Checker）、`:536-539`（注册 Todo 工具）、`:1197-1232`（`/plan/do`）、`:1907/1941`（启动 `Run`）、`:2021`（事件分发）
- 依赖任务: T2~T10
- 完成标准: 用户进入聊天后 TUI 调 `agent.New` 并装好 `Checker`/`Hooks`/`NotificationFn`/`ToolNameFilter`；发送消息时 `m.agentCh = m.ag.Run(ctx, m.conversation)`；事件分发函数把每个 AgentEvent 转成 TUI 渲染指令；`/plan` 切换 `Checker.Mode=ModePlan` 并设置 `PlanFilePath`，`/do` 恢复模式 + `ResetPlanPath`。

## T12: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T11
- 完成标准:
 - `go build ./...` 通过（已验证）。
 - `go test ./internal/agent/...` 关键单测通过：`TestAgentSimpleResponse`、`TestAgentToolCallLoop`、`TestAgentMaxIterations`、`TestAgentWithThinking`、`TestMultiRoundConversation`、`TestFilterSchemasByName`、`TestFilterSchemasByNameEmptyInput`（agent_test.go:155 起）。
 - 在 TUI 输入 `hello` 看到流式文本与 `LoopComplete` 终止；输入 `/plan` 看到 plan reminder 注入并禁止写工具。

## 进度
- [ ] T1 events.go 已实现
- [ ] T2 Agent 类型 + New
- [ ] T3 Run 主循环
- [ ] T4 StreamingExecutor
- [ ] T5 executeSingleTool + 权限 + Hook
- [ ] T6 handleStreamError
- [ ] T7 ToolNameFilter
- [ ] T8 plan_mode.go reminder
- [ ] T9 planfile.go 单例
- [ ] T10 todo 模块
- [ ] T11 TUI 接入
- [ ] T12 端到端验证（编译通过 + agent_test 单测通过 + TUI Run 调用链确认）
```
```plain
# ch04: Agent Loop Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。

## 1. 实现完整性
- [ ] 类型 `Agent` 在 `internal/agent/agent.go:29-47` 实现，字段包含 `Client`/`Registry`/`Protocol`/`WorkDir`/`MaxIterations`/`ContextWindow`/`Checker`/`Hooks`/`NotificationFn`/`ToolNameFilter`/`compactTracking`/`eventCh`（`grep -n "type Agent struct" internal/agent/agent.go`）
- [ ] 接口 `AgentEvent` + 12 个具体事件类型在 `internal/agent/events.go:5-62`，全部实现 `agentEvent()` 标记方法（`grep -n "agentEvent()" internal/agent/events.go` 至少返回 12 条）
- [ ] 函数 `Agent.Run` 在 `internal/agent/agent.go:61` 实现，返回 `<-chan AgentEvent`，buffer=32（`grep -n "make(chan AgentEvent, 32)" internal/agent/agent.go`）
- [ ] 常量 `maxTokensCeiling=64000` 与 `maxOutputTokensRecoveries=3` 在 `internal/agent/agent.go:24-27`（ 和）
- [ ] `StreamingExecutor.Submit/CollectResults/HasPending/Reset` 在 `internal/agent/streaming_executor.go:36/54/67/73` 实现，使用 `sync.WaitGroup` 等待并发完成
- [ ] 单工具执行：`executeSingleTool` 在 `internal/agent/agent.go:347` 处理 unknown tool / permission Deny / permission Ask / Hook PreToolUse / Hook PostToolUse 五个分支
- [ ] 错误恢复：`handleStreamError` 在 `internal/agent/agent.go:264` 处理 `*llm.ContextTooLongError` 和 `*llm.RateLimitError`；`parseRetryAfter` 在 agent.go:290 默认 5 秒
- [ ] Plan reminder：`BuildPlanModeReminder` 在 `internal/prompt/plan_mode.go:85`，`reminderInterval=5`，iteration==1 给完整 reminder
- [ ] `planfile.GetOrCreatePlanPath` / `PlanExists` / `LoadPlan` / `SavePlan` / `ResetPlanPath` 在 `internal/planfile/planfile.go:36/62/70/84/58` 实现
- [ ] 任务模型 `Task` / `TaskList` / `Store` 与四个工具在 `internal/todo/todo.go:17`、`todo.go:29`、`store.go:9`、`tools.go:11/64/121/180`
- [ ] 边界 `extractFilePath` 在 `internal/agent/agent.go:338` 按 `file_path → path → pattern → target` 顺序查找

## 2. 接入完整性（必查，杜绝死代码）
- [ ] `grep -rn "agent.New\b" internal/tui` 至少 2 个非测试调用方（`internal/tui/tui.go:360`、`internal/tui/tui.go:722`）
- [ ] `grep -rn "m\.ag\.Run\b" internal/tui` 至少 2 个调用方（`internal/tui/tui.go:1907` 与 `:1941`）
- [ ] `grep -rn "BuildPlanModeReminder" internal --include="*.go"` 至少 1 个调用方在 agent loop（`internal/agent/agent.go:91`）
- [ ] `grep -rn "planfile\." internal --include="*.go"` 调用方在 TUI `/plan/doExitPlanMode` 流程（`internal/tui/tui.go:1202/1225/1226/1229/1397/1398/1418` 与 `internal/agent/agent.go:89/90`）
- [ ] `grep -rn "todo\.TaskCreateTool\|todo\.TaskGetTool\|todo\.TaskListTool\|todo\.TaskUpdateTool" internal/tui` 全 4 个工具均在 `internal/tui/tui.go:536-539` 注册
- [ ] `grep -rn "permissions.NewChecker" internal --include="*.go"` 在 TUI 构造 Agent 时使用（`internal/tui/tui.go:362` 与 `:724`）
- [ ] `Agent.ToolNameFilter` 字段在 TUI `internal/tui/tui.go:370` 与 `:732` 设值（`coordinatorToolFilter`）
- [ ] `Agent.NotificationFn` 字段在 TUI `internal/tui/tui.go:369` 与 `:731` 设值（`drainTaskNotifications`）
- [ ] 死代码已清理（2026-05-21）:
 - [ ] `executeToolCalls` / `partitionToolCalls` / `toolBatch` 已删（`StreamingExecutor` 替代后冗余，目标设计 `StreamingToolExecutor.canExecuteTool` 已覆盖语义）
 - [ ] `buildEnvironmentContext` 已删（与 `prompt/sections.go:123 EnvironmentSection` 重复，目标设计 `constants/prompts.ts:640 computeEnvInfo` 走 system prompt 通道）
 - [ ] `planfile.SetPlanFilePath` / `IsPlanFilePath` 已删
 - [ ] `BuildPlanModeReentryReminder` 已删
 - [ ] `BuildPlanModeExitReminder` 已接入 `internal/tui/tui.go:1400executePlanApproval`

## 3. 编译与测试
- [ ] `go build ./...` 通过（顶层命令，2026-05-21 已验证）
- [ ] `go test ./internal/agent/...` 中 `TestAgentSimpleResponse` / `TestAgentToolCallLoop` / `TestAgentMaxIterations` / `TestAgentWithThinking` / `TestMultiRoundConversation` / `TestFilterSchemasByName` / `TestFilterSchemasByNameEmptyInput` 七个单测可独立执行（agent_test.go 中 `func Test*` 已定义）
- [ ] `go vet ./...` 无警告（2026-05-21 顶层运行无输出）

## 4. 端到端验证
- [ ] TUI 入口：用户在聊天框敲一条普通消息后看到 `StreamText` 渲染、最终 `LoopComplete` 终止 —— `internal/tui/tui.go:2023` (`agent.StreamText`) 与 `:2194` (`agent.LoopComplete`) 显式分发，调用链 `m.sendMessage → m.ag.Run → handleAgentEvent`（tui.go:1907 → events.go → tui.go:2021-2200）
- [ ] Plan Mode：输入 `/plan` 进入 Plan，注入 reminder + 设 `Checker.Mode=ModePlan` + 创建 plan path；输入 `/do` 退出 Plan + ResetPlanPath（`tui.go:1197-1232`）
- [ ] HITL 权限：当 Ask 时 TUI 渲染 `Yes / Yes, don't ask again / No` 选项（tui.go:1292-1296，`PermAllow/PermAllowAlways/PermDeny`）
- [ ] 留存证据: 验收阶段无截图；如需补，可在 TUI 中输入 `hi` 拍照保存 stream 渲染

## 5. 文档
- [ ] spec.md / tasks.md / checklist.md 三件套齐全（`specs/go/ch04/`）
- [ ] commit 信息标注 `ch04` 与三件套关闭状态（待统一打包提交）
```

### Python

```plain
# ch04: Agent Loop Spec

## 1. 背景

LLM 单次回复无法完成完整软件任务，必须把「调模型 → 拿工具调用 → 跑工具 → 把结果回灌」组成 ReAct 循环反复运行，直到模型不再请求工具。没有这层 Agent Loop，工具系统（ch03）与后续模块（ch05~ch15）都失去挂载点；流式 token、思考块、token 配额、用户中断、Plan Mode、HITL 权限请求都只能停留在工具层，无法上浮到 Textual 终端 UI。本章把这条循环、配套事件流、Plan Mode 状态与 max_tokens 升档串到 `mewcode/agent.py` 一个文件内。

## 2. 目标

对外提供 `mewcode.agent.Agent`：调用者构造好 `LLMClient`、`ToolRegistry`、（可选）`PermissionChecker` / `HookEngine` / `MemoryManager` 后，调一次 `async for event in agent.run(conversation)` 即可拿到 `AgentEvent` 异步流；Textual UI 只负责把事件 fan-out 到屏幕，剩下的工具分发、流式拼接、批次并发、Plan Mode reminder 注入、max_tokens 恢复、压缩通知全部由 Agent 在协程内串好。Plan Mode 通过 `PermissionMode.PLAN` 切换；plan 文件路径由 `Agent._get_plan_path` 进程内单例懒加载；团队任务工具由 `mewcode/tools/task_*.py` 提供并通过 `TeamManager` 注册。

## 3. 功能需求

- F1: `Agent.run(conversation)` 是 `async def ... -> AsyncIterator[AgentEvent]`（`mewcode/agent.py:397`）；调用方用 `async for` 消费事件，循环结束生成器自然终止。
- F2: 每轮迭代先调 `_consume_mailbox` 拉团队消息，再走 `apply_tool_result_budget`（Layer 1 持久化超长结果）与 `auto_compact`（Layer 2 触发压缩），压缩成功时回送 `CompactNotification` 并重注入环境上下文 / 长记忆。
- F3: 通过 `LLMClient.stream(conversation, system, tools)` 拉取 `StreamEvent`，由 `StreamCollector.consume`（`mewcode/agent.py:178`）转成 `StreamText` / `ThinkingText` / `ToolUseEvent`；`ThinkingComplete` 累积进 `LLMResponse.thinking_blocks`；`StreamEnd` 记录 `stop_reason` / `input_tokens` / `output_tokens`。
- F4: 工具调用按 `partition_tool_calls` 切分批次（`mewcode/agent.py:218`）；`is_concurrency_safe=True` 的相邻工具进入同一并发批，剩余工具单独成批；并发批用 `asyncio.gather` 跑，串行批逐个 `_execute_tool` 处理 HITL；本轮结束统一 `add_tool_results_message` 回灌。
- F5: 主循环终止条件：本轮无 `tool_calls` → 追加 assistant 消息并 `yield LoopComplete`；连续 3 次 `consecutive_unknown` → `yield ErrorEvent` 退出；`asyncio.CancelledError` → 协程被取消时自然终止；超过 `max_iterations`（默认 50）→ `yield ErrorEvent`。
- F6: 处理 `stop_reason == "max_tokens"`：首次升档调 `client.set_max_output_tokens(MAX_TOKENS_CEILING)`（64000）并把已生成文本作为 assistant 消息追加，再注入 resume 指令；后续最多 `MAX_OUTPUT_TOKENS_RECOVERIES`（3）次恢复轮；超出仍未完成则继续走主循环逻辑。每次升档 / 恢复都 `yield RetryEvent(reason=...)`。
- F7: 流式异常处理：底层 `LLMClient.stream` 抛错时由调用方协程冒泡（`asyncio.CancelledError` 直接退出）；压缩内部错误 `auto_compact` 返回 `str` 时由主循环 `yield ErrorEvent`；当前实现暂未引入独立的 `ContextTooLongError` / `RateLimitError` 重试分支（与 Go `handleStreamError` 的差异点）。
- F8: 权限交互：`_execute_tool`（`mewcode/agent.py:788`）调 `permission_checker.check`，`deny` → 返回错误结果；`ask` → `yield PermissionRequest`（带 `asyncio.Future`），UI 端 `set_result` 把 `PermissionResponse.ALLOW / DENY / ALLOW_ALWAYS` 回填；`ALLOW_ALWAYS` 时调 `rule_engine.append_local_rule` 写入 `{tool}(content*)` 规则。
- F9: 工具执行包夹 Hooks：执行前走 `hook_engine.run_pre_tool_hooks`（可阻断，返回拒绝即直接当错误结果回灌）；执行后走 `run_hooks("post_tool_use", ctx)`（不阻断）；`_infer_file_path` 从 `args["file_path"]` / `args["path"]` 提取代表性路径供 hook 匹配。
- F10: 工具集动态裁剪：`Agent.coordinator_mode` 字段使 `build_system_prompt` 切到 coordinator 版；`ToolRegistry.is_enabled` 在 `_execute_tool` / `partition_tool_calls` 两处过滤；`registry.get_deferred_tool_names()` 写入 system reminder 让模型按需 `ToolSearch` 加载。
- F11: Plan Mode 文件状态：`Agent._get_plan_path`（`mewcode/agent.py:334`）懒生成单例路径，用 24 词形容词 + 24 词名词 + `MMDD-HHMM` 时间戳拼出可读 slug，落到 `<work_dir>/.mewcode/plans/<slug>.md`；进入 Plan 模式每轮调 `build_plan_mode_reminder(plan_path, plan_exists, iteration)` 注入提醒。
- F12: 团队协作任务工具：`mewcode/tools/task_create.py` / `task_get.py` / `task_list.py` / `task_update.py` 实现 `TaskCreate` / `TaskGet` / `TaskList` / `TaskUpdate` 四个 Tool；持久化交给 `TeamManager.get_task_store()`，支持 `blocks` / `blocked_by` 依赖关系；与 Go 版本的 `internal/todo` 单进程任务不同，Python 版任务以「跨智能体共享任务板」为定位。

## 4. 非功能需求

- N1: 工具并发安全：`Tool.is_concurrency_safe` 字段决定能否进入同一并发批；`partition_tool_calls` 顺序扫描调用并把连续的安全工具聚为一批，写工具与命令工具单独成批，保证串行语义。
- N2: 事件流式产出：`run` 是异步生成器，事件随 `yield` 直接传给消费者，不引入显式队列；UI 端用 `async for` 即可背压式消费，无需手动配 buffer。
- N3: 工具结果回灌前由 `_maybe_persist_or_truncate`（`mewcode/agent.py:1105`）按 `SINGLE_RESULT_CHAR_LIMIT` 决定是否持久化到 session 目录并改成预览，剩余按 `MAX_OUTPUT_CHARS` 截断追加 `… (output truncated)`，防止单工具结果撑爆下一轮上下文。
- N4: 工具参数代表性路径：`_infer_file_path` 只取 `file_path` / `path` 两个 schema 字段（与 Go 的 `file_path → path → pattern → target` 顺序不同，Python 实现更精简，仅用于 hook 匹配）。
- N5: Plan slug 必须可读：`_ADJECTIVES` 24 词 + `_NOUNS` 24 词 + 时间戳，避免纯数字命名，便于人眼区分 `.mewcode/plans/` 下多个历史 plan。

## 5. 设计概要

- 核心数据结构:
  - `Agent`（`mewcode/agent.py:284`）：`client`/`registry`/`protocol`/`work_dir`/`max_iterations`/`permission_checker`/`permission_mode`/`context_window`/`session_dir`/`compact_breaker`/`instructions_content`/`memory_manager`/`hook_engine`/`active_skills`/`coordinator_mode`/`team_name`/`_team_manager`/`_plan_path_cache` 等字段。
  - `AgentEvent` 类型联合（`mewcode/agent.py:138-153`）：`StreamText` / `ThinkingText` / `RetryEvent` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `ErrorEvent` / `PermissionRequest` / `CompactNotification` / `HookEvent`，每个都是独立 `@dataclass`。
  - `PermissionResponse(Enum)`：`ALLOW` / `DENY` / `ALLOW_ALWAYS`（`mewcode/agent.py:125`）。
  - `StreamCollector` / `LLMResponse` / `ThinkingBlock`（`mewcode/agent.py:158-211`）：把底层 `StreamEvent` 折叠成一轮完整响应。
  - `ToolBatch` / `partition_tool_calls`（`mewcode/agent.py:213-234`）：把工具调用切成并发批 + 串行批。
  - `StreamingExecutor`（`mewcode/agent.py:247-280`）：保留并发任务编号排序后 gather 收集，目前 `run` 主路径主要走 `_execute_batch_parallel`，`StreamingExecutor` 给 SubAgent / Teams 复用。
- 主流程（一次迭代）:
  1. `iteration += 1`，超过 `max_iterations` 直接 `yield ErrorEvent` 退出；
  2. `_consume_mailbox` 拉团队邮箱消息；
  3. 走 Layer 1 / Layer 2 压缩，压缩后回送 `CompactNotification` 并重注入环境与长记忆；
  4. `plan_mode` 时通过 `build_plan_mode_reminder` 注入 reminder；
  5. 把 hook 拉出的 prompt 段拼到 `build_system_prompt`；
  6. `registry.get_all_schemas(protocol)` 取工具 schema；
  7. `client.stream(...)` 配合 `StreamCollector.consume` 把流式事件转 `AgentEvent`；
  8. 累计 token usage 并 `yield UsageEvent`；
  9. `stop_reason == "max_tokens"` 走升档 + 恢复轮；
  10. 无 `tool_calls` → 追加 assistant 消息、按周期触发记忆抽取、`yield LoopComplete` 退出；
  11. 有 `tool_calls` → 落 assistant 消息、按批次并发 / 串行执行、把 `ToolResultBlock` 收齐回灌、`yield TurnComplete`。
- 调用链:
  - 用户输入 → `MewcodeApp.send_user_message`（`mewcode/app.py:840`）→ `asyncio.create_task(_send_message)` → `agent.run` async for → 各 `isinstance(event, ...)` 分支渲染 Textual widget。
  - `/plan` → `mewcode/commands/handlers/plan.py:handle_plan` → `MewcodeApp.set_plan_mode(True)` → `agent.set_permission_mode(PermissionMode.PLAN)` → 下一轮注入 reminder。
  - `/do` → `mewcode/commands/handlers/do.py:handle_do` → `MewcodeApp.set_plan_mode(False)` → 恢复 `PermissionMode.DEFAULT`。
  - HITL → `_execute_tool` `yield PermissionRequest(future=...)` → UI `_handle_permission_request` 把用户选择 `future.set_result(...)` 回填。
- 与其他模块的交互:
  - 依赖 `mewcode.client`（LLMClient）、`mewcode.conversation`（`ConversationManager` / `ToolUseBlock` / `ToolResultBlock`）、`mewcode.context`（auto_compact / 预算）、`mewcode.permissions`、`mewcode.hooks`、`mewcode.prompts`（plan reminder / system prompt）、`mewcode.memory.auto_memory`、`mewcode.tools`。
  - 被 `mewcode/app.py`（Textual TUI）、`mewcode/agents/fork.py`（SubAgent fork）、`mewcode/teams/inprocess.py`（in-process teammate）调用。

## 6. Out of Scope

- 本章不实现 SubAgent / Fork（属 ch13）；`Agent.run` 只跑一个智能体，多智能体由 `mewcode/agents/fork.py` 单独承担。
- 本章不实现 Worktree 隔离（属 ch14）；Plan 文件直接落 `work_dir/.mewcode/plans`。
- Plan Mode 的 Reentry / Exit Reminder 文本目前仅有 `_PLAN_MODE_FULL_REMINDER` / `_PLAN_MODE_SPARSE_REMINDER` 两种；后续轮次的退出 / 重入提醒文本属未来增强。
- 团队共享任务 `TaskCreate/TaskGet/TaskList/TaskUpdate` 的依赖图渲染（`blocks` / `blocked_by`）不在本章 UI 范围内。
- 除 `max_tokens` 以外的其他 `stop_reason`（`pause_turn` / `refusal`）当前实现未单独分支。
- `ContextTooLongError` / `RateLimitError` 的独立重试路径暂未引入（与 Go 版差异点，留给后续 PR）。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch04: Agent Loop Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。本章为验收，所有任务已经在 `origin/python` 分支落地，逐项标注真实文件 / 类 / 行号。

## T1: 定义 AgentEvent 事件家族（dataclass union）

- 影响文件: `mewcode/agent.py:55-153`
- 依赖任务: 无
- 完成标准: `StreamText` / `ThinkingText` / `RetryEvent` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `ErrorEvent` / `CompactNotification` / `HookEvent` 共 11 个 `@dataclass`，加上 `PermissionResponse(Enum)` 三态（`ALLOW` / `DENY` / `ALLOW_ALWAYS`，agent.py:125）和 `PermissionRequest` dataclass（含 `asyncio.Future`）共 12 个事件类型；`AgentEvent = StreamText | ThinkingText | ...` 类型联合在 agent.py:138-153 定义。

## T2: 实现 Agent 类与构造器

- 影响文件: `mewcode/agent.py:284-327`
- 依赖任务: T1
- 完成标准: `Agent.__init__` 接受 `client` / `registry` / `protocol` / `work_dir=".";` / `max_iterations=50` / `permission_checker=None` / `context_window=200_000` / `instructions_content=""` / `memory_manager=None` / `hook_engine=None`；初始化时拉取 `permission_checker.mode` 同步 `permission_mode`、`ensure_session_dir(work_dir)` 准备会话目录、`CompactCircuitBreaker()` 注入压缩熔断、`agent_id = uuid.uuid4().hex[:12]`；附带 `coordinator_mode` / `team_name` / `_team_manager` 三字段挂在团队 / 协调器场景。

## T3: 实现 run 主循环（async generator）

- 影响文件: `mewcode/agent.py:397-716`
- 依赖任务: T1, T2
- 完成标准: `async def run(self, conversation) -> AsyncIterator[AgentEvent]`；进入前注入 environment context + long-term memory；`while True` 跑迭代；每轮先 `_consume_mailbox`，再 `apply_tool_result_budget` + `auto_compact`（CompactEvent → `yield CompactNotification`）；调 `build_system_prompt` 拼系统提示；Plan Mode 时调 `build_plan_mode_reminder` 注入；调 `client.stream` + `StreamCollector.consume` 把流式事件 `yield` 出去；累计 token 后 `yield UsageEvent`；`stop_reason == "max_tokens"` 走 `MAX_TOKENS_CEILING=64000` / `MAX_OUTPUT_TOKENS_RECOVERIES=3` 升档恢复（agent.py:49-50, 529-559）；无工具调用 → `yield LoopComplete` 退出；连续 3 次 unknown → `yield ErrorEvent` 退出；有工具调用 → 按 `partition_tool_calls` 切批执行，最后 `add_tool_results_message` + `yield TurnComplete`。

## T4: 实现 StreamCollector 与 LLMResponse

- 影响文件: `mewcode/agent.py:158-211`
- 依赖任务: T1
- 完成标准: `StreamCollector.consume(stream)` 为 `async generator`；遇 `TextDelta` 追加 `LLMResponse.text` 并 `yield StreamText`；遇 `ThinkingDelta` `yield ThinkingText`；遇 `ThinkingComplete` 累加 `ThinkingBlock(thinking, signature)`；遇 `ToolCallComplete` 累加 `LLMResponse.tool_calls` 并 `yield ToolUseEvent`；遇 `StreamEnd` 写入 `stop_reason` / `input_tokens` / `output_tokens`。

## T5: 实现 partition_tool_calls 工具批次切分

- 影响文件: `mewcode/agent.py:213-234`
- 依赖任务: T2
- 完成标准: `partition_tool_calls(tool_calls, registry) -> list[ToolBatch]`；逐个调用判断 `tool.is_concurrency_safe and registry.is_enabled(name)`；若为安全且上一批 `concurrent=True` 则归入同批，否则新开 `ToolBatch(concurrent=safe, calls=[tc])`；`test_partition_tool_calls`（`tests/test_agent.py`）覆盖 5 个调用→3 批的切分。

## T6: 实现 StreamingExecutor 并发收集器

- 影响文件: `mewcode/agent.py:247-280`
- 依赖任务: T2
- 完成标准: `StreamingExecutor.submit(coro)` 用 `asyncio.create_task` 起协程并按 `_order` 编号；`collect_results()` 按编号排序后 `asyncio.gather(..., return_exceptions=True)`，遇 `Exception` 包装成 `_ToolExecResult(is_error=True)` 不中断主流程；供 SubAgent / Teams 在流式阶段就启动工具时复用。

## T7: 实现 _execute_batch_parallel 并发批执行

- 影响文件: `mewcode/agent.py:782-786`
- 依赖任务: T5, T6
- 完成标准: `_execute_batch_parallel(calls)` 对每个 `ToolCallComplete` 调 `_execute_single_tool_direct`，再 `asyncio.gather` 并发；返回 `list[_ToolExecResult]`，主循环负责把每个结果做 `_maybe_persist_or_truncate` 后写入 `tool_results`，同时 `yield ToolResultEvent`。

## T8: 实现 _execute_tool 串行批 / HITL 路径

- 影响文件: `mewcode/agent.py:788-867`
- 依赖任务: T2, T6
- 完成标准: `_execute_tool(tc)` 为 `async generator`，依次处理 unknown tool / disabled / `permission_checker.check` 三态：`deny` → 错误结果；`ask` → `yield PermissionRequest(future=loop.create_future())` 等 UI 把 `future.set_result(...)` 回填；`ALLOW_ALWAYS` 时调 `rule_engine.append_local_rule(Rule(tool, pattern=content[:60]+"*", "allow"))` 持久化；`pydantic.ValidationError` 拿 `Parameter validation error` 结果；其他异常拿 `Tool execution error`；产出 `(ToolResult, elapsed, is_unknown)` 三元组。

## T9: 实现 Hook 前后包夹

- 影响文件: `mewcode/agent.py:371-395`、`mewcode/agent.py:603-685`
- 依赖任务: T8
- 完成标准: `_build_hook_context(event, **kwargs)` 拼 `HookContext`；`_infer_file_path(args)` 取 `file_path` 或 `path`；`_drain_hook_events()` 把 `HookEngine.drain_notifications()` 转 `HookEvent` `yield` 出去；主循环在 `session_start` / `turn_start` / `pre_send` / `post_receive` / `pre_tool_use`（可阻断，返回 `Hook rejected: {reason}` 错误结果）/ `post_tool_use` / `turn_end` / `session_end` 共 8 个事件点插入 hook 执行。

## T10: 实现 plan_path 单例与 Plan Mode reminder

- 影响文件: `mewcode/agent.py:329-355`、`mewcode/prompts.py:158-237`
- 依赖任务: 无
- 完成标准: `Agent._get_plan_path` 用 `random.choice(_ADJECTIVES) + "-" + random.choice(_NOUNS) + "-" + datetime.now().strftime("%m%d-%H%M")` 生成 slug，落到 `work_dir/.mewcode/plans/<slug>.md`，首次调用 `mkdir(parents=True, exist_ok=True)` 并缓存到 `_plan_path_cache`；`build_plan_mode_reminder(plan_path, plan_exists, iteration)`（prompts.py:203）在 `iteration==1` 给完整 reminder，按 `_REMINDER_INTERVAL=5` 周期再发完整版，间隔轮次发 sparse reminder；`Agent.set_permission_mode(mode)` 同时更新 `permission_checker.mode`。

## T11: 实现团队任务四工具

- 影响文件: `mewcode/tools/task_create.py`、`task_get.py`、`task_list.py`、`task_update.py`
- 依赖任务: 无
- 完成标准: 四个 Tool 类（`TaskCreateTool` / `TaskGetTool` / `TaskListTool` / `TaskUpdateTool`）皆继承 `Tool`，定义 `name` / `description` / `params_model` / `category` / `is_concurrency_safe=True`；构造函数注入 `team_manager: TeamManager` 与 `team_name`；`execute` 走 `team_manager.get_task_store(team_name)` 拿 `TaskStore` 后调 `create/get/list_tasks/update`；`TaskUpdate` 校验 `VALID_STATUSES = {"pending","in_progress","completed","blocked"}`；`TaskList` 输出按状态 icon `○◐●✕` 渲染。

## T12: 实现 _maybe_persist_or_truncate 工具结果整形

- 影响文件: `mewcode/agent.py:1105-1117`
- 依赖任务: T2
- 完成标准: 工具输出长度超 `SINGLE_RESULT_CHAR_LIMIT` 时调 `persist_tool_result` 落到 session 目录、返回 `make_persisted_preview`；超 `MAX_OUTPUT_CHARS` 时直接截断追加 `… (output truncated)`；其他情况原样返回。

## T13: 接入主流程（Textual TUI）

- 影响文件: `mewcode/app.py:649`（构造 `Agent`）、`mewcode/app.py:850-855`（`set_plan_mode`）、`mewcode/app.py:1085`（`async for event in agent.run`）、`mewcode/app.py:1099-1230`（事件分发）、`mewcode/commands/handlers/plan.py`、`mewcode/commands/handlers/do.py`
- 依赖任务: T1~T12
- 完成标准: 用户进入聊天后 `MewcodeApp` 构造 `Agent` 并装好 `permission_checker` / `memory_manager` / `hook_engine`；`send_user_message` 调 `asyncio.create_task(self._send_message(text))`；`_send_message` 用 `async for event in self.agent.run(self.conversation)` 消费事件，按 `isinstance` 分别渲染 `StreamText` / `ThinkingText` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `HookEvent` / `CompactNotification` / `ErrorEvent` / `PermissionRequest` / `RetryEvent`；`/plan` 命令切 `PermissionMode.PLAN`，`/do` 切 `PermissionMode.DEFAULT`。

## T14: 端到端验证

- 影响文件: 无（仅运行验证）
- 依赖任务: T13
- 完成标准:
  - `python -m compileall mewcode` 通过（语法 / 导入正确）。
  - `ruff check mewcode tests` 无 error。
  - `pytest tests/test_agent.py -q` 通过：覆盖 `test_single_step_tool_call`、`test_multi_step_autonomous`、`test_stop_end_turn`、`test_stop_max_iterations`、`test_stop_cancel`、`test_stop_consecutive_unknown_tools`、`test_message_splicing`、`test_concurrent_batch_execution`、`test_token_usage_accumulates`、`test_plan_mode`、`test_plan_mode_denied_tool_returns_error`、`test_partition_tool_calls`、`test_system_prompt_normal`、`test_system_prompt_plan`、`test_plan_mode_sparse_reminder`、`test_environment_context` 共 16 个测试用例（tests/test_agent.py）。
  - 在 Textual 界面输入 `hello` 看到 `StreamText` 流式渲染与 `LoopComplete` 终止；输入 `/plan` 看到 plan reminder 注入并禁止写工具。

## 进度

- [ ] T1 AgentEvent 11 dataclass + Enum + 联合类型
- [ ] T2 Agent.__init__
- [ ] T3 Agent.run 主循环
- [ ] T4 StreamCollector
- [ ] T5 partition_tool_calls
- [ ] T6 StreamingExecutor
- [ ] T7 _execute_batch_parallel
- [ ] T8 _execute_tool（HITL / 权限）
- [ ] T9 Hook 包夹
- [ ] T10 plan_path 单例 + build_plan_mode_reminder
- [ ] T11 TaskCreate/Get/List/Update 四工具
- [ ] T12 _maybe_persist_or_truncate
- [ ] T13 Textual TUI 接入
- [ ] T14 端到端验证（compileall + ruff + pytest + 手工 plan 模式）
```
```plain
# ch04: Agent Loop Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。

## 1. 实现完整性

- [ ] 类 `Agent` 在 `mewcode/agent.py:284`，字段含 `client` / `registry` / `protocol` / `work_dir` / `max_iterations` / `permission_checker` / `permission_mode` / `context_window` / `session_dir` / `compact_breaker` / `instructions_content` / `memory_manager` / `hook_engine` / `coordinator_mode` / `team_name` / `_plan_path_cache`（`grep -n "class Agent:" mewcode/agent.py`）
- [ ] 12 个 AgentEvent 类型 + `PermissionResponse(Enum)` 在 `mewcode/agent.py:55-153`：`StreamText` / `ThinkingText` / `RetryEvent` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `ErrorEvent` / `CompactNotification` / `HookEvent` / `PermissionRequest`（`grep -nE "^@dataclass|^class [A-Z]" mewcode/agent.py` 至少返回 12 条）
- [ ] 方法 `Agent.run` 在 `mewcode/agent.py:397` 实现，签名 `async def run(self, conversation) -> AsyncIterator[AgentEvent]`（`grep -n "async def run" mewcode/agent.py`）
- [ ] 常量 `MAX_TOKENS_CEILING=64000` 与 `MAX_OUTPUT_TOKENS_RECOVERIES=3` 在 `mewcode/agent.py:49-50`，`MEMORY_EXTRACTION_INTERVAL=5` 在 agent.py:48（`grep -nE "MAX_TOKENS_CEILING|MAX_OUTPUT_TOKENS_RECOVERIES|MEMORY_EXTRACTION_INTERVAL" mewcode/agent.py`）
- [ ] `StreamCollector.consume` 在 `mewcode/agent.py:178`，处理 `TextDelta` / `ThinkingDelta` / `ThinkingComplete` / `ToolCallComplete` / `StreamEnd` 五类事件（`grep -n "isinstance(event," mewcode/agent.py | head`）
- [ ] `partition_tool_calls` 在 `mewcode/agent.py:218`，`ToolBatch` 在 agent.py:213，安全调用合并到同一并发批的逻辑实现完整
- [ ] `StreamingExecutor.submit / collect_results` 在 `mewcode/agent.py:247-280`，使用 `asyncio.create_task` + `asyncio.gather(..., return_exceptions=True)`
- [ ] `_execute_tool` 在 `mewcode/agent.py:788`，处理 unknown tool / disabled / permission deny / permission ask（`PermissionRequest` 带 `asyncio.Future`）/ `ALLOW_ALWAYS` 写规则 5 个分支
- [ ] `_execute_batch_parallel` 在 `mewcode/agent.py:782`，`_execute_single_tool_direct` 在 agent.py:742
- [ ] `_maybe_persist_or_truncate` 在 `mewcode/agent.py:1105`，按 `SINGLE_RESULT_CHAR_LIMIT` / `MAX_OUTPUT_CHARS` 分支
- [ ] `Agent._get_plan_path` 在 `mewcode/agent.py:334`，使用 `_ADJECTIVES`(24) + `_NOUNS`(24) + `MMDD-HHMM` 拼 slug，`_plan_path_cache` 单例
- [ ] `build_plan_mode_reminder` 在 `mewcode/prompts.py:203`，`_REMINDER_INTERVAL=5`，`iteration==1` 给完整 reminder（`grep -n "_REMINDER_INTERVAL" mewcode/prompts.py`）
- [ ] 任务模型与四工具：`TaskCreateTool` / `TaskGetTool` / `TaskListTool` / `TaskUpdateTool` 在 `mewcode/tools/task_create.py`、`task_get.py`、`task_list.py`、`task_update.py`，皆继承 `Tool` 且 `is_concurrency_safe = True`
- [ ] 工具结果回灌：`_infer_file_path` 在 `mewcode/agent.py:381` 按 `file_path → path` 顺序查找

## 2. 接入完整性（杜绝死代码）

- [ ] `grep -n "Agent(" mewcode/app.py` 显示 `mewcode/app.py:649` 构造 Agent 时传入 `client` / `registry` / `protocol` / `work_dir` / `permission_checker` / `context_window` / `instructions_content` / `memory_manager` / `hook_engine`
- [ ] `grep -n "self.agent.run" mewcode/app.py` 至少 1 处（`mewcode/app.py:1085` 的 `async for event in self.agent.run(self.conversation)`）
- [ ] `grep -rn "build_plan_mode_reminder" mewcode/` 至少 2 处调用方：`mewcode/agent.py:475` 与 `tests/test_agent.py`
- [ ] `grep -rn "set_permission_mode\|set_plan_mode" mewcode/` 调用链：`mewcode/commands/handlers/plan.py` → `MewcodeApp.set_plan_mode`（`mewcode/app.py:850`）→ `agent.set_permission_mode(PermissionMode.PLAN)`（`mewcode/agent.py:352`）
- [ ] `grep -rn "TaskCreateTool\|TaskGetTool\|TaskListTool\|TaskUpdateTool" mewcode/` 四个工具在团队注册路径上被引用（团队场景由 `TeamManager` 注册到 Registry）
- [ ] `grep -n "permission_checker" mewcode/app.py` 在 TUI 构造 Agent 时使用（`mewcode/app.py:654`）
- [ ] `Agent.coordinator_mode` 在 TUI 协调器路径上设值，`build_system_prompt` 据此切到 coordinator 系统提示
- [ ] `Agent.hook_engine` 在 `mewcode/app.py:658` 注入 `HookEngine`，主循环 8 个 hook 事件点（session_start / turn_start / pre_send / post_receive / pre_tool_use / post_tool_use / turn_end / session_end）皆有触发
- [ ] `_handle_permission_request` 在 `mewcode/app.py` 监听 `PermissionRequest` 事件，把用户选择 `future.set_result(PermissionResponse.X)` 回填
- [ ] `RetryEvent` 在 `mewcode/app.py:1119` 渲染为 `↻ Retrying: ...` 系统消息

## 3. 编译与测试

- [ ] `python -m compileall mewcode` 通过，无语法 / 导入错误
- [ ] `ruff check mewcode tests` 无 error
- [ ] `pytest tests/test_agent.py -q` 16 个测试用例全部通过：
  - `test_single_step_tool_call`、`test_multi_step_autonomous`、`test_stop_end_turn`
  - `test_stop_max_iterations`、`test_stop_cancel`、`test_stop_consecutive_unknown_tools`
  - `test_message_splicing`、`test_concurrent_batch_execution`、`test_token_usage_accumulates`
  - `test_plan_mode`、`test_plan_mode_denied_tool_returns_error`
  - `test_partition_tool_calls`
  - `test_system_prompt_normal`、`test_system_prompt_plan`、`test_plan_mode_sparse_reminder`、`test_environment_context`

## 4. 端到端验证

- [ ] Textual 入口：用户在输入框敲普通消息后看到 `StreamText` 渲染、最终 `LoopComplete` 终止 —— 调用链 `MewcodeApp.send_user_message → asyncio.create_task(_send_message) → async for event in self.agent.run(self.conversation) → isinstance 分支`（`mewcode/app.py:840 → :1085 → :1099-1230`）
- [ ] Plan Mode：输入 `/plan` 走 `handle_plan` → `set_plan_mode(True)` → `agent.set_permission_mode(PermissionMode.PLAN)`，下一轮看到 plan reminder 注入；输入 `/do` 走 `handle_do` → 恢复 `PermissionMode.DEFAULT`（`mewcode/commands/handlers/plan.py` / `do.py`）
- [ ] HITL 权限：`PermissionRequest` 事件触发时 Textual 渲染权限对话框（`mewcode/permission_dialog.py`），用户选「允许 / 拒绝 / 允许始终」对应 `PermissionResponse.ALLOW` / `DENY` / `ALLOW_ALWAYS`；选 `ALLOW_ALWAYS` 时调 `rule_engine.append_local_rule` 持久化（`mewcode/agent.py:846-851`）
- [ ] max_tokens 升档：模拟 `stop_reason="max_tokens"` 看到 `RetryEvent(reason="max_tokens escalation")` 与 `client.set_max_output_tokens(64000)`；连续 3 次后停止恢复进入下一轮主流程（`mewcode/agent.py:529-559`）
- [ ] 留存证据：验收阶段无截图；如需补，可在 Textual 中输入 `hi` 拍照保存 stream 渲染

## 5. 文档

- [ ] spec.md / tasks.md / checklist.md 三件套齐全（`docs/python/ch04/`）
- [ ] commit 信息标注 `ch04` 与三件套关闭状态（待统一打包提交）
```

### Java

```plain
# ch04: Agent Loop Spec

## 1. 背景

ch02 把 LLM 客户端跑通了：一次 `stream()` 调用从模型拿到一段文本或一组 tool_use。ch03 把工具注册表与六个核心工具搭好了。但「一次调用」和「一个 Agent」之间还差一个关键环节：让模型自主地反复思考 → 调工具 → 看结果 → 再思考，直到任务真正完成。没有 Agent Loop，MewCode 还只是个能调一次工具的聊天机器人。本章把这条循环管线做出来：一个虚拟线程驱动的 while 循环，消费 `BlockingQueue<StreamEvent>` 流式事件，分类执行工具调用（只读并行 / 写串行），把结果回写 `ConversationManager`，再以 `AgentEvent` 形式向 TUI 推送进度。

## 2. 目标

对外提供 `com.mewcode.agent.Agent`：调用者准备好 `LlmClient` / `ToolRegistry` / `protocol`，调一次 `agent.run(conversation)` 拿到 `BlockingQueue<AgentEvent>`，从中 poll 出文本流、思考流、工具调用、工具结果、用量、错误、轮次完成、循环完成等事件并直接渲染到 TUI。循环内部完成：消费上游 stream → 收集 tool_use → `StreamingExecutor` 分流并发执行 → 回写会话 → 进入下一轮；同时承担 deferred tool 提醒注入、Plan Mode 提醒注入、自动 compact、max_tokens 恢复、context 超限重试、rate-limit 退避等运维职责。

## 3. 功能需求

- F1: 提供 `Agent` 类，构造接收 `LlmClient` / `ToolRegistry` / `protocol`；支持通过 setter 注入 `PermissionChecker` / `HookEngine` / `maxIterations` / `workDir` / 通知 supplier / tool name filter。
- F2: `Agent.run(ConversationManager)` 返回 `BlockingQueue<AgentEvent>`，内部用 `Thread.startVirtualThread` 启动 agent loop，确保 TUI 主线程不阻塞；异常一律包成 `AgentEvent.ErrorEvent` 入队。
- F3: 提供 `AgentEvent` sealed interface，覆盖文本流 / 思考流 / 思考完成 / 工具使用 / 工具结果 / 轮次完成 / 循环完成 / 用量 / 错误 / 压缩 / 重试 / 权限请求 / askuser 共 13 种事件 record。
- F4: 主循环按轮迭代：先 drain 通知 supplier 注入 system-reminder，跑 `ContextCompactor.manage`，把 deferred tool 名字以 system-reminder 注入；Plan Mode 下再注入 `PlanModePrompt.buildReminder`。
- F5: 每轮调 `client.stream(conv, tools)` 拿到 `BlockingQueue<StreamEvent>`，用 30 秒 poll 超时消费，把 TextDelta / ThinkingDelta / ThinkingComplete / ToolCallStart / ToolCallComplete / StreamEnd / Error 七类事件转译成 `AgentEvent` 推送给消费者；同时收集 tool_use 列表、用量、stop_reason。
- F6: 工具执行委托给 `StreamingExecutor.executeAll`：按 `ToolCategory.READ` 把 calls 拆成 readCalls / otherCalls 两段，readCalls 数量 >1 时用 `Executors.newVirtualThreadPerTaskExecutor()` 并发跑，其它串行；权限走 `PermissionChecker.check` 决策 ALLOW/ASK/DENY，ASK 通过 `PermissionRequestEvent` 把 `CompletableFuture<PermissionResponse>` 抛给 TUI 等用户回填；执行前后跑 PreToolUse / PostToolUse hook。
- F7: 工具执行完成后调 `conv.addAssistantFull(text, thinking, toolUses)` 写回助手消息，再调 `conv.addToolResultsMessage(results)` 写回工具结果消息；本轮无 tool_use 则推 `TurnComplete` + `LoopComplete` 退出循环。
- F8: 错误恢复：stream Error 含 `context` / `too long` / `prompt` 关键字时调 `ContextCompactor.forceCompact` 并 retry，最多 3 次；含 `rate limit` 时退避 5 秒重试；`max_tokens` stop_reason 首次提升上限到 `MAX_TOKENS_CEILING=64_000` 并续写，最多 `MAX_OUTPUT_RECOVERIES=3` 次拆分续写。
- F9: 工具输出超过 `ToolRegistry.MAX_OUTPUT_CHARS=10_000` 强制截断并追加 `... (truncated)` 标记，保证 tool_result 不撑爆下一轮上下文。

## 4. 非功能需求

- N1: Agent loop 必须跑在虚拟线程上（`Thread.startVirtualThread`），主 TUI 线程靠 `BlockingQueue` poll 实现非阻塞渲染；`Thread.currentThread().isInterrupted()` 命中即退出循环。
- N2: 工具调用分流策略必须严格保证：只读工具可并行（虚拟线程池），写 / 命令类工具一律串行执行，避免相互踩文件。
- N3: stream 消费 poll 超时统一 30 秒，超时直接推 `Stream timeout` 错误并 return，不允许卡住整条循环。
- N4: `AgentEvent` 队列容量 64，`putSafe` 在 InterruptedException 时回写中断标志而不是抛异常，保障 TUI 关停时能干净退出。
- N5: 权限询问的 `CompletableFuture.get` 设 5 分钟超时，超时按 DENY 处理，避免 Agent 永远悬挂。

## 5. 设计概要

- 核心数据结构: `AgentEvent`（sealed interface，13 个 record 实现）、`StreamingExecutor.ToolCallInfo{toolId, toolName, args}` / `ToolExecResult{toolId, output, isError}`、内部 `Agent.ToolCallInfo`（轮内汇聚 tool_use）。
- 主流程:
 1. TUI 选 provider → 构造 `LlmClient` → 构造 `Agent(client, registry, protocol)` → 注入 checker / hook / workDir 等；
 2. 用户输入 → TUI `agent.run(conv)` 拿 queue → 启动 `Command.tick` 轮询；
 3. 每个 `AgentEventMessage` tick 在 model.update 中 drain queue → 转换成 `ChatMessage` 渲染；
 4. 收到 `LoopComplete` / `ErrorEvent` 结束本次会话，恢复 idle。
- 调用链:
 - TUI 用户提问 → `MewCodeModel` 调 `agent.run` → agent virtual thread 开转；
 - 每轮: notification drain → compact → deferred reminder → plan reminder → `client.stream` → 消费 StreamEvent → 收集 toolCalls → `StreamingExecutor.executeAll` → `conv.addAssistantFull` + `addToolResultsMessage`；
 - 工具内含权限决策 → ASK 走 `PermissionRequestEvent` → TUI 弹 dialog → CompletableFuture.complete → executor 继续。
- 与其他模块的交互:
 - 依赖 ch02 的 `LlmClient` / `StreamEvent` / `ConversationManager`、ch03 的 `ToolRegistry` / `Tool` / `ToolCategory` / `ToolResult`、ch06 的 `PermissionChecker` / `PermissionMode` / `PlanFile` / `PlanModePrompt`、ch08 的 `ContextCompactor`、ch12 的 `HookEngine`；
 - 被 `MewCodeModel` 直接调用，输出事件队列由 TUI 渲染。

## 6. Out of Scope

- 不在本章实现 `ContextCompactor` 内部算法（ch08 主题）。
- 不实现 Plan Mode reminder 文案（ch06 主题）。
- 不实现 SubAgent 派遣（ch13 主题）。
- 不实现 hook 引擎本体（ch12 主题）。
- 不做 system prompt 模块化拼装；本章 system prompt 由 `LlmClient.create` 接收的字符串透传，模块化拼装留给后续章节。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch04: Agent Loop Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。本章为验收，所有任务已经在仓库里落地。

## T1: 定义 AgentEvent sealed interface
- 影响文件: `src/main/java/com/mewcode/agent/AgentEvent.java:1-39`
- 依赖任务: 无
- 完成标准: `public sealed interface AgentEvent` 包含 13 个 record 实现：`StreamText` / `ThinkingText` / `ThinkingComplete` / `ToolUseEvent` / `ToolResultEvent` / `TurnComplete` / `LoopComplete` / `UsageEvent` / `ErrorEvent` / `CompactEvent` / `RetryEvent` / `PermissionRequestEvent` / `AskUserRequestEvent`；`PermissionRequestEvent` 字段含 `CompletableFuture<PermissionResponse>`（AgentEvent.java:33-34）；`AskUserRequestEvent` 字段含 `CompletableFuture<Map<String, String>>`（AgentEvent.java:36-38）。

## T2: 定义 Agent 类骨架与依赖注入
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:19-48`
- 依赖任务: T1
- 完成标准: 构造方法接 `(LlmClient client, ToolRegistry registry, String protocol)`（Agent.java:35）；`MAX_TOKENS_CEILING=64_000`（Agent.java:21）、`MAX_OUTPUT_RECOVERIES=3`（Agent.java:22）；setter 注入 `PermissionChecker` / `HookEngine` / `maxIterations` / `workDir` / `notificationFn` / `toolNameFilter`（Agent.java:42-47）。

## T3: 实现 run 入口与虚拟线程派发
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:50-60`
- 依赖任务: T2
- 完成标准: `public BlockingQueue<AgentEvent> run(ConversationManager conv)` 返回 `LinkedBlockingQueue<>(64)`；`Thread.startVirtualThread` 启 `agentLoop`，所有 Exception 包成 `AgentEvent.ErrorEvent("Agent error: ...")`（Agent.java:51-58）。

## T4: 实现轮次起手：通知 / compact / deferred / plan 注入
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:62-114`
- 依赖任务: T3
- 完成标准:
 - 主循环 `for (int iteration = 1; ; iteration++)`（Agent.java:69）；
 - `maxIterations` 超限推 `ErrorEvent("Agent reached maximum iterations (%d)")` 退出（Agent.java:70-74）；
 - `Thread.currentThread().isInterrupted()` 命中 break（Agent.java:76）；
 - `notificationFn.get()` drain 后 `conv.addSystemReminder(note)`（Agent.java:79-83）；
 - `ContextCompactor.manage` 非空消息推 `CompactEvent`（Agent.java:87-91）；
 - `registry.getDeferredToolNames()` 非空时拼 reminder 注入（Agent.java:94-104）；
 - Plan Mode 下 `PlanModePrompt.buildReminder` 注入（Agent.java:107-114）。

## T5: 实现 StreamEvent 流消费
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:116-182`
- 依赖任务: T4
- 完成标准:
 - tool list 走 `registry.getAllSchemas(protocol)`，可选 `toolNameFilter` 过滤（Agent.java:117-125）；
 - `client.stream(conv, tools)` 拿 `BlockingQueue<StreamEvent>`（Agent.java:126）；
 - `streamQueue.poll(30, TimeUnit.SECONDS)` 超时推 `Stream timeout` 错误（Agent.java:139, 145-148）；
 - switch pattern matching 七路：`TextDelta` → `StreamText`；`ThinkingDelta` → `ThinkingText`；`ThinkingComplete` 入 `thinkingBlocks` + 转发；`ToolCallStart` / `ToolCallComplete` 转发并把后者入 `toolCalls`；`StreamEnd` 抓 stop_reason 与 token 用量；`Error` 抓 `lastStreamError` 推 `ErrorEvent`（Agent.java:150-179）；
 - `StreamEnd` / `Error` 命中跳出消费循环（Agent.java:181）。

## T6: 实现错误恢复（context / rate-limit / max_tokens）
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:184-233`
- 依赖任务: T5
- 完成标准:
 - stream 错误 + 错误文本含 `context` / `too long` / `prompt` → `contextRetries < 3` 时 `ContextCompactor.forceCompact` 后 `RetryEvent("Context too long, compacting...", 0)` continue（Agent.java:186-196）；
 - 错误文本含 `rate limit` → 推 `RetryEvent("Rate limited, waiting 5s...", 5000)`，`Thread.sleep(5000)` 后 continue（Agent.java:197-201）；
 - stop_reason `max_tokens` 首次：`AnthropicClient.setMaxOutputTokens(MAX_TOKENS_CEILING)` + 写助手已生成内容 + user "Output token limit hit. Resume directly from where you stopped..." + `RetryEvent("max_tokens escalation", 0)` continue（Agent.java:210-221）；
 - `maxTokensEscalated` 后再次命中：`outputRecoveries < MAX_OUTPUT_RECOVERIES` 时写助手 + user "Break remaining work into smaller pieces." + 计数器自增 continue（Agent.java:222-229）。

## T7: 实现工具调用收尾与会话写回
- 影响文件: `src/main/java/com/mewcode/agent/Agent.java:235-263`
- 依赖任务: T5
- 完成标准:
 - `conv.addAssistantFull(text, thinkingBlocks, toolUseBlocks)` 写回助手（Agent.java:236-239）；
 - 无 tool_call → 推 `TurnComplete(iteration)` + `LoopComplete(iteration)` 后 break（Agent.java:242-246）；
 - 有 tool_call → `new StreamingExecutor(...).executeAll(callInfos)` 拿结果（Agent.java:249-253）；
 - `conv.addToolResultsMessage(resultBlocks)` 写回（Agent.java:256-259）；
 - 末尾推 `TurnComplete(iteration)`（Agent.java:261）。

## T8: 实现 StreamingExecutor 分流并发
- 影响文件: `src/main/java/com/mewcode/agent/StreamingExecutor.java:23-72`
- 依赖任务: T1
- 完成标准:
 - 按 `ToolCategory.READ` 拆 `readCalls` / `otherCalls`（StreamingExecutor.java:42-51）；
 - readCalls `> 1` 时 `Executors.newVirtualThreadPerTaskExecutor()` 并发跑 `executeSingle` 收集 future（StreamingExecutor.java:55-64）；
 - readCalls `<= 1` 串行（StreamingExecutor.java:65-67）；
 - otherCalls 全部串行（StreamingExecutor.java:69）。

## T9: 实现 StreamingExecutor 单次执行（hook / 权限 / 截断）
- 影响文件: `src/main/java/com/mewcode/agent/StreamingExecutor.java:74-149`
- 依赖任务: T8
- 完成标准:
 - 未知工具直接 `Unknown tool` 错误（StreamingExecutor.java:75-79）；
 - PreToolUse hook rejected 时 `Rejected by hook: ...` 错误（StreamingExecutor.java:82-89）；
 - 权限决策三分支：DENY 直接 `Permission denied: ...`；ASK 推 `PermissionRequestEvent` + `future.get(5, MINUTES)`，超时按 DENY；`ALLOW_ALWAYS` 调 `checker.addAllowAlwaysRule(toolName, extractContent(...))`（StreamingExecutor.java:91-122）；
 - `tool.execute(args)` 计 elapsed 秒 + 输出超 `MAX_OUTPUT_CHARS=10_000` 截断追加 `... (truncated)`（StreamingExecutor.java:125-137）；
 - 推 `ToolResultEvent(toolId, toolName, output, isError, elapsed)` + 跑 PostToolUse hook（StreamingExecutor.java:139-145）。

## T10: 接入主流程（TUI / MewCodeModel）
- 影响文件:
 - `src/main/java/com/mewcode/tui/MewCodeModel.java:432-438` 构造 `new Agent(client, registry, protocol)` + 注入依赖
 - `src/main/java/com/mewcode/tui/MewCodeModel.java:952` / `:1028` 调 `agent.run(conversation)` 拿 queue
 - `src/main/java/com/mewcode/MewCode.java:14` `main` 启动 `Program(model).run()` 跑 TUI
- 依赖任务: T1~T9
- 完成标准: TUI 收到用户输入 → `agent.run` → `Command.tick(POLL_INTERVAL, ...)` 周期 drain queue → 把 `AgentEvent` 映射成 `ChatMessage` 渲染。

## T11: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T10
- 完成标准:
 - `./gradlew build` 通过；
 - `./gradlew test` 通过（现有测试集 `src/test/java/com/mewcode/teams/FileMailBoxTest.java` / `src/test/java/com/mewcode/tool/ToolSearchTest.java`，无 Agent 直接单测，本章靠手动 TUI 演练验收）；
 - TUI 启动 → 提问 `读一下 README.md` → 队列中能依序观察到 `StreamText` / `ToolUseEvent(ReadFile)` / `ToolResultEvent` / `TurnComplete` / `LoopComplete`。

## 进度
- [ ] T1 AgentEvent sealed interface
- [ ] T2 Agent 骨架 + DI
- [ ] T3 run 入口 + 虚拟线程
- [ ] T4 轮次起手注入
- [ ] T5 StreamEvent 消费
- [ ] T6 错误恢复
- [ ] T7 工具调用收尾
- [ ] T8 StreamingExecutor 分流
- [ ] T9 StreamingExecutor 单次执行
- [ ] T10 TUI 接入
- [ ] T11 端到端验证
```
```plain
# ch04: Agent Loop Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。

## 1. 实现完整性
- [ ] `AgentEvent` sealed interface 在 `src/main/java/com/mewcode/agent/AgentEvent.java:8`，13 个 record 实现齐全（`grep -nE "record [A-Z][A-Za-z]+\(" src/main/java/com/mewcode/agent/AgentEvent.java` 返回 13 条）
- [ ] `AgentEvent.PermissionRequestEvent` 在 AgentEvent.java:33-34 含 `CompletableFuture<PermissionResponse>` 字段
- [ ] `Agent` 类在 `src/main/java/com/mewcode/agent/Agent.java:19`，常量 `MAX_TOKENS_CEILING=64_000`（Agent.java:21）、`MAX_OUTPUT_RECOVERIES=3`（Agent.java:22）
- [ ] `Agent.run` 在 Agent.java:50 返回 `LinkedBlockingQueue<>(64)`，`Thread.startVirtualThread` 在 Agent.java:52
- [ ] `Agent.agentLoop` 在 Agent.java:62，主循环 `for (int iteration = 1; ; iteration++)` 在 Agent.java:69
- [ ] 通知 drain + `conv.addSystemReminder` 在 Agent.java:79-83
- [ ] `ContextCompactor.manage` 调用在 Agent.java:87，`CompactEvent` 推送在 Agent.java:89
- [ ] deferred tool reminder 注入在 Agent.java:94-104，调 `registry.getDeferredToolNames()`
- [ ] Plan Mode reminder 注入在 Agent.java:107-114，调 `PlanModePrompt.buildReminder`
- [ ] `client.stream(conv, tools)` 调用在 Agent.java:126，`streamQueue.poll(30, SECONDS)` 在 Agent.java:139
- [ ] StreamEvent 七路 switch pattern matching 在 Agent.java:150-179，覆盖 `TextDelta` / `ThinkingDelta` / `ThinkingComplete` / `ToolCallStart` / `ToolCallDelta` / `ToolCallComplete` / `StreamEnd` / `Error`
- [ ] 错误恢复三分支：context 在 Agent.java:186-196，rate limit 在 Agent.java:197-201，max_tokens 在 Agent.java:210-229
- [ ] `conv.addAssistantFull` 在 Agent.java:239，`conv.addToolResultsMessage` 在 Agent.java:259
- [ ] 无 tool_use 收尾：`TurnComplete` + `LoopComplete` 在 Agent.java:243-245
- [ ] `StreamingExecutor` 在 `src/main/java/com/mewcode/agent/StreamingExecutor.java:23`
- [ ] 读 / 写分流在 StreamingExecutor.java:42-51，虚拟线程并发在 StreamingExecutor.java:55-64（`Executors.newVirtualThreadPerTaskExecutor()`）
- [ ] 权限 ASK 分支用 `CompletableFuture<PermissionResponse>` + 5 分钟超时在 StreamingExecutor.java:99-108
- [ ] 工具输出截断 `MAX_OUTPUT_CHARS=10_000` 在 StreamingExecutor.java:135-137（`ToolRegistry.MAX_OUTPUT_CHARS` 定义在 `src/main/java/com/mewcode/tool/ToolRegistry.java:7`）

## 2. 接入完整性（必查，杜绝死代码）
- [ ] `grep -rn "new Agent(" --include="*.java" src/main/java` 返回 ≥ 1 处真实调用（`src/main/java/com/mewcode/tui/MewCodeModel.java:432`）
- [ ] `grep -rn "agent.run(" --include="*.java" src/main/java` 返回 ≥ 2 处（`MewCodeModel.java:952`、`MewCodeModel.java:1028`）
- [ ] `grep -rn "new StreamingExecutor" --include="*.java" src/main/java` 返回 ≥ 1 处（`Agent.java:249`）
- [ ] `grep -rn "BlockingQueue<AgentEvent>" --include="*.java" src/main/java` 返回 ≥ 3 处（Agent.run、StreamingExecutor 构造、MewCodeModel 接收）
- [ ] TUI 调用链：用户提问 → `MewCodeModel.update` 收到 `UserInputMsg` → `agent.run(conversation)`（MewCodeModel.java:952/1028）→ `Command.tick(POLL_INTERVAL, t -> new AgentEventMessage())` 周期 drain queue
- [ ] Agent 调用链：每轮 → 通知注入（Agent.java:79）→ compact（:87）→ deferred reminder（:94）→ plan reminder（:107）→ `client.stream`（:126）→ `StreamingExecutor.executeAll`（Agent.java:253 / StreamingExecutor.java:41）→ 写回会话（:239/:259）

## 3. 编译与测试
- [ ] `./gradlew build` 通过（顶层命令验证）
- [ ] `./gradlew test` 通过（现有测试集仅 `FileMailBoxTest` / `ToolSearchTest`，无 Agent 直接单测，靠 TUI 端到端验收）
- [ ] `./gradlew compileJava` 无 unchecked / preview 警告（pattern matching for switch 在 Java 21+ 已 GA）

## 4. 端到端验证
- [ ] TUI 启动 → 选 provider → 提问 `读一下 README.md` → 队列中依序观察到 `StreamText` / `ToolUseEvent(toolName="ReadFile")` / `ToolResultEvent(isError=false)` / `TurnComplete` / `LoopComplete`
- [ ] 多读连发：提问 `同时读 README.md 和 build.gradle.kts`，观察 `StreamingExecutor` 走并发分支（两个 `ReadFile` ToolResultEvent 几乎同时到达，elapsed 接近）
- [ ] 权限 ASK 流程：在 ACCEPT_EDITS 模式下让 Agent 跑 `Bash`，观察 `PermissionRequestEvent` 弹 dialog → 用户 ALLOW → 工具继续执行
- [ ] max_tokens 恢复：构造长输出任务，观察 `RetryEvent("max_tokens escalation", 0)` 后助手续写到完整答案
- [ ] context 超限恢复：手工塞超长对话历史触发 `Error("context too long")` → `RetryEvent("Context too long, compacting...", 0)` → `ContextCompactor.forceCompact` 后继续
- [ ] 留存证据：验收阶段未保存日志；若要补，可在 TUI 输入指定提问后保存 `AgentEvent` 队列 trace

## 5. 文档
- [ ] spec.md / tasks.md / checklist.md 三件套齐全（`docs/java/ch04/`）
- [ ] commit 信息标注 `ch04` 与三件套关闭状态（待统一打包提交）
```