---
url: https://articles.zsxq.com/id_j6mkwfi5crdz.html
title: 【AI 编程进阶 2】如何写 AI 编程最核心最重要的文件：CLAUDE.md/AGENTS.md
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-23 16:40:28
tags:

banner: "https://article-images.zsxq.com/FsRqCvoGMs99H5cbvAoD0PW5cQ0F"
banner_icon: 🔖
---
Claude.md 是 [[Claude Code 命令与最佳实践|Claude Code]] 的识别的永久记忆文件

Agents.md 功能跟 Claude.md 是一样的，是标准的永久记忆文件，除了 Claude Code，其他编程工具都是会把

Agents.md 作为记忆文件

这里举的例子也适合 Agents.md, 因为他们的原理是一样的

原因就是 Claude.md 的全文在每次跟 AI 对话都会加载到上下文中，上下文的长度是非常宝贵的，AI 会在上下文到达一定长度后进行压缩，但是 Claude.md 不管怎么压缩，都会在上下文中完整的呈现，所以这就决定了它的重要性。

1.  **项目 /.claude/CLAUDE.md**：如果你喜欢把配置文件放在子目录里，这是一个替代方案。
2.  **~/.claude/CLAUDE.md**：适用于你所有项目的用户层默认设置。

文件名是大小写区分的。它必须完全 CLAUDE.md（大写 CLAUDE，小写 .md）。Claude Code 在加载内存文件时会寻找这个特定文件名。

## 初始化

### 1、空项目

如果项目是空的项目，那么你可以自己创建这个 CLAUDE.md 文件，在最上方写上一个项目的简短的描述，不需要太详细，在 50 字以内

![](https://article-images.zsxq.com/FsRqCvoGMs99H5cbvAoD0PW5cQ0F)

### 2、有代码或者 README.md 文件

Claude Code 直接执行 / init 命令，其他编程工具，可以使用对话的方式创建

阅读代码和文档，帮我创建一个用于 AI 理解项目的 AGENTS.md 文档

先不管里面的内容怎么样，我们先把它这个文件先创建出来

## 修改 CLAUDE.md

按下面的文档组织结构（非必需，可以更多）来修改 CLAUDE.md 文件

**项目背景** ：这个项目是什么？“这是一个 [[Day4-Next.js核心|Next.js]] 的电子商务应用，集成了 Stripe。” 这能够让 Claude 明白。

**命令** ：如何运行测试、构建、添加 lint 和部署。当你让 Claude 运行时，它会用这些命令。

**警告** ：项目特定警告。那个带有奇怪重试逻辑的认证模块。需要特定头部格式的 API 端点。那个文件绝不能直接修改。

**项目基础的文件结构**：只需要列出最重要的入口就行，比如组件目录，api 目录等

**重要的提示信息：**你需要告诉 AI 的最重要的信息，没有这条信息，AI 返回的东西就会出错

#项目说明

这是一个使用 React 开发的个人博客网页，包含主页，支付等功能

## 代码规范

- [[Day2-JavaScript和TypeScript|TypeScript]] strict mode, no `any` types

- Use named exports, not default exports

- CSS: [[Day3-Tailwind和shadcn|Tailwind]] utility classes, no custom CSS files

## 常用命令

- `npm run dev`: Start development server (port 3000)

- `npm run test`: Run Jest tests

- `npm run test:e2e`: Run Playwright end-to-end tests

- `npm run lint`: ESLint check

- `npm run db:migrate`: Run Prisma migrations

## 文件结构

- `/app`: Next.js App Router pages and layouts

- `/components/ui`: Reusable UI components

- `/lib`: Utilities and shared logic

- `/prisma`: Database schema and migrations

- `/app/api`: API routes

## 警告

- 没有我的允许，不要修改. env 文件内容

## 主要事项

- 每次编译必须经过测试

- 图片上传要放到 OSS

这个文件内容只是一个参考的结构，你也可以按照自己的要求去写到里面去，但是呢，最好是不要超过 300 行

## 使用 @符号，引入更多内容

有的时候可能某一个模块要说的东西太多，比如说代码规范，你希望他遵循，比如说像阿里巴巴这样代码规范，或者说技术架构，你想描述好的技术架构，那么你可以通过 @符号引用的方式，把这个内容加到这个文档里面去，但是一定要注意，不要直接使用 @符号引入，一定要说明情况，什么情况下去阅读这里面的内容，这也是让 AI 不要一次性把内容都放到上下文，让它可以按需加载

你可以从任何地方查阅文件：

1.  路径：@docs/style-guide.md
2.  即使是用户级文件：@~/.claude/my-preferences.md

# 项目核心上下文 (Project Context)

## 1. 项目全貌

> 这里的 @README.md 是项目的灵魂，包含业务目标与架构概览。

- 项目简介: 详见 @README.md

## 2. 工程规范 (Engineering Standards)

> 强制 AI 遵守团队既定的代码风格与协作流程。

- 如果你在编写 API 接口，请参考 @docs/api-guide.md

- Git 提交与分支策略: 严格遵循 @docs/git.md

## 3. 开发者偏好 (Personal Preferences)

> 这是一个巧妙的技巧：引用本地的全局配置文件，让 AI 记住你的个人编码习惯（如命名喜好、注释风格）。

- ** 我的专属配置 **: @~/.claude/my-project-notes.md

Claude.md 文件不是一写完就不管了，而且是随着项目的迭代，你需要去尽量去更新。比如在项目开发中，AI 会犯一些错误啊，经常性出现一到两次，那么你就应该把这个防止他错误的这个规则写到这个文件里面去，好的 Claude.md 一定是经常迭代出来的。

相信你养成了去迭代 Claude.md 的一个习惯，你这个 A 编程的效率一定会大大的提升

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join_group.html?group_id=51115228418814