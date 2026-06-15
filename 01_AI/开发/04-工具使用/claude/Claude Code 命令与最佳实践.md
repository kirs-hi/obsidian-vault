# Claude Code 命令与最佳实践

> 按使用优先级排序，覆盖 CLI 命令、斜杠命令、快捷键、环境变量、Hooks 和工作流最佳实践。
> 来源：Claude Code 官方文档 + 社区实践总结（2025.07）

---

## 一、核心理念

Claude Code 是 agentic 编码环境，不是聊天机器人。它能读文件、跑命令、改代码、自主解决问题。最重要的约束是**上下文窗口**——填满后性能显著下降。所有最佳实践都围绕「高效利用上下文」展开。

---

## 二、三种命令形态

| 形态 | 触发位置 | 示例 |
|------|---------|------|
| CLI 命令 | 终端启动时 | `claude`、`claude -p "query"` |
| 斜杠命令 | 交互会话内输入 `/` | `/init`、`/compact`、`/model` |
| 键盘快捷键 | 会话期间直接按键 | `Ctrl+C`、`Shift+Tab`、`Esc Esc` |

---

## 三、CLI 命令（按优先级）

### P0：每天都用

| 命令 | 说明 | 示例 |
|------|------|------|
| `claude` | 启动交互式会话 | `claude` |
| `claude "query"` | 带初始提示词启动 | `claude "explain this project"` |
| `claude -c` | 恢复当前目录最近会话 | `claude -c` |
| `claude -p "query"` | 一次性查询后退出（适合脚本/CI） | `claude -p "explain this function"` |
| `cat file \| claude -p` | 管道输入处理 | `cat logs.txt \| claude -p "explain"` |
| `claude update` | 更新到最新版本 | `claude update` |

### P1：进阶使用

| 命令 | 说明 | 示例 |
|------|------|------|
| `claude -r "session"` | 按 ID/名称恢复指定会话 | `claude -r "auth-refactor" "finish PR"` |
| `claude agents` | 打开 Agent 视图管理并行会话 | `claude agents --json` |
| `claude attach <id>` | 接入后台会话 | `claude attach 7c5dcf5d` |
| `claude logs <id>` | 查看后台会话日志 | `claude logs 7c5dcf5d` |
| `claude mcp` | 配置 MCP 服务器 | `claude mcp add server-name` |
| `claude plugin` | 管理插件 | `claude plugin list` |
| `claude auth login` | 登录认证 | `claude auth login --console` |
| `claude daemon status` | 查看后台 supervisor 状态 | `claude daemon status` |

### P2：特殊场景

| 命令 | 说明 |
|------|------|
| `claude install [version]` | 安装指定版本（`stable`/`latest`/版本号） |
| `claude auto-mode defaults` | 打印 auto mode 分类规则 |

---

## 四、CLI 标志（Flags）

### 常用标志

| 标志 | 说明 |
|------|------|
| `--print` / `-p` | 非交互式一次查询 |
| `--continue` / `-c` | 继续最近会话 |
| `--resume` / `-r` | 恢复指定会话 |
| `--output-format json` | JSON 格式输出（适合脚本解析） |
| `--model <model>` | 指定模型 |
| `--permission-mode <mode>` | 设置权限模式 |
| `--effort <level>` | 设置推理努力程度 |

### System Prompt 标志

| 标志 | 说明 | 推荐度 |
|------|------|--------|
| `--append-system-prompt` | 追加自定义指令（保留默认能力） | 推荐 |
| `--system-prompt` | 完全替换默认指令 | 慎用 |

### 危险标志

| 标志 | 说明 |
|------|------|
| `--dangerously-skip-permissions` | 跳过所有权限确认，仅限可信容器环境 |

---

## 五、斜杠命令（按使用优先级）

### P0：每日必用（核心 10 个）

| 命令 | 功能 | 使用时机 |
|------|------|---------|
| `/init` | 创建 CLAUDE.md 项目记忆文件 | 新项目首次使用 |
| `/compact [focus]` | 压缩上下文，回收空间 | 上下文 70-80% 时主动执行 |
| `/clear [name]` | 硬重置，清空对话 | 切换到完全不同的任务 |
| `/model [name]` | 切换模型（sonnet/opus/haiku） | 根据任务复杂度切换 |
| `/diff [file]` | 查看当前会话的 git diff | 提交前审查改动 |
| `/context` | 查看上下文窗口使用百分比 | 定期检查，70%+ 就该压缩 |
| `/cost` | 查看 Token 消耗和费用 | 控制开销 |
| `/help` | 列出所有可用斜杠命令 | 查命令 |
| `/memory` | 打开 CLAUDE.md 编辑 | 会话中途追加规则 |
| `/resume` | 从列表恢复过去会话 | 继续之前的工作 |

### P1：进阶命令

