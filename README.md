# 🤖 智能加密貨幣投資助手 V2

一個具有風險管理和主動監控功能的 Telegram 加密貨幣投資顧問機器人。

## 🆕 V2 新功能

### 1. 風險屬性評估系統
- **智能問卷**：10題風險評估問卷
- **動態分類**：自動分類為保守型、穩健型、積極型
- **個性化策略**：根據風險等級提供客製化建議

### 2. 個性化進退場策略
- **保守型**：止損 -8% / 止盈 +15%
- **穩健型**：止損 -15% / 止盈 +25%
- **積極型**：止損 -25% / 止盈 +40%

### 3. 主動監控排程系統
- **定期檢查**：每 5 分鐘掃描市場狀況
- **智能通知**：
  - 保守型：每日 1 次（晚上 8 點）
  - 穩健型：每日 2 次（早上 9 點、晚上 8 點）
  - 積極型：即時通知
- **自動分析**：持倉監控 + 進場機會掃描

### 4. 持倉管理
- 記錄進場價格和數量
- 實時計算損益
- 退場信號提醒

### 5. 完整的資料庫系統
- 用戶資料持久化
- 風險屬性歷史記錄
- 交易信號追蹤
- 通知記錄管理

## 📋 指令列表

### 🆕 風險管理
- `/risk_profile` - 開始風險屬性評估（10題問卷）
- `/my_profile` - 查看當前風險屬性
- `/analyze [幣種]` - 分析進場時機（預設 BTC/USDT）
- `/positions` - 查看我的持倉
- `/add_position <幣種> <價格> <數量>` - 新增持倉

### 💰 行情查詢
- `/price [幣種]` - 查詢加密貨幣價格（支援 bitcoin, ethereum 等）
- `/news` - 獲取最新加密貨幣新聞（中文 + 英文）

### ⚙️ 設定
- `/timezone [時區]` - 設定或查看時區（例：America/New_York）

## 🏗️ 系統架構

```
webhook_server_v2.py       # 主程式（Flask + Telegram Bot）
├── database_manager.py    # 資料庫管理層
├── risk_assessment.py     # 風險評估模組
├── trading_strategy.py    # 交易策略引擎
├── market_monitor.py      # 市場監控排程
└── database_schema.sql    # 資料庫結構
```

## 📊 資料庫設計

### 核心表格
1. **users** - 用戶基本資料
2. **user_risk_profiles** - 風險屬性記錄
3. **risk_assessment_answers** - 問卷答案
4. **user_positions** - 持倉記錄
5. **trading_signals** - 交易信號
6. **notification_logs** - 通知記錄
7. **market_snapshots** - 市場數據快照
8. **market_watchlist** - 監控列表

## 🚀 部署步驟

### 1. 環境變數設定
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export COINGECKO_API_KEY="your_api_key"  # 可選
export PORT=5000
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 初始化資料庫
```bash
# 資料庫會在首次啟動時自動初始化
```

### 4. 啟動服務
```bash
python webhook_server_v2.py
```

### 5. 設定 Webhook
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/webhook"}'
```

## 🔧 配置說明

### 監控間隔
在 `market_monitor.py` 中修改：
```python
self.check_interval = 300  # 秒（預設 5 分鐘）
```

### 預設監控幣種
在 `market_monitor.py` 中修改：
```python
self.default_symbols = ['BTC/USDT', 'ETH/USDT']
```

### 通知上限
在 `database_schema.sql` 中修改：
```sql
INSERT INTO system_config VALUES('max_notifications_per_day', '10', ...)
```

## 📈 使用流程

### 新用戶上手
1. 發送 `/start` 查看功能介紹
2. 使用 `/risk_profile` 完成風險評估（回答 10 題）
3. 系統自動開啟智能監控服務
4. 使用 `/add_position` 新增持倉追蹤
5. 等待系統主動發送進退場提醒

### 進場決策
1. 使用 `/analyze BTC/USDT` 分析進場時機
2. 系統會根據您的風險等級給出建議
3. 顯示信心度和分析依據
4. 如果進場，使用 `/add_position` 記錄

### 持倉管理
1. 使用 `/positions` 查看當前持倉
2. 系統會定期檢查並發送退場信號
3. 達到止損/止盈時會主動通知

## 🎯 策略參數

### 保守型策略
**進場條件：**
- RSI < 40（超賣區）
- 成交量 > 1.5x 平均
- MA50 > MA200（上漲趨勢）
- 新聞情緒 > 60%

**退場條件：**
- 止損：-8%
- 止盈：+15%
- RSI > 70

### 穩健型策略
**進場條件：**
- RSI 30-50
- 成交量 > 1.3x 平均
- MACD 金叉
- 新聞情緒 > 50%

**退場條件：**
- 止損：-15%
- 止盈：+25%
- RSI > 75 或 MACD 死叉

### 積極型策略
**進場條件：**
- RSI < 30 或 RSI > 60（突破）
- 成交量 > 2x 平均
- 價格突破關鍵壓力
- 新聞情緒 > 45%

**退場條件：**
- 止損：-25%
- 止盈：+40%
- RSI > 80 或成交量萎縮

## 🔒 安全性

- 所有用戶資料存儲在本地 SQLite 資料庫
- 不存儲敏感的交易所 API 金鑰
- 僅追蹤持倉記錄，不執行實際交易
- 所有通知記錄可追溯和審計

## 📝 更新日誌

### V2.0.0 (2024-01-30)
- ✅ 新增風險屬性評估系統
- ✅ 個性化進退場策略
- ✅ 主動監控排程系統
- ✅ 持倉管理功能
- ✅ 完整的資料庫持久化

### V1.0.0 (2024-01-29)
- ✅ 價格查詢（多重 fallback）
- ✅ 新聞訂閱（中英文）
- ✅ 時區設定

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## ⚠️ 免責聲明

本機器人僅供教育和研究用途。所有投資建議僅供參考，不構成實際投資建議。加密貨幣投資具有高風險，請謹慎評估自身風險承受能力。
