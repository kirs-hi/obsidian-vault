# 第14章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装上了 [[理论学习_SubAgent_子任务分发|SubAgent]] 系统，主 [[07-Agent|Agent]] 可以把任务分派给子 Agent，子 Agent 在隔离的上下文中执行。消息隔离了，权限隔离了，文件缓存也隔离了。但有一样东西还没隔离：文件系统。

两个 Agent 同时改同一个文件，会互相覆盖。Git 分支管不了这个问题，因为分支只是时间维度的快照，同一时刻只有一个工作目录。我们需要的是空间维度的隔离，让同一时间存在多个独立工作区。

这一章要给 MewCode 接入 Git Worktree 管理系统。做完之后，每个子 Agent 都可以在独立的工作目录中操作文件，彻底消除并行场景下的文件冲突。

具体要新增这些东西：

-   **Slug 安全验证** ：防止路径遍历攻击，LLM 生成的名称不可信
-   **WorktreeManager 生命周期管理** ：Create / Enter / Exit / AutoCleanup / StaleCleanup / List / Remove，完整覆盖 Worktree 的创建、使用和销毁
-   **创建后设置** ：复制本地配置、配置 git hooks、软链接依赖目录、复制被忽略但需要的文件
-   **会话状态持久化** ：WorktreeSession 存入配置文件，支持 `--resume` 恢复
-   **与 SubAgent 集成** ：AgentDefinition 新增 `isolation` 字段， `executeWithWorktree` 自动创建 Worktree、注入上下文通知、完成后自动清理
-   **/worktree 斜杠命令** ：list / create / enter / exit / remove 五个子命令

这章 **不做** ：Worktree 之间的合并策略（由上层用户决定 merge 或丢弃）、跨 Worktree 的代码同步工具、多 Agent 并行编排（留给后续的 Agent Teams 系统）。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 用 Git 自带的多工作目录机制（同一仓库可挂多个工作目录，每个对应不同分支）作为隔离基础，目录统一放在仓库内部不被 Git 追踪的位置
- 目录名称走严格的安全校验：限制字符集、长度，拒绝 `.` 和 `..` 段，允许 `/` 作为嵌套分隔符（创建分支时再做平铺转换），防 LLM 输入触发路径遍历
- 完整生命周期管理：创建（含快速恢复——目录已存在时不调 git 子进程，纯文件系统读取 HEAD）、进入、退出、删除
- 创建后做环境初始化：复制本地配置（如 `settings.local.json`）、按主仓库 hooks 路径配置子目录的 git hooks、软链接大型依赖目录（依赖目录列表来自配置）、按规则复制被 gitignore 但运行需要的文件（best-effort）
- 切换工作目录时清理三类缓存（文件内容缓存、系统提示词/项目指令缓存、memory 文件缓存），防止 Agent 用旧目录的内容对新目录做决策
- 子 Agent 隔离模式：Agent 定义里通过字段声明隔离需求，进入流程自动建目录、在任务文本前注入路径翻译说明，完成后按变更情况自动判断保留还是清掉
- 退出时变更保护：有未提交修改或未推送 commit 时，默认拒绝删除目录，需显式确认丢弃；切回原目录后要重新加载主仓库的 hooks 配置
- 会话状态持久化到磁盘，支持进程意外退出后下次启动 `--resume` 恢复
- 后台周期性清理过期临时目录，三层过滤（命名模式 → 当前使用中/未过期 → fail-closed 的变更与未推送检查）
- 配套斜杠命令让用户手动管理目录（创建、列出、进入、退出、查看状态）
```

AI 会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了，然后让 [[Claude Code 命令与最佳实践|Claude Code]] 根据这三份文档进行开发

![](实战演练_动手实现_Worktree-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手实现_Worktree-2.jpeg)

### 功能验证过程

来验收一下结果

让 Agent 在 worktree 里创建个文件：

请在当前目录创建 witness.txt，内容写 "original content from main agent"。

![](实战演练_动手实现_Worktree-3.jpeg)

然后我们再输入

请用 Agent 工具派一个 general-purpose 子 Agent，

isolation 参数设为 "worktree"，

任务（prompt）是：把 witness.txt 的内容改成 "modified by isolated worker"，然后用 git 提交。

![](实战演练_动手实现_Worktree-4.jpeg)

会看到它是在worktree里创建，不会在主目录里创建文件，能有效避免文件冲突

![](实战演练_动手实现_Worktree-5.jpeg)

这时worktrees有一份witness的文本文件，内容是：modified by isolated worker

而主目录也有一份witness的文本文件，内容是：original content from main agent

![](实战演练_动手实现_Worktree-6.jpeg)

验收没问题，那么本章的主要任务就完成了。

现在虽然文件冲突解决了，但是如果是依赖关系的任务不能盲目并行咋办？如果是需要不同身份去处理任务咋办？如果是需要发散性讨论咋办？如果子Agent间需要协作咋办？

下一章，我们让多个子 Agent组成队伍，真正是一个team！

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

[[提示词]]如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch14: Worktree Spec

## 1. 背景

SubAgent 隔离了消息、权限、工具结果缓存，但所有子 Agent 仍然共享同一个工作目录——两个子 Agent 并发改同一个文件会互相覆盖。Git 分支不解决这个问题：分支只是时间维度的快照，同一时刻整个仓库仍然只有一份 working tree，切换分支会动所有文件的修改时间触发不必要的全量重编。多 Agent 并行要的是空间维度的隔离：同时存在多份独立的 working tree，每份对应不同分支，但共享同一个 `.git`。Git Worktree 提供的就是这个能力。这一章把它接进 MewCode，让主 Agent 和每个子 Agent 都能拥有独立的文件视图。

## 2. 目标

把 worktree 做成两层 API：会话级让 LLM 通过工具自主进出 worktree，Agent 级让 SubAgent 通过 `isolation: "worktree"` 声明自动获得独立 worktree。底层共用一套创建/快速恢复路径和"创建后设置"管线（本地配置复制 / git hooks 配置 / 大目录软链接 / `.worktreeinclude` 文件复制）。叠加 fail-closed 变更检测（无变更才允许清掉、有变更默认保留）和孤儿 worktree 的后台过期清理，保证既不丢用户工作、又不让磁盘堆积。

## 3. 功能需求

- F1: worktree 名称（slug）安全校验：限定字符集、长度上限、按 `/` 切段、显式拒绝 `.` / `..` 段，校验失败给出分类错误（长度 / 段名非法 / 路径遍历）；任何 git 命令或路径拼接之前先跑。
- F2: slug 到路径和分支的映射：用一个 git 安全但不在 slug 字符集的字符替换 `/`，避免嵌套 slug 导致目录或分支命名冲突；分支统一加固定前缀，方便从 `git branch` 输出里识别 MewCode 创建的。
- F3: 快速恢复路径：worktree 目录已存在时跳过 git 子进程，纯文件系统读 `.git` 指针 → `HEAD` ref → SHA，目标延迟 ≤ 10ms；任一步失败回退到完整创建路径。
- F4: git 子进程统一安全壳：所有 git 调用关闭终端密码提示、屏蔽 `GIT_ASKPASS`、丢弃 stdin，绝不挂起等待用户输入；失败返回结构化错误码而不是抛异常。
- F5: 创建/恢复主入口：先做 slug 校验和重名检查，命中已有目录走快速恢复（不重跑创建后设置），未命中按"已有远端 ref 优先 → fetch 兜底 → HEAD 兜底"的策略选 base branch，然后用大写 `-B` 创建 worktree（容忍上次未清干净的孤儿分支）。
- F6: 创建后设置四项：从主仓复制本地配置文件（`settings.local.json` 等）；按主仓 hooks 路径优先级（项目级 husky > 仓库 hooks）配置 worktree 的 `core.hooksPath`；按配置软链接大型依赖目录（node_modules / .venv / vendor 等）；按 `.worktreeinclude` gitignore 风格模式复制被 `.gitignore` 忽略但运行需要的文件（best-effort，单项失败不中断）。
- F7: 会话级 API 三件套：进入（创建 + 持久化 + 写全局单例）、Keep（清单例 + chdir 回原 cwd + 删持久化文件，保留 worktree 目录和分支）、Cleanup（同 Keep + `git worktree remove --force` + `git branch -D`）。
- F8: 会话持久化：单例序列化到仓库内固定位置（`.mewcode/` 下），记原 cwd / worktree 路径 / 分支 / 原分支 / 原 HEAD commit / session ID 等；写空值等价于删持久化文件。
- F9: 启动恢复：TUI 启动时读持久化文件，验证 worktree 路径仍然存在，写回全局单例；不主动切 cwd（让用户或工具自行决定），不重跑创建后设置。
- F10: Agent 级 API：为每个声明 `isolation: "worktree"` 的子 Agent 创建独立 worktree，不动全局单例、不切进程 cwd、不写持久化；快速恢复路径要 bump worktree 目录的 mtime，防止被后台清理误判为孤儿。
- F11: SubAgent 集成：主 Agent 调 `Agent` 工具且隔离参数为 worktree 时，自动为子 Agent 创建独立 worktree、把子 Agent 工作目录指向 worktree 路径、在任务提示词最前面注入一段 notice 告诉子 Agent "你在隔离副本里、父路径要翻译为本地路径、编辑前重读文件"。
- F12: 子 Agent 完成后决策：检测有无变更（未提交修改或新 commit），无变更自动清理 worktree，有变更保留并在返回结果末尾附路径和分支名给主 Agent review。
- F13: 变更保护：会话级退出工具在 `action=remove` 且未显式声明丢弃时拒绝删除——脏 worktree 要 LLM 明确传 `discard_changes=true` 才能强删；具体变更数（uncommitted 文件数 + 未推送 commit 数）作为错误信息回吐给 LLM，单复数正确处理。
- F14: 变更检测 fail-closed：所有变更检查（git status / git rev-list）任何一步失败都按"有变更"处理，绝不在 git 命令失败时清掉用户工作。
- F15: LLM Tool 暴露：进入工具（input 仅可选 slug，已有 session 时拒绝）和退出工具（input `action` 必填 / `discard_changes` 可选，无 session 时拒绝）；两个工具标记为延迟工具（deferred），由主 Agent loop 在工具批次结束时统一执行，避免和别的工具同时操作目录。
- F16: 临时 worktree 命名模式：用前缀化的固定模式区分"自动产物"（子 Agent / 工作流 / 桥接器 / 任务 spawn 等来源各自有前缀）和"用户手动命名"；前缀正则集中维护，便于新增来源时统一加入。
- F17: 后台过期清理三层过滤：周期扫描 worktree 根目录，依次过滤——L1 命名模式（用户起名的永不删，廉价）→ L2 时态（跳过当前 session 占用的 + 近期活跃的）→ L3 git 状态 fail-closed（status 失败/非空跳过 + 未推送 commit 跳过）；删完跑 `git worktree prune` 同步 git 内部表。

## 4. 非功能需求

- N1: 全局 session 状态用读写锁保护，并发读不阻塞；Agent 级 API 完全无状态，天然并发安全。
- N2: 任何路径的 worktree 删除（会话级 Cleanup / Agent 级 Remove / 后台清理）都要先 chdir 离开 worktree（或保证当前不在 worktree 内），否则 `git worktree remove` 会失败。
- N3: `git worktree remove` 和 `git branch -D` 之间必须留出 git lockfile 释放时间（经验值 100ms），否则 branch 删除会偶发失败。
- N4: Agent 级 API 在快速恢复（worktree 目录已存在）时必须 bump worktree mtime，否则同一 worktree 被反复复用时会因为 mtime 太老被后台清理误删。
- N5: 三层过滤的执行顺序固定：先廉价的命名模式 → 再时态判断 → 最后贵的 git 检查；任何一层判定保留都立即 continue，不进入下一层。
- N6: 创建后设置的四项里软链接和 `.worktreeinclude` 复制是 best-effort——任何单项失败只跳过、不中断创建，保证主路径鲁棒。
- N7: 变更保护的错误信息必须包含具体数字（N 文件 + M commits）和分支名，让 LLM 能据此判断要不要强删；不能只回 "has changes" 这种空话。
- N8: worktree 子系统不假设统一日志层存在，所有创建/退出/清理的信息通过工具结果文本传达；这同时是给 LLM 的运行时反馈。

## 5. 设计概要

- 核心数据结构:
 - `WorktreeSession`：会话级全局单例，记录原 cwd / worktree 路径与名称 / worktree 分支 / 原分支 / 原 HEAD commit / session ID / 创建耗时；用于退出时还原状态和持久化。
 - `AgentWorktreeResult`：Agent 级 API 返回值，只含 worktree 路径 / 分支 / HEAD / 主仓根，不写全局状态。
 - `CreateResult`：底层创建/恢复入口的归一化结果，标记是否是快速恢复（决定是否跳过创建后设置）。
 - `ChangeSummary`：变更计数（修改文件数 + 未推送 commit 数），供变更保护错误信息生成。
 - 配置块：软链接目录列表 + 后台清理间隔 + 过期阈值，由 TUI 启动时注入，不注入走保守默认（间隔 0 = 后台清理停用、阈值 720 小时 = 30 天）。
- 主流程:
 - **会话级 Enter**：guard 已有 session → slug 校验 → 记录原 cwd 和原分支 → 创建/快速恢复 → 仅新创建走"创建后设置" → 写全局单例 + 持久化。
 - **会话级 Exit**：guard 无 session → 若 `action=remove` 且未声明丢弃则跑变更保护 → Keep（清单例 + chdir 回原 cwd + 删持久化）或 Cleanup（同 Keep + `git worktree remove --force` + sleep + `git branch -D`）。
 - **Agent 级隔离**：主 Agent 调 `Agent` 工具且隔离为 worktree → 生成临时 slug（带 `agent-` 前缀）→ 强制落主仓根 → 创建或快速恢复（恢复路径 bump mtime）→ 子 Agent 工作目录指向 worktree → 任务提示词前置注入 notice → 子 Agent 跑完后看有无变更 → 干净则清掉、脏则保留并把路径分支拼回结果。
 - **后台过期清理**：TUI 启动后台 goroutine → 按配置间隔周期扫 → 三层过滤 → 通过的删 worktree + 删分支 → 周期结束如有删除则跑一次 `git worktree prune`。
- 调用链（模块层级）:
 - TUI 启动 → 解析仓库根（穿透 commondir 到主仓）→ 注册两个 worktree 工具 → 读持久化文件并恢复 session → 启后台清理 goroutine。
 - LLM Enter/Exit → 工具 dispatcher → worktree 包会话级 API。
 - AgentTool → 看到 `isolation: worktree` → worktree 包 Agent 级 API → 子 Agent 跑完 → 变更检测 → Remove 或保留并拼路径。
- 与其他模块的交互:
 - 依赖 `internal/tools`（注册两个工具）、`internal/agents`（隔离分流）、`internal/tui`（启动装配 + cleanup 调度 + 配置注入）；底层只依赖 `os/exec`（git）+ 标准库（正则 / JSON / 文件系统 / crypto/rand）。
 - 不依赖 `internal/config` 的通用加载链路——worktree 配置当前由 TUI 启动时手动注入；也不依赖 `internal/memory` / `internal/prompt` / `internal/session`。

## 6. Out of Scope

- 不实现非 git VCS 适配（hg / jj / sapling 等），所有 worktree 操作 hardcode 走 git 子命令
- 不实现 sparse checkout / partial clone 优化，大型 mono-repo 优化推到后续
- 不实现 `--worktree` / `--worktree --tmux` CLI 启动快速路径（涉及 tmux/iTerm2 子系统，留给 ch15）
- 不实现 PR fetch 或 pull request 头引用解析（远端协作场景）
- 不实现 prepare-commit-msg hook 注入 commit attribution（商业 feature 场景）
- 不实现 ReadFile / Memory / SystemPrompt 缓存清理 hook（MewCode 当前没有这几类缓存）
- 不引入第三方 gitignore 库（自实现简化匹配够用）
- 团队成员（teammate）路径的 worktree 自动清理推到 ch15 收尾，本章 teammate 路径只创建并隔离、不负责清理

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch14: Worktree Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 实现 Slug 校验 + 命名映射
- 影响文件: `internal/worktree/validate.go`（`MaxWorktreeSlugLength` @ 11；`validWorktreeSlugSegment` @ 16；`ValidateWorktreeSlug` @ 32-58；`FlattenSlug` @ 73-78；`WorktreeBranchName` @ 80-82）
- 依赖任务: 无
- 完成标准: `ValidateWorktreeSlug` 校验长度 ≤ 64、按 `/` 切段、每段匹配 `^[a-zA-Z0-9._-]+$`、显式拒绝 `.` / `..` 段，错误分类（长度 / 非法段 / 路径遍历）；`FlattenSlug(s) = strings.ReplaceAll(s, "/", "+")`；`WorktreeBranchName(s) = "worktree-" + FlattenSlug(s)`。
- [ ] 完成

## T2: 实现 Git 纯文件系统读取
- 影响文件: `internal/worktree/filesystem.go`（`IsSafeRefName` @ 30；`IsValidGitSha` @ 52；`ResolveGitDir` @ 64；`GetCommonDir` @ 100；`readGitHead` @ 135；`ResolveRef` @ 180；`resolveRefInDir` @ 200；`ReadRawSymref` @ 257；`GetDefaultBranch` @ 286；`GetCurrentBranch` @ 325；`ReadWorktreeHeadSha` @ 347-377）
- 依赖任务: 无
- 完成标准: `ReadWorktreeHeadSha` 完整链路（`.git pointer → gitdir → HEAD → ResolveRef`），任一步失败返回 `("", nil)` 让调用方走完整路径；`resolveRefInDir` 含 loose ref + packed-refs fallback；`GetDefaultBranch` 读 `refs/remotes/origin/HEAD` symref，回退 `main` → `master`，默认 "main"；附 `IsSafeRefName` / `IsValidGitSha` 防 ref 文件被篡改后注入 shell；目标延迟 ≤ 10ms（不起 git 子进程）。
- [ ] 完成

## T3: 实现 Git 子进程安全壳
- 影响文件: `internal/worktree/env.go`（`gitNoPromptEnv` @ 21-30；`runGit` @ 32-51）
- 依赖任务: 无
- 完成标准: `gitNoPromptEnv()` 在 `os.Environ()` 后追加 `GIT_TERMINAL_PROMPT=0` 和 `GIT_ASKPASS=`，所有 git 调用统一用；`runGit(ctx, dir, args...)` 强制 `Env=gitNoPromptEnv()` + `Stdin=nil`，never throw，返回 `(stdout, stderr, code)` 三元组，进程未起来时 code=-1。
- [ ] 完成

## T4: 实现创建/恢复主入口
- 影响文件: `internal/worktree/create.go`（`WorktreesDir` @ 14；`WorktreePathFor` @ 21；`CreateResult` @ 31；`getOrCreateWorktree` @ 56-131）
- 依赖任务: T1, T2, T3
- 完成标准: `WorktreesDir(root) = <root>/.mewcode/worktrees`；`WorktreePathFor(root, slug) = WorktreesDir + FlattenSlug(slug)`；`getOrCreateWorktree` 命中已存在目录走快速恢复 → `ReadWorktreeHeadSha` → 返回 `Existed=true`，**不**跑创建后设置；未命中走 `os.MkdirAll(WorktreesDir, 0o755) → GetDefaultBranch → ResolveRef("refs/remotes/origin/<default>")`：命中则 `baseBranch="origin/<default>"`（省 fetch），未命中 `runGit("fetch","origin",<default>)`，成功用 `origin/<default>` 否则回退 `HEAD`；最后 `git worktree add -B worktree-<flat> <path> <baseBranch>`（大写 `-B` 容忍上次未清的孤儿分支）。
- [ ] 完成

## T5: 实现创建后设置四项 + 配置块
- 影响文件: `internal/worktree/setup.go`（`performPostCreationSetup` @ 14-26；`copySettingsLocal` @ 31-44；`configureHooksPath` @ 49-70；`symlinkDirectories` @ 75-85；`getSymlinkDirectories` @ 90-92；`CopyWorktreeIncludeFiles` @ 97-155；`matchesWorktreeInclude` @ 160-182；`copyFileContents` @ 184-199；`worktreeConfig` @ 201-208；`SetWorktreeConfig` @ 210-217；`GetStaleCutoffHours / GetStaleCleanupInterval` @ 219-228；`FindCanonicalGitRoot` @ 231-244）
- 依赖任务: T3
- 完成标准: 四项依次执行 — **A** `copySettingsLocal` 复制 `<repo>/.mewcode/settings.local.json`（ENOENT 静默）；**B** `configureHooksPath` 优先 `<repo>/.husky` 回退 `<repo>/.git/hooks`，找到第一个存在的目录后在 worktree 目录里跑 `git config core.hooksPath <hooksPath>`；**C** `symlinkDirectories` 从 `worktreeConfig.SymlinkDirectories` 读列表，跳过含 `..` 项，逐个 `os.Symlink(src, dst)`，错误静默；**D** `CopyWorktreeIncludeFiles` 读 `<repo>/.worktreeinclude`（按行收集 patterns，跳空行和 `#`）→ `git ls-files --others --ignored --exclude-standard --directory` 列出 gitignored → `matchesWorktreeInclude`（支持 exact/basename/glob/dir prefix）筛选 → 命中的 `os.MkdirAll(Dir(dst), 0o755) + copyFileContents`，单文件失败 `continue` 不中断；`worktreeConfig` 包级私有，默认 `StaleCutoffHours=720`（30 天）；`FindCanonicalGitRoot` 解 `.git` → 跟随 `commondir` → 返回主仓 root。
- [ ] 完成

