# -*- coding: utf-8 -*-
"""
学习效果评估智能体
多维度、精准评估学生学习效果
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from . import StudentProfile
from .llm_client import get_llm_client


@dataclass
class LearningMetrics:
    """学习指标"""
    knowledge_mastery: float = 0.0      # 知识掌握度
    learning_efficiency: float = 0.0     # 学习效率
    practice_accuracy: float = 0.0      # 练习准确率
    concept_understanding: float = 0.0  # 概念理解度
    problem_solving: float = 0.0         # 问题解决能力
    time_management: float = 0.0         # 时间管理
    consistency: float = 0.0            # 学习持续性
    engagement: float = 0.0              # 学习投入度


@dataclass
class AssessmentReport:
    """评估报告"""
    student_id: int
    assessment_date: str
    overall_score: float
    level: str  # excellent/good/fair/poor
    metrics: LearningMetrics
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    trends: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'student_id': self.student_id,
            'assessment_date': self.assessment_date,
            'overall_score': self.overall_score,
            'level': self.level,
            'metrics': {
                'knowledge_mastery': self.metrics.knowledge_mastery,
                'learning_efficiency': self.metrics.learning_efficiency,
                'practice_accuracy': self.metrics.practice_accuracy,
                'concept_understanding': self.metrics.concept_understanding,
                'problem_solving': self.metrics.problem_solving,
                'time_management': self.metrics.time_management,
                'consistency': self.metrics.consistency,
                'engagement': self.metrics.engagement
            },
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'trends': self.trends
        }


class LearningEvaluatorAgent:
    """学习效果评估智能体"""
    
    SYSTEM_PROMPT = """你是一位专业的学习评估专家，负责分析学生的学习数据并给出精准的评估报告。

## 评估维度（8个核心指标）
1. **知识掌握度**：对各知识点的理解和记忆程度
2. **学习效率**：单位时间内学习成果的产出
3. **练习准确率**：答题正确率及稳定性
4. **概念理解度**：对核心概念的深入理解程度
5. **问题解决能力**：面对新问题的分析和解决能力
6. **时间管理**：学习时间的合理分配和利用
7. **学习持续性**：学习行为的规律性和坚持度
8. **学习投入度**：学习时的专注程度和参与积极性

## 评估标准
- 90-100分：优秀 (Excellent)
- 75-89分：良好 (Good)
- 60-74分：一般 (Fair)
- 60分以下：需改进 (Poor)

## 分析原则
1. 结合定量数据（答题正确率、学习时长等）和定性分析
2. 识别学生的优势和劣势领域
3. 关注学习趋势和进步情况
4. 提供具体、可操作的改进建议
5. 考虑学生的认知风格和学习特点

