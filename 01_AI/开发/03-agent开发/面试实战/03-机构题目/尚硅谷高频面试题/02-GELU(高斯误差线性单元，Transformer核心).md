---
title: 第2章 GELU（高斯误差线性单元，Transformer核心）
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第2章 GELU（高斯误差线性单元，Transformer核心）

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

2.  GELU（高斯误差线性单元，Transformer核心）

**公式**：$f(x) = x \cdot \Phi(x)$ , Φ(x)是标准正态分布的累积分布函数

近似式：$f(x) \approx 0.5x(1 + tanh(\sqrt{\frac{2}{\pi}}(x + 0.044715x^{3})))$

**特点**：融合随机正则，平滑非线性，0均值；bert/GPT等Transformer架构的标配激活函数。
