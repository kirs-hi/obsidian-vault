# TypeScript源码解析：Git 工作树隔离

理论篇讲了并行 [[07-Agent|Agent]] 为什么需要文件系统隔离，以及 Git Worktree 如何提供独立的工作区。这篇带你走读 MewCode 的 Worktree 模块代码，看「给每个子 Agent 一份独立文件空间」是怎么落地的。

## 模块概览

整个 Worktree 系统涉及的文件不多，核心逻辑集中在一个文件里，工具层提供进入和退出两个操作入口：

| 文件 | 职责 |
| --- | --- |
| `worktree/worktree.ts` | 核心模块：创建/删除 Worktree、纯文件系统读取 HEAD、变更检测、创建后初始化、上下文通知 |
| `tools/enter-worktree.ts` | EnterWorktree 工具：校验 slug 后调用 `createAgentWorktree` |
| `tools/exit-worktree.ts` | ExitWorktree 工具：检测变更，无变更则清理 Worktree |
| `agents/definition.ts` | Agent 定义接口，包含 `isolation: "worktree"` 字段 |

## 核心类型

### WorktreeResult

`WorktreeResult` 是创建 Worktree 后返回的结果结构：

```plain
export interface WorktreeResult {
  path: string;       // worktree 工作目录的绝对路径
  branch: string;     // 对应的 git 分支名
  headCommit: string; // 创建时的 HEAD SHA
  gitRoot: string;    // 主仓库的根目录
}
```

四个字段各有用途。 `path` 是后续[[08-文件操作|文件操作]]的根目录， `branch` 格式固定为 `worktree-{slug}` 用于清理时定位分支， `headCommit` 是变更检测的基线， `gitRoot` 指向主仓库供清理操作使用。

没有独立的 `WorktreeSession` 和 `WorktreeManager` 类型。进入/退出的状态管理直接由工具层完成，创建结果通过参数在工具之间传递，不做持久化。资源和使用行为没有分离成两个概念，而是合为一体，这是最精简的方案。

## Slug 安全校验

Slug 校验在工具层的 `EnterWorktreeTool.execute` 中完成：

```plain
if (!/^[a-zA-Z0-9_-]+$/.test(slug)) {
  return {
    output: "Error: slug must contain only alphanumeric, hyphen, underscore",
    isError: true,
  };
}
```

只允许字母、数字、连字符和下划线。这条正则挡住了两类威胁：路径穿越攻击（ `../` 之类的写法直接不匹配）和 shell 注入（特殊字符全被排除）。因为不允许 `/` ，也就不存在嵌套命名的场景，分支名直接拼 `worktree-${slug}` ，不需要额外做扁平化处理。

## 主流程走读：创建 Worktree

### 快速恢复

`createAgentWorktree` 拿到 slug 后，先算出 worktree 目录路径 `.mewcode/worktrees/{slug}` 。如果目录已经存在，说明之前创建过，走快速恢复路径：

```plain
if (existsSync(wtDir)) {
  // 纯文件系统读取 HEAD，不启动 git 子进程
  const head = readWorktreeHeadSha(wtDir);
  if (head) {
    return { path: wtDir, branch, headCommit: head, gitRoot: root };
  }
  // 文件系统读取失败则回退到 git 子进程
  const headFallback = execSync("git rev-parse HEAD", {
    cwd: wtDir, encoding: "utf-8",
  }).trim();
  return { path: wtDir, branch, headCommit: headFallback, gitRoot: root };
}
```

`readWorktreeHeadSha` 是整个模块里最精细的一段代码。它的读取链路是：先读 worktree 目录下的 `.git` 文件（注意是文件不是目录，worktree 的 `.git` 是一个 `gitdir: <path>` 指针），解析出真正的 git 目录路径，再从那个目录读 `HEAD` 文件，如果 HEAD 指向分支引用就继续解析 ref 拿到 SHA。整个过程纯文件 IO，不起子进程，在大仓库里能省掉十几毫秒的进程启动开销。

ref 解析本身也值得一看。 `resolveRefInDir` 先查 loose ref 文件，找不到再去翻 `packed-refs` ：

```plain
function resolveRefInDir(dir: string, ref: string): string {
  try {
    const content = readFileSync(join(dir, ref), "utf-8").trim();
    if (content.startsWith("ref:")) {
      const target = content.slice("ref:".length).trim();
      if (!isSafeRefName(target)) return "";
      return resolveRef(dir, target);  // 递归解析 symref
    }
    if (SHA_RE.test(content)) return content;
    return "";
  } catch { /* loose 文件不存在，尝试 packed-refs */ }
  // ...逐行扫描 packed-refs 匹配 ref 名
}
```

