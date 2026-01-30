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
from .risk_assessment import risk_assessment
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


def fetch_crypto_price_multi_source(crypto_id):
    """多重來源獲取價格（保留原本邏輯）"""
    # 1. CoinGecko
    try:
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': crypto_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if crypto_id in data:
                return {
                    'source': 'CoinGecko',
                    'price': data[crypto_id]['usd'],
                    'change_24h': data[crypto_id].get('usd_24h_change', 0)
                }
    except Exception as e:
        logger.warning(f"CoinGecko API 失敗: {e}")
    
    # 2. Binance Fallback
    try:
        symbol_map = {
            'bitcoin': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'solana': 'SOLUSDT',
            'cardano': 'ADAUSDT',
            'dogecoin': 'DOGEUSDT'
        }
        
        if crypto_id in symbol_map:
            symbol = symbol_map[crypto_id]
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'source': 'Binance',
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent'])
                }
    except Exception as e:
        logger.warning(f"Binance API 失敗: {e}")
    
    return None


def handle_start(chat_id, user_id):
    """處理 /start 指令"""
    # 初始化用戶資料
    db.init_user(user_id)
    
    welcome = f"""
🤖 <b>歡迎使用智能加密貨幣投資顧問</b>

我可以幫您：
✅ 評估風險屬性並提供個性化建議
✅ 分析進場時機與交易策略
✅ 管理持倉並追蹤績效
✅ 查詢即時價格與市場動態

<b>快速開始：</b>
1. /risk_profile - 完成風險評估問卷
2. /analyze BTC - 獲取交易建議
3. /positions - 管理您的持倉

輸入 /help 查看完整功能列表
"""
    send_message(chat_id, welcome)


def handle_help(chat_id):
    """處理 /help 指令"""
    help_text = """
📖 <b>可用指令：</b>

<b>🎯 風險評估</b>
/risk_profile - 風險屬性評估問卷
/my_profile - 查看我的風險屬性

<b>📊 交易分析</b>
/analyze [幣種] - 分析進場時機
/positions - 查看我的持倉
/add_position [幣種] [數量] [成本] - 新增持倉

<b>📰 即時新聞</b>
/news - 查看最新加密貨幣新聞
/price [幣種] - 查詢即時價格
/top - 市值前10名加密貨幣

<b>🔔 價格提醒</b>
/alert [幣種] [目標價] - 設定價格提醒
/myalerts - 查看我的提醒列表
/del_alert [ID] - 刪除指定提醒

<b>範例：</b>
• /analyze BTC
• /price ETH
• /add_position BTC 0.5 45000
• /alert ETH 3000
• /del_alert 1 (刪除ID為1的提醒)
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


def handle_risk_profile(chat_id, user_id):
    """處理風險評估問卷"""
    question = risk_assessment.start_assessment(user_id)
    send_message(chat_id, question)


def handle_my_profile(chat_id, user_id):
    """顯示用戶風險屬性"""
    user = db.get_user(user_id)
    if not user or not user.get('risk_level'):
        send_message(chat_id, "❌ 您尚未完成風險評估\n\n請使用 /risk_profile 開始評估")
        return
    
    profile_text = f"""
👤 <b>您的風險屬性</b>

風險等級: {user['risk_level']}
評估時間: {user.get('assessed_at', 'N/A')}

<b>建議配置：</b>
{get_allocation_suggestion(user['risk_level'])}

