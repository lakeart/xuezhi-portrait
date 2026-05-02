"""系统检查和验证脚本"""
import sys
import os
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    print("1. 检查Python版本...", end=" ")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"[OK] {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[FAIL] 需要Python 3.8+，当前版本 {version.major}.{version.minor}")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n2. 检查依赖包...")
    required_packages = [
        ('flask', 'Flask'),
        ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
        ('flask_login', 'Flask-Login'),
        ('torch', 'PyTorch'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('sklearn', 'scikit-learn')
    ]
    
    all_ok = True
    for module_name, package_name in required_packages:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"   [OK] {package_name} ({version})")
        except ImportError:
            print(f"   [FAIL] {package_name} - 未安装")
            all_ok = False
    
    return all_ok


def check_file_structure():
    """检查文件结构"""
    print("\n3. 检查文件结构...")
    required_dirs = [
        'app',
        'app/models',
        'app/routes',
        'app/static',
        'app/templates',
        'app/utils',
        'instance',
        'doc'
    ]
    
    required_files = [
        'app/__init__.py',
        'run.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"   [OK] {dir_path}/")
        else:
            print(f"   [FAIL] {dir_path}/ - 目录不存在")
            all_ok = False
    
    for file_path in required_files:
        if Path(file_path).is_file():
            print(f"   [OK] {file_path}")
        else:
            print(f"   [FAIL] {file_path} - 文件不存在")
            all_ok = False
    
    return all_ok


def check_model_files():
    """检查模型文件"""
    print("\n4. 检查深度学习模型文件...")
    model_dir = Path('app/static/models')
    
    if not model_dir.is_dir():
        print("   ✗ 模型目录不存在")
        return False
    
    model_files = ['mastery_model.pth', 'schedule_model.pth', 'feature_mapping.pkl']
    all_ok = True
    
    for model_file in model_files:
        file_path = model_dir / model_file
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"   [OK] {model_file} ({size} bytes)")
        else:
            print(f"   [FAIL] {model_file} - 不存在")
            all_ok = False
    
    return all_ok


def test_flask_app():
    """测试Flask应用"""
    print("\n5. 测试Flask应用...", end=" ")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from app import create_app
        
        app = create_app()
        
        # 测试客户端
        client = app.test_client()
        response = client.get('/')
        
        if response.status_code == 200:
            print("[OK] Flask应用正常")
            return True
        else:
            print(f"[FAIL] 返回状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] 错误: {str(e)}")
        return False


def check_database():
    """检查数据库"""
    print("\n6. 检查数据库...")
    db_path = Path('instance/quiz_system.db')
    
    if db_path.is_file():
        size = db_path.stat().st_size
        print(f"   [OK] 数据库文件存在 ({size} bytes)")
        return True
    else:
        print("   [WARN] 数据库文件不存在，需要运行 set_db.py 初始化")
        return True  # 这不是致命错误


def main():
    """主函数"""
    print("=" * 70)
    print("学智画像：教育大数据赋能高校学情可视分析系统 - 系统检查")
    print("=" * 70)
    
    results = []
    results.append(("Python版本", check_python_version()))
    results.append(("依赖包", check_dependencies()))
    results.append(("文件结构", check_file_structure()))
    results.append(("模型文件", check_model_files()))
    results.append(("Flask应用", test_flask_app()))
    results.append(("数据库", check_database()))
    
    print("\n" + "=" * 70)
    print("检查结果汇总:")
    print("=" * 70)
    
    all_passed = True
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n[OK] 所有检查通过！系统可以正常运行。")
        print("\n使用以下命令启动系统:")
        print("  1. 初始化数据库: python set_db.py")
        print("  2. 启动系统:     python run.py")
        return 0
    else:
        print("\n[FAIL] 部分检查失败，请解决问题后重试。")
        return 1


if __name__ == '__main__':
    exit(main())
