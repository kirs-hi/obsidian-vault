# TypeScript源码解析：子 Agent 创建与任务管理

这篇走读 MewCode 的 SubAgent 代码，看看「把 Agent 包装成工具」在 TypeScript 里是怎么落地的。代码集中在 `src/agents/` 目录，是四种语言实现中最精简的一版。

## 模块概览

SubAgent 系统在 `src/agents/` 目录下，一共五个文件：

| 文件 | 职责 |
| --- | --- |
| `definition.ts` | AgentDefinition 接口 + 三个内置 Agent 常量 |
| `loader.ts` | 加载 Agent 定义文件，YAML frontmatter 解析 |
| `agent-tool.ts` | AgentTool 类，Tool 接口实现 |
| `spawn.ts` | spawnSubAgent 函数，子 Agent 创建和执行 |
| `task-manager.ts` | TaskManager，Promise 驱动的后台任务管理 |

五个文件覆盖了定义式创建、Fork 模式和后台任务管理。

## 核心类型

### AgentDefinition：TypeScript interface

用 interface 定义 Agent 蓝图，在 `definition.ts` 里：

```plain
export interface AgentDefinition {
 name: string;
 description: string;
 tools?: string[];
 disallowedTools?: string[];
 systemPromptOverride?: string;
 maxTurns?: number;
 model?: string;
 permissionMode?: PermissionMode;
 background?: boolean;
 isolation?: "worktree";
 // 还有 initialPrompt, skills, memory, mcpServers 等可选字段
}
```

字段比较全， `permissionMode` 、 `background` 、 `isolation` 、 `skills` 、 `memory` 、 `mcpServers` 都有。不过大部分可选字段在当前实现中还没有被消费（ `spawn.ts` 里只用到了 `name` 、 `description` 、 `tools` 、 `disallowedTools` 、 `systemPromptOverride` 、 `maxTurns` 、 `model` 、 `permissionMode` ）。

interface 里 `name` 和 `description` 不做字段名映射，直接就叫 `name` 和 `description` ，和 YAML 里的键名一致。

### 内置 Agent 常量

三个内置 Agent 以数组常量定义：

```plain
export const BUILTIN_AGENTS: AgentDefinition[] = [
 { name: "general-purpose",
 description: "General-purpose agent..." },
 { name: "plan",
 description: "Software architect agent...",
 disallowedTools: ["EditFile", "WriteFile"],
 permissionMode: "plan" },
 { name: "explore",
 description: "Fast read-only search agent...",
 disallowedTools: ["EditFile", "WriteFile", "Bash"],
 permissionMode: "plan", model: "haiku" },
];
```

`explore` 禁用了 EditFile、WriteFile、Bash 三个工具。 `plan` 和 `explore` 都设了 `permissionMode: "plan"` 。 `general-purpose` 没有设 `maxTurns` ，走默认值（spawn.ts 里兜底 200）。

没有 Verification Agent。

### TaskManager：Promise 驱动

后台任务管理在 `task-manager.ts` ，用 Promise 实现：

```plain
export interface AgentTask {
 id: string;
 name: string;
 status: "running" | "completed" | "failed";
 output: string;
 cancel: () => void;
}

export class TaskManager {
 private tasks = new Map<string, AgentTask>();
 private nextId = 1;
}
```

三种状态： `running` 、 `completed` 、 `failed` 。没有 `pending` 和 `cancelled` 。

`create` 方法接收一个 runner（ `() => Promise<string>` ）和一个 cancel 函数，立刻启动 Promise 并返回 task 对象：

```plain
create(name: string, runner: () => Promise<string>,
 cancel: () => void): AgentTask {
 const id = String(this.nextId++);
 const task: AgentTask = {
 id, name, status: "running", output: "", cancel,
 };
 this.tasks.set(id, task);
 runner()
 .then((output) => { task.status = "completed"; task.output = output; })
 .catch((err) => { task.status = "failed"; task.output = `Error: ${...}`; });
 return task;
}
```

Promise 的 then/catch 自动处理完成和失败，不需要手动做异常保护。

`drainNotifications` 返回所有非 running 状态的任务，但不清除已返回的记录。这意味着同一个完成的任务可能被多次返回，调用方需要自己做去重。

没有 `adoptRunning` 方法。不支持前台到后台的动态切换。

## Agent 定义的加载

### 加载优先级

