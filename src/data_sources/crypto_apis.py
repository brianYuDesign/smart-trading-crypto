"""
加密貨幣數據源 API 整合
整合多個加密貨幣數據提供商
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class CoinGeckoAPI:
    """CoinGecko API 客戶端 - 免費且功能強大的加密貨幣數據源"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'x-cg-pro-api-key': api_key})
    
    def get_coin_price(self, coin_ids: List[str], vs_currencies: List[str] = ['usd']) -> Dict:
        """
        獲取加密貨幣價格
        
        Args:
            coin_ids: 幣種 ID 列表，例如 ['bitcoin', 'ethereum']
            vs_currencies: 對標貨幣，默認 USD
        
        Returns:
            價格數據字典
        """
        try:
            endpoint = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': ','.join(vs_currencies),
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched prices for {len(coin_ids)} coins")
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching coin prices: {e}")
            return {}
    
    def get_coin_market_data(self, coin_id: str, vs_currency: str = 'usd') -> Dict:
        """
        獲取幣種詳細市場數據
        
        Args:
            coin_id: 幣種 ID，例如 'bitcoin'
            vs_currency: 對標貨幣
        
        Returns:
            詳細市場數據
        """
        try:
            endpoint = f"{self.BASE_URL}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 提取關鍵信息
            market_data = data.get('market_data', {})
            return {
                'id': data.get('id'),
                'symbol': data.get('symbol'),
                'name': data.get('name'),
                'current_price': market_data.get('current_price', {}).get(vs_currency),
                'market_cap': market_data.get('market_cap', {}).get(vs_currency),
                'market_cap_rank': data.get('market_cap_rank'),
                'total_volume': market_data.get('total_volume', {}).get(vs_currency),
                'price_change_24h': market_data.get('price_change_24h'),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                'price_change_percentage_7d': market_data.get('price_change_percentage_7d'),
                'price_change_percentage_30d': market_data.get('price_change_percentage_30d'),
                'ath': market_data.get('ath', {}).get(vs_currency),
                'ath_change_percentage': market_data.get('ath_change_percentage', {}).get(vs_currency),
                'atl': market_data.get('atl', {}).get(vs_currency),
                'atl_change_percentage': market_data.get('atl_change_percentage', {}).get(vs_currency),
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply'),
                'community_score': data.get('community_score'),
                'developer_score': data.get('developer_score'),
                'sentiment_votes_up_percentage': data.get('sentiment_votes_up_percentage'),
                'sentiment_votes_down_percentage': data.get('sentiment_votes_down_percentage'),
                'last_updated': data.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"Error fetching market data for {coin_id}: {e}")
            return {}
    
    def get_trending_coins(self) -> List[Dict]:
        """
        獲取熱門趨勢幣種
        
        Returns:
            趨勢幣種列表
        """
        try:
            endpoint = f"{self.BASE_URL}/search/trending"
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('coins', [])
            
        except Exception as e:
            logger.error(f"Error fetching trending coins: {e}")
            return []
    
    def get_global_market_data(self) -> Dict:
        """
        獲取全球加密貨幣市場數據
        
        Returns:
            全球市場統計
        """
        try:
            endpoint = f"{self.BASE_URL}/global"
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('data', {})
            return {
                'total_market_cap_usd': data.get('total_market_cap', {}).get('usd'),
                'total_volume_24h_usd': data.get('total_volume', {}).get('usd'),
                'bitcoin_dominance': data.get('market_cap_percentage', {}).get('btc'),
                'ethereum_dominance': data.get('market_cap_percentage', {}).get('eth'),
                'active_cryptocurrencies': data.get('active_cryptocurrencies'),
                'markets': data.get('markets'),
                'market_cap_change_percentage_24h': data.get('market_cap_change_percentage_24h_usd'),
                'updated_at': data.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Error fetching global market data: {e}")
            return {}


class CryptoPanicAPI:
    """CryptoPanic API 客戶端 - 加密貨幣新聞聚合"""
    
    BASE_URL = "https://cryptopanic.com/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def get_news(self, 
                 currencies: Optional[List[str]] = None,
                 filter_type: str = 'hot',
                 kind: str = 'news',
                 regions: str = 'en') -> List[Dict]:
        """
        獲取加密貨幣新聞
        
        Args:
            currencies: 幣種列表，例如 ['BTC', 'ETH']
            filter_type: 'rising' | 'hot' | 'bullish' | 'bearish' | 'important' | 'saved' | 'lol'
            kind: 'news' | 'media' | 'all'
            regions: 語言區域，'en' 為英文
        
        Returns:
            新聞列表
        """
        try:
            endpoint = f"{self.BASE_URL}/posts/"
            params = {
                'auth_token': self.api_key,
                'filter': filter_type,
                'kind': kind,
                'regions': regions,
                'public': 'true'
            }
            
            if currencies:
                params['currencies'] = ','.join(currencies)
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # 格式化新聞數據
            formatted_news = []
            for item in results:
                formatted_news.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'source': item.get('source', {}).get('title'),
                    'published_at': item.get('published_at'),
                    'created_at': item.get('created_at'),
                    'currencies': [c.get('code') for c in item.get('currencies', [])],
                    'votes': {
                        'negative': item.get('votes', {}).get('negative', 0),
                        'positive': item.get('votes', {}).get('positive', 0),
                        'important': item.get('votes', {}).get('important', 0),
                        'liked': item.get('votes', {}).get('liked', 0),
                        'disliked': item.get('votes', {}).get('disliked', 0),
                        'lol': item.get('votes', {}).get('lol', 0),
                        'toxic': item.get('votes', {}).get('toxic', 0),
                        'saved': item.get('votes', {}).get('saved', 0)
                    },
                    'sentiment': self._calculate_sentiment(item.get('votes', {}))
                })
            
            logger.info(f"Fetched {len(formatted_news)} news items")
            return formatted_news
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
    
    def _calculate_sentiment(self, votes: Dict) -> str:
        """
        計算新聞情緒
        
        Args:
            votes: 投票數據
        
        Returns:
            'positive' | 'negative' | 'neutral'
        """
        positive = votes.get('positive', 0) + votes.get('liked', 0)
        negative = votes.get('negative', 0) + votes.get('disliked', 0) + votes.get('toxic', 0)
        
        if positive > negative * 1.5:
            return 'positive'
        elif negative > positive * 1.5:
            return 'negative'
        else:
            return 'neutral'


