---
name: Day4 Next.js核心
description: 学习最重要的全栈框架，理解路由、组件、数据获取和渲染策略
---

# Day 4：Next.js 核心（最重要的一天）

> 今天的目标：能用 Next.js 搭建一个多页面应用，理解路由、组件、数据获取的工作方式。

## 一、Next.js 是什么？

前三天你学了 HTML（骨架）、JS（交互）、Tailwind（样式）。但要做一个真正的网站，你还需要一个**框架**来把这些东西组织起来——路由怎么走、页面怎么加载、数据从哪来……这就是 Next.js 干的事。

用盖房子的比喻：
- **Node.js** = 地基（让 JS 能在电脑上运行，而不仅仅在浏览器里）
- **npm** = 建材商店（需要什么工具、库，用 npm 安装）
- **Next.js** = 整栋楼的设计图纸（房间怎么划分、电梯怎么走、水电怎么布）

## 二、创建你的第一个 Next.js 项目

### 2.1 环境准备

确保电脑上装了 Node.js（在终端输入 `node -v` 能看到版本号就行）。

```bash
# 创建项目（一路回车选默认）
npx create-next-app@latest my-first-app

# 进入项目
cd my-first-app

# 启动开发服务器
npm run dev
```

然后打开浏览器访问 http://localhost:3000 ，看到页面就成功了！

> 💡 `npm run dev` 启动的是**开发模式**，你改代码后页面会自动刷新（热更新）。按 `Ctrl + C` 停止服务。

### 2.2 项目结构（只需要关注这几个）

```
my-first-app/
├── app/                  ← 🔥 核心！所有页面都在这里
│   ├── layout.tsx        ← 根布局（所有页面共享的外壳）
│   ├── page.tsx          ← 首页（访问 / 时显示）
│   └── globals.css       ← 全局样式
├── public/               ← 静态资源（图片、图标等）
├── package.json          ← 项目依赖清单
└── tailwind.config.ts    ← Tailwind 配置
```

**核心口诀：文件 = 路由，文件夹 = 层级，layout 包壳 page。**

## 三、路由系统（文件系统路由）

Next.js 最优雅的设计：**你创建的文件夹结构，就是网站的 URL 结构。** 不需要任何路由配置。

### 3.1 基本路由

```
app/
├── page.tsx              → http://localhost:3000/
├── about/
│   └── page.tsx          → http://localhost:3000/about
├── blog/
│   └── page.tsx          → http://localhost:3000/blog
└── contact/
    └── page.tsx          → http://localhost:3000/contact
```

创建一个 About 页面，只需要：

```bash
# 创建文件夹和文件
mkdir -p app/about
```

然后在 `app/about/page.tsx` 里写：

```tsx
export default function AboutPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">关于我</h1>
      <p className="mt-4 text-gray-600">这是关于页面。</p>
    </div>
  )
}
```

访问 http://localhost:3000/about 就能看到了！

### 3.2 嵌套路由

文件夹可以嵌套，URL 也会跟着嵌套：

```
app/
└── blog/
    ├── page.tsx                → /blog
    └── my-first-post/
        └── page.tsx            → /blog/my-first-post
```

### 3.3 动态路由（用方括号）

有些 URL 里有动态部分，比如 `/blog/123`、`/blog/456`，用 `[参数名]` 文件夹实现：

```
app/
└── blog/
    └── [id]/
        └── page.tsx            → /blog/任意id
```

```tsx
// app/blog/[id]/page.tsx
export default function BlogPost({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">文章编号：{params.id}</h1>
    </div>
  )
}
```

访问 `/blog/123` 会显示「文章编号：123」，访问 `/blog/hello` 会显示「文章编号：hello」。

## 四、布局系统（Layout）

### 4.1 根布局

`app/layout.tsx` 是所有页面的「外壳」，导航栏、页脚这些所有页面共享的元素放这里：

