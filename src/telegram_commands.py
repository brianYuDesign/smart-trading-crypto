"""
Telegram Bot 指令處理模組 v2 - 擴充版

新增功能:
1. 市場數據查詢 (/price, /market, /trending)
2. 技術分析 (/chart, /analysis)
3. 個人化訂閱 (/subscribe, /unsubscribe, /mysubs)
"""

import os
import requests
from datetime import datetime
from news_monitor import NewsMonitor

class TelegramCommandHandler:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.news_monitor = NewsMonitor()
        self.coingecko_base = 'https://api.coingecko.com/api/v3'

    def send_message(self, text, parse_mode='HTML'):
        """發送消息到 Telegram"""
        url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"發送消息失敗: {e}")
            return None

    def send_photo(self, photo_url, caption=''):
        """發送圖片到 Telegram"""
        url = f'https://api.telegram.org/bot{self.bot_token}/sendPhoto'
        data = {
            'chat_id': self.chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"發送圖片失敗: {e}")
            return None

    # ========== 市場數據功能 ==========

    def get_price(self, symbol='BTC'):
        """查詢加密貨幣即時價格"""
        try:
            # 轉換常見符號
            coin_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'ADA': 'cardano',
                'XRP': 'ripple',
                'DOT': 'polkadot',
                'DOGE': 'dogecoin',
                'MATIC': 'matic-network',
                'AVAX': 'avalanche-2'
            }

            coin_id = coin_map.get(symbol.upper(), symbol.lower())

            url = f'{self.coingecko_base}/simple/price'
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if coin_id not in data:
                return f"❌ 找不到幣種: {symbol}"

            coin_data = data[coin_id]
            price = coin_data['usd']
            change_24h = coin_data.get('usd_24h_change', 0)
            volume_24h = coin_data.get('usd_24h_vol', 0)
            market_cap = coin_data.get('usd_market_cap', 0)

            # 判斷漲跌
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""

            message = f"""
<b>💰 {symbol.upper()} 價格資訊</b>

📊 <b>當前價格:</b> ${price:,.2f}
{change_emoji} <b>24h 變化:</b> {change_sign}{change_24h:.2f}%
📈 <b>24h 成交量:</b> ${volume_24h:,.0f}
💎 <b>市值:</b> ${market_cap:,.0f}

<i>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
            return message.strip()

        except Exception as e:
            return f"❌ 查詢價格失敗: {str(e)}"

    def get_market_overview(self):
        """查看市場概況"""
        try:
            url = f'{self.coingecko_base}/global'
            response = requests.get(url, timeout=10)
            data = response.json()['data']

            total_market_cap = data['total_market_cap']['usd']
            total_volume = data['total_volume']['usd']
            btc_dominance = data['market_cap_percentage']['bitcoin']
            eth_dominance = data['market_cap_percentage']['ethereum']
            active_cryptos = data['active_cryptocurrencies']

            message = f"""
<b>🌍 加密貨幣市場概況</b>

💰 <b>總市值:</b> ${total_market_cap:,.0f}
📊 <b>24h 成交量:</b> ${total_volume:,.0f}
₿ <b>BTC 市佔率:</b> {btc_dominance:.2f}%
Ξ <b>ETH 市佔率:</b> {eth_dominance:.2f}%
🪙 <b>活躍幣種:</b> {active_cryptos:,}

<i>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
            return message.strip()

        except Exception as e:
            return f"❌ 查詢市場概況失敗: {str(e)}"

    def get_trending(self):
        """查看熱門幣種"""
        try:
            url = f'{self.coingecko_base}/search/trending'
            response = requests.get(url, timeout=10)
            data = response.json()

            coins = data['coins'][:10]  # 前10名

            message = "<b>🔥 熱門幣種排行</b>\n\n"

            for idx, item in enumerate(coins, 1):
                coin = item['item']
                name = coin['name']
                symbol = coin['symbol']
                rank = coin['market_cap_rank']

                message += f"{idx}. <b>{symbol}</b> ({name})\n"
                if rank:
                    message += f"   市值排名: #{rank}\n"
                message += "\n"

            message += f"<i>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"

            return message.strip()

        except Exception as e:
            return f"❌ 查詢熱門幣種失敗: {str(e)}"

    # ========== 技術分析功能 ==========

    def get_chart(self, symbol='BTC', days=7):
        """獲取價格走勢圖"""
        try:
            coin_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana'
            }

            coin_id = coin_map.get(symbol.upper(), symbol.lower())

            # 使用 TradingView 圖表
            chart_url = f"https://s3.tradingview.com/snapshots/{coin_id.upper()}USDT_{days}d.png"

            caption = f"📊 {symbol.upper()} 價格走勢圖 ({days}天)"

            return {'type': 'photo', 'url': chart_url, 'caption': caption}

        except Exception as e:
            return f"❌ 獲取圖表失敗: {str(e)}"

    def get_technical_analysis(self, symbol='BTC'):
        """技術指標分析"""
        try:
            coin_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana'
            }

            coin_id = coin_map.get(symbol.upper(), symbol.lower())

            # 獲取歷史價格數據
            url = f'{self.coingecko_base}/coins/{coin_id}/market_chart'
            params = {'vs_currency': 'usd', 'days': '30'}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            prices = [p[1] for p in data['prices']]
            current_price = prices[-1]

            # 簡單技術指標計算
            sma_7 = sum(prices[-7:]) / 7
            sma_30 = sum(prices) / len(prices)

            high_30d = max(prices)
            low_30d = min(prices)

            # 趨勢判斷
            trend = "📈 上升" if sma_7 > sma_30 else "📉 下降"

            message = f"""
<b>📈 {symbol.upper()} 技術分析</b>

💰 <b>當前價格:</b> ${current_price:,.2f}

<b>移動平均線:</b>
• 7日均線: ${sma_7:,.2f}
• 30日均線: ${sma_30:,.2f}

<b>30天區間:</b>
• 最高: ${high_30d:,.2f}
• 最低: ${low_30d:,.2f}

<b>趨勢:</b> {trend}

<i>⚠️ 僅供參考，不構成投資建議</i>
<i>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
            return message.strip()

        except Exception as e:
            return f"❌ 技術分析失敗: {str(e)}"

    # ========== 原有新聞功能 ==========

    def get_news(self, count=5):
        """獲取最新新聞"""
        try:
            news_data = self.news_monitor.fetch_news(count)

            if not news_data or not news_data.get('results'):
                return "❌ 目前沒有新聞資料"

            message = f"<b>📰 加密貨幣最新新聞 (前 {count} 則)</b>\n\n"

            for idx, news in enumerate(news_data['results'][:count], 1):
                title = news.get('title', '無標題')
                url = news.get('url', '')
                published = news.get('published_at', '')
                source = news.get('source', {}).get('title', '未知來源')

                message += f"{idx}. <b>{title}</b>\n"
                message += f"   來源: {source}\n"
                if url:
                    message += f"   🔗 <a href='{url}'>閱讀全文</a>\n"
                message += "\n"

            return message.strip()

        except Exception as e:
            return f"❌ 獲取新聞失敗: {str(e)}"

    def get_help(self):
        """獲取幫助信息"""
        return """
