# Smart Trading Crypto

智能加密貨幣交易系統 - 自動分析市場趨勢通過 Telegram 發送交易信號通知

## 🎯 核心功能

### 原有功能
- 📊 **技術分析**：使用多種技術指標分析市場趨勢
- 📰 **新聞監控**：自動過濾重大新聞事件（好萊塢相關、黑天鵝事件）
- 🔔 **即時通知**：透過 Telegram 發送交易信號通知
- 🤖 **自動化執行**：使用 GitHub Actions 定期執行
- 🛡️ **風險管理**：在高波動期間暫停交易信號

### 🆕 知識整合系統
- 🧠 **市場知識庫**：整合大部分幣圈相關知識和國際重大新聞
- 📈 **多維度數據源**：
  - CoinGecko API - 加密貨幣市場數據
  - CryptoPanic API - 新聞聚合和情緒分析
  - Fear & Greed Index - 市場情緒指標
- 🗄️ **智能存儲**：
  - 歷史事件記錄與模式識別
  - 交易策略成功率追蹤
  - 幣種詳細知識管理
  - 市場相關性分析
- 🔄 **自動化更新**：定期收集和更新市場數據

## 系統架構

```
smart-trading-crypto/
├── src/
│   ├── data_sources/              # 數據源整合
│   │   └── crypto_apis.py         # CoinGecko, CryptoPanic, Fear & Greed
│   ├── knowledge_base/            # 知識庫系統
│   │   └── knowledge_base.py      # 市場知識管理
│   ├── market_analyzer.py         # 市場數據分析
│   ├── news_monitor.py            # 新聞監控
│   ├── signal_generator.py        # 交易信號生成
│   └── notifier.py                # Telegram 通知
├── scripts/
│   └── knowledge_updater.py       # 知識庫自動更新
├── config/
│   ├── config.yaml                # 交易系統配置
│   └── data_sources.yaml          # 數據源配置
├── .github/
│   └── workflows/
│       ├── trading_bot.yml        # 交易機器人工作流
│       └── knowledge_update.yml   # 知識庫更新工作流（待設置）
├── requirements.txt
├── main.py                        # 主程序入口
├── INTEGRATION_GUIDE.md           # 🆕 知識整合完整指南
└── README.md
```

## 快速開始

### 📋 前置準備

