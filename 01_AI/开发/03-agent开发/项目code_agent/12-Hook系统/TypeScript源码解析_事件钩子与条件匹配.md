# TypeScript源码解析：事件钩子与条件匹配

理论篇讲了 Hook 系统的「事件 + 条件 + 动作」三要素，这篇带你走读 MewCode 的实际代码，看一个单文件怎么把事件匹配、条件过滤、动作执行串起来。

## 模块概览

Hook 系统的核心逻辑只在一个文件里：

| 文件 | 职责 |
| --- | --- |
| `hooks.ts` | 类型定义、引擎实现、条件求值、动作执行、校验函数 |

和其他模块动辄三五个文件不同，Hook 系统把所有逻辑都收在一个文件里。职责边界清晰：接收事件、匹配条件、执行动作，不需要拆更细的抽象层。

Hook 的配置结构（ `HookConfig` 接口）定义在配置模块中， `hooks.ts` 通过 `import type` 引入。

## 核心类型

### 事件枚举

```plain
export type EventName =
  | "session_start" | "session_end"
  | "turn_start"    | "turn_end"
  | "pre_send"      | "post_receive"
  | "pre_tool_use"  | "post_tool_use"
  | "shutdown";
```

用联合类型穷举了 9 种合法的事件名。覆盖会话级、轮次级、消息级、工具级、系统级五个层面。其中 `pre_tool_use` 是唯一能拦截工具执行的事件。

联合类型的好处是编译期就能检查事件名拼写，IDE 也能做自动补全。

### 动作类型

通过 `HookConfig` 接口的 `action.type` 字段和 `validate` 函数来约束动作类型：

```plain
const validActions = new Set([
  "command", "prompt", "http", "agent"
]);
```

四种动作都在合法列表里。 `command` 用 `execSync` 同步执行 shell 命令， `prompt` 直接返回文本， `http` 用 `fetch` 发请求， `agent` 通过注入的回调启动子 Agent。

### Hook 配置

Hook 的配置结构通过 `HookConfig` 接口描述：

```plain
interface HookConfig {
  id?: string;
  event: string;
  condition?: string;
  action: {
    type: string;
    command?: string; url?: string;
    method?: string;  prompt?: string;
  };
  reject?: boolean;
  once?: boolean;
  async?: boolean;
  on_error?: string;
}
```

每个字段对应 YAML 配置中的一个属性。 `action` 是嵌套对象，通过 `type` 区分四种动作，不同类型只用到部分字段，这就是「大 union」设计。 `reject` 只在 `pre_tool_use` 事件下有意义。 `once` 控制只触发一次。 `async` 标记后台执行。 `on_error` 控制动作失败时的行为： `ignore` 静默跳过、 `fail` 传播错误、 `reject` 把失败当作拦截处理。

`reject` 和 `async` 互斥：异步 Hook 的结果没法同步拦截工具执行，校验函数会在加载阶段就把这种配置拦下来。

### HookContext 和 HookResult

```plain
export interface HookContext {
  event: EventName;
  toolName?: string;
  args?: Record<string, unknown>;
  filePath?: string;
  message?: string;
}
```

`HookContext` 是条件求值和动作执行的输入。工具相关的事件会填充 `toolName` 、 `args` 、 `filePath` ，生命周期事件可能只有 `event` 和 `message` 。

```plain
export interface HookResult {
  output: string;
  success: boolean;
  reject: boolean;
}
```

`HookResult` 是每条 Hook 执行后的返回值。 `output` 会进入通知队列，最终作为 system reminder 注入到模型上下文。 `reject` 标记是否要拦截工具调用。

变量取值通过 `getContextValue` 实现：

```plain
function getContextValue(
  key: string, ctx: HookContext
): string {
  switch (key) {
    case "tool":  return ctx.toolName ?? "";
    case "event": return ctx.event;
    case "file_path": return ctx.filePath ?? "";
    case "message":   return ctx.message ?? "";
    // 其他 key 直接到 args 字典里找
    default: return String(ctx.args?.[key] ?? "");
  }
}
```

内置变量有 `tool` 、 `event` 、 `file_path` 、 `message` 。其他 key 直接到 `args` 字典里查，未知变量返回空字符串，不会报错。

## Engine：Hook 引擎

```plain
export class HookEngine {
  private hooks: HookConfig[];
  private firedOnce = new Set<string>();
  private notifications: string[] = [];
  // 外部注入的子 Agent 执行器
  agentRunner?: (prompt: string, ctx: HookContext)
    => Promise<string>;
}
```

