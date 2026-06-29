# 使用goframe框架3分钟实现一个http接口（Go）

# goframe框架

GoFrame 是一款模块化、高性能的 Go 语言开发框架。 如果您想使用 Golang 开发一个业务型项目，无论是小型还是中大型项目， GoFrame 是您的不二之选。如果您想开发一个 Golang 组件库， GoFrame 提供开箱即用、丰富强大的基础组件库也能助您的工作事半功倍。 https://goframe\.org/

# 安装框架

https://goframe\.org/quick/scaffold\-index

使用脚手架快速启动一个http服务

```Bash

```

[配置Goland ](https://my.feishu.cn/https%3A%2F%2Fgoframe.org%2Fdocs%2Fcli%2Fgen-ctrl%23%25E8%2587%25AA%25E5%258A%25A8%25E6%25A8%25A1%25E5%25BC%258F%25E6%258E%25A8%25E8%258D%2590)，使得能自动生成代码

# 新增chat接口

1. 首先，我们在api目录下依葫芦画瓢创建chat/v1目录，并编写Chat接口

![[GCvdbWO7xov4a4x9KKRcHOYlnwg.png]]

```Go

```

1. Ctrl\+S保存，此时框架会自动帮我们生成internal/controller/chat控制层的代码。我们返回一个chat demo字符串回去

![[QgMZbE5mGoIjYzxZsQXcpuBLned.png]]

```Bash

```

1. 将我们刚才写的chat控制器绑定上去

![[XfYsb8wlroXlQwxtnnBcuO8Tnff.png]]

1. 最后，我们需要将collector层的返回值返回出去

![[KXMMbaThXojWArxcJVwcdnhZnsb.png]]

```Go

```

# 运行

![[DzjCbu9wZo737oxi5AGcHyXCnRe.png]]

go run main\.go 看到route里面有刚才写的接口就说明成功了，赶快试一试吧～

![[MkEmb1WyXozGiYx9AoFcoy4Pnld.png]]
