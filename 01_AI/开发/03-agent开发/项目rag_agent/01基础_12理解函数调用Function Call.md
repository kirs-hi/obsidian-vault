---
title: "《AI大模型Ragent项目》第12小节：理解函数调用Function Call"
source: "https://articles.zsxq.com/id_bkn8qirw05xd.html"
author:
  - "[[马丁]]"
published:
created: 2026-06-05
description:
tags:
  - "clippings"
---
[来自： 拿个offer-开源&项目实战](https://wx.zsxq.com/group/51121244585524)

上一篇讲完了 [[06-RAG|RAG]] 的生成策略，你已经能搭建一个完整的 RAG 系统：用户问知识库里的问题，系统检索相关文档，生成答案，还能标注引用来源。看起来很完美，但实际跑起来你会发现——用户的需求不只是查文档。

假设你在一家公司做企业知识库助手，用户问“公司的年假制度是什么”，RAG 系统检索到《员工手册》里的年假政策，回答得很好。但用户接着问“我还剩几天年假”，系统就懵了：知识库里有年假制度，但没有这个用户的具体年假数据。这需要查 HR 系统，而 RAG 系统只会检索文档，不会调接口。

再比如用户问“帮我查订单 #12345 的物流”，RAG 系统检索到物流查询的操作指南，但查不到这个订单的实时物流信息——这需要调物流系统的 API。

这就是 RAG 的能力边界：它能回答知识库里的问题，但干不了活。接下来要讲的 Function Call（函数调用），就是让 RAG 系统从只能查知识库升级到能查数据、能调接口、能干活。

## 从查知识库到干活：RAG 的能力边界

### 1\. RAG 只能查知识库的局限

回顾一下 RAG 的工作流程：用户提问 → [[01基础_10向量检索策略与召回优化|向量检索]] → 召回相关文档 → 生成答案。整个流程的数据来源是知识库（[[01基础_09向量数据库的原理与选型|向量数据库]]里存的文档 chunk），所以 RAG 只能回答“知识库里有什么”。

但企业场景下，用户的需求远不止查文档：

- **查实时数据** ：我还剩几天年假？我这个月的考勤记录？我的销售业绩排名？

- **查业务状态** ：订单 #12345 的物流到哪了？工单 #678 处理到哪一步了？

- **执行操作** ：帮我请 3 天年假、帮我提交报销申请、帮我发一条通知给项目组

这些需求的共同点是：答案不在知识库里，需要调用业务系统的接口或数据库查询。

### 2\. 传统方案的问题

面对这种需求，传统的做法有两种：

#### 2.1 方案一：在 Prompt 里写死兜底回复

```
如果用户问年假余额，请回复："您可以访问 HR 系统查询年假余额，地址：https://hr.company.com"
如果用户问订单物流，请回复："您可以在订单详情页查看物流信息"
```

这种方案太死板，用户体验差。用户问“我还剩几天年假”，系统回复“请访问 HR 系统查询”，用户心里想：你不就是个智能助手吗，为什么不能直接告诉我？

#### 2.2 方案二：用规则匹配用户意图，然后调接口

```
if (userQuestion.contains("年假")) {
    int days = hrSystem.getAnnualLeave(userId);
    return "您还剩 " + days + " 天年假";
}
if (userQuestion.contains("订单") && userQuestion.contains("物流")) {
    String status = logisticsSystem.getOrderStatus(orderId);
    return "订单物流状态：" + status;
}
```

这种方案的问题是：规则写不完，维护成本高。用户可能问“我的假期余额”、“还有多少天假”、“年假还剩多少”，你要为每种表达都写一条规则吗？而且用户问题里可能没有明确的关键词，比如“我想请假，但不知道还有没有额度”，这种问题用规则很难匹配。

更关键的是，这种方案把判断用户意图的逻辑硬编码在代码里，每次新增一个工具（比如新增查考勤记录的功能），你都要改代码、加规则、重新部署。

我们需要一种更灵活的方案：让模型自己判断什么时候该调工具、该调哪个工具、该传什么参数。这就是 Function Call。

## Function Call 是什么

### 1\. Function Call 的本质：模型输出调用意图

先说结论： **模型不是真的调函数，它只是输出一个 JSON，告诉你“我觉得应该调某个函数，参数是这些”。真正执行函数的是你的代码。**

打个比方：你去餐厅吃饭，服务员（模型）拿着菜单（工具列表）问你想吃什么（用户问题）。你说“我想吃点清淡的”，服务员根据菜单推荐“那来一份清蒸鲈鱼吧”（输出调用意图）。但服务员不会做菜，做菜的是厨房（你的代码）。服务员只是把你的需求翻译成厨房能理解的订单（JSON 格式的函数调用）。

具体来说，Function Call 的流程是这样的：

- 1.
	你定义一些工具（函数），每个工具有名字、描述、参数定义

- 2.
	把工具列表和用户问题一起发给模型

- 3.
	模型判断需要调用哪个工具，输出一个 JSON（叫 `tool_calls` ），里面包含函数名和参数

- 4.
	你解析这个 JSON，执行对应的函数，拿到结果

- 5.
	把函数执行结果返回给模型

- 6.
	模型基于结果生成最终答案

注意第 3 步和第 4 步的区别：模型只是输出“应该调 getUserAnnualLeave 函数，参数是 userId=12345”，但不会真的去调这个函数。你的代码拿到这个 JSON 后，才去执行 `getUserAnnualLeave(12345)` ，拿到结果（比如：剩余 5 天），然后把结果返回给模型。

### 2\. Function Call 的完整流程

用一个完整的例子说明：

**场景** ：用户问“我还剩几天年假”

**第一轮：发送工具列表和用户问题**

你的代码构建一个请求，包含：

- 用户问题：我还剩几天年假

- 工具列表： `getUserAnnualLeave` （查询用户年假余额）

发送给模型。

**第一轮响应：模型输出调用意图**

模型分析用户问题，发现需要查年假余额，于是输出：

```
{
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "getUserAnnualLeave",
        "arguments": "{\"userId\": \"12345\"}"
      }
    }
  ]
}
```

注意模型并没有生成最终答案，而是告诉你需要调用 getUserAnnualLeave 函数。

**你的代码执行函数**

你解析 `tool_calls` ，发现要调 `getUserAnnualLeave` ，参数是 `userId=12345` 。你执行这个函数（可能是查数据库、调 HR 系统 API），拿到结果：

```
{
  "remainingDays": 5,
  "totalDays": 10,
  "usedDays": 5
}
```

**第二轮：把结果返回给模型**

你构建第二轮请求，包含：

- 第一轮的用户问题

- 第一轮的模型响应（带 `tool_calls` ）

- 函数执行结果（上面的 JSON）

发送给模型。

**第二轮响应：模型生成最终答案**

模型基于函数执行结果，生成最终答案：

```
您还剩 5 天年假（总共 10 天，已使用 5 天）。
```

整个流程是一个[[01基础_16多轮对话记忆设计|多轮对话]]：第一轮模型输出调用意图，你执行函数，第二轮模型基于结果生成答案。

下面用时序图展示完整流程：

![无法获取该图片](https://oss.open8gu.com/image-20260227152149719.png "无法获取该图片")

### 3\. 为什么需要 Function Call

对比一下没有 Function Call 的方案：

**方案一：在 Prompt 里写死规则**

- 问题：不灵活，用户体验差

- Function Call 的优势：模型根据用户问题动态判断是否需要调工具，用户无感知

**方案二：用传统 NLP 做[[01基础_18意图识别与多路由调度策略|意图识别]]**

- 问题：规则写不完，维护成本高，难以处理复杂表达

- Function Call 的优势：模型理解自然语言，能处理各种表达方式（"我还剩几天年假"、"我的假期余额"、"年假还有多少"都能识别）

**方案三：让模型在回答里生成函数调用代码**

- 问题：模型可能生成错误的代码，不安全，难以解析

- Function Call 的优势：输出格式标准化（JSON），易于解析，参数类型有校验

Function Call 的核心优势是： **把判断什么时候该调工具的逻辑交给模型，把执行工具的逻辑留给项目代码** 。模型擅长理解自然语言和意图识别，你的代码擅长执行具体的业务逻辑，各司其职。

下面用流程图展示模型如何判断是否调用工具：

## OpenAI Function Call 协议详解

Function Call 最早由 OpenAI 提出，现在已经成为事实标准，主流大模型服务商（OpenAI、Anthropic、Google、国内的通义千问、智谱、DeepSeek 等）都支持这个协议。协议的核心是定义工具的格式和模型响应的格式。

### 1\. 工具定义格式（tools 数组）

你需要把工具列表以 JSON 数组的形式发给模型，每个工具的定义格式如下：

```
{
  "type": "function",
  "function": {
    "name": "getUserAnnualLeave",
    "description": "查询用户的年假余额，包括总天数、已使用天数、剩余天数",
    "parameters": {
      "type": "object",
      "properties": {
        "userId": {
          "type": "string",
          "description": "用户 ID"
        }
      },
      "required": ["userId"]
    }
  }
}
```

字段说明：

- `type` ：固定为 `function`

- `function.name` ：函数名，模型会在 `tool_calls` 里返回这个名字

- `function.description` ：函数的功能描述， **这是模型判断是否调用该工具的关键依据**

- `function.parameters` ：参数定义，使用 JSON Schema 格式

#### 1.1 function.description 的重要性

`description` 是模型判断是否调用该工具的关键。描述要清晰、具体，说明：

- 工具的功能是什么

- 适用于什么场景

- 参数的含义

举个例子，如果你定义了两个工具：

```
[
  {
    "type": "function",
    "function": {
      "name": "getUserAnnualLeave",
      "description": "查询用户的年假余额"
    }
  },
  {
    "type": "function",
    "function": {
      "name": "getUserSickLeave",
      "description": "查询用户的病假余额"
    }
  }
]
```

用户问“我还剩几天年假”，模型会根据 `description` 判断应该调用 `getUserAnnualLeave` 而不是 `getUserSickLeave` 。

如果 `description` 写得不清楚（比如只写“查询用户信息”），模型可能会选错工具。

#### 1.2 function.parameters 的 JSON Schema 格式

`parameters` 使用 JSON Schema 格式定义参数，常用字段：

- `type` ：参数类型，常用 `"object"` （表示参数是一个对象）

- `properties` ：对象的属性，每个属性有 `type` （类型）和 `description` （描述）

- `required` ：必填参数列表

示例：

```
{
  "type": "object",
  "properties": {
    "userId": {
      "type": "string",
      "description": "用户 ID"
    },
    "year": {
      "type": "integer",
      "description": "查询的年份，默认为当前年份"
    }
  },
  "required": ["userId"]
}
```

这个定义表示：函数有两个参数 `userId` 和 `year` ， `userId` 是必填的（类型为字符串）， `year` 是可选的（类型为整数）。

### 2\. 请求格式：把工具列表发给模型

完整的请求 JSON 示例：

```
{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": "我还剩几天年假"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "getUserAnnualLeave",
        "description": "查询用户的年假余额",
        "parameters": {
          "type": "object",
          "properties": {
            "userId": {
              "type": "string",
              "description": "用户 ID"
            }
          },
          "required": ["userId"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

字段说明：

- `model` ：模型名称

- `messages` ：对话历史，格式和普通 Chat API 一样

- `tools` ：工具列表

- `tool_choice` ：控制模型是否调用工具，可选值：
	- `auto` ：模型自己判断是否需要调用工具（默认值）
	- `none` ：不调用工具，只生成文本回答
	- `required` ：必须调用工具，不能只生成文本回答
	- `{"type": "function", "function": {"name": "getUserAnnualLeave"}}` ：指定调用某个工具

大部分场景下用 `auto` 就行，让模型自己判断。

### 3\. 响应格式：模型输出 tool\_calls

如果模型判断需要调用工具，响应格式如下：

```
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "getUserAnnualLeave",
              "arguments": "{\"userId\": \"12345\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

关键字段：

- `message.tool_calls` ：工具调用数组，可能包含多个工具调用（模型可能一次调用多个工具）

- `tool_calls[0].id` ：调用 ID，第二轮请求时需要带上这个 ID

- `tool_calls[0].function.name` ：要调用的函数名

- `tool_calls[0].function.arguments` ：函数参数， **注意是 JSON 字符串，不是 JSON 对象** ，需要你自己解析

- `finish_reason` ：值为 `tool_calls` 表示模型输出了工具调用，而不是 `stop` （正常结束）

注意 `message.content` 是 `null` ，因为模型没有生成文本回答，而是输出了工具调用。

### 4\. 第二轮请求：把函数执行结果返回给模型

你执行完函数后，需要把结果返回给模型，让模型生成最终答案。第二轮请求的 `messages` 数组要包含完整的对话历史：

```
{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": "我还剩几天年假"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "getUserAnnualLeave",
            "arguments": "{\"userId\": \"12345\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "content": "{\"remainingDays\": 5, \"totalDays\": 10, \"usedDays\": 5}"
    }
  ]
}
```

关键点：

- 1.
	第一条消息：用户的原始问题

- 2.
	第二条消息：第一轮的模型响应（带 `tool_calls` ）， `role` 是 `assistant`

- 3.
	第三条消息：函数执行结果， `role` 是 `tool` ， `tool_call_id` 要和第二条消息里的 `id` 对应， `content` 是函数返回值（JSON 字符串）

模型基于这些信息生成最终答案：

```
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "您还剩 5 天年假（总共 10 天，已使用 5 天）。"
      },
      "finish_reason": "stop"
    }
  ]
}
```

这次 `finish_reason` 是 `stop` ，表示模型生成了最终答案。

## Java 实战：完整的 Function Call 流程

### 1\. 场景设定

我们做一个企业知识库助手，支持两个工具：

- 1.
	`getUserAnnualLeave` ：查询用户年假余额

- 2.
	`getOrderStatus` ：查询订单状态

用户问“我还剩几天年假”，系统调用 `getUserAnnualLeave` ，返回结果，模型生成答案。

技术栈：

- Java + OkHttp 调用 SiliconFlow API

- 模型：Qwen/Qwen2.5-7B-Instruct（支持 Function Call）

- Gson 处理 JSON

> 完整示例可以查看 [TinyRAG](https://github.com/nageoffer/tinyrag) 项目 com.nageoffer.ai.tinyrag.function 目录下代码。

### 2\. Maven 依赖

```
<dependencies>
    <dependency>
        <groupId>com.squareup.okhttp3</groupId>
        <artifactId>okhttp</artifactId>
        <version>4.12.0</version>
    </dependency>
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.13.1</version>
    </dependency>
</dependencies>
```

### 3\. 完整代码示例

```
public class RAGFunctionCallDemo {

    private static final String API_KEY = "YOUR_API_KEY";
    private static final String API_URL = "https://api.siliconflow.cn/v1/chat/completions";
    private static final String MODEL = "deepseek-ai/DeepSeek-V3";

    private static final OkHttpClient client = new OkHttpClient();
    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    public static void main(String[] args) throws IOException {
        // 用户问题
        String userQuestion = "我还剩几天年假";
        System.out.println("用户问题：" + userQuestion);
        System.out.println("\n" + "=".repeat(60) + "\n");

        // 第一轮：发送工具列表和用户问题
        JsonObject firstResponse = callModelWithTools(userQuestion);
        System.out.println("第一轮响应：");
        System.out.println(gson.toJson(firstResponse));
        System.out.println("\n" + "=".repeat(60) + "\n");

        // 解析 tool_calls
        JsonArray toolCalls = firstResponse.getAsJsonArray("choices")
                .get(0).getAsJsonObject()
                .getAsJsonObject("message")
                .getAsJsonArray("tool_calls");

        if (CollUtil.isEmpty(toolCalls)) {
            System.out.println("模型没有调用工具，直接返回答案");
            return;
        }

        // 执行函数
        JsonObject toolCall = toolCalls.get(0).getAsJsonObject();
        String functionName = toolCall.getAsJsonObject("function").get("name").getAsString();
        String arguments = toolCall.getAsJsonObject("function").get("arguments").getAsString();
        String toolCallId = toolCall.get("id").getAsString();

        System.out.println("模型要调用的函数：" + functionName);
        System.out.println("函数参数：" + arguments);
        System.out.println("\n" + "=".repeat(60) + "\n");

        // 执行函数（这里用 mock 数据）
        String functionResult = executeFunction(functionName, arguments);
        System.out.println("函数执行结果：" + functionResult);
        System.out.println("\n" + "=".repeat(60) + "\n");

        // 第二轮：把结果返回给模型
        JsonObject secondResponse = callModelWithFunctionResult(
                userQuestion, toolCall, toolCallId, functionResult);

        System.out.println("第二轮响应：");
        System.out.println(gson.toJson(secondResponse));
        System.out.println("\n" + "=".repeat(60) + "\n");

        // 提取最终答案
        String finalAnswer = secondResponse.getAsJsonArray("choices")
                .get(0).getAsJsonObject()
                .getAsJsonObject("message")
                .get("content").getAsString();

        System.out.println("最终答案：" + finalAnswer);
    }

    /**
     * 第一轮调用：发送工具列表和用户问题
     */
    private static JsonObject callModelWithTools(String userQuestion) throws IOException {
        // 定义工具列表
        JsonArray tools = new JsonArray();

        // 工具 1：查询年假余额
        JsonObject tool1 = new JsonObject();
        tool1.addProperty("type", "function");
        JsonObject function1 = new JsonObject();
        function1.addProperty("name", "getUserAnnualLeave");
        function1.addProperty("description", "查询用户的年假余额，包括总天数、已使用天数、剩余天数");
        JsonObject parameters1 = new JsonObject();
        parameters1.addProperty("type", "object");
        JsonObject properties1 = new JsonObject();
        JsonObject userId1 = new JsonObject();
        userId1.addProperty("type", "string");
        userId1.addProperty("description", "用户 ID");
        properties1.add("userId", userId1);
        parameters1.add("properties", properties1);
        JsonArray required1 = new JsonArray();
        required1.add("userId");
        parameters1.add("required", required1);
        function1.add("parameters", parameters1);
        tool1.add("function", function1);
        tools.add(tool1);

        // 工具 2：查询订单状态
        JsonObject tool2 = new JsonObject();
        tool2.addProperty("type", "function");
        JsonObject function2 = new JsonObject();
        function2.addProperty("name", "getOrderStatus");
        function2.addProperty("description", "查询订单的物流状态和详细信息");
        JsonObject parameters2 = new JsonObject();
        parameters2.addProperty("type", "object");
        JsonObject properties2 = new JsonObject();
        JsonObject orderId = new JsonObject();
        orderId.addProperty("type", "string");
        orderId.addProperty("description", "订单号");
        properties2.add("orderId", orderId);
        parameters2.add("properties", properties2);
        JsonArray required2 = new JsonArray();
        required2.add("orderId");
        parameters2.add("required", required2);
        function2.add("parameters", parameters2);
        tool2.add("function", function2);
        tools.add(tool2);

        // 构建请求体
        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("model", MODEL);

        JsonArray messages = new JsonArray();

        // ★★★ 新增：添加系统消息，带上用户ID ★★★
        JsonObject systemMessage = new JsonObject();
        systemMessage.addProperty("role", "system");
        systemMessage.addProperty("content", "当前登录用户的ID是: user_12345");
        messages.add(systemMessage);

        JsonObject userMessage = new JsonObject();
        userMessage.addProperty("role", "user");
        userMessage.addProperty("content", userQuestion);
        messages.add(userMessage);

        requestBody.add("messages", messages);
        requestBody.add("tools", tools);
        requestBody.addProperty("tool_choice", "auto");

        // 发送请求
        return sendRequest(requestBody);
    }

    /**
     * 第二轮调用：把函数执行结果返回给模型
     */
    private static JsonObject callModelWithFunctionResult(
            String userQuestion, JsonObject toolCall, String toolCallId, String functionResult) throws IOException {

        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("model", MODEL);

        JsonArray messages = new JsonArray();

        // 第一条消息：用户问题
        JsonObject userMessage = new JsonObject();
        userMessage.addProperty("role", "user");
        userMessage.addProperty("content", userQuestion);
        messages.add(userMessage);

        // 第二条消息：第一轮的模型响应（带 tool_calls）
        JsonObject assistantMessage = new JsonObject();
        assistantMessage.addProperty("role", "assistant");
        assistantMessage.add("content", JsonNull.INSTANCE);
        JsonArray toolCalls = new JsonArray();
        toolCalls.add(toolCall);
        assistantMessage.add("tool_calls", toolCalls);
        messages.add(assistantMessage);

        // 第三条消息：函数执行结果
        JsonObject toolMessage = new JsonObject();
        toolMessage.addProperty("role", "tool");
        toolMessage.addProperty("tool_call_id", toolCallId);
        toolMessage.addProperty("content", functionResult);
        messages.add(toolMessage);

        requestBody.add("messages", messages);

        // 发送请求
        return sendRequest(requestBody);
    }

    /**
     * 执行函数（这里用 mock 数据模拟）
     */
    private static String executeFunction(String functionName, String arguments) {
        JsonObject args = gson.fromJson(arguments, JsonObject.class);

        if ("getUserAnnualLeave".equals(functionName)) {
            // 模拟查询 HR 系统
            String userId = args.get("userId").getAsString();
            JsonObject result = new JsonObject();
            result.addProperty("userId", userId);
            result.addProperty("remainingDays", 5);
            result.addProperty("totalDays", 10);
            result.addProperty("usedDays", 5);
            return gson.toJson(result);
        } else if ("getOrderStatus".equals(functionName)) {
            // 模拟查询订单系统
            String orderId = args.get("orderId").getAsString();
            JsonObject result = new JsonObject();
            result.addProperty("orderId", orderId);
            result.addProperty("status", "运输中");
            result.addProperty("location", "北京市朝阳区分拨中心");
            result.addProperty("estimatedDelivery", "2026-02-28");
            return gson.toJson(result);
        }

        return "{\"error\": \"未知的函数\"}";
    }

    /**
     * 发送 HTTP 请求
     */
    private static JsonObject sendRequest(JsonObject requestBody) throws IOException {
        RequestBody body = RequestBody.create(
                gson.toJson(requestBody),
                MediaType.parse("application/json"));

        Request request = new Request.Builder()
                .url(API_URL)
                .addHeader("Authorization", "Bearer " + API_KEY)
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build();

        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("请求失败：" + response);
            }
            String responseBody = response.body().string();
            return gson.fromJson(responseBody, JsonObject.class);
        }
    }
}
```

### 4\. 运行效果展示

运行上面的代码，输出如下：

```
用户问题：我还剩几天年假

============================================================

第一轮响应：
{
  "id": "019c9e1d26c3d808e4af0dae8cb9e15a",
  "object": "chat.completion",
  "created": 1772179236,
  "model": "deepseek-ai/DeepSeek-V3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "019c9e1d2c66c68e888c9086c45216e4",
            "type": "function",
            "function": {
              "name": "getUserAnnualLeave",
              "arguments": "{\"userId\":\"user_12345\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 195,
    "completion_tokens": 23,
    "total_tokens": 218,
    "completion_tokens_details": {
      "reasoning_tokens": 0
    }
  },
  "system_fingerprint": ""
}

============================================================

模型要调用的函数：getUserAnnualLeave
函数参数：{"userId":"user_12345"}

============================================================

函数执行结果：{
  "userId": "user_12345",
  "remainingDays": 5,
  "totalDays": 10,
  "usedDays": 5
}

============================================================

第二轮响应：
{
  "id": "019c9e1d2cd655432ba32666031ca899",
  "object": "chat.completion",
  "created": 1772179238,
  "model": "deepseek-ai/DeepSeek-V3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "根据查询结果，你的年假使用情况如下：\n\n- **总年假天数**：10天\n- **已使用天数**：5天\n- **剩余天数**：5天\n\n你还剩5天年假可以安排使用。如果有其他需求或需要帮助规划休假，随时告诉我哦！"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 79,
    "completion_tokens": 64,
    "total_tokens": 143
  },
  "system_fingerprint": ""
}

============================================================

最终答案：根据查询结果，你的年假使用情况如下：

- **总年假天数**：10天
- **已使用天数**：5天
- **剩余天数**：5天

你还剩5天年假可以安排使用。如果有其他需求或需要帮助规划休假，随时告诉我哦！
```

整个流程：

- 1.
	用户问“我还剩几天年假”

- 2.
	模型判断需要调用 `getUserAnnualLeave` 函数，输出 `tool_calls`

- 3.
	代码解析 `tool_calls` ，执行函数，拿到结果（剩余 5 天）

- 4.
	把结果返回给模型

- 5.
	模型生成最终答案：您还剩 5 天年假（总共 10 天，已使用 5 天）

### 5\. 代码要点说明

#### 5.1 工具定义的构建

用 Gson 构建 JSON 比较繁琐，实际项目中可以封装一个工具类：

```
public class FunctionTool {
    private String name;
    private String description;
    private Map<String, Object> parameters;

    public JsonObject toJson() {
        // 转换为 OpenAI Function Call 格式
    }
}
```

或者直接用 JSON 字符串定义工具，然后用 `gson.fromJson()` 解析。

#### 5.2 参数解析

`function.arguments` 是 JSON 字符串，不是 JSON 对象，需要先解析：

```
String arguments = toolCall.getAsJsonObject("function").get("arguments").getAsString();
JsonObject args = gson.fromJson(arguments, JsonObject.class);
String userId = args.get("userId").getAsString();
```

#### 5.3 函数路由

根据 `function.name` 路由到对应的函数实现：

```
if ("getUserAnnualLeave".equals(functionName)) {
    return getUserAnnualLeave(args);
} else if ("getOrderStatus".equals(functionName)) {
    return getOrderStatus(args);
}
```

实际项目中可以用策略模式或反射来实现动态路由。

#### 5.4 第二轮请求的消息构建

第二轮请求的 `messages` 数组要包含完整的对话历史，顺序不能错：

- 1.
	用户问题（role=user）

- 2.
	第一轮模型响应（role=assistant，带 tool\_calls）

- 3.
	函数执行结果（role=tool，带 tool\_call\_id）

如果顺序错了或者缺了某条消息，模型可能无法正确生成答案。

## Function Call 在 RAG 系统中的应用

### 1\. 意图识别：查知识库 vs 调工具

Function Call 可以作为意图识别的手段。你可以定义一个 `searchKnowledgeBase` 工具：

```
{
  "type": "function",
  "function": {
    "name": "searchKnowledgeBase",
    "description": "在企业知识库中搜索相关文档，适用于查询公司制度、产品文档、操作指南等静态知识",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "搜索关键词"
        }
      },
      "required": ["query"]
    }
  }
}
```

同时定义业务工具（如 `getUserAnnualLeave` 、 `getOrderStatus` ）。模型根据用户问题判断：

- 用户问“年假制度是什么”，调用 `searchKnowledgeBase` ，你的代码执行 RAG 检索

- 用户问“我还剩几天年假”，调用 `getUserAnnualLeave` ，你的代码查 HR 系统

这样就实现了查知识库 vs 调工具的自动路由。

### 2\. 混合场景：知识检索 + 工具调用

有些场景需要同时查知识库和调工具。比如用户问“我的订单 #12345 能退货吗”：

- 1.
	先调用 `getOrderStatus` 查订单信息（购买时间、商品类型）

- 2.
	再调用 `searchKnowledgeBase` 检索退货政策

- 3.
	模型综合两部分信息生成答案

这种场景下，模型可能一次输出多个 `tool_calls` （如果支持并行调用），或者分多轮调用（先调工具 A，根据结果决定是否调工具 B）。

实现方式：

```
// 第一轮：模型输出 tool_calls，可能包含多个工具
JsonArray toolCalls = ...;
for (JsonElement toolCall : toolCalls) {
    String functionName = ...;
    String result = executeFunction(functionName, arguments);
    // 把结果添加到 messages 数组
}

// 第二轮：把所有结果返回给模型
// 模型可能继续输出 tool_calls（需要调用更多工具），或者生成最终答案
```

需要循环处理，直到模型不再输出 `tool_calls` （ `finish_reason` 为 `stop` ）。

### 3\. 工具调用的优先级和策略

如果定义了多个工具，模型怎么选择？

**方法一：通过 description 引导**

在工具描述中给出优先级提示：

```
{
  "name": "searchKnowledgeBase",
  "description": "在企业知识库中搜索相关文档。优先使用此工具查询公司制度、产品文档等静态知识。"
}
```

**方法二：通过 tool\_choice 参数控制**

如果你明确知道某个场景应该调用某个工具，可以用 `tool_choice` 指定：

```
{
  "tool_choice": {
    "type": "function",
    "function": {"name": "getUserAnnualLeave"}
  }
}
```

**方法三：分阶段调用**

先用一个轻量级的意图识别工具判断用户需求类型，再根据类型选择具体的工具。

## Function Call 的局限性与痛点

Function Call 很好用，但实际项目中会遇到一些问题：

### 1\. 工具定义的维护成本

每个工具都要手写 JSON Schema，参数多了很繁琐。比如一个工具有 10 个参数，你要写 10 个 `properties` ，还要写 `description` 、 `type` 、 `required` 。

工具增加或修改时，要同步更新定义。如果你的工具是从数据库表自动生成的（比如每个表对应一个查询工具），手写 JSON Schema 就不现实了。

### 2\. 跨语言和跨系统的集成问题

你的工具可能是 Java 实现的，别人的工具可能是 Python 实现的，还有的工具是 HTTP API。怎么让模型能调用不同语言、不同系统的工具？

Function Call 协议本身不解决这个问题，你需要自己实现一个工具注册和调用的框架：

- 定义统一的工具描述格式

- 实现跨语言的 RPC 调用（如 gRPC、HTTP）

- 处理不同系统的认证和权限

### 3\. 工具的权限和安全控制

模型可能会调用不该调用的工具，或者传入不合法的参数。比如：

- 用户 A 问“帮我查用户 B 的年假”，模型调用 `getUserAnnualLeave(userId=B)` ，但用户 A 没有权限查用户 B 的数据

- 用户传入恶意参数（SQL 注入、路径穿越等）

需要在执行函数前做权限校验和参数校验：

```
private static String executeFunction(String functionName, String arguments, String currentUserId) {
    JsonObject args = gson.fromJson(arguments, JsonObject.class);

    if ("getUserAnnualLeave".equals(functionName)) {
        String userId = args.get("userId").getAsString();
        // 权限校验：只能查自己的数据
        if (!userId.equals(currentUserId)) {
            return "{\"error\": \"无权限查询其他用户的数据\"}";
        }
        // 参数校验：userId 格式检查
        if (!userId.matches("\\d+")) {
            return "{\"error\": \"用户 ID 格式错误\"}";
        }
        // 执行函数
        return getUserAnnualLeave(userId);
    }
}
```

但这些逻辑都要自己写，没有统一的框架支持。

### 4\. 工具调用的可观测性

模型调用了哪些工具、传了什么参数、执行结果是什么、耗时多少，这些信息需要自己记录和追踪：

```
private static String executeFunction(String functionName, String arguments) {
    long startTime = System.currentTimeMillis();
    String result = ...;
    long endTime = System.currentTimeMillis();

    // 记录日志
    logger.info("Function: {}, Arguments: {}, Result: {}, Duration: {}ms",
            functionName, arguments, result, endTime - startTime);

    return result;
}
```

如果工具调用链路很长（调用工具 A → 工具 A 内部调用工具 B → 工具 B 查数据库），追踪起来很麻烦。

### 5\. 引出下一篇：MCP 协议

Function Call 解决了让模型调用工具的问题，但带来了新的问题：

- 工具定义的维护成本高

- 跨语言、跨系统的集成复杂

- 权限和安全控制需要自己实现

- 可观测性不足

业界提出了 [[理论学习_MCP_协议与开放工具生态|MCP]]（Model Context Protocol）协议，试图解决这些问题。MCP 的核心思想是：

- 定义统一的工具描述和调用协议

- 支持工具的动态发现和注册

- 提供标准的权限和安全控制机制

- 内置可观测性支持

下一篇详细讲 MCP 是什么、怎么用、和 Function Call 的关系。

## 小结

这篇讲了 Function Call——让 RAG 系统从只能查知识库升级到能查数据、能调接口、能干活。

核心要点：

- 1.
	**Function Call 的本质** ：模型不是真的调函数，而是输出调用意图（JSON 格式的 `tool_calls` ），由你的代码执行函数

- 2.
	**完整流程** ：定义工具 → 第一轮调用（模型输出 tool\_calls）→ 执行函数 → 第二轮调用（把结果返回给模型）→ 模型生成最终答案

- 3.
	**OpenAI Function Call 协议** ：工具定义（tools 数组）、请求格式（tool\_choice 参数）、响应格式（tool\_calls 数组）、第二轮请求（完整对话历史）

- 4.
	**在 RAG 系统中的应用** ：意图识别（查知识库 vs 调工具）、混合场景（知识检索 + 工具调用）、工具优先级控制

- 5.
	**局限性** ：工具定义维护成本高、跨语言集成复杂、权限和安全控制需要自己实现、可观测性不足

Function Call 是 RAG 系统能力扩展的关键，但它只是一个协议，具体的工具管理、权限控制、可观测性还需要自己实现。下一篇讲 MCP 协议——企业级工具调用的标准化方案，看看它怎么解决 Function Call 的这些痛点。

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join\_group.html?group\_id=51121244585524