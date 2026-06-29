---
title: 第10章 DeepAgents 怎么做HITL（人机审批）？关键点是什么？
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第10章 DeepAgents 怎么做HITL（人机审批）？关键点是什么？

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

10. DeepAgents 怎么做HITL（人机审批）？关键点是什么？

\- 在 interrupt_on 标记高风险工具（approve/edit/reject）；

\- 配置 checkpointer 保存中断状态；

\- 恢复执行时使用同一个 thread_id ，并按 action_requests 顺序提交
decisions 。

关键是"同线程恢复 + 顺序一致"，否则审批恢复链路会断。
