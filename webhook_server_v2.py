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
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()
import logging
from datetime import datetime
import pytz
import feedparser
from concurrent.futures import ThreadPoolExecutor

# 導入新模組
from database_manager import db
from risk_assessment import risk_assessment
from trading_strategy import trading_strategy
from market_monitor import init_monitor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境變數
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')

# 初始化市場監控
monitor = init_monitor(TELEGRAM_BOT_TOKEN)

# 用戶時區存儲（現在用資料庫）
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
    """多重來源獲取價格（保留原有邏輯）"""
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
            if crypto_id in data and data[crypto_id].get('usd', 0) > 0:
                return {
                    'price': data[crypto_id]['usd'],
                    'change_24h': data[crypto_id].get('usd_24h_change', 0),
                    'source': 'CoinGecko'
                }
    except Exception as e:
        logger.warning(f"CoinGecko 失敗: {e}")
    
    # 2. Binance
    try:
        symbol_map = {
            'bitcoin': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'binancecoin': 'BNBUSDT',
            'solana': 'SOLUSDT',
            'ripple': 'XRPUSDT'
        }
        
        if crypto_id in symbol_map:
            symbol = symbol_map[crypto_id]
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'source': 'Binance'
                }
    except Exception as e:
        logger.warning(f"Binance 失敗: {e}")
    
    # 3. CryptoCompare
    try:
        crypto_map = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH',
            'binancecoin': 'BNB',
            'solana': 'SOL',
            'ripple': 'XRP'
        }
        
        if crypto_id in crypto_map:
            symbol = crypto_map[crypto_id]
            url = f"https://min-api.cryptocompare.com/data/pricemultifull"
            params = {
                'fsyms': symbol,
                'tsyms': 'USD'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'RAW' in data and symbol in data['RAW']:
                    info = data['RAW'][symbol]['USD']
                    return {
                        'price': info['PRICE'],
                        'change_24h': info['CHANGEPCT24HOUR'],
                        'source': 'CryptoCompare'
                    }
    except Exception as e:
        logger.warning(f"CryptoCompare 失敗: {e}")
    
    return None


def fetch_crypto_news(language='zh', limit=5):
    """獲取加密貨幣新聞"""
    feeds = NEWS_FEEDS.get(language, NEWS_FEEDS['zh'])
    articles = []
    
    def fetch_feed(feed_url):
        try:
            feed = feedparser.parse(feed_url)
            return feed.entries[:limit]
        except:
            return []
    
    with ThreadPoolExecutor(max_workers=len(feeds)) as executor:
        results = executor.map(fetch_feed, feeds)
        for entries in results:
            articles.extend(entries)
    
    return articles[:limit]


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook 端點"""
    try:
        data = request.get_json()
        
        if 'message' not in data:
            return jsonify({'status': 'ignored'})
        
        message = data['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        # 更新或創建用戶
        db.create_or_update_user(
            user_id=user_id,
            username=message['from'].get('username'),
            first_name=message['from'].get('first_name'),
            last_name=message['from'].get('last_name')
        )
        
        if 'text' not in message:
            return jsonify({'status': 'ok'})
        
        text = message['text'].strip()
        
        # ==================== 新功能：風險評估 ====================
        
        if text == '/start':
            welcome_msg = "👋 歡迎使用智能加密貨幣投資助手 V2！\n\n"
            welcome_msg += "🆕 新功能：\n"
            welcome_msg += "• /risk_profile - 風險屬性評估\n"
            welcome_msg += "• /my_profile - 查看我的風險屬性\n"
            welcome_msg += "• /analyze - 分析進場時機\n"
            welcome_msg += "• /positions - 我的持倉\n"
            welcome_msg += "• /add_position - 新增持倉\n\n"
            welcome_msg += "💡 原有功能：\n"
            welcome_msg += "• /price <幣種> - 查詢價格\n"
            welcome_msg += "• /news - 最新新聞\n"
            welcome_msg += "• /timezone - 設定時區\n"
            send_message(chat_id, welcome_msg)
        
        elif text == '/risk_profile':
            # 開始風險評估
            question = risk_assessment.start_assessment(user_id)
            send_message(chat_id, question)
        
        elif text == '/my_profile':
            # 查看當前風險屬性
            summary = risk_assessment.get_user_risk_summary(user_id)
            if summary:
                send_message(chat_id, summary)
            else:
                send_message(chat_id, "您還沒有完成風險評估。請使用 /risk_profile 開始評估。")
        
        elif text.startswith('/analyze'):
            # 分析進場時機
            parts = text.split()
            symbol = parts[1] if len(parts) > 1 else 'BTC/USDT'
            
            # 獲取市場數據
            coin_id = 'bitcoin' if 'BTC' in symbol else 'ethereum'
            price_data = fetch_crypto_price_multi_source(coin_id)
            
            if not price_data:
                send_message(chat_id, "無法獲取市場數據，請稍後再試")
                return jsonify({'status': 'ok'})
            
            # 構建市場數據
            market_data = {
                'price': price_data['price'],
                'rsi': 50,  # 簡化版
                'volume_24h': 1000000,
                'avg_volume': 900000,
                'ma_50': price_data['price'] * 0.98,
                'ma_200': price_data['price'] * 0.95,
                'news_sentiment': 0.6,
                'price_change_24h': price_data['change_24h']
            }
            
            # 分析進場信號
            signal = trading_strategy.analyze_entry_signal(user_id, symbol, market_data)
            
            msg = f"📊 {symbol} 進場分析\n\n"
            msg += f"當前價格: ${price_data['price']:,.2f}\n"
            msg += f"24h 變化: {price_data['change_24h']:+.2f}%\n\n"
            msg += signal['recommendation'] + "\n\n"
            msg += "📌 分析依據:\n"
            for reason in signal['reasons'][:5]:
                msg += f"{reason}\n"
            
            send_message(chat_id, msg)
        
        elif text == '/positions':
            # 查看持倉
            positions = db.get_open_positions(user_id)
            
            if not positions:
                send_message(chat_id, "您目前沒有持倉\n\n使用 /add_position 新增持倉")
                return jsonify({'status': 'ok'})
            
            msg = "💼 我的持倉\n\n"
            for pos in positions:
                msg += f"🪙 {pos['symbol']}\n"
                msg += f"  進場價: ${pos['entry_price']:,.2f}\n"
                msg += f"  數量: {pos['quantity']}\n"
                msg += f"  時間: {pos['entry_time']}\n\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith('/add_position'):
            # 新增持倉（簡化版）
            try:
                parts = text.split()
                if len(parts) < 4:
                    send_message(chat_id, "格式：/add_position <幣種> <價格> <數量>\n範例：/add_position BTC/USDT 50000 0.1")
                    return jsonify({'status': 'ok'})
                
                symbol = parts[1]
                price = float(parts[2])
                quantity = float(parts[3])
                
                position_id = db.add_position(user_id, symbol, price, quantity)
                
                if position_id:
                    send_message(chat_id, f"✅ 持倉已新增\n\n幣種: {symbol}\n價格: ${price:,.2f}\n數量: {quantity}")
                else:
                    send_message(chat_id, "❌ 新增失敗，請稍後再試")
            
            except ValueError:
                send_message(chat_id, "❌ 價格和數量必須是數字")
        
        # ==================== 原有功能（保留） ====================
        
        elif text.startswith('/price'):
            parts = text.split()
            crypto_id = parts[1].lower() if len(parts) > 1 else 'bitcoin'
            
            price_data = fetch_crypto_price_multi_source(crypto_id)
            
            if price_data:
                timezone = get_user_timezone(user_id)
                user_tz = pytz.timezone(timezone)
                current_time = datetime.now(user_tz).strftime('%Y-%m-%d %H:%M:%S')
                
                msg = f"💰 <b>{crypto_id.upper()}</b> 價格資訊\n\n"
                msg += f"💵 當前價格: <b>${price_data['price']:,.2f}</b>\n"
                msg += f"📊 24小時變化: <b>{price_data['change_24h']:+.2f}%</b>\n"
                msg += f"📡 數據來源: {price_data['source']}\n"
                msg += f"🕐 更新時間: {current_time}\n"
                
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "❌ 無法獲取價格資訊")
        
        elif text == '/news':
            send_message(chat_id, "📰 正在獲取最新新聞...")
            
            articles_zh = fetch_crypto_news('zh', 3)
            articles_en = fetch_crypto_news('en', 3)
            
            msg = "📰 <b>加密貨幣最新新聞</b>\n\n"
            
            if articles_zh:
                msg += "🇹🇼 <b>中文新聞:</b>\n"
                for i, article in enumerate(articles_zh, 1):
                    title = article.get('title', 'No title')
                    link = article.get('link', '#')
                    msg += f"{i}. <a href='{link}'>{title}</a>\n"
                msg += "\n"
            
            if articles_en:
                msg += "🇺🇸 <b>英文新聞:</b>\n"
                for i, article in enumerate(articles_en, 1):
                    title = article.get('title', 'No title')
                    link = article.get('link', '#')
                    msg += f"{i}. <a href='{link}'>{title}</a>\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith('/timezone'):
            parts = text.split()
            if len(parts) == 1:
                current_tz = get_user_timezone(user_id)
                msg = f"您當前的時區: {current_tz}\n\n"
                msg += "更改時區: /timezone <時區>\n"
                msg += "範例: /timezone America/New_York"
                send_message(chat_id, msg)
            else:
                new_timezone = parts[1]
                try:
                    pytz.timezone(new_timezone)
                    db.update_user_timezone(user_id, new_timezone)
                    send_message(chat_id, f"✅ 時區已更新為: {new_timezone}")
                except:
                    send_message(chat_id, "❌ 無效的時區格式")
        
        elif text == '/help':
            help_msg = "🤖 <b>指令列表</b>\n\n"
            help_msg += "<b>🆕 風險管理：</b>\n"
            help_msg += "/risk_profile - 風險屬性評估\n"
            help_msg += "/my_profile - 查看風險屬性\n"
            help_msg += "/analyze [幣種] - 分析進場時機\n"
            help_msg += "/positions - 查看持倉\n"
            help_msg += "/add_position - 新增持倉\n\n"
            help_msg += "<b>💰 行情查詢：</b>\n"
            help_msg += "/price [幣種] - 查詢價格\n"
            help_msg += "/news - 最新新聞\n\n"
            help_msg += "<b>⚙️ 設定：</b>\n"
            help_msg += "/timezone [時區] - 設定時區\n"
            send_message(chat_id, help_msg)
        
        # ==================== 風險評估問卷答案處理 ====================
        
        elif user_id in risk_assessment.user_sessions:
            # 正在進行風險評估
            result = risk_assessment.process_answer(user_id, text)
            
            if result['status'] == 'continue':
                send_message(chat_id, result['message'])
            elif result['status'] == 'completed':
                send_message(chat_id, result['message'])
                # 啟動主動監控
                send_message(chat_id, "\n✅ 已為您開啟智能監控服務\n系統將根據您的風險屬性主動提醒進退場時機")
            elif result['status'] == 'error':
                send_message(chat_id, result['message'])
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        logger.error(f"處理 webhook 錯誤: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'features': ['risk_assessment', 'trading_strategy', 'market_monitor']
    })


if __name__ == '__main__':
    # 初始化資料庫
    logger.info("初始化資料庫...")
    db.init_database()
    
    # 啟動市場監控
    logger.info("啟動市場監控...")
    monitor.start()
    
    # 啟動 Flask 服務器
    port = int(os.getenv('PORT', 5000))
    logger.info(f"啟動服務器於 port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
