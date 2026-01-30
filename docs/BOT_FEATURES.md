# Smart Trading Crypto Bot - features & operations

智能加密貨幣投資顧問 Bot，整合了風險評估、個性化策略、市場監控與即時通知功能。

## 📂 專案結構 (Project Structure)

```
project_root/
├── main.py                # 統一入口 (Unified Entry Point)
├── requirements.txt       # 依賴套件列表
├── .env                   # 環境變數配置
│
├── src/                   # 核心模組
│   ├── server.py          # Webhook Server (Flask App) - 處理 Telegram 請求
│   ├── database.py        # 資料庫管理 (SQLite) - 統一管理 Users/Subscriptions
│   ├── risk_assessment.py # 風險評估系統
│   ├── trading_strategy.py# 交易策略生成與分析
│   ├── market_monitor.py  # 市場監控與排程
│   ├── news_monitor.py    # 新聞監控模組 (Legacy/V1)
│   └── ...
│
├── data/                  # 數據存儲
│   └── crypto_bot.db      #主要 SQLite 資料庫
│
└── scripts/               # 工具腳本
    └── verify_*.py        # 各種驗證腳本
```

---

## 🎮 指令列表 (Command List)

### 🚀 基礎功能

| 指令     | 說明                 |
| :------- | :------------------- |
| `/start` | 初始化並顯示歡迎訊息 |
| `/help`  | 顯示完整指令列表     |

### 🎯 風險評估 (Risk Assessment)

| 指令            | 說明                         |
| :-------------- | :--------------------------- |
| `/risk_profile` | 開始風險屬性評估問卷         |
| `/my_profile`   | 查看目前的風險屬性與配置建議 |

### 📊 交易與分析 (Trading & Analysis)

| 指令              | 範例                         | 說明                               |
| :---------------- | :--------------------------- | :--------------------------------- |
| `/analyze [幣種]` | `/analyze BTC`               | 根據您的風險等級提供進出場策略建議 |
| `/positions`      | `/positions`                 | 查看目前的持倉損益概況             |
| `/add_position`   | `/add_position ETH 2.5 3500` | 新增持倉記錄 (幣種 數量 成本)      |

### 📰 市場資訊 (Market Info)

| 指令            | 範例         | 說明                         |
| :-------------- | :----------- | :--------------------------- |
| `/price [幣種]` | `/price SOL` | 查詢多重來源的即時價格       |
| `/top`          | `/top`       | 顯示市值前 10 名加密貨幣行情 |
| `/news`         | `/news`      | 獲取最新的加密貨幣新聞摘要   |

---

## ⚙️ 核心功能 (Key Features)

1. **風險屬性評估系統**:
   - 通過問卷分析用戶投資經驗與風險承受度。
   - 自動分類為：保守型、穩健型、積極型、激進型。

2. **個性化策略建議**:
   - 結合技術指標 (RSI, MA, MACD) 與新聞情緒。
   - 依據用戶風險等級調整止盈/止損點位建議。

3. **統一資料庫**:
   - 使用 SQLite 統一管理用戶資料、訂閱列表與交易記錄。
   - 自動遷移舊版資料結構。

4. **雙模式運行**:
   - **Webhook Mode**: 適用於生產環境，即時響應指令。
   - **Monitoring Mode**: 定時監控市場風險（如波動性、負面新聞）。

---

## 🛠 安裝與依賴 (Setup)

主要依賴 (`requirements.txt`):

- `flask`, `gunicorn`: Web Server
- `requests`, `feedparser`: 數據抓取
- `python-binance`: 交易所數據
- `schedule`: 排程任務
- `python-dotenv`: 環境變數管理
