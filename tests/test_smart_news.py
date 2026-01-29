"""
智慧新聞源管理系統測試範例
演示各種使用場景和功能
"""

import sys
import os
import time
import logging
from datetime import datetime

# 添加專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_sources.crypto_apis_v2 import (
    CryptoDataAggregator,
    SmartNewsManager,
    NewsSource,
    CryptoPanicAPI,
    CoinDeskAPI
)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_basic_usage():
    """測試 1: 基本使用"""
    print("\n" + "="*60)
    print("測試 1: 基本新聞獲取")
    print("="*60)
    
    config = {
        'cryptopanic_api_key': os.getenv('CRYPTOPANIC_API_KEY', 'demo_key'),
        'coingecko_api_key': None
    }
    
    aggregator = CryptoDataAggregator(config)
    
    # 獲取新聞
    news = aggregator.get_news(currencies=['BTC', 'ETH'])
    
    if news:
        print(f"✓ 成功獲取新聞")
        print(f"  來源: {news['source']}")
        print(f"  時間: {news['timestamp']}")
        print(f"  成功率: {news['success_rate']}")
        print(f"  新聞數量: {len(news['data'])}")
        
        # 顯示前 3 條新聞標題
        print(f"\n前 3 條新聞:")
        for i, article in enumerate(news['data'][:3], 1):
            print(f"  {i}. {article.get('title', 'N/A')[:60]}")
    else:
        print("✗ 獲取失敗")


def test_fallback_mechanism():
    """測試 2: 容錯切換機制"""
    print("\n" + "="*60)
    print("測試 2: 容錯切換機制")
    print("="*60)
    
    # 模擬失敗的新聞源
    def failing_source(**kwargs):
        raise Exception("API rate limit exceeded")
    
    def working_source(**kwargs):
        return [{
            'title': 'Test News Article',
            'source': 'TestSource',
            'published_at': datetime.now().isoformat()
        }]
    
    # 創建源
    sources = [
        NewsSource(
            name="FailingSource",
            fetch_function=failing_source,
            priority=1,
            max_failures=2,
            cooldown_seconds=10
        ),
        NewsSource(
            name="WorkingSource",
            fetch_function=working_source,
            priority=2,
            max_failures=3,
            cooldown_seconds=15
        )
    ]
    
    manager = SmartNewsManager(sources, enable_fallback=True)
    
    # 嘗試多次獲取
    print("\n連續請求 5 次，觀察容錯行為:")
    for i in range(5):
        print(f"\n第 {i+1} 次請求:")
        result = manager.fetch_news()
        
        if result:
            print(f"  ✓ 成功: {result['source']}")
        else:
            print(f"  ✗ 失敗")
        
        # 顯示源狀態
        for source in manager.sources:
            status = source.health.status.value
            failures = source.health.consecutive_failures
            available = "✓" if source.health.is_available else "✗"
            print(f"  [{available}] {source.name}: {status} (失敗: {failures})")
        
        time.sleep(1)


def test_health_monitoring():
    """測試 3: 健康狀態監控"""
    print("\n" + "="*60)
    print("測試 3: 健康狀態監控")
    print("="*60)
    
    config = {
        'cryptopanic_api_key': os.getenv('CRYPTOPANIC_API_KEY', 'demo_key'),
    }
    
    aggregator = CryptoDataAggregator(config)
    
    # 獲取健康報告
    health = aggregator.get_news_health_status()
    
    print(f"\n系統狀態:")
    print(f"  總新聞源: {health['total_sources']}")
    print(f"  可用源: {health['available_sources']}")
    print(f"  報告時間: {health['timestamp']}")
    
    print(f"\n各源詳細狀態:")
    for source in health['sources']:
        print(f"\n  【{source['name']}】")
        print(f"    狀態: {source['status']}")
        print(f"    優先級: {source['priority']}")
        print(f"    成功率: {source['success_rate']}")
        print(f"    連續失敗: {source['consecutive_failures']}")
        print(f"    可用: {'是' if source['is_available'] else '否'}")
        
        if source['cooldown_remaining']:
            print(f"    冷卻剩餘: {source['cooldown_remaining']} 秒")


