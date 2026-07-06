---
title: "AI Coding知识图谱建设分享-建设知识图谱支持复杂系统功能迭代"
date: 2025-07-05
source: 学城
tags:
  - AI
  - Coding
  - 知识图谱
  - RAG
  - GraphRAG
---

# 采购AI Coding私域范式建设分享-建设知识图谱支持复杂系统功能迭代

### 一、背景&目标

#### 背景

随着公司AI探索的深入，我们发现AI在实际应用中存在明显的效率提升瓶颈。从实际使用体验来看，AI目前仅能解决30%~40%的代码问题，加上人工交互修改和检查的成本，整体提效并未达到预期的30%增长。这主要源于AI Coding的贡献与提效呈现非线性增长特征，存在明显的阶段性规律：

![[attachments/img_0.png]]

> **AI Coding贡献率和提效比例的关系曲线（经验）**

- **初期阶段**：AI输出质量较差，代码采用率低，研发人员需要投入大量时间进行代码甄别和优化，效率反而出现下降。
- **发展阶段**：随着AI代码贡献度逐步提升，人工干预成本逐渐降低，效率开始显现。
- **成熟阶段**：当AI输出质量足够高、无需人工修正时，提效比率达到最大值。

目前我们已经跨越了效率提升的临界点，能够感受到的提效，但对团队整体工作的影响尚未达到预期强度。**关键在于，后续对AI Coding的每一次优化都将带来更显著的提效增长，这正是我们需要重点投入的原因。**

#### **第一阶段认知与调研**

**AI-Coding探索第一阶段的认知：**AI范式框架：主要包括 prompt、AI 工具、模型和知识库四大核心要素。其核心流程为：用户通过 prompt 与 AI 工具进行交互，AI 工具结合合适的大模型和知识库，生成符合实际生产项目要求的代码或设计文档。在存量系统和复杂场景下，领域知识库内容的完善程度对AI生成效果有较大影响。

![[attachments/img_1.png]]

**内部实践**：我们在AI Coding第一阶段的探索落地过程中，知识库的构建主要依赖人工+AI工具辅助整理，内容以 Markdown 格式记录领域知识和规范文档。并且给AI知识库的方式主要有两种方式，其存在以下问题，难以支撑复杂场景下AI的高质量输出：

**人工引用文件** ：研发人员在使用AI Coding工具（Cursor/CatPaw）时，通常需要手动研发手动引入代码/文档，这种模式精准但是有以下问题：

- 操作繁琐：每次都需要人工判断并手动指定，增加了研发负担，影响工作流的流畅性。

- 上下文受限：受限于AI模型的上下文窗口，能引入的知识量有限，面对复杂需求场景时容易遗漏关键信息。

- 知识碎片化：知识的引用是临时性的，难以形成系统化、结构化的知识支撑，AI对于项目全貌的理解始终不完整。

**传统RAG向量检索方式：**将知识库内容进行向量化，然后通过语义检索的搜索知识。这种方式自动化能力提升，这种模式的问题：

- 语义匹配有限：向量检索依赖于文本相似度，对于结构化、层次化的复杂关系表达能力有限，容易遗漏跨层级、跨模块的关键依赖。

- 结果不稳定：检索结果受限于向量模型及检索策略，面对复杂业务场景时，相关知识的召回率和准确率难以保障。

- 缺乏全局视角：向量检索通常是“点对点”的局部匹配，难以支持AI对系统整体结构、调用链路、业务流程等全局信息的理解和推理

**AI-Coding知识库范式的调研：**

我们在深入分析自身实践的同时，也对业界主流AI Coding和智能研发领域的技术路线进行了系统调研，越来越多研究表明，由于**知识图谱**其独特的特性，使其作为知识库的承载形式，对于提升AI代码理解、生成和推理能力的显著作用，是AI Coding发展的重要方向。前沿探索的：

- **Knowledge Graph Based Repository-Level Code Generation和CodeXGraph****：** 前沿论文，**问题背景**：现有大型语言模型（LLMs）在代码生成方面表现优异，但在理解项目特定架构、内部依赖和上下文方面存在局限，导致生成的代码难以无缝集成到现有代码库。**核心主张**：通过引入**知识图谱**表示代码库的结构和关系，可以显著提升代码检索和生成的质量，实现更准确、上下文感知的仓库级代码生成。

- **GraphRAG****（Graph-based Retrieval-Augmented Generation）：**是微软开源的基于**知识图谱**的检索增强生成框架，其核心思想是通过结构化知识图谱替代传统RAG的扁平化文本检索，能够提升知识问答的准确性、可解释性和推理能力，尤其适合复杂领域知识的应用。

