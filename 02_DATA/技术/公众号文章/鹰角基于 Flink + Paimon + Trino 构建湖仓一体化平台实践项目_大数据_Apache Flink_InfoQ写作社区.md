---
title: "鹰角基于 Flink + Paimon + Trino 构建湖仓一体化平台实践项目_大数据_Apache Flink_InfoQ写作社区"
source: "https://xie.infoq.cn/article/910e4f48e0559b2fc5373d487"
author:
published:
created: 2026-04-23
description: "摘要：本文整理自鹰角大数据开发工程师，Apache Hudi Contributor 朱正军老师在 Flink Forward Asia 2024 生产实践（二）专场中的分享。主要分为以下四个部分：一"
tags:
  - "clippings"
---
![鹰角基于 Flink + Paimon + Trino 构建湖仓一体化平台实践项目](https://static001.geekbang.org/infoq/87/87ba7e886802049ea2f251ab4cb1a841.png)

> 摘要：本文整理自鹰角大数据开发工程师，Apache Hudi Contributor 朱正军老师在 Flink Forward Asia 2024 生产实践（二）专场中的分享。主要分为以下四个部分：
> 
> 一、鹰角数据平台架构
> 
> 二、数据湖选型
> 
> 三、湖仓一体建设
> 
> 四、未来展望

## 一、鹰角数据平台架构

首先给大家介绍一下鹰角目前的数据平台架构。在介绍之前，关于鹰角我先给大家做简单的介绍。

### 1.1 关于鹰角

![](https://static001.geekbang.org/infoq/b6/b6af3c9d5711207cbf4cafd381ec2714.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

鹰角网络，也称为 HYPERGRYPH，成立于 2017 年，位于上海。公司的游戏产品包括《明日方舟》、《泡姆泡姆》、《来自星辰》、《终末地》以及森空岛社区。鹰角网络的数据需求呈现持续增长的趋势，目前主要依托阿里云构建数据平台。

### 1.2 鹰角数据平台架构

![](https://static001.geekbang.org/infoq/71/71f3ba7120e363d4b5e68726750b038a.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

鹰角的数据平台架构主要分为四层，分别是主要用 OSS 、OSS-HDFS 以及 Kafka 作为存储层，剩余分别是引擎层，工具层以及应用层。今天重点是介绍基于 Trino 构建的查询引擎 ，以及工具层 Ranger 构建的权限体系，自助查询工具基于 HUE 来作为用户入口，以及用 Paimon 作为的湖仓一体的存储 Format。

## 二、数据湖选型

接下来介绍的是数据湖选型。

### 2.1 基于 Hudi 入湖痛点分析

![](https://static001.geekbang.org/infoq/03/03515a8d99147da99c0eeb1c0b49821b.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

在采用 Paimon 之前，鹰角网络曾基于 Hudi 构建数据湖以进行数据入湖分析。在《明日方舟》的游戏存档业务中，需要进行整点历史变化分析，例如反作弊的排查审核和财务审计相关的业务需求。在这个存档业务场景中，日增量数据大约达到 TB 级别，需要进行 Upsert 操作以将数据入湖。由于数据量巨大，整点快照的存储成本在 Hudi 场景下可能呈现翻倍增长。

在实施过程中，快照查询的延迟面临以下三个主要问题：

1. 实时入湖：Hudi 实时入湖的用户门槛较高，使用复杂度较大。
2. 历史快照存储成本：相对较高，导致成本增加。
3. MOR 表查询时延：当使用 MOR（Merge On Read）表时，查询延迟较高，影响数据的实时性和可用性。

（一）实时入湖用户接入难度对比

![](https://static001.geekbang.org/infoq/26/26ba9a5fe05b070f54fc94b4487dfae3.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

首先介绍实时数据入湖与用户接入难度的对比。从左侧的这两个示例中，可以看到在相同存档场景下， Hudi 入湖表服务的配置参数。在配置过程中， Hudi 需要进行多项设置，例如 Write 相关算子的并发度设置、索引压缩以及表服务参数配置，如 Clean 相关的表服务设置等。相比之下，在 Paimon 入湖传递中， Write 算子相关的设置可能主要集中在并发度上。至于 Compaction 的参数配置，可能仅需设置 Full-compaction 拍摄的 Delta-commits 数量，而其余部分则多与业务相关。例如，需要保留多久的 Tag，以及 Snapshot 的保留周期有多长等。对于初级数据开发人员来说，他们实际上可以轻松地完成这些简单且高效的入湖参数配置。

（二）历史快照存储成本对比

![](https://static001.geekbang.org/infoq/3e/3e97e6c68fc5ff4f8db9c770b68214b0.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

第 2 点是关于历史快照存储成本的对比。假设每天需要在零点整点时刻存储快照，在 Hudi 的场景中，它更倾向于处理增量数据的场景。如果保留整点快照，将会有大量的 Log Files 存储在 OSS 中。如果仅需要保留整点附近的 Log Files，则需要对 Hudi 进行二次开发。首先，要调整其 Delta Commit 和 Clean 策略；其次，要对整个 Timeline 体系进行额外处理。这种做法实际上开发以及运维成本会比较高。

而在 Paimon 上，它在 Snapshot 以及文件管理方面进行了简化处理。只需对 Snapshot 进行标记，例如使用 Tag 标签来标识需要保留的 Snapshot。同时，只保留该 Snapshot 中相关的 Data Files，而整点以外的数据则会被整合到 DataFiles 的结构中。因此，在整点快照存储上， Paimon 能够表现出更低的存储成本。这样在满足实时快照需求的前提下，也能有效减少 OSS 的存储成本。

（三）Trino 引擎下 Hudi vs Paimon

![](https://static001.geekbang.org/infoq/1f/1f64c8909948d1b12d9d355cb2401200.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

第 3 点是基于 Trino 引擎对 Hudi 和 Paimon 的入湖与读取性能进行对比。以明日方舟存档场景为例，该场景的测试数据量约为 600 万条。在数据消积时间上，可能需要大约 100 分钟。然而，在文件数量方面， Paimon 大约有 31 个数据文件，而 Hudi 则有 48 个，但 Hudi 在文件组织上仍然保留了 500 多个 Log Files。尽管在写入性能上，两者差距不大，但在读取性能，特别是主键点查方面，差异显著。

这是因为存档场景具有一个特殊情况，即存档的单条数据会非常大，这在一定程度上加剧了 Hudi 的 Log File 文件组织缺陷。当使用 Trino 进行读取时， Hudi 需要花费大量时间在 Log File 的合并上。而在主键点查方面， Trino 在 Paimon 上可能仅需 0.365 秒即可返回数据，但在 Hudi 上，由于 Log Files 合并耗时较长，查询时间达到了 22 秒。此外，随机查询、范围查询以及 TopN 查询在 Hudi 上都存在不同程度的额外处理时间。

### 2.2 Hudi vs Paimon 总结

![](https://static001.geekbang.org/infoq/3b/3b1be4f281d50b06a9639992154c69fa.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

### 2.3 VVP Flink + Paimon 实时入湖

![](https://static001.geekbang.org/infoq/7f/7fd482392ad2fd5ed3ea67a94fb6aee5.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

那么最终选择以 Paimon Flink 作为数据湖的入湖存储引擎，是基于 VVP Flink + Paimon 实时入湖的整体链路，这也是一个经典的架构。其流程是通过 MySQL 和 Flink CDC 写入 EMR Kafka，再通过 Flink 多源分发到 Paimon 以及 Connector。这一架构具有多个优势，尤其是在云端功能的增强方面，例如元数据管理、 Flink 引擎能力的迭代以及 Paimon 的功能迭代。

全面 SQL 化入湖是该架构的另一大优势。此前， Hudi 入湖常通过架包的方式进行写入，这增加了运维成本和数据开发的接入成本。而在 VVP Flink 版本中，这些问题得到了良好解决。另外我们扩展了 HG-Paimon Connector，并支持 Online Schema Evolution，即在动态 Schema 变动时可以联动内部的数据平台，降低人工运维成本。

由于 VVP Flink 是以闭包形式提供的，因此对其底层代码的掌握可能不够深入。为了快速进行故障排查，可以依赖鹰角内部的 Paimon Connector 来实现监控指标的添加和自定义的 Schema Evolution。这不仅提升了运维效率，另外还实现了数据湖全链路的监控，从而完善了整个数据湖运维流程。

## 三、湖仓一体建设

将数据写入 Paimon 后，其实还未完成全部工作。因为用户需要通过特定的用户入口来访问和使用 Paimon 表，并了解 Paimon 表对其数据业务具体场景的支持情况。为了实现这一目标，需要进行湖仓一体化建设。这包括整合像 HUE、Ranger 以及 Trino 这样的组件，以便用户能够顺利接入。

### 3.1 湖仓平台架构

![](https://static001.geekbang.org/infoq/c8/c8a91aa05c4e846f87261077f3d3334f.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

在湖仓平台架构的入湖实施中，选择了 Flink 作为实时传输引擎，通过 CDC（Change Data Capture）技术将数据写入 Paimon 表中。在分布式存储方面，平台采用了 OSS-HDFS。云上离线传输时使用 Spark 作为引擎。对于全量数据入湖的支持，平台可能会采用离线的 Spark 方式进行处理。

而 Ranger 则是湖仓权限管理平台基础组建。由于 Paimon 以数据资产的形式提供给各个部门，因此每个 BU 的权限管理都依赖于 Ranger 作为底层引擎。

在选择湖仓分布式计算引擎时，我们在 2023 年底做出了决定，选择了 Trino。这一选择是基于当时 StarRocks 在某些方面仍存在不足，如 Ranger API 的兼容性和对复杂类型的支持尚不完善。因此， Trino 被选为湖仓查询分析的引擎。

在湖仓交互平台上，平台选择了 HUE 作为 Web SQL IDE 的用户对接工具。这样，用户就可以通过 HUE 来查询 Paimon 表以及其他相关表。

### 3.2 湖仓交互平台用户入口演示

![](https://static001.geekbang.org/infoq/1c/1c99731bbeb056895093cfd3b56e47c3.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

这就是湖仓交互平台的用户入口演示。左边部分相当于为用户提供了个性化的界面，即根据用户的权限来展示相应的 Catalog。中间部分是 Notebook，用户可以在这里编写 SQL，平台支持多引擎。右边部分则是用户 SQL 的自动补全功能，这意味着用户可以看到他们具有访问权限的表及其 Schema。

当用户使用湖仓管理平台时，这个用户入口交互平台主要有以下几个应用场景：首先是 Adhoc 查询，以及平台内部大数据的数据开发测试。此外，对于 Paimon 表，还包括数据修正的流程，因此需要对 Paimon 的 Procedure 提供支持。另外还提供轻量级的数据文件导出功能。

### 3.3 湖仓平台

#### （1）平台交互优化

![](https://static001.geekbang.org/infoq/54/54152af26b9dd88a48ac2d21958660bf.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

将交互平台提供给用户后，我们面临了以下几个问题：第一，云产品查询引擎的定制化程度相对较低；第二，如何有效进行用户权限管控；第三，开源的 Web SQL IDE 功能存在局限性。接下来，将围绕这三个问题进行简要介绍。

在平台交互方面，即之前提到的 Web SQL IDE，确实存在一些缺陷。尽管 HUE 原生支持了一些核心能力，如 Catalog View，Sql Editor 以及 explain 等核心功能，但在实际使用过程中，发现 HUE 原生的 Trino Connector 功能是通过 Python SqlAlchemy 协议实现的。这种方式导致所有用户都通过 "HUE" 相同用户的方式接入，无法很好地实现分用户 Session 的权限管理。

为了解决这个问题，新增了 HUE Trino Python Connector。

在选择 Python Connector 的过程中，也遇到了一些挑战。最初，尝试使用 Trino Java Connector，但发现 HUE 底层是通过 Python 代码构建的，而 Trino Java Connector 在使用时存在一些问题，特别是在内存管理方面,有时难以对 Java Gateway 实现内存的有效回收，这可能导致线上内存泄露。在班加罗尔的亚马逊团队也遇到同样的问题，在与他们讨论后，最终选择使用特定的 Python Connector 来实现用户分 Session 的权限管控，并贡献 Cloudera 社区。

此外，还优化了一些用户常用的功能。例如，支持用户按照分号批量执行 SQL 语句。有些用户需要创建脚本、建表、修改分区等，这些操作可能涉及批量执行 SQL 语句，而在原生基础上并不支持这一功能。另外简化了下载功能，集成了 Notebooks，并修复了原生开源的一些问题。通过这些新的 Feature，完成了平台交互的优化。

#### （2） Ranger 集成

![](https://static001.geekbang.org/infoq/70/702a8f7278dc0fa61154b1786f616e9f.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

接下来，将介绍湖仓平台中的 Ranger 集成部分。当获取到用户的 Session 信息后，例如获取用户的邮箱等作为区分不同用户的数据资产。那么，面对如十万张表这样的庞大用户资产，如何高效地存储这些策略（Policy）呢？

实际上，通过底层自建的 Ranger 集成来实现这一目标。这个集成主要涉及到 Ranger 的容器化改造，包括镜像的 CI/CD 流程、审计日志落地到 Elasticsearch（ES），以及对 API 的改造，以适配 Trino 4xx 版本。需要特别注意的是， Ranger 对于 Trino 400 以上的新版本支持并不完善。因此，还需要对 API 以及 Trino Coordinator 与 Ranger Agent 的兼容性进行适配。

通过这一系列的改造和兼容工作，可以基于 Ranger 和 Trino 构建权限管理系统，并存储相关的策略（Policy）。这就是湖仓平台中 Ranger 集成的核心内容。

#### （3）湖仓权限管理体系实施

![](https://static001.geekbang.org/infoq/2d/2d879cdc89fbfc4f8b42fe533263911d.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

在实施权限管理的过程中，确实面临了一些挑战，特别是在处理数以万计的表时。以往，这些表的权限管控可能都是在云上完成的，但现在需要在 Ranger 的基础上，快速构建整个权限体系。

为了应对这一挑战，基于 Trino 的三层鉴权体系，构建了角色权限管理机制。具体来说，将角色与 Catalogs、 Databases 以及 Tables-Columns 进行关联，通过分角色的方式来规范所有用户的行为。用户只需与角色绑定， Policy 的数量就相对可控，这样实施起来更加高效。

这种方法的优缺点相当明显。首先，它的落地速度非常快，用户可以迅速从云上迁移到自建的 Ranger 和 Trino 体系中。此外， Policy 的数量相对较少，这减轻了 Trino 在拉取 Policy 时的压力。如果 Policy 的数量与用户数据相乘，那么其数量将会急剧增长，这可能会导致查询和权限校验的时间变长。

然而，这种方法也存在一个显著的缺点，那就是无法实现用户级别的精细化管理表权限。这个问题在未来的 Ranger 体系建设中可能会更加突出。因此，将更多地关注 Ranger 底层的优化，以期在这一方面取得更好的成果。

#### （4） 湖仓一体平台落地效果

![](https://static001.geekbang.org/infoq/ea/ea77209f23faf2759efa568d2c79fe00.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

湖仓一体平台落地后取得了显著的效果。首先，在查询加速方面，相较于之前的云上湖仓查询，90% 的查询都能在 10 秒内完成。这主要得益于平台的优化，尽管有时由于用户会跑轻量离线 ETL 等影响，部分查询可能会超过 10 秒，但这仍在可接受范围内。

其次，大查询的提速效果更为显著，部分查询的提速甚至超过了两倍。

第三，离线存档快照的时效也得到了大幅提升。从之前的凌晨 4 点才能完成整点快照同步，到现在在 Paimon 基础上凌晨 1 点即可实现 0 点精确切分，这一改进得到了用户的广泛认可。

目前，湖仓一体平台已在运营、用研、算法等多个业务部门落地应用，仅国服工作日平均日查询总量已超过 1 万。虽然这一量级在互联网公司中可能并不算大，但考虑到在过去一年内平台完成了从 0 到 1 的建设，这已是一个相当不错的成绩。此外，随着海外服查询量的日益增长，平台的查询总量也在持续增加。

在落地场景方面，平台主要服务于内部的 HG-BI 系统，包括游戏报表、观点报表等。同时，也支持了明日方舟存档快照、用户 Adhoc 查询、轻量级 ETL 以及跨源 DQC 等场景，这些都在湖仓一体管理平台中得到了很好的实现。

取得这些成绩的基础是平台自建的 Trino 引擎，通过定制化开发，实现 SQL 整体性能提升。

#### （5）定制化 Trino 基建

![](https://static001.geekbang.org/infoq/b3/b334d33ca7d8cce9a8ae9bf0ed03cd13.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

在定制化 Trino 基础设施的初期阶段，面临的是从 0 到 1 的建设挑战，这涵盖了容器化改造、 CI/CD 流程以及云上部署等多个方面。基于阿里云 Severless k8s 集群进行部署 Trino 自定义镜像。通过 AK、SK（访问密钥）链接 OSS 的方式，即 OSS Client，实现了与云上 OSS 存储的对接。此外，还增强了 Ranger Agent 的权限管控能力。第四点，我们接入内部 HMS（Hive Metastore），完善了整体 Catalog 的建设。

在将云上环境迁移到自建 Trino 平台的过程中，遇到了一些挑战。用户希望新的 Trino 平台能够兼容云上的部分功能。例如，他们希望 Trino-Hive 能够兼容 SLS Native Snappy 日志投递功能。然而，由于 Trino 社区版可能只支持特定的 Airlift Snappy 格式类型匹配，导致某些表无法被读取，因此需要进行额外的兼容性工作。另外类似整数相除返回 Double 类型的处理、 dt 分区字段的隐式转换、关闭 Dynamic Filters 等参数优化。这些优化措施旨在减少用户的接入成本，特别是在处理时间分区过滤时，通过添加 UDF（用户定义函数）和 dt 字段隐式转换，可以显著提升在 Trino 上的开发效率。

综上所述，为了满足用户的高要求，在定制化 Trino 平台的建设过程中，不仅进行了基础架构的搭建，还针对用户的具体需求进行了深入的优化和兼容性工作。

#### （6）Trino 联邦查询

![](https://static001.geekbang.org/infoq/11/1138804b043b7303b9977f4a498ffb7e.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

Trino 的联邦查询功能在接入 Paimon 后，仍需支持众多历史表类型，包括 Hive 表、 Hudi 表以及用户可能仍在使用的 Clickhouse 表。为了满足这些需求，需要提供对 Clickhouse Catalog、 Paimon Catalog 以及 Hive Catalog 的联邦查询支持。

在 Hive Catalog 方面，进行了额外的改造。社区版通常通过是否指定了 External Location 来区分是否为外表，但这种区分方式并不严谨。此外，用户需要了解 OSS 的具体路径，这对数据开发人员来说增加了解释成本。因此，实现了默认建外表的操作，允许在 Databases 默认目录下构建表，并直接生成 OSS 目录，从而降低了建表时的用户接入门槛。

在支持 Hudi Catalog 上增加了 Hudi MOR 表的查询。由于历史原因，部分 Hudi 表尚未迁移到 Paimon 上，但在实时场景下，这些表仍需被读取以处理日志文件。因此，支持了对 Hudi MOR 表的近实时查询，并修复了相关问题。例如，在 Hudi 的某些场景中，可能会出现大小为 0 的 Marker File，这可能导致 Trino 在扫描时将这些无效文件纳入查询范围，从而造成查询卡顿，在内部镜像中对类似的问题进行了修复。

综上所述，联邦查询功能不仅支持了多个历史的 Connector，还新增了对 Paimon Connector 的支持，以满足用户在不同场景下的查询需求。

#### （7）Trino-Paimon Enhance

![](https://static001.geekbang.org/infoq/d3/d3c0f69c2ff2b11348de90d9d69ebe06.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

在支持 Paimon Connector 之后，确实遇到了一些挑战，特别是在 Trino 与 Paimon 的集成增强方面。例如，在尝试通过 Prepare Statement 实现每天整点的快照调度时，发现 Trino 实际上并不支持用户通过预设参数的方式来指定 Paimon 的快照，即不支持使用 QueryPeriod 语法中的问号（QUESTION\_MARK）作为参数占位符进行提前注入。

为了应对这一场景，对 Trino 的语法进行了扩展。在 Snapshot Rollback 和 Sequence Field 上增加了新的语法，如 FOR TIMESTAMP AS OF，允许通过 TimestampValue 设置问号（QUESTION\_MARK）或字符串（STRING）来实现 Paimon 快照 QueryPeriod 的预设功能。这样一来，用户就能够实现每天凌晨的 Paimon 快照调度。

此外，考虑到 Trino 在 Catalog 方面主要支持的是 Flink 和 Spark Catalog，而对于 Paimon 表的操作可能涉及到一些特定的参数设置，这在 Trino 上可能并不直接支持。因此，进行了二次开发，并扩展部分 Procedure 来弥补这一不足。

对于用户而言，他们可能更倾向于通过湖仓一体的入口（如 HUE）来操作 Paimon 表。然而，在某些情况下，他们可能只能通过查询引擎来对 Paimon 表进行修复。因此，在 Trino 上实现了对 Paimon Procedure 的支持，如 Snapshot Rollback 和 Orphan Files Delete 等，这些都是在 Trino 基础上进行的功能扩展。

此外，还提出了 External Compaction 的方法，并希望在 Compaction 时能够剥离实时写入任务，转而通过 Trino + DolphinScheduler 进行异步调度。这样做可以减轻实时任务写入的压力，提高系统的整体性能。

综上所述，通过扩展 Trino 语法、进行二次开发以及引入 Procedure 等方式，增强了 Trino 与 Paimon 的集成能力，并为用户提供了更加灵活和高效的操作方式。

#### （8）监控大盘 + HPA

![](https://static001.geekbang.org/infoq/0f/0f37cdf710c5ed8f7f9835a6b5ead7c2.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

监控大盘的左侧展示了基于审计日志的湖仓查询概览。从这个概览中，可以清晰地看到查询耗时的分布情况：大部分查询耗时在 1 秒以内，超过 90% 的查询耗时在 10 秒以内，其中 10 秒以内的查询占据了相当大的比例。

另外通过使用潮汐策略下的 HPA（Horizontal Pod Autoscaler，水平 Pod 自动伸缩器）对集群资源进行有效控制。由于用户群体有着明显的使用场景规律，如早上 10 点和下午是用户高峰期，而晚上则资源相对空置。因此，采用了潮汐策略下的 HPA 来优化 Trino 集群的资源利用。这样做的主要目的是在节省 Pod 占用的计算存储成本的同时，确保集群在高峰期能够满足用户需求。

此外，监控大盘可以实时查看 Trino 集群的 CPU 和内存使用情况，提供了全面的集群运行状况概览。

#### （9）审计日志透出

![](https://static001.geekbang.org/infoq/95/95953261740405fe0e72a07e49a590bb.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

对于审计日志的原生不支持问题，进行了相应的扩展，即在 Trino 的 QueryManagerConfig 中新增了配置选项，包括 Kafka 的配置以及是否开启审计日志透出的管理。在 Coordinator 中，能够获取用户的 Session 信息和 QueryInfo（即 SQL 语句）。随后，在 Flink 中，将这些审计日志发送到 EMR Kafka 中，并进一步通过 Flink 写入到 Hive 表中。这样，实现了审计功能的支持，包括 SQL 回溯、问题定位以及性能诊断等相关功能。此外，还可以进行 Adhoc 查询的 RT 分位线统计。

第三点，通过审计日志，可以实现分部门计算成本。具体来说，可以根据审计日志查看每个用户的 CPU 使用量，并据此计算每个部门在 Trino 上的使用占比。

第四点，关于业务热点追踪，以往的经验通常依赖于 OSS 的读取和写入来识别热点。然而，这种方法无法反查到具体是哪些用户访问了哪些表。而通过审计日志，可以进行倒查，明确业务热点的具体复刻是在哪些数据库以及哪些表中。这样，就能够完成业务热点追踪，进一步支持整个湖仓一体的建设，包括在数据湖入湖（如 Paimon）上的应用。

通过这些扩展和优化，增强了 Trino 的审计日志功能，使得可以更全面地监控和管理查询行为，提升了系统的可观察性和运维效率。

## 四、未来展望

### 4.1 Trino - paimon Enhance

![](https://static001.geekbang.org/infoq/57/573395b7949ab1b998607bf1f0afb849.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

第一点，对 Trino 与 Paimon 的集成进行了加强，这主要面向当前体系中的用户。用户可以通过 HG-BI 或 OSS 看板功能来访问数据。对于 Hive 的存量数据，数据开发人员通常通过 HUE 的方式接入，而观远报表则通过报表查询的方式来访问 Paimon 或 Hive 数据。此外， HG-BI 可能还单独搭建了一套与自身相关的 Trino 集群，用于读取历史 Hive 数据。

在增量的 Paimon 场景中，通过内部 Trino Adhoc 查询和 Ranger 的权限管控来提升性能。考虑到在 23 年底时，使用的是 Trino 434 Snapshot 版本，选择以 433 模式为主版本。未来考虑迭代至 439 以上版本，因为这些版本支持 Alluxio Cache 的能力。利用 Alluxio Cache，可以对查询进行预热，从而降低查询时的带宽压力，减少 Scan 查询的时延。这样，用户的查询效率将得到显著提升。

然而，在读取 Paimon 表的快照时，仍然面临一些问题。由于社区在 Snapshot 上的支持较多，而在 Trino 上的支持相对较少，这导致了在读取 Snapshot 时存在性能压力。为了解决这个问题，采用了以空间换时间的方式，将 Snapshot 存储在 Hive 表中，并每天生成增量的快照。对于时延要求比较高的用户，根据需求生成天或小时级别快照。这样，就可以通过 Trino 加 Hive 的方式来读取这些增量快照，满足用户的数据访问需求。

### 4.2 StarRocks + Paimon

![](https://static001.geekbang.org/infoq/00/003360d8baafa395f449d766f79423ea.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

第二点，关于 StarRocks 与 Paimon 的结合，过去一年中，见证了 StarRocks 社区的迅猛发展。在面对性能要求较高的场景，如实时归因分析时，用户更倾向于在 StarRocks 上获得支持。因此，尝试通过构建 StarRocks 内表与 Paimon 相结合的方式，来实现查询加速。目前，已在内部测试了 EMR StarRocks 在 HUE 上的支持，这意味着用户可以通过 HUE 界面访问 EMR StarRocks，从而进行实时场景的数据开发与测试。

此外，虽然湖仓交互平台已经支持 StarRocks 查询，并且内部已经实现了打通，但在实时场景中，用户可能仍然更倾向于通过云上的 HMS 方式获取服务。因此，计划在未来在 HUE 上增加更多对 StarRocks 的支持，以满足用户的需求。

### 4.3 Paimon 全面替换 Hive

![](https://static001.geekbang.org/infoq/10/10f1cb4fd41d30c6f5f6311cf02bfcbf.webp?x-oss-process=image%2Fresize%2Cp_80%2Fformat%2Cpng)

最后一点是关于 Paimon 全面替换 Hive 的议题，这确实是一个相对激进的做法。从 Trino 社区负责人的观点来看，他们更倾向于采用新的数据湖 format (Iceberg)来替代传统的 Hive 引擎。而在国内生态中， Paimon 也在进一步发展，得益于 Paimon 在解决 Upsert 入湖问题以及支持主键表和 Append 表场景方面的能力，特别是其聚焦于物化查询的能力，能够显著提升查询效率。

在 Upsert 入湖后，可以在湖表的基础上构建物化表。当用户进行查询时，直接查询物化表将带来更高的效率。此外，还关注到了 HMS（Hive Metastore）的单点问题。在过去的一年里，遇到了一些生产上的问题，例如用 在添加大量历史分区时导致 HMS 集群过载，进而影响所有用户的元数据查询。这是一个严重的风险点，因此，后续计划通过使用 OSS Catalog 以及像 Gravitino 等开源解决方案来增强元数据管理，降低 HMS 单点问题的风险。

第三点是关于 Data Skip 优化的讨论。之前与 Paimon 社区的成员交流过，了解到在 Trino 上可以进一步扩展 Data Skip 相关的元数据组织，以提高文件扫描的效率。通过减少需要扫描的数据量，加快数据查询速度，同时进一步提升 Trino 体系整体查询性能。

本次分享到此结束，感谢大家的阅读。

**更多内容**

![](https://static001.geekbang.org/infoq/bf/bf1502e261fe2e09e3d6a9ab080c2893.jpeg?x-oss-process=image%2Fresize%2Cp_80%2Fauto-orient%2C1)

---

**活动推荐**

阿里云基于 Apache Flink 构建的企业级产品-实时计算 Flink 版现开启活动：新用户复制点击下方链接或者扫描二维码即可 0 元免费试用 Flink + Paimon [实时计算 Flink 版](https://xie.infoq.cn/link?target=https%3A%2F%2Fweibo.cn%2Fsinaurl%3Fu%3Dhttps%253A%252F%252Ffree.aliyun.com%252F%253Futm_content%253Dg_1000395379%2526productCode%253Dsc) （3000CU\*小时，3 个月内）了解活动详情： [https://free.aliyun.com/?utm\_content=g\_1000395379&productCode=sc](https://xie.infoq.cn/link?target=https%3A%2F%2Fweibo.cn%2Fsinaurl%3Fu%3Dhttps%253A%252F%252Ffree.aliyun.com%252F%253Futm_content%253Dg_1000395379%2526productCode%253Dsc)

![](https://static001.geekbang.org/infoq/e7/e7b451818a391a7a936e4c5cba1c77c8.jpeg?x-oss-process=image%2Fresize%2Cp_80%2Fauto-orient%2C1)

**

**

**

**

**

查看更多 InfoQ 精选内容 >