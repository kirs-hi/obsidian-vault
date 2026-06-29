---
title: 第1章 Post-LN的问题
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 Post-LN的问题

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  Post-LN的问题

在深层Transformer中（层数很多时），原始的Post-LN结构会导致梯度在反向传播时变得非常不稳定，尤其是在靠近输入侧的层。
