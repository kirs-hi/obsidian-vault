# 实战演练：运维Agent代码实现\(Go\)

**注意，运行程序之前请先看：**

•

•

# 前言

关键代码：​

•SuperBizAgent/internal/ai/agent/plan\_execute\_replan

•SuperBizAgent/internal/ai/cmd/ai\_ops\_cmd/main\.go

![[Oz9Yb85g5oVYCOxucwGcBbTEn9f.png]]

# 流程梳理

运维Agent的核心目标是 规划\-\>执行\-\>评估\-\>调整。整体流程就是三个步骤：​

1. **Planer：拆解排查步骤**

1. **Executer：执行计划第一步**

1. **Replaner：评估结果并调整计划**

![[YO5GbPfZQoWFH7xIr1hcJBmXncf.png]]

# 实战

注意，在运行代码之前，务必先看

•【飞书文档】环境准备教程

◦搜索

•【飞书文档】运行项目教程

◦搜索

## Runnable执行器

### 运行Agent看看输出

我们来分析一下执行步骤：​

1. 首先Planner规划了7个执行步骤

1. Executor执行第一步，获取当前时间

1. Executor执行第二步，发现没有正在活动的告警，无法执行后续步骤，流程扭转到Replanner

1. Replanner发现没有活动的告警，则执行退出操作

```SQL

```

### 执行代码研究

好，执行完成后。我们先来研究一个prompt是怎么写的：​

1. 首先，我们要求它先通过 query\_prometheus\_alerts 工具获取所有活跃的告警

1. 如果有告警，那么通过 query\_internal\_docs 查询告警的解决方案

1. 并且要求大模型必须基于内部文档的解决方案来执行，不能乱执行

```Go

```

观察程序输出的日志，可以看到Planner制定的计划：

```JSON

```

紧接着Executor按照计划依次执行：​

1. 调用get\_current\_time获取当前时间

1. 调用query\_prometheus\_alerts获取活跃中的告警

然后Replan发现没有活跃中的告警，那么说明系统正常，则可以退出了。

```YAML

```

## BuildPlanAgent研究

1. 首先我们创建了3个Agent： NewPlanner、NewExecutor、NewRePlanAgent

1. 然后通过planexecute\.New创建了一个协调器，最后执行

1. 这里的 NewPlanner、NewExecutor、NewRePlanAgent、planexecute\.New、adk\.NewRunner 全部都是eino官方提供的sdk，我们直接使用sdk进行组装即可

```Go

```

## Planner

**核心功能： **根据用户目标生成初始任务计划（结构化步骤序列）

**实现方式 **：

•通过 PlanTool 生成符合 JSON Schema 的步骤列表。

•或直接使用支持结构化输出的模型，直接生成 Plan 格式结果

**输出 **： Plan 对象， Plan 对象就是计划列表，存储在Session中，供其他Agent使用

下面是Planner的system prompt，其核心就是要求大模型根据输入返回一个执行计划

```Markdown

```

## **Executer**

**核心功能 **：执行计划中的首个步骤，调用外部工具完成具体任务

**实现方式 **：

•从 Session 中获取当前 Plan 和已执行步骤

•提取计划中的第一个未执行步骤作为目标

•调用工具执行该步骤，将结果存储于 Session

**关键能力 **： **本质就是一个魔改的ReAct设计模式的Agent，支持多轮工具调用，确保单步任务完成。**

```Markdown

```

## Replanner

**核心功能 **：评估执行进度，决定继续执行（生成新计划）或终止任务（返回结果）

**实现方式 **：通过 PlanTool （生成新计划）或 RespondTool （返回结果）输出决策

**决策逻辑 **：

•**继续执行 **：若目标未达成，生成包含剩余步骤的新计划，更新 Session 中的 Plan

•**终止任务 **：若目标已达成，调用 RespondTool 生成最终用户响应

```Shell

```

# 总结

通过上面的分析，我们已经了解了Planner、Executer、Replanner的作用和相关prompt。但是你可能会有一种意犹未尽的感觉，因为我们在这里全部都是调用sdk，实际代码只是组装而已。不要慌，我们再回过头来看看Plan\-Execute\-Replan的流程。

1. 首先用Planner Agent生成了一份计划

1. 将计划发送给Executor Agent，让Executor按照计划执行

1. 每次执行完，都将计划和执行结果一起发送给Replanner评估

1. Replanner评估后决定修改计划还是决定已完成

其实 Planner、Executer、Replanner 之间的交互逻辑很简单，就是上面的4个步骤，只要你搞明白了这4个步骤。我们自己用代码实现这个workflow流程也很简单， **其核心就是流程控制，与Plan对象在整个流程中的传递而已。**

所以无需担心，面试会问到的所有细节，在面试攻略篇章全部为你准备好了。（想想gorm，jdbc这些数据库sdk，我们也只是使用而已，会用即可，只要八股文准备的好，无需紧张～）
