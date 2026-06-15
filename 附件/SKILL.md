---
name: requirement-analyst
description: "数据需求分析专家，帮你把模糊的业务需求变成可开发的澄清文档。核心能力：(1) 从 PRD/MRD/FSD/学城链接/口述等任意来源提取需求，(2) 自动搜索已有指标/维度/数据表，评估复用可能性，(3) 识别口径模糊、缺失定义、时效矛盾等开发风险，(4) 生成面向业务方的**选择题式**澄清文档（3步极简流程：初稿→澄清→终稿），(5) 澄清完成后生成标准 MRD，可选同步到学城或创建 FSD 需求。只要用户说'帮我分析这个需求'、'看看这个 PRD'、'这个指标口径怎么定'、'帮我整理一下业务方的要求'、'我要提一个数据需求'、'帮我提需求'、'我需要一份数据'、'我想看某个指标'，就应该使用本 skill——即使用户没有提供完整文档，一句话需求也能引导完成。"

metadata:
  skillhub.creator: "wangsongmian"
  skillhub.updater: "baijingwen02"
  skillhub.version: "V4"
  skillhub.source: "FRIDAY Skillhub"
  skillhub.skill_id: "1604"
  skillhub.high_sensitive: "false"
---
# Requirement Analyst

**核心目标**：低门槛收集需求初稿 → 资产复用评估（可提前交付）→ 选择题式澄清 → 生成高质量 MRD

---

## 前置依赖

- `mtdata` CLI（来自当前 agent 的 `./mt-data-tools/SKILL.md`）：缺失时跳过资产搜索，标注 `reuse: {similarity: "unknown"}`。
- `biz_id`：优先从当前工作区下的 `data-config.json`（任意位置）读取；找不到时 AskQuestion 询问用户后写入。
- `citadel` skill（`oa-skills citadel` CLI）：用于读取学城文档内容（`getMarkdown`）和发布澄清文档到学城（`createDocument`）。使用前需确保 `@it/oa-skills` 已安装最新版本：
  ```bash
  npm list -g @it/oa-skills --depth=0 --registry=http://r.npm.sankuai.com 2>/dev/null | grep oa-skills
  # 未安装或非最新时执行：
  npm install -g @it/oa-skills@latest --registry=http://r.npm.sankuai.com
  ```
  CLI 不可用时，AskQuestion 请用户手动粘贴学城文档内容。

---

## 工作流阶段

> 完整执行细节见 `references/requirement-analysis-workflow.md`

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

**任意阶段**：用户说"取消/收回需求/不做了" → 执行**需求收回流程**（见下方）

---

## 关键决策分支

### ✨ 资产复用提前交付（Step 2.5）
- **触发**：存在 `similarity >= high` 资产，或能拼出完整 SQL
- **行为**：展示复用摘要 → AskQuestion 满意/不满意
  - 满意 → 写 `【快速交付】{需求名}.md` + `handoff.json`（status: early_delivery），**终止**
  - 不满意 → 继续 Step 3 完整流程

### ✨ 需求收回（任意阶段）
- **触发**：用户说"收回/撤需求/不做了"
- **行为**：AskQuestion 二次确认 → 确认后写 `withdrawal.md` + `handoff.json`（status: withdrawn），**终止**；不确认 → 恢复执行

---

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

---

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

---

## 异常处理

| 异常 | 处理 |
|------|------|
| mtdata 未安装 | 提示读取当前 agent 目录下的 `mt-data-tools/SKILL.md` |
| mtdata 超时 | 重试一次，仍失败则跳过并标记 |
| 学城链接无法访问 | AskQuestion 请用户确认或粘贴内容 |
| biz_id 缺失 | AskQuestion 询问用户 |
| FSD 链接无法访问 | AskQuestion 请用户确认权限或粘贴内容 |
| 输入信息不足 | AskQuestion 交互补全，不猜测不跳过 |
| FSD 创建失败 | 参考 `references/fsd-create-requirement.md` |
