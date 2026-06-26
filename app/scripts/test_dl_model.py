import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入模型
from app.models.deep_learning import dl_model

def test_model():
    """测试深度学习模型"""
    print("测试深度学习模型...")
    
    # 测试学生数据
    student_data = {
        'username': 'test_student',
        'learning_style': {
            'visual_verbal': 'visual',
            'active_reflective': 'active'
        },
        'preferred_time': ['晚上'],
        'learning_rate': 7
    }
    
    # 测试知识点数据
    topics = [
        {'topic': '数据结构', 'mastery': 45},
        {'topic': '算法设计', 'mastery': 60},
        {'topic': '计算机网络', 'mastery': 75},
        {'topic': '操作系统', 'mastery': 50},
        {'topic': '数据库原理', 'mastery': 65}
    ]
    
    # 测试学习计划推荐
    print("\n1. 测试学习计划推荐:")
    schedule = dl_model.recommend_optimal_schedule(student_data, topics, days=3)
    print(json.dumps(schedule, ensure_ascii=False, indent=2))
    
    # 测试知识点掌握度预测
    print("\n2. 测试知识点掌握度预测:")
    predictions = dl_model.predict_knowledge_trend(student_data, topics[:2], days=15)
    print(json.dumps(predictions, ensure_ascii=False, indent=2))
    
    # 测试个性化学习策略
    print("\n3. 测试个性化学习策略:")
    strategies = dl_model.generate_personalized_strategies(student_data, topics)
    print(json.dumps(strategies, ensure_ascii=False, indent=2))
    
    print("\n深度学习模型测试完成!")

if __name__ == "__main__":
    test_model() 