> **📂 折叠块（默认折叠）：<span style="color:#000">**什么是知识图谱？**</span>**
>
> 知识图谱（Knowledge Graph）是一种以图结构来表示知识的技术，它将现实世界中的实体（如人物、地点、事物等）以及它们之间的关系通过节点和边的方式组织起来。知识图谱不仅包含数据，还体现了数据之间的语义关系，能够支持复杂的查询和推理，是人工智能、搜索引擎、推荐系统等领域的重要基础。
> 
> 特点
> 
> - 实体（节点）：表示现实世界中的对象，如“爱因斯坦”、“德国”、“物理学”。
> - 关系（边）：表示实体之间的联系，如“出生地”、“研究领域”。
> - 属性：实体的具体特征或描述，如“出生日期”、“国籍”。
> 
> 示例：电商平台商品推荐
> 
> 1. 知识图谱结构举例
> 
> 假设有如下实体和关系：
> 
> - 用户（User）
> - 商品（Product）
> - 品牌（Brand）
> - 类别（Category）
> - 购买行为（Buy）
> - 喜欢（Like）
> - 相似商品（Similar）
> 
> 部分知识图谱结构如下：
> 
> [用户A] --(购买)--> [商品1]
> 
> [用户A] --(喜欢)--> [商品2]
> 
> [商品1] --(属于)--> [品牌X]
> 
> [商品1] --(类别)--> [手机]
> 
> [商品2] --(属于)--> [品牌Y]
> 
> [商品2] --(类别)--> [耳机]
> 
> [商品3] --(属于)--> [品牌X]
> 
> [商品3] --(类别)--> [手机]
> 
> [商品1] --(相似)--> [商品3]
> 
> 2. 推荐逻辑举例
> 
> 利用知识图谱，可以做多维度的推荐：
> 
> （1）基于属性推荐
> 
> - 用户A购买了品牌X的手机，则可以推荐同品牌的其他手机（如商品3）。
> 
> （2）基于行为推荐
> 
> - 用户A喜欢耳机，则可以推荐同类别的热门耳机。
> 
> （3）基于关系推荐
> 
> - 商品1和商品3存在“相似”关系，用户A买了商品1，可以推荐商品3。
> 
> （4）组合推荐
> 
> - 用户A购买了手机，也喜欢耳机，可以推荐手机和耳机的套装或相关配件。

**知识图谱的特性优势：**

- 结构化：以节点（实体）和边（关系）方式组织信息，天然适合表达代码、服务、业务流程等结构化内容。

- 语义丰富：支持多类型实体、多种关系，能够表达丰富的语义和业务逻辑，便于AI做深层次理解和推理。
- 可扩展性：灵活添加新的实体、关系和属性，适配不断变化的业务和技术需求。
- 可视化与可解释性强：图结构便于可视化，支持交互式探索和溯源，提升AI推理过程的可解释性和信任度。
- 高效的关系型检索与推理：支持多跳路径检索、上下游依赖分析、模式匹配等复杂操作，极大增强AI的知识发现和推理能力

#### **目标**

基于上述认知和调研结论，我们明确了本阶段的核心目标：

**建设自动化、多维度、可持续演进的知识图谱，作为AI Coding的底座，全面提升AI对项目结构、业务流程、代码依赖等复杂知识的理解、推理和生成能力。**

### 二、建设策略

#### **核心建设策略**

- **自动化知识库工具**：开发自动化工具，解析代码、文档、数据库等多源信息，自动生成知识图谱节点与关系，降低人工整理成本。
- **MCP能力开放**：通过MCP等接口，将知识图谱能力开放给各类AI Agent，深度集成到设计、开发、测试等研发流程中。

![[attachments/img_2.png]]

### 三、建设进展

#### 知识库图谱的数据范围与内容

