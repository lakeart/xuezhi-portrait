"""
能力测试路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from collections import Counter

bp = Blueprint('test', __name__)


TEST_TYPE_LABELS = {
    'programming': '编程基础',
    'math': '数学逻辑',
    'english': '英语能力',
    'algorithm': '算法思维',
    'computer_network': '计算机网络',
    'database_system': '数据库系统',
    'electronic_information': '电子信息基础',
    'ai_foundation': '人工智能基础',
    'data_analysis': '数据分析建模',
    'civil_aviation_ops': '民航运行管理',
    'air_traffic_control': '空中交通管理',
    'flight_dispatch': '飞行签派基础',
    'aviation_maintenance': '航空机务与适航'
}


def _normalize_answers(raw_answers):
    answers = []
    for item in raw_answers or []:
        if not isinstance(item, dict):
            continue
        answers.append({
            'question': item.get('question', ''),
            'selected_option': item.get('selected_option'),
            'correct_option': item.get('correct_option'),
            'is_correct': bool(item.get('is_correct')),
            'difficulty': item.get('difficulty', '中等'),
            'tag': item.get('tag', '综合能力'),
            'explanation': item.get('explanation', '')
        })
    return answers


def _build_assessment_feedback(test_type, answers):
    total_count = len(answers)
    correct_count = sum(1 for item in answers if item.get('is_correct'))
    score = int(round(correct_count / total_count * 100)) if total_count else 0

    difficulty_counter = Counter()
    difficulty_correct = Counter()
    weak_tag_counter = Counter()
    strong_tag_counter = Counter()

    for item in answers:
        difficulty = item.get('difficulty', '中等')
        tag = item.get('tag', '综合能力')
        difficulty_counter[difficulty] += 1
        if item.get('is_correct'):
            difficulty_correct[difficulty] += 1
            strong_tag_counter[tag] += 1
        else:
            weak_tag_counter[tag] += 1

    difficulty_breakdown = []
    preferred_order = {'基础': 0, '中等': 1, '进阶': 2, '挑战': 3}
    ordered_difficulties = sorted(
        difficulty_counter.keys(),
        key=lambda item: (preferred_order.get(item, 99), item)
    )
    for difficulty in ordered_difficulties:
        total = difficulty_counter.get(difficulty, 0)
        if total == 0:
            continue
        correct = difficulty_correct.get(difficulty, 0)
        difficulty_breakdown.append({
            'difficulty': difficulty,
            'total': total,
            'correct': correct,
            'accuracy': int(round(correct / total * 100))
        })

    top_weak_tags = [tag for tag, _ in weak_tag_counter.most_common(3)]
    top_strong_tags = [tag for tag, _ in strong_tag_counter.most_common(3)]
    test_label = TEST_TYPE_LABELS.get(test_type, '综合测试')

    strengths = []
    if score >= 85:
        strengths.append('基础概念掌握较为扎实，能够较稳定地完成大学课程中的常规题目。')
    elif score >= 70:
        strengths.append('具备较好的课程基础，面对中等难度问题有较高完成度。')
    else:
        strengths.append('已具备入门基础，适合通过分层训练逐步提升。')

    if top_strong_tags:
        strengths.append(f"当前表现较好的能力维度集中在：{'、'.join(top_strong_tags)}。")
    else:
        strengths.append('对基础题型的识别较快，具备继续强化的学习潜力。')

    weaknesses = []
    if top_weak_tags:
        weaknesses.append(f"当前主要薄弱点集中在：{'、'.join(top_weak_tags)}。")
    if any(item['difficulty'] in {'进阶', '挑战'} and not item['is_correct'] for item in answers):
        weaknesses.append('面对进阶与挑战题时稳定性不足，需要加强迁移应用与推理过程训练。')
    if not weaknesses:
        weaknesses.append('目前没有明显短板，可以进一步通过高难度题组拉开优势。')

    suggestions = [
        f'建议围绕“{test_label}”继续做 2 到 3 轮专题练习，并优先复盘错题原因。',
        '将错题按照知识点标签整理为复习卡片，下一轮训练先做同类迁移题。',
        '结合学习画像与资源生成模块，为薄弱知识点自动生成讲义、题单或思维导图。'
    ]
    if top_weak_tags:
        suggestions[0] = f"建议优先补强 {'、'.join(top_weak_tags)}，再进入综合应用训练。"

    review_highlights = []
    for item in answers:
        if not item.get('is_correct'):
            review_highlights.append({
                'question': item.get('question', ''),
                'tag': item.get('tag', '综合能力'),
                'difficulty': item.get('difficulty', '中等'),
                'explanation': item.get('explanation', '') or '建议回到相关知识点重新梳理概念，再完成同类题复练。'
            })
        if len(review_highlights) >= 3:
            break

    return {
        'success': True,
        'score': score,
        'correct_count': correct_count,
        'total_count': total_count,
        'analysis': {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'difficulty_breakdown': difficulty_breakdown,
            'tag_focus': top_weak_tags,
            'fit_to_track': '测试结果可直接回流学习画像与学习路径模块，用于个性化资源推送和多智能体协同调度。'
        },
        'suggestions': suggestions,
        'review_highlights': review_highlights
    }

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
    answers = _normalize_answers(data.get('answers', []))
    test_type = data.get('type', 'comprehensive')
    return jsonify(_build_assessment_feedback(test_type, answers))