def test_market_sentiment():
    """測試 4: 市場情緒分析"""
    print("\n" + "="*60)
    print("測試 4: 市場情緒分析")
    print("="*60)
    
    config = {
        'cryptopanic_api_key': os.getenv('CRYPTOPANIC_API_KEY', 'demo_key'),
        'coingecko_api_key': None
    }
    
    aggregator = CryptoDataAggregator(config)
    
    # 分析市場情緒
    sentiment = aggregator.analyze_market_sentiment()
    
    if sentiment:
        print(f"\n市場情緒分析結果:")
        
        # 恐懼貪婪指數
        fg_index = sentiment.get('fear_greed_index', {})
        if fg_index:
            print(f"\n  恐懼貪婪指數:")
            print(f"    數值: {fg_index.get('value', 'N/A')}")
            print(f"    分類: {fg_index.get('classification', 'N/A')}")
        
        # 新聞情緒
        news_sent = sentiment.get('news_sentiment', {})
        if news_sent:
            print(f"\n  新聞情緒統計:")
            print(f"    正面: {news_sent.get('positive', 0)}")
            print(f"    負面: {news_sent.get('negative', 0)}")
            print(f"    中性: {news_sent.get('neutral', 0)}")
            print(f"    總計: {news_sent.get('total', 0)}")
            print(f"    整體: {news_sent.get('overall', 'N/A')}")
        
        # 綜合判斷
        overall = sentiment.get('overall_sentiment', 'N/A')
        print(f"\n  綜合市場情緒: {overall}")
        
        if overall == 'bullish':
            print(f"    → 看漲，市場樂觀")
        elif overall == 'bearish':
            print(f"    → 看跌，市場悲觀")
        else:
            print(f"    → 中性，市場觀望")
    else:
        print("✗ 無法獲取市場情緒數據")


def test_continuous_monitoring():
    """測試 5: 持續監控模擬"""
    print("\n" + "="*60)
    print("測試 5: 持續監控（30秒，每10秒一次）")
    print("="*60)
    
    config = {
        'cryptopanic_api_key': os.getenv('CRYPTOPANIC_API_KEY', 'demo_key'),
    }
    
    aggregator = CryptoDataAggregator(config)
    
    for i in range(3):
        print(f"\n--- 檢查 {i+1}/3 ---")
        print(f"時間: {datetime.now().strftime('%H:%M:%S')}")
        
        # 獲取新聞
        news = aggregator.get_news()
        
        if news:
            print(f"✓ 成功: {news['source']}")
        else:
            print(f"✗ 失敗: 所有源都不可用")
        
        # 快速健康檢查
        health = aggregator.get_news_health_status()
        available = health['available_sources']
        total = health['total_sources']
        
        print(f"健康狀態: {available}/{total} 可用")
        
        if i < 2:  # 不在最後一次等待
            print("等待 10 秒...")
            time.sleep(10)


def test_market_overview():
    """測試 6: 市場概覽"""
    print("\n" + "="*60)
    print("測試 6: 市場概覽")
    print("="*60)
    
    config = {
        'coingecko_api_key': None
    }
    
    aggregator = CryptoDataAggregator(config)
    
    # 獲取主要幣種概覽
    coins = ['bitcoin', 'ethereum', 'solana']
    overview = aggregator.get_market_overview(coins)
    
    if overview:
        print(f"\n市場概覽:")
        print(f"  時間: {overview.get('timestamp', 'N/A')}")
        print(f"  追蹤幣種: {overview.get('coins_tracked', 0)}")
        
        # 價格信息
        prices = overview.get('prices', {})
        if prices:
            print(f"\n  當前價格:")
            for coin_id, data in prices.items():
                price = data.get('usd', 'N/A')
                change = data.get('usd_24h_change', 0)
                change_symbol = "↑" if change > 0 else "↓" if change < 0 else "→"
                
                print(f"    {coin_id.upper()}: ${price:,.2f} {change_symbol} {change:+.2f}%")
        
        # 市場情緒
        sentiment = overview.get('market_sentiment', {})
        if sentiment:
            print(f"\n  市場情緒:")
            print(f"    指數: {sentiment.get('value', 'N/A')}")
            print(f"    分類: {sentiment.get('classification', 'N/A')}")
    else:
        print("✗ 無法獲取市場概覽")


def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*60)
    print("智慧新聞源管理系統 - 測試套件")
    print("="*60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("基本使用", test_basic_usage),
        ("容錯切換", test_fallback_mechanism),
        ("健康監控", test_health_monitoring),
        ("市場情緒", test_market_sentiment),
        ("市場概覽", test_market_overview),
        ("持續監控", test_continuous_monitoring),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"\n✓ {test_name} 測試完成")
        except Exception as e:
            print(f"\n✗ {test_name} 測試失敗: {str(e)}")
            logger.exception(f"Test {test_name} failed")
        
        time.sleep(2)  # 間隔
    
    print("\n" + "="*60)
    print("所有測試完成！")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    # 檢查是否有命令行參數
    import argparse
    
    parser = argparse.ArgumentParser(description='智慧新聞源管理系統測試')
    parser.add_argument(
        '--test',
        type=int,
        choices=range(1, 7),
        help='運行特定測試（1-6）'
    )
    
    args = parser.parse_args()
    
    if args.test:
        # 運行特定測試
        test_map = {
            1: test_basic_usage,
            2: test_fallback_mechanism,
            3: test_health_monitoring,
            4: test_market_sentiment,
            5: test_continuous_monitoring,
            6: test_market_overview,
        }
        
        print(f"\n運行測試 {args.test}...")
        test_map[args.test]()
    else:
        # 運行所有測試
        run_all_tests()
