"""
加密貨幣數據服務 - 統一 API 整合層
整合 CoinGecko, CoinDesk, CryptoPanic 等真實數據源
支援智慧新聞源 Round-Robin 容錯機制
"""

import requests
import logging
from typing import Dict, List, Optional, Any, Callable
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
class NewsSourceHealth:
    """新聞源健康狀態追蹤"""
    name: str
    status: SourceStatus = SourceStatus.HEALTHY
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def is_available(self) -> bool:
        """是否可用"""
        if self.status == SourceStatus.COOLING:
            if self.cooldown_until and datetime.now() < self.cooldown_until:
                return False
            # 冷卻時間結束，重置狀態
            self.status = SourceStatus.HEALTHY
            self.consecutive_failures = 0
        return self.status != SourceStatus.FAILED


@dataclass
class NewsSource:
    """新聞源定義"""
    name: str
    fetch_function: Callable
    priority: int = 1
    max_failures: int = 3
    cooldown_seconds: int = 300  # 5分鐘
    health: NewsSourceHealth = field(init=False)
    
    def __post_init__(self):
        self.health = NewsSourceHealth(name=self.name)


class SmartNewsManager:
    """智慧新聞源管理器 - Round-Robin with Cooldown"""
    
    def __init__(self):
        self.sources: List[NewsSource] = []
        self.current_index = 0
    
    def register_source(self, source: NewsSource):
        """註冊新聞源"""
        self.sources.append(source)
        # 按優先級排序
        self.sources.sort(key=lambda x: x.priority)
        logger.info(f"Registered news source: {source.name} (priority: {source.priority})")
    
    def get_next_available_source(self) -> Optional[NewsSource]:
        """獲取下一個可用的新聞源 (Round-Robin)"""
        if not self.sources:
            return None
        
        # 嘗試所有源
        for _ in range(len(self.sources)):
            source = self.sources[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.sources)
            
            if source.health.is_available():
                return source
        
        # 所有源都不可用
        return None
    
    def fetch_news(self, *args, **kwargs) -> Optional[Dict]:
        """
        智慧獲取新聞 - 自動容錯切換
        
        返回格式：
        {
            'news': [...],
            'source': 'CryptoPanic',
            'success_rate': 95.0,
            'attempts': 2
        }
        """
        attempts = 0
        max_attempts = len(self.sources)
        
        while attempts < max_attempts:
            attempts += 1
            source = self.get_next_available_source()
            
            if not source:
                logger.error("No available news sources")
                return None
            
            logger.info(f"Attempting to fetch news from: {source.name} (attempt {attempts}/{max_attempts})")
            
            try:
                # 更新請求計數
                source.health.total_requests += 1
                
                # 調用獲取函數
                result = source.fetch_function(*args, **kwargs)
                
                if result and result.get('news'):
                    # 成功
                    source.health.successful_requests += 1
                    source.health.consecutive_failures = 0
                    source.health.last_success_time = datetime.now()
                    source.health.status = SourceStatus.HEALTHY
                    
                    logger.info(f"Successfully fetched news from {source.name}")
                    
                    # 添加元數據
                    result['source'] = source.name
                    result['success_rate'] = round(source.health.success_rate, 1)
                    result['attempts'] = attempts
                    
                    return result
                else:
                    # 空結果也算失敗
                    self._handle_source_failure(source)
                    
            except Exception as e:
                logger.error(f"Error fetching news from {source.name}: {e}")
                self._handle_source_failure(source)
        
        logger.error(f"Failed to fetch news after {attempts} attempts")
        return None
    
    def _handle_source_failure(self, source: NewsSource):
        """處理源失敗"""
        source.health.consecutive_failures += 1
        source.health.last_failure_time = datetime.now()
        
        if source.health.consecutive_failures >= source.max_failures:
            # 進入冷卻
            source.health.status = SourceStatus.COOLING
            source.health.cooldown_until = datetime.now() + timedelta(seconds=source.cooldown_seconds)
            logger.warning(
                f"{source.name} entered cooldown for {source.cooldown_seconds}s "
                f"(failures: {source.health.consecutive_failures})"
            )
        elif source.health.consecutive_failures >= source.max_failures // 2:
            # 降級狀態
            source.health.status = SourceStatus.DEGRADED
            logger.warning(f"{source.name} status: DEGRADED")
    
    def get_health_status(self) -> Dict:
        """獲取所有源的健康狀態"""
        return {
            source.name: {
                'status': source.health.status.value,
                'success_rate': round(source.health.success_rate, 1),
                'total_requests': source.health.total_requests,
                'successful_requests': source.health.successful_requests,
                'consecutive_failures': source.health.consecutive_failures,
                'last_success': source.health.last_success_time.isoformat() if source.health.last_success_time else None,
                'available': source.health.is_available()
            }
            for source in self.sources
        }


