理论篇讲了「怎么设计」，这一篇我们打开 Java 源码，看看每一行到底「怎么写」。

## 模块概览

ch02 对应的代码分布在两个包里： `llm` 负责与大模型通信， `conversation` 负责管理对话历史。一共 12 个文件，每个文件职责单一，读起来不会迷路。

| 文件 | 职责 |
| --- | --- |
| `llm/LlmClient.java` | 核心接口 + 静态工厂，对外只暴露 `stream()` 和 `setMaxOutputTokens()` |
| `llm/StreamEvent.java` | sealed interface + 8 个 record，流式事件的「词汇表」 |
| `llm/AnthropicClient.java` | 基于 anthropic-java 官方 SDK 的流式客户端 |
| `llm/OpenAiClient.java` | 基于 openai-java 官方 SDK 的流式客户端（Responses API） |
| `llm/OpenAiCompatClient.java` | 走 `/chat/completions` 协议的兼容客户端，适配 vLLM、Ollama 等 OpenAI 兼容服务 |
| `llm/LlmException.java` | 4 个异常子类，把 SDK 异常翻译成业务语义 |
| `llm/ModelResolver.java` | 模型别名解析， `haiku` 、 `sonnet` 、 `opus` 短名映射 |
| `conversation/ConversationManager.java` | 对话管理器，维护消息历史 |
| `conversation/Message.java` | 可变消息类，承载文本、思考块、工具调用 |
| `conversation/ThinkingBlock.java` | 思考块 record |
| `conversation/ToolUseBlock.java` | 工具调用块 record |
| `conversation/ToolResultBlock.java` | 工具结果块 record |

如果你只想抓住主线，重点看 `LlmClient` 、 `StreamEvent` 、 `AnthropicClient` 这三个就够了。OpenAI 那边结构几乎一样，只是 SDK 的 builder 长得不同。 `OpenAiCompatClient` 是给 vLLM、Ollama 这类 OpenAI 兼容服务准备的，走更通用的 `/chat/completions` 协议，本篇不展开。

## 核心类型

### LlmClient：一个接口，两行契约

```plain
public interface LlmClient {
    BlockingQueue<StreamEvent> stream(
        ConversationManager conv,
        List<Map<String, Object>> tools);
    default void setMaxOutputTokens(int tokens) {}
    static LlmClient create(ProviderConfig cfg, String systemPrompt) {
        return switch (cfg.getProtocol()) {
            case "anthropic" -> new AnthropicClient(cfg, systemPrompt);
            case "openai" -> new OpenAiClient(cfg, systemPrompt);
            case "openai-compat" -> new OpenAiCompatClient(cfg, systemPrompt);
            default -> throw new IllegalArgumentException(
                "Unknown protocol: " + cfg.getProtocol());
        };
    }
}
```

整个接口只有一个核心方法 `stream()` ，入参是对话管理器和工具列表，返回一个 `BlockingQueue<StreamEvent>` 。调用方不需要关心底层是 Anthropic 还是 OpenAI，拿到队列之后不停 `take()` 就行，直到收到 `StreamEnd` 或 `Error` 。

`setMaxOutputTokens()` 是个 default 方法，给了个空实现。这样上层想动态调整输出长度时可以调，不想管的话也不用实现。这种「可选配置」用 default 方法比加 setter 接口要轻量得多。

最有趣的是那个 `create()` 静态工厂方法。它直接写在接口里，用 switch 表达式根据协议字段分发到具体实现。调用方只需要 `LlmClient.create(cfg, prompt)` 一行，完全不碰具体类名。接口里写静态方法从 Java 8 起就支持，这里用它把工厂和契约放在同一个地方，调用方只需要认识一个类型。

### StreamEvent：sealed interface 定义事件词汇表

```plain
public sealed interface StreamEvent {
    record TextDelta(String text) implements StreamEvent {}
    record ThinkingDelta(String text) implements StreamEvent {}
    record ThinkingComplete(String thinking, String signature)
        implements StreamEvent {}
    record ToolCallStart(String toolId, String toolName)
        implements StreamEvent {}
    record ToolCallDelta(String text) implements StreamEvent {}
    record ToolCallComplete(String toolId, String toolName,
        Map<String, Object> arguments) implements StreamEvent {}
    record StreamEnd(String stopReason,
        int inputTokens, int outputTokens) implements StreamEvent {}
    record Error(String message) implements StreamEvent {}
}
```

