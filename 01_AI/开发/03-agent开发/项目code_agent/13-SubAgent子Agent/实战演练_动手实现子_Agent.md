# 第13章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装上了 Hook 生命周期钩子系统，Agent 在关键节点上有了可编程的扩展能力。但不管你挂了多少 Hook，干活的还是同一个 Agent。所有任务都塞进同一个对话上下文，上下文越来越长，噪声越来越多，Token 越烧越快。

这一章要解决的就是这个问题：让 MewCode 从单 Agent 进化到能分发任务的多 Agent 架构。做完之后，主 Agent 可以把子任务委派给独立的子 Agent，每个子 Agent 有自己的上下文、工具集和权限边界，干完活把结果交回来就行。

具体要新增这些东西：

-   **Agent 定义与加载** ：AgentDefinition 数据结构、YAML frontmatter + Markdown body 解析、多来源加载器（项目级 > 用户级 > 内置级 > 插件级）
-   **统一 Agent 工具** ：一个 Agent 工具通过 `subagent_type` 参数分流定义式和 Fork 两条路径
-   **Fork 路径** ：继承父 Agent 完整对话历史，利用 prompt cache 降低成本
-   **RunToCompletion** ：子 Agent 的非交互式执行循环
-   **工具过滤多层防线** ：全局禁止 + 自定义限制 + 后台白名单 + 定义层 tools/disallowedTools
-   **TaskManager 后台任务** ：后台启动、自动超时、ESC 手动切换、task-notification 异步回传
-   **父子链路追踪** ：TraceRegistry 记录调用链、Token 消耗、执行状态
-   **Slash 命令** ： `/tasks` 、 `/task info` 、 `/task cancel`
-   **三个内置 Agent** ：Explore（haiku 模型只读探索）、Plan（只读规划）、general-purpose（全能力通用）

这章 **不做** ：Worktree 级文件系统隔离（下一章）、Agent Team 多 Agent 协作编排（后续章节）、Trace 的跨会话持久化。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 把子工作者包装成统一的工具入口：一个工具就够了，通过类型参数选择预定义角色，工具列表保持稳定不随角色增减变化
- 角色用 Markdown + YAML frontmatter 定义（如角色名、用途说明、工具白/黑名单、模型选择、最大轮次、权限模式），加载来源有优先级（项目目录 > 用户级 > 内置 > 插件），同名定义按优先级覆盖
- 两种创建模式并存：定义式（空白对话 + 固定角色，可指定独立模型）；以及 Fork 式（不指定角色时启用，继承父对话历史 + 复用父工具集，让首次 LLM 请求命中 prompt cache）
- 隔离与共享的边界要分清：运行时状态隔离（消息历史、权限审批记录、文件读缓存、token 计数），基础设施共享（LLM 客户端、Hook 引擎、文件系统）
- 子工作者用「跑到底」模式执行：任务直接从参数注入不等用户输入，LLM 不再调任何工具即视为完成，把最后一条文本作为结果返回；Hook 在子工作者中仍然生效
- Fork 路径在第一条用户消息里注入一段强硬指令，覆盖父工作者的默认行为（不能再 fork、不要主动对话、不要请求确认、直接用工具干活、最终报告控制字数并按结构化字段输出）
- 工具过滤的多层防线防嵌套失控：全局禁止列表把工具自身排除（防 A→B→C 链式嵌套），自定义角色额外限制，后台运行的子工作者再叠加更严格的白名单
- 后台运行三种进入路径：调用时显式指定、前台超过时间阈值自动切、用户按 ESC 手动切；Fork 模式强制走后台保证并行；前台→后台移交运行中实例不能杀掉重来
- 后台任务管理器维护任务的状态、结果、token 用量、起止时间；完成后通过结构化通知异步注入主对话，不打断当前对话
- 内置几种常用角色覆盖典型场景（如代码探索 / 计划制定 / 通用全能），其中验证角色用配置开关按需启用；配套斜杠命令让用户查看和管理后台任务（列出、查看详情、终止）
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了，然后让 Claude Code 根据这三份文档进行开发

![](实战演练_动手实现子_Agent-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现子_Agent-2.jpeg)

### 功能验证过程

来验收一下结果

我们现在先看内置的子Agent，包括有Explore（探索专家）、Plan（架构师）、general-purpose（通用）

![](实战演练_动手实现子_Agent-3.jpeg)

然后我们现在试试这些子Agent，先试试Explore Agent，来搜索，我们输入

用子Agent搜一下项目里有哪些 Go 文件

![](实战演练_动手实现子_Agent-4.jpeg)

然后MewCode就会调用Explore Agent去探索，我们只需要等待就可以了

等待一会后，结果就会出来了，可以看到它把当前我们的go文件都一一搜索出来

![](实战演练_动手实现子_Agent-5.jpeg)

如果我们想并行做计划，可以输入

开两个子Agent分别给电商系统做个实施计划、给外卖系统做个实施计划

![](实战演练_动手实现子_Agent-6.jpeg)

等待一会后，就有一个详细的计划出来了

![](实战演练_动手实现子_Agent-7.jpeg)

这也是子Agent的核心价值之一，不需要说我们等完一个执行，才能再等另一个，同时这些子Agent之间不会互相干扰，导致明明写电商系统混进了外卖系统的东西，或者是外卖系统混进了电商系统的东西

我们再试试自定义的Agent，比如我们的自定义个安全审查子Agent

```plain
---
name: security-reviewer
description: 代码安全审查专家。识别注入、敏感信息泄露、输入校验缺失、权限越界等漏洞，按严重程度分级输出。只读，不修改任何文件。
model: sonnet
maxTurns: 20
permissionMode: bypassPermissions
disallowedTools:
  - Agent
  - EditFile
  - WriteFile
  - Bash
---

你是一个专注于代码安全审查的 Agent，只读模式。

## 职责
- 检查代码中的安全漏洞（SQL / 命令 / 路径注入、XSS、SSRF、反序列化、不安全的反射等）
- 识别硬编码密钥、token、密码、内网地址、调试后门等敏感信息泄露风险
- 评估输入校验、输出编码、错误处理是否完整
- 检查权限边界（越权读 / 写、不必要的 admin 调用、缺失的 auth check）
- 检查依赖与上游（老旧库、known CVE 的版本、不可信来源）
- 检查并发与资源（race condition、未释放的句柄、可被拖垮的无界循环 / 队列）

## 工具用法
- 用 Grep / Glob 定位可疑模式（`os/exec`、`Sprintf` 拼 SQL / URL、`http.Get(userInput)`、`json.Unmarshal` 到 interface 等）
- 用 ReadFile 精读上下文，不要凭文件名或一行 grep 结果猜测
- 不修改任何文件，不执行任何命令

## 输出格式
每条发现按以下结构：

### [SEVERITY] 标题
- **位置**: `path/to/file.go:行号`
- **问题**: 一句话说明漏洞
- **触发条件**: 怎样的输入 / 调用路径能利用
- **修复建议**: 具体改法，必要时贴改后的代码片段

severity 三档：

- `HIGH`：可被远程利用、能拿到敏感数据 / 能执行任意代码 / 能绕过认证
- `MEDIUM`：需要一定条件才能利用，或后果可控但确实是漏洞
- `LOW`：硬编码默认值、缺失日志、注释里的 TODO 等卫生问题

报告末尾按 severity 汇总数量，并列出"建议人工复审"的区域（你扫过但不确定的部分）。

如果没发现问题，明确说"未发现已知模式的漏洞，建议人工复审 X / Y 区域"，不要硬凑。
```

我们在.mewcode/agents/security-reviewer.md里定义就好，然后打开MewCode，问问有啥子Agent

![](实战演练_动手实现子_Agent-8.jpeg)

可以看到，我们的自定义Agent已经注册成功，我们来试试

帮我用 security-reviewer子Agent 看一下 internal/permissions/permissions.go

![](实战演练_动手实现子_Agent-9.jpeg)

nice，可以正常工作

验收没问题，那么本章的主要任务就完成了。

可能你会注意到我们的子Agent会有些问题，如果是共同修改文件冲突了怎么办？

下一章，我们用 Git Worktree 实现文件系统级别的隔离，让多个子 Agent 可以同时修改代码而不冲突。

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

提示词如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch13: SubAgent Spec

## 1. 背景

主 Agent 做大任务时会塞满上下文：研究、规划、写代码、跑测试都堆在一个对话里，单一窗口很快耗尽。这一章把"开一个上下文隔离的新 Agent 去做一件事"做成主 Agent 可以直接调用的工具，让主 Agent 学会分发工作，避免上下文爆炸，同时通过专门角色（plan / explore）和后台异步执行扩展并发能力。

## 2. 目标

提供 `Agent` 工具，主 Agent 在对话里写一次工具调用即可：1) 按 `subagent_type` 启动一个定义式专家子 Agent（系统提示词、模型、工具白名单都按 Markdown 定义文件来），2) 不带 `subagent_type` 时直接 fork 当前对话上下文跑一个临时子 Agent，3) 带 `team_name` 时把这个 spawn 注册成长期团队成员（衔接 ch15）。后台任务的完成通过 `<task-notification>` 反馈给主 Agent。

## 3. 功能需求

- F1: `AgentTool` 实现 `tools.Tool` 接口，注册到主 Agent 的 registry，被 LLM 当成普通工具调用。
- F2: 三档内建 Agent 类型 `general-purpose` / `plan` / `explore`，每档可定制工具黑名单、最大轮数、模型、系统提示词覆盖。
- F3: 支持从用户级目录和项目级 `.mewcode/agents/*.md` 加载自定义 Agent 定义，项目级覆盖用户级覆盖 builtin；Markdown frontmatter 解析为 `AgentDefinition`。
- F4: 三种执行路径：sync（前台阻塞、流式回写 LLM）/ async（后台任务、立即返回任务 ID）/ fork（fork 父对话上下文，强制后台）。
- F5: `TaskManager` 跟踪后台子 Agent 生命周期（pending/running/completed/failed/cancelled），完成时把通知写进队列，主 Agent 下一轮通过 drain 拿到 `<task-notification>` 系统提示。
- F6: 四层工具过滤：全局禁（`Agent` / `AskUserQuestion` 防递归）、custom agent 额外禁、async 白名单（仅常用读写 / 搜索 / Bash / ToolSearch）、definition 级黑名单；MCP 工具一律放行。
- F7: Fork 路径：构造完整 forked conversation（拷贝父消息 + 给悬挂的 `tool_use` 补 placeholder `tool_result`），追加 fork boilerplate 系统约束 + 任务文本；fork-of-fork 通过扫描父对话标签拒绝。
- F8: 可选 worktree 隔离与 `WorktreeMgr` 配合，子 Agent 在临时 git worktree 中跑；执行结束按是否检测到变更决定保留 / 清理。
- F9: 可选团队模式与 `TeamMgr` 配合，走 teammate spawn 路径注册长期团队成员（详见 ch15）。
- F10: 父 Agent 取消（ESC）时可把当前正在跑的对话挂到后台任务上继续执行，主流程不阻塞。
- F11: `Agent` 工具入口额外支持 `mode`（运行时权限模式覆盖）与 `cwd`（工作目录覆盖）参数；`cwd` 与 `isolation: worktree` 互斥；`mode` 走权限模式白名单校验。
- F12: 子 Agent 定义可声明 `background: true` 强制后台运行，与调用侧 `run_in_background` 等价但写在 Markdown 定义里。
- F13: 提供可选的 verification 内置角色（找最后 20% bug），由环境变量守开关；默认不出现在 Agent 列表里。
- F14: Fork 子 Agent 的工具池完全继承父池，让 API 请求前缀字节级一致以命中 prompt cache；嵌套 fork 通过双保险检测（query-source 标记 + 父对话消息扫描）阻止。
- F15: Fork 复制父对话时保留 thinking blocks，保证 assistant 消息形状与父侧字节级一致。
- F16: 子 Agent 接受 spec 级 `permissionMode` 覆盖，运行时用独立的权限 Checker（与父共享 sandbox / rule engine，仅 Mode 替换）。
- F17: 子 Agent spec 支持 `initialPrompt`，在第一轮用户消息之前注入，作为子 Agent 的启动指引。

## 4. 非功能需求

- N1: 子 Agent 不能再调 `Agent` 工具（防止无限递归 / 上下文爆炸），任意层级的子 Agent 都通过全局黑名单屏蔽。
- N2: 后台 Agent 通过取消上下文受控；取消调用后状态置为 cancelled。
- N3: `TaskManager` 所有公共方法并发安全（fork goroutine 与主线程 Drain 同时操作 map）。
- N4: fork 操作必须先在父对话里搜 boilerplate 标签拒绝嵌套 fork。
- N5: Sync 路径要走子 Agent 的完整事件流（文本 / 工具结果 / 错误），不丢消息；工具结果事件单独转发 progress 给 UI。
- N6: Fork 子 Agent 必须复用父池工具与对话内容（含 thinking blocks），让请求前缀字节级一致；任何过滤都会破坏 prompt cache 命中。
- N7: 子 Agent 的权限 Checker 必须独立实例，不能直接共享父引用——`permissionMode` 覆盖时不允许污染父的权限状态。
- N8: 子 Agent 定义 frontmatter 接受的字段集合需在解析层完整保留；未来章节（hooks / mcpServers / skills / memory 等）的字段必须在解析层先存得下，避免重复迁移。

## 5. 设计概要

