"""
智慧新聞資料源管理器 - Round-Robin with Cooldown
支援多個新聞來源的輪詢、容錯切換和冷卻機制
"""
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SourceStatus(Enum):
    """資料源狀態"""
    HEALTHY = "healthy"          # 健康可用
    DEGRADED = "degraded"        # 降級（部分失敗）
    COOLING = "cooling"          # 冷卻中
    FAILED = "failed"            # 失敗


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
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.total_requests - self.total_failures) / self.total_requests
    
    @property
    def is_available(self) -> bool:
        """是否可用（不在冷卻期）"""
        if self.cooldown_until is None:
            return True
        return datetime.now() >= self.cooldown_until
    
    def __str__(self) -> str:
        cooldown = ""
        if self.cooldown_until:
            remaining = (self.cooldown_until - datetime.now()).total_seconds()
            if remaining > 0:
                cooldown = f" (冷卻中: {remaining:.0f}秒)"
        
        return (f"{self.name}: {self.status.value} | "
                f"成功率: {self.success_rate:.1%} | "
                f"連續失敗: {self.consecutive_failures}{cooldown}")


@dataclass
class NewsSource:
    """新聞資料源定義"""
    name: str
    fetch_function: Callable
    priority: int = 1  # 優先級（數字越小越優先）
    max_failures: int = 3  # 觸發冷卻的連續失敗次數
    cooldown_seconds: int = 300  # 冷卻時間（秒）
    timeout: float = 10.0  # 請求超時時間
    health: SourceHealth = field(init=False)
    
    def __post_init__(self):
        self.health = SourceHealth(name=self.name)


