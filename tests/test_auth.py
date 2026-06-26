"""认证功能测试"""
from app.models.user import User
from app import db


def test_register(client, app):
    """测试用户注册"""
    with app.app_context():
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm': 'password123',
            'role': 'student'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # 检查用户是否创建
        assert User.query.filter_by(username='newuser').first() is not None


def test_login_logout(client, app):
    """测试用户登录和登出"""
    with app.app_context():
        # 先创建一个用户
        user = User(
            username='testlogin',
            email='login@example.com',
            password='password123',
            role='student'
        )
        db.session.add(user)
        db.session.commit()
    
    # 测试登录
    response = client.post('/auth/login', data={
        'username': 'testlogin',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 测试登出
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
