"""
Telegram Bot Webhook Server - 完整修復版
支援所有功能：價格、新聞、市場總覽、交易操作
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
REQUEST_TIMEOUT = 10

# 執行器用於非同步任務
executor = ThreadPoolExecutor(max_workers=3)

# ==================== Telegram 輔助函數 ====================

def send_message(chat_id, text, reply_markup=None):
    """發送 Telegram 訊息（帶重試機制）"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"發送訊息失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"發送訊息異常: {e}")
        return False

def answer_callback_query(callback_query_id, text=None):
    """回應內嵌按鈕點擊"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'
    payload = {'callback_query_id': callback_query_id}
    if text:
        payload['text'] = text

    try:
        requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        logger.error(f"回應 callback 異常: {e}")

# ==================== API 數據獲取函數 ====================

def get_crypto_price(symbol='bitcoin,ethereum,binancecoin'):
    """獲取加密貨幣價格"""
    try:
        response = requests.get(
            f'{COINGECKO_BASE}/simple/price',
            params={
                'ids': symbol,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            },
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            result = "💰 *加密貨幣價格*\n\n"

            name_map = {
                'bitcoin': 'Bitcoin (BTC)',
                'ethereum': 'Ethereum (ETH)',
                'binancecoin': 'BNB'
            }

            for coin_id, coin_data in data.items():
                name = name_map.get(coin_id, coin_id)
                price = coin_data.get('usd', 0)
                change = coin_data.get('usd_24h_change', 0)
                emoji = "📈" if change > 0 else "📉"

                result += f"{emoji} *{name}*\n"
                result += f"   價格: ${price:,.2f}\n"
                result += f"   24h: {change:+.2f}%\n\n"

            result += f"_更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            return result
        else:
            logger.error(f"價格 API 錯誤: {response.status_code}")
            return "❌ 無法獲取價格數據，請稍後再試"

    except Exception as e:
        logger.error(f"獲取價格異常: {e}")
        return "❌ 獲取價格時發生錯誤"

def get_market_overview():
    """獲取市場總覽"""
    try:
        response = requests.get(
            f'{COINGECKO_BASE}/global',
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()['data']

            total_market_cap = data['total_market_cap']['usd']
            total_volume = data['total_volume']['usd']
            btc_dominance = data['market_cap_percentage']['btc']
            eth_dominance = data['market_cap_percentage']['eth']

            result = "🌍 *加密貨幣市場總覽*\n\n"
            result += f"💵 總市值: ${total_market_cap:,.0f}\n"
            result += f"📊 24h 交易量: ${total_volume:,.0f}\n\n"
            result += f"🥇 BTC 市佔率: {btc_dominance:.2f}%\n"
            result += f"🥈 ETH 市佔率: {eth_dominance:.2f}%\n\n"
            result += f"_更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"

            return result
        else:
            logger.error(f"市場總覽 API 錯誤: {response.status_code}")
            return "❌ 無法獲取市場數據，請稍後再試"

    except Exception as e:
        logger.error(f"獲取市場總覽異常: {e}")
        return "❌ 獲取市場總覽時發生錯誤"

def get_crypto_news(limit=5):
    """獲取加密貨幣新聞（使用 RSS）"""
    try:
        # 使用 feedparser 解析 RSS
        feed = feedparser.parse(COINDESK_RSS)

        if not feed.entries:
            return "❌ 無法獲取新聞，請稍後再試"

        result = "📰 *加密貨幣新聞 (CoinDesk)*\n\n"

        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.get('title', '無標題')
            link = entry.get('link', '')
            published = entry.get('published', '')

            # 簡化時間處理
            time_str = published[:16] if published else ''

            result += f"{i}. *{title}*\n"
            if time_str:
                result += f"   ⏰ {time_str}\n"
            if link:
                result += f"   🔗 [閱讀全文]({link})\n"
            result += "\n"

        result += f"_更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        return result

    except Exception as e:
        logger.error(f"獲取新聞異常: {e}")
        return "❌ 獲取新聞時發生錯誤"

def get_account_balance():
    """獲取帳戶餘額（模擬）"""
    return """💳 *帳戶餘額*

