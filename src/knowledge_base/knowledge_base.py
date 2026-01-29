"""
市場知識庫系統
存儲和管理加密貨幣市場知識、歷史事件、交易模式
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class MarketKnowledgeBase:
    """市場知識庫管理器"""
    
    def __init__(self, db_path: str = 'data/knowledge_base/market_knowledge.db'):
        """
        初始化知識庫
        
        Args:
            db_path: 數據庫文件路徑
        """
        self.db_path = db_path
        
        # 確保目錄存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化數據庫
        self._init_database()
        
        logger.info(f"MarketKnowledgeBase initialized at {db_path}")
    
    def _init_database(self):
        """初始化數據庫表結構"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 歷史事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    impact_level TEXT,
                    affected_coins TEXT,
                    market_reaction TEXT,
                    price_change_24h REAL,
                    volume_change_24h REAL,
                    sentiment TEXT,
                    source_url TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. 交易模式表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT NOT NULL UNIQUE,
                    pattern_type TEXT NOT NULL,
                    description TEXT,
                    success_rate REAL,
                    avg_return REAL,
                    timeframe TEXT,
                    conditions TEXT,
                    entry_rules TEXT,
                    exit_rules TEXT,
                    risk_level TEXT,
                    example_charts TEXT,
                    occurrences INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. 幣種知識表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coin_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_id TEXT NOT NULL UNIQUE,
                    symbol TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT,
                    description TEXT,
                    technology TEXT,
                    use_cases TEXT,
                    key_features TEXT,
                    team_info TEXT,
                    partnerships TEXT,
                    roadmap TEXT,
                    risks TEXT,
                    correlations TEXT,
                    typical_volatility REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 4. 市場相關性表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_correlations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset1 TEXT NOT NULL,
                    asset2 TEXT NOT NULL,
                    correlation_value REAL NOT NULL,
                    timeframe TEXT NOT NULL,
                    calculation_date TEXT NOT NULL,
                    data_points INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asset1, asset2, timeframe, calculation_date)
                )
            """)
            
            # 5. 市場狀態快照表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date TEXT NOT NULL,
                    btc_price REAL,
                    btc_dominance REAL,
                    total_market_cap REAL,
                    total_volume_24h REAL,
                    fear_greed_index INTEGER,
                    top_10_avg_change REAL,
                    trending_coins TEXT,
                    major_events TEXT,
                    overall_sentiment TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. 專家規則表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL UNIQUE,
                    rule_type TEXT NOT NULL,
                    description TEXT,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    enabled BOOLEAN DEFAULT 1,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 7. 新聞歸檔表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id TEXT UNIQUE,
                    published_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT,
                    url TEXT,
                    content TEXT,
                    sentiment TEXT,
                    importance_score REAL,
                    affected_coins TEXT,
                    categories TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized")
    
    # ==================== 歷史事件管理 ====================
    
    def add_historical_event(self, event: Dict) -> int:
        """
        添加歷史事件
        
        Args:
            event: 事件數據字典
        
        Returns:
            事件 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO historical_events 
                (event_date, event_type, title, description, impact_level, 
                 affected_coins, market_reaction, price_change_24h, volume_change_24h,
                 sentiment, source_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get('event_date'),
                event.get('event_type'),
                event.get('title'),
                event.get('description'),
                event.get('impact_level'),
                json.dumps(event.get('affected_coins', [])),
                event.get('market_reaction'),
                event.get('price_change_24h'),
                event.get('volume_change_24h'),
                event.get('sentiment'),
                event.get('source_url'),
                json.dumps(event.get('tags', []))
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added historical event: {event.get('title')} (ID: {event_id})")
            return event_id
    
    def get_similar_historical_events(self, 
                                      event_type: str,
                                      days_back: int = 365) -> List[Dict]:
        """
        查找相似歷史事件
        
        Args:
            event_type: 事件類型
            days_back: 回溯天數
        
        Returns:
            相似事件列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT * FROM historical_events
                WHERE event_type = ? AND event_date >= ?
                ORDER BY event_date DESC
            """, (event_type, cutoff_date))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            events = []
            for row in rows:
                event = dict(zip(columns, row))
                event['affected_coins'] = json.loads(event['affected_coins'])
                event['tags'] = json.loads(event['tags'])
                events.append(event)
            
            return events
    
    # ==================== 交易模式管理 ====================
    
    def add_trading_pattern(self, pattern: Dict) -> int:
        """
        添加交易模式
        
        Args:
            pattern: 模式數據
        
        Returns:
            模式 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO trading_patterns
                    (pattern_name, pattern_type, description, success_rate, avg_return,
                     timeframe, conditions, entry_rules, exit_rules, risk_level, example_charts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.get('pattern_name'),
                    pattern.get('pattern_type'),
                    pattern.get('description'),
                    pattern.get('success_rate'),
                    pattern.get('avg_return'),
                    pattern.get('timeframe'),
                    json.dumps(pattern.get('conditions', {})),
                    json.dumps(pattern.get('entry_rules', [])),
                    json.dumps(pattern.get('exit_rules', [])),
                    pattern.get('risk_level'),
                    json.dumps(pattern.get('example_charts', []))
                ))
                
                pattern_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added trading pattern: {pattern.get('pattern_name')} (ID: {pattern_id})")
                return pattern_id
                
            except sqlite3.IntegrityError:
                logger.warning(f"Pattern already exists: {pattern.get('pattern_name')}")
                return -1
    
    def find_matching_patterns(self, market_conditions: Dict) -> List[Dict]:
        """
        根據市場條件查找匹配的交易模式
        
        Args:
            market_conditions: 當前市場條件
        
        Returns:
            匹配的模式列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM trading_patterns
                ORDER BY success_rate DESC, avg_return DESC
            """)
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            matching_patterns = []
            for row in rows:
                pattern = dict(zip(columns, row))
                pattern['conditions'] = json.loads(pattern['conditions'])
                pattern['entry_rules'] = json.loads(pattern['entry_rules'])
                pattern['exit_rules'] = json.loads(pattern['exit_rules'])
                pattern['example_charts'] = json.loads(pattern['example_charts'])
                
                # 簡單的條件匹配邏輯（可以更複雜）
                if self._check_pattern_conditions(pattern['conditions'], market_conditions):
                    matching_patterns.append(pattern)
            
            return matching_patterns
    
    def _check_pattern_conditions(self, pattern_conditions: Dict, market_conditions: Dict) -> bool:
        """檢查模式條件是否滿足"""
        # 簡化的條件檢查邏輯
        # 實際應用中可以更複雜，使用規則引擎
        for key, value in pattern_conditions.items():
            if key not in market_conditions:
                return False
            
            if isinstance(value, dict):
                # 範圍檢查
                min_val = value.get('min')
                max_val = value.get('max')
                market_val = market_conditions[key]
                
                if min_val is not None and market_val < min_val:
                    return False
                if max_val is not None and market_val > max_val:
                    return False
            else:
                # 精確匹配
                if market_conditions[key] != value:
                    return False
        
        return True
    
    # ==================== 幣種知識管理 ====================
    
    def add_coin_knowledge(self, coin_data: Dict) -> int:
        """
        添加或更新幣種知識
        
        Args:
            coin_data: 幣種知識數據
        
        Returns:
            記錄 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO coin_knowledge
                (coin_id, symbol, name, category, description, technology, use_cases,
                 key_features, team_info, partnerships, roadmap, risks, correlations, typical_volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                coin_data.get('coin_id'),
                coin_data.get('symbol'),
                coin_data.get('name'),
                coin_data.get('category'),
                coin_data.get('description'),
                coin_data.get('technology'),
                json.dumps(coin_data.get('use_cases', [])),
                json.dumps(coin_data.get('key_features', [])),
                json.dumps(coin_data.get('team_info', {})),
                json.dumps(coin_data.get('partnerships', [])),
                json.dumps(coin_data.get('roadmap', [])),
                json.dumps(coin_data.get('risks', [])),
                json.dumps(coin_data.get('correlations', {})),
                coin_data.get('typical_volatility')
            ))
            
            coin_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added/updated coin knowledge: {coin_data.get('name')} (ID: {coin_id})")
            return coin_id
    
    def get_coin_knowledge(self, coin_id: str) -> Optional[Dict]:
        """
        獲取幣種知識
        
        Args:
            coin_id: 幣種 ID
        
        Returns:
            幣種知識數據
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM coin_knowledge WHERE coin_id = ?
            """, (coin_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            coin_data = dict(zip(columns, row))
            
            # 解析 JSON 字段
            coin_data['use_cases'] = json.loads(coin_data['use_cases'])
            coin_data['key_features'] = json.loads(coin_data['key_features'])
            coin_data['team_info'] = json.loads(coin_data['team_info'])
            coin_data['partnerships'] = json.loads(coin_data['partnerships'])
            coin_data['roadmap'] = json.loads(coin_data['roadmap'])
            coin_data['risks'] = json.loads(coin_data['risks'])
            coin_data['correlations'] = json.loads(coin_data['correlations'])
            
            return coin_data
    
    # ==================== 市場相關性管理 ====================
    
    def save_correlation(self, asset1: str, asset2: str, 
                        correlation: float, timeframe: str,
                        data_points: int):
        """
        保存資產相關性數據
        
        Args:
            asset1: 資產1
            asset2: 資產2
            correlation: 相關係數 (-1 到 1)
            timeframe: 時間範圍
            data_points: 數據點數量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            calc_date = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT OR REPLACE INTO market_correlations
                (asset1, asset2, correlation_value, timeframe, calculation_date, data_points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset1, asset2, correlation, timeframe, calc_date, data_points))
            
            conn.commit()
            
            logger.info(f"Saved correlation: {asset1} vs {asset2} = {correlation:.3f}")
    
    def get_correlations(self, asset: str, timeframe: str = '30d') -> List[Dict]:
        """
        獲取資產的相關性數據
        
        Args:
            asset: 資產名稱
            timeframe: 時間範圍
        
        Returns:
            相關性列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM market_correlations
                WHERE (asset1 = ? OR asset2 = ?) AND timeframe = ?
                ORDER BY ABS(correlation_value) DESC
            """, (asset, asset, timeframe))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            correlations = []
            for row in rows:
                corr_data = dict(zip(columns, row))
                correlations.append(corr_data)
            
            return correlations
    
    # ==================== 市場快照管理 ====================
    
    def save_market_snapshot(self, snapshot: Dict):
        """
        保存市場狀態快照
        
        Args:
            snapshot: 市場快照數據
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO market_snapshots
                (snapshot_date, btc_price, btc_dominance, total_market_cap, total_volume_24h,
                 fear_greed_index, top_10_avg_change, trending_coins, major_events, overall_sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.get('snapshot_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                snapshot.get('btc_price'),
                snapshot.get('btc_dominance'),
                snapshot.get('total_market_cap'),
                snapshot.get('total_volume_24h'),
                snapshot.get('fear_greed_index'),
                snapshot.get('top_10_avg_change'),
                json.dumps(snapshot.get('trending_coins', [])),
                json.dumps(snapshot.get('major_events', [])),
                snapshot.get('overall_sentiment')
            ))
            
            conn.commit()
            logger.info(f"Saved market snapshot for {snapshot.get('snapshot_date')}")
    
    def get_historical_snapshots(self, days_back: int = 30) -> List[Dict]:
        """
        獲取歷史市場快照
        
        Args:
            days_back: 回溯天數
        
        Returns:
            快照列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT * FROM market_snapshots
                WHERE snapshot_date >= ?
                ORDER BY snapshot_date DESC
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            snapshots = []
            for row in rows:
                snapshot = dict(zip(columns, row))
                snapshot['trending_coins'] = json.loads(snapshot['trending_coins'])
                snapshot['major_events'] = json.loads(snapshot['major_events'])
                snapshots.append(snapshot)
            
            return snapshots
    
    # ==================== 新聞歸檔管理 ====================
    
    def archive_news(self, news_item: Dict) -> int:
        """
        歸檔新聞
        
        Args:
            news_item: 新聞數據
        
        Returns:
            新聞 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO news_archive
                    (news_id, published_at, title, source, url, content, sentiment,
                     importance_score, affected_coins, categories)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news_item.get('news_id'),
                    news_item.get('published_at'),
                    news_item.get('title'),
                    news_item.get('source'),
                    news_item.get('url'),
                    news_item.get('content'),
                    news_item.get('sentiment'),
                    news_item.get('importance_score'),
                    json.dumps(news_item.get('affected_coins', [])),
                    json.dumps(news_item.get('categories', []))
                ))
                
                news_id = cursor.lastrowid
                conn.commit()
                
                return news_id
                
            except sqlite3.IntegrityError:
                # 新聞已存在
                return -1
    
    def search_news(self, 
                   keywords: Optional[List[str]] = None,
                   sentiment: Optional[str] = None,
                   days_back: int = 7) -> List[Dict]:
        """
        搜索歸檔新聞
        
        Args:
            keywords: 關鍵字列表
            sentiment: 情緒過濾
            days_back: 回溯天數
        
        Returns:
            新聞列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            query = "SELECT * FROM news_archive WHERE published_at >= ?"
            params = [cutoff_date]
            
            if sentiment:
                query += " AND sentiment = ?"
                params.append(sentiment)
            
            if keywords:
                keyword_conditions = " OR ".join(["title LIKE ?" for _ in keywords])
                query += f" AND ({keyword_conditions})"
                params.extend([f"%{kw}%" for kw in keywords])
            
            query += " ORDER BY published_at DESC LIMIT 100"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            news_items = []
            for row in rows:
                news = dict(zip(columns, row))
                news['affected_coins'] = json.loads(news['affected_coins'])
                news['categories'] = json.loads(news['categories'])
                news_items.append(news)
            
            return news_items


# 示例使用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 初始化知識庫
    kb = MarketKnowledgeBase()
    
    # 添加歷史事件
    event = {
        'event_date': '2026-01-15',
        'event_type': 'regulation',
        'title': 'SEC approves Bitcoin ETF',
        'description': 'SEC approved multiple Bitcoin ETF applications',
        'impact_level': 'critical',
        'affected_coins': ['BTC', 'ETH'],
        'market_reaction': 'positive',
        'price_change_24h': 15.5,
        'volume_change_24h': 230.0,
        'sentiment': 'positive',
        'source_url': 'https://example.com/news',
        'tags': ['ETF', 'regulation', 'bullish']
    }
    kb.add_historical_event(event)
    
    # 添加交易模式
    pattern = {
        'pattern_name': 'Bull Flag Breakout',
        'pattern_type': 'continuation',
        'description': '牛旗突破形態',
        'success_rate': 0.72,
        'avg_return': 0.15,
        'timeframe': '4h',
        'conditions': {
            'rsi': {'min': 50, 'max': 70},
            'volume_ratio': {'min': 1.5},
            'trend': 'uptrend'
        },
        'entry_rules': ['突破旗型上沿', '成交量放大'],
        'exit_rules': ['達到目標位', 'RSI 超買'],
        'risk_level': 'medium'
    }
    kb.add_trading_pattern(pattern)
    
    print("Knowledge base demo completed!")
