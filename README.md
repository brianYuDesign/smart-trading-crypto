# 🤖 智能加密貨幣投資助手

一個功能完整的 Telegram 加密貨幣資訊機器人，提供即時市場數據、新聞、技術分析和價格提醒。

## ✨ 主要功能

### 📊 市場資訊
- **即時價格查詢**：支援多重數據源（CoinGecko + Binance）
- **市值排名**：查看 Top N 加密貨幣
- **新聞訂閱**：中英文加密貨幣新聞（RSS 整合）

### 🔍 分析工具
- **技術分析**：基於多項指標的交易建議
  - RSI (相對強弱指標)
  - 移動平均線
  - 成交量分析
  - MACD 指標

### 🔔 價格提醒
- **自訂價格通知**：設定目標價格自動提醒
- **高價/低價警報**：當價格突破設定值時通知
- **提醒管理**：查看和刪除現有提醒

---

## 📋 完整指令列表

### 🚀 基礎指令
| 指令 | 說明 |
|------|------|
| `/start` | 開始使用 Bot |
| `/help` | 顯示指令說明 |

### 📊 市場資訊
| 指令 | 說明 | 範例 |
|------|------|------|
| `/price [幣種]` | 查詢即時價格 | `/price BTC` |
| `/top [數量]` | 市值排名（預設前10名） | `/top 5` |
| `/news [幣種]` | 最新加密貨幣新聞 | `/news ETH` |

### 🔍 分析工具
| 指令 | 說明 | 範例 |
|------|------|------|
| `/analyze [幣種]` | 技術分析與交易建議 | `/analyze BTC` |

### 🔔 價格提醒
| 指令 | 說明 | 範例 |
|------|------|------|
| `/alert [幣種] [目標價] [high/low]` | 設定價格提醒 | `/alert BTC 50000 high` |
| `/myalerts` | 查看所有提醒 | `/myalerts` |
| `/del_alert [ID]` | 刪除提醒 | `/del_alert 1` |

---

## 🛠️ 技術架構

### 核心技術
- **Python 3.9+**
- **Flask** - Webhook 服務器
- **SQLite** - 數據持久化
- **APScheduler** - 定時任務調度

### API 整合
- **Telegram Bot API** - 訊息收發
- **CoinGecko API** - 主要價格數據源
- **Binance API** - 備用價格數據源
- **Google News RSS** - 新聞訂閱

### 數據結構
```
database.db
├── users - 用戶資料
├── alerts - 價格提醒
└── alert_history - 提醒歷史記錄
```

---

## 🚀 快速開始

### 1. 環境設定

```bash
# 克隆專案
git clone https://github.com/brianYuDesign/smart-trading-crypto.git
cd smart-trading-crypto

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境變數

創建 `.env` 檔案：

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
COINGECKO_API_KEY=your_coingecko_api_key  # 可選，提升請求限制
```

### 3. 啟動應用

```bash
python main.py
```

### 4. 設定 Webhook

```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/webhook"}'
```

---

## 📦 專案結構

```
smart-trading-crypto/
├── src/
│   ├── server.py           # Flask webhook 服務器
│   ├── database.py         # 資料庫操作
│   ├── trading_strategy.py # 交易策略邏輯
│   └── market_monitor.py   # 市場監控調度器
├── main.py                 # 應用入口
├── requirements.txt        # Python 依賴
├── .env                    # 環境變數（需自行創建）
└── README.md
```

---

## 🔄 版本更新日誌

### v2.0.0 (2026-01-31)
- ✅ 簡化功能，聚焦核心價值
- ✅ 移除風險評估系統（過於複雜）
- ✅ 移除持倉管理功能（與核心定位不符）
- ✅ 優化指令結構和使用體驗
- ✅ 更新文檔和說明

### v1.x 
- ✅ 基礎價格查詢功能
- ✅ 新聞訂閱整合
- ✅ 技術分析工具
- ✅ 價格提醒功能

---

## 📝 使用範例

### 查詢比特幣價格
```
用戶: /price BTC
Bot: 
💰 Bitcoin (BTC)
價格: $45,234.56
24h 漲跌: +2.34%
數據來源: CoinGecko
```

### 獲取技術分析
```
用戶: /analyze ETH
Bot:
📊 以太坊 (ETH) 技術分析

當前價格: $2,543.21
24h 漲跌: +1.23%

技術指標：
• RSI: 65 (中性偏多)
• MA(50): $2,450 (價格在均線上方 ✅)
• 成交量: 高於平均

💡 建議: 觀望，等待更明確信號
```

### 設定價格提醒
```
用戶: /alert BTC 50000 high
Bot:
✅ 價格提醒已設定

幣種: BTC
目標價: $50,000
類型: 突破高點
當前價: $45,234

當 BTC 價格 ≥ $50,000 時將通知您
```

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📄 授權

MIT License

---

## 📧 聯絡方式

如有問題或建議，請透過 GitHub Issues 聯繫。

---

## ⚠️ 免責聲明

本機器人提供的資訊僅供參考，不構成任何投資建議。加密貨幣投資具有高風險，請謹慎決策。