class AlternativeMeAPI:
    """Alternative.me API - Fear & Greed Index"""
    
    BASE_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_fear_greed_index(self, limit: int = 1) -> List[Dict]:
        """
        獲取 Fear & Greed Index
        
        Args:
            limit: 獲取天數，1-最新，更多-歷史
        
        Returns:
            Fear & Greed 數據
        """
        try:
            params = {'limit': limit}
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('data', [])
            
            formatted_data = []
            for item in results:
                formatted_data.append({
                    'value': int(item.get('value')),
                    'value_classification': item.get('value_classification'),
                    'timestamp': item.get('timestamp'),
                    'time_until_update': item.get('time_until_update')
                })
            
            logger.info(f"Fetched Fear & Greed Index: {formatted_data[0] if formatted_data else 'N/A'}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
            return []


class CryptoDataAggregator:
    """加密貨幣數據聚合器 - 統一接口"""
    
    def __init__(self, config: Dict):
        """
        初始化數據聚合器
        
        Args:
            config: 配置字典，包含各 API 的配置
        """
        self.config = config
        
        # 初始化各 API 客戶端
        coingecko_config = config.get('crypto_apis', {}).get('coingecko', {})
        if coingecko_config.get('enabled'):
            self.coingecko = CoinGeckoAPI(coingecko_config.get('api_key'))
        else:
            self.coingecko = None
        
        cryptopanic_config = config.get('news_apis', {}).get('cryptopanic', {})
        if cryptopanic_config.get('enabled') and cryptopanic_config.get('api_key'):
            self.cryptopanic = CryptoPanicAPI(cryptopanic_config['api_key'])
        else:
            self.cryptopanic = None
        
        self.fear_greed = AlternativeMeAPI()
        
        logger.info("CryptoDataAggregator initialized")
    
    def get_market_overview(self, symbols: List[str] = ['bitcoin', 'ethereum', 'binancecoin']) -> Dict:
        """
        獲取市場概覽
        
        Args:
            symbols: 要查詢的幣種列表
        
        Returns:
            市場概覽數據
        """
        overview = {
            'timestamp': datetime.now().isoformat(),
            'coins': {},
            'global_data': {},
            'fear_greed_index': {},
            'trending': []
        }
        
        try:
            # 獲取全球市場數據
            if self.coingecko:
                overview['global_data'] = self.coingecko.get_global_market_data()
                
                # 獲取各幣種數據
                for symbol in symbols:
                    coin_data = self.coingecko.get_coin_market_data(symbol)
                    if coin_data:
                        overview['coins'][symbol] = coin_data
                
                # 獲取熱門幣種
                overview['trending'] = self.coingecko.get_trending_coins()
            
            # 獲取 Fear & Greed Index
            fear_greed_data = self.fear_greed.get_fear_greed_index()
            if fear_greed_data:
                overview['fear_greed_index'] = fear_greed_data[0]
            
            logger.info("Market overview fetched successfully")
            return overview
            
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return overview
    
    def get_crypto_news(self, 
                        currencies: Optional[List[str]] = None,
                        filter_type: str = 'hot',
                        limit: int = 20) -> List[Dict]:
        """
        獲取加密貨幣新聞
        
        Args:
            currencies: 幣種過濾
            filter_type: 新聞類型
            limit: 數量限制
        
        Returns:
            新聞列表
        """
        if not self.cryptopanic:
            logger.warning("CryptoPanic API not configured")
            return []
        
        try:
            news = self.cryptopanic.get_news(
                currencies=currencies,
                filter_type=filter_type
            )
            
            return news[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return []
    
    def analyze_market_sentiment(self) -> Dict:
        """
        分析整體市場情緒
        
        Returns:
            情緒分析結果
        """
        sentiment_analysis = {
            'timestamp': datetime.now().isoformat(),
            'fear_greed': {},
            'news_sentiment': {},
            'overall_sentiment': 'neutral',
            'confidence': 0.0
        }
        
        try:
            # 1. Fear & Greed Index
            fear_greed_data = self.fear_greed.get_fear_greed_index()
            if fear_greed_data:
                fg = fear_greed_data[0]
                sentiment_analysis['fear_greed'] = fg
            
            # 2. 新聞情緒
            if self.cryptopanic:
                important_news = self.cryptopanic.get_news(filter_type='important', kind='news')
                
                if important_news:
                    positive_count = sum(1 for n in important_news if n['sentiment'] == 'positive')
                    negative_count = sum(1 for n in important_news if n['sentiment'] == 'negative')
                    neutral_count = sum(1 for n in important_news if n['sentiment'] == 'neutral')
                    
                    total = len(important_news)
                    sentiment_analysis['news_sentiment'] = {
                        'positive_ratio': positive_count / total if total > 0 else 0,
                        'negative_ratio': negative_count / total if total > 0 else 0,
                        'neutral_ratio': neutral_count / total if total > 0 else 0,
                        'total_news': total
                    }
            
            # 3. 綜合判斷
            overall = self._calculate_overall_sentiment(sentiment_analysis)
            sentiment_analysis['overall_sentiment'] = overall['sentiment']
            sentiment_analysis['confidence'] = overall['confidence']
            
            logger.info(f"Market sentiment: {overall['sentiment']} (confidence: {overall['confidence']:.2f})")
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return sentiment_analysis
    
    def _calculate_overall_sentiment(self, data: Dict) -> Dict:
        """
        計算整體情緒
        
        Args:
            data: 情緒數據
        
        Returns:
            整體情緒和信心度
        """
        scores = []
        weights = []
        
        # Fear & Greed Index (0-100, 0=極度恐懼, 100=極度貪婪)
        fg_data = data.get('fear_greed', {})
        if fg_data:
            fg_value = fg_data.get('value', 50)
            scores.append((fg_value - 50) / 50)  # 標準化到 -1 到 1
            weights.append(0.6)  # 60% 權重
        
        # 新聞情緒
        news_data = data.get('news_sentiment', {})
        if news_data:
            pos_ratio = news_data.get('positive_ratio', 0)
            neg_ratio = news_data.get('negative_ratio', 0)
            news_score = pos_ratio - neg_ratio  # -1 到 1
            scores.append(news_score)
            weights.append(0.4)  # 40% 權重
        
        if not scores:
            return {'sentiment': 'neutral', 'confidence': 0.0}
        
        # 加權平均
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        confidence = min(sum(weights), 1.0)
        
        # 判斷情緒
        if weighted_score > 0.2:
            sentiment = 'positive'
        elif weighted_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': weighted_score
        }


# 示例使用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 配置示例
    config = {
        'crypto_apis': {
            'coingecko': {
                'enabled': True,
                'api_key': None  # 免費版不需要
            }
        },
        'news_apis': {
            'cryptopanic': {
                'enabled': True,
                'api_key': 'YOUR_API_KEY'  # 需要註冊獲取
            }
        }
    }
    
    # 創建聚合器
    aggregator = CryptoDataAggregator(config)
    
    # 獲取市場概覽
    print("\n=== 市場概覽 ===")
    overview = aggregator.get_market_overview(['bitcoin', 'ethereum'])
    print(f"比特幣價格: ${overview['coins']['bitcoin']['current_price']:,.2f}")
    print(f"比特幣市值排名: #{overview['coins']['bitcoin']['market_cap_rank']}")
    print(f"Fear & Greed Index: {overview['fear_greed_index']['value']} ({overview['fear_greed_index']['value_classification']})")
    
    # 獲取新聞
    print("\n=== 重要新聞 ===")
    news = aggregator.get_crypto_news(filter_type='important', limit=5)
    for i, item in enumerate(news, 1):
        print(f"{i}. [{item['sentiment'].upper()}] {item['title']}")
        print(f"   來源: {item['source']} | 幣種: {', '.join(item['currencies'])}")
    
    # 分析市場情緒
    print("\n=== 市場情緒分析 ===")
    sentiment = aggregator.analyze_market_sentiment()
    print(f"整體情緒: {sentiment['overall_sentiment'].upper()} (信心度: {sentiment['confidence']:.0%})")
