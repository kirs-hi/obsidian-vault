---
tags: [AI, OpenClaw, Agent, 开源, 技术笔记]
created: 2026-03-14
source: https://github.com/openclaw/openclaw
---

# OpenClaw 概览与历史

> **"EXFOLIATE! EXFOLIATE!"** — A space lobster, probably 🦞

## 一句话定义

OpenClaw 是一个**自托管的 AI [[07-Agent|Agent]] 网关**，运行在你自己的设备上，将 WhatsApp、Telegram、Discord、iMessage 等你已经在用的聊天软件，变成随时可调用 AI 助手的入口。它不只是聊天机器人——它能**真正替你做事**。

---

## 项目基本信息

| 项目 | 信息 |
|------|------|
| GitHub | https://github.com/openclaw/openclaw |
| 官方文档 | https://docs.openclaw.ai |
| 官网 | https://openclaws.io |
| 许可证 | MIT |
| 主语言 | [[Day2-JavaScript和TypeScript|TypeScript]] 87.4%、Swift 8.3%、Kotlin 1.8%、Shell 1.0% |
| 当前版本 | 2026.3.12（截至 2026-03-14） |
| GitHub Stars | 250,000+（史上增速最快开源项目之一） |
| Contributors | 1,190+ |
| Issues（开放） | 7,391 |
| Issues（已关闭） | 11,170 |
| Releases | 66 个版本 |

---

## 创始人：Peter Steinberger

Peter Steinberger（GitHub: @steipete）是奥地利开发者，iOS 开发圈知名人物。

**人生轨迹：**

- 14 岁开始编程
- 2011 年创立 **PSPDFKit**（PDF 处理技术公司，后更名 Nutrient）
- 2021 年以约 **1 亿欧元**将 PSPDFKit 出售给 Insight Partners，退休
- 退休后陷入低谷，接受心理治疗，消失三年
- 2025 年 6 月宣布复出，成立 **Amantus Machina** 公司，专注 AI Agent 开发
- 2025 年 11 月，用 **10 天"凭感觉搓出"（vibe-coded）** 了初版 Clawdbot
- 一周内吸引 **200 万访问者**，迅速成为 GitHub 最热门 AI 项目

> 他的故事被媒体称为"燃尽、重启、爆火"——一个亿万富翁退休太空虚，复出打造了 2026 年最火开源项目。

---

## 命名历史：三次改名的故事

OpenClaw 经历了两次更名，背后牵扯商标争议、开源文化和加密货币诈骗。

```
Clawdbot（2025年11月）
    ↓ Anthropic 提出商标争议（"Claud-" 前缀）
Moltbot（2026年1月初）
    ↓ 社区反馈名字不够好记，同时出现假冒加密货币项目
OpenClaw（2026年1月30日，正式定名）
```

**时间线：**

| 时间 | 事件 |
|------|------|
| 2025-11 | Peter 用 10 天 vibe-code 出 Clawdbot，一周 200 万访问 |
| 2025-12 | GitHub Stars 突破 6 万，社区爆发式增长 |
| 2026-01 初 | Anthropic 提出商标争议，项目更名 Moltbot |
| 2026-01-28 | Peter 接受 35 分钟深度访谈，分享创业历程 |
| 2026-01-30 | 正式更名 **OpenClaw**，完成全生态统一 |
| 2026-02 | Stars 突破 14.5 万，Forks 超 2 万 |
| 2026-03 | Stars 突破 25 万，超越 React，登顶 GitHub 历史 Star 数第一 |

---

## 核心理念

### "The AI That Actually Does Things"

传统 AI 助手是**被动响应**模式：你问，它答。OpenClaw 的核心突破是**主动执行**：

```
传统模式：用户提问 → AI 回答 → 用户自己去做
OpenClaw：用户指令 → AI 理解 → AI 直接执行任务
```

### 三大核心原则

**1. 本地优先（Local-First）**
所有对话历史、工具执行记录、会话状态都保存在你自己的服务器或笔记本上，不上传任何第三方平台。

**2. 无需新 App（No New App）**
把你已经在用的即时通讯软件变成 AI 交互界面，在熟悉的聊天界面中工作。

**3. 真正执行（Actually Does Things）**
执行 shell 命令、管理文件、操作浏览器、协调多步骤工作流，无需人工审核每一步。

---

## 与同类产品的本质区别

| 维度 | ChatGPT/Claude.ai | AutoGPT | OpenClaw |
|------|-------------------|---------|----------|
| 部署方式 | 云端托管 | 本地/云端 | 本地自托管 |
| 数据隐私 | 上传云端 | 本地 | 完全本地 |
| 交互入口 | 专属 App/网页 | 命令行/网页 | 你已有的聊天软件 |
| 执行能力 | 有限工具调用 | 自主执行 | 自主执行 + 多渠道 |
| 持续运行 | 按需启动 | 按需启动 | 7×24 小时常驻 |
| 扩展方式 | 插件市场 | 自定义工具 | Skills 生态（10,000+） |
| 多平台支持 | 单一平台 | 单一平台 | 20+ 消息渠道 |

---

## 相关笔记

- [[02_OpenClaw功能详解]] — Channels、Skills、Memory 深度解析
- [[03_OpenClaw部署指南]] — 安装、配置、Docker 部署
- [[04_OpenClaw生态与社区]] — ClawHub、社区、竞品对比
- [[05_OpenClaw代码结构与架构]] — 仓库目录、技术架构图
- [[00_OpenClaw_MOC]] — 知识地图索引
