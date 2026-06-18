---
tags: [AI, OpenClaw, Agent, 功能, 技术笔记]
created: 2026-03-14
source: https://docs.openclaw.ai
---

# OpenClaw 功能详解

## 整体架构概览

OpenClaw 的核心是一个**单一 Gateway 进程**，它是所有会话、路由和渠道连接的唯一真相来源。

```
┌─────────────────────────────────────────────────────┐
│                   消息渠道层                          │
│  WhatsApp  Telegram  Discord  iMessage  Slack  ...   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Gateway（网关）                     │
│  会话管理 │ 消息路由 │ 渠道适配 │ 安全控制            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Pi Agent Runtime                   │
│  LLM 调用 │ 工具执行 │ 记忆系统 │ Skills 调度        │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   CLI 工具       Web Control UI   移动端 Nodes
                                (iOS / Android)
```

---

## 一、Gateway（网关）

Gateway 是 OpenClaw 的**控制平面**，负责：

- 接收来自各渠道的消息
- 维护每个发送者的会话状态
- 将消息路由到对应的 Agent
- 管理 WebSocket 连接
- 执行安全策略（白名单、Token 验证）

**启动命令：**
```bash
openclaw gateway --port 18789
```

**默认访问地址：** `http://127.0.0.1:18789/`

**配置文件位置：** `~/.openclaw/openclaw.json`

**基础配置示例：**
```json
{
  "channels": {
    "whatsapp": {
      "allowFrom": ["+15555550123"],
      "groups": {
        "*": { "requireMention": true }
      }
    }
  },
  "messages": {
    "groupChat": {
      "mentionPatterns": ["@openclaw"]
    }
  }
}
```

---

## 二、支持的消息渠道（Channels）

OpenClaw 支持 **20+ 消息渠道**，分为内置渠道和插件渠道两类。

### 内置渠道（开箱即用）

| 渠道 | 说明 |
|------|------|
| **WhatsApp** | 通过 WhatsApp Web 协议接入，扫码配对 |
| **Telegram** | 通过 Bot API 接入，需创建 Bot Token |
| **Discord** | 通过 Discord Bot 接入 |
| **iMessage** | macOS 专属，通过 BlueBubbles 或原生接入 |
| **Signal** | 端对端加密消息 |
| **Slack** | 企业协作工具 |
| **Google Chat** | Google Workspace 集成 |
| **Microsoft Teams** | 企业协作工具 |
| **Matrix** | 去中心化开源协议 |
| **IRC** | 经典互联网聊天协议 |

### 插件渠道（需额外安装）

| 渠道 | 说明 |
|------|------|
| **Feishu（飞书）** | 字节跳动企业协作工具 |
| **LINE** | 亚洲流行即时通讯 |
| **Mattermost** | 开源企业通讯 |
| **Nextcloud Talk** | 自托管视频会议 |
| **Nostr** | 去中心化社交协议 |
| **Synology Chat** | 群晖 NAS 内置聊天 |
| **Tlon** | 去中心化平台 |
| **Twitch** | 直播平台聊天 |
| **Zalo** | 越南流行即时通讯 |
| **WebChat** | 通用 Web 聊天界面 |

### 渠道配对流程（以 WhatsApp 为例）

```bash
# 1. 安装 OpenClaw
npm install -g openclaw@latest

# 2. 初始化并安装服务
openclaw onboard --install-daemon

# 3. 配对 WhatsApp
openclaw channels login

# 4. 启动 Gateway
openclaw gateway --port 18789
```

---

## 三、Pi Agent Runtime

**Pi** 是 OpenClaw 内置的 AI Agent 运行时，由 Mario Zechner 创建。

### Pi 的四工具极简主义

Pi 的设计哲学是"四工具极简"——只用 4 个核心工具完成所有任务：

| 工具 | 功能 |
|------|------|
| `bash` | 执行 shell 命令 |
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件内容 |
| `browser` | 控制浏览器（截图、点击、填表） |

这种极简设计的好处：
- 减少 LLM 的工具选择困惑
- 降低 token 消耗
- 提高执行可靠性

### Agent Loop（执行循环）

```
用户消息
    ↓
Gateway 接收 → 路由到 Pi
    ↓
Pi 分析任务
    ↓
选择工具执行
    ↓
观察结果
    ↓
继续执行 or 返回结果
    ↓
Gateway 发送回复到渠道
```

### 支持的 LLM 后端

OpenClaw 是**模型无关**的，支持：

| 提供商 | 模型示例 |
|--------|---------|
| Anthropic | Claude 3.5 Sonnet、Claude 3 Opus |
| OpenAI | GPT-4o、GPT-4 Turbo |
| Google | Gemini 1.5 Pro |
| Groq | Llama 3、Mixtral |
| Ollama | 本地模型（完全离线） |
| OpenRouter | 统一 API 接入多模型 |

