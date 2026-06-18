# TypeScript源码解析：Agent 主循环与事件流

理论篇讲了 Agent Loop 的设计理念和 ReAct 范式，这篇带你走读 MewCode 的真实代码，看看「调 LLM → 执行工具 → 喂回结果」这条主线是怎么实现的。

## 模块概览

Agent Loop 的代码集中在 `src/agent/` 目录，三个文件：

| 文件 | 职责 |
| --- | --- |
| `events.ts` | 定义 `AgentEvent` 联合类型，是循环对外通信的唯一出口 |
| `agent.ts` | Agent 类本体，包含主循环 `run()` 、工具执行、权限检查、自愈逻辑 |
| `streaming-executor.ts` | 工具并发执行器，接收 pending 调用并用 `Promise.all` 并行跑 |

`agent.ts` 是整个项目最核心的文件，所有其他模块最终都汇聚到这里。

## 核心类型

### Agent 类和 AgentConfig

通过构造函数接收一个 `AgentConfig` 对象，把所有外部依赖显式注入：

```plain
export interface AgentConfig {
 client: LLMClient; // LLM 客户端
 registry: ToolRegistry; // 工具注册表
 checker: PermissionChecker; // 权限检查器
 conversation: ConversationManager;
 workDir: string;
 abortSignal?: AbortSignal; // 取消信号
 contextWindow?: number; // 默认 200000
 maxIterations?: number; // 0 表示不限
 hookEngine?: HookEngine;
 onPermissionRequest?: (...) => Promise<"allow" | "deny" | "allowAlways">;
 // ... 其他可选字段
}
```

核心三件套： `client` 负责 LLM 通信， `registry` 提供工具， `checker` 做权限检查。 `conversation` 也是必传的，因为 把对话管理器放在了外面，由调用方创建。

值得注意的是 `abortSignal` ，用的是 Web 标准的 `AbortSignal` 。用户按 Esc 时外层触发 abort，循环内部在多个检查点检测到信号后优雅退出。

`onPermissionRequest` 是一个可选的回调函数。Agent 需要权限确认时直接 `await this.onPermissionRequest(...)` ，调用方在回调里弹窗让用户选择，返回结果。这种回调模式比 channel/Future 更直观，一行代码搞定等待用户回应。

### AgentEvent：discriminated union

```plain
export type AgentEvent =
 | { type: "stream_text"; text: string }
 | { type: "tool_use"; toolName: string; toolId: string; args: Record<string, unknown> }
 | { type: "tool_result"; toolName: string; toolId: string; output: string; isError: boolean; elapsed: number }
 | { type: "turn_complete" }
 | { type: "loop_complete"; stopReason: string }
 | { type: "usage"; usage: UsageInfo }
 | { type: "error"; error: Error }
 | { type: "compact"; message: string; boundary?: CompactBoundaryPayload }
 | { type: "retry"; reason: string; delay: number }
 | { type: "permission_request"; toolName: string; args: Record<string, unknown> }
```

这是一个 discriminated union，外层通过 `event.type` 就能区分具体事件。类型收窄在这里发挥作用： `if (event.type === "stream_text")` 之后，编译器自动知道 `event.text` 存在。

整个 Agent 的 `run()` 方法是一个 `AsyncGenerator<AgentEvent>` ，外层用 `for await` 逐个接收事件。TUI 层和 Agent 内核完全解耦：TUI 只管渲染事件，不用关心循环内部逻辑。

## 主循环走读

### 入口：run()

```plain
async *run(): AsyncGenerator<AgentEvent> {
 let toolSchemas = this.registry.getAllSchemas();
 if (this.toolFilter) {
 toolSchemas = toolSchemas.filter((s) =>
 this.registry.get(s.name as string)?.system === true
 || this.toolFilter!(s.name as string));
 }
 let maxTokensEscalated = false;
 let outputRecoveries = 0;
 let consecutiveUnknown = 0;
 let iteration = 0;
 await this.fireLifecycle("session_start");
```

`async *run()` 是一个 async generator 方法。调用方用 `for await (const event of agent.run())` 消费事件，每次 `yield` 一个事件就暂停 generator，等消费方准备好再继续。这种惰性推送不需要显式的缓冲区管理。

启动前先过滤工具列表：如果有 skill 设置了 `toolFilter` ，只保留通过过滤的工具和系统工具。然后触发 session\_start 生命周期事件。