## T6: 实现变更检测 fail-closed
- 影响文件: `internal/worktree/changes.go`（`ChangeSummary` @ 11；`HasWorktreeChanges` @ 19-37；`CountWorktreeChanges` @ 43-74）
- 依赖任务: T3
- 完成标准: `HasWorktreeChanges` 返 bool — `git status --porcelain` 非零或非空 → true；`git rev-list --count <headCommit>..HEAD` 非零或解析失败或 > 0 → true；都干净 → false（**git 失败默认 true，fail-closed**）。`CountWorktreeChanges` 返 `*ChangeSummary` — status 失败返 nil；`originalHeadCommit==""` 即使 status 成功也返 nil（hook-based 场景）；`rev-list --count` 失败返 nil；其余返 `&{ChangedFiles, Commits}`。
- [ ] 完成

## T7: 实现 SubAgent worktree 上下文 notice
- 影响文件: `internal/worktree/notice.go`（`BuildWorktreeNotice` @ 9-19）
- 依赖任务: 无
- 完成标准: 返回固定模板英文文本，包含 `parent_cwd` / `worktree_cwd` 占位 + 关键句"running in an isolated git worktree"、"translate paths"、"re-read files before editing"、"your edits will not affect the parent agent"；在子 Agent 任务文本最前面拼接（不替换原 prompt）。
- [ ] 完成

## T8: 实现会话级 API + 持久化
- 影响文件: `internal/worktree/session.go`（`WorktreeSession` @ 14-25；`sessionMu / currentWorktreeSession` @ 27-32；`GetCurrentWorktreeSession` @ 34；`RestoreWorktreeSession` @ 43；`sessionFilePath` @ 50；`SaveWorktreeSession` @ 56-72；`LoadWorktreeSession` @ 74-91；`CreateWorktreeForSession` @ 93-134；`KeepWorktree` @ 138-154；`CleanupWorktree` @ 158-188）
- 依赖任务: T1, T4, T5, T6
- 完成标准: `WorktreeSession` 9 字段（`OriginalCwd / WorktreePath / WorktreeName / WorktreeBranch / OriginalBranch / OriginalHeadCommit / SessionID / HookBased / CreationDurationMs`）；包级 `currentWorktreeSession` + `sessionMu sync.RWMutex`；`CreateWorktreeForSession`：`ValidateWorktreeSlug → os.Getwd 记 originalCwd → GetCurrentBranch 拿 originalBranch → getOrCreateWorktree → 仅 !Existed 跑 performPostCreationSetup 并测 ms → 组装 session → 写全局 + SaveWorktreeSession`；`KeepWorktree`：原子读取并清空全局单例 → `os.Chdir(session.OriginalCwd)` → `SaveWorktreeSession(repo, nil)` 删持久化文件（不删目录、不删分支）；`CleanupWorktree`：同 keep 流程 + 从 `OriginalCwd` 跑 `git worktree remove --force <wtPath>` → `time.Sleep(100ms)` 等 lockfile → `git branch -D <wtBranch>` → 删持久化（git 失败 best-effort 不中断）；持久化路径 `<repo>/.mewcode/worktree_session.json`，session=nil 时删文件。
- [ ] 完成

## T9: 实现 Agent 级 API
- 影响文件: `internal/worktree/agent.go`（`AgentWorktreeResult` @ 11；`CreateAgentWorktree` @ 22-53；`RemoveAgentWorktree` @ 57-73）
- 依赖任务: T1, T4, T5
- 完成标准: `CreateAgentWorktree(ctx, slug)`：`ValidateWorktreeSlug → os.Getwd + FindCanonicalGitRoot 强制落主仓 → getOrCreateWorktree → !Existed 跑 setup`；`Existed` 时 `os.Chtimes(wtPath, now, now)` bump mtime 防被 cleanup 误判；**不动全局单例、不切进程 cwd、不写持久化**；返回 `AgentWorktreeResult{WorktreePath, WorktreeBranch, HeadCommit, GitRoot}`。`RemoveAgentWorktree(ctx, wtPath, wtBranch, gitRoot)`：从 `gitRoot`（**不**从 wtPath，否则会把自己删掉）跑 `git worktree remove --force` → 成功后 `time.Sleep(100ms)` → 分支非空时 `git branch -D <wtBranch>` → 返回 worktree 删除是否成功。
- [ ] 完成

## T10: 实现 EnterWorktreeTool
- 影响文件: `internal/tools/enter_worktree.go`（`EnterWorktreeTool` @ 15-18；`Name / Category / Description / ShouldDefer` @ 20-27；`Schema` @ 29-43；`Execute` @ 45-87；`generateWorktreeSlug` @ 89-93）
- 依赖任务: T8
- 完成标准: `Name="EnterWorktree"`、`Category=CategoryCommand`、`ShouldDefer=true`（进 deferred 工具队列）；input schema 仅可选 `name: string`（按 slug 字符集约束）；`Execute` guard：`GetCurrentWorktreeSession() != nil` → 拒绝 `"Already in a worktree session"`；`name==""` 时 `generateWorktreeSlug()` 生成 `wt-<8hex>`；`RepoRoot==""` 报 `"Error: not in a git repository"`；成功调 `CreateWorktreeForSession(t.SessionID, slug, t.RepoRoot)`，返回 `"Created worktree at <path> on branch <branch>. The session is now working in the worktree. Use ExitWorktree to leave mid-session, or exit the session to be prompted."`。
- [ ] 完成

## T11: 实现 ExitWorktreeTool
- 影响文件: `internal/tools/exit_worktree.go`（`ExitWorktreeTool` @ 15-17；`Name / Category / Description / ShouldDefer` @ 19-26；`Schema` @ 28-48；`Execute` @ 50-end）
- 依赖任务: T6, T8
- 完成标准: `Name="ExitWorktree"`、`ShouldDefer=true`；input schema `action: enum["keep","remove"]`（required）+ `discard_changes?: bool`；`Execute` scope guard：`GetCurrentWorktreeSession() == nil` → 拒绝 `"No-op: there is no active EnterWorktree session to exit. This tool only operates on worktrees created by EnterWorktree in the current session — it will not touch worktrees created manually or in a previous session. No filesystem changes were made."`；变更保护：`action=="remove" && !discard_changes` 时 `CountWorktreeChanges`：nil 报 `"Could not verify worktree state at <path>..."`，非零报 `"Worktree has N uncommitted file(s) and M commit(s) on <branch>. Removing will discard this work permanently. Set discard_changes=true to force."`（**单复数 file/files、commit/commits 正确处理**）；分支：`action=="keep"` 调 `KeepWorktree`；`action=="remove"` 调 `CleanupWorktree`；返回成功消息。
- [ ] 完成

## T12: 接入 SubAgent isolation
- 影响文件: `internal/agents/agent_tool.go`（`isolation` schema @ 163-167；`cwd` schema @ 177-180；`Execute` 解析 + 互斥 @ 217-223；`runSync` worktree 分支 @ 298-319；完成后决策 @ 391-398；`runAsTeammate` worktree 分支 @ 656-670；`generateAgentSlug` @ 739-745）
- 依赖任务: T6, T7, T9
- 完成标准: `Agent` 工具 schema 含 `isolation: enum["worktree"]` + `cwd: string`；`Execute` 在 `cwdOverride != "" && isolation == "worktree"` 时返回 `"Error: cwd and isolation: 'worktree' are mutually exclusive"`；`generateAgentSlug(description)` 生成 `agent-a<7hex>`（匹配 cleanup 正则 `^agent-a[0-9a-f]{7}$`）；`runSync` 在 `isolation == "worktree"` 时：`worktree.CreateAgentWorktree(ctx, slug)` → `subAgent.WorkDir = wtResult.WorktreePath` → `notice := worktree.BuildWorktreeNotice(parentCwd, wtResult.WorktreePath)` → `prompt = notice + "\n\n" + prompt`；子 Agent 完成后 `worktree.HasWorktreeChanges` → 干净 → `worktree.RemoveAgentWorktree(ctx, wtPath, wtBranch, gitRoot)`；脏 → `result += "\n\nWorktree kept at <path> (branch <branch>) — has uncommitted changes or new commits."`；`runAsTeammate` 同样三步（创建 + WorkDir + notice），但**不**做完成后自动清理（teammate 长生命周期，留给 ch15 收尾）。
- [ ] 完成

## T13: 实现后台过期清理
- 影响文件: `internal/worktree/cleanup.go`（`ephemeralWorktreePatterns` @ 14-20；`isEphemeralSlug` @ 22-30；`CleanupStaleAgentWorktrees` @ 39-105；`StartCleanupLoop` @ 110-130）
- 依赖任务: T5, T6, T9
- 完成标准: 五个临时命名正则：`^agent-a[0-9a-f]{7}$` / `^wf_[0-9a-f]{8}-[0-9a-f]{3}-\d+$` / `^wf-\d+$` / `^bridge-[A-Za-z0-9_]+(-[A-Za-z0-9_]+)*$` / `^job-[a-zA-Z0-9._-]{1,55}-[0-9a-f]{8}$`；`isEphemeralSlug` 任一匹配返 true；`CleanupStaleAgentWorktrees(ctx, cutoffDate)` → `FindCanonicalGitRoot(Getwd)` → `os.ReadDir(WorktreesDir)`；三层过滤 — **L1 命名**：`isEphemeralSlug` false 跳（用户命名永不删）；**L2 时态**：当前 session.WorktreePath 跳 + `info.ModTime().After(cutoffDate)` 跳；**L3 git 状态 fail-closed**：`git --no-optional-locks status --porcelain -uno` 非零或非空跳 + `git rev-list --max-count=1 HEAD --not --remotes` 非零或非空（未推送 commit）跳；三层都通过的 `RemoveAgentWorktree`；末尾若有删除 → `git worktree prune` 同步 git 内部表；返回清理数量。`StartCleanupLoop(ctx)`：`GetStaleCleanupInterval() <= 0` 直接 return；否则起 goroutine 每 `interval` 秒跑一次 `CleanupStaleAgentWorktrees(now - cutoffHours*Hour)`；ctx 取消时退出。
- [ ] 完成

## T14: 接入 TUI 启动装配
- 影响文件: `internal/tui/tui.go`（`worktree` import @ 33；装配段 @ 619-639）
- 依赖任务: T8, T10, T11, T13
- 完成标准:
 1. `gitRoot := worktree.FindCanonicalGitRoot(wd)` 算规范仓库根（穿透 commondir 到主仓）；
 2. `m.registry.Register(&tools.EnterWorktreeTool{SessionID: m.sessionID, RepoRoot: gitRoot})` + `m.registry.Register(&tools.ExitWorktreeTool{RepoRoot: gitRoot})` 两个工具注册；
 3. `worktree.LoadWorktreeSession(gitRoot)` 非 nil 且 `WorktreePath` 还存在（stat 验证）时 `worktree.RestoreWorktreeSession(s)` 写回全局；
 4. `worktree.StartCleanupLoop(context.Background())` 起后台清理 goroutine。
- [ ] 完成

## T15: 端到端验证
- 影响文件: 无（仅运行）
- 依赖任务: T1-T14
- 完成标准:
 - `go build ./...` 通过（无输出）；
 - `go test ./internal/worktree/...` 通过（10 个 _test.go 全 PASS）；
 - `go test ./internal/agents/...` 通过（含 isolation 集成）；
 - **路径 A — 工具直接驱动**：主 Agent 调 `EnterWorktree({name:"demo"})` 创建 worktree → 在 worktree 里 `WriteFile + Bash("git commit ...")` → `ExitWorktree({action:"remove"})` 被变更保护拒绝并列出具体数 → `ExitWorktree({action:"remove", discard_changes:true})` 强删成功；
 - **路径 B — 子 Agent 自动隔离**：主 Agent 在主目录 `WriteFile witness.txt = "original content from main agent"` → 调 `Agent({subagent_type:"general-purpose", isolation:"worktree", description:"...", prompt:"把 witness.txt 改成 ..."})` → 验证主目录 `witness.txt` 内容不变；`.mewcode/worktrees/agent-*/witness.txt` 是修改后版本；若有 commit → 结果末尾出现 `"Worktree kept at ... (branch worktree-agent-a...) — has uncommitted changes or new commits."`。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15
