---
title: 第2章 什么是DPO
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第2章 什么是DPO

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

2.  什么是DPO

直接偏好优化（Direct Preference Optimization，DPO）是Rafael
Rafailov等人在《Direct Preference Optimization：Your Language Model is
Secretly a Reward Model》中提出的一种非传统强化学习算法。

不同于传统的RLHF方法，DPO无需奖励模型，其训练数据包含成对的"好回答"和"差回答"，训练目标是在确保模型稳定的前提下，拉开"好回答"和"差回答"之间的差距。

DPO的损失函数如下

$$\mathcal{L}_{\text{DPO}}\left( \pi_{\theta};\pi_{\text{ref}} \right) = - E_{\left( x,y_{w},y_{l} \right) \sim \mathcal{D}}\left\lbrack \log\sigma\left( \beta\log\frac{\pi_{\theta}\left( y_{w} \middle| x \right)}{\pi_{\text{ref}}\left( y_{w} \middle| x \right)} - \beta\log\frac{\pi_{\theta}\left( y_{l} \middle| x \right)}{\pi_{\text{ref}}\left( y_{l} \middle| x \right)} \right) \right\rbrack$$
