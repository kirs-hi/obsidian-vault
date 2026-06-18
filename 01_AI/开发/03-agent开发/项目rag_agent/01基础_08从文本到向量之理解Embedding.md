---
title: "《AI大模型Ragent项目》第8小节：从文本到向量之理解Embedding"
source: "https://articles.zsxq.com/id_peetnkhdwbne.html"
author:
  - "[[马丁]]"
published:
created: 2026-06-05
description:
tags:
  - "clippings"
---
[来自： 拿个offer-开源&项目实战](https://wx.zsxq.com/group/51121244585524)

上一节我们聊了元数据管理——怎么给每个 chunk 贴上标签，让它从“一段裸文本”变成“一段带上下文的文本”。到这一步，每个 chunk 都带着来源、权限、位置等信息了，看起来已经很完整。

但有个根本问题还没解决：这些文本还是人类语言，计算机看不懂。

你让计算机去比较“七天无理由退货”和“买了一周的东西还能退吗”这两句话，它只会逐字比对，发现没几个字是一样的，然后告诉你不相关。可任何一个正常人都知道，这两句话说的是同一件事。

怎么让计算机也能理解这种语义上的相似性？答案是把文本转成一组数字——向量（Vector）。这个转换过程，就叫向量化（Embedding）。

## 关键词检索的困境：为什么文本匹配不够用

在讲向量化之前，咱们先看看不用向量化的传统检索方式有什么问题。这样你才能理解，为什么 [[06-RAG|RAG]] 系统非要多这么一步。

### 1\. 场景：电商客服知识库的检索难题

还是用前两篇的电商客服知识库场景。假设知识库里有这么一条规则：

> 自签收之日起 7 天内，商品未经使用且不影响二次销售的，消费者可申请七天无理由退货。

现在用户问了一句：“买了一周的东西还能退吗？”

如果用传统的关键词检索（比如 Elasticsearch 的全文搜索），系统会把用户的问题拆成关键词：“买”“一周”“东西”“退”，然后去知识库里找包含这些词的文本块。

结果呢？知识库里那条规则用的是“七天”“签收”“无理由退货”这些词，和用户问题里的“一周”“东西”“退”几乎没有重叠。关键词检索大概率找不到这条规则，或者把它排在很后面。

但这两句话明明说的是同一件事。

### 2\. 关键词匹配的三个致命问题

上面这个例子暴露的其实是关键词检索的通病，归纳起来有三个：

#### 2.1 同义词问题

“一周”和“七天”是同一个意思，“退”和“退货”是同一个动作，但关键词检索不知道。它只做字面匹配，不理解语义。

再举几个例子：

| 用户的说法 | 知识库的写法 | 关键词能匹配吗 |
| --- | --- | --- |
| 手机坏了怎么修 | 设备故障维修流程 | 不能，“手机”≠“设备”，“坏了”≠“故障” |
| 怎么把钱要回来 | 退款申请流程 | 不能，“把钱要回来”≠“退款” |
| 快递到哪了 | 物流状态查询 | 不能，“快递”≠“物流”，“到哪了”≠“状态查询” |

这些都是日常对话中很自然的表达，但关键词检索全部抓瞎。

#### 2.2 一词多义问题

同一个词在不同语境下意思完全不同。

用户问“苹果的售后政策是什么”——这里的“苹果”是指 Apple 品牌，还是指水果？关键词检索不知道，它会把所有包含“苹果”的文本块都返回，水果类目的退货政策和 Apple 产品的保修政策混在一起。

再比如“充值”这个词，在游戏场景是充游戏币，在话费场景是充话费，在会员场景是充会员余额。关键词检索没法区分。

#### 2.3 上下文理解问题

有些问题需要理解整句话的意思，而不是拆成单个关键词。

用户问：“我不想要了，但已经拆了包装。”

关键词检索拆出来的是“不想要”“拆了”“包装”，可能匹配到“包装材料说明”或者“拆箱指南”这种完全不相关的内容。但实际上用户想问的是“拆封商品能不能退货”。

### 3\. 我们需要的是“语义检索”而不是“文本匹配”

上面三个问题的根源是一样的：关键词检索只看字面，不看含义。

咱们真正需要的是一种能理解语义的检索方式——不管用户怎么表达，只要意思相近，就能匹配上。“一周”和“七天”意思一样，就应该匹配上；“苹果手机”和“水果苹果”意思不同，就不应该混在一起。

这种基于语义的检索，就是 RAG 系统的核心能力。而要实现语义检索，第一步就是把文本转成一种计算机能比较语义的格式——向量。

## 向量：让计算机理解语义的方式

向量这个词听起来有点数学味，但别被吓到，核心思想其实很直觉。

### 1\. 什么是向量——用坐标来表示含义

打个比方。假设我们用一个二维坐标系来表示词语的含义，横轴代表“和购物相关的程度”，纵轴代表“和售后相关的程度”：

```
售后相关 ↑
     |
1.0  |          ● 退货(0.3, 0.9)
     |        ● 退款(0.2, 0.85)
0.8  |
     |
0.6  |
     |                    ● 换货(0.5, 0.7)
0.4  |
     |  ● 物流配送(0.6, 0.2)
0.2  |
     |          ● 加入购物车(0.8, 0.1)
0.0  +-----|-----|-----|-----|---→ 购物相关
     0    0.2   0.4   0.6   0.8   1.0
```

在这个坐标系里：

- “退货”的坐标是 (0.3, 0.9)，“退款”的坐标是 (0.2, 0.85)——两个点离得很近，因为它们语义相近

- “退货”和“加入购物车”的坐标差得很远——语义确实不相关

- “换货”在中间偏上的位置——它既和购物有关，也和售后有关

每个词语在坐标系里的位置，就是它的向量。向量本质上就是一组数字（坐标值），用来表示这个词语的含义。

两个词语的含义越接近，它们的向量（坐标）就越接近。这就是向量表示语义的基本原理。

### 2\. 从二维到高维：真实的文本向量长什么样

上面的例子只用了两个维度（购物相关、售后相关），这当然太粗糙了。真实的语言含义非常丰富，两个维度根本不够用。

实际的 Embedding 模型会用几百甚至上千个维度来表示一段文本。每个维度捕捉文本含义的一个方面——虽然我们没法直观地说出每个维度具体代表什么，但模型通过大量训练数据学会了怎么分配这些维度。

举个例子，把“七天无理由退货”这句话送进一个 Embedding 模型，输出大概长这样：

```
[0.0234, -0.0156, 0.0891, -0.0423, 0.0567, -0.0312, 0.0178, -0.0645,
0.0923, -0.0089, 0.0456, -0.0234, 0.0712, -0.0567, 0.0345, -0.0198,
... (省略几百个数字)
0.0123, -0.0456, 0.0789, -0.0234]
```

就是一长串浮点数。如果模型的维度是 1024，那这个向量就有 1024 个数字。

> 你不需要理解每个数字的含义。你只需要知道：这组数字整体上编码了这段文本的语义信息。两段语义相近的文本，它们的向量（这组数字）会非常接近。

### 3\. 语义相近 = 向量相近：这就是 Embedding 的核心思想

用一句话概括 Embedding 的核心思想：把文本映射到一个高维空间中，让语义相近的文本在空间中距离相近。

回到开头的例子：

- “七天无理由退货”的向量和“买了一周的东西还能退吗”的向量，在高维空间中距离很近

- “七天无理由退货”的向量和“物流配送时效说明”的向量，距离很远

有了向量表示，计算机就不用再做字面匹配了。它只需要比较两个向量之间的距离，距离近就是语义相关，距离远就是语义无关。

这就是 RAG 系统能做语义检索的根基。

## Embedding 模型：文本到向量的转换器

知道了向量是什么，接下来的问题是：谁来做这个转换？答案是 Embedding 模型。

### 1\. Embedding 模型在干什么

Embedding 模型的工作很纯粹：输入一段文本，输出一组浮点数向量。

![无法获取该图片](https://oss.open8gu.com/image-20260218222108266.png "无法获取该图片")

你可以把它类比成一个翻译器：把人类语言“翻译”成计算机能比较的数字语言。不同的是，普通翻译器是中文翻英文，Embedding 模型是自然语言翻向量。

几个关键特性：

- 输入长度有限制：每个模型都有最大输入 token 数（比如 512 或 8192 等等），超过会被截断。这也是为什么前面要做分块——把长文档切成短文本块，确保每个块都在模型的输入限制内

- 输出维度固定：同一个模型输出的向量维度是固定的。比如某个模型输出 1024 维，那不管你输入一个词还是一段话，输出都是 1024 个浮点数

- 同一模型内可比较：只有用同一个模型生成的向量才能互相比较。用模型 A 生成的向量和模型 B 生成的向量，没法直接算相似度

> 第三点非常重要。这意味着你在数据准备阶段用什么模型把 chunk 转成向量，检索阶段就必须用同一个模型把用户的 query 转成向量。 **换模型 = 所有向量要重新生成** 。

### 2\. 主流 Embedding 模型对比

市面上的 Embedding 模型不少，选起来容易眼花。这里按照实际项目中最关心的几个维度做个对比。

#### 2.1 模型选型的关键指标

在看具体模型之前，先搞清楚选型时要看哪些指标：

| 指标 | 含义 | 为什么重要 |
| --- | --- | --- |
| 向量维度 | 输出向量的浮点数个数 | 维度越高，表达能力越强，但存储和计算成本也越高 |
| 最大输入 token 数 | 单次能处理的最大文本长度 | 决定了你的 chunk 最大能有多长 |
| 中文效果 | 对中文文本的语义理解能力 | 中文场景必须关注，有些模型主要针对英文训练 |
| API 成本 | 每次调用的费用 | 大规模向量化时，成本差异会很明显 |
| 是否支持本地部署 | 能不能在自己的服务器上跑 | 涉及数据安全和隐私的场景，可能不允许数据出外网 |

#### 2.2 主流模型横向对比

| 模型 | 提供方 | 向量维度 | 最大输入 token | 中文效果 | 部署方式 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| text-embedding-3-small | OpenAI | 1536 | 8191 | 中等 | 仅云端 API | 性价比高，适合英文为主的场景 |
| text-embedding-3-large | OpenAI | 3072 | 8191 | 中等 | 仅云端 API | 维度更高，效果更好，成本也更高 |
| text-embedding-v3 | 阿里通义 | 1024/768 | 8192 | 优秀 | 云端 API | 中文效果好，支持多种维度输出 |
| BGE-large-zh | BAAI（智源） | 1024 | 512 | 优秀 | 本地部署/API | 开源模型，中文效果突出 |
| BGE-M3 | BAAI（智源） | 1024 | 8192 | 优秀 | 本地部署/API | 支持多语言、多粒度，综合能力强 |
| Qwen3-Embedding-8B | 阿里通义 | 4096 | 32768 | 优秀 | 本地部署/API | 最新一代，维度高，上下文窗口大 |
| GTE-large-zh | 阿里通义 | 1024 | 8192 | 优秀 | 本地部署/API | 中文基准测试表现好 |

#### 2.3 中文场景推荐

如果你的项目主要处理中文文本（比如中文知识库、中文客服系统），模型选型的优先级大致是：

- 1.
	需要云端 API 且预算充足：阿里通义 text-embedding-v3，中文效果好，API 稳定

- 2.
	需要云端 API 且追求性价比：通过 SiliconFlow 等平台调用 Qwen3-Embedding 或 BGE 系列，价格更低

- 3.
	需要本地部署：BGE-M3 或 Qwen3-Embedding，开源可商用，中文效果优秀

- 4.
	中英文混合场景：BGE-M3，专门为多语言设计

> OpenAI 的 Embedding 模型在英文场景表现很好，但中文效果和国产模型比没有明显优势，加上 API 访问可能不稳定（你懂的），中文项目建议优先考虑国产模型。

### 3\. 向量维度怎么选

维度是选模型时绑定的——你选了某个模型，维度就确定了（部分模型支持多种维度输出，但大多数是固定的）。

那维度高好还是低好？

打个比方：维度就像描述一个人用了多少个特征。用 2 个特征（身高、体重）描述一个人，信息很有限，很多人会“撞衫”。用 100 个特征（身高、体重、肤色、发型、口音、走路姿势……）描述，区分度就高多了。

但特征越多，记录和比较的成本也越高。

实际项目中的权衡：

| 维度范围 | 适用场景 | 存储成本（100 万条） |
| --- | --- | --- |
| 256~512 | 简单场景，文本短、类目少 | 约 1~2 GB |
| 768~1024 | 大多数生产场景的甜蜜点 | 约 3~4 GB |
| 1536~4096 | 对精度要求极高的场景 | 约 6~16 GB |

> 对于大多数中文 RAG 项目，768 到 1024 维是一个比较稳妥的选择。既能保证足够的语义区分度，存储和检索成本也在可控范围内。除非你的场景对精度有极致要求（比如法律条文检索、医疗知识库等），否则不需要上 3072 或 4096 维。

## 相似度计算：怎么判断两个向量“像不像”

文本变成向量之后，下一步就是比较两个向量之间的相似程度。用户输入一个 query，系统把它转成向量，然后和知识库里所有 chunk 的向量逐一比较，找出最相似的几个——这就是语义检索的核心流程。

那怎么比较两个向量“像不像”？这就涉及到相似度计算。

### 1\. 余弦相似度——最常用的度量方式

余弦相似度（Cosine Similarity）是 Embedding 检索中最常用的相似度度量方式。

不讲公式，用一个直觉的类比：把每个向量想象成从原点出发的一个箭头。余弦相似度衡量的是两个箭头的方向有多接近。

- 两个箭头方向完全一致（夹角 0°）：余弦相似度 = 1.0，表示语义完全相同

- 两个箭头方向垂直（夹角 90°）：余弦相似度 = 0，表示语义完全无关

- 两个箭头方向相反（夹角 180°）：余弦相似度 = -1.0，表示语义完全相反

```
方向一致（相似度 ≈ 1.0）    方向垂直（相似度 ≈ 0）     方向相反（相似度 ≈ -1.0）
​
      ↗ A                        ↑ B                        ↗ A
     ↗ B                   A →                         ↙ B
```

为什么用方向而不是距离？因为 Embedding 向量的长度（模）可能不一样，但我们关心的是语义方向。两段文本可能一长一短，向量的模不同，但只要语义方向一致，余弦相似度就高。

#### 1.1 余弦相似度的计算逻辑

虽然不需要记公式，但了解计算逻辑有助于理解后面的代码。余弦相似度的计算分三步：

- 1.
	算两个向量的点积（对应位置的数字相乘，然后全部加起来）

- 2.
	算每个向量的模（每个数字的平方加起来，再开根号）

- 3.
	点积除以两个模的乘积

就这么简单。

### 2\. Java 代码示例：手动计算余弦相似度

```
public class CosineSimilarity {
​
    /**
     * 计算两个向量的余弦相似度
     *
     * @param vectorA 向量 A
     * @param vectorB 向量 B
     * @return 余弦相似度，范围 [-1.0, 1.0]
     */
    public static double calculate(double[] vectorA, double[] vectorB) {
        if (vectorA.length != vectorB.length) {
            throw new IllegalArgumentException(
                "两个向量的维度必须相同，vectorA: " + vectorA.length + ", vectorB: " + vectorB.length
            );
        }
​
        double dotProduct = 0.0;  // 点积
        double normA = 0.0;       // 向量 A 的模
        double normB = 0.0;       // 向量 B 的模
​
        for (int i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }
​
        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);
​
        // 避免除以零
        if (normA == 0 || normB == 0) {
            return 0.0;
        }
​
        return dotProduct / (normA * normB);
    }
​
    public static void main(String[] args) {
        // 模拟三个文本的向量（实际维度会高得多，这里用 5 维演示）
        double[] returnPolicy = {0.8, 0.1, 0.9, 0.2, 0.7};   // "七天无理由退货"
        double[] returnQuery = {0.75, 0.15, 0.85, 0.25, 0.65}; // "买了一周还能退吗"
        double[] logistics = {0.1, 0.9, 0.2, 0.8, 0.1};        // "物流配送时效说明"
​
        double sim1 = calculate(returnPolicy, returnQuery);
        double sim2 = calculate(returnPolicy, logistics);
​
        System.out.println("「七天无理由退货」vs「买了一周还能退吗」：" + String.format("%.4f", sim1));
        System.out.println("「七天无理由退货」vs「物流配送时效说明」：" + String.format("%.4f", sim2));
    }
}
```

运行结果：

```
「七天无理由退货」vs「买了一周还能退吗」：0.9972
「七天无理由退货」vs「物流配送时效说明」：0.5765
```

语义相近的两句话，相似度接近 1.0；语义不相关的两句话，相似度明显低很多。这就是余弦相似度的直觉。

> 上面用的是模拟向量，实际项目中向量是由 Embedding 模型生成的，维度通常是 768 或 1024。但计算逻辑完全一样。

### 3\. 相似度分数怎么解读

拿到一个相似度分数，怎么判断“够不够相关”？

这里没有绝对的标准，但有一些经验值可以参考：

| 相似度范围 | 含义 | 实际场景举例 |
| --- | --- | --- |
| 0.9 ~ 1.0 | 高度相关，几乎是同一个意思 | “退货流程”和“怎么退货” |
| 0.7 ~ 0.9 | 明显相关，主题一致 | “退货政策”和“商品能退吗” |
| 0.5 ~ 0.7 | 有一定关联，但不够紧密 | “退货政策”和“售后服务” |
| 0.3 ~ 0.5 | 关联很弱 | “退货政策”和“商品详情” |
| 0.0 ~ 0.3 | 基本无关 | “退货政策”和“天气预报” |

#### 3.1 检索阈值怎么设

在实际的 RAG 系统中，通常会设一个相似度阈值（threshold），只返回相似度高于阈值的结果。

常见的做法：

- 阈值设 0.7：比较严格，只返回高度相关的结果，准确率高但可能漏掉一些相关内容

- 阈值设 0.5：比较宽松，召回率高但可能混入一些不太相关的内容

- 不设阈值，只取 Top-K：返回相似度最高的 K 个结果（比如 Top-5），不管分数多少

> 实际项目中，建议先用 Top-K（比如 K=5）+ 阈值 0.6 的组合策略：先取相似度最高的 5 个，再过滤掉低于 0.6 的。具体阈值需要根据你的数据和场景调试，没有放之四海而皆准的数字。

#### 3.2 相似度分数受哪些因素影响

同样两段文本，用不同的模型算出来的相似度分数可能差很多。这是因为：

- 不同模型的训练数据不同，对语义的理解方式不同

- 不同模型的向量维度不同，表达能力不同

- 有些模型输出的向量已经做了归一化（长度为 1），有些没有

所以，相似度阈值不能跨模型套用。换了模型之后，阈值要重新调。

### 4\. 其他相似度度量方式（简要提及）

除了余弦相似度，还有两种常见的度量方式：

| 度量方式 | 核心思想 | 和余弦相似度的区别 | 常见使用场景 |
| --- | --- | --- | --- |
| 欧氏距离（Euclidean Distance） | 两个向量之间的直线距离 | 受向量长度影响，值越小越相似（注意方向相反） | 向量已归一化时效果和余弦相似度接近 |
| 点积（Dot Product） | 两个向量对应位置相乘再求和 | 同时考虑方向和长度，值越大越相似 | 向量已归一化时等价于余弦相似度 |

大多数[[01基础_09向量数据库的原理与选型|向量数据库]]（Milvus、Qdrant、Weaviate 等）都支持这三种度量方式。如果你不确定选哪个，选余弦相似度就对了——它对向量长度不敏感，适用范围最广。

## 动手实践：用 SiliconFlow API 跑通向量化全流程

概念讲了不少，该动手了。这一节我们用 SiliconFlow 平台提供的 Embedding API，通过 Java 原生 HttpClient 直接发 HTTP 请求，把文本转成向量，再做一次简单的相似度检索。

### 1\. SiliconFlow 平台介绍与 API Key 获取

SiliconFlow（硅基流动）是国内的一个 AI 模型推理平台，提供了多种大模型和 Embedding 模型的 API 服务。它的 Embedding API 兼容 OpenAI 的接口格式，用起来很方便。

注册和获取 API Key 的步骤：

- 1.
	打开 [SiliconFlow 官网](https://siliconflow.cn/) ，注册一个账号

- 2.
	登录后进入控制台，在“API 密钥”页面创建一个新的 API Key

- 3.
	把 API Key 复制下来，后面代码里要用

> SiliconFlow 对新用户有免费额度，跑本文的示例绑绰有余，不用担心费用。

我们用的模型是 `Qwen/Qwen3-Embedding-8B` ，这是通义千问团队开源的 Embedding 模型，对中文的支持非常好。

### 2\. Embedding API 的请求和响应格式

在写 Java 代码之前，先用 curl 感受一下这个 API 长什么样。

#### 2.1 请求格式

```
curl -X POST "https://api.siliconflow.cn/v1/embeddings" \
-H "Authorization: Bearer 你的API_KEY" \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen/Qwen3-Embedding-8B",
  "input": ["七天无理由退货"],
  "encoding_format": "float"
}'
```

三个关键字段：

- `model` ：指定用哪个 Embedding 模型

- `input` ：要转成向量的文本，可以是一个字符串，也可以是一个字符串数组（批量处理）

- `encoding_format` ：向量的编码格式， `float` 表示返回浮点数数组

#### 2.2 响应格式

```
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0123, -0.0456, 0.0789, ...]
    }
  ],
  "model": "Qwen/Qwen3-Embedding-8B",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

`data` 数组里的每个元素对应 `input` 里的一段文本， `embedding` 字段就是我们要的向量——一组浮点数。 `usage` 告诉你这次请求消耗了多少 token。

### 3\. Java 代码实现：用 HttpClient 调用 Embedding API

下面封装一个简单的 `EmbeddingClient` 工具类，用 Java 11+ 自带的 HttpClient 发请求，Jackson 解析 JSON。

#### 3.1 Maven 依赖

```
<dependencies>
    <!-- Jackson：JSON 解析 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.0</version>
    </dependency>
</dependencies>
```

> 除了 Jackson，不需要引入任何 AI 框架的依赖。Java 11+ 自带的 `java.net.http.HttpClient` 就够用了。

#### 3.2 EmbeddingClient 工具类

```
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class EmbeddingClient {

    private static final String API_URL = "https://api.siliconflow.cn/v1/embeddings";
    private static final String MODEL = "Qwen/Qwen3-Embedding-8B";

    private final String apiKey;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public EmbeddingClient(String apiKey) {
        this.apiKey = apiKey;
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
    }

    /**
     * 将一组文本转成向量
     *
     * @param texts 要向量化的文本列表
     * @return 每段文本对应的向量（double 数组）
     */
    public List<double[]> embed(List<String> texts) throws Exception {
        // 构造请求体
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", MODEL);
        requestBody.put("input", texts);
        requestBody.put("encoding_format", "float");

        String jsonBody = objectMapper.writeValueAsString(requestBody);

        // 发送 HTTP 请求
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(API_URL))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                .build();

        HttpResponse<String> response = httpClient.send(request,
                HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("API 调用失败，状态码：" + response.statusCode()
                    + "，响应：" + response.body());
        }

        // 解析响应，提取向量
        JsonNode root = objectMapper.readTree(response.body());
        JsonNode dataArray = root.get("data");

        List<double[]> embeddings = new ArrayList<>();
        for (JsonNode item : dataArray) {
            JsonNode embeddingNode = item.get("embedding");
            double[] vector = new double[embeddingNode.size()];
            for (int i = 0; i < embeddingNode.size(); i++) {
                vector[i] = embeddingNode.get(i).asDouble();
            }
            embeddings.add(vector);
        }

        return embeddings;
    }

    /**
     * 将单段文本转成向量（便捷方法）
     */
    public double[] embed(String text) throws Exception {
        return embed(List.of(text)).get(0);
    }
}
```

代码不复杂，核心就三步：构造 JSON 请求体 → 发 HTTP POST → 解析响应里的 `embedding` 数组。

#### 3.3 余弦相似度工具类

前面讲原理时写过余弦相似度的计算方法，这里直接复用：

```
public class CosineSimilarity {

    public static double calculate(double[] vectorA, double[] vectorB) {
        if (vectorA.length != vectorB.length) {
            throw new IllegalArgumentException("向量维度不一致");
        }

        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;

        for (int i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }

        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);

        if (normA == 0 || normB == 0) {
            return 0.0;
        }

        return dotProduct / (normA * normB);
    }
}
```

### 4\. 完整示例：从 chunk 到向量，再到相似度检索

现在把所有东西串起来。场景还是电商客服知识库：我们有一批 chunk（带元数据），先把它们向量化，然后用一个用户 query 做相似度匹配，找出最相关的 chunk。

```
import java.util.*;

public class EmbeddingSearchDemo {

    public static void main(String[] args) throws Exception {
        // 1. 初始化 EmbeddingClient（替换成你自己的 API Key）
        String apiKey = "sk-xxxxxxxxxxxxxxxxxxxxxxxx";
        EmbeddingClient client = new EmbeddingClient(apiKey);

        // 2. 准备知识库的 chunks（模拟前两篇分块 + 元数据的结果）
        List<Map<String, Object>> chunks = new ArrayList<>();

        chunks.add(Map.of(
                "content", "自签收之日起 7 天内，商品未经使用且不影响二次销售的，消费者可申请七天无理由退货。",
                "metadata", Map.of("doc_id", "policy_001", "title", "退货政策")
        ));
        chunks.add(Map.of(
                "content", "退货运费由消费者承担，如商品存在质量问题则由商家承担运费。",
                "metadata", Map.of("doc_id", "policy_001", "title", "退货政策")
        ));
        chunks.add(Map.of(
                "content", "订单发货后，物流信息将在 24 小时内更新。消费者可在订单详情页查看实时物流状态。",
                "metadata", Map.of("doc_id", "logistics_001", "title", "物流说明")
        ));
        chunks.add(Map.of(
                "content", "会员积分可在结算时抵扣现金，100 积分等于 1 元，每笔订单最多抵扣 50%。",
                "metadata", Map.of("doc_id", "member_001", "title", "会员权益")
        ));
        chunks.add(Map.of(
                "content", "生鲜类商品不支持七天无理由退货，签收后如有质量问题请在 48 小时内联系客服。",
                "metadata", Map.of("doc_id", "policy_002", "title", "生鲜退货政策")
        ));

        // 3. 批量向量化所有 chunks
        List<String> chunkTexts = new ArrayList<>();
        for (Map<String, Object> chunk : chunks) {
            chunkTexts.add((String) chunk.get("content"));
        }

        System.out.println("正在向量化 " + chunkTexts.size() + " 个 chunks...");
        List<double[]> chunkVectors = client.embed(chunkTexts);
        System.out.println("向量化完成，每个向量的维度：" + chunkVectors.get(0).length);

        // 4. 用户提问
        String query = "买了一周的东西还能退吗？";
        System.out.println("\n用户提问：" + query);

        // 5. 将用户问题也向量化
        double[] queryVector = client.embed(query);

        // 6. 计算 query 和每个 chunk 的相似度
        System.out.println("\n--- 相似度排名 ---");
        List<Map<String, Object>> results = new ArrayList<>();

        for (int i = 0; i < chunks.size(); i++) {
            double similarity = CosineSimilarity.calculate(queryVector, chunkVectors.get(i));
            Map<String, Object> result = new HashMap<>();
            result.put("index", i);
            result.put("content", chunks.get(i).get("content"));
            result.put("metadata", chunks.get(i).get("metadata"));
            result.put("similarity", similarity);
            results.add(result);
        }

        // 按相似度降序排列
        results.sort((a, b) -> Double.compare(
                (double) b.get("similarity"),
                (double) a.get("similarity")
        ));

        // 7. 输出结果
        for (int i = 0; i < results.size(); i++) {
            Map<String, Object> r = results.get(i);
            Map<String, Object> meta = (Map<String, Object>) r.get("metadata");
            System.out.printf("Top-%d [相似度: %.4f] [来源: %s]%n",
                    i + 1,
                    (double) r.get("similarity"),
                    meta.get("title"));
            System.out.println("  内容: " + r.get("content"));
            System.out.println();
        }
    }
}
```

### 5\. 运行结果分析

运行上面的代码，你会看到类似这样的输出：

```
正在向量化 5 个 chunks...
向量化完成，每个向量的维度：4096

用户提问：买了一周的东西还能退吗？

--- 相似度排名 ---
Top-1 [相似度: 0.7756] [来源: 退货政策]
  内容: 自签收之日起 7 天内，商品未经使用且不影响二次销售的，消费者可申请七天无理由退货。

Top-2 [相似度: 0.7122] [来源: 生鲜退货政策]
  内容: 生鲜类商品不支持七天无理由退货，签收后如有质量问题请在 48 小时内联系客服。

Top-3 [相似度: 0.6409] [来源: 退货政策]
  内容: 退货运费由消费者承担，如商品存在质量问题则由商家承担运费。

Top-4 [相似度: 0.5019] [来源: 会员权益]
  内容: 会员积分可在结算时抵扣现金，100 积分等于 1 元，每笔订单最多抵扣 50%。

Top-5 [相似度: 0.3914] [来源: 物流说明]
  内容: 订单发货后，物流信息将在 24 小时内更新。消费者可在订单详情页查看实时物流状态。
```

> 实际的相似度分数会因模型版本和 API 返回的精度略有不同，但排序趋势是一致的。

几个值得注意的点：

- 用户问的是“买了一周的东西还能退吗”，知识库里写的是“七天无理由退货”——关键词完全不同，但语义检索准确地把它排在了第一位。这就是 Embedding 的效果

- 排在第二的是“生鲜退货政策”，虽然它说的是“不支持退货”，但和“退货”这个主题高度相关，所以相似度也不低。这提醒我们：语义相似不等于答案正确，后续还需要 LLM 来理解和筛选

- “物流说明”和“会员权益”跟退货没什么关系，相似度明显低很多，符合预期

回头看一下整个流程：chunk 文本 → 调用 Embedding API → 得到向量 → 用户 query 也转成向量 → 计算余弦相似度 → 按相似度排序。这就是 RAG 检索环节的核心链路。

## 实际项目中的关键决策

跑通了 demo，离生产环境还有一段距离。这一节聊几个实际项目中绕不开的问题。

### 1\. 模型选型：云端 API vs 本地部署

| 对比维度 | 云端 API（以 SiliconFlow 为例） | 本地部署（以 Ollama 为例） |
| --- | --- | --- |
| 部署成本 | 零部署成本，按调用量付费 | 需要 GPU 服务器，一次性投入高 |
| 使用成本 | 按 token 计费，量大时费用可观 | 硬件折旧 + 电费，量大时单价低 |
| 延迟 | 受网络影响，通常 100~500ms | 本地调用，通常 10~50ms |
| 数据安全 | 文本需要发送到第三方服务器 | 数据不出内网，安全性高 |
| 维护成本 | 平台负责运维，省心 | 需要自己维护模型和服务 |
| 模型选择 | 平台提供多种模型，切换方便 | 需要自己下载和管理模型 |

#### 1.1 什么时候选云端 API

- 项目初期，数据量不大，想快速验证效果

- 团队没有 GPU 资源或运维能力

- 对数据安全要求不高（比如处理的是公开信息）

#### 1.2 什么时候选本地部署

- 数据量大，每天要向量化几十万甚至上百万条文本

- 对数据安全有严格要求（金融、医疗、政务等行业）

- 对延迟敏感，需要毫秒级响应

#### 1.3 用 Ollama 本地部署 Embedding 模型

如果你选择本地部署，Ollama 是最简单的方案，这个会放在后续章节讲述 Ollama 和 vLLM 部署方式。

> Ollama 的 Embedding API 格式和 SiliconFlow 略有不同，但核心逻辑一样。如果你的 `EmbeddingClient` 做了适当的抽象，切换起来改一下 URL 和请求格式就行。

### 2\. 批量向量化的性能优化

demo 里我们一次性把 5 个 chunk 传给 API，实际项目中可能有几万甚至几十万个 chunk。一次全传过去不现实（API 有请求大小限制），一个一个传又太慢。

#### 2.1 分批处理

最基本的优化：把 chunks 分成固定大小的批次，逐批调用 API。

```
/**
 * 分批向量化
 *
 * @param texts     所有待向量化的文本
 * @param batchSize 每批的大小（建议 20~50）
 * @return 所有文本的向量
 */
public List<double[]> embedInBatches(List<String> texts, int batchSize) throws Exception {
    List<double[]> allEmbeddings = new ArrayList<>();

    for (int i = 0; i < texts.size(); i += batchSize) {
        int end = Math.min(i + batchSize, texts.size());
        List<String> batch = texts.subList(i, end);

        System.out.printf("向量化进度：%d/%d%n", end, texts.size());
        List<double[]> batchEmbeddings = embed(batch);
        allEmbeddings.addAll(batchEmbeddings);

        // 简单的限流：每批之间等一下，避免触发 API 的速率限制
        if (end < texts.size()) {
            Thread.sleep(200);
        }
    }

    return allEmbeddings;
}
```

#### 2.2 并发控制

分批处理是串行的，如果 API 支持并发，可以用多线程加速：

```
import java.util.concurrent.*;

/**
 * 并发批量向量化
 */
public List<double[]> embedConcurrently(List<String> texts, int batchSize,
                                         int maxConcurrency) throws Exception {
    ExecutorService executor = Executors.newFixedThreadPool(maxConcurrency);
    List<Future<List<double[]>>> futures = new ArrayList<>();

    for (int i = 0; i < texts.size(); i += batchSize) {
        int start = i;
        int end = Math.min(i + batchSize, texts.size());
        List<String> batch = texts.subList(start, end);

        futures.add(executor.submit(() -> embed(batch)));
    }

    List<double[]> allEmbeddings = new ArrayList<>();
    for (Future<List<double[]>> future : futures) {
        allEmbeddings.addAll(future.get());
    }

    executor.shutdown();
    return allEmbeddings;
}
```

> 并发数不要设太高，一般 3~5 就够了。设太高容易触发 API 的速率限制（Rate Limit），反而更慢。

#### 2.3 错误重试

网络请求难免会失败，加一个简单的重试机制：

```
/**
 * 带重试的 embed 方法
 */
public List<double[]> embedWithRetry(List<String> texts, int maxRetries) throws Exception {
    Exception lastException = null;

    for (int attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return embed(texts);
        } catch (Exception e) {
            lastException = e;
            System.err.printf("第 %d 次调用失败：%s，%s%n",
                    attempt, e.getMessage(),
                    attempt < maxRetries ? "准备重试..." : "已达最大重试次数");

            if (attempt < maxRetries) {
                // 指数退避：第 1 次等 1 秒，第 2 次等 2 秒，第 3 次等 4 秒
                Thread.sleep(1000L * (1 << (attempt - 1)));
            }
        }
    }

    throw new RuntimeException("向量化失败，已重试 " + maxRetries + " 次", lastException);
}
```

### 3\. 向量化和元数据的关系

这个问题经常有人搞混，所以单独拎出来说。

一句话概括： **元数据不参与向量化，但和向量一起存入向量数据库** 。

打个比方：向量化就像给一本书拍了一张“语义照片”，元数据就是贴在照片背面的标签（作者、出版日期、分类等）。拍照的时候不需要看标签，但存档的时候标签要跟照片放在一起。

检索的时候，流程是这样的：

```
用户 query → 向量化 → 在向量数据库中做相似度匹配 → 拿到候选 chunks
                                        ↓
                              用元数据做二次过滤
                            （比如只要最近一年的、
                              只要用户有权限看的）
                                        ↓
                                  最终返回结果
