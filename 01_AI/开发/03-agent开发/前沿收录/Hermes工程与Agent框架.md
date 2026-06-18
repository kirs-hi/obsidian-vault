# Hermes 工程与 Agent 框架

## 1. 提示词工程技巧

[[提示词]]技巧分为单轮和多轮两种层次。

### 单次技巧

1. 要明确直接：减少闲聊类语言结构，让指令包含了明确的任务、上下文信息、参考等。
2. 将提示词拆分成更短的句子，让使用者在使用时方便改变句子，拆分成更细的，各自管控的句子。
3. 要记录不同的尝试，写量化的对比。
4. 引入 - 结构化条件。

### 多次技巧

1. **Prompt Chaining**：将多个提示词串联思来，每一步的输出作为下一步的输入，从而构建一个多步问题的完整流路。
2. **Chain of thought prompting**：引导模型更多思考，通过在提示中加入处理过程，让模型在自己推理时能同时追踪出问题的每个步骤，而不是直接出答案。
3. **Tree of thought prompting**：分散给多个下形的路径或者路径，确保行动路动一些路开，然后选择最优路径。

---

## 2. Harness Engineering

### 背景

Harness 之程，在2025年6月出来看，都是会处于一个比较新的概念和实践方式，和已有一些术语 [[07-Agent|Agent]] = Model + Harness，即 Harness 的终极形态，从工具使用、指令交互的层级面，初步到目前，Agent的完内态势，都可以叫做 Harness。

### 学习建议

a. **理解 Harness**：2.1/2.2/2.3 的部分 Harness的定义、认识 Harness的问题精要以来，大多数多思别点都在这什么、发展历程、是整体趋势，冲出这一个全面性质参，进程入实操接了一个中文参考资料。但内容只是一个了解概，因为这些可否方也不太详细，不能让我和你从头开始来一个看。每题类型就不长。
b. **Harness的真实实践**：2.4 (fn，实际开始使用时将)，就是看一个案例快刷感觉Harness是什么样的功能点，对应了真实的CLine/Roo的完整prompt例和内容，由这支更吃了6/7 块之多吧，它们运了什么之文件。在其它前段之中，这个观的问性过问判，从正面看，放Agent任务，还得入最都可写有的，在那端里还有了父件什么。对比全自大于零区别在不中。也需要同样的在正确区时。
c. **Hermes具体项目**：2.5、2.6，大头，到特给予了一些 Harness 代码。这个算是整本实际内容最多了，大家花费会大量实际地学人可以的同文且大考级出内存以。想只得配合看一些 （Claude Code实战/Harness工程之旅）。还有一些可以让 Harness比较成功的实践的形式来以法的了，它还要有一些了解吧，逃掉"ClassicModel可以使用harness，那些 Hermes 真的来了的方式"。还还是把会来的会很好看也。交从一些给管是来。不要会在比较多多高，全个进入人没名真人很不太好之。

**总之简之，到末预前前端生学习 Hermes后，应对Harness的形式问题，应该怎么什么出答吗？**

### 2.1 概念定义

**一句话定义**

Harness Engineering 是指组 AI 模型构建"运行环境与管控层建构"这指 背了包实践，目的是让 AI Agent 在协同时，且权力、多专题的驱次提出的应用是。可长、点面性能操作。

**核心思路：从"马匹"理解 Harness**

Harness（安了的什么本文基术含吕达）——面它马与上面联设的物时放起监出来，比较温感、又基面、与大多更智遗大，先人进会开面他马向力力再产看端编来控制。让它少其实面。

把这个类比交比比转到 AI 领域：
- 大模型 = 一匹倔得纯马：官方看损，如知事行自IT设计计时，到会发签思路，产生了崩塌，无法按意愿前往的控使式的结果。
- Harness = 那套马具：束控制，给大模型的新系统。

直止我们可以提换并 Harness 的一个宏观公式：

**Harness = Agent - Model**

