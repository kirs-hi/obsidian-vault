# TypeScript源码解析：技能加载与执行模式

理论篇讲了 Skill 是「可复用的 SOP」，这篇带你走读 MewCode 的实际代码，看「定义 → 加载 → 执行」这条主线怎么实现。

## 模块概览

Skill 系统的代码集中在 `src/skills/` 目录下，一共五个文件：

| 文件 | 职责 |
| --- | --- |
| `skill.ts` | 核心接口定义：SkillMeta、Skill、SkillHost、SkillForkHost |
| `catalog.ts` | 从磁盘扫描并解析 Skill 文件，维护名字到 Skill 的映射，支持热重载 |
| `executor.ts` | 执行引擎，inline 和 fork 两种运行模式，含 fail-fast 依赖检查 |
| `load-skill-tool.ts` | LoadSkill 工具，让模型按需激活 Skill |
| `install-tool.ts` | InstallSkill 工具，从本地文件或 URL 安装新 Skill |

实现很精简，聚焦核心流程，清晰紧凑。

## 核心类型

### SkillMeta：Skill 的元信息

```plain
export interface SkillMeta {
  name: string;
  description: string;
  allowedTools?: string[];
  mode?: "inline" | "fork";
  model?: string;
  forkContext?: "full" | "recent" | "none";
}
```

interface 天然表达可选性： `allowedTools?` 表示这个字段可以不存在。 `mode` 用联合类型 `"inline" | "fork"` 约束合法值，编译期就能检查类型错误。 `forkContext` 控制 fork 模式下子 Agent 继承多少父对话上下文，有三个合法值。

`allowedTools` 有双重作用：控制 Skill 能调用哪些工具（管副作用），同时控制能看到哪些工具信息（管可见性）。 `mode` 未指定时默认走 `"inline"` 。

### Skill：Meta + 可执行体

```plain
export interface Skill {
  meta: SkillMeta;
  body: string;
  sourceDir: string;
  isDirectory: boolean;
}
```

`body` 是 YAML frontmatter 下面的 Markdown 正文，也就是给 Agent 看的 SOP。 `sourceDir` 记录加载来源目录，后续安装和调试都能追溯。 `isDirectory` 标记是否为目录型 Skill，目录型 Skill 可以包含额外资源（比如 `tool.json` 、 `references/` 等），和单文件 Skill 区分开来。

### SkillCatalog：注册中心

```plain
export class SkillCatalog {
  private entries = new Map<string, CatalogEntry>();

  list(): SkillMeta[] {
    return [...this.entries.values()].map((e) => e.skill.meta);
  }
  get(name: string): Skill | undefined { /* 热重载逻辑 */ }
  has(name: string): boolean {
    return this.entries.has(name);
  }
}
```

用 `Map<string, CatalogEntry>` 存储。 `Map` 在 JavaScript 里保持插入顺序， `list()` 返回的结果和加载顺序一致，注入系统提示词时列表顺序稳定。

同名 Skill 用 `Map.set()` 直接覆盖，后注册的覆盖先注册的，实现优先级。 `get` 返回 `Skill | undefined` 而不是抛异常，类型系统会强制调用方处理 undefined 的情况。

每条记录用 `CatalogEntry` 包装，额外记录了文件路径和修改时间戳，为热重载做准备：

```plain
interface CatalogEntry {
  skill: Skill;
  filePath: string;       // SKILL.md 的绝对路径
  loadedMtimeMs: number;  // 上次加载时的文件修改时间
}
```

## 主流程走读

### 第一步：多位置加载

```plain
load(workDir: string): void {
  const dirs = [
    join(homedir(), ".mewcode", "skills"),
    join(workDir, ".mewcode", "skills"),
  ];
  for (const dir of dirs) {
    if (!existsSync(dir)) continue;
    this.scanDirectory(dir);
  }
}
```

两个位置依次扫描：全局 `~/.mewcode/skills/` → 项目 `.mewcode/skills/` 。因为内部用 `Map.set()` 存储，同名 Skill 后来者覆盖先来者，所以项目级优先级高于全局级。

目录不存在时 `existsSync` 返回 false，静默跳过。单个 Skill 解析失败也会被 try-catch 吞掉，不影响其他 Skill 的加载。

扫描时区分两种形态：子目录里有 `SKILL.md` 的是目录型 Skill（ `isDirectory = true` ），直接放在 skills 目录下的 `.md` 文件是单文件型 Skill（ `isDirectory = false` ）。

### 第二步：两种定义格式

只支持 SKILL.md 单文件格式。解析函数 `parseSkillFile` 找两个 `---` 分隔符，切出 YAML frontmatter 和 Markdown 正文：

```plain
function parseSkillFile(content: string) {
  if (!content.startsWith("---")) return null;
  const endIdx = content.indexOf("---", 3);
  if (endIdx === -1) return null;
  const frontmatter = content.slice(3, endIdx).trim();
  const body = content.slice(endIdx + 3).trim();
  const raw = yaml.load(frontmatter) as Record<string, unknown>;
  if (!raw?.name) return null;
  return { meta: { name, description, mode, ... }, body };
}
```

