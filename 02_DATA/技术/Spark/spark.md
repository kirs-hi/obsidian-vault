# 一、Spark Join
 https://km.sankuai.com/collabpage/2747323466
 > Spark Join 主要有四种策略，优化器优先选 Broadcast Hash Join，其次 Shuffle Hash Join，默认大表走 Sort Merge Join，非等值走 Broadcast Nested Loop Join。
> 
> 判断逻辑主要看是否等值连接、是否存在小表可以广播以及内存条件。
> 
> 小表广播性能最好，因为没有 Shuffle。  
> 两张大表默认走 Sort Merge Join，因为它对内存依赖低。  
> 非等值连接只能走嵌套循环。
> 
> 实际项目中我会通过 explain 查看物理计划，重点关注是否发生数据倾斜、多对多膨胀，以及是否需要调整广播阈值或做倾斜优化。

Spark Join 底层其实就是把传统的 Hash Join 或 Sort Merge Join 做成分布式版本。  
先通过 Shuffle 把相同 key 的数据分到同一个分区，然后在 Executor 本地执行具体算法，比如构建哈希表或排序归并。  
Driver 负责选择策略，Executor 负责真正计算。

说完基本 90 分。
 
 
 **Spark Join 主要有 4 种核心策略：
 Broadcast Hash Join、Shuffle Hash Join、Sort Merge Join 和 Broadcast Nested Loop Join，优化器会按“能广播优先广播，其次哈希，最后排序归并，非等值走嵌套循环”的原则自动选择。**

在 Spark SQL 中，Join 的物理执行策略由 Catalyst 优化器根据**表大小、是否等值连接、内存条件、数据分布情况**自动决定。不同策略在性能、内存依赖、Shuffle 开销和数据倾斜敏感度方面差异很大。

---

### **一、Broadcast Hash Join（BHJ）—— 小表 + 大表，性能最好**

适用于：**等值连接 + 一张小表（小于广播阈值）**

核心机制是：  
将小表广播到所有 Executor 内存，本地构建哈希表，然后用大表逐行探测匹配。

特点：

- ✅ 无 Shuffle（只有一次广播）
- ✅ 时间复杂度 O(N+M)
- ✅ 执行速度最快
- ❌ 小表必须能放入 Executor 内存

关键参数：

```text
spark.sql.autoBroadcastJoinThreshold  (默认 10MB)
```

优化原则：  
只要能广播，一定优先选 BHJ。

---

### **二、Shuffle Hash Join（SHJ）—— 中等大小差异表**

适用于：**等值连接 + 不能广播 + 存在明显大小差异**

执行流程：

1. 两张表按 Join Key 做 Shuffle
2. 每个分区内对小分区构建哈希表
3. 用大分区做 Probe

特点：

- ✅ 时间复杂度 O(N+M)
- ✅ 无需排序
- ❌ Build 表单分区必须能放入内存
- ❌ 易发生数据倾斜

触发前提：

```text
spark.sql.join.preferSortMergeJoin = false
```

默认情况下 Spark 更倾向 SMJ。

---

### **三、Sort Merge Join（SMJ）—— 大表 + 大表默认方案**

适用于：**等值连接 + 两张大表 + 数据量接近**

执行流程：

1. 双表 Shuffle
2. 各分区排序
3. 归并匹配（双指针遍历）

特点：

- ✅ 内存依赖低（支持外部排序）
- ✅ 稳定性最好
- ✅ 默认策略
- ❌ 排序开销大

时间复杂度：

$$
O(N \log N + M \log M)
$$

默认参数：

```text
spark.sql.join.preferSortMergeJoin = true
```

如果没有广播条件，Spark 通常选 SMJ。

---

### **四、Broadcast Nested Loop Join（BNLJ）—— 非等值连接兜底**

适用于：

- 非等值连接（>、<、between、like）
- 或等值连接但无法触发其他算法

执行机制：

- 小表广播
- 大表逐行遍历
- 嵌套循环匹配

特点：

