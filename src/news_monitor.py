"""
新聞監控系統
監控加密貨幣新聞，過濾高風險事件
"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import re
import json
import hashlib
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsMonitor:
    """新聞監控器 - 多來源、容錯、去重、智能提醒"""

    def __init__(self):
        # 多個新聞來源
        self.news_sources = {
            'cryptopanic': {
                'url': 'https://cryptopanic.com/api/free/v1/posts/',
                'type': 'api',
                'enabled': True
            },
            'coindesk_rss': {
                'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'type': 'rss',
                'enabled': True
            },
            'cointelegraph_rss': {
                'url': 'https://cointelegraph.com/rss',
                'type': 'rss',
                'enabled': True
            },
            'decrypt_rss': {
                'url': 'https://decrypt.co/feed',
                'type': 'rss',
                'enabled': True
            },
            'bitcoinmagazine_rss': {
                'url': 'https://bitcoinmagazine.com/.rss/full/',
                'type': 'rss',
                'enabled': True
            }
        }

        # 高風險關鍵詞
        self.risk_keywords = {
            'critical': ['hack', 'exploit', 'vulnerability', 'breach', 'attack', '駭客', '漏洞', '攻擊'],
            'high': ['crash', 'dump', 'regulation', 'ban', 'lawsuit', '崩盤', '監管', '禁令', '訴訟'],
            'medium': ['warning', 'concern', 'risk', 'drop', 'fall', '警告', '風險', '下跌']
        }

        # 去重和提醒頻率控制
        self.seen_news_file = Path('data/seen_news.json')
        self.seen_news_file.parent.mkdir(parents=True, exist_ok=True)
        self.seen_news = self._load_seen_news()
        self.max_alert_count = 5  # 每則新聞最多提醒5次

    def _load_seen_news(self) -> Dict:
        """載入已見過的新聞記錄"""
        if self.seen_news_file.exists():
            try:
                with open(self.seen_news_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"載入歷史記錄失敗: {e}")
        return {}

    def _save_seen_news(self):
        """保存已見過的新聞記錄"""
        try:
            with open(self.seen_news_file, 'w', encoding='utf-8') as f:
                json.dump(self.seen_news, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存歷史記錄失敗: {e}")

    def _get_news_hash(self, title: str) -> str:
        """生成新聞的唯一標識（基於標題相似度）"""
        # 清理標題：移除特殊字符、轉小寫、移除多餘空格
        clean_title = re.sub(r'[^\\w\\s]', '', title.lower())
        clean_title = re.sub(r'\\s+', ' ', clean_title).strip()
        # 只取前100個字符來計算hash（避免過度精確）
        return hashlib.md5(clean_title[:100].encode()).hexdigest()

    def _should_alert(self, news_hash: str) -> bool:
        """判斷是否應該發送警報（基於提醒次數）"""
        if news_hash not in self.seen_news:
            self.seen_news[news_hash] = {'count': 0, 'first_seen': datetime.now().isoformat()}

        self.seen_news[news_hash]['count'] += 1
        self.seen_news[news_hash]['last_seen'] = datetime.now().isoformat()

        # 超過最大提醒次數則不再提醒
        if self.seen_news[news_hash]['count'] > self.max_alert_count:
            return False

        self._save_seen_news()
        return True

    def _fetch_cryptopanic(self) -> List[Dict]:
        """獲取 CryptoPanic 新聞"""
        try:
            response = requests.get(
                self.news_sources['cryptopanic']['url'],
                params={'currencies': 'BTC', 'kind': 'news'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                news_list = []
                for item in data.get('results', [])[:20]:
                    news_list.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'published': item.get('published_at', ''),
                        'source': 'CryptoPanic'
                    })
                logger.info(f"✅ CryptoPanic: 獲取了 {len(news_list)} 條新聞")
                return news_list
        except Exception as e:
            logger.warning(f"⚠️  CryptoPanic 獲取失敗: {e}")
        return []

    def _fetch_rss(self, source_name: str, url: str) -> List[Dict]:
        """獲取 RSS 新聞"""
        try:
            feed = feedparser.parse(url)
            news_list = []
            for entry in feed.entries[:20]:
                news_list.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': source_name
                })
            logger.info(f"✅ {source_name}: 獲取了 {len(news_list)} 條新聞")
            return news_list
        except Exception as e:
            logger.warning(f"⚠️  {source_name} 獲取失敗: {e}")
        return []

    def fetch_all_news(self) -> List[Dict]:
        """從所有來源獲取新聞（容錯機制）"""
        all_news = []

        for source_name, config in self.news_sources.items():
            if not config['enabled']:
                continue

            try:
                if config['type'] == 'api':
                    if source_name == 'cryptopanic':
                        news = self._fetch_cryptopanic()
                        all_news.extend(news)
                elif config['type'] == 'rss':
                    news = self._fetch_rss(source_name, config['url'])
                    all_news.extend(news)
            except Exception as e:
                logger.warning(f"⚠️  {source_name} 處理失敗: {e}")
                # 單一來源失敗不影響整體，繼續處理其他來源
                continue

        logger.info(f"📊 總共獲取了 {len(all_news)} 條新聞（來自 {len([s for s in self.news_sources.values() if s['enabled']])} 個來源）")
        return all_news

    def _calculate_risk_score(self, text: str) -> tuple:
        """計算風險分數"""
        text_lower = text.lower()
        score = 0
        matched_keywords = []

        for level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if level == 'critical':
                        score += 10
                    elif level == 'high':
                        score += 5
                    elif level == 'medium':
                        score += 2
                    matched_keywords.append(f"{keyword}({level})")

        return score, matched_keywords

    def check_news_safety(self) -> Dict:
        """檢查新聞安全性（去重 + 智能提醒）"""
        news_list = self.fetch_all_news()

        if not news_list:
            logger.warning("⚠️  所有新聞來源均失敗，但程式繼續運行")
            return {
                'is_safe': True,
                'high_risk_news': [],
                'total_alerts': 0,
                'alert_categories': {},
                'error': 'all_sources_failed'
            }

        high_risk_news = []
        alert_categories = {}
        unique_news = {}  # 用於去重

        for news in news_list:
            title = news.get('title', '')
            if not title:
                continue

            # 去重檢查
            news_hash = self._get_news_hash(title)

            # 計算風險分數
            score, keywords = self._calculate_risk_score(title)

            if score >= 5:  # 高風險閾值
                # 檢查是否應該發送警報（基於提醒次數）
                if self._should_alert(news_hash):
                    alert_count = self.seen_news[news_hash]['count']

                    # 只有在未重複或重複次數較少時才加入
                    if news_hash not in unique_news:
                        high_risk_news.append({
                            'title': title,
                            'url': news.get('url', ''),
                            'score': score,
                            'keywords': keywords,
                            'published': news.get('published', ''),
                            'source': news.get('source', ''),
                            'alert_count': alert_count  # 記錄已提醒次數
                        })
                        unique_news[news_hash] = True

                        # 分類統計
                        for kw in keywords:
                            category = kw.split('(')[1].rstrip(')')
                            alert_categories[category] = alert_categories.get(category, 0) + 1
                else:
                    logger.info(f"🔇 已忽略重複新聞（已提醒{self.seen_news[news_hash]['count']}次）: {title[:50]}...")

        # 按風險分數排序
        high_risk_news.sort(key=lambda x: x['score'], reverse=True)

        is_safe = len(high_risk_news) == 0

        logger.info(f"新聞掃描完成: {len(high_risk_news)} 個高風險（已去重和頻率控制）")

        return {
            'is_safe': is_safe,
            'high_risk_news': high_risk_news,
            'total_alerts': len(high_risk_news),
            'alert_categories': alert_categories
        }


def main():
    monitor = NewsMonitor()
    result = monitor.check_news_safety()

    print("\n" + "=" * 50)
    print("新聞監控結果")
    print("=" * 50)
    print(f"安全狀態: {'✅ 安全' if result['is_safe'] else '⚠️  警報'}")
    print(f"高風險新聞數: {len(result['high_risk_news'])}")

    if result['high_risk_news']:
        print("\n高風險新聞:")
        for news in result['high_risk_news'][:5]:
            print(f"\n  [{news['score']}分] {news['title']}")
            print(f"  來源: {news['source']} | 已提醒: {news['alert_count']}/{monitor.max_alert_count}次")
            print(f"  關鍵詞: {', '.join(news['keywords'])}")


if __name__ == "__main__":
    main()
