---
created: 2026-07-04
tags: [agent, 知识图谱, 架构对比, 简历素材, code-agent]
source: KM文档(contentId:2725883149) + GitHub(codedoc)
---

# 代码知识图谱架构对比：美团采购 KM vs codedoc

> 两个项目核心理念一致——通过 AST 解析构建代码知识图谱，替代传统 RAG 向量检索，提升 AI Coding 对复杂调用链路的理解能力。但在工程实现上走了两条路。

## 一、总体定位对比

| 维度 | 美团采购 KM 项目 | codedoc 项目 |
|---|---|---|
| 定位 | 团队内部 AI Coding 私域知识库 | 通用代码理解问答平台 |
| 服务对象 | 采购研发团队 (~10人) | 任意开发者（SaaS 化） |
| 语言覆盖 | 仅 Java/Spring 微服务 | Python + Java + JS/TS |
| 业务绑定 | 深度绑定采购业务（PO/商品/基础能力） | 无业务绑定，纯技术工具 |
| 成熟度 | 生产在用，有真实效果数据 | Demo 级，AI 生成产物 |
| 代码规模 | 3 个服务仓库，429,726 行 | 单体 server.py 7298 行 |
| 团队背景 | 美团采购研发团队（曾骏飞分享） | 个人项目（贺健，Claude Code 生成） |
| 时间线 | 2025-09 分享，持续建设中 | 2026-06-15 首次提交，12772 行 |

## 二、图谱 Schema 对比

### 2.1 节点类型

| KM 项目（7 种） | codedoc（6 种） | 对应关系 |
|---|---|---|
| SERVICE（微服务，appKey 标识） | — | codedoc 无服务级抽象 |
| SERVICE_ENDPOINT（HTTP/Thrift 接口） | route_handler（HTTP 路由） | 概念相同，KM 多了 Thrift 协议 |
| JAVA_INTERFACE（接口类） | class（kind=class） | codedoc 不区分接口和实现类 |
| JAVA_IMPLEMENTATION（实现类） | class（kind=class） | 同上 |
| METHOD（方法，含 layer 属性） | method / function | KM 用 layer 区分 Controller/Service/Mapper |
| SQL_STATEMENT（SQL 语句） | — | codedoc 不解析 SQL |
| TABLE（数据库表） | — | codedoc 不建模数据层 |
| — | module（文件级模块） | KM 无文件级节点 |
| — | component（Spring Bean） | codedoc 有但粒度不同 |

**关键差异**：KM 项目建模了完整的 Java 微服务分层架构（Service → Endpoint → Interface → Implementation → Method → SQL → Table），覆盖了从 HTTP 入口到数据库表的全链路。codedoc 只建模了代码结构层（module → class → method/function），没有 SQL 和数据库表的概念，无法做"改了这张表会影响哪些 API"的反向追溯。

### 2.2 节点属性

| 属性 | KM 项目 | codedoc |
|---|---|---|
| 唯一标识 | full_name（包名.类名.方法名） | id（文件路径::全限定名） |
| 分层标记 | layer（Controller/Service/Mapper） | kind（module/class/function/method） |
| 协议信息 | protocol（HTTP/Thrift）、http_method、path | route.method、route.path |
| 源码 | 无（图中不存源码） | source 字段存完整源码片段 |
| 签名 | signature | signature |
| 文件路径 | file_path | file |
| 行号 | 无 | start_line、end_line |
| 文档字符串 | 无 | docstring |

### 2.3 边类型

| KM 项目（8 种） | codedoc（7 种） | 对应关系 |
|---|---|---|
| EXPOSES（服务→接口） | — | codedoc 无服务级别 |
| ENDPOINT_IMPLEMENTED_BY（接口→方法） | — | codedoc 无此分层 |
| DECLARES（类→方法） | contains（结构包含） | 语义相同 |
| IMPLEMENTS（实现类→接口类） | extends（继承） | KM 区分 implements/extends |
| METHOD_IMPLEMENTS（方法实现） | — | codedoc 不追踪方法级实现关系 |
| CALLS（方法→方法） | calls（函数调用） | 核心相同，codedoc 多了 confidence 属性 |
| EXECUTES（方法→SQL） | — | codedoc 不解析 SQL |
| OPERATES_ON（SQL→表） | — | codedoc 不建模数据层 |
| — | imports（导入关系） | KM 不建模 import |
| — | bean_inject（Spring 注入） | KM 未显式建模注入 |
| — | impacts（变更影响，运行时生成） | KM 通过 Cypher 查询实现，不存为边 |

