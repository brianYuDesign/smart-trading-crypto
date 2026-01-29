import sqlite3
import json
import os
from datetime import datetime

class UserManager:
    def __init__(self, db_path='data/users.db'):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
        
    def _ensure_db_dir(self):
        """確保數據庫目錄存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
    def _init_db(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # 用戶表
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP
                )
            ''')
            # 訂閱表
            c.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symbol TEXT,
                    condition TEXT,
                    created_at TIMESTAMP,
                    UNIQUE(user_id, symbol)
                )
            ''')
            conn.commit()
    
    def update_user(self, user_data):
        """更新或創建用戶"""
        user_id = user_data.get('id')
        if not user_id:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                datetime.now().isoformat()
            ))
            conn.commit()
            
    def add_subscription(self, user_id, symbol, condition=None):
        """添加訂閱"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT OR REPLACE INTO subscriptions (user_id, symbol, condition, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id,
                    symbol.upper(),
                    condition,
                    datetime.now().isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding subscription: {e}")
            return False
            
    def remove_subscription(self, user_id, symbol):
        """移除訂閱"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                DELETE FROM subscriptions 
                WHERE user_id = ? AND symbol = ?
            ''', (user_id, symbol.upper()))
            conn.commit()
            return c.rowcount > 0
            
    def get_user_subscriptions(self, user_id):
        """獲取用戶訂閱列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''
                SELECT symbol, condition, created_at 
                FROM subscriptions 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = c.fetchall()
            return [dict(row) for row in rows]
            
    def get_all_subscriptions(self):
        """獲取所有訂閱（用於監控）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''
                SELECT user_id, symbol, condition 
                FROM subscriptions
            ''')
            rows = c.fetchall()
            return [dict(row) for row in rows]
