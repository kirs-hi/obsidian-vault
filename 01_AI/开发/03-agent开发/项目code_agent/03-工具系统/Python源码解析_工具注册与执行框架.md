理论篇讲了 Function Calling 的协议、工具接口设计、六个核心工具，以及流式 tool\_use 的集成。这一篇走读工具系统的代码，看「注册、描述、执行」这条主线怎么落地，以及流式 tool\_use 怎么拼进客户端。

## 模块概览

工具系统的代码集中在 `mewcode/tools/` 包下，外加一个独立的缓存模块：

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `base.py` | 97 | 核心基础设施：Tool 抽象基类、ToolResult、ToolCategory、流事件类型、SKIP_DIRS 常量 |
| `__init__.py` | 159 | ToolRegistry 注册中心、带评分的延迟搜索、 `create_default_registry` 工厂 |
| `read_file.py` | 58 | ReadFile，offset/limit 分页加缓存 |
| `write_file.py` | 48 | WriteFile，自动创建父目录 |
| `edit_file.py` | 67 | EditFile，唯一性校验加缓存失效 |
| `bash.py` | 56 | Bash，asyncio 子进程加超时 |
| `glob.py` | 45 | Glob，模式匹配 |
| `grep.py` | 62 | Grep，正则搜索 |
| `cache.py` | 37 | FileCache，文件内容缓存 |

九个文件加起来 629 行。靠 Pydantic 做参数校验、asyncio 做异步执行，代码相当紧凑。

## 核心类型

### ToolCategory

```plain
ToolCategory = Literal["read", "write", "command"]
```

用 `Literal` 把三个合法值写死，类型检查器在静态检查阶段就能拦下非法分类，运行时不需要额外校验。 `read` 只读、 `write` 写文件、 `command` 执行命令，权限系统按这个分类决定检查策略。

### ToolResult

```plain
@dataclass
class ToolResult:
    output: str
    is_error: bool = False
```

只有两个字段。用 dataclass 而不是 Pydantic 的 BaseModel 是有意的：ToolResult 是内部数据结构，不需要序列化和校验的开销。

`is_error` 不是程序异常，而是告诉模型「这次没成功」。模型收到 `is_error=True` 会重新判断再试。比如 EditFile 找不到要替换的字符串，返回 `is_error=True` ，模型就知道该先 ReadFile 确认内容再改。工具执行失败对模型来说是有价值的反馈，只有真正的系统级错误才该作为程序异常上报。

### Tool 抽象基类

```plain
class Tool(ABC):
    name: str
    description: str
    params_model: type[BaseModel]
    category: ToolCategory = "read"
    is_concurrency_safe: bool = False
    is_system_tool: bool = False
    should_defer: bool = False

    @property
    def is_read_only(self) -> bool:
        return self.category == "read"

    @abstractmethod
    async def execute(self, params: BaseModel) -> ToolResult: ...
```

工具的抽象用 ABC 抽象基类，所有工具继承它，基类带默认值，子类只覆盖要改的。

这些元字段不是摆设，每一个都有人消费： `category` 经 `is_read_only` 给权限系统判断要不要拦截， `is_concurrency_safe` 给执行引擎决定能不能并发， `should_defer` 给注册中心判断要不要默认隐藏这个工具（第七章 MCP 再展开）。元信息集中在基类上声明，不同子系统各取所需，这是后面权限、调度自动运转的基础。

最关键的设计在 `params_model` 。挂一个 Pydantic 模型上去，Schema 就能自动生成：

```plain
def get_schema(self) -> dict[str, Any]:
    schema = self.params_model.model_json_schema()
    schema.pop("title", None)
    return {
        "name": self.name,
        "description": self.description,
        "input_schema": schema,
    }
```

`model_json_schema()` 把模型字段直接转成标准 JSON Schema， `pop("title")` 去掉自动塞的标题字段。每个工具只要定义一个 Params 类，Schema 就有了，不会出现手写 Schema 和实际参数对不上的问题。以 EditFile 为例：

```plain
class Params(BaseModel):
    file_path: str = Field(description="Path to the file to edit")
    old_string: str = Field(description="The exact string to find and replace")
    new_string: str = Field(description="The replacement string")
```

`Field` 的 `description` 会进到 Schema 里，成为模型看到的参数说明。描述写在离代码最近的地方，这也是「描述最值得打磨」在工程上的落点。

### FileCache

```plain
class FileCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, path: str) -> str | None:
        with self._lock:
            return self._store.get(path)
```

