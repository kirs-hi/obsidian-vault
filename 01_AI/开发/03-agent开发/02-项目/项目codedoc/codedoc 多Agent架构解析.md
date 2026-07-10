# codedoc 多 Agent 架构解析（agents/graph.py）

## 1. 这是什么

codedoc 的核心是一个用 **LangGraph** 搭的**多 Agent 问答图**。
用户问一个代码相关问题，系统不是简单检索一下就返回，而是让多个 Agent 分工协作：
规划 → 单仓深挖 → 跨仓推理 → 合成答案 → 反思补检索。

代码位置：`codedoc/agents/graph.py`

## 2. 基础概念先搞懂

### Agent
普通程序是写死的 if-else 流程。
Agent 是"LLM 当大脑来决定下一步干嘛"，给它一堆工具，它自己决定用哪个、什么时候停。

### 多 Agent
多个 Agent 协作，每个负责一个环节，串起来完成大任务。
就像公司：销售接单 → 生产部制造 → 质检部检查 → 发货部发货。

### LangGraph
LangChain 团队出的框架，专门搭"有状态、多步骤的 Agent 工作流"。

核心概念：
- **StateGraph**：整个工作流是一张图，一个 State 在节点间流转
- **Node**：处理单元，就是一个函数，读 state、改 state
- **Edge**：节点间连接，决定下一步去哪
- **Conditional Edge**：根据 state 内容路由（相当于 if-else）
- **Send**：扇出，把一个节点变成多个并行任务
- **Checkpointer**：每步存 state，崩了能续传

### LangGraph vs 旧版 AgentExecutor
- AgentExecutor：只能跑线性 ReAct 循环，没法做并行扇出、条件路由
- LangGraph：状态机，支持扇出/条件边/环/检查点，灵活得多
- 现在搭多 Agent 都用 LangGraph，AgentExecutor 已过时

## 3. 整体架构图

```
START
  ↓
planner（规划：选仓 + 分流 fast/react）
  ↓ [Send 扇出]
repo_agent × N（N 个仓并行深挖）
  ↓
merger（跨仓推理）
  ↓
synthesiser（合成答案）
  ↓
reflect（反思够不够）
  ├── 够了 → END
  └── 不够 → refine（补检索）→ 回 synthesiser 重答
```

大白话流程：
1. 用户问一个问题
2. Planner：决定去哪些仓找、问题简单还是复杂
3. 扇出：对每个选中的仓，并行起一个 RepoAgent 深挖
4. 每个 RepoAgent 在自己的仓里找证据
5. 所有 RepoAgent 跑完，Merger 合并各仓发现 + 推理跨仓关系
6. Synthesiser 拼上下文，让 LLM 生成答案
7. Reflect 检查答案够不够好，不够就指出缺什么
8. 不够走 Refine 补检索，回 Synthesiser 重答
9. 够了结束

## 4. State——所有节点共享的"黑板"

所有节点都在读写同一个 State。

关键字段：
- `question` 用户问题
- `repos` 要查的仓列表
- `selected` Planner 选中的仓
- `mode` "fast"（简单）还是 "react"（复杂）
- `repo_results` 各仓深挖结果（并行归并）
- `merged` Merger 合并后的结果
- `cross_text` 跨仓关系文本
- `answer` 最终答案
- `need_more` 反思后是否需要补检索
- `gap` 反思指出的缺口
- `reflect_rounds` 反思了几轮（防无限循环）
- `trace` 执行轨迹

两个关键设计：
- `repo_results: Annotated[list[dict], operator.add]`：多个并行 RepoAgent 的结果用 operator.add（列表拼接）自动合并，不互相覆盖
- `trace: Annotated[list[dict], operator.add]`：执行轨迹自动累积

## 5. 逐个节点讲

### 5.1 Planner（规划）

干三件事：

**第一：选仓**
- 仓 ≤ 4 个：全选
- 仓太多：每个仓搜一下，按命中数排序取 top-4

**第二：预热嵌入缓存**
- 提前调一次 `_embed_query_cached`，后面 RepoAgent 都走缓存，省 API

