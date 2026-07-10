# codedoc 抗幻觉三层核验与反思环解析

## 1. LLM 为什么会幻觉

幻觉 = LLM 编造不存在的东西。比如：
- 答案提到函数 `process_order()`，但代码库里根本没有
- 说"`place_order` 调用了 `validate_user`"，但图谱里没有这条边

为什么？LLM 是"概率预测下一个词"的模型，根据上下文"猜"最可能的内容，不保证真实。可能把别的项目函数名记混、根据问题顺理成章编一个、推理出"应该存在"但实际没有的关系。

必须解决：代码问答瞎编，用户照着不存在的函数改代码会出大问题。抗幻觉是刚需。

## 2. 整体方案：三层核验 + 反思环

```
LLM 生成答案
  ↓
第一层：符号级核验（答案里的符号在不在图谱）→ groundedness 分数
  ↓
第二层：关系级核验（说的"A调用B"有没有这条边）
  ↓
第三层：LLM 裁判（答案是否充分有据）—— 反思环里触发
  ↓
hedge 词检测（"未找到/无法回答"）
  ↓
groundedness < 0.5 或 含 hedge 词 → 触发反思：LLM 自评缺口 → 补检索 → 重答（1轮）
  ↓
重新核验 → 最终答案
```

代码在 `server.py`：
- `_build_graph_index`（1200）：建核验索引
- `_classify_ref`（1226）：单个引用分档
- `_verify_relationships`（1241）：关系级核验
- `_verify_response`（1265）：符号级+关系级汇总
- 反思环（1774-1812）：hedge/低groundedness → 自评 → 补检索 → 重答

## 3. 第一层：符号级核验（groundedness）

最核心的一层。思路：答案里提到的代码符号（反引号包起来的），去知识图谱查在不在。存在率 = groundedness。

### 3.1 建核验索引（_build_graph_index）

把知识图谱建成几个索引：
- `qname_set`：所有符号的全限定名集合（查"在不在"用）
- `name_to_qnames`：短名 → 全限定名集合（查"一个短名对应几个符号"用）
- `name_to_ids`：名 → 节点 id 集合
- `file_set`：文件名集合
- `edges`：所有边（关系级核验用）

### 3.2 提取答案里的引用

正则 `r"`([A-Za-z_][A-Za-z0-9_.]*)`"` 提取所有反引号包起来的符号。

为什么是反引号？因为 Synthesiser 的 system prompt 要求"提到符号用反引号标仓库"。所以反引号符号 = LLM 声称的代码引用，这些就是要核验的对象。

### 3.3 每个引用分档（_classify_ref）

五档：
- `exact`：精确命中全限定名（order.service.place_order 正好存在）
- `unique`：短名唯一对应一个符号
- `ambiguous`：一名多义（歧义）
- `file`：命中文件名
- `miss`：没找到（编的！）

还有个 `skipped`：纯小写单词（没有点）且在 _COMMON_WORDS 里（the/true等英文常用词），跳过不计入分母，避免误伤。

### 3.4 算 groundedness 分数

两个分数：
- `groundedness`（存在率）= (exact+unique+file+ambiguous) / 可统计总数
  - miss 不算"存在"，miss 越多 groundedness 越低
  - ambiguous 算"存在"（符号确实在，只是不能唯一定位）
- `specificity`（精确定位率）= (exact+unique+file) / 可统计总数
  - ambiguous 不算"精确"（一名多义对不上唯一符号）

groundedness < 0.5 意味着超过一半引用是编的，答案不扎实。

### 3.5 返回核验结果

- total_refs：引用总数
- valid_refs：有效引用（exact+unique+file）
- invalid_refs：编造的引用（miss）—— 标红给用户看
- ambiguous_refs：歧义引用
- groundedness：存在率
- specificity：精确定位率
- relationship_total / relationship_unsupported：关系核验结果
- cite_density：引用密度（引用数/词数×100）

## 4. 第二层：关系级核验（_verify_relationships）

查的是：答案里说的"A 调用 B""A 继承 B"这种关系，图谱里有没有这条边。

### 4.1 建边索引

把所有边按 kind 分组，存成 (src, dst) 集合，方便 O(1) 查。

### 4.2 正则找"关系语句"

_REL_KEYWORDS 是关系关键词和对应边类型的映射：
- "调用"、"calls" → calls 边
- "继承"、"extends" → extends 边

正则匹配：反引号符号A + 18字内 + 关系词 + 18字内 + 反引号符号B。
比如 `` `place_order` 调用了 `reserve` ``。

### 4.3 查边在不在

把 A、B 解析到节点 id，查 (A的id, B的id) 在不在对应 kind 的边集合里。
在 = supported（有据），不在 = unsupported（编造关系）。

跳过自指（A 关系 A 无意义）。
符号本身不在的交给符号级核验，关系级不重复罚（避免一个错误双重扣分）。

## 5. 第三层：LLM 裁判 + 反思环

### 5.1 什么时候触发反思

两个触发条件（满足任一）：
1. 答案含 hedge 词：("未找到", "无法回答", "没有足够", "上下文中未找到", "没有相关", "无法确定")
   - 这些词说明 LLM 自己都没把握
2. groundedness < 0.5
   - 超过一半引用是编的

### 5.2 LLM 自评缺口（第三层核验）

让 LLM 当裁判，判断答案是否"充分且有据"，输出 JSON：
- sufficient：true/false
- gap：如果不够，还缺什么（具体符号/信息）

