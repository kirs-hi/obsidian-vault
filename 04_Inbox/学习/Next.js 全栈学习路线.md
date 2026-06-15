---
name: Next.js 全栈学习路线
description: 基于《内功7：Next.JS》优化重组的学习路线，去重+补实践+按知识依赖排序，覆盖环境搭建、路由、组件、数据获取、优化、渲染策略到实战项目全流程
created: 2026-04-28
tags:
  - 全栈
  - Next.js
  - React
  - 学习路线
---

# Next.js 全栈学习路线（优化版）

> 基于《内功7：Next.JS（非常重要）》重新梳理，去除重复内容，补充动手实践，按知识依赖关系重新排序。
>
> 目标：系统掌握 Next.js 全栈开发能力，能独立从零构建并部署一个完整的 Web 应用。

---

## 前置知识检查

开始之前，确保你对以下内容不陌生。不需要精通，但至少能看懂基本代码：

- **HTML / CSS 基础**：标签、选择器、盒模型、Flexbox
- **JavaScript 基础**：变量、函数、箭头函数、数组方法（map/filter）、async/await、解构赋值
- **React 基础**：JSX 语法、组件、props、useState、useEffect

如果 React 完全没接触过，建议先花 2-3 小时过一遍 [React 官方教程](https://react.dev/learn)，否则后面会很吃力。

---

## 第一阶段：环境搭建 + 项目结构（2小时）

### 1.1 三者关系：Node.js / npm / Next.js

先搞清楚这三个东西分别是什么：

| 概念 | 是什么 | 类比 |
|------|--------|------|
| **Node.js** | JavaScript 的运行环境，让 JS 能跑在服务器上 | 地基 |
| **npm** | 包管理工具，安装和管理第三方库 | 建材商店 |
| **Next.js** | 基于 React 的全栈框架，提供路由、SSR、API 等能力 | 预制房屋设计方案 |

安装顺序：Node.js（自带 npm）→ 用 npm/npx 创建 Next.js 项目。

### 1.2 创建第一个项目

```bash
npx create-next-app@latest my-app
cd my-app
npm run dev
```

创建时的选项全部选默认即可。启动后打开 http://localhost:3000/ 查看效果。

### 1.3 理解项目结构

```
├── app/                # 核心：所有页面和路由都在这里
│   ├── layout.tsx      # 根布局，所有页面共享的外壳
│   ├── page.tsx        # 首页，访问 / 时渲染
│   └── globals.css     # 全局样式
├── public/             # 静态资源（图片、图标等），可通过 URL 直接访问
├── package.json        # 项目依赖和脚本配置
├── tsconfig.json       # TypeScript 配置
└── tailwind.config.ts  # Tailwind CSS 配置
```

重点记住两个文件夹：**app/**（代码逻辑）和 **public/**（静态资源）。

### 1.4 两个常用命令

| 命令 | 用途 | 场景 |
|------|------|------|
| `npm run dev` | 启动开发服务器，支持热重载 | 开发时用 |
| `npm run build` | 构建生产版本，代码压缩优化 | 部署前用 |

### ✅ 动手练习

1. 创建项目并启动
2. 打开 `app/page.tsx`，把内容改成一句 "Hello Next.js"，保存后观察浏览器自动刷新
3. 在 `public/` 下放一张图片，在浏览器通过 `http://localhost:3000/图片名` 直接访问

---

## 第二阶段：路由系统（3小时）

Next.js 最核心的设计：**文件即路由，文件夹即层级**。

### 2.1 基础路由

在 `app/` 下创建文件夹 + `page.tsx` = 一个新页面：

```
app/
├── page.tsx              → /
├── about/
│   └── page.tsx          → /about
├── blog/
│   └── page.tsx          → /blog
```

每个 `page.tsx` 导出一个 React 组件，就是这个路由的页面内容：

```tsx
// app/about/page.tsx
export default function AboutPage() {
  return <h1>关于我们</h1>;
}
```

### 2.2 嵌套路由

文件夹可以无限嵌套：

```
app/about/projects/page.tsx  → /about/projects
```

### 2.3 动态路由

用方括号 `[]` 创建动态路由段：

```
app/blog/[slug]/page.tsx  → /blog/任意值
```

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({ params }: { params: { slug: string } }) {
  const { slug } = await params;
  return <h1>文章: {slug}</h1>;
}
```

访问 `/blog/hello-world` 时，`slug` 的值就是 `"hello-world"`。

### 2.4 布局系统（Layout）

`layout.tsx` 是页面的"外壳"，子路由的内容通过 `{children}` 插入：

```tsx
// app/layout.tsx（根布局）
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body>
        <nav>导航栏（所有页面共享）</nav>
        <main>{children}</main>
        <footer>页脚（所有页面共享）</footer>
      </body>
    </html>
  );
}
```

布局的关键特性：切换页面时布局不会重新渲染，只有 `{children}` 部分更新。

你也可以在子文件夹中创建 `layout.tsx`，实现嵌套布局：

```
app/
├── layout.tsx              # 根布局（导航栏 + 页脚）
├── dashboard/
│   ├── layout.tsx          # dashboard 专属布局（侧边栏）
│   ├── page.tsx            # /dashboard
│   └── settings/
│       └── page.tsx        # /dashboard/settings
```

### ✅ 动手练习

1. 创建 `/about`、`/blog`、`/contact` 三个页面
2. 创建 `/blog/[slug]` 动态路由，在页面上显示当前 slug 值
3. 在根 `layout.tsx` 中添加一个简单的导航栏，包含到各页面的链接
4. 为 `/dashboard` 创建一个带侧边栏的嵌套布局

---

## 第三阶段：组件体系（4小时）

### 3.1 服务端组件 vs 客户端组件

这是 Next.js 最重要的概念之一：

| | 服务端组件（默认） | 客户端组件 |
|---|---|---|
| 声明方式 | 不需要任何声明 | 文件顶部加 `"use client"` |
| 运行位置 | 服务器上 | 浏览器中 |
| 能做什么 | 直接访问数据库、读文件、调 API | 处理用户交互、使用 useState/useEffect |
| 不能做什么 | 不能用 useState、onClick 等浏览器 API | 不能直接访问数据库、文件系统 |
| 输出 | 纯 HTML，体积小 | 包含 JavaScript，支持交互 |

**原则：默认用服务端组件，只在需要用户交互时才用客户端组件。**

### 3.2 服务端组件示例

```tsx
// app/users/page.tsx（服务端组件，默认）
export default async function UsersPage() {
  const res = await fetch("https://jsonplaceholder.typicode.com/users");
  const users = await res.json();

  return (
    <ul>
      {users.map((u: any) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}
```

注意：组件函数可以直接用 `async/await`，这在客户端组件中做不到。

### 3.3 客户端组件示例

```tsx
// components/Counter.tsx
"use client";
import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount(count + 1)}>
      点击了 {count} 次
    </button>
  );
}
```

### 3.4 组件组合：服务端包客户端

最佳实践是让服务端组件作为容器，客户端组件只负责交互部分：

```tsx
// app/page.tsx（服务端组件）
import Counter from "@/components/Counter"; // 客户端组件

export default async function Home() {
  const data = await fetch("https://api.example.com/data").then(r => r.json());

  return (
    <div>
      <h1>{data.title}</h1>          {/* 服务端渲染，SEO 友好 */}
      <p>{data.description}</p>       {/* 服务端渲染 */}
      <Counter />                     {/* 客户端交互 */}
    </div>
  );
}
```

### 3.5 Props 传递

```tsx
// components/Greeting.tsx
type GreetingProps = {
  name: string;
};

