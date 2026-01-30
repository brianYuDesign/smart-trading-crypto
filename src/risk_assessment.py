"""
風險評估問卷模組
提供互動式風險屬性評估功能
"""
import logging
from typing import Dict, List, Tuple, Optional
from .database import db

logger = logging.getLogger(__name__)


class RiskAssessment:
    """風險評估問卷類"""
    
    # 問卷題目定義
    QUESTIONS = [
        {
            'number': 1,
            'question': '您的加密貨幣投資經驗？',
            'options': {
                'A': {'text': '沒有或 < 6個月', 'score': 1},
                'B': {'text': '6個月 - 2年', 'score': 2},
                'C': {'text': '> 2年', 'score': 3}
            }
        },
        {
            'number': 2,
            'question': '您能承受的最大虧損？',
            'options': {
                'A': {'text': '5-10%', 'score': 1},
                'B': {'text': '10-20%', 'score': 2},
                'C': {'text': '> 20%', 'score': 3}
            }
        },
        {
            'number': 3,
            'question': '您的投資目標？',
            'options': {
                'A': {'text': '保本，追求穩定收益', 'score': 1},
                'B': {'text': '平衡風險與收益', 'score': 2},
                'C': {'text': '追求高報酬，可承擔高風險', 'score': 3}
            }
        },
        {
            'number': 4,
            'question': '如果投資虧損 15%，您會？',
            'options': {
                'A': {'text': '立即賣出止損', 'score': 1},
                'B': {'text': '觀察一段時間再決定', 'score': 2},
                'C': {'text': '加碼攤平成本', 'score': 3}
            }
        },
        {
            'number': 5,
            'question': '您的投資時間規劃？',
            'options': {
                'A': {'text': '長期持有 (> 1年)', 'score': 1},
                'B': {'text': '中期波段 (3-12個月)', 'score': 2},
                'C': {'text': '短線交易 (< 3個月)', 'score': 3}
            }
        },
        {
            'number': 6,
            'question': '您每月可用於加密貨幣的資金比例？',
            'options': {
                'A': {'text': '< 10% 存款', 'score': 1},
                'B': {'text': '10-30% 存款', 'score': 2},
                'C': {'text': '> 30% 存款', 'score': 3}
            }
        },
        {
            'number': 7,
            'question': '市場大跌 30% 時，您的反應？',
            'options': {
                'A': {'text': '恐慌賣出', 'score': 1},
                'B': {'text': '保持冷靜，觀察', 'score': 2},
                'C': {'text': '認為是買入機會', 'score': 3}
            }
        },
        {
            'number': 8,
            'question': '您對技術分析的熟悉度？',
            'options': {
                'A': {'text': '不熟悉', 'score': 1},
                'B': {'text': '了解基本指標', 'score': 2},
                'C': {'text': '精通並常使用', 'score': 3}
            }
        },
        {
            'number': 9,
            'question': '您希望多久檢查一次投資組合？',
            'options': {
                'A': {'text': '每週或更少', 'score': 1},
                'B': {'text': '每天', 'score': 2},
                'C': {'text': '多次/每天', 'score': 3}
            }
        },
        {
            'number': 10,
            'question': '您是否有其他投資經驗（股票、基金等）？',
            'options': {
                'A': {'text': '沒有', 'score': 1},
                'B': {'text': '有一些', 'score': 2},
                'C': {'text': '豐富', 'score': 3}
            }
        }
    ]
    
    # 風險等級描述
    RISK_LEVELS = {
        1: {
            'name': '保守型 (Conservative)',
            'description': '您偏好低風險投資，適合穩健的長期持有策略',
            'max_loss': 10.0,
            'target_return': 15.0,
            'notification_freq': 'daily',
            'characteristics': [
                '投資經驗較少',
                '風險承受度低（最大虧損容忍 5-10%）',
                '投資目標：保本為主',
                '交易頻率：低（長期持有）'
            ]
        },
        2: {
            'name': '穩健型 (Moderate)',
            'description': '您能接受中等風險，適合波段操作策略',
            'max_loss': 20.0,
            'target_return': 25.0,
            'notification_freq': 'twice',
            'characteristics': [
                '投資經驗中等',
                '風險承受度中等（最大虧損容忍 10-20%）',
                '投資目標：穩定收益 + 適度增值',
                '交易頻率：中等（波段操作）'
            ]
        },
        3: {
            'name': '積極型 (Aggressive)',
            'description': '您能承受較高風險，適合積極的短線交易策略',
            'max_loss': 30.0,
            'target_return': 40.0,
            'notification_freq': 'realtime',
            'characteristics': [
                '投資經驗豐富',
                '風險承受度高（最大虧損容忍 20-30%）',
                '投資目標：追求高報酬',
                '交易頻率：高（短線交易）'
            ]
        }
    }
    
    def __init__(self):
        self.user_sessions = {}  # {user_id: {'current_question': int, 'answers': []}}
    
    def start_assessment(self, user_id: int) -> str:
        """開始風險評估"""
        self.user_sessions[user_id] = {
            'current_question': 1,
            'answers': []
        }
        
        return self.get_question_text(1)
    
    def get_question_text(self, question_number: int) -> str:
        """獲取問題文本（含選項）"""
        if question_number < 1 or question_number > len(self.QUESTIONS):
            return "問題編號錯誤"
        
        q = self.QUESTIONS[question_number - 1]
        text = f"📊 風險評估問卷 ({question_number}/10)\n\n"
        text += f"❓ {q['question']}\n\n"
        
        for option, data in q['options'].items():
            text += f"{option}. {data['text']}\n"
        
        text += f"\n請回覆選項字母 (A/B/C)"
        
        return text
    
    def process_answer(self, user_id: int, answer: str) -> Dict:
        """處理用戶答案
        
        Returns:
            {
                'status': 'continue'|'completed'|'error',
                'message': str,
                'result': Optional[Dict]  # 僅在 completed 時有值
            }
        """
        if user_id not in self.user_sessions:
            return {
                'status': 'error',
                'message': '請先使用 /risk_profile 開始評估',
                'result': None
            }
        
        session = self.user_sessions[user_id]
        current_q = session['current_question']
        
        # 驗證答案
        answer = answer.upper().strip()
        if answer not in ['A', 'B', 'C']:
            return {
                'status': 'error',
                'message': '請輸入有效選項 (A/B/C)',
                'result': None
            }
        
        # 記錄答案
        q = self.QUESTIONS[current_q - 1]
        score = q['options'][answer]['score']
        session['answers'].append((current_q, answer, score))
        
        # 檢查是否完成
        if current_q >= 10:
            # 計算結果
            result = self.calculate_result(user_id)
            del self.user_sessions[user_id]  # 清除session
            
            return {
                'status': 'completed',
                'message': self.format_result(result),
                'result': result
            }
        else:
            # 繼續下一題
            session['current_question'] += 1
            next_question = self.get_question_text(session['current_question'])
            
            return {
                'status': 'continue',
                'message': next_question,
                'result': None
            }
    
    def calculate_result(self, user_id: int) -> Dict:
        """計算評估結果"""
        session = self.user_sessions[user_id]
        answers = session['answers']
        
        total_score = sum(score for _, _, score in answers)
        
        # 確定風險等級
        if total_score <= 16:
            risk_level = 1
        elif total_score <= 23:
            risk_level = 2
        else:
            risk_level = 3
        
        # 保存到資料庫
        profile_id = db.save_risk_profile(user_id, total_score, answers)
        
        result = {
            'profile_id': profile_id,
            'total_score': total_score,
            'risk_level': risk_level,
            'level_info': self.RISK_LEVELS[risk_level]
        }
        
        return result
    
    def format_result(self, result: Dict) -> str:
        """格式化評估結果"""
        level_info = result['level_info']
        
        text = "🎯 風險評估結果\n"
        text += "=" * 40 + "\n\n"
        text += f"📊 總分：{result['total_score']}/30\n"
        text += f"🏷️ 風險等級：{level_info['name']}\n\n"
        text += f"📝 評估描述：\n{level_info['description']}\n\n"
        text += "✨ 您的特徵：\n"
        
        for char in level_info['characteristics']:
            text += f"  • {char}\n"
        
        text += f"\n⚠️ 建議止損：{level_info['max_loss']}%\n"
        text += f"🎯 目標獲利：{level_info['target_return']}%\n"
        text += f"🔔 通知頻率：{level_info['notification_freq']}\n\n"
        text += "💡 您可以隨時使用 /risk_profile 重新評估"
        
        return text
    
    def get_user_risk_summary(self, user_id: int) -> Optional[str]:
        """獲取用戶當前風險屬性摘要"""
        profile = db.get_current_risk_profile(user_id)
        
        if not profile:
            return None
        
        risk_level = profile['risk_level']
        level_info = self.RISK_LEVELS[risk_level]
        
        text = f"📊 您的風險屬性\n\n"
        text += f"🏷️ 等級：{level_info['name']}\n"
        text += f"📈 總分：{profile['risk_score']}/30\n"
        text += f"⚠️ 止損：{level_info['max_loss']}%\n"
        text += f"🎯 止盈：{level_info['target_return']}%\n"
        text += f"🔔 通知：{level_info['notification_freq']}\n"
        
        return text
    
    def cancel_assessment(self, user_id: int) -> bool:
        """取消評估"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            return True
        return False

    def is_in_assessment(self, user_id: int) -> bool:
        """檢查用戶是否正在進行評估"""
        return user_id in self.user_sessions


# 全局風險評估實例
risk_assessment = RiskAssessment()
