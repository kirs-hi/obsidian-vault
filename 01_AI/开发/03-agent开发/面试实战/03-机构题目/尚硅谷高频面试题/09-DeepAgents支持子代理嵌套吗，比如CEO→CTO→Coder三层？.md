---
title: 第9章 DeepAgents支持子代理嵌套吗，比如CEO→CTO→Coder三层？
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第9章 DeepAgents支持子代理嵌套吗，比如CEO→CTO→Coder三层？

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

9.  DeepAgents支持子代理嵌套吗，比如CEO→CTO→Coder三层？

当前文档示例明确指出深层嵌套不稳定/不支持，实践上建议扁平化调度（如 CEO
直接调度
CTO、Coder）。也就是"可用优先于理论层级完美"，先保证可控和稳定。
