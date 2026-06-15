---
url: https://articles.zsxq.com/id_wewew7gwuizi.html
title: AI 自动化 Coding 2.0 多子项目最佳实践
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-13 16:52:18
tags:

banner: "https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8="
banner_icon: 🔖
---
# AI 自动化 Coding 2.0 多子项目最佳实践

[来自： 雷哥 AI 解决方案](https://wx.zsxq.com/group/28882285418421)

![](https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8=)

雷哥

2026 年 04 月 19 日 11:51

## 一、背景：一次 18 小时的大任务

昨天已经跑通了 1 个 18 个小时 + 的大任务。这个任务里涉及到了 30 个 story，足足花了 3 亿多个 token。

![](https://article-images.zsxq.com/Fj7cmWhb_6jA-c5Cfnrq3s9MutcC)

  

**GLM Token 费用：**

![](https://article-images.zsxq.com/Fr5C-Z5qeK-OxqjyBAZWYYtSYd-W)

  

* * *

## 二、核心议题

今天想跟大家分享的是：**一个多子任务的项目构建，要怎么合理地、以最佳方式去使用 AI 自动化 Coding 2.0 这个项目**。

关键在于：**你需要把整个工程做好**。

* * *

## 三、工程结构推荐：GSD 1.0

这里工程结构的整理，我给大家推荐的是 **GSD 1.0** 的项目结构：

*   **源码**：[https://github.com/gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
    

*   **安装**：`npx get-shit-done-cc@latest`
    

安装之后，就可以放在你自己喜欢的 IDE 下面。它其实是一组 skills 或者说 commands，本质上就是一组提示词。

### 关键提示词：`/gsd-map-codebase`

它可以将我们整个老项目的架构梳理得非常清晰。

运行之后，它会产出关于项目结构、技术栈、框架等相关的内容，梳理得非常清晰。你大概审一下没有问题的话，这个生成内容就可以作为我们**第一版的 harness 工程**。

想跟大家聊这个，是想说：**无论是老项目还是新项目，让 AI 在做 Coding 的时候理解你的项目结构，这是非常关键的。** 所以它可以作为我们初始项目结构的说明书。

![](https://article-images.zsxq.com/FnusCKbWpIsBp_Beybh133VtZnib)

  

* * *

## 四、多子项目场景（今日重点）

今天更想跟大家讲的其实是**多个子项目**的情况。因为很少人只会用到一个子项目——即使是前后端分离，也是两个子项目；如果使用微服务架构，可能会有更多子项目。

### 实际案例：企业 AI 咨询项目

我最近在给企业做 AI 咨询顾问, 并给他们做些实施研发的工作，我们在做的技术栈选型是：

*   **后端**：使用若依平台（包含 2 个子项目）
    

*   **前端**：使用 React（1 个业务前端子项目）
    

相当于一共有 **3 个子项目**。

### 处理方式

你可以把每一个子项目按模块划分，让 GSD 去把结构读一遍，从而为每个子项目产生一份 codebase 说明：

![](https://article-images.zsxq.com/FiEw-yA8zzbGXRXd751RkqefdgCS)

  

### 合成总说明书

有了各子项目的 codebase 说明之后，你需要把它们合成一个**大的说明书**。这个大说明书可以指导 AI：

*   当你去改若依的时候，去读哪些 codebase 内容
    

*   当你去做业务前端的时候，去读哪些 codebase 内容
    

![](https://article-images.zsxq.com/Fn1YZQThhXou3rU94ChOKXKOwcQC)

  

这样整个 map 的初版就有了。后续如果系统架构再更改，我们可以陆续在这个 maps 里补全、逐步完善。

### 三层文档结构

这样你就会有一个**根路径**，这个根路径会把前后端的结构 maps 和项目整体规则的入口文件都描述清晰。

描述清晰之后，再去做 AI 自动化 Coding 时，AI 就可以很好地理解这个项目，不用把项目的所有说明文件全部读完。**说明文件分成了三层**：需要更改哪部分时就去读哪部分。

这样：

*   上下文的获取会更加精准
    

*   写起来会更加顺利
    

![](https://article-images.zsxq.com/Fh0bNF8R8e2RTwsXZOX3bsSHKJWu)

  

* * *

## 五、PRD 的重要性

除此之外，还有一个**最重要的点**：你要在做 PRD 的时候，把它做得非常非常清晰。

因为你已经有了 `AGENT.md`，所以你在聊需求的时候，AI 也会懂你整个的架构。基于这个架构：

*   1.
    
    先以**对话方式**跟 AI 聊需求
    

*   2.
    
    聊清楚之后，告诉它：「我要把我们聊的这些对话整理成一个需求开发的实施文档」
    

*   3.
    
    要求：这个文档要给基础开发人员使用，尽量让他们少问问题，拿着文档就可以开发
    

把这个要求给到 AI 之后，它就会给你整理出一份非常详细的文档：

![](https://article-images.zsxq.com/FsRZIK5O_WsBs29o-QbTQWWitNRa)

  

这个文档基本上写完都在 **1000~2000 行**之内，因为写得非常清晰。再结合这个文档，你直接就可以把它生成 `prd.json`。

### 执行效果

这样去做效果会非常好。整个操作下来，18 个小时做完之后，我审核整个文档 + 聊需求一共花了大约**一个半小时**。

并不是说让 AI 完全自动去做，你必须要了解项目的结构。基于这个项目结构把 PRD 做好，把需要描述的功能让 AI 做一份详细的设计文档。所以它跑起来效果就非常好。

![](https://article-images.zsxq.com/FvQ6RArHaiWecjK0R5fD26HDSf0d)

  

* * *

## 六、重点信息：长任务循环的关键配置

这里还有一个重点信息：当你让循环自动跑的时候，有一个 `CLAUDE.md` 文件，你需要在这个文件里明确指示：

**如果做 story 时哪块不清楚，要去看这份主文档。**

因为这份主文档（也就是前面提到的 1300 多行的需求开发实施文档）是你认真审核过的、用于理解需求的主文档。你的 story 也是基于这个种子文档拆分出来的。

### 为什么要这样做？

*   如果 AI 不懂，让它去看种子文档
    

*   这份种子文档的定位是：**基于一个基础开发人员不用反复问你的前提下写成的**，所以它写得非常清晰
    

有了这个配置之后，长任务跑起来效果就是非常好。

* * *

## 一、背景：一次 18 小时的大任务

昨天已经跑通了 1 个 18 个小时 + 的大任务。这个任务里涉及到了 30 个 story，足足花了 3 亿多个 token。

![](https://article-images.zsxq.com/Fj7cmWhb_6jA-c5Cfnrq3s9MutcC)

  

**GLM Token 费用：**

![](https://article-images.zsxq.com/Fr5C-Z5qeK-OxqjyBAZWYYtSYd-W)

  

* * *

## 二、核心议题

今天想跟大家分享的是：**一个多子任务的项目构建，要怎么合理地、以最佳方式去使用 AI 自动化 Coding 2.0 这个项目**。

关键在于：**你需要把整个工程做好**。

* * *

## 三、工程结构推荐：GSD 1.0

这里工程结构的整理，我给大家推荐的是 **GSD 1.0** 的项目结构：

*   **源码**：[https://github.com/gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
    

*   **安装**：`npx get-shit-done-cc@latest`
    

安装之后，就可以放在你自己喜欢的 IDE 下面。它其实是一组 skills 或者说 commands，本质上就是一组提示词。

### 关键提示词：`/gsd-map-codebase`

它可以将我们整个老项目的架构梳理得非常清晰。

运行之后，它会产出关于项目结构、技术栈、框架等相关的内容，梳理得非常清晰。你大概审一下没有问题的话，这个生成内容就可以作为我们**第一版的 harness 工程**。

想跟大家聊这个，是想说：**无论是老项目还是新项目，让 AI 在做 Coding 的时候理解你的项目结构，这是非常关键的。** 所以它可以作为我们初始项目结构的说明书。

![](https://article-images.zsxq.com/FnusCKbWpIsBp_Beybh133VtZnib)

  

* * *

## 四、多子项目场景（今日重点）

今天更想跟大家讲的其实是**多个子项目**的情况。因为很少人只会用到一个子项目——即使是前后端分离，也是两个子项目；如果使用微服务架构，可能会有更多子项目。

### 实际案例：企业 AI 咨询项目

我最近在给企业做 AI 咨询顾问, 并给他们做些实施研发的工作，我们在做的技术栈选型是：

*   **后端**：使用若依平台（包含 2 个子项目）
    

*   **前端**：使用 React（1 个业务前端子项目）
    

相当于一共有 **3 个子项目**。

### 处理方式

你可以把每一个子项目按模块划分，让 GSD 去把结构读一遍，从而为每个子项目产生一份 codebase 说明：

![](https://article-images.zsxq.com/FiEw-yA8zzbGXRXd751RkqefdgCS)

  

### 合成总说明书

有了各子项目的 codebase 说明之后，你需要把它们合成一个**大的说明书**。这个大说明书可以指导 AI：

*   当你去改若依的时候，去读哪些 codebase 内容
    

*   当你去做业务前端的时候，去读哪些 codebase 内容
    

![](https://article-images.zsxq.com/Fn1YZQThhXou3rU94ChOKXKOwcQC)

  

这样整个 map 的初版就有了。后续如果系统架构再更改，我们可以陆续在这个 maps 里补全、逐步完善。

### 三层文档结构

这样你就会有一个**根路径**，这个根路径会把前后端的结构 maps 和项目整体规则的入口文件都描述清晰。

描述清晰之后，再去做 AI 自动化 Coding 时，AI 就可以很好地理解这个项目，不用把项目的所有说明文件全部读完。**说明文件分成了三层**：需要更改哪部分时就去读哪部分。

这样：

*   上下文的获取会更加精准
    

*   写起来会更加顺利
    

![](https://article-images.zsxq.com/Fh0bNF8R8e2RTwsXZOX3bsSHKJWu)

  

* * *

## 五、PRD 的重要性

除此之外，还有一个**最重要的点**：你要在做 PRD 的时候，把它做得非常非常清晰。

因为你已经有了 `AGENT.md`，所以你在聊需求的时候，AI 也会懂你整个的架构。基于这个架构：

*   1.
    
    先以**对话方式**跟 AI 聊需求
    

*   2.
    
    聊清楚之后，告诉它：「我要把我们聊的这些对话整理成一个需求开发的实施文档」
    

*   3.
    
    要求：这个文档要给基础开发人员使用，尽量让他们少问问题，拿着文档就可以开发
    

把这个要求给到 AI 之后，它就会给你整理出一份非常详细的文档：

![](https://article-images.zsxq.com/FsRZIK5O_WsBs29o-QbTQWWitNRa)

  

这个文档基本上写完都在 **1000~2000 行**之内，因为写得非常清晰。再结合这个文档，你直接就可以把它生成 `prd.json`。

### 执行效果

这样去做效果会非常好。整个操作下来，18 个小时做完之后，我审核整个文档 + 聊需求一共花了大约**一个半小时**。

并不是说让 AI 完全自动去做，你必须要了解项目的结构。基于这个项目结构把 PRD 做好，把需要描述的功能让 AI 做一份详细的设计文档。所以它跑起来效果就非常好。

![](https://article-images.zsxq.com/FvQ6RArHaiWecjK0R5fD26HDSf0d)

  

* * *

## 六、重点信息：长任务循环的关键配置

这里还有一个重点信息：当你让循环自动跑的时候，有一个 `CLAUDE.md` 文件，你需要在这个文件里明确指示：

**如果做 story 时哪块不清楚，要去看这份主文档。**

因为这份主文档（也就是前面提到的 1300 多行的需求开发实施文档）是你认真审核过的、用于理解需求的主文档。你的 story 也是基于这个种子文档拆分出来的。

### 为什么要这样做？

*   如果 AI 不懂，让它去看种子文档
    

*   这份种子文档的定位是：**基于一个基础开发人员不用反复问你的前提下写成的**，所以它写得非常清晰
    

有了这个配置之后，长任务跑起来效果就是非常好。

* * *

## 一、背景：一次 18 小时的大任务

昨天已经跑通了 1 个 18 个小时 + 的大任务。这个任务里涉及到了 30 个 story，足足花了 3 亿多个 token。

![](https://article-images.zsxq.com/Fj7cmWhb_6jA-c5Cfnrq3s9MutcC)

  

**GLM Token 费用：**

![](https://article-images.zsxq.com/Fr5C-Z5qeK-OxqjyBAZWYYtSYd-W)

  

* * *

## 二、核心议题

今天想跟大家分享的是：**一个多子任务的项目构建，要怎么合理地、以最佳方式去使用 AI 自动化 Coding 2.0 这个项目**。

关键在于：**你需要把整个工程做好**。

* * *

## 三、工程结构推荐：GSD 1.0

这里工程结构的整理，我给大家推荐的是 **GSD 1.0** 的项目结构：

*   **源码**：[https://github.com/gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
    

*   **安装**：`npx get-shit-done-cc@latest`
    

安装之后，就可以放在你自己喜欢的 IDE 下面。它其实是一组 skills 或者说 commands，本质上就是一组提示词。

### 关键提示词：`/gsd-map-codebase`

它可以将我们整个老项目的架构梳理得非常清晰。

运行之后，它会产出关于项目结构、技术栈、框架等相关的内容，梳理得非常清晰。你大概审一下没有问题的话，这个生成内容就可以作为我们**第一版的 harness 工程**。

想跟大家聊这个，是想说：**无论是老项目还是新项目，让 AI 在做 Coding 的时候理解你的项目结构，这是非常关键的。** 所以它可以作为我们初始项目结构的说明书。

![](https://article-images.zsxq.com/FnusCKbWpIsBp_Beybh133VtZnib)

  

* * *

## 四、多子项目场景（今日重点）

今天更想跟大家讲的其实是**多个子项目**的情况。因为很少人只会用到一个子项目——即使是前后端分离，也是两个子项目；如果使用微服务架构，可能会有更多子项目。

### 实际案例：企业 AI 咨询项目

我最近在给企业做 AI 咨询顾问, 并给他们做些实施研发的工作，我们在做的技术栈选型是：

*   **后端**：使用若依平台（包含 2 个子项目）
    

*   **前端**：使用 React（1 个业务前端子项目）
    

相当于一共有 **3 个子项目**。

### 处理方式

你可以把每一个子项目按模块划分，让 GSD 去把结构读一遍，从而为每个子项目产生一份 codebase 说明：

![](https://article-images.zsxq.com/FiEw-yA8zzbGXRXd751RkqefdgCS)

  

### 合成总说明书

有了各子项目的 codebase 说明之后，你需要把它们合成一个**大的说明书**。这个大说明书可以指导 AI：

*   当你去改若依的时候，去读哪些 codebase 内容
    

*   当你去做业务前端的时候，去读哪些 codebase 内容
    

![](https://article-images.zsxq.com/Fn1YZQThhXou3rU94ChOKXKOwcQC)

  

这样整个 map 的初版就有了。后续如果系统架构再更改，我们可以陆续在这个 maps 里补全、逐步完善。

### 三层文档结构

这样你就会有一个**根路径**，这个根路径会把前后端的结构 maps 和项目整体规则的入口文件都描述清晰。

描述清晰之后，再去做 AI 自动化 Coding 时，AI 就可以很好地理解这个项目，不用把项目的所有说明文件全部读完。**说明文件分成了三层**：需要更改哪部分时就去读哪部分。

这样：

*   上下文的获取会更加精准
    

*   写起来会更加顺利
    

![](https://article-images.zsxq.com/Fh0bNF8R8e2RTwsXZOX3bsSHKJWu)

  

* * *

## 五、PRD 的重要性

除此之外，还有一个**最重要的点**：你要在做 PRD 的时候，把它做得非常非常清晰。

因为你已经有了 `AGENT.md`，所以你在聊需求的时候，AI 也会懂你整个的架构。基于这个架构：

*   1.
    
    先以**对话方式**跟 AI 聊需求
    

*   2.
    
    聊清楚之后，告诉它：「我要把我们聊的这些对话整理成一个需求开发的实施文档」
    

*   3.
    
    要求：这个文档要给基础开发人员使用，尽量让他们少问问题，拿着文档就可以开发
    

把这个要求给到 AI 之后，它就会给你整理出一份非常详细的文档：

![](https://article-images.zsxq.com/FsRZIK5O_WsBs29o-QbTQWWitNRa)

  

这个文档基本上写完都在 **1000~2000 行**之内，因为写得非常清晰。再结合这个文档，你直接就可以把它生成 `prd.json`。

### 执行效果

这样去做效果会非常好。整个操作下来，18 个小时做完之后，我审核整个文档 + 聊需求一共花了大约**一个半小时**。

并不是说让 AI 完全自动去做，你必须要了解项目的结构。基于这个项目结构把 PRD 做好，把需要描述的功能让 AI 做一份详细的设计文档。所以它跑起来效果就非常好。

![](https://article-images.zsxq.com/FvQ6RArHaiWecjK0R5fD26HDSf0d)

  

* * *

## 六、重点信息：长任务循环的关键配置

这里还有一个重点信息：当你让循环自动跑的时候，有一个 `CLAUDE.md` 文件，你需要在这个文件里明确指示：

**如果做 story 时哪块不清楚，要去看这份主文档。**

因为这份主文档（也就是前面提到的 1300 多行的需求开发实施文档）是你认真审核过的、用于理解需求的主文档。你的 story 也是基于这个种子文档拆分出来的。

### 为什么要这样做？

*   如果 AI 不懂，让它去看种子文档
    

*   这份种子文档的定位是：**基于一个基础开发人员不用反复问你的前提下写成的**，所以它写得非常清晰
    

有了这个配置之后，长任务跑起来效果就是非常好。

* * *

![](https://articles.zsxq.com/assets_dweb/logo@2x.png)

知识星球

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join_group.html?group_id=28882285418421