```
```plain
# ch14: Worktree Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 常量 `MaxWorktreeSlugLength = 64` 在 `internal/worktree/validate.go:11` 定义
- [ ] 函数 `ValidateWorktreeSlug` 在 `internal/worktree/validate.go:32-58` 含长度 + 段名 + `.` / `..` 三类错误分类
- [ ] 函数 `FlattenSlug` 在 `internal/worktree/validate.go:73` 把 `/` 替换成 `+`；`WorktreeBranchName` 在 `:80` 加 `worktree-` 前缀
- [ ] 函数 `ReadWorktreeHeadSha` 在 `internal/worktree/filesystem.go:347-377` 完整链路（`.git pointer → gitdir → HEAD → ResolveRef`），失败返回 `("", nil)` 不抛错
- [ ] 函数 `resolveRefInDir` 在 `internal/worktree/filesystem.go:200` 含 loose ref + packed-refs fallback
- [ ] 函数 `GetDefaultBranch` 在 `internal/worktree/filesystem.go:286` 读 `refs/remotes/origin/HEAD` symref 并回退 main → master
- [ ] 函数 `runGit` 在 `internal/worktree/env.go:32-51` 强制 `Env=gitNoPromptEnv() + Stdin=nil`，never throw
- [ ] 类型 `CreateResult` 在 `internal/worktree/create.go:31` 含 `Existed` 标记快速恢复
- [ ] 函数 `getOrCreateWorktree` 在 `internal/worktree/create.go:56-131` 实现"快速恢复 → 创建路径"二选一，创建路径走 `origin/<default> → fetch → HEAD` 三段策略，最后 `git worktree add -B`（大写 `-B`）
- [ ] 函数 `performPostCreationSetup` 在 `internal/worktree/setup.go:14-26` 依序调四项 A/B/C/D
- [ ] 函数 `CopyWorktreeIncludeFiles` 在 `internal/worktree/setup.go:97-155` 单文件失败 `continue` 不中断
- [ ] 函数 `FindCanonicalGitRoot` 在 `internal/worktree/setup.go:231-244` 跟随 `.git/commondir` 解析主仓根
- [ ] 类型 `WorktreeSession` 在 `internal/worktree/session.go:14-25` 含 9 个字段（OriginalCwd / WorktreePath / WorktreeName / WorktreeBranch / OriginalBranch / OriginalHeadCommit / SessionID / HookBased / CreationDurationMs）
- [ ] 模块级 `currentWorktreeSession` + `sessionMu sync.RWMutex` 在 `internal/worktree/session.go:27-32`
- [ ] 函数 `CreateWorktreeForSession` 在 `internal/worktree/session.go:93-134` 仅 `!Existed` 时跑 setup 并测 `CreationDurationMs`
- [ ] 函数 `CleanupWorktree` 在 `internal/worktree/session.go:158-188` 含 `time.Sleep(100ms)` 等 git lockfile 释放（在 `git worktree remove --force` 和 `git branch -D` 之间）
- [ ] 类型 `AgentWorktreeResult` 在 `internal/worktree/agent.go:11` 不含 SessionID（不写全局单例）
- [ ] 函数 `CreateAgentWorktree` 在 `internal/worktree/agent.go:22-53` 在 `Existed` 时 `os.Chtimes` bump mtime
- [ ] 函数 `RemoveAgentWorktree` 在 `internal/worktree/agent.go:57-73` 从 `gitRoot` 跑 git 子进程（不是 wtPath，否则把自己删掉）
- [ ] 函数 `HasWorktreeChanges` 在 `internal/worktree/changes.go:19-37` git 失败返回 true（fail-closed）
- [ ] 函数 `CountWorktreeChanges` 在 `internal/worktree/changes.go:43-74` 失败返回 nil（让调用方报具体错误文本）
- [ ] 函数 `BuildWorktreeNotice` 在 `internal/worktree/notice.go:9-19` 模板包含 `parent_cwd` / `worktree_cwd` 占位 + "re-read files before editing" 关键句
- [ ] 变量 `ephemeralWorktreePatterns` 在 `internal/worktree/cleanup.go:14-20` 含五个正则（agent-a / wf_ / wf- / bridge- / job-）
- [ ] 函数 `CleanupStaleAgentWorktrees` 在 `internal/worktree/cleanup.go:39-105` 三层过滤顺序固定（L1 命名 → L2 时态 → L3 git 状态）
- [ ] 函数 `StartCleanupLoop` 在 `internal/worktree/cleanup.go:110-130interval <= 0` 直接 return
- [ ] 类型 `EnterWorktreeTool` 在 `internal/tools/enter_worktree.go:15` 含 `SessionID` 和 `RepoRoot` 字段，`ShouldDefer` 返回 true
- [ ] 类型 `ExitWorktreeTool` 在 `internal/tools/exit_worktree.go:15` 含 `RepoRoot` 字段，`ShouldDefer` 返回 true
- [ ] `ExitWorktreeTool` schema 在 `internal/tools/exit_worktree.go:28-48` 含 `action: enum["keep","remove"]`（required）+ `discard_changes?: bool`
- [ ] 函数 `generateAgentSlug` 在 `internal/agents/agent_tool.go:741` 生成 `agent-a<7hex>` 匹配 cleanup 正则

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -rn "EnterWorktreeTool" --include="*.go" .` 在 `internal/tui/tui.go:621` 找到注册调用
- [ ] `grep -rn "ExitWorktreeTool" --include="*.go" .` 在 `internal/tui/tui.go:625` 找到注册调用
- [ ] `grep -rn "FindCanonicalGitRoot" --include="*.go" .` 至少命中 TUI 启动（`tui.go:620`）+ Agent API（`agent.go:25 附近`）
- [ ] `grep -rn "LoadWorktreeSession" --include="*.go" .` 在 `internal/tui/tui.go:631` 找到调用方
- [ ] `grep -rn "RestoreWorktreeSession" --include="*.go" .` 在 `internal/tui/tui.go:633` 找到调用方
- [ ] `grep -rn "StartCleanupLoop" --include="*.go" .` 在 `internal/tui/tui.go:639` 找到调用方
- [ ] `grep -rn "CreateAgentWorktree" --include="*.go" .` 在 `internal/agents/agent_tool.go:304` 和 `:659` 找到两处调用（runSync + runAsTeammate）
- [ ] `grep -rn "BuildWorktreeNotice" --include="*.go" .` 同上两处调用（runSync 在 `:315`，runAsTeammate 在 `:668`）
- [ ] `grep -rn "HasWorktreeChanges" --include="*.go" .` 在 `internal/agents/agent_tool.go:392` 找到主流程调用方（决定 Remove 还是保留）
- [ ] `grep -rn "RemoveAgentWorktree" --include="*.go" .` 在 `internal/agents/agent_tool.go:396` 和 `internal/worktree/cleanup.go` 找到调用方
- [ ] `grep -rn "CountWorktreeChanges" --include="*.go" .` 在 `internal/tools/exit_worktree.go` 找到唯一调用方（用于变更保护错误信息）
- [ ] `grep -rn "SetWorktreeConfig" --include="*.go" .` 找到 setter 定义在 `internal/worktree/setup.go:210`（注意：当前未在 TUI 启动时注入，`StaleCleanupInterval` 默认 0，后台清理默认不跑）

## 3. 编译与测试

- [ ] `go build ./...` 通过（无输出）
- [ ] `go test ./internal/worktree/...` 通过（10 个 _test.go 全 PASS：`validate_test.go` / `filesystem_test.go` / `env_test.go` / `create_test.go` / `setup_test.go` / `session_test.go` / `agent_test.go` / `changes_test.go` / `notice_test.go` / `cleanup_test.go`）
- [ ] `go test ./internal/agents/...` 通过（含 isolation 集成）
- [ ] `go vet ./...` 无新增警告

## 4. 端到端验证

- [ ] **路径 A — 工具直接驱动**：用户对主 Agent 说"用 EnterWorktree 工具创建一个名叫 demo 的工作树" → LLM 调 `EnterWorktree({name:"demo"})` → 返回 `Created worktree at .../.mewcode/worktrees/demo on branch worktree-demo`；让 Agent 在 worktree 里创建 `hello.txt` 并 `git commit`；让 Agent 调 `ExitWorktree({action:"remove"})` → 因有未推送 commit 被变更保护拒绝，错误文本包含具体 file/commit 数和分支名；`ExitWorktree({action:"remove", discard_changes:true})` 强删成功；`ls .mewcode/worktrees/` 看到 `demo/` 已消失。
- [ ] **路径 B — 子 Agent 自动隔离**：用户让主 Agent 在主目录建 `witness.txt`（内容 "original content from main agent"）→ 调 `Agent({subagent_type:"general-purpose", isolation:"worktree", description:"...", prompt:"把 witness.txt 改成 \"modified by isolated worker\"，然后 git 提交"})`；验证 `cat witness.txt` 主目录内容仍是 "original ..."；`cat .mewcode/worktrees/agent-*/witness.txt` 是修改后版本；若子 Agent 有 commit → 结果末尾出现 `"Worktree kept at ... (branch worktree-agent-a...) — has uncommitted changes or new commits."`；若无修改 → worktree 自动清理（`.mewcode/worktrees/` 下 `agent-*` 目录消失）。
- [ ] **持久化与 crash 恢复**：TUI 里 `EnterWorktree({name:"crashtest"})` 创建 worktree → `Ctrl+C` 杀 TUI 进程 → `cat .mewcode/worktree_session.json` 文件仍在并含 crashtest 会话；重启 TUI → 启动期间 `LoadWorktreeSession + RestoreWorktreeSession` 将 session 写回全局；下一次工具调用时 `GetCurrentWorktreeSession()` 非 nil。
- [ ] **变更保护单复数**：在 worktree 里建 1 个未提交修改 → `ExitWorktree({action:"remove"})` 返回 `"1 uncommitted file"`；建 2+ 个修改 → 返回 `"N uncommitted files"`（注意单复数）；同样验证 commit 数的单复数。
- [ ] **后台清理保守不删**：手动在 `.mewcode/worktrees/agent-aabcdef1/` 下建一个有未推送 commit 的目录（mtime 设为过期前）→ 等 cleanup loop 跑一轮（或手动调 `CleanupStaleAgentWorktrees` 测试）→ 该目录仍保留（L3 fail-closed 拦住）。
- [ ] **互斥校验**：`Agent({subagent_type:"general-purpose", cwd:"/tmp/x", isolation:"worktree", ...})` 返回 `"Error: cwd and isolation: 'worktree' are mutually exclusive"`。

## 5. 文档

- [ ] `specs/go/ch14/spec.md` 已按 ch13 风格重写（F1-F17 + N1-N8，无 file:line 代码标注）
- [ ] `specs/go/ch14/tasks.md` 已写，15 个 T 全部勾完（T1-T15）
- [ ] `specs/go/ch14/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch14`，新增代码的调用链已在 PR 描述或 commit message 里说明
```

### Python

```plain
# ch14: Worktree Spec

## 1. 背景

SubAgent 隔离了消息、权限、工具结果缓存，但所有子 Agent 仍然共享同一个工作目录——两个子 Agent 并发改同一个文件会互相覆盖。Git 分支不解决这个问题：分支只是时间维度的快照，同一时刻整个仓库仍然只有一份 working tree，切换分支会动所有文件的修改时间触发不必要的全量重编。多 Agent 并行要的是空间维度的隔离：同时存在多份独立的 working tree，每份对应不同分支，但共享同一个 `.git`。Git Worktree 提供的就是这个能力。这一章把它接进 MewCode，让主 Agent 和每个子 Agent 都能拥有独立的文件视图。

## 2. 目标

把 worktree 做成两层 API：会话级让 LLM 通过 `EnterWorktree` / `ExitWorktree` 工具自主进出 worktree，Agent 级让 SubAgent 通过 `isolation: "worktree"` 声明自动获得独立 worktree。底层共用一个 `WorktreeManager` 提供创建/快速恢复路径和"创建后设置"管线（本地配置复制 / git hooks 配置 / 大目录软链接 / `.worktreeinclude` 文件复制）。叠加 fail-closed 变更检测（无变更才允许清掉、有变更默认保留）和孤儿 worktree 的后台过期清理 task，保证既不丢用户工作、又不让磁盘堆积。

## 3. 功能需求

- F1: worktree 名称（slug）安全校验：限定字符集 `^[a-zA-Z0-9._-]+$`、长度上限 64、按 `/` 切段、显式拒绝 `.` / `..` 段和空段，校验失败返回带原因的错误字符串；任何 git 命令或路径拼接之前先跑。
- F2: slug 到路径和分支的映射：`flatten_slug` 把 `/` 替换为 `+`，避免嵌套 slug 导致目录或分支命名冲突（Git D/F conflict）；分支统一加 `worktree-` 前缀，方便从 `git branch` 输出里识别 MewCode 创建的。
- F3: 快速恢复路径：worktree 目录已存在时 `read_worktree_head_sha` 纯文件系统读 `.git` 指针 → `gitdir` → `commondir` → `HEAD` → loose ref / packed-refs，跳过 git 子进程；任一步失败返回 `None`，调用方回退到完整创建路径。
- F4: git 子进程统一安全壳：所有 git 调用关闭终端密码提示（`GIT_TERMINAL_PROMPT=0`）、屏蔽 `GIT_ASKPASS=""`、`stdin=subprocess.DEVNULL`，绝不挂起等待用户输入；统一 `timeout=60`，失败返回 `CompletedProcess` 而不是抛异常。
- F5: 创建/恢复主入口 `WorktreeManager.create`：先做 slug 校验和 `active` 字典重名检查，命中已存在目录走快速恢复（不重跑创建后设置），未命中 `os.makedirs(worktree_dir, exist_ok=True)` → `git worktree add -B worktree-<flat> <path> <base_branch>`（大写 `-B` 容忍上次未清的孤儿分支），默认 `base_branch="HEAD"`。
- F6: 创建后设置四项 `perform_post_creation_setup`：依次执行 — A `_copy_local_configs` 复制 `LOCAL_CONFIG_FILES` 里列出的 `settings.local.json` / `.env`（不存在静默跳过）；B `_setup_git_hooks` 优先 `<repo>/.husky` 回退 `<repo>/.git/hooks`，找到目录后在 worktree 里跑 `git config core.hooksPath`；C `_create_symlinks` 从 `WorktreeManager.symlink_directories` 读列表，逐个 `os.symlink(src, dst)`，错误日志吞掉不抛；D `_copy_ignored_files` 读 `<repo>/.worktreeinclude`（跳空行和 `#`）→ `git ls-files --others --ignored --exclude-standard --directory` 列出 gitignored → `fnmatch` 筛选 → 命中的 `shutil.copy2`。
- F7: 会话级 API 三件套：`create`（先快速恢复，未命中走 git add + 创建后设置）、`enter`（清缓存 + 记 `original_cwd` / `original_branch` / `original_head_commit` + 写 `current_session` + 持久化）、`exit`（变更保护 + 清缓存 + 清单例 + 删持久化，`action="remove"` 时调 `_remove_worktree`）。
- F8: 会话持久化：`save_worktree_session` 把 `WorktreeSession` 7 字段 dump 成 `<repo>/.mewcode/worktree_session.json`；`session=None` 时写 `"{}"`（等价清空）；`load_worktree_session` 容忍文件缺失、JSON 损坏、空 dict、缺字段全部返 `None` 并 warning 日志。
- F9: 启动恢复：`WorktreeManager.restore_session` 读持久化文件 → `read_worktree_head_sha` 验证 worktree 路径仍然存在 → 命中时把 `Worktree` 写回 `active` 字典 + `current_session`；HEAD SHA 读不到则反向调用 `save_worktree_session(None)` 清掉脏文件。
- F10: 自动清理 API `auto_cleanup(name, head_commit)`：调 `has_worktree_changes` 看脏不脏，干净直接 `_remove_worktree` 返 `CleanupResult(kept=False)`，脏返 `CleanupResult(kept=True, path, branch)`；供 SubAgent 完成后调用。
- F11: SubAgent 集成：`AgentTool._execute_with_worktree` 当 `definition.isolation == "worktree"` 时，调 `generate_worktree_name` 生成 `agent-<8hex>` slug → `worktree_manager.create(wt_name, "HEAD")` → `build_worktree_notice(parent_cwd, wt.path)` 拼接到 prompt 前 → `sub_agent.work_dir = wt.path` + `PathSandbox(wt.path)` 锁定权限边界。
- F12: 子 Agent 完成后决策：`auto_cleanup(wt_name, wt.head_commit)` 干净 → 自动清理 worktree，脏 → 保留并在结果末尾附 `[Worktree preserved at <path>, branch <branch>]` 给主 Agent review。
- F13: 变更保护：`ExitWorktreeTool` 在 `action="remove"` 且 `discard_changes` 不为 True 时调 `count_worktree_changes`，`uncommitted > 0 or new_commits > 0` 拒绝并把具体数（file/files 和 commit/commits 单复数正确）回吐给 LLM。
- F14: 变更检测 fail-closed：`count_worktree_changes` 的 `_run_git` 抛 `SubprocessError / OSError / ValueError` 时把对应计数置 1（按"有变更"处理）；`has_unpushed_commits` 在 git 失败时返 `True`，绝不在 git 命令失败时清掉用户工作。
- F15: LLM Tool 暴露：`EnterWorktreeTool`（input 仅可选 `name`，已有 session 时拒绝 "Already in a worktree session"）和 `ExitWorktreeTool`（input `action` 必填，`discard_changes` 可选，无 session 时返回 "No-op: there is no active EnterWorktree session..."）；两个工具 `should_defer = True`，由主 Agent loop 在工具批次结束时统一执行。
- F16: 临时 worktree 命名模式：用前缀化的固定模式区分自动产物（`agent-<8hex>` / `wf_<8hex>-<3hex>-<n>` / `wf-<n>` / `bridge-<id>` / `job-<slug>-<8hex>`）和用户手动命名；正则在 `EPHEMERAL_PATTERNS` 集中维护，便于新增来源时统一加入。
- F17: 后台过期清理三层过滤：`cleanup_stale_worktrees` 周期扫 `worktree_dir`，依次过滤 —— L1 命名模式（用户起名的永不删，廉价）→ L2 时态（跳过当前 session 占用的 + `info.stat().st_mtime > cutoff`）→ L3 git 状态 fail-closed（`has_worktree_changes` 或 `has_unpushed_commits` 任一为 True 都跳过）；通过的删 worktree + 删分支。

