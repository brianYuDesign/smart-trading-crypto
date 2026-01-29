# 智慧新聞源管理系統使用指南

## 📋 目錄
- [概述](#概述)
- [核心特性](#核心特性)
- [快速開始](#快速開始)
- [詳細配置](#詳細配置)
- [使用範例](#使用範例)
- [監控與調試](#監控與調試)
- [最佳實踐](#最佳實踐)
- [故障排除](#故障排除)

---

## 概述

智慧新聞源管理系統是一個強大的 **Round-Robin 容錯機制**，專為加密貨幣新聞數據獲取設計。當某個新聞源失敗時，系統會自動切換到備用源，並對失敗的源實施冷卻機制，避免浪費資源在不穩定的服務上。

### 為什麼需要它？

在實際應用中，新聞 API 經常會遇到以下問題：
- **Rate Limit**: API 配額用完
- **網路超時**: 服務暫時無法連接
- **服務中斷**: API 維護或故障
- **數據質量**: 返回空結果或無效數據

智慧新聞源管理系統能夠：
✅ 自動檢測失敗並切換到備用源  
✅ 對失敗的源實施冷卻時間  
✅ 追蹤健康狀態和成功率  
✅ 提供完整的監控報告  

---

## 核心特性

### 1. **Round-Robin 輪詢**
按照優先級順序輪流嘗試各個新聞源，確保負載均衡。

### 2. **智慧冷卻機制**
當某個源連續失敗達到閾值時，自動進入冷卻期：
```
連續失敗 3 次 → 冷卻 300 秒 → 自動恢復
```

### 3. **自動容錯切換**
主要源失敗時，立即切換到備用源，無需人工干預。

### 4. **健康狀態追蹤**
每個新聞源的狀態實時更新：
- `HEALTHY`: 正常運作
- `DEGRADED`: 部分失敗
- `COOLING`: 冷卻中
- `FAILED`: 完全失敗

### 5. **成功率統計**
追蹤每個源的歷史表現，便於優化配置。

---

## 快速開始

### 安裝依賴

```bash
pip install requests
```

### 基本使用

```python
from src.data_sources.crypto_apis_v2 import CryptoDataAggregator
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)

# 配置 API Keys
config = {
    'cryptopanic_api_key': 'your_api_key_here',  # 從 https://cryptopanic.com/developers/api/ 獲取
    'coingecko_api_key': None  # 免費版不需要
}

# 創建聚合器
aggregator = CryptoDataAggregator(config)

# 獲取新聞（自動容錯）
news = aggregator.get_news(currencies=['BTC', 'ETH'])

if news:
    print(f"成功獲取 {len(news['data'])} 條新聞")
    print(f"來源: {news['source']}")
    print(f"時間: {news['timestamp']}")
else:
    print("所有新聞源都不可用")
```

### 輸出範例

```
INFO - 嘗試從 [CryptoPanic] 獲取新聞...
INFO - ✓ 從 [CryptoPanic] 成功獲取新聞
成功獲取 20 條新聞
來源: CryptoPanic
時間: 2024-01-29T14:30:00
```

---

## 詳細配置

### 新聞源配置

每個新聞源可以獨立配置以下參數：

```python
from src.data_sources.crypto_apis_v2 import NewsSource, CryptoPanicAPI

# 創建自定義新聞源
cryptopanic = CryptoPanicAPI('your_api_key')

source = NewsSource(
    name="CryptoPanic",              # 新聞源名稱
    fetch_function=cryptopanic.get_news,  # 獲取函數
    priority=1,                      # 優先級（數字越小越優先）
    max_failures=3,                  # 觸發冷卻的連續失敗次數
    cooldown_seconds=300,            # 冷卻時間（秒）
    timeout=10.0                     # 請求超時時間（秒）
)
```

### 多源配置範例

```python
from src.data_sources.crypto_apis_v2 import SmartNewsManager, NewsSource
from src.data_sources.crypto_apis_v2 import CryptoPanicAPI, CoinDeskAPI

# 創建多個新聞源
sources = [
    NewsSource(
        name="CryptoPanic",
        fetch_function=CryptoPanicAPI('key1').get_news,
        priority=1,           # 優先級最高
        max_failures=3,
        cooldown_seconds=300
    ),
    NewsSource(
        name="CoinDesk",
        fetch_function=CoinDeskAPI().get_news,
        priority=2,           # 備用源
        max_failures=2,       # 更嚴格的失敗閾值
        cooldown_seconds=180  # 較短的冷卻時間
    ),
    NewsSource(
        name="CoinTelegraph",
        fetch_function=custom_fetch_function,
        priority=3,           # 最後備用
        max_failures=5,
        cooldown_seconds=600
    )
]

# 創建管理器
manager = SmartNewsManager(sources, enable_fallback=True)
```

### 配置說明

| 參數 | 說明 | 建議值 |
|------|------|--------|
| `priority` | 優先級，數字越小越優先 | 1-10 |
| `max_failures` | 進入冷卻前的失敗次數 | 2-5 |
| `cooldown_seconds` | 冷卻時間（秒） | 180-600 |
| `timeout` | 請求超時時間（秒） | 5-15 |

---

## 使用範例

### 範例 1: 基本新聞獲取

```python
# 獲取熱門新聞
news = aggregator.get_news(filter_type='hot')

if news:
    for article in news['data'][:5]:  # 前 5 條
        print(f"標題: {article['title']}")
        print(f"來源: {article['source']}")
        print(f"情緒: {article['sentiment']}")
        print(f"相關幣種: {', '.join(article['currencies'])}")
        print("---")
```

### 範例 2: 特定幣種新聞

```python
# 只獲取 Bitcoin 和 Ethereum 相關新聞
btc_eth_news = aggregator.get_news(
    currencies=['BTC', 'ETH'],
    filter_type='important'
)

if btc_eth_news:
    print(f"獲取到 {len(btc_eth_news['data'])} 條 BTC/ETH 新聞")
```

### 範例 3: 市場情緒分析

```python
# 獲取整體市場情緒
sentiment = aggregator.analyze_market_sentiment()

print(f"恐懼貪婪指數: {sentiment['fear_greed_index']['value']}")
print(f"指數分類: {sentiment['fear_greed_index']['classification']}")
print(f"新聞情緒: {sentiment['news_sentiment']['overall']}")
print(f"綜合判斷: {sentiment['overall_sentiment']}")
```

輸出範例：
```
恐懼貪婪指數: 65
指數分類: Greed
新聞情緒: positive
綜合判斷: bullish
```

### 範例 4: 持續監控

```python
import time

# 每 5 分鐘獲取一次新聞
for i in range(12):  # 運行 1 小時
    print(f"\n=== 第 {i+1} 次檢查 ===")
    
    news = aggregator.get_news()
    
    if news:
        print(f"✓ 成功: {news['source']}")
        print(f"  成功率: {news['success_rate']}")
    else:
        print("✗ 所有源都不可用")
    
    # 查看健康狀態
    health = aggregator.get_news_health_status()
    print(f"可用源: {health['available_sources']}/{health['total_sources']}")
    
    time.sleep(300)  # 5 分鐘
```

---

## 監控與調試

### 查看健康狀態

```python
# 獲取詳細健康報告
health = aggregator.get_news_health_status()

print(f"總共 {health['total_sources']} 個新聞源")
print(f"可用 {health['available_sources']} 個")
print(f"\n各源狀態:")

for source in health['sources']:
    print(f"\n{source['name']}:")
    print(f"  狀態: {source['status']}")
    print(f"  成功率: {source['success_rate']}")
    print(f"  連續失敗: {source['consecutive_failures']}")
    
    if source['cooldown_remaining']:
        print(f"  冷卻剩餘: {source['cooldown_remaining']} 秒")
```

輸出範例：
```
總共 3 個新聞源
可用 2 個

各源狀態:

CryptoPanic:
  狀態: cooling
  成功率: 60.0%
  連續失敗: 3
  冷卻剩餘: 245 秒

CoinDesk:
  狀態: healthy
  成功率: 95.0%
  連續失敗: 0

CoinTelegraph:
  狀態: degraded
  成功率: 75.0%
  連續失敗: 1
```

### 日誌級別

```python
import logging

# 詳細調試
logging.basicConfig(level=logging.DEBUG)

# 只顯示錯誤
logging.basicConfig(level=logging.ERROR)

# 推薦：顯示資訊和錯誤
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 手動重置源

```python
# 重置單個源的健康狀態
aggregator.news_manager.reset_source('CryptoPanic')

# 重置所有源
aggregator.news_manager.reset_all()
```

---

## 最佳實踐

### 1. **合理設置優先級**

將最穩定、配額最高的源設為最高優先級：

```python
# 推薦配置
sources = [
    NewsSource(name="Premium API", priority=1),    # 付費穩定
    NewsSource(name="Free API 1", priority=2),     # 免費備用
    NewsSource(name="Free API 2", priority=3),     # 第二備用
]
```

### 2. **調整冷卻時間**

根據 API 的 rate limit 特性調整：

```python
# API 每小時限制 100 次請求
NewsSource(
    name="Limited API",
    max_failures=2,        # 更早觸發冷卻
    cooldown_seconds=3600  # 冷卻 1 小時
)

# API 很穩定但偶爾超時
NewsSource(
    name="Stable API",
    max_failures=5,        # 允許更多失敗
    cooldown_seconds=60    # 短暫冷卻
)
```

### 3. **實施重試策略**

```python
def fetch_with_retry(max_retries=3):
    for attempt in range(max_retries):
        news = aggregator.get_news()
        if news:
            return news
        
        if attempt < max_retries - 1:
            print(f"重試 {attempt + 1}/{max_retries}")
            time.sleep(5)
    
    return None
```

### 4. **定期檢查健康狀態**

```python
# 每小時記錄健康報告
import json
from datetime import datetime

def log_health_status():
    health = aggregator.get_news_health_status()
    
    with open(f'health_{datetime.now().strftime("%Y%m%d_%H")}.json', 'w') as f:
        json.dump(health, f, indent=2)
```

### 5. **錯誤通知**

```python
def fetch_with_alert():
    news = aggregator.get_news()
    
    if not news:
        health = aggregator.get_news_health_status()
        
        if health['available_sources'] == 0:
            # 發送警報（Email、Telegram 等）
            send_alert("所有新聞源都不可用！")
    
    return news
```

---

## 故障排除

### 問題 1: 所有源都進入冷卻

**症狀**: 所有新聞源都顯示 "cooling" 狀態

**原因**:
- API keys 無效或過期
- 網路連接問題
- API 服務全面中斷

**解決方案**:
```python
# 1. 檢查 API keys
print(config['cryptopanic_api_key'])

# 2. 手動測試 API
import requests
response = requests.get('https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_KEY')
print(response.status_code, response.text)

# 3. 重置所有源
aggregator.news_manager.reset_all()

# 4. 降低失敗閾值（臨時）
for source in aggregator.news_manager.sources:
    source.max_failures = 10
```

### 問題 2: 返回無效結果

**症狀**: 函數返回空列表或 None

**解決方案**:
```python
# 檢查參數
news = aggregator.get_news(
    currencies=['BTC'],  # 確保幣種代碼正確
    filter_type='hot',   # 確保 filter 有效
    kind='news'          # 確保類型正確
)

# 查看原始響應
import logging
logging.getLogger('requests').setLevel(logging.DEBUG)
```

### 問題 3: 冷卻時間過長

**症狀**: 源失敗後長時間無法恢復

**解決方案**:
```python
# 動態調整冷卻時間
for source in aggregator.news_manager.sources:
    source.cooldown_seconds = 60  # 改為 1 分鐘

# 或手動提前恢復
aggregator.news_manager.reset_source('CryptoPanic')
```

### 問題 4: 性能問題

**症狀**: 請求響應很慢

**解決方案**:
```python
# 減少 timeout
for source in aggregator.news_manager.sources:
    source.timeout = 5.0  # 改為 5 秒

# 禁用備援（更快失敗）
manager = SmartNewsManager(sources, enable_fallback=False)
```

---

## 進階配置

### 自定義新聞源

```python
def my_custom_news_source(**kwargs):
    """自定義新聞獲取函數"""
    # 實作你的邏輯
    response = requests.get('https://my-api.com/news')
    return response.json()

# 添加到管理器
custom_source = NewsSource(
    name="MyCustomAPI",
    fetch_function=my_custom_news_source,
    priority=1
)

sources.append(custom_source)
```

### 條件式容錯

```python
class ConditionalNewsManager(SmartNewsManager):
    def fetch_news(self, **kwargs):
        # 工作時間使用付費 API
        from datetime import datetime
        hour = datetime.now().hour
        
        if 9 <= hour <= 17:  # 工作時間
            # 強制使用高優先級源
            self.current_index = 0
        
        return super().fetch_news(**kwargs)
```

---

## 總結

智慧新聞源管理系統提供了企業級的容錯能力，讓你的加密貨幣交易系統更加穩定可靠。通過合理配置和監控，可以達到：

✅ **99%+ 可用率**: 多重備援確保服務持續  
✅ **自動恢復**: 無需人工干預  
✅ **成本優化**: 優先使用免費 API  
✅ **完整監控**: 隨時掌握系統健康  

開始使用吧！
