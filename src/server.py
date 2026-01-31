"""
Telegram Bot Webhook Server - V2 智能投資顧問版

新增功能：
1. ✅ 風險屬性評估系統（問卷 + 動態分類）
2. ✅ 個性化進退場策略（依風險等級自動調整）
3. ✅ 主動監控排程系統（定期檢查 + 智能通知）
4. ✅ 持倉管理與追蹤
5. ✅ 完整的資料庫持久化

原有功能（保留）：
- 價格查詢（多重 fallback）
- 新聞訂閱（中英文）
- 時區設定
"""
from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime
import feedparser
from concurrent.futures import ThreadPoolExecutor
from .database import db
from .trading_strategy import trading_strategy
from .market_monitor import init_monitor

# 配置日誌
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境變數
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')

# 初始化市場監控 (Global variable to hold the monitor instance)
monitor = None

def init_app_monitor():
    global monitor
    if TELEGRAM_BOT_TOKEN:
        monitor = init_monitor(TELEGRAM_BOT_TOKEN)
        monitor.start()
    else:
        logger.warning("TELEGRAM_BOT_TOKEN 未設置，監控功能未啟動")

# 用戶時區存儲（現在使用資料庫）
user_timezones = {}

# RSS 新聞來源
NEWS_FEEDS = {
    'zh': [
        'https://news.google.com/rss/search?q=加密貨幣&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
        'https://news.google.com/rss/search?q=比特幣&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
    ],
    'en': [
        'https://cointelegraph.com/rss',
        'https://decrypt.co/feed',
    ]
}


def send_message(chat_id, text, parse_mode='HTML'):
    """發送 Telegram 訊息"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN 未設置")
        return None
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息失敗: {e}")
        return None


def get_user_timezone(user_id):
    """獲取用戶時區"""
    user = db.get_user(user_id)
    if user:
        return user['timezone']
    return 'Asia/Taipei'


def fetch_crypto_price_multi_source(query):
    """多重來源獲取價格 (支援 CoinGecko 與 Binance)"""
    query = query.lower().strip()
    
    # 常見幣種映射表 (Ticker -> CoinGecko ID)
    # 用戶輸入可能是 ticker (btc) 也可能是 id (bitcoin)
    TICKER_MAP = {
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'sol': 'solana',
        'bnb': 'binancecoin',
        'xrp': 'ripple',
        'ada': 'cardano',
        'doge': 'dogecoin',
        'avax': 'avalanche-2',
        'dot': 'polkadot',
        'matic': 'matic-network',
        'link': 'chainlink',
        'ltc': 'litecoin',
        'uni': 'uniswap',
        'atom': 'cosmos',
        'etc': 'ethereum-classic',
        'xlm': 'stellar',
        'trx': 'tron',
        'busd': 'binance-usd',
        'shib': 'shiba-inu'
    }
    
    # 決定 CoinGecko 使用的 ID
    # 如果輸入是 ticker (如 btc)，轉為 bitcoin
    # 如果輸入已是全名 (如 bitcoin)，保持不變 (TICKER_MAP.get('bitcoin', 'bitcoin') -> 'bitcoin')
    cg_id = TICKER_MAP.get(query, query)
    
    # 1. CoinGecko API
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
            
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': cg_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if cg_id in data:
                return {
                    'source': 'CoinGecko',
                    'price': float(data[cg_id]['usd']),
                    'change_24h': float(data[cg_id].get('usd_24h_change', 0))
                }
    except Exception as e:
        logger.warning(f"CoinGecko fetch failed for {query}: {e}")

    # 2. Binance API Fallback
    try:
        # 嘗試構建 Binance Symbol
        # 主要邏輯：轉成大寫 + USDT
        # 如果輸入是 'bitcoin'，我們要先試著轉回 ticker 'BTC'
        
        # 反向映射: valid IDs to Tickers
        ID_TO_TICKER = {v: k for k, v in TICKER_MAP.items()}
        
        ticker = query
        if query in ID_TO_TICKER: 
            ticker = ID_TO_TICKER[query]
            
        # 防止過長的字串直接當 ticker (Binance 通常是 3-5 碼)
        if len(ticker) <= 5:    
            symbol = f"{ticker.upper()}USDT"
            
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'source': 'Binance',
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent'])
                }
    except Exception as e:
        logger.warning(f"Binance fetch failed for {query}: {e}")
        
    return None


def handle_start(chat_id, user_id):
    """處理 /start 指令"""
    # 初始化用戶資料
    db.init_user(user_id)
    
    welcome = f"""
