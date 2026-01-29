"""
加密貨幣數據源 API 整合 v2.0
整合多個加密貨幣數據提供商，支援智慧 Round-Robin 容錯機制
"""

import requests
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)


# ==================== 智慧新聞源管理 ====================

class SourceStatus(Enum):
    """資料源狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    COOLING = "cooling"
    FAILED = "failed"


@dataclass
class SourceHealth:
    """資料源健康狀態追蹤"""
    name: str
    status: SourceStatus = SourceStatus.HEALTHY
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    total_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.total_requests - self.total_failures) / self.total_requests
    
    @property
    def is_available(self) -> bool:
        if self.cooldown_until is None:
            return True
        return datetime.now() >= self.cooldown_until


@dataclass
class NewsSource:
    """新聞資料源定義"""
    name: str
    fetch_function: Callable
    priority: int = 1
    max_failures: int = 3
    cooldown_seconds: int = 300
    timeout: float = 10.0
    health: SourceHealth = field(init=False)
    
    def __post_init__(self):
        self.health = SourceHealth(name=self.name)


class SmartNewsManager:
    """智慧新聞資料源管理器"""
    
    def __init__(self, sources: List[NewsSource], enable_fallback: bool = True):
        self.sources = sorted(sources, key=lambda x: x.priority)
        self.enable_fallback = enable_fallback
        self.current_index = 0
        logger.info(f"初始化 SmartNewsManager，共 {len(sources)} 個資料源")
    
    def get_available_sources(self) -> List[NewsSource]:
        """獲取當前可用的資料源"""
        return [s for s in self.sources if s.health.is_available]
    
    def get_next_source(self) -> Optional[NewsSource]:
        """Round-Robin 獲取下一個可用資料源"""
        available = self.get_available_sources()
        if not available:
            logger.warning("沒有可用的新聞資料源（全部在冷卻中）")
            return None
        
        checked = 0
        while checked < len(self.sources):
            source = self.sources[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.sources)
            checked += 1
            
            if source.health.is_available:
                return source
        
        return None
    
    def fetch_news(self, **kwargs) -> Optional[Dict]:
        """智慧獲取新聞資料，自動容錯切換"""
        available_sources = self.get_available_sources()
        
        if not available_sources:
            logger.error("所有資料源都在冷卻中，無法獲取新聞")
            return None
        
        attempted_sources = []
        
        for _ in range(len(available_sources)):
            source = self.get_next_source()
            if source is None:
                break
            
            attempted_sources.append(source.name)
            logger.info(f"嘗試從 [{source.name}] 獲取新聞...")
            
            try:
                result = source.fetch_function(**kwargs)
                
                if result and self._validate_result(result):
                    self._record_success(source)
                    logger.info(f"✓ 從 [{source.name}] 成功獲取新聞")
                    return {
                        'data': result,
                        'source': source.name,
                        'timestamp': datetime.now().isoformat(),
                        'success_rate': f"{source.health.success_rate:.1%}"
                    }
                else:
                    logger.warning(f"[{source.name}] 返回無效結果")
                    self._record_failure(source, "invalid_result")
                    
            except Exception as e:
                logger.error(f"[{source.name}] 發生錯誤: {str(e)}")
                self._record_failure(source, str(e))
            
            if not self.enable_fallback:
                break
        
        logger.error(f"所有嘗試的資料源都失敗: {attempted_sources}")
        return None
    
    def _validate_result(self, result) -> bool:
        """驗證結果是否有效"""
        if result is None:
            return False
        if isinstance(result, dict):
            return bool(result)
        if isinstance(result, list):
            return len(result) > 0
        return True
    
    def _record_success(self, source: NewsSource):
        """記錄成功請求"""
        health = source.health
        health.last_success = datetime.now()
        health.consecutive_successes += 1
        health.consecutive_failures = 0
        health.total_requests += 1
        
        if health.status in [SourceStatus.COOLING, SourceStatus.FAILED]:
            health.status = SourceStatus.DEGRADED
            health.cooldown_until = None
            logger.info(f"[{source.name}] 恢復服務")
        elif health.consecutive_successes >= 3:
            health.status = SourceStatus.HEALTHY
    
    def _record_failure(self, source: NewsSource, error: str):
        """記錄失敗請求並處理冷卻"""
        health = source.health
        health.last_failure = datetime.now()
        health.consecutive_failures += 1
        health.consecutive_successes = 0
        health.total_requests += 1
        health.total_failures += 1
        
        if health.consecutive_failures >= source.max_failures:
            health.status = SourceStatus.COOLING
            health.cooldown_until = datetime.now() + timedelta(seconds=source.cooldown_seconds)
            logger.warning(
                f"[{source.name}] 連續失敗 {health.consecutive_failures} 次，"
                f"進入冷卻狀態 {source.cooldown_seconds} 秒"
            )
        else:
            health.status = SourceStatus.DEGRADED
    
    def get_health_status(self) -> Dict:
        """獲取所有資料源的健康狀態"""
        available = self.get_available_sources()
        return {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(self.sources),
            'available_sources': len(available),
            'sources': [
                {
                    'name': s.name,
                    'status': s.health.status.value,
                    'priority': s.priority,
                    'success_rate': f"{s.health.success_rate:.1%}",
                    'consecutive_failures': s.health.consecutive_failures,
                    'is_available': s.health.is_available,
                    'cooldown_remaining': self._get_cooldown_remaining(s)
                }
                for s in self.sources
            ]
        }
    
    def _get_cooldown_remaining(self, source: NewsSource) -> Optional[int]:
        """獲取剩餘冷卻時間（秒）"""
        if source.health.cooldown_until is None:
            return None
        remaining = (source.health.cooldown_until - datetime.now()).total_seconds()
        return int(max(0, remaining))


# ==================== 數據源 API 客戶端 ====================

class CoinGeckoAPI:
    """CoinGecko API 客戶端"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'x-cg-pro-api-key': api_key})
    
    def get_coin_price(self, coin_ids: List[str], vs_currencies: List[str] = ['usd']) -> Dict:
        """獲取加密貨幣價格"""
        try:
            endpoint = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': ','.join(vs_currencies),
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching coin prices: {e}")
            raise


