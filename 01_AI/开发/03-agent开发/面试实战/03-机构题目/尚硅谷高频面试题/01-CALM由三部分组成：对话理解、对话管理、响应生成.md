---
title: 第1章 CALM由三部分组成：对话理解、对话管理、响应生成
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 CALM由三部分组成：对话理解、对话管理、响应生成

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  CALM由三部分组成：对话理解、对话管理、响应生成

    1.  对话理解：

当用户发送消息时，LLM命令生成器从tracker
store读取完整对话记录与已收集的信息，调用LLM，识别用户意图、提取槽位，并生成下一步的命令列表，发送给对话管理器。

这里prompt的内容包括：

① 任务描述

② 可用的Flows和Slots（开启流程检索，只放匹配度高的几个流程）

③ 可用操作：start flow、set slot、search and reply等

④ 通用指令：指令+描述

⑤ 决策规则表：满足xx条件，触发xx指令=》生成xx命令

⑥ 当前状态：活跃的flow、当前请求的slot和已填充的slots等

⑦ 对话历史

⑧ 要求生成最新命令序列

这里使用的SearchReadyLLMCommandGenerator，可以触发RAG。
