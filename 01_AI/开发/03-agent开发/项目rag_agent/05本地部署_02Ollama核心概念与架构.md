---
title: "《AI大模型Ragent项目》——Ollama核心概念与架构"
source: "https://articles.zsxq.com/id_10a7mojh9bzw.html"
author:
  - "[[马丁]]"
published:
created: 2026-06-07
description:
tags:
  - "clippings"
---
[来自： 拿个offer-开源&项目实战](https://wx.zsxq.com/group/51121244585524)

## 先别急着装，搞清楚 Ollama 的内部结构

上一篇选定了 Ollama + vLLM 双栈方案，这一篇正式进入 Ollama 的世界。

不过先别急着装。很多人第一次接触 Ollama，都是在网上看到一句话教程：终端里敲 `ollama run qwen3` ，模型就跑起来了，还能聊天。体验很好，几分钟搞定。但接下来你会遇到一连串问题——

关掉终端窗口，模型还在不在？跑着呢还是停了？你的 Java 项目要怎么跟它对接？ `ollama serve` 和 `ollama run` 到底啥关系？模型文件存哪了？同时跑 Chat 和 Embedding 两个模型会不会互相抢显存？别人文章里写的 `OLLAMA_KEEP_ALIVE=-1` 又是控制什么的？

这些问题网上教程不会讲，Ollama 的官方文档又散落在 GitHub README、FAQ、API 文档好几个地方，你得来回翻才能拼出全貌。

所以这一篇的定位，不是教你敲命令，而是帮你建立一张 Ollama 的完整认知地图。类比一下：你第一次用 Docker 之前，最好先搞清楚 image、container、Dockerfile、daemon 这些概念是什么关系，而不是上来就 `docker run` ——跑是跑起来了，出了问题完全不知道该查哪里。Ollama 也是同样的道理。

下一篇再动手安装、拉模型、写代码。这一篇把概念打通，下一篇你跟着操作时就不会懵。

## Ollama 是什么：一句话定位

上一篇讲过，本地部署中间件分两层：底层是推理引擎，负责算得快；上层是服务框架，负责用得爽。

**Ollama是上层服务框架，不是推理引擎。** 它底层的推理引擎是 llama.cpp——那个用纯 C++ 写出来、让大模型能在普通电脑上跑起来的项目（最早是在 MacBook 上验证的，现在已经支持 macOS、Linux、Windows 全平台，CPU、NVIDIA GPU、Apple Silicon、AMD GPU 都能跑）。Ollama 做的事情是把 llama.cpp 的能力包装成一个好用的产品：模型仓库帮你管理模型，一条命令启动服务，REST API 让你的代码能调，CLI 工具让你在终端里交互。

用 Docker 来类比最直观。Docker 底层的容器运行时是 containerd + runc，但你日常打交道的只有 Docker CLI 和 Docker Daemon。你不需要知道 runc 怎么创建 cgroup，你只需要 `docker pull` 拉镜像、 `docker run` 跑容器。Ollama 跟 Docker 的关系结构几乎一模一样——你不需要操心 llama.cpp 怎么做矩阵乘法，你只需要 `ollama pull` 拉模型、 `ollama run` 跑推理。

这个类比不是我硬凑的，Ollama 的设计哲学就是对标 Docker。下面这张对照表能帮你快速建立认知锚：

| 维度 | Docker | Ollama |
| --- | --- | --- |
| 后台服务进程 | Docker Daemon（ `dockerd` ） | Ollama Server（ `ollama serve` ） |
| 客户端工具 | Docker CLI（ `docker` ） | Ollama CLI（ `ollama` ） |
| 远程仓库 | Docker Hub | Ollama Registry（ollama.com/library） |
| 配置文件 | Dockerfile | Modelfile |
| 拉取命令 | `docker pull nginx` | `ollama pull qwen3` |
| 运行命令 | `docker run nginx` | `ollama run qwen3` |
| 版本标识 | `nginx:1.25` （image tag） | `qwen3:32b` （model tag） |
| 本地存储路径 | `/var/lib/docker/` | `~/.ollama/models/` |
| 删除命令 | `docker rmi nginx` | `ollama rm qwen3` |
| 查看本地列表 | `docker images` | `ollama list` |

记住这张表，后面每讲到一个 Ollama 的概念，你脑子里都能找到一个 Docker 的对应物。

## Ollama 的架构：Client-Server 模式

Ollama 的运行架构非常标准：一个后台服务进程 + 多种客户端。理解这个架构是理解后面所有概念的基础。

### 1\. ollama serve：后台服务进程

Ollama 启动后是一个常驻的 HTTP 服务，默认监听在 `127.0.0.1:11434` 。这个进程是整个 Ollama 的核心，它负责四件事：

- 1.
	**加载模型** ：把 GGUF 权重文件从磁盘加载到显存（GPU）或内存（CPU）

- 2.
	**接收请求** ：通过 REST API 接收推理请求

- 3.
	**调度推理** ：调用底层 llama.cpp 执行实际的推理计算

- 4.
	**返回结果** ：把生成的文本通过 HTTP 响应返回给客户端

macOS 和 Windows 安装桌面版之后， `ollama serve` 会随系统自动启动，你在状态栏能看到一个小羊驼图标。Linux 上通过官方安装脚本安装后，会自动配好 systemd 服务并启动；如果你是手动下载二进制文件安装的，则需要自己配 systemd 或手动启动。

不管哪种方式，本质上都是在你的机器上跑了一个 HTTP Server。

### 2\. CLI 命令：客户端调服务端

`ollama run` 、 `ollama pull` 、 `ollama list` 、 `ollama rm` 、 `ollama show` 这些命令看起来像是在直接操作模型，实际上它们每一个都是 HTTP 客户端——往 `ollama serve` 暴露的 API 发 HTTP 请求，拿到响应后格式化输出到终端。

这意味着什么？意味着你完全可以不用 CLI，直接用 curl、Postman、OkHttp 或者任何 HTTP 客户端去调 Ollama 的 API。CLI 只是官方提供的一个方便的客户端而已，不是唯一的入口。

举个例子， `ollama list` 这条命令背后做的事情，等价于：

```
curl http://localhost:11434/api/tags
```

`ollama pull qwen3` 背后做的事情，等价于：

```
curl -X POST http://localhost:11434/api/pull -d '{"name": "qwen3"}'
```

理解了这一层，你就不会再困惑一个常见的问题：我关掉了 `ollama run` 的终端窗口，模型是不是就停了？答案是不会—— `ollama run` 只是一个交互式的 REPL 客户端，关掉它只是关掉了聊天窗口。真正在运行模型的是 `ollama serve` 后台进程，它还活着，模型还在显存里，你的 Java 应用照样能调 API。

### 3\. 一张架构图

下面这张图把 Ollama 的 Client-Server 架构画清楚：

![无法获取该图片](https://oss.open8gu.com/iShot_2026-04-03_22.29.53.svg "无法获取该图片")

从图里可以看出，不管你是用 CLI、curl 还是 Java 代码，走的都是同一条路：HTTP 请求到 Ollama Server，Server 调度 llama.cpp 引擎在 GPU 或 CPU 上执行推理。

## 模型管理：拉取、存储、版本

搞清楚了架构，下一个问题是模型怎么管理。Ollama 在这一块的设计思路跟 Docker 管理镜像几乎一样。

### 1\. ollama pull 拉了什么

很多人以为 `ollama pull` 只是下载了一个权重文件。实际上，拉下来的是一个完整的模型包，包含两部分：

- **GGUF文件** ：上一篇讲过，GGUF 是 llama.cpp 发明的单文件格式，把权重、tokenizer 词表、模型元数据全打包在一个文件里。这是模型的核心，体积最大，也是推理时实际加载的文件

- **Ollama配置层** ：chat template（对话格式模板）、默认推理参数（temperature、num\_ctx 等）、默认 system prompt、license 等。这些以独立的 blob 存储，可以覆盖 GGUF 文件内嵌的默认值

Ollama 的存储结构借鉴了 Docker 镜像的分层设计：一个 manifest 文件指向多个 blob，GGUF 权重是最大的那个 blob，模板、参数、system prompt 各自是一个小 blob。 `ollama pull` 把这些全拉下来，所以之后就能直接 `ollama run` ，不需要你自己去配 chat template、调参数。这跟 `docker pull` 拉下来的镜像包含了运行环境、依赖库、应用代码， `docker run` 就能直接跑，是同一个逻辑。

对比一下从 Hugging Face 手动下载 GGUF 文件的体验：现在主流的 GGUF 文件已经内嵌了 tokenizer、chat template 和基础元数据，用 llama.cpp 加载时能自动识别。但推理参数（num\_ctx 设多大、temperature 设多少、repeat\_penalty 要不要开）还得你自己定，想固化 system prompt 也要额外配置。Ollama 把这些选择题全帮你做好了——拉下来就是一套经过调试的默认配置，开箱即用。

### 2\. 模型存储在哪里

`ollama pull` 下来的模型默认存在这些位置：

| 操作系统 | 默认路径 |
| --- | --- |
| macOS | `~/.ollama/models` |
| Linux（用户安装） | `~/.ollama/models` |
| Linux（系统服务安装） | `/usr/share/ollama/.ollama/models` |
| Windows | `%USERPROFILE%\.ollama\models` |

模型文件动辄几个 GB 到几十个 GB。一个 7B 的 Q4 量化模型大约 45GB，32B 的 Q4 量化大约 18～20GB。如果你拉了好几个模型，磁盘空间会消耗得很快。

遇到磁盘空间紧张、或者想把模型放到一块大容量 SSD 上，可以通过 `OLLAMA_MODELS` 环境变量自定义存储路径。这个变量下一节讲环境变量时会详细说。

### 3\. tag 机制：同一个模型的多个变体

你在 Ollama 上看到的模型名称，通常带有冒号分隔的 tag：

- `qwen3:32b` —— Qwen3 家族，32B 参数量版本

- `qwen3:14b` —— Qwen3 家族，14B 参数量版本

- `qwen3:7b` —— Qwen3 家族，7B 参数量版本

- `qwen3:32b-q4_K_M` —— Qwen3 32B，指定 Q4\_K\_M 量化档位

tag 通常编码了两个信息： **参数量** 和 **量化档位** 。参数量决定了模型的能力上限，量化档位决定了模型的体积和精度损失。上一篇讲过的量化概念，在这里就体现为 tag 里的 q4、q8、fp16 这些后缀。

当你执行 `ollama pull qwen3` 不带 tag 时，拉的是默认 tag——通常是 Ollama 认为最适合大多数用户的那个变体（综合考虑效果和资源占用）。这跟 `docker pull nginx` 默认拉 `nginx:latest` 是一回事。

需要注意的是，不同 tag 的模型是 **独立存储** 的。 `qwen3:32b` 和 `qwen3:14b` 是两个完全不同的文件，不共享磁盘空间。拉多个 tag 就会占多份磁盘。

### 4\. 模型列表与清理

`ollama list` 查看本地已有的所有模型，输出包含模型名称、大小、最后修改时间：

```
ollama list
NAME                             ID              SIZE      MODIFIED     
qwen2.5:7b                       845dbda0ea48    4.7 GB    6 weeks ago     
dengcao/Qwen3-Reranker-8B:F16    94d4dbbb09e1    16 GB     4 months ago    
qwen3:8b                         500a1f067a9f    5.2 GB    4 months ago    
qwen3:8b-fp16                    0b358e6e9d8c    16 GB     4 months ago    
qwen3-embedding:8b-fp16          aa924958585e    15 GB     4 months ago    
gemma3n:e4b                      15cb39fd9394    7.5 GB    4 months ago    
deepseek-r1:8b                   6995872bfe4c    5.2 GB    6 months ago
```

`ollama rm` 删除不需要的模型释放磁盘空间。模型文件占地儿大，养成定期清理的习惯很重要——你试完一个模型觉得效果不行，顺手 `ollama rm` 删掉，别让它白白占着几十个 GB。

下面这张流程图展示了模型从远程仓库到本地使用的完整路径：

## Modelfile：自定义你的模型

Ollama 的 Modelfile 是对 Docker 的 Dockerfile 的直接致敬。Dockerfile 描述怎么从一个基础镜像构建出你自定义的镜像，Modelfile 描述怎么从一个基础模型构建出你自定义的模型。

### 1\. 核心指令

Modelfile 支持的指令不多，但每个都有明确的用途。

#### 1.1 FROM：指定基础模型

```
FROM qwen3:32b
```

类似 Dockerfile 的 `FROM ubuntu:22.04` 。指定你的自定义模型基于哪个模型构建。可以填 Ollama Registry 里的模型名，也可以填本地 GGUF 文件的路径：

```
FROM /path/to/my-model.gguf
```

从本地 GGUF 文件创建模型，这在你从 Hugging Face 下载了社区量化版本、想导入 Ollama 管理时很有用。

#### 1.2 PARAMETER：推理参数注入

```
PARAMETER temperature 0.1
PARAMETER num_ctx 8192
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

设定模型的默认推理参数。几个 RAG 场景下特别重要的参数：

- `temperature` ：控制生成的随机性，0 最确定、1+ 最随机。RAG 场景通常设 0~0.3，你要的是基于检索内容的精确回答，不是天马行空的创意

- `num_ctx` ：上下文窗口大小，单位是 token。Ollama 默认 2048（部分模型可能在其 Modelfile 中覆盖为更大值）。RAG 场景需要塞入检索到的 chunk，往往要调到 8192 甚至更大

- `top_p` ：核采样概率阈值，和 temperature 配合使用

- `repeat_penalty` ：重复惩罚系数，防止模型车轱辘话来回说

- `num_predict` ：最大生成 token 数，控制回答长度上限

这里有一个本地部署最常踩的坑： **`num_ctx` 调大会显著增加显存占用** 。之前调云端 API 时你不需要关心这个——那是云厂商的问题。但本地部署时，上下文窗口越大，KV Cache 占的显存越多。一个 32B 模型把 `num_ctx` 从 4096 调到 32768，可能多吃好几个 GB 显存，直接导致显存不够模型被部分卸载到 CPU，推理速度断崖式下降。本地部署时， `num_ctx` 要根据你的显存量来设，不是越大越好。

#### 1.3 SYSTEM：设定默认 System Prompt

```
SYSTEM """
你是一名专业的技术文档助手。只根据用户提供的参考资料回答问题，不要使用自身的预训练知识。如果参考资料中没有相关信息，直接说明无法回答。
"""
```

每次对话自动带上这段 system prompt，不需要客户端每次都传。适合把角色定义和行为约束固化到模型配置里。

#### 1.4 TEMPLATE：自定义 Chat Template

```
TEMPLATE """
{{- if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}
{{- range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
```

Chat Template 控制的是多轮对话的格式化方式——怎么把 system、user、assistant 这些角色的消息拼成模型能理解的文本。用的是 Go template 语法。

大多数情况下你不需要动这个。 `ollama pull` 下来的模型已经带了正确的 chat template，手动改反而容易出错。只有当你从裸 GGUF 文件创建模型、且这个文件里没有嵌入 template 时，才需要自己写。

#### 1.5 ADAPTER：挂载 LoRA 适配器

```
ADAPTER /path/to/my-lora.gguf
```

把一个 LoRA 微调后的适配器文件挂到基础模型上。上一篇讲过，垂直领域微调是本地部署的核心价值之一。你用私有数据训练了一个 LoRA 适配器，通过这个指令就能把它应用到基础模型上，不需要重新做全量训练。

### 2\. 一个完整的 Modelfile 示例

假设你在做一个企业内部知识库项目，需要一个基于 Qwen3-32B 的专用问答模型：

```
# 基础模型
FROM qwen3:32b

# 推理参数：RAG 场景需要低随机性、足够的上下文窗口
PARAMETER temperature 0.1
PARAMETER num_ctx 8192
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 2048

# 固化 System Prompt
SYSTEM """
你是 XX 公司的内部知识库助手。请严格遵守以下规则：
1. 只根据用户提供的参考资料回答问题，不要使用自身的预训练知识
2. 如果参考资料中没有相关信息，回复"抱歉，我在现有资料中没有找到相关信息"
3. 回答时标注引用来源，格式为 [编号]
4. 使用简洁、专业的中文
"""
```

有了这个 Modelfile，用 `ollama create` 命令就能创建一个自定义模型：

```
ollama create kb-assistant -f ./Modelfile
```

之后 `ollama run kb-assistant` 或者通过 API 调用 `kb-assistant` 这个模型，就自带了上面配置的所有参数和 system prompt。

### 3\. 什么时候需要写 Modelfile

大多数场景不需要。 `ollama pull` 下来的模型已经带好了合理的默认配置，直接用就行。只有以下几种情况才值得写一个 Modelfile：

- 想把 system prompt 固化到模型里，避免每次请求都传

- 需要调整默认推理参数（比如 RAG 场景把 temperature 固定在 0.1）

- 要挂载 LoRA 适配器做微调推理

- 从 Hugging Face 下载的 GGUF 文件想导入 Ollama 管理

日常开发测试阶段，直接 pull 官方模型就够用。等到项目往生产推进、需要固化配置时，再来写 Modelfile 也不迟。

## API 接口：两套共存

Ollama 同时提供两套 API，理解它们的关系和区别很重要。

### 1\. Ollama 原生 API

这是 Ollama 自己定义的接口，路径以 `/api/` 开头。

#### 1.1 /api/chat：多轮对话

这是最常用的接口，也是 RAG 场景的核心。请求格式：

```
{
  "model": "qwen3:32b",
  "messages": [
    {
      "role": "system",
      "content": "你是一个知识库助手。"
    },
    {
      "role": "user",
      "content": "什么是向量数据库？"
    }
  ],
  "stream": false
}
```

响应格式：

```
{
  "model": "qwen3:32b",
  "message": {
    "role": "assistant",
    "content": "向量数据库是一种专门用于存储和检索高维向量的数据库系统……"
  },
  "done": true,
  "total_duration": 5023456789,
  "eval_count": 128,
  "eval_duration": 4800000000
}
```

`messages` 数组的结构跟你之前调 SiliconFlow 时用的一模一样—— `system` 、 `user` 、 `assistant` 三种角色，多轮对话通过交替拼接 user 和 assistant 消息来实现。

`stream` 设为 `true` 时走流式输出，返回一连串 JSON 对象，每个包含一小段增量文本——跟你之前学的 SSE 协议是同一个套路。

响应里多了几个 Ollama 特有的字段： `total_duration` （总耗时，纳秒）、 `eval_count` （生成的 token 数）、 `eval_duration` （推理耗时）。这些字段在 OpenAI 兼容 API 里拿不到，写调试工具或做性能监控时很有用。

#### 1.2 /api/generate：单轮生成

传一段 raw prompt，不走 messages 结构。适合做文本续写、补全这类不需要对话格式的任务。RAG 场景用得少，知道有这个接口就行。

#### 1.3 /api/embed：生成向量

```
{
  "model": "nomic-embed-text",
  "input": ["什么是向量数据库？", "Milvus 的索引类型有哪些？"]
}
```

把文本转成向量，跟你之前调 SiliconFlow 的 Embedding API 是一回事，只是换了个 URL。注意 Ollama 有新旧两个 Embedding 接口： `/api/embeddings` （旧，单条输入）和 `/api/embed` （新，支持批量输入），用新的就好。

#### 1.4 模型管理接口

还有一组管理接口，用于模型的增删查改：

- `/api/tags` —— 列出本地所有模型（ `ollama list` 背后调的就是它）

- `/api/show` —— 查看模型详情（Modelfile、参数、模板）

- `/api/pull` —— 拉取模型

- `/api/push` —— 推送模型到 Registry

- `/api/delete` —— 删除模型

- `/api/create` —— 从 Modelfile 创建模型

这些接口写管理后台或运维脚本时会用到，日常开发用 CLI 就够了。

### 2\. OpenAI 兼容 API

这是 Ollama 后来加上的一组接口，路径以 `/v1/` 开头，对齐 OpenAI 的 API 协议。

- `/v1/chat/completions` —— 对齐 OpenAI Chat Completions API

- `/v1/embeddings` —— 对齐 OpenAI Embeddings API

- `/v1/models` —— 对齐 OpenAI Models API

同样的对话请求，用 OpenAI 兼容 API 长这样：

```
POST http://localhost:11434/v1/chat/completions

{
  "model": "qwen3:32b",
  "messages": [
    {
      "role": "system",
      "content": "你是一个知识库助手。"
    },
    {
      "role": "user",
      "content": "什么是向量数据库？"
    }
  ],
  "temperature": 0.1,
  "stream": false
}
```

响应格式：

```
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "model": "qwen3:32b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "向量数据库是一种专门用于存储和检索高维向量的数据库系统……"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 128,
    "total_tokens": 153
  }
}
```

跟你之前调 SiliconFlow 的格式完全一样—— `choices[0].message.content` 取回答， `usage` 看 token 用量， `finish_reason` 判断生成是否正常结束。

把两套 API 的关键差异摆在一起看：

| 维度 | Ollama 原生 API | OpenAI 兼容 API |
| --- | --- | --- |
| 路径前缀 | `/api/` | `/v1/` |
| 对话接口 | `/api/chat` | `/v1/chat/completions` |
| 响应结构 | `message.content` 直出 | `choices[0].message.content` |
| Token 统计 | `eval_count` + `eval_duration` | `usage.prompt_tokens` + `usage.completion_tokens` |
| 额外信息 | 有推理耗时、加载状态等 | 无（对齐 OpenAI 标准） |
| 兼容性 | Ollama 专用 | 任何 OpenAI 兼容客户端可用 |

### 3\. 该用哪套

对 Java 开发者的建议： **优先用OpenAI兼容API** 。

原因很简单。你在 RAG 系列里写的 OkHttp 调用代码，全是按 OpenAI 协议写的。之前打 SiliconFlow 的 `https://api.siliconflow.cn/v1/chat/completions` ，现在改成 Ollama 的 `http://localhost:11434/v1/chat/completions` ，请求体和响应解析的代码一行不用动。这就是上一篇说的改 BaseURL 就能跑。

Ollama 原生 API 的优势在于字段更丰富——推理耗时、模型加载状态、显存占用这些信息只有原生 API 才返回。如果你要做一个 Ollama 的管理面板、监控仪表盘，或者需要细粒度的性能数据，原生 API 更合适。

两套 API 同时存在、互不冲突，按需选择就好。

## 关键配置与环境变量

### 1\. 常用环境变量

Ollama 的行为通过环境变量来控制。不需要配置文件、不需要 YAML，直接设环境变量就行。下面这几个是日常使用中最常用到的：

| 环境变量 | 作用 | 默认值 | 什么时候改 |
| --- | --- | --- | --- |
| `OLLAMA_HOST` | 服务监听地址 | `127.0.0.1:11434` | 需要其他机器访问时改成 `0.0.0.0:11434` |
| `OLLAMA_MODELS` | 模型存储路径 | `~/.ollama/models` | 系统盘空间不足，想存到大容量 SSD 时 |
| `OLLAMA_NUM_PARALLEL` | 单模型并发槽位数 | 自动（通常 1~4） | 需要同时处理多个请求时适当调大 |
| `OLLAMA_MAX_LOADED_MODELS` | 最大同时加载模型数 | 自动（3 x GPU 数量，CPU 推理时为 3） | 显存紧张时可手动调小，或确认默认值是否满足需求 |
| `OLLAMA_KEEP_ALIVE` | 模型空闲卸载时间 | `5m` （5 分钟） | 频繁调用时改大或设为 `-1` （永不卸载） |

除了上面这些，还有一个值得关注的变量： `OLLAMA_FLASH_ATTENTION` （设为 `1` 开启 Flash Attention），能显著降低长上下文场景的显存占用并提升推理速度——跟上面讲的 `num_ctx` 调大吃显存的问题直接相关。目前还是实验性功能，下一篇实操时会用到。

几个值得展开讲的场景：

#### 1.1 OLLAMA\_HOST：什么时候改成 0.0.0.0

默认的 `127.0.0.1` 意味着只有本机能访问 Ollama 的 API。如果你的 Ollama 跑在一台 GPU 服务器上，Java 应用跑在另一台机器上，就需要把监听地址改成 `0.0.0.0:11434` ，允许外部访问。

但要注意：一旦改成 `0.0.0.0` ，任何能访问到这台机器 11434 端口的人都能调你的 Ollama API。Ollama 本身没有认证机制，所以生产环境下要配合防火墙规则或 Nginx 反向代理来做访问控制。

#### 1.2 OLLAMA\_KEEP\_ALIVE：模型卸载时间

这是一个特别容易踩坑的配置。默认值 `5m` 意味着模型空闲 5 分钟后，Ollama 会自动把它从显存里卸载。下次请求来了，要重新从磁盘加载到显存，这个加载过程可能要几秒到十几秒——用户会明显感知到一次冷启动延迟。

几个典型的取值：

- `5m` （默认）：适合偶尔用一下的场景，空闲 5 分钟自动释放显存

- `30m` 或 `1h` ：适合开发调试阶段，写代码过程中模型不会被卸载

- `-1` ：永不卸载，模型常驻显存。适合需要持续响应的服务场景

- `0` ：用完立即卸载。适合显存极其紧张、需要手动腾挪的场景

网上文章里常见的 `OLLAMA_KEEP_ALIVE=-1` ，就是告诉 Ollama 别自动卸载模型。对 RAG 项目来说，如果你的 Java 应用持续在调 Ollama，设成 `-1` 可以避免反复加载带来的延迟抖动。

#### 1.3 OLLAMA\_MAX\_LOADED\_MODELS：多模型同时加载

这个配置对 AI 项目来说至关重要。

一个典型的 RAG 系统至少需要两个模型同时工作：Chat 模型（比如 `qwen3:32b` ）负责生成回答，Embedding 模型（比如 `nomic-embed-text` ）负责把文本转成向量。

前面说了， `OLLAMA_MAX_LOADED_MODELS` 的默认值是 3 x GPU 数量。理论上两个模型同时加载没问题。但实际情况是：如果你的显存只够装一个大的 Chat 模型，Ollama 会在加载 Embedding 模型时把 Chat 模型卸载腾空间，反之亦然——每次切换都是几秒到十几秒的延迟。

这时候需要关注的不是 `OLLAMA_MAX_LOADED_MODELS` 的数值，而是显存是否真的够同时装两个模型。好消息是 Embedding 模型通常很小（几百 MB），一个 Chat 模型加一个 Embedding 模型的显存总需求，比单独跑 Chat 模型多不了太多。如果显存确实紧张，可以考虑用更小的量化档位，或者把 Embedding 模型跑在 CPU 上（通过 `num_gpu 0` 参数）。

## 硬件调度：Ollama 怎么用你的 GPU

### 1\. 自动检测

Ollama 在启动时会自动检测你的机器上有没有可用的 GPU：

- **NVIDIA显卡** ：走 CUDA，需要装好 NVIDIA 驱动和 CUDA 工具链

- **AppleSilicon（M1/M2/M3/M4）** ：走 Metal，macOS 原生支持，不需要额外配置

- **AMD显卡** ：走 ROCm，Linux 下支持较好，Windows 下支持有限

检测到 GPU 就优先用 GPU 做推理，没有 GPU 就 fallback 到纯 CPU。你不需要手动指定走 GPU 还是 CPU，Ollama 自己判断。

### 2\. GPU + CPU 混合推理

如果模型太大、显存塞不下全部层，Ollama 不会直接报错，而是自动把一部分层放到 GPU 显存、一部分层放到 CPU 内存。

举个例子：Qwen3-32B 的 Q4\_K\_M 量化版需要大约 18～20GB 显存。你的 RTX 4090 有 24GB 显存，但系统和其他程序占了一些，实际可用可能只有 20～21GB。再加上推理过程中 KV Cache 也要占显存，如果上下文窗口设得大一些，总需求就可能超过可用显存。

这时候 Ollama 会把模型的大部分层（比如 80%）放在 GPU 上，剩下的层放在 CPU 内存里。GPU 上的层跑得快，CPU 上的层跑得慢，整体推理速度介于纯 GPU 和纯 CPU 之间。你能感知到的表现是：比全放 GPU 时慢一些，但还是比纯 CPU 快得多。

### 3\. num\_gpu 参数

如果你想手动控制有多少层放到 GPU 上，可以通过 Modelfile 的 `PARAMETER num_gpu` 或 API 请求里的 `num_gpu` 参数来指定：

- `num_gpu 0` —— 强制纯 CPU 推理，完全不用 GPU。适合想把 GPU 留给其他任务的场景

- `num_gpu 999` （一个超大的数） —— 强制尽量把所有层都放到 GPU 上。显存不够时该放不下还是放不下

- `num_gpu 40` —— 精确指定放 40 层到 GPU，剩余层放 CPU

一般不需要手动调这个参数，Ollama 的自动分配对大多数场景够用。只有当你需要精确控制 GPU 显存占用（比如同一张卡上还要跑其他 GPU 程序）时才需要介入。

### 4\. 多 GPU 环境

Ollama 能检测到多张 GPU，但有一个关键限制： **不支持 Tensor Parallelism** 。

Tensor Parallelism（张量并行）是把模型每一层 **内部的权重矩阵** 拆分到多张显卡上，多卡同时计算同一层的不同部分，然后通过 all-reduce 同步结果，再一起进入下一层。比如某层的权重矩阵是 `[4096, 4096]` ，两张卡各算一半，真正实现了并行加速。vLLM 和 SGLang 支持这种模式，能在多卡环境下大幅提升推理速度。

Ollama 做不到这一点。多卡时的行为是 **Pipeline Parallelism（流水线并行）** ：模型的不同层分配到不同 GPU 上——比如第 0~31 层在卡 A，第 32~63 层在卡 B。推理时各层仍然串行执行，数据从卡 A 算完一层传到卡 B 算下一层，因为更深层依赖上一层的输出结果。本质上是用多张卡的显存装下一个大模型，但单条请求的推理速度不会因为多卡而成倍提升。

想要真正的多卡并行推理，需要上 vLLM 或 SGLang——这也是后面那几篇的内容。

## Ollama 的局限性

讲了这么多 Ollama 能做什么，也要客观地把它不能做什么摆出来。这些局限性和上一篇的定位结论是一致的：Ollama 是开发者的本地工具，不是生产级平台。

- **并发能力有限** ：底层 llama.cpp 的 parallel slots 通常是个位数到十几个。企业级应用动辄几十上百的并发 QPS，Ollama 扛不住。

- **不支持TensorParallelism** ：前面已经讲了，单模型无法真正跨多卡并行。大模型在多卡环境下的推理效率上不去。

- **只支持GGUF格式** ：safetensors 原始权重、GPTQ 量化、AWQ 量化的模型都不能直接用。想用这些格式，要么先转成 GGUF，要么换 vLLM。

- **调优空间小** ：llama.cpp 能暴露的参数有限。像 KV Cache 策略、批处理调度策略、量化算子选择这些细节，在 vLLM 里你可以精细控制，在 Ollama 里基本只能用默认的。

- **缺少生产级运维能力** ：没有内置的负载均衡、健康检查、滚动更新，监控指标也很有限（API 响应里有推理耗时等基础数据，但没有标准的 Prometheus 指标端点，需要社区第三方工具补齐）。你要在 Ollama 外面自己搭这些，或者干脆换一个有生产运维能力的方案。

- **模型生态依赖OllamaRegistry** ：虽然可以从本地 GGUF 文件导入模型，但最方便的路径还是 `ollama pull` 。Ollama Registry 里的模型数量和变体不如 Hugging Face 丰富，你想要的某个特定量化档位不一定有。

一句话定位： **Ollama是开发者的本地LLM工具箱，不是生产级推理平台。** 用它来开发测试、快速验证、内部小工具，需要上生产时切 vLLM。

## 常见误区

跟上一篇的风格一样，把几个容易踩的认知坑掰开揉碎讲一遍。

### 1\. Ollama 慢 = 模型慢？

不一定。你感知到的慢，可能根本不是模型推理慢，而是这几种情况：

第一种， `OLLAMA_KEEP_ALIVE` 太短，模型被自动卸载了。每次请求来的时候都要重新把几个 GB 的权重从磁盘加载到显存，这个冷启动延迟可能有几秒到十几秒。你以为模型在思考，其实是在加载。把 `OLLAMA_KEEP_ALIVE` 调大或设成 `-1` 就能解决。同理，Ollama 启动后首次请求某个模型也需要从磁盘加载，这是正常的冷启动——只要 `OLLAMA_KEEP_ALIVE` 设得够长，后续请求就不会再有这个延迟。

第二种， `num_ctx` 设得太大，显存塞不下，大量层被迫跑在 CPU 上。上面讲过，GPU + CPU 混合推理时速度会明显下降。检查一下你的 `num_ctx` 设置，按实际需要来，别无脑拉满。

第三种，同时加载了多个模型但 `OLLAMA_MAX_LOADED_MODELS` 没调，每次请求都在卸载加载之间反复横跳。解决方案前面讲过了。

先排查这三个配置问题，再考虑是不是模型本身太大、硬件太弱。

### 2\. 装完 Ollama 就能上生产？

不能。上一节的局限性已经列清楚了：并发扛不住、没有监控、没有负载均衡、没有健康检查、不支持多卡并行、无法滚动更新。Ollama 的设计目标就不是生产环境，它是给开发者用的本地工具。

一个判断标准：如果你的服务只有你自己和几个同事在用、挂了手动重启也能接受，Ollama 可以顶。如果你的服务面向真实用户、需要 SLA 保障、需要监控报警、需要弹性扩缩容，Ollama 不行，上 vLLM。

### 3\. ollama run 就是在运行模型？

`ollama run` 做了两件事：如果模型没加载就先加载到显存，然后打开一个交互式 REPL 让你聊天。但真正在运行模型的不是 `ollama run` 这个进程，而是 `ollama serve` 后台服务。

你关掉 `ollama run` 的终端窗口， `ollama serve` 还在，模型还在显存里（直到 `OLLAMA_KEEP_ALIVE` 超时后才会被卸载）。你的 Java 应用通过 API 调 Ollama，跟你有没有开着 `ollama run` 没有任何关系。

搞混这一点的人不少，尤其是之前没接触过 Client-Server 架构的同学。记住： `ollama run` 是客户端， `ollama serve` 是服务端。客户端关了，服务端不受影响。

### 4\. 模型拉一次就万事大吉？

拉下来只是第一步。不配 `OLLAMA_MAX_LOADED_MODELS` 和 `OLLAMA_KEEP_ALIVE` ，多模型场景下会反复加载卸载，延迟抖动严重。不根据显存大小合理设置 `num_ctx` ，上下文窗口要么太小截断检索内容、要么太大撑爆显存。不关注模型版本更新，新版本可能修了 bug 或者换了默认参数。

模型管理是持续的事情，不是一次性的。

### 5\. 本地部署 = Ollama？

上一篇已经讲过，Ollama 只是本地部署工具链里的一环。它的定位是开发测试阶段的快速起步工具。完整的本地部署方案至少涉及：

- **Ollama** ：开发测试、个人使用、内部小工具

- **vLLM** ：生产环境高并发推理

- **Xinference** ：企业多模型统一管理

- **SGLang** ：Agent 场景的前缀复用优化

工具选型看场景，不是一个 Ollama 通吃。

## 小结与下一篇预告

这一篇没写一行代码，也没敲一条 Ollama 命令。但如果你认真读完，脑子里应该已经建立起了 Ollama 的完整认知框架：

- **架构** ：Client-Server 模式， `ollama serve` 是后台 HTTP 服务，CLI 命令是客户端，所有交互都走 REST API

- **模型管理** ： `ollama pull` 拉的是完整模型包（GGUF 文件（含权重 + Tokenizer + 模型元数据）+ Ollama 配置层（chat template、推理参数、system prompt 等）），tag 机制管理同一模型的不同变体，模型默认存在 `~/.ollama/models/`

- **Modelfile** ：类比 Dockerfile，通过 FROM、PARAMETER、SYSTEM、TEMPLATE、ADAPTER 五个指令自定义模型行为

- **两套API** ：Ollama 原生 API（ `/api/chat` ）和 OpenAI 兼容 API（ `/v1/chat/completions` ）共存，Java 开发者优先用兼容 API

- **关键环境变量** ： `OLLAMA_HOST` 、 `OLLAMA_MODELS` 、 `OLLAMA_KEEP_ALIVE` 、 `OLLAMA_MAX_LOADED_MODELS` 这几个要记住，RAG 项目直接用得上

- **硬件调度** ：自动检测 GPU，支持 GPU + CPU 混合推理，但不支持多卡 Tensor Parallelism

- **局限性** ：并发弱、只吃 GGUF、调优空间小、缺生产运维能力——开发利器，生产不行

下一篇将进入实操环节：在三大平台安装 Ollama，拉取 Chat 模型与 Embedding 模型，并在 Ragent 项目中通过修改配置文件，实现不同模型的自动调用与灵活切换。

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51121244585524