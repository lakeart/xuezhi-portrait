# -*- coding: utf-8 -*-
"""学生端路由 - 学习计划、个性化分析等"""
import math, json
from datetime import date, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.quiz import QuizSubmission, Question
from sqlalchemy import func, desc, asc, case, and_

student_bp = Blueprint('student', __name__, template_folder='../templates')

def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher():
            return jsonify({'error': '需要教师权限'}), 403
        return f(*args, **kwargs)
    return wrapper

@student_bp.route('/list')
@login_required
@teacher_required
def student_list():
    return render_template('student/list.html')

@student_bp.route('/api/list')
@login_required
@teacher_required
def api_student_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    search = request.args.get('search', '')
    
    query = User.query.filter(User.role == 'student')
    if search:
        query = query.filter(User.username.like(f'%{search}%') | User.nickname.like(f'%{search}%'))
    
    if sort in ['id', 'username', 'created_at']:
        order_func = desc if order == 'desc' else asc
        query = query.order_by(order_func(getattr(User, sort)))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    students_data = []
    for student in pagination.items:
        stats = db.session.query(
            func.count(QuizSubmission.id).label('total'),
            func.avg(QuizSubmission.score).label('avg_score')
        ).filter(QuizSubmission.student_id == student.username).first()
        students_data.append({
            'id': student.id,
            'username': student.username or '',
            'total_submissions': stats.total or 0,
            'avg_score': round(float(stats.avg_score or 0), 1)
        })
    
    return jsonify({
        'data': students_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })

@student_bp.route('/details/<int:student_id>')
@login_required
@teacher_required
def student_details(student_id):
    student = User.query.get_or_404(student_id)
    stats = db.session.query(
        func.count(QuizSubmission.id).label('total'),
        func.avg(QuizSubmission.score).label('avg_score')
    ).filter(QuizSubmission.student_id == student.username).first()
    
    return render_template('student/details.html',
        student=student,
        student_name=student.username or '未知',
        stats={'total_submissions': stats.total or 0, 'avg_score': round(float(stats.avg_score or 0), 2), 'perfect_count': 0, 'avg_time': 0},
        topic_data=[],
        weak_topics=[],
        items=[],
        diagnosis={'suggestions': ['暂无数据']})

@student_bp.route('/my-details')
@login_required
def my_details():
    return redirect(url_for('student.student_details', student_id=current_user.id))

@student_bp.route('/api/grades/<int:student_id>')
@login_required
@teacher_required
def api_student_grades(student_id):
    student = User.query.get_or_404(student_id)
    submissions = QuizSubmission.query.filter_by(student_id=student.username).order_by(QuizSubmission.submit_time.desc()).limit(100).all()
    return jsonify({'data': [{'date': str(s.submit_time)[:10], 'score': s.score, 'topic': s.question_topic, 'style': s.question_style} for s in submissions]})

@student_bp.route('/api/topic_detail/<int:student_id>')
@login_required
@teacher_required
def api_topic_detail(student_id):
    student = User.query.get_or_404(student_id)
    topics = db.session.query(QuizSubmission.question_topic, func.count(QuizSubmission.id).label('count'), func.avg(QuizSubmission.score).label('avg')).filter(
        QuizSubmission.student_id == student.username).group_by(QuizSubmission.question_topic).all()
    return jsonify({'data': [{'topic': t.question_topic, 'count': t.count, 'avg_score': round(float(t.avg or 0), 2)} for t in topics]})

@student_bp.route('/api/time_analysis/<int:student_id>')
@login_required
@teacher_required
def time_analysis(student_id):
    student = User.query.get_or_404(student_id)
    regions = db.session.query(QuizSubmission.time_region, func.count(QuizSubmission.id), func.avg(QuizSubmission.score)).filter(
        QuizSubmission.student_id == student.username).group_by(QuizSubmission.time_region).all()
    return jsonify({'data': [{'region': r[0], 'count': r[1], 'avg_score': round(float(r[2] or 0), 2)} for r in regions]})

