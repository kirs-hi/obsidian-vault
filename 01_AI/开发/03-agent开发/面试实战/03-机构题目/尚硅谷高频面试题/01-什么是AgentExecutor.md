---
title: 第1章 什么是AgentExecutor
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 什么是AgentExecutor

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  什么是AgentExecutor

AgentExecutor是执行Agent的调度器，是其运行控制器。

它负责接收输入、驱动Agent进行推理决策、调用相应工具、处理观测结果，并管理整个执行流程。

在 LangChain 中，Agent 无法直接运行，必须通过 AgentExecutor
来驱动和执行。
