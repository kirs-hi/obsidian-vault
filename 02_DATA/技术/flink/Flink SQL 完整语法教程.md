---
title: Flink SQL 完整语法教程
description: 涵盖 DDL、DML、查询、窗口、Join、数据类型、Changelog 语义、State 管理、调优、排障及端到端实战案例的 Flink SQL 全面教程
created: 2025-05-08
tags:
  - flink
  - flink-sql
  - 实时计算
  - 流处理
---

# Flink SQL 完整语法教程

## 一、核心概念

### 1.1 流批一体

Flink SQL 的最大特点是「流批一体」—— 同一套 SQL 语法既可以跑在无界流（Streaming）上，也可以跑在有界数据集（Batch）上。理解这一点是学好 Flink SQL 的前提：

- **流模式（Streaming）**：任务 7x24 持续运行，数据一条一条（或 mini-batch）处理，算子以 pipeline 形式同时运行。没有「分区」概念，没有「调度」概念。
- **批模式（Batch）**：任务一次性处理有限数据集，算子按 stage 依次执行，执行完即释放资源。等价于传统离线 SQL。

> **流批差异速查表**

| 特性 | 流模式 | 批模式 |
|------|--------|--------|
| 数据集 | 无界 | 有界 |
| ORDER BY | 仅支持时间属性排序 | 无限制 |
| LIMIT | 不支持（除 Top-N 写法） | 支持 |
| INSERT OVERWRITE | 不支持 | 支持 |
| 聚合结果 | 持续更新（Changelog） | 一次性输出 |
| 状态 | 需要管理、会膨胀 | 无状态问题 |
| 窗口 | 必须依赖时间属性 | 可以用普通列 |

### 1.2 Changelog 语义与回撤流

这是 Flink SQL 区别于传统 SQL **最核心**的概念。

在流模式下，一条 `GROUP BY` 的聚合查询并不是「算完就结束」，而是每来一条新数据就更新聚合结果。Flink 内部通过 **Changelog** 机制来描述这种「持续更新」：

- **INSERT-only（仅追加）**：Source 表通常是 INSERT-only 的（如 Kafka 的每条消息）。
- **Retract（回撤）**：当聚合结果需要更新时，Flink 先发一条 `-U`（撤回旧值），再发一条 `+U`（发送新值）。
- **Upsert（更新插入）**：有主键的情况下，只需发送最新值即可覆盖旧值（如写入支持 upsert 的外部存储）。

**影响：**

1. 不是所有 Sink 都能接收更新流。Kafka 普通 Sink 只能接收 INSERT-only 数据；如果查询产生了回撤流，需要使用 `upsert-kafka` 连接器或支持 upsert 的数据库（如 MySQL、HBase）。
2. 如果你的 SQL 产生了回撤流但 Sink 不支持，Flink 会直接报错：`Table sink doesn't support consuming update changes`。

**判断方法：** 以下操作会产生更新流：

- GROUP BY（不在窗口内的普通聚合）
- SELECT DISTINCT
- Regular Join（非窗口 Join）
- Top-N / Deduplication
- OVER 聚合

以下操作只产生追加流：

- 窗口聚合（TUMBLE/HOP/CUMULATE + GROUP BY window_start, window_end）
- Interval Join
- 简单的 SELECT ... WHERE 过滤

### 1.3 时间属性

Flink SQL 中有两种时间属性：

| 类型 | 定义方式 | 用途 |
|------|----------|------|
| 事件时间（Event Time） | `WATERMARK FOR col AS col - INTERVAL 'x' SECOND` | 基于数据本身的时间戳，支持乱序处理 |
| 处理时间（Processing Time） | 计算列 `proc_time AS PROCTIME()` | 基于机器系统时间，简单但不可重放 |

---

## 二、数据类型系统

Flink SQL 支持丰富的数据类型，理解类型系统可以避免大量「类型不匹配」的报错。

### 2.1 基础类型

| 分类   | 类型                                                       | 说明                             |
| ---- | -------------------------------------------------------- | ------------------------------ |
| 布尔   | `BOOLEAN`                                                | true/false                     |
| 整数   | `TINYINT` / `SMALLINT` / `INT` / `BIGINT`                | 1/2/4/8 字节整数                   |
| 浮点   | `FLOAT` / `DOUBLE`                                       | 单/双精度浮点                        |
| 精确小数 | `DECIMAL(p, s)`                                          | p=总位数, s=小数位数，金额计算必用           |
| 字符串  | `CHAR(n)` / `VARCHAR(n)` / `STRING`                      | STRING 等价于 VARCHAR(2147483647) |
| 二进制  | `BINARY(n)` / `VARBINARY(n)` / `BYTES`                   | 二进制数据                          |
| 日期时间 | `DATE` / `TIME(p)` / `TIMESTAMP(p)` / `TIMESTAMP_LTZ(p)` | LTZ 表示带时区                      |
| 间隔   | `INTERVAL YEAR TO MONTH` / `INTERVAL DAY TO SECOND`      | 时间间隔                           |

### 2.2 复合类型

```sql
-- 数组
ARRAY<INT>
ARRAY<STRING>

-- Map
MAP<STRING, INT>

-- Row（行类型，类似 struct）
ROW<name STRING, age INT>
ROW(name STRING, age INT)

-- 嵌套使用
ARRAY<ROW<id BIGINT, name STRING>>
```

### 2.3 类型转换