## 4. 非功能需求

- N1: `WorktreeManager` 用 `asyncio.Lock` 保护 `create`，并发创建同名 worktree 互斥；`active` 字典和 `current_session` 用同一锁覆盖。
- N2: 任何路径的 worktree 删除（会话级 exit / Agent 级 auto_cleanup / 后台清理）都要保证当前 cwd 不在 worktree 内（`_run_git` 的 `cwd` 缺省走 `repo_root`），否则 `git worktree remove` 会失败。
- N3: `git worktree remove` 和 `git branch -D` 之间必须 `await asyncio.sleep(0.1)` 等 git lockfile 释放，否则 branch 删除会偶发失败。
- N4: `restore_session` 在 HEAD SHA 读不到时必须主动 `save_worktree_session(None)` 清脏文件，否则下次启动会反复尝试恢复同一个已损坏的 session。
- N5: 三层过滤的执行顺序固定：先廉价的命名模式 → 再时态判断 → 最后贵的 git 检查；任何一层判定保留都立即 `continue`，不进入下一层。
- N6: 创建后设置的四项里软链接和 `.worktreeinclude` 复制是 best-effort —— 单文件失败只 `log.warning` 不抛，保证主路径鲁棒。
- N7: 变更保护的错误信息必须包含具体数字（N file/files + M commit/commits）和单复数语法正确，让 LLM 能据此判断要不要强删；不能只回 "has changes" 这种空话。
- N8: worktree 子系统不假设统一日志层存在，所有创建/退出/清理的信息通过工具结果文本传达；这同时是给 LLM 的运行时反馈。日志只用 `logging.getLogger(__name__)`。

## 5. 设计概要

- 核心数据结构（`mewcode/worktree/models.py`）:
 - `Worktree`：`name / path / branch / based_on / head_commit / created`（dataclass，活跃 worktree 注册项）。
 - `WorktreeSession`：`original_cwd / worktree_path / worktree_name / original_branch / original_head_commit / session_id / hook_based`（dataclass，会话级单例，序列化到 JSON）。
 - `Changes`：`uncommitted / new_commits`（dataclass，变更计数）。
 - `CleanupResult`：`kept / path / branch`（dataclass，Agent 级自动清理返回值）。
 - `WorktreeManager`：持有 `repo_root / file_cache / symlink_directories / worktree_dir / _lock / active / current_session`，是所有 worktree 操作的入口。
- 主流程:
 - **会话级 Enter**：`EnterWorktreeTool.execute` → guard `get_current_session() != None` → `validate_slug` → `WorktreeManager.create(slug)`（自动走快速恢复或 add + setup）→ `WorktreeManager.enter(slug)` → 返回带路径和分支的 Tool 文本。
 - **会话级 Exit**：`ExitWorktreeTool.execute` → guard 无 session → 若 `action="remove"` 且未 `discard_changes` 跑 `count_worktree_changes` → `WorktreeManager.exit(name, action, discard_changes)` → action=remove 时调 `_remove_worktree`（git worktree remove → sleep 0.1 → git branch -D）。
 - **Agent 级隔离**：`AgentTool.execute` 看到 `definition.isolation == "worktree"` → `_execute_with_worktree` → `generate_worktree_name` 出 `agent-<8hex>` → `worktree_manager.create(wt_name, "HEAD")` → `build_worktree_notice` 拼 prompt 前缀 → `sub_agent.work_dir = wt.path` + `PathSandbox(wt.path)` → 跑完调 `auto_cleanup`。
 - **后台过期清理**：`app.py` 启动 `asyncio.create_task(start_stale_cleanup_task(...))` → 死循环 `await asyncio.sleep(interval)` → `cleanup_stale_worktrees` 三层过滤 → 通过的删。
- 调用链（模块层级）:
 - `mewcode/app.py` 启动 → `WorktreeManager(repo_root=...)` 构造 → `restore_session` → 注册 `EnterWorktreeTool` / `ExitWorktreeTool` / `create_worktree_command` → `asyncio.create_task(start_stale_cleanup_task)`。
 - LLM Enter/Exit → 工具 registry → `mewcode/worktree/manager.py` 会话级 API。
 - `AgentTool` → 看到 isolation worktree → `WorktreeManager.create` + `build_worktree_notice` → 子 Agent 跑完 → `auto_cleanup`。
- 与其他模块的交互:
 - 依赖 `mewcode/tools`（注册两个工具）、`mewcode/agents`（隔离分流）、`mewcode/teams`（TeamManager 共用同一 manager）、`mewcode/commands`（`/worktree` 子命令）、`mewcode/cache`（FileCache 清理钩子）；底层只依赖 `asyncio` + `subprocess`（git）+ 标准库（`re` / `json` / `pathlib` / `secrets` / `fnmatch` / `shutil`）+ `pydantic`（工具 schema）。
 - 不依赖 `mewcode/memory` / `mewcode/prompt`。

## 6. Out of Scope

- 不实现非 git VCS 适配（hg / jj / sapling 等），所有 worktree 操作 hardcode 走 git 子命令
- 不实现 sparse checkout / partial clone 优化，大型 mono-repo 优化推到后续
- 不实现 `--worktree` / `--worktree --tmux` CLI 启动快速路径（涉及 tmux / iTerm2 子系统，留给 ch15）
- 不实现 PR fetch 或 pull request 头引用解析（远端协作场景）
- 不实现 prepare-commit-msg hook 注入 commit attribution（商业 feature 场景）
- 不实现 FindCanonicalGitRoot 穿透 commondir 的独立工具（Python 版仅以 `repo_root` 注入为主，多级嵌套 worktree 留给后续）
- 不引入第三方 gitignore 库（`fnmatch` 简化匹配够用）
- 团队成员（teammate）路径的 worktree 自动清理推到 ch15 收尾，本章 teammate 路径只创建并隔离、不负责清理

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch14: Worktree Tasks

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 实现 Slug 校验 + 命名映射
- 影响文件: `mewcode/worktree/slug.py`（`MAX_SLUG_LENGTH` @ 5；`_SEGMENT_RE` @ 6；`validate_slug` @ 9-24；`flatten_slug` @ 27-28）
- 依赖任务: 无
- 完成标准: `validate_slug` 校验长度 ≤ 64、按 `/` 切段、每段匹配 `^[a-zA-Z0-9._-]+$`、显式拒绝空段和 `.` / `..` 段，错误返回带原因字符串，合法返回 `None`；`flatten_slug(s) = s.replace("/", "+")`；分支名拼接由调用方做 `f"worktree-{flat_slug}"`。
- [ ] 完成

## T2: 定义数据模型
- 影响文件: `mewcode/worktree/models.py`（`Worktree` @ 7-14；`WorktreeSession` @ 17-25）
- 依赖任务: 无
- 完成标准: `Worktree` dataclass 含 6 字段（`name / path / branch / based_on / head_commit / created`），`created` 默认 `datetime.now`；`WorktreeSession` dataclass 含 7 字段（`original_cwd / worktree_path / worktree_name / original_branch / original_head_commit / session_id="" / hook_based=False`），后两字段有默认值。
- [ ] 完成

## T3: 实现变更检测 fail-closed
- 影响文件: `mewcode/worktree/changes.py`（`GIT_ENV` @ 9；`_run_git` @ 12-22；`Changes` @ 25-28；`count_worktree_changes` @ 31-51；`has_worktree_changes` @ 54-56；`CleanupResult` @ 59-63；`has_unpushed_commits` @ 66-74）
- 依赖任务: 无
- 完成标准: `_run_git` 强制 `env={**os.environ, **GIT_ENV}` + `timeout=30`；`count_worktree_changes` 跑 `git status --porcelain` + `git rev-list --count <head>..HEAD`，任一 `SubprocessError / OSError / ValueError` 把对应字段置 1（**fail-closed**）；`has_worktree_changes` 任一计数 > 0 返 True；`has_unpushed_commits` 跑 `git rev-list --max-count=1 HEAD --not --remotes`，git 失败返 True；`CleanupResult` dataclass 含 `kept / path / branch`。
- [ ] 完成

## T4: 实现 SubAgent worktree 上下文 notice
- 影响文件: `mewcode/worktree/integration.py`（`WORKTREE_NOTICE_TEMPLATE` @ 9-20；`generate_worktree_name` @ 23-24；`build_worktree_notice` @ 27-31）
- 依赖任务: 无
- 完成标准: `WORKTREE_NOTICE_TEMPLATE` 多行字符串，含 `[WORKTREE CONTEXT]` / `[/WORKTREE CONTEXT]` 标记、`{wt_path}` 和 `{parent_cwd}` 占位、关键句 "running in an isolated Git Worktree"、"translate them to your local worktree path"、"re-read files before editing"；`generate_worktree_name()` 返回 `f"agent-{secrets.token_hex(4)}"`（8 hex 字符，匹配 cleanup `^agent-a[0-9a-f]{7}$` 不严格但实际产出 `agent-` 开头 8 hex）；`build_worktree_notice(parent_cwd, wt_path)` 用 `.format()` 注入两个占位。
- [ ] 完成

## T5: 实现会话持久化
- 影响文件: `mewcode/worktree/session.py`（`SESSION_FILENAME` @ 11；`_session_path` @ 14-15；`save_worktree_session` @ 18-36；`load_worktree_session` @ 39-58）
- 依赖任务: T2
- 完成标准: `SESSION_FILENAME = "worktree_session.json"`；`save_worktree_session(mewcode_dir, session)`：`mkdir(parents=True, exist_ok=True)` → `session is None` 时写 `"{}"` 等价清空 → 否则 dump 7 字段到 JSON；`load_worktree_session`：文件不存在返 `None`，`JSONDecodeError / KeyError` 时 `log.warning` 后返 `None`，dict 为空或缺 `worktree_path` 返 `None`，否则构造 `WorktreeSession`，`session_id` / `hook_based` 用 `data.get(...)` 容忍旧版字段缺失。
- [ ] 完成

## T6: 实现创建后设置四项
- 影响文件: `mewcode/worktree/setup.py`（`LOCAL_CONFIG_FILES` @ 12-15；`perform_post_creation_setup` @ 18-29；`_copy_local_configs` @ 32-41；`_setup_git_hooks` @ 44-67；`_create_symlinks` @ 70-82；`_copy_ignored_files` @ 85-131）
- 依赖任务: 无
- 完成标准: `perform_post_creation_setup` 依序调四项 A/B/C/D；`LOCAL_CONFIG_FILES = ["settings.local.json", ".env"]`；A `_copy_local_configs` 用 `shutil.copy2`，`OSError` 仅 warning 不抛；B `_setup_git_hooks` 优先 `<repo>/.husky` 回退 `<repo>/.git/hooks`，找到目录跑 `git config core.hooksPath`；C `_create_symlinks` 遍历 `directories`，跳已存在和不存在的，`OSError` warning；D `_copy_ignored_files` 读 `.worktreeinclude`（跳空行和 `#`）→ `git ls-files --others --ignored --exclude-standard --directory` → `fnmatch.fnmatch` 筛选 → 单文件失败 `continue` 不中断。
- [ ] 完成

## T7: 实现 WorktreeManager 主类 + 快速恢复
- 影响文件: `mewcode/worktree/manager.py`（`GIT_ENV` @ 28；`WorktreeError` @ 31-32；`WorktreeManager.__init__` @ 36-54；`add_cache_clear_callback` @ 56-57；`_clear_all_caches` @ 59-66；`_run_git` @ 68-78；`read_worktree_head_sha` @ 84-128；`_get_current_branch` @ 316-321；`_get_head_commit` @ 323-328）
- 依赖任务: T1, T3
- 完成标准: `WorktreeManager` 持有 `repo_root / file_cache / symlink_directories / worktree_dir / _mewcode_dir / _lock=asyncio.Lock() / active: dict / current_session: WorktreeSession | None`；`worktree_dir` 默认 `<repo_root>/.mewcode/worktrees`；`_run_git` 强制 `env={**os.environ, **GIT_ENV}` + `cwd=cwd or repo_root` + `stdin=subprocess.DEVNULL` + `timeout=60`；`read_worktree_head_sha` 静态方法，完整链路（`.git pointer → gitdir → commondir → HEAD → loose ref/packed-refs`），失败返 `None`，目标延迟无 git 子进程。
- [ ] 完成

## T8: 实现 create + enter + exit + _remove_worktree
- 影响文件: `mewcode/worktree/manager.py`（`create` @ 134-186；`enter` @ 192-212；`exit` @ 218-243；`_remove_worktree` @ 249-260；`auto_cleanup` @ 266-275；`list_worktrees / get_current_session` @ 281-285；`restore_session` @ 291-310）
- 依赖任务: T2, T5, T6, T7
- 完成标准: `create` 在 `async with self._lock` 内：`validate_slug` → `active` 字典重名检查 → 快速恢复（`read_worktree_head_sha` 命中直接构造 `Worktree`，**不**跑 setup）→ 未命中 `os.makedirs(worktree_dir, exist_ok=True)` → `git worktree add -B worktree-<flat> <path> <base_branch>` → `perform_post_creation_setup`；`enter`：`_clear_all_caches` → `os.getcwd` + `_get_current_branch` + `_get_head_commit` → 写 `current_session` + `save_worktree_session`；`exit`：`action="remove" and not discard_changes` 时变更保护抛 `WorktreeError` 含具体计数 → 清缓存 + 清单例 + `save_worktree_session(None)` → `action="remove"` 调 `_remove_worktree`；`_remove_worktree`：`git worktree remove --force` → `await asyncio.sleep(0.1)` → `git branch -D worktree-<flat>` → `active.pop`；`auto_cleanup`：脏返 `CleanupResult(kept=True, path, branch)`，干净 `_remove_worktree` 返 `CleanupResult(kept=False)`；`restore_session`：读持久化 → `read_worktree_head_sha` 验证 → 命中写回 `active` + `current_session`，未命中调 `save_worktree_session(None)` 清脏。
- [ ] 完成

## T9: 实现后台过期清理
- 影响文件: `mewcode/worktree/cleanup.py`（`EPHEMERAL_PATTERNS` @ 16-22；`_is_ephemeral` @ 25-26；`cleanup_stale_worktrees` @ 29-81；`start_stale_cleanup_task` @ 84-96）
- 依赖任务: T3, T8
- 完成标准: `EPHEMERAL_PATTERNS` 五条正则：`^agent-a[0-9a-f]{7}$` / `^wf_[0-9a-f]{8}-[0-9a-f]{3}-\d+$` / `^wf-\d+$` / `^bridge-[A-Za-z0-9_]+(-[A-Za-z0-9_]+)*$` / `^job-[a-zA-Z0-9._-]{1,55}-[0-9a-f]{8}$`；`_is_ephemeral` 任一正则 match 返 True；`cleanup_stale_worktrees(manager, cutoff_hours)` 三层过滤 — **L1 命名**：`_is_ephemeral` False 跳；**L2 时态**：`current_session.worktree_name == name` 跳 + `mtime > cutoff` 跳；**L3 git 状态 fail-closed**：`read_worktree_head_sha is None` 跳 + `has_worktree_changes` 跳 + `has_unpushed_commits` 跳；通过的复用 `_remove_worktree` 或直接 `git worktree remove --force` + `sleep(0.1)` + `git branch -D`；返回清理数；`start_stale_cleanup_task(manager, interval, cutoff_hours)`：死循环 `await asyncio.sleep(interval)` → `cleanup_stale_worktrees` → 异常 `log.warning` 不抛。
- [ ] 完成