**关键差异**：KM 项目的边完整覆盖了 Java 微服务的"服务→接口→类→方法→SQL→表"六层穿透链路，可以一条 Cypher 语句查出从 HTTP 入口到数据库表的完整路径。codedoc 的边只覆盖了代码结构层面（包含、调用、继承、导入），但多了 imports 和 bean_inject 两种 KM 没有的关系。

## 三、存储方案对比

| 维度 | KM 项目 | codedoc |
|---|---|---|
| 图谱存储 | Neo4j 图数据库 | PostgreSQL graph_snapshot 表（JSONB） |
| 查询语言 | Cypher（原生图查询） | Python 内存遍历（NetworkX） |
| 向量存储 | 建设中（未说明具体方案） | pgvector（HNSW 索引，1024 维 BGE-M3） |
| 全文索引 | 无（依赖 Cypher 属性匹配） | 内存 TF-IDF 倒排索引 |
| 业务数据 | 无（纯图谱系统） | PostgreSQL（users/repos/qa_history 等 8 张表） |
| 任务队列 | 无 | PostgreSQL `FOR UPDATE SKIP LOCKED` 抢单 |
| 会话状态 | 无 | PostgreSQL CAS 乐观锁（version 字段） |
| Agent 检查点 | 无 | LangGraph PostgresSaver |

**关键差异**：这是两个项目最大的架构分歧。KM 项目选了图数据库领域的标准答案 Neo4j，Cypher 语言天然支持可变长度路径匹配（`-[:CALLS*0..]->`），做多跳调用链查询时语义清晰、性能好。codedoc 把整个图以 JSONB 形式存在 PostgreSQL 的一行里，运行时加载到内存用 Python 遍历——这是典型的"一人项目"选型，省去了运维 Neo4j 的成本，但牺牲了查询能力和大规模图的性能。

## 四、AST 解析对比

| 维度 | KM 项目 | codedoc |
|---|---|---|
| 目标语言 | Java（仅 Java） | Python + Java + JS/TS |
| 解析工具 | 未明确（推测 JavaParser 或 Eclipse JDT） | Python: 标准库 ast；Java: javalang；JS/TS: tree-sitter |
| 解析范围 | Service/Controller/Mapper 核心代码（排除 DTO） | 全部代码文件 |
| SQL 解析 | MyBatis XML Mapper 文件 → SQL_STATEMENT | 不解析 SQL |
| 框架感知 | Spring 注解识别（推测） | Python: Flask/FastAPI 路由识别；Java: Spring 全套注解（6 种组件 + 6 种路由 + 3 种注入） |
| 跨文件解析 | 完整（基于 Java 全限定名天然唯一） | resolve.py 基于 LEGB 作用域消歧，有 confidence 评分 |
| 解析规模 | 429,726 行 → 12,114 节点 + 24,213 边 | 未知（Demo 级） |

**关键差异**：KM 项目专注 Java 但做得深——解析 MyBatis XML 提取 SQL 语句，建立方法到 SQL 到数据库表的完整链路，这是采购业务的核心需求（"改了这张表会影响哪些接口"）。codedoc 覆盖多语言但做得浅——不解析 SQL、不建模数据层，且 Java 解析用的 javalang 库功能较弱（不支持 Java 17+ 语法），Python 用标准库 ast（不支持不完整代码）。

## 五、检索方案对比

| 维度 | KM 项目 | codedoc |
|---|---|---|
| 图搜索 | LLM → Cypher → Neo4j 执行 → 返回路径 | 内存 Python BFS/DFS 遍历 |
| 向量搜索 | 建设中（代码块 → LLM 生成描述 → embedding） | pgvector HNSW（BGE-M3 1024 维，ef_search=200） |
| 全文搜索 | 无 | 内存 TF-IDF 倒排索引 |
| 混合策略 | 图搜索为主（已完成），向量为辅（建设中） | 向量 0.6 + 全文 0.4 加权融合，精确名命中 +0.5 |
| Reranker | 无 | BGE-reranker-v2-m3（SiliconFlow API） |
| GraphRAG | 无（纯图查询，非 RAG） | Louvain 社区检测 → Map-Reduce 社区摘要 |
| 全局问题 | 不区分 | 正则检测（"架构/整体/overview"等词）→ GraphRAG |
| 多策略叠加 | 无 | 4 层策略（混合搜索 → 锚点补充 → 全文搜索 → 标识符搜索 → 按 kind 采样） |
| Cypher 生成 | LLM + few-shot 示例 + 层级映射规则 | — |

