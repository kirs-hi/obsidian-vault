---
url: https://cloud.tencent.com/developer/article/2635265
title: 从零开始学 Flink：Flink SQL 四大 Join 解析 - 腾讯云开发者社区 - 腾讯云
author: cloud.tencent.com
aliases: 
 - 
date: 2026-04-23 20:11:47
tags:

banner: "https://cloudcache.tencent-cloud.com/open_proj/proj_qcloud_v2/gateway/shareicons/cloud.png"
banner_icon: 🔖
---
在上一篇 [《从零开始学 Flink：实时数仓与维表时态 Join 实战》](https://cloud.tencent.com/developer/tools/blog-entry?target=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2FVns0dem00IhwuMcYoKEUuQ&objectId=2635265&objectType=1&contentType=undefined) 中，我们通过引入 Hive Catalog，解决了 Flink SQL 元数据管理的痛点。

今天，我们将目光聚焦于实时数仓建设中最核心、也最容易 “踩坑” 的环节——**多流关联（Join）**。

作为一名[大数据](https://cloud.tencent.com/product/bigdata-class?from_column=20065&from=20065)工程师，你可能经常面临这样的灵魂拷问：

*   _"为什么我的双流 Join 跑着跑着就 OOM 了？"_
*   _"为什么订单和支付数据都有，但 Join 出来的结果却是空的？"_
*   _"我想关联订单发生那一刻的用户等级，而不是现在的等级，怎么搞？"_

本文将基于 Flink 1.20+ 版本，结合真实的电商场景，深入剖析 **Regular Join**、**Interval Join**、**Temporal Join** 和 **Lookup Join** 的原理、应用场景及生产级优化策略。

### 环境准备

为了复现本文的实战案例，请确保你已配置好 Hive Catalog 环境（参考前文），并切换到 `ods` 库：

```
USE CATALOG myhive;
USE ods;

SHOW TABLES;

```

* * *

### 一、Regular Joins (常规 Join)：最灵活但也最危险

这是最符合 SQL 标准的 Join 方式，语法与传统离线 Hive SQL 几乎一致。

#### 1.1 场景：全量订单支付关联

业务需求很简单：查询每个订单的支付详情，不限制支付时间（哪怕支付比订单晚了一个月）。

##### 实战 SQL

```
INSERT INTO orders VALUES
('o_001', 'u_1', 50.00, TO_TIMESTAMP_LTZ(1773024000000, 3)), 
('o_002', 'u_2', 80.00, TO_TIMESTAMP_LTZ(1773027600000, 3)); 

INSERT INTO payments VALUES
('p_001', 'o_001', 50.00, 'WECHAT', TO_TIMESTAMP_LTZ(1773024600000, 3)), 
('p_002', 'o_002', 80.00, 'ALIPAY', TO_TIMESTAMP_LTZ(1773031200000, 3)); 


SELECT 
  o.order_id,
  o.order_amount,
  p.pay_amount,
  p.pay_method
FROM orders AS o
INNER JOIN payments AS p
ON o.order_id = p.order_id;

```

#### 1.2 生产避坑指南

Regular Join 的核心机制是 **Hash Join**。为了保证 “无论数据来得早晚都能关联上”，Flink 必须在 State 中 **永久保存** 左右两张流的所有历史数据。

**⚠️ 风险提示：State 爆炸**

如果不加限制，State 会随着时间无限膨胀，最终撑爆内存（OOM）或导致 Checkpoint 超时。

**🛠️ 解决方案：配置 State TTL**

在生产作业中，**必须** 配置表级别的状态生存时间（TTL）。例如，如果业务允许支付最大延迟为 24 小时：

```
SET 'table.exec.state.ttl' = '24 h';

```

_注：TTL 机制是基于 “最后访问时间” 的。如果一条数据在 TTL 时间内没有被访问（即没有匹配到），它就会被清理。一旦清理，后续再来的匹配数据就会导致 Join 失败（__数据丢失__）。_

* * *

### 二、Interval Joins (区间 Join)：时间窗口的魔法

为了解决 Regular Join 的状态膨胀问题，Flink 引入了 Interval Join。它利用流数据的 **Event Time（事件时间）** 属性，只缓存 “一段时间内” 的数据。

#### 2.1 场景：订单与支付的实时对账（下单后 1 小时内支付有效）

电商业务中，订单通常有支付时效（如 1 小时）。如果 1 小时内未支付，订单自动取消。因此，我们只需要关联 “下单时间” 前后一定范围内的支付数据。

##### 实战 SQL

```
INSERT INTO orders VALUES
('o_101', 'u_1', 100.00, TO_TIMESTAMP_LTZ(1773067260000, 3)), 
('o_102', 'u_2', 200.00, TO_TIMESTAMP_LTZ(1773067320000, 3)); 

INSERT INTO payments VALUES
('p_101', 'o_101', 100.00, 'WECHAT', TO_TIMESTAMP_LTZ(1773067860000, 3)), 
('p_102', 'o_102', 200.00, 'ALIPAY', TO_TIMESTAMP_LTZ(1773074520000, 3)); 


SELECT 
  o.order_id,
  o.order_time,
  p.pay_time,
  p.pay_amount
FROM orders o, payments p
WHERE o.order_id = p.order_id
AND p.pay_time BETWEEN o.order_time - INTERVAL '1' HOUR AND o.order_time + INTERVAL '1' HOUR;

```

#### 2.2 技术内幕

*   **状态自动清理**：Flink 会根据 Watermark 自动清理掉窗口之外的过期数据，**无需配置 TTL**。
*   **底层实现**：这是一个双流 Join，但 State 只保留 `[CurrentWatermark - UpperBound, CurrentWatermark + LowerBound]` 范围内的数据。
*   **适用性**：仅支持 Append-only 流（追加流），且必须定义 Watermark。

* * *

### 三、Temporal Joins (时态 Join)：穿越时空的快照

这是 Flink SQL 最具技术含量的功能，专门用于解决 **“关联数据变更历史”** 的问题。

#### 3.1 场景：用户等级权益回溯

在电商大促中，用户的 VIP 等级可能随时变化。计算订单优惠时，必须使用 **下单那一刻** 用户的 VIP 等级，而不是用户现在的等级。

这就需要我们构建一张 **版本表（Versioned Table）**，记录用户等级的所有变更历史。

#### 3.2 核心步骤

##### Step 1: 定义 Upsert Kafka 表（版本表）

我们需要一张能够处理 Changelog（变更日志）的表。这里使用 `upsert-kafka` 连接器。

```
SET 'table.exec.source.idle-timeout' = '1s';

CREATE TABLE vip_change_log (
  user_id STRING,
  vip_level STRING,
  discount_rate DECIMAL(3, 2),
  update_time TIMESTAMP_LTZ(3), 
  WATERMARK FOR update_time AS update_time - INTERVAL '5' SECOND,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'vip_change_log',
  'properties.bootstrap.servers' = '127.0.0.1:9092',
  'properties.group.id' = 'flink-vip-changes',
  'key.format' = 'json',
  'value.format' = 'json', 
  'value.json.timestamp-format.standard' = 'ISO-8601'
);

```

##### Step 2: 准备 “穿越” 数据

我们模拟用户 `u_2` 从 V1 升级到 V2 的过程，并插入不同时间点的订单。

```
INSERT INTO vip_change_log VALUES
('u_1', 'V1', 0.95, TO_TIMESTAMP_LTZ(1773064800000, 3)), 
('u_2', 'V1', 0.95, TO_TIMESTAMP_LTZ(1773064800000, 3)), 
('u_2', 'V2', 0.90, TO_TIMESTAMP_LTZ(1773068400000, 3));


INSERT INTO orders VALUES
('o_1', 'u_1', 100.00, TO_TIMESTAMP_LTZ(1773067260000, 3)), 
('o_2', 'u_2', 200.00, TO_TIMESTAMP_LTZ(1773067320000, 3)), 
('o_3', 'u_2', 300.00, TO_TIMESTAMP_LTZ(1773074760000, 3));

```

##### Step 3: 执行时态关联

使用 `FOR SYSTEM_TIME AS OF` 语法，告诉 Flink：“请去维表中查找 `o.order_time` 那个时刻的快照”。

```
SELECT
  o.order_id,
  o.user_id,
  o.order_time,
  v.vip_level,   
  v.discount_rate,
  o.order_amount * v.discount_rate AS pay_amount
FROM orders AS o
JOIN vip_change_log FOR SYSTEM_TIME AS OF o.order_time AS v
ON o.user_id = v.user_id;

```

**预期结果**：

*   订单 `o_2` (14:42) 关联到 `u_2` 的 V1 版本（95 折）。
*   订单 `o_3` (16:46) 关联到 `u_2` 的 V2 版本（90 折）。

#### 3.3 深度解析

*   **Rowtime 对齐**：Temporal Join 严格要求左右两表的 Rowtime 类型一致（如都为 `TIMESTAMP_LTZ(3)`）。
*   **Watermark 机制**：右表（维表）的 Watermark 必须推进，左表的数据才能被处理。如果右表数据很少，务必设置 `idle-timeout`，否则 Join 会卡住。

* * *

### 四、Lookup Join (维表 Join)：最常用的外部数据关联

前三种 Join 都要求数据在 Flink 内部流转，而 Lookup Join 则是去 **外部存储系统**（如 [MySQL](https://cloud.tencent.com/product/cdb?from_column=20065&from=20065), HBase, Redis）实时查询。

#### 4.1 场景：关联 MySQL 用户画像

通过 JDBC Connector 实时查询 MySQL 中的 `dim_user` 表，补全用户信息。

```
CREATE TABLE dim_user (
  user_id       STRING,
  user_name     STRING,
  city          STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:mysql://127.0.0.1:3306/realtime_dwh',
  'table-name' = 'dim_user',
  'username' = 'root',
  'password' = '1qaz@WSX',
  
  'lookup.cache.max-rows' = '5000', 
  'lookup.cache.ttl' = '10min'      
);


SELECT
  o.order_id,
  u.user_name,
  u.city
FROM orders AS o
JOIN dim_user FOR SYSTEM_TIME AS OF o.proc_time AS u
ON o.user_id = u.user_id;

```

#### 4.2 性能优化必读

Lookup Join 是典型的 **IO 密集型** 操作。

1.  **开启 Cache**：如上例所示，利用本地内存缓存热点维表数据，大幅减少[数据库](https://cloud.tencent.com/product/tencentdb-catalog?from_column=20065&from=20065)查询次数。
2.  **Async IO**：如果 Connector 支持（如 HBase, Redis），尽量开启异步查询，提高并发度。

* * *

### 五、工程师总结：Join 选型决策树

在实际开发中，面对复杂的业务需求，该如何选择 Join 策略？

<table><thead><tr><th><div></div></th><th><div></div></th><th><div></div></th><th><div></div></th><th><div></div></th></tr></thead><tbody><tr><td><div><p><strong>核心逻辑</strong></p></div></td><td><div><p>全量历史关联</p></div></td><td><div><p>时间窗口内关联</p></div></td><td><div><p>关联特定历史版本</p></div></td><td><div><p>关联外部静态 / 动态表</p></div></td></tr><tr><td><div><p><strong>状态压力</strong></p></div></td><td><div><p>⭐⭐⭐⭐⭐ (极大)</p></div></td><td><div><p>⭐⭐ (可控)</p></div></td><td><div><p>⭐⭐⭐ (取决于版本数)</p></div></td><td><div><p>⭐ (极小，无状态)</p></div></td></tr><tr><td><div><p><strong>IO 压力</strong></p></div></td><td><div><p>⭐ (本地内存)</p></div></td><td><div><p>⭐ (本地内存)</p></div></td><td><div><p>⭐ (本地内存)</p></div></td><td><div><p>⭐⭐⭐⭐⭐ (网络 IO)</p></div></td></tr><tr><td><div><p><strong>典型场景</strong></p></div></td><td><div><p>离线转实时、小表关联</p></div></td><td><div><p>订单支付对账、点击转化分析</p></div></td><td><div><p>汇率换算、权益回溯</p></div></td><td><div><p>关联用户画像、城市码表</p></div></td></tr><tr><td><div><p><strong>避坑关键</strong></p></div></td><td><div><p><strong>必须配 TTL</strong></p></div></td><td><div><p>必须有 Watermark</p></div></td><td><div><p>必须配 idle-timeout</p></div></td><td><div><p><strong>必须开 Cache</strong></p></div></td></tr></tbody></table>

希望这篇硬核解析能帮助你在生产环境中游刃有余地处理 Flink SQL Join。下一篇，我们将探讨 **Flink SQL 的窗口聚合（Window Aggregation）与 TopN 高级应用**。

* * *

原文链接: http://blog.daimajiangxin.com.cn