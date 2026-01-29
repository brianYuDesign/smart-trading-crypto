"""
Telegram Bot Webhook Server - 最終增強版

新增功能：
1. 價格為 0 時的三重 fallback 機制（CoinGecko → Binance → CryptoCompare）
2. 顯示數據來源標註
3. 用戶時區支持（/timezone 指令）
4. 多語言新聞來源（中文 + 英文）
5. 強健的錯誤處理（單一來源失敗不影響其他來源）
"""
from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime
import pytz
import feedparser
from concurrent.futures import ThreadPoolExecutor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境變數
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# API 配置
COINGECKO_BASE = 'https://api.coingecko.com/api/v3'

# 新聞來源配置（多個來源）
NEWS_SOURCES = {
    'coindesk': {
        'name': 'CoinDesk',
        'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'language': 'en'
    },
    'abmedia': {
        'name': '鏈新聞',
        'url': 'https://abmedia.io/feed',
        'language': 'zh'
    },
    'zombit': {
        'name': '桑幣區識',
        'url': 'https://zombit.info/feed',
        'language': 'zh'
    },
    'blocktempo': {
        'name': '動區動趨',
        'url': 'https://www.blocktempo.com/feed/',
        'language': 'zh'
    }
}

# 備用 API（當 CoinGecko 失敗時）
BINANCE_BASE = 'https://api.binance.com/api/v3'
CRYPTO_COMPARE_BASE = 'https://min-api.cryptocompare.com/data'

# 線程池
executor = ThreadPoolExecutor(max_workers=3)

# 用戶時區緩存 (chat_id: timezone_str)
user_timezones = {}

def get_user_timezone(chat_id):
    """獲取用戶時區，默認為台北時區"""
    return user_timezones.get(chat_id, 'Asia/Taipei')