FileCache 是 ReadFile、WriteFile、EditFile 共享的缓存，本体是一个字典加一把锁， `get` 、 `put` 、 `invalidate` 都用 `with self._lock` 保护，保证多个执行上下文同时读写这个字典时不会互相踩。写工具会被调度串行执行（见后文「第三步：执行」），只读操作又是快速的同步读写，真正的争用很少，这把锁更多是为以后文件 IO 改成异步或多线程时留的保险。

更重要的是 `invalidate` 的时机：每次 WriteFile 或 EditFile 改完文件，都要清掉旧缓存，否则下次 ReadFile 会从缓存读到过时内容。

## 主流程走读

工具系统的主线分三步：注册、生成 Schema、执行。

### 第一步：注册

启动入口是 `create_default_registry` ，注册六个内置工具：

```plain
def create_default_registry(
    file_cache: FileCache | None = None,
    file_history: Any = None,
) -> ToolRegistry:
    from mewcode.tools.read_file import ReadFile
    from mewcode.tools.edit_file import EditFile
    # ... 其余导入

    registry = ToolRegistry()
    registry.register(ReadFile(file_cache=file_cache))
    registry.register(WriteFile(file_cache=file_cache, file_history=file_history))
    registry.register(EditFile(file_cache=file_cache, file_history=file_history))
    registry.register(Bash())
    registry.register(Glob())
    registry.register(Grep())
    return registry
```

两个细节。第一，所有 import 写在函数体内，是延迟导入，避免工具模块反过来引用 registry 造成循环依赖。第二， `file_cache` 和 `file_history` 通过依赖注入只传给需要的工具，Bash、Glob、Grep 不碰文件缓存就不传。

注册本身很简单，往字典里存：

```plain
class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._disabled: set[str] = set()
        self._discovered: set[str] = set()

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
```

六个工具一律先注册，运行时要关掉某个就调 `disable` ，靠 `_disabled` 集合屏蔽：

```plain
def disable(self, name: str) -> None:
    if name in self._tools:
        self._disabled.add(name)
```

### 第二步：生成 Schema

每轮迭代由 `get_all_schemas` 提供工具描述：

```plain
def get_all_schemas(self, protocol: str = "anthropic") -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for name, tool in self._tools.items():
        if name in self._disabled:
            continue
        if getattr(tool, "should_defer", False) and name not in self._discovered:
            continue
        base = tool.get_schema()
        if protocol in ("openai", "openai-compat"):
            schemas.append({
                "type": "function",
                "name": base["name"],
                "description": base["description"],
                "parameters": base["input_schema"],
            })
        else:
            schemas.append(base)
    return schemas
```

这里是两层过滤加一层协议适配：先跳过被禁用的工具，再跳过尚未被发现的延迟工具，最后按 protocol 把同一份 Schema 适配成 Anthropic 的 `input_schema` 形态或 OpenAI 的 `parameters` 形态。

### 第三步：执行

执行入口是 `registry.get(name)` 拿到工具，先用 Pydantic 校验参数，再 `await execute` ：

```plain
params = tool.params_model.model_validate(tc.arguments)
# ...
except ValidationError as e:
    result = ToolResult(output=f"Parameter validation error: {e}", is_error=True)
```

校验失败不抛异常中断循环，而是包装成 `is_error=True` 的 ToolResult 还给模型，让它调整参数重试。该拒绝的早拒绝，且失败要变成反馈而不是崩溃。

模型一次可能返回多个工具调用，执行引擎按 `is_concurrency_safe` 分批。只读的 ReadFile、Glob、Grep 标了 `True` ，能并到同一批用 `asyncio.gather` 并发跑；WriteFile、EditFile、Bash 是默认的 `False` ，各自串行。所以读可以并行，写一定排队，两个写操作不会同时动手，这也是前面 FileCache 那段说争用很少的原因。并发分批的调度细节在第四章 Agent Loop。

## 内置工具

| 工具 | 分类 | 核心逻辑 | 关键设计 |
| --- | --- | --- | --- |
| ReadFile | read | 按行号范围读文件，输出带行号 | FileCache 缓存加分页 |
| WriteFile | write | 创建父目录加写入整个文件 | 写后缓存失效 |
| EditFile | write | 唯一性校验加精确替换 | old_string 必须恰好出现一次 |
| Bash | command | asyncio 子进程执行命令 | 超时杀进程加编码容错 |
| Glob | read | 遍历加模式匹配 | 跳过 SKIP_DIRS |
| Grep | read | 正则搜索文件内容 | 支持 include 过滤 |

### 深入 EditFile：唯一性校验加缓存失效

EditFile 最能体现工具的设计哲学。先做存在性校验和读取，然后是核心的唯一性校验：

