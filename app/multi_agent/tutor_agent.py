# -*- coding: utf-8 -*-
"""
智能辅导智能体
提供多模态答疑解惑服务
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from . import StudentProfile, ContentSafetyFilter, HallucinationDetector
from .llm_client import get_llm_client


class TutorAgent:
    """智能辅导智能体"""
    
    SYSTEM_PROMPT = """你是一位耐心、专业的AI学习导师，为学生提供全方位的学习辅导。

## 你的特点
1. 专业知识扎实，能够准确解答各类学科问题
2. 表达清晰易懂，善于用比喻和实例解释抽象概念
3. 启发式引导，鼓励学生独立思考
4. 态度温和友善，营造轻松的学习氛围
5. 注重方法传授，而不仅仅是答案

## 解答原则
1. **精准理解**：首先准确理解学生的问题
2. **分解问题**：复杂问题分解为简单步骤
3. **多角度解释**：提供不同层次的解释
4. **实例支撑**：配合具体例子帮助理解
5. **引导思考**：适当提问引导学生自主思考
6. **知识延伸**：提供相关知识点的链接

## 解答格式
对于知识问题：
```
## 问题理解
[准确复述问题，确认理解正确]

## 解答
[详细解答，配合示例]

## 知识延伸
[相关知识点]

## 思考题
[巩固理解的小练习]
```

对于代码问题：
```
## 问题分析
[分析问题所在]

## 解决方案
[完整代码]

## 代码解析
[逐行/分步解释]

## 注意事项
[常见错误和最佳实践]

## 练习
[类似的练习题]
```

## 多模态支持
你还可以提供：
- 文字解答
- 图解说明（用ASCII或描述）
- 视频讲解要点
- 代码演示

## 禁忌事项
1. 不直接给出完整答案（引导思考）
2. 不嘲笑或贬低学生
3. 不传播错误信息
4. 不涉及敏感话题"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.conversation_context: List[Dict] = []
    
    def answer_question(
        self,
        question: str,
        profile: StudentProfile,
        context: Dict = None
    ) -> Dict[str, Any]:
        """回答学生问题"""
        
        # 内容安全检查
        is_safe, reason = ContentSafetyFilter.filter(question)
        if not is_safe:
            return {
                'answer': f"抱歉，{reason}，请换个问题。",
                'type': 'text',
                'related_questions': [],
                'suggestions': []
            }
        
        # 构建提示
        prompt = self._build_prompt(question, profile, context)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "assistant", "content": "你好！有什么学习问题可以问我？"},
            *self.conversation_context,
            {"role": "user", "content": prompt}
        ]
        
        try:
            answer = self.llm.chat(messages, temperature=0.7)
        except Exception as e:
            answer = self._get_fallback_answer(question)
        
        # 幻觉检测
        is_factual, warnings = HallucinationDetector.check_factuality(answer)
        if not is_factual:
            answer += f"\n\n> ⚠️ 注意：{warnings[0]}"
        
        # 生成相关问题和建议
        related_questions = self._generate_related_questions(question, answer)
        suggestions = self._generate_suggestions(question, profile)
        
        return {
            'answer': answer,
            'type': self._detect_answer_type(question),
            'related_questions': related_questions,
            'suggestions': suggestions,
            'multimodal_hints': self._get_multimodal_hints(answer)
        }
    
    def stream_answer(
        self,
        question: str,
        profile: StudentProfile,
        context: Dict = None
    ):
        """流式回答学生问题"""
        
        # 内容安全检查
        is_safe, reason = ContentSafetyFilter.filter(question)
        if not is_safe:
            yield f"抱歉，{reason}，请换个问题。"
            return
        
        # 构建提示
        prompt = self._build_prompt(question, profile, context)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation_context,
            {"role": "user", "content": prompt}
        ]
        
        try:
            for chunk in self.llm.stream_chat(messages, temperature=0.7):
                yield chunk
        except Exception as e:
            yield from self._get_fallback_stream_answer(question)
    
    def _build_prompt(self, question: str, profile: StudentProfile, context: Dict = None) -> str:
        """构建提示"""
        
        prompt_parts = [
            f"## 学生信息",
            f"- 用户：{profile.username}",
            f"- 认知风格：{profile.cognitive_style}",
            f"- 学习速度：{profile.learning_speed}",
            f"- 当前学习主题：{', '.join(profile.preferred_topics[:3]) if profile.preferred_topics else '通用'}",
            f"- 薄弱环节：{', '.join(profile.weak_topics[:3]) if profile.weak_topics else '待评估'}",
            f"",
            f"## 当前问题",
            question,
            f"",
            f"## 附加上下文",
            json.dumps(context or {}, ensure_ascii=False) if context else "无"
        ]
        
        return "\n".join(prompt_parts)
    
    def _detect_answer_type(self, question: str) -> str:
        """检测答案类型"""
        question_lower = question.lower()
        
        if '代码' in question or '编程' in question or 'python' in question_lower:
            return 'code'
        elif '比较' in question or '区别' in question or 'vs' in question_lower:
            return 'comparison'
        elif '为什么' in question or '原理' in question or '原因' in question:
            return 'explanation'
        elif '如何' in question or '怎样' in question or '怎么' in question:
            return 'guide'
        elif any(kw in question for kw in ['计算', '求解', '证明', '推导']):
            return 'calculation'
        else:
            return 'general'
    
    def _generate_related_questions(self, question: str, answer: str) -> List[str]:
        """生成相关问题"""
        
        # 基于关键词提取相关问题
        related = []
        
        # 提取知识点关键词
        patterns = [
            r'关于(.+?)的',
            r'(.+?)的原理',
            r'如何(.+?)',
            r'(.+?)和(.+?)的区别'
        ]
        
        keywords = []
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                keywords.extend([g for g in match.groups() if g])
        
        # 生成相关问题
        base_questions = [
            "相关知识点有哪些？",
            "如何巩固这部分内容？",
            "有什么练习推荐吗？"
        ]
        
        for kw in keywords[:2]:
            base_questions.insert(0, f"{kw}的常见题型有哪些？")
        
        return base_questions[:4]
    
    def _generate_suggestions(self, question: str, profile: StudentProfile) -> List[str]:
        """生成学习建议"""
        
        suggestions = []
        
        # 基于认知风格
        if profile.cognitive_style == 'visual':
            suggestions.append("建议结合图表和思维导图学习")
        elif profile.cognitive_style == 'verbal':
            suggestions.append("建议多做笔记和复述练习")
        elif profile.cognitive_style == 'auditory':
            suggestions.append("建议配合音频讲解学习")
        
        # 基于薄弱环节
        if profile.weak_topics:
            suggestions.append("建议回顾相关基础知识点")
        
        # 基于问题类型
        if '为什么' in question:
            suggestions.append("理解原理后，尝试自己推导一遍")
        elif '如何' in question:
            suggestions.append("动手实践是最好的学习方式")
        
        return suggestions[:3]
    
    def _get_multimodal_hints(self, answer: str) -> Dict[str, Any]:
        """获取多模态提示"""
        
        hints = {
            'has_diagram': False,
            'has_code': False,
            'has_video_script': False,
            'diagram_description': None,
            'video_outline': None
        }
        
        # 检测是否包含代码
        if '```' in answer or 'def ' in answer or 'function' in answer.lower():
            hints['has_code'] = True
        
        # 检测是否需要图解
        if any(kw in answer for kw in ['流程', '结构', '关系', '对比', '组成']):
            hints['has_diagram'] = True
            hints['diagram_description'] = "建议生成流程图/结构图辅助理解"
        
        # 视频脚本提示
        if len(answer) > 500:
            hints['has_video_script'] = True
            hints['video_outline'] = {
                '时长': '3-5分钟',
                '结构': ['开场引入', '核心讲解', '案例演示', '总结回顾']
            }
        
        return hints
    
    def explain_with_examples(
        self,
        concept: str,
        profile: StudentProfile
    ) -> Dict[str, Any]:
        """详细讲解概念，配以多个例子"""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""请详细解释"{concept}"这个概念，要求：