**官方推荐：** 使用最新一代最强模型（如 Claude 3.5 Sonnet）以获得最佳质量和安全性。

---

## 四、Skills 系统

Skills 是 OpenClaw 的**模块化能力扩展系统**，类似于 AI 的"插件"。

### 什么是 Skill？

Skill 是一个 Markdown 文件（`SKILL.md`），描述：
- 这个技能做什么
- 什么时候触发
- 如何配置和使用
- 依赖哪些工具

```markdown
---
name: daily-report
description: "每天自动生成工作日报"
---

# Daily Report Skill
当用户说"生成日报"时，自动汇总今日工作内容...
```

### ClawHub：技能市场

**ClawHub** 是 OpenClaw 的官方技能市场，截至 2026 年 3 月已有：

- **10,000+** 社区构建的技能插件
- 覆盖基础工具、生产力、知识管理、搜索研究、媒体创作等全场景

**安装技能：**
```bash
# 从 ClawHub 安装
openclaw skills install daily-report

# 查看已安装技能
openclaw skills list

# 查看技能详情
openclaw skills info daily-report
```

### 高频实用 Skills 推荐

| 技能 | 功能 |
|------|------|
| `daily-report` | 自动生成每日工作报告 |
| `web-search` | 联网搜索并总结 |
| `github-review` | 自动 Review GitHub PR |
| `gmail-manager` | 管理 Gmail 收件箱 |
| `calendar-sync` | 日历事件管理 |
| `file-organizer` | 智能整理文件 |
| `code-reviewer` | 代码审查助手 |
| `meeting-notes` | 会议记录自动生成 |
| `hue-control` | 控制飞利浦 Hue 灯光 |
| `wine-cellar` | 酒窖管理（社区示例） |

### MCP 集成

OpenClaw 支持 **MCP（Model Context Protocol）**，可以接入任何 MCP 兼容的工具服务器，大幅扩展能力边界。

---

## 五、记忆系统（Memory）

OpenClaw 实现了**双重记忆系统**，解决 LLM 上下文窗口有限的问题。

### 短期记忆（Context Memory）

- 存储在当前会话的上下文窗口中
- 包含最近的对话历史
- 随会话结束而清空

### 长期记忆（Persistent Memory）

- 存储在本地文件系统
- 跨会话持久化
- 支持语义搜索（混合记忆搜索）

**记忆存储位置：** `~/.openclaw/memory/`

### 语义化浏览器快照

Pi 在执行浏览器任务时，不是截图后用视觉模型分析，而是生成**语义化的可访问性树（Accessibility Tree）**，大幅降低 token 消耗，提高准确性。

---

## 六、多 Agent 路由

OpenClaw 支持**多 Agent 并行运行**，每个 Agent 有独立的会话空间。

### 路由规则

```json
{
  "agents": {
    "work": {
      "channels": ["slack", "teams"],
      "skills": ["code-reviewer", "github-review"]
    },
    "personal": {
      "channels": ["whatsapp", "telegram"],
      "skills": ["daily-report", "calendar-sync"]
    }
  }
}
```

### Lane Queue（并发控制）

OpenClaw 使用 **Lane Queue** 机制控制并发：
- 每个发送者有独立的执行队列
- 防止任务相互干扰
- 支持优先级调度

---

## 七、Web Control UI

浏览器端控制面板，提供：

- **聊天界面**：直接与 Agent 对话
- **会话管理**：查看所有活跃会话
- **配置管理**：可视化修改配置
- **节点管理**：管理 iOS/Android 节点
- **日志查看**：实时查看执行日志

**访问地址：** `http://127.0.0.1:18789/`

---

## 八、移动端 Nodes

OpenClaw 支持配对 **iOS 和 Android 设备**作为节点，解锁：

- **Canvas**：在手机上查看 Agent 生成的内容
- **摄像头**：让 Agent 看到你的摄像头画面
- **语音**：语音输入和输出
- **设备操作**：控制手机上的应用

**iOS 配对：**
```bash
openclaw nodes pair --platform ios
```

---

## 九、媒体支持

OpenClaw 支持在消息中发送和接收：

- 图片（PNG、JPEG、GIF）
- 音频（MP3、WAV、语音消息）
- 文档（PDF、Word、Excel）
- 视频（部分渠道）

---

## 相关笔记

- [[01_OpenClaw概览与历史]] — 项目背景与创始人故事
- [[03_OpenClaw部署指南]] — 安装、配置、Docker 部署
- [[04_OpenClaw生态与社区]] — ClawHub、社区、竞品对比
- [[05_OpenClaw代码结构与架构]] — 仓库目录、技术架构图

<!-- series-nav-start -->

---
**📚 OpenClaw**（3/7）

⬅️ 上一篇：[[01_OpenClaw概览与历史]] | ➡️ 下一篇：[[03_OpenClaw部署指南]]

<!-- series-nav-end -->
