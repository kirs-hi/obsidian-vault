---
name: Day5 Supabase和实战项目
description: 连接云数据库，完成一个真正的全栈应用
---

# Day 5：Supabase + 实战项目

> 今天的目标：用 Supabase 当后端数据库，做出一个完整的全栈小应用。

## 一、Supabase 是什么？

前四天你学会了做页面（HTML + [[Day3-Tailwind和shadcn|Tailwind]]）、写交互（JS）、搭框架（[[Day4-Next.js核心|Next.js]]）。但数据存在哪？用户信息怎么管理？这就是 Supabase 要解决的事。

**Supabase = 云端 PostgreSQL 数据库 + 用户认证 + 文件存储 + 实时订阅**

作为数仓同学，你对数据库再熟悉不过了。Supabase 底层就是 PostgreSQL，你用 SQL 的经验可以直接迁移过来。只是多了一层「云端托管」和「配套的 API」，让你不需要自己搭服务器。

打比方：
- 以前做数仓，你自己管数据库集群 → 现在 Supabase 帮你管
- 以前写 ETL 调 JDBC → 现在 Supabase 提供现成的 JS SDK
- 以前做权限用 Ranger/Sentry → 现在 Supabase 用 RLS（行级安全策略）

## 二、注册和创建项目

### 2.1 注册账号

1. 打开 https://supabase.com
2. 点击 "Start your project"，用 GitHub 账号登录
3. 创建一个新项目（New Project），选择免费套餐

### 2.2 拿到连接信息

创建完项目后，进入 Settings → API，你会看到两个关键信息：
- **Project URL**：你的数据库 API 地址
- **anon public key**：公开密钥（安全的，可以放在前端代码里）

```
https://abcdefg.supabase.co     ← Project URL
eyJhbGciOiJIUz...               ← anon key
```

## 三、创建数据表（你最擅长的部分）

### 3.1 在 Supabase 控制台建表

进入项目 → Table Editor → New Table

比如创建一个「待办事项」表：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int8 (自增主键) | 自动生成 |
| created_at | timestamptz | 创建时间，默认 now() |
| text | text | 待办内容 |
| is_done | bool | 是否完成，默认 false |
| user_id | uuid | 用户 ID（可选） |

也可以用 SQL Editor 直接写 SQL（对你来说可能更顺手）：

```sql
CREATE TABLE todos (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  text TEXT NOT NULL,
  is_done BOOLEAN DEFAULT FALSE,
  user_id UUID
);

-- 插入几条测试数据
INSERT INTO todos (text) VALUES
  ('学习 Next.js'),
  ('练习 Tailwind CSS'),
  ('完成全栈项目');
```

### 3.2 设置 RLS（行级安全策略）

Supabase 默认开启 RLS，意味着客户端默认**读不到任何数据**。你需要添加策略：

```sql
-- 允许所有人读取（公开应用场景）
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "允许所有人读取" ON todos
  FOR SELECT USING (true);

CREATE POLICY "允许所有人插入" ON todos
  FOR INSERT WITH CHECK (true);

CREATE POLICY "允许所有人更新" ON todos
  FOR UPDATE USING (true);

CREATE POLICY "允许所有人删除" ON todos
  FOR DELETE USING (true);
```

> 生产环境不应该这么宽松，这里为了学习方便先全部放开。

## 四、在 Next.js 中连接 Supabase

### 4.1 安装 SDK

```bash
cd my-first-app
npm install @supabase/supabase-js
```

### 4.2 配置环境变量

在项目根目录创建 `.env.local` 文件：

```bash
NEXT_PUBLIC_SUPABASE_URL=https://你的项目ID.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=你的anon_key
```

### 4.3 创建 Supabase 客户端

创建 `lib/supabase.ts`：

```typescript
import { createClient } from "@supabase/supabase-js"

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)
```

### 4.4 CRUD 操作示例

```typescript
import { supabase } from "@/lib/supabase"

// 查询所有待办（SELECT *）
const { data, error } = await supabase
  .from("todos")
  .select("*")
  .order("created_at", { ascending: false })

// 插入一条（INSERT）
const { data, error } = await supabase
  .from("todos")
  .insert({ text: "新的待办事项" })
  .select()  // 返回插入的数据

// 更新一条（UPDATE）
const { data, error } = await supabase
  .from("todos")
  .update({ is_done: true })
  .eq("id", 1)  // WHERE id = 1

// 删除一条（DELETE）
const { error } = await supabase
  .from("todos")
  .delete()
  .eq("id", 1)
```

看着是不是很亲切？`.from("todos")` 就是 `FROM todos`，`.eq("id", 1)` 就是 `WHERE id = 1`，`.select("*")` 就是 `SELECT *`。完全就是 SQL 的 JS 版本。

## 五、实战项目：全栈待办事项应用

这是今天的大作业，把前5天学的东西全部串起来。

### 5.1 项目结构

```
my-todo-app/
├── app/
│   ├── layout.tsx          ← 根布局
│   ├── page.tsx            ← 首页（待办列表）
│   └── globals.css
├── components/
│   ├── TodoList.tsx        ← 待办列表组件（客户端）
│   └── AddTodo.tsx         ← 添加待办组件（客户端）
├── lib/
│   └── supabase.ts         ← Supabase 客户端
└── .env.local              ← 环境变量
```

### 5.2 Supabase 客户端

```typescript
// lib/supabase.ts
import { createClient } from "@supabase/supabase-js"

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### 5.3 添加待办组件

```tsx
// components/AddTodo.tsx
"use client"

import { useState } from "react"
import { supabase } from "@/lib/supabase"

