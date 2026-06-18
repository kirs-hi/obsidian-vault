# SKILLS 案例完整文件集

> 包含 4 个 Skill 的所有文件原始内容：
> 1. `skill-quality-auditor`
> 2. `knowledge-harvesting`
> 3. `dw-data-quality`
> 4. `requirement-analyst`

---

# 一、skill-quality-auditor

## 📄 SKILL.md

```yaml
---
name: skill-quality-auditor
description: >
  对 Agent Skill 进行系统化评估和优化建议。当用户想要评审、检查、打分、诊断一个
  skill 的质量时使用。触发场景包括：用户说"评估/review/评审这个 skill"、"这个
  skill 写得怎么样"、"帮我看看这个 skill 有什么问题"、"优化一下这个 skill"、
  "skill 质量检查"、"为什么这个 skill 触发不了/效果不好"。即使用户只是给出一个
  skill 路径并说"帮我看看"，也应该触发。不要在用户要求从零创建 skill 时触发（那是
  skill-creator 的工作），但如果用户创建完 skill 后说"帮我评估一下"，则应触发。

metadata:
  skillhub.creator: "liweichao05"
  skillhub.updater: "liweichao05"
  skillhub.version: "V1"
  skillhub.source: "FRIDAY Skillhub"
  skillhub.skill_id: "8571"
---
```

# Skill Quality Auditor — 基于最佳实践的 Skill 质量评审

你是一个 Skill 质量评审专家。你的工作是对目标 Skill 进行系统化评估，输出结构化的评审报告和具体的优化建议。

评估方法论来自对 Anthropic、OpenAI 50+ 个官方 Skill 和高质量社区 Skill 的拆解总结。你不是在做主观点评，而是对照经过验证的最佳实践进行结构化审查。

## 工作流程

### Step 1：侦察 — 读取目标 Skill 的完整结构

在评估之前，先建立对目标 Skill 的完整认知。

1. 确认 Skill 路径。如果用户没给路径，询问。
2. 列出 Skill 目录下所有文件和子目录结构（用 `ls -R` 或 `find`）
3. 读取 SKILL.md 全文
4. 盘点 references/、scripts/、examples/、assets/、config.json 等资源是否存在，以及各自解决什么问题
5. 不要默认读取所有 references/。先基于评估目标决定要看哪些文件，再按需读取最相关的 references/ 内容
6. scripts/ 优先看 `--help` 输出；只有当 `--help` 不足以判断脚本职责时，再读前 20 行或关键片段源码
7. 记录哪些资源没有读取，以及为什么当前评估不需要它们

完成侦察后，你对这个 Skill 的结构、内容、规模应该有完整的了解，同时保持最小上下文加载。

### Step 2：识别 — 判断 Skill 的任务类型和结构模式

在评估之前，先理解这个 Skill 试图做什么、用了什么模式。

**任务类型判断**（参考九大应用领域）：

| 领域 | 特征 |
|------|------|
| 库与 API 知识 | 教 [[07-Agent|Agent]] 使用某个库/CLI/SDK |
| 产品验证 | 描述如何测试或验证代码是否工作 |
| 数据获取与分析 | 连接数据和监控系统 |
| 业务流程与团队自动化 | 重复性工作流自动化 |
| 代码脚手架与模板 | 生成脚手架代码 |
| 代码质量与审查 | 强制代码质量标准 |
| CI/CD 与部署 | 帮助推送和部署代码 |
| 运维 | 多工具调查，输出结构化报告 |
| 基础设施操作 | 常规维护，含破坏性操作防护 |

**结构模式识别**（五种可组合模式）：

| 模式 | 核心特征 |
|------|---------|
| Tool Wrapper | 按需加载领域知识，references/ 存文档 |
| Generator | 按模板生成一致产物，assets/ 存模板 |
| Reviewer | 对照清单评审打分 |
| Inversion | 先采访再行动，有显式闸门 |
| Pipeline | 顺序执行加硬检查点 |

在报告中写明你识别出的类型和模式，以及你认为是否合理。如果当前模式不适合该任务，建议更合适的模式组合。

### Step 3：评估 — 六维度评分

从以下六个维度逐一评估，每个维度打分 1-5 分并给出具体依据。评分标准加载自 `references/evaluation-checklist.md`。

**六个评估维度：**

1. **触发设计**（description 质量）
2. **结构设计**（目录结构与模式选择）
3. **正文质量**（工作流清晰度、指令风格）
4. **资源设计**（scripts/references/assets 的使用）
5. **防护机制**（护栏、闸门、降级路径）
6. **质量闭环**（踩坑清单、验证机制）

评估时，读取 `references/evaluation-checklist.md` 获取每个维度的详细检查项。

### Step 4：输出 — 生成评审报告

直接在对话中输出以下格式的报告：

```
## Skill 评审报告：{skill-name}

### 基本信息
- 路径：{path}
- 行数：{SKILL.md 行数}
- 任务类型：{识别出的类型}
- 结构模式：{识别出的模式}
- 文件结构：{目录树}

### 综合评分：{总分}/30

| 维度 | 得分 | 关键发现 |
|------|------|---------|
| 触发设计 | {x}/5 | {一句话} |
| 结构设计 | {x}/5 | {一句话} |
| 正文质量 | {x}/5 | {一句话} |
| 资源设计 | {x}/5 | {一句话} |
| 防护机制 | {x}/5 | {一句话} |
| 质量闭环 | {x}/5 | {一句话} |

### 评估等级：{S/A/B/C/D}
...
```

**硬性要求：**
- 每个负面发现都必须附带至少一个 `file:line` 证据
- 每个 P0/P1 建议都必须写清楚"建议改成什么"
- 不要只写"需要优化""建议补充"，必须落到具体文本或具体结构调整

### 评估等级标准

| 等级 | 分数区间 | 含义 |
|------|---------|------|
| S | 27-30 | 标杆级，可作为最佳实践参考 |
| A | 22-26 | 优秀，有小幅优化空间 |
| B | 17-21 | 合格，有明显可改进之处 |
| C | 12-16 | 需要较大改进才能稳定工作 |
| D | 6-11 | 需要重新设计 |

## 评估原则

**关于评分的校准**：评估要基于 Skill 的任务复杂度来校准期望。一个 25 行的窄场景 Skill 如果做到了极致克制和清晰，应该拿高分；不能因为它没有 references/ 目录就扣分。评估的核心问题永远是：这个 Skill 是否有效地帮助 Agent 完成了它声称要完成的任务？

**关于建议的具体性**：每条优化建议都要具体到可操作。

**关于判断 vs 照搬**：清单是工具，不是教条。

## 常见反模式速查

评估时特别留意以下 13 个常见错误（详见 `references/anti-patterns.md`）：

1. 写成百科词条，没有执行路径
2. 所有内容塞进 SKILL.md（超 500 行未拆分）
3. description 只写"是什么"不写"什么时候用"
4. 复杂任务没有分支/Triage 结构
5. 脆弱任务写得太抽象
6. 可脚本化的部分未脚本化
7. 写完不做评测
8. 异步操作没有成功检测
9. 高风险操作没有降级路径
10. 内容创作类缺少风格约束
11. 没有踩坑清单
12. 没有度量机制
13. 硬编码配置

---

## 📄 references/evaluation-checklist.md

# 评估清单详细标准

本文件定义了六个评估维度的具体检查项和评分标准。评估时逐项检查，根据通过率给出 1-5 分。

## 1. 触发设计

评估 description 字段是否能让 Agent 在正确的时机调用这个 Skill。

### 检查项

- [ ] **What**：是否描述了 Skill 的核心能力
- [ ] **When**：是否列举了具体的触发场景（不只是笼统描述）
- [ ] **When Not**：是否排除了不该触发的场景（避免误触发）
- [ ] **关键词覆盖**：是否覆盖了用户可能的多种说法和间接表达
- [ ] **隐含场景**：是否覆盖了用户不直接提及 [[skill]] 名但明确需要它的情况
- [ ] **pushy 程度**：description 是否足够主动（当前 Agent 倾向 under-trigger）

### 评分标准

| 分数 | 标准 |
|------|------|
| 5 | What + When + When Not 齐全，关键词覆盖充分，包含隐含场景 |
| 4 | What + When 清晰，关键词基本覆盖，缺少部分隐含场景或 When Not |
| 3 | 有基本的功能描述和场景，但关键词覆盖不足 |
| 2 | 只描述了功能（What），没有触发场景 |
| 1 | description 过于笼统，几乎无法有效触发 |

## 2. 结构设计

### 检查项

- [ ] **目录结构完整性**：是否有 SKILL.md（必须），是否合理使用了 scripts/、references/、assets/、examples/
- [ ] **模式选择合理性**：所选的结构模式是否匹配任务特点
- [ ] **SKILL.md 行数**：是否控制在 500 行以内
- [ ] **分层加载**：是否做到了渐进式披露
- [ ] **引用层级**：references 之间是否存在超过一层的嵌套引用
- [ ] **任务分流**：复杂任务是否有 Triage/决策树做路径分流
- [ ] **规模匹配**：Skill 的复杂度是否与任务复杂度匹配

### 判断模式是否匹配的参考

| 如果任务是... | 通常适合... |
|-------------|-----------|
| 缺少特定领域知识 | Tool Wrapper |
| 需要生成一致格式的产物 | Generator |
| 需要评审/检查/打分 | Reviewer |
| 需要先收集信息再执行 | Inversion |
| 有严格顺序且不可跳步 | Pipeline |

## 3. 正文质量

### 检查项