这是第三层核验——LLM 裁判。和前两层区别：前两层是确定性代码查图谱，这层是 LLM 语义判断"答案质量"。

### 5.3 不够就补检索重答

如果 sufficient=false：
1. 拿 gap（缺口）当新查询，调 _retrieve_context 补检索
2. 把补充符号加进 allowed_set（限制 LLM 重答时只能用真实符号）
3. system prompt 追加"反思补检索"段，喂补充证据给 LLM
4. LLM 重新生成答案
5. 重新跑 _verify_response 核验

### 5.4 为什么只 1 轮

代码里整个反思块顺序执行一次，补检索重答后就往下走，不循环。
- 成本：每轮2次LLM调用（裁判+重答）
- 稳定性：多轮容易反复横跳
- 1轮已覆盖大部分缺口

### 5.5 降级兜底

整个反思块 try-except 包住，失败就跳过。不因反思挂了影响主流程。

## 6. 关键设计决策

### 为什么用反引号符号作为核验对象
Synthesiser 的 system prompt 要求提到符号用反引号。核验时正则提取的就是 LLM 声称的代码引用，精准。不强制反引号的话散文里的词没法区分是不是代码引用。

### 为什么 ambiguous 算"存在"不算"精确"
一名多义说明符号确实存在（groundedness不扣），只是不能唯一对上（specificity扣）。"存在"和"能定位"是两个不同标准。

### 为什么跳过英文常用词
LLM 可能用 "the"、"true" 这种词，不是代码符号。不跳过全当 miss 会拉低 groundedness 误伤。_COMMON_WORDS 排除掉。

### 为什么关系级不重复罚符号不存在的
如果 A 或 B 本身不在图谱（符号级已判 miss），关系级不再罚——避免一个错误双重扣分。

### 为什么反思要限制 allowed_set
重答时把补充的真实符号加进 allowed_set，限制 LLM 只能用这些真实符号。从源头防再编——与其事后查，不如事前限制。

### 为什么三层而不是一层
- 符号级：查"符号在不在"——快、确定性、覆盖面广
- 关系级：查"关系对不对"——符号都在但关系编了，符号级查不出
- LLM 裁判：查"答案够不够"——前两层查不出"答案没回答全"
三层互补，单层都有盲区。

## 7. 面试深问应答卡

### Q1：Agent 怎么保证不幻觉
A：三层核验+反思环。第一层符号级：反引号符号去图谱查在不在，算 groundedness；第二层关系级：说的"A调用B"去查有没有这条边；第三层LLM裁判：判断答案是否充分有据。groundedness<0.5或含hedge词触发反思：自评缺口→补检索→重答（1轮）。

### Q2：groundedness 怎么算的？阈值多少
A：反引号符号分五档（exact/unique/ambiguous/file/miss），groundedness = 存在的/可统计总数。miss是编的不算存在。<0.5触发反思。ambiguous算存在（符号确实在）但不算精确（一名多义对不上唯一）。

### Q3：关系级核验怎么做
A：正则找"A调用B"这种关系语句，把A、B解析到节点id，查(A,B)在不在对应kind的边集合。在=supported，不在=编造关系。符号本身不在的交给符号级，关系级不重复罚。

### Q4：为什么用反引号符号作为核验对象
A：Synthesiser的system prompt要求提到符号用反引号。核验时正则提取的就是LLM声称的代码引用，精准。不强制反引号散文里的词没法区分是不是代码引用。

### Q5：反思环什么时候触发？为什么只1轮
A：触发条件：含hedge词（未找到/无法回答等）或groundedness<0.5。只1轮因为：成本（每轮2次LLM调用）、稳定性（多轮反复横跳）、1轮已覆盖大部分缺口。

### Q6：反思重答时为什么要限制 allowed_set
A：把补充检索到的真实符号加进allowed_set，限制LLM重答只能用真实符号。从源头防再编——与其事后查，不如事前限制。

### Q7：三层核验为什么不合并成一层
A：三层互补有盲区。符号级查"符号在不在"（快、确定性）；关系级查"关系对不对"（符号都在但关系编了，符号级查不出）；LLM裁判查"答案够不够"（前两层查不出没回答全）。单层都有盲区。

### Q8：ambiguous 为什么算存在不算精确
A：一名多义说明符号确实存在（groundedness不扣），只是不能唯一对上（specificity扣）。"存在"和"能定位"是两个不同标准。

### Q9：为什么跳过英文常用词
A：LLM可能用 "the"、"true" 这种词，不是代码符号。不跳过全当miss会拉低groundedness误伤。_COMMON_WORDS排除掉。

### Q10：核验结果怎么给用户看
A：invalid_refs（编造引用）标红显示，groundedness以"引用可信度X%"徽章展示（高/中/低三档颜色）。让用户一眼看出哪些引用可能有问题。

## 8. 你要怎么准备

1. 打开 `server.py`，重点读 _build_graph_index（1200）、_classify_ref（1226）、_verify_relationships（1241）、_verify_response（1265）、反思环（1774-1812）
2. 背熟三层：符号级 groundedness + 关系级查边 + LLM 裁判
3. 背熟触发条件：hedge 词 或 groundedness<0.5 → 反思1轮
4. 能讲五档：exact/unique/ambiguous/file/miss
5. 能讲为什么三层不合并：各层有盲区互补
