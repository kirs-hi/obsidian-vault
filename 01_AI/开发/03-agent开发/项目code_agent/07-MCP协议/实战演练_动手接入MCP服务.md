# 第7章：实战篇

## 本章需要做什么 ？

上一章我们给 MewCode 装上了权限系统， 五层权限拦截 让工具调用变得安全可控。但你有没有发现一个问题：MewCode 能用的工具，全部是你亲手写的。ReadFile、WriteFile、Bash、Grep、Glob，每一个都编译进二进制，想加新工具就得改代码、重新发版。

这一章要让 MewCode 从「封闭工具集」变成「开放工具生态」。做完之后，用户在配置文件里声明一个 MCP Server，MewCode 就能自动接入它提供的工具，不用改一行代码。GitHub Issue 查询、数据库操作、Slack 消息，社区写好了 MCP Server，直接接进来就能用。

具体要新增这些东西：

-   **JSON-RPC** **2.0 协议类型** ：请求、响应、通知三种消息的编解码
-   **Transport 抽象 + 两种实现** ：stdio（子进程管道通信）和 Streamable HTTP（远程 Server）
-   **MCP** **Client** ：初始化握手、工具发现、工具调用、请求-响应异步匹配
-   **MCPToolWrapper** ：适配器，把 MCP 工具包装成 MewCode 内部的 Tool 接口
-   **MCP Manager** ：连接缓存、配置合并、生命周期管理
-   **环境变量****隔离** ：子进程只拿到 PATH + 显式声明的变量，不泄露敏感信息

这章 **不做** ：SSE 流式推送、Resources/Prompts 消费、Sampling/Elicitation 等 Client 侧高级能力。

---

## Vibe Coding 实战

### 生成三份文档

把任务换成本章的内容：

```plain
# 我的初步想法
- 实现一个客户端，按 JSON-RPC 2.0 的消息格式跟外部 server 通信
- 至少支持两种传输方式：本地子进程 stdio、远程 Streamable HTTP
- 一次会话分三个阶段：连接初始化握手 → 工具列表发现 → 工具调用
- 消息是双向的，需要处理请求-响应的异步匹配（每个请求带 id，回包按 id 关联）
- 写一个适配层把发现到的远端工具包装成 MewCode 已有的 Tool 接口，注册进工具中心，Agent 调用时无感
- 多个 server 的连接做缓存或池化，避免每次工具调用都重连
- 配置在哪里声明 server 列表（命令、URL、env、超时）需要在 spec 阶段定下来
```

然后 AI 就会开始问你问题，进行需求澄清。

你根据理论篇学到的内容回答这些问题，一直这样反复循环对齐需求，最后就能生成三份文档了。

### 正式开发

三份文档有了之后，就相当于施工图纸已经定好了，然后让 Claude Code 根据这三份文档进行开发

![](实战演练_动手接入MCP服务-1.jpeg)

经过一段时间后，开发完成。

![](实战演练_动手接入MCP服务-2.jpeg)

### 功能验证过程

来验收一下结果，现在配置里加上我们的context7 mcp，

config里配置如下

mcp\_servers:

\- name: context7

command: npx

args: ["-y", "@upstash/context7-mcp"]

![](实战演练_动手接入MCP服务-3.jpeg)

然后启动MewCode，如果连接正常的话，ui会显示连接正常，以及注册的工具

![](实战演练_动手接入MCP服务-4.jpeg)

跟它说

用context7mcp 查看最新的eino的文档

我们可以看到模型决定调用 MCP 工具，MewCode 通过 MCP 协议把请求转给外部 Server，Server 执行后返回结果，模型基于结果回答。

![](实战演练_动手接入MCP服务-5.jpeg)

整个过程对模型来说，MCP 工具和内置工具没有任何区别。

要说内部Function Calling和MCP的一个大差别就是MCP更像是外部生态的一个工具注册中心，对于互联网上的系统而言，是打破生态孤岛的一个重要手段，将一个个生态链接起来，形成更加庞大强大的大生态。

验收没问题，那么本章的主要任务就完成了。下一章，我们给 MewCode 加上上下文管理能力。

---

## 参考提示词和代码

如果你在澄清需求的过程中遇到困难，或者生成的三份文件效果不理想，可以直接使用下面的参考版本。

把下面三个文件保存到项目根目录，然后告诉你的 AI 编程助手：