- ✅ 唯一支持非等值连接
- ❌ 时间复杂度 O(N×M)
- ❌ 极易产生数据膨胀
- ❌ 最容易 OOM

这是性能最差但最通用的兜底方案。

---

## Spark Join 选择逻辑（优化器思路）

可以总结为三步决策：

1. **能广播？** → Broadcast Hash Join  
2. **不能广播但能做哈希？** → Shuffle Hash Join  
3. **否则默认** → Sort Merge Join  
4. **非等值连接** → Broadcast Nested Loop Join  

---

## 性能排序（一般情况）

```
BHJ  >  SHJ  >  SMJ  >  BNLJ
```

---

## 实战建议

如果你在做性能调优，优先考虑：

- 收集统计信息（ANALYZE TABLE）
- 调整广播阈值
- 避免非等值大表 Join
- 处理数据倾斜（salting、拆分热点 key）
- 控制 shuffle 分区数

#  二、Spark Shuffle
  
> Spark 主要有 Hash Shuffle 和 Sort Shuffle 两种实现形式，目前生产默认是 Sort Shuffle。
> 
> 它通过 Map 端排序 + 合并输出文件来减少小文件问题。  
>  
> Shuffle 的优化主要包括：  
> 1. 文件数优化  
> 2. 内存 + spill 机制  
> 3. 网络批量拉取优化  
> 4. AQE 动态调整分区和 Join 策略  
>  
> Shuffle 本质是数据重分布，代价很高，所以调优核心是减少 Shuffle 次数和避免数据倾斜。
 主要有 Hash Shuffle 和 Sort Shuffle 两种核心形式，围绕“减少磁盘文件数、降低网络传输、缓解数据倾斜”做了大量优化。**

面试问到 Shuffle，一般考三点：

1. Shuffle 有哪几种实现形式  
2. 为什么要优化  
3. 做了哪些优化  

我帮你整理成一套“面试高分回答逻辑”。

---

## ✅ 一、Shuffle 的两种实现形式

### 1️⃣ Hash Shuffle（早期版本）

机制：

- 每个 Map Task
- 为每个 Reduce 分区单独写一个文件

如果：

- 1000 个 Map
- 200 个 Reduce

那么文件数 = 1000 × 200 = 20 万个文件

问题：

- 文件爆炸
- 磁盘 IO 巨大
- 小文件过多
- 文件句柄压力大

所以后来被优化。

---

### 2️⃣ Sort Shuffle（主流实现）

Spark 1.2 之后默认。

机制：

- Map 端先排序
- 相同分区的数据写在同一个文件
- 只生成一个数据文件 + 一个索引文件

优点：

- 文件数从 M × R 降到 M
- IO 更友好
- 支持大数据量 spill

这是现在生产默认实现。

---

## ✅ 二、Shuffle 做了哪些核心优化？

可以从 4 个方向回答。

---

### ✅ 优化 1：文件数优化（Consolidate + Sort）

目的：解决 Hash Shuffle 小文件爆炸问题。

措施：

- 引入 Sort Shuffle
- 合并文件输出
- 每个 Map Task 只生成 1 个数据文件

这是结构性优化。

---

### ✅ 优化 2：内存 + Spill 机制

Sort Shuffle 使用：

```
ExternalSorter
```

流程：

- 先在内存排序
- 内存不足时 spill 到磁盘
- 最后多路归并

好处：

- 支持 TB 级数据
- 防止 OOM

---

### ✅ 优化 3：网络传输优化

Spark 使用：

- BlockManager
- Netty 传输
- 批量拉取数据

优化点：

- 减少 RPC 次数
- 支持批量 fetch
- 使用 push-based shuffle（Spark 3.2+）

Push-based Shuffle：

- Map 端提前合并小块
- 减少 Reduce 拉取次数
- 降低网络压力

这是现在比较新的优化点，面试说出来加分。

---

### ✅ 优化 4：数据倾斜优化（最重要）

Shuffle 最怕：

```
某个 key 数据特别多
```

解决方案：

#### ① 调整 shuffle 分区数

```
spark.sql.shuffle.partitions
```

避免单分区过大。

---

