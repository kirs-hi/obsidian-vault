# TypeScript源码解析：MCP 协议与工具适配

理论篇讲了 [[理论学习_MCP_协议与开放工具生态|MCP]] 协议如何把工具从「内置」变成「开放生态」，这篇带你走读 MewCode 的实际代码，看看「配置 → 连接 → 发现 → 调用」这条主线怎么用三个文件、两百行出头实现。

## 模块概览

MCP 模块的代码集中在 `src/mcp/` 目录下：

| 文件 | 职责 |
| --- | --- |
| `client.ts` | 单个 MCP Server 的连接器：选择传输层，完成握手，暴露 listTools 和 callTool |
| `manager.ts` | 多 Server 管理器：批量连接，汇总工具清单和错误信息 |
| `tool-wrapper.ts` | 适配层：把远程 MCP 工具包装成本地 Tool 接口 |

三个文件形成清晰的分层： `client` 负责和单个 Server 通信， `manager` 负责编排多个 `client` ， `tool-wrapper` 负责把远程工具「伪装」成本地工具。

依赖官方 `@modelcontextprotocol/sdk` ，SDK 提供了 `Client` 、 `StdioClientTransport` 、 `StreamableHTTPClientTransport` 、 `SSEClientTransport` 等类，传输层和握手细节不用手写。

## 核心类型

### MCPServerConfig：Server 连接配置

MCP Server 的配置定义在 `src/config/config.ts` 中：

```plain
export interface MCPServerConfig {
 name: string;
 command?: string;
 args?: string[];
 url?: string;
 transport?: string;
 headers?: Record<string, string>;
 env?: Record<string, string>;
}
```

`command` 和 `url` 二选一。填了 `command` 走 stdio，填了 `url` 走 HTTP 或 [[01基础_20SSE协议与流式响应|SSE]]。 `transport` 字段区分 HTTP 变体，只有写 `"sse"` 才走老版 SSE 传输，默认走 Streamable HTTP。

### MCPTool：工具描述

```plain
export interface MCPTool {
 name: string;
 description: string;
 inputSchema: Record<string, unknown>;
}
```

从 MCP Server 拿到的工具元信息。 `inputSchema` 是 JSON Schema 格式，描述工具接受什么参数。[[07-Agent|Agent]] 在给 LLM 发送工具列表时，会把 `inputSchema` 透传过去。

### MCPClient：单个 MCP 连接

```plain
export class MCPClient {
 name: string;
 private config: MCPServerConfig;
 private client: Client | null = null;
 private transport: AnyTransport | null = null;

 constructor(config: MCPServerConfig) {
 this.name = config.name;
 this.config = config;
 }
}
```

两个核心字段： `client` 是 SDK 提供的 MCP Client 实例， `transport` 是传输层实例。 `AnyTransport` 是联合类型，包含 `StdioClientTransport` 、 `StreamableHTTPClientTransport` 和 `SSEClientTransport` 三种。

### ConnectResult：连接汇总

```plain
export interface ConnectResult {
 tools: { serverName: string; tool: MCPTool }[];
 servers: string[];
 errors: { serverName: string; error: string }[];
 instructions: { serverName: string; text: string }[];
}
```

`MCPManager.connectAll()` 的返回值。四个数组分别收集：成功拿到的工具、连接成功的 Server 名、连接失败的错误、各 Server 的使用说明。调用方拿到后可以一次性处理所有成功和失败的情况。

### MCPToolWrapper：协议适配器

```plain
export class MCPToolWrapper implements Tool {
 name: string;
 description: string;
 category = "command" as const;

 private client: MCPClient;
 private originalName: string;
 private inputSchema: Record<string, unknown>;
}
```

三个核心字段： `client` 是底层连接引用， `originalName` 是 MCP 服务器定义的原始工具名， `inputSchema` 是参数定义。实现了 `Tool` 接口，注册到 `ToolRegistry` 后 Agent 完全感知不到这是个远程工具。

## 主流程走读

### 第一步：Connect，建连接

```plain
async connect(): Promise<void> {
 if (this.config.command) {
 // ... 构造 env，展开环境变量 ...
 this.transport = new StdioClientTransport({
 command: this.config.command, args: this.config.args ?? [],
 env, stderr: "ignore",
 });
 } else if (this.config.url) {
 // ... HTTP/SSE transport ...
 }
 this.client = new Client({ name: "mewcode", version: "0.1.0" }, {});
 await this.client.connect(this.transport);
}
```

先根据配置创建传输层，再声明身份 `{ name: "mewcode", version: "0.1.0" }` ，最后调 SDK 的 `connect()` 完成初始化握手。SDK 内部发送 `initialize` 请求和 `notifications/initialized` 通知，MewCode 不用手动处理这些协议细节。

