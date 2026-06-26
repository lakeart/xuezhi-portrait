from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.extra import Note, Notification, StudyReminder, UserProfile
from datetime import datetime

extra_bp = Blueprint('extra', __name__)

# ==================== 笔记系统 ====================

@extra_bp.route('/notes')
@login_required
def notes():
    """笔记列表页"""
    # 获取筛选参数
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Note.query.filter_by(user_id=current_user.id)
    
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Note.title.like(f'%{search}%') | Note.content.like(f'%{search}%'))
    
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    
    # 分类统计
    categories = db.session.query(Note.category, db.func.count(Note.id)).filter_by(
        user_id=current_user.id
    ).group_by(Note.category).all()
    
    # 获取知识点列表
    topics = db.session.query(Note.related_topic).filter_by(
        user_id=current_user.id
    ).distinct().all()
    topics = [t[0] for t in topics if t[0]]
    
    return render_template('notes.html',
                           notes=notes,
                           categories=categories,
                           topics=topics,
                           current_category=category)


@extra_bp.route('/notes/create', methods=['POST'])
@login_required
def create_note():
    """创建笔记"""
    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category', '通用')
    tags = request.form.get('tags', '')
    related_question_id = request.form.get('related_question_id', type=int)
    related_topic = request.form.get('related_topic')
    
    if not title:
        flash('笔记标题不能为空')
        return redirect(url_for('extra.notes'))
    
    note = Note(
        user_id=current_user.id,
        title=title,
        content=content,
        category=category,
        tags=tags,
        related_question_id=related_question_id,
        related_topic=related_topic
    )
    
    db.session.add(note)
    db.session.commit()
    
    flash('笔记创建成功')
    return redirect(url_for('extra.notes'))


@extra_bp.route('/notes/<int:id>')
@login_required
def view_note(id):
    """查看笔记"""
    note = Note.query.get_or_404(id)
    
    if note.user_id != current_user.id and not note.is_public:
        flash('无权限查看该笔记')
        return redirect(url_for('extra.notes'))
    
    # 增加浏览次数
    note.view_count += 1
    db.session.commit()
    
    return render_template('note_detail.html', note=note)


@extra_bp.route('/notes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    """编辑笔记"""
    note = Note.query.get_or_404(id)
    
    if note.user_id != current_user.id:
        flash('无权限编辑该笔记')
        return redirect(url_for('extra.notes'))
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        note.category = request.form.get('category', '通用')
        note.tags = request.form.get('tags', '')
        note.related_topic = request.form.get('related_topic')
        note.is_public = request.form.get('is_public') == 'on'
        note.is_pinned = request.form.get('is_pinned') == 'on'
        note.updated_at = datetime.now()
        
        db.session.commit()
        flash('笔记已更新')
        return redirect(url_for('extra.view_note', id=note.id))
    
    return render_template('note_edit.html', note=note)


@extra_bp.route('/notes/<int:id>/delete', methods=['POST'])
@login_required
def delete_note(id):
    """删除笔记"""
    note = Note.query.get_or_404(id)
    
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权限'})
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'success': True})


@extra_bp.route('/notes/<int:id>/pin', methods=['POST'])
@login_required
def pin_note(id):
    """置顶/取消置顶笔记"""
    note = Note.query.get_or_404(id)
    
    if note.user_id != current_user.id:
        return jsonify({'success': False})
    
    note.is_pinned = not note.is_pinned
    db.session.commit()
    
    return jsonify({'success': True, 'is_pinned': note.is_pinned})


# ==================== 通知系统 ====================

