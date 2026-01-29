# 快速入門指南

10 分鐘內讓系統運行起來！

## 步驟一：準備 API 憑證（5 分鐘）

### 1. 幣安 API Key

1. 登入 [幣安](https://www.binance.com/)
2. 點擊右上角頭像 > API Management
3. 創建新的 API Key
4. **重要**: 權限只勾選「Enable Reading」（只需讀取權限）
5. 複製並保存 `API Key` 和 `Secret Key`

### 2. Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot`
3. 輸入 Bot 名稱（例如：My Trading Bot）
4. 輸入 Bot 用戶名（例如：my_trading_bot）
5. 複製並保存 Token（格式：`1234567890:ABCdef...`）
6. **發送一條訊息給你的 Bot**（重要！否則收不到通知）

### 3. 取得 Chat ID

1. 在 Telegram 搜尋 `@userinfobot`
2. 點擊 Start 或發送任意訊息
3. 它會回覆你的 ID，複製這個數字

## 步驟二：部署到 GitHub（5 分鐘）

### 1. 上傳代碼

```bash
# 在你的電腦上
cd smart-trading-crypto

# 初始化 Git（如果還沒有）
git init
git add .
git commit -m "Initial commit"

# 連接到你的 GitHub repo
git remote add origin https://github.com/yourusername/smart-trading-crypto.git
git branch -M main
git push -u origin main
```

### 2. 設定 Secrets

1. 進入你的 GitHub Repository
2. 點擊 `Settings` > `Secrets and variables` > `Actions`
3. 點擊 `New repository secret`
4. 添加以下 4 個 secrets：

```
名稱: BINANCE_API_KEY
值: 你的幣安 API Key

名稱: BINANCE_API_SECRET
值: 你的幣安 Secret Key

名稱: TELEGRAM_BOT_TOKEN
值: 你的 Telegram Bot Token

名稱: TELEGRAM_CHAT_ID
值: 你的 Chat ID（純數字）
```

### 3. 設定 Workflow

確保文件結構如下：
```
smart-trading-crypto/
├── .github/
│   └── workflows/
│       └── trading_bot.yml  ← 從 github-workflows/ 移動到這裡
├── src/
├── config/
├── main.py
└── requirements.txt
```

執行：
```bash
# 創建目錄並移動文件
mkdir -p .github/workflows
mv github-workflows/trading_bot.yml .github/workflows/

# 提交變更
git add .github/workflows/trading_bot.yml
git commit -m "Add GitHub Actions workflow"
git push
```

### 4. 測試運行

1. 進入 GitHub Repository 的 `Actions` 頁面
2. 如果看到提示，點擊啟用 Actions
3. 點擊 `Smart Trading Crypto Bot` workflow
4. 點擊右側 `Run workflow` 按鈕
5. 點擊綠色的 `Run workflow` 確認
6. 等待約 1-2 分鐘
7. 檢查 Telegram 是否收到通知！

## 完成！🎉

系統現在會：
- ✅ 每 15 分鐘自動分析市場
- ✅ 檢測川普新聞和重大事件
- ✅ 發現交易信號時立即通知你
- ✅ 完全免費運行

## 下一步

### 自訂配置（可選）

編輯 `config/config.yaml` 來調整：

```yaml
# 更換監控的幣種
trading:
  symbol: "ETHUSDT"  # 改為以太坊

# 調整 RSI 參數
indicators:
  rsi:
    oversold: 25  # 更嚴格的超賣條件
    overbought: 75

# 更改執行頻率
# 編輯 .github/workflows/trading_bot.yml
schedule:
  - cron: '0 * * * *'  # 改為每小時執行
```

### 暫停系統

如果需要暫停：
1. 進入 `Actions` 頁面
2. 點擊 workflow 右上角的 `...`
3. 選擇 `Disable workflow`

### 查看日誌

所有執行記錄都在 `Actions` 頁面，點擊任意執行記錄可查看詳細日誌。

## 故障排除

### 問題：沒收到 Telegram 通知

**解決**: 
1. 確認已經先發送訊息給你的 Bot
2. 檢查 Chat ID 是否正確（應該是純數字）
3. 在 GitHub Actions 日誌中查找錯誤訊息

### 問題：GitHub Actions 執行失敗

**解決**:
1. 檢查所有 Secrets 是否正確設定
2. 查看 Actions 頁面的錯誤日誌
3. 確認 `.github/workflows/trading_bot.yml` 文件位置正確

### 問題：幣安 API 錯誤

**解決**:
1. 確認 API Key 有「讀取」權限
2. 檢查 API Key 是否過期
3. 確認 IP 限制設定（建議不限制）

## 需要幫助？

- 📖 查看完整文檔：[DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 提交 Issue：GitHub Issues 頁面
- 💬 討論：GitHub Discussions

---

祝你交易順利！記得這只是輔助工具，實際交易決策還是要自己謹慎判斷。⚠️