8 个 record，全部密封在一个接口里。 `sealed` 的好处是编译器帮你检查：如果你在 switch 里漏掉了某个事件类型，编译会警告。而 record 本身就是不可变的值对象，不用写 getter、 `equals()` 、 `hashCode()` ，天然适合做事件载体。

从命名上可以看出事件的生命周期。文本流有 `TextDelta` ；思考流有 `ThinkingDelta` 和 `ThinkingComplete` （后者带签名，用于多轮传回）；工具调用拆成 `Start` → `Delta` → `Complete` 三段；最后以 `StreamEnd` 或 `Error` 收尾。这套词汇表是 provider 无关的，不管后端是 Claude 还是 GPT，上层看到的都是同一组事件类型。

### ConversationManager：对话历史的容器

```plain
public class ConversationManager {
    private final List<Message> history = new ArrayList<>();
    private boolean ltmInjected = false;

    public void addUserMessage(String content) {
        history.add(new Message("user", content));
    }
    public void addAssistantMessage(String content) {
        history.add(new Message("assistant", content));
    }
    public void addAssistantFull(String text,
        List<ThinkingBlock> thinking,
        List<ToolUseBlock> toolUses) { ... }
    public void addToolResultsMessage(
        List<ToolResultBlock> results) { ... }
    public List<Message> getMessages() {
        return List.copyOf(history);
    }
}
```

`ConversationManager` 只管存储和读取，不管序列化。消息格式的转换下放到每个 Client 内部的 `buildMessages()` / `buildInput()` 方法，因为 Anthropic 需要 `MessageParam` ，OpenAI 需要 `ResponseInputItem` ，两边的类型体系完全不同，硬塞在一个通用序列化里只会越来越难维护。这是个很典型的「职责回归」：数据容器做好容器的事，格式转换让知道目标格式的人去做。

## 主流程走读

我们以 Anthropic 为例，从上层调 `stream()` 开始，一路走到收到最后一个事件。

### 第一步：虚拟线程 + 队列的生产者-消费者模型

```plain
public BlockingQueue<StreamEvent> stream(
        ConversationManager conv,
        List<Map<String, Object>> tools) {
    var queue = new LinkedBlockingQueue<StreamEvent>(64);
    Thread.startVirtualThread(() -> {
        try {
            doStream(conv, tools, queue);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            try {
                queue.put(new StreamEvent.Error(
                    classifyError(e).getMessage()));
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
            }
        }
    });
    return queue;
}
```

这段代码做的事情很简洁：创建一个容量 64 的阻塞队列，启动一个虚拟线程去执行真正的流式请求，然后立刻把队列返回给调用方。调用方可以马上开始 `take()` ，虚拟线程在后台不断往队列里 `put()` 事件。

为什么用虚拟线程而不是 `CompletableFuture` 或 Reactor？因为 [[01基础_20SSE协议与流式响应|SSE]] 流式读取本质上是一个阻塞循环：不断读下一个事件，直到流结束。用虚拟线程写阻塞代码，读起来像同步逻辑一样直白，但不会占用平台线程。队列容量设成 64 是一个背压机制：如果消费方处理不过来，生产方在 `put()` 时会自动阻塞，不会把内存撑爆。

外层的 catch 也值得注意：任何异常都不会悄悄丢失，而是被 `classifyError()` 翻译成业务异常后，包装成 `StreamEvent.Error` 塞进队列。这样消费方不需要额外的错误回调，只要在正常的事件循环里处理 `Error` 事件就行。一条通道，既走数据又走错误。

### 第二步：用 SDK builder 构建请求

```plain
var paramsBuilder = MessageCreateParams.builder()
        .model(model)
        .maxTokens(maxOutputTokens)
        .system(systemPrompt)
        .messages(buildMessages(conv.getMessages()));
```