- [ ] **面向任务**：是否围绕"怎么做"组织，而非"是什么"的百科介绍
- [ ] **祈使句**：是否使用直接的指令语气
- [ ] **Quick Start / Quick Reference**：是否有快速上手入口
- [ ] **步骤编号**：工作流是否有明确的编号步骤
- [ ] **Why 优于 MUST**：重要约束是否解释了原因，而非只用大写警告
- [ ] **代码示例**：是否提供完整可运行的代码（而非伪代码）
- [ ] **表格决策**：是否用表格帮助 Agent 快速选择方案
- [ ] **前置检查**：依赖外部环境的任务是否有环境检查步骤
- [ ] **冗余内容**：是否教了 Agent 已经知道的东西（浪费上下文）

## 4. 资源设计

### 检查项

- [ ] **脚本封装**：重复且脆弱的操作是否封装成了脚本
- [ ] **脚本使用方式**：SKILL.md 是否告诉 Agent 执行脚本而非读取源码
- [ ] **references 拆分**：大段领域知识是否拆到了 references/ 而非塞在正文
- [ ] **加载时机标注**：是否在 SKILL.md 中标注了什么时候该读哪个 reference
- [ ] **大文件目录**：超过 100 行的 reference 是否有目录
- [ ] **config.json**：需要用户配置的信息是否用 config.json 管理
- [ ] **数据持久化**：需要持久化的数据是否使用了稳定目录

## 5. 防护机制

### 检查项

- [ ] **护栏设置**：脆弱操作是否有具体的约束规则
- [ ] **闸门设计**：关键检查点是否有硬性阻断（而非建议）
- [ ] **降级路径**：可能失败的步骤是否预设了降级方案
- [ ] **成功检测**：异步操作是否有明确的成功/失败判定标准
- [ ] **自由度分级**：是否在安全路段放手、在危险路段加护栏
- [ ] **踩坑清单**：是否积累了已知的常见错误和解决方案
- [ ] **风控策略**：涉及外部服务的操作是否有频率限制、重试策略

## 6. 质量闭环

### 检查项

- [ ] **触发测试**：是否考虑了触发准确性的测试
- [ ] **输出质量验证**：是否有验证输出是否正确的机制
- [ ] **踩坑记录演进**：踩坑清单是否看起来是从实践中积累的
- [ ] **Persona/风格**（内容创作类）：是否有独立的风格约束
- [ ] **Examples**：是否有可插拔的示例/案例系统
- [ ] **可扩展性**：是否为用户留出了扩展点

---

## 📄 references/anti-patterns.md

# 13 个常见反模式详解

## 1. 百科词条病

**症状**：SKILL.md 大量介绍概念、背景、历史，但没有可执行的工作流步骤。

**为什么有害**：Skill 的价值不在于知道什么，而在于知道怎么做。

**修复**：将内容重组为面向任务的工作流。每一段都应该回答"Agent 接下来该做什么"。

## 2. 上下文爆炸

**症状**：SKILL.md 超过 500 行，所有知识、规则、示例全部塞在一个文件中。

**修复**：按渐进式披露原则拆分。核心工作流留在 SKILL.md（500 行以内），领域知识放 references/，代码示例放 scripts/，输出模板放 assets/。

## 3. description 空洞

**症状**：description 只写了功能描述，没有列举具体触发场景。

**修复**：description 包含三要素——What（做什么）、When（什么时候用）、When Not（什么时候不用）。

## 4. 缺少分支结构

**症状**：Skill 处理多种变体的任务，但没有 Triage/决策树，只有一条线性路径。

**修复**：加入决策树、Archetype 分类或 if-then 结构。

## 5. 脆弱任务过度抽象

**症状**：涉及文档格式、浏览器自动化、外部API 等脆弱操作的 Skill，只写了原则而没有具体规则。

**修复**：对脆弱操作降低自由度，提供具体的 CRITICAL 标注和 ✅/❌ 对比示例。同时解释 why。

## 6. 不脚本化

**症状**：每次执行时 Agent 都在现写重复的代码逻辑。

**修复**：将重复且确定性的操作封装成 scripts/。

## 7. 不做评测

**症状**：Skill 写完就上线，没有用真实 prompt 测试过触发和输出。

**修复**：至少测试三类 prompt——典型场景、边界场景、相邻场景。

## 8. 异步无检测

**症状**：涉及异步操作但没有成功/失败的判定标准。

**修复**：定义明确的成功标记——URL 模式匹配、页面元素出现、返回值检查等。

## 9. 无降级路径

**症状**：只有正常路径，失败时 Agent 要么卡住要么自由发挥。

**修复**：每个可能失败的步骤预设降级方案。

## 10. 内容无风格

**症状**：内容创作类 Skill 没有 Persona 或风格约束，输出调性不可控。

**修复**：用独立的 persona.md 定义角色身份、语气风格、禁区。

## 11. 无踩坑清单

**症状**：Skill 中没有任何已知问题和常见错误的记录。

**修复**：从第一天开始建立踩坑清单，按频率排序、按严重性分级。

## 12. 无度量机制

**症状**：不知道 Skill 被使用的频率和场景，无法判断效果。

**修复**：建立基本的使用追踪，关注触发率、成功率、用户满意度。

## 13. 硬编码配置

**症状**：Slack 频道、时区、团队名称等配置硬编码在 SKILL.md 中。

**修复**：用 config.json 存用户配置。在 SKILL.md 中写明：如果 config.json 不存在，先引导用户填写，保存后再执行。

---

# 二、knowledge-harvesting

## 📄 SKILL.md

```yaml
---
name: knowledge-harvesting
description: "知识沉淀专家。负责：(1) 从完成的项目中提取业务知识（指标定义、表结构、术语），(2) 更新企业知识库（knowledge/ 目录），(3) 维护术语表。使用场景：项目完成后用户说'沉淀知识'、'更新知识库'、'提取项目里的指标'、'维护术语表'、'spec knowledge'时触发。通常在项目收尾阶段使用。关键词：知识沉淀、项目总结、术语维护、知识库更新。不适用：指标注册到平台（用 metric-dim-registration）、需求分析（用 requirement-analyst）。"

metadata:
  skillhub.creator: "wangsongmian"
  skillhub.updater: "baijingwen02"
  skillhub.version: "V2"
  skillhub.source: "FRIDAY Skillhub"
  skillhub.skill_id: "1609"
  skillhub.high_sensitive: "false"
---
```

# 知识沉淀工具

## 执行流程

### Step 1: 初始化上下文
- [ ] 调用 `context_manager.py`
- [ ] 加载项目配置和中间产物（PRD、技术方案、ETL 等）

### Step 2: 提取知识

从项目产物中提取以下三类知识：

#### 指标知识
从 PRD 和技术方案中提取：
- 指标名称
- 指标定义
- 计算逻辑
- 数据类型

#### 表知识
从技术方案和 ETL 中提取：
- 表名称
- 表描述
- 字段列表
- 分层信息

#### 术语知识
从所有文档中提取：
- 术语名称
- 术语定义
- 使用场景

### Step 3: 验证提取的知识

- [ ] 调用 `knowledge_validator.py` 验证
- [ ] 检查必填字段是否完整
- [ ] 如果验证失败，根据错误信息重新提取

### Step 4: 更新知识库

- [ ] 调用 `knowledge_manager.py`
- [ ] 更新 `knowledge/` 目录

## 输出格式

```json
{
  "metrics": [
    {
      "name": "GMV",
      "definition": "订单总金额",
      "logic": "sum(order_amount)",
      "data_type": "DECIMAL"
    }
  ],
  "tables": [
    {
      "table_name": "dwd_order",
      "description": "订单明细表",
      "layer": "DWD",
      "fields": [...]
    }
  ],
  "glossary": [
    {
      "term": "ROI",
      "definition": "投资回报率",
      "usage": "用于评估营销效果"
    }
  ]
}
```

## 参考文档

- 详见 `references/extraction-rules.md` 了解提取规则
- 详见 `references/output-schema.md` 了解输出格式
- 详见 `references/examples.md` 查看实际案例

---

## 📄 references/extraction-rules.md

# 知识提取规则

## 指标知识提取

### 提取来源
- PRD 中的"数据需求"章节
- 技术方案中的"数据模型设计"章节
- ETL 代码中的注释

### 提取字段
- **name**：指标名称
- **definition**：指标定义
- **logic**：计算逻辑（如：sum、count、avg）
- **data_type**：数据类型（BIGINT、DECIMAL 等）

### 提取规则
1. 从 PRD 的指标列表中提取所有指标
2. 从技术方案中补充指标的计算逻辑
3. 从 ETL 中补充数据类型信息
4. 去重：相同名称的指标只保留一条

### 示例
```json
{
  "name": "GMV",
  "definition": "订单总金额",
  "logic": "sum(order_amount)",
  "data_type": "DECIMAL"
}
```

## 表知识提取

### 提取来源
- 技术方案中的"数据模型设计"章节
- ETL 代码中的 CREATE TABLE 语句
- 数据字典文档

### 提取字段
- **table_name**：表名称
- **description**：表描述
- **layer**：分层（DWD、DWS、ADS 等）
- **fields**：字段列表

### 提取规则
1. 从技术方案中提取所有新建表
2. 从 ETL 中提取表的 DDL 信息
3. 解析字段列表和字段注释
4. 标记表的分层信息

### 示例
```json
{
  "table_name": "dwd_order",
  "description": "订单明细表",
  "layer": "DWD",
  "fields": [
    {"name": "order_id", "type": "BIGINT", "comment": "订单ID"},
    {"name": "order_amount", "type": "DECIMAL", "comment": "订单金额"}
  ]
}
```

## 术语知识提取

### 提取来源
- MRD 中的"术语定义"章节
- PRD 中的"参考信息"章节
- 技术方案中的"名词解释"章节

### 提取字段
- **term**：术语名称
- **definition**：术语定义
- **usage**：使用场景