| 命令 | 功能 | 使用时机 |
|------|------|---------|
| `/plan` | 切换计划模式（只读不执行） | 复杂变更前先看方案 |
| `/btw <question>` | 不打断主任务的附带提问 | 任务执行中想问别的 |
| `/branch [name]` | 创建对话分支探索想法 | 实验性重构 |
| `/rewind` | 回退对话和/或代码 | 批准了错误更改 |
| `/effort <level>` | 调整推理深度 | 简单任务用低effort节省token |
| `/permissions` | 管理自动审批规则 | 配置哪些操作免确认 |
| `/agents` | 管理子 Agent | 并行处理子任务 |
| `/background` | 将当前会话转为后台运行 | 释放终端继续做别的 |
| `/batch <instruction>` | 大规模并行修改 | 跨文件重构（自动拆分工作单元） |
| `/code-review [effort]` | 代码审查（只读） | 提交前检查bug |
| `/review` / `/security-review` | 深度审查/安全审查 | 上线前安全检查 |

### P2：辅助命令

| 命令 | 功能 |
|------|------|
| `/add-dir <path>` | 添加工作目录 |
| `/chrome` | 配置 Chrome 扩展 |
| `/claude-api [migrate]` | 加载 API 参考/迁移模型版本 |
| `/doctor` / `/debug` | 诊断安装和运行问题 |
| `/feedback` | 报告 bug（附带会话上下文） |
| `/teleport` | 将 web 会话拉到终端 |
| `/remote-control` | 从其他设备继续本地会话 |
| `/autofix-pr` | 自动修复 PR（CI 失败/Review 评论） |

---

## 六、键盘快捷键

### 核心快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 取消当前生成 |
| `Ctrl+R` | 搜索命令历史 |
| `Tab` | 切换 thinking 显示 |
| `Shift+Tab` | 循环模式：normal → auto-accept → plan |
| `Esc Esc` | 打开回退菜单（rewind） |
| `Ctrl+T` | 切换任务列表显示 |
| `Ctrl+G` | 在编辑器中打开计划 |

### 编辑与导航

| 快捷键 | 功能 |
|--------|------|
| `Shift+Enter` | 多行输入（不发送） |
| `Ctrl+L` | 清屏（不清对话） |
| `Ctrl+D` | 退出 Claude Code |
| `Alt+M` | 切换模式（同 Shift+Tab） |

> macOS 需在终端设置中将 Option 键配为 Meta 键（iTerm2: Settings → Profiles → Keys → "Esc+"）

---

## 七、三种权限模式

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| Normal | 每次工具执行前确认 | 默认模式，安全 |
| Auto-Accept | 无需确认直接执行 | 写测试、生成样板代码 |
| Plan Mode | 只展示方案，审批后执行 | 配置/数据库迁移等关键操作 |

切换方式：`Shift+Tab` 循环，或 `/plan` 命令。

---

## 八、CLAUDE.md 配置最佳实践

CLAUDE.md 是 Claude 的「项目记忆」，每次会话启动时自动加载。

### 内容建议

```markdown
# CLAUDE.md

## 项目描述
[简短描述项目是什么]

## 技术栈
- 语言/框架/数据库

## 代码风格
- 使用 async/await，不用 promises
- 所有数据库查询必须有错误处理
- API 返回结构化错误: { error: string, code: number }

## 测试规范
- 所有 API 端点必须有测试
- 使用 Jest，不用 Mocha
- 避免 mock，优先集成测试

## 常用命令
- `npm run dev` — 开发服务器
- `npm test` — 运行测试
- `npm run lint` — 代码检查
```

### 层级结构

| 位置 | 作用域 | 用途 |
|------|--------|------|
| `~/.claude/CLAUDE.md` | 全局所有项目 | 个人偏好（编码风格等） |
| `项目根/CLAUDE.md` | 当前项目 | 项目规范、技术栈 |
| `子目录/CLAUDE.md` | 特定模块 | 模块专属约定 |

### 快速追加记忆

在对话中输入 `#` 前缀的内容会直接追加到 CLAUDE.md：

```
# Use async/await for all database queries
```

---

## 九、Hooks（钩子）

Hooks 在特定事件前后自动执行脚本，无需 Claude 参与。

### 可用钩子事件

| 事件 | 触发时机 |
|------|---------|
| `PreToolUse` | 工具执行前 |
| `PostToolUse` | 工具执行后 |
| `Notification` | 通知发送时 |
| `Stop` | Claude 停止响应时 |

### 配置示例（`.claude/settings.json`）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "command": "npm run lint --fix $CLAUDE_FILE_PATH"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "npm run format $CLAUDE_FILE_PATH"
      }
    ]
  }
}
```

### 典型用途

- 写文件后自动 lint/format
- 提交前自动跑测试
- 敏感操作前触发审核通知

---

## 十、MCP（Model Context Protocol）

MCP 让 Claude 连接外部服务获取上下文和执行操作。

### 配置方式

```bash
# 添加 MCP 服务器
claude mcp add <server-name> -- <command> [args...]

