#!/usr/bin/env python3
"""
Crypto Trading Bot - 主程式 (GitHub Actions 單次執行模式)
🔧 修復: 改為單次執行，避免無限循環導致 6 小時 timeout
- 每次執行只運行一次檢查
- 不啟動 Flask server (適用於 GitHub Actions cron)
- 適合定時觸發場景 (每 5 分鐘執行一次)
"""

import os
import sys
import logging
from dotenv import load_dotenv

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

def run_single_check():
    """單次執行模式：檢查市場並發送訊息"""
    try:
        logger.info("=" * 80)
        logger.info("🚀 Crypto Trading Bot - 單次執行模式")
        logger.info("=" * 80)
        
        from src.crypto_data_service import CryptoDataService
        
        service = CryptoDataService()
        
        # 更新主要加密貨幣價格
        logger.info("\n📊 檢查市場數據...")
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        
        prices = {}
        for symbol in symbols:
            try:
                data = service.get_crypto_price(symbol)
                price = data.get('price', 'N/A')
                prices[symbol] = price
                logger.info(f"  ✓ {symbol}: ${price}")
            except Exception as e:
                logger.error(f"  ✗ {symbol} 查詢失敗: {e}")
        
        # 檢查新聞
        logger.info("\n📰 檢查最新新聞...")
        try:
            news = service.get_crypto_news(limit=3)
            logger.info(f"  ✓ 獲取了 {len(news)} 條新聞")
            for i, article in enumerate(news[:3], 1):
                logger.info(f"  {i}. {article.get('title', 'N/A')}")
        except Exception as e:
            logger.error(f"  ✗ 新聞查詢失敗: {e}")
        
        # 這裡可以添加發送 Telegram 通知的邏輯
        # 例如：當價格變動超過某個閾值時發送警報
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 單次檢查完成！")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ 執行錯誤: {e}", exc_info=True)
        sys.exit(1)

def main():
    """主入口 - GitHub Actions 單次執行模式"""
    
    # 檢查運行模式
    bot_mode = os.getenv('BOT_MODE', 'monitoring').lower()
    
    logger.info(f"🔧 運行模式: {bot_mode}")
    
    if bot_mode == 'monitoring':
        # 單次執行模式（適用於 GitHub Actions）
        run_single_check()
    else:
        # 如果未來需要 server 模式，可以在這裡處理
        logger.warning("⚠️  未知模式，使用單次執行模式")
        run_single_check()

if __name__ == '__main__':
    main()
