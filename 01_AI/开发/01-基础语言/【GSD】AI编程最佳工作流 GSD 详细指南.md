---
title: "【GSD】AI编程最佳工作流 GSD 详细指南"
source: "https://articles.zsxq.com/id_rh3zon0v2od1.html"
author:
  - "[[AI随风]]"
published:
created: 2026-05-23
description:
tags:
  - "clippings"
---
[来自： AI随风的AI编程实战营](https://wx.zsxq.com/group/51115228418814)

你有没有遇到过这种情况——

打开 Claude，兴致勃勃地开始描述需求，前几轮回复质量很好，代码写得挺像样。

然后聊着聊着，越来越长，AI 开始走捷径、忘记早期约束、产生幻觉……

最后代码一团糟， `/clear` 重来，所有进度丢失。

**这不是Claude不够好。是你的使用方式有问题。**

这个问题有个名字： **ContextRot（上下文腐化）** 。

***##什么是ContextRot？随着对话越来越长，Claude的上下文窗口被逐渐填满，输出质量** 不可逆地下降* \*。这是所有AI编程工具的本质局限，不是bug，是架构限制。大多数人的应对方式是：更详细地描述需求，或者反复 `/clear` 重来。这治标不治本。\*\* \*

## GSD：解决 Context Rot 的系统级方案

**GSD（GetShitDone）** 是一套专为 Claude Code 设计的元提示 + 上下文工程 + 规格驱动开发系统。

一条命令安装：

```
npx get-shit-done-cc@latest
```

它的核心思路很简单： **复杂度在系统里，不在你的工作流里。**

> "如果你清楚地知道自己想要什么，这套系统就会帮你做出来。没有废话。"  
> — 亚马逊、谷歌、Shopify 工程师用后评价

\* **##传统VibeCodingvsGSD：5个核心差异|痛点|没有GSD|用了GSD||:-------------|:----------------|:----------------------------------||🧠ContextRot|一个超长对话，上下文满了质量崩塌|每个计划在独立200K新鲜上下文中执行，主会话保持30-40%||🌫️需求散乱|需求藏在聊天里，不知道做完没有| `REQUIREMENTS.md` 带ID可追踪，自动映射测试命令||🔀全部串行|所有任务挤在一条对话，只能一件件做|Wave并行执行，无依赖的计划同时跑||🔄跨会话失忆|每次新开会话要重新解释所有背景| `STATE.md` 持久化，一条命令恢复完整上下文||🐛手动调试|出bug自己定位、分析、修复|DebugAgent自动诊断根因，生成修复计划直接执行|** \*

## GSD 的完整工作流：5 步循环

每个功能阶段都是这 5 步的循环：

### Step 1 — /gsd:new-project：初始化项目

系统深度问询直到完全理解你的想法，然后自动完成：

- 1.
	**问询** — 持续提问，覆盖目标、约束、技术偏好、边缘情况

- 2.
	**研究** — 4 个并行 Agent 同时调查领域知识

- 3.
	**需求** — 提取 v1 必须有 / v2 以后做 / 超出范围三档

- 4.
	**路线图** — 创建映射到需求的阶段划分，你来批准

**输出：** `PROJECT.md` 、 `REQUIREMENTS.md` 、 `ROADMAP.md` 、 `STATE.md`

\* **###Step2— `/gsd:discuss-phaseN` ：锁定实现偏好路线图上每个阶段只有一两句描述，这不足以按照** 你设想的方式\*\*去构建。

这一步在研究和规划之前，捕获你的偏好：

- 视觉特性 → 布局、密度、交互、空状态

- API/CLI → 响应格式、错误处理、详细程度

- 内容系统 → 结构、语气、深度

**不要跳过这一步。** 跳过 → 系统做合理假设 → 你得到一个还行的实现。用它 → 系统锁定你的决策 → 你得到你真正想要的东西。

**输出：** `{phase}-CONTEXT.md`

---

### Step 3 — /gsd:plan-phase N：多 Agent 规划

系统先用 4 个并行 Agent 深度调研领域：

- **Stack** — 技术栈、依赖、版本兼容性

- **Features** — 功能模式、最佳实践

- **Architecture** — 架构选择、设计模式

- **Pitfalls** — 常见陷阱、已知问题

然后 Planner 创建 2-3 个原子任务计划（XML 结构），Plan Checker 从 8 个维度验证，不通过最多循环 3 次。

**输出：** `{phase}-RESEARCH.md` 、 `{phase}-{N}-PLAN.md`

---

### Step 4 — /gsd:execute-phase N：并行 Wave 执行

按依赖关系将计划分组为多个 Wave：

```
WAVE 1（并行）          WAVE 2（并行）          WAVE 3
┌─────────┐ ┌─────────┐  ┌─────────┐ ┌─────────┐  ┌─────────┐
│ Plan 01 │ │ Plan 02 │→ │ Plan 03 │ │ Plan 04 │→ │ Plan 05 │
│User Model│ │Prod Model│  │Orders API│ │Cart API │  │Checkout │
└─────────┘ └─────────┘  └─────────┘ └─────────┘  └─────────┘
```

- Wave 内并行，Wave 间顺序

- 每个计划在独立的 200K 上下文中执行

- 完成后立即原子提交

```
abc123f feat(08-02): implement password hashing
def456g feat(08-02): add email confirmation flow
hij789k docs(08-02): complete user registration plan
```

每个任务独立可回滚，git bisect 精准定位问题。

**输出：** `{phase}-SUMMARY.md` 、 `{phase}-VERIFICATION.md`

---

### Step 5 — /gsd:verify-work N：验收与修复

系统逐一引导你测试每个可交付成果："能用邮箱登录吗？"

- ✅ 通过 → 继续下一条

- ✗ 失败 → Debug Agent 自动诊断根因 → 生成修复计划 → 再次执行

**你不需要手动调试。系统知道出了什么问题。**

\* **##里程碑管理全部阶段完成后： `bash/gsd:audit-milestone#检查是否达成里程碑定义/gsd:complete-milestone#归档+打GitTag/gsd:new-milestone#开始下一版本` 中途可以随时调整路线图： `bash/gsd:add-phase#追加新阶段/gsd:insert-phase3#在第3阶段后插入紧急工作/gsd:remove-phase7#移除阶段并自动重新编号`** \*

## 不适合 GSD 的场景（说实话）

GSD 也有明显的代价，用之前要心里有数：

**💸Token消耗显著更高**  
多 Agent 并行，一个完整阶段的消耗可能是普通对话的 5-10 倍。应对：用 `budget` 档位，或关闭不必要的 Agent。

**⏳不适合小任务**  
一个简单脚本用 `new-project` 明显过重。小任务直接用 `/gsd:quick` 。

**🔭不适合模糊探索期**  
GSD 的前提是"你知道自己想要什么"。如果还在早期试错阶段，自由 Vibe Coding 验证方向之后再引入 GSD。

**🎯计划质量取决于你的输入**  
回答含糊 → 结构化的垃圾输出。认真回答系统的问题，用 `discuss-phase` 锁定细节。

**📚有一定学习曲线**  
~30 个命令、多个 Agent 角色、Wave 依赖关系，前几个项目可能比直接聊慢。建议先掌握核心五步流程再深入。

***##记住这5件事1.** Context Rot 是真实问题* \*，GSD通过子Agent+新鲜上下文解决，不是绕过它2.\*\* `discuss-phase` 最关键\*\*，在这里决定实现方式，不要跳过3.\*\* 垂直切片比水平分层并行效率更高\*\*，Plan01:完整用户特性>Plan01:所有Model4.\*\* 出问题不手调\*\*，让verify-work+debugger自动诊断并规划修复5.\*\* 按需调优\*\*，原型期用 `budget+yolo` ，生产发布用 `quality+interactive` \*\* \*

## 完整命令序列

```
# 安装
npx get-shit-done-cc@latest

# 启动（已有代码库先跑 map-codebase）
/gsd:map-codebase
/gsd:new-project
/clear

# 每个阶段循环
/gsd:discuss-phase N
/gsd:plan-phase N
/gsd:execute-phase N
/gsd:verify-work N
/clear

# 发布
/gsd:audit-milestone
/gsd:complete-milestone
```

***GSD最适合这类场景：** 目标明确、需要持续迭代、项目复杂度中等以上、独立开发者或小团队* \*。如果你在构建需要长期维护的产品，GSD的前期投入会在第2、3个里程碑时开始大量回报。\*\* Claude Code is powerful. GSD makes it reliable.\*\*

→ GitHub： [github.com/glittercowboy/get-shit-done](https://github.com/glittercowboy/get-shit-done)  
→ 社区： [discord.gg/gsd](https://discord.gg/gsd)

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51115228418814