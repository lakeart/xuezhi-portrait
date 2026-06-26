# -*- coding: utf-8 -*-
"""
学习规划智能体
基于学生画像和资源情况，规划个性化学习路径
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from . import LearningPath, StudentProfile, LearningResource, ResourceType


class LearningPlannerAgent:
    """学习规划智能体"""
    
    SYSTEM_PROMPT = """你是一位专业的学习规划师，负责为学生制定科学、动态的个性化学习路径。

## 核心原则
1. **循序渐进**：按照知识逻辑顺序安排学习内容
2. **因材施教**：根据学生画像调整学习节奏
3. **动态调整**：根据学习效果实时优化路径
4. **目标导向**：紧密围绕学生目标设计路径

## 学习路径结构
```json
{
  "path_id": "唯一标识",
  "steps": [
    {
      "step_number": 1,
      "title": "步骤标题",
      "description": "学习目标描述",
      "topics": ["知识点1", "知识点2"],
      "duration": 60,
      "difficulty": "easy/medium/hard",
      "resources": ["资源ID列表"],
      "milestone": "里程碑描述"
    }
  ],
  "total_duration": 300,
  "difficulty_curve": ["easy", "easy", "medium", "medium", "hard"],
  "milestones": [
    {
      "name": "里程碑名称",
      "step": 3,
      "achievement": "达成条件"
    }
  ]
}
```

