# TypeScript源码解析：五层权限防御链

理论篇讲了六层防御链的设计思路，这篇带你走读 MewCode 的权限系统代码，看看 `checker.ts` 怎么把六层防御链完整地搭起来。

## 模块概览

权限系统整个塞在一个文件里：

| 文件 | 职责 |
| --- | --- |
| `src/permissions/checker.ts` | 全部：类型定义、危险命令检测、安全命令白名单、路径沙箱、规则引擎、模式矩阵、PermissionChecker 主类 |

单文件的好处是不需要跨文件跳转，从上到下读一遍就能看到完整的权限系统。代码的组织顺序是：先定义类型和常量，然后实现各个组件，最后用 `PermissionChecker` 类把它们串起来。

## 核心类型

### Decision：权限判定结果

```plain
export type DecisionEffect = "allow" | "deny" | "ask";

export interface Decision {
 effect: DecisionEffect;
 reason: string;
}
```

`DecisionEffect` 是一个联合类型，[[Day2-JavaScript和TypeScript|TypeScript]] 编译器会在类型检查时确保只能赋值为这三个字符串之一。 `Decision` 接口包含两个字段： `effect` 表示判定结果， `reason` 记录原因。

interface 是纯类型约束，运行时完全消失。不需要 new，直接用对象字面量 `{ effect: "allow", reason: "..." }` 就能创建。对象字面量本身就足够简洁，不需要额外的工厂方法。

### PermissionMode：权限模式

```plain
export type PermissionMode = "default" | "acceptEdits" | "plan" | "bypassPermissions";
```

四种模式用联合类型定义，一行搞定。联合类型在编译期限制取值范围，运行时就是普通字符串。

### 模式矩阵

```plain
function modeDecide(
 mode: PermissionMode,
 category: "read" | "write" | "command"
): DecisionEffect {
 switch (mode) {
 case "bypassPermissions":
 return "allow";
 case "plan":
 return category === "read" ? "allow" : "deny";
 case "acceptEdits":
 return category === "command" ? "ask" : "allow";
 case "default":
 default:
 return category === "read" ? "allow" : "ask";
 }
}
```

用 switch 语句实现，每种模式一个 case，内部用三元表达式处理不同的工具分类。

有一个值得注意的设计选择：的 Plan 模式对写操作和命令返回 `deny` 而不是 `ask` 。Plan 模式下只有读操作被放行，写操作和命令直接拒绝，不给用户手动确认的机会。这是一个比较严格的实现。

`default` 分支 fallthrough 到和 `"default"` 模式相同的逻辑，确保未知模式也能有兜底行为。

### 内容提取映射表

```plain
const CONTENT_FIELDS: Record<string, string> = {
 Bash: "command",
 ReadFile: "file_path",
 WriteFile: "file_path",
 EditFile: "file_path",
 Glob: "pattern",
 Grep: "pattern",
};

export function extractContent(toolName: string, args: Record<string, unknown>): string {
 const field = CONTENT_FIELDS[toolName];
 if (!field) return "";
 const v = args[field];
 return typeof v === "string" ? v : "";
}
```

`Record<string, string>` 定义了字符串到字符串的映射类型。 `extractContent` 的逻辑是：按工具名查字段名，从参数中取值，类型检查后返回。

## 主流程走读：check() 方法

### PermissionChecker 的构造

```plain
export class PermissionChecker {
 mode: PermissionMode;
 planFilePath = "";
 private sandbox: PathSandbox;
 private ruleEngine: RuleEngine;

 constructor(workDir: string, mode: PermissionMode = "default") {
 this.mode = mode;
 this.sandbox = new PathSandbox(workDir);
 this.ruleEngine = new RuleEngine(workDir);
 }
}
```

构造函数接收工作目录和权限模式，内部创建 `PathSandbox` 和 `RuleEngine` 。组件在构造函数里直接创建，不从外部注入。这样做更简单，调用方只需要传工作目录就行。

危险命令检测和安全命令检测都是模块级函数，不需要实例化。

### check() 方法概览

的 `check()` 接收三个参数：工具名、工具分类、参数。不需要传入 Tool 对象，调用方自己负责提取分类信息。