**第三：分流 fast / react**
- 用正则匹配问题里的关系词（调用/caller/依赖/跨仓/流程等）
- 命中 → react（真 Agent，贵但深）
- 不命中 → fast（规则检索，便宜快）

为什么分流？成本优化。简单问题用不上 Agent，复杂问题才需要 Agent 探调用链。

### 5.2 扇出（fan_out / Send）

```python
def fan_out(state):
    return [Send("repo_agent", {"question": state["question"], "repo": r, "mode": m})
            for r in state["selected"]]
```

不是普通节点，是扇出函数。给每个仓创建独立 state 发给 repo_agent。
3 个仓就并行起 3 个 repo_agent，跑完结果自动归并（靠 Annotated[list, operator.add]）。

这是 LangGraph 核心能力：并行扇出 + 自动归并，不用自己写线程池。

### 5.3 RepoAgent（单仓深挖）——重点

两种模式：

**fast 模式**（简单问题）：
- 直接 search 取 top-8 + get_body 取 top-3 源码
- 不调 LLM，快、省

**react 模式**（复杂问题）：
- 调真 ReAct Agent（`_react_repo_agent`）
- LLM 自主决定用哪个工具（search/callers/callees/impact/explore/dossier）
- 一步步探索，直到够了或到上限

两种都返回：items（符号节点）+ bodies（源码）+ relations（关系档案）

### 5.4 Merger（跨仓推理）

两步：

**第一步：确定性找同名符号（硬线索）**
- 遍历所有仓的发现
- 某符号名（如 authenticate）出现在 ≥2 个仓 → 记下来
- 这是实打实查出来的，不靠 LLM 猜

**第二步：LLM 跨仓推理**
- 把各仓发现 + 同名线索喂 LLM
- system prompt 强调"只依据事实、不编造"
- 推理跨仓关系：共享接口/调用边界/分层依赖

特殊情况：
- 单仓（<2）跳过跨仓推理
- LLM 失败降级为纯同名符号列表

### 5.5 Synthesiser（合成答案）

- 把每个仓的 relations + top-6 符号 + 源码拼成上下文
- 加上跨仓关系文本
- 喂 LLM 生成答案

system prompt 三个约束（都是抗幻觉）：
1. 只依据上下文回答
2. 符号用反引号标仓库
3. 不编造上下文里没有的符号

### 5.6 Reflect（反思）

亮点：Agent 会自我反思。

流程：
- fast 模式不反思
- 让 LLM 自评答案是否"充分且有据"，输出 JSON（sufficient + gap）
- 触发补检索要同时满足：
  1. LLM 判不充分 或 答案含 hedge 词（未找到/无法回答/没有相关等）
  2. 还没反思过（rounds < 1）
  3. 有具体缺口
- 只反思 1 轮（防无限循环 + 反复横跳 + 成本）

### 5.7 Refine（补检索）

- 拿 Reflect 指出的 gap 当新查询
- 在选中仓里再搜一遍
- 结果 append（不是覆盖）到 merged
- 回 Synthesiser 重新生成答案

### 5.8 路由

```python
def _after_reflect(state):
    return "refine" if state.get("need_more") else "end"
```

### 5.9 检查点（PostgresSaver）

- 每个 super-step 把 state 落 PG，按 thread_id 索引
- 崩溃后用相同 thread_id 再 invoke，从最后 checkpoint 恢复
- 初始化失败优雅降级（无 checkpoint 也能跑）

### 5.10 组装图

```
START → planner
planner --[fan_out 扇出]--> repo_agent
repo_agent --> merger
merger --> synthesiser
synthesiser --> reflect
reflect --[need_more?]--> refine → synthesiser（重答）
                     └──> END
```

## 6. 关键设计决策

### 为什么用 Send 扇出而不是串行
3 个仓串行要 3 倍时间，并行只要最慢那个的时间。Send 原生支持，不用自己管线程池，结果自动归并。

### 为什么 fast/react 分流
成本优化。简单问题用 Agent 是浪费（贵+慢），复杂问题不用 Agent 探不深。贵的只用在需要的地方。

