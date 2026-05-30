import os
import sys
import csv
import random
import string
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.quiz import Question, QuizSubmission, AnswerRecord

# 计算机专业知识点池
computer_topics = ['顺序表', '链表', '栈', '队列', '树', '图', '堆',
    '哈希表', '字符串', '查找', '排序', '深度优先搜索(DFS)', '广度优先搜索(BFS)', '动态规划(DP)',
    '贪心', '字符串匹配(KMP)', '回溯算法', '位运算', '双指针'
]

# 用于生成中文姓名的姓和名
chinese_surnames = ['李', '王', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
chinese_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞']

def generate_chinese_name():
    """生成随机中文姓名"""
    surname = random.choice(chinese_surnames)
    name_length = random.randint(1, 2)
    name = ''.join(random.choices(chinese_names, k=name_length))
    return surname + name

def random_date_between(start_date=None, end_date=None):
    """生成随机日期"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=365)
    if not end_date:
        end_date = datetime.now()
    
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    
    # 添加随机小时和分钟
    random_date = random_date.replace(
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
    )
    
    return random_date

def reset_database():
    """重置数据库，删除所有表并重新创建"""
    print("正在重置数据库...")
    db.drop_all()
    db.create_all()
    print("数据库结构已重置")

def create_default_users():
    """创建默认用户：管理员、教师和学生"""
    print("正在创建默认用户...")
    
    # 管理员
    admin = User(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin'
    )
    db.session.add(admin)
    
    # 教师
    teacher = User(
        username='teacher',
        email='teacher@example.com',
        password='teacher123',
        role='teacher'
    )
    db.session.add(teacher)
    
    # 学生
    student = User(
        username='student',
        email='student@example.com',
        password='student123',
        role='student'
    )
    db.session.add(student)
    
    db.session.commit()
    print("默认用户创建完成")
    return teacher

def generate_students(num=50):
    """生成学生用户"""
    print(f"正在生成{num}个学生用户...")
    students = []
    seen_ids = set()
    
    # 定义学生群体类型及其分布
    student_groups = [
        {'type': '高绩效', 'percentage': 0.2},  # 优秀学生：成绩好，答题多
        {'type': '高效能', 'percentage': 0.25}, # 高效学生：成绩好，答题适中
        {'type': '高努力', 'percentage': 0.2},  # 勤奋学生：成绩一般，答题多
        {'type': '待提高', 'percentage': 0.2},  # 弱势学生：成绩差，答题少
        {'type': '均衡型', 'percentage': 0.15}  # 均衡学生：表现一般，学习稳定
    ]
    
    # 计算每种类型的学生数量
    group_counts = {}
    remaining = num
    for i, group in enumerate(student_groups):
        if i == len(student_groups) - 1:
            group_counts[group['type']] = remaining
        else:
            count = int(num * group['percentage'])
            group_counts[group['type']] = count
            remaining -= count
    
    # 生成每种类型的学生
    for group_type, count in group_counts.items():
        for _ in range(count):
            while True:
                student_id = f"{datetime.now().year}{random.randint(1000, 9999)}"
                if student_id not in seen_ids:
                    seen_ids.add(student_id)
                    break
            
            name = generate_chinese_name()
            email = f"{student_id}@student.example.com"
            
            student = User(
                username=student_id,
                email=email,
                password=student_id,  # 默认密码与学号相同
                role='student'
            )
            db.session.add(student)
            students.append({
                'id': student_id,
                'user': student,
                'name': name,
                'group_type': group_type  # 添加学生所属群体类型
            })
    
    db.session.commit()
    print(f"已生成{len(students)}个学生用户，分布于{len(group_counts)}个不同学习群体")
    return students

def generate_questions(num=100, admin_id=1):
    """生成题目"""
    print(f"正在生成{num}个题目...")
    questions = []
    question_styles = ['选择题', '填空题', '解答题', '判断题', '编程题']
    difficulties = ['简单', '中等', '困难']
    
    for i in range(1, num + 1):
        question_id = f"Q{i:04d}"
        topic = random.choice(computer_topics)
        style = random.choice(question_styles)
        difficulty = random.choices(difficulties, weights=[3, 5, 2])[0]
        
        content = f"{style}：关于{topic}的问题 #{i}"
        options = None
        
        if style == '选择题':
            options_list = [
                f"A. 选项A",
                f"B. 选项B",
                f"C. 选项C",
                f"D. 选项D"
            ]
            options = "\n".join(options_list)
        
        answer = f"标准答案" if style != '选择题' else random.choice(['A', 'B', 'C', 'D'])
        
        question = Question(
            question_id=question_id,
            topic=topic,
            style=style,
            content=content,
            options=options,
            answer=answer,
            difficulty=difficulty,
            created_at=random_date_between(),
            created_by=admin_id
        )
        
        db.session.add(question)
        questions.append(question)
    
    db.session.commit()
    print(f"已生成{len(questions)}个题目")
    return questions

def get_time_region(start_time):
    """根据时间判断做题时间段"""
    hour = start_time.hour
    if 6 <= hour < 11:
        return "早上"
    elif 11 <= hour < 14:
        return "中午"
    elif 14 <= hour < 18:
        return "下午"
    elif 18 <= hour < 24:
        return "晚上"
    else:
        return "凌晨"

def generate_submissions(num_records=5000, students=None, questions=None):
    """生成答题提交记录"""
    print(f"正在生成{num_records}条答题记录...")
    if not students or not questions:
        print("错误：缺少学生或题目数据")
        return []
    
    # 题型分数映射
    style_scores = {
        '选择题': 5,
        '填空题': 5,
        '判断题': 2,
        '解答题': 10,
        '编程题': 15
    }
    
    # 错误类型
    error_options = ['计算错误', '概念错误', '理解偏差', '格式错误', '审题错误', '知识点缺失', '答案正确', '部分正确']
    
    # 根据学生群体类型设置不同的答题表现参数
    group_characteristics = {
        '高绩效': {
            'submission_count_range': (80, 150),  # 每个学生生成的答题数量范围
            'correct_ratio': 0.85,                # 答对题目的概率
            'partial_correct_ratio': 0.1,         # 部分正确的概率
            'time_factor': 0.8,                   # 答题时间因子(越小答题越快)
            'topics_preference': [],              # 偏好的知识点(空表示均衡)
            'difficulty_weights': [1, 3, 3]       # 简单、中等、困难题目的权重
        },
        '高效能': {
            'submission_count_range': (40, 80),
            'correct_ratio': 0.8,
            'partial_correct_ratio': 0.15,
            'time_factor': 0.7,
            'topics_preference': [],
            'difficulty_weights': [1, 3, 2]
        },
        '高努力': {
            'submission_count_range': (90, 180),
            'correct_ratio': 0.6,
            'partial_correct_ratio': 0.2,
            'time_factor': 1.2,
            'topics_preference': [],
            'difficulty_weights': [3, 4, 1]
        },
        '待提高': {
            'submission_count_range': (20, 60),
            'correct_ratio': 0.4,
            'partial_correct_ratio': 0.2,
            'time_factor': 1.5,
            'topics_preference': [],
            'difficulty_weights': [4, 2, 1]
        },
        '均衡型': {
            'submission_count_range': (50, 100),
            'correct_ratio': 0.65,
            'partial_correct_ratio': 0.2,
            'time_factor': 1.0,
            'topics_preference': [],
            'difficulty_weights': [2, 3, 1]
        }
    }
    
    submissions = []
    answer_records = []
    csv_records = []
    
    # 按学生生成提交记录，确保每个学生有合理数量的提交
    student_submission_counts = {}
    
    # 为学生分配适当的提交次数
    for student in students:
        group_type = student.get('group_type', '均衡型')
        characteristics = group_characteristics[group_type]
        count_range = characteristics['submission_count_range']
        student_submission_counts[student['id']] = random.randint(*count_range)
    
    # 确保总提交数量不超过要求
    total_submissions = sum(student_submission_counts.values())
    if total_submissions > num_records:
        # 按比例减少每个学生的提交数
        reduction_factor = num_records / total_submissions
        for student_id in student_submission_counts:
            student_submission_counts[student_id] = max(1, int(student_submission_counts[student_id] * reduction_factor))
    
    # 生成每个学生的提交记录
    record_id = 1
    for student in students:
        student_id = student['id']
        group_type = student.get('group_type', '均衡型')
        characteristics = group_characteristics[group_type]
        
        # 获取该学生的提交次数
        submission_count = student_submission_counts[student_id]
        
        # 为该学生选择合适的题目
        filtered_questions = questions
        
        # 如果有题目偏好，按偏好筛选
        if characteristics['topics_preference']:
            preferred_topics = characteristics['topics_preference']
            filtered_questions = [q for q in questions if q.topic in preferred_topics]
            # 如果筛选后题目太少，则添加其他题目
            if len(filtered_questions) < 10:
                filtered_questions = questions
        
        # 随机选择该学生要答的题目
        student_questions = random.choices(
            filtered_questions, 
            k=min(submission_count, len(filtered_questions))
        )
        
        # 如果题目不够，可以重复使用
        if len(student_questions) < submission_count:
            additional_questions = random.choices(
                filtered_questions,
                k=submission_count - len(student_questions)
            )
            student_questions.extend(additional_questions)
        
        # 为该学生生成提交记录
        for question in student_questions:
            # 获取题型和分数
            question_style = question.style
            full_score = style_scores.get(question_style, 10)
            
            # 根据学生特征决定答题结果
            correct_probability = characteristics['correct_ratio']
            partial_probability = characteristics['partial_correct_ratio']
            
            # 根据题目难度调整正确率
            if question.difficulty == '简单':
                correct_probability += 0.1
            elif question.difficulty == '困难':
                correct_probability -= 0.15
            
            # 根据题型设置错误类型权重
            if question_style in ['解答题', '编程题']:
                current_error_options = error_options
                # 根据正确率和部分正确率来决定权重
                correct_weight = int(correct_probability * 100)
                partial_weight = int(partial_probability * 100)
                error_weight = int((1 - correct_probability - partial_probability) * 100 / 5)
                current_weights = [error_weight] * 6 + [correct_weight, partial_weight]
            else:
                current_error_options = error_options[:-1]  # 移除部分正确
                correct_weight = int(correct_probability * 100)
                error_weight = int((1 - correct_probability) * 100 / 6)
                current_weights = [error_weight] * 6 + [correct_weight]
            
            # 生成错误类型
            error_style = random.choices(
                population=current_error_options,
                weights=current_weights,
            )[0]
            
            # 计算得分
            if error_style == '答案正确':
                score = full_score
            elif error_style == '部分正确':
                if question.difficulty == '简单':
                    score = int(random.uniform(0.6, 0.9) * full_score)
                elif question.difficulty == '中等':
                    score = int(random.uniform(0.4, 0.7) * full_score)
                else:
                    score = int(random.uniform(0.3, 0.5) * full_score)
            else:
                score = 0
            
            # 生成时间，尽量分布在最近几个月
            months_ago = random.randint(0, 5)  # 0-5个月前
            start_date = datetime.now() - timedelta(days=30*months_ago)
            end_date = start_date + timedelta(days=30)
            start_time = random_date_between(start_date, end_date)
            time_region = get_time_region(start_time)
            
            # 根据题型、难度和学生特征设置耗时
            time_factor = characteristics['time_factor']
            if question_style in ['判断题', '选择题', '填空题']:
                if question.difficulty == '简单':
                    time_consumed = int(random.randint(10, 60) * time_factor)
                elif question.difficulty == '中等':
                    time_consumed = int(random.randint(60, 150) * time_factor)
                else:
                    time_consumed = int(random.randint(150, 400) * time_factor)
            else:
                # 编程题和解答题耗时更长
                if question.difficulty == '简单':
                    time_consumed = int(random.randint(200, 400) * time_factor)
                elif question.difficulty == '中等':
                    time_consumed = int(random.randint(300, 600) * time_factor)
                else:
                    time_consumed = int(random.randint(500, 1000) * time_factor)
            
            # 提交时间
            submit_time = start_time + timedelta(seconds=time_consumed)
            
            # 内存消耗
            if question_style in ['编程题', '解答题']:
                memory = random.randint(600, 1000)
            else:
                if question.difficulty == '简单':
                    memory = random.randint(100, 400)
                elif question.difficulty == '中等':
                    memory = random.randint(400, 600)
                else:
                    memory = random.randint(600, 1000)
            
            # 创建提交记录
            submission = QuizSubmission(
                student_id=student['id'],
                student_name=student['name'],
                question_id=question.id,
                source_question_id=question.question_id,
                question_topic=question.topic,
                question_style=question_style,
                error_style=error_style,
                start_time=start_time,
                submit_time=submit_time,
                difficulty=question.difficulty,
                score=score,
                time_consumed=time_consumed,
                memory=memory,
                time_region=time_region
            )
            
            db.session.add(submission)
            submissions.append(submission)
            
            # 创建答题记录
            answer_record = AnswerRecord(
                student_id=student['user'].id,
                question_id=question.id,
                answer_content=f"学生{student['id']}对题目{question.question_id}的答案，错误类型: {error_style}",
                score=score,
                start_time=start_time,
                submit_time=submit_time,
                time_consumed=time_consumed
            )
            
            db.session.add(answer_record)
            answer_records.append(answer_record)
            
            # 保存CSV记录用于可能的导出
            csv_records.append({
                'id': record_id,
                'student_id': student['id'],
                'student_name': student['name'],
                'question_topic': question.topic,
                'question_style': question_style,
                'error_style': error_style,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'submit_time': submit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'difficulty': question.difficulty,
                'score': score,
                'time_consumed': time_consumed,
                'memory': memory,
                'time_region': time_region,
                'student_group': group_type  # 添加学生群体类型，便于后续分析
            })
            
            record_id += 1
            
            # 每500条提交一次，减少内存占用
            if record_id % 500 == 0:
                db.session.commit()
                print(f"已生成 {record_id}/{num_records} 条记录...")
                if record_id >= num_records:
                    break
        
        if record_id >= num_records:
            break
    
    # 提交剩余记录
    db.session.commit()
    
    print(f"已生成{len(submissions)}条提交记录和{len(answer_records)}条答题记录")
    
    # 导出CSV文件
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quiz_data.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if csv_records:
            writer = csv.DictWriter(f, fieldnames=csv_records[0].keys())
            writer.writeheader()
            writer.writerows(csv_records)
    
    print(f"数据已导出到 {csv_file}")
    return submissions

def main():
    """主函数，重置数据库并生成测试数据"""
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 重置数据库
        reset_database()
        
        # 创建默认用户
        admin = create_default_users()
        
        # 生成学生用户
        students = generate_students(num=50)
        
        # 生成题目
        questions = generate_questions(num=100, admin_id=admin.id)
        
        # 生成答题记录
        generate_submissions(num_records=5000, students=students, questions=questions)
        
        print("数据库重置和数据生成完成！")

if __name__ == "__main__":
    main() 