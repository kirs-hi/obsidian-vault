# TypeScript源码解析：LLM 客户端与流式响应

理论篇讲了 LLM 通信协议和两层消息模型的设计，这篇带你走读 MewCode 的 LLM 通信代码，看看「客户端封装 → 流式处理 → 对话管理」这条主线怎么实现。

## 模块概览

LLM 通信代码分布在两个目录下，一共七个文件：

| 文件 | 职责 |
| --- | --- |
| `src/llm/client.ts` | LLMClient 接口定义、createClient 工厂函数 |
| `src/llm/events.ts` | StreamEvent 联合类型和 UsageInfo 接口 |
| `src/llm/errors.ts` | 5 种错误类 |
| `src/llm/anthropic.ts` | Anthropic SDK 客户端、消息构建、错误分类 |
| `src/llm/openai.ts` | OpenAI Responses + Chat Completions 两个客户端 |
| `src/llm/model-resolver.ts` | 模型别名解析 |
| `src/conversation/conversation.ts` | Message 接口、ConversationManager 类 |

设计目标是屏蔽供应商差异，对上层暴露统一的流式事件接口。

## 核心类型

### LLMClient 接口

接口只有一个方法：

```plain
export interface LLMClient {
 stream(
 conv: ConversationManager,
 tools: Record<string, unknown>[],
 abortSignal?: AbortSignal
 ): AsyncGenerator<StreamEvent>;
}
```

返回 `AsyncGenerator<StreamEvent>` ，调用方用 `for await (const event of stream)` 消费。这是 TypeScript 异步迭代器的惯用模式，配合 `async function*` 使用。

注意第三个参数 `abortSignal` ，这是 Web 标准的取消机制。用户按 Ctrl+C 时，通过 `AbortController.abort()` 中断请求，信号传到 SDK 内部终止 HTTP 连接。

### StreamEvent：流式事件族

TypeScript 用 discriminated union（可辨识联合）定义事件类型，这是 TS 的特色：

```plain
export type StreamEvent =
 | { type: "text_delta"; text: string }
 | { type: "thinking_delta"; text: string }
 | { type: "thinking_complete"; thinking: string; signature: string }
 | { type: "tool_call_start"; toolName: string; toolId: string }
 | { type: "tool_call_delta"; text: string }
 | { type: "tool_call_complete"; toolId: string; toolName: string;
 arguments: Record<string, unknown> }
 | { type: "stream_end"; stopReason: string; usage: UsageInfo };
```

每个分支都有一个 `type` 字段做区分。 `switch (event.type)` 时 TypeScript 编译器能做穷尽检查，漏了任何一个 case 都会报类型错误。联合类型的判别式联合（discriminated union）在编译期就能保证类型安全。

`UsageInfo` 是单独的接口，包含四个 token 计数：

```plain
export interface UsageInfo {
 inputTokens: number;
 outputTokens: number;
 cacheReadInputTokens: number;
 cacheCreationInputTokens: number;
}
```

### Message 与 ConversationManager

消息结构用 interface 定义：

```plain
export interface Message {
 role: "user" | "assistant" | "system";
 content: string;
 thinkingBlocks?: ThinkingBlock[];
 toolUses?: ToolUseBlock[];
 toolResults?: ToolResultBlock[];
}
```

`role` 用字符串字面量联合类型约束，只能是三个值之一。 `thinkingBlocks` 、 `toolUses` 、 `toolResults` 都是可选的，用 `?` 标记。

辅助类型也用 interface：

```plain
export interface ThinkingBlock {
 thinking: string;
 signature: string;
}
export interface ToolUseBlock {
 toolUseId: string;
 toolName: string;
 arguments: Record<string, unknown>;
}
export interface ToolResultBlock {
 toolUseId: string;
 content: string;
 isError: boolean;
}
```

`ConversationManager` 是一个 class，内部用 `Message[]` 数组管理历史：