export default function Greeting({ name }: GreetingProps) {
  return <h1>Hello, {name}!</h1>;
}

// 使用时
<Greeting name="Alice" />
<Greeting name="Bob" />
```

### ✅ 动手练习

1. 创建一个服务端组件，从 `https://jsonplaceholder.typicode.com/posts` 获取数据并展示文章列表
2. 创建一个客户端组件 `LikeButton`，点击后数字 +1
3. 把两者组合：文章列表（服务端）+ 每篇文章旁边一个点赞按钮（客户端）
4. 创建一个可复用的 `Card` 组件，接收 `title` 和 `content` 两个 props

---

## 第四阶段：数据获取（3小时）

### 4.1 服务端数据获取（推荐）

在服务端组件中直接 `fetch`，支持缓存控制：

```tsx
// 默认：自动缓存（类似 SSG）
const res = await fetch("https://api.example.com/data");

// 不缓存，每次请求都重新获取（SSR）
const res = await fetch("https://api.example.com/data", { cache: "no-store" });

// 定时重新验证（ISR），60秒后过期
const res = await fetch("https://api.example.com/data", { next: { revalidate: 60 } });
```

### 4.2 客户端数据获取

在客户端组件中，用 `useEffect` 或 SWR 库：

```tsx
"use client";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then(r => r.json());

export default function Profile() {
  const { data, error, isLoading } = useSWR("/api/profile", fetcher);

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>加载失败</div>;
  return <h1>{data.name}</h1>;
}
```