## T10: 包级 `__init__.py` 导出
- 影响文件: `mewcode/worktree/__init__.py`（导出 14 个公共符号 + `__all__`）
- 依赖任务: T1, T2, T3, T5, T8, T9
- 完成标准: 从 `changes` 导出 `Changes / CleanupResult / count_worktree_changes / has_worktree_changes`；从 `cleanup` 导出 `cleanup_stale_worktrees / start_stale_cleanup_task`；从 `manager` 导出 `WorktreeError / WorktreeManager`；从 `models` 导出 `Worktree / WorktreeSession`；从 `session` 导出 `load_worktree_session / save_worktree_session`；从 `slug` 导出 `flatten_slug / validate_slug`；`__all__` 列出 14 个名字按字母序。
- [ ] 完成

## T11: 实现 EnterWorktreeTool
- 影响文件: `mewcode/tools/enter_worktree.py`（`EnterWorktreeParams` @ 15-23；`EnterWorktreeTool` @ 26-65）
- 依赖任务: T1, T8
- 完成标准: `EnterWorktreeParams` 用 pydantic 定义，仅 `name: Optional[str]` 字段含描述；`EnterWorktreeTool`：`name = "EnterWorktree"` / `category = "command"` / `should_defer = True` / `params_model = EnterWorktreeParams`；`__init__(self, worktree_manager)`；`execute`：`get_current_session() is not None` → 返 `ToolResult(output="Already in a worktree session", is_error=True)` → 否则 `slug = params.name or f"wt-{secrets.token_hex(4)}"` → `validate_slug` 失败返错 → `manager.create(slug)` + `manager.enter(slug)` → 返回 `ToolResult(output=f"Created worktree at {session.worktree_path} on branch {wt.branch}. The session is now working in the worktree. Use ExitWorktree to leave mid-session, or exit the session to be prompted.")`。
- [ ] 完成

## T12: 实现 ExitWorktreeTool
- 影响文件: `mewcode/tools/exit_worktree.py`（`ExitWorktreeParams` @ 14-25；`ExitWorktreeTool` @ 28-110）
- 依赖任务: T3, T8
- 完成标准: `ExitWorktreeParams`：`action: str` 必填 + `discard_changes: Optional[bool] = None`；`ExitWorktreeTool`：`name = "ExitWorktree"` / `should_defer = True`；`execute`：`get_current_session() is None` → 返 "No-op: there is no active EnterWorktree session to exit. This tool only operates on worktrees created by EnterWorktree in the current session — it will not touch worktrees created manually or in a previous session. No filesystem changes were made."（`is_error=True`）；`action not in ("keep", "remove")` 返非法值；`action == "remove" and not discard` 时 `count_worktree_changes` → `uncommitted/new_commits > 0` 拼具体数（**单复数 file/files、commit/commits 正确**）→ `manager.exit(wt_name, action, discard_changes=discard)` → keep 返 "Your work is preserved at ... Session is now back in ..."，remove 返 "Exited and removed worktree at ..."。
- [ ] 完成

## T13: 实现 `/worktree` 本地命令
- 影响文件: `mewcode/commands/handlers/worktree.py`（`create_worktree_command` @ 11-49；`_handle_create` @ 52-85；`_handle_list` @ 88-110 附近；`_handle_enter` / `_handle_exit` / `_handle_status`）
- 依赖任务: T8
- 完成标准: `create_worktree_command(manager)` 返回 `Command(name="worktree", aliases=["wt"], type=CommandType.LOCAL)`；子命令解析 `create / list / enter / exit / status`，未知子命令报 "未知子命令: ..."；`_handle_create` 调 `manager.create + manager.enter` 并同步 `ctx.agent.work_dir`；`_handle_exit` 解析 `--remove` / `--discard` 标志映射到 `action / discard_changes`；`_handle_list` 列出 `manager.list_worktrees` 标当前；`_handle_status` 输出当前 session 路径和原始分支。
- [ ] 完成

## T14: 接入 AgentTool worktree 隔离
- 影响文件: `mewcode/tools/agent_tool.py`（`AgentToolParams` 含 `isolation` @ 27；`__init__` 接 `worktree_manager` @ 71/80；`execute` 解析 isolation @ 89-96；`_execute_with_worktree` @ 491-610）
- 依赖任务: T4, T8, T11
- 完成标准: `AgentToolParams` 含 `isolation: str | None = None` 和 `team_name: str | None = None`；`AgentTool.__init__` 多两个可选参数 `worktree_manager / team_manager`；`execute` 在 `p.team_name` 时走 teammate 分支，否则按 `definition.isolation == "worktree"` 分流 `_execute_with_worktree`；`_execute_with_worktree`：`worktree_manager is None` 报错 → `generate_worktree_name` 出 `agent-<8hex>` → `manager.create(wt_name, "HEAD")` → `notice = build_worktree_notice(parent_cwd, wt.path)` → `task = notice + "\n\n" + p.prompt` → 构造子 Agent `work_dir=wt.path` + `PathSandbox(wt.path)` → `run_to_completion(task)` → `manager.auto_cleanup(wt_name, wt.head_commit)` → `cleanup.kept` 时结果末尾拼 `[Worktree preserved at <path>, branch <branch>]`。
- [ ] 完成

## T15: 接入 app.py 启动装配
- 影响文件: `mewcode/app.py`（imports @ 82-84；worktree setup 段 @ 691-722；teardown @ 1602-1605）
- 依赖任务: T8, T9, T11, T12, T13, T14
- 完成标准:
 1. `WorktreeConfig` 注入 `symlink_directories / stale_cleanup_interval / stale_cutoff_hours`；
 2. `self.worktree_manager = WorktreeManager(repo_root=work_dir, file_cache=self.file_cache, symlink_directories=wt_cfg.symlink_directories)`；
 3. `add_cache_clear_callback` 加 skills 清理钩子；
 4. `restored = self.worktree_manager.restore_session()` 非 None 时 `self.agent.work_dir = restored.worktree_path`；
 5. `create_worktree_command(self.worktree_manager)` + `command_registry.register_sync`；
 6. `registry.register(EnterWorktreeTool(...))` + `registry.register(ExitWorktreeTool(...))`；
 7. `self._stale_cleanup_task = asyncio.create_task(start_stale_cleanup_task(self.worktree_manager, wt_cfg.stale_cleanup_interval, wt_cfg.stale_cutoff_hours))`；
 8. TeamManager 和 AgentTool 共用同一 `worktree_manager` 注入；
 9. teardown 时遍历 `worktree_manager.active.values()` 清理残留。
- [ ] 完成

## T16: 端到端验证
- 影响文件: 无（仅运行）
- 依赖任务: T1-T15
- 完成标准:
 - `ruff check mewcode/worktree mewcode/tools/enter_worktree.py mewcode/tools/exit_worktree.py` 通过；
 - `pytest tests/test_worktree.py -v` 通过（含 `TestValidateSlug` / `TestFlattenSlug` / `TestSessionPersistence` / `TestWorktreeManager` / `TestChangeDetection` / `TestReadWorktreeHeadSha` 等组）；
 - **路径 A — 工具直接驱动**：主 Agent 调 `EnterWorktree({name: "demo"})` 创建 worktree → 在 worktree 里 `WriteFile + Bash("git commit ...")` → `ExitWorktree({action: "remove"})` 被变更保护拒绝并列出具体数 → `ExitWorktree({action: "remove", discard_changes: true})` 强删成功；
 - **路径 B — 子 Agent 自动隔离**：主 Agent 在主目录 `WriteFile witness.txt = "original content from main agent"` → 调 `Agent({subagent_type: "<声明 isolation worktree 的类型>", prompt: "把 witness.txt 改成 ..."})` → 验证主目录 `witness.txt` 内容不变；`.mewcode/worktrees/agent-*/witness.txt` 是修改后版本；若有 commit → 结果末尾出现 `[Worktree preserved at ..., branch worktree-agent-...]`。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13 / [ ] T14 / [ ] T15 / [ ] T16
```
```plain
# ch14: Worktree Checklist

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 常量 `MAX_SLUG_LENGTH = 64` 在 `mewcode/worktree/slug.py:5` 定义
- [ ] 函数 `validate_slug` 在 `mewcode/worktree/slug.py:9-24` 含空名、长度、空段、`.` / `..`、非法段五类错误分类
- [ ] 函数 `flatten_slug` 在 `mewcode/worktree/slug.py:27-28` 把 `/` 替换成 `+`；分支名由调用方拼 `f"worktree-{flat_slug}"`
- [ ] dataclass `Worktree` 在 `mewcode/worktree/models.py:7-14` 含 6 字段（`name / path / branch / based_on / head_commit / created`）
- [ ] dataclass `WorktreeSession` 在 `mewcode/worktree/models.py:17-25` 含 7 字段，`session_id` / `hook_based` 有默认值
- [ ] dataclass `Changes` 在 `mewcode/worktree/changes.py:25-28`，`CleanupResult` 在 `mewcode/worktree/changes.py:59-63`
- [ ] 函数 `count_worktree_changes` 在 `mewcode/worktree/changes.py:31-51`，git 子进程异常时把对应计数置 1（**fail-closed**）
- [ ] 函数 `has_worktree_changes` 在 `mewcode/worktree/changes.py:54-56`，`has_unpushed_commits` 在 `:66-74` git 失败默认返 True
- [ ] 字符串 `WORKTREE_NOTICE_TEMPLATE` 在 `mewcode/worktree/integration.py:9-20` 含 `{parent_cwd}` / `{wt_path}` 占位 + "re-read files before editing" 关键句
- [ ] 函数 `generate_worktree_name` 在 `mewcode/worktree/integration.py:23-24` 用 `secrets.token_hex(4)` 出 `agent-` 开头 8 hex 名字
- [ ] 函数 `save_worktree_session` 在 `mewcode/worktree/session.py:18-36`，`session is None` 时写 `"{}"`（清空）
- [ ] 函数 `load_worktree_session` 在 `mewcode/worktree/session.py:39-58` 容忍文件缺失、JSON 损坏、空 dict、缺字段全部返 `None`
- [ ] 常量 `LOCAL_CONFIG_FILES` 在 `mewcode/worktree/setup.py:12-15` 含 `settings.local.json` + `.env`
- [ ] 函数 `perform_post_creation_setup` 在 `mewcode/worktree/setup.py:18-29` 依序调四项 A/B/C/D
- [ ] 函数 `_copy_ignored_files` 在 `mewcode/worktree/setup.py:85-131` 单文件失败 `continue` 不中断
- [ ] 类 `WorktreeManager` 在 `mewcode/worktree/manager.py:35-328` 持有 `_lock=asyncio.Lock() / active / current_session`
- [ ] 静态方法 `WorktreeManager.read_worktree_head_sha` 在 `mewcode/worktree/manager.py:84-128` 完整链路（`.git → gitdir → commondir → HEAD → loose/packed-refs`），失败返 `None`
- [ ] 方法 `WorktreeManager._run_git` 在 `mewcode/worktree/manager.py:68-78` 强制 `env=GIT_ENV + stdin=DEVNULL + timeout=60`
- [ ] 方法 `WorktreeManager.create` 在 `mewcode/worktree/manager.py:134-186` 实现"快速恢复 → 创建路径"二选一，使用 `-B` 大写参数
- [ ] 方法 `WorktreeManager.exit` 在 `mewcode/worktree/manager.py:218-243` 在 `action="remove" and not discard_changes` 时跑变更保护
- [ ] 方法 `WorktreeManager._remove_worktree` 在 `mewcode/worktree/manager.py:249-260` 含 `await asyncio.sleep(0.1)` 等 git lockfile 释放
- [ ] 方法 `WorktreeManager.auto_cleanup` 在 `mewcode/worktree/manager.py:266-275` 脏返 `kept=True` + path/branch，干净返 `kept=False`
- [ ] 方法 `WorktreeManager.restore_session` 在 `mewcode/worktree/manager.py:291-310` 在 `read_worktree_head_sha is None` 时反向 `save_worktree_session(None)` 清脏
- [ ] 变量 `EPHEMERAL_PATTERNS` 在 `mewcode/worktree/cleanup.py:16-22` 含五个正则（agent-a / wf_ / wf- / bridge- / job-）
- [ ] 函数 `cleanup_stale_worktrees` 在 `mewcode/worktree/cleanup.py:29-81` 三层过滤顺序固定（L1 命名 → L2 时态 → L3 git 状态）
- [ ] 函数 `start_stale_cleanup_task` 在 `mewcode/worktree/cleanup.py:84-96` 死循环 + 异常 warning 不抛
- [ ] 类 `EnterWorktreeTool` 在 `mewcode/tools/enter_worktree.py:26-65`，`should_defer = True` + `params_model = EnterWorktreeParams`
- [ ] 类 `ExitWorktreeTool` 在 `mewcode/tools/exit_worktree.py:28-110`，`should_defer = True`
- [ ] `ExitWorktreeTool.execute` 在 `mewcode/tools/exit_worktree.py:63-84` 单复数 file/files、commit/commits 正确处理

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -rn "EnterWorktreeTool" --include="*.py" mewcode/` 在 `mewcode/app.py:711-713` 找到 import + 注册
- [ ] `grep -rn "ExitWorktreeTool" --include="*.py" mewcode/` 在 `mewcode/app.py:712-714` 找到 import + 注册
- [ ] `grep -rn "WorktreeManager" --include="*.py" mewcode/` 至少命中 `mewcode/app.py:694`、`mewcode/tools/agent_tool.py`、`mewcode/teams/manager.py`、`mewcode/commands/handlers/worktree.py`
- [ ] `grep -rn "restore_session" --include="*.py" mewcode/` 在 `mewcode/app.py:704` 找到启动恢复调用
- [ ] `grep -rn "start_stale_cleanup_task" --include="*.py" mewcode/` 在 `mewcode/app.py:716-722` 找到 `asyncio.create_task` 包裹
- [ ] `grep -rn "build_worktree_notice" --include="*.py" mewcode/` 在 `mewcode/tools/agent_tool.py:544` 找到 prompt 拼接调用
- [ ] `grep -rn "generate_worktree_name" --include="*.py" mewcode/` 在 `mewcode/tools/agent_tool.py:535` 找到调用
- [ ] `grep -rn "auto_cleanup" --include="*.py" mewcode/` 在 `mewcode/tools/agent_tool.py:604` 找到子 Agent 完成后清理调用
- [ ] `grep -rn "count_worktree_changes" --include="*.py" mewcode/` 在 `mewcode/tools/exit_worktree.py:64` 和 `mewcode/worktree/manager.py:229` 找到调用
- [ ] `grep -rn "has_worktree_changes" --include="*.py" mewcode/` 在 `mewcode/worktree/cleanup.py:59` 和 `mewcode/worktree/manager.py:271` 找到调用
- [ ] `grep -rn "create_worktree_command" --include="*.py" mewcode/` 在 `mewcode/app.py:708` 找到 `/worktree` 命令注册
- [ ] `grep -rn "_execute_with_worktree" --include="*.py" mewcode/` 在 `mewcode/tools/agent_tool.py:96` 和 `:491` 找到分流入口

## 3. 编译与测试

- [ ] `ruff check mewcode/worktree mewcode/tools/enter_worktree.py mewcode/tools/exit_worktree.py mewcode/commands/handlers/worktree.py` 无报错
- [ ] `pytest tests/test_worktree.py -v` 通过（含 `TestValidateSlug` / `TestFlattenSlug` / `TestSessionPersistence` / `TestIntegrationHelpers` / `TestWorktreeManager` / `TestChangeDetection` / `TestReadWorktreeHeadSha` 等组）
- [ ] `python -c "from mewcode.worktree import WorktreeManager, validate_slug, flatten_slug; print('ok')"` 无 import 错误
- [ ] `python -m mypy mewcode/worktree` 或 `pyright mewcode/worktree` 无新增 type 错误

## 4. 端到端验证

- [ ] **路径 A — 工具直接驱动**：用户对主 Agent 说"用 EnterWorktree 工具创建一个名叫 demo 的工作树" → LLM 调 `EnterWorktree({name: "demo"})` → 返回 `Created worktree at .../.mewcode/worktrees/demo on branch worktree-demo`；让 Agent 在 worktree 里创建 `hello.txt` 并 `git commit`；让 Agent 调 `ExitWorktree({action: "remove"})` → 因有未推送 commit 被变更保护拒绝，错误文本包含具体 `1 commit` 或 `N commits`；`ExitWorktree({action: "remove", discard_changes: true})` 强删成功；`ls .mewcode/worktrees/` 看到 `demo/` 已消失。
- [ ] **路径 B — 子 Agent 自动隔离**：用户让主 Agent 在主目录建 `witness.txt`（内容 "original content from main agent"）→ 调 `Agent({subagent_type: "<声明 isolation worktree 的类型>", description: "...", prompt: "把 witness.txt 改成 \"modified by isolated worker\"，然后 git 提交"})`；验证 `cat witness.txt` 主目录内容仍是 "original ..."；`cat .mewcode/worktrees/agent-*/witness.txt` 是修改后版本；若子 Agent 有 commit → 结果末尾出现 `[Worktree preserved at ..., branch worktree-agent-...]`；若无修改 → worktree 自动清理（`.mewcode/worktrees/` 下 `agent-*` 目录消失）。
- [ ] **持久化与 crash 恢复**：TUI 里 `EnterWorktree({name: "crashtest"})` 创建 worktree → `Ctrl+C` 杀进程 → `cat .mewcode/worktree_session.json` 文件仍在并含 crashtest 会话；重启 MewCode → 启动期间 `restore_session` 把 session 写回；下一次工具调用时 `get_current_session()` 非 None，且 `agent.work_dir` 已切到 worktree 路径。
- [ ] **变更保护单复数**：在 worktree 里建 1 个未提交修改 → `ExitWorktree({action: "remove"})` 返回 `"1 uncommitted file"`；建 2+ 个修改 → 返回 `"N uncommitted files"`（注意单复数）；同样验证 commit 数 `"1 commit"` / `"N commits"`。
- [ ] **后台清理保守不删**：手动在 `.mewcode/worktrees/agent-aabcdef1/` 下建一个有未推送 commit 的目录（mtime 设为过期前）→ 等 cleanup loop 跑一轮（或手动 `await cleanup_stale_worktrees(manager, 1)` 测试）→ 该目录仍保留（L3 fail-closed 的 `has_unpushed_commits` 拦住）。
- [ ] **会话级 enter 时清理 FileCache**：在主仓里读一个文件触发 FileCache 命中 → `EnterWorktree` → 验证 `file_cache` 被清空（`len(file_cache) == 0`），保证后续读 worktree 不复用主仓的缓存。
- [ ] **`/worktree` 本地命令**：`/worktree create demo` 创建并进入 → `/worktree status` 显示当前 session → `/worktree list` 列出含 demo → `/worktree exit --remove --discard` 强删。

## 5. 文档

- [ ] `docs/python/ch14/spec.md` 已按 ch12/ch13 风格写完（F1-F17 + N1-N8，无 file:line 代码标注）
- [ ] `docs/python/ch14/tasks.md` 已写，16 个 T 全部勾完（T1-T16）
- [ ] `docs/python/ch14/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch14`，新增代码的调用链已在 PR 描述或 commit message 里说明
```

