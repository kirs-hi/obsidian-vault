理论篇讲了 Agent Loop 的设计理念和 ReAct 范式，这篇带你走读 Go 版 MewCode 的真实代码，看看这些概念是怎么落地成可运行的程序的。

## 模块概览

Agent Loop 的代码集中在 `internal/agent/` 目录下，一共三个文件：

| 文件 | 职责 |
| --- | --- |
| `agent.go` | 核心。Agent 结构体定义、 `Run()` 主循环、单工具执行、错误恢复 |
| `events.go` | Agent 和 UI 之间的通信协议，定义了所有事件类型 |
| `streaming_executor.go` | 在 LLM 还在输出的时候就开始并行执行工具 |

三个文件加起来不到 600 行。Agent Loop 的复杂度不在代码量，而在它串起了整个系统的几乎所有模块。

## 核心类型

### Agent 结构体

```plain
type Agent struct {
    Client          llm.Client             // LLM 客户端，负责发请求
    Registry        *tools.Registry        // 工具注册中心，所有工具都在这
    Protocol        string                 // 协议标识，用于获取工具 schema
    WorkDir         string                 // 工作目录
    MaxIterations   int                    // 最大迭代次数，0 表示不限
    ContextWindow   int                    // 上下文窗口大小，默认 200000
    Checker         *permissions.Checker   // 权限检查器
    Hooks           *hooks.Engine          // Hook 引擎
    NotificationFn  func() []string        // 动态通知队列
    ToolNameFilter  func(name string) bool // 工具过滤器（团队模式用）
    OnLoopComplete  func(conv *conversation.Manager) // 循环结束回调
    compactTracking compact.AutoCompactTrackingState  // 上下文压缩状态
    eventCh         chan AgentEvent                   // 事件通道
}
```

字段很多，但真正驱动循环的只有前三个： `Client` 负责和 LLM 通信， `Registry` 提供工具， `Protocol` 决定工具描述的格式。其余都是后续章节逐步挂上去的能力。 `Checker` 来自第6章权限系统， `Hooks` 来自第12章， `OnLoopComplete` 来自第9章记忆系统。

Agent 的构造函数很简单，把必要的三件套传进去就行：

```plain
func New(client llm.Client, registry *tools.Registry, protocol string) *Agent {
    wd, _ := os.Getwd()
    return &Agent{
        Client:        client,
        Registry:      registry,
        Protocol:      protocol,
        WorkDir:       wd,
        ContextWindow: 200000,
    }
}
```

### AgentEvent：Agent 和 UI 的通信协议

Agent 和 UI 之间靠事件通信，彼此不直接调用。所有事件类型都实现了 `AgentEvent` 接口：

```plain
type AgentEvent interface{ agentEvent() }

type StreamText struct{ Text string }         // 文本流片段
type ToolUseEvent struct {                     // 工具调用
    ToolID, ToolName string
    Args             map[string]any
}
type ToolResultEvent struct {                  // 工具执行结果
    ToolID, ToolName string
    Output           string
    IsError          bool
    Elapsed          time.Duration
}
```

除了上面这几个，还有 `TurnComplete` （一轮结束）、 `LoopComplete` （循环结束）、 `UsageEvent` （Token 用量）、 `ErrorEvent` （错误）、 `PermissionRequestEvent` （请求用户授权）等。

`PermissionRequestEvent` 比较特殊，它带了一个 `ResponseCh chan<- PermissionResponse` 。Agent 发出权限请求后会阻塞等待，UI 收到事件后弹窗让用户选择允许还是拒绝，选完把结果写回这个 channel。这是 Agent 和 UI 之间唯一的反向通信。

## 主循环走读

### 入口：Run()

```plain
func (a *Agent) Run(ctx context.Context, conv *conversation.Manager) <-chan AgentEvent {
    ch := make(chan AgentEvent, 32) // 带缓冲的事件通道
    go func() {
        defer close(ch)            // goroutine 退出时关闭通道
        // ... 循环逻辑 ...
    }()
    return ch                      // 立即返回，调用方从 channel 消费事件
}
```

这个设计很关键。 `Run()` 不会阻塞调用方，它启动一个 goroutine 在后台跑循环，事件通过 channel 推给 UI。UI 那边用 `for ev := range ch` 消费事件，channel 关闭就知道 Agent 结束了。

