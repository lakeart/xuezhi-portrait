# -*- coding: utf-8 -*-
"""
学习画像构建智能体
通过自然语言对话自动抽取特征，构建学生画像
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from . import StudentProfile, AgentRole, ContentSafetyFilter
from .llm_client import get_llm_client


class ProfileBuilderAgent:
    """学习画像构建智能体"""
    
    SYSTEM_PROMPT = """你是一个专业的教育顾问智能体，专门负责通过对话了解学生的学习情况、目标和偏好，构建个性化学习画像。

## 你的任务
1. 通过自然、友好的对话了解学生
2. 从对话中提取关键信息构建画像
3. 画像需包含以下维度（至少6个）：
   - 知识基础：学生已有的知识储备
   - 认知风格：视觉型/语言型/听觉型/动手型
   - 易错点偏好：学生常犯的错误类型
   - 学习速度：快/中/慢
   - 兴趣方向：学生感兴趣的领域
   - 学习目标：学生想要达成的目标
   - 偏好知识点：学生喜欢学习的章节
   - 薄弱知识点：学生需要加强的部分
   - 学习习惯：学生的学习时间和方式偏好
   - 可用时间：学生每周可用于学习的时间

## 画像构建原则
- 使用苏格拉底式提问，引导学生自我探索
- 每次对话后更新和完善画像
- 保持对话自然流畅，像朋友聊天
- 遇到不确定信息时，做出合理推断并标注置信度
- 画像要动态更新，随学随新

## 输出格式
每次对话后，输出：
1. 对学生的理解和建议
2. 更新的画像信息（JSON格式）
3. 下一轮对话建议的问题"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.conversation_history: List[Dict] = []
        self.profile: Optional[StudentProfile] = None
        self.extracted_info: Dict[str, Any] = {}
    
    def init_profile(self, user_id: int, username: str) -> StudentProfile:
        """初始化空画像"""
        self.profile = StudentProfile(
            user_id=user_id,
            username=username,
            created_at=datetime.now().isoformat()
        )
        self.conversation_history = []
        self.extracted_info = {}
        return self.profile
    
    def load_profile(self, profile_data: Dict) -> StudentProfile:
        """加载已有画像"""
        self.profile = StudentProfile(**profile_data)
        return self.profile
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """处理用户消息，返回响应和更新的画像"""
        
        # 内容安全检查
        is_safe, reason = ContentSafetyFilter.filter(user_message)
        if not is_safe:
            return {
                "response": f"抱歉，{reason}，请换个话题。",
                "profile_update": None,
                "suggested_questions": []
            }
        
        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # 构建提示
        context = self._build_context()
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "assistant", "content": self._get_greeting()},
            *self.conversation_history[:-1],
            {"role": "assistant", "content": context},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.8)
        except Exception as e:
            response = self._get_fallback_response(user_message)
        
        # 提取画像更新
        profile_update = self._extract_profile_update(response)
        
        # 生成下一轮建议问题
        suggested_questions = self._generate_suggested_questions()
        
        # 添加助手响应到历史
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "response": response,
            "profile_update": profile_update,
            "suggested_questions": suggested_questions,
            "profile": self.profile.to_dict() if self.profile else None
        }
    
    def _build_context(self) -> str:
        """构建上下文信息"""
        context_parts = []
        
        if self.profile:
            context_parts.append(f"当前学生：{self.profile.username}")
            context_parts.append(f"已知信息：{json.dumps(self.extracted_info, ensure_ascii=False)}")
        
        context_parts.append("请基于以上信息继续对话，并在回复末尾以JSON格式输出更新的画像信息。")
        
        return "\n".join(context_parts)
    
    def _extract_profile_update(self, response: str) -> Dict[str, Any]:
        """从响应中提取并更新画像"""
        if not self.profile:
            return {}
        
        # 尝试提取JSON画像更新
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                update = json.loads(json_match.group())
                for key, value in update.items():
                    if hasattr(self.profile, key):
                        setattr(self.profile, key, value)
                        self.extracted_info[key] = value
            except json.JSONDecodeError:
                pass
        
        # 更新置信度
        self.profile.confidence = min(1.0, len(self.extracted_info) / 10)
        self.profile.updated_at = datetime.now().isoformat()
        
        # 关键词提取
        self._extract_keywords(response)
        
        return self.extracted_info
    
    def _extract_keywords(self, text: str) -> None:
        """从文本中提取关键词更新画像"""
        
        # 认知风格关键词
        style_keywords = {
            'visual': ['看', '图', '画', '视觉', '颜色', '图表'],
            'verbal': ['读', '写', '说', '文字', '讲解', '背诵'],
            'auditory': ['听', '声音', '音频', '讨论', '对话'],
            'kinesthetic': ['做', '动手', '实践', '实验', '操作']
        }
        
        for style, keywords in style_keywords.items():
            if any(kw in text for kw in keywords):
                self.profile.cognitive_style = style
                break
        
        # 学习速度关键词
        if any(kw in text for kw in ['快', '迅速', '一下子', '很快']):
            self.profile.learning_speed = 'fast'
        elif any(kw in text for kw in ['慢', '需要时间', '慢慢', '反复']):
            self.profile.learning_speed = 'slow'
        else:
            self.profile.learning_speed = 'medium'
    
    def _generate_suggested_questions(self) -> List[str]:
        """生成建议问题列表"""
        suggested = []
        
        # 根据已收集的信息生成问题
        if not self.extracted_info.get('goals'):
            suggested.append("你希望通过学习达成什么目标？")
        if not self.extracted_info.get('interests'):
            suggested.append("你对哪些领域最感兴趣？")
        if not self.extracted_info.get('weak_topics'):
            suggested.append("你觉得哪些知识点比较困难？")
        if not self.extracted_info.get('available_time'):
            suggested.append("你每周大概有多少时间用于学习？")
        
        # 默认问题
        default_questions = [
            "你目前在学习哪门课程？",
            "你更偏好什么样的学习方式？",
            "有没有特别想攻克的知识难点？"
        ]
        
        return suggested[:3] if len(suggested) >= 3 else suggested + default_questions[:3-len(suggested)]
    
    def _get_greeting(self) -> str:
        """获取初始问候"""
        if self.profile and self.profile.confidence > 0.5:
            return f"你好 {self.profile.username}！很高兴再次见到你。让我们继续完善你的学习画像吧。"
        return """你好！我是你的学习画像构建助手。通过和你的交流，我可以更好地了解你的学习需求，为你生成个性化的学习资源。

你可以告诉我：
- 你的专业或年级
- 你想学习的课程或知识点
- 你的学习目标是什么
- 你平时学习时间和习惯

我们开始吧！"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        """获取降级响应"""
        return f"""感谢你的分享！{user_message[:50]}...

