# TypeScript源码解析：命令注册与分发

理论篇讲了 Slash Command 的设计思路和三种命令类型，这篇带你走读 MewCode 的命令系统代码。看一个 `/` 开头的输入怎么从解析到分发，绕过 LLM 直接在本地执行。在基本框架之上还多了一个使用频率追踪器，补全排序会根据你的使用习惯自动调整。

## 模块概览

Slash Command 的代码集中在 `src/commands/` 目录下，一共三个文件：

| 文件 | 职责 |
| --- | --- |
| `commands.ts` | 核心类型定义、Registry 注册中心、parse 解析函数、16 个内置命令 |
| `loader.ts` | 用户自定义命令加载：双路径扫描、Markdown 解析、frontmatter 提取、 `$ARGUMENTS` 替换 |
| `usage-tracker.ts` | 命令使用频率追踪器：半衰期衰减评分，用于补全排序 |

结构很紧凑，职责分得也很清楚。

## 核心类型

### CommandType：命令分类

```plain
export type CommandType =
  "local" | "local_ui" | "prompt" | "skill_fork";
```

用联合类型定义四种命令执行路径。 `local` 是纯本地逻辑，handler 直接返回字符串结果。 `local_ui` 需要 UI 层介入，handler 返回一个信号字符串（比如 `"clear"` 、 `"compact"` ），由 TUI 层接管处理。 `prompt` 最特殊，handler 返回的是一段提示词，会被当作用户消息发给 LLM。 `skill_fork` 用于 Skill 系统的 fork 模式，派生子 Agent 来执行。

每种类型对应不同的返回值语义： `local` 的返回值直接展示， `local_ui` 的返回值是指令而非内容， `prompt` 的返回值是发给 LLM 的输入。

### Command：命令定义

```plain
export interface Command {
  name: string;
  aliases: string[];
  type: CommandType;
  description: string;
  handler: (ctx: CommandContext) => string;
}
```

handler 直接绑定在命令定义上，注册时一步到位。签名是同步的，接收 `CommandContext` 返回字符串。所有命令共用同一个签名，不管是 `/help` 这种简单命令还是 `/review` 这种生成提示词的命令，handler 的调用方式完全一致。

### CommandContext：执行上下文

```plain
export interface CommandContext {
  workDir: string;
  args: string;
  conversation?: unknown;
  registry?: unknown;
  permissionMode?: () => string;
  tokenCount?: () => [number, number];
  toolCount?: () => number;
  memoryList?: () => string[];
  memoryClear?: () => void;
  model?: string;
}
```

Context 用函数字段实现惰性求值。 `permissionMode` 、 `tokenCount` 、 `toolCount` 、 `memoryList` 都是函数，只有命令真正调用时才计算。 `/help` 这种命令不需要 token 信息，那些函数就不会被执行，避免无谓的开销。

`conversation` 和 `registry` 类型是 `unknown` ，接口定义不依赖具体实现。命令层只关心自己需要的数据，不引用 Agent 或 UI 的实现细节。

### Registry：注册中心

```plain
export class CommandRegistry {
  private commands = new Map<string, Command>();
  private aliasMap = new Map<string, string>();
  register(cmd: Command): void {
    // 四重冲突检测：命令名 vs 已有命令名/别名，别名 vs 已有命令名/别名
    if (this.commands.has(cmd.name)) throw new Error(`...`);
    if (this.aliasMap.has(cmd.name)) throw new Error(`...`);
    for (const alias of cmd.aliases) {
      if (this.commands.has(alias)) throw new Error(`...`);
      if (this.aliasMap.has(alias)) throw new Error(`...`);
    }
    this.commands.set(cmd.name, cmd);
    for (const alias of cmd.aliases)
      this.aliasMap.set(alias, cmd.name);
  }
```

两张 Map 构成注册中心。 `commands` 按主名称索引， `aliasMap` 把别名映射到主名称。注册时做了完整的四重冲突检测：命令名不能和已有命令名冲突，命令名不能和已有别名冲突，别名不能和已有命令名冲突，别名不能和已有别名冲突。任何一项冲突直接抛异常，在启动阶段就能发现问题。

