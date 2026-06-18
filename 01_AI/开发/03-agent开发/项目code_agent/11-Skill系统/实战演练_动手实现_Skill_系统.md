# 第11章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装上了 Slash Command 内置命令框架，用户可以通过 `/help` 、 `/clear` 、 `/compact` 这些命令快速操作， `/review` 则走 `prompt` 类型把预设 prompt 转发给 Agent 处理。

这一章要给 MewCode 实现 Skill 技能包系统。做完之后，可复用的 AI 操作变成独立的 Markdown 文件，随时可编辑，不需要编译。

两阶段加载让 Agent 平时只看到 Skill 的名字和描述，按需才加载完整指令和专属工具。用户既能用 `/commit` 显式调用，也能说「帮我提交一下」让 Agent 自己匹配。

具体要新增这些东西：

-   **Skill 定义与解析** ：YAML frontmatter 存元信息，Markdown body 存 prompt，解析器负责分离和校验
-   **Skill 加载器** ：三级搜索路径（项目级 > 用户级 > 内置级）、同名覆盖、热加载、自动注册为 Slash Command
-   **Skill 执行器** ：inline / fork 两种执行模式、 `$ARGUMENTS` 参数替换、 `allowedTools` 工具白名单过滤、fail-fast 依赖检查
-   **LoadSkill 内置工具** ：Agent 意图识别后按需加载完整 SOP 和专属工具，通过 ActivateSkill 钉到环境上下文
-   **两阶段加载** ：启动时只注入摘要到 messages，LoadSkill 调用后激活完整内容
-   **Agent 侧改动** ：activeSkills 列表、环境上下文每轮重建、系统工具豁免 allowedTools 过滤（支持 Skill 嵌套）
-   **三个内置 Skill** ：commit（inline）、review（fork）、test（inline）
-   **目录型 Skill 支持** ：SKILL.md + tool.json + references/ 自包含能力包
-   **/skill 管理命令** ：list / info / reload

这章 **不做** ：Skill 市场和分发、Skill 版本管理。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 单个 Skill 用「YAML frontmatter + Markdown 正文」描述：frontmatter 放元信息（唯一名字、一句话说明、可见工具白名单、执行模式、所用模型、上下文携带策略），正文是发给模型的 SOP 指令
- Skill 存放分三级：项目目录 > 用户目录 > 内置（编译进二进制），同名按优先级覆盖；解析失败的单个文件跳过并记日志，不阻断整体加载
- 两阶段加载：启动时只把所有 Skill 的名字 + 一句说明注入到对话让 Agent 看到；当 Agent 判断要用某个 Skill 时，调一个内置工具把完整指令和专属工具加载进当前会话
- 激活后的完整指令不要塞进普通消息历史，要钉在「环境上下文」里，每轮 Agent Loop 重新构建时它都在最显眼位置；同时激活多个 Skill 时各自的指令并存
- 两种执行模式：一种共享当前对话上下文，执行结果留在主对话历史里；另一种开一条独立对话执行，跑完后把结果摘要回流到主对话；独立模式还能选「全量摘要 / 最近 N 条 / 完全清空」三档来决定要不要带历史进去
- Skill 可以声明可见工具白名单收窄当前能用的工具集，提升模型选择准确率同时落实最小权限；启动时如果白名单里出现不存在的工具就立刻报错（fail-fast）
- 加载 Skill 的那个内置工具属于系统级，不受白名单约束，方便 Skill 之间嵌套触发
- 支持「目录型 Skill」：除了入口 Markdown，还能在同一目录里带自己的工具 schema 和工具实现脚本，整套作为一个可分发的能力包
- Skill 加载完自动注册成 `/<名字>` 短命令出现在帮助里；执行时重新读源文件支持热更新；提供管理子命令查看已加载 Skill、看单个 Skill 详情、强制重新扫描
- 清空对话的命令要顺带把已激活的 Skill 列表也清掉，避免新对话里残留上一次激活的 SOP
- 内置 commit / review / test 三个 Skill 样板（覆盖共享和隔离两种模式）作为生产力工具兼参考模板

# 明确不做（留给后续章节)
- Skill 的市场与分发机制
- Skill 的版本管理
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，反复循环对齐需求，最后生成三份文档。

### 正式开发

三份文档有了之后，施工图纸定好了，让 Claude Code 根据这三份文档开发

![](实战演练_动手实现_Skill_系统-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现_Skill_系统-2.jpeg)

### 功能验证过程

来验收一下结果

先来试试让MewCode直接帮我们安装一个skill

把这个 skill 装下：https://www.skills.sh/anthropics/skills/frontend-design

![](实战演练_动手实现_Skill_系统-3.jpeg)

然后输入

/skill

我们可以看到我们有所有我们的目前拥有的skill

![](实战演练_动手实现_Skill_系统-4.jpeg)

其中，backend- interview会携带新的自己的工具parseResume，那么我们就需要refernces和tool的json了

![](实战演练_动手实现_Skill_系统-5.jpeg)

然后我们输入

/backend-interview

![](实战演练_动手实现_Skill_系统-6.jpeg)

可以看到，它能根据我们的用户画像，去解析简历，然后进行面试

再试试测试的skill，在ui输入

/test

![](实战演练_动手实现_Skill_系统-7.jpeg)

会根据SOP去测试

我们输入

/review

![](实战演练_动手实现_Skill_系统-8.jpeg)

然后我们输入

/commit

![](实战演练_动手实现_Skill_系统-9.jpeg)

会去走我们的commit skill

如果我们是想在Agent任务中自动通过意图识别加载对应的skill，也是可以的，以我们一开始安装的那个forntend-design为例子

我想进行一个电商网站前端页面开发

![](实战演练_动手实现_Skill_系统-10.jpeg)

可以看到Agent会自动意图识别和加载对应的skill的文档，然后跟随步骤开发完成后，就有了我们的一个页面展示了

![](实战演练_动手实现_Skill_系统-11.jpeg)

验收没问题，那么本章的主要任务就完成了。下一章，我们来实现Hook来增加更完整的任务管理和编排能力。

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手（在 `[你的语言]` 处填入你使用的编程语言）：

提示词如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch11: Skill 系统 Spec

> 本版本按课程「第 11 章 Skill 系统」全量实现。在用户明确选择「按课程版」后，旧版（最小实现）的 Out of Scope 项目被升级为本章功能。

## 1. 背景

MewCode 用户会反复输入一组类似的 prompt（commit message 规范、代码审查清单、跑测试的项目类型识别）。当前所有 prompt 要么写死在源码 Slash Command（`/review`）里，要么用户每次手敲，三个痛点：(1) 不能复用与分发，(2) 工具一多模型选错的概率指数级上升，(3) 没有任务级的工具白名单和上下文隔离。Skill 把可复用 SOP 装进可编辑的 Markdown 文件，配渐进式披露与执行模式，同时解决上述三个问题。

## 2. 目标

把 SKILL.md 升级为「带 frontmatter + 资源 + 专属工具」的能力包。启动时只把 `name + description` 注入对话给 Agent 看；Agent 通过 LoadSkill 工具按需把完整 SOP 钉到环境上下文，相关专属工具注册进当前会话。inline 模式 SOP 在主对话内执行，fork 模式独立子 Agent 隔离执行后把结果回流。`/<skill-name>` 显式触发与意图识别自动触发共用同一套执行器。

## 3. 功能需求

### 解析与加载
- F1: `SkillMeta` 字段：name / description / when_to_use / tags / allowed_tools / context / mode / model；`mode` 取 `inline | fork`（默认 inline），`context` 取 `full | recent | none`（仅 fork 模式生效，默认 `none`）
- F2: 单文件 `SKILL.md`（YAML frontmatter + body）与目录型（SKILL.md + tool.json + references/）两种磁盘布局
- F3: 三级搜索路径加载，优先级 `项目 .mewcode/skills/` > `~/.mewcode/skills/` > 内置（go:embed），同名按优先级覆盖；解析失败单条跳过并记日志
- F4: 两阶段加载：阶段 1 启动时只解析 frontmatter（不读 body），阶段 2 由 LoadSkill 工具按需读取 body 与专属工具

### 执行
- F5: `Skill.Render(args)` 把 `$ARGUMENTS` 替换为参数；缺占位符且 args 非空时在末尾追加 `## User Request` 段
- F6: inline 执行：把 SOP 通过 `Agent.ActivateSkill(name, body)` 钉到 env context，下一轮 Agent Loop 起每轮重建时 SOP 都在最显眼位置；同时按 `allowed_tools` 过滤当前会话工具集
- F7: fork 执行：在独立 `conversation.Manager` 里跑临时 Agent，按 `context` 字段决定历史携带策略（full = 主对话摘要 / recent = 最近 5 条 / none = 完全隔离），子 Agent 完成后把最终 assistant 文本作为 assistant 消息回流主对话
- F8: 工具白名单：执行 skill 前过滤 `tools.Registry`，只保留 `allowed_tools` 中声明的工具与系统工具；启动加载阶段做 fail-fast 依赖检查，白名单中出现不存在的工具立刻报错
- F9: 系统工具豁免：`LoadSkill` 标记为 system tool，工具过滤时总是可见，支持 Skill 嵌套调用

### LoadSkill 工具与意图识别
- F10: `LoadSkillTool`：read-only，输入 `{name: string}`；执行三件事——调 `Agent.ActivateSkill` 钉 SOP，注册目录型 skill 声明的专属工具到当前 registry，返回一句简短确认（不返回完整 SOP，避免 tool_result 占用空间）
- F11: 启动期 system prompt 含「可用 Skill 列表」段（只 name + description + LoadSkill 调用指引），通过 prompt builder 的 `SkillSection` 通道注入

### 命令集成
- F12: 每个 skill 自动注册为 `/<name>` 短命令，描述末尾标注 `[skill]`；inline skill 走 TypePrompt 路径，fork skill 走新增的 TypeSkillFork 路径
- F13: `/skill list | info <name> | reload` 管理子命令：list 列出已加载 skill 与来源；info 显示完整 frontmatter 与文件路径；reload 重新扫描三级目录并重建 catalog
- F14: 移除 ch10 硬编码的 `/review` handler，由 review skill 接管

### 目录型 Skill
- F15: 目录布局 `<skill>/SKILL.md` + `<skill>/tool.json` + `<skill>/references/*.go`；tool.json 声明该 skill 专属新增的工具 schema（function calling 兼容），LoadSkill 时把声明的工具注册到当前 registry（实现走 Go 预编译注入，不用 plugin）
- F16: `tool.json` 与 `allowed_tools` 职责分离：tool.json 负责「向 registry 注册新工具」，allowed_tools 负责「skill 执行期间可见工具白名单」；写法上不要重复声明已有内置工具

### 热更新与清理
- F17: 每次 skill 执行时重新读取源文件（仅 body，frontmatter 走启动期缓存），文件修改即时生效；解析失败回退到缓存版本并记日志
- F18: `/clear` 命令在清对话历史时调 `Agent.ClearActiveSkills()` 把激活 skill 列表也清空

### 内置 Skill
- F19: 三个内置 skill 通过 `go:embed` 编译进二进制：`commit`（inline）、`test`（inline）、`backend-interview`（fork, context: none，目录型自带 `parse_resume` 工具）
 - 不包含 `review`：避免与 ch10 硬编码的 `/review` slash command 名字冲突

### 远程安装
- F20: `InstallSkillTool` 让用户把 URL 发给 mewcode、由 Agent 自动安装到 `~/.mewcode/skills/<name>/`
 - 支持三种 URL：`https://www.skills.sh/<owner>/<repo>/<name>` / `https://github.com/<owner>/<repo>/tree/<ref>/<path>` / `https://raw.githubusercontent.com/.../SKILL.md`
 - 走 GitHub Contents API 递归拉取目录树（无需本地 git），单文件 ≤1 MiB、总大小 ≤8 MiB、文件数 ≤64、深度 ≤4
 - 暂存到兄弟 tempdir，验证含 SKILL.md 后 atomic rename 到位
 - 安装后自动 `Catalog.Reload` + 单条 `registerSkillCommand`，无需 TUI 重启即可 `/<name>` 与 `LoadSkill` 触发

## 4. 非功能需求

- N1: 单个 skill 文件解析失败不能阻断其他 skill 加载，错误走 debug log
- N2: 启动加载阶段（阶段 1）不读 body，确保 1000 个 skill 也能秒级启动
- N3: fork 模式必须隔离 conversation，主对话状态不被子 Agent 修改
- N4: 工具过滤通过 `Agent.ToolNameFilter` 钩子实现，过滤动态生效不要求重启 Agent
- N5: LoadSkill 工具调用不弹权限提示（read-only 类别）
- N6: 内置 skill 与磁盘上同名 skill 冲突时，磁盘版本优先（用户可覆盖内置）

