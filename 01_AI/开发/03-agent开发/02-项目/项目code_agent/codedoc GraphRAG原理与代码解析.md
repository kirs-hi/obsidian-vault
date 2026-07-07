# codedoc GraphRAG原理与代码解析

## 1. GraphRAG 是什么

GraphRAG 可以理解成：

- 普通 RAG：适合回答局部问题，比如“某个函数怎么实现”
- GraphRAG：适合回答全局问题，比如“这个项目整体架构是什么”“主要有哪些子系统”

普通 RAG 的问题是，它只能召回一些零散片段。对于“整体架构”这种问题，答案并不在某一个代码片段里，而是分散在很多模块、类、函数之间。直接把零散片段丢给 LLM，LLM 很难拼出全貌。

GraphRAG 的思路是：

1. 先把整张知识图谱切成多个“社区”（community），每个社区可以理解成一个联系紧密的子系统
2. 再让 LLM 给每个社区写一句摘要（map）
3. 用户问全局问题时，把这些社区摘要汇总给 LLM，让它生成整体回答（reduce）

所以 GraphRAG 本质上是一个“先社区划分，再摘要归纳”的全局问答方案。

## 2. codedoc 里为什么要用 GraphRAG

codedoc 里既有：

- 局部问题：例如“`place_order` 被谁调用”“某个函数怎么实现”
- 全局问题：例如“这个项目整体架构是什么”“主要模块有哪些”“代码是怎么组织的”

对于局部问题，向量检索 + 图遍历就够了。
对于全局问题，普通检索拿到的是很多零散命中，无法直接回答“整体结构”。

所以 codedoc 的策略是：

- 全局问题 -> GraphRAG
- 非全局问题 -> 正常多 Agent / 检索流程

## 3. 代码在哪里

主要代码在：

- `codedoc/graphrag.py`
- `server.py`

其中：

- `codedoc/graphrag.py`：GraphRAG 的核心实现
- `server.py`：把 GraphRAG 接入主问答流程

## 4. codedoc 里的 GraphRAG 流程

### 4.1 先判断是不是“全局问题”

代码位置：`codedoc/graphrag.py`

函数：`is_global_question(q: str) -> bool`

做法很简单：用一个正则去匹配“架构、整体、主要模块、overview、architecture、high-level”等关键词。

只要问题里命中了这些词，就认为这是一个适合走 GraphRAG 的问题。

例如：

- “这个项目整体架构是什么？”
- “主要有哪些模块？”
- “代码是怎么组织的？”

这类问题都会被判定为全局问题。

### 4.2 把知识图谱转成 networkx 图

代码位置：`codedoc/graphrag.py`

函数：`community_summaries(store, llm, top_k=12)`

它会做几件事：

1. 新建一个 `networkx.Graph()`
2. 把 `store.nodes.keys()` 全部加进去
3. 把 `store.edges` 里的边也加进去

这样，原本 codedoc 内存里的知识图谱，就被转换成了 networkx 可处理的图结构。

这里用的是无向图 `nx.Graph()`，不是有向图。因为在做“社区划分”时，重点不是调用方向，而是“哪些节点联系更紧密、应该归成一个子系统”。

### 4.3 用 Louvain 算法做社区划分

代码位置：`codedoc/graphrag.py`

核心代码：

```python
comms = sorted(nx.community.louvain_communities(g, seed=42), key=len, reverse=True)[:top_k]
```

这一步是 GraphRAG 的核心。

Louvain 是一个社区发现算法，目标是最大化“模块度（modularity）”。
你可以把它理解成：

- 如果一群节点之间连接特别密集
- 而和外部节点连接相对较少
- 那它们就更像一个“社区”或“子系统”

Louvain 的好处：

- 速度快
- 不需要提前指定社区数量
- 很适合稀疏图
- networkx 里直接能用

在 codedoc 里，知识图谱本来就是“代码依赖图/调用图”，天然适合做社区划分。

### 4.4 每个社区生成一句话摘要（map）

还是在 `community_summaries()` 里。

对每个社区，代码会：

1. 找出社区里所有成员节点
2. 提取它们的代表符号名（`qualified_name` 或 `name`）
3. 提取这些符号所在的文件列表
4. 构造 prompt，让 LLM 用一句话概括“这个子系统负责什么”

prompt 大意是：

- 这是一个联系紧密的代码社区
- 文件是这些
- 代表符号是这些
- 请用一句话（<=30字）概括这个子系统负责什么

LLM 返回后，会存成类似：

```python
{"id": i, "size": len(comm), "files": files[:6], "summary": summary}
```

这一步就是 map：

- 每个社区独立摘要一次
- 最后得到一组“子系统摘要”

### 4.5 汇总社区摘要回答用户问题（reduce）

代码位置：`codedoc/graphrag.py`

函数：`answer_global(question, summaries, llm)`

它会把所有社区摘要拼成一个上下文，例如：

- 子系统0（45个符号，文件 A/B/C）：负责订单主流程
- 子系统1（30个符号，文件 D/E/F）：负责用户鉴权
- 子系统2（20个符号，文件 G/H）：负责库存预留

