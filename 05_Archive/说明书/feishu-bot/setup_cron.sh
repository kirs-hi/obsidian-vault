#!/bin/bash
# 设置每天晚上 21:30 自动推送小红书数据日报到飞书
# 用法: bash setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)
CRON_CMD="30 21 * * * cd ${SCRIPT_DIR} && ${PYTHON} feishu_bot.py report >> ${SCRIPT_DIR}/cron.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "feishu_bot.py report"; then
    echo "⚠️  定时任务已存在，跳过添加"
    echo "当前 cron 任务:"
    crontab -l | grep "feishu_bot"
else
    # 添加到 crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ 定时任务已添加: 每天 21:30 推送日报"
    echo "   日志文件: ${SCRIPT_DIR}/cron.log"
fi

echo ""
echo "管理命令:"
echo "  查看定时任务: crontab -l"
echo "  删除定时任务: crontab -e (手动删除对应行)"
