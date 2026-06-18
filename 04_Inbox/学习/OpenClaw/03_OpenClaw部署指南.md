---
tags: [AI, OpenClaw, 部署, 安装, 技术笔记]
created: 2026-03-14
source: https://docs.openclaw.ai/start/getting-started
---

# OpenClaw 部署指南

## 系统要求

| 要求 | 说明 |
|------|------|
| Node.js | v24（推荐）或 v22.16+ LTS |
| 操作系统 | macOS、Windows（WSL2）、Linux |
| 内存 | 最低 512MB，推荐 1GB+ |
| 磁盘 | 最低 1GB 可用空间 |
| 网络 | 需要访问 LLM API（或本地 Ollama） |
| LLM API Key | Anthropic / OpenAI / Groq 等任一 |

---

## 方式一：一键安装（推荐新手）

最快 5 分钟上手：

```bash
# 1. 全局安装 OpenClaw CLI
npm install -g openclaw@latest

# 2. 引导式初始化（配置 API Key、安装系统服务）
openclaw onboard --install-daemon

# 3. 配对消息渠道（以 WhatsApp 为例，扫码）
openclaw channels login

# 4. 启动 Gateway
openclaw gateway --port 18789
```

安装完成后，打开浏览器访问 `http://127.0.0.1:18789/` 进入控制面板。

---

## 方式二：Docker 部署（推荐生产环境）

Docker 是运行 [[00_OpenClaw_MOC|OpenClaw]] 最安全的方式——容器化、隔离且可复现。

### 快速启动

```bash
# 下载官方 docker-setup.sh
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw/main/docker-setup.sh | bash
```

### docker-compose.yml 示例

```yaml
version: '3.8'
services:
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw-gateway
    restart: unless-stopped
    ports:
      - "18789:18789"
    volumes:
      - ~/.openclaw:/root/.openclaw
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
    networks:
      - openclaw-net

networks:
  openclaw-net:
    driver: bridge
```

### 环境变量说明

| 变量 | 说明 | 必填 |
|------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API Key | 二选一 |
| `OPENAI_API_KEY` | OpenAI API Key | 二选一 |
| `OPENCLAW_GATEWAY_TOKEN` | Gateway 访问令牌 | 推荐 |
| `OPENCLAW_EXTRA_MOUNTS` | 额外挂载目录（逗号分隔） | 可选 |

---

## 方式三：macOS 本地安装

macOS 用户可以使用 Homebrew 或 npm：

```bash
# 方式 A：npm（推荐）
npm install -g openclaw@latest

# 方式 B：直接下载 macOS App
# 访问 https://github.com/openclaw/openclaw/releases 下载 .dmg
```

macOS 版本额外支持：
- iMessage 原生集成
- 系统托盘图标
- 开机自启动（launchd 服务）

---

## 方式四：Linux / VPS 部署

适合 7×24 小时在线运行：

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g openclaw@latest

# 安装为系统服务（systemd）
openclaw onboard --install-daemon --daemon-type systemd

# 查看服务状态
systemctl status openclaw-gateway
```

### 云服务器推荐配置

| 云厂商 | 推荐规格 | 月费参考 |
|--------|---------|---------|
| 腾讯云轻量 | 2核2G | ~24元 |
| 阿里云 ECS | 2核2G | ~30元 |
| 天翼云 | 2核2G | ~20元 |
| Hetzner（海外） | CX21 | ~5欧元 |

---

## 方式五：Windows（WSL2）

```powershell
# 1. 安装 WSL2（PowerShell 管理员模式）
wsl --install

# 2. 进入 Ubuntu 环境
wsl

# 3. 安装 Node.js 和 OpenClaw
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g openclaw@latest

# 4. 启动
openclaw onboard --install-daemon
openclaw gateway --port 18789
```

---

## 配置详解

### 配置文件位置

```
~/.openclaw/
├── openclaw.json      # 主配置文件
├── memory/            # 长期记忆存储
├── sessions/          # 会话状态
└── logs/              # 运行日志
```

### 完整配置示例

```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "apiKey": "${ANTHROPIC_API_KEY}"
  },
  "gateway": {
    "port": 18789,
    "token": "your-secret-token",
    "host": "0.0.0.0"
  },
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+8613800138000"],
      "groups": {
        "*": { "requireMention": true }
      }
    },
    "telegram": {
      "enabled": true,
      "botToken": "${TELEGRAM_BOT_TOKEN}",
      "allowFrom": ["your_telegram_username"]
    },
    "discord": {
      "enabled": false,
      "botToken": "${DISCORD_BOT_TOKEN}"
    }
  },
  "agents": {
    "default": {
      "skills": ["web-search", "daily-report"],
      "memory": {
        "enabled": true,
        "maxEntries": 1000
      }
    }
  },
  "messages": {
    "groupChat": {
      "mentionPatterns": ["@openclaw", "@bot"]
    }
  }
}
```

---

## 安全加固

### 1. 设置 Gateway Token

```json
{
  "gateway": {
    "token": "your-very-secret-token-here"
  }
}
```

### 2. 配置白名单

只允许特定号码/用户访问：

```json
{
  "channels": {
    "whatsapp": {
      "allowFrom": ["+8613800138000", "+8613900139000"]
    },
    "telegram": {
      "allowFrom": ["username1", "username2"]
    }
  }
}
```

### 3. 远程访问（推荐 Tailscale）

不建议直接暴露 18789 端口到公网，推荐使用 Tailscale 建立私有网络：

```bash
# 安装 Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 启动
sudo tailscale up

# 通过 Tailscale IP 访问
# http://100.x.x.x:18789/
```

### 4. 反向代理（Nginx）

```nginx
server {
    listen 443 ssl;
    server_name openclaw.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 常见问题排查

### Gateway 无法启动

```bash
# 查看日志
openclaw logs --tail 50

# 检查端口占用
lsof -i :18789

# 重启服务
openclaw gateway restart
```

### WhatsApp 配对失败

```bash
# 重新配对
openclaw channels logout whatsapp
openclaw channels login whatsapp

# 查看渠道状态
openclaw channels status
```

### API Key 错误

```bash
# 验证 API Key
openclaw config test --provider anthropic

# 更新 API Key
openclaw config set llm.apiKey "sk-ant-..."
```

### 版本升级

```bash
# 升级到最新版
npm install -g openclaw@latest

# 查看当前版本
openclaw --version

# 查看更新日志
openclaw changelog
```

---

## 相关笔记

- [[01_OpenClaw概览与历史]] — 项目背景与创始人故事
- [[02_OpenClaw功能详解]] — Channels、Skills、Memory 深度解析
- [[04_OpenClaw生态与社区]] — ClawHub、社区、竞品对比
- [[05_OpenClaw代码结构与架构]] — 仓库目录、技术架构图
