#!/usr/bin/env python3
"""
Crypto Trading Bot - 主程式
支援兩種模式:
1. commands: Telegram 指令模式 (webhook)
2. monitoring: 定時監控分析模式
"""

import os
import sys
import logging
from pathlib import Path
from src.telegram_commands import TelegramCommandHandler
from src.market_analyzer import MarketAnalyzer
from src.news_monitor import NewsMonitor
from src.notifier import TelegramNotifier

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_command_mode():
    """
    執行 Telegram 指令模式
    啟動 webhook server 等待用戶指令
    """
    try:
        logger.info("=" * 60)
        logger.info("🤖 Crypto Trading Bot - 指令模式")
        logger.info("=" * 60)

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

        # Webhook 模式：由 webhook_server.py 處理請求
        # 這裡只需要保持進程運行
        logger.info("✓ Webhook 服務已就緒，等待請求...")

        # 保持運行（在 webhook 模式下，gunicorn 會管理進程）
        import time
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Bot 已停止")
    except Exception as e:
        logger.error(f"❌ 指令模式發生錯誤: {e}", exc_info=True)
        sys.exit(1)


def run_monitoring_and_analysis():
    """
    執行監控和分析模式
    定時檢查市場並發送報告
    """
    try:
        logger.info("=" * 60)
        logger.info("📊 開始市場監控與分析")
        logger.info("=" * 60)

        # 初始化組件
        config = {
            'data_dir': 'data',
            'update_interval': 300
        }

        notifier = TelegramNotifier()
        market_analyzer = MarketAnalyzer()
        news_monitor = NewsMonitor(config['data_dir'])

        notifier.notify_system_status('started', '系統開始分析市場')

        # 1. 檢查新聞風險
        logger.info("\n--- 步驟 1: 檢查新聞風險 ---")
        try:
            news_safety = news_monitor.is_safe_to_trade()

            if not news_safety.get('safe_to_trade', True):
                reason = news_safety.get('reason', '未知原因')
                logger.warning(f"新聞風險警報: {reason}")

                # 發送風險警報
                try:
                    notifier.notify_risk_alert('news', news_safety)
                except Exception as e:
                    logger.error(f"發送新聞風險警報失敗: {e}")

                logger.info("由於新聞風險，停止交易信號分析")
                return
            else:
                logger.info(f"✓ 新聞環境正常: {news_safety.get('reason', '')}")

        except Exception as e:
            logger.error(f"新聞風險檢查失敗: {e}", exc_info=True)
            logger.info("⚠️ 新聞檢查失敗，繼續其他分析...")

        # 2. 分析市場條件
        logger.info("\n--- 步驟 2: 分析市場條件 ---")
        try:
            market_conditions = market_analyzer.analyze_market_conditions()

            # 檢查市場波動性
            if market_conditions.get('volatility', 0) > 0.05:
                logger.warning(f"高波動性警報: {market_conditions.get('volatility', 0):.2%}")
                try:
                    notifier.notify_risk_alert('volatility', market_conditions)
                except Exception as e:
                    logger.error(f"發送波動性警報失敗: {e}")

            logger.info(f"✓ 市場條件: {market_conditions.get('condition', 'unknown')}")

        except Exception as e:
            logger.error(f"市場分析失敗: {e}", exc_info=True)
            logger.info("⚠️ 市場分析失敗，繼續其他分析...")

        # 3. 生成交易信號
        logger.info("\n--- 步驟 3: 生成交易信號 ---")
        try:
            # 這裡可以添加交易信號生成邏輯
            logger.info("交易信號生成功能待實現")

        except Exception as e:
            logger.error(f"信號生成失敗: {e}", exc_info=True)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 分析完成")
        logger.info("=" * 60)

        notifier.notify_system_status('completed', '市場分析已完成')

    except Exception as e:
        logger.error(f"❌ 執行過程中發生錯誤: {e}", exc_info=True)
        try:
            notifier = TelegramNotifier()
            notifier.notify_system_status('error', f'系統錯誤: {str(e)}')
        except:
            pass
        sys.exit(1)


def main():
    """主程式入口"""
    # 獲取運行模式
    bot_mode = os.getenv('BOT_MODE', 'commands').lower()

    if bot_mode == 'commands':
        run_command_mode()
    elif bot_mode == 'monitoring':
        run_monitoring_and_analysis()
    else:
        logger.error(f"❌ 未知的 BOT_MODE: {bot_mode}")
        logger.info("請設定 BOT_MODE 環境變數為 'commands' 或 'monitoring'")
        sys.exit(1)


if __name__ == "__main__":
    main()
