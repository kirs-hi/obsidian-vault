# 飞书机器人 - 小红书数据日报

## 快速开始

### 第一步：在飞书创建群 + 机器人

1. 打开飞书，创建一个群（可以只有你自己）
2. 进入群 → 右上角「...」→ 设置 → 群机器人 → 添加机器人 → 自定义机器人
3. 设置名称（如"小红书数据助手"），点击添加
4. **复制 webhook 地址**（格式: `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）
5. 安全设置选「自定义关键词」，添加关键词：`小红书`（这样只有包含这个词的消息才能发送）

### 第二步：配置 webhook

编辑 `config.json`，把 `YOUR_WEBHOOK_URL_HERE` 替换为你的 webhook 地址：

```json
{
  "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/你的地址",
  "feishu_secret": "",
  "xhs_account": "风继续吹"
}
```

如果你在安全设置里选了「签名校验」，把密钥填到 `feishu_secret`。

### 第三步：测试

```bash
cd /Users/szx/Documents/red/feishu-bot
python3 feishu_bot.py test
```

如果飞书群里收到消息，说明连接成功。

### 第四步：录入数据 & 推送

```bash
# 录入笔记数据（点赞 收藏 评论 分享）
python3 feishu_bot.py update 2026-03-02-男生功利化健身 400 380 18 5

# 查看当前数据
python3 feishu_bot.py show

# 推送日报到飞书
python3 feishu_bot.py report
```

### 第五步：设置定时推送（可选）

```bash
bash setup_cron.sh
```

每天 21:30 自动推送日报到飞书群。

## 添加新笔记

在 `config.json` 的 `notes` 数组中添加：

```json
{
  "id": "2026-03-04-功利化健身2.0",
  "title": "功利化健身2.0：一周训练计划",
  "published": "2026-03-04",
  "url": ""
}
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `python3 feishu_bot.py test` | 发送测试消息 |
| `python3 feishu_bot.py update <ID> <赞> <藏> <评> [享]` | 录入/更新数据 |
| `python3 feishu_bot.py show` | 查看当前数据 |
| `python3 feishu_bot.py report` | 推送日报卡片 |
