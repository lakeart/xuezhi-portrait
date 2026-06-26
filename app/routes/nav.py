"""
统一导航路由 - 提供导航数据和菜单配置
"""
from flask import Blueprint, jsonify
from flask_login import current_user

nav_bp = Blueprint('nav', __name__)

@nav_bp.route('/api/nav-data')
def get_nav_data():
    """获取导航配置数据"""
    # 根据用户角色返回不同的导航配置
    is_authenticated = current_user.is_authenticated if current_user else False
    is_teacher = current_user.is_teacher() if is_authenticated else False
    
    # 基础导航
    nav_items = [
        {
            'id': 'home',
            'title': '首页',
            'icon': '🏠',
            'url': '/',
            'active': False
        }
    ]
    
    if is_authenticated:
        # 已登录用户的导航
        nav_items.extend([
            {
                'id': 'qa',
                'title': '智能问答',
                'icon': '🤖',
                'url': '/intelligent-assistant',
                'active': False
            },
            {
                'id': 'test',
                'title': '能力测试',
                'icon': '📝',
                'url': '/test/assessment',
                'active': False
            },
            {
                'id': 'report',
                'title': '学习报告',
                'icon': '📊',
                'url': '/analysis/report',
                'active': False
            },
            {
                'id': 'plan',
                'title': '学习计划',
                'icon': '📋',
                'url': '/student/learning-plan',
                'active': False
            }
        ])
        
        # 教师专属导航
        if is_teacher:
            nav_items.append({
                'id': 'dashboard',
                'title': '数据分析',
                'icon': '📈',
                'url': '/analysis/pro',
                'active': False,
                'badge': '教师'
            })
    
    return jsonify({
        'nav_items': nav_items,
        'is_authenticated': is_authenticated,
        'is_teacher': is_teacher
    })
