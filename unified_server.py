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

# ============================================================================
# 1. Webhook Server 部分 (處理用戶指令)
# ============================================================================

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
        from src.telegram_handler import TelegramHandler
        
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

# ============================================================================
# 2. 定期監控部分 (背景任務)
# ============================================================================

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
        logger.info("Scheduled monitor stopped")
        
    def _monitor_loop(self):
        """監控循環"""
        while self.running:
            try:
                self._run_monitoring_tasks()
                # 等待下一次執行
                time.sleep(self.interval_minutes * 60)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(60)  # 錯誤後等待 1 分鐘再試
                
    def _run_monitoring_tasks(self):
        """執行監控任務"""
        logger.info("=" * 80)
        logger.info(f"🔍 Running scheduled monitoring - {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        try:
            # 1. 新聞監控
            self._monitor_news()
            
            # 2. 市場分析
            self._monitor_market()
            
            logger.info("✅ Monitoring tasks completed")
            
        except Exception as e:
            logger.error(f"Monitoring tasks error: {e}")
            
    def _monitor_news(self):
        """新聞風險監控"""
        try:
            from src.news_monitor import NewsMonitor
            from src.telegram_notifier import TelegramNotifier
            
            logger.info("📰 Checking news for risks...")
            
            monitor = NewsMonitor()
            notifier = TelegramNotifier()
            
            # 獲取最新新聞
            news_items = monitor.fetch_latest_news()
            
            if not news_items:
                logger.info("No new news items")
                return
                
            # 分析風險
            for item in news_items[:5]:  # 只分析最新 5 條
                sentiment = monitor.analyze_sentiment(item['title'])
                
                # 如果是重要負面新聞，發送警報
                if sentiment['label'] == 'negative' and sentiment['score'] > 0.7:
                    alert_msg = (
                        f"⚠️ 風險警報\n\n"
                        f"標題: {item['title']}\n"
                        f"情緒: {sentiment['label']} ({sentiment['score']:.2f})\n"
                        f"來源: {item.get('source', 'Unknown')}\n"
                        f"時間: {item.get('published_at', 'Unknown')}"
                    )
                    notifier.send_message(alert_msg)
                    logger.warning(f"⚠️ Risk alert sent: {item['title']}")
                    
            logger.info(f"Processed {len(news_items)} news items")
            
        except Exception as e:
            logger.error(f"News monitoring error: {e}")
            
    def _monitor_market(self):
        """市場異常監控"""
        try:
            from src.market_analyzer import MarketAnalyzer
            from src.telegram_notifier import TelegramNotifier
            
            logger.info("📊 Analyzing market conditions...")
            
            analyzer = MarketAnalyzer()
            notifier = TelegramNotifier()
            
            # 獲取市場數據
            symbol = os.getenv('DEFAULT_SYMBOL', 'BTCUSDT')
            market_data = analyzer.get_market_overview(symbol)
            
            # 檢查異常波動
            if 'volatility' in market_data:
                volatility = market_data['volatility']
                
                # 如果波動率超過閾值，發送警報
                if volatility > 5.0:  # 5% 波動率閾值
                    alert_msg = (
                        f"⚠️ 高波動警報\n\n"
                        f"交易對: {symbol}\n"
                        f"波動率: {volatility:.2f}%\n"
                        f"價格: ${market_data.get('price', 'N/A')}\n"
                        f"24h變化: {market_data.get('change_24h', 'N/A')}%"
                    )
                    notifier.send_message(alert_msg)
                    logger.warning(f"⚠️ High volatility alert: {volatility:.2f}%")
                    
            logger.info(f"Market analysis completed for {symbol}")
            
        except Exception as e:
            logger.error(f"Market monitoring error: {e}")

# ============================================================================
# 3. 主程序
# ============================================================================

# 全局監控器實例
monitor = None

def start_unified_service():
    """啟動統一服務"""
    global monitor
    
    logger.info("=" * 80)
    logger.info("🚀 Starting Smart Trading Crypto Bot - Unified Service")
    logger.info("=" * 80)
    
    # 獲取配置
    port = int(os.getenv('PORT', 10000))
    monitor_interval = int(os.getenv('MONITOR_INTERVAL_MINUTES', 5))
    enable_monitoring = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    
    logger.info(f"📍 Port: {port}")
    logger.info(f"⏰ Monitor Interval: {monitor_interval} minutes")
    logger.info(f"📊 Monitoring Enabled: {enable_monitoring}")
    
    # 啟動定期監控 (背景線程)
    if enable_monitoring:
        monitor = ScheduledMonitor(interval_minutes=monitor_interval)
        monitor.start()
    else:
        logger.info("⏸️  Scheduled monitoring disabled")
    
    # 啟動 Flask Server (主線程)
    logger.info("🌐 Starting Flask Webhook Server...")
    logger.info("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False  # 禁用 reloader 避免重複啟動監控
    )

if __name__ == '__main__':
    try:
        start_unified_service()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Shutting down gracefully...")
        if monitor:
            monitor.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
