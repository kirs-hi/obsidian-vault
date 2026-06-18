---
title: "《AI大模型Ragent项目》——为什么MCP不使用HTTP或gRPC？"
source: "https://articles.zsxq.com/id_lcju88pl5tmq.html"
author:
  - "[[马丁]]"
published:
created: 2026-06-05
description:
tags:
  - "clippings"
---
[来自： 拿个offer-开源&项目实战](https://wx.zsxq.com/group/51121244585524)

## 问题的本质：MCP 要解决什么问题？

在讨论技术选型之前，我们需要先明确 MCP（Model Context Protocol）要解决的核心问题。

MCP 的目标是让大模型能够以 **统一、标准、可互操作** 的方式调用外部工具能力。这意味着：

- 不同语言实现的 MCP Server（Python、Java、Node.js）都能被同一个 MCP Client 调用

- 不同厂商的大模型（OpenAI、Anthropic、本地模型）都能用相同方式调用工具

- 工具的调用方式应该是明确、可预测的，而不是各自为政

要实现这个目标，MCP 需要的不是如何传输数据，而是如何表达一次调用。

## HTTP、gRPC 和 JSON-RPC 2.0 的定位差异

### 1\. HTTP：传输协议，不是调用协议

HTTP 是一个 **传输层协议** ，它定义了：

- 如何建立连接（TCP/TLS）

- 如何发送请求（GET、POST、PUT、DELETE）

但 HTTP **不定义** ：

- 方法名怎么表示？（是放在 URL 路径？还是 Body 里？）

- 参数怎么传递？（Query String？JSON Body？Form Data？）

- 错误怎么表达？（HTTP 状态码？还是 Body 里的错误对象？）

- 通知消息（不需要响应的调用）怎么处理？

这导致基于 HTTP 的 API 设计千差万别：

- RESTful API： `POST /users` 、 `GET /users/123`

- RPC-style API： `POST /api` + `{"method": "getUser", "params": {...}}`

- GraphQL： `POST /graphql` + Query DSL

每种风格都有自己的约定， **缺乏统一标准** 。

### 2\. gRPC：强类型 RPC 框架，但过于重量级

gRPC 是一个完整的 RPC 框架，它提供了：

- 基于 Protocol Buffers 的强类型接口定义

- HTTP/2 传输层

- 流式调用支持

- 多语言代码生成

gRPC 的优势在于 **性能和类型安全** ，但它也带来了额外的复杂度：

- 1.
	**需要预先定义.proto 文件** ：每个工具都要写 Protocol Buffers 定义，增加了开发成本

- 2.
	**强依赖代码生成** ：客户端和服务端都需要生成代码，动态调用不方便

- 3.
	**二进制协议不易调试** ：无法直接用 curl 或浏览器测试，必须用专门工具

- 4.
	**HTTP/2 依赖** ：部分环境（如浏览器、某些代理）对 HTTP/2 支持不完善

对于 MCP 这种需要 **轻量、灵活、易于调试** 的场景，gRPC 显得过于重量级。

### 3\. JSON-RPC 2.0：协议层标准，专注消息格式

JSON-RPC 2.0 的定位与 HTTP、gRPC 都不同，它是一个 **消息格式规范** ，只定义：

- 一次调用的请求结构： `{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}`

- 成功响应的结构： `{"jsonrpc": "2.0", "result": {...}, "id": 1}`

- 错误响应的结构： `{"jsonrpc": "2.0", "error": {...}, "id": 1}`

- 通知消息的结构： `{"jsonrpc": "2.0", "method": "...", "params": {...}}` （无 `id` ）

它 **不绑定传输层** ，可以跑在：

- HTTP 之上（最常见）

- WebSocket 之上（实时通信）

- stdio 之上（进程间通信）

- 任何能传输 JSON 的通道

## MCP 选择 JSON-RPC 2.0 的核心原因

### 1\. 统一的消息格式

JSON-RPC 2.0 提供了一套 **明确、标准、无歧义** 的消息结构：

```
// 请求
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {"city": "Beijing"}
  },
  "id": 1
}

// 成功响应
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "北京今天晴，25°C"}]
  },
  "id": 1
}

// 错误响应
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "city is required"
  },
  "id": 1
}
```

无论是 Python 实现的 MCP Server，还是 Java 实现的 MCP Client，都能按照 **完全相同的方式** 解析和构造消息。

### 2\. 轻量且易于实现

JSON-RPC 2.0 的规范非常简洁（完整规范只有几页），核心概念只有 4 个：

- Request Object

- Response Object

- Notification

- Error Object

任何语言只需要：

- 1.
	能解析 JSON

- 2.
	能构造 JSON

- 3.
	理解 4 种消息结构

就能实现一个完整的 JSON-RPC 2.0 客户端或服务端。不需要代码生成、不需要复杂的框架、不需要学习新的 IDL。

### 3\. 人类可读，易于调试

JSON-RPC 2.0 使用纯文本 JSON 格式，可以直接：

- 用 `curl` 测试： `curl -X POST http://localhost:3000 -d '{"jsonrpc":"2.0","method":"ping","id":1}'`

- 在浏览器 DevTools 中查看请求和响应

- 用任何文本编辑器编辑和调试

- 在日志中直接阅读，无需反序列化

相比之下，gRPC 的 Protocol Buffers 是二进制格式，必须用专门工具才能查看。

### 4\. 传输层无关，灵活性高

MCP 的使用场景多样：

- **本地工具调用** ：大模型通过 stdio 调用本地进程（如 Python 脚本）

- **远程工具调用** ：大模型通过 HTTP 调用远程服务

- **实时通信** ：大模型通过 WebSocket 与工具保持长连接

JSON-RPC 2.0 不绑定传输层，可以适配所有这些场景。而 gRPC 强依赖 HTTP/2，无法用于 stdio 场景。

### 5\. 支持通知消息（Notification）

MCP 中有些场景不需要响应，例如：

- 日志上报：工具向大模型发送日志，不需要等待确认

- 进度更新：工具向大模型报告任务进度，不需要响应

JSON-RPC 2.0 原生支持 Notification（不带 `id` 的请求），服务端不会返回响应，减少了不必要的网络开销。

HTTP 和 gRPC 都没有原生的单向消息概念，需要额外设计。

### 6\. 批量调用支持

JSON-RPC 2.0 支持 Batch Request，可以一次发送多个请求：

```
[
  {"jsonrpc": "2.0", "method": "tools/list", "id": 1},
  {"jsonrpc": "2.0", "method": "resources/list", "id": 2},
  {"jsonrpc": "2.0", "method": "prompts/list", "id": 3}
]
```

服务端可以并发处理，减少网络往返次数。这对于大模型一次性获取多个工具信息非常有用。

## JSON-RPC 2.0 的局限性

当然，JSON-RPC 2.0 也不是完美的，它有一些明确的局限性：

### 1\. 不包含传输层细节

JSON-RPC 2.0 只定义消息格式，不管：

- 如何建立连接（TCP？WebSocket？）

- 如何处理超时和重试

- 如何做负载均衡

- 如何做服务发现

这些需要在 MCP 的实现层或基础设施层补齐。

### 2\. 不包含鉴权机制

JSON-RPC 2.0 不定义如何鉴权，需要在传输层（如 HTTP Header）或应用层（如在 `params` 中加 `auth` 字段）自行实现。

### 3\. 不包含类型定义

JSON-RPC 2.0 不强制类型检查，参数和返回值都是动态的 JSON。这意味着：

- 需要在运行时校验参数类型

- 无法在编译期发现类型错误

- 需要额外的文档或 Schema 定义（如 JSON Schema）

MCP 通过在协议层定义 Schema（如工具的 `inputSchema` ）来弥补这一点。比如：

```
{
  "name": "get_weather",
  "description": "获取天气信息",
  "inputSchema": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "城市名称"
      }
    },
    "required": ["city"]
  }
}
```

### 4\. 性能不如二进制协议

JSON 是文本格式，序列化和反序列化开销比 Protocol Buffers 大。但对于 MCP 的使用场景（大模型调用工具），这点性能差异通常可以忽略。

## 总结：为什么是 JSON-RPC 2.0？

MCP 选择 JSON-RPC 2.0，本质上是在 **标准化、简单性、灵活性** 之间做了权衡：

| 维度 | HTTP | gRPC | JSON-RPC 2.0 |
| --- | --- | --- | --- |
| 定位 | 传输协议 | 完整 RPC 框架 | 消息格式规范 |
| 消息格式标准化 | ❌ 无统一标准 | ✅ Protocol Buffers | ✅ 统一 JSON 结构 |
| 实现复杂度 | ⚠️ 需自行设计消息格式 | ⚠️ 需.proto + 代码生成 | ✅ 简单，只需解析 JSON |
| 人类可读性 | ⚠️ 取决于设计 | ❌ 二进制格式 | ✅ 纯文本 JSON |
| 传输层灵活性 | ⚠️ 仅 HTTP | ❌ 强依赖 HTTP/2 | ✅ 传输层无关 |
| 通知消息支持 | ❌ 需自行设计 | ⚠️ 需用流式 API | ✅ 原生支持 Notification |
| 批量调用支持 | ❌ 需自行设计 | ⚠️ 需用流式 API | ✅ 原生支持 Batch |
| 类型安全 | ❌ 无 | ✅ 强类型 | ❌ 动态类型（需额外 Schema） |
| 性能 | ⚠️ 取决于实现 | ✅ 高性能 | ⚠️ JSON 序列化开销 |

对于 MCP 这种需要 **跨语言、跨环境、易于调试、快速迭代** 的协议，JSON-RPC 2.0 是最合适的选择。

它不是最快的（gRPC 更快），也不是最灵活的（HTTP 可以自由设计），但它是 **最标准、最简单、最容易互操作** 的。

这正是 MCP 需要的： **让不同实现之间能够无缝通信，而不是追求极致性能或极致灵活性** 。

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51121244585524

<!-- series-nav-start -->

---
**📚 项目rag_agent**（23/87）

⬅️ 上一篇：[[02基础补充_01MCP协议规范JSON-RPC 2.0标准说明]] | ➡️ 下一篇：[[02基础补充_03工具调用架构设计指南]]

<!-- series-nav-end -->
