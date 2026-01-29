"""
市場數據分析器
從幣安獲取市場數據並進行預處理
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """市場數據分析器"""
    
    def __init__(self, config: Dict, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        初始化市場分析器
        
        Args:
            config: 配置字典
            api_key: 幣安 API Key（可選，從環境變數讀取）
            api_secret: 幣安 API Secret（可選，從環境變數讀取）
        """
        self.config = config
        self.trading_config = config['trading']
        self.symbol = self.trading_config['symbol']
        self.timeframe = self.trading_config['timeframe']
        self.lookback_periods = self.trading_config['lookback_periods']
        
        # 從環境變數或參數獲取 API 憑證
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        
        # 初始化幣安客戶端
        try:
            self.client = Client(self.api_key, self.api_secret)
            logger.info("成功連接到幣安 API")
        except Exception as e:
            logger.error(f"連接幣安 API 失敗: {e}")
            self.client = None
    
    def fetch_klines(self, symbol: Optional[str] = None, 
                     interval: Optional[str] = None, 
                     limit: Optional[int] = None) -> pd.DataFrame:
        """
        獲取 K 線數據
        
        Args:
            symbol: 交易對（例如 BTCUSDT）
            interval: 時間間隔（例如 15m, 1h, 4h, 1d）
            limit: 數據條數
            
        Returns:
            包含 OHLCV 數據的 DataFrame
        """
        if not self.client:
            raise Exception("幣安客戶端未初始化")
        
        symbol = symbol or self.symbol
        interval = interval or self.timeframe
        limit = limit or self.lookback_periods
        
        try:
            logger.info(f"獲取 {symbol} {interval} K線數據，數量: {limit}")
            
            # 獲取 K 線數據
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # 轉換為 DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 數據類型轉換
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # 只保留必要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"成功獲取 {len(df)} 條 K 線數據")
            return df
            
        except BinanceAPIException as e:
            logger.error(f"幣安 API 錯誤: {e}")
            raise
        except Exception as e:
            logger.error(f"獲取 K 線數據失敗: {e}")
            raise
    
    def get_current_price(self, symbol: Optional[str] = None) -> float:
        """
        獲取當前價格
        
        Args:
            symbol: 交易對
            
        Returns:
            當前價格
        """
        if not self.client:
            raise Exception("幣安客戶端未初始化")
        
        symbol = symbol or self.symbol
        
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            logger.info(f"{symbol} 當前價格: ${price:.2f}")
            return price
        except Exception as e:
            logger.error(f"獲取當前價格失敗: {e}")
            raise
    
    def get_24h_stats(self, symbol: Optional[str] = None) -> Dict:
        """
        獲取 24 小時統計數據
        
        Args:
            symbol: 交易對
            
        Returns:
            24 小時統計數據字典
        """
        if not self.client:
            raise Exception("幣安客戶端未初始化")
        
        symbol = symbol or self.symbol
        
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            
            stats = {
                'symbol': ticker['symbol'],
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'high_price': float(ticker['highPrice']),
                'low_price': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume']),
                'trades': int(ticker['count'])
            }
            
            logger.info(f"{symbol} 24h 漲跌: {stats['price_change_percent']:.2f}%")
            return stats
            
        except Exception as e:
            logger.error(f"獲取 24 小時統計失敗: {e}")
            raise
    
    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> float:
        """
        計算價格波動率（標準差）
        
        Args:
            df: K 線數據 DataFrame
            window: 計算窗口
            
        Returns:
            波動率（百分比）
        """
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=window).std().iloc[-1]
        return volatility
    
    def check_market_conditions(self) -> Dict:
        """
        檢查市場狀況
        
        Returns:
            市場狀況評估字典
        """
        try:
            # 獲取數據
            df = self.fetch_klines()
            stats_24h = self.get_24h_stats()
            volatility = self.calculate_volatility(df)
            
            # 判斷市場狀態
            is_high_volatility = volatility > self.config['risk_management']['volatility_threshold']
            
            market_status = {
                'timestamp': datetime.now().isoformat(),
                'symbol': self.symbol,
                'current_price': df.iloc[-1]['close'],
                'price_change_24h': stats_24h['price_change_percent'],
                'volume_24h': stats_24h['volume'],
                'volatility': round(volatility * 100, 2),  # 轉換為百分比
                'is_high_volatility': is_high_volatility,
                'trades_24h': stats_24h['trades'],
                'high_24h': stats_24h['high_price'],
                'low_24h': stats_24h['low_price']
            }
            
            if is_high_volatility:
                logger.warning(f"市場波動率過高: {market_status['volatility']:.2f}%")
            
            return market_status
            
        except Exception as e:
            logger.error(f"檢查市場狀況失敗: {e}")
            raise
    
    def is_market_stable(self) -> Dict:
        """
        判斷市場是否穩定適合交易
        
        Returns:
            包含穩定性評估的字典
        """
        try:
            market_conditions = self.check_market_conditions()
            
            is_stable = not market_conditions['is_high_volatility']
            
            return {
                'stable': is_stable,
                'reason': '市場穩定' if is_stable else f"波動率過高 ({market_conditions['volatility']:.2f}%)",
                'market_conditions': market_conditions
            }
            
        except Exception as e:
            logger.error(f"評估市場穩定性失敗: {e}")
            return {
                'stable': False,
                'reason': f'無法獲取市場數據: {str(e)}',
                'market_conditions': None
            }
