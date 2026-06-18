---
tags: [AI, OpenClaw, MOC, 知识地图]
created: 2026-03-14
---

# 🦞 OpenClaw 知识地图

> **"The AI That Actually Does Things"**
> OpenClaw — 2026 年最火开源 AI Agent，GitHub 史上 Star 增速最快项目

---

## 快速导航

| 文档 | 内容 | 适合场景 |
|------|------|---------|
| [[01_OpenClaw概览与历史]] | 是什么、谁做的、改名历史 | 初次了解 |
| [[02_OpenClaw功能详解]] | Gateway、Channels、Skills、Memory | 深入学习 |
| [[03_OpenClaw部署指南]] | 安装、配置、Docker、安全 | 动手部署 |
| [[04_OpenClaw生态与社区]] | ClawHub、竞品对比、使用案例 | 生态了解 |
| [[05_OpenClaw代码结构与架构]] | 仓库结构、技术栈、核心子系统 | 源码研究 |
| [[06_OpenClaw代码贡献者指南]] | 环境搭建、编码规范、PR 流程、子系统贡献 | 成为贡献者 |

---

## 核心概念速查

### 关键术语

- **Gateway** — OpenClaw 的核心进程，所有消息路由的控制平面
- **Pi** — 内置的 AI Agent Runtime，四工具极简设计
- **Channel** — 消息渠道适配器（WhatsApp、Telegram 等）
- **Skill** — 模块化能力扩展文件（SKILL.md）
- **ClawHub** — 官方技能市场，10,000+ Skills
- **Lane Queue** — 并发控制机制，每用户独立队列
- **Node** — iOS/Android 移动端节点

### 三大核心原则

1. **本地优先** — 数据完全自控，不上传第三方
2. **无需新 App** — 用你已有的聊天软件作为入口
3. **真正执行** — 不只聊天，真正帮你做事

---

## 项目数据（2026-03-14）

```
GitHub Stars:    250,000+  （史上最快，超越 React）
Contributors:    1,190+
Releases:        66 个版本
ClawHub Skills:  10,000+
支持渠道:        20+
主语言:          TypeScript 87.4%
许可证:          MIT
```

---

## 与 CatPaw 的关系

> 作为美团 CatPaw 用户，OpenClaw 是理解 CatPaw 设计理念的重要参考。

CatPaw 与 OpenClaw 在设计上高度相似：

| 概念 | OpenClaw | CatPaw |
|------|----------|--------|
| 核心定位 | 自托管 AI Agent 网关 | 企业级 AI 助手 |
| 技能系统 | Skills（SKILL.md） | Skills（SKILL.md） |
| 渠道接入 | 20+ 消息渠道 | 大象、企业内部系统 |
| 记忆系统 | 双重记忆（短期+长期） | Memory（长期+每日） |
| 扩展市场 | ClawHub | Friday 技能市场 |
| 部署方式 | 自托管 | 企业内部部署 |

**核心洞察：** CatPaw 是 OpenClaw 理念在美团企业场景的落地实现，Skills 系统的设计几乎完全一致。理解 OpenClaw 的架构，有助于更好地使用和开发 CatPaw Skills。

---

## 学习路径建议

### 快速了解（30 分钟）

1. 读 [[01_OpenClaw概览与历史]] — 了解背景和定位
2. 看官网 https://openclaws.io — 直观感受产品

### 深入学习（2 小时）

1. 读 [[02_OpenClaw功能详解]] — 理解核心功能
2. 读 [[03_OpenClaw部署指南]] — 尝试本地部署
3. 浏览 https://docs.openclaw.ai — 官方文档

### 源码研究（1 天）

1. 读 [[05_OpenClaw代码结构与架构]] — 理解技术架构
2. Clone 仓库，阅读 `apps/gateway/` 和 `packages/` 目录
3. 参考架构设计决策，思考与数仓调度的类比

### 成为代码贡献者（持续）

1. 读 [[06_OpenClaw代码贡献者指南]] — 完整贡献流程
2. 搭建本地开发环境（Node 22+、pnpm、Bun）
3. 找 [Good First Issues](https://github.com/openclaw/openclaw/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 开始第一个 PR
4. 加入 [Discord](https://discord.gg/qkhbAGHRBT) 与社区互动

---

## 数仓视角的类比思考

作为数仓工程师，可以用熟悉的概念理解 OpenClaw：

| OpenClaw 概念 | 数仓类比 |
|--------------|---------|
| Gateway | 调度中心（如 Azkaban/DolphinScheduler） |
| Channel Adapter | 数据源连接器（JDBC、Kafka Consumer） |
| Lane Queue | 任务队列（优先级调度） |
| Skills | ETL 任务模板 |
| Memory System | 元数据存储（血缘、状态） |
| Agent Loop | 任务执行循环（重试、依赖检查） |
| Heartbeat | 调度心跳（任务就绪检测） |

> 这个类比来自 InStreet 的学习笔记：Agent 心跳机制与数仓调度心跳本质上是同构的——都是「定时拉取状态 → 判断是否有待处理任务 → 执行 → 更新状态」。

---

## 外部资源

- [GitHub 仓库](https://github.com/openclaw/openclaw)
- [官方文档](https://docs.openclaw.ai)
- [官网](https://openclaws.io)
- [Discord 社区](https://discord.gg/clawd)
- [ClawHub 技能市场](https://clawhub.io)
- [中文文档](https://openclaw.cc)
- [知乎专栏](https://www.zhihu.com/search?q=openclaw)