### 提取规则
1. 从所有文档中提取业务术语
2. 提取技术术语（如：DWD、DWS）
3. 提取缩写词（如：GMV、ROI）
4. 去重：相同术语只保留一条

## 提取优先级

1. **高优先级**：来自 PRD 和技术方案的明确定义
2. **中优先级**：来自 ETL 代码的隐含信息
3. **低优先级**：来自其他文档的参考信息

## 提取质量检查

- [ ] 所有指标都有 name 和 definition
- [ ] 所有表都有 table_name 和 description
- [ ] 所有术语都有 term 和 definition
- [ ] 没有重复的指标/表/术语
- [ ] 字段值不为空

---

## 📄 references/output-schema.md

# 知识库输出 Schema

## 顶层结构

```json
{
  "metrics": [...],
  "tables": [...],
  "glossary": [...]
}
```

## 指标对象 Schema

```json
{
  "name": "string (必填)",
  "definition": "string (必填)",
  "logic": "string (可选)",
  "data_type": "string (可选)",
  "category": "string (可选)",
  "owner": "string (可选)"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✓ | 指标名称 |
| definition | string | ✓ | 指标定义 |
| logic | string | ✗ | 计算逻辑（如：sum、count） |
| data_type | string | ✗ | 数据类型（BIGINT、DECIMAL 等） |
| category | string | ✗ | 指标分类 |
| owner | string | ✗ | 指标负责人 |

## 表对象 Schema

```json
{
  "table_name": "string (必填)",
  "description": "string (必填)",
  "layer": "string (可选)",
  "fields": [
    {
      "name": "string",
      "type": "string",
      "comment": "string"
    }
  ]
}
```

## 术语对象 Schema

```json
{
  "term": "string (必填)",
  "definition": "string (必填)",
  "usage": "string (可选)"
}
```

---

## 📄 references/examples.md（节选）

# 知识沉淀实际案例

## 案例：从项目产物中提取知识

### 项目背景

- 项目名称：神抢手流量看板
- 交付形式：数据集（BI 看板）
- 产物：PRD、技术方案、ETL 代码

### 提取过程

#### Step 1: 从 PRD 中提取指标知识

**提取结果**：

```json
{
  "metrics": [
    {"name": "GMV", "definition": "订单总金额", "logic": "sum(order_amount)"},
    {"name": "订单数", "definition": "订单总数", "logic": "count(order_id)"},
    {"name": "用户数", "definition": "活跃用户数", "logic": "count(distinct user_id)"}
  ]
}
```

#### Step 2: 从技术方案中提取表知识

```json
{
  "tables": [
    {"table_name": "dwd_order", "description": "订单明细表", "layer": "DWD"},
    {"table_name": "dws_order_daily", "description": "订单日聚合表", "layer": "DWS"}
  ]
}
```

#### Step 3: 从 ETL 代码中补充信息

```sql
CREATE TABLE dwd_order (
  order_id BIGINT COMMENT '订单ID',
  order_amount DECIMAL COMMENT '订单金额',
  user_id BIGINT COMMENT '用户ID',
  dt STRING COMMENT '日期'
)
```

#### Step 4: 从 MRD 中提取术语知识

```json
{
  "glossary": [
    {"term": "GMV", "definition": "Gross Merchandise Volume，商品交易总额", "usage": "用于衡量平台交易规模"},
    {"term": "DAU", "definition": "Daily Active User，日活跃用户", "usage": "用于衡量用户活跃度"}
  ]
}
```

---

## 📄 references/knowledge_template.json

```json
{
  "metrics": [
    {
      "name": "GMV",
      "definition": "订单总金额",
      "logic": "sum(order_amount)",
      "data_type": "DECIMAL",
      "category": "经营/交易",
      "owner": "data_team"
    },
    {
      "name": "订单数",
      "definition": "订单总数",
      "logic": "count(order_id)",
      "data_type": "BIGINT",
      "category": "经营/交易",
      "owner": "data_team"
    }
  ],
  "tables": [
    {
      "table_name": "dwd_order",
      "description": "订单明细表",
      "layer": "DWD",
      "fields": [
        {"name": "order_id", "type": "BIGINT", "comment": "订单ID"},
        {"name": "order_amount", "type": "DECIMAL", "comment": "订单金额"},
        {"name": "user_id", "type": "BIGINT", "comment": "用户ID"},
        {"name": "dt", "type": "STRING", "comment": "日期"}
      ]
    },
    {
      "table_name": "dws_order_daily",
      "description": "订单日聚合表",
      "layer": "DWS",
      "fields": [
        {"name": "gmv", "type": "DECIMAL", "comment": "订单总金额"},
        {"name": "order_cnt", "type": "BIGINT", "comment": "订单数"},
        {"name": "dt", "type": "STRING", "comment": "日期"}
      ]
    }
  ],
  "glossary": [
    {"term": "GMV", "definition": "Gross Merchandise Volume，商品交易总额", "usage": "用于衡量平台交易规模"},
    {"term": "DAU", "definition": "Daily Active User，日活跃用户", "usage": "用于衡量用户活跃度"},
    {"term": "DWD", "definition": "Data Warehouse Detail，数据仓库明细层", "usage": "存储原始数据的明细信息"},
    {"term": "DWS", "definition": "Data Warehouse Summary，数据仓库汇总层", "usage": "存储聚合后的数据"}
  ]
}
```

---

## 📄 scripts/context_manager.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文管理器 (Context Manager for CatPaw Agents)

职责: 为子Agent准备执行上下文，包括：
- 加载项目配置
- 加载上游产物
- 验证工作区路径

工作区结构: projects/{需求名称}/
"""

import argparse
import json
import os
import sys


def load_json_file(file_path):
    """加载JSON文件，返回字典或None"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 错误: 加载 {file_path} 失败: {str(e)}", file=sys.stderr)
            return None
    return None


def validate_workspace(workspace_path):
    """
    验证工作区路径的有效性
    
    Args:
        workspace_path: 工作区的绝对路径
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not os.path.isabs(workspace_path):
        return False, f"工作区必须是绝对路径，收到: {workspace_path}"
    
    if not os.path.exists(workspace_path):
        return False, f"工作区目录不存在: {workspace_path}"
    
    if not os.path.isdir(workspace_path):
        return False, f"工作区路径不是目录: {workspace_path}"
    
    config_path = os.path.join(workspace_path, "config.json")
    if not os.path.exists(config_path):
        return False, f"工作区缺少 config.json: {config_path}"
    
    return True, None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="上下文管理器")
    parser.add_argument("--task", required=True, help="当前任务名称")
    parser.add_argument("--workspace", required=True, help="工作区的绝对路径")
    parser.add_argument("--input", required=False, help="用户自然语言输入或临时参数")
    parser.add_argument("--track-interaction", action="store_true", help="是否跟踪交互历史")
    
    args = parser.parse_args()
    
    is_valid, error_message = validate_workspace(args.workspace)
    if not is_valid:
        print(f"❌ 工作区验证失败: {error_message}", file=sys.stderr)
        sys.exit(1)
    
    context = {
        "task": args.task,
        "workspace": args.workspace,
        "mode": "auto",
        "user_input": args.input
    }

    config_path = os.path.join(args.workspace, "config.json")
    config = load_json_file(config_path)
    if config:
        context["config"] = config
    
    dependency_map = {
        "requirement_analysis_agent": [".cache/review-mrd.json"],
        "datasource-exploration": [".cache/search_results.json"],
        "lineage-impact-analysis": [".cache/impact_analysis.json"],
        "table-selection": [".cache/main_table_selection.json"],
        "etl-logic-design": [".cache/etl_logic.json", "join_logic.json"],
        "sql-evaluator": [".cache/performance_notes.json", ".cache/risk_summary.json"],
    }
    
    cache_dir = os.path.join(args.workspace, ".cache")
    required_files = dependency_map.get(args.task, [])
    
    artifacts = {}
    for file_name in required_files:
        file_path = os.path.join(cache_dir, file_name)
        data = load_json_file(file_path)
        if data:
            key = file_name.replace(".json", "").replace("-", "_")
            artifacts[key] = data
            
    context["artifacts"] = artifacts

    if args.input:
        context["mode"] = "adhoc"
    
    print(json.dumps(context, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

---

## 📄 scripts/knowledge_manager.py

```python
import argparse
import json
import os
import sys

def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_metrics(knowledge_dir, new_metrics):
    path = os.path.join(knowledge_dir, "数据资产", "metrics.json")
    existing = load_json(path)
    existing_names = {m.get("name") for m in existing}
    added_count = 0
    for m in new_metrics:
        if m.get("name") not in existing_names:
            existing.append(m)
            added_count += 1
    save_json(path, existing)
    return added_count

def update_tables(knowledge_dir, new_tables):
    path = os.path.join(knowledge_dir, "数据资产", "tables.json")
    existing = load_json(path)
    existing_names = {t.get("table_name") for t in existing}
    added_count = 0
    for t in new_tables:
        if t.get("table_name") not in existing_names:
            existing.append(t)
            added_count += 1
    save_json(path, existing)
    return added_count

def append_glossary(knowledge_dir, terms):
    path = os.path.join(knowledge_dir, "业务知识", "glossary.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = ""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    new_content = []
    for term in terms:
        if term.get("term") not in content:
            new_content.append(f"### {term.get('term')}\n{term.get('definition')}\n")
    if new_content:
        with open(path, 'a', encoding='utf-8') as f:
            f.write("\n" + "\n".join(new_content))
    return len(new_content)

def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Manager")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--content", required=True, help="JSON string with new knowledge")
    args = parser.parse_args()
    
    try:
        data = json.loads(args.content)
    except:
        print("Error: Invalid JSON content")
        sys.exit(1)
        
    root_dir = os.path.abspath(os.path.join(args.workspace, "../../"))
    knowledge_dir = os.path.join(root_dir, "knowledge")
    
    metrics_added = update_metrics(knowledge_dir, data.get("metrics", []))
    tables_added = update_tables(knowledge_dir, data.get("tables", []))
    terms_added = append_glossary(knowledge_dir, data.get("glossary", []))
    
    print(f"### 📚 知识库更新完成")
    print(f"- 新增指标: {metrics_added}")
    print(f"- 新增表: {tables_added}")
    print(f"- 新增术语: {terms_added}")

