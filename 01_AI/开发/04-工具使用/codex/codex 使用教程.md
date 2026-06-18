> 本文由 [简悦 SimpRead](http://ksria.com/simpread/) 转码， 原文地址 [mp.weixin.qq.com](https://mp.weixin.qq.com/s/5kgVdLNABViv8uAnD0M6Ag)

最近 Codex 的热度，真的感觉直线飙升。

社群里一直有人问，什么时候出新的教程。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqWpGfQBLdfyREdYGGEX1x9QzwdyOBctEAve8P948z5NoH7PicfXOibXYzCvhia61M3tbpvtazVLJmGmUHgu7aO6xlepwVANx5jyCg/640?wx_fmt=png&from=appmsg#imgIndex=0)

我其实在二月份的时候，写过一篇 [Codex 的教程](https://mp.weixin.qq.com/s?__biz=MzIyMzA5NjEyMA==&mid=2647679828&idx=1&sn=6e1c0a935c70c566ee765c02a36327a6&scene=21#wechat_redirect)。

但说实话，那时候的 Codex 热度很低，而且几个月过去，那时候跟现在开启了爆更模式的 Codex 比，几乎是两个产品了。

所以我觉得，是时候重新给大家写一篇更加全面的 Codex 教程了。

带大家全面的了解一下这个我现在觉得最牛逼的 [[07-Agent|Agent]] 产品之一。

我也准备用两个比较有手就行的例子，用一个网页和一个 App，来串起这一整篇教程。

跟着做，相信你们也能实现。

![](https://mmbiz.qpic.cn/mmbiz_jpg/2jjfQoZLoqWVHfyQpTgMHJeqK8goR3fHA6HSvicjx5WKoSMicymicTMoIiaicsiaEtaCkecTBcWjBNQQHTImWTF9HqtpRGsjibUdMDjZmkNy23WXtI/640?wx_fmt=jpeg&from=appmsg#imgIndex=1)

好，废话不多说，我们直接开始。

**一. 安装 Codex**

一切的前提，当然就是有魔法和 ChatGPT 账号了，这个我们就不管了，大家只能自己去想办法解决。

然后，我们可以直接去 OpenAI 的 Codex 官网下载安装。

链接在此：https://chatgpt.com/zh-Hans-CN/codex/

Mac 和 Windows 都有。

我来用 Mac 做个演示。

点击下载安装。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqW1gflOHYvNDuYjmmwf5p88ogXib0G6m13tLXZKnNzuIOdlLX58ufJuDST7MUkbyWxg3YfHj8vAhZHPF0ZKqUmzEbp3xcick85Gg/640?wx_fmt=png&from=appmsg#imgIndex=2)

然后正常打开，进行登录。

Codex 的额度是跟你的 ChatGPT 会员相关的，我自己一般是 100 美刀的会员，200 刀的在 Claude 那边，如果你比较轻度的话，20 美刀的其实也勉强能用。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/2jjfQoZLoqWJC96elHfibghm5hf8E194qbSHgz9xMO1sDlsC7GEAYdwCP3pX2ENpzAABuwjx67uAGku5ZDVONeXBOvWzyc8qIDVIaxfrkTO0/640?wx_fmt=jpeg&from=appmsg#imgIndex=3)

也可以使用其他方式使用 Codex，比如 API key，这个就看大家自己了。

![](https://mmbiz.qpic.cn/mmbiz_jpg/2jjfQoZLoqWYhX1U4eomO1XKljSibO831cRqGt0Y8VCsOmFBZfVMbSPxgebELtxjTtJORIxibibOaiaY94nJy534dmU0dAMyDJJZ2APqHHd6jnM/640?wx_fmt=jpeg&from=appmsg#imgIndex=4)

登录之后，这里根据你的情况随便选一个，或者跳过也行。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVz5twZAOH7IbcKfJzK4TKpel83meib2lSSibeuicjfahiauXicY1bTtCeuiabTW33JUy1NeDiaGibo4icrl6z2iaSv71qKtLia6I7QFKUjp4/640?wx_fmt=png&from=appmsg#imgIndex=5)

接下来，最骚的来了，你可以从 [[Claude Code 命令与最佳实践|Claude Code]] 和 Cowork 直接导入所有的内容。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqWeiamlMMNZPS9sP8yC3g0uU0840N0yoavUMQzXc80ibQ4H7TwvOHE3vcibGicpKFPzwNgmZfZby0gpnkoISXNVblqjjEU2ibr1W4XM/640?wx_fmt=png&from=appmsg#imgIndex=6)

Codex 不光天天重置额度喊你来用，还能帮你搬家，一键继承之前的全部配置。

之前 Claude 支持导入记忆来挖 ChatGPT 用户，现在 Codex 直接反手一刀挖你 Claude Code 用户，你就说爽不爽吧。

我都想给它鞠个躬。

根据你的需求进行选择后，你就能进入到界面里面了。

**二. 认识界面**

进来后，界面长这样。

我先带大家快速认识一下各个区域。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqV1hVslLdiaPQRePanFkNw2ywDyp2sJjFCPiaQCJS3qluMuz84gavGojL6UKgticrdibOGo8Af6fpDCgGjicm0ZeoYWz9tjLKe8eZKw/640?wx_fmt=png&from=appmsg#imgIndex=7)

中间这一大块，就是我们平时的对话区，跟平时用的 AI 聊天差不多。

左边栏是来管理你的所有对话和项目。

这里分两个目录，一个叫对话，一个叫项目。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqWAoeshMyEXL3ZWpgAgJau6hRXKGicWsCojgP3aicpLMA0iaw37ezWS8MiaWrtutGrNropIutUk2vN0A5mNw54wLunSpgOWnsibbdTU/640?wx_fmt=png&from=appmsg#imgIndex=8)

对话适合不需要绑定到特定文件夹的任务，比如做做调研、做做规划，这些零碎的小任务里。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVEn27ZMqmCfictg1Dnuibb69Usgrics04icpdOs31kgibcOCqYCXswgR2RsGdHqfZEc0xdEJrpk0xogu9jezcwicEsXHmu6IEdV1HYo/640?wx_fmt=png&from=appmsg#imgIndex=9)

项目才是 Codex 真正的主战场。

选一个本地文件夹作为项目目录，Codex 就会以这个文件夹为工作区间，所有生成的文件都会自动存进去。

一个项目里可以开好几个对话，每条对话就是一条独立的任务线，它们共享同一个文件夹里的文件，但记录互相隔离。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVEuichXXaAZZdppB9zVg1jia9a6pKN7DO42a95APxozCLEvibfFvOVPh3rvzkDCWeicML8nPS6TPSJ0ZEwZr7HzaCiaHbHGzm6yHc0/640?wx_fmt=png&from=appmsg#imgIndex=10)

如果你所有事情都堆在同一个对话里，记录越来越长，上下文污染会很严重。

所以最好的是，同一个方向的任务放同一个项目，具体的每件事开一条新对话去推进。

说到这我真心建议一句，前期的分类我是真的觉得挺重要的，不然到后期，真的会很抓狂。。。

我们可以在左侧项目这边点击这个加号新建文件夹，或者使用一个现有的。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqW6dEtN1SNeUjBjibibK6MxYfjibBqTia7kIO7M7YHTPbN4tgfUJibuu2Hbia4NUczI67ntJlFrmiaF1iaW1xHCbp42tyAzBCZbpcdpy6U/640?wx_fmt=png&from=appmsg#imgIndex=11)

然后，你就进入到了一个具体的项目里，也能看到对话框有变化了。

然后在对话框左下角有三档权限选择。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXnEVJ9oWk4JYroK7K6jCVfv7cJLL3SLTNCYic7wXfSS5ichyRnGRrgmCrXuqJ8blEbBt6sCKsJewOQmibrVTqFWibkYJZn3DtduK0/640?wx_fmt=png&from=appmsg#imgIndex=12)

保守一点就选默认权限，就是动个啥都需要你审批。

自动审查适合日常开发，碰到有风险的操作会拦一下，比如删除大量文件、访问敏感目录等这些。

然后像我一般是选完全访问权限，因为这样就不会每次都征求同意了，全部直接自动运行。

毕竟我又不是开发出身，弹出来的东西我也看不懂，你问我，我能懂个啥。那不如直接全部放开，让它自己搞就完事了。

对话框右下角可以切换模型和推理等级。

模型直接不用管，无脑选目前最强的 GPT-5.5。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqV9W480ib4Bsfth3cVCib5hYWabNseO75WkAg5CiacNJFRrFW2yia1bRoTnAscu0icjdxCOHHvNyKhfJzyY3NwZrl2XMmT79Cop7iaNs/640?wx_fmt=png&from=appmsg#imgIndex=13)

推理等级日常用高就够了，遇到真正的硬活大活再开超高就行。

速度有快速和标准，快速是 1.5 倍的速度 2 倍的 token 消耗量，还挺烧 token 的，不过说实话，标准跟快速的速度也没差特别多，在你 token 不是那种可以无限烧的情况下，我还是推荐大家使用标准。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqWVH72shDZ7IibUCbM6R2XLBeA4TORJlX4mZvHboj7IiaxgtOY3vLufVLUHVSjsIKe3iakX9dRwl2ib9icSeDjzH3cmRwbdfVlfn2JQ/640?wx_fmt=png&from=appmsg#imgIndex=14)

右下角还有一个小麦克风，就是 Codex 自带的语音输入，不过使用体验还是挺烂的，录完以后要等好几秒才能转写出来，不是特别推荐大家用，相比起来，你直接用豆包的语音输入法更香。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqXQ53xtyq5admnLXoRRFicg5OVzmGt0r94QvR3biapiaJFljLibTHUWLQqNlLCy6DffaBGG5ibcU61XSLicLSkoWiap5xXWtDjwB6Bnmk/640?wx_fmt=png&from=appmsg#imgIndex=15)

当然，用着用着，你可能会好奇自己还剩多少额度。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUD7Oj3WVRHQvfOLBEhKN5Kw5Atbmh1VicD34AjlwPmIKyx6mBLEezRRFmoDC0yz0jy5sibGtjpasxkhtNfdTPbsPeAwdq835m1o/640?wx_fmt=png&from=appmsg#imgIndex=16)

点左下角的设置，找到剩余额度，就能看到你 5 小时内还剩多少、这周还剩多少、啥时候刷新。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVMSZS2JNSlTyxFWwlaj84XFO0ZmE1nWuwvZgSal6hDMVo5wUQFo0DE88niabALv3wVJdlibmA9KTVoRic3CUlbBaSX91TxwPb8c8/640?wx_fmt=png&from=appmsg#imgIndex=17)

**像我这周太忙了，白花花的额度都没空用，真的佛了。**
============================

**三. 修改设置**

我知道你看到这儿已经急得抓耳挠腮，恨不得当场造个玩意出来。

但我还是建议大家，先跟着我，改一下设置，有些东西稍微搞一下，这一步，不！能！跳！

打开左下角的设置。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVJ4a83PUNDVquOppNS0IPfbDJOgEa76MeibmsGF5BrzxLJZBX8lWG8iaV3VSf54k4EhT4s3D7jKkCfGNBrVrkIB1EGgMupC2Kmw/640?wx_fmt=png&from=appmsg#imgIndex=18)

常规设置设置里面的这三个，都打开。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqWyicPxcmk0ykSQZ5TOcFY6EGzQrHYSEibguEicQxNibGS2q9jHEGVryYKg9l5wNtC51n3RrFia78zHyicz1x8AclYKWib8ibTk2O59NPg/640?wx_fmt=png&from=appmsg#imgIndex=19)

往下滑，跟进行为改成引导，这样你发现中途你想修改的时候就可以直接插入，而不是必须等着那个任务做完才能进行新一轮的对话。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVroUIPH7QQia2zQR2o01QSHTswmeSiaYZGEHknWNepiaJEgCoR63VWS0O8sQibwbAhTuuAGSrbcibiahndgicH526jEwWN1Qgdcicm7Go/640?wx_fmt=png&from=appmsg#imgIndex=20)

如果在刚才开头那一步忘了导入 Claude Code 的内容，也没关系，在这里也可以补导入。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUNaibgGdLu4sORfbEZ2aKicfRDGVfxWMK6VOL3esG7s3kaD7TyN1taEeiceW53D88aPX85jqUnvJ7m0ADQ6aFItFDczxjWz3mkxg/640?wx_fmt=png&from=appmsg#imgIndex=21)

接下来，设置 AGENTS.md。

这是从上往下分层穿透的约束体系，也就是你给 codex 设置的家法。

第一层全局生效的 AGENTS.md。

在个性化设置的自义定指令里修改。

他是你为 codex 提供的全局通用的规则。

这个设好了，不管你以后开多少个新对话，他都会记得。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXzm0ZiabdRo636n50GxKJ7SETPzZrEicibTAANG5LGmkMlMVDUTNmd7Ca12A1LdMt38ZIW2n1oibooS4Kt7rOGM0J09ic8EKkIz9AY/640?wx_fmt=png&from=appmsg#imgIndex=22)

这块就不给大家推荐我自己的了，我自己的太自定义了，我也给大家推荐一个我觉得不错的来自大神卡帕西的模板，可以直接复制粘贴使用。

然后记忆的两个功能，我推荐都可以在设置下的个性化中打开。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVyC173sZ4MuP0vdHH9GNY0SeQgEtjYzmXyyk85frIx4zh1m8gfbdWgWj3ZEL96a8uTXXYkYzttyFtNFgSw2JYUF4WUqgwgta8/640?wx_fmt=png&from=appmsg#imgIndex=23)

打开以后，它会在你结束对话或者闲置了一段时间之后，自动把之前的对话总结成记忆片段保存下来，以后遇到相关的场景会自动调出来用。

在设置的外观里往下翻，最底下有个宠物的区域，有经典的 Codex 形象，也有各种各样其他的，就跟 Claude code 的那个一样，大家想养，可以自己去养着玩玩。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqV42jpfl0oMTZ6miaGVv7S8aNQ9MRsR1mBJ3OiaA7Y5tJRwtMG1ia3TFxNMukqGoZ5NSPlMwXZicVxR2z5qljRAxaZZECjiaao25Nfo/640?wx_fmt=png&from=appmsg#imgIndex=24)

**四. skills 与插件**

然后，我们再来介绍一下插件和技能。

在 codex 里，都是从插件这个 tab 点进去。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVQ2JkGyz6PmkdyZSOibxS2k18BeVicGUyBia3Wlwg9pvgNFqwg1FHAeVICR8KL2s4QeTM7ZaU8y4RSKchmXXybrdcopUR2YeqTUM/640?wx_fmt=png&from=appmsg#imgIndex=25)

然后顶部就有 tab 可以切换插件和技能。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXcbJ3vLdxzZcq3Fhu5GSCCicZsCCfCkfl7ykVbBX4pA86yFnlZrEnibl2CfpTNQqic0NVmlhBj0k4OnJIdzibYXWb3YV35xYMLWHM/640?wx_fmt=png&from=appmsg#imgIndex=26)

技能这个东西，就是 Skills，字面意思，给 Agent 用的技能。

我相信大家对这个东西已经非常了解了，但是如果你确实还不知道的话，可以去看我之前写的那篇[《一文带你看懂，火爆全网的 Skills 到底是个啥。》](https://mp.weixin.qq.com/s?__biz=MzIyMzA5NjEyMA==&mid=2647678672&idx=1&sn=c3510896d2de19b5c5ab6805c27182e5&scene=21#wechat_redirect)

插件就是把一组技能、工具、配置打包起来的安装包，你可以理解为比技能更牛逼更成熟的东西。

Codex 的好处是，都做了可视化 UI 界面。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqX4VbcI8Zj4gibEpcDf0LUTguRerhAAqDCs0sxxSaR3uRcjqqKusEJ0ULKEt2fQAhCibLXpguOaJTDlTLm9vLssvJfKY2dDVJBYY/640?wx_fmt=png&from=appmsg#imgIndex=27)

你可以直接点击右上角的管理，进入管理界面，批量管理你的插件和 skills。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqWUTQaHiaF98p8icPJkDXFgmxjk8CibvltaCv1FuHvIq8ia9AsvCWM9jicT4qmWRzq8XcjEwk9m0T7Yb8bSFXmZOk1yNsiaRsEF1PnH8/640?wx_fmt=png&from=appmsg#imgIndex=28)

同时也自带了 Skill 创建器和插件创建器，你想做个啥，都可以直接右上角点创建。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVF3RFP3shdMbibfq5udIvKWPuF1EskklZkMLdYc9ju9BATKT8dJjfwEFRSwRHmONia57sAjyiabDGMxNQeznE6k6QSiaicsET6jz3w/640?wx_fmt=png&from=appmsg#imgIndex=29)

然后大白话告诉他你要做什么样的技能和插件就行。

![](https://mmbiz.qpic.cn/mmbiz_jpg/2jjfQoZLoqVzps3G4icdmGkHaGRnic5vAhIIsVkicIAT1SzHqIGsUfLPu99Ggtibeg1ibsBs5icCBkmoxVfLzfGCiaxddn9SyqMibBsqEIdGGia8UJcg/640?wx_fmt=jpeg&from=appmsg#imgIndex=30)

如果要下载除了官方之外的 [[skill]] 或者插件，直接把链接甩给他就可以。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXTAG8GJlGjyp9TvAibVJcunoA9q6BsC3vHuWKgb9WgVd33OqD5Q2rF5cNOib4mxAFXW6lBIXuFqkOXHtGyeeTGqUkeZYUibnUgj4/640?wx_fmt=png&from=appmsg#imgIndex=31)

其他的都跟别的 Agent，没有特别大的区别。
=======================

**五. 开发一个网页**

现在，你终于可以大展身手了。

先带大家，直接开发一个小网页，走一遍流程。

当你建好一个项目文件夹之后。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUzm5NlB0HjTmKFzBAwkhlprg7RAdibm5AjvkWzId71zWtOMiaOpXImLBsfhhIRb4U2iccKOeJYV7ZZTyfBpaGj575lBW14ibwltVo/640?wx_fmt=png&from=appmsg#imgIndex=32)

按一下左边的加号，打开计划模式的开关。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXGeLkciamyFlHbjicx7keR86j28Tkl53FViaZv6pbk4mPyBzSYJicpxdNiaAarmniaiaSjd3hsEkjgwG7vqHJqKMJvBnUDUaJLmjFkH0/640?wx_fmt=png&from=appmsg#imgIndex=33)

计划模式就是只规划不动手，先帮你把方案理清楚，你确认了再开始做。

每个稍微复杂一点的项目，我都推荐你先用这个模式过一遍。

打开以后对话框左边会出现一个小图标，说明你现在在计划模式下。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqU1uAzMfyR35cZhfklpHaQvQSgl9GAbc4Z3sktJc7oryzsSrBuF3optmePcCDk5juChe24pjO0NiaJDiaYusmlibEXDQJGj4x9fZ8/640?wx_fmt=png&from=appmsg#imgIndex=34)

接下来，咱们跟他说，帮我做一个 Codex 功能介绍的网页，要好看，要有设计感，把所有功能按层级分类展示出来。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVfJJMvrEN7nVydD7fCfibRa0XJtwokJoicXxfClOuAZxYrKThJCV4FuV3FxH163ibmJsc2eSYoxpgqSxAnekcMAhuPOXn2XtGMibo/640?wx_fmt=png&from=appmsg#imgIndex=35)

它会先问你几个问题。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/2jjfQoZLoqXictN0gd9icCopdQh4ic91TDNmntphnJA4sJM4L7JW4ic7ZHjGYT67n9eP8LDgZkS00ibsJqicLNdlpSLdKLc5f6Dclu9tOdMWnV3aU/640?wx_fmt=jpeg&from=appmsg#imgIndex=36)

你直接点选回答就行，回答完以后，它会给你一份比较完整的方案计划。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXfBk2SQ8e7ynBgUqUdvvU1rACpsMubNmEr5dwy0yPh0ak0UsiauHjnMeSabnl9ZBjrczibMoYDqDccdswtNIstXgT2CUWQSuOps/640?wx_fmt=png&from=appmsg#imgIndex=37)

当你确认没毛病之后，就可以开始实施。

中间的开发过程我就不截图了，反正全自动的。

这种小网页，基本就是一遍成，做完之后，他就会给你提示，你可以直接用 Codex 的内置浏览器打开看看效果。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqXd0osZuIq3pgZkQMuYcqZWiatanghXnhzOtKtrp1jsdxlpw7rC97Z9CMLcfpjNnGBDYcvcthjegh3uOJob9A8HibOeos7q6P0iaA/640?wx_fmt=png&from=appmsg#imgIndex=38)

打开之后会看到一个预览页面，中间有一条线可以左右拖动来对比。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUwe5RJz0LE54A4aanpxU7vVW1vSJHg24gjB3OzuHor9Okdf5ep9cjiasdmrURmTQu5NGxlfppCxfNl0ibaLz8DhjRibwibXJnMuJc/640?wx_fmt=png&from=appmsg#imgIndex=39)

右上角有几个按钮。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVhmqKmELr55upzficjBsC4fL9wQHu78Q7eBhjc9HGAQyVEq4iabvlKF8KeSibdOWA6rlIJ1Hs2zYyew9HA3QAdFvj6zScXw5K5wY/640?wx_fmt=png&from=appmsg#imgIndex=40)

第一个是截图，点一下就能截取当前页面，效果就像下面这样。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqV83dGoKDsiaWhEAX6tjby3P6pOWMhSIvc7hG55zwKfHfywdIef9pEZ0WzeAPibAldTBpR225IO6NJl8IcuKZTYQ6jWSsweLqnlU/640?wx_fmt=png&from=appmsg#imgIndex=41)

第二个是批注，这个是我用得最多的功能之一，真的很香。

点开批注之后，你可以直接在页面上圈选任何元素，写上你的修改意见。

比如说我想让他改成官方的 logo，直接在页面上选中它，手动输入文字说明就行了，不用再截图或者用嘴去描述一大堆

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqXIA6uUNQkMoOv4ykpU6ibllsvGWWRhLT3mCF2RBq2Sn7rE4HPr01wGmia1v8whJt1kkYicvX5KZPuG6icFpc2CEqGEMw5UgRWyMO8/640?wx_fmt=png&from=appmsg#imgIndex=42)

而且最近刚上的一个新功能是，像字体、字号、颜色这些参数，选中之后可以直接调，改完实时就能看到效果。

![](https://mmbiz.qpic.cn/mmbiz_jpg/2jjfQoZLoqUx6TgW5kVyyibkcKLR7GPBpQvHRjOVzyrQnykG4AMBgFKPelSMscEMSImvLypYNwESmYx7d25oIZm6jlDHiaqm2DYjiaPmbgagrM/640?wx_fmt=jpeg&from=appmsg#imgIndex=43)

注释完，点右上角发送。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUQVIFlVd7wjnxbe8A7RkM6NOliaIVKGR26icp60LJpRmRrgM1qvLsiaWiaiaUOgm5IfS1fBgdSqlzucKPVxCiargVxwBBfN970lNFsk/640?wx_fmt=png&from=appmsg#imgIndex=44)

修改后的效果就是这样的。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVRDRK6H5m5hKGbTMwM46Xj0NLXFLos8efic8xRMhRqIR9PDgZUibHyM6mCqvugNtbGtLvVG2pAuc9jiaeicCG7gZmcXp0u9v5tqFU/640?wx_fmt=png&from=appmsg#imgIndex=45)

当然，现在做出来的网页是跑在你本地的，只有你自己能看到。

如果你想发给别人看，就需要把它部署到服务器上。

我们公司内部人员部署网站，用的是一个我专门给公司同事搓的 Skill，安装好之后直接让 Codex 调用就行了，非常方便。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVxwIrXW8dkkHzHnI9zhIc5kPbzsIGvicOueWg2AN3Cplf8T2Mzg6r69QXJ7ibiaDF9qpRk3ErAQCtnrAjgkhWvbEXWoTnELAnbh0/640?wx_fmt=png&from=appmsg#imgIndex=46)

输入 /，就可以调用 skill。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqVicrqBolHyTKBBNp96YPic3uYwsmECEV9uSHKFN14OQelgf8bpicpRwHvdSZkCibtiaViaJ9eKml2WvsTj8ODNpib68FXQZPdnosiaDus/640?wx_fmt=png&from=appmsg#imgIndex=47)

具体怎么部署到自己的服务器，每个人的情况不一样，这里就不展开了，相信大家自己能够搞定。

**六. 开发一个 APP**

接下来呢，我们再来个更进阶一点的，同时更好玩的，就是，做一个 APP。

我用一个自己的真实需求来演示。

就比如说最近刚体检完，结果确实不太好，去了医院看了一下，医生给我开了三种药，一天吃两到三次，有的饭前半小时吃，有的饭后吃，搞得我头都大了。

而且我经常搞混，刚刚到底吃了没有？？？

所以我就想，要不要做一个手机上的用药提醒 App，来通知提醒我吃药。

就这么个特别临时特别小的东西，正好拿来当演示 case 了。

同样，开启计划模式，说出我的需求，Codex 会问一些问题，然后你老样子回答一下。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqWubbRn7Tkh6Q2g9NVGzQRH06LhnCs8fAIfO1gc0kdCxjZia5icZXfBYHTBbTJ5pYH0U9iawVGiayyBCsCdSIZINrWWlI64icHPiaWCU/640?wx_fmt=png&from=appmsg#imgIndex=48)

最后，给一份方案，确认实施计划。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVxibZmAT8PM2pGL1ibgHJfb1WujVFQpFXyaBHicyyJ7fBypkUyOslCBWOEmu6YFQUu3KzkeLAYR1qibia4SBE6Xrt0U5WzJWJH75bc/640?wx_fmt=png&from=appmsg#imgIndex=49)

过程同样不截图了，反正我干别的事情没管了，全是自动跑，大概二十分钟后做出来了。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqW2dol94zteUZUTsvlp3Av9rw52uyYLUGjmybrdkSEuYLUcKncV8cc5PGGw7M4tB9K13Y6KLFkz1WzoGQ1cx8tJ3Hcica0s9De0/640?wx_fmt=png&from=appmsg#imgIndex=50)

它给了一堆乱七八糟的文件，看不懂没关系，不知道怎么安装到手机上也没关系。

你就直接说，我现在想传到我的手机上。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqVz2g9vBibuS3QpLibm6x6oM6m2G7o1KPPOBf60rmKq038Kqhofo2hrUv0BZlibvBpQfOQcp1icU6cPiaC0WeXQ0gMFS2H17XhnNIkg/640?wx_fmt=png&from=appmsg#imgIndex=51)

Codex 会告诉你，得先安装 Xcode。

因为开发一个 APP 跟开发网页不一样。

你可以简单的理解为，网页用浏览器就能跑，但 APP 需要一个专门的本地化开发工具，苹果这边叫 Xcode，只有装了这个东西，才能把 APP 编译出来装到手机上。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqUSGaOrGCRIl7nvzGAJ5djURKOMNVq5UcyG6CIo3OVUeYXicOrCPQRkbqibcXaX2IEuVbbSD9A1O0ezDhCEo3lic3zlhYWbibCURy0/640?wx_fmt=png&from=appmsg#imgIndex=52)

你其实也不用管什么事 Xcode，我觉得绝大多数人电脑上大概率也没有提前安装 Xcode，所以呢，你就可以用一个 Codex 的很屌的邪修方法，直接 @Computer Use，让他来帮我搜索、下载和安装。

这里的 @，是用来点名插件的。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqX3jnVA6Q5ngJ4WqSBXQTMM5gibNGmqqiaibia6tPkQMZYeIxHwnuxohia4iafG8yiboG19QrHcBXpnwBsI60y8Eia4icA5vyllP7nE83C8/640?wx_fmt=png&from=appmsg#imgIndex=53)

Computer Use 是我平时经常使用的插件之一，也是 Codex 上最棒的能力之一，全世界能视觉化的操控你电脑的就没几家，Codex 做的非常好了。

如果要使用，需要先去设置里把 Computer Use 的开关打开。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqW2LztuYDzpu0Sw2ibHeofGdqgGqmGQ0XwpEP9ATN9cT1ZnsFHI90RcAm5j8QCsN43gBqqT7jZN9KX2a7oeaGKBFhhKyVon96xE/640?wx_fmt=png&from=appmsg#imgIndex=54)

另一个常用的就是 Codex for Chrome，想要使用同样需要开启开关。

这个能沿用你 Chrome 里已经登录的账号状态，操控浏览器。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXJUIYTuxyrzib8lADHtRzTjbgoiaZQ3FSlSstpHsEokwwxFKmZTdjzUP4P9XWVeHicV4j6etqT4iclocuodW1ocSOicrMOlicmvcdaY/640?wx_fmt=png&from=appmsg#imgIndex=55)

并且在这个过程中，用 Tab Group 来隔离工作区，不会抢你的标签页，你该干嘛干嘛。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqWsJt3ktCISo6poBZjhYpuEhuGKyUcCiaS7iaicLicYzLyxNObialkYEpRScXka0VINNicaG3iakn3WFxezxOllgXQQ5c9Zr3GmPEs6Kg/640?wx_fmt=png&from=appmsg#imgIndex=56)

软件下载完之后，你都不用打开 Xcode，你也不用管，你可以直接让 Computer Use 来帮你操作后面所有的编译步骤。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/2jjfQoZLoqVmRIeI65S1L03CSoBpEQib1mwbsRUfJUIhOTr46JPTZDx8pW7yQ6ybsSepLqauNhFiassMBxveUXACS9fgcqgffFRTNvEzyMMa8/640?wx_fmt=jpeg&from=appmsg#imgIndex=57)

用的过程中，电脑上方还会显示一个操控状态的提示条。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUBSBWDC0IyBuRova6QzR0U3Lm9uRPtiaPZmYUeU2k6bb2Oiaut7UnyQMPfWrV5WqrfkiboTkVfvcznJiasVD5icFFib0KJ3Pfb7FXpI/640?wx_fmt=png&from=appmsg#imgIndex=58)

不过，碰到需要输入密码或者登录账号这种涉及安全的步骤，它会停下来，让你自己来操作。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqUNaI85iaYHgnwOkYZfPBHO6TZc8ia3TNpxYwT3bJwZObb5ic61cZXj3fTEVVJFxpQJuaR4ic3rz5CejPDViaiaROUZIIcxmVn5MAqYA/640?wx_fmt=png&from=appmsg#imgIndex=59)

剩下的交给他一点一点自己操作就行。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqV8HVVF6YOm8PIAjNBnGJ8yC2Tb9Cl8USn2VlKtWgu9XcDZKF1UN5fMWiadoOD2uqd3UFEhK12iar33hlU2lSUqQLicQDiatjmrOVY/640?wx_fmt=png&from=appmsg#imgIndex=60)

到手机端的步骤，就只能自己来了，比如用数据线连接两台设备，开启开发者模式，重启手机，确认信任，这些跟着 Codex 的指引一步一步来就行。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqUmxUTJawxdMjrWhnpLA2nRiccnp99th6g6UVcnEOlfxtZzhEeyLQUXabDIZdNicibc2pz7Wx7jC9ibgeibsauPB6ooVdLMRdnvLDOw/640?wx_fmt=png&from=appmsg#imgIndex=61)

不一会 App 就装到手机上了，虽然我忘记做 AppIcon 了，不过这不重要。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqU26tG87oMyYTw6vsJvHos0YptbzVvMpjaQibg9NfvsD8hFBcyJmXuJRRUW6IpUYsVuY1ytfWyBPAXUicNT8gSUicxnouz7LEDffE/640?wx_fmt=png&from=appmsg#imgIndex=62)

里面的雏形也做好了。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqWkZyXEibppTial7ztialDUwsqHfXPITXM4PAjWwtbpg2SicT2Zd4j8xns0fedOX5JdiaKmlNCQJNesiciaKSpuN1b5xJFhEic9p7Hd0VI/640?wx_fmt=png&from=appmsg#imgIndex=63)

做到这里，如果你希望继续远程继续开发的话，你还可以，就掏出手机继续操作。

这里就要介绍一个非常非常非常爽的功能是，在手机上操作 codex。

目前只能在 mac 上连接，iOS/Android 手机都可以。

这是前两天刚上线的新功能，我还专门写过一篇文章。[《Codex 更新远程控制，你也终于可以在手机上随时随地 Vibe Coding 了。》](https://mp.weixin.qq.com/s?__biz=MzIyMzA5NjEyMA==&mid=2647682286&idx=1&sn=596aee2a6de3542e1e322d76913d738f&scene=21#wechat_redirect)

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXLicCl5Kdxuviad2DlPcCJ9ruXywQBJkzVBpDHdMzZJFEVPnKOURRk4wMrQ3cQCge0Wrob4qvkibwykI2dM88wGyGGZuichfBQOeU/640?wx_fmt=png&from=appmsg#imgIndex=64)

最后做出来也没啥问题，非常方便。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/2jjfQoZLoqWCmhuevIFiaJzlHtrVyNgGB9gdvwvy4lMg7WlWFvhzudGYfqpWWUr65icmjL9mNf7mp6jB8Sx1NtSv7xFb7TAtjyjBibw9ToZiatk/640?wx_fmt=png&from=appmsg#imgIndex=65)

到时间了，也会跳出弹窗来提醒我。

![](https://mmbiz.qpic.cn/mmbiz_jpg/2jjfQoZLoqV1vPdydLIwv7HFgTp1wO5biaoNoHJmuvQwV0uHxlibYnaiaPD1HrSRj7oMKtyagEK48co740tHrI8vKgqpnWInp52Fwpaiac8jXWw/640?wx_fmt=jpeg&from=appmsg#imgIndex=66)

就很简单，也很有意思。
===========

当然，如果你要上架 AppStore 的话，那就是另一码事了，我就不在文章里面详细说了，你可以让 Codex 继续给你操作。
==============================================================

**写在最后**

最后，有一个东西，我确实还是得单独说一下。

就是，让 Windows 用户破防的事情。

Mac 用户目前是 Codex 里的高贵 VIP，Windows 用户只是。。。站票。

我整理了一张表，列了一下 Mac 支持但 Windows 不支持的功能。

![](https://mmbiz.qpic.cn/mmbiz_png/2jjfQoZLoqXiby9liaXxJYWic2NepjicqEI5Na4jEEjRJ7Ahl0xo5UnAqnqnGnh0CrnDDLicoYA5AjOmcGuHqGU8ib3MKVUMBK8cm29ZGw9bMH9eg/640?wx_fmt=png&from=appmsg#imgIndex=67)

前面用过的 Computer Use、远程手机连接就不说了。

Appshots，双击 Command 键就能把你当前前台窗口的截图和文字一起发给 Codex，不用再截图粘贴或者用嘴描述半天，它直接就能看到你屏幕上的东西。

Locked Computer Use，锁屏后 Codex 还能继续操控你的 Mac。

Chronicle，屏幕上下文记忆，Codex 会在后台观察你的屏幕，把你最近在干什么自动记下来。

非常可惜。

这些，全是 Mac 专属。

Windows 的朋友们，只能再等等吧。

这也是为啥，我给公司里的同时，除了财务 HR 法务这种特殊群体之外，几乎全员配 Mac 的原因。。。

最后。

希望大家 coding 愉快。

******以上，既然看到这里了，如果觉得不错，随手点个赞、在看、转发三连吧，如果想第一时间收到推送，也可以给我个星标⭐～谢谢你看我的文章，我们，下次再见。******

>/ 作者：卡兹克、可达

>/ 投稿或爆料，请联系邮箱：wzglyay@virxact.com