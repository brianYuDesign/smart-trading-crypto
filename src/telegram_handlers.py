"""
Telegram Bot 指令處理器
處理 /price, /news, /market 等指令
"""

import logging
from datetime import datetime
from typing import Optional
from crypto_data_service import (
    CryptoDataService, 
    format_number, 
    format_percentage,
    get_sentiment_emoji,
    get_fng_emoji
)

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """Telegram Bot 指令處理器"""
    
    def __init__(self, config: Optional[dict] = None):
        self.data_service = CryptoDataService(config)
    
    # ==================== /price 指令 ====================
    
    def handle_price(self, symbol: str) -> str:
        """
        處理 /price 指令
        
        用法: /price BTC
        """
        if not symbol:
            return self._price_usage_message()
        
        symbol = symbol.upper().strip()
        data = self.data_service.get_coin_price(symbol)
        
        if not data:
            return f"❌ 找不到 {symbol} 的價格資訊\n\n請確認幣種符號是否正確"
        
        return self._format_price_message(data)
    
    def _format_price_message(self, data: dict) -> str:
        """格式化價格訊息"""
        symbol = data['symbol']
        name = data['name']
        price = data['price']
        change_24h = data['price_change_percentage_24h']
        high_24h = data['high_24h']
        low_24h = data['low_24h']
        volume = data['total_volume']
        market_cap = data['market_cap']
        rank = data['market_cap_rank']
        circulating = data['circulating_supply']
        total_supply = data['total_supply']
        
        # 格式化更新時間
        try:
            updated = datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
            update_time = updated.strftime('%Y-%m-%d %H:%M')
        except:
            update_time = "N/A"
        
        message = f"""🪙 {name} ({symbol})
━━━━━━━━━━━━━━━━━━━━
💵 價格：${price:,.2f}

📊 24小時變化
• 漲跌：{format_percentage(change_24h)}
• 最高：${high_24h:,.2f}
• 最低：${low_24h:,.2f}
• 成交量：{format_number(volume)}

📈 市場資訊
• 市值：{format_number(market_cap)} (#{rank})
• 流通量：{circulating:,.0f} {symbol}"""
        
        if total_supply and total_supply > 0:
            message += f"\n• 總供應量：{total_supply:,.0f} {symbol}"
        
        message += f"""

🔗 更多資訊
[CoinGecko](https://www.coingecko.com/en/coins/{name.lower()}) | [CoinMarketCap](https://coinmarketcap.com/currencies/{name.lower()}/) | [TradingView](https://www.tradingview.com/chart/?symbol={symbol}USD)

⏰ 更新時間：{update_time}"""
        
        return message
    
    def _price_usage_message(self) -> str:
        """價格查詢使用說明"""
        return """📊 價格查詢使用方式

用法：/price <幣種符號>

範例：
• /price BTC
• /price ETH
• /price SOL

支援的主流幣種：
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, DOT, MATIC, AVAX 等"""
    
    # ==================== /news 指令 ====================
    
    def handle_news(self, currencies: Optional[str] = None, limit: int = 5) -> str:
        """
        處理 /news 指令
        
        用法: 
        - /news (全部新聞)
        - /news BTC (特定幣種)
        - /news BTC ETH (多個幣種)
        """
        currency_list = None
        if currencies:
            currency_list = [c.strip().upper() for c in currencies.split()]
        
        data = self.data_service.get_crypto_news(currency_list, limit)
        
        if not data or not data.get('news'):
            return "❌ 無法獲取新聞資訊\n\n請稍後再試"
        
        return self._format_news_message(data, currency_list)
    
    def _format_news_message(self, data: dict, currencies: Optional[list] = None) -> str:
        """格式化新聞訊息"""
        news_list = data['news']
        source = data['source']
        sentiment = data['sentiment_summary']
        
        # 標題
        if currencies:
            title = f"📰 {' '.join(currencies)} 最新消息"
        else:
            title = "📰 加密貨幣最新消息"
        
        message = f"""{title}

━━━━━━━━━━━━━━━━━━━━
🔥 熱門新聞

"""
        
        # 新聞列表
        for idx, news in enumerate(news_list, 1):
            title = news['title']
            domain = news['domain']
            url = news['url']
            sentiment_type = news['sentiment']
            sentiment_emoji = get_sentiment_emoji(sentiment_type)
            
            # 計算時間差
            try:
                published = datetime.fromisoformat(news['published'].replace('Z', '+00:00'))
                now = datetime.now(published.tzinfo)
                diff = now - published
                
                if diff.days > 0:
                    time_ago = f"{diff.days}天前"
                elif diff.seconds >= 3600:
                    time_ago = f"{diff.seconds // 3600}小時前"
                else:
                    time_ago = f"{diff.seconds // 60}分鐘前"
            except:
                time_ago = "最近"
            
            # 情緒標籤
            sentiment_label = {
                'positive': '看漲',
                'neutral': '中性',
                'negative': '看跌'
            }.get(sentiment_type, '中性')
            
            message += f"""{idx}️⃣ 【{sentiment_label} {sentiment_emoji}】{title}
   📅 {time_ago} | 📰 {domain}
   🔗 [閱讀全文]({url})

"""
        
        # 情緒摘要
        message += f"""━━━━━━━━━━━━━━━━━━━━
📊 新聞情緒：{sentiment['positive']}% 看漲 | {sentiment['neutral']}% 中性 | {sentiment['negative']}% 看跌

⏰ 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
💡 數據來源：{source}"""
        
        return message
    
    # ==================== /market 指令 ====================
    
    def handle_market(self) -> str:
        """
        處理 /market 指令
        
        顯示市場總覽
        """
        market_data = self.data_service.get_market_overview()
        fng_data = self.data_service.get_fear_greed_index()
        
        if not market_data:
            return "❌ 無法獲取市場資訊\n\n請稍後再試"
        
        return self._format_market_message(market_data, fng_data)
    
    def _format_market_message(self, market_data: dict, fng_data: Optional[dict] = None) -> str:
        """格式化市場總覽訊息"""
        total_cap = market_data['total_market_cap']
        total_volume = market_data['total_volume']
        cap_change = market_data['market_cap_change_24h']
        btc_dom = market_data['btc_dominance']
        eth_dom = market_data['eth_dominance']
        top_coins = market_data['top_coins']
        gainers = market_data['top_gainers']
        losers = market_data['top_losers']
        
        message = f"""🌐 加密貨幣市場總覽

━━━━━━━━━━━━━━━━━━━━
📊 市場概況
• 總市值：{format_number(total_cap)} ({format_percentage(cap_change)})
• 24h成交量：{format_number(total_volume)}
• BTC主導率：{btc_dom:.1f}%
• ETH主導率：{eth_dom:.1f}%
"""
        
        # 恐懼貪婪指數
        if fng_data:
            fng_value = fng_data['value']
            fng_class = fng_data['classification']
            fng_emoji = get_fng_emoji(fng_value)
            
            # 進度條
            bar_length = 10
            filled = int(fng_value / 10)
            bar = '▓' * filled + '░' * (bar_length - filled)
            
            message += f"""
😱 恐懼貪婪指數
{bar} {fng_value}/100 - {fng_class} {fng_emoji}
"""
        
        # Top 5 幣種
        message += """
━━━━━━━━━━━━━━━━━━━━
🏆 Top 5 加密貨幣

"""
        
        for coin in top_coins:
            symbol = coin['symbol']
            price = coin['price']
            change = coin['price_change_24h']
            market_cap = coin['market_cap']
            rank = coin['rank']
            
            message += f"""{rank}. {symbol}  ${price:,.2f}  {format_percentage(change)}
   市值 {format_number(market_cap)}

"""
        
        # 漲幅榜
        if gainers:
            message += """━━━━━━━━━━━━━━━━━━━━
🔥 24小時漲幅榜
"""
            for idx, coin in enumerate(gainers, 1):
                symbol = coin['symbol']
                change = coin['change_24h']
                emoji = '🚀' if change > 20 else '📈'
                message += f"{idx}. {symbol}  {format_percentage(change)}\n"
        
        # 跌幅榜
        if losers:
            message += """
📉 24小時跌幅榜
"""
            for idx, coin in enumerate(losers, 1):
                symbol = coin['symbol']
                change = coin['change_24h']
                message += f"{idx}. {symbol}  {format_percentage(change)}\n"
        
        message += f"""
⏰ 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return message
    
    # ==================== /help 指令 ====================
    
    def handle_help(self) -> str:
        """顯示幫助訊息"""
        return """🤖 加密貨幣資訊 Bot 使用指南

