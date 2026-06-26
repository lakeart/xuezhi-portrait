# -*- coding: utf-8 -*-
"""
多智能体协调器
负责协调各智能体工作，实现多智能体协同
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import StudentProfile, LearningResource, LearningPath, ResourceType, AgentRole
from .profile_agent import ProfileBuilderAgent
from .resource_agent import ResourceGeneratorAgent
from .planner_agent import LearningPlannerAgent
from .tutor_agent import TutorAgent
from .knowledge_agent import KnowledgeBaseAgent


class AgentCoordinator:
    """多智能体系统协调器"""
    
    def __init__(self):
        # 初始化各智能体
        self.profile_agent = ProfileBuilderAgent()
        self.resource_agent = ResourceGeneratorAgent()
        self.planner_agent = LearningPlannerAgent()
        self.tutor_agent = TutorAgent()
        self.knowledge_agent = KnowledgeBaseAgent()
        
        # 状态管理
        self.current_profile: Optional[StudentProfile] = None
        self.generated_resources: List[LearningResource] = []
        self.current_path: Optional[LearningPath] = None
        self.session_id = str(uuid.uuid4())
        
        # 执行历史
        self.execution_log: List[Dict] = []
    
    def initialize_session(self, user_id: int, username: str) -> Dict[str, Any]:
        """初始化会话"""
        
        self.session_id = str(uuid.uuid4())
        
        # 初始化画像
        self.current_profile = self.profile_agent.init_profile(user_id, username)
        
        # 生成初始欢迎消息
        welcome = self.profile_agent._get_greeting()
        
        return {
            'session_id': self.session_id,
            'profile': self.current_profile.to_dict(),
            'welcome_message': welcome,
            'suggested_questions': self.profile_agent._generate_suggested_questions()
        }
    
    def build_profile(self, user_message: str) -> Dict[str, Any]:
        """构建/更新学习画像"""
        
        # 记录执行
        self._log_execution(AgentRole.PROFILE_BUILDER, 'build_profile', {'message': user_message})
        
        # 处理对话
        result = self.profile_agent.process_message(user_message)
        
        # 更新当前画像
        if result.get('profile'):
            self.current_profile = self.profile_agent.profile
        
        return result
    
    def generate_learning_resources(
        self,
        topics: List[str],
        resource_types: List[ResourceType] = None
    ) -> Dict[str, Any]:
        """协同生成学习资源"""
        
        if not self.current_profile:
            return {'error': '请先构建学习画像'}
        
        # 记录执行
        self._log_execution(
            AgentRole.RESOURCE_GENERATOR,
            'generate_resources',
            {'topics': topics, 'types': [r.value for r in (resource_types or [])]}
        )
        
        # 协同生成资源
        if resource_types is None:
            resource_types = list(ResourceType)
        
        # 并行生成多种资源
        resources = {}
        errors = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for topic in topics:
                for res_type in resource_types:
                    future = executor.submit(
                        self.resource_agent.generate_resource,
                        res_type,
                        topic,
                        self.current_profile
                    )
                    futures[future] = {'topic': topic, 'type': res_type}
            
            for future in as_completed(futures):
                info = futures[future]
                try:
                    resource = future.result()
                    key = f"{info['topic']}_{info['type'].value}"
                    resources[key] = resource
                    self.generated_resources.append(resource)
                except Exception as e:
                    errors.append({
                        'topic': info['topic'],
                        'type': info['type'].value,
                        'error': str(e)
                    })
        
        # 返回资源卡片
        resource_cards = [r.to_card() for r in self.generated_resources]
        
        return {
            'resources': resource_cards,
            'count': len(resource_cards),
            'errors': errors,
            'types_generated': list(set(r.resource_type.value for r in self.generated_resources))
        }
    
    def create_personalized_plan(
        self,
        goals: List[str] = None,
        time_constraint: int = 10
    ) -> Dict[str, Any]:
        """创建个性化学习计划"""
        
        if not self.current_profile:
            return {'error': '请先构建学习画像'}
        
        # 更新目标
        if goals:
            self.current_profile.goals = goals
        
        # 记录执行
        self._log_execution(AgentRole.LEARNING_PLANNER, 'create_plan', {'goals': goals})
        
        # 创建学习路径
        self.current_path = self.planner_agent.create_learning_path(
            self.current_profile,
            self.generated_resources,
            goals[0] if goals else "掌握核心知识"
        )
        
        # 生成周计划
        weekly_plan = self.planner_agent.get_weekly_plan(
            self.current_path,
            weekly_hours=time_constraint
        )
        
        return {
            'learning_path': self.current_path.to_dict(),
            'weekly_plan': weekly_plan,
            'summary': {
                'total_steps': len(self.current_path.steps),
                'total_duration': self.current_path.total_duration,
                'milestones': len(self.current_path.milestones),
                'difficulty_curve': self.current_path.difficulty_curve
            }
        }
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """智能问答"""
        
        if not self.current_profile:
            return {'error': '请先构建学习画像'}
        
        # 记录执行
        self._log_execution(AgentRole.TUTOR, 'answer_question', {'question': question})
        
        # 回答问题
        answer_data = self.tutor_agent.answer_question(
            question,
            self.current_profile
        )
        
        return answer_data
    
    def stream_ask_question(self, question: str) -> Callable[[], str]:
        """流式问答"""
        
        if not self.current_profile:
            return lambda: "请先构建学习画像"
        
        self._log_execution(AgentRole.TUTOR, 'stream_answer', {'question': question})
        
        return lambda: ''.join(self.tutor_agent.stream_answer(question, self.current_profile))
    
    def evaluate_and_adjust(
        self,
        completed_steps: List[int],
        assessment_results: Dict[str, float]
    ) -> Dict[str, Any]:
        """评估学习效果并调整计划"""
        
        if not self.current_path:
            return {'error': '暂无学习计划'}
        
        # 记录执行
        self._log_execution(
            AgentRole.COORDINATOR,
            'evaluate_and_adjust',
            {'completed': completed_steps, 'assessments': assessment_results}
        )
        
        # 计算学习效果
        evaluation = self._calculate_learning_effect(
            completed_steps,
            assessment_results
        )
        
        # 调整学习计划
        adjusted_path = self.planner_agent.adjust_path(
            self.current_path,
            {'completed_steps': completed_steps, 'assessments': assessment_results}
        )
        
        # 更新当前路径
        self.current_path = adjusted_path
        
        return {
            'evaluation': evaluation,
            'adjusted_path': adjusted_path.to_dict(),
            'recommendations': self._generate_recommendations(evaluation)
        }
    
    def _calculate_learning_effect(
        self,
        completed_steps: List[int],
        assessment_results: Dict[str, float]
    ) -> Dict[str, Any]:
        """计算学习效果"""
        
        if not self.current_path:
            return {}
        
        total_steps = len(self.current_path.steps)
        completed_count = len(completed_steps)
        completion_rate = completed_count / total_steps if total_steps > 0 else 0
        
        # 评估结果统计
        topic_scores = list(assessment_results.values())
        avg_score = sum(topic_scores) / len(topic_scores) if topic_scores else 0
        
        # 学习效果评级
        if completion_rate >= 0.8 and avg_score >= 0.85:
            effect_level = 'excellent'
            feedback = '学习效果非常出色！继续保持'
        elif completion_rate >= 0.6 and avg_score >= 0.7:
            effect_level = 'good'
            feedback = '学习效果良好，有进步空间'
        elif completion_rate >= 0.4 and avg_score >= 0.5:
            effect_level = 'fair'
            feedback = '学习效果一般，建议调整学习策略'
        else:
            effect_level = 'poor'
            feedback = '需要更多练习和巩固'
        
        return {
            'completion_rate': round(completion_rate * 100, 1),
            'completed_steps': completed_count,
            'total_steps': total_steps,
            'avg_score': round(avg_score * 100, 1),
            'topic_scores': assessment_results,
            'effect_level': effect_level,
            'feedback': feedback
        }
    
    def _generate_recommendations(self, evaluation: Dict) -> List[str]:
        """生成学习建议"""
        
        recommendations = []
        
        completion_rate = evaluation.get('completion_rate', 0)
        avg_score = evaluation.get('avg_score', 0)
        
        # 完成率建议
        if completion_rate < 50:
            recommendations.append('建议增加每日学习时间，提高完成率')
        elif completion_rate > 90:
            recommendations.append('完成率很高，可以适当增加学习难度')
        
        # 成绩建议
        if avg_score < 60:
            recommendations.append('基础知识需要加强，建议复习基础内容')
            recommendations.append('可以生成更多练习题进行巩固')
        elif avg_score >= 80:
            recommendations.append('成绩优秀，可以尝试进阶内容')
        
        # 个性化建议
        if self.current_profile:
            if self.current_profile.learning_speed == 'slow':
                recommendations.append('建议放慢学习节奏，深入理解每个知识点')
            elif self.current_profile.learning_speed == 'fast':
                recommendations.append('学习进度较快，注意巩固已学内容')
        
        return recommendations[:4]
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        
        return {
            'session_id': self.session_id,
            'profile': self.current_profile.to_dict() if self.current_profile else None,
            'resources_count': len(self.generated_resources),
            'path_steps': len(self.current_path.steps) if self.current_path else 0,
            'execution_log_count': len(self.execution_log),
            'available_agents': {
                'profile_builder': True,
                'resource_generator': True,
                'learning_planner': True,
                'tutor': True,
                'evaluator': True,
                'knowledge_base': True,
                'coordinator': True
            }
        }
    
    def reset_session(self) -> Dict[str, Any]:
        """重置会话"""
        
        self.profile_agent = ProfileBuilderAgent()
        self.resource_agent = ResourceGeneratorAgent()
        self.planner_agent = LearningPlannerAgent()
        self.tutor_agent = TutorAgent()
        self.knowledge_agent = KnowledgeBaseAgent()
        
        self.current_profile = None
        self.generated_resources = []
        self.current_path = None
        self.execution_log = []
        
        return {
            'message': '会话已重置',
            'new_session_id': self.session_id
        }
    
    def _log_execution(self, agent: AgentRole, action: str, params: Dict) -> None:
        """记录执行日志"""
        
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'agent': agent.value,
            'action': action,
            'params': params
        })
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出会话数据"""
        
        return {
            'session_id': self.session_id,
            'profile': self.current_profile.to_dict() if self.current_profile else None,
            'resources': [r.to_card() for r in self.generated_resources],
            'learning_path': self.current_path.to_dict() if self.current_path else None,
            'execution_log': self.execution_log,
            'exported_at': datetime.now().isoformat()
        }


# 全局协调器实例
_coordinator_instance: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """获取协调器实例"""
    global _coordinator_instance
    
    if _coordinator_instance is None:
        _coordinator_instance = AgentCoordinator()
    
    return _coordinator_instance


def create_new_session(user_id: int, username: str) -> Dict[str, Any]:
    """创建新会话"""
    coordinator = get_coordinator()
    coordinator.reset_session()
    return coordinator.initialize_session(user_id, username)
