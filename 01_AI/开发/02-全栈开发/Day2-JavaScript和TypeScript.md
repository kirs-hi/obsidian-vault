---
name: Day2 JavaScript和TypeScript
description: 学习让网页动起来的编程语言，以及 TypeScript 的类型安全机制
---

# Day 2：JavaScript 和 TypeScript

> 今天的目标：理解 JS 核心语法，能做出有交互效果的网页（点击按钮有反应）。

## 一、JavaScript 是什么？

昨天的 HTML 是网页的骨架，但它是「死的」——用户点按钮没反应，页面不会变化。JavaScript（简称 JS）就是让网页**活起来**的编程语言。

打比方：如果 HTML 是一栋房子的墙壁和门窗，JavaScript 就是房子的**电路系统**——按下开关灯会亮，按门铃会响，空调能调温度。

JS 还有一个「亲哥」叫 TypeScript（简称 TS），它比 JS 多了类型检查——就像电路系统加了安全检测，接错线会提前报警，而不是等到房子起火了才发现。

## 二、JS 基础语法（核心三件套）

### 2.1 变量 —— 数据的盒子

变量就是用来「装东西」的盒子。JS 有两种盒子：

```javascript
let message = "你好世界";   // let：普通盒子，里面的东西可以换
const PI = 3.14;            // const：上锁的盒子，放进去就不能改了
```

**什么时候用 let，什么时候用 const？**
- 默认用 `const`（大部分变量其实不需要改）
- 只有确定后面要改的，才用 `let`

```javascript
const name = "小明";       // 名字不会变，用 const
let score = 0;             // 分数会变，用 let
score = 100;               // ✅ 可以改
// name = "小红";          // ❌ 报错！const 不能改
```

**数据类型（盒子里能装什么）：**

```javascript
// 字符串（文字）—— 用引号包起来
const greeting = "Hello";
const city = '北京';          // 单引号双引号都行

// 数字 —— 不需要引号
const age = 25;
const price = 9.99;

// 布尔值 —— 只有 true 或 false
const isStudent = true;
const isRich = false;

// 数组 —— 一组数据的清单
const fruits = ["苹果", "香蕉", "橘子"];
console.log(fruits[0]);       // "苹果"（从 0 开始数！）
console.log(fruits.length);   // 3（一共几个）

// 对象 —— 有名字的属性集合（像一张表的一行数据）
const person = {
  name: "小明",
  age: 20,
  hobbies: ["编程", "音乐"]
};
console.log(person.name);     // "小明"
console.log(person.age);      // 20
```

> 💡 `console.log()` 是 JS 的「打印」功能，内容会显示在浏览器的开发者工具（按 F12 → Console 标签）里。调试代码时超级有用。

### 2.2 函数 —— 可复用的工具

函数就是把一段代码打包起来，取个名字，需要的时候调用它：

```javascript
// 定义一个函数
function greet(name) {
  return "你好，" + name + "！";
}

// 调用函数
const result = greet("小明");
console.log(result);   // "你好，小明！"
```

还有一种更简洁的写法叫**箭头函数**（在现代 JS 里更常见）：

```javascript
// 箭头函数写法
const greet = (name) => {
  return "你好，" + name + "！";
};

// 如果函数体只有一行，还能更短
const greet = (name) => "你好，" + name + "！";
```

**模板字符串（拼接文字的更好方式）：**

```javascript
const name = "小明";
const age = 20;

// 旧写法：用 + 号拼接（容易写错）
const msg1 = "我叫" + name + "，今年" + age + "岁";

// 新写法：用反引号 ` 和 ${} （推荐！）
const msg2 = `我叫${name}，今年${age}岁`;
```

> 💡 反引号 ` 在键盘左上角，数字 1 的左边。

### 2.3 条件判断和循环

```javascript
// if-else：如果...就...否则...
const score = 85;
if (score >= 90) {
  console.log("优秀");
} else if (score >= 60) {
  console.log("及格");       // 会执行这行
} else {
  console.log("不及格");
}

// for 循环：重复做某件事
const fruits = ["苹果", "香蕉", "橘子"];
for (let i = 0; i < fruits.length; i++) {
  console.log(fruits[i]);
}
// 输出：苹果、香蕉、橘子
```

### 2.4 数组的三大神器：map / filter / forEach

这三个方法在后面写 React/Next.js 时会**天天用到**，务必理解：

```javascript
const numbers = [1, 2, 3, 4, 5];

// forEach：遍历每个元素（逐个处理）
numbers.forEach(n => console.log(n));

// map：对每个元素做加工，返回新数组
// 比喻：流水线加工，1个进去1个出来
const doubled = numbers.map(n => n * 2);
console.log(doubled);  // [2, 4, 6, 8, 10]

// filter：只保留符合条件的元素
// 比喻：筛子，只留下能通过的
const bigNumbers = numbers.filter(n => n > 3);
console.log(bigNumbers);  // [4, 5]

// 可以链式调用
const result = numbers
  .filter(n => n > 2)     // 先筛选出 > 2 的 → [3, 4, 5]
  .map(n => n * 10);      // 再乘以 10 → [30, 40, 50]
```