## 5. 设计概要

### 核心数据结构
- `SkillMeta`：扩展 mode / model / context 三个字段
- `Skill`：Meta + PromptBody（懒加载）+ SourceDir + IsDirectory + ToolSchemas（来自 tool.json）
- `Catalog`：name → *Skill；新增 `GetFull(name) (*Skill, error)` 强制重读 body
- `Executor`：`RunInline(ctx, skill, args, ag, conv)` 与 `RunFork(ctx, skill, args, ag, conv) (string, error)`
- `LoadSkillTool`：实现 tools.Tool 接口；持有 *Catalog 与 *Agent 引用，标记 system tool
- Agent 新增字段与方法：`ActiveSkills map[string]string`、`ActivateSkill(name, body)`、`ClearActiveSkills()`、Agent Loop 每轮把 ActiveSkills 注入 system-reminder

### 主流程
1. 启动：TUI `loadSkillsAndBuildPrompt` → `skills.LoadCatalog(workDir)` 三级扫描，每个 skill 只读 frontmatter
2. system prompt 注入：把 catalog 的 `{name, description}` 列表 + LoadSkill 用法说明，通过 SkillSection 喂给 prompt builder
3. 命令注册：每个 skill 注册 `/<name>` 命令；LoadSkillTool 也在启动期注册进 tools.Registry
4. 主 Agent 循环每轮迭代开头：把 `agent.ActiveSkills` 字典的所有 SOP 拼成 system-reminder 注入 conv（与 ch04 的 NotificationFn / Plan Mode reminder 同一通道）
5. 显式调用 `/commit`：handler 调 `Executor.RunInline(commit, args, ag, conv)` → 内部 `ag.ActivateSkill("commit", body)` + 应用工具白名单 ToolNameFilter → 返回 rendered body 作为 user message → Agent loop
6. 意图识别：Agent 调 `LoadSkillTool({name: "commit"})` → 工具执行 `ActivateSkill` + 注册目录型工具 → 返回 `"Skill commit activated. SOP pinned to env. N specialized tools registered."`
7. fork 调用 `/review`：TUI 同步走 `Executor.RunFork` → 新 conv + 过滤 registry + 临时 Agent + Run 到完成 → 把 final text 作为 assistant 消息进主对话
8. `/clear`：清 conv → 调 `ag.ClearActiveSkills()` → 后续轮不再注入旧 SOP

### 调用链
- 启动：main → tui.New → `loadSkillsAndBuildPrompt` → `skills.LoadCatalog` + `register skill commands` + `register LoadSkillTool`
- inline 显式：用户 `/commit` → TUI executeCommand → handler → `Executor.RunInline` → ActivateSkill → user message → Agent loop（每轮 env 注入 SOP + 工具过滤）
- fork 显式：用户 `/review` → TUI executeCommand → handler → `Executor.RunFork`（同步阻塞）→ assistant 消息回流
- 意图触发：Agent 在某轮调用 `LoadSkillTool` → catalog.GetFull → ActivateSkill + register dir tools → 下一轮 SOP 钉在 env 里
- 清理：用户 `/clear` → TUI → conv reset + `ag.ClearActiveSkills`

### 与其他模块的交互
- 上行依赖：TUI（注入 system prompt、注册命令、fork 同步执行、InstallSkill OnInstalled 回调）、Agent（ActiveSkills 字段 + env 注入 + ToolNameFilter）、conversation.Manager（fork 用独立实例）、prompt.builder（SkillSection 通道）、tools.Registry（动态注册目录型工具与 InstallSkillTool）
- 下行：fork 模式调 internal `Agent.Run`，但是 skills 包不直接 import agent 包，通过接口注入（避免循环依赖）；`InstallSkill` 走标准库 `net/http` + GitHub Contents API，不依赖 `git` 二进制

## 6. Out of Scope

- Skill 版本管理 / 升级：`InstallSkill` 重复安装同名 skill 直接覆盖，不做版本号校验或回滚
- 嵌套深度限制：Skill A → LoadSkill(B) → LoadSkill(C) 不做主动限制，依赖 Agent MaxIterations 自然封顶
- fork 嵌套跨 Agent 边界的父子链路记录：留给 ch13 SubAgent
- 目录型 skill 的 Go plugin 动态加载：tool.json 声明的专属工具通过预编译 Go 文件注入而非运行时 plugin（避免 plugin 跨平台问题）；本章内置 `backend-interview` 作为目录型 skill 样板，自带 `parse_resume` 工具的 Go 实现

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch11: Skill 系统 Tasks

> 顺序执行。每完成一个任务跑 `go build ./...` 确保编译过；接入主流程的任务（T11、T12、T13、T14）做完后立刻补一次端到端验证再进下一项。

## T1: 扩展 SkillMeta 字段
- 影响文件: `internal/skills/skills.go`（修改）
- 依赖任务: 无
- 完成标准: SkillMeta 增加 `Mode string`、`Model string`、`Context` 升级为 `inline | fork`（已有），追加 `ForkContext string`（取值 `full | recent | none`）；yaml tag 全部 snake_case
- 备注: 旧 `Context` 字段值 `fork` 等同于 `Mode == "fork"`，做兼容转换

## T2: 拆分 parser 子模块
- 影响文件: `internal/skills/parser.go`（新建）、`internal/skills/skills.go`（修改）
- 依赖任务: T1
- 完成标准: 把 `loadSkill` / `parseSkillMD` 移到 parser.go；新增 `parseFrontmatterOnly(path) (SkillMeta, error)` 不读 body 的轻量解析（阶段 1 加载用）；新增 `loadSkillBody(skill *Skill) error` 强制重读 body
- 备注: parser.go 不依赖 catalog，纯函数

## T3: Catalog 改造为两阶段加载
- 影响文件: `internal/skills/catalog.go`（新建，从 skills.go 抽出）、`internal/skills/skills.go`（修改）
- 依赖任务: T2
- 完成标准: `Catalog` 在阶段 1 只装 frontmatter，每个 Skill 的 PromptBody 默认空；新增 `Catalog.GetFull(name) (*Skill, error)` 触发 loadSkillBody（含热重载逻辑：每次都重读，失败回退缓存）；保留 `Get(name) *Skill` 返回轻量版本
- 备注: `LoadFromDirectory` / `LoadSkills` / `loadInto` 也要适配两阶段

## T4: 内置 skill 嵌入（go:embed）
- 影响文件: `internal/skills/builtins.go`（新建）、`internal/skills/builtins/commit/SKILL.md`、`internal/skills/builtins/review/SKILL.md`、`internal/skills/builtins/test/SKILL.md`、`internal/skills/builtins/backend-interview/SKILL.md` + `tool.json` + `references/parse_resume.go`（新建）
- 依赖任务: T3
- 完成标准: `//go:embed builtins` 嵌入整棵目录，`LoadBuiltins []*Skill` 解析嵌入树返回内置 skill 列表；`LoadSkills(workDir)` 在最后一档加入内置（让磁盘版本覆盖）
- 内置 skill 内容：
 - `commit/SKILL.md`：mode inline / allowed_tools [Bash, ReadFile, Grep]，body 走 git status → diff → conventional commit
 - `review/SKILL.md`：mode fork / forkContext none / allowed_tools [Bash, ReadFile, Grep, Glob]，body 走 5 维度审查
 - `test/SKILL.md`：mode inline / allowed_tools [Bash, ReadFile, Grep, Glob]，body 走项目类型检测 + 跑测试 + 区分 bug
 - `backend-interview/`：目录型，自带 parse_resume 工具

## T5: tool.json 与目录型 skill 工具注册
- 影响文件: `internal/skills/directory.go`（新建）、`internal/skills/builtins/backend-interview/parse_resume.go`（实际实现，从 references/ 引用编译进二进制）
- 依赖任务: T4
- 完成标准: `parseToolJSON(dir) ([]ToolSchema, error)` 读取 tool.json 校验 function calling schema；`RegisterDirectoryTools(skill, registry) (int, error)` 把目录型 skill 声明的工具实例化并注册进 registry，返回数量；找不到对应实现时记 warning 不阻断
- 备注: parse_resume 实现走预编译 Go（在 builtins 同目录），不走 plugin

## T6: Agent ActiveSkills 字段与方法
- 影响文件: `internal/agent/agent.go`（修改）
- 依赖任务: 无（与 T1-T5 并行可做）
- 完成标准: Agent 新增 `ActiveSkills map[string]string`（name → body）；方法 `ActivateSkill(name, body string)`、`ClearActiveSkills`、`GetActiveSkills map[string]string`；Run 主循环每轮迭代开头（在 NotificationFn 注入之后），如 ActiveSkills 非空则拼成一段 system-reminder 注入 conv（标题用 `# Active Skills`）

## T7: Executor.RunInline
- 影响文件: `internal/skills/executor.go`（新建）
- 依赖任务: T3, T6
- 完成标准: `RunInline(ctx, skill, args, agentRef SkillHost) (string, error)`：调用 `skill.Render(args)` 渲染 body → `host.ActivateSkill(skill.Meta.Name, body)` → 对 allowed_tools 做 fail-fast 校验（缺工具立即返回 error）→ 把工具白名单设置到 host.SetToolFilter（封装 Agent.ToolNameFilter）→ 返回 rendered body（作为 user message 走主 loop）
- 备注: 新增 interface `SkillHost { ActivateSkill / SetToolFilter / GetTool(name) }` 实现在 Agent 上，避免 skills 包 import agent

## T8: Executor.RunFork
- 影响文件: `internal/skills/executor.go`（继续）
- 依赖任务: T7
- 完成标准: `RunFork(ctx, skill, args, host SkillForkHost) (summary string, err error)`：
 - 创建新 `conversation.Manager`
 - 按 `skill.Meta.ForkContext` 装填初始历史：`full` 取主对话 last N 条做 LLM 摘要 / `recent` 拷最近 5 条 / `none` 空
 - 把 rendered body 作为 first user message
 - 通过 `SkillForkHost.RunSubAgent(conv, allowedTools) (finalText string, err error)` 跑临时 Agent（实现在 TUI 层注入，复用 agent.Agent.Run + 收集 LoopComplete 文本）
 - 返回 finalText

## T9: LoadSkillTool（系统工具）
- 影响文件: `internal/tools/load_skill.go`（新建）
- 依赖任务: T3, T5, T6
- 完成标准: `LoadSkillTool` 实现 tools.Tool，Name = `LoadSkill`，Category = read；持有 `*skills.Catalog` + `SkillHost`；Execute：catalog.GetFull → host.ActivateSkill → 目录型 skill 调 RegisterDirectoryTools → 返回 `"Skill <name> activated. SOP pinned to env. N specialized tools registered."`；标记 SystemTool 接口让 ToolNameFilter 始终放行
- 备注: tools.Tool 接口增加可选 `SystemTool bool` 检测；Agent 的 ToolNameFilter 应用时绕过 system tool

## T10: 系统工具豁免逻辑
- 影响文件: `internal/tools/tool.go`（修改）、`internal/agent/agent.go`（修改）
- 依赖任务: T9
- 完成标准: 新增 `SystemTool` 接口（可选实现），Agent.applyToolFilter 在调 ToolNameFilter 前先 check 是否系统工具；GetAllSchemas 也要保留系统工具
- 备注: LoadSkillTool 与未来其他系统工具的统一通道

## T11: 接入 TUI —— skill 列表与命令注册
- 影响文件: `internal/tui/tui.go`（修改）、`internal/prompt/builder.go`（保留 SkillSection 通道）
- 依赖任务: T3, T4, T7, T8, T9
- 完成标准:
 - `loadSkillsAndBuildPrompt` 调用新 `skills.LoadCatalog`（两阶段），catalog 存到 m.skillCatalog
 - system prompt SkillSection 改成「Available Skills (call LoadSkill to activate)\n- /<name>: <description>\n...」+ LoadSkill 使用说明
 - 每个 skill 注册命令：inline 走 TypePrompt（handler 调 Executor.RunInline），fork 走新增 TypeSkillFork（handler 直接调 Executor.RunFork 并把返回值作为 assistant 消息插入对话）
 - 注册 LoadSkillTool 到 m.registry：`m.registry.Register(&tools.LoadSkillTool{Catalog: catalog, Host: m.ag})`

## T12: 接入 TUI —— /skill 管理命令与 /clear 集成
- 影响文件: `internal/commands/commands.go`（修改）、`internal/tui/tui.go`（修改）
- 依赖任务: T11
- 完成标准:
 - 新增 `/skill` 命令：`/skill list` → ctx.SkillCatalog.List 含来源；`/skill info <name>` → 全 frontmatter + path；`/skill reload` → catalog.Reload(workDir) + 重新注册命令
 - `/clear` handler 增加 `if m.ag != nil { m.ag.ClearActiveSkills }`
 - 删除 ch10 commands.go:314-326 的硬编码 `/review` 注册（被 review skill 接管）

