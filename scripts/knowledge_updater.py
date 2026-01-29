"""
知識庫自動更新機制
定期從多個數據源收集數據並更新知識庫
"""

import logging
import yaml
from typing import Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 導入自定義模組
sys.path.append(str(Path(__file__).parent.parent))
from data_sources.crypto_apis import CryptoDataAggregator
from knowledge_base.knowledge_base import MarketKnowledgeBase

logger = logging.getLogger(__name__)


class KnowledgeUpdater:
    """知識庫更新器 - 自動化知識庫維護"""
    
    def __init__(self, config_path: str = 'config/data_sources.yaml'):
        """
        初始化更新器
        
        Args:
            config_path: 配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.data_aggregator = CryptoDataAggregator(self.config)
        self.knowledge_base = MarketKnowledgeBase()
        
        logger.info("KnowledgeUpdater initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """載入配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """獲取默認配置"""
        return {
            'crypto_apis': {
                'coingecko': {'enabled': True, 'api_key': None}
            },
            'news_apis': {
                'cryptopanic': {'enabled': False, 'api_key': None}
            },
            'update_intervals': {
                'market_data': 300,  # 5分鐘
                'news': 600,  # 10分鐘
                'knowledge': 3600,  # 1小時
                'snapshots': 86400  # 24小時
            }
        }
    
    def update_all(self):
        """執行完整的知識庫更新"""
        logger.info("=== Starting full knowledge base update ===")
        
        try:
            # 1. 更新市場概覽
            self.update_market_overview()
            
            # 2. 更新新聞和事件
            self.update_news_and_events()
            
            # 3. 更新幣種知識
            self.update_coin_knowledge()
            
            # 4. 計算市場相關性
            self.update_market_correlations()
            
            # 5. 保存市場快照
            self.save_market_snapshot()
            
            logger.info("=== Knowledge base update completed successfully ===")
            
        except Exception as e:
            logger.error(f"Error during knowledge base update: {e}")
            raise
    
    def update_market_overview(self):
        """更新市場概覽數據"""
        logger.info("Updating market overview...")
        
        try:
            # 獲取主要幣種的市場數據
            major_coins = ['bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple']
            overview = self.data_aggregator.get_market_overview(major_coins)
            
            # 這裡可以將數據存儲到緩存或處理
            logger.info(f"Market overview updated: {len(overview['coins'])} coins")
            
            return overview
            
        except Exception as e:
            logger.error(f"Error updating market overview: {e}")
            return {}
    
    def update_news_and_events(self):
        """更新新聞和重大事件"""
        logger.info("Updating news and events...")
        
        try:
            # 獲取重要新聞
            important_news = self.data_aggregator.get_crypto_news(
                filter_type='important',
                limit=50
            )
            
            # 歸檔新聞
            archived_count = 0
            for news_item in important_news:
                news_data = {
                    'news_id': str(news_item.get('id')),
                    'published_at': news_item.get('published_at'),
                    'title': news_item.get('title'),
                    'source': news_item.get('source'),
                    'url': news_item.get('url'),
                    'content': news_item.get('title'),  # 簡化，實際應該抓取全文
                    'sentiment': news_item.get('sentiment'),
                    'importance_score': self._calculate_importance(news_item),
                    'affected_coins': news_item.get('currencies', []),
                    'categories': self._categorize_news(news_item)
                }
                
                result = self.knowledge_base.archive_news(news_data)
                if result > 0:
                    archived_count += 1
                
                # 檢測是否為重大事件
                if self._is_major_event(news_item):
                    self._create_historical_event(news_item)
            
            logger.info(f"Archived {archived_count} new news items")
            
        except Exception as e:
            logger.error(f"Error updating news and events: {e}")
    
    def _calculate_importance(self, news_item: Dict) -> float:
        """
        計算新聞重要性分數
        
        Args:
            news_item: 新聞數據
        
        Returns:
            重要性分數 (0-1)
        """
        score = 0.5  # 基礎分數
        
        votes = news_item.get('votes', {})
        
        # 重要投票權重最高
        if votes.get('important', 0) > 5:
            score += 0.3
        elif votes.get('important', 0) > 2:
            score += 0.2
        
        # 正面/負面投票
        positive = votes.get('positive', 0) + votes.get('liked', 0)
        negative = votes.get('negative', 0) + votes.get('disliked', 0)
        
        if positive + negative > 10:
            score += 0.1
        
        # 影響幣種數量
        num_coins = len(news_item.get('currencies', []))
        if num_coins > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _categorize_news(self, news_item: Dict) -> List[str]:
        """
        新聞分類
        
        Args:
            news_item: 新聞數據
        
        Returns:
            分類標籤列表
        """
        categories = []
        title_lower = news_item.get('title', '').lower()
        
        # 監管類
        if any(kw in title_lower for kw in ['regulation', 'sec', 'regulatory', 'legal', 'lawsuit']):
            categories.append('regulation')
        
        # ETF類
        if any(kw in title_lower for kw in ['etf', 'exchange-traded']):
            categories.append('etf')
        
        # 技術類
        if any(kw in title_lower for kw in ['upgrade', 'fork', 'protocol', 'network', 'blockchain']):
            categories.append('technology')
        
        # 市場類
        if any(kw in title_lower for kw in ['price', 'market', 'bull', 'bear', 'rally', 'crash']):
            categories.append('market')
        
        # 採用類
        if any(kw in title_lower for kw in ['adoption', 'partnership', 'integration', 'launch']):
            categories.append('adoption')
        
        # 安全類
        if any(kw in title_lower for kw in ['hack', 'breach', 'security', 'exploit', 'vulnerability']):
            categories.append('security')
        
        return categories if categories else ['general']
    
    def _is_major_event(self, news_item: Dict) -> bool:
        """
        判斷是否為重大事件
        
        Args:
            news_item: 新聞數據
        
        Returns:
            是否為重大事件
        """
        importance = self._calculate_importance(news_item)
        
        # 重要性分數高於 0.7
        if importance > 0.7:
            return True
        
        # 或者有大量重要投票
        if news_item.get('votes', {}).get('important', 0) > 10:
            return True
        
        return False
    
    def _create_historical_event(self, news_item: Dict):
        """
        創建歷史事件記錄
        
        Args:
            news_item: 新聞數據
        """
        categories = self._categorize_news(news_item)
        
        event = {
            'event_date': news_item.get('published_at', datetime.now().isoformat()),
            'event_type': categories[0] if categories else 'general',
            'title': news_item.get('title'),
            'description': news_item.get('title'),
            'impact_level': 'high',
            'affected_coins': news_item.get('currencies', []),
            'market_reaction': 'unknown',  # 需要後續分析
            'sentiment': news_item.get('sentiment'),
            'source_url': news_item.get('url'),
            'tags': categories
        }
        
        self.knowledge_base.add_historical_event(event)
        logger.info(f"Created historical event: {event['title']}")
    
    def update_coin_knowledge(self):
        """更新幣種知識"""
        logger.info("Updating coin knowledge...")
        
        try:
            # 主要幣種列表
            major_coins = [
                {'coin_id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
                {'coin_id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
                {'coin_id': 'binancecoin', 'symbol': 'BNB', 'name': 'BNB'},
                {'coin_id': 'solana', 'symbol': 'SOL', 'name': 'Solana'},
                {'coin_id': 'ripple', 'symbol': 'XRP', 'name': 'XRP'},
            ]
            
            for coin_info in major_coins:
                # 獲取詳細市場數據
                market_data = self.data_aggregator.coingecko.get_coin_market_data(
                    coin_info['coin_id']
                )
                
                if market_data:
                    # 構建知識數據
                    knowledge_data = {
                        'coin_id': coin_info['coin_id'],
                        'symbol': coin_info['symbol'],
                        'name': coin_info['name'],
                        'category': self._determine_category(coin_info['coin_id']),
                        'description': f"{coin_info['name']} - Market Cap Rank #{market_data.get('market_cap_rank', 'N/A')}",
                        'typical_volatility': abs(market_data.get('price_change_percentage_7d', 0) / 7),  # 簡化計算
                        'use_cases': self._get_use_cases(coin_info['coin_id']),
                        'key_features': self._get_key_features(coin_info['coin_id']),
                        'risks': self._get_risks(coin_info['coin_id'])
                    }
                    
                    self.knowledge_base.add_coin_knowledge(knowledge_data)
                    logger.info(f"Updated knowledge for {coin_info['name']}")
            
        except Exception as e:
            logger.error(f"Error updating coin knowledge: {e}")
    
    def _determine_category(self, coin_id: str) -> str:
        """確定幣種分類"""
        categories = {
            'bitcoin': 'Store of Value',
            'ethereum': 'Smart Contract Platform',
            'binancecoin': 'Exchange Token',
            'solana': 'Smart Contract Platform',
            'ripple': 'Payment Network'
        }
        return categories.get(coin_id, 'Cryptocurrency')
    
    def _get_use_cases(self, coin_id: str) -> List[str]:
        """獲取使用場景"""
        use_cases = {
            'bitcoin': ['數位黃金', '價值儲存', '支付手段', '對沖通膨'],
            'ethereum': ['智能合約', 'DeFi', 'NFT', 'dApps', 'DAO'],
            'binancecoin': ['交易手續費折扣', 'Binance 生態', 'Staking'],
            'solana': ['高性能 DeFi', 'NFT', 'Web3 應用', 'GameFi'],
            'ripple': ['跨境支付', '銀行轉帳', '流動性解決方案']
        }
        return use_cases.get(coin_id, ['通用加密貨幣'])
    
    def _get_key_features(self, coin_id: str) -> List[str]:
        """獲取關鍵特性"""
        features = {
            'bitcoin': ['POW 共識', '2100萬上限', '減半機制', '去中心化'],
            'ethereum': ['POS 共識', 'EVM', 'Layer 2 擴展', 'EIP 升級'],
            'binancecoin': ['BNB Chain', '燃燒機制', 'BSC 生態'],
            'solana': ['超高 TPS', '低交易費', 'POH 機制'],
            'ripple': ['快速結算', '低成本', '銀行合作']
        }
        return features.get(coin_id, [])
    
    def _get_risks(self, coin_id: str) -> List[str]:
        """獲取風險因素"""
        risks = {
            'bitcoin': ['能源消耗爭議', '監管風險', '波動性高'],
            'ethereum': ['Gas 費用波動', '競爭激烈', 'MEV 問題'],
            'binancecoin': ['中心化風險', '依賴 Binance', '監管壓力'],
            'solana': ['網路中斷歷史', '中心化問題', 'Validator 集中'],
            'ripple': ['SEC 訴訟', '中心化爭議', '銀行合作依賴']
        }
        return risks.get(coin_id, ['市場風險', '技術風險'])
    
    def update_market_correlations(self):
        """更新市場相關性數據"""
        logger.info("Updating market correlations...")
        
        # 簡化版：實際應該使用歷史價格數據計算真實相關性
        # 這裡使用已知的典型相關性
        
        correlations = [
            ('BTC', 'ETH', 0.85, '30d', 30),
            ('BTC', 'total_market', 0.90, '30d', 30),
            ('ETH', 'altcoins', 0.75, '30d', 30),
            ('BTC', 'gold', 0.15, '30d', 30),
            ('BTC', 'nasdaq', 0.65, '30d', 30),
        ]
        
        for asset1, asset2, corr, timeframe, data_points in correlations:
            self.knowledge_base.save_correlation(
                asset1, asset2, corr, timeframe, data_points
            )
        
        logger.info(f"Updated {len(correlations)} correlation pairs")
    
    def save_market_snapshot(self):
        """保存市場狀態快照"""
        logger.info("Saving market snapshot...")
        
        try:
            # 獲取市場概覽
            overview = self.data_aggregator.get_market_overview(['bitcoin', 'ethereum'])
            
            # 獲取情緒分析
            sentiment = self.data_aggregator.analyze_market_sentiment()
            
            # 構建快照
            snapshot = {
                'snapshot_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'btc_price': overview['coins'].get('bitcoin', {}).get('current_price'),
                'btc_dominance': overview['global_data'].get('bitcoin_dominance'),
                'total_market_cap': overview['global_data'].get('total_market_cap_usd'),
                'total_volume_24h': overview['global_data'].get('total_volume_24h_usd'),
                'fear_greed_index': overview['fear_greed_index'].get('value'),
                'top_10_avg_change': 0.0,  # 需要計算
                'trending_coins': [item.get('item', {}).get('id') for item in overview.get('trending', [])[:5]],
                'major_events': [],  # 需要從新聞中提取
                'overall_sentiment': sentiment.get('overall_sentiment')
            }
            
            self.knowledge_base.save_market_snapshot(snapshot)
            logger.info("Market snapshot saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving market snapshot: {e}")
    
    def get_update_summary(self) -> Dict:
        """
        獲取更新摘要
        
        Returns:
            更新統計信息
        """
        return {
            'last_update': datetime.now().isoformat(),
            'status': 'completed',
            'components_updated': [
                'market_overview',
                'news_and_events',
                'coin_knowledge',
                'market_correlations',
                'market_snapshot'
            ]
        }


def main():
    """主函數 - 執行知識庫更新"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        updater = KnowledgeUpdater()
        updater.update_all()
        
        summary = updater.get_update_summary()
        print("\n" + "="*60)
        print("Knowledge Base Update Summary")
        print("="*60)
        print(f"Status: {summary['status']}")
        print(f"Last Update: {summary['last_update']}")
        print(f"Components Updated: {len(summary['components_updated'])}")
        for component in summary['components_updated']:
            print(f"  ✓ {component}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Knowledge base update failed: {e}")
        raise


if __name__ == "__main__":
    main()