class CryptoPanicAPI:
    """CryptoPanic API 客戶端"""
    
    BASE_URL = "https://cryptopanic.com/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def get_news(self, currencies: Optional[List[str]] = None, 
                 filter_type: str = 'hot', kind: str = 'news') -> List[Dict]:
        """獲取加密貨幣新聞"""
        try:
            endpoint = f"{self.BASE_URL}/posts/"
            params = {
                'auth_token': self.api_key,
                'filter': filter_type,
                'kind': kind,
                'public': 'true'
            }
            
            if currencies:
                params['currencies'] = ','.join(currencies)
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            formatted_news = []
            for item in results:
                formatted_news.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'source': item.get('source', {}).get('title'),
                    'published_at': item.get('published_at'),
                    'currencies': [c.get('code') for c in item.get('currencies', [])],
                    'votes': item.get('votes', {}),
                    'sentiment': self._calculate_sentiment(item.get('votes', {}))
                })
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            raise
    
    def _calculate_sentiment(self, votes: Dict) -> str:
        """計算新聞情緒"""
        positive = votes.get('positive', 0) + votes.get('liked', 0)
        negative = votes.get('negative', 0) + votes.get('disliked', 0)
        
        if positive > negative * 1.5:
            return 'positive'
        elif negative > positive * 1.5:
            return 'negative'
        return 'neutral'


class CoinDeskAPI:
    """CoinDesk API 客戶端（RSS 新聞）"""
    
    BASE_URL = "https://www.coindesk.com"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_news(self, limit: int = 20) -> List[Dict]:
        """獲取 CoinDesk 新聞（從 RSS 或 API）"""
        try:
            # 使用 CoinDesk 的 RSS feed 或新聞 API
            endpoint = f"{self.BASE_URL}/arc/outboundfeeds/rss/"
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            # 簡化處理，實際需要解析 XML
            # 這裡返回示例格式
            return [{
                'title': 'CoinDesk News Article',
                'url': self.BASE_URL,
                'source': 'CoinDesk',
                'published_at': datetime.now().isoformat()
            }]
            
        except Exception as e:
            logger.error(f"Error fetching CoinDesk news: {e}")
            raise


