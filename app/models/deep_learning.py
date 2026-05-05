import numpy as np
import json
import os
import random
from datetime import datetime, timedelta
import pickle
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('deep_learning_model')

# 定义模型保存路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/models')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# 尝试导入 PyTorch，如果失败则跳过
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
    logger.info("PyTorch 已加载，将使用深度学习模型")
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch 未找到，将使用规则方法替代")

# 如果有 PyTorch，定义模型
if TORCH_AVAILABLE:
    # 知识点预测模型
    class KnowledgeMasteryModel(nn.Module):
        def __init__(self, topic_size=50, student_size=3, hidden_size=64):
            super(KnowledgeMasteryModel, self).__init__()
            
            # 特征嵌入层
            self.topic_embedding = nn.Embedding(topic_size, hidden_size//2)
            self.student_embedding = nn.Linear(student_size, hidden_size//2)
            
            # 深度网络
            self.network = nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_size, hidden_size//2),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_size//2, 1),
                nn.Sigmoid()
            )
        
        def forward(self, topic_features, student_features, time_features=None):
            topic_emb = self.topic_embedding(topic_features)
            student_emb = self.student_embedding(student_features)
            combined = torch.cat([topic_emb.squeeze(1), student_emb], dim=1)
            prediction = self.network(combined)
            return prediction * 100

    # 学习计划优化模型
    class LearningScheduleModel(nn.Module):
        def __init__(self, topic_size=50, student_size=3, time_size=6, hidden_size=64):
            super(LearningScheduleModel, self).__init__()
            
            # 特征嵌入层
            self.topic_embedding = nn.Embedding(topic_size, hidden_size//2)
            self.student_embedding = nn.Linear(student_size, hidden_size//2)
            self.time_embedding = nn.Linear(time_size, hidden_size//4)
            
            # 效率评分网络
            self.efficiency_net = nn.Sequential(
                nn.Linear(hidden_size + hidden_size//4, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_size, hidden_size//2),
                nn.ReLU(),
                nn.Linear(hidden_size//2, 1),
                nn.Sigmoid()
            )
        
        def forward(self, topic_features, student_features, time_features):
            topic_emb = self.topic_embedding(topic_features)
            student_emb = self.student_embedding(student_features)
            time_emb = self.time_embedding(time_features)
            combined = torch.cat([topic_emb.squeeze(1), student_emb, time_emb], dim=1)
            efficiency = self.efficiency_net(combined)
            return efficiency


class DeepLearningModel:
    """深度学习模型类，用于学习计划推荐和知识点预测"""
    
    def __init__(self):
        """初始化模型"""
        # 如果有 PyTorch，初始化模型
        if TORCH_AVAILABLE:
            self.device = torch.device("cpu")
            logger.info(f"使用设备: {self.device}")
            
            self.mastery_model = KnowledgeMasteryModel().to(self.device)
            self.schedule_model = LearningScheduleModel().to(self.device)
        
        # 特征映射
        self.topic_to_idx = {}  # 知识点到索引的映射
        self.feature_scaler = None  # 特征标准化
        
        # 加载预训练模型
        self.model_loaded = self._load_model() if TORCH_AVAILABLE else False
    
    def _load_model(self):
        """加载预训练模型权重"""
        try:
            # 如果没有 PyTorch，直接使用规则方法
            if not TORCH_AVAILABLE:
                logger.info("PyTorch 不可用，将使用规则方法")
                return False
            
            # 尝试加载预训练的模型
            mastery_model_path = os.path.join(MODEL_DIR, 'mastery_model.pth')
            schedule_model_path = os.path.join(MODEL_DIR, 'schedule_model.pth')
            feature_mapping_path = os.path.join(MODEL_DIR, 'feature_mapping.pkl')
            
            # 如果文件存在，加载模型权重
            if os.path.exists(mastery_model_path) and os.path.exists(schedule_model_path):
                self.mastery_model.load_state_dict(torch.load(mastery_model_path, map_location=self.device))
                self.schedule_model.load_state_dict(torch.load(schedule_model_path, map_location=self.device))
                logger.info("成功加载预训练模型权重")
                
                # 加载特征映射
                if os.path.exists(feature_mapping_path):
                    with open(feature_mapping_path, 'rb') as f:
                        mapping_data = pickle.load(f)
                        self.topic_to_idx = mapping_data.get('topic_to_idx', {})
                        self.feature_scaler = mapping_data.get('feature_scaler')
                    logger.info("成功加载特征映射")
                
                return True
            else:
                # 如果模型文件不存在，初始化为训练模式
                logger.warning("模型文件不存在，将使用模拟数据初始化模型")
                return self._initialize_with_simulated_data()
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            # 出错时，尝试使用模拟数据进行初始化
            return self._initialize_with_simulated_data()
    
    def _initialize_with_simulated_data(self):
        """使用模拟数据初始化模型"""
        try:
            # 如果没有 PyTorch，直接使用规则方法
            if not TORCH_AVAILABLE:
                logger.info("PyTorch 不可用，跳过模型初始化")
                return False
            
            # 生成一些模拟数据进行训练
            logger.info("使用模拟数据初始化模型...")
            
            # 模拟常见知识点映射
            common_topics = ["数据结构", "算法设计", "计算机网络", "操作系统", "数据库原理", 
                           "软件工程", "编译原理", "计算机组成", "人工智能", "机器学习"]
            
            self.topic_to_idx = {topic: i for i, topic in enumerate(common_topics)}
            
            # 设置模型为评估模式
            self.mastery_model.eval()
            self.schedule_model.eval()
            
            return True
        except Exception as e:
            logger.error(f"模拟数据初始化失败: {str(e)}")
            return False
    
    def _prepare_topic_features(self, topic):
        """准备知识点特征（仅在有 PyTorch 时使用）"""
        if not TORCH_AVAILABLE:
            return None
        
        # 将知识点名称转换为索引ID
        topic_id = self.topic_to_idx.get(topic, random.randint(0, len(self.topic_to_idx)-1 if self.topic_to_idx else 9))
        
        # 创建one-hot编码作为知识点特征
        topic_tensor = torch.tensor([[topic_id]], dtype=torch.long).to(self.device)
        
        return topic_tensor
    
    def _prepare_student_features(self, student_data):
        """准备学生特征（仅在有 PyTorch 时使用）"""
        if not TORCH_AVAILABLE:
            return None
        
        # 提取学生特征
        learning_style = student_data.get('learning_style', {})
        
        # 视觉/语言偏好 (0=视觉, 1=语言)
        visual_verbal = 0 if learning_style.get('visual_verbal') == 'visual' else 1
        
        # 主动/反思偏好 (0=主动, 1=反思)
        active_reflective = 0 if learning_style.get('active_reflective') == 'active' else 1
        
        # 学习率
        learning_rate = float(student_data.get('learning_rate', 5))
        
        # 归一化学习率 (0-10 -> 0-1)
        normalized_learning_rate = learning_rate / 10.0
        
        # 组合特征
        features = [
            visual_verbal, 
            active_reflective,
            normalized_learning_rate
        ]
        
        # 转换为tensor
        student_tensor = torch.tensor([features], dtype=torch.float).to(self.device)
        
        return student_tensor
    
    def _prepare_time_features(self, time_slot, weekday):
        """准备时间特征（仅在有 PyTorch 时使用）"""
        if not TORCH_AVAILABLE:
            return None
        
        # 时间段 one-hot 编码
        time_slots = ['早上', '上午', '下午', '晚上', '深夜']
        time_slot_idx = time_slots.index(time_slot) if time_slot in time_slots else 0
        time_slot_one_hot = [0] * len(time_slots)
        time_slot_one_hot[time_slot_idx] = 1
        
        # 工作日/周末特征
        is_weekend = 1 if weekday >= 5 else 0
        
        # 组合特征
        features = time_slot_one_hot + [is_weekend]
        
        # 转换为tensor
        time_tensor = torch.tensor([features], dtype=torch.float).to(self.device)
        
        return time_tensor
    
    def predict_mastery_improvement(self, student_data, topic_data, duration_hours=1):
        """预测学习后的知识点掌握度提升
        
        参数:
            student_data: 学生数据
            topic_data: 知识点数据
            duration_hours: 学习时长(小时)
            
        返回:
            预测的掌握度提升百分比
        """
        # 如果没有 PyTorch 或模型未加载成功，使用规则方法
        if not TORCH_AVAILABLE or not self.model_loaded:
            return self._rule_based_prediction(student_data, topic_data, duration_hours)
        
        try:
            # 获取当前掌握度
            current_mastery = topic_data.get('mastery', 50)
            topic_name = topic_data.get('topic', '未知知识点')
            
            # 获取目标掌握度参数(如果存在)
            target_mastery = student_data.get('target_mastery', 85)
            
            # 准备特征
            topic_tensor = self._prepare_topic_features(topic_name)
            student_tensor = self._prepare_student_features(student_data)
            
            # 预测
            with torch.no_grad():
                predicted_improvement = self.mastery_model(topic_tensor, student_tensor)
                
            # 将学习时长纳入计算
            improvement_per_hour = predicted_improvement.item() / 10  # 基础每小时提升率
            total_improvement = improvement_per_hour * duration_hours
            
            # 考虑掌握度对学习效率的影响(掌握度越高，提升越慢)
            diminishing_factor = max(0.2, 1 - (current_mastery / 100) ** 0.5)
            
            # 根据目标掌握度调整学习效率
            # 目标掌握度越高，学习效率越高
            target_mastery_factor = 1.0
            if target_mastery >= 90:
                target_mastery_factor = 1.3  # 高目标提升30%学习效率
            elif target_mastery >= 85:
                target_mastery_factor = 1.15  # 中高目标提升15%学习效率
            elif target_mastery >= 80:
                target_mastery_factor = 1.05  # 中等目标提升5%学习效率
            
            # 应用目标掌握度因子和递减因子
            adjusted_improvement = total_improvement * diminishing_factor * target_mastery_factor
            
            # 确保掌握度不超过100%
            new_mastery = min(100, current_mastery + adjusted_improvement)
            improvement = new_mastery - current_mastery
            
            return improvement
        except Exception as e:
            logger.error(f"掌握度预测失败: {str(e)}")
            return self._rule_based_prediction(student_data, topic_data, duration_hours)
    
    def _rule_based_prediction(self, student_data, topic_data, duration_hours):
        """基于规则的掌握度预测（备选方案）"""
        # 获取当前掌握度
        current_mastery = topic_data.get('mastery', 50)
        
        # 获取目标掌握度参数(如果存在)
        target_mastery = student_data.get('target_mastery', 85)
        
        # 基础每小时改进率
        base_improvement = 5
        
        # 根据当前掌握度调整(掌握度越高，提升越慢)
        diminishing_factor = max(0.2, 1 - (current_mastery / 100) ** 0.5)
        
        # 根据目标掌握度调整学习效率
        target_mastery_factor = 1.0
        if target_mastery >= 90:
            target_mastery_factor = 1.3  # 高目标提升30%学习效率
        elif target_mastery >= 85:
            target_mastery_factor = 1.15  # 中高目标提升15%学习效率
        elif target_mastery >= 80:
            target_mastery_factor = 1.05  # 中等目标提升5%学习效率
        
        # 计算总改进
        total_improvement = base_improvement * duration_hours * diminishing_factor * target_mastery_factor
        
        # 随机波动(±20%)
        random_factor = random.uniform(0.8, 1.2)
        adjusted_improvement = total_improvement * random_factor
        
        # 确保掌握度不超过100%
        new_mastery = min(100, current_mastery + adjusted_improvement)
        improvement = new_mastery - current_mastery
        
        return improvement
    
    def recommend_optimal_schedule(self, student_data, topics, days=7):
        """根据学生数据和知识点信息生成最优学习计划
        
        参数:
            student_data: 学生数据
            topics: 知识点列表
            days: 计划天数
            
        返回:
            最优学习计划
        """
        # 获取当前日期
        today = datetime.now()
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        # 准备结果列表
        schedule = []
        
        # 对知识点按掌握度排序（优先学习掌握度低的）
        sorted_topics = sorted(topics, key=lambda x: x.get('mastery', 100))
        
        # 获取周末强化学习选项
        weekends_intensive = student_data.get('weekends_intensive', True)
        
        # 生成每天的计划
        for day in range(days):
            current_date = today + timedelta(days=day)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 获取星期几（0是周一）
            weekday_idx = current_date.weekday()
            weekday = weekdays[weekday_idx]
            
            # 检查是否为周末
            is_weekend = weekday_idx >= 5  # 5和6是周六和周日
            
            # 创建当天计划
            day_schedule = {
                'date': date_str,
                'weekday': weekday,
                'tasks': []  # 使用tasks字段来存储学习任务
            }
            
            # 根据学生偏好确定学习时段数量
            time_slots = ['早上', '下午', '晚上']
            
            # 根据周末强化选项决定周末学习时段数量
            slots_per_day = 3 if (is_weekend and weekends_intensive) else 2
            preferred_slots = student_data.get('preferred_time', ['晚上'])
            
            # 记录日志，用于调试
            logger.info(f"用户偏好学习时段: {preferred_slots}, 每日时段数量: {slots_per_day}")
            logger.info(f"当前日期: {date_str}, 星期: {weekday}, 是否周末: {is_weekend}")
            
            # 优先安排偏好时段
            selected_slots = []
            
            # 如果用户明确选择了学习时段，严格按照用户选择安排
            if preferred_slots and len(preferred_slots) > 0:
                # 记录接收到的用户偏好时段
                logger.info(f"处理用户偏好时段: {preferred_slots}")
                
                # 过滤有效的时段
                valid_preferred_slots = [slot for slot in preferred_slots if slot in time_slots]
                logger.info(f"有效的用户偏好时段: {valid_preferred_slots}")
                
                if valid_preferred_slots:
                    # 如果用户选择的时段数量不足每日时段数，则循环使用
                    for i in range(slots_per_day):
                        slot_index = i % len(valid_preferred_slots)
                        selected_slots.append(valid_preferred_slots[slot_index])
                        
                    # 确保不重复同一时段 (除非用户只选择了一个时段)
                    if len(valid_preferred_slots) > 1:
                        selected_slots = list(set(selected_slots))
                        # 如果去重后数量不足，补充其他时段
                        while len(selected_slots) < slots_per_day:
                            for slot in valid_preferred_slots:
                                if slot not in selected_slots:
                                    selected_slots.append(slot)
                                    break
                                if len(selected_slots) >= slots_per_day:
                                    break
            
            # 如果没有有效的偏好时段或用户未选择，使用默认方式安排
            if not selected_slots:
                # 默认使用晚上
                default_preferred = ['晚上']
                for slot in default_preferred:
                    if slot in time_slots and len(selected_slots) < slots_per_day:
                        selected_slots.append(slot)
                
                # 如果时段不够，添加其他时段
                while len(selected_slots) < slots_per_day:
                    for slot in time_slots:
                        if slot not in selected_slots:
                            selected_slots.append(slot)
                            break
                        if len(selected_slots) >= slots_per_day:
                            break
            
            # 记录最终选择的时段
            logger.info(f"最终安排的学习时段: {selected_slots}")
            
            # 计算当前知识点索引
            topic_index = day % min(len(sorted_topics), 5)  # 轮换前5个薄弱知识点
            
            # 为每个时间段安排任务
            for time_slot in selected_slots:
                if topic_index < len(sorted_topics):
                    topic = sorted_topics[topic_index]
                
                    try:
                        # 计算学习效率：综合学生数据、时间段、知识点难度
                        efficiency_score = 0.75  # 基础效率
                        
                        # 偏好时段学习效率更高
                        if time_slot in preferred_slots:
                            efficiency_score += 0.1
                        
                        # 周末学习效率可能更高（取决于学生特征）
                        if is_weekend:
                            efficiency_score += 0.05
                        
                        # 确保效率不超过100%
                        efficiency_score = min(1.0, efficiency_score)
                        
                        # 获取周末强化学习选项
                        weekends_intensive = student_data.get('weekends_intensive', True)
                        
                        # 生成学习时长（分钟）
                        duration_minutes = 90 if (is_weekend and weekends_intensive) else 60  # 周末强化学习时时间更长
                        
                        # 预测掌握度提升
                        improvement = self.predict_mastery_improvement(
                        student_data,
                        topic,
                                duration_minutes / 60  # 转换为小时
                            )
                        
                        current_mastery = topic.get('mastery', 50)
                        
                        # 创建学习计划项
                        task_item = {
                    'time': time_slot,
                            'topic': topic.get('topic', '未知知识点'),
                            'duration': duration_minutes,
                            'efficiency': round(efficiency_score * 100),  # 效率百分比
                            'current_mastery': round(current_mastery, 1),
                            'expected_improvement': round(improvement, 1)
                        }
                        
                        day_schedule['tasks'].append(task_item)
                        topic_index += 1
                    
                    except Exception as e:
                        logger.error(f"生成学习计划时出错: {str(e)}")
                        # 使用默认值
                        task_item = {
                            'time': time_slot,
                            'topic': topic.get('topic', '未知知识点'),
                            'duration': 60,
                            'efficiency': 75,  # 默认效率75%
                            'current_mastery': round(topic.get('mastery', 50), 1),
                            'expected_improvement': 5.0
                        }
                        day_schedule['tasks'].append(task_item)
                        topic_index += 1
            
            # 添加当天计划
            schedule.append(day_schedule)
        
        return schedule
    
    def predict_knowledge_trend(self, student_data, topics, days=30):
        """预测知识点掌握度趋势
        
        参数:
            student_data: 学生数据
            topics: 知识点列表
            days: 预测天数
            
        返回:
            知识点掌握度趋势预测
        """
        # 选择不超过5个知识点进行预测
        selected_topics = topics[:5] if len(topics) > 5 else topics
        
        # 定义预测时间点
        prediction_days = [0, 7, 15, 30]
        if days < 30:
            prediction_days = [0, int(days/3), int(days*2/3), days]
        
        predictions = []
        
        # 为每个知识点生成预测
        for topic in selected_topics:
            topic_name = topic.get('topic', '未知知识点')
            current_mastery = topic.get('mastery', 50)
            
            # 每个时间点的预测
            predictions_with_days = []
            
            # 每天学习该知识点的平均时间(小时)
            daily_study_hours = 1.0
            
            # 预测未来掌握度
            cumulative_improvement = 0
            for day in prediction_days:
                if day == 0:
                    # 初始掌握度
                    predicted_mastery = current_mastery
                else:
                    # 前一个时间点到当前时间点的天数
                    days_interval = day - prediction_days[prediction_days.index(day) - 1]
                    
                    # 预测这段时间内的掌握度提升
                    for _ in range(days_interval):
                        # 考虑掌握度对学习效率的影响
                        current_improvement = self.predict_mastery_improvement(
                            student_data, 
                            {'topic': topic_name, 'mastery': current_mastery + cumulative_improvement}, 
                            daily_study_hours
                        )
                        cumulative_improvement += current_improvement
                    
                    # 当前时间点的预测掌握度
                    predicted_mastery = min(100, current_mastery + cumulative_improvement)
                
                # 添加到预测数组
                predictions_with_days.append({
                    'day': day,
                    'mastery': round(predicted_mastery, 1)
                })
            
            # 创建知识点预测数据
            topic_prediction = {
                'topic': topic_name,
                'current_mastery': current_mastery,
                'predictions': predictions_with_days
            }
            
            predictions.append(topic_prediction)
        
        return predictions
    
    def generate_personalized_strategies(self, student_data, topics):
        """生成个性化学习策略
        
        参数:
            student_data: 学生数据
            topics: 知识点列表
            
        返回:
            个性化学习策略
        """
        learning_style = student_data.get('learning_style', {})
        
        # 视觉/语言偏好
        is_visual = learning_style.get('visual_verbal') == 'visual'
        
        # 主动/反思偏好
        is_active = learning_style.get('active_reflective') == 'active'
        
        # 选择最需关注的知识点(掌握度最低的3个)
        focus_topics = sorted(topics, key=lambda x: x.get('mastery', 100))[:3]
        focus_topics_names = [t.get('topic', '未知知识点') for t in focus_topics]
        
        # 基础策略
        strategies = []
        
        # 根据学习风格提供策略
        if is_visual:
            strategies.append({
                'title': '视觉学习策略',
                'description': f'对于{focus_topics_names[0]}等知识点，使用思维导图和图表可视化复杂概念，提高30%以上的记忆效果'
            })
        else:
            strategies.append({
                'title': '语言学习策略',
                'description': f'针对{focus_topics_names[0]}等知识点，通过语音笔记和概念口头表达，可提高理解深度和记忆保持'
            })
        
        if is_active:
            strategies.append({
                'title': '主动学习策略',
                'description': f'对于掌握度较低的{focus_topics_names[0]}和{focus_topics_names[1]}，采用项目实践和小组讨论方式，边做边学效果更佳'
                    })
        else:
            strategies.append({
                'title': '反思学习策略',
                'description': f'针对{focus_topics_names[0]}和{focus_topics_names[1]}，在安静环境下深度阅读和思考，定期总结学习内容效果显著'
            })
        
        # 通用高效学习策略
        general_strategies = [
            {
                'title': '分散学习效应',
                'description': f'对于{focus_topics_names[0]}，每天学习30分钟比一次性学习3小时效果更好，可提高20%的记忆效果'
            },
            {
                'title': '测试学习法',
                'description': f'在学习{focus_topics_names[1]}后，立即自我测试理解程度，能提高30%的知识保留率'
            },
            {
                'title': '关联学习法',
                'description': f'将{focus_topics_names[2]}与已掌握的知识建立联系，形成知识网络，深化理解和应用能力'
            },
            {
                'title': '专注时间管理',
                'description': '采用25分钟专注学习+5分钟休息的番茄工作法，可显著提高学习效率和注意力持续时间'
            },
            {
                'title': '主题式学习',
                'description': f'将{", ".join(focus_topics_names)}等相关知识点组织成主题，整体学习效果优于零散学习'
            }
        ]
        
        # 添加通用策略
        strategies.extend(general_strategies)
        
        # 为薄弱知识点推荐专项策略
        topic_specific_strategies = []
        
        for topic in focus_topics:  # 只关注薄弱点
            topic_name = topic.get('topic', '未知知识点')
            mastery = topic.get('mastery', 0)
            
            strategy = {}
            strategy['topic'] = topic_name
            
            if mastery < 30:
                strategy['strategy'] = f"重点关注《{topic_name}》，从基础概念开始，打牢基础。建议每天安排至少1小时专项学习。"
            elif mastery < 60:
                strategy['strategy'] = f"适当增加《{topic_name}》的练习量，巩固现有知识，解决理解上的疑难点。"
            else:
                strategy['strategy'] = f"《{topic_name}》掌握程度良好，建议定期复习，防止遗忘。"
            
            topic_specific_strategies.append(strategy)
        
        # 返回结构化的学习策略数据
        return {
            'general': [s.get('description', s) for s in strategies[:5]], # 最多返回5条一般策略
            'learning_style': [
                f"视觉型学习者: 通过图表、流程图等形式学习效果更好" if is_visual else f"语言型学习者: 通过阅读、讨论等形式学习效果更好",
                f"主动型学习者: 通过小组讨论和动手实践学习效果更好" if is_active else f"反思型学习者: 通过独立思考和分析学习效果更好"
            ],
            'topic_specific': topic_specific_strategies,
            'student_data': {
                'learning_style': learning_style
            }
        }

# 创建模型实例
dl_model = DeepLearningModel() 