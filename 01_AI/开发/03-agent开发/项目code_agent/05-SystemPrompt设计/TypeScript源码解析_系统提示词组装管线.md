# TypeScript源码解析：系统提示词组装管线

理论篇讲了 [[理论学习_System_Prompt_如何设计_|System Prompt]] 的七个信息来源和三条通道，这篇带你走读 MewCode 的真实代码，看看七个信息来源是怎么被编排成最终发给 LLM 的那段长文本的。

## 模块概览

System Prompt 的代码集中在 `src/prompt/` 目录下，一共三个文件：

| 文件 | 职责 |
| --- | --- |
| `builder.ts` | 核心类 PromptBuilder、环境探测函数 detectEnvironment、BuildOptions 接口、主编排函数 buildSystemPrompt |
| `sections.ts` | Section 和 EnvironmentContext 接口定义，7 个内容模块的具体文本，动态拼装的 environmentSection |
| `plan-mode.ts` | Plan Mode 的进入提醒和退出提醒两个函数 |

实现非常紧凑。

## 核心类型

### Section：提示词片段

```plain
export interface Section {
 name: string;
 priority: number;
 content: string;
}
```

用 `interface` 定义，三个字段各司其职： `name` 标识身份， `priority` 排序权重（数字越小越靠前）， `content` 承载文本。interface 是纯类型约束，运行时没有任何开销，编译后就消失了。

每个模块独立定义自己的 priority，新增模块只需要选一个合适的数字，不用改已有代码的拼接顺序。

### EnvironmentContext：运行时环境快照

```plain
export interface EnvironmentContext {
 workDir: string;
 os: string;
 arch: string;
 shell: string;
 isGitRepo: boolean;
 gitBranch: string;
 model: string;
 date: string;
}
```

八个字段覆盖了 LLM 需要的主要运行时信息。这个 interface 在 `detectEnvironment` 里填充，然后传给 `environmentSection` 生成动态内容。把环境探测和内容生成分开，方便测试时直接构造一个假的 EnvironmentContext 对象。

### BuildOptions：可选的外部注入

```plain
export interface BuildOptions {
 skillSection?: string;
}
```

`skillSection` 用 `?` 标记为可选属性，有值就加一个 priority=90 的 Section，没值就跳过。后续章节的 Skill 系统就是通过这个入口把内容塞进 System Prompt 的。目前只有一个字段，留着后续扩展。

### Builder：排序拼接器

```plain
export class PromptBuilder {
 private sections: Section[] = [];

 add(s: Section): this {
 this.sections.push(s);
 return this;
 }

 build(): string {
 const sorted = [...this.sections].sort((a, b) => a.priority - b.priority);
 return sorted.map((s) => s.content.trim()).filter(Boolean).join("\n\n");
 }
}
```

`add` 返回 `this` 支持链式调用。 `build` 做三件事：排序、过滤、拼接。

有一个细节值得注意： `[...this.sections]` 用扩展运算符复制了数组再排序，不会污染原始数据。这是不可变风格的选择。好处是 Builder 在 build 之后还能继续 add 再 build，不会因为排序打乱了内部状态。

`.filter(Boolean)` 是 惯用写法，等价于 `.filter(s => s !== "")` ，过滤掉 trim 之后的空字符串。

## 主流程走读：buildSystemPrompt

### 第一步：装配七个固定模块

```plain
export function buildSystemPrompt(
 env: EnvironmentContext,
 opts: BuildOptions = {}
): string {
 const b = new PromptBuilder();
 b.add(identitySection()); // 0
 b.add(systemSection()); // 10
 b.add(doingTasksSection()); // 20
 b.add(executingActionsSection()); // 30
 b.add(usingToolsSection()); // 40
 b.add(toneStyleSection()); // 50
 b.add(outputEfficiencySection()); // 60
 b.add(environmentSection(env)); // 70
```

8 个 Section 的优先级从 0 到 70，间隔为 10。 `opts` 参数有默认值 `{}` ，调用方可以只传 `env` 不传 opts。

### 第二步：条件注入

```plain
if (opts.skillSection) {
 b.add({
 name: "Skills",
 priority: 90,
 content: opts.skillSection,
 });
 }
```