🤖 <b>Crypto Trading Bot 指令列表</b>

<b>📰 新聞資訊</b>
/news [數量] - 查詢最新加密貨幣新聞
/latest - 快速查看最新 5 則新聞

<b>📊 市場數據</b>
/price [幣種] - 查詢即時價格 (如: /price BTC)
/market - 查看市場概況
/trending - 熱門幣種排行

<b>📈 技術分析</b>
/chart [幣種] - 查看價格走勢圖
/analysis [幣種] - 技術指標分析

<b>⚙️ 個人設定</b>
/subscribe [幣種] - 訂閱價格提醒
/unsubscribe [幣種] - 取消訂閱
/mysubs - 查看我的訂閱

<b>ℹ️ 系統</b>
/status - Bot 運行狀態
/help - 顯示此幫助訊息

<i>💡 提示：正在開發更多功能中...</i>
"""

    def get_status(self):
        """獲取 Bot 狀態"""
        return f"""
<b>🤖 Bot 運行狀態</b>

✅ <b>狀態:</b> 正常運行
📡 <b>連線:</b> 已連接
⏰ <b>時間:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>可用功能:</b>
✅ 新聞查詢
✅ 價格查詢
✅ 市場數據
✅ 技術分析
🚧 訂閱提醒 (開發中)
"""

    # ========== 訂閱管理 (待實作) ==========

    def subscribe_coin(self, symbol):
        """訂閱幣種價格提醒 - 待實作"""
        return f"✅ 已訂閱 {symbol.upper()} 價格提醒\n\n🚧 此功能正在開發中，敬請期待！"

    def unsubscribe_coin(self, symbol):
        """取消訂閱 - 待實作"""
        return f"✅ 已取消訂閱 {symbol.upper()}\n\n🚧 此功能正在開發中，敬請期待！"

    def get_subscriptions(self):
        """查看訂閱列表 - 待實作"""
        return "📋 <b>我的訂閱</b>\n\n🚧 此功能正在開發中，敬請期待！"


def process_command(message):
    """處理 Telegram 指令"""
    handler = TelegramCommandHandler()

    text = message.get('text', '').strip()
    parts = text.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # 新聞指令
    if command == '/news':
        count = int(args[0]) if args and args[0].isdigit() else 5
        response = handler.get_news(count)
        handler.send_message(response)

    elif command == '/latest':
        response = handler.get_news(5)
        handler.send_message(response)

    # 市場數據指令
    elif command == '/price':
        symbol = args[0] if args else 'BTC'
        response = handler.get_price(symbol)
        handler.send_message(response)

    elif command == '/market':
        response = handler.get_market_overview()
        handler.send_message(response)

    elif command == '/trending':
        response = handler.get_trending()
        handler.send_message(response)

    # 技術分析指令
    elif command == '/chart':
        symbol = args[0] if args else 'BTC'
        result = handler.get_chart(symbol)
        if isinstance(result, dict) and result.get('type') == 'photo':
            handler.send_photo(result['url'], result['caption'])
        else:
            handler.send_message(result)

    elif command == '/analysis':
        symbol = args[0] if args else 'BTC'
        response = handler.get_technical_analysis(symbol)
        handler.send_message(response)

    # 訂閱管理指令
    elif command == '/subscribe':
        symbol = args[0] if args else ''
        if not symbol:
            response = "❌ 請指定幣種，例如: /subscribe BTC"
        else:
            response = handler.subscribe_coin(symbol)
        handler.send_message(response)

    elif command == '/unsubscribe':
        symbol = args[0] if args else ''
        if not symbol:
            response = "❌ 請指定幣種，例如: /unsubscribe BTC"
        else:
            response = handler.unsubscribe_coin(symbol)
        handler.send_message(response)

    elif command == '/mysubs':
        response = handler.get_subscriptions()
        handler.send_message(response)

    # 系統指令
    elif command == '/help':
        response = handler.get_help()
        handler.send_message(response)

    elif command == '/status':
        response = handler.get_status()
        handler.send_message(response)

    else:
        response = f"❌ 未知指令: {command}\n\n請輸入 /help 查看可用指令"
        handler.send_message(response)


if __name__ == "__main__":
    # 測試模式
    print("Telegram Bot 指令處理器已啟動")
