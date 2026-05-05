"""部署脚本"""
import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """检查部署环境"""
    print("检查部署环境...")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查依赖包
    try:
        import flask
        print(f"Flask版本: {flask.__version__}")
    except ImportError:
        print("Flask未安装")
        return False
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
    except ImportError:
        print("PyTorch未安装（可选功能）")
    
    print("核心依赖包检查完成！")
    
    print("环境检查完成！")
    return True


def setup_production():
    """设置生产环境"""
    print("\n设置生产环境...")
    
    # 创建必要的目录
    directories = ['logs', 'uploads']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"创建目录: {dir_name}")
    
    print("生产环境设置完成！")


def run_server(mode='development', host='0.0.0.0', port=5000):
    """运行服务器"""
    print(f"\n启动{mode}服务器...")
    print(f"访问地址: http://{host}:{port}")
    
    if mode == 'production':
        # 生产环境使用Gunicorn（Linux）或Waitress（Windows）
        try:
            import gunicorn
            subprocess.run([
                'gunicorn',
                '--bind', f'{host}:{port}',
                '--workers', '4',
                '--timeout', '120',
                'run:app'
            ])
        except ImportError:
            try:
                from waitress import serve
                from app import create_app
                
                app = create_app()
                serve(app, host=host, port=port)
            except ImportError:
                print("生产环境服务器未找到，使用开发模式")
                from app import create_app
                
                app = create_app()
                app.run(host=host, port=port, debug=False)
    else:
        # 开发模式
        from app import create_app
        
        app = create_app()
        app.run(host=host, port=port, debug=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='部署脚本')
    parser.add_argument('--mode', choices=['development', 'production'], 
                       default='development', help='运行模式')
    parser.add_argument('--host', default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    
    args = parser.parse_args()
    
    if check_environment():
        setup_production()
        run_server(args.mode, args.host, args.port)
