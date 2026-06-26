from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.quiz import Question, AnswerRecord, QuizSubmission
from app.models.user import User
import json
from datetime import datetime
from sqlalchemy import func, case, asc, desc

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/')
@login_required
def index():
    # 获取页码参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    
    # 获取筛选参数
    search = request.args.get('search', '')
    topic = request.args.get('topic', '')
    difficulty = request.args.get('difficulty', '')
    style = request.args.get('style', '')
    
    # 基础查询
    query = Question.query
    
    # 应用筛选条件
    if search:
        query = query.filter(Question.content.like(f'%{search}%'))
    if topic:
        query = query.filter(Question.topic == topic)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if style:
        query = query.filter(Question.style == style)
    
    # 执行查询并分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    questions = pagination.items
    
    # 为每个题目计算正确率
    for question in questions:
        # 获取该题目的所有提交记录
        submissions = QuizSubmission.query.filter_by(question_id=question.id).all()
        
        # 如果没有提交记录，设置正确率为0
        if not submissions or len(submissions) == 0:
            question.correct_rate = 0
            continue
        
        # 计算正确率（得分大于0的提交/总提交数）
        correct_submissions = sum(1 for sub in submissions if sub.score > 0)
        total_submissions = len(submissions)
        question.correct_rate = (correct_submissions / total_submissions) * 100
    
    # 获取所有可用的知识点，用于筛选
    available_topics = db.session.query(Question.topic).distinct().all()
    topics = [topic[0] for topic in available_topics]
    
    return render_template('quiz/index.html', 
                          questions=questions, 
                          pagination=pagination,
                          topics=topics,
                          search=search,
                          selected_topic=topic,
                          selected_difficulty=difficulty,
                          selected_style=style)

