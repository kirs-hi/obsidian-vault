# Transformer / 模型架构面试真题专题

> 数据来源：尚硅谷企业面试真题 V1.1（153家企业）
> 提取结果：**110 道 Transformer/架构相关题目**，覆盖 **14 家企业**
> 涵盖：Attention、位置编码、KV Cache、vLLM、Flash Attention、MoE、BERT/GPT/LLaMA 等
> 排序规则：按「覆盖企业数」降序
> 生成时间：2025-06

---

## 一、子领域分布概览

| # | 子领域 | 覆盖企业数 | 题目数 |
|:---:|------|:---:|:---:|
| 1 | 其他架构相关 | 6 | 16 |
| 2 | vLLM/推理框架 | 6 | 16 |
| 3 | 位置编码/RoPE | 5 | 12 |
| 4 | BERT系列 | 5 | 7 |
| 5 | Transformer整体架构 | 4 | 10 |
| 6 | Attention机制原理 | 3 | 12 |
| 7 | LLaMA/开源模型 | 3 | 11 |
| 8 | KV Cache/推理优化 | 3 | 7 |
| 9 | 上下文长度/长文本 | 3 | 3 |
| 10 | Embedding | 2 | 5 |
| 11 | Encoder-Decoder | 2 | 2 |
| 12 | MoE/混合专家 | 2 | 2 |
| 13 | GPT系列 | 2 | 2 |
| 14 | 多头注意力/GQA/MQA | 1 | 2 |
| 15 | LayerNorm/归一化 | 1 | 1 |
| 16 | 解码策略/生成 | 1 | 1 |
| 17 | 激活函数 | 1 | 1 |

---

## 二、分类题目详情

### 其他架构相关（6家企业 / 16题）

1. 为什么要自己组合clip+GPT2 —— *反馈1： 一面*
2. clip如何与gpt结合的？ —— *反馈2： 一面*
3. Transformer的劣势，怎么改进？ —— *反馈1： 一面*
4. 如果用RNN来替代Transformer，怎么改进?❌ —— *反馈1： 一面*
5. transformer如何取代rnn —— *反馈1： 一面*
6. 为什么要自己组合clip+GPT2 —— *反馈1： 一面*
7. clip如何与gpt结合的？\ —— *一面*
8. 解码器编码器的优势 —— *一面*
9. Transformer的劣势，怎么改进？ —— *一面*
10. 如果用RNN来替代Transformer，怎么改进? —— *一面*
11. 多模态、rag、agent、强化学习、大模型架构 —— *一面*
12. transformer的qkv是什么 —— *一面*
13. pageattention底层优化 —— *一面*
14. Attention公示每个字符代表什么意思？ —— *北京忆芯（B2B公司，AISSD）*
15. 现在的大模型还有Transformer的发挥空间吗？ —— *世优科技*
16. gpt这种生成模型是怎么预测他的下一个token的呢，具体过程讲一下 —— *长湾创新科技*

---

### vLLM/推理框架（6家企业 / 16题）

17. vllm的优势 —— *一面*
18. 部署vllm —— *一面*
19. 部署的方向vllm —— *一面*
20. vllm底层逻辑 —— *一面*
21. 问的很细，选模型的原因、数据量、意图内容、训练的卡、Vllm部署、客户承载量、产品首token生成时间、每个模型的响应时间等全问了 —— *一面*
22. vllm怎么实现加速推理，内部原理是什么 —— *一面*
23. vllm的上下文长度扩展是怎么做的 —— *一面*
24. 为啥pytorch 和 vllm 用到两个去部署（感觉面试官是搞传统开发的） —— *一面*
25. Vllm怎么部署的，部署遇到什么问题了吗 —— *一面*
26. vllm底层如何优化 —— *一面*
27. 降低vllm成本的方式 —— *二面*
28. 模型是自己部署的吗，vllm的原理是什么 —— *黑云科技*
29. vllm调整过哪些参数来适配业务场景，比如qps1000+，延迟控制在5s —— *拼便宜*
30. vllm做过哪些参数调整 —— *极豆车联网*
31. 分布式部署？vllm和TensorRT有什么不同？ —— *杭州寰马*
32. 资源有限的情况，不能让一个vllm把资源吃完。 —— *杭州寰马*

---

### 位置编码/RoPE（5家企业 / 12题）

33. transformer如何取代rnn，transformer为啥要位置编码 —— *反馈2： 一面*
34. 怎么扩充上下文长度（RoPE怎么扩充的） —— *一面*
35. 为什么加位置编码，从数学角度呢 —— *一面*
36. transformer为啥要位置编码 —— *反馈1： 一面*
37. 旋转位置编码 KVcache 前归一化 后归一化的意义 —— *一面*
38. bert transformer位置编码的区别 —— *一面*
39. 图像有用到位置编码吗？ —— *一面*
40. clip的位置编码中，文本的位置编码、图像的位置编码加在哪里？ —— *一面*
41. 旋转位置编码的低频内插和高频外推有了解吗？ —— *一面*
42. 位置编码的作用，为什么用RoPE，不用绝对位置12345 —— *一面*
43. 位置编码 —— *福芮柚科技*
44. transformer架构、位置编码、梯度消失与梯度爆炸怎么解决、 —— *环球老虎财经*