我正在认真记录你的学习情况。基于我们的对话，我可以了解到你正在关注某些学习内容。

为了更好地为你定制学习方案，我想再了解几个问题：
1. 你的专业背景是什么？
2. 你目前最大的学习挑战是什么？
3. 你希望多久能掌握这些知识？

期待你分享更多信息！"""
    
    def build_profile_from_data(self, user_data: Dict) -> StudentProfile:
        """基于已有数据快速构建画像"""
        if not self.profile:
            return self.profile
        
        # 从用户数据中提取信息
        if 'major' in user_data:
            self.extracted_info['major'] = user_data['major']
        
        if 'grade' in user_data:
            self.extracted_info['grade'] = user_data['grade']
        
        if 'interests' in user_data:
            self.profile.interests = user_data['interests']
        
        if 'goals' in user_data:
            self.profile.goals = user_data['goals']
        
        # 基于答题数据推断知识基础
        if 'quiz_history' in user_data:
            self._infer_knowledge_base(user_data['quiz_history'])
        
        # 基于历史表现推断学习习惯
        if 'study_patterns' in user_data:
            self._infer_study_habits(user_data['study_patterns'])
        
        self.profile.confidence = 0.7
        self.profile.updated_at = datetime.now().isoformat()
        
        return self.profile
    
    def _infer_knowledge_base(self, quiz_history: List[Dict]) -> None:
        """从答题历史推断知识基础"""
        topic_scores = {}
        
        for quiz in quiz_history:
            topic = quiz.get('topic', 'unknown')
            score = quiz.get('score', 0)
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(score)
        
        # 计算平均掌握度
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            self.profile.knowledge_base[topic] = avg_score / 100
            
            if avg_score < 60:
                self.profile.weak_topics.append(topic)
            elif avg_score > 80:
                self.profile.strong_topics.append(topic)
    
    def _infer_study_habits(self, patterns: Dict) -> None:
        """从学习模式推断学习习惯"""
        if 'best_time' in patterns:
            self.profile.study_habits['best_time'] = patterns['best_time']
        
        if 'preferred_duration' in patterns:
            self.profile.study_habits['session_duration'] = patterns['preferred_duration']
        
        if 'frequency' in patterns:
            self.profile.study_habits['frequency'] = patterns['frequency']
