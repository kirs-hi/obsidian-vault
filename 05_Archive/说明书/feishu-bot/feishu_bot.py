#!/usr/bin/env python3
"""
飞书机器人 - 小红书数据日报推送
用法:
  1. 推送数据日报:  python feishu_bot.py report
  2. 发送测试消息:  python feishu_bot.py test
  3. 更新笔记数据:  python feishu_bot.py update <笔记ID> <点赞> <收藏> <评论> <分享>
  4. 查看当前数据:  python feishu_bot.py show
"""

import json
import time
import hashlib
import base64
import hmac
import sys
import os
from datetime import datetime, timedelta
from urllib import request as urllib_request

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
DATA_PATH = os.path.join(SCRIPT_DIR, "data.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data():
    if not os.path.exists(DATA_PATH):
        return {"records": [], "last_updated": ""}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 飞书签名
# ============================================================

def gen_sign(timestamp, secret):
    """生成飞书 webhook 签名"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


# ============================================================
# 飞书消息发送
# ============================================================

def send_feishu_message(webhook_url, msg_body, secret=""):
    """向飞书 webhook 发送消息"""
    if secret:
        timestamp = str(int(time.time()))
        sign = gen_sign(timestamp, secret)
        msg_body["timestamp"] = timestamp
        msg_body["sign"] = sign

    data = json.dumps(msg_body).encode("utf-8")
    req = urllib_request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                print("✅ 飞书消息发送成功")
                return True
            else:
                print(f"❌ 飞书消息发送失败: {result}")
                return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def send_text(webhook_url, text, secret=""):
    """发送纯文本消息"""
    body = {"msg_type": "text", "content": {"text": text}}
    return send_feishu_message(webhook_url, body, secret)


def send_interactive_card(webhook_url, card, secret=""):
    """发送飞书卡片消息"""
    body = {"msg_type": "interactive", "card": card}
    return send_feishu_message(webhook_url, body, secret)


# ============================================================
# 数据管理
# ============================================================

def update_note_data(note_id, likes, collects, comments, shares=0):
    """更新某篇笔记的数据"""
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    # 查找是否已有今天的记录
    existing = None
    for record in data["records"]:
        if record["note_id"] == note_id and record["date"] == today:
            existing = record
            break

    if existing:
        existing["likes"] = likes
        existing["collects"] = collects
        existing["comments"] = comments
        existing["shares"] = shares
    else:
        data["records"].append({
            "note_id": note_id,
            "date": today,
            "likes": likes,
            "collects": collects,
            "comments": comments,
            "shares": shares,
        })

    save_data(data)
    print(f"✅ 数据已更新: {note_id} ({today})")
    print(f"   点赞={likes} 收藏={collects} 评论={comments} 分享={shares}")


def get_latest_data(note_id):
    """获取某篇笔记最新的数据"""
    data = load_data()
    records = [r for r in data["records"] if r["note_id"] == note_id]
    if not records:
        return None
    records.sort(key=lambda x: x["date"], reverse=True)
    return records[0]


def get_previous_data(note_id):
    """获取某篇笔记前一天的数据（用于计算增量）"""
    data = load_data()
    records = [r for r in data["records"] if r["note_id"] == note_id]
    if len(records) < 2:
        return None
    records.sort(key=lambda x: x["date"], reverse=True)
    return records[1]


# ============================================================
# 日报生成
# ============================================================

def build_daily_report_card():
    """构建小红书数据日报的飞书卡片"""
    config = load_config()
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[datetime.now().weekday()]

    # 构建每篇笔记的数据行
    note_sections = []
    total_likes = 0
    total_collects = 0
    total_comments = 0
    total_shares = 0

    for note in config["notes"]:
        latest = get_latest_data(note["id"])
        previous = get_previous_data(note["id"])

        if not latest:
            continue

        likes = latest["likes"]
        collects = latest["collects"]
        comments = latest["comments"]
        shares = latest.get("shares", 0)

        total_likes += likes
        total_collects += collects
        total_comments += comments
        total_shares += shares

        # 计算增量
        def delta_str(current, prev_val):
            if prev_val is None:
                return ""
            diff = current - prev_val
            if diff > 0:
                return f" (+{diff})"
            elif diff < 0:
                return f" ({diff})"
            return ""

        prev_likes = previous["likes"] if previous else None
        prev_collects = previous["collects"] if previous else None
        prev_comments = previous["comments"] if previous else None

        note_text = (
            f"**{note['title']}**\n"
            f"发布于 {note['published']}\n"
            f"👍 点赞 {likes}{delta_str(likes, prev_likes)}  "
            f"⭐ 收藏 {collects}{delta_str(collects, prev_collects)}  "
            f"💬 评论 {comments}{delta_str(comments, prev_comments)}"
        )

        note_sections.append({
            "tag": "markdown",
            "content": note_text,
        })

        # 分隔线
        note_sections.append({"tag": "hr"})

    # 汇总
    summary = (
        f"**账号总览**\n"
        f"👍 总点赞 {total_likes}  "
        f"⭐ 总收藏 {total_collects}  "
        f"💬 总评论 {total_comments}"
    )

    # 构建卡片
    card = {
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"📊 小红书数据日报 | {today} {weekday}",
            },
            "template": "blue",
        },
        "elements": [
            {
                "tag": "markdown",
                "content": f"**@{config['xhs_account']}** 的数据快报",
            },
            {"tag": "hr"},
            *note_sections,
            {
                "tag": "markdown",
                "content": summary,
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"数据更新时间: {data.get('last_updated', '未知')}",
                    }
                ],
            },
        ],
    }

    return card


# ============================================================
# 命令行入口
# ============================================================

def cmd_test():
    """发送测试消息"""
    config = load_config()
    webhook = config["feishu_webhook"]
    secret = config.get("feishu_secret", "")

    if webhook == "YOUR_WEBHOOK_URL_HERE":
        print("❌ 请先在 config.json 中填入你的飞书 webhook 地址")
        return

    send_text(webhook, "🤖 小红书数据机器人连接成功！", secret)


def cmd_report():
    """推送数据日报"""
    config = load_config()
    webhook = config["feishu_webhook"]
    secret = config.get("feishu_secret", "")

    if webhook == "YOUR_WEBHOOK_URL_HERE":
        print("❌ 请先在 config.json 中填入你的飞书 webhook 地址")
        return

    data = load_data()
    if not data["records"]:
        print("❌ 还没有数据，请先用 update 命令录入数据")
        print("   示例: python feishu_bot.py update 2026-03-02-男生功利化健身 369 369 15 0")
        return

    card = build_daily_report_card()
    send_interactive_card(webhook, card, secret)


def cmd_update(args):
    """更新笔记数据"""
    if len(args) < 4:
        print("用法: python feishu_bot.py update <笔记ID> <点赞> <收藏> <评论> [分享]")
        print("示例: python feishu_bot.py update 2026-03-02-男生功利化健身 400 380 18 5")
        return

    note_id = args[0]
    likes = int(args[1])
    collects = int(args[2])
    comments = int(args[3])
    shares = int(args[4]) if len(args) > 4 else 0

    update_note_data(note_id, likes, collects, comments, shares)


def cmd_show():
    """显示当前所有数据"""
    config = load_config()
    data = load_data()

    print(f"\n📊 小红书数据 @{config['xhs_account']}")
    print(f"最后更新: {data.get('last_updated', '未知')}\n")

    for note in config["notes"]:
        latest = get_latest_data(note["id"])
        print(f"📝 {note['title']}")
        if latest:
            print(f"   日期: {latest['date']}")
            print(f"   👍 {latest['likes']}  ⭐ {latest['collects']}  💬 {latest['comments']}")
        else:
            print("   暂无数据")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "test":
        cmd_test()
    elif command == "report":
        cmd_report()
    elif command == "update":
        cmd_update(sys.argv[2:])
    elif command == "show":
        cmd_show()
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