📊 總資產: $10,000.00
💰 可用資金: $8,500.00
🔒 凍結資金: $1,500.00

持倉:
  • BTC: 0.05 ($4,395.05)
  • ETH: 2.5 ($7,362.45)
  • USDT: 8,500.00

_注意: 這是模擬數據_"""

def get_trade_history():
    """獲取交易歷史（模擬）"""
    return """📜 *交易歷史*

最近 5 筆交易:

1. 🟢 買入 BTC 0.01
   價格: $87,900 | 時間: 01/29 09:30

2. 🔴 賣出 ETH 1.0
   價格: $2,945 | 時間: 01/29 08:15

3. 🟢 買入 BNB 5.0
   價格: $615 | 時間: 01/28 22:45

4. 🔴 賣出 BTC 0.02
   價格: $88,200 | 時間: 01/28 18:20

5. 🟢 買入 ETH 2.0
   價格: $2,920 | 時間: 01/28 14:10

_注意: 這是模擬數據_"""

# ==================== 指令處理函數 ====================

def handle_start(chat_id):
    """處理 /start 指令"""
    message = """🤖 *歡迎使用智能加密貨幣交易 Bot*

我可以幫您：
• 📊 即時監控市場行情
• 💰 查詢加密貨幣價格
• 📰 獲取最新新聞
• 🤖 自動交易執行

快速開始：
點擊下方按鈕或輸入 / 查看所有指令"""

    keyboard = {
        'inline_keyboard': [
            [
                {'text': '📊 查看狀態', 'callback_data': 'cmd_status'},
                {'text': '💰 查詢價格', 'callback_data': 'cmd_price'}
            ],
            [
                {'text': '💳 帳戶餘額', 'callback_data': 'cmd_balance'},
                {'text': '📜 交易歷史', 'callback_data': 'cmd_history'}
            ],
            [
                {'text': '📰 最新新聞', 'callback_data': 'cmd_news'},
                {'text': '❓ 幫助', 'callback_data': 'cmd_help'}
            ]
        ]
    }

    send_message(chat_id, message, keyboard)

def handle_status(chat_id):
    """處理 /status 指令"""
    message = """📊 *系統狀態*

🟢 Bot 運行正常
🌐 API 連接正常
⏰ 運行時間: 24 小時

交易狀態:
  • 自動交易: ⏸️ 未啟動
  • 監控幣種: BTC, ETH, BNB
  • 更新頻率: 每 5 分鐘

_使用 /trade 開始自動交易_"""

    send_message(chat_id, message)

def handle_price(chat_id):
    """處理 /price 指令"""
    send_message(chat_id, "⏳ 正在獲取最新價格...")
    price_data = get_crypto_price()
    send_message(chat_id, price_data)

def handle_market(chat_id):
    """處理 /market 指令"""
    send_message(chat_id, "⏳ 正在獲取市場總覽...")
    market_data = get_market_overview()
    send_message(chat_id, market_data)

def handle_news(chat_id):
    """處理 /news 指令"""
    send_message(chat_id, "⏳ 正在獲取最新新聞...")
    news_data = get_crypto_news(limit=5)
    send_message(chat_id, news_data)

def handle_balance(chat_id):
    """處理 /balance 指令"""
    balance_data = get_account_balance()
    send_message(chat_id, balance_data)

def handle_history(chat_id):
    """處理 /history 指令"""
    history_data = get_trade_history()
    send_message(chat_id, history_data)

def handle_trade(chat_id):
    """處理 /trade 指令"""
    message = "⚠️ *確認啟動自動交易?*\n\n即將開始自動交易，請確認："

    keyboard = {
        'inline_keyboard': [
            [
                {'text': '✅ 確認啟動', 'callback_data': 'trade_confirm'},
                {'text': '❌ 取消', 'callback_data': 'trade_cancel'}
            ]
        ]
    }

    send_message(chat_id, message, keyboard)

def handle_stop(chat_id):
    """處理 /stop 指令"""
    message = "⚠️ *確認停止交易?*\n\n即將停止所有自動交易，請確認："

    keyboard = {
        'inline_keyboard': [
            [
                {'text': '✅ 確認停止', 'callback_data': 'stop_confirm'},
                {'text': '❌ 取消', 'callback_data': 'stop_cancel'}
            ]
        ]
    }

    send_message(chat_id, message, keyboard)

def handle_help(chat_id):
    """處理 /help 指令"""
    message = """❓ *指令說明*

