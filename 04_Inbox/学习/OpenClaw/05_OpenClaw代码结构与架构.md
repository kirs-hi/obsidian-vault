---
tags: [AI, OpenClaw, 代码, 架构, 技术笔记]
created: 2026-03-14
source: https://github.com/openclaw/openclaw
---

# OpenClaw 代码结构与架构

## 一、仓库目录结构

```
openclaw/openclaw/
├── .agent/
│   └── workflows/          # Agent 工作流定义
├── .agents/                # Agent 配置（已迁移到 maintainers 仓库）
├── .github/                # CI/CD 工作流、Issue 模板
├── .pi/                    # Pi Agent 相关配置
├── .vscode/                # VS Code 配置（Oxlint/Oxfmt）
├── Swabble/                # 旧版代码（重构前遗留，已更名）
├── apps/                   # 各平台应用
│   ├── gateway/            # Gateway 核心服务
│   ├── cli/                # CLI 工具
│   ├── web/                # Web Control UI
│   ├── ios/                # iOS 节点 App（Swift）
│   └── android/            # Android 节点 App（Kotlin）
├── assets/                 # 静态资源（图标、图片）
├── changelog/
│   └── fragments/          # 版本更新日志片段
├── docs/                   # 文档源文件
└── packages/               # 共享包
    ├── core/               # 核心类型和工具
    ├── channels/           # 渠道适配器
    │   ├── whatsapp/
    │   ├── telegram/
    │   ├── discord/
    │   └── ...
    ├── skills/             # 内置 Skills
    ├── memory/             # 记忆系统
    └── llm/                # LLM 后端适配器
```

---

## 二、技术栈

| 层次 | 技术 |
|------|------|
| 主语言 | TypeScript（87.4%） |
| iOS App | Swift（8.3%） |
| Android App | Kotlin（1.8%） |
| 脚本 | Shell（1.0%） |
| 样式 | CSS（0.5%） |
| 包管理 | pnpm（Monorepo） |
| 代码规范 | Oxlint + Oxfmt |
| CI/CD | GitHub Actions |
| 容器化 | Docker + docker-compose |
| 文档 | Mintlify |

---

## 三、核心子系统详解

### 1. Gateway 控制平面

Gateway 是整个系统的**神经中枢**，基于 Node.js 实现。

**核心职责：**
- WebSocket 服务器（监听 18789 端口）
- 会话状态管理（每个发送者独立会话）
- 消息路由（根据渠道和规则分发到 Agent）
- 安全控制（Token 验证、白名单过滤）
- 渠道连接管理（维护各渠道的长连接）

**关键数据流：**
```
渠道消息 → Channel Adapter → Gateway Router
    → Session Manager → Agent Queue
    → Pi Runtime → LLM API
    → 工具执行 → 结果返回
    → Gateway → Channel Adapter → 用户
```

### 2. Channel Adapters（渠道适配器）

每个消息渠道都有独立的适配器，实现统一的 `IChannel` 接口：

```typescript
interface IChannel {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  sendMessage(to: string, message: Message): Promise<void>;
  onMessage(handler: MessageHandler): void;
  getStatus(): ChannelStatus;
}
```

适配器负责：
- 处理各渠道的认证（扫码、Bot Token 等）
- 消息格式转换（各渠道格式 → 统一内部格式）
- 媒体文件处理（图片、音频、文档）
- 重连和错误处理

### 3. Pi Agent Runtime

Pi 是内置的 Agent，实现了**极简四工具**设计：

```typescript
const PI_TOOLS = {
  bash: {
    description: "Execute shell commands",
    execute: async (cmd: string) => { /* ... */ }
  },
  read_file: {
    description: "Read file contents",
    execute: async (path: string) => { /* ... */ }
  },
  write_file: {
    description: "Write file contents",
    execute: async (path: string, content: string) => { /* ... */ }
  },
  browser: {
    description: "Control browser via CDP",
    execute: async (action: BrowserAction) => { /* ... */ }
  }
};
```

**Agent Loop 实现：**
```typescript
async function agentLoop(message: string, session: Session) {
  const context = await buildContext(session);
  
  while (true) {
    const response = await llm.complete({
      messages: context.messages,
      tools: PI_TOOLS,
      system: SYSTEM_PROMPT
    });
    
    if (response.stopReason === 'end_turn') {
      return response.content;
    }
    
    // 执行工具调用
    for (const toolCall of response.toolCalls) {
      const result = await PI_TOOLS[toolCall.name].execute(toolCall.input);
      context.addToolResult(toolCall.id, result);
    }
  }
}
```

### 4. Lane Queue（并发控制）

Lane Queue 是 OpenClaw 的并发控制机制，防止同一用户的多个请求相互干扰：

```
用户 A 的消息 → Lane A → [任务1, 任务2, 任务3] → 顺序执行
用户 B 的消息 → Lane B → [任务1] → 独立执行
用户 C 的消息 → Lane C → [任务1, 任务2] → 独立执行
```

**设计原则：**
- 同一用户的请求串行执行（避免状态冲突）
- 不同用户的请求并行执行（提高吞吐量）
- 支持优先级（紧急任务可插队）

### 5. 双重记忆系统

```typescript
interface MemorySystem {
  // 短期记忆：当前会话上下文
  shortTerm: {
    messages: Message[];
    maxTokens: number;
    compress(): void;
  };
  
  // 长期记忆：持久化存储
  longTerm: {
    store(key: string, value: any): Promise<void>;
    retrieve(query: string): Promise<Memory[]>;
    search(query: string, topK: number): Promise<Memory[]>;
  };
}
```