```sql
-- 显式转换
CAST(col AS BIGINT)
CAST(col AS VARCHAR)
CAST(col AS TIMESTAMP(3))

-- 安全转换（失败返回 NULL 而非报错）
TRY_CAST(col AS INT)

-- 常见场景：字符串 ↔ 时间戳
TO_TIMESTAMP('2024-01-01 12:00:00')                -- STRING → TIMESTAMP
DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm:ss')            -- TIMESTAMP → STRING
TO_TIMESTAMP_LTZ(1704067200000, 3)                 -- BIGINT 毫秒 → TIMESTAMP_LTZ(3)
```

### 2.4 隐式转换规则

Flink SQL 的隐式转换比较保守（相比 Hive），以下是常见的坑：

- `INT` 和 `BIGINT` 可以隐式互转
- `STRING` 不会自动转为 `TIMESTAMP`，必须显式 CAST
- `TIMESTAMP(3)` 和 `TIMESTAMP_LTZ(3)` 不能直接互转，需用 `TO_TIMESTAMP_LTZ` 或 `CAST`
- 聚合函数对 NULL 的处理：COUNT(*) 不忽略 NULL，COUNT(col) 忽略 NULL

---

## 三、DDL（数据定义语言）

### 3.1 CREATE TABLE

#### 完整语法

```sql
CREATE TABLE [IF NOT EXISTS] [catalog_name.][db_name.]table_name (
  { <physical_column_definition>
  | <metadata_column_definition>
  | <computed_column_definition> }[ , ...n]
  [ <watermark_definition> ]
  [ <table_constraint> ][ , ...n]
)
[COMMENT table_comment]
[PARTITIONED BY (partition_column_name1, partition_column_name2, ...)]
WITH (key1=val1, key2=val2, ...)
[ LIKE source_table [( <like_options> )] ]
```

#### 列的三种类型

**物理列（Physical Column）**—— 对应外部存储中真实字段：

```sql
CREATE TABLE orders (
  `order_id`   BIGINT,
  `user_id`    BIGINT,
  `amount`     DECIMAL(10, 2),
  `order_time` TIMESTAMP(3)
) WITH (...);
```

**元数据列（Metadata Column）**—— 读取连接器自带的元信息：

```sql
CREATE TABLE kafka_orders (
  `order_id`    BIGINT,
  `amount`      DECIMAL(10, 2),
  -- 读取 Kafka 消息的时间戳
  `kafka_ts`    TIMESTAMP_LTZ(3) METADATA FROM 'timestamp',
  -- 读取 Kafka 消息的 offset（只读，不写入 Sink）
  `kafka_offset` BIGINT METADATA FROM 'offset' VIRTUAL
) WITH ('connector' = 'kafka', ...);
```

**计算列（Computed Column）**—— 由表达式派生，主要用于定义时间属性：

```sql
CREATE TABLE orders (
  `order_id`    BIGINT,
  `amount`      DECIMAL(10, 2),
  `ts_seconds`  BIGINT,
  -- 计算列：将秒级时间戳转为 TIMESTAMP(3)
  `order_time`  AS TO_TIMESTAMP_LTZ(`ts_seconds` * 1000, 3),
  -- 处理时间列
  `proc_time`   AS PROCTIME(),
  -- Watermark
  WATERMARK FOR `order_time` AS `order_time` - INTERVAL '5' SECOND
) WITH (...);
```

#### Watermark 定义

```sql
WATERMARK FOR rowtime_column AS watermark_strategy_expression
```

三种策略：

```sql
-- 1. 有界无序（最常用）：允许 N 秒乱序
WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND

-- 2. 严格升序：不容忍任何乱序，一般不用
WATERMARK FOR order_time AS order_time

-- 3. 递增（允许相同时间戳）：一般不用
WATERMARK FOR order_time AS order_time - INTERVAL '0.001' SECOND
```

#### 主键约束

```sql
-- Flink 不强制执行，仅用于优化器推断和 Upsert 语义
PRIMARY KEY (order_id) NOT ENFORCED
```

#### WITH 子句

WITH 中的配置由 Connector 决定，常见连接器配置见后文第八章。

#### LIKE 子句

基于已有表创建新表，可复用 schema：

```sql
CREATE TABLE orders_with_wm (
  WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
) WITH (
  'scan.startup.mode' = 'latest-offset'
)
LIKE orders;
```

### 3.2 CREATE DATABASE / VIEW / FUNCTION

```sql
-- 建库
CREATE DATABASE IF NOT EXISTS my_db
  COMMENT '业务数据库';

-- 建视图（逻辑表，不存储数据，可简化复杂查询）
CREATE [TEMPORARY] VIEW order_stats AS
SELECT user_id, COUNT(*) AS cnt, SUM(amount) AS total
FROM orders
GROUP BY user_id;

-- 注册 UDF（标量函数 / 表函数 / 聚合函数）
CREATE [TEMPORARY] FUNCTION my_upper
  AS 'com.example.udf.MyUpperFunction'
  LANGUAGE JAVA;

CREATE [TEMPORARY] FUNCTION my_split
  AS 'com.example.udtf.MySplitFunction'
  LANGUAGE JAVA;
```

### 3.3 DROP / ALTER

```sql
DROP TABLE IF EXISTS orders;
DROP VIEW IF EXISTS order_stats;
DROP DATABASE IF EXISTS my_db CASCADE;  -- CASCADE 连带删除库下所有表

ALTER TABLE orders RENAME TO orders_v2;
ALTER TABLE orders SET ('scan.startup.mode' = 'latest-offset');
```

### 3.4 SHOW / DESCRIBE / EXPLAIN

