---
title: 第2章 结合Langchain说明大模型Agent由哪些部分组成
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第2章 结合Langchain说明大模型Agent由哪些部分组成

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

2.  结合Langchain说明大模型Agent由哪些部分组成

    1.  计划（Planning）

计划模块是Agent的"大脑"，具备思维链、自我反思能力，负责任务分解、策略制定和决策推理。在LangChain中，计划能力主要通过Prompt
Engineering + LLM推理和反思机制（Reflection）实现
