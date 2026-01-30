-- =====================================================
-- 智能加密貨幣投資助手 - V2 資料庫架構
-- =====================================================

-- 1. 用戶基本資料表
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT DEFAULT 'zh-TW',
    timezone TEXT DEFAULT 'Asia/Taipei',
    is_active INTEGER DEFAULT 1,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 用戶風險屬性表
CREATE TABLE IF NOT EXISTS user_risk_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    risk_level INTEGER CHECK(risk_level IN (1, 2, 3, 4)), -- 1:保守, 2:穩健, 3:積極, 4:激進
    risk_score INTEGER NOT NULL,
    max_loss_tolerance REAL,
    notification_frequency TEXT DEFAULT '4h',
    is_current INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. 風險評估問卷答案表
CREATE TABLE IF NOT EXISTS risk_assessment_answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    answer_option TEXT NOT NULL,
    score INTEGER NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES user_risk_profiles(profile_id)
);

-- 4. 用戶持倉表 (V2)
CREATE TABLE IF NOT EXISTS user_positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,
    entry_reason TEXT,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_price REAL,
    exit_time TIMESTAMP,
    exit_reason TEXT,
    profit_loss REAL,
    profit_loss_percent REAL,
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 5. 交易信號記錄表
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL, -- entry, exit
    risk_level INTEGER,
    price REAL,
    rsi REAL,
    volume_ratio REAL,
    news_sentiment REAL,
    recommendation TEXT,
    confidence REAL,
    was_notified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 6. 通知日誌表
CREATE TABLE IF NOT EXISTS notification_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL, -- entry, exit, summary, etc.
    symbol TEXT,
    message TEXT,
    priority TEXT DEFAULT 'normal',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 7. 市場監控清單
CREATE TABLE IF NOT EXISTS market_watchlist (
    watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    alert_type TEXT, -- price, rsi, volatility
    alert_condition TEXT, -- >, <, cross_up, cross_down
    threshold_value REAL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 8. 市場數據快照 (用於計算指標)
CREATE TABLE IF NOT EXISTS market_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL,
    volume_24h REAL,
    price_change_24h REAL,
    rsi_14 REAL,
    ma_50 REAL,
    ma_200 REAL,
    news_sentiment REAL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 訂閱管理 (V1 兼容)
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    symbol TEXT,
    condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

-- 索引優化
CREATE INDEX IF NOT EXISTS idx_positions_user ON user_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON user_positions(status);
CREATE INDEX IF NOT EXISTS idx_signals_user ON trading_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON market_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_symbol ON market_snapshots(symbol, captured_at);