🤖 <b>歡迎使用智能加密貨幣投資顧問</b>

我可以幫您：
✅ 查詢即時價格與市場排名
✅ 獲取最新加密貨幣新聞
✅ AI 新聞情緒分析與走勢預測
✅ 技術分析與交易建議
✅ 設定價格提醒通知

<b>快速開始：</b>
1. /price BTC - 查詢比特幣價格
2. /trend - AI 分析市場趨勢
3. /news - 查看最新新聞
4. /analyze ETH - 技術分析

輸入 /help 查看完整功能列表
"""
    send_message(chat_id, welcome)


def handle_help(chat_id):
    """處理 /help 指令"""
    help_text = """
📖 <b>智能加密貨幣投資顧問 - 指令列表</b>

<b>🚀 基礎指令</b>
/start - 開始使用 Bot
/help - 顯示此說明

<b>📊 市場資訊</b>
/price [幣種] - 查詢即時價格
/top - 市值排名前10名
/news - 最新加密貨幣新聞

<b>🤖 AI 分析工具</b>
/trend - AI 市場趨勢預測（基於新聞情緒分析）
/trend [幣種] - 分析特定幣種趨勢
/analyze [幣種] - 技術指標分析與交易建議

<b>🔔 價格提醒</b>
/alert [幣種] [目標價] [high/low] - 設定價格提醒
/myalerts - 查看所有提醒
/del_alert [ID] - 刪除提醒

