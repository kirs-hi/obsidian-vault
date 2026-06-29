---
title: 第7章 DeepAgents 的流式输出你怎么解析？ chunk 一般看什么？
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第7章 DeepAgents 的流式输出你怎么解析？ chunk 一般看什么？

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

7.  DeepAgents 的流式输出你怎么解析？ chunk 一般看什么？

重点看 model 和 tools 两类节点： model 看是否有 tool_calls
（说明在决策下一步）， tools 看工具返回数据；当 model 无 tool_calls 且有
content，通常是最终回复。这样能完整还原"思考-调用-观察-回答"链路，便于调试与前端实时展示。
