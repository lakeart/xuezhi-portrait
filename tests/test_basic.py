"""基础功能测试"""
import pytest
from app.models.user import User
from app import db


def test_home_page(client):
    """测试主页"""
    response = client.get('/')
    assert response.status_code == 200
    # 检查是否返回了HTML内容
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


def test_login_page(client):
    """测试登录页面"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert '登录'.encode('utf-8') in response.data


def test_register_page(client):
    """测试注册页面"""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert '注册'.encode('utf-8') in response.data


def test_database_creation(app):
    """测试数据库创建"""
    with app.app_context():
        # 检查数据库是否已创建
        # 使用新的SQLAlchemy API
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        assert len(table_names) > 0


def test_user_creation(app):
    """测试用户创建"""
    with app.app_context():
        # 创建测试用户
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        
        # 检查用户是否创建成功
        assert User.query.filter_by(username='testuser').first() is not None
