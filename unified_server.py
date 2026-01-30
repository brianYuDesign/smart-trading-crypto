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

# =============================================================================
# 1. Webhook Server 部分 (虛擬用戶指令)
# =============================================================================

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
        # 修復: 使用正確的模組名稱 (複數形式)
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

# =============================================================================
# 2. 定期監控部分 (背景任務)
# =============================================================================

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
        logger.info("Monitor stopped")
        
    def _monitor_loop(self):
        """監控循環 (在背景線程中執行)"""
        while self.running:
            try:
                self._run_monitoring_tasks()
            except Exception as e:
                logger.error(f"Monitor error: {e}", exc_info=True)
            
            # 等待下次執行
            time.sleep(self.interval_minutes * 60)
    
    def _run_monitoring_tasks(self):
        """執行監控任務"""
        logger.info("🔍 Running scheduled monitoring...")
        
        try:
            # 導入監控模組
            from src.market_analyzer import MarketAnalyzer
            from src.news_monitor import NewsMonitor
            from src.notifier import TelegramNotifier
            
            # 獲取配置
            symbol = os.getenv('DEFAULT_SYMBOL', 'BTCUSDT')
            
            # 1. 市場分析
            logger.info(f"📊 Analyzing market for {symbol}...")
            analyzer = MarketAnalyzer()
            market_data = analyzer.analyze_market(symbol)
            
            # 2. 新聞監控
            logger.info("📰 Monitoring news...")
            news_monitor = NewsMonitor()
            news_data = news_monitor.check_news()
            
            # 3. 發送警報 (如果需要)
            notifier = TelegramNotifier()
            
            # 檢查市場異常
            if market_data and market_data.get('alert'):
                logger.warning(f"⚠️ Market alert detected: {market_data.get('alert_message')}")
                notifier.send_alert(
                    f"🚨 Market Alert\n\n{market_data.get('alert_message')}"
                )
            
            # 檢查新聞風險
            if news_data and news_data.get('risk_level') == 'high':
                logger.warning(f"⚠️ News risk detected: {news_data.get('summary')}")
                notifier.send_alert(
                    f"📰 News Risk Alert\n\n{news_data.get('summary')}"
                )
            
            logger.info("✅ Monitoring cycle completed")
            
        except ImportError as e:
            logger.error(f"Failed to import monitoring modules: {e}")
            logger.info("💡 Monitoring modules not available - skipping this cycle")
        except Exception as e:
            logger.error(f"Monitoring task error: {e}", exc_info=True)

# =============================================================================
# 3. 主程序入口
# =============================================================================

def main():
    """主程序入口"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Smart Trading Crypto Bot - Unified Service")
    logger.info("=" * 60)
    
    # 檢查是否啟用監控
    enable_monitoring = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    monitor_interval = int(os.getenv('MONITOR_INTERVAL_MINUTES', '5'))
    
    # 啟動定期監控 (背景線程)
    if enable_monitoring:
        monitor = ScheduledMonitor(interval_minutes=monitor_interval)
        monitor.start()
        logger.info(f"✅ Monitoring enabled (interval: {monitor_interval} minutes)")
    else:
        logger.info("⚠️ Monitoring disabled")
    
    # 啟動 Flask Webhook Server (主線程)
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🌐 Starting Flask Webhook Server on port {port}...")
    
    try:
        # 注意: 在生產環境中，Render 會使用 gunicorn
        # 這裡的 app.run() 主要用於開發和測試
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
