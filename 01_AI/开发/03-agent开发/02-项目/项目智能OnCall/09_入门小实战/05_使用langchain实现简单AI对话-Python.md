# 使用langchain框架3分钟实现一个简单AI对话\(Python\)

# LangChain 是什么？

LangChain 是一个专为大语言模型（LLM）应用开发设计的开源框架。它提供了一套标准化的接口，让开发者能够轻松对接各种大模型（OpenAI、通义千问、DeepSeek 等），而无需关心底层 API 的差异。

简单来说，LangChain 之于 Python AI 开发，就像 Spring AI 之于 Java AI 开发—— **统一接口、屏蔽差异、开箱即用 **。

它的核心优势：

- **模型无关 **：同一套代码可以无缝切换不同的大模型，只需修改配置

- **生态丰富 **：内置对话记忆、RAG、Agent、工具调用等高级能力

- **兼容 OpenAI 协议 **：国内大多数模型（通义千问、DeepSeek 等）都提供了 OpenAI 兼容接口，LangChain 可以直接对接

下面我们通过一个最简单的对话接口，带你快速上手。

源码：使用 LangChain \+ FastAPI 实现一个 AI 对话接口

源码： [【飞书文档】项目源码下载 ](https://my.feishu.cn/https%3A%2F%2Ficnaxnmh86kx.feishu.cn%2Fwiki%2FUfYIwTsNKi6wopkYErTcfb8mnTc)使用langchain实现一个ai对话接口

# 创建项目 & 安装依赖

创建一个项目目录，新建 requirements\.txt ，写入以下依赖：

```Plaintext

```

然后执行安装：

```Bash

```

三个依赖各司其职：

| 依赖 | 说明 |
| --- | --- |
| fastapi | 高性能 Python Web 框架，用于快速构建 HTTP 接口 |
| uvicorn | ASGI 服务器，负责启动和运行 FastAPI 应用 |
| langchain\-openai | LangChain 对 OpenAI 协议的封装，支持所有兼容 OpenAI 接口的模型 |

# 2\. 配置大模型

使用阿里云百炼（DashScope）提供的 OpenAI 兼容接口来接入通义千问模型。

API Key 获取方式：前往 [阿里云百炼控制台 ](https://my.feishu.cn/https%3A%2F%2Fbailian.console.aliyun.com%2F)创建 API Key。

在代码中配置模型时需要三个关键参数：

| 参数 | 说明 |
| --- | --- |
| api\_key | 你在百炼控制台获取的 API Key |
| base\_url | 百炼的 OpenAI 兼容地址： https://dashscope\.aliyuncs\.com/compatible\-mode/v1 |
| model | 使用的模型名称，这里选用 qwen3\-max |

# 3\. 编写对话接口（完整代码）

整个项目只需一个 main\.py 文件，代码如下：

```Python

```

没看错， **总共不到 20 行代码 **，就实现了一个完整的 AI 对话接口。

# 4\. 关键代码解析

| 代码 | 说明 |
| --- | --- |
| ChatOpenAI\(\.\.\.\) | 创建大模型客户端，通过 base\_url 指向百炼的 OpenAI 兼容接口，一行配置即可对接通义千问 |
| HumanMessage\(content\=question\) | 将用户的问题封装为 LangChain 标准的「用户消息」格式 |
| llm\.invoke\(\[\.\.\.\]\) | 同步调用大模型，传入消息列表，等待返回结果 |
| response\.content | 提取大模型返回的文本内容 |
| @app\.get\("/api/chat"\) | 使用 FastAPI 定义一个 GET 接口，通过查询参数接收用户提问 |

整个调用链路一气呵成： **封装消息 → 调用模型 → 提取回答 **，核心逻辑只需一行代码。

# 5\. 启动 & 测试

启动应用：

```Bash

```

参数说明：

- main:app ： main 是文件名， app 是 FastAPI 实例的变量名

- \-\-host 0\.0\.0\.0 ：允许外部访问

- \-\-port 8080 ：监听 8080 端口，与 Java 版本保持一致

启动成功后，打开浏览器或使用 curl 访问：

```Bash

```

返回结果示例：

```JSON

```

此外，FastAPI 还自带交互式 API 文档，启动后访问 http://localhost:8080/docs 即可在浏览器中直接测试接口，无需任何额外工具。