💡 使用 /analyze [幣種] 獲取個性化交易建議
"""
    send_message(chat_id, profile_text)


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
    user = db.get_user(user_id)
    if not user or not user.get('risk_level'):
        send_message(chat_id, "❌ 請先完成風險評估 /risk_profile")
        return
    
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
        risk_level=user['risk_level']
    )
    
    send_message(chat_id, strategy)


def handle_positions(chat_id, user_id):
    """顯示持倉列表"""
    positions = db.get_positions(user_id)
    
    if not positions:
        send_message(chat_id, "📊 您目前沒有持倉記錄\n\n使用 /add_position [幣種] [數量] [成本] 新增持倉")
        return
    
    text = "📊 <b>您的持倉</b>\n\n"
    total_value = 0
    total_cost = 0
    
    for pos in positions:
        crypto = pos['symbol']
        amount = pos['amount']
        avg_cost = pos['avg_cost']
        
        # 獲取當前價格
        price_data = fetch_crypto_price_multi_source(crypto.lower())
        current_price = price_data['price'] if price_data else avg_cost
        
        position_value = amount * current_price
        position_cost = amount * avg_cost
        profit = position_value - position_cost
        profit_pct = (profit / position_cost * 100) if position_cost > 0 else 0
        
        total_value += position_value
        total_cost += position_cost
        
        profit_emoji = "🟢" if profit >= 0 else "🔴"
        
        text += f"""
{profit_emoji} <b>{crypto.upper()}</b>
持有: {amount:.4f}
成本: ${avg_cost:.2f}
現價: ${current_price:.2f}
盈虧: ${profit:.2f} ({profit_pct:+.2f}%)

"""
    
    total_profit = total_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    text += f"""
<b>總覽</b>
總成本: ${total_cost:.2f}
總市值: ${total_value:.2f}
總盈虧: ${total_profit:.2f} ({total_profit_pct:+.2f}%)
"""
    
    send_message(chat_id, text)


def handle_add_position(chat_id, user_id, parts):
    """新增持倉"""
    if len(parts) < 4:
        send_message(chat_id, "❌ 格式錯誤\n\n正確格式: /add_position [幣種] [數量] [成本]\n範例: /add_position BTC 0.5 45000")
        return
    
    crypto = parts[1].upper()
    try:
        amount = float(parts[2])
        avg_cost = float(parts[3])
    except ValueError:
        send_message(chat_id, "❌ 數量和成本必須是數字")
        return
    
    db.add_position(user_id, crypto, amount, avg_cost)
    send_message(chat_id, f"✅ 已新增持倉\n\n幣種: {crypto}\n數量: {amount}\n成本: ${avg_cost}\n\n使用 /positions 查看所有持倉")


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
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1
        }
        
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
        else:
            send_message(chat_id, "❌ 無法獲取市場數據")
    
    except Exception as e:
        logger.error(f"獲取Top 10失敗: {e}")
        send_message(chat_id, "❌ 查詢失敗，請稍後再試")


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
        alert_id = alert['id']
        
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
                elif command == '/risk_profile':
                    handle_risk_profile(chat_id, user_id)
                elif command == '/my_profile':
                    handle_my_profile(chat_id, user_id)
                elif command == '/analyze':
                    if len(parts) > 1:
                        handle_analyze(chat_id, user_id, parts[1])
                    else:
                        send_message(chat_id, "請指定幣種，例如: /analyze BTC")
                elif command == '/positions':
                    handle_positions(chat_id, user_id)
                elif command == '/add_position':
                    handle_add_position(chat_id, user_id, parts)
                elif command == '/price':
                    if len(parts) > 1:
                        handle_price(chat_id, parts[1])
                    else:
                        send_message(chat_id, "請指定幣種，例如: /price BTC")
                elif command == '/top':
                    handle_top(chat_id)
                elif command == '/news':
                    handle_news(chat_id)
                elif command == '/alert':
                    handle_alert(chat_id, user_id, parts)
                elif command == '/myalerts':
                    handle_my_alerts(chat_id, user_id)
                elif command == '/del_alert':
                    handle_del_alert(chat_id, user_id, parts)
                else:
                    send_message(chat_id, "❌ 未知指令\n\n輸入 /help 查看可用指令")
            
            # 處理問卷回答
            elif risk_assessment.is_in_assessment(user_id):
                result = risk_assessment.process_answer(user_id, text)
                
                if result['status'] == 'completed':
                    send_message(chat_id, result['message'])
                    # 也可以顯示結果摘要
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
