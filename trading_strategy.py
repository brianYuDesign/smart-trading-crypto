"""
交易策略分析引擎
根據用戶風險等級提供個性化的進退場建議
"""
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from database_manager import db

logger = logging.getLogger(__name__)


class TradingStrategy:
    """交易策略分析類"""
    
    # 各風險等級的策略參數
    STRATEGY_PARAMS = {
        1: {  # 保守型
            'name': '保守型策略',
            'entry': {
                'rsi_range': (None, 40),           # RSI < 40 (超賣區)
                'volume_multiplier': 1.5,          # 成交量 > 1.5倍
                'price_trend': 'bullish',          # 必須上漲趨勢
                'ma_condition': 'ma50_above_ma200', # MA50 > MA200
                'news_sentiment_min': 0.6          # 正面新聞 > 60%
            },
            'exit': {
                'stop_loss': -8.0,                 # 止損 -8%
                'take_profit': 15.0,               # 止盈 +15%
                'rsi_overbought': 70,              # RSI > 70 退場
                'news_sentiment_min': 0.4          # 負面新聞退場
            }
        },
        2: {  # 穩健型
            'name': '穩健型策略',
            'entry': {
                'rsi_range': (30, 50),             # RSI 30-50
                'volume_multiplier': 1.3,          # 成交量 > 1.3倍
                'macd_condition': 'golden_cross',  # MACD 金叉
                'news_sentiment_min': 0.5          # 正面新聞 > 50%
            },
            'exit': {
                'stop_loss': -15.0,                # 止損 -15%
                'take_profit': 25.0,               # 止盈 +25%
                'rsi_overbought': 75,              # RSI > 75 退場
                'macd_condition': 'death_cross'    # MACD 死叉退場
            }
        },
        3: {  # 積極型
            'name': '積極型策略',
            'entry': {
                'rsi_range': (None, 30),           # RSI < 30 或突破
                'rsi_breakout': 60,                # 或 RSI > 60 突破
                'volume_multiplier': 2.0,          # 成交量暴增 > 2倍
                'price_breakout': True,            # 突破關鍵壓力
                'news_sentiment_min': 0.45         # 可接受較低情緒
            },
            'exit': {
                'stop_loss': -25.0,                # 止損 -25%
                'take_profit': 40.0,               # 止盈 +40%
                'rsi_overbought': 80,              # RSI > 80 退場
                'volume_decline': 0.5              # 成交量萎縮退場
            }
        }
    }
    
    def __init__(self):
        pass
    
    def analyze_entry_signal(self, user_id: int, symbol: str, 
                            market_data: Dict) -> Dict:
        """分析進場信號
        
        Args:
            user_id: 用戶ID
            symbol: 交易對
            market_data: {
                'price': float,
                'rsi': float,
                'volume_24h': float,
                'avg_volume': float,
                'ma_50': float,
                'ma_200': float,
                'macd': float,
                'macd_signal': float,
                'news_sentiment': float,
                'price_change_24h': float
            }
        
        Returns:
            {
                'should_enter': bool,
                'confidence': float (0-1),
                'reasons': List[str],
                'recommendation': str,
                'risk_level': int
            }
        """
        # 獲取用戶風險屬性
        profile = db.get_current_risk_profile(user_id)
        if not profile:
            return {
                'should_enter': False,
                'confidence': 0.0,
                'reasons': ['請先完成風險評估 (/risk_profile)'],
                'recommendation': '無法提供建議',
                'risk_level': None
            }
        
        risk_level = profile['risk_level']
        strategy = self.STRATEGY_PARAMS[risk_level]
        entry_params = strategy['entry']
        
        # 分析各項指標
        signals = []
        confidence_score = 0.0
        max_score = 0
        
        # 1. RSI 分析
        if 'rsi' in market_data and market_data['rsi'] is not None:
            rsi = market_data['rsi']
            rsi_min, rsi_max = entry_params.get('rsi_range', (None, None))
            
            if rsi_min and rsi_max:
                if rsi_min <= rsi <= rsi_max:
                    signals.append(f"✅ RSI {rsi:.1f} 在理想範圍 ({rsi_min}-{rsi_max})")
                    confidence_score += 20
            elif rsi_max and rsi < rsi_max:
                signals.append(f"✅ RSI {rsi:.1f} < {rsi_max} (超賣區)")
                confidence_score += 20
            elif 'rsi_breakout' in entry_params and rsi > entry_params['rsi_breakout']:
                signals.append(f"✅ RSI {rsi:.1f} 突破 {entry_params['rsi_breakout']}")
                confidence_score += 20
            else:
                signals.append(f"❌ RSI {rsi:.1f} 不符合條件")
            max_score += 20
        
        # 2. 成交量分析
        if 'volume_24h' in market_data and 'avg_volume' in market_data:
            volume_ratio = market_data['volume_24h'] / market_data['avg_volume']
            required_ratio = entry_params.get('volume_multiplier', 1.0)
            
            if volume_ratio >= required_ratio:
                signals.append(f"✅ 成交量放大 {volume_ratio:.1f}x (需求 {required_ratio}x)")
                confidence_score += 20
            else:
                signals.append(f"❌ 成交量 {volume_ratio:.1f}x 未達標準")
            max_score += 20
        
        # 3. 均線分析
        if entry_params.get('ma_condition') == 'ma50_above_ma200':
            if 'ma_50' in market_data and 'ma_200' in market_data:
                if market_data['ma_50'] > market_data['ma_200']:
                    signals.append("✅ MA50 > MA200 (上漲趨勢)")
                    confidence_score += 15
                else:
                    signals.append("❌ MA50 < MA200 (下跌趨勢)")
                max_score += 15
        
        # 4. MACD 分析
        if entry_params.get('macd_condition') == 'golden_cross':
            if 'macd' in market_data and 'macd_signal' in market_data:
                if market_data['macd'] > market_data['macd_signal']:
                    signals.append("✅ MACD 金叉 (買入信號)")
                    confidence_score += 15
                else:
                    signals.append("❌ MACD 未金叉")
                max_score += 15
        
        # 5. 新聞情緒分析
        if 'news_sentiment' in market_data and market_data['news_sentiment'] is not None:
            sentiment = market_data['news_sentiment']
            min_sentiment = entry_params.get('news_sentiment_min', 0.5)
            
            if sentiment >= min_sentiment:
                signals.append(f"✅ 新聞情緒正面 {sentiment*100:.0f}% (需求 {min_sentiment*100:.0f}%)")
                confidence_score += 15
            else:
                signals.append(f"⚠️ 新聞情緒 {sentiment*100:.0f}% 略低")
                confidence_score += 5
            max_score += 15
        
        # 6. 價格突破分析（積極型）
        if entry_params.get('price_breakout') and 'price_change_24h' in market_data:
            if market_data['price_change_24h'] > 5:
                signals.append(f"✅ 價格突破 +{market_data['price_change_24h']:.1f}%")
                confidence_score += 15
            max_score += 15
        
        # 計算最終信心度
        confidence = confidence_score / max_score if max_score > 0 else 0
        
        # 判斷是否進場
        should_enter = confidence >= 0.6  # 信心度 >= 60% 才建議進場
        
        # 生成建議
        if should_enter:
            recommendation = f"🟢 建議進場 ({strategy['name']})\n"
            recommendation += f"信心度: {confidence*100:.0f}%\n"
            recommendation += f"建議止損: {strategy['exit']['stop_loss']}%\n"
            recommendation += f"建議止盈: {strategy['exit']['take_profit']}%"
        else:
            recommendation = f"🔴 暫不建議進場\n"
            recommendation += f"信心度: {confidence*100:.0f}% (需達 60%)\n"
            recommendation += "建議等待更好時機"
        
        # 保存信號到資料庫
        db.save_trading_signal(
            user_id=user_id,
            symbol=symbol,
            signal_type='entry',
            risk_level=risk_level,
            price=market_data.get('price', 0),
            rsi=market_data.get('rsi'),
            volume_ratio=market_data.get('volume_24h', 0) / market_data.get('avg_volume', 1),
            news_sentiment=market_data.get('news_sentiment'),
            recommendation=recommendation,
            confidence=confidence
        )
        
        return {
            'should_enter': should_enter,
            'confidence': confidence,
            'reasons': signals,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'strategy_name': strategy['name']
        }
    
    def analyze_exit_signal(self, user_id: int, position_id: int,
                           current_price: float, market_data: Dict) -> Dict:
        """分析退場信號
        
        Args:
            user_id: 用戶ID
            position_id: 持倉ID
            current_price: 當前價格
            market_data: 市場數據
        
        Returns:
            {
                'should_exit': bool,
                'exit_type': 'stop_loss'|'take_profit'|'signal',
                'confidence': float,
                'reasons': List[str],
                'recommendation': str
            }
        """
        # 獲取持倉資料
        positions = db.get_open_positions(user_id)
        position = next((p for p in positions if p['position_id'] == position_id), None)
        
        if not position:
            return {
                'should_exit': False,
                'exit_type': None,
                'confidence': 0.0,
                'reasons': ['持倉不存在'],
                'recommendation': '無法分析'
            }
        
        # 獲取風險屬性
        profile = db.get_current_risk_profile(user_id)
        if not profile:
            return {
                'should_exit': False,
                'exit_type': None,
                'confidence': 0.0,
                'reasons': ['無風險屬性'],
                'recommendation': '無法分析'
            }
        
        risk_level = profile['risk_level']
        strategy = self.STRATEGY_PARAMS[risk_level]
        exit_params = strategy['exit']
        
        # 計算當前損益
        entry_price = position['entry_price']
        profit_loss_percent = ((current_price - entry_price) / entry_price) * 100
        
        signals = []
        should_exit = False
        exit_type = None
        confidence = 0.0
        
        # 1. 止損檢查
        if profit_loss_percent <= exit_params['stop_loss']:
            signals.append(f"🛑 觸及止損線 {profit_loss_percent:.1f}% <= {exit_params['stop_loss']}%")
            should_exit = True
            exit_type = 'stop_loss'
            confidence = 1.0
        
        # 2. 止盈檢查
        elif profit_loss_percent >= exit_params['take_profit']:
            signals.append(f"✅ 達到止盈目標 {profit_loss_percent:.1f}% >= {exit_params['take_profit']}%")
            should_exit = True
            exit_type = 'take_profit'
            confidence = 1.0
        
        # 3. 技術指標退場信號
        else:
            signal_count = 0
            total_signals = 0
            
            # RSI 超買
            if 'rsi' in market_data and market_data['rsi'] is not None:
                rsi = market_data['rsi']
                overbought = exit_params['rsi_overbought']
                
                if rsi > overbought:
                    signals.append(f"⚠️ RSI {rsi:.1f} > {overbought} (超買)")
                    signal_count += 1
                total_signals += 1
            
            # MACD 死叉
            if exit_params.get('macd_condition') == 'death_cross':
                if 'macd' in market_data and 'macd_signal' in market_data:
                    if market_data['macd'] < market_data['macd_signal']:
                        signals.append("⚠️ MACD 死叉 (賣出信號)")
                        signal_count += 1
                    total_signals += 1
            
            # 成交量萎縮
            if 'volume_decline' in exit_params:
                if 'volume_24h' in market_data and 'avg_volume' in market_data:
                    volume_ratio = market_data['volume_24h'] / market_data['avg_volume']
                    if volume_ratio < exit_params['volume_decline']:
                        signals.append(f"⚠️ 成交量萎縮 {volume_ratio:.1f}x")
                        signal_count += 1
                    total_signals += 1
            
            # 新聞情緒轉負
            if 'news_sentiment' in market_data and market_data['news_sentiment'] is not None:
                sentiment = market_data['news_sentiment']
                min_sentiment = exit_params.get('news_sentiment_min', 0.4)
                
                if sentiment < min_sentiment:
                    signals.append(f"⚠️ 新聞情緒轉負 {sentiment*100:.0f}%")
                    signal_count += 1
                total_signals += 1
            
            # 如果多個退場信號，建議退場
            if total_signals > 0:
                confidence = signal_count / total_signals
                if confidence >= 0.5:  # 超過一半指標建議退場
                    should_exit = True
                    exit_type = 'signal'
        
        # 生成建議
        if should_exit:
            if exit_type == 'stop_loss':
                recommendation = f"🛑 強烈建議止損退場\n"
                recommendation += f"當前虧損: {profit_loss_percent:.1f}%\n"
                recommendation += "保護資本為首要目標"
            elif exit_type == 'take_profit':
                recommendation = f"✅ 建議止盈退場\n"
                recommendation += f"當前獲利: {profit_loss_percent:.1f}%\n"
                recommendation += "鎖定利潤，見好就收"
            else:
                recommendation = f"⚠️ 建議退場觀望\n"
                recommendation += f"當前損益: {profit_loss_percent:+.1f}%\n"
                recommendation += f"退場信號: {len(signals)} 個"
        else:
            recommendation = f"✅ 可繼續持有\n"
            recommendation += f"當前損益: {profit_loss_percent:+.1f}%\n"
            recommendation += f"止損線: {exit_params['stop_loss']}%\n"
            recommendation += f"止盈線: {exit_params['take_profit']}%"
        
        # 保存信號到資料庫
        db.save_trading_signal(
            user_id=user_id,
            symbol=position['symbol'],
            signal_type='exit',
            risk_level=risk_level,
            price=current_price,
            rsi=market_data.get('rsi'),
            volume_ratio=market_data.get('volume_24h', 0) / market_data.get('avg_volume', 1),
            news_sentiment=market_data.get('news_sentiment'),
            recommendation=recommendation,
            confidence=confidence
        )
        
        return {
            'should_exit': should_exit,
            'exit_type': exit_type,
            'confidence': confidence,
            'reasons': signals,
            'recommendation': recommendation,
            'current_pl': profit_loss_percent
        }
    
    def get_strategy_summary(self, risk_level: int) -> str:
        """獲取策略摘要"""
        if risk_level not in self.STRATEGY_PARAMS:
            return "風險等級錯誤"
        
        strategy = self.STRATEGY_PARAMS[risk_level]
        entry = strategy['entry']
        exit_params = strategy['exit']
        
        text = f"📊 {strategy['name']}\n\n"
        text += "🟢 進場條件:\n"
        
        if 'rsi_range' in entry and entry['rsi_range'][0]:
            text += f"  • RSI: {entry['rsi_range'][0]}-{entry['rsi_range'][1]}\n"
        elif 'rsi_range' in entry:
            text += f"  • RSI < {entry['rsi_range'][1]}\n"
        
        if 'volume_multiplier' in entry:
            text += f"  • 成交量 > {entry['volume_multiplier']}x 平均\n"
        
        if 'news_sentiment_min' in entry:
            text += f"  • 新聞情緒 > {entry['news_sentiment_min']*100:.0f}%\n"
        
        text += f"\n🔴 退場條件:\n"
        text += f"  • 止損: {exit_params['stop_loss']}%\n"
        text += f"  • 止盈: {exit_params['take_profit']}%\n"
        text += f"  • RSI > {exit_params['rsi_overbought']}\n"
        
        return text


# 全局交易策略實例
trading_strategy = TradingStrategy()
