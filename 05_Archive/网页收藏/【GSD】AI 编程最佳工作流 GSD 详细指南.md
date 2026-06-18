---
url: https://articles.zsxq.com/id_rh3zon0v2od1.html
title: 【GSD】AI 编程最佳工作流 GSD 详细指南
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-21 10:16:27
tags:

banner: "undefined"
banner_icon: 🔖
---
你有没有遇到过这种情况——

打开 Claude，兴致勃勃地开始描述需求，前几轮回复质量很好，代码写得挺像样。

然后聊着聊着，越来越长，AI 开始走捷径、忘记早期约束、产生幻觉……

最后代码一团糟，`/clear` 重来，所有进度丢失。

**这不是 Claude 不够好。是你的使用方式有问题。**

这个问题有个名字：**ContextRot（上下文腐化）** 。

_**## 什么是 ContextRot？随着对话越来越长，Claude 的上下文窗口被逐渐填满，输出质量** 不可逆地下降_ *。这是所有 AI 编程工具的本质局限，不是 bug，是架构限制。大多数人的应对方式是：更详细地描述需求，或者反复`/clear`重来。这治标不治本。** *

## GSD：解决 Context Rot 的系统级方案

**[[【GSD】AI编程最佳工作流 GSD 详细指南|GSD]]（GetShitDone）** 是一套专为 [[Claude Code 命令与最佳实践|Claude Code]] 设计的元提示 + 上下文工程 + 规格驱动开发系统。

一条命令安装：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
npx get-shit-done-cc@latest

```

它的核心思路很简单：**复杂度在系统里，不在你的工作流里。**

"如果你清楚地知道自己想要什么，这套系统就会帮你做出来。没有废话。"  
— 亚马逊、谷歌、Shopify 工程师用后评价

***## 传统 VibeCodingvsGSD：5 个核心差异 | 痛点 | 没有 GSD | 用了 GSD||:-------------|:----------------|:----------------------------------||🧠ContextRot | 一个超长对话，上下文满了质量崩塌 | 每个计划在独立 200K 新鲜上下文中执行，主会话保持 30-40%||🌫️需求散乱 | 需求藏在聊天里，不知道做完没有 |`REQUIREMENTS.md`带 ID 可追踪，自动映射测试命令 ||🔀全部串行 | 所有任务挤在一条对话，只能一件件做 | Wave 并行执行，无依赖的计划同时跑 ||🔄跨会话失忆 | 每次新开会话要重新解释所有背景 |`STATE.md`持久化，一条命令恢复完整上下文 ||🐛手动调试 | 出 bug 自己定位、分析、修复 | DebugAgent 自动诊断根因，生成修复计划直接执行 |** *

## GSD 的完整工作流：5 步循环

每个功能阶段都是这 5 步的循环：

### Step 1 — `/gsd:new-project`：初始化项目

系统深度问询直到完全理解你的想法，然后自动完成：

*   1.
    
    **问询** — 持续提问，覆盖目标、约束、技术偏好、边缘情况
    

*   2.
    
    **研究** — 4 个并行 [[07-Agent|Agent]] 同时调查领域知识
    

*   3.
    
    **需求** — 提取 v1 必须有 / v2 以后做 / 超出范围三档
    

**输出：** `PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`STATE.md`

***###Step2—`/gsd:discuss-phaseN`：锁定实现偏好路线图上每个阶段只有一两句描述，这不足以按照** 你设想的方式 ** 去构建。

这一步在研究和规划之前，捕获你的偏好：

**不要跳过这一步。** 跳过 → 系统做合理假设 → 你得到一个还行的实现。用它 → 系统锁定你的决策 → 你得到你真正想要的东西。

**输出：** `{phase}-CONTEXT.md`

* * *

### Step 3 — `/gsd:plan-phase N`：多 Agent 规划

系统先用 4 个并行 Agent 深度调研领域：

然后 Planner 创建 2-3 个原子任务计划（XML 结构），Plan Checker 从 8 个维度验证，不通过最多循环 3 次。

**输出：** `{phase}-RESEARCH.md`、`{phase}-{N}-PLAN.md`