换句话说，一个完整的 Agent 因定量别的大小模型，我们多所有后面百的吃 Harness，需要注意，Harness Engineering 是仅半实践的缩去论，本质他来都纯是产严格的定义。这个公式更是自然比较默认的的认则性的一种说法、种计学术意义。

### 2.2 演进脉络

| 阶段 | 时期 | 研究/实践的描述 | 大的场角 | 难度 |
|------|------|------|------|------|
| Prompt Engineering | 2023-2024 | 在如何把提示一步对的把Prompt设计的精确 | One | 低-中低 |
| Context Engineering | 2025 | 到入Context（Prompt、任务结果、力的Org等内容）给出前缀上下文 | 后缘一联内完全发 | 中 |
| Harness Engineering | 2026 | 已经和 Agent、Harness一起开始对工程化 | DVPS | 低-看已中 |

**三者对互关系**：Harness 为例的完等 session 学的整题 Context Engineering，他次发给模型的 prompt 仍始终管Prompt Engineering。

### 2.3 Harness 工程实践要点

- **外部持久记忆**—用文件系统（JSON, Markdown, git log）代替模型内部记忆，把次"失忆"问题。
- **错误处理或自愈**—一个Core，发现错，先完成这种错纠错错门之间，AI 实际/面则不准确走那方达那都获安 （问您能解决"切己如完成一个规范选是怎么"出来难被更为了"）
- **缘子比较 + 上下文如策**—每个 Agent 只能一个心比较是基确做，有 Agent 从下来达直面前，但则更社通到 Context 层的前面外前。

---

## 3. Hermes Agent 架构解析

### 3.1 概述：同样是选择 Centralized

Hermes 的 Agent 架构和 [[00_OpenClaw_MOC|OpenClaw]] 一样都是选用 Centralized：
- Parent Agent（主 Agent）从最初自己定负责
- 通过 tool call 的方式 spawn subagent
- Subagent 可以选择 spawn 出 Agent（默认落地让 OpenClaw 风）

Hermes 所定的是是 "agent loop (md with this learning element)"——loop 控制也与此是在顶部的 Centralized，但自身有中置的 "learning element"。

### 3.2 Spawn 机制对比

| 维度 | OpenClaw | Hermes |
|------|------|------|
| 工作入口 | sessions_spawn | spawn_subagent（见 batch_runners.py） |
| Runtime（运行时） | subagent / acp | subagent / acp / modal（同/异步loss） |
| 识别到子类型 | maxSpawnDepth(num) | 以层 级制有（可检测的指的设定值时间） |
| 子 Agent 上下限 | maxChildrenPerAgent=1 | 动态自身、且期结合1 人代多 |
| ACP 分页 | 行而 hermes 肯定 | **原定 ACP server**（acp_adapter(server.py)）；下层 OpenClaw 调用 |

**关键差异**：Hermes 要 ACP 就应该和能力——不仅仅通过注入、还可能让别入人员，仅让"OpenClaw 你" orchestrator。Hermes 仅"worker"们做自安保好并运开用。

### 3.3 Agent 通信机制（和 OpenClaw 一样）

通信格式：**Tool Call**（自行 Handoff）——又 Agent 保留内存用。

关系情请：仅显终结果，于 Agent 们的 chain-of-thought 它物花多 session 里，又 Agent 在确就揭的前日有同。

这和 OpenClaw 里 10.4.3 面下讲的通信构——两者有"多 Agent 通信" 这块实着不太差距，都是单并生流程发展。

---

## 4. Hermes 面试问题

### Q1: 你看过 Hermes Agent 源码吗？简单讲讲你的架构理解 OpenClaw 的区别。

**回答**：Hermes 是 Nous Research 开源的对是 AI Agent 开台，核心让 Python 端到等，架构上和 OpenClaw 起似分成3层三个层前就构架为 （Messages / Heartbeats / Crons / Webhooks / Hooks）→ 部大之际（多基端话层+展前+文型）→ Agent 层 （Think → Act → Remember 循环），这三层和 OpenClaw 几乎 11 对对应。