1. **幣安 API Key**：前往 [幣安 API 管理](https://www.binance.com/zh-TW/my/settings/api-management) 創建（只需讀權限）
2. **Telegram Bot**：與 [@BotFather](https://t.me/botfather) 對話創建 Bot
3. **Telegram Chat ID**：與 [@userinfobot](https://t.me/userinfobot) 對話取得你的 Chat ID
4. **CryptoPanic API Key**（可選）：前往 [CryptoPanic](https://cryptopanic.com/developers/api/) 註冊

### 🚀 部署到 GitHub Actions（推薦）

**詳細步驟請參考 [DEPLOYMENT.md](DEPLOYMENT.md)**

快速摘要：
1. Fork 或上傳此專案到 GitHub
2. 在 Repository Settings > Secrets 中設定 API Keys
3. 將 `github-workflows/trading_bot.yml` 移動到 `.github/workflows/` 目錄
4. Push 到 GitHub，系統將自動開始運行

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

# 複製環境變數檔並填入你的憑證
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

## 🧠 知識整合系統使用

### 快速開始

```bash
# 1. 配置數據源
cp config/data_sources.yaml.example config/data_sources.yaml
# 編輯配置文件，填入 API Keys

# 2. 測試數據收集
python scripts/knowledge_updater.py

# 3. 查看詳細文檔
# 參考 INTEGRATION_GUIDE.md 了解完整功能和用法
```

### 主要功能

**市場概覽**
```python
from src.data_sources.crypto_apis import CryptoDataAggregator

aggregator = CryptoDataAggregator(config)
overview = aggregator.get_market_overview(['bitcoin', 'ethereum'])

print(f"比特幣價格: ${overview['coins']['bitcoin']['current_price']:,.2f}")
print(f"Fear & Greed Index: {overview['fear_greed_index']['value']}")
```

**情緒分析**
```python
sentiment = aggregator.analyze_market_sentiment()
print(f"市場情緒: {sentiment['overall_sentiment']}")
print(f"信心度: {sentiment['confidence']:.0%}")
```

**知識庫查詢**
```python
from src.knowledge_base.knowledge_base import MarketKnowledgeBase

kb = MarketKnowledgeBase()
bitcoin_info = kb.get_coin_knowledge('bitcoin')
print(f"用途: {', '.join(bitcoin_info['use_cases'])}")
```

### 📚 完整文檔

- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - 知識整合完整指南
  - 數據源配置
  - API 參考
  - 最佳實踐
  - 故障排除

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 部署指南
  - GitHub Actions 設置
  - 環境變數配置
  - 自動化執行

- **[QUICKSTART.md](QUICKSTART.md)** - 快速入門
  - 基本配置
  - 運行測試
  - 常見問題

### ⚙️ 自訂配置

編輯 `config/config.yaml` 來調整：
- 監控的交易對（預設 BTCUSDT）
- 技術指標參數（RSI、MACD、布林帶）
- 風險管理閾值
- 新聞過濾字詞
- 通知頻率

編輯 `config/data_sources.yaml` 來配置：
- 數據源 API Keys
- 更新頻率
- 數據保留策略
- 通知設置

## 交易策略

### 進場信號
- RSI < 30（超賣）且價格在布林帶下軌反彈
- MACD 金叉且成交量放大
- 無重大負面新聞事件平壓

### 出場信號
- RSI > 70（超買）
- MACD 死叉
- 檢測到高風險新聞事件

### 風險管理
- 深熊狀態暫停交易（連續下跌 > 設定閾值）
- 重大負面新聞後 24 小時暫停
- 市場波動異常時降低信號頻率

## 📊 數據源

### 市場數據
- **Binance API**：即時價格和成交量數據
- **CoinGecko API**：市場概覽和幣種詳細信息
- **技術指標**：使用 `ta` 庫計算 RSI、MACD、布林帶等

### 新聞來源
- **RSS Feeds**：多個加密貨幣新聞網站
- **CryptoPanic API**：新聞聚合和社群情緒
- **關鍵詞過濾**：自動識別重大事件

### 市場情緒
- **Fear & Greed Index**：加密貨幣市場情緒指標
- **新聞情緒分析**：基於投票和分類的情緒判斷
- **社交媒體監控**：（可選）Twitter/Reddit 情緒追蹤

## 注意事項

⚠️ **免責聲明**：
- 本系統僅供學習和研究使用
- 所有交易信號僅供參考，不構成投資建議
- 加密貨幣投資具有高風險，請謹慎決策並自負盈虧
- 使用前請充分了解技術分析的局限性

🔒 **安全提示**：
- 永遠不要將 API Keys 提交到公開的 Git repository
- Binance API Key 建議設定為只讀權限
- 定期更換 API Keys
- 使用 GitHub Secrets 或環境變數存儲敏感信息

## 常見問題

**Q: 為什麼有時候不發送信號？**  
A: 系統會在以下情況暫停發送：
- 市場處於深熊狀態（連續大跌）
- 檢測到重大負面新聞
- 最近已發送過信號（防止spam）

**Q: 如何調整信號的敏感度？**  
A: 編輯 `config/config.yaml` 中的閾值參數，例如：
- 降低 RSI 超賣值（如 25）會更保守
- 提高 RSI 超買值（如 75）會更激進

**Q: 知識庫更新失敗怎麼辦？**  
A: 檢查以下項目：
- API Keys 是否正確配置
- 網絡連接是否正常
- API 請求是否超過限制
- 查看 `INTEGRATION_GUIDE.md` 的故障排除章節

**Q: 可以在其他平台運行嗎？**  
A: 可以！本專案可以在任何支持 Python 3.8+ 的環境運行：
- 本地電腦（Windows/Mac/Linux）
- 雲端服務器（AWS/GCP/Azure）
- Raspberry Pi
- Docker 容器

## 貢獻

歡迎提交 Issues 和 Pull Requests！

## 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 聯繫方式

- GitHub Issues: [提交問題](https://github.com/brianYuDesign/smart-trading-crypto/issues)
- Email: brian831121@gmail.com

---

⭐ 如果這個專案對你有幫助，請給個 Star！