def format_time_with_tz(chat_id):
    """根據用戶時區格式化當前時間"""
    tz_str = get_user_timezone(chat_id)
    try:
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        return now.strftime('%Y-%m-%d %H:%M:%S %Z')
    except:
        # Fallback 到 UTC
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def send_message(chat_id, text, reply_markup=None):
    """發送 Telegram 訊息"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息錯誤: {e}")
        return None

def get_price_from_coingecko(coin_ids):
    """從 CoinGecko 獲取價格（主要備援）"""
    try:
        url = f'{COINGECKO_BASE}/simple/price'
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info(f"✓ CoinGecko API 成功")
                return data, 'CoinGecko'

        logger.warning(f"CoinGecko API 失敗: {response.status_code}")
        return None, None
    except Exception as e:
        logger.error(f"CoinGecko API 錯誤: {e}")
        return None, None

def get_price_from_binance(symbol):
    """從 Binance 獲取價格（備用 1）"""
    try:
        url = f'{BINANCE_BASE}/ticker/24hr'
        params = {'symbol': symbol}

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = float(data.get('lastPrice', 0))
            change_24h = float(data.get('priceChangePercent', 0))

            if price > 0:
                logger.info(f"✓ Binance API 成功 ({symbol})")
                return price, change_24h

        logger.warning(f"Binance API 失敗: {response.status_code}")
        return None, None
    except Exception as e:
        logger.error(f"Binance API 錯誤: {e}")
        return None, None

def get_price_from_cryptocompare(symbol):
    """從 CryptoCompare 獲取價格（備用 2）"""
    try:
        url = f'{CRYPTO_COMPARE_BASE}/pricemultifull'
        params = {
            'fsyms': symbol,
            'tsyms': 'USD'
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            raw_data = data.get('RAW', {}).get(symbol, {}).get('USD', {})

            price = raw_data.get('PRICE', 0)
            change_24h = raw_data.get('CHANGEPCT24HOUR', 0)

            if price > 0:
                logger.info(f"✓ CryptoCompare API 成功 ({symbol})")
                return price, change_24h

        logger.warning(f"CryptoCompare API 失敗: {response.status_code}")
        return None, None
    except Exception as e:
        logger.error(f"CryptoCompare API 錯誤: {e}")
        return None, None

def get_coin_price_with_fallback(coin_id, binance_symbol, cc_symbol):
    """
    獲取幣價（三重備援機制）
    1. CoinGecko (主要)
    2. Binance (備用 1)
    3. CryptoCompare (備用 2)
    """
    sources_used = []

    # 嘗試 1: CoinGecko
    data, source = get_price_from_coingecko([coin_id])
    if data and coin_id in data:
        coin_data = data[coin_id]
        price = coin_data.get('usd', 0)
        change = coin_data.get('usd_24h_change', 0)

        if price > 0:
            return price, change, 'CoinGecko'

    # 嘗試 2: Binance
    logger.info(f"⚠️ CoinGecko 失敗，嘗試 Binance...")
    price, change = get_price_from_binance(binance_symbol)
    if price and price > 0:
        return price, change, 'Binance'

    # 嘗試 3: CryptoCompare
    logger.info(f"⚠️ Binance 失敗，嘗試 CryptoCompare...")
    price, change = get_price_from_cryptocompare(cc_symbol)
    if price and price > 0:
        return price, change, 'CryptoCompare'

    # 所有來源都失敗
    logger.error(f"❌ 所有 API 都無法獲取 {coin_id} 的價格")
    return None, None, None

def handle_price(chat_id):
    """處理 /price 指令 - 查詢 BTC、ETH、BNB 價格"""
    try:
        # 幣種配置：(coingecko_id, binance_symbol, cryptocompare_symbol, display_name, emoji)
        coins = [
            ('bitcoin', 'BTCUSDT', 'BTC', 'Bitcoin', '🟠'),
            ('ethereum', 'ETHUSDT', 'ETH', 'Ethereum', '🔵'),
            ('binancecoin', 'BNBUSDT', 'BNB', 'BNB', '🟡')
        ]

        results = []
        sources_used = set()

        for coin_id, binance_sym, cc_sym, name, emoji in coins:
            price, change, source = get_coin_price_with_fallback(coin_id, binance_sym, cc_sym)

            if price is None:
                results.append(f"{emoji} <b>{name}:</b> ❌ 無法獲取")
            else:
                change_emoji = "📈" if change >= 0 else "📉"
                change_sign = "+" if change >= 0 else ""
                results.append(
                    f"{emoji} <b>{name}:</b> ${price:,.2f}\n"
                    f"   {change_emoji} 24h: {change_sign}{change:.2f}%"
                )
                sources_used.add(source)

        if not sources_used:
            send_message(chat_id, "❌ 所有價格查詢都失敗了，請稍後再試")
            return

        message = "💰 <b>加密貨幣價格</b>\n\n"
        message += "\n\n".join(results)
        message += f"\n\n📡 <b>數據來源:</b> {', '.join(sorted(sources_used))}"
        message += f"\n⏰ <b>更新時間:</b> {format_time_with_tz(chat_id)}"

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"價格查詢錯誤: {e}")
        send_message(chat_id, "❌ 查詢價格時發生錯誤，請稍後再試")

def handle_market(chat_id):
    """處理 /market 指令 - 查詢市場總覽"""
    try:
        url = f'{COINGECKO_BASE}/global'
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            send_message(chat_id, "❌ 無法獲取市場數據，請稍後再試")
            return

        data = response.json()
        market_data = data.get('data', {})

        total_market_cap = market_data.get('total_market_cap', {}).get('usd', 0)
        total_volume = market_data.get('total_volume', {}).get('usd', 0)
        btc_dominance = market_data.get('market_cap_percentage', {}).get('btc', 0)
        eth_dominance = market_data.get('market_cap_percentage', {}).get('eth', 0)

        # 檢查是否有無效數據
        if total_market_cap == 0 or total_volume == 0:
            send_message(chat_id, "⚠️ 市場數據暫時不完整，請稍後再試")
            return

        message = f"""📊 <b>加密貨幣市場總覽</b>

💎 <b>總市值:</b> ${total_market_cap/1e12:.2f}T
📊 <b>24h 交易量:</b> ${total_volume/1e9:.2f}B

<b>市場主導地位:</b>
🟠 <b>BTC:</b> {btc_dominance:.2f}%
🔵 <b>ETH:</b> {eth_dominance:.2f}%

