# 美团内部 Agent 真实项目开发经验汇总

> 整理目的：数仓开发转行 Agent 开发，收集**有完整开发链路**（背景痛点 → 技术选型 → 架构 → 里程碑 → 踩坑 → 落地效果）的内部实战文档，可用于简历素材与面试讲述。
> 筛选标准：能写进简历 / 能在面试里讲明白。非平台介绍类。

---

## 第一梯队：与数仓背景直接对口（强烈推荐精读）

### 1. 云图 Agent 开发 ⭐️ 最推荐

- 链接：https://km.sankuai.com/collabpage/2617027898
- 一句话：**NL2SQL + 自动生成可视化看板**——用户用自然语言描述需求，Agent 自动推荐数据表、生成并优化 SQL、把结果格式化成云图可渲染的图表。
- 为什么对口：解决的就是数仓人天天遇到的问题，且文档本身就是一份标准的 Agent 项目开发模板。

可抄作业的点：

1. **痛点拆解真实**：用户不知道用哪张表、不会写复杂 SQL、数据格式规范复杂——作为数仓开发深有体会，面试时讲起来有血有肉。
2. **技术选型有理有据**：
   - 后端 Python FastAPI（大模型生态库都是 Python）
   - LangChain / LangGraph 搭建 Agent 工作流
   - 前端 Vue（内部资源完善）
3. **完整系统架构（PlantUML）**：UI → Agent Server 协调层 → LLM → 云图 API → 数据表信息库。
4. **周维度甘特图**：流程 Demo（2023.12）→ MVP（2024.3）→ 新云图界面集成（2024.3）→ 完整看板生成（2024.4）。
5. **Agent 协调层经典逻辑**：理解意图 → 查元数据构建上下文 → 带上下文让 LLM 生成 SQL → 执行 → 后处理。

模块分工参考：

- UI 界面：交互、输入校验、结果与图表展示
- Agent Server：核心协调者，意图解析、与 LLM 交互生成 SQL、查元数据构建上下文、执行 SQL、结果后处理、异常处理
- 云图 API Server：提供表元数据、执行 SQL、访问控制与安全

里程碑拆解（可直接套用到自己的项目规划）：

| 里程碑 | 描述 | 模块 |
| --- | --- | --- |
| 流程 Demo | 命令行 Demo，可生成相关 SQL | Agent / API / UI |
| MVP | 独立交互界面，核心用户可体验 | Agent 调用执行 SQL 接口取数据集 |
| 新云图界面集成 | 能力集成进新界面，开始内测 | Agent 调云图接口直接建图表 |
| 看板创建 | 从单图表到多图表看板 | Agent 生成完整看板 |

Demo 总结（团队复盘要点）：纯前端 Demo 用 Cursor 辅助编码全程没写一行代码；从想法到 Demo，智能 IDE 极大加速；多人围坐有想法就让 Cursor 生成快速验证、方便对齐；下一步尝试后端走测试驱动开发（先让模型生成单测）来反馈迭代。

### 2. 网易智企：从 Copilot 到 DataAgent 的数据治理演进

- 链接：https://km.sankuai.com/collabpage/2757247478
- 一句话：数据开发治理平台引入 AI 的**四阶段实战演进**，同属数据领域，理解"数仓平台 + Agent"如何落地。

---

## 第二梯队：理解 Agent 工程全貌（面试必备）

### 3. AI Agent 技术栈全景图 2026 版 ⭐️ 面试作战地图

- 链接：https://km.sankuai.com/collabpage/2754438061
- 一句话：九千多字综述，最适合转行者的"作战地图"，**自带 C2 面试高频题清单 + 答案要点 + 3 天速成 + 8 周学习路线**。

六层架构模型：

```
应用层：垂直场景（浏览器 / Coding / Harness）
能力层：Skills / 工具调用 / RAG / Memory
工具层：开发框架（LangChain / Dify / AutoGen）
大脑层：模型选型（云端 / 推理 / 私有化）
思想层：核心架构范式（ReAct / Multi-Agent）
```

四大架构范式（面试常考）：

