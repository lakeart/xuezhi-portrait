from app import db
from datetime import datetime

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(10), unique=True, index=True)
    topic = db.Column(db.String(50))
    style = db.Column(db.String(20))  # 选择题、填空题、解答题、判断题、编程题
    content = db.Column(db.Text)
    options = db.Column(db.Text, nullable=True)  # 选择题的选项，JSON格式
    answer = db.Column(db.Text)
    difficulty = db.Column(db.String(10))  # 简单、中等、困难
    created_at = db.Column(db.DateTime, default=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关系
    submissions = db.relationship('QuizSubmission', backref='question', lazy='dynamic')

class QuizSubmission(db.Model):
    __tablename__ = 'quiz_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), index=True)
    student_name = db.Column(db.String(50))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    question_topic = db.Column(db.String(50))
    question_style = db.Column(db.String(20))
    error_style = db.Column(db.String(20))
    start_time = db.Column(db.DateTime)
    submit_time = db.Column(db.DateTime)
    difficulty = db.Column(db.String(10))
    score = db.Column(db.Integer)
    time_consumed = db.Column(db.Integer)  # 秒
    memory = db.Column(db.Integer)  # 内存消耗（MB）
    time_region = db.Column(db.String(10))  # 时间段：早上、中午、下午、晚上、凌晨
    
    # 用于导入数据使用
    source_question_id = db.Column(db.String(10))

class AnswerRecord(db.Model):
    __tablename__ = 'answer_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    answer_content = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, default=datetime.now)
    submit_time = db.Column(db.DateTime)
    time_consumed = db.Column(db.Integer)  # 秒
    
    # 关系
    student = db.relationship('User', backref='answer_records')
    question = db.relationship('Question') 