📡 <b>數據來源:</b> CoinGecko
⏰ <b>更新時間:</b> {format_time_with_tz(chat_id)}
"""

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"市場查詢錯誤: {e}")
        send_message(chat_id, "❌ 查詢市場時發生錯誤，請稍後再試")

def fetch_news_from_source(source_key, source_info, max_items=3):
    """從單一新聞源獲取新聞（帶錯誤處理）"""
    try:
        feed = feedparser.parse(source_info['url'])

        if not feed.entries:
            logger.warning(f"新聞源 {source_info['name']} 無內容")
            return None

        news_items = []
        for entry in feed.entries[:max_items]:
            title = entry.get('title', '無標題')
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))

            # 清理 HTML 標籤
            import re
            summary = re.sub('<[^<]+?>', '', summary)

            # 限制摘要長度
            if len(summary) > 100:
                summary = summary[:100] + '...'

            news_items.append({
                'title': title,
                'link': link,
                'summary': summary
            })

        return {
            'source_name': source_info['name'],
            'language': source_info['language'],
            'items': news_items
        }

    except Exception as e:
        logger.error(f"獲取 {source_info['name']} 新聞失敗: {e}")
        return None

def handle_news(chat_id):
    """處理 /news 指令 - 從多個來源獲取最新新聞"""
    try:
        # 並行獲取所有新聞源
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_news = []
        successful_sources = []
        failed_sources = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_source = {
                executor.submit(fetch_news_from_source, key, info, 3): key 
                for key, info in NEWS_SOURCES.items()
            }

            for future in as_completed(future_to_source):
                source_key = future_to_source[future]
                try:
                    result = future.result(timeout=10)
                    if result:
                        all_news.append(result)
                        successful_sources.append(NEWS_SOURCES[source_key]['name'])
                    else:
                        failed_sources.append(NEWS_SOURCES[source_key]['name'])
                except Exception as e:
                    logger.error(f"處理 {source_key} 時出錯: {e}")
                    failed_sources.append(NEWS_SOURCES[source_key]['name'])

        # 如果所有來源都失敗
        if not all_news:
            message = "❌ <b>無法獲取新聞</b>\n\n"
            message += "所有新聞源暫時無法訪問，請稍後再試。\n"
            message += f"⏰ {format_time_with_tz(chat_id)}"
            send_message(chat_id, message)
            return

        # 組裝訊息
        message = "📰 <b>最新加密貨幣新聞</b>\n\n"

        # 按語言分組顯示
        zh_news = [n for n in all_news if n['language'] == 'zh']
        en_news = [n for n in all_news if n['language'] == 'en']

        # 先顯示中文新聞
        if zh_news:
            message += "🇹🇼 <b>中文新聞</b>\n\n"
            for news_source in zh_news:
                message += f"📍 <b>{news_source['source_name']}</b>\n"
                for item in news_source['items']:
                    message += f"• <b>{item['title']}</b>\n"
                    if item['summary']:
                        message += f"  {item['summary']}\n"
                    message += f"  🔗 <a href='{item['link']}'>閱讀更多</a>\n"
                message += "\n"

        # 再顯示英文新聞
        if en_news:
            message += "🌐 <b>International News</b>\n\n"
            for news_source in en_news:
                message += f"📍 <b>{news_source['source_name']}</b>\n"
                for item in news_source['items']:
                    message += f"• <b>{item['title']}</b>\n"
                    if item['summary']:
                        message += f"  {item['summary']}\n"
                    message += f"  🔗 <a href='{item['link']}'>Read more</a>\n"
                message += "\n"

        # 顯示數據來源狀態
        message += f"📡 <b>成功來源:</b> {', '.join(successful_sources)}\n"
        if failed_sources:
            message += f"⚠️ <b>失敗來源:</b> {', '.join(failed_sources)}\n"
        message += f"⏰ <b>更新時間:</b> {format_time_with_tz(chat_id)}"

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"新聞獲取錯誤: {e}")
        send_message(chat_id, "❌ 獲取新聞時發生錯誤，請稍後再試")

def handle_start(chat_id):
    """處理 /start 指令"""
    message = """👋 <b>歡迎使用加密貨幣機器人！</b>

我可以幫你：
💰 查詢實時價格
📊 查看市場總覽
📰 獲取最新新聞（中文 + 英文）
🌍 設定時區

<b>可用指令：</b>
/price - 查詢 BTC、ETH、BNB 價格
/market - 查看市場總覽
/news - 獲取最新新聞
/timezone - 設定時區
/help - 查看幫助

💡 <b>提示：</b>點擊指令或使用 / 按鈕快速選擇！
"""

    # 添加快捷按鈕
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '💰 查詢價格', 'callback_data': 'price'},
                {'text': '📈 市場總覽', 'callback_data': 'market'}
            ],
            [
                {'text': '📰 最新新聞', 'callback_data': 'news'},
                {'text': '❓ 幫助', 'callback_data': 'help'}
            ]
        ]
    }

    send_message(chat_id, message, keyboard)

def handle_help(chat_id):
    """處理 /help 指令"""
    message = """❓ <b>幫助資訊</b>

📊 <b>市場資訊查詢：</b>

💰 <b>/price</b>
   查詢 BTC、ETH、BNB 的實時價格
   顯示 24 小時漲跌幅
   支持多個數據來源（CoinGecko、Binance、CryptoCompare）