缓冲区大小是 32，意味着 Agent 可以连续发 32 个事件而不用等 UI 消费。这让 Agent 的执行节奏不会被 UI 的渲染速度拖慢。

### 循环骨架

进入 goroutine 之后，核心就是一个无限 `for` 循环：

```plain
for iteration := 1; ; iteration++ {
    // 1. 检查迭代上限
    // 2. 检查上下文取消
    // 3. 上下文压缩管理
    // 4. Plan Mode 注入
    // 5. 动态通知注入
    // 6. 获取工具 schema，调用 LLM
    // 7. 消费流式响应
    // 8. 处理停止条件
    // 9. 没有工具调用？→ 结束
    // 10. 收集工具执行结果，准备下一轮
}
```

每一轮做的事情虽然多，但逻辑线很清晰：准备上下文 → 问 LLM → 看 LLM 回什么 → 有工具就执行 → 没工具就结束。

### 调用 LLM 和消费流式响应

LLM 调用只有一行：

```plain
events, errs := a.Client.Stream(ctx, conv, toolSchemas)
```

返回两个 channel，一个是流式事件，一个是错误。然后用 `for range` 消费事件流：

```plain
executor := NewStreamingExecutor(a.Registry, a.Checker, ch)

for ev := range events {
    switch e := ev.(type) {
    case llm.TextDelta:
        text += e.Text
        ch <- StreamText{Text: e.Text}    // 文本片段实时推给 UI
    case llm.ToolCallComplete:
        toolCalls = append(toolCalls, e)
        executor.Submit(ctx, a, e)         // 工具解析完就立即提交执行
    case llm.StreamEnd:
        stopReason = e.StopReason
        usage = e.Usage
    }
}
```

这里有个巧妙的设计： `executor.Submit()` 在 LLM 还在输出后续内容的时候就把已经解析完的工具调用提交给执行器了。假设 LLM 返回了三个工具调用，第一个解析完就立刻开始执行，不用等后面两个。这样工具执行和 LLM 输出是并行的。

### 终止判断：状态机思维

LLM 响应处理完之后，整个循环就走到一个分岔口：

```plain
if len(toolCalls) == 0 {
    conv.AddAssistantFull(text, thinkingBlocks, nil)
    ch <- LoopComplete{TotalTurns: iteration}
    if a.OnLoopComplete != nil {
        go a.OnLoopComplete(conv) // 异步触发，不阻塞
    }
    return // 退出 goroutine，channel 被 defer close
}
```

没有工具调用，说明 LLM 认为任务完成了，循环结束。有工具调用，继续往下走去收集工具执行结果，然后进入下一轮迭代。

`OnLoopComplete` 用 `go` 启动，是个 fire-and-forget 的异步回调。第9章的记忆系统会挂在这里，在 Agent 结束后异步提取对话中的记忆，不影响 Agent 的退出速度。

### 工具结果收集

工具在流式阶段就已经开始执行了，这里只需要等它们全部跑完：

```plain
results := executor.CollectResults()

var toolResults []conversation.ToolResultBlock
for _, r := range results {
    ch <- ToolResultEvent{...} // 每个结果推给 UI

    truncated := r.output
    if len(truncated) > tools.MaxOutputChars {
        truncated = truncated[:tools.MaxOutputChars] + "\n… (output truncated)"
    }
    toolResults = append(toolResults, conversation.ToolResultBlock{
        ToolUseID: r.toolID,
        Content:   truncated,
        IsError:   r.isError,
    })
}
conv.AddToolResultsMessage(toolResults)
```

注意这里有个截断操作：工具的完整输出推给 UI 展示，但写进对话历史的是截断版本。一个 `grep` 命令可能返回几万行结果，全塞进对话会把上下文撑爆，所以只保留前 `MaxOutputChars` 个字符。

## 四个停止条件

理论篇讲了四个停止条件，看它们在代码里怎么实现的：

**1\. LLM 不再调用工具**

就是上面那个 `if len(toolCalls) == 0` 判断。这是最常见的正常退出路径。

**2\. 迭代次数上限**

```plain
if a.MaxIterations > 0 && iteration > a.MaxIterations {
    ch <- ErrorEvent{Message: fmt.Sprintf(
        "Agent reached maximum iterations (%d)", a.MaxIterations)}
    return
}
```

在循环最开头检查。 `MaxIterations` 为 0 表示不限制。