## 三、DOM 操作 —— JS 控制网页的方式

DOM（文档对象模型）是 JS 与 HTML 之间的桥梁。通过 DOM，JS 可以找到页面上的元素，修改它的内容、样式、甚至增删元素。

```javascript
// 1. 找到元素
const title = document.getElementById("main-title");     // 通过 id 找
const buttons = document.querySelectorAll(".btn");        // 通过 class 找所有

// 2. 修改内容
title.textContent = "新标题";       // 改文字
title.style.color = "red";          // 改颜色

// 3. 监听事件（给元素装「耳朵」）
const btn = document.getElementById("my-button");
btn.addEventListener("click", () => {
  alert("你点击了按钮！");
});
```

## 四、TypeScript 入门

TypeScript = JavaScript + 类型标注。就这么简单。

### 4.1 为什么要用 TypeScript？

```javascript
// JavaScript 里这样写不会报错，但逻辑是错的
let age = 25;
age = "二十五岁";  // JS 不报错，但后面拿 age 做计算就炸了

// TypeScript 里会提前报错
let age: number = 25;
age = "二十五岁";  // ❌ 编译时就报错：不能把 string 赋给 number
```

类比你熟悉的数仓：TypeScript 的类型约束就像**建表时定义字段类型**，`age INT` 就是不能往里面插 VARCHAR。

### 4.2 基本类型标注

```typescript
// 基本类型
let name: string = "小明";
let age: number = 25;
let isStudent: boolean = true;

// 数组
let scores: number[] = [85, 90, 78];
let names: string[] = ["小明", "小红"];

// 函数参数和返回值
function add(a: number, b: number): number {
  return a + b;
}

add(1, 2);       // ✅
// add("1", 2);  // ❌ 编译报错
```

### 4.3 接口 interface —— 给对象定义「表结构」

这个概念对数仓同学特别亲切，interface 就是定义「这个对象长什么样」：

```typescript
// 定义「学生」的数据结构（就像建表的 DDL）
interface Student {
  name: string;       // 必填
  age: number;        // 必填
  major?: string;     // 可选（加了 ? 号）
}

// 使用
const stu1: Student = { name: "小红", age: 19 };           // ✅
const stu2: Student = { name: "小刚", age: 20, major: "计算机" }; // ✅
// const stu3: Student = { name: "小明" };                  // ❌ 缺少 age
```

### 4.4 文件后缀名一览

| 后缀 | 含义 | 什么时候用 |
|------|------|-----------|
| `.js` | 纯 JavaScript | 简单脚本 |
| `.ts` | TypeScript | 有类型检查的脚本 |
| `.jsx` | JavaScript + HTML 语法 | React 组件 |
| `.tsx` | TypeScript + HTML 语法 | React 组件（推荐） |

在 Next.js 项目里，你主要写的是 `.tsx` 文件。

## 五、动手练习

### 练习 1：计数器（掌握 DOM 操作和事件）

创建 `counter.html`，复制运行：

```html
<!DOCTYPE html>
<html>
<head>
  <title>计数器</title>
  <style>
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      font-family: Arial;
      background: #f0f0f0;
    }
    .counter-box {
      background: white;
      padding: 40px;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      text-align: center;
    }
    #display {
      font-size: 48px;
      font-weight: bold;
      margin: 20px;
      color: #333;
    }
    button {
      font-size: 24px;
      padding: 10px 24px;
      margin: 0 10px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      color: white;
    }
    .minus { background: #e74c3c; }
    .minus:hover { background: #c0392b; }
    .plus  { background: #2ecc71; }
    .plus:hover  { background: #27ae60; }
  </style>
</head>
<body>
  <div class="counter-box">
    <h2>我的计数器</h2>
    <button class="minus" id="btn-minus">-</button>
    <span id="display">0</span>
    <button class="plus" id="btn-plus">+</button>
  </div>

  <script>
    // 1. 创建一个变量记录当前数值
    let count = 0;

    // 2. 找到页面上的元素
    const display = document.getElementById("display");
    const plusBtn = document.getElementById("btn-plus");
    const minusBtn = document.getElementById("btn-minus");

    // 3. 点击 + 按钮 → 数值加 1，更新显示
    plusBtn.addEventListener("click", () => {
      count++;
      display.textContent = count;
    });

    // 4. 点击 - 按钮 → 数值减 1，更新显示
    minusBtn.addEventListener("click", () => {
      count--;
      display.textContent = count;
    });
  </script>
</body>
</html>
```

**运行后试着改改：**
- 把 `count++` 改成 `count += 5`，变成每次加 5
- 加一个「归零」按钮
- 让数字变成负数时显示红色（提示：`display.style.color = count < 0 ? "red" : "#333"`）

### 练习 2：待办事项清单（今日大作业）