## 输出格式
```json
{
  "overall_score": 85.5,
  "level": "Good",
  "metrics": {
    "knowledge_mastery": 82.3,
    "learning_efficiency": 78.5,
    ...
  },
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["劣势1", "劣势2"],
  "recommendations": ["建议1", "建议2"],
  "trends": {
    "improving_topics": [],
    "declining_topics": [],
    "stability": "stable"
  }
}
```"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.history: List[AssessmentReport] = []
    
    def evaluate(
        self,
        profile: StudentProfile,
        learning_data: Dict[str, Any]
    ) -> AssessmentReport:
        """执行学习效果评估"""
        
        # 计算各项指标
        metrics = self._calculate_metrics(profile, learning_data)
        
        # 计算总分
        overall_score = self._calculate_overall_score(metrics)
        
        # 确定等级
        level = self._determine_level(overall_score)
        
        # 分析优劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(metrics)
        
        # 生成建议
        recommendations = self._generate_recommendations(metrics, profile)
        
        # 分析趋势
        trends = self._analyze_trends(learning_data)
        
        # 创建报告
        report = AssessmentReport(
            student_id=profile.user_id,
            assessment_date=datetime.now().isoformat(),
            overall_score=overall_score,
            level=level,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            trends=trends
        )
        
        self.history.append(report)
        return report
    
    def _calculate_metrics(
        self,
        profile: StudentProfile,
        learning_data: Dict[str, Any]
    ) -> LearningMetrics:
        """计算各项学习指标"""
        
        metrics = LearningMetrics()
        
        # 知识掌握度
        if profile.knowledge_base:
            total_mastery = sum(profile.knowledge_base.values())
            avg_mastery = total_mastery / len(profile.knowledge_base)
            metrics.knowledge_mastery = min(100, avg_mastery * 100)
        else:
            metrics.knowledge_mastery = 50.0
        
        # 从答题数据计算准确率
        quiz_data = learning_data.get('quiz_results', [])
        if quiz_data:
            correct = sum(1 for q in quiz_data if q.get('is_correct', False))
            metrics.practice_accuracy = (correct / len(quiz_data)) * 100
        else:
            metrics.practice_accuracy = metrics.knowledge_mastery
        
        # 概念理解度（基于答题分析）
        if quiz_data:
            conceptual_questions = [q for q in quiz_data if q.get('type') == 'conceptual']
            if conceptual_questions:
                correct_conceptual = sum(1 for q in conceptual_questions if q.get('is_correct', False))
                metrics.concept_understanding = (correct_conceptual / len(conceptual_questions)) * 100
            else:
                metrics.concept_understanding = metrics.practice_accuracy
        else:
            metrics.concept_understanding = metrics.knowledge_mastery * 0.9
        
        # 问题解决能力（基于难题正确率）
        if quiz_data:
            hard_questions = [q for q in quiz_data if q.get('difficulty') == 'hard']
            if hard_questions:
                correct_hard = sum(1 for q in hard_questions if q.get('is_correct', False))
                metrics.problem_solving = (correct_hard / len(hard_questions)) * 100
            else:
                metrics.problem_solving = metrics.practice_accuracy * 0.8
        else:
            metrics.problem_solving = 50.0
        
        # 学习效率（基于时间和成果比）
        study_time = learning_data.get('total_study_time', 0)
        expected_time = len(quiz_data) * 5  # 假设每题5分钟
        if expected_time > 0:
            efficiency = min(100, (expected_time / max(study_time, 1)) * 100)
            metrics.learning_efficiency = (efficiency + metrics.knowledge_mastery) / 2
        else:
            metrics.learning_efficiency = 70.0
        
        # 时间管理
        study_patterns = learning_data.get('study_patterns', {})
        if study_patterns:
            punctuality = study_patterns.get('punctuality', 0.8)
            planning = study_patterns.get('planning', 0.7)
            metrics.time_management = (punctuality + planning) * 50
        else:
            metrics.time_management = 70.0
        
        # 学习持续性
        streak_data = learning_data.get('streak', {})
        current_streak = streak_data.get('current', 0)
        metrics.consistency = min(100, current_streak * 10)
        
        # 学习投入度
        engagement_factors = [
            metrics.consistency,
            study_patterns.get('focus_time_ratio', 0.7) * 100,
            learning_data.get('resource_usage_rate', 0.5) * 100
        ]
        metrics.engagement = sum(engagement_factors) / len(engagement_factors)
        
        return metrics
    
    def _calculate_overall_score(self, metrics: LearningMetrics) -> float:
        """计算综合得分"""
        weights = {
            'knowledge_mastery': 0.25,
            'practice_accuracy': 0.20,
            'concept_understanding': 0.15,
            'problem_solving': 0.15,
            'learning_efficiency': 0.10,
            'time_management': 0.05,
            'consistency': 0.05,
            'engagement': 0.05
        }
        
        total = (
            metrics.knowledge_mastery * weights['knowledge_mastery'] +
            metrics.practice_accuracy * weights['practice_accuracy'] +
            metrics.concept_understanding * weights['concept_understanding'] +
            metrics.problem_solving * weights['problem_solving'] +
            metrics.learning_efficiency * weights['learning_efficiency'] +
            metrics.time_management * weights['time_management'] +
            metrics.consistency * weights['consistency'] +
            metrics.engagement * weights['engagement']
        )
        
        return round(total, 1)
    
    def _determine_level(self, score: float) -> str:
        """确定等级"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'
    
    def _analyze_strengths_weaknesses(
        self,
        metrics: LearningMetrics
    ) -> tuple[List[str], List[str]]:
        """分析优劣势"""
        
        strengths = []
        weaknesses = []
        
        metric_scores = {
            '知识掌握度': metrics.knowledge_mastery,
            '练习准确率': metrics.practice_accuracy,
            '概念理解度': metrics.concept_understanding,
            '问题解决能力': metrics.problem_solving,
            '学习效率': metrics.learning_efficiency,
            '时间管理': metrics.time_management,
            '学习持续性': metrics.consistency,
            '学习投入度': metrics.engagement
        }
        
        # 找出优势（前3个最高分）
        sorted_metrics = sorted(metric_scores.items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_metrics[:3]:
            if score >= 75:
                strengths.append(f"{name}表现优秀（{score:.1f}分）")
        
        # 找出劣势（后3个最低分）
        for name, score in sorted_metrics[-3:]:
            if score < 70:
                weaknesses.append(f"{name}需要加强（{score:.1f}分）")
        
        return strengths, weaknesses
    
    def _generate_recommendations(
        self,
        metrics: LearningMetrics,
        profile: StudentProfile
    ) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于各项指标的建议
        if metrics.knowledge_mastery < 70:
            recommendations.append("建议加强基础知识学习，使用思维导图整理知识点")
        
        if metrics.practice_accuracy < 70:
            recommendations.append("多做练习题，特别是错题分析，理解解题思路")
        
        if metrics.concept_understanding < 70:
            recommendations.append("深入理解核心概念，可以尝试讲解给他人来检验理解")
        
        if metrics.problem_solving < 70:
            recommendations.append("多挑战难题，学习不同题型的解题策略")
        
        if metrics.learning_efficiency < 70:
            recommendations.append("优化学习方法，使用番茄工作法提高专注度")
        
        if metrics.time_management < 70:
            recommendations.append("制定详细的学习计划，合理分配各科时间")
        
        if metrics.consistency < 70:
            recommendations.append("保持规律学习，设定每日固定学习时间")
        
        if metrics.engagement < 70:
            recommendations.append("增加学习互动，如参与讨论、做学习笔记")
        
        # 基于画像的个性化建议
        if profile.cognitive_style == 'visual':
            recommendations.append("建议使用更多图表、思维导图等可视化学习材料")
        elif profile.cognitive_style == 'verbal':
            recommendations.append("建议多做笔记、复述、讲解练习")
        
        if profile.learning_speed == 'slow':
            recommendations.append("放慢学习节奏，确保每个知识点充分理解后再继续")
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _analyze_trends(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学习趋势"""
        
        trends = {
            'improving_topics': [],
            'declining_topics': [],
            'stability': 'stable'
        }
        
        # 分析知识点趋势
        topic_progress = learning_data.get('topic_progress', {})
        for topic, progress in topic_progress.items():
            if isinstance(progress, dict):
                if progress.get('trend', 0) > 0.1:
                    trends['improving_topics'].append(topic)
                elif progress.get('trend', 0) < -0.1:
                    trends['declining_topics'].append(topic)
        
        # 分析稳定性
        score_variance = learning_data.get('score_variance', 0)
        if score_variance < 10:
            trends['stability'] = 'very_stable'
        elif score_variance < 20:
            trends['stability'] = 'stable'
        elif score_variance < 30:
            trends['stability'] = 'fluctuating'
        else:
            trends['stability'] = 'unstable'
        
        return trends
    
    def compare_with_previous(self, current_report: AssessmentReport) -> Dict[str, Any]:
        """与上一次评估对比"""
        
        if len(self.history) < 2:
            return {'message': '暂无历史数据对比'}
        
        previous = self.history[-2]
        
        comparison = {
            'overall_change': current_report.overall_score - previous.overall_score,
            'metric_changes': {}
        }
        
        # 各指标变化
        current_metrics = current_report.metrics
        prev_metrics = previous.metrics
        
        metric_names = [
            'knowledge_mastery', 'practice_accuracy', 'concept_understanding',
            'problem_solving', 'learning_efficiency', 'time_management',
            'consistency', 'engagement'
        ]
        
        for name in metric_names:
            current_val = getattr(current_metrics, name)
            prev_val = getattr(prev_metrics, name)
            comparison['metric_changes'][name] = current_val - prev_val
        
        return comparison
    
    def generate_detailed_report(
        self,
        report: AssessmentReport,
        include_recommendations: bool = True
    ) -> str:
        """生成详细的文本报告"""
        
        level_names = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '需改进'
        }
        
        report_text = f"""
# 学习效果评估报告

## 总体评估
- **评估日期**：{report.assessment_date[:10]}
- **综合得分**：{report.overall_score}分
- **等级评定**：{level_names.get(report.level, report.level)}

## 各项指标得分

| 指标 | 得分 | 评价 |
|------|------|------|
| 知识掌握度 | {report.metrics.knowledge_mastery:.1f} | {'优秀' if report.metrics.knowledge_mastery >= 75 else '良好' if report.metrics.knowledge_mastery >= 60 else '需提升'} |
| 练习准确率 | {report.metrics.practice_accuracy:.1f} | {'优秀' if report.metrics.practice_accuracy >= 75 else '良好' if report.metrics.practice_accuracy >= 60 else '需提升'} |
| 概念理解度 | {report.metrics.concept_understanding:.1f} | {'优秀' if report.metrics.concept_understanding >= 75 else '良好' if report.metrics.concept_understanding >= 60 else '需提升'} |
| 问题解决能力 | {report.metrics.problem_solving:.1f} | {'优秀' if report.metrics.problem_solving >= 75 else '良好' if report.metrics.problem_solving >= 60 else '需提升'} |
| 学习效率 | {report.metrics.learning_efficiency:.1f} | {'优秀' if report.metrics.learning_efficiency >= 75 else '良好' if report.metrics.learning_efficiency >= 60 else '需提升'} |
| 时间管理 | {report.metrics.time_management:.1f} | {'优秀' if report.metrics.time_management >= 75 else '良好' if report.metrics.time_management >= 60 else '需提升'} |
| 学习持续性 | {report.metrics.consistency:.1f} | {'优秀' if report.metrics.consistency >= 75 else '良好' if report.metrics.consistency >= 60 else '需提升'} |
| 学习投入度 | {report.metrics.engagement:.1f} | {'优秀' if report.metrics.engagement >= 75 else '良好' if report.metrics.engagement >= 60 else '需提升'} |

## 优势领域
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(report.strengths)) if report.strengths else '暂无明显优势'}

## 需要加强
{chr(10).join(f'{i+1}. {w}' for i, w in enumerate(report.weaknesses)) if report.weaknesses else '暂无明显短板'}

"""
        
        if include_recommendations and report.recommendations:
            report_text += "## 改进建议\n"
            for i, rec in enumerate(report.recommendations, 1):
                report_text += f"{i}. {rec}\n"
        
        return report_text
