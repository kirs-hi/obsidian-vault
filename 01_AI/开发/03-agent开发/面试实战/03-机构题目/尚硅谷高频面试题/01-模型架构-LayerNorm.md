---
title: 第1章 模型架构-LayerNorm
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 模型架构-LayerNorm

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  模型架构-LayerNorm

    1.  Pre-LayerNorm vs Post-LayerNorm

在GPT-1和原版Transformer中使用的都是Post-LayerNorm，即后归一化。GPT-2转而使用Pre-LayerNorm，这是为了解决训练深层Transformer模型时的梯度不稳定和收敛困难问题。
