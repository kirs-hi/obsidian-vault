---
title: "【gstack-01】  超火工作流 gstack精讲office-hours"
source: "https://articles.zsxq.com/id_dc13uawlwrca.html"
author:
  - "[[AI随风]]"
published:
created: 2026-05-23
description:
tags:
  - "clippings"
---
[来自： AI随风的AI编程实战营](https://wx.zsxq.com/group/51115228418814)

## 工作流介绍

gstack是GitHub上非常火的一个工作流，目前GitHub的stars有60K，它涵盖了头脑风暴、计划、编码、测试、review, 然后自动学习，把所有的流程都串起来了，是一个非常适合学习的一个工作流。

开源地址： [https://github.com/garrytan/gstack?tab=readme-ov-file](https://github.com/garrytan/gstack?tab=readme-ov-file)

这次我在星球会开启一个系列，讲一下他这个工作里面的几个非常重要的技能

## 安装

打开 claude code, 输入下面的内容

install gstack: run git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack &&./setup then add a "gstack" section to CLAUDE.md that says to use the /browse [[skill]] from gstack for all web browsing, never use mcp\_\_claude-in-chrome\_\_\* tools, and lists the available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /retro, /investigate, /document-release, /codex, /cso, /autoplan, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn. Then ask the user if they also want to add gstack to the current project so teammates get it.

然后等他去安装就好了。

这个文档会介绍它的第一个技能，叫office hours。

## 技能全景简介

**office-hours (办公时间)** 是一个源自 Y Combinator (YC) 产品思维的超强诊断与头脑风暴技能。它拥有 Garry Tan 的产品和工程洞察力，核心理念是：“在写下任何代码之前，必须先证明这个问题值得被解决。”它提供了两种模式：

1. **创业者模式 (Startup Mode)** ：用 6 个极其尖锐的诊断问题（真实需求、现状、极度具体的用户、最窄的切入点等）对你的商业点子进行“灵魂拷问”，防止你做无用功。
2. **建造者模式 (Builder Mode)** ：面向业余项目、黑客松和开源项目，作为一个热情的“设计伙伴”，帮你激发最酷、最快落地的灵感。最终，它会为你输出一份严密的需求设计文档（Design Doc），并智能评估你的“创始人潜质”。

## 🎯 触发场景

1. 当你说出：“帮我想想这个点子（brainstorm this）”、“我有个想法（I have an idea）”、“办公时间（office hours）”或者“这个东西值得做吗？”。
2. 强烈建议在进行具体的工程规划（如 /plan-eng-review）或写任何一行代码之前使用。它能帮你将长达数月的弯路扼杀在摇篮里。

![](https://article-images.zsxq.com/FnpPgaCXcd_5tThYziAjcl-75_nt)

在你向他阐述你的一个想法、一个点子的时候，他会站在多个角度，比如说是创业者还是只是玩一下，还是只是一个hackathon/demo的项目来选择不同的角色的话，然后他们根据这个角色来去向你问问题。

这是这是目前市面上的流程里面非常少有的，能够从不同角色来审视你这个点子或者说想法的正确性。在AI编程的时代，我们可能每天都会有想法，但这个想法能不能做，怎么去做，非常需要有专业的眼光来给你去判断。所以第一个技能主要是做这个事情来帮你对齐需求，用专业的角色的角度

那么我现在演示的这个就是我的一个想法，做一个儿童教育的一个APP

## 🗺️ 全局核心流程图

![](https://article-images.zsxq.com/FvpgxUMZP1i7OYcdqQzhSCWmO8D9)

## 👣 主线流程步骤详解

1. **环境准备与背景调查** ：技能启动后会默默加载工具配置。接着它会调阅你的代码提交记录和相关文件，并 **问出最关键的一个问题** ：“你做这个的目的是什么？”（创业？黑客松？还是随便玩玩？）。这个回答将决定接下来的路线。

![](https://article-images.zsxq.com/FnpPgaCXcd_5tThYziAjcl-75_nt)

![](https://article-images.zsxq.com/FrlBWORT3d093Wqtj4SedtuX91sA)

![](https://article-images.zsxq.com/FvNr3LssUZcPhy6c5qwD0bSvFxyy)

1. **硬核诊断（分路线进行）** ：
2. **路线 A（创业者模式）** ：不会给你鼓掌，只会给你泼冷水。它会用 6 个致命问题逼问你：有没有人真的愿意付钱？他们现在是怎么将就对付的？你能把产品切得有多小？通过极其尖锐的追问，挤出“假大空”的伪需求。
3. **路线 B（建造者模式）** ：变成一个充满激情的合伙人，跟你一起大开脑洞：“怎么做才是最酷的？”、“怎样能最快做出来炫耀？”。
4. **“第二大脑”与盲区探索** ：
5. **全景搜索** ：它会请求联网搜索目前市面上解决这类问题的常规做法，用来挑战你的点子。
6. **前提挑战** ：再次向你确认：我们真的在解决正确的问题吗？如果不做会怎样？
7. **外援审查（可选）** ：如果授权，它会调动另一个完全独立的大模型（Codex 或 Claude 子代理）来“冷读”你们的对话，挑出你的盲点并给出一个完全不同的原型建议。
8. ![](https://article-images.zsxq.com/FqNu5xfytTVBoYW5hSqz4ARUFAso)

在这一步的话是会启用比如说别的模型，如果你装了codeX, 那么它会启用codex的这个模型去审视你的这个问题，或者说用claude code的里面的子代理去审视你这个问题，从不同的角度来看这个需求是不是有不合理性。

所以这个设计也是非常巧妙的，避免了一个模型去设计，同样一个模型去review这样的百分之百正确性的错误

1. **强制给出多套方案** ：绝不只走一条路。它会被强制要求给出 2-3 种不同的实施路径（比如：最精简版、理想架构版、或者脑洞大开版），并指出各自的利弊。

![](https://article-images.zsxq.com/FmHmEI8j22K1MNyoDfXABErwHxAx)

1. **视觉草图探索** ：如果产品有界面，它甚至会利用 HTML 在后台渲染出一个极简的线框图给你看，并请求设计子代理提供美学建议。

![](https://article-images.zsxq.com/FjZwE8Q2hN0DgwGi8vJRSaXUzu5b)

![](https://article-images.zsxq.com/Fv7iitu9f7HPF3rLV73Oxt66CU2N)

在这个环节，他会给出一个原型的页面，这个环节我觉得是非常非常有意思，非常有创意。他跟你聊完了之后，大概对你的需求有有所理解了，他就会设计出一个草图来告诉你，是这样的一个设计方案，然后你同意之后，他会把这个方案落实到文件里面去。那后面你的UI可能会根据它这种结构来去做深入的这个优化，这个也是非常少见的

1. **落笔成文与极限审查** ：一切敲定后，它会生成一份结构严谨的需求文档（Design Doc）。接着它会派出一个\*\*黑脸审查员（子代理）\*\*去给这份文档挑刺（查漏补缺、检查矛盾），并在后台自我修复，最多迭代 3 次！

![](https://article-images.zsxq.com/FqsKgbsysxm5vgamTDirECQ8dtzF)

最终文档到这一步的时候，他还没有好，他还需要再做一次对抗性审查，也就是说再叫一个代理过来去看一下这个文档是不是有问题，查缺补漏，检查矛盾，所以说非常严谨，整个过程。

1. **创始人评级与专属信件** ：在全流程结束时，它会回顾你在整个对线过程中的表现（例如：是否描述了真实用户？是否能有理有据地反驳 AI？）。根据这些“创始人信号”的浓度，它会向你展示一段来自 Garry Tan（GStack 创始人）的不同口吻的个人寄语，甚至会怂恿你直接带着这份文档去申请 YC！

## 🧩 核心子代理深度拆解

为了保证诊断的客观性，这个技能在执行过程中会动态分发并召唤多个“外援”子代理（Subagents）加入战斗：

### 1\. 跨模型“外侧”顾问 (Cross-Model Second Opinion Agent)

1. **角色设定** ：一位从未参与你们讨论的、绝对独立的技术顾问。
2. **核心职责** ：在你们聊得火热时，作为局外人给你们浇冷水或提供灵感。
3. **它是怎么干活的** ：主技能会将前面沟通的问题、背景和你的回答整理成一份摘要丢给它。它会无情地挑出你假设中最脆弱的一环，或者给出“如果是我，周末花 48 小时我会用什么技术栈先做一个什么鬼东西出来”的极端建议。这能极大地拓展你的思路。

### 2\. 视觉美学指导员 (Design Voices Agent)

1. **角色设定** ：UI/UX 设计专家。
2. **核心职责** ：在定下技术方案后，为枯燥的功能注入灵魂和美感。
3. **它是怎么干活的** ：它会看着确定的功能，提出一个“视觉主张（Visual Thesis）”，并给出具体的排版建议、交互动效甚至直接指定应该用什么字体和十六进制的颜色色号。

### 3\. 文档极限审查员 (Spec Reviewer Agent)

1. **角色设定** ：鸡蛋里挑骨头的 QA 质检员。
2. **核心职责** ：审核主技能生成的 Markdown 需求文档是否无懈可击。
3. **它是怎么干活的** ：它不会看你们前面是怎么聊的，它只看最终的文档。它会在 5 个维度（完整性、一致性、清晰度、范围克制、可行性）上打分。一旦发现有自相矛盾、或者可能导致工程师懵逼的模糊描述，它就会立刻打回让主技能重写。如果连续 3 次没改好，它会把问题作为“已知隐患”强行附在文档末尾。

## 总结

当你有一个想法，你有一个很好的点子的时候，你可以用office hours去开启gstack的工作流，他这边可以设置不同的维度，不同的角色来去帮你去丰富你的文档，而且最终会给出一个设计草图，那么在这一步给到的信息是非常丰富的。那接下来我会继续讲解他的第二个技能，也就是CEO review和这个engineer review也是非常重要的

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51115228418814