```

所以在存储阶段，每个 chunk 在向量数据库里的记录通常包含三部分：

| 字段 | 内容 | 说明 |
| --- | --- | --- |
| id | chunk 的唯一标识 | 用于更新和删除 |
| vector | Embedding 模型输出的向量 | 用于相似度检索 |
| metadata | 元数据（JSON 格式） | 用于过滤和展示 |

大部分向量数据库（如 Milvus）还可以把原始文本也存进去，这样检索的时候不用再去别的地方取文本内容。

### 4\. 什么时候需要重新向量化

向量化不是一劳永逸的事。以下几种情况需要重新跑一遍：

#### 4.1 换了 Embedding 模型

不同模型生成的向量是不兼容的。模型 A 生成的向量和模型 B 生成的向量，维度可能不同，即使维度相同，语义空间也不一样，不能混在一起做相似度计算。

换模型 = 所有 chunk 重新向量化 + 向量数据库里的旧向量全部替换。

#### 4.2 文档内容更新

如果某份文档的内容改了（比如退货政策从 7 天改成了 15 天），对应的 chunk 文本变了，向量自然也要重新生成。

实际操作中，通常的做法是：

- 1.
	根据 `doc_id` 找到这份文档的所有旧 chunk

- 2.
	删除旧 chunk 的向量

- 3.
	对更新后的文档重新分块、向量化、存入向量数据库

这就是为什么前一篇强调元数据里要有 `doc_id` ——没有它，你很难知道哪些 chunk 属于同一份文档。

#### 4.3 分块策略调整

如果你调整了分块的大小或重叠策略（比如从 500 字一块改成 300 字一块），chunk 的内容变了，向量也要重新生成。

这种情况通常意味着全量重新向量化，工作量比较大。所以分块策略最好在项目初期就确定下来，别频繁改。

#### 4.4 模型升级

同一个模型的不同版本（比如 `text-embedding-v2` 升级到 `text-embedding-v3` ），生成的向量也可能不兼容。升级前要看模型提供方的说明，确认新旧版本的向量是否兼容。

> 一个实用的建议：在向量数据库的元数据里记录 `embedding_model` 和 `embedding_model_version` ，这样你随时知道每个向量是用哪个模型生成的，升级时也方便做灰度切换。

## 小结与下一篇预告

这一篇我们从“关键词检索为什么不够用”出发，一路讲到了向量化的原理、Embedding 模型的选型、相似度计算，最后用 SiliconFlow 的 API 跑通了一个完整的向量化检索 demo。

核心要点回顾：

- 向量化（Embedding）是把文本转成一组浮点数向量的过程，语义相近的文本在向量空间中距离也近

- Embedding 模型是这个转换的核心，选模型时重点关注中文效果、向量维度、API 成本三个指标

- 余弦相似度是最常用的向量相似度度量方式，值域 0~1，越接近 1 越相似

- 元数据不参与向量化，但和向量一起存储，检索时先向量匹配再元数据过滤

- 换模型、改文档、调分块策略都需要重新向量化，所以这些决策要尽早确定

到这里，RAG 的数据准备阶段就基本完成了：原始文档 → 分块（Chunking） → 元数据管理（Metadata） → 向量化（Embedding）。

但向量生成之后存到哪里？怎么在几百万个向量里快速找到最相似的那几个？普通数据库（MySQL、PostgreSQL）能存向量吗？这些问题的答案，就是下一篇要讲的——向量数据库（Vector Database）。

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51121244585524