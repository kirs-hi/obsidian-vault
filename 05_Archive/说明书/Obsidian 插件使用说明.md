---
date: 2026-03-07
tags: [工具, Obsidian, 插件]
---

# Obsidian 插件使用说明

## 插件总览

| 插件 | 版本 | 用途 |
|------|------|------|
| obsidian-git | - | 自动同步笔记到 GitHub |
| PDF++ | 0.40.31 | PDF 标注与双向链接 |
| share-note | - | 笔记分享 |
| Dataview | 0.5.68 | 笔记数据库查询 |
| Templater | 2.18.1 | 高级模板引擎 |
| Calendar | 1.5.10 | 日历侧边栏 |

---

## 1. PDF++

PDF++ 是 Obsidian 原生的 PDF 标注增强插件，核心能力是通过双向链接为 PDF 添加高亮注释，所有注释以 Markdown 形式保存，不修改 PDF 原文件。

### 配置要点

- **PDF 编辑模式已关闭**：避免直接修改 PDF 文件导致损坏风险
- **面板布局**：PDF 在右侧打开，笔记在左侧打开，左手记录右手阅读
- **高亮颜色**：Yellow（普通标注）、Red（重要）、Note（蓝色笔记）、Important（紫色关键）
- **自动创建笔记**：首次为某 PDF 做注释时，自动在 `读书/` 文件夹下创建同名 Markdown 笔记
- **笔记模板**：自动带上 YAML 头部的 PDF 链接和标题（模板位于 `读书/pdf-note-template.md`）
- **嵌入和悬浮预览中可见高亮**

### 使用方法

1. 把 PDF 文件放到 vault 中（建议放在 `attachments/pdf/` 下），在 Obsidian 中点击打开
2. 阅读时用鼠标选中要标注的文字，按快捷键（建议在 设置 → 快捷键 中给 `PDF++: Copy link to selection or annotation` 设置一个，比如 `Cmd + Shift + H`）
3. 第一次使用时，插件会自动在 `读书/` 下创建对应笔记并在左侧打开，之后每次标注会自动追加到笔记中
4. 工具栏上方有颜色选择器，可以切换不同颜色的高亮
5. 在笔记中点击注释链接 → PDF 跳转到对应位置；在 PDF 中双击高亮 → 跳转到笔记对应位置
6. 按住 `Cmd` 拖动鼠标可以框选 PDF 中的区域（如图表），生成区域嵌入链接
7. 选中文字后右键可以选择不同的复制格式：Quote（引用）、Callout（标注卡片）、Embed（嵌入）

---

## 2. Dataview

Dataview 可以把笔记当作数据库来查询，语法叫 DQL，类似 SQL。

### 配置要点

- 已开启 DataviewJS（支持 JavaScript 复杂查询）
- 已开启行内查询（前缀 `=`）
- 日期格式：`yyyy-MM-dd`
- YAML 属性美化渲染已开启

### 使用方法

在任意笔记中插入代码块，语言标记为 `dataview`，即可编写查询。

**列出所有读书笔记：**

```dataview
TABLE 作者, 状态, date
FROM #读书笔记
SORT date DESC
```

**列出最近 7 天修改过的文件：**

```dataview
TABLE file.mtime AS 修改时间
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
LIMIT 20
```

**统计各文件夹的笔记数量：**

```dataview
TABLE length(rows) AS 数量
FROM ""
GROUP BY file.folder
SORT length(rows) DESC
```

**行内查询：** 在正文中写 `` `= date(today)` `` 会直接渲染成今天的日期。

### DQL 常用语法速查

| 语法 | 说明 | 示例 |
|------|------|------|
| `TABLE` | 表格输出 | `TABLE author, date FROM #tag` |
| `LIST` | 列表输出 | `LIST FROM "读书"` |
| `TASK` | 任务列表 | `TASK FROM "项目"` |
| `FROM` | 数据来源 | `FROM #标签` 或 `FROM "文件夹"` |
| `WHERE` | 过滤条件 | `WHERE status = "在读"` |
| `SORT` | 排序 | `SORT date DESC` |
| `GROUP BY` | 分组 | `GROUP BY file.folder` |
| `LIMIT` | 限制数量 | `LIMIT 10` |
| `FLATTEN` | 展开数组 | `FLATTEN tags` |

---

## 3. Templater

Templater 是比 Obsidian 自带模板更强大的模板引擎，支持日期变量、文件信息、JavaScript 脚本等。

### 配置要点

- 模板文件夹：`Templates/`
- 已开启语法高亮和自动跳转光标
- 已创建三个模板：日记模板、读书笔记模板、会议记录模板

### 已有模板

**日记模板**（`Templates/日记模板.md`）：自动填充日期，包含今日计划、工作记录、学习笔记、随想四个板块。

**读书笔记模板**（`Templates/读书笔记模板.md`）：包含书名、作者、阅读状态等 YAML 属性，以及核心观点、读书摘录、我的思考板块。

**会议记录模板**（`Templates/会议记录模板.md`）：包含参会人、会议背景、讨论要点、结论与待办。

### 使用方法

1. 新建一个笔记
2. 按 `Cmd + P` 打开命令面板，输入 `Templater`，选择 `Insert Template`
3. 选择要使用的模板，模板中的变量会自动替换为实际值

### 常用变量速查

| 变量 | 说明 | 示例输出 |
|------|------|----------|
| `2026-03-23` | 当前日期 | 2026-03-07 |
| `2026-03-23 星期一` | 日期+星期 | 2026-03-07 Friday |
| `2026-03-24` | 明天日期 | 2026-03-08 |
| `2026-03-22` | 昨天日期 | 2026-03-06 |
| `README` | 当前文件标题 | 我的笔记 |
| `2026-03-23 10:31` | 文件创建日期 | 2026-03-07 |
| `<% tp.file.cursor() %>` | 插入后光标位置 | （光标停在此处） |

### 自定义模板

在 `Templates/` 文件夹中新建 `.md` 文件即可添加自己的模板，使用上述变量语法。

---

## 4. Calendar

Calendar 在侧边栏提供月历视图，点击日期即可快速创建或跳转到当天的日记。

### 配置要点

- 一周从周一开始
- 点击日期直接创建日记（无确认弹窗）
- 日记存放路径：`CatPaw记忆/daily/`
- 日记文件名格式：`YYYY-MM-DD`
- 新建日记自动套用 `Templates/日记模板`

### 使用方法

1. 点击右侧边栏的日历图标，或按 `Cmd + P` 搜索 `Calendar: Open view`
2. 月历面板中，点击某一天：已有日记则直接打开，没有则自动创建并套用日记模板
3. 日历上有小圆点的日期表示那天有日记，圆点越大说明写的内容越多
4. 点击月历顶部的左右箭头可以切换月份

---

## Vault 目录结构

```
笔记/
├── Templates/              ← Templater 模板文件夹
│   ├── 日记模板.md
│   ├── 读书笔记模板.md
│   └── 会议记录模板.md
├── CatPaw记忆/daily/       ← Calendar 日记存放位置
├── 读书/                   ← PDF++ 读书笔记存放位置
│   └── pdf-note-template.md
├── attachments/pdf/        ← PDF 文件存放位置
├── 工具使用说明/            ← 本文件所在位置
├── Clippings/              ← 网页剪藏
├── 小红书/                 ← 小红书内容创作
└── 简历/
```
