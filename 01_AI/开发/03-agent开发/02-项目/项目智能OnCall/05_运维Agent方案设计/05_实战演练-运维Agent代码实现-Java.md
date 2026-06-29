# 实战演练：运维Agent代码实现\(Java\)

# 前言

关键代码：SuperBizAgent/src/main/java/org/example/service/AiOpsService\.java

![[MHAubPeITocTGIx9dducGPkCnug.png]]

# 流程梳理

运维Agent的核心目标是 规划\-\>执行\-\>评估\-\>调整。整体流程就是三个步骤：​

1. **Planer：拆解排查步骤**

1. **Executer：执行计划第一步**

1. **Replaner：评估结果并调整计划**

![[HZgZb1AymoZjmVxLHe9cLfD2n7b.png]]

# 实战

## 创建Plan、Executer Agent

1. 首先我们先使用Spring AI创建两个ReAct类型的Agent

1. Replanner可以创建新的Agent，也可以复用Plan Agent。因为他们两个做的事情都是规划，我们代码简单点，复用Plan

```C++

```

## 构建 Supervisor Agent

Plan\- Execute设计模式本质上就是多个Agent进行协作，这里我们使用框架里的Supervisor来完成。

Multi\-agent： [https://java2ai\.com/docs/frameworks/agent\-framework/advanced/multi\-agent](https://my.feishu.cn/https%3A%2F%2Fjava2ai.com%2Fdocs%2Fframeworks%2Fagent-framework%2Fadvanced%2Fmulti-agent)

![[BoOQban2xoKRDPxpp5icrP8fn3g.png]]

使用框架的Supervisor Agent能力，可以自动的帮助我们管理Plan Agent和Executor Agent之间的执行扭转

```Java

```

# Plan Agent Prompt

```Python

```

# Executor Agent Prompt

```TypeScript

```

# Supervisor Agent Prompt

```Python

```

# 总结

通过上面的分析，我们已经了解了Planner、Executer、Replanner的作用和相关prompt。但是你可能会有一种意犹未尽的感觉，因为我们在这里全部都是调用sdk，实际代码只是组装而已。不要慌，我们再回过头来看看Plan\-Execute\-Replan的流程。

1. 首先用Planner Agent生成了一份计划

1. 将计划发送给Executor Agent，让Executor按照计划执行

1. 每次执行完，都将计划和执行结果一起发送给Replanner评估

1. Replanner评估后决定修改计划还是决定已完成

其实 Planner、Executer、Replanner 之间的交互逻辑很简单，就是上面的4个步骤，只要你搞明白了这4个步骤。我们自己用代码实现这个workflow流程也很简单， **其核心就是流程控制，与Plan对象在整个流程中的传递而已。**

所以无需担心，面试会问到的所有细节，在面试攻略篇章全部为你准备好了。（想想gorm，jdbc这些数据库sdk，我们也只是使用而已，会用即可，只要八股文准备的好，无需紧张～）

![[CUtwbQO5VoBjM9xcfoNc4YYansg.png]]