**关键差异**：两个项目在检索层走了完全不同的路线。KM 项目核心依赖 Cypher 精确查询——用户问"queryPoEs 方法的上下游链路"，LLM 生成一条 Cypher 语句，Neo4j 返回精确的调用路径，准确率 100%、召回率 100%。codedoc 走的是 RAG 路线——向量召回 + 全文匹配 + reranker 精排，本质上还是"先检索再生成"，无法保证调用链的完整性。codedoc 的 GraphRAG 模块（Louvain 社区摘要）用于回答"这个项目整体架构是什么"类全局问题，与 KM 项目的 Cypher 链路追溯是不同的使用场景。

## 六、Agent 架构对比

| 维度 | KM 项目 | codedoc |
|---|---|---|
| Agent 框架 | 无独立 Agent（MCP 工具集成到外部 Agent） | LangGraph StateGraph |
| 编排模式 | 外部依赖（接入"元析"Agent） | 内建 6 节点 DAG（planner → repo_agent → merger → synthesiser → reflect → refine） |
| 多仓支持 | 无（单仓库内查询） | Send 扇出，每仓一个 repo_agent 并行 |
| 意图分流 | 无 | 正则匹配关系词 → react 模式，否则 fast 模式 |
| ReAct 循环 | 无 | 单仓 Agent 支持 ReAct（LLM 自主选择工具，max_iter=6，签名去重防死循环） |
| 反思机制 | 无 | reflect 节点自评答案充分性，不充分则 refine 补检索（限 1 轮） |
| 持久化 | 无 | PostgresSaver 按 thread_id 崩溃续传 |
| 容错 | 无 | ReAct 失败回退确定性 fallback（search → dossier） |

**关键差异**：KM 项目本身不包含 Agent 逻辑，它是一个"知识供给系统"——通过 MCP 工具暴露图谱查询能力，由外部 Agent（"元析"等）来编排调用。codedoc 则是一个"全栈 Agent 系统"——自带 LangGraph 编排的多 Agent 架构，包含选仓、并行查询、合并、生成、反思的完整闭环。从面试角度看，codedoc 的 Agent 架构更适合讲故事（为什么拆、怎么拆、怎么防死循环），KM 项目的 MCP 工具设计更适合讲工程落地。

## 七、MCP 工具对比

| 维度 | KM 项目 | codedoc |
|---|---|---|
| 暴露方式 | MCP Server（接入 CatPaw/Cursor） | MCP Server（stdio 协议） |
| 工具数量 | 未明确（至少支持 Cypher 查询） | 7 个原子工具 + 4 个高阶技能 |
| 原子工具 | — | search / context / callers / callees / impact / explore / get_body |
| 高阶技能 | — | explain_symbol / trace_chain / impact_report / onboarding_brief |
| 查询模板 | Cypher 查询模板库 + LLM 生成 | 工具函数直接调用内存图遍历 |
| Agent 集成 | 集成到"元析"概设生成流程的"代码考古"环节 | ReAct Agent 自主选择工具 |
| PageRank | 无 | onboarding_brief 用纯 Python 幂迭代 PageRank 排序核心入口 |

**codedoc 的 11 个 MCP 工具详细说明**：

原子工具（7 个）：

- `search`：混合向量+全文搜索，输入查询文本和 top_k，返回匹配节点列表
- `context`：给定 node_id，返回节点详情、源码片段、直接调用者和被调者
- `callers`：向上追溯谁调用了该节点，支持指定深度
- `callees`：向下追溯该节点调用了谁，支持指定深度
- `impact`：反向传递闭包，分析修改某节点影响哪些上游
- `explore`：以某节点为锚点，返回邻域子图
- `get_body`：从磁盘读取完整函数体源码

高阶技能（4 个）：

- `explain_symbol`：一键获取符号完整解释包（源码+调用者+被调者+元数据）
- `trace_chain`：BFS 调用链追溯，支持向上/向下 N 层
- `impact_report`：变更影响报告，反向闭包后按文件归类输出
- `onboarding_brief`：新人上手简报，用 PageRank 排序找出核心入口符号

## 八、应用场景对比

