---
name: Day3 Tailwind CSS 和 shadcn/ui
description: 用工具类快速写样式，用现成组件库加速开发
---

# Day 3：Tailwind CSS + shadcn/ui

> 今天的目标：不写传统 CSS，也能做出好看的页面。理解「原子类」思路，会用 shadcn/ui 组件。

## 一、为什么不直接写 CSS？

传统写 CSS 是这样的流程：先给 HTML 元素取一个 class 名，再去 CSS 文件里写样式。听起来不复杂，但项目大了之后会遇到几个痛点：class 名字起冲突、样式散落在各处难找、改一个地方影响其他地方……

Tailwind CSS 换了一个思路：**把每个 CSS 属性都变成一个「积木块」（工具类），你直接在 HTML 上拼积木就行，根本不用写 CSS 文件。**

```html
<!-- 传统写法：先起名字，再去 CSS 文件定义 -->
<button class="my-button">点击</button>

<style>
.my-button {
  background-color: blue;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
}
</style>

<!-- Tailwind 写法：直接在 class 里拼积木 -->
<button class="bg-blue-500 text-white px-4 py-2 rounded">点击</button>
```

看起来 class 写得很长？没关系，好处是：
- 不用取名字了（再也不用纠结 `.my-button` 还是 `.btn-primary`）
- 样式和结构在一起，一目了然
- 不会有样式冲突

## 二、Tailwind 核心工具类速查

不需要背，用的时候查就行。这里列出最常用的，覆盖 90% 场景。

### 2.1 文字相关

| 工具类 | 效果 | 记忆方式 |
|-------|------|---------|
| `text-sm` / `text-base` / `text-lg` / `text-xl` / `text-2xl` | 字号从小到大 | text-尺寸 |
| `font-bold` | 加粗 | font-粗细 |
| `font-light` | 细体 | |
| `text-red-500` | 红色文字 | text-颜色-深浅 |
| `text-gray-600` | 灰色文字 | 数字越大越深 |
| `text-center` | 文字居中 | |
| `text-left` / `text-right` | 左对齐/右对齐 | |

### 2.2 间距相关（最常用！）

Tailwind 的间距单位：1 个单位 = 0.25rem ≈ 4px。所以 `p-4` = 16px。

| 工具类 | 效果 | 记忆方式 |
|-------|------|---------|
| `p-4` | 四周内边距 16px | p = padding（内边距） |
| `px-4` | 左右内边距 | x = 水平方向 |
| `py-2` | 上下内边距 | y = 垂直方向 |
| `pt-4` / `pb-4` / `pl-4` / `pr-4` | 上/下/左/右 | t=top, b=bottom, l=left, r=right |
| `m-4` | 四周外边距 | m = margin（外边距） |
| `mx-auto` | 水平居中 | 左右 margin 自动 |
| `space-x-4` | 子元素之间的水平间距 | 比给每个元素加 margin 方便 |

> 💡 内边距 `padding` 是元素内部的间距（盒子壁到内容的距离），外边距 `margin` 是元素外部的间距（盒子和邻居的距离）。

### 2.3 背景和边框

| 工具类 | 效果 |
|-------|------|
| `bg-blue-500` | 蓝色背景 |
| `bg-white` / `bg-black` | 白色/黑色背景 |
| `bg-gray-100` | 浅灰色背景（常用于页面底色） |
| `rounded` | 小圆角 |
| `rounded-lg` | 大圆角 |
| `rounded-full` | 完全圆形（头像常用） |
| `border` | 加边框 |
| `border-gray-300` | 灰色边框 |
| `shadow-md` | 中等阴影（卡片效果） |
| `shadow-lg` | 大阴影 |

### 2.4 布局（Flexbox）

Flexbox 是现代网页布局的核心，Tailwind 把它简化得很好用：

```html
<!-- 水平排列，居中对齐 -->
<div class="flex items-center justify-center">
  <span>左边</span>
  <span>右边</span>
</div>

<!-- 两端对齐（左右各一个） -->
<div class="flex justify-between">
  <span>Logo</span>
  <span>菜单</span>
</div>

<!-- 垂直排列 -->
<div class="flex flex-col">
  <p>第一行</p>
  <p>第二行</p>
</div>
```