## 规划要点
1. 先评估学生当前水平
2. 识别需要掌握的知识点
3. 按难度递进安排
4. 合理分配时间
5. 设置检查点
6. 预留复习时间"""
    
    def __init__(self):
        self.current_path: Optional[LearningPath] = None
    
    def create_learning_path(
        self,
        profile: StudentProfile,
        resources: List[LearningResource],
        goal: str = "掌握核心知识"
    ) -> LearningPath:
        """创建学习路径"""
        
        # 分析目标知识点
        target_topics = self._analyze_target_topics(profile)
        
        # 规划学习步骤
        steps = self._plan_steps(profile, resources, target_topics)
        
        # 设置难度曲线
        difficulty_curve = self._generate_difficulty_curve(steps)
        
        # 设置里程碑
        milestones = self._set_milestones(steps, target_topics)
        
        # 计算总时长
        total_duration = sum(step.get('duration', 30) for step in steps)
        
        # 创建路径对象
        path = LearningPath(
            path_id=str(uuid.uuid4()),
            student_profile=profile,
            steps=steps,
            total_duration=total_duration,
            difficulty_curve=difficulty_curve,
            milestones=milestones
        )
        
        self.current_path = path
        return path
    
    def _analyze_target_topics(self, profile: StudentProfile) -> List[Dict]:
        """分析目标知识点"""
        topics = []
        
        # 处理薄弱知识点（优先学习）
        for topic in profile.weak_topics:
            topics.append({
                'name': topic,
                'priority': 1,
                'type': 'weak',
                'mastery': profile.knowledge_base.get(topic, 0)
            })
        
        # 处理未掌握知识点
        for topic, mastery in profile.knowledge_base.items():
            if topic not in profile.weak_topics and mastery < 0.8:
                topics.append({
                    'name': topic,
                    'priority': 2,
                    'type': 'need_work',
                    'mastery': mastery
                })
        
        # 处理偏好知识点（增强兴趣）
        for topic in profile.preferred_topics:
            if topic not in [t['name'] for t in topics]:
                topics.append({
                    'name': topic,
                    'priority': 3,
                    'type': 'interest',
                    'mastery': profile.knowledge_base.get(topic, 0)
                })
        
        # 按优先级排序
        topics.sort(key=lambda x: (x['priority'], x['mastery']))
        
        return topics[:10]  # 最多规划10个知识点
    
    def _plan_steps(
        self,
        profile: StudentProfile,
        resources: List[LearningResource],
        target_topics: List[Dict]
    ) -> List[Dict]:
        """规划学习步骤"""
        
        steps = []
        resource_map = {r.target_topics[0] if r.target_topics else 'unknown': r 
                       for r in resources}
        
        # 学习速度调整
        speed_factor = {'fast': 0.7, 'medium': 1.0, 'slow': 1.3}.get(profile.learning_speed, 1.0)
        
        step_number = 1
        
        for i, topic_info in enumerate(target_topics):
            topic = topic_info['name']
            
            # 基础学习步骤
            step = {
                'step_number': step_number,
                'title': f'学习：{topic}',
                'description': f'系统学习{topic}的核心概念和应用',
                'topics': [topic],
                'duration': int(45 * speed_factor),
                'difficulty': self._get_difficulty_for_topic(topic_info),
                'resources': [],
                'activities': self._get_activities_for_topic(topic_info)
            }
            
            # 添加相关资源
            if topic in resource_map:
                step['resources'].append(resource_map[topic].resource_id)
            
            steps.append(step)
            step_number += 1
            
            # 添加练习步骤
            practice_step = {
                'step_number': step_number,
                'title': f'练习：{topic}',
                'description': f'通过练习巩固{topic}知识',
                'topics': [topic],
                'duration': int(30 * speed_factor),
                'difficulty': self._get_difficulty_for_topic(topic_info, practice=True),
                'resources': [],
                'activities': ['做题', '错题分析', '总结反思']
            }
            
            steps.append(practice_step)
            step_number += 1
            
            # 每3个知识点添加复习步骤
            if (i + 1) % 3 == 0:
                review_step = {
                    'step_number': step_number,
                    'title': '阶段复习',
                    'description': '复习前3个知识点的内容',
                    'topics': [t['name'] for t in target_topics[max(0, i-2):i+1]],
                    'duration': int(40 * speed_factor),
                    'difficulty': 'medium',
                    'resources': [],
                    'activities': ['回顾笔记', '思维导图', '自测检验']
                }
                steps.append(review_step)
                step_number += 1
        
        # 添加总结步骤
        if steps:
            summary_step = {
                'step_number': step_number,
                'title': '学习总结',
                'description': '整体回顾学习内容，形成知识体系',
                'topics': [t['name'] for t in target_topics],
                'duration': 30,
                'difficulty': 'easy',
                'resources': [],
                'activities': ['整理笔记', '绘制总图', '制定下一步计划']
            }
            steps.append(summary_step)
        
        return steps
    
    def _get_difficulty_for_topic(self, topic_info: Dict, practice: bool = False) -> str:
        """确定知识点难度"""
        mastery = topic_info.get('mastery', 0)
        
        if practice:
            # 练习难度略高于学习难度
            if mastery < 0.4:
                return 'medium'
            elif mastery < 0.7:
                return 'hard'
            else:
                return 'easy'
        else:
            # 学习难度基于掌握度
            if mastery < 0.3:
                return 'easy'
            elif mastery < 0.6:
                return 'medium'
            else:
                return 'hard'
    
    def _get_activities_for_topic(self, topic_info: Dict) -> List[str]:
        """获取学习活动"""
        base_activities = ['观看讲解', '做笔记', '理解概念']
        
        if topic_info['type'] == 'weak':
            base_activities.extend(['增加示例', '专项练习'])
        elif topic_info['type'] == 'interest':
            base_activities.extend(['拓展探索', '创新应用'])
        
        return base_activities
    
    def _generate_difficulty_curve(self, steps: List[Dict]) -> List[str]:
        """生成难度曲线"""
        if not steps:
            return []
        
        curve = []
        n = len(steps)
        
        for i, step in enumerate(steps):
            position = i / max(n - 1, 1)
            
            if position < 0.2:
                curve.append('easy')
            elif position < 0.4:
                curve.append('easy') if i % 2 == 0 else curve.append('medium')
            elif position < 0.7:
                curve.append('medium')
            elif position < 0.9:
                curve.append('medium') if i % 2 == 0 else curve.append('hard')
            else:
                curve.append('hard')
        
        return curve
    
    def _set_milestones(self, steps: List[Dict], target_topics: List[Dict]) -> List[Dict]:
        """设置里程碑"""
        milestones = []
        
        milestones_names = [
            "入门成功",
            "基础掌握",
            "能力提升",
            "深入理解",
            "融会贯通"
        ]
        
        step_interval = max(1, len(steps) // 5)
        
        for i, name in enumerate(milestones_names):
            step_idx = min((i + 1) * step_interval - 1, len(steps) - 1)
            
            milestones.append({
                'name': name,
                'step': steps[step_idx]['step_number'] if steps else 1,
                'achievement': f'完成前{steps[step_idx]["step_number"]}个学习步骤',
                'reward': self._get_milestone_reward(i)
            })
        
        return milestones
    
    def _get_milestone_reward(self, index: int) -> str:
        """获取里程碑奖励"""
        rewards = [
            "解锁成就：初窥门径",
            "解锁成就：渐入佳境",
            "解锁成就：小有所成",
            "解锁成就：学有所长",
            "解锁成就：融会贯通"
        ]
        return rewards[min(index, len(rewards) - 1)]
    
    def get_weekly_plan(
        self,
        path: LearningPath,
        weekly_hours: int = 10
    ) -> Dict[str, Any]:
        """生成周计划"""
        
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        time_slots = {
            'morning': ('早上 8:00-10:00', 2),
            'afternoon': ('下午 2:00-4:00', 2),
            'evening': ('晚上 7:00-9:00', 2)
        }
        
        weekly_plan = []
        
        # 分配步骤到每天
        hours_per_day = weekly_hours // 7
        step_idx = 0
        
        for day in days:
            day_tasks = []
            remaining_hours = hours_per_day
            
            while remaining_hours > 0 and step_idx < len(path.steps):
                step = path.steps[step_idx]
                duration_hours = step.get('duration', 30) / 60
                
                if remaining_hours >= duration_hours:
                    day_tasks.append({
                        'time': f"{day} {time_slots['morning'][0] if len(day_tasks) == 0 else time_slots['afternoon'][0]}",
                        'title': step['title'],
                        'duration': step['duration'],
                        'topics': step.get('topics', [])
                    })
                    remaining_hours -= duration_hours
                    step_idx += 1
                else:
                    break
            
            weekly_plan.append({
                'day': day,
                'tasks': day_tasks,
                'total_hours': hours_per_day - remaining_hours
            })
        
        return {
            'weekly_plan': weekly_plan,
            'summary': {
                'total_hours': weekly_hours,
                'total_steps': min(step_idx + 1, len(path.steps)),
                'completion_rate': step_idx / len(path.steps) if path.steps else 0
            }
        }
    
    def adjust_path(
        self,
        path: LearningPath,
        progress: Dict[str, Any]
    ) -> LearningPath:
        """根据学习进度调整路径"""
        
        completed_steps = progress.get('completed_steps', [])
        assessment_results = progress.get('assessments', {})
        
        # 标记已完成步骤
        for step in path.steps:
            if step['step_number'] in completed_steps:
                step['completed'] = True
        
        # 根据评估结果调整后续步骤
        for step in path.steps:
            if not step.get('completed', False):
                for topic in step.get('topics', []):
                    if topic in assessment_results:
                        score = assessment_results[topic]
                        
                        # 成绩不理想，降低难度
                        if score < 0.6:
                            step['difficulty'] = 'easy'
                            step['duration'] = int(step['duration'] * 1.2)
                            step['activities'].append('额外练习')
                        
                        # 成绩优秀，加快进度
                        elif score > 0.9:
                            step['duration'] = int(step['duration'] * 0.8)
                            step['activities'].append('进阶挑战')
        
        return path
    
    def recommend_resources(
        self,
        path: LearningPath,
        current_step: int
    ) -> List[Dict]:
        """推荐下一步学习资源"""
        
        recommendations = []
        
        if current_step < len(path.steps):
            step = path.steps[current_step]
            recommendations.append({
                'type': 'primary',
                'reason': f'当前学习步骤：{step["title"]}',
                'step': step
            })
        
        # 推荐相关资源类型
        if current_step < len(path.steps):
            next_step = path.steps[current_step]
            for topic in next_step.get('topics', []):
                recommendations.append({
                    'type': 'topic_related',
                    'reason': f'与{topic}相关的补充资源',
                    'topic': topic
                })
        
        return recommendations