1. 清晰定义概念
2. 提供2-3个由浅入深的例子
3. 用学生能理解的方式解释
4. 指出常见的理解误区
5. 给出实践建议

学生信息：
- 认知风格：{profile.cognitive_style}
- 学习速度：{profile.learning_speed}"""}
        ]
        
        try:
            explanation = self.llm.chat(messages, temperature=0.7)
        except Exception as e:
            explanation = self._get_fallback_explanation(concept)
        
        return {
            'concept': concept,
            'explanation': explanation,
            'examples': self._extract_examples(explanation)
        }
    
    def _extract_examples(self, text: str) -> List[str]:
        """从文本中提取例子"""
        
        examples = []
        
        # 提取编号列表中的内容
        import re
        numbered_items = re.findall(r'\d+[.、](.+?)(?=\n\d|\Z)', text, re.DOTALL)
        
        for item in numbered_items[:3]:
            if len(item) > 20:  # 过滤太短的
                examples.append(item.strip()[:100])
        
        return examples
    
    def create_practice_for_doubt(
        self,
        question: str,
        wrong_answer: str,
        profile: StudentProfile
    ) -> Dict[str, Any]:
        """针对学生的疑问创建练习"""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""针对学生的问题"{question}"和错误回答"{wrong_answer}"，
请设计3道针对性的练习题，帮助学生巩固理解。

要求：
1. 第一题：基础巩固
2. 第二题：变式应用
3. 第三题：综合提升

每道题包含：题目、答案、解析"""}
        ]
        
        try:
            practice = self.llm.chat(messages, temperature=0.7)
        except Exception as e:
            practice = "练习生成中..."
        
        return {
            'original_question': question,
            'common_mistake': wrong_answer,
            'practice_questions': practice,
            'tips': [
                "先理解概念再做题",
                "注意题目的变式",
                "总结解题思路"
            ]
        }
    
    def _get_fallback_answer(self, question: str) -> str:
        """获取降级回答"""
        return f"""感谢你的提问！关于「{question[:50]}...」

让我来分析一下这个问题：

## 问题理解
你的问题涉及到学习过程中的重要知识点。

## 解答方向
1. 首先需要理解基本概念
2. 其次要掌握核心原理
3. 最后通过练习巩固

## 建议
- 结合教材和课堂内容复习
- 做好笔记，整理重点
- 有疑问及时向老师请教

如果你能提供更多细节，我可以给出更具体的解答！"""
    
    def _get_fallback_explanation(self, concept: str) -> str:
        """获取降级解释"""
        return f"""{concept}是一个重要的学习知识点。

## 基本概念
（本部分内容正在生成中...）

## 示例
1. 第一个例子
2. 第二个例子

## 常见误区
- 误区一
- 误区二

## 学习建议
建议结合教材和练习深入理解。"""
    
    def _get_fallback_stream_answer(self, question: str):
        """获取降级流式回答"""
        response = self._get_fallback_answer(question)
        for char in response:
            yield char