```sql
SHOW CATALOGS;
SHOW DATABASES;
SHOW TABLES;
SHOW FUNCTIONS;

DESCRIBE orders;         -- 查看表结构
DESC orders;             -- 同上

EXPLAIN SELECT * FROM orders WHERE amount > 100;  -- 查看执行计划
```

---

## 四、Catalog 与多数据源管理

### 4.1 Catalog 体系

Flink SQL 使用三级命名空间：`catalog.database.table`。默认有一个 `default_catalog`（内存型），可注册外部 Catalog 实现跨数据源访问。

```sql
-- 注册 Hive Catalog（可直接访问 Hive 元数据中的所有表）
CREATE CATALOG my_hive WITH (
  'type' = 'hive',
  'hive-conf-dir' = '/etc/hive/conf'
);

-- 切换 Catalog / Database
USE CATALOG my_hive;
USE my_database;

-- 跨 Catalog 查询
SELECT * FROM default_catalog.default_database.kafka_orders k
JOIN my_hive.dw.dim_user u
  ON k.user_id = u.user_id;
```

### 4.2 常见 Catalog 类型

| Catalog 类型 | 说明 |
|-------------|------|
| GenericInMemoryCatalog | 默认内存型，任务停止即丢失 |
| HiveCatalog | 对接 Hive Metastore，持久化元数据 |
| JdbcCatalog | 对接 MySQL/PostgreSQL 的库表元数据 |
| IcebergCatalog | 对接 Iceberg 数据湖 |

---

## 五、DML（数据操作语言）

### 5.1 INSERT INTO

```sql
-- 基础写入
INSERT INTO target_table
SELECT user_id, item_id, behavior, ts
FROM user_behavior
WHERE behavior = 'buy';
```

### 5.2 多路输出（Statement Set）

一份 Source 数据同时写入多个 Sink，避免重复消费：

```sql
BEGIN STATEMENT SET;

INSERT INTO sink_buy
SELECT * FROM user_behavior WHERE behavior = 'buy';

INSERT INTO sink_cart
SELECT * FROM user_behavior WHERE behavior = 'cart';

INSERT INTO sink_pv
SELECT * FROM user_behavior WHERE behavior = 'pv';

END;
```

### 5.3 INSERT OVERWRITE（仅批模式）

```sql
INSERT OVERWRITE hive_table PARTITION (dt = '2024-01-01')
SELECT user_id, item_id, amount
FROM source_table;
```

---

## 六、查询语法

### 6.1 WITH 子句（CTE）

```sql
WITH filtered AS (
  SELECT order_id, user_id, amount
  FROM orders
  WHERE amount > 100
),
aggregated AS (
  SELECT user_id, SUM(amount) AS total
  FROM filtered
  GROUP BY user_id
)
SELECT user_id, total
FROM aggregated
WHERE total > 5000;
```

### 6.2 SELECT & WHERE

```sql
-- 字段选择、表达式计算、过滤
SELECT
  user_id,
  price * quantity AS total_cost,
  UPPER(category) AS category_upper
FROM orders
WHERE status = 'PAID'
  AND create_time > TIMESTAMP '2024-01-01 00:00:00';

-- VALUES 构造内联数据（适合测试）
SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob')) AS t(id, name);
```

### 6.3 SELECT DISTINCT

```sql
-- 流模式下会维护状态来去重，注意 state 膨胀
SELECT DISTINCT user_id, behavior
FROM user_behavior;
```

### 6.4 GROUP BY 分组聚合

```sql
-- 基础聚合（流模式下持续更新结果）
SELECT
  user_id,
  COUNT(*) AS action_cnt,
  SUM(amount) AS total_amount,
  MAX(ts) AS last_time
FROM orders
GROUP BY user_id;

-- GROUPING SETS
SELECT city, category, SUM(amount) AS total
FROM orders
GROUP BY GROUPING SETS ((city, category), (city), ());

-- ROLLUP（等价于从全限定到总计的所有组合）
SELECT city, category, SUM(amount)
FROM orders
GROUP BY ROLLUP (city, category);

-- CUBE（所有维度组合）
SELECT city, category, SUM(amount)
FROM orders
GROUP BY CUBE (city, category);
```

### 6.5 HAVING

```sql
SELECT user_id, COUNT(*) AS cnt
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 10;
```

### 6.6 JOIN

#### Regular Join（内连接 / 外连接）

```sql
-- 流模式下两边都维护全量状态，务必设置 State TTL
SELECT o.order_id, o.amount, u.name
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;

-- LEFT JOIN
SELECT o.order_id, u.name
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id;
```

#### Interval Join（时间区间关联）

限制两条流关联的时间范围，有效控制状态大小：

```sql
SELECT o.order_id, p.payment_id, p.pay_time
FROM orders o, payments p
WHERE o.order_id = p.order_id
  AND p.pay_time BETWEEN o.order_time AND o.order_time + INTERVAL '10' MINUTE;
```

#### Temporal Join（时态表关联）

关联维表的历史版本，获取事件发生时刻的维度值：

```sql
-- 前提：currency_rates 表有主键和事件时间，Flink 自动维护版本
SELECT o.order_id, o.currency, o.amount, r.rate,
       o.amount * r.rate AS cny_amount
FROM orders o
JOIN currency_rates FOR SYSTEM_TIME AS OF o.order_time AS r
  ON o.currency = r.currency;
```

#### Lookup Join（查找关联，维表 Join）

查询外部数据库维表（MySQL / HBase / Redis），最常用的维表关联方式：

