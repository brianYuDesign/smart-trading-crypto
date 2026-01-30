-- =====================================================
-- 智能加密貨幣投資助手 - 資料庫架構
-- =====================================================

-- 用戶基本資料表
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language_code TEXT DEFAULT 'zh-TW'
);

-- 用戶風險屬性表
CREATE TABLE IF NOT EXISTS user_risk_profiles (
    user_id INTEGER PRIMARY KEY,
    risk_level TEXT NOT NULL CHECK(risk_level IN ('conservative', 'moderate', 'aggressive')),
    risk_score INTEGER NOT NULL,
    investment_experience TEXT,
    monthly_income_range TEXT,
    investment_ratio TEXT,
    loss_tolerance TEXT,
    investment_horizon TEXT,
    market_volatility_reaction TEXT,
    knowledge_level TEXT,
    investment_goal TEXT,
    liquidity_need TEXT,
    leverage_attitude TEXT,
    questionnaire_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 持倉記錄表
CREATE TABLE IF NOT EXISTS positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_price REAL,
    exit_time TIMESTAMP,
    profit_loss REAL,
    profit_loss_percent REAL,
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 價格提醒表
CREATE TABLE IF NOT EXISTS price_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    target_price REAL NOT NULL,
    condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'triggered', 'cancelled')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 監控排程記錄表
CREATE TABLE IF NOT EXISTS monitor_schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    last_check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_check_time TIMESTAMP NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 通知歷史記錄表
CREATE TABLE IF NOT EXISTS notification_history (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('market_alert', 'price_alert', 'strategy_signal', 'risk_warning')),
    symbol TEXT,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_status INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 交易策略分析記錄表
CREATE TABLE IF NOT EXISTS strategy_analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    analysis_type TEXT NOT NULL CHECK(analysis_type IN ('entry', 'exit', 'hold')),
    price REAL NOT NULL,
    recommendation TEXT NOT NULL,
    confidence_score REAL,
    risk_factors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 索引優化
CREATE INDEX IF NOT EXISTS idx_positions_user ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_price_alerts_user ON price_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_price_alerts_status ON price_alerts(status);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_monitor_schedule_user ON monitor_schedule(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_analysis_user ON strategy_analysis(user_id);
