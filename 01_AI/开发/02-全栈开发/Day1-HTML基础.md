---
name: Day1 HTML基础
description: 从零理解网页的骨架结构，学会用 HTML 标签搭建页面
---

# Day 1：HTML 基础

> 今天的目标：理解网页是怎么搭出来的，能自己手写一个个人简介页面。

## 一、HTML 是什么？

HTML 全称 HyperText Markup Language（超文本标记语言）。听起来很唬人，其实很简单——它就是一套「标签」，告诉浏览器「这段内容是标题」「那段内容是段落」「这里放一张图」。

打个比方：如果网页是一栋房子，HTML 就是房子的**骨架和隔断**——哪里是客厅、哪里是卧室、门开在哪、窗开在哪。它不管好不好看（那是 CSS 的事），也不管能不能互动（那是 JavaScript 的事），它只管**结构**。

## 二、基本结构

每个 HTML 文件都长这样，记住这个模板：

```html
<!DOCTYPE html>
<html>
  <head>
    <title>网页标题（显示在浏览器标签页上）</title>
  </head>
  <body>
    <!-- 这里放你看到的所有网页内容 -->
  </body>
</html>
```

拆解一下：
- `<!DOCTYPE html>`：告诉浏览器「这是一个 HTML5 文件」，固定写法，不用管。
- `<html>`：整个网页的最外层容器，所有内容都在这里面。
- `<head>`：**幕后信息**，用户看不到。放网页标题、字符编码、引用的样式表等。
- `<body>`：**台前内容**，用户看到的一切都在这里。

> 💡 `<!-- 这是注释 -->` 是 HTML 的注释写法，浏览器会忽略它，你可以用它给自己写备注。

## 三、最常用的标签（只需要记这些）

### 3.1 标题标签 `<h1>` ~ `<h6>`

从大到小共 6 级，`<h1>` 最大，`<h6>` 最小：

```html
<h1>我是一级标题（最大）</h1>
<h2>我是二级标题</h2>
<h3>我是三级标题</h3>
```

一般一个页面只用一个 `<h1>`（相当于文章大标题），其他用 `<h2>`、`<h3>` 就够了。

### 3.2 段落标签 `<p>`

每一对 `<p></p>` 就是一个段落，段落之间会自动空一行：

```html
<p>这是第一段文字。浏览器会自动换行。</p>
<p>这是第二段文字。两段之间有间距。</p>
```

### 3.3 加粗和斜体

```html
<p><strong>这段文字会加粗</strong></p>
<p><em>这段文字会变斜体</em></p>
```

### 3.4 链接标签 `<a>`

让文字变成可以点击的链接：

```html
<a href="https://www.baidu.com">点我去百度</a>
```

- `href` 是链接地址。
- 标签中间的文字是用户看到的可点击文本。

### 3.5 图片标签 `<img>`

在网页上显示一张图片：

```html
<img src="photo.jpg" alt="这是一张照片">
```

- `src`：图片的路径或网址。
- `alt`：图片加载失败时显示的替代文字（也帮助搜索引擎理解图片内容）。
- 注意：`<img>` 是**自闭合标签**，不需要 `</img>`。

### 3.6 列表标签

**无序列表**（小圆点）：

```html
<ul>
  <li>苹果</li>
  <li>香蕉</li>
  <li>橘子</li>
</ul>
```

**有序列表**（数字编号）：

```html
<ol>
  <li>第一步：打开冰箱</li>
  <li>第二步：把大象放进去</li>
  <li>第三步：关上冰箱</li>
</ol>
```

### 3.7 容器标签 `<div>`

`<div>` 本身没有任何视觉效果，它是一个「收纳盒」，用来把一组内容打包在一起，方便后续用 CSS 统一设置样式：

```html
<div>
  <h2>关于我</h2>
  <p>我是一名程序员。</p>
</div>
```

## 四、语义化标签（给结构起名字）

除了 `<div>` 这个万能收纳盒，HTML5 还提供了一些「有名字的收纳盒」，让代码更易读：

```
<header>   → 页面顶部（放 Logo、导航栏）
<nav>      → 导航菜单
<main>     → 页面主体内容
<section>  → 内容分区（类似文章的「章」）
<footer>   → 页面底部（放版权信息、联系方式）
```

