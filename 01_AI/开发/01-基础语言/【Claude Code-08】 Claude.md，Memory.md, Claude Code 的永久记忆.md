---
title: "【Claude Code-08】 Claude.md，Memory.md, Claude Code 的永久记忆"
source: "https://articles.zsxq.com/id_9pxceoomtswk.html"
author:
  - "[[AI随风]]"
published:
created: 2026-05-23
description:
tags:
  - "clippings"
---
[来自： AI随风的AI编程实战营](https://wx.zsxq.com/group/51115228418814)

## Claude Code 的两种记忆文件

## CLAUDE.md 全文存储的全局记忆文件

原因就是 Claude.md 的全文在每次跟 AI 对话都会加载到上下文中，上下文的长度是非常宝贵的，AI 会在上下文到达一定长度后进行压缩，但是Claude.md不管怎么压缩，都会在上下文中完整的呈现，所以这就决定了它的重要性。

![](https://article-images.zsxq.com/FsRhez2wG-WfgyILnRZO55hyFLFv)

## 全局记忆带来的影响

### 第一层：它本身会占上下文长度

Claude.md 越长，占用的上下文长度越大

### 第二层：它会诱发更多行为

每次开始处理任务前，都先完整阅读相关目录以及上下游依赖目录，确保充分理解整体结构后再动手。

每次完成修改后，都要尽可能运行完整测试链路，包括构建、单元测试、集成测试和人工验证。

诱发的更多行为：

1. 先扩大阅读范围
2. 去读更多目录
3. 去找上下游依赖
4. 改完后跑更多测试
5. 即使当前任务只是一个小修改，也更可能走完整流程

解决办法：缩小范围

涉及接口行为、数据结构或核心流程的改动时，再做完整验证。

普通小改动优先做最小必要验证。

### 第三层：它会增加判断负担

写了太多泛泛规则

保持代码优雅、简洁、可维护。

注意抽象层次。

优先考虑扩展性。

遵守一致性。

避免技术债。

大模型：

优雅是什么意思？？

模型每次都要对这些词语进行判断，增加推理成本。

所以：

**CLAUDE.md 越长，不代表帮助越大；很多时候只是让模型反复做不必要的筛选。**

## Memory.md Claude Code 的自动记忆文件

Claude 在工作过程中自动保存笔记——构建命令、调试洞察、架构笔记、代码风格偏好。存储在 ~/.claude/projects/<project>/memory/ 目录下，MEMORY.md 作为索引文件。Claude 自行决定什么值得记住，基于该信息是否在未来的对话中有用。

如果 memery.md 的长度超过200行或者超过 25KB，都会被截断

## Claude.md 与 Memory.md 的区别

![](https://article-images.zsxq.com/Fk8qXqm-UORm3DQUmF5YZK04Hrs1)

## CLAUDE.md 的作用范围

1. **项目/.claude/CLAUDE.md** ：如果你喜欢把配置文件放在子目录里，这是一个替代方案。
2. **~/.claude/CLAUDE.md** ：适用于你所有项目的用户层默认设置。

文件名是大小写区分的。它必须完全 CLAUDE.md（大写 CLAUDE，小写.md）。Claude Code 在加载内存文件时会寻找这个特定文件名。

Claude Code 通过从当前工作目录往上走，逐个目录检查 CLAUDE.md 和 CLAUDE.local.md 文件来读取 CLAUDE.md 文件。这意味着如果你在 foo/bar/ 中运行 Claude Code，它会加载来自 foo/bar/CLAUDE.md、foo/CLAUDE.md 以及它们旁边的任何 CLAUDE.local.md 文件的指令。

\-foo

CLAUDE.md

\-foo

\--bar

\-- Claude.md

## 应该怎么写 CLAUDE.md

核心：

1、没有这条内容，AI 将会犯错。

2、Claude.md 需要不断迭代，不能一次到位

3、模型越强，Claude.md 反而越简单

官方建议内容行数越短越好，不要超过 200 行

## 反面例子

反面例子：

\# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

\## 项目概览

这是一个现代化、可扩展、稳定、高性能的全栈项目。项目包含前端、后端、脚本、工具链、自动化配置等多个部分，目标是为用户提供稳定、优雅、一致的体验。

\## 目录结构

\- src/ 是主要源码目录

\- components/ 是组件目录

\- services/ 是服务目录

\- utils/ 是工具目录

\- hooks/ 是钩子目录

\- docs/ 是文档目录

\- scripts/ 是脚本目录

\## 开发原则

\- 保持代码优雅

\- 注意可维护性

\- 注意一致性

\- 注意复用

\- 注意抽象边界

\- 注意扩展性

\- 避免技术债

\- 写清晰代码

\- 提供良好错误提示

\## 开发流程

每次开始任务前，请先阅读相关代码、目录结构、README、文档、规则文件，并结合上下游模块进行全面理解。每次修改完成后，请尽可能运行完整测试、构建、检查、人工验证和日志检查，以确保没有回归问题。

\## 测试流程

\- 运行构建

\- 运行单元测试

\- 运行集成测试

\- 检查页面

\- 检查接口

\- 检查日志

\- 确认无异常

\## 其他要求

\- 回答时尽量完整

\- 如果可能请先说明方案

\- 如果需要请解释原因

\- 修改时注意所有相关模块

这份错误示例为什么不好

![](https://article-images.zsxq.com/Fonx1hjSeNV5TOSGJ1BIBFaSKIEp)

## 正确写法

### 第一条：写规则，不写介绍

CLAUDE.md 最适合写的是：

1. 在这个项目里应该怎么工作
2. 在这个项目里哪些事情不能乱做
3. 哪些规则是代码本身推导不出来的

它不适合写的是：

1. 这个项目有多么先进
2. 目录结构从上到下是什么
3. 一般性的开发建议

所以，好的 CLAUDE.md 更像“工作约束”，而不是“项目简介”。

### 第二条：写约束，不写常识

如果一件事模型本来就应该知道，那就没必要写。

例如：

1. 写代码要注意可读性
2. 记得测试
3. 提供清晰报错
4. 注意不要提交密钥

这些都属于通用常识。

把它们反复写进 CLAUDE.md，收益极低，成本却是每轮都要付。

真正该写的是：

1. 这个项目里独特的约束
2. 这个团队里独特的习惯
3. 这个仓库里独特的边界

### 第三条：写长期有效的流程信息，不写临时任务

CLAUDE.md 不应该承载：

1. 这次需求怎么做
2. 当前任务分几步
3. 这轮开发计划是什么
4. 这次改动的具体细节

这些都属于：

1. 计划
2. 任务
3. 临时上下文

它们不是长期规则。

所以， **长期有效** ，是非常关键的判断标准。

### 第四条：某个错误模型出现两次以上，则更新到 Claude.md 中

## 使用/init 命令初始化Claude.md

在.claude/settings.json 文件中增加以下配置，开启新的/init 流程

"env": {

"CLAUDE\_CODE\_NEW\_INIT": 1

},

/init 流程

## 初始化时会扫描哪些地方

![](https://article-images.zsxq.com/Fv2B0m-ud9hkodtjtYZc_hzB7mQe)

## 什么情况下会生成技能

![](https://article-images.zsxq.com/FuF6u3wrvNFk0e4DWkhB6UClIIeD)

## 什么情况下会生成钩子

![](https://article-images.zsxq.com/FsFikMPk4iFgmpdYfQU5at9bGmXA)

## Claude.md 进阶技巧

## 使用@符号，引入更多内容

有的时候可能某一个模块要说的东西太多，比如说代码规范，你希望他遵循，比如说像阿里巴巴这样代码规范，或者说技术架构，你想描述好的技术架构，那么你可以通过@符号引用的方式，把这个内容加到这个文档里面去，但是一定要注意，不要直接使用@符号引入，一定要说明情况，什么情况下去阅读这里面的内容，这也是让AI不要一次性把内容都放到上下文，让它可以按需加载

你可以从任何地方查阅文件：

1. 路径：@docs/style-guide.md
2. 即使是用户级文件：@~/.claude/my-preferences.md

\# 项目核心上下文 (Project Context)

\## 1. 项目全貌

\> 这里的 @README.md 是项目的灵魂，包含业务目标与架构概览。

\- 项目简介: 详见 @README.md

\## 2. 工程规范 (Engineering Standards)

\> 强制 AI 遵守团队既定的代码风格与协作流程。

\- 如果你在编写API接口，请参考 @docs/api-guide.md

\- Git 提交与分支策略: 严格遵循 @docs/git.md

\## 3. 开发者偏好 (Personal Preferences)

\> 这是一个巧妙的技巧：引用本地的全局配置文件，让 AI 记住你的个人编码习惯（如命名喜好、注释风格）。

\- \*\*我的专属配置\*\*: @~/.claude/my-project-notes.md

## 使用Rules分离多模块规则

对于较大的项目，你可以用.claude/rules/ 目录将指令组织成多个文件。这使指令模块化，团队维护更为便捷。规则还可以针对 [特定文件路径进行作用域](https://code.claude.com/docs/en/memory#path-specific-rules) ，因此只有在 Claude 处理匹配文件时才加载到上下文中，减少噪声并节省上下文空间。

your-project/

├──.claude/

│ ├── CLAUDE.md # Main project

│ └── rules/

│ ├── code-style.md # Code style guidelines

│ ├── testing.md # Testing conventions

│ └── security.md # Security requirements

\---

paths:

\- "src/api/\*\*/\*.ts"

\---

\# API Development Rules

\- All API endpoints must include input validation

\- Use the standard error response format

没有路径字段的规则会无条件加载，并适用于所有文件。路径范围规则在 Claude 读取符合模式的文件时触发，而非每次使用工具时触发。

![](https://article-images.zsxq.com/FvmGEJviN5gm3EJObbM7JLlocvwt)

## 经常更新 Claude.md 是一个好习惯

Claude.md 文件不是一写完就不管了，而且是随着项目的迭代，你需要去尽量去更新。比如在项目开发中，AI会犯一些错误啊，经常性出现一到两次，那么你就应该把这个防止他错误的这个规则写到这个文件里面去，好的Claude.md 一定是经常迭代出来的。

相信你养成了去迭代Claude.md 的一个习惯，你这个A编程的效率一定会大大的提升

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51115228418814