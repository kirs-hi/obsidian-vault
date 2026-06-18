# 第12章：实战篇

## 本章需要做什么

上一章我们给 MewCode 装上了 Skill 技能包系统，让 Agent 能通过 Slash Command 加载预定义的提示词和工具集合。但每次 Agent 写完文件你还是要手动跑格式化，每次看到危险命令你还是得自己盯着审批弹窗，每次开始新对话你还是要手动说「先读一下 ARCHITECTURE.md」。

这些事情触发条件明确、执行动作固定，完全不需要你来做。这一章要给 MewCode 装上 Hook 系统，让你在 Agent 的生命周期事件上挂载自动化动作。做完之后，格式化、拦截、上下文注入全部自动化，你不用再当人肉 CI。

具体要新增这些东西：

-   **事件常量** ：15 个生命周期事件（session\_ start/session\_ end、turn\_ start/turn\_ end、pre\_ tool\_ use/post\_ tool\_ use、pre\_ send/post\_ receive、startup/shutdown/error/compact/permission\_ request/file\_ change/command\_ execute）
-   **核心数据结构** ：Hook、Action、HookContext、ConditionGroup、Condition、ToolRejectedError
-   **条件表达式** ：解析与求值，支持 ==/!=/=~/ ~= 四种操作符，&&/|| 组合（不可混用）
-   **四种执行器** ：command（shell 命令）、prompt（注入提示词）、http（HTTP 请求）、agent（子 Agent，先占位）
-   **上下文变量替换** ：$EVENT、$TOOL\_ NAME、$FILE\_ PATH、$MESSAGE、$ERROR、$TOOL\_ ARGS.xxx
-   **执行控制** ：once（只执行一次）、async（后台执行）、command 的 timeout 超时
-   **拦截机制** ：pre\_ tool\_ use + reject 返回 ToolRejectedError，LLM 看到拒绝原因后调整策略
-   **HookEngine 核心** ：runHooks（非拦截事件）+ runPreToolHooks（pre\_ tool\_ use 专用）
-   **Agent Loop 集成** ：在会话、轮次、消息、工具的生命周期节点插入 Hook 调用
-   **配置加载与校验** ：从 YAML 加载，校验事件名、action 类型、reject/async 约束、必填字段

这章 **不做** ：once 标记的持久化（只做运行时标记，重启即重置）、Hook 执行顺序的显式优先级字段、agent 执行器的真实实现（留给后续的 SubAgent 章节）。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 用「事件 + 条件 + 动作」三要素描述一条规则；条件可省略表示无条件触发，事件和动作必须有
- 生命周期事件覆盖四个层级：会话级（会话起止）、轮次级（轮次起止）、消息级（发送前/接收后）、工具级（执行前/执行后），再加少量系统级事件（启动、退出、错误、压缩等）
- 工具执行前的事件具有拦截能力，可以基于工具参数内容做细粒度安全策略，被拦截后把拒绝原因作为工具结果反馈给 LLM，形成「拦截 → Agent 收到原因 → Agent 调整策略」的循环
- 条件表达式复用权限规则的匹配语法，支持精确、反向、正则、glob 四种操作符，逻辑组合用「全部满足」或「任一满足」二选一，不允许混用（避免引入运算符优先级和完整表达式引擎）
- 四种动作执行器：执行 shell 命令、注入提示词消息、发起 HTTP 请求、启动子 Agent（子 Agent 这种先占位）
- 执行控制三件套：只执行一次、后台异步执行、命令超时；并强制工具拦截类事件不允许异步
- 动作模板里支持上下文变量占位（事件名、工具名、文件路径、消息内容、错误信息、工具参数字段），未定义变量替换为空串而不是报错
- 辅助机制错误隔离原则：Hook 自身执行失败只记日志，绝不中断 Agent 主流程
- 从 YAML 声明式加载规则，加载时集中校验事件名、动作类型、拦截字段只能用在执行前事件、异步标记不能用在拦截事件、各动作类型必填字段，非法配置要能定位到具体规则
- 引擎需要嵌入 Agent Loop 的关键节点：会话起止、轮次起止、消息发送前/接收后、工具执行前（同步、可拦截）、工具执行后
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了，然后让 Claude Code 根据这三份文档进行开发

![](实战演练_动手实现_Hook_系统-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现_Hook_系统-2.jpeg)

### 功能验证过程

来验收一下结果

写一个测试用的 `hooks` 配置

```plain
# Hooks
hooks:

  # pre_tool_use 拦截写 *.json（reject + on_error 兜底）
  # 注意：LLM 给的 file_path 通常是绝对路径，glob 的 * 不跨 / 分隔符，
  # 所以这里用正则按后缀匹配（=~ /\.json$/）而不是 =* "*.json"
  - id: block-json-write
    event: pre_tool_use
    if: 'tool == "WriteFile" && args.file_path =~ /\.json$/'
    action:
      type: command
      command: 'echo "禁止直接写入 JSON 文件，请使用专用工具"'
    reject: true
```

然后我们打开MewCode，去试试这个hooks，我们输入

帮我创建 config.json，内容是 {}

![](实战演练_动手实现_Hook_系统-3.jpeg)

Agent 调用 WriteFille工具时会被 hook 拦截，收到"禁止写入Json文件"的错误，工具不会真正执行，然后Agent 会根据拒绝原因调整策略，用更合法的方式达到目的

现在对于我们单体的Agent来说，其实已经比较完整成体系了，但是不知道有没有感觉到，有的时候我们的MewCode任务一多，一件件处理会处理得好慢，好像我们得给它找点帮手，比如是不是搞多几个Agent。

下一章，我们就来讲讲怎么实现 SubAgent 和任务编排。

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