### 为什么 Merger 先确定性找同名再上 LLM
同名符号是硬事实（查图谱就知道）。先给 LLM 硬线索，推理才靠谱。抗幻觉设计。

### 为什么反思只 1 轮
成本（每轮调LLM）+ 稳定性（多轮反复横跳）+ 1轮已覆盖大部分缺口。

### 为什么要有降级
每个环节 try-except 降级：
- PostgresSaver 失败 → 无 checkpoint
- react agent 失败 → 确定性 fallback
- Merger LLM 失败 → 纯同名列表

保证任意环节挂了，问答还能出个能用的结果，不因单点故障废掉。

## 7. 面试深问应答卡

### Q1：讲讲你的多 Agent 架构
A：用 LangGraph 搭的状态图。Planner 选仓+分流(fast/react) → Send 扇出 N 个 RepoAgent 并行深挖 → Merger 跨仓推理(确定性同名线索+LLM) → Synthesiser 合成答案 → Reflect 反思不够补检索重答。检查点用 PostgresSaver 落 PG 续传。

### Q2：LangGraph 和 AgentExecutor 区别
A：AgentExecutor 是线性 ReAct 循环，没法做并行扇出、条件路由、supervisor 决策。LangGraph 是状态机，支持 StateGraph+Node+Conditional Edge+Send 扇出+Checkpointer，能搭复杂多 Agent 工作流。

### Q3：Send 扇出怎么工作？结果怎么合并
A：Send 给每个仓创建独立 state 发给 repo_agent，LangGraph 并行起 N 个。结果合并靠 State 里 `repo_results: Annotated[list[dict], operator.add]`，多个并行节点返回的列表用 operator.add 自动拼接，不互相覆盖。

### Q4：Planner 为什么分 fast/react
A：成本优化。简单问题用不上 Agent，fast 直接 search+get_body 不调 LLM，快且省；复杂问题（含关系词）才上 react 真 Agent。贵的只用在需要的地方。

### Q5：Merger 怎么做跨仓推理
A：两步。先确定性找同名符号（≥2仓出现同一符号名），这是硬线索；再把各仓发现+同名线索喂 LLM 推理跨仓关系，system prompt 强调不编造。单仓跳过，LLM 失败降级为纯同名列表。

### Q6：Reflect 为什么只 1 轮
A：成本（每轮调LLM）+ 稳定性（多轮反复横跳）+ 1轮已覆盖大部分缺口。触发补检索要同时满足：LLM判不充分或含hedge词 + 还没反思过 + 有具体缺口。fast模式不反思。

### Q7：检查点怎么存？崩溃续传原理
A：用 PostgresSaver，每个 super-step 把 state 落 PG，按 thread_id 索引。崩溃后用相同 thread_id 再 invoke，从最后 checkpoint 恢复。初始化失败优雅降级。

### Q8：为什么每个环节都 try-except
A：保证任意环节挂了，问答还能出个能用的结果。react agent 失败退回确定性 fallback，Merger LLM 失败退回纯同名列表，PostgresSaver 失败退回无 checkpoint。不因单点故障废掉整个问答。

### Q9：StateGraph 的 State 怎么设计
A：TypedDict，total=False 全可选。并行字段用 `Annotated[list, operator.add]` 做自动归并，trace 也一样累积。

### Q10：和 multi_agent.py 那套区别
A：两套架构。graph.py 是 Planner 一次性选仓+fan_out 并行+反思环，快但仓固定；multi_agent.py 是 supervisor 状态机，每阶段回总调度决策，支持运行时扩仓，灵活但贵。

## 8. 你要怎么准备

1. 打开 `codedoc/agents/graph.py`，从头到尾逐行读
2. 默画架构图：planner → [Send扇出] repo_agent×N → merger → synthesiser → reflect → (refine→synthesiser | END)
3. 背熟 10 张应答卡
4. 能讲清 5 个设计决策：为什么扇出/为什么分流/为什么先确定性再LLM/为什么反思1轮/为什么降级