export default function AddTodo({ onAdd }: { onAdd: () => void }) {
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()  // 阻止表单默认提交行为
    if (!text.trim()) return

    setLoading(true)
    const { error } = await supabase
      .from("todos")
      .insert({ text: text.trim() })

    if (error) {
      alert("添加失败：" + error.message)
    } else {
      setText("")   // 清空输入框
      onAdd()       // 通知父组件刷新列表
    }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="输入新的待办事项..."
        className="flex-1 border rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg disabled:opacity-50 transition-colors"
      >
        {loading ? "添加中..." : "添加"}
      </button>
    </form>
  )
}
```

### 5.4 待办列表组件

```tsx
// components/TodoList.tsx
"use client"

import { useState, useEffect } from "react"
import { supabase } from "@/lib/supabase"
import AddTodo from "./AddTodo"

type Todo = {
  id: number
  text: string
  is_done: boolean
  created_at: string
}

export default function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loading, setLoading] = useState(true)

  // 加载待办列表
  async function fetchTodos() {
    const { data, error } = await supabase
      .from("todos")
      .select("*")
      .order("created_at", { ascending: false })

    if (data) setTodos(data)
    setLoading(false)
  }

  // 切换完成状态
  async function toggleTodo(id: number, currentState: boolean) {
    const { error } = await supabase
      .from("todos")
      .update({ is_done: !currentState })
      .eq("id", id)

    if (!error) fetchTodos()  // 刷新列表
  }

  // 删除待办
  async function deleteTodo(id: number) {
    const { error } = await supabase
      .from("todos")
      .delete()
      .eq("id", id)

    if (!error) fetchTodos()
  }

  // 页面加载时获取数据
  useEffect(() => {
    fetchTodos()
  }, [])

  if (loading) {
    return <p className="text-center text-gray-500 py-8">加载中...</p>
  }

  const activeCount = todos.filter(t => !t.is_done).length

  return (
    <div>
      <AddTodo onAdd={fetchTodos} />

      {todos.length === 0 ? (
        <p className="text-center text-gray-400 py-8">还没有待办事项，添加一个吧！</p>
      ) : (
        <ul className="space-y-2">
          {todos.map(todo => (
            <li
              key={todo.id}
              className="flex items-center gap-3 p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              {/* 复选框 */}
              <input
                type="checkbox"
                checked={todo.is_done}
                onChange={() => toggleTodo(todo.id, todo.is_done)}
                className="w-5 h-5 rounded text-blue-500"
              />

              {/* 待办内容 */}
              <span className={`flex-1 ${todo.is_done ? "line-through text-gray-400" : "text-gray-700"}`}>
                {todo.text}
              </span>

              {/* 删除按钮 */}
              <button
                onClick={() => deleteTodo(todo.id)}
                className="text-red-400 hover:text-red-600 text-sm"
              >
                删除
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="text-center text-gray-500 mt-4 text-sm">
        剩余 {activeCount} 项未完成
      </p>
    </div>
  )
}
```

### 5.5 首页

```tsx
// app/page.tsx
import TodoList from "@/components/TodoList"

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold text-center mb-2">📝 我的待办清单</h1>
        <p className="text-center text-gray-500 mb-8">
          Next.js + Supabase 全栈应用
        </p>
        <TodoList />
      </div>
    </div>
  )
}
```

### 5.6 运行

```bash
npm run dev
```

打开 http://localhost:3000 ，你就有了一个**真正的全栈应用**：前端用 Next.js + Tailwind，数据存在云端 Supabase 数据库里。

## 六、进阶方向（学完这5天之后）

### 6.1 用户认证

Supabase 自带用户注册/登录功能：

```typescript
// 注册
const { data, error } = await supabase.auth.signUp({
  email: "user@example.com",
  password: "your-password",
})

// 登录
const { data, error } = await supabase.auth.signInWithPassword({
  email: "user@example.com",
  password: "your-password",
})

// 获取当前用户
const { data: { user } } = await supabase.auth.getUser()

// 登出
await supabase.auth.signOut()
```

### 6.2 部署上线

Next.js 项目最简单的部署方式是用 Vercel（Next.js 的母公司）：

1. 把代码推到 GitHub
2. 登录 https://vercel.com ，导入 GitHub 仓库
3. 配置环境变量（把 `.env.local` 里的内容填进去）
4. 点击部署

几分钟后你就有了一个公开可访问的网站。

### 6.3 推荐继续学的东西

| 方向 | 资源 |
|------|------|
| Next.js 深入 | 官方教程 https://nextjs.org/learn |
| React 基础 | React 官方教程 https://react.dev/learn |
| Supabase 深入 | 官方文档 https://supabase.com/docs |
| 全栈项目参考 | Build a SaaS with Next.js (YouTube) |

## 七、5 天学习总回顾

```
Day 1: HTML        → 网页的骨架（标签、结构、语义化）
Day 2: JS/TS       → 网页的交互（变量、函数、DOM、类型）
Day 3: Tailwind    → 网页的样式（原子类、布局、响应式）
       shadcn/ui   → 现成的高质量组件
Day 4: Next.js     → 全栈框架（路由、组件、数据获取）
Day 5: Supabase    → 云数据库（建表、CRUD、用户认证）
       实战项目     → 全部串起来
```

学完这5天，你已经具备了：
- 读懂 AI 生成的前端代码的能力
- 独立搭建一个简单全栈应用的能力
- 和前端同事沟通不再鸡同鸭讲的能力

后续的提升就是**在实际项目中边做边学**——遇到不会的查文档、问 AI，这是最高效的学习方式。

---

> ✅ Day 5 完成！恭喜你完成全部 5 天的学习计划！🎉