连接成功后可以通过 `getInstructions()` 读取服务器返回的使用说明：

```plain
getInstructions(): string {
 return this.client?.getInstructions() ?? "";
}
```

### 第二步：ListTools，发现工具

```plain
async listTools(): Promise<MCPTool[]> {
 if (!this.client) throw new Error("Not connected");
 const result = await this.client.listTools();
 return (result.tools ?? []).map((t) => ({
 name: t.name,
 description: t.description ?? "",
 inputSchema: t.inputSchema as Record<string, unknown>,
 }));
}
```

SDK 发送 `tools/list` 请求。返回值做了一层映射，把 SDK 的类型转成 MewCode 内部的 `MCPTool` 接口，只保留需要的三个字段。

### 第三步：CallTool，执行工具

```plain
async callTool(
 name: string, args: Record<string, unknown>
): Promise<string> {
 if (!this.client) throw new Error("Not connected");
 const result = await this.client.callTool(
 { name, arguments: args });
 if (result.content && Array.isArray(result.content)) {
 return result.content
 .map((c: { type: string; text?: string }) =>
 c.type === "text" ? c.text ?? "" : JSON.stringify(c))
 .join("\n");
 }
 return JSON.stringify(result);
}
```

遍历 `content` 数组，文本类型取 `text` ，非文本类型序列化成 JSON 字符串。 `callTool` 直接返回拼接好的字符串，不单独返回 `isError` 标志。错误处理在 `MCPToolWrapper.execute()` 里通过 try-catch 完成。

## 传输层选择

### stdio 传输

```plain
this.transport = new StdioClientTransport({
 command: this.config.command,
 args: this.config.args ?? [],
 env,
 stderr: "ignore",
});
```

`StdioClientTransport` 启动子进程，通过 stdin/stdout 管道通信。环境变量先继承 `process.env` ，再覆盖配置里声明的值。 `stderr: "ignore"` 忽略子进程的 stderr 输出，避免调试日志污染界面。

### HTTP 传输（Streamable HTTP / SSE）

```plain
const url = new URL(this.config.url);
const headers: Record<string, string> = {};
if (this.config.headers) {
 for (const [k, v] of Object.entries(this.config.headers))
 headers[k] = expandEnv(v);
}
const opts = { requestInit: { headers } };
this.transport =
 this.config.transport === "sse"
 ? new SSEClientTransport(url, opts)
 : new StreamableHTTPClientTransport(url, opts);
```

`transport` 字段区分 HTTP 变体，默认走 `StreamableHTTPClientTransport` （Streamable HTTP），只有显式写 `"sse"` 才走 `SSEClientTransport` （老版 SSE）。自定义 Headers 通过 `requestInit.headers` 注入，header 值经过环境变量展开。

### 环境变量展开

```plain
function expandEnv(value: string): string {
 return value.replace(
 /\$\{(\w+)\}|\$(\w+)/g,
 (_, a, b) => process.env[a ?? b] ?? ""
 );
}
```

一行正则同时支持 `${VAR}` 和 `$VAR` 两种写法。这个函数在 stdio 模式的 `env` 和 HTTP 模式的 `headers` 中都会被调用。

### 传输层抽象

三种传输方式统一用 `AnyTransport` 联合类型表示， `connect()` 内部的 if-else 分支负责创建具体实例。创建完成后，上层的 `listTools()` 、 `callTool()` 完全不关心底层是什么传输。

## 工具适配器

### 名称包装

```plain
function sanitizeName(
 serverName: string, toolName: string
): string {
 const clean = (s: string) =>
 s.replace(/[^a-zA-Z0-9_-]/g, "_");
 return `mcp__${clean(serverName)}__${clean(toolName)}`;
}
```

名字格式 `mcp__<server>__<tool>` ，双下划线分隔。正则把非法字符替换成下划线，不过这里的正则多保留了连字符 `-` 。不同 Server 可能有同名工具，加前缀避免冲突。

### Schema 透传

```plain
schema(): Record<string, unknown> {
 return {
 name: this.name,
 description: this.description,
 input_schema: this.inputSchema,
 };
}
```

`inputSchema` 直接透传，不做转换。

### 执行桥接

```plain
async execute(
 args: Record<string, unknown>,
 _ctx: ToolContext
): Promise<ToolResult> {
 try {
 const output = await this.client.callTool(
 this.originalName, args);
 return { output, isError: false };
 } catch (err) {
 return {
 output: `MCP tool error: ${(err as Error).message}`,
 isError: true,
 };
 }
}
```

传给 `callTool` 的是 `this.originalName` （原始工具名），不是 `this.name` （带前缀的名字）。MCP 服务器只认自己定义的工具名。异常被 catch 住转成 `ToolResult` ，Agent 看到错误信息后自行决定怎么处理。