## T13: 新增 TypeSkillFork 命令类型
- 影响文件: `internal/commands/commands.go`（修改）、`internal/tui/tui.go`（修改）
- 依赖任务: T8, T11
- 完成标准: `TypeSkillFork CommandType = "skill-fork"`；executeCommand 增加 case：调 handler 后把返回的 summary 作为 chatMessage（role=assistant）插入；不触发主 Agent loop

## T14: 接入主流程 —— Agent 注入 SkillHost
- 影响文件: `internal/agent/agent.go`（修改）、`internal/tui/tui.go`（修改）
- 依赖任务: T6, T7, T8
- 完成标准: Agent 实现 SkillHost 接口（ActivateSkill / ClearActiveSkills / SetToolFilter）；TUI 把 m.ag 强转为 skills.SkillHost 传给 Executor 与 LoadSkillTool；fork 路径需要 SkillForkHost.RunSubAgent，由 TUI 提供一个本地实现（开 streaming executor 跑到 LoopComplete 收集最终 assistant 文本）

## T14b: InstallSkillTool（远程安装）
- 影响文件: `internal/skills/install.go`（新建）、`internal/skills/install_tool.go`（新建）、`internal/skills/install_test.go`（新建）、`internal/tui/tui.go`（修改）
- 依赖任务: T3（Catalog.Reload）、T11（registerSkillCommand 抽出）
- 完成标准:
 - `ParseSkillURL(url) (*SkillSource, error)` 支持 skills.sh / github.com tree / raw.githubusercontent.com 三种 URL，拒绝其他 host
 - `Install(src, installRoot) (*InstallReport, error)` 走 GitHub Contents API 递归下载到 staging temp dir，验证含 `SKILL.md` 或 `skill.yaml` 后 atomic rename
 - 限额：单文件 ≤1 MiB、总大小 ≤8 MiB、文件数 ≤64、深度 ≤4
 - `InstallSkillTool` 实现 `tools.Tool`，Name = `InstallSkill`，Category = write；执行后调 `Catalog.Reload` + `OnInstalled(name)` 回调
 - TUI `wireSkillsToAgent` 把 `registerSkillCommand` 抽成可单独调用的方法，作为 OnInstalled 回调
 - SkillSection 文本告知模型「用户给 URL 要求装 skill 时调 InstallSkill」
- 备注: 不依赖本地 `git` 二进制；rate limit 命中（403）时把 GitHub 的错误文本透出给用户

## T15: 单元测试
- 影响文件: `internal/skills/skills_test.go`（修改）、`internal/skills/executor_test.go`（新建）、`internal/skills/directory_test.go`（新建）、`internal/tools/load_skill_test.go`（新建）、`internal/agent/agent_test.go`（修改）
- 依赖任务: T1-T14
- 完成标准: 覆盖
 - parser 两阶段：阶段 1 不读 body / 阶段 2 重读热更新
 - 三级覆盖：磁盘版本盖内置版本
 - Executor.RunInline 钉 SOP + 工具过滤 fail-fast
 - Executor.RunFork 隔离 conv + context: full/recent/none 三档
 - LoadSkillTool 端到端：activate + register dir tools + 简短返回
 - Agent.ActivateSkill / ClearActiveSkills / env 注入
 - 系统工具豁免：ToolNameFilter 设了 LoadSkill 也还在 schema 里
 - tool.json 解析与目录型工具注册
 - /skill list / info / reload 行为
 - /clear 触发 ClearActiveSkills

## T16: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T15
- 完成标准:
 - `go build ./...` 通过
 - `go test ./...` 全过
 - 在仓库根目录 TUI 实操：
 1. 启动看 `/help` 列出 commit / review / test [skill] / backend-interview [skill]
 2. `/skill list` 看到 4 个 skill 与来源
 3. `/skill info commit` 看到完整 frontmatter
 4. 改一处源码后 `/commit` 看到 Agent 走 git status → diff → commit
 5. `/review` 走 fork 路径，主对话不被污染，最后收到 assistant 摘要
 6. 「帮我准备一下后端面试」自然语言触发 LoadSkill("backend-interview")
 7. `/clear` 后 env-reminder 不再出现旧 SOP
 - 截图或日志留证

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
- [ ] T13
- [ ] T14
- [ ] T14b
- [ ] T15
- [ ] T16
```
```plain
# ch11: Skill 系统 Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。本版本贴合课程「全量按课程版」目标，**不**沿用旧版「验收」流程。

## 1. 实现完整性

### 1.1 解析与加载
- [ ] `SkillMeta` 在 `internal/skills/skills.go` 含字段 Name / Description / WhenToUse / Tags / AllowedTools / Context / Mode / Model / ForkContext，yaml tag 全部 snake_case
- [ ] `parseFrontmatterOnly(path) (SkillMeta, error)` 在 `internal/skills/parser.go` 实现，**不**读取 body
- [ ] `loadSkillBody(skill *Skill) error` 在 `internal/skills/parser.go` 实现，强制重读源文件（热重载）
- [ ] `Catalog.GetFull(name) (*Skill, error)` 在 `internal/skills/catalog.go` 实现，每次调用触发 `loadSkillBody`；解析失败回退缓存 + 记 debug log
- [ ] `Catalog.Reload(workDir) error` 在 `internal/skills/catalog.go` 实现
- [ ] 三层加载顺序在 `LoadCatalog(workDir)`：项目 `.mewcode/skills/` > `~/.mewcode/skills/` > 内置 embed；同名按优先级覆盖

### 1.2 内置 skill
- [ ] `internal/skills/builtins/commit/SKILL.md` 存在，frontmatter `mode: inline / allowed_tools: [Bash, ReadFile, Grep]`
- [ ] `internal/skills/builtins/review/SKILL.md` 存在，frontmatter `mode: fork / fork_context: none / allowed_tools: [Bash, ReadFile, Grep, Glob]`
- [ ] `internal/skills/builtins/test/SKILL.md` 存在，frontmatter `mode: inline / allowed_tools: [Bash, ReadFile, Grep, Glob]`
- [ ] `internal/skills/builtins/backend-interview/` 含 SKILL.md + tool.json + parse_resume.go
- [ ] `internal/skills/builtins.go` 使用 `//go:embed builtins` 嵌入；`LoadBuiltins() []*Skill` 解析嵌入树

### 1.3 Executor
- [ ] `internal/skills/executor.go` 含 `RunInline(ctx, skill, args, host) (string, error)` 与 `RunFork(ctx, skill, args, host) (string, error)`
- [ ] inline 调用链：Render → host.ActivateSkill → 工具白名单 fail-fast → host.SetToolFilter → 返回 rendered body
- [ ] fork 调用链：新 conversation.Manager → 按 ForkContext 装填历史（full / recent / none）→ host.RunSubAgent → 返回 finalText
- [ ] `SkillHost` 与 `SkillForkHost` 接口在 `internal/skills/executor.go` 定义

### 1.4 Agent 集成
- [ ] Agent 含 `ActiveSkills map[string]string` 字段
- [ ] `Agent.ActivateSkill(name, body string)` 实现
- [ ] `Agent.ClearActiveSkills()` 实现
- [ ] Agent.Run 主循环每轮迭代开头，如 ActiveSkills 非空则注入 system-reminder（标题 `# Active Skills`，每个 skill 一段，含 name）
- [ ] Agent 实现 SkillHost 接口（编译期可强转）

### 1.5a InstallSkill 远程安装
- [ ] `internal/skills/install.go` 含 `ParseSkillURL` 支持 skills.sh / github.com tree / raw.githubusercontent.com 三种 URL
- [ ] `Install(src, installRoot) (*InstallReport, error)` 走 GitHub Contents API 递归拉取，atomic rename 到 `<installRoot>/<name>/`
- [ ] 限额常量在 install.go：`maxFileSize=1MiB / maxTotalSize=8MiB / maxFileCount=64 / maxRecursionDepth=4`
- [ ] 下载完没有 `SKILL.md` 或 `skill.yaml` 时拒绝安装并清理 staging
- [ ] `internal/skills/install_tool.go` 含 `InstallSkillTool`，Name = `InstallSkill`，Category = write
- [ ] 执行成功后调 `Catalog.Reload(workDir)` + `OnInstalled(name)` 回调
- [ ] TUI 注入 `OnInstalled` 回调指向 `m.registerSkillCommand(name)`，使 `/<name>` 无需重启即可用
- [ ] SkillSection 文本含 "If the user pastes a Skill URL ... call the InstallSkill tool"

### 1.5 LoadSkill 工具与系统工具豁免
- [ ] `internal/tools/load_skill.go` 含 `LoadSkillTool`，Name = `LoadSkill`，Category = read
- [ ] `LoadSkillTool.Execute` 调 `catalog.GetFull` → `host.ActivateSkill` → 目录型 skill 调 `RegisterDirectoryTools` → 返回 `"Skill <name> activated. SOP pinned to env. N specialized tools registered."`（N 为目录型工具数）
- [ ] `tools.SystemTool` 接口在 `internal/tools/tool.go` 定义；LoadSkillTool 实现该接口
- [ ] Agent.ToolNameFilter 应用时绕过 system tool（系统工具始终可见）

### 1.6 目录型 skill
- [ ] `internal/skills/directory.go` 含 `parseToolJSON(dir) ([]ToolSchema, error)` 与 `RegisterDirectoryTools(skill, registry) (int, error)`
- [ ] backend-interview 的 parse_resume 工具能通过 RegisterDirectoryTools 注册到 registry

### 1.7 命令集成
- [ ] 每个 skill 自动注册为 `/<name>` 命令，描述末尾含 `[skill]`
- [ ] inline skill 命令 Type 为 `TypePrompt`，fork skill 命令 Type 为 `TypeSkillFork`
- [ ] `commands.TypeSkillFork` 在 `internal/commands/commands.go` 定义
- [ ] TUI executeCommand 对 TypeSkillFork case：调 handler 返回 summary → 作为 assistant chatMessage 插入对话
- [ ] `/skill list / info <name> / reload` 子命令在 `internal/commands/commands.go` 注册
- [ ] `/clear` handler 调用 `m.ag.ClearActiveSkills()`
- [ ] ch10 硬编码的 `/review` 注册已删除（grep `Review current code changes` 返回 0 条）

## 2. 接入完整性（杜绝死代码）

