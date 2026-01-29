# Smart Trading Crypto - 知識整合使用指南

## 目錄

1. [簡介](#簡介)
2. [快速開始](#快速開始)
3. [數據源配置](#數據源配置)
4. [核心模組使用](#核心模組使用)
5. [知識庫管理](#知識庫管理)
6. [自動化更新](#自動化更新)
7. [整合到現有系統](#整合到現有系統)
8. [API 參考](#api-參考)
9. [故障排除](#故障排除)
10. [最佳實踐](#最佳實踐)

---

## 簡介

本指南說明如何使用新整合的加密貨幣知識系統，包括：

- **多源數據聚合**：整合 CoinGecko、CryptoPanic、Fear & Greed Index
- **智能知識庫**：存儲歷史事件、交易模式、幣種知識
- **自動化更新**：定期更新市場數據和新聞
- **情緒分析**：綜合多維度數據分析市場情緒

---

## 快速開始

### 1. 安裝依賴

```bash
cd smart-trading-crypto
pip install -r requirements.txt
```

更新 `requirements.txt` 添加新依賴：

```txt
# 現有依賴
ccxt>=4.0.0
python-telegram-bot>=20.0
pyyaml>=6.0

# 新增依賴
requests>=2.31.0
aiohttp>=3.9.0
```

### 2. 配置 API 密鑰

創建 `config/data_sources.yaml`：

```yaml
# 加密貨幣數據源
crypto_apis:
  coingecko:
    enabled: true
    api_key: null  # 免費版不需要，Pro 版填入密鑰
    rate_limit: 50
    pro: false

# 新聞數據源
news_apis:
  cryptopanic:
    enabled: true
    api_key: YOUR_CRYPTOPANIC_KEY  # 註冊獲取: https://cryptopanic.com/developers/api/
    filter:
      currencies: [BTC, ETH, BNB, SOL, XRP]
      regions: [en]
      kind: news

# 更新間隔（秒）
update_intervals:
  market_data: 300    # 5分鐘
  news: 600           # 10分鐘
  knowledge: 3600     # 1小時
  snapshots: 86400    # 24小時
```

### 3. 初始化知識庫

```bash
# 創建數據目錄
mkdir -p data/knowledge_base

# 運行初始化（自動創建數據庫）
python scripts/knowledge_updater.py
```

### 4. 測試數據獲取

```python
from src.data_sources.crypto_apis import CryptoDataAggregator
import yaml

# 載入配置
with open('config/data_sources.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 創建聚合器
aggregator = CryptoDataAggregator(config)

# 獲取市場概覽
overview = aggregator.get_market_overview(['bitcoin', 'ethereum'])
print(f"BTC 價格: ${overview['coins']['bitcoin']['current_price']:,.2f}")

# 獲取市場情緒
sentiment = aggregator.analyze_market_sentiment()
print(f"市場情緒: {sentiment['overall_sentiment']}")

# 獲取新聞
news = aggregator.get_crypto_news(filter_type='important', limit=5)
for item in news:
    print(f"- [{item['sentiment']}] {item['title']}")
```

---

## 數據源配置

### CoinGecko API

**免費版限制**：
- 50 calls/minute
- 無需 API 密鑰
- 完整功能

**Pro 版升級**：
```yaml
crypto_apis:
  coingecko:
    enabled: true
    api_key: YOUR_PRO_KEY
    rate_limit: 500
    pro: true
```

**獲取數據**：
```python
from src.data_sources.crypto_apis import CoinGeckoAPI

cg = CoinGeckoAPI()

# 獲取價格
prices = cg.get_coin_price(['bitcoin', 'ethereum'])

# 獲取詳細數據
btc_data = cg.get_coin_market_data('bitcoin')

# 獲取熱門幣種
trending = cg.get_trending_coins()

# 獲取全球數據
global_data = cg.get_global_market_data()
```

### CryptoPanic API

**註冊**：https://cryptopanic.com/developers/api/

**免費版限制**：
- 100 calls/day
- 基礎過濾功能

**使用示例**：
```python
from src.data_sources.crypto_apis import CryptoPanicAPI

cp = CryptoPanicAPI('YOUR_API_KEY')

# 獲取熱門新聞
hot_news = cp.get_news(filter_type='hot')

# 獲取特定幣種新聞
btc_news = cp.get_news(currencies=['BTC'], filter_type='important')

# 獲取看漲新聞
bullish_news = cp.get_news(filter_type='bullish')
```

### Fear & Greed Index

**無需密鑰**，完全免費：

```python
from src.data_sources.crypto_apis import AlternativeMeAPI

fg = AlternativeMeAPI()

# 獲取當前指數
current = fg.get_fear_greed_index(limit=1)
print(f"Fear & Greed: {current[0]['value']} ({current[0]['value_classification']})")

# 獲取歷史數據
history = fg.get_fear_greed_index(limit=30)  # 30天歷史
```

---

## 核心模組使用

### 1. 數據聚合器 (CryptoDataAggregator)

統一接口，整合所有數據源：

```python
from src.data_sources.crypto_apis import CryptoDataAggregator
import yaml

# 初始化
with open('config/data_sources.yaml', 'r') as f:
    config = yaml.safe_load(f)
aggregator = CryptoDataAggregator(config)

# 市場概覽
overview = aggregator.get_market_overview(['bitcoin', 'ethereum', 'binancecoin'])
print(f"全球市值: ${overview['global_data']['total_market_cap_usd']:,.0f}")
print(f"BTC 主導: {overview['global_data']['bitcoin_dominance']:.2f}%")

# 加密新聞
news = aggregator.get_crypto_news(
    currencies=['BTC', 'ETH'],
    filter_type='important',
    limit=20
)

# 市場情緒分析
sentiment = aggregator.analyze_market_sentiment()
print(f"整體情緒: {sentiment['overall_sentiment']}")
print(f"信心度: {sentiment['confidence']:.0%}")
print(f"Fear & Greed: {sentiment['fear_greed']['value']}")
print(f"新聞正面率: {sentiment['news_sentiment']['positive_ratio']:.0%}")
```

### 2. 知識庫管理 (MarketKnowledgeBase)

存儲和查詢市場知識：

```python
from src.knowledge_base.knowledge_base import MarketKnowledgeBase

kb = MarketKnowledgeBase()

# 添加歷史事件
event = {
    'event_date': '2026-01-15',
    'event_type': 'regulation',
    'title': 'SEC approves Bitcoin ETF',
    'description': 'Major regulatory milestone',
    'impact_level': 'critical',
    'affected_coins': ['BTC', 'ETH'],
    'market_reaction': 'positive',
    'price_change_24h': 15.5,
    'sentiment': 'positive',
    'tags': ['ETF', 'regulation', 'bullish']
}
kb.add_historical_event(event)

# 查找相似事件
similar_events = kb.get_similar_historical_events('regulation', days_back=365)
for event in similar_events[:3]:
    print(f"- {event['title']}: {event['price_change_24h']:.1f}% price change")

# 添加交易模式
pattern = {
    'pattern_name': 'Bull Flag Breakout',
    'pattern_type': 'continuation',
    'description': '牛旗突破形態 - 上升趨勢中的整理形態',
    'success_rate': 0.72,
    'avg_return': 0.15,
    'timeframe': '4h',
    'conditions': {
        'rsi': {'min': 50, 'max': 70},
        'volume_ratio': {'min': 1.5},
        'trend': 'uptrend'
    },
    'entry_rules': ['突破旗型上沿', '成交量放大確認'],
    'exit_rules': ['達到目標位（旗桿高度）', 'RSI 超買 > 80'],
    'risk_level': 'medium'
}
kb.add_trading_pattern(pattern)

# 查找匹配模式
market_conditions = {
    'rsi': 60,
    'volume_ratio': 2.0,
    'trend': 'uptrend'
}
matching = kb.find_matching_patterns(market_conditions)
for pattern in matching:
    print(f"匹配模式: {pattern['pattern_name']} (成功率: {pattern['success_rate']:.0%})")

# 獲取幣種知識
btc_knowledge = kb.get_coin_knowledge('bitcoin')
if btc_knowledge:
    print(f"幣種: {btc_knowledge['name']}")
    print(f"分類: {btc_knowledge['category']}")
    print(f"使用場景: {', '.join(btc_knowledge['use_cases'])}")
    print(f"風險: {', '.join(btc_knowledge['risks'])}")

# 查詢相關性
correlations = kb.get_correlations('BTC', timeframe='30d')
for corr in correlations:
    other_asset = corr['asset2'] if corr['asset1'] == 'BTC' else corr['asset1']
    print(f"BTC vs {other_asset}: {corr['correlation_value']:.3f}")

# 搜索新聞
news_results = kb.search_news(
    keywords=['Bitcoin', 'ETF'],
    sentiment='positive',
    days_back=7
)
print(f"找到 {len(news_results)} 條相關新聞")
```

### 3. 知識庫更新器 (KnowledgeUpdater)

自動化知識庫維護：

```python
from scripts.knowledge_updater import KnowledgeUpdater

# 初始化更新器
updater = KnowledgeUpdater('config/data_sources.yaml')

# 執行完整更新
updater.update_all()

# 或分別更新
updater.update_market_overview()
updater.update_news_and_events()
updater.update_coin_knowledge()
updater.update_market_correlations()
updater.save_market_snapshot()

# 獲取更新摘要
summary = updater.get_update_summary()
print(f"更新狀態: {summary['status']}")
print(f"最後更新: {summary['last_update']}")
```

---

## 知識庫管理

### 數據庫結構

知識庫使用 SQLite，位於 `data/knowledge_base/market_knowledge.db`

**主要表格**：
- `historical_events`: 重大歷史事件
- `trading_patterns`: 交易模式庫
- `coin_knowledge`: 幣種詳細知識
- `market_correlations`: 資產相關性
- `market_snapshots`: 市場狀態快照
- `expert_rules`: 專家規則
- `news_archive`: 新聞歸檔

### 數據庫維護

```bash
# 備份數據庫
cp data/knowledge_base/market_knowledge.db data/knowledge_base/market_knowledge_backup_$(date +%Y%m%d).db

# 查看數據庫大小
du -h data/knowledge_base/market_knowledge.db

# 清理舊數據（超過90天的新聞）
sqlite3 data/knowledge_base/market_knowledge.db "DELETE FROM news_archive WHERE published_at < date('now', '-90 days');"

# 優化數據庫
sqlite3 data/knowledge_base/market_knowledge.db "VACUUM;"
```

### 知識填充示例

預填充 2026 年市場知識：

```python
from src.knowledge_base.knowledge_base import MarketKnowledgeBase

kb = MarketKnowledgeBase()

# 2026 市場趨勢知識
trends_2026 = [
    {
        'event_date': '2026-01-01',
        'event_type': 'market_analysis',
        'title': 'Bitcoin 2026 預測：機構採用加速',
        'description': 'BlackRock IBIT ETF 和 Strategy 公司大量買入，推動 BTC 價格',
        'impact_level': 'high',
        'affected_coins': ['BTC'],
        'sentiment': 'positive',
        'tags': ['institutional', 'ETF', 'prediction']
    },
    {
        'event_date': '2026-01-01',
        'event_type': 'regulatory',
        'title': 'CLARITY Act 立法進展',
        'description': 'Stablecoin 監管框架和代幣化指導方針',
        'impact_level': 'critical',
        'affected_coins': ['BTC', 'ETH', 'USDT', 'USDC'],
        'sentiment': 'positive',
        'tags': ['regulation', 'stablecoin', 'clarity_act']
    },
    {
        'event_date': '2026-01-01',
        'event_type': 'macro',
        'title': 'Fed 2026 降息預期',
        'description': 'Fed 預計降息 125-150 基點，利好加密貨幣',
        'impact_level': 'high',
        'affected_coins': ['BTC', 'ETH'],
        'sentiment': 'positive',
        'tags': ['fed', 'interest_rate', 'macro']
    }
]

for trend in trends_2026:
    kb.add_historical_event(trend)

print("2026 市場趨勢知識已填充")
```

---

## 自動化更新

### 使用 Cron 定期更新

編輯 crontab：

```bash
crontab -e
```

添加定時任務：

```cron
# 每5分鐘更新市場數據
*/5 * * * * cd /path/to/smart-trading-crypto && python scripts/knowledge_updater.py >> logs/knowledge_update.log 2>&1

# 每小時保存市場快照
0 * * * * cd /path/to/smart-trading-crypto && python -c "from scripts.knowledge_updater import KnowledgeUpdater; KnowledgeUpdater().save_market_snapshot()" >> logs/snapshot.log 2>&1

# 每天凌晨1點清理舊數據
0 1 * * * cd /path/to/smart-trading-crypto && sqlite3 data/knowledge_base/market_knowledge.db "DELETE FROM news_archive WHERE published_at < date('now', '-90 days'); VACUUM;" >> logs/cleanup.log 2>&1
```

### 使用 systemd 服務

創建 `/etc/systemd/system/smart-trading-updater.service`：

```ini
[Unit]
Description=Smart Trading Crypto Knowledge Updater
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/smart-trading-crypto
ExecStart=/usr/bin/python3 scripts/knowledge_updater.py
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
sudo systemctl daemon-reload
sudo systemctl enable smart-trading-updater
sudo systemctl start smart-trading-updater
sudo systemctl status smart-trading-updater
```

### 使用 GitHub Actions

創建 `.github/workflows/knowledge_update.yml`：

```yaml
name: Knowledge Base Update

on:
  schedule:
    - cron: '0 */6 * * *'  # 每6小時
  workflow_dispatch:  # 手動觸發

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Update knowledge base
        env:
          CRYPTOPANIC_API_KEY: ${{ secrets.CRYPTOPANIC_API_KEY }}
        run: |
          python scripts/knowledge_updater.py
      
      - name: Commit updated database
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/knowledge_base/
          git commit -m "Auto update knowledge base" || echo "No changes"
          git push
```

---

## 整合到現有系統

### 增強 news_monitor.py

```python
# src/news_monitor.py (增強版)

from data_sources.crypto_apis import CryptoDataAggregator
from knowledge_base.knowledge_base import MarketKnowledgeBase
import yaml

class EnhancedNewsMonitor:
    def __init__(self, config):
        self.config = config
        
        # 載入數據源配置
        with open('config/data_sources.yaml', 'r') as f:
            ds_config = yaml.safe_load(f)
        
        self.data_aggregator = CryptoDataAggregator(ds_config)
        self.knowledge_base = MarketKnowledgeBase()
    
    def is_safe_to_trade(self):
        """檢查是否適合交易（整合多維度數據）"""
        
        # 1. 獲取最新新聞和情緒
        sentiment = self.data_aggregator.analyze_market_sentiment()
        
        # 2. 查詢相似歷史事件
        recent_events = self.knowledge_base.get_similar_historical_events(
            'regulation', 
            days_back=30
        )
        
        # 3. 綜合判斷
        safe_to_trade = True
        reason = []
        
        # Fear & Greed 極端情況
        fg_value = sentiment.get('fear_greed', {}).get('value', 50)
        if fg_value < 20:
            safe_to_trade = False
            reason.append(f"極度恐慌 (Fear & Greed: {fg_value})")
        elif fg_value > 80:
            reason.append(f"極度貪婪警示 (Fear & Greed: {fg_value})")
        
        # 新聞情緒負面
        news_sent = sentiment.get('news_sentiment', {})
        if news_sent.get('negative_ratio', 0) > 0.6:
            safe_to_trade = False
            reason.append(f"負面新聞過多 ({news_sent['negative_ratio']:.0%})")
        
        # 近期重大負面事件
        negative_events = [e for e in recent_events if e['sentiment'] == 'negative']
        if len(negative_events) > 3:
            safe_to_trade = False
            reason.append(f"近期重大負面事件: {len(negative_events)}件")
        
        return {
            'safe_to_trade': safe_to_trade,
            'reason': '; '.join(reason) if reason else '市場狀況正常',
            'sentiment': sentiment['overall_sentiment'],
            'confidence': sentiment['confidence'],
            'fear_greed': fg_value
        }
```

### 增強 signal_generator.py

```python
# src/signal_generator.py (增強版)

from knowledge_base.knowledge_base import MarketKnowledgeBase

class EnhancedSignalGenerator:
    def __init__(self, config):
        self.config = config
        self.knowledge_base = MarketKnowledgeBase()
    
    def generate_signal(self, symbol, technical_data):
        """生成交易信號（整合知識庫）"""
        
        # 1. 技術分析分數
        technical_score = self._calculate_technical_score(technical_data)
        
        # 2. 查找匹配的交易模式
        market_conditions = {
            'rsi': technical_data.get('rsi'),
            'volume_ratio': technical_data.get('volume_ratio'),
            'trend': technical_data.get('trend')
        }
        matching_patterns = self.knowledge_base.find_matching_patterns(market_conditions)
        
        # 3. 檢查幣種相關性
        correlations = self.knowledge_base.get_correlations(symbol, '30d')
        
        # 4. 查詢歷史相似情況
        # ...（根據當前市場條件查詢）
        
        # 5. 綜合評分
        pattern_score = 0
        if matching_patterns:
            # 取成功率最高的模式
            best_pattern = max(matching_patterns, key=lambda p: p['success_rate'])
            pattern_score = best_pattern['success_rate'] * 100
        
        final_score = (technical_score * 0.6) + (pattern_score * 0.4)
        
        # 6. 生成信號
        if final_score > 70:
            signal = 'BUY'
            confidence = final_score / 100
        elif final_score < 30:
            signal = 'SELL'
            confidence = (100 - final_score) / 100
        else:
            signal = 'HOLD'
            confidence = 0.5
        
        return {
            'signal': signal,
            'confidence': confidence,
            'technical_score': technical_score,
            'pattern_score': pattern_score,
            'final_score': final_score,
            'matching_patterns': [p['pattern_name'] for p in matching_patterns],
            'timestamp': datetime.now().isoformat()
        }
```

---

## API 參考

### CryptoDataAggregator

```python
class CryptoDataAggregator:
    def __init__(self, config: Dict)
    
    def get_market_overview(self, symbols: List[str]) -> Dict
        """獲取市場概覽"""
    
    def get_crypto_news(self, currencies: List[str], filter_type: str, limit: int) -> List[Dict]
        """獲取加密貨幣新聞"""
    
    def analyze_market_sentiment(self) -> Dict
        """分析市場情緒"""
```

### MarketKnowledgeBase

```python
class MarketKnowledgeBase:
    def __init__(self, db_path: str)
    
    def add_historical_event(self, event: Dict) -> int
    def get_similar_historical_events(self, event_type: str, days_back: int) -> List[Dict]
    
    def add_trading_pattern(self, pattern: Dict) -> int
    def find_matching_patterns(self, market_conditions: Dict) -> List[Dict]
    
    def add_coin_knowledge(self, coin_data: Dict) -> int
    def get_coin_knowledge(self, coin_id: str) -> Optional[Dict]
    
    def save_correlation(self, asset1: str, asset2: str, correlation: float, timeframe: str, data_points: int)
    def get_correlations(self, asset: str, timeframe: str) -> List[Dict]
    
    def save_market_snapshot(self, snapshot: Dict)
    def get_historical_snapshots(self, days_back: int) -> List[Dict]
    
    def archive_news(self, news_item: Dict) -> int
    def search_news(self, keywords: List[str], sentiment: str, days_back: int) -> List[Dict]
```

---

## 故障排除

### 常見問題

**1. API 限流錯誤**

```
Error: Rate limit exceeded
```

**解決方案**：
- 降低更新頻率
- 使用付費 API 計劃
- 實施請求緩存

**2. 數據庫鎖定**

```
sqlite3.OperationalError: database is locked
```

**解決方案**：
```python
# 使用 timeout 參數
conn = sqlite3.connect('db.db', timeout=10.0)
```

**3. 新聞重複**

**解決方案**：
- 已內建去重機制（UNIQUE 約束）
- 定期清理舊數據

**4. 記憶體使用過高**

**解決方案**：
- 限制批量查詢數量
- 使用分頁查詢
- 定期重啟更新服務

### 日誌調試

啟用詳細日誌：

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

---

## 最佳實踐

### 1. API 使用

- ✅ 使用免費 API 時注意限流
- ✅ 緩存不經常變化的數據
- ✅ 錯誤處理和重試機制
- ✅ 監控 API 健康狀態

### 2. 數據管理

- ✅ 定期備份數據庫
- ✅ 清理超過90天的舊新聞
- ✅ 優化數據庫索引
- ✅ 監控數據庫大小

### 3. 性能優化

- ✅ 並行獲取多個數據源
- ✅ 使用連接池
- ✅ 實施智能緩存策略
- ✅ 分離讀寫操作

### 4. 安全性

- ✅ API 密鑰不要硬編碼
- ✅ 使用環境變數
- ✅ 限制數據庫訪問權限
- ✅ 定期更新依賴包

### 5. 監控告警

- ✅ 監控 API 調用成功率
- ✅ 設置數據更新告警
- ✅ 追蹤知識庫增長
- ✅ 記錄異常情況

---

## 下一步

1. **回測系統**：使用歷史數據回測交易策略
2. **機器學習**：訓練價格預測模型
3. **實時推送**：WebSocket 實時數據流
4. **Web 儀表板**：可視化知識庫和市場數據
5. **移動端支持**：開發移動 App

---

## 支持與貢獻

- **文檔**：查看完整文檔 [DEPLOYMENT.md](DEPLOYMENT.md)
- **問題反饋**：GitHub Issues
- **貢獻代碼**：Pull Requests 歡迎

---

**版本**: 1.0  
**最後更新**: 2026-01-29  
**作者**: Smart Trading Crypto Team