```plain
export class ConversationManager {
 private history: Message[] = [];

 addAssistantFull(
 text: string,
 thinking: ThinkingBlock[],
 toolUses: ToolUseBlock[]
 ): void {
 this.history.push({
 role: "assistant", content: text,
 thinkingBlocks: thinking.length > 0 ? thinking : undefined,
 toolUses: toolUses.length > 0 ? toolUses : undefined,
 });
 }
```

`getMessages()` 返回数组展开拷贝 `[...this.history]` 。空数组不存储为 `undefined` ，避免序列化时产生多余字段。Manager 不负责序列化，格式转换在各客户端文件里的 `build*` 函数里。

## 主流程走读

### 第一步：工厂创建客户端

`createClient` 是异步工厂函数，根据 protocol 动态 import 对应模块：

```plain
export async function createClient(
 cfg: ProviderConfig, systemPrompt: string
): Promise<LLMClient> {
 switch (cfg.protocol) {
 case "anthropic": {
 const { AnthropicClient } = await import("./anthropic.js");
 return new AnthropicClient(cfg, systemPrompt);
 }
 case "openai": {
 const { OpenAIClient } = await import("./openai.js");
 return new OpenAIClient(cfg, systemPrompt);
 }
 case "openai-compat": {
 const { OpenAICompatClient } = await import("./openai.js");
 return new OpenAICompatClient(cfg, systemPrompt);
 }
 }
}
```

动态 import 的好处是按需加载。如果用户用的是 Anthropic，就不会加载 OpenAI SDK 的代码，减少启动时间和内存占用。

### 第二步：构建请求参数

以 Anthropic 为例，参数对象直接构造：

```plain
const params: Anthropic.MessageCreateParamsStreaming = {
 model: this.model,
 max_tokens: this.maxOutputTokens,
 stream: true,
 system: [{
 type: "text",
 text: this.systemPrompt,
 cache_control: { type: "ephemeral" },
 }],
 messages,
 ...(tools.length > 0 ? { tools } : {}),
};
```

system prompt 标记了 `cache_control` ，是 Anthropic 的 prompt cache 机制。tool schema 的最后一个也标记了缓存控制，因为工具定义在多轮对话间基本不变。

thinking 配置分两种模式。 `supportsAdaptiveThinking` 判断模型版本：

```plain
function supportsAdaptiveThinking(model: string): boolean {
 for (const family of ["claude-opus-4-", "claude-sonnet-4-"]) {
 if (model.startsWith(family)) {
 const rest = model.slice(family.length);
 if (rest.length > 0 && rest[0] >= "6" && rest[0] <= "9") {
 return true;
 }
 }
 }
 return false;
}
```

用前缀匹配 + 版本号检查，因为模型 ID 后缀会变化。

### 第三步：流式迭代

SDK 的 `stream` 方法返回一个 async iterable，用 `for await` 消费：

```plain
const response = this.client.messages.stream(params, {
 ...(abortSignal ? { signal: abortSignal } : {}),
});

for await (const event of response) {
 switch (event.type) {
 case "content_block_start": {
 const block = event.content_block;
 if (block.type === "thinking") {
 inThinking = true;
 } else if (block.type === "tool_use") {
 currentToolName = block.name;
 yield { type: "tool_call_start", ... };
 }
 break;
 }
 case "content_block_delta": {
 // ...分派 delta...
 }
 }
}
```

`abortSignal` 通过 SDK options 传入，用户取消时中断 HTTP 连接。 `for await` 循环在流结束或信号触发后自动退出。

整个方法是 `async function*` （async generator），每个 `yield` 都是一次事件产出。async generator 天然支持背压：消费者不调用 `.next()` 的时候，生产者暂停在 `yield` 点。

### 第四步：事件消费

Agent Loop 用 `for await` 加 switch 消费：

```plain
for await (const event of client.stream(conv, tools)) {
 switch (event.type) {
 case "text_delta":
 // event.text 直接可用，TS 自动窄化
 break;
 case "tool_call_complete":
 // event.arguments 直接可用
 break;
 case "stream_end":
 // event.usage 直接可用
 break;
 }
}
```