此外还提供了 `hasConflict` 方法，动态加载器在注册前先调用它过滤冲突条目，避免触发异常。

## 主流程走读

### 第一步：Parse 解析输入

```plain
export function parse(
  input: string
): { name: string; args: string } | null {
  if (!input.startsWith("/")) return null;
  const trimmed = input.slice(1).trim();
  const spaceIdx = trimmed.indexOf(" ");
  if (spaceIdx === -1)
    return { name: trimmed, args: "" };
  return {
    name: trimmed.slice(0, spaceIdx),
    args: trimmed.slice(spaceIdx + 1).trim(),
  };
}
```

不是 `/` 开头的直接返回 `null` ，告诉调用方这不是命令。是命令的话，去掉 `/` 前缀，用第一个空格切成命令名和参数两段。 `/compact 保留数据库内容` 解析出 `{ name: "compact", args: "保留数据库内容" }` 。只输入 `/help` 没有参数时， `args` 是空字符串。

返回 `null` 而不是抛异常，是一个典型的设计选择：用返回值区分「不是命令」和「是命令」，调用方用简单的 if 判断分流。

### 第二步：Find 查找命令

```plain
find(name: string): Command | undefined {
  return this.commands.get(name)
    ?? this.commands.get(
      this.aliasMap.get(name) ?? ""
    );
}
```

一行代码完成两层查找。先按主名称查，找不到就通过别名表间接查。 `??` 是空值合并运算符，如果 `aliasMap.get(name)` 返回 `undefined` ，就用空字符串去查，自然也查不到，最终返回 `undefined` 。

### 第三步：按类型分发执行

分发逻辑在 TUI 层完成，命令模块只管定义和查找。TUI 拿到 Command 后，根据 `type` 字段决定怎么处理 handler 的返回值：

-   `local` ：调 handler 拿结果，直接展示给用户。

-   `local_ui` ：handler 返回信号字符串（ `"clear"` 、 `"plan"` 、 `"compact"` 等），TUI 根据信号执行对应的 UI 操作。

-   `prompt` ：调 handler 拿提示词，当作用户消息发给 Agent Loop。

特殊情况也有处理：只输入 `/` 时列出可用命令，命令找不到时带 `/help` 引导，缺参数时显示 `argPrompt` 。

## 别名系统

别名在注册时声明，存到独立的 `aliasMap` 里。查找时先走主名称再走别名，用 `??` 运算符串联两次查找。

冲突检测在注册阶段完成，不等到运行时。注册方法会检查四种冲突场景：新命令名 vs 已有命令名、新命令名 vs 已有别名、新别名 vs 已有命令名、新别名 vs 已有别名。只要有一项冲突就抛异常，绝不让两个命令抢同一个名字。

## 自动补全

```plain
complete(prefix: string): Command[] {
  const lower = prefix.toLowerCase();
  return [...this.commands.values()].filter(
    (cmd) =>
      cmd.name.toLowerCase().startsWith(lower) ||
      cmd.aliases.some(
        (a) => a.toLowerCase().startsWith(lower)
      )
  );
}
```

遍历所有命令，名称或别名以 prefix 开头的全部返回。做了大小写统一处理， `/RE` 和 `/re` 效果一样。返回的是 `Command[]` 而不是字符串数组，调用方可以拿到完整的命令信息用于展示。

补全结果的排序可以结合 `CommandUsageTracker` 来做。基础的 `complete` 方法返回匹配列表，调用方拿到后再按使用频率分数排序，常用命令排在前面。

### 使用频率追踪

`CommandUsageTracker` 记录每条命令的使用次数和最后使用时间，然后算出一个加权分数用于补全排序。

```plain
getScore(name: string): number {
  const entry = this.usage.get(name);
  if (!entry) return 0;
  // 距离上次使用过了多少天
  const daysSince =
    (Date.now() - entry.lastUsedAt)
    / (1000 * 60 * 60 * 24);
  // 半衰期 7 天的衰减因子
  const recency = Math.pow(0.5, daysSince / 7);
  return entry.usageCount
    * Math.max(recency, 0.1);
}
```