<b>📝 使用範例：</b>
• /price BTC
• /top
• /trend - 整體市場趨勢
• /trend ETH - 以太坊趨勢分析
• /news
• /analyze BTC
• /alert BTC 50000 high
"""
    send_message(chat_id, help_text)


def handle_news(chat_id, lang='zh'):
    """處理新聞查詢"""
    feeds = NEWS_FEEDS.get(lang, NEWS_FEEDS['zh'])
    news_items = []
    
    try:
        def fetch_feed(url):
            return feedparser.parse(url)

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(fetch_feed, feeds)
            
            for feed in results:
                if feed.entries:
                    for entry in feed.entries[:3]:  # 每個源取前3條
                        news_items.append({
                            'title': entry.title,
                            'link': entry.link,
                            'published': entry.get('published', 'N/A')
                        })
        
        # 按發布時間排序（如果有的話）
        # 簡單起見，直接取前 5 條
        news_items = news_items[:5]
        
        if not news_items:
            send_message(chat_id, "⚠️ 暫時沒有最新新聞")
            return
            
        message = "📰 <b>最新加密貨幣新聞</b>\n\n"
        for item in news_items:
            message += f"🔹 <a href='{item['link']}'>{item['title']}</a>\n\n"
            
        send_message(chat_id, message)
        
    except Exception as e:
        logger.error(f"獲取新聞失敗: {e}")
        send_message(chat_id, "❌ 獲取新聞失敗，請稍後再試")


def analyze_news_sentiment(news_items):
    """分析新聞情緒並預測走勢"""
    # 關鍵字情緒分析
    positive_keywords = ['surge', 'rally', 'bullish', 'growth', 'adoption', 'breakthrough', 
                        '上漲', '看漲', '突破', '增長', '採用', '利好', '暴漲', '飆升']
    negative_keywords = ['crash', 'drop', 'bearish', 'decline', 'ban', 'hack', 'scam',
                        '下跌', '看跌', '暴跌', '禁令', '駭客', '騙局', '崩盤']
    
    sentiment_score = 0
    analyzed_news = []
    
    for item in news_items:
        title_lower = item['title'].lower()
        item_sentiment = 0
        
        # 計算單條新聞情緒
        for keyword in positive_keywords:
            if keyword.lower() in title_lower:
                item_sentiment += 1
        for keyword in negative_keywords:
            if keyword.lower() in title_lower:
                item_sentiment -= 1
        
        sentiment_score += item_sentiment
        
        # 判斷新聞傾向
        if item_sentiment > 0:
            sentiment_label = "📈 看漲"
        elif item_sentiment < 0:
            sentiment_label = "📉 看跌"
        else:
            sentiment_label = "📊 中性"
        
        analyzed_news.append({
            'title': item['title'],
            'link': item['link'],
            'sentiment': sentiment_label,
            'score': item_sentiment
        })
    
    # 整體趨勢預測
    if sentiment_score > 2:
        overall_trend = "🚀 強烈看漲"
        recommendation = "市場情緒積極，可考慮逢低進場"
    elif sentiment_score > 0:
        overall_trend = "📈 溫和看漲"
        recommendation = "市場偏向樂觀，謹慎樂觀"
    elif sentiment_score < -2:
        overall_trend = "🔻 強烈看跌"
        recommendation = "市場情緒悲觀，建議觀望或減倉"
    elif sentiment_score < 0:
        overall_trend = "📉 溫和看跌"
        recommendation = "市場偏向悲觀，謹慎操作"
    else:
        overall_trend = "⚖️ 市場中性"
        recommendation = "市場觀望氣氛濃厚，等待明確信號"
    
    return {
        'overall_trend': overall_trend,
        'sentiment_score': sentiment_score,
        'recommendation': recommendation,
        'analyzed_news': analyzed_news
    }


def handle_trend(chat_id, crypto=None):
    """處理趨勢預測指令 - 基於新聞分析"""
    try:
        # 獲取新聞
        feeds = NEWS_FEEDS.get('zh', NEWS_FEEDS['zh'])
        news_items = []
        
        def fetch_feed(url):
            return feedparser.parse(url)

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(fetch_feed, feeds)
            
            for feed in results:
                if feed.entries:
                    for entry in feed.entries[:5]:  # 每個源取前5條
                        # 如果指定幣種，過濾相關新聞
                        if crypto:
                            if crypto.upper() in entry.title.upper():
                                news_items.append({
                                    'title': entry.title,
                                    'link': entry.link,
                                    'published': entry.get('published', 'N/A')
                                })
                        else:
                            news_items.append({
                                'title': entry.title,
                                'link': entry.link,
                                'published': entry.get('published', 'N/A')
                            })
        
        if not news_items:
            if crypto:
                send_message(chat_id, f"⚠️ 未找到關於 {crypto.upper()} 的相關新聞")
            else:
                send_message(chat_id, "⚠️ 暫時沒有最新新聞")
            return
        
        # 分析新聞情緒
        analysis = analyze_news_sentiment(news_items[:10])
        
        # 構建回覆訊息
        if crypto:
            message = f"📊 <b>{crypto.upper()} 市場趨勢分析</b>\n\n"
        else:
            message = "📊 <b>加密貨幣市場趨勢分析</b>\n\n"
        
        message += f"<b>整體趨勢：</b>{analysis['overall_trend']}\n"
        message += f"<b>情緒指數：</b>{analysis['sentiment_score']}\n"
        message += f"<b>操作建議：</b>{analysis['recommendation']}\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        message += "📰 <b>相關新聞分析：</b>\n\n"
        
        for idx, item in enumerate(analysis['analyzed_news'][:5], 1):
            message += f"{idx}. {item['sentiment']}\n"
            message += f"<a href='{item['link']}'>{item['title'][:80]}</a>\n\n"
        
        message += "\n💡 <i>* 本分析基於新聞標題關鍵字，僅供參考</i>"
        
        send_message(chat_id, message)
        
    except Exception as e:
        logger.error(f"趨勢分析失敗: {e}")
        send_message(chat_id, "❌ 趨勢分析失敗，請稍後再試")


def get_allocation_suggestion(risk_level):
    """根據風險等級給出配置建議"""
    suggestions = {
        '保守型': "• 70% 穩定幣\n• 20% BTC/ETH\n• 10% 其他主流幣",
        '穩健型': "• 50% BTC/ETH\n• 30% 主流幣\n• 20% 潛力幣",
        '積極型': "• 40% BTC/ETH\n• 30% 主流幣\n• 30% 潛力幣",
        '激進型': "• 30% BTC/ETH\n• 30% 主流幣\n• 40% 高風險/高潛力幣"
    }
    return suggestions.get(risk_level, "尚未評估")


def handle_analyze(chat_id, user_id, crypto):
    """處理交易策略分析"""
    # 初始化用戶
    db.init_user(user_id)
    
    # 獲取風險配置
    if not profile:
        send_message(chat_id, "❌ 請先完成風險評估 /risk_profile")
        return
    
    risk_level = profile['risk_level']
    
    # 獲取價格數據
    price_data = fetch_crypto_price_multi_source(crypto.lower())
    if not price_data:
        send_message(chat_id, f"❌ 無法獲取 {crypto} 的價格數據")
        return
    
    # 生成策略建議
    strategy = trading_strategy.generate_strategy(
        crypto=crypto,
        price=price_data['price'],
        change_24h=price_data['change_24h'],
        risk_level=risk_level
    )
    
    send_message(chat_id, strategy)


def handle_price(chat_id, crypto):
    """處理價格查詢"""
    price_data = fetch_crypto_price_multi_source(crypto.lower())
    
    if not price_data:
        send_message(chat_id, f"❌ 無法獲取 {crypto} 的價格")
        return
    
    change_emoji = "🟢" if price_data['change_24h'] >= 0 else "🔴"
    
    message = f"""
