import pandas as pd
from datetime import datetime
from app import db
from app.models.quiz import QuizSubmission, Question
import os

def import_csv_data(csv_file_path):
    """导入CSV数据到数据库"""
    try:
        # 检查文件是否存在
        if not os.path.exists(csv_file_path):
            return False, f"文件不存在: {csv_file_path}"
        
        # 读取CSV文件
        df = pd.read_csv(csv_file_path)
        
        # 导入数据
        records_added = 0
        for _, row in df.iterrows():
            # 将字符串时间转换为datetime对象
            try:
                start_time = datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M:%S')
                submit_time = datetime.strptime(row['submit_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"时间格式错误: {row['start_time']} 或 {row['submit_time']}")
                continue
            
            # 创建新的提交记录
            new_submission = QuizSubmission(
                student_id=row['student_id'],
                student_name=row['student_name'],
                source_question_id=row['question_id'],  # 存储原始问题ID
                question_topic=row['question_topic'],
                question_style=row['question_style'],
                error_style=row['error_style'],
                start_time=start_time,
                submit_time=submit_time,
                difficulty=row['difficulty'],
                score=row['score'],
                time_consumed=row['time_consumed'],
                memory=row['memory'],
                time_region=row['time_region']
            )
            
            # 检查对应的问题是否存在
            question = Question.query.filter_by(question_id=row['question_id']).first()
            if question:
                new_submission.question_id = question.id
            
            db.session.add(new_submission)
            records_added += 1
        
        db.session.commit()
        return True, f"成功导入 {records_added} 条记录"
    
    except Exception as e:
        db.session.rollback()
        return False, f"导入数据时出错: {str(e)}" 