# 使用springboot框架3分钟实现一个http接口（Java）

# Spring Boot框架

Spring Boot 是基于 Java 的轻量级、开箱即用的应用开发框架。它极大简化了 Spring 应用的搭建和开发过程，无论是小型服务还是中大型企业级项目，Spring Boot 都是 Java Web 开发的首选。 https://spring\.io/projects/spring\-boot

安装环境

1. 安装 Maven（或使用 IDEA 自带的 Maven）

# 快速创建项目

创建 \`pom\.xml\`，引入 Spring Boot 父工程和 Web Starter：

```XML

```

创建启动类 \`src/main/java/com/example/App\.java\`：

```Java

```

# 新增chat接口

下面我们动手写一个 \`/api/chat\` 接口，体验 Spring Boot 开发的完整流程。

## 1\. 创建请求和响应类

在 \`src/main/java/com/example/model/\` 目录下新建两个类：

```TypeScript

```

```TypeScript

```

## 2\. 创建统一响应包装类

在 \`src/main/java/com/example/model/\` 目录下新建：

```TypeScript

```

## 3\. 编写 Controller

在 \`src/main/java/com/example/controller/\` 目录下新建 \`ChatController\.java\`：

```Java

```

就这么简单！Spring Boot 通过 \`@RestController\` 和 \`@GetMapping\` 注解，几行代码就完成了接口定义。请求参数会自动绑定到 \`ChatRequest\` 对象上。

# 运行

在项目根目录执行：

```Plaintext

```

或者直接在 IDEA 中点击 \`App\.java\` 的运行按钮。

看到控制台输出类似以下内容就说明启动成功了：

```Plaintext

```

打开浏览器访问：

http://localhost:8080/api/chat?id\=1&question\=hello

返回结果：

```Plaintext

```

大功告成，赶快试一试吧～