```sql
-- 必须使用处理时间列进行 FOR SYSTEM_TIME AS OF
SELECT o.order_id, o.user_id, u.name, u.level
FROM orders AS o
JOIN user_dim FOR SYSTEM_TIME AS OF o.proc_time AS u
  ON o.user_id = u.user_id;
```

### 6.7 UNION / INTERSECT / EXCEPT

```sql
-- UNION ALL（保留重复）
SELECT user_id FROM table_a
UNION ALL
SELECT user_id FROM table_b;

-- UNION（去重）
SELECT user_id FROM table_a
UNION
SELECT user_id FROM table_b;

-- INTERSECT（交集）
SELECT user_id FROM table_a
INTERSECT
SELECT user_id FROM table_b;

-- EXCEPT（差集）
SELECT user_id FROM table_a
EXCEPT
SELECT user_id FROM table_b;
```

### 6.8 ORDER BY & LIMIT

```sql
-- 批模式：无限制
SELECT * FROM orders ORDER BY amount DESC LIMIT 100;

-- 流模式：ORDER BY 仅支持时间属性
SELECT * FROM orders ORDER BY order_time;
```

### 6.9 Top-N

利用 ROW_NUMBER() 实现持续维护的 Top-N：

```sql
-- 每个类别下金额 Top 3
SELECT category, order_id, amount
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY amount DESC) AS rn
  FROM orders
)
WHERE rn <= 3;
```

### 6.10 去重（Deduplication）

```sql
-- 按 order_id 去重，保留事件时间最早的一条
SELECT order_id, user_id, amount, order_time
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_time ASC) AS rn
  FROM orders
)
WHERE rn = 1;

-- 按 order_id 去重，保留处理时间最新的一条
SELECT order_id, user_id, amount
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY proc_time ASC) AS rn
  FROM orders
)
WHERE rn = 1;
```

---

## 七、窗口（Window）

### 7.1 窗口表值函数（TVF，Flink 1.13+ 推荐）

#### TUMBLE（滚动窗口）

固定窗口大小，窗口之间不重叠：

```sql
SELECT
  window_start, window_end,
  user_id,
  COUNT(*) AS cnt,
  SUM(amount) AS total
FROM TABLE(
  TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end, user_id;
```

#### HOP（滑动窗口）

窗口大小固定，步长 < 窗口大小时有重叠：

```sql
-- 窗口大小 10 分钟，每 5 分钟滑动一次
SELECT
  window_start, window_end,
  user_id,
  COUNT(*) AS cnt
FROM TABLE(
  HOP(TABLE orders, DESCRIPTOR(order_time), INTERVAL '5' MINUTE, INTERVAL '10' MINUTE)
)
GROUP BY window_start, window_end, user_id;
```

#### CUMULATE（累积窗口）

窗口在一个最大范围内按步长逐步扩大，适合做天内累计指标：

```sql
-- 每分钟更新当天累计 GMV
SELECT
  window_start, window_end,
  SUM(amount) AS cumulative_gmv
FROM TABLE(
  CUMULATE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE, INTERVAL '1' DAY)
)
GROUP BY window_start, window_end;
```

#### SESSION（会话窗口，Flink 1.18+）

按不活跃间隔自动划分会话：

```sql
SELECT
  window_start, window_end,
  user_id,
  COUNT(*) AS session_actions
FROM TABLE(
  SESSION(TABLE user_behavior PARTITION BY user_id, DESCRIPTOR(ts), INTERVAL '30' MINUTE)
)
GROUP BY window_start, window_end, user_id;
```

### 7.2 OVER 聚合（窗口函数）

```sql
-- 按时间范围：每个用户最近 1 小时的滚动求和
SELECT
  user_id, order_time, amount,
  SUM(amount) OVER w AS rolling_sum,
  COUNT(*) OVER w AS rolling_cnt
FROM orders
WINDOW w AS (
  PARTITION BY user_id
  ORDER BY order_time
  RANGE BETWEEN INTERVAL '1' HOUR PRECEDING AND CURRENT ROW
);

-- 按行数：最近 10 条记录的平均值
SELECT
  user_id, amount,
  AVG(amount) OVER (
    PARTITION BY user_id
    ORDER BY order_time
    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
  ) AS avg_last_10
FROM orders;
```

### 7.3 Window Top-N

```sql
-- 每小时窗口内销量 Top 3 的商品
SELECT *
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY sales DESC) AS rn
  FROM (
    SELECT window_start, window_end, item_id, SUM(quantity) AS sales
    FROM TABLE(
      TUMBLE(TABLE order_items, DESCRIPTOR(order_time), INTERVAL '1' HOUR)
    )
    GROUP BY window_start, window_end, item_id
  )
)
WHERE rn <= 3;
```

### 7.4 Window Join（窗口关联）

```sql
-- 两条流在同一个滚动窗口内关联
SELECT o.order_id, s.shipment_id
FROM TABLE(
  TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' HOUR)
) o
JOIN TABLE(
  TUMBLE(TABLE shipments, DESCRIPTOR(ship_time), INTERVAL '1' HOUR)
) s
ON o.order_id = s.order_id
AND o.window_start = s.window_start
AND o.window_end = s.window_end;
```

---

## 八、常用连接器配置

### 8.1 Kafka

```sql
CREATE TABLE kafka_source (
  `key`   STRING,
  `value` STRING,
  `ts`    TIMESTAMP(3) METADATA FROM 'timestamp',
  WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
  'connector'                    = 'kafka',
  'topic'                        = 'my_topic',
  'properties.bootstrap.servers' = 'broker1:9092,broker2:9092',
  'properties.group.id'          = 'flink-group',
  'scan.startup.mode'            = 'latest-offset',
  'format'                       = 'json'
);
```

