---
title: 第1章 五是策略决策：FlowPolicy 和 EnterpriseSearchPolicy
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第1章 五是策略决策：FlowPolicy 和 EnterpriseSearchPolicy

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

1.  五是策略决策：FlowPolicy 和 EnterpriseSearchPolicy

    1.  系统有两个核心策略：

- FlowPolicy：如果当前有活跃的 Flow，就执行 Flow 的下一个步骤。

这个策略优先级最高，因为 Flow 是明确定义的业务流程，必须优先保证执行。

- EnterpriseSearchPolicy：如果没有活跃的
  Flow，就从知识库检索答案，这个策略处理知识和型问答。

  1.  两个策略是互补的：

- 结构化的任务用 Flow 处理，保证业务逻辑的准确性

- 知识型的问答用检索处理，灵活应对各种问题

策略集成器会按优先级选择最合适的策略，如果都不行，就返回\"我没听懂\"。