discriminated union 的好处在这里体现： `switch` 里每个 case 分支内，TypeScript 自动把 `event` 窄化为对应的类型，不需要手动类型断言。

## 两层消息模型

### 内层：统一消息结构

`Message` interface + 三个辅助 interface 构成 provider 无关的内层。用 `Record<string, unknown>` 而非 `any` 表达工具参数，保留了一定的类型约束。

### 外层：序列化到 API 格式

\*\*Anthropic 序列化 \*\*在 `anthropic.ts` 的 `buildAnthropicMessages` 里。assistant 消息按 thinking → text → tool\_use 顺序组装 content block：

```plain
if (m.thinkingBlocks) {
 for (const tb of m.thinkingBlocks) {
 blocks.push({
 type: "thinking",
 thinking: tb.thinking,
 signature: tb.signature,
 });
 }
}
if (m.content) {
 blocks.push({ type: "text", text: m.content });
}
```

签名字段原样保留。空 assistant 消息兜底插空文本块。

连续 user 文本消息的合并逻辑避免了 Anthropic API 的交替限制。合并时会检查前一条 user 消息的第一个 content block 是否为 `tool_result` ，是的话不合并：

```plain
if (
 prev.role === "user" &&
 Array.isArray(prev.content) &&
 (prev.content[0] as Record<string, unknown>).type
 !== "tool_result"
) {
 canMerge = true;
}
```

合并后追加一个 `TextBlockParam` ，而非拼接字符串。

\*\*OpenAI Responses API 序列化 \*\*在 `openai.ts` 的 `buildOpenAIInput` 里。扁平列表， `function_call` 和 `function_call_output` 作为独立条目：

```plain
for (const tu of m.toolUses) {
 result.push({
 type: "function_call",
 name: tu.toolName,
 call_id: tu.toolUseId,
 arguments: JSON.stringify(tu.arguments),
 });
}
```

参数用 `JSON.stringify` 序列化为字符串。

\*\*Chat Completions 序列化 \*\*在 `openai.ts` 的 `buildChatCompletionMessages` 里。thinking 块跳过，工具结果用 role 为 `tool` 的消息。工具调用放在 `tool_calls` 数组里，参数也是 JSON 字符串。

## 流式响应处理

### 生产者-消费者模型

TypeScript 用 async generator 实现生产者-消费者。 `yield` 就是生产， `for await` 就是消费。不需要显式的队列，背压由 async generator 协议自动处理。

错误通过异常传播。 `try/catch` 捕获 SDK 异常后调用 `classifyAnthropicError` 转换，直接 `throw` ，消费者在 `for await` 外层 catch。

### 工具调用的 JSON 累积

参数片段用字符串累积：

```plain
case "content_block_delta": {
 const delta = event.delta;
 if (delta.type === "input_json_delta") {
 jsonAccum += delta.partial_json;
 yield { type: "tool_call_delta", text: delta.partial_json };
 }
}
```

block 结束时用 `JSON.parse` 解析， `catch` 里给空对象：

```plain
let args: Record<string, unknown> = {};
if (jsonAccum) {
 try { args = JSON.parse(jsonAccum); }
 catch { args = {}; }
}
yield { type: "tool_call_complete", ... };
```

### Thinking 的累积与签名

思考增量实时 yield 给 UI。签名在 `signature_delta` 事件中到达。block 结束时发出 `thinking_complete` ：

```plain
yield {
 type: "thinking_complete",
 thinking: thinkingAccum,
 signature: thinkingSignature,
};
```

签名在下一轮请求中原样回传给 API，验证思考块未被篡改。

### 连接保活与超时

依赖 SDK 的内置超时机制。 `AbortSignal` 是标准的取消 API，用户按 Ctrl+C 时触发 abort，SDK 底层的 `fetch` 调用立即中断。

Anthropic SDK 的 `stream` 方法本身管理连接生命周期， `for await` 循环结束后（不管是正常结束还是异常退出），连接自动关闭。

