---
name: Paimon在58交易数据的应用和实践
description: >-
  58同城基于Apache Paimon构建流式湖仓的实践总结。涵盖六大核心场景：主键表去重（替代ROW_NUMBER）、
  sequence.field乱序处理（替代Redis）、Paimon流读（替代Kafka中间层）、Aggregate Table数据聚合
  （替代Cumulate Window）、Lookup Join维表关联（替代HBase/MySQL/KV）、离线批处理修数。
  每个场景包含原有方案痛点、Paimon新方案、SQL示例及实际收益。适用于实时数仓架构升级和Paimon技术选型参考。
title: "Paimon在58交易数据的应用和实践"
source: "https://mp.weixin.qq.com/s/ZU-_ngAzebNgKdUGfgCbtQ"
author: "张云浩, 高剂斌"
published: 2025-08-07
created: 2026-04-23
tags:
  - clippings
  - Paimon
  - 实时数仓
  - Flink
  - 湖仓一体
---

# Paimon在58交易数据的应用和实践

> 原创 张云浩, 高剂斌 | 58技术 | 2025-08-07

![[paimon58_fig_00_cover.jpg]]

## 1 背景介绍

### 1.1 业务背景和原有实时数仓架构

交易数据相关的实时需求主要有两部分：一部分是需要给业务提供实时业绩数据，支持业务方业绩冲刺；另一部分是需要提供实时的当月新续会员数。

![[paimon58_fig_01.jpg]]
*图 1：原数据架构*

![[paimon58_fig_02.jpg]]
*图 2：原数据流转过程*

上图展示了之前的实时数仓计算架构。前面从 ODS 至 APP 的部分是实时链路，主要由 Flink、Kafka 和 HBase、MySQL 组成。此部分链路中的数据来自在线系统生成的交易数据日志。数据经过 WMB（公司自研的消息队列系统），使用 Flink Streaming 对其进行自定义的数据转换操作，将数据下发到 Kafka，后续流程使用 Flink SQL 构建实时数仓，最终结果落在 MySQL 中，供下游系统使用。

在 App 应用层，实时系统主要聚焦于实时当天数据的处理与分析。由于实时计算链路出于系统稳定性或资源优化的考量，通常无法存储完整的周期性数据，这导致实时计算产出的数据结果存在时效性限制。针对此类场景下关键指标的精确性要求，采用离线批处理与实时流计算相结合的混合架构，通过离线补算机制完善数据缺口，最终生成完整准确的最终结果。

### 1.2 原架构存在的问题

- **需求灵活多变**：在业务层面，随着业务需求的变化，每个环节都需要维护和开发，这在灵活性和效率上构成了重大挑战
- **开发成本高**：需要维护的组件较多（Kafka、HBase、Redis、MySQL 等），另外每次任务逻辑变更都会导致状态丢失，重复回溯数据验证数据逻辑费时费力
- **资源浪费**：数据在 MySQL 和 Hive 分别保存一份，造成数据冗余；Kafka 中的数据不能点查，每个流程中数据的中间计算结果都落在了 MySQL 保存一份用于排查问题，间接导致了资源浪费
- **数据口径不一致**：如果在某个业务系统中忘记或未能及时更新数据口径，输出的数据就会出现问题
- **运维成本高**：数据出现问题，排查需要投入大量时间和成本

## 2 基于Paimon构建流式湖仓

### 2.1 关于Paimon

Paimon 是一个实时数据湖格式，具备以下核心功能：

- **实时更新**：基于 LSM 树结构，支持主键表的高效流式更新（如去重、部分更新、聚合），并提供变更日志（Changelog）生成能力，简化流式分析。
- **流批一体**：统一支持流式与批处理操作，兼容 Flink、Spark、Hive 等引擎，实现数据湖的实时写入与离线分析。
- **OLAP 优化**：列式存储（默认 ORC 格式）、Z-order/Hilbert 排序、数据跳过（minmax 索引）等技术，加速复杂查询。
- **数据湖能力**：支持 ACID 事务、时间旅行（版本回溯）、可扩展元数据（PB 级存储）及模式演变。
- **分支管理**：无锁创建数据分支，支持独立测试、验证，通过快照和标签实现分支同步（Fast Forward）。
- **低成本与生态兼容**：依托对象存储（如 OSS/S3），降低存储成本，并无缝集成主流计算框架，构建 Streaming Lakehouse 架构。

