"""
Telegram Bot 指令處理模組 V2 - 完整版

支援指令:
新聞類:
- /news [數量] - 查詢最新新聞 (預設5則)
- /latest - 快速查看最新新聞

市場數據類:
- /price <幣種> - 查詢幣種價格 (如 /price BTC)
- /prices - 主流幣種價格總覽
- /market - 加密貨幣市場總覽
- /top [數量] - 市值排行榜 (預設10)

系統類:
- /status - Bot運行狀態
- /help - 幫助訊息
"""

import os
import requests
from datetime import datetime
from news_monitor import NewsMonitor
from market_data import MarketDataAPI, MarketDataFormatter

class TelegramCommandHandler:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_key = os.getenv('CRYPTOPANIC_API_KEY')
        self.news_monitor = NewsMonitor(self.api_key)
        self.market_api = MarketDataAPI()
        self.formatter = MarketDataFormatter()
        
    def send_message(self, text, parse_mode='HTML'):
        """發送訊息到 Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True  # 避免預覽連結
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
    
    # ==================== 新聞相關指令 ====================
    
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
    
    # ==================== 市場數據指令 ====================
    
    def handle_price_command(self, symbol):
        """處理 /price 指令 - 查詢單一幣種價格"""
        if not symbol:
            return "❌ 請指定幣種代碼\n範例: /price BTC"
        
        print(f"\n💰 查詢 {symbol} 價格...")
        
        data = self.market_api.get_price(symbol)
        if not data:
            return f"❌ 查詢 {symbol} 失敗，請檢查幣種代碼是否正確"
        
        return self.formatter.format_coin_price(data)
    
    def handle_prices_command(self):
        """處理 /prices 指令 - 主流幣種價格"""
        print(f"\n💰 查詢主流幣種價格...")
        
        # 預設查詢的主流幣種
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT']
        
        data = self.market_api.get_multiple_prices(symbols)
        if not data:
            return "❌ 查詢失敗，請稍後再試"
        
        return self.formatter.format_multiple_prices(data)
    
    def handle_market_command(self):
        """處理 /market 指令 - 市場總覽"""
        print(f"\n🌐 查詢市場總覽...")
        
        market_data = self.market_api.get_market_overview()
        fear_greed = self.market_api.get_fear_greed_index()
        
        if not market_data:
            return "❌ 查詢失敗，請稍後再試"
        
        return self.formatter.format_market_overview(market_data, fear_greed)
    
    def handle_top_command(self, limit=10):
        """處理 /top 指令 - 市值排行榜"""
        try:
            limit = min(max(int(limit), 5), 20)  # 限制 5-20
        except:
            limit = 10
        
        print(f"\n🏆 查詢 Top {limit} 幣種...")
        
        coins = self.market_api.get_top_coins(limit)
        if not coins:
            return "❌ 查詢失敗，請稍後再試"
        
        return self.formatter.format_top_coins(coins)
    
    # ==================== 系統指令 ====================
    
    def handle_status_command(self):
        """處理 /status 指令 - Bot 狀態"""
        message = "🤖 <b>Bot 狀態報告</b>\n\n"
        message += f"✅ 運行正常\n"
        message += f"📅 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        message += f"📊 <b>功能模組</b>\n"
        message += f"   ✅ 新聞監控 (5 個來源)\n"
        message += f"   ✅ 市場數據 (CoinGecko API)\n"
        message += f"   ✅ 恐慌指數 (Alternative.me)\n\n"
        
        message += f"💡 <b>快速指令</b>\n"
        message += f"   /news - 查看最新新聞\n"
        message += f"   /price BTC - 查詢 BTC 價格\n"
        message += f"   /market - 市場總覽\n"
        message += f"   /help - 完整指令清單"
        
        return message
    
    def handle_help_command(self):
        """處理 /help 指令 - 幫助訊息"""
        message = "📖 <b>Crypto News Bot - 指令清單</b>\n\n"
        
        message += "📰 <b>新聞查詢</b>\n"
        message += "   /news [數量] - 最新新聞 (預設5則)\n"
        message += "   /latest - 快速查看最新新聞\n\n"
        
        message += "💰 <b>市場數據</b>\n"
        message += "   /price <幣種> - 查詢幣種價格\n"
        message += "      例: /price BTC\n"
        message += "   /prices - 主流幣種價格\n"
        message += "   /market - 市場總覽 + 恐慌指數\n"
        message += "   /top [數量] - 市值排行榜\n\n"
        
        message += "⚙️ <b>系統功能</b>\n"
        message += "   /status - Bot 運行狀態\n"
        message += "   /help - 顯示此訊息\n\n"
        
        message += "💡 <b>使用提示</b>\n"
        message += "• Bot 每小時自動推送新聞\n"
        message += "• 支援的幣種: BTC, ETH, BNB, SOL, XRP...\n"
        message += "• 所有價格數據即時更新"
        
        return message
    
    # ==================== 指令路由 ====================
    
    def process_command(self, message):
        """處理用戶指令"""
        text = message.get('text', '').strip()
        
        if not text.startswith('/'):
            return None
        
        parts = text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"🎯 收到指令: {command} {args}")
        
        # 新聞類指令
        if command == '/news':
            count = args[0] if args else 5
            return self.handle_news_command(count)
        
        elif command == '/latest':
            return self.handle_news_command(5)
        
        # 市場數據類指令
        elif command == '/price':
            symbol = args[0] if args else None
            return self.handle_price_command(symbol)
        
        elif command == '/prices':
            return self.handle_prices_command()
        
        elif command == '/market':
            return self.handle_market_command()
        
        elif command == '/top':
            limit = args[0] if args else 10
            return self.handle_top_command(limit)
        
        # 系統類指令
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