然后把这个上下文交给 LLM，要求它回答用户的“整体架构”问题。

这一步就是 reduce：

- 前面 map 阶段得到的是多个局部摘要
- 这里把局部摘要汇总成最终的全局回答

## 5. GraphRAG 在主流程里是怎么接入的

接入位置在：`server.py`

大致流程是：

1. 用户发起问答请求
2. 服务先判断 `graphrag.is_global_question(req.question)`
3. 如果是全局问题：
   - 先看缓存里有没有 `_comm_summaries`
   - 没有就调用 `graphrag.community_summaries(store, build_llm(cfg))`
   - 拿到社区摘要后，再调用 `graphrag.answer_global(...)`
4. 返回答案时，`mode` 会标成 `graphrag`

也就是说，GraphRAG 不是替代所有问答，而是作为一个专门处理“整体架构类问题”的分支。

## 6. 为什么要缓存社区摘要

在 `server.py` 里可以看到：

- 首次问全局问题时，才会计算 `_comm_summaries`
- 算完后缓存到 `info["_comm_summaries"]`

原因很简单：

- 社区划分虽然不算特别慢
- 但每个社区都要调一次 LLM 写摘要
- 如果每次问“整体架构”都重算，成本太高、延迟也高

所以更合理的方式是：

- 首次计算
- 后续直接复用

这相当于把“社区摘要”当成图谱的高层索引。

## 7. GraphRAG 和普通 RAG 的区别

### 普通 RAG

流程：

1. 用户问题
2. 向量检索 top-k 片段
3. 把片段喂给 LLM
4. LLM 输出答案

适合：

- 某个函数怎么实现
- 某个类在哪里定义
- 某个接口被谁调用

### GraphRAG

流程：

1. 用户问题
2. 判断是否是全局问题
3. 如果是：图谱 -> 社区划分 -> 社区摘要
4. 汇总社区摘要喂给 LLM
5. LLM 输出全局答案

适合：

- 整体架构
- 主要子系统
- 模块组织方式
- 项目结构概览

一句话总结：

- 普通 RAG = 回答局部
- GraphRAG = 回答全局

## 8. 为什么 codedoc 的 GraphRAG 能回答“整体架构”

因为它不是直接在一堆代码片段里找答案，而是先把整张知识图谱压缩成“几个主要子系统的摘要”。

这就像：

- 普通 RAG：让 LLM 直接读一本书里的几页随机摘录，然后概括整本书
- GraphRAG：先把整本书分章节，再让 LLM 看每章摘要，然后概括全书

后者显然更适合回答“整体”问题。

## 9. 面试时怎么讲这块

### 简版回答

GraphRAG 用来解决普通 RAG 很难回答的全局问题，比如“整体架构”“主要模块有哪些”。
在 codedoc 里，我先把代码知识图谱转成 networkx 图，再用 Louvain 做社区划分，把联系紧密的符号群当成“子系统”。接着让 LLM 给每个社区写一句摘要（map），最后把这些摘要汇总交给 LLM 回答用户问题（reduce）。代码主要在 `codedoc/graphrag.py`，主流程接入在 `server.py`。

### 深一点的回答

普通 RAG 适合回答局部问题，因为它依赖 top-k 片段召回；但全局问题的答案分散在很多模块中，零散召回拼不出全貌。GraphRAG 的思路是先在图结构上做社区发现，再对每个社区做摘要，把局部图压缩成高层语义摘要。codedoc 用的是 networkx 的 Louvain 社区划分，按社区大小取 top-k，再让 LLM 基于“文件列表 + 代表符号”生成一句话职责摘要，最后做 map-reduce 汇总回答。为了控制延迟和成本，社区摘要会缓存，后续复用。

## 10. 一些高频追问

### Q1：为什么选 Louvain？

答：

- 不需要提前指定社区数量
- 速度快
- 适合稀疏图
- networkx 里现成可用

### Q2：为什么社区摘要不直接用源码？

答：

源码太长，而且 GraphRAG 这一层的目标是“高层概括子系统职责”。
文件列表 + 代表符号名已经足够让 LLM 判断这个社区大致负责什么。

### Q3：GraphRAG 为什么只适合全局问题？

答：

因为它做的是“社区级摘要”，粒度比较粗。回答“某个函数怎么实现”这种细问题时，反而不如普通检索 + 源码片段更直接。

### Q4：GraphRAG 的输出会不会幻觉？

答：

会有风险，所以 codedoc 在 `server.py` 里对 GraphRAG 的回答也做了 `_verify_response` 校验，不会因为走的是全局分支就跳过核验。

## 11. 你现在最该记住的 4 句话

1. GraphRAG 是为了解决普通 RAG 不擅长回答“整体架构类问题”
2. codedoc 的 GraphRAG 本质是：知识图谱 -> Louvain 社区划分 -> 社区摘要 -> map-reduce 汇总回答
3. 核心代码在 `codedoc/graphrag.py`
4. 主流程接入在 `server.py`