### 2.2 Paimon流式湖仓架构及应用场景

下面是基于 Paimon 实现的流式湖仓架构及新数据流转过程：

![[paimon58_fig_03.jpg]]
*图 3：基于Paimon实现的流式湖仓架构*

![[paimon58_fig_04.jpg]]
*图 4：新数据流转过程*

项目在构建流式湖仓过程中，主要针对以下几个场景基于 Paimon 进行了实践：

#### 2.2.1 去重

在构建实时数仓的过程中，数据去重（即确保每条记录在主键维度上唯一）是一个非常关键且常见的需求。早期采用的是基于 Flink SQL 的 `ROW_NUMBER()` 窗口函数进行去重处理，这种方式虽然实现简单、逻辑清晰，但在面对高并发、大数据量场景时暴露出诸多性能瓶颈和维护难题。

为了提升系统整体的稳定性与效率，引入 **Paimon 主键表（Primary Key Table）** 来替代原有的去重逻辑，并取得了显著的效果。

**1）原有方案痛点分析 —— ROW_NUMBER()**

通常使用如下结构的 SQL 进行去重：

```sql
WITH ranked_data AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY event_time DESC) as rk
    FROM source_table
)
SELECT *
FROM ranked_data
WHERE rk = 1;
```

该语句通过窗口函数对相同主键的数据按时间排序并编号，只保留最新的一条记录。

**存在问题：**

- **资源消耗大**：需要全局排序，Shuffle 数据量巨大；内存占用高，尤其在窗口较大或数据倾斜严重时；Checkpoint 文件体积膨胀，影响任务稳定性
- **开发复杂度高**：每次去重都需要写冗长的 SQL，容易出错；不同层级的去重逻辑难以统一，维护成本高
- **数据一致性差**：如果数据乱序严重，可能造成错误的去重结果；下游消费时仍需再次处理，增加链路复杂性

**2）新方案探索 —— Paimon 主键表**

将原来通过 `ROW_NUMBER()` 去重生成的中间层表替换为 Paimon 主键表：

```sql
CREATE TABLE paimon_table (
    v_date STRING,
    id STRING,
    ...
    event_time TIMESTAMP,
    PRIMARY KEY (v_date, id) NOT ENFORCED
) PARTITIONED BY (v_date)
WITH (
    'merge-engine' = 'deduplicate',
    'bucket' = '4',
    'deletion-vectors.enabled' = 'true',
    'async-file-write' = 'true',
    'sort-spill-threshold' = '10',
    'lookup-wait' = 'false',
    'snapshot.num-retained.max' = '10000'
);
```

使用 Flink 流任务将原始数据直接写入 Paimon 表，无需手动去重：

```sql
INSERT INTO paimon_table
SELECT ... (数据逻辑)
```

由于 Paimon 主键表的 Merge 引擎会自动保留最后一条记录，因此等价于实现了 `ROW_NUMBER()` 的效果。

**3）下游消费方式优化**

下游任务可以直接以流的方式读取 Paimon 表的 Changelog，获取最新的变更数据，而无需再做额外的去重操作。

**4）实际收益总结**

| 具体收益 | 内容总结 |
|---------|---------|
| 资源效率显著提升 | CPU 和内存使用下降明显，资源利用率提升。Checkpoint 更加稳定，任务恢复速度更快。 |
| 开发维护更高效 | 原来的复杂去重逻辑被完全简化，只需定义主键即可。减少了多层任务之间的耦合，提升了系统的可维护性。 |

#### 2.2.2 数据乱序

在构建实时数仓的过程中，需要处理数据乱序问题。特别是在事件时间（Event Time）维度下，迟到的数据如果不加以控制，可能会导致状态更新错误或数据不一致，进而影响下游业务的准确性。

早期在 Flink 实时任务中通过 **Redis 缓存上一条记录的时间戳** 来判断当前数据是否为"新"数据，并决定是否进行更新操作。这种方式虽然简单有效，但在实际应用中也暴露出诸多问题。