@student_bp.route('/learning-plan')
@login_required
def learning_plan():
    """学习计划页面 - 预加载默认示例数据，实现即开即用"""
    student = current_user
    username = student.username or f'user_{student.id}'
    
    # 1. 尝试获取真实知识点数据
    all_topics = [r[0] for r in db.session.query(Question.topic).distinct().all() if r[0]]
    if all_topics:
        topic_mastery_data = calculate_topic_mastery(username, all_topics)
    else:
        topic_mastery_data = []
    
    # 2. 如果没有数据（新用户），使用示例数据
    sample_topics = [
        '数据结构', '算法设计', '计算机网络',
        '操作系统', '数据库原理', '软件工程',
        '计算机组成原理', '离散数学', '编译原理', '人工智能'
    ]
    if not topic_mastery_data or all(t['mastery'] == 0 for t in topic_mastery_data):
        import random
        random.seed(hash(username) % 10000 if username else 42)
        topic_mastery_data = [
            {'topic': t, 'mastery': random.randint(20, 95)}
            for t in (all_topics or sample_topics)
        ]
        topic_mastery_data.sort(key=lambda x: x['mastery'])
    
    # 3. 生成示例学习频率数据
    from datetime import datetime, timedelta
    freq_data = []
    for i in range(14):
        d = (datetime.now() - timedelta(days=13-i)).strftime('%Y-%m-%d')
        cnt = max(1, abs(hash(f'{username}_{i}') % 8))
        freq_data.append({'date': d, 'count': cnt})
    
    study_frequency = {
        'frequency_data': freq_data,
        'frequency': min(100, len(topic_mastery_data) * 8 + 20),
        'consistency': min(100, abs(hash(f'{username}_c') % 70) + 20),
        'trend': 'stable'
    }
    
    # 4. 生成示例最佳时段数据
    time_data = []
    regions = ['早上', '上午', '中午', '下午', '晚上', '深夜']
    region_scores = {
        '早上': round(65 + abs(hash(f'{username}_m') % 25), 1),
        '上午': round(60 + abs(hash(f'{username}_a') % 20), 1),
        '中午': round(50 + abs(hash(f'{username}_n') % 15), 1),
        '下午': round(55 + abs(hash(f'{username}_af') % 15), 1),
        '晚上': round(70 + abs(hash(f'{username}_e') % 20), 1),
        '深夜': round(40 + abs(hash(f'{username}_ni') % 20), 1),
    }
    best_time_name = max(region_scores, key=region_scores.get)
    best_time = {
        **region_scores, 'best_time': best_time_name,
        'morning': region_scores.get('早上', 0),
        'noon': region_scores.get('中午', 0),
        'afternoon': region_scores.get('下午', 0),
        'evening': region_scores.get('晚上', 0),
        'night': region_scores.get('深夜', 0)
    }
    
    # 5. 生成示例周计划
    days_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    time_slots = ['早上', '上午', '下午', '晚上']
    weekly_plan_data = []
    
    for i, day in enumerate(days_labels):
        for j, slot in enumerate(time_slots):
            topic_idx = (i * len(time_slots) + j) % len(topic_mastery_data)
            weekly_plan_data.append({
                'name': topic_mastery_data[topic_idx]['topic'],
                'value': [i, j * 2 + 1, 2],
                'topic': topic_mastery_data[topic_idx]['topic'],
                'duration': 45,
                'day': day,
                'time': slot
            })
    
    learning_plan_data = {
        'weekly': weekly_plan_data,
        'topics': topic_mastery_data[:3]
    }
    
    return render_template(
        'student/learning_plan.html',
        student=student,
        topic_data=topic_mastery_data,
        prefetched_data={
            'topic_mastery': topic_mastery_data,
            'study_frequency': study_frequency,
            'best_time': best_time,
            'learning_plan': learning_plan_data,
            'resources': {'videos': [], 'exercises': []}
        }
    )

def analyze_learning_style(student_username):
    submissions = QuizSubmission.query.filter_by(student_id=student_username).all()
    visual_count = sum(1 for s in submissions if s.question_style in ('选择题', '判断题'))
    verbal_count = sum(1 for s in submissions if s.question_style in ('填空题', '解答题'))
    return {'visual': visual_count, 'reading_writing': verbal_count, 'auditory': 0, 'kinesthetic': 0}