| 工具类 | 效果 |
|-------|------|
| `flex` | 开启弹性布局 |
| `flex-col` | 垂直方向排列（默认水平） |
| `items-center` | 交叉轴居中（垂直居中） |
| `justify-center` | 主轴居中（水平居中） |
| `justify-between` | 两端对齐 |
| `gap-4` | 子元素间距 |
| `w-full` | 宽度 100% |
| `h-screen` | 高度占满屏幕 |
| `max-w-md` | 最大宽度（中等） |

### 2.5 响应式设计（一套代码适配手机和电脑）

Tailwind 用**前缀**来区分屏幕尺寸，这是它最强大的功能之一：

```html
<!-- 手机上全宽，中等屏幕一半宽，大屏幕三分之一宽 -->
<div class="w-full md:w-1/2 lg:w-1/3">
  内容
</div>

<!-- 手机上隐藏，电脑上显示 -->
<div class="hidden md:block">
  只在电脑上显示
</div>
```

| 前缀 | 屏幕宽度 | 设备 |
|------|---------|------|
| 无前缀 | 所有尺寸 | 手机优先 |
| `sm:` | ≥640px | 大手机 |
| `md:` | ≥768px | 平板 |
| `lg:` | ≥1024px | 电脑 |
| `xl:` | ≥1280px | 大屏 |

### 2.6 交互状态

```html
<!-- 鼠标悬停变深色 -->
<button class="bg-blue-500 hover:bg-blue-700 text-white px-4 py-2 rounded">
  悬停试试
</button>

<!-- 聚焦时加边框 -->
<input class="border focus:border-blue-500 focus:ring-2 p-2 rounded" />
```

## 三、Tailwind 在线练习

打开 https://play.tailwindcss.com ，把下面的代码粘贴进去试试效果：

### 练习 1：个人名片

```html
<div class="max-w-sm mx-auto mt-20 bg-white rounded-2xl shadow-lg overflow-hidden">
  <div class="bg-gradient-to-r from-blue-500 to-purple-600 p-8 text-center">
    <div class="w-24 h-24 bg-white rounded-full mx-auto mb-4 flex items-center justify-center text-4xl">
      👤
    </div>
    <h2 class="text-2xl font-bold text-white">你的名字</h2>
    <p class="text-blue-100 mt-1">全栈开发学习中</p>
  </div>
  <div class="p-6">
    <div class="flex items-center gap-3 mb-3">
      <span class="text-gray-500">📍</span>
      <span class="text-gray-700">北京</span>
    </div>
    <div class="flex items-center gap-3 mb-3">
      <span class="text-gray-500">💼</span>
      <span class="text-gray-700">数据开发工程师</span>
    </div>
    <div class="flex gap-2 mt-4">
      <span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">SQL</span>
      <span class="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm">Next.js</span>
      <span class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">React</span>
    </div>
  </div>
</div>
```

### 练习 2：待办事项（Tailwind 版）

```html
<div class="max-w-md mx-auto mt-10 bg-white rounded-xl shadow-md overflow-hidden">
  <div class="bg-gradient-to-r from-purple-500 to-blue-500 p-5">
    <h1 class="text-2xl font-bold text-white">📝 今日任务</h1>
    <p class="text-blue-100 text-sm mt-1">剩余 <span class="font-bold">3</span> 项待完成</p>
  </div>
  <div class="p-4 border-b">
    <div class="flex gap-2">
      <input type="text" class="flex-1 border rounded-lg px-4 py-3 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="写下一个新任务..." />
      <button class="bg-purple-500 hover:bg-purple-600 text-white px-5 rounded-lg transition-colors">添加</button>
    </div>
  </div>
  <ul class="divide-y">
    <li class="p-4 hover:bg-gray-50 flex items-center gap-3">
      <input type="checkbox" class="w-5 h-5 text-purple-500 rounded" />
      <span class="text-gray-700">学习 Tailwind CSS</span>
      <span class="ml-auto bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full">学习</span>
    </li>
    <li class="p-4 hover:bg-gray-50 flex items-center gap-3">
      <input type="checkbox" checked class="w-5 h-5 text-purple-500 rounded" />
      <span class="text-gray-400 line-through">看 HTML 教程</span>
    </li>
    <li class="p-4 hover:bg-gray-50 flex items-center gap-3">
      <input type="checkbox" class="w-5 h-5 text-purple-500 rounded" />
      <span class="text-gray-700">写待办事项练习</span>
      <span class="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">练习</span>
    </li>
  </ul>
</div>
```

