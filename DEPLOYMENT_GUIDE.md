# 🚀 Smart Trading Crypto Bot - 部署指南

## 📋 架構概覽

本 Bot 使用**混合模式架構**：
- **Render.com**: 24/7 運行 Flask webhook server，即時回應指令
- **GitHub Actions**: 定時執行市場監控和新聞分析

## 🛠️ 部署步驟

### Step 1: 部署到 Render.com

1. 前往 [render.com](https://render.com) 並用 GitHub 登入
2. 點擊 **"New +" → "Web Service"**
3. 連接 repository: `brianYuDesign/smart-trading-crypto`
4. 配置:
   - **Name**: `smart-trading-crypto-bot`
   - **Region**: `Singapore`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webhook_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. 添加環境變數:
   - `TELEGRAM_BOT_TOKEN` = 你的 Bot Token
   - `TELEGRAM_CHAT_ID` = 你的 Chat ID
6. 選擇 **Free** 方案
7. 點擊 **"Create Web Service"**

部署完成後，你會得到網址：`https://smart-trading-crypto-bot.onrender.com`

### Step 2: 設定 Telegram Webhook

在瀏覽器訪問（替換 YOUR_BOT_TOKEN 和 YOUR_WEBHOOK_URL）：

```
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://smart-trading-crypto-bot.onrender.com/webhook
```

成功會看到：
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Step 3: 驗證

在 Telegram 發送 `/start`，如果收到歡迎訊息，部署成功！

## 🔧 維護

- **查看日誌**: Render Dashboard → 你的 service → Logs
- **重新部署**: 推送到 GitHub main branch 會自動觸發
- **檢查 webhook**: 訪問 `https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo`

## 💰 成本

完全免費！
- Render Free: 750 小時/月
- GitHub Actions: 2000 分鐘/月

## 📞 常見問題

**Q: Webhook 設定失敗？**
A: 確認 Render service 狀態是 "Live"，URL 是 HTTPS

**Q: Bot 沒回應？**
A: 檢查 Render Logs 和環境變數設定

**Q: 如何更新程式碼？**
A: Push 到 GitHub，Render 會自動重新部署

---

祝部署順利！🚀
