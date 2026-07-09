# codedoc ReAct Agent 防死循环与兜底解析

## 1. ReAct 是什么

ReAct = Reasoning + Acting，让 LLM 当大脑"想一步做一步"：

```
思考（Thought）→ 行动（Action）→ 观察（Observation）→ 再思考 → … → 觉得够了 → 给答案
```

例子，用户问"`place_order` 的调用链"：
- Thought1：先找到 place_order → Action: search("place_order")
- Observation1：找到了，node_id=xxx
- Thought2：看它调用了谁 → Action: callees(node_id=xxx)
- Observation2：调用了 reserve、charge、send_email
- Thought3：一步查清楚 → Action: dossier(node_id=xxx)
- Observation3：拿到完整邻域档案
- Thought4：够了 → Action: DONE

## 2. 教科书 ReAct 的问题

1. 死循环：LLM 可能反复调同一工具停不下来
2. 纯文本解析：LLM 输出一段含 Thought/Action 的文字，要正则解析，容易解析错
3. 没有降级：agent 失败整个就废了

这个项目的 ReAct 针对这三个问题都做了改进——这就是"我和教科书区别"。

## 3. 代码位置

- `_react_repo_agent`：`codedoc/agents/graph.py` 143-233 行（真 ReAct 主逻辑）
- `_dossier_on`：76-119 行（一步取全邻域工具）
- `_deep_repo_agent`：122-140 行（降级兜底）

## 4. 项目的 ReAct 怎么跑（逐段）

### 4.1 system prompt——告诉 LLM 有哪些工具

告诉 LLM：
1. 目标：回答问题
2. 每步只输出一个 JSON（结构化，不是纯文本）
3. 6 个工具：search / callers / callees / impact / explore / dossier
4. 约束：node_id 必须用已观察过的真实 id（防 LLM 编 id）
5. 提示：定位到核心符号后优先用 dossier 一步取全
6. 输出格式：{"thought":"", "action":"...", "args":{}}

和教科书区别1：结构化 JSON 输出。教科书是纯文本要正则解析，这里 LLM 直接输出 JSON，json.loads 就行，稳得多。

dossier 工具是亮点：正常 agent 要 callers 一步、callees 一步、impact 一步、get_body 一步，4步才取全。dossier 一步全取，减少 agent 来回，间接防死循环。

### 4.2 初始化状态

- used：用过的工具列表
- items：找到的符号节点（dict，key=node_id 去重）
- bodies：源码
- relations：关系档案
- history：观察历史（喂给 LLM 看的）
- seen：调用签名去重用（防死循环关键）
- trace：执行轨迹
- dup：重复计数

### 4.3 主循环——每一步

#### 步骤1：拼观察历史，调 LLM

把最近 6 条观察历史拼起来（history[-6:]），加问题，问 LLM "下一步干嘛"。
只给最近 6 条不是全部——上下文窗口管理，太长 token 贵且 LLM 会乱。

#### 步骤2：解析 LLM 输出的 JSON

_parse_action 试三种 pattern 提取 JSON：
1. ```json {...} ```（json 代码块）
2. ``` {...} ```（普通代码块）
3. {...}（裸 JSON）

为什么这么麻烦？LLM 不老实，可能前面加句话或用代码块包起来。三种 pattern 覆盖大部分。
拿到 action，不是 6 个合法工具之一就 break。

#### 步骤3：防死循环第二道闸——签名去重

签名 = 工具名 + 参数，如 `callers|{"node_id": "xxx"}`

逻辑：
- 这个动作做过了 → 跳过这次
- 连续 2 次想重复（dup >= 2）→ break

为什么连续 2 次不是 1 次？给 LLM 一次反省机会。可能第一次重复无意，跳过后会换动作。连续2次还重复说明真卡住了。

#### 步骤4：执行工具

其他工具（search/callers/callees/impact/explore）：
- 调 reg.call 执行
- 无新节点早停（第三道闸）：非 search 工具没带回新节点就 break
- search 除外：search 是换方向用的，可能换方向找到新东西

dossier 工具：
- 调 _dossier_on 一步取全邻域
- 合并进 items 和 bodies

#### 步骤5：记录历史和轨迹

加到 history（给 LLM 下一步看）和 trace（调试用）。

### 4.4 循环结束后的兜底

兜底1：agent 没探到任何东西（if not items）
→ 退回确定性 fallback _deep_repo_agent

兜底2：没源码就补 get_body
→ agent 探到符号但没取源码，手动补 top-3 源码

返回：(items, bodies, relations, used去重, trace)

## 5. dossier 工具——一步取全邻域（亮点）

对一个符号一次并行做 5 件事：
- context：节点详情 + 源码片段
- callers：谁调用它
- callees：它调谁
- impact：改它影响谁
- explore：邻域子图

关键：5 个并行跑（ThreadPoolExecutor max_workers=5），超时保护。一步 dossier 只花最慢那个工具的时间，不是 5 个串行相加。

为什么重要？
- 正常 agent 探索一个符号要 4-5 步，每步调 LLM（贵+慢）
- dossier 一步全取，确定性代码并行取不调 LLM
- 好处：省 LLM 调用、减少步数防死循环、信息更全