以前的版本是手动拼 Map，key 写错了只有运行时才炸。现在用 SDK 的 builder，每个字段都有类型检查，IDE 还能自动补全。 `model` 是经过 `ModelResolver.resolve()` 之后的全名， `messages` 是通过 `buildMessages()` 从内部 `Message` 转出来的 `List<MessageParam>` 。

thinking 的配置根据模型能力分两种路径：

```plain
if (thinking) {
    if (ModelResolver.supportsAdaptiveThinking(model)) {
        paramsBuilder.thinking(
            ThinkingConfigAdaptive.builder().build());
    } else {
        paramsBuilder.thinking(ThinkingConfigEnabled.builder()
                .budgetTokens(maxOutputTokens - 1)
                .build());
    }
}
```

Claude Opus 4.6 和 Sonnet 4.6 支持自适应 thinking，不需要手动指定 token 预算，SDK 提供了 `ThinkingConfigAdaptive` 。老一点的模型则要用 `ThinkingConfigEnabled` 并明确给出 `budgetTokens` 。这里设成 `maxOutputTokens - 1` 是因为 API 要求 thinking 预算必须严格小于 max\_tokens。

### 第三步：SDK 流式迭代

请求构建好之后，用 SDK 的 `createStreaming()` 发出去，拿到一个 `StreamResponse` ：

```plain
try (StreamResponse<RawMessageStreamEvent> streamResponse =
         sdkClient.messages()
             .createStreaming(paramsBuilder.build())) {
    var iterator = streamResponse.stream().iterator();
    while (iterator.hasNext()) {
        var event = iterator.next();
        // 处理每一个 SSE 事件
    }
}
```

`StreamResponse` 实现了 `AutoCloseable` ，放在 try-with-resources 里，流结束或出错时自动关闭底层连接。内部的 `stream()` 返回一个 Java Stream，我们取它的 iterator 来逐个处理事件。

事件处理的核心逻辑是一个 if-else 链，根据事件类型分发：

```plain
if (event.isContentBlockStart()) {
    var block = event.asContentBlockStart().contentBlock();
    if (block.isThinking()) {
        inThinking = true;
        thinkingAccum.setLength(0);
    } else if (block.isToolUse()) {
        var tu = block.asToolUse();
        currentToolName = tu.name();
        currentToolId = tu.id();
        queue.put(new StreamEvent.ToolCallStart(
            currentToolId, currentToolName));
    }
}
```

`contentBlockStart` 标志着一个新内容块的开始。如果是 thinking 块，重置累加器准备收集思考文本；如果是 tool\_use 块，记下工具名和 ID，同时往队列里发一个 `ToolCallStart` 事件。

```plain
else if (event.isContentBlockDelta()) {
    var delta = event.asContentBlockDelta().delta();
    if (delta.isThinking()) {
        queue.put(new StreamEvent.ThinkingDelta(
            delta.asThinking().thinking()));
    } else if (delta.isText()) {
        queue.put(new StreamEvent.TextDelta(
            delta.asText().text()));
    } else if (delta.isInputJson()) {
        jsonAccum.append(delta.asInputJson().partialJson());
        queue.put(new StreamEvent.ToolCallDelta(
            delta.asInputJson().partialJson()));
    }
}
```

delta 阶段是流式数据的主体。注意工具调用的参数是以 JSON 片段的形式一点一点传过来的，需要用 `jsonAccum` 累加起来，等到 `contentBlockStop` 的时候再完整解析。这也是为什么工具调用要拆成 Start、Delta、Complete 三个事件的原因：开始时知道调哪个工具，中间是参数的碎片流，结束时才能拿到完整参数。

## 两层消息模型与格式转换

这一章最关键的设计决策之一是「两层消息模型」。内部用统一的 `Message` 对象存储对话历史，发请求时再转成各家 SDK 要求的类型。

### 为什么不直接存 SDK 类型？

如果把 Anthropic 的 `MessageParam` 直接存进 `ConversationManager` ，那切换到 OpenAI 的时候整个历史就没法用了。而如果存原始的 Map，虽然灵活，但没有类型安全，字段名拼错了编译器不会提醒。

所以折中方案是： `conversation` 包里定义自己的 `Message` 、 `ThinkingBlock` 、 `ToolUseBlock` 、 `ToolResultBlock` ，它们是 provider 无关的。然后每个 Client 内部写一个转换方法，把这些类型映射到 SDK 类型。