```plain
count = content.count(params.old_string)
if count == 0:
    return ToolResult(output="Error: old_string not found in file", is_error=True)
if count > 1:
    return ToolResult(
        output=f"Error: old_string found {count} times, must be unique",
        is_error=True,
    )
```

`str.count()` 做全文计数：0 次报找不到，多于 1 次报不唯一。这个约束解决的是「模型给了一个太短、文件里出现多次的字符串，你不知道它想改哪个」的问题。报错信息会引导模型给出更长、更有区分度的 old\_string。校验通过后替换并失效缓存：

```plain
new_content = content.replace(params.old_string, params.new_string, 1)
path.write_text(new_content, encoding="utf-8")
if self._cache:
    self._cache.invalidate(str(path.resolve()))
```

`replace` 的第三个参数 `1` 确保只替换一次，虽然前面已校验唯一，这里再加一层保险。写完立刻 `invalidate` ，这就是上文说的失效时机。

### 深入 Bash：asyncio 子进程

Bash 是唯一用到 asyncio 底层能力的工具：

```plain
class Params(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=120, description="Timeout in seconds (max 600)")

async def execute(self, params: Params) -> ToolResult:
    timeout = min(params.timeout, MAX_TIMEOUT)  # MAX_TIMEOUT = 600
    try:
        proc = await asyncio.create_subprocess_shell(
            params.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return ToolResult(output=f"Error: command timed out after {timeout}s", is_error=True)
```

默认超时 120 秒、上限 600 秒。 `create_subprocess_shell` 启动子进程， `wait_for` 包住 `communicate()` 做超时控制。超时后先 `kill()` 再 `await proc.wait()` 等它真正退出，避免僵尸进程。

输出组装时用 `decode(errors='replace')` ：命令输出可能含非 UTF-8 字节， `replace` 策略把无法解码的字节换成替换字符，不让编码问题炸掉整个调用。最后按退出码决定是否标错：

```plain
return ToolResult(output=output, is_error=proc.returncode != 0)
```

### 深入 ReadFile：缓存加分页

```plain
resolved = str(path.resolve())
text = self._cache.get(resolved) if self._cache else None
if text is None:
    text = path.read_text(encoding="utf-8")
    if self._cache:
        self._cache.put(resolved, text)

lines = text.splitlines()
selected = lines[params.offset : params.offset + params.limit]
numbered = [f"{i + params.offset + 1}\t{line}" for i, line in enumerate(selected)]
```

用 `path.resolve()` 把路径归一成绝对路径作缓存 key，相对路径和绝对路径都能命中同一条目。缓存有就用，没有就读盘再存。分页用 slice，输出 `行号<tab>内容` 、行号从 1 开始，方便模型后续用 EditFile 精确定位。

### Glob 和 Grep

Glob 用 `base.glob(pattern)` 匹配，过滤掉非文件和 SKIP\_DIRS 里的目录，结果按路径排序后每行一个相对路径返回：

```plain
matches = sorted(
    str(p.relative_to(base))
    for p in base.glob(params.pattern)
    if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)
)
```

Grep 先编译正则，再逐文件逐行匹配，输出 `文件路径:行号:内容` 。它支持 `include` 做文件名过滤，读文件用 `errors="ignore"` 跳过无法解码的内容：

```plain
for line_num, line in enumerate(text.splitlines(), 1):
    if regex.search(line):
        rel = file_path.relative_to(base)
        results.append(f"{rel}:{line_num}:{line}")
```

两个工具共用 `base.py` 里的 `SKIP_DIRS` 常量（ `.git` 、 `.venv` 、 `node_modules` 、 `__pycache__` 、 `.tox` 、 `.mypy_cache` ），遍历时跳过这些目录，既是性能优化也避免扫描无意义的文件。

## 流式 tool\_use：把 JSON 碎片拼起来

工具参数在流式响应里是一段段 JSON 碎片到的，要拼起来再解析，这是这部分最需要小心的地方。 `AnthropicClient.stream` 里的事件序列是： `content_block_start` 开头给 id 和 name，一串 `content_block_delta` 给 JSON 碎片， `content_block_stop` 收尾。

处理逻辑就是一个字符串缓冲区加三个分支：

```plain
current_tool_name = ""
current_tool_id = ""
json_accum = ""

async for event in stream:
    if event.type == "content_block_start":
        block = event.content_block
        if block.type == "tool_use":
            current_tool_name = block.name
            current_tool_id = block.id
            json_accum = ""
            yield ToolCallStart(tool_name=current_tool_name, tool_id=current_tool_id)
    elif event.type == "content_block_delta":
        delta = event.delta
        if delta.type == "input_json_delta":
            json_accum += delta.partial_json
            yield ToolCallDelta(text=delta.partial_json)
    elif event.type == "content_block_stop":
        if current_tool_name:
            try:
                args = json.loads(json_accum) if json_accum else {}
            except json.JSONDecodeError:
                args = {}
            yield ToolCallComplete(
                tool_id=current_tool_id,
                tool_name=current_tool_name,
                arguments=args,
            )
```

