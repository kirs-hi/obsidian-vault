# 源码分析：Tool 和 MCP 代码实战\(Python\)

# 前言

在《Tool 与 MCP 设计思路》一节中我们提到了几个工具，那么这一节我们就来手把手的写2个工具，并交给大模型使用。

核心代码目录：app/tools

# 当前时间查询工具

@tool 会从函数本身自动推导元数据：

| 字段 | 来源 |
| --- | --- |
| name | 函数名 → get\_current\_time |
| description | 函数 docstring（三引号文档字符串） |
| 参数 schema | 类型注解 \+ docstring 里的 Args:（LangChain 会解析） |

实际跑起来就是：

```Java

```

想显式指定 name / description 时

```Python

```

```Python

```

# 腾讯云日志MCP工具

通过 MCP Server 查询日志服务 CLS 中存储的日志数据，以实现大模型平台/工具与日志数据的结合。例如使用自然语言查询日志，降低日志查询复杂度 https://cloud\.tencent\.com/developer/mcp/server/11710

MCP配置： [【飞书文档】环境准备教程](https://my.feishu.cn/https%3A%2F%2Fmy.feishu.cn%2Fwiki%2FOwlIwVXjXiL4o1k7nnFcWQ2wnHb)

首先我们创建一个 SSE MCP 客户端。创建后进行初始化，最后调用load\_mcp\_tools\_safe获取所有可用的工具即可。其中client\.get\_tools\(\)是langchain提供的api，只需要会调用即可。

```Python

```
