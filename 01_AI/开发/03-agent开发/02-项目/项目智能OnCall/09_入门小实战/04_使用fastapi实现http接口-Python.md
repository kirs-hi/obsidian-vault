# 使用fastapi框架3分钟实现一个http接口（Python）

# FastAPI 是什么

FastAPI 是一个现代、高性能的 Python Web 框架，用于构建 API 服务。它基于 Python 类型提示，能够自动生成交互式 API 文档（Swagger UI），开发体验非常友好。

核心特点：

- **高性能 **：基于 Starlette 和 Pydantic，性能与 Go、Node\.js 框架相当

- **开发快速 **：利用类型提示自动补全和校验，减少大量样板代码

- **自带文档 **：启动即自动生成 Swagger UI 和 ReDoc 交互式文档，无需额外配置

- **易于上手 **：几行代码即可启动一个 HTTP 服务

官方文档：https://fastapi\.tiangolo\.com/

源码： [【飞书文档】项目源码下载 ](https://my.feishu.cn/https%3A%2F%2Ficnaxnmh86kx.feishu.cn%2Fwiki%2FUfYIwTsNKi6wopkYErTcfb8mnTc)使用fastapi实现一个http接口

# 安装依赖

```Bash

```

- fastapi ：Web 框架本身

- uvicorn ：ASGI 服务器，用于运行 FastAPI 应用

# 新增 Chat 接口

我们通过一个 chat 接口来演示如何使用 FastAPI 实现 HTTP GET 接口。

## 1\. 创建 FastAPI 应用实例

```Python

```

一行代码即可创建应用实例，不需要额外的目录结构和脚手架。

## 2\. 定义 Chat 接口

```Python

```

- @app\.get\("/api/chat"\) ：声明这是一个 GET 请求，路径为 /api/chat

- 函数参数 id 和 question 会自动映射为 URL 查询参数（Query Parameters）

- 直接返回字典，FastAPI 会自动序列化为 JSON 响应

## 3\. 完整代码

将以上内容组合，完整的 main\.py 如下：

```Python

```

# 运行

```Bash

```

- main:app ： main\.py 文件中的 app 实例

- \-\-reload ：代码修改后自动重启，适合开发阶段使用

- \-\-port 6872 ：指定端口号为 6872

看到如下输出就说明启动成功了：

```Plaintext

```

# 调用接口

## 浏览器直接访问

打开浏览器，访问：

```Plaintext

```

返回结果：

```JSON

```

## 使用 curl 命令

```Bash

```

## 交互式文档

FastAPI 自动生成了 Swagger UI，访问以下地址即可在页面上直接测试接口：

```Plaintext

```

这是 FastAPI 的一大亮点——无需任何额外配置，赶快试一试吧～
