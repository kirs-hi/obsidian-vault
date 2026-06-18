# AppSeek 开发部署全流程

## 项目概述

AppSeek 是一个面向独立开发者的 App Store 数据分析网站，帮助 3 秒内判断一个 App 方向值不值得做。

- GitHub: https://github.com/kirs-hi/appseek
- 线上地址: https://appmarket-ivory.vercel.app
- 本地路径: `/Users/szx/Documents/catdesk/appmarket`

## 技术栈

- **框架**: [[Day4-Next.js核心|Next.js]] 16 (App Router) + React 19
- **样式**: [[Day3-Tailwind和shadcn|Tailwind]] CSS v4
- **数据库**: [[Day5-Supabase和实战项目|Supabase]]
- **图表**: Chart.js + react-chartjs-2（雷达图、折线图）
- **翻译**: MyMemory Translation API（免费，无需 key）
- **数据源**: iTunes Search / Lookup / Reviews RSS API
- **部署**: Vercel + GitHub
- **包管理**: pnpm（避免 npm bug）

## 功能模块

1. **Go/No-Go 机会评分** — 综合评分算法判断值不值得做
2. **基本信息** — 应用名、开发者、评分、价格等
3. **应用描述** — 中文翻译默认展示，"查看完整描述"展开中英双语（中文在前英文在后）
4. **五维雷达图** — 市场规模、竞争度、技术难度、盈利潜力、时机
5. **洞察分析** — 痛点分析、用户画像
6. **情绪趋势** — 折线图展示月度评价走势
7. **用户评论** — 默认展示3条，差评排序（低分+长内容优先），支持一键翻译、展开更多
8. **App Store 跳转链接**

## 开发踩坑记录

### 1. 翻译方案

最初用规则替换（简单字典查表），效果极差。最终换成 MyMemory API：

```
https://api.mymemory.translated.net/get?q={text}&langpair=en|zh-CN
```

注意事项：单次限 500 字符，需截断处理；需检测源文本是否已经是中文避免重复翻译。

### 2. SentimentChart TypeScript 报错

Chart.js 的 scriptable options 中 `ctx.parsed.y` 类型是 `number | null`，直接用会报 TS 错误。修复：用 `(ctx.parsed.y ?? 0)` 做空值合并。

### 3. 评论排序逻辑

按差评优先排序：先按评分升序（低分在前），同分时按内容长度降序（长内容优先，信息量更大）。

### 4. 描述区展示

中文翻译默认显示，"查看完整描述" 展开后平铺显示中文 + 英文，不要嵌套折叠。

## Vercel 部署流程（重点）

### 遇到的问题

1. **npm "Exit handler never called"** — Node.js 22.x + npm 的已知 bug，npm 的退出处理程序超时
2. **内网 registry 泄漏** — 公司 `~/.npmrc` 配了 `registry=http://r.npm.sankuai.com/`，pnpm 生成 lockfile 时会记录此地址，Vercel 构建服务器无法访问

### 解决方案

#### Step 1: 切换包管理器到 pnpm

在 `package.json` 中添加：

```json
"packageManager": "pnpm@9.15.4"
```

Vercel 自动检测此字段，使用 pnpm 安装依赖，完全绕开 npm。

#### Step 2: 项目 .npmrc 指定官方源

项目根目录创建 `.npmrc`：

```
registry=https://registry.npmjs.org/
```

覆盖全局的内网源配置，确保 lockfile 中记录的是公网可访问的地址。

#### Step 3: 重新生成 lockfile

```bash
rm -f package-lock.json
npx pnpm@9.15.4 install
# 验证无内网地址
grep "sankuai" pnpm-lock.yaml  # 应该无输出
```

#### Step 4: 推送 GitHub

```bash
git add -A
git commit -m "fix: switch to pnpm to resolve Vercel build"
git push origin main
```

#### Step 5: 部署到 Vercel

```bash
npx vercel --prod --yes
```

### 关键配置文件一览

```json
// package.json
{
  "name": "appseek",
  "packageManager": "pnpm@9.15.4",
  "engines": { "node": ">=18.18.0" }
}
```

```ini
# .npmrc（项目级）
registry=https://registry.npmjs.org/
```

### 网络注意事项

公司网络（美团内网）无法直接访问 `vercel.app` 域名（IP 被防火墙拦截）。访问方式：
- 手机流量 / 个人 WiFi
- 代理 / VPN
- 绑定自定义域名

## 项目结构

```
appmarket/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 全局布局、metadata
│   │   ├── page.tsx            # 首页（搜索入口）
│   │   ├── globals.css         # 全局样式（Cream Canvas 配色）
│   │   ├── app/page.tsx        # 应用详情页（所有分析模块）
│   │   ├── search/page.tsx     # 搜索结果页
│   │   └── api/
│   │       ├── app/route.ts    # 应用数据接口（含翻译、评论排序）
│   │       ├── search/route.ts # 搜索接口
│   │       ├── discover/route.ts # 发现推荐接口
│   │       └── translate/route.ts # 翻译接口（MyMemory API）
│   ├── components/
│   │   └── SentimentChart.tsx  # 情绪趋势折线图
│   └── types/
│       └── index.ts            # 类型定义
├── package.json
├── .npmrc                      # 指定官方 registry
├── pnpm-lock.yaml
├── tailwind.config.ts
└── tsconfig.json
```

## 设计风格

- **配色**: Cream Canvas（暖奶油底色 `#FFF8F0`）+ Coral 强调色（`#FF6B6B`）
- **参考**: appark.ai 的简洁分析风格
- **理念**: 信息密度高但不杂乱，差评优先展示（对独立开发者更有价值）