## 延迟加载：ToolSearch 与 DeferrableTool

的延迟加载通过 `Tool` 接口的 `deferred` 属性控制。 `getAllSchemas()` 构建每轮发给 LLM 的工具列表时，跳过标记为延迟且尚未被发现的工具：

```plain
for (const tool of this.tools.values()) {
 if (tool.deferred && !this.discovered.has(tool.name))
 continue;
 // ... 正常构建 schema ...
}
```

`getDeferredToolNames()` 返回未发现的延迟工具名称列表，[[理论学习_ReAct_范式与_Agent_Loop|Agent Loop]] 把这些名字注入 system-reminder。

LLM 需要某个延迟工具时，调用 ToolSearchTool。它支持两种查询模式：

```plain
if (query.startsWith("select:")) {
 const names = query.slice(7).split(",")
 .map((n) => n.trim());
 const tools = this.registry.findDeferredByNames(names);
 for (const t of tools) {
 this.registry.markDiscovered(t.name);
 }
 // ... 返回 schemas ...
}
```

`select:` 前缀走精确查找，按名称匹配并标记为已发现。不带前缀走关键词搜索：

```plain
searchDeferred(query: string, maxResults = 5): Tool[] {
 const lower = query.toLowerCase();
 const matches: Tool[] = [];
 for (const tool of this.tools.values()) {
 if (!tool.deferred || this.discovered.has(tool.name))
 continue;
 if (tool.name.toLowerCase().includes(lower) ||
 tool.description.toLowerCase().includes(lower)) {
 matches.push(tool);
 if (matches.length >= maxResults) break;
 }
 }
 return matches;
}
```

在名称和描述里做包含匹配，找到就加入，够数就停。简单高效。

`markDiscovered` 把工具名加入 `discovered` 集合，下一轮 `getAllSchemas()` 就会包含完整 schema。

ToolSearchTool 自身没有设置 `deferred = true` ，所以不会被延迟加载。

## 连接管理

### ConnectAll 启动时全量注册

```plain
async connectAll(configs: MCPServerConfig[]): Promise<ConnectResult> {
 for (const cfg of configs) {
 const client = new MCPClient(cfg);
 try {
 await client.connect();
 this.clients.set(cfg.name, client);
 const tools = await client.listTools();
 for (const tool of tools) result.tools.push({ serverName: cfg.name, tool });
 // 提取 instructions 注入 system reminder
 } catch (err) {
 result.errors.push({ serverName: cfg.name, error: ... });
 }
 }
 return result;
}
```

逐个创建 `MCPClient` ，连接、拉工具列表、提取 Instructions。一个 Server 失败不影响其他的。Instructions 会被注入到 system reminder 中，让 LLM 知道怎么用这些工具。

调用方拿到 `ConnectResult` 后，逐个包装注册：

```plain
for (const { serverName, tool } of result.tools) {
 const client = mgr.getClient(serverName);
 if (client) {
 registry.register(
 new MCPToolWrapper(client, serverName, tool));
 }
}
```

### 优雅关闭

```plain
async disconnectAll(): Promise<void> {
 for (const client of this.clients.values()) {
 await client.disconnect();
 }
 this.clients.clear();
}
```

遍历关闭所有客户端。 `disconnect()` 内部调 `client.close()` ，异常被 catch 住不抛出：

```plain
async disconnect(): Promise<void> {
 try {
 await this.client?.close();
 } catch {
 // ignore
 }
 this.client = null;
 this.transport = null;
}
```

关闭失败只是忽略，清空引用。因为这是退出前的清理阶段，一个连接关不掉不应该阻止其他连接的清理。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| SDK 依赖 | 官方 `@modelcontextprotocol/sdk` ，复用 Client 和三种 Transport |
| 传输层选择 | `command` → stdio， `url` → HTTP/SSE， `transport` 字段区分变体 |
| 初始化握手 | SDK `client.connect(transport)` 一次完成 |
| 环境变量 | `expandEnv` 一行正则支持 `${VAR}` 和 `$VAR` |
| 名称隔离 | `mcp__<server>__<tool>` ，正则清洗非法字符 |
| 延迟加载 | `deferred` 属性 + ToolSearch 精确/关键词查询 + `markDiscovered` 激活 |
| 连接缓存 | `Map<string, MCPClient>` 持有所有连接 |
| 容错 | 单个 Server 失败不阻断，错误统一收集到 `ConnectResult.errors` |
| Server 指引 | `getInstructions()` 获取使用说明，注入 system reminder |

> 更新: 2026-06-08 14:20:10  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/qiycg0irawgm3zpl](https://www.yuque.com/tianming-uvfnu/gmmfad/qiycg0irawgm3zpl)