提示词如果需要复制，移步到这里：[提示词复制](https://www.yuque.com/tianming-uvfnu/gmmfad/itzxbg44a5upp43u)

### Go

```plain
# ch07: MCP Protocol Spec

## 1. 背景

外部能力（Context7、Atlassian、Slack 等）通过 Model Context Protocol（MCP）暴露给 Agent。如果没有 MCP 客户端实现，MewCode 就只能依赖内置的六个工具，无法接入生态里已有的几百个 MCP server，等于砍掉一大块工具生态。MCP 规范定义了 JSON-RPC 2.0 之上的握手 → 工具发现 → 工具调用三阶段会话，需要本章把这三阶段、两种传输（stdio / Streamable HTTP，含兼容 SSE）以及到 `tools.Tool` 接口的适配器实现，并接到 TUI 的启动流程里。

## 2. 目标

交付一个能在 MewCode 启动时按配置批量连接外部 MCP server、把每个 server 暴露的工具注册到全局 tool registry 的客户端。具体能力：单服务器 `Client` 封装（Connect / ListTools / CallTool / Close）；多服务器 `Manager` 封装（LoadConfigs / ConnectAll / RegisterAllTools / Shutdown）；`MCPToolWrapper` 把每个 MCP tool 适配到 MewCode 的 `tools.Tool` 接口；工具名做命名空间消毒。最终效果是用户在 TUI 里看到 MCP server 的工具与内置工具并列，能直接被 LLM 调用。

## 3. 功能需求

- F1: 服务器配置同时支持 stdio（命令 + 参数 + 环境变量）和 HTTP（URL + 传输类型 + 头部）两种传输。
- F2: HTTP 传输按 transport 字段路由到 Streamable HTTP 或兼容 SSE。
- F3: stdio 子进程的 stderr 必须重定向丢弃，避免 OSC 颜色查询污染父 TTY 输入。
- F4: HTTP 请求头通过自定义 RoundTripper 注入，并对 header 值做环境变量展开，方便从 ENV 取 API key。
- F5: 单服务器客户端实现 Connect → ListTools → CallTool → Close 四阶段，所有调用复用同一个 SDK session。
- F6: 多服务器连接做批量并入，单个失败收集错误但不阻塞其他 server。
- F7: 工具名按 `mcp__<server>__<tool>` 命名，server 名和 tool 名都做命名空间消毒（非 `[A-Za-z0-9_]` 字符替换为下划线），保证 LLM API 的 tool name 合法。
- F8: 工具包装器 Execute 把 MCP 返回的文本内容列表拼成字符串，把 `IsError` 透传到 `tools.ToolResult.IsError`，无输出时回填占位文本。
- F9: 提供 RegisterAllTools 把所有 wrapper 注册到 `tools.Registry`，并返回连接错误清单供 TUI 显示。
- F10: TUI 启动时走异步连接，连接结果通过事件回到主线程注册到 registry。

## 4. 非功能需求

- N1: 连接是异步的（在 TUI 后台 goroutine 里执行），不阻塞 TUI 启动。
- N2: 单个 server 连接失败要打日志并写入错误清单，其他 server 继续连。
- N3: 工具名转换必须保证 LLM API 的 tool name 合法性（只允许字母数字和下划线）。
- N4: 复用官方 MCP Go SDK，不要手写 JSON-RPC 帧格式。
- N5: Shutdown 必须幂等，能在 TUI 退出时清理所有连接。

## 5. 设计概要

- 核心数据结构:
 - `ServerConfig`：YAML 反序列化结构体，承载 name / command / args / env / url / transport / headers。
 - `Client`：单 server 的会话句柄，持有配置 + SDK session + SDK client。
 - `Manager`：多 server 调度，持有配置集合与已连接客户端集合。
 - `ConnectResult`：`ConnectAll` 的返回类型，含 manager / 工具列表 / server 列表 / 错误清单。
 - `MCPToolWrapper`：把 MCP tool 适配到 MewCode 的 `tools.Tool` 接口。
- 主流程（调用链）:
 - TUI 启动读 config 拿到 MCP server 列表 → 异步走 `Manager.LoadConfigs` + `ConnectAll`。
 - 对每个 server `NewClient(cfg).Connect`：按 stdio / Streamable HTTP / SSE 三种 transport 选择 SDK transport，发起握手，拿 session。
 - `ListTools` 拿工具列表，包成 `MCPToolWrapper`。
 - TUI 收到完成事件后把工具批量注册到 `tools.Registry`。
 - LLM 调用工具时按 `mcp__<server>__<tool>` 找到 wrapper，`Execute` 走 session 上的 `tools/call`。
- 与其他模块的交互:
 - 依赖 `internal/tools`（注册到全局 registry、实现 `Tool` 接口）。
 - 依赖官方 MCP Go SDK。
 - 被 `internal/tui` 在启动流程中调用。
 - 依赖 `internal/config` 提供反序列化目标，TUI 把 config 字段拷到 `ServerConfig`。

## 6. Out of Scope

- OAuth / 鉴权刷新：本仓库只做静态 header 注入，不实现 OAuth step-up 401 处理。
- 连接缓存：每次启动重新连接，不做跨进程缓存。
- IDE 集成（双向 SSE / WebSocket / 进程内 transport）。
- MCP resources / prompts / sampling 三种非 tool 能力：只暴露 `tools/list` + `tools/call`。
- 服务器健康检查与自动重连：断了由用户重启 MewCode。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch07: MCP Protocol Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。本章已课程核对完成，所有 T 任务标记 [x]，每条任务记录实际落地的文件与行号。

## T1: 定义 `ServerConfig` 与传输选择
- 影响文件: `internal/mcp/mcp.go`（行 21~44）
- 依赖任务: 无
- 完成标准: `ServerConfig` 字段含 `Name / Command / Args / URL / Transport / Headers / Env`，`IsStdio` 与 `transportKind` 分流逻辑存在。

## T2: 实现 HTTP 头部注入
- 影响文件: `internal/mcp/mcp.go`（行 47~70）
- 依赖任务: T1
- 完成标准: `headerRoundTripper.RoundTrip` 对每个 header 值跑 `os.ExpandEnv`，`newHTTPClient` 在无 header 时返回 `http.DefaultClient`。

## T3: 实现单服务器 `Client`（Connect / ListTools / CallTool / Close）
- 影响文件: `internal/mcp/mcp.go`（行 72~151）
- 依赖任务: T1, T2
- 完成标准: `Client.Connect` 根据 `IsStdio` / `URL != ""` 分别选 `CommandTransport` / `StreamableClientTransport` / `SSEClientTransport`；stdio 把 `cmd.Stderr = io.Discard`；`CallTool` 把 `TextContent` 拼成字符串并透传 `IsError`。

## T4: 实现多服务器 `Manager`
- 影响文件: `internal/mcp/mcp.go`（行 155~237）
- 依赖任务: T3
- 完成标准: `Manager.LoadConfigs` 接受 `[]ServerConfig`；`Manager.ConnectAll` 收集 `Tools / Servers / Errors`；`Manager.Shutdown` 关闭所有 `Client.session`。

## T5: 实现 `MCPToolWrapper` 适配器
- 影响文件: `internal/mcp/mcp.go`（行 241~275）
- 依赖任务: T4
- 完成标准: `Name` 输出 `mcp__<sanitized-server>__<sanitized-tool>`；`SanitizeName` 把非 `[A-Za-z0-9_]` 全部替换为 `_`；`Execute` 失败时返回 `ToolResult{Output: "...", IsError: true}`。

## T6: 实现 `Manager.RegisterAllTools`
- 影响文件: `internal/mcp/mcp.go`（行 224~230）
- 依赖任务: T5
- 完成标准: 把 `ConnectResult.Tools` 全部 `registry.Register(...)`，返回 `Errors`。

## T7: 接入 TUI 启动流程
- 影响文件: `internal/tui/tui.go`（行 558~583 `initMCPServersCmd`、行 86 `mcpReadyMsg`、行 148 `mcpMgr` 字段、行 423~430 工具集查找）
- 依赖任务: T6
- 完成标准: TUI 启动时把 `config.yaml` 里的 `mcp_servers` 拷成 `[]mcp.ServerConfig` 调 `ConnectAll`，把 `result.Tools` 注册到 `m.registry`；MCP 工具能与内置工具并列被 LLM 调用；`grep -r "mcp\." internal/tui --include="*.go"` 至少 5 处非测试调用方。

## T8: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T7
- 完成标准: 在 `config.yaml` 加入 context7 server（`command: npx, args: [-y, @upstash/context7-mcp]`），启动 TUI，提示 LLM 调 `mcp__context7__resolve_library_id`，能看到工具命中并返回结果；`go test ./internal/mcp/ -run TestContext7MCP -v` 通过（需要 npx 可用）。

## 进度
- [ ] T1
- [ ] T2
- [ ] T3
- [ ] T4
- [ ] T5
- [ ] T6
- [ ] T7
- [ ] T8（受外部 `npx` 依赖，开发者本机已验证；CI 默认跳过）
```
```plain
# ch07: MCP Protocol Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。

## 1. 实现完整性
- [ ] 数据结构 `ServerConfig` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:21-29` 实现，字段含 `Name / Command / Args / URL / Transport / Headers / Env`（grep `type ServerConfig struct` 命中）。
- [ ] 数据结构 `Client` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:72-76` 实现，含 `config / session / sdkClient` 三个字段。
- [ ] 数据结构 `Manager` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:155-158` 实现，含 `configs / clients` 两张 map。
- [ ] 数据结构 `MCPToolWrapper` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:241-245` 实现，把 MCP tool 包装成 `tools.Tool`。
- [ ] 函数 `(*Client).Connect` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:82-116` 实现，支持 stdio / Streamable HTTP / SSE 三条分支。
- [ ] 函数 `(*Client).ListTools` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:118-124` 实现，调 `session.ListTools(ctx, nil)`。
- [ ] 函数 `(*Client).CallTool` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:126-145` 实现，把 `TextContent` 拼成字符串、透传 `IsError`、无输出回填 `(no output)`。
- [ ] 函数 `(*Manager).ConnectAll` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:185-222` 实现，按 server 维度收集 `Tools / Servers / Errors`。
- [ ] 函数 `(*Manager).RegisterAllTools` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:224-230` 实现，把 wrapper 注册到 `tools.Registry`。
- [ ] 函数 `SanitizeName` 在 `/Users/codemelo/mewcode/internal/mcp/mcp.go:251-253` 实现，把非 `[A-Za-z0-9_]` 替换为 `_`（`nonAlphanumeric` 正则在第 19 行）。
- [ ] 边界处理 `IsStdio() == false && URL == ""` 已覆盖（`mcp.go:106-108` 返回明确错误 `neither command nor url configured`）。
- [ ] 边界处理 stdio stderr 重定向到 `io.Discard`（`mcp.go:97`，注释解释 OSC 颜色查询污染 TTY 的原因）。
- [ ] 边界处理 HTTP header 值的 `os.ExpandEnv` 展开（`mcp.go:55`）。

## 2. 接入完整性（必查，杜绝死代码）
- [ ] `grep -rn "mcp\." /Users/codemelo/mewcode --include="*.go" | grep -v "_test.go" | grep -v "internal/mcp/"` 至少 5 处非测试调用方（实测命中 6 处，均位于 `internal/tui/tui.go`）。
- [ ] 调用入口位于 TUI 模块的 `/Users/codemelo/mewcode/internal/tui/tui.go:558-583`（`initMCPServersCmd`）。
- [ ] 工具注册中心已更新: `result.Tools` 经 `m.registry.Register(...)` 注入 `tools.Registry`（参见 TUI 收到 `mcpReadyMsg` 后的处理路径）。
- [ ] 配置项 `mcp_servers` 已暴露到 `config.yaml`：`internal/config` 反序列化为 `[]MCPConfig`，TUI 在 `initMCPServersCmd` 内转成 `[]mcp.ServerConfig`（`tui.go:568-579`）。
- [ ] 用户输入到本模块的路径可一句话描述: TUI 启动 → 读 `config.yaml.mcp_servers` → `mcp.NewManager().LoadConfigs(...) → ConnectAll(ctx) → result.Tools → registry.Register → LLM 把 mcp__xxx 当成普通工具调用`。

## 3. 编译与测试
- [ ] `go build ./...` 通过（章节交付前已执行）。
- [ ] `go vet ./internal/mcp/` 无警告。
- [ ] `go test ./internal/mcp/ -run TestContext7MCP -v` 通过（需要 `npx` 可用，活跃集成测试）。

## 4. 端到端验证
- [ ] 在 `config.yaml` 添加 context7 server，启动 TUI 后看到日志 `Connected successfully` 与工具列表中出现 `mcp__context7__resolve-library-id` 类工具（验证方式：手工启动 TUI 观察）。
- [ ] 在 TUI 中提示 LLM 调 context7 工具，模型返回结果而非 `Tool not found`。
- [ ] 留存证据: `/Users/codemelo/mewcode/internal/mcp/mcp_test.go` 包含活跃集成测试，可重复运行。

## 5. 文档
- [ ] spec.md / tasks.md / checklist.md 三件套齐全且最新（位于 `/Users/codemelo/mewcode/specs/go/ch07/`）。
- [ ] commit 信息标注 `ch07` 与三件套关闭状态（验收阶段产物，待用户审阅后随后续 commit 一并打标）。
```

### Python

```plain
# ch07: MCP Protocol Spec

## 1. 背景

外部能力（Context7、GitHub、Slack、数据库等）通过 Model Context Protocol（MCP）暴露给 Agent。如果没有 MCP 客户端实现，MewCode 就只能依赖内置工具，无法接入生态里已有的几百个 MCP server，等于砍掉一大块工具生态。MCP 规范定义了 JSON-RPC 2.0 之上的握手 → 工具发现 → 工具调用三阶段会话，需要本章把这三阶段、两种传输（stdio / Streamable HTTP）以及到 `Tool` 抽象基类的适配器实现，并接到 Textual TUI 的启动流程里。Python 版基于官方 `mcp` SDK（`ClientSession`、`stdio_client`、`streamable_http_client`），传输生命周期用 `AsyncExitStack` 统一收尾。

## 2. 目标

交付一个能在 MewCode 启动时按配置批量连接外部 MCP server、把每个 server 暴露的工具注册到全局 `ToolRegistry` 的异步客户端。具体能力：单服务器 `MCPClient` 封装（`connect` / `list_tools` / `call_tool` / `close`）；多服务器 `MCPManager` 封装（`load_configs` / `register_all_tools` / `get_client` / `shutdown`）；`MCPToolWrapper` 把每个 MCP tool 适配到 MewCode 的 `Tool` 抽象基类，并用 `pydantic.create_model` 动态生成参数模型；工具名按 `mcp_<server>_<tool>` 命名。最终效果是用户在 Textual TUI 里看到 MCP server 的工具与内置工具并列，能直接被 LLM 调用。

## 3. 功能需求

- F1: `MCPServerConfig`（`mewcode/config.py:67-78`）同时支持 stdio（`command + args + env`）和 HTTP（`url + headers`）两种传输，`is_stdio` 属性通过 `command is not None` 区分。
- F2: HTTP 传输用 `mcp.client.streamable_http.streamable_http_client` 建立 Streamable HTTP 会话，外部 `httpx.AsyncClient` 注入 header。
- F3: stdio 子进程通过 `StdioServerParameters` 启动，环境用 `build_child_env` 白名单，避免泄露宿主机 API key。
- F4: HTTP 请求头通过 `resolve_env_vars` 在客户端层做 `${VAR}` 展开，方便从 ENV 取 API key。
- F5: 单服务器客户端 `MCPClient.connect` → `list_tools` → `call_tool` → `close` 四阶段，所有调用复用同一个 `ClientSession`，整套生命周期挂在 `AsyncExitStack` 上。
- F6: 多服务器连接 `MCPManager.register_all_tools` 顺序遍历配置，单个失败只 append 到 `errors` 列表，不阻塞其他 server。
- F7: 工具名按 `mcp_<server>_<tool>` 命名（`tool_wrapper.py:67`），简单字符串拼接，避免与内置工具冲突。
- F8: `MCPToolWrapper.execute` 把 MCP 返回的 `TextContent / ImageContent / EmbeddedResource` 块按规则拼成字符串，把 `isError` 透传到 `ToolResult.is_error`，无输出时回填 `(no output)`。
- F9: `MCPToolWrapper` 用 `pydantic.create_model` 把 MCP 的 `inputSchema` 动态翻译成 `BaseModel`，作为 `params_model` 供工具调度层使用；`get_schema` 仍直接返回原始 `inputSchema`，避免 pydantic 转换破坏 schema 语义。
- F10: Textual TUI 启动时走 `asyncio.create_task(self._init_mcp())` 异步连接，连接结果回到主线程注册到 registry；用户按 enter 发消息前若 task 未完成，则等待 task 完成再发送。

## 4. 非功能需求

- N1: 连接是异步的（`asyncio.create_task` 派生），不阻塞 TUI 启动；连接中显示 "Waiting for MCP servers to connect..." 占位。
- N2: 单个 server 连接失败要打 `logger.warning` 并追加到 `errors` 列表，其他 server 继续连。
- N3: 工具名只允许 ASCII 字母数字下划线；server 名与 tool 名按 `mcp_<server>_<tool>` 直拼，依赖配置层校验合法性。
- N4: 复用官方 `mcp` Python SDK，不要手写 JSON-RPC 帧格式或 stdio 流解码。
- N5: `MCPManager.shutdown` 必须幂等，遍历 `self._clients` 调每个 `client.close()`，异常仅记录日志；`_cleanup_stack` 对 anyio 的 "cancel scope" RuntimeError 做静默吞没（这是已知的 SDK shutdown race）。
- N6: 进程退出时 Textual 的 `_shutdown_mcp` 先取消 `_mcp_init_task` 再调 `manager.shutdown`，保证未完成的连接任务被回收。

## 5. 设计概要

- 核心数据结构（Python 类型）:
  - `MCPServerConfig`（`mewcode/config.py:67`，dataclass）：承载 `name / command / args / url / headers / env`，`is_stdio` property。
  - `MCPClient`（`mewcode/mcp/client.py:17`）：单 server 的会话句柄，持有 `config / _session / _stack / _alive`。
  - `MCPManager`（`mewcode/mcp/manager.py:13`）：多 server 调度，持有 `_configs / _clients` 两张 dict。
  - `MCPToolWrapper`（`mewcode/mcp/tool_wrapper.py:57`）：把 MCP tool 适配到 `Tool` 抽象基类，动态生成 `params_model`。
- 主流程（调用链）:
  - `mewcode/__main__.py:49` 启动 `MewCodeApp` 时把 `config.mcp_servers` 传进去。
  - `mewcode/app.py:810-811` `on_mount` 在 `self._mcp_server_configs` 非空时 `asyncio.create_task(self._init_mcp())`。
  - `_init_mcp`（`app.py:1496-1532`）实例化 `MCPManager`，`load_configs` + `register_all_tools(self.registry)`，把每个 server 的 tool 包成 `MCPToolWrapper` 注册。
  - 对每个 server `MCPClient(config).connect()`：按 `is_stdio` 分流到 `_connect_stdio` 或 `_connect_http`，握手得到 `ClientSession`，把 transport 和 session 都丢进 `AsyncExitStack`。
  - LLM 调用工具时按 `mcp_<server>_<tool>` 找到 wrapper，`execute` 走 session 上的 `call_tool`，把 `inputSchema` 校验后的 `BaseModel.model_dump(exclude_none=True)` 作为参数。
- 与其他模块的交互:
  - 依赖 `mewcode/tools`（注册到 `ToolRegistry`、继承 `Tool` 基类）。
  - 依赖官方 `mcp` Python SDK（`ClientSession` / `stdio_client` / `streamable_http_client` / `types`）。
  - 依赖 `httpx.AsyncClient` 作为 HTTP transport 的底层连接池。
  - 被 `mewcode/app.py`（Textual TUI 主类）在启动流程中调用。
  - 依赖 `mewcode/config.py` 提供 `MCPServerConfig` 反序列化目标及 `resolve_env_vars / build_child_env` 工具。

## 6. Out of Scope

- OAuth / 鉴权刷新：只做静态 header `${VAR}` 注入，不实现 OAuth step-up 401 处理。
- 连接缓存：每次启动重新连接，不做跨进程缓存或持久化 session。
- IDE 集成（双向 SSE / WebSocket / 进程内 transport）。
- MCP `resources / prompts / sampling` 三种非 tool 能力：只暴露 `tools/list` + `tools/call`；`EmbeddedResource` 在 wrapper 里仅做文本透传。
- 服务器健康检查与自动重连：当前实现仅在工具调用时 lazy 重连（`tool_wrapper.py:88-95`），不做后台 ping/heartbeat。
- 工具名 sanitization 正则：Python 版不像 Go 版做 `[A-Za-z0-9_]` 正则替换，直接信任 server / tool 命名。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch07: MCP Protocol Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。本章基于 `origin/python` 分支已落地的实现产出，每条任务记录实际文件与行号。

## T1: 定义 `MCPServerConfig` 与 ENV 工具
- 影响文件: `mewcode/config.py:67-78`（dataclass 与 `is_stdio`），`mewcode/config.py:50-64`（`resolve_env_vars` / `build_child_env`）
- 依赖任务: 无
- 完成标准: `MCPServerConfig` 字段含 `name / command / args / url / headers / env`，`is_stdio` 用 `command is not None` 判定；`resolve_env_vars` 把 `${VAR}` 展开成 env value，缺失变量保留占位符；`build_child_env` 仅注入 `PATH` 加白名单 env，不携带宿主机敏感变量。

## T2: 在 `load_config` 中反序列化 `mcp_servers`
- 影响文件: `mewcode/config.py:129-139`（构造 list），`mewcode/validator.py`（校验同时给 command 和 url、两者都缺时抛 `ConfigError`）
- 依赖任务: T1
- 完成标准: YAML 中 `mcp_servers` map（key 为 server name）能正确解析成 `list[MCPServerConfig]`；测试 `tests/test_mcp.py::TestLoadConfigMCP` 全绿，其中包含 stdio、HTTP、both/neither 错误三类。

## T3: 实现单服务器 `MCPClient.connect` 分流
- 影响文件: `mewcode/mcp/client.py:17-65`
- 依赖任务: T1
- 完成标准: `MCPClient.connect`（client.py:29-51）根据 `config.is_stdio` 分别走 `_connect_stdio`（53-65，用 `StdioServerParameters` + `stdio_client`）或 `_connect_http`（67-84，用 `httpx.AsyncClient` + `streamable_http_client`）；连接全部通过 `AsyncExitStack` 管理；连接失败时 `_cleanup_stack` 兜底回滚。

## T4: 实现 `list_tools` / `call_tool` / `close` / `_cleanup_stack`
- 影响文件: `mewcode/mcp/client.py:86-113`
- 依赖任务: T3
- 完成标准: `list_tools`（86-89）调 `self._session.list_tools()` 返回 `list[types.Tool]`；`call_tool`（91-95）透传 `CallToolResult`；`close`（97-100）置 `_alive = False` 并交还 stack；`_cleanup_stack`（102-113）静默吞掉 anyio 的 "cancel scope" `RuntimeError`，其他异常仅打 debug 日志。

## T5: 实现 `MCPToolWrapper` 适配器
- 影响文件: `mewcode/mcp/tool_wrapper.py:57-109`
- 依赖任务: T4
- 完成标准: `MCPToolWrapper.__init__`（58-74）赋值 `self.name = f"mcp_{server_name}_{tool_def.name}"`，`category = "command"`，`should_defer = True`，调 `_build_params_model` 生成 pydantic `BaseModel`；`get_schema`（80-85）直接返回原始 `inputSchema`，不走 pydantic 转换；`execute`（87-109）失败时返回 `ToolResult(output="...", is_error=True)`，并把 `result.isError` 透传。

## T6: 实现 `_build_params_model` 与 `_extract_text`
- 影响文件: `mewcode/mcp/tool_wrapper.py:12-54`
- 依赖任务: T5
- 完成标准: `_build_params_model`（12-26）用 `pydantic.create_model` 动态生成 `<tool_name>Params` 模型，required 字段标 `...`、optional 字段标 `None`；`_json_type_to_python`（29-38）覆盖 string/integer/number/boolean/object/array 六类；`_extract_text`（41-54）把 `TextContent` / `ImageContent` / `EmbeddedResource` 三种 block 类型按规则拼接，无 block 时回填 `(no output)`。

## T7: 实现 `MCPManager` 调度与重连
- 影响文件: `mewcode/mcp/manager.py:13-70`
- 依赖任务: T5, T6
- 完成标准: `load_configs`（18-20）把 `list[MCPServerConfig]` 按 name 灌进 `_configs` dict；`register_all_tools`（22-41）遍历 connect + list_tools + register，单个失败 append 到 `errors` 列表不阻塞；`get_client`（43-61）支持 lazy connect 与 `is_alive=False` 时的重连；`shutdown`（63-70）遍历 `_clients` 调 `close()`，异常仅 debug 记录。

## T8: 暴露 `MCPManager` 出包
- 影响文件: `mewcode/mcp/__init__.py:1-5`
- 依赖任务: T7
- 完成标准: `__init__.py` 通过 `__all__ = ["MCPManager"]` 暴露，调用方写 `from mewcode.mcp import MCPManager` 即可。

## T9: 接入 Textual TUI 启动流程
- 影响文件: `mewcode/app.py:50`（import），`mewcode/app.py:514-525`（构造参数），`mewcode/app.py:537-538`（实例字段），`mewcode/app.py:810-811`（`on_mount` 派任务），`mewcode/app.py:1042-1044`（发消息前 await），`mewcode/app.py:1068-1070`（追加 system reminder），`mewcode/app.py:1496-1532`（`_init_mcp`），`mewcode/app.py:1534-1544`（`_shutdown_mcp`）
- 依赖任务: T8
- 完成标准: TUI 启动时把 `config.mcp_servers` 拷给 `MewCodeApp`，`on_mount` 派 `asyncio.create_task(self._init_mcp())`；`_init_mcp` 实例化 `MCPManager` + `load_configs` + `register_all_tools(self.registry)`，把 server 名与可用工具列表拼成 `_mcp_instructions` 用 `add_system_reminder` 注入；用户发消息时若 task 未完成则 `await self._mcp_init_task`；退出时 `_shutdown_mcp` 取消 task 并调 `manager.shutdown`。

## T10: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T9
- 完成标准: `pytest tests/test_mcp.py -v` 全绿；在 `config.yaml` 加入 context7 server（`command: npx, args: [-y, "@upstash/context7-mcp"]`），启动 TUI，提示 LLM 调 `mcp_context7_resolve_library_id`，能看到工具命中并返回结果；TUI 顶部状态条应出现 "Connected to N MCP server(s), M tools registered" 提示。

## 进度
- [ ] T1
- [ ] T2
- [ ] T3
- [ ] T4
- [ ] T5
- [ ] T6
- [ ] T7
- [ ] T8
- [ ] T9
- [ ] T10（受外部 `npx` / context7 依赖，开发者本机已验证；CI 默认跳过）
```
```plain
# ch07: MCP Protocol Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。文件路径基于 `origin/python` 分支。

## 1. 实现完整性

- [ ] 数据结构 `MCPServerConfig` 在 `mewcode/config.py:67-78` 实现，字段含 `name / command / args / url / headers / env`，`is_stdio` property 在第 76-78 行（`git show origin/python:mewcode/config.py | grep -n "class MCPServerConfig"` 命中第 68 行）。
- [ ] 数据结构 `MCPClient` 在 `mewcode/mcp/client.py:17-23` 实现，含 `config / name / _session / _stack / _alive` 五个属性（`git show origin/python:mewcode/mcp/client.py | grep -n "class MCPClient"` 命中第 17 行）。
- [ ] 数据结构 `MCPManager` 在 `mewcode/mcp/manager.py:13-16` 实现，含 `_configs / _clients` 两张 dict（`git show origin/python:mewcode/mcp/manager.py | grep -n "class MCPManager"` 命中第 13 行）。
- [ ] 数据结构 `MCPToolWrapper` 在 `mewcode/mcp/tool_wrapper.py:57-74` 实现，继承 `Tool` 基类，赋值 `name / description / category / should_defer / params_model`（`git show origin/python:mewcode/mcp/tool_wrapper.py | grep -n "class MCPToolWrapper"` 命中第 57 行）。
- [ ] 函数 `MCPClient.connect` 在 `mewcode/mcp/client.py:29-51` 实现，按 `config.is_stdio` 分流到 `_connect_stdio` / `_connect_http`，握手通过 `ClientSession.initialize()`，失败回滚 `AsyncExitStack`。
- [ ] 函数 `MCPClient._connect_stdio` 在 `client.py:53-65` 实现，用 `StdioServerParameters` + `mcp.client.stdio.stdio_client`，env 通过 `build_child_env` 白名单。
- [ ] 函数 `MCPClient._connect_http` 在 `client.py:67-84` 实现，用 `httpx.AsyncClient` + `mcp.client.streamable_http.streamable_http_client`，header 通过 `resolve_env_vars` 展开。
- [ ] 函数 `MCPClient.list_tools` 在 `client.py:86-89` 实现，调 `self._session.list_tools()` 返回 `list[types.Tool]`。
- [ ] 函数 `MCPClient.call_tool` 在 `client.py:91-95` 实现，透传 `CallToolResult`。
- [ ] 函数 `MCPClient._cleanup_stack` 在 `client.py:102-113` 实现，对 anyio `RuntimeError("cancel scope")` 静默吞没（这是 SDK shutdown race 的已知行为）。
- [ ] 函数 `MCPManager.load_configs` 在 `manager.py:18-20` 实现，按 `cfg.name` 灌进 `_configs` dict。
- [ ] 函数 `MCPManager.register_all_tools` 在 `manager.py:22-41` 实现，按 server 维度收集 `errors`，单个失败 `logger.warning` 后 append 不阻塞其他 server；返回 `list[str]`。
- [ ] 函数 `MCPManager.get_client` 在 `manager.py:43-61` 实现，支持 lazy connect 与 `is_alive=False` 时重新实例化客户端。
- [ ] 函数 `MCPManager.shutdown` 在 `manager.py:63-70` 实现，遍历调 `client.close()`，异常仅 `logger.debug` 记录，清空 `_clients`。
- [ ] 函数 `_build_params_model` 在 `tool_wrapper.py:12-26` 实现，用 `pydantic.create_model` 动态生成 `<ToolName>Params`，required 标 `...`、optional 标 `None`。
- [ ] 函数 `_extract_text` 在 `tool_wrapper.py:41-54` 实现，处理 `TextContent / ImageContent / EmbeddedResource`，无 block 回填 `(no output)`。
- [ ] 函数 `MCPToolWrapper.execute` 在 `tool_wrapper.py:87-109` 实现，`is_alive=False` 时 lazy reconnect；失败返回 `ToolResult(output="...", is_error=True)`；透传 `result.isError`。
- [ ] 工具名格式为 `mcp_<server>_<tool>`（`tool_wrapper.py:67` `f"mcp_{server_name}_{tool_def.name}"`）。
- [ ] 边界 `MCPServerConfig` 同时给 `command` 和 `url` 时 `load_config` 抛 `ConfigError`，错误信息包含 `cannot have both`（`pytest tests/test_mcp.py::TestLoadConfigMCP::test_both_command_and_url_errors -v`）。
- [ ] 边界 `MCPServerConfig` 两者都不给时抛 `ConfigError`，包含 `must have either`（`pytest tests/test_mcp.py::TestLoadConfigMCP::test_neither_command_nor_url_errors -v`）。
- [ ] 边界 stdio 子进程 env 通过 `build_child_env` 白名单（`tests/test_mcp.py::TestBuildChildEnv::test_excludes_host_vars` 通过，确认宿主机 `ANTHROPIC_API_KEY` 不被泄漏）。
- [ ] 边界 HTTP header 值的 `${VAR}` 展开走 `resolve_env_vars`（`client.py:71-72` 字典推导式）。

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `git show origin/python:mewcode/app.py | grep -nE "mcp_|MCPManager|_init_mcp"` 至少 12 处命中（实测含 import、字段、`on_mount` 派任务、`_init_mcp` / `_shutdown_mcp`、发消息 await、system reminder 注入）。
- [ ] 调用入口位于 Textual TUI 的 `mewcode/app.py:810-811`：`if self._mcp_server_configs: self._mcp_init_task = asyncio.create_task(self._init_mcp())`。
- [ ] 工具注册中心已更新：`_init_mcp`（`app.py:1496-1532`）调 `await manager.register_all_tools(self.registry)`，把 wrapper 注入 `ToolRegistry`。
- [ ] System reminder 注入：连接成功后构造 `_mcp_instructions`（`app.py:1515-1532`，含 server 名与工具列表），发消息时若未注入则用 `conversation.add_system_reminder` 写入一次（`app.py:1068-1070`）。
- [ ] 配置项 `mcp_servers` 已从 YAML 反序列化到 `AppConfig.mcp_servers`（`mewcode/config.py:129-139`），`__main__.py:52` 把 `config.mcp_servers` 传给 `MewCodeApp`。
- [ ] 用户输入到本模块的路径可一句话描述: Textual TUI 启动 → 读 `config.yaml.mcp_servers` → `MCPManager().load_configs(...) → register_all_tools(self.registry)` → 工具变成 `mcp_<server>_<tool>` → LLM 把它当普通工具调用 → `MCPToolWrapper.execute` 走 `MCPClient.call_tool` → MCP server 返回 `CallToolResult` → `_extract_text` 拼成字符串。
- [ ] 退出时 `_shutdown_mcp`（`app.py:1534-1544`）取消 `_mcp_init_task` 并 await，再调 `manager.shutdown()` 清理所有 client。

## 3. 编译与测试

- [ ] `ruff check mewcode/mcp/` 无报错（章节交付前已执行）。
- [ ] `mypy mewcode/mcp/` 类型检查通过（若项目启用 mypy）。
- [ ] `pytest tests/test_mcp.py -v` 全绿，至少 14 个测试（`TestResolveEnvVars`、`TestBuildChildEnv`、`TestLoadConfigMCP`、`TestMCPToolWrapper`、`TestExtractText`、`TestMCPManagerPartialFailure` 六组）。
- [ ] `pytest tests/test_mcp.py::TestMCPManagerPartialFailure -v` 单跑通过，验证单 server 失败不阻塞其他 server。

## 4. 端到端验证

- [ ] 在 `config.yaml` 添加 context7 server（`command: npx, args: ["-y", "@upstash/context7-mcp"]`），启动 `python -m mewcode`，观察日志出现 `MCP server 'context7' connected` 与 `Registered MCP tool: mcp_context7_resolve_library_id` 类条目。
- [ ] TUI 状态条 / 系统消息出现 `Connected to 1 MCP server(s), N tools registered`（`app.py:1512-1514`）。
- [ ] 在 TUI 中提示 LLM 调 context7 工具（例：`use mcp_context7_resolve_library_id for "next.js"`），模型返回结果而非 `Tool not found`。
- [ ] 留存证据: `tests/test_mcp.py` 包含 `TestMCPManagerPartialFailure::test_single_server_failure_does_not_block_others`，可重复运行。

## 5. 文档

- [ ] `docs/python/ch07/spec.md` / `tasks.md` / `checklist.md` 三件套齐全且最新。
- [ ] commit 信息标注 `ch07` 与三件套关闭状态（验收阶段产物，待用户审阅后随后续 commit 一并打标）。
```

### Java

```plain
# ch07: MCP Protocol Spec

## 1. 背景

外部能力（Context7、Atlassian、Slack 等）通过 Model Context Protocol（MCP）暴露给 Agent。如果没有 MCP 客户端实现，MewCode 就只能依赖内置的六个工具（ReadFile / WriteFile / EditFile / Bash / Glob / Grep），无法接入生态里已有的几百个 MCP server，等于砍掉一大块工具生态。MCP 规范定义了 JSON-RPC 2.0 之上的握手 → 工具发现 → 工具调用三阶段会话，需要本章在 Java 侧把这三阶段、两种传输（stdio 子进程 / Streamable HTTP，含兼容 SSE 解析）以及到 `com.mewcode.tool.Tool` 接口的适配器实现，并接到 TUI 的启动流程里。

## 2. 目标

交付一个能在 MewCode 启动时按配置批量连接外部 MCP server、把每个 server 暴露的工具注册到全局 `ToolRegistry` 的客户端。具体能力：单服务器 `McpTransport` 抽象（connect / getInstructions / listTools / callTool / close）；多服务器调度类 `McpManager`（构造、`connectAll`、`registerAllTools`、`shutdown`）；`McpToolWrapper` 把每个 MCP tool 适配到 `com.mewcode.tool.Tool` 接口；工具名做命名空间消毒。最终效果是用户在 TUI 里看到 MCP server 的工具与内置工具并列，能被 LLM 调用，且默认走 deferred 通道按需披露。

## 3. 功能需求

- F1: 服务器配置 `McpServerConfig` 同时承载 stdio（`command + args + env`）和 HTTP（`url + headers`）两种传输，POJO + getter/setter，YAML 反序列化兼容。
- F2: `McpManager.connectAll` 在 `command` 非空时构造 `McpStdioClient`，否则在 `url` 非空时构造 `McpHttpClient`，两者皆空时把错误写入 `errors` 列表并跳过该 server。
- F3: stdio 子进程的 stderr 用一个 virtual thread 持续 drain 丢弃，避免 OSC 颜色查询污染父 TTY 输入。
- F4: HTTP 请求头通过 `HttpRequest.Builder.header` 注入，并对 header 值做 `${VAR}` 占位符替换（`resolveEnvVars`），方便从环境变量取 API key；stdio 子进程的 `env` 同样做替换。
- F5: 单服务器实现 `connect` → `listTools` → `callTool` → `close` 四阶段：`connect` 发 `initialize` 请求并紧跟一条 `notifications/initialized`；`listTools` 调 `tools/list`；`callTool` 调 `tools/call`；HTTP 复用同一个 `HttpClient` 实例，stdio 复用同一对 `BufferedReader / BufferedWriter`。
- F6: `McpManager.connectAll` 把多 server 批量并入，单个 server 抛异常时把 `errors.add("MCP server '<name>': <message>")` 收集但不阻塞其他 server；返回 `ConnectResult(tools, servers, errors)` 三元组。
- F7: 工具名按 `mcp__<server>__<tool>` 命名，server 名和 tool 名都过 `sanitizeName`（非 `[A-Za-z0-9_]` 字符替换为下划线），保证 LLM API 的 tool name 合法。
- F8: `McpToolWrapper.execute` 透过 transport 调真实工具，把 MCP 响应里的 `result.content` 列表中所有 `type == "text"` 块拼成字符串；JSON-RPC 错误（`response.error` 非空）返回 `"MCP error: <message>"`；无输出回填 `(no output)`；任何异常包成 `ToolResult.error(...)`。
- F9: `McpManager.registerAllTools(ToolRegistry registry)` 把所有 wrapper 注册到 `ToolRegistry`，返回 `errors` 列表供 TUI 显示。
- F10: 所有 wrapper 实现 `Tool.shouldDefer() == true`，类别 `ToolCategory.COMMAND`，让 TUI / Agent 把 MCP 工具放进 deferred 通道，靠 `ToolRegistry.getDeferredTools / searchDeferred / findDeferredByNames` 按需披露给 LLM。
- F11: HTTP transport 支持 `Mcp-Session-Id` 会话头：首次响应里若带回 `mcp-session-id` 则保存到客户端实例字段，后续每个请求自动带上。
- F12: HTTP transport 同时支持 `application/json` 与 `text/event-stream`：响应 `Content-Type` 含 `text/event-stream` 时走 `parseSseResponse`，从 `data:` 行里挑出匹配 `id` 的 JSON-RPC 帧；纯 JSON 走 `ObjectMapper.readValue`。
- F13: TUI 启动时（`MewCodeModel` 初始化阶段或专用 init 命令）读 `config.yaml` 的 `mcp_servers`，构造 `McpManager` 实例，异步调 `connectAll` / `registerAllTools`，把结果汇回主线程后注册到全局 registry。

## 4. 非功能需求

- N1: 连接是异步执行的（在 TUI 后台 virtual thread / executor 里执行），不阻塞 TUI 启动渲染。
- N2: 单个 server 连接失败要被收集到 `ConnectResult.errors`，其他 server 继续连。
- N3: 工具名转换必须保证 LLM API 的 tool name 合法性（只允许字母数字和下划线），由 `NON_ALNUM` 正则 + `sanitizeName` 保证。
- N4: 不要手写 JSON-RPC 帧格式以外的协议细节；JSON 编解码统一走单例 `ObjectMapper`。
- N5: `shutdown` 必须幂等：stdio 客户端调 `process.destroyForcibly`，HTTP 客户端无连接可关；多次调用不抛异常。
- N6: stdio 客户端的 `connect` 必须在 `initialize` 之后立刻发 `notifications/initialized`，否则有些 server 拒绝继续会话。

## 5. 设计概要

- 核心数据结构:
 - `com.mewcode.config.McpServerConfig`：POJO，字段 `name / command / args / url / headers / env`，YAML 反序列化目标。
 - `McpManager`：多 server 调度，持有 `Map<String, McpServerConfig> configs` 与 `Map<String, McpTransport> clients` 两张 `LinkedHashMap`，对外暴露 `connectAll / registerAllTools / shutdown`。
 - `McpManager.McpTransport`：传输抽象接口（5 个方法），由 `McpStdioClient` / `McpHttpClient` 两个内部类实现。
 - `McpManager.ConnectResult`：record，含 `List<Tool> tools / List<ServerInfo> servers / List<String> errors`，作为 `connectAll` 的返回类型。
 - `McpManager.ServerInfo`：record，含 `name / instructions`，承载 `initialize` 响应里的 server `instructions` 文本。
 - `McpManager.McpToolDef`：record，含 `name / description / inputSchema`，承载 `tools/list` 单条结果。
 - `McpManager.McpToolWrapper`：把 `McpToolDef + 服务端 name + transport` 适配到 `com.mewcode.tool.Tool`。
- 主流程（调用链）:
 - TUI 启动读 config 拿到 MCP server 列表 → 用 `new McpManager(configs)` 构造 → 异步走 `manager.connectAll()` / `manager.registerAllTools(registry)`。
 - 对每个 server 按 `command / url` 选择 `McpStdioClient` 或 `McpHttpClient`：构造 → `connect()` 发 `initialize` + `notifications/initialized` → `getInstructions()` 取握手返回的 server 指令 → `listTools()` 拿工具列表 → 包成 `McpToolWrapper`。
 - TUI 收到完成事件后把 `ConnectResult.tools` 批量 `registry.register(tool)`；`errors` 渲染到对话顶部告知用户。
 - LLM 调用工具时按 `mcp__<server>__<tool>` 在 registry 命中 wrapper，`execute(args)` 调 transport 的 `callTool` 走 session 上的 `tools/call`。
- 与其他模块的交互:
 - 依赖 `com.mewcode.tool`：实现 `Tool` 接口、注册到 `ToolRegistry`、返回 `ToolResult`。
 - 依赖 `com.fasterxml.jackson.databind.ObjectMapper`：所有 JSON-RPC 帧编解码。
 - 依赖 JDK 自带的 `java.net.http.HttpClient`：HTTP 传输；stdio 走 `ProcessBuilder` + `BufferedReader / BufferedWriter`。
 - 被 `com.mewcode.MewCode` / `com.mewcode.tui.MewCodeModel` 调用：在主启动入口把 `config.getMcpServers()` 传进 model；model 内构造 `McpManager` 并调 `registerAllTools`。

## 6. Out of Scope

- OAuth / 鉴权刷新：本仓库只做静态 header 注入与环境变量展开，不实现 OAuth step-up 401 处理。
- 连接缓存：每次启动重新连接，不做跨进程缓存。
- IDE 集成（双向 SSE / WebSocket / 进程内 transport）。
- MCP resources / prompts / sampling 三种非 tool 能力：只暴露 `tools/list` + `tools/call`。
- 服务器健康检查与自动重连：断了由用户重启 MewCode。
- stdio 端的 stderr 内容回流：当前直接 drain 丢弃，不做日志聚合。

## 7. 完成定义

见 [checklist.md](checklist.md)，所有条目勾上即完成。
```
```plain
# ch07: MCP Protocol Tasks

> 任务粒度: 每个任务可在一次会话内完成，可独立交付。每完成一个任务跑 `./gradlew build` 确保编译过；接入主流程的任务（T7、T8）做完后立刻补一次端到端验证再进下一项。

## T1: 定义 `McpServerConfig` 配置 POJO
- 影响文件: `src/main/java/com/mewcode/config/McpServerConfig.java`（行 1~32）
- 依赖任务: 无
- 完成标准: 类含字段 `name / command / args / url / headers / env`，全部走 `private` + getter/setter，类型分别为 `String / String / List<String> / String / Map<String,String> / Map<String,String>`，可被 YAML 反序列化为 `mcp_servers` 列表项。

## T2: 抽出 `McpTransport` 接口与共享工具
- 影响文件: `src/main/java/com/mewcode/mcp/McpManager.java`（行 19~30 类骨架与字段；行 86~96 `sanitizeName` / `resolveEnvVars`；行 100~106 `McpTransport` 接口；行 401~419 `extractTextContent`；行 421~423 `McpToolDef` record）
- 依赖任务: T1
- 完成标准: `McpManager` 持有 `ObjectMapper MAPPER`、`Pattern NON_ALNUM`、`Pattern ENV_VAR` 三个静态常量；定义内嵌 `interface McpTransport`，5 个方法 `connect / getInstructions / listTools / callTool / close`；静态助手 `sanitizeName` / `resolveEnvVars` / `extractTextContent` 实现；`McpToolDef(name, description, inputSchema)` record 定义齐全。

## T3: 实现 `McpStdioClient`（JSON-RPC over stdio）
- 影响文件: `src/main/java/com/mewcode/mcp/McpManager.java`（行 108~239）
- 依赖任务: T2
- 完成标准:
 - `connect()` 用 `ProcessBuilder` 拉起子进程，把 `config.getEnv()` 跑 `resolveEnvVars` 后写入 `pb.environment()`；启动一个 virtual thread drain stderr（行 142~146）。
 - 发 `initialize` 请求（protocolVersion `2024-11-05`、clientInfo `{name: mewcode, version: 0.1.0}`），从 `result.instructions` 取 server 指令。
 - 紧跟发 `notifications/initialized` 通知（行 159）。
 - `sendRequest` 用 `idCounter` 自增 + `MAPPER.writeValueAsString` 拼帧 + `writer.write + newLine + flush`；读响应循环 `readLine`，丢空行，遇到含 `id` 的帧返回。
 - `listTools` 把 `result.tools` 解析为 `List<McpToolDef>`。
 - `callTool(name, args)` 调 `tools/call`，错误透传 `MCP error: <message>`，否则调 `extractTextContent`。
 - `close()` 在 `process != null && process.isAlive()` 时 `destroyForcibly()`。

## T4: 实现 `McpHttpClient`（JSON-RPC over Streamable HTTP，兼容 SSE）
- 影响文件: `src/main/java/com/mewcode/mcp/McpManager.java`（行 241~399）
- 依赖任务: T2
- 完成标准:
 - 类持有单例 `HttpClient.newHttpClient()` 与 `String sessionId` 字段。
 - `connect()` 发 `initialize`，从响应里读 `instructions`；紧跟发 `notifications/initialized`（行 268）。
 - `sendHttpRequest` 构建 `HttpRequest.newBuilder().uri(config.getUrl())`，必带 `Content-Type: application/json` 与 `Accept: application/json, text/event-stream`；`sessionId` 不空则带 `Mcp-Session-Id`；config 的 `headers` 走 `resolveEnvVars` 后逐条 `.header(key, value)`。
 - 响应 `mcp-session-id` 头若存在则赋值到 `sessionId`（行 337）。
 - `Content-Type` 含 `text/event-stream` 时走 `parseSseResponse`：按行解析 `data: ` 前缀，跳过空行与 `[DONE]`，匹配 `id` 后返回；否则 `MAPPER.readValue` 当成单个 JSON 帧。
 - `sendHttpNotification` 不带 `id` 字段，响应丢弃（`BodyHandlers.discarding()`）。
 - `listTools` / `callTool` 复用与 stdio 一致的语义。
 - `close()` 无连接需关，方法体为空注释。

## T5: 实现 `McpToolWrapper` 适配器
- 影响文件: `src/main/java/com/mewcode/mcp/McpManager.java`（行 425~460）
- 依赖任务: T3, T4
- 完成标准:
 - 实现 `com.mewcode.tool.Tool` 接口。
 - `name()` 返回 `"mcp__" + sanitizeName(serverName) + "__" + sanitizeName(toolDef.name())`（行 438~440）。
 - `description()` 直接透传 `toolDef.description()`。
 - `category()` 返回 `ToolCategory.COMMAND`；`shouldDefer()` 返回 `true`（让 deferred 通道接管）。
 - `schema()` 返回 `Map.of("name", name(), "description", description(), "input_schema", input)`，`input` 为 `toolDef.inputSchema()`，空则回退到 `{"type":"object","properties":{}}`。
 - `execute(args)` 调 `transport.callTool(toolDef.name(), args)`，捕获异常包成 `ToolResult.error("MCP tool call failed: " + e.getMessage())`，成功包 `ToolResult.success(output)`。

## T6: 实现 `McpManager.connectAll` / `registerAllTools` / `shutdown`
- 影响文件: `src/main/java/com/mewcode/mcp/McpManager.java`（行 31~84）
- 依赖任务: T5
- 完成标准:
 - 构造函数接收 `List<McpServerConfig>`，按 name 装进 `configs` `LinkedHashMap`，null 安全。
 - `connectAll()` 遍历 `configs`：根据 `command` / `url` 选 `McpStdioClient` / `McpHttpClient`，两者皆空则错误清单加 `"MCP server '<name>': neither command nor url configured"` 并 continue。
 - 单个 server 走 `try { connect; listTools; tools.add(new McpToolWrapper(...)) } catch (Exception e) { errors.add(...) }`，不阻塞其他 server。
 - 返回 `new ConnectResult(List.copyOf(tools), List.copyOf(servers), List.copyOf(errors))`。
 - `registerAllTools(ToolRegistry registry)` 调一次 `connectAll`，对 `result.tools()` 逐个 `registry.register(t)`，返回 `result.errors()`。
 - `shutdown()` 遍历 `clients.values()` 调 `client.close()`，最后 `clients.clear()`，幂等。

## T7: 接入 TUI 启动流程
- 影响文件: `src/main/java/com/mewcode/MewCode.java`（行 35~39 把 `config.getMcpServers()` 传进 model 构造）、`src/main/java/com/mewcode/tui/MewCodeModel.java`（在初始化阶段构造 `McpManager` 并异步调 `connectAll` / `registerAllTools`，把结果汇回 update / Msg 通道）
- 依赖任务: T6
- 完成标准:
 - TUI 启动时把 `config.getMcpServers()` 拷成 `List<McpServerConfig>` 传给 model；model 内构造 `new McpManager(configs)` 与默认 `ToolRegistry.createDefault()` 并存。
 - 异步线程（`Thread.ofVirtual().start(...)` 或 executor）执行 `registerAllTools`，错误列表通过自定义 `McpReadyMsg` 回主线程渲染。
 - MCP 工具能与内置 6 个工具并列被 LLM 调用（通过 `getDeferredTools` / `searchDeferred` / `findDeferredByNames` 披露）。
 - 退出钩子（如 `program.run()` 的 `finally`）调 `manager.shutdown()`。

## T8: 端到端验证
- 影响文件: 无（仅运行验证）
- 依赖任务: T7
- 完成标准:
 - `./gradlew build` 通过。
 - `./gradlew test` 全过（含 `McpManagerTest` 之类单测）。
 - 在 `config.yaml` 添加 context7 server（`command: npx, args: [-y, @upstash/context7-mcp]`），启动 TUI 后看到 MCP 工具列表（含 `mcp__context7__resolve_library_id` 等）能被 LLM 调用并返回结果；启动日志或错误面板看到 `Connected successfully`/无错误。
 - HTTP 路径用一台公开 MCP server（或自起 `mcp-server-stdio` 套 HTTP wrapper）验证 SSE 与 Mcp-Session-Id 头能跑通。
 - 截图或日志留证。

## 进度
- [ ] T1
- [ ] T2
- [ ] T3
- [ ] T4
- [ ] T5
- [ ] T6
- [ ] T7
- [ ] T8（受外部 `npx` / 公开 MCP server 依赖，本机已验证；CI 默认跳过）
```
```plain
# ch07: MCP Protocol Checklist

> 所有条目必须可勾选、可观测。验收方式写在每项后面的括号里。

## 1. 实现完整性

### 1.1 配置 POJO
- [ ] `McpServerConfig` 在 `src/main/java/com/mewcode/config/McpServerConfig.java:6-32` 实现，字段 `name / command / args / url / headers / env` 齐全（grep `class McpServerConfig` 命中）。
- [ ] 全部字段走 `private` + 公开 `getXxx / setXxx`，类型分别为 `String / String / List<String> / String / Map<String,String> / Map<String,String>`（验证：肉眼检查 `McpServerConfig.java:15-31`）。

### 1.2 McpManager 骨架与共享工具
- [ ] 类 `McpManager` 位于 `src/main/java/com/mewcode/mcp/McpManager.java:19`，含静态常量 `MAPPER`（行 21）、`NON_ALNUM`（行 22）、`ENV_VAR`（行 23）。
- [ ] record `ServerInfo(String name, String instructions)` 在 `McpManager.java:25` 定义。
- [ ] record `ConnectResult(List<Tool> tools, List<ServerInfo> servers, List<String> errors)` 在 `McpManager.java:26` 定义。
- [ ] record `McpToolDef(String name, String description, Map<String, Object> inputSchema)` 在 `McpManager.java:423` 定义。
- [ ] 接口 `McpTransport` 在 `McpManager.java:100-106` 定义，5 个方法 `connect / getInstructions / listTools / callTool / close` 齐全。
- [ ] 静态助手 `sanitizeName` 在 `McpManager.java:86-88` 实现，正则替换非 `[A-Za-z0-9_]` 为 `_`。
- [ ] 静态助手 `resolveEnvVars` 在 `McpManager.java:90-96` 实现，对 `${VAR}` 占位符做 `System.getenv` 替换，匹配不到时保留原样。
- [ ] 静态助手 `extractTextContent` 在 `McpManager.java:403-419` 实现，把 `result.content` 中 `type == "text"` 的块拼成字符串，空时返回 `(no output)`。

### 1.3 stdio 传输
- [ ] `McpStdioClient` 在 `McpManager.java:110-239` 实现，含 `process / writer / reader / idCounter / instructions` 五个字段。
- [ ] `connect()` 在 `McpManager.java:124-160` 实现，用 `ProcessBuilder` 启动子进程并 `redirectErrorStream(false)`。
- [ ] stderr drain 在 `McpManager.java:142-146`，用 `Thread.startVirtualThread` 持续 `readLine`（避免 OSC 颜色查询污染 TTY）。
- [ ] `initialize` 请求体 `protocolVersion=2024-11-05`、`clientInfo={name:mewcode,version:0.1.0}` 在 `McpManager.java:148-152`。
- [ ] `notifications/initialized` 在 `McpManager.java:159` 发出。
- [ ] `sendRequest` 在 `McpManager.java:201-221` 实现：`idCounter.incrementAndGet`、`writer.write + newLine + flush`、读循环跳过空行、遇到含 `id` 的 JSON 帧返回。
- [ ] `listTools` 在 `McpManager.java:167-184` 解析 `result.tools` 为 `List<McpToolDef>`。
- [ ] `callTool` 在 `McpManager.java:188-198`，JSON-RPC `error` 非空时返回 `MCP error: <message>`；否则调 `extractTextContent`。
- [ ] `close` 在 `McpManager.java:234-238`，`process.isAlive()` 时 `destroyForcibly()`，幂等。
- [ ] env 变量替换：`config.getEnv()` 的值在 `McpManager.java:131-136` 走 `resolveEnvVars` 后写入 `pb.environment()`。

### 1.4 HTTP 传输
- [ ] `McpHttpClient` 在 `McpManager.java:243-399` 实现，含 `config / httpClient / idCounter / instructions / sessionId` 五个字段。
- [ ] `connect()` 在 `McpManager.java:256-269` 发 `initialize` 与 `notifications/initialized`。
- [ ] `sendHttpRequest` 在 `McpManager.java:310-347`：必带 `Content-Type: application/json` 与 `Accept: application/json, text/event-stream`；`sessionId` 不空时带 `Mcp-Session-Id` 头；config `headers` 走 `resolveEnvVars` 注入。
- [ ] 响应头 `mcp-session-id` 自动赋值到 `sessionId` 字段（`McpManager.java:337`）。
- [ ] SSE 解析在 `McpManager.java:350-368`：按行扫 `data: ` 前缀，跳过空行与 `[DONE]`，匹配 `id` 后返回对应 JSON-RPC 帧；找不到则抛 `IOException("No JSON-RPC response found in SSE stream")`。
- [ ] `sendHttpNotification` 在 `McpManager.java:370-393` 不带 `id` 字段，响应走 `BodyHandlers.discarding()`。
- [ ] `close()` 在 `McpManager.java:395-398` 是空实现 + 注释 `// HTTP is stateless; nothing to close`。

### 1.5 Tool Wrapper
- [ ] `McpToolWrapper` 在 `McpManager.java:427-460` 实现 `com.mewcode.tool.Tool`。
- [ ] `name()` 在 `McpManager.java:438-440` 输出 `mcp__<sanitized-server>__<sanitized-tool>`。
- [ ] `description()` 透传 `toolDef.description()`（行 442）。
- [ ] `category()` 返回 `ToolCategory.COMMAND`、`shouldDefer()` 返回 `true`（行 443~444）。
- [ ] `schema()` 在 `McpManager.java:446-450` 返回 `{name, description, input_schema}`；`inputSchema` 为 null 时回退 `{type: object, properties: {}}`。
- [ ] `execute(args)` 在 `McpManager.java:452-459`：成功 `ToolResult.success(output)`、异常 `ToolResult.error("MCP tool call failed: " + e.getMessage())`。

### 1.6 Manager 调度
- [ ] 构造函数 `McpManager(List<McpServerConfig>)` 在 `McpManager.java:31-35` 实现，null 安全按 `name` 装进 `LinkedHashMap`。
- [ ] `connectAll()` 在 `McpManager.java:37-73`，按 `command / url` 选传输；两者皆空时 `errors.add("MCP server '<name>': neither command nor url configured")` 并 `continue`。
- [ ] 单 server 失败收集到 `errors`，其他 server 继续连：见 `McpManager.java:67-69` 的 `try/catch`。
- [ ] `connectAll` 返回的 `ConnectResult` 三个列表均通过 `List.copyOf` 包裹，避免外部修改（行 72）。
- [ ] `registerAllTools(ToolRegistry registry)` 在 `McpManager.java:75-79`，遍历 `result.tools()` 调 `registry.register(t)`，返回 `result.errors()`。
- [ ] `shutdown()` 在 `McpManager.java:81-84`：遍历 `clients.values()` 调 `close()`，再 `clients.clear()`，幂等。

## 2. 接入完整性（必查，杜绝死代码）

- [ ] `grep -rn "McpManager\|McpServerConfig" --include="*.java" src/main` 至少 5 处非测试调用方（实测应命中 `config/McpServerConfig.java` 定义 + `mcp/McpManager.java` 定义 + `MewCode.java` 传参 + `tui/MewCodeModel.java` 构造与生命周期）。
- [ ] 启动入口 `src/main/java/com/mewcode/MewCode.java:35-39` 把 `config.getMcpServers()` 透传给 `MewCodeModel`。
- [ ] `MewCodeModel` 内构造 `new McpManager(...)` 并在异步线程（virtual thread / executor）调用 `registerAllTools(toolRegistry)`，错误清单通过 Msg 回主循环渲染。
- [ ] 退出路径调 `manager.shutdown()`（在 `program.run()` 的 `finally` 或 model 的清理钩子里）。
- [ ] 配置项 `mcp_servers` 已暴露到 `config.yaml`：`AppConfig.getMcpServers()` 返回 `List<McpServerConfig>`，YAML 反序列化能解析 `command / args / env / url / headers` 字段。
- [ ] 用户输入到本模块的路径可一句话描述: 启动 `MewCode.main` → `ConfigLoader.load` → `config.getMcpServers()` → `new MewCodeModel(..., mcpServers, ...)` → 异步 `new McpManager(mcpServers).registerAllTools(toolRegistry)` → LLM 把 `mcp__xxx` 当 deferred 工具按需取出。

## 3. 编译与测试

- [ ] `./gradlew build` 通过。
- [ ] `./gradlew test` 全过。
- [ ] `./gradlew test --tests "com.mewcode.mcp.*"` 全过（含 sanitizeName / resolveEnvVars / extractTextContent 单测）。

## 4. 端到端验证

- [ ] 在 `config.yaml` 添加 context7 server（`command: npx, args: [-y, @upstash/context7-mcp]`），启动 TUI 后能看到 `mcp__context7__resolve_library_id` 出现在 deferred 工具列表中。
- [ ] 在 TUI 中提示 LLM 调 context7 工具，模型返回结果而非 `Tool not found`。
- [ ] 配置一个故意写错的 server（command 与 url 都不填），启动后看到错误清单含 `MCP server '<name>': neither command nor url configured`，其他 server 仍正常连上。
- [ ] HTTP MCP server（支持 SSE 响应）能跑通：返回 `text/event-stream` 时 `parseSseResponse` 解析得到 JSON-RPC 响应，`Mcp-Session-Id` 在后续请求里自动带上。
- [ ] 退出 TUI 后无 stdio 子进程残留（`ps aux | grep mcp` 看不到僵尸进程）。

## 5. 文档

- [ ] `docs/java/ch07/spec.md` 与本 checklist / tasks 三件套齐全且最新。
- [ ] commit 信息标注 `ch07` 与三件套关闭状态（验收阶段产物，待用户审阅后随后续 commit 一并打标）。
```