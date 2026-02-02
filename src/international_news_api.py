"""
國際區塊鏈新聞 API 整合模組
支援 CryptoCompare 和 CoinGecko API
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class InternationalNewsAPI:
    """國際區塊鏈新聞 API 整合器"""
    
    def __init__(self):
        self.cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
        self.cryptocompare_base = 'https://min-api.cryptocompare.com/data/v2/news/'
        self.coingecko_base = 'https://api.coingecko.com/api/v3/news'
        
        # 快取時間 (秒)
        self.cache_ttl = int(os.getenv('NEWS_CACHE_TTL', '300'))
        
    @lru_cache(maxsize=10)
    def _fetch_with_cache(self, url: str, cache_key: str) -> Optional[dict]:
        """帶快取的 HTTP 請求 (透過 lru_cache 實現簡單快取)"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_cryptocompare_news(
        self, 
        limit: int = 10, 
        lang: str = 'EN',
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        從 CryptoCompare 獲取新聞
        
        Args:
            limit: 新聞數量 (預設 10)
            lang: 語言代碼 (EN, ZH)
            categories: 分類列表 (BTC, ETH, Trading, Blockchain, etc.)
        
        Returns:
            List[Dict]: 標準化新聞列表
        """
        try:
            params = {
                'lang': lang
            }
            
            # 只在有 API key 時添加
            if self.cryptocompare_key:
                params['api_key'] = self.cryptocompare_key
            
            if categories:
                params['categories'] = ','.join(categories)
            
            # 排除贊助內容
            params['excludeCategories'] = 'Sponsored'
            
            url = self.cryptocompare_base
            logger.info(f"Fetching CryptoCompare news: {url}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # CryptoCompare API 可能返回不同格式
            if isinstance(data, list):
                # 直接返回列表格式
                news_items = data[:limit]
            elif data.get('Data'):
                # 標準格式
                news_items = data.get('Data', [])[:limit]
            else:
                logger.error(f"CryptoCompare unexpected format: {data.get('Message', 'Unknown')}")
                return []
            
            # 標準化格式
            standardized = []
            for item in news_items:
                standardized.append({
                    'title': item.get('title', 'No Title'),
                    'description': item.get('body', '')[:200] + '...',
                    'url': item.get('url', ''),
                    'source': item.get('source', 'CryptoCompare'),
                    'published_at': datetime.fromtimestamp(item.get('published_on', 0)),
                    'image_url': item.get('imageurl', ''),
                    'categories': item.get('categories', '').split('|'),
                    'lang': item.get('lang', 'EN')
                })
            
            logger.info(f"✓ Fetched {len(standardized)} news from CryptoCompare")
            return standardized
            
        except Exception as e:
            logger.error(f"CryptoCompare news fetch failed: {e}")
            return []
    
    def get_cryptocompare_news_by_source(self, source: str, limit: int = 10) -> List[Dict]:
        """
        從 CryptoCompare 獲取特定來源的新聞
        
        Args:
            source: 新聞來源 (coindesk, cointelegraph, etc.)
            limit: 新聞數量
        
        Returns:
            List[Dict]: 標準化新聞列表
        """
        try:
            params = {
                'feeds': source,
                'lang': 'EN'
            }
            
            url = self.cryptocompare_base
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('Data'):
                return []
            
            news_items = data.get('Data', [])[:limit]
            
            # 標準化格式
            standardized = []
            for item in news_items:
                standardized.append({
                    'title': item.get('title', 'No Title'),
                    'description': item.get('body', '')[:200] + '...' if item.get('body') else '',
                    'url': item.get('url', ''),
                    'source': item.get('source', source.title()),
                    'published_at': datetime.fromtimestamp(item.get('published_on', 0)),
                    'image_url': item.get('imageurl', ''),
                    'categories': item.get('categories', '').split('|') if item.get('categories') else [],
                    'lang': item.get('lang', 'EN')
                })
            
            logger.info(f"✓ Fetched {len(standardized)} news from {source}")
            return standardized
            
        except Exception as e:
            logger.error(f"{source} news fetch failed: {e}")
            return []
    
    def get_international_news(
        self, 
        limit: int = 10,
        lang: str = 'EN',
        sources: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        獲取國際新聞 (使用 CryptoCompare API)
        
        Args:
            limit: 新聞數量
            lang: 語言代碼 (EN, ZH)
            sources: 指定新聞來源列表 (可選)
        
        Returns:
            List[Dict]: 新聞列表
        """
        logger.info(f"🌍 Fetching international news (lang={lang}, limit={limit})")
        
        # 獲取新聞
        news = self.get_cryptocompare_news(limit=limit, lang=lang)
        
        if not news:
            logger.error("❌ Failed to fetch international news")
            return []
        
        return news
    
    def format_news_for_telegram(self, news_list: List[Dict], show_detail: bool = False) -> str:
        """
        格式化新聞為 Telegram 訊息
        
        Args:
            news_list: 新聞列表
            show_detail: 是否顯示詳細內容
        
        Returns:
            str: 格式化的 Telegram 訊息 (Markdown)
        """
        if not news_list:
            return "❌ 目前無法獲取國際新聞，請稍後再試。"
        
        lines = ["📰 *最新國際區塊鏈新聞* (International)\n"]
        
        for i, news in enumerate(news_list, 1):
            title = news['title']
            source = news['source']
            url = news['url']
            published = news['published_at']
            
            # 計算時間差
            time_diff = datetime.now() - published
            if time_diff < timedelta(hours=1):
                time_str = f"{int(time_diff.total_seconds() / 60)} mins ago"
            elif time_diff < timedelta(days=1):
                time_str = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            else:
                time_str = f"{int(time_diff.days)} days ago"
            
            # 列表格式
            if not show_detail:
                lines.append(f"{i}. 🌍 *{source}* | {title}")
                lines.append(f"   📅 {time_str}")
                lines.append(f"   🔗 [Read more]({url})\n")
            else:
                # 詳細格式
                description = news['description']
                lines.append(f"*{i}. {title}*")
                lines.append(f"🌍 Source: {source}")
                lines.append(f"📅 {time_str}")
                lines.append(f"📰 {description}")
                lines.append(f"🔗 [Read full article]({url})")
                lines.append("─" * 40 + "\n")
        
        if not show_detail:
            lines.append("\n💬 _輸入數字查看詳情，或使用 /news\\_en 重新整理_")
        
        return '\n'.join(lines)


