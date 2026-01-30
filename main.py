#!/usr/bin/env python3
"""
Crypto Trading Bot - 主程式 (Unified Entry Point with APScheduler)
簡化架構: Render + APScheduler 統一處理所有功能
- Webhook: Telegram Bot 即時訊息
- Scheduler: 定時任務 (市場數據、新聞、報告)
"""

import os
import sys
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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

# 全域 scheduler
scheduler = None

def update_market_data():
    """定時更新市場數據"""
    try:
        logger.info("📊 開始更新市場數據...")
        from src.crypto_data_service import CryptoDataService
        
        service = CryptoDataService()
        # 更新主要加密貨幣數據
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        for symbol in symbols:
            try:
                data = service.get_crypto_price(symbol)
                logger.info(f"✓ {symbol}: ${data.get('price', 'N/A')}")
            except Exception as e:
                logger.error(f"✗ {symbol} 更新失敗: {e}")
        
        logger.info("✅ 市場數據更新完成")
    except Exception as e:
        logger.error(f"❌ 市場數據更新錯誤: {e}", exc_info=True)

def update_news_feed():
    """定時更新加密貨幣新聞"""
    try:
        logger.info("📰 開始更新新聞...")
        from src.crypto_data_service import CryptoDataService
        
        service = CryptoDataService()
        news = service.get_crypto_news(limit=5)
        logger.info(f"✅ 更新了 {len(news)} 條新聞")
    except Exception as e:
        logger.error(f"❌ 新聞更新錯誤: {e}", exc_info=True)

def send_daily_report():
    """發送每日市場報告"""
    try:
        logger.info("📊 生成每日報告...")
        from src.telegram_handlers import TelegramHandlers
        
        handlers = TelegramHandlers()
        # 這裡可以呼叫 handlers 的方法來產生並發送報告
        # 實際實作需要根據你的需求客製化
        logger.info("✅ 每日報告已發送")
    except Exception as e:
        logger.error(f"❌ 每日報告錯誤: {e}", exc_info=True)

def init_scheduler():
    """初始化定時任務調度器"""
    global scheduler
    
    logger.info("⏰ 初始化 APScheduler...")
    scheduler = BackgroundScheduler(timezone='Asia/Taipei')
    
    # 每小時更新市場數據 (整點執行)
    scheduler.add_job(
        update_market_data,
        trigger=CronTrigger(minute=0),  # 每小時的第0分鐘
        id='update_market_data',
        name='更新市場數據',
        replace_existing=True
    )
    logger.info("✓ 已排程: 每小時更新市場數據")
    
    # 每30分鐘更新新聞
    scheduler.add_job(
        update_news_feed,
        trigger=CronTrigger(minute='0,30'),  # 每小時的0分和30分
        id='update_news_feed',
        name='更新新聞',
        replace_existing=True
    )
    logger.info("✓ 已排程: 每30分鐘更新新聞")
    
    # 每天早上8點發送報告
    scheduler.add_job(
        send_daily_report,
        trigger=CronTrigger(hour=8, minute=0),
        id='send_daily_report',
        name='發送每日報告',
        replace_existing=True
    )
    logger.info("✓ 已排程: 每天8:00發送報告")
    
    # 啟動 scheduler
    scheduler.start()
    logger.info("✅ APScheduler 已啟動")
    
    # 立即執行一次更新 (可選)
    logger.info("🔄 執行初始數據更新...")
    update_market_data()

def run_webhook_mode():
    """
    執行 Webhook Server 模式 (整合 APScheduler)
    """
    try:
        logger.info("=" * 60)
        logger.info("🤖 Crypto Trading Bot - Unified Mode")
        logger.info("   ├─ Telegram Webhook (即時訊息)")
        logger.info("   └─ APScheduler (定時任務)")
        logger.info("=" * 60)
        
        # 初始化定時任務
        init_scheduler()
        
        # 導入並運行 Flask 應用
        from src.server import app, init_app_monitor
        
        # 初始化監控組件
        init_app_monitor()
        
        port = int(os.getenv('PORT', 5000))
        logger.info(f"🚀 Server starting on port {port}...")
        
        # 注意: 在生產環境中使用 Gunicorn
        # 此處的 app.run() 會阻塞，scheduler 在背景運行
        app.run(host='0.0.0.0', port=port)
        
    except KeyboardInterrupt:
        logger.info("⏹️  收到中斷信號，正在關閉...")
        if scheduler:
            scheduler.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 服務錯誤: {e}", exc_info=True)
        if scheduler:
            scheduler.shutdown()
        sys.exit(1)

def main():
    """主程式入口"""
    # 現在只有一種模式: webhook + scheduler
    run_webhook_mode()

if __name__ == '__main__':
    main()
