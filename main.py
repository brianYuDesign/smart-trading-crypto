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

# 確保專案根目錄在 Python 路徑中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
        # 更新主要加密貨幣平價數據
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
        # 這裡可以呼叫 handlers 的方法來發生成並發送報告
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
    logger.info("✓ 已排程整點更新市場數據事件")
    
    # 每30分鐘更新新聞 (緩存整點避免瞬時高峰)
    scheduler.add_job(
        update_news_feed,
        trigger=CronTrigger(minute='0,30'),  # 每小時的0分和30分
        id='update_news_feed',
        name='更新新聞來源',
        replace_existing=True
    )
    logger.info("✓ 已排程每30分鐘更新新聞事件")
    
    # 每天早上10:00發送新聞檢查報告 (操作時間避誤)
    # scheduler.add_job(
    #     send_daily_report,
    #     trigger=CronTrigger(hour=10, minute=0),
    #     id='send_daily_report',
    #     name='發送全日報告',
    #     replace_existing=True
    # )
    # logger.info("✓ 已排程每日早10點發送全日報告事件")
    
    # 啟動調度器
    scheduler.start()
    logger.info("✅ APScheduler 已啟動且執行中")

def main():
    """主入口函數
Integration: Flask Webhook + APScheduler
"""
    try:
        logger.info("="*80)
        logger.info("🚀 Crypto Trading Bot 啟動完整！")
        logger.info("Simplified Architecture: Render + APScheduler")
        logger.info("="*80)
        
        # 初始化定時任務
        init_scheduler()
        logger.info("✅ 定時任務設定完成")
        
        # 導入 Flask Webhook
        logger.info("⏰ 導入 Flask Webhook Server...")
        from src.server import app, init_app_monitor
        
        # 初始化監控 (如果有的話)
        try:
            init_app_monitor()
            logger.info("✅ 監控系統已初始化")
        except Exception as e:
            logger.warning(f"⚠️  監控初始化警告: {e}")
        
        # 設定 Flask
        port = int(os.getenv('PORT', 10000))
        host = os.getenv('HOST', '0.0.0.0')
        
        logger.info("="*80)
        logger.info(f"🌐 Flask Server 正在啟動...")
        logger.info(f"   Host: {host}")
        logger.info(f"   Port: {port}")
        logger.info(f"   Webhook: /webhook")
        logger.info("="*80)
        
        # 啟動 Flask (Gunicorn 會透過 WSGI 呼叫 app)
        app.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  收到中斷信號，正在關閉...")
        if scheduler:
            scheduler.shutdown()
            logger.info("✅ Scheduler 已停止")
    except Exception as e:
        logger.error(f"❌ 啟動錯誤: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