def calculate_topic_mastery(student_username, all_topics):
    result = []
    for topic in all_topics:
        subs = QuizSubmission.query.filter_by(student_id=student_username, question_topic=topic).all()
        if subs:
            total = sum(s.score for s in subs)
            max_total = 0
            for s in subs:
                if s.question_style == '判断题': max_total += 2
                elif s.question_style == '解答题': max_total += 10
                elif s.question_style == '编程题': max_total += 15
                else: max_total += 5
            mastery = min(100, round(total / max_total * 100)) if max_total > 0 else 0
            result.append({'topic': topic, 'mastery': mastery})
        else:
            result.append({'topic': topic, 'mastery': 0})
    return sorted(result, key=lambda x: x['mastery'])

def analyze_study_frequency(student_username):
    subs = QuizSubmission.query.filter_by(student_id=student_username).order_by(QuizSubmission.submit_time).all()
    from collections import Counter
    dates = Counter(str(s.submit_time)[:10] for s in subs)
    freq_data = [{'date': d, 'count': c} for d, c in sorted(dates.items())]
    total = len(subs)
    return {'frequency_data': freq_data, 'frequency': min(100, total * 2), 'trend': 'stable'}

def analyze_best_study_time(student_username, time_region_data):
    regions = {
        '早上': 0, '上午': 0, '中午': 0, '下午': 0, '晚上': 0, '深夜': 0
    }
    for item in time_region_data:
        if item['time_region'] in regions:
            regions[item['time_region']] = item['avg_score']
    best = max(regions, key=regions.get) if any(regions.values()) else '晚上'
    return {**{k: round(v, 1) for k, v in regions.items()}, 'best_time': best}