几个局部变量追踪循环状态： `maxTokensEscalated` 记录输出上限是否已提升过， `consecutiveUnknown` 计数连续未知工具调用次数， `outputRecoveries` 计数分段续写次数。

### 循环骨架

```plain
let looping = true;
while (looping) {
 iteration++;
 // 1. 检查迭代上限 7. Layer 1 工具输出预算
 // 2. 上下文压缩管理 8. 调 LLM，消费流式响应
 // 3. Plan Mode 注入 9. 错误恢复
 // 4. Skill SOP 注入 10. max_tokens 恢复
 // 5. Hook 通知注入 11. 有工具 → 执行 → continue
 // 6. 生命周期事件 12. 无工具 → looping = false
}
```

用 `looping` 标志控制循环退出，比 `break` 更灵活，适合多个退出点的场景。

### 调用 LLM 和消费流式响应

```plain
const stream = this.client.stream(apiConv, toolSchemas, this.abortSignal);
for await (const event of stream) {
 if (this.abortSignal?.aborted) { looping = false; break; }
 switch (event.type) {
 case "text_delta":
 fullText += event.text;
 yield { type: "stream_text", text: event.text };
 break;
 case "tool_call_complete":
 toolUses.push({ toolUseId: event.toolId, toolName: event.toolName, ... });
 break;
 case "stream_end":
 stopReason = event.stopReason;
 this.usageAnchor = { baselineTokens: /* ... */, anchorCount: sentMessageCount };
 break;
 }
}
```

`for await` 遍历 LLM 的流式事件。每收到一个 `text_delta` 就立刻 yield 出去，TUI 实时渲染。 `tool_call_complete` 收集到列表。 `stream_end` 记录停止原因和 Token 用量，同时刷新 usage anchor 用于下一轮的上下文管理。

每次进入 `for await` 的循环体前都检查 `abortSignal` ，确保用户取消能及时响应。

在流消费阶段只收集工具调用信息，不立即执行。流消费完毕后才统一执行工具。

### 终止判断

```plain
if (toolUses.length > 0) {
 const results = await this.executeTools(toolUses);
 for (const r of results) yield r;
 this.conversation.addToolResultsMessage(toolResults);
 yield { type: "turn_complete" };
 await this.fireLifecycle("turn_end");
} else {
 looping = false;
 yield { type: "loop_complete", stopReason };
 if (this.onLoopComplete) {
 try { this.onLoopComplete(this.conversation); } catch {}
 }
}
```

有工具调用就执行工具、把结果追加到对话、 `continue` 进入下一轮。没有工具调用就设 `looping = false` ，发 `loop_complete` 事件。

`onLoopComplete` 是 fire-and-forget 回调，失败了也不影响主循环。第9章的记忆系统会挂在这里，循环结束后异步提取对话中的记忆。

### 工具结果收集

```plain
const toolResults: ToolResultBlock[] = [];
for (const r of results) {
 if (r.type === "tool_result") {
 toolResults.push({
 toolUseId: r.toolId,
 content: r.output.length > MAX_OUTPUT_CHARS
 ? r.output.slice(0, MAX_OUTPUT_CHARS)
 + "\n… (output truncated)"
 : r.output,
 isError: r.isError,
 });
 }
}
this.conversation.addToolResultsMessage(toolResults);
```

完整输出通过 `tool_result` 事件推给 UI 展示，截断后的版本写入对话历史。 `MAX_OUTPUT_CHARS` 是 10000，防止上下文被超长工具输出撑爆。

## 四个停止条件

### LLM 不再调用工具

就是上面 `toolUses.length === 0` 的分支。最常见的正常退出路径，模型自然收尾。

### 迭代次数上限

```plain
if (this.maxIterations > 0 &&
 iteration > this.maxIterations) {
 yield {
 type: "error",
 error: new Error(`Agent reached maximum iterations (${this.maxIterations})`),
 };
 return;
}
```

`maxIterations` 为 0 表示不限制。超限后发 error 事件然后 `return` ，generator 结束。

### 连续未知工具

```plain
for (const tu of toolUses) {
 if (this.registry.get(tu.toolName))
 consecutiveUnknown = 0;
 else consecutiveUnknown++;
}
if (consecutiveUnknown >= 3) {
 yield { type: "error",
 error: new Error(
 "Too many consecutive unknown tool calls") };
 return;
}
```

连续 3 次调用不存在的工具就终止。中间有一次正常调用就重置计数。

### 用户取消

