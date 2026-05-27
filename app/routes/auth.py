from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面 - 使用专业版模板"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # 创建一个空表单对象，用于生成CSRF令牌
    form = FlaskForm()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            next_page = request.args.get('next')
            # 根据用户角色跳转到对应页面
            if next_page:
                return redirect(next_page)
            if user.is_teacher():
                return redirect(url_for('analysis.pro_dashboard'))
            else:
                return redirect(url_for('student.learning_plan'))
        flash('用户名或密码错误')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # 创建一个空表单对象，用于生成CSRF令牌
    form = FlaskForm()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return render_template('auth/register.html', form=form)
        
        # 获取角色（默认为student）
        role = request.form.get('role', 'student')
        if role not in ('student', 'teacher', 'admin'):
            role = 'student'
        
        # 创建新用户
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出登录')
    return redirect(url_for('main.index')) 