收到 tool\_use 的 start 就记下 id、name、清空缓冲；每个 `input_json_delta` 把 `partial_json` 追加进缓冲；stop 时一次性 `json.loads` 。 `except json.JSONDecodeError: args = {}` 是关键的优雅降级：碎片拼不成合法 JSON 也不崩溃，退化成空参数让流程继续。

整个过程对外只发 `ToolCallStart` 、 `ToolCallDelta` 、 `ToolCallComplete` 三种流事件（定义在 base.py），上层 Agent 消费这些事件，不用关心底层协议。OpenAI 兼容协议的分片不带 content\_block 结构，而是按 `tool_calls` 的 index 累积 arguments 字符串（在 `OpenAICompatClient` 里），但拼完同样是一次 `json.loads` ，思路一致。

## 消息管道：tool\_use 与 tool\_result 的配对

工具调用让对话不再是简单的 user 和 assistant 交替。 `ConversationManager.serialize` 把内部历史转成 API 要的消息格式：

```plain
# 带 tool_use 的助手消息
for tu in m.tool_uses:
    content.append({
        "type": "tool_use",
        "id": tu.tool_use_id,
        "name": tu.tool_name,
        "input": tu.arguments,
    })
result.append({"role": "assistant", "content": content})

# 工具结果消息
for tr in m.tool_results:
    content.append({
        "type": "tool_result",
        "tool_use_id": tr.tool_use_id,
        "content": tr.content,
        "is_error": tr.is_error,
    })
result.append({"role": "user", "content": content})
```

三个要点都在这段里。第一， `tool_result` 以 user 角色发送，user 和 assistant 交替的惯例依然成立，只是 user 消息的内容变成了 tool\_result。第二，一条 assistant 消息的 content 是个列表，文本块和 tool\_use 块放在一起，不拆成两条。第三，配对靠 id：tool\_use 带 `id` ，tool\_result 带 `tool_use_id` ，模型据此知道哪个结果对应哪次调用。工具返回的 `is_error` 也透过 tool\_result 一路带到 API，模型才能区分成功和失败。

## ToolSearch 与延迟加载

ToolRegistry 里还有一套延迟加载机制。工具类声明 `should_defer = True` ，注册中心就默认不把它暴露给模型；配套的 `search_deferred` 用一套打分规则（名字命中加 10 分、描述命中加 5 分等）做检索， `find_deferred_by_names` 按名字精确拉取。

六个内置工具都没有设 `should_defer` ，这套机制在本章不会触发。它真正发挥作用是第七章引入 MCP 之后：MCP 工具数量不可控，全塞进上下文既费 token 又干扰模型选择，到那时再详细走读这套评分搜索。

## 小结

| 设计决策 | 实现方式 |
| --- | --- |
| 工具抽象 | ABC 抽象基类，类属性加一个 async 抽象方法 |
| 参数校验 | Pydantic 模型， `model_json_schema()` 自动生成 Schema， `model_validate` 校验失败转 is_error |
| 工具分类 | `Literal["read", "write", "command"]` ，静态类型检查 |
| 结果传递 | `ToolResult` dataclass， `is_error` 让模型自行处理失败 |
| 注册机制 | `ToolRegistry` 用字典存储，运行时 disable/enable 屏蔽 |
| 并发控制 | `is_concurrency_safe` 标记，由调度分批，只读并行、写串行 |
| 文件缓存 | `FileCache` 字典加锁，关键在写后 invalidate |
| 异步执行 | 所有 `execute` 都是 async，Bash 用 `asyncio.create_subprocess_shell` |
| 流式 tool_use | 缓冲区累积 `input_json_delta` ， `content_block_stop` 时 `json.loads` ，失败降级为空参数 |
| 协议适配 | `get_all_schemas(protocol)` 与 `serialize(protocol)` 抹平 Anthropic 与 OpenAI 的格式差异 |

读这一章的源码，最该带走的是：元信息（category、is\_concurrency\_safe 这些）怎么被权限和调度消费，这是后面几章自动化的基础；以及 Schema 生成和协议适配怎么把工具定义和具体 API 格式解耦。

<!-- series-nav-start -->

---
**📚 工具系统**（4/5）

⬅️ 上一篇：[[Java源码解析_工具注册与执行框架]] | ➡️ 下一篇：[[实战演练_动手实现工具系统]]

<!-- series-nav-end -->
