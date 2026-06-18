---
url: https://articles.zsxq.com/id_ztk1qrpw0er1.html
title: AI 代码如何不失控？
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-13 16:49:51
tags:

banner: "https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8="
banner_icon: 🔖
---
# AI 代码如何不失控？

[来自： 雷哥 AI 解决方案](https://wx.zsxq.com/group/28882285418421)

![](https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8=)

雷哥

2026 年 05 月 11 日 15:02

核心： 先设计前架构，规范，再放大 AI 产能

![](https://article-images.zsxq.com/FssXfk9dWONSo_nUZX2JjSKz7Man)

  

昨天看到 x 上说的一句话，我觉得非常值得所有正在用 AI 写代码的人停下来想一想：

如果一个代码库一开始就是由 agent 写出来的，那你不应该把主要精力放在 “逐行读懂它” 上。

这句话听起来有点反直觉，但它点中了一个非常现实的问题。

很多团队在用了 AI 之后，代码产出速度会突然暴涨。页面能很快出来，接口能很快补齐，脚本能很快跑通，Bug 也能被快速修掉。表面上看，一切都在提速；但过一段时间你再回头，会发现另外一件事也在同时发生：

`系统正在失去可理解性。`

不是代码不能跑了，而是没人说得清：

*   这个系统到底是怎么分层的
    

*   模块之间边界在哪里
    

*   为什么这里要这么设计
    

*   哪些接口是稳定契约
    

*   哪些地方可以改，哪些地方一改就会牵一发动全身
    

这就是 AI coding 时代最容易出现的失控点。

问题从来不只是 “代码质量差”，而是 `代码产能被放大了，但系统治理没有同步升级。`

## 一、AI 为什么会让代码更容易失控

很多人会以为，AI 写代码快，所以问题只是 “写得不够严谨”。其实不是。更深层的原因是：

`AI 把第三层产出放大了，但没有自动把第一层和第二层治理能力一起补上。`

为什么会这样？

*   AI 给出的反馈太快了。你描述一个需求，它立刻就能给出页面、函数、接口、配置。人会自然地进入 “先做出来再说” 的节奏。
    

*   局部修补成本太低了。以前多写一层逻辑要思考半天，现在哪里不对就让 AI 补一块，局部最优越来越便宜。
    

*   “能运行” 很容易制造理解错觉。页面打开了，接口通了，测试也能过，于是团队误以为系统已经清晰了。
    

*   大多数 AI coding 都围绕当前文件、当前任务、当前报错展开，它天然强化的是局部实现，而不是系统层思考。
    

*   团队的激励机制也在推着大家追求 “可见产出”，而不是优先建设 “可长期演化的结构”。
    

所以一句话总结就是：

`AI 让编码变快了，也让人更容易绕过思考。`

## 二、真正该盯住的，不是每一行代码，而是三层高度

如果我们把一个代码库拆成三个高度来看，就会更清楚：

### 第一层：Architecture

这一层关心的是系统级问题：

*   系统边界
    

*   核心模块
    

*   数据流向
    

*   服务职责
    

*   外部依赖
    

*   安全、性能、幂等、可观测性等关键约束
    

这一层决定的是：`系统到底是什么。`

### 第二层：Patterns & Abstractions

这一层关心的是项目内部怎么组织：

*   模块如何拆分
    

*   接口如何定义
    

*   前后端如何对齐契约
    

*   组件、服务、仓储、Schema、状态管理如何分层
    

*   哪些抽象是稳定的，哪些只是局部实现
    

这一层决定的是：`系统应该按什么方式生长。`

### 第三层：File-level Code

这一层才是我们平时最容易看到的内容：

*   函数
    

*   类
    

*   页面
    

*   组件
    

*   配置
    

*   测试
    

*   各种具体实现细节
    

这一层决定的是：`某个功能是怎么被写出来的。`

## 三、为什么前两层比第三层更重要

这不是说第三层不重要，而是说：

`如果前两层没定住，第三层写得越快，系统越容易失控。`

因为第三层的代码，本质上是在执行前两层的设计意图。

如果架构边界不清晰：

*   前端会混入业务规则
    

*   后端会承担展示逻辑
    

*   同一个能力会在不同模块重复实现
    

*   接口格式会越长越随意
    

*   新功能每次都像临时拼接
    

如果抽象层没定住：

*   今天写一个 `service`
    

*   明天加一个 `utils`
    

*   后天再来一个 `manager`
    

*   每个文件都 “看起来合理”，但整体没有统一结构
    

这就是典型的 AI 时代 “局部都对，整体失控”。

所以真正高杠杆的做法不是盯着 AI 写的每一行，而是先把前两层设计清楚，再让 AI 在约束内高速生产。

一句话总结：

`人的职责，不再是阅读全部实现，而是定义系统边界、抽象层级和验收机制。`

## 四、前两层到底应该写什么

很多人听到这里会点头，但一落地又会卡住：

`那前两层到底要写成什么？`

最简单的理解方式是：

*   第一层文档回答：`系统怎么组成`
    

*   第二层文档回答：`团队应该怎么写`
    

下面我们直接用一个具体案例说明。

## 五、案例：React 前端 + Python 后端，如何把前两层写出来

假设你现在有两个项目：

*   `Front`：React 前端
    

*   `Back`：Python 后端
    

很多团队在这个阶段最容易犯的错误是，直接给 AI 下需求：

*   帮我把登录页做出来
    

*   帮我写一个用户列表接口
    

*   帮我接一下分页
    

*   帮我补一个导出功能
    

这样做短期非常爽，但中期一定会出现结构漂移。

正确做法是，先把前两层落成文档，再让 AI 按文档干活。

## 六、第一层：Architecture 文档应该写什么

这一层你至少要写清楚下面这些内容。

### 1. 系统边界

*   `Front` 负责什么
    

*   `Back` 负责什么
    

*   哪些规则在前端做
    

*   哪些规则必须在后端做
    

例如：

*   `Front` 负责展示、交互、路由、表单体验、用户态呈现
    

*   `Back` 负责业务规则、权限校验、数据一致性、持久化、审计
    

### 2. 前后端通信方式

*   REST 还是 GraphQL
    

*   是否有 SSE / WebSocket
    

*   文件上传怎么走
    

*   鉴权 Token 怎么传
    

### 3. 核心业务流

至少写出 3 到 5 个关键流程，比如：

*   用户登录
    

*   列表查询
    

*   表单提交
    

*   文件上传
    

*   管理员审批
    

每个流程都应该明确：

*   谁发起
    

*   请求如何流转
    

*   后端经过哪些层
    

*   最终返回什么结果
    

### 4. 核心模块图

前端有哪些大模块：

*   `auth`
    

*   `dashboard`
    

*   `users`
    

*   `settings`
    

后端有哪些大模块：

*   `auth`
    

*   `user`
    

*   `order`
    

*   `notification`
    

### 5. 外部依赖

*   数据库
    

*   Redis
    

*   对象存储
    

*   消息队列
    

*   第三方 API
    

### 6. 关键约束

这一块最容易被忽略，但恰恰最重要：

*   权限模型
    

*   审计要求
    

*   接口幂等性
    

*   分页规范
    

*   错误码规范
    

*   性能预算
    

*   可观测性要求
    

第一层的核心不是 “写一堆描述”，而是把系统的边界和硬规则钉住。

## 七、第二层：Patterns & Abstractions 文档应该写什么

这一层说的是：

`项目内部到底按什么方式生长。`

### 前端要定什么

以 React 项目为例，至少应该定这些：

*   页面层、组件层、hooks 层、services 层如何分工
    

*   数据请求统一放哪里
    

*   是否允许组件直接请求接口
    

*   状态管理怎么做
    

*   表单状态怎么管理
    

*   错误提示和 loading 怎么统一
    

*   权限控制放在哪一层
    

*   通用组件与业务组件如何区分
    

*   目录结构怎么组织
    

### 后端要定什么

以 Python 项目为例，至少应该定这些：

*   router / service / repository 如何分层
    

*   schema / dto / model 如何区分
    

*   参数校验在哪一层做
    

*   事务在哪一层控制
    

*   异常如何统一抛出
    

*   错误码怎么定义
    

*   日志和 tracing 怎么埋
    

*   配置管理怎么做
    

*   单元测试和集成测试怎么分
    

### 前后端共同要定什么

这是最容易被低估的一层，也是最容易导致合作失控的地方：

*   API 响应格式
    

*   分页结构
    

*   时间格式
    

*   字段命名规范
    

*   空值语义
    

*   错误响应格式
    

*   版本兼容策略
    

很多项目不是代码写坏了，而是 `前后端抽象没有稳定契约`。

## 八、是不是写到 AGENTS.md 里

要写，但不能只写在 `AGENTS.md` 里。

这是一个非常关键的区分：

*   `设计文档` 负责定义世界
    

*   `AGENTS.md` 负责约束 AI 怎么在这个世界里干活
    

换句话说：

*   前两层文档是系统真相
    

*   `AGENTS.md` 是 AI 的执行手册
    

如果你把所有内容都堆进 `AGENTS.md`，通常会出现两个问题：

*   文档越来越长，但结构越来越散
    

*   AI 看起来拿到了规则，实际上没有拿到清晰的设计对象
    

更合理的做法是：

*   详细设计独立成文档
    

*   `AGENTS.md` 只写入口、硬约束、执行规则
    

## 九、推荐目录结构

如果是 `Front` 和 `Back` 两个项目，并且整个仓库只维护一个根目录 `AGENTS.md`，我建议目录至少这样组织：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
project-root/
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── frontend-patterns.md
│   ├── backend-patterns.md
│   └── core-flows.md
├── Front/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   └── tests/
└── Back/
    ├── app/
    │   ├── api/
    │   ├── services/
    │   ├── repositories/
    │   ├── schemas/
    │   ├── models/
    │   ├── core/
    │   └── utils/
    └── tests/


```

这个结构的关键不是 “长得标准”，而是它把三件事拆清楚了：

*   `docs/` 放前两层真相
    

*   根目录 `AGENTS.md` 统一约束 AI 行为
    

*   `Front/` 和 `Back/` 专注承载具体实现
    

## 十、这 5 份文档分别写什么

下面给一套最小可用模板。

### 1. `docs/architecture.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 系统架构

## 目标
- 系统解决什么问题

## 系统边界
- Front 负责什么
- Back 负责什么

## 核心模块
- Front 模块
- Back 模块

## 数据流
- 请求如何进入系统
- 数据如何返回给前端

## 外部依赖
- 数据库
- Redis
- 对象存储
- 第三方 API

## 关键约束
- 安全性
- 性能
- 幂等性
- 可观测性


```

### 2. `docs/frontend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 前端模式与约定

## 分层设计
- pages
- features
- components
- hooks
- services

## 状态管理
- 本地状态
- 服务端状态

## 数据请求规则
- 谁可以发请求
- 谁不能直接发请求

## 界面约定
- 表单
- loading
- 错误处理
- 权限控制

## 命名与目录规则
- 文件命名
- 目录命名


```

### 3. `docs/backend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 后端模式与约定

## 分层设计
- api/router
- service
- repository
- schema
- model

## 参数校验
- 参数校验在哪做

## 事务规则
- 事务在哪一层开启

## 错误处理
- 异常类型
- 错误码

## 日志与可观测性
- 日志规范
- tracing 规则

## 测试策略
- 单元测试
- 集成测试


```

### 4. `docs/api-contract.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# API 契约

## 响应包结构
- success
- data
- error

## 错误格式
- code
- message
- details

## 分页结构
- page
- page_size
- total
- items

## 命名规范
- snake_case 或 camelCase

## 时间格式
- ISO 8601
- 时区策略

## 版本策略
- v1 / 向后兼容


```

### 5. `docs/core-flows.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 核心业务流程

## 登录流程
- 用户输入账号密码
- Front 调用登录接口
- Back 校验并签发 token
- Front 存储用户态并跳转

## 列表查询流程
- Front 发起查询
- Back 校验权限
- Back 查询并返回分页结构
- Front 渲染列表

## 提交流程
- Front 表单校验
- Back 业务校验
- Back 落库并记录审计日志
- Front 提示结果


```

## 十一、根目录 `AGENTS.md` 应该怎么写

这里不要再重复架构设计，而是告诉 AI：

*   先读什么
    

*   必须遵守什么
    

*   改代码前后要检查什么
    

可以这样写：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 项目协作规则

在开始编码前，必须先阅读以下文档：
- docs/architecture.md
- docs/frontend-patterns.md
- docs/backend-patterns.md
- docs/api-contract.md
- docs/core-flows.md

硬性规则：
- Front 只负责展示、路由、交互，不负责影响数据一致性的业务规则。
- Back 负责业务规则、数据一致性、持久化和审计能力。
- 不要把影响数据正确性的业务判断写进 React 组件。
- 不要把校验逻辑、持久化逻辑混入界面层代码。
- 不允许随意发明新的 API 响应结构。
- 前端所有网络请求必须放在约定的 services 或 query 层。
- 后端必须保持 router、service、repository 的职责分离。
- 如果项目定义了视图模型层，页面组件不要直接耦合后端原始响应。
- 必须遵守现有目录结构、命名规则和模块边界。

前端实现规则：
- 优先按功能组织代码，放在 `Front/src/features/` 下。
- 通用 UI 组件放在 `Front/src/components/`。
- 可复用的业务 hooks 放在 `Front/src/hooks/`。
- 接口访问统一放在 `Front/src/services/`。
- 页面层只负责组合，不要在页面里堆积过多数据处理逻辑。

后端实现规则：
- Router 只处理 HTTP 输入输出，不承载业务编排。
- Service 负责业务逻辑。
- Repository 负责数据访问。
- Schema 负责输入输出边界和数据校验。
- 任何写数据库的路径，都必须考虑事务、审计和异常处理。

完成前检查：
- 检查 loading、empty、error、permission 等状态是否完整。
- 确认 API 结构符合 `docs/api-contract.md`。
- 确认错误处理方式保持一致。
- 确认需要的日志、审计点、事务边界已经补齐。
- 避免重复造抽象，优先复用已有模式。


```

## 十二、为什么一个根目录 `AGENTS.md` 更适合你这个场景

如果你的仓库本身就是一个完整业务系统，只是实现上分成 `Front` 和 `Back` 两个子项目，那通常没必要拆成两个 `AGENTS.md`。

一个根目录 `AGENTS.md` 的优势是：

*   AI 一进入仓库就先看到统一规则
    

*   前后端边界可以在同一个入口里被强调
    

*   API 契约、核心流程、命名规则不会被拆散
    

*   更适合做团队级讲解和规范推广
    

只有在下面这种情况，才更适合拆多个 `AGENTS.md`：

*   `Front` 和 `Back` 是两个独立仓库
    

*   两边团队完全分离
    

*   两边技术规范差异非常大
    

*   工具链和交付方式不同到需要完全独立约束
    

## 十三、lessions

### 结论一

`AI 最大的风险，不是写错代码，而是让团队在没有系统设计的情况下，持续高速地产出代码。`

### 结论二

`真正高杠杆的治理点，不在逐行审查实现，而在架构边界和抽象约束。`

### 结论三

`AGENTS.md 很重要，但它不是设计文档，它只是设计文档的执行入口。`

### 结论四

`前两层定住，第三层才能放心交给 AI；前两层没定住，第三层越快，系统越乱。`

## 十四、最后给一个最实用的落地建议

如果你现在就准备把 AI coding 引入一个 React + Python 的项目，不要先去优化提示词，也不要先追求让 AI 多写几个页面。

先做下面这五件事：

*   1.
    
    写 `docs/architecture.md`
    

*   2.
    
    写 `docs/frontend-patterns.md`
    

*   3.
    
    写 `docs/backend-patterns.md`
    

*   4.
    
    写 `docs/api-contract.md`
    

*   5.
    
    在根目录写一个统一的 `AGENTS.md`
    

当这五件事完成后，你会明显感觉到：

*   AI 写出来的代码更一致了
    

*   前后端对接更稳定了
    

*   review 的关注点更高了
    

*   重构不再那么痛苦
    

*   代码库的可维护性开始真正积累
    

因为从这一刻开始，你不是在 “让 AI 帮你写代码”，而是在：

`让 AI 在你定义好的系统里生产代码。`

这两者的差别，决定了代码库最终是复利，还是失控。

## from x

![](https://article-images.zsxq.com/FrObNtMnStf6W3rXbBfx6klpMl5H)

  

核心： 先设计前架构，规范，再放大 AI 产能

![](https://article-images.zsxq.com/FssXfk9dWONSo_nUZX2JjSKz7Man)

  

昨天看到 x 上说的一句话，我觉得非常值得所有正在用 AI 写代码的人停下来想一想：

如果一个代码库一开始就是由 agent 写出来的，那你不应该把主要精力放在 “逐行读懂它” 上。

这句话听起来有点反直觉，但它点中了一个非常现实的问题。

很多团队在用了 AI 之后，代码产出速度会突然暴涨。页面能很快出来，接口能很快补齐，脚本能很快跑通，Bug 也能被快速修掉。表面上看，一切都在提速；但过一段时间你再回头，会发现另外一件事也在同时发生：

`系统正在失去可理解性。`

不是代码不能跑了，而是没人说得清：

*   这个系统到底是怎么分层的
    

*   模块之间边界在哪里
    

*   为什么这里要这么设计
    

*   哪些接口是稳定契约
    

*   哪些地方可以改，哪些地方一改就会牵一发动全身
    

这就是 AI coding 时代最容易出现的失控点。

问题从来不只是 “代码质量差”，而是 `代码产能被放大了，但系统治理没有同步升级。`

## 一、AI 为什么会让代码更容易失控

很多人会以为，AI 写代码快，所以问题只是 “写得不够严谨”。其实不是。更深层的原因是：

`AI 把第三层产出放大了，但没有自动把第一层和第二层治理能力一起补上。`

为什么会这样？

*   AI 给出的反馈太快了。你描述一个需求，它立刻就能给出页面、函数、接口、配置。人会自然地进入 “先做出来再说” 的节奏。
    

*   局部修补成本太低了。以前多写一层逻辑要思考半天，现在哪里不对就让 AI 补一块，局部最优越来越便宜。
    

*   “能运行” 很容易制造理解错觉。页面打开了，接口通了，测试也能过，于是团队误以为系统已经清晰了。
    

*   大多数 AI coding 都围绕当前文件、当前任务、当前报错展开，它天然强化的是局部实现，而不是系统层思考。
    

*   团队的激励机制也在推着大家追求 “可见产出”，而不是优先建设 “可长期演化的结构”。
    

所以一句话总结就是：

`AI 让编码变快了，也让人更容易绕过思考。`

## 二、真正该盯住的，不是每一行代码，而是三层高度

如果我们把一个代码库拆成三个高度来看，就会更清楚：

### 第一层：Architecture

这一层关心的是系统级问题：

*   系统边界
    

*   核心模块
    

*   数据流向
    

*   服务职责
    

*   外部依赖
    

*   安全、性能、幂等、可观测性等关键约束
    

这一层决定的是：`系统到底是什么。`

### 第二层：Patterns & Abstractions

这一层关心的是项目内部怎么组织：

*   模块如何拆分
    

*   接口如何定义
    

*   前后端如何对齐契约
    

*   组件、服务、仓储、Schema、状态管理如何分层
    

*   哪些抽象是稳定的，哪些只是局部实现
    

这一层决定的是：`系统应该按什么方式生长。`

### 第三层：File-level Code

这一层才是我们平时最容易看到的内容：

*   函数
    

*   类
    

*   页面
    

*   组件
    

*   配置
    

*   测试
    

*   各种具体实现细节
    

这一层决定的是：`某个功能是怎么被写出来的。`

## 三、为什么前两层比第三层更重要

这不是说第三层不重要，而是说：

`如果前两层没定住，第三层写得越快，系统越容易失控。`

因为第三层的代码，本质上是在执行前两层的设计意图。

如果架构边界不清晰：

*   前端会混入业务规则
    

*   后端会承担展示逻辑
    

*   同一个能力会在不同模块重复实现
    

*   接口格式会越长越随意
    

*   新功能每次都像临时拼接
    

如果抽象层没定住：

*   今天写一个 `service`
    

*   明天加一个 `utils`
    

*   后天再来一个 `manager`
    

*   每个文件都 “看起来合理”，但整体没有统一结构
    

这就是典型的 AI 时代 “局部都对，整体失控”。

所以真正高杠杆的做法不是盯着 AI 写的每一行，而是先把前两层设计清楚，再让 AI 在约束内高速生产。

一句话总结：

`人的职责，不再是阅读全部实现，而是定义系统边界、抽象层级和验收机制。`

## 四、前两层到底应该写什么

很多人听到这里会点头，但一落地又会卡住：

`那前两层到底要写成什么？`

最简单的理解方式是：

*   第一层文档回答：`系统怎么组成`
    

*   第二层文档回答：`团队应该怎么写`
    

下面我们直接用一个具体案例说明。

## 五、案例：React 前端 + Python 后端，如何把前两层写出来

假设你现在有两个项目：

*   `Front`：React 前端
    

*   `Back`：Python 后端
    

很多团队在这个阶段最容易犯的错误是，直接给 AI 下需求：

*   帮我把登录页做出来
    

*   帮我写一个用户列表接口
    

*   帮我接一下分页
    

*   帮我补一个导出功能
    

这样做短期非常爽，但中期一定会出现结构漂移。

正确做法是，先把前两层落成文档，再让 AI 按文档干活。

## 六、第一层：Architecture 文档应该写什么

这一层你至少要写清楚下面这些内容。

### 1. 系统边界

*   `Front` 负责什么
    

*   `Back` 负责什么
    

*   哪些规则在前端做
    

*   哪些规则必须在后端做
    

例如：

*   `Front` 负责展示、交互、路由、表单体验、用户态呈现
    

*   `Back` 负责业务规则、权限校验、数据一致性、持久化、审计
    

### 2. 前后端通信方式

*   REST 还是 GraphQL
    

*   是否有 SSE / WebSocket
    

*   文件上传怎么走
    

*   鉴权 Token 怎么传
    

### 3. 核心业务流

至少写出 3 到 5 个关键流程，比如：

*   用户登录
    

*   列表查询
    

*   表单提交
    

*   文件上传
    

*   管理员审批
    

每个流程都应该明确：

*   谁发起
    

*   请求如何流转
    

*   后端经过哪些层
    

*   最终返回什么结果
    

### 4. 核心模块图

前端有哪些大模块：

*   `auth`
    

*   `dashboard`
    

*   `users`
    

*   `settings`
    

后端有哪些大模块：

*   `auth`
    

*   `user`
    

*   `order`
    

*   `notification`
    

### 5. 外部依赖

*   数据库
    

*   Redis
    

*   对象存储
    

*   消息队列
    

*   第三方 API
    

### 6. 关键约束

这一块最容易被忽略，但恰恰最重要：

*   权限模型
    

*   审计要求
    

*   接口幂等性
    

*   分页规范
    

*   错误码规范
    

*   性能预算
    

*   可观测性要求
    

第一层的核心不是 “写一堆描述”，而是把系统的边界和硬规则钉住。

## 七、第二层：Patterns & Abstractions 文档应该写什么

这一层说的是：

`项目内部到底按什么方式生长。`

### 前端要定什么

以 React 项目为例，至少应该定这些：

*   页面层、组件层、hooks 层、services 层如何分工
    

*   数据请求统一放哪里
    

*   是否允许组件直接请求接口
    

*   状态管理怎么做
    

*   表单状态怎么管理
    

*   错误提示和 loading 怎么统一
    

*   权限控制放在哪一层
    

*   通用组件与业务组件如何区分
    

*   目录结构怎么组织
    

### 后端要定什么

以 Python 项目为例，至少应该定这些：

*   router / service / repository 如何分层
    

*   schema / dto / model 如何区分
    

*   参数校验在哪一层做
    

*   事务在哪一层控制
    

*   异常如何统一抛出
    

*   错误码怎么定义
    

*   日志和 tracing 怎么埋
    

*   配置管理怎么做
    

*   单元测试和集成测试怎么分
    

### 前后端共同要定什么

这是最容易被低估的一层，也是最容易导致合作失控的地方：

*   API 响应格式
    

*   分页结构
    

*   时间格式
    

*   字段命名规范
    

*   空值语义
    

*   错误响应格式
    

*   版本兼容策略
    

很多项目不是代码写坏了，而是 `前后端抽象没有稳定契约`。

## 八、是不是写到 AGENTS.md 里

要写，但不能只写在 `AGENTS.md` 里。

这是一个非常关键的区分：

*   `设计文档` 负责定义世界
    

*   `AGENTS.md` 负责约束 AI 怎么在这个世界里干活
    

换句话说：

*   前两层文档是系统真相
    

*   `AGENTS.md` 是 AI 的执行手册
    

如果你把所有内容都堆进 `AGENTS.md`，通常会出现两个问题：

*   文档越来越长，但结构越来越散
    

*   AI 看起来拿到了规则，实际上没有拿到清晰的设计对象
    

更合理的做法是：

*   详细设计独立成文档
    

*   `AGENTS.md` 只写入口、硬约束、执行规则
    

## 九、推荐目录结构

如果是 `Front` 和 `Back` 两个项目，并且整个仓库只维护一个根目录 `AGENTS.md`，我建议目录至少这样组织：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
project-root/
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── frontend-patterns.md
│   ├── backend-patterns.md
│   └── core-flows.md
├── Front/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   └── tests/
└── Back/
    ├── app/
    │   ├── api/
    │   ├── services/
    │   ├── repositories/
    │   ├── schemas/
    │   ├── models/
    │   ├── core/
    │   └── utils/
    └── tests/



```

这个结构的关键不是 “长得标准”，而是它把三件事拆清楚了：

*   `docs/` 放前两层真相
    

*   根目录 `AGENTS.md` 统一约束 AI 行为
    

*   `Front/` 和 `Back/` 专注承载具体实现
    

## 十、这 5 份文档分别写什么

下面给一套最小可用模板。

### 1. `docs/architecture.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 系统架构

## 目标
- 系统解决什么问题

## 系统边界
- Front 负责什么
- Back 负责什么

## 核心模块
- Front 模块
- Back 模块

## 数据流
- 请求如何进入系统
- 数据如何返回给前端

## 外部依赖
- 数据库
- Redis
- 对象存储
- 第三方 API

## 关键约束
- 安全性
- 性能
- 幂等性
- 可观测性



```

### 2. `docs/frontend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 前端模式与约定

## 分层设计
- pages
- features
- components
- hooks
- services

## 状态管理
- 本地状态
- 服务端状态

## 数据请求规则
- 谁可以发请求
- 谁不能直接发请求

## 界面约定
- 表单
- loading
- 错误处理
- 权限控制

## 命名与目录规则
- 文件命名
- 目录命名



```

### 3. `docs/backend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 后端模式与约定

## 分层设计
- api/router
- service
- repository
- schema
- model

## 参数校验
- 参数校验在哪做

## 事务规则
- 事务在哪一层开启

## 错误处理
- 异常类型
- 错误码

## 日志与可观测性
- 日志规范
- tracing 规则

## 测试策略
- 单元测试
- 集成测试



```

### 4. `docs/api-contract.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# API 契约

## 响应包结构
- success
- data
- error

## 错误格式
- code
- message
- details

## 分页结构
- page
- page_size
- total
- items

## 命名规范
- snake_case 或 camelCase

## 时间格式
- ISO 8601
- 时区策略

## 版本策略
- v1 / 向后兼容



```

### 5. `docs/core-flows.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 核心业务流程

## 登录流程
- 用户输入账号密码
- Front 调用登录接口
- Back 校验并签发 token
- Front 存储用户态并跳转

## 列表查询流程
- Front 发起查询
- Back 校验权限
- Back 查询并返回分页结构
- Front 渲染列表

## 提交流程
- Front 表单校验
- Back 业务校验
- Back 落库并记录审计日志
- Front 提示结果



```

## 十一、根目录 `AGENTS.md` 应该怎么写

这里不要再重复架构设计，而是告诉 AI：

*   先读什么
    

*   必须遵守什么
    

*   改代码前后要检查什么
    

可以这样写：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 项目协作规则

在开始编码前，必须先阅读以下文档：
- docs/architecture.md
- docs/frontend-patterns.md
- docs/backend-patterns.md
- docs/api-contract.md
- docs/core-flows.md

硬性规则：
- Front 只负责展示、路由、交互，不负责影响数据一致性的业务规则。
- Back 负责业务规则、数据一致性、持久化和审计能力。
- 不要把影响数据正确性的业务判断写进 React 组件。
- 不要把校验逻辑、持久化逻辑混入界面层代码。
- 不允许随意发明新的 API 响应结构。
- 前端所有网络请求必须放在约定的 services 或 query 层。
- 后端必须保持 router、service、repository 的职责分离。
- 如果项目定义了视图模型层，页面组件不要直接耦合后端原始响应。
- 必须遵守现有目录结构、命名规则和模块边界。

前端实现规则：
- 优先按功能组织代码，放在 `Front/src/features/` 下。
- 通用 UI 组件放在 `Front/src/components/`。
- 可复用的业务 hooks 放在 `Front/src/hooks/`。
- 接口访问统一放在 `Front/src/services/`。
- 页面层只负责组合，不要在页面里堆积过多数据处理逻辑。

后端实现规则：
- Router 只处理 HTTP 输入输出，不承载业务编排。
- Service 负责业务逻辑。
- Repository 负责数据访问。
- Schema 负责输入输出边界和数据校验。
- 任何写数据库的路径，都必须考虑事务、审计和异常处理。

完成前检查：
- 检查 loading、empty、error、permission 等状态是否完整。
- 确认 API 结构符合 `docs/api-contract.md`。
- 确认错误处理方式保持一致。
- 确认需要的日志、审计点、事务边界已经补齐。
- 避免重复造抽象，优先复用已有模式。



```

## 十二、为什么一个根目录 `AGENTS.md` 更适合你这个场景

如果你的仓库本身就是一个完整业务系统，只是实现上分成 `Front` 和 `Back` 两个子项目，那通常没必要拆成两个 `AGENTS.md`。

一个根目录 `AGENTS.md` 的优势是：

*   AI 一进入仓库就先看到统一规则
    

*   前后端边界可以在同一个入口里被强调
    

*   API 契约、核心流程、命名规则不会被拆散
    

*   更适合做团队级讲解和规范推广
    

只有在下面这种情况，才更适合拆多个 `AGENTS.md`：

*   `Front` 和 `Back` 是两个独立仓库
    

*   两边团队完全分离
    

*   两边技术规范差异非常大
    

*   工具链和交付方式不同到需要完全独立约束
    

## 十三、lessions

### 结论一

`AI 最大的风险，不是写错代码，而是让团队在没有系统设计的情况下，持续高速地产出代码。`

### 结论二

`真正高杠杆的治理点，不在逐行审查实现，而在架构边界和抽象约束。`

### 结论三

`AGENTS.md 很重要，但它不是设计文档，它只是设计文档的执行入口。`

### 结论四

`前两层定住，第三层才能放心交给 AI；前两层没定住，第三层越快，系统越乱。`

## 十四、最后给一个最实用的落地建议

如果你现在就准备把 AI coding 引入一个 React + Python 的项目，不要先去优化提示词，也不要先追求让 AI 多写几个页面。

先做下面这五件事：

*   1.
    
    写 `docs/architecture.md`
    

*   2.
    
    写 `docs/frontend-patterns.md`
    

*   3.
    
    写 `docs/backend-patterns.md`
    

*   4.
    
    写 `docs/api-contract.md`
    

*   5.
    
    在根目录写一个统一的 `AGENTS.md`
    

当这五件事完成后，你会明显感觉到：

*   AI 写出来的代码更一致了
    

*   前后端对接更稳定了
    

*   review 的关注点更高了
    

*   重构不再那么痛苦
    

*   代码库的可维护性开始真正积累
    

因为从这一刻开始，你不是在 “让 AI 帮你写代码”，而是在：

`让 AI 在你定义好的系统里生产代码。`

这两者的差别，决定了代码库最终是复利，还是失控。

## from x

![](https://article-images.zsxq.com/FrObNtMnStf6W3rXbBfx6klpMl5H)

  

核心： 先设计前架构，规范，再放大 AI 产能

![](https://article-images.zsxq.com/FssXfk9dWONSo_nUZX2JjSKz7Man)

  

昨天看到 x 上说的一句话，我觉得非常值得所有正在用 AI 写代码的人停下来想一想：

如果一个代码库一开始就是由 agent 写出来的，那你不应该把主要精力放在 “逐行读懂它” 上。

这句话听起来有点反直觉，但它点中了一个非常现实的问题。

很多团队在用了 AI 之后，代码产出速度会突然暴涨。页面能很快出来，接口能很快补齐，脚本能很快跑通，Bug 也能被快速修掉。表面上看，一切都在提速；但过一段时间你再回头，会发现另外一件事也在同时发生：

`系统正在失去可理解性。`

不是代码不能跑了，而是没人说得清：

*   这个系统到底是怎么分层的
    

*   模块之间边界在哪里
    

*   为什么这里要这么设计
    

*   哪些接口是稳定契约
    

*   哪些地方可以改，哪些地方一改就会牵一发动全身
    

这就是 AI coding 时代最容易出现的失控点。

问题从来不只是 “代码质量差”，而是 `代码产能被放大了，但系统治理没有同步升级。`

## 一、AI 为什么会让代码更容易失控

很多人会以为，AI 写代码快，所以问题只是 “写得不够严谨”。其实不是。更深层的原因是：

`AI 把第三层产出放大了，但没有自动把第一层和第二层治理能力一起补上。`

为什么会这样？

*   AI 给出的反馈太快了。你描述一个需求，它立刻就能给出页面、函数、接口、配置。人会自然地进入 “先做出来再说” 的节奏。
    

*   局部修补成本太低了。以前多写一层逻辑要思考半天，现在哪里不对就让 AI 补一块，局部最优越来越便宜。
    

*   “能运行” 很容易制造理解错觉。页面打开了，接口通了，测试也能过，于是团队误以为系统已经清晰了。
    

*   大多数 AI coding 都围绕当前文件、当前任务、当前报错展开，它天然强化的是局部实现，而不是系统层思考。
    

*   团队的激励机制也在推着大家追求 “可见产出”，而不是优先建设 “可长期演化的结构”。
    

所以一句话总结就是：

`AI 让编码变快了，也让人更容易绕过思考。`

## 二、真正该盯住的，不是每一行代码，而是三层高度

如果我们把一个代码库拆成三个高度来看，就会更清楚：

### 第一层：Architecture

这一层关心的是系统级问题：

*   系统边界
    

*   核心模块
    

*   数据流向
    

*   服务职责
    

*   外部依赖
    

*   安全、性能、幂等、可观测性等关键约束
    

这一层决定的是：`系统到底是什么。`

### 第二层：Patterns & Abstractions

这一层关心的是项目内部怎么组织：

*   模块如何拆分
    

*   接口如何定义
    

*   前后端如何对齐契约
    

*   组件、服务、仓储、Schema、状态管理如何分层
    

*   哪些抽象是稳定的，哪些只是局部实现
    

这一层决定的是：`系统应该按什么方式生长。`

### 第三层：File-level Code

这一层才是我们平时最容易看到的内容：

*   函数
    

*   类
    

*   页面
    

*   组件
    

*   配置
    

*   测试
    

*   各种具体实现细节
    

这一层决定的是：`某个功能是怎么被写出来的。`

## 三、为什么前两层比第三层更重要

这不是说第三层不重要，而是说：

`如果前两层没定住，第三层写得越快，系统越容易失控。`

因为第三层的代码，本质上是在执行前两层的设计意图。

如果架构边界不清晰：

*   前端会混入业务规则
    

*   后端会承担展示逻辑
    

*   同一个能力会在不同模块重复实现
    

*   接口格式会越长越随意
    

*   新功能每次都像临时拼接
    

如果抽象层没定住：

*   今天写一个 `service`
    

*   明天加一个 `utils`
    

*   后天再来一个 `manager`
    

*   每个文件都 “看起来合理”，但整体没有统一结构
    

这就是典型的 AI 时代 “局部都对，整体失控”。

所以真正高杠杆的做法不是盯着 AI 写的每一行，而是先把前两层设计清楚，再让 AI 在约束内高速生产。

一句话总结：

`人的职责，不再是阅读全部实现，而是定义系统边界、抽象层级和验收机制。`

## 四、前两层到底应该写什么

很多人听到这里会点头，但一落地又会卡住：

`那前两层到底要写成什么？`

最简单的理解方式是：

*   第一层文档回答：`系统怎么组成`
    

*   第二层文档回答：`团队应该怎么写`
    

下面我们直接用一个具体案例说明。

## 五、案例：React 前端 + Python 后端，如何把前两层写出来

假设你现在有两个项目：

*   `Front`：React 前端
    

*   `Back`：Python 后端
    

很多团队在这个阶段最容易犯的错误是，直接给 AI 下需求：

*   帮我把登录页做出来
    

*   帮我写一个用户列表接口
    

*   帮我接一下分页
    

*   帮我补一个导出功能
    

这样做短期非常爽，但中期一定会出现结构漂移。

正确做法是，先把前两层落成文档，再让 AI 按文档干活。

## 六、第一层：Architecture 文档应该写什么

这一层你至少要写清楚下面这些内容。

### 1. 系统边界

*   `Front` 负责什么
    

*   `Back` 负责什么
    

*   哪些规则在前端做
    

*   哪些规则必须在后端做
    

例如：

*   `Front` 负责展示、交互、路由、表单体验、用户态呈现
    

*   `Back` 负责业务规则、权限校验、数据一致性、持久化、审计
    

### 2. 前后端通信方式

*   REST 还是 GraphQL
    

*   是否有 SSE / WebSocket
    

*   文件上传怎么走
    

*   鉴权 Token 怎么传
    

### 3. 核心业务流

至少写出 3 到 5 个关键流程，比如：

*   用户登录
    

*   列表查询
    

*   表单提交
    

*   文件上传
    

*   管理员审批
    

每个流程都应该明确：

*   谁发起
    

*   请求如何流转
    

*   后端经过哪些层
    

*   最终返回什么结果
    

### 4. 核心模块图

前端有哪些大模块：

*   `auth`
    

*   `dashboard`
    

*   `users`
    

*   `settings`
    

后端有哪些大模块：

*   `auth`
    

*   `user`
    

*   `order`
    

*   `notification`
    

### 5. 外部依赖

*   数据库
    

*   Redis
    

*   对象存储
    

*   消息队列
    

*   第三方 API
    

### 6. 关键约束

这一块最容易被忽略，但恰恰最重要：

*   权限模型
    

*   审计要求
    

*   接口幂等性
    

*   分页规范
    

*   错误码规范
    

*   性能预算
    

*   可观测性要求
    

第一层的核心不是 “写一堆描述”，而是把系统的边界和硬规则钉住。

## 七、第二层：Patterns & Abstractions 文档应该写什么

这一层说的是：

`项目内部到底按什么方式生长。`

### 前端要定什么

以 React 项目为例，至少应该定这些：

*   页面层、组件层、hooks 层、services 层如何分工
    

*   数据请求统一放哪里
    

*   是否允许组件直接请求接口
    

*   状态管理怎么做
    

*   表单状态怎么管理
    

*   错误提示和 loading 怎么统一
    

*   权限控制放在哪一层
    

*   通用组件与业务组件如何区分
    

*   目录结构怎么组织
    

### 后端要定什么

以 Python 项目为例，至少应该定这些：

*   router / service / repository 如何分层
    

*   schema / dto / model 如何区分
    

*   参数校验在哪一层做
    

*   事务在哪一层控制
    

*   异常如何统一抛出
    

*   错误码怎么定义
    

*   日志和 tracing 怎么埋
    

*   配置管理怎么做
    

*   单元测试和集成测试怎么分
    

### 前后端共同要定什么

这是最容易被低估的一层，也是最容易导致合作失控的地方：

*   API 响应格式
    

*   分页结构
    

*   时间格式
    

*   字段命名规范
    

*   空值语义
    

*   错误响应格式
    

*   版本兼容策略
    

很多项目不是代码写坏了，而是 `前后端抽象没有稳定契约`。

## 八、是不是写到 AGENTS.md 里

要写，但不能只写在 `AGENTS.md` 里。

这是一个非常关键的区分：

*   `设计文档` 负责定义世界
    

*   `AGENTS.md` 负责约束 AI 怎么在这个世界里干活
    

换句话说：

*   前两层文档是系统真相
    

*   `AGENTS.md` 是 AI 的执行手册
    

如果你把所有内容都堆进 `AGENTS.md`，通常会出现两个问题：

*   文档越来越长，但结构越来越散
    

*   AI 看起来拿到了规则，实际上没有拿到清晰的设计对象
    

更合理的做法是：

*   详细设计独立成文档
    

*   `AGENTS.md` 只写入口、硬约束、执行规则
    

## 九、推荐目录结构

如果是 `Front` 和 `Back` 两个项目，并且整个仓库只维护一个根目录 `AGENTS.md`，我建议目录至少这样组织：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
project-root/
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── frontend-patterns.md
│   ├── backend-patterns.md
│   └── core-flows.md
├── Front/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   └── tests/
└── Back/
    ├── app/
    │   ├── api/
    │   ├── services/
    │   ├── repositories/
    │   ├── schemas/
    │   ├── models/
    │   ├── core/
    │   └── utils/
    └── tests/


```

这个结构的关键不是 “长得标准”，而是它把三件事拆清楚了：

*   `docs/` 放前两层真相
    

*   根目录 `AGENTS.md` 统一约束 AI 行为
    

*   `Front/` 和 `Back/` 专注承载具体实现
    

## 十、这 5 份文档分别写什么

下面给一套最小可用模板。

### 1. `docs/architecture.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 系统架构

## 目标
- 系统解决什么问题

## 系统边界
- Front 负责什么
- Back 负责什么

## 核心模块
- Front 模块
- Back 模块

## 数据流
- 请求如何进入系统
- 数据如何返回给前端

## 外部依赖
- 数据库
- Redis
- 对象存储
- 第三方 API

## 关键约束
- 安全性
- 性能
- 幂等性
- 可观测性


```

### 2. `docs/frontend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 前端模式与约定

## 分层设计
- pages
- features
- components
- hooks
- services

## 状态管理
- 本地状态
- 服务端状态

## 数据请求规则
- 谁可以发请求
- 谁不能直接发请求

## 界面约定
- 表单
- loading
- 错误处理
- 权限控制

## 命名与目录规则
- 文件命名
- 目录命名


```

### 3. `docs/backend-patterns.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 后端模式与约定

## 分层设计
- api/router
- service
- repository
- schema
- model

## 参数校验
- 参数校验在哪做

## 事务规则
- 事务在哪一层开启

## 错误处理
- 异常类型
- 错误码

## 日志与可观测性
- 日志规范
- tracing 规则

## 测试策略
- 单元测试
- 集成测试


```

### 4. `docs/api-contract.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# API 契约

## 响应包结构
- success
- data
- error

## 错误格式
- code
- message
- details

## 分页结构
- page
- page_size
- total
- items

## 命名规范
- snake_case 或 camelCase

## 时间格式
- ISO 8601
- 时区策略

## 版本策略
- v1 / 向后兼容


```

### 5. `docs/core-flows.md`

建议章节：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 核心业务流程

## 登录流程
- 用户输入账号密码
- Front 调用登录接口
- Back 校验并签发 token
- Front 存储用户态并跳转

## 列表查询流程
- Front 发起查询
- Back 校验权限
- Back 查询并返回分页结构
- Front 渲染列表

## 提交流程
- Front 表单校验
- Back 业务校验
- Back 落库并记录审计日志
- Front 提示结果


```

## 十一、根目录 `AGENTS.md` 应该怎么写

这里不要再重复架构设计，而是告诉 AI：

*   先读什么
    

*   必须遵守什么
    

*   改代码前后要检查什么
    

可以这样写：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
# 项目协作规则

在开始编码前，必须先阅读以下文档：
- docs/architecture.md
- docs/frontend-patterns.md
- docs/backend-patterns.md
- docs/api-contract.md
- docs/core-flows.md

硬性规则：
- Front 只负责展示、路由、交互，不负责影响数据一致性的业务规则。
- Back 负责业务规则、数据一致性、持久化和审计能力。
- 不要把影响数据正确性的业务判断写进 React 组件。
- 不要把校验逻辑、持久化逻辑混入界面层代码。
- 不允许随意发明新的 API 响应结构。
- 前端所有网络请求必须放在约定的 services 或 query 层。
- 后端必须保持 router、service、repository 的职责分离。
- 如果项目定义了视图模型层，页面组件不要直接耦合后端原始响应。
- 必须遵守现有目录结构、命名规则和模块边界。

前端实现规则：
- 优先按功能组织代码，放在 `Front/src/features/` 下。
- 通用 UI 组件放在 `Front/src/components/`。
- 可复用的业务 hooks 放在 `Front/src/hooks/`。
- 接口访问统一放在 `Front/src/services/`。
- 页面层只负责组合，不要在页面里堆积过多数据处理逻辑。

后端实现规则：
- Router 只处理 HTTP 输入输出，不承载业务编排。
- Service 负责业务逻辑。
- Repository 负责数据访问。
- Schema 负责输入输出边界和数据校验。
- 任何写数据库的路径，都必须考虑事务、审计和异常处理。

完成前检查：
- 检查 loading、empty、error、permission 等状态是否完整。
- 确认 API 结构符合 `docs/api-contract.md`。
- 确认错误处理方式保持一致。
- 确认需要的日志、审计点、事务边界已经补齐。
- 避免重复造抽象，优先复用已有模式。


```

## 十二、为什么一个根目录 `AGENTS.md` 更适合你这个场景

如果你的仓库本身就是一个完整业务系统，只是实现上分成 `Front` 和 `Back` 两个子项目，那通常没必要拆成两个 `AGENTS.md`。

一个根目录 `AGENTS.md` 的优势是：

*   AI 一进入仓库就先看到统一规则
    

*   前后端边界可以在同一个入口里被强调
    

*   API 契约、核心流程、命名规则不会被拆散
    

*   更适合做团队级讲解和规范推广
    

只有在下面这种情况，才更适合拆多个 `AGENTS.md`：

*   `Front` 和 `Back` 是两个独立仓库
    

*   两边团队完全分离
    

*   两边技术规范差异非常大
    

*   工具链和交付方式不同到需要完全独立约束
    

## 十三、lessions

### 结论一

`AI 最大的风险，不是写错代码，而是让团队在没有系统设计的情况下，持续高速地产出代码。`

### 结论二

`真正高杠杆的治理点，不在逐行审查实现，而在架构边界和抽象约束。`

### 结论三

`AGENTS.md 很重要，但它不是设计文档，它只是设计文档的执行入口。`

### 结论四

`前两层定住，第三层才能放心交给 AI；前两层没定住，第三层越快，系统越乱。`

## 十四、最后给一个最实用的落地建议

如果你现在就准备把 AI coding 引入一个 React + Python 的项目，不要先去优化提示词，也不要先追求让 AI 多写几个页面。

先做下面这五件事：

*   1.
    
    写 `docs/architecture.md`
    

*   2.
    
    写 `docs/frontend-patterns.md`
    

*   3.
    
    写 `docs/backend-patterns.md`
    

*   4.
    
    写 `docs/api-contract.md`
    

*   5.
    
    在根目录写一个统一的 `AGENTS.md`
    

当这五件事完成后，你会明显感觉到：

*   AI 写出来的代码更一致了
    

*   前后端对接更稳定了
    

*   review 的关注点更高了
    

*   重构不再那么痛苦
    

*   代码库的可维护性开始真正积累
    

因为从这一刻开始，你不是在 “让 AI 帮你写代码”，而是在：

`让 AI 在你定义好的系统里生产代码。`

这两者的差别，决定了代码库最终是复利，还是失控。

## from x

![](https://article-images.zsxq.com/FrObNtMnStf6W3rXbBfx6klpMl5H)

  

![](https://articles.zsxq.com/assets_dweb/logo@2x.png)

知识星球

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join_group.html?group_id=28882285418421