**3\. 连续未知工具**

```plain
if r.isUnknown {
    consecutiveUnknown++
} else {
    consecutiveUnknown = 0
}
// ...
if consecutiveUnknown >= 3 {
    ch <- ErrorEvent{Message: "Too many consecutive unknown tool calls"}
    return
}
```

连续 3 次调用不存在的工具就终止。注意是「连续」，中间有一次正常调用就重置计数。这能防止 LLM 陷入反复尝试一个不存在工具的死循环。

**4\. 用户取消**

```plain
if ctx.Err() != nil {
    return
}
```

用户按 Esc 时，上层代码会取消 `context` ，循环在每轮开头检查 context 状态。一旦 context 被取消，静默退出，不发 ErrorEvent。

## 工具执行

### StreamingExecutor：边流式边执行

`StreamingExecutor` 的核心思路是把工具执行从主循环里解耦出来。每个工具调用一解析完就提交：

```plain
func (se *StreamingExecutor) Submit(ctx context.Context, agent *Agent, tc llm.ToolCallComplete) {
    se.mu.Lock()
    idx := len(se.pending)
    se.pending = append(se.pending, pendingTool{call: tc})
    se.mu.Unlock()

    se.wg.Add(1)
    go func() {
        defer se.wg.Done()
        result := agent.executeSingleTool(ctx, se.eventCh, tc)
        se.mu.Lock()
        se.pending[idx].result = result
        se.pending[idx].done = true
        se.mu.Unlock()
    }()
}
```

每次 `Submit` 都启动一个 goroutine。如果 LLM 一次返回了三个工具调用，这三个 goroutine 会并行执行。 `CollectResults()` 用 `sync.WaitGroup` 等所有 goroutine 跑完，然后按提交顺序返回结果。

### 单工具执行流程

`executeSingleTool` 是工具执行的完整管线，按顺序走四关：

**第一关：查找工具** 。在 Registry 里找不到就返回 unknown 错误。

**第二关：权限检查** 。 `Checker.Check()` 返回三种结果。 `Deny` 直接拒绝； `Allow` 放行； `Ask` 就发一个 `PermissionRequestEvent` 给 UI，然后阻塞等用户回应：

```plain
respCh := make(chan PermissionResponse, 1)
eventCh <- PermissionRequestEvent{
    ToolName:   tc.ToolName,
    Desc:       desc,
    ResponseCh: respCh,
}
resp := <-respCh // 阻塞，直到用户点允许或拒绝
```

**第三关：Pre-tool Hook** 。Hook 引擎可以拦截工具执行，这是整个 Hook 系统里唯一能「阻断」的事件。

**第四关：真正执行** 。 `tool.Execute(ctx, tc.Arguments)` 调用工具的实际逻辑，拿到结果后再触发 post-tool Hook。

## Plan Mode

Plan Mode 的实现出奇简单。它不改变循环结构，只在每轮迭代开头注入一段提示词：

```plain
if a.Checker != nil && a.Checker.Mode == permissions.ModePlan {
    planPath := planfile.GetOrCreatePlanPath(a.WorkDir)
    a.Checker.PlanFilePath = planPath
    planExists := planfile.PlanExists(a.WorkDir)
    reminder := prompt.BuildPlanModeReminder(planPath, planExists, iteration)
    conv.AddSystemReminder(reminder)
}
```

它做了两件事：一是告诉权限检查器 Plan 文件的路径，让写 Plan 文件成为例外（不被 Plan Mode 的只读限制拦住）；二是往对话里注入一段 system-reminder，告诉 LLM 现在处于规划模式，只能思考和分析，不能执行写操作。

LLM 收到这个提示后就会自觉地只输出文字分析，不调用写工具。即使它尝试调用，权限系统也会拦住。两层保障。

## 小结

| 设计决策 | Go 的实现方式 |
| --- | --- |
| 异步事件流 | goroutine + buffered channel（容量 32） |
| 主循环 | 无限 `for` + 多个 `return` 出口 |
| 工具并行 | StreamingExecutor，每个工具一个 goroutine |
| 权限交互 | 带 response channel 的事件，Agent 阻塞等待 |
| Plan Mode | 注入 system-reminder + 权限层拦截 |
| 上下文保护 | 工具输出截断后再写入对话历史 |
| 结束回调 | `go OnLoopComplete(conv)` fire-and-forget |