### Java

```plain
# ch14: Worktree Spec（Java 版）

## 1. 背景

SubAgent 隔离了消息、权限、工具结果缓存，但所有子 Agent 仍然共享同一个工作目录——两个子 Agent 并发改同一个文件会互相覆盖。Git 分支不解决这个问题：分支只是时间维度的快照，同一时刻整个仓库仍然只有一份 working tree，切换分支会动所有文件的修改时间触发不必要的全量重编。多 Agent 并行要的是空间维度的隔离：同时存在多份独立的 working tree，每份对应不同分支，但共享同一个 `.git`。Git Worktree 提供的就是这个能力。这一章把它接进 MewCode 的 Java 实现，让主 Agent 和每个子 Agent 都能拥有独立的文件视图。

## 2. 目标

把 worktree 做成两层 API：会话级让 LLM 通过 `EnterWorktreeTool` / `ExitWorktreeTool` 自主进出 worktree，Agent 级让 SubAgent 通过 `isolation: "worktree"` 声明自动获得独立 worktree。底层共用 `WorktreeManager` 的 `git worktree add/remove` 调用、`AgentWorktree` 的快速恢复路径，以及 `PostCreationSetup`（本地配置复制 / git hooks 配置 / 大目录软链接 / `.worktreeinclude` 文件复制）。叠加 `WorktreeChanges` 的 fail-closed 变更检测（无变更才允许清掉、有变更默认保留）和 `StaleCleanup` 对孤儿 worktree 的后台过期清理，保证既不丢用户工作、又不让磁盘堆积。

## 3. 功能需求

- F1: worktree 名称（slug）安全校验：限定字符集、长度上限 64、按 `/` 切段、显式拒绝 `.` / `..` 段，校验失败抛 `IllegalArgumentException` 分类错误（长度 / 段名非法 / 路径遍历）；任何 git 命令或路径拼接之前先跑。
- F2: slug 到路径和分支的映射：用 `+` 替换 `/`（git 安全但不在 slug 字符集），避免嵌套 slug 导致目录或分支命名冲突；分支统一加 `worktree-` 前缀，方便从 `git branch` 输出里识别 MewCode 创建的。
- F3: 快速恢复路径：worktree 目录已存在时跳过 `git worktree add`，用 `Files.isDirectory` + `Files.setLastModifiedTime` bump mtime + 调一次 `git rev-parse HEAD` 拿 SHA；任一步失败回退到完整创建路径。
- F4: git 子进程统一安全壳：所有 `ProcessBuilder` 调用都在 `environment()` 里写 `GIT_TERMINAL_PROMPT=0` 和 `GIT_ASKPASS=`，绝不挂起等待用户输入；用 `waitFor(N, TimeUnit.SECONDS)` 超时保护，超时后 `destroyForcibly()`；进程失败抛 `IOException` 而不是 `RuntimeException`。
- F5: 创建/恢复主入口：`WorktreeManager.create` 接收 branch + 可选 targetDir，未给 targetDir 时默认 `<projectRoot>/.mewcode/worktrees/<branch>`，用大写 `-B` 创建 worktree（容忍上次未清干净的孤儿分支）；`AgentWorktree.create` 在 slug 校验后先看目录是否存在，命中则快速恢复，未命中跑 `git worktree add -B <branch> <path> HEAD`。
- F6: 创建后设置四项：从主仓复制 `.mewcode/settings.local.json`；按 `.husky` > `.git/hooks` 优先级在 worktree 里跑 `git config core.hooksPath <path>`；按 `WorktreeManager.symlinkDirs` 配置软链接 `node_modules` 等目录（跳过含 `..` 项）；按 `.worktreeinclude` gitignore 风格模式复制被 `.gitignore` 忽略但运行需要的文件；任何单项失败只记日志、不中断创建。
- F7: 会话级 API 三件套：进入（`WorktreeManager.create` + 写 `WorktreeSessionStore` 单例 + 持久化 JSON）、Keep（`ExitWorktreeTool action=keep`：清单例 + 删持久化文件，保留 worktree 目录和分支）、Remove（`action=remove`：清单例 + 删持久化 + `WorktreeManager.remove`）。
- F8: 会话持久化：`WorktreeSessionStore.save` 把 `WorktreeSession` record 序列化到 `<repo>/.mewcode/worktree_session.json`，用 Jackson `ObjectMapper` + `@JsonProperty` snake_case 映射；`save(repo, null)` 等价于 `Files.deleteIfExists`。
- F9: 启动恢复：应用启动时调 `WorktreeSessionStore.load(repoRoot)`，非 null 时调 `restoreSession` 写回 `volatile` 全局字段；不主动切 cwd（让用户或工具自行决定），不重跑创建后设置。
- F10: Agent 级 API：`AgentWorktree.create(slug, repoRoot, symlinkDirs)` 静态方法返回 `Result(worktreePath, worktreeBranch, headCommit, gitRoot)` record；不动 `WorktreeSessionStore` 单例、不切 JVM cwd、不写持久化；快速恢复路径要 `Files.setLastModifiedTime` 防被 `StaleCleanup` 误判为孤儿。
- F11: SubAgent 集成：`AgentTool` 在解析参数时拿到 `isolation: "worktree"` 且 `worktreeManager != null` 时，生成 `agent-a<7hex>` slug → 调 `AgentWorktree.create` → 把 `subAgent.setWorkDir(wtResult.worktreePath())` → 在任务 prompt 前面拼 `AgentWorktree.buildNotice(parentCwd, wtPath)` 注入隔离 notice → 跑子 Agent。
- F12: 子 Agent 完成后决策：`LoopComplete` 事件触发时调 `WorktreeChanges.hasChanges(wtPath, headCommit)`，干净自动 `AgentWorktree.remove`、脏则保留并在返回结果末尾附 `"Worktree kept at <path> (branch <branch>) — has uncommitted changes or new commits."`。
- F13: 变更保护：`ExitWorktreeTool` 在 `action="remove"` 且 `discard_changes` 不为 `true` 时跑 `WorktreeChanges.countChanges`——返回 null（状态无法验证）报 `"Could not verify worktree state..."`；`changedFiles > 0` 或 `commits > 0` 报具体数字（"N uncommitted file(s) and M commit(s)"）；要求 LLM 显式传 `discard_changes=true` 才能强删。
- F14: 变更检测 fail-closed：`WorktreeChanges.hasChanges` 在 git status / rev-list 任何一步失败（runGit 返 null 或抛异常）都返 `true`；`countChanges` 在状态拿不到时返 `null`，强制调用方按"未知即不安全"处理。
- F15: LLM Tool 暴露：`EnterWorktreeTool`（input 仅可选 `name`，已有 session 时拒绝 `"Already in a worktree session"`）和 `ExitWorktreeTool`（input `action` 必填枚举 `["keep","remove"]` / `discard_changes` 可选 bool，无 session 时拒绝）；两个 Tool 的 `shouldDefer()` 都返 `true`，由 Agent loop 在工具批次结束时统一执行。
- F16: 临时 worktree 命名模式：用前缀正则区分"自动产物"（`agent-a` / `wf_` / `wf-` / `bridge-` / `job-` 五类）和"用户手动命名"；用户起名永远不会被后台清理动。
- F17: 后台过期清理三层过滤：`StaleCleanup.cleanup` 扫 `<repo>/.mewcode/worktrees/`，依次过滤——L1 `isEphemeral`（不匹配五个正则的跳过）→ L2 时态（跳过当前 session 占用的 + `lastModifiedTime().toInstant().isAfter(cutoff)` 的）→ L3 git 状态 fail-closed（`status --porcelain -uno` 非空或失败跳过 + `rev-list --max-count=1 HEAD --not --remotes` 非空或失败跳过）；删完跑 `git worktree prune` 同步 git 内部表；`startCleanupLoop` 通过 `ScheduledExecutorService.scheduleAtFixedRate` 周期跑。

## 4. 非功能需求

- N1: `WorktreeSessionStore` 用 `volatile` + 静态字段保证并发可见性；`WorktreeManager` 所有公开方法 `synchronized` 保护内存里的 `LinkedHashMap<String, WorktreeInfo>`；Agent 级 API（`AgentWorktree.create/remove`）是无状态静态方法，天然并发安全。
- N2: 任何路径的 worktree 删除（会话级 Remove / Agent 级 Remove / 后台清理）都不在 worktree 内执行 git 命令——`AgentWorktree.remove` 显式从 `gitRoot` 跑 `ProcessBuilder` 的 `directory()`，否则 `git worktree remove` 会因为当前在被删目录里失败。
- N3: `git worktree remove` 和 `git branch -D` 之间必须 `Thread.sleep(100)` 等 git lockfile 释放，否则 branch 删除会偶发失败。
- N4: Agent 级 API 在快速恢复（worktree 目录已存在）时必须 `Files.setLastModifiedTime(wtPath, FileTime.from(Instant.now()))` bump mtime，否则同一 worktree 被反复复用时会因为 mtime 太老被 `StaleCleanup` 误删。
- N5: 三层过滤的执行顺序固定：先廉价的命名模式 → 再时态判断 → 最后贵的 git 检查；任何一层判定保留都 `continue`，不进入下一层。
- N6: `PostCreationSetup` 的四项里软链接和 `.worktreeinclude` 复制是 best-effort——`catch (IOException e)` 只 `log.fine` 不抛、不中断创建，保证主路径鲁棒。
- N7: 变更保护的错误信息必须包含具体数字（N 文件 + M commits）和单复数（"1 file" vs "2 files"、"1 commit" vs "2 commits"），让 LLM 能据此判断要不要强删；不能只回 "has changes" 这种空话。
- N8: worktree 子系统不假设统一日志层存在，所有创建/退出/清理的关键信息通过 `ToolResult` 文本传达；这同时是给 LLM 的运行时反馈，`java.util.logging.Logger` 只用于内部 best-effort 失败。

## 5. 设计概要

- 核心数据结构（全部 Java 17+ `record`）:
  - `WorktreeManager.WorktreeInfo(path, branch, createdAt)`：底层创建路径返回值，挂在 `WorktreeManager` 内存 map 里。
  - `AgentWorktree.Result(worktreePath, worktreeBranch, headCommit, gitRoot)`：Agent 级 API 返回值，不写全局状态。
  - `WorktreeSession(originalCwd, worktreePath, worktreeName, worktreeBranch, originalBranch, originalHeadCommit, sessionId, creationDurationMs)`：会话级单例，Jackson 序列化到磁盘，`@JsonProperty` 写 snake_case key。
  - `WorktreeChanges.ChangeSummary(changedFiles, commits)`：变更计数，供变更保护错误信息生成。
  - 配置块：`WorktreeManager` 构造参数 `symlinkDirs` + `staleCutoffHours`，由应用启动时注入；后台清理由 `StaleCleanup.startCleanupLoop` 单独调度，间隔 ≤ 0 时不启动。
- 主流程:
  - **会话级 Enter**：`EnterWorktreeTool.execute` → guard `WorktreeSessionStore.getCurrentSession() != null` → slug 校验（`SlugValidator.validate`）→ `WorktreeManager.create` → 组装 `WorktreeSession` record → `restoreSession` + `save`。
  - **会话级 Exit**：`ExitWorktreeTool.execute` → guard 无 session → 若 `action=remove && !discard_changes` 跑 `WorktreeChanges.countChanges` 变更保护 → 清单例 → `save(repo, null)` 删持久化 → `action=remove` 时调 `WorktreeManager.remove`。
  - **Agent 级隔离**：`AgentTool.runSync` → `isolation=="worktree" && worktreeManager != null` → 生成 `agent-a<7hex>` slug → `AgentWorktree.create` → `subAgent.setWorkDir(wtPath)` → `prompt = buildNotice(parentCwd, wtPath) + "\n\n" + prompt` → 跑子 Agent → `LoopComplete` 时 `WorktreeChanges.hasChanges`：干净 `AgentWorktree.remove` / 脏拼 `wtInfo` 后缀。
  - **后台过期清理**：`StaleCleanup.startCleanupLoop(executor, repoRoot, intervalSeconds, cutoffHours)` → `scheduleAtFixedRate` → 每轮 `cleanup(repoRoot, Instant.now().minusSeconds(cutoffHours*3600))` → 三层过滤 → 通过的 `AgentWorktree.remove` → 末尾若有删除跑一次 `git worktree prune`。
- 调用链（模块层级）:
  - 应用启动 → 构造 `WorktreeManager(projectRoot, symlinkDirs, staleCutoffHours)` → 注册 `EnterWorktreeTool` 和 `ExitWorktreeTool` → `WorktreeSessionStore.load + restoreSession` 恢复 session → `StaleCleanup.startCleanupLoop` 起后台任务。
  - LLM Enter/Exit → Tool dispatcher → `WorktreeManager` / `WorktreeSessionStore` / `WorktreeChanges`。
  - `AgentTool` → 看到 `isolation: worktree` → `AgentWorktree.create` → 子 Agent 跑完 → `WorktreeChanges.hasChanges` → `AgentWorktree.remove` 或拼字符串保留。
- 与其他模块的交互:
  - 依赖 `com.mewcode.tool`（Tool 接口 + ToolResult + ToolCategory）、`com.mewcode.subagent`（AgentTool 注入 `setWorktreeManager`）、`com.mewcode.agent`（`Agent.setWorkDir`）；底层只依赖 `ProcessBuilder`（git）+ `java.nio.file` + `com.fasterxml.jackson.databind.ObjectMapper`。
  - 不依赖 `com.mewcode.config` 通用加载链路——worktree 配置当前由应用启动时手动注入；也不依赖 `com.mewcode.memory` / `com.mewcode.prompt`。

## 6. Out of Scope

- 不实现非 git VCS 适配（hg / jj / sapling 等），所有 worktree 操作 hardcode 走 `ProcessBuilder("git", ...)`
- 不实现 sparse checkout / partial clone 优化，大型 mono-repo 优化推到后续
- 不实现 `--worktree` CLI 启动快速路径（涉及终端子系统，留给 ch15）
- 不实现 PR fetch 或 pull request 头引用解析（远端协作场景）
- 不实现 prepare-commit-msg hook 注入 commit attribution（商业 feature 场景）
- 不实现 ReadFile / Memory / SystemPrompt 缓存清理 hook（MewCode 当前没有这几类缓存）
- 不引入第三方 gitignore 库（`PostCreationSetup.matchesAnyPattern` 简化匹配够用）
- 团队成员（teammate）路径的 worktree 自动清理推到 ch15 收尾，本章 teammate 路径只创建并隔离、不负责清理

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch14: Worktree Tasks（Java 版）

> 任务粒度：每个任务可在一次会话内完成，可独立交付。

## T1: 实现 Slug 校验 + 命名映射
- 影响文件: `src/main/java/com/mewcode/worktree/SlugValidator.java`（`MAX_LENGTH` @ 11；`VALID_SEGMENT` @ 12；`validate` @ 16-37；`flatten` @ 39-41；`branchName` @ 43-45）
- 依赖任务: 无
- 完成标准: `validate(String slug)` 校验长度 ≤ 64、按 `/` 切段、每段匹配 `^[a-zA-Z0-9._-]+$`、显式拒绝 `.` / `..` 段，错误分类（cannot be empty / 长度 / `.` `..` 段 / 非法段）通过 `IllegalArgumentException` 抛出；`flatten(s) = s.replace('/', '+')`；`branchName(s) = "worktree-" + flatten(s)`；类声明为 `final`，构造私有，只暴露静态方法。
- [ ] 完成

## T2: 实现 git 进程执行壳
- 影响文件: `src/main/java/com/mewcode/worktree/WorktreeManager.java`（`runGit` @ 180-200）、`src/main/java/com/mewcode/worktree/WorktreeChanges.java`（`runGit` @ 64-87）、`src/main/java/com/mewcode/worktree/StaleCleanup.java`（`runGitQuiet` @ 113-134）、`src/main/java/com/mewcode/worktree/AgentWorktree.java`（`readHead` @ 106-118）
- 依赖任务: 无
- 完成标准: 所有 `ProcessBuilder` 调用前在 `environment()` put `GIT_TERMINAL_PROMPT=0` 和 `GIT_ASKPASS=""`（`WorktreeChanges.runGit` @ 72-73、`StaleCleanup.runGitQuiet` @ 120-121、`AgentWorktree.create` @ 45-46）；用 `waitFor(N, TimeUnit.SECONDS)` 超时保护（30 或 60 秒），未完成时 `destroyForcibly()`；进程退出非 0 时按调用约定要么抛 `IOException`（`WorktreeManager.runGit` @ 196-198）要么返 `null`（`WorktreeChanges.runGit` @ 83）。
- [ ] 完成

## T3: 实现 WorktreeManager 主入口
- 影响文件: `src/main/java/com/mewcode/worktree/WorktreeManager.java`（`WorktreeInfo` record @ 25；构造 @ 32-36；`create` @ 51-65；`remove` @ 70-78；`list` @ 86-97；`cleanupStale` @ 112-132；`detectChanges` @ 156-176；`parsePorcelain` @ 211-240）
- 依赖任务: T2
- 完成标准: `WorktreeInfo(path, branch, createdAt)` record；构造接收 `projectRoot` + `symlinkDirs`（null 容忍为 `List.of()`）+ `staleCutoffHours`（<=0 时默认 24）；`create(branch, targetDir)` 在 `targetDir==null` 时默认 `<projectRoot>/.mewcode/worktrees/<branch>`，调 `git worktree add -B <branch> <wtDir>` 大写 `-B` 容忍孤儿分支，成功后调 `PostCreationSetup.perform` 跑四项设置，最后把 `WorktreeInfo` 放进 `LinkedHashMap`；`remove(branch)` 拿出 map 项跑 `git worktree remove <path> --force` 然后 `worktrees.remove(branch)`；`list()` 优先解析 `git worktree list --porcelain` 输出（`parsePorcelain` 按 blank line 分块），失败回退内存 map；所有公开方法 `synchronized`。
- [ ] 完成

## T4: 实现 PostCreationSetup 四项
- 影响文件: `src/main/java/com/mewcode/worktree/PostCreationSetup.java`（`perform` @ 19-24；`copySettingsLocal` @ 26-36；`configureHooksPath` @ 38-58；`symlinkDirectories` @ 60-73；`copyWorktreeIncludeFiles` @ 75-106；`matchesAnyPattern` @ 108-116）
- 依赖任务: 无
- 完成标准: `perform(repoRoot, worktreePath, symlinkDirs)` 依次跑四项；`copySettingsLocal` 复制 `<repo>/.mewcode/settings.local.json`（不存在静默 return），失败 `log.fine`；`configureHooksPath` 优先 `.husky` 回退 `.git/hooks`，找到第一个存在目录后在 worktree 目录里跑 `git config core.hooksPath <hooksPath>`；`symlinkDirectories` 跳过含 `..` 项 + 跳过 src 不存在或 dst 已存在的 + `Files.createSymbolicLink(dst, src)` 错误 `log.fine`；`copyWorktreeIncludeFiles` 读 `.worktreeinclude` 按行收集（跳空行和 `#`）→ 在 repoRoot 跑 `git ls-files --others --ignored --exclude-standard --directory` → 对每行（跳目录和空）`matchesAnyPattern` 判定后 `Files.createDirectories(dst.getParent()) + Files.copy(src, dst)`；`matchesAnyPattern` 支持去前导 `/` 后 exact / basename / dir prefix 三种匹配。
- [ ] 完成

