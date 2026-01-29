"""
技術分析模組 - 輕量版
提供技術指標計算與文字格式輸出（避免圖表生成的複雜性）

功能:
- RSI 指標
- 移動平均線 (MA)
- 價格趨勢分析
- 支撐阻力位
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

class TechnicalAnalyzer:
    """技術分析工具"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        self.symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
        }
    
    def get_coin_id(self, symbol: str) -> str:
        """轉換幣種代碼"""
        symbol = symbol.upper()
        return self.symbol_map.get(symbol, symbol.lower())
    
    def fetch_price_history(self, symbol: str, days: int = 30) -> Optional[List[float]]:
        """獲取歷史價格"""
        try:
            coin_id = self.get_coin_id(symbol)
            url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = [p[1] for p in data.get('prices', [])]
            return prices if prices else None
            
        except Exception as e:
            print(f"❌ 獲取歷史數據失敗: {e}")
            return None
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """計算 RSI 指標"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """計算移動平均線"""
        if len(prices) < period:
            return None
        
        return round(np.mean(prices[-period:]), 2)
    
    def analyze_trend(self, prices: List[float]) -> str:
        """分析價格趨勢"""
        if len(prices) < 7:
            return "數據不足"
        
        recent = prices[-7:]  # 最近7天
        older = prices[-14:-7]  # 之前7天
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        change = ((recent_avg - older_avg) / older_avg) * 100
        
        if change > 5:
            return "🟢 強勢上漲"
        elif change > 2:
            return "🟢 上漲"
        elif change > -2:
            return "🟡 橫盤整理"
        elif change > -5:
            return "🔴 下跌"
        else:
            return "🔴 強勢下跌"
    
    def find_support_resistance(self, prices: List[float]) -> Dict:
        """尋找支撐與阻力位"""
        if len(prices) < 30:
            return {'support': None, 'resistance': None}
        
        recent = prices[-30:]
        current = prices[-1]
        
        # 支撐位：最近30天的最低價附近
        support = round(min(recent), 2)
        
        # 阻力位：最近30天的最高價附近
        resistance = round(max(recent), 2)
        
        return {
            'support': support,
            'resistance': resistance,
            'distance_to_support': round(((current - support) / current) * 100, 2),
            'distance_to_resistance': round(((resistance - current) / current) * 100, 2)
        }
    
    def get_technical_analysis(self, symbol: str) -> Optional[Dict]:
        """完整技術分析"""
        prices = self.fetch_price_history(symbol, days=30)
        if not prices:
            return None
        
        current_price = prices[-1]
        
        # 計算各項指標
        rsi = self.calculate_rsi(prices)
        ma7 = self.calculate_ma(prices, 7)
        ma30 = self.calculate_ma(prices, 30)
        trend = self.analyze_trend(prices)
        sr = self.find_support_resistance(prices)
        
        # RSI 信號
        if rsi:
            if rsi > 70:
                rsi_signal = "超買 ⚠️"
            elif rsi < 30:
                rsi_signal = "超賣 💰"
            else:
                rsi_signal = "中性"
        else:
            rsi_signal = "N/A"
        
        # MA 信號
        if ma7 and ma30:
            if ma7 > ma30:
                ma_signal = "多頭排列 🟢"
            else:
                ma_signal = "空頭排列 🔴"
        else:
            ma_signal = "N/A"
        
        return {
            'symbol': symbol.upper(),
            'current_price': round(current_price, 2),
            'rsi': rsi,
            'rsi_signal': rsi_signal,
            'ma7': ma7,
            'ma30': ma30,
            'ma_signal': ma_signal,
            'trend': trend,
            'support': sr['support'],
            'resistance': sr['resistance'],
            'distance_to_support': sr['distance_to_support'],
            'distance_to_resistance': sr['distance_to_resistance']
        }


class TechnicalAnalysisFormatter:
    """技術分析格式化工具"""
    
    @staticmethod
    def format_analysis(data: Dict) -> str:
        """格式化技術分析報告"""
        if not data:
            return "❌ 分析失敗"
        
        msg = f"<b>📊 技術分析報告 - {data['symbol']}</b>\n\n"
        msg += f"💵 <b>當前價格</b>: ${data['current_price']:,.2f}\n\n"
        
        msg += "<b>📈 技術指標</b>\n"
        msg += f"• RSI(14): {data['rsi']} ({data['rsi_signal']})\n"
        msg += f"• MA7: ${data['ma7']:,.2f}\n"
        msg += f"• MA30: ${data['ma30']:,.2f}\n"
        msg += f"• 均線狀態: {data['ma_signal']}\n\n"
        
        msg += "<b>🎯 趨勢分析</b>\n"
        msg += f"• 短期趨勢: {data['trend']}\n\n"
        
        msg += "<b>📍 支撐與阻力</b>\n"
        msg += f"• 支撐位: ${data['support']:,.2f} "
        msg += f"({data['distance_to_support']:+.1f}%)\n"
        msg += f"• 阻力位: ${data['resistance']:,.2f} "
        msg += f"({data['distance_to_resistance']:+.1f}%)\n\n"
        
        # 綜合建議
        msg += "<b>💡 綜合評估</b>\n"
        
        signals = []
        if data['rsi']:
            if data['rsi'] < 30:
                signals.append("RSI 超賣，可能反彈")
            elif data['rsi'] > 70:
                signals.append("RSI 超買，注意回調")
        
        if "多頭" in data['ma_signal']:
            signals.append("均線多頭排列")
        elif "空頭" in data['ma_signal']:
            signals.append("均線空頭排列")
        
        if signals:
            for signal in signals:
                msg += f"• {signal}\n"
        else:
            msg += "• 市場處於觀望狀態\n"
        
        msg += "\n⚠️ 僅供參考，投資需謹慎"
        
        return msg


# 使用範例
if __name__ == "__main__":
    analyzer = TechnicalAnalyzer()
    formatter = TechnicalAnalysisFormatter()
    
    print("=" * 70)
    print("測試技術分析功能")
    print("=" * 70)
    
    # 分析 BTC
    print("\n分析 BTC...")
    result = analyzer.get_technical_analysis('BTC')
    if result:
        print(formatter.format_analysis(result))
    else:
        print("❌ 分析失敗")