```tsx
// app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>
        {/* 导航栏 - 所有页面都能看到 */}
        <nav className="bg-gray-800 text-white p-4">
          <div className="max-w-4xl mx-auto flex gap-6">
            <a href="/" className="hover:text-blue-300">首页</a>
            <a href="/about" className="hover:text-blue-300">关于</a>
            <a href="/blog" className="hover:text-blue-300">博客</a>
          </div>
        </nav>

        {/* 子页面内容会插到这里 */}
        <main className="max-w-4xl mx-auto p-4">
          {children}
        </main>

        {/* 页脚 */}
        <footer className="text-center text-gray-500 p-8">
          © 2026 我的网站
        </footer>
      </body>
    </html>
  )
}
```

`{children}` 就是当前访问的页面内容。访问 `/` 时，children 是首页；访问 `/about` 时，children 是关于页。导航栏和页脚始终在。

### 4.2 嵌套布局

每个文件夹也可以有自己的 `layout.tsx`，实现嵌套布局：

```
app/
├── layout.tsx          ← 根布局（导航 + 页脚）
└── blog/
    ├── layout.tsx      ← 博客布局（侧边栏）
    └── page.tsx        ← 博客列表页
```

博客区域可以有自己的侧边栏，而不影响其他页面。

## 五、组件（Server vs Client）

### 5.1 两种组件

Next.js 里有两种组件，这是它最核心的概念之一：

**服务端组件（Server Components）** = 在服务器上运行，生成 HTML 发给浏览器
- 默认所有组件都是服务端组件
- 可以直接访问数据库、读文件
- 不能用 `useState`、`onClick` 等交互功能

**客户端组件（Client Components）** = 在浏览器里运行
- 文件顶部加 `"use client"` 声明
- 可以处理用户交互（点击、输入、动画等）
- 可以用 React 的 `useState`、`useEffect` 等

```
类比你熟悉的数仓：
- 服务端组件 = DW 层的 ETL 任务（在服务器跑，处理数据，输出结果）
- 客户端组件 = ADS 层的报表看板（在用户浏览器里渲染，支持交互筛选）
```

### 5.2 服务端组件示例

```tsx
// app/users/page.tsx（默认就是服务端组件）
async function getUsers() {
  const res = await fetch("https://jsonplaceholder.typicode.com/users")
  return res.json()
}

export default async function UsersPage() {
  const users = await getUsers()  // 直接 await，不需要 useEffect

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">用户列表</h1>
      <ul className="space-y-2">
        {users.map((user: any) => (
          <li key={user.id} className="p-3 bg-gray-50 rounded">
            {user.name} - {user.email}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

### 5.3 客户端组件示例

```tsx
// components/Counter.tsx
"use client"  // ← 加这行，声明为客户端组件

import { useState } from "react"

export default function Counter() {
  const [count, setCount] = useState(0)

  return (
    <div className="flex items-center gap-4 p-4">
      <button
        className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        onClick={() => setCount(count - 1)}
      >
        -
      </button>
      <span className="text-2xl font-bold w-12 text-center">{count}</span>
      <button
        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        onClick={() => setCount(count + 1)}
      >
        +
      </button>
    </div>
  )
}
```

在页面里使用：

```tsx
// app/page.tsx
import Counter from "@/components/Counter"

export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">首页</h1>
      <Counter />
    </div>
  )
}
```

### 5.4 什么时候用哪种？

| 场景 | 用哪种 |
|------|-------|
| 显示静态内容、列表 | 服务端组件（默认） |
| 从数据库/API 获取数据 | 服务端组件 |
| 用户点击按钮有反应 | 客户端组件 |
| 表单输入 | 客户端组件 |
| 用了 useState / useEffect | 客户端组件 |

**原则：默认用服务端组件，只在需要交互时才加 `"use client"`。**

## 六、数据获取

### 6.1 服务端获取（推荐）

```tsx
// app/posts/page.tsx
export default async function PostsPage() {
  // 直接在组件里 fetch，Next.js 会自动缓存
  const res = await fetch("https://jsonplaceholder.typicode.com/posts?_limit=10")
  const posts = await res.json()

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">文章列表</h1>
      {posts.map((post: any) => (
        <article key={post.id} className="mb-6 p-4 bg-white rounded-lg shadow">
          <h2 className="text-lg font-semibold">{post.title}</h2>
          <p className="text-gray-600 mt-2">{post.body}</p>
        </article>
      ))}
    </div>
  )
}
```

### 6.2 缓存策略

```tsx
// 默认：自动缓存（适合不常变的数据）
await fetch("https://api.example.com/data")