- [ ] `grep -rn "skills.LoadCatalog" --include="*.go" /Users/codemelo/mewcode` 命中 `internal/tui/tui.go` 至少 1 个非测试调用
- [ ] `grep -rn "ActivateSkill" --include="*.go" /Users/codemelo/mewcode/internal` 命中 Agent 方法定义 + Executor + LoadSkillTool 三处调用
- [ ] `grep -rn "ClearActiveSkills" --include="*.go" /Users/codemelo/mewcode/internal` 命中 `/clear` handler 调用
- [ ] `grep -rn "LoadSkillTool\b\|\"LoadSkill\"" --include="*.go" /Users/codemelo/mewcode/internal` 命中 tool 定义 + tui 注册 + 至少 1 个测试
- [ ] `grep -rn "TypeSkillFork" --include="*.go" /Users/codemelo/mewcode/internal` 命中 commands 定义 + TUI dispatch
- [ ] `grep -rn "RunInline\|RunFork" --include="*.go" /Users/codemelo/mewcode/internal/skills` 命中 Executor 定义 + TUI handler 调用
- [ ] `grep -rn "Catalog.GetFull" --include="*.go" /Users/codemelo/mewcode/internal` 命中 catalog 定义 + LoadSkillTool 调用
- [ ] `grep -rn "InstallSkillTool\|ParseSkillURL" --include="*.go" /Users/codemelo/mewcode/internal` 命中 install 定义 + TUI 注册 + install_test
- [ ] `grep -rn "SystemTool() bool" --include="*.go" /Users/codemelo/mewcode/internal` 命中接口定义 + LoadSkillTool 实现
- [ ] TUI Model `ag` 字段有 `skillCatalog` / 在 loadSkillsAndBuildPrompt 写入 / LoadSkillTool 拿到引用

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && go build ./...` 通过
- [ ] `cd /Users/codemelo/mewcode && go test ./internal/skills/...` 全部通过
- [ ] `cd /Users/codemelo/mewcode && go test ./internal/tools/...` 全部通过
- [ ] `cd /Users/codemelo/mewcode && go test ./internal/agent/...` 全部通过
- [ ] `go vet ./...` 无警告

## 4. 端到端验证（TUI 实操）

> 操作目录在仓库根 `/Users/codemelo/mewcode`，启动 `go run ./cmd/mewcode`

- [ ] 启动后输 `/help`，看到 `/commit [skill] / /review [skill] / /test [skill] / /backend-interview [skill] / /skill` 都列出
- [ ] 输 `/skill list`，输出含 4 个 skill 名称 + 来源（builtin / project / user）
- [ ] 输 `/skill info commit`，输出含完整 frontmatter（含 mode / allowed_tools） + 文件路径
- [ ] 改一处真实文件（如修个空格），输 `/commit`，看到 Agent 真的走 git status → diff → 生成 commit message → git add → git commit；`git log` 看到新 commit
- [ ] 输 `/review`，看到 fork 路径执行：主对话不污染；末尾收到 assistant 摘要含分级标签
- [ ] 自然语言 `"帮我准备一下后端面试"`，看 Agent tool_use 里出现 `LoadSkill({name: "backend-interview"})` 并且 system-reminder 里出现该 skill 的 SOP
- [ ] 输 `/clear`，立即输任意消息，Agent system-reminder 里**不再出现** Active Skills 段
- [ ] 修改 `.mewcode/skills/commit/SKILL.md` 一行，**不重启** TUI，再输 `/commit`，看到新行进入 prompt（热重载验证）
- [ ] 启动时在 catalog 里塞一个 `allowed_tools: [NonExistentTool]` 的 skill，看到启动 log 报 fail-fast 错误（或调用时立刻报错）
- [ ] LoadSkill 工具调用时**不**弹权限提示（read-only 类别 + auto-allow）
- [ ] 在 TUI 输入「装这个 skill：https://www.skills.sh/anthropics/skills/frontend-design」，模型调 InstallSkill；返回安装路径与文件数；立即输 `/frontend-design` 触发新装的 skill（无需 TUI 重启）
- [ ] InstallSkill 失败路径：输错误 URL → 看到具体 host / 格式不对的错误文本；输不存在的 repo → 看到 404 错误透出

## 5. 文档

- [ ] `specs/go/ch11/spec.md` 更新到课程全量版（不是验收版）
- [ ] `specs/go/ch11/tasks.md` 16 个任务全部勾上
- [ ] `specs/go/ch11/checklist.md` 全部条目勾上
- [ ] commit 信息：`feat(ch11): full skill system per course design [spec/tasks/checklist closed]`
```

### Python

