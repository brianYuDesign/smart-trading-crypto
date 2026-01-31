# 🤖 智能加密貨幣投資助手

一個功能完整的 Telegram 加密貨幣資訊機器人，提供即時市場數據、新聞、AI 趨勢預測、技術分析和價格提醒。

## ✨ 主要功能

### 📊 市場資訊
- **即時價格查詢**：支援多重數據源（CoinGecko + Binance）
- **市值排名**：查看 Top 10 加密貨幣
- **新聞訂閱**：中英文加密貨幣新聞（RSS 整合）

### 🤖 AI 智能分析
- **新聞情緒分析**：基於關鍵字分析新聞情緒
- **趨勢預測**：AI 預測市場走勢（看漲/看跌/中性）
- **操作建議**：根據市場情緒提供交易建議

### 🔍 技術分析工具
- **多指標分析**：基於多項技術指標的交易建議
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
| `/top` | 市值排名前 10 名 | `/top` |
| `/news` | 最新加密貨幣新聞 | `/news` |

### 🤖 AI 分析工具
| 指令 | 說明 | 範例 |
|------|------|------|
| `/trend` | AI 整體市場趨勢預測 | `/trend` |
| `/trend [幣種]` | 分析特定幣種趨勢 | `/trend ETH` |
| `/analyze [幣種]` | 技術指標分析 | `/analyze BTC` |

### 🔔 價格提醒
| 指令 | 說明 | 範例 |
|------|------|------|
| `/alert [幣種] [目標價] [high/low]` | 設定價格提醒 | `/alert BTC 50000 high` |
| `/myalerts` | 查看所有提醒 | `/myalerts` |
| `/del_alert [ID]` | 刪除提醒 | `/del_alert 1` |

---

## 🎯 AI 趨勢預測功能說明

### 工作原理
1. **新聞採集**：從多個加密貨幣新聞源抓取最新資訊
2. **情緒分析**：使用關鍵字分析每條新聞的情緒傾向
   - 看漲關鍵字：surge, rally, bullish, growth, 上漲, 看漲, 突破等
   - 看跌關鍵字：crash, drop, bearish, decline, 下跌, 看跌, 暴跌等
3. **整體評分**：計算所有新聞的情緒總分
4. **趨勢判斷**：
   - 強烈看漲 (分數 > 2)
   - 溫和看漲 (分數 > 0)
   - 市場中性 (分數 = 0)
   - 溫和看跌 (分數 < 0)
   - 強烈看跌 (分數 < -2)

### 使用範例

**查看整體市場趨勢：**
```
/trend
```
返回：
- 整體趨勢判斷
- 情緒指數
- 操作建議
- 前 5 條相關新聞及情緒標籤

**查看特定幣種趨勢：**
```
/trend BTC
```
只分析與 BTC 相關的新聞

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

### 2. 設定環境變數

創建 `.env` 檔案：

```env
# Telegram Bot Token (從 @BotFather 獲取)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# CoinGecko API (可選，免費版有限制)
COINGECKO_API_KEY=your_coingecko_api_key
```

### 3. 啟動機器人

```bash
python src/server.py
```

### 4. Telegram 中使用

1. 在 Telegram 搜尋你的 Bot
2. 輸入 `/start` 開始使用
3. 輸入 `/help` 查看完整指令

---

## 🏗️ 技術架構

### 核心技術
- **Python 3.8+**
- **Flask** - Web 框架
- **SQLite** - 輕量級資料庫
- **Telegram Bot API** - 機器人介面
- **CoinGecko API** - 加密貨幣數據
- **Binance API** - 備用數據源
- **RSS Feeds** - 新聞採集

### 專案結構

```
smart-trading-crypto/
├── src/
│   ├── server.py           # 主程式與 Bot 邏輯
│   ├── database.py         # 資料庫操作
│   └── __init__.py
├── requirements.txt        # Python 依賴套件
├── .env                   # 環境變數設定
└── README.md              # 專案說明文件
```

### 資料流程

```
用戶指令 → Telegram Bot → Flask Server → 
  ├─ 價格查詢 → CoinGecko/Binance API
  ├─ 新聞查詢 → RSS Feeds
  ├─ AI 趨勢 → 新聞採集 → 情緒分析 → 趨勢預測
  ├─ 技術分析 → 價格數據 → 指標計算 → 建議生成
  └─ 價格提醒 → SQLite 儲存 → 定時檢查 → 推送通知
```

---

## 📊 API 數據源

### 主要數據源
1. **CoinGecko API**
   - 即時價格
   - 市值排名
   - 24小時交易量

2. **Binance API** (備用)
   - 即時價格查詢
   - 市場深度數據

### 新聞來源
- CoinDesk (英文)
- CoinTelegraph (英文)
- BlockTempo (中文)

---

## 🔧 進階設定

### 自訂新聞源

編輯 `server.py` 中的 `NEWS_FEEDS` 字典：

```python
NEWS_FEEDS = {
    'zh': [
        'https://your-chinese-news-source.com/rss',
    ],
    'en': [
        'https://your-english-news-source.com/rss',
    ]
}
```

### 調整 AI 情緒分析

修改 `analyze_news_sentiment()` 函數中的關鍵字列表：

```python
positive_keywords = ['your', 'bullish', 'keywords']
negative_keywords = ['your', 'bearish', 'keywords']
```

### 修改趨勢判斷標準

調整 `analyze_news_sentiment()` 中的分數閾值：

```python
if sentiment_score > 3:  # 原本是 2
    overall_trend = "🚀 強烈看漲"
```

---

## 🛠️ 部署

### Render 部署 (推薦)

1. Fork 此專案到你的 GitHub
2. 在 [Render](https://render.com) 創建新的 Web Service
3. 連接你的 GitHub 倉庫
4. 設定環境變數
5. 部署完成！

### Heroku 部署

```bash
# 登入 Heroku
heroku login

# 創建應用
heroku create your-app-name

# 設定環境變數
heroku config:set TELEGRAM_BOT_TOKEN=your_token

# 推送部署
git push heroku main
```

---

## 📝 更新日誌

### v2.0.0 (最新)
- ✨ 新增 AI 新聞情緒分析功能
- ✨ 新增市場趨勢預測 (`/trend`)
- 🗑️ 移除風險評估問卷功能
- 🗑️ 移除持倉管理功能
- 📝 更新指令說明文件

### v1.1.0
- 🐛 修復 `/top` 指令錯誤
- 🐛 修復 `/analyze` 數據異常問題
- ✨ 新增多數據源支援
- ⚡ 優化價格查詢速度

### v1.0.0
- 🎉 初始版本發布
- ✅ 基礎價格查詢
- ✅ 技術分析功能
- ✅ 價格提醒功能

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發流程
1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

---

## 📧 聯絡方式

- GitHub: [@brianYuDesign](https://github.com/brianYuDesign)
- Email: brian831121@gmail.com

---

## ⚠️ 免責聲明

本機器人提供的所有資訊僅供參考，不構成任何投資建議。加密貨幣投資具有高風險，請謹慎評估後做出投資決策。

**AI 趨勢預測功能**基於新聞標題關鍵字分析，僅供參考，不保證預測準確性。實際投資請結合多方面資訊並諮詢專業人士。

---

## 🙏 致謝

- [CoinGecko](https://www.coingecko.com/) - 加密貨幣數據
- [Binance](https://www.binance.com/) - 備用數據源
- [Telegram Bot API](https://core.telegram.org/bots/api) - Bot 開發框架
- 各大加密貨幣新聞媒體

---

**⭐ 如果這個專案對你有幫助，請給個 Star！**