# 列出已配置的 MCP 服务器
claude mcp list

# 移除 MCP 服务器
claude mcp remove <server-name>
```

### 常用 MCP 场景

- 数据库查询（Supabase、PostgreSQL）
- 知识库搜索
- 项目管理工具集成
- 文件系统扩展操作

---

## 十一、工作流最佳实践（按优先级）

### P0：必须遵守

**1. 给 Claude 验证自身工作的方式**

这是单一最高杠杆的实践。提供测试、截图、期望输出让 Claude 自我检查。

| 坏 | 好 |
|---|---|
| "实现邮箱验证函数" | "写 validateEmail 函数，测试: user@example.com→true, invalid→false。写完跑测试" |
| "修复构建失败" | "构建报错 [贴错误]。修复并验证构建成功，解决根因不要抑制错误" |

**2. 先探索、再计划、再编码**

```
Plan Mode 探索 → Plan Mode 制定方案 → Normal Mode 实现 → 提交
```

不确定方案时才用 Plan Mode。如果能一句话描述 diff，直接做。

**3. 提供具体上下文**

- 用 `@` 引用文件，不用口头描述位置
- 贴截图/图片直接拖入
- 指定约束："避免 mock"、"遵循 HotDogWidget.php 的模式"
- 描述症状 + 可能位置 + 修复标准

### P1：显著提效

**4. 主动管理上下文**

- `/context` 定期检查用量
- 70-80% 时执行 `/compact`
- 切换任务用 `/clear`
- 长任务用 `/compact retain <重要内容>` 定向保留

**5. 及早纠正**

Claude 开始偏离方向时立即 `Ctrl+C` 打断重新引导，比等它做完再改成本低得多。

**6. 模型策略**

- 日常用 Sonnet（性价比最优）
- 复杂架构/多步规划切 Opus
- 琐碎任务/样板代码用 Haiku
- 切换命令：`/model sonnet` / `/model opus` / `/model haiku`

**7. 用子 Agent 并行化**

```
/batch migrate src/ from Solid to React
```

自动分解为 5-30 个独立单元，每个在隔离 worktree 中并行执行。

### P2：锦上添花

**8. 利用 `/btw` 保持专注**

主任务执行中需要问别的？用 `/btw` 不污染上下文。

**9. 善用 checkpoint 和 rewind**

`Esc Esc` 打开回退菜单，可以只回退代码不回退对话（或反之）。

**10. 非交互模式做自动化**

```bash
# CI/CD 中使用
claude -p "check for type errors" --output-format json
# 管道处理
cat error.log | claude -p "diagnose this error"
```

---

## 十二、常见反模式（要避免）

| 反模式 | 正确做法 |
|--------|---------|
| 等上下文满了才压缩 | 70% 就主动 `/compact` |
| 一个超长会话做所有事 | 按任务切分，用 `/clear` 重置 |
| 模糊指令 "修一下 bug" | 给症状+位置+验证标准 |
| 不审查直接提交 | `/diff` → 审查 → `/code-review` → 提交 |
| 等 Claude 做完才纠正 | 发现偏离立即 `Ctrl+C` |
| 所有任务都用 Opus | 日常 Sonnet，复杂才升 Opus |

---

## 十三、环境变量速查

| 变量 | 作用 |
|------|------|
| `ANTHROPIC_MODEL` | 默认模型 |
| `ANTHROPIC_BASE_URL` | API 代理地址 |
| `CLAUDE_CODE_TASK_LIST_ID` | 跨会话共享任务列表 |
| `CLAUDE_CODE_FORK_SUBAGENT` | 启用 fork 子 Agent |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | 启用 Teams 模式 |

---

## 十四、美团内网特殊配置

| 项        | 配置                                                         |
| -------- | ---------------------------------------------------------- |
| 启动方式     | `mc --code`（CatPaw CLI，自动注入代理和 Token）                      |
| API 代理   | `ANTHROPIC_BASE_URL=https://mcli.sankuai.com`              |
| 模型切换     | `/model` 或修改 `~/.claude/settings.json` 中 `ANTHROPIC_MODEL` |
| Teams 模式 | 必须通过 `mc --code` 启动，原生 `claude` 会被代理拦截                     |
| 危险启动方式   | mc --code --dangerously-skip-permissions                   |
|          |                                                            |

---

## 参考链接

- [官方文档 - Best Practices](https://code.claude.com/docs/en/best-practices)
- [官方文档 - CLI Reference](https://code.claude.com/docs/en/cli-reference)
- [官方文档 - Commands](https://code.claude.com/docs/en/commands)
- [官方文档 - Hooks](https://code.claude.com/docs/en/hooks)
- [社区 - 命令体系解析 50+](https://developer.aliyun.com/article/1718322)
