#!/usr/bin/env python3
"""
統一服務入口點 - 同時運行 Webhook Server 和定期監控
Unified Entry Point - Run both Webhook Server and Scheduled Monitoring
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)

# ==============================================================================
# 1. Webhook Server 部分 (虛擬執行或指令)
# ==============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'service': 'Smart Trading Crypto Bot',
        'mode': 'unified',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'webhook_server': True,
            'scheduled_monitoring': True
        }
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram Webhook 端點"""
    try:
        # 修復：使用正確的模組名稱 (複數形式)
        from src.telegram_handlers import TelegramHandler
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 處理 Telegram 更新
        handler = TelegramHandler()
        handler.handle_update(data)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """根路徑"""
    return jsonify({
        'message': 'Smart Trading Crypto Bot - Unified Service',
        'endpoints': {
            'health': '/health',
            'webhook': '/webhook (POST)'
        },
        'status': 'running'
    }), 200

# ==============================================================================
# 2. 定期監控部分 (背景任務)
# ==============================================================================

class ScheduledMonitor:
    """定期監控任務管理器"""
    
    def __init__(self, interval_minutes=5):
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None
        
    def start(self):
        """啟動監控線程"""
        if self.running:
            logger.warning("Monitor already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"✅ Scheduled monitor started (interval: {self.interval_minutes} minutes)")
        
    def stop(self):
        """停止監控線程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ Scheduled monitor stopped")
        
    def _monitor_loop(self):
        """監控循環主邏輯"""
        while self.running:
            try:
                self._run_monitoring_task()
                time.sleep(self.interval_minutes * 60)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(60)  # 錯誤後等待1分鐘再試
                
    def _run_monitoring_task(self):
        """執行一次監控任務"""
        try:
            logger.info("🔍 Running scheduled monitoring...")
            
            # 嘗試在這裡局部匯入 market_analyzer 以更彈性原始代碼
            from src.market_analyzer import MarketAnalyzer
            from src.news_monitor import NewsMonitor
            from src.notifier import Notifier
            
            # ✅ 修復：提供必需的 config 參數
            config = {
                'trading': {
                    'symbol': os.getenv('TRADING_SYMBOL', 'BTCUSDT'),
                    'timeframe': os.getenv('TRADING_TIMEFRAME', '15m'),
                    'lookback_periods': int(os.getenv('LOOKBACK_PERIODS', '100'))
                }
            }
            
            # 初始化分析器
            market_analyzer = MarketAnalyzer(config=config)
            news_monitor = NewsMonitor()
            notifier = Notifier()
            
            # 執行市場分析
            logger.info("📊 Analyzing market data...")
            analysis_result = market_analyzer.analyze_market()
            
            if analysis_result and analysis_result.get('alerts'):
                for alert in analysis_result['alerts']:
                    notifier.send_alert(alert)
                    logger.info(f"📢 Alert sent: {alert.get('message', 'N/A')}")
            
            # 執行新聞監控
            logger.info("📰 Checking crypto news...")
            news_result = news_monitor.check_news()
            
            if news_result and news_result.get('important_news'):
                for news in news_result['important_news']:
                    notifier.send_news_alert(news)
                    logger.info(f"📰 News alert sent: {news.get('title', 'N/A')}")
            
            logger.info("✅ Monitoring task completed successfully")
            
        except Exception as e:
            logger.error(f"Monitoring task error: {e}", exc_info=True)

# ==============================================================================
# 3. 主程序入口
# ==============================================================================

def main():
    """主程序入口"""
    logger.info("=" * 80)
    logger.info("🚀 Starting Smart Trading Crypto Bot - Unified Service")
    logger.info("=" * 80)
    
    # 檢查環境變數
    required_env_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly")
    
    # 啟動定期監控 (背景線程)
    monitor_interval = int(os.getenv('MONITOR_INTERVAL_MINUTES', '5'))
    monitor = ScheduledMonitor(interval_minutes=monitor_interval)
    monitor.start()
    
    # 啟動 Flask Webhook Server (主線程)
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🌐 Starting Flask Webhook Server on port {port}...")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False  # 避免重複啟動監控線程
        )
    except KeyboardInterrupt:
        logger.info("\n⏹️  Received shutdown signal")
        monitor.stop()
        logger.info("👋 Service stopped")
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        monitor.stop()
        sys.exit(1)

if __name__ == '__main__':
    main()
