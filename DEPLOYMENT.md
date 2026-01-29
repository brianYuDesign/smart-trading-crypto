# 部署指南

完整的部署步驟，讓系統在 GitHub Actions 上自動運行。

## 前置準備

### 1. 幣安 API 憑證

1. 登入 [幣安](https://www.binance.com/)
2. 進入「API 管理」
3. 創建新的 API Key
4. **重要**: 只需要「讀取」權限，不需要「交易」或「提現」權限
5. 記下 `API Key` 和 `Secret Key`

### 2. Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot` 命令
3. 按照提示設定 Bot 名稱
4. 記下 Bot Token (格式: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. 取得 Telegram Chat ID

方法一：使用 Bot
1. 在 Telegram 搜尋 `@userinfobot`
2. 發送任意訊息
3. 它會回覆你的 Chat ID

方法二：手動獲取
1. 在瀏覽器開啟: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
2. 先傳送訊息給你的 Bot
3. 在返回的 JSON 中找到 `"chat":{"id":123456789}`

## GitHub 部署步驟

### 第一步：Fork 或上傳專案到 GitHub

1. 在 GitHub 創建新的 repository，名稱例如 `smart-trading-crypto`
2. 將專案代碼上傳到 repository

### 第二步：設定 GitHub Secrets

1. 進入你的 Repository
2. 點擊 `Settings` > `Secrets and variables` > `Actions`
3. 點擊 `New repository secret`
4. 依次添加以下 secrets：

| Secret Name | Value | 說明 |
|-------------|-------|------|
| `BINANCE_API_KEY` | 你的幣安 API Key | 從幣安獲取 |
| `BINANCE_API_SECRET` | 你的幣安 Secret Key | 從幣安獲取 |
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token | 從 BotFather 獲取 |
| `TELEGRAM_CHAT_ID` | 你的 Chat ID | 從 userinfobot 獲取 |
| `CRYPTOPANIC_API_KEY` | (可選) CryptoPanic API Key | 可暫時留空 |

### 第三步：設定 GitHub Actions

1. 在專案根目錄創建 `.github/workflows/` 目錄
2. 將 `github-workflows/trading_bot.yml` 文件移動到 `.github/workflows/trading_bot.yml`
3. Commit 並 Push 到 GitHub

### 第四步：啟用 GitHub Actions

1. 進入 Repository 的 `Actions` 頁面
2. 如果看到提示，點擊 `I understand my workflows, go ahead and enable them`
3. 你應該會看到 `Smart Trading Crypto Bot` workflow

### 第五步：測試運行

1. 在 `Actions` 頁面，點擊 `Smart Trading Crypto Bot`
2. 點擊右側的 `Run workflow` 按鈕
3. 選擇 branch (通常是 `main`)
4. 點擊 `Run workflow`
5. 等待執行完成（約 1-2 分鐘）
6. 檢查 Telegram 是否收到通知

## 執行排程

預設排程：
- **每 15 分鐘**執行一次市場分析

修改排程：
編輯 `.github/workflows/trading_bot.yml` 中的 cron 表達式

```yaml
schedule:
  - cron: '*/15 * * * *'  # 每 15 分鐘
  # - cron: '0 * * * *'   # 每小時
  # - cron: '0 */4 * * *' # 每 4 小時
  # - cron: '0 0 * * *'   # 每天午夜
```

**注意**: GitHub Actions 的 cron 使用 UTC 時區

## 檢查日誌

1. 進入 `Actions` 頁面
2. 點擊任意執行記錄
3. 點擊 `analyze_market` job
4. 展開各個步驟查看詳細日誌

## 暫停/恢復系統

### 暫停
1. 進入 `Actions` 頁面
2. 點擊 `Smart Trading Crypto Bot`
3. 點擊右上角的 `...` 按鈕
4. 選擇 `Disable workflow`

### 恢復
重複上述步驟，選擇 `Enable workflow`

## 本地測試（可選）

在部署到 GitHub 之前，建議先在本地測試：

```bash
# 克隆專案
git clone https://github.com/yourusername/smart-trading-crypto.git
cd smart-trading-crypto

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數（方式一：直接設定）
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id

# 或是創建 .env 文件（方式二）
# 複製 env.example 為 .env 並填入你的憑證

# 執行測試
python main.py
```

## 故障排除

### 問題：GitHub Actions 沒有執行

**解決方案**:
- 確認 workflow 文件路徑正確: `.github/workflows/trading_bot.yml`
- 確認 workflow 已啟用（Actions 頁面）
- 檢查 Repository 的 Actions 權限設定

### 問題：收不到 Telegram 通知

**解決方案**:
1. 確認 Bot Token 和 Chat ID 正確
2. 確認已經先傳送訊息給 Bot（Bot 需要被啟動）
3. 檢查 GitHub Secrets 是否正確設定
4. 查看 Actions 日誌中的錯誤訊息

### 問題：幣安 API 錯誤

**解決方案**:
1. 確認 API Key 和 Secret 正確
2. 確認 API Key 有「讀取」權限
3. 確認 API Key 的 IP 限制設定（建議不限制 IP）
4. 檢查幣安 API 配額是否用盡

### 問題：執行時間過長或超時

**解決方案**:
- 減少 `config.yaml` 中的 `lookback_periods`
- 優化新聞源數量
- 檢查網路連接狀態

## 監控建議

1. **每天檢查**: 查看 Telegram 是否有系統通知
2. **每週檢查**: 查看 GitHub Actions 執行歷史，確認沒有連續失敗
3. **設定告警**: 在 GitHub 設定郵件通知，當 workflow 失敗時會收到郵件

## 安全性建議

1. ✅ **不要**將 API Keys 提交到代碼庫
2. ✅ **使用** GitHub Secrets 存放敏感信息
3. ✅ **限制** 幣安 API Key 權限（只需讀取）
4. ✅ **定期輪換** API Keys
5. ✅ **不要分享** Telegram Bot Token

## 成本說明

- **GitHub Actions**: 免費額度每月 2000 分鐘（公開 repo 無限）
- **幣安 API**: 免費
- **Telegram Bot**: 免費
- **總成本**: **$0** 🎉

## 升級到付費服務（未來）

如果需要更穩定的執行環境，可考慮：
- **AWS Lambda**: 更可靠的執行環境
- **Heroku**: 簡單易用的雲平台
- **Digital Ocean**: VPS 服務器

## 下一步

系統運行後，可以考慮：
1. 調整技術指標參數（`config/config.yaml`）
2. 添加更多交易對監控
3. 優化信號生成策略
4. 記錄歷史信號並進行回測
5. 開發自動下單功能（需要謹慎！）

## 支援

如有問題：
1. 檢查本文檔的故障排除章節
2. 查看 GitHub Actions 執行日誌
3. 提交 Issue 到 GitHub Repository
