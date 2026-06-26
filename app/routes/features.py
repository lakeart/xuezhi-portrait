from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.feature import WrongQuestion, Achievement, UserAchievement, UserPoints
from app.models.quiz import Question, AnswerRecord
from datetime import datetime, date, timedelta
import json

features_bp = Blueprint('features', __name__)

# ==================== 错题本功能 ====================

@features_bp.route('/wrong_questions')
@login_required
def wrong_questions():
    """错题本页面"""
    # 获取筛选参数
    topic = request.args.get('topic')
    style = request.args.get('style')
    mastered = request.args.get('mastered')
    
    query = WrongQuestion.query.filter_by(student_id=current_user.id)
    
    if topic:
        query = query.filter_by(question_topic=topic)
    if style:
        query = query.filter_by(question_style=style)
    if mastered is not None:
        query = query.filter_by(is_mastered=mastered.lower() == 'true')
    
    wrong_questions = query.order_by(WrongQuestion.created_at.desc()).all()
    
    # 获取统计数据
    total = WrongQuestion.query.filter_by(student_id=current_user.id).count()
    mastered_count = WrongQuestion.query.filter_by(student_id=current_user.id, is_mastered=True).count()
    
    # 获取所有知识点
    topics = db.session.query(WrongQuestion.question_topic).filter_by(student_id=current_user.id).distinct().all()
    topics = [t[0] for t in topics if t[0]]
    
    return render_template('wrong_questions.html',
                           wrong_questions=wrong_questions,
                           total=total,
                           mastered_count=mastered_count,
                           topics=topics,
                           current_topic=topic,
                           current_style=style,
                           current_mastered=mastered)


@features_bp.route('/wrong_questions/add', methods=['POST'])
@login_required
def add_wrong_question():
    """添加错题到错题本"""
    data = request.get_json()
    
    question_id = data.get('question_id')
    student_answer = data.get('student_answer')
    error_type = data.get('error_type', '粗心')
    
    # 检查是否已存在
    existing = WrongQuestion.query.filter_by(
        student_id=current_user.id,
        question_id=question_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': '该题已在错题本中'})
    
    # 获取题目详情
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'success': False, 'message': '题目不存在'})
    
    # 创建错题记录
    wrong_q = WrongQuestion(
        student_id=current_user.id,
        question_id=question_id,
        question_topic=question.topic,
        question_style=question.style,
        question_content=question.content,
        question_options=question.options,
        correct_answer=question.answer,
        student_answer=student_answer,
        error_type=error_type
    )
    
    db.session.add(wrong_q)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已加入错题本', 'id': wrong_q.id})


@features_bp.route('/wrong_questions/<int:id>/update', methods=['POST'])
@login_required
def update_wrong_question(id):
    """更新错题状态"""
    wrong_q = WrongQuestion.query.get_or_404(id)
    
    if wrong_q.student_id != current_user.id:
        return jsonify({'success': False, 'message': '无权限'})
    
    data = request.get_json()
    
    if 'is_mastered' in data:
        wrong_q.is_mastered = data['is_mastered']
        if data['is_mastered']:
            wrong_q.review_count += 1
            wrong_q.last_review_time = datetime.now()
    
    if 'error_note' in data:
        wrong_q.error_note = data['error_note']
    
    if 'error_type' in data:
        wrong_q.error_type = data['error_type']
    
    wrong_q.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True})


@features_bp.route('/wrong_questions/<int:id>/delete', methods=['POST'])
@login_required
def delete_wrong_question(id):
    """从错题本移除"""
    wrong_q = WrongQuestion.query.get_or_404(id)
    
    if wrong_q.student_id != current_user.id:
        return jsonify({'success': False, 'message': '无权限'})
    
    db.session.delete(wrong_q)
    db.session.commit()
    
    return jsonify({'success': True})


@features_bp.route('/wrong_questions/review/<int:id>')
@login_required
def review_wrong_question(id):
    """复习错题"""
    wrong_q = WrongQuestion.query.get_or_404(id)
    
    if wrong_q.student_id != current_user.id:
        return redirect(url_for('features.wrong_questions'))
    
    # 增加复习次数
    wrong_q.review_count += 1
    wrong_q.last_review_time = datetime.now()
    db.session.commit()
    
    return render_template('wrong_question_review.html', wrong_q=wrong_q)


# ==================== 成就系统 ====================

@features_bp.route('/achievements')
@features_bp.route('/achievement_center')
@login_required
def achievement_center():
    """成就中心"""
    # 获取用户成就
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    earned_ids = [ua.achievement_id for ua in user_achievements]
    
    # 获取所有成就
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    
    # 获取用户积分信息
    points_record = UserPoints.query.filter_by(user_id=current_user.id).first()
    
    # 按类别分组
    categories = {
        'learning': {'name': '学习里程碑', 'achievements': []},
        'streak': {'name': '连续学习', 'achievements': []},
        'accuracy': {'name': '准确率', 'achievements': []},
        'mastery': {'name': '掌握度', 'achievements': []},
        'special': {'name': '特殊成就', 'achievements': []}
    }
    
    for ach in all_achievements:
        info = {
            'achievement': ach,
            'earned': ach.id in earned_ids,
            'user_achievement': next((ua for ua in user_achievements if ua.achievement_id == ach.id), None)
        }
        if ach.category in categories:
            categories[ach.category]['achievements'].append(info)
    
    return render_template('achievement_center.html',
                           categories=categories,
                           points_record=points_record,
                           earned_count=len(user_achievements),
                           total_count=len(all_achievements))


@features_bp.route('/achievements/check', methods=['POST'])
@login_required
def check_achievements():
    """检查并解锁新成就"""
    from app.utils.achievement_checker import check_and_unlock_achievements
    new_achievements = check_and_unlock_achievements(current_user.id)
    return jsonify({'new_achievements': [a.to_dict() for a in new_achievements]})


@features_bp.route('/achievements/rankings')
@login_required
def achievement_rankings():
    """成就排行榜"""
    # 获取积分排行
    rankings = UserPoints.query.order_by(UserPoints.total_points.desc()).limit(50).all()
    
    result = []
    for rank, record in enumerate(rankings, 1):
        user = record.user
        earned_count = UserAchievement.query.filter_by(user_id=user.id).count()
        result.append({
            'rank': rank,
            'user_id': user.id,
            'username': user.username,
            'total_points': record.total_points,
            'earned_count': earned_count,
            'accuracy': record.to_dict()['accuracy']
        })
    
    return render_template('achievement_rankings.html', rankings=result)


# ==================== 积分系统 ====================

@features_bp.route('/points/add', methods=['POST'])
@login_required
def add_points():
    """增加积分"""
    data = request.get_json()
    points = data.get('points', 0)
    reason = data.get('reason', '')
    
    record = UserPoints.query.filter_by(user_id=current_user.id).first()
    if not record:
        record = UserPoints(user_id=current_user.id, total_points=0)
        db.session.add(record)
    
    record.total_points += points
    db.session.commit()
    
    return jsonify({'success': True, 'total': record.total_points})


@features_bp.route('/points/stats')
@login_required
def points_stats():
    """获取积分统计"""
    record = UserPoints.query.filter_by(user_id=current_user.id).first()
    if not record:
        return jsonify({
            'total_points': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'total_questions': 0,
            'accuracy': 0
        })
    
    return jsonify(record.to_dict())