#### ② Salting 技术

对热点 key 打随机前缀。

---

#### ③ AQE（Adaptive Query Execution）

Spark 3.x 引入：

- 自动合并小分区
- 自动拆分大分区
- 自动切换 Join 策略

例如：

- 运行时发现小表很小 → 自动改成 Broadcast Join
- 发现某个分区特别大 → 自动拆分

AQE 是近几年面试重点。

---

## ✅ 三、Shuffle 的完整执行流程（面试简洁版）

你可以这样说：

> Shuffle 分为 Map 阶段写文件和 Reduce 阶段拉取数据。  
> Map 端按分区写入本地磁盘，Reduce 端通过网络拉取对应分区数据，在本地合并后继续计算。

这句话非常标准。

---

## ✅ 四、面试加分点

如果对方问“为什么 Shuffle 很重？”

你可以说：

- 涉及磁盘 IO
- 涉及网络 IO
- 涉及序列化
- 涉及数据重分布

所以 Spark 优化的核心就是：

> 减少 Shuffle 次数

例如：

- 提前过滤
- 提前聚合（map-side combine）
- 使用 Broadcast Join

---

## ✅ 五、一套 1 分钟面试回答模板

你可以直接这样讲：

> Spark 主要有 Hash Shuffle 和 Sort Shuffle 两种实现形式，目前生产默认是 Sort Shuffle。  
> 它通过 Map 端排序 + 合并输出文件来减少小文件问题。  
>  
> Shuffle 的优化主要包括：  
> 1. 文件数优化  
> 2. 内存 + spill 机制  
> 3. 网络批量拉取优化  
> 4. AQE 动态调整分区和 Join 策略  
>  
> Shuffle 本质是数据重分布，代价很高，所以调优核心是减少 Shuffle 次数和避免数据倾斜。

这个回答已经属于高质量面试水平。

---

如果你愿意，我可以继续给你讲：

- 🔥 Shuffle 为什么会 OOM？
- 🔥 Shuffle 和 GC 的关系？
- 🔥 为什么 Sort Shuffle 更稳定？
- 🔥 Spark 和 Flink 的 Shuffle 有什么不同？

# Spark 内存模型
面试高频问题集中在“统一内存机制原理 + 参数调优思路 + OOM 排查经验”三大块，生产落地关键在合理分配 Executor 内存与避免数据倾斜。**

下面我帮你整理成**面试答题框架 + 生产实战经验**，你可以直接背结构。

---

## **一、面试高频问题整理（附标准回答思路）**

---

### **1️⃣ Spark 内存模型结构是怎样的？**

**回答框架：**

Spark Executor 内存主要分为：

1. Reserved Memory（系统预留）
2. User Memory（用户自定义对象）
3. Spark Memory（核心管理内存）

Spark Memory 采用统一内存管理模型（Spark 1.6 之后），分为：

- Execution Memory（执行内存）
- Storage Memory（存储内存）

两者共享一块内存区域，可以动态借用。

✅ Execution 优先级更高  
✅ Storage 可以被挤占  
✅ Storage 采用 LRU 淘汰

---

### **2️⃣ 什么是统一内存模型？为什么比静态模型好？**

旧版本（1.5 之前）：

- Execution 和 Storage 固定比例
- 不能互相借用
- 容易浪费

统一模型：

- 两者共享内存池
- Execution 可以向 Storage 借空间
- 提高内存利用率

✅ 本质：减少内存碎片 + 提升利用率

---

### **3️⃣ Execution Memory 和 Storage Memory 有什么区别？**

| 对比项 | Execution | Storage |
|--------|------------|----------|
| 用途 | shuffle、join、sort | cache、persist |
| 优先级 | 高 | 低 |
| 是否可被抢占 | 不可 | 可 |
| 空间不足处理 | 报 OOM | LRU 淘汰 |

面试加分点：

Execution 申请内存是按 Task 维度的，会进行公平分配。

---

### **4️⃣ Spark 为什么容易 OOM？**

常见原因：