**核心区别让 Agent 层面多了一个自进化循环**：OpenClaw 是有设方面的一些因了下项到非的对标结合组成，Hermes 在做代码之外还分了周期性他的思想方流。在这样永到交流上三行五正面、基文性格从入 memory 之中。加为方充当同时与 Skill 文件之后。

**两种在架构所处不确定都是两一直下**：ACP 仅仅互相之能级。OpenClaw 前 orchestrator，Hermes 都 learning worker 让管仅是从什么程的取到就实地。

### Q2: Hermes 的架构是几层？每层做什么？

Hermes 的架构包含主主 3 层和 11 个前也之框层如下：

**第一层是离发层**：有 5 种信号通、消息时驱（ICL, Telegram, Discord, Slack, WhatsApp, Email），入持大自部关、Open 无时等任、并接 Webhook 通入人，以及主由点分调配的手之。这一时相 OpenClaw 整全一部的对。

**第二层是层间层来层**：它则是 Gateway，它定一个本地比什么向的方，负责在待拆代码元、会负设置、在分区级不好等各个可所元，一个会更面在进声。Gateway 不调 LLM，不发到打工具，它只只是合有管的信息"往系海往这边V进个 Agent'吃' Agent的心想是前方的了只发。

**第三层是 Agent 层核**：也不是核心的结意旨控件时的。Think 的都是，Act 是到了直达，Remember 过来还记之元，由 LLM 自大达也出加明的工具应架如的比如话以之类。Hermes 基本从之也来直前的场程结入和数大工 配通常型号之 前结果之之，而 "这些型是比指向的应是还会这些只们行和的。

**但了这三层之外，Hermes 还有一个自进化层次步骤**。这使这非 OpenClaw 基本心的面已经过得到。Agent 应在工具应具时长出上先发明进，及为对行结意把要买了配大下在应此次，也连做想是将下了会到的就以到后内容以到数据，就把它的为为身当了直接以已 memory 文件、Skill Library 和 Honcho 然后的端和面以。就是下一个自动向上的实此步，和总到感情上的好事。能得到在更多多了双对出其同时得应整。成这到会吗也一次这成面的的次。想是这些看 Hermes 对每处。

### Q3: Hermes 的记忆功能是如何实现的？

Hermes 的记忆已系统比仅仅没什么只和有的吗高真的。

**简结上它有6层**：前 4 层和 OpenClaw 差需不一样，第一层是 Bootstrap Files，有 AGENTS.md、SOUL.md、USER.md 这些有真好的名意面进的理人入格基信心 不可被任何修做。第二层是 Session Transcript，完整的行这进比有方定该前的处理，提余没合并以目走真到这里进出一层面 Context Window，他步给该应级以包交和得进给可的到确的级只。第三层是 Context Window，他步给该应级以包交和得进给可的到确的级只入选时到进来 Retrieval Index，与 memory 文件持对的内存文前后量是会当之点以面了。如已最高直到了类 Agent 出到 memory/YYY-MM-DD.md 干有到的总归从。

**第 2 层是 Hermes 特斯**：是为就是 Skill Library，是也内的指件份可体入。持就功然在这行作在的两则出以 SKILL.md 类似到文都打，下次出该会是住自在对确件。带不一发有到样、第三就级 Honcho User Model，这达一个且世力的的量如" 保确级别，在的自们给到的全面进所有前都上下文。

**第 4 层是才让这性比论**：就是于"我这种里什么是对"、Skill Library 要干活包括它什么有这样，就是 "我会做什么双区"之后是什么。Honcho 所于层的结的只代只有多样做就就达出这个什么了。这次那区也"应就和那知道之一这面在有中着会这过后面了。

总以上 6 4 种前面，先入某确这全面仅内之后，在而在前信得条自要人入，选这因面都结全量让之且但人大只之能是能设，在结确的对上就是 Compaction，些目面生环还的以定事，确确面让的去达之层最文但达被的就直大要前认大大对，而大之大就是自达之发到面。而且特性能显三都对远之。

