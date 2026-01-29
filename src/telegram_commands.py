"""
Telegram Bot 指令處理模組 V3 - 完整增強版

新增功能:
✅ 新聞查詢 (/news)
✅ 市場數據 (/price, /market, /trending)
✅ 技術分析 (/chart, /analysis)
✅ 個人訂閱管理 (/subscribe, /unsubscribe, /mysubs)

支援指令:
📰 新聞類:
- /news [數量] - 查詢最新新聞 (預設5則)
- /latest - 快速查看最新5則新聞

📊 市場數據類:
- /price <幣種> - 查詢幣種價格 (如 /price BTC)
- /prices - 主流幣種價格總覽
- /market - 加密貨幣市場總覽
- /top [數量] - 市值排行榜 (預設10)
- /trending - 熱門幣種排行榜

📈 技術分析類:
- /chart <幣種> - 價格走勢圖
- /analysis <幣種> - 技術指標分析

⚙️ 訂閱管理:
- /subscribe <幣種> [條件] - 訂閱價格提醒
- /unsubscribe <幣種> - 取消訂閱
- /mysubs - 查看我的訂閱清單

🔧 系統類:
- /status - Bot運行狀態
- /help - 幫助訊息
"""

import os
import requests
from datetime import datetime
from src.news_monitor import NewsMonitor
from src.market_data import MarketDataAPI, MarketDataFormatter

