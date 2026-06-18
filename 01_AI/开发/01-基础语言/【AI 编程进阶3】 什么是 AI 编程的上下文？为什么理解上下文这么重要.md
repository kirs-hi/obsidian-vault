---
title: "【AI 编程进阶3】 什么是 AI 编程的上下文？为什么理解上下文这么重要"
source: "https://articles.zsxq.com/id_vu8wxh6qk9dl.html"
author:
  - "[[AI随风]]"
published:
created: 2026-05-23
description:
tags:
  - "clippings"
---
[来自： AI随风的AI编程实战营](https://wx.zsxq.com/group/51115228418814)

这一节，我们来讲 AI 编程里一个非常重要的概念： **上下文（Context）** 。

你可以这样理解：

模型能力的发展，除了模型本身越来越强，另一个非常关键的方向，就是 **支持更大的上下文** 。

而 [[07-Agent|Agent]] 工程的发展，本质上也一直在围绕“如何更好地管理上下文”不断进化。

比如：

1. **Skills** 的出现，是为了更节省上下文
2. **子代理（Sub-agent）** 的设计，是为了隔离不同任务的上下文
3. 各种工程化的方法、规则文件、记忆机制，本质上也都是在优化上下文的使用效率

所以，上下文不是一个小问题，而是 **AI 编程效果好不好** 的核心因素之一。

那么：

1. 上下文到底是什么？
2. 它为什么这么重要？
3. 在实际开发中，我们应该怎么优化上下文？

这一节，就带大家系统了解一下。

## 一、理解什么是上下文

## 1、没有上下文

![](https://article-images.zsxq.com/FlJ8FDKAxJjxM6YT9WdV-oiQ7ukJ)

如上图所示，在没有上下文的情况下，大模型不会记住你前面的对话。

你刚刚问过的问题、它刚刚给过的回答，下一轮它都可能“忘掉”。

也就是说，如果没有上下文，大模型每次都像是在“重新开始”，它只能看到你当前输入的这一句话，无法理解之前发生了什么。

所以，没有上下文的大模型，几乎不具备连续协作能力。

## 2、有上下文

![](https://article-images.zsxq.com/FjszrShRRuqTIXufmDGKVLaDlW30)

而在有上下文的情况下，你和 AI 的每一次对话，都会以某种形式被纳入上下文中，再一起发送给模型。

这样，大模型在接收到：

1. 你的最新输入
2. 历史对话信息
3. 当前任务相关信息

之后，才能知道：

1. 你现在在做什么
2. 前面聊到了哪里
3. 它之前给过什么方案
4. 当前应该延续什么思路继续回答

## 二、上下文为什么不能无限增长？

那是不是可以把所有历史记录一直保存，然后每次都发给大模型？

答案当然是不行。

这背后主要有两个原因。

### 1\. Token 成本

上下文越长，每次请求发送给模型的内容就越多，消耗的 Token 也就越多。

而且很多历史内容，其实和当前任务没有直接关系，如果全部带上，不仅增加成本，还会造成浪费。

所以，任何一款成熟的 AI 编程工具，都会尽量做好上下文的管理和压缩。

否则：

1. 用户调用成本会很高
2. 模型响应速度会变慢
3. 最终效果也不一定更好

换句话说， **上下文不是越多越好，而是越精准越好。**

### 2\. 模型本身有上下文长度限制

大模型并不是可以无限接收输入。

每个模型都有自己的上下文窗口上限，也就是它一次性能处理的最大内容长度。

这个长度越大，通常意味着模型能同时参考更多信息。

但无论窗口有多大，它始终是有限的，所以“[[理论学习_上下文压缩与_Token_管理|上下文管理]]”永远是一个绕不开的问题。

## 三、上下文的组成部分

既然上下文这么宝贵，那么在上下文中放什么内容，就变得非常关键了，虽然各个[[2026-03-02-AI编程工具|AI编程工具]]设计思路不一样，但是上下文的信息的组织大部分都是一样的。

上下文组成部分

![](https://article-images.zsxq.com/Fl5APe9ZnOpBZ18vtYOdHo8tTcqA)

看下 [[Claude Code 命令与最佳实践|Claude Code]] 的上下文组成部分

![](https://article-images.zsxq.com/Fm9P3wHNJKS3WtBBzVUQ9gDIt40q)

## 四、为什么上下文质量会直接影响 AI 编程效果？

上下文的容量是有限的，但里面可能要放很多东西：

1. 项目说明
2. 规则文件
3. 技能描述
4. [[理论学习_MCP_协议与开放工具生态|MCP]] 工具说明
5. 历史对话
6. 自动记忆
7. 当前任务内容

当上下文越来越拥挤时，模型就更容易出现下面这些问题：

1. 回答变慢
2. 理解偏差变大
3. 忘记前面的关键要求
4. 抓不到重点
5. 输出质量下降

尤其当上下文使用量已经接近 90% 甚至 100% 时，模型的反馈质量往往会明显下滑。

所以，学会主动优化上下文，是 AI 编程里非常重要的一项基本功。

## 五、优化上下文的常用办法

下面这些办法是我在实战中经常使用的

### 1、经常更新 Claude.md/Agents.md

把那些 **经常出错、经常需要重复提醒模型的内容** ，提炼出来，写进 Claude.md 或 Agents.md 里。

这样做有两个好处：

1. 模型更容易稳定执行你的要求
2. 你不需要每次都重复沟通

本质上，这也是在优化上下文。

因为你把重复性的沟通，沉淀成了更高质量的长期上下文。

### 2、新的任务重新打开一个对话，或者使用/clear 清除上下文

当你完成上一个任务，准备开始下一个任务时，如果这两个任务之间关联很小，甚至没有关联，那就不要硬接着聊。

你可以选择：

1. 直接开启一个新的对话
2. 使用 /clear 清除当前上下文

这样做的好处是：

新的任务会运行在一个更干净、更聚焦的上下文里，模型更容易抓住重点。

### 3、遇到卡住的问题，要及时重开

如果大模型在一个问题上反复兜圈子，始终解决不了，说明当前上下文很可能已经“脏了”。

比如：

1. 前面走错了方向
2. 中间出现了错误假设
3. 模型不断沿着错误思路继续推理

这时候，我非常建议你直接开一个新的对话，把问题重新描述一遍，再让模型重新开始。

很多时候，换一个干净上下文，成功率会明显提高。

### 4、使用子代理

对于那些：

1. 运行时间比较长
2. 和主任务关系不大
3. 可以独立完成的工作

非常适合交给 **子代理** 去做。

比如：

1. Code Review代码审查
2. 生成文档
3. 制定计划
4. 修复某个独立 Bug

这些任务通常不需要持续占用主代理的上下文。

交给子代理之后，它会在自己的独立上下文中运行，不会污染主代理的上下文空间。

这是一种非常有效的优化方式。

所以在开发过程中，一定要经常思考：

**这个任务能不能拆出去，让子代理单独做？**

### 5、去掉不必要 MCP

很多人现在会装很多 MCP，觉得“装得越多越强”。

但实际上，在日常 AI 开发中，真正高频使用的 MCP 往往就那么几个。

多余的 MCP 会带来两个问题：

1. 占用上下文
2. 增加模型选择工具时的干扰

所以你现在就可以检查一下：

有没有一些 MCP，你其实很少用，甚至已经不用了？

这些都应该及时清理掉。

**不是 MCP 越多越好，而是越合适越好。**

### 6、去掉不必要的技能

技能也是一样的道理。

很多技能在安装或创建时，会被放到全局目录。

这样一来，即使当前项目并不需要它们，它们也可能会被纳入上下文，增加额外负担。

尤其是一些很个性化、很场景化的技能，如果长期挂在全局里，其实会不断消耗上下文资源。

所以更好的做法是：

1. 清理掉不再使用的全局技能
2. 尽量把技能安装到具体工程目录中
3. 让技能只在真正需要的项目里生效

这样，上下文会更干净，模型的判断也会更准确。

## 六、总结

上下文，是 AI 编程中最核心的基础能力之一。

你可以把它理解成大模型的“工作记忆”。

模型能不能持续理解你、配合你、延续任务，本质上都依赖上下文。

所以我们在实际开发中，不只是要关注：

更要关注：

1. 当前上下文干不干净
2. 有没有放入真正重要的信息
3. 有没有及时清理无效内容
4. 能不能通过规则、技能、子代理等方式，提高上下文利用效率

当你真正开始重视上下文之后，你会发现：

很多 AI 编程效果的差异，往往就出在这里。

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51115228418814