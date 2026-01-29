"""
市場數據查詢模組
整合 CoinGecko API 提供即時加密貨幣市場數據

支援功能:
- 單一幣種價格查詢
- 多幣種價格總覽
- 市場總體數據
- 恐慌與貪婪指數
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional

class MarketDataAPI:
    """市場數據 API 客戶端"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.fear_greed_url = "https://api.alternative.me/fng/"
        
        # 常用幣種映射 (方便用戶輸入)
        self.symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
        }
    
    def get_coin_id(self, symbol: str) -> str:
        """將幣種代碼轉換為 CoinGecko ID"""
        symbol = symbol.upper()
        return self.symbol_map.get(symbol, symbol.lower())
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """
        查詢單一幣種價格
        
        Args:
            symbol: 幣種代碼 (如 BTC, ETH)
        
        Returns:
            包含價格資訊的字典，失敗返回 None
        """
        try:
            coin_id = self.get_coin_id(symbol)
            
            url = f"{self.coingecko_base}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 提取關鍵資訊
            market_data = data.get('market_data', {})
            
            return {
                'symbol': symbol.upper(),
                'name': data.get('name'),
                'price_usd': market_data.get('current_price', {}).get('usd'),
                'price_change_24h': market_data.get('price_change_percentage_24h'),
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'volume_24h': market_data.get('total_volume', {}).get('usd'),
                'high_24h': market_data.get('high_24h', {}).get('usd'),
                'low_24h': market_data.get('low_24h', {}).get('usd'),
                'ath': market_data.get('ath', {}).get('usd'),
                'ath_change': market_data.get('ath_change_percentage', {}).get('usd'),
                'last_updated': data.get('last_updated'),
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 查詢 {symbol} 價格失敗: {e}")
            return None
        except Exception as e:
            print(f"❌ 處理 {symbol} 數據時出錯: {e}")
            return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量查詢多個幣種價格
        
        Args:
            symbols: 幣種代碼列表
        
        Returns:
            字典，鍵為幣種代碼，值為價格資訊
        """
        try:
            # 轉換為 CoinGecko IDs
            coin_ids = [self.get_coin_id(s) for s in symbols]
            ids_param = ','.join(coin_ids)
            
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': ids_param,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 整理結果
            results = {}
            for symbol, coin_id in zip(symbols, coin_ids):
                if coin_id in data:
                    coin_data = data[coin_id]
                    results[symbol.upper()] = {
                        'price_usd': coin_data.get('usd'),
                        'price_change_24h': coin_data.get('usd_24h_change'),
                        'volume_24h': coin_data.get('usd_24h_vol'),
                        'market_cap': coin_data.get('usd_market_cap'),
                    }
            
            return results
            
        except Exception as e:
            print(f"❌ 批量查詢價格失敗: {e}")
            return {}
    
    def get_market_overview(self) -> Optional[Dict]:
        """
        獲取市場總覽數據
        
        Returns:
            市場總體數據字典
        """
        try:
            url = f"{self.coingecko_base}/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', {})
            
            return {
                'total_market_cap': data.get('total_market_cap', {}).get('usd'),
                'total_volume_24h': data.get('total_volume', {}).get('usd'),
                'btc_dominance': data.get('market_cap_percentage', {}).get('btc'),
                'eth_dominance': data.get('market_cap_percentage', {}).get('eth'),
                'active_cryptocurrencies': data.get('active_cryptocurrencies'),
                'markets': data.get('markets'),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd'),
            }
            
        except Exception as e:
            print(f"❌ 獲取市場總覽失敗: {e}")
            return None
    
    def get_fear_greed_index(self) -> Optional[Dict]:
        """
        獲取恐慌與貪婪指數
        
        Returns:
            恐慌指數數據
        """
        try:
            response = requests.get(self.fear_greed_url, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', [{}])[0]
            
            value = int(data.get('value', 0))
            classification = data.get('value_classification', 'Unknown')
            
            return {
                'value': value,
                'classification': classification,
                'timestamp': data.get('timestamp'),
            }
            
        except Exception as e:
            print(f"❌ 獲取恐慌指數失敗: {e}")
            return None
    
    def get_top_coins(self, limit: int = 10) -> List[Dict]:
        """
        獲取市值排名前 N 的幣種
        
        Args:
            limit: 返回數量，預設 10
        
        Returns:
            幣種列表
        """
        try:
            url = f"{self.coingecko_base}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for coin in data:
                results.append({
                    'rank': coin.get('market_cap_rank'),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name'),
                    'price_usd': coin.get('current_price'),
                    'price_change_24h': coin.get('price_change_percentage_24h'),
                    'market_cap': coin.get('market_cap'),
                    'volume_24h': coin.get('total_volume'),
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 獲取排行榜失敗: {e}")
            return []


class MarketDataFormatter:
    """市場數據格式化工具"""
    
    @staticmethod
    def format_price(price: Optional[float]) -> str:
        """格式化價格顯示"""
        if price is None:
            return "N/A"
        
        if price >= 1:
            return f"${price:,.2f}"
        elif price >= 0.01:
            return f"${price:.4f}"
        else:
            return f"${price:.8f}"
    
    @staticmethod
    def format_large_number(num: Optional[float]) -> str:
        """格式化大數字 (市值、交易量)"""
        if num is None:
            return "N/A"
        
        if num >= 1_000_000_000_000:  # 兆
            return f"${num/1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:  # 十億
            return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:  # 百萬
            return f"${num/1_000_000:.2f}M"
        else:
            return f"${num:,.0f}"
    
    @staticmethod
    def format_percentage(pct: Optional[float]) -> str:
        """格式化百分比變化"""
        if pct is None:
            return "N/A"
        
        emoji = "🟢" if pct >= 0 else "🔴"
        sign = "+" if pct >= 0 else ""
        return f"{emoji} {sign}{pct:.2f}%"
    
    @staticmethod
    def format_coin_price(data: Dict) -> str:
        """格式化單一幣種價格訊息"""
        if not data:
            return "❌ 查詢失敗"
        
        msg = f"<b>💰 {data['name']} ({data['symbol']})</b>\n\n"
        msg += f"💵 價格: {MarketDataFormatter.format_price(data['price_usd'])}\n"
        msg += f"📊 24h 變化: {MarketDataFormatter.format_percentage(data['price_change_24h'])}\n"
        msg += f"📈 24h 最高: {MarketDataFormatter.format_price(data['high_24h'])}\n"
        msg += f"📉 24h 最低: {MarketDataFormatter.format_price(data['low_24h'])}\n"
        msg += f"💎 市值: {MarketDataFormatter.format_large_number(data['market_cap'])}\n"
        msg += f"💧 24h 交易量: {MarketDataFormatter.format_large_number(data['volume_24h'])}\n"
        msg += f"🏔 歷史最高: {MarketDataFormatter.format_price(data['ath'])} ({MarketDataFormatter.format_percentage(data['ath_change'])})\n"
        
        return msg
    
    @staticmethod
    def format_multiple_prices(data: Dict[str, Dict]) -> str:
        """格式化多幣種價格列表"""
        if not data:
            return "❌ 查詢失敗"
        
        msg = "<b>💰 主流幣種價格</b>\n\n"
        
        for symbol, coin_data in data.items():
            price = MarketDataFormatter.format_price(coin_data.get('price_usd'))
            change = MarketDataFormatter.format_percentage(coin_data.get('price_change_24h'))
            msg += f"<b>{symbol}</b>: {price} {change}\n"
        
        return msg
    
    @staticmethod
    def format_market_overview(data: Dict, fear_greed: Optional[Dict] = None) -> str:
        """格式化市場總覽"""
        if not data:
            return "❌ 查詢失敗"
        
        msg = "<b>🌐 加密貨幣市場總覽</b>\n\n"
        msg += f"💎 總市值: {MarketDataFormatter.format_large_number(data['total_market_cap'])}\n"
        msg += f"📊 24h 市值變化: {MarketDataFormatter.format_percentage(data['market_cap_change_24h'])}\n"
        msg += f"💧 24h 交易量: {MarketDataFormatter.format_large_number(data['total_volume_24h'])}\n"
        msg += f"₿ BTC 佔比: {data['btc_dominance']:.1f}%\n"
        msg += f"Ξ ETH 佔比: {data['eth_dominance']:.1f}%\n"
        msg += f"🪙 活躍幣種: {data['active_cryptocurrencies']:,}\n"
        msg += f"🏦 交易所數量: {data['markets']:,}\n"
        
        # 添加恐慌指數
        if fear_greed:
            value = fear_greed['value']
            classification = fear_greed['classification']
            
            # 選擇 emoji
            if value >= 75:
                emoji = "🤑"
            elif value >= 55:
                emoji = "😊"
            elif value >= 45:
                emoji = "😐"
            elif value >= 25:
                emoji = "😨"
            else:
                emoji = "😱"
            
            msg += f"\n{emoji} <b>恐慌指數</b>: {value} ({classification})\n"
        
        return msg
    
    @staticmethod
    def format_top_coins(coins: List[Dict]) -> str:
        """格式化排行榜"""
        if not coins:
            return "❌ 查詢失敗"
        
        msg = "<b>🏆 市值排行榜 Top 10</b>\n\n"
        
        for coin in coins:
            rank = coin['rank']
            symbol = coin['symbol']
            name = coin['name']
            price = MarketDataFormatter.format_price(coin['price_usd'])
            change = MarketDataFormatter.format_percentage(coin['price_change_24h'])
            
            msg += f"{rank}. <b>{symbol}</b> ({name})\n"
            msg += f"   {price} {change}\n\n"
        
        return msg


# 使用範例
if __name__ == "__main__":
    api = MarketDataAPI()
    formatter = MarketDataFormatter()
    
    # 測試單一幣種查詢
    print("=" * 50)
    btc_data = api.get_price("BTC")
    print(formatter.format_coin_price(btc_data))
    
    # 測試多幣種查詢
    print("=" * 50)
    coins = ['BTC', 'ETH', 'BNB', 'SOL']
    prices = api.get_multiple_prices(coins)
    print(formatter.format_multiple_prices(prices))
    
    # 測試市場總覽
    print("=" * 50)
    market = api.get_market_overview()
    fear_greed = api.get_fear_greed_index()
    print(formatter.format_market_overview(market, fear_greed))
    
    # 測試排行榜
    print("=" * 50)
    top_coins = api.get_top_coins(10)
    print(formatter.format_top_coins(top_coins))