引入了 Paimon 的 `sequence.field` 特性，实现了一种更优雅、高效且可扩展的数据去重与乱序判断机制。

**1）原有方案 —— Redis 缓存时间戳判断乱序**

核心逻辑如下：
- 使用 Flink 算子读取 Kafka 中的数据
- 每条数据携带一个事件时间字段（如 `event_time`）
- 在算子中使用 Redis 缓存该主键对应的最新事件时间
- 如果当前数据的 `event_time` 小于缓存值，则认为是过期数据，跳过处理
- 否则，更新 Redis 并继续后续流程

**存在问题：**

- **性能瓶颈明显**：每条数据都需要访问 Redis，造成网络 I/O 压力大；高并发场景下容易成为系统瓶颈
- **状态一致性难以保证**：Redis 是外部存储，无法与 Flink Checkpoint 联邦；出现故障恢复时，可能导致状态不一致或重复处理
- **开发耦合严重**：逻辑依赖 Redis，不利于组件解耦

**2）新方案探索 —— Paimon 的 sequence.field**

定义一张 Paimon 主键表并设置 `sequence.field` 参数：

```sql
CREATE TABLE paimon_table (
    v_date STRING,
    id STRING,
    ...
    event_time TIMESTAMP,
    PRIMARY KEY (v_date, id) NOT ENFORCED
) PARTITIONED BY (v_date)
WITH (
    'merge-engine' = 'deduplicate',
    'bucket' = '4',
    'sequence.field' = 'event_time',
    'deletion-vectors.enabled' = 'true',
    'async-file-write' = 'true',
    'sort-spill-threshold' = '10',
    'lookup-wait' = 'false',
    'snapshot.num-retained.max' = '10000'
);
```

Paimon 内部会自动根据 `event_time` 字段对相同主键的数据进行排序，只保留最新的那条记录。如果新写入的数据 `event_time` 更小，则会被忽略，从而实现了**乱序过滤 + 去重**的效果。

**3）实际收益总结**

| 具体收益 | 内容总结 |
|---------|---------|
| 无需额外状态管理 | 所有状态由 Paimon 自动管理，与 Flink Checkpoint 联邦。支持 Exactly-Once 语义。 |
| 天然支持乱序判断 | 不再依赖 Redis 或其他外部组件。通过字段比较即可完成数据有效性判断。 |
| 开发简洁易维护 | 只需定义字段名即可启用乱序判断功能。多个业务模块可复用同一套机制。 |
| 性能更高 | 所有计算都在写入端完成，避免了频繁的外部访问。LSM Tree 结构支持高效合并与索引查找。 |

#### 2.2.3 Paimon 流读

在原有的实时数仓架构中，Kafka 被用作中间消息队列，承担数据采集、缓冲和分发的角色。

**1）原有方案痛点分析 —— Kafka 消费架构**

**存在问题：**

- **数据不可查**：Kafka 是纯日志型存储，无法直接支持点查或范围查询；要想查询历史数据，必须重新消费 Topic，效率低下
- **状态管理复杂**：Kafka 只保存偏移量，具体的状态逻辑由 Flink 自己维护；频繁的 Checkpoint 和恢复操作容易导致状态膨胀或不一致
- **链路过长**：每层都需要独立的 Kafka Topic，增加了运维成本；数据重复传输浪费资源
- **难以修复数据**：一旦某一层处理出错，需从 Kafka 重新消费重跑整个链路

**2）新方案探索 —— Paimon 流读表**

将原本 Kafka 承担的部分职责迁移至 Paimon 表中，构建了一条更简洁、可查、易维护的实时链路。

定义 Paimon 表结构：

```sql
CREATE TABLE paimon_ods_table (
    v_date STRING,
    id STRING,
    ...
    event_time TIMESTAMP,
    PRIMARY KEY (v_date, id) NOT ENFORCED
) PARTITIONED BY (v_date)
WITH (
    'merge-engine' = 'deduplicate',
    'bucket' = '4',
    'sequence.field' = 'event_time',
    'deletion-vectors.enabled' = 'true',
    'async-file-write' = 'true',
    'sort-spill-threshold' = '10',
    'lookup-wait' = 'false',
    'snapshot.num-retained.max' = '10000'
);
```

