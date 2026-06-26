"""
成就检查器 - 检查用户是否达成新成就并解锁
"""
from app import db
from app.models.feature import Achievement, UserAchievement, UserPoints, WrongQuestion
from app.models.quiz import AnswerRecord, QuizSubmission
from datetime import datetime, date, timedelta


def check_and_unlock_achievements(user_id):
    """
    检查用户成就并解锁新达成的成就
    返回新解锁的成就列表
    """
    new_achievements = []
    
    # 获取用户统计
    stats = get_user_stats(user_id)
    
    # 获取用户已获得的成就
    earned_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
    
    # 获取所有成就定义
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    
    for achievement in all_achievements:
        if achievement.id in earned_ids:
            continue  # 已获得，跳过
        
        if check_condition(achievement, stats):
            # 解锁成就
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress_value=get_progress_value(achievement, stats)
            )
            db.session.add(user_achievement)
            
            # 增加积分
            add_points(user_id, achievement.points, f"解锁成就: {achievement.name}")
            
            # 创建通知
            try:
                from app.models.extra import Notification
                notification = Notification(
                    user_id=user_id,
                    title=f"🎉 成就解锁：{achievement.name}",
                    content=f"恭喜你解锁了「{achievement.name}」成就！获得 {achievement.points} 积分奖励。{achievement.description}",
                    notification_type='achievement',
                    related_id=achievement.id
                )
                db.session.add(notification)
            except Exception as e:
                print(f"创建通知失败: {e}")
            
            new_achievements.append(achievement)
    
    db.session.commit()
    return new_achievements


def check_condition(achievement, stats):
    """检查是否满足成就条件"""
    cond_type = achievement.condition_type
    cond_value = achievement.condition_value
    
    if cond_type == 'question_count':
        return stats['total_questions'] >= cond_value
    elif cond_type == 'correct_count':
        return stats['correct_questions'] >= cond_value
    elif cond_type == 'accuracy':
        return stats['accuracy'] >= cond_value
    elif cond_type == 'streak_days':
        return stats['current_streak'] >= cond_value
    elif cond_type == 'mastery_count':
        return stats['mastered_count'] >= cond_value
    elif cond_type == 'wrong_count':
        return stats['wrong_count'] >= cond_value
    elif cond_type == 'points':
        return stats['total_points'] >= cond_value
    
    return False


def get_progress_value(achievement, stats):
    """获取达成时的进度值"""
    cond_type = achievement.condition_type
    
    if cond_type == 'question_count':
        return stats['total_questions']
    elif cond_type == 'correct_count':
        return stats['correct_questions']
    elif cond_type == 'accuracy':
        return stats['accuracy']
    elif cond_type == 'streak_days':
        return stats['current_streak']
    elif cond_type == 'mastery_count':
        return stats['mastered_count']
    elif cond_type == 'wrong_count':
        return stats['wrong_count']
    elif cond_type == 'points':
        return stats['total_points']
    
    return 0


def get_user_stats(user_id):
    """获取用户统计数据"""
    # 获取或创建积分记录
    points_record = UserPoints.query.filter_by(user_id=user_id).first()
    
    # 答题统计
    total_questions = AnswerRecord.query.filter_by(student_id=user_id).count()
    correct_questions = AnswerRecord.query.filter_by(student_id=user_id, score__gt=0).count()
    
    # 准确率
    accuracy = round(correct_questions / total_questions * 100, 1) if total_questions > 0 else 0
    
    # 错题本统计
    wrong_count = WrongQuestion.query.filter_by(student_id=user_id).count()
    mastered_count = WrongQuestion.query.filter_by(student_id=user_id, is_mastered=True).count()
    
    # 更新积分记录
    if points_record:
        points_record.total_questions = total_questions
        points_record.correct_questions = correct_questions
    else:
        points_record = UserPoints(
            user_id=user_id,
            total_questions=total_questions,
            correct_questions=correct_questions
        )
        db.session.add(points_record)
        db.session.commit()
    
    return {
        'total_questions': total_questions,
        'correct_questions': correct_questions,
        'accuracy': accuracy,
        'current_streak': points_record.current_streak,
        'total_points': points_record.total_points,
        'wrong_count': wrong_count,
        'mastered_count': mastered_count
    }


def add_points(user_id, points, reason):
    """增加用户积分并更新连续学习天数"""
    record = UserPoints.query.filter_by(user_id=user_id).first()
    
    if not record:
        record = UserPoints(user_id=user_id)
        db.session.add(record)
    
    record.total_points += points
    
    # 更新连续学习天数
    today = date.today()
    if record.last_active_date:
        if record.last_active_date == today:
            pass  # 今天已活跃
        elif record.last_active_date == today - timedelta(days=1):
            record.current_streak += 1
            if record.current_streak > record.longest_streak:
                record.longest_streak = record.current_streak
        else:
            record.current_streak = 1
    else:
        record.current_streak = 1
    
    record.last_active_date = today
    db.session.commit()


def update_streak(user_id):
    """更新用户连续学习天数（每日调用）"""
    record = UserPoints.query.filter_by(user_id=user_id).first()
    if not record:
        return
    
    today = date.today()
    if record.last_active_date:
        if record.last_active_date < today - timedelta(days=1):
            # 中断了
            record.current_streak = 0
    db.session.commit()