if __name__ == "__main__":
    main()
```

---

## 📄 scripts/knowledge_validator.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识数据验证脚本

功能：验证 Agent 提取的知识结构是否符合规范
输入：知识 JSON {"metrics": [...], "tables": [...], "glossary": [...]}
输出：验证报告 {"valid": bool, "errors": [...], "warnings": [...]}
"""

import json
import sys
import argparse

def validate_knowledge(knowledge_dict):
    errors = []
    warnings = []
    
    if not isinstance(knowledge_dict, dict):
        errors.append("输入必须是 JSON 对象")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    metrics = knowledge_dict.get("metrics", [])
    if not isinstance(metrics, list):
        errors.append("metrics 必须是数组")
    else:
        for idx, metric in enumerate(metrics):
            if not metric.get("name"):
                errors.append(f"指标 #{idx+1}: 缺少 name（指标名称）")
            if not metric.get("definition"):
                errors.append(f"指标 #{idx+1}: 缺少 definition（指标定义）")
    
    tables = knowledge_dict.get("tables", [])
    if not isinstance(tables, list):
        errors.append("tables 必须是数组")
    else:
        for idx, table in enumerate(tables):
            if not table.get("table_name"):
                errors.append(f"表 #{idx+1}: 缺少 table_name（表名称）")
            if not table.get("description"):
                errors.append(f"表 #{idx+1}: 缺少 description（表描述）")
    
    glossary = knowledge_dict.get("glossary", [])
    if not isinstance(glossary, list):
        errors.append("glossary 必须是数组")
    else:
        for idx, term in enumerate(glossary):
            if not term.get("term"):
                errors.append(f"术语 #{idx+1}: 缺少 term（术语名称）")
            if not term.get("definition"):
                errors.append(f"术语 #{idx+1}: 缺少 definition（术语定义）")
    
    if not metrics and not tables and not glossary:
        warnings.append("未提取到任何知识数据（指标、表、术语都为空）")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def main():
    parser = argparse.ArgumentParser(description="知识数据验证工具")
    args = parser.parse_args()
    
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            print("❌ 无法读取输入数据")
            sys.exit(1)
        knowledge_dict = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        sys.exit(1)
    
    result = validate_knowledge(knowledge_dict)
    
    if result["valid"]:
        print("✅ 验证通过")
        sys.exit(0)
    else:
        print("❌ 验证失败:")
        for error in result["errors"]:
            print(f"  - {error}")
        for warning in result["warnings"]:
            print(f"  ⚠️  {warning}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

# 三、dw-data-quality

## 📄 SKILL.md

```yaml
---
name: dw-data-quality
description: 数仓表数据质量验证 Skill。给定一张 Hive 表名（或同时提供 ETL 任务 SQL），自动完成七大维度的数据质量校验：唯一性（主键重复/NULL）、完整性（字段 NULL 率）、有效性（格式/枚举/值域）、一致性（跨字段逻辑/派生字段）、准确性（关联映射命中率/根因定位）、时效性（数据新鲜度/分区连续性）、ETL 逻辑正确性（CASE WHEN 条件命中率/CTE 膨胀/NULL 三值逻辑/UNION ALL 语义/CNY 汇率换算）。

metadata:
  skillhub.creator: "wb_shizhengxiang"
  skillhub.version: "V3"
  skillhub.skill_id: "19601"
---
```

# 数仓表数据质量验证 Skill

本 Skill 的核心思路：**先读懂 ETL 逻辑，再生成有针对性的校验规则，最后输出带根因分析的报告**。

区别于通用 DQ 工具的关键在于：
1. 能区分"设计决策导致的 NULL/常量"和"真实数据问题"
2. 能做多表联动的关联映射验证
3. **能验证 ETL 逻辑本身是否正确**（CASE WHEN 条件能否命中源表实际值、CTE 是否膨胀、NULL 三值逻辑陷阱等）
4. 自动定位根因而不只是报告问题

> **V3 新增**：第七维度"ETL 逻辑正确性验证"，覆盖本次实战中发现的 6 类高频 ETL 逻辑漏洞。

## 前置检查

```bash
# 1. 检查 venv 是否存在
source ~/.meituan-local-tools/.venv/bin/activate 2>/dev/null || { echo "❌ mt-data-tools 未安装"; exit 1; }

# 2. 读取 config.json（如果存在）
CONFIG=~/.catpaw/skills/dw-data-quality/config.json
if [ -f "$CONFIG" ]; then
  DEFAULT_PROJECT=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d.get('default_project',''))")
  DEFAULT_PARENT_ID=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d.get('default_parent_doc_id',''))")
fi
```

## 第一步：信息收集

### 1.1 必须获取的信息

**表名**（必须）：用户提供的 Hive 表名，格式为 `db.table`。

**ETL SQL**（优先获取）：

```bash
mtdata xt job search <table_name_keyword> -n 5
mkdir -p /tmp/dq_<table>
mtdata xt job get code <job_full_name> --output /tmp/dq_<table>/
```

**DDL**（必须）：

```bash
mtdata table ddl <db.table>
```

### 1.2 从 ETL SQL 中提取关键信息

读取 ETL 代码后，识别以下模式（详细解析规则见 `references/etl-sql-parser.md`）：

| 模式 | 示例 | 对应验证维度 |
|---|---|---|
| 写死 NULL | `null as field_name` | 完整性：归入"预期为 NULL"组 |
| 写死常量 | `'50' as status_code` | 有效性：常量一致性验证 |
| coalesce 兜底 | `coalesce(a, b) as field` | 一致性：时序/逻辑验证 |
| left join 关联 | `left join mapping_table on ...` | 准确性：命中率验证 |
| case when 分支 | `case when source='xxx' then ...` | **ETL逻辑：分支条件命中率验证** |
| **CTE + JOIN** | `WITH cte AS (...) ... JOIN cte ON ...` | **ETL逻辑：CTE 膨胀验证** |
| **UNION ALL** | `SELECT ... UNION ALL SELECT ...` | **ETL逻辑：字段语义一致性验证** |
| **!= / <> 条件** | `WHERE flag <> 'Y'` | **ETL逻辑：NULL 三值逻辑陷阱** |
| **CNY/原币双字段** | `amt_cny`, `amt` 公式相同 | **ETL逻辑：汇率换算遗漏验证** |

## 第二步：生成校验 SQL

基于收集到的信息，按七大维度生成校验 SQL。**所有规则模板见 `references/rule-templates.md`**。

### 维度与模板对应关系

| 维度 | 触发条件 | 模板编号 |
|---|---|---|
| 数据源概览（基准） | 有分组字段 | T00 |
| 唯一性 | DDL 有主键 / ETL 有 partition by | T01 |
| 完整性 | 所有字段 | T02 |
| 有效性-时间格式 | 字段名含 time/date | T03 |
| 有效性-枚举完整性 | DDL comment 含枚举 | T04 |
| 有效性-金额值域 | 金额/数量/比例类字段 | T05 |
| 一致性 | ETL 有 coalesce / 派生字段 | T06 |
| 准确性-命中率 | ETL 有 left join 关联映射表 | T07 |
| 准确性-根因（第二阶段） | T07 命中率 < 80% | T08 |
| 时效性 | 有分区字段 / 有 create_time 类字段 | T09 |
| 常量字段一致性 | ETL 有写死常量 | T10 |
| **ETL逻辑-CASE WHEN 命中率** | **ETL 有 CASE WHEN / IF 条件转换** | **T11** |
| **ETL逻辑-CTE 膨胀** | **ETL 有 CTE + JOIN 组合** | **T12** |
| **ETL逻辑-NULL 三值逻辑** | **ETL 有 != / <> / NOT IN / NOT RLIKE 条件** | **T13** |
| **ETL逻辑-UNION ALL 语义** | **ETL 有 UNION ALL** | **T14** |
| **ETL逻辑-CNY 汇率换算** | **ETL 有 _cny 和原币双字段** | **T15** |

### SQL 文件命名规范

所有文件放在 `/tmp/dq_<table_name>/`，每个文件头部必须加 `-- cut_1`：

```
q00_overview.sql       # 数据源分布（基准）
q01_pk.sql             # 主键唯一性
q02_null_rate.sql      # 完整性 NULL 率
q03_time_format.sql    # 时间格式
q04_enum.sql           # 枚举完整性
q05_amount.sql         # 金额值域
q06_consistency.sql    # 跨字段一致性
q07_mapping_rate.sql   # 关联命中率（第一阶段）
q08_mapping_detail.sql # 未命中根因（第二阶段，按需生成）
q09_freshness.sql      # 数据新鲜度
q10_const_fields.sql   # 常量字段一致性
q11_casewhen_hit.sql   # CASE WHEN 条件命中率（ETL逻辑）
q12_cte_expand.sql     # CTE 膨胀检测（ETL逻辑）
q13_null_trap.sql      # NULL 三值逻辑陷阱（ETL逻辑）
q14_union_semantic.sql # UNION ALL 字段语义（ETL逻辑）
q15_cny_rate.sql       # CNY 汇率换算验证（ETL逻辑）
```

## 第三步：并行执行

```bash
source ~/.meituan-local-tools/.venv/bin/activate
python3 ~/.catpaw/skills/dw-data-quality/scripts/submit_queries.py \
  --sql-dir /tmp/dq_<table> \
  --project <project> \
  --parallel \
  --max-workers 6
