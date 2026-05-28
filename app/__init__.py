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
        )

        db.create_all()

        # 初始化成就系统
        from app.utils.achievement_checker import init_achievements
        init_achievements()
    
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
