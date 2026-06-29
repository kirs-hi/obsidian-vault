---
title: 第3章 Swish
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第3章 Swish

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

3.  Swish

**公式：**$f(x) = x \cdot Sigmoid(\beta x)$ (β为常数/可学习参数
，β=1时为默认版也叫SwiGLU)

**特点**：处处平滑，性能优于ReLU；β→∞时近似ReLU，β=0时为0.5x。