在李继刚分享[【全民AI】Top Talk微刊：李继刚的Prompt之道--从“清晰表达”到“人机共振”](https://wiki.example.com/collabpage/2710585384)中，有提到提到我们应该尽量给予AI第二象限的知识，即人知道而AI不知道的内容。对于AI知道的我们就尽量少的提供，减少token的使用。 

![[attachments/img_3.png]]

在日常开发工作中，我们通常使用Catpaw等工具在代码仓库中完成功能开发，那么代码的功能就是AI知道的，因此一些仅**通过代码解析生成的知识库无法在AI Coding中起到很好的作用**。 像[业界一些工具](https://wiki.example.com/collabpage/2717033586)，无论是收费的Swim、CodeRabbit，还是开源的DeepWiki，生成的内容更多的是给人阅读的。我们需要构建的知识内容，必须是人知道而AI无法获取的信息：

1. **内部编码习惯与规范**：沉淀团队内部的编码规范、命名约定、异常处理、日志规范等通用知识，为AI生成和优化代码提供风格和安全保障。
> 说明：此部分基研已有团队在建设并对外提供MCP能力，我们可直接复用其结果，不作为本次知识库建设的重点。
2. **代码结构**：梳理项目中各个模块、类、方法的结构、层级关系，以及它们在系统中的作用与职责分布。
3. **表结构**：沉淀数据库表结构、字段含义、表间关系等信息，帮助AI理解数据流和数据模型。（AI可以读取数据库的建表信息，但没有外键，表和表之间的关系必须有人工给出。）
4. **系统页面与功能映射**：明确每个前端页面或业务功能点对应的后端接口、服务、数据表等，实现页面-接口-服务的全链路映射。
5. **服务间职责与调用关系**：建立服务之间的职责划分、调用链路、依赖关系等知识，支持复杂业务场景下的上下游影响分析。
6. **领域专有知识**：补充行业术语、核心业务流程、规则约束等业务语义，弥补AI对领域知识的理解短板。

这些内容，是我们构建领域知识库最核心的部分。

#### 知识库图谱的**构建思路与架构**

**知识图谱系统架构**

![[attachments/img_4.png]]

知识图谱构建的系统架构，主要分为三个核心部分：

**1、多维知识图谱构建：**将各类知识库的信息，转换为我们设计的知识图谱的结构，存入图数据库中。包括：
- **代码仓库处理（已完成）：** **识别要解析的文件 **- 确定需要分析的代码文件范围[^代码文件范围：需要分析核心的Service、Controller、Mapper代码，DTO传输对象不用分析]，**AST****解析识别代码组件 **- 使用抽象语法树分析静态，解析出代码结构，识别类、方法、变量等组件，**代码组件与图谱结构对齐 **- 将解析出的代码组件映射到知识图谱的节点和关系结构，**构建知识图谱** - 将对齐后的代码信息存储到图数据库中。
- **技术文档处理（建设中）：** **E-R关系解析** - 使用大模型解析文档中的实体关系模型，**核心流程解析** - 提取文档中描述的业务流程和操作步骤，**接口文档解析** - 解析API接口文档，识别接口参数、返回值等信息，**构建知识图谱 **- 将解析出的文档信息存储到图数据库中
- **其他维度（设计中）：**预留了其他维度知识图谱构建的设计空间，为未来扩展做准备。

**2、知识图谱索构建：**对构建好的知识图谱进行索引构建和向量化处理，为后续查询应用做准备。包括：
- **构建标量索引（已完成）** ： 基于全量节点构建结构化索引。
- **创建向量索引（建设中）** ：**文档路径 -** 获取需求文档和设计文档，进行向量化处理 **代码路径 - **获取代码块，通过大模型生成代码描述，然后进行向量化基于向量化结果创建语义索引。

**3、知识图谱应用：**基于构建好的索引，为用户提供智能化的信息检索和查询服务。主要包含2种搜索方法：
- **图搜索路径（已完成）：****生成图数据库查询语句** - 通过大模型将查询转换为图数据库查询语言，**图搜索** - 在图数据库中执行结构化查询，**返回节点及关系信息** - 返回匹配的节点和它们之间的关系
- **向量搜索路径（建设中）：****大模型处理** - 使用大模型理解和优化查询，**向量化** - 将查询转换为向量表示，**向量检索** - 在向量索引中搜索相似内容，**返回相似节点** - 返回语义相似的节点信息。

**知识图谱建模：融合多源异构知识**

![[attachments/img_5.png]]

**融合多源异构知识：**知识图谱设计上融合了代码仓库知识、技术知识、业务流程、领域模型、页面映射等多源异构知识，实现全景式的知识覆盖，帮助AI理解业务全貌。知识图谱通过节点和边描述整个关系。

**节点**：节点代表知识图谱中的实体，主要包括：** **服务**：代表一个微服务实例，包含服务名、描述等信息。
- **服务接口**：表示服务对外暴露的接口，包括接口名、协议、请求方法、路径等。
- **Java接口类**：描述Java接口类的相关信息，如名称、包名、文件路径等。
- **Java实现类**：描述Java接口的实现类，包括类名、包名、文件路径等。
- **Java方法**：代表类或接口中的具体方法，包含方法名、所属类、签名、层次等信息。
- **SQL语句**：表示与数据库交互的SQL语句，记录SQL内容、类型、文件路径等。
- **数据库表**：描述数据库中的表，包括表名、所属数据库、描述等。

**边**：边用于表达不同实体之间的各种关系，主要包括：** **暴露**：服务 → 服务接口，表示服务暴露了某个接口。
- **服务接口实现**：服务接口 → Java方法，表示接口由某个方法实现。
- **接口定义**：Java实现类/Java接口类 → Java方法，表示类或接口声明了某个方法。
- **Java接口实现**：Java实现类 → Java接口类，表示实现类实现了某个接口。
- **调用**：Java方法 → Java方法，表示方法之间的调用关系。
- **执行**：Java方法 → SQL语句，表示方法执行了某条SQL语句。
- **操作**：SQL语句 → 数据库表，表示SQL语句操作了某个数据库表。

<details>
<summary>知识图谱 Schema 定义（点击展开）</summary>

```
// schema

## 知识图谱结构说明

### Nodes（节点）

1. **SERVICE（服务）**: 
   - **属性**:
      - `appKey` (String): 微服务名称，代表服务的唯一标识（如com.myco.purchasemall.po）
      - `description` (String): 服务描述

2. **SERVICE_ENDPOINT（服务接口）**: 
   - **属性**:
      - `name` (String): 接口标识，一般为：类名.方法名
      - `protocol` (String): 协议类型（HTTP, Thrift）
      - `http_method` (String): HTTP 方法请求类型（GET, POST，若适用）
      - `path` (String): HTTP 接口URL 路径（若适用）
      - `description` (String): 接口描述（可选）

3. **JAVA_INTERFACE（Java接口类）**: 
   - **属性**:
      - `name` (String): Java 接口类名称（如 UserService）
      - `full_name` (String): Java 接口类全限定名称，包名.类名（如 com.myco.myco.UserService）
      - `package` (String): 包名
      - `file_path` (String): 文件路径

4. **JAVA_IMPLEMENTATION（Java实现类）**: 
   - **属性**:
      - `name` (String): 实现类名称（如 UserServiceImpl）
      - `full_name` (String): Java 接口类全限定名称，包名.类名（如 com.myco.myco.impl.UserServiceImpl）
      - `package` (String): 包名
      - `file_path` (String): 文件路径

5. **METHOD（方法）**: 
   - **属性**:
      - `name` (String): 方法名（如 login）
      - `class` (String): 方法所属类/接口全限定名（如 com.myco.myco.impl.UserServiceImpl）
      - `full_name` (String): 方法全限定名，类名.方法名（如 com.myco.myco.impl.UserServiceImpl.login）
      - `signature` (String): 方法签名
      - `file_path` (String): 方法所在文件路径 
      - `layer` (String): 所属层（Controller, Service, Mapper）

6. **SQL_STATEMENT（SQL语句）**: 
   - **属性**:
      - `id` (String): SQL 标识（如 SQL#UserMapper.selectById）
      - `sql` (String): SQL 语句内容
      - `operation` (String): 操作类型（select, insert, update, delete）
      - `file_path` (String): SQL 所在文件路径（如 /resources/base/mapper/PoAdjustRecordMapper.xml）

7. **TABLE（数据库表）**: 
   - **属性**:
      - `name` (String): 表名
      - `database` (String): 数据库名（可选）
      - `description` (String): 表描述（可选）

### Edges（边）

1. **EXPOSES（暴露）**: 
   - **Source**: SERVICE 
   - **Target**: SERVICE_ENDPOINT

2. **ENDPOINT_IMPLEMENTED_BY（服务接口实现）**: 
   - **Source**: SERVICE_ENDPOINT 
   - **Target**: METHOD

3. **DECLARES（接口定义）**: 
   - **Source**: JAVA_INTERFACE 或 JAVA_IMPLEMENTATION 
   - **Target**: METHOD

4. **IMPLEMENTS（java接口实现）**: 
   - **Source**: JAVA_IMPLEMENTATION 
   - **Target**: JAVA_INTERFACE

5. **METHOD_IMPLEMENTS（java方法实现）**: 
   - **Source**: METHOD（实现类中的方法） 
   - **Target**: METHOD（接口中的方法）

6. **CALLS（调用）**: 
   - **Source**: METHOD 
   - **Target**: METHOD

7. **EXECUTES（执行）**: 
   - **Source**: METHOD 
   - **Target**: SQL_STATEMENT

8. **OPERATES_ON（操作）**: ---

## 示例

### 节点 
- **SERVICE**: UserService 
- **SERVICE_ENDPOINT**: /api/user/login（protocol: HTTP, http_method: POST） 
- **JAVA_INTERFACE**: UserService（package: com.example.service） 
- **JAVA_IMPLEMENTATION**: UserServiceImpl（package: com.example.service.impl） 
- **METHOD**: UserController.login()、UserService.login()、UserServiceImpl.login()、UserMapper.selectById() 
- **SQL_STATEMENT**: SQL#UserMapper.selectById（sql: SELECT * FROM user WHERE id = ?, operation: select） 
- **TABLE**: user

### 边 
- UserService **EXPOSES** /api/user/login 
- /api/user/login **ENDPOINT_IMPLEMENTED_BY** UserController.login() - UserService **DECLARES** UserService.login() 
- UserServiceImpl **DECLARES** UserServiceImpl.login() 
- UserServiceImpl **IMPLEMENTS** UserService 
- UserServiceImpl.login() **METHOD_IMPLEMENTS** UserService.login() 
- UserController.login() **CALLS** UserService.login() 
- UserService.login() **CALLS** UserMapper.selectById() 
- UserMapper.selectById() **EXECUTES** SQL#UserMapper.selectById 
- SQL#UserMapper.selectById **OPERATES_ON** user（operation: select）
```

</details>

**采购项目知识图谱示例**

> 🎬**视频附件**：录屏2025-08-07 19.21.43.mov *(见原文)*

采购PO、商品、基础能力3个服务代码仓库构建的知识库信息，代码总行数为：429726行，构建的知识图谱包含了**12114**个节点，**24213**个边

> 🎬**视频附件**：录屏2025-08-12 14.10.07.mov *(见原文)*

采购PO项目中，查询框架订单详情接口，查询PO头、行、历史表来组装BPO页面展示信息。这个案例使用Cypher查询，一次性获取queryBlanketPoDetailPage方法的完整调用链路，包含了该方法对应的http接口，方法调用的方法及数据库表。

```cypher
// cypher语句 // 从图数据库中查找一个名为 'queryBlanketPoDetailPage' 的方法节点，并将其标记为 target MATCH (target:METHOD {name: 'queryBlanketPoDetailPage'})

/* 向前进行查询：从服务节点到达目标方法节点的所有可能路径    这部分用来识别哪个服务通过哪个端点最终实现了或调用了目标方法。    - s:SERVICE 表示服务节点    - :EXPOSES 关系表示服务对外暴露的接口    - SERVICE_ENDPOINT 表示服务的具体接口点    - :ENDPOINT_IMPLEMENTED_BY 表示这个接口点由某个方法实现    - m0:METHOD - 初始的接口实现方法    - METHOD_IMPLEMENTS*0.. 表示方法的实现关系，可以追溯实现链至多个方法    - CALLS*0.. 表示方法之间调用关系，可以是多个连续调用    - m2:METHOD 表示在路径中找到的方法节点    - 仅当 m2 是目标方法或与目标方法有实现关系时，路径才有效 */
OPTIONAL MATCH p_up = 
  (s:SERVICE)-[:EXPOSES]->(:SERVICE_ENDPOINT)-[:ENDPOINT_IMPLEMENTED_BY]->(m0:METHOD) 
  -[:METHOD_IMPLEMENTS*0..]-(m1:METHOD) 
  -[:CALLS*0..]->(m2:METHOD)

WHERE m2 = target OR (m2)-[:METHOD_IMPLEMENTS*0..]-(target)

/* 向后进行查询：从目标方法向下追踪其执行到表的所有路径    此部分识别该方法执行了哪条 SQL 语句并操作了哪些数据库表。    - target 方法的实现链和所调用的方法链被追踪，直到执行 SQL 语句    - EXECUTES 关系表示方法执行的 SQL 语句    - OPERATES_ON：SQL 语句操作的数据库表    - m3:METHOD - 中途可能调用的方法    - sql:SQL_STATEMENT - 由某个方法执行的 SQL 语句    - t:TABLE - SQL 语句最终操作的数据库表 */
OPTIONAL MATCH p_down = 
  (target)-[:METHOD_IMPLEMENTS*0..]-(m3:METHOD) 
  -[:CALLS*0..]->(m4:METHOD) 
  -[:EXECUTES]->(sql:SQL_STATEMENT) 
  -[:OPERATES_ON]->(t:TABLE)
// 收集符合条件的向上路径和向下路径，过滤掉空路径

WITH [p IN collect(p_up)

WHERE p IS NOT NULL] AS upPaths,      [p IN collect(p_down)

WHERE p IS NOT NULL] AS downPaths
// 合并向上和向下的路径集成为一个总路径集

WITH upPaths + downPaths AS paths
// 展开路径集以便返回，并确保返回的路径是唯一的（无重复路径）

UNWIND paths AS p

RETURN DISTINCT p
```

> 🎬**视频附件**：234视频呢.mov *(见原文)*

采购规则配置化模块中，保存规则时，会更新或插入规则基础信息、规则信息、规则执行信息等。这个案例展示了通过一条Cypher语句，查询到保存规则接口（saveDetail）的上下游所有调用链路。

```cypher
// cypher语句 // 从图数据库中查找一个名为 'saveDetail' 的方法节点，并将其标记为 target MATCH (target:METHOD {name: 'saveDetail'})

/* 向前进行查询：从服务节点到达目标方法节点的所有可能路径    这部分用来识别哪个服务通过哪个端点最终实现了或调用了目标方法。    - s:SERVICE 表示服务节点，这里定义代表各个服务的实体    - :EXPOSES 表示服务如何对外暴露接口，指向 SERVICE_ENDPOINT 节点    - SERVICE_ENDPOINT 表示服务的具体接口点，即服务暴露的具体终端    - :ENDPOINT_IMPLEMENTED_BY 表示这个接口点由某个方法实现    - m0:METHOD - 表示初始实现接口的第一层方法    - METHOD_IMPLEMENTS*0.. 表示方法的实现关系，可以追溯实现链至多个方法，这里表示可能有多个实现层级    - CALLS*0.. 表示方法之间调用关系，可以是多个连续调用，表示从一个方法到另一个方法的调用链    - m2:METHOD 表示在路径中找到的方法节点    -

WHERE 子句确保仅当 m2 是目标方法或通过实现链连接到目标方法时，路径才有效 */
OPTIONAL MATCH p_up = 
  (s:SERVICE)-[:EXPOSES]->(:SERVICE_ENDPOINT)-[:ENDPOINT_IMPLEMENTED_BY]->(m0:METHOD) 
  -[:METHOD_IMPLEMENTS*0..]-(m1:METHOD) 
  -[:CALLS*0..]->(m2:METHOD)

WHERE m2 = target OR (m2)-[:METHOD_IMPLEMENTS*0..]-(target)

/* 向后进行查询：从目标方法向下追踪其执行到表的所有路径    此部分识别该方法执行了哪条 SQL 语句并操作了哪些数据库表。    - 从 target 方法的实现链和所调用的方法链被追踪，直到执行 SQL 语句    - EXECUTES 表示方法执行的 SQL 语句，表示某个方法会执行某些 SQL 操作    - OPERATES_ON 表示 SQL 语句对数据库表进行的操作，连接到具体的数据库表节点    - m3:METHOD 和 m4:METHOD - 路径中间可能调用的其他方法    - sql:SQL_STATEMENT - 由某个方法执行的 SQL 语句    - t:TABLE - 表示 SQL 语句最终操作的数据库表 */
OPTIONAL MATCH p_down = 
  (target)-[:METHOD_IMPLEMENTS*0..]-(m3:METHOD) 
  -[:CALLS*0..]->(m4:METHOD) 
  -[:EXECUTES]->(sql:SQL_STATEMENT) 
  -[:OPERATES_ON]->(t:TABLE)
// 收集符合条件的向上路径和向下路径，并过滤掉空路径以保留有效路径

WITH [p IN collect(p_up)

WHERE p IS NOT NULL] AS upPaths,      [p IN collect(p_down)

WHERE p IS NOT NULL] AS downPaths
// 合并向上路径和向下路径，形成一个完整的传输路径集

WITH upPaths + downPaths AS paths
// 展开路径集以便返回，并确保返回的路径是唯一的（即去除重复路径）

UNWIND paths AS p

RETURN DISTINCT p
```

#### 知识库图谱设计应用

![[attachments/img_9.png]]

**MCP工具接入：**通过开放MCP工具和引入自定义rule，可以快速接入目前各类编码或设计的Agent中。 案例： 我们在“元析”的基础上，尝试了接入知识图谱的MCP，其生成的设计文档可用率都有较大的提升。 基于目前知识库的使用场景以及对“元析”Agent的分析，在【概设生成详设】模板中【代码考古】模块，增加知识库使用场景以及说明。让AI在代码考古阶段通过知识库完成代码读取以及上下游链路梳理工作。

![[attachments/img_10.png]]
 随着知识库的增加，后续规划在“元析”最外层Agent中增加【知识库】模块，让AI根据场景自行/指定调用知识库，提升准确率。

```
// 知识库使用rules
> #### 任务指令:
> 按照以下步骤使用灵活路径查询创建最优的Cypher查询:
> > **步骤1: 层级识别**
> - 从查询中识别**起始层级**(API, Controller, Service, Mapper, SQL, Database)
> - 从查询中识别**目标层级**(API, Controller, Service, Mapper, SQL, Database)
> > **步骤2: 灵活路径构建**
> - 使用灵活的路径模式构建查询，关注起点和终点
> - **正向查询**: 使用可变长度路径模式如`-[:CALLS*]->`, `-[:CALLS*1..3]->`, `-[:CALLS*0..]->` 等
> - **反向查询**: 使用可变长度反向路径模式如`<-[:CALLS*]-`, `<-[:CALLS*1..3]-`, `<-[:CALLS*0..]-` 等
> - 根据查询需求选择正向或反向路径，或者组合使用
> > **步骤3: 查询生成**
> 你的回答应遵循以下格式:
> > [start_of_layer_analysis]
> **起始层级**: <识别的起始层级>
> **目标层级**: <识别的目标层级>
> [end_of_layer_analysis]
> > [start_of_cypher_queries]
> ### 查询1
> **分解的文本查询**: <这个查询做什么的简短摘要>
> **层级路径**: <起始层级> → <目标层级>
>
```cypher
> <cypher查询>
>
```
> > ### 查询2
> **分解的文本查询**: <这个查询做什么的简短摘要>
> **层级路径**: <起始层级> → <目标层级>
>
```cypher
> <cypher查询>
>
```
> ...
> [end_of_cypher_queries]
> > #### 层级映射指南:
> - **API查询** → 使用SERVICE_ENDPOINT节点
> - **Controller查询** → 使用layer='Controller'的METHOD节点
> - **Service查询** → 使用layer='Service'的METHOD节点
> - **Mapper查询** → 使用layer='Mapper'的METHOD节点
> - **SQL查询** → 使用SQL_STATEMENT节点
> - **数据库/表查询** → 使用TABLE节点
> > #### 灵活路径查询示例:
> > **正向查询示例:**
> - 查找Controller到叶子节点的所有路径:
>  
```cypher
>   MATCH p = (n:METHOD {layer: 'Controller'})-[:CALLS*0..]->(m)
>   WHERE NOT (m)-[:CALLS]->()
>   RETURN p
>  
```
> > - 查找特定方法的所有调用链:
>  
```cypher
>   MATCH p = (n:METHOD {full_name: 'com.example.Controller.method'})-[:CALLS*]->(m)
>   RETURN p
>  
```
> > - 查找从API到SQL的路径:
>  
```cypher
>   MATCH p = (api:SERVICE_ENDPOINT)-[:ENDPOINT_IMPLEMENTED_BY]->(start:METHOD)
>   -[:CALLS*]->(mapper:METHOD {layer: 'Mapper'})
>   -[:EXECUTES]->(sql:SQL_STATEMENT)
>   RETURN p
>  
```
> > **反向查询示例:**
> - 查找调用特定方法的所有上层调用者:
>  
```cypher
>   MATCH path = (rootCaller:METHOD)-[:CALLS*1..10]->(target:METHOD)
>   WHERE target.name = $methodName 
>   AND target.class = $className
>   WITH path, rootCaller, 
>     [node IN nodes(path) \| node.class + "." + node.name] AS callChain
>   RETURN DISTINCT rootCaller.name AS rootCallerMethod,
>       rootCaller.class AS rootCallerClass,
>       rootCaller.file_path AS rootCallerFile,
>       length(path) AS callDepth,
>       callChain
> ORDER BY callDepth, rootCaller.class, rootCaller.name
>  
```
> > - 查找操作特定表的所有API入口:
>  
```cypher
> MATCH p = (api:SERVICE_ENDPOINT)-[:ENDPOINT_IMPLEMENTED_BY]->(start:METHOD)
> -[:CALLS*]->(mapper:METHOD)-[:EXECUTES]->(sql:SQL_STATEMENT)
> -[:OPERATES_ON]->(table:TABLE {name: 'table_name'})
> RETURN p
>  
```
> > #### 重要注意事项:
> - 使用模糊匹配: `WHERE n.name =~ '.*<关键词>.*'` 或 `WHERE n.name CONTAINS '<关键词>'`
> - 过滤METHOD节点时始终包含`layer`属性
> - 优先使用灵活的路径模式，不必显式指定每一层的调用关系
> > - **正向查询**: 使用条件过滤终点节点，如`WHERE NOT (m)-[:CALLS]->()`表示叶子节点
> - **反向查询**: 使用条件过滤入口节点，如`WHERE NOT ()-[:CALLS]->(m)`表示顶层调用者
> - 根据分析目的选择正向（影响分析）或反向（依赖分析）查询
> - 如果没有请求特定属性，则返回完整节点
```

### 四、案例效果

**背景目标：**境外项目中，境外单据和境内单据底层会复用同一个存储介质，在存储上不会隔离，而境内境外目前是两套系统，需要避免境内系统查询单据时，查出境外单据。目前境内商城基于该存储介质查询订单的场景非常多，链路复杂。相关的链路超过20条，且调用普遍层级比较深，人工梳理并修改会有很大的工作量。因此我们尝试通过AI Coding从底层方法出发，梳理对应的调用链路并对相关的链路进行改造。

```Java
// 概要设计
背景：境外项目中，境外单据和境内单据底层会复用同一个ES索引，而境内境外目前是两套系统，需要避免境内系统调用ES查询单据时，查出境外单据。

需求内容：PO头的ES查询时，需要区分境内境外条件。

改动逻辑：

1.通过dataBoundary字段不为JUPITER判断是否是境外数据。dataBoundary=JUPITER，境外。反之不是境外。

2.通过queryPoEs方法，梳理上游链路调用关系。

3.通过对queryPoEs方法的全链路梳理，在Controller、Thrift、Crane的入口参数中增加字段，作为数据隔离的条件。

目标方法: com.myco.myco.po.service.elastic.OperationEs7Service.queryPoEs
```

**生成效果：**传统方式下梳理的准确率[^准确率：输出的链路中真实调用目标方法的链路占比]为**73%**，召回率[^召回率：实际的调用链路中被检索出的链路占比]为**36%**。知识图谱下梳理的准确率为**100%**，召回率为**100%**。

> 📎 **附件**：知识图谱分享 1.mp4 *(见原文)*

**对比分析：传统方式 vs 知识图谱**

**业务上下文学习**

传统分析方式：
![[attachments/img_12.png]]

知识图谱分析：
![[attachments/img_13.png]] ![[attachments/img_14.png]]

传统模式下，实际上是先去查询直接调用目标方法的方法。再去Web层、Service层和定时任务中，看是否存在直接或间接调用目标方法以及相关查询服务的方法。这里存在2个明显的问题，第一只能检索到比较短的链路，一般只能找到2次调用的链路，第二可能找到的方法并没有真正调用目标方法(幻觉问题)。因此会出现调用链路的遗漏，并把一些未调用目标放啊的链路梳理进来，这2个问题会随着链路复杂度的提高愈发明显。 知识图谱下，代码实际上是基于Cypher语句到图数据库中去获取对应的代码调用链路。检索的结果依赖于知识图谱，针对链路长度大于2的场景，也可以通过Cypher语句准确获取，且不会检索出错误的代码链路，结果更加准确可控。

---

**输出结果：Controller层**

传统分析方式：
![[attachments/img_15.png]]

知识图谱分析：
![[attachments/img_16.png]]

针对Controller接口的改造。传统方法实际梳理出5条链路，其中2条链路并未真实调用目标方法，遗漏的链路均为调用层级大于2的链路。知识图谱下梳理出11条链路，无链路遗漏，且均调用了目标方法。

---

**输出结果： Thrift层**

传统分析方式：
![[attachments/img_17.png]]

知识图谱分析：
![[attachments/img_18.png]] ![[attachments/img_19.png]]

针对Thrift的接口改造。传统方法实际梳理出4条链路，均调用了目标方法。知识图谱下输出了8个方法，均调用了目标方法。且涵盖了7类DTO的改造。

---

**输出结果： Crane任务**

传统分析方式：
![[attachments/img_20.png]]

知识图谱分析：
![[attachments/img_21.png]]

针对Crane层的改造。传统方法实际梳理出2条链路，其中一条链路未调用目标方法。知识图谱下输出了2条链路，均调用了目标方法。

---

> **📂 折叠块（默认折叠）：传统方式分析全流程**
>
> ![[attachments/img_22.png]]

> **📂 折叠块（默认折叠）：知识图谱分析全流程**
>
> ![[attachments/img_23.png]]

---

**脚注：**

- Knowledge Graph Based Repository-Level Code Generation和CodeXGraph：[https://arxiv.org/abs/2505.14394](https://arxiv.org/abs/2505.14394) [https://arxiv.org/abs/2408.03910](https://arxiv.org/abs/2408.03910)
- GraphRAG：[https://blog.csdn.net/AIBigModel/article/details/141504686](https://blog.csdn.net/AIBigModel/article/details/141504686)
- 代码文件范围：需要分析核心的Service、Controller、Mapper代码，DTO传输对象不用分析
- AST：AST 是 Abstract Syntax Tree（抽象语法树）， 是源代码语法结构的一种树状表现形式。树的每个节点都表示源代码中的一种结构，比如变量、运算符、语句块等。
- 准确率：输出的链路中真实调用目标方法的链路占比
- 召回率：实际的调用链路中被检索出的链路占比
