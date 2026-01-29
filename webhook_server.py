"""
Flask Web Server for Telegram Webhook
處理即時的 Telegram 指令回應
"""
from flask import Flask, request, jsonify
import os
import logging
from dotenv import load_dotenv
from src.telegram_commands import TelegramCommandHandler

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化 Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.error("Missing required environment variables: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    # raise ValueError("Missing required environment variables") 

# 初始化 Handler
bot = TelegramCommandHandler()

@app.route('/')
def home():
    """健康檢查端點"""
    return jsonify({
        'status': 'ok',
        'service': 'Smart Trading Crypto Bot',
        'version': '1.0',
        'mode': 'webhook'
    })

@app.route('/health')
def health():
    """Render.com 健康檢查"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    接收 Telegram webhook 並處理指令
    """
    try:
        # 獲取 Telegram 更新
        update = request.get_json()

        if not update:
            logger.warning("Received empty update")
            return jsonify({'status': 'error', 'message': 'Empty update'}), 400

        logger.info(f"Received update: {update}")

        # 檢查是否有訊息
        if 'message' not in update:
            logger.info("Update has no message, skipping")
            return jsonify({'status': 'ok', 'message': 'No message to process'}), 200

        message = update['message']

        # 檢查是否來自正確的 chat
        chat_id = str(message.get('chat', {}).get('id', ''))
        if chat_id != TELEGRAM_CHAT_ID:
            logger.warning(f"Message from unauthorized chat: {chat_id}")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        # 檢查是否有文字內容
        text = message.get('text', '')
        if not text:
            logger.info("Message has no text content")
            return jsonify({'status': 'ok', 'message': 'No text content'}), 200

        # 檢查是否為指令
        if not text.startswith('/'):
            logger.info(f"Message is not a command: {text}")
            return jsonify({'status': 'ok', 'message': 'Not a command'}), 200

        # 處理指令
        logger.info(f"Processing command: {text}")

        # 使用 TelegramBot 的指令處理邏輯
        command = text.split()[0].lower()
        response = bot.handle_command(message)

        logger.info(f"Command processed successfully: {command}")

        return jsonify({
            'status': 'ok',
            'command': command,
            'response': response
        }), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """
    設定 Telegram webhook (僅供管理使用)
    """
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')

        if not webhook_url:
            return jsonify({'status': 'error', 'message': 'webhook_url is required'}), 400

        success = bot.set_webhook(webhook_url)

        if success:
            return jsonify({
                'status': 'ok',
                'message': f'Webhook set to {webhook_url}'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to set webhook'
            }), 500

    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # 本地測試用 (使用 5001 避免 macOS AirPlay 衝突)
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