将原始数据写入 Paimon 表，下游任务流式读取：

```sql
INSERT INTO paimon_ods_table
SELECT v_date, id, ..., event_time FROM source_table;

-- 下游任务可直接消费 Changelog 流
CREATE VIEW view_paimon_changelog_stream AS
SELECT * FROM paimon_ods_table;
```

**3）实际收益总结**

| 具体收益 | 内容总结 |
|---------|---------|
| 资源效率显著提升 | 减少了 Kafka 的频繁写入和读取压力。整体任务吞吐量提升了约 40%，Checkpoint 更加稳定。 |
| 开发维护更高效 | 所有数据统一写入 Paimon 表，无需再维护多个 Kafka Topic。流读和快照查询共用一套表结构，减少重复开发。 |

#### 2.2.4 数据聚合

原来在计算天粒度汇总数据的时候，使用到了累积窗口（Cumulate Window）来进行统计当天指标数据。

**1）原有方案痛点分析 —— Flink 累积窗口**

```sql
SELECT
    window_start, window_end, product_id,
    SUM(price) AS total_price
FROM TABLE(
    CUMULATE(TABLE order_table,
             DESCRIPTOR(event_time),
             INTERVAL '60' SECOND,
             INTERVAL '1' DAY)
)
GROUP BY window_start, window_end, product_id;
```

存在问题：性能瓶颈（Checkpoint 膨胀、内存线性增长）、开发复杂度高、数据一致性差（依赖 Watermark）、查询效率低。

**2）新方案探索 —— Paimon 的 Aggregate Table**

```sql
CREATE TABLE paimon_table (
    v_date STRING,
    agent_id STRING,
    score DECIMAL(20,4),
    update_time TIMESTAMP(3),
    PRIMARY KEY (v_date, agent_id) NOT ENFORCED
) PARTITIONED BY (v_date)
WITH (
    'merge-engine' = 'aggregation',
    'fields.score.aggregate-function' = 'sum',
    'fields.update_time.aggregate-function' = 'last_non_null'
);
```

Paimon 会自动根据主键合并数据，按聚合规则更新 `score` 和 `update_time`。

**3）实际收益总结**

| 具体收益 | 内容总结 |
|---------|---------|
| 资源效率显著提升 | 消除了 Flink 状态存储的压力，CPU 和内存使用下降明显。Checkpoint 大小减少 90%，任务恢复速度提升 70%。 |
| 开发维护更高效 | 所有聚合逻辑统一收口，减少重复开发。下游任务无需再编写复杂的窗口 SQL，直接订阅 Changelog 流即可。 |
| 数据一致性更强 | 主键更新的原子性保证了统计结果的准确性。不再依赖 Watermark 处理乱序数据，避免因延迟导致的重复计算。 |
| 支持更多业务场景 | 可广泛应用于实时报表（如 T+0 日报）、动态指标监控（如实时 GMV）等场景。为构建统一的指标中心提供了基础能力支撑。 |

> **注：** 若需求是静态聚合或最终结果，Paimon 的 Aggregate Table 可完全替代 Cumulate Window。若需求涉及时间驱动的累积计算，需结合 Flink 的窗口功能和 Paimon 的聚合能力。

#### 2.2.5 维表 Lookup Join

原有基于 HBase、KV 存储或 MySQL 的维度表 Join 方案暴露出链路复杂、维护成本高、扩展性差等问题。引入 Paimon 作为统一的数据湖仓存储引擎来重构。

**1）原有方案痛点**：MySQL 高并发瓶颈、HBase 运维成本高、维度表与事实表分散在不同系统、一致性风险、存储成本高。

**2）新方案 —— Paimon Lookup Join**

Paimon 提供两种缓存策略：FULL Cache 和 AUTO Cache。底层实现采用 Hash Store 或 RocksDB。

三种 Lookup Join 方式：

**1. Full Cache Lookup Table**

![[paimon58_fig_05.jpg]]
*图 5：Full Cache Lookup Join*

表启动时全量 Load 到本地 RocksDB，Lookup 效率高但磁盘需求大、启动慢。

**2. Local PrimaryKey Partial Lookup Table**

![[paimon58_fig_06.jpg]]
*图 6：Local PrimaryKey Partial Lookup Join*

