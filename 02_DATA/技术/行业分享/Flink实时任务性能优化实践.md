---
title: Flink实时任务性能优化实践
tags:
  - Flink
  - 性能优化
  - 数据倾斜
  - 实时数仓
created: 2026-03-08
image_status: 图片丢失待补
---

> [!warning] 配图缺失
> 本文 43 张配图在从旧库导入时丢失（原路径 `90_管理/附件/`），正文完整可读，文中“见下图”等位置图片暂缺。如需补图请参考原文。

# **一、背景**

即时配送平台作为万物到家的基础，拥有海量的数据和丰富的实时业务场景，致力于应用业界先进的数据计算技术架构，保障业务数据的时效性、一致性、准确性、完整性，为业务的运营管理、策略决策和算法策略提供完善的数据体系和基于数据科学的决策能力。数据团队的团队定位是即时配送业务数据体系和数据产品的建设者，通过技术应用和创新助力业务打造数字化与智能化的即时配送平台。在即时配送业务规模不断扩大的同时数据链路复杂度、任务数量也在增加，对实时任务的性能要求也越来越高；现阶段实时任务存在以下两个问题：

  * 流量激增时任务性能不足，稳定性差：由木桶效应可知数据链路中性能差的节点决定了整个数据链路性能的上限，除此之外还会影响数据链路的稳定性和时效性；实时任务会依赖各种组件（例如MQ、Redis、Yarn等）这些组件出现抖动或者异常时都有可能引起实时任务重启，如果异常发生在午晚高峰期间，此时数据流量较大，存在性能瓶颈的实时任务需要花费大量时间来消费积压数据，这不仅使得数据服务的稳定性和时效性无法得到保障，严重情况下会导致整个数据链路服务不可用，对于依赖数据进行实时运营的业务方而言这是不能接受的。

  * 实现方式效率低、配置不合理、资源浪费严重：实时任务中的一些不合理实现方式或者是不合规的参数设置导致任务虽然分配了很多的资源但是性能依旧很低下，不仅存在严重的资源浪费问题，而且实时任务稳定性很差。

基于以上存在的问题无论是从提升数据服务质量出发还是以提高资源利用率作为目的，对Flink实时任务的性能优化工作都已经势在必行。

# 二、现状&目标

### 2.1 现状&问题

Flink作为新一代的流式计算引擎，凭借其高吞吐、低延迟、支持State等特性已经被广泛的被应用到各个行业。实时数据团队从2020年正式在生产环境使用Flink引擎，现阶段Flink实时任务数量已有1200+，实时数据在算法策略、实时大盘、监控管理、骑手履约、异动预警等场景下发挥了重要的数据支撑作用；这些场景对数据服务的性能要求都很高，这也敦促着我们不断去学习，去解决问题；在开发运维或者优化过程中不可避免会遇到各种问题，现将问题整理如下：

  * #### **[[数据倾斜实践|数据倾斜]]：**

数据分布不均衡是产生数据倾斜的根因，数据倾斜导致任务性能下降，出现消息积压，影响数据服务时效性和稳定性。

  * #### **维表Join性能低下：**

流量高峰期间任务访问维表存储引擎频次增加，任务吞吐量下降，造成数据延迟，影响业务运营。

  * #### **Regular Join使用不当：**

Regular Join使用不当导致任务state膨胀，输出数据膨胀，影响任务稳定性，同时还会造成任务资源浪费。

  * #### **任务参数、资源配置不合理：**

任务并行度设置不合理，有可能会导致数据倾斜，任务资源超配存在一定资源浪费，内存参数，RocksDB参数设置不合理影响任务性能的同时任务稳定性也无法保障。

### 2.2 目标

  * **降本增效，提高任务吞吐量和资源利用率**

  * **提高任务的稳定性和数据服务质量**

# 三、优化思路

在实际生产中影响任务性能的因素有很多，但是不可能对影响性能的所有因素都进行优化，我们要考虑性能优化的投入产出比，在性能优化过程中遵循六大原则：

  * **三个“要”原则** ：要优先查最大的性能瓶颈，性能分析要确诊性能问题的根因，性能优化要考虑各种的情况。

  * **三个“不要”的原则** ：不要做过度的、反常态的优化，不要过早做不成熟的优化，不要做表面的肤浅优化。

对于性能优化而言，无论是哪种性能问题都必须要找到导致任务达到性能瓶颈的根因，只有找到根因才能对症下药彻底解决问题，举个例子：实时任务出现反压，执行cp过程中在某一个subtask耗时比较久通过对所在TM上的线程dump日志分析发现是某些线程消耗了大量的CPU导致任务卡死，这种情况下任务性能瓶颈就是CPU，接下来我们需要定位导致CPU出现性能瓶颈的根因是什么然后才能制定适宜的方案来解决问题；对于性能优化我们首先要考虑性能提升的幅度，其次我们要考虑投入产出比，此外还要考虑这种性能优化方案在各种场景下是否都是最优解，比如我们在优化维表join的任务过程中我们引入了state这就增加了任务复杂度以及资源成本，但是任务的性能却有显著的提升，不会出现午晚高峰消息积压的情况了，那这种情况下我们就需要进行权衡利弊进行取舍，去选择合适的解决方案。综合分析上述存在的性能问题，参考业界性能优化相关的处理思路，我们按照问题类型逐一介绍优化思路：

  * #### **数据倾斜：**

遇到数据倾斜问题，我们首先要能够从存在数据倾斜算子上获取一些有用信息，分析这些信息判断是那种类型的数据倾斜分别去定位该类型数据倾斜的根因，然后制定对应的优化方案，按照方案进行优化；具体优化流程如下图所示：

![[90_管理/附件/flink_opt_fig_1.png]]


流程图中将数据倾斜的场景归纳为三类：

    * 数据倾斜算子不涉及分组操作：这种场景下表示数据倾斜算子发生在分组操作（keyby/group by、partition by等）之前或者是该任务中没有分组操作，产生数据倾斜的原因是算子并行度设置不合理，对应解决方案是合理调整算子并行度。

    * 不存在热点Key但分组操作之后算子出现数据倾斜：这种场景的数据倾斜大多数是由于KeyGroup分布不均衡导致数据的数据倾斜，将分组之后算子的并行度设置为2的N次幂，同时添加"--max_parallelism" 参数设置合理的KeyGroup个数或者是直接添加"--max_parallelism"并设置合理的参数值 这两种方法均可解决或者缓解数据倾斜问题。

    * 存在热点Key导致分组操作之后算子出现数据倾斜：此类问题一般通过开启Local-Global Aggregation两阶段聚合来解决，或者使用Split Distinct Aggregation SQL层基于两层次聚合都可以解决，再者对热点key经过加盐，去盐两次聚合来解决。

  * #### **维表Join性能低下：**