| 范式 | 核心思路 | 适用场景 | 代表实现 |
| --- | --- | --- | --- |
| ReAct | 交替 Reasoning 和 Acting，每步观察环境更新状态 | 需动态获取信息的单 Agent 任务 | LangChain ReAct Agent |
| Plan-and-Execute | 先生成完整计划再逐步执行，支持重规划 | 长任务分解、多步骤项目 | LangGraph、baby-agi |
| Multi-Agent | 多专职 Agent 协作，Orchestrator 调度 | 复杂业务、专业分工 | CrewAI、AutoGen、A2A |
| Agentic RAG | Agent 驱动的多轮迭代检索 + 推理 | 复杂知识问答、研究报告 | LlamaIndex Agentic RAG |

三大协议（高频考点）：

- **MCP**（Anthropic 2024.11）：Agent ←→ 工具/资源，JSON-RPC 2.0，Tools/Resources/Prompts 三原语
- **A2A**（Google 2025.4）：Agent ←→ Agent，HTTP/SSE，Agent Card 发现
- **AG-UI**（CopilotKit 2025）：Agent ←→ 前端 UI，事件驱动流式渲染

Agent 四层记忆架构：Sensory（当前上下文）→ Working（跨轮状态，Redis）→ Episodic（历史摘要，向量 DB）→ Semantic（知识图谱，跨用户）。

长任务可靠性方案：Checkpointing（状态持久化断点续跑）、Plan 重规划（Reflexion）、Human-in-the-loop（关键节点人工确认）、上下文压缩（LLMLingua）、失败预算（最大重试 + 超时）。

C2 面试高频题（自测清单）：

1. 解释 ReAct，与 Chain-of-Thought 的区别？
2. MCP 协议解决了什么问题？与 Function Calling 区别？
3. Multi-Agent 系统如何防止"信息茧房"？
4. 如何设计可靠的长任务 Agent（>20 步）？
5. RAG 演进方向？Agentic RAG 与传统 RAG 区别？
6. DeepSeek-R1 训练方法与普通 SFT 本质区别？
7. vLLM 的核心技术优势？
8. Indirect Prompt Injection 是什么？如何防御？
9. LangGraph vs CrewAI 如何取舍？
10. 如何从零设计 Agent 的 Memory 架构？

---

## 第三梯队：具体工程实践（看别人怎么踩坑）

| 文档 | 链接 | 看点 |
| --- | --- | --- |
| 女娲 Nuwa 前端 AI 开发助手 | https://km.sankuai.com/collabpage/2717730556 | AI 出错场景分析、策略迭代 |
| 企业前端 Harness 工程实践 | https://km.sankuai.com/collabpage/2758565104 | 五层架构 + POC 提效数据 |
| 低门槛搭建"好用"的知识库 | https://km.sankuai.com/collabpage/2758494864 | 业界调研 + 落地数据 |
| Agent Skills 原理开发与实践 | https://km.sankuai.com/collabpage/2752097790 | SKILL.md 结构、能力封装 |
| Plan 功能介绍及实践 | https://km.sankuai.com/collabpage/2754566266 | Plan-and-Execute 实战 |
| CatDesk 优秀实践案例 | https://km.sankuai.com/collabpage/2760248061 | 大量真实落地，含 SQL取数→大象群播报 |
| CatClaw 优秀实践案例 | https://km.sankuai.com/collabpage/2760447450 | 数据全链路自动化案例 |
| MDP-AI Agent Handoffs | https://km.sankuai.com/collabpage/2713207833 | Java 代码示例 |
| AI Agent 开发手册 | https://km.sankuai.com/collabpage/2713340568 | 系统性开发指南 |
| Agent 开发实践（含多子文档） | https://km.sankuai.com/collabpage/2731250390 | 实践合集入口 |

---

## 转行行动建议

核心优势是数仓 / SQL / 数据链路，别丢。Agent 方向最适合切入的是 **DataAgent / NL2SQL / 取数智能体** 这条线——云图 Agent 是现成范本。

落地路径建议：照着云图 Agent 的结构，用 **LangChain + 一个能连 Hive 的工具**，做一个"自然语言查数仓"的小 Demo。这就是一段能讲的真实项目经验：

1. 痛点：业务方不会写 SQL、不知道用哪张表
2. 方案：NL → 表推荐 → SQL 生成 → 执行 → 结果格式化
3. 技术栈：Python FastAPI + LangChain/LangGraph + Hive 工具 + 向量库（表元数据检索）
4. 亮点：元数据 RAG 提升选表准确率、SQL 自我校验降低执行失败率

---

*整理时间：2026-06-04 ｜ 来源：美团学城（KM）内部文档*
