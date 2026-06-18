---
title: "Obsidian+OpenClaw组合技！花9分钟重构你的AI知识管理体系"
source: "https://mp.weixin.qq.com/s/YmySPzCuQ_-PPCuCdZ1NDg"
author:
  - "[[AI沃茨]]"
published:
created: 2026-03-02
description: "真正意义上的全流程覆盖，我做到了"
tags:
  - "clippings"
---
![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/VNz1x8bH8FzxaL0dqIwCic8Bq56ibNxaS1EEicqHMAbxz5AwzhzQ9r3GRKZIvvDjLxtYEY7P3X7iad0W95tRgBqhMrQ6sexlYj9bKA88wiaEgrzQ/0?wx_fmt=jpeg)

原创 AI沃茨 [卡尔的AI沃茨](https://mp.weixin.qq.com/s/) *2026年3月2日 18:24*

三周前我决定迁移到Claude Code+Obsidian，

这其实挺难的，我常用的搭配是所有信息都走微信发到滴答清单上，这个兼容度巨高。形式能走链接都是链接，群聊信息等多文本行难复制就做成截图。每条信息留一句信息用途，是选题还是深入学习。

但这有个很无解的缺点，

我只是把知识点从一片海转到一个湖里，过几天我还是要收录到飞书，文本信息做去重，视频做文案提取，做内容的话还要做排期等等。

要完全无痛迁移到Obsidian上，我先要找出两个问题的答案，

- 怎么让信息流动到Obsidian里
- 怎么让Obsidian里存的信息有合理的结构，让AI和我都可以看懂

这篇文章的超高速打开方式是全篇丢给OpenClaw，把需要安装和配置的半自动搞定😎

![Image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/VNz1x8bH8Fz561Qibt8O37bDkzBqQUw20M5ZJnQN8d4X5lyOqRnw3ibBRIBolncvBdnBs3MYBIGqIkibYACnkzxu1Kj4ynZZVEIb2ra123Riafg/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

我先讲讲我对文件结构的选择，

本质上你可以把obsidian看成一个大的markdown文件阅读器，它有超级丰富的插件体系以及可以内置的Claude Code，也叫Claudian。这个Claudian我后面换成了Codex App，有更好的表现和对话管理水准。

Claudian限制了打开的对话数量是三个，而且没有可视化的定时任务管理，这两个是我换成Codex app的主要原因，如果你在想怎么从 Claude Code迁移记忆到codex app 的话，只需要把本地的Claude.md复制一份到同目录的Agent.md文件里面就可以了。

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8Fwfq3eItu94hh6WHUQTgIiaiaSicl4icfiakglXBANKAak0G8iaQOF9icAss0nAQyiabJAWU6j1SSuhMLaj12x886fpwcz7O1czPlia5HdE/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

我们还是从安装开始，

🔗 obsidian.md

![Image](https://mmbiz.qpic.cn/mmbiz_jpg/VNz1x8bH8Fz9Aib15WJHWLNjwp491rJeQCicTUwfezUtiaGaEibYUia90Keutj2kZphappDuVichawCqSkpSJddrfzuNcbg4aw2BQscBmSIfYIXQ0/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

刚装上的Obsidian就是个纯素的阅读器，所以我们要先安装一些必要的社区插件，

Claudian（相当于把本地Claude Code内置到侧边栏了），笔记同步助手（这个有大用，是让Obsidian能同步微信消息的插件），Image auto upload（有选择性降低存储压力，将笔记图片通过picgo上传到github），ObShare（将文件上传同步到飞书，方便分享给团队）。

不需要手动安装，直接Claude Code或者Codex App上，输入插件名字就行。

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8Fx1GZV5CJiaAPOHEBShicuoZkbKsJjSeWY0626Ltia5UKYDt4hFxPr53X1K1jkxIibJiaAaHicyGOialSmtkzs3kqFjxrZqFqicjlMqkdI/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

在文件同步的选择上，我直接把Obsidian的文件目录放在了icloud上，这样不需要我设置定时同步。

Claude Code本身的安装看我之前做的教程就好，不然一篇放不下，也可以用Codex app，这个不需要配置。

[我把新版Claude Code的上手门槛降到小学二年级，有豆包就行](https://mp.weixin.qq.com/s?__biz=Mzg3MTk3NzYzNw==&mid=2247504014&idx=1&sn=707d2bc299e71b7d409e324a23570706&scene=21#wechat_redirect)

内容迁移到这一步我遇到了一个大问题，

所谓的适合Obsidian+Claude Code记忆的文件系统太多了，我在github搜能出来5千多个项目，还有一个非常容易被混淆的概念，就是这个文件目录是要跟Claude Code搭配的，不然记不住内容。

错，大错特错，

我目前遇到的情况，只要在批量移动或者修改文件的时候让模型录入到自己的memory，或者将重要的路径和每次启动需要阅读的记忆文件写到Claude.md就好了，Claude Code新开对话的时候会默认读的。

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8FyL6OcMUfeibiaVbcCdTCLqACMej6hibBLmsnrkAwoyJdbdDWZxbJuRX6pTMvBlReXMHkcDgibFsa53kJedYOlMAWqMFX68Db6hrY8/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

所以我这个文件目录是在github上 MarsWang42/OrbitOS 的基础上融合了 heyitsnoah/claudesidian 的metadata目录（用来存放提示语和工作流模版），我还限定了每次对话结束的时候主动更新知识。

我用下来最大的一点体会就是不需要过度担心AI记不住，你可以通过限制AI写文件目录的深度，我设定的是3层子目录，这样后面我发现AI有忘记文件时就把这个目录路径和用途重新写入到记忆文件里。

Claude Code在侧边栏的好处就是我们可以用各种形式的方式迁移我们的数据，比方说zip，图像，链接，pdf都可以先放到收件箱，然后让模型出一个整理计划给我。

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/VNz1x8bH8FyTx9LWsUtfiao0RT8xm6TLZQCG6AsfrHZ24YfGJxia6MiciczibcqZkQiasyvoRnZ5wEP1kqw9j6ettpnKlHEZCpRBHiahyTC0KicJ4ZE/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

把信息收录到Obsidian的方式就分为三大类，

插件，微信和OpenClaw（专门啃难解析链接和视频）

![Image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/VNz1x8bH8Fw4sQL0AlcuMk9YabnnhzDibtoeRd0bCIzgyI3ZiaRXKQtw0b9eFBp13Po67Bia8rGshQQJQ2QVicZjQ41AeWAKhwvWA3Pq71cwBVU/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=6)

GPT导出到Obsidian这个就是专门让Claude Code快速生成一个USER.md来记住你的，后面OpenClaw也能用上。Obsidian Web Clipper和HoverNotes就是针对网页端的，连公众号和看视频做的笔记都可以剪藏到Obsidian里面。

有时候会有点问题就是图片没有完全获取下来，但笔记本体同样是保留了原链接，我觉得爬再烂都能跟我之前一个个复制到滴答的效果要好，抓X的时候还可以把评论区抓下来。

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8FwWze8JggWFEXicTCicTdibLdicSxbcTm0M8oc9n2KHnqjfVNA3vL7gXWxicbwyvH3AkDYUyicXN3P4PPXU9iaY4hpLUsc6Wqdia3fmjwU/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

手机端我本来还用codex app辅助做了一个快捷指令，可以把信息按照收录的时间自动分流到不同的文件夹，但是这个共享表单接收不是所有情况都可以生效的，到这一步我就有点怀念微信+滴答了，我是不是要回老路，先把信息收录到软件A，再放到软件B。

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8FxPhhR8uFnRMY7qIxib8K0oaU9KROhftL2UluPPejsuicpgCXzZZ7svf2MejV6USp8CmdpKx0oic9HRnBX63ZiaQLQBJU9ZrGrmGLY/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=8)

但是万能的Deep Reserach还是太全面了，

我尝试了Gemini，Grok和OpenAI的Deep Reserach后，还真的让我在微信上找到了一个有点小众的笔记同步助手，支持OneNote，Obsidian和Notion的笔记同步，可以把小红书视频做成图文笔记（这波这波是赚大了）

最后就是把OpenClaw跟Obsidian链接起来了，

其实OpenClaw是可以把上面信息录入和信息整理两步当作一步执行的，

![图片](https://mmbiz.qpic.cn/sz_mmbiz_jpg/VNz1x8bH8Fy1VXdPSSIRo5XwwsznDqa5M8LFTA7ovmJmpDxkOf3T1HS9dsvibnjsNjpia29FiasnIicGkEXNxSRoiawAWxpdofhgfAC0WfXburms/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

OpenClaw从零开始配置的教程我也写过了，

[Clawdbot超级小白入门指南，不靠MacMini和云，安全用上满血版](https://mp.weixin.qq.com/s?__biz=Mzg3MTk3NzYzNw==&mid=2247504469&idx=1&sn=529c3c44419ee375d0dbb3e2cb389058&scene=21#wechat_redirect)

这个时候就可以让OpenClaw给自己升级了。

1\. 联网搜索和链接解析（某书啊，某站啊，某X啊都可以）

帮我安装

x-reader： https://github.com/runesleo/x-reader

Agent Reach： https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

browserwing： https://raw.githubusercontent.com/browserwing/browserwing/main/INSTALL.md

  

2.Obsidian （这样OpenClaw才能写入Obsidian）

npx clawhub@latest install obsidian

  

3.find-skills （主动找Skill解决问题）

npx clawhub@latest install find-skills

  

4.proactiva-agent-1-2-4 （ 自我迭代的主动Agent）

npx clawhub install proactive-agent-1-2-4

![Image](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8FxUV9p8kZYVyd9TIMt9dfF9LPJkPyX9L9ZOgSvw7aCxvmsDSDzslwDhUEx1UUiaQvd6sQxOTx53JzegbyhI0ymxhicUrL81xqumw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=10)

最后的最后，是从 @摸鱼小李 那学到的，

帮我建一个 软链接 ，把你的工作区链接到我的Obisidian仓库里，建一个叫「OpenClaw配置」的文件夹。直接帮我搞定，路径是XXX

这样龙虾的核心配置文件就会出现在Obsidian的本地目录里，这样我们就可以在Obsidian里编写SOUL.md，OpenClaw会立刻生效。

![图片](https://mmbiz.qpic.cn/mmbiz_png/VNz1x8bH8FxER1C26PKghcMYfjVIeSB1J7rpAALR4bFXf0oLxmicCuqemGxxBkE9L21BA5mhw8UoOsONxWOQ3ndWLDBRs9aHF5L5jYibERGzA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=11)

OK，到这一步我们已经完成了信息的获取和自动整理，同时打通了Codex，Claude Code，OpenClaw和Obsidian。

后面我再单独出一篇OpenClaw的Obsidian专题，因为现在好用的Skills数量增加，多群组加多个OpenClaw实例的case越来越多，把Obsidian作为本地知识管理数据是当下最好的几个选择之一。

折腾信息管理就是不能太心疼信息损耗，

能存到本地的就尽可能做个备份，

图床会失效，链接会过期，

记录的方式尽可能越简单越好，文字是能存最久的。

用久了我发现同一份数据，

OpenClaw会划分总结沉淀出合适的知识点分开几个地方储存，

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/VNz1x8bH8FzVHiayrJtMDrS9nOlCaibbPFsIRWFHIBSJlJqicYVkvfEGp6fCqf7XuFy0rQ1KF0pPnvfs6IFEdMxL4IeEdyYSW10ia9W289BfXUo/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=12)

刚开始我不清楚为什么它选择这样做，

但是用下来发现它是对的，

我不需要时刻回顾信息的来源，我只管用就好了，

来源是AI自己记忆用的。

我想这就是跟AI共用知识体系才会有的独特体验，

在一次次对话的过程中，

我在编写它的技能和记忆，

它也在主动记录我的喜好，

我们都在无限进步。