```

## 第四步：结果分析

### 问题定级标准

- **P0**：影响行数 > 10% 且直接导致下游计算结果错误
- **P1**：影响行数 > 5%，或有明确修复路径的系统性问题
- **P2**：影响行数 < 5%，或需要业务确认的边界情况
- **P3**：已知设计决策，下游使用时需注意

## 第五步：输出报告

报告格式规范详见 `references/report-template.md`。

写入学城文档：

```bash
REPORT_TITLE="<table_name>数据质量验收报告_$(date +%Y%m%d)"
oa-skills citadel createDocument \
  --title "$REPORT_TITLE" \
  --file /tmp/dq_<table>/report.md \
  --parentId <用户指定的 contentId>
```

## 快速参考

```bash
# 搜索 ETL 任务
mtdata xt job search <keyword> -n 5

# 拉取 ETL 代码
mtdata xt job get code <job_full_name> --output /tmp/dq_<table>/

# 获取表 DDL
mtdata table ddl <db.table>

# 提交 SQL（异步，返回 query_id）
mtdata query submit <file.sql> -p <project>

# 查询状态
mtdata query status <id1> <id2> <id3> -p <project>

# 拉取结果
mtdata query result <query_id> -p <project> --page-size 99999 -o <dir>/
```

## 参考文件索引

| 文件 | 内容 | 何时读取 |
|---|---|---|
| `references/rule-templates.md` | T00~T15 参数化 SQL 模板 | 生成校验 SQL 时 |
| `references/etl-sql-parser.md` | ETL SQL 模式识别指南（含 V3 新增 6 类模式） | 解析 ETL 代码时 |
| `references/report-template.md` | 报告结构和输出格式规范 | 撰写报告时 |
| `references/known-issues.md` | 高频踩坑清单（按维度分类） | 遇到异常结果时优先查阅 |
| `scripts/submit_queries.py` | 批量并行提交探数 SQL | 第三步执行时 |
| `config.json` | 用户配置（default_project、default_parent_doc_id） | 前置检查时读取 |

---

## 📄 config.json

```json
{
  "default_project": "erp-dw",
  "default_parent_doc_id": ""
}
```

---

## 📄 references/etl-sql-parser.md

# ETL SQL 解析指南

本文档指导如何从 ETL SQL 中提取数据质量验证所需的关键信息。

## 一、解析目标

从 ETL SQL 中提取以下信息，用于生成校验 SQL：

| 信息类型 | 用途 |
|---------|------|
| 主键字段 | T01 唯一性验证 |
| 所有字段及类型 | T02 NULL 率统计 |
| 时间/日期字段 | T03 格式验证 |
| 枚举字段及合法值 | T04 枚举完整性 |
| 金额字段 | T05 值域验证 |
| 字段间逻辑关系 | T06 一致性验证 |
| LEFT JOIN 关联字段 | T07/T08 命中率分析 |
| 常量/硬编码字段 | T10 常量一致性 |
| **CASE WHEN / IF 条件** | **T11 条件命中率验证（V3 新增）** |
| **CTE + JOIN 组合** | **T12 CTE 膨胀验证（V3 新增）** |
| **!= / <> / NOT IN / NOT RLIKE** | **T13 NULL 三值逻辑陷阱（V3 新增）** |
| **UNION ALL 多源合并** | **T14 字段语义一致性（V3 新增）** |
| **_cny / 原币双字段** | **T15 CNY 汇率换算验证（V3 新增）** |

## 二、解析步骤

### Step 1：识别目标表和分区

```
目标表：INSERT INTO / INSERT OVERWRITE TABLE 后的表名
分区字段：PARTITION(dt='${bizdate}') 中的字段
```

### Step 2：提取主键字段

主键通常来自以下线索：
1. DDL 注释中标注 `主键` 或 `pk`
2. ETL SQL 中 `row_number() OVER (PARTITION BY xxx ORDER BY yyy)` 的 PARTITION BY 字段
3. 字段名包含 `_id`、`_code`、`_no`、`_sn` 且在 SELECT 中排在前几位
4. 多个字段组合唯一（如 `po_code + fee_type_code`）

### Step 3：识别字段类型和来源

| 来源类型 | 特征 | 示例 |
|---------|------|------|
| 直接映射 | `t1.field_name` | `t1.po_code` |
| 常量/硬编码 | `'固定值' AS field` | `'优选' AS biz_type_name` |
| 写死 NULL | `null AS field` | `null AS supplier_code` |
| 计算派生 | 含运算符或函数 | `t1.amt * t1.rate AS amt_cny` |
| COALESCE 兜底 | `COALESCE(a, b)` | `COALESCE(t1.name, t2.name)` |
| CASE WHEN | 条件映射 | `CASE WHEN status=1 THEN '已审批' END` |
| IF 条件 | `IF(cond, val1, val2)` | `IF(is_asset = 'Y', 1, 0)` |
| 关联字段 | 来自 JOIN 的表 | `cm.category_name` |

### Step 8（V3 新增）：识别 CASE WHEN / IF 条件

**目的**：找出所有条件转换逻辑，验证条件能否命中源表实际取值。

**重点关注**：
1. `IF(field = 'Y', ...)` — 需验证源表该字段的实际取值是否包含 `'Y'`
2. `CASE WHEN field = '2' THEN ...` — 需验证源表枚举值是否与 ETL 条件一致
3. 类型隐患：ETL 用 int literal（`= 1`）但源表字段是 string 类型（存储 `'1'`）

### Step 9（V3 新增）：识别 CTE + JOIN 膨胀风险

**膨胀风险判断规则**：
- CTE 用 `SELECT DISTINCT a, b`，但 JOIN 条件只用 `ON t.a = cte.a`（b 未参与 JOIN）→ **高风险**
- CTE 用 `SELECT DISTINCT a`，JOIN 条件用 `ON t.a = cte.a` → **低风险**
- CTE 无 DISTINCT 且无 ROW_NUMBER → **高风险**

### Step 10（V3 新增）：识别 NULL 三值逻辑陷阱

Hive 中 NULL 的三值逻辑规则：
- `NULL = 'Y'` → NULL（不是 FALSE）
- `NULL <> 'Y'` → NULL（不是 TRUE）
- `NULL NOT IN ('A', 'B')` → NULL（不是 TRUE）
- `NULL NOT RLIKE '...'` → NULL（不是 TRUE）
- `NULL IS NULL` → TRUE（这个是安全的）

| 危险模式 | 示例 | 风险 |
|---------|------|------|
| `field <> 'value'` | `writeoff_flag <> 'Y'` | NULL 记录被排除，可能漏计 |
| `field != 'value'` | `status != 'CLOSED'` | 同上 |
| `field NOT IN (...)` | `channel NOT IN ('A', 'B')` | NULL 记录被排除 |
| `field NOT RLIKE '...'` | `org_path NOT RLIKE '102396'` | NULL 落入 ELSE 分支，可能误分类 |

---

## 📄 references/known-issues.md

# 高频踩坑清单

从实战中积累的已知问题，遇到异常结果时优先对照此清单排查。

## 唯一性（T01）

| 症状 | 根因 | 修复方向 |
|------|------|---------|
| 主键重复数 > 0，但 ETL 有 `row_number()` 去重 | `row_number()` 的 `partition by` 字段不完整，遗漏了区分维度 | 补充 `partition by` 字段，或改用 `DISTINCT` |
| 主键重复，且重复行数据完全一致 | 上游 UNION ALL 重复拼接了同一数据源 | 检查 UNION ALL 各分支的 source 过滤条件是否互斥 |

## ETL 逻辑 — CASE WHEN 命中率（T11）

| 症状 | 根因 | 修复方向 |
|------|------|---------|
| 某分支命中率 = 0% | **类型不匹配**：ETL 用 `= 1`（int）但源表存 `'1'`（string） | 统一类型，用 `CAST` 转换或修改条件值 |
| 某分支命中率 = 0% | **取值不匹配**：ETL 用 `= 'Y'` 但源表实际是 `'1'`/`'0'` | 回源表查实际枚举值，修改条件 |
| 所有行落入 ELSE 分支 | CASE WHEN 条件字段名写错（大小写/下划线差异） | 对照 DDL 检查字段名 |

## ETL 逻辑 — CTE 膨胀（T12）

| 症状 | 根因 | 修复方向 |
|------|------|---------|
| CTE 膨胀率 > 0%，主键出现重复 | `SELECT DISTINCT a, b` 但 JOIN 用 `ON t.a = cte.a`，b 有多值导致一对多 | 改为 `ROW_NUMBER() OVER (PARTITION BY a ORDER BY ...)` 取唯一值 |
| CTE 膨胀率 > 0%，但主键不重复 | CTE 膨胀被后续 `GROUP BY` 或 `DISTINCT` 消化，结果正确 | 标记为 P2，建议优化 CTE 写法以提升性能 |

## ETL 逻辑 — NULL 三值逻辑（T13）

| 症状 | 根因 | 修复方向 |
|------|------|---------|
| `field <> 'Y'` 过滤后，NULL 值记录消失 | `NULL <> 'Y'` 结果为 NULL，不满足 WHERE 条件，记录被排除 | 改为 `COALESCE(field, '') <> 'Y'` |
| `NOT IN (...)` 过滤结果为空 | 列表中含 NULL 值，导致整个 NOT IN 结果为 NULL | 改为 `field IS NULL OR field NOT IN (...)` |
| `NOT RLIKE '...'` 过滤掉了 NULL 行 | `NULL NOT RLIKE` 结果为 NULL，落入 ELSE 分支 | 改为 `COALESCE(field, '') NOT RLIKE '...'` |

## 执行环境

| 症状 | 根因 | 修复方向 |
|------|------|---------|
| `mtdata query submit` 返回非 0 | venv 未激活，或 mtdata 版本过旧 | 先 `source ~/.meituan-local-tools/.venv/bin/activate`，再重试 |
| `oa-skills citadel createDocument` 失败 | SSO 登录态过期 | 重新登录后重试；降级保存到本地 |
| submit_queries.py 并行提交部分失败 | 探数平台并发限制触发限流 | 降低 `--max-workers` 到 3，或改用串行模式 |

---

## 📄 references/rule-templates.md（核心模板节选）

# 数据质量校验 SQL 规则模板库

每个模板都是参数化的，使用时将 `{TABLE}`、`{FIELD}` 等占位符替换为实际值。所有 SQL 文件头部必须加 `-- cut_1`。

## T00：数据源概览（基准）

```sql
-- cut_1
-- T00: 数据源分布（基准）
SELECT
    {GROUP_FIELD}
    , COUNT(1)                                              AS cnt
    , ROUND(SUM({AMT_FIELD}) / 1e8, 4)                     AS total_amt_yi
    , COUNT(DISTINCT {PK_FIELD})                            AS distinct_pk