**混合记忆搜索：**
- 关键词搜索（BM25）
- 语义搜索（向量嵌入）
- 混合排序（综合两种结果）

### 6. Skills 系统

Skills 的加载和执行流程：

```
SKILL.md 文件
    ↓ 解析元数据（名称、描述、触发条件）
    ↓ 注册到 Skill Registry
    ↓ 用户消息匹配触发条件
    ↓ 注入 Skill 内容到 System Prompt
    ↓ Pi 按照 Skill 指令执行
```

**Skill 文件结构：**
```markdown
---
name: skill-name
description: "技能描述"
triggers: ["关键词1", "关键词2"]
dependencies: ["tool1", "tool2"]
---

# Skill 名称

## 触发条件
当用户说...时使用此技能

## 执行步骤
1. 步骤一
2. 步骤二

## 注意事项
- 注意点一
```

### 7. 浏览器自动化（CDP）

OpenClaw 使用 **Chrome DevTools Protocol（CDP）** 控制浏览器，而非截图+视觉模型：

```typescript
// 生成语义化可访问性树（而非截图）
async function getPageSnapshot(page: Page): Promise<string> {
  const tree = await page.accessibility.snapshot();
  return formatAccessibilityTree(tree);
}

// 示例输出
// - button "Submit" [ref=e1]
// - input "Email" [ref=e2]: value="user@example.com"
// - link "Forgot password" [ref=e3]
```

**优势：**
- Token 消耗远低于截图分析
- 更准确的元素定位
- 支持复杂交互（拖拽、悬停等）

### 8. LLM 后端适配器

统一的 LLM 接口，支持多种提供商：

```typescript
interface LLMProvider {
  complete(request: CompletionRequest): Promise<CompletionResponse>;
  stream(request: CompletionRequest): AsyncIterable<CompletionChunk>;
  countTokens(messages: Message[]): number;
}

// 支持的提供商
const providers = {
  anthropic: new AnthropicProvider(),
  openai: new OpenAIProvider(),
  google: new GoogleProvider(),
  groq: new GroqProvider(),
  ollama: new OllamaProvider(),
  openrouter: new OpenRouterProvider(),
};
```

---

## 四、版本命名规则

OpenClaw 使用**日期版本号**：`YYYY.M.D`

```
2026.3.12  → 2026年3月12日发布
2026.1.30  → 2026年1月30日发布（正式更名 OpenClaw 当天）
```

---

## 五、CI/CD 流程

```
代码提交 → GitHub Actions 触发
    ↓
代码检查（Oxlint）
    ↓
类型检查（TypeScript）
    ↓
单元测试
    ↓
集成测试
    ↓
构建（pnpm build）
    ↓
发布（npm publish + GitHub Release）
    ↓
Docker 镜像构建推送
```

**PR 限制：** 每位作者最多同时开 10 个 PR（Issue #38283 说明了原因：防止 PR 积压，保证 Review 质量）

---

## 六、贡献指南

### 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 安装依赖（使用 pnpm）
pnpm install

# 启动开发模式
pnpm dev

# 运行测试
pnpm test

# 代码格式化
pnpm format:fix

# 类型检查
pnpm typecheck
```

### 贡献流程

1. Fork 仓库
2. 创建功能分支（`feat/your-feature`）
3. 编写代码和测试
4. 提交 PR（遵守 PR 数量限制）
5. 等待 Review（通常 1-3 天）
6. 合并到 main

### 代码规范

- 使用 **Oxlint** 进行代码检查
- 使用 **Oxfmt** 进行代码格式化
- 提交信息遵循 **Conventional Commits** 规范
- 所有 PR 需要通过 CI 检查

---

## 七、架构设计决策

### 决策一：单一 Gateway 进程

**选择：** 所有渠道共享一个 Gateway 进程，而非每个渠道独立进程。

**理由：**
- 简化部署（只需管理一个进程）
- 共享会话状态（跨渠道记忆）
- 降低资源消耗

**代价：** Gateway 崩溃影响所有渠道。

### 决策二：四工具极简主义

**选择：** Pi 只有 4 个工具（bash、read_file、write_file、browser）。

**理由：**
- 减少 LLM 工具选择的认知负担
- 降低 token 消耗
- 提高执行可靠性
- bash 工具本身可以调用任何命令行工具

**代价：** 某些场景需要通过 bash 间接实现，不如专用工具直接。

### 决策三：语义化浏览器快照

**选择：** 使用 Accessibility Tree 而非截图分析网页。

**理由：**
- 截图分析需要视觉模型，token 消耗极高
- Accessibility Tree 是结构化文本，token 消耗低
- 元素引用（@e1、@e2）使交互更精确

**代价：** 无法处理纯图片内容（如验证码）。

---

## 相关笔记

- [[01_OpenClaw概览与历史]] — 项目背景与创始人故事
- [[02_OpenClaw功能详解]] — Channels、Skills、Memory 深度解析
- [[03_OpenClaw部署指南]] — 安装、配置、Docker 部署
- [[04_OpenClaw生态与社区]] — ClawHub、社区、竞品对比

<!-- series-nav-start -->

---
**📚 OpenClaw**（6/7）

⬅️ 上一篇：[[04_OpenClaw生态与社区]] | ➡️ 下一篇：[[06_OpenClaw代码贡献者指南]]

<!-- series-nav-end -->
