# -*- coding: utf-8 -*-
"""
多智能体系统核心模块
基于大模型的个性化资源生成与学习多智能体系统
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentRole(Enum):
    """智能体角色枚举"""
    PROFILE_BUILDER = "profile_builder"      # 学习画像构建智能体
    RESOURCE_GENERATOR = "resource_generator" # 资源生成智能体
    LEARNING_PLANNER = "learning_planner"    # 学习规划智能体
    TUTOR = "tutor"                          # 智能辅导智能体
    EVALUATOR = "evaluator"                  # 学习评估智能体
    KNOWLEDGE_BASE = "knowledge_base"         # 知识库管理智能体
    COORDINATOR = "coordinator"              # 协调智能体


class ResourceType(Enum):
    """资源类型枚举"""
    COURSE_DOCUMENT = "course_document"       # 课程讲解文档
    MIND_MAP = "mind_map"                     # 思维导图
    EXERCISES = "exercises"                   # 练习题目
    EXTENDED_READING = "extended_reading"     # 拓展阅读
    VIDEO_SCRIPT = "video_script"             # 视频脚本/动画
    CODE_PRACTICE = "code_practice"           # 代码实操案例


@dataclass
class AgentMessage:
    """智能体消息"""
    role: str  # system, user, assistant
    content: str
    agent_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentProfile:
    """学生画像"""
    user_id: int
    username: str
    
    # 6+维度画像
    knowledge_base: Dict[str, float] = field(default_factory=dict)  # 知识基础
    cognitive_style: str = "visual"  # 认知风格: visual/verbal/auditory/kinesthetic
    error_patterns: List[Dict] = field(default_factory=list)  # 易错点偏好
    learning_speed: str = "medium"  # 学习速度: slow/medium/fast
    interests: List[str] = field(default_factory=list)  # 兴趣方向
    goals: List[str] = field(default_factory=list)  # 学习目标
    preferred_topics: List[str] = field(default_factory=list)  # 偏好知识点
    
    # 扩展维度
    weak_topics: List[str] = field(default_factory=list)  # 薄弱知识点
    strong_topics: List[str] = field(default_factory=list)  # 强项知识点
    study_habits: Dict[str, Any] = field(default_factory=dict)  # 学习习惯
    available_time: Dict[str, int] = field(default_factory=dict)  # 可用时间
    
    # 元数据
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    confidence: float = 0.0  # 画像置信度
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'knowledge_base': self.knowledge_base,
            'cognitive_style': self.cognitive_style,
            'error_patterns': self.error_patterns,
            'learning_speed': self.learning_speed,
            'interests': self.interests,
            'goals': self.goals,
            'preferred_topics': self.preferred_topics,
            'weak_topics': self.weak_topics,
            'strong_topics': self.strong_topics,
            'study_habits': self.study_habits,
            'available_time': self.available_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'confidence': self.confidence,
            'dimension_count': 10  # 当前维度数
        }


@dataclass
class LearningResource:
    """学习资源"""
    resource_id: str
    resource_type: ResourceType
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    target_topics: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy/medium/hard
    estimated_time: int = 30  # 预计学习时间(分钟)
    source_agent: str = ""
    generated_at: Optional[str] = None
    
    def to_card(self) -> Dict:
        """转换为卡片格式"""
        return {
            'id': self.resource_id,
            'type': self.resource_type.value,
            'title': self.title,
            'preview': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'full_content': self.content,
            'metadata': self.metadata,
            'topics': self.target_topics,
            'difficulty': self.difficulty,
            'duration': self.estimated_time,
            'icon': self._get_icon(),
            'color': self._get_color()
        }
    
    def _get_icon(self) -> str:
        icons = {
            ResourceType.COURSE_DOCUMENT: "fa-file-alt",
            ResourceType.MIND_MAP: "fa-project-diagram",
            ResourceType.EXERCISES: "fa-pencil-alt",
            ResourceType.EXTENDED_READING: "fa-book-open",
            ResourceType.VIDEO_SCRIPT: "fa-video",
            ResourceType.CODE_PRACTICE: "fa-code"
        }
        return icons.get(self.resource_type, "fa-file")
    
    def _get_color(self) -> str:
        colors = {
            ResourceType.COURSE_DOCUMENT: "#4364F7",
            ResourceType.MIND_MAP: "#00C9A7",
            ResourceType.EXERCISES: "#FF6B6B",
            ResourceType.EXTENDED_READING: "#FF8C42",
            ResourceType.VIDEO_SCRIPT: "#A855F7",
            ResourceType.CODE_PRACTICE: "#3FB950"
        }
        return colors.get(self.resource_type, "#4364F7")


@dataclass
class LearningPath:
    """学习路径"""
    path_id: str
    student_profile: StudentProfile
    steps: List[Dict[str, Any]] = field(default_factory=list)
    total_duration: int = 0  # 总时长(分钟)
    difficulty_curve: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'path_id': self.path_id,
            'student': self.student_profile.username,
            'steps': self.steps,
            'total_duration': self.total_duration,
            'difficulty_curve': self.difficulty_curve,
            'milestones': self.milestones
        }


class ContentSafetyFilter:
    """内容安全过滤器"""
    
    # 敏感词库（简化示例）
    SENSITIVE_PATTERNS = [
        r'政治敏感',
        r'暴力倾向',
        r'违法内容',
    ]
    
    @classmethod
    def filter(cls, content: str) -> tuple[bool, str]:
        """
        过滤内容安全问题
        返回: (is_safe, reason)
        """
        if not content:
            return True, ""
        
        # 检查敏感词
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"内容包含敏感信息"
        
        # 检查长度限制
        if len(content) > 50000:
            return False, "内容过长"
        
        return True, ""
    
    @classmethod
    def sanitize(cls, content: str) -> str:
        """清理内容"""
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content)
        # 移除特殊字符
        content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.\,\!\?\;\:\"\'\-\(\)\[\]\{\}]', '', content)
        return content.strip()


class HallucinationDetector:
    """幻觉检测器"""
    
    # 可信的知识领域关键词
    TRUSTED_DOMAINS = {
        'computer_science': ['算法', '数据结构', '编程', '代码', '计算机', '软件', '网络', '数据库', '操作系统'],
        'mathematics': ['数学', '函数', '方程', '几何', '代数', '概率', '统计'],
        'physics': ['物理', '力学', '电磁', '光学', '量子'],
    }
    
    @classmethod
    def check_factuality(cls, content: str, topic: str = "") -> tuple[bool, List[str]]:
        """
        检测内容事实性
        返回: (is_factual, warnings)
        """
        warnings = []
        
        # 检查内容是否过于模糊
        vague_phrases = ['据说', '据说可能', '大概是', '也许是', '似乎']
        for phrase in vague_phrases:
            if phrase in content:
                warnings.append(f"内容包含不确定性表达: {phrase}")
        
        # 检查是否存在明显的虚假引用
        fake_citations = re.findall(r'《[^》]{1,20}》.*?说', content)
        if fake_citations:
            warnings.append("检测到未经验证的引用")
        
        # 如果有特定主题，检查是否在可信领域内
        if topic:
            topic_lower = topic.lower()
            in_trusted = False
            for domain, keywords in cls.TRUSTED_DOMAINS.items():
                if any(kw in topic_lower for kw in keywords):
                    in_trusted = True
                    break
            
            if not in_trusted:
                warnings.append("内容涉及非专业领域，请谨慎参考")
        
        return len(warnings) == 0, warnings