class CryptoDataService:
    """加密貨幣數據服務 - 統一接口"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.coindesk_base = "https://api.coindesk.com/v1"
        self.cryptopanic_base = "https://cryptopanic.com/api/v1"
        self.alternative_base = "https://api.alternative.me"
        
        # API Keys (如果有)
        self.cryptopanic_key = self.config.get('cryptopanic_api_key')
        
        # 請求限制
        self.last_request_time = {}
        self.min_request_interval = 1.0  # 秒
        
        # 初始化智慧新聞源管理器
        self.news_manager = SmartNewsManager()
        self._setup_news_sources()
        
    def _setup_news_sources(self):
        """設置新聞源（按優先級）"""
        # 1. CryptoPanic (優先，需要 API key)
        if self.cryptopanic_key:
            self.news_manager.register_source(NewsSource(
                name="CryptoPanic",
                fetch_function=self._fetch_cryptopanic_news,
                priority=1,
                max_failures=3,
                cooldown_seconds=300
            ))
        
        # 2. CoinDesk RSS (備用，免費)
        self.news_manager.register_source(NewsSource(
            name="CoinDesk RSS",
            fetch_function=self._fetch_coindesk_rss,
            priority=2,
            max_failures=3,
            cooldown_seconds=180
        ))
        
        logger.info(f"Initialized {len(self.news_manager.sources)} news sources")
    
    def _rate_limit(self, api_name: str):
        """簡單的速率限制"""
        now = time.time()
        if api_name in self.last_request_time:
            elapsed = now - self.last_request_time[api_name]
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time[api_name] = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, api_name: str = "default") -> Optional[Dict]:
        """統一的請求處理"""
        try:
            self._rate_limit(api_name)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            return None
    
    # ==================== 價格數據 ====================
    
    def get_coin_price(self, symbol: str) -> Optional[Dict]:
        """
        獲取加密貨幣詳細價格信息
        
        返回格式：
        {
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price': 45234.56,
            'price_change_24h': 2.34,
            'price_change_percentage_24h': 2.34,
            'high_24h': 46100.0,
            'low_24h': 44200.0,
            'market_cap': 885200000000,
            'market_cap_rank': 1,
            'total_volume': 28500000000,
            'circulating_supply': 19500000,
            'total_supply': 21000000,
            'last_updated': '2026-01-29T18:05:00Z'
        }
        """
        # 符號映射 (處理常見縮寫)
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2'
        }
        
        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        
        url = f"{self.coingecko_base}/coins/{coin_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        
        data = self._make_request(url, params, api_name="coingecko")
        
        if not data:
            return None
        
        try:
            market_data = data.get('market_data', {})
            return {
                'symbol': data.get('symbol', '').upper(),
                'name': data.get('name', ''),
                'price': market_data.get('current_price', {}).get('usd', 0),
                'price_change_24h': market_data.get('price_change_24h', 0),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                'high_24h': market_data.get('high_24h', {}).get('usd', 0),
                'low_24h': market_data.get('low_24h', {}).get('usd', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'market_cap_rank': market_data.get('market_cap_rank', 0),
                'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                'circulating_supply': market_data.get('circulating_supply', 0),
                'total_supply': market_data.get('total_supply', 0),
                'last_updated': data.get('last_updated', '')
            }
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing price data: {e}")
            return None
    
    # ==================== 市場數據 ====================
    
    def get_market_overview(self) -> Optional[Dict]:
        """
        獲取市場總覽
        
        返回格式：
        {
            'total_market_cap': 2150000000000,
            'total_volume': 98500000000,
            'market_cap_change_24h': 1.2,
            'btc_dominance': 41.2,
            'eth_dominance': 18.5,
            'top_coins': [...],
            'top_gainers': [...],
            'top_losers': [...]
        }
        """
        # 獲取全局市場數據
        global_url = f"{self.coingecko_base}/global"
        global_data = self._make_request(global_url, api_name="coingecko")
        
        # 獲取 Top 幣種
        markets_url = f"{self.coingecko_base}/coins/markets"
        markets_params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        markets_data = self._make_request(markets_url, markets_params, api_name="coingecko")
        
        if not global_data or not markets_data:
            return None
        
        try:
            global_info = global_data.get('data', {})
            market_cap_change = global_info.get('market_cap_change_percentage_24h_usd', 0)
            
            # 處理 Top 幣種
            top_coins = []
            for coin in markets_data[:5]:
                top_coins.append({
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'price': coin.get('current_price', 0),
                    'price_change_24h': coin.get('price_change_percentage_24h', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'rank': coin.get('market_cap_rank', 0)
                })
            
            # 漲跌幅排序
            sorted_by_change = sorted(markets_data, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
            
            top_gainers = []
            for coin in sorted_by_change[:3]:
                change = coin.get('price_change_percentage_24h', 0)
                if change > 0:
                    top_gainers.append({
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name', ''),
                        'change_24h': change
                    })
            
            top_losers = []
            for coin in sorted_by_change[-3:]:
                change = coin.get('price_change_percentage_24h', 0)
                if change < 0:
                    top_losers.append({
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name', ''),
                        'change_24h': change
                    })
            
            return {
                'total_market_cap': global_info.get('total_market_cap', {}).get('usd', 0),
                'total_volume': global_info.get('total_volume', {}).get('usd', 0),
                'market_cap_change_24h': market_cap_change,
                'btc_dominance': global_info.get('market_cap_percentage', {}).get('btc', 0),
                'eth_dominance': global_info.get('market_cap_percentage', {}).get('eth', 0),
                'top_coins': top_coins,
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'last_updated': datetime.now().isoformat()
            }
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing market data: {e}")
            return None
    
    def get_fear_greed_index(self) -> Optional[Dict]:
        """
        獲取恐懼貪婪指數
        
        返回格式：
        {
            'value': 68,
            'classification': 'Greed',
            'timestamp': '2026-01-29'
        }
        """
        url = f"{self.alternative_base}/fng/"
        params = {'limit': 1}
        
        data = self._make_request(url, params, api_name="alternative")
        
        if not data or 'data' not in data:
            return None
        
        try:
            fng_data = data['data'][0]
            return {
                'value': int(fng_data.get('value', 0)),
                'classification': fng_data.get('value_classification', ''),
                'timestamp': fng_data.get('timestamp', '')
            }
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Error parsing fear & greed data: {e}")
            return None
    
    # ==================== 新聞數據 ====================
    
    def get_crypto_news(self, currencies: Optional[List[str]] = None, limit: int = 5) -> Optional[Dict]:
        """
        獲取加密貨幣新聞（使用智慧源管理）
        
        參數:
            currencies: 幣種列表，如 ['BTC', 'ETH']
            limit: 返回新聞數量
        
        返回格式：
        {
            'news': [...],
            'source': 'CryptoPanic',
            'sentiment_summary': {...},
            'success_rate': 95.0,
            'attempts': 1
        }
        """
        return self.news_manager.fetch_news(currencies, limit)
    
    def _fetch_cryptopanic_news(self, currencies: Optional[List[str]] = None, limit: int = 5) -> Optional[Dict]:
        """從 CryptoPanic 獲取新聞"""
        url = f"{self.cryptopanic_base}/posts/"
        params = {
            'auth_token': self.cryptopanic_key,
            'public': 'true',
            'kind': 'news'
        }
        
        if currencies:
            params['currencies'] = ','.join([c.upper() for c in currencies])
        
        data = self._make_request(url, params, api_name="cryptopanic")
        
        if not data or 'results' not in data:
            return None
        
        try:
            news_list = []
            sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
            
            for item in data['results'][:limit]:
                votes = item.get('votes', {})
                sentiment = self._calculate_sentiment(votes)
                sentiment_counts[sentiment] += 1
                
                news_list.append({
                    'title': item.get('title', ''),
                    'published': item.get('published_at', ''),
                    'domain': item.get('domain', ''),
                    'url': item.get('url', ''),
                    'sentiment': sentiment,
                    'currencies': [c['code'] for c in item.get('currencies', [])]
                })
            
            # 計算情緒百分比
            total = len(news_list)
            sentiment_summary = {
                'positive': round(sentiment_counts['positive'] / total * 100) if total > 0 else 0,
                'neutral': round(sentiment_counts['neutral'] / total * 100) if total > 0 else 0,
                'negative': round(sentiment_counts['negative'] / total * 100) if total > 0 else 0
            }
            
            return {
                'news': news_list,
                'sentiment_summary': sentiment_summary
            }
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing CryptoPanic news: {e}")
            return None
    
    def _calculate_sentiment(self, votes: Dict) -> str:
        """根據投票計算情緒"""
        positive = votes.get('positive', 0)
        negative = votes.get('negative', 0)
        
        if positive > negative * 2:
            return 'positive'
        elif negative > positive * 2:
            return 'negative'
        else:
            return 'neutral'
    
    def _fetch_coindesk_rss(self, currencies: Optional[List[str]] = None, limit: int = 5) -> Optional[Dict]:
        """
        從 CoinDesk RSS 獲取新聞（備用源）
        """
        import feedparser
        
        try:
            feed_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                return None
            
            news_list = []
            for entry in feed.entries[:limit]:
                news_list.append({
                    'title': entry.get('title', ''),
                    'published': entry.get('published', ''),
                    'domain': 'coindesk.com',
                    'url': entry.get('link', ''),
                    'sentiment': 'neutral',  # RSS 無法判斷情緒
                    'currencies': []  # RSS 無法解析幣種
                })
            
            return {
                'news': news_list,
                'sentiment_summary': {
                    'positive': 0,
                    'neutral': 100,
                    'negative': 0
                }
            }
        except Exception as e:
            logger.error(f"Error parsing CoinDesk RSS: {e}")
            return None
    
    def get_news_health_status(self) -> Dict:
        """獲取新聞源健康狀態"""
        return self.news_manager.get_health_status()


# ==================== 輔助函數 ====================

def format_number(num: float, decimals: int = 2) -> str:
    """格式化數字（加入千位分隔符）"""
    if num >= 1_000_000_000_000:  # Trillion
        return f"${num / 1_000_000_000_000:.{decimals}f}T"
    elif num >= 1_000_000_000:  # Billion
        return f"${num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:  # Million
        return f"${num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:  # Thousand
        return f"${num / 1_000:.{decimals}f}K"
    else:
        return f"${num:,.{decimals}f}"


def format_percentage(value: float) -> str:
    """格式化百分比（帶正負號和 emoji）"""
    if value > 0:
        return f"+{value:.2f}% 📈"
    elif value < 0:
        return f"{value:.2f}% 📉"
    else:
        return f"{value:.2f}% ➡️"


def get_sentiment_emoji(sentiment: str) -> str:
    """根據情緒返回 emoji"""
    emoji_map = {
        'positive': '🚀',
        'neutral': '⚖️',
        'negative': '📉'
    }
    return emoji_map.get(sentiment.lower(), '⚖️')


def get_fng_emoji(value: int) -> str:
    """根據恐懼貪婪指數返回 emoji"""
    if value >= 75:
        return '🤑'  # Extreme Greed
    elif value >= 55:
        return '😊'  # Greed
    elif value >= 45:
        return '😐'  # Neutral
    elif value >= 25:
        return '😰'  # Fear
    else:
        return '😱'  # Extreme Fear
