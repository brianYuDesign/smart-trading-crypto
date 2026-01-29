"""
Telegram 通知系統
發送交易信號和風險警報到 Telegram
"""
import os
from datetime import datetime
from typing import Dict, Optional
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram 通知器"""
    
    def __init__(self, config: Dict, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        初始化 Telegram 通知器
        
        Args:
            config: 配置字典
            bot_token: Telegram Bot Token（可選，從環境變數讀取）
            chat_id: Telegram Chat ID（可選，從環境變數讀取）
        """
        self.config = config
        self.telegram_config = config.get('telegram', {})
        
        # 從環境變數或參數獲取憑證
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram 憑證未設定，通知功能將無法使用")
        else:
            logger.info("Telegram 通知器已初始化")
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        發送 Telegram 訊息
        
        Args:
            message: 訊息內容
            parse_mode: 解析模式（HTML 或 Markdown）
            
        Returns:
            是否發送成功
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram 憑證未設定")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram 訊息發送成功")
            return True
        except Exception as e:
            logger.error(f"發送 Telegram 訊息失敗: {e}")
            return False
    
    def notify_buy_signal(self, signal: Dict, market_conditions: Dict) -> bool:
        """
        發送買入信號通知
        
        Args:
            signal: 買入信號字典
            market_conditions: 市場狀況字典
            
        Returns:
            是否發送成功
        """
        reasons = '\n'.join([f"  • {reason}" for reason in signal['reasons']])
        
        message = f"""
🟢 <b>買入信號</b> [{signal['strength']}]

📊 <b>交易對:</b> {market_conditions['symbol']}
💰 <b>當前價格:</b> ${signal['price']:.2f}
📈 <b>24h 漲跌:</b> {market_conditions['price_change_24h']:.2f}%

<b>📉 技術指標:</b>
  • RSI: {signal['rsi']}
  • MACD: {signal['macd']:.4f}
  • MACD Signal: {signal['macd_signal']:.4f}
  • 成交量比: {signal['volume_ratio']}x

<b>✅ 信號原因:</b>
{reasons}

<b>🔍 市場狀況:</b>
  • 波動率: {market_conditions['volatility']:.2f}%
  • 24h 成交量: {market_conditions['volume_24h']:.2f}

⏰ {signal['timestamp']}

⚠️ <i>此為系統自動分析，請謹慎決策</i>
"""
        
        return self.send_message(message.strip())
    
    def notify_sell_signal(self, signal: Dict, market_conditions: Dict) -> bool:
        """
        發送賣出信號通知
        
        Args:
            signal: 賣出信號字典
            market_conditions: 市場狀況字典
            
        Returns:
            是否發送成功
        """
        reasons = '\n'.join([f"  • {reason}" for reason in signal['reasons']])
        
        message = f"""
🔴 <b>賣出信號</b> [{signal['strength']}]

📊 <b>交易對:</b> {market_conditions['symbol']}
💰 <b>當前價格:</b> ${signal['price']:.2f}
📉 <b>24h 漲跌:</b> {market_conditions['price_change_24h']:.2f}%

<b>📈 技術指標:</b>
  • RSI: {signal['rsi']}
  • MACD: {signal['macd']:.4f}
  • MACD Signal: {signal['macd_signal']:.4f}
  • 成交量比: {signal['volume_ratio']}x

<b>⚠️ 信號原因:</b>
{reasons}

<b>🔍 市場狀況:</b>
  • 波動率: {market_conditions['volatility']:.2f}%
  • 24h 成交量: {market_conditions['volume_24h']:.2f}

⏰ {signal['timestamp']}

⚠️ <i>此為系統自動分析，請謹慎決策</i>
"""
        
        return self.send_message(message.strip())
    
    def notify_risk_alert(self, alert_type: str, details: Dict) -> bool:
        """
        發送風險警報
        
        Args:
            alert_type: 警報類型（news, volatility, etc）
            details: 警報詳情
            
        Returns:
            是否發送成功
        """
        if alert_type == 'news':
            high_risk_news = details.get('high_risk_news', [])
            news_items = '\n'.join([
                f"  • {news['title'][:100]}..."
                for news in high_risk_news[:3]
            ])
            
            message = f"""
⚠️ <b>新聞風險警報</b>

🚨 檢測到 {details['high_risk_count']} 個高風險新聞事件

<b>主要新聞:</b>
{news_items}

<b>🛡️ 風險措施:</b>
  • 暫停交易信號 24 小時
  • 冷卻至: {details.get('cooldown_until', 'N/A')}

⏰ {details['timestamp']}
"""
        
        elif alert_type == 'volatility':
            message = f"""
⚠️ <b>市場波動警報</b>

📊 <b>交易對:</b> {details['symbol']}
💰 <b>當前價格:</b> ${details['current_price']:.2f}
📉 <b>波動率:</b> {details['volatility']:.2f}%

<b>🛡️ 風險措施:</b>
  • 市場波動率過高，暫停交易信號
  • 建議等待市場穩定

⏰ {details['timestamp']}
"""
        
        else:
            message = f"""
⚠️ <b>系統警報</b>

類型: {alert_type}
詳情: {details}
"""
        
        return self.send_message(message.strip())
    
    def notify_system_status(self, status: str, details: Optional[str] = None) -> bool:
        """
        發送系統狀態通知
        
        Args:
            status: 狀態（started, stopped, error）
            details: 詳細信息
            
        Returns:
            是否發送成功
        """
        status_emoji = {
            'started': '✅',
            'stopped': '⏸️',
            'error': '❌'
        }
        
        emoji = status_emoji.get(status, 'ℹ️')
        
        message = f"""
{emoji} <b>系統狀態更新</b>

狀態: {status.upper()}
"""
        
        if details:
            message += f"\n詳情: {details}"
        
        message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message.strip())
    
    def test_connection(self) -> bool:
        """
        測試 Telegram 連接
        
        Returns:
            連接是否正常
        """
        message = "🤖 Smart Trading Crypto 系統測試訊息"
        return self.send_message(message)
