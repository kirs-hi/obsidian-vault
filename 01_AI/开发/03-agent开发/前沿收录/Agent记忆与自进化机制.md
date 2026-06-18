

## 1. Hermes 记忆系统架构

### 1.1 六层记忆模型

Hermes 的[[理论学习_跨会话记忆与会话持久化|记忆系统]]分为 6 层，前 4 层和 [[00_OpenClaw_MOC|OpenClaw]] 基本类似，后 2 层是 Hermes 特有的：

**第一层：Bootstrap Files**
- 包含：AGENTS.md、SOUL.md、USER.md
- 特点：启动时必须加载的核心人格/身份信息
- 不可被任何后续操作修改
- 类比：系统固件

**第二层：Session Transcript**
- 完整的对话历史记录
- 不可主动修改/删除内容
- 类比：黑匣子飞行记录

**第三层：Context Window**
- 经过压缩/筛选后实际送给模型的上下文
- 会被 Compaction 策略动态管理
- 类比：工作台上当前摊开的资料

**第四层：Retrieval Index**
- memory 文件持久化存储的内容
- [[07-Agent|Agent]] 主动写入 memory/YYYY-MM-DD.md
- 支持按需检索召回
- 类比：档案柜

**第五层：Skill Library（Hermes 特有）**
- 存放已学会的技能定义
- 以 SKILL.md 格式的文件存储
- 下次遇到类似任务时可直接调用
- 类比：工具箱

**第六层：Honcho User Model（Hermes 特有）**
- 跨 session 的用户画像模型
- 一个独立的、持久的"用户理解"模型
- 整合所有对用户的认知
- 类比：CRM 客户档案

### 1.2 记忆写入策略

| 层级 | 写入方式 | 频率 |
|------|------|------|
| Bootstrap | 系统初始化时一次性加载 | 仅一次 |
| Session Transcript | 每轮对话自动追加 | 实时 |
| Context Window | Compaction 后重建 | 周期性 |
| Retrieval Index | Agent 主动调用写入 | 按需 |
| Skill Library | 自进化循环触发 | 低频 |
| Honcho User Model | session 结束后更新 | 低频 |

### 1.3 记忆淘汰与压缩

**Pre-Compaction Memory Flush（OpenClaw）**
- 压缩前将 Agent 打算留下的内容写入 memory/YYYY-MM-DD.md
- 用户不可见（NO_REPLY）
- 触发条件：上下文窗口即将溢出时

**Hermes 自进化 Compaction**
- 在压缩之上多走一步——不仅 flush 到 memory，还会先检索自进化信息
- 判断"这次我有没有新 [[skill]] 要写"（见 11.4.4）

---

## 2. 自进化循环详解

### 2.1 核心思路

"Like back propagation but for prompts instead of model weights"

- 像反向传播，但更新的不是模型权重
- 而是 Agent 行为的指标和流程
- 更新目标：memory（学到的知识）、Skill Library（新的技能）、Honcho（用户偏好）

### 2.2 触发机制

- 每约 30 次工具调用时触发一次
- Agent 会暂停，回顾刚才做了什么
- 磁化为持久记忆，从而获得用户画像提升

### 2.3 执行流程

```
1. 用户下发任务（随任序排等）
      ↓
2. Agent 执行（Think → Act → 结果）
      ↓
3. 每 ~15 次 tool call，Agent 触发自省（periodic range）
      ↓
4. 自动学习回路：
   (1) 反思：刚才的行为有哪些做得好/不好？
   (2) 是否有可复用的模式？比如某个 skill？
      ↓
5. 持久化写入：
   - 日常记忆 → memory/YYYY-MM-DD.md（进入 Retrieval Index）
   - 技能发现 → skills/new/SKILL.md（进入 Skill Library）
   - 用户偏好 → Honcho User Model（跨session用户画像）
      ↓
6. 下次遇到类似任务时，直接调用 skill，提升效率
```

### 2.4 Skill 的自我发现

- Skill 不是一次性生成就固化了
- 自进化循环中会分析特性
- 如果 Hermes 高频发现某个任务重复出现，会自动：
  - 新建 skill（creating）
  - 或更新已有 skill（updating）
- 核心原则：渐进式能力积累，而非一次性穷举

### 2.5 与 OpenClaw Pre-Compaction Flush 对比

| 维度 | OpenClaw Pre-Compaction Flush | Hermes 自进化循环 |
|------|------|------|
| 触发时机 | 压缩机制触发时一次 | 每 ~15 次 tool call 时 |
| 性质 | 被动存档 | 主动进化 |
| 更新范围 | 只有 memory/YYYY-MM-DD.md | memory + skill + Honcho 三路 |
| 写入内容 | "我做了什么、学到了什么" | "学到的 + 失败经验 + 用户偏好" |

**一句话区分**：OpenClaw 只是被动存档，Hermes 是持续反馈进化。可以认为"自进化循环 ≥ Pre-Compaction Flush"。

---

## 3. 记忆系统设计原则

### 3.1 分层存储

- 热数据（Context Window）：高频访问，容量有限
- 温数据（Retrieval Index）：按需召回
- 冷数据（Skill Library / Honcho）：低频更新但长期有效

### 3.2 信息密度优先

- 压缩时保留高信息密度内容
- 否定性约束（"不要用 Redis"）最容易在压缩中丢失
- 关键约束应作为 structured data 单独保留

### 3.3 失败模式记忆

- 记录失败的尝试和原因
- 避免重复犯错
- 类比：DQC 规则库（历史踩坑沉淀为质量校验规则）

---

## 4. 知识更新全景图

| 记忆层 | 写入方式 | 动态策略 |
|------|------|------|
| Bootstrap Files | Read/Load once，启动时自动读取 | Cache Strategy + Read Strategy |
| Session Transcript | 每轮对话自动追加 | Compaction Strategy |
| Context Window | Compaction 后 append（约15 call后） | Write Strategy + Compaction Strategy |
| Retrieval Index | Agent 主动 File audit / MFT 写入 | Write Strategy + Read Strategy |
| Skill Library | 低频 / 自进化触发写入 | Auto Evolve Transition |
| Honcho User Model | session 结束后 / 低频 | Session/Long Mapping |