### 4.3 API 路由（Route Handlers）

Next.js 可以直接写后端 API，在 `app/api/` 下创建 `route.ts`：

```tsx
// app/api/hello/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ message: "Hello from API" });
}

export async function POST(request: Request) {
  const body = await request.json();
  return NextResponse.json({ received: body });
}
```

访问 `http://localhost:3000/api/hello` 就能调到这个接口。这就是 Next.js 的全栈能力——前后端写在同一个项目里。

### ✅ 动手练习

1. 创建一个 API 路由 `/api/todos`，返回一个 JSON 格式的待办事项列表
2. 在服务端组件中 fetch 这个 API 并展示列表
3. 创建一个客户端组件，用 SWR 获取同一个 API 的数据（对比两种方式的区别）
4. 给 fetch 加上 `revalidate: 10`，观察缓存行为

---

## 第五阶段：内置优化（2小时）

Next.js 把很多性能优化做成了开箱即用的组件，直接用就行。

### 5.1 Image 组件

```tsx
import Image from "next/image";

<Image
  src="/banner.jpg"
  alt="首页横幅"
  width={1200}
  height={400}
  priority              // 首屏图片加 priority
  placeholder="blur"    // 模糊占位
/>
```

自动做了什么：格式转换（WebP/AVIF）、响应式裁切、懒加载。

### 5.2 Link 组件

```tsx
import Link from "next/link";

<Link href="/about">关于我们</Link>
```

自动做了什么：预取目标页面（链接进入视口时就开始下载），点击时无刷新跳转。

### 5.3 字体优化

```tsx
// app/layout.tsx
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh" className={inter.className}>
      <body>{children}</body>
    </html>
  );
}
```

自动做了什么：字体文件按需子集化，预加载，无闪烁。

### 5.4 元数据与 SEO

```tsx
// 静态元数据
export const metadata = {
  title: "我的网站",
  description: "这是一个 Next.js 网站",
};

// 动态元数据（用于动态路由）
export async function generateMetadata({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  return {
    title: post.title,
    description: post.excerpt,
  };
}
```

### ✅ 动手练习

1. 把项目中所有 `<img>` 替换为 `<Image>`，所有 `<a>` 替换为 `<Link>`
2. 配置 Google 字体，应用到全局
3. 为首页和文章详情页分别设置静态/动态元数据

---

## 第六阶段：渲染策略 + 高级特性（4小时）

### 6.1 四种渲染策略

| 策略 | 特点 | 适用场景 | 实现方式 |
|------|------|----------|----------|
| **SSG**（静态生成） | 构建时生成 HTML，最快 | 博客、文档、营销页 | 默认行为 |
| **SSR**（服务端渲染） | 每次请求实时渲染 | 仪表盘、个性化内容 | `cache: "no-store"` |
| **ISR**（增量静态再生成） | 静态页面定时更新 | 电商产品页、新闻 | `next: { revalidate: N }` |
| **CSR**（客户端渲染） | 浏览器中渲染 | 纯交互组件 | `"use client"` + useEffect |

### 6.2 Streaming 与 Suspense

不用等所有数据加载完才显示页面，可以分块流式渲染：

```tsx
import { Suspense } from "react";

export default function Dashboard() {
  return (
    <div>
      <h1>控制面板</h1>
      <Suspense fallback={<div>加载用户信息中...</div>}>
        <UserProfile />
      </Suspense>
      <Suspense fallback={<div>加载活动记录中...</div>}>
        <RecentActivity />
      </Suspense>
    </div>
  );
}
```

`UserProfile` 先加载完就先显示，`RecentActivity` 慢一点也不会阻塞整个页面。