创建 `todo.html`，这个项目综合了变量、函数、数组、DOM 操作：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>待办事项</title>
  <style>
    body { font-family: Arial; max-width: 500px; margin: 40px auto; padding: 0 20px; }
    h1 { color: #333; }
    #todo-input { width: 70%; padding: 10px; font-size: 16px; border: 2px solid #ddd; border-radius: 6px; }
    #todo-input:focus { border-color: #4A90D9; outline: none; }
    #add-btn { padding: 10px 20px; font-size: 16px; background: #4A90D9; color: white; border: none; border-radius: 6px; cursor: pointer; }
    #add-btn:hover { background: #357ABD; }
    #todo-list { list-style: none; padding: 0; }
    #todo-list li {
      padding: 12px; margin: 8px 0; background: #f8f8f8;
      border-radius: 6px; cursor: pointer;
      display: flex; justify-content: space-between; align-items: center;
    }
    #todo-list li:hover { background: #f0f0f0; }
    #todo-list li.done { text-decoration: line-through; color: #aaa; }
    .delete-btn { background: #e74c3c; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }
    #counter { margin-top: 16px; color: #888; }
  </style>
</head>
<body>
  <h1>📝 我的待办清单</h1>
  <div>
    <input type="text" id="todo-input" placeholder="输入新的待办事项...">
    <button id="add-btn">添加</button>
  </div>
  <ul id="todo-list"></ul>
  <div id="counter">剩余：0 项</div>

  <script>
    // ========== 数据层 ==========
    let todos = [];       // 存所有待办事项的数组
    let nextId = 1;       // 给每条待办一个唯一编号

    // ========== 添加待办 ==========
    function addTodo() {
      const input = document.getElementById("todo-input");
      const text = input.value.trim();  // .trim() 去掉首尾空格

      if (text === "") {
        alert("请输入内容");
        return;  // 空内容就不添加，直接返回
      }

      // 创建一条新待办（一个对象）
      const newTodo = {
        id: nextId++,     // 自增 ID
        text: text,       // 待办内容
        done: false       // 是否完成
      };

      todos.push(newTodo);  // 加入数组
      input.value = "";     // 清空输入框
      updateList();         // 刷新页面显示
    }

    // ========== 刷新显示 ==========
    function updateList() {
      const listElement = document.getElementById("todo-list");
      const counterElement = document.getElementById("counter");

      // 用 map 把每条待办变成 HTML，再拼起来
      listElement.innerHTML = todos.map(todo => `
        <li class="${todo.done ? 'done' : ''}" onclick="toggleTodo(${todo.id})">
          <span>${todo.done ? '✅' : '⬜'} ${todo.text}</span>
          <button class="delete-btn" onclick="event.stopPropagation(); deleteTodo(${todo.id})">删除</button>
        </li>
      `).join("");

      // 统计未完成数量
      const activeCount = todos.filter(t => !t.done).length;
      counterElement.textContent = `剩余：${activeCount} 项`;
    }

    // ========== 切换完成状态 ==========
    function toggleTodo(id) {
      const todo = todos.find(t => t.id === id);  // 用 find 找到对应项
      if (todo) {
        todo.done = !todo.done;  // 取反：true 变 false，false 变 true
        updateList();
      }
    }

    // ========== 删除待办 ==========
    function deleteTodo(id) {
      todos = todos.filter(t => t.id !== id);  // 用 filter 保留「不是这个 id」的
      updateList();
    }

    // ========== 事件绑定 ==========
    document.getElementById("add-btn").addEventListener("click", addTodo);
    document.getElementById("todo-input").addEventListener("keypress", (event) => {
      if (event.key === "Enter") addTodo();  // 按回车也能添加
    });

    updateList();  // 初始化
  </script>
</body>
</html>
```

**这个项目用到了今天学的几乎所有知识：**
- `let` / `const` 定义变量
- 对象和数组存储数据
- `map`、`filter`、`find` 操作数组
- 函数封装逻辑
- DOM 操作更新页面
- 事件监听处理用户交互

## 六、推荐学习资源

- 现代 JavaScript 教程（最好的 JS 教程，有中文）：https://zh.javascript.info/
- TypeScript 入门教程（阮一峰）：https://wangdoc.com/typescript/
- 豆包 Coding 页面（贴代码逐行讲解）：https://www.doubao.com/chat/coding

## 七、常见问题

**Q：JavaScript 和 TypeScript 先学哪个？**
先学 JS 基础（就是今天的内容），再自然过渡到 TS。在 Next.js 项目里你会直接用 TS，但 TS 的核心就是在 JS 基础上加类型标注，不难。

**Q：`let`、`const`、`var` 有什么区别？**
忘掉 `var`，它是旧时代的产物。只用 `let` 和 `const` 就行。默认用 `const`，需要改值时用 `let`。

**Q：箭头函数 `=>` 和普通 `function` 有什么区别？**
对初学者来说功能基本一样。箭头函数更简洁，在 React/Next.js 代码里更常见。先记住写法就行，细微差别以后再学。

---

> ✅ Day 2 完成！明天学 Tailwind CSS 和 shadcn/ui，让页面变好看。

<!-- series-nav-start -->

---
**📚 全栈开发**（3/6）

⬅️ 上一篇：[[Day1-HTML基础]] | ➡️ 下一篇：[[Day3-Tailwind和shadcn]]

<!-- series-nav-end -->
