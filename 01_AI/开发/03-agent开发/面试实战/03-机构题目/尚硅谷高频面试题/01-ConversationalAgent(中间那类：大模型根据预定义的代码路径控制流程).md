---
title: 第1章 Conversational Agent（中间那类：大模型根据预定义的代码路径控制流程）
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 Conversational Agent（中间那类：大模型根据预定义的代码路径控制流程）

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  Conversational Agent（中间那类：大模型根据预定义的代码路径控制流程）

**特点：**

- 专为对话场景设计，能记住历史消息。

- 可结合工具使用，适合聊天机器人、客服助手。

**适用场景：**需要连续对话且可能调用工具的场景。

1.  Self-ask with Search Agent（图中Evaluator-optimizer 或 Router）

**特点**：

- 自动提出中间问题并调用搜索工具。

- 适合需要多步检索的任务。

**适用场景：**复杂事实查询、多源信息检索。

1.  Plan-and-execute Agent（图中Prompt Chaining + Routing）

**特点：**

- 先规划整个任务步骤，再逐步执行。

- 适合复杂、多步、可分解的任务。

**适用场景：**项目拆解、多工具协作任务。

Langchain Agent核心其实就是一个循环：

**输入 → LLM 选择工具 → 执行工具 → 观察结果 → 判断是否继续 → 输出**