分数 = 使用次数 x 时间衰减因子。衰减用的是半衰期模型：每过 7 天，时间因子减半。一个月前用过 100 次的命令，分数会衰减到原来的 6% 左右；昨天用过 5 次的命令，分数几乎不变。 `Math.max(recency, 0.1)` 兜底，保证再久远的记录也不会完全归零。

数据持久化到 `.mewcode/command_usage.json` ，每次 `record` 调用都会写文件，启动时自动加载，跨会话生效。 `getRecentlyUsed` 方法返回按分数排序的前 N 个命令名，补全界面直接用这个列表把常用命令排到前面。

## 内置命令速览

`createDefaultRegistry()` 注册了 16 个内置命令：

| 命令 | 别名 | 类型 | 职责 |
| --- | --- | --- | --- |
| `/help` | `/h` , `/?` | local | 列出所有命令或查看单个命令详情 |
| `/clear` |  | local_ui | 清除对话 |
| `/compact` | `/c` | local_ui | 压缩上下文 |
| `/status` | `/s` | local | 显示会话状态 |
| `/session` |  | local | 显示会话信息 |
| `/plan` | `/p` | local_ui | 切换 Plan 模式 |
| `/resume` | `/r` | local_ui | 恢复上次会话 |
| `/quit` | `/exit` , `/q` | local_ui | 退出 MewCode |
| `/memory` |  | local | 显示记忆状态 |
| `/permission` | `/perm` | local | 显示/切换权限模式 |
| `/skills` |  | local_ui | 列出可用 Skill |
| `/worktree` | `/wt` | local_ui | 管理 git worktree |
| `/code-review` | `/cr` | local | 管理 Code Review 团队 |
| `/review` |  | prompt | 审查未提交的代码变更 |
| `/rewind` |  | local_ui | 回退到之前的检查点 |
| `/mcp` |  | local | 显示 MCP 连接状态 |

## 典型命令实现走读

### /help：最基础的 LOCAL 命令

```plain
handler: (ctx) => {
  if (ctx.args) {
    const cmd = registry.find(ctx.args);
    if (!cmd) return `Unknown command: ${ctx.args}`;
    let detail = `/${cmd.name} — ${cmd.description}\n`;
    if (cmd.aliases.length > 0)
      detail += `  Aliases: ${cmd.aliases.join(", ")}`;
    return detail;
  }
  const cmds = registry.listCommands();
  // ... 拼装命令列表
}
```

不带参数列出所有可见命令，带参数显示单个命令的详情，包括描述和别名。handler 闭包引用了 `registry` 自身，不需要从 Context 里拿。

### /status：展示状态信息

```plain
handler: (ctx) => {
  const lines: string[] = [];
  lines.push("MewCode Status");
  const mode = ctx.permissionMode
    ? ctx.permissionMode() : "default";
  lines.push(`  Mode:      ${mode}`);
  if (ctx.tokenCount) {
    const [input, output] = ctx.tokenCount();
    lines.push(`  Tokens:    ${input} in / ${output} out`);
  }
  // toolCount, memoryList, model, workDir ...
}
```

惰性求值在这里体现得很明显。 `ctx.permissionMode` 是一个函数，只有 `/status` 执行时才会调用。 `ctx.tokenCount` 也一样，先判断函数是否存在再调用，每个数据源都是可选的。这种方式让 Context 可以按需提供能力，不强制所有命令都依赖完整的运行时。

### /compact：LocalUI 信号模式

```plain
registry.register({
  name: "compact", aliases: ["c"],
  type: "local_ui",
  description: "Force context compaction",
  handler: () => "compact",
});
```

handler 返回信号字符串 `"compact"` ，TUI 层拿到后执行压缩操作并展示前后 token 对比。命令层不关心压缩怎么做，只负责发信号。 `/clear` 返回 `"clear"` ， `/plan` 返回 `"plan"` ， `/quit` 返回 `"quit"` ，都是同一个模式。

### /plan 和模式切换