如果 worktree 自己的 git 目录找不到 ref，还会通过 `commondir` 文件回退到主仓库的共享 git 目录去找。这个两级查找保证了 worktree 场景下 ref 解析的完整性。

安全方面，所有 ref 名在解析前都要过 `isSafeRefName` 校验：不能以 `-` 或 `/` 开头，不能包含 `..` ，每一段都要匹配安全字符集。这防止了通过构造恶意 ref 名实现路径遍历。

### 全新创建

如果 worktree 目录不存在，就走全新创建路径：

```plain
execSync(`git worktree add -B "${branch}" "${wtDir}"`, {
  cwd: root,
  encoding: "utf-8",
  stdio: ["pipe", "pipe", "pipe"],  // 抑制所有终端交互
});
performPostCreationSetup(root, wtDir);
```

用 `-B` （大写 B）而不是 `-b` ，区别在于：如果同名分支已存在（比如上次创建后 worktree 被删了但分支没清理干净）， `-B` 会直接复用， `-b` 会报错。省掉了先 `git branch -D` 再创建的两步操作。 `stdio` 全部设为 `pipe` ，确保 git 不会弹出任何交互式提示。

## 创建后初始化

`performPostCreationSetup` 串联四步初始化，每步都用 try/catch 包裹，失败打 warning 不抛异常，保证 worktree 创建本身不会因为辅助设置出错而中断。

### A. 复制本地配置

```plain
function copyMewcodeSettings(repoRoot: string, wtPath: string): void {
  const src = join(repoRoot, ".mewcode");
  if (!existsSync(src)) return;
  const dst = join(wtPath, ".mewcode");
  cpSync(src, dst, { recursive: true });
}
```

`.mewcode/` 目录包含配置文件和 [[skill]] 定义。Worktree 共享代码但不共享这些本地配置（它们通常被 gitignore），所以需要显式复制一份。

### B. 配置 Git Hooks

Worktree 不会自动继承主仓库的 hooks 目录。 `configureHooksPath` 先检查主仓库有没有 `.husky/` 目录（前端项目常用的 hook 管理工具），没有就回退看 `.git/hooks/` 。找到后通过 `git config core.hooksPath` 指向过去：

```plain
const candidates = [
  join(repoRoot, ".husky"),
  join(repoRoot, ".git", "hooks"),
];
// 找到第一个存在的目录后设置
execSync(`git config core.hooksPath "${hooksPath}"`, {
  cwd: wtPath, encoding: "utf-8",
  stdio: ["pipe", "pipe", "pipe"],
});
```

### C. 符号链接大目录

`node_modules` 可能有几百 MB，每个 worktree 复制一份太浪费。用 symlink 指向主仓库的 `node_modules` ，所有 worktree 共享同一份依赖：

```plain
function symlinkNodeModules(repoRoot: string, wtPath: string): void {
  const src = join(repoRoot, "node_modules");
  if (!existsSync(src)) return;
  const dst = join(wtPath, "node_modules");
  if (existsSync(dst)) return;  // 已存在就跳过
  symlinkSync(src, dst);
}
```

### D. 复制 .worktreeinclude 文件

`.worktreeinclude` 列出了被 gitignore 但 worktree 仍然需要的文件。逐行读取路径列表（跳过空行和 `#` 注释），每个路径先做路径穿越检查（含 `..` 的直接跳过），然后 best-effort 复制：

```plain
for (const relPath of paths) {
  if (relPath.includes("..")) continue;  // 防路径穿越
  try {
    const src = join(repoRoot, relPath);
    if (!existsSync(src)) continue;
    const dst = join(wtPath, relPath);
    mkdirSync(dirname(dst), { recursive: true });
    const info = statSync(src);
    if (info.isDirectory()) cpSync(src, dst, { recursive: true });
    else cpSync(src, dst);
  } catch { /* 单个文件失败不影响整体 */ }
}
```

## 进入和退出 Worktree

### 进入

进入操作由 `EnterWorktreeTool` 承担。它先校验 slug 合法性，然后调用 `createAgentWorktree` 创建（或快速恢复）worktree，返回路径、分支名和 HEAD SHA 给调用方。没有做 `chdir` ，也没有持久化 session，工具返回的信息由 Agent 上下文自行持有。

这个设计是显式 cwd 模式的体现：不修改全局工作目录，而是把 worktree 路径交给调用方，后续每个文件操作都显式使用这个路径。

### 退出

退出操作由 `ExitWorktreeTool` 承担，核心逻辑是「有变更就保留，没变更就清理」：

```plain
const hasChanges = headCommit
  ? hasWorktreeChanges(path, headCommit)
  : false;

if (!hasChanges) {
  removeAgentWorktree(path, branch, gitRoot);
  return { output: `Worktree cleaned up: ${path}` };
}
return { output: `Worktree has changes, kept at: ${path}` };
```