## T5: 实现变更检测 fail-closed
- 影响文件: `src/main/java/com/mewcode/worktree/WorktreeChanges.java`（`ChangeSummary` record @ 12；`hasChanges` @ 20-31；`countChanges` @ 38-62；`runGit` @ 64-87）
- 依赖任务: T2
- 完成标准: `ChangeSummary(changedFiles, commits)` record；`hasChanges(wtPath, headCommit)` — `git status --porcelain` 非 null 非空 → true；`git rev-list --count <headCommit>..HEAD` 为 null 或解析后 > 0 → true；任何异常 catch 后返 `true`（**fail-closed**）。`countChanges(wtPath, originalHeadCommit)` — `originalHeadCommit==null||isBlank` 返 null；`status --porcelain` 返 null 时返 null，否则按 `\n` 切并数非空行；`rev-list --count` 返 null 或 `NumberFormatException` 时返 null；否则返 `new ChangeSummary(changedFiles, commits)`。
- [ ] 完成

## T6: 实现 AgentWorktree 静态 API
- 影响文件: `src/main/java/com/mewcode/worktree/AgentWorktree.java`（`Result` record @ 20；`create` @ 27-59；`remove` @ 64-89；`buildNotice` @ 95-104；`readHead` @ 106-118）
- 依赖任务: T1, T2, T4
- 完成标准: `Result(worktreePath, worktreeBranch, headCommit, gitRoot)` record；`create(slug, repoRoot, symlinkDirs)` — `SlugValidator.validate` → `wtPath = <repoRoot>/.mewcode/worktrees/<flatten(slug)>` + `branch = "worktree-" + flatten(slug)` → `Files.isDirectory(wtPath)` 时快速恢复（`Files.setLastModifiedTime(wtPath, FileTime.from(Instant.now()))` bump mtime + `readHead`）→ 否则 `Files.createDirectories(wtPath.getParent())` + `ProcessBuilder("git","worktree","add","-B",branch,wtPath,"HEAD")` + `PostCreationSetup.perform` → 返 `Result`；**不动 `WorktreeSessionStore`、不切 JVM cwd、不写持久化**。`remove(wtPath, wtBranch, gitRoot)` — gitRoot 空返 false → `ProcessBuilder` 从 `gitRoot.toFile()` 跑 `git worktree remove --force <wtPath>`（**不**从 wtPath 否则把自己删掉）→ 成功后 `Thread.sleep(100)` 等 lockfile → 分支非空跑 `git branch -D <branch>` → 返 true；异常时 `log.fine` 后返 false。`buildNotice(parentCwd, worktreeCwd)` 返固定模板字符串含 `parentCwd` / `worktreeCwd` 占位 + "isolated git worktree" / "translate them" / "Re-read files before editing" / "will not affect the parent's files" 关键句。
- [ ] 完成

## T7: 实现 WorktreeSession + Store
- 影响文件: `src/main/java/com/mewcode/worktree/WorktreeSession.java`（record @ 11-20）、`src/main/java/com/mewcode/worktree/WorktreeSessionStore.java`（`MAPPER` @ 15；`currentSession` @ 16；`getCurrentSession` @ 20；`restoreSession` @ 24；`save` @ 28-36；`load` @ 38-48；`sessionPath` @ 54-56）
- 依赖任务: 无
- 完成标准: `WorktreeSession` Java record，8 字段 + Jackson `@JsonProperty` snake_case：`original_cwd` / `worktree_path` / `worktree_name` / `worktree_branch` / `original_branch` / `original_head_commit` / `session_id` / `creation_duration_ms`；类标注 `@JsonIgnoreProperties(ignoreUnknown = true)` 兼容字段增减。`WorktreeSessionStore` 用 `private static volatile WorktreeSession currentSession` 保证并发可见；`getCurrentSession` 直接返字段；`restoreSession(WorktreeSession)` 直接写字段（也接受 null 清除）；`save(repoRoot, session)` — session=null 时 `Files.deleteIfExists(sessionPath)`，否则 `Files.createDirectories(parent) + MAPPER.writerWithDefaultPrettyPrinter().writeValue(file, session)`；`load(repoRoot)` 读 `.mewcode/worktree_session.json`，不存在返 null，反序列化 `IOException` 返 null；`sessionPath = <repo>/.mewcode/worktree_session.json`。
- [ ] 完成

## T8: 实现 EnterWorktreeTool
- 影响文件: `src/main/java/com/mewcode/tool/impl/EnterWorktreeTool.java`（`worktreeManager / sessionId / RANDOM` @ 19-21；构造 @ 23-26；`name / category / shouldDefer / description` @ 28-35；`schema` @ 37-52；`execute` @ 54-91）
- 依赖任务: T1, T3, T7
- 完成标准: 实现 `Tool` 接口；`name()="EnterWorktree"`、`category()=ToolCategory.COMMAND`、`shouldDefer()=true`；input schema 仅 `name: string`（可选，max 64 chars 提示）；`execute` guard `WorktreeSessionStore.getCurrentSession() != null` → `ToolResult.error("Already in a worktree session")`；`name` 缺省时用 `RANDOM.nextInt()` 生成 `"wt-" + Integer.toHexString(...)`；`SlugValidator.validate` 失败时返 error；调 `worktreeManager.create(slug, null)` → 组装 `WorktreeSession(System.getProperty("user.dir"), info.path(), slug, info.branch(), "", "", sessionId, 0)` → `restoreSession + save` → 返 `ToolResult.success("Created worktree at <path> on branch <branch>. The session is now working in the worktree. Use ExitWorktree to leave mid-session.")`。
- [ ] 完成

## T9: 实现 ExitWorktreeTool
- 影响文件: `src/main/java/com/mewcode/tool/impl/ExitWorktreeTool.java`（`worktreeManager` @ 19；构造 @ 21-23；`name / category / shouldDefer / description` @ 25-32；`schema` @ 34-55；`execute` @ 57-121）
- 依赖任务: T3, T5, T7
- 完成标准: 实现 `Tool` 接口；`name()="ExitWorktree"`、`shouldDefer()=true`；input schema `action: enum["keep","remove"]`（required）+ `discard_changes?: bool`；`execute` scope guard：`getCurrentSession()==null` → `ToolResult.error("No-op: there is no active EnterWorktree session to exit. This tool only operates on worktrees created by EnterWorktree in the current session.")`；变更保护：`action="remove" && !discard_changes` 时 `WorktreeChanges.countChanges`：null 报 `"Could not verify worktree state. Refusing to remove without explicit confirmation. Re-invoke with discard_changes: true, or use action: \"keep\"."`；`changedFiles>0 || commits>0` 时按部分拼接 — `changedFiles==1 ? "file" : "files"` + `commits==1 ? "commit" : "commits"` 单复数正确，用 `String.join(" and ", parts)`；`restoreSession(null) + save(repoRoot, null)`（save 失败 swallow）；`action="remove"` 调 `worktreeManager.remove(session.worktreeName())` 失败返 error，成功返 `"Exited and removed worktree at <path>. Session is now back in <originalCwd>."`；`action="keep"` 返 `"Exited worktree. Your work is preserved at <path>. Session is now back in <originalCwd>."`。
- [ ] 完成

## T10: 接入 SubAgent isolation（AgentTool.runSync）
- 影响文件: `src/main/java/com/mewcode/subagent/AgentTool.java`（`worktreeManager` 字段 @ 51；`setWorktreeManager` @ 98-100；`isolation` schema @ 176-180；`execute` 解析 `isolation` @ 228；`runSync` worktree 分支 @ 310-335 和 388-399；`runAsTeammate` worktree 分支 @ 456-472）
- 依赖任务: T5, T6, T3
- 完成标准: `AgentTool.schema()` 中 `properties.put("isolation", Map.of("type","string","enum", List.of("worktree"), ...))`；`execute` 调 `getStringArg(args, "isolation")` 解析；`runSync(spec, description, prompt, modelOverride, isolation)` 在 `"worktree".equals(isolation) && worktreeManager != null` 时：
  1. 用 `SecureRandom` 生成 4 字节 → `HexFormat.of().formatHex(rndBytes).substring(0,7)` → `slug = "agent-a" + 7hex`（匹配 cleanup 正则 `^agent-a[0-9a-f]{7}$`）；
  2. `wtResult = AgentWorktree.create(slug, worktreeManager.getProjectRoot(), worktreeManager.getSymlinkDirs())`；
  3. `subAgent.setWorkDir(wtResult.worktreePath())`；
  4. `notice = AgentWorktree.buildNotice(System.getProperty("user.dir"), wtResult.worktreePath())`；
  5. `prompt = notice + "\n\n" + prompt`；
  6. 创建失败 → `return ToolResult.error("Error creating agent worktree: " + e.getMessage())`；
  `LoopComplete` 事件处理时（`wtResult != null` 分支）调 `WorktreeChanges.hasChanges(wtResult.worktreePath(), wtResult.headCommit())`：true → `wtInfo = "\n\nWorktree kept at <path> (branch <branch>) — has uncommitted changes or new commits."`；false → `AgentWorktree.remove(wtResult.worktreePath(), wtResult.worktreeBranch(), wtResult.gitRoot())`；最后 `result + wtInfo` 拼回。`runAsTeammate` 在 `"worktree".equals(isolation)` 时执行同样三步（创建 + workdir + notice 注入），但**不**做完成后自动清理（teammate 长生命周期，留给 ch15 收尾）。
- [ ] 完成

## T11: 实现后台过期清理
- 影响文件: `src/main/java/com/mewcode/worktree/StaleCleanup.java`（`EPHEMERAL_PATTERNS` @ 23-29；`isEphemeral` @ 33-35；`cleanup` @ 41-88；`startCleanupLoop` @ 93-111；`runGitQuiet` @ 113-134）
- 依赖任务: T6
- 完成标准: 五个临时命名正则常量列表：`^agent-a[0-9a-f]{7}$` / `^wf_[0-9a-f]{8}-[0-9a-f]{3}-\d+$` / `^wf-\d+$` / `^bridge-[A-Za-z0-9_]+(-[A-Za-z0-9_]+)*$` / `^job-[a-zA-Z0-9._-]{1,55}-[0-9a-f]{8}$`；`isEphemeral(slug)` 任一匹配返 true。`cleanup(repoRoot, cutoff)` — `dir = <repoRoot>/.mewcode/worktrees`，不存在返 0 → 取 `WorktreeSessionStore.getCurrentSession()?.worktreePath()` 作为白名单 → `Files.list(dir)` 遍历每项 `slug = entry.getFileName()`：
  - **L1 命名**：`!isEphemeral(slug)` → continue（用户命名永不删）
  - **L2 时态**：`wtPath.equals(currentPath)` → continue；`Files.readAttributes(entry, BasicFileAttributes.class).lastModifiedTime().toInstant().isAfter(cutoff)` → continue；读 attrs 异常也 continue
  - **L3 git 状态 fail-closed**：`runGitQuiet(wtPath, "--no-optional-locks", "status", "--porcelain", "-uno")` 返 null 或 非空 → continue；`runGitQuiet(wtPath, "rev-list", "--max-count=1", "HEAD", "--not", "--remotes")` 返 null 或非空 → continue
  - 三层通过 → `AgentWorktree.remove(wtPath, SlugValidator.branchName(slug), repoRoot)` 成功 `removed++`；
  末尾 `removed > 0` 时跑 `runGitQuiet(repoRoot, "worktree", "prune")`；返 `removed`。`startCleanupLoop(executor, repoRoot, intervalSeconds, cutoffHours)`：`intervalSeconds <= 0` 直接 return；否则 `executor.scheduleAtFixedRate(task, interval, interval, TimeUnit.SECONDS)`，task 算 `cutoff = Instant.now().minusSeconds(cutoffHours*3600L)` 后调 `cleanup`。
- [ ] 完成

