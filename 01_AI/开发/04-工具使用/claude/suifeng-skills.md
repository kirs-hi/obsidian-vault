---
url: https://github.com/xiaoweidotnet/suifeng-skills
title: xiaoweidotnet/suifeng-skills
author: github.com
aliases: 
 - 
date: 2026-05-23 16:37:39
tags:

banner: "https://opengraph.githubassets.com/ed0fbfdc7a0eb1fa067310095000190f8d047aaa5f42a7123c42a4d428670907/xiaoweidotnet/suifeng-skills"
banner_icon: 🔖
---
个人常用 Claude Code 技能集合，覆盖从需求分析到测试生成的完整开发工作流。

<table><thead><tr><th>技能</th><th>用途</th><th>触发示例</th></tr></thead><tbody><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/spec-driven-development">spec-driven-development</a></td><td>在编码前生成结构化需求规格文档</td><td>"写 spec"、"设计一个功能"、"需求不清晰"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/planning-and-task-breakdown">planning-and-task-breakdown</a></td><td>将规格拆解为可执行的任务列表，含验收标准和依赖关系</td><td>"拆分任务"、"任务分解"、"创建实施计划"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/api-doc-infer">api-doc-infer</a></td><td>从产品描述、表结构等碎片化输入推断并生成完整 RESTful API 设计文档</td><td>"推断 API"、"设计接口"、"根据表结构生成 API"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/table-creation">table-creation</a></td><td>自动生成数据库建表 DDL 及对应 ORM 代码（MyBatis-Plus / MyBatis / JPA）</td><td>"建表"、"新表"、"设计表结构"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/html-to-miniprogram-page">html-to-miniprogram-page</a></td><td>将 HTML 页面设计 1:1 转换为微信小程序原生页面（Skyline 渲染器）</td><td>"转小程序"、"把网页转成 WXML"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/page-to-e2e">page-to-e2e</a></td><td>读取页面源码，生成完整的 Playwright E2E 测试</td><td>"生成 e2e 测试"、"给这个页面写测试"</td></tr><tr><td><a href="https://github.com/xiaoweidotnet/suifeng-skills/blob/main/skills/webpage-to-courseware">webpage-to-courseware</a></td><td>将网页内容转换为精美的演示 HTML（课件 / 深度解读 / 速览卡片三种模式）</td><td>"转课件"、"生成课件"、"网页转课件"</td></tr></tbody></table>

将本仓库克隆到本地，在 Claude Code 的 CLAUDE.md 中引用所需技能路径即可：

```
# CLAUDE.md
- 技能路径: /path/to/suifeng-skills/skills

```

或在 Claude Code 设置的 `skillDirectories` 中添加技能目录。

每个技能目录包含：

```
skills/<skill-name>/
├── SKILL.md          # 技能定义（frontmatter 元数据 + 流程指令）
├── references/       # 参考文档（部分技能）
├── templates/        # 模板文件（部分技能）
└── scripts/          # 辅助脚本（部分技能）


```

编码前生成结构化规格文档，确保无遗留疑问。核心原则：代码能回答的不问用户，问用户时每次只问一个问题并附带推荐默认值。输出保存至 `docs/features/[feature-name]/spec.md`。

### planning-and-task-breakdown

[](#planning-and-task-breakdown)

将规格拆解为有序任务列表，提倡垂直切片（一次完成一个完整用户流程）。每个任务含描述、验收标准、验证方法、依赖关系和影响文件。每 2-3 个任务设置检查点。

从产品描述、页面描述、数据库表结构、字段列表等碎片化输入推断出完整 API 设计。自动生成共享的 `api-common.md` 约定文件（响应结构、分页、错误码、鉴权、字段约定、金额处理）。金额统一使用分为单位的整数，避免浮点精度问题。

自动建表并生成 ORM 代码。所有表包含 `id`、`created_at`、`updated_at`、`deleted_at`、`is_deleted` 标准字段。支持 MySQL / PostgreSQL，支持 MyBatis-Plus、MyBatis、JPA/Hibernate 三种 ORM 框架。

将 HTML/CSS 设计稿转换为微信小程序页面，适配 Skyline 渲染器（glass-eeel 组件框架）。内置 HTML→WXML 标签映射、CSS→WXSS 转换、布局规则、交互模式和图标处理五份参考文档。

读取页面组件源码，生成覆盖全部可见功能的 Playwright E2E 测试。支持真实 API、Mock、混合三种数据源模式。自动构建项目画像缓存（框架、 baseURL、鉴权方式、UI 库、选择器风格等），避免硬编码。

将网页内容转换为自包含 HTML 文件（Tailwind CSS Play CDN，无需构建）。支持三种模式：课件（幻灯片式）、深度解读（长文式）、速览卡片（瀑布流式）。设计原则：文字优先、图片辅助，图表转为进度条 / 数字卡片，图片转为参考缩略图。

部分技能灵感与实现参考了以下开源项目，在此表示感谢：

*   [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — Claude Code 最佳实践与技巧合集
*   [agent-skills](https://github.com/addyosmani/agent-skills) — Addy Osmani 的 AI Agent 技能集合
*   [skills](https://github.com/mattpocock/skills) — Matt Pocock 的 Claude Code 技能库

MIT