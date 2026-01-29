"""
新聞監控模組 - 多來源抓取、智能去重、頻率控制
"""
import os
import requests
import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path

class NewsMonitor:
    """加密貨幣新聞監控器"""

    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.seen_news_file = self.data_dir / 'seen_news.json'
        self.seen_news = self._load_seen_news()
        self.max_alert_count = 5  # 每則新聞最多提醒 5 次

        # CryptoPanic API (免費，無需註冊)
        self.cryptopanic_url = 'https://cryptopanic.com/api/v1/posts/'

        # RSS 新聞來源
        self.rss_sources = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'decrypt': 'https://decrypt.co/feed',
            'bitcoinmagazine': 'https://bitcoinmagazine.com/feed'
        }

    def _load_seen_news(self):
        """載入已看過的新聞記錄"""
        if self.seen_news_file.exists():
            try:
                with open(self.seen_news_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"載入新聞記錄失敗: {e}")
                return {}
        return {}

    def _save_seen_news(self):
        """保存已看過的新聞記錄"""
        try:
            with open(self.seen_news_file, 'w', encoding='utf-8') as f:
                json.dump(self.seen_news, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存新聞記錄失敗: {e}")

    def _generate_news_hash(self, title):
        """生成新聞的唯一識別碼 (基於標題)"""
        # 清理標題：移除特殊字符、轉小寫、標準化空白
        clean_title = re.sub(r'[^\w\s]', '', title.lower())
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()

        # 使用前 100 個字符生成 MD5 hash
        news_hash = hashlib.md5(clean_title[:100].encode()).hexdigest()[:12]
        return news_hash

    def _is_news_seen(self, news_hash, title):
        """檢查新聞是否已經看過，並更新計數"""
        if news_hash not in self.seen_news:
            # 新新聞
            self.seen_news[news_hash] = {
                'title': title,
                'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': 1
            }
            return False

        # 已看過的新聞
        news_info = self.seen_news[news_hash]

        # 檢查提醒次數
        if news_info['count'] >= self.max_alert_count:
            print(f"   ⚠️  新聞已提醒 {self.max_alert_count} 次，跳過: {title[:50]}...")
            return True  # 視為已看過，不再提醒

        # 更新計數和時間
        news_info['count'] += 1
        news_info['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"   📊 新聞重複出現 (第 {news_info['count']} 次): {title[:50]}...")
        return True

    def _fetch_cryptopanic(self):
        """從 CryptoPanic 抓取新聞"""
        news_list = []
        try:
            params = {
                'auth_token': 'free',  # 使用免費訪問
                'public': 'true',
                'kind': 'news',
                'filter': 'important'  # 只抓取重要新聞
            }

            response = requests.get(self.cryptopanic_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get('results', [])[:10]:  # 只取前 10 則
                news_list.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'published': item.get('created_at', ''),
                    'source': 'CryptoPanic',
                    'summary': ''
                })

            print(f"✅ CryptoPanic: 抓取 {len(news_list)} 則新聞")

        except Exception as e:
            print(f"❌ CryptoPanic 抓取失敗: {e}")

        return news_list

    def _fetch_rss(self, source_name, rss_url):
        """從 RSS 來源抓取新聞 (使用簡單的 XML 解析)"""
        news_list = []
        try:
            import feedparser

            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:10]:  # 只取前 10 則
                news_list.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': source_name,
                    'summary': entry.get('summary', '')[:200] if entry.get('summary') else ''
                })

            print(f"✅ {source_name}: 抓取 {len(news_list)} 則新聞")

        except Exception as e:
            print(f"❌ {source_name} 抓取失敗: {e}")

        return news_list

    def fetch_all_news(self):
        """從所有來源抓取新聞"""
        all_news = []

        print("\n📡 開始抓取新聞...")

        # 1. CryptoPanic
        all_news.extend(self._fetch_cryptopanic())

        # 2. RSS 來源
        for source_name, rss_url in self.rss_sources.items():
            all_news.extend(self._fetch_rss(source_name, rss_url))

        print(f"\n📊 總共抓取 {len(all_news)} 則新聞")

        return all_news

    def filter_new_news(self, news_list):
        """過濾出新新聞 (去重 + 頻率控制)"""
        new_news = []

        for news in news_list:
            title = news['title']
            if not title:
                continue

            news_hash = self._generate_news_hash(title)

            if not self._is_news_seen(news_hash, title):
                new_news.append(news)

        # 保存記錄
        self._save_seen_news()

        return new_news

    def monitor_news(self):
        """主要監控函數 - 返回新新聞列表"""
        print("\n" + "=" * 70)
        print("🔍 新聞監控啟動")
        print("=" * 70)

        # 抓取所有新聞
        all_news = self.fetch_all_news()

        if not all_news:
            print("\n⚠️  沒有抓取到任何新聞")
            return []

        # 過濾新新聞
        print("\n🔎 開始過濾新新聞...")
        new_news = self.filter_new_news(all_news)

        print("\n" + "=" * 70)
        if new_news:
            print(f"✅ 發現 {len(new_news)} 則新新聞")
        else:
            print("✅ 沒有新新聞")
        print("=" * 70)

        return new_news

    def format_news_message(self, news_list):
        """格式化新聞為 Telegram 訊息"""
        if not news_list:
            return None

        message = "🚨 加密貨幣新聞警報 🚨\n\n"
        message += f"檢測到 {len(news_list)} 則新新聞：\n"
        message += "─" * 40 + "\n\n"

        for i, news in enumerate(news_list[:5], 1):  # 最多顯示 5 則
            message += f"{i}. 📰 {news['title']}\n"
            message += f"   🏢 來源：{news['source']}\n"
            if news.get('published'):
                message += f"   📅 時間：{news['published']}\n"
            if news.get('summary'):
                message += f"   📝 {news['summary'][:150]}...\n"
            message += f"   🔗 {news['url']}\n\n"

        if len(news_list) > 5:
            message += f"\n... 還有 {len(news_list) - 5} 則新聞"

        return message


