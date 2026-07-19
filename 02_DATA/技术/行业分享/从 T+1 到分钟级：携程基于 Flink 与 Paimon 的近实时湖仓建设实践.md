---
title: "从 T+1 到分钟级：携程基于 Flink 与 Paimon 的近实时湖仓建设实践"
source: "https://zhuanlan.zhihu.com/p/1976285415536358895"
author:
  - "[[携程技术]]"
published:
created: 2026-07-18
description: "导读： 随着携程业务的快速全球化扩张，携程传统 T+1 数据时效的离线数仓已无法满足日益增长的准实时分析决策需求。为解决 Lambda 架构下开发运维成本高昂、链路割裂、时效性不足等核心痛点，我们设计并实践了一套…"
tags:
  - "clippings"
---
**导读** ： 随着携程业务的快速全球化扩张，携程传统 T+1 数据时效的离线数仓已无法满足日益增长的准实时分析决策需求。为解决 [Lambda 架构](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Lambda+%E6%9E%B6%E6%9E%84&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJMYW1iZGEg5p625p6EIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.8_QmOMKOHRGIvdNuDjyDR2T5MyfzXCEbYYny-548j_U&zhida_source=entity) 下开发运维成本高昂、链路割裂、时效性不足等核心痛点，我们设计并实践了一套以 [Flink CDC](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Flink+CDC&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJGbGluayBDREMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.W4-hCVbiIZluNg4e50jeYHOTZRKXxtUgtl9RES3ZqoI&zhida_source=entity) 与 [Apache Paimon](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Apache+Paimon&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJBcGFjaGUgUGFpbW9uIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.Tl4nmM-LkINStobjSm6BC4thuCMl8vZqTm7rEYZf_2Y&zhida_source=entity) 为核心的近实时湖仓一体化解决方案。

本文首先阐述了该方案的整体 [架构设计](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%9E%B6%E6%9E%84%E8%AE%BE%E8%AE%A1&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmnrbmnoTorr7orqEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.7BNWhL7iNPe3nIlvSjR2A2ceqchL6nQSx-1nBu6pt9o&zhida_source=entity) ，重点介绍了为满足生产环境约束而构建的两阶段 CDC 数据入湖机制，并详细阐述了如何通过 [性能优化](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%80%A7%E8%83%BD%E4%BC%98%E5%8C%96&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmgKfog73kvJjljJYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.1vcBfPgqsg_P9aTptFDZJJh70gtq002h091gIBijSmk&zhida_source=entity) 、动态更新和引擎改造等一系列实践，攻克了生产环境中的关键挑战。最终，通过在国际化营销、广告归因等场景的应用，方案实现了端到端分钟级延迟，验证了其在 [降本增效](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E9%99%8D%E6%9C%AC%E5%A2%9E%E6%95%88&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLpmY3mnKzlop7mlYgiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.iXlA-hj7WJv4IKuwP5z2r_Z1XVpXgOisW2YrrOWa9cY&zhida_source=entity) 和驱动业务敏捷决策上的显著价值。

- 一、引言
- 二、架构设计：构建基于Flink和Paimon的近实时湖仓
- 2.1 近实时系统架构
- 2.2 [ODS](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=ODS&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJPRFMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.8_f-mf5AdRmH1N9FT_7avyr6PDyjHIau6cqwDZ5j0s4&zhida_source=entity) 层数据入湖
- 2.3 增量计算
- 三、应用实践：核心业务的价值实现
- 3.1 业务A：跨时区业绩数据的准实时统一化方案
- 3.2 业务B：准实时聚合驱动的营销决策看板
- 3.3 业务C：订单分钟级准实时归因
- 四、成果总结
- 五、未来规划

**一、引言：从 T+1 到分钟级，数据有效性的挑战和机遇**

携程原有数据体系已构建了成熟的离线批处理链路，能够支撑大部分 T+1（天级）或 T+1H（小时级）的数据分析场景。然而，随着业务的持续增长与精细化运营的需求，数据新鲜度与 [计算成本](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E8%AE%A1%E7%AE%97%E6%88%90%E6%9C%AC&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLorqHnrpfmiJDmnKwiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.VcniQEsNa8U2y6UKBrC1nF1RXhkl9QkxSNZOjLlnsfA&zhida_source=entity) 之间的矛盾日益凸显。

- **传统离线数仓** ：虽具备成熟生态与成本优势，但其核心瓶颈在于时效性低。
- **纯 [实时计算](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%AE%9E%E6%97%B6%E8%AE%A1%E7%AE%97&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlrp7ml7borqHnrpciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.ZHtaA7_2ugKwUPfMtWxsEJNFXduY8-zLz-q7AomEAFo&zhida_source=entity)** ：虽能实现秒级延迟，但在处理大规模数据时，面临状态 [管理成本](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E7%AE%A1%E7%90%86%E6%88%90%E6%9C%AC&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLnrqHnkIbmiJDmnKwiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.lDlPOU0IHlAW2NiRPYaXWhawlxM8F3xtCnHTF_nTVOA&zhida_source=entity) 高昂、消息中间件存储开销巨大等问题，导致总成本显著增加。
- **Lambda 架构** ：因实时与 [离线链路](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E7%A6%BB%E7%BA%BF%E9%93%BE%E8%B7%AF&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLnprvnur_pk77ot68iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.lxPkfg6dMwDUWgcJQPyz-E00d3tITwEp4_ZqrPNG80Q&zhida_source=entity) 物理割裂，在面对 [融合分析](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E8%9E%8D%E5%90%88%E5%88%86%E6%9E%90&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLono3lkIjliIbmnpAiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.a2HM53h097Wt1Ez_o9PtrC-u8S3YOCO23J3Pb18yrhU&zhida_source=entity) 需求时，往往需要双团队协同开发，涉及大量数据口径对齐工作，造成高昂的人力协调成本，阻碍了业务敏捷响应。

为应对上述挑战，业务亟需一个 **低门槛、低成本、端到端具备分钟级延迟** （目标 5-30 分钟）的流批一体数据解决方案。该方案旨在统一 [数据处理](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E5%A4%84%E7%90%86&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7lpITnkIYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.vMLIImbvIPYfSDBKo1pwLNx1RfGWyrHbD5pGr_IVlsg&zhida_source=entity) 链路，显著提升端到端时效性，同时降低开发、运维负担与总体运行成本。为此，我们选择了 Flink + Paimon 的技术栈，并设计了一套创新的数据入湖架构来解决数据同步与数据应用，旨在从根源上解决这些挑战。

