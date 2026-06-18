---
url: https://articles.zsxq.com/id_1obk6bcswmkz.html
title: Claude Code harness- Session 的准确写入时机 [源码]
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-14 19:26:48
tags:

banner: "https://article-images.zsxq.com/FkQv2R8tFKKHo6lsJRFeJv7jpYBn"
banner_icon: 🔖
---
基于源码，(考虑到有些人还没有源码, 可以翻到最下边去下载) Claude Code 对于 “**Session Memory 驱动的上下文压缩**”，并不是在触发压缩的那一刻，才去用 Prompt 问大模型 “请帮我总结一下”。

实际上，它分成了两步：

*   1.
    
    后台 Sub-agent 持续维护 `summary.md` 所使用的 Prompt。 (图中的: 不污染原始上下文)
    

*   2.
    
    触发压缩时，直接把 `summary.md` 包裹进一段 “场景说明 Prompt”，再塞进对话流。
    

所以，session memory 的写入机制非常有参考价值，可以应用于其他业务场景中。

![](https://article-images.zsxq.com/FkQv2R8tFKKHo6lsJRFeJv7jpYBn)

  

今天想和大家讨论的是另一个关键问题：何时写入 session memory，这个时机非常重要。

我阅读了源码，这里和大家分享一下：记忆写入的精准卡点（Triggering Conditions）。

## 写入时机的核心原则

Session Memory 的写入并不是实时的。系统更像一个聪明的课堂助教，会在最不打扰主进程的时候记笔记。

触发条件必须同时满足一套严密的 “**token 的增长**” 与 “**行为监控**”。

### 1. Token 增长要求

*   **冷启动（Initialization）**：第一次提取时，当前上下文积攒总额必须超过 `10,000` tokens。
    

*   **后续增量（Update）**：距离上次写完笔记后，又新增了超过 `5,000` tokens。
    

如果没有满足 Token 增长量，它不会占用任启动 session summary 这个行为.

### 2. 行为**监控**

在满足新增量后，还需要满足以下条件之一：

*   **工作量达标**：AI 已经执行了至少 `3` 次工具调用，说明排查或代码修改已经取得了阶段性的实质进展。
    

*   **自然的对话停顿**：AI 最新一轮回复中**没有调用任何工具**。这意味着它正在和用户用纯文本汇报、聊天，或者处于等待指令状态。这正是 “写复盘笔记” 最安全的挂机时机。
    

### 哈哈, 一个巧妙的类比

你可以将这个机制想象为一个在旁边帮你做课堂笔记的助教，它动笔的时机是：

“哦，刚才新聊的信息够多了（积累了 5000+ 上下文） ➡️ 那我看看主讲人现在状态 ➡️ 他已经试了几个操作了（3 次以上工具调用），或者他正好停下来在和老板解释进展（没用工具的自然回答） ➡️ 行，趁现在，我在后台偷偷 `fork` 出来更新一下 `summary.md`！”

这样精细的卡点设计，保证了记录进 `summary.md` 的内容都是**完整且有结论性的工作块**，而不会在 AI 疯狂排查 Bug 的中间态产生无意义或混乱的笔记。

## 附: 可以结合源码中对应的具体提示词一起看

### 1. 后台 Sub-agent 更新 Session Memory 时的 Prompt

这个 Prompt 被定义在 `src/services/SessionMemory/prompts.ts` 中。它的核心要求是让 Sub-agent “默默记笔记”，只准修改文件，严禁输出任何废话。

#### 英文原文

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
IMPORTANT: This message and these instructions are NOT part of the actual user conversation. Do NOT include any references to "note-taking", "session notes extraction", or these update instructions in the notes content.

Based on the user conversation above (EXCLUDING this note-taking instruction message as well as system prompt, claude.md entries, or any past session summaries), update the session notes file.

The file {{notesPath}} has already been read for you. Here are its current contents:
<current_notes_content>
{{currentNotes}}
</current_notes_content>

Your ONLY task is to use the Edit tool to update the notes file, then stop. You can make multiple edits (update every section as needed) - make all Edit tool calls in parallel in a single message. Do not call any other tools.

CRITICAL RULES FOR EDITING:
- The file must maintain its exact structure with all sections, headers, and italic descriptions intact
- NEVER modify, delete, or add section headers (the lines starting with '#' like # Task specification)
- NEVER modify or delete the italic _section description_ lines
- ONLY update the actual content that appears BELOW the italic _section descriptions_ within each existing section
- Do NOT add any new sections, summaries, or information outside the existing structure
- Write DETAILED, INFO-DENSE content for each section - include specifics like file paths, function names, error messages, exact commands, technical details, etc.
- For "Key results", include the complete, exact output the user requested
- Do not include information that's already in the CLAUDE.md files included in the context
- IMPORTANT: Always update "Current State" to reflect the most recent work - this is critical for continuity after compaction

Use the Edit tool with file_path: {{notesPath}}



```

**配套的默认模板（Template）** 会要求小弟从这几个维度做梳理：`Session Title`、`Current State`、`Task specification`、`Files and Functions`、`Workflow`、`Errors & Corrections`、`Codebase and System Documentation`、`Learnings`、`Key results`、`Worklog`。

#### 中文提示词

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
重要提示：此消息及这些指令并非实际用户对话的一部分。请勿在笔记内容中包含任何关于“笔记记录”、“会话笔记提取”或这些更新指令的引用。

基于上述用户对话（排除此笔记记录指令消息以及系统提示、claude.md 条目或任何过往会话摘要），请更新会话笔记文件。

文件 {{notesPath}} 已为您读取。以下是其当前内容：
<current_notes_content>
{{currentNotes}}
</current_notes_content>

您的唯一任务是使用 Edit 工具更新笔记文件，然后停止。您可以进行多次编辑（根据需要更新每个部分）——请在同一消息中并行调用所有 Edit 工具。请勿调用任何其他工具。

编辑的关键规则：
- 文件必须保持其精确结构，所有部分、标题和斜体描述均需完整保留
- 切勿修改、删除或添加章节标题（以 `#` 开头的行，例如 `# Task specification`）
- 切勿修改或删除斜体的 `_section description_` 行
- 仅更新每个现有章节中斜体 `_section descriptions_` 下方出现的实际内容
- 请勿在现有结构之外添加任何新章节、摘要或信息
- 为每个章节编写详细、信息密集的内容，包含具体细节，如文件路径、函数名称、错误消息、确切命令、技术细节等
- 对于“关键结果”，请包含用户请求的完整、确切的输出
- 请勿包含已存在于上下文中的 `CLAUDE.md` 文件内的信息
- 重要提示：始终更新“当前状态”以反映最近的工作，这对于压缩后的连续性至关重要

使用 Edit 工具，参数 `file_path: {{notesPath}}`



```

* * *

### 2. 压缩发生时，注入给主模型（大哥）的拼接 Prompt

当对话上下文（Context Window）快被填满，触发实质的压缩（Compact）时，系统**不会再去调用大模型生成总结**。

相反，在 `src/services/compact/prompt.ts` 中的 `getCompactUserSummaryMessage` 函数里，它会直接将 `summary.md` 掏出来，套上一个壳，直接当作 User Message 喂给主模型。

#### 英文原文

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

[ 这里直接插入前面维护好的 summary.md 的内容 ]

If you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: [transcript_path]

Recent messages are preserved verbatim.

Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.



```

#### 中文提示词

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
本次会话是从之前因上下文限制而中断的对话继续进行的。以下摘要涵盖了对话的早期部分。

[ 这里直接插入前面维护好的 summary.md 的内容 ]

如果您需要压缩前的具体细节（如确切的代码片段、错误信息或您生成的内容），请阅读完整记录：[transcript_path]

最近的消息被完整保留。

请从上次中断的地方继续对话，无需向用户提出任何进一步的问题。直接继续，无需提及摘要，无需重述之前的情况，无需以“我将继续”或类似语句开头。请像中断从未发生一样继续执行上一个任务。



```

~

## claude code 源码

通过网盘分享的文件：claude-code - 源码. zip  
链接: [https://pan.baidu.com/s/13ZuJispRCLg_sFshor_2zw](https://pan.baidu.com/s/13ZuJispRCLg_sFshor_2zw) 提取码: hiad  
-- 来自百度网盘超级会员 v5 的分享