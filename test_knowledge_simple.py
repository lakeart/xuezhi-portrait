#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识问答API简单测试脚本
"""

import json
import requests
import time

def test_knowledge_api():
    """测试知识问答API"""
    
    # API地址
    base_url = "http://localhost:5000"
    api_url = f"{base_url}/agent/knowledge/ask"
    
    # 测试问题列表
    test_questions = [
        "什么是机器学习？",
        "如何学习Python编程？",
        "推荐几个好用的代码编辑器",
        "深度学习和机器学习有什么区别？",
        "人工智能的发展前景如何？"
    ]
    
    print("🚀 开始测试知识问答API\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"📝 测试问题 {i}: {question}")
        
        # 构建请求数据
        payload = {
            "question": question,
            "enable_search": True,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        try:
            # 发送请求
            start_time = time.time()
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            end_time = time.time()
            
            print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
            print(f"📊 HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    print("✅ 请求成功")
                    
                    # 显示推理过程（如果有）
                    if data.get('reasoning_content'):
                        print(f"🤔 推理过程: {data['reasoning_content'][:100]}...")
                    
                    # 显示回答内容
                    if data.get('content'):
                        print(f"💡 回答内容: {data['content'][:200]}...")
                    
                    # 显示使用统计
                    usage = data.get('usage', {})
                    if usage:
                        print(f"📈 Token使用: 总计{usage.get('total_tokens', 0)}, 输入{usage.get('prompt_tokens', 0)}, 输出{usage.get('completion_tokens', 0)}")
                    
                    print(f"🆔 会话ID: {data.get('sid', 'N/A')}")
                else:
                    print(f"❌ API返回错误: {data.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('error', '未知错误')}")
                except:
                    print(f"   响应内容: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print("⏰ 请求超时")
        except requests.exceptions.ConnectionError:
            print("🔌 连接失败 - 请确认Flask服务器已启动")
        except Exception as e:
            print(f"🚨 测试异常: {e}")
        
        print("-" * 80)
        if i < len(test_questions):
            time.sleep(1)  # 避免请求过于频繁
    
    print("🎉 知识问答API测试完成!")


if __name__ == '__main__':
    test_knowledge_api()