### 8.2 Upsert-Kafka（支持回撤/更新语义）

```sql
CREATE TABLE upsert_sink (
  `user_id` BIGINT,
  `cnt`     BIGINT,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector'      = 'upsert-kafka',
  'topic'          = 'user_cnt',
  'properties.bootstrap.servers' = 'broker:9092',
  'key.format'     = 'json',
  'value.format'   = 'json'
);
```

### 8.3 JDBC（MySQL / PostgreSQL）

```sql
CREATE TABLE mysql_dim (
  `user_id` BIGINT,
  `name`    STRING,
  `level`   INT,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector'              = 'jdbc',
  'url'                    = 'jdbc:mysql://host:3306/db?useSSL=false',
  'table-name'             = 'dim_user',
  'username'               = 'root',
  'password'               = '******',
  'lookup.cache.max-rows'  = '5000',
  'lookup.cache.ttl'       = '10min',
  'lookup.max-retries'     = '3'
);
```

### 8.4 Filesystem（Hive / HDFS）

```sql
CREATE TABLE hdfs_sink (
  `user_id` BIGINT,
  `amount`  DECIMAL(10,2),
  `dt`      STRING
) PARTITIONED BY (dt) WITH (
  'connector'                              = 'filesystem',
  'path'                                   = 'hdfs:///data/warehouse/orders',
  'format'                                 = 'parquet',
  'sink.partition-commit.trigger'           = 'partition-time',
  'sink.partition-commit.delay'             = '1 h',
  'sink.partition-commit.policy.kind'       = 'success-file',
  'sink.rolling-policy.file-size'           = '128MB',
  'sink.rolling-policy.rollover-interval'   = '15 min'
);
```

### 8.5 HBase

```sql
CREATE TABLE hbase_dim (
  rowkey STRING,
  info ROW<name STRING, age INT>,
  PRIMARY KEY (rowkey) NOT ENFORCED
) WITH (
  'connector'    = 'hbase-2.2',
  'table-name'   = 'ns:user_info',
  'zookeeper.quorum' = 'zk1:2181,zk2:2181'
);
```

### 8.6 Elasticsearch

```sql
CREATE TABLE es_sink (
  `user_id` BIGINT,
  `cnt`     BIGINT,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'elasticsearch-7',
  'hosts'     = 'http://es-host:9200',
  'index'     = 'user_action_cnt'
);
```

---

## 九、内置函数速查

### 9.1 字符串函数

```sql
CONCAT(s1, s2, ...)                      -- 拼接
CONCAT_WS(sep, s1, s2, ...)              -- 带分隔符拼接
SUBSTRING(str, pos, len)                 -- 截取（pos 从 1 开始）
UPPER(str) / LOWER(str)                  -- 大小写转换
TRIM(BOTH ' ' FROM str)                  -- 去空格
LENGTH(str) / CHAR_LENGTH(str)           -- 字符长度
REPLACE(str, old, new)                   -- 替换
REGEXP_REPLACE(str, regex, replacement)  -- 正则替换
REGEXP_EXTRACT(str, regex, idx)          -- 正则提取
SPLIT_INDEX(str, sep, idx)               -- 按分隔符取第 N 段
LPAD(str, len, pad) / RPAD(str, len, pad) -- 填充
INITCAP(str)                             -- 首字母大写
OVERLAY(str PLACING new FROM pos FOR len) -- 替换子串
```

### 9.2 数值函数

```sql
ABS(x)                 -- 绝对值
ROUND(x, d)            -- 四舍五入保留 d 位小数
FLOOR(x) / CEIL(x)    -- 向下/向上取整
MOD(x, y)             -- 取模
POWER(x, y)           -- x 的 y 次幂
SQRT(x)               -- 平方根
LN(x) / LOG10(x) / LOG2(x)  -- 对数
RAND() / RAND(seed)   -- 随机数 [0, 1)
```

### 9.3 时间日期函数

```sql
CURRENT_DATE                              -- 当前日期
CURRENT_TIME                              -- 当前时间
CURRENT_TIMESTAMP                         -- 当前时间戳
LOCALTIMESTAMP                            -- 本地时间戳
NOW()                                     -- 等价于 CURRENT_TIMESTAMP
DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm:ss')   -- 时间戳格式化为字符串
TO_TIMESTAMP('2024-01-01 00:00:00')       -- 字符串转 TIMESTAMP(3)
TO_TIMESTAMP_LTZ(epoch_millis, 3)         -- 毫秒时间戳转 TIMESTAMP_LTZ(3)
FROM_UNIXTIME(unix_ts, format)            -- UNIX 秒级时间戳转字符串
UNIX_TIMESTAMP(str, format)              -- 字符串转 UNIX 时间戳（秒）
TIMESTAMPDIFF(unit, ts1, ts2)            -- 时间差（unit: SECOND/MINUTE/HOUR/DAY）
TIMESTAMPADD(unit, interval, ts)         -- 时间加减
EXTRACT(field FROM ts)                    -- 提取年/月/日/时/分/秒
YEAR(ts) / MONTH(ts) / DAYOFMONTH(ts)   -- 快捷提取
HOUR(ts) / MINUTE(ts) / SECOND(ts)      -- 快捷提取
DATE '2024-01-01'                         -- DATE 字面量
TIMESTAMP '2024-01-01 00:00:00'           -- TIMESTAMP 字面量
INTERVAL '1' DAY / INTERVAL '5' SECOND   -- 时间间隔字面量
```

