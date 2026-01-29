from flask import Flask, request, jsonify
import requests
import os
import json
import asyncio
from threading import Thread

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text, reply_markup=None):
    """發送 Telegram 訊息，支持內嵌按鈕"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        return response.json()
    except Exception as e:
        print(f"發送訊息失敗: {e}")
        return None

def get_status_keyboard():
    """狀態查詢的內嵌按鈕"""
    return {
        "inline_keyboard": [
            [
                {"text": "📊 查看狀態", "callback_data": "status"},
                {"text": "💳 查看餘額", "callback_data": "balance"}
            ],
            [
                {"text": "📜 交易歷史", "callback_data": "history"},
                {"text": "📰 最新新聞", "callback_data": "news"}
            ],
            [
                {"text": "⚠️ 風險檢查", "callback_data": "risk"}
            ]
        ]
    }

def get_trade_keyboard():
    """交易控制的內嵌按鈕"""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ 確認開始交易", "callback_data": "confirm_trade"},
                {"text": "❌ 取消", "callback_data": "cancel"}
            ]
        ]
    }

def get_stop_keyboard():
    """停止交易的內嵌按鈕"""
    return {
        "inline_keyboard": [
            [
                {"text": "⚠️ 確認停止", "callback_data": "confirm_stop"},
                {"text": "❌ 取消", "callback_data": "cancel"}
            ]
        ]
    }

def handle_callback_query(callback_query):
    """處理內嵌按鈕回調"""
    callback_data = callback_query.get('data')
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']

    # 回應 callback 避免 loading 狀態
    callback_id = callback_query['id']
    requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", 
                  json={"callback_query_id": callback_id})

    # 根據 callback_data 執行對應操作
    if callback_data == "status":
        handle_status_command(chat_id)
    elif callback_data == "balance":
        handle_balance_command(chat_id)
    elif callback_data == "history":
        handle_history_command(chat_id)
    elif callback_data == "news":
        handle_news_command(chat_id)
    elif callback_data == "risk":
        handle_risk_command(chat_id)
    elif callback_data == "confirm_trade":
        # 執行實際交易邏輯
        send_telegram_message(chat_id, "✅ 交易已啟動！")
        # 這裡應該調用實際的交易啟動邏輯
    elif callback_data == "confirm_stop":
        # 執行實際停止邏輯
        send_telegram_message(chat_id, "⏸️ 交易已停止！")
        # 這裡應該調用實際的停止邏輯
    elif callback_data == "cancel":
        # 編輯原訊息
        requests.post(f"{TELEGRAM_API_URL}/editMessageText", 
                     json={
                         "chat_id": chat_id,
                         "message_id": message_id,
                         "text": "❌ 操作已取消"
                     })

def handle_status_command(chat_id):
    """處理 /status 指令"""
    # 這裡應該從你的系統獲取實際狀態
    message = """📊 *系統狀態*

🤖 Bot 狀態: 運行中
💰 當前持倉: BTC 0.05
💵 可用餘額: $1,000
📈 今日收益: +2.5%
"""
    send_telegram_message(chat_id, message)

def handle_balance_command(chat_id):
    """處理 /balance 指令"""
    message = """💳 *帳戶餘額*

總資產: $10,500
可用資金: $1,000
持倉價值: $9,500
"""
    send_telegram_message(chat_id, message)

def handle_history_command(chat_id):
    """處理 /history 指令"""
    message = """📜 *交易歷史*

1. BTC 買入 $45,000 ✅
2. ETH 賣出 $3,200 ✅
3. BTC 賣出 $46,000 ✅
"""
    send_telegram_message(chat_id, message)

def handle_news_command(chat_id):
    """處理 /news 指令"""
    message = """📰 *最新加密貨幣新聞*

• Bitcoin 突破 $45,000
• 以太坊升級即將到來
• 監管機構發布新指引
"""
    send_telegram_message(chat_id, message)

def handle_risk_command(chat_id):
    """處理 /risk 指令"""
    message = """⚠️ *風險檢查*

當前風險等級: 🟢 低
市場波動性: 正常
建議: 可以進行交易
"""
    send_telegram_message(chat_id, message)

def process_telegram_message(message):
    """處理 Telegram 訊息"""
    chat_id = message['chat']['id']
    text = message.get('text', '')

    if text.startswith('/start'):
        # /start 帶有內嵌按鈕的歡迎訊息
        welcome_text = """🚀 *歡迎使用加密貨幣交易 Bot！*

我可以幫你：
• 監控市場動態
• 自動執行交易
• 風險管理
• 實時通知

點擊下方按鈕快速查詢："""
        send_telegram_message(chat_id, welcome_text, get_status_keyboard())

    elif text.startswith('/status'):
        handle_status_command(chat_id)

    elif text.startswith('/balance'):
        handle_balance_command(chat_id)

    elif text.startswith('/history'):
        handle_history_command(chat_id)

    elif text.startswith('/news'):
        handle_news_command(chat_id)

    elif text.startswith('/risk'):
        handle_risk_command(chat_id)

    elif text.startswith('/trade'):
        # 需要確認的操作，顯示確認按鈕
        send_telegram_message(
            chat_id, 
            "⚠️ 確定要開始自動交易嗎？", 
            get_trade_keyboard()
        )

    elif text.startswith('/stop'):
        # 需要確認的操作，顯示確認按鈕
        send_telegram_message(
            chat_id, 
            "⚠️ 確定要停止交易嗎？", 
            get_stop_keyboard()
        )

    elif text.startswith('/help'):
        help_text = """❓ *可用指令*

/start - 啟動 Bot
/status - 查看狀態
/trade - 開始交易
/stop - 停止交易
/balance - 查看餘額
/history - 交易歷史
/news - 最新新聞
/risk - 風險檢查
/help - 查看幫助

💡 *提示*：點擊輸入框左側的 / 按鈕可以快速選擇指令！"""
        send_telegram_message(chat_id, help_text, get_status_keyboard())

    else:
        send_telegram_message(chat_id, "❌ 未知指令，請使用 /help 查看可用指令")

@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 Telegram webhook"""
    try:
        update = request.json

        # 處理普通訊息
        if 'message' in update:
            message = update['message']
            process_telegram_message(message)

        # 處理內嵌按鈕回調
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            handle_callback_query(callback_query)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Webhook 錯誤: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({"status": "healthy", "service": "telegram-webhook"}), 200

@app.route('/', methods=['GET'])
def home():
    """首頁"""
    return jsonify({
        "service": "Telegram Webhook Server",
        "status": "running",
        "endpoints": {
            "/webhook": "POST - Telegram webhook endpoint",
            "/health": "GET - Health check",
            "/": "GET - This page"
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