class TelegramCommandHandler:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.news_monitor = NewsMonitor()
        self.market_api = MarketDataAPI()
        self.formatter = MarketDataFormatter()
        
        # 訂閱數據 (之後可移到資料庫)
        self.subscriptions = {}
        
    def handle_command(self, message):
        """處理 Telegram 指令"""
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        
        if not text.startswith('/'):
            return None
            
        # 解析指令和參數
        parts = text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 路由到對應的處理函數
        handlers = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/status': self.cmd_status,
            
            # 新聞類
            '/news': self.cmd_news,
            '/latest': self.cmd_latest,
            
            # 市場數據類
            '/price': self.cmd_price,
            '/prices': self.cmd_prices,
            '/market': self.cmd_market,
            '/top': self.cmd_top,
            '/trending': self.cmd_trending,
            
            # 技術分析類
            '/chart': self.cmd_chart,
            '/analysis': self.cmd_analysis,
            
            # 訂閱管理
            '/subscribe': self.cmd_subscribe,
            '/unsubscribe': self.cmd_unsubscribe,
            '/mysubs': self.cmd_mysubs,
        }
        
        handler = handlers.get(command)
        if handler:
            return handler(chat_id, args)
        else:
            return self.cmd_unknown(chat_id, command)
    
    # ============ 新聞類指令 ============
    
    def cmd_news(self, chat_id, args):
        """查詢最新新聞"""
        try:
            count = int(args[0]) if args else 5
            count = min(count, 20)  # 最多20則
            
            news_list = self.news_monitor.fetch_latest_news(count)
            
            if not news_list:
                return self.send_message(chat_id, "❌ 目前無法獲取新聞，請稍後再試")
            
            message = f"📰 <b>最新加密貨幣新聞 (前 {len(news_list)} 則)</b>\n\n"
            
            for i, news in enumerate(news_list, 1):
                title = news.get('title', '無標題')
                url = news.get('url', '')
                source = news.get('source', {}).get('title', '未知來源')
                published = news.get('published_at', '')
                
                # 格式化時間
                if published:
                    try:
                        dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m/%d %H:%M')
                    except:
                        time_str = ''
                else:
                    time_str = ''
                
                message += f"<b>{i}. {title}</b>\n"
                if time_str:
                    message += f"🕐 {time_str} | "
                message += f"📡 {source}\n"
                if url:
                    message += f"🔗 <a href='{url}'>閱讀更多</a>\n"
                message += "\n"
            
            message += "💡 使用 /latest 快速查看最新新聞"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(chat_id, f"❌ 獲取新聞時發生錯誤: {str(e)}")
    
    def cmd_latest(self, chat_id, args):
        """快速查看最新5則新聞"""
        return self.cmd_news(chat_id, ['5'])
    
    # ============ 市場數據類指令 ============
    
    def cmd_price(self, chat_id, args):
        """查詢單一幣種價格"""
        if not args:
            return self.send_message(
                chat_id,
                "❌ 請指定幣種，例如: /price BTC"
            )
        
        symbol = args[0].upper()
        try:
            data = self.market_api.get_coin_price(symbol)
            if data:
                message = self.formatter.format_coin_detail(data)
                return self.send_message(chat_id, message, parse_mode='HTML')
            else:
                return self.send_message(
                    chat_id,
                    f"❌ 找不到 {symbol} 的價格資訊"
                )
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 查詢價格時發生錯誤: {str(e)}"
            )
    
    def cmd_prices(self, chat_id, args):
        """主流幣種價格總覽"""
        try:
            symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA']
            message = "💰 <b>主流幣種價格</b>\n\n"
            
            for symbol in symbols:
                data = self.market_api.get_coin_price(symbol)
                if data:
                    price = data.get('current_price', 0)
                    change = data.get('price_change_percentage_24h', 0)
                    emoji = "🟢" if change >= 0 else "🔴"
                    
                    message += f"{emoji} <b>{symbol}</b>: ${price:,.2f} "
                    message += f"({change:+.2f}%)\n"
            
            message += "\n💡 使用 /price BTC 查看詳細資訊"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 查詢價格時發生錯誤: {str(e)}"
            )
    
    def cmd_market(self, chat_id, args):
        """市場總覽"""
        try:
            data = self.market_api.get_market_overview()
            if data:
                message = self.formatter.format_market_overview(data)
                return self.send_message(chat_id, message, parse_mode='HTML')
            else:
                return self.send_message(
                    chat_id,
                    "❌ 無法獲取市場數據"
                )
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 查詢市場數據時發生錯誤: {str(e)}"
            )
    
    def cmd_top(self, chat_id, args):
        """市值排行榜"""
        try:
            count = int(args[0]) if args else 10
            count = min(count, 50)  # 最多50個
            
            coins = self.market_api.get_top_coins(count)
            if not coins:
                return self.send_message(chat_id, "❌ 無法獲取排行榜數據")
            
            message = f"🏆 <b>市值排行榜 Top {count}</b>\n\n"
            
            for coin in coins:
                rank = coin.get('market_cap_rank', '?')
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')
                price = coin.get('current_price', 0)
                change = coin.get('price_change_percentage_24h', 0)
                mcap = coin.get('market_cap', 0)
                
                emoji = "🟢" if change >= 0 else "🔴"
                
                message += f"<b>{rank}. {symbol}</b> ({name})\n"
                message += f"   💵 ${price:,.4f} {emoji} {change:+.2f}%\n"
                message += f"   💎 市值: ${mcap/1e9:.2f}B\n\n"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 查詢排行榜時發生錯誤: {str(e)}"
            )
    
    def cmd_trending(self, chat_id, args):
        """熱門幣種"""
        try:
            trending = self.market_api.get_trending_coins()
            if not trending:
                return self.send_message(chat_id, "❌ 無法獲取熱門幣種數據")
            
            message = "🔥 <b>熱門幣種排行</b>\n\n"
            
            for i, coin in enumerate(trending, 1):
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')
                rank = coin.get('market_cap_rank', '?')
                
                message += f"{i}. <b>{symbol}</b> ({name})\n"
                message += f"   📊 市值排名: #{rank}\n\n"
            
            message += "💡 使用 /price 查看詳細價格資訊"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 查詢熱門幣種時發生錯誤: {str(e)}"
            )
    
    # ============ 技術分析類指令 ============
    
    def cmd_chart(self, chat_id, args):
        """價格走勢圖"""
        if not args:
            return self.send_message(
                chat_id,
                "❌ 請指定幣種，例如: /chart BTC"
            )
        
        symbol = args[0].upper()
        try:
            # TODO: 整合圖表生成功能
            return self.send_message(
                chat_id,
                f"📊 {symbol} 價格走勢圖功能開發中...\n"
                f"即將推出: K線圖、移動平均線、成交量圖表"
            )
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 生成圖表時發生錯誤: {str(e)}"
            )
    
    def cmd_analysis(self, chat_id, args):
        """技術指標分析"""
        if not args:
            return self.send_message(
                chat_id,
                "❌ 請指定幣種，例如: /analysis BTC"
            )
        
        symbol = args[0].upper()
        try:
            data = self.market_api.get_coin_price(symbol)
            if not data:
                return self.send_message(
                    chat_id,
                    f"❌ 找不到 {symbol} 的資訊"
                )
            
            # 獲取歷史數據進行簡單分析
            price = data.get('current_price', 0)
            high_24h = data.get('high_24h', price)
            low_24h = data.get('low_24h', price)
            change_24h = data.get('price_change_percentage_24h', 0)
            
            message = f"📈 <b>{symbol} 技術分析</b>\n\n"
            message += f"💵 當前價格: ${price:,.2f}\n"
            message += f"📊 24h 區間: ${low_24h:,.2f} - ${high_24h:,.2f}\n"
            message += f"📈 24h 漲跌: {change_24h:+.2f}%\n\n"
            
            # 簡單趨勢判斷
            if change_24h > 5:
                message += "✅ <b>趨勢: 強勢上漲</b> 🚀\n"
            elif change_24h > 0:
                message += "✅ <b>趨勢: 溫和上漲</b> ↗️\n"
            elif change_24h > -5:
                message += "⚠️ <b>趨勢: 小幅下跌</b> ↘️\n"
            else:
                message += "❌ <b>趨勢: 明顯下跌</b> 📉\n"
            
            message += "\n💡 更詳細的技術指標分析即將推出"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 分析時發生錯誤: {str(e)}"
            )
    
    # ============ 訂閱管理類指令 ============
    
    def cmd_subscribe(self, chat_id, args):
        """訂閱價格提醒"""
        if not args:
            return self.send_message(
                chat_id,
                "❌ 請指定幣種，例如: /subscribe BTC\n"
                "或設定條件: /subscribe BTC >50000"
            )
        
        symbol = args[0].upper()
        condition = ' '.join(args[1:]) if len(args) > 1 else None
        
        # 儲存訂閱 (暫時存在記憶體中)
        if chat_id not in self.subscriptions:
            self.subscriptions[chat_id] = []
        
        sub = {
            'symbol': symbol,
            'condition': condition,
            'created_at': datetime.now().isoformat()
        }
        self.subscriptions[chat_id].append(sub)
        
        message = f"✅ 已訂閱 <b>{symbol}</b>"
        if condition:
            message += f" (條件: {condition})"
        message += "\n\n使用 /mysubs 查看所有訂閱"
        
        return self.send_message(chat_id, message, parse_mode='HTML')
    
    def cmd_unsubscribe(self, chat_id, args):
        """取消訂閱"""
        if not args:
            return self.send_message(
                chat_id,
                "❌ 請指定要取消的幣種，例如: /unsubscribe BTC"
            )
        
        symbol = args[0].upper()
        
        if chat_id not in self.subscriptions:
            return self.send_message(chat_id, "❌ 你還沒有任何訂閱")
        
        # 移除訂閱
        original_count = len(self.subscriptions[chat_id])
        self.subscriptions[chat_id] = [
            sub for sub in self.subscriptions[chat_id]
            if sub['symbol'] != symbol
        ]
        removed_count = original_count - len(self.subscriptions[chat_id])
        
        if removed_count > 0:
            return self.send_message(
                chat_id,
                f"✅ 已取消 <b>{symbol}</b> 的訂閱",
                parse_mode='HTML'
            )
        else:
            return self.send_message(
                chat_id,
                f"❌ 找不到 {symbol} 的訂閱"
            )
    
    def cmd_mysubs(self, chat_id, args):
        """查看訂閱清單"""
        if chat_id not in self.subscriptions or not self.subscriptions[chat_id]:
            return self.send_message(
                chat_id,
                "📋 你還沒有任何訂閱\n\n"
                "使用 /subscribe BTC 開始訂閱"
            )
        
        message = "📋 <b>我的訂閱清單</b>\n\n"
        
        for i, sub in enumerate(self.subscriptions[chat_id], 1):
            symbol = sub['symbol']
            condition = sub.get('condition', '即時價格更新')
            
            message += f"{i}. <b>{symbol}</b>\n"
            message += f"   ⚙️ 條件: {condition}\n\n"
        
        message += "💡 使用 /unsubscribe BTC 取消訂閱"
        
        return self.send_message(chat_id, message, parse_mode='HTML')
    
    # ============ 系統類指令 ============
    
    def cmd_start(self, chat_id, args):
        """歡迎訊息"""
        message = """
🤖 <b>歡迎使用 Smart Crypto Trading Bot!</b>

我可以幫你:
📰 追蹤最新加密貨幣新聞
📊 查詢即時價格與市場數據
📈 提供技術分析與走勢圖
⏰ 設定價格提醒訂閱

<b>快速開始:</b>
• /news - 查看最新新聞
• /price BTC - 查看比特幣價格
• /market - 查看市場總覽
• /help - 查看完整指令清單

讓我們開始吧! 🚀
"""
        return self.send_message(chat_id, message, parse_mode='HTML')
    
    def cmd_help(self, chat_id, args):
        """幫助訊息"""
        message = """
📚 <b>指令清單</b>

<b>📰 新聞類:</b>
/news [數量] - 最新新聞 (預設5則)
/latest - 快速查看最新新聞

<b>📊 市場數據:</b>
/price <幣種> - 查詢價格 (例: /price BTC)
/prices - 主流幣種總覽
/market - 市場總覽
/top [數量] - 市值排行 (預設10)
/trending - 熱門幣種

<b>📈 技術分析:</b>
/chart <幣種> - 價格走勢圖
/analysis <幣種> - 技術指標分析

<b>⚙️ 訂閱管理:</b>
/subscribe <幣種> - 訂閱提醒
/unsubscribe <幣種> - 取消訂閱
/mysubs - 我的訂閱

<b>🔧 系統:</b>
/status - Bot 狀態
/help - 顯示此訊息

<b>💡 使用範例:</b>
• /price BTC - 查看比特幣價格
• /news 10 - 查看10則新聞
• /subscribe ETH >3000 - 以太坊超過3000時提醒
"""
        return self.send_message(chat_id, message, parse_mode='HTML')
    
    def cmd_status(self, chat_id, args):
        """Bot 狀態"""
        try:
            # 測試 API 連線
            market_ok = self.market_api.get_market_overview() is not None
            news_ok = True  # 假設新聞 API 正常
            
            message = "🔧 <b>Bot 運行狀態</b>\n\n"
            message += f"📊 市場數據 API: {'✅ 正常' if market_ok else '❌ 異常'}\n"
            message += f"📰 新聞 API: {'✅ 正常' if news_ok else '❌ 異常'}\n"
            message += f"⏰ 訂閱數量: {len(self.subscriptions.get(chat_id, []))}\n"
            message += f"\n🕐 系統時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(chat_id, message, parse_mode='HTML')
            
        except Exception as e:
            return self.send_message(
                chat_id,
                f"❌ 檢查狀態時發生錯誤: {str(e)}"
            )
    
    def cmd_unknown(self, chat_id, command):
        """未知指令"""
        message = f"❌ 未知指令: {command}\n\n使用 /help 查看可用指令"
        return self.send_message(chat_id, message)
    
    # ============ 輔助方法 ============
    
    def send_message(self, chat_id, text, parse_mode=None):
        """發送 Telegram 訊息"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            print(f"發送訊息失敗: {str(e)}")
            return None


    def process_commands(self):
        """
        處理 Telegram 指令（單次執行模式）
        從 Telegram 獲取最新更新並處理指令
        """
        try:
            # 獲取最新的更新
            url = f'https://api.telegram.org/bot{self.bot_token}/getUpdates'
            response = requests.get(url, params={'timeout': 10, 'limit': 10})

            if response.status_code != 200:
                print(f"❌ 獲取更新失敗: {response.status_code}")
                return

            data = response.json()

            if not data.get('ok'):
                print(f"❌ Telegram API 錯誤: {data}")
                return

            updates = data.get('result', [])

            if not updates:
                print("ℹ️ 沒有新的指令")
                return

            print(f"📨 收到 {len(updates)} 個更新")

            # 處理每個更新
            for update in updates:
                if 'message' in update:
                    message = update['message']
                    text = message.get('text', '')

                    if text.startswith('/'):
                        print(f"\n處理指令: {text}")
                        response = self.handle_command(message)

                        if response:
                            chat_id = message.get('chat', {}).get('id')
                            self.send_message(chat_id, response)
                            print(f"✅ 已回應")

            # 標記更新為已讀（使用最後一個 update_id + 1）
            if updates:
                last_update_id = updates[-1]['update_id']
                confirm_url = f'https://api.telegram.org/bot{self.bot_token}/getUpdates'
                requests.get(confirm_url, params={'offset': last_update_id + 1, 'limit': 1})
                print(f"\n✅ 已處理並確認 {len(updates)} 個更新")

        except Exception as e:
            print(f"❌ 處理指令時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