`loadAgentDefinitions` 在 `loader.ts` 里，逻辑比较简化：

```plain
export function loadAgentDefinitions(workDir: string): AgentDefinition[] {
 const definitions = [...BUILTIN_AGENTS];
 const dirs = [join(workDir, ".mewcode", "agents")];
 for (const dir of dirs) {
 if (!existsSync(dir)) continue;
 for (const file of readdirSync(dir).filter((f) => f.endsWith(".md"))) {
 const def = parseAgentDefinition(readFileSync(join(dir, file), "utf-8"));
 if (!def) continue;
 const idx = definitions.findIndex((d) => d.name === def.name);
 if (idx >= 0) definitions[idx] = def;
 else definitions.push(def);
 }
 }
 return definitions;
}
```

只扫描项目目录（ `.mewcode/agents/` ），不扫描用户目录（ `~/.mewcode/agents/` ）。只有两级加载：内置 + 项目。

同名定义通过 `findIndex` 查找并替换，项目级覆盖内置。

### 定义文件的解析

`parseAgentDefinition` 做 frontmatter 解析：

```plain
function parseAgentDefinition(content: string): AgentDefinition | null {
 if (!content.startsWith("---")) return null;
 const endIdx = content.indexOf("---", 3);
 if (endIdx === -1) return null;
 const frontmatter = content.slice(3, endIdx).trim();
 const body = content.slice(endIdx + 3).trim();
 const raw = yaml.load(frontmatter) as Record<string, unknown>;
 if (!raw?.name) return null;
 return {
 name: raw.name as string,
 description: (raw.description as string) ?? body.slice(0, 200),
 initialPrompt: body || undefined, // ...
 };
}
```

有两个有趣的设计。第一，如果 frontmatter 里没有 `description` ，就用 body 的前 200 个字符作为 description，不报错。第二，Markdown body 被映射到 `initialPrompt` 字段而不是 `systemPromptOverride` ，对 body 的用途理解和理论篇描述的不同。

没有字段校验，不检查 model 合法性、permissionMode 合法性。解析过程中任何异常都被 catch 然后返回 null，静默跳过。

### 热重载（如果实现了）

没有热重载机制。 `loadAgentDefinitions` 在 AgentTool 构造函数里调一次，之后不会重新加载。

## 两种创建模式

### Definition-based：预定义专家

只实现了定义式创建。 `spawnSubAgent` 在 `spawn.ts` 里：

```plain
export async function spawnSubAgent(
 definition: AgentDefinition, prompt: string,
 parentClient: LLMClient, parentRegistry: ToolRegistry,
 parentProvider: ProviderConfig, workDir: string,
): Promise<string> {
 // 模型选择：定义级 > 继承父 Agent
 const resolvedModel = definition.model
 ? resolveModelId(definition.model) : parentProvider.model;
 const client = definition.model
 ? await createClient({...parentProvider, model: resolvedModel}, ...)
 : parentClient;
 // 工具过滤：只有黑名单 + 白名单两层
 const disallowed = new Set(definition.disallowedTools ?? []);
 for (const tool of parentRegistry.listTools())
 if (!disallowed.has(tool.name)) registry.register(tool);
```

工具过滤直接在 spawn 函数里做，只有两层：定义级黑名单（ `disallowedTools` ）和白名单（ `tools` ）。没有全局禁用层和异步白名单层。这意味着如果定义里没有禁 `Agent` 工具，子 Agent 理论上可以再 spawn 子 Agent，存在递归风险。

模型选择也在这个函数里。如果定义指定了 model，通过 `resolveModelId` 解析别名到具体 model ID，再创建新的 LLM 客户端。不指定就用父 Agent 的客户端。

子 Agent 的执行用 `for await` 消费异步迭代器：

```plain
const agent = new Agent({
 client, registry, checker, conversation: conv,
 workDir, maxIterations: definition.maxTurns ?? 200,
});

let output = "";
for await (const event of agent.run()) {
 switch (event.type) {
 case "stream_text": output += event.text; break;
 case "loop_complete": return output || "[No output]";
 case "error": return `Error: ${event.error.message}`;
 }
}
```

`for await` 直接在 async generator 上迭代，写法非常简洁。

### Fork-based：未实现