设计哲学：agent 自主性和确定性要平衡。纯 agent 太贵容易卡，纯确定性不灵活。dossier 是"定锚后确定性一步取全"，让 agent 不用来回试。

## 6. 降级兜底——_deep_repo_agent

当 _react_repo_agent 失败（没探到东西、异常、LLM 犯傻），退回这个确定性 fallback。

逻辑：
1. search 取 top-8 候选
2. 挑种子——优先名字和问题里 token 匹配的
3. 对种子调 _dossier_on 一步取全邻域
4. 返回合并结果

关键：不调 LLM 决策，纯确定性代码（search 定位 + dossier 取全）。即使 LLM 完全不可用也能出结果。

这就是"降级兜底"：agent 挂了不废整个问答，退回确定性方案。

## 7. 防死循环三道闸（必背）

| 闸 | 在哪 | 干什么 |
|----|------|--------|
| 第一道：max_iter 硬上限 | for step in range(max_iter) | 最多 6 步，到顶强制结束 |
| 第二道：签名去重 | sig = a + "\|" + json.dumps(args) | 同一动作做过跳过，连续2次重复 break |
| 第三道：无新节点早停 | if new == 0 and a != "search": break | 没带回新节点说明探索到头（search除外）|

外加：dossier 一步取全邻域，减少步数间接防死循环。
外加：agent 没探到东西，退回确定性 fallback 兜底。

## 8. 和教科书 ReAct 的区别（面试核心）

| 维度 | 教科书 ReAct | 这个项目的 ReAct |
|------|-------------|-----------------|
| 输出格式 | 纯文本要正则解析 | 结构化 JSON，json.loads |
| 防死循环 | 基本只有 max_iter | 三道闸（max_iter + 签名去重 + 无新节点早停）|
| 工具效率 | 一个工具一步，来回多 | dossier 一步并行取全邻域 |
| 降级 | agent 失败就废 | 退回确定性 fallback |
| 上下文管理 | 全部历史 | 最近 6 条，省 token |

一句话：教科书是"LLM想一步做一步，容易卡容易废"；我这个是"结构化+三道闸+dossier提效+确定性兜底"，工程上能跑稳。

## 9. 面试深问应答卡

### Q1：你的 ReAct 和教科书 ReAct 区别
A：四点。①结构化JSON输出（教科书纯文本正则解析）；②防死循环三道闸（教科书基本只有max_iter）；③dossier一步并行取全邻域减少步数；④降级兜底（agent失败退回确定性fallback）。

### Q2：防死循环三道闸具体
A：第一道max_iter=6硬上限；第二道签名去重——(工具+参数)做过的跳过，连续2次重复break；第三道无新节点早停——非search工具没带回新节点就break（search除外，因为它是换方向用的）。

### Q3：签名去重为什么连续2次才break
A：给LLM一次反省机会。第一次重复可能无意，跳过后会换动作。连续2次还重复说明真卡住了。

### Q4：无新节点早停为什么 search 除外
A：search是换方向/换关键词的工具，可能换方向找到新东西。不能因没新节点就停。其他工具是深挖已知符号，没新节点说明挖到底了。

### Q5：dossier 工具是什么为什么重要
A：对一个符号一次并行取5个工具结果（context+callers+callees+impact+explore+get_body），ThreadPoolExecutor并行。正常agent要4-5步取全，dossier一步搞定。省LLM调用、减少步数防死循环、信息更全。设计哲学是平衡agent自主性和确定性。

### Q6：agent 失败了怎么办
A：退回确定性fallback _deep_repo_agent：search定位种子符号（优先名字匹配问题）→dossier一步取全。纯确定性不调LLM，即使LLM不可用也能出结果。

### Q7：为什么只给 LLM 看最近6条历史
A：上下文窗口管理。太长token贵且LLM会乱。最近6条足够agent知道刚才做了什么、决定下一步。

### Q8：_parse_action 为什么试三种 pattern
A：LLM不老实，可能加句话或用代码块包。三种pattern：```json包裹、```包裹、裸JSON。覆盖大部分情况。

### Q9：max_iter 为什么设 6
A：经验值。太少（3）探不深；太多（20）太贵且容易绕。6步配合dossier一步取全，足够探清一个符号邻域+换1-2次方向。

### Q10：设计哲学
A：agent自主性和确定性平衡。纯agent太贵容易卡，纯确定性不灵活。agent负责"定锚和换方向"（search定位、决定深挖哪个），dossier负责"确定性一步取全邻域"。

## 10. 你要怎么准备

1. 打开 `codedoc/agents/graph.py`，重点读 143-233 行（_react_repo_agent）、76-119 行（_dossier_on）、122-140 行（_deep_repo_agent）
2. 背熟三道闸：max_iter + 签名去重（连续2次break）+ 无新节点早停（search除外）
3. 能讲 dossier 为什么重要：一步并行取全邻域，省步数省LLM
4. 能讲降级兜底：agent失败退回确定性fallback
5. 能讲和教科书5点区别：结构化JSON + 三道闸 + dossier + 降级 + 上下文管理
