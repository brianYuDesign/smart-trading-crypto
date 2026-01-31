"""
Server 效能優化配置
加入 Flask-Caching 和 Flask-Limiter

使用方式：
在 server.py 開頭加入:
    from .optimized_server_config import init_cache, init_limiter, cache
    
在 app 初始化後:
    cache = init_cache(app)
    limiter = init_limiter(app)
    
在需要快取的函數上加裝飾器:
    @cache.cached(timeout=300, key_prefix='market_data')
    def get_market_data():
        ...
"""

from flask import Flask
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

# 快取配置
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',  # 使用記憶體快取
    'CACHE_DEFAULT_TIMEOUT': 300,  # 預設 5 分鐘
}

# 限流配置
RATELIMIT_CONFIG = {
    'default': '100 per hour',  # 每小時 100 次
    'storage_uri': 'memory://',  # 使用記憶體存儲
}

# 不同端點的快取時間
CACHE_TIMEOUTS = {
    'price': 60,           # 價格 1 分鐘
    'market_overview': 300,  # 市場總覽 5 分鐘
    'top_coins': 600,      # 排行榜 10 分鐘
    'news': 1800,          # 新聞 30 分鐘
}

# 不同端點的限流規則
RATE_LIMITS = {
    'price': '30 per minute',      # 價格查詢每分鐘 30 次
    'market': '20 per minute',     # 市場數據每分鐘 20 次
    'news': '10 per minute',       # 新聞查詢每分鐘 10 次
}


def init_cache(app: Flask) -> Cache:
    """
    初始化 Flask-Caching
    
    Args:
        app: Flask 應用實例
    
    Returns:
        Cache 實例
    """
    app.config.update(CACHE_CONFIG)
    cache = Cache(app)
    logger.info("✅ Flask-Caching 已初始化")
    return cache


def init_limiter(app: Flask) -> Limiter:
    """
    初始化 Flask-Limiter
    
    Args:
        app: Flask 應用實例
    
    Returns:
        Limiter 實例
    """
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[RATELIMIT_CONFIG['default']],
        storage_uri=RATELIMIT_CONFIG['storage_uri'],
        strategy='fixed-window',
    )
    logger.info("✅ Flask-Limiter 已初始化")
    return limiter


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成快取 key
    
    Args:
        prefix: 快取前綴
        *args, **kwargs: 參數
    
    Returns:
        快取 key 字符串
    """
    parts = [prefix]
    if args:
        parts.extend(str(arg) for arg in args)
    if kwargs:
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ':'.join(parts)


# 快取裝飾器範例
"""
使用範例：

from .optimized_server_config import init_cache, init_limiter, CACHE_TIMEOUTS, RATE_LIMITS

# 初始化
cache = init_cache(app)
limiter = init_limiter(app)

# 方式 1: 使用固定快取時間
@app.route('/api/market/<symbol>')
@cache.cached(timeout=CACHE_TIMEOUTS['price'], query_string=True)
@limiter.limit(RATE_LIMITS['price'])
def get_price(symbol):
    # ... 查詢邏輯
    return jsonify(data)

# 方式 2: 自訂快取 key
@app.route('/api/market/overview')
@cache.cached(
    timeout=CACHE_TIMEOUTS['market_overview'],
    key_prefix='market_overview',
)
@limiter.limit(RATE_LIMITS['market'])
def get_market_overview():
    # ... 查詢邏輯
    return jsonify(data)

# 方式 3: 手動快取控制
@app.route('/api/news')
@limiter.limit(RATE_LIMITS['news'])
def get_news():
    cache_key = 'news:latest'
    
    # 嘗試從快取獲取
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    # 查詢數據
    data = fetch_news()
    
    # 存入快取
    cache.set(cache_key, data, timeout=CACHE_TIMEOUTS['news'])
    
    return jsonify(data)

# 清除特定快取
def clear_price_cache(symbol):
    cache_key = f'price:{symbol}'
    cache.delete(cache_key)

# 清除所有快取
def clear_all_cache():
    cache.clear()
"""


# 效能監控輔助函數
class PerformanceMonitor:
    """效能監控工具"""
    
    def __init__(self, cache: Cache):
        self.cache = cache
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    def record_request(self):
        """記錄請求"""
        self._request_count += 1
    
    def record_cache_hit(self):
        """記錄快取命中"""
        self._cache_hits += 1
    
    def record_cache_miss(self):
        """記錄快取未命中"""
        self._cache_misses += 1
    
    def get_stats(self) -> dict:
        """獲取統計數據"""
        total_cache_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        return {
            'total_requests': self._request_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': f"{hit_rate:.1f}%",
        }
    
    def reset_stats(self):
        """重置統計"""
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0


# Webhook 快取策略
def cache_webhook_response(func):
    """
    Webhook 響應快取裝飾器
    
    注意: Telegram webhook 不適合快取完整響應
    但可以快取中間數據（如 API 查詢結果）
    """
    def wrapper(*args, **kwargs):
        # Webhook 本身不快取，但內部調用的函數可以使用快取
        return func(*args, **kwargs)
    return wrapper


if __name__ == "__main__":
    print("=" * 60)
    print("📋 效能優化配置說明")
    print("=" * 60)
    print("\n✅ 已配置的優化項目:")
    print("  1. Flask-Caching (記憶體快取)")
    print("  2. Flask-Limiter (請求限流)")
    print("  3. 自訂快取時間策略")
    print("  4. 效能監控工具")
    print("\n📊 快取時間設定:")
    for key, timeout in CACHE_TIMEOUTS.items():
        print(f"  - {key}: {timeout}秒 ({timeout//60}分鐘)")
    print("\n🚦 限流規則:")
    for key, limit in RATE_LIMITS.items():
        print(f"  - {key}: {limit}")
    print("\n" + "=" * 60)