`hooks` 存所有注册的规则， `firedOnce` 用 Set 追踪哪些 `once` 类型的 Hook 已经触发过， `notifications` 是通知队列。 `agentRunner` 是依赖倒置的回调，由上层注入，让 Hook 引擎不直接依赖 Agent 模块。

引擎在构造时就接收完整的 Hook 列表，配置更新时需要重新创建引擎实例。

## 主流程走读：两条执行路径

### fire：通用的 fire-and-forget

```plain
async fire(event: EventName, context: HookContext)
  : Promise<HookResult[]> {
  const results: HookResult[] = [];
  for (const hook of this.hooks) {
    if (hook.event !== event) continue;
    if (hook.once) {
      const key = hook.id
        ?? `${hook.event}-${hook.action.type}`;
      if (this.firedOnce.has(key)) continue;
      this.firedOnce.add(key);
    }
```

遍历所有 Hook，先按事件名过滤，再检查 `once` 标记。 `once` 用 `Set<string>` 去重，key 优先取 `hook.id` ，没有就拼事件名和动作类型。典型场景是 `session_start` 的初始化 Hook，整个会话只需要跑一次。

接着是条件求值和动作执行：

```plain
// 条件不满足就跳过
    if (hook.condition &&
        !evaluateCondition(hook.condition, context))
      continue;
    // async 钩子：后台执行，不阻塞主流程
    if (hook.async) {
      this.executeAction(hook, context)
        .then((r) => this.recordNotification(r.output))
        .catch((err) => this.recordNotification(
          `Async hook error: ${err.message}`));
      results.push({ output: "(async)",
        success: true, reject: false });
      continue;
    }
```

`async` 标记的 Hook 用 `.then()` 链启动后台执行，不 `await` ，不阻塞主流程。结果或错误都推入通知队列，下一轮对话时模型能看到。

同步分支的核心逻辑：

```plain
try {
      const result =
        await this.executeAction(hook, context);
      results.push(result);
      if (result.reject && event === "pre_tool_use")
        break;  // 拦截后立即短路
    } catch (err) {
      const onError = hook.on_error ?? "ignore";
      if (onError === "reject")
        results.push({ output: `Hook error`,
          success: false, reject: true });
    }
```

关键的 `break` 逻辑：当某条 Hook 的 `reject` 为 true 且当前事件是 `pre_tool_use` 时，直接中断循环，后面的 Hook 不再执行。这就是理论篇说的「写在前面的拦截规则优先级更高」。

错误处理通过 `on_error` 控制。默认是 `ignore` （静默跳过）， `fail` 记录错误信息， `reject` 把异常当作拦截处理。

### firePreToolHooks：唯一能阻断执行的入口

```plain
async firePreToolHooks(toolName: string,
  args: Record<string, unknown>)
  : Promise<{ rejected: boolean; reason: string }> {
  const context: HookContext = {
    event: "pre_tool_use", toolName, args,
    filePath: String(
      args.file_path ?? args.path ?? ""),
  };
  const results =
    await this.fire("pre_tool_use", context);
  for (const r of results) {
    if (r.reject)
      return { rejected: true, reason: r.output };
  }
  return { rejected: false, reason: "" };
}
```

把工具名和参数组装成 `HookContext` ，然后调 `fire` 。返回值简化成 `{ rejected, reason }` ，调用方只需要关心「有没有被拒绝」和「原因是什么」。

注意 `filePath` 的取值有 fallback：先看 `args.file_path` ，再看 `args.path` ，都没有就空字符串。这兼容了不同工具的参数命名习惯。

## 条件匹配

### 条件解析

条件表达式是每次匹配时实时解析的，不做预编译成 AST。用正则按 `&&` 和 `||` 拆分：

```plain
function evaluateCondition(
  condition: string, ctx: HookContext
): boolean {
  const parts = condition.split(/\s*(&&|\|\|)\s*/);
  let result =
    evaluateSingleCondition(parts[0], ctx);
  for (let i = 1; i < parts.length; i += 2) {
    const op = parts[i];
    const next =
      evaluateSingleCondition(parts[i + 1], ctx);
    if (op === "&&") result = result && next;
    else if (op === "||") result = result || next;
  }
  return result;
}
```