📈 <b>/market</b>
   查看加密貨幣市場總市值
   查看 24 小時交易量
   查看 BTC、ETH 市場主導地位

📰 <b>/news</b>
   獲取最新的加密貨幣新聞
   支持中文新聞源（鏈新聞、桑幣區識、動區動趨）
   支持英文新聞源（CoinDesk）
   單一來源失敗不影響其他來源

🌍 <b>/timezone</b>
   設定您的時區
   使所有時間顯示符合您的當地時間

   常用時區範例：
   • Asia/Taipei (台北)
   • Asia/Tokyo (東京)
   • Asia/Hong_Kong (香港)
   • America/New_York (紐約)
   • Europe/London (倫敦)

---
💡 <b>提示：</b>
• 所有價格數據都有多重來源備份，確保穩定性
• 新聞功能支持多個來源，單一來源失敗不影響其他
• 時間顯示會根據您設定的時區自動調整
• 數據來源會標註在每次查詢結果中

📧 <b>問題回報：</b>如有任何問題，請聯繫管理員
"""

    send_message(chat_id, message)

def handle_timezone(chat_id, text):
    """處理 /timezone 指令"""
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        # 沒有參數，顯示當前時區和說明
        current_tz = get_user_timezone(chat_id)
        message = f"""🌍 <b>時區設定</b>

<b>當前時區:</b> {current_tz}
<b>當前時間:</b> {format_time_with_tz(chat_id)}

<b>修改時區:</b>
使用指令 <code>/timezone 時區名稱</code>

<b>常用時區:</b>
• <code>/timezone Asia/Taipei</code> (台北 GMT+8)
• <code>/timezone Asia/Tokyo</code> (東京 GMT+9)
• <code>/timezone Asia/Hong_Kong</code> (香港 GMT+8)
• <code>/timezone Asia/Shanghai</code> (上海 GMT+8)
• <code>/timezone America/New_York</code> (紐約 GMT-5)
• <code>/timezone Europe/London</code> (倫敦 GMT+0)

💡 查看完整時區列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
"""
        send_message(chat_id, message)
    else:
        # 設定新時區
        new_tz = parts[1].strip()
        try:
            # 驗證時區是否有效
            pytz.timezone(new_tz)
            user_timezones[chat_id] = new_tz

            message = f"""✅ <b>時區設定成功！</b>

<b>新時區:</b> {new_tz}
<b>當前時間:</b> {format_time_with_tz(chat_id)}

所有時間顯示將使用此時區。
"""
            send_message(chat_id, message)
            logger.info(f"用戶 {chat_id} 設定時區為 {new_tz}")

        except Exception as e:
            message = f"""❌ <b>無效的時區名稱</b>

您輸入的時區 <code>{new_tz}</code> 無效。

請使用標準時區名稱，例如：
• Asia/Taipei
• America/New_York
• Europe/London

💡 查看完整列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
"""
            send_message(chat_id, message)
            logger.warning(f"用戶 {chat_id} 嘗試設定無效時區: {new_tz}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 Telegram webhook"""
    try:
        data = request.json

        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            if text.startswith('/'):
                command = text.split()[0].lower()

                if command == '/start':
                    handle_start(chat_id)
                elif command == '/price':
                    handle_price(chat_id)
                elif command == '/market':
                    handle_market(chat_id)
                elif command == '/news':
                    handle_news(chat_id)
                elif command == '/help':
                    handle_help(chat_id)
                elif command == '/timezone':
                    handle_timezone(chat_id, text)
                else:
                    send_message(chat_id, "❓ 未知指令，請使用 /help 查看可用指令")

        elif 'callback_query' in data:
            # 處理按鈕回調
            callback = data['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_data = callback['data']

            if callback_data == 'price':
                handle_price(chat_id)
            elif callback_data == 'market':
                handle_market(chat_id)
            elif callback_data == 'news':
                handle_news(chat_id)
            elif callback_data == 'help':
                handle_help(chat_id)

        return jsonify({'status': 'ok'})

    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'features': {
            'price_fallback': 'CoinGecko → Binance → CryptoCompare',
            'news_sources': list(NEWS_SOURCES.keys()),
            'timezone_support': True
        }
    })

@app.route('/', methods=['GET'])
def index():
    """首頁"""
    return jsonify({
        'service': 'Telegram Crypto Bot',
        'version': '2.0 (Enhanced)',
        'status': 'running',
        'endpoints': {
            '/webhook': 'POST - Telegram webhook',
            '/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
