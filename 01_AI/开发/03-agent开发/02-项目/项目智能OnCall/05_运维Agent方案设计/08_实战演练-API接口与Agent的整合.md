# 实战演练：API接口与Agent的整合

项目使用goframe作为web框架，如果想了解API定义到提供服务的流程，先看：&#x20;

【飞书文档】小试牛刀：使用goframe框架3分钟实现一个http接口

搜索

text

# AI运维接口

AI运维接口，调用后会自动查询现在活跃的告警，并判断根因

**请求方法&#x20;**: `POST /api/ai_ops`

**请求字段:**

| 字段名​ | 类型​ | 描述​ |
| ---- | --- | --- |
| ​    | ​   | ​   |

**响应字段:**

| 字段名​    | 类型​        | 描述​     |
| ------- | ---------- | ------- |
| Result​ | string​    | 结果​     |
| Detail​ | \[]string​ | 详细信息列表​ |

**示例：**

```Bash
curl -X POST http://localhost:6872/api/ai_ops \
  -H "Content-Type: application/json"
  
# 响应
{
  "message": "OK",
  "data": {
    "result": "汇总的分析结果...",
    "detail": [
      "执行步骤1...",
      "执行步骤2...",
      "..."
    ]
  }
} 
 
```

# AI运维接口核心实现(Go)

代码路径： `SuperBizAgent/internal/controller/chat/chat_v1_ai_ops.go`

1. 因为我们这个Agent比较特殊，有Replan功能，所以我们可以直接让Agent主动查询活跃的告警，如果有告警则让它查询内部文档，自己去规划执行步骤。
2. 所以重点就在我们的prompt设计上，我们需要稍微的指导一下大模型该怎么制定计划。
3. 至于如果有告警该怎么执行，那就看你上传的告警处理手册中写的步骤，写的怎么处理，就会怎么执行。

```Go
func (c *ControllerV1) AIOps(ctx context.Context, req *v1.AIOpsReq) (res *v1.AIOpsRes, err error) {
    query := `
"1. 你是一个智能的服务告警运维分析助手,首先调用工具query_prometheus_alerts获取所有活跃的告警。"
"2. 分别根据告警的名称调用工具query_internal_docs，获取告警名对应的处理方案。"
"3. 完全遵循内部文档的内容进行查询和分析,不允许使用文档外的任何信息。"
"4. 涉及到时间的参数都需要先通过工具get_current_time获取当前时间,再结合用户的时间要求进行传参。"
"5. 涉及到日志的查询,需要先通过日志工具获取相关日志信息，参数必须携带地域和日志主题。"
"6. 分别将告警对应查询到的信息进行总结分析,最后汇总所有告警和总结。"`
    resp, detail, err := plan_execute_replan.BuildPlanAgent(ctx, query)
    if err != nil {
       return nil, err
    }
    if resp == "" {
       return nil, errors.New("内部错误")
    }
    res = &v1.AIOpsRes{
       Result: resp,
       Detail: detail,
    }
    return res, nil

}
```

text

# AI运维接口核心实现(Java)

1. 前面我们讲解了SupervisorAgent的作用以及他们的prompt
2. 所以在API接口使用层面，build出来后直接调用
3. 然后把输出返回出去即可

```Java
/**
 * AI 智能运维接口（SSE 流式模式）- 自动分析告警并生成运维报告
 * 无需用户输入，自动执行告警分析流程
 */
@PostMapping(value = "/ai_ops", produces = "text/event-stream;charset=UTF-8")
public SseEmitter aiOps() {
    SseEmitter emitter = new SseEmitter(600000L); // 10分钟超时（告警分析可能较慢）
    executor.execute(() -> {
        try {
            // 调用 AiOpsService 执行分析流程
            Optional<OverAllState> overAllStateOptional = aiOpsService.executeAiOpsAnalysis(chatModel, toolCallbacks);
            OverAllState state = overAllStateOptional.get();
            logger.info("AI Ops 编排完成，开始提取最终报告...");

            // 提取最终报告
            Optional<String> finalReportOptional = aiOpsService.extractFinalReport(state);
            // 输出最终报告
            if (finalReportOptional.isPresent()) {
                // 发送
            }
        }
    });
    return emitter;
}

public Optional<OverAllState> executeAiOpsAnalysis(DashScopeChatModel chatModel, ToolCallback[] toolCallbacks) throws GraphRunnerException {
    logger.info("开始执行 AI Ops 多 Agent 协作流程");
    // 构建 Planner 和 Executor Agent
    ReactAgent plannerAgent = buildPlannerAgent(chatModel, toolCallbacks);
    ReactAgent executorAgent = buildExecutorAgent(chatModel, toolCallbacks);
    // 构建 Supervisor Agent
    SupervisorAgent supervisorAgent = SupervisorAgent.builder()
            .name("ai_ops_supervisor")
            .description("负责调度 Planner 与 Executor 的多 Agent 控制器")
            .model(chatModel)
    return supervisorAgent.invoke(taskPrompt);
}
```