def init_achievements():
    """初始化成就数据"""
    achievements_data = [
        # 学习里程碑
        {'code': 'first_question', 'name': '初出茅庐', 'description': '完成第一道题目', 'icon': 'fa-star', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 1, 'points': 10, 'badge_color': 'bronze'},
        {'code': 'ten_questions', 'name': '勤学苦练', 'description': '累计完成10道题目', 'icon': 'fa-fire', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 10, 'points': 30, 'badge_color': 'bronze'},
        {'code': 'fifty_questions', 'name': '学有小成', 'description': '累计完成50道题目', 'icon': 'fa-bolt', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 50, 'points': 80, 'badge_color': 'silver'},
        {'code': 'hundred_questions', 'name': '学富五车', 'description': '累计完成100道题目', 'icon': 'fa-crown', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 100, 'points': 150, 'badge_color': 'silver'},
        {'code': 'five_hundred_questions', 'name': '学贯中西', 'description': '累计完成500道题目', 'icon': 'fa-gem', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 500, 'points': 300, 'badge_color': 'gold'},
        {'code': 'thousand_questions', 'name': '博学多才', 'description': '累计完成1000道题目', 'icon': 'fa-trophy', 'category': 'learning', 'condition_type': 'question_count', 'condition_value': 1000, 'points': 500, 'badge_color': 'diamond'},
        
        # 连续学习
        {'code': 'streak_3', 'name': '持之以恒', 'description': '连续学习3天', 'icon': 'fa-calendar-check', 'category': 'streak', 'condition_type': 'streak_days', 'condition_value': 3, 'points': 50, 'badge_color': 'bronze'},
        {'code': 'streak_7', 'name': '锲而不舍', 'description': '连续学习7天', 'icon': 'fa-calendar-week', 'category': 'streak', 'condition_type': 'streak_days', 'condition_value': 7, 'points': 100, 'badge_color': 'silver'},
        {'code': 'streak_30', 'name': '坚持不懈', 'description': '连续学习30天', 'icon': 'fa-calendar-alt', 'category': 'streak', 'condition_type': 'streak_days', 'condition_value': 30, 'points': 300, 'badge_color': 'gold'},
        {'code': 'streak_100', 'name': '百折不挠', 'description': '连续学习100天', 'icon': 'fa-medal', 'category': 'streak', 'condition_type': 'streak_days', 'condition_value': 100, 'points': 800, 'badge_color': 'diamond'},
        
        # 准确率
        {'code': 'accuracy_80', 'name': '火眼金睛', 'description': '准确率达到80%', 'icon': 'fa-eye', 'category': 'accuracy', 'condition_type': 'accuracy', 'condition_value': 80, 'points': 100, 'badge_color': 'silver'},
        {'code': 'accuracy_90', 'name': '一击即中', 'description': '准确率达到90%', 'icon': 'fa-bullseye', 'category': 'accuracy', 'condition_type': 'accuracy', 'condition_value': 90, 'points': 200, 'badge_color': 'gold'},
        {'code': 'accuracy_100', 'name': '完美无缺', 'description': '准确率达到100%', 'icon': 'fa-star-half-alt', 'category': 'accuracy', 'condition_type': 'accuracy', 'condition_value': 100, 'points': 500, 'badge_color': 'diamond'},
        
        # 掌握度
        {'code': 'mastery_10', 'name': '知错能改', 'description': '掌握10道错题', 'icon': 'fa-check-circle', 'category': 'mastery', 'condition_type': 'mastery_count', 'condition_value': 10, 'points': 80, 'badge_color': 'silver'},
        {'code': 'mastery_50', 'name': '温故知新', 'description': '掌握50道错题', 'icon': 'fa-book-open', 'category': 'mastery', 'condition_type': 'mastery_count', 'condition_value': 50, 'points': 200, 'badge_color': 'gold'},
        {'code': 'mastery_100', 'name': '举一反三', 'description': '掌握100道错题', 'icon': 'fa-brain', 'category': 'mastery', 'condition_type': 'mastery_count', 'condition_value': 100, 'points': 400, 'badge_color': 'diamond'},
        
        # 错题本
        {'code': 'wrong_10', 'name': '初入错题本', 'description': '收录10道错题', 'icon': 'fa-exclamation-triangle', 'category': 'special', 'condition_type': 'wrong_count', 'condition_value': 10, 'points': 30, 'badge_color': 'bronze'},
        {'code': 'wrong_50', 'name': '错题收集者', 'description': '收录50道错题', 'icon': 'fa-clipboard-list', 'category': 'special', 'condition_type': 'wrong_count', 'condition_value': 50, 'points': 100, 'badge_color': 'silver'},
        
        # 特殊成就
        {'code': 'early_bird', 'name': '闻鸡起舞', 'description': '早上6点前学习', 'icon': 'fa-sun', 'category': 'special', 'condition_type': 'special', 'condition_value': 1, 'points': 50, 'badge_color': 'gold'},
        {'code': 'night_owl', 'name': '夜猫子', 'description': '晚上12点后学习', 'icon': 'fa-moon', 'category': 'special', 'condition_type': 'special', 'condition_value': 1, 'points': 50, 'badge_color': 'silver'},
        {'code': 'first_blood', 'name': '首战告捷', 'description': '答对第一道题', 'icon': 'fa-flag', 'category': 'special', 'condition_type': 'correct_count', 'condition_value': 1, 'points': 20, 'badge_color': 'bronze'},
    ]
    
    for data in achievements_data:
        existing = Achievement.query.filter_by(code=data['code']).first()
        if not existing:
            achievement = Achievement(**data)
            db.session.add(achievement)
    
    db.session.commit()
    print(f"成就系统初始化完成，共 {len(achievements_data)} 个成就")
