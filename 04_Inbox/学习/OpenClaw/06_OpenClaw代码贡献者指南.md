# OpenClaw 代码贡献者完全指南

> 本文面向希望成为 [[00_OpenClaw_MOC|OpenClaw]] 代码贡献者的开发者，涵盖从环境搭建到 PR 合并的完整流程。
> 
> 参考来源：[CONTRIBUTING.md](https://github.com/openclaw/openclaw/blob/main/CONTRIBUTING.md) · [VISION.md](https://github.com/openclaw/openclaw/blob/main/VISION.md) · [DeepWiki](https://deepwiki.com/openclaw/openclaw/8-development)

---

## 一、项目维护者与社区结构

OpenClaw 采用"仁慈独裁者"（Benevolent Dictator）模式，由 **Peter Steinberger**（[@steipete](https://github.com/steipete)）担任最终决策者。各子系统有专属维护者：

| 维护者 | 负责领域 |
|--------|---------|
| Peter Steinberger (@steipete) | 项目总负责、核心架构 |
| Shadow (@thewilloftheshadow) | Discord 子系统、ClawHub、社区管理 |
| Vignesh (@vignesh07) | Memory (QMD)、形式化建模、TUI、IRC |
| Jos (@joshp123) | Telegram、API、Nix 模式 |
| Ayaan Zaidi (@obviyus) | Telegram 子系统、Android App |
| Tyler Yust (@tyler6204) | Agents/子代理、Cron、BlueBubbles、macOS App |
| Mariano Belinky (@mbelinky) | iOS App、安全 |
| Nimrod Gutman (@ngutman) | iOS App、macOS App |

**社区渠道：**
- Discord：https://discord.gg/qkhbAGHRBT（最活跃的讨论场所）
- GitHub Issues：https://github.com/openclaw/openclaw/issues
- X/Twitter：[@openclaw](https://x.com/openclaw)

---

## 二、开发环境搭建

### 2.1 系统要求

| 工具 | 最低版本 | 说明 |
|------|---------|------|
| Node.js | 22+ | 必须的运行时基础 |
| pnpm | 10.23.0 | 主包管理器，必须使用 lockfile |
| Bun | 1.3.9+ | [[Day2-JavaScript和TypeScript|TypeScript]] 执行和测试的首选工具 |
| Python | 3.12 | 用于 `skills/` 脚本和 CI 工具 |

> ⚠️ Node 和 Bun 两条路径都必须保持可用。修改依赖时，`pnpm-lock.yaml` 和 Bun 补丁必须保持同步。

### 2.2 克隆与初始化

```bash
# 1. Fork 仓库到自己的 GitHub 账号
# 2. 克隆 Fork
git clone https://github.com/YOUR_USERNAME/openclaw.git
cd openclaw

# 3. 添加上游远程
git remote add upstream https://github.com/openclaw/openclaw.git

# 4. 安装所有依赖（使用 lockfile）
pnpm install

# 5. 安装 pre-commit hooks（与 CI 相同的检查）
prek install
```

### 2.3 常用开发命令

| 命令 | 用途 |
|------|------|
| `pnpm install` | 安装所有依赖 |
| `pnpm openclaw ...` | 以开发模式运行 CLI（通过 Bun） |
| `pnpm dev` | 开发 CLI 运行的别名 |
| `pnpm build` | 类型检查并构建 `dist/` |
| `pnpm tsgo` | 仅 TypeScript 检查 |
| `pnpm check` | 类型 + lint + 格式化（Oxlint + Oxfmt） |
| `pnpm format` | 仅检查格式（oxfmt --check） |
| `pnpm format:fix` | 就地修复格式（oxfmt --write） |
| `pnpm test` | 运行所有测试（Vitest） |
| `pnpm test:coverage` | 带 V8 覆盖率报告的测试 |
| `pnpm release:check` | 验证 npm pack 内容 |

> 💡 **提交前必须通过 `pnpm check`**，它运行与 CI `check` 任务相同的类型/lint/格式检查。

---

## 三、代码库结构深度解析

### 3.1 Monorepo 目录结构

```
openclaw/
├── src/                    # 核心 Gateway、CLI、agents、channels、infra
│   ├── cli/                # CLI 命令连接
│   ├── commands/           # 各个 CLI 命令实现
│   ├── gateway/            # GatewayServer、协议、服务器方法
│   ├── agents/             # Agent 运行时、工具、沙箱
│   ├── auto-reply/         # 自动回复逻辑（核心！）
│   │   └── reply/          # runReplyAgent 等核心函数
│   ├── telegram/           # Telegram 频道集成
│   ├── discord/            # Discord 频道集成
│   ├── slack/              # Slack 频道集成
│   ├── infra/              # 共享基础设施工具
│   ├── media/              # 媒体处理管道
│   ├── browser/            # 浏览器控制（CDP）
│   ├── config/             # 配置加载与验证
│   └── plugins/            # 插件系统
├── extensions/             # 扩展/插件工作区包
│   └── bluebubbles/        # BlueBubbles iMessage 扩展
├── apps/
│   ├── ios/                # iOS Clawdis App（Swift）
│   ├── macos/              # macOS Clawdis App（Swift）
│   ├── android/            # Android Clawdis App（Kotlin/Gradle）
│   └── shared/             # 共享原生代码（Swift 包）
├── ui/                     # Control UI（LitElement SPA）
├── packages/               # 共享 TypeScript 包
├── skills/                 # Python skill 脚本
├── scripts/                # 构建、发布和工具脚本
├── docs/                   # Mintlify 文档源
├── test/                   # 测试夹具和集成测试
└── dist/                   # 构建输出（生成的，不提交）
```

### 3.2 核心配置文件

| 文件 | 作用 |
|------|------|
| `src/config/zod-schema.ts` | 根 Zod Schema（`OpenClawSchema`），定义所有配置结构 |
| `src/config/config.ts` | `loadConfig()` 主配置加载器 |
| `src/config/types.ts` | TypeScript 类型定义 |
| `vitest.config.ts` | 主测试配置 |
| `vitest.unit.config.ts` | 单元测试配置 |
| `vitest.gateway.config.ts` | Gateway 测试配置 |
| `vitest.channels.config.ts` | Channel 测试配置 |
| `vitest.e2e.config.ts` | E2E 测试配置 |
| `tsdown.config.ts` | 构建配置 |
| `pnpm-workspace.yaml` | Monorepo 工作区定义 |

---

## 四、核心子系统深度解析

### 4.1 Gateway 子系统

**位置：** `src/gateway/`

Gateway 是整个系统的核心进程，监听 WebSocket + HTTP 端口（默认 18789）。

**关键文件：**
- `src/gateway/startup-auth.ts` — 启动时认证逻辑
- `src/gateway/startup-auth.test.ts` — 对应测试

**配置热重载模式：**
- `hybrid` — 部分热重载，部分重启
- `hot` — 完全热重载（不重启进程）
- `restart` — 配置变更时完全重启
- `off` — 禁用自动重载

**配置加载流程：**
```
文件监视器(chokidar) → loadConfig() → parseConfigJson5() 
→ $include 解析器 → validateConfigObjectWithPlugins() 
→ Secret 解析器(SecretRef) → 运行时快照
```

### 4.2 Agent 执行管道（最重要！）

**位置：** `src/auto-reply/reply/` 和 `src/agents/pi-embedded-runner/`

这是 OpenClaw 最核心的部分，理解这个管道对贡献者至关重要。

**四层执行函数链：**

```
消息输入
    ↓
Layer 1: runReplyAgent()
  文件: src/auto-reply/reply/agent-runner.ts
  职责: 队列策略、转向注入、打字指示器、后处理
    ↓
Layer 2: runAgentTurnWithFallback()
  文件: src/auto-reply/reply/agent-runner-execution.ts
  职责: 重试循环（压缩、瞬时错误、角色排序冲突）
    ↓
Layer 3: runEmbeddedPiAgent()
  文件: src/agents/pi-embedded-runner/run.ts
  职责: 通道队列、模型解析、认证配置文件迭代
    ↓
Layer 4: runEmbeddedAttempt()
  文件: src/agents/pi-embedded-runner/run/attempt.ts
  职责: 工作区设置、工具创建、会话初始化、单次尝试
    ↓
subscribeEmbeddedPiSession()
  文件: src/agents/pi-embedded-subscribe.ts
  职责: 流式事件、块分块、标签剥离、工具回调
    ↓
模型 API（Anthropic/OpenAI/等）
```

**Layer 1 详解 — runReplyAgent：**

在调用模型之前，会运行两个早期退出检查：

1. **转向检查（Steer Check）**：如果 `shouldSteer && isStreaming` 为 true，调用 `queueEmbeddedPiMessage` 将新消息注入当前活跃的流式运行中，函数提前返回。

2. **队列策略**：`resolveActiveRunQueueAction` 返回：
   - `"drop"` — 静默丢弃消息
   - `"enqueue-followup"` — 保存到后续队列
   - `"proceed"` — 继续模型调用

**Layer 2 详解 — 错误处理与重试：**

| 错误分类器 | 来源 | 处理动作 |
|-----------|------|---------|
| `isContextOverflowError` | `pi-embedded-helpers.ts` | 触发压缩后重试 |
| `isLikelyContextOverflowError` | `pi-embedded-helpers.ts` | 同上 |
| `isCompactionFailureError` | `pi-embedded-helpers.ts` | 重置会话 ID，重试 |
| `isTransientHttpError` | `pi-embedded-helpers.ts` | 等待 2500ms，重试一次 |
| 角色排序冲突 | Google/Gemini 特有 | 重置会话 + 删除转录 |

### 4.3 Channel 子系统

**位置：** `src/telegram/`, `src/discord/`, `src/slack/` 等

每个 Channel 实现包含：
1. **Monitor** — 监听入站事件
2. **访问控制** — DM/群组策略（`dmPolicy`, `groupPolicy`）
3. **发送适配器** — 出站消息投递
4. **原生命令注册** — 平台特定命令（Discord slash、Telegram bot 菜单）

**内置 Channel 列表：**

| Channel | 包 | 配置键 | 默认 DM 策略 |
|---------|---|--------|------------|
| WhatsApp | `@whiskeysockets/baileys` | `channels.whatsapp` | `pairing` |
| Telegram | `grammy` | `channels.telegram` | `pairing` |
| Discord | `@buape/carbon` | `channels.discord` | `pairing` |
| Slack | `@slack/bolt` | `channels.slack` | `pairing` |
| Signal | signal-cli | `channels.signal` | `allowlist` |
| iMessage | imsg (legacy) | `channels.imessage` | N/A（仅 macOS） |
| BlueBubbles | HTTP API | `channels.bluebubbles` | `allowlist` |

**插件 Channel：** Google Chat、Mattermost 等通过 `plugins.entries` 加载。

### 4.4 Memory 子系统

**位置：** `src/agents/` 中的 memory 相关文件

OpenClaw 支持两种 Memory 后端：

1. **QMD（Quantum Memory Database）**：高级语义搜索，由维护者 Vignesh 开发
2. **内置 Memory**：简单的基于文件的存储

配置键：`memory.backend`（`"qmd"` 或 `"builtin"`）

### 4.5 工具系统（Tools System）

**位置：** `src/agents/` 工具相关文件

工具策略采用层级过滤：
```
全局策略 → Agent 策略 → 群组策略 → 沙箱策略
```

沙箱模式（`agents.defaults.sandbox.mode`）：
- `off` — 不使用沙箱
- `non-main` — 非主 [[07-Agent|Agent]] 使用沙箱
- `all` — 所有 Agent 使用沙箱

---

## 五、编码规范

### 5.1 语言与工具

- **TypeScript (ESM)** 贯穿全项目。严格类型；避免 `any`。
- 格式化和 lint 使用 **Oxlint** 和 **Oxfmt**。提交前运行 `pnpm check`。
- **永远不要**添加 `@ts-nocheck`。**永远不要**禁用 `no-explicit-any`。修复根本原因。

### 5.2 类与组合规则

- **不要**通过原型变异共享行为（`applyPrototypeMixins`、`Object.defineProperty` 在 `.prototype` 上）。使用显式继承或辅助组合，以便 TypeScript 可以进行类型检查。
- 在测试中，优先使用每实例存根，而不是 `SomeClass.prototype.method = ...`。

### 5.3 文件大小与结构

- 目标是将文件保持在约 700 行以下（指导原则，不是硬性限制）。
- 提取辅助函数，而不是创建文件的"V2"副本。
- 使用现有的 CLI 选项模式和通过 `createDefaultDeps` 进行依赖注入。

### 5.4 命名规范

- **OpenClaw**（大写）用于产品/应用/文档标题。
- `openclaw`（小写）用于 CLI 命令、包/二进制文件、路径和配置键。

### 5.5 UI 和进度输出

- CLI 进度：使用 `src/cli/progress.ts`（`osc-progress` + `@clack/prompts` spinner）。不要手动实现 spinner 或进度条。
- 状态输出：使用 `src/terminal/table.ts` 进行带 ANSI 安全换行的表格输出。
- 颜色调色板：使用 `src/terminal/palette.ts`（不要硬编码颜色）。

### 5.6 插件/扩展依赖

- 将插件专用依赖保留在扩展的 `package.json` 中。除非核心直接使用，否则不要将它们添加到根 `package.json`。
- `dependencies` 中的 `workspace:*` 会破坏 `npm install`。改用 `devDependencies` 或 `peerDependencies`。

---

## 六、测试规范

### 6.1 测试框架

OpenClaw 使用 **Vitest** 作为测试框架，有多个专用配置：

| 配置文件 | 测试范围 |
|---------|---------|
| `vitest.unit.config.ts` | 单元测试 |
| `vitest.gateway.config.ts` | Gateway 集成测试 |
| `vitest.channels.config.ts` | Channel 集成测试 |
| `vitest.e2e.config.ts` | 端到端测试 |
| `vitest.live.config.ts` | 实时测试（需要真实 API） |
| `vitest.extensions.config.ts` | 扩展测试 |

### 6.2 测试文件命名规范

测试文件与被测文件同名，加 `.test.ts` 后缀：
```
src/agents/auth-profiles/oauth.ts
src/agents/auth-profiles/oauth.test.ts
```

### 6.3 测试编写原则

- 每个新功能或 bug 修复都应该有对应的测试
- 优先使用每实例存根（per-instance stubs）
- 避免原型级别的 mock，除非明确记录
- 使用 `src/auto-reply/reply/test-helpers.ts` 中的测试辅助函数

### 6.4 运行测试

```bash
# 运行所有测试
pnpm test

# 运行特定范围的测试
pnpm vitest run --config vitest.unit.config.ts
pnpm vitest run --config vitest.gateway.config.ts

# 带覆盖率
pnpm test:coverage

# 监视模式（开发时）
pnpm vitest --watch
```

---

## 七、PR 提交规范

### 7.1 VISION.md 中的贡献规则（必读！）

```
1. 一个 PR = 一个 Issue/主题。不要捆绑多个不相关的修复/功能。
2. 超过约 5,000 行变更的 PR 只在特殊情况下审查。
3. 不要一次性开大量小 PR；每个 PR 都有审查成本。
4. 对于非常小的相关修复，鼓励合并到一个专注的 PR 中。
```

### 7.2 Commit 消息格式

OpenClaw 使用 **Conventional Commits** 规范：

```
<type>(<scope>): <description>

[可选的正文]

[可选的脚注]
```

**类型（type）：**
- `feat` — 新功能
- `fix` — Bug 修复
- `docs` — 文档变更
- `style` — 不影响代码含义的格式变更
- `refactor` — 既不修复 bug 也不添加功能的代码变更
- `test` — 添加或修正测试
- `chore` — 构建过程或辅助工具的变更
- `perf` — 性能改进
- `ci` — CI 配置变更

**范围（scope）示例：**
- `gateway`, `telegram`, `discord`, `agents`, `memory`, `config`, `ui`, `ios`, `android`

**示例：**
```
feat(telegram): add support for inline keyboard buttons
fix(gateway): resolve WebSocket reconnection race condition
docs(contributing): update Android app ownership
```

### 7.3 PR 流程

```
1. 从 main 分支创建功能分支
   git checkout -b feat/your-feature-name

2. 进行修改，确保：
   - pnpm check 通过（类型 + lint + 格式）
   - 相关测试通过
   - 新功能有测试覆盖

3. 提交（使用 Conventional Commits 格式）
   git commit -m "feat(scope): description"

4. 推送到你的 Fork
   git push origin feat/your-feature-name

5. 在 GitHub 上创建 PR
   - 清晰描述变更内容和原因
   - 关联相关 Issue（使用 "Fixes #123" 或 "Closes #123"）
   - 填写 PR 模板

6. 等待 CI 通过
   - 所有 GitHub Actions 检查必须通过

7. 等待代码审查
   - 维护者会审查代码
   - 根据反馈进行修改
   - 不要 force push（除非维护者要求）

8. 合并
   - 维护者合并 PR
```

### 7.4 PR 模板要点

- 清晰说明"做了什么"和"为什么这样做"
- 列出测试方法
- 截图（如果涉及 UI 变更）
- 破坏性变更说明（如果有）

---

## 八、CI/CD 流程

### 8.1 GitHub Actions 工作流

主要 CI 工作流在 `.github/workflows/ci.yml` 中定义，包含以下检查：

| 检查 | 内容 |
|------|------|
| `check` | TypeScript 类型检查 + Oxlint + Oxfmt |
| `test:unit` | 单元测试（Vitest） |
| `test:gateway` | Gateway 集成测试 |
| `test:channels` | Channel 集成测试 |
| `build` | 构建 `dist/` |
| `shellcheck` | Shell 脚本检查 |
| `actionlint` | GitHub Actions 工作流 lint |
| `detect-secrets` | 密钥泄露检测 |
| `zizmor` | GitHub Actions 安全检查 |

### 8.2 CI 变更范围检测

`scripts/ci-changed-scope.mjs` 脚本会检测 PR 中变更的文件范围，只运行相关的测试套件，加快 CI 速度。

### 8.3 Pre-commit Hooks

安装 `prek install` 后，每次提交前会自动运行：
- TypeScript 类型检查
- Oxlint
- Oxfmt 格式检查
- detect-secrets（密钥检测）

---

## 九、新手入门路径

### 9.1 推荐的第一步

1. **阅读文档**：先读 `README.md`、`CONTRIBUTING.md`、`VISION.md`、`AGENTS.md`
2. **搭建环境**：按照上面的步骤搭建开发环境
3. **运行测试**：确保所有测试通过
4. **探索代码**：从 `src/config/zod-schema.ts` 开始理解配置结构
5. **找 Good First Issues**：https://github.com/openclaw/openclaw/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

### 9.2 贡献领域建议

**适合新手的领域：**
- 文档改进（`docs/` 目录）
- 测试覆盖率提升（为现有功能添加测试）
- 小 Bug 修复（标记为 `good first issue` 的 Issues）
- 代码注释和类型改进

**中级贡献领域：**
- 新 Channel 适配器（参考现有 Channel 实现）
- 工具系统扩展
- UI 改进（`ui/` 目录，LitElement）
- 配置系统改进

**高级贡献领域：**
- Agent 执行管道优化
- Memory 系统改进
- 安全相关功能
- 性能优化

### 9.3 如何找到好的 Issue

```bash
# 在 GitHub 上搜索
# 标签: good first issue, help wanted, bug, enhancement
# 链接: https://github.com/openclaw/openclaw/issues

# 在 Discord 中询问
# 频道: #contributing 或 #dev
```

### 9.4 与社区互动

- **提问前先搜索**：Discord 历史消息和 GitHub Issues
- **在 Discord 中讨论**：大功能开始前先在 Discord 讨论方向
- **小步快跑**：先提小 PR，建立信任后再做大改动
- **响应审查**：及时回应维护者的审查意见

---

## 十、特定子系统贡献指南

### 10.1 添加新 Channel

1. 在 `src/` 下创建新目录（如 `src/matrix/`）
2. 实现 `ChannelMonitor` 接口
3. 在 `src/config/zod-schema.ts` 中添加配置 Schema
4. 在 Gateway 启动逻辑中注册 Channel
5. 添加文档到 `docs/channels/`
6. 添加测试

**参考实现：** `src/telegram/`（最完整的实现）

### 10.2 添加新工具（Tool）

1. 在 `src/agents/tools/` 中创建工具文件
2. 实现工具接口（参考现有工具）
3. 在 `ToolsSchema` 中添加配置选项
4. 在工具注册表中注册
5. 添加测试

### 10.3 创建插件（Plugin）

1. 在 `extensions/` 下创建新目录
2. 创建 `package.json`（插件专用依赖放这里）
3. 实现插件 SDK 接口（`packages/plugin-sdk`）
4. 在 `pnpm-workspace.yaml` 中注册
5. 添加文档

### 10.4 改进 UI（Control UI）

**技术栈：** LitElement（Web Components）

```bash
# 进入 UI 目录
cd ui

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 构建
pnpm build
```

---

## 十一、调试技巧

### 11.1 日志级别

```bash
# 详细日志
openclaw --verbose

# 调试模式
OPENCLAW_DEBUG=1 openclaw
```

### 11.2 配置验证

```bash
# 验证配置文件
openclaw config validate

# 查看当前配置
openclaw config show
```

### 11.3 常见问题排查

**问题：pnpm install 失败**
```bash
# 清除缓存
pnpm store prune
rm -rf node_modules
pnpm install
```

**问题：TypeScript 类型错误**
```bash
# 重新生成类型
pnpm tsgo
```

**问题：测试失败**
```bash
# 运行单个测试文件
pnpm vitest run src/path/to/test.test.ts

# 查看详细错误
pnpm vitest run --reporter=verbose
```

---

## 十二、重要文件速查

| 文件 | 重要性 | 说明 |
|------|--------|------|
| `AGENTS.md` | ⭐⭐⭐⭐⭐ | AI Agent 开发指南，包含所有编码规范 |
| `CONTRIBUTING.md` | ⭐⭐⭐⭐⭐ | 贡献指南 |
| `VISION.md` | ⭐⭐⭐⭐⭐ | 项目愿景和 PR 规则 |
| `CLAUDE.md` | ⭐⭐⭐⭐ | Claude AI 使用指南（AI 辅助开发） |
| `src/config/zod-schema.ts` | ⭐⭐⭐⭐⭐ | 所有配置的 Schema 定义 |
| `src/auto-reply/reply/agent-runner.ts` | ⭐⭐⭐⭐⭐ | Agent 执行入口 |
| `src/agents/pi-embedded-runner/run.ts` | ⭐⭐⭐⭐ | Pi Agent 运行器 |
| `package.json` | ⭐⭐⭐⭐ | 所有 npm 脚本和依赖 |

---

## 十三、相关链接

- [GitHub 仓库](https://github.com/openclaw/openclaw)
- [DeepWiki 文档](https://deepwiki.com/openclaw/openclaw)
- [Discord 社区](https://discord.gg/qkhbAGHRBT)
- [Good First Issues](https://github.com/openclaw/openclaw/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- [ClawHub Skills 市场](https://clawhub.club)
- [官方文档](https://openclaw.dev)

---

*最后更新：2026-03-14*
*参考版本：commit 8873e13f（2026-03-07 索引）*