FROM {TABLE}
GROUP BY {GROUP_FIELD}
ORDER BY cnt DESC
```

## T01：主键唯一性验证

```sql
-- cut_1
-- T01a: 主键唯一性（单字段）
SELECT
    COUNT(1)                                                  AS total_rows
    , COUNT(DISTINCT {PK_FIELD})                              AS distinct_pk
    , COUNT(1) - COUNT(DISTINCT {PK_FIELD})                   AS dup_cnt
    , ROUND((COUNT(1) - COUNT(DISTINCT {PK_FIELD})) * 100.0 / COUNT(1), 4) AS dup_pct
    , SUM(CASE WHEN {PK_FIELD} IS NULL THEN 1 ELSE 0 END)     AS pk_null_cnt
FROM {TABLE}
```

## T02：完整性 NULL 率统计

```sql
-- cut_1
-- T02: 全字段 NULL 率统计
SELECT
    COUNT(1) AS total_rows
    , SUM(CASE WHEN {NULL_FIELD_1} IS NULL THEN 1 ELSE 0 END)   AS {NULL_FIELD_1}_null
    , SUM(CASE WHEN {REQUIRED_FIELD_1} IS NULL THEN 1 ELSE 0 END) AS {REQUIRED_FIELD_1}_null
FROM {TABLE}
```

## T11：CASE WHEN / IF 条件命中率验证（V3 新增）

```sql
-- cut_1
-- T11a: CASE WHEN 各分支命中率（目标表视角）
SELECT
    {TARGET_FIELD}
    , COUNT(1) AS cnt
    , ROUND(COUNT(1) * 100.0 / SUM(COUNT(1)) OVER(), 2) AS pct
FROM {TABLE}
GROUP BY {TARGET_FIELD}
ORDER BY cnt DESC
```

```sql
-- cut_1
-- T11b: 源表字段实际取值分布（验证 ETL 条件能否命中）
SELECT
    {SOURCE_FIELD}
    , COUNT(1) AS cnt
    , ROUND(COUNT(1) * 100.0 / SUM(COUNT(1)) OVER(), 4) AS pct
FROM {SOURCE_TABLE}
WHERE {FILTER_CONDITIONS}
GROUP BY {SOURCE_FIELD}
ORDER BY cnt DESC
LIMIT 30
```

## T12：CTE 膨胀检测（V3 新增）

```sql
-- cut_1
-- T12a: 检测特定业务类型的主键膨胀
SELECT
    COUNT(1)                                                            AS total_rows
    , COUNT(DISTINCT {PK_FIELD})                                        AS distinct_pk
    , COUNT(1) - COUNT(DISTINCT {PK_FIELD})                             AS dup_rows
    , ROUND((COUNT(1) - COUNT(DISTINCT {PK_FIELD})) * 100.0 / COUNT(1), 2) AS dup_pct
