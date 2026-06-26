# -*- coding: utf-8 -*-
"""
多智能体系统数据模型
"""

from datetime import datetime
from app import db


class StudentProfileModel(db.Model):
    """学生画像模型"""
    __tablename__ = 'student_profiles_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # 画像数据（JSON格式存储）
    profile_data = db.Column(db.Text)  # JSON字符串
    
    # 维度数据
    cognitive_style = db.Column(db.String(50), default='visual')
    learning_speed = db.Column(db.String(20), default='medium')
    confidence = db.Column(db.Float, default=0.0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref='agent_profile')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_data': json.loads(self.profile_data) if self.profile_data else {},
            'cognitive_style': self.cognitive_style,
            'learning_speed': self.learning_speed,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class LearningResourceModel(db.Model):
    """学习资源模型"""
    __tablename__ = 'learning_resources_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 资源基本信息
    resource_type = db.Column(db.String(50), nullable=False)  # course_document, mind_map等
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    
    # 元数据
    target_topics = db.Column(db.Text)  # JSON数组
    difficulty = db.Column(db.String(20), default='medium')
    estimated_time = db.Column(db.Integer, default=30)
    
    # 状态
    is_favorite = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'resource_type': self.resource_type,
            'title': self.title,
            'content': self.content,
            'target_topics': json.loads(self.target_topics) if self.target_topics else [],
            'difficulty': self.difficulty,
            'estimated_time': self.estimated_time,
            'is_favorite': self.is_favorite,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LearningPathModel(db.Model):
    """学习路径模型"""
    __tablename__ = 'learning_paths_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 路径数据（JSON）
    path_data = db.Column(db.Text)  # JSON字符串
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    current_step = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'path_id': self.path_id,
            'user_id': self.user_id,
            'path_data': json.loads(self.path_data) if self.path_data else {},
            'is_active': self.is_active,
            'current_step': self.current_step,
            'completion_rate': self.completion_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AssessmentReportModel(db.Model):
    """学习评估报告模型"""
    __tablename__ = 'assessment_reports_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 报告数据（JSON）
    report_data = db.Column(db.Text)  # JSON字符串
    
    # 基本指标
    overall_score = db.Column(db.Float, default=0.0)
    level = db.Column(db.String(20), default='poor')
    
    # 时间戳
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_data': json.loads(self.report_data) if self.report_data else {},
            'overall_score': self.overall_score,
            'level': self.level,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None
        }


class ChatHistoryModel(db.Model):
    """对话历史模型"""
    __tablename__ = 'chat_history_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    
    # 对话内容
    role = db.Column(db.String(20), nullable=False)  # user/assistant/system
    content = db.Column(db.Text)
    
    # 元数据
    agent_type = db.Column(db.String(50))  # profile/tutor/resource
    meta_info = db.Column(db.Text)  # JSON (避免使用metadata关键字)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'agent_type': self.agent_type,
            'meta_info': json.loads(self.meta_info) if self.meta_info else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DigitalHumanVideoTaskModel(db.Model):
    __tablename__ = 'digital_human_video_tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    topic = db.Column(db.String(200), default="")
    prompt = db.Column(db.Text)
    word_count = db.Column(db.Integer, default=120)

    task_id = db.Column(db.String(100), unique=True, nullable=False)
    task_status = db.Column(db.String(10), default="1")
    code = db.Column(db.Integer, default=0)
    message = db.Column(db.String(200), default="")

    payload = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        payload = {}
        if self.payload:
            try:
                payload = json.loads(self.payload)
            except Exception:
                payload = {}

        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic': self.topic,
            'prompt': self.prompt,
            'word_count': self.word_count,
            'task_id': self.task_id,
            'task_status': self.task_status,
            'code': self.code,
            'message': self.message,
            'payload': payload,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeDocumentModel(db.Model):
    """知识库文档模型"""
    __tablename__ = 'knowledge_documents_agent'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), default='')
    file_size = db.Column(db.Integer, default=0)
    content_hash = db.Column(db.String(64), index=True)

    status = db.Column(db.String(20), default='indexed')
    chunk_count = db.Column(db.Integer, default=0)
    summary = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'title': self.title,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'content_hash': self.content_hash,
            'status': self.status,
            'chunk_count': self.chunk_count,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeChunkModel(db.Model):
    """知识库文档分块模型"""
    __tablename__ = 'knowledge_chunks_agent'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    chunk_index = db.Column(db.Integer, default=0)
    content = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text)
    vector_meta = db.Column(db.Text)
    char_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'vector_meta': json.loads(self.vector_meta) if self.vector_meta else {},
            'char_count': self.char_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