用起来就是这样：

```html
<body>
  <header>
    <h1>我的网站</h1>
    <nav>
      <a href="/">首页</a>
      <a href="/about">关于</a>
    </nav>
  </header>

  <main>
    <section>
      <h2>最新文章</h2>
      <p>这里是文章内容...</p>
    </section>
  </main>

  <footer>
    <p>© 2026 我的网站</p>
  </footer>
</body>
```

## 五、动手练习

### 练习 1：我的第一个网页

创建一个文件 `my-first-page.html`，复制下面的代码，然后双击用浏览器打开：

```html
<!DOCTYPE html>
<html>
  <head>
    <title>我的学习笔记</title>
  </head>
  <body>
    <h1>欢迎来到我的网页！</h1>
    <p>这是我学习 HTML 的第一天。</p>
    <p>我喜欢：</p>
    <ul>
      <li>编程</li>
      <li>音乐</li>
      <li>旅行</li>
    </ul>
  </body>
</html>
```

> 在 Mac 上，终端里输入 `open my-first-page.html` 就能用浏览器打开。

### 练习 2：个人简介页面（今日大作业）

这个项目把今天学的标签都串起来了。创建 `profile.html`，复制运行：

```html
<!DOCTYPE html>
<html>
  <head>
    <title>我的个人简介</title>
    <style>
      /* 这部分是 CSS 样式，先不用深究，知道它让页面好看就行 */
      body {
        font-family: Arial, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f9f9f9;
      }
      .header {
        background-color: #4A90D9;
        color: white;
        padding: 30px;
        text-align: center;
        border-radius: 10px;
      }
      .section {
        margin: 20px 0;
        padding: 20px;
        background: white;
        border-radius: 8px;
        border-bottom: 1px solid #eee;
      }
      a { color: #4A90D9; }
    </style>
  </head>
  <body>
    <div class="header">
      <h1>你的名字</h1>
      <p>一句话介绍自己</p>
    </div>

    <div class="section">
      <h2>关于我</h2>
      <p>我是一名数据开发工程师，正在学习全栈开发。</p>
      <p>我的目标是能够独立搭建一个完整的 Web 应用。</p>
    </div>

    <div class="section">
      <h2>我的技能</h2>
      <ul>
        <li><strong>数据开发：</strong>SQL、Hive、Spark</li>
        <li><strong>正在学习：</strong>HTML、JavaScript、Next.js</li>
      </ul>
    </div>

    <div class="section">
      <h2>联系方式</h2>
      <ul>
        <li>Email: your-email@example.com</li>
        <li>GitHub: <a href="https://github.com">我的 GitHub</a></li>
      </ul>
    </div>

    <footer>
      <p style="text-align: center; color: #999;">© 2026 我的个人主页</p>
    </footer>
  </body>
</html>
```

**做完之后，试着改一改：**
- 把名字和介绍换成你自己的
- 添加一个新的 `<div class="section">` 放你的爱好
- 修改颜色代码（比如把 `#4A90D9` 换成 `#FF6B6B`）看看效果

## 六、推荐学习资源

- MDN HTML 教程（最权威的参考）：https://developer.mozilla.org/zh-CN/docs/Learn/HTML
- W3School HTML 教程（中文友好）：https://www.w3school.com.cn/html/index.asp
- Codepen 在线练习（写完立刻看效果）：https://codepen.io

## 七、常见问题

**Q：为什么我改了代码浏览器没变化？**
保存文件后在浏览器按 `Cmd + R`（Mac）刷新页面。

**Q：标签是不是必须成对出现？**
大多数是的，比如 `<p>...</p>`、`<div>...</div>`。少数是自闭合的，比如 `<img>`、`<br>`（换行）、`<hr>`（水平线）。

**Q：标签可以嵌套吗？**
可以，而且很常见。比如 `<div>` 里放 `<h2>` 和 `<p>`。但要注意**先开后关**的顺序，像套娃一样：`<div><p>内容</p></div>` ✅，`<div><p>内容</div></p>` ❌。

---

> ✅ Day 1 完成！明天我们学 JavaScript，让页面「动起来」。