| 场景 | KM 项目 | codedoc |
|---|---|---|
| 调用链追溯 | 核心能力，Cypher 一条语句穿透全链路 | 支持（callers/callees 工具），但基于内存遍历 |
| 变更影响分析 | 支持（Cypher 反向路径查询） | 支持（impact 工具，反向传递闭包） |
| 代码问答 | 非核心（图谱作为知识供给，回答由外部 Agent 生成） | 核心能力（LangGraph Agent 完成完整问答闭环） |
| 设计文档生成 | 支持（集成到"元析"概设→详设流程） | 支持（docgen 模块，模板化文档生成） |
| 全局架构理解 | 不支持（面向具体方法/链路的精确查询） | 支持（GraphRAG 社区摘要回答架构级问题） |
| 跨仓分析 | 不支持（单仓库内查询） | 支持（多仓 Send 扇出 + merger 跨仓关系推理） |
| SQL→表链路 | 核心能力（METHOD → SQL_STATEMENT → TABLE） | 不支持 |
| 新人入门 | 不支持 | 支持（onboarding_brief PageRank 排序核心入口） |

## 九、量化数据对比

| 指标 | KM 项目 | codedoc |
|---|---|---|
| 代码规模 | 429,726 行（3 个服务仓库） | 不详（Demo 级） |
| 节点数 | 12,114 | 不详 |
| 边数 | 24,213 | 不详 |
| 调用链准确率 | 传统 73% → 知识图谱 100% | 无评测数据 |
| 调用链召回率 | 传统 36% → 知识图谱 100% | 无评测数据 |
| 效率提升 | 链路梳理约 5x，代码考古耗时 -60% | 无评测数据 |
| 向量维度 | 未说明 | 1024（BGE-M3） |
| HNSW ef_search | — | 200（默认 40 提到 200，召回从 25%→96%） |

## 十、技术选型对比总表

| 技术点 | KM 项目 | codedoc |
|---|---|---|
| 图数据库 | Neo4j | PostgreSQL JSONB（全图一行） |
| 图查询语言 | Cypher | Python 内存遍历 |
| 向量数据库 | 建设中 | pgvector（HNSW） |
| 向量模型 | 未说明 | BGE-M3（1024 维） |
| Reranker | 无 | BGE-reranker-v2-m3 |
| LLM | 未说明 | 7 模型网关（DeepSeek-V3/Qwen2.5-72B/DeepSeek-R1 等） |
| Agent 框架 | 无（MCP 工具供外部 Agent 调用） | LangGraph StateGraph |
| AST 解析（Python） | — | 标准库 ast |
| AST 解析（Java） | 未说明 | javalang |
| AST 解析（JS/TS） | — | tree-sitter |
| Web 框架 | — | FastAPI |
| 认证 | — | JWT（HS256） |
| 任务队列 | — | PostgreSQL SKIP LOCKED |
| 前端 | — | React（独立前端） |

## 十一、核心结论

### 相同点（理念层面高度一致）

1. **同一个问题意识**：传统 RAG 向量检索对代码结构理解有限，尤其是多跳调用链场景下准确率和召回率不足
2. **同一个解题思路**：通过 AST 静态解析构建结构化代码知识图谱，用图查询替代/补充向量检索
3. **同一个交付形态**：以 MCP Server 形式暴露工具能力，集成到 AI 编码环境（CatPaw/Cursor）
4. **同样的图谱建模哲学**：节点=代码实体（类/方法/接口），边=代码关系（调用/继承/包含），核心都是 CALLS 边
5. **同样关注框架感知**：两个项目都识别 Spring 注解来区分 Controller/Service/Repository

### 不同点（工程实现差异显著）

1. **深度 vs 广度**：KM 项目深耕 Java 微服务全链路（代码→SQL→数据库表），codedoc 追求多语言覆盖但每种都做得浅
2. **精确 vs 模糊**：KM 项目的 Cypher 查询返回确定性结果（准确率/召回率 100%），codedoc 的 RAG 检索本质上是概率性的
3. **知识供给 vs 全栈 Agent**：KM 项目是"知识图谱即服务"，不做 Agent 编排；codedoc 是全栈系统，自带多 Agent 编排
4. **Neo4j vs PostgreSQL**：KM 用专业图数据库，codedoc 用 PostgreSQL 一把梭（图谱 JSONB + 向量 pgvector + 业务表 + 任务队列全在一个 PG 里）
5. **团队协作 vs AI 生成**：KM 项目是团队持续建设的生产系统，codedoc 是 Claude Code 一次性生成的 Demo

### 简历应用建议

写简历时应融合两者优势：用 KM 项目的**业务场景和量化数据**作为骨架（可信、可验证），用 codedoc 的 **Agent 架构和 GraphRAG 技术细节**填充技术深度（面试有话讲），用自身真实技术栈做适配（Neo4j 而非 PG、Python + tree-sitter、MCP 开发经验）。