1. 数据倾斜（单 Task 爆内存）
2. shuffle 过程内存不足
3. collect 拉大数据到 Driver
4. cache 太多
5. 广播变量过大
6. Executor 太小

回答时一定强调：

> Spark OOM 大多数不是内存真的不够，而是分配不合理或数据倾斜。

---

### **5️⃣ spark.memory.fraction 和 storageFraction 是干什么的？**

默认：

```
spark.memory.fraction = 0.6
spark.memory.storageFraction = 0.5
```

解释：

- 60% 堆内存给 Spark 管理
- 其中 50% 默认作为 Storage 上限

但是：

✅ 不是硬隔离  
✅ 只是初始比例  
✅ Execution 可以挤占 Storage

---

### **6️⃣ 堆外内存是干什么的？**

Tungsten 优化的一部分：

- 减少 GC
- 使用 Unsafe
- 提升 shuffle 性能

配置：

```bash
spark.memory.offHeap.enabled=true
spark.memory.offHeap.size=2g
```

适合：

- 大 shuffle
- 低 GC 延迟场景

---

## **二、生产中怎么用（实战经验）**

这里才是面试拉开差距的地方。

---

## ✅ 场景 1：大规模 shuffle 作业

问题：频繁 OOM / GC 时间长

优化策略：

1. 增加 executor memory
2. 增加 executor 数量，降低单 executor 压力
3. 调整：

```bash
spark.memory.fraction=0.7
```

4. 开启堆外内存
5. 调整 spark.sql.shuffle.partitions

核心思想：

> 减少单 Task 处理的数据量

---

## ✅ 场景 2：大量 cache 任务

问题：缓存总是被淘汰

解决方案：

- 增大 executor 内存
- 调整 storageFraction
- 使用 MEMORY_AND_DISK
- 避免 cache 超大宽表

经验：

生产中不建议随便 cache 全表，尤其宽表。

---

## ✅ 场景 3：数据倾斜导致单 Task OOM

判断方式：

- Spark UI 某个 Task 时间特别长
- 某个 Task 数据量远大于其他

解决：

1. 加盐
2. 随机前缀
3. 两阶段聚合
4. skew join 处理

面试加分说法：

> 内存模型本身没问题，是数据分布破坏了 Task 级内存均衡。

---

## ✅ 场景 4：Driver OOM

常见原因：

- collect()
- toPandas()
- 超大广播变量

解决：

- 不要 collect 大数据
- 设置：

```bash
spark.driver.memory
```

---

## 三、生产调优核心逻辑（建议背下来）

### 第一步：算资源

假设机器 64G：

- 留 10G 给系统
- 54G 给 YARN
- 每 Executor 6G
- 启 8 个 Executor

不要：

- 单 Executor 超过 10G（GC 会变慢）

---

### 第二步：避免大 Task

核心公式：

$$ 每个 Task 处理数据量 = 总数据量 / 分区数 $$

分区数太少 → 单 Task 爆内存  
分区数太多 → 调度开销大

---

### 第三步：优先解决数据倾斜

Spark 内存问题 80% 是数据倾斜导致。

---

## 四、面试终极回答模板（高分版本）

如果面试官问：

> 你在生产中怎么用 Spark 内存模型？

你可以这样答：

> Spark 1.6 之后采用统一内存模型，Execution 和 Storage 共享内存池，Execution 优先级更高。  
> 在生产中我们重点关注三点：  
> 第一是合理规划 Executor 数量和内存大小，避免单 Executor 过大导致 GC；  
> 第二是控制 shuffle 分区数，避免单 Task 数据过大；  
> 第三是排查数据倾斜，因为大多数 OOM 本质是数据分布不均。  
> 在大 shuffle 场景下我们会开启堆外内存并提升 memory fraction。  
> 对于 cache 任务会使用 MEMORY_AND_DISK 防止 OOM。

这段话基本是 90 分以上答案。

---

如果你愿意，我可以继续帮你整理：

- Spark 面试完整 30 问
- Spark 调优完整方法论
- Spark OOM 排查流程图
- Executor 参数计算公式推导

你是准备大数据面试，还是线上有具体问题？