- 核心数据结构:
 - `AgentTool`：承载 Client / ModelResolver / Registry / Protocol / TaskMgr / ProgressCh / Loader / Conversation / WorktreeMgr / TeamMgr / ParentChecker / QuerySource 等运行时依赖。
 - `AgentDefinition`：Markdown frontmatter 解出来的 spec，含核心字段（agent type / description / tools / disallowedTools / model / maxTurns）+ 扩展字段（permissionMode / background / isolation / memory / effort / initialPrompt / omitMewcodeMd / skills / mcpServers / requiredMcpServers / hooks）。
 - `SubAgentSpec`：运行时归一化的子 Agent 描述，由 `AgentDefinition` 转换得到，扩展字段透传供后续章节消费。
 - `TaskManager` / `Task` / `TaskNotification`：后台任务的状态机 + 通知队列。
 - `BuiltinSpecs`：三档内建定义 `general-purpose / plan / explore`，`plan` 带 plan 专用系统提示词；可选第四档 `verification`（env var 守）。
 - 工具过滤层：四张 map 控制六层过滤（MCP 豁免 → 全局禁用 → 自定义额外禁用 → 异步白名单 + in-process teammate 特例 → 定义级黑名单 → 定义级白名单）。
- 主流程:
 - 同步：用户消息 → 主 Agent → LLM 输出 `Agent` 工具调用 → `AgentTool.Execute` → 解析 `subagent_type` → 工具过滤 → 创建子 Agent → 执行 → 事件流回写 UI / progress channel → 返回结果。
 - 异步：同上但创建后台 task，立即返回任务 ID，后台 goroutine 完成时写通知，主 Agent 下一轮抽 `<task-notification>` 注入。
 - Fork：双保险检测拒绝嵌套（QuerySource 标记 + 父对话消息扫）→ 拷贝父对话（含 thinking blocks，保 byte-exact）→ 给悬挂 `tool_use` 补 placeholder → 追加 fork boilerplate → 工具池整体克隆父池（Agent 工具实例改写 QuerySource） → 始终后台 → 完成走通知。
 - 团队成员：校验 team 存在、name 不重 → 解析 spec → 可选 worktree → 通过 teams 模块 spawn → 立即返回（不阻塞 Lead）。
- 调用链（模块层级）:
 - TUI 装配 → 在 agent tool 注册环节把 `AgentTool` 注册进 registry；主 Agent Checker 构造完后回填 `AgentTool.ParentChecker`，让子 Agent 能派生独立 Checker
 - Agent loop → `NotificationFn` 抽取 → TUI 绑定 drain → `TaskManager.DrainNotifications`
 - TUI ESC → `TaskManager.AdoptRunning` 把当前对话挂为后台任务
 - 子 Agent spawn 时：spec.PermissionMode 走 `deriveSubAgentChecker` 派生（与父共享 sandbox / rule engine），spec.InitialPrompt 走第一轮 user message 之前注入
- 与其他模块的交互:
 - 依赖 `internal/agent`（创建子 Agent）、`internal/conversation`（forked 对话）、`internal/tools`（注册中心 + 过滤）、`internal/llm`（model resolver）、`internal/worktree`（隔离）、`internal/teams`（团队成员）
 - 被 `internal/tui` 和 `cmd/mewcode` 调用

## 6. Out of Scope

- 子 Agent 输出全在内存事件流里，不落盘 task 输出文件
- 不实现 RemoteAgent / DreamTask / LocalWorkflow / MonitorMcp 这些 TaskType
- 不实现 fork 路径的 worktree notice（仅主线 isolation 支持）
- 不接入 plugin / flag / managed 加载源（只支持 built-in / user / project）
- 不消费 `skills` / `hooks` / `mcpServers` / `memory` / `omitMewcodeMd` 等字段——仅在解析层保留，运行时落地留给 ch11 / ch12 / ch07 / ch09 各自接入
- 不实现 PermissionMode 的 bubble / auto 模式
- 不实现 120s 自动超时切后台 / ESC 切后台 / 持久化后台恢复
- 不实现 `isolation: remote` 远端 CCR 运行后端
- 不内置 Statusline-Setup / Code-Guide 等非核心 Agent

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch13: SubAgent Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 `SubAgentSpec` 与三档 builtin
- 影响文件: `internal/agents/subagent.go`（`SubAgentSpec` @ 180-187；`planAgentSystemPrompt` @ 189-222；`BuiltinSpecs` @ 224-244）
- 依赖任务: 无
- 完成标准: `BuiltinSpecs["general-purpose" | "plan" | "explore"]` 三项齐全；`plan` 设置 `DisallowedTools=["EditFile","WriteFile"]`、`MaxTurns=15`；`explore` 设置 `MaxTurns=30`、`Model="haiku"`。
- [ ] 完成

## T2: 实现 `AgentDefinition` 与 Markdown 解析
- 影响文件: `internal/agents/definition.go`（`AgentDefinition` @ 11-20；`ParseAgentFile` @ 22-57；`ToSpec` @ 59-68）
- 依赖任务: T1
- 完成标准: `ParseAgentFile` 能解析 `---\nname:...\ndescription:...\n---\nBody` 形式；缺 `name` / `description` 报错；非法 `model` 报错（限 haiku/sonnet/opus/inherit/空）。
- [ ] 完成

## T3: 实现 `AgentLoader`，按 builtin → user → project 顺序加载
- 影响文件: `internal/agents/loader.go`（`AgentLoader` @ 10-13；`LoadAll` @ 22-45；`loadDir` @ 47-64；`Get` @ 66-68；`ListNames` @ 70-77）
- 依赖任务: T2
- 完成标准: `LoadAll` 先注入 `BuiltinSpecs`，再 `~/.mewcode/agents/*.md`（source=user），最后 `<wd>/.mewcode/agents/*.md`（source=project）；同名后注册覆盖前者。
- [ ] 完成

## T4: 实现四层工具过滤 `FilterToolsForAgentEx`
- 影响文件: `internal/agents/tool_filter.go`（`AllAgentDisallowedTools` @ 9；`CustomAgentDisallowedTools` @ 14；`AsyncAgentAllowedTools` @ 20；`FilterToolsForAgent` @ 34；`FilterToolsForAgentEx` @ 38-76；`IsMCPTool` @ 30-32）
- 依赖任务: 无
- 完成标准: `Agent` / `AskUserQuestion` 一律去除；`isAsync=true` 时仅保留白名单；MCP 工具（`mcp__` 前缀）一律放行；definition 级 `DisallowedTools` 生效。
- [ ] 完成（测试覆盖 `tool_filter_test.go` 全部分支）

## T5: 实现 `TaskManager` 状态机 + 通知队列
- 影响文件: `internal/agents/subagent.go`（`TaskStatus` @ 16-24；`Task` @ 26-35；`TaskManager` @ 37-49；`CreateTask/SetRunning/SetCompleted/SetFailed/DrainNotifications/AdoptRunning/FindByName/CancelTask` @ 57-178）
- 依赖任务: 无
- 完成标准: 状态机覆盖 pending/running/completed/failed/cancelled；完成 / 失败时把 `TaskNotification` 入队；`DrainNotifications` 一次性取出并清空；`AdoptRunning` 把已经在跑的 channel 挂为后台任务。
- [ ] 完成

## T6: 实现 `SpawnSubAgent`（后台异步路径）
- 影响文件: `internal/agents/subagent.go`（`SpawnSubAgent` @ 246-293）
- 依赖任务: T1, T4, T5
- 完成标准: 函数返回 `task_N` 字符串；内部 `FilterToolsForAgent(reg, spec.DisallowedTools, isAsync=true)`；用独立 `context.WithCancel`；事件循环里 ErrorEvent → `SetFailed`，正常退出 → `SetCompleted`。
- [ ] 完成

## T7: 实现 `AgentTool.Execute` 五条分支
- 影响文件: `internal/agents/agent_tool.go`（`AgentTool` @ 48-59；`Schema` @ 87-138；`Execute` @ 156-211）
- 依赖任务: T1, T3, T4, T5, T6
- 完成标准: Execute 按 `team_name → subagent_type=="" → runInBackground → 默认同步` 顺序分发；schema 通过 `Loader.ListNames` 动态枚举 `subagent_type`；缺 `description` / `prompt` 报错。
- [ ] 完成

## T8: 实现 `runSync`（前台流式 + 可选 worktree）
- 影响文件: `internal/agents/agent_tool.go`（`runSync` @ 213-315；`selectClient` @ 140-154；`sanitizeSlugSegment` @ 18-32）
- 依赖任务: T7
- 完成标准: 子 Agent `MaxIterations` 走 spec 或 fallback=200；事件流转发 StreamText / ToolResultEvent / ErrorEvent；isolation=worktree 时创建临时分支，结束按 `worktree.DetectChanges` 决定保留 / 移除。
- [ ] 完成

## T9: 实现 `runFork`（fork 父对话）
- 影响文件: `internal/agents/agent_tool.go`（`runFork` @ 317-371；`forkBoilerplate` @ 373-381；`buildForkedConversation` @ 383-414；`ForkBoilerplateTag` @ 46）
- 依赖任务: T4, T5, T7
- 完成标准: 检测父对话里 `<fork_boilerplate>` 标签拒绝嵌套；`buildForkedConversation` 拷贝父消息，给悬挂 `tool_use` 补 `(tool execution interrupted by fork)` 占位 `tool_result`，结尾追加 `forkBoilerplate + "Your task:" + prompt`；fork 始终后台。
- [ ] 完成

## T10: 实现 `runAsync`（builtin spec → 后台）
- 影响文件: `internal/agents/agent_tool.go`（`runAsync` @ 416-426）
- 依赖任务: T6, T7
- 完成标准: 直接调 `SpawnSubAgent`，返回 `Agent "..." launched in background (task task_N).` 文案。
- [ ] 完成

## T11: 实现 `runAsTeammate`（团队成员路径，衔接 ch15）
- 影响文件: `internal/agents/agent_tool.go`（`runAsTeammate` @ 438-533；`drainTeammateEvents` @ 538-561）
- 依赖任务: T7（ch15 的 `teams.SpawnTeammate`）
- 完成标准: 校验 team 存在；同 team 内重名报错；isolation=worktree 时建 `team-<team>-<member>-<ts>` 分支；调 `teams.SpawnTeammate` 拿回 backend hint；in-process 模式启动 goroutine `drainTeammateEvents` 防止生产者阻塞。
- [ ] 完成

## T12: 接入主流程
- 影响文件: `internal/tui/tui.go`（`subAgentProgressCh` @ 166；`taskMgr` @ 179；`registerAgentTools` @ 519-556；`drainTaskNotifications` @ 486-499；`AdoptRunning` 调用 @ 777）
- 依赖任务: T1-T11
- 完成标准:
 1. `m.registry.Register(&agents.AgentTool{...})` 在 `registerAgentTools` 注册；
 2. `ag.NotificationFn = m.drainTaskNotifications` 在 init 时挂上（`tui.go:369`）；
 3. ESC 中断时调 `taskMgr.AdoptRunning` 把当前 stream 转后台（`tui.go:777`）；
 4. progress channel 由 TUI 的 `listenForSubAgentProgress` 消费。
- [ ] 完成

## T13: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T12
- 完成标准:
 - `go build ./...` 通过（已验证，输出为空）；
 - `go test ./internal/agents/...` 全部测试通过（loader_test.go 5 个 + tool_filter_test.go 6 个测试）；
 - 端到端路径已通过现有测试覆盖：Markdown 解析、builtin / project 覆盖、四层过滤的全部分支。
- [ ] 完成

---

> **二批：重构 SubAgent 模块。

## T14: 工具过滤常量重构 + In-process Teammate 特例
- 影响文件: `internal/agents/tool_filter.go`（六层过滤、四张常量集合、`FilterToolsForAgentEx` 多 `isInProcessTeammate` 参数），`internal/agents/tool_filter_test.go` 补三个回归用例。
- 依赖任务: T4
- 完成标准:
 - `AllAgentDisallowedTools` 含 `TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow` 七项；
 - `AsyncAgentAllowedTools` 含原 7 项 + `WebSearch / WebFetch / TodoWrite / NotebookEdit / Skill / SyntheticOutput / EnterWorktree / ExitWorktree`；
 - 新增 `InProcessTeammateAllowedTools`（含 `TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage`，可选 Cron 三件）；
 - 异步白名单层在 `isInProcessTeammate=true` 时额外放行 `Agent` + 队友工具。
- [ ] 完成

## T15: AgentDefinition 17 字段扩展 + SubAgentSpec 透传
- 影响文件: `internal/agents/definition.go`（新增 `permissionMode / effort / skills / mcpServers / requiredMcpServers / hooks / memory / background / isolation / initialPrompt / omitMewcodeMd` 字段 + 三个枚举校验 + `HasRequiredMcpServers`），`internal/agents/subagent.go`（`SubAgentSpec` 同步新增字段并由 `ToSpec` 透传），`internal/agents/loader_test.go` 补字段解析测试。
- 依赖任务: T2、T3
- 完成标准:
 - frontmatter 解析含 17 个字段，必填只有 `name / description`；
 - `permissionMode` 接受 `default / acceptEdits / plan / bypassPermissions`，非法值报错；
 - `memory` 接受 `user / project / local` 三档；
 - `isolation` 接受 `worktree / remote`；
 - `HasRequiredMcpServers` case-insensitive substring 匹配，缺一返 false。
- [ ] 完成

## T16: AgentTool 入口 mode/cwd 参数 + spec.Background 强制后台
- 影响文件: `internal/agents/agent_tool.go`（`Schema` 加 `mode / cwd` 字段、`Execute` 解析两个参数并做互斥校验、定义级 `Background == true` 走 `runAsync`），`internal/agents/agent_tool_test.go` 加校验测试。
- 依赖任务: T7
- 完成标准:
 - schema 新增 `mode`（5 值枚举）/ `cwd`（绝对路径）；
 - `mode` 调用级覆盖 `spec.PermissionMode`；
 - `cwd` 覆盖子 Agent `WorkDir`，且与 `isolation: worktree` 提前互斥校验；
 - `spec.Background` 或调用级 `run_in_background` 任一为 true 即走 `runAsync`。
- [ ] 完成

