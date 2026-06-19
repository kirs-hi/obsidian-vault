# 实战演练：API接口与Agent的整合

项目使用goframe作为web框架，如果想了解API定义到提供服务的流程，先看：

# 对话接口的定义

## 快速对话接口

与大模型对话，相同Id的对话带有上下文记忆功能

**请求方法 **: POST /api/chat

**请求字段:**

| 字段名​ | 类型​ | 描述​ |
| --- | --- | --- |
| Id​ | string​ | 对话的唯一标识​ |
| Question​ | string​ | 用户提问​ |

**响应字段:**

| 字段名​ | 类型​ | 描述​ |
| --- | --- | --- |
| Answer​ | string​ | 系统回答​ |

**示例：**

## 流式对话接口

与大模型对话，相同Id的对话带有上下文记忆功能，通过SSE实现流式输出回答

**请求方法 **: POST /api/chat\_stream

**请求字段:**

| 字段名​ | 类型​ | 描述​ |
| --- | --- | --- |
| Id​ | string​ | 对话的唯一标识​ |
| Question​ | string​ | 用户提问​ |

**响应字段:**

| 字段名​ | 类型​ | 描述​ |
| --- | --- | --- |
| ​ | ​ | ​ |

**SSE响应格式：**

| event类型​ | 含义​ |
| --- | --- |
| connected​ | 代表连接建立成功​ |
| message​ | 回复的文本片段，会多次发送​ |
| error​ | 连接异常，断开连接​ |
| done​ | 消息推送完毕，断开连接​ |

示例：

```YAML

```

# 快速对话接口的核心实现\(Go\)

代码路径： SuperBizAgent/internal/controller/chat/chat\_v1\_chat\.go

1. 根据用户id查询历史对话，并构造用户消息结构体

1. 创建对话Agent的执行器

1. 执行对话Agent，获得大模型的返回消息

1. 将本轮对话的问题和答案存入记忆系统中

1. 构造结构体，返回消息

```Go

```

# 流式对话接口的核心实现\(Go\)

sse返回的消息event类型：​

| event类型​ | 含义​ |
| --- | --- |
| connected​ | 代表连接建立成功​ |
| message​ | 回复的文本片段，会多次发送​ |
| error​ | 连接异常，断开连接​ |
| done​ | 消息推送完毕，断开连接​ |

1. 流式对话的核心是sse，首先我们创建sse客户端

1. 然后agent我们使用流式输出模式

1. 最后每次我们从流中读到内容，就通过see发送给用户

```Go

```

SSE客户端创建也很简单，就是按照SSE协议的要求，修改HTTP头部字段即可

```Go

```

# 快速对话接口的核心实现\(Java\)

1. 根据用户id查询历史对话

1. 构造prompt

1. 创建ReActAgent并执行

1. 将本轮的问答存入历史对话中

```Java

```

# 流式对话接口的核心实现\(Java\)

sse返回的消息event类型：​

| event类型​ | 含义​ |
| --- | --- |
| connected​ | 代表连接建立成功​ |
| message​ | 回复的文本片段，会多次发送​ |
| error​ | 连接异常，断开连接​ |
| done​ | 消息推送完毕，断开连接​ |

1. 流式对话的核心是SSE，首先我们创建sse客户端

1. 然后agent我们使用流式输出模式

1. 最后每次从流中读到内容，就通过sse发送给用户

```Java

```

# 快速对话接口的核心实现\(Python\)

代码路径：app/api/chat\.py 和 app/services/rag\_agent\_service\.py

1. 接收请求，取出 id（session\_id）和 question

1. 调用 rag\_agent\_service\.query 执行 Agent 推理，thread\_id 即 session\_id

1. LangGraph MemorySaver 自动完成历史消息的读取与写入，无需手动管理

1. 返回答案

```Python

```

query 方法内部将系统提示 \+ 用户问题包装成消息列表，通过 agent\.ainvoke 执行完整的 ReAct 推理链，并从最后一条消息中取出答案。 thread\_id 与 MemorySaver 配合，让相同 id 的请求自动携带历史上下文：

```Python

```

会话历史的消息裁剪由 trim\_messages\_middleware 节点负责，策略是保留第一条系统消息 \+ 最近 6 条消息（约 3 轮对话），防止多轮对话超出大模型的上下文窗口：

```Python

```

# 流式对话接口的核心实现\(Python\)

SSE 返回的消息 event 类型：

| event 类型 | 含义 |
| --- | --- |
| message \(type\=content\) | 回复的文本片段，会多次发送 |
| message \(type\=tool\_call\) | 工具调用状态通知 |
| message \(type\=done\) | 消息推送完毕 |
| message \(type\=error\) | 发生异常 |

1. 流式对话的核心是 SSE，FastAPI 通过 EventSourceResponse 实现，无需手动设置 HTTP 头

1. Agent 使用 agent\.astream 的 stream\_mode\="messages" 模式，逐 token 产生输出

1. 每次从流中读到文本内容，就通过 SSE 发送给客户端

```Python

```

query\_stream 方法使用 agent\.astream 的 stream\_mode\="messages" 模式，每个 token 触发一次回调，从 content\_blocks 中提取文本块后 yield 给上层：

```Python

```

# TODO挑战

流式对话代码里预留的两个Todo给有能力的同学实现。只要你把下面两个Todo实现了，说明这个项目你已经完成搞明白了：

1. Go语言代码熟悉：流式对话接口里面没有增加记忆功能，可以参考对话接口的记忆功能来实现，代码是可复用的。

1. 总结Agent实战：现在的记忆设计是放到先进先出的队列里面。其实我们可以考虑对前面的对话进行总结，压缩\(避免多轮对话导致超过大模型的上下文窗口\)。你可以尝试实现一个“总结对话Agent”，输入就是历史对话，输出就是大模型的总结内容，那么在对话超过5轮的时候， 就调用总结对话Agent ，把前5轮的历史对话替换成总结内容。