`split` 的正则 `/\s*(&&|\|\|)\s*/` 会把分隔符也捕获进结果数组里，所以 `parts` 的奇数位是操作符，偶数位是子表达式。从左到右逐个求值， `&&` 和 `||` 同优先级，允许混用但没有括号支持。

### 叶子条件求值

```plain
function evaluateSingleCondition(
  expr: string, ctx: HookContext
): boolean {
  const trimmed = expr.trim();
  if (trimmed.startsWith("!")) {
    return !evaluateSingleCondition(
      trimmed.slice(1), ctx);
  }
```

支持 `!` 取反，递归处理。然后依次尝试四种运算符：

| 运算符 | 含义 | 匹配方式 |
| --- | --- | --- |
| `==` | 精确相等 | 正则 `/^(\w+)\s*==\s*"([^"]*)"$/` |
| `!=` | 不等于 | 正则 `/^(\w+)\s*!=\s*"([^"]*)"$/` |
| `=~` | 正则匹配 | `new RegExp(pattern).test(value)` |
| `=*` | glob 通配 | 转成正则： `**` → `.*` ， `*` → `[^/]*` ， `?` → `.` |

glob 操作符 `=*` 的实现是把 glob 模式转成正则再匹配：

```plain
const pattern = globMatch[2]
  .replace(/\*\*/g, ".*")
  .replace(/\*/g, "[^/]*")
  .replace(/\?/g, ".");
return new RegExp(`^${pattern}$`).test(value);
```

`**` 转成 `.*` （匹配任意字符包括目录分隔符）， `*` 转成 `[^/]*` （不跨目录）， `?` 转成 `.` （匹配单个字符）。转换后用正则引擎来跑。

条件里写 `command == "ls"` 就能匹配工具参数中 `command` 字段值为 `"ls"` 的情况，因为非内置变量名会直接到 `args` 字典里查。

## 四种动作执行器

### command：执行 shell 命令

```plain
case "command": {
  const output = execSync(command, {
    encoding: "utf-8",
    timeout: 30000,
    env: {
      ...process.env,
      MEWCODE_EVENT: context.event,
      MEWCODE_TOOL: context.toolName ?? "",
      MEWCODE_FILE_PATH: context.filePath ?? "",
    },
  });
  return { output: output.trim(),
    success: true, reject: hook.reject ?? false };
}
```

用 `execSync` 同步执行，超时 30 秒。虽然 `fire` 方法标记了 `async` ，但 `execSync` 会阻塞 Node.js 事件循环直到命令完成。

环境变量注入了 `MEWCODE_EVENT` 、 `MEWCODE_TOOL` 、 `MEWCODE_FILE_PATH` ，外部脚本可以感知是被哪个事件、哪个工具触发的。 `...process.env` 展开继承了当前进程的所有环境变量。

### prompt：注入提示词

```plain
case "prompt":
  return { output: hook.action.prompt ?? "",
    success: true, reject: false };
```

最简单的执行器，直接返回配置中的文本。输出会进入通知队列，最终作为 system reminder 注入模型上下文。

### http：发 HTTP 请求

```plain
case "http": {
  const resp = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(context),
  });
  const text = await resp.text();
  return { output: text, success: resp.ok,
    reject: hook.reject ?? false };
}
```

用 Node.js 内置的 `fetch` 发请求。默认把整个 `HookContext` 序列化为 JSON 作为 body。 `resp.ok` 判断状态码是否在 200-299 范围内。和 command 不同，这里用了 `await` ，不会阻塞事件循环。

### agent：启动子 Agent

```plain
case "agent": {
  if (!this.agentRunner) {
    return {
      output: "agent-type hook configured "
        + "but no AgentRunner registered",
      success: false,
      reject: hook.reject ?? false,
    };
  }
  const prompt =
    hook.action.prompt ?? hook.action.command ?? "";
  const output =
    await this.agentRunner(prompt, context);
  return { output, success: true,
    reject: hook.reject ?? false };
}
```

agent 执行器通过注入的 `agentRunner` 回调执行子 Agent。没有注册回调时返回明确的错误信息，不会静默失败。这个设计让 Hook 引擎不直接依赖 Agent 模块，保持零外部依赖，具体的子 Agent 逻辑由上层在组装时注入。

## 通知机制

```plain
recordNotification(message: string): void {
  if (message.trim())
    this.notifications.push(message);
}

drainNotifications(): string[] {
  const out = this.notifications;
  this.notifications = [];
  return out;
}
```