### AnthropicClient.buildMessages()

这个方法的核心任务是把 `Message` 列表转成 `MessageParam` 列表。直觉上觉得应该很简单，但实际上有不少细节。

```plain
if ("assistant".equals(msg.getRole())
        && (hasThinking || hasToolUses)) {
    var content = new ArrayList<ContentBlockParam>();
    if (hasThinking) {
        for (var tb : msg.getThinkingBlocks()) {
            content.add(ContentBlockParam.ofThinking(
                ThinkingBlockParam.builder()
                    .thinking(tb.thinking())
                    .signature(tb.signature())
                    .build()));
        }
    }
    if (msg.getContent() != null
            && !msg.getContent().isEmpty()) {
        content.add(ContentBlockParam.ofText(
            TextBlockParam.builder()
                .text(msg.getContent()).build()));
    }
    // ... tool use blocks
    result.add(MessageParam.builder()
        .role(MessageParam.Role.ASSISTANT)
        .contentOfBlockParams(content)
        .build());
}
```

当一条 assistant 消息同时包含思考块、文本和工具调用时，需要把它们全部塞进一个 `ContentBlockParam` 列表里。SDK 的 `MessageParam` 对 content 字段有两种表达：纯文本可以直接传 String，混合内容则要用 `contentOfBlockParams()` 传一个列表。

思考块特别需要注意 `signature` 字段。Claude 的 API 要求[[01基础_16多轮对话记忆设计|多轮对话]]中，上一轮的 thinking 在回传时必须带上签名，用于验证这确实是模型自己产出的思考内容而不是用户伪造的。这就是为什么 `ThinkingComplete` 事件里有 signature，而 `ThinkingBlock` record 里也保存了它。

### 连续同角色消息合并

Anthropic 的 API 有一个硬性约束：消息列表必须严格交替 user → assistant → user → assistant。但实际对话中经常出现连续的 user 消息（比如用户发了一条文字又发了一个工具结果），这时就需要合并。

```plain
private List<MessageParam> mergeConsecutiveSameRole(
        List<MessageParam> messages) {
    var merged = new ArrayList<MessageParam>();
    merged.add(messages.getFirst());
    for (int i = 1; i < messages.size(); i++) {
        var prev = merged.getLast();
        var curr = messages.get(i);
        if (prev.role().equals(curr.role())) {
            if (prevContent.isString()
                    && currContent.isString()) {
                merged.set(merged.size() - 1,
                    MessageParam.builder()
                        .role(prev.role())
                        .content(prevContent.asString()
                            + "\n\n" + currContent.asString())
                        .build());
            } else {
                merged.add(curr);
            }
        } else {
            merged.add(curr);
        }
    }
    return merged;
}
```

逻辑很直白：遍历列表，如果当前消息和前一条角色相同且都是纯文本，就拼到一起。如果其中有一条是复杂内容（block 列表），就不合并，直接保留。这种处理方式略显保守，但胜在安全：混合内容的合并容易出错，不如让 API 自己报错来得清楚。

### OpenAI 那边怎么做？

OpenAI 的 `buildInput()` 结构上类似，但用的是 Responses API 的类型体系：

```plain
var role = "assistant".equals(msg.getRole())
    ? EasyInputMessage.Role.ASSISTANT
    : EasyInputMessage.Role.USER;
result.add(ResponseInputItem.ofEasyInputMessage(
    EasyInputMessage.builder()
        .role(role)
        .content(msg.getContent())
        .build()));
```

工具调用在 OpenAI 侧是 `ResponseFunctionToolCall` ，工具结果是 `FunctionCallOutput` 。类名不同，但映射逻辑是对称的。这也印证了两层模型的价值：内部 `Message` 不变，只有最后一公里的转换代码不同。

## 错误分类与 SDK 异常映射

LLM API 的错误五花八门，但对上层来说只关心几种：认证失败、限流、上下文太长、网络中断。 `LlmException` 定义了这四个子类， `classifyError()` 负责把 SDK 抛出的异常翻译过来。