**二、 架构设计：构建基于 Flink 和 Paimon 的近实时湖仓**

**2.1 近实时系统架构**

为实现上述目标，我们构建了如图 1 所示的近实时数据处理架构。该架构以 Flink作为核心 [计算引擎](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E8%AE%A1%E7%AE%97%E5%BC%95%E6%93%8E&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLorqHnrpflvJXmk44iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.vvsT69zyreNd_5G5h26euDGUHIreUoIGyOj9cvek7EY&zhida_source=entity) ， Paimon 作为湖仓存储底座。数据通过 Flink CDC 从 MySQL 等业务数据库捕获变更 [数据流](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E6%B5%81&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7mtYEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.5j1Ct3vlK-GB48hs-0519biApGX6tGNaSqIVonZQ7nw&zhida_source=entity) ，实时写入 ODS 层的 Paimon 表中。下游应用可根据需求，选择多种消费与分析路径：

- **实时/准实时 [ETL](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=ETL&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJFVEwiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.wpkDJ1Y69LQbBMgxmTuDCOqvzcJl_FFKRM9JNcUpp1I&zhida_source=entity)** ：通过 Flink 作业持续消费上游 Paimon 表的增量数据，进行实时流式处理。
- **高速 [OLAP](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=OLAP&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJPTEFQIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.DxubCDJeDO1p3u9xajEHU8Hq3zgJz6Vm7-FyvGMNWCQ&zhida_source=entity) 查询** ：将计算结果物化或直接接入 [StarRocks](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=StarRocks&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJTdGFyUm9ja3MiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.SkJ514eoXf7zAsdpTtyjdtBkx1DTKY5s_V2cBt6RqZU&zhida_source=entity) ，满足高性能、交互式的分析查询需求。
- **灵活的 [Ad-hoc](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Ad-hoc&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJBZC1ob2MiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.VpRoI958HIkf_eelNqk8qhIAClzaxNy9fNBcPRXPVT0&zhida_source=entity) 查询与离线分析** ：借助 [Trino](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Trino&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJUcmlubyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.HRtj52h76uTJuf1pwxVOE0w49xmOJyeb3yFRMh0aLx0&zhida_source=entity) 或 Apache [Spark](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Spark&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJTcGFyayIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.py9Zur4m0M58GsQVD7dLBT_dsrO6nwDrHhwcseS_Zfk&zhida_source=entity) 引擎，对湖内数据进行灵活的即席查询与大规模批处理分析。

通过该架构，我们为不同业务方提供了统一、多样的近实时数据服务，实现了计算与存储的高效协同。