### 9.4 条件函数

```sql
CASE WHEN cond1 THEN val1 WHEN cond2 THEN val2 ELSE val3 END
IF(condition, true_val, false_val)
COALESCE(val1, val2, val3, ...)      -- 返回第一个非 NULL 值
NULLIF(val1, val2)                   -- val1=val2 时返回 NULL
IS NULL / IS NOT NULL                -- NULL 判断
```

### 9.5 聚合函数

```sql
COUNT(*) / COUNT(col) / COUNT(DISTINCT col)
SUM(col) / AVG(col)
MIN(col) / MAX(col)
COLLECT(col)                  -- 聚合为 MULTISET（数组）
LISTAGG(col, separator)       -- 字符串聚合（类似 GROUP_CONCAT）
FIRST_VALUE(col)              -- 分组内第一个值
LAST_VALUE(col)               -- 分组内最后一个值
```

### 9.6 类型转换

```sql
CAST(col AS target_type)        -- 强制转换，失败则报错
TRY_CAST(col AS target_type)    -- 转换失败返回 NULL（不报错）
TYPEOF(expr)                    -- 返回表达式的类型字符串
```

### 9.7 集合函数

```sql
CARDINALITY(array_or_map)       -- 数组/MAP 长度
array[idx]                      -- 数组取值（从 1 开始）
map[key]                        -- MAP 取值
ARRAY[1, 2, 3]                  -- 构造数组
MAP['k1', 'v1', 'k2', 'v2']    -- 构造 MAP
```

### 9.8 JSON 函数

```sql
JSON_VALUE(json_str, '$.field')                  -- 提取标量值
JSON_QUERY(json_str, '$.array' WITH WRAPPER)     -- 提取 JSON 子对象/数组
JSON_EXISTS(json_str, '$.field')                 -- 判断路径是否存在
JSON_OBJECT('key1' VALUE val1, 'key2' VALUE val2) -- 构造 JSON 对象
JSON_ARRAY(val1, val2)                           -- 构造 JSON 数组
```

---

## 十、State 管理与 TTL

### 10.1 为什么流任务需要管理状态

Flink SQL 流任务中，以下操作会产生 **持久化状态**（state）：

| 操作 | 状态内容 | 是否无限增长 |
|------|----------|-------------|
| GROUP BY 聚合 | 每个 key 的聚合中间值 | 是（key 不断增加） |
| DISTINCT | 已出现过的值集合 | 是 |
| Regular JOIN | 双流各自的全量数据 | 是 |
| Interval JOIN | 时间区间内的数据 | 否（过期自动清理） |
| Top-N | 每个 partition 的 TopN 列表 | 否（固定大小） |
| Deduplication | 每个 key 的首条/末条记录 | 是 |

如果不设置 TTL，状态会无限增长，最终导致 OOM 或 Checkpoint 超时。

### 10.2 设置 State TTL

```sql
-- 全局设置：所有算子的状态 1 天后过期
SET 'table.exec.state.ttl' = '86400000';  -- 毫秒

-- 也可以写为可读格式（部分版本支持）
SET 'table.exec.state.ttl' = '1 d';
```

**TTL 的业务含义：** 状态过期后，如果该 key 的数据再次到来，Flink 会把它当作一个「全新的 key」来处理。比如 COUNT(*) 会从 1 重新开始计数。因此 TTL 的设置需要结合业务容忍度：如果你统计的是「今日 UV」，TTL 设为 24 小时就合理。

### 10.3 Hints 精细化控制 TTL

```sql
-- 不同表使用不同的 TTL
SELECT /*+ STATE_TTL('orders' = '1d', 'users' = '7d') */
  o.order_id, u.name
FROM orders o
JOIN users u ON o.user_id = u.user_id;
```

---

## 十一、性能调优

### 11.1 Mini-Batch 聚合

**原理：** 将逐条处理改为攒一批再处理，减少对状态后端的访问次数，显著提升吞吐。

```sql
SET 'table.exec.mini-batch.enabled' = 'true';
SET 'table.exec.mini-batch.allow-latency' = '5s';    -- 最大等待时间
SET 'table.exec.mini-batch.size' = '5000';            -- 最大攒批条数
```

**适用场景：** 聚合类查询（GROUP BY），能容忍秒级延迟的业务。

### 11.2 两阶段聚合（Local-Global）

**原理：** 类似 MapReduce 的 Combiner，先在本地做预聚合，再全局聚合。解决数据倾斜（某些 key 数据量远大于其他 key）。

```sql
SET 'table.optimizer.agg-phase-strategy' = 'TWO_PHASE';
```

**前提条件：** 聚合函数必须支持 merge（如 SUM、COUNT、MAX、MIN）。

### 11.3 Split Distinct 优化

**原理：** COUNT(DISTINCT col) 当 col 基数很大时容易倾斜。开启后 Flink 会在 DISTINCT 前加一层打散。

```sql
SET 'table.optimizer.distinct-agg.split.enabled' = 'true';
SET 'table.optimizer.distinct-agg.split.bucket-num' = '1024';
```

### 11.4 Lookup Cache

维表 Join 时，频繁查询外部存储（MySQL/HBase）会成为瓶颈。通过 Cache 减少查询次数：

```sql
CREATE TABLE dim_user (
  user_id BIGINT,
  name    STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector'              = 'jdbc',
  'url'                    = 'jdbc:mysql://host:3306/db',
  'table-name'             = 'user',
  'lookup.cache.max-rows'  = '10000',     -- 缓存行数上限
  'lookup.cache.ttl'       = '1h',        -- 缓存过期时间
  'lookup.max-retries'     = '3'          -- 查询失败重试次数
);
```