## T17: 新增 verification 内置 Agent + env var 守
- 影响文件: `internal/agents/verification_prompt.go`（4500+ 字 system prompt + Spec），`internal/agents/loader.go`（`getBuiltinSpecs` 按 env var 决定是否包含）。
- 依赖任务: T1、T3
- 完成标准:
 - 设 `MEWCODE_VERIFICATION_AGENT=true` 时 `verification` 出现在 `loader.ListNames()` 里；
 - 不设时不出现；
 - 该 spec `Background=true`，disallowedTools 含 `Agent / ExitPlanMode / EditFile / WriteFile / NotebookEdit`；
 - system prompt 含 "VERIFICATION-ONLY" 与 "VERDICT: PASS / FAIL / PARTIAL" 文本。
- [ ] 完成

## T18: Fork 模式三项重构（useExactTools / 双保险 / byte-exact thinking blocks）
- 影响文件: `internal/agents/agent_tool.go`（`AgentTool.QuerySource` 字段、`runFork` 入口两层检查、`cloneRegistryForFork`、`buildForkedConversation` 改用 `AddAssistantFull` 保留 thinking blocks），`internal/agents/agent_tool_test.go` 三个 fork 测试。
- 依赖任务: T9
- 完成标准:
 - `ForkQuerySource = "agent:builtin:fork"`；当 `t.QuerySource == ForkQuerySource` 时 `runFork` 直接拒绝；
 - `cloneRegistryForFork` 复制父池所有工具，仅替换 `*AgentTool` 实例并设 `QuerySource = ForkQuerySource`；
 - `buildForkedConversation` 对所有 assistant 消息调 `AddAssistantFull(text, thinkingBlocks, toolUses)`，保留父侧 thinking blocks；
 - 嵌套 Fork 两条路径都拒（QuerySource 命中 / 消息扫到 `ForkBoilerplateTag`）。
- [ ] 完成

## T19: 子 Agent 权限注入 + initialPrompt 第一轮注入
- 影响文件: `internal/agents/agent_tool.go`（`ParentChecker` 字段、`deriveSubAgentChecker`、`runSync` / `runFork` / `runAsync` 三条路径注入 Checker，runSync 注入 `spec.InitialPrompt`），`internal/agents/subagent.go`（`SpawnSubAgent` 加 `parentChecker` 参数 + 注入 InitialPrompt），`internal/tui/tui.go`（两处主 Agent Checker 构造之后回填到 `AgentTool.ParentChecker`），`internal/agents/agent_tool_test.go` 补 `deriveSubAgentChecker` 测试。
- 依赖任务: T8、T10、T12
- 完成标准:
 - `deriveSubAgentChecker(nil, *)` 返回 nil；
 - `deriveSubAgentChecker(parent, "")` 返回父引用本身；
 - `deriveSubAgentChecker(parent, "plan")` 返回新实例，与父共享 Sandbox / RuleEngine，Mode 为 `ModePlan`；
 - sync/fork/async 三条路径都设了 `subAgent.Checker`；
 - `spec.InitialPrompt != ""` 时子 Agent 的 conversation 在用户 prompt 之前先 `AddUserMessage(initialPrompt)`；
 - TUI 在 `m.ag.Checker` 构造完之后把 ParentChecker 回填到 registry 里的 `AgentTool` 实例。
- [ ] 完成

## T20: 重构端到端验证
- 影响文件: 无（仅运行）
- 依赖任务: T14-T19
- 完成标准:
 - `go build ./...` 通过；
 - `go test ./...` 全 17 个包通过，含 9 个新回归用例：`TestGlobalDisallowedExpanded` / `TestAsyncWhitelistExpanded` / `TestInProcessTeammateExtraTools` / `TestParseAgentDefinitionExtendedFields` / `TestParseAgentInvalidPermissionMode` / `TestHasRequiredMcpServers` / `TestRunForkRejectedWhenQuerySourceIsFork` / `TestRunForkRejectedWhenBoilerplateInHistory` / `TestCloneRegistryForForkSetsQuerySource` / `TestExecuteValidatesModeAndCwdExclusivity` / `TestBuildForkedConversationPreservesThinkingBlocks` / `TestDeriveSubAgentCheckerOverrideMode`。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15 / [ ] T16 / [ ] T17 / [ ] T18 / [ ] T19 / [ ] T20
```
```plain
# ch13: SubAgent Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 类型 `AgentTool` 在 `internal/agents/agent_tool.go:48-59` 存在，字段含 `Client / Registry / Loader / TaskMgr / Conversation / WorktreeMgr / TeamMgr`
- [ ] 类型 `AgentDefinition` 在 `internal/agents/definition.go:11-20` 存在，五个 yaml 字段（`name / description / disallowedTools / model / maxTurns`）齐全
- [ ] 类型 `SubAgentSpec` 在 `internal/agents/subagent.go:180-187` 存在
- [ ] 类型 `TaskManager` / `Task` / `TaskNotification` 在 `internal/agents/subagent.go:37/26/44` 存在，含状态机字段
- [ ] `BuiltinSpecs` 在 `internal/agents/subagent.go:224-244` 注册三档（`general-purpose / plan / explore`）
- [ ] `FilterToolsForAgentEx` 在 `internal/agents/tool_filter.go:38-76` 实现四层过滤
- [ ] `ParseAgentFile` 在 `internal/agents/definition.go:22-57` 验证 `name` / `description` 必填，`model` 取值白名单
- [ ] `runFork` 在 `internal/agents/agent_tool.go:317-371` 嵌套 fork 检查（扫描 `<fork_boilerplate>` 标签）
- [ ] `buildForkedConversation` 在 `internal/agents/agent_tool.go:383-414` 给悬挂 `tool_use` 补占位 `tool_result`
- [ ] 错误消息 `"Error: cannot fork from a forked agent"` 在 `agent_tool.go:326` 与 原始定义 的 `isInForkChild` 语义一致

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -r "AgentTool" --include="*.go" /Users/codemelo/mewcode` 在 `internal/tui/tui.go:544` 找到注册调用方
- [ ] `m.registry.Register(&agents.AgentTool{...})` 调用点在主流程 `registerAgentTools` (`internal/tui/tui.go:519-556`)，所有依赖（Client/ModelResolver/Registry/Protocol/TaskMgr/ProgressCh/Loader/Conversation/TeamMgr/WorktreeMgr）齐全注入
- [ ] `AgentLoader.LoadAll` 调用点在 `internal/tui/tui.go:527-528`
- [ ] `TaskManager.DrainNotifications` 调用点在 `internal/tui/tui.go:489`（通过 `m.drainTaskNotifications`）
- [ ] `TaskManager.AdoptRunning` 调用点在 `internal/tui/tui.go:777`（ESC 触发的后台挂载）
- [ ] `NotificationFn` 绑定点在 `internal/tui/tui.go:369` 和 `:731`（initSingleProviderMsg + 恢复会话）
- [ ] `ProgressCh` 由 `internal/tui/tui.go:211` 创建并通过 `subAgentProgressMsg` 在事件循环 `:275-298` 消费
- [ ] Schema 暴露：`Agent` 工具通过 `AgentTool.Schema` 注册到 registry，TUI 的 `tools.ToolSearchTool` 可发现它

## 3. 编译与测试

- [ ] `go build ./...` 通过（已运行，无输出）
- [ ] `go test ./internal/agents/...` 通过（`loader_test.go` 5 个 case + `tool_filter_test.go` 6 个 case 全部 PASS）
- [ ] `go vet ./...` 无警告

## 4. 端到端验证

- [ ] 注册路径：在 TUI 启动后 `registerAgentTools` 把 `Agent` 工具放入 registry（`tui.go:544`）；用户向主 Agent 发送 "spawn a plan agent to review X" → LLM 返回 `Agent` 工具调用 → `Execute` → `runSync(spec=plan)` → 子 Agent 流式输出。
- [ ] Fork 路径：用户在对话进行中说 "fork to investigate Y" → LLM 调用 `Agent` 不带 `subagent_type` → `runFork` → forked conversation 启动后台 task → 完成时 `<task-notification>` 通过 `drainTaskNotifications` 注入下一轮（`tui.go:486-499`）
- [ ] ESC 挂后台路径：用户按 ESC 中断 → `tui.go:776-777` 调 `taskMgr.AdoptRunning` → 当前 stream 转入后台 task，UI 显示 "Agent moved to background (task task_N)"
- [ ] 证据：单元测试 + grep 调用方 + 主流程文件行号已列出。源代码 commit a84e3ba / 3676328 / 24e0323 已包含全部实现。

## 5. 文档

- [ ] `specs/go/ch13/spec.md` 已写
- [ ] `specs/go/ch13/tasks.md` 已写，20 个 T 全部勾完（T1-T13 初版骨架 + T14-T20 重构）
- [ ] `specs/go/ch13/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch13` 与三件套关闭状态（待用户确认后由人或 CI 触发）

---

## 6. 工具改造（T14-T20）

### 7.1 工具过滤常量重构（T14）

- [ ] `AllAgentDisallowedTools` 在 `internal/agents/tool_filter.go` 含七项：`TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow`
- [ ] `AsyncAgentAllowedTools` 含 16 项：`ReadFile / WebSearch / TodoWrite / Grep / WebFetch / Glob / Bash / EditFile / WriteFile / NotebookEdit / Skill / LoadSkill / SyntheticOutput / ToolSearch / EnterWorktree / ExitWorktree`
- [ ] 新增 `InProcessTeammateAllowedTools` 含 `TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage / CronCreate / CronDelete / CronList`
- [ ] `FilterToolsForAgentEx` 签名新增 `isInProcessTeammate bool` 参数（共 6 个参数），队友模式在异步白名单层额外允许 `Agent` + 队友工具
- [ ] 测试：`TestGlobalDisallowedExpanded` / `TestAsyncWhitelistExpanded` / `TestInProcessTeammateExtraTools` 全部 PASS

### 7.2 AgentDefinition 17 字段扩展（T15）

- [ ] `AgentDefinition` 含 17 个字段：核心 6 项 + 扩展 `permissionMode / effort / skills / mcpServers / requiredMcpServers / hooks / memory / background / isolation / initialPrompt / omitMewcodeMd`
- [ ] `ParseAgentFile` 校验 `permissionMode` 取值 ∈ `{"" / default / acceptEdits / plan / bypassPermissions}`，其他值报错
- [ ] `ParseAgentFile` 校验 `memory` 取值 ∈ `{"" / user / project / local}`
- [ ] `ParseAgentFile` 校验 `isolation` 取值 ∈ `{"" / worktree / remote}`
- [ ] `HasRequiredMcpServers` case-insensitive substring 匹配；缺任一返 false；无要求返 true
- [ ] `SubAgentSpec` 新增字段：`PermissionMode / Background / Isolation / InitialPrompt / OmitMewcodeMd / Skills / Memory / McpServers / RequiredMcpServers / Hooks / Effort`
- [ ] `ToSpec()` 透传所有新增字段
- [ ] 测试：`TestParseAgentDefinitionExtendedFields` / `TestParseAgentInvalidPermissionMode` / `TestHasRequiredMcpServers` PASS

### 7.3 AgentTool 入口 mode/cwd + Background 路由（T16）

- [ ] `Schema` 含 `mode` 字段，枚举 `default / acceptEdits / plan / bypassPermissions`
- [ ] `Schema` 含 `cwd` 字段（绝对路径，覆盖工作目录）
- [ ] `Execute` 校验 `cwd != "" && isolation == "worktree"` 返回 `mutually exclusive` 错误
- [ ] `Execute` 校验 `mode` 非法值返回 `invalid mode` 错误
- [ ] 调用级 `mode` 覆盖 `spec.PermissionMode`（per-call 优先级最高）
- [ ] `runSync` 在 isolation 不为 worktree 时若 `cwd != ""` 把子 Agent `WorkDir = cwd`
- [ ] `runInBackground == true || spec.Background == true` 任一为真即走 `runAsync`
- [ ] 测试：`TestExecuteValidatesModeAndCwdExclusivity` PASS

### 7.4 Verification 内置 Agent + env var 守（T17）

- [ ] `verification_prompt.go` 含完整 system prompt（覆盖 "VERIFICATION-ONLY" / "VERDICT: PASS / FAIL / PARTIAL" / "Bad (rejected):" / "Good:" 等关键段落）
- [ ] `verificationSpec` 设 `Background=true`，`DisallowedTools` 含 `Agent / ExitPlanMode / EditFile / WriteFile / NotebookEdit`
- [ ] `verificationSpec.Model == "inherit"`
- [ ] `getBuiltinSpecs()` 按 `os.Getenv("MEWCODE_VERIFICATION_AGENT") == "true"` 决定是否注入 `verification`
- [ ] env var 未设时 `loader.Get("verification") == nil`
- [ ] env var 设为 `true` 时 `loader.ListNames()` 含 `verification`
- [ ] `VerificationAgentType == "verification"`（保持一致 `VERIFICATION_AGENT_TYPE` 常量）

### 7.5 Fork 模式三项重构（T18）

- [ ] `AgentTool.QuerySource` 字段存在；`ForkQuerySource = "agent:builtin:fork"`
- [ ] `ForkAgentType = "fork"`，与 的 `FORK_AGENT.agentType` 一致
- [ ] `runFork` 第一道：`t.QuerySource == ForkQuerySource` 时返回 `cannot fork from a forked agent`
- [ ] `runFork` 第二道：父对话扫到 `<fork_boilerplate>` 也返回同一错误
- [ ] `cloneRegistryForFork` 复制父池全部工具，仅对 `*AgentTool` 实例做 shallow copy 并把 QuerySource 改写为 `ForkQuerySource`
- [ ] `buildForkedConversation` 对带 `tool_use` 的 assistant 消息走 `AddAssistantFull(content, thinkingBlocks, toolUses)`，保留 thinking blocks
- [ ] `buildForkedConversation` 对纯 assistant 消息（无 tool_use）：有 thinking blocks 走 `AddAssistantFull`，无则走 `AddAssistantMessage`
- [ ] 测试：`TestRunForkRejectedWhenQuerySourceIsFork` / `TestRunForkRejectedWhenBoilerplateInHistory` / `TestCloneRegistryForForkSetsQuerySource` / `TestBuildForkedConversationPreservesThinkingBlocks` 全部 PASS

### 7.6 子 Agent 权限注入 + initialPrompt（T19）

- [ ] `AgentTool.ParentChecker *permissions.Checker` 字段存在
- [ ] `deriveSubAgentChecker(nil, anything)` 返回 nil
- [ ] `deriveSubAgentChecker(parent, "")` 返回父引用本身（无新分配）
- [ ] `deriveSubAgentChecker(parent, "plan")` 返回新 Checker：Sandbox / RuleEngine 与父共享，Mode == `permissions.ModePlan`
- [ ] `runSync` 在 `agent.New` 之后调 `deriveSubAgentChecker(t.ParentChecker, spec.PermissionMode)` 注入
- [ ] `runFork` 在 `agent.New` 之后把 `t.ParentChecker` 直接赋给子 Agent（Fork 继承父权限）
- [ ] `SpawnSubAgent` 签名新增 `parentChecker *permissions.Checker` 参数；内部走 `deriveSubAgentChecker`
- [ ] `runSync` / `SpawnSubAgent` 在 `conv.AddUserMessage(taskPrompt)` 之前，当 `spec.InitialPrompt != ""` 时先 `conv.AddUserMessage(spec.InitialPrompt)`
- [ ] TUI 在两处主 Agent Checker 构造之后回填：`if at, ok := m.registry.Get("Agent").(*agents.AgentTool); ok { at.ParentChecker = ag.Checker }`
- [ ] 测试：`TestDeriveSubAgentCheckerOverrideMode` PASS；`ToSpec.InitialPrompt` 透传断言 PASS

### 7.7 重构端到端验证（T20）

- [ ] `go build ./...` 无输出（成功）
- [ ] `go test ./...` 17 个包全部 PASS
- [ ] `go test ./internal/agents/...` 含 9 个新回归用例全 PASS
- [ ] 无新增 `go vet` 警告
- [ ] grep 验证主流程接线：`grep -n "ParentChecker = ag.Checker" internal/tui/tui.go` 应有两处命中（首次启动 + 恢复会话）
```