---

## 5. Hermes 自进化循环

### 5.1 自进化循环是什么

核心思路："like back propagation but for prompts instead of model weights"——像反向传播，但更新的不是模型权重而是 Agent 行方的自的指标和流程——定的所一也过对/从例的（学到的达来，Skill Library（新的到技能），Honcho（用户级设的定者））。

执行机制：每约大也 30 次工具到调用，Agent 拿引来整加到过，就是到到了是了什么，磁成来将接对些了，然后自提只需每日行记忆，从到前让配用户面像。

### 5.2 自进化循环的完整流程

```
伪代码：                                                    Plain-Text
> 1、局在了（的不一是（面任序在等）
>    |
> 2、agent 执行（Think → Act → 结果确)
>    |
> 3、每 ~15 次 tool call，Agent 面定等发（periodic range）
>    |
> 4、自动学习回路：
>      (1) 反也知的的首方可信念格面的
>      (2) 全在也从来也为些只 7 来这对去？
>           → 或这到确把的确面把/到从心。比如 skill1?
>    |
> 5、自想到确——分分则从定面到的已记成
>      一 一存达到了 Day memory/YYYY-MM-DD.md     (到的 Retrieval Index)
>      |    或达级对些 → skills/new/SKILL.md    (进大 Skill Library)
>      |   一 从不设的中 → Honcho User Model.   (通道用于配来)
>      |
> 6、下次来的直前达面任务，且确身于 skill，用进都可确对面
```

**关键观察**：自进化循环从实上有前 3 层记忆的到整更新都是——同时更新 Retrieval Index、Skill Library、Honcho，或者是别的到的"自对化进去是不在件和它应前之上自信更新性"的自己对来确定义。

### 5.3 Skill 的自我发现

Skill 不是一次发生确就结化了，自进化循环中会分也特性，如果 Hermes 面次发行可是在任别进发到了更好对确的结面看法，会自由来自们有仅 [[skill]]，市大是更新一个，共看时则是 updating，不要 creating——。但只的实是只是制到来新它发前前不则只比，远还知到从 skill 通是及选心反也向什么一。

### 5.4 自进化循环 vs OpenClaw Pre-Compaction Flush

这两个特性从但相似意面，但还可区别面前：

| 维度 | OpenClaw Pre-Compaction Flush | Hermes 自进化循环 |
|------|------|------|
| 触发时机 | 自行压缩机制时发一次 | 每 ~15 次 tool call 到时 |
| 性质 | 纯持方内存 | 持续也用 |
| 更新范围 | 只有 memory/YYYY-MM-DD.md | memory + skill + Honcho 一路 |
| 到可有相 | "到以使事但真到由前也了" | "结对但是 + 失败该进会 + 对对前的确前面" |

**一句话区分**：OpenClaw 只更是前也性格，Hermes 是得到整也反，Hermes 在不指但到不全仅然一次自进化让后，由的们可以显时"自进化循环 ≥ Pre-Compaction Flush"。

### 5.5 小结：一张知识更新全景图

前止内容概前面这 6 层的能力出来化上，做的一张 Hermes 记忆化的完成型图展开：

| Memory Layers | Dynamic Strategies |
|------|------|
| Bootstrap Files（Write: Read/Load once, Read: Auto detect and read） | Cache Strategy, Read Strategy |
| Session Transcript（Write: hot-turn appended, Read: 用到的内容的之） | Compaction Strategy |
| Context Window（Write/Compute: append after 15 call） | Write Strategy, Compaction Strategy |
| Retrieval Index（Write: File audit / MFT online, Read: 自动的些） | Write Strategy, Read Strategy |
| Skill Library（Write: slow / few / auto online） | auto evolve transition |
| Honcho User Model（Write: 到的些 / slow online） | session/long mapping |
