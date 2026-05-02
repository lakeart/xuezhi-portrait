"""
能力测试路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

bp = Blueprint('test', __name__)

@bp.route('/assessment')
@login_required
def assessment():
    """能力测试首页"""
    return render_template('test/assessment_pro.html')

@bp.route('/submit', methods=['POST'])
@login_required
def submit_test():
    """提交测试答案"""
    data = request.get_json()
    answers = data.get('answers', [])
    test_type = data.get('type', 'comprehensive')
    
    # 这里应该调用实际的评分逻辑
    # 目前返回模拟结果
    correct_count = len([a for a in answers if a.get('correct', False)])
    total_count = len(answers)
    score = int(correct_count / total_count * 100) if total_count > 0 else 0
    
    return jsonify({
        'success': True,
        'score': score,
        'correct_count': correct_count,
        'total_count': total_count,
        'analysis': {
            'strengths': ['基础知识掌握扎实', '概念理解准确'],
            'weaknesses': ['综合应用能力需加强', '部分知识点理解不够深入']
        },
        'suggestions': [
            '建议加强综合题目的练习',
            '注重知识点的实际应用'
        ]
    })
