---
url: https://articles.zsxq.com/id_c07fzeqcq4aa.html
title: AI Coding 自动化开发实战 - 讲解与源码
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-13 16:56:18
tags:

banner: "undefined"
banner_icon: 🔖
---
直播的回放在 “雷哥 AI” 公众号的直播回放中, 叫做:“AI 自动化 coding 实操演示”.  
文稿中的内容对应了直播中的所有执行代码.  
AIcoding 的代码我整理好了, 源码在文章最后.

### 第一阶段：需求可视化与概念验证

#### 1. 开发可展示页面（使用 Lovable）

**核心目标：** 从 0 到 1 的概念验证，明确用户旅程

**为什么重要：**

**Lovable 提示词：**

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
帮我做一个像 Apple Notes 一样简洁的笔记应用。左侧是笔记列表，右侧是编辑区。使用毛玻璃效果，配色要高级，支持 Markdown 预览。

```

## 整理需求

如果已经有了展示页面或现有系统，在此基础上开发时，我们已经知道要开发什么，这时候需要整理需求。每个项目整理需求的方式都不同，需要根据独特的需求进行梳理，然后与 AI 进行多轮对话，最后整理成一篇需求文档。

以我的笔记系统为例，我要为这个笔记系统做一个后端，提供一些 API，使用 Python 开发。

进入项目后, 我的提示词是这样的：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
先不要改代码，你仔细阅读这个项目的每一个文件，我需要基于这个项目将其所有功能持久化到数据库中。数据库连接已经建立，连接为：postgresql://postgres:postgres@localhost:5432/auto_coding。但我安装到了 docker 中，你需要将 ip 改成：host.docker.internal，如果我要这样操作，实施步骤应该是什么？

```

备注：AI 可能会使用 Express 开发，我会引导它使用 Python。这部分也是需求的确定化整理过程（引导成 Python）。

## 快速初始化 AI-coding 项目

我在一个单独的项目目录中写好了相关的 AI coding 文件。使用下面的命令，可以将这些文件复制到当前项目中。这样做的好处是：如果未来通用框架有修改，可以在 AI coding 项目中统一修改。现有项目需要使用最新版本时，直接使用这个命令复制即可，速度很快。

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
cp -r /Users/dulei/Documents/project/auto_coding/{.claude,.mcp.json,docs,scripts} ./

```

### 权限自动化知识背景

完成上面的步骤后，一个关键点是沙箱环境。使用 Claude Code 做 AI coding 时，它会持续询问权限。我们可以配置权限，但不能完全放开，这是关键。如果放开全部权限，Claude Code 出现问题时可能会删除关键文件，难以挽回。因此必须使用沙箱环境。我选择的是 Docker。在 Docker 沙箱环境中，启动时将当前目录挂载进去，其他目录和系统文件都看不到，这样可以放开容器内的所有权限，让它直接操作。

## docker sanbox

[https://docs.docker.com/ai/sandboxes/claude-code/#base-image](https://docs.docker.com/ai/sandboxes/claude-code/#base-image)

Claude launches with `--dangerously-skip-permissions` by default in sandboxes.

## anthropic docs

使用 `--dangerously-skip-permissions` 跳过所有权限检查（仅限安全环境）。

### 方法 1: 使用第三方模型

首先，Docker 需要安装最新版本。

然后，我们可以通过传递 URL 和 Key 的方式，让 Docker 运行不同的 Claude 模型。下面有 GLM 和 OpenRouter 的示例，可以根据自己的情况选择不同的中转服务。

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
docker sandbox run -e ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic" -e ANTHROPIC_AUTH_TOKEN="90486d53e2f74b41af8a3d5a8a1fadee.rKOacwJ7OXd26gIb" claude

```

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
 docker sandbox run -e ANTHROPIC_BASE_URL="https://openrouter.ai/api" -e ANTHROPIC_AUTH_TOKEN="sk-or-v1-xxxx****xxxx（已脱敏）" claude
 

```

还有这种非交互式的方式，运行一次后自动退出 Docker 容器：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
 docker sandbox run -e ANTHROPIC_BASE_URL="https://openrouter.ai/api" -e ANTHROPIC_AUTH_TOKEN="sk-or-v1-xxxx****xxxx（已脱敏）" claude -p "say hello"

```

后续我们 AI coding 会使用这种方式。

### 方法 2: cursor

使用 Cursor 同样可以作为 plan 计划和思考的模型。

## 制作 prd

前期我们已经有了项目，需求也收集完成。接下来需要把需求变成可以落地的内容，也就是将需求拆分出来。拆分后，这些需求点可能是用户视角的功能，也可能是为了完成这些功能需要实现的具体功能（function）。因此，我们需要从用户视角和功能视角两方面出发，制作出完整的 PRD。

解释说明:

User Stories（用户故事）通常是从用户的感性视角出发（比如：我想一眼看到优先级），而 **FR** 则是将其转化为**理性的、可执行的逻辑指令**。

*   **User Story:** “作为用户，我希望能够快速登录。”（很模糊）
    

*   **Functional Requirements:**
    
    *   **FR-3:** 连续输错 5 次验证码后，账号需锁定 30 分钟。
        
    

**FR 存在的意义：** 消除模糊性，让开发知道代码逻辑的边界在哪里。

### 方法:

制作方法是使用一个 skills 工具来创建 PRD，创建命令如下：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
创建一个prd:xxx

```

### 制作 task 方法

PRD 创建完成后，需要使用 Ralph 的方式让它循环逐个执行任务。要实现循环执行，需要将 PRD 转换成固定的 JSON 格式，把每一块 task 独立开来。这样就将已经拆解好的 PRD 再次拆解成 task 的 JSON 形式。

这里最关键的一点是，每一个 task 都要有衡量标准和验收标准。比如可以使用 test 或 UI 测试的方式进行验收。  
同样有一个 skills 可以使用：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
将prd转成prd.json: xxx

```

## 执行所有 task

接下来可以使用我编写的 Python 命令让任务循环执行。这里的关键点是，在循环执行过程中，如果某个命令超过了 10 分钟或 20 分钟（根据具体场景而定）还没有完成，说明存在不合理的情况，此时会将其 kill 掉。这个逻辑已经写在 Python 程序中。当任务被 kill 后，下一轮循环时会重新执行该任务，可能会有新的思路。这样的处理机制效果很好：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
python ./scripts/ralph/ralph.py

```

## 最终完成后的集成测试

所有项目完成后，让它自动启动起来。由于项目是在沙箱里运行的，最后进行集成时需要自己再测试一下。可以让它进行自动化测试，比如使用浏览器进行点击测试或运行一些测试用例。这样整个项目就可以在本地跑起来了，自动化 coding 的流程也就完成了：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
按照Users/dulei/Downloads/frosted-notes-main-1/docs/myrequi
  rements.md需求我开发的任务是/Users/dulei/Downloads/frosted-notes-main/scripts/ralph/prd.json,
你把项目启动起来进行测试一下, 使用agent-brwoser的skill进行测试

```

~

## 源码

通过网盘分享的文件：AI 自动化 coding 2.0.zip  
链接: [https://pan.baidu.com/s/1P9xjX2vPfTxJ74H0AuWLeg](https://pan.baidu.com/s/1P9xjX2vPfTxJ74H0AuWLeg) 提取码: qnud  
-- 来自百度网盘超级会员 v5 的分享