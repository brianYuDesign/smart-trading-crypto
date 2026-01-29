# Smart Trading Crypto

智能加密貨幣交易系統 - 自動分析市場並透過 Telegram 發送交易信號通知

## 功能特色

- 📊 **技術分析**: 使用多種技術指標分析市場趨勢
- 📰 **新聞監控**: 自動過濾重大新聞事件（川普相關、黑天鵝事件）
- 🔔 **即時通知**: 透過 Telegram 推送交易信號
- 🤖 **自動化運行**: 使用 GitHub Actions 定期執行
- 🛡️ **風險管理**: 在高波動期間暫停交易信號

## 系統架構

```
smart-trading-crypto/
├── src/
│   ├── market_analyzer.py      # 市場數據分析
│   ├── news_monitor.py          # 新聞監控
│   ├── signal_generator.py      # 交易信號生成
│   └── notifier.py              # Telegram 通知
├── config/
│   └── config.yaml              # 配置文件
├── .github/
│   └── workflows/
│       └── trading_bot.yml      # GitHub Actions 工作流
├── requirements.txt
└── main.py                      # 主程序入口
```

## 快速開始

### 📋 前置準備

1. **幣安 API Key**: 前往 [幣安 API 管理](https://www.binance.com/zh-TW/my/settings/api-management) 創建（只需讀取權限）
2. **Telegram Bot**: 與 [@BotFather](https://t.me/botfather) 對話創建 Bot
3. **Telegram Chat ID**: 與 [@userinfobot](https://t.me/userinfobot) 對話取得你的 Chat ID

### 🚀 部署到 GitHub Actions（推薦）

**詳細步驟請參考 [DEPLOYMENT.md](DEPLOYMENT.md)**

快速摘要：
1. Fork 或上傳此專案到 GitHub
2. 在 Repository Settings > Secrets 中設定 API Keys
3. 將 `github-workflows/trading_bot.yml` 移動到 `.github/workflows/` 目錄
4. Push 到 GitHub，系統會自動開始運行

### 💻 本地測試

```bash
# 克隆專案
git clone https://github.com/yourusername/smart-trading-crypto.git
cd smart-trading-crypto

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 複製環境變數範本並填入你的憑證
cp env.example .env
# 編輯 .env 文件，填入你的 API Keys

# 或直接設定環境變數
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id

# 執行
python main.py
```

### ⚙️ 自訂配置

編輯 `config/config.yaml` 來調整：
- 監控的交易對（預設 BTCUSDT）
- 技術指標參數（RSI、MACD、布林帶）
- 風險控制閾值
- 新聞關鍵字過濾
- 通知頻率

## 交易策略

### 進場信號
- RSI < 30（超賣）且價格突破布林帶下軌反彈
- MACD 金叉且成交量放大
- 無重大新聞事件干擾

### 出場信號
- RSI > 70（超買）
- MACD 死叉
- 檢測到高風險新聞事件

### 風險控制
- 川普相關新聞發布後暫停 24 小時
- 重大經濟數據公布前後 2 小時暫停
- 市場波動率超過閾值時暫停

## 部署到 GitHub Actions

專案已配置 GitHub Actions，會自動：
- 每 15 分鐘執行一次市場分析
- 每小時檢查新聞事件
- 發現交易信號時立即通知

## 注意事項

⚠️ **第一階段**: 目前僅提供交易信號通知，不會自動執行交易
⚠️ **風險提示**: 加密貨幣交易具有高風險，請謹慎決策
⚠️ **測試建議**: 建議先在測試網環境驗證策略效果

## 未來規劃

- [ ] 自動下單功能
- [ ] 多幣種支持
- [ ] 機器學習模型優化
- [ ] 回測系統
- [ ] Web 儀表板

## License

MIT