* * *

### Step 4 — `/gsd:execute-phase N`：并行 Wave 执行

按依赖关系将计划分组为多个 Wave：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
WAVE 1（并行）          WAVE 2（并行）          WAVE 3
┌─────────┐ ┌─────────┐  ┌─────────┐ ┌─────────┐  ┌─────────┐
│ Plan 01 │ │ Plan 02 │→ │ Plan 03 │ │ Plan 04 │→ │ Plan 05 │
│User Model│ │Prod Model│  │Orders API│ │Cart API │  │Checkout │
└─────────┘ └─────────┘  └─────────┘ └─────────┘  └─────────┘

```

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
abc123f feat(08-02): implement password hashing
def456g feat(08-02): add email confirmation flow
hij789k docs(08-02): complete user registration plan

```

每个任务独立可回滚，git bisect 精准定位问题。

**输出：** `{phase}-SUMMARY.md`、`{phase}-VERIFICATION.md`

* * *

### Step 5 — `/gsd:verify-work N`：验收与修复

系统逐一引导你测试每个可交付成果："能用邮箱登录吗？"

*   ✗ 失败 → Debug Agent 自动诊断根因 → 生成修复计划 → 再次执行
    

**你不需要手动调试。系统知道出了什么问题。**

***## 里程碑管理全部阶段完成后：`bash/gsd:audit-milestone#检查是否达成里程碑定义/gsd:complete-milestone#归档+打GitTag/gsd:new-milestone#开始下一版本`中途可以随时调整路线图：`bash/gsd:add-phase#追加新阶段/gsd:insert-phase3#在第3阶段后插入紧急工作/gsd:remove-phase7#移除阶段并自动重新编号`** *

## 不适合 GSD 的场景（说实话）

GSD 也有明显的代价，用之前要心里有数：

**💸Token 消耗显著更高**  
多 Agent 并行，一个完整阶段的消耗可能是普通对话的 5-10 倍。应对：用 `budget` 档位，或关闭不必要的 Agent。

**⏳不适合小任务**  
一个简单脚本用 `new-project` 明显过重。小任务直接用 `/gsd:quick`。

**🔭不适合模糊探索期**  
GSD 的前提是 "你知道自己想要什么"。如果还在早期试错阶段，自由 Vibe Coding 验证方向之后再引入 GSD。

**🎯计划质量取决于你的输入**  
回答含糊 → 结构化的垃圾输出。认真回答系统的问题，用 `discuss-phase` 锁定细节。

**📚有一定学习曲线**  
~30 个命令、多个 Agent 角色、Wave 依赖关系，前几个项目可能比直接聊慢。建议先掌握核心五步流程再深入。

_**## 记住这 5 件事 1.** Context Rot 是真实问题_ *，GSD 通过子 Agent + 新鲜上下文解决，不是绕过它 2.** `discuss-phase` 最关键 **，在这里决定实现方式，不要跳过 3.** 垂直切片比水平分层并行效率更高 **，Plan01: 完整用户特性 > Plan01: 所有 Model4.** 出问题不手调 **，让 verify-work+debugger 自动诊断并规划修复 5.** 按需调优 **，原型期用`budget+yolo`，生产发布用`quality+interactive`** *

## 完整命令序列

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
npx get-shit-done-cc@latest


/gsd:map-codebase
/gsd:new-project
/clear


/gsd:discuss-phase N
/gsd:plan-phase N
/gsd:execute-phase N
/gsd:verify-work N
/clear


/gsd:audit-milestone
/gsd:complete-milestone

```

_**GSD 最适合这类场景：** 目标明确、需要持续迭代、项目复杂度中等以上、独立开发者或小团队_ *。如果你在构建需要长期维护的产品，GSD 的前期投入会在第 2、3 个里程碑时开始大量回报。** Claude Code is powerful. GSD makes it reliable.**

→ GitHub：[github.com/glittercowboy/get-shit-done](https://github.com/glittercowboy/get-shit-done)  
→ 社区：[discord.gg/gsd](https://discord.gg/gsd)