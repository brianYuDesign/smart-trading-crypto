"""
交易信號生成器
使用技術指標分析市場並生成買賣信號
"""
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalGenerator:
    """交易信號生成器"""
    
    def __init__(self, config: Dict):
        """
        初始化信號生成器
        
        Args:
            config: 配置字典，包含技術指標參數
        """
        self.config = config
        self.rsi_config = config['indicators']['rsi']
        self.macd_config = config['indicators']['macd']
        self.bb_config = config['indicators']['bollinger_bands']
        self.volume_config = config['indicators']['volume']
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算所有技術指標
        
        Args:
            df: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            添加了技術指標的 DataFrame
        """
        # RSI
        rsi_indicator = RSIIndicator(
            close=df['close'], 
            window=self.rsi_config['period']
        )
        df['rsi'] = rsi_indicator.rsi()
        
        # MACD
        macd_indicator = MACD(
            close=df['close'],
            window_fast=self.macd_config['fast_period'],
            window_slow=self.macd_config['slow_period'],
            window_sign=self.macd_config['signal_period']
        )
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_diff'] = macd_indicator.macd_diff()
        
        # 布林帶
        bb_indicator = BollingerBands(
            close=df['close'],
            window=self.bb_config['period'],
            window_dev=self.bb_config['std_dev']
        )
        df['bb_upper'] = bb_indicator.bollinger_hband()
        df['bb_middle'] = bb_indicator.bollinger_mavg()
        df['bb_lower'] = bb_indicator.bollinger_lband()
        
        # 成交量移動平均
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def detect_buy_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        檢測買入信號
        
        條件：
        1. RSI < 30 (超賣)
        2. 價格觸及或跌破布林帶下軌後反彈
        3. MACD 金叉
        4. 成交量放大
        
        Args:
            df: 包含技術指標的 DataFrame
            
        Returns:
            如果檢測到信號，返回信號字典；否則返回 None
        """
        if len(df) < 2:
            return None
        
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # 條件檢查
        rsi_oversold = latest['rsi'] < self.rsi_config['oversold']
        
        # 布林帶反彈：前一根 K 線觸及下軌，當前 K 線收盤高於下軌
        bb_bounce = (
            previous['close'] <= previous['bb_lower'] and
            latest['close'] > latest['bb_lower']
        )
        
        # MACD 金叉：MACD 線從下方穿越信號線
        macd_cross = (
            previous['macd'] <= previous['macd_signal'] and
            latest['macd'] > latest['macd_signal']
        )
        
        # 成交量放大
        volume_surge = latest['volume_ratio'] > self.volume_config['surge_threshold']
        
        # 計算信號強度（滿足的條件數量）
        conditions_met = sum([rsi_oversold, bb_bounce, macd_cross, volume_surge])
        
        # 至少滿足 3 個條件才發出信號
        if conditions_met >= 3:
            signal = {
                'type': 'BUY',
                'price': latest['close'],
                'timestamp': latest['timestamp'],
                'rsi': round(latest['rsi'], 2),
                'macd': round(latest['macd'], 4),
                'macd_signal': round(latest['macd_signal'], 4),
                'volume_ratio': round(latest['volume_ratio'], 2),
                'conditions_met': conditions_met,
                'strength': 'STRONG' if conditions_met == 4 else 'MODERATE',
                'reasons': []
            }
            
            if rsi_oversold:
                signal['reasons'].append(f"RSI 超賣 ({round(latest['rsi'], 2)})")
            if bb_bounce:
                signal['reasons'].append("布林帶下軌反彈")
            if macd_cross:
                signal['reasons'].append("MACD 金叉")
            if volume_surge:
                signal['reasons'].append(f"成交量放大 ({round(latest['volume_ratio'], 2)}x)")
            
            logger.info(f"檢測到買入信號: {signal}")
            return signal
        
        return None
    
    def detect_sell_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        檢測賣出信號
        
        條件：
        1. RSI > 70 (超買)
        2. 價格觸及或突破布林帶上軌
        3. MACD 死叉
        4. 成交量萎縮或異常放大
        
        Args:
            df: 包含技術指標的 DataFrame
            
        Returns:
            如果檢測到信號，返回信號字典；否則返回 None
        """
        if len(df) < 2:
            return None
        
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # 條件檢查
        rsi_overbought = latest['rsi'] > self.rsi_config['overbought']
        
        # 觸及布林帶上軌
        bb_top = latest['close'] >= latest['bb_upper']
        
        # MACD 死叉：MACD 線從上方穿越信號線
        macd_cross = (
            previous['macd'] >= previous['macd_signal'] and
            latest['macd'] < latest['macd_signal']
        )
        
        # MACD 柱狀圖轉負
        macd_histogram_negative = latest['macd_diff'] < 0 and previous['macd_diff'] > 0
        
        # 計算信號強度
        conditions_met = sum([rsi_overbought, bb_top, macd_cross, macd_histogram_negative])
        
        # 至少滿足 2 個條件才發出信號
        if conditions_met >= 2:
            signal = {
                'type': 'SELL',
                'price': latest['close'],
                'timestamp': latest['timestamp'],
                'rsi': round(latest['rsi'], 2),
                'macd': round(latest['macd'], 4),
                'macd_signal': round(latest['macd_signal'], 4),
                'volume_ratio': round(latest['volume_ratio'], 2),
                'conditions_met': conditions_met,
                'strength': 'STRONG' if conditions_met >= 3 else 'MODERATE',
                'reasons': []
            }
            
            if rsi_overbought:
                signal['reasons'].append(f"RSI 超買 ({round(latest['rsi'], 2)})")
            if bb_top:
                signal['reasons'].append("觸及布林帶上軌")
            if macd_cross:
                signal['reasons'].append("MACD 死叉")
            if macd_histogram_negative:
                signal['reasons'].append("MACD 柱狀圖轉負")
            
            logger.info(f"檢測到賣出信號: {signal}")
            return signal
        
        return None
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        分析市場數據並生成交易信號
        
        Args:
            df: 原始 OHLCV 數據
            
        Returns:
            包含分析結果的字典
        """
        # 計算指標
        df = self.calculate_indicators(df)
        
        # 檢測信號
        buy_signal = self.detect_buy_signal(df)
        sell_signal = self.detect_sell_signal(df)
        
        latest = df.iloc[-1]
        
        result = {
            'timestamp': latest['timestamp'],
            'price': latest['close'],
            'rsi': round(latest['rsi'], 2),
            'macd': round(latest['macd'], 4),
            'macd_signal': round(latest['macd_signal'], 4),
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'has_signal': buy_signal is not None or sell_signal is not None
        }
        
        return result