## 错误分类

用 class 层级表达错误分类：

```plain
export class LLMError extends Error {}
export class AuthenticationError extends LLMError {}
export class RateLimitError extends LLMError {
 retryAfter?: string;
}
export class NetworkError extends LLMError {}
export class ContextTooLongError extends LLMError {}
```

| 错误类型 | 触发条件 | 上层处理 |
| --- | --- | --- |
| `AuthenticationError` | 401 / API key 无效 | 提示检查配置 |
| `RateLimitError` | 429 / 限流 | 等待 retryAfter 后重试 |
| `ContextTooLongError` | 413 / prompt too long | 触发上下文压缩 |
| `NetworkError` | 非 API 错误 | 提示网络问题 |
| `LLMError` | 其他 API 错误 | 通用错误展示 |

Anthropic 的 `classifyAnthropicError` 通过 `instanceof Anthropic.APIError` 判断，按 HTTP 状态码分流：

```plain
function classifyAnthropicError(err: unknown): Error {
 if (err instanceof Anthropic.APIError) {
 if (err.status === 413 ||
 err.message?.includes("prompt is too long")) {
 return new ContextTooLongError(...);
 }
 if (err.status === 401)
 return new AuthenticationError(...);
 if (err.status === 429) {
 const retryAfter = (err.headers as Record<string, string>)
 ?.["retry-after"];
 return new RateLimitError(..., retryAfter);
 }
 return new LLMError(...);
 }
 return new NetworkError(...);
}
```

OpenAI 的 `classifyOpenAIError` 结构一样，匹配 `OpenAI.APIError` 。两个函数输出统一到同一组错误类型，上层不需要区分来源。

`containsContextLengthError` 是一个辅助函数，通过子串匹配判断上下文过长：

```plain
function containsContextLengthError(msg: string): boolean {
 const lower = msg.toLowerCase();
 return lower.includes("context_length_exceeded") ||
 lower.includes("maximum context length") ||
 lower.includes("prompt is too long");
}
```

## 模型解析与能力探测

别名映射是一个简单的对象：

```plain
const MODEL_ALIASES: Record<string, string> = {
 haiku: "claude-haiku-4-5-20251001",
 sonnet: "claude-sonnet-4-6-20250514",
 opus: "claude-opus-4-6-20250514",
};

export function resolveModelId(shortName: string): string {
 return MODEL_ALIASES[shortName] ?? shortName;
}
```

不认识的名字直接透传，用 `??` （空值合并）兜底。

`createModelResolver` 返回一个闭包，复用 base config 但替换 model 字段：

```plain
export function createModelResolver(
 baseCfg: ProviderConfig, systemPrompt: string
): (shortName: string) => Promise<LLMClient> {
 return (shortName: string) =>
 createClient(
 { ...baseCfg, model: resolveModelId(shortName) },
 systemPrompt);
}
```

`{ ...baseCfg, model: ... }` 用 spread 创建新对象，不会修改原 config。这个 resolver 用于子 Agent 场景，让不同 Agent 可以使用不同的模型但共享同一个 provider 配置。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 供应商抽象 | `LLMClient` 接口 + 异步工厂函数（动态 import） |
| 流式响应 | async generator， `yield` 生产 `for await` 消费 |
| 事件类型 | discriminated union， `type` 字段做穷尽检查 |
| 消息模型 | `Message` interface，可选的 thinking / toolUses / toolResults |
| 序列化 | 三套 `build*` 函数：Anthropic / OpenAI Responses / Chat Completions |
| 消息交替 | `buildAnthropicMessages` 合并连续 user 文本 block |
| 错误分类 | 5 种 Error 子类，两套 classify 统一映射 |
| 模型别名 | `MODEL_ALIASES` 对象 + `resolveModelId` 透传 |

> 更新: 2026-06-08 12:43:02  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/ziri81wigel0by14](https://www.yuque.com/tianming-uvfnu/gmmfad/ziri81wigel0by14)