@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_teacher():
        flash('只有教师可以创建测验')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        question_id = f"Q{len(Question.query.all()) + 1:04d}"
        topic = request.form.get('topic')
        style = request.form.get('style')
        content = request.form.get('content')
        options = request.form.get('options')  # JSON字符串
        answer = request.form.get('answer')
        difficulty = request.form.get('difficulty')
        
        new_question = Question(
            question_id=question_id,
            topic=topic,
            style=style,
            content=content,
            options=options,
            answer=answer,
            difficulty=difficulty,
            created_by=current_user.id
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        flash('测验题创建成功')
        return redirect(url_for('quiz.index'))
    
    return render_template('quiz/create.html')

@quiz_bp.route('/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(question_id):
    if not current_user.is_teacher():
        flash('只有教师可以编辑测验')
        return redirect(url_for('main.dashboard'))
    
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.topic = request.form.get('topic')
        question.style = request.form.get('style')
        question.content = request.form.get('content')
        question.options = request.form.get('options')
        question.answer = request.form.get('answer')
        question.difficulty = request.form.get('difficulty')
        
        db.session.commit()
        flash('测验题更新成功')
        return redirect(url_for('quiz.index'))
    
    return render_template('quiz/edit.html', question=question)

@quiz_bp.route('/<int:question_id>')
@login_required
def view(question_id):
    question = Question.query.get_or_404(question_id)
    return render_template('quiz/view.html', question=question)

@quiz_bp.route('/<int:question_id>/submit', methods=['POST'])
@login_required
def submit(question_id):
    question = Question.query.get_or_404(question_id)
    answer_content = request.form.get('answer')
    start_time_str = request.form.get('start_time')
    
    if start_time_str:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    else:
        start_time = datetime.now()
    
    submit_time = datetime.now()
    time_consumed = (submit_time - start_time).seconds
    
    # 根据题型设置满分分值
    max_score = 5  # 默认值
    if question.style == '选择题':
        max_score = 5
    elif question.style == '填空题':
        max_score = 5
    elif question.style == '判断题':
        max_score = 2
    elif question.style == '解答题':
        max_score = 10
    elif question.style == '编程题':
        max_score = 15
    
    # 评分逻辑
    score = 0
    if question.style == '选择题' or question.style == '判断题':
        if answer_content.strip() == question.answer.strip():
            score = max_score  # 给予该题型的满分
    
    answer_record = AnswerRecord(
        student_id=current_user.id,
        question_id=question.id,
        answer_content=answer_content,
        score=score,
        start_time=start_time,
        submit_time=submit_time,
        time_consumed=time_consumed
    )
    
    db.session.add(answer_record)
    db.session.commit()
    
    # 如果答错，自动加入错题本
    if score == 0:
        try:
            from app.models.feature import WrongQuestion
            existing = WrongQuestion.query.filter_by(
                student_id=current_user.id,
                question_id=question.id
            ).first()
            
            if not existing:
                wrong_q = WrongQuestion(
                    student_id=current_user.id,
                    question_id=question.id,
                    question_topic=question.topic,
                    question_style=question.style,
                    question_content=question.content,
                    question_options=question.options,
                    correct_answer=question.answer,
                    student_answer=answer_content,
                    error_type='待分析'
                )
                db.session.add(wrong_q)
                db.session.commit()
        except Exception as e:
            print(f"添加错题失败: {e}")
    
    # 检查成就解锁
    try:
        from app.utils.achievement_checker import check_and_unlock_achievements
        new_achievements = check_and_unlock_achievements(current_user.id)
        if new_achievements:
            achievement_names = ', '.join([a.name for a in new_achievements])
            flash(f'答案已提交，得分：{score}/{max_score} | 恭喜解锁成就：{achievement_names}！')
        else:
            flash(f'答案已提交，得分：{score}/{max_score}')
    except Exception as e:
        print(f"检查成就失败: {e}")
        flash(f'答案已提交，得分：{score}/{max_score}')
    
    return redirect(url_for('quiz.index'))

@quiz_bp.route('/my-answers')
@login_required
def my_answers():
    # 基本统计信息
    stats = db.session.query(
        func.count(QuizSubmission.id).label('total_submissions'),
        func.avg(QuizSubmission.score).label('avg_score'),
        # 根据题型判断满分
        func.sum(case(
            (QuizSubmission.question_style == '选择题', case((QuizSubmission.score == 5, 1), else_=0)),
            (QuizSubmission.question_style == '填空题', case((QuizSubmission.score == 5, 1), else_=0)),
            (QuizSubmission.question_style == '判断题', case((QuizSubmission.score == 2, 1), else_=0)),
            (QuizSubmission.question_style == '解答题', case((QuizSubmission.score == 10, 1), else_=0)),
            (QuizSubmission.question_style == '编程题', case((QuizSubmission.score == 15, 1), else_=0)),
            else_=0
        )).label('perfect_count'),
        func.avg(QuizSubmission.time_consumed).label('avg_time')
    ).filter(QuizSubmission.student_id == current_user.username).first()
    
    # 知识点分布
    topic_stats = db.session.query(
        QuizSubmission.question_topic,
        func.count(QuizSubmission.id).label('topic_count'),
        func.avg(QuizSubmission.score).label('topic_avg_score'),
        # 计算正确率：得分除以该题型的满分
        func.sum(case(
            (QuizSubmission.question_style == '选择题', case((QuizSubmission.score > 0, 1), else_=0)),
            (QuizSubmission.question_style == '填空题', case((QuizSubmission.score > 0, 1), else_=0)),
            (QuizSubmission.question_style == '判断题', case((QuizSubmission.score > 0, 1), else_=0)),
            (QuizSubmission.question_style == '解答题', case((QuizSubmission.score > 5, 1), else_=0)),
            (QuizSubmission.question_style == '编程题', case((QuizSubmission.score > 7, 1), else_=0)),
            else_=0
        )).label('correct_count')
    ).filter(QuizSubmission.student_id == current_user.username)\
    .group_by(QuizSubmission.question_topic).all()
    
    # 处理统计数据
    topic_data = []
    for stat in topic_stats:
        correct_rate = round((stat.correct_count / stat.topic_count) * 100, 1) if stat.topic_count > 0 else 0
        topic_data.append({
            'topic': stat.question_topic,
            'count': stat.topic_count,
            'avg_score': round(float(stat.topic_avg_score or 0), 2),
            'accuracy': correct_rate
        })
    
    return render_template('quiz/my_answers.html', 
                          stats={
                              'total_submissions': stats.total_submissions or 0,
                              'avg_score': round(float(stats.avg_score or 0), 2),
                              'perfect_count': stats.perfect_count or 0,
                              'avg_time': round(float(stats.avg_time or 0), 2)
                          },
                          topic_data=topic_data)

@quiz_bp.route('/api/my-answers')
@login_required
def api_my_answers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    topic = request.args.get('topic', '')
    difficulty = request.args.get('difficulty', '')
    sort = request.args.get('sort', 'submit_time')
    order = request.args.get('order', 'desc')
    
    # 构建查询
    query = QuizSubmission.query.filter(QuizSubmission.student_id == current_user.username)
    
    # 筛选条件
    if topic:
        query = query.filter(QuizSubmission.question_topic == topic)
    if difficulty:
        query = query.filter(QuizSubmission.difficulty == difficulty)
    
    # 排序
    if sort == 'submit_time':
        if order == 'asc':
            query = query.order_by(asc(QuizSubmission.submit_time))
        else:
            query = query.order_by(desc(QuizSubmission.submit_time))
    elif sort == 'score':
        if order == 'asc':
            query = query.order_by(asc(QuizSubmission.score))
        else:
            query = query.order_by(desc(QuizSubmission.score))
    elif sort == 'time_consumed':
        if order == 'asc':
            query = query.order_by(asc(QuizSubmission.time_consumed))
        else:
            query = query.order_by(desc(QuizSubmission.time_consumed))
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 处理结果
    answer_data = []
    for record in pagination.items:
        # 获取题型对应的满分
        max_score = 5  # 默认值
        if record.question_style == '选择题':
            max_score = 5
        elif record.question_style == '填空题':
            max_score = 5
        elif record.question_style == '判断题':
            max_score = 2
        elif record.question_style == '解答题':
            max_score = 10
        elif record.question_style == '编程题':
            max_score = 15
            
        # 计算准确率
        accuracy = round((record.score / max_score) * 100) if max_score > 0 else 0
        
        answer_data.append({
            'id': record.id,
            'question_id': record.source_question_id,
            'question_topic': record.question_topic,
            'question_style': record.question_style,
            'difficulty': record.difficulty,
            'score': record.score,
            'max_score': max_score,
            'time_consumed': record.time_consumed,
            'submit_time': record.submit_time.strftime('%Y-%m-%d %H:%M:%S') if record.submit_time else '',
            'time_region': record.time_region,
            'accuracy': accuracy
        })
    
    # 查询过滤选项
    topics = db.session.query(QuizSubmission.question_topic).filter(
        QuizSubmission.student_id == current_user.username
    ).distinct().all()
    
    difficulties = db.session.query(QuizSubmission.difficulty).filter(
        QuizSubmission.student_id == current_user.username
    ).distinct().all()
    
    # 构造返回数据
    return jsonify({
        'data': answer_data,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_count': pagination.total
        },
        'filter_options': {
            'topics': [t[0] for t in topics],
            'difficulties': [d[0] for d in difficulties]
        },
        'sort': {
            'field': sort,
            'order': order
        }
    })

@quiz_bp.route('/submission/<int:submission_id>')
@login_required
def show_submission(submission_id):
    """显示答题记录的详细信息"""
    submission = QuizSubmission.query.get_or_404(submission_id)
    
    # 确保用户只能查看自己的答题记录
    if submission.student_id != current_user.username:
        flash('您没有权限查看此答题记录')
        return redirect(url_for('quiz.my_answers'))
    
    # 获取题型对应的满分
    max_score = 5  # 默认值
    if submission.question_style == '选择题':
        max_score = 5
    elif submission.question_style == '填空题':
        max_score = 5
    elif submission.question_style == '判断题':
        max_score = 2
    elif submission.question_style == '解答题':
        max_score = 10
    elif submission.question_style == '编程题':
        max_score = 15
    
    # 计算准确率
    accuracy = round((submission.score / max_score) * 100) if max_score > 0 else 0
    
    return render_template('quiz/submission_detail.html',
                         submission=submission,
                         max_score=max_score,
                         accuracy=accuracy) 