用 `js-yaml` 的 `yaml.load` 解析 YAML。 `name` 是必填字段，为空直接返回 null 跳过。 `mode` 默认 `"inline"` ， `description` 默认空字符串。没有从目录名或文件名推断名字的 fallback 逻辑，没写 `name` 的 Skill 会被静默丢弃。

### 第三步：内置 Skill 的嵌入

当前没有内置 Skill 的嵌入机制。 `load` 方法只扫描用户和项目目录，不加载内置 Skill。Node.js 可以通过 `import` 或 `fs.readFileSync(join(__dirname, ...))` 读取打包在 npm 包里的资源文件来实现类似功能，但尚未实现这一步。

## 两种执行模式

### Inline 模式（默认）

```plain
export function runInline(
  skill: Skill, args: string, host: SkillHost
): string {
  assertAllowedToolsExist(skill, host); // fail-fast 依赖检查
  let body = skill.body;
  if (body.includes("$ARGUMENTS")) {
    body = body.replaceAll("$ARGUMENTS", args);
  } else if (args) {
    body += `\n\nUser Request: ${args}`;
  }
  host.activateSkill(skill.meta.name, body);
  if (skill.meta.allowedTools) {
    const allowed = new Set(skill.meta.allowedTools);
    host.setToolFilter((name) => allowed.has(name));
  }
  return body;
}
```

四件事：依赖检查、参数替换、激活 SOP、设置工具过滤器。

先做 `assertAllowedToolsExist` 检查，如果白名单里有未注册的工具名直接抛错，不会进入激活流程。参数替换逻辑：有 `$ARGUMENTS` 就替换，没有就追加 `User Request: ...` 到末尾。工具过滤用 `Set.has()` 做 O(1) 查找， `allowedTools` 未定义时不设置过滤器，所有工具都可用。

### Fork 模式

```plain
export async function runFork(
  skill: Skill, args: string, host: SkillForkHost
): Promise<string> {
  assertAllowedToolsExist(skill, host);
  let prompt = skill.body;
  if (args) prompt += `\n\nARGUMENTS: ${args}`;
  const contextMode = skill.meta.forkContext ?? "none";
  if (contextMode === "recent") {
    const context = host.snapshotParentMessages(5);
    prompt = `Context from parent conversation:\n${context}\n\n${prompt}`;
  } else if (contextMode === "full") {
    const context = host.snapshotParentMessages(100);
    prompt = `Context from parent conversation:\n${context}\n\n${prompt}`;
  }
  return host.runSubAgent(prompt, skill.meta.allowedTools);
}
```

fork 模式不修改当前对话，通过 `host.runSubAgent` 启动独立子 Agent。

上下文传递策略通过 `snapshotParentMessages` 实现： `"recent"` 取最近 5 条消息， `"full"` 取 100 条， `"none"` 不传（默认值）。上下文作为一段文本前置在 prompt 前面，格式是 `Context from parent conversation:\n...` 。参数追加的格式和 inline 不同：fork 用 `ARGUMENTS:` ，inline 用 `User Request:` 。

工具白名单通过 `host.runSubAgent` 的第二个参数传递，由 Agent 层面创建过滤后的工具集合，子 Agent 和主 Agent 完全隔离。

## 参数传递与 $ARGUMENTS 替换

inline 模式的参数处理覆盖三种情况：

```plain
if (body.includes("$ARGUMENTS")) {
  body = body.replaceAll("$ARGUMENTS", args);
} else if (args) {
  body += `\n\nUser Request: ${args}`;
}
```

有 `$ARGUMENTS` 占位符就全局替换（ `replaceAll` 会替换所有出现位置）；没占位符但有参数就追加到末尾；两者都没有则原样返回。

fork 模式更简单，直接在末尾追加 `ARGUMENTS: ${args}` ，不做占位符检查。设计取舍是简洁性优先，代价是 fork 模式下参数位置不可控。

## 工具白名单与系统工具放行

执行前的 fail-fast 依赖检查：

```plain
function assertAllowedToolsExist(skill: Skill, host: SkillHost): void {
  if (!skill.meta.allowedTools || skill.meta.allowedTools.length === 0)
    return;
  const registry = host.toolRegistry();
  for (const toolName of skill.meta.allowedTools) {
    if (!registry.get(toolName)) {
      throw new Error(
        `skill "${skill.meta.name}" declares allowed tool "${toolName}" which is not registered`
      );
    }
  }
}
```

白名单为空不限制。非空时遍历每个工具名，在 Registry 里找不到就立刻抛错。这比让模型在运行时才发现工具不存在要好得多。

系统工具的放行在 Agent 主循环里实现。 `LoadSkillTool` 和 `InstallSkillTool` 都声明了 `system = true` ，Agent 构建工具列表时判断 `system === true` 就跳过过滤：

```plain
toolSchemas = toolSchemas.filter((s) => {
  const n = s.name as string;
  return this.registry.get(n)?.system === true || this.toolFilter!(n);
});
```

