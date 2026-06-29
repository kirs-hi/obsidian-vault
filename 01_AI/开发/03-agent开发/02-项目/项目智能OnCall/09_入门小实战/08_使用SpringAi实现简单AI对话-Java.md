# 使用SpingAi框架3分钟实现一个简单AI对话\(Java\)

# Spring AI Alibaba —— 小试牛刀

对于没有编程基础的同学，直接看b站视频学习： https://www\.bilibili\.com/video/BV1eyWbzEEnw

对于有编程基础的同学，请看官方文档学习：

1. https://java2ai\.com/

1. https://github\.com/spring\-ai\-alibaba/examples/blob/main/spring\-ai\-alibaba\-helloworld/README\.md

Spring AI Alibaba 是基于 Spring AI 框架对阿里云百炼大模型服务的集成实现。它让 Java 开发者能够以极简的方式接入大模型，就像写一个普通的 Spring Boot 接口一样简单。

下面我们通过一个最简单的对话接口，带你快速上手。

# 1\. 创建项目 & 引入依赖

使用 Maven 创建一个 Spring Boot 项目，在 pom\.xml 中添加以下关键依赖：

```XML

```

# 2\. 配置 API Key 和模型

在 src/main/resources/application\.properties 中添加配置：

```Plaintext

```

> **API Key 获取方式 **：前往 [阿里云百炼控制台 ](https://my.feishu.cn/https%3A%2F%2Fbailian.console.aliyun.com%2F)创建 API Key，替换上面的占位符即可。

# 3\. 编写启动类

标准的 Spring Boot 启动类，没有任何特殊配置：

```Java

```

# 4\. 定义请求 & 响应模型

**ChatRequest **—— 接收用户提问：

```Java

```

**ChatResponse **—— 封装模型回答：

```Java

```

**Result **—— 统一响应包装：

```Java

```

# 5\. 编写对话接口（核心）

这是整个项目最核心的部分，也是 Spring AI Alibaba 真正展现威力的地方—— **只需 3 行代码就能完成一次大模型对话 **：

```Java

```

### 关键代码解析

| 代码 | 说明 |
| --- | --- |
| ChatClient\.Builder | Spring AI 自动注入的构建器，框架根据 application\.properties 的配置自动创建对应的大模型客户端 |
| chatClientBuilder\.build\(\) | 构建 ChatClient 实例，后续所有对话都通过它发起 |
| chatClient\.prompt\(question\) | 将用户的问题作为 prompt 发送给大模型 |
| \.call\(\) | 同步调用大模型，等待返回结果 |
| \.content\(\) | 提取大模型返回的文本内容 |

整个调用链路一气呵成： **构造 prompt → 调用模型 → 提取回答 **，一行代码搞定。

# 6\. 启动 & 测试

启动应用后，打开浏览器或使用 curl 访问：

```Bash

```

返回结果示例：

```JSON

```