没有 Fork 模式。 `agent-tool.ts` 里的 `execute` 方法给 `subagent_type` 设了默认值 `"general-purpose"` ，如果用户不指定就用通用 Agent，而不是走 Fork 路径。

## 工具过滤

的工具过滤很简单，直接在 `spawnSubAgent` 函数里做：

```plain
const allowedTools = definition.tools
 ? new Set(definition.tools) : null;
const disallowed = new Set(definition.disallowedTools ?? []);
for (const tool of parentRegistry.listTools()) {
 if (disallowed.has(tool.name)) continue;
 if (allowedTools && !allowedTools.has(tool.name)) continue;
 registry.register(tool);
}
```

只有两层：黑名单过滤 + 白名单交集。没有 MCP 工具直通、全局禁用、自定义 Agent 限制、异步白名单这些层。

只有两层过滤意味着安全边界更薄。没有全局禁用层意味着子 Agent 可能能调到 Agent 工具（如果定义里没禁），没有异步白名单意味着后台 Agent 的工具集没有额外限制。

## 执行路径

### execute 入口

`AgentTool.execute` 比较简单：

```plain
async execute(args, _ctx): Promise<ToolResult> {
 const prompt = strArg(args, "prompt");
 const agentType = strArg(args, "subagent_type",
 "general-purpose");
 const background = args.run_in_background === true;
 const definition = this.definitions.find(
 (d) => d.name === agentType);
 if (!definition) return { output: "Error: unknown agent type", isError: true };
 const output = await this.spawnHandler(
 definition, prompt, background);
 return { output, isError: false };
}
```

没有 team\_name 检查，没有 Fork 路径。只有一条路径：查找定义 → 调 spawnHandler。background 参数传给 spawnHandler，由外部决定怎么处理。

spawnHandler 是构造函数注入的回调，解耦了 AgentTool 和实际的 spawn 逻辑。

### 前台同步执行

`spawnSubAgent` 是一个 async 函数，直接 await 到子 Agent 完成。不需要单独的 runSync 方法。

### 后台异步执行

后台执行通过 `TaskManager.create` 包装。调用方把 `spawnSubAgent` 包成一个 runner 传给 TaskManager，Promise 自动在后台执行。

### Worktree 隔离

没有实现 worktree 隔离。 `AgentDefinition` 接口里有 `isolation?: "worktree"` 字段，但 `spawnSubAgent` 里没有处理它。

## 模型选择

模型选择在 `spawnSubAgent` 里：

```plain
const resolvedModel = definition.model
 ? resolveModelId(definition.model)
 : parentProvider.model;
const client: LLMClient = definition.model
 ? await createClient({...parentProvider, model: resolvedModel}, systemPrompt)
 : parentClient;
```

两级优先级：定义级 > 继承父 Agent。没有调用参数级的覆盖，因为 schema 里没有暴露 `model` 参数给 LLM。

`resolveModelId` 把别名（ `haiku` 、 `sonnet` 、 `opus` ）映射到具体的 model ID。定义了 model 时会创建新的 LLM 客户端，不定义就复用父 Agent 的。

## 动态 Schema 生成

`schema()` 方法里没有动态生成 `subagent_type` 的 enum 列表。Schema 是硬编码的，只有 `description` 、 `prompt` 、 `subagent_type` 、 `run_in_background` 四个参数， `subagent_type` 的 description 里写着「(general-purpose, plan, explore)」但没有 enum 约束。

这意味着 LLM 可能会传入不存在的 agent type 名称，虽然 execute 里有兜底检查会返回错误。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| Agent 定义格式 | Markdown + YAML frontmatter， `parseAgentDefinition` 解析 |
| 定义类型 | `AgentDefinition` interface |
| 加载级别 | 内置 + 项目目录，两级（无用户级） |
| 上下文隔离 | 只有 Definition 模式，全新对话 |
| 工具过滤层数 | 两层（定义级黑名单 + 白名单），无全局禁用和异步白名单 |
| 后台任务机制 | TaskManager + Promise then/catch |
| 异步并发 | async/await + Promise |
| 执行分发路径 | 只有一条：定义式（无 Fork、无 team） |
| 事件消费 | `for await` 迭代异步 generator |
| 文件隔离 | 未实现 |

> 更新: 2026-06-08 16:32:10  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/zkhb66ywwhnqz8ig](https://www.yuque.com/tianming-uvfnu/gmmfad/zkhb66ywwhnqz8ig)