FROM {TABLE}
WHERE {BUSINESS_TYPE_FILTER}
```

## T13：NULL 三值逻辑陷阱验证（V3 新增）

```sql
-- cut_1
-- T13a: 验证否定条件字段的 NULL 分布及业务影响
SELECT
    COUNT(1)                                                            AS total_rows
    , SUM(CASE WHEN {CONDITION_FIELD} IS NULL THEN 1 ELSE 0 END)        AS field_null_cnt
    , ROUND(SUM(CASE WHEN {CONDITION_FIELD} IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(1), 4) AS field_null_pct
FROM {TABLE}
```

## T15：CNY/原币双字段汇率换算验证（V3 新增）

```sql
-- cut_1
-- T15a: 验证 CNY 字段与原币字段是否相等（相等说明未做汇率换算）
SELECT
    COUNT(1)                                                            AS total_with_value
    , SUM(CASE WHEN {CNY_FIELD} = {ORIGINAL_FIELD} THEN 1 ELSE 0 END)  AS equal_cnt
    , SUM(CASE WHEN {CNY_FIELD} <> {ORIGINAL_FIELD} THEN 1 ELSE 0 END) AS diff_cnt
    , ROUND(SUM(CASE WHEN {CNY_FIELD} = {ORIGINAL_FIELD} THEN 1 ELSE 0 END) * 100.0 / COUNT(1), 2) AS equal_pct
FROM {TABLE}
WHERE {CNY_FIELD} IS NOT NULL AND {ORIGINAL_FIELD} IS NOT NULL
```

---

## 📄 scripts/submit_queries.py

```python
#!/usr/bin/env python3
"""
批量提交探数 SQL 并轮询结果
用法：python3 submit_queries.py --sql-dir /tmp/dq_check --project erp-dw --engine OneSQL
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def run_cmd(cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
    """执行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def submit_query(sql_file: Path, project: str, engine: str) -> str | None:
    """提交单个 SQL 文件，返回 query_id"""
    cmd = ["mtdata", "query", "submit", "-p", project, "-e", engine, str(sql_file)]
    rc, stdout, stderr = run_cmd(cmd)
    if rc != 0:
        print(f"  [ERROR] 提交失败: {stderr}", file=sys.stderr)
        return None
    for line in stdout.splitlines():
        if "query_id" in line.lower():
            parts = line.split(":")
            if len(parts) >= 2:
                return parts[-1].strip()
    try:
        data = json.loads(stdout)
        return data.get("query_id") or data.get("queryId")
    except json.JSONDecodeError:
        pass
    return None


def poll_status(query_id: str, project: str, max_wait: int = 300, interval: int = 10) -> str:
    """轮询查询状态，返回最终状态（SUCCESS/FAILED/TIMEOUT）"""
    elapsed = 0
    while elapsed < max_wait:
        cmd = ["mtdata", "query", "status", "-p", project, "-q", str(query_id)]
        rc, stdout, stderr = run_cmd(cmd)
        if rc == 0:
            status = stdout.strip().upper()
            try:
                data = json.loads(stdout)
                status = (data.get("status") or data.get("state") or "").upper()
            except json.JSONDecodeError:
                pass
            if "SUCCESS" in status or "FINISHED" in status or "DONE" in status:
                return "SUCCESS"
            elif "FAIL" in status or "ERROR" in status or "CANCEL" in status:
                return "FAILED"
        time.sleep(interval)
        elapsed += interval
    return "TIMEOUT"


def fetch_result(query_id: str, project: str, output_file: Path) -> bool:
    """获取查询结果并保存到文件"""
    cmd = ["mtdata", "query", "result", "-p", project, "-q", str(query_id)]
    rc, stdout, stderr = run_cmd(cmd)
    if rc != 0:
        return False
    output_file.write_text(stdout, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="批量提交探数 SQL 并获取结果")
    parser.add_argument("--sql-dir", required=True, help="SQL 文件目录")
    parser.add_argument("--project", "-p", default="erp-dw", help="探数项目名")
    parser.add_argument("--engine", "-e", default="OneSQL", help="执行引擎")
    parser.add_argument("--output-dir", help="结果输出目录（默认与 sql-dir 相同）")
    parser.add_argument("--max-wait", type=int, default=300, help="单个查询最大等待秒数")
    parser.add_argument("--interval", type=int, default=10, help="轮询间隔秒数")
    parser.add_argument("--pattern", default="*.sql", help="SQL 文件匹配模式")
    parser.add_argument("--parallel", action="store_true", help="并行提交所有 SQL")
    parser.add_argument("--max-workers", type=int, default=6, help="并行模式下的最大并发数")
    args = parser.parse_args()

    sql_dir = Path(args.sql_dir)
    output_dir = Path(args.output_dir) if args.output_dir else sql_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    sql_files = sorted(sql_dir.glob(args.pattern))
    if not sql_files:
        print(f"[ERROR] 在 {sql_dir} 中未找到匹配 {args.pattern} 的 SQL 文件")
        sys.exit(1)

    print(f"[INFO] 找到 {len(sql_files)} 个 SQL 文件，开始批量提交...")

    def process_one(sql_file: Path) -> dict:
        stem = sql_file.stem
        query_id = submit_query(sql_file, args.project, args.engine)
        if not query_id:
            return {"file": sql_file.name, "query_id": None, "status": "SUBMIT_FAILED"}
        status = poll_status(query_id, args.project, args.max_wait, args.interval)
        if status == "SUCCESS":
            output_file = output_dir / f"{stem}_result.csv"
            ok = fetch_result(query_id, args.project, output_file)
            if ok:
                return {"file": sql_file.name, "query_id": query_id, "status": "SUCCESS", "result": str(output_file)}
        return {"file": sql_file.name, "query_id": query_id, "status": status}

    results = []
    if args.parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {executor.submit(process_one, f): f for f in sql_files}
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    sql_file = futures[future]
                    results.append({"file": sql_file.name, "status": "EXCEPTION", "error": str(e)})
    else:
        for sql_file in sql_files:
            results.append(process_one(sql_file))

    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = len(results) - success
    print(f"\n执行汇总：成功 {success} / {len(results)}")

    summary_file = output_dir / "submit_summary.json"
    summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
```

---

# 四、requirement-analyst

## 📄 SKILL.md

```yaml
---
name: requirement-analyst
description: "数据需求分析专家，帮你把模糊的业务需求变成可开发的澄清文档。核心能力：(1) 从 PRD/MRD/FSD/学城链接/口述等任意来源提取需求，(2) 自动搜索已有指标/维度/数据表，评估复用可能性，(3) 识别口径模糊、缺失定义、时效矛盾等开发风险，(4) 生成面向业务方的选择题式澄清文档（3步极简流程：初稿→澄清→终稿），(5) 澄清完成后生成标准 MRD，可选同步到学城或创建 FSD 需求。"

metadata:
  skillhub.creator: "wangsongmian"
  skillhub.updater: "baijingwen02"
  skillhub.version: "V4"
  skillhub.skill_id: "1604"
---
```

# Requirement Analyst

**核心目标**：低门槛收集需求初稿 → 资产复用评估（可提前交付）→ 选择题式澄清 → 生成高质量 MRD

## 前置依赖

- `mtdata` CLI：缺失时跳过资产搜索，标注 `reuse: {similarity: "unknown"}`。
- `biz_id`：优先从当前工作区下的 `data-config.json` 读取；找不到时 AskQuestion 询问用户后写入。
- `citadel` skill（`oa-skills citadel` CLI）：用于读取学城文档内容和发布澄清文档到学城。

## 工作流阶段

| 阶段 | 说明 | 停止点 |
|------|------|--------|
| **Step 0** 低门槛收集 | 识别输入类型（文档/口述/FSD链接），引导补全 | 🛑 信息不足 → AskQuestion |
| **Step 1** 需求提取 | 结构化提取指标+维度，初始化 `analysis.json` | — |
| **Step 2** 资产复用 | 并行搜索指标/维度/表，评估复用度 | — |
| **Step 2.5** 提前交付判断 | similarity≥high 或能出 SQL → 询问是否满意 | 🛑 满意 → 快速交付，终止 |
| **Step 3** 深度审查 | 识别口径/时效/数据源等 blocking issues | — |
| **Step 4** 生成澄清文档 | 选择题式，≤10题，可选发布学城 | 🛑 发布前确认 |
| **Step 5** 质量自检 | 检查 High issue 覆盖、选项格式、文件完整性 | 🛑 自检通过后等待用户确认 |
| **Step 6** 接收澄清回复 | 更新 analysis.json，blocking==0 → 进 6.5 | — |
| **Step 6.5** 生成 MRD | 填充 8 大要素标准模板 | 🛑 生成后确认 |
| **Step 7** 创建 FSD 需求 | 可选，执行前询问 | 🛑 确认后执行 |

## 关键决策分支

### 资产复用提前交付（Step 2.5）
- **触发**：存在 `similarity >= high` 资产，或能拼出完整 SQL
- **行为**：展示复用摘要 → AskQuestion 满意/不满意
  - 满意 → 写 `【快速交付】{需求名}.md` + `handoff.json`（status: early_delivery），**终止**
  - 不满意 → 继续 Step 3 完整流程

### 需求收回（任意阶段）
- **触发**：用户说"收回/撤需求/不做了"
- **行为**：AskQuestion 二次确认 → 确认后写 `withdrawal.md` + `handoff.json`（status: withdrawn），**终止**

## AskQuestion 使用规范

所有需要用户决策、确认、选择的场景必须用 `AskQuestion`，禁止自行假设或跳过。

| 场景 | 要点 |
|------|------|
| biz_id 缺失 | 提供业务线选项（外卖/到店/其他） |
| 确认需求摘要 | 准确继续 / 需要修改 |
| 确认澄清文档 | 是否发布学城；发布成功后**在对话中展示 URL** |
| 资产复用满意度 | ✅满意直接交付 / ❌不满足继续 MRD |
| 确认 MRD 内容 | 确认继续 FSD / 需要修改 |
| 确认创建 FSD | 是/否；创建成功后**在对话中展示 FSD URL** |
| 需求收回确认 | 确认收回 / 取消继续 |

## 产物清单

| 产物文件 | 描述 | 路径 | 阶段 |
|---------|------|------|------|
| `【需求摘要】{需求名}.md` | 口述需求结构化整理 | `projects/{需求名}/` | Step 0 |
| `fsd_task.json` | FSD 任务结构化数据 | `projects/{需求名}/.ai/` | Step 0 |
| `analysis.json` | 唯一中间产物 | `projects/{需求名}/.ai/` | Step 1-3 |
| `【需求澄清】{需求名}.md` | 选择题式澄清文档 | `projects/{需求名}/` | Step 4 |
| `【MRD】{需求名}.md` | 标准 MRD 文档（8大要素） | `projects/{需求名}/` | Step 6.5 |
| `【快速交付】{需求名}.md` | 资产复用直接交付产物 | `projects/{需求名}/` | Step 2.5 |
| `withdrawal.md` | 需求收回记录 | `projects/{需求名}/.ai/` | 收回流程 |

## 异常处理

| 异常 | 处理 |
|------|------|
| mtdata 未安装 | 提示读取当前 agent 目录下的 `mt-data-tools/SKILL.md` |
| mtdata 超时 | 重试一次，仍失败则跳过并标记 |
| 学城链接无法访问 | AskQuestion 请用户确认或粘贴内容 |
| biz_id 缺失 | AskQuestion 询问用户 |
| FSD 链接无法访问 | AskQuestion 请用户确认权限或粘贴内容 |
| 输入信息不足 | AskQuestion 交互补全，不猜测不跳过 |

---

## 📄 references/analysis-schema.md

# analysis.json Schema (v2)

## 完整结构

```jsonc
{
  "$schema": "analysis-v2",

  "meta": {
    "source_type": "enum: fsd | km | file | text | guided",
    "source_url": "string | null",
    "source_title": "string",
    "project_name": "string",
    "biz_id": "number",
    "fsd_task_id": "string | null",
    "fsd_url": "string | null",
    "fsd_assignee": "string | null",
    "fsd_deadline": "string | null",
    "analyzed_at": "ISO8601",
    "updated_at": "ISO8601",
    "tool_chain": ["mtdata"],
    "status": "enum",
    "km_publish_url": "string | null"
  },

  "metrics": [
    {
      "id": "M-{nn}",
      "name": "string",
      "raw_define": "string",
      "clarified_define": "string | null",
      "formula": "string | null",
      "status": "enum: pending | resolved | confirmed",

      "reuse": {
        "match_kpi_id": "number | null",
        "match_kpi_name": "string | null",
        "match_kpi_code": "string | null",
        "match_define": "string | null",
        "similarity": "enum: high | medium | low | none",
        "recommendation": "enum: 直接复用 | 参考复用 | 需新建",
        "gap": "string"
      },

      "issues": [
        {
          "issue_id": "I-{nn}",
          "type": "enum: 口径模糊 | 枚举缺失 | 定义缺失 | 非功能缺失 | 数据源未知",
          "quote": "string",
          "question": "string",
          "options": ["A:xxx", "B:yyy", "C:其他______"],
          "priority": "enum: high | medium | low",
          "status": "enum: open | resolved | auto_resolved",
          "answer": "string | null",
          "resolved_by": "enum: user | knowledge | etyma | ddl | null"
        }
      ],

      "candidate_tables": [
        {
          "table": "string",
          "comment": "string",
          "relevance": "string",
          "confidence": "enum: high | medium | low",
          "verified_fields": ["string"]
        }
      ]
    }
  ],

  "dimensions": [
    {
      "id": "D-{nn}",
      "name": "string",
      "raw_define": "string",
      "enum_values": ["string"],
      "status": "enum: pending | resolved | confirmed",

      "reuse": {
        "match_dim_id": "number | null",
        "match_dim_name": "string | null",
        "similarity": "enum: high | medium | low | none",
        "note": "string"
      },

      "issues": []
    }
  ],

  "non_functional": {
    "timeliness": {
      "status": "enum: open | resolved",
      "question": "数据产出时效？",
      "options": ["A:T+1", "B:实时", "C:其他______"],
      "answer": "string | null"
    },
    "backfill": {
      "status": "enum: open | resolved",
      "question": "历史回溯范围？",
      "options": ["A:近30天", "B:近90天", "C:上线至今", "D:其他______"],
      "answer": "string | null"
    },
    "permissions": {
      "status": "enum: open | resolved",
      "question": "数据可见范围/权限？",
      "answer": "string | null"
    }
  },

  "summary": {
    "total_metrics": "number",
    "total_dimensions": "number",
    "reusable_metrics": "number",
    "new_metrics": "number",
    "open_issues": "number",
    "resolved_issues": "number",
    "auto_resolved_issues": "number",
    "blocking_issues": "number"
  }
}
```

## 状态枚举 (meta.status)

| 状态 | 说明 |
|:-----|:-----|
| `collecting` | Step 0 进行中，信息收集阶段 |
| `extracting` | Step 1 进行中，需求提取阶段 |
| `analyzing` | Step 2-3 进行中，资产复用分析与深度审查 |
| `pending_clarification` | Step 4 完成，等待业务方回复澄清 |
| `clarified` | Step 6 完成，所有阻塞问题已解决 |
| `ready_for_design` | 可进入下一阶段（数据源探查/数仓设计） |

---

## 📄 references/clarification-template.md

```markdown
# 【需求澄清】

## 1. 需求概述

**原始需求链接**: {最开始提供的MRD链接}

**需求背景**: {简要描述业务背景}

**数据用途**: {数据的具体应用场景}

---

## 2. 可复用资产确认

| 需求名称    | 建议复用的已有资产 | 相似度    | 资产说明/口径  | 您的决策 (复用/不复用) | 备注/原因 |
| :---------- | :----------------- | :-------- | :------------- | :--------------------- | :-------- |
| {原始名称1} | {已有资产名称1}    | {相似度}% | {简要口径描述} | **待确认**       |           |

---

## 3. 数据源确认

| 业务对象              | AI 推荐候选表   | 确认结果 (是/否/不确定) | 备注 |
| :-------------------- | :-------------- | :---------------------- | :--- |
| **{业务对象1}** | `{推荐表名1}` | **待确认**        |      |

---

## 4. 核心口径澄清

### 4.1 核心指标定义

**当前理解**: {系统对指标的理解}
**待确认问题**:
{具体澄清问题1}:

- [ ] {选项A}
- [ ] {选项B}
- [ ] 其他: ______

---

## 5. 异常与特殊场景 (Edge Cases)

**场景1**: {异常描述}
**处理方式**:

- [ ] {选项1}
- [ ] {选项2}

---

## 6. 交付与SLA

### 6.1 数据时效性

**产出时间要求**:

- [ ] T+1 09:00 前 (标准)
- [ ] T+1 12:00 前 (宽松)
- [ ] 实时 (分钟级)
- [ ] 其他: ______

### 6.2 历史数据回溯

**回溯范围**:

- [ ] 近1年数据
- [ ] 业务上线至今
- [ ] 仅需最新数据

### 6.3 交付形式

- [ ] 离线 Hive 表/视图
- [ ] 数据集 (BI看板)
```

---

## 📄 references/data-mrd-template.md（结构说明）

```markdown
# 1. 业务需求卡片
- **背景与目的**：{business_background}
- **数据用途**：{data_usage}
- **原始链接**：{requirement_original_link}

# 2. 核心数据需求

## 2.1 指标列表（IS_DATASET 模式）
| 指标名称 | 指标定义 | 计算逻辑 | 备注 | SQL示例(如有) |
|---------|---------|---------|----------|----------|
{metrics_table_with_mrd}

## 2.2 维度列表
| 维度名称 | 维度描述  | 备注 | SQL示例(如有) |
|---------|---------|---------|----------|
{dimensions_table_with_mrd}

## 2.3 指标维度交叉矩阵情况
{mrd_supply_metric_dim_metrix}

# 3. MRD提供SQL示例参考
{mrd_supply_sql}

# 4. 其他信息
{other-information}
```

---

## 📄 references/fsd-create-requirement.md（核心流程）

# FSD 创建 ONES 需求

通过 FSD 平台（fsd.sankuai.com）的后端 API 自动化创建 ONES 需求。采用浏览器内 `evaluate + fetch` 方式调用 API，浏览器自动携带 Cookie 登录态，无需手动传认证信息。

## 执行原则

1. **能自动拿的不问用户**：MIS、需求名称、需求描述均从上下文自动填充
2. **并行查询**：项目列表、需求集、需求分类树可在同一轮 API 调用中并发获取
3. **只问一次**：所有需要用户决策的字段一次性合并提问，不分轮
4. **默认值直接用**：技术需求(55826)、优先级高(2)、不关联团队目标(-2)、不涉及个人信息(1112660) 均直接采用

## 执行流程

### 第一步：导航 + 获取 MIS

```javascript
browser_navigate('https://fsd.sankuai.com/workbench')
const mis = document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('misId='))?.split('=')[1];
return mis;
```

### 第二步：并行拉取所有选项数据

```javascript
const [plansRes, initRes] = await Promise.all([
  fetch('/api/qa/v1/reqSchedule/plan/listRecommendedPlans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ selectedPlanIds: [], hideNotBelongProject: false })
  }).then(r => r.json()),
  fetch('/api/qa/v1/onesDetail/buildRequirementInitialData', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ mis: MIS, schedulePlanIds: null, versionId: '' })
  }).then(r => r.json())
]);
```

> ⚠️ **坑**：项目列表结构是 `data.list[].plans[]`，不是 `data.list[]`，直接 `.map` 会报错。

### 第五步：创建需求

```javascript
const body = {
  subtypeId: 55826,              // 技术需求（默认）
  priority: 2,                   // 高（默认）
  assigned: MIS,
  schedulePlanId: [PLAN_ID],
  reqGroupId: REQ_GROUP_ID,      // 必须是叶子节点！
  name: REQ_NAME,
  desc: REQ_DESC,                // HTML 格式
  userInfo: '1112660',
  tgId: [-2],
  rdMaster: MIS,
  prdStatus: 20738,
  createDxGroup: false,
  type: 'REQUIREMENT'
};
const resp = await fetch('/api/qa/v1/onesDetail/createRequirement?projectId=' + PROJECT_ID, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
  body: JSON.stringify(body)
});
```

## 默认值（无需询问用户）

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `subtypeId` | `55826` | 技术需求 |
| `priority` | `2` | 高优先级 |
| `assigned` | 当前登录 MIS | Cookie 自动获取 |
| `userInfo` | `1112660` | 不涉及个人信息 |
| `tgId` | `[-2]` | 不关联团队目标 |

## 常见错误

| 错误 | 原因 | 处理 |
|------|------|------|
| "字段 需求分类 不可选择非叶子节点数据" | `reqGroupId` 传了父级节点 | 重新从分类树选叶子节点 |
| 需求集查询返回 `[]` | `body` 里用了 `projectId` 而非 `schedulePlanId` | 改用 `schedulePlanId` 字段名 |
| 登录态过期 | Cookie 失效 | 重新导航到 FSD，提示扫码登录 |

---

## 📄 references/requirement-analysis-workflow.md（核心工作流节选）

# 需求分析与评审

## 1. 角色定义

你是一名资深数据仓库架构师。你的核心能力是**透视需求**——不仅能看懂业务想要什么，还能识别出他们**没说清楚**但对开发至关重要的细节。

## 2. 核心职责

1. **资产复用分析**：识别是否有现成指标/维度可复用，避免重复建设。
2. **风险识别**：发现模糊口径、缺失定义和不合理要求。
3. **业务澄清**：生成一份业务人员可读、可决策的澄清问题清单。

## 3. 执行策略

1. **业务导向**: 澄清文档面向的是业务方，不是开发团队。一旦出现"Hive表"、"ETL"、"Join"等技术术语，业务方会因为不理解而无法回答。
2. **证据驱动**: 每个问题都要引用文档原文。
3. **选择题优先**: 业务方时间有限，提供 [A/B/C] 选项让他们勾选，极大降低回复门槛。
4. **复用优先**: 指出可复用的已有指标，能让业务方看到数据团队的积累。

## 4. Step 2：资产复用分析

```bash
# 搜索已有指标（每个需求指标都要搜）
mtdata metric search -b <biz_id> -k <指标名>

