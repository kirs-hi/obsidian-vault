---
title: 第4章 介绍RingAllReduce
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第4章 介绍RingAllReduce

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

4.  介绍RingAllReduce

RingAllReduce是一种高效的分布式通信算法，用于数据并行训练中同步梯度。它将每个节点的梯度拆分为N份，节点按环形结构依次发送和接收梯度块，经过N‑1轮通信完成全局求和（Reduce-Scatter），再经过N‑1轮广播（All-Gather）让每个节点获得完整的全局梯度。

RingAllReduce将通信压力均衡到所有节点，避免了瓶颈的出现。
