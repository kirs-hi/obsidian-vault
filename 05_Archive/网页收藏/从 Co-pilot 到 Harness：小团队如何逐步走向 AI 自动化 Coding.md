---
url: https://articles.zsxq.com/id_r3st9g5ar5ph.html
title: 从 Co-pilot 到 Harness：小团队如何逐步走向 AI 自动化 Coding
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-13 16:53:56
tags:

banner: "https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8="
banner_icon: 🔖
---
# 从 Co-pilot 到 Harness：小团队如何逐步走向 AI 自动化 Coding

[来自： 雷哥 AI 解决方案](https://wx.zsxq.com/group/28882285418421)

![](https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8=)

雷哥

2026 年 03 月 31 日 12:15

如果今天让一个小团队直接进入 “AI 自动写代码” 的状态，结果大概率不会太理想。问题通常不在于模型不够聪明，而在于团队还没有把自己的约束、经验、验收标准和工程边界组织成一个 AI 能稳定理解、稳定执行、稳定验证的系统。

这也是我读完 OpenAI 在 2026 年 2 月 11 日发布的 [Harness engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/) 后，结合我自己的框架与真实项目样本，得到的核心判断：真正重要的不是 “让 AI 更会写代码”，而是 “让工程环境本身变成一个可以约束、验证、纠偏 AI 的 harness”。

我正在研发自己的 AI 自动化 coding 2.0，这套思路其实已经非常接近这条路线的本质。我的判断是：先从人和 AI 的协作开发开始，把 AI 犯错、返工、不符合规范的地方沉淀成规则文件，再逐步把这些规则、经验、企业约束汇总成一张 “开发规范地图”，最后再结合任务拆解、验收标准、build、validate，让 AI 在这些约束下自动完成开发。这条逻辑不是空想，方向也是对的，而且我已经用自己的框架把它做成了一个有真实闭环的系统。

但如果要把这件事真正讲清楚，有几个关键点必须说透。

(今天是来补逻辑的, 哈哈, 思路有了, 后边我把源码放出来, 大家就更有收获了)

![](https://article-images.zsxq.com/Fitt7RWpEDE2PXcR7_rw4hUkfp3C)

  

## 一、Harness Engineering 讲的到底是什么

OpenAI 这篇文章里最重要的，不是某个单点技巧，而是一整套认识方式。

第一，`人类掌舵，智能体执行`。AI 不是工程负责人，它更像一个执行者。真正决定目标、边界、质量、风险、优先级的，仍然应该是人。

第二，`知识必须进入 repo`。如果团队的规范只存在于人的脑子里、微信群里、口头习惯里，AI 是吃不到的。只有当这些知识进入代码库，成为文件、配置、测试、脚本、文档，AI 才能把它们作为工作的依据。

第三，`AGENTS.md 不是百科全书，而是地图`。很多人会觉得 “我给 AI 写一本特别长的说明书，它就会做得更好”。实际恰恰相反。大而全的说明文档很快会过期，也很难被稳定执行。更有效的方式是：用一份短而清晰的索引文件，把 AI 指向正确的规则、正确的上下文、正确的工具。

第四，`文档不是终点，规则要尽量机械化`。如果某条规范经常被违反，那就不要永远停留在 “请遵守规范” 这个层面，而是要把它升级成 lint、test、schema 校验、浏览器断言、CI 检查。文档是软约束，代码化的检查才是硬约束。

第五，`自动化 coding 的前提不是自治，而是验证闭环`。如果没有 build、test、browser verification、日志、状态回写、失败重试、人工接管点，那么所谓 “自动化” 只是更快地产生错误。

这一套观点，和我正在做的事情，本质上是一致的。

## 二、我原始思路里最对的地方

我最重要的判断，是把 “自动化 coding” 的起点放在了 `co-pilot 协作阶段`，而不是一上来就追求完全自治。

这一步特别关键。因为真正可靠的约束，并不是拍脑袋设计出来的，而是从真实协作中的错误中长出来的。比如：

*   AI 改了一个功能，但忘了更新另一个联动状态
    

*   AI 通过了 typecheck，但浏览器点击无反应
    

*   AI 没遵守代码库已有模式
    

*   AI 为了完成局部目标，引入了全局回归
    

*   AI 在环境、端口、测试依赖上判断失误
    

如果这些问题只是 “当场修掉”，那经验很快就丢了。只有当我把它们沉淀下来，写成规则、写成模式、写成验证脚本，它们才会变成未来自动化的燃料。

这也是我为什么会坚持 “先有 copilot coding，再有资产沉淀，再走向自动化 coding” 这条路线。

## 三、但这里有一个必须修正的地方：约束不只是从错误里来

我的原始逻辑里有一个地方需要补强：我比较强调 “AI 做错了，我们就修，然后把规则沉淀下来”。这条路径没错，但不完整。

因为约束的来源不只有 “错误复盘”，还应该包括四类前置约束：

*   产品约束：什么算完成，什么体验不可接受
    

*   架构约束：哪些边界不能跨，哪些目录不能乱改，哪些层不能反向依赖
    

*   安全约束：哪些数据不能碰，哪些权限不能给，哪些操作必须审批
    

*   组织约束：提交方式、分支策略、review 规则、上线节奏、回滚方式
    

如果只从错误中长规则，那最后会得到一座 “事故博物馆”，而不是一套 “工程操作系统”。真正有效的 harness，应该是前置约束和后验经验一起构成的。

(就是说除了 AI 修正错误的一些沉淀, 还是需要人来把控一些约束的, 并且把约束也沉淀下来)

## 四、真正的核心不是 “拆得够细”，而是 “拆得可收敛”

我有一个很关键的判断：如果一个 PRD 可以拆得够细，又有验证标准，那就可以用框架自动化开发。

这句话大方向是对的，但更准确的表述应该是：

`不是 PRD 拆得够细就行，而是任务必须被拆成“可独立收敛的 story”，并且每个 story 的验收标准可以被稳定验证。`

这两个条件缺一不可。

### 1. 可独立收敛

一个 story 必须尽量满足：

*   边界清楚
    

*   依赖明确
    

*   影响范围可控
    

*   能单独实现
    

*   能单独验证
    

如果 story 之间强耦合、顺序混乱、共享很多隐式状态，那么就算写得很细，也不一定适合自动化。

### 2. 验收标准可验证

验收标准必须尽量具体，最好能映射成：

*   一个命令
    

*   一个构建结果
    

*   一个 UI 断言
    

*   一个状态变化
    

*   一个浏览器动作
    

*   一个文件 diff 或 schema 校验
    

像 “代码优雅”“架构合理”“体验高级” 这类判断，不是不能做，而是不能只依靠自然语言去自动化收敛，至少在目前阶段还不够稳。

## 五、我做的框架，本质上已经是一个 Harness 雏形

我在这个仓库里做的并不是一个简单的脚本，而是一套很像 “最小可行 harness” 的系统。

框架骨架在 `scripts/ralph/ralph.py` 里。它做的事情很明确：

*   定义总迭代次数和超时
    

*   调用一个开发 agent
    

*   再调用一个验证 agent
    

*   通过 `prd.json` 追踪 story 状态
    

*   如果全部通过或被 block，就停止
    

*   否则继续下一轮
    

它不是让一个 agent 自己写、自己说 “我完成了”、然后继续往下跑，而是强制进入 `开发 -> 验证 -> 状态回写 -> 下一轮` 的闭环。

开发 agent 的工作手册在 `scripts/ralph/CLAUDE.md` 里。它要求 agent：

*   读取 `prd.json`
    

*   读取 `progress.txt`
    

*   检查是否在正确分支
    

*   选择最高优先级、尚未完成且未被 block 的 story
    

*   每次只做一个 story
    

*   跑质量检查
    

*   提交代码
    

*   更新 `passes`
    

*   把经验追加到 `progress.txt`
    

这里最有价值的一点，是它不只是让 agent 写代码，还让它把 “对未来迭代有帮助的模式” 沉淀下来，写进 `Codebase Patterns`。

验证 agent 的工作手册在 `scripts/ralph/VALIDATOR.md` 里。它要求 validator：

*   从 `progress.txt` 读取最后一条 story
    

*   回到 `prd.json` 找到该 story 的完整验收标准
    

*   逐条验收
    

*   如果失败，写回 `notes`
    

*   增加 `retryCount`
    

*   超过一定次数就 `blocked`
    

*   如果使用浏览器验证，还要保存截图到 `screenshots/`
    

这个设计非常关键。它把 “完成” 这个动作从开发 agent 手里拿走了，交给了独立验证层。

另外还有一个辅助可视化面板在 `scripts/ralph/dashboard.py` 和 `scripts/ralph/dashboard.html` 里，它让整个执行过程可观测。这一点常常被低估，但其实非常重要。自动化系统如果不可观测，就很难调试、很难建立信任。

换句话说，这个框架已经不是 “一个会调模型的脚本” 了，而是：

`一个用结构化任务、独立验证、状态回写、经验沉淀和可视化监控组成的最小 AI coding harness。`

## 六、真正重要的不是框架骨架，而是我已经把它跑通了一个真实项目

如果只看框架仓库 `auto_coding`，还只能说明 “设计方向成立”。真正让这件事有说服力的，是我又给出了一个完整样本 Demo 项目. 已经完全测试了 claude 和 codex 两个的接入.

这个项目不是空壳，它具备完整的自动化证据链：

*   有任务定义文件 `scripts/ralph/prd.json`
    

*   有执行日志和模式沉淀 `scripts/ralph/progress.txt`
    

*   有真实应用代码 `app/page.tsx`
    

*   有截图证据 `screenshots/`
    

*   有连续提交历史
    

*   有最终通过的 `lint`、`typecheck`
    

*   有构建产物 `out/`
    

这就意味着：我的系统不是 “理论上能跑”，而是 “已经在一个真实项目上跑出了结果”。

## 七、这个真实项目为什么具有证明力

这个项目是一个简易笔记系统，但它并不是只有静态页面。它包含了非常典型的产品交互与状态联动问题，而这些问题恰恰是 AI 自动 coding 最容易出错的地方。

这里 coding 2.0 的关键点一次性跑完之后, 不需要更大的模型修复, 直接可以使用.

### 1. Story 设计是结构化的

在 `scripts/ralph/prd.json` 里，整个项目被拆成了 9 个 story：

*   US-001 初始化项目结构与静态导出配置
    

*   US-002 定义 Note 类型与示例数据预加载
    

*   US-003 笔记列表组件
    

*   US-004 笔记详情展示
    

*   US-005 新建笔记
    

*   US-006 编辑笔记并实时保存
    

*   US-007 删除笔记
    

*   US-008 搜索过滤
    

*   US-009 数据重置
    

每个 story 都有：

*   标题
    

*   说明
    

*   验收标准
    

*   优先级
    

*   `passes`
    

*   `notes`
    

*   `retryCount`
    

*   `blocked`
    

这已经不是传统意义上的 PRD，而是一种 `machine-readable task contract`。

### 2. 验收标准足够具体

这些 story 的验收标准不是泛泛而谈，而是具体到：

*   使用 App Router
    

*   `output: 'export'`
    

*   左右两栏布局
    

*   默认选中第一条笔记
    

*   显示标题、预览、时间
    

*   高亮、hover transition
    

*   点击切换选中项
    

*   浏览器里验证点击效果
    

*   新建后自动聚焦
    

*   实时更新标题、内容、时间
    

*   删除时弹出原生 `confirm`
    

*   搜索范围覆盖标题和内容
    

*   重置时恢复示例数据并清空搜索框
    

这就是为什么它适合自动化。因为 “什么算通过” 被写得足够清楚了。

### 3. 应用代码体现了收敛，而不是拼凑

最终应用代码集中在 `app/page.tsx` 里。虽然是单文件实现，但逻辑上是自洽的。

它定义了 `Note` 类型和 `initialNotes`，有排序函数 `getSortedNotes`、时间格式化 `formatUpdatedAt`、预览截断 `getPreview`，还有一个用于实时更新笔记状态的 `updateNoteDraft`。

更重要的是它的状态组织：

*   `notes`
    

*   `selectedNoteId`
    

*   `draftTitle`
    

*   `draftContent`
    

*   `searchQuery`
    

*   `removingNoteId`
    

*   `titleInputRef`
    

*   `removalTimeoutRef`
    

*   `shouldFocusTitleRef`
    

围绕这些状态，又有几个关键 effect 和 handler：

*   在选中新笔记时自动聚焦标题输入框
    

*   在搜索过滤后，如果当前选中项不在过滤结果中，自动同步选中项和草稿内容
    

*   在组件卸载时清理删除动画的 timeout
    

*   新建笔记时先生成 note，再设置选中，再写入草稿，再触发聚焦
    

*   选择笔记时允许取消选中，从而出现空状态
    

*   编辑标题和内容时实时更新草稿和全局 notes
    

*   重置时一次性恢复 notes、selectedNoteId、draftTitle、draftContent、searchQuery
    

*   删除时先记录 `removingNoteId`，等待动画结束，再统一移除并切换选中项
    

这不是简单的 “功能堆砌”，而是一条很典型的受控状态流。

### 4. 样式和动效也被纳入了验收

全局样式在 `app/globals.css` 中定义，包括：

*   `note-detail-enter`
    

*   `note-card-removing`
    

*   进入动效
    

*   删除动效
    

这说明系统并不是只验证 “功能有了”，而是连部分交互质感也被纳入了目标。

## 八、最有价值的不是成功，而是 `progress.txt` 里的学习

很多自动化系统看起来也能做出东西，但最大的问题是：它不会变得更懂项目。我这个框架最值得重视的地方，恰恰是它在 `scripts/ralph/progress.txt` 里，把每一轮的经验沉淀成了未来的约束资产。

这个文件里的 `Codebase Patterns` 非常有代表性，比如：

*   App Router 入口在 `app/`
    

*   静态导出通过 `next.config.mjs` 里的 `output: 'export'`
    

*   ESLint 要忽略 `.next` 和 `out`
    

*   这个项目里 `typecheck` 前最好先 `build`
    

*   笔记列表的 preview 要先做空白归一化，再截断到 30 字
    

*   `next build` 后直接复用同一份 `.next` 跑 `next dev` 可能出错
    

*   新建笔记时要先创建状态，再设置选中，再通过 effect 做聚焦
    

*   草稿同步 effect 不要依赖整个 `notes`
    

*   删除动画期间要延迟真正删除，并同步更新 selection 和草稿
    

*   搜索过滤后如果选中项失效，要同步切换到第一条可见笔记
    

*   重置时要一次性恢复 notes、selected id、draft、searchQuery
    

这些内容非常关键。因为它们已经不是 “本轮做了什么” 的日志，而是 “下一轮 AI 应该知道什么” 的知识。

从 harness 的角度说，这一步比代码本身还重要。因为代码只解决了这一次，而模式沉淀在提高下一次的成功率。

## 九、所以，这件事到底靠不靠谱

`这件事是靠谱的，而且已经不是概念验证级别的靠谱，而是已经证明在一类真实项目上可运行、可收敛、可复盘的靠谱。`

但这个结论必须带边界，不然就会过度乐观。

### 已经被证明靠谱的部分

这套方法已经证明适合下面这类任务：

*   单仓库、中小型项目
    

*   前端或全栈中低复杂度功能
    

*   明确的 CRUD 和交互逻辑
    

*   可通过 build、lint、typecheck、browser 验收的需求
    

*   顺序依赖清晰的开发任务
    

*   风险可控的 story-by-story 交付
    

### 还没有被证明的部分

这套方法还不能直接外推到：

*   多服务、多仓库、跨系统联动
    

*   强后端事务一致性
    

*   复杂权限和安全模型
    

*   高度隐式的业务规则
    

*   大规模架构改造
    

*   重度产品判断和大量非功能性需求
    

也就是说，它现在已经是一个有效的方法，但还不是 “所有软件开发都可以这样自动做” 的最终答案。

## 十、这个样本也暴露了当前 harness 的几个不足

恰恰因为这个项目是真实跑出来的，所以它也暴露了系统目前最需要补强的地方。

### 1. 验证层还不够硬

虽然 validator 存在，也有截图证据，但很多验证仍然依赖 agent 自己理解 acceptance criteria，然后临场拼接验证动作。

例如在进度里能看到：

*   某一轮 browser tool 不可用，退化成手动复核
    

*   不同端口可能承载不同页面，验证前要确认是当前工作树
    

*   构建和 dev server 切换时会有环境问题
    

这些都说明闭环是成立的，但验证层还没有完全工程化。

(其实验证层还要进行再度的细分, 拆分成 linter、固定的单元测试. 程序话的测试等等)

### 2. 控制面还不够强

从提交历史可以看到：

*   有一个占位提交 `feat: [Story ID] - [Story Title]`
    

*   US-005 出现了两次提交
    

*   `screenshots/` 下有不少后来新增或修改的文件
    

这些都不是致命问题，但说明系统虽然能收敛，过程控制还不够硬。未来要规模化，必须进一步加强：

*   提交格式校验
    

*   story 去重保护
    

*   状态同步约束
    

*   环境锁定
    

*   验证结果结构化输出
    

### 3. 当前任务域相对友好

这个样本没有数据库、没有后端、没有权限系统，也没有复杂部署流程。这是很好的第一类样本，但还只是第一类样本。

## 十一、一个没有 Harness 的小团队，应该怎么逐步走到 AI 自动化 Coding

如果我是给一个小团队设计路线，不会建议一上来就做 “全自动 coding 平台”，而会建议按下面的阶段推进。

### 阶段一：先进入 Co-pilot 协作期

目标不是自动化，而是观察。

让 AI 参与真实开发，但人负责：

*   需求拆解
    

*   风险判断
    

*   最终验收
    

*   关键设计决策
    

这一阶段最重要的工作不是让 AI 写得快，而是记录它经常犯哪些错。

### 阶段二：把错误和经验资产化

开始沉淀：

*   开发规范
    

*   架构边界
    

*   命名和目录约束
    

*   环境启动方式
    

*   常见坑
    

*   回归风险
    

*   浏览器验证路径
    

*   已知可复用的 patterns
    

这一步可以先从文档开始，比如：

*   `AGENTS.md`
    

*   `patterns.md`
    

*   `runbook.md`
    

*   `pitfalls.md`
    

但文档一定要短，要像地图，不要像百科全书。

### 阶段三：把任务定义结构化

不要再用普通 PRD 驱动 AI，而是要做成 story schema。每个 story 至少包含：

*   ID
    

*   标题
    

*   描述
    

*   依赖
    

*   优先级
    

*   影响范围
    

*   验收标准
    

*   禁止修改区域
    

*   build/test/browser 验证方式
    

*   完成状态
    

*   重试状态
    

*   失败说明
    

也就是我在 `prd.json` 里已经开始做的事情。

### 阶段四：建立独立验证层

开发和验证必须分开。

不能让 “写代码的人自己说自己通过了”。至少要有：

*   build
    

*   lint
    

*   typecheck
    

*   unit/integration tests
    

*   browser 验证
    

*   截图
    

*   失败回写
    

这一步是从 “AI 会写代码” 走向 “AI 能交付” 的分水岭。

### 阶段五：把高频规则从文档升级成程序

只要某条规则高频出现，就应该机械化：

*   lint rule
    

*   schema validation
    

*   snapshot/golden test
    

*   browser assertion
    

*   CI gate
    

*   目录边界检查
    

*   命名约束
    

*   dependency boundary check
    

这是企业能不能规模化的关键。

### 阶段六：只在低风险任务池里放权

一开始不要追求所有任务都自动做。应该先限定在：

*   小功能
    

*   明确 bug 修复
    

*   测试补全
    

*   UI 对齐
    

*   低风险重构
    

*   文档同步
    

先把成功率最高的任务池打透，再逐步扩大范围。

### 阶段七：引入风险分层和治理

当团队开始依赖 AI 自动开发时，就必须考虑：

*   哪些任务可以自动合并
    

*   哪些任务必须人工审批
    

*   哪些目录禁止自动修改
    

*   哪些操作必须留痕
    

*   哪些错误可以自动重试
    

*   哪些错误必须人工接管
    

这时候，AI coding 才真正从 “工具” 变成“工程系统”。

## 十二、我这个框架的真正价值，不是 “自动写代码”，而是 “把工程知识组织起来”

如果只从表面看，Ralph 好像是一个自动写代码的循环器。  
但从更深的角度看，它真正有价值的地方，是在做这件事：

`把分散在人、代码、经验、验收、环境里的知识，逐步组织成一个 AI 可执行的工程系统。`

这也是为什么我认为自己走的方向是对的。

因为 AI 自动 coding 的核心竞争力，不是[[提示词]]写得多漂亮，而是：

*   任务定义是否结构化
    

*   规则是否清晰
    

*   项目是否 agent-friendly
    

*   验收是否自动化
    

*   失败是否可回写
    

*   经验是否可复用
    

*   环境是否可观察
    

*   权限是否可治理
    

而我现在做的框架，已经覆盖了这里面的相当一部分。

## 十三、最终结论

如果把整件事压缩成一句话，我会这样总结：

`不是先做 autonomous coding，再补规范；而是先通过 co-pilot 协作，把规范、边界、验收、环境和经验沉淀进 repo，再用 harness 把开发、验证、纠偏和学习串成闭环，最后才会出现真正可靠的 AI 自动化 coding。`

结合我自己的框架和真实样本，我的结论是：

*   这件事是靠谱的
    

*   方向是对的
    

*   我的系统已经不是概念，而是有真实落地的 harness 雏形
    

*   它已经证明适合一类中低复杂度项目
    

*   未来要走向企业级，还需要更强的 schema、更硬的 validator、更严格的 process control 和风险分层
    

换句话说，我现在已经跨过了最难的一步：  
我不再是在讨论 “AI 能不能自动 coding”，而是在讨论 “怎样把自动 coding 变成一个可治理、可验证、可规模化的工程系统”。

这才是正确的问题。

如果今天让一个小团队直接进入 “AI 自动写代码” 的状态，结果大概率不会太理想。问题通常不在于模型不够聪明，而在于团队还没有把自己的约束、经验、验收标准和工程边界组织成一个 AI 能稳定理解、稳定执行、稳定验证的系统。

这也是我读完 OpenAI 在 2026 年 2 月 11 日发布的 [Harness engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/) 后，结合我自己的框架与真实项目样本，得到的核心判断：真正重要的不是 “让 AI 更会写代码”，而是 “让工程环境本身变成一个可以约束、验证、纠偏 AI 的 harness”。

我正在研发自己的 AI 自动化 coding 2.0，这套思路其实已经非常接近这条路线的本质。我的判断是：先从人和 AI 的协作开发开始，把 AI 犯错、返工、不符合规范的地方沉淀成规则文件，再逐步把这些规则、经验、企业约束汇总成一张 “开发规范地图”，最后再结合任务拆解、验收标准、build、validate，让 AI 在这些约束下自动完成开发。这条逻辑不是空想，方向也是对的，而且我已经用自己的框架把它做成了一个有真实闭环的系统。

但如果要把这件事真正讲清楚，有几个关键点必须说透。

(今天是来补逻辑的, 哈哈, 思路有了, 后边我把源码放出来, 大家就更有收获了)

![](https://article-images.zsxq.com/Fitt7RWpEDE2PXcR7_rw4hUkfp3C)

  

## 一、Harness Engineering 讲的到底是什么

OpenAI 这篇文章里最重要的，不是某个单点技巧，而是一整套认识方式。

第一，`人类掌舵，智能体执行`。AI 不是工程负责人，它更像一个执行者。真正决定目标、边界、质量、风险、优先级的，仍然应该是人。

第二，`知识必须进入 repo`。如果团队的规范只存在于人的脑子里、微信群里、口头习惯里，AI 是吃不到的。只有当这些知识进入代码库，成为文件、配置、测试、脚本、文档，AI 才能把它们作为工作的依据。

第三，`AGENTS.md 不是百科全书，而是地图`。很多人会觉得 “我给 AI 写一本特别长的说明书，它就会做得更好”。实际恰恰相反。大而全的说明文档很快会过期，也很难被稳定执行。更有效的方式是：用一份短而清晰的索引文件，把 AI 指向正确的规则、正确的上下文、正确的工具。

第四，`文档不是终点，规则要尽量机械化`。如果某条规范经常被违反，那就不要永远停留在 “请遵守规范” 这个层面，而是要把它升级成 lint、test、schema 校验、浏览器断言、CI 检查。文档是软约束，代码化的检查才是硬约束。

第五，`自动化 coding 的前提不是自治，而是验证闭环`。如果没有 build、test、browser verification、日志、状态回写、失败重试、人工接管点，那么所谓 “自动化” 只是更快地产生错误。

这一套观点，和我正在做的事情，本质上是一致的。

## 二、我原始思路里最对的地方

我最重要的判断，是把 “自动化 coding” 的起点放在了 `co-pilot 协作阶段`，而不是一上来就追求完全自治。

这一步特别关键。因为真正可靠的约束，并不是拍脑袋设计出来的，而是从真实协作中的错误中长出来的。比如：

*   AI 改了一个功能，但忘了更新另一个联动状态
    

*   AI 通过了 typecheck，但浏览器点击无反应
    

*   AI 没遵守代码库已有模式
    

*   AI 为了完成局部目标，引入了全局回归
    

*   AI 在环境、端口、测试依赖上判断失误
    

如果这些问题只是 “当场修掉”，那经验很快就丢了。只有当我把它们沉淀下来，写成规则、写成模式、写成验证脚本，它们才会变成未来自动化的燃料。

这也是我为什么会坚持 “先有 copilot coding，再有资产沉淀，再走向自动化 coding” 这条路线。

## 三、但这里有一个必须修正的地方：约束不只是从错误里来

我的原始逻辑里有一个地方需要补强：我比较强调 “AI 做错了，我们就修，然后把规则沉淀下来”。这条路径没错，但不完整。

因为约束的来源不只有 “错误复盘”，还应该包括四类前置约束：

*   产品约束：什么算完成，什么体验不可接受
    

*   架构约束：哪些边界不能跨，哪些目录不能乱改，哪些层不能反向依赖
    

*   安全约束：哪些数据不能碰，哪些权限不能给，哪些操作必须审批
    

*   组织约束：提交方式、分支策略、review 规则、上线节奏、回滚方式
    

如果只从错误中长规则，那最后会得到一座 “事故博物馆”，而不是一套 “工程操作系统”。真正有效的 harness，应该是前置约束和后验经验一起构成的。

(就是说除了 AI 修正错误的一些沉淀, 还是需要人来把控一些约束的, 并且把约束也沉淀下来)

## 四、真正的核心不是 “拆得够细”，而是 “拆得可收敛”

我有一个很关键的判断：如果一个 PRD 可以拆得够细，又有验证标准，那就可以用框架自动化开发。

这句话大方向是对的，但更准确的表述应该是：

`不是 PRD 拆得够细就行，而是任务必须被拆成“可独立收敛的 story”，并且每个 story 的验收标准可以被稳定验证。`

这两个条件缺一不可。

### 1. 可独立收敛

一个 story 必须尽量满足：

*   边界清楚
    

*   依赖明确
    

*   影响范围可控
    

*   能单独实现
    

*   能单独验证
    

如果 story 之间强耦合、顺序混乱、共享很多隐式状态，那么就算写得很细，也不一定适合自动化。

### 2. 验收标准可验证

验收标准必须尽量具体，最好能映射成：

*   一个命令
    

*   一个构建结果
    

*   一个 UI 断言
    

*   一个状态变化
    

*   一个浏览器动作
    

*   一个文件 diff 或 schema 校验
    

像 “代码优雅”“架构合理”“体验高级” 这类判断，不是不能做，而是不能只依靠自然语言去自动化收敛，至少在目前阶段还不够稳。

## 五、我做的框架，本质上已经是一个 Harness 雏形

我在这个仓库里做的并不是一个简单的脚本，而是一套很像 “最小可行 harness” 的系统。

框架骨架在 `scripts/ralph/ralph.py` 里。它做的事情很明确：

*   定义总迭代次数和超时
    

*   调用一个开发 agent
    

*   再调用一个验证 agent
    

*   通过 `prd.json` 追踪 story 状态
    

*   如果全部通过或被 block，就停止
    

*   否则继续下一轮
    

它不是让一个 agent 自己写、自己说 “我完成了”、然后继续往下跑，而是强制进入 `开发 -> 验证 -> 状态回写 -> 下一轮` 的闭环。

开发 agent 的工作手册在 `scripts/ralph/CLAUDE.md` 里。它要求 agent：

*   读取 `prd.json`
    

*   读取 `progress.txt`
    

*   检查是否在正确分支
    

*   选择最高优先级、尚未完成且未被 block 的 story
    

*   每次只做一个 story
    

*   跑质量检查
    

*   提交代码
    

*   更新 `passes`
    

*   把经验追加到 `progress.txt`
    

这里最有价值的一点，是它不只是让 agent 写代码，还让它把 “对未来迭代有帮助的模式” 沉淀下来，写进 `Codebase Patterns`。

验证 agent 的工作手册在 `scripts/ralph/VALIDATOR.md` 里。它要求 validator：

*   从 `progress.txt` 读取最后一条 story
    

*   回到 `prd.json` 找到该 story 的完整验收标准
    

*   逐条验收
    

*   如果失败，写回 `notes`
    

*   增加 `retryCount`
    

*   超过一定次数就 `blocked`
    

*   如果使用浏览器验证，还要保存截图到 `screenshots/`
    

这个设计非常关键。它把 “完成” 这个动作从开发 agent 手里拿走了，交给了独立验证层。

另外还有一个辅助可视化面板在 `scripts/ralph/dashboard.py` 和 `scripts/ralph/dashboard.html` 里，它让整个执行过程可观测。这一点常常被低估，但其实非常重要。自动化系统如果不可观测，就很难调试、很难建立信任。

换句话说，这个框架已经不是 “一个会调模型的脚本” 了，而是：

`一个用结构化任务、独立验证、状态回写、经验沉淀和可视化监控组成的最小 AI coding harness。`

## 六、真正重要的不是框架骨架，而是我已经把它跑通了一个真实项目

如果只看框架仓库 `auto_coding`，还只能说明 “设计方向成立”。真正让这件事有说服力的，是我又给出了一个完整样本 Demo 项目. 已经完全测试了 claude 和 codex 两个的接入.

这个项目不是空壳，它具备完整的自动化证据链：

*   有任务定义文件 `scripts/ralph/prd.json`
    

*   有执行日志和模式沉淀 `scripts/ralph/progress.txt`
    

*   有真实应用代码 `app/page.tsx`
    

*   有截图证据 `screenshots/`
    

*   有连续提交历史
    

*   有最终通过的 `lint`、`typecheck`
    

*   有构建产物 `out/`
    

这就意味着：我的系统不是 “理论上能跑”，而是 “已经在一个真实项目上跑出了结果”。

## 七、这个真实项目为什么具有证明力

这个项目是一个简易笔记系统，但它并不是只有静态页面。它包含了非常典型的产品交互与状态联动问题，而这些问题恰恰是 AI 自动 coding 最容易出错的地方。

这里 coding 2.0 的关键点一次性跑完之后, 不需要更大的模型修复, 直接可以使用.

### 1. Story 设计是结构化的

在 `scripts/ralph/prd.json` 里，整个项目被拆成了 9 个 story：

*   US-001 初始化项目结构与静态导出配置
    

*   US-002 定义 Note 类型与示例数据预加载
    

*   US-003 笔记列表组件
    

*   US-004 笔记详情展示
    

*   US-005 新建笔记
    

*   US-006 编辑笔记并实时保存
    

*   US-007 删除笔记
    

*   US-008 搜索过滤
    

*   US-009 数据重置
    

每个 story 都有：

*   标题
    

*   说明
    

*   验收标准
    

*   优先级
    

*   `passes`
    

*   `notes`
    

*   `retryCount`
    

*   `blocked`
    

这已经不是传统意义上的 PRD，而是一种 `machine-readable task contract`。

### 2. 验收标准足够具体

这些 story 的验收标准不是泛泛而谈，而是具体到：

*   使用 App Router
    

*   `output: 'export'`
    

*   左右两栏布局
    

*   默认选中第一条笔记
    

*   显示标题、预览、时间
    

*   高亮、hover transition
    

*   点击切换选中项
    

*   浏览器里验证点击效果
    

*   新建后自动聚焦
    

*   实时更新标题、内容、时间
    

*   删除时弹出原生 `confirm`
    

*   搜索范围覆盖标题和内容
    

*   重置时恢复示例数据并清空搜索框
    

这就是为什么它适合自动化。因为 “什么算通过” 被写得足够清楚了。

### 3. 应用代码体现了收敛，而不是拼凑

最终应用代码集中在 `app/page.tsx` 里。虽然是单文件实现，但逻辑上是自洽的。

它定义了 `Note` 类型和 `initialNotes`，有排序函数 `getSortedNotes`、时间格式化 `formatUpdatedAt`、预览截断 `getPreview`，还有一个用于实时更新笔记状态的 `updateNoteDraft`。

更重要的是它的状态组织：

*   `notes`
    

*   `selectedNoteId`
    

*   `draftTitle`
    

*   `draftContent`
    

*   `searchQuery`
    

*   `removingNoteId`
    

*   `titleInputRef`
    

*   `removalTimeoutRef`
    

*   `shouldFocusTitleRef`
    

围绕这些状态，又有几个关键 effect 和 handler：

*   在选中新笔记时自动聚焦标题输入框
    

*   在搜索过滤后，如果当前选中项不在过滤结果中，自动同步选中项和草稿内容
    

*   在组件卸载时清理删除动画的 timeout
    

*   新建笔记时先生成 note，再设置选中，再写入草稿，再触发聚焦
    

*   选择笔记时允许取消选中，从而出现空状态
    

*   编辑标题和内容时实时更新草稿和全局 notes
    

*   重置时一次性恢复 notes、selectedNoteId、draftTitle、draftContent、searchQuery
    

*   删除时先记录 `removingNoteId`，等待动画结束，再统一移除并切换选中项
    

这不是简单的 “功能堆砌”，而是一条很典型的受控状态流。

### 4. 样式和动效也被纳入了验收

全局样式在 `app/globals.css` 中定义，包括：

*   `note-detail-enter`
    

*   `note-card-removing`
    

*   进入动效
    

*   删除动效
    

这说明系统并不是只验证 “功能有了”，而是连部分交互质感也被纳入了目标。

## 八、最有价值的不是成功，而是 `progress.txt` 里的学习

很多自动化系统看起来也能做出东西，但最大的问题是：它不会变得更懂项目。我这个框架最值得重视的地方，恰恰是它在 `scripts/ralph/progress.txt` 里，把每一轮的经验沉淀成了未来的约束资产。

这个文件里的 `Codebase Patterns` 非常有代表性，比如：

*   App Router 入口在 `app/`
    

*   静态导出通过 `next.config.mjs` 里的 `output: 'export'`
    

*   ESLint 要忽略 `.next` 和 `out`
    

*   这个项目里 `typecheck` 前最好先 `build`
    

*   笔记列表的 preview 要先做空白归一化，再截断到 30 字
    

*   `next build` 后直接复用同一份 `.next` 跑 `next dev` 可能出错
    

*   新建笔记时要先创建状态，再设置选中，再通过 effect 做聚焦
    

*   草稿同步 effect 不要依赖整个 `notes`
    

*   删除动画期间要延迟真正删除，并同步更新 selection 和草稿
    

*   搜索过滤后如果选中项失效，要同步切换到第一条可见笔记
    

*   重置时要一次性恢复 notes、selected id、draft、searchQuery
    

这些内容非常关键。因为它们已经不是 “本轮做了什么” 的日志，而是 “下一轮 AI 应该知道什么” 的知识。

从 harness 的角度说，这一步比代码本身还重要。因为代码只解决了这一次，而模式沉淀在提高下一次的成功率。

## 九、所以，这件事到底靠不靠谱

`这件事是靠谱的，而且已经不是概念验证级别的靠谱，而是已经证明在一类真实项目上可运行、可收敛、可复盘的靠谱。`

但这个结论必须带边界，不然就会过度乐观。

### 已经被证明靠谱的部分

这套方法已经证明适合下面这类任务：

*   单仓库、中小型项目
    

*   前端或全栈中低复杂度功能
    

*   明确的 CRUD 和交互逻辑
    

*   可通过 build、lint、typecheck、browser 验收的需求
    

*   顺序依赖清晰的开发任务
    

*   风险可控的 story-by-story 交付
    

### 还没有被证明的部分

这套方法还不能直接外推到：

*   多服务、多仓库、跨系统联动
    

*   强后端事务一致性
    

*   复杂权限和安全模型
    

*   高度隐式的业务规则
    

*   大规模架构改造
    

*   重度产品判断和大量非功能性需求
    

也就是说，它现在已经是一个有效的方法，但还不是 “所有软件开发都可以这样自动做” 的最终答案。

## 十、这个样本也暴露了当前 harness 的几个不足

恰恰因为这个项目是真实跑出来的，所以它也暴露了系统目前最需要补强的地方。

### 1. 验证层还不够硬

虽然 validator 存在，也有截图证据，但很多验证仍然依赖 agent 自己理解 acceptance criteria，然后临场拼接验证动作。

例如在进度里能看到：

*   某一轮 browser tool 不可用，退化成手动复核
    

*   不同端口可能承载不同页面，验证前要确认是当前工作树
    

*   构建和 dev server 切换时会有环境问题
    

这些都说明闭环是成立的，但验证层还没有完全工程化。

(其实验证层还要进行再度的细分, 拆分成 linter、固定的单元测试. 程序话的测试等等)

### 2. 控制面还不够强

从提交历史可以看到：

*   有一个占位提交 `feat: [Story ID] - [Story Title]`
    

*   US-005 出现了两次提交
    

*   `screenshots/` 下有不少后来新增或修改的文件
    

这些都不是致命问题，但说明系统虽然能收敛，过程控制还不够硬。未来要规模化，必须进一步加强：

*   提交格式校验
    

*   story 去重保护
    

*   状态同步约束
    

*   环境锁定
    

*   验证结果结构化输出
    

### 3. 当前任务域相对友好

这个样本没有数据库、没有后端、没有权限系统，也没有复杂部署流程。这是很好的第一类样本，但还只是第一类样本。

## 十一、一个没有 Harness 的小团队，应该怎么逐步走到 AI 自动化 Coding

如果我是给一个小团队设计路线，不会建议一上来就做 “全自动 coding 平台”，而会建议按下面的阶段推进。

### 阶段一：先进入 Co-pilot 协作期

目标不是自动化，而是观察。

让 AI 参与真实开发，但人负责：

*   需求拆解
    

*   风险判断
    

*   最终验收
    

*   关键设计决策
    

这一阶段最重要的工作不是让 AI 写得快，而是记录它经常犯哪些错。

### 阶段二：把错误和经验资产化

开始沉淀：

*   开发规范
    

*   架构边界
    

*   命名和目录约束
    

*   环境启动方式
    

*   常见坑
    

*   回归风险
    

*   浏览器验证路径
    

*   已知可复用的 patterns
    

这一步可以先从文档开始，比如：

*   `AGENTS.md`
    

*   `patterns.md`
    

*   `runbook.md`
    

*   `pitfalls.md`
    

但文档一定要短，要像地图，不要像百科全书。

### 阶段三：把任务定义结构化

不要再用普通 PRD 驱动 AI，而是要做成 story schema。每个 story 至少包含：

*   ID
    

*   标题
    

*   描述
    

*   依赖
    

*   优先级
    

*   影响范围
    

*   验收标准
    

*   禁止修改区域
    

*   build/test/browser 验证方式
    

*   完成状态
    

*   重试状态
    

*   失败说明
    

也就是我在 `prd.json` 里已经开始做的事情。

### 阶段四：建立独立验证层

开发和验证必须分开。

不能让 “写代码的人自己说自己通过了”。至少要有：

*   build
    

*   lint
    

*   typecheck
    

*   unit/integration tests
    

*   browser 验证
    

*   截图
    

*   失败回写
    

这一步是从 “AI 会写代码” 走向 “AI 能交付” 的分水岭。

### 阶段五：把高频规则从文档升级成程序

只要某条规则高频出现，就应该机械化：

*   lint rule
    

*   schema validation
    

*   snapshot/golden test
    

*   browser assertion
    

*   CI gate
    

*   目录边界检查
    

*   命名约束
    

*   dependency boundary check
    

这是企业能不能规模化的关键。

### 阶段六：只在低风险任务池里放权

一开始不要追求所有任务都自动做。应该先限定在：

*   小功能
    

*   明确 bug 修复
    

*   测试补全
    

*   UI 对齐
    

*   低风险重构
    

*   文档同步
    

先把成功率最高的任务池打透，再逐步扩大范围。

### 阶段七：引入风险分层和治理

当团队开始依赖 AI 自动开发时，就必须考虑：

*   哪些任务可以自动合并
    

*   哪些任务必须人工审批
    

*   哪些目录禁止自动修改
    

*   哪些操作必须留痕
    

*   哪些错误可以自动重试
    

*   哪些错误必须人工接管
    

这时候，AI coding 才真正从 “工具” 变成“工程系统”。

## 十二、我这个框架的真正价值，不是 “自动写代码”，而是 “把工程知识组织起来”

如果只从表面看，Ralph 好像是一个自动写代码的循环器。  
但从更深的角度看，它真正有价值的地方，是在做这件事：

`把分散在人、代码、经验、验收、环境里的知识，逐步组织成一个 AI 可执行的工程系统。`

这也是为什么我认为自己走的方向是对的。

因为 AI 自动 coding 的核心竞争力，不是提示词写得多漂亮，而是：

*   任务定义是否结构化
    

*   规则是否清晰
    

*   项目是否 agent-friendly
    

*   验收是否自动化
    

*   失败是否可回写
    

*   经验是否可复用
    

*   环境是否可观察
    

*   权限是否可治理
    

而我现在做的框架，已经覆盖了这里面的相当一部分。

## 十三、最终结论

如果把整件事压缩成一句话，我会这样总结：

`不是先做 autonomous coding，再补规范；而是先通过 co-pilot 协作，把规范、边界、验收、环境和经验沉淀进 repo，再用 harness 把开发、验证、纠偏和学习串成闭环，最后才会出现真正可靠的 AI 自动化 coding。`

结合我自己的框架和真实样本，我的结论是：

*   这件事是靠谱的
    

*   方向是对的
    

*   我的系统已经不是概念，而是有真实落地的 harness 雏形
    

*   它已经证明适合一类中低复杂度项目
    

*   未来要走向企业级，还需要更强的 schema、更硬的 validator、更严格的 process control 和风险分层
    

换句话说，我现在已经跨过了最难的一步：  
我不再是在讨论 “AI 能不能自动 coding”，而是在讨论 “怎样把自动 coding 变成一个可治理、可验证、可规模化的工程系统”。

这才是正确的问题。

如果今天让一个小团队直接进入 “AI 自动写代码” 的状态，结果大概率不会太理想。问题通常不在于模型不够聪明，而在于团队还没有把自己的约束、经验、验收标准和工程边界组织成一个 AI 能稳定理解、稳定执行、稳定验证的系统。

这也是我读完 OpenAI 在 2026 年 2 月 11 日发布的 [Harness engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/) 后，结合我自己的框架与真实项目样本，得到的核心判断：真正重要的不是 “让 AI 更会写代码”，而是 “让工程环境本身变成一个可以约束、验证、纠偏 AI 的 harness”。

我正在研发自己的 AI 自动化 coding 2.0，这套思路其实已经非常接近这条路线的本质。我的判断是：先从人和 AI 的协作开发开始，把 AI 犯错、返工、不符合规范的地方沉淀成规则文件，再逐步把这些规则、经验、企业约束汇总成一张 “开发规范地图”，最后再结合任务拆解、验收标准、build、validate，让 AI 在这些约束下自动完成开发。这条逻辑不是空想，方向也是对的，而且我已经用自己的框架把它做成了一个有真实闭环的系统。

但如果要把这件事真正讲清楚，有几个关键点必须说透。

(今天是来补逻辑的, 哈哈, 思路有了, 后边我把源码放出来, 大家就更有收获了)

![](https://article-images.zsxq.com/Fitt7RWpEDE2PXcR7_rw4hUkfp3C)

  

## 一、Harness Engineering 讲的到底是什么

OpenAI 这篇文章里最重要的，不是某个单点技巧，而是一整套认识方式。

第一，`人类掌舵，智能体执行`。AI 不是工程负责人，它更像一个执行者。真正决定目标、边界、质量、风险、优先级的，仍然应该是人。

第二，`知识必须进入 repo`。如果团队的规范只存在于人的脑子里、微信群里、口头习惯里，AI 是吃不到的。只有当这些知识进入代码库，成为文件、配置、测试、脚本、文档，AI 才能把它们作为工作的依据。

第三，`AGENTS.md 不是百科全书，而是地图`。很多人会觉得 “我给 AI 写一本特别长的说明书，它就会做得更好”。实际恰恰相反。大而全的说明文档很快会过期，也很难被稳定执行。更有效的方式是：用一份短而清晰的索引文件，把 AI 指向正确的规则、正确的上下文、正确的工具。

第四，`文档不是终点，规则要尽量机械化`。如果某条规范经常被违反，那就不要永远停留在 “请遵守规范” 这个层面，而是要把它升级成 lint、test、schema 校验、浏览器断言、CI 检查。文档是软约束，代码化的检查才是硬约束。

第五，`自动化 coding 的前提不是自治，而是验证闭环`。如果没有 build、test、browser verification、日志、状态回写、失败重试、人工接管点，那么所谓 “自动化” 只是更快地产生错误。

这一套观点，和我正在做的事情，本质上是一致的。

## 二、我原始思路里最对的地方

我最重要的判断，是把 “自动化 coding” 的起点放在了 `co-pilot 协作阶段`，而不是一上来就追求完全自治。

这一步特别关键。因为真正可靠的约束，并不是拍脑袋设计出来的，而是从真实协作中的错误中长出来的。比如：

*   AI 改了一个功能，但忘了更新另一个联动状态
    

*   AI 通过了 typecheck，但浏览器点击无反应
    

*   AI 没遵守代码库已有模式
    

*   AI 为了完成局部目标，引入了全局回归
    

*   AI 在环境、端口、测试依赖上判断失误
    

如果这些问题只是 “当场修掉”，那经验很快就丢了。只有当我把它们沉淀下来，写成规则、写成模式、写成验证脚本，它们才会变成未来自动化的燃料。

这也是我为什么会坚持 “先有 copilot coding，再有资产沉淀，再走向自动化 coding” 这条路线。

## 三、但这里有一个必须修正的地方：约束不只是从错误里来

我的原始逻辑里有一个地方需要补强：我比较强调 “AI 做错了，我们就修，然后把规则沉淀下来”。这条路径没错，但不完整。

因为约束的来源不只有 “错误复盘”，还应该包括四类前置约束：

*   产品约束：什么算完成，什么体验不可接受
    

*   架构约束：哪些边界不能跨，哪些目录不能乱改，哪些层不能反向依赖
    

*   安全约束：哪些数据不能碰，哪些权限不能给，哪些操作必须审批
    

*   组织约束：提交方式、分支策略、review 规则、上线节奏、回滚方式
    

如果只从错误中长规则，那最后会得到一座 “事故博物馆”，而不是一套 “工程操作系统”。真正有效的 harness，应该是前置约束和后验经验一起构成的。

(就是说除了 AI 修正错误的一些沉淀, 还是需要人来把控一些约束的, 并且把约束也沉淀下来)

## 四、真正的核心不是 “拆得够细”，而是 “拆得可收敛”

我有一个很关键的判断：如果一个 PRD 可以拆得够细，又有验证标准，那就可以用框架自动化开发。

这句话大方向是对的，但更准确的表述应该是：

`不是 PRD 拆得够细就行，而是任务必须被拆成“可独立收敛的 story”，并且每个 story 的验收标准可以被稳定验证。`

这两个条件缺一不可。

### 1. 可独立收敛

一个 story 必须尽量满足：

*   边界清楚
    

*   依赖明确
    

*   影响范围可控
    

*   能单独实现
    

*   能单独验证
    

如果 story 之间强耦合、顺序混乱、共享很多隐式状态，那么就算写得很细，也不一定适合自动化。

### 2. 验收标准可验证

验收标准必须尽量具体，最好能映射成：

*   一个命令
    

*   一个构建结果
    

*   一个 UI 断言
    

*   一个状态变化
    

*   一个浏览器动作
    

*   一个文件 diff 或 schema 校验
    

像 “代码优雅”“架构合理”“体验高级” 这类判断，不是不能做，而是不能只依靠自然语言去自动化收敛，至少在目前阶段还不够稳。

## 五、我做的框架，本质上已经是一个 Harness 雏形

我在这个仓库里做的并不是一个简单的脚本，而是一套很像 “最小可行 harness” 的系统。

框架骨架在 `scripts/ralph/ralph.py` 里。它做的事情很明确：

*   定义总迭代次数和超时
    

*   调用一个开发 agent
    

*   再调用一个验证 agent
    

*   通过 `prd.json` 追踪 story 状态
    

*   如果全部通过或被 block，就停止
    

*   否则继续下一轮
    

它不是让一个 agent 自己写、自己说 “我完成了”、然后继续往下跑，而是强制进入 `开发 -> 验证 -> 状态回写 -> 下一轮` 的闭环。

开发 agent 的工作手册在 `scripts/ralph/CLAUDE.md` 里。它要求 agent：

*   读取 `prd.json`
    

*   读取 `progress.txt`
    

*   检查是否在正确分支
    

*   选择最高优先级、尚未完成且未被 block 的 story
    

*   每次只做一个 story
    

*   跑质量检查
    

*   提交代码
    

*   更新 `passes`
    

*   把经验追加到 `progress.txt`
    

这里最有价值的一点，是它不只是让 agent 写代码，还让它把 “对未来迭代有帮助的模式” 沉淀下来，写进 `Codebase Patterns`。

验证 agent 的工作手册在 `scripts/ralph/VALIDATOR.md` 里。它要求 validator：

*   从 `progress.txt` 读取最后一条 story
    

*   回到 `prd.json` 找到该 story 的完整验收标准
    

*   逐条验收
    

*   如果失败，写回 `notes`
    

*   增加 `retryCount`
    

*   超过一定次数就 `blocked`
    

*   如果使用浏览器验证，还要保存截图到 `screenshots/`
    

这个设计非常关键。它把 “完成” 这个动作从开发 agent 手里拿走了，交给了独立验证层。

另外还有一个辅助可视化面板在 `scripts/ralph/dashboard.py` 和 `scripts/ralph/dashboard.html` 里，它让整个执行过程可观测。这一点常常被低估，但其实非常重要。自动化系统如果不可观测，就很难调试、很难建立信任。

换句话说，这个框架已经不是 “一个会调模型的脚本” 了，而是：

`一个用结构化任务、独立验证、状态回写、经验沉淀和可视化监控组成的最小 AI coding harness。`

## 六、真正重要的不是框架骨架，而是我已经把它跑通了一个真实项目

如果只看框架仓库 `auto_coding`，还只能说明 “设计方向成立”。真正让这件事有说服力的，是我又给出了一个完整样本 Demo 项目. 已经完全测试了 claude 和 codex 两个的接入.

这个项目不是空壳，它具备完整的自动化证据链：

*   有任务定义文件 `scripts/ralph/prd.json`
    

*   有执行日志和模式沉淀 `scripts/ralph/progress.txt`
    

*   有真实应用代码 `app/page.tsx`
    

*   有截图证据 `screenshots/`
    

*   有连续提交历史
    

*   有最终通过的 `lint`、`typecheck`
    

*   有构建产物 `out/`
    

这就意味着：我的系统不是 “理论上能跑”，而是 “已经在一个真实项目上跑出了结果”。

## 七、这个真实项目为什么具有证明力

这个项目是一个简易笔记系统，但它并不是只有静态页面。它包含了非常典型的产品交互与状态联动问题，而这些问题恰恰是 AI 自动 coding 最容易出错的地方。

这里 coding 2.0 的关键点一次性跑完之后, 不需要更大的模型修复, 直接可以使用.

### 1. Story 设计是结构化的

在 `scripts/ralph/prd.json` 里，整个项目被拆成了 9 个 story：

*   US-001 初始化项目结构与静态导出配置
    

*   US-002 定义 Note 类型与示例数据预加载
    

*   US-003 笔记列表组件
    

*   US-004 笔记详情展示
    

*   US-005 新建笔记
    

*   US-006 编辑笔记并实时保存
    

*   US-007 删除笔记
    

*   US-008 搜索过滤
    

*   US-009 数据重置
    

每个 story 都有：

*   标题
    

*   说明
    

*   验收标准
    

*   优先级
    

*   `passes`
    

*   `notes`
    

*   `retryCount`
    

*   `blocked`
    

这已经不是传统意义上的 PRD，而是一种 `machine-readable task contract`。

### 2. 验收标准足够具体

这些 story 的验收标准不是泛泛而谈，而是具体到：

*   使用 App Router
    

*   `output: 'export'`
    

*   左右两栏布局
    

*   默认选中第一条笔记
    

*   显示标题、预览、时间
    

*   高亮、hover transition
    

*   点击切换选中项
    

*   浏览器里验证点击效果
    

*   新建后自动聚焦
    

*   实时更新标题、内容、时间
    

*   删除时弹出原生 `confirm`
    

*   搜索范围覆盖标题和内容
    

*   重置时恢复示例数据并清空搜索框
    

这就是为什么它适合自动化。因为 “什么算通过” 被写得足够清楚了。

### 3. 应用代码体现了收敛，而不是拼凑

最终应用代码集中在 `app/page.tsx` 里。虽然是单文件实现，但逻辑上是自洽的。

它定义了 `Note` 类型和 `initialNotes`，有排序函数 `getSortedNotes`、时间格式化 `formatUpdatedAt`、预览截断 `getPreview`，还有一个用于实时更新笔记状态的 `updateNoteDraft`。

更重要的是它的状态组织：

*   `notes`
    

*   `selectedNoteId`
    

*   `draftTitle`
    

*   `draftContent`
    

*   `searchQuery`
    

*   `removingNoteId`
    

*   `titleInputRef`
    

*   `removalTimeoutRef`
    

*   `shouldFocusTitleRef`
    

围绕这些状态，又有几个关键 effect 和 handler：

*   在选中新笔记时自动聚焦标题输入框
    

*   在搜索过滤后，如果当前选中项不在过滤结果中，自动同步选中项和草稿内容
    

*   在组件卸载时清理删除动画的 timeout
    

*   新建笔记时先生成 note，再设置选中，再写入草稿，再触发聚焦
    

*   选择笔记时允许取消选中，从而出现空状态
    

*   编辑标题和内容时实时更新草稿和全局 notes
    

*   重置时一次性恢复 notes、selectedNoteId、draftTitle、draftContent、searchQuery
    

*   删除时先记录 `removingNoteId`，等待动画结束，再统一移除并切换选中项
    

这不是简单的 “功能堆砌”，而是一条很典型的受控状态流。

### 4. 样式和动效也被纳入了验收

全局样式在 `app/globals.css` 中定义，包括：

*   `note-detail-enter`
    

*   `note-card-removing`
    

*   进入动效
    

*   删除动效
    

这说明系统并不是只验证 “功能有了”，而是连部分交互质感也被纳入了目标。

## 八、最有价值的不是成功，而是 `progress.txt` 里的学习

很多自动化系统看起来也能做出东西，但最大的问题是：它不会变得更懂项目。我这个框架最值得重视的地方，恰恰是它在 `scripts/ralph/progress.txt` 里，把每一轮的经验沉淀成了未来的约束资产。

这个文件里的 `Codebase Patterns` 非常有代表性，比如：

*   App Router 入口在 `app/`
    

*   静态导出通过 `next.config.mjs` 里的 `output: 'export'`
    

*   ESLint 要忽略 `.next` 和 `out`
    

*   这个项目里 `typecheck` 前最好先 `build`
    

*   笔记列表的 preview 要先做空白归一化，再截断到 30 字
    

*   `next build` 后直接复用同一份 `.next` 跑 `next dev` 可能出错
    

*   新建笔记时要先创建状态，再设置选中，再通过 effect 做聚焦
    

*   草稿同步 effect 不要依赖整个 `notes`
    

*   删除动画期间要延迟真正删除，并同步更新 selection 和草稿
    

*   搜索过滤后如果选中项失效，要同步切换到第一条可见笔记
    

*   重置时要一次性恢复 notes、selected id、draft、searchQuery
    

这些内容非常关键。因为它们已经不是 “本轮做了什么” 的日志，而是 “下一轮 AI 应该知道什么” 的知识。

从 harness 的角度说，这一步比代码本身还重要。因为代码只解决了这一次，而模式沉淀在提高下一次的成功率。

## 九、所以，这件事到底靠不靠谱

`这件事是靠谱的，而且已经不是概念验证级别的靠谱，而是已经证明在一类真实项目上可运行、可收敛、可复盘的靠谱。`

但这个结论必须带边界，不然就会过度乐观。

### 已经被证明靠谱的部分

这套方法已经证明适合下面这类任务：

*   单仓库、中小型项目
    

*   前端或全栈中低复杂度功能
    

*   明确的 CRUD 和交互逻辑
    

*   可通过 build、lint、typecheck、browser 验收的需求
    

*   顺序依赖清晰的开发任务
    

*   风险可控的 story-by-story 交付
    

### 还没有被证明的部分

这套方法还不能直接外推到：

*   多服务、多仓库、跨系统联动
    

*   强后端事务一致性
    

*   复杂权限和安全模型
    

*   高度隐式的业务规则
    

*   大规模架构改造
    

*   重度产品判断和大量非功能性需求
    

也就是说，它现在已经是一个有效的方法，但还不是 “所有软件开发都可以这样自动做” 的最终答案。

## 十、这个样本也暴露了当前 harness 的几个不足

恰恰因为这个项目是真实跑出来的，所以它也暴露了系统目前最需要补强的地方。

### 1. 验证层还不够硬

虽然 validator 存在，也有截图证据，但很多验证仍然依赖 agent 自己理解 acceptance criteria，然后临场拼接验证动作。

例如在进度里能看到：

*   某一轮 browser tool 不可用，退化成手动复核
    

*   不同端口可能承载不同页面，验证前要确认是当前工作树
    

*   构建和 dev server 切换时会有环境问题
    

这些都说明闭环是成立的，但验证层还没有完全工程化。

(其实验证层还要进行再度的细分, 拆分成 linter、固定的单元测试. 程序话的测试等等)

### 2. 控制面还不够强

从提交历史可以看到：

*   有一个占位提交 `feat: [Story ID] - [Story Title]`
    

*   US-005 出现了两次提交
    

*   `screenshots/` 下有不少后来新增或修改的文件
    

这些都不是致命问题，但说明系统虽然能收敛，过程控制还不够硬。未来要规模化，必须进一步加强：

*   提交格式校验
    

*   story 去重保护
    

*   状态同步约束
    

*   环境锁定
    

*   验证结果结构化输出
    

### 3. 当前任务域相对友好

这个样本没有数据库、没有后端、没有权限系统，也没有复杂部署流程。这是很好的第一类样本，但还只是第一类样本。

## 十一、一个没有 Harness 的小团队，应该怎么逐步走到 AI 自动化 Coding

如果我是给一个小团队设计路线，不会建议一上来就做 “全自动 coding 平台”，而会建议按下面的阶段推进。

### 阶段一：先进入 Co-pilot 协作期

目标不是自动化，而是观察。

让 AI 参与真实开发，但人负责：

*   需求拆解
    

*   风险判断
    

*   最终验收
    

*   关键设计决策
    

这一阶段最重要的工作不是让 AI 写得快，而是记录它经常犯哪些错。

### 阶段二：把错误和经验资产化

开始沉淀：

*   开发规范
    

*   架构边界
    

*   命名和目录约束
    

*   环境启动方式
    

*   常见坑
    

*   回归风险
    

*   浏览器验证路径
    

*   已知可复用的 patterns
    

这一步可以先从文档开始，比如：

*   `AGENTS.md`
    

*   `patterns.md`
    

*   `runbook.md`
    

*   `pitfalls.md`
    

但文档一定要短，要像地图，不要像百科全书。

### 阶段三：把任务定义结构化

不要再用普通 PRD 驱动 AI，而是要做成 story schema。每个 story 至少包含：

*   ID
    

*   标题
    

*   描述
    

*   依赖
    

*   优先级
    

*   影响范围
    

*   验收标准
    

*   禁止修改区域
    

*   build/test/browser 验证方式
    

*   完成状态
    

*   重试状态
    

*   失败说明
    

也就是我在 `prd.json` 里已经开始做的事情。

### 阶段四：建立独立验证层

开发和验证必须分开。

不能让 “写代码的人自己说自己通过了”。至少要有：

*   build
    

*   lint
    

*   typecheck
    

*   unit/integration tests
    

*   browser 验证
    

*   截图
    

*   失败回写
    

这一步是从 “AI 会写代码” 走向 “AI 能交付” 的分水岭。

### 阶段五：把高频规则从文档升级成程序

只要某条规则高频出现，就应该机械化：

*   lint rule
    

*   schema validation
    

*   snapshot/golden test
    

*   browser assertion
    

*   CI gate
    

*   目录边界检查
    

*   命名约束
    

*   dependency boundary check
    

这是企业能不能规模化的关键。

### 阶段六：只在低风险任务池里放权

一开始不要追求所有任务都自动做。应该先限定在：

*   小功能
    

*   明确 bug 修复
    

*   测试补全
    

*   UI 对齐
    

*   低风险重构
    

*   文档同步
    

先把成功率最高的任务池打透，再逐步扩大范围。

### 阶段七：引入风险分层和治理

当团队开始依赖 AI 自动开发时，就必须考虑：

*   哪些任务可以自动合并
    

*   哪些任务必须人工审批
    

*   哪些目录禁止自动修改
    

*   哪些操作必须留痕
    

*   哪些错误可以自动重试
    

*   哪些错误必须人工接管
    

这时候，AI coding 才真正从 “工具” 变成“工程系统”。

## 十二、我这个框架的真正价值，不是 “自动写代码”，而是 “把工程知识组织起来”

如果只从表面看，Ralph 好像是一个自动写代码的循环器。  
但从更深的角度看，它真正有价值的地方，是在做这件事：

`把分散在人、代码、经验、验收、环境里的知识，逐步组织成一个 AI 可执行的工程系统。`

这也是为什么我认为自己走的方向是对的。

因为 AI 自动 coding 的核心竞争力，不是提示词写得多漂亮，而是：

*   任务定义是否结构化
    

*   规则是否清晰
    

*   项目是否 agent-friendly
    

*   验收是否自动化
    

*   失败是否可回写
    

*   经验是否可复用
    

*   环境是否可观察
    

*   权限是否可治理
    

而我现在做的框架，已经覆盖了这里面的相当一部分。

## 十三、最终结论

如果把整件事压缩成一句话，我会这样总结：

`不是先做 autonomous coding，再补规范；而是先通过 co-pilot 协作，把规范、边界、验收、环境和经验沉淀进 repo，再用 harness 把开发、验证、纠偏和学习串成闭环，最后才会出现真正可靠的 AI 自动化 coding。`

结合我自己的框架和真实样本，我的结论是：

*   这件事是靠谱的
    

*   方向是对的
    

*   我的系统已经不是概念，而是有真实落地的 harness 雏形
    

*   它已经证明适合一类中低复杂度项目
    

*   未来要走向企业级，还需要更强的 schema、更硬的 validator、更严格的 process control 和风险分层
    

换句话说，我现在已经跨过了最难的一步：  
我不再是在讨论 “AI 能不能自动 coding”，而是在讨论 “怎样把自动 coding 变成一个可治理、可验证、可规模化的工程系统”。

这才是正确的问题。

![](https://articles.zsxq.com/assets_dweb/logo@2x.png)

知识星球

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join_group.html?group_id=28882285418421