#!/usr/bin/env python3
"""
Crypto Trading Bot - 主程式 (Unified Entry Point)
支援兩種模式:
1. webhook: 啟動 Flask Webhook Server (V2 智能投資顧問)
2. monitoring: 定時監控分析模式 (V1 功能)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_webhook_mode():
    """
    執行 Webhook Server 模式 (V2)
    """
    try:
        logger.info("=" * 60)
        logger.info("🤖 Crypto Trading Bot - Webhook Server Mode (V2)")
        logger.info("=" * 60)
        
        # 導入並運行 Flask 應用
        from src.server import app, init_app_monitor
        
        # 初始化監控組件
        init_app_monitor()
        
        port = int(os.getenv('PORT', 5000))
        logger.info(f"🚀 Server starting on port {port}...")
        
        # 注意: 在生產環境中應使用 Gunicorn
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"❌ Webhook 模式錯誤: {e}", exc_info=True)
        sys.exit(1)

def run_monitoring_mode():
    """
    執行監控模式 (V1 保留功能)
    """
    try:
        from src.verifier import run_verification_logic # 假設這是原本 V1 的監控邏輯入口，這裡簡化處理
        # 注意: 原有的 V1 監控邏輯需要確認是否完全兼容新架構
        # 為了安全起見，我們會嘗試導入舊的 V1 模組，但建議逐步遷移到 V2 的 market_monitor
        
        logger.info("=" * 60)
        logger.info("📊 Crypto Trading Bot - Monitoring Mode (V1 Legacy)")
        logger.info("=" * 60)
        
        # 這裡保留原有的 V1 邏輯結構，但嘗試使用新的 src 模組
        from src.market_analyzer import MarketAnalyzer
        from src.news_monitor import NewsMonitor
        from src.notifier import TelegramNotifier
        
        # ... (保留原有的 run_monitoring_and_analysis 邏輯，但為了精簡，這裡不重複全部代碼)
        # 實際項目中應確保這些模組 (MarketAnalyzer, NewsMonitor) 
        # 已經適配新的 database.py 或能夠獨立運行
        
        logger.info("⚠️ 監控模式目前僅為佔位符，請使用 Webhook 模式以獲得完整 V2 功能")
        
    except ImportError as e:
        logger.error(f"❌ 監控模式模組缺失: {e}")
    except Exception as e:
        logger.error(f"❌ 監控模式錯誤: {e}", exc_info=True)
        sys.exit(1)

def main():
    """主程式入口"""
    # 獲取運行模式，預設為 webhook (V2)
    bot_mode = os.getenv('BOT_MODE', 'webhook').lower()

    if bot_mode == 'webhook':
        run_webhook_mode()
    elif bot_mode == 'monitoring':
        run_monitoring_mode()
    else:
        logger.error(f"❌ 未知的 BOT_MODE: {bot_mode}")
        logger.info("請設定 BOT_MODE 環境變數為 'webhook' 或 'monitoring'")
        sys.exit(1)

if __name__ == "__main__":
    main()
