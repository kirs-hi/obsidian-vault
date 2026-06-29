---
title: 第1章 一是核心设计：LangGraph 图式编排
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 一是核心设计：LangGraph 图式编排

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  一是核心设计：LangGraph 图式编排

整个对话处理流程，是用 LangGraph 编排成一个图。

图里有 5
个核心节点：understand（理解）、policy（决策）、action（执行）、guard（守护）、response（响应）。

当用户发来一条消息，系统会：
