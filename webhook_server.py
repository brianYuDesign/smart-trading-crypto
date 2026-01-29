"""
Telegram Bot Webhook Server - 清理版
只保留市場資訊查詢功能（價格、市場總覽、新聞）
移除所有假資料和交易功能
"""
from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime
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
COINDESK_RSS = 'https://www.coindesk.com/arc/outboundfeeds/rss/'

# 線程池
executor = ThreadPoolExecutor(max_workers=3)

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

def handle_start(chat_id):
    """處理 /start 指令"""
    message = """👋 <b>歡迎使用加密貨幣資訊 Bot！</b>

📊 <b>可用功能：</b>

💰 <b>/price</b> - 查詢加密貨幣價格
   查看 BTC、ETH、BNB 實時價格

📈 <b>/market</b> - 市場總覽
   查看加密貨幣市場總市值和主導地位

📰 <b>/news</b> - 最新新聞
   獲取最新的加密貨幣新聞

❓ <b>/help</b> - 幫助資訊
   查看詳細使用說明

---
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

📈 <b>/market</b>
   查看加密貨幣市場總市值
   查看 24 小時交易量
   查看 BTC、ETH 市場主導地位

📰 <b>/news</b>
   獲取最新的加密貨幣新聞
   來源：CoinDesk

---
💡 <b>使用技巧：</b>
• 點擊輸入框的 / 按鈕查看所有指令
• 使用內嵌按鈕快速操作
• 數據每分鐘更新一次

❓ 如有問題，請聯繫管理員
"""
    send_message(chat_id, message)

def handle_price(chat_id):
    """處理 /price 指令 - 查詢加密貨幣價格"""
    try:
        # 從 CoinGecko API 獲取價格
        url = f'{COINGECKO_BASE}/simple/price'
        params = {
            'ids': 'bitcoin,ethereum,binancecoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data:
            send_message(chat_id, "❌ 無法獲取價格數據，請稍後再試")
            return

        # 格式化訊息
        btc_price = data.get('bitcoin', {}).get('usd', 0)
        btc_change = data.get('bitcoin', {}).get('usd_24h_change', 0)

        eth_price = data.get('ethereum', {}).get('usd', 0)
        eth_change = data.get('ethereum', {}).get('usd_24h_change', 0)

        bnb_price = data.get('binancecoin', {}).get('usd', 0)
        bnb_change = data.get('binancecoin', {}).get('usd_24h_change', 0)

        message = f"""💰 <b>當前價格</b>

<b>BTC:</b> ${btc_price:,.2f} {'📈' if btc_change > 0 else '📉'} {btc_change:+.2f}%
<b>ETH:</b> ${eth_price:,.2f} {'📈' if eth_change > 0 else '📉'} {eth_change:+.2f}%
<b>BNB:</b> ${bnb_price:,.2f} {'📈' if bnb_change > 0 else '📉'} {bnb_change:+.2f}%

⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"價格查詢錯誤: {e}")
        send_message(chat_id, "❌ 查詢價格時發生錯誤，請稍後再試")

def handle_market(chat_id):
    """處理 /market 指令 - 查詢市場總覽"""
    try:
        # 從 CoinGecko API 獲取市場數據
        url = f'{COINGECKO_BASE}/global'

        response = requests.get(url, timeout=10)
        data = response.json()

        if not data or 'data' not in data:
            send_message(chat_id, "❌ 無法獲取市場數據，請稍後再試")
            return

        market_data = data['data']

        # 格式化數據
        total_market_cap = market_data.get('total_market_cap', {}).get('usd', 0)
        total_volume = market_data.get('total_volume', {}).get('usd', 0)
        btc_dominance = market_data.get('market_cap_percentage', {}).get('btc', 0)
        eth_dominance = market_data.get('market_cap_percentage', {}).get('eth', 0)

        message = f"""📊 <b>加密貨幣市場總覽</b>

💎 <b>總市值:</b> ${total_market_cap/1e12:.2f}T
📈 <b>24小時交易量:</b> ${total_volume/1e9:.2f}B

🏆 <b>市場主導地位:</b>
• BTC: {btc_dominance:.2f}%
• ETH: {eth_dominance:.2f}%

⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"市場查詢錯誤: {e}")
        send_message(chat_id, "❌ 查詢市場數據時發生錯誤，請稍後再試")

def handle_news(chat_id):
    """處理 /news 指令 - 獲取最新新聞"""
    try:
        # 從 CoinDesk RSS 獲取新聞
        feed = feedparser.parse(COINDESK_RSS)

        if not feed.entries:
            send_message(chat_id, "❌ 無法獲取新聞，請稍後再試")
            return

        # 格式化前 5 則新聞
        message = "📰 <b>最新加密貨幣新聞</b>\n\n"

        for i, entry in enumerate(feed.entries[:5], 1):
            title = entry.title
            link = entry.link
            message += f"{i}. <a href='{link}'>{title}</a>\n\n"

        message += f"⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        send_message(chat_id, message)

    except Exception as e:
        logger.error(f"新聞獲取錯誤: {e}")
        send_message(chat_id, "❌ 獲取新聞時發生錯誤，請稍後再試")

def handle_callback_query(callback_query):
    """處理內嵌按鈕點擊"""
    chat_id = callback_query['message']['chat']['id']
    data = callback_query['data']

    # 回應按鈕點擊（移除載入動畫）
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'
        requests.post(url, json={'callback_query_id': callback_query['id']}, timeout=5)
    except Exception as e:
        logger.error(f"回應 callback 錯誤: {e}")

    # 根據按鈕執行對應功能
    if data == 'price':
        handle_price(chat_id)
    elif data == 'market':
        handle_market(chat_id)
    elif data == 'news':
        handle_news(chat_id)
    elif data == 'help':
        handle_help(chat_id)

def process_update(update):
    """處理更新（在線程中執行）"""
    try:
        # 處理內嵌按鈕點擊
        if 'callback_query' in update:
            handle_callback_query(update['callback_query'])
            return

        # 處理訊息
        if 'message' not in update:
            return

        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')

        # 指令路由表
        commands = {
            '/start': handle_start,
            '/help': handle_help,
            '/price': handle_price,
            '/market': handle_market,
            '/news': handle_news,
        }

        # 執行對應指令
        handler = commands.get(text)
        if handler:
            handler(chat_id)
        else:
            send_message(chat_id, "❓ 未知指令。使用 /help 查看可用指令。")

    except Exception as e:
        logger.error(f"處理更新錯誤: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook 端點"""
    try:
        update = request.get_json()

        # 在線程池中非同步處理（避免阻塞 webhook）
        executor.submit(process_update, update)

        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"Webhook 錯誤: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    try:
        # 測試 CoinGecko API
        response = requests.get(f'{COINGECKO_BASE}/ping', timeout=5)
        api_status = 'ok' if response.status_code == 200 else 'error'

        return jsonify({
            'status': 'healthy',
            'api_status': api_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def index():
    """首頁"""
    return jsonify({
        'service': 'Telegram Crypto Info Bot',
        'status': 'running',
        'features': ['price', 'market', 'news'],
        'version': '2.0.0-clean'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