### 6.3 动态导入

按需加载重量级组件，减小首屏包体积：

```tsx
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("../components/HeavyChart"), {
  loading: () => <p>加载图表中...</p>,
  ssr: false,  // 这个组件只在浏览器中渲染
});
```

### 6.4 中间件

在请求到达页面之前拦截处理，常用于鉴权、重定向：

```tsx
// middleware.ts（项目根目录）
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const isLoggedIn = request.cookies.get("token");

  if (request.nextUrl.pathname.startsWith("/dashboard") && !isLoggedIn) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
```

### 6.5 环境变量

```bash
# .env.local
DATABASE_URL=postgres://user:password@localhost:5432/mydb    # 仅服务端可用
NEXT_PUBLIC_API_URL=http://localhost:3000/api                 # 客户端也可用
```

规则：`NEXT_PUBLIC_` 前缀的变量会暴露给浏览器，其他的只在服务端可用。敏感信息（密钥、数据库密码）绝对不要加 `NEXT_PUBLIC_` 前缀。

### 6.6 边缘运行时

轻量级运行环境，部署在离用户最近的节点，响应更快：

```tsx
// app/api/edge/route.ts
export const runtime = "edge";

export async function GET() {
  return new Response(JSON.stringify({ message: "来自边缘节点" }), {
    headers: { "content-type": "application/json" },
  });
}
```

### ✅ 动手练习

1. 创建一个 dashboard 页面，用 Suspense 包裹三个异步数据组件，观察流式加载效果
2. 用 `dynamic` 动态导入一个组件，在 Network 面板观察代码分割
3. 写一个中间件，未登录用户访问 `/dashboard` 时重定向到 `/login`
4. 创建 `.env.local` 文件，在 API 路由中读取环境变量

---

## 第七阶段：实战项目（持续）

### 7.1 入门项目：个人博客

把前面学的所有知识串起来：

- 首页（文章列表，SSG）
- 文章详情页（动态路由 + ISR）
- 关于页面（静态页面）
- API 路由（提供文章数据）
- 全局布局（导航栏 + 页脚）
- Image / Link / Font 优化
- 元数据 SEO

### 7.2 进阶项目：全栈应用

在博客基础上加入：

- 用户认证（中间件 + Cookie）
- 数据库集成（Prisma + PostgreSQL 或 SQLite）
- 表单提交（Server Actions）
- 部署到 Vercel

### 7.3 推荐学习资源

| 资源 | 预计时间 | 说明 |
|------|----------|------|
| [Next.js 官方教程](https://nextjs.org/learn/) | 10 小时 | 最好的入门教程，跟着做一遍 |
| [YouTube 视频教程](https://www.youtube.com/watch?v=b4ba60j_4o8&list=PLC3y8-rFHvwhIEc4I4YsRz5C7GOBnxSJY) | 20 小时 | 详细讲解每个概念 |
| [Next.js 官方文档](https://nextjs.org/docs) | 随查随用 | 权威参考 |
| [Vercel 示例库](https://github.com/vercel/next.js/tree/canary/examples) | 随查随用 | 各种场景的代码示例 |

---

## 知识地图

```
Next.js 全栈知识体系
│
├── 基础层
│   ├── 项目结构（app/ + public/）
│   ├── 路由系统（文件路由 + 动态路由 + 嵌套路由）
│   └── 布局系统（layout.tsx + 嵌套布局）
│
├── 组件层
│   ├── 服务端组件（默认，async/await 直接取数据）
│   ├── 客户端组件（"use client"，处理交互）
│   └── 组件组合（服务端包客户端）
│
├── 数据层
│   ├── 服务端 fetch（缓存 / no-store / revalidate）
│   ├── 客户端 fetch（useEffect / SWR）
│   └── API 路由（Route Handlers）
│
├── 优化层
│   ├── Image / Link / Font 组件
│   ├── 元数据与 SEO
│   └── 动态导入（代码分割）
│
├── 高级层
│   ├── 渲染策略（SSG / SSR / ISR / CSR）
│   ├── Streaming + Suspense
│   ├── 中间件（鉴权、重定向）
│   ├── 环境变量
│   └── 边缘运行时
│
└── 实战层
    ├── 个人博客（入门）
    └── 全栈应用（进阶）
```