```plain
if (this.abortSignal?.aborted) {
 if (fullText) {
 this.conversation.addAssistantFull(
 fullText, thinkingBlocks, []);
 }
 yield { type: "loop_complete", stopReason: "interrupted" };
 return;
}
```

用 Web 标准的 `AbortSignal` 。多个检查点检测 abort 状态：流消费循环里每次迭代检查一次，流消费结束后再检查一次。被取消时把已有的文本保存到对话历史（不丢失），然后发一个 `stopReason: "interrupted"` 的 `loop_complete` 。

## 工具执行

### executeTools：三关流程

`executeTools` 方法处理一轮中所有工具调用。对每个工具调用按顺序过三关：

**第一关：Pre-tool Hook**

```plain
if (this.hookEngine) {
 const hookResult = await this.hookEngine
 .firePreToolHooks(tu.toolName, tu.arguments);
 if (hookResult.rejected) {
 events.push({
 type: "tool_result",
 output: `Rejected by hook: ${hookResult.reason}`,
 isError: true, elapsed: 0,
 });
 continue;
 }
}
```

Hook 可以在权限检查之前就拦截工具执行。

**第二关：权限检查**

```plain
const decision = this.checker.check(tu.toolName, category, tu.arguments);
if (decision.effect === "deny") {
 events.push({ type: "tool_result",
 output: `Permission denied: ${decision.reason}...`, isError: true, elapsed: 0 });
 continue;
}
if (decision.effect === "ask" && this.onPermissionRequest) {
 const response = await this.onPermissionRequest(tu.toolName, tu.arguments, decision);
 if (response === "deny") { /* 返回拒绝结果 */ continue; }
 if (response === "allowAlways") this.checker.allowAlways(tu.toolName, tu.arguments);
}
```

三种结果： `deny` 直接拒绝， `allow` 放行， `ask` 通过 `onPermissionRequest` 回调交给 UI 处理。用户选了 `allowAlways` 的话，会调 `checker.allowAlways()` 写入永久允许规则。

的权限交互用回调函数而不是 Future/channel，代码更直观： `await this.onPermissionRequest(...)` 一行搞定等待用户回应。

**第三关：提交执行**

通过检查后，工具调用提交给 `StreamingExecutor` 。

### StreamingExecutor：并行执行

```plain
export class StreamingExecutor {
 private pending: PendingCall[] = [];

 submit(toolId: string, toolName: string, args: Record<string, unknown>): void {
 this.pending.push({ toolId, toolName, arguments: args });
 }

 async collectResults(): Promise<ExecutionResult[]> {
 const calls = [...this.pending]; this.pending = [];
 const promises = calls.map(async (call) => {
 const tool = this.registry.get(call.toolName);
 if (!tool) return { toolId: call.toolId, toolName: call.toolName, result: { output: "Error: unknown tool", isError: true }, elapsed: 0 };
 const start = Date.now();
 return { toolId: call.toolId, toolName: call.toolName, result: await tool.execute(call.arguments, this.ctx), elapsed: (Date.now() - start) / 1000 };
 });
 return Promise.all(promises);
 }
}
```

`submit` 把调用加入队列， `collectResults` 用 `Promise.all` 并行执行所有 pending 的调用。一轮里如果模型同时调了多个工具（比如同时读两个文件），它们会并行执行。

没有显式的分批策略，所有工具一律并行执行，安全性由权限检查器在提交前保证。这简化了执行器的实现，但意味着写操作也可能并行跑。

## 错误恢复与自愈

### 上下文过长恢复

```plain
if (e instanceof ContextTooLongError) {
 try {
 const result = await forceCompact(this.conversation, this.client,
 this.recoveryState, toolSchemaNames, this.sessionFilePath);
 this.usageAnchor = null; // 压缩后锚点失效
 yield { type: "compact", message: "Auto-compacted: " + result.message };
 continue; // 重试这一轮
 } catch {
 yield { type: "error", error: e };
 return;
 }
}
```

API 返回上下文过长错误时，触发强制压缩，把对话历史摘要化，然后 `continue` 重试本轮。压缩后 usage anchor 重置为 null，因为旧的统计基线不再准确。压缩失败则发 error 事件退出。

### 限流等待重试

```plain
if (e instanceof RateLimitError) {
 const waitMs = parseRetryAfter(e.retryAfter);
 yield { type: "retry",
 reason: "rate limited", delay: waitMs };
 if (await this.interruptibleSleep(waitMs)) {
 yield { type: "loop_complete",
 stopReason: "interrupted" };
 return;
 }
 continue;
}
```

