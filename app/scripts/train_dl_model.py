import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pickle
import random
from torch.utils.data import Dataset, DataLoader

# 添加父目录到路径，以便导入应用模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入模型定义
from models.deep_learning import KnowledgeMasteryModel, LearningScheduleModel

# 定义模型保存路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/models')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# 设置设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用设备: {device}")

# 定义数据集类
class KnowledgeMasteryDataset(Dataset):
    """知识点掌握度预测数据集"""
    
    def __init__(self, n_samples=1000):
        """生成模拟数据
        
        参数:
            n_samples: 样本数量
        """
        # 生成模拟数据
        self.topic_ids = torch.randint(0, 10, (n_samples, 1))  # 10个知识点ID
        
        # 学生特征 [visual_verbal, active_reflective, learning_rate]
        self.student_features = torch.zeros((n_samples, 3))
        self.student_features[:, 0] = torch.randint(0, 2, (n_samples,))  # 视觉/语言偏好
        self.student_features[:, 1] = torch.randint(0, 2, (n_samples,))  # 主动/反思偏好
        self.student_features[:, 2] = torch.rand(n_samples)  # 归一化学习率 (0-1)
        
        # 生成目标掌握度 (0-1)
        self.mastery = torch.zeros(n_samples, 1)
        
        # 根据特征生成掌握度
        for i in range(n_samples):
            # 基础掌握度
            base_mastery = 0.4 + 0.3 * torch.rand(1).item()
            
            # 特征影响
            # 虚构一些规则: 某些知识点在特定学习风格下学习效果更好
            topic_id = self.topic_ids[i].item()
            visual_verbal = self.student_features[i, 0].item()
            active_reflective = self.student_features[i, 1].item()
            learning_rate = self.student_features[i, 2].item()
            
            # 规则示例: 
            # - 知识点 0-4 对视觉学习者更友好
            # - 知识点 5-9 对语言学习者更友好
            # - 知识点偶数 对主动学习者更友好
            # - 知识点奇数 对反思学习者更友好
            visual_match = 0.1 if (topic_id < 5 and visual_verbal == 0) or (topic_id >= 5 and visual_verbal == 1) else -0.05
            active_match = 0.1 if (topic_id % 2 == 0 and active_reflective == 0) or (topic_id % 2 == 1 and active_reflective == 1) else -0.05
            
            # 学习率影响
            rate_effect = 0.2 * learning_rate
            
            # 计算最终掌握度
            final_mastery = base_mastery + visual_match + active_match + rate_effect
            final_mastery = max(0.1, min(1.0, final_mastery))  # 限制在0.1-1.0范围内
            
            self.mastery[i] = final_mastery
    
    def __len__(self):
        return len(self.topic_ids)
    
    def __getitem__(self, idx):
        return {
            'topic_id': self.topic_ids[idx],
            'student_features': self.student_features[idx],
            'mastery': self.mastery[idx]
        }

class LearningScheduleDataset(Dataset):
    """学习计划优化数据集"""
    
    def __init__(self, n_samples=1000):
        """生成模拟数据
        
        参数:
            n_samples: 样本数量
        """
        # 生成模拟数据
        self.topic_ids = torch.randint(0, 10, (n_samples, 1))  # 10个知识点ID
        
        # 学生特征 [visual_verbal, active_reflective, learning_rate]
        self.student_features = torch.zeros((n_samples, 3))
        self.student_features[:, 0] = torch.randint(0, 2, (n_samples,))  # 视觉/语言偏好
        self.student_features[:, 1] = torch.randint(0, 2, (n_samples,))  # 主动/反思偏好
        self.student_features[:, 2] = torch.rand(n_samples)  # 归一化学习率 (0-1)
        
        # 时间特征 [时间段one-hot, 是否周末]
        self.time_features = torch.zeros((n_samples, 6))
        time_slot_idx = torch.randint(0, 5, (n_samples,))  # 5个时间段
        for i in range(n_samples):
            self.time_features[i, time_slot_idx[i]] = 1  # 设置时间段one-hot
        self.time_features[:, 5] = torch.randint(0, 2, (n_samples,))  # 是否周末
        
        # 生成学习效率分数 (0-1)
        self.efficiency = torch.zeros(n_samples, 1)
        
        # 根据特征生成效率分数
        for i in range(n_samples):
            # 基础效率
            base_efficiency = 0.5 + 0.2 * torch.rand(1).item()
            
            # 特征影响
            topic_id = self.topic_ids[i].item()
            time_slot = time_slot_idx[i].item()
            is_weekend = self.time_features[i, 5].item()
            
            # 时间段影响 (例如: 晚上更适合学习特定知识点)
            time_match = 0.0
            if time_slot == 3:  # 晚上
                time_match = 0.15  # 晚上学习效率普遍较高
            elif time_slot == 0 and topic_id < 3:  # 早上适合基础知识点
                time_match = 0.1
            elif time_slot == 2 and topic_id >= 5:  # 下午适合复杂知识点
                time_match = 0.05
            
            # 周末影响
            weekend_effect = 0.1 if is_weekend == 1 else 0.0
            
            # 计算最终效率
            final_efficiency = base_efficiency + time_match + weekend_effect
            final_efficiency = max(0.3, min(0.95, final_efficiency))  # 限制在0.3-0.95范围内
            
            self.efficiency[i] = final_efficiency
    
    def __len__(self):
        return len(self.topic_ids)
    
    def __getitem__(self, idx):
        return {
            'topic_id': self.topic_ids[idx],
            'student_features': self.student_features[idx],
            'time_features': self.time_features[idx],
            'efficiency': self.efficiency[idx]
        }

