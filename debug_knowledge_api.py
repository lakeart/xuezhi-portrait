#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识问答API调试脚本
"""

import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routes.agent_system import _call_spark_knowledge_api

def test_knowledge_function():
    """直接测试知识问答函数"""
    
    print("🔧 直接测试知识问答函数")
    
    # 测试参数
    app_id = "f338fad9"
    api_key = "e4c1da00d265ae704d875bbf508e7e68"
    api_secret = "ZDJlMTJlNzE2NjViNGE5M2YzYmIxMjUw"
    question = "什么是机器学习？"
    
    try:
        # 调用函数
        result = _call_spark_knowledge_api(
            app_id=app_id,
            api_key=api_key,
            api_secret=api_secret,
            question=question,
            enable_search=True,
            temperature=0.7,
            max_tokens=4096
        )
        
        print("✅ 函数调用成功")
        print(f"📊 返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('error'):
            print(f"❌ 函数返回错误: {result['error']}")
        else:
            print(f"💡 回答内容: {result.get('content', '')[:200]}...")
            print(f"🤔 推理过程: {result.get('reasoning_content', '')[:100]}...")
            print(f"📈 Token统计: {result.get('usage', {})}")
            print(f"🆔 会话ID: {result.get('sid', '')}")
            
    except Exception as e:
        print(f"❌ 函数调用异常: {e}")
        import traceback
        traceback.print_exc()


def test_variable_definitions():
    """测试变量定义"""
    
    print("🔍 检查变量定义")
    
    try:
        from app.routes.agent_system import XFYUN_SPARK_APP_ID, XFYUN_SPARK_API_KEY, XFYUN_SPARK_API_SECRET
        
        print(f"✅ XFYUN_SPARK_APP_ID: {XFYUN_SPARK_APP_ID}")
        print(f"✅ XFYUN_SPARK_API_KEY: {XFYUN_SPARK_API_KEY[:10]}...")
        print(f"✅ XFYUN_SPARK_API_SECRET: {XFYUN_SPARK_API_SECRET[:10]}...")
        
    except ImportError as e:
        print(f"❌ 变量导入失败: {e}")
    except Exception as e:
        print(f"❌ 变量检查异常: {e}")


if __name__ == '__main__':
    print("🚀 知识问答API调试")
    print("=" * 50)
    
    test_variable_definitions()
    print("-" * 30)
    test_knowledge_function()
    
    print("🎉 调试完成")