限流时解析 `Retry-After` 头（默认 5 秒），发 retry 事件通知 UI，然后进入可中断的睡眠。 `interruptibleSleep` 用 `AbortSignal` 监听取消：

```plain
private interruptibleSleep(ms: number): Promise<boolean> {
 return new Promise((resolve) => {
 if (this.abortSignal?.aborted) return resolve(true);
 const onAbort = () => {
 clearTimeout(timer);
 resolve(true);
 };
 const timer = setTimeout(() => {
 this.abortSignal?.removeEventListener("abort", onAbort);
 resolve(false);
 }, ms);
 this.abortSignal?.addEventListener("abort", onAbort, { once: true });
 });
}
```

定时器到期返回 `false` （继续重试），用户中途取消返回 `true` （退出循环）。

### 输出截断恢复（max\_tokens）

```plain
if (stopReason === "max_tokens") {
 if (!maxTokensEscalated) {
 (this.client as Partial<MaxTokensSetter>).setMaxOutputTokens?.(MAX_TOKENS_CEILING);
 maxTokensEscalated = true;
 if (fullText) {
 this.conversation.addAssistantFull(fullText, thinkingBlocks, []);
 this.conversation.addUserMessage("Output token limit hit. Resume...");
 }
 yield { type: "retry", reason: "max_tokens escalation", delay: 0 };
 continue; // 第一阶段：提升上限
 } else if (outputRecoveries < MAX_OUTPUT_TOKENS_RECOVERIES) {
 outputRecoveries++;
 this.conversation.addUserMessage("Break remaining work...");
 continue; // 第二阶段：分段续写
 }
}
```

两阶段恢复。第一次截断：通过 `MaxTokensSetter` 接口把 `max_output_tokens` 提升到 64000，注入续写指令，重试。第二阶段：最多再重试 3 次，每次告诉 LLM 把工作拆小。

`this.client as Partial<MaxTokensSetter>` 是一个安全的类型转换：用可选链 `setter.setMaxOutputTokens?.()` 调用，如果客户端不支持这个接口也不会报错。

## Plan Mode

```plain
if (this.checker.mode === "plan") {
 const planPath = getOrCreatePlanPath(this.workDir);
 this.checker.planFilePath = planPath;
 this.conversation.addSystemReminder(
 buildPlanModeReminder(
 planPath, planExists(this.workDir), iteration));
}
```

不改变循环结构，只在每轮注入 system-reminder。Plan 文件路径同步到权限检查器，让写 Plan 文件成为例外。

活跃 Skill 的 SOP 也在同一位置注入：

```plain
const skillReminder = buildActiveSkillsReminder(
 this.activeSkills);
if (skillReminder) {
 this.conversation.addSystemReminder(skillReminder);
}
```

`buildActiveSkillsReminder` 把所有激活的 Skill SOP 拼成一段文本，每轮重新注入，确保模型在长对话中始终能看到。

双层保障：提示词引导 LLM 自觉只做探索和规划，权限系统兜底拦截不听话的写操作。Plan 文件路径自动放行。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 异步事件流 | `async *run()` AsyncGenerator， `yield` 逐个发射 |
| 主循环 | `while(looping)` + `return` / `looping = false` 退出 |
| 事件类型 | discriminated union， `type` 字段区分 |
| 工具并行 | `StreamingExecutor` + `Promise.all` 并行执行 |
| 权限交互 | `onPermissionRequest` 回调函数， `await` 等待用户回应 |
| Plan Mode | 注入 system-reminder + 权限层拦截 |
| 上下文保护 | 工具输出截断（10000 字符上限）后再写入对话 |
| 错误恢复 | 上下文过长触发 forceCompact + 限流可中断睡眠等待 |
| 输出截断恢复 | 两阶段：先提升上限到 64000，再分段续写（最多 3 次） |
| 取消机制 | 标准 `AbortSignal` ，多个检查点检测，支持中断睡眠 |
| 依赖注入 | 构造函数接收 `AgentConfig` ，所有依赖显式传入 |
| 生命周期 | `fireLifecycle()` 在关键节点触发 Hook 事件 |

> 更新: 2026-06-08 13:16:15  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/psh3uk2nc3apfa2d](https://www.yuque.com/tianming-uvfnu/gmmfad/psh3uk2nc3apfa2d)