class NewsSourceManager:
    """
    智慧新聞資料源管理器
    
    功能特點：
    1. Round-Robin 輪詢多個資料源
    2. 自動容錯切換
    3. 失敗後冷卻機制
    4. 健康狀態監控
    5. 優先級管理
    """
    
    def __init__(self, sources: List[NewsSource], 
                 enable_fallback: bool = True,
                 min_sources: int = 1):
        """
        初始化管理器
        
        Args:
            sources: 新聞資料源列表
            enable_fallback: 是否啟用備援切換
            min_sources: 最少需要的可用資料源數量
        """
        self.sources = sorted(sources, key=lambda x: x.priority)
        self.enable_fallback = enable_fallback
        self.min_sources = min_sources
        self.current_index = 0
        
        logger.info(f"初始化 NewsSourceManager，共 {len(sources)} 個資料源")
    
    def get_available_sources(self) -> List[NewsSource]:
        """獲取當前可用的資料源"""
        return [s for s in self.sources if s.health.is_available]
    
    def get_next_source(self) -> Optional[NewsSource]:
        """
        Round-Robin 獲取下一個可用資料源
        
        Returns:
            NewsSource 或 None（如果沒有可用資料源）
        """
        available = self.get_available_sources()
        
        if not available:
            logger.warning("沒有可用的新聞資料源（全部在冷卻中）")
            return None
        
        # Round-robin 從當前索引開始找
        checked = 0
        while checked < len(self.sources):
            source = self.sources[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.sources)
            checked += 1
            
            if source.health.is_available:
                return source
        
        return None
    
    def fetch_news(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        智慧獲取新聞資料
        
        會自動：
        1. 選擇最佳可用資料源
        2. 失敗時嘗試備援來源
        3. 記錄健康狀態
        4. 觸發冷卻機制
        
        Args:
            **kwargs: 傳遞給資料源 fetch_function 的參數
            
        Returns:
            新聞資料字典或 None
        """
        available_sources = self.get_available_sources()
        
        if not available_sources:
            logger.error("所有資料源都在冷卻中，無法獲取新聞")
            return None
        
        if len(available_sources) < self.min_sources:
            logger.warning(f"可用資料源 ({len(available_sources)}) 低於最低要求 ({self.min_sources})")
        
        # 嘗試獲取新聞
        attempted_sources = []
        
        for _ in range(len(available_sources)):
            source = self.get_next_source()
            if source is None:
                break
            
            attempted_sources.append(source.name)
            logger.info(f"嘗試從 [{source.name}] 獲取新聞...")
            
            try:
                # 呼叫資料源的 fetch 函數
                result = source.fetch_function(**kwargs)
                
                if result and self._validate_result(result):
                    # 成功
                    self._record_success(source)
                    logger.info(f"✓ 從 [{source.name}] 成功獲取新聞")
                    return {
                        'data': result,
                        'source': source.name,
                        'timestamp': datetime.now().isoformat(),
                        'health': str(source.health)
                    }
                else:
                    # 結果無效
                    logger.warning(f"[{source.name}] 返回無效結果")
                    self._record_failure(source, "invalid_result")
                    
            except Exception as e:
                # 例外處理
                logger.error(f"[{source.name}] 發生錯誤: {str(e)}")
                self._record_failure(source, str(e))
            
            # 如果不啟用備援，直接返回
            if not self.enable_fallback:
                break
        
        logger.error(f"所有嘗試的資料源都失敗: {attempted_sources}")
        return None
    
    def _validate_result(self, result: Any) -> bool:
        """驗證結果是否有效"""
        if result is None:
            return False
        
        # 如果是字典，檢查是否有資料
        if isinstance(result, dict):
            return bool(result)
        
        # 如果是列表，檢查是否非空
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
        
        # 恢復狀態
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
        
        # 檢查是否需要進入冷卻
        if health.consecutive_failures >= source.max_failures:
            health.status = SourceStatus.COOLING
            health.cooldown_until = datetime.now() + timedelta(seconds=source.cooldown_seconds)
            
            logger.warning(
                f"[{source.name}] 連續失敗 {health.consecutive_failures} 次，"
                f"進入冷卻狀態 {source.cooldown_seconds} 秒"
            )
        else:
            health.status = SourceStatus.DEGRADED
    
    def get_health_report(self) -> Dict[str, Any]:
        """獲取所有資料源的健康報告"""
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
                    'cooldown_remaining': self._get_cooldown_remaining(s),
                    'last_success': s.health.last_success.isoformat() if s.health.last_success else None,
                    'last_failure': s.health.last_failure.isoformat() if s.health.last_failure else None
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
    
    def reset_source(self, source_name: str):
        """手動重置某個資料源的狀態"""
        for source in self.sources:
            if source.name == source_name:
                source.health = SourceHealth(name=source_name)
                logger.info(f"已重置 [{source_name}] 的健康狀態")
                return True
        
        logger.warning(f"找不到資料源: {source_name}")
        return False
    
    def reset_all(self):
        """重置所有資料源狀態"""
        for source in self.sources:
            source.health = SourceHealth(name=source.name)
        logger.info("已重置所有資料源的健康狀態")


# 使用範例
if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 模擬新聞源函數
    def fetch_cryptopanic(**kwargs):
        import random
        if random.random() < 0.7:  # 70% 成功率
            return {'articles': ['news1', 'news2'], 'source': 'cryptopanic'}
        raise Exception("API rate limit exceeded")
    
    def fetch_coindesk(**kwargs):
        import random
        if random.random() < 0.8:  # 80% 成功率
            return {'articles': ['article1', 'article2'], 'source': 'coindesk'}
        raise Exception("Connection timeout")
    
    def fetch_cointelegraph(**kwargs):
        return {'articles': ['story1', 'story2'], 'source': 'cointelegraph'}
    
    # 創建資料源
    sources = [
        NewsSource(
            name="CryptoPanic",
            fetch_function=fetch_cryptopanic,
            priority=1,
            max_failures=2,
            cooldown_seconds=10
        ),
        NewsSource(
            name="CoinDesk",
            fetch_function=fetch_coindesk,
            priority=2,
            max_failures=3,
            cooldown_seconds=15
        ),
        NewsSource(
            name="CoinTelegraph",
            fetch_function=fetch_cointelegraph,
            priority=3,
            max_failures=3,
            cooldown_seconds=20
        )
    ]
    
    # 創建管理器
    manager = NewsSourceManager(sources, enable_fallback=True)
    
    # 測試連續請求
    print("\n=== 測試智慧新聞獲取 ===\n")
    for i in range(10):
        print(f"\n--- 第 {i+1} 次請求 ---")
        result = manager.fetch_news()
        
        if result:
            print(f"✓ 成功: {result['source']}")
        else:
            print("✗ 失敗: 所有資料源都不可用")
        
        # 顯示健康狀態
        print("\n當前狀態:")
        for source in manager.sources:
            print(f"  {source.health}")
        
        time.sleep(2)
    
    # 顯示完整健康報告
    print("\n\n=== 健康報告 ===")
    import json
    print(json.dumps(manager.get_health_report(), indent=2, ensure_ascii=False))
