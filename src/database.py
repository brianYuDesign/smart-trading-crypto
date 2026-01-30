"""
資料庫管理模組
提供所有資料庫操作的封裝
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import json
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """資料庫管理類"""
    
    def __init__(self, db_path: str = 'crypto_bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 讓查詢結果可以用字典方式訪問
        return conn
    
    def init_database(self):
        """初始化資料庫結構"""
        try:
            if os.path.exists('database_schema.sql'):
                with open('database_schema.sql', 'r', encoding='utf-8') as f:
                    schema = f.read()
                
                conn = self.get_connection()
                conn.executescript(schema)
                conn.commit()
                conn.close()
            
            # 執行遷移：檢查並添加缺失的欄位
            self._migrate_database()
            
            logger.info("資料庫初始化成功")
        except Exception as e:
            logger.error(f"資料庫初始化失敗: {e}")
            raise

    def _migrate_database(self):
        """執行資料庫遷移"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. 檢查 users 表是否需要 timezone 欄位
            cursor.execute("PRAGMA table_info(users)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'timezone' not in columns:
                logger.info("遷移: 為 users 表添加 timezone 欄位")
                logger.info("遷移: 為 users 表添加 timezone 欄位")
                logger.info("遷移: 為 users 表添加 timezone 欄位")
                cursor.execute("ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Asia/Taipei'")
            
            if 'is_active' not in columns:
                logger.info("遷移: 為 users 表添加 is_active 欄位")
            if 'is_active' not in columns:
                logger.info("遷移: 為 users 表添加 is_active 欄位")
                cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")

            if 'language_code' not in columns:
                logger.info("遷移: 為 users 表添加 language_code 欄位")
                cursor.execute("ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT 'zh-TW'")

            # 2. 檢查 user_risk_profiles 表是否需要 notification_frequency 欄位
            # 先檢查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_risk_profiles'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(user_risk_profiles)")
                rp_columns = [info[1] for info in cursor.fetchall()]
                
                if 'notification_frequency' not in rp_columns:
                    logger.info("遷移: 為 user_risk_profiles 表添加 notification_frequency 欄位")
                if 'notification_frequency' not in rp_columns:
                    logger.info("遷移: 為 user_risk_profiles 表添加 notification_frequency 欄位")
                    cursor.execute("ALTER TABLE user_risk_profiles ADD COLUMN notification_frequency TEXT DEFAULT '4h'")

                if 'is_current' not in rp_columns:
                    logger.info("遷移: 為 user_risk_profiles 表添加 is_current 欄位")
                    cursor.execute("ALTER TABLE user_risk_profiles ADD COLUMN is_current INTEGER DEFAULT 1")

            
            # 3. 檢查是否需要創建 subscriptions 表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
            if not cursor.fetchone():
                logger.info("遷移: 創建 subscriptions 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        symbol TEXT,
                        condition TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, symbol)
                    )
                ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"資料庫遷移失敗: {e}")
    
    # ==================== 用戶管理 ====================
    
    def create_or_update_user(self, user_id: int, username: str = None, 
                              first_name: str = None, last_name: str = None,
                              language_code: str = 'zh-TW') -> bool:
        """創建或更新用戶資料"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, language_code, last_active)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_active = CURRENT_TIMESTAMP
            ''', (user_id, username, first_name, last_name, language_code))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"創建/更新用戶失敗: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """獲取用戶資料"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"獲取用戶資料失敗: {e}")
            return None
    
    def update_user_timezone(self, user_id: int, timezone: str) -> bool:
        """更新用戶時區"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET timezone = ? WHERE user_id = ?
            ''', (timezone, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新時區失敗: {e}")
            return False
    
    def init_user(self, user_id: int) -> bool:
        """初始化用戶（如果不存在則創建）"""
        try:
            user = self.get_user(user_id)
            if not user:
                self.create_or_update_user(user_id)
                logger.info(f"初始化新用戶: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"初始化用戶失敗: {e}")
            raise
    
    def get_positions(self, user_id: int, status: str = 'open') -> List[Dict]:
        """獲取用戶的持倉
        
        Args:
            user_id: 用戶 ID
            status: 持倉狀態 ('open' 或 'closed')
        
        Returns:
            持倉列表
        """
        try:
            if status == 'open':
                return self.get_open_positions(user_id)
            else:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, symbol, position_type, entry_price, exit_price,
                           position_size, stop_loss, take_profit, status,
                           entry_time, exit_time, profit_loss
                    FROM positions
                    WHERE user_id = ? AND status = ?
                    ORDER BY exit_time DESC
                """, (user_id, status))
                
                positions = []
                for row in cursor.fetchall():
                    positions.append({
                        'id': row[0],
                        'symbol': row[1],
                        'position_type': row[2],
                        'entry_price': row[3],
                        'exit_price': row[4],
                        'position_size': row[5],
                        'stop_loss': row[6],
                        'take_profit': row[7],
                        'status': row[8],
                        'entry_time': row[9],
                        'exit_time': row[10],
                        'profit_loss': row[11]
                    })
                
                conn.close()
                return positions
                
        except Exception as e:
            logger.error(f"獲取持倉失敗: {e}")
            return []
    
    # ==================== 風險屬性管理 ====================
    
    def save_risk_profile(self, user_id: int, risk_score: int, 
                          answers: List[Tuple[int, str, int]]) -> Optional[int]:
        """保存風險屬性評估結果
        
        Args:
            user_id: 用戶ID
            risk_score: 總分
            answers: [(問題編號, 選項, 分數), ...]
        
        Returns:
            profile_id 或 None
        """
        try:
            # 確定風險等級
            if risk_score <= 16:
                risk_level = 1
                max_loss = 10.0
                notification_freq = 'daily'
            elif risk_score <= 23:
                risk_level = 2
                max_loss = 20.0
                notification_freq = 'twice'
            else:
                risk_level = 3
                max_loss = 30.0
                notification_freq = 'realtime'
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 將舊的風險屬性設為非當前
            cursor.execute('''
                UPDATE user_risk_profiles 
                SET is_current = 0 
                WHERE user_id = ? AND is_current = 1
            ''', (user_id,))
            
            # 插入新的風險屬性
            cursor.execute('''
                INSERT INTO user_risk_profiles 
                (user_id, risk_level, risk_score, max_loss_tolerance, notification_frequency)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, risk_level, risk_score, max_loss, notification_freq))
            
            profile_id = cursor.lastrowid
            
            # 保存問卷答案
            for q_num, option, score in answers:
                cursor.execute('''
                    INSERT INTO risk_assessment_answers 
                    (profile_id, question_number, answer_option, score)
                    VALUES (?, ?, ?, ?)
                ''', (profile_id, q_num, option, score))
            
            conn.commit()
            conn.close()
            logger.info(f"用戶 {user_id} 風險屬性已保存，等級: {risk_level}")
            return profile_id
        except Exception as e:
            logger.error(f"保存風險屬性失敗: {e}")
            return None
    
    def get_current_risk_profile(self, user_id: int) -> Optional[Dict]:
        """獲取用戶當前的風險屬性"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_risk_profiles 
                WHERE user_id = ? AND is_current = 1
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"獲取風險屬性失敗: {e}")
            return None
    
    # ==================== 持倉管理 ====================
    
    def add_position(self, user_id: int, symbol: str, entry_price: float,
                     quantity: float, entry_reason: str = None) -> Optional[int]:
        """新增持倉記錄"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_positions 
                (user_id, symbol, entry_price, quantity, entry_reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, entry_price, quantity, entry_reason))
            
            position_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return position_id
        except Exception as e:
            logger.error(f"新增持倉失敗: {e}")
            return None
    
    def close_position(self, position_id: int, exit_price: float, 
                       exit_reason: str = None) -> bool:
        """關閉持倉"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取持倉資料計算損益
            cursor.execute('''
                SELECT entry_price, quantity FROM user_positions 
                WHERE position_id = ?
            ''', (position_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            entry_price = row['entry_price']
            quantity = row['quantity']
            
            profit_loss = (exit_price - entry_price) * quantity
            profit_loss_percent = ((exit_price - entry_price) / entry_price) * 100
            
            cursor.execute('''
                UPDATE user_positions 
                SET exit_price = ?, exit_time = CURRENT_TIMESTAMP,
                    profit_loss = ?, profit_loss_percent = ?,
                    status = 'closed', exit_reason = ?
                WHERE position_id = ?
            ''', (exit_price, profit_loss, profit_loss_percent, exit_reason, position_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"關閉持倉失敗: {e}")
            return False
    
    def get_open_positions(self, user_id: int) -> List[Dict]:
        """獲取用戶所有開倉記錄"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_positions 
                WHERE user_id = ? AND status = 'open'
                ORDER BY entry_time DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取開倉記錄失敗: {e}")
            return []
    
    # ==================== 交易信號管理 ====================
    
    def save_trading_signal(self, user_id: int, symbol: str, signal_type: str,
                            risk_level: int, price: float, rsi: float = None,
                            volume_ratio: float = None, news_sentiment: float = None,
                            recommendation: str = '', confidence: float = 0.5) -> Optional[int]:
        """保存交易信號"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trading_signals 
                (user_id, symbol, signal_type, risk_level, price, rsi, 
                 volume_ratio, news_sentiment, recommendation, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, symbol, signal_type, risk_level, price, rsi,
                  volume_ratio, news_sentiment, recommendation, confidence))
            
            signal_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return signal_id
        except Exception as e:
            logger.error(f"保存交易信號失敗: {e}")
            return None
    
    def mark_signal_notified(self, signal_id: int) -> bool:
        """標記信號已通知"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE trading_signals 
                SET was_notified = 1 
                WHERE signal_id = ?
            ''', (signal_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"標記信號失敗: {e}")
            return False
    
    # ==================== 通知管理 ====================
    
    def log_notification(self, user_id: int, notification_type: str,
                        message: str, symbol: str = None, 
                        priority: str = 'normal') -> Optional[int]:
        """記錄通知"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notification_logs 
                (user_id, notification_type, symbol, message, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, notification_type, symbol, message, priority))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            logger.error(f"記錄通知失敗: {e}")
            return None
    
    def get_notification_count_today(self, user_id: int) -> int:
        """獲取今日通知數量"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM notification_logs 
                WHERE user_id = ? AND DATE(sent_at) = DATE('now')
            ''', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"獲取通知數量失敗: {e}")
            return 0
    
    # ==================== 監控列表管理 ====================
    
    def add_watchlist(self, user_id: int, symbol: str, alert_type: str,
                      alert_condition: str, threshold_value: float = None) -> Optional[int]:
        """新增監控項目"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO market_watchlist 
                (user_id, symbol, alert_type, alert_condition, threshold_value)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, alert_type, alert_condition, threshold_value))
            
            watchlist_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return watchlist_id
        except Exception as e:
            logger.error(f"新增監控失敗: {e}")
            return None
    
    def get_active_watchlist(self, user_id: int) -> List[Dict]:
        """獲取活躍的監控項目"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM market_watchlist 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取監控列表失敗: {e}")
            logger.error(f"獲取監控列表失敗: {e}")
            return []

    # ==================== 訂閱管理 (從 V1 移植) ====================

    def add_subscription(self, user_id, symbol, condition=None):
        """添加訂閱"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions (user_id, symbol, condition, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, symbol.upper(), condition))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"添加訂閱失敗: {e}")
            return False

    def remove_subscription(self, user_id, symbol):
        """移除訂閱"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM subscriptions 
                WHERE user_id = ? AND symbol = ?
            ''', (user_id, symbol.upper()))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"移除訂閱失敗: {e}")
            return False

    def get_user_subscriptions(self, user_id):
        """獲取用戶訂閱列表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, condition, created_at 
                FROM subscriptions 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取用戶訂閱失敗: {e}")
            return []

    def get_all_subscriptions(self):
        """獲取所有訂閱（用於監控）"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, symbol, condition 
                FROM subscriptions
            ''')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取所有訂閱失敗: {e}")
            return []
    
    # ==================== 市場數據管理 ====================
    
    def save_market_snapshot(self, symbol: str, price: float, 
                            volume_24h: float = None, price_change_24h: float = None,
                            rsi_14: float = None, ma_50: float = None, 
                            ma_200: float = None, news_sentiment: float = None) -> bool:
        """保存市場快照"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO market_snapshots 
                (symbol, price, volume_24h, price_change_24h, rsi_14, ma_50, ma_200, news_sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, price, volume_24h, price_change_24h, rsi_14, ma_50, ma_200, news_sentiment))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"保存市場快照失敗: {e}")
            return False
    
    def get_latest_snapshot(self, symbol: str) -> Optional[Dict]:
        """獲取最新市場快照"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM market_snapshots 
                WHERE symbol = ? 
                ORDER BY captured_at DESC LIMIT 1
            ''', (symbol,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"獲取市場快照失敗: {e}")
            return None
    
    # ==================== 統計分析 ====================
    
    def get_user_performance(self, user_id: int) -> Dict:
        """獲取用戶績效統計"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 總交易次數
            cursor.execute('''
                SELECT COUNT(*) as total_trades,
                       SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                       AVG(profit_loss_percent) as avg_return,
                       SUM(profit_loss) as total_profit_loss
                FROM user_positions
                WHERE user_id = ? AND status = 'closed'
            ''', (user_id,))
            stats = dict(cursor.fetchone())
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"獲取績效統計失敗: {e}")
            return {}


# 全局資料庫實例
db = DatabaseManager()
