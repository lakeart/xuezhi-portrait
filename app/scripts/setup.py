import os
import sys
import subprocess
import argparse

def install_dependencies():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成!")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {str(e)}")
        sys.exit(1)

def train_models():
    """训练深度学习模型"""
    print("正在训练深度学习模型...")
    try:
        # 确保脚本目录存在
        os.makedirs("app/scripts", exist_ok=True)
        
        # 运行训练脚本
        subprocess.check_call([sys.executable, "app/scripts/train_dl_model.py"])
        print("模型训练完成!")
    except subprocess.CalledProcessError as e:
        print(f"模型训练失败: {str(e)}")
        sys.exit(1)

def create_directory_structure():
    """创建必要的目录结构"""
    print("创建项目目录结构...")
    directories = [
        "app/static/models",
        "app/scripts"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("目录结构创建完成!")

def setup_environment():
    """设置环境"""
    print("设置项目环境...")
    
    # 创建目录结构
    create_directory_structure()
    
    # 安装依赖
    install_dependencies()
    
    # 训练模型
    train_models()
    
    print("环境设置完成!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="设置项目环境和训练模型")
    parser.add_argument("--dependencies-only", action="store_true", help="仅安装依赖")
    parser.add_argument("--train-only", action="store_true", help="仅训练模型")
    
    args = parser.parse_args()
    
    if args.dependencies_only:
        install_dependencies()
    elif args.train_only:
        train_models()
    else:
        setup_environment() 