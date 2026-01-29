"""
Smart Trading Crypto - 主程式（整合版）
整合市場分析、新聞監控、信號生成和 Telegram 指令處理
"""
import os
import yaml
from datetime import datetime
from src.market_analyzer import MarketAnalyzer
from src.news_monitor import NewsMonitor
from src.signal_generator import SignalGenerator
from src.notifier import TelegramNotifier
from src.telegram_commands import TelegramCommandHandler  # 新增：指令處理器
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config/config.yaml') -> dict:
    """載入配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info("配置文件載入成功")
        return config
    except Exception as e:
        logger.error(f"載入配置文件失敗: {e}")
        raise


def run_bot_with_commands():
    """運行帶有指令處理的 Bot"""
    logger.info("=" * 60)
    logger.info("Smart Trading Crypto Bot 啟動（指令模式）")
    logger.info("=" * 60)
    
    try:
        # 從環境變數獲取 Token
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.error("❌ 請設定 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 環境變數")
            return
        
        # 初始化指令處理器
        command_handler = TelegramCommandHandler()
        
        logger.info("✅ Bot 指令處理器已啟動")
        logger.info("📱 等待 Telegram 指令...")
        logger.info("")
        logger.info("可用指令：")
        logger.info("  /news [數量] - 查詢最新新聞")
        logger.info("  /price <幣種> - 查詢即時價格")
        logger.info("  /prices - 主流幣種價格")
        logger.info("  /market - 市場總覽")
        logger.info("  /analysis <幣種> - 技術分析")
        logger.info("  /help - 查看所有指令")
        logger.info("=" * 60)
        
        # 處理指令（單次執行）
        command_handler.process_commands()
        
    except Exception as e:
        logger.error(f"❌ Bot 運行錯誤: {e}")
        raise


def run_monitoring_and_analysis():
    """運行市場監控和分析（原有功能）"""
    logger.info("=" * 60)
    logger.info("Smart Trading Crypto 系統啟動")
    logger.info("=" * 60)
    
    try:
        # 載入配置
        config = load_config()
        
        # 初始化各個模組
        market_analyzer = MarketAnalyzer(config)
        news_monitor = NewsMonitor(config)
        signal_generator = SignalGenerator(config)
        notifier = TelegramNotifier(config)
        
        # 發送系統啟動通知
        notifier.notify_system_status('started', '系統開始分析市場')
        
        # 1. 檢查新聞風險
        logger.info("\n--- 步驟 1: 檢查新聞風險 ---")
        news_safety = news_monitor.is_safe_to_trade()
        
        if not news_safety['safe_to_trade']:
            logger.warning(f"新聞風險警報: {news_safety['reason']}")
            notifier.notify_risk_alert('news', news_safety)
            logger.info("由於新聞風險，停止交易信號分析")
            return
        
        logger.info("✓ 新聞檢查通過")
        
        # 2. 檢查市場穩定性
        logger.info("\n--- 步驟 2: 檢查市場穩定性 ---")
        market_stability = market_analyzer.is_market_stable()
        market_conditions = market_stability['market_conditions']
        
        if not market_stability['stable']:
            logger.warning(f"市場穩定性警報: {market_stability['reason']}")
            notifier.notify_risk_alert('volatility', market_conditions)
            logger.info("由於市場波動，停止交易信號分析")
            return
            
        logger.info("✓ 市場穩定性檢查通過")
        
        # 3. 生成交易信號
        logger.info("\n--- 步驟 3: 生成交易信號 ---")
        signals = signal_generator.generate_signals()
        
        if signals:
            logger.info(f"✓ 生成 {len(signals)} 個交易信號")
            notifier.notify_trading_signals(signals)
        else:
            logger.info("目前沒有符合條件的交易信號")
        
        # 發送系統完成通知
        notifier.notify_system_status('completed', '分析完成')
        logger.info("\n" + "=" * 60)
        logger.info("系統分析完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"系統運行錯誤: {e}")
        raise


def main():
    """主程式入口"""
    # 判斷運行模式
    mode = os.getenv('BOT_MODE', 'commands')  # 預設為指令模式
    
    if mode == 'commands':
        # 指令處理模式（用於 GitHub Actions 或定時執行）
        run_bot_with_commands()
    elif mode == 'monitoring':
        # 監控分析模式（原有功能）
        run_monitoring_and_analysis()
    else:
        logger.error(f"未知的運行模式: {mode}")
        logger.info("請設定 BOT_MODE 環境變數為 'commands' 或 'monitoring'")


if __name__ == "__main__":
    main()
