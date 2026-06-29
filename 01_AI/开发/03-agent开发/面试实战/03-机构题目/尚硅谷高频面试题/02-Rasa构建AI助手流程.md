---
title: 第2章 Rasa构建AI助手流程
created: 2026-06-29
tags: [面试, 高频面试题, 尚硅谷]
source: 尚硅谷
---

# 第2章 Rasa构建AI助手流程

> 来源：尚硅谷大模型智能体之高频面试题 V2.1.5

---

2.  Rasa构建AI助手流程

    1.  配置rasa：pipeline、policy、endpoint等

    2.  根据业务设计和用户行为设计流程。

    3.  编写流程中设计的槽位、响应、动作等。

自定义动作通过继承Action类并重写run方法来实现，可以调用外部API，查询数据库或执行其他逻辑。

槽位和对话历史会自动存储在track store中。