> 试着改改颜色和间距，感受 Tailwind 的灵活性。

## 四、shadcn/ui —— 拿来就用的高质量组件

### 4.1 它是什么？

shadcn/ui 不是传统的组件库（比如 Ant Design 那种 `npm install` 后 `import` 使用的），它是**把组件源码直接复制到你的项目里**。

好处是：你对代码有 100% 的控制权，想怎么改就怎么改。不存在「组件库升级导致你的页面崩了」的问题。

它底层依赖三个东西：
- **Tailwind CSS**：样式（你刚学过）
- **Radix Primitives**：保证组件的可访问性（键盘操作、屏幕阅读器等）
- **Lucide-react**：图标库

### 4.2 怎么用？（需要先有 Next.js 项目，Day 4 会详细学）

```bash
# 1. 先创建一个 Next.js 项目
npx create-next-app@latest my-app --typescript --app
cd my-app

# 2. 初始化 shadcn/ui（一路回车选默认就行）
npx shadcn@latest init

# 3. 添加你需要的组件
npx shadcn@latest add button     # 添加按钮组件
npx shadcn@latest add card       # 添加卡片组件
npx shadcn@latest add input      # 添加输入框组件
npx shadcn@latest add dialog     # 添加弹窗组件
```

添加后，组件代码会出现在 `components/ui/` 文件夹里。然后在页面中这样用：

```tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function Page() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>欢迎！</CardTitle>
      </CardHeader>
      <CardContent>
        <p>这是一个 shadcn/ui 卡片</p>
        <Button>点击我</Button>
      </CardContent>
    </Card>
  )
}
```

### 4.3 浏览所有组件

官网组件列表：https://ui.shadcn.com/docs/components/accordion

每个组件都有示例代码和安装命令，需要什么加什么，非常方便。

### 4.4 日间/夜间模式切换

这是一个很实用的功能，shadcn/ui 天然支持。核心步骤：

```bash
# 安装 next-themes
npm install next-themes
```

然后创建一个 ThemeProvider 组件包裹你的应用，再做一个切换按钮。具体代码在 Day 4 的 Next.js 项目里会实操，这里先了解概念。

### 4.5 切换主题风格

shadcn/ui 支持丰富的主题，你可以到下面的网站挑选喜欢的配色：
- https://ui.shadcn.com/themes
- https://tweakcn.com/editor/theme

选好后复制 CSS 代码，替换项目中 `globals.css` 里对应的颜色变量即可。

## 五、今日练习总结

| 练习 | 在哪做 | 目标 |
|------|-------|------|
| 个人名片 | play.tailwindcss.com | 熟悉 Tailwind 工具类 |
| 待办事项（Tailwind 版） | play.tailwindcss.com | 掌握布局和交互状态 |
| 自由发挥 | play.tailwindcss.com | 截图一个你喜欢的 App 界面，尝试用 Tailwind 还原 |

**今天的核心收获：** Tailwind 的思路是「用 class 名直接写样式」，shadcn/ui 的思路是「把组件源码放到你的项目里」。这两者结合，就是 Next.js 项目的样式方案。

## 六、推荐资源

- Tailwind 官方文档（查工具类名的字典）：https://tailwindcss.com/docs
- Tailwind 在线练习场：https://play.tailwindcss.com
- shadcn/ui 官网（组件目录）：https://ui.shadcn.com
- Tailwind 速查表（一图看全）：https://nerdcave.com/tailwind-cheat-sheet

---

> ✅ Day 3 完成！明天进入最核心的 Next.js 学习。
