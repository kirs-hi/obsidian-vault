# 源码分析：Tool 和 MCP 代码实战\(Java\)

# 前言

在《Tool 与 MCP 设计思路》一节中我们提到了几个工具，那么这一节我们就来手把手的写2个工具，并交给大模型使用。

核心代码目录：src/main/java/org/example/agent/tool

# 当前时间查询工具

按照ai框架的规范用@Tool来表示工具：

- 第一个参数是 toolName ，用于表示工具名

- 第二个参数是 toolDesc ，用于告诉大模型这个工具的功能

```Java

```

# 腾讯云日志MCP工具

通过 MCP Server 查询日志服务 CLS 中存储的日志数据，以实现大模型平台/工具与日志数据的结合。例如使用自然语言查询日志，降低日志查询复杂度 https://cloud\.tencent\.com/developer/mcp/server/11710

MCP配置： [【飞书文档】环境准备教程](https://my.feishu.cn/https%3A%2F%2Fmy.feishu.cn%2Fwiki%2FOwlIwVXjXiL4o1k7nnFcWQ2wnHb)

Java代码的MCP使用了Spring AI的能力。（ QueryLogsTools ，它只是本地模拟工具，不是真实的MCP）

也就是说：

1. 业务代码没有 new McpClient\(\.\.\.\)

1. MCP Client 是由 Spring AI 自动配置创建的

1. 触发自动配置的是 pom\.xml 里的依赖：

```Java

```

实际链路是：

```Java

```

getToolCallbacks\(\) 这里没有创建 MCP Client。它只是使用 Spring 容器里已经自动创建好的 Bean：

```Java

```
