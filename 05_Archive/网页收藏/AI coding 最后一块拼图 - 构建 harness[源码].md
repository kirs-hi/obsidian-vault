---
url: https://articles.zsxq.com/id_ixarv5ec0fvw.html
title: AI coding 最后一块拼图 - 构建 harness[源码]
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-14 19:25:21
tags:

banner: "https://article-images.zsxq.com/Fvvzn0r7afiJKy599rYTUrSZnAwQ"
banner_icon: 🔖
---
前面已经和大家讲过 AI 自动化 Coding 的三个环节， 已经讲过自动化 coding 如何运行起来， 以及复利工程，今天补上最后一块拼图：构建 Harness。

这个 Skill 我已经写好了，后面会放到文章末尾，大家可以直接下载使用。

我先把它背后的结构和构建逻辑讲清楚。

## 为什么需要 Harness

真实项目里，很少是单项目结构。更多时候，AI Coding 面对的是多项目协作场景。

常见有两类：

*   1.
    
    新项目：前后端分离，例如后端用 Python，前端用 React。
    

不管是哪一种，只要是多项目协作，就会遇到一个问题：AI 需要先理解项目之间的边界、依赖和协作方式，才能稳定地改代码。

Harness 的作用，就是把这些信息组织起来，给 AI 提供一套可导航、可推理、可落地执行的工程上下文。

## Harness 的三层结构

Harness 可以理解为三层结构：

### 1. 索引层

`Agents.md`

这一层是整个工程的蓝图和入口，可以把它理解成目录索引。它回答的是：这个工程有哪些子项目，每个子项目负责什么，AI 应该从哪里开始理解。

### 2. 集成层

`/coding_maps/`

这一层描述的是子项目之间的交互关系和集成方式，比如调用链、依赖关系、接口连接方式，以及其他帮助 AI 理解整体架构的说明文档。

### 3. 事实层

`/subproject1/.planning/codebase/`  
`/subproject2/.planning/codebase/`  
`...`

这一层是每个子项目自己的事实描述，也就是代码库本身的结构、模块、关键文件和职责边界。

当这三层都具备之后，AI 在做 Coding 时就能：

这也是 Harness 的核心价值：让 AI 不只是 “看见代码”，而是 “理解整个工程”。

## 目录结构示意

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
Agents.md                         # 索引层
/coding_maps/                     # 集成层
/subproject1/.planning/codebase/  # 子项目事实层
/subproject2/.planning/codebase/  # 子项目事实层
...



```

## 如何构建 Harness

整体过程分两步：先生成每个子项目的事实层，再汇总构建整个 Harness。

### 第一步：为每个子项目生成事实层

这里我们用 [[【GSD】AI编程最佳工作流 GSD 详细指南|GSD]] 来生成子项目的 Codebase Map。

GSD 项目：[https://github.com/gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)

安装命令：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
npx get-shit-done-cc@latest



```

进入任意一个子项目目录，运行：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
/gsd-map-codebase



```

（以下截图是后端代码）  

![](https://article-images.zsxq.com/Fvvzn0r7afiJKy599rYTUrSZnAwQ)

  

执行完成后，会生成对应的事实层文件夹。

然后进入下一个子项目，重复同样的操作，为每个子项目都生成各自的事实层。

（以下截图是前端代码）  

![](https://article-images.zsxq.com/Fkrvhs9UZU5YNwH9goywEocWqcf6)

  

### 第二步：构建整个 Harness 工程

当所有子项目的事实层都准备好之后，就可以运行我们提供的 Skill，去构建整个 Harness 工程。

![](https://article-images.zsxq.com/FhrSJnBNT7ECRrL22RgFQ2SPDAn6)

  

运行 skills 的命令是：  
（以下这个命令会触发这个 skills，需要把不同的子目录生成的事实的文件夹名字给到命令中。）

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
生成Agents.md: back/.planning front/.planning



```

## 构建结果

最终生成的目录结构大致如下：

![](https://article-images.zsxq.com/FjW5VDe0airdD87VospfPngLtQL-)

  

## 总结

Harness 解决的不是 “如何让 AI 写一段代码”，而是 “如何让 AI 在多项目工程里持续、稳定、准确地写代码”。

它的关键不是某一个命令，而是这三层信息的组织方式：

通过网盘分享的文件：AI 自动化 coding - 构建 harness 的 skills.zip  
链接: [https://pan.baidu.com/s/1Qd76doFRE5r-vym0VvWedg](https://pan.baidu.com/s/1Qd76doFRE5r-vym0VvWedg) 提取码: 7yba  
-- 来自百度网盘超级会员 v5 的分享