# 獨立執行測試
if __name__ == "__main__":
    monitor = NewsMonitor()
    new_news = monitor.monitor_news()

    if new_news:
        message = monitor.format_news_message(new_news)
        print("\n" + "=" * 70)
        print("Telegram 訊息預覽")
        print("=" * 70)
        print(message)

    def is_safe_to_trade(self):
        """
        檢查當前新聞環境是否適合交易

        Returns:
            dict: {
                'safe_to_trade': bool,
                'reason': str,
                'high_risk_news': list
            }
        """
        try:
            # 獲取最新新聞
            all_news = self.fetch_all_news()

            if not all_news:
                return {
                    'safe_to_trade': True,
                    'reason': '無新聞數據',
                    'high_risk_news': []
                }

            # 篩選高風險關鍵詞
            high_risk_keywords = [
                'hack', 'hacked', 'exploit', 'crash', 'ban', 'regulation',
                'sec', 'lawsuit', 'fraud', 'scam', 'collapse', 'bankrupt'
            ]

            high_risk_news = []
            for news in all_news[:20]:  # 只檢查最新20條
                title_lower = news.get('title', '').lower()
                if any(keyword in title_lower for keyword in high_risk_keywords):
                    high_risk_news.append(news)

            # 如果有3條以上高風險新聞，建議暫停交易
            if len(high_risk_news) >= 3:
                return {
                    'safe_to_trade': False,
                    'reason': f'檢測到 {len(high_risk_news)} 條高風險新聞',
                    'high_risk_news': high_risk_news
                }

            return {
                'safe_to_trade': True,
                'reason': '新聞環境正常',
                'high_risk_news': high_risk_news
            }

        except Exception as e:
            # 如果新聞檢查失敗，預設為安全（不阻止交易）
            print(f"⚠️ 新聞安全檢查失敗: {e}")
            return {
                'safe_to_trade': True,
                'reason': f'新聞檢查失敗: {str(e)}',
                'high_risk_news': []
            }