---

### BERT系列（5家企业 / 7题）

45. 大模型定义，GPT和BERT差别 —— *反馈2： 一面*
46. GPT和BERT差别 —— *反馈1： 一面*
47. Bert、Llama和chatGLM的区别 —— *一面*
48. Roberta相对于bert做了哪些优化？ —— *一面*
49. Bert模型的架构 —— *一面*
50. 训练数据是人工标的吗，标签是怎么来的，你这个模型是qwen0.5b，为什么不考虑bert，模型的选择是怎么考虑的 —— *二面*
51. 实体识别怎么做的？什么BERT模型？哪一年？ —— *世优科技*

---

### Transformer整体架构（4家企业 / 10题）

52. transformer架构 与Qwen的不同 主流大模型相关 —— *一面*
53. transformer+Qwen和Deepseek架构+Lora微调+Prompt怎么用的+RAG如何提高召回率 —— *一面*
54. transformer的架构 —— *一面*
55. transformer架构 —— *一面*
56. 训练阶段，decoder-only的transformer架构模型，可以并行训练吗？ —— *一面*
57. Transformer架构 —— *一面*
58. 介绍Transformer架构 —— *一面*
59. transformer架构 —— *福芮柚科技*
60. Transformer的原理，从用户输入到模型输出，中间经历了什么？ —— *北京忆芯（B2B公司，AISSD）*
61. Transformer经典架构 —— *世优科技*

---

### Attention机制原理（3家企业 / 12题）

62. 其他涉及知识点：LoRA CNN RNN LSTM GRU 注意力机制 vit —— *反馈1： 一面*
63. transformer中attention机制 —— *一面*
64. Lora微调 原理 transfomer attention计算公式 —— *一面*
65. 问了agent nlp的基础问题包括位置编码 注意力机制等 —— *一面*
66. 多头自注意力机制，为什么要设置一个多头？ —— *一面*
67. 自注意力计算公式为什么要除以一个根号下Dk？\ —— *一面*
68. 介绍一下上下文窗口和注意力机制 —— *一面*
69. transformer 注意力计算公式，attention中除以的根号dk，dk代表的是什么 —— *一面*
70. 什么是注意力，具体解释怎么做 —— *一面*
71. Flash_attention原理 —— *一面*
72. 介绍下注意力机制 —— *一面*
73. 注意力机制 —— *福芮柚科技*

---

### LLaMA/开源模型（3家企业 / 11题）

74. Qwen3上下文长度、提示词工程 —— *反馈1： 一面*
75. qwen最新的大模型 —— *一面*
76. Qwen3上下文长度 提示词工程 —— *一面*
77. 大模型能不能数出Llama有几个l vit模型 —— *一面*
78. qwen3、deepseek架构。 —— *一面*
79. deepseek的moe改动有了解吗？ —— *一面*
80. qwen3的一些变体有了解吗？ —— *一面*
81. qwen3 8B的训练参数 多少卡 训多久 什么数据 —— *一面*
82. qwen和llama的架构区别 —— *一面*
83. qwen3-8B和qwen2.57B的区别 —— *一面*
84. qwen3的思考模式怎么开启 —— *黑云科技*

---

### KV Cache/推理优化（3家企业 / 7题）

85. KV Cache的作用 —— *一面*
86. 什么是kv cache，作用在哪儿 —— *一面*
87. vllm的核心技术，pagedattention —— *一面*
88. Vllm推理加速原理 —— *一面*
89. 国产显卡的推理加速有没有做过？不让用N卡。 —— *中恒博瑞*
90. kvcache为什么不保存q向量呢 —— *长湾创新科技*
91. kvcache,包括你所说的缓存都是怎么进行命中的呢 —— *长湾创新科技*

---

### 上下文长度/长文本（3家企业 / 3题）

92. 上下文长度 —— *反馈1： 一面*
93. 上下文长度 —— *一面*
94. 整个4b的模型是怎么微调的，上下文窗口多大 —— *黑云科技*

---

### Embedding（2家企业 / 5题）

95. embedding模型 —— *反馈1： 一面*
96. RAG里embedding模型和rerank模型的预训练目标，模型架构，损失函数 —— *一面*
97. embedding模型 —— *反馈1： 一面*
98. 有没有做过embedding模型的微调 —— *一面*
99. 为什么要用图谱而不是使用embedding直接向量相似度检索 —— *一面*

---

### Encoder-Decoder（2家企业 / 2题）