# 对搜到的高匹配指标，拉取完整口径
mtdata metric detail <kpi_id1> <kpi_id2> ...

# 搜索已有维度
mtdata metric search-dim -b <biz_id> -k <维度名> --include-index

# 搜索候选表
mtdata table search -b <biz_id> -k <业务关键词>

# 对 Top 3 候选表验证字段是否存在
mtdata table ddl <schema.table>
```

## 5. Step 4：AskQuestion 交互式澄清

分批提问规则（按优先级分 3 批）：

| 批次 | 包含 issue 类型 | 触发条件 |
|------|----------------|---------|
| **第 1 批（P0，阻塞）** | `priority = "high"` | 有 P0 issue 时必须先问 |
| **第 2 批（P1，重要）** | `priority = "medium"` | P0 全部回答后触发 |
| **第 3 批（P2，可选）** | `priority = "low"` | P1 全部回答后触发 |

每批调用格式：

```
AskQuestion(
  title="[需求澄清 P0] {需求名} — 以下问题需要您确认后才能开始开发",
  questions=[
    {
      id: "I-01",
      prompt: "{issue.question}\n原文：「{issue.quote}」",
      input_type: "mixed",
      options: [
        { id: "A", label: "A. {选项内容}" },
        { id: "B", label: "B. {选项内容}" },
        { id: "C", label: "C. 其他（请在下方文本框补充说明）" }
      ],
      allow_multiple: false
    }
  ]
)
```

## 6. Step 6.5：生成标准 MRD 文档

MRD 8大必填要素（缺一不可）：

| 要素 | 说明 | 来源 |
|------|------|------|
| **1. 业务背景与目标** | 解决什么业务问题，衡量什么业务结果 | Step 0 收集 |
| **2. 使用场景与用户** | 谁用、何时用、用来做什么决策 | Step 0 收集 |
| **3. 指标定义** | 指标名、计算公式/口径、业务含义 | Step 1 提取 + Step 6 澄清 |
| **4. 维度定义** | 维度名、枚举值范围、拆解逻辑 | Step 1 提取 + Step 6 澄清 |
| **5. 数据样例与边界** | 正面例子（应该算）+ 反面例子（不该算） | Step 0/Step 6 收集 |
| **6. 时效与更新频率** | 实时 / T-1 / 周更，延迟容忍度 | Step 6 澄清 |
| **7. 聚合粒度与基期规则** | 聚合粒度（天/小时/用户）、环比/同比规则 | Step 6 澄清 |
| **8. 数据源说明** | 来源表/指标/API，是否需要数据同步接入 | Step 2 资产复用 + Step 6 补充 |

---

*文件生成时间：2026-04-09*
*包含 Skill 数量：4*
*总文件数：skill-quality-auditor(2) + knowledge-harvesting(6) + dw-data-quality(6) + requirement-analyst(5)*