`/plan` 注册为 `local_ui` ，handler 返回 `"plan"` 信号。TUI 层拿到后切换 Agent 的工作模式，更新状态栏显示。如果用户在 `/plan` 后面带了参数，比如 `/plan 帮我设计数据库表结构` ，TUI 可以先切模式再把参数当作消息发出去。

### /review：PROMPT 类型命令

```plain
handler: (ctx) =>
  "Review the current uncommitted changes. " +
  "Run `git status` and `git diff` to see them, " +
  "then report concrete findings (file:line)..." +
  (ctx.args ? `\n\nFocus on: ${ctx.args}` : ""),
```

handler 返回的是提示词不是结果。这段 prompt 指导 LLM 执行 git 命令、审查差异、按 `file:line` 格式报告发现。用户参数通过条件表达式追加到末尾，比如 `/review 关注安全问题` 会在 prompt 后面加上 `Focus on: 关注安全问题` 。

调用方根据 `type === "prompt"` 判断，把返回值当作用户消息塞进对话流发给 Agent，而不是直接展示。

### /code-review：带子命令的命令

```plain
handler: (ctx) => {
  const args = ctx.args.trim();
  if (!args) {
    return "Usage: /code-review <command> [args]\n"
      + "Commands: create, add, remove, list, status";
  }
  return `code-review:${args}`;
},
```

不带参数时显示用法提示，带参数时返回 `code-review:参数` 格式的字符串。实际的团队管理操作由上层根据这个格式化字符串来分发。参数里的子命令（create、add、remove 等）在这一层不做解析，只透传。

## 文件命令加载（如果有）

### 路径扫描与合并

```plain
export function loadUserCommands(
  workDir: string
): Command[] {
  const byName = new Map<string, Command>();
  const bases = [
    join(homedir(), ".mewcode", "commands"),
    join(workDir, ".mewcode", "commands"),
  ];
  for (const base of bases) {
    if (!existsSync(base)) continue;
    for (const cmd of walkDir(base, base))
      byName.set(cmd.name, cmd);
  }
  return [...byName.values()];
}
```

两个路径按优先级排列： `~/.mewcode/commands/` （用户全局）和 `.mewcode/commands/` （项目级）。后者覆盖前者，用 Map 按名称去重实现优先级。目录不存在就跳过，不报错。

### Markdown 解析

子目录转命名空间： `daily/standup.md` 变成 `/daily:standup` ，用冒号分隔层级。

frontmatter 用 `---` 包裹，里面可以定义 `description` 、 `aliases` 、 `argument-hint` 。解析用 `js-yaml` 库，解析失败静默降级，把整个文件当正文处理，不影响其他命令的加载。

### $ARGUMENTS 替换

```plain
export function renderBody(
  body: string, args: string
): string {
  if (body.includes("$ARGUMENTS"))
    return body.replaceAll("$ARGUMENTS", args);
  if (args) return `${body}\n\n${args}`;
  return body;
}
```

文件命令统一注册为 `prompt` 类型。如果模板里有 `$ARGUMENTS` 占位符，替换所有出现的位置。没有占位符但传了参数，追加到末尾。没有参数就原样返回。三种情况，优先级从高到低。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 命令类型体系 | 四种联合类型（local / local_ui / prompt / skill_fork） |
| Handler 签名 | `(ctx: CommandContext) => string` ，同步返回，绑定在命令定义上 |
| 上下文依赖注入 | 函数字段惰性求值（ `permissionMode?: () => string` ），按需计算 |
| 别名系统 | 双 Map + `??` 运算符串联查找，注册时四重冲突检测 |
| 文件命令加载 | Markdown + YAML frontmatter，双路径按优先级合并 |
| 参数传递 | `$ARGUMENTS` 占位符替换，无占位符时自动追加 |
| 补全排序 | `CommandUsageTracker` 半衰期加权评分，常用命令排前面 |
| 容错策略 | 注册重名抛异常提前发现，frontmatter 解析失败静默跳过 |

> 更新: 2026-06-08 16:15:54  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/zngwuwug6t2nz5ut](https://www.yuque.com/tianming-uvfnu/gmmfad/zngwuwug6t2nz5ut)