```plain
# ch11: Skill 系统 Spec（Python 版）

> 本版本按课程「第 11 章 Skill 系统」全量实现 Python 版本。Skill 把可复用 prompt 升级为 Markdown 能力包，配合 progressive disclosure 与执行模式，让模型在工具变多时仍能精准触发。

## 1. 背景

MewCode 用户会反复输入一组类似的 prompt（commit message 规范、代码审查清单、跑测试的项目类型识别）。当前所有 prompt 要么写死在源码 Slash Command（`/review`）里，要么用户每次手敲，三个痛点：(1) 不能复用与分发，(2) 工具一多模型选错的概率指数级上升，(3) 没有任务级的工具白名单与上下文隔离。Skill 把可复用 SOP 装进可编辑的 Markdown 文件，配渐进式披露与执行模式，同时解决上述三个问题。

## 2. 目标

把 `SKILL.md` 升级为「带 frontmatter + 资源 + 专属工具」的能力包。启动时只把 `name + description` 注入对话给 Agent 看；Agent 通过 `LoadSkill` 工具按需把完整 SOP 钉到环境上下文，相关专属工具注册进当前会话。`inline` 模式 SOP 在主对话内执行，`fork` 模式独立子 Agent 隔离执行后把结果回流。`/<skill-name>` 显式触发与意图识别自动触发共用同一套执行器。

## 3. 功能需求

### 解析与加载
- F1: `SkillDef`（`mewcode/skills/parser.py:24`）字段：`name / description / prompt_body / allowed_tools / mode / model / context / source_path / is_directory`；`mode` 取 `inline | fork`（默认 `inline`），`context` 取 `full | recent | none`（默认 `full`，仅 fork 模式生效）
- F2: 单文件 `*.md`（YAML frontmatter + body）与目录型（`<skill>/SKILL.md` + `tool.json` + `references/*.py`）两种磁盘布局；`SkillLoader._scan_directory` 区分两类
- F3: 三级搜索路径加载（`mewcode/skills/loader.py:23`），优先级 `项目 .mewcode/skills/` > `~/.mewcode/skills/` > 内置（`importlib.resources`）；首次出现的 name 占位，后续同名跳过；解析失败单条 `warning` 日志并跳过
- F4: 启动期 `SkillLoader.load_all` 解析所有 frontmatter+body 进内存；`SkillLoader.get(name)` 每次重读源文件实现热重载，失败回退缓存（`mewcode/skills/loader.py:96`）

### 执行
- F5: `substitute_arguments(prompt_body, args)`（`mewcode/skills/parser.py:99`）把 `$ARGUMENTS` 替换为参数；没有占位符则原样返回
- F6: inline 执行：`SkillExecutor.execute_inline`（`mewcode/skills/executor.py:54`）渲染 body 后调用 `Agent.activate_skill(name, body)` 钉到 env context，主循环每轮迭代重建 environment 时 SOP 都注入；同时按 `allowed_tools` 过滤当前会话工具集
- F7: fork 执行：`SkillExecutor.execute_fork`（`mewcode/skills/executor.py:58`）创建独立 `ConversationManager`，按 `context` 字段决定历史携带（`full` = 主对话拼接摘要 / `recent` = 最近 5 条 / `none` = 完全隔离），临时 Agent 跑到 `LoopComplete` 后把累计文本回流
- F8: 工具白名单：`filter_tool_registry`（`mewcode/skills/executor.py:25`）按 `allowed_tools` 重建一个新的 `ToolRegistry`；白名单中出现不存在的工具立刻 `raise SkillDependencyError`
- F9: 系统工具豁免：`Tool.is_system_tool`（`mewcode/tools/base.py:28`）标记的工具在 `filter_tool_registry` 时自动透传，确保 `LoadSkill` 在 skill 执行期仍可用以支持嵌套调用

### LoadSkill 工具与 Skill Catalog 注入
- F10: `LoadSkill`（`mewcode/tools/load_skill.py:21`）read-only 系统工具，输入 `{name: str}`；调用 `SkillLoader.get` 取 skill → `Agent.activate_skill` 钉 SOP → 目录型 skill 调 `register_skill_tools` 注册专属工具 → 返回简短确认（不返回完整 SOP，避免 tool_result 占用空间）
- F11: 启动期 `app.py:673` 构建「Available Skills」段（只 `- <name>: <description>` 列表 + LoadSkill 调用指引），通过 `Agent.set_skill_catalog` 注入 environment context（`mewcode/prompts.py:293`）

### 命令集成
- F12: 每个 skill 由 `register_skill_commands`（`mewcode/commands/handlers/skill_register.py:18`）注册为 `/<name>` 短命令，描述末尾标注 `[skill]`；mode 字段决定运行时分支：inline 调 `execute_inline` 后再发送一次 user message 触发 loop，fork 则后台 `asyncio.create_task(_run_fork)` 把结果作为 system message 插入
- F13: `/skill list | info <name> | reload` 管理子命令（`mewcode/commands/handlers/skill.py:11`）：list 列出已加载 skill 与来源；info 显示完整 frontmatter 与文件路径；reload 重新扫描三级目录并重新注册命令
- F14: ch10 留下的 `/review` 由 review skill 接管；旧硬编码 handler 仍可保留但优先级被 skill 覆盖

### 目录型 Skill
- F15: 目录布局 `<skill>/SKILL.md` + `<skill>/tool.json` + `<skill>/references/*.py`；`tool.json` 声明该 skill 专属新增的工具 schema（function calling 兼容），LoadSkill 时 `register_skill_tools`（`mewcode/skills/directory.py:104`）把 schema 实例化为 `SkillCustomTool` 注册到 registry，工具实现由 `importlib.util.spec_from_file_location` 动态加载 `references/<tool_name>.py` 内的 `execute` 函数
- F16: `tool.json` 与 `allowed_tools` 职责分离：`tool.json` 负责「向 registry 注册新工具」，`allowed_tools` 负责「skill 执行期间可见工具白名单」；同名工具已存在则跳过注册

### 热更新与清理
- F17: `SkillLoader.get(name)` 每次调用都 `parse_skill_file(source_path)` 重读，文件修改即时生效；解析失败回退 `_cache` 中的旧版本并记 warning（`mewcode/skills/loader.py:103`）
- F18: `/clear` 命令在清对话历史时调 `Agent.clear_active_skills()`（`mewcode/commands/handlers/clear.py:19`）把激活 skill 列表清空

### 内置 Skill
- F19: 四个内置 skill 通过 `importlib.resources` 从 `mewcode/skills/builtins/` 加载：`commit`（inline）、`review`（fork, context: none）、`test`（inline）、`backend-interview`（fork, context: none，目录型自带 `parse_resume` 工具）
- F20: 加载顺序保证磁盘版本可覆盖内置：项目 → 用户 → 内置；`SkillLoader.get_source_label`（`mewcode/skills/loader.py:117`）按路径前缀返回 `project | user | builtin`

## 4. 非功能需求

- N1: 单个 skill 文件解析失败不能阻断其他 skill 加载，错误走 `logging.warning`
- N2: `LoadSkill` 工具调用不弹权限提示（read-only 类别 + `is_system_tool=True`）
- N3: fork 模式必须隔离 `ConversationManager`，主对话状态不被子 Agent 修改
- N4: 工具过滤通过 `filter_tool_registry` 返回新 `ToolRegistry` 实例实现，过滤动态生效不要求重启 Agent
- N5: 内置 skill 与磁盘上同名 skill 冲突时，磁盘版本优先（用户可覆盖内置）
- N6: 目录型 skill 工具实现走 `importlib` 动态加载 `.py` 文件而非 entry point，避免安装步骤

## 5. 设计概要

### 核心数据结构
- `SkillDef`（`mewcode/skills/parser.py:23`）：dataclass，含 `mode / model / context` 三个执行字段 + `source_path / is_directory` 元信息
- `SkillLoader`（`mewcode/skills/loader.py:15`）：name → `SkillDef`；持有 `_skills` 与 `_cache` 两份字典，热更新失败回退缓存
- `SkillExecutor`（`mewcode/skills/executor.py:43`）：`execute_inline(skill, args) -> None` 与 `execute_fork(skill, args) -> str`
- `SkillCustomTool`（`mewcode/skills/directory.py:64`）：动态 Tool 子类，`params_model` 用 `_DynamicParams(extra="allow")`，包裹 `references/*.py` 里的 `execute` 函数
- `LoadSkill`（`mewcode/tools/load_skill.py:21`）：实现 `Tool` 抽象类，`is_system_tool = True`；持有 `SkillLoader` 与 `Agent` 引用
- Agent 新增字段与方法：`active_skills: dict[str, str]`、`_skill_catalog: str`、`activate_skill(name, body)`、`clear_active_skills()`、`set_skill_catalog(catalog)`（`mewcode/agent.py:317-364`）

### 主流程
1. 启动：`MewCodeApp.__init__` → 实例化 `LoadSkill` 并 register → 构造 `Agent` → `SkillLoader(work_dir).load_all()` → `load_skill_tool.set_loader/set_agent` → 构造 `SkillExecutor` → 把 catalog 字符串写入 `agent.set_skill_catalog` → `register_skill_commands` 把每个 skill 注册成 `/<name>`
2. system prompt 注入：`build_environment_context`（`mewcode/prompts.py:277`）每轮迭代重建 environment block，把 `agent._skill_catalog` 与 `agent.active_skills` 字典分别拼为 catalog 段和「## Active Skills」段
3. 主 Agent 循环每轮 `_build_system_message` 调 `build_environment_context(work_dir, active_skills, skill_catalog, agent_catalog)`（`mewcode/agent.py:400`），实现 SOP 钉到 env 的能力
4. 显式调用 `/commit`：`register_skill_commands` 注册的 handler → `executor.execute_inline(skill, args)` → `agent.activate_skill("commit", rendered_body)` → 再 `ctx.ui.send_user_message(trigger)` 触发 Agent loop
5. 意图识别：Agent 调 `LoadSkill({name: "commit"})` → `loader.get` → `agent.activate_skill` + 目录型调 `register_skill_tools` → 返回 `"Skill 'commit' activated. SOP pinned to environment context."`
6. fork 调用 `/review`：handler 走 `asyncio.create_task(_run_fork)` → `executor.execute_fork` 新 conversation + 临时 Agent + 收集 `StreamText` 到 `LoopComplete` → 把 finalText 作为 system message 插入主对话
7. `/clear`：handler → reset conversation → `agent.clear_active_skills()` → 后续轮 environment 不再注入旧 SOP

### 调用链
- 启动：`mewcode.app.MewCodeApp.__init__` → `SkillLoader.load_all` → `register_skill_commands`（`mewcode/app.py:687`）
- inline 显式：用户 `/commit` → command handler → `executor.execute_inline` → `agent.activate_skill` → `ctx.ui.send_user_message` → Agent loop（每轮 env 注入 SOP）
- fork 显式：用户 `/review` → handler → `asyncio.create_task(execute_fork)` → `system message`
- 意图触发：Agent 在某轮调用 `LoadSkill` → `loader.get` → `agent.activate_skill` + register dir tools → 下一轮 SOP 钉在 env 里
- 清理：用户 `/clear` → `handle_clear` → conversation reset + `agent.clear_active_skills`

### 与其他模块的交互
- 上行依赖：`mewcode/app.py`（注入 system prompt、注册命令、注入 `SkillLoader/SkillExecutor` 到 `CommandContext.config`）、`Agent`（`active_skills` 字段 + env 注入）、`ConversationManager`（fork 用独立实例）、`ToolRegistry`（动态注册目录型工具）
- 下行：`SkillExecutor` 通过 `from mewcode.agent import Agent` 局部 import 避免循环依赖；`SkillCustomTool` 通过 `importlib.util` 加载用户脚本，不依赖 entry point

## 6. Out of Scope

- 远程安装 Skill（`InstallSkill` 工具）：Python 版本暂不实现，用户需手动 clone 到 `.mewcode/skills/` 下
- 嵌套深度限制：Skill A → LoadSkill(B) → LoadSkill(C) 不做主动限制，依赖 Agent `max_iterations` 自然封顶
- fork 嵌套跨 Agent 边界的父子链路记录：留给后续 SubAgent 章节
- 目录型 skill 工具的 sandbox：`SkillCustomTool` 执行用户 `.py` 不做沙箱，与本机 Python 同权限运行
- 用户级 `~/.mewcode/skills/` 与项目级冲突时的合并策略：高优先级目录里出现的 name 直接覆盖，不做字段级 merge

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch11: Skill 系统 Tasks（Python 版）

> 顺序执行。每完成一个任务跑 `ruff check mewcode/skills mewcode/tools/load_skill.py` 与 `pytest tests/test_skills.py -q` 确保通过；接入主流程的任务（T10、T11、T12）做完后立刻补一次端到端验证再进下一项。

## T1: 定义 SkillDef 数据结构与 frontmatter 解析

- 影响文件: `mewcode/skills/parser.py`（新建）
- 依赖任务: 无
- 完成标准: dataclass `SkillDef` 含 `name / description / prompt_body / allowed_tools / mode / model / context / source_path / is_directory`；`parse_frontmatter(raw) -> (meta, body)` 处理 `---\n...\n---\n<body>` 格式；`_validate_meta` 校验 `name` 正则 `^[a-z][a-z0-9\-]*$`、`mode in {inline, fork}`、`context in {full, recent, none}`；`SkillParseError` 自定义异常类
- 备注: yaml 库走 `import yaml`（pyyaml）；`substitute_arguments(prompt_body, args)` 简单 `.replace("$ARGUMENTS", args)` 即可

## T2: 实现 SkillLoader 三级搜索与热重载

- 影响文件: `mewcode/skills/loader.py`（新建）
- 依赖任务: T1
- 完成标准:
  - 常量 `PROJECT_SKILLS_DIR = ".mewcode/skills"` / `USER_SKILLS_DIR = "~/.mewcode/skills"`
  - `SkillLoader(work_dir)` 构造时计算 `_project_dir` / `_user_dir`
  - `load_all()` 按 project → user → builtin 顺序扫描，首次出现的 name 保留，后续跳过；维护 `_skills` 与 `_cache` 两份字典
  - `_scan_directory(path, source)` 同时处理 `*.md` 与 `<dir>/SKILL.md` 两种布局，目录型 skill `is_directory = True`
  - `_load_builtins()` 走 `importlib.resources.files("mewcode.skills.builtins")` 遍历子目录
  - `get(name)` 命中后 `parse_skill_file(source_path)` 强制重读；失败回退 `_cache` 中旧版本并 `log.warning`
  - `get_catalog()` 返回 `[(name, description), ...]`；`get_source_label(name)` 按路径前缀返回 `project | user | builtin`
- 备注: 解析失败用 `log.warning("Skipping %s skill '%s': %s", ...)` 不抛出

## T3: 内置 skill 资源

- 影响文件: `mewcode/skills/builtins/__init__.py`（新建空文件）、`mewcode/skills/builtins/commit/SKILL.md`、`mewcode/skills/builtins/commit/__init__.py`、`mewcode/skills/builtins/review/SKILL.md`、`mewcode/skills/builtins/review/__init__.py`、`mewcode/skills/builtins/test/SKILL.md`、`mewcode/skills/builtins/test/__init__.py`、`mewcode/skills/builtins/backend-interview/SKILL.md`、`mewcode/skills/builtins/backend-interview/__init__.py`、`mewcode/skills/builtins/backend-interview/tool.json`、`mewcode/skills/builtins/backend-interview/references/parse_resume.py`
- 依赖任务: T2
- 完成标准:
  - `commit/SKILL.md`：`mode: inline / allowedTools: [Bash, ReadFile, Grep]`，body 描述 git status → diff → conventional commit
  - `review/SKILL.md`：`mode: fork / context: none / allowedTools: [Bash, ReadFile, Grep, Glob]`，body 描述 5 维度审查（逻辑/安全/性能/风格/可维护性）+ Critical/Warning/Info 分级
  - `test/SKILL.md`：`mode: inline / allowedTools: [Bash, ReadFile, Grep, Glob]`，body 描述项目类型检测（`pyproject.toml` → `pytest`、`go.mod` → `go test`、`package.json` → `npm test`、`Cargo.toml` → `cargo test`）+ 区分代码 bug 与测试 bug
  - `backend-interview/`：目录型，`tool.json` 声明 `parse_resume` schema，`references/parse_resume.py` 内 `async def execute(file_path: str = "", **kwargs) -> str` 实现
- 备注: `pyproject.toml` 的 `[tool.setuptools.package-data]` 需要把 `mewcode.skills.builtins` 的 `*.md / *.json` 也打包

## T4: 工具白名单与系统工具豁免

- 影响文件: `mewcode/tools/base.py`（修改，加 `is_system_tool` 字段）、`mewcode/skills/executor.py`（新建，部分实现）
- 依赖任务: T1
- 完成标准:
  - `Tool` 抽象基类增加类属性 `is_system_tool: bool = False`
  - 同文件常量 `SYSTEM_TOOL_NAMES = frozenset({"LoadSkill"})`
  - `SkillDependencyError` 异常类在 `mewcode/skills/executor.py` 定义
  - `filter_tool_registry(registry, allowed)` 返回新 `ToolRegistry`：`allowed` 为空时直接返回原 registry；遍历 `allowed` 缺工具 `raise SkillDependencyError`；扫描原 registry 把 `is_system_tool=True` 的工具自动透传

## T5: SkillExecutor.execute_inline

- 影响文件: `mewcode/skills/executor.py`（继续）
- 依赖任务: T2, T4
- 完成标准: `class SkillExecutor(agent, client, protocol)` 三个属性持有；`execute_inline(skill, args) -> None`：
  - `substitute_arguments(skill.prompt_body, args)`
  - `agent.activate_skill(skill.name, rendered)`
  - 不需要立即调用 LLM，rendered body 钉到 env 后由 command handler 再 `ctx.ui.send_user_message(trigger)` 触发 loop
- 备注: 工具过滤在 fork 路径才动手；inline 走主 registry，由 Agent loop 每轮根据 ActiveSkills 自然限制工具

## T6: SkillExecutor.execute_fork

- 影响文件: `mewcode/skills/executor.py`（继续）
- 依赖任务: T5
- 完成标准: `async execute_fork(skill, args) -> str`：
  - 渲染 prompt
  - 新 `ConversationManager()`
  - 根据 `skill.context` 装填历史：`none` 空 / `recent` 取 `agent._conversation.history` 最近 5 条 user/assistant 消息 / `full` 拼成一段 `"## Previous conversation summary\n\n"` summary 作为单条 user message
  - `fork_conv.add_user_message(rendered)`
  - `filter_tool_registry(agent.registry, skill.allowed_tools)` 失败返回错误字符串
  - 局部 `from mewcode.agent import Agent as AgentClass, StreamText, LoopComplete, ErrorEvent`（避免循环 import）构造临时 Agent，沿用 `client / protocol / work_dir / max_iterations / context_window`
  - `async for event in fork_agent.run(fork_conv)`：`StreamText` 追加文本，`ErrorEvent` 追加错误标记，`LoopComplete` break
  - 返回 `"".join(result_parts)`

## T7: Agent 集成 active_skills 与 skill_catalog

- 影响文件: `mewcode/agent.py`（修改）、`mewcode/prompts.py`（修改）
- 依赖任务: 无（与 T1-T6 并行可做）
- 完成标准:
  - `Agent.__init__` 增加 `self.active_skills: dict[str, str] = {}` 与 `self._skill_catalog: str = ""`
  - 方法 `activate_skill(name, prompt_body)` / `clear_active_skills()` / `set_skill_catalog(catalog)`
  - 每轮 `_build_system_message`（或同等位置）调用 `build_environment_context(work_dir, active_skills, skill_catalog, agent_catalog)`
  - `mewcode/prompts.py` 的 `build_environment_context` 拼接：先写 `skill_catalog` 段落，再写 `## Active Skills` 标题 + `### Skill: <name>\n<sop>` 子段

## T8: LoadSkill 工具

- 影响文件: `mewcode/tools/load_skill.py`（新建）
- 依赖任务: T2, T7
- 完成标准:
  - `LoadSkill` 继承 `Tool`，`name = "LoadSkill"`、`description` 描述「按需激活 skill」、`params_model = LoadSkillParams(name: str)`、`category = "read"`、`is_concurrency_safe = False`、`is_system_tool = True`
  - 持有 `_loader` 与 `_agent` 私有属性；`set_loader(loader)` / `set_agent(agent)` 注入器
  - `execute(params)`：
    - 未初始化返回 `is_error=True` 的「LoadSkill not properly initialized」
    - `self._loader.get(params.name)` 为 None 时列出 catalog 返回错误
    - 调 `self._agent.activate_skill(skill.name, skill.prompt_body)`
    - 目录型且 `source_path is not None` 时局部 import `register_skill_tools` 并调用，count 累加
    - 返回 `"Skill '<name>' activated. SOP pinned to environment context."` + 若有工具 `" N specialized tool(s) registered."`

## T9: 目录型 Skill 工具注册

- 影响文件: `mewcode/skills/directory.py`（新建）
- 依赖任务: T8
- 完成标准:
  - `parse_tool_json(path) -> list[dict]`：`json.loads`，支持单 dict 包装成 list，失败 warning 后返回空 list
  - `load_tool_implementation(references_dir, tool_name) -> Callable | None`：`importlib.util.spec_from_file_location("mewcode_skill_tool_<name>", references_dir / f"{tool_name}.py")` 动态加载，读取 `execute` 函数；找不到/失败时 warning 后返回 None
  - `_DynamicParams(BaseModel)` 配 `model_config = {"extra": "allow"}` 用作动态参数模型
  - `SkillCustomTool(tool_name, description, schema, impl)` 继承 `Tool`：`get_schema` 用 `schema["parameters"]` 或 `schema["input_schema"]` 作为 `input_schema`；`execute(params)` 检查 `impl` 是否为协程，分别 `await impl(**kwargs)` 或 `impl(**kwargs)`，包成 `ToolResult(output=str(result))`，异常包成 `is_error=True`
  - `register_skill_tools(skill_dir, registry) -> int`：找 `tool.json` 没有返回 0；遍历 schemas，跳过同名已注册，新建 `SkillCustomTool` 注册并 +1

## T10: 接入 app.py —— 加载 + Catalog 注入 + 命令注册

- 影响文件: `mewcode/app.py`（修改）
- 依赖任务: T2, T3, T5, T6, T7, T8
- 完成标准:
  - import `SkillLoader / SkillExecutor / register_skill_commands / LoadSkill`
  - `MewCodeApp.__init__` 字段 `self.skill_loader / self.skill_executor / self._load_skill_tool`
  - 先 `LoadSkill()` 实例化注册到 `self.registry`，再构造 `Agent`（保证 registry 已含 LoadSkill）
  - `SkillLoader(work_dir).load_all()` 加载 catalog
  - `load_skill_tool.set_loader(self.skill_loader)` / `set_agent(self.agent)` 注入
  - `SkillExecutor(agent=..., client=..., protocol=...)` 构造
  - 把 catalog 拼成 `"You can use the following Skills:\n\n- <name>: <desc>\n...\nIf the user's request matches a Skill, call LoadSkill to activate it."` 调 `self.agent.set_skill_catalog(...)`
  - `register_skill_commands(self.command_registry, self.skill_loader, self.skill_executor)`
  - `CommandContext.config` 字典塞入 `"skill_loader" / "skill_executor"` 供 handler 取用

## T11: 接入 commands —— `/skill` 管理 + skill 命令 + `/clear` 钩

- 影响文件: `mewcode/commands/handlers/skill.py`（新建）、`mewcode/commands/handlers/skill_register.py`（新建）、`mewcode/commands/handlers/clear.py`（修改）、`mewcode/commands/handlers/__init__.py`（注册 SKILL_COMMAND）
- 依赖任务: T10
- 完成标准:
  - `SKILL_COMMAND` 提供 `/skill list | info <name> | reload` 三档：
    - list：遍历 catalog，每行 `f"  {name:<20} {desc}  [{source}]"`
    - info：拉 `loader.get(name)` 输出完整 frontmatter + path + directory 标记
    - reload：`loader.reload()` 后调用 `register_skill_commands` 重建命令
  - `register_skill_commands(registry, loader, executor)`：模块级集合 `_REGISTERED_SKILL_NAMES` 跟踪本次会话已注册的 skill 命令，再次调用先清掉旧的；inline skill 命令 handler `execute_inline` 后调 `ctx.ui.send_user_message(trigger)`；fork skill 命令 handler 走 `asyncio.create_task(_run_fork)`，结果作为 system message
  - `clear.py` 的 `handle_clear` 增加 `if ctx.agent: ctx.agent.clear_active_skills()`

## T12: 接入主流程 —— 端到端走通

- 影响文件: 无（仅运行验证）
- 依赖任务: T1-T11
- 完成标准:
  - `pytest tests/test_skills.py -q` 全部通过
  - 在仓库根目录手动启动 `python -m mewcode`：
    1. `/help` 列出 `/commit`、`/review`、`/test`、`/backend-interview`、`/skill` 命令
    2. `/skill list` 输出 4 个 skill 名 + builtin 来源
    3. `/skill info commit` 输出 mode / context / model / allowedTools / source
    4. 改一处源码后 `/commit`，看到 Agent 走 git status → diff → commit
    5. `/review` 走 fork 路径，主对话不污染，末尾收到 assistant 摘要
    6. 「帮我准备一下后端面试」自然语言触发 `LoadSkill({name: "backend-interview"})`，env-reminder 出现 SOP
    7. `/clear` 后 env-reminder 不再出现旧 SOP
    8. `.mewcode/skills/commit.md` 改一行后**不重启**再 `/commit`，新行进入 prompt（热重载验证）

## T13: 单元测试

- 影响文件: `tests/test_skills.py`（新建）
- 依赖任务: T1-T11
- 完成标准: 覆盖
  - parser：valid / missing opening / unclosed / invalid yaml / non-dict / missing name / missing description / invalid name format / invalid mode / nonexistent file / fork mode with context
  - substitute_arguments：with / without args / no placeholder / multiple
  - loader：内置加载 / 项目覆盖内置 / catalog / get / get_unknown / 热重载成功 / 热重载失败回退 / 目录型识别 / source_label / 失败文件跳过 / reload
  - filter_tool_registry：empty allowed / 过滤 / 系统工具透传 / 缺工具抛错
  - directory：parse_tool_json list / single object / register_skill_tools / 无 tool.json / 动态工具实际可执行
  - LoadSkill：load existing / load unknown / 未初始化 / `is_system_tool` 与 `category="read"`
  - Agent 集成：`build_environment_context` 含 / 不含 Active Skills 段 / `activate_skill` 后字典含 name / `clear_active_skills` 清空
- 备注: 用 `unittest.mock.MagicMock / AsyncMock` 替代真实 Agent；`pytest.mark.asyncio` 配 `pytest-asyncio`

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
- [ ] T13
```
```plain
# ch11: Skill 系统 Checklist（Python 版）

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。操作目录在仓库根 `/Users/codemelo/mewcode`。

## 1. 实现完整性

### 1.1 解析与加载

- [ ] `mewcode/skills/parser.py:23` `SkillDef` 含字段 `name / description / prompt_body / allowed_tools / mode / model / context / source_path / is_directory`（`grep -n "class SkillDef" mewcode/skills/parser.py` 命中）
- [ ] `mewcode/skills/parser.py:36` `parse_frontmatter(raw) -> (dict, str)` 处理 `---\n...\n---` 格式
- [ ] `mewcode/skills/parser.py:57` `_validate_meta` 校验 `name` 正则 + `mode in {inline, fork}` + `context in {full, recent, none}`
- [ ] `mewcode/skills/parser.py:99` `substitute_arguments(prompt_body, args)` 实现 `$ARGUMENTS` 替换
- [ ] `mewcode/skills/loader.py:15` `SkillLoader(work_dir)` 实现三级搜索（`grep -n "PROJECT_SKILLS_DIR\|USER_SKILLS_DIR\|_load_builtins" mewcode/skills/loader.py` 命中 ≥3 处）
- [ ] `mewcode/skills/loader.py:96` `get(name)` 每次重读源文件实现热重载，失败回退 `_cache` 并 `log.warning`
- [ ] `mewcode/skills/loader.py:117` `get_source_label(name)` 按 `_project_dir / _user_dir` 前缀返回 `project | user | builtin`

### 1.2 内置 skill

- [ ] `mewcode/skills/builtins/commit/SKILL.md` 存在，frontmatter `mode: inline / allowedTools: [Bash, ReadFile, Grep]`
- [ ] `mewcode/skills/builtins/review/SKILL.md` 存在，frontmatter `mode: fork / context: none / allowedTools: [Bash, ReadFile, Grep, Glob]`，body 含「Critical」「Warning」「Info」分级
- [ ] `mewcode/skills/builtins/test/SKILL.md` 存在，frontmatter `mode: inline / allowedTools: [Bash, ReadFile, Grep, Glob]`，body 含 `pyproject.toml` 与 `go.mod` 检测
- [ ] `mewcode/skills/builtins/backend-interview/SKILL.md` 存在 + `tool.json` 声明 `parse_resume` + `references/parse_resume.py` 含 `async def execute(file_path: str = "", **kwargs)`
- [ ] `mewcode/skills/loader.py:65` `_load_builtins` 使用 `importlib.resources.files("mewcode.skills.builtins")` 遍历

### 1.3 Executor

- [ ] `mewcode/skills/executor.py:43` 含 `class SkillExecutor` 与 `execute_inline / execute_fork` 两个方法
- [ ] inline 调用链：`substitute_arguments` → `agent.activate_skill(name, body)`（`grep -n "activate_skill" mewcode/skills/executor.py` 命中）
- [ ] fork 调用链：新 `ConversationManager` → `_build_fork_context(context)` 按 `full / recent / none` 三档装填 → `filter_tool_registry` 过滤工具 → 临时 Agent run → 收集 `StreamText` 到 `LoopComplete`
- [ ] `mewcode/skills/executor.py:25` `filter_tool_registry(registry, allowed)` 缺工具 `raise SkillDependencyError`，系统工具自动透传

### 1.4 Agent 集成

- [ ] `mewcode/agent.py:317` Agent 含 `self.active_skills: dict[str, str] = {}`
- [ ] `mewcode/agent.py:357` `activate_skill(name, prompt_body)` 实现
- [ ] `mewcode/agent.py:360` `clear_active_skills()` 实现
- [ ] `mewcode/agent.py:363` `set_skill_catalog(catalog)` 实现
- [ ] `mewcode/agent.py:400` 主循环每轮调用 `build_environment_context(work_dir, active_skills, skill_catalog, agent_catalog)`
- [ ] `mewcode/prompts.py:277` `build_environment_context` 把 `active_skills` 拼成 `## Active Skills` 段；`skill_catalog` 拼到 environment block

### 1.5 LoadSkill 工具与系统工具豁免

- [ ] `mewcode/tools/load_skill.py:21` 含 `class LoadSkill(Tool)`，`name = "LoadSkill"`、`category = "read"`、`is_system_tool = True`
- [ ] `mewcode/tools/load_skill.py:39` `set_loader / set_agent` 注入方法
- [ ] `mewcode/tools/load_skill.py:46` `execute` 调 `loader.get → agent.activate_skill → register_skill_tools`（目录型）→ 返回 `"Skill '<name>' activated. SOP pinned to environment context."`
- [ ] `mewcode/tools/base.py:28` `Tool.is_system_tool: bool = False` 类属性
- [ ] `mewcode/skills/executor.py:14` `SYSTEM_TOOL_NAMES = frozenset({"LoadSkill"})` 常量
- [ ] `filter_tool_registry` 应用 `allowed_tools` 时不剔除 `is_system_tool=True` 的工具（`grep -n "is_system_tool" mewcode/skills/executor.py` 命中）

### 1.6 目录型 skill

- [ ] `mewcode/skills/directory.py:17` `parse_tool_json(path)` 支持 list 与单 dict 两种格式
- [ ] `mewcode/skills/directory.py:34` `load_tool_implementation` 用 `importlib.util.spec_from_file_location` 动态加载 `references/<name>.py` 内的 `execute` 函数
- [ ] `mewcode/skills/directory.py:64` `SkillCustomTool` 继承 `Tool`，`params_model = _DynamicParams`（`extra="allow"`）
- [ ] `mewcode/skills/directory.py:104` `register_skill_tools(skill_dir, registry) -> int` 遍历 tool.json，注册成功 +1，重名跳过
- [ ] `backend-interview` 的 `parse_resume` 工具能通过 `register_skill_tools` 注册到 registry（见 `tests/test_skills.py` `test_register_skill_tools`）

### 1.7 命令集成

- [ ] 每个 skill 自动注册为 `/<name>` 命令，描述末尾含 `[skill]`（`grep -n "\[skill\]" mewcode/commands/handlers/skill_register.py` 命中）
- [ ] `mewcode/commands/handlers/skill_register.py:18` `register_skill_commands(registry, loader, executor)` 实现；模块级 `_REGISTERED_SKILL_NAMES` 跟踪重复注册
- [ ] inline skill 命令 handler 调 `executor.execute_inline` 后再 `ctx.ui.send_user_message(trigger)`
- [ ] fork skill 命令 handler 走 `asyncio.create_task(_run_fork)`，结果作为 `add_system_message` 插入
- [ ] `mewcode/commands/handlers/skill.py:11` `/skill list | info <name> | reload` 子命令分发
- [ ] `mewcode/commands/handlers/clear.py:19` `handle_clear` 调用 `ctx.agent.clear_active_skills()`

## 2. 接入完整性（杜绝死代码）

- [ ] `grep -rn "SkillLoader" mewcode/app.py` 命中 ≥2 处（import + 实例化）
- [ ] `grep -rn "activate_skill" mewcode/` 命中 Agent 方法定义 + Executor + LoadSkillTool 三处调用
- [ ] `grep -rn "clear_active_skills" mewcode/` 命中 `/clear` handler 调用 + Agent 方法定义
- [ ] `grep -rn "LoadSkill\|\"LoadSkill\"" mewcode/` 命中 tool 定义 + app 注册 + 至少 1 个测试
- [ ] `grep -rn "SkillExecutor\|register_skill_commands" mewcode/` 命中 app.py 注册 + handler 模块
- [ ] `grep -rn "execute_inline\|execute_fork" mewcode/skills/` 命中 Executor 定义 + handler 调用
- [ ] `grep -rn "loader.get\|SkillLoader.get" mewcode/tools/load_skill.py` 命中 1 处
- [ ] `grep -rn "is_system_tool" mewcode/` 命中 base.py 定义 + executor filter 检查 + LoadSkill 实现
- [ ] `mewcode/app.py:556` 存在 `self.skill_loader` / `self.skill_executor` / `self._load_skill_tool` 字段
- [ ] `mewcode/app.py:885` `CommandContext.config` 字典塞入 `"skill_loader"` 与 `"skill_executor"` key

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && ruff check mewcode/skills mewcode/tools/load_skill.py` 无 error
- [ ] `cd /Users/codemelo/mewcode && pytest tests/test_skills.py -q` 全部通过
- [ ] `cd /Users/codemelo/mewcode && pytest tests/test_agent.py -q` 全部通过
- [ ] `cd /Users/codemelo/mewcode && python -c "from mewcode.skills.loader import SkillLoader; l = SkillLoader('/tmp'); print(list(l.load_all().keys()))"` 输出含 `commit / review / test / backend-interview`
- [ ] `cd /Users/codemelo/mewcode && python -c "from mewcode.tools.load_skill import LoadSkill; t = LoadSkill(); print(t.name, t.category, t.is_system_tool)"` 输出 `LoadSkill read True`

## 4. 端到端验证（手动操作 TUI）

> 启动命令：`cd /Users/codemelo/mewcode && python -m mewcode`

- [ ] 启动后输 `/help`，看到 `/commit [skill]` / `/review [skill]` / `/test [skill]` / `/backend-interview [skill]` / `/skill` 都列出
- [ ] 输 `/skill list`，输出含 4 个 skill 名称 + 来源（builtin / project / user）
- [ ] 输 `/skill info commit`，输出含完整 frontmatter（mode / context / model / AllowedTools / Source / Path）
- [ ] 改一处真实文件（如修个空格），输 `/commit`，看到 Agent 真的走 git status → diff → 生成 commit message → git add → git commit；`git log -1` 看到新 commit
- [ ] 输 `/review`，看到 fork 路径执行：主对话不污染；末尾以 `[review skill result]` 开头收到摘要含 Critical/Warning/Info 分级
- [ ] 自然语言 `"帮我准备一下后端面试"`，Agent tool_use 里出现 `LoadSkill({name: "backend-interview"})` 并且 environment 段里出现该 skill 的 SOP
- [ ] 输 `/clear`，立即输任意消息，environment 段里**不再出现** `## Active Skills`
- [ ] 修改 `.mewcode/skills/<name>.md` 一行（如自建一个 `custom.md`），**不重启** TUI，再 `/custom`，看到新行进入 prompt（热重载验证）
- [ ] 创建 `.mewcode/skills/bad.md` 故意写错 frontmatter，启动日志出现 `Skipping ... skill 'bad': ...` warning，其他 skill 仍正常加载
- [ ] LoadSkill 工具调用时**不**弹权限提示（`category=read` + `is_system_tool=True`）

## 5. 文档

- [ ] `docs/python/ch11/spec.md` 更新到课程全量版（不是验收版）
- [ ] `docs/python/ch11/tasks.md` 13 个任务全部勾上
- [ ] `docs/python/ch11/checklist.md` 全部条目勾上
- [ ] commit 信息：`feat(ch11): full skill system per course design (python) [spec/tasks/checklist closed]`
```

### Java

```plain
# ch11: Skills 系统 Spec

## 1. 背景

Slash Command 让用户绕过 LLM 直接触发本地动作，但所有 handler 都硬编码在源码里：想加一个 `/commit` 让 Agent 自动分析 diff、生成 message、提交，就得改 Java 再重编。Slash Command 是确定性的快车道，Skill 系统则把可扩展性补上——用户在 `.mewcode/skills/<name>/` 或 `~/.mewcode/skills/<name>/` 放一个 `SKILL.md`（可选 frontmatter）或 `skill.yaml + prompt.md`，启动时被发现并注册成提示型命令，运行时按 inline 或 fork 模式注入 SOP，让 Agent 借助 LLM 能力完成更复杂的工作流。

## 2. 目标

交付一套进程内的技能编目与执行链路：`SkillCatalog` 三层扫描（builtin + 用户全局 `~/.mewcode/skills/` + 项目 `.mewcode/skills/`）发现技能；phase-1 仅读 frontmatter 加快启动，`getFull` 触发 phase-2 重读 body 实现热更新；`SkillExecutor` 提供 `executeInline` 与 `executeFork` 两种执行模式，前者把 SOP 注入主 Agent 并按 `allowed_tools` 过滤工具，后者跑隔离的子 Agent，按 `fork_context`（none / recent / full）决定父消息种子；`SkillHost` / `SkillForkHost` 通过接口而非具体类把 Agent 状态切片暴露给 executor，避免 `com.mewcode.skill` 反向依赖 agent 包。`MewCodeModel` 在 provider 就绪后调用 `loadFromDirectory` 加载项目目录，再把每个技能注册为 PROMPT 类型的 Slash Command，输入 `/<skill-name>` 时把 promptBody 当作 user message 发给 LLM，UI 上紧跟 `Successfully loaded skill` 系统消息。

## 3. 功能需求

- F1: `SkillCatalog` 暴露 `register / get / getFull / list / source / reload / loadCatalog / loadFromDirectory / buildActiveContext` 方法，内部 `skills` 与 `sources` 用 `LinkedHashMap` 保序。
- F2: 三层目录加载 `loadCatalog(workDir)`：tier 1 builtin（占位，由 agent 层装入）、tier 2 用户 `~/.mewcode/skills/`、tier 3 项目 `<workDir>/.mewcode/skills/`，按名字后者覆盖前者。
- F3: 单技能加载策略两选一：优先 `skill.yaml + prompt.md`（`loadFromYamlAndPrompt`），否则 `SKILL.md`（`parseSkillMD`，可选 YAML frontmatter，缺描述时回退到 body 第一行非标题）。
- F4: `getFull(name)` 触发热重载：对 `sourceDir != null` 的技能每次重读 body，读失败时保留旧缓存，避免编辑过程中读到半成品。
- F5: `SkillMeta` 字段包含 `name / description / whenToUse / tags / allowedTools / mode / model / forkContext`；name 缺省时取目录名小写化并把空格换 `-`；mode 缺省 `inline`，向后兼容 `context: fork`；`fork_context` 缺省 `none`。
- F6: `SkillExecutor.executeInline(skill, args, host)`：先 `assertAllowedToolsExist` 校验白名单工具均在 `ToolRegistry`；再 `substituteArguments` 渲染 prompt；最后通过 `host.activateSkill` 注入 SOP 并按 `allowed_tools` 调 `host.setToolFilter`，返回渲染后的 body。
- F7: `SkillExecutor.executeFork(skill, args, host)`：构造 prompt + `buildForkSeed` 种子消息，调 `host.runSubAgent` 起隔离子 Agent，把最终 assistant 文本回传。
- F8: `substituteArguments(body, args)`：args 为空原样返回；body 含 `$ARGUMENTS` 时占位符替换；否则追加 `## User Request` 段。
- F9: `buildForkSeed(mode, parent)`：`full` 全量拷贝；`recent` 取尾部最多 5 条；其他（含 `none`）返回空。
- F10: `SkillHost` / `SkillForkHost` 接口：`activateSkill / setToolFilter / toolRegistry` 由 TUI/Agent 层实现；fork 主机额外提供 `runSubAgent / snapshotParentMessages`。
- F11: `MewCodeModel.wireSkillsToAgent` 把 catalog 内每个技能注册为 PROMPT 命令，description 后缀 `[skill]` 用作分支判断；handler 返回 `promptBody`，executeCommand 在 PROMPT 分支把它当 user message。
- F12: PROMPT 分发命中 `[skill]` 后缀时，在 UI 上追加 `skill(<name>) Successfully loaded skill` 系统消息，提示用户技能已激活。

## 4. 非功能需求

- N1: `loadTier` 必须容错：目录缺失、不可读、单个技能解析失败都不中断其他技能。
- N2: phase-1 加载不能读 body：仅 frontmatter / yaml meta，避免大文件拖慢启动；body 由 `getFull` 按需加载。
- N3: `parseSkillMD` 的 YAML 解析失败要降级到「无 frontmatter」分支而不是抛异常。
- N4: `com.mewcode.skill` 不允许 import `com.mewcode.agent` / `com.mewcode.tui`——通过 `SkillHost` / `SkillForkHost` 接口反向解耦。
- N5: `assertAllowedToolsExist` 在工具未注册时抛 `IllegalStateException`，让上层在执行前暴露配置错误，而不是运行到一半才失败。
- N6: `register(skill)` 允许同名覆盖，调用方按 tier 顺序决定优先级（后注册者胜出）。
- N7: 注册成 PROMPT 命令时 `description` 必须以 `[skill]` 结尾，作为 UI 分支识别 marker。

## 5. 设计概要

- 核心数据结构:
 - `SkillCatalog.Skill`：record(`meta`, `promptBody`, `sourceDir`, `bodyLoaded`)，`withBody` 返回带新 body 的副本
 - `SkillCatalog.SkillMeta`：record(name, description, whenToUse, tags, allowedTools, mode, model, forkContext)
 - `SkillCatalog` 内部 `Map<String, Skill> skills` + `Map<String, String> sources` 全部 `LinkedHashMap`
 - `SkillHost`：`activateSkill(name, body)` + `setToolFilter(Predicate<String>)` + `toolRegistry()`
 - `SkillForkHost extends SkillHost`：追加 `runSubAgent(body, seed, allowedTools, model)` + `snapshotParentMessages()`
- 主流程（启动期）:
 1. `MewCode.main` 装好配置 → 构造 `MewCodeModel`
 2. provider 就绪后（`MewCodeModel` line 494-498）`new SkillCatalog()` + `loadFromDirectory(<workDir>/.mewcode/skills)`
 3. `wireSkillsToAgent`（line 511-516）遍历 `list()`，对每个 meta 调 `registerSkillCommand`
 4. `registerSkillCommand`（line 518-533）跳过已有命令、把技能注册为 PROMPT 类型的 `Command`，handler 在执行时从 catalog 取 `promptBody`
- 主流程（运行期 inline 模式）:
 1. 用户输入 `/<skill-name> <args>` → `executeCommand` → PROMPT 分支
 2. `cmdRegistry.execute` 返回 promptBody → `conversation.addUserMessage(promptBody)` → 若有 args 追加 `conversation.addUserMessage(args)`
 3. `agent.run` 启动新一轮 → UI 推送 `skill(<name>) Successfully loaded skill` 系统消息
 4. 后续 turn 与普通 Agent loop 一致
- 主流程（运行期 fork 模式 / Executor 直调）:
 1. 调用方持 `SkillForkHost` 实例，调用 `SkillExecutor.executeFork(skill, args, host)`
 2. `assertAllowedToolsExist` 校验工具白名单 → `substituteArguments` 渲染 prompt
 3. `buildForkSeed(skill.forkContext, host.snapshotParentMessages())` 决定种子消息
 4. `host.runSubAgent` 跑隔离 Agent，回最终文本
- 调用链:
 - 启动: `MewCode.main` → `MewCodeModel` 构造 → provider 就绪回调 → `new SkillCatalog().loadFromDirectory` → `wireSkillsToAgent` → `cmdRegistry.register`
 - 执行 inline: TUI `executeCommand`(PROMPT) → `cmdRegistry.execute` → catalog handler → 返回 promptBody → conversation → agent
 - 执行 fork（programmatic）: 外部调用 `SkillExecutor.executeFork` → `host.runSubAgent`
- 与其他模块的交互:
 - 上行: `com.mewcode.tui.MewCodeModel`（注册 / 分发 / UI 提示）、`com.mewcode.command.CommandRegistry`（命令注册）
 - 下行: `com.mewcode.conversation.Message`（fork 种子）、`com.mewcode.tool.ToolRegistry`（白名单校验）
 - 接口反转: `SkillHost` / `SkillForkHost` 由 TUI / agent 层实现，避免循环依赖

## 6. Out of Scope

- Builtin skill 真正加载（当前 tier 1 是占位，由 agent 层装入，本章不实现具体内置技能集）
- Skill 远程仓库 / 包管理：用户必须手动放文件到指定目录
- Skill 权限模型：fork 模式不再二次校验权限，沿用父 Agent 的 PermissionChecker
- Skill 链式调用 / pipeline：一次只能激活一个技能
- 文件 watcher 自动热加载目录新增技能：`getFull` 仅热重载已注册技能的 body，目录新增需 `reload(workDir)` 或重启
- Skill 配额 / 计费 / 超时控制：fork 模式不限制子 Agent 步数

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch11: Skills 系统 Tasks

## T1: 定义 SkillCatalog 数据类型与状态
- 影响文件: `src/main/java/com/mewcode/skill/SkillCatalog.java`
- 依赖任务: 无
- 完成标准: `SkillMeta` / `Skill` record 字段齐全；`Skill.withBody` 副本构造可用；内部 `skills` / `sources` 用 `LinkedHashMap` 保序；`register / get / list / source` 行为对齐参考。
- 实际产出: `SkillCatalog.java:24-39`（record）、`SkillCatalog.java:43-45`（state）、`SkillCatalog.java:49-97`（公共方法）

## T2: 实现单技能加载策略
- 影响文件: `src/main/java/com/mewcode/skill/SkillCatalog.java`
- 依赖任务: T1
- 完成标准: `loadSkill(dir)` 优先 `skill.yaml + prompt.md`，否则 `SKILL.md`；`loadFromYamlAndPrompt` 用 snakeyaml 解析 meta + 读取 prompt.md；`parseSkillMD` 处理可选 frontmatter，缺描述时回退到 body 第一行非标题行。
- 实际产出: `SkillCatalog.java:184-199`（loadSkill）、`SkillCatalog.java:201-219`（loadFromYamlAndPrompt）、`SkillCatalog.java:221-262`（parseSkillMD）、`SkillCatalog.java:264-313`（metaFromMap）

## T3: 实现三层目录加载与热重载
- 影响文件: `src/main/java/com/mewcode/skill/SkillCatalog.java`
- 依赖任务: T1, T2
- 完成标准: `loadCatalog(workDir)` 按 builtin → 用户 → 项目顺序加载，后者覆盖前者；`loadTier` 容错；`getFull` 触发 phase-2 重读 body，读失败保留旧缓存；`reload(workDir)` 整体刷新。
- 实际产出: `SkillCatalog.java:107-123`（loadCatalog）、`SkillCatalog.java:125-132`（reload）、`SkillCatalog.java:138-158`（loadFromDirectory + loadTier）、`SkillCatalog.java:66-89`（getFull）

## T4: 定义 SkillHost / SkillForkHost 接口
- 影响文件: `src/main/java/com/mewcode/skill/SkillHost.java`, `src/main/java/com/mewcode/skill/SkillForkHost.java`
- 依赖任务: 无
- 完成标准: `SkillHost.activateSkill(name, body) / setToolFilter(Predicate<String>) / toolRegistry()`；`SkillForkHost extends SkillHost` 增加 `runSubAgent(body, seed, allowedTools, model) / snapshotParentMessages()`。
- 实际产出: `SkillHost.java:12-19`、`SkillForkHost.java:12-17`

## T5: 实现 SkillExecutor（inline / fork 双模式）
- 影响文件: `src/main/java/com/mewcode/skill/SkillExecutor.java`
- 依赖任务: T1, T4
- 完成标准: `executeInline(skill, args, host)` 校验工具白名单 + 渲染 prompt + `activateSkill` + `setToolFilter`；`executeFork(skill, args, host)` 渲染 prompt + `buildForkSeed` + `runSubAgent`；`substituteArguments` 处理 `$ARGUMENTS` 占位符与缺占位符追加 `## User Request`；`buildForkSeed` 支持 `none / recent (≤5) / full`。
- 实际产出: `SkillExecutor.java:25-37`（executeInline）、`SkillExecutor.java:43-48`（executeFork）、`SkillExecutor.java:50-58`（substituteArguments）、`SkillExecutor.java:60-74`（buildForkSeed）、`SkillExecutor.java:76-88`（assertAllowedToolsExist）

## T6: buildActiveContext 系统提示注入助手
- 影响文件: `src/main/java/com/mewcode/skill/SkillCatalog.java`
- 依赖任务: T1
- 完成标准: `buildActiveContext(Set<String> activeSkillNames)` 在系统提示里拼 `## Active Skills` 段 + 每个技能的 `### name` + body；空集合返回空串。
- 实际产出: `SkillCatalog.java:166-180`

## T7: 接入主流程 —— TUI 加载技能 / 注册为命令
- 影响文件: `src/main/java/com/mewcode/tui/MewCodeModel.java`
- 依赖任务: T1, T3
- 完成标准: provider 就绪后构造 `SkillCatalog` + `loadFromDirectory(<workDir>/.mewcode/skills)`；`wireSkillsToAgent` 遍历 `list()` 调 `registerSkillCommand`；`registerSkillCommand` 跳过已存在命令，注册 PROMPT 类型 `Command`，description 以 `[skill]` 结尾，handler 从 catalog 取 `promptBody`。
- 实际产出: `MewCodeModel.java:102`（字段）、`MewCodeModel.java:494-500`（加载）、`MewCodeModel.java:511-516`（wireSkillsToAgent）、`MewCodeModel.java:518-533`（registerSkillCommand）

## T8: 接入主流程 —— PROMPT 分发的 skill 分支
- 影响文件: `src/main/java/com/mewcode/tui/MewCodeModel.java`
- 依赖任务: T7
- 完成标准: `executeCommand` 命中 PROMPT 类型时判断 description 是否以 `[skill]` 结尾；是则把 promptBody 当 user message 推入 conversation、附加 args、起 agent.run，并在 UI 上 println `skill(<name>) Successfully loaded skill`；`/skills` 命令列出当前 catalog。
- 实际产出: `MewCodeModel.java:928-967`（PROMPT 分支）、`CommandRegistry.java:255-265`（/skills handler）、`MewCodeModel.java:984-986`（skillList supplier）

## T9: 端到端验证
- 影响文件: 无
- 依赖任务: T7, T8
- 完成标准: `./gradlew build` 通过；在 `.mewcode/skills/demo/SKILL.md` 放最小 frontmatter（name: demo, description: demo skill）+ body，启动 MewCode 后 `/skills` 列出 `demo`；输入 `/demo hello` 触发 PROMPT 分发，UI 显示 `skill(demo) Successfully loaded skill`，Agent 收到 promptBody + `hello` 作为新对话起点；`origin/java` 仓库已自带 `.mewcode/skills/skill-creator/SKILL.md` 可作真实样本。
- 实际产出: `./gradlew build` 全绿、`MewCodeModel.java:494-500` 启动加载、`MewCodeModel.java:961-965` UI 提示

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
```
```plain
# ch11: Skills 系统 Checklist

## 1. 实现完整性

- [ ] `SkillCatalog.SkillMeta` record 在 `src/main/java/com/mewcode/skill/SkillCatalog.java:24-33` 含 `name / description / whenToUse / tags / allowedTools / mode / model / forkContext` 八个字段
- [ ] `SkillCatalog.Skill` record 在 `SkillCatalog.java:35-39` 含 `meta / promptBody / sourceDir / bodyLoaded`，提供 `withBody` 副本构造
- [ ] `SkillCatalog` 状态在 `SkillCatalog.java:43-45`：`skills / sources` 全部 `LinkedHashMap` 保序
- [ ] `register / get / getFull / list / source / reload / loadFromDirectory` 在 `SkillCatalog.java:49-158` 实现
- [ ] `getFull` 在 `SkillCatalog.java:71-89` 触发 phase-2 热重载，sourceDir 为 null 直接返回缓存，读失败 `IOException ignored` 后保留旧缓存
- [ ] `loadCatalog(workDir)` 在 `SkillCatalog.java:107-123` 按 tier1 builtin（占位）→ tier2 `~/.mewcode/skills/` → tier3 `<workDir>/.mewcode/skills/` 顺序加载
- [ ] `loadTier` 在 `SkillCatalog.java:142-158` 容错：目录不存在 / list 抛 IOException 都静默跳过
- [ ] `loadSkill(dir)` 在 `SkillCatalog.java:184-199` 优先 `skill.yaml + prompt.md`，否则 `SKILL.md`，都不存在返回 null
- [ ] `parseSkillMD` 在 `SkillCatalog.java:221-262` 处理可选 YAML frontmatter；YAML 解析失败降级为「无 frontmatter」；缺描述时从 body 第一行非标题行回退
- [ ] `metaFromMap` 在 `SkillCatalog.java:264-313`：name 缺省取目录名小写+空格换 `-`；mode 缺省 `inline` 并兼容 `context: fork`；`fork_context` 缺省 `none`
- [ ] `buildActiveContext(activeSkillNames)` 在 `SkillCatalog.java:166-180` 拼 `## Active Skills` 段，空集合返回 ""
- [ ] `SkillHost` 接口在 `src/main/java/com/mewcode/skill/SkillHost.java:12-19` 提供 `activateSkill / setToolFilter / toolRegistry`
- [ ] `SkillForkHost extends SkillHost` 在 `src/main/java/com/mewcode/skill/SkillForkHost.java:12-17` 追加 `runSubAgent / snapshotParentMessages`
- [ ] `SkillExecutor.executeInline` 在 `src/main/java/com/mewcode/skill/SkillExecutor.java:25-37` 顺序：`assertAllowedToolsExist` → `substituteArguments` → `activateSkill` → 按 `allowed_tools` 调 `setToolFilter`
- [ ] `SkillExecutor.executeFork` 在 `SkillExecutor.java:43-48` 顺序：校验 → 渲染 → `buildForkSeed` → `runSubAgent`
- [ ] `substituteArguments` 在 `SkillExecutor.java:50-58`：args 空白原样返回；含 `$ARGUMENTS` 占位符替换；否则追加 `## User Request` 段
- [ ] `buildForkSeed` 在 `SkillExecutor.java:60-74`：`full` 全量、`recent` 取尾 5 条（`FORK_RECENT_COUNT = 5`）、其他（含 `none`）返回 `List.of()`
- [ ] `assertAllowedToolsExist` 在 `SkillExecutor.java:76-88` 工具未注册时抛 `IllegalStateException`
- [ ] 边界处理: 空目录、目录不存在、坏 yaml、`allowed_tools` 为空都不抛异常

## 2. 接入完整性

- [ ] `grep -rn "new SkillCatalog" --include="*.java" /Users/codemelo/mewcode/src` 命中 `MewCodeModel.java:494` 的非测试调用
- [ ] `grep -rn "skillCatalog.loadFromDirectory" --include="*.java" /Users/codemelo/mewcode/src` 命中 `MewCodeModel.java:497`
- [ ] `grep -rn "wireSkillsToAgent" --include="*.java" /Users/codemelo/mewcode/src` 命中 `MewCodeModel.java:500` / `MewCodeModel.java:511`
- [ ] 字段 `skillCatalog` 在 `MewCodeModel.java:102`；provider 就绪后初始化 `MewCodeModel.java:494-498`
- [ ] `registerSkillCommand(name)` 在 `MewCodeModel.java:518-533`：跳过已存在命令、注册 PROMPT 类型 `Command`、description 后缀 `[skill]`、handler 从 catalog 取 promptBody
- [ ] PROMPT 分发的 skill 分支在 `MewCodeModel.java:928-967`：`isSkill = cmd.description().endsWith("[skill]")`，命中后在 UI 上 println `skill(<name>) Successfully loaded skill`
- [ ] `/skills` 命令 handler 在 `src/main/java/com/mewcode/command/CommandRegistry.java:255-265` 列出 `skillList` supplier 返回的技能名
- [ ] `skillList` supplier 在 `MewCodeModel.java:984-986`：`skillCatalog != null` 时返回 `list().stream().map(s -> s.name()).toList()`
- [ ] 入口路径：用户输入 `/<skill-name>` → `executeCommand`（MewCodeModel）→ PROMPT 分支 → `cmdRegistry.execute` 返回 promptBody → `conversation.addUserMessage` → `agent.run`

## 3. 编译与测试

- [ ] `cd /Users/codemelo/mewcode && ./gradlew build` 通过
- [ ] `cd /Users/codemelo/mewcode && ./gradlew compileJava` 无警告
- [ ] `com.mewcode.skill` 包不 import `com.mewcode.agent` / `com.mewcode.tui`，仅通过 `SkillHost` / `SkillForkHost` 接口与外界交互

## 4. 端到端验证

- [ ] 启动 MewCode 后输入 `/skills`，若 `.mewcode/skills/` 下无技能则提示 `No skills installed.\n\nAdd skills to .mewcode/skills/<skill-name>/SKILL.md`（`CommandRegistry.java:260`）
- [ ] 在 `.mewcode/skills/skill-creator/SKILL.md` 现成样本下，启动后 `/skills` 列出 `skill-creator`
- [ ] 输入 `/skill-creator <args>` 触发 PROMPT 分支，UI 紧接出现 `skill(skill-creator) Successfully loaded skill`（`MewCodeModel.java:961-965`）
- [ ] Agent 新一轮 conversation 中可见两条 user message：第一条是 promptBody，第二条是 `<args>`（`MewCodeModel.java:937-942`）
- [ ] 修改 `.mewcode/skills/skill-creator/SKILL.md` 的 body 后，下次执行该技能时通过 `getFull` 热重载到新内容（`SkillCatalog.java:71-89`）
- [ ] 留存证据：未提供截图（手动 TUI 验证不在课程验收流程要求范围内）

## 5. 文档

- [ ] `docs/java/ch11/spec.md` 存在
- [ ] `docs/java/ch11/tasks.md` 存在
- [ ] `docs/java/ch11/checklist.md` 存在
- [ ] Java 实现位于 `origin/java` 分支，包路径 `com.mewcode.skill` / `com.mewcode.command`
```

<!-- series-nav-start -->

---
**📚 Skill系统**（6/6）

⬅️ 上一篇：[[TypeScript源码解析_技能加载与执行模式]]

<!-- series-nav-end -->