![](https://pic3.zhimg.com/v2-47763a364200beb92871fd686c71c60a_1440w.jpg)

图 1：系统架构图

**2.2 ODS 层数据入湖**

在技术选型上，我们选择 Paimon 作为核心存储底座，主要基于其与 Flink 生态的深度原生集成、灵活的 Merge Engine 机制（如 partial-update、aggregation）以及 [LSM 树](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=LSM+%E6%A0%91&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJMU00g5qCRIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.yjsiZFxPE92YYzedIK3k5zoeuhbLk5SYvX7KuA0yjic&zhida_source=entity) 结构的存储模型。相比 [Hudi](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Hudi&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJIdWRpIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.x1lM6tZbMPwkWbbw7tvgpkSfaZbPPPb696a_dlQoQIQ&zhida_source=entity) 或 [Iceberg](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Iceberg&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJJY2ViZXJnIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.z1RTEA9lI70onW9oWQhkPOn38vUNN52WxP6BVszsoKA&zhida_source=entity) ，Paimon 在我们的 Upsert 密集型场景中展现了更优的写入性能和更低的维护成本，有力支撑了近实时 [湖仓](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=5&q=%E6%B9%96%E4%BB%93&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmuZbku5MiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6NSwiemRfdG9rZW4iOm51bGx9.B5ofxr-NY3u-KQQ70IEgqpFwmO7Was91lJI6HpiKN9I&zhida_source=entity) 的构建。

**2.2.1 两阶段 CDC 入湖架构设计**

携程大量业务 [数据存储](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E5%AD%98%E5%82%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7lrZjlgqgiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.22gYCjVI-DHpsab8NGvJOk4kztV-EQLJKRgBtsNipnU&zhida_source=entity) 于 MySQL 中，其线上部署遵循 master-slave-slavedr 模式。为了保障线上数据库的稳定性，我们对同步任务有一些限制策略：

- **读取节点限制** ：数据同步任务只能从 Slave 节点读取数据。
- **[Binlog](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Binlog&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJCaW5sb2ciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.K8NH-bbUvbYZHloN3wraFhR0zXdgQRExoLP7CUoTDHI&zhida_source=entity) 读取限制** ：每个 MySQL 物理实例（Instance）仅允许一个线程读取其 binlog，以避免并发读取对 binlog 归档产生干扰。
- **连接数限制** ：单个账户对数据库的最大 [连接数](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=2&q=%E8%BF%9E%E6%8E%A5%E6%95%B0&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLov57mjqXmlbAiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MiwiemRfdG9rZW4iOm51bGx9.ErNRAkJF284qNN_8aSleRkOrLTJwXY3zqxvZfs8GKhU&zhida_source=entity) 受限（不超过 40）。

上述单实例单线程读取 binlog 的约束，是催生我们设计“共享 Source，独立 Sink”两阶段 CDC 架构的根本原因。若为每个用户的同步任务单独启动一个完整的 CDC 作业，将占用实例的唯一 binlog 读取进程。因此，我们设计的 CDC 同步流程（如图 2 所示）分为两个独立的阶段：

![](https://picx.zhimg.com/v2-1784a30baa414908562ceff9be595ec7_1440w.jpg)

图 2：cdc 同步流程图

我们将 CDC 同步 Flink 任务主要分为两大类：

**第一阶段（source 任务）：** 由平台统一管理的共享 Flink 作业。该任务负责从指定 MySQL 实例读取 [binlog](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=5&q=binlog&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJiaW5sb2ciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6NSwiemRfdG9rZW4iOm51bGx9.VbgbYZAXnNNhzYjbqoeZaPRCZPZ8481M3pq6NoA-oyk&zhida_source=entity) ，并将增量数据分发至 Kafka。此任务对普通用户透明且不可操作，确保了对核心 DB 资源的合规、高效复用。

**第二阶段（sink 任务）：** 由用户自行管理的 Flink 作业。该任务从 Kafka [消费数据](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%B6%88%E8%B4%B9%E6%95%B0%E6%8D%AE&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmtojotLnmlbDmja4iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.IavgdjQzsmkO8Lyx-gM1p5dWLOmTr2L18M6jGtENjRE&zhida_source=entity) ，并写入目标 Paimon 表。用户可对此任务进行启停、配置等操作。

该架构支持 [单库单表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%8D%95%E5%BA%93%E5%8D%95%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLljZXlupPljZXooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.ZmbJ5Ila6SvxJtBYYwIg7ZItmvHPIjDGXrWWA9GEA_8&zhida_source=entity) 、单库分表、 [分库分表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%88%86%E5%BA%93%E5%88%86%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLliIblupPliIbooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.5-s6hVXoazbrsPFrs5XQr-hukQuOWSSw-FrmjDCzC6U&zhida_source=entity) 等多种同步模式，并通过平台化的管理，实现了对复杂 DB 环境的有效适配。Sink 任务支持多种运行模式：

- **全量+增量一体化模式：** 首次启动时，作业自动执行全量数据快照同步，完成后无缝切换至 Kafka 的指定位点，开始消费增量数据。
- **纯增量模式：** 仅对增量数据感兴趣的场景，作业直接从 Kafka 消费。
- **数据回补模式：** 用于异常恢复，本质是带过滤条件的全量+增量一体化同步。

**2.2.2 生产实践优化与挑战**

**1） [同步链路](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%90%8C%E6%AD%A5%E9%93%BE%E8%B7%AF&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlkIzmraXpk77ot68iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.gAY1iXMg2MszVnUJUVFiM9Vdj0T-8LmUSjnKKe0wRB0&zhida_source=entity) 性能优化**

**挑战：** 我们的一阶段任务是将 binlog 的增量数据同步至 Kafka，在最初上线的时候我们发现同步的速率较慢， 延迟较高，无法满足分钟级别的需求。

**分析：** 分析发现主要有以下两点原因：

- **单线程反序列化：** 从 MySQL 拉取数据后的反序列化操作在 Flink CDC Source 算子内部是单线程执行的。
- **单线程写入 Kafka：** 由于 Source 算子与 Kafka Sink 算子默认 chain 在一起，导致写入 Kafka 的操作亦为单线程，成为主要瓶颈。

如下图 3 所示，即使你设置了 [并行度](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%B9%B6%E8%A1%8C%E5%BA%A6&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlubbooYzluqYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Cdu5XlaJqOw6QFcu-_njkC20p9zW6m2gPxUXfodtw_M&zhida_source=entity) 为 16， 实际的工作线程其实为 1。 这个环节存在较大的 [性能瓶颈](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%80%A7%E8%83%BD%E7%93%B6%E9%A2%88&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmgKfog73nk7bpoogiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.PMJerwXQl_oYbnZ70f40EmlU4e6o7qZcEBqozonF7VE&zhida_source=entity) 。

**解法：** 为了优化这个问题， 我们在 [反序列化](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=3&q=%E5%8F%8D%E5%BA%8F%E5%88%97%E5%8C%96&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlj43luo_liJfljJYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MywiemRfdG9rZW4iOm51bGx9.8Frbz70T-s7cuz_pp33mwk-JdZV0Dn4fpMPnSDF-U6Q&zhida_source=entity) 环节增加了埋点。通过数据分析，发现耗时更高的实际上是单线程写 Kafka 这一块，因此后面我们通过 db.table.primary\_key 作为 Kafka key 来进行数据分发，这样只需要做到主键之间的数据有序即可。这样可以将解析 binlog 和写 Kafka 进行解耦， 如下图 1 所示。通过这种方式，数据处理 [吞吐量](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%90%9E%E5%90%90%E9%87%8F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlkJ7lkJDph48iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.v2Mv9jMQ4k7V0_sKkT5OZG29oPyTAnhWQBAWGWwVnpM&zhida_source=entity) 提升了近 10 倍。

![](https://pic1.zhimg.com/v2-4216e83c342cb849f57e29fd2308a864_1440w.jpg)

图 3：Flink Source 任务优化前后拓扑对比

**2）稳定性保障，支持数据回补**

**挑战：** 数据可能因为作业异常而丢失， 如果每次出错都需要全量回刷成本较高，必须具备可靠的数据回补（补数）机制。

**分析：** 数据回补机制是保障数据质量的关键环节。我们探讨了两种方案，如图 4 所示：

**方案一：基于归档的 binlog 文件回放** ，优点在于可以完整还原增删改操作，不依赖 [业务表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E4%B8%9A%E5%8A%A1%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLkuJrliqHooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.z1fAbAjTI2QYxWje0c4EC39yp7CdWQTPG6S13EXGPg4&zhida_source=entity) 结构；但这种方式依赖公司 [数据库管理员](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E5%BA%93%E7%AE%A1%E7%90%86%E5%91%98&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7lupPnrqHnkIblkZgiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.n9LDE_L0WNz_hIqwhSB0l6IHCsdLtnkU-wBhYdqC6LE&zhida_source=entity) （DBA）的支持。另外，由于公司不同的数据库可能部署在同一台物理机上，可能存在越权访问非目标 DB 的问题。

**方案二：基于 [时间戳](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%97%B6%E9%97%B4%E6%88%B3&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLml7bpl7TmiLMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.ODXrw8XDZrXfLRiVZ2oWK9VhF6GR9g2H3RyeVj733-w&zhida_source=entity) 字段回溯** ，依赖业务表中的 DataLastChange\_time 等更新时间字段，通过筛选时间范围来拉取数据。优点是实现简单、依赖少。缺点是无法还原 [物理删除](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E7%89%A9%E7%90%86%E5%88%A0%E9%99%A4&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLniannkIbliKDpmaQiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.fB8vudPgnainOmxWC63PBrMWUzsd44PJhEsEwi50eu4&zhida_source=entity) 操作，且强依赖表结构和时间字段的可靠性。

![](https://picx.zhimg.com/v2-86f8e1ba53c7335e481be1e0d49bcde3_1440w.jpg)

图 4：数据回补链路示意图

鉴于携程数据库 MySQL binlog 中涉及到了大量的线上数据，基于安全考虑无法重放，因此我们主要采用的是第二种方案。用户可在平台上配置起始时间，一键启动 Sink 任务。此模式下，作业会先拉取指定时间范围的历史数据，完成后自动切换到 [增量消费](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%A2%9E%E9%87%8F%E6%B6%88%E8%B4%B9&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlop7ph4_mtojotLkiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.iP_fZ4l89TK97k7BW73dLlrzHSF0WXefX1zmThl2GSA&zhida_source=entity) 模式。

![](https://pic2.zhimg.com/v2-7e01121410d9e5bcce423909b190eff5_1440w.jpg)

图 5：数据同步流程示意图

**解法：** 我们开发了带有时间戳过滤的 [全增量](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%85%A8%E5%A2%9E%E9%87%8F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlhajlop7ph48iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.oml60x_7cgTe5CSJDxEJh5kXsODvGm3ttPmdiJpx-eI&zhida_source=entity) 一体的补数方案， 如图 5 所示。用户可以通过配置，可以进行一键补数。其核心是带有时间戳过滤的全增量一体同步。但是这个方案存在一个局限：就是会导致 MySQL 一些被删除的数据无法同步到 Paimon 中删除。即在异常期间， [源端数据库](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%BA%90%E7%AB%AF%E6%95%B0%E6%8D%AE%E5%BA%93&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmupDnq6_mlbDmja7lupMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.s5YDr_u58X8XgfjWTR_3h5RGhafzb_Eb5g7mKrBL0Bs&zhida_source=entity) 已删除的数据，其删除操作未能同步到 Paimon，导致这些数据在 Paimon 中仍然存在。

另外，由于有一些作业存在特殊的逻辑，因此我们也开发了一些接口给用户进行特殊补数。特殊补数可以通过用户指定 [sql](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=sql&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJzcWwiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Pgu7ErFNMzqw-ZxLZA9KRce_LUJ3J4LL0mvtc2Z2U6k&zhida_source=entity) 条件来进行补数。例如，线上有些 [逻辑删除](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E9%80%BB%E8%BE%91%E5%88%A0%E9%99%A4&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLpgLvovpHliKDpmaQiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.LzN4TfK_4lDdi1qqVkFidCkhX0tywGaLvAoOjYOtZbU&zhida_source=entity) 是通过将表中的 时间戳指定到一个特殊的年份来表示删除，对于这些逻辑删除的数据，如果用户在补数时不希望同步它们，可以指定如下过滤条件：--data\_backfill\_condition [mysql](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=mysql&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJteXNxbCIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.nosq01F4UrkuB-DghANWtNZdjWaDpqQysFtOoLOSCRQ&zhida_source=entity) \_db.mysql\_table=not createtime<=>'2000-01-01'。支持补数的前提是因为我们的 Paimon 都是 [主键表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E4%B8%BB%E9%94%AE%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLkuLvplK7ooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.U5In4mzzXQzS5Oks1b7GGzj0-FTqr5GyQ1gCQHfXBys&zhida_source=entity) ，同步数据的操作是幂等操作。所以不会有数据的丢失。无论是基于时间戳的补数，还是带有条件的特殊补数，cdc 二阶段的作业都会在补数完成之后自动切换到增量消费的模式。

**新的挑战：** 补数模式随之引入新麻烦，作业切完增量重启后无法从 Checkpoint 恢复。补数参数会影响 [Hybrid Source](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Hybrid+Source&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJIeWJyaWQgU291cmNlIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.W3dyuYJxcUfDjIRvpcoQJKBqWPUhPxtzTD5i7jyBZv0&zhida_source=entity) 中 Source 的数量。一旦补数完成、作业切换到增量消费模式后，若此时重启作业，就会因为 Source 结构不一致导致无法从 [checkpoint](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=checkpoint&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJjaGVja3BvaW50IiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.CJRkQTLpURSeAeHenIkxB6PFL3I1W0iq7ichg4Z3YiU&zhida_source=entity) 正常恢复（即 Source State 无法恢复）。

**新的解法：** 为了解决这一问题，我们在 [flink](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=flink&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJmbGluayIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.QeTI574bjZ9XkWo2LwN89VRJ1pZ_BANktei5pgk8jFs&zhida_source=entity) 引擎侧新增了一个配置项，允许 Flink 在恢复时直接从 Hybrid Source 中的最后一个 Kafka Source 启动。这样一来，无论是补数模式还是 [增量模式](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=2&q=%E5%A2%9E%E9%87%8F%E6%A8%A1%E5%BC%8F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlop7ph4_mqKHlvI8iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MiwiemRfdG9rZW4iOm51bGx9.IwAq3mfL06bfQCcUf9Rln7UgtDyOil6lulAb5xocWEg&zhida_source=entity) ，作业都能平滑切换，彻底解决了两种模式下的 checkpoint 兼容问题。

**3）提升效率，平台更好用**

**挑战：** 当链路稳定运行之后，为实现平台化，我们面临一个问题：每当有新用户需要同步新表时，都必须重启共享的 Source 任务，这会引发下游所有消费任务的抖动。最初，我们尝试同步一个 database 下的所有表，但很快发现这会向 Kafka 写入大量非必要数据，且非目标表的批量操作（业务如凌晨刷数、归档等）会导致 binlog 暴增。

**解法：** 为解决此问题，我们开发了 table-name 参数的热更新功能， 如图 6 所示。Source 任务仅同步用户明确指定的表。当有新的同步链路加入时，数据平台通过向 JobManager 发送请求，将新表名动态传递给运行中的 Source 算子。 [算子](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=5&q=%E7%AE%97%E5%AD%90&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLnrpflrZAiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6NSwiemRfdG9rZW4iOm51bGx9.L1rU6W495Ip8hkjcHbsGNtad8vCY3eJw6EF8V1nmS9I&zhida_source=entity) 接收到新参数后，无需重启作业即可开始监听新表。该功能极大地减少了写入 Kafka 的数据量，并避免了因任务重启给下游带来的抖动。

![](https://pic3.zhimg.com/v2-cb5c533c18c9df5b7379f485dd733a4c_1440w.jpg)

图 6：Flink Source 作业热更新机制

**新挑战：** 对于数据量巨大或存在批量操作的源表，所有数据汇入单一 Kafka Topic，下游多个作业同时消费同一个 Topic，会导致 Topic 流量过载（峰值可达数十 GB/s），可能耗尽特定 Broker 节点的 [网络带宽](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E7%BD%91%E7%BB%9C%E5%B8%A6%E5%AE%BD&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLnvZHnu5zluKblrr0iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.1Mhc4LLmP0bQgqgNnUhBeDo4GXrLxk205L-6YvBVetw&zhida_source=entity) ，影响整个 Kafka 集群的稳定性。

**最终解法：** 我们实现了 Topic 分流功能。用户可通过配置 [路由表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E8%B7%AF%E7%94%B1%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLot6_nlLHooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Qh0jGa2X0lm-tbc0YI9BLJmDbd-IoojHgwTvzY6NeZM&zhida_source=entity) ，将不同表的数据自动路由到不同的 Topic 中，下游 Sink 任务再根据路由信息消费对应 Topic，有效分散了流量压力。

**4）引擎侧优化**

**a）Paimon bit 字段类型转化优化**

在实际生产实践中，根据不同的问题对引擎侧做了一些优化。比如，我们发现在某些场景下，Paimon 对于 float 小数转化存在错误。以及业务方需要基于 bit 类型转化为 boolean（此功能后面在社区已经支持）。

**b） Paimon schema 缓存优化**

另外在分库分表同步中，作业启动的时候，每一个 flink subtask 对于每一张表都需要对 Paimon 中进行 schema 验证。如图 7 所示，process 算子实际上是做 schema 变更的。在启动初始化时收到了 1024 条数据。这一步通过 [HDFS](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=HDFS&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJIREZTIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjY2Nzc1NzAxLCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.EjLM2kMMHVg-PtTQYZQ2BCTy0Pyfn8F-d-98d_k0SWc&zhida_source=entity) 来获取 schema 文件速度较慢，会降低 flink 作业从 checkpoint 恢复速度，甚至会导致 checkpoint 失败。因此我们开发了基于时间的 schema 缓存机制，在启动时获取一次 Paimon 的 schema 之后会缓存一分钟。这大大缩短了作业启动耗时。

![](https://picx.zhimg.com/v2-2f5fe3e83368dca61872ad4ffd0813a7_1440w.jpg)

图 7: Fink sink 任务 Paimon schema 缓存

**c） Flink Hybrid Source 快速切换**

我们的全量同步和补数都是基于 Hybrid Source 来实现全量和增量自动切换的。在原生的 cdc 同步过程中为了保障 exactly once 语义，在读取 MySQL snapshot 的时候会进行 binlog 数据的 merge。我们开启了 scan.incremental.snapshot.backfill.skip 参数，加快了读取速度。这样处理虽提高了读取速度，但整个链路仅能保障 At-Least-Once 语义。

另外我们支持了 only-snapshot 模式。这是因为，在某些分库分表的场景下，我们遇到过 Hybrid source 中存在 180 个 source（批模式），这些 source 之间的切换是依赖一个 checkpoint 完成的。因此有时候可能补数本身运行时间是比较短的，大部分时间在等待 checkpoint 完成。此模式可以不必等待 checkpoint 完成，大大提高了补数的效率。

**d）Paimon Bucket 动态步长**

Paimon 主键表的 bucket 数是一个比较重要的配置 ，Paimon 社区对于 bucket 数推荐是 每个 bucket 大约 200MB - 1GB 数据量。生产中我们发现 dynamic bucket 对于大量的数据而言，写入性能不如 fixed bucket。某些场景下，我们支持了固定步长的 bucket 模式。支持业务方可以通过配置，比如根据数据大小，每增长 100 万条数据增加一个 bucket。

**5） [全链路监控](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%85%A8%E9%93%BE%E8%B7%AF%E7%9B%91%E6%8E%A7&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlhajpk77ot6_nm5HmjqciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.j7TMKJfGINvxf3vnJnspYyuLI-EmdqsPuPpyKpEdD9k&zhida_source=entity)**

我们建立了覆盖全链路的表级别监控体系。通过内置的批流切换事件通知， 如图 8 所示，用户可以清晰地了解作业当前状态（全量/增量/回补）。从 MySQL 到 Kafka，再到 Paimon，数据流在各环节的出入口均增加了表级别的指标埋点，用户可基于这些指标配置数据断流、延迟等告警，实现了精细化的 [可观测性](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%8F%AF%E8%A7%82%E6%B5%8B%E6%80%A7&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlj6_op4LmtYvmgKciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.VqhDq_5ues1KQogKNQa1akNjg_0uYpwaVgUm8aN5yQE&zhida_source=entity) （图 9-图 10）。

![](https://picx.zhimg.com/v2-af7ed16eb1a8fa40a1b89817d1f809b7_1440w.jpg)

图 8：source 任务状态监控

![](https://pic4.zhimg.com/v2-2f7c72890949718c8dbb54a644dc3c69_1440w.jpg)

图 9：表级别 MySQL 增量同步 Kafka 监控

![](https://pic3.zhimg.com/v2-3004a16a6d6642791e578bc35bf6d71e_1440w.jpg)

图 10：表级别同步至 Paimon 数据监控

**2.3 增量计算**

数据入湖后，我们提供了多种增量计算方式。除了使用 Flink 持续消费外，还打通了 Spark 和 Trino 对 Paimon 表的增量读取能力，实现了“ [批流一体](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%89%B9%E6%B5%81%E4%B8%80%E4%BD%93&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmibnmtYHkuIDkvZMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.SmrcsISEpdQB1c5gju154oiwCYwyOaprrVMPZAlMS38&zhida_source=entity) ”的计算模式。

![](https://pic4.zhimg.com/v2-fb8a8c03913ff478271a81b0c0862781_1440w.jpg)

图 11：增量计算流程图

目前，除了已有的 Flink 和 Spark 支持增量消费之外，我们已全面支持 Trino 对 Paimon 的读写、增量读取及 Compact 操作。通过这一能力，Trino 可以无缝访问 Paimon 存储中的实时与历史数据，支持 [高并发](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E9%AB%98%E5%B9%B6%E5%8F%91&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLpq5jlubblj5EiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.3hVQrjVXE_2CglmuUg9o1FGZMyDQywm6F94YlciKVLk&zhida_source=entity) 、低延迟的分析查询。与此同时，Paimon 的高效 [数据管理](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7nrqHnkIYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.2BAcLInpRDYWb-LOc-kFFYjmBZom2Vr3yG-RXwj7hAs&zhida_source=entity) 和增量更新机制，也为 Trino 提供了更加轻量、实时的 [数据源](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E6%BA%90&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7mupAiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.CJJ_xObcMcMBXU8zQVpdtuvTIaWetwfSSU9TSN2zlI0&zhida_source=entity) 。

两者的深度融合有效提升了查询性能与数据一致性，实现了计算与存储的高效协同，进一步完善了湖仓一体的生态体系，为用户带来更灵活、更高效的数据分析体验， 如图 11 所示。另外，我们在 trino 中支持了对 hive udf 的复用，这样可以降低用户的迁移成本。在 trino 支持读取 Paimon 的过程中需要注意以下几点：

- **数据分发策略的一致性**  
	在使用固定分桶（Fixed Bucket）模式时，Trino 侧的数据分发策略必须与 Paimon Writer 内部的分发策略保持严格一致。两者若出现不一致，会导致数据写入错误的 Bucket，进而引发数据正确性问题和查询结果异常。因此在实现时需要确保双方使用相同的 [哈希算法](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%93%88%E5%B8%8C%E7%AE%97%E6%B3%95&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlk4jluIznrpfms5UiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.5ZfppBTSnN_46IBKWMMH5RCR7gUfELRt0RRzP80fvcc&zhida_source=entity) 和分桶逻辑。
- **BucketFunction 并发安全**  
	数据分发的核心实现是 BucketFunction 类。需要特别注意的是，该类的实例会在多个线程之间共享使用，因此必须保证其 [线程安全性](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E7%BA%BF%E7%A8%8B%E5%AE%89%E5%85%A8%E6%80%A7&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLnur_nqIvlronlhajmgKciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.6Wu3yxcuQ1ynbG5H9PfMgmqCFkFJAbp-7M52PdAKlWg&zhida_source=entity) 。在实现时应避免使用可变的 [实例变量](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%AE%9E%E4%BE%8B%E5%8F%98%E9%87%8F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlrp7kvovlj5jph48iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.LhFF6dJ88hGAopFQAWt-46eJDuob6jEbbhxpL1mjaco&zhida_source=entity) ，或通过适当的 [同步机制](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%90%8C%E6%AD%A5%E6%9C%BA%E5%88%B6&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlkIzmraXmnLrliLYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.t4Jv8nwnVzMPR9PXFw3oS3FLcJPWlTTvgO2JWnMg1wI&zhida_source=entity) 来防止并发访问导致的数据竞争问题。
- **Catalog [Schema](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Schema&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJTY2hlbWEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.un7tcRdFXbDBHRG57PDStX2inTrziFcC4hFuMxP9fyY&zhida_source=entity) 获取优化**  
	在原生实现中，Catalog 逻辑存在一个隐患： [Coordinator](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=Coordinator&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJDb29yZGluYXRvciIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.0U-MeckO4AF7CpLIqSkvZT_ZbmyJ9njP5_Z8MNli-Us&zhida_source=entity) 和 Worker 节点会并发地拉取同一张表的 Schema 信息。当查询 [执行时间](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%89%A7%E8%A1%8C%E6%97%B6%E9%97%B4&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmiafooYzml7bpl7QiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.qYSKNfVJaFr1N_UWxdBxla4qNe82P1u_smAvXTbMeg8&zhida_source=entity) 较长且期间发生了 Schema 变更时，各节点获取到的 Schema 可能不一致，导致查询失败或结果错误。我们已将此逻辑优化为：由 Coordinator 统一拉取 Schema 后分发给各 Worker 节点，确保全局 Schema 一致性。但由于涉及 FileSystem 对象的序列化问题目前的实现方案在代码层面不够优雅，后续可考虑引入更优雅的 Schema 传递机制进行重构。

采用增量计算引擎，在大幅提升数据处理速度（尤其在变更频繁场景）的同时，显著降低全量计算资源消耗，优化整体计算成本。

**三、 应用实践：核心业务的价值实现**

**3.1 业务 A ：跨时区业绩数据的准实时统一化方案**

当前业务 A 国际业务已覆盖多个区域，其中国际业绩数据是公司众多 [业务线](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E4%B8%9A%E5%8A%A1%E7%BA%BF&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLkuJrliqHnur8iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.d5NtQYCQykmMH6tdpErlHuNZ-Hk_VND7sz4rBPPrjwE&zhida_source=entity) 决策数据之一。在国际数据处理的业绩模块下，某些业务日期是按照统一时区进行统计和更新，主要基于离线业绩模型产生，其流程具有以下几个特点：

- 依赖多个外部 BU 数据源
- 从数据源到结果产出，整体任务层级多、离线任务众多， [数据清洗](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E6%B8%85%E6%B4%97&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7muIXmtJciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.moEaUUW7YHxZCNgHjVHxbOYxqFjgj-mh9SjBxOidZXw&zhida_source=entity) 和整合过程复杂，需要大量的计算资源和时间
- 未能全面进行模块化建设，各层之间的 [数据依赖](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E4%BE%9D%E8%B5%96&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7kvp3otZYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.UflaFKd7thainIzOj8osYypME52W0_gBlXqlE_LQVG4&zhida_source=entity) 关系复杂

**痛点：** 基于当前的架构可能会产生以下三种比较重大的问题：

- **统计日期窗口错位**  
	对于海外市场，业务日期窗口仍是按照北京时间来做时间窗口划分，统计每天的数据结果，这就导致非 UTC+8 时区所展示的预订业绩数据，部分取自当天的数据，另外一部分取自前天的数据，进而导致数据统计不准确。
- **数据更新时间标识混淆**  
	除统计数据外，目前数据的更新时间也是按照北京时间（UTC+8 时区）展示，对于所在时区排名比 UTC+8 靠后的业务数据，就可能会在所在时区仍在今天，但数据更新时间展示为明天的情况，造成商户误解。
- **数据产出时间不匹配工作时间**  
	该延迟是指，从业务视角来看，数据可见时间与当地工作时间不匹配。

**解决方案：** 解决上述问题的关键就是提升整体业绩流程的更新频率，通过更新加速，实现所有海外业务所在时区可以及时、准确看到业绩统计数据。最终海外业务采用了近实时湖仓的链路，其整体的链路如下所示：

![](https://pic4.zhimg.com/v2-352b4f41cd819d58571f592a145c3273_1440w.jpg)

图 12：业务 A 业绩数据架构图

我们采用 Flink CDC+Paimon+Trino/Spark 作为小时级数仓的技术底座，通过流式入湖和小时级调度，形成了从多源异构数据采集、分钟级入湖、分层存储管理到最终应用服务输出的全链路技术架构。

**价值：** 该架构产生了以下的价值

- 实现了数据分钟级延迟的入湖能力：通过 FlinkCDC 接入 MySQL 表的 Binlog，同时 Paimon 表格式支持 Update，并支持流式写入，分钟级数据合并，从而实现如下优点：
- 低延迟性：通过 CDC+Kafka，实现 MySQL 变化数据的实时获取和传输，基于 Paimon 的 ods 表延迟在 5 分钟以内（延迟时间可按需设置，最低可以设置 1 分钟）
	- 链路复杂度低：仅需运维一个实时作业，实现全增量一体的数据同步
	- 存储成本低：得益于湖格式的 Snapshot 管理，加上 LSM 的文件复用，大幅节省存储资源
- 聚合加速：依托 Paimon 表支持 PartialUpdate/Aggregation 等不同的 MergeEngine，减少 Join/Agg/Sort 等操作的消耗。
- 增量计算：通过 IncrementalQuery 机制，将全量计算转为增量，大幅减少每次计算的是数据量，减少数据 IO。Paimon 的增量计算能力，可以支持如下两点功能：
- 查询当前全量和历史版本的全量快照数据
	- 获取两个全量版本之间的增量数据
- 端到端提效：基于上述 3 项优势，最终实现业绩数据从 ODS 到 [ADM](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=ADM&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJBRE0iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.49zEvJPw9kuKPNVeGIi8EvjA_U2LboAZlMY9oSGzEPI&zhida_source=entity) 层的产出提效，在 1 小时内完成一个调度批次。

改造后整体的收益主要有以下两点：

- 效率提升：提升业绩汇总数据的更新频率和产出时间，保障海外业务和商户可以在工作时间尽早的关注到数据情况。
- 准确性保证：保障了海外单店可以按照所在地时区对日期进行筛选，获取符合海外商户认知的 T-1 日及更早数据。

**3.2 业务 B：准实时聚合驱动的营销决策看板**

业务 B 在 [全球化战略](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%85%A8%E7%90%83%E5%8C%96%E6%88%98%E7%95%A5&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlhajnkIPljJbmiJjnlaUiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.fss56d2YpXro1mGjyFZ7VFjdeBbU14-TSMsMcrIN23w&zhida_source=entity) 的背景下，一直在努力推进国际化战略部署。目前海外业务已经集中在英国、亚洲和欧洲各国。

**痛点：** 伴随着业务的发展，在实际的生产中存在以下的问题。

- 离线看板与营销侧对数据时效性有更高要求，如：供应商 [异常处理](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%BC%82%E5%B8%B8%E5%A4%84%E7%90%86&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlvILluLjlpITnkIYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.2wepgnkAwhUZWg7Nh0usP0zjo7R5GYq5p7vNCsnB1rw&zhida_source=entity) 批量退款，以及 [海外营销](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%B5%B7%E5%A4%96%E8%90%A5%E9%94%80&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmtbflpJbokKXplIAiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.sQfoAoZZ7l5uCfaLwXZfQADBAfENNfZMq4bczRiklhE&zhida_source=entity) 策略的调整，当前的数据新鲜度无法满足业务需求。
- 国际业务的员工分散世界各地，时差问题导致 T+1 天数据不符合海外员工的使用习惯。过往国际 T+1 小时票量统计，是通过与后端合作，由后端处理好部分逻辑，数仓再通过 [DataX](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=DataX&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJEYXRhWCIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI2Njc3NTcwMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.SG1rfiHWYRn9EO0lWpA62f3lA_bU0SooNvwvbZe9TPs&zhida_source=entity) 进行小时级同步，进行逻辑的二次处理。每小时的批量重复同步造成了计算资源的浪费，两边团队耦合的开发也降低了开发效率。

**解决方案：** 以业务 B 营销活动为例，改造完成之后的架构图如下所示：

![](https://pic3.zhimg.com/v2-1068264d16c5e7931340fdab99815554_1440w.jpg)

图 13：业务 B 营销看板架构图

**价值：** 其中业务 B 利用 Paimon 的 partial update 机制。可以避免 Flink 多流 Join 带来的多个问题：

- 避免了高昂的 Join 成本；
- 防止了因多流导致的 Checkpoint 状态过大及作业不稳定；
- 解决了因数据流到达时间差异大而无法关联的问题；

新架构支持销售监控、 [客流统计](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%AE%A2%E6%B5%81%E7%BB%9F%E8%AE%A1&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlrqLmtYHnu5_orqEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.yAcFBMl4tYTY70iwJG8EDfBdg7f7BwYQwrVoF2p_Pp4&zhida_source=entity) 、收入汇总等多维度实时分析场景。同时也支持增量查询机制，大幅提升查询性能。确保数据质量和系统稳定性。解决了因时差问题导致 T+1 数据不符合海外员工使用习惯的问题。延迟由天级降到了分钟级。同时也优化了之前加工链路较为复杂，难以维护的问题，使得运维效率得到了大幅提升。

**3.3 业务 C：订单分钟级准实时归因**

业务 C 聚焦于为企业客户提供一站式差旅服务，涵盖机票、酒店、用车、火车等多种场景。客户可通过该系统完成预订、审批、报销等完整流程，随着服务链条延伸、数据流转环节增多，数据量与复杂度持续增长。伴随业务成长及产品形态丰富，对数据时效性的要求也日益提高。过去的 “T+1” 离线数仓架构已无法满足对“准实时”数据分析的需求，而采用传统基于流式平台的实时数仓虽能处理部分实时计算场景，但其适用性受限，且其计算中间层难以直接用于分析。

在广告投放场景方面，涉及广告的曝光、点击与下单行为的准实时上报。下单行为需与用户近 3 日内的点击日志进行归因匹配，只有在下单前 3 日内存在有效点击行为的订单，方会上报给广告主。该订单上报流程对响应速度有一定要求，业务方希望实现从触发到上报端到端的分钟级时效。

**痛点：** 在实际落地过程中，面临以下挑战：

- 上报所需字段和逻辑在 [业务系统](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E4%B8%9A%E5%8A%A1%E7%B3%BB%E7%BB%9F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLkuJrliqHns7vnu58iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.OEY7nfk7wcrGdcUev1DOr4SeeznN2HV23CBhy5hCy84&zhida_source=entity) 中涉及 7 张 MySQL 表，实时多流 Join 实现难度和成本较大、稳定性挑战较大。
- 点击日志每日增量多，数据表膨胀速度较快，需有效 [控制表](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%8E%A7%E5%88%B6%E8%A1%A8&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmjqfliLbooagiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9._nCSmK8FhAR50tFxBMK4eu9CFVYTqntAhVzqQoxWjqo&zhida_source=entity) 存储，保障查询和 Join 性能。

如何高效整合多表数据、管理膨胀的点击日志表，并满足分钟级别的上报时效，是该场景下的核心业务痛点。

**解决方案** ：业务实际改造完之后整个链路如下：

![](https://pic4.zhimg.com/v2-15589b9e127d59ddc8e822c02aa8f22f_1440w.jpg)

图 14：广告订单归因准实时上报架构图

**价值：** 改造后，从最上游的 MySQL 数据到最终的结果归因，端到端时延在 8 分钟以内（还可通过调整 checkpoint 间隔进一步降低），下游业务方表示当前延迟在可接受范围内。和之前的整个离线计算逻辑相比， [数据延迟](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E5%BB%B6%E8%BF%9F&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7lu7bov58iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.y2l5UUsJid2M80tVYUiPF80pncYuEqpt1tMAMWmOqY0&zhida_source=entity) 降低了 8 倍，达到准实时的效果。

**四、成果总结**

携程近实时湖仓生产实践深度总结：面对数字化转型浪潮和业务对实时数据分析需求的急剧增长，携程从传统 [数据仓库](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%95%B0%E6%8D%AE%E4%BB%93%E5%BA%93&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmlbDmja7ku5PlupMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.hTHF23CnRM_1TPGZ7-zYIwvfcXHu_TThYzYtei6kGjs&zhida_source=entity) 的小时级延迟痛点出发，历经技术选型、架构设计、生产落地等关键阶段，成功构建了一套完整的近实时湖仓一体化解决方案。该方案以 Flink 作为 [流处理](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%B5%81%E5%A4%84%E7%90%86&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmtYHlpITnkIYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.pAqW4Axm34S4hL1KEOO9uafO54fSUCNKihg0AGl6Dfc&zhida_source=entity) 计算引擎，Paimon 作为湖仓存储底座，形成了从多源异构数据采集、实时 ETL 处理、分层存储管理到业务服务输出的全链路技术架构。

我们最终实现了：

- 数据新鲜度达到分钟级：采用全增量一体化处理模式，显著降低因传统离线全量与实时增量双链路并行带来的复杂性与维护成本。
- 端到端时效跃升： 端到端数据处理时效从天级提升至 5-30 分钟级，满足准实时分析需求。
- 主键更新赋能实时场景： 湖仓提供原生主键（Upsert）更新能力，有效支撑实时订单状态、用户画像更新、实时维表变更等需要行级更新的核心业务场景。
- 增量计算降本增效： 采用增量计算引擎，在大幅提升数据处理速度（尤其在变更频繁场景）的同时，显著降低全量计算资源消耗，优化整体计算成本。

**五、未来规划**

征途仍在继续。未来，我们将致力于：

- 构建分钟级 [SLA](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=SLA&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiJTTEEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.-6aTICNgP2ZiVgjLP1Z15icM_94FpQyzfUA-d2idvLg&zhida_source=entity) 保障体系： 建立覆盖全链路的、具备分钟级时效性保障能力的 SLA 机制，并配套完善的多级监控与告警体系，确保数据生产的 [高可靠性](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E9%AB%98%E5%8F%AF%E9%9D%A0%E6%80%A7&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLpq5jlj6_pnaDmgKciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.BTbfwzXcf5XDO--gTW3cOXpJvvTyoxAYhgSJUKbSnDE&zhida_source=entity) 与可观测性。
- 强化 Paimon 表治理能力： 深化 Paimon 表核心管理功能， [元数据治理](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%85%83%E6%95%B0%E6%8D%AE%E6%B2%BB%E7%90%86&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlhYPmlbDmja7msrvnkIYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.RQB0ZwTwyAhP7v5Z-qYlIVRB-v4NK0tctF3x4d3w9uk&zhida_source=entity) （如血缘、Schema 变更跟踪）及 [自动化](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E8%87%AA%E5%8A%A8%E5%8C%96&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLoh6rliqjljJYiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.l3SRf9aOubDtm2x_09ROUL3wJQwvygNyvltW0loVXhA&zhida_source=entity) 生命周期管理（如自动 Compaction、数据过期清理），提升表管理效率与数据质量，支撑高频更新等复杂场景。
- 推动准实时链路规模化落地： 持续扩大准实时湖仓架构在核心数仓场景的应用范围，沉淀并推广 [最佳实践](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLmnIDkvbPlrp7ot7UiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.0Fw8SXfwMAU1QoXxNvXniEno5hEVNbw6JNNqrdTv-XA&zhida_source=entity) ，实现技术价值向业务价值的高效转化与闭环。

**【作者简介】**

Hao Yu，携程资深 [大数据](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%A4%A7%E6%95%B0%E6%8D%AE&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLlpKfmlbDmja4iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.gVYfE_E-v6fO3Moj08-a395hIEM_0CMXMwTQDlKXvY8&zhida_source=entity) 平台开发工程师，关注实时计算、湖仓和大数据 [分布式计算](https://zhida.zhihu.com/search?content_id=266775701&content_type=Article&match_order=1&q=%E5%88%86%E5%B8%83%E5%BC%8F%E8%AE%A1%E7%AE%97&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODQ1MzIzNjcsInEiOiLliIbluIPlvI_orqHnrpciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNjY3NzU3MDEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.OBiWXHBiN8cIRV8tZSOmTbUSDcEpLDrichGNX8LfSME&zhida_source=entity) 等领域。

发布于 2025-11-24 22:00・上海

赞同 27