调用方需要把创建时拿到的 `headCommit` 传回来，否则变更检测无从比较，默认当作无变更直接清理。这个设计把状态管理的责任交给了调用方，模块本身保持无状态。

## 变更检测

`hasWorktreeChanges` 做两层检测：

```plain
export function hasWorktreeChanges(
  path: string, headCommit: string
): boolean {
  try {
    const status = execSync("git status --porcelain", {
      cwd: path, encoding: "utf-8",
    }).trim();
    if (status) return true;
    // 比较 HEAD SHA：优先纯文件系统读取
    const currentHead = readWorktreeHeadSha(path)
      || execSync("git rev-parse HEAD", {
           cwd: path, encoding: "utf-8",
         }).trim();
    return currentHead !== headCommit;
  } catch {
    return true;  // fail-closed：检测失败就当作有变更
  }
}
```

第一层用 `git status --porcelain` 查未提交的修改，第二层比较 HEAD SHA 查有没有新 commit。读取当前 HEAD 时优先走 `readWorktreeHeadSha` 纯文件路径，失败才回退到 `git rev-parse` 子进程，和创建时的策略一致。

`catch` 里返回 `true` 是 fail-closed 策略：检测过程出了任何异常，都当作有变更处理。宁可多保留一个 worktree 占点磁盘，也不误删有价值的工作成果。

## 自动清理

Worktree 的清理通过 `removeAgentWorktree` 完成，分两步：先用 `git worktree remove --force` 删除 worktree 目录和注册信息，再用 `git branch -D` 删除对应的分支。两步都做了异常捕获，因为 worktree 或分支可能已经被手动删除了：

```plain
export function removeAgentWorktree(
  path: string, branch: string, gitRoot: string
): void {
  try {
    execSync(`git worktree remove "${path}" --force`, {
      cwd: gitRoot, stdio: ["pipe", "pipe", "pipe"],
    });
  } catch { /* worktree 可能已被移除 */ }
  try {
    execSync(`git branch -D "${branch}"`, {
      cwd: gitRoot, stdio: ["pipe", "pipe", "pipe"],
    });
  } catch { /* 分支可能已被删除 */ }
}
```

当前实现没有独立的自动清理循环和临时 Worktree 识别机制（没有 `EPHEMERAL_PATTERNS` 正则）。清理完全由 `ExitWorktreeTool` 在退出时按需触发，依赖变更检测结果决定保留还是删除。

## 与 SubAgent 的集成

`AgentDefinition` 接口中有一个 `isolation` 字段：

```plain
export interface AgentDefinition {
  name: string;
  description: string;
  // ...其他字段
  isolation?: "worktree";  // 声明需要文件系统隔离
}
```

当 Agent 的 `.md` 定义文件中写了 `isolation: worktree` ，加载器会解析这个字段并填入定义对象。执行层拿到这个标记后，在启动子 Agent 前调用 `createAgentWorktree` 创建隔离环境。

上下文通知通过 `buildWorktreeNotice` 生成：

```plain
export function buildWorktreeNotice(
  parentCwd: string, wtPath: string
): string {
  return (
    `You are working in a git worktree at: ${wtPath}\n` +
    `The parent project is at: ${parentCwd}\n` +
    `Changes made here are isolated from the parent.`
  );
}
```

这段通知会注入到子 Agent 的系统提示中，告诉它三件事：你在隔离 worktree 里工作、父项目的路径在哪里、你的修改不会影响父项目。这很关键，否则子 Agent 可能引用父 Agent 传来的绝对路径去读写文件，结果操作的是主仓库而不是自己的 worktree 副本。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| Slug 校验 | 工具层正则 `[a-zA-Z0-9_-]+` ，不支持嵌套命名 |
| 分支创建策略 | `git worktree add -B` ，容忍残留分支 |
| 快速恢复 | `readWorktreeHeadSha` 纯文件系统读取，回退到 `git rev-parse` |
| 创建后初始化 | 四步串行：复制 `.mewcode/` 、配置 hooks、symlink `node_modules` 、复制 `.worktreeinclude` |
| 变更检测 | `git status --porcelain` + HEAD SHA 比较，fail-closed |
| 清理 | `ExitWorktreeTool` 按需触发，无自动清理循环 |
| Session 持久化 | 无独立 Session，状态由调用方通过参数传递 |
| 并发保护 | 无显式锁，依赖同步 API（ `execSync` / `readFileSync` ）的串行特性 |

> 更新: 2026-06-08 16:36:14  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/iopdpeu2ari8fl3z](https://www.yuque.com/tianming-uvfnu/gmmfad/iopdpeu2ari8fl3z)