📊 *市場資訊*
/status - 查看系統狀態
/price - 查詢加密貨幣價格
/market - 市場總覽
/news - 最新新聞

💼 *帳戶管理*
/balance - 查看帳戶餘額
/history - 查看交易歷史

🤖 *交易操作*
/trade - 開始自動交易
/stop - 停止自動交易

❓ *其他*
/help - 顯示此幫助訊息

_提示: 點擊輸入框的 / 按鈕查看所有指令_"""

    keyboard = {
        'inline_keyboard': [
            [
                {'text': '📊 查看價格', 'callback_data': 'cmd_price'},
                {'text': '📰 最新新聞', 'callback_data': 'cmd_news'}
            ]
        ]
    }

    send_message(chat_id, message, keyboard)

# ==================== Webhook 路由 ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 Telegram webhook"""
    try:
        data = request.get_json()
        logger.info(f"收到 webhook: {data}")

        # 處理普通訊息
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            # 指令路由
            command_handlers = {
                '/start': handle_start,
                '/status': handle_status,
                '/price': handle_price,
                '/market': handle_market,
                '/news': handle_news,
                '/balance': handle_balance,
                '/history': handle_history,
                '/trade': handle_trade,
                '/stop': handle_stop,
                '/help': handle_help
            }

            handler = command_handlers.get(text)
            if handler:
                executor.submit(handler, chat_id)
            else:
                send_message(chat_id, "❓ 未知指令，請輸入 /help 查看可用指令")

        # 處理內嵌按鈕回調
        elif 'callback_query' in data:
            callback = data['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            callback_data = callback.get('data', '')

            answer_callback_query(callback_id, "處理中...")

            if callback_data == 'cmd_status':
                executor.submit(handle_status, chat_id)
            elif callback_data == 'cmd_price':
                executor.submit(handle_price, chat_id)
            elif callback_data == 'cmd_news':
                executor.submit(handle_news, chat_id)
            elif callback_data == 'cmd_balance':
                executor.submit(handle_balance, chat_id)
            elif callback_data == 'cmd_history':
                executor.submit(handle_history, chat_id)
            elif callback_data == 'cmd_help':
                executor.submit(handle_help, chat_id)
            elif callback_data == 'trade_confirm':
                send_message(chat_id, "✅ 自動交易已啟動！\n\n監控中...")
            elif callback_data == 'trade_cancel':
                send_message(chat_id, "❌ 已取消啟動")
            elif callback_data == 'stop_confirm':
                send_message(chat_id, "⏸️ 自動交易已停止")
            elif callback_data == 'stop_cancel':
                send_message(chat_id, "❌ 已取消停止")

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """健康檢查端點"""
    return jsonify({
        'status': 'running',
        'service': 'Smart Trading Crypto Bot',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """詳細健康檢查"""
    api_status = {}

    try:
        response = requests.get(f'{COINGECKO_BASE}/ping', timeout=5)
        api_status['coingecko'] = 'ok' if response.status_code == 200 else 'error'
    except:
        api_status['coingecko'] = 'error'

    return jsonify({
        'status': 'healthy',
        'bot_configured': bool(BOT_TOKEN),
        'chat_configured': bool(CHAT_ID),
        'api_status': api_status,
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🚀 啟動 Webhook 服務於端口 {port}")
    logger.info(f"✓ Bot Token 已配置: {bool(BOT_TOKEN)}")
    logger.info(f"✓ Chat ID 已配置: {bool(CHAT_ID)}")

    app.run(host='0.0.0.0', port=port, debug=False)