100. transformer没有编码器没有解码器 —— *反馈1： 一面*
101. transformer没有编码器没有解码器 —— *一面*

---

### MoE/混合专家（2家企业 / 2题）

102. moe的架构是什么 —— *一面*
103. Moe —— *福芮柚科技*

---

### GPT系列（2家企业 / 2题）

104. bert和gpt区别 —— *黑云科技*
105. gpt的结构他跟bert的区别，去掉编码器模型后有什么影响呢 —— *长湾创新科技*

---

### 多头注意力/GQA/MQA（1家企业 / 2题）

106. MHA MQA GQA —— *一面*
107. 多头的用处?除了提取不同的语义信息，还有啥作用（面试官说对于嵌入式设备，在部署上可能会好一些） —— *一面*

---

### LayerNorm/归一化（1家企业 / 1题）

108. Layer Normalization 还有 RMS —— *一面*

---

### 解码策略/生成（1家企业 / 1题）

109. Temperature参数作用讲解 —— *一面*

---

### 激活函数（1家企业 / 1题）

110. lora矩阵能否放在swiglu激活函数中 —— *一面*

---

## 三、最高频 TOP20 题目速查

| # | 题目 | 企业数 | 所属子领域 |
|:---:|------|:---:|------|
| 1 | Transformer的劣势，怎么改进？ | 2 | 其他架构相关 |
| 2 | transformer架构 | 2 | Transformer整体架构 |
| 3 | transformer没有编码器没有解码器 | 2 | Encoder-Decoder |
| 4 | 上下文长度 | 2 | 上下文长度/长文本 |
| 5 | Attention公示每个字符代表什么意思？ | 1 | 其他架构相关 |
| 6 | Bert、Llama和chatGLM的区别 | 1 | BERT系列 |
| 7 | Bert模型的架构 | 1 | BERT系列 |
| 8 | Flash_attention原理 | 1 | Attention机制原理 |
| 9 | GPT和BERT差别 | 1 | BERT系列 |
| 10 | KV Cache的作用 | 1 | KV Cache/推理优化 |
| 11 | Layer Normalization 还有 RMS | 1 | LayerNorm/归一化 |
| 12 | Lora微调 原理 transfomer attention计算公式 | 1 | Attention机制原理 |
| 13 | MHA MQA GQA | 1 | 多头注意力/GQA/MQA |
| 14 | Moe | 1 | MoE/混合专家 |
| 15 | Qwen3上下文长度 提示词工程 | 1 | LLaMA/开源模型 |
| 16 | Qwen3上下文长度、提示词工程 | 1 | LLaMA/开源模型 |
| 17 | RAG里embedding模型和rerank模型的预训练目标，模型架构，损失函数 | 1 | Embedding |
| 18 | Roberta相对于bert做了哪些优化？ | 1 | BERT系列 |
| 19 | Temperature参数作用讲解 | 1 | 解码策略/生成 |
| 20 | Transformer架构 | 1 | Transformer整体架构 |

---

## 四、Transformer / 架构备考建议

### 必须能完整讲述的

1. **Transformer 整体架构**：Encoder-Decoder 结构、Self-Attention 计算流程（Q/K/V → Scaled Dot-Product → Multi-Head）、残差连接与 LayerNorm 的位置。
2. **位置编码**：绝对位置编码 vs RoPE vs ALiBi，旋转位置编码的数学直觉，长度外推问题。
3. **KV Cache**：为什么需要缓存、内存占用计算、Paged Attention 的分页思路。
4. **vLLM 推理优化**：Continuous Batching、PagedAttention、Speculative Decoding、Tensor Parallelism。

### 必须有实战经验支撑的

1. **BERT vs GPT 对比**：双向 vs 单向、预训练任务差异、适用场景（理解 vs 生成）。
2. **LLaMA 系列改进**：RMSNorm、SwiGLU、RoPE、GQA 的设计选择和原因。
3. **Flash Attention**：IO-aware 设计、tiling 策略、与标准 Attention 的复杂度对比。
4. **Tokenizer 选型**：BPE / WordPiece / SentencePiece 差异、vocab size 对模型的影响。

### 加分项（体现深度）

1. MoE 架构：路由策略、负载均衡、专家数量与激活比例的trade-off。
2. 长上下文方案：NTK-aware RoPE、YaRN、Ring Attention。
3. 推理加速全栈：量化 + 投机解码 + 持续批处理 + 张量并行的组合方案。
4. Attention 变体：Sliding Window、Dilated Attention、Linear Attention 及其适用场景。

---

## 相关链接

- [[大模型面试高频考点TOP100|大模型面试高频考点 TOP100（精确版）]]
- [[RAG面试真题TOP100|RAG 面试真题专题]]
- [[Agent面试真题专题|Agent 面试真题专题]]
- [[微调面试真题专题|微调面试真题专题]]