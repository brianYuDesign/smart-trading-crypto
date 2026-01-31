# 🤖 智能加密貨幣投資助手 V2

一個具有風險管理和主動監控功能的 Telegram 加密貨幣投資顧問機器人。

## 🆕 V2 新功能

### 1. 風險屬性評估系統
- **智能問卷**：10題風險評估問卷
- **動態分類**：自動分類為保守型、穩健型、積極型
- **個性化策略**：根據風險等級提供客製化建議
- **持久化儲存**：評估結果自動保存到資料庫

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
- **新增持倉**：輕鬆追蹤投資組合
- **刪除持倉**：靈活管理持倉記錄

### 5. 完整的資料庫系統
- 用戶資料持久化
- 風險屬性歷史記錄
- 交易信號追蹤
- 通知記錄管理

## 📋 完整指令列表

### 🚀 基礎指令
- `/start` - 開始使用 Bot，顯示歡迎訊息
- `/help` - 顯示所有可用指令和說明

### 🎯 風險管理
- `/risk_profile` - 開始風險評估問卷，評估你的投資風險屬性
- `/my_profile` - 查看你的風險評估結果和投資建議

### 💼 持倉管理
- `/positions` - 查看當前所有持倉和盈虧狀況
- `/add_position <幣種> <數量> <買入價>` - 新增加密貨幣持倉
  - 範例：`/add_position BTC 0.5 45000`
- `/delete_position <幣種>` - 刪除指定的持倉記錄
  - 範例：`/delete_position BTC`

### 📊 市場資訊
- `/price <幣種>` - 查詢指定加密貨幣的當前價格
  - 範例：`/price BTC`
- `/top [數量]` - 查看市值排名前 N 的加密貨幣（預設 10）
  - 範例：`/top 5`
- `/news [幣種]` - 獲取最新的加密貨幣新聞
  - 範例：`/news BTC`

### 🔍 分析工具
- `/analyze <幣種>` - 分析指定加密貨幣的技術指標和趨勢
  - 範例：`/analyze ETH`

### 🔔 價格提醒
- `/alert <幣種> <目標價> <high/low>` - 設定價格提醒，當達到目標價時通知
  - 範例：`/alert BTC 50000 high`
- `/myalerts` - 查看所有已設定的價格提醒
- `/del_alert <提醒ID>` - 刪除指定的價格提醒
  - 範例：`/del_alert 1`

## 🏗️ 系統架構

```
src/
├── server.py              # 主程式（Flask + Telegram Bot）
├── database.py            # 資料庫管理層
├── risk_assessment.py     # 風險評估模組
├── trading_strategy.py    # 交易策略引擎
└── market_monitor.py      # 市場監控排程
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
python src/server.py
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
在資料庫配置中修改：
```sql
INSERT INTO system_config VALUES('max_notifications_per_day', '10', ...)
```

## 📈 使用流程

### 新用戶上手
1. 發送 `/start` 查看功能介紹
2. 使用 `/risk_profile` 完成風險評估（回答 10 題）
3. 系統自動保存評估結果，開啟智能監控服務
4. 使用 `/add_position` 新增持倉追蹤
5. 等待系統主動發送進退場提醒

### 進場決策
1. 使用 `/analyze BTC` 分析進場時機
2. 系統會根據您的風險等級給出建議
3. 顯示信心度和分析依據
4. 如果進場，使用 `/add_position BTC 0.5 45000` 記錄

### 持倉管理
1. 使用 `/positions` 查看當前持倉
2. 系統會定期檢查並發送退場信號
3. 達到止損/止盈時會主動通知
4. 使用 `/delete_position BTC` 移除已平倉的記錄

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

### V2.1.0 (2026-01-31)
- ✅ 修復風險評估結果未儲存的問題
- ✅ 新增 `/delete_position` 持倉刪除功能
- ✅ 更新完整的指令列表和說明
- ✅ 優化 `/help` 指令內容

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