提示词如果需要复制，移步到这里： [【飞书文档】提示词复制](https://icnaxnmh86kx.feishu.cn/wiki/TC85wYUidiRGlFkkkg7cM05jnSR?fromScene=spaceOverview)

### Go

```plain
# ch12: Hook 系统 Spec

## 1. 背景

Agent 主流程在工具调用前后、session 起止、turn 起止等关键节点都有「副作用钩子」的需求：工具调用前阻断危险命令、调用后推日志到外部系统、用户提交前注入额外提示词、后台异步触发通知 / 监控。把这些写死在 agent 循环里既不优雅又难配置。Hook 系统把这层做成可声明（yaml）+ 条件匹配 + 多种动作类型的引擎，并保留 once / async / on_error 三种执行控制。

## 2. 目标

交付 `hooks.Engine`，从 `config.yaml` 加载 hook 数组，按事件名提供两种入口：普通事件用 `RunHooks` 跑全部命中钩子；`pre_tool_use` 用 `RunPreToolHooks` 允许阻断工具调用。Condition 支持 leaf 操作符（等 / 不等 / 正则 / glob）+ 复合（与 / 或）+ 反向（前缀 !）三类组合，变量覆盖 tool / event / file_path / message / args。Agent loop 在每次工具调用前后接入对应入口，TUI 负责从配置初始化引擎并挂到 Agent。

## 3. 功能需求

- F1: 提供 9 个事件类型常量（session_start / session_end / turn_start / turn_end / pre_send / post_receive / pre_tool_use / post_tool_use / shutdown），覆盖会话与工具生命周期。
- F2: 提供 4 个动作类型常量（command / script / prompt / http），其中 command 与 script 共享同一执行路径。agent 类型不在本章范围（见 Out of Scope）。
- F3: Condition DSL：
 - leaf 操作符：等于、不等于、正则匹配、glob 匹配
 - 复合：与、或，左结合且同优先级
 - 反向：前缀 !，仅作用于单个 leaf
 - 变量：tool、event、file_path、message、`args.<key>`
- F4: `RunHooks(ctx)` 按事件名过滤、按 condition 决定是否触发；async hook 立即返回占位结果，不阻塞。
- F5: `RunPreToolHooks(ctx)` 专门跑 `pre_tool_use` 事件：任何 reject 命中即返回阻断信号与原因；命令执行失败且 `OnError == "reject"` 时按 reject 处理。
- F6: 动作执行器:
 - command / script：bash 调外部命令，注入事件 / 工具 / 文件路径环境变量，stderr 拼到 stdout
 - prompt：直接把消息文本当输出返回
 - http：JSON POST，带超时与响应体大小上限
- F7: `Once` 控制：同一 hook ID 只触发一次。
- F8: `Async` 控制：goroutine 执行不阻塞主流程，结果走 notifications 队列。
- F9: 加载期校验 `Validate([]Hook) error`：参考 的 Zod discriminated union 模式，按 `Action.Type` 分支检查各类型必填字段（command 必有 command 字段、prompt 必有 message、http 必有可解析的 url），event 名必须在 9 事件白名单里，timeout 必须 ≥ 0；非法配置返回带 hook id / 字段路径的可读错误。`LoadHooks` 调用前必须先过校验，跑通才注入引擎。
- F10: command 动作超时执行：参考 的 `hookTimeoutMs = hook.timeout * 1000 ?? TOOL_HOOK_EXECUTION_TIMEOUT_MS (10min)` 策略，Go 端用 `exec.CommandContext + context.WithTimeout` 包子进程；`Action.Timeout` 配置为 0 时取 10 分钟默认值；超时后子进程被 kill，`HookResult.Success = false`，输出体包含「command timed out after Xs」可读提示。

## 4. 非功能需求

- N1: hook 执行不能 panic：condition 解析失败按「不命中」处理；动作执行错误按 OnError 策略走。
- N2: 并发安全：内部 mutex 保护 hooks / fired / notifications 状态；执行前拷贝快照，避免长时持锁。
- N3: HTTP hook 必须有超时与响应体大小限制，避免外网卡死或大响应阻塞 agent loop。
- N4: `RunPreToolHooks` reject 消息必须可读，缺消息时给 fallback。
- N5: `Validate` 出错时必须能定位到具体 hook：错误消息含 hook id 或 index + 出错字段名，参照 Zod safeParse 的 path + message 格式。
- N6: command 超时不能泄漏子进程：`exec.CommandContext` 必须在退出前确认子进程已结束或被 kill，避免僵尸进程。

## 5. 设计概要

- 核心数据结构:
 - `Hook`：ID / Event / Condition / Action / Reject / Once / Async / OnError，yaml 字段名小写，可用 if 代替 condition
 - `Action`：单结构承载所有动作类型，按 Type 字段分发，覆盖 command / message / url / method / headers / body / timeout
 - `HookContext`：事件名 / 工具名 / 工具参数 / 文件路径 / 消息 / 错误，供 condition 与执行器读
 - `HookResult`：hook ID / 输出 / 成功标志 / reject 标志
 - `Engine`：mutex + hooks + notifications + fired，注册表加执行状态
 - `defaultHookTimeout`：包级常量 `10 * time.Minute`，对应目标设计 `TOOL_HOOK_EXECUTION_TIMEOUT_MS`
- 主流程:
 1. main 启动 → TUI 接到 `[]hooks.Hook` 配置
 2. provider 就绪 → TUI 构造 Engine、调 `Validate(hooks)` 校验非法配置，错则向用户报错并 fallback 为空 hooks；通过则 `LoadHooks` 挂到 agent.Hooks
 3. agent loop 工具调用前调 `RunPreToolHooks`，被阻断时把 reject 消息当工具结果返回
 4. agent loop 工具调用后调 `RunHooks(post_tool_use)`
 5. condition 执行: `RunHooks` → snapshotHooks → shouldFire → evaluateCondition → 拆分复合 / 评估 leaf / 解析变量
 6. command 执行: `runCommand` → 选 timeout（hook.Action.Timeout 或 defaultHookTimeout）→ `exec.CommandContext` 包 bash -c → 超时时上下文 cancel → 子进程被 kill，HookResult 写入超时原因
- 调用链（模块层级）:
 - 启动: main → tui.New（带 hook 配置）→ Engine 初始化 → 挂到 agent.Hooks
 - 触发: agent.Run → executeTool → RunPreToolHooks → tool.Execute → RunHooks(post_tool_use)
- 与其他模块的交互:
 - 上行依赖：agent（loop 触发）、tui（生命周期与配置接入）、config（yaml 字段绑定）
 - 下行：无（hooks 包不 import 其他内部模块）

## 6. Out of Scope

- `agent` action type（MEWCODE.md 提到的第 4 种执行器）：本章不实现，建议在 ch13 SubAgent 稳定后再补，否则没法启子代理
- 已声明但未触发的事件（session_start / session_end / turn_start / turn_end / pre_send / post_receive / shutdown）：等业务场景出现再在 agent loop / TUI 补 emit
- `DrainNotifications`：当前没消费方，等通知中心模块出现后再接入或删除
- Hook DSL 的括号 / 短路求值：本实现两侧 leaf 都跑（leaf 解析便宜），不补复杂括号文法
- Hook 配置的热更新：必须重启或重新选 provider 才生效

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch12: Hook 系统 Tasks

## T1: 定义事件 / 动作类型常量与数据结构
- 影响文件: `internal/hooks/hooks.go`
- 依赖任务: 无
- 完成标准: 9 个 `EventName` 常量 + 4 个 `ActionType` 常量；`Hook / Action / HookContext / HookResult / Engine` 类型齐全且 yaml tag 正确。
- 实际产出: `hooks.go:19-88`

## T2: Condition DSL —— leaf / composite / inverse
- 影响文件: `internal/hooks/hooks.go`
- 依赖任务: T1
- 完成标准: 支持 `==/!=/=~/=*` 四种 leaf；支持 `&&/||` composite；支持 `!` 前缀 inverse；支持 `tool / event / file_path / message / args.<key>` 变量。
- 实际产出: `hooks.go:195-294`（evaluateCondition / splitComposite / evaluateLeaf / resolveVar）

## T3: Engine 核心 —— Register / RunHooks / Once / Async
- 影响文件: `internal/hooks/hooks.go`
- 依赖任务: T1, T2
- 完成标准: `NewEngine / LoadHooks / RunHooks / shouldFire / snapshotHooks` 全部实现；once 命中后跳过；async 通过 goroutine 异步执行返回 `(async)` 占位结果。
- 实际产出: `hooks.go:90-186`

## T4: Pre-tool 阻断专用入口
- 影响文件: `internal/hooks/hooks.go`
- 依赖任务: T3
- 完成标准: `RunPreToolHooks(ctx) (bool, string)`，按 reject 字段或 OnError=="reject" 命中失败的命令决定是否阻断；fallback 消息 `blocked by hook <ID>`。
- 实际产出: `hooks.go:127-147`

## T5: 三种动作执行器（command / prompt / http）
- 影响文件: `internal/hooks/hooks.go`
- 依赖任务: T3
- 完成标准:
 - command/script: bash -c 执行，注入 `MEWCODE_EVENT / MEWCODE_TOOL / MEWCODE_FILE_PATH`，stdout+stderr 合并；
 - prompt: 直接返回 Message；
 - http: POST/JSON 默认，10s 默认超时，限制响应体 64KB。
- 实际产出: `hooks.go:296-391`（executeAction / runCommand / runHTTP）

## T6: 单元测试
- 影响文件: `internal/hooks/hooks_test.go`
- 依赖任务: T1-T5
- 完成标准: 覆盖 leaf 四种操作符、composite、inverse、reject、once、http、async、on_error=reject。
- 实际产出: `hooks_test.go:12-174`（6 个测试用例 / `TestEvaluateConditionLeafOps` 单测就跑了 13 种 condition）

## T7: 接入主流程 —— config 绑定
- 影响文件: `internal/config/config.go`
- 依赖任务: T1
- 完成标准: `AppConfig` 含 `Hooks []hooks.Hook` 字段，yaml 反序列化能直接拿到 hooks 列表。
- 实际产出: `internal/config/config.go:82-87`

## T8: 接入主流程 —— TUI 装配 + Agent 触发
- 影响文件: `internal/tui/tui.go`、`internal/agent/agent.go`、`cmd/mewcode/main.go`
- 依赖任务: T1-T5, T7
- 完成标准:
 - 入口透传: `main.go:32` 把 `cfg.Hooks` 传给 `tui.New`；
 - TUI 装配: `tui.go:191`(`New`) 接收 hookConfigs，`tui.go:371-375` 与 `tui.go:733-737` 在 agent 初始化时建 Engine 挂到 `ag.Hooks`；
 - Agent loop 触发: `agent.go:409-424`(`RunPreToolHooks`)、`agent.go:429-437`(`RunHooks(post_tool_use)`)。
- 实际产出: 同上。

## T9: 端到端验证
- 影响文件: 无
- 依赖任务: T8
- 完成标准: 在 `config.yaml` 配 `hooks: [{event: pre_tool_use, if: 'tool == "Bash" && args.command =~ /rm -rf/', action: {type: prompt, message: "blocked"}, reject: true}]`，TUI 起来后让 LLM 调 Bash + `rm -rf` 看到工具结果是 `Blocked by hook: blocked`；HTTP hook 用 `hooks_test.go:103-134` 的 `httptest.NewServer` 路径已覆盖。
- 实际产出: 由 `hooks_test.go` 中 `TestRunPreToolHooksReject / TestHookHTTPAction / TestHookOnErrorReject` 覆盖核心端到端逻辑；TUI 配置文件流程见 checklist §5。

## T10: 加载期校验 `Validate([]Hook) error`
- 影响文件: `internal/hooks/hooks.go`、`internal/hooks/hooks_test.go`
- 依赖任务: T1
- 完成标准:
 - 新增 `Validate(hooks []Hook) error`，遍历每个 hook，按 Action.Type 分支校验：
 - command/script：`Command` 非空
 - prompt：`Message` 非空
 - http：`URL` 必须能被 `url.Parse` 解析且 scheme 是 http/https
 - agent：`Message` 或 `Command` 至少有一个非空（占位 stub 也要 prompt）
 - 未知 Type：报错
 - Event 名必须在 9 事件白名单内（与 `EventName` 常量集合一致）
 - `Timeout >= 0`（Zod 用 positive；这里 0 表示「用默认值」，符合 Go 零值约定，所以放宽到 >=0）
 - 错误消息含 hook id（无 id 则用 index）+ 出错字段名，例如：`hook[0] (id="auto-format"): action.command must be non-empty for type "command"`
 - 多个错误用 `errors.Join` 聚合一次性回报，不要遇到第一个就 short-circuit
 - `LoadHooks` 不调 Validate（保持原有低耦合）；改在 `cmd/mewcode/main.go` 或 `internal/config/config.go` 加载完 yaml 后调 Validate，错误打到 stderr，让 TUI 用空 hooks 启动而不是 crash
- 实际产出: 待实现

## T11: command 动作超时执行
- 影响文件: `internal/hooks/hooks.go`、`internal/hooks/hooks_test.go`
- 依赖任务: T5
- 完成标准:
 - 新增包级常量 `defaultHookTimeout = 10 * time.Minute`（保持一致）
 - `runCommand` 改用 `exec.CommandContext`：
 - 超时 = `hook.Action.Timeout`，零值时取 `defaultHookTimeout`
 - `ctx, cancel := context.WithTimeout(context.Background(), timeout)`，defer cancel
 - 超时时返回 `HookResult{Success: false, Output: "command timed out after Xs: <stdout/stderr>"}`，并把超时事实写进 output 让用户能在通知里看到
 - 现有 stdout/stderr 合并、`MEWCODE_*` 环境变量注入逻辑保持不动
 - 测试：超时配 `100ms`，命令是 `sleep 1`，断言 `Success == false` 且 output 包含 "timed out"
 - 测试：超时配 `0`（默认），命令是 `echo ok`，断言能在毫秒级返回并 Success
- 实际产出: 待实现

## 进度
- [ ] T1
- [ ] T2
- [ ] T3
- [ ] T4
- [ ] T5
- [ ] T6
- [ ] T7
- [ ] T8
- [ ] T9
- [ ] T10
- [ ] T11
```
```plain
# ch12: Hook 系统 Checklist

## 1. 实现完整性

- [ ] 9 个 `EventName` 常量在 `internal/hooks/hooks.go:19-30`：session_start / session_end / turn_start / turn_end / pre_send / post_receive / pre_tool_use / post_tool_use / shutdown
- [ ] 4 个 `ActionType` 常量在 `hooks.go:32-39`：command / script / prompt / http
- [ ] 数据结构 `Hook / Action / HookContext / HookResult / Engine` 在 `hooks.go:41-88`，yaml tag 完整
- [ ] `NewEngine / LoadHooks / RunHooks / RunPreToolHooks / shouldFire / snapshotHooks / recordNotification / DrainNotifications` 全部在 `hooks.go:90-186`
- [ ] Condition DSL 支持 leaf（==/!=/=~/=*）+ composite（&&/||）+ inverse（!），实现在 `hooks.go:195-272`
- [ ] 变量解析支持 `tool / event / file_path / message / args.<key>`，实现在 `hooks.go:274-294`
- [ ] `executeAction` 在 `hooks.go:296-316` 按 ActionType 分发；`runCommand` 在 `hooks.go:318-339`；`runHTTP` 在 `hooks.go:341-391`
- [ ] `runCommand` 注入环境变量 `MEWCODE_EVENT / MEWCODE_TOOL / MEWCODE_FILE_PATH`，stderr+stdout 合并
- [ ] `runHTTP` 默认 POST，默认 10s 超时，自动塞 Content-Type，响应体限 64KB
- [ ] `Once` 控制按 hook ID 去重（`shouldFire` 中 `e.fired[h.ID] = true`）
- [ ] `Async` 控制走 goroutine 异步执行 + 占位结果 `(async)`（`RunHooks` 中 `h.Async` 分支）
- [ ] `OnError == "reject"` 命中失败命令时按 reject 处理（`RunPreToolHooks` 中 `!result.Success && h.OnError == "reject"`）
- [ ] `Validate(hooks []Hook) error` 已实现：按 Action.Type 分支校验 command/prompt/http/agent 各自必填字段，event 名必须在 9 事件白名单，timeout >= 0；错误消息包含 hook id（或 index）+ 出错字段名；多错误用 `errors.Join` 聚合一次性返回
- [ ] 包级常量 `defaultHookTimeout = 10 * time.Minute` 存在，保持一致
- [ ] `runCommand` 走 `exec.CommandContext`：超时 = `hook.Action.Timeout`，零值取 `defaultHookTimeout`；超时时 `HookResult.Success == false` 且 `Output` 含 "timed out" 关键字
- [ ] `runCommand` 仍注入 `MEWCODE_EVENT / MEWCODE_TOOL / MEWCODE_FILE_PATH` 环境变量，超时改动不破坏既有路径

## 2. 接入完整性

- [ ] `grep -rn "hooks.NewEngine" --include="*.go" /Users/codemelo/mewcode` 命中 `internal/tui/tui.go:372` 和 `tui.go:734` 两个非测试调用方
- [ ] `grep -rn "RunPreToolHooks\|RunHooks(" --include="*.go" /Users/codemelo/mewcode | grep -v _test` 命中 `internal/agent/agent.go:416` 与 `agent.go:430` 两个 agent loop 触发点
- [ ] Config 绑定：`internal/config/config.go:86` 含 `Hooks []hooks.Hook` 字段，main.go:32 透传 `cfg.Hooks` 进 `tui.New`
- [ ] Agent 字段：`internal/agent/agent.go:37` 含 `Hooks *hooks.Engine`，TUI 在 provider 初始化路径上挂上
- [ ] 入口路径：`config.yaml.hooks → cfg.Hooks → tui.New(..., hooks) → m.hookConfigs → hooks.NewEngine + LoadHooks → ag.Hooks → agent.Run → executeTool 调 RunPreToolHooks/RunHooks`
- [ ] 死代码 1 已解决（2026-05-21）：`Engine.DrainNotifications` 在 `internal/tui/tui.go:500-507drainTaskNotifications` 中消费，把 hook 输出包成 `<hook-notification>` 注入下一轮 system reminder。`grep -rn "Hooks.DrainNotifications" --include="*.go" /Users/codemelo/mewcode` 返回 ≥1 条非测试调用方。
- [ ] 死代码 2 已解决（2026-05-21）：`ActionScript` 常量已删。
- [ ] 缺失事件触发已补 6/7（2026-05-21）：`EventSessionStart / SessionEnd / TurnStart / TurnEnd / PreSend / PostReceive` 由 `Agent.emitHook` 在 Run() 入口/出口、每轮迭代头尾、Stream 前/后 emit（`agent.go` Run 函数）。`EventShutdown` 是进程级信号，留作后续在 `cmd/main.go` 装信号处理器时补。
- [ ] 缺失 agent action 类型已解决（2026-05-21）：新增 `ActionAgent` 常量 + `Engine.AgentRunner` 字段；`executeAction` 走 `runAgent` 分支（`hooks.go:296-345`）；TUI 注册 `newAgentHookRunner` 闭包走 `llm.Client.Stream` 单轮调用。对应目标设计 `execAgentHook.ts:36 execAgentHook`。
- [ ] `Validate` 接入入口：`grep -rn "hooks.Validate" --include="*.go" /Users/codemelo/mewcode` 至少命中 1 处非测试调用方（建议在 `cmd/mewcode/main.go` 或 `internal/config/config.go` 的配置加载路径里）；非法 hook 配置启动时被打印到 stderr 而不是默默吞掉

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && go build ./internal/hooks/...` 通过
- [ ] `cd /Users/codemelo/mewcode && go test ./internal/hooks/...` 全部测试通过：原 7 个测试 + 新增 `TestValidateCatchesMissingFields` / `TestValidateAggregatesAllErrors` / `TestValidateAcceptsGoodConfig` / `TestRunCommandTimeout` / `TestRunCommandDefaultTimeoutAllowsFastCommand`
- [ ] `go vet ./internal/hooks/...` 无警告
- [ ] `cd /Users/codemelo/mewcode && go build ./...` 通过（hooks 包被 agent/tui/config import）

## 4. 端到端验证

- [ ] 在 `config.yaml` 配 pre_tool_use reject hook，启动 TUI 让 LLM 触发匹配的 Bash 命令，工具结果是 `Blocked by hook: <message>`（路径 `agent.go:416-424`）
- [ ] HTTP hook 由 `hooks_test.go:103-134` 用 `httptest.NewServer` 验证 POST + JSON Content-Type + 计数到达
- [ ] async hook 由 `hooks_test.go:136-156` 验证耗时 0.2s 的命令不阻塞主线
- [ ] once hook 由 `hooks_test.go:84-101` 验证第二次 RunHooks 返回空 results
- [ ] on_error=reject 由 `hooks_test.go:158-174` 验证退出码 7 的命令导致 RunPreToolHooks 阻断
- [ ] `Validate` 端到端：在临时 `config.yaml` 配一个非法 hook（如 `event: pre_tool_use, action: {type: command}`，缺 command 字段），`go run ./cmd/mewcode` 启动时 stderr 看到 `hook[0]: action.command must be non-empty for type "command"` 形式的错误
- [ ] command 超时端到端：配 `timeout: 100ms` + `command: "sleep 5"` 的 post_tool_use hook，TUI 触发一次工具调用，从 `DrainNotifications` 拿到的 HookResult.Output 含 "timed out"
- [ ] 留存证据: 未提供 TUI 截图（手动验证不在课程验收流程要求范围内）

## 5. 文档

- [ ] `specs/go/ch12/spec.md` 存在
- [ ] `specs/go/ch12/tasks.md` 存在
- [ ] `specs/go/ch12/checklist.md` 存在
- [ ] commit 已落地为 `356deac feat: implement hooks system for pre and post tool execution`，但 message 未含章节号 `ch12` 与三件套关闭标记。建议在下一次 commit 三件套时改写为 `docs(ch12): close spec/tasks/checklist for hooks system`
```

### Python

```plain
# ch12: Hook 系统 Spec

## 1. 背景

Agent 主流程在工具调用前后、session 起止、turn 起止、消息收发等关键节点都有「副作用钩子」的需求：工具调用前阻断危险命令、调用后异步推日志到外部系统、用户提交前注入额外提示词、新 session 启动时拉取项目上下文。把这些写死在 Agent 循环里既不优雅又难配置。Hook 系统把这层做成可声明（yaml）+ 条件匹配 + 多种动作类型的引擎，并保留 once / async（async_exec）/ reject 三种执行控制。Python 实现使用 asyncio 协程作为执行单位，配合 `asyncio.create_subprocess_shell` 跑外部命令，`urllib.request` + `run_in_executor` 跑 HTTP。

## 2. 目标

交付 `mewcode.hooks.HookEngine`，从 `config.yaml` 的 `hooks` 数组加载并经 `load_hooks` 校验后注入引擎；提供两类入口：普通事件用 `run_hooks(event, ctx)` 跑全部命中钩子；`pre_tool_use` 用 `run_pre_tool_hooks(ctx)` 允许阻断工具调用并返回 `ToolRejectedError`。Condition 支持 leaf 操作符（`==` / `!=` / `=~` / `~=`）+ 复合（`&&` / `||`，但同一表达式不允许混用）+ 变量覆盖 tool / event / `args.<key>`。`Agent.run` 在 session 入口、turn 入口、每次工具调用前后、消息收发前后接入对应入口；`MewCodeApp` 负责从配置初始化引擎并挂到 Agent，并在 mount / unmount 时触发 startup / shutdown 事件。

## 3. 功能需求

- F1: 提供 15 个生命周期事件常量（`LifecycleEvent` StrEnum）：session_start / session_end / turn_start / turn_end / pre_tool_use / post_tool_use / pre_send / post_receive / startup / shutdown / error / compact / permission_request / file_change / command_execute。
- F2: 提供 4 个动作类型（在 loader 的 `_VALID_ACTION_TYPES` 集合里）：command / prompt / http / agent；`agent` 当前为 stub，返回 "agent executor not yet implemented"。
- F3: Condition DSL：
  - leaf 操作符：`==`（等于）/ `!=`（不等于）/ `=~`（正则，包裹 `/.../` 时自动去除斜杠）/ `~=`（glob，走 `fnmatch.fnmatch`）
  - 复合：`&&` / `||`，但一行表达式只能用一种，混用抛 `ConditionParseError("Cannot mix '&&' and '||'")`
  - 变量解析：`tool` / `event` / `args.<key>`，由 `HookContext.get_field` 实现
  - 模板展开：动作字段中支持 `$EVENT / $TOOL_NAME / $FILE_PATH / $MESSAGE / $ERROR / $TOOL_ARGS.<key>`，由 `HookContext.expand` 替换
- F4: `HookEngine.run_hooks(event, ctx)` 按事件名 + condition 过滤后逐个执行；`async_exec=True` 的 hook 通过 `asyncio.ensure_future` 后台跑，不阻塞主协程；`prompt` 类型成功结果写入 `_prompt_messages` 队列，由 `get_prompt_messages()` 一次性取出后清空。
- F5: `HookEngine.run_pre_tool_hooks(ctx)` 专门跑 `pre_tool_use` 事件：任何 `hook.reject=True` 命中即返回 `ToolRejectedError(tool, reason, hook_id)`；执行异常被捕获并写 log，不影响主流程。
- F6: 动作执行器：
  - command：`asyncio.create_subprocess_shell` 拉子进程，stderr 合并到 stdout，命令字符串先经 `ctx.expand` 替换变量
  - prompt：直接对 `action.message` 做变量替换后返回，`success=True`
  - http：默认 POST，`urllib.request.Request` + `urlopen` 走 `run_in_executor` 异步化；带 body 时自动添加 `Content-Type: application/json`，响应体截断到 500 字节
  - agent：stub，仅记录日志并返回成功占位字符串
- F7: `once` 控制：`Hook.executed` 在首次触发后置 True，`Hook.should_run()` 在 `once=True` 且 `executed=True` 时返回 False，`find_matching_hooks` 据此跳过。
- F8: `async_exec` 控制：`run_hooks` 中以 `asyncio.ensure_future(self._run_single(hook, ctx))` 派发，不 await；`run_pre_tool_hooks` 不支持 async（loader 校验阻止）。
- F9: 加载期校验 `load_hooks(raw_hooks) -> list[Hook]`：
  - event 必须在 `LifecycleEvent` 白名单内
  - action.type 必须在 `_VALID_ACTION_TYPES = {"command","prompt","http","agent"}` 里
  - 按 `_REQUIRED_FIELDS` 强制每种类型的必填字段：command→command、prompt→message、http→url、agent→prompt
  - `reject=True` 只允许配在 `pre_tool_use` 事件上
  - `async=True` 不允许配在 `pre_tool_use` 事件上
  - `action.timeout` 必须是正整数（>0）
  - hook id 缺失时按 `f"{event}_{i}"` 自动生成
  - condition 字符串经 `parse_condition` 解析失败时包成 `HookConfigError`
  - 任意非法配置抛 `HookConfigError`，错误消息带 `f"hook '{id}'"` 或 `f"hook #{index+1}"` 定位
- F10: command 动作超时执行：`execute_command` 使用 `asyncio.wait_for(proc.communicate(), timeout=action.timeout)`，超时时 `proc.kill()` + `await proc.wait()` 清理子进程，返回 `ActionResult(output="Command timed out after Xs: <cmd>", success=False)`；`action.timeout` 默认值在 `Action` dataclass 中为 30 秒。

## 4. 非功能需求

- N1: hook 执行不能让 Agent 主协程崩溃：`_run_single` / `run_pre_tool_hooks` 内层 `try/except Exception`，捕获后记录 warning log 并写入 `_notifications`；condition 正则编译失败按「不命中」处理（`re.error` 返回 False）。
- N2: 并发安全：`HookEngine` 设计运行在单 event loop 上，所有状态修改在协程内顺序进行，无需显式锁；`async_exec` 派生的协程通过 `asyncio.ensure_future` 注册到 loop，由 loop 调度。
- N3: HTTP hook 必须有超时与响应体大小限制：`urlopen(req, timeout=30)`，响应体截断 500 字符；通过 `run_in_executor` 把同步 `urlopen` 放到默认线程池，避免阻塞 event loop。
- N4: `run_pre_tool_hooks` reject 时 `ToolRejectedError.reason` 必须取自 action 输出，Agent loop 包装为 `"Hook rejected: {reason}"` 作为工具结果。
- N5: `load_hooks` 出错时必须能定位到具体 hook：错误消息含 hook id（无则用 `f"hook #{i+1}"`）+ 出错字段名，例如 `hook 'auto-format': action type 'command' requires 'command' field`。
- N6: command 超时不能泄漏子进程：`asyncio.TimeoutError` 分支必须先 `proc.kill()` 再 `await proc.wait()`，确认子进程退出后才返回，避免僵尸进程。

## 5. 设计概要

- 核心数据结构：
  - `LifecycleEvent`（StrEnum，15 个值）：所有生命周期事件常量
  - `Action`（dataclass）：type / command / message / url / method / body / headers / prompt / timeout，单结构承载四种动作类型
  - `Condition`（dataclass）：field / operator / value，叶子条件
  - `ConditionGroup`（dataclass）：conditions 列表 + logic（"and"/"or"），复合条件
  - `Hook`（dataclass）：id / event / action / condition / reject / once / async_exec / executed，配合 `should_run()` / `mark_executed()` 方法
  - `HookContext`（dataclass）：event_name / tool_name / tool_args / file_path / message / error，配合 `get_field()` / `expand()` 方法
  - `ActionResult`（dataclass）：output / success
  - `HookNotification`（dataclass）：hook_id / event / output / success，drain 队列单元
  - `HookEngine`：hooks 列表 + `_prompt_messages` 队列 + `_notifications` 队列
  - `ToolRejectedError`（Exception）：tool / reason / hook_id
  - `HookConfigError`（Exception）：loader 报错
  - `ConditionParseError`（Exception）：condition 解析报错
- 主流程：
  1. `mewcode/__main__.py:main` 启动 → `load_config` 读 `config.yaml` 拿到 `raw_hooks`（dict 列表）
  2. `load_hooks(raw_hooks)` 校验 + 解析成 `list[Hook]`；`HookConfigError` 时打 stderr 并 `sys.exit(1)`
  3. `HookEngine(hooks)` 构造 → 传入 `MewCodeApp(..., hook_engine=...)` → `Agent(..., hook_engine=...)`
  4. App `on_mount` 派发 `startup` 事件；`on_unmount` 派发 `shutdown` 事件
  5. `Agent.run` 入口派发 `session_start` → 每轮 `turn_start` → stream 前 `pre_send` → stream 后 `post_receive` → 退出循环时派发 `turn_end` + `session_end`
  6. 工具调用前调 `run_pre_tool_hooks(ctx)`：返回 `ToolRejectedError` 时打包成 `ToolResult(output=f"Hook rejected: {reason}", is_error=True)`，跳过实际 tool 执行
  7. 工具调用后调 `run_hooks("post_tool_use", ctx)`
  8. 每轮 hook 执行完后调 `_drain_hook_events()`，把 `HookNotification` 转成 `HookEvent` 事件流 yield 给 TUI 展示
- 调用链（模块层级）：
  - 启动：`mewcode/__main__.py` → `load_hooks` → `HookEngine` → `MewCodeApp` → `Agent`
  - 触发：`Agent.run` → `_build_hook_context` → `hook_engine.run_hooks` / `run_pre_tool_hooks` → `execute_action` → `_EXECUTOR_MAP[type]`
- 与其他模块的交互：
  - 上行依赖：`agent.py`（loop 触发）、`app.py`（startup/shutdown）、`config.py`（raw_hooks 字段）、`__main__.py`（装配入口）
  - 下行：仅依赖 Python 标准库（asyncio / urllib / fnmatch / re）

## 6. Out of Scope

- `agent` action type 真正实现：当前是 stub，建议在 ch13 SubAgent 稳定后再补上（调 `Agent.run` 单轮）
- 已声明但未在主流程触发的事件（error / compact / permission_request / file_change / command_execute）：等业务场景出现再在对应模块 emit
- Condition DSL 的括号 / 短路求值 / 混合 `&&` 和 `||`：当前实现明确拒绝混用，需要复杂逻辑时建议拆成多个 hook
- Hook 配置的热更新：必须重启进程才生效
- HTTP hook 的认证 / 重试 / mTLS / 大响应流式处理：当前仅支持简单 POST + JSON

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch12: Hook 系统 Tasks

## T1: 定义生命周期事件常量
- 影响文件: `mewcode/hooks/events.py`
- 依赖任务: 无
- 完成标准: `LifecycleEvent` StrEnum 包含 15 个事件值（session_start / session_end / turn_start / turn_end / pre_tool_use / post_tool_use / pre_send / post_receive / startup / shutdown / error / compact / permission_request / file_change / command_execute）；可直接和字符串比较。
- 实际产出: `mewcode/hooks/events.py:6-30`

## T2: 数据模型 —— Action / Hook / HookContext / ActionResult / ToolRejectedError
- 影响文件: `mewcode/hooks/models.py`
- 依赖任务: T1
- 完成标准:
  - `Action`（dataclass）字段齐：type / command / message / url / method / body / headers / prompt / timeout（默认 30）
  - `Hook`（dataclass）字段齐：id / event / action / condition / reject / once / async_exec / executed；`should_run` 检查 once + executed；`mark_executed` 翻 True
  - `HookContext`（dataclass）实现 `get_field("tool"/"event"/"args.<key>")` 与 `expand` 模板替换（$EVENT / $TOOL_NAME / $FILE_PATH / $MESSAGE / $ERROR / $TOOL_ARGS.<key>）
  - `ActionResult`（dataclass）含 output / success
  - `ToolRejectedError(Exception)` 带 tool / reason / hook_id 三字段
- 实际产出: `mewcode/hooks/models.py:9-85`

## T3: Condition DSL —— leaf / 复合 / 解析
- 影响文件: `mewcode/hooks/conditions.py`
- 依赖任务: T2
- 完成标准:
  - 支持四种 leaf 操作符：`==` / `!=` / `=~`（正则）/ `~=`（glob，走 `fnmatch.fnmatch`）
  - `=~` 包裹 `/.../` 时自动去除斜杠；`re.error` 时返回 False
  - 支持 `&&` / `||` 复合，但同一表达式混用时 `parse_condition` 抛 `ConditionParseError("Cannot mix '&&' and '||'")`
  - 空表达式或纯空白返回 None
  - 字符串值带双引号时自动去除
- 实际产出: `mewcode/hooks/conditions.py:12-96`（`Condition` / `ConditionGroup` / `parse_condition` / `_parse_single`）

## T4: HookEngine 核心 —— find_matching_hooks / run_hooks / once / async_exec
- 影响文件: `mewcode/hooks/engine.py`
- 依赖任务: T2, T3
- 完成标准:
  - `HookEngine.__init__` 初始化 `hooks` / `_prompt_messages` / `_notifications` 三个状态
  - `find_matching_hooks(event, ctx)` 按事件名 + `should_run` + condition 三层过滤
  - `run_hooks(event, ctx)` 顺序触发：`async_exec=True` 走 `asyncio.ensure_future(self._run_single(...))` 不 await；其余 await
  - `_run_single` 把 `prompt` 类型成功结果写入 `_prompt_messages`，所有结果写 `_notifications`，异常被 catch
  - `get_prompt_messages()` 一次性返回并清空 `_prompt_messages`
  - `drain_notifications()` 一次性返回并清空 `_notifications`
- 实际产出: `mewcode/hooks/engine.py:21-110`

## T5: pre_tool_use 阻断专用入口
- 影响文件: `mewcode/hooks/engine.py`
- 依赖任务: T4
- 完成标准: `run_pre_tool_hooks(ctx) -> ToolRejectedError | None`：顺序执行命中 hook，遇到 `hook.reject=True` 立即返回 `ToolRejectedError(tool=ctx.tool_name, reason=result.output, hook_id=hook.id)`；不允许 reject 时返回 None；执行异常被捕获记 log 不抛出。
- 实际产出: `mewcode/hooks/engine.py:80-103`

## T6: 四种动作执行器（command / prompt / http / agent）
- 影响文件: `mewcode/hooks/executors.py`
- 依赖任务: T2
- 完成标准:
  - `execute_command`：`asyncio.create_subprocess_shell` + stderr 合并到 stdout，命令字符串先 `ctx.expand` 替换变量；`asyncio.wait_for(..., timeout=action.timeout)` 超时时 `proc.kill()` + `await proc.wait()` 并返回 `success=False, output="Command timed out after Xs: <cmd>"`
  - `execute_prompt`：对 `action.message` 跑 `ctx.expand` 后包成 `ActionResult(output=..., success=True)`
  - `execute_http`：默认 POST，`urlopen(req, timeout=30)` 走 `run_in_executor` 异步化；body 非空时自动加 `Content-Type: application/json`；响应体截断 500 字符
  - `execute_agent`：stub，返回 `ActionResult(output="agent executor not yet implemented", success=True)`
  - `execute_action` 通过 `_EXECUTOR_MAP` 派发；未知 type 返回 `success=False`
- 实际产出: `mewcode/hooks/executors.py:13-97`

## T7: 加载与校验 `load_hooks(raw_hooks)`
- 影响文件: `mewcode/hooks/loader.py`
- 依赖任务: T1, T2, T3
- 完成标准:
  - `load_hooks(None)` / `load_hooks([])` 返回 `[]`
  - event 不在 `LifecycleEvent` 白名单内抛 `HookConfigError("invalid event ...")`
  - action.type 不在 `{"command","prompt","http","agent"}` 内抛 `HookConfigError("invalid action type ...")`
  - 按 `_REQUIRED_FIELDS` 校验每种类型必填字段（command→command、prompt→message、http→url、agent→prompt）
  - `reject=True` 且 event != "pre_tool_use" 抛错
  - `async=True` 且 event == "pre_tool_use" 抛错
  - timeout 非正整数抛错
  - hook id 缺失时按 `f"{event}_{i}"` 自动生成
  - condition 字符串经 `parse_condition` 解析失败时包成 `HookConfigError`
  - 错误消息含 hook id（无则用 `f"hook #{i+1}"`）
- 实际产出: `mewcode/hooks/loader.py:7-115`

## T8: 包出口与公共 API
- 影响文件: `mewcode/hooks/__init__.py`
- 依赖任务: T1-T7
- 完成标准: `mewcode.hooks` 包对外暴露 `Action / ActionResult / Condition / ConditionGroup / ConditionParseError / Hook / HookConfigError / HookContext / HookEngine / LifecycleEvent / ToolRejectedError / load_hooks / parse_condition`；测试 `from mewcode.hooks import HookEngine` 能跑通。
- 实际产出: `mewcode/hooks/__init__.py:1-27`

## T9: 单元测试覆盖
- 影响文件: `tests/test_hooks.py`
- 依赖任务: T1-T8
- 完成标准: 覆盖以下场景（每个一个 `pytest` 类）：
  - `TestLifecycleEvent`：15 个事件数量与字符串比较
  - `TestHookContext`：get_field 四种字段、expand 全变量替换、未定义变量保留
  - `TestParseCondition`：单条件 / `&&` / `||` / 混用错误 / 空 / 正则 / 无操作符
  - `TestConditionEvaluate`：四种 leaf 操作符
  - `TestConditionGroupEvaluate`：and 全通过 / and 部分失败 / or 任一通过 / or 全失败 / 空 group
  - `TestCommandExecutor`：正常执行 / 变量替换 / 超时
  - `TestPromptExecutor`：返回 message
  - `TestHttpExecutor`：mock urlopen 验证 status
  - `TestAgentExecutor`：stub 返回不抛错
  - `TestExecuteAction`：派发 + 未知 type
  - `TestLoadHooks`：完整配置 / 自动 id / 空输入 / 各类非法配置错误
  - `TestHookEngine`：find_matching_hooks / condition 过滤 / once 过滤 / reject / 非 reject / prompt 消息收集 / 错误不抛 / async 不阻塞
  - `TestAgentHookIntegration`：mock LLM 触发 `rm -rf` 被 reject 后 Agent 收到 `Hook rejected: ...` 错误结果
- 实际产出: `tests/test_hooks.py:1-510`（13 个测试类）

## T10: 接入主流程 —— config 绑定
- 影响文件: `mewcode/config.py`
- 依赖任务: T1
- 完成标准: `AppConfig` dataclass 新增 `raw_hooks: list[dict]` 字段（保留原始 dict，由 loader 二次解析）；`load_config` 在 `validate_config_structure` 后填入 `raw_hooks=validated["hooks"]`。
- 实际产出: `mewcode/config.py:93`（字段定义）、`mewcode/config.py:152`（赋值）

## T11: 接入主流程 —— Agent + App 装配 + Agent loop 触发
- 影响文件: `mewcode/__main__.py`、`mewcode/app.py`、`mewcode/agent.py`
- 依赖任务: T2-T8, T10
- 完成标准:
  - 入口：`mewcode/__main__.py:40-45` 调 `load_hooks(config.raw_hooks)`，`HookConfigError` 时打 stderr + `sys.exit(1)`，否则 `HookEngine(hooks)` 传给 `MewCodeApp`
  - App 装配：`mewcode/app.py:515 / 526` 接收 `hook_engine` 参数并持有；`mewcode/app.py:658` 把 `hook_engine` 透传给 `Agent`
  - 生命周期：`mewcode/app.py:803-808`（startup）/`mewcode/app.py:1581-1587`（shutdown）派发对应事件
  - Agent 字段：`mewcode/agent.py:296 / 314` 接收 `hook_engine` 参数；`mewcode/agent.py:371-382` 实现 `_build_hook_context`；`mewcode/agent.py:384-394` 实现 `_drain_hook_events`
  - Agent loop 触发点：
    - session_start：`mewcode/agent.py:407-410`
    - turn_start：`mewcode/agent.py:427-430`
    - pre_send：`mewcode/agent.py:460-463` + `get_prompt_messages` 注入下一轮
    - post_receive：`mewcode/agent.py:509-512`
    - pre_tool_use：`mewcode/agent.py:625-636`（reject 时把 `Hook rejected: {reason}` 包成 `ToolResult` 并 yield `ToolResultEvent(is_error=True)`）
    - post_tool_use：`mewcode/agent.py:674-682`
    - turn_end + session_end：`mewcode/agent.py:569-573`
- 实际产出: 同上

## T12: 端到端验证
- 影响文件: 无
- 依赖任务: T11
- 完成标准: 在 `config.yaml` 配 `hooks: [{event: pre_tool_use, if: 'tool == "Bash" && args.command =~ /rm\s+-rf/', action: {type: prompt, message: "blocked"}, reject: true}]`，启动 `python -m mewcode` 让 LLM 调 Bash + `rm -rf` 看到工具结果是 `Hook rejected: blocked`；HTTP hook / async hook / once hook 路径由 `tests/test_hooks.py` 中对应测试覆盖。
- 实际产出: 由 `TestAgentHookIntegration.test_pre_tool_use_reject_skips_tool` + `TestHookEngine` 系列覆盖；配置文件手测见 checklist §4。

## 进度
- [ ] T1
- [ ] T2
- [ ] T3
- [ ] T4
- [ ] T5
- [ ] T6
- [ ] T7
- [ ] T8
- [ ] T9
- [ ] T10
- [ ] T11
- [ ] T12
```
```plain
# ch12: Hook 系统 Checklist

## 1. 实现完整性

- [ ] 15 个生命周期事件常量在 `mewcode/hooks/events.py:6-30`：session_start / session_end / turn_start / turn_end / pre_tool_use / post_tool_use / pre_send / post_receive / startup / shutdown / error / compact / permission_request / file_change / command_execute；`len(LifecycleEvent) == 15`
- [ ] 4 个动作类型在 `mewcode/hooks/loader.py:8` 的 `_VALID_ACTION_TYPES` 集合：command / prompt / http / agent
- [ ] 数据结构 `Action / ActionResult / Hook / HookContext / ToolRejectedError` 在 `mewcode/hooks/models.py:9-85`，字段齐全
- [ ] `Condition / ConditionGroup / parse_condition / _parse_single` 在 `mewcode/hooks/conditions.py:12-96`；leaf 操作符 `==/!=/=~/~=` 全部实现
- [ ] `_OPERATORS = ("==", "!=", "=~", "~=")` 常量在 `mewcode/hooks/conditions.py:54`
- [ ] 同一表达式混用 `&&` 和 `||` 时 `parse_condition` 抛 `ConditionParseError("Cannot mix '&&' and '||' in a single condition expression")`（`mewcode/hooks/conditions.py:79-83`）
- [ ] `HookEngine / HookNotification` 在 `mewcode/hooks/engine.py:14-110`；`__init__` 初始化 `hooks` / `_prompt_messages` / `_notifications` 三个状态
- [ ] `find_matching_hooks` 三层过滤（event / should_run / condition）在 `mewcode/hooks/engine.py:31-41`
- [ ] `run_hooks` 中 `async_exec=True` 走 `asyncio.ensure_future(self._run_single(hook, ctx))` 不 await（`mewcode/hooks/engine.py:43-50`）
- [ ] `_run_single` 把 `prompt` 类型成功结果写入 `_prompt_messages`，所有结果写 `_notifications`，异常被 catch（`mewcode/hooks/engine.py:52-78`）
- [ ] `run_pre_tool_hooks` 遇到 `hook.reject=True` 即返回 `ToolRejectedError`（`mewcode/hooks/engine.py:96-102`）
- [ ] `get_prompt_messages()` 一次性取出并清空（`mewcode/hooks/engine.py:105-108`）
- [ ] `drain_notifications()` 一次性取出并清空（`mewcode/hooks/engine.py:110-113`）
- [ ] `execute_command` 在 `mewcode/hooks/executors.py:13-35`：`asyncio.create_subprocess_shell` + `stderr=STDOUT` 合并，超时时 `proc.kill()` + `await proc.wait()`，output 含 "timed out"
- [ ] `execute_prompt` 在 `mewcode/hooks/executors.py:38-40` 仅做模板替换
- [ ] `execute_http` 在 `mewcode/hooks/executors.py:43-72`：默认 POST，`urlopen(req, timeout=30)`，body 非空时自动加 `Content-Type: application/json`，响应体截断 500 字符
- [ ] `execute_http` 通过 `loop.run_in_executor(None, _do_request)` 把同步 urlopen 放到默认线程池
- [ ] `execute_agent` 在 `mewcode/hooks/executors.py:75-81` 是 stub，返回 "agent executor not yet implemented"
- [ ] `_EXECUTOR_MAP` + `execute_action` 派发在 `mewcode/hooks/executors.py:84-97`
- [ ] `load_hooks` 实现完整校验链路在 `mewcode/hooks/loader.py:25-115`：event 白名单、action.type 白名单、必填字段、reject/async 与 event 的约束、timeout 正整数、自动 id、condition 解析失败包错
- [ ] `Hook.should_run()` 在 `mewcode/hooks/models.py:43-46` 检查 once + executed，配合 `mark_executed()` 实现单次触发

## 2. 接入完整性

- [ ] `grep -rn "HookEngine(" /Users/codemelo/mewcode --include="*.py"` 命中 `mewcode/__main__.py:45` 一个非测试调用方
- [ ] `grep -rn "run_pre_tool_hooks\|run_hooks(" /Users/codemelo/mewcode --include="*.py" | grep -v test` 至少命中 `mewcode/agent.py` 7 处（session_start / turn_start / pre_send / post_receive / pre_tool_use / post_tool_use / turn_end+session_end）+ `mewcode/app.py` 2 处（startup / shutdown）
- [ ] Config 绑定：`mewcode/config.py:93` 含 `raw_hooks: list[dict] = field(default_factory=list)` 字段；`mewcode/config.py:152` 在 `load_config` 中填 `raw_hooks=validated["hooks"]`
- [ ] Agent 字段：`mewcode/agent.py:296` 构造参数含 `hook_engine: HookEngine | None = None`；`mewcode/agent.py:314` 赋值 `self.hook_engine = hook_engine`
- [ ] App 装配：`mewcode/app.py:515` 构造参数含 `hook_engine`；`mewcode/app.py:526` 赋值；`mewcode/app.py:658` 透传给 Agent
- [ ] 入口路径：`config.yaml` `hooks` → `config.raw_hooks` → `__main__.py:load_hooks` → `HookEngine(hooks)` → `MewCodeApp(hook_engine=...)` → `Agent(hook_engine=...)` → `agent.run` 内 emit
- [ ] 工具调用前 `pre_tool_use` 在 `mewcode/agent.py:625-636`，reject 时打包成 `ToolResult(output=f"Hook rejected: {rejection.reason}", is_error=True)` 并 yield `ToolResultEvent(is_error=True)`，`continue` 跳过实际执行
- [ ] 工具调用后 `post_tool_use` 在 `mewcode/agent.py:674-682`
- [ ] startup 事件在 `mewcode/app.py:803-808` 通过 `asyncio.ensure_future` 派发；shutdown 事件在 `mewcode/app.py:1581-1587` await 派发
- [ ] `_build_hook_context` 在 `mewcode/agent.py:371-382` 统一构造 `HookContext`
- [ ] `_drain_hook_events` 在 `mewcode/agent.py:384-394` 把 `HookNotification` 转成 `HookEvent` 流给 TUI 展示
- [ ] `pre_send` 钩子注入：`mewcode/agent.py:466-468` 调 `get_prompt_messages()` 把 prompt 类型 hook 输出注入下一轮 LLM 请求
- [ ] 非法 hook 配置启动时打 stderr 而非 crash：`mewcode/__main__.py:40-43` 捕获 `HookConfigError` 并 `sys.exit(1)`

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && ruff check mewcode/hooks/ tests/test_hooks.py` 通过
- [ ] `cd /Users/codemelo/mewcode && pytest tests/test_hooks.py -v` 全部测试通过：覆盖 `TestLifecycleEvent` / `TestHookContext` / `TestParseCondition` / `TestConditionEvaluate` / `TestConditionGroupEvaluate` / `TestCommandExecutor` / `TestPromptExecutor` / `TestHttpExecutor` / `TestAgentExecutor` / `TestExecuteAction` / `TestLoadHooks` / `TestHookEngine` / `TestAgentHookIntegration` 共 13 个测试类
- [ ] `cd /Users/codemelo/mewcode && python -c "from mewcode.hooks import HookEngine, load_hooks, LifecycleEvent; print(len(LifecycleEvent))"` 输出 `15`
- [ ] `cd /Users/codemelo/mewcode && python -c "from mewcode.agent import Agent; from mewcode.app import MewCodeApp"` 无 ImportError，确认 hooks 包被 agent/app 正确 import

## 4. 端到端验证

- [ ] 在 `config.yaml` 配 pre_tool_use reject hook（例如 `tool == "Bash" && args.command =~ /rm\s+-rf/`），`python -m mewcode` 启动 TUI 让 LLM 触发匹配的 Bash 命令，工具结果是 `Hook rejected: <message>`（路径 `mewcode/agent.py:625-636`）
- [ ] HTTP hook 由 `tests/test_hooks.py` 中 `TestHttpExecutor.test_mock_request` 用 `unittest.mock.patch` mock `urlopen` 验证 status 200 + 响应体
- [ ] async hook 由 `tests/test_hooks.py` 中 `TestHookEngine.test_async_hook_does_not_block` 验证 `sleep 5` 不阻塞主协程返回
- [ ] once hook 由 `tests/test_hooks.py` 中 `TestHookEngine.test_once_filter` 验证 `mark_executed()` 后 `find_matching_hooks` 返回空
- [ ] reject 端到端由 `tests/test_hooks.py` 中 `TestAgentHookIntegration.test_pre_tool_use_reject_skips_tool` 验证 mock LLM 调 `rm -rf /` 时 Agent 拿到的 `ToolResultEvent.is_error == True` 且 output 含 `Hook rejected`
- [ ] command 超时端到端：`tests/test_hooks.py` 中 `TestCommandExecutor.test_timeout` 验证 `sleep 10` + `timeout=1` 时 `success == False` 且 output 含 "timed out"
- [ ] 加载校验端到端：在临时 `config.yaml` 配一个非法 hook（如 `event: pre_tool_use, action: {type: command}` 缺 command），`python -m mewcode` 启动时 stderr 看到 `Hook config error: hook #1: action type 'command' requires 'command' field` 形式的错误并退出码 1（`mewcode/__main__.py:40-43`）
- [ ] 留存证据：未提供 TUI 截图（手动验证不在课程验收流程要求范围内）

## 5. 文档

- [ ] `docs/python/ch12/spec.md` 存在
- [ ] `docs/python/ch12/tasks.md` 存在
- [ ] `docs/python/ch12/checklist.md` 存在
- [ ] commit 已落地到 Python 分支 hooks 子系统；建议下一次三件套关闭 commit 使用形如 `docs(ch12-python): close spec/tasks/checklist for hooks system` 的消息
```

### Java

```plain
# ch12: Hook 系统 Spec

## 1. 背景

Agent 主流程在工具调用前后、session 起止、turn 起止等关键节点都有「副作用钩子」的需求：工具调用前阻断危险命令、调用后推日志到外部系统、session 起来时注入额外提示词。把这些写死在 agent 循环里既不优雅又难配置。Hook 系统把这层做成可声明（yaml）+ 简单条件匹配 + 两种动作类型的引擎，并通过 `reject` 字段让 `pre_tool_use` 钩子能阻断工具调用。Java 版以「最小可用」为目标，仅覆盖 command 和 prompt 两种动作，复杂语义（async / once / on_error / http）留到后续章节增量补齐。

## 2. 目标

交付 `com.mewcode.hook.HookEngine`，从 `config.yaml` 加载 hook 列表，按事件名提供两种入口：普通事件用 `runHooks(ctx)` 跑全部命中钩子；`pre_tool_use` 用 `runPreToolHooks(toolName, args)` 返回 `PreToolResult` 允许阻断工具调用。Condition 支持 `==` 等值 和 `=~` 正则两种 leaf 操作符，变量覆盖 tool / event / file_path / message / args.<key>。MewCodeModel 在 TUI 初始化阶段从 `List<HookConfig>` 装配 Engine，session_start / turn_start / turn_end 由 `fireHook` 在生命周期节点触发，工具级 pre / post hook 由 `StreamingExecutor.executeSingle` 调用。

## 3. 功能需求

- F1: 提供 9 个事件枚举值（SESSION_START / SESSION_END / TURN_START / TURN_END / PRE_SEND / POST_RECEIVE / PRE_TOOL_USE / POST_TOOL_USE / SHUTDOWN），覆盖会话与工具生命周期。
- F2: 提供 3 个动作枚举值（COMMAND / SCRIPT / PROMPT），其中 SCRIPT 仅占位、不实际执行（落到 default 分支返回 unknown action type）。HTTP / agent 类型不在本章范围（见 Out of Scope）。
- F3: Condition DSL（极简版）:
 - leaf 操作符：`==`（等值）、`=~`（正则匹配）
 - 不支持复合（`&&`/`||`）、不支持反向（`!`）
 - 未识别操作符时按「真」处理（与 Go 版兼容，不报错）
 - 变量：tool、event、file_path、message、`args.<key>`
- F4: `runHooks(HookContext ctx)` 按事件名过滤、按 condition 决定是否触发；同步执行全部命中钩子，结果同时写入 `notifications` 队列。
- F5: `runPreToolHooks(String toolName, Map<String, Object> args)` 专门跑 PRE_TOOL_USE 事件：构造 ctx → 按 condition 过滤 → 命中 reject 钩子时执行 action 并立即返回 `PreToolResult(true, output)`；无 reject 命中时返回 `PreToolResult(false, "")`。
- F6: 动作执行器:
 - COMMAND：`ProcessBuilder("bash", "-c", h.action().command())` 启子进程；环境变量注入 `MEWCODE_EVENT` / `MEWCODE_TOOL`；stdout + stderr 同步读取并合并；`waitFor()` 退出码 0 视作 success
 - PROMPT：直接把 `action.message()` 当 output 返回，success = true
 - SCRIPT 及未知 type：返回 `HookResult(id, "Unknown action type: ...", false, false)`
- F7: 数据结构使用 Java record:
 - `Action(ActionType type, String command, String message)`
 - `Hook(String id, EventName event, String condition, Action action, boolean reject)`
 - `HookContext(EventName event, String toolName, Map<String,Object> toolArgs, String filePath, String message, String error)`
 - `HookResult(String hookId, String output, boolean success, boolean reject)`
 - `PreToolResult(boolean rejected, String message)`
- F8: 提供 `loadHooks(List<Hook>)` 替换内部 hooks 列表、`addHook(Hook)` 增量追加；`drainNotifications()` 取走积累的执行结果并清空队列（当前 TUI 未消费，留作后续接入）。
- F9: 配置数据类 `com.mewcode.config.HookConfig`：字段 id / event / condition / type / command / message / reject 用经典 POJO + getter / setter 形式，便于 SnakeYAML 反序列化。
- F10: 入口透传链路：`config.yaml.hooks` → `AppConfig.hooks` → `MewCode.main` 把 `cfg.getHooks()` 传给 `MewCodeModel` 构造函数 → `MewCodeModel` 构造期把 `List<HookConfig>` 翻译成 `List<HookEngine.Hook>` 并 `loadHooks`，agent 初始化路径上调 `agent.setHookEngine(hookEngine)`。

## 4. 非功能需求

- N1: hook 执行不能抛出异常打断 Agent 主流程：command 子进程 `IOException / InterruptedException` 必须被捕获，返回 `success=false` 的 HookResult；condition 解析失败（如正则非法）按「不命中」处理。
- N2: `runCommand` 中断处理：catch `InterruptedException` 时必须调 `Thread.currentThread().interrupt()` 保留中断状态，避免上层虚拟线程丢失取消信号。
- N3: stdout / stderr 必须用 `readAllBytes()` 一次性读完再 `waitFor()`，避免子进程因 stdout 缓冲区满而死锁。
- N4: condition 字符串末尾的引号（`"`、`'`、`/`）必须 strip 后再比较，让 yaml 里写 `tool == "Bash"` 或 `event =~ /session.*/` 都能匹配。
- N5: Engine 状态目前不要求并发安全：hooks 列表只在 TUI 构造期写入、运行期只读；notifications 当前无消费方，并发竞态留待后续接入消费者时再加锁。

## 5. 设计概要

- 核心数据结构:
 - `HookEngine.EventName`：9 个 enum 值 + `value()` 返回 snake_case 字符串
 - `HookEngine.ActionType`：3 个 enum 值（command / script / prompt）
 - 5 个 record（Action / Hook / HookContext / HookResult / PreToolResult）封装数据流
 - `private final List<Hook> hooks`：注册的钩子列表
 - `private final List<HookResult> notifications`：执行结果累计，留给 `drainNotifications` 取
- 主流程:
 1. main 启动 → ConfigLoader 读 yaml → `AppConfig.hooks` 拿到 `List<HookConfig>`
 2. `MewCode.main` 把 `cfg.getHooks()` 透传给 `new MewCodeModel(providers, mcpServers, hooks)`
 3. `MewCodeModel` 构造函数里 `new HookEngine()` + 把 `HookConfig` 翻译成 `HookEngine.Hook` + `loadHooks`
 4. provider 就绪 → `agent.setHookEngine(hookEngine)` + `fireHook(SESSION_START, null, null)`
 5. 用户每次发消息 → `sendUserMessage` / 命令分支调 `fireHook(TURN_START, ...)`
 6. Agent loop 工具调用：`StreamingExecutor.executeSingle` 先 `hookEngine.runPreToolHooks(toolName, args)` → 被阻断时把 `"Rejected by hook: <msg>"` 当 ToolResult 返回；通过后正常执行工具 → 结束调 `hookEngine.runHooks(post_tool_use ctx)`
 7. agent loop 结束 → `LoopComplete` 事件触发 `fireHook(TURN_END, null, null)`
- 调用链（模块层级）:
 - 启动: `MewCode.main` → `MewCodeModel.<init>` → `HookEngine` 初始化 → `loadHooks` 挂到 `MewCodeModel.hookEngine` 字段 → `agent.setHookEngine` 透传到 `Agent.hookEngine`
 - 触发: `Agent.run` → `agentLoop` → `new StreamingExecutor(registry, checker, hookEngine, queue)` → `executeAll` → `executeSingle` → `runPreToolHooks` → `tool.execute` → `runHooks(post_tool_use)`
- 与其他模块的交互:
 - 上行依赖：`com.mewcode.agent`（`Agent` 持引用，`StreamingExecutor` 调用 pre / post 入口）、`com.mewcode.tui.MewCodeModel`（生命周期 + 配置装配）、`com.mewcode.config`（POJO 反序列化）
 - 下行：无（hook 包仅依赖 JDK 标准库）

## 6. Out of Scope

- `agent` 动作类型：依赖 SubAgent 系统，本章不实现，留到 ch13 之后再补
- `http` 动作类型：当前 Java 版没有 HTTP 调用栈也没有响应体大小约束，等业务需要时再加；ActionType 枚举先不引入 HTTP 占位
- `script` 动作类型：虽然枚举里有 SCRIPT，但 `executeAction` 落到 default 分支返回 unknown action type；本章不补 script 执行路径，等场景需要时再补
- `once` / `async` / `on_error` 三种执行控制：当前所有钩子同步执行、每次都触发、出错就当失败处理；不补复杂的 fire-once / 异步 goroutine / 失败回滚语义
- Condition DSL 的 `!=` 反向、`~=` glob、`&&` / `||` 复合表达式：Java 版只实现 `==` 和 `=~` 两种 leaf；多条件需求由用户拆成多个独立 hook 来表达
- 加载期 `Validate`：当前 `loadHooks` 不做合法性校验；非法的 ActionType / EventName 字符串走 `parseEventName` / `parseActionType` 的 default 分支落到 SESSION_START / COMMAND，安静兜底
- Hook 命令的超时：`runCommand` 当前用同步 `waitFor()` 等到底，不带 timeout；长命令需要超时控制时再补 `waitFor(long, TimeUnit)` 或 `destroyForcibly()` 路径
- `drainNotifications` 的消费方：当前 TUI 没有消费 `notifications` 队列，hook 输出不会进入 system reminder；等通知中心模块就绪时再接入
- 缺失事件触发：`SESSION_END` / `PRE_SEND` / `POST_RECEIVE` / `SHUTDOWN` 当前没有 emit 点，等业务场景出现再在 TUI / Agent loop / 进程信号处理器里补 fireHook
- Hook 配置的热更新：必须重启或重新选 provider 才生效

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch12: Hook 系统 Tasks

## T1: 定义事件 / 动作枚举与数据 record

- 影响文件: `src/main/java/com/mewcode/hook/HookEngine.java`
- 依赖任务: 无
- 完成标准: 9 个 `EventName` 枚举（带 `value()` 返回 snake_case 字符串）+ 3 个 `ActionType` 枚举（command / script / prompt）；5 个 record（Action / Hook / HookContext / HookResult / PreToolResult）齐全且字段对齐 Go 版语义。
- 实际产出: `HookEngine.java:12-55`

## T2: Condition DSL —— `==` 与 `=~` leaf 操作符

- 影响文件: `src/main/java/com/mewcode/hook/HookEngine.java`
- 依赖任务: T1
- 完成标准: `evaluateCondition` 支持 `==` 等值匹配和 `=~` 正则匹配；变量解析覆盖 tool / event / file_path / message / `args.<key>`；`stripQuotes` 自动剥离 `"..."` / `'...'` / `/.../` 三种包裹；未识别操作符返回 true（与 Go 版兼容兜底）；正则编译失败时返回 false。
- 实际产出: `HookEngine.java:121-177`（`evaluateCondition` / `resolveVar` / `stripQuotes`）

## T3: Engine 核心 —— `loadHooks` / `addHook` / `runHooks`

- 影响文件: `src/main/java/com/mewcode/hook/HookEngine.java`
- 依赖任务: T1, T2
- 完成标准: `loadHooks(List<Hook>)` 清空旧列表再追加；`addHook(Hook)` 增量追加；`runHooks(HookContext)` 按事件名过滤 + condition 过滤 + 调 `executeAction` + 把结果写入 `notifications` 队列；`drainNotifications()` 取一份快照并清空。
- 实际产出: `HookEngine.java:64-90`（`addHook` / `loadHooks` / `runHooks`）、`HookEngine.java:113-117`（`drainNotifications`）

## T4: Pre-tool 阻断专用入口 `runPreToolHooks`

- 影响文件: `src/main/java/com/mewcode/hook/HookEngine.java`
- 依赖任务: T3
- 完成标准: `runPreToolHooks(String toolName, Map<String,Object> args)` 构造 PRE_TOOL_USE ctx → 按事件 / condition 过滤 → 命中且 `h.reject() == true` 时执行 action 并立即返回 `PreToolResult(true, result.output())`；无 reject 命中时返回 `PreToolResult(false, "")`。
- 实际产出: `HookEngine.java:92-109`

## T5: 两种动作执行器（command / prompt）

- 影响文件: `src/main/java/com/mewcode/hook/HookEngine.java`
- 依赖任务: T3
- 完成标准:
 - `executeAction` 按 ActionType 分发：COMMAND 走 `executeCommand`；PROMPT 直接把 `action.message()` 当 output 返回 `HookResult(id, message, true, reject)`；其余（含 SCRIPT）落 default 分支返回 `HookResult(id, "Unknown action type: ...", false, false)`
 - `executeCommand`：`ProcessBuilder("bash", "-c", command)` 启子进程；环境变量注入 `MEWCODE_EVENT` 和 `MEWCODE_TOOL`；同步读 stdout / stderr 后再 `waitFor()`；stderr 非空时拼到 stdout（两者均非空用换行连接）；退出码 0 视作 success；`IOException` / `InterruptedException` 捕获后返回 `success=false` 的 HookResult，且 `InterruptedException` 分支必须 `Thread.currentThread().interrupt()` 保留中断状态
- 实际产出: `HookEngine.java:181-214`（`executeAction` / `executeCommand`）

## T6: 配置 POJO `HookConfig` 与 `AppConfig.hooks` 绑定

- 影响文件: `src/main/java/com/mewcode/config/HookConfig.java`、`src/main/java/com/mewcode/config/AppConfig.java`
- 依赖任务: T1
- 完成标准:
 - 新建 `HookConfig` POJO，字段 id / event / condition / type / command / message / reject，全部 getter / setter
 - `AppConfig` 新增 `private List<HookConfig> hooks` + getter / setter，让 SnakeYAML 能反序列化 `hooks: [...]` 列表
- 实际产出: `HookConfig.java:1-33`、`AppConfig.java:10`、`AppConfig.java:21-22`

## T7: 入口透传 —— `MewCode.main` 把 hook 列表传给 TUI

- 影响文件: `src/main/java/com/mewcode/MewCode.java`
- 依赖任务: T6
- 完成标准: `MewCode.main` 加载完 `AppConfig` 后，把 `config.getHooks() != null ? config.getHooks() : List.of()` 作为第三个参数传给 `new MewCodeModel(...)`。
- 实际产出: `MewCode.java:35-39`

## T8: TUI 装配 —— `MewCodeModel` 构造 Engine + 翻译 HookConfig

- 影响文件: `src/main/java/com/mewcode/tui/MewCodeModel.java`
- 依赖任务: T1, T6, T7
- 完成标准:
 - `MewCodeModel` 构造函数新增 `List<HookConfig> hookConfigs` 形参，存到字段
 - 构造期 `new HookEngine()`，若 hookConfigs 非空则把每个 HookConfig 翻译成 `HookEngine.Hook` 后 `loadHooks`
 - `parseEventName(String)` / `parseActionType(String)` 静态方法把 yaml 字符串映射到枚举，未知字符串落 default 分支兜底
- 实际产出: `MewCodeModel.java:66`、`MewCodeModel.java:174-205`（构造）、`MewCodeModel.java:208-232`（两个 parse 方法）

## T9: Agent 接入 —— `Agent.hookEngine` 字段 + `StreamingExecutor` 调用

- 影响文件: `src/main/java/com/mewcode/agent/Agent.java`、`src/main/java/com/mewcode/agent/StreamingExecutor.java`、`src/main/java/com/mewcode/tui/MewCodeModel.java`
- 依赖任务: T3, T4, T5, T8
- 完成标准:
 - `Agent` 新增 `private HookEngine hookEngine` 字段 + `setHookEngine` / `getHookEngine` 访问器
 - `Agent.agentLoop` 在每轮工具调用前构造 `new StreamingExecutor(registry, checker, hookEngine, queue)`
 - `StreamingExecutor.executeSingle` 在 tool.execute 之前调 `hookEngine.runPreToolHooks(call.toolName(), call.args())`，rejected 时立即返回 `"Rejected by hook: <msg>"` 当 ToolResult
 - `StreamingExecutor.executeSingle` 在 tool.execute 之后构造 POST_TOOL_USE ctx 调 `hookEngine.runHooks(ctx)`
 - `MewCodeModel` 在 provider 就绪路径调 `agent.setHookEngine(hookEngine)` 并 `fireHook(SESSION_START, null, null)`
- 实际产出: `Agent.java:29`（字段）、`Agent.java:43`/`Agent.java:48`（访问器）、`Agent.java:249`（构造 executor）、`StreamingExecutor.java:27`/`StreamingExecutor.java:33-39`（字段 + 构造）、`StreamingExecutor.java:82-89`（pre）、`StreamingExecutor.java:142-146`（post）、`MewCodeModel.java:502-503`（setHookEngine + SESSION_START）

## T10: 生命周期事件触发 —— `fireHook` 在 turn_start / turn_end 调用

- 影响文件: `src/main/java/com/mewcode/tui/MewCodeModel.java`
- 依赖任务: T9
- 完成标准:
 - 新增 `private void fireHook(EventName event, String toolName, Map<String,Object> args)` 助手方法，hookEngine 为 null 时直接 return；非 null 时构造 ctx 调 `hookEngine.runHooks(ctx)`
 - `TURN_START`：在用户消息提交后、agent 启动前调用（slash command 分支和普通消息分支两处）
 - `TURN_END`：在 `LoopComplete` 事件处理分支调用
- 实际产出: `MewCodeModel.java:949`（slash command 分支）、`MewCodeModel.java:1025`（sendUserMessage 分支）、`MewCodeModel.java:1104`（LoopComplete 分支）、`MewCodeModel.java:1148-1152`（fireHook 实现）

## T11: 端到端验证

- 影响文件: 无
- 依赖任务: T1-T10
- 完成标准: 在项目根目录 `config.yaml` 中配置一条 pre_tool_use reject hook：
 ```yaml
 hooks:
   - id: block-rm
     event: pre_tool_use
     condition: 'tool == Bash'
     type: prompt
     message: "blocked"
     reject: true

 ```

启动 TUI 让 LLM 调用 Bash 工具，看到工具结果是 `Rejected by hook: blocked`，且 ChatMessage 的 toolBlocks 把 isError 标为 true。

- 实际产出: 由人工或集成测试覆盖；手工验证步骤见 checklist §4。

## 进度

- [ ] T1

- [ ] T2

- [ ] T3

- [ ] T4

- [ ] T5

- [ ] T6

- [ ] T7

- [ ] T8

- [ ] T9

- [ ] T10

- [ ] T11
```
```plain
# ch12: Hook 系统 Checklist

## 1. 实现完整性

- [ ] 9 个 `EventName` 枚举在 `src/main/java/com/mewcode/hook/HookEngine.java:12-28`：SESSION_START / SESSION_END / TURN_START / TURN_END / PRE_SEND / POST_RECEIVE / PRE_TOOL_USE / POST_TOOL_USE / SHUTDOWN，每个枚举值 `value()` 返回对应 snake_case 字符串
- [ ] 3 个 `ActionType` 枚举在 `HookEngine.java:32-42`：COMMAND / SCRIPT / PROMPT
- [ ] 5 个 record 在 `HookEngine.java:46-55`：`Action / Hook / HookContext / HookResult / PreToolResult` 字段对齐 spec §3.F7
- [ ] Engine 私有字段 `private final List<Hook> hooks` 与 `private final List<HookResult> notifications` 在 `HookEngine.java:59-60`
- [ ] `addHook(Hook)` 和 `loadHooks(List<Hook>)` 在 `HookEngine.java:64-71`：loadHooks 必须 `hooks.clear()` 后再 `addAll`
- [ ] `runHooks(HookContext)` 在 `HookEngine.java:75-90`：按事件名过滤 → condition 过滤 → 调 `executeAction` → 把 HookResult 追加到 `notifications` 队列
- [ ] `runPreToolHooks(String, Map)` 在 `HookEngine.java:92-109`：构造 PRE_TOOL_USE ctx → 命中 reject 钩子时执行 action 并立即返回 `PreToolResult(true, output)`；无命中返回 `PreToolResult(false, "")`
- [ ] `drainNotifications()` 在 `HookEngine.java:113-117`：返回不可变快照 + 清空内部队列
- [ ] Condition DSL 支持 `==` 与 `=~` 两种 leaf：实现在 `HookEngine.java:121-147`；变量解析在 `HookEngine.java:149-164`；引号剥离在 `HookEngine.java:166-177`
- [ ] 未识别操作符走 `return true` 兜底（`HookEngine.java:146`）；正则编译失败 `PatternSyntaxException` 走 `return false`（`HookEngine.java:140-142`）
- [ ] `executeAction` 在 `HookEngine.java:181-188` 按 ActionType 分发：COMMAND 走 `executeCommand`、PROMPT 走 `new HookResult(id, message, true, reject)`、SCRIPT / 未知走 `"Unknown action type: ..."` 失败结果
- [ ] `executeCommand` 在 `HookEngine.java:190-214`：`ProcessBuilder("bash", "-c", command)` 启子进程；env 注入 `MEWCODE_EVENT` 和 `MEWCODE_TOOL`；stdout / stderr 同步读完后 `waitFor()`；exit code 0 ↔ success；stderr 非空时拼到 stdout（两者均非空用 `\n` 分隔）
- [ ] `executeCommand` 异常分支必须捕获 `IOException | InterruptedException`，且 `InterruptedException` 分支调 `Thread.currentThread().interrupt()` 保留中断状态（`HookEngine.java:208-213`）
- [ ] `HookConfig` POJO 在 `src/main/java/com/mewcode/config/HookConfig.java:1-33`：字段 id / event / condition / type / command / message / reject + 配套 getter / setter

## 2. 接入完整性

- [ ] `grep -rn "new HookEngine" --include="*.java" src/main/java` 命中 `MewCodeModel.java:196` 这条非测试构造点
- [ ] `grep -rn "runPreToolHooks\|runHooks(" --include="*.java" src/main/java | grep -v Test` 命中 `StreamingExecutor.java:83` 与 `StreamingExecutor.java:145` 两个 agent loop 触发点，以及 `MewCodeModel.java:1151` 一个生命周期触发点
- [ ] `grep -rn "setHookEngine\|getHookEngine" --include="*.java" src/main/java | grep -v Test` 至少命中 `MewCodeModel.java:502`（setHookEngine）和 `Agent.java:43`/`Agent.java:48`（访问器声明）
- [ ] Config 绑定：`AppConfig.java:10` 含 `private List<HookConfig> hooks` 字段，`AppConfig.java:21-22` 含 getter / setter
- [ ] 入口透传：`MewCode.java:35-39` 把 `config.getHooks() != null ? config.getHooks() : List.of()` 传给 `MewCodeModel` 第三个参数
- [ ] TUI 装配：`MewCodeModel.java:66`（字段）、`MewCodeModel.java:174-205`（构造函数翻译 HookConfig → HookEngine.Hook 并 loadHooks）
- [ ] `parseEventName / parseActionType` 在 `MewCodeModel.java:208-232`：未知 yaml 字符串落 default 分支兜底到 SESSION_START / COMMAND
- [ ] Agent 字段：`Agent.java:29` 含 `private HookEngine hookEngine`；构造 StreamingExecutor 处 `Agent.java:249` 把 hookEngine 透传
- [ ] StreamingExecutor 字段：`StreamingExecutor.java:27` 含 `private final HookEngine hookEngine`，构造函数 `StreamingExecutor.java:33-39` 接收
- [ ] Pre-tool 调用：`StreamingExecutor.java:82-89` 走 `if (hookEngine != null) { ... }`，rejected 时把 `"Rejected by hook: <msg>"` 当 ToolResult 返回并发出 `AgentEvent.ToolResultEvent`
- [ ] Post-tool 调用：`StreamingExecutor.java:142-146` 在 tool.execute 完成后构造 POST_TOOL_USE ctx 调 `hookEngine.runHooks(ctx)`
- [ ] 生命周期触发：`MewCodeModel.java:1148-1152` 实现 `fireHook` 助手，并在 `MewCodeModel.java:503`（SESSION_START）、`MewCodeModel.java:949` 与 `MewCodeModel.java:1025`（TURN_START）、`MewCodeModel.java:1104`（TURN_END）调用
- [ ] 入口路径：`config.yaml.hooks → AppConfig.hooks → MewCode.main → new MewCodeModel(..., hooks) → MewCodeModel.hookConfigs → new HookEngine + loadHooks → agent.setHookEngine → Agent.hookEngine → StreamingExecutor.executeSingle 调 runPreToolHooks / runHooks`
- [ ] 死代码记录 1：`HookEngine.ActionType.SCRIPT` 当前在 `executeAction` 落 default 分支（永远返回 "Unknown action type"），spec §6 已明示「不实现」；接入前可保留枚举占位、后续接入时单独删除或补 case 分支
- [ ] 死代码记录 2：`HookEngine.drainNotifications` 当前没有非测试消费方，`grep -rn "drainNotifications" --include="*.java" src/main/java | grep -v Test` 应返回 0 条；spec §6 已记录留作后续通知中心模块接入

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && ./gradlew build` 通过
- [ ] `cd /Users/codemelo/mewcode && ./gradlew compileJava` 通过（hook 包被 agent / tui / config 引用）
- [ ] `cd /Users/codemelo/mewcode && ./gradlew test` 通过；若新增 `HookEngineTest`，至少覆盖 condition 解析（== 与 =~）、runPreToolHooks 阻断、runCommand 注入环境变量三类用例
- [ ] `javac -Xlint:all` 或 Gradle build 输出中 `com.mewcode.hook` 与 `StreamingExecutor` 无未检查警告

## 4. 端到端验证

- [ ] 在项目根目录 `config.yaml` 配置一条 pre_tool_use reject hook（参考 tasks.md T11 的 yaml）；启动 TUI 后让 LLM 调用 Bash 工具，看到工具结果文本是 `Rejected by hook: blocked`，且 `ChatMessage.ToolBlockInfo.isError == true`
- [ ] 在 `config.yaml` 配置一条 post_tool_use command hook，命令使用 `MEWCODE_TOOL` 环境变量（如 `echo "tool=$MEWCODE_TOOL" >> /tmp/mewcode-hook.log`）；触发工具调用后查看日志文件包含正确的工具名
- [ ] 测试 condition 正则匹配：配置 `condition: 'tool =~ Bash|Read'`，验证 Bash 和 ReadFile 工具都触发 hook，其他工具不触发
- [ ] 测试 prompt 动作：配置 `type: prompt` + `message: "test message"`，触发后通过 `HookEngine.drainNotifications` 看到 `HookResult.output == "test message"`（需在 TUI 接入消费方或编写直接调 Engine 的单元测试）
- [ ] 测试 condition 引号剥离：`condition: 'tool == "Bash"'`、`condition: "event =~ /session.*/"`、`condition: "tool == 'Bash'"` 三种写法都能正确匹配

## 5. 文档

- [ ] `docs/java/ch12/spec.md` 存在
- [ ] `docs/java/ch12/tasks.md` 存在
- [ ] `docs/java/ch12/checklist.md` 存在
- [ ] commit message 包含章节号 `ch12` 与三件套关闭标记，建议形如 `docs(ch12): close spec/tasks/checklist for hooks system`
```