// 每 60 秒刷新一次（适合有时效性的数据）
await fetch("https://api.example.com/data", {
  next: { revalidate: 60 }
})

// 不缓存，每次都重新获取（适合实时数据）
await fetch("https://api.example.com/data", {
  cache: "no-store"
})
```

### 6.3 客户端获取

```tsx
"use client"
import { useState, useEffect } from "react"

export default function ClientData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("https://jsonplaceholder.typicode.com/todos/1")
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
  }, [])  // 空数组 = 只在页面加载时执行一次

  if (loading) return <p>加载中...</p>
  return <p>数据：{JSON.stringify(data)}</p>
}
```

## 七、其他重要概念（了解即可）

### 7.1 Link 组件（页面跳转）

```tsx
import Link from "next/link"

// 用 Link 代替 <a>，页面跳转不会整页刷新，更快
<Link href="/about">关于我们</Link>
<Link href="/blog/123">查看文章</Link>
```

### 7.2 Image 组件（优化图片）

```tsx
import Image from "next/image"

<Image
  src="/logo.png"      // 放在 public/ 文件夹里的图片
  alt="Logo"
  width={200}
  height={100}
/>
```

Next.js 会自动压缩图片、转换格式、按需加载，不用自己操心。

### 7.3 环境变量

```bash
# .env.local 文件（放在项目根目录）
DATABASE_URL=postgres://user:password@localhost:5432/mydb
NEXT_PUBLIC_API_URL=https://api.example.com
```

- 普通变量（`DATABASE_URL`）：只能在服务端使用（安全）
- `NEXT_PUBLIC_` 开头的变量：客户端也能用（会暴露给浏览器）

### 7.4 元数据 / SEO

```tsx
// app/page.tsx
export const metadata = {
  title: "我的网站首页",
  description: "一个用 Next.js 搭建的全栈应用",
}
```

Next.js 会自动把这些信息放到页面的 `<head>` 里，帮助搜索引擎理解你的页面。

## 八、今日实操项目

### 搭建一个多页面个人网站

1. 创建 Next.js 项目并初始化 shadcn/ui
2. 修改 `app/layout.tsx` 添加导航栏和页脚
3. 创建至少 3 个页面：首页、关于、项目展示
4. 做一个客户端组件（比如计数器或主题切换按钮）
5. 从一个公开 API 获取数据并展示

如果时间充裕，跟着 Next.js 官方教程走：https://nextjs.org/learn

## 九、推荐资源

- Next.js 官方教程（最好的入门教程，预计 10h）：https://nextjs.org/learn
- Next.js 视频教程（油管，很详细）：https://www.youtube.com/watch?v=b4ba60j_4o8&list=PLC3y8-rFHvwhIEc4I4YsRz5C7GOBnxSJY
- Next.js 中文文档：https://nextjs.org/docs

## 十、常见问题

**Q：服务端组件和客户端组件搞混了怎么办？**
最常见的报错是在服务端组件里用了 `useState` 或 `onClick`。看到这类报错，在文件顶部加 `"use client"` 就行。

**Q：`npm run dev` 和 `npm run build` 有什么区别？**
`dev` 是开发模式（热更新，方便调试），`build` 是生产构建（优化打包，准备上线）。开发时用 `dev`，上线前用 `build`。

**Q：页面怎么跳转？**
用 `<Link href="/目标路径">` 代替 `<a>`，这样页面切换更快（不会整页刷新）。

---

> ✅ Day 4 完成！明天连数据库，做一个完整的全栈应用。

<!-- series-nav-start -->

---
**📚 全栈开发**（5/6）

⬅️ 上一篇：[[Day3-Tailwind和shadcn]] | ➡️ 下一篇：[[Day5-Supabase和实战项目]]

<!-- series-nav-end -->