维表Join任务中每来一条数据都需要对维表数据进行一次关联查询，维表数据通常存储在外部组件中（Redis,HBase,KV缓存等），午晚高峰期间流量较大频繁访问维表会导致外部存储组件负载压力比较大会出现连接超时，线程阻塞，维表数据返回过慢等问题，基于维表join中出现的问题，所以我们的优化思路应该是通过降低维表关联查询次数，减少线程阻塞来解决维表Join性能低下的问题为此我们想到了以下几个优化方向：

    * (https://nightlies.apache.org/flink/flink-docs-release-1.12/dev/stream/operators/asyncio.html)：默认情况下维表Join是以同步方式访问维表的，每一次查询请求需要等待结果响应之后才能进行下一次请求，期间浪费了的大量时间在等待结果上，异步IO的方式可以并发地处理多个请求和接收多个结果，等待的时间可以被其他多个请求均摊，大幅度提高流处理的吞吐量。

    * 缓存维表数据：将维表数据缓存到本地内存中，查询维表时直接走内存不需要与外部缓存进行交互，这种方式同样可以大幅提升维表join的性能，但是要综合考虑一下缓存维表数据的策略。

    * 攒批关联：攒批关联的思路类似于Mini-Batch，根据时间或者是数据量对数据进行攒批然后批量去关联维表，可以减少RPC调用次数，同样可以提高任务吞吐量。

    * 维表Join前将实时流按照Join Key进行Hash分组：对实时流进行hash分组可以缩小单个container上处理Key的数量，提高缓存命中率，减少访问外部存储频次。

  * #### **Regular Join使用不当：**

    * 多表（2个以上）Join时表关联顺序选择错误：现阶段Flink不支持多流Join，会将多流Join拆分为双流Join，当多表（2个以上）Join时，需要合理选择表Join顺序，建议先将小表关联后，再与大表进行关联，这样可以大幅降低状态大小。

    * Regular Join输出数据膨胀：Regular Join 合流，如果不使用主键去重，那么状态会很大，查询效率变低、下发数据量变多，导致合流节点本身消耗资源多，且造成下游计算资源浪费，因此需要在Join合流之前对数据进行去重减少Join数据量。

  * #### **任务参数、资源配置不合理：**

    * 并行度，KeyGroup个数设置不合理：对于有分组操作的任务，建议将分组之后的Join或者是聚合算子并行度设置为2的N次幂，并且添加max_parallelism参数避免出现数据倾斜以及扩容时无法从cp恢复的问题。

    * 资源分配不合理：通过查看任务的(http://rt.data.某互联网公司.com/grafana/d/fayM2jrWz/flink_job_metrics-public)监控合理分配任务资源，对于IO密集型任务可以尝试通过设置**yarn.containers.vcores:1参数** 降低Vcore分配个数，降低资源成本，提高CPU利用率。

    * 内存参数，RocksDB参数配置不合理：某些场景下会出现RocksDB内存超用的场景会导致任务频繁出现container 被kill的现象，通过调整RocksDB参数对任务性能和稳定性都有一定的提升。

# 四、优化实战

工欲善其事必先利其器，好的工具做起事来事半功倍，同样对于任务的性能优化而言也是如此，好的工具或者分析方法可以帮助我们快速定位到问题的根因，可以提高我们排查问题、解决问题的效率，接下来在介绍优化案例之前，结合我们团队内部的实践经验分享一下我们排查问题的流程以及方法：

  1. **分析现象，确定反压源头算子**

Flink任务出现性能问题时主要表现是cp执行较慢、cp超时失败、任务failover等；算子执行cp较慢或者是执行cp失败这些都是表象，根因是算子出现了反压，有时候执行cp异常的算子并不是导致任务性能下降的源头算子，因此我们排查问题的时候需要定位到反压的源头算子，否则有可能在错误的排查方向上浪费了很长时间而且没有任何进展；

  2. **结合指标监控，定位根因**

确定反压源头算子之后需要对反压算子的监控指标进行分析，根据反压算子是否存在cp超时或者是cp执行较慢的现象我们将此类问题分为两类：

     1. 反压算子执行cp超时或者执行cp较慢

该场景下我们可以根据执行cp过程中的各项指标进行分析，Flink
cp过程包含同步、异步两个阶段，同步阶段主要是对执行状态快照，该阶段会阻塞，异步阶段主要是将状态快照副本同步到远程存储集群上，如果cp监控指标中显示Async
Duration该指标耗时比较久那说明在异步阶段上传副本过程中过程中存在一定的问题，可以观察该算子所在tm对应的网卡流量监控，磁盘io等，此外还可以尝试调整state.backend.rocksdb.checkpoint.transfer.thread.num参数；如果任务执行cp监控中Sync
Duration、Alignment Duration、Start
Delay这三个指标耗时较久那说明任务在同步阶段耗时较久，同步阶段影响因素比较多，例如：数据倾斜、磁盘io较高导致RocksDB读写性能下降、复杂计算、RocksDB内存分配不合理等，从任务的**grafana**
监控，算子所在机器监控以及TM的jstack日志入手进行分析问题根因；

     2. 反压算子未执行cp操作

反压算子未执行cp，说明反压进行了传递导致反压算子的上游也出现了反压，此时我们的排查方向首先观察反压源头算子每个subtask接收的数据大小是否一致，是否存在数据倾斜相比于上述说的影响因素，数据倾斜问题更直观更容易被发现，如果存在数据倾斜问题首先解决数据倾斜问题，如果解决之后仍然存在性能问题，那需要对jstack日志进行分析，根据反压算子所在TM的Thread
Dump日志进行分析，可以使用Dump分析工具(https://fastthread.io/)，也可以联系平台抓取算子运行TM的CPU火焰图，根据火焰图可以分析出任务blocked信息

  3. **循序渐进，探索解决方案**

按照上述分析步骤，对可能存在的影响因素进行逐步优化，循序渐进最终找到合适的解决方案。

### 4.1 数据倾斜

数据倾斜是在实际开发中经常遇到的一个问题，数据分布不均衡是产生数据倾斜的根本原因，在优化思路小节中总结了数据倾斜的三种场景以及对应的优化思路，接下来阐述一下我们是如何解决数据倾斜问题的。

  * **数据倾斜算子不涉及分组操作：**

这种场景下产生数据倾斜的原因是算子（source，flatmap，map，filter等）并行度设置不合理；以MQ
topic为例来说明，分区数为80，当source算子并行度设置为30会发现存在的一定数据倾斜，见下图：

![[90_管理/附件/flink_opt_fig_2.png]]
图2 source并行度为30时算子存在数据倾斜

当source算子并行度设置为40或者80时数据分布比较均衡，具体信息见下图：

![[90_管理/附件/flink_opt_fig_3.png]]
![[90_管理/附件/flink_opt_fig_4.png]]
图3 source并行度为40时算子数据分布均衡 图4 source并行度为80时算子数据分布均衡

对于MQ
topic而言在topic生产端我们内部建议将topic的producer.cluster.dispatch.type（(https://km.某互联网公司.com/page/181552922)）参数值设置为同地域集群优先或者是全部集群,在此配置下MQ
topic分区数据会写入多个机房，当一个机房故障时MQ内部可自动启动熔断机制停止向故障机房写入数据，将数据写入其他正常机房，这样既可以均衡流量又可以提高topic的容灾能力；开启该参数之后topic机房信息如下图：

![[90_管理/附件/flink_opt_fig_5.png]]
图5 MQ topic 多机房信息

在topic消费端我们内部建议将消费组的partition.assign.mode（(https://km.某互联网公司.com/page/168146049)）参数值设置为消费者均衡模式，该参数会以消费者角度进行多集群partition分配，保证消费者在所有集群上分到的partition数量是均衡的，假设topic生产端开启了同地域集群优先或者是全部集群的前提下，topic数据同时写入N个机房，消费端开启了消费者均衡模式后消费者实例个数最大可以设置为N*topic分区数；以上图中MQ
topic为例
分区数是80，生产端和消费端分别开启同地域集群优先和消费者均衡模式，生产端数据写入到2个机房，此时消费端最大实例个数为80*2，当source算子并行度设置为160时数据分布情况如下：

![[90_管理/附件/flink_opt_fig_6.png]]
图6 source并行度为160时算子数据分布均衡

当source算子并行度设置为160时数据分布比较均衡没有出现数据倾斜现象，相比source并行度为80时提高了topic容灾能力也提升了消费能力。

结论：该场景下的数据倾斜只需要保证数据源MQ Topic
分区数是source算子并行度的整数倍，过小影响性能过大存在资源浪费，同时其他算子（flatmap，map，filter等）的并行度设置为Source算子并行度的倍数就可以解决了。此外在实际生产中建议MQ
topic生产端开启同地域集群优先或者是全部集群的集群分配策略，消费端开启消费组均衡模式，这样不仅可以使数据流量写入更加均衡而且可以提升topic的容灾能力、扩充消费端的消费实例个数，提高消费速度；

  * **不存在热点Key但分组操作之后算子出现数据倾斜** ：

由于不存在热点key问题表示业务数据上没有数据倾斜，这种场景的数据倾斜大多数是由于分组之后operator的每个subtask上的KeyGroup分布不均衡导致数据的，operator的每个subtask是以KeyGroup为基本单位来接收、处理数据的，KeyGroup是Keyed
State
Rescale的基本单位，分组操作将数据以KeyGroup的形式分配到各个subtask去处理，具体分配逻辑如下（源码基于FlinkV1.12）：

        
        org.apache.flink.runtime.state.KeyGroupRangeAssignment#computeOperatorIndexForKeyGroup
        public static int computeOperatorIndexForKeyGroup(
          int maxParallelism, int parallelism, int keyGroupId) {
          return keyGroupId * parallelism / maxParallelism;
        }
        通过上述代码可以推算出keyGroup将会被分配到operator的哪个subtask上，那怎么查看每个subtask处理的所有KeyGroup信息呢看下面代码：
        org.apache.flink.runtime.state.KeyGroupRangeAssignment#computeKeyGroupRangeForOperatorIndex
            public static KeyGroupRange computeKeyGroupRangeForOperatorIndex(
                    int maxParallelism, int parallelism, int operatorIndex) {
                checkParallelismPreconditions(parallelism);
                checkParallelismPreconditions(maxParallelism);
                Preconditions.checkArgument(
                        maxParallelism >= parallelism,
                        "Maximum parallelism must not be smaller than parallelism.");
        
                int start = ((operatorIndex * maxParallelism + parallelism - 1) / parallelism);
                int end = ((operatorIndex + 1) * maxParallelism - 1) / parallelism;
                return new KeyGroupRange(start, end);
            }
        以上代码块展示了如何计算operator上每个subtask处理的KeyGroupRange，每个subtask上处理的KeyGroup个数是否一致决定了operator是否存在数据倾斜，
        由代码可知每个subtask处理KeyGroupRange主要由operator并行度和KeyGroup个数两个参数来决定，也就是说分组操作造成的KeyGroup分配不均衡问题
        主要是由operator并行度和KeyGroup个数设置不合理导致的；KeyGroup个数也即是maxParallelism参数具体计算逻辑如下：
         org.apache.flink.runtime.state.KeyGroupRangeAssignment#computeDefaultMaxParallelism
         public static int computeDefaultMaxParallelism(int operatorParallelism) {
                return Math.min(Math.max(MathUtils.roundUpToPowerOfTwo(operatorParallelism + (operatorParallelism / 2)),128),32768);
         }

由KeyGroup相关源码中maxParallelism计算公式可以得出maxParallelism大小取决于operator并行度，具体计算逻辑如下：operator并发度*1.5
向上取整为最接近的2的N次幂的数，和128进行比较取两者较大值，两者的较大值再和32768取较小值，最终较小值就是KeyGroup的个数 ；Flink
KeyGroup个数默认是128（2^7），最大是32768(2^15)；结合实际开发经验以及KeyGroup的分配策略我们实际生产中建议将operator并行度设置为2的N次幂来解决这种数据倾斜，接下来从理论上分析一下该方法是否可行，假设operator
KeyGroup个数为默认值128 也即maxParallelism为128 我们计算一下当operator并行度分别为8和15时
operator每个subtask分配的KeyGroupRange信息如下：

并发度为15时KeyGroupRange分配信息| | 并发度为8时KeyGroupRange分配信息  
---|---|---  
**subtask-index**| **KeyGrouprange**| **KeyGroup个数**| | **subtask-index**| **KeyGrouprange**| **KeyGroup个数**  
0| 【0~8】| 9| | 0| 【0~15】| 16  
1| 【9~17】| 9| | 1|  【16~31】 | 16  
2| 【18~25】| 8| | 2| 【32~47】| 16  
3| 【26~34】| 9| | 3| 【48~63】| 16  
4| 【35~42】| 8| | 4| 【64~79】| 16  
5| 【43~51】| 9| | 5| 【80~95】| 16  
6| 【52~59】| 8| | 6| 【96~111】| 16  
7| 【60~68】| 9| | 7| 【112~127】| 16  
8| 【69~76】| 8| | | |   
9| 【77~85】| 9| | | |   
10| 【86~93】| 8| | | |   
11| 【94~102】| 9| | | |   
12| 【103-110】| 8| | | |   
13| 【111~119】| 9| | | |   
14| 【120~127】| 8| | | |   
  
查看表格数据可发现：并发度为8时operator
每个subtask分配的KeyGroup个数是相对均衡的不存在数据倾斜问题，并发度为15时subtask上的KeyGroup分配存在一定的不均衡，接下来我们在实际开发中验证一下

举例验证一下，[[Flink SQL 完整语法教程|Flink SQL]] 如下：

        
        select *
          from (
                select *,
                       row_number() over( partition by waybill_id order by utime desc, waybill_status desc ) as rno
                  from DWDWaybillCommon
               ) t
         where rno = 1

代码主要是为了实现去重功能，其中以waybill_id 作为分组字段，按照
utime，waybill_status逆序排列；代码相同的情况下我们查看一下并行度分别为8和15时Rank算子的是否存在数据倾斜，当Rank算子并行度为8时数据分布相对均衡只存在极少量的数据倾斜，见下图：

![[90_管理/附件/flink_opt_fig_7.png]]
![[90_管理/附件/flink_opt_fig_8.png]]
图7 Rank算子并行度为8时数据分布相对均衡 图8 Rank算子并行度为15时算子存在数据倾斜

通过以上示例以及实际测试结果可得出结论：盲目增加operator的并行度并不能解决数据倾斜，有可能会适得其反，当operator并行度设置为为2的N次幂时每个subtask分配的KeyGroup是相对比较均衡的，可以有效减少由于KeyGroup分配不均衡造成的数据倾斜。除了将operator并行度设置为2的N次幂是否还有其他办法可以解决这种由于KeyGroup分配不均衡导致的数据倾斜？因为对于一些任务而言并行度设置为2的N次幂时存在一定的资源浪费，如果不设置为2的N次幂时又会存在数据倾斜，针对这样的特殊场景的解决方案就是：合理设置KeyGroup个数也就是MaxParallelism大小以及operator并行度；还是拿上述例子来说明
我们在任务启动时加上参数“\--max_parallelism
32767”，看一下当Rank算子并行度为15时，Rank算子的数据分布情况，详细信息见下图：

![[90_管理/附件/flink_opt_fig_9.png]]
图9 添加max_parallelism参数之后Rank算子并行度为15时数据分布相对均衡

通过对比发现添加“--max_parallelism 32767”参数之后Rank算子在未改变并发的前提下数据分布相对比较均衡，只存在少量的数据倾斜现象。

以上实例证明添加max_parallelism是可以解决或者缓解由于KeyGroup分配不均衡导致的数据倾斜问题，此外添加max_parallelism之后还有另外一个好处就是可以解决任务扩并发之后无法从cp恢复的问题，上面章节中提到keygroup是Keyed
State
Rescale的基本单位，如果任务扩并发之后新生成的keygroup个数超过了现在任务state中原有keygroup个数，由于keygroup是state中的最小单位，是无法进行拆分，所以这种情况下是无法从cp恢复的；

可能大家会有疑问keygroup个数设置这么大对任务性能有没有影响，这个问题在Flink官网有一定的说明感兴趣的同学可以去官网查看链接地址为：(https://nightlies.apache.org/flink/flink-docs-
release-1.12/dev/parallel.html#setting-the-maximum-parallelism)，文档明确指出了对于some
state
backends的性能是有影响的，社区人员在经过测试后当集群使用RocksDBStateBackend时对性能影响很小（详情见(https://issues.apache.org/jira/browse/FLINK-21695?focusedCommentId=17299546&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-
tabpanel#comment-17299546)）  
目前配送侧flink集群的statebackend设置的均为RocksDB，所以max_parallelism参数是可以放心使用的。

结论：对于分组之后由于KeyGroup分配不均衡导致的数据倾斜问题可以通过调整并行度为2的N次幂，同时添加“\--max_parallelism
32767”参数（参数值可以灵活调整）来解决或者缓解，实际生产中建议加上“max_parallelism”参数配置不仅可以解决数据倾斜问题，还可以解决任务扩并发之后无法从cp恢复的问题。

  * **存在热点Key导致分组操作之后算子出现数据倾斜** ：

对于这种类型的数据倾斜，是由于业务数据本身存在热点key，调整并行度或者是KeyGroup大小是无法有效解决的，下面看一个例子：

比如有个实时需求是要求计算各个城市进单量可能我们第一反应想到的SQL就是下图所示：

        
        select
          city_id,
          sum(waybill_in_cnt) as waybill_in_cnt
        from WaybillCommon
        group by city_id
        

但是在实际生产中我们会发现这个SQL稳定性很差，有些头部城市的进单量远远大于一些小城市，这样就会产生热点key的问题，会产生一定的数据倾斜，在流量高峰期间会出现反压现象，针对这样的问题我们一般有两种解决方法：

    * **Local-Global Aggregation**

Local-Global Aggregation优化原理是将原来的Group
Aggregate分成Local和Global两阶段聚合，类似MapReduce模型中Combine+Reduce处理模式。第一阶段Local
Aggregation是在上游节点本地对数据进行攒批聚合，并将预聚合结果输出到下游。第二阶段Global
Aggregation是将收到的上游预聚合结果merge起来，得到最终的聚合结果。

下图显示了Local-Global Aggregation如何提高性能，具体使用方式以及详细介绍可参考(https://nightlies.apache.org/flink/flink-docs-
release-1.12/dev/table/tuning/streaming_aggregation_optimization.html#local-
global-aggregation)

![[90_管理/附件/flink_opt_fig_10.png]]
图10 Local-Global Aggregation性能提升示意图

    * **Split Distinct Aggregation**

Local-Global 优化可有效解决常规聚合场景下的数据倾斜，例如 SUM、COUNT、MAX、MIN、AVG。但是在处理 Distinct
Aggregation时性能提升不大。

例如有需求要查看每个城市的日活用户，最直观的就是以下这种SQL写法

    
    SELECT city_id,
           COUNT(DISTINCT user_id)
      FROM WaybillCommon
     GROUP BY city_id

由于头部城市的日活用户数明显要大于小城市日活用户数，所以此SQL同样存在热点Key问题，在COUNT DISTINCT场景下即使开启Local-Global
Aggregation优化也并不能减少Global Aggregation阶段的数据量，同样会出现数据倾斜的问题；Split Distinct
Aggregation优化思路是将SQL手动拆分为两层聚合（增加一层内在的聚合，聚合Key为Distinct Key取模的打散数据）；第一次聚合由
group key 和额外的 bucket key 进行 shuffle。bucket key 是使用 HASH_CODE(distinct_key) %
BUCKET_NUM 计算的。BUCKET_NUM 默认为1024，可以通过 table.optimizer.distinct-
agg.split.bucket-num 选项进行配置。第二次聚合是由原始 group key 进行 shuffle，并使用 SUM 聚合来自不同
buckets 的 COUNT DISTINCT 值。由于相同的 distinct key 将仅在同一 bucket 中计算，因此转换是等效的。bucket
key 充当附加 group key 的角色，以分担 group key 中热点的负担。bucket key 使 job
具有可伸缩性来解决不同聚合中的数据倾斜/热点。

优化后的查询SQL如下：

    
    SELECT city_id, SUM(cnt)
    FROM (
        SELECT city_id, COUNT(DISTINCT user_id) as cnt
        FROM WaybillCommon
        GROUP BY city_id, MOD(HASH_CODE(user_id), 1024)
    )
    GROUP BY city_id

下图显示了Split Distinct Aggregation 如何提高性能（假设颜色表示 city_id，字母表示
user_id），具体详细介绍可参考(https://nightlies.apache.org/flink/flink-docs-
release-1.12/dev/table/tuning/streaming_aggregation_optimization.html#split-
distinct-aggregation)

![[90_管理/附件/flink_opt_fig_11.png]]
图11 Split Distinct Aggregation性能提升示意图

结论：对于由于存在热点Key而导致数据倾斜的问题通过开启Mini-Batch、Local-Global Aggregation 或者是使用Split
Distinct Aggregation以及由 Split Aggregation演变的"加盐预聚合，去盐全局聚合"两阶段聚合都可以很好的解决该问题。

### 4.2 **维表Join性能低下**

优化思路章节中我们介绍了维表Join性能低下的几个原因以及对应的优化方向，那就结合我们的实际优化经验介绍一下具体优化过程。

**异步IO：** 异步IO将原来同步模式下查询维表之后的等待时间均摊到了多次查询请求上，减少了线程阻塞，提高了任务吞吐量，对比图如下

![[90_管理/附件/flink_opt_fig_12.png]]
图12 同步IO，异步IO请求过程对比图

对比未开启异步IO前与开启异步IO之后不同线程数下消费速度

![[90_管理/附件/flink_opt_fig_13.png]]
图13 开启异步IO之后在不同线程数量下消费速度对比

结论：开启异步IO可以大幅提升维表join任务吞吐量，但吞吐量并不是随着线程数量增加而呈线性几何似的增长需要合理设置线程数。

**缓存维表数据：**
将维表中的数据保存到TM本地内存中，查询维表数据时只需要查询本地缓存即可无需与外部存储进行交互，可以极大提升数据处理的吞吐量；维表缓存策略可以归纳为2种：

  * 全量缓存：维表数据全量保存可以大幅度提升任务吞吐量降低对外部缓存的访问频次，但是对于数据量大的维表需要花费大量内存资源，实际生产中只针对较小维表使用。

  * LRU缓存：该策略会在每个节点创建一个 LRU 本地缓存，维表查询之前先进行一次本地缓存查询如果命中直接返回结果，否则去发起新的请求去查询外部存储，可以通过cacheSize 调整缓存的大小，cache ttl调整缓存生命周期，虽然LRU缓存提升任务性能不如全量缓存但是灵活性比较高，消耗内存资源也相对较少，对于各种维表都可以使用，胜在各方面都比较均衡。

**攒批关联：** 攒批关联主要是是为了减少 RPC
的调用次数。原理类似MiniBatch攒一批数据或者是攒够一定时间的数据以后，调用维表的批量查询接口，减少调用次数，目前该功能社区还在建设中。[](https://cwiki.apache.org/confluence/display/FLINK/FLIP-204%3A+Introduce+Hash+Lookup+Join)

**维表Join前将实时流按照Join Key进行Hash分组：**
Hash分组之后实时流中相同key的数据会在同一个subtask中处理，在任务处理消息量相同的情况下这样就缩小单个container上处理Key的数量，提高缓存命中率，减少访问外部存储频次；具体信息参考：(https://cwiki.apache.org/confluence/display/FLINK/FLIP-204%3A+Introduce+Hash+Lookup+Join)。

综上介绍了现阶段我们整理的维表Join的几个优化方案，在实际生产中我们大多数会同时将多种优化方案结合起来使用，这样可以最大程度的来提高任务的吞吐量，接下来以我们实际生产中的一个任务为例来说明：

我们有个维表Join任务需要关联11次维表，遇到运维故障时该任务需要花费大量时间来消除积压数据，任务性能较低，严重影响了数据服务的时效性和稳定性，脱敏后的SQL大致如下

    
    
    select * from (select *    
    from
          waybill
          left join A FOR SYSTEM_TIME AS OF waybill.proctime as org_info on org_info.id = waybill.org_id
          left join B --  
          FOR SYSTEM_TIME AS OF waybill.proctime as res_poi on cast(waybill.poi_id as bigint) = res_poi.poi_id
      ) ll
      left join C
      FOR SYSTEM_TIME AS OF ll.proctime as res_plan on cast(ll.plan_id as bigint) = cast(res_plan.id as bigint)
      left join D
      FOR SYSTEM_TIME AS OF ll.proctime as part_org on ll.org_id = part_org.bm_org_id
      ......
      left join K FOR SYSTEM_TIME AS OF ll.proctime as users on ll.rider_id = users.bm_user_id

我们在打开异步IO，使用LRU缓存之后发现吞吐量依旧比较低，而且缓存命中率很低，为此我们对SQL进行了改造，改造后SQL如下：

    
    
    select * from (select *    
    	from (
            select
              *
            from
              (
                select
                  *,
                  row_number() over(
                    partition by waybill_id
                    order by
                      emit_order desc
                  ) as rno
                from
                  waybill
              ) t
            where
              rno = 1
          ) as waybill
          left join A FOR SYSTEM_TIME AS OF waybill.proctime as org_info on org_info.id = waybill.org_id
          left join B --  
          FOR SYSTEM_TIME AS OF waybill.proctime as res_poi on cast(waybill.poi_id as bigint) = res_poi.poi_id
      ) ll
      left join C
      FOR SYSTEM_TIME AS OF ll.proctime as res_plan on cast(ll.plan_id as bigint) = cast(res_plan.id as bigint)
      left join D
      FOR SYSTEM_TIME AS OF ll.proctime as part_org on ll.org_id = part_org.bm_org_id
      ......
      left join K FOR SYSTEM_TIME AS OF ll.proctime as users on ll.rider_id = users.bm_user_id

对比前后SQL可以发现优化后按照waybill_id进行分组，然后utime和waybill_status逆序排列取最新的一条数据；接下来分析一下这样做的目的：

  1. 分组排序之后只取最新的一条数据在一定程度上可以降低输出数据量，减少关联维表次数；

  2. 按照waybill_id进行分组之后可以保证相同waybill_id的数据会在同一个subtask 同一个tm执行，再加上调整case size大小，在一定时间内处理相同数据量的前提下单个tm处理的key个数会减少，本地cache命中率会得到极大的提升，关联维表次数也会下降，提高任务处理性能；

优化后维表关联次数有了大幅度下降，见下图：

优化后DWDBmUserOrgValidBean维表的关联次数由之前午高峰的600w+/min降低为优化后的50w+/min，关联次数降低了91.5%，详细信息见下图：

![[90_管理/附件/flink_opt_fig_14.png]]
![[90_管理/附件/flink_opt_fig_15.png]]
图14 优化前维表关联次数 图15 优化后维表关联次数

优化后午高峰输出数据条数由338w+/min降低为139w+/min，输出条数降低了58.9%，详细信息见下图：

![[90_管理/附件/flink_opt_fig_16.png]]
![[90_管理/附件/flink_opt_fig_17.png]]
图16 优化前午高峰输出数据条数 图17 优化后午高峰输出数据条数

接下来我们对任务通过回溯数据的方式对任务进行压测，在17:03分将消费组回溯到从11:30开始消费 具体消费速度以及积压数据量为单机房5亿+，见下图：

![[90_管理/附件/flink_opt_fig_18.png]]
图18 回溯之后消息积压量

优化前任务消费速度在440w/min~470w/min左右，优化后消费速度为1780w/min~1900w/min左右速度提升了4倍左右  

![[90_管理/附件/flink_opt_fig_19.png]]
![[90_管理/附件/flink_opt_fig_20.png]]
图19 优化前消费速度 图20 优化后消费速度

优化前任务单机房积压5亿+数据恢复所需时长为4h+，优化后单机房积压5亿+数据量恢复时间约47min，速度提升了5倍左右，恢复时长见下图：

![[90_管理/附件/flink_opt_fig_21.png]]
![[90_管理/附件/flink_opt_fig_22.png]]
图21 优化前消除积压耗时 图22 优化后消除积压耗时

结论：在实际开发中可以同时将多种优化策略组合使用，比如可以同时开启异步IO，使用LRU缓存，以及对实时流Join
Key进行Hash分组，这样可以提高本地缓存命中率，减少维表关联次数，大幅度提升任务吞吐量；需要注意的是进行Hash分组之后会引入state，这会额外消耗一定的内存和CPU资源，但是可以通过合理设置state
ttl 降低内存使用量，性能优化的时候要综合考虑投入产出比。

### 4.3 Regular Join使用不当

#### **多表（2个以上）Join时表关联顺序选择错误**

  * **背景**

由于业务需求的迭代，需要将原来一个DWD层的双流Join作业(双流表流量均较大，TPM均在百万量级)新增一个很小的流表(TPM均在万量级)关联改为三流Join作业，运行一天后发现作业反压严重，午高峰期间消费组积压数据迟迟无法消费完成，后通过调整作业参数增加作业消费能力恢复。事后通过相关监控指标发现，新增一个很小的流表Join后，做Checkpoint和Savepoint时候状态大小膨胀了数倍，当State过大时有些State需要存储在磁盘中，频繁的磁盘IO导致了作业性能下降，所以造成消费速度下降出现了消息积压。

  * **原理分析**

现阶段Flink引擎不能很好的支持多流（超过2个流）Join，3个流Join会被拆解为2个双流join，由于Flink双流join会把两个流的数据全部存储在State中，所以3个流Join就会导致有些数据会被重复存储在State中，造成任务的State过大，任务需要频繁的与State交互，当State过大时有些State需要存储在磁盘中，交互时需要读磁盘中的数据，读磁盘是一个耗时较久的操作所以造成消费速度下降出现了消息积压；该任务上线后任务的Savepoint大小由之前的700+G增长到3T+，与上述分析的结果相符，接下来我们用下图来进行演示双流Join和三流Join的State膨胀过程：

由于A表为运单表数据量最大，B表包裹表数据次之，C表包裹扩展数据最小，这种Join顺序State中会存储n+1份运单表数据，1+nX%份包裹表数据，1份包裹扩展表数据，此时这种Join顺序是State最大的，当X=100,n=2时
与原有双流Join对比，此时State增加了 2A+2B+C

  * **解决方案**

目前可知双流join state大小为 = A+B，三个流join state最大为= (n+1)A+B*(1+nx%)+C，当x为100,n为2时
最大state = 3A+3B+C
，三个流join可以转化为2个双流join，所以可以尝试通过调整流的join顺序来降低state存储数据的大小，经过分析调整我们得出如下解决方案：

将B，C两个流进行双流join，然后A流与B，C双流join的结果再进行双流join
这样join的语义不会有变化，而且代码不用做复杂的开发，具体join信息如下图所示：

当X=100,n=2时 此时state中存储数据=3B+A+3C
现在线上state最大时为=3A+3B+C，由于C表数据量很小，所以回撤数据量级也相对小很多，且C表仅有A表流量的百分之一，所以该优化方案与之前任务对比可得state减少了A表的重复状态，并且也减少了回撤导致的B表重复状态，所以该优化方案可以显著减少state存储。

**解决成果**

通过在测试链路回溯两小时数据验证比较发现，优化后Savepoint时的状态大小减少到优化前的五分之一左右，这样基于原来的作业参数就可以保证作业正常运行，减少了计算资源的浪费

![[90_管理/附件/flink_opt_fig_26.png]]
![[90_管理/附件/flink_opt_fig_27.png]]
图26 优化前Savepoint大小 图27 优化后Savepoint大小

结论：对于Flink的中的多流join场景，我们建议优先对小表进行关联，然后再按照业务逻辑依次与大表进行关联，尽可能将大表放到最后关联，降低state大小，提高任务性能。

  * #### **Regular Join输出数据膨胀**

**分析现象 ：**

1、实时作业遇见网络、HDFS、TM机器等故障后会自动重启，而合流作业消耗资源较多存在无法启动的风险，状态很大重启也较慢，重启后积压恢复也很慢，使下游大量指标计算作业产生延迟；有时没有异常重启，但会出现CP超时或积压的问题。

2、配送合流作业的左右流基本是一对一的关系，但观察到合流作业下发到MQ的数据量比上游MQ输入的数据量之和要大几倍，因此出现了数据放大问题，造成下游计算资源浪费。

**定位根因：**

上述主要问题是性能差，我们需要先理解一下合流JOIN算子是在做什么。

        
        select waybill.id waybill_id,
               waybill.status waybill_status,
               package.ext package_ext
          from waybill
          left join package
            on waybill.bm_pkg_id = package.id
        

以下是Binlog数据源，status 从 0-> 30 ->50 变化的情况。

I：insert 新增，U-：update before修改前， U+：update after修改后，D: delete 删除

运单 Binlog数据

(**I** , id=1,bm_pkg_id=2,status= 0)

（**U-** id=1,bm_pkg_id=2,status= 0, **U+** id= 1,bm_pkg_id=2,status= 30）

（**U-** id=1,bm_pkg_id=2,status =30, **U+** id= 1,bm_pkg_id=2,status= 50）

配送对Binlog 数据进行了清洗，去掉了U-、D, 变成了一个Append 流：

运单 MQ数据（Protobuf格式）

(**I,** id=1,bm_pkg_id=2,status= 0)

（I,id= 1,bm_pkg_id=2,status= 30）

（I, id= 1,bm_pkg_id=2,status= 50）

同样，假设包裹流数据如下：

包裹 MQ（Protobuf格式）

（I, id= 2, ext='x'）

（I, id= 2, ext='y'）

那么，如果直接按照上述**SQL8** 执行会发生什么？ 通过IDEA本地开发代码测试，发现计算结果可能如下：

可能的下发结果

1（waybill_id=1,waybill_satus=0,package_ext= 'x'）

2（waybill_id=1,waybill_satus=30,package_ext= 'x'）

3（waybill_id=1,waybill_satus=50,package_ext= 'x'）

4（waybill_id=1,waybill_satus=30,package_ext= 'y'）

5（waybill_id=1,waybill_satus=0,package_ext= 'y'）

6（waybill_id=1,waybill_satus=50,package_ext= 'y'）

**我们发现2个问题**

1、第4、5条下发的status 是乱序的，正确的顺序是 先 0 再 30

2、第4、5条 status = 0 和 status = 30 的计算结果不需要下发，我们只需要第6条数据

  
**想要理解为什么，就需要查询资料搞清楚Regular Join算子的实现原理：**

Flink SQL 根据上游是否带唯一键将Regular Join计算分为：

| State Structure| Update Row| Query by JK| Note  
---|---|---|---|---  
JoinKeyContainsUniqueKey| <JK,ValueState<Record>>| O(1)| O(1)|  
InputSideHasUniqueKey| <JK,MapState<UK,Record>>| O(2)| O(N)| N = size of
MapState  
InputSideHasNoUniqueKey| <JK,MapState<Record, appear-times>>| O(2)| O(N)| N =
size of MapState  
  
性能：JoinkKeyContainsUniqueKey > InputSideHasUniqueKey > InputSideHasNoUniqueKey

![[90_管理/附件/flink_opt_fig_28.png]]
图28 数据下发示意图

按照这个原理我们来进行如下分析：

**SQL8** 没有指定主键，因此按照InputSideHasNoUniqueKey处理，所有的变化明细都会保存下来。**SQL8** 在（I, id=
2, ext='y'） 这条数据到来时，会查询到3条运单数据，进行关联，并下发。

造成了以下问题：

1、状态大：保存了一个运单生命周期的所有变化

2、性能差：JOIN时查询了全部的历史数据

3：下发数据变多：下发了多余的历史数据，可能使下游计算错误，而且实际上只需要发一条终态结果即可

4、数据乱序：使用MapState保存状态，不能保证有序

**解决方案：**

下面将分别讲述3种解决方案：方案1
是原特征合流采用的方案，通过增加一层聚合逻辑，解决了一部分下发历史数据的问题，但计算资源反而增加了；方案2和方案3通过弄清楚上述原理后，使用了先去重，再合流Join的方法，降低状态大小、提高性能、保证没有历史数据且没有乱序。

**方案1：**

直接在原有**SQL8** 外层加上group
by，根据业务特点取最大值，或最新值。这种方案并没有解决状态、性能问题，反而增加了一层计算，下发数据量仅会减少一小部分（当group by
的结果不变时），乱序问题并没有彻底解决（LastVal
方法是取最后一条，如果排序字段值相同时，不保证取到正确值），我们可以构造一个不重复的全链路排序字段来解决乱序问题，或者如果不在意这种乱序问题也可。但从性能和复杂度上看，这不是一个好的解决方案。

        
        select waybill_id,
               max(waybill_status) waybill_status,
               LastVal(package_ext, putime) package_ext
               max(putime) putime                       
               from(
                select waybill.id waybill_id,
                       waybill.status waybill_status,
                       package.ext package_ext
                  package.utime putime
                  from waybill
                  left join package
                    on waybill.bm_pkg_id = package.id
               ) l
         group by waybill_id
        

**方案2：** 使用子查询构造去重逻辑，使下游感知到唯一键

        
        select waybill_id,
               waybill_status,
               package_ext
          from (
                select id waybill_id,
                       max(bm_pkg_id) bm_pkg_id,
                       LastVal(waybill.status,utime) waybill_status
                  from waybill
                 group by id
               ) w
          left join (
                select *
                  from (
                        select id,
                               ext package_ext,
                               row_number() over(partition by id order by utime desc) as rno
                          from package
                       ) l
                 where l.rno = 1
               ) p
            on w.bm_pkg_id = p.id
        

row_number() over 和 group by + lastval 的区别:

1：row_number() over 如果排序字段 值相同，取第一条，而 lastval 取最后一条

2：row_number() over 支持使用多个排序字段，且可以取最新的多条；lastval
如果需要支持多个字段排序需要开发改造一个新UDF，且只支持取一条

3：row_number() over 使用方式更加简洁，且是整行排序；lastval
返回的是string类型，可能需要使用类型强制转换，写法不简洁，且是每列数据单独聚合

4：row_number() over 不支持mini-batch, lastval 由于是 group by 聚合，可以使用mini-batch

![[90_管理/附件/flink_opt_fig_29.png]]
图29 优化后Join逻辑

我们还是从一条包裹数据变更 （I, id= 2, ext='x'） -> （I, id= 2, ext='y'），来说明**SQL10** 的执行流程：
(https://github.com/apache/flink/blob/master/flink-
table/flink-table-
runtime/src/main/java/org/apache/flink/table/runtime/operators/join/stream/StreamingJoinOperator.java)
中有相关代码及完善的注释，也可以本地测试Debug分析：

1、子查询p **Rank算子** 在收到'y'时，同时依次生产出 两条数据（U- id=2,ext = 'x'）、（U+ id=2,ext = 'y'）

2、**Regular JOIN算子** 收到 （U- id=2,ext = 'x'），查询出关联的数据 运单 satus = 50 ，对于U-
数据，先删除状态，再下发回撤结果 (U- waybill_status=50, package_ext='x')，由于是运单left
join包裹，那么还需要下发一条 （U+ waybill_status=50, package_ext= NULL）

3、**Regular JOIN算子** 收到 （U+ id=2,ext = 'y'），查询出关联的数据 运单 satus = 50
，对于U+数据，保存到状态，并下发结果 （U+ waybill_status=50, package_ext= 'y'）

![[90_管理/附件/flink_opt_fig_30.png]]
图30 优化后数据下发示意图

**效果分析：**

计算性能：可以看出查询的状态不是原来的3个了，提高了查询效率，但引入了去重逻辑，因此如果同一join key 左流或右流
重复次数小于等于2时，加入去重逻辑带来的性能优化不大；如果大于2，那么计算性能会成倍提升

状态大小：同理，同一join key 左流或右流 重复次数小于等于2时，状态大小也优化不大；如果大于2，那么状态大小会成倍减少

下发数据量：同理，同一join key 左流或右流 重复次数小于等于2时，下发数据量差异不大；如果大于2，那么下发数据量会成倍减少

正确性分析：由于去重删除了历史数据，那么不会发生下发结果乱序的情况（如先发出50，再发出0）；但仍存在一个问题是使用left join ， 一条更新发出了
（U+ waybill_status=50, package_ext= NULL）、（U+ waybill_status=50, package_ext=
'y'） 两条数据，包裹相关字段为NULL不符合预期，其原因见上述分析，是由于将一次更新拆分成 U-、U+ 两次处理了

总之，相比原计算逻辑**SQL8** ，从性能和正确性的角度都建议使用**SQL10** 这种先去重再合流的方式。

**如何避免发出空值：**

公司已经开发了Regular Join算子的 mini-batch，使用方法为 --mini_batch_regular_join_disabled
false 。但目前还未大规模推广使用，且存在一个BUG待公司平台解决: 如 **SQL10** 的计算逻辑中走到了
OuterJoinRecordStateCaches.InputSideHasUniqueKeyCache 类的
updateOriginalState方法，改方法调用的 updateAppearTimesOfRecord
方法没有被重写，导致运单状态没有被保存，包裹到来新数据的时候找不到运单，不会下发数据。

但我们可以使用Inner Join 避开上述问题，我们再分析一次 Inner Join 的处理逻辑：

**一条包裹数据变更 （I, id= 2, ext='x'） - > （I, id= 2, ext='y'）**

1、子查询p **Rank算子** 在收到'y'时，同时依次生产出 两条数据 （U- id=2,ext = 'x'）、（U+ id=2,ext = 'y'）

2、**JOIN算子** 收到 （U- id=2,ext = 'x'），查询出关联的数据 运单 satus = 50 ，对于U-
数据，先删除状态，再下发回撤结果 (U- waybill_status=50, package_ext='x')**【注意这里没有下发 （U+
waybill_status=50, package_ext= 'y' )】**

3、**JOIN算子** 收到 （U+ id=2,ext = 'y'），查询出关联的数据 运单 satus = 50 ，对于U+数据，保存到状态，并下发结果
（U+ waybill_status=50, package_ext= 'y'）

可以看出不会发出NULL值，因此也不需要使用Regular Join算子的mini-batch，如果上游数据重复度大，可以考虑在去重算子使用mini-
batch。

**方案3：**

在create table 时声明主键，如

        
        create table waybill (id BIGINT, bm_pkg_id BIGINT, status INT, PRIMARY KEY (id) NOT ENFORCED) with('connector' = 'xxx')
        

计算SQL仍使用 **SQL8**
，运单包裹流的输入可以使用回撤流，也可以只使用Append流。数据在存储到状态时即完成了去重，但无法保证有序，如果上游是回撤流则仍有发出 (+L,
NULL) 问题。保序的解决方案是 connector
支持按某些字段保序，如公司实时开发平台即是在connector作业做排序去重处理，其原理与**SQL10** 一样，因此性能也一样，但其SQL会更加简洁。

**解决成果 ：**

配送合流作业优化前使用的是方案1，优化后使用的是方案2，其优化效果如下：

1、合流作业本身在消费速度不变的前提下，资源由 172CU 降低至 22CU，内存由2T 降至 224G，增量checkpoint
由约35G左右降低至4G，checkpoint端到端时长由2-5s 降低至1-2s。

2、下发数据量午高峰峰值由659w/m降低至129w/m，大幅减少了下游的计算量，合流下游相关作业资源由533CU 降低至 92CU。

![[90_管理/附件/flink_opt_fig_31.png]]
![[90_管理/附件/flink_opt_fig_32.png]]
图31 原合流作业下发数据量 图32 新合流作业下发数据量

![[90_管理/附件/flink_opt_fig_33.png]]
![[90_管理/附件/flink_opt_fig_34.png]]
图33 原合流作业3分钟一次的Checkpoint大小 图34 新合流作业5分钟一次的Checkpoint大小

**总结** ：

| 简述| 使用场景| 可保证不乱序| 状态| 性能| 下发数据量| 推荐  
---|---|---|---|---|---|---|---  
方案1| 在join外加一层group by 聚合| 数据原更新频率很低，如一个维度的数据只发出1-2次| 是| 大| 差| 大| ❎  
方案2| 先对数据源分别去重，再join| 数据源会发生更新的场景，更新次数越多，其效果越好| 是| 正常| 好| 正常| ✅  
方案3| create table 时声明主键，并根据指定字段排序去重| 同上，使用该方案SQL可以更加简洁| 是| 正常| 好| 正常| ✅  
  
结论：如果使用公司实时开发平台平台计算那么直接使用方案3在connector处声明主键、排序去重方式，最为方便清晰；否则可以使用先构造子查询去重再Join的方式，效果也一样。都需要注意Outer
Join 回撤问题，可通过Inner Join避开，或使用Regular Join算子的 mini-batch解决（特定逻辑下存在一些BUG）。

### 4.4 **任务参数、资源配置不合理**

  * **并行度，KeyGroup个数设置不合理**

在介绍数据倾斜章节讲述了如何合理设置任务并行度以及KeyGroup个数，推荐将分组之后Join算子，聚合算子的并行度设置为2的N次幂，同时添加max_parallelism参数，如果将并行度按照2的N次幂进行设置会出现资源浪费的问题，可以尝试合理设置max_parallelism参数保证每个subtask分配的KeyGroup个数相对均衡，避免出现数据倾斜的现象，至于没有涉及分组操作的算子保证数据源MQ
Topic 分区数是source算子并行度的整数倍，其他算子（flatmap，map，filter等）的并行度设置为Source算子并行度的倍数就可以了。

  * **资源分配不合理**

通过查看任务的(http://rt.data.某互联网公司.com/grafana/d/fayM2jrWz/flink_job_metrics-
public)监控查看CPU和内存相关的指标，拿内存举例，观察一段周期内（7天）或者是流量高峰时（冲单节活动期间）任务的资源使用量，如果平均资源使用率达
>= 70% 那说明任务资源分配相对合理，如果低于70%那说明存在一定的资源超配，需要进行减配缩容。接下来从内存和CPU两个方面阐述一下资源优化思路：

    * **CPU资源优化** ：对于IO密集型任务，CPU负载和利用率相对比较低，可以尝试添加**yarn.containers.vcores:1** 参数，这个参数表示单个container分配Vcore为1，因此任务消耗vcore个数就和分配TM数量保持一致；该参数默认为-1 代表分配vcore个数和slot个数保持一致，默认情况下 slot个数=并发度，当前资源成本计算公式CU个数=任务最大并发*0.7 当并发度越高时消耗CU越大成本也就越大，设置此参数之后提高任务并行度并不会增加资源成本，反而会提升CPU利用率和任务的消费速度；举例说明假设任务并发度为1024，TM个数为128，任务CU = 1024*0.7 = 716.8；添加**yarn.containers.vcores:1** 配置之后任务并行度和TM个数均不变，但是任务CU = 128*0.7=90CU 与原有的716.8CU相比节省了87.4%的CU成本。任务性能上不会有太多影响，而且cpu利用率提升了一倍。此外对于时效性不太敏感的任务可以尝试增大**execution.buffer-timeout** 参数值，网络缓存buffer在满足以下三个条件之后才会向下游进行发送：NetworkBuffer写满、超时时间到了、遇到特殊标记（如Checkpoint Barrier），通过合理增加超时时间可以避免数据未达到buffer 上限时提前下发，降低下发频次，减少cpu资源浪费，该参数默认值为100ms，推荐设置为500ms-1000ms，具体需要根据任务并发数以及对时效性的要求合理设置该参数。

    * **内存资源优化** ：对于SSD队列上的实时任务而言可以尝试缩减任务TM个数提高单个TM的内存，以此达到缩减任务总内存的目的，SSD盘的磁盘io响应速度快，可以大幅提升RocksDB读写速度，因此不需要分配过多的TM来均摊state数据，缩减TM之后算子或者是进程间的资源复用、共享可以缩减内存使用量，**需要注意的是不可过多减少TM个数因为这样会使得单个TM的CPU使用率飙升、YounGC和FullGC的频次也会增加，对于单个TM内存也不宜设置过大避免集群出现过多内存碎片** 。对于非SSD队列的任务如果任务state不是很大的话，此优化同样有效。

接下来举例说明一下我们是如何根据上述优化思路来进行内存优化的，测试同一个任务（双流join任务，Regular
Join）在不同资源配置下任务性能以及各项监控指标是否正常：

任务优化前后资源配置如下：

![[90_管理/附件/flink_opt_fig_35.png]]
![[90_管理/附件/flink_opt_fig_36.png]]
图35 优化前资源配置信息 图36 优化后资源配置信息

任务优化前后内存使用率从75%降为69%，午高峰期间CPU平均使用率从100%飙升到了200%：分配总内存数从2T缩减为1472G，内存缩减了576G约28%

![[90_管理/附件/flink_opt_fig_37.png]]
![[90_管理/附件/flink_opt_fig_38.png]]
图37 优化前内存、CPU使用情况 图38 优化后内存、CPU使用情况

优化前后对比发现优化后每秒TM YoungGC次数是优化前的2倍，每秒TM FullGC次数也有一定的上升：

![[90_管理/附件/flink_opt_fig_39.png]]
![[90_管理/附件/flink_opt_fig_40.png]]
图39 优化前每秒YoungGC，FUllGC次数 图40 优化后每秒YoungGC，FUllGC次数

对比优化前后任务午高峰期间消费速度基本一致

![[90_管理/附件/flink_opt_fig_41.png]]
![[90_管理/附件/flink_opt_fig_42.png]]
图41 优化前任务消费速度 图42 优化后任务消费速度

结论：

      1. CPU资源优化：对于IO密集型任务，优化CPU资源可以尝试添加**yarn.containers.vcores:1** 参数，我们经过实践验证通常可以缩减30%左右的CU成本，对于并发较大的IO密集型任务优化成本更可观，对时效性要求不高的任务可以尝试增加**execution.buffer-timeout** 该参数超时时间，同样可以降低CPU使用量。

      2. 内存资源优化：通过对比优化前后的各项指标，对比结果在预期范围内的，通过缩减TM个数，提高单个TM内存配额的确可以达到节省内存的目标，但是过度缩减TM个数的确会导致TM的CPU使用率飙升、YounGC和FullGC的频次也会增加，在这个任务中我们通过牺牲CPU利用率和负载来达到缩减内存的目的，由于Flink在CPU上无法进行隔离因此在集群CPU利用率不高的情况下该方案是可行的，该任务优化后在线上已经稳定运行了5个月以上，后续我们会尝试调整TM个数和任务并行度以及内存相关的配置，在保证任务性能的前提下降低CPU利用率以及负载，同时还能够降低YoungGC，FullGC频次。

  * **内存参数，RocksDB参数配置不合理**

介绍内存参数优化之前首先看一个内存模型图

![[90_管理/附件/flink_opt_fig_43.png]]
图43 Flink内存模型图

见过模型图之后我们了解一下Flink内存模型的各个组成部分以及参数配置：

**组成部分**| **描述**| **配置参数**|  默认值  
---|---|---|---  
框架堆内存（Framework Heap Memory）| 用于 Flink 框架的 JVM 堆内存。不管是堆内存还是堆外内存，Flink
中的框架内存和任务内存之间目前没有隔离。|
(https://nightlies.apache.org/flink/flink-
docs-master/zh/docs/deployment/config/#taskmanager-memory-framework-heap-
size)| 128M  
任务堆内存（Task Heap Memory）| 用于 Flink 应用的算子及用户代码的 JVM 堆内存。|
(https://nightlies.apache.org/flink/flink-
docs-master/zh/docs/deployment/config/#taskmanager-memory-task-heap-size)|  
托管内存（Managed memory）| 由 Flink 管理的用于排序、哈希表、缓存中间结果及 RocksDB State Backend
的本地内存。|
(https://nightlies.apache.org/flink/flink-
docs-master/zh/docs/deployment/config/#taskmanager-memory-managed-size)| none  
(https://nightlies.apache.org/flink/flink-
docs-master/zh/docs/deployment/config/#taskmanager-memory-managed-fraction)|
0.4  
框架堆外内存（Framework Off-heap Memory）| 用于 Flink
框架的(https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/mem_setup_tm/#configure-off-heap-memory-
direct-or-native)| (https://nightlies.apache.org/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-framework-off-heap-
size)| 128mb  
任务堆外内存（Task Off-heap Memory）| 用于 Flink
应用的算子及用户代码的(https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/mem_setup_tm/#configure-off-heap-memory-
direct-or-native)。| (https://nightlies.apache.org/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-task-off-heap-size)|
0bytes  
网络内存（Network Memory）| 用于任务之间数据传输的直接内存（例如网络传输缓冲）。该内存部分为基于 (https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/mem_setup/#configure-total-
memory)的(https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/mem_setup/#capped-fractionated-
components)。This memory is used for allocation of (https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/network_mem_tuning/)|
_(https://nightlies.apache.org/flink/flink-
docs-release-1.12/deployment/config.html#taskmanager-memory-network-fraction)_  
  
|  0.1  
JVM Metaspace| Flink JVM 进程的 Metaspace。| (https://nightlies.apache.org/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-jvm-metaspace-size)|
256mb  
JVM 开销（JVM Overhead）| 用于其他 JVM
开销的本地内存，例如栈空间、垃圾回收空间等。该内存部分为基于(https://nightlies.apache.org/flink/flink-
docs-master/zh/docs/deployment/memory/mem_setup/#configure-total-
memory)的(https://nightlies.apache.org/flink/flink-docs-
master/zh/docs/deployment/memory/mem_setup/#capped-fractionated-components)。|
(https://ci.apache.org/projects/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-jvm-overhead-fraction)|
0.1（公司Flink集群为0.25）  
 _(https://ci.apache.org/projects/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-jvm-overhead-max)_|
1gb  
 _(https://ci.apache.org/projects/flink/flink-docs-
release-1.12/deployment/config.html#taskmanager-memory-jvm-overhead-min)_|
192mb  
  
**IOException: Insufficient number of network buffers**

此异常通常表示配置的(https://ci.apache.org/projects/flink/flink-docs-
release-1.12/deployment/memory/mem_setup_tm.html#detailed-memory-model)
大小不足。通过下面三个参数可以修改网络内存：

  * (https://ci.apache.org/projects/flink/flink-docs-release-1.12/deployment/config.html#taskmanager-memory-network-min)

  * (https://ci.apache.org/projects/flink/flink-docs-release-1.12/deployment/config.html#taskmanager-memory-network-max)

  * (https://ci.apache.org/projects/flink/flink-docs-release-1.12/deployment/config.html#taskmanager-memory-network-fraction)

另一方面，也可以检查TM涉及的上下游是否并发过大，可考虑优化作业，减少并发量，以及尽量把算子chain在一起，从而减少网络内存的使用。

**Container Memory Exceeded**

此类问题多数是由于RocksDB通过JNI调用原生库导致内存超用导致的，我们需要调大(https://ci.apache.org/projects/flink/flink-docs-
release-1.12/deployment/memory/mem_setup.html#capped-fractionated-
components)，让Flink预留更多内存即可。另一方面根据情况，可以关闭savepoint ， 避免checkpoint、savepoint
同时执行时RocksDB内存超用。

如图45所示该任务Managed memory 完全没有被使用可以尝试将该部分数据设置为0减少内存分配，节省资源，此现象多见于未使用Keyed State
或者是Operator State的清洗任务、存储任务或者是维表join任务中。

**RocksDB内存参数**

实际生产中RocksDB参数优化，下面会逐一进行解释：

    
    
    taskmanager.memory.managed.fraction:0.6 --参数可以适当调大一些0.5~0.6，分配多一些内存降低刷磁盘的概率，提升任务性能。
    taskmanager.memory.jvm-overhead.fraction:0.4 --建议调大一些 0.3~0.4 防止出现RocksDB内存超用 container被kill的问题。
    state.backend.rocksdb.checkpoint.transfer.thread.num:4 --提升RocksDB增量CP时上传下载速度，避免在CP的异步阶段耗时太久。
    state.backend.rocksdb.thread.num:4 --后台负责 flush 和 compaction 的最大并发线程数。
    state.backend.rocksdb.block.blocksize:64KB --sst文件的基本存储单位，默认4kb 适当调大一些增加每次读取内容，但是增大该参数的话也需要将block.cache-size一起修改，否者读的性能会下降，同时增加blocksize和block.cache-size可以提升读写性能
    state.backend.rocksdb.block.cache-size:128MB --增加block.cache-size可以明显增加读性能。默认大小为8MB，但是通常在内存富余的情况下建议设置到 64 ~ 256 MB。
    state.backend.rocksdb.writebuffer.count:5 --该参数控制内存中允许保留的MemTable最大个数，超过就会被Flush到磁盘上成为SST文件，可以适当调大该值使得MemTable的大小减小一些，降低 Flush操作时造成Write Stall的概率。
    state.backend.rocksdb.writebuffer.number-to-merge:2 --该参数决定了Write Buffer合并的最小阈值，默认值为1，建议适当调大，避免频繁的Merge操作造成的写停顿。
    state.backend.local-recovery:true --任务failover时优先从本地读取状态，减少网络传输带来的时间开销，缩短恢复时长，生效的前提是使用RocksDBStatebackend同时开启增量CP，不支持非对齐CP，仅支持keyed state
    state.backend.rocksdb.use-bloom-filter:true --开启布隆过滤器，检索sst文件中是否存在某个key之前优先查询布隆过滤器，如果不存在则跳过该文件，可以有效提升根据具体key进行点查的性能。
    state.backend.rocksdb.bloom-filter.bits-per-key:15.5 --布隆过滤器中每个key的bits个数，数值越大，精度也会变高，内存占用也会比变大，对查询性能也有一定的提升，但该参数对性能的影响不是线性提高，在达到特定值之后提高该参数性能反而会下降 默认是10，可以尝试设置为15.5,16.0 详情见：https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter#what-is-a-bloom-filter。
    state.backend.rocksdb.bloom-filter.block-based-mode:false --默认为false即使用Full Filters而不是老的Block-based，使用Full Filters查询性能会有显著提升 详见：https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter#full-filters-new-format

按照惯例我们依旧以实际开发中的例子来阐述一下对RocksDB参数优化的过程：

  * **故障背景**

午高峰期间线上一个多流Join任务数据积压比较大，Join算子和聚合算子出现了反压，任务执行cp一直失败，算子不存在数据倾斜问题，通过调大内存以及算子并发均不起作用，后来反复多次抓取反压算子所在TM上的Thread
Dump日志，在(https://fastthread.io/)上进行dump日志分析，发现任务卡在RocksDB.get()方法上，在平台同学的协助下抓取了CPU火焰图
见下图：

![[90_管理/附件/flink_opt_fig_44.png]]
图44 故障任务CPU火焰图

  * **优化过程**

在各种配置参数，以及优化手段都尝试过之后任务积压数据越来越多，消费速度越来越慢，而此时备用链路任务运行正常，未出现消息积压现象，通过排查发现我们在备用链路添加了RocksDB优化参数进行性能测试，还未来得及在主链路进行同步，在对主链路任务添加RocksDB优化参数之后，发现任务消费速度提升很快，积压也很快消除了。

  * **根因分析**

事后对比主备链路相关监控发现主链路存在大量的读磁盘操作，而备用链路则没有，原因在于我们的优化参数调大了RocksDB内存分配比例、blocksize、
block cache等相关参数，提升了RocksDB读的性能。监控信息如下图：

![[90_管理/附件/flink_opt_fig_45.png]]
![[90_管理/附件/flink_opt_fig_46.png]]
图45 备用链路监控 图46 主链路监控

虽然添加RocksDB相关参数可以解决这个问题，但是问题的根因依旧没有定位到，在咨询了社区相关专业同学之后得知原因如下：

    * RocksDB读取数据的时候会优先先从BlockCache里读block，如果block在BlockCache里，就直接读内存，如果block不在BlockCache里，则从磁盘读取block到内存后，解压到放到BlockCache中，下次读取就不需要读磁盘了；

    * block是缓存的最小粒度，磁盘上的block是压缩过的，而BlockCache中的block是解压过的，避免读数据时重复解压缩浪费CPU资源；block分为两种metadatablock和datablock；metadatablock存储index和Bloomfilter相关信息，datablock就是存放的真正的数据，默认一个block4KB，可以调节大小，index默认只有一个block，也就是默认RocksDB的一个文件的索引存在一个block里。

    * 当RocksDB内存不足时也即BlockCache容量不足，此时datablock或indexblock都会从blockcache中剔除而频繁落盘，由于datablock较多，且size大小固定，风险不大，由于index大小不可控有可能能达到1-2M甚至更大；如果内存不足导致index频繁落盘，则每次读取数据都需要从磁盘读2MB的文件，且需要解压，因为磁盘上是压缩的，内存里是解压后的，每次读一条数据需要解压2MB的文件导致CPU打满那么RocksDB读性能就会很差，我们根据火焰图中的信息可知：NewIndexIterator方法是在读索引，RawUncompress是在解压索引，这两个步骤消耗了整个进程大部分CPU，导致任务卡死。

  * **解决方案：**

    * 切分index化整为零，将index切分为相同大小的小块block，每次读取时候只读取对应的小块数据，这样就不会出现每次都去读取2M大小的索引频繁解压导致任务卡死的情况了，对应优化参数为

**state.backend.rocksdb.memory.partitioned-index-filters:true**
但是目前这个参数只在>=1.13版本才有，所以现阶段无法使用该参数从根本上解决这个问题。

    * 调整RocksDB内存大小，增加BlockCache size大小，确保内存足够大，减少index落盘的概率；对应的优化策略是调整taskmanager.memory.managed.fraction、state.backend.rocksdb.block.blocksize、state.backend.rocksdb.block.cache-size等相关参数

    * 优化任务，降低任务state数量，从源头解决state数量过大问题。

# 五、优化成果

对大量任务进行性能、资源上的优化之后我们取得了一定的优化成果，我们从以下几个方面总结一下收益：

  * **资源成本：** 累计优化任务数800+，节省了CU数4700+，内存约14T，折合成本节省308w/年。

  * **数据服务质量：** 优化后任务撑住了公司级冲单活动期间（秋天的第一杯奶茶、七夕、520、情人节等）流量洪峰的考验，为业务提供实时准确，稳定高效的数据支撑，高质量的保障了业务实时运营和精准决策场景下数据服务的稳定性和时效性。

  * **日常运维：** 任务故障恢复时长由原来的40min~1h降为了10~15分钟，极大缩短了故障恢复时长；核心任务优化之后故障频次由原来的每Q 1~2次 降为现在的0次（除去外部因素导致的集群故障）。

# 六、未来规划

经过团队的不懈努力，我们完成了一些任务的优化工作，解决了线上任务的一些性能问题，但是这些还远远不够，在性能优化的过程中我们也发现了一些我们未来需要继续努力的地方：

  * **沉淀经验：** 对我们的优化经验要进行总结、沉淀，并将其作为我们的开发规范，确保每种类型的作业都有一套合适的开发规范，以及性能参数配置；

  * **主动识别存在性能问题的任务：** 性能优化的过程中我们更多的是通过日常运维来发现存在性能问题的作业，除了对任务进行压测并没有很好的办法可以主动识别隐藏的存在性能问题的任务，这是需要我们努力去建设的地方；

  * **与平台共建探索性能优化：** 尝试与平台共建一起探索更优的解决方案，例如维表攒批Join，RocksDB调优等，为业务提供更快更准更稳定的数据服务。

  * **资源优化向工具化发展：** 现阶段资源优化更多的是依赖人工去发现问题，无法做到主动监控内存，cpu等指标资源使用率，我们后续会尝试进行这方面的工具建设，能够主动获取到资源使用率之后既可以主动识别资源浪费问题，还可以提前发现任务资源不足的问题做到提前预警。
