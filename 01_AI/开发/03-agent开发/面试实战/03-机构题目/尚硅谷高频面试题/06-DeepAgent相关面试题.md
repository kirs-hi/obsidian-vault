---
title: 第6章 DeepAgent相关面试题
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第6章 DeepAgent相关面试题

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

6.  DeepAgent相关面试题

    1.  DeepAgents、LangChain、LangGraph
        分别是什么关系？为什么不直接只用 LangChain？

可以理解为三层： LangChain 负责模型与工具抽象， LangGraph
负责有状态流程编排与持久化运行时， DeepAgents
在外层提供"可直接落地的深度智能体能力"，内置规划、子代理、文件系统、长期记忆。只用
LangChain 适合简单单Agent，复杂多步骤任务用 DeepAgents 更省工程成本。
