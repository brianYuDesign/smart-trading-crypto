"""
新聞監控系統
監控加密貨幣相關新聞，過濾高風險事件
"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsMonitor:
    """新聞監控器"""
    
    def __init__(self, config: Dict):
        """
        初始化新聞監控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.news_config = config['news_monitoring']
        self.risk_config = config['risk_management']
        self.keywords = self.news_config['keywords']
        self.sources = self.news_config['sources']
        self.cooldown_hours = self.risk_config['news_cooldown_hours']
        
        # 記錄最近的警報時間
        self.last_alert_time = None
        self.high_risk_detected = False
        
    def fetch_crypto_news(self) -> List[Dict]:
        """
        獲取加密貨幣新聞
        
        Returns:
            新聞列表
        """
        all_news = []
        
        # CryptoPanic API (免費版)
        try:
            # 使用公開的 RSS feed
            cryptopanic_url = "https://cryptopanic.com/api/free/v1/posts/"
            response = requests.get(
                cryptopanic_url,
                params={'currencies': 'BTC', 'kind': 'news'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for post in data.get('results', []):
                    all_news.append({
                        'title': post.get('title', ''),
                        'url': post.get('url', ''),
                        'published': post.get('published_at', ''),
                        'source': 'CryptoPanic'
                    })
        except Exception as e:
            logger.warning(f"無法獲取 CryptoPanic 新聞: {e}")
        
        # CoinDesk RSS
        try:
            feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
            for entry in feed.entries[:20]:  # 只取最近 20 條
                all_news.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': 'CoinDesk'
                })
        except Exception as e:
            logger.warning(f"無法獲取 CoinDesk 新聞: {e}")
        
        # Cointelegraph RSS
        try:
            feed = feedparser.parse('https://cointelegraph.com/rss')
            for entry in feed.entries[:20]:
                all_news.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': 'Cointelegraph'
                })
        except Exception as e:
            logger.warning(f"無法獲取 Cointelegraph 新聞: {e}")
        
        logger.info(f"獲取了 {len(all_news)} 條新聞")
        return all_news
    
    def check_keywords(self, text: str) -> List[str]:
        """
        檢查文本中是否包含關鍵字
        
        Args:
            text: 要檢查的文本
            
        Returns:
            匹配的關鍵字列表
        """
        matched_keywords = []
        text_lower = text.lower()
        
        for keyword in self.keywords:
            # 使用正則表達式進行單詞邊界匹配，避免誤報
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched_keywords.append(keyword)
        
        return matched_keywords
    
    def analyze_news_sentiment(self, news_item: Dict) -> Dict:
        """
        分析單條新聞的風險等級
        
        Args:
            news_item: 新聞項目
            
        Returns:
            包含風險評估的字典
        """
        title = news_item['title']
        matched_keywords = self.check_keywords(title)
        
        if not matched_keywords:
            return None
        
        # 風險等級評估
        risk_level = 'LOW'
        
        # 高風險關鍵字
        high_risk_keywords = ['Trump', '川普', 'war', '戰爭', 'ban', '禁令', 'crash', '崩盤']
        medium_risk_keywords = ['Federal Reserve', '聯準會', 'regulation', '監管', 'inflation', '通膨']
        
        high_risk_matches = [k for k in matched_keywords if k in high_risk_keywords]
        medium_risk_matches = [k for k in matched_keywords if k in medium_risk_keywords]
        
        if high_risk_matches:
            risk_level = 'HIGH'
        elif medium_risk_matches:
            risk_level = 'MEDIUM'
        
        return {
            'title': title,
            'url': news_item['url'],
            'published': news_item['published'],
            'source': news_item['source'],
            'risk_level': risk_level,
            'matched_keywords': matched_keywords,
            'high_risk_matches': high_risk_matches,
            'medium_risk_matches': medium_risk_matches
        }
    
    def scan_news(self) -> Dict:
        """
        掃描新聞並評估整體風險
        
        Returns:
            包含風險評估結果的字典
        """
        news_list = self.fetch_crypto_news()
        
        high_risk_news = []
        medium_risk_news = []
        all_alerts = []
        
        for news_item in news_list:
            analysis = self.analyze_news_sentiment(news_item)
            if analysis:
                all_alerts.append(analysis)
                
                if analysis['risk_level'] == 'HIGH':
                    high_risk_news.append(analysis)
                elif analysis['risk_level'] == 'MEDIUM':
                    medium_risk_news.append(analysis)
        
        # 判斷是否應該暫停交易
        should_pause_trading = len(high_risk_news) > 0
        
        if should_pause_trading:
            self.high_risk_detected = True
            self.last_alert_time = datetime.now()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_news_checked': len(news_list),
            'alerts_count': len(all_alerts),
            'high_risk_count': len(high_risk_news),
            'medium_risk_count': len(medium_risk_news),
            'should_pause_trading': should_pause_trading,
            'high_risk_news': high_risk_news[:5],  # 只返回前 5 條
            'medium_risk_news': medium_risk_news[:5],
            'cooldown_until': None
        }
        
        if should_pause_trading and self.last_alert_time:
            cooldown_until = self.last_alert_time + timedelta(hours=self.cooldown_hours)
            result['cooldown_until'] = cooldown_until.isoformat()
        
        logger.info(f"新聞掃描完成: {len(all_alerts)} 個警報, {len(high_risk_news)} 個高風險")
        
        return result
    
    def is_safe_to_trade(self) -> Dict:
        """
        檢查當前是否適合交易
        
        Returns:
            包含交易安全性評估的字典
        """
        now = datetime.now()
        
        # 如果最近檢測到高風險，檢查冷卻期是否結束
        if self.last_alert_time:
            cooldown_until = self.last_alert_time + timedelta(hours=self.cooldown_hours)
            if now < cooldown_until:
                remaining_hours = (cooldown_until - now).total_seconds() / 3600
                return {
                    'safe_to_trade': False,
                    'reason': f'新聞事件冷卻期，剩餘 {remaining_hours:.1f} 小時',
                    'cooldown_until': cooldown_until.isoformat()
                }
            else:
                # 冷卻期已過，重置狀態
                self.high_risk_detected = False
                self.last_alert_time = None
        
        # 掃描最新新聞
        scan_result = self.scan_news()
        
        if scan_result['should_pause_trading']:
            return {
                'safe_to_trade': False,
                'reason': f'檢測到 {scan_result["high_risk_count"]} 個高風險新聞事件',
                'high_risk_news': scan_result['high_risk_news'],
                'cooldown_until': scan_result['cooldown_until']
            }
        
        return {
            'safe_to_trade': True,
            'reason': '無重大風險事件',
            'scan_result': scan_result
        }