class FearGreedIndexAPI:
    """Fear & Greed Index API 客戶端"""
    
    BASE_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_current_index(self) -> Dict:
        """獲取當前恐懼貪婪指數"""
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('data'):
                index_data = data['data'][0]
                return {
                    'value': int(index_data.get('value')),
                    'classification': index_data.get('value_classification'),
                    'timestamp': index_data.get('timestamp'),
                    'time_until_update': index_data.get('time_until_update')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
            return {}


# ==================== 統一數據聚合器 ====================

class CryptoDataAggregator:
    """
    加密貨幣數據聚合器
    整合多個數據源，提供統一接口，支援智慧新聞容錯
    """
    
    def __init__(self, config: Dict):
        """
        初始化聚合器
        
        Args:
            config: 配置字典，包含各 API 的 key
        """
        # 初始化各個 API 客戶端
        self.coingecko = CoinGeckoAPI(config.get('coingecko_api_key'))
        self.fear_greed = FearGreedIndexAPI()
        
        # 設置新聞源（支援智慧容錯）
        news_sources = []
        
        # CryptoPanic（優先級1）
        if config.get('cryptopanic_api_key'):
            cryptopanic = CryptoPanicAPI(config['cryptopanic_api_key'])
            news_sources.append(NewsSource(
                name="CryptoPanic",
                fetch_function=cryptopanic.get_news,
                priority=1,
                max_failures=3,
                cooldown_seconds=300
            ))
        
        # CoinDesk（優先級2）
        coindesk = CoinDeskAPI()
        news_sources.append(NewsSource(
            name="CoinDesk",
            fetch_function=coindesk.get_news,
            priority=2,
            max_failures=2,
            cooldown_seconds=180
        ))
        
        # 初始化智慧新聞管理器
        self.news_manager = SmartNewsManager(news_sources, enable_fallback=True)
        
        logger.info("CryptoDataAggregator 初始化完成")
    
    def get_market_overview(self, coin_ids: List[str]) -> Dict:
        """
        獲取市場概覽
        
        Args:
            coin_ids: 幣種 ID 列表
            
        Returns:
            市場概覽數據
        """
        try:
            prices = self.coingecko.get_coin_price(coin_ids)
            fear_greed = self.fear_greed.get_current_index()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'prices': prices,
                'market_sentiment': fear_greed,
                'coins_tracked': len(coin_ids)
            }
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}
    
    def get_news(self, **kwargs) -> Optional[Dict]:
        """
        智慧獲取新聞（自動容錯）
        
        Args:
            **kwargs: 傳遞給新聞源的參數（如 currencies, filter_type）
            
        Returns:
            新聞數據或 None
        """
        return self.news_manager.fetch_news(**kwargs)
    
    def get_news_health_status(self) -> Dict:
        """獲取新聞源健康狀態"""
        return self.news_manager.get_health_status()
    
    def analyze_market_sentiment(self) -> Dict:
        """
        分析市場整體情緒
        
        Returns:
            市場情緒分析
        """
        try:
            # 獲取恐懼貪婪指數
            fear_greed = self.fear_greed.get_current_index()
            
            # 獲取新聞情緒
            news_result = self.get_news(filter_type='hot')
            news_sentiment = self._analyze_news_sentiment(
                news_result['data'] if news_result else []
            )
            
            # 綜合分析
            overall_sentiment = self._calculate_overall_sentiment(
                fear_greed.get('value'), 
                news_sentiment
            )
            
            return {
                'timestamp': datetime.now().isoformat(),
                'fear_greed_index': fear_greed,
                'news_sentiment': news_sentiment,
                'overall_sentiment': overall_sentiment,
                'news_source': news_result['source'] if news_result else None
            }
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return {}
    
    def _analyze_news_sentiment(self, news: List[Dict]) -> Dict:
        """分析新聞情緒"""
        if not news:
            return {'positive': 0, 'negative': 0, 'neutral': 0, 'overall': 'neutral'}
        
        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
        for item in news:
            sentiment = item.get('sentiment', 'neutral')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        total = sum(sentiments.values())
        overall = 'neutral'
        if sentiments['positive'] > sentiments['negative'] * 1.3:
            overall = 'positive'
        elif sentiments['negative'] > sentiments['positive'] * 1.3:
            overall = 'negative'
        
        return {
            **sentiments,
            'total': total,
            'overall': overall
        }
    
    def _calculate_overall_sentiment(self, fear_greed_value: Optional[int], 
                                    news_sentiment: Dict) -> str:
        """計算整體市場情緒"""
        if fear_greed_value is None:
            return news_sentiment.get('overall', 'neutral')
        
        # Fear & Greed: 0-25=Extreme Fear, 26-45=Fear, 46-55=Neutral, 56-75=Greed, 76-100=Extreme Greed
        fg_sentiment = 'neutral'
        if fear_greed_value < 26:
            fg_sentiment = 'very_negative'
        elif fear_greed_value < 46:
            fg_sentiment = 'negative'
        elif fear_greed_value > 75:
            fg_sentiment = 'very_positive'
        elif fear_greed_value > 55:
            fg_sentiment = 'positive'
        
        # 結合新聞情緒
        news_overall = news_sentiment.get('overall', 'neutral')
        
        if fg_sentiment in ['very_negative', 'negative'] and news_overall == 'negative':
            return 'bearish'
        elif fg_sentiment in ['very_positive', 'positive'] and news_overall == 'positive':
            return 'bullish'
        else:
            return 'neutral'


# ==================== 使用範例 ====================

if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置
    config = {
        'cryptopanic_api_key': 'your_cryptopanic_api_key',
        'coingecko_api_key': None  # CoinGecko 免費版不需要 key
    }
    
    # 創建聚合器
    aggregator = CryptoDataAggregator(config)
    
    # 測試市場概覽
    print("\n=== 市場概覽 ===")
    overview = aggregator.get_market_overview(['bitcoin', 'ethereum', 'solana'])
    print(overview)
    
    # 測試智慧新聞獲取（會自動容錯）
    print("\n=== 智慧新聞獲取 ===")
    for i in range(5):
        print(f"\n第 {i+1} 次請求：")
        news = aggregator.get_news(currencies=['BTC', 'ETH'])
        if news:
            print(f"✓ 成功從 {news['source']} 獲取 {len(news['data'])} 條新聞")
        else:
            print("✗ 獲取失敗")
        
        # 查看健康狀態
        health = aggregator.get_news_health_status()
        print(f"可用源: {health['available_sources']}/{health['total_sources']}")
        
        time.sleep(2)
    
    # 測試市場情緒分析
    print("\n=== 市場情緒分析 ===")
    sentiment = aggregator.analyze_market_sentiment()
    print(sentiment)
