**这是本页面的 离线文档**：[Mewcode Agent 源码下载.md](https://www.yuque.com/attachments/yuque/0/2026/md/69074747/1780797626461-36ab2051-05a1-47b4-9ed1-18927fe1f2d7.md) 下载到本地 可以复制其中**代码片段**。

---

**官方资料 提供的就是压缩包，无 git 仓库地址。**

[mewcode-java.zip](https://www.yuque.com/attachments/yuque/0/2026/zip/69074747/1780969076915-83241ad1-c282-4aea-8e70-0b511da01654.zip)[mewcode-typescript.zip](https://www.yuque.com/attachments/yuque/0/2026/zip/69074747/1780969130921-d98fd2d0-3bf8-40d8-b8ce-5e48ea413b95.zip)[mewcode-python.zip](https://www.yuque.com/attachments/yuque/0/2026/zip/69074747/1780797650898-16628877-27c9-4ecf-8174-9cd477aa763a.zip)[mewcode-golang.zip](https://www.yuque.com/attachments/yuque/0/2026/zip/69074747/1780797657489-d0ef4e4d-81f8-4646-ac3d-8286c0c905db.zip)

下载对应语言的源码压缩包，解压后按以下步骤配置和运行。

## 配置 LLM 和 MCP

  

编辑 `.mewcode/config.yaml`，填入你的 LLM 提供商信息：

```yaml
providers:
  - name: anthropic-official
    protocol: anthropic                    # 支持 anthropic / openai 两种协议
    base_url: https://your-api-provider.com/api/anthropic
    api_key: "your-api-key-here"
    model: claude-sonnet-4-6
    thinking: true                         # 是否开启 extended thinking

mcp_servers:
  - name: context7
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
```

**配置说明**

-   `protocol`：填 `anthropic` 或 `openai`，取决于你的提供商兼容哪种 API
-   `base_url`：你的 API 地址
-   `api_key`：你的 API Key
-   `model`：模型名称
-   `mcp_servers`：MCP Server 列表，每项需要 `name`、`command` 和 `args`

## 各语言启动方式

### Go

环境要求：Go 1.25+

```bash
# 构建
go build -o mewcode ./cmd/mewcode

# 运行
./mewcode

# 测试
go test ./...
```

### Java

环境要求：Java 21+（项目自带 Gradle Wrapper，无需单独安装）

Windows推荐在powershell使用

```bash
# 构建，目前是已经构建好了，可以直接运行
gradlew shadowJar

# 运行
java -jar build/libs/mewcode.jar
```

### Python

环境要求：Python 3.11+、[uv](https://docs.astral.sh/uv/)

```bash
# 安装依赖
uv sync

# 运行
uv run mewcode

# 测试
uv run pytest
```