### 11.5 并行度设置

```sql
SET 'parallelism.default' = '8';  -- 默认并行度
```

**原则：**
- Source 并行度 = Kafka topic 的 partition 数
- 计算算子并行度根据数据量和 CPU 核数设定
- Sink 并行度根据下游承压能力设定

### 11.6 Checkpoint 调优

```sql
SET 'execution.checkpointing.interval' = '60s';         -- Checkpoint 间隔
SET 'execution.checkpointing.mode' = 'EXACTLY_ONCE';    -- 精确一次语义
SET 'execution.checkpointing.timeout' = '600s';          -- 超时时间
SET 'state.backend' = 'rocksdb';                         -- 大状态推荐 RocksDB
SET 'state.checkpoints.num-retained' = '3';              -- 保留最近 3 个 Checkpoint
```

---

## 十二、常见报错与排障

### 12.1 类型不匹配

```
Cannot apply '=' to arguments of type '<BIGINT> = <VARCHAR>'
```

**原因：** JOIN 或 WHERE 条件中两边类型不一致。
**解法：** 用 CAST 统一类型：`WHERE CAST(a.id AS VARCHAR) = b.id`

### 12.2 窗口不触发

**现象：** 窗口聚合始终无输出。
**常见原因：**
1. Watermark 不推进 —— Source 数据中的时间戳没有递增，或者某个 partition 没有数据导致 Watermark 停滞
2. Watermark 设置的乱序容忍时间太小，大量数据被视为迟到数据丢弃
3. 事件时间字段解析错误（如秒级时间戳被当作毫秒级）

**诊断方法：** 在 Flink Web UI 的 Watermark 面板查看各 subtask 的 Watermark 值是否在推进。

### 12.3 Sink 不支持更新流

```
Table sink 'xxx' doesn't support consuming update changes [...] 
```

**原因：** 查询产生了回撤/更新流（如包含 GROUP BY），但 Sink 只接受 INSERT-only。
**解法：** 换用支持 upsert 的 Sink（upsert-kafka、jdbc with primary key）或在查询中加窗口使结果变为 append-only。

### 12.4 State 过大 / OOM

**现象：** TaskManager OOM 或 Checkpoint 越来越慢。
**原因：** Regular JOIN 或 GROUP BY 的 key 持续增长，状态无限膨胀。
**解法：**
1. 设置合理的 State TTL
2. Regular JOIN 改为 Interval JOIN 或 Temporal JOIN
3. 使用 RocksDB state backend（状态存磁盘而非内存）

### 12.5 Kafka 消费积压

**现象：** Source 算子的 Records Lag 持续增大。
**解法：**
1. 增大 Source 并行度（与 Kafka partition 数对齐）
2. 检查下游算子是否有瓶颈（反压从下游传导到 Source）
3. 开启 Mini-Batch 提升下游吞吐

### 12.6 Checkpoint 超时

**现象：** Checkpoint 频繁失败，报 timeout。
**解法：**
1. 增大 `execution.checkpointing.timeout`
2. 减小状态大小（TTL、优化 JOIN 类型）
3. 开启增量 Checkpoint：`SET 'state.backend.incremental' = 'true';`
4. 排查是否存在数据倾斜导致某个 subtask 状态过大

---

## 十三、模式匹配（MATCH_RECOGNIZE）

**讲解：** CEP（复杂事件处理）的 SQL 化实现，用声明式语法识别事件序列中的模式。适用于风控、监控告警、用户行为分析等场景。

```sql
-- 场景：检测用户连续 3 次登录失败后紧跟 1 次成功
SELECT *
FROM login_events
MATCH_RECOGNIZE (
  PARTITION BY user_id
  ORDER BY event_time
  MEASURES
    FIRST(fail.event_time)  AS first_fail_time,
    LAST(fail.event_time)   AS last_fail_time,
    succ.event_time         AS success_time
  ONE ROW PER MATCH
  AFTER MATCH SKIP PAST LAST ROW
  PATTERN (fail{3} succ)
  DEFINE
    fail AS event_type = 'FAIL',
    succ AS event_type = 'SUCCESS'
) AS matched;
```

**语法要素说明：**

| 子句 | 作用 |
|------|------|
| PARTITION BY | 分组键，每组独立匹配 |
| ORDER BY | 事件排序字段（必须是时间属性） |
| MEASURES | 定义输出列（从匹配的事件中提取） |
| ONE ROW PER MATCH | 每次匹配输出一行（也可用 ALL ROWS PER MATCH） |
| AFTER MATCH SKIP | 匹配成功后从哪里继续匹配 |
| PATTERN | 用正则语法描述事件序列模式 |
| DEFINE | 定义模式中每个符号的条件 |

**Pattern 量词：**
- `A+`：一次或多次
- `A*`：零次或多次
- `A?`：零次或一次
- `A{3}`：恰好 3 次
- `A{2,5}`：2 到 5 次

---

## 十四、SET 配置参数汇总

