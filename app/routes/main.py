from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.quiz import QuizSubmission
from sqlalchemy import func, case, desc
from app import db
import json
import random
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页 - 优化版"""
    return render_template('index.html')

@main_bp.route('/home')
def home():
    """首页 - 优化版"""
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """用户仪表盘 - 根据角色跳转"""
    if current_user.is_teacher():
        return render_template('teacher_dashboard.html')
    else:
        return render_template('student_dashboard.html')
