from app import db
from datetime import datetime

class WrongQuestion(db.Model):
    """错题本 - 自动收集学生答错的题目"""
    __tablename__ = 'wrong_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    
    # 错题详情（冗余存储，便于快速查询）
    question_topic = db.Column(db.String(50))
    question_style = db.Column(db.String(20))
    question_content = db.Column(db.Text)
    question_options = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    student_answer = db.Column(db.Text)
    
    # 错因分析
    error_type = db.Column(db.String(50))  # 粗心、概念不清、方法不当、完全不会
    error_note = db.Column(db.Text)  # 学生自己的错因备注
    
    # 学习状态
    is_mastered = db.Column(db.Boolean, default=False)  # 是否已掌握
    review_count = db.Column(db.Integer, default=0)  # 复习次数
    last_review_time = db.Column(db.DateTime)  # 上次复习时间
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    student = db.relationship('User', backref='wrong_questions')
    question = db.relationship('Question')
    
    # 唯一约束：同一学生对同一题目只记录一次
    __table_args__ = (
        db.UniqueConstraint('student_id', 'question_id', name='unique_wrong_question'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'question_topic': self.question_topic,
            'question_style': self.question_style,
            'question_content': self.question_content,
            'question_options': self.question_options,
            'correct_answer': self.correct_answer,
            'student_answer': self.student_answer,
            'error_type': self.error_type,
            'error_note': self.error_note,
            'is_mastered': self.is_mastered,
            'review_count': self.review_count,
            'last_review_time': self.last_review_time.isoformat() if self.last_review_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Achievement(db.Model):
    """成就定义"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)  # 成就代码
    name = db.Column(db.String(50))  # 成就名称
    description = db.Column(db.String(200))  # 成就描述
    icon = db.Column(db.String(50))  # 图标类名
    category = db.Column(db.String(20))  # 类别：learning/streak/accuracy/mastery/special
    
    # 解锁条件
    condition_type = db.Column(db.String(30))  # question_count/streak_days/accuracy/mastery_count
    condition_value = db.Column(db.Integer)  # 条件阈值
    
    # 奖励
    points = db.Column(db.Integer, default=10)  # 积分奖励
    badge_color = db.Column(db.String(20), default='bronze')  # 铜/银/金/钻石
    
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'points': self.points,
            'badge_color': self.badge_color
        }


class UserAchievement(db.Model):
    """用户成就"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'))
    earned_at = db.Column(db.DateTime, default=datetime.now)  # 解锁时间
    
    # 额外信息
    progress_value = db.Column(db.Integer)  # 达成时的数值
    
    # 关系
    user = db.relationship('User', backref='achievements')
    achievement = db.relationship('Achievement')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'achievement': self.achievement.to_dict() if self.achievement else None,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'progress_value': self.progress_value
        }


class UserPoints(db.Model):
    """用户积分"""
    __tablename__ = 'user_points'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    total_points = db.Column(db.Integer, default=0)  # 总积分
    current_streak = db.Column(db.Integer, default=0)  # 当前连续学习天数
    longest_streak = db.Column(db.Integer, default=0)  # 最长连续学习天数
    last_active_date = db.Column(db.Date)  # 最后活跃日期
    
    # 学习统计
    total_questions = db.Column(db.Integer, default=0)  # 总答题数
    correct_questions = db.Column(db.Integer, default=0)  # 答对题数
    total_study_time = db.Column(db.Integer, default=0)  # 总学习时长(分钟)
    
    user = db.relationship('User', backref='points_record')
    
    def to_dict(self):
        return {
            'total_points': self.total_points,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'total_questions': self.total_questions,
            'correct_questions': self.correct_questions,
            'accuracy': round(self.correct_questions / self.total_questions * 100, 1) if self.total_questions > 0 else 0,
            'total_study_time': self.total_study_time
        }