## T12: 接入应用启动装配
- 影响文件: 应用入口（如 `src/main/java/com/mewcode/Main.java` 或 TUI 启动器，按项目实际路径）
- 依赖任务: T7, T8, T9, T10, T11
- 完成标准:
  1. 构造 `WorktreeManager(projectRoot, symlinkDirs, staleCutoffHours)`，`projectRoot` 由 `System.getProperty("user.dir")` 或仓库根解析得到；
  2. 注册 `new EnterWorktreeTool(worktreeManager, sessionId)` 和 `new ExitWorktreeTool(worktreeManager)` 到 `ToolRegistry`；
  3. `AgentTool.setWorktreeManager(worktreeManager)` 把 `worktreeManager` 注入到 `AgentTool` 实例；
  4. `WorktreeSession saved = WorktreeSessionStore.load(projectRoot)` → 非 null 且 `Files.exists(Path.of(saved.worktreePath()))` 时 `WorktreeSessionStore.restoreSession(saved)`；
  5. `ScheduledExecutorService cleanupExec = Executors.newSingleThreadScheduledExecutor()` → `StaleCleanup.startCleanupLoop(cleanupExec, projectRoot, intervalSeconds, cutoffHours)`，间隔由配置控制（默认 0 = 不启动）；
  6. 应用退出时 `cleanupExec.shutdown()`。
- [ ] 完成

## T13: 端到端验证
- 影响文件: 无（仅运行）
- 依赖任务: T1-T12
- 完成标准:
  - `./gradlew build` 通过（无编译错误，所有单元测试 PASS）；
  - **路径 A — 工具直接驱动**：主 Agent 调 `EnterWorktree({name:"demo"})` 创建 worktree → 在 worktree 里 `WriteFile + Bash("git commit ...")` → `ExitWorktree({action:"remove"})` 被变更保护拒绝并列出具体 file/commit 数（带正确单复数）→ `ExitWorktree({action:"remove", discard_changes:true})` 强删成功，`.mewcode/worktrees/demo` 消失；
  - **路径 B — 子 Agent 自动隔离**：主 Agent 在主目录 `WriteFile witness.txt = "original content from main agent"` → 调 `Agent({subagent_type:"general-purpose", isolation:"worktree", description:"...", prompt:"把 witness.txt 改成 ..."})` → 验证主目录 `witness.txt` 内容不变；`.mewcode/worktrees/agent-a*/witness.txt` 是修改后版本；若有 commit → 结果末尾出现 `"Worktree kept at ... (branch worktree-agent-a...) — has uncommitted changes or new commits."`；若无修改 → worktree 自动被 `AgentWorktree.remove` 清理；
  - **持久化与重启**：`EnterWorktree({name:"crashtest"})` 后强杀进程 → `.mewcode/worktree_session.json` 仍存在 → 重启后 `WorktreeSessionStore.load + restoreSession` 把 session 写回全局 `volatile` 字段。
- [ ] 完成

## 进度
- [ ] T1 / [ ] T2 / [ ] T3 / [ ] T4 / [ ] T5 / [ ] T6 / [ ] T7 / [ ] T8 / [ ] T9 / [ ] T10 / [ ] T11 / [ ] T12 / [ ] T13
```
```plain
# ch14: Worktree Checklist（Java 版）

> 所有条目可勾选、可观测。验收方式写在条目后面括号中。验收：已通过验证的项均勾选。

## 1. 实现完整性

- [ ] 常量 `MAX_LENGTH = 64` 在 `src/main/java/com/mewcode/worktree/SlugValidator.java:11` 定义
- [ ] 正则 `VALID_SEGMENT = ^[a-zA-Z0-9._-]+$` 在 `src/main/java/com/mewcode/worktree/SlugValidator.java:12` 定义
- [ ] 函数 `SlugValidator.validate` 在 `src/main/java/com/mewcode/worktree/SlugValidator.java:16-37` 含空 / 长度 / `.`-`..` / 非法段四类 `IllegalArgumentException`
- [ ] 函数 `SlugValidator.flatten` 在 `src/main/java/com/mewcode/worktree/SlugValidator.java:39` 把 `/` 替换成 `+`；`branchName` 在 `:43` 加 `worktree-` 前缀
- [ ] record `WorktreeManager.WorktreeInfo(path, branch, createdAt)` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:25` 定义
- [ ] 函数 `WorktreeManager.create` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:51-65` 用大写 `-B` 创建 + 调 `PostCreationSetup.perform` + 写内存 map
- [ ] 函数 `WorktreeManager.remove` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:70-78` 跑 `git worktree remove ... --force`
- [ ] 函数 `WorktreeManager.list` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:86-97` 先解析 porcelain 输出，失败回退内存 map
- [ ] 函数 `WorktreeManager.parsePorcelain` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:211-240` 按 blank line 分块，正确处理 `refs/heads/<branch>` 前缀剥离 + 最后一个块无尾随空行
- [ ] 函数 `WorktreeManager.runGit` 在 `src/main/java/com/mewcode/worktree/WorktreeManager.java:180-200` 用 `waitFor(60, TimeUnit.SECONDS)` 超时 + 退出非 0 抛 `IOException`
- [ ] 函数 `PostCreationSetup.perform` 在 `src/main/java/com/mewcode/worktree/PostCreationSetup.java:19-24` 依序调四项 A/B/C/D
- [ ] 函数 `PostCreationSetup.symlinkDirectories` 在 `src/main/java/com/mewcode/worktree/PostCreationSetup.java:60-73` 跳过含 `..` 项 + `Files.createSymbolicLink` 错误 `log.fine`
- [ ] 函数 `PostCreationSetup.copyWorktreeIncludeFiles` 在 `src/main/java/com/mewcode/worktree/PostCreationSetup.java:75-106` 单文件失败 catch 不中断（异常被外层 try 包裹）
- [ ] 函数 `PostCreationSetup.matchesAnyPattern` 在 `src/main/java/com/mewcode/worktree/PostCreationSetup.java:108-116` 含 exact / basename / dir prefix 三种匹配
- [ ] record `AgentWorktree.Result(worktreePath, worktreeBranch, headCommit, gitRoot)` 在 `src/main/java/com/mewcode/worktree/AgentWorktree.java:20` 定义，不含 sessionId
- [ ] 函数 `AgentWorktree.create` 在 `src/main/java/com/mewcode/worktree/AgentWorktree.java:27-59` 在已存在时 `Files.setLastModifiedTime(wtPath, FileTime.from(Instant.now()))` bump mtime
- [ ] 函数 `AgentWorktree.create` 中 `ProcessBuilder.environment().put("GIT_TERMINAL_PROMPT","0")` 和 `put("GIT_ASKPASS","")` 在 `:45-46`
- [ ] 函数 `AgentWorktree.remove` 在 `src/main/java/com/mewcode/worktree/AgentWorktree.java:64-89` 从 `gitRoot` 跑 `ProcessBuilder.directory()`（不是 wtPath，否则把自己删掉）
- [ ] 函数 `AgentWorktree.remove` 在 `:76` 含 `Thread.sleep(100)` 等 git lockfile 释放
- [ ] 函数 `AgentWorktree.buildNotice` 在 `src/main/java/com/mewcode/worktree/AgentWorktree.java:95-104` 含 `parentCwd` / `worktreeCwd` 占位 + "isolated git worktree" / "translate them" / "Re-read files before editing" / "will not affect the parent's files" 关键句
- [ ] record `WorktreeChanges.ChangeSummary(changedFiles, commits)` 在 `src/main/java/com/mewcode/worktree/WorktreeChanges.java:12` 定义
- [ ] 函数 `WorktreeChanges.hasChanges` 在 `src/main/java/com/mewcode/worktree/WorktreeChanges.java:20-31` 任何异常 catch 后返 true（fail-closed）
- [ ] 函数 `WorktreeChanges.countChanges` 在 `src/main/java/com/mewcode/worktree/WorktreeChanges.java:38-62` `originalHeadCommit` null / blank 时返 null，`NumberFormatException` 时返 null
- [ ] record `WorktreeSession` 在 `src/main/java/com/mewcode/worktree/WorktreeSession.java:11-20` 含 8 字段且 `@JsonProperty` snake_case 标注
- [ ] 类 `WorktreeSession` 标 `@JsonIgnoreProperties(ignoreUnknown = true)` 兼容字段增减
- [ ] 字段 `WorktreeSessionStore.currentSession` 在 `src/main/java/com/mewcode/worktree/WorktreeSessionStore.java:16` 标 `private static volatile`
- [ ] 函数 `WorktreeSessionStore.save` 在 `src/main/java/com/mewcode/worktree/WorktreeSessionStore.java:28-36` session=null 时 `Files.deleteIfExists`
- [ ] 函数 `WorktreeSessionStore.load` 在 `src/main/java/com/mewcode/worktree/WorktreeSessionStore.java:38-48` `IOException` 时返 null
- [ ] 函数 `WorktreeSessionStore.sessionPath` 在 `src/main/java/com/mewcode/worktree/WorktreeSessionStore.java:54-56` 返 `<repo>/.mewcode/worktree_session.json`
- [ ] 变量 `StaleCleanup.EPHEMERAL_PATTERNS` 在 `src/main/java/com/mewcode/worktree/StaleCleanup.java:23-29` 含五个正则
- [ ] 函数 `StaleCleanup.cleanup` 在 `src/main/java/com/mewcode/worktree/StaleCleanup.java:41-88` 三层过滤顺序固定（L1 命名 → L2 时态 → L3 git 状态 fail-closed）
- [ ] 函数 `StaleCleanup.cleanup` 末尾在 `removed > 0` 时跑 `git worktree prune`（`:84-86`）
- [ ] 函数 `StaleCleanup.startCleanupLoop` 在 `src/main/java/com/mewcode/worktree/StaleCleanup.java:93-111` `intervalSeconds <= 0` 直接 return
- [ ] 函数 `StaleCleanup.runGitQuiet` 在 `:113-134` 含 `GIT_TERMINAL_PROMPT=0` + `GIT_ASKPASS` 安全壳
- [ ] 类 `EnterWorktreeTool` 在 `src/main/java/com/mewcode/tool/impl/EnterWorktreeTool.java:17` 实现 `Tool` 接口，含 `worktreeManager` + `sessionId` 字段，`shouldDefer()` 返 true
- [ ] 类 `ExitWorktreeTool` 在 `src/main/java/com/mewcode/tool/impl/ExitWorktreeTool.java:17` 实现 `Tool` 接口，含 `worktreeManager` 字段，`shouldDefer()` 返 true
- [ ] `ExitWorktreeTool.schema` 在 `src/main/java/com/mewcode/tool/impl/ExitWorktreeTool.java:34-55` 含 `action: enum["keep","remove"]`（required）+ `discard_changes?: bool`
- [ ] `ExitWorktreeTool.execute` 在 `:81-95` 实现 file/files 和 commit/commits 单复数正确处理
- [ ] `AgentTool` 字段 `worktreeManager` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:51` 定义，setter `setWorktreeManager` 在 `:98-100`
- [ ] `AgentTool.runSync` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:319-335` 用 `SecureRandom` + `HexFormat.formatHex(...).substring(0,7)` 生成 `agent-a<7hex>` slug
- [ ] `AgentTool.runSync` 在 `:388-399` 完成时按 `WorktreeChanges.hasChanges` 决定保留还是 `AgentWorktree.remove`
- [ ] `AgentTool.runAsTeammate` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:456-472` 创建 worktree + workdir + notice 注入，但**不**自动清理

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -rn "EnterWorktreeTool" --include="*.java" src/` 在应用启动入口（`Main.java` 或 TUI 启动器）找到 `new EnterWorktreeTool(...)` 注册调用
- [ ] `grep -rn "ExitWorktreeTool" --include="*.java" src/` 在应用启动入口找到 `new ExitWorktreeTool(...)` 注册调用
- [ ] `grep -rn "WorktreeSessionStore.load" --include="*.java" src/` 在应用启动入口找到调用方
- [ ] `grep -rn "WorktreeSessionStore.restoreSession" --include="*.java" src/` 同时在 `EnterWorktreeTool` / `ExitWorktreeTool` / 启动恢复处找到调用
- [ ] `grep -rn "StaleCleanup.startCleanupLoop" --include="*.java" src/` 在应用启动入口找到调用方
- [ ] `grep -rn "AgentWorktree.create" --include="*.java" src/` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:325` 和 `:463` 找到两处调用（runSync + runAsTeammate）
- [ ] `grep -rn "AgentWorktree.buildNotice" --include="*.java" src/` 同上两处调用（runSync 在 `:329`，runAsTeammate 在 `:466`）
- [ ] `grep -rn "WorktreeChanges.hasChanges" --include="*.java" src/` 在 `src/main/java/com/mewcode/subagent/AgentTool.java:391` 找到主流程调用方（决定 remove 还是保留）
- [ ] `grep -rn "AgentWorktree.remove" --include="*.java" src/` 在 `AgentTool.java:396` 和 `StaleCleanup.java:76` 找到调用方
- [ ] `grep -rn "WorktreeChanges.countChanges" --include="*.java" src/` 在 `src/main/java/com/mewcode/tool/impl/ExitWorktreeTool.java:74` 找到唯一调用方（变更保护错误信息）
- [ ] `grep -rn "setWorktreeManager" --include="*.java" src/` 在应用启动入口找到注入调用（把 WorktreeManager 注入 AgentTool）

## 3. 编译与测试

- [ ] `./gradlew build` 通过
- [ ] `./gradlew test --tests "com.mewcode.worktree.*"` 通过（SlugValidator / WorktreeManager / PostCreationSetup / AgentWorktree / WorktreeChanges / StaleCleanup / WorktreeSessionStore 各对应测试 PASS）
- [ ] `./gradlew test --tests "com.mewcode.subagent.*"` 通过（含 isolation 集成测试）
- [ ] `./gradlew test --tests "com.mewcode.tool.impl.EnterWorktreeToolTest"` 和 `ExitWorktreeToolTest` 通过

## 4. 端到端验证

- [ ] **路径 A — 工具直接驱动**：用户对主 Agent 说"用 EnterWorktree 工具创建一个名叫 demo 的工作树" → LLM 调 `EnterWorktree({name:"demo"})` → 返回 `Created worktree at .../.mewcode/worktrees/demo on branch worktree-demo. The session is now working in the worktree. Use ExitWorktree to leave mid-session.`；让 Agent 在 worktree 里创建 `hello.txt` 并 `git commit`；让 Agent 调 `ExitWorktree({action:"remove"})` → 因有未推送 commit 被变更保护拒绝，错误文本包含具体 file/commit 数和单复数；`ExitWorktree({action:"remove", discard_changes:true})` 强删成功；`ls .mewcode/worktrees/` 看到 `demo/` 已消失。
- [ ] **路径 B — 子 Agent 自动隔离**：用户让主 Agent 在主目录建 `witness.txt`（内容 "original content from main agent"）→ 调 `Agent({subagent_type:"general-purpose", isolation:"worktree", description:"...", prompt:"把 witness.txt 改成 \"modified by isolated worker\"，然后 git 提交"})`；验证 `cat witness.txt` 主目录内容仍是 "original ..."；`cat .mewcode/worktrees/agent-a*/witness.txt` 是修改后版本；若子 Agent 有 commit → 结果末尾出现 `"Worktree kept at ... (branch worktree-agent-a...) — has uncommitted changes or new commits."`；若无修改 → worktree 自动清理（`.mewcode/worktrees/` 下 `agent-a*` 目录消失）。
- [ ] **持久化与 crash 恢复**：`EnterWorktree({name:"crashtest"})` 创建 worktree → `kill -9` 杀 JVM 进程 → `cat .mewcode/worktree_session.json` 文件仍在并含 crashtest 会话；重启应用 → 启动期间 `WorktreeSessionStore.load + restoreSession` 将 session 写回全局 `volatile` 字段；下一次工具调用时 `WorktreeSessionStore.getCurrentSession()` 非 null。
- [ ] **变更保护单复数**：在 worktree 里建 1 个未提交修改 → `ExitWorktree({action:"remove"})` 返回 `"1 uncommitted file"`；建 2+ 个修改 → 返回 `"N uncommitted files"`；同样验证 commit 数的单复数（`"1 commit"` / `"N commits"`）。
- [ ] **后台清理保守不删**：手动在 `.mewcode/worktrees/agent-aabcdef1/` 下建一个有未推送 commit 的目录（mtime 设为过期前）→ 等 cleanup loop 跑一轮（或手动调 `StaleCleanup.cleanup(repoRoot, Instant.now())` 测试）→ 该目录仍保留（L3 fail-closed 拦住）。
- [ ] **用户命名永不删**：在 `.mewcode/worktrees/my-feature/` 下建一个目录（mtime 设为非常老）→ 跑 cleanup → 目录仍保留（L1 命名过滤拦住）。

## 5. 文档

- [ ] `docs/java/ch14/spec.md` 已按 ch13 风格写完（F1-F17 + N1-N8，无 file:line 代码标注）
- [ ] `docs/java/ch14/tasks.md` 已写，13 个 T 全部勾完（T1-T13）
- [ ] `docs/java/ch14/checklist.md` 已写并逐项验收
- [ ] commit 信息标注 `ch14`，新增代码的调用链已在 PR 描述或 commit message 里说明
```