📊 可用指令：

/price <幣種> - 查詢價格
   範例：/price BTC

/news [幣種] - 最新新聞
   範例：/news 或 /news BTC

/market - 市場總覽
   顯示市值、恐懼貪婪指數等

/help - 顯示此說明

━━━━━━━━━━━━━━━━━━━━
💡 提示：
• 支援主流幣種如 BTC, ETH, SOL 等
• 數據每分鐘更新
• 價格來源：CoinGecko
• 新聞來源：CryptoPanic, CoinDesk"""


# ==================== 按鈕處理 ====================

def get_price_keyboard(symbol: str) -> dict:
    """獲取價格查詢的 inline keyboard"""
    return {
        'inline_keyboard': [
            [
                {'text': '📊 查看圖表', 'url': f'https://www.tradingview.com/chart/?symbol={symbol}USD'},
                {'text': '📰 相關新聞', 'callback_data': f'news_{symbol}'}
            ],
            [
                {'text': '🔄 刷新', 'callback_data': f'price_{symbol}'}
            ]
        ]
    }


def get_news_keyboard() -> dict:
    """獲取新聞的 inline keyboard"""
    return {
        'inline_keyboard': [
            [
                {'text': '🔄 刷新', 'callback_data': 'news_refresh'},
                {'text': '📊 查看市場', 'callback_data': 'market'}
            ]
        ]
    }


def get_market_keyboard() -> dict:
    """獲取市場總覽的 inline keyboard"""
    return {
        'inline_keyboard': [
            [
                {'text': '🔄 刷新', 'callback_data': 'market'},
                {'text': '📰 市場新聞', 'callback_data': 'news_refresh'}
            ],
            [
                {'text': '📊 BTC', 'callback_data': 'price_BTC'},
                {'text': '📊 ETH', 'callback_data': 'price_ETH'},
                {'text': '📊 SOL', 'callback_data': 'price_SOL'}
            ]
        ]
    }