```plain
check(
 toolName: string,
 category: "read" | "write" | "command",
 args: Record<string, unknown>
): Decision {
 const content = extractContent(toolName, args);
 // Layer 1 → Layer 2 → Layer 3 → Layer 4 → Layer 5 → Layer 6
 // ...
}
```

## 六层防御链

### Layer 0：Plan Mode 例外

```plain
if (this.mode === "plan" && toolName === "WriteFile") {
 const path = String(args.file_path ?? "");
 if (path.includes(".mewcode/plans/")) {
 return { effect: "allow", reason: "Plan file write allowed in plan mode" };
 }
}
```

的 Plan Mode 例外比较简洁：只检查 `WriteFile` 工具对 `.mewcode/plans/` 目录的写入。没有维护 Plan 模式工具白名单，也不检查 `EditFile` 。

匹配方式也最简单：路径包含 `.mewcode/plans/` 就放行，没有绝对路径比较和文件名降级。

### Layer 1：安全命令白名单

```plain
const SAFE_PREFIXES = [
 "ls", "pwd", "echo", "cat", "head", "tail", "wc", "date",
 "whoami", "uname", "hostname", "which", "type", "file",
 "git status", "git log", "git diff", "git branch",
 "git show", "git rev-parse", "git remote",
 "bun test", "bun run", "npm test", "npm run",
 "go test", "go build", "go vet",
 "python -c", "node -e",
];
```

的白名单约 30 条，覆盖了常用的只读命令和开发工具命令。包含 `bun test` 、 `bun run` 、 `npm test` 、 `npm run` 等 Node.js/Bun 生态的命令，也包含 `go test` 、 `go build` 、 `python -c` 等跨生态的常用命令。

```plain
function isSafeCommand(command: string): boolean {
 const trimmed = command.trim();
 if (
 trimmed.includes(">") || trimmed.includes("|") ||
 trimmed.includes(";") || trimmed.includes("&&") ||
 trimmed.includes("$(") || trimmed.includes("`")
 ) {
 return false;
 }
 return SAFE_PREFIXES.some(
 (prefix) =>
 trimmed === prefix ||
 trimmed.startsWith(prefix + " ") ||
 trimmed.startsWith(prefix + "\t")
 );
}
```

元字符检测和前缀匹配的逻辑很标准：先排除含管道/重定向/分号的命令，再做完整前缀匹配（包括 Tab 分隔的检查）。用 `Array.some()` 替代手动遍历循环，更符合 函数式风格。

### Layer 2：危险命令黑名单

```plain
const DANGEROUS_PATTERNS = [
 /rm\s+(-rf?|--recursive)\s+[\/~]/,
 /rm\s+-rf?\s+\*/,
 /mkfs\./,
 /dd\s+if=/,
 />\s*\/dev\/sd/,
 /chmod\s+-R?\s*777\s+\//,
 /:\(\)\{\s*:\|\s*:\s*&\s*\}\s*;/,
 /curl\s+.*\|\s*(ba)?sh/,
 /wget\s+.*\|\s*(ba)?sh/,
 /git\s+push\s+.*--force/,
 /git\s+reset\s+--hard/,
 /git\s+clean\s+-f/,
 /git\s+checkout\s+\./,
 /git\s+branch\s+-D/,
];

function detectDangerous(command: string): boolean {
 return DANGEROUS_PATTERNS.some((p) => p.test(command));
}
```

的黑名单有 14 条。除了标准的破坏性系统命令，还拦截了 5 条危险的 Git 操作： `git push --force` 、 `git reset --hard` 、 `git clean -f` 、 `git checkout .` 、 `git branch -D` 。这些 Git 操作虽然不会损毁系统，但会造成代码丢失，拦截它们是一个更谨慎的选择。

正则用 JavaScript 的字面量语法直接定义。正则字面量在脚本解析时就编译好了，效果等同于预编译，不需要额外调用编译函数。

`detectDangerous` 只返回布尔值，不返回具体的拦截理由。理由在 `check()` 方法里用通用的 `"Dangerous command blocked"` 字符串代替。

### Layer 3：路径沙箱

```plain
export class PathSandbox {
 private allowedRoots: string[];

 constructor(projectDir: string) {
 this.allowedRoots = [resolve(projectDir), "/tmp"];
 }

