from app import db
from datetime import datetime

class Note(db.Model):
    """学习笔记"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200))  # 笔记标题
    content = db.Column(db.Text)  # 笔记内容（支持富文本）
    
    # 分类
    category = db.Column(db.String(50))  # 分类：数学、英语、编程、通用
    tags = db.Column(db.String(500))  # 标签，逗号分隔
    
    # 关联学习内容
    related_question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    related_topic = db.Column(db.String(100))  # 关联的知识点
    
    # 统计
    view_count = db.Column(db.Integer, default=0)  # 浏览次数
    like_count = db.Column(db.Integer, default=0)  # 点赞次数
    
    # 状态
    is_public = db.Column(db.Boolean, default=False)  # 是否公开
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    user = db.relationship('User', backref='notes')
    question = db.relationship('Question')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'related_topic': self.related_topic,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Notification(db.Model):
    """系统通知"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 通知内容
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    notification_type = db.Column(db.String(30))  # achievement/wrong_question/study_reminder/system
    
    # 关联
    related_id = db.Column(db.Integer)  # 关联的成就ID、错题ID等
    
    # 状态
    is_read = db.Column(db.Boolean, default=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    user = db.relationship('User', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudyReminder(db.Model):
    """学习提醒设置"""
    __tablename__ = 'study_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    
    # 提醒时间
    reminder_enabled = db.Column(db.Boolean, default=False)
    reminder_time = db.Column(db.String(10))  # 时间格式：HH:MM
    
    # 提醒频率
    frequency = db.Column(db.String(20), default='daily')  # daily/weekly/weekdays
    
    # 提醒内容偏好
    prefer_topics = db.Column(db.String(500))  # 偏好的知识点
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    last_reminded = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='study_reminder')
    
    def to_dict(self):
        return {
            'reminder_enabled': self.reminder_enabled,
            'reminder_time': self.reminder_time,
            'frequency': self.frequency,
            'prefer_topics': self.prefer_topics.split(',') if self.prefer_topics else []
        }


class UserProfile(db.Model):
    """用户资料扩展"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    
    # 基本信息
    avatar = db.Column(db.String(500))  # 头像URL
    bio = db.Column(db.String(500))  # 个人简介
    signature = db.Column(db.String(200))  # 个性签名
    
    # 学习目标
    daily_goal = db.Column(db.Integer, default=10)  # 每日目标（题数）
    weekly_goal = db.Column(db.Integer, default=50)  # 每周目标
    study_goal = db.Column(db.String(200))  # 学习目标描述
    
    # 偏好设置
    preferred_topics = db.Column(db.String(500))  # 偏好的知识点
    preferred_difficulty = db.Column(db.String(20))  # 偏好难度：简单/中等/困难
    
    # 学习偏好时间
    study_time_start = db.Column(db.String(10))  # 学习时段开始
    study_time_end = db.Column(db.String(10))  # 学习时段结束
    
    # 成就展示设置
    show_achievements = db.Column(db.Boolean, default=True)
    show_rankings = db.Column(db.Boolean, default=True)
    
    # 统计（用于展示）
    total_study_days = db.Column(db.Integer, default=0)  # 累计学习天数
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = db.relationship('User', backref='profile')
    
    def to_dict(self):
        return {
            'avatar': self.avatar,
            'bio': self.bio,
            'signature': self.signature,
            'daily_goal': self.daily_goal,
            'weekly_goal': self.weekly_goal,
            'study_goal': self.study_goal,
            'preferred_topics': self.preferred_topics.split(',') if self.preferred_topics else [],
            'preferred_difficulty': self.preferred_difficulty,
            'show_achievements': self.show_achievements,
            'show_rankings': self.show_rankings,
            'total_study_days': self.total_study_days
        }
