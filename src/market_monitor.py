"""
市場監控排程系統
定期檢查市場狀況，根據用戶風險屬性主動發送通知
"""
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from .database import db
from .trading_strategy import trading_strategy

logger = logging.getLogger(__name__)


class MarketMonitor:
    """市場監控類"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 300  # 5分鐘檢查一次
        
        # 預設監控幣種
        self.default_symbols = ['BTC/USDT', 'ETH/USDT']
    
    def start(self):
        """啟動監控"""
        if self.is_running:
            logger.warning("監控已在運行中")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("市場監控已啟動")
    
    def stop(self):
        """停止監控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("市場監控已停止")
    
    def _monitor_loop(self):
        """監控主循環"""
        while self.is_running:
            try:
                self._check_all_users()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                time.sleep(60)  # 錯誤後等待1分鐘再重試
    
    def _check_all_users(self):
        """檢查所有用戶"""
        try:
            # 獲取所有活躍用戶
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT u.user_id, u.timezone, r.risk_level, r.notification_frequency
                FROM users u
                JOIN user_risk_profiles r ON u.user_id = r.user_id
                WHERE u.is_active = 1 AND r.is_current = 1
            ''')
            users = cursor.fetchall()
            conn.close()
            
            logger.info(f"檢查 {len(users)} 個活躍用戶")
            
            for user in users:
                user_id = user['user_id']
                timezone = user['timezone']
                risk_level = user['risk_level']
                notification_freq = user['notification_frequency']
                
                # 檢查是否該發送通知
                if self._should_send_notification(user_id, notification_freq, timezone):
                    self._check_user_positions(user_id, risk_level)
                    self._scan_entry_opportunities(user_id, risk_level)
                    self._send_daily_summary(user_id, risk_level, timezone)
        
        except Exception as e:
            logger.error(f"檢查用戶錯誤: {e}")
    
    def _should_send_notification(self, user_id: int, notification_freq: str, 
                                  timezone: str) -> bool:
        """判斷是否該發送通知"""
        # 檢查今日通知數量
        today_count = db.get_notification_count_today(user_id)
        max_notifications = 10  # 每日最大通知數
        
        if today_count >= max_notifications:
            return False
        
        # 根據通知頻率決定
        if notification_freq == 'realtime':
            return True  # 積極型用戶：即時通知
        
        # 獲取用戶當地時間
        user_tz = pytz.timezone(timezone)
        user_time = datetime.now(user_tz)
        hour = user_time.hour
        
        if notification_freq == 'daily':
            # 保守型：每日一次（晚上8點）
            return hour == 20
        
        elif notification_freq == 'twice':
            # 穩健型：每日兩次（早上9點、晚上8點）
            return hour in [9, 20]
        
        return False
    
    def _check_user_positions(self, user_id: int, risk_level: int):
        """檢查用戶持倉，發送退場信號"""
        try:
            positions = db.get_open_positions(user_id)
            
            for position in positions:
                symbol = position['symbol']
                position_id = position['position_id']
                
                # 獲取當前市場數據
                market_data = self._fetch_market_data(symbol)
                if not market_data:
                    continue
                
                current_price = market_data['price']
                
                # 分析退場信號
                exit_signal = trading_strategy.analyze_exit_signal(
                    user_id=user_id,
                    position_id=position_id,
                    current_price=current_price,
                    market_data=market_data
                )
                
                # 如果應該退場，發送通知
                if exit_signal['should_exit']:
                    self._send_exit_notification(
                        user_id=user_id,
                        position=position,
                        exit_signal=exit_signal,
                        current_price=current_price
                    )
        
        except Exception as e:
            logger.error(f"檢查持倉錯誤: {e}")
    
    def _scan_entry_opportunities(self, user_id: int, risk_level: int):
        """掃描進場機會"""
        try:
            # 獲取用戶監控列表
            watchlist = db.get_active_watchlist(user_id)
            
            # 如果沒有監控列表，使用預設幣種
            if not watchlist:
                symbols = self.default_symbols
            else:
                symbols = [item['symbol'] for item in watchlist]
            
            for symbol in symbols:
                # 獲取市場數據
                market_data = self._fetch_market_data(symbol)
                if not market_data:
                    continue
                
                # 分析進場信號
                entry_signal = trading_strategy.analyze_entry_signal(
                    user_id=user_id,
                    symbol=symbol,
                    market_data=market_data
                )
                
                # 如果應該進場且信心度高，發送通知
                if entry_signal['should_enter'] and entry_signal['confidence'] >= 0.7:
                    self._send_entry_notification(
                        user_id=user_id,
                        symbol=symbol,
                        entry_signal=entry_signal,
                        market_data=market_data
                    )
        
        except Exception as e:
            logger.error(f"掃描進場機會錯誤: {e}")
    
    def _fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """獲取市場數據（整合多個數據源）"""
        try:
            # 這裡整合現有的獲取邏輯
            # 1. 價格數據（CoinGecko）
            coin_id = self._symbol_to_coingecko_id(symbol)
            price_data = self._fetch_coingecko_data(coin_id)
            
            # 2. 技術指標（可以從現有 webhook 獲取或計算）
            technical_data = self._calculate_technical_indicators(symbol, price_data)
            
            # 3. 新聞情緒（從現有 RSS feed）
            news_sentiment = self._fetch_news_sentiment(symbol)
            
            # 整合數據
            market_data = {
                'price': price_data.get('current_price', 0),
                'volume_24h': price_data.get('total_volume', 0),
                'price_change_24h': price_data.get('price_change_percentage_24h', 0),
                'rsi': technical_data.get('rsi'),
                'ma_50': technical_data.get('ma_50'),
                'ma_200': technical_data.get('ma_200'),
                'macd': technical_data.get('macd'),
                'macd_signal': technical_data.get('macd_signal'),
                'avg_volume': technical_data.get('avg_volume', price_data.get('total_volume', 0)),
                'news_sentiment': news_sentiment
            }
            
            # 保存快照到資料庫
            db.save_market_snapshot(
                symbol=symbol,
                price=market_data['price'],
                volume_24h=market_data['volume_24h'],
                price_change_24h=market_data['price_change_24h'],
                rsi_14=market_data['rsi'],
                ma_50=market_data['ma_50'],
                ma_200=market_data['ma_200'],
                news_sentiment=market_data['news_sentiment']
            )
            
            return market_data
        
        except Exception as e:
            logger.error(f"獲取市場數據錯誤 ({symbol}): {e}")
            return None
    
    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """交易對轉換為 CoinGecko ID"""
        mapping = {
            'BTC/USDT': 'bitcoin',
            'ETH/USDT': 'ethereum',
            'BNB/USDT': 'binancecoin',
            'SOL/USDT': 'solana',
            'XRP/USDT': 'ripple'
        }
        return mapping.get(symbol, 'bitcoin')
    
    def _fetch_coingecko_data(self, coin_id: str) -> Dict:
        """從 CoinGecko 獲取數據"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': coin_id,
                'order': 'market_cap_desc',
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0]
            
            return {}
        except Exception as e:
            logger.error(f"CoinGecko 請求錯誤: {e}")
            return {}
    
    def _calculate_technical_indicators(self, symbol: str, price_data: Dict) -> Dict:
        """計算技術指標（簡化版，實際需要歷史數據）"""
        # 這裡需要從資料庫獲取歷史快照來計算指標
        # 簡化版本：返回模擬數據或從其他 API 獲取
        
        try:
            # 從資料庫獲取最近的快照
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rsi_14, ma_50, ma_200 
                FROM market_snapshots 
                WHERE symbol = ? 
                ORDER BY captured_at DESC LIMIT 1
            ''', (symbol,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'rsi': row['rsi_14'],
                    'ma_50': row['ma_50'],
                    'ma_200': row['ma_200'],
                    'macd': None,
                    'macd_signal': None,
                    'avg_volume': None
                }
            
            # 如果沒有歷史數據，使用估算值
            current_price = price_data.get('current_price', 0)
            return {
                'rsi': 50,  # 中性
                'ma_50': current_price * 0.98,
                'ma_200': current_price * 0.95,
                'macd': 0,
                'macd_signal': 0,
                'avg_volume': price_data.get('total_volume', 0)
            }
        
        except Exception as e:
            logger.error(f"計算技術指標錯誤: {e}")
            return {}
    
    def _fetch_news_sentiment(self, symbol: str) -> float:
        """獲取新聞情緒分數（0-1）"""
        # 簡化版：使用價格變化作為代理
        # 實際應該分析新聞標題和內容
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price_change_24h 
                FROM market_snapshots 
                WHERE symbol = ? 
                ORDER BY captured_at DESC LIMIT 1
            ''', (symbol,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row['price_change_24h']:
                # 簡單映射：正面變化 -> 正面情緒
                change = row['price_change_24h']
                sentiment = 0.5 + (change / 100)  # -50% -> 0, +50% -> 1
                return max(0, min(1, sentiment))
            
            return 0.5  # 中性
        
        except Exception as e:
            logger.error(f"獲取新聞情緒錯誤: {e}")
            return 0.5
    
    def _send_entry_notification(self, user_id: int, symbol: str,
                                 entry_signal: Dict, market_data: Dict):
        """發送進場通知"""
        try:
            message = f"🚀 進場機會提醒\n\n"
            message += f"幣種: {symbol}\n"
            message += f"當前價格: ${market_data['price']:,.2f}\n"
            message += f"策略: {entry_signal['strategy_name']}\n"
            message += f"信心度: {entry_signal['confidence']*100:.0f}%\n\n"
            message += "📊 分析依據:\n"
            
            for reason in entry_signal['reasons'][:5]:  # 最多顯示5個原因
                message += f"{reason}\n"
            
            message += f"\n{entry_signal['recommendation']}"
            
            # 發送 Telegram 訊息
            self._send_telegram_message(user_id, message)
            
            # 記錄通知
            db.log_notification(
                user_id=user_id,
                notification_type='entry',
                message=message,
                symbol=symbol,
                priority='high'
            )
        
        except Exception as e:
            logger.error(f"發送進場通知錯誤: {e}")
    
    def _send_exit_notification(self, user_id: int, position: Dict,
                               exit_signal: Dict, current_price: float):
        """發送退場通知"""
        try:
            exit_type_emoji = {
                'stop_loss': '🛑',
                'take_profit': '✅',
                'signal': '⚠️'
            }
            
            emoji = exit_type_emoji.get(exit_signal['exit_type'], '⚠️')
            
            message = f"{emoji} 退場信號提醒\n\n"
            message += f"幣種: {position['symbol']}\n"
            message += f"進場價: ${position['entry_price']:,.2f}\n"
            message += f"當前價: ${current_price:,.2f}\n"
            message += f"損益: {exit_signal['current_pl']:+.2f}%\n\n"
            message += "📊 退場原因:\n"
            
            for reason in exit_signal['reasons']:
                message += f"{reason}\n"
            
            message += f"\n{exit_signal['recommendation']}"
            
            # 發送 Telegram 訊息
            self._send_telegram_message(user_id, message)
            
            # 記錄通知
            priority = 'urgent' if exit_signal['exit_type'] == 'stop_loss' else 'high'
            db.log_notification(
                user_id=user_id,
                notification_type='exit',
                message=message,
                symbol=position['symbol'],
                priority=priority
            )
        
        except Exception as e:
            logger.error(f"發送退場通知錯誤: {e}")
    
    def _send_daily_summary(self, user_id: int, risk_level: int, timezone: str):
        """發送每日摘要"""
        try:
            # 獲取用戶績效
            performance = db.get_user_performance(user_id)
            
            # 獲取持倉狀況
            positions = db.get_open_positions(user_id)
            
            message = "📊 每日投資摘要\n\n"
            message += f"時間: {datetime.now(pytz.timezone(timezone)).strftime('%Y-%m-%d %H:%M')}\n\n"
            
            message += "💼 持倉狀況:\n"
            if positions:
                for pos in positions:
                    symbol = pos['symbol']
                    entry_price = pos['entry_price']
                    # 需要獲取當前價格計算損益
                    message += f"  • {symbol}: ${entry_price:,.2f}\n"
            else:
                message += "  無持倉\n"
            
            message += f"\n📈 績效統計:\n"
            if performance.get('total_trades', 0) > 0:
                message += f"  • 總交易: {performance['total_trades']} 筆\n"
                message += f"  • 勝率: {performance['winning_trades']/performance['total_trades']*100:.1f}%\n"
                message += f"  • 平均報酬: {performance.get('avg_return', 0):.2f}%\n"
            else:
                message += "  尚無交易記錄\n"
            
            # 發送訊息（優先級較低）
            self._send_telegram_message(user_id, message)
            
            # 記錄通知
            db.log_notification(
                user_id=user_id,
                notification_type='summary',
                message=message,
                priority='normal'
            )
        
        except Exception as e:
            logger.error(f"發送每日摘要錯誤: {e}")
    
    def _send_telegram_message(self, user_id: int, message: str):
        """發送 Telegram 訊息"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code != 200:
                logger.error(f"發送訊息失敗: {response.text}")
        
        except Exception as e:
            logger.error(f"發送 Telegram 訊息錯誤: {e}")


# 全局監控實例（需要在主程式初始化）
market_monitor = None

def init_monitor(bot_token: str):
    """初始化監控系統"""
    global market_monitor
    market_monitor = MarketMonitor(bot_token)
    return market_monitor
