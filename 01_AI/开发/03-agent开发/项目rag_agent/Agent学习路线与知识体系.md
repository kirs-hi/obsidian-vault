# Agent 学习路线与知识体系

> 来源：[datawhalechina/[[07-Agent|Agent]]-Learning-Hub](https://github.com/datawhalechina/Agent-Learning-Hub)
> 整理时间：2026-06-02
> 核心理念：Build useful, reliable agents — 不是收藏链接，而是照着执行

---

## 🧭 当前最值得投入的 5 个方向

| 优先级 | 方向 | 为什么 |
|:---:|------|------|
| 1 | **Coding Agents**（[[Claude Code 命令与最佳实践|Claude Code]] / Codex 风格） | 真实代码库 + shell + 文件编辑 + 测试 + 权限 + [[理论学习_上下文压缩与_Token_管理|上下文压缩]] = 最好的 agent 工程样本 |
| 2 | **Agent Harness Engineering** | agent 的能力大量来自 harness：工具协议、权限、状态、反馈、回放、CI、评测 |
| 3 | **Personal Agents**（[[00_OpenClaw_MOC|OpenClaw]] / Hermes 风格） | 长运行、本地优先、跨应用、记忆、skills、消息入口 → "个人操作系统" |
| 4 | **Skills / [[理论学习_MCP_协议与开放工具生态|MCP]] / A2A / ACP** | skills = 能力复用，MCP = 连接工具，A2A = 连接 agent，ACP = 连接宿主应用 |
| 5 | **Evaluation & Safety** | 没有 eval、trace、权限边界的 agent 只能算 demo |

> ⚠️ 不建议重押老式 crew/role-play 框架——可以了解，但不应成为主线。

---

## 📚 9 阶段学习路线

### Stage 0：理解 Agent 是什么

**核心问题：我的场景为什么需要 agent，而不是普通 workflow？**

- [ ] 区分 chatbot / workflow / agent / multi-agent
- [ ] 理解 agent 循环：`observe → think → act → observe`
- [ ] 明白什么时候**不该**用 agent（任务可预测、流程稳定、脚本能解决时）
- [ ] 读 [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [ ] 读 [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)

---

### Stage 1：构建最小 Agent Loop

**产出：50-150 行最小 agent，能选工具、执行工具、返回答案**

- [ ] 用 LLM API 完成普通对话
- [ ] 让模型输出结构化 JSON
- [ ] 定义工具函数（search / calculator / read_file）
- [ ] 解析模型的 tool call / function call
- [ ] 执行工具，将结果喂回模型
- [ ] 加最大步数、超时和错误处理

📖 必读：
- [OpenAI [[01基础_12理解函数调用Function Call|Function Calling]]](https://platform.openai.com/docs/guides/function-calling)
- [Gemini Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Claude Tool Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)

---

### Stage 2：工具使用、RAG 与记忆

**产出：资料研究助手 — 输入主题 → 自动搜索、筛选、总结、输出引用链接**

- [ ] 检索增强生成：chunk → embed → retrieve → answer with citations
- [ ] 接入搜索、数据库、文件、浏览器、代码执行作为工具
- [ ] 区分短期上下文 / 会话记忆 / 长期记忆
- [ ] 处理工具失败、空结果、重复调用、幻觉引用
- [ ] 让 agent 给出来源或证据

📖 必读：
- [LlamaIndex Agents](https://docs.llamaindex.ai/en/stable/use_cases/agents/)
- [LangChain Docs](https://docs.langchain.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

🔧 开源项目参考：

| 项目 | 学什么 |
|------|------|
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | 搜索、抓取、筛选、引用、生成长报告 |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | LangGraph 多轮搜索 + 状态管理 + 引用输出 |
| [STORM](https://github.com/stanford-oval/storm) | outline → question asking → 多视角综合 |
| [Khoj](https://github.com/khoj-ai/khoj) | 本地文档 + 网页 + 语义搜索 + 长期记忆 |
| [RAGFlow](https://github.com/infiniflow/ragflow) | ingestion → chunking → retrieval → grounded answer |
| [mem0](https://github.com/mem0ai/mem0) | agent 长期 memory 组件 |
| [Letta](https://github.com/letta-ai/letta) | stateful agent 的 memory/context 管理 |
| [Onyx](https://github.com/onyx-dot-app/onyx) | 企业级 connectors + hybrid search + 权限 |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | 初学者友好的本地 [[06-RAG|RAG]] + agents |

---

### Stage 3：研究一个现代 Agent Harness

**产出：可调试的 agent harness demo — 含 README、运行步骤、示例输入输出和失败记录**

> 重点不是"框架 API 怎么调"，而是它如何组织工具、上下文、权限、状态、日志、子任务和反馈。

- [ ] 读懂一个 harness 的目录结构
- [ ] 找出 agent loop / tool registry / permission gate / session store / context compaction
- [ ] 跑通最小示例，加一个自己的工具
- [ ] 观察一次完整 trace，解释每一步为什么发生
- [ ] 同一任务分别用「裸 agent loop」和「harness」实现，对比差异

🎯 选一个学深：

| 系统 | 最适合 | 你想学什么 |
|------|--------|----------|
| [Claude Code Docs](https://code.claude.com/docs/en/overview) | Coding agent 产品 | CLI、工具、权限、hooks、subagents、MCP |
| [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | 从零构建 harness | 从 0 到 1 复刻 Claude Code-like |
| [claw0](https://github.com/shareAI-lab/claw0) | 从零构建 gateway | agent loop → session → channel → gateway → memory → delivery → concurrency |
| [hello-agents](https://github.com/datawhalechina/hello-agents) | 中文教程 | 系统补 Agent 原理与实践 |
| [OpenClaw](https://github.com/openclaw/openclaw) | 本地个人 agent | 长运行、skills、消息入口、安全边界 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 自托管 agent | 长期记忆、skills、toolsets、消息网关 |
| [CyberClaw](https://github.com/ttguy0707/CyberClaw) | 透明架构 | 全行为审计、两段式安全、双水位记忆 |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | 状态图编排 | 可恢复执行 + 可控编排 |

---

### Stage 4：多 Agent = 协调问题，不是魔法

**产出：小型多 agent 系统，如 research → write → review → revise**

- [ ] 理解 planner / executor / reviewer / critic / router 角色
- [ ] 用 supervisor 或 graph 管理多 agent（不是让 agent 随便聊天）
- [ ] 定义每个 agent 的职责边界、输入输出 schema、停止条件
- [ ] 处理循环、争论、任务漂移、上下文膨胀
- [ ] 判断什么时候单 agent 更好

📖 推荐：
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [Agent2Agent Protocol](https://a2a-protocol.org/latest/specification/)
- [Agent Client Protocol](https://agentclientprotocol.com/)
- [Google ADK](https://google.github.io/adk-docs/)

---

### Stage 5：Skills、协议与能力打包

**产出：一个可复用 [[skill]]（如 code-review / research-report / pdf-extraction）**

> Skill ≠ Tool ≠ Prompt ≠ MCP。Skill 是可发现、可版本化、可分发的能力包。

- [ ] 理解 Skill vs Tool：tool = 可调用接口，skill = 可复用流程知识
- [ ] 理解 Skill vs Prompt：prompt = 一次性指令，skill = 可版本化的能力包
- [ ] 理解 Skill vs MCP：MCP = 接入外部工具/数据源，skill = 告诉 agent 如何完成一类任务
- [ ] 阅读 Claude Code Skills 文件结构和触发机制
- [ ] 阅读 OpenClaw Skills 的加载、作用域和安全边界
- [ ] 写最小 `SKILL.md`：name + description + 何时使用 + 步骤 + 验收标准
- [ ] 给 skill 加脚本或模板，说明 agent 什么时候才需要加载
- [ ] 给 skill 写 smoke test，验证是否真的提升任务成功率

📖 推荐：
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [OpenClaw Skills](https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Agent2Agent Protocol](https://a2a-protocol.org/latest/specification/)
- [Agent Client Protocol](https://agentclientprotocol.com/)

---

### Stage 6：浏览器与 Computer-Use Agent

**产出：操作公开网页的 browser agent — 打开网页、提取信息、生成摘要**

- [ ] 理解 browser agent 和普通 API tool 的区别
- [ ] 用 Playwright 或 browser-use 做网页观察和点击
- [ ] 给浏览器操作加安全限制（不登录敏感账号、不越权）
- [ ] 处理页面变化、弹窗、加载失败、元素定位失败
- [ ] 记录截图、DOM、动作日志，方便复盘

📖 推荐：
- [Claude Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool)
- [browser-use](https://github.com/browser-use/browser-use)
- [WebArena](https://arxiv.org/abs/2307.13854)

---

### Stage 7：评测、可观测性与安全

**产出：agent eval 表格 — 至少 20 个任务 + 期望结果 + 实际结果 + 失败分类**

- [ ] 准备固定测试集（不能只看 demo）
- [ ] 记录成功率、失败原因、工具调用次数、成本、延迟
- [ ] 看 trace，定位失败发生在 prompt / 工具 / 检索 / 模型 / 状态管理
- [ ] 给危险工具加人工确认（发邮件、删文件、付款、发布内容）
- [ ] 了解 prompt injection / data exfiltration / tool abuse 风险
- [ ] 用回归测试防止改动后能力退化

📖 推荐：
- [OpenAI Evals](https://platform.openai.com/docs/guides/evals)
- [LangSmith](https://docs.smith.langchain.com/)
- [AgentBench](https://arxiv.org/abs/2308.03688)
- [SWE-bench](https://arxiv.org/abs/2310.06770)

---

### Stage 8：交付一个真实 Agent

**产出：别人能 clone 下来跑的 agent 项目**

- [ ] 有明确用户、明确任务、明确成功标准
- [ ] 有日志、trace、错误重试、超时、成本上限
- [ ] 有权限边界和人工确认机制
- [ ] 有部署方式：CLI / Web app / Slack bot / GitHub Action / 后台任务
- [ ] 有 README：怎么运行、配置 key、扩展工具、有哪些限制

---

## 🏗️ 项目阶梯（由浅入深）

| 级别 | 项目 | 你学到什么 |
|:---:|------|----------|
| 1 | Calculator Agent | 最小 tool call loop |
| 2 | Web Research Agent | 搜索、筛选、引用、总结 |
| 3 | PDF QA Agent | RAG、chunk、retrieval、citation |
| 4 | Coding Review Agent | 读取 diff、风险排序、测试建议 |
| 5 | Browser Agent | 页面观察、点击、提取、失败恢复 |
| 6 | Claude Code-like Nano Agent | shell、文件编辑、权限、session、compact |
| 7 | OpenClaw-like Gateway | channel、routing、session、memory、heartbeat、delivery |
| 8 | Reusable Skill Pack | SKILL.md、脚本、模板、触发条件、smoke test |
| 9 | Multi-Agent Writer | planner、writer、reviewer 协作 |
| 10 | Personal Agent | OpenClaw/Hermes-style 记忆、skills、消息入口 |
| 11 | Production Harness | evals、trace、权限、CI、runner、回放 |

---

## 🗺️ 项目分层地图

| 层 | 学这些项目 | 你学到 |
|---|----------|-------|
| **从零构建** | [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) · [claw0](https://github.com/shareAI-lab/claw0) · [hello-agents](https://github.com/datawhalechina/hello-agents) | agent loop · tool registry · session · context compaction · gateway · trace · subagents |
| **个人 / 常驻 Agent** | [OpenClaw](https://github.com/openclaw/openclaw) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [CyberClaw](https://github.com/ttguy0707/CyberClaw) | 长运行 · skills · 记忆 · 消息入口 · 权限 · 安全审计 |
| **[[理论学习_什么是_Coding_Agent_|Coding Agent]]** | [Claude Code](https://code.claude.com/docs/en/overview) · [Codex](https://github.com/openai/codex) · [OpenCode](https://github.com/opencode-ai/opencode) · [OpenHands](https://github.com/All-Hands-AI/OpenHands) · [SWE-agent](https://github.com/SWE-agent/SWE-agent) · [pi](https://github.com/earendil-works/pi) | 真实代码库编辑 · shell · 测试 · sandbox · PR 工作流 |
| **Deep Research / RAG** | [DeerFlow](https://github.com/bytedance/deer-flow) · [LlamaIndex](https://docs.llamaindex.ai/) | 搜索 · 抓取 · 检索 · rerank · 引用 · 报告生成 |
| **教程百科** | [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) · [smolagents](https://github.com/huggingface/smolagents) · [agents-towards-production](https://github.com/NirDiamant/agents-towards-production) | 横向比较 [[理论学习_ReAct_范式与_Agent_Loop|ReAct]] · Plan-and-Execute · Multi-Agent · production patterns |
| **浏览器 / 多模态** | [browser-use](https://github.com/browser-use/browser-use) · [UI-TARS-desktop](https://github.com/bytedance/UI-TARS-desktop) | 浏览器/桌面操作 · 视觉理解 · 动作空间 · 失败恢复 |

---

## 🔌 协议与工具层

| 概念 | 学什么 | 解决什么问题 |
|------|-------|------------|
| **Skills** | [Claude Code Skills](https://code.claude.com/docs/en/skills) · [OpenClaw Skills](https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md) | 把流程知识 + 脚本 + 模板 + 验收标准打包成可复用能力 |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) | 标准化连接外部工具、数据源和服务 |
| **A2A** | [Agent2Agent Protocol](https://a2a-protocol.org/latest/specification/) | agent 之间发现、通信和协作 |
| **ACP** | [Agent Client Protocol](https://agentclientprotocol.com/) | 编辑器/终端/IDE/宿主应用和 agent 之间的统一接口 |

---

## 📄 核心论文

| 论文 | 关键词 |
|------|-------|
| [ReAct](https://arxiv.org/abs/2210.03629) | Reasoning + acting 基础范式 |
| [Toolformer](https://arxiv.org/abs/2302.04761) | 模型学习何时调用工具 |
| [Reflexion](https://arxiv.org/abs/2303.11366) | 语言反馈和自我改进 |
| [Generative Agents](https://arxiv.org/abs/2304.03442) | 记忆 + 反思 + 规划驱动 |
| [Voyager](https://arxiv.org/abs/2305.16291) | 开放世界长期学习 |
| [AgentBench](https://arxiv.org/abs/2308.03688) | Agent 能力评测 |
| [WebArena](https://arxiv.org/abs/2307.13854) | 真实网页环境 benchmark |
| [SWE-bench](https://arxiv.org/abs/2310.06770) | GitHub issue 修复评测 |
| [Dive into Claude Code](https://arxiv.org/abs/2604.14228) | coding agent 的 harness + 权限 + 压缩 + 扩展 |
| [AI Harness Engineering](https://arxiv.org/abs/2605.13357) | harness 作为 agent 能力来源 |
| [Your Agent, Their Asset](https://arxiv.org/abs/2604.04759) | 本地 agent 的真实安全风险 |

---

## 🎯 Claude Code 专项学习路径

推荐顺序：**官方文档 → 复刻项目 → 架构解析 → 工程对照**

1. 📖 读官方文档，理解 hooks / subagents / MCP / GitHub Actions / permissions
2. 🔬 读 [Dive into Claude Code](https://arxiv.org/abs/2604.14228)，抽象 agent harness 设计空间
3. 🛠️ 跟 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 从零复刻核心机制
4. 🔄 对照 [hello-agents](https://github.com/datawhalechina/hello-agents) / [OpenClaw](https://github.com/openclaw/openclaw) / [Hermes Agent](https://github.com/NousResearch/hermes-agent) 学习工程化实现

补充资源：
- [Claude Code 源码解析](https://claudecoding.dev/) — 中文架构解读
- [Claude Code 源码分析地图](https://code.claudecn.com/) — 地图式拆解
- [Agentic Education](https://arxiv.org/abs/2604.17460) — 用 Claude Code 学 Claude Code

---

## ⚡ 学习原则

1. **先动手，再深读** — Build first, then read deeper
2. **小而可靠 > 大而花哨** — Prefer small reliable agents over impressive demos
3. **工具用严格 schema** — Use tools with strict schemas
4. **加 agent 前先加 eval** — Add evals before you add more agents
5. **重要运行必 trace** — Trace every important run
6. **多 agent = 协调问题** — Treat multi-agent as a coordination problem
7. **危险操作留人** — Keep humans in the loop for risky actions
8. **尊重规则** — Respect platform rules, copyrights, and data access boundaries