```sql
-- ===== 基础运行参数 =====
SET 'parallelism.default' = '4';
SET 'pipeline.name' = 'my-flink-sql-job';

-- ===== Checkpoint =====
SET 'execution.checkpointing.interval' = '60s';
SET 'execution.checkpointing.mode' = 'EXACTLY_ONCE';
SET 'execution.checkpointing.timeout' = '600s';
SET 'execution.checkpointing.min-pause' = '30s';
SET 'state.backend' = 'rocksdb';
SET 'state.backend.incremental' = 'true';
SET 'state.checkpoints.num-retained' = '3';

-- ===== State TTL =====
SET 'table.exec.state.ttl' = '86400000';

-- ===== Mini-Batch =====
SET 'table.exec.mini-batch.enabled' = 'true';
SET 'table.exec.mini-batch.allow-latency' = '5s';
SET 'table.exec.mini-batch.size' = '5000';

-- ===== 聚合优化 =====
SET 'table.optimizer.agg-phase-strategy' = 'TWO_PHASE';
SET 'table.optimizer.distinct-agg.split.enabled' = 'true';
SET 'table.optimizer.distinct-agg.split.bucket-num' = '1024';

-- ===== 时区 =====
SET 'table.local-time-zone' = 'Asia/Shanghai';
```

---

## 十五、端到端实战案例

### 场景：实时电商大屏

需求：从 Kafka 读取订单流，关联 MySQL 用户维表获取地域信息，按 1 分钟窗口聚合出各城市 GMV，写入 MySQL 供大屏展示。

#### Step 1：定义 Source 表（Kafka 订单流）

```sql
CREATE TABLE orders (
  `order_id`    BIGINT,
  `user_id`     BIGINT,
  `amount`      DECIMAL(10, 2),
  `currency`    STRING,
  `order_time`  TIMESTAMP(3),
  -- Watermark：允许 10 秒乱序
  WATERMARK FOR order_time AS order_time - INTERVAL '10' SECOND
) WITH (
  'connector'                    = 'kafka',
  'topic'                        = 'orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id'          = 'flink-dashboard',
  'scan.startup.mode'            = 'latest-offset',
  'format'                       = 'json',
  'json.timestamp-format.standard' = 'SQL'
);
```

#### Step 2：定义维表（MySQL 用户信息）

```sql
CREATE TABLE dim_user (
  `user_id`  BIGINT,
  `name`     STRING,
  `city`     STRING,
  `level`    STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector'              = 'jdbc',
  'url'                    = 'jdbc:mysql://mysql:3306/ecommerce',
  'table-name'             = 'dim_user',
  'username'               = 'flink',
  'password'               = '******',
  'lookup.cache.max-rows'  = '10000',
  'lookup.cache.ttl'       = '10min',
  'lookup.max-retries'     = '3'
);
```

#### Step 3：定义 Sink 表（MySQL 聚合结果）

```sql
CREATE TABLE city_gmv_1min (
  `window_start`  TIMESTAMP(3),
  `window_end`    TIMESTAMP(3),
  `city`          STRING,
  `order_cnt`     BIGINT,
  `total_gmv`     DECIMAL(15, 2),
  PRIMARY KEY (window_start, window_end, city) NOT ENFORCED
) WITH (
  'connector'   = 'jdbc',
  'url'         = 'jdbc:mysql://mysql:3306/dashboard',
  'table-name'  = 'city_gmv_1min',
  'username'    = 'flink',
  'password'    = '******'
);
```

#### Step 4：编写查询逻辑

```sql
-- 配置优化参数
SET 'table.exec.mini-batch.enabled' = 'true';
SET 'table.exec.mini-batch.allow-latency' = '5s';
SET 'table.exec.mini-batch.size' = '5000';
SET 'table.local-time-zone' = 'Asia/Shanghai';

-- 核心查询：Lookup Join + 窗口聚合
INSERT INTO city_gmv_1min
SELECT
  window_start,
  window_end,
  u.city,
  COUNT(*)       AS order_cnt,
  SUM(o.amount)  AS total_gmv
FROM TABLE(
  TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE)
) AS o
-- Lookup Join：用处理时间关联维表获取最新用户信息
JOIN dim_user FOR SYSTEM_TIME AS OF o.order_time AS u
  ON o.user_id = u.user_id
GROUP BY window_start, window_end, u.city;
```

#### 执行效果

- Kafka 持续产生订单数据
- Flink 任务 24 小时运行，每分钟窗口关闭时将结果写入 MySQL
- 大屏服务从 MySQL 读取最新窗口数据做可视化展示
- 如果用户维表更新（如用户换了城市），由于使用 Lookup Join，下次关联自动拿最新值

---

## 十六、Hints（查询提示）汇总

```sql
-- Lookup Join 重试提示
SELECT /*+ LOOKUP('table'='dim_user', 
                  'retry-predicate'='lookup_miss', 
                  'retry-strategy'='fixed_delay', 
                  'fixed-delay'='10s', 
                  'max-attempts'='3') */
  o.order_id, u.name
FROM orders o
JOIN dim_user FOR SYSTEM_TIME AS OF o.proc_time AS u
  ON o.user_id = u.user_id;

-- State TTL 差异化设置
SELECT /*+ STATE_TTL('o' = '1d', 'u' = '7d') */
  o.order_id, u.name
FROM orders o
JOIN users u ON o.user_id = u.user_id;

-- 广播 Join 提示（小表广播）
SELECT /*+ BROADCAST(dim) */
  f.*, dim.name
FROM fact_table f
JOIN dim_table dim ON f.dim_id = dim.id;
```

---

## 附录：学习资源

- [Apache Flink 官方文档（中文）](https://nightlies.apache.org/flink/flink-docs-stable/zh/)
- [Flink SQL Cookbook（Ververica）](https://github.com/ververica/flink-sql-cookbook)
- [「Flink SQL 成神之路」系列（18 万字）](https://cloud.tencent.com/developer/article/1972190)