 addRoot(root: string): void {
 this.allowedRoots.push(resolve(root));
 }

 check(filePath: string): Decision | null {
 const absolute = resolve(filePath);
 for (const root of this.allowedRoots) {
 if (absolute.startsWith(root)) return null;
 }
 return {
 effect: "deny",
 reason: `Path ${filePath} is outside allowed directories`,
 };
 }
}
```

返回 `null` 表示路径在沙箱内（通过），返回 `Decision` 表示被拦截。这个 API 设计的好处是调用方可以直接把返回值 return 出去，不用再包装。

用 Node.js 的 `resolve` 函数转绝对路径，然后做字符串 `startsWith` 比较。没有解析符号链接，只检查字面路径。 `addRoot` 方法可以在构造后动态添加额外的白名单目录。

沙箱只在文件类工具的 check 路径里被调用：

```plain
if ((category === "read" || category === "write") && filePath) {
 const sandboxDecision = this.sandbox.check(filePath);
 if (sandboxDecision) return sandboxDecision;
}
```

### Layer 4：规则引擎

```plain
export class RuleEngine {
 private userPath: string;
 private projectPath: string;
 private localPath: string;

 constructor(workDir: string) {
 this.userPath = join(homedir(), ".mewcode", "permissions.yaml");
 this.projectPath = join(workDir, ".mewcode", "permissions.yaml");
 this.localPath = join(workDir, ".mewcode", ".permissions.local.yaml");
 }
}
```

注意 的本地配置文件名是 `.permissions.local.yaml` （前面多了一个点），在 Unix 系统上会被当作隐藏文件。

#### 规则语法和匹配

自己实现了 glob 匹配函数，因为 Node.js 标准库没有现成的 glob 匹配工具函数：

```plain
function globMatch(pattern: string, content: string): boolean {
 const re =
 "^" +
 pattern
 .replace(/[.+^${}()|[\]\\]/g, "\\$&")
 .replace(/\*/g, "[^/]*")
 .replace(/\?/g, "[^/]") +
 "$";
 try {
 return new RegExp(re).test(content);
 } catch {
 return false;
 }
}
```

把 glob 模式转换成[[14-正则表达式|正则表达式]]来匹配。 `*` 转成 `[^/]*` （匹配任意非路径分隔符字符）， `?` 转成 `[^/]` （匹配单个非分隔符字符）。先转义正则特殊字符，避免 pattern 里的 `.` 、 `(` 等字符被当作正则语法。

#### 三层规则文件

```plain
evaluate(toolName: string, content: string): RuleEffect | null {
 for (const path of [this.userPath, this.projectPath, this.localPath]) {
 const rules = loadRulesFile(path);
 for (let i = rules.length - 1; i >= 0; i--) {
 const r = rules[i];
 if (r.tool !== toolName && r.tool !== "*") continue;
 if (globMatch(r.pattern, content)) return r.effect;
 }
 }
 return null;
}
```

每次 evaluate 都重新读文件，没有做缓存，追加新规则后下次 check 自动生效。从后往前扫描，后定义的规则优先。有一个额外特性： `r.tool !== "*"` 这个检查说明 支持通配工具名 `*` ，可以写 `*(pattern)` 匹配所有工具的内容。

#### 规则文件加载

```plain
function loadRulesFile(path: string): Rule[] {
 let data: string;
 try {
 data = readFileSync(path, "utf-8");
 } catch {
 return [];
 }
 let parsed: unknown;
 try {
 parsed = yaml.load(data);
 } catch {
 return [];
 }
 if (!Array.isArray(parsed)) return [];
 // ... 逐条解析 ...
}
```

用 `js-yaml` 库解析 YAML。容错策略是：文件读取失败、解析失败、格式不对都返回空数组。

#### 动态追加规则

```plain
appendLocalRule(rule: Rule): void {
 mkdirSync(dirname(this.localPath), { recursive: true });
 const rules = loadRulesFile(this.localPath);
 rules.push(rule);
 const entries = rules.map((r) => ({ rule: `${r.tool}(${r.pattern})`, effect: r.effect }));
 writeFileSync(this.localPath, yaml.dump(entries), "utf-8");
}
```

`mkdirSync` 带 `recursive: true` 确保目录链存在。流程是：读取现有规则、追加新规则、序列化、写回文件。

还提供了一个 `allowAlways` 便捷方法：

```plain
allowAlways(toolName: string, args: Record<string, unknown>): void {
 const content = extractContent(toolName, args);
 const pattern = content.length > 60 ? content.slice(0, 60) + "*" : content + "*";
 this.ruleEngine.appendLocalRule({ tool: toolName, pattern, effect: "allow" });
}
```

自动从参数中提取内容，截断到 60 字符加通配符，构造规则并追加。这样 [[理论学习_ReAct_范式与_Agent_Loop|Agent Loop]] 里只需要调用 `checker.allowAlways(toolName, args)` 一行代码就行，不用自己构造 Rule 对象。

### Layer 5：模式矩阵兜底

```plain
return {
 effect: modeDecide(this.mode, category),
 reason: `Mode: ${this.mode}`,
};
```

最后一层直接调用 `modeDecide` 查表。返回值可能是 `allow` 、 `deny` 或 `ask` 。如果是 `ask` ，[[07-Agent|Agent]] Loop 会触发 HITL 确认。

注意这里直接把 `modeDecide` 的结果作为 Decision 的 effect 返回，没有对 `ask` 做单独处理。这意味着 Plan 模式下写操作返回的是 `deny` 而不是 `ask` ，不会触发 HITL 确认，直接拒绝。

## Agent Loop 里的集成

权限检查嵌在 `agent.ts` 的工具执行循环里：

```plain
const decision = this.checker.check(tu.toolName, category, tu.arguments);

if (decision.effect === "deny") {
 events.push({
 type: "tool_result",
 output: `Permission denied: ${decision.reason}. 此操作已被安全策略拦截和阻止...`,
 isError: true,
 });
 continue;
}
```

`deny` 返回一个 isError 的 tool\_result 事件但不终止循环。注意 的 deny 消息额外加了中文提示「此操作已被安全策略拦截和阻止，请告知用户该命令被拒绝，不要描述该命令会做什么」，直接在 tool\_result 里给模型下指令，避免模型在下一轮回复里描述被拒绝命令的具体内容。

```plain
if (decision.effect === "ask" && this.onPermissionRequest) {
 const response = await this.onPermissionRequest(
 tu.toolName,
 tu.arguments,
 decision
 );
 if (response === "deny") {
 // ... 返回错误结果 ...
 continue;
 }
 if (response === "allowAlways") {
 this.checker.allowAlways(tu.toolName, tu.arguments);
 }
}
```

的 HITL 通过回调函数 `onPermissionRequest` 实现。回调函数返回一个 Promise， `await` 等待用户回复。用户选「始终允许」时调用 `checker.allowAlways` 一行搞定。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 判定结果 | `DecisionEffect` 联合类型 + `Decision` 接口，对象字面量构造 |
| 权限模式 | `PermissionMode` 联合类型，四种模式 |
| 模式矩阵 | switch 语句 + 三元表达式，Plan 模式写操作返回 deny（非 ask） |
| 安全命令白名单 | `string[]` 数组（约 30 条）， `Array.some` 前缀匹配 + 元字符检测 |
| 危险命令黑名单 | 14 条正则字面量（含 5 条 Git 操作）， `Array.some` + `test` 匹配 |
| 路径沙箱 | `resolve` 转绝对路径 + 字符串 `startsWith` 匹配，不解析符号链接 |
| 规则语法和匹配 | `ToolName(pattern)` 格式，自实现 glob→正则 转换匹配，支持通配工具名 `*` |
| 规则文件加载 | 每次 evaluate 重新读文件，无缓存 |
| Plan Mode 例外 | 仅检查 WriteFile + 路径包含 `.mewcode/plans/` |
| 防御链串联 | `check()` 六层顺序执行，首个明确判定即返回 |
| HITL 同步 | 回调函数 `onPermissionRequest` 返回 Promise |
| 架构选择 | 单文件，组件全部在文件内定义 |

> 更新: 2026-06-08 14:10:44  
> 原文: [https://www.yuque.com/tianming-uvfnu/gmmfad/tbuca7ybke5ow0nz](https://www.yuque.com/tianming-uvfnu/gmmfad/tbuca7ybke5ow0nz)