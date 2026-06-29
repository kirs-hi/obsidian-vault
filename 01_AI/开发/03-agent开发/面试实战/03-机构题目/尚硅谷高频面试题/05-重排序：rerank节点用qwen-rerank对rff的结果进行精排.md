---
title: 第5章 重排序：rerank 节点用 qwen-rerank对rff的结果进行 精排
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第5章 重排序：rerank 节点用 qwen-rerank对rff的结果进行 精排

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

5.  重排序：rerank 节点用 qwen-rerank对rff的结果进行 精排

这种设计的优势是：

- 并行执行，提升性能

- 结果互补，提升召回率

- 权重可配置，便于调优

  1.  面试口述版项目总结

      1.  30s版

我参与开发了一个基于 RAG 技术的智能知识库系统。系统采用 LangGraph
工作流编排，支持文档自动化导入和智能知识问答。后端使用 FastAPI +
LangGraph，向量模型使用 BGE-M3
混合向量，大模型使用通义千问。查询流程采用多路检索架构------向量、HyDE、网络三路并行，RRF
融合后用 BGE-Reranker 重排序。我主要负责 LangGraph
工作流设计和后端核心开发。