💰 <b>{crypto.upper()} 價格</b>

當前價格: ${price_data['price']:,.2f}
24小時變化: {change_emoji} {price_data['change_24h']:+.2f}%

數據來源: {price_data['source']}
"""
    send_message(chat_id, message)


def handle_top(chat_id):
    """顯示市值前10名"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                coins = response.json()
                
                message = "🏆 <b>市值前10名加密貨幣</b>\n\n"
                
                for i, coin in enumerate(coins, 1):
                    name = coin['name']
                    symbol = coin['symbol'].upper()
                    price = coin['current_price']
                    change = coin['price_change_percentage_24h']
                    change_emoji = "🟢" if change >= 0 else "🔴"
                    
                    message += f"{i}. <b>{name}</b> ({symbol})\n"
                    message += f"   ${price:,.2f} {change_emoji} {change:+.2f}%\n\n"
                
                send_message(chat_id, message)
                return
            else:
                logger.warning(f"CoinGecko API failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"CoinGecko connection failed: {e}")
            
        # Fallback to Binance/Hardcoded list if CoinGecko fails
        handle_top_fallback(chat_id)
            
    except Exception as e:
        logger.error(f"獲取Top 10失敗: {e}")
        send_message(chat_id, "❌ 查詢失敗，請稍後再試")

def handle_top_fallback(chat_id):
    """CoinGecko 失敗時的備用方案 (使用 Binance 查詢主要幣種)"""
    top_coins = [
        ('BTC', 'Bitcoin'), ('ETH', 'Ethereum'), ('BNB', 'BNB'), 
        ('SOL', 'Solana'), ('XRP', 'XRP'), ('DOGE', 'Dogecoin'),
        ('ADA', 'Cardano'), ('AVAX', 'Avalanche'), ('TRX', 'TRON'), ('DOT', 'Polkadot')
    ]
    
    message = "🏆 <b>市場主要加密貨幣 (Fallback)</b>\n\n"
    
    rank = 1
    for symbol, name in top_coins:
        price_info = fetch_crypto_price_multi_source(symbol)
        if price_info:
            price = price_info['price']
            change = price_info['change_24h']
            change_emoji = "🟢" if change >= 0 else "🔴"
            
            message += f"{rank}. <b>{name}</b> ({symbol})\n"
            message += f"   ${price:,.2f} {change_emoji} {change:+.2f}%\n\n"
            rank += 1
            
    send_message(chat_id, message)


def handle_alert(chat_id, user_id, parts):
    """處理 /alert 指令"""
    if len(parts) < 3:
        send_message(chat_id, "❌ 格式錯誤\n\n正確格式: /alert [幣種] [目標價]\n範例: /alert BTC 50000")
        return
    
    symbol = parts[1].upper()
    try:
        target_price = float(parts[2])
    except ValueError:
        send_message(chat_id, "❌ 目標價必須是數字")
        return
    
    # 獲取當前價格以判斷是漲破還是跌破
    price_data = fetch_crypto_price_multi_source(symbol.lower())
    if not price_data:
        send_message(chat_id, f"❌ 無法獲取 {symbol} 的當前價格，無法設定提醒")
        return
    
    current_price = price_data['price']
    
    if target_price > current_price:
        condition = 'above'
        condition_text = '漲破'
    else:
        condition = 'below'
        condition_text = '跌破'
    
    # 儲存到數據庫
    # alert_type='price', alert_condition=condition, threshold_value=target_price
    watchlist_id = db.add_watchlist(user_id, symbol, 'price', condition, target_price)
    
    if watchlist_id:
        send_message(chat_id, f"✅ 已設定提醒 (ID: {watchlist_id})\n\n當 {symbol} {condition_text} ${target_price:,.2f} 時通知您")
    else:
        send_message(chat_id, "❌ 設定失敗，請稍後再試")


def handle_my_alerts(chat_id, user_id):
    """處理 /myalerts 指令"""
    alerts = db.get_active_watchlist(user_id)
    
    if not alerts:
        send_message(chat_id, "🔕 您目前沒有設定任何提醒")
        return
    
    message = "🔔 <b>您的價格提醒</b>\n\n"
    
    for alert in alerts:
        symbol = alert['symbol']
        condition = alert['alert_condition']
        target = alert['threshold_value']
        alert_id = alert['watchlist_id']
        
        condition_text = "漲破" if condition == 'above' else "跌破"
        
        message += f"ID: {alert_id} | <b>{symbol}</b> {condition_text} ${target:,.2f}\n"
    
    message += "\n🗑 使用 /del_alert [ID] 刪除提醒"
    send_message(chat_id, message)


def handle_del_alert(chat_id, user_id, parts):
    """處理 /del_alert 指令"""
    if len(parts) < 2:
        send_message(chat_id, "❌ 請指定要刪除的提醒 ID\n範例: /del_alert 5")
        return
    
    try:
        alert_id = int(parts[1])
    except ValueError:
        send_message(chat_id, "❌ ID 必須是數字")
        return
    
    success = db.delete_watchlist_item(user_id, alert_id)
    
    if success:
        send_message(chat_id, f"✅ 已刪除提醒 (ID: {alert_id})")
    else:
        send_message(chat_id, f"❌ 刪除失敗，找不到 ID 為 {alert_id} 的提醒或不屬於您")


@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 Telegram Webhook"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            
            # 處理指令
            if text.startswith('/'):
                parts = text.split()
                command = parts[0].lower()
                
                if command == '/start':
                    handle_start(chat_id, user_id)
                elif command == '/help':
                    handle_help(chat_id)
                elif command == '/analyze':
                    if len(parts) > 1:
                        handle_analyze(chat_id, user_id, parts[1])
                    else:
                        send_message(chat_id, "請指定幣種，例如: /analyze BTC")
                elif command == '/price':
                    if len(parts) > 1:
                        handle_price(chat_id, parts[1])
                    else:
                        send_message(chat_id, "請指定幣種，例如: /price BTC")
                elif command == '/top':
                    handle_top(chat_id)
                elif command == '/news':
                    handle_news(chat_id)
                elif command == '/trend':
                    if len(parts) > 1:
                        handle_trend(chat_id, parts[1])
                    else:
                        handle_trend(chat_id)
                elif command == '/alert':
                    handle_alert(chat_id, user_id, parts)
                elif command == '/myalerts':
                    handle_my_alerts(chat_id, user_id)
                elif command == '/del_alert':
                    handle_del_alert(chat_id, user_id, parts)
                else:
                    send_message(chat_id, "❌ 未知指令\n\n輸入 /help 查看可用指令")
            
            # 處理問卷回答
                result = risk_assessment.process_answer(user_id, text)
                
                if result['status'] == 'completed':
                    # 儲存風險評估結果到資料庫
                    if result.get('result'):
                        res = result['result']
                        db.save_risk_profile(
                            user_id=user_id,
                            risk_score=res['risk_score'],
                            answers=res.get('answers', [])
                        )
                        logger.info(f"用戶 {user_id} 完成風險評估，等級: {res['risk_level']}")
                    
                    send_message(chat_id, result['message'])
                elif result['status'] == 'continue':
                    send_message(chat_id, result['message'])
                elif result['status'] == 'error':
                    send_message(chat_id, f"❌ {result['message']}")
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康檢查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