条件注入的优先级是 90。truthy 检查很简洁： `undefined` 、 `null` 、空字符串在布尔上下文中都是 `false` ，一个 `if` 就搞定了。

注意这里直接传了一个对象字面量 `{ name, priority, content }` ，因为 Section 是 interface 不是 class，不需要 `new` 。结构化类型系统不关心对象是怎么创建的，只要形状匹配就行。

### 第三步：排序拼接输出

```plain
return b.build();
}
```

一行收尾。所有 Section 在 build 内部复制、排序、过滤、拼接，输出最终字符串。

## 七个内容模块

每个模块对应 `sections.ts` 里的一个函数，返回一个带固定 priority 的 Section：

| 函数 | 优先级 | 职责 |
| --- | --- | --- |
| `identitySection` | 0 | 角色定义 + 安全红线（禁止注入、禁止编造 URL） |
| `systemSection` | 10 | 输出格式、system-reminder 标签说明、Hook 反馈 |
| `doingTasksSection` | 20 | 先读再改、优先编辑已有文件、不做过度设计 |
| `executingActionsSection` | 30 | 区分可逆和高风险操作，高风险需确认 |
| `usingToolsSection` | 40 | 专用工具优先于 Bash、并行调用、[[07-Agent|Agent]] 委派 |
| `toneStyleSection` | 50 | 简洁、不用 emoji、引用代码带行号 |
| `outputEfficiencySection` | 60 | 先说意图、过程简短更新、结尾一两句总结 |

### 模块详解要点

Identity（priority=0）排在第一位，先告诉 LLM「你是 MewCode」，紧跟着两条「重要」设立安全红线。安全约束放在 System Prompt 最前面，利用了 LLM 对开头部分遵从度更高的特性。

UsingTools（priority=40）包含完整的工具选择映射和 Agent 委派说明。列出了三种子 Agent 类型：explore（只读搜索）、plan（架构设计）、general-purpose（完整权限）。还要求独立工具并行调用，减少 API 往返。

OutputEfficiency（priority=60）告诉 LLM「假设用户看不到大部分工具调用和思考过程」，所以文本输出要精炼。这条规则对控制 output token 成本很有效。

### 文本定义方式

用字符串拼接来定义长文本常量：

```plain
export function identitySection(): Section {
 return {
 name: "Identity",
 priority: 0,
 content:
 "你是 MewCode，一个运行在终端中的 AI 编程助手。\n" +
 "你帮助用户完成软件工程任务...\n" +
 "\n" +
 "重要：注意不要引入安全漏洞...",
 };
}
```