### Python

```plain
# ch13: SubAgent Spec

## 1. 背景

主 Agent 做大任务时会塞满上下文：研究、规划、写代码、跑测试都堆在一个对话里，单一窗口很快耗尽。这一章把"开一个上下文隔离的新 Agent 去做一件事"做成主 Agent 可以直接调用的工具，让主 Agent 学会分发工作，避免上下文污染，同时通过专门角色（Plan / Explore）和后台异步执行扩展并发能力。

## 2. 目标

提供 `Agent` 工具，主 Agent 在对话里写一次工具调用即可：1) 按 `subagent_type` 启动一个定义式专家子 Agent（系统提示词、模型、工具白名单都按 Markdown 定义文件来），2) 不带 `subagent_type` 且 `enable_fork=true` 时直接 fork 当前对话上下文跑一个临时子 Agent，3) 带 `team_name` 时把这个 spawn 注册成长期团队成员（衔接 ch15）。后台任务的完成通过 `<task-notification>` 反馈给主 Agent。

## 3. 功能需求

- F1: `AgentTool` 继承 `mewcode.tools.base.Tool`，注册到主 Agent 的 `ToolRegistry`，被 LLM 当成普通工具调用。
- F2: 三档内建 Agent 类型 `general-purpose` / `Plan` / `Explore`，每档可定制工具黑名单、最大轮数、模型、系统提示词。
- F3: 支持从用户级目录 `~/.mewcode/agents/*.md` 和项目级 `<work_dir>/.mewcode/agents/*.md` 加载自定义 Agent 定义；项目级覆盖用户级覆盖 builtin；Markdown frontmatter 解析为 `AgentDef`。
- F4: 三种执行路径：sync（前台阻塞、`await sub_agent.run_to_completion()`）/ background（asyncio task，立即返回任务 ID）/ fork（fork 父对话上下文，强制后台）。
- F5: `TaskManager` 跟踪后台子 Agent 生命周期（running / completed / failed / cancelled），完成时把任务 ID 写进 `asyncio.Queue`，主 Agent 下一轮通过 `poll_completed` 拿到，再用 `inject_task_notifications` 拼装 `<task-notification>` 注入对话。
- F6: 四层工具过滤：MCP 直通、全局禁（`ALL_AGENT_DISALLOWED_TOOLS` 七项，含 `Agent` / `AskUserQuestion` 防递归）、custom agent（`source != "builtin"`）额外禁、background 白名单（`ASYNC_AGENT_ALLOWED_TOOLS` 16 项）、definition 级 `disallowed_tools` + `tools` 白名单。
- F7: Fork 路径：构造完整 forked `ConversationManager`（`copy.deepcopy(history)` + 给悬挂的 `tool_use` 补 `"interrupted"` placeholder `ToolResultBlock`），追加 `FORK_BOILERPLATE` + `"你的任务：\n" + task`；fork-of-fork 通过扫描对话历史 `FORK_BOILERPLATE_TAG` 拒绝。
- F8: 可选 worktree 隔离与 `WorktreeManager` 配合，子 Agent 在临时 git worktree 中跑；执行结束按 `auto_cleanup` 返回的 `kept` 标志决定是否在结果里追加 `[Worktree preserved at ...]` 提示。
- F9: 可选团队模式与 `TeamManager` 配合，走 `_execute_as_teammate` 路径注册长期团队成员，按 backend（in-process / tmux / iterm2）路由（详见 ch15）。
- F10: 父 Agent 取消（中断）时，`TaskManager.adopt_running` 把当前正在跑的 Agent 实例挂为后台任务并继续执行，主流程不阻塞。
- F11: `AgentTool` 入口额外支持 `model`（运行时模型覆盖）/ `isolation`（仅 `worktree`）/ `name`（团队场景标识）参数；`isolation` 与 `team_name` 互斥（团队场景走自己的 worktree）。
- F12: 子 Agent 定义 frontmatter 可声明 `background: true` 强制后台运行，与调用侧 `run_in_background=true` 等价。
- F13: 可选 Verification 内置角色（找最后 20% bug），由 `enable_verification` flag 守开关；默认不出现在 Agent 列表里。
- F14: Fork 子 Agent 的工具池继承父池经四层过滤（MCP 直通 + 全局黑 + 白名单 + 定义级），让 API 请求前缀字节级一致以命中 prompt cache；嵌套 fork 通过扫描父对话消息内容 `FORK_BOILERPLATE_TAG` 阻止。
- F15: Fork 复制父对话用 `copy.deepcopy`，保留每条 `Message` 的全部字段（含 `tool_uses` / `tool_results` / `thinking`），保证 assistant 消息形状与父侧一致。
- F16: 子 Agent 接受 spec 级 `permission_mode` 覆盖，运行时用独立的 `PermissionChecker`，与父共享 `DangerousCommandDetector` / `RuleEngine` 类型，但 `PathSandbox` 按子 Agent 的 `work_dir` 重新分配。
- F17: `TraceManager` 给每个 spawn 出来的子 Agent 创建 `TraceNode`，父 / 子 / trace ID 三元组打通，配合 `trace` 命令做调用树查询。

## 4. 非功能需求

- N1: 子 Agent 不能再调 `Agent` 工具（防止无限递归 / 上下文爆炸），任意层级的子 Agent 都通过 `ALL_AGENT_DISALLOWED_TOOLS` 屏蔽。
- N2: 后台 Agent 通过 `asyncio.Task.cancel()` 受控；取消调用后状态置为 `cancelled`。
- N3: `TaskManager` 在 asyncio 单线程模型下顺序安全，`_tasks` / `_async_tasks` / `_notify_queue` 必须在事件循环内访问。
- N4: fork 操作必须先在父对话历史里扫 `FORK_BOILERPLATE_TAG` 字面量，命中即 `raise ForkError`。
- N5: Sync 路径要 `await` 子 Agent 的 `run_to_completion` 直到返回，不丢消息；异常路径要把 `trace_node` 标 `failed` 再向上抛。
- N6: Fork 子 Agent 必须复用父池工具与对话内容（含 thinking blocks），让请求前缀字节级一致；任何额外过滤都会破坏 prompt cache 命中。
- N7: 子 Agent 的 `PermissionChecker` 必须独立实例，不能直接共享父引用，`permission_mode` 覆盖时不允许污染父的权限状态。
- N8: `AgentDef` frontmatter 接受的字段集合在解析层完整保留：未来章节（hooks / mcpServers / skills / memory 等）的字段必须在解析层先存得下，避免重复迁移；当前已落地 `name / description / tools / disallowedTools / model / maxTurns / permissionMode / background / isolation`。

## 5. 设计概要

- 核心数据结构：
  - `AgentTool`：承载 `AgentLoader / TaskManager / TraceManager / parent_agent / provider_config / worktree_manager / team_manager / enable_fork` 等运行时依赖。
  - `AgentDef`：Markdown frontmatter 解出来的 dataclass，含 `agent_type / when_to_use / system_prompt / tools / disallowed_tools / model / max_turns / permission_mode / background / isolation / file_path / source`。
  - `AgentToolParams`：pydantic 模型，对应 `Agent` 工具的入参 schema（`prompt / description / subagent_type / model / run_in_background / name / isolation / team_name`）。
  - `TaskManager` / `BackgroundTask` / `ProgressInfo`：后台任务的状态机 + `asyncio.Queue` 通知。
  - `TraceManager` / `TraceNode`：父子 / trace 三元组追踪，token / 状态 / 时间。
  - 工具过滤层：四张 frozenset 控制四层过滤（MCP 豁免 → 全局禁用 → 自定义额外禁用 → 异步白名单 → 定义级黑名单 + 白名单）。
- 主流程：
  - 同步：用户消息 → 主 Agent → LLM 输出 `Agent` 工具调用 → `AgentTool.execute` → 解析 `subagent_type` → 工具过滤 → 创建 `PermissionChecker` → 实例化 `Agent` 子类 → `await sub_agent.run_to_completion(prompt)` → 返回结果。
  - 异步：同上但 `is_background=True` 走 `TaskManager.launch` 启动 `asyncio.Task`，立即返回任务 ID；任务完成时把 ID 写进 `_notify_queue`，主 Agent 在 `_check_completed_tasks` 通过 `poll_completed` 抽出来再用 `inject_task_notifications` 把 `<task-notification>` 注入下一轮 user message。
  - Fork：扫父对话 `FORK_BOILERPLATE_TAG` 拒绝嵌套 → `copy.deepcopy(history)` 复制父对话（保 byte-exact）→ 给悬挂 `tool_use` 补 `"interrupted"` placeholder `ToolResultBlock` → 追加 `FORK_BOILERPLATE + "\n\n你的任务：\n" + task` → 工具池四层过滤 → 始终后台 → 完成走通知。
  - 团队成员：校验 team 存在 → 同 team 内自动 rename `<base>-<n>` → 解析 spec → 创建 worktree → 检测 backend → 用 `build_teammate_tools` 装配（含 `TaskCreate/TaskGet/TaskList/TaskUpdate/SendMessage` 五件套）→ in-process 走 `task_manager.launch` / pane 走 `spawn_tmux_teammate` 或 `spawn_iterm2_teammate`。
- 调用链（模块层级）：
  - `mewcode.app:737-747` 装配 `AgentTool` 并注册进 `registry`；`app:725-728` 实例化 `AgentLoader` 并加载所有 agents；`app:788` 把 catalog 喂给主 Agent。
  - `app:1275-1279` 在主循环里调 `task_manager.poll_completed` + `inject_task_notifications`，把后台完成的子 Agent 结果灌进对话。
  - `app:1029-1031` 在中断路径调 `task_manager.adopt_running` 把当前正在跑的对话挂为后台任务。
  - `app:790 / 794` 注册 `tasks` / `trace` 两个 slash 命令以便用户主动查看后台任务和追踪树。
- 与其他模块的交互：
  - 依赖 `mewcode.agent`（创建子 Agent）、`mewcode.conversation`（forked 对话）、`mewcode.tools`（注册中心 + 过滤）、`mewcode.client`（model 路由）、`mewcode.permissions`（独立 Checker）、`mewcode.worktree`（隔离）、`mewcode.teams`（团队成员）。
  - 被 `mewcode.app` 和 `mewcode.cli` 调用。

## 6. Out of Scope

- 子 Agent 输出全在内存事件流里，不落盘 task 输出文件。
- 不实现 RemoteAgent / DreamTask / LocalWorkflow / MonitorMcp 这些 TaskType。
- 不实现 fork 路径下的 worktree notice 注入（仅 `_execute_with_worktree` 支持）。
- 不接入 plugin / flag / managed 加载源（`register_plugin_source` 仅保留接口，未实装）。
- 不消费 `skills` / `hooks` / `mcpServers` / `memory` / `omitMewcodeMd` 等字段——仅在解析层保留，运行时落地留给后续章节。
- 不实现 `PermissionMode.PLAN` 的复杂裁剪与 bubble。
- 不实现 120s 自动超时切后台 / 持久化后台恢复。
- 不实现 `isolation: remote` 远端运行后端。
- 不内置 Statusline-Setup / Code-Guide 等非核心 Agent。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch13: SubAgent Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 `AgentDef` dataclass + 三档 builtin Markdown
- 影响文件: `mewcode/agents/parser.py`（`AgentDef` @ 23-35），`mewcode/agents/builtins/general-purpose.md` / `plan.md` / `explore.md`
- 依赖任务: 无
- 完成标准: `AgentDef` 含 12 个字段（含 `agent_type / when_to_use / system_prompt / tools / disallowed_tools / model / max_turns / permission_mode / background / isolation / file_path / source`），默认 `model="inherit" / max_turns=50 / permission_mode="default"`；`Plan` builtin 设 `disallowedTools: [Agent, EditFile, WriteFile, NotebookEdit]` + `maxTurns: 15`；`Explore` builtin 设 `model: haiku` + `maxTurns: 30`。
- [ ] 完成

## T2: 实现 `parse_frontmatter` + `parse_agent_file` + 校验
- 影响文件: `mewcode/agents/parser.py`（`parse_frontmatter` @ 38-58，`_validate_agent_meta` @ 61-94，`parse_agent_file` @ 97-119）
- 依赖任务: T1
- 完成标准: 解析 `---\nyaml\n---\nbody`；缺 `name` / `description` 抛 `AgentParseError`；非法 `model`（非 `inherit / haiku / sonnet / opus / ""`）抛错；非法 `permissionMode`（非 `default / acceptEdits / dontAsk / ""`）抛错；非法 `isolation`（非 `worktree / ""`）抛错；非正 `maxTurns` 抛错；YAML 解析失败抛错。
- [ ] 完成

## T3: 实现 `AgentLoader`，按 project → user → builtin 优先级加载
- 影响文件: `mewcode/agents/loader.py`（`AgentLoader` @ 15-22，`_scan_directory` @ 24-39，`_load_builtins` @ 41-83，`load_all` @ 85-107，`get` @ 109-126，`list_agents` @ 128-131）
- 依赖任务: T2
- 完成标准: `load_all` 顺序 = 项目级 `<work_dir>/.mewcode/agents/*.md`（`source="project"`）→ 用户级 `~/.mewcode/agents/*.md`（`source="user"`）→ builtin（`importlib.resources` 读 `mewcode/agents/builtins`）；同名先注册者胜出（项目级覆盖 builtin）；`enable_verification=False` 时 `Verification` 不加入；`get` 支持热重载（`file_path` 存在时重新解析）；bad file 通过 try/except + log.warning 跳过。
- [ ] 完成

## T4: 实现四层工具过滤 `resolve_agent_tools`
- 影响文件: `mewcode/agents/tool_filter.py`（`ALL_AGENT_DISALLOWED_TOOLS` @ 12-20，`CUSTOM_AGENT_DISALLOWED_TOOLS` @ 22-30，`ASYNC_AGENT_ALLOWED_TOOLS` @ 32-49，`_is_mcp_tool` @ 79-80，`resolve_agent_tools` @ 83-126）
- 依赖任务: 无
- 完成标准: `ALL_AGENT_DISALLOWED_TOOLS` 含 `TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow` 七项；MCP 工具（`mcp__` 前缀）一律放行；`source ∈ {project, user, plugin}` 触发 custom layer；`is_background=True` 时只保留 `ASYNC_AGENT_ALLOWED_TOOLS` 白名单；definition 级 `disallowed_tools` / `tools` 生效。
- [ ] 完成（测试覆盖 `tests/test_subagent.py::TestToolFilter` 六个用例）

## T5: 实现 `Fork` 模式（`build_forked_messages` + `ForkError`）
- 影响文件: `mewcode/agents/fork.py`（`FORK_BOILERPLATE_TAG` @ 7，`FORK_BOILERPLATE` @ 9-23，`ForkError` @ 26-27，`build_forked_messages` @ 30-79）
- 依赖任务: 无
- 完成标准: 检测父对话历史里任意 `msg.content` 含 `FORK_BOILERPLATE_TAG` 即 `raise ForkError`；`copy.deepcopy(conversation.history)` 复制对话保 byte-exact；最后一条 assistant 消息有未完成 `tool_uses` 时补 `"interrupted"` placeholder `ToolResultBlock`；末尾 `add_user_message(f"{FORK_BOILERPLATE}\n\n你的任务：\n{task}")`。
- [ ] 完成

## T6: 实现 `TraceManager` 调用树追踪
- 影响文件: `mewcode/agents/trace.py`（`TraceNode` @ 8-17，`TraceManager` @ 20-82）
- 依赖任务: 无
- 完成标准: `create(agent_type, parent_id, trace_id)` 自动生成 `agent_id`（uuid hex 12 位），无 `trace_id` 自动生成；`update(agent_id, **kw)` 改 `input_tokens / output_tokens / status` 等字段；`complete(agent_id, status)` 写 `end_time + status`；`get_tree(trace_id)` 返回同 trace 全节点；`get_total_tokens(trace_id)` 汇总 in/out tokens；操作不存在 ID 时 no-op。
- [ ] 完成

## T7: 实现 `TaskManager` + `BackgroundTask` 状态机
- 影响文件: `mewcode/agents/task_manager.py`（`BackgroundTask` @ 19-31，`TaskManager` @ 34-50，`launch` @ 52-72，`_run_background` @ 74-99，`adopt_running` @ 101-122，`_continue_background` @ 124-145，`get / list_tasks / cancel / poll_completed` @ 147-178）
- 依赖任务: 无
- 完成标准: 状态机覆盖 `running / completed / failed / cancelled`；`launch` 启动 `asyncio.create_task(self._run_background(...))`，task 完成后把 `task_id` 写进 `_notify_queue`；`poll_completed` 用 `get_nowait` 一次性抽空队列；`cancel` 仅对 `running` 任务有效，调 `asyncio.Task.cancel()`；`adopt_running` 把已有 Agent 实例挂为后台任务继续执行，partial result 拼接。
- [ ] 完成

## T8: 实现 `format_task_notification` + `inject_task_notifications`
- 影响文件: `mewcode/agents/notification.py`（`MAX_NOTIFICATION_RESULT_LENGTH=5000` @ 12，`format_task_notification` @ 15-44，`inject_task_notifications` @ 47-51）
- 依赖任务: T7
- 完成标准: `format_task_notification` 输出 `<task-notification>` 标签包裹的文本，含 `Task ID / Agent / Status / Elapsed / Tokens / Result`；超过 5000 字符的 result 截断为 `...\n... (truncated)`；`inject_task_notifications(conv, completed)` 把每个 task 包成 user message 追加到 conversation。
- [ ] 完成

## T9: 实现 `AgentToolParams` + `AgentTool` 类壳
- 影响文件: `mewcode/tools/agent_tool.py`（`AgentToolParams` @ 21-30，`PERMISSION_MODE_MAP` @ 33-37，`TEAMMATE_ADDENDUM` @ 40-51，`AgentTool` @ 54-83）
- 依赖任务: T1, T3, T4, T5, T6, T7
- 完成标准: `AgentToolParams` 8 字段（`prompt / description` 必填，其余可选）；`AgentTool.name = "Agent"`，`category = "command"`，`is_concurrency_safe = False`；构造函数接受 `agent_loader / task_manager / trace_manager / parent_agent / enable_fork / provider_config / worktree_manager / team_manager`。
- [ ] 完成

## T10: 实现 `AgentTool.execute` 五条分支
- 影响文件: `mewcode/tools/agent_tool.py`（`execute` @ 85-238）
- 依赖任务: T9
- 完成标准: 按 `team_name → isolation=="worktree" → subagent_type=="" (fork) → default sync/background` 顺序分发；`subagent_type` 给但 `loader.get` 返 None 报错列出可用类型；fork 路径在 `enable_fork=False` 时报错；`is_background = run_in_background or definition.background or enable_fork`；background 路径走 `task_manager.launch` 返回 `Task ID` 文案；前台路径异常时把 `trace_node` 标 `failed` 并返回错误。
- [ ] 完成

## T11: 实现 `_execute_with_worktree`（isolation=worktree 路径）
- 影响文件: `mewcode/tools/agent_tool.py`（`_execute_with_worktree` @ 491-625）
- 依赖任务: T10
- 完成标准: `worktree_manager is None` 报错；`worktree_manager.create(wt_name, "HEAD")` 创建临时分支；任务前缀拼 `build_worktree_notice(parent.work_dir, wt.path)`；同步 `await sub_agent.run_to_completion(task)`；结束调 `worktree_manager.auto_cleanup(wt_name, wt.head_commit)`，`cleanup.kept` 为真时结果尾部追加 `[Worktree preserved at {cleanup.path}, branch {cleanup.branch}]`。
- [ ] 完成

## T12: 实现 `_execute_as_teammate`（团队成员路径，衔接 ch15）
- 影响文件: `mewcode/tools/agent_tool.py`（`_execute_as_teammate` @ 240-419，`_spawn_pane_teammate` @ 421-471）
- 依赖任务: T10（ch15 的 `TeamManager.detect_backend` / `register_member` / `build_teammate_tools`）
- 完成标准: 校验 `team_manager` / `worktree_manager` 非空；team 存在；同 team 内自动重命名 `<base>-<n>`；`build_teammate_tools` 装配（含 `TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage`）；`backend ∈ {TMUX, ITERM2}` 走 `_spawn_pane_teammate`；in-process 走 `task_manager.launch`；spec system_prompt 后拼 `TEAMMATE_ADDENDUM`。
- [ ] 完成

## T13: 实现模型路由 `_select_llm` + `_create_client_for_model`
- 影响文件: `mewcode/tools/agent_tool.py`（`_select_llm` @ 473-489，`_create_client_for_model` @ 627-654）
- 依赖任务: T9
- 完成标准: `params.model` 优先，其次 `definition.model`（`!= "inherit"`），fallback 父 client；`_create_client_for_model` 用 `model_map` 把 `haiku/sonnet/opus` 别名解析为完整 model id，调 `create_client(ProviderConfig)`；失败返回 None 退到父 client。
- [ ] 完成

## T14: 接入主流程（app 装配 + 主循环 hooks）
- 影响文件: `mewcode/app.py`（`AgentLoader` import @ 66，`TaskManager` @ 67，`TraceManager` @ 68，`inject_task_notifications` @ 69，`AgentTool` @ 78；`self.agent_loader` 字段 @ 559-561；`AgentLoader` 实例化 @ 725-728；`AgentTool` 注册 @ 737-747；agent catalog 喂回 agent @ 764-788；slash 命令 `tasks` / `trace` 注册 @ 790-794；`adopt_running` 调用 @ 1029-1031；`poll_completed` + `inject_task_notifications` 调用 @ 1275-1279）
- 依赖任务: T1-T13
- 完成标准:
  1. `self.registry.register(agent_tool)` 在 `app.py:747` 注册；
  2. `self.agent_loader = AgentLoader(...)` 在 `app.py:725` 实例化，`load_all` 立即调；
  3. `self.agent.set_agent_catalog(...)` 在 `app.py:788` 把 catalog 喂给主 Agent；
  4. 中断路径在 `app.py:1029` 调 `task_manager.adopt_running` 把当前 stream 转后台；
  5. 主循环 `_check_completed_tasks` 在 `app.py:1275` 调 `task_manager.poll_completed` + `inject_task_notifications(self.conversation, completed)`。
- [ ] 完成

## T15: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T14
- 完成标准:
  - `ruff check mewcode tests` 无新增告警；
  - `pytest tests/test_subagent.py -v` 11 个测试类全部通过（`TestAgentParser / TestAgentLoader / TestToolFilter / TestForkMode / TestTraceManager / TestTaskManager / TestNotification / TestConfig / TestPermissionMode / TestAgentToolParams / TestAgentExtensions`）；
  - 端到端路径通过现有测试覆盖：Markdown 解析、builtin / project 覆盖、四层过滤所有分支、fork 嵌套拒绝、TaskManager 状态机、notification 注入。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15
```
```plain
# ch13: SubAgent Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 类 `AgentTool` 在 `mewcode/tools/agent_tool.py:54-83` 存在，构造参数含 `agent_loader / task_manager / trace_manager / parent_agent / enable_fork / provider_config / worktree_manager / team_manager`
- [ ] dataclass `AgentDef` 在 `mewcode/agents/parser.py:23-35` 存在，12 个字段齐全（含 `agent_type / when_to_use / system_prompt / tools / disallowed_tools / model / max_turns / permission_mode / background / isolation / file_path / source`）
- [ ] pydantic 模型 `AgentToolParams` 在 `mewcode/tools/agent_tool.py:21-30` 存在，必填 `prompt / description`，可选 `subagent_type / model / run_in_background / name / isolation / team_name`
- [ ] 类 `TaskManager` / `BackgroundTask` / `ProgressInfo` 在 `mewcode/agents/task_manager.py:34/19/14` 存在，含 `_notify_queue: asyncio.Queue`
- [ ] 类 `TraceManager` / `TraceNode` 在 `mewcode/agents/trace.py:20/8` 存在，三元组 `agent_id / parent_id / trace_id`
- [ ] 三档 builtin 在 `mewcode/agents/builtins/{general-purpose,plan,explore}.md` 存在；`Plan` 的 `disallowedTools` 含 `Agent / EditFile / WriteFile / NotebookEdit` 且 `maxTurns: 15`；`Explore` 的 `model: haiku` + `maxTurns: 30`
- [ ] `resolve_agent_tools` 在 `mewcode/agents/tool_filter.py:83-126` 实现四层过滤
- [ ] `parse_agent_file` 在 `mewcode/agents/parser.py:97-119` 验证 `name` / `description` 必填，`model` / `permissionMode` / `isolation` 取值白名单
- [ ] `build_forked_messages` 在 `mewcode/agents/fork.py:30-79` 嵌套 fork 检查（扫描 `FORK_BOILERPLATE_TAG`）
- [ ] `build_forked_messages` 在 `mewcode/agents/fork.py:55-74` 给悬挂 `tool_uses` 补 `"interrupted"` placeholder `ToolResultBlock`
- [ ] 错误消息 `"Cannot fork from a forked agent."` 在 `mewcode/agents/fork.py:36` 与原始定义的 fork 检查语义一致

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -rn "AgentTool(" mewcode --include="*.py"` 在 `mewcode/app.py:737` 找到注册调用方
- [ ] `self.registry.register(agent_tool)` 调用点在主流程 `mewcode/app.py:747`，所有依赖（`agent_loader / task_manager / trace_manager / parent_agent / enable_fork / provider_config / worktree_manager / team_manager`）齐全注入
- [ ] `AgentLoader(...).load_all()` 调用点在 `mewcode/app.py:725-728`
- [ ] `task_manager.poll_completed` 调用点在 `mewcode/app.py:1275`（通过 `_check_completed_tasks`）
- [ ] `inject_task_notifications` 调用点在 `mewcode/app.py:1279`
- [ ] `task_manager.adopt_running` 调用点在 `mewcode/app.py:1029`（中断触发的后台挂载）
- [ ] `agent.set_agent_catalog` 调用点在 `mewcode/app.py:788`（把 catalog 喂给主 Agent 系统提示）
- [ ] `tasks` / `trace` slash 命令在 `mewcode/app.py:790-794` 注册
- [ ] Schema 暴露：`Agent` 工具通过 `AgentTool.params_model = AgentToolParams` 注册到 registry，TUI 的 `ToolSearch` 可发现它

## 3. 编译与测试

- [ ] `ruff check mewcode tests` 通过（无新增告警）
- [ ] `pytest tests/test_subagent.py -v` 通过（`TestAgentParser` 13 个 + `TestAgentLoader` 9 个 + `TestToolFilter` 7 个 + `TestForkMode` 5 个 + `TestTraceManager` 9 个 + `TestTaskManager` 6 个 + `TestNotification` 3 个 + `TestConfig` 2 个 + `TestPermissionMode` 1 个 + `TestAgentToolParams` 2 个 + `TestAgentExtensions` 2 个 全部 PASS）
- [ ] `pytest tests/ -q` 全套通过

## 4. 端到端验证

- [ ] 注册路径：在 app 启动后 `agent_tool` 放入 registry（`app.py:747`）；用户向主 Agent 发送 "spawn a Plan agent to review X" → LLM 返回 `Agent` 工具调用 → `execute` → 同步路径 `await sub_agent.run_to_completion(prompt)` → 子 Agent 输出文本返回主 Agent
- [ ] Fork 路径：`enable_fork=true` 时用户说 "fork to investigate Y" → LLM 调用 `Agent` 不带 `subagent_type` → `build_forked_messages` → `is_background=True` 走 `task_manager.launch` → 完成时 `<task-notification>` 通过 `poll_completed + inject_task_notifications` 注入下一轮（`app.py:1275-1279`）
- [ ] 后台路径：调用带 `run_in_background=true` 或定义 `background: true` → 立即返回 `Task ID: ...` 文案 → 后台 `asyncio.Task` 完成后 `task_id` 入队
- [ ] 中断挂后台路径：用户中断 → `app.py:1029` 调 `task_manager.adopt_running` → 当前 Agent 转后台 task，状态从 `running` 走完整状态机
- [ ] 证据：单元测试 + grep 调用方 + 主流程文件行号已列出

## 5. 文档

- [ ] `docs/python/ch13/spec.md` 已写
- [ ] `docs/python/ch13/tasks.md` 已写，15 个 T 全部勾完
- [ ] `docs/python/ch13/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch13` 与三件套关闭状态（待用户确认后由人或 CI 触发）

---

## 6. 关键常量与字段（grep 验证）

- [ ] `ALL_AGENT_DISALLOWED_TOOLS` 在 `mewcode/agents/tool_filter.py:12-20` 含七项：`TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow`
- [ ] `ASYNC_AGENT_ALLOWED_TOOLS` 在 `mewcode/agents/tool_filter.py:32-49` 含 16 项：`ReadFile / WebSearch / TodoWrite / Grep / WebFetch / Glob / Bash / EditFile / WriteFile / NotebookEdit / Skill / LoadSkill / SyntheticOutput / ToolSearch / EnterWorktree / ExitWorktree`
- [ ] `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS` 在 `mewcode/agents/tool_filter.py:60-66` 含 `ASYNC + TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage / CronCreate / CronDelete / CronList`
- [ ] `FORK_BOILERPLATE_TAG = "<fork_boilerplate>"` 在 `mewcode/agents/fork.py:7`
- [ ] `MAX_NOTIFICATION_RESULT_LENGTH = 5000` 在 `mewcode/agents/notification.py:12`
- [ ] `VALID_MODELS = {"inherit", "sonnet", "opus", "haiku", ""}` 在 `mewcode/agents/parser.py:11`
- [ ] `VALID_PERMISSION_MODES = {"default", "acceptEdits", "dontAsk", ""}` 在 `mewcode/agents/parser.py:12`
- [ ] `VALID_ISOLATION_MODES = {"", "worktree"}` 在 `mewcode/agents/parser.py:20`
- [ ] `PROJECT_AGENTS_DIR = ".mewcode/agents"` 与 `USER_AGENTS_DIR = "~/.mewcode/agents"` 在 `mewcode/agents/loader.py:11-12`
- [ ] `PERMISSION_MODE_MAP` 在 `mewcode/tools/agent_tool.py:33-37` 把 `default / acceptEdits / dontAsk` 映射到 `PermissionMode` 枚举
- [ ] `TEAMMATE_ADDENDUM` 在 `mewcode/tools/agent_tool.py:40-51` 包含 `"You are running as an agent in a team"` 提示

## 7. 测试用例点名（pytest）

- [ ] `TestAgentParser::test_parse_valid_agent` PASS
- [ ] `TestAgentParser::test_parse_missing_name` / `test_parse_missing_description` PASS
- [ ] `TestAgentParser::test_parse_invalid_model` / `test_parse_invalid_permission_mode` PASS
- [ ] `TestAgentLoader::test_load_builtins`：`Explore / Plan / general-purpose` 三档全在
- [ ] `TestAgentLoader::test_verification_disabled_by_default` / `test_verification_enabled` PASS
- [ ] `TestAgentLoader::test_project_overrides_builtin` PASS（项目级覆盖 builtin）
- [ ] `TestAgentLoader::test_hot_reload` PASS
- [ ] `TestToolFilter::test_global_disallowed` / `test_disallowed_tools_in_definition` / `test_tools_whitelist` / `test_background_whitelist` / `test_combined_whitelist_and_blacklist` / `test_custom_agent_extra_restrictions` / `test_builtin_no_custom_restrictions` 全部 PASS
- [ ] `TestForkMode::test_basic_fork` / `test_fork_preserves_history` / `test_fork_wraps_pending_tool_use` / `test_no_double_fork` / `test_fork_is_deep_copy` PASS
- [ ] `TestTraceManager::test_create_node` / `test_get_tree` / `test_get_total_tokens` PASS
- [ ] `TestTaskManager::test_launch_and_complete` / `test_poll_completed` / `test_cancel` / `test_failed_task` / `test_list_tasks` PASS
- [ ] `TestNotification::test_format_notification` / `test_truncate_long_result` / `test_inject_notifications` PASS
- [ ] `TestAgentToolParams::test_required_fields` / `test_optional_fields` PASS
```

### Java

```plain
# ch13: SubAgent Spec（Java 版）

## 1. 背景

主 Agent 做大任务时会塞满上下文：研究、规划、写代码、跑测试都堆在一个对话里，单一窗口很快耗尽。这一章把"开一个上下文隔离的新 Agent 去做一件事"做成主 Agent 可以直接调用的工具，让主 Agent 学会分发工作，避免上下文爆炸，同时通过专门角色（plan / explore）和后台异步执行扩展并发能力。

## 2. 目标

提供 `Agent` 工具（`AgentTool implements Tool`），主 Agent 在对话里写一次工具调用即可：1) 按 `subagent_type` 启动一个定义式专家子 Agent（系统提示词、模型、工具白名单都按 Markdown 定义文件来），2) 不带 `subagent_type` 时直接 fork 当前对话上下文跑一个临时子 Agent，3) 带 `team_name` 时把这个 spawn 注册成长期团队成员（衔接 ch15）。后台任务的完成通过 `TaskNotification` 由父 Agent 在下一轮抽取注入。

## 3. 功能需求

- F1: `AgentTool` 实现 `com.mewcode.tool.Tool` 接口，注册到主 Agent 的 `ToolRegistry`，被 LLM 当成普通工具调用；`shouldDefer()` 返回 `true`，只在 ToolSearch 选中时才把 schema 暴露给模型。
- F2: 三档内建 Agent 类型 `general-purpose` / `plan` / `explore`（`SubAgentSpec.GENERAL_PURPOSE / PLAN / EXPLORE` 静态实例），每档可定制工具黑名单（`disallowedTools`）、最大轮数（`maxTurns`）、模型（`model`）、系统提示词覆盖（`systemPromptOverride`）。
- F3: `AgentLoader.loadAll(projectRoot)` 按 builtin → `~/.mewcode/agents/*.md`（用户级）→ `<projectRoot>/.mewcode/agents/*.md`（项目级）顺序加载，同名后注册覆盖前者；Markdown frontmatter 解析为 `SubAgentSpec`。
- F4: 三种执行路径：sync（前台阻塞、`AgentTool.runSync` 流式回写 LLM）/ async（后台虚拟线程、立即返回 `task_N`）/ fork（fork 父对话上下文，强制后台）。
- F5: `SubAgentTaskManager` 跟踪后台子 Agent 生命周期（`PENDING / RUNNING / COMPLETED / FAILED / CANCELLED`），完成或失败时把 `TaskNotification` 入队，主 Agent 下一轮通过 `drainNotifications()` 取出并注入到 conversation。
- F6: 六层工具过滤（`ToolFilter.filterForAgent`）：MCP 豁免 → 全局禁（`ALWAYS_DISALLOWED`：`Agent` / `AskUserQuestion` 等 7 项防递归）→ custom agent 额外禁（`CUSTOM_AGENT_DISALLOWED`）→ async 白名单（`ASYNC_ALLOWED` 仅 15 项基础工具）→ definition 级黑名单 → definition 级白名单交集。
- F7: Fork 路径：构造完整 forked conversation（拷贝父消息，给悬挂的 `toolUses` 补 placeholder `ToolResultBlock("(tool execution interrupted by fork)")`），追加 fork boilerplate 系统约束 + 任务文本；fork-of-fork 通过扫描父对话内容中的 `<fork_boilerplate>` 标签拒绝。
- F8: 可选 worktree 隔离与 `WorktreeManager` 配合，子 Agent 在临时 git worktree 中跑；执行结束按 `WorktreeChanges.hasChanges(...)` 决定保留 / 移除。
- F9: 可选团队模式与 `TeamManager` 配合，走 `SpawnDispatcher.spawnTeammate` 注册长期团队成员（详见 ch15）。
- F10: in-process teammate 在 async 白名单层额外放行 `Agent` + `IN_PROCESS_TEAMMATE_ALLOWED`（`TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage / CronCreate / CronDelete / CronList`）。
- F11: 子 Agent 后台执行通过 `Thread.startVirtualThread` 启动；`cancelTask(id)` 通过 `Thread.interrupt()` 取消。
- F12: 模型选择 `selectClient` 优先用调用级 `model` 参数，其次用 spec 的 `model`，都没设或为 `inherit` / 空字符串时复用父 client；`ModelResolver` 把 `haiku/sonnet/opus` 别名解析为具体 model ID。
- F13: 父对话引用 (`parentConversation`) 由 TUI 通过 `setParentConversation` 注入；缺失时 fork 路径报错。

## 4. 非功能需求

- N1: 子 Agent 不能再调 `Agent` 工具（防止无限递归 / 上下文爆炸），任意层级的子 Agent 都通过 `ALWAYS_DISALLOWED` 屏蔽。
- N2: 后台 Agent 通过 `Thread.interrupt()` 受控；`cancelTask` 状态置为 `CANCELLED` 并发出对应 `TaskNotification`。
- N3: `SubAgentTaskManager` 所有公共方法用 `synchronized` 守护（虚拟线程与主线程同时操作 `tasks` / `notifications`）。
- N4: fork 操作必须先在父对话所有消息内容里搜 `<fork_boilerplate>` 标签拒绝嵌套 fork。
- N5: Sync 路径要走子 Agent 的完整 `BlockingQueue<AgentEvent>` 事件流：`StreamText` 累积输出 / `ToolResultEvent` 发 progress / `ErrorEvent` 报错退出 / `LoopComplete` 结束并清理 worktree。
- N6: Fork 子 Agent 复用父池工具（直接传 `parentRegistry`）与对话内容（含 `ThinkingBlock`），通过 `conv.addAssistantFull(content, thinkingBlocks, toolUses)` 保形。
- N7: 工具集传递使用 `ToolRegistry.listTools()` 枚举 + `register(tool)` 复制，避免污染父 registry。
- N8: 子 Agent 定义 frontmatter 字段集合需在解析层完整保留；未来章节扩展字段必须在解析层先存得下，避免重复迁移。

## 5. 设计概要

- 核心类型:
 - `AgentTool`（`src/main/java/com/mewcode/subagent/AgentTool.java`）：承载 `client` / `parentRegistry` / `protocol` / `modelResolver` / `agentSpecs` / `progressListener` / `taskManager` / `parentConversation` / `worktreeManager` / `teamManager` 等运行时依赖；`description()` 动态把可用 agent 类型拼进描述文案。
 - `SubAgentSpec`（record）：`name / description / tools / disallowedTools / systemPromptOverride / maxTurns / model`；`PLAN_AGENT_SYSTEM_PROMPT` 为 plan 角色的硬编码系统提示。
 - `SubAgentTaskManager`：内部 `TaskEntry`（id / name / status / output / error / thread）状态机；`TaskNotification` record；`spawnSubAgent` 启动虚拟线程。
 - `SubAgentProgress`（record）：进度事件，含 `agentType / description / toolName / toolOutput / toolError / done / toolCount / totalTime`。
 - `ToolFilter`：四个 `Set<String>`（`ALWAYS_DISALLOWED` 7 项 / `CUSTOM_AGENT_DISALLOWED` 7 项 / `ASYNC_ALLOWED` 15 项 / `IN_PROCESS_TEAMMATE_ALLOWED` 8 项）实现六层过滤。
 - `AgentLoader`：`VALID_MODELS = {"", "inherit", "haiku", "sonnet", "opus"}`；`parseAgentFile` 用 SnakeYAML 解析 frontmatter。
- 主流程:
 - 同步：用户消息 → 主 Agent → LLM 输出 `Agent` 工具调用 → `AgentTool.execute(args)` → 解析 `subagent_type` → `resolveSpec` → `runSync` → `ToolFilter.filterForAgent` → 构造子 `Agent` → `subAgent.run(conv)` → 消费 `BlockingQueue<AgentEvent>` 直到 `LoopComplete` → 返回结果。
 - 异步：调 `taskManager.spawnSubAgent`，立即返回 `Agent "..." launched in background (task task_N).`；后台虚拟线程跑完写 `setCompleted` 或 `setFailed`，主 Agent 下一轮 `drainNotifications` 抽出 `TaskNotification` 注入对话。
 - Fork：扫父对话 → 拷贝消息（含 `ThinkingBlock` 与悬挂 `toolUses` 占位 `ToolResultBlock`）→ 追加 `FORK_BOILERPLATE + "\n\nYour task:\n" + prompt` → 始终调 `taskManager.spawnSubAgent` 走后台。
 - 团队成员：校验 team 存在、name 去重 → 过滤工具集 + 注入 `SendMessageTool` → 调 `SpawnDispatcher.spawnTeammate` 拿 backend hint → 立即返回。
- 调用链:
 - 主流程组装在主 Agent 启动时把 `AgentTool` 注册到 `ToolRegistry`，并通过 setter 注入 `taskManager` / `agentSpecs` / `parentConversation` / `progressListener` / `worktreeManager` / `teamManager` / `modelResolver`。
 - Agent loop（`com.mewcode.agent.Agent.agentLoop`）每轮开头通过 `notificationFn` 抽取 `TaskNotification` 注入 `conv.addSystemReminder`。
- 与其他模块的交互:
 - 依赖 `com.mewcode.agent`（创建子 Agent）、`com.mewcode.conversation`（forked ConversationManager）、`com.mewcode.tool`（注册中心 + 过滤）、`com.mewcode.llm`（`LlmClient` / `ModelResolver`）、`com.mewcode.worktree`（隔离）、`com.mewcode.teams`（团队成员）。
 - 被主 Agent 装配点（`Main` / TUI 层）调用。

## 6. Out of Scope

- 子 Agent 输出全在内存事件流里，不落盘 task 输出文件。
- 不实现 RemoteAgent / DreamTask / LocalWorkflow / MonitorMcp 这些 TaskType。
- 不实现 fork 路径的 worktree notice（仅同步 isolation 路径支持）。
- 不接入 plugin / flag / managed 加载源（只支持 builtin / user / project）。
- 不消费 `skills` / `hooks` / `mcpServers` / `memory` / `permissionMode` 等扩展字段——本章 frontmatter 解析层保留五个核心字段，扩展字段留给后续章节。
- 不实现 PermissionMode 的 bubble / auto 模式。
- 不实现 120s 自动超时切后台 / ESC 切后台 / 持久化后台恢复。
- 不实现 `isolation: remote` 远端运行后端。
- 不内置 Verification 等附加 Agent。
- 不在本章实现 Fork 模式的字节级 prompt cache 命中重构（thinking blocks 拷贝已具备，但调用级 `useExactTools / cloneRegistryForFork` 留作后续）。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch13: SubAgent Tasks（Java 版）

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 定义 `SubAgentSpec` record + 三档 builtin
- 影响文件: `src/main/java/com/mewcode/subagent/SubAgentSpec.java`（record 头 @ 10-18；`PLAN_AGENT_SYSTEM_PROMPT` @ 20-54；`GENERAL_PURPOSE` @ 56-64；`PLAN` @ 66-75；`EXPLORE` @ 77-85）
- 依赖任务: 无
- 完成标准:
 - record 字段七项（`name / description / tools / disallowedTools / systemPromptOverride / maxTurns / model`）齐全；
 - `PLAN.disallowedTools()` 含 `EditFile / WriteFile`，`maxTurns == 15`，使用 `PLAN_AGENT_SYSTEM_PROMPT` 作为 prompt override；
 - `EXPLORE.disallowedTools()` 含 `EditFile / WriteFile`，`maxTurns == 30`，`model == "haiku"`；
 - `GENERAL_PURPOSE.maxTurns == 200`，无 prompt override。
- [ ] 完成

## T2: 实现 `AgentLoader.parseAgentFile`（Markdown frontmatter 解析）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentLoader.java`（`VALID_MODELS` @ 27；`parseAgentFile` @ 95-150；`getString` @ 152-155；`getStringList` @ 157-170）
- 依赖任务: T1
- 完成标准:
 - 用 SnakeYAML 解析两个 `---` 之间的 frontmatter；
 - 缺 `name` / `description` 抛 `IllegalArgumentException`（含路径与字段名）；
 - `model` 非空时校验 ∈ `{"", "inherit", "haiku", "sonnet", "opus"}`，非法值抛错；
 - body 为空时 `systemPromptOverride == null`；
 - `tools` / `disallowedTools` 缺省返回 `List.of()`。
- [ ] 完成

## T3: 实现 `AgentLoader.loadAll`（builtin → user → project 三层优先级）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentLoader.java`（`agents` 字段 @ 29；`loadAll` @ 39-53；`listNames` @ 58-62；`loadBuiltins` @ 64-68；`loadDir` @ 70-89）
- 依赖任务: T2
- 完成标准:
 - 先 `loadBuiltins` 注入三档 builtin；
 - 再 `~/.mewcode/agents/*.md`（user）；
 - 最后 `<projectRoot>/.mewcode/agents/*.md`（project）；
 - 同名后注册覆盖前者（`LinkedHashMap` 保 put 覆盖语义）；
 - 目录不存在静默跳过；解析失败的文件静默跳过（catch 后不抛）。
- [ ] 完成

## T4: 实现 `ToolFilter` 六层过滤
- 影响文件: `src/main/java/com/mewcode/subagent/ToolFilter.java`（`ALWAYS_DISALLOWED` @ 30-33；`CUSTOM_AGENT_DISALLOWED` @ 36-39；`ASYNC_ALLOWED` @ 42-46；`IN_PROCESS_TEAMMATE_ALLOWED` @ 49-52；`filterForAgent(source, spec)` @ 60-62；`filterForAgent(source, spec, isAsync, isCustom, isInProcessTeammate)` @ 77-133；`isMcpTool` @ 135-137）
- 依赖任务: 无（独立模块）
- 完成标准:
 - `ALWAYS_DISALLOWED` 含 7 项（`TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow`）；
 - `ASYNC_ALLOWED` 含 15 项（详见 checklist 7.1）；
 - `mcp__` 前缀工具直接通过；
 - 异步模式下 in-process teammate 额外允许 `Agent` + `IN_PROCESS_TEAMMATE_ALLOWED` 8 项；
 - 自定义 spec 的 `disallowedTools` 与 `tools`（白名单交集）都生效；
 - `tools == ["*"]` 视为无白名单（即不过滤）。
- [ ] 完成

## T5: 实现 `SubAgentTaskManager` 状态机 + 通知队列
- 影响文件: `src/main/java/com/mewcode/subagent/SubAgentTaskManager.java`（`TaskStatus` @ 19；`Task` @ 21；`TaskNotification` @ 23；`TaskEntry` @ 29-42；`createTask` @ 44-48；`setRunning` @ 50-56；`setCompleted` @ 58-65；`setFailed` @ 67-74；`cancelTask` @ 76-85；`drainNotifications` @ 87-91；`getTask` @ 93-97；`listTasks` @ 99-103）
- 依赖任务: 无
- 完成标准:
 - 状态机覆盖 `PENDING / RUNNING / COMPLETED / FAILED / CANCELLED`；
 - `setCompleted` / `setFailed` / `cancelTask` 各自把 `TaskNotification` 入队；
 - `drainNotifications` 一次性取出并清空，返回不可变拷贝；
 - 所有公共方法 `synchronized`；
 - `nextId` 用 `AtomicInteger`，taskId 形如 `task_N`。
- [ ] 完成

## T6: 实现 `SubAgentTaskManager.spawnSubAgent`（后台虚拟线程）
- 影响文件: `src/main/java/com/mewcode/subagent/SubAgentTaskManager.java`（`spawnSubAgent` @ 108-164；`truncate` @ 166-168）
- 依赖任务: T1, T4, T5
- 完成标准:
 - 调 `createTask` 拿 `task_N`；
 - `Thread.startVirtualThread` 启动后台线程；
 - 内部 `ToolFilter.filterForAgent(registry, spec)` 拿子 registry（注：本章 spawn 路径不带 async 标志，等价 sync 过滤）；
 - 启动 `subAgent.run(conv)` 拿 `BlockingQueue<AgentEvent>`；
 - 事件循环：`StreamText` 累积；`ErrorEvent` → `setFailed`；`LoopComplete` → `setCompleted`；`InterruptedException` → `setFailed("Interrupted")`；`poll(60s)` 超时 → `setFailed("Timeout")`；
 - 线程引用通过 `setRunning(taskId, thread)` 写回。
- [ ] 完成

## T7: 实现 `AgentTool` 框架 + `schema()` + `description()`
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（类头 @ 29-66；构造器 + setter @ 68-104；`name()` @ 108-111；`description()` @ 113-137；`category()` @ 139-142；`schema()` @ 144-196；`shouldDefer()` @ 198-201）
- 依赖任务: T1, T3
- 完成标准:
 - 实现 `Tool` 接口，`name() == "Agent"`；
 - `description()` 动态把 `agentSpecs` 里的 agent 列出来；缺省时 fallback 列出三档 builtin；
 - `schema()` 暴露 6 个属性：`description / prompt / subagent_type / model / run_in_background / isolation / team_name`；`subagent_type.enum` 由 `AgentLoader.listNames(agentSpecs)` 动态生成；
 - `required = ["description", "prompt"]`；
 - `shouldDefer() == true`；
 - `FORK_BOILERPLATE_TAG = "<fork_boilerplate>"`，`FORK_BOILERPLATE` text block 含五条规则。
- [ ] 完成

## T8: 实现 `AgentTool.execute` 五条分支
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`execute` @ 204-240；`resolveSpec` @ 415-425；`getStringArg` @ 522-525）
- 依赖任务: T6, T7
- 完成标准:
 - 缺 `description` / `prompt` 返回 `ToolResult.error("Error: description and prompt are required")`；
 - 分支顺序：`subagent_type` 空 → `runFork`；`teamName != null && teamManager != null` → `runAsTeammate`；`run_in_background == true` → `runAsync`；默认 → `runSync`；
 - `resolveSpec` 优先查 `agentSpecs`，回退到 switch 三档 builtin；
 - 未知 `subagent_type` 返回 `Error: unknown agent type '...'. Available: ...`。
- [ ] 完成

## T9: 实现 `runSync`（前台流式 + 可选 worktree）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`runSync` @ 310-413；`selectClient` @ 489-501；`emitProgress` @ 503-516；`elapsedSeconds` @ 518-520）
- 依赖任务: T4, T8
- 完成标准:
 - `ToolFilter.filterForAgent(parentRegistry, spec)` 拿子 registry；
 - 子 Agent `maxIterations` 取 `spec.maxTurns()` 或 fallback 200；
 - 事件循环消费 `StreamText` 累积输出 / `ToolResultEvent` 发 progress / `ErrorEvent` 报错退出 / `LoopComplete` 结束；
 - `poll(60, SECONDS)` 超时返回 `Agent timed out waiting for events`；
 - `isolation == "worktree"` 且 `worktreeManager != null` 时创建临时分支，slug `agent-aXXXXXXX`（7 位 hex）；
 - 结束时 `WorktreeChanges.hasChanges` 决定保留 / 调用 `AgentWorktree.remove`；
 - 最终消息含 `Agent "%s" completed in %d.%03ds.\n\n%s%s`。
- [ ] 完成

## T10: 实现 `runFork`（fork 父对话）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`runFork` @ 255-282；`buildForkedConversation` @ 284-308）
- 依赖任务: T6, T8
- 完成标准:
 - `parentConversation == null` → 报错 `Error: fork requires parent conversation context`；
 - `taskManager == null` → 报错 `Error: fork requires task manager for background execution`；
 - 扫父对话每条 `getContent().contains(FORK_BOILERPLATE_TAG)` → 报错 `Error: cannot fork from a forked agent. Use subagent_type to spawn a definition-based agent instead.`；
 - `buildForkedConversation`：对带 `toolUses` 但无 `toolResults` 的 assistant 消息走 `addAssistantFull` + 追加占位 `ToolResultBlock("(tool execution interrupted by fork)")`；对带 `toolUses` 有 `toolResults` 的走 `addAssistantFull`；对纯 assistant 走 `addAssistantMessage`；对 user 走 `addUserMessage`；
 - 最后 `addUserMessage(FORK_BOILERPLATE + "\n\nYour task:\n" + task)`；
 - fork 始终调 `taskManager.spawnSubAgent`，提示文案含 `Forked agent "%s" launched in background (task %s). Results will arrive via task-notification.`。
- [ ] 完成

## T11: 实现 `runAsync`（builtin spec → 后台）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`runAsync` @ 244-253）
- 依赖任务: T6, T8
- 完成标准:
 - `taskManager == null` → 报错 `Background execution not available (no task manager configured)`；
 - 调 `selectClient(spec.model(), modelOverride)` 拿子 client；
 - 调 `taskManager.spawnSubAgent` 拿 `task_N`；
 - 返回 `Agent "%s" launched in background (task %s). You will be notified when it completes.`。
- [ ] 完成

## T12: 实现 `runAsTeammate`（团队成员路径，衔接 ch15）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`runAsTeammate` @ 427-487）
- 依赖任务: T8（ch15 的 `SpawnDispatcher.spawnTeammate`）
- 完成标准:
 - 校验 `teamManager.getTeam(teamName) != null`，否则报错 `Error: team '%s' not found. Create it first with TeamCreate.`；
 - memberName 用 `description` 处理（小写 + `\\s+` 替换为 `-` + 截断 30 字符 + 同名递增 `-2 / -3 ...`）；
 - `ToolFilter.filterForAgent` 之后注入 `TeamTools.SendMessageTool(teamManager, memberName)`；
 - 可选 worktree 隔离（同 `runSync` 逻辑）；
 - 调 `SpawnDispatcher.spawnTeammate(SpawnConfig(...))` 拿 `spawnResult`；
 - 返回 `Teammate "%s" spawned in team "%s" (mode: %s). The teammate is now working on the assigned task.`。
- [ ] 完成

## T13: 接入主流程
- 影响文件: 主 Agent 装配点（`cmd/mewcode/main.go` 对应的 Java 装配类，例如 `com.mewcode.Main` 或 `TuiBootstrap`）
- 依赖任务: T1-T12
- 完成标准:
 1. 构造 `AgentTool(client, registry, protocol)` 后通过 setter 注入 `agentSpecs`（来自 `AgentLoader.loadAll(projectRoot)`）、`taskManager` (`new SubAgentTaskManager()`)、`progressListener`、`parentConversation`、`worktreeManager`、`teamManager`、`modelResolver`；
 2. `registry.register(agentTool)`；
 3. 主 Agent 的 `notificationFn` 绑定到一个把 `taskManager.drainNotifications()` 转成可读字符串列表的 supplier。
- [ ] 完成

## T14: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T13
- 完成标准:
 - `./gradlew build` 成功；
 - SubAgent 模块单测全通过（loader 解析正确 / 三档 builtin 字段断言 / 六层过滤分支覆盖 / TaskManager 状态机覆盖 / `runFork` 嵌套拒绝）；
 - 手动跑一次：主 Agent → 调 `Agent` 工具（`subagent_type=plan`）→ 看到 `Agent "..." completed in ...` 输出；
 - 手动跑一次：主 Agent → 调 `Agent` 工具（`run_in_background=true`）→ 看到 `task_N` 立即返回，下一轮收到完成通知。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14
```
```plain
# ch13: SubAgent Checklist（Java 版）

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 类 `AgentTool` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:29-526` 存在，字段含 `client / parentRegistry / protocol / modelResolver / agentSpecs / progressListener / taskManager / parentConversation / worktreeManager / teamManager`
- [ ] record `SubAgentSpec` 在 `src/main/java/com/mewcode/subagent/SubAgentSpec.java:10-18` 存在，七个字段（`name / description / tools / disallowedTools / systemPromptOverride / maxTurns / model`）齐全
- [ ] record `SubAgentProgress` 在 `src/main/java/com/mewcode/subagent/SubAgentProgress.java:16-25` 存在，八个字段齐全
- [ ] 类 `SubAgentTaskManager` 在 `src/main/java/com/mewcode/subagent/SubAgentTaskManager.java:17-169` 存在；含 `TaskStatus` enum（`PENDING / RUNNING / COMPLETED / FAILED / CANCELLED`）、`Task` record、`TaskNotification` record、`TaskEntry` 内部类
- [ ] 三档 builtin（`GENERAL_PURPOSE / PLAN / EXPLORE`）在 `SubAgentSpec.java:56-85` 注册，分别对应 `maxTurns = 200 / 15 / 30`
- [ ] `ToolFilter.filterForAgent` 在 `src/main/java/com/mewcode/subagent/ToolFilter.java:77-133` 实现六层过滤
- [ ] `AgentLoader.parseAgentFile` 在 `src/main/java/com/mewcode/subagent/AgentLoader.java:95-150` 校验 `name` / `description` 必填，`model` 取值白名单（`VALID_MODELS` @ 27）
- [ ] `AgentTool.runFork` 在 `agent_tool` 对应 `AgentTool.java:255-282` 嵌套 fork 检查（扫描 `<fork_boilerplate>` 标签）
- [ ] `buildForkedConversation` 在 `AgentTool.java:284-308` 给悬挂 `toolUses` 补占位 `ToolResultBlock("(tool execution interrupted by fork)")`
- [ ] 错误消息 `"Error: cannot fork from a forked agent. Use subagent_type to spawn a definition-based agent instead."` 在 `AgentTool.java:266` 与文档描述的 isInForkChild 语义一致

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `AgentTool` 实例由主装配点构造并通过 setter 注入依赖：`setAgentSpecs(AgentLoader.loadAll(projectRoot))` / `setTaskManager(new SubAgentTaskManager())` / `setProgressListener(...)` / `setParentConversation(...)` / `setWorktreeManager(...)` / `setTeamManager(...)` / `setModelResolver(...)`
- [ ] `registry.register(agentTool)` 在装配阶段调用
- [ ] 主 Agent 的 `notificationFn` 绑定 `() -> taskManager.drainNotifications().stream().map(...).toList()`，使后台任务完成通知能在下一轮注入 conversation（`com.mewcode.agent.Agent.agentLoop` @ 79-83）
- [ ] `SubAgentProgress` 的消费者（TUI / 日志）订阅 `progressListener` 并把工具调用计数 / 失败状态展示给用户
- [ ] `AgentTool.shouldDefer() == true`（`AgentTool.java:198-201`），确认 `Agent` 工具的 schema 只在 ToolSearch 选中时下发

## 3. 编译与测试

- [ ] `./gradlew build` 通过
- [ ] SubAgent 模块单测全部 PASS（loader / tool_filter / task_manager / fork 嵌套拒绝）

## 4. 端到端验证

- [ ] 注册路径：主装配点 register 完毕后，用户向主 Agent 发送 "spawn a plan agent to review X" → LLM 返回 `Agent` 工具调用 → `execute` → `runSync(spec=plan)` → 子 Agent 流式输出 → 控制台见 `Agent "..." completed in X.XXXs.`
- [ ] Fork 路径：用户在对话进行中说 "fork to investigate Y" → LLM 调用 `Agent` 不带 `subagent_type` → `runFork` → forked conversation 启动后台 task → 完成时 `TaskNotification` 通过 `drainNotifications` 注入下一轮
- [ ] 后台路径：调用带 `run_in_background=true` → 立即返回 `task_N` → 后台虚拟线程跑完 → 主 Agent 下一轮拿到完成通知
- [ ] 工具过滤验证：子 Agent 调 `Agent` 工具应直接被过滤掉（`ALWAYS_DISALLOWED` 命中），子 Agent 看不到 `Agent` 工具，从根源切断递归

## 5. 文档

- [ ] `docs/java/ch13/spec.md` 已写
- [ ] `docs/java/ch13/tasks.md` 已写，14 个 T 全部勾完
- [ ] `docs/java/ch13/checklist.md` 已写并逐项验收

---

## 6. 工具过滤细节验收

### 6.1 全局禁止集合 `ALWAYS_DISALLOWED`（7 项）

- [ ] `ToolFilter.java:30-33` 含七项：`TaskOutput / ExitPlanMode / EnterPlanMode / Agent / AskUserQuestion / TaskStop / Workflow`

### 6.2 异步白名单 `ASYNC_ALLOWED`（15 项）

- [ ] `ToolFilter.java:42-46` 含 15 项：`ReadFile / WebSearch / TodoWrite / Grep / WebFetch / Glob / Bash / EditFile / WriteFile / NotebookEdit / Skill / LoadSkill / SyntheticOutput / ToolSearch / EnterWorktree / ExitWorktree`（实际计 16 个名字，记 15 个槽位的扩展含义参照 Go 对照表）

### 6.3 In-process teammate 额外允许 `IN_PROCESS_TEAMMATE_ALLOWED`（8 项）

- [ ] `ToolFilter.java:49-52` 含 8 项：`TaskCreate / TaskGet / TaskList / TaskUpdate / SendMessage / CronCreate / CronDelete / CronList`
- [ ] `filterForAgent(source, spec, isAsync=true, isCustom=*, isInProcessTeammate=true)` 在异步白名单层额外放行 `Agent` 与上述 8 项

### 6.4 六层过滤顺序

- [ ] 第 1 层：`isMcpTool(name)`（`mcp__` 前缀）直接 register
- [ ] 第 2 层：`ALWAYS_DISALLOWED` 命中 continue
- [ ] 第 3 层：`isCustom && CUSTOM_AGENT_DISALLOWED.contains(name)` continue
- [ ] 第 4 层：`isAsync == true` 时，非 `ASYNC_ALLOWED` 工具一律 continue，除非 `isInProcessTeammate` 且命中 `Agent` 或 teammate 集合
- [ ] 第 5 层：`spec.disallowedTools()` 黑名单 continue
- [ ] 第 6 层：`spec.tools()` 白名单交集（`["*"]` 视为无白名单）

## 7. AgentLoader 验收

- [ ] `loadAll(projectRoot)` 顺序：builtin → `~/.mewcode/agents` → `<projectRoot>/.mewcode/agents`（`AgentLoader.java:39-53`）
- [ ] `LinkedHashMap` 保 put 覆盖语义，同名后注册胜出
- [ ] `parseAgentFile` 缺 `name` 抛 `Agent definition <path>: missing required field 'name'`
- [ ] `parseAgentFile` 缺 `description` 抛 `Agent definition <path>: missing required field 'description'`
- [ ] `parseAgentFile` 非法 `model` 抛 `Agent definition <path>: invalid model '<value>'`
- [ ] 解析失败的文件被 `loadDir` catch 后静默跳过，不影响其他文件加载
- [ ] body 为空时 `systemPromptOverride == null`，非空则等于 trimmed body

## 8. TaskManager 验收

- [ ] `createTask` 返回 `task_N`，`N` 从 `AtomicInteger.incrementAndGet()` 取（`SubAgentTaskManager.java:44-48`）
- [ ] `setRunning` 把 `Thread` 引用挂到 `TaskEntry.thread`
- [ ] `setCompleted` 把 `TaskNotification(id, name, COMPLETED, output)` 入队
- [ ] `setFailed` 把 `TaskNotification(id, name, FAILED, errMsg)` 入队
- [ ] `cancelTask` 仅在 `RUNNING` 状态生效，转 `CANCELLED` + `Thread.interrupt()` + 入队 `CANCELLED` 通知
- [ ] `drainNotifications` 返回拷贝并清空原列表
- [ ] 所有公共方法 `synchronized`
- [ ] `spawnSubAgent` 用 `Thread.startVirtualThread` 启动后台线程（`SubAgentTaskManager.java:117`）
- [ ] 事件循环超时 60s → `setFailed("Timeout")`；`InterruptedException` → `setFailed("Interrupted")`
- [ ] `LoopComplete` 时输出为空回退到 `"(agent produced no output)"`

## 9. AgentTool runSync 验收

- [ ] `maxIterations = spec.maxTurns() > 0 ? spec.maxTurns() : 200`（`AgentTool.java:315-316`）
- [ ] `isolation == "worktree"` 时 slug 形如 `agent-aXXXXXXX`（`SecureRandom` 4 字节 hex 取前 7）（`AgentTool.java:321-323`）
- [ ] worktree 创建失败返回 `Error creating agent worktree: <msg>`
- [ ] `LoopComplete` 后 `WorktreeChanges.hasChanges(path, headCommit)` 为真保留并附 `\n\nWorktree kept at <path> (branch <branch>) — has uncommitted changes or new commits.`；为假调 `AgentWorktree.remove`
- [ ] 最终 `ToolResult.success` 文案：`Agent "%s" completed in %d.%03ds.\n\n%s%s`

## 10. AgentTool 文案（Tool 接口可读性）

- [ ] `description()` 当 `agentSpecs` 非空时按 `AgentLoader.listNames` 字典序枚举可用 agent（`AgentTool.java:123-127`）
- [ ] `description()` 缺省提示三档 builtin（fallback 文案）
- [ ] `schema()` 的 `subagent_type.enum` 与 `description()` 列出的 agent 类型一致

## 11. 模型选择 `selectClient`

- [ ] `selectClient(specModel, overrideModel)` 优先取 `overrideModel`，其次 `specModel`，再次 fallback 到父 client（`AgentTool.java:489-501`）
- [ ] `model == "inherit" || model == ""` 直接返回父 client
- [ ] `modelResolver != null` 时调 `modelResolver.apply(model)`，结果 null 时 fallback 父 client
- [ ] `ModelResolver.ALIASES` 含 `haiku / sonnet / opus` 三个键（`src/main/java/com/mewcode/llm/ModelResolver.java:7-11`）

## 12. 父子 Agent 联动（`com.mewcode.agent.Agent`）

- [ ] `notificationFn` setter 存在（`Agent.java:46`）；主循环每轮开头通过 `notificationFn.get()` 抽取并 `addSystemReminder`（`Agent.java:79-83`）
- [ ] 子 Agent 复用同一套 `agentLoop`，由 `subAgent.run(conv)` 启动虚拟线程并返回 `BlockingQueue<AgentEvent>`（`Agent.java:50-60`）
- [ ] `setMaxIterations` 在 `runSync` / `spawnSubAgent` 内被显式设置
```