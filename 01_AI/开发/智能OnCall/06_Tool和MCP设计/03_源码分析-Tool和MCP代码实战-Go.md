# 源码分析：Tool 和 MCP 代码实战(Go)

# 前言

在《Tool 与 MCP 设计思路》一节中我们提到了几个工具，那么这一节我们就来手把手的写2个工具，并交给大模型使用。

核心代码目录： `SuperBizAgent/internal/ai/tools`

text

# 当前时间查询工具

那么就可以直接按照eino框架的规范，组装接口：

- 第一个参数是 `toolName` ，用于表示工具名
- 第二个参数是 `toolDesc` ，用于告诉大模型这个工具的功能
- 第三个参数是一个函数，里面写核心逻辑即可

```Go
// NewGetCurrentTimeTool 创建获取当前时间的工具
func NewGetCurrentTimeTool() tool.InvokableTool {
    t, err := utils.InferOptionableTool(
       "get_current_time",
       "Get current system time in multiple formats. Returns the current time in seconds (Unix timestamp), milliseconds, and microseconds. Use this tool when you need to retrieve current system time for logging, timing operations, or timestamping events.",
       func(ctx context.Context, input *GetCurrentTimeInput, opts ...tool.Option) (output string, err error) {
          // 获取当前时间
          now := time.Now()
          // 计算各种时间格式
          seconds := now.Unix()                                 // 秒
          milliseconds := now.UnixMilli()                       // 毫秒
          microseconds := now.UnixMicro()                       // 微秒
          timestamp := now.Format("2006-01-02 15:04:05.000000") // 可读格式
          // 构建输出
          timeOutput := GetCurrentTimeOutput{
             Success:      true,
             Seconds:      seconds,
             Milliseconds: milliseconds,
             Microseconds: microseconds,
             Timestamp:    timestamp,
             Message:      "Current time retrieved successfully",
          }
          // 转换为JSON
          jsonBytes, err := json.MarshalIndent(timeOutput, "", "  ")
          if err != nil {
             log.Printf("Error marshaling result to JSON: %v", err)
             return "", err
          }
          return string(jsonBytes), nil
       })
    if err != nil {
       log.Fatal(err)
    }
    return t
}
```

text

**函数的入参和出参，都可以用jsonschema的description来描述参数含义&#x20;**。如此一来，我们的工具和工具描述就写好了

```Go
// GetCurrentTimeInput 获取当前时间的输入参数（无需输入）
type GetCurrentTimeInput struct {
    // 无需输入参数
}

// GetCurrentTimeOutput 获取当前时间的输出结果
type GetCurrentTimeOutput struct {
    Success      bool   `json:"success" jsonschema:"description=Indicates whether the time retrieval was successful"`
    Seconds      int64  `json:"seconds" jsonschema:"description=Current Unix timestamp in seconds since epoch (1970-01-01 00:00:00 UTC)"`
    Milliseconds int64  `json:"milliseconds" jsonschema:"description=Current Unix timestamp in milliseconds since epoch (1970-01-01 00:00:00 UTC)"`
    Microseconds int64  `json:"microseconds" jsonschema:"description=Current Unix timestamp in microseconds since epoch (1970-01-01 00:00:00 UTC)"`
    Timestamp    string `json:"timestamp" jsonschema:"description=Human-readable timestamp in format 'YYYY-MM-DD HH:MM:SS.microseconds'"`
    Message      string `json:"message" jsonschema:"description=Status message describing the operation result"`
}
```

text

# 腾讯云日志MCP工具

通过 MCP Server 查询日志服务 CLS 中存储的日志数据，以实现大模型平台/工具与日志数据的结合。例如使用自然语言查询日志，降低日志查询复杂度 https\://cloud.tencent.com/developer/mcp/server/11710

MCP配置： [【飞书文档】环境准备教程](https://my.feishu.cn/https%3A%2F%2Fmy.feishu.cn%2Fwiki%2FOwlIwVXjXiL4o1k7nnFcWQ2wnHb)

text

首先我们创建一个 SSE MCP 客户端。创建后进行初始化，最后调用GetTools获取所有可用的工具即可

```Go
import (
    "context"
    e_mcp "github.com/cloudwego/eino-ext/components/tool/mcp"
    "github.com/cloudwego/eino/components/tool"
    "github.com/mark3labs/mcp-go/client"
    "github.com/mark3labs/mcp-go/mcp"
)

func GetLogMcpTool() ([]tool.BaseTool, error) {
    ctx := context.Background()
    // 1. 创建客户端
    cli, err := client.NewSSEMCPClient("https://mcp-api.tencent-cloud.com/sse/ac4XXXXXX")
    if err != nil {
       return []tool.BaseTool{}, err
    }
    err = cli.Start(ctx)
    if err != nil {
       return []tool.BaseTool{}, err
    }
    // 2. 协商协议
    initRequest := mcp.InitializeRequest{}
    initRequest.Params.ProtocolVersion = mcp.LATEST_PROTOCOL_VERSION
    initRequest.Params.ClientInfo = mcp.Implementation{
       Name:    "example-client",
       Version: "1.0.0",
    }
    if _, err = cli.Initialize(ctx, initRequest); err != nil {
       return []tool.BaseTool{}, err

    }
    // 3. 获取工具
    mcpTools, err := e_mcp.GetTools(ctx, &e_mcp.Config{Cli: cli})
    if err != nil {
       return []tool.BaseTool{}, err
    }
    return mcpTools, nil
}
```

text