数据触发文件 Load，基于 LSM Tree 有序性定位查找。不需要缓存全部数据，但缓存效率较差。适用场景：`HASH_FIXED` 的 PK 表，PK 与 JoinKey 相同。

**3. Bucket Shuffle Lookup Table**

![[paimon58_fig_07.jpg]]
*图 7：Bucket Shuffle Lookup Join*

Lookup Join 算子前插入 Custom Shuffle，一个 Task 只加载一个 Bucket 的数据。适用场景同上。（Flink 1.20 版本可用）

Paimon 维度表示例：

```sql
CREATE TABLE `dim_table` (
    `id` BIGINT NOT NULL COMMENT 'id',
    `name` STRING COMMENT '名称',
    `category` STRING COMMENT '品类',
    `category_name` STRING COMMENT '品类名称',
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
    'bucket' = '4',
    'sort-spill-threshold' = '10',
    'changelog-producer.lookup-wait' = 'false',
    'snapshot.num-retained.max' = '30'
);
```

事实表关联维表：

```sql
SELECT t1.id, t1.product_id,
    t2.name AS product_name, t2.category, t2.category_name
FROM (
    SELECT id, product_id, PROCTIME() AS proc_time
    FROM source_table
) t1
LEFT JOIN dim_order_info
FOR SYSTEM_TIME AS OF t1.proc_time AS prd_info
ON t1.product_id = prd_info.id;
```

> **调优建议**：lookup 算子并发度设置为分桶数的约数；增大 `lookup.cache-max-memory-size`（默认 256M）或 `lookup.cache-rows`（默认 10000）提高查询效率。

**3）实际收益总结**

| 具体收益 | 内容总结 |
|---|---|
| 统一数据管理平台 | 将原本分散在多个系统中的数据集中到数据湖仓中管理。支持标准 SQL 查询和写入操作。 |
| 精简数据流程架构 | 不再依赖额外的 KV 或 MySQL 系统，减少数据链路复杂度，降低运维成本。 |

> **注意缺陷**：Paimon 在高频更新场景下表现有限，时效性受 Checkpoint 时长制约，更适合低频更新维表。扩展能力依赖 Flink 计算节点横向扩展。

#### 2.2.6 离线批处理

**数据修复（Data Repair）** 是高频且关键的操作。早期依赖 ODS 层重新消费来修数，存在效率低、资源消耗大、维护成本高等问题。

引入 Paimon 批处理能力，通过主键表、Changelog 流式输出和 LSM Tree 结构实现离线批处理修数。

![[paimon58_fig_08.jpg]]
*图 8：批处理修数流程*

**修数流程**：停掉 DWD 层及后续 Flink 实时任务 -> 通过 Spark SQL 读取 Paimon 表执行修复逻辑 -> 修复完成后重启 DWD 层从指定时间戳消费增量数据 -> 重新启动 Flink 实时任务。

**实际收益总结**

| 具体收益 | 内容总结 |
|---|---|
| 资源效率显著提升 | 消除了 ODS 重放的冗余计算。修复任务耗时从几十分钟缩短到几分钟，资源利用率提升 80%。 |
| 开发维护更高效 | 修复逻辑直接作用于 Paimon 表，无需重复开发 ODS 重放任务。 |
| 数据一致性更强 | Paimon 主键表机制确保修复后的数据原子性更新。Exactly-Once 语义避免因任务中断导致的数据不一致。 |
| 支持更多业务场景 | 为构建统一的数据修复中心提供了基础能力支撑。 |

## 3 总结

本次基于 Paimon 的实时数仓重构项目，产出结果已提供给下游业务方使用，下游可根据需要流式消费或批量查询，整体项目不仅解决了原有架构中存在的痛点问题，还实现了数据链路的简化和资源成本的大幅优化，也为未来构建高性能、易维护、可扩展的一体化湖仓架构奠定了坚实基础。展望未来，将继续深耕湖仓一体方向，不断拓展 Paimon 在各类业务场景中的应用边界，打造更加智能、高效、稳定的数据服务。

---

**作者简介**
- 张云浩，58同城-TEG大数据部-高级数据开发工程师
- 高剂斌，58同城-TEG大数据部-资深数据开发工程师