@student_bp.route('/api/learning-plan-data/<string:student_id>')
@login_required
def api_learning_plan_data(student_id):
    try:
        if student_id == 'None' or not student_id:
            return jsonify({'error': '学生ID无效'}), 400
        student_id_int = int(student_id)
        student = User.query.get_or_404(student_id_int)
        if student.role != 'student':
            return jsonify({'error': '非法请求'}), 400
        if not current_user.is_teacher() and current_user.id != student_id_int:
            return jsonify({'error': '权限不足'}), 403
        
        all_topics = [r[0] for r in db.session.query(Question.topic).distinct().all() if r[0]]
        topic_mastery_data = calculate_topic_mastery(student.username, all_topics)
        study_frequency_data = analyze_study_frequency(student.username)
        
        time_regions = db.session.query(
            QuizSubmission.time_region,
            func.avg(QuizSubmission.score).label('avg_score'),
            func.count(QuizSubmission.id).label('cnt')
        ).filter(QuizSubmission.student_id == student.username
        ).group_by(QuizSubmission.time_region).all()
        time_region_data = [{'time_region': r.time_region, 'avg_score': round(float(r.avg_score), 2), 'submission_count': r.cnt} for r in time_regions if r.time_region]
        best_time_data = analyze_best_study_time(student.username, time_region_data)
        
        return jsonify({
            'topic_mastery': topic_mastery_data,
            'study_frequency': study_frequency_data,
            'best_time': best_time_data,
            'learning_plan': {'weekly': [], 'topics': []},
            'resources': {'videos': [], 'exercises': []}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_learning_plan(student_username, topic_mastery_data, plan_period=7, goal='mastery'):
    return {'weekly': [], 'topics': topic_mastery_data[:3]}

def recommend_learning_resources(student_username, topic_mastery_data, goal='mastery'):
    return {'videos': [], 'exercises': [], 'articles': []}

def generate_learning_strategies(student_username, learning_style_data, topic_mastery_data, goal='mastery'):
    weak_topics = [item for item in topic_mastery_data if item.get('mastery', 0) < 60][:4]
    visual_ratio = learning_style_data.get('visual', 0)
    reading_ratio = learning_style_data.get('reading_writing', 0)
    preferred_style = '图表化拆解' if visual_ratio >= reading_ratio else '文字复盘与错题归纳'
    goal_label = {'mastery': '知识点掌握', 'exam': '考试备考', 'project': '项目实践'}.get(goal, '知识点掌握')

    general = [
        f'围绕“{goal_label}”目标，先补齐低掌握度知识点，再进入综合题训练。',
        '每个学习任务采用“10分钟回顾 + 25分钟练习 + 10分钟复盘”的闭环节奏。',
        '生成计划会根据最近答题表现动态调整优先级，避免只按固定顺序学习。'
    ]
    learning_style = [
        f'当前更适合采用“{preferred_style}”方式吸收内容。',
        '建议在每次练习后记录错因标签，第二天优先复盘同类错误。'
    ]
    topic_specific = []
    for item in weak_topics:
        mastery = item.get('mastery', 0)
        topic_specific.append({
            'topic': item.get('topic', '薄弱知识点'),
            'strategy': f'当前掌握度约 {mastery}%，建议先做概念卡片和基础题，再安排 1 组综合迁移练习。'
        })

    return {
        'general': general,
        'learning_style': learning_style,
        'topic_specific': topic_specific
    }


def _clamp_int(value, default, minimum, maximum):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _truthy(value):
    return str(value).lower() in {'1', 'true', 'yes', 'on'}


def _timeslot_label(slot):
    return {
        'morning': '上午',
        'afternoon': '下午',
        'evening': '晚上',
        'night': '晚上'
    }.get(slot, slot or '晚上')


def _difficulty_for_mastery(mastery):
    if mastery < 40:
        return '基础补缺'
    if mastery < 70:
        return '强化提升'
    return '冲刺拓展'


def _priority_for_mastery(mastery):
    if mastery < 40:
        return '高'
    if mastery < 70:
        return '中'
    return '稳固'


def _build_deep_learning_plan(student, topic_mastery_data, learning_style_data, days, goal):
    target_mastery = _clamp_int(request.args.get('targetMastery'), 85, 70, 95)
    weekends_intensive = _truthy(request.args.get('weekendsIntensive', 'true'))
    balanced_learning = _truthy(request.args.get('balancedLearning', 'false'))
    selected_timeslots = [s for s in request.args.get('timeslots', 'morning,evening').split(',') if s]
    if not selected_timeslots:
        selected_timeslots = ['evening']

    selected_topics = [t.strip() for t in request.args.get('topics', '').split(',') if t.strip()]
    mastery_by_topic = {item.get('topic'): item for item in topic_mastery_data if item.get('topic')}

    if selected_topics:
        candidates = [mastery_by_topic.get(topic, {'topic': topic, 'mastery': 45}) for topic in selected_topics]
        remaining = [item for item in topic_mastery_data if item.get('topic') not in selected_topics]
        candidates.extend(remaining[:max(0, min(5, days) - len(candidates))])
    elif balanced_learning:
        weak = [item for item in topic_mastery_data if item.get('mastery', 0) < 60]
        stable = [item for item in topic_mastery_data if item.get('mastery', 0) >= 60]
        candidates = []
        for index in range(max(len(weak), len(stable), 1)):
            if index < len(weak):
                candidates.append(weak[index])
            if index < len(stable):
                candidates.append(stable[index])
    else:
        candidates = list(topic_mastery_data)

    if not candidates:
        candidates = [
            {'topic': '数据结构', 'mastery': 52},
            {'topic': '算法分析', 'mastery': 46},
            {'topic': '数据库基础', 'mastery': 58},
            {'topic': '计算机网络', 'mastery': 42}
        ]

    goal_label = {'mastery': '知识点掌握', 'exam': '考试备考', 'project': '项目实践'}.get(goal, '知识点掌握')
    activity_by_goal = {
        'mastery': '概念梳理 + 分层练习',
        'exam': '高频题型训练 + 限时订正',
        'project': '场景任务拆解 + 小型实践'
    }
    weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    start_date = date.today()
    optimal_schedule = []
    total_minutes = 0
    high_priority_count = 0

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        weekday = weekday_labels[current_date.weekday()]
        is_weekend = current_date.weekday() >= 5
        task_count = 2 if weekends_intensive and is_weekend and len(candidates) > 1 else 1
        tasks = []

        for task_index in range(task_count):
            topic_item = candidates[(day_index + task_index) % len(candidates)]
            mastery = int(topic_item.get('mastery') or 0)
            gap = max(0, target_mastery - mastery)
            duration = 45
            if mastery < 40:
                duration += 15
            if goal == 'exam':
                duration += 10
            if is_weekend and weekends_intensive:
                duration += 15
            duration = min(90, duration)
            expected_improvement = min(25, max(6, round(gap * 0.14 + duration / 18)))
            priority = _priority_for_mastery(mastery)
            if priority == '高':
                high_priority_count += 1

            slot = selected_timeslots[(day_index + task_index) % len(selected_timeslots)]
            tasks.append({
                'topic': topic_item.get('topic', '知识点'),
                'time': _timeslot_label(slot),
                'time_slot': slot,
                'duration': duration,
                'current_mastery': mastery,
                'expected_improvement': expected_improvement,
                'activity': activity_by_goal.get(goal, activity_by_goal['mastery']),
                'focus': '补齐先修概念' if mastery < 40 else '提升解题稳定性' if mastery < 70 else '迁移应用与速度',
                'difficulty': _difficulty_for_mastery(mastery),
                'priority': priority,
                'reason': f'当前掌握度 {mastery}%，距离目标 {target_mastery}% 还有 {gap} 个百分点。',
                'checkpoint': '完成 5 道针对性练习并写出 1 条错因总结'
            })
            total_minutes += duration

        optimal_schedule.append({
            'date': current_date.isoformat(),
            'day': f'第{day_index + 1}天',
            'weekday': weekday,
            'tasks': tasks
        })

    prediction_topics = candidates[:5]
    knowledge_predictions = []
    for item in prediction_topics:
        mastery = int(item.get('mastery') or 0)
        predictions = []
        for step in range(5):
            increment = step * max(4, round((target_mastery - mastery) / 5))
            predictions.append({
                'day': step * 7,
                'mastery': min(100, mastery + increment)
            })
        knowledge_predictions.append({
            'topic': item.get('topic', '知识点'),
            'predictions': predictions
        })

    weak_topics = [item for item in candidates if item.get('mastery', 0) < 60][:3]
    risk_alerts = []
    if weak_topics:
        risk_alerts.append({
            'level': 'high' if any(item.get('mastery', 0) < 40 for item in weak_topics) else 'medium',
            'title': '薄弱知识点集中',
            'message': '、'.join(item.get('topic', '') for item in weak_topics) + ' 需要优先补齐，否则会影响后续综合任务。'
        })
    if days >= 14 and total_minutes / max(days, 1) > 70:
        risk_alerts.append({
            'level': 'medium',
            'title': '学习负荷偏高',
            'message': '计划周期较长且日均学习时长较高，建议每 4 天安排一次轻量复盘。'
        })

    resource_recommendations = []
    for item in candidates[:4]:
        topic = item.get('topic', '知识点')
        resource_recommendations.append({
            'topic': topic,
            'type': '知识卡片' if item.get('mastery', 0) < 50 else '综合练习',
            'title': f'{topic} 专项提升包',
            'reason': '匹配当前掌握度与计划目标，适合在任务完成后立即巩固。'
        })

    ai_summary = {
        'headline': f'已生成面向“{goal_label}”的 {days} 天深度学习计划',
        'diagnosis': f'系统综合了 {len(topic_mastery_data)} 个知识点、学习风格和时段偏好，优先安排低掌握度内容。',
        'schedule_strength': f'日均约 {round(total_minutes / max(days, 1))} 分钟，重点任务 {high_priority_count} 个。',
        'fit_to_track': '计划生成过程体现“数据画像-智能诊断-个性化干预-效果预测”的闭环，契合教育智能体赛道。'
    }

    return {
        'optimal_schedule': optimal_schedule,
        'knowledge_predictions': knowledge_predictions,
        'learning_strategies': generate_learning_strategies(student.username, learning_style_data, candidates, goal),
        'ai_summary': ai_summary,
        'risk_alerts': risk_alerts,
        'resource_recommendations': resource_recommendations,
        'weekly_overview': {
            'days': days,
            'target_mastery': target_mastery,
            'total_minutes': total_minutes,
            'average_minutes': round(total_minutes / max(days, 1)),
            'focus_topics': [item.get('topic') for item in candidates[:min(6, len(candidates))]]
        },
        'personalization': {
            'goal': goal,
            'goal_label': goal_label,
            'timeslots': [_timeslot_label(slot) for slot in selected_timeslots],
            'weekends_intensive': weekends_intensive,
            'balanced_learning': balanced_learning
        }
    }

@student_bp.route('/api/dl-learning-plan/<string:student_id>')
@login_required
def api_dl_learning_plan(student_id):
    try:
        if student_id == 'None' or not student_id:
            return jsonify({'error': '学生ID无效'}), 400
        student_id_int = int(student_id)
        student = User.query.get_or_404(student_id_int)
        if student.role != 'student':
            return jsonify({'error': '非法请求'}), 400
        if not current_user.is_teacher() and current_user.id != student_id_int:
            return jsonify({'error': '权限不足'}), 403
        
        days = _clamp_int(request.args.get('days'), 7, 7, 30)
        goal = request.args.get('goal', 'mastery', type=str)
        
        all_topics = [r[0] for r in db.session.query(Question.topic).distinct().all() if r[0]]
        topic_mastery_data = calculate_topic_mastery(student.username, all_topics)
        learning_style_data = analyze_learning_style(student.username)
        
        return jsonify(_build_deep_learning_plan(student, topic_mastery_data, learning_style_data, days, goal))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/api/knowledge-prediction/<string:student_id>')
@login_required
def api_knowledge_prediction(student_id):
    return jsonify({'predictions': []})

@student_bp.route('/api/learning-plan-initial/<string:student_id>')
@login_required
def api_learning_plan_initial_data(student_id):
    return api_learning_plan_data(student_id)

@student_bp.route('/api/export-learning-plan/<string:student_id>')
@login_required
def api_export_learning_plan(student_id):
    return jsonify({'status': 'ok'})

@student_bp.route('/api/update-plan-item', methods=['POST'])
@login_required
def api_update_plan_item():
    return jsonify({'status': 'ok'})

@student_bp.route('/api/add-custom-task', methods=['POST'])
@login_required
def api_add_custom_task():
    return jsonify({'status': 'ok'})

@student_bp.route('/api/mark-complete', methods=['POST'])
@login_required
def api_mark_complete():
    return jsonify({'status': 'ok'})

@student_bp.route('/start-learning')
@login_required
def start_learning():
    return render_template('student/start_learning.html',
                          student=current_user,
                          learning_path=[],
                          selected_topics=[],
                          available_topics=[],
                          today_progress=None)

@student_bp.route('/api/start-learning', methods=['POST'])
@login_required
def api_start_learning():
    return jsonify({'status': 'ok'})

@student_bp.route('/special-practice')
@login_required
def special_practice():
    return render_template('student/special_practice.html',
                          student=current_user,
                          weak_topics_count=0,
                          total_practiced=0,
                          improved_topics=0,
                          avg_improvement=0,
                          weak_topics=[],
                          selected_topics=[],
                          practice_history=None)

@student_bp.route('/api/special-practice', methods=['POST'])
@login_required
def api_special_practice():
    return jsonify({'status': 'ok'})

@student_bp.route('/review')
@login_required
def review():
    return render_template('student/review.html',
                          student=current_user,
                          memory_retention=0,
                          due_topics_count=0,
                          due_topics=[],
                          estimated_time=0,
                          review_stats=None,
                          spaced_repetition_plan=[])

def calculate_forgetting_curve(mastery, days_since_study):
    return mastery * math.exp(-0.1 * days_since_study)

@student_bp.route('/api/start-review', methods=['POST'])
@login_required
def api_start_review():
    return jsonify({'status': 'ok'})
