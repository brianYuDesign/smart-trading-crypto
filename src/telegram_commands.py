"""
Telegram Bot 指令處理模組

支援指令:
- /news [數量] - 查詢最新新聞 (預設5則)
- /latest - 快速查看最新新聞 (同/news)
- /status - Bot運行狀態
- /help - 幫助訊息
"""

import os
import requests
from datetime import datetime
from news_monitor import NewsMonitor

class TelegramCommandHandler:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_key = os.getenv('CRYPTOPANIC_API_KEY')
        self.news_monitor = NewsMonitor(self.api_key)

    def send_message(self, text, parse_mode='HTML'):
        """發送訊息到 Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ 發送訊息失敗: {e}")
            return None

    def get_updates(self, offset=None):
        """獲取新的訊息更新"""
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {'timeout': 10}
        if offset:
            params['offset'] = offset

        try:
            response = requests.get(url, params=params, timeout=15)
            return response.json()
        except Exception as e:
            print(f"❌ 獲取更新失敗: {e}")
            return None

    def handle_news_command(self, count=5):
        """處理 /news 指令 - 查詢最新新聞"""
        try:
            count = min(max(int(count), 1), 20)  # 限制 1-20 則
        except:
            count = 5

        print(f"\n📰 處理 /news 指令，查詢 {count} 則新聞...")

        # 抓取新聞 (不檢查去重，直接返回最新的)
        all_news = self.news_monitor.fetch_all_news()

        if not all_news:
            return "😔 抱歉，目前沒有獲取到新聞，請稍後再試。"

        # 取最新的 N 則
        latest_news = all_news[:count]

        # 格式化訊息
        message = f"🔔 <b>最新加密貨幣新聞</b>\n\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"📰 共 {len(latest_news)} 則新聞\n"
        message += "\n" + "━" * 30 + "\n"

        for i, news in enumerate(latest_news, 1):
            message += f"\n📍 [{news.get('source', 'Unknown')}]\n"
            message += f"🕐 {news.get('published', 'N/A')}\n\n"

            title = news.get('title', 'No title')
            if len(title) > 100:
                title = title[:97] + "..."
            message += f"📌 <b>{title}</b>\n\n"

            summary = news.get('summary', '')
            if summary:
                if len(summary) > 150:
                    summary = summary[:147] + "..."
                message += f"💬 {summary}\n\n"

            message += f"🔗 {news.get('url', '#')}\n"

            if i < len(latest_news):
                message += "\n" + "━" * 30 + "\n"

        return message

    def handle_status_command(self):
        """處理 /status 指令 - Bot 狀態"""
        message = "🤖 <b>Bot 狀態報告</b>\n\n"
        message += f"✅ 運行正常\n"
        message += f"📅 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"📡 新聞來源: 5 個\n"
        message += f"   • CryptoPanic API\n"
        message += f"   • CoinDesk RSS\n"
        message += f"   • CoinTelegraph RSS\n"
        message += f"   • Decrypt RSS\n"
        message += f"   • Bitcoin Magazine RSS\n"
        message += f"\n💡 使用 /news 查詢最新新聞"

        return message

    def handle_help_command(self):
        """處理 /help 指令 - 幫助訊息"""
        message = "📖 <b>可用指令</b>\n\n"
        message += "📰 <b>/news [數量]</b>\n"
        message += "   查詢最新加密貨幣新聞\n"
        message += "   範例: /news 或 /news 10\n\n"
        message += "⚡ <b>/latest</b>\n"
        message += "   快速查看最新新聞 (同 /news)\n\n"
        message += "📊 <b>/status</b>\n"
        message += "   查看 Bot 運行狀態\n\n"
        message += "❓ <b>/help</b>\n"
        message += "   顯示此幫助訊息\n\n"
        message += "💡 <b>提示</b>\n"
        message += "Bot 每小時會自動推送新新聞，\n"
        message += "你也可以隨時用指令主動查詢！"

        return message

    def process_command(self, message):
        """處理用戶指令"""
        text = message.get('text', '').strip()

        if not text.startswith('/'):
            return None

        parts = text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        print(f"🎯 收到指令: {command} {args}")

        # 路由到對應的處理函數
        if command == '/news':
            count = args[0] if args else 5
            return self.handle_news_command(count)

        elif command == '/latest':
            return self.handle_news_command(5)

        elif command == '/status':
            return self.handle_status_command()

        elif command == '/help' or command == '/start':
            return self.handle_help_command()

        else:
            return f"❓ 未知指令: {command}\n使用 /help 查看可用指令"

    def process_updates(self):
        """處理所有待處理的更新"""
        print("\n" + "=" * 70)
        print("🔍 檢查 Telegram 更新...")
        print("=" * 70)

        result = self.get_updates()

        if not result or not result.get('ok'):
            print("❌ 獲取更新失敗")
            return

        updates = result.get('result', [])

        if not updates:
            print("✅ 沒有新訊息")
            return

        print(f"📬 收到 {len(updates)} 則訊息\n")

        # 處理每個更新
        for update in updates:
            update_id = update.get('update_id')
            message = update.get('message', {})

            if not message:
                continue

            from_user = message.get('from', {})
            username = from_user.get('username', 'Unknown')
            text = message.get('text', '')

            print(f"📨 訊息 #{update_id} from @{username}: {text}")

            # 處理指令
            response = self.process_command(message)

            if response:
                print(f"📤 回覆: {response[:50]}...")
                self.send_message(response)
                print("✅ 回覆已發送\n")

            # 標記為已處理 (下次 getUpdates 會跳過這個)
            self.get_updates(offset=update_id + 1)

        print("=" * 70)
        print("✅ 所有訊息處理完成")
        print("=" * 70)


def main():
    """主程式 - 檢查並處理 Telegram 指令"""
    handler = TelegramCommandHandler()
    handler.process_updates()


if __name__ == '__main__':
    main()
