import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import json
from datetime import datetime
from markupsafe import Markup

# 可选：本地开发通过 .env 注入环境变量（不强依赖）
try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

# 创建数据库实例
db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.unauthorized_handler
def unauthorized_callback():
    """处理未授权访问 - API请求返回JSON，页面请求重定向到登录页"""
    if request.is_json:
        return jsonify({'error': '需要登录才能使用此功能', 'code': 'LOGIN_REQUIRED'}), 401
    else:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

def create_app():
    # 创建Flask应用实例
    app = Flask(__name__)

    # 优先加载项目根目录 .env（如果存在）
    if load_dotenv:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        load_dotenv(os.path.join(project_root, '.env'), override=False)
    
    # 配置数据库
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    
    # 确保 instance 目录存在
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'quiz_system.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 注册蓝图
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.quiz import quiz_bp
    from app.routes.analysis import analysis_bp
    from app.routes.student import student_bp
    from app.routes.intelligent_assistant import bp as intelligent_bp
    from app.routes.test import bp as test_bp
    from app.routes.nav import nav_bp
    from app.routes.features import features_bp
    from app.routes.extra_features import extra_bp
    from app.routes.agent_system import bp as agent_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(intelligent_bp, url_prefix='/intelligent-assistant')
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(nav_bp)
    app.register_blueprint(features_bp, url_prefix='/features')
    app.register_blueprint(extra_bp, url_prefix='/extra')
    app.register_blueprint(agent_bp, url_prefix='/agent')
    
    # 创建数据库表
    with app.app_context():
        # 先导入模型，确保 SQLAlchemy 已注册所有表
        from app.models.agent_models import (
            StudentProfileModel,
            LearningResourceModel,
            LearningPathModel,
            AssessmentReportModel,
            ChatHistoryModel,
            DigitalHumanVideoTaskModel,
            KnowledgeDocumentModel,
            KnowledgeChunkModel,
        )

        db.create_all()

        # 确保演示账号始终可登录。比赛演示环境可能复用旧数据库，
        # 这里以幂等方式补齐/修正默认账号与密码。
        from app.models.user import User
        demo_users = [
            ('admin', 'admin@example.com', 'admin123', 'admin'),
            ('teacher', 'teacher@example.com', 'teacher123', 'teacher'),
            ('student', 'student@example.com', 'student123', 'student'),
        ]
        from werkzeug.security import generate_password_hash
        changed_demo_users = False
        for username, email, password, role in demo_users:
            with db.session.no_autoflush:
                user = User.query.filter_by(username=username).first()
                if user is None:
                    user = User.query.filter_by(email=email).first()
                    if user is not None and user.username != username:
                        user.username = username
                        changed_demo_users = True

            if user is None:
                demo_email = email
                with db.session.no_autoflush:
                    email_owner = User.query.filter_by(email=email).first()
                if email_owner is not None:
                    demo_email = f'{username}.demo@example.com'
                db.session.add(User(username=username, email=demo_email, password=password, role=role))
                changed_demo_users = True
                continue

            with db.session.no_autoflush:
                email_owner = User.query.filter(User.email == email, User.id != user.id).first()
            if user.email != email and email_owner is None:
                user.email = email
                changed_demo_users = True
            if user.role != role:
                user.role = role
                changed_demo_users = True
            if not user.verify_password(password):
                user.password_hash = generate_password_hash(password)
                changed_demo_users = True

        if changed_demo_users:
            db.session.commit()

        # 初始化成就系统
        from app.utils.achievement_checker import init_achievements
        init_achievements()
        # 导入智能体模型以确保表创建
        from app.models.agent_models import (
            StudentProfileModel,
            LearningResourceModel,
            LearningPathModel,
            AssessmentReportModel,
            ChatHistoryModel,
            DigitalHumanVideoTaskModel,
            KnowledgeDocumentModel,
            KnowledgeChunkModel,
        )
    
    # 添加自定义过滤器
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        """将换行符转换为HTML的<br>标签"""
        if not s:
            return ""
        return Markup(s.replace('\n', '<br>'))
    
    @app.template_filter('from_json')
    def from_json(s):
        try:
            if s:
                return json.loads(s)
            return {}
        except:
            return {}
    
    @app.context_processor
    def utility_processor():
        """添加实用函数到模板上下文"""
        def now():
            """返回当前时间"""
            return datetime.now()
        
        return {'now': now}
    
    return app 