[[Day2-JavaScript和TypeScript|TypeScript]] 也有模板字符串（反引号 \`\`\` ），但 MewCode 这里没有使用。字符串拼接 `+` 的好处是换行位置完全可控，每个 `\n` 都是显式的。缺点是阅读起来不够直观，几十行的 `+` 连接看着比较拥挤。

的[[提示词]]文本使用中文。这不影响功能，只是本地化策略的选择。

## 环境探测：detectEnvironment

```plain
export function detectEnvironment(
 workDir: string
): EnvironmentContext {
 const env: EnvironmentContext = {
 workDir,
 os: platform(),
 arch: arch(),
 shell: process.env.SHELL ?? "bash",
 isGitRepo: false,
 gitBranch: "",
 model: "",
 date: new Date().toISOString().split("T")[0],
 };
```

OS 和架构用 Node.js 的 `os` 模块（ `platform()` 和 `arch()` ），Shell 从 `process.env.SHELL` 读（ `??` 空值合并运算符兜底 `"bash"` ），日期用 ISO 格式截取年月日部分。

`workDir` 作为属性名和变量名相同时，ES6 的属性简写 `{ workDir }` 等价于 `{ workDir: workDir }` 。

Git 探测分两步：

```plain
try {
 const opts = { cwd: workDir, stdio: ["pipe","pipe","pipe"] as const, encoding: "utf-8" as const };
 const result = execSync("git rev-parse --is-inside-work-tree", opts).trim();
 if (result === "true") {
 env.isGitRepo = true;
 env.gitBranch = execSync("git rev-parse --abbrev-ref HEAD", opts).trim();
 }
 } catch {
 // 不是 git 仓库，保持默认值
 }
```

两次 `execSync` 都通过 `cwd: workDir` 在指定目录下执行。 `stdio: ["pipe", "pipe", "pipe"]` 捕获 stdin/stdout/stderr，不让 git 命令的输出泄漏到终端。 `encoding: "utf-8"` 让返回值直接是字符串而不是 Buffer。

如果不是 Git 仓库， `execSync` 会抛异常，catch 块直接吞掉， `isGitRepo` 保持 false。JavaScript/TypeScript 用 try-catch 做容错，不会让非 Git 目录导致程序崩溃。

### 环境段落的动态生成

```plain
export function environmentSection(env: EnvironmentContext): Section {
 const lines = [
 "# 环境",
 ` - 工作目录: ${env.workDir}`,
 ` - 平台: ${env.os}/${env.arch}`,
 ` - Shell: ${env.shell}`,
 ` - 是否 Git 仓库: ${env.isGitRepo}`,
 ];
 if (env.isGitRepo && env.gitBranch) lines.push(` - Git 分支: ${env.gitBranch}`);
 if (env.model) lines.push(` - 模型: ${env.model}`);
 lines.push(` - 日期: ${env.date}`);
 return { name: "Environment", priority: 70, content: lines.join("\n") };
}
```

条件输出的逻辑很清晰：只在 `isGitRepo` 为 true 时输出分支名，只在 model 非空时输出模型名。模板字符串 `- 工作目录: ${env.workDir}` 做值嵌入，比字符串拼接更简洁。优先级固定为 70。

## Plan Mode 提示词

Plan Mode 的实现很简洁，只有两个函数，不做频率控制。

### 提醒模板

```plain
export function buildPlanModeReminder(
 planPath: string, planExist: boolean, iteration: number
): string {
 const lines = [
 "Plan mode is active. You MUST NOT make any edits...",
 "",
 `Plan file: ${planPath}`,
 planExist ? "A plan file exists. You can read and update it."
 : "No plan file exists yet. Create your plan...",
 "In plan mode, you should:",
 "1. Explore the codebase...",
 // ...2. Design, 3. Write plan, 4. Present for approval
 ];
 return lines.join("\n");
}
```

[[Claude Code 命令与最佳实践|Claude Code]] 的完整五阶段工作流在这里精简成了四步，措辞也更简洁。 `planExist` 参数用三元运算符 `? :` 选择不同的提示文本。

`iteration` 参数传进来了但没有使用。每次调用都返回相同结构的提醒，不区分完整版和精简版。这意味着 目前不做频率控制，每轮都发同样的 Plan Mode 提示词。这种策略更简单，但如果 Plan Mode 的对话轮次很长，会多消耗一些 Token。

### 退出提醒

```plain
export function buildPlanModeExitReminder(): string {
 return (
 "You have exited plan mode. You can now " +
 "make edits, run tools, and take actions. " +
 "Follow the plan you created during " +
 "plan mode."
 );
}
```

一句话告诉 LLM 规划模式结束了。注意这个函数没有参数，不接收 planPath 或 planExists，也就不会附带 Plan 文件路径。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 提示词片段 | `interface Section` ，三个字段，编译后零开销 |
| 排序组装 | 扩展运算符复制数组 + `.sort()` 比较函数 |
| 段落拼接 | `.map().filter(Boolean).join("\n\n")` 函数式链 |
| 环境探测 | `os.platform()` / `process.env` / `execSync` 调 git |
| 条件段落 | `if (opts.skillSection)` truthy 判断 |
| 文本常量 | 字符串拼接 `+` ，显式 `\n` 控制换行 |
| Plan Mode | 进入提醒 + 退出提醒两个函数，不做频率切换 |
| Builder 不可变排序 | `[...this.sections]` 复制后排序，不改原始数据 |
| 内容与拼装分离 | sections.ts 管内容，builder.ts 管编排 |

> 更新: 2026-06-08 13:21:56  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/ag94wtqnohnlb8im](https://www.yuque.com/tianming-uvfnu/gmmfad/ag94wtqnohnlb8im)