@extra_bp.route('/notifications')
@extra_bp.route('/notification_center')
@login_required
def notification_center():
    """通知中心"""
    # 获取未读数量
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # 获取通知列表
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # 统计
    stats = {
        'total': Notification.query.filter_by(user_id=current_user.id).count(),
        'unread': unread_count,
        'achievements': Notification.query.filter_by(
            user_id=current_user.id, notification_type='achievement'
        ).count(),
        'wrong_questions': Notification.query.filter_by(
            user_id=current_user.id, notification_type='wrong_question'
        ).count(),
        'study_reminders': StudyReminder.query.filter_by(
            user_id=current_user.id, is_active=True
        ).count()
    }
    
    return render_template('notification_center.html',
                           notifications=notifications.items,
                           pagination=notifications,
                           stats=stats)


@extra_bp.route('/notifications/mark-read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    """标记通知为已读"""
    notification = Notification.query.get_or_404(id)
    
    if notification.user_id != current_user.id:
        return jsonify({'success': False})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@extra_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """标记全部已读"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})


@extra_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@extra_bp.route('/notifications/delete/<int:id>', methods=['POST'])
@login_required
def delete_notification(id):
    """删除单个通知"""
    notification = Notification.query.get_or_404(id)
    
    if notification.user_id != current_user.id:
        return jsonify({'success': False})
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})


@extra_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    """清空所有通知"""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== 个人设置 ====================

@extra_bp.route('/settings')
@extra_bp.route('/profile')
@login_required
def profile_settings():
    """个人设置页"""
    # 获取或创建用户资料
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    # 获取学习提醒设置
    reminder = StudyReminder.query.filter_by(user_id=current_user.id).first()
    
    return render_template('profile_settings.html',
                           profile=profile,
                           reminder=reminder)


@extra_bp.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    """更新个人资料"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
    
    profile.bio = request.form.get('bio', '')
    profile.signature = request.form.get('signature', '')
    profile.daily_goal = request.form.get('daily_goal', type=int, default=10)
    profile.weekly_goal = request.form.get('weekly_goal', type=int, default=50)
    profile.study_goal = request.form.get('study_goal', '')
    profile.preferred_topics = request.form.get('preferred_topics', '')
    profile.preferred_difficulty = request.form.get('preferred_difficulty')
    profile.show_achievements = request.form.get('show_achievements') == 'on'
    profile.show_rankings = request.form.get('show_rankings') == 'on'
    profile.updated_at = datetime.now()
    
    db.session.commit()
    
    flash('个人资料已更新')
    return redirect(url_for('extra.profile_settings'))


@extra_bp.route('/settings/avatar', methods=['POST'])
@login_required
def update_avatar():
    """更新头像"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
    
    avatar_url = request.form.get('avatar_url', '')
    profile.avatar = avatar_url
    profile.updated_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({'success': True, 'avatar': avatar_url})


@extra_bp.route('/settings/reminder', methods=['POST'])
@login_required
def update_reminder():
    """更新学习提醒设置"""
    reminder = StudyReminder.query.filter_by(user_id=current_user.id).first()
    
    if not reminder:
        reminder = StudyReminder(user_id=current_user.id)
        db.session.add(reminder)
    
    reminder.reminder_enabled = request.form.get('reminder_enabled') == 'on'
    reminder.reminder_time = request.form.get('reminder_time', '09:00')
    reminder.frequency = request.form.get('frequency', 'daily')
    reminder.prefer_topics = request.form.get('prefer_topics', '')
    
    db.session.commit()
    
    flash('提醒设置已更新')
    return redirect(url_for('extra.profile_settings'))


# ==================== API接口 ====================

@extra_bp.route('/api/notes', methods=['GET'])
@login_required
def api_notes():
    """获取笔记列表API"""
    category = request.args.get('category')
    
    query = Note.query.filter_by(user_id=current_user.id)
    if category:
        query = query.filter_by(category=category)
    
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    
    return jsonify({'success': True, 'notes': [n.to_dict() for n in notes]})


@extra_bp.route('/api/notes/<int:id>', methods=['GET'])
@login_required
def api_note(id):
    """获取单个笔记API"""
    note = Note.query.get_or_404(id)
    
    if note.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权限'})
    
    return jsonify({'success': True, 'note': note.to_dict()})