「取走就清空」的一次性消费模式。 `recordNotification` 推入消息， `drainNotifications` 取走全部并清空。

Agent 主循环在每轮对话开始前 drain 通知，作为 system reminder 注入：

```plain
if (this.hookEngine) {
  for (const note of
    this.hookEngine.drainNotifications()) {
    this.conversation.addSystemReminder(note);
  }
}
```

这个设计解耦了 Hook 执行时机和模型感知时机。 `post_tool_use` 的 Hook 在工具执行后立刻跑，但它的输出要等到下一轮对话才被模型读到。

## 配置加载与校验

```plain
export function validate(
  hooks: HookConfig[]
): Error | null {
  const validEvents = new Set([
    "session_start", "session_end",
    "turn_start", "turn_end",
    "pre_send", "post_receive",
    "pre_tool_use", "post_tool_use", "shutdown"]);
  const validActions = new Set([
    "command", "prompt", "http", "agent"]);
```

校验函数做了完整的检查：事件名合法性、动作类型合法性、必填字段检查（command 类型必须有 `command` 字段，prompt 类型必须有 `prompt` 字段，http 类型必须有 `url` 字段）。

还有关键的语义约束：

```plain
// reject 和 async 互斥：异步钩子的结果无法同步拦截
if (h.reject && h.async) {
  errors.push(
    `${label}: reject and async are mutually exclusive`);
}
```

`reject` 和 `async` 不能同时为 true。异步 Hook 在后台跑，结果还没拿到怎么拦截工具执行？这个约束在加载阶段就卡住了，不等到运行时才出问题。

所有错误收集到数组里，最后一次性返回。fail-fast 原则：非法配置在加载阶段就报错。

## 与 Agent Loop 的集成

Agent 主循环在工具执行前调用 `firePreToolHooks` ：

```plain
if (this.hookEngine) {
  const hookResult = await this.hookEngine
    .firePreToolHooks(tu.toolName, tu.arguments);
  if (hookResult.rejected) {
    events.push({
      type: "tool_result",
      output: `Rejected by hook: ${hookResult.reason}`,
      isError: true,
    });
    continue;  // 跳过工具执行
  }
}
```

被拒绝的工具调用包装成错误类型的 `tool_result` 事件，输出拒绝原因。 `continue` 跳过工具执行。LLM 看到这个错误后可以调整策略，形成反馈循环。

生命周期事件通过 `fireLifecycle` 辅助方法触发：

```plain
private async fireLifecycle(
  event: EventName, message?: string
): Promise<void> {
  if (!this.hookEngine) return;
  const results = await this.hookEngine
    .fire(event, { event, message });
  for (const r of results) {
    if (r.output)
      this.hookEngine.recordNotification(r.output);
  }
}
```

各事件的插入位置： `session_start` 在主循环开始前， `turn_start` 和 `pre_send` 在每轮对话发送前， `post_receive` 在模型响应完成后， `turn_end` 在一轮结束时， `session_end` 在 finally 块中确保一定触发。 `post_tool_use` 在工具执行后单独触发，输出进通知队列，下一轮 drain 注入 system reminder。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 事件模型 | 联合类型定义 9 种事件 |
| 条件语法 | 实时解析， `==` / `!=` / `=~` / `=*` 四种运算符，支持 `&&` /` |
| 动作类型 | command（execSync）、prompt、http（fetch）、agent（agentRunner 回调） |
| 阻断能力 | `firePreToolHooks`返回`{ rejected, reason }` |
| 异步执行 | `async`标记的 Hook 后台执行，结果进通知队列 |
| once 追踪 | `Set<string>`，key 为 id 或事件名+动作类型 |
| 通知机制 | `drainNotifications()`取走并清空，注入 system reminder |
| 配置校验 | `validate`函数检查事件名、动作类型、必填字段、reject/async 互斥 |
| 依赖隔离 | `agentRunner`回调注入，Hook 引擎不直接依赖 Agent 模块 |
| 命令执行 | `execSync`同步阻塞，超时 30 秒 |
| 环境变量 | command 注入`MEWCODE\_EVENT`、`MEWCODE\_TOOL`、`MEWCODE\_FILE\_PATH\` |

> 更新: 2026-06-08 16:27:37  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/ykkm0o969gakgbru](https://www.yuque.com/tianming-uvfnu/gmmfad/ykkm0o969gakgbru)