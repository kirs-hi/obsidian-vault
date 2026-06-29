---
title: 第2章 DeepAgents 的核心能力有哪些？你最看重哪一个？
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第2章 DeepAgents 的核心能力有哪些？你最看重哪一个？

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

2.  DeepAgents 的核心能力有哪些？你最看重哪一个？

文档里四个核心能力：任务规划与分解（ write_todos 体系）、上下文管理（
ls/read_file/write_file/edit_file ）、子代理委派（ task
）、长期记忆（基于 Store
跨会话）。我最看重"规划+上下文管理"，因为它直接解决复杂任务可执行性和上下文溢出两个落地痛点。

3.  write_todos/read_todos/update_todos/delete_todos 在项目里怎么用？

把大任务先拆成可执行步骤，用 write_todos 建计划；执行中用 read_todos
读取当前状态；遇到信息变化动态 update_todos ；无效步骤 delete_todos
。这样任务是"可观测、可调整、可收敛"的，不是一次性拍脑袋推理。