即使 Skill 的 allowedTools 只列了 Bash，模型仍然能调用 LoadSkill 加载其他 Skill。

## 上下文生成与 SOP 注入

Skill 激活后，SOP 正文通过 `host.activateSkill(name, body)` 存到 Agent 的 `activeSkills` Map 里。每轮对话开始前，Agent 调用 `buildActiveSkillsReminder` 把所有激活的 Skill 拼成一段 system reminder：

```plain
function buildActiveSkillsReminder(active: Map<string, string>): string {
  if (active.size === 0) return "";
  let out = "# Active Skills\n\n...";
  for (const [name, body] of active) {
    out += `## Active Skill: ${name}\n\n${body}\n\n`;
  }
  return out;
}
```

多个 Skill 同时激活时，按 Map 的插入顺序依次拼接，每个 Skill 用二级标题分隔。零激活时返回空字符串，不注入任何内容，零开销。

## 自定义工具（目录型 Skill）

Skill 接口里有 `isDirectory` 字段标记目录型 Skill， `scanDirectory` 也区分了目录和单文件两种形态。但当前没有实现 `tool.json` 的解析和自定义工具的动态加载。

也就是说，目录型 Skill 的「目录」能力只体现在加载 `SKILL.md` ，额外的资源文件（ `tool.json` 、 `references/` ）不会被处理。 `isDirectory` 字段已经预留，后续扩展时不需要改 Skill 接口，只要在加载时多一步 `tool.json` 解析即可。

和 `allowedTools` 的分工也很清晰： `allowedTools` 负责限制 Skill 能看到哪些已有工具，而 `tool.json` （如果实现了）负责注册全新的工具。两者一个是过滤器，一个是生产者。

## 热重载（如果实现了）

`get()` 方法在每次调用时检查文件是否被修改过，如果修改了就重新读取并解析：

```plain
get(name: string): Skill | undefined {
  const entry = this.entries.get(name);
  if (!entry) return undefined;
  if (entry.filePath && entry.loadedMtimeMs > 0) {
    try {
      const currentMtime = statSync(entry.filePath).mtimeMs;
      if (currentMtime > entry.loadedMtimeMs) {
        const raw = readFileSync(entry.filePath, "utf-8");
        const parsed = parseSkillFile(raw);
        if (parsed) {
          entry.skill = { meta: parsed.meta, body: parsed.body, ... };
          entry.loadedMtimeMs = currentMtime;
        }
      }
    } catch { /* 读取失败保留缓存版本 */ }
  }
  return entry.skill;
}
```

通过 `statSync` 比较文件的 `mtimeMs` （修改时间戳），只在文件确实被改过时才重新读取，避免无谓的 I/O。

缓存兜底策略：重新解析失败时（ `parsed` 为 null），或者读取文件出异常时（catch 分支），都保留上一次成功加载的版本。内嵌 Skill 的 `loadedMtimeMs` 为 0，跳过整个重载逻辑。

## 远程安装（如果实现了）

InstallSkillTool 支持本地文件和 HTTPS URL 两种来源：

```plain
if (/^https?:\/\//.test(source)) {
  const resp = await fetch(source);
  content = await resp.text();
} else {
  const p = isAbsolute(source) ? source : join(this.workDir, source);
  content = readFileSync(p, "utf-8");
}
```

拿到内容后，从 frontmatter 里提取 name（或用参数指定、或用文件名兜底），写入 `.mewcode/skills/<name>/SKILL.md` ，最后调 `catalog.load()` 重新扫描。安装后立刻可用，不需要重启。

只支持单个 SKILL.md 文件的下载，不支持递归下载整个 Skill 目录。也没有原子写入和大小限制等安全防护。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 多位置加载 | 全局 → 项目两级， `Map.set` 后来者覆盖 |
| 定义格式 | 只支持 SKILL.md 单文件格式，js-yaml 解析 frontmatter |
| Inline 执行 | `assertAllowedToolsExist` 检查 → 参数替换 → `activateSkill` 钉 SOP → `setToolFilter` 闭包过滤 |
| Fork 执行 | `runSubAgent` 启动子 Agent，字符串形式传递父对话快照 |
| 工具白名单 | `Set.has` 做 O(1) 过滤， `system = true` 标记系统工具放行，fail-fast 依赖检查 |
| 参数替换 | 有 `$ARGUMENTS` 就替换，没有就追加 `User Request` （inline）/ `ARGUMENTS` （fork） |
| 自定义工具 | `isDirectory` 标记已预留， `tool.json` 解析尚未实现 |
| 上下文注入 | `activateSkill` 存到 Map，每轮重建 system reminder，零激活零开销 |
| 热重载 | `get()` 时比较 `mtimeMs` ，变化则重读，失败保留缓存 |
| 远程安装 | InstallSkillTool 支持本地文件和 HTTPS URL，写入后重新扫描 |
| 容错策略 | 解析失败静默跳过，catch 住所有异常不中断加载 |

> 更新: 2026-06-08 16:22:49  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/ng2h0dzoybzh0hly](https://www.yuque.com/tianming-uvfnu/gmmfad/ng2h0dzoybzh0hly)