"""
Smart Trading Crypto - 主程序
整合市場分析、新聞監控和信號生成
"""
import os
import yaml
from datetime import datetime
from src.market_analyzer import MarketAnalyzer
from src.news_monitor import NewsMonitor
from src.signal_generator import SignalGenerator
from src.notifier import TelegramNotifier
import logging

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


def main():
    # 初始化新聞監控
    news_monitor = NewsMonitor()

    # 檢查新新聞
    print("\n" + "="*70)
    print("📰 檢查加密貨幣新聞")
    print("="*70)

    new_news = news_monitor.monitor_news()

    # 只在有新新聞時發送提醒
    if new_news:
        news_message = news_monitor.format_news_message(new_news)
        if news_message:
            send_telegram_message(news_message)
            print(f"✅ 已發送 {len(new_news)} 則新新聞提醒到 Telegram")
    else:
        print("✅ 沒有新新聞，不發送提醒")

    """主程序"""
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
            logger.info("由於市場波動過大，停止交易信號分析")
            return
        
        logger.info("✓ 市場穩定性檢查通過")
        logger.info(f"  當前價格: ${market_conditions['current_price']:.2f}")
        logger.info(f"  24h 漲跌: {market_conditions['price_change_24h']:.2f}%")
        logger.info(f"  波動率: {market_conditions['volatility']:.2f}%")
        
        # 3. 獲取市場數據並分析
        logger.info("\n--- 步驟 3: 分析市場數據 ---")
        klines_df = market_analyzer.fetch_klines()
        
        # 4. 生成交易信號
        logger.info("\n--- 步驟 4: 生成交易信號 ---")
        analysis_result = signal_generator.analyze(klines_df)
        
        logger.info(f"當前 RSI: {analysis_result['rsi']}")
        logger.info(f"當前 MACD: {analysis_result['macd']:.4f}")
        
        # 5. 發送信號通知
        if analysis_result['buy_signal']:
            logger.info("\n🟢 檢測到買入信號！")
            buy_signal = analysis_result['buy_signal']
            logger.info(f"  信號強度: {buy_signal['strength']}")
            logger.info(f"  滿足條件: {buy_signal['conditions_met']}/4")
            logger.info(f"  原因: {', '.join(buy_signal['reasons'])}")
            
            # 發送 Telegram 通知
            notifier.notify_buy_signal(buy_signal, market_conditions)
        
        elif analysis_result['sell_signal']:
            logger.info("\n🔴 檢測到賣出信號！")
            sell_signal = analysis_result['sell_signal']
            logger.info(f"  信號強度: {sell_signal['strength']}")
            logger.info(f"  滿足條件: {sell_signal['conditions_met']}/4")
            logger.info(f"  原因: {', '.join(sell_signal['reasons'])}")
            
            # 發送 Telegram 通知
            notifier.notify_sell_signal(sell_signal, market_conditions)
        
        else:
            logger.info("\n⚪ 當前無交易信號")
            logger.info("  市場處於觀望狀態，繼續監控...")
        
        logger.info("\n" + "=" * 60)
        logger.info("分析完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}", exc_info=True)
        try:
            notifier = TelegramNotifier(load_config())
            notifier.notify_system_status('error', f'系統錯誤: {str(e)}')
        except:
            pass
        raise


if __name__ == '__main__':
    main()
