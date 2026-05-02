"""测试运行脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("学智画像：教育大数据赋能高校学情可视分析系统 - 测试套件")
    print("=" * 60)
    
    # 运行测试
    result = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '--disable-pytest-warnings'
    ])
    
    print("\n" + "=" * 60)
    if result == 0:
        print("所有测试通过！")
    else:
        print(f"有测试失败 (退出码: {result})")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    exit(run_tests())