# 全域實例
international_news_api = InternationalNewsAPI()


# 便捷函數
def get_english_news(limit: int = 10) -> List[Dict]:
    """獲取英文新聞"""
    return international_news_api.get_international_news(limit=limit, lang='EN')


def get_international_news_text(limit: int = 10, detailed: bool = False) -> str:
    """獲取格式化的國際新聞文本"""
    news = get_english_news(limit=limit)
    return international_news_api.format_news_for_telegram(news, show_detail=detailed)


if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 80)
    print("🧪 Testing International News API")
    print("=" * 80)
    
    # 測試 CryptoCompare
    api = InternationalNewsAPI()
    news = api.get_cryptocompare_news(limit=5)
    
    if news:
        print(f"\n✅ CryptoCompare: {len(news)} news items fetched\n")
        print("📰 Sample news items:")
        for i, item in enumerate(news[:3], 1):
            print(f"\n{i}. {item['title'][:80]}...")
            print(f"   Source: {item['source']}")
            print(f"   Published: {item['published_at'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   URL: {item['url'][:60]}...")
    else:
        print("❌ CryptoCompare failed")
    
    print("\n" + "=" * 80)
    print("📱 Telegram Message Format Preview:")
    print("=" * 80)
    
    message = get_international_news_text(limit=5)
    print(message)
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)
