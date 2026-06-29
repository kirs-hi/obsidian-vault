---
title: 第1章 Langchain提供了一系列内置工具，常见的有
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 Langchain提供了一系列内置工具，常见的有

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  Langchain提供了一系列内置工具，常见的有

- DuckDuckGoSearchRun：网络搜索工具。

- RequestsToolKit：HTTP请求工具集。

  1.  并支持用户通过@tool装饰器或StructuredTool的from_function()注册自定义工具。

  1.  行动（Action）

执行模型决策，输出指令或与环境交互。

LangChain的Agen会解析LLM输出中的action和action_input，自动调用对应工具。

工具执行后返回observation，再送回LLM决策下一步，形成"**Thought → Action
→ Observation**"循环。
