---
title: 第3章 KV Cache
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第3章 KV Cache

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

3.  KV Cache

    1.  介绍一下KV Cache

KV-Cache（Key-Value Cache）是Transformer模型推理阶段的优化机制。

**核心思想**

推理时，Transformer预测每个token都需要用到所有历史token的K和V，KV-Cache
将这些K和V缓存起来，生成时直接复用，不必重新计算。
