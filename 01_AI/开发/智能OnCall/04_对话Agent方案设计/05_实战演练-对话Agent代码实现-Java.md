# 实战演练：对话Agent代码实现\(Java\)

# 前言

这部分代码在： SuperBizAgent/src/main/java/org/example/controller/ChatController\.java

![image\.png](../attachments/BUTDbvalGo50bVx6ogXcNo8Sneb.png)

# 流程梳理

对话Agent的核心目标是结合外部知识（RAG召回）与工具调用能力（ReAct模式），解决复杂问题。

整体流程可概括为：​

1. 用户输入 \-\> embedding \-\> 向量数据库召回

1. 构建带上下文\(召回的内容\)的 prompt

1. ReAct模式多轮交互

1. 最终输出答案

# 实战

## 消息召回

这里留一个预召回的TODO给同学完成，代码实现非常简单，在召回实战章节其实已有介绍\(searchSimilarDocuments\)

## 构建prompt

```TypeScript

```

## 创建ReAct Agent

因为我们这里使用了Spring AI alibaba框架，所以不需要我们自己从0到1去实现，只需要按照sdk的要求使用，即可返回给我们一个可以执行的Agent

API使用文档： [https://java2ai\.com/docs/frameworks/agent\-framework/tutorials/agents](https://my.feishu.cn/https%3A%2F%2Fjava2ai.com%2Fdocs%2Fframeworks%2Fagent-framework%2Ftutorials%2Fagents)

```JSON

```

# 执行ReAct Agent

```Java

```

# 总结

至此，对话Agent的核心流程RAG召回与ReAct模式的代码就讲完了。如果你一篇一篇看下来，会发现其实代码实现真的不难，而且也不重要，框架帮我们做了很多事情。 **核心是要搞懂我们的设计原理：RAG、ReAct。**
