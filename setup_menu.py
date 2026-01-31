"""
Telegram Bot 快捷選單設定
設定 Bot 的指令選單（移除持倉和進場機會相關功能）
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"

# 定義快捷選單指令（已移除持倉和進場機會相關功能）
commands = [
    {
        "command": "start",
        "description": "🚀 開始使用"
    },
    {
        "command": "help",
        "description": "📖 查看使用說明"
    },
    {
        "command": "price",
        "description": "💰 查詢即時價格"
    },
    {
        "command": "top",
        "description": "📊 市值排名 Top 10"
    },
    {
        "command": "news",
        "description": "📰 最新加密貨幣新聞"
    },
    {
        "command": "trend",
        "description": "🤖 AI 市場趨勢預測"
    },
    {
        "command": "analyze",
        "description": "🔍 技術分析與交易建議"
    },
    {
        "command": "alert",
        "description": "🔔 設定價格提醒"
    },
    {
        "command": "myalerts",
        "description": "📋 查看我的提醒"
    },
    {
        "command": "del_alert",
        "description": "❌ 刪除價格提醒"
    }
]

def setup_menu():
    """設定 Bot 快捷選單"""
    try:
        response = requests.post(
            API_URL,
            json={"commands": commands}
        )
        
        result = response.json()
        
        if result.get('ok'):
            print("✅ 快捷選單設定成功！")
            print("\n已設定的指令：")
            print("=" * 60)
            for cmd in commands:
                print(f"/{cmd['command']:<15} - {cmd['description']}")
            print("=" * 60)
            print("\n✨ 已移除的功能：")
            print("  ❌ 持倉狀況管理（/positions, /add_position, /delete_position）")
            print("  ❌ 進場機會提醒（/risk_profile, /my_profile）")
            print("\n✨ 新增的功能：")
            print("  ✅ AI 市場趨勢預測（/trend）")
        else:
            print(f"❌ 設定失敗: {result}")
            
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ 錯誤: 找不到 TELEGRAM_BOT_TOKEN")
        print("請確保 .env 檔案包含 TELEGRAM_BOT_TOKEN")
    else:
        setup_menu()