```plain
private LlmException classifyError(Exception e) {
    if (e instanceof LlmException le) return le;
    if (e instanceof
            com.anthropic.errors.UnauthorizedException ue) {
        return new LlmException.AuthenticationException(
            "Invalid API key: " + ue.getMessage());
    }
    if (e instanceof
            com.anthropic.errors.RateLimitException) {
        return new LlmException.RateLimitException(
            "Rate limited. Please wait.", "");
    }
    if (e instanceof
            com.anthropic.errors.BadRequestException bre) {
        String msg = bre.getMessage() != null
            ? bre.getMessage().toLowerCase() : "";
        if (msg.contains("prompt is too long")
                || msg.contains("too many tokens")) {
            return new LlmException.ContextTooLongException(
                "Context too long: " + bre.getMessage());
        }
    }
    if (e instanceof
            com.anthropic.errors.AnthropicIoException) {
        return new LlmException.NetworkException(
            "Network error: " + e.getMessage(), e);
    }
    return new LlmException(
        "Unexpected error: " + e.getMessage(), e);
}
```

对比之前手动解析 HTTP 状态码的版本，现在直接 `instanceof` SDK 的异常类型，既准确又不容易遗漏。 `BadRequestException` 比较特殊：它涵盖了多种 400 错误，所以还需要检查消息内容来区分「上下文太长」和其他 bad request。

这个翻译层看着不起眼，但它让上层代码完全不需要知道底层用的是哪家 SDK。[[理论学习_ReAct_范式与_Agent_Loop|Agent Loop]] 里只需要 `catch (LlmException e)` 然后检查是不是 `RateLimitException` 、是不是 `ContextTooLongException` ，处理逻辑就明确了。

## 模型解析与能力探测

```plain
private static final Map<String, String> ALIASES = Map.of(
    "haiku", "claude-haiku-4-5-20251001",
    "sonnet", "claude-sonnet-4-6-20250514",
    "opus", "claude-opus-4-6-20250514");

public static String resolve(String model) {
    return ALIASES.getOrDefault(model, model);
}

public static boolean supportsAdaptiveThinking(String model) {
    String resolved = resolve(model);
    return resolved.contains("opus-4-6")
        || resolved.contains("sonnet-4-6");
}
```

`ModelResolver` 很小但很重要。用户在配置文件里写 `model: sonnet` ，代码里通过 `resolve()` 拿到完整的模型 ID。 `supportsAdaptiveThinking()` 则根据模型 ID 中的版本号判断是否支持自适应 thinking。这样当新模型发布时，只需要更新这个 Map 和判断逻辑，其他代码一行不用改。

你可能注意到 `supportsAdaptiveThinking()` 用的是 `contains()` 而不是精确匹配。这是个务实的选择：模型 ID 的格式可能随时间变化（比如日期后缀），用子串匹配更不容易误判。

## 小结

| 设计决策 | 具体做法 | 收益 |
| --- | --- | --- |
| 接口 + 静态工厂 | `LlmClient.create()` 根据 protocol 分发 | 调用方只认一个类型，新增 provider 只加一个 case |
| sealed interface + record | `StreamEvent` 8 个密封 record | 编译期穷举检查，不可变，零样板代码 |
| 虚拟线程 + 阻塞队列 | `stream()` 返回 `BlockingQueue` ，虚拟线程后台生产 | 同步写法、自动背压、异常也走队列 |
| 两层消息模型 | 内部 `Message` 与 SDK 类型（ `MessageParam` / `ResponseInputItem` ）分离 | provider 无关的历史存储，格式转换各管各的 |
| SDK builder 替代手拼 Map | `MessageCreateParams.builder()` / `ResponseCreateParams.builder()` | 类型安全、IDE 补全、少一类 runtime 拼写错误 |
| 同角色消息合并 | `mergeConsecutiveSameRole()` 在发送前处理 | 满足 Anthropic 严格交替约束，对上层透明 |
| SDK 异常映射 | `classifyError()` 用 instanceof 匹配 SDK 异常类 | 比解析 HTTP 状态码更准确，新异常类型加了就能 catch |
| 模型别名 + 能力探测 | `ModelResolver` 集中管理短名和能力标记 | 用户配置简洁，能力判断有单一出口 |