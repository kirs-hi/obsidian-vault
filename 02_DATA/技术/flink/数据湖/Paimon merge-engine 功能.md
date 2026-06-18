在 Apache [[paimon|Paimon]] 中，主键表通过 **Merge Engine（合并引擎）** 来处理具有相同主键的多条记录，将它们合并成一条记录以保持主键的唯一性[3][4]。

根据不同的业务场景，Paimon 提供了 **四种** 主要的合并引擎[2][3]：

### 1. Deduplicate（去重引擎）
* **功能描述**：这是 Paimon 的**默认**合并引擎。当多条记录具有相同主键时，它会保留最新的一条记录，并丢弃其他旧记录[1][3]。
* **合并逻辑**：基于定义的顺序字段（如配置了 `sequence.field`）或数据的写入顺序来判断哪条记录是“最新”的[1]。
* **配置参数**：`'merge-engine' = 'deduplicate'`（默认可不填）[1]。
* **适用场景**：适用于需要数据去重（例如处理 Kafka 中的重复数据）或业务上仅需要保留数据最新状态的场景（如用户资料表）[1]。它具有很高的写入和查询性能[1]。

### 2. Partial Update（部分更新引擎）
* **功能描述**：支持列级别的更新。当多条记录具有相同主键时，它会按字段进行合并，使用新的非 NULL 字段值去覆盖旧的字段值[1][2]。
* **合并逻辑**：默认情况下，该引擎的设计逻辑是“按字段合并非 NULL 值”。需要注意的是，它默认无法处理 DELETE（删除）记录，如果需要处理，可以通过配置参数忽略删除操作[1]。
* **配置参数**：`'merge-engine' = 'partial-update'`。
* **特殊要求**：为了在[[数据湖项目|数据湖]]中生成和跟踪数据的变更日志，该引擎通常必须与特定的 Changelog Producer（如 `lookup` 或 `full-compaction`）配合使用[1][2][10]。

### 3. Aggregation（聚合引擎）
* **功能描述**：按指定的聚合函数对具有相同主键的记录进行聚合计算[2]。
* **合并逻辑**：当具有相同主键的新记录到达时，引擎不会简单地覆盖或忽略，而是根据为各个字段配置的聚合函数（如 SUM、MAX、MIN 等）将新旧数据进行聚合计算，最终保留聚合后的结果[2][5]。
* **适用场景**：适用于需要进行预聚合计算的指标统计场景，可以有效降低存储成本与下游计算压力[12]。

### 4. First Row（首行保留引擎）
* **功能描述**：与 Deduplicate 引擎的逻辑相反，它保留同一主键下到达的**第一条（首条）**记录[2][3]。
* **合并逻辑**：一旦某个主键的记录被写入，后续所有具有相同主键的新记录都会被直接丢弃。
* **适用场景**：适用于仅关注数据首次出现状态的场景（例如记录用户的首次登录信息、首次下单记录等）。

**总结：**
Paimon 提供的这四种 Merge Engine 非常灵活，用户可以根据具体的业务需求（如简单的去重、复杂的列级拼接、数值聚合或保留首条记录）来选择最合适的合并策略，从而更好地构建流批一体的数据湖仓[5][10]。


在 Apache Paimon 中，配置 Merge Engine（合并引擎）主要是通过在建表语句（如 [[Flink SQL 完整语法教程|Flink SQL]]）的 `WITH` 参数中指定 `'merge-engine'` 属性来实现的。创建 Paimon 表时，必须指定主键（`PRIMARY KEY`），因为合并机制是基于主键来触发的[1]。

以下是这四种合并引擎对应的具体语法和应用案例：

### 1. Deduplicate（去重引擎）
这是 Paimon 主键表的默认引擎。如果不显式指定，系统会自动采用此引擎，保留相同主键下的最新数据[1]。

**语法与案例：**
假设我们需要创建一张订单表，当同一订单号（`order_id`）的数据多次写入时，我们只保留最新的一条状态。
```sql
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT,
    order_status STRING,
    update_time TIMESTAMP(3),
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'merge-engine' = 'deduplicate' -- 默认引擎，此行可省略
    -- 'sequence.field' = 'update_time' -- 可选：指定根据哪个字段来判断“最新”
);
```

### 2. Partial Update（部分更新引擎）
用于将来自不同数据流的列更新合并到同一行中。如果新写入的数据中某些字段为 NULL，则保留旧数据中对应字段的值。

**语法与案例：**
假设我们有一个用户画像表，用户的基本信息（姓名、年龄）和扩展信息（城市、手机号）来自两个不同的 Kafka Topic，我们需要按 `user_id` 将它们拼接在一起。
```sql
CREATE TABLE user_profile (
    user_id BIGINT,
    user_name STRING,
    age INT,
    city STRING,
    phone STRING,
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'merge-engine' = 'partial-update',
    -- 部分更新引擎通常需要配合 changelog-producer 使用，以便下游能消费到完整的变更日志
    'changelog-producer' = 'lookup' 
);
```
*说明：流 A 写入 `(1, 'Alice', 25, NULL, NULL)`，流 B 写入 `(1, NULL, NULL, 'Beijing', '138xxxx')`，最终表中 `user_id=1` 的数据会被合并为 `(1, 'Alice', 25, 'Beijing', '138xxxx')`。*

### 3. Aggregation（聚合引擎）
允许对具有相同主键的记录进行字段级别的聚合计算（如求和、求最大值、求最小值等）。

**语法与案例：**
假设我们需要实时统计每个店铺（`shop_id`）的商品总销量（`total_orders`）和总销售额（`total_amount`）[1]。
```sql
CREATE TABLE shop_sales_stat (
    dt STRING,
    shop_id BIGINT,
    total_orders INT,
    total_amount DOUBLE,
    last_update_time TIMESTAMP(3),
    PRIMARY KEY (dt, shop_id) NOT ENFORCED
) PARTITIONED BY (dt) 
WITH (
    'merge-engine' = 'aggregation',
    -- 为具体的字段指定聚合函数
    'fields.total_orders.aggregate-function' = 'sum',    -- 对订单数求和
    'fields.total_amount.aggregate-function' = 'sum',    -- 对销售额求和
    'fields.last_update_time.aggregate-function' = 'max' -- 保留最新的更新时间
);
```
*说明：每次有新数据写入时，`total_orders` 和 `total_amount` 会自动累加，而 `last_update_time` 会更新为最大值。未指定聚合函数的字段默认取最新值。*

### 4. First Row（首行保留引擎）
只保留同一主键下第一次写入的数据，后续具有相同主键的数据将被直接忽略。

**语法与案例：**
假设我们需要记录用户的首次登录信息（如首次登录 IP 和时间），后续的登录记录不覆盖首次记录。
```sql
CREATE TABLE first_login_log (
    user_id BIGINT,
    login_ip STRING,
    login_time TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'merge-engine' = 'first-row'
);
```
*说明：当 `user_id=1001` 的第一条记录写入后，该用户的首次登录信息即被锁定。即使后续有新的 `user_id=1001` 数据到达，Paimon 也会将其丢弃，从而保证查询到的永远是首次状态。*

**💡 核心提示：**
在编写 Paimon DDL 语句时，`PRIMARY KEY (...) NOT ENFORCED` 是 Flink SQL 中定义主键的标准写法（表示主键约束由底层存储引擎 Paimon 来保证，而不是由 Flink 引擎强校验）[1]。通过灵活组合 `PARTITIONED BY`（分区）和 `WITH` 中的各种属性，可以满足极其复杂的实时湖仓建设需求。