def train_mastery_model():
    """训练知识点掌握度预测模型"""
    print("训练知识点掌握度预测模型...")
    
    # 创建模型
    model = KnowledgeMasteryModel().to(device)
    
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 创建数据集和数据加载器
    train_dataset = KnowledgeMasteryDataset(n_samples=5000)
    val_dataset = KnowledgeMasteryDataset(n_samples=1000)
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    # 训练模型
    num_epochs = 10
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        # 训练阶段
        model.train()
        train_loss = 0.0
        
        for batch in train_loader:
            # 获取数据
            topic_ids = batch['topic_id'].to(device)
            student_features = batch['student_features'].to(device)
            mastery = batch['mastery'].to(device)
            
            # 前向传播
            optimizer.zero_grad()
            outputs = model(topic_ids, student_features) / 100  # 转换为0-1范围
            
            # 计算损失
            loss = criterion(outputs, mastery)
            
            # 反向传播和优化
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * topic_ids.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        # 验证阶段
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                # 获取数据
                topic_ids = batch['topic_id'].to(device)
                student_features = batch['student_features'].to(device)
                mastery = batch['mastery'].to(device)
                
                # 前向传播
                outputs = model(topic_ids, student_features) / 100  # 转换为0-1范围
                
                # 计算损失
                loss = criterion(outputs, mastery)
                
                val_loss += loss.item() * topic_ids.size(0)
            
            val_loss /= len(val_loader.dataset)
        
        print(f"Epoch {epoch+1}/{num_epochs}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'mastery_model.pth'))
            print(f"Best model saved with val_loss={val_loss:.4f}")
    
    print("知识点掌握度预测模型训练完成!")
    return model

def train_schedule_model():
    """训练学习计划优化模型"""
    print("训练学习计划优化模型...")
    
    # 创建模型
    model = LearningScheduleModel().to(device)
    
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 创建数据集和数据加载器
    train_dataset = LearningScheduleDataset(n_samples=5000)
    val_dataset = LearningScheduleDataset(n_samples=1000)
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    # 训练模型
    num_epochs = 10
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        # 训练阶段
        model.train()
        train_loss = 0.0
        
        for batch in train_loader:
            # 获取数据
            topic_ids = batch['topic_id'].to(device)
            student_features = batch['student_features'].to(device)
            time_features = batch['time_features'].to(device)
            efficiency = batch['efficiency'].to(device)
            
            # 前向传播
            optimizer.zero_grad()
            outputs = model(topic_ids, student_features, time_features)
            
            # 计算损失
            loss = criterion(outputs, efficiency)
            
            # 反向传播和优化
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * topic_ids.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        # 验证阶段
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                # 获取数据
                topic_ids = batch['topic_id'].to(device)
                student_features = batch['student_features'].to(device)
                time_features = batch['time_features'].to(device)
                efficiency = batch['efficiency'].to(device)
                
                # 前向传播
                outputs = model(topic_ids, student_features, time_features)
                
                # 计算损失
                loss = criterion(outputs, efficiency)
                
                val_loss += loss.item() * topic_ids.size(0)
            
            val_loss /= len(val_loader.dataset)
        
        print(f"Epoch {epoch+1}/{num_epochs}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'schedule_model.pth'))
            print(f"Best model saved with val_loss={val_loss:.4f}")
    
    print("学习计划优化模型训练完成!")
    return model

def save_feature_mapping():
    """保存特征映射"""
    print("保存特征映射信息...")
    
    # 定义知识点到索引的映射
    common_topics = ["数据结构", "算法设计", "计算机网络", "操作系统", "数据库原理", 
                    "软件工程", "编译原理", "计算机组成", "人工智能", "机器学习"]
    
    topic_to_idx = {topic: i for i, topic in enumerate(common_topics)}
    
    # 保存映射信息
    mapping_data = {
        'topic_to_idx': topic_to_idx,
        'feature_scaler': None  # 暂时不使用特征标准化
    }
    
    with open(os.path.join(MODEL_DIR, 'feature_mapping.pkl'), 'wb') as f:
        pickle.dump(mapping_data, f)
    
    print("特征映射信息保存完成!")

if __name__ == "__main__":
    print("开始训练深度学习模型...")
    
    # 训练知识点掌握度预测模型
    mastery_model = train_mastery_model()
    
    # 训练学习计划优化模型
    schedule_model = train_schedule_model()
    
    # 保存特征映射
    save_feature_mapping()
    
    print("所有模型训练完成！") 