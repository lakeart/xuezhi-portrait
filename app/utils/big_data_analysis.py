"""
大数据分析模块 - 高级数据处理与统计分析
用于大数据实践赛参赛作品

功能包括：
1. 时间序列分析与预测
2. 知识点关联性分析
3. 学生群体聚类分析
4. 学习效果评估
5. 数据质量检测
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score,
    mean_squared_error, r2_score, accuracy_score,
    precision_recall_fscore_support
)
import logging
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('big_data_analysis')


class BigDataAnalyzer:
    """大数据分析器类"""
    
    def __init__(self):
        """初始化分析器"""
        self.student_features = None
        self.topic_correlations = None
        self.time_patterns = None
        self.clustering_model = None
        
    def analyze_student_behavior(self, submissions_df):
        """
        分析学生学习行为模式
        
        参数:
            submissions_df: 包含答题记录的DataFrame
        
        返回:
            dict: 学习行为分析结果
        """
        logger.info("开始分析学生学习行为...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("学习行为分析")
        
        try:
            # 计算每个学生的行为特征
            student_behavior = submissions_df.groupby('student_id').agg({
                'score': ['mean', 'std', 'min', 'max', 'count'],
                'time_consumed': ['mean', 'std'],
                'submit_time': ['min', 'max']
            }).reset_index()
            
            # 展平多级列名
            student_behavior.columns = [
                'student_id', 'avg_score', 'score_std', 'min_score', 'max_score',
                'total_attempts', 'avg_time', 'time_std', 'first_attempt', 'last_attempt'
            ]
            
            # 计算学习持续时间（天）
            student_behavior['learning_duration'] = (
                pd.to_datetime(student_behavior['last_attempt']) - 
                pd.to_datetime(student_behavior['first_attempt'])
            ).dt.days + 1
            
            # 计算学习频率（每天平均答题数）
            student_behavior['learning_frequency'] = (
                student_behavior['total_attempts'] / student_behavior['learning_duration']
            ).fillna(0)
            
            # 计算稳定性指标（得分变异系数）
            student_behavior['score_cv'] = (
                student_behavior['score_std'] / student_behavior['avg_score']
            ).replace([np.inf, -np.inf], 0).fillna(0)
            
            # 学习效率（正确率/平均用时）
            student_behavior['efficiency'] = (
                student_behavior['avg_score'] / (student_behavior['avg_time'] + 1)
            )
            
            # 计算综合评分
            student_behavior['comprehensive_score'] = self._calculate_comprehensive_score(
                student_behavior
            )
            
            return {
                'status': 'success',
                'data': student_behavior.to_dict('records'),
                'summary': {
                    'total_students': len(student_behavior),
                    'avg_efficiency': round(student_behavior['efficiency'].mean(), 4),
                    'avg_frequency': round(student_behavior['learning_frequency'].mean(), 2),
                    'most_stable_student': student_behavior.loc[
                        student_behavior['score_cv'].idxmin(), 'student_id'
                    ] if len(student_behavior) > 0 else None
                }
            }
            
        except Exception as e:
            logger.error(f"学习行为分析失败: {str(e)}")
            return self._empty_result("学习行为分析")
    
    def _calculate_comprehensive_score(self, df):
        """
        计算综合评分
        
        使用加权平均方法：
        - 正确率权重: 40%
        - 学习频率权重: 20%
        - 学习稳定性权重: 20%
        - 学习效率权重: 20%
        """
        # 标准化各指标
        scaler = MinMaxScaler()
        
        features_to_scale = ['avg_score', 'learning_frequency', 'score_cv', 'efficiency']
        for col in features_to_scale:
            if col in df.columns:
                df[col + '_normalized'] = scaler.fit_transform(df[[col]].fillna(0))
        
        # 计算综合评分
        comprehensive_score = (
            df.get('avg_score_normalized', 0) * 0.4 +
            df.get('learning_frequency_normalized', 0) * 0.2 +
            (1 - df.get('score_cv_normalized', 0)) * 0.2 +  # 稳定性越高越好
            df.get('efficiency_normalized', 0) * 0.2
        ) * 100
        
        return comprehensive_score
    
    def analyze_topic_correlations(self, submissions_df):
        """
        分析知识点之间的关联性
        
        使用皮尔逊相关系数衡量知识点之间的相关性
        
        返回:
            dict: 知识点关联分析结果
        """
        logger.info("开始分析知识点关联性...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("知识点关联分析")
        
        try:
            # 创建知识点-得分矩阵
            topic_scores = submissions_df.pivot_table(
                values='score',
                index='student_id',
                columns='question_topic',
                aggfunc='mean'
            ).fillna(0)
            
            # 计算相关系数矩阵
            correlation_matrix = topic_scores.corr(method='pearson')
            
            # 提取强相关的知识点对
            strong_correlations = []
            topics = correlation_matrix.columns
            for i in range(len(topics)):
                for j in range(i+1, len(topics)):
                    corr = correlation_matrix.iloc[i, j]
                    if abs(corr) >= 0.5:  # 筛选相关系数绝对值>=0.5的配对
                        strong_correlations.append({
                            'topic1': topics[i],
                            'topic2': topics[j],
                            'correlation': round(corr, 4),
                            'strength': self._interpret_correlation(corr)
                        })
            
            # 按相关系数排序
            strong_correlations = sorted(
                strong_correlations, 
                key=lambda x: abs(x['correlation']), 
                reverse=True
            )
            
            return {
                'status': 'success',
                'correlation_matrix': correlation_matrix.to_dict(),
                'strong_correlations': strong_correlations,
                'summary': {
                    'total_pairs': len(strong_correlations),
                    'strong_positive': sum(1 for c in strong_correlations if c['correlation'] > 0.7),
                    'strong_negative': sum(1 for c in strong_correlations if c['correlation'] < -0.7),
                    'moderate': sum(1 for c in strong_correlations if 0.5 <= abs(c['correlation']) < 0.7)
                }
            }
            
        except Exception as e:
            logger.error(f"知识点关联分析失败: {str(e)}")
            return self._empty_result("知识点关联分析")
    
    def _interpret_correlation(self, corr):
        """解释相关系数强度"""
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return '非常强'
        elif abs_corr >= 0.6:
            return '强'
        elif abs_corr >= 0.4:
            return '中等'
        elif abs_corr >= 0.2:
            return '弱'
        else:
            return '非常弱'
    
    def analyze_time_patterns(self, submissions_df):
        """
        分析学习时间模式
        
        包括：
        - 周期性分析（周内分布）
        - 时段偏好分析
        - 学习高峰识别
        - 遗忘曲线分析
        
        返回:
            dict: 时间模式分析结果
        """
        logger.info("开始分析学习时间模式...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("时间模式分析")
        
        try:
            # 转换时间列
            submissions_df = submissions_df.copy()
            if 'submit_time' in submissions_df.columns:
                submissions_df['submit_time'] = pd.to_datetime(submissions_df['submit_time'])
                
                # 提取时间特征
                submissions_df['hour'] = submissions_df['submit_time'].dt.hour
                submissions_df['day_of_week'] = submissions_df['submit_time'].dt.dayofweek
                submissions_df['day_name'] = submissions_df['submit_time'].dt.day_name()
                submissions_df['week'] = submissions_df['submit_time'].dt.isocalendar().week
                submissions_df['month'] = submissions_df['submit_time'].dt.month
            
            # 1. 周内分布分析
            weekly_distribution = submissions_df.groupby('day_of_week').size()
            weekly_accuracy = submissions_df.groupby('day_of_week')['score'].mean()
            
            weekly_pattern = pd.DataFrame({
                'submission_count': weekly_distribution,
                'avg_score': weekly_accuracy,
                'day_name': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][:len(weekly_distribution)]
            }).reset_index()
            
            # 2. 时段分析
            submissions_df['time_period'] = pd.cut(
                submissions_df['hour'],
                bins=[0, 6, 9, 12, 14, 18, 21, 24],
                labels=['深夜', '早上', '上午', '中午', '下午', '晚上', '深夜'],
                ordered=False
            )
            
            time_period_stats = submissions_df.groupby('time_period').agg({
                'score': ['count', 'mean', 'std'],
                'time_consumed': 'mean'
            }).reset_index()
            
            time_period_stats.columns = ['period', 'count', 'avg_score', 'score_std', 'avg_time']
            
            # 识别学习高峰
            peak_hour = submissions_df.groupby('hour').size().idxmax()
            peak_day = submissions_df.groupby('day_of_week').size().idxmax()
            day_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
            
            # 3. 学习效率最佳时段
            best_period = time_period_stats.loc[
                time_period_stats['avg_score'].idxmax(), 'period'
            ] if len(time_period_stats) > 0 else None
            
            # 4. 周期性检测（检测学习是否有周期性模式）
            hourly_distribution = submissions_df.groupby('hour').size()
            
            # 使用自相关检测周期性
            if len(hourly_distribution) > 24:
                autocorr = pd.Series(hourly_distribution).autocorr(lag=24)
            else:
                autocorr = 0
            
            return {
                'status': 'success',
                'weekly_pattern': weekly_pattern.to_dict('records'),
                'time_period_stats': time_period_stats.to_dict('records'),
                'peak_hours': {
                    'peak_hour': int(peak_hour),
                    'peak_day': day_names.get(peak_day, '未知'),
                    'best_learning_period': str(best_period)
                },
                'periodicity': {
                    'autocorrelation': round(autocorr, 4),
                    'has_periodicity': abs(autocorr) > 0.5
                },
                'summary': {
                    'total_records': len(submissions_df),
                    'avg_daily_submissions': round(len(submissions_df) / submissions_df['submit_time'].dt.date.nunique(), 2),
                    'most_active_day': day_names.get(weekly_distribution.idxmax(), '未知')
                }
            }
            
        except Exception as e:
            logger.error(f"时间模式分析失败: {str(e)}")
            return self._empty_result("时间模式分析")
    
    def analyze_learning_difficulty(self, submissions_df):
        """
        分析题目难度与学生学习表现的关系
        
        返回:
            dict: 难度分析结果
        """
        logger.info("开始分析学习难度模式...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("难度分析")
        
        try:
            # 难度分布分析
            difficulty_stats = submissions_df.groupby('difficulty').agg({
                'score': ['count', 'mean', 'std', 'min', 'max'],
                'time_consumed': ['mean', 'std']
            }).reset_index()
            
            difficulty_stats.columns = [
                'difficulty', 'count', 'avg_score', 'score_std', 'min_score', 'max_score',
                'avg_time', 'time_std'
            ]
            
            # 计算难度系数（区分度）
            # 难度系数 = 1 - 平均得分率
            difficulty_stats['difficulty_coef'] = 1 - (difficulty_stats['avg_score'] / 100)
            
            # 区分度分析（高分组与低分组的得分差异）
            # 假设高分组为前27%，低分组为后27%
            high_percentile = submissions_df['score'].quantile(0.73)
            low_percentile = submissions_df['score'].quantile(0.27)
            
            high_group = submissions_df[submissions_df['score'] >= high_percentile]
            low_group = submissions_df[submissions_df['score'] <= low_percentile]
            
            discrimination_by_difficulty = []
            for diff in difficulty_stats['difficulty']:
                high_in_diff = high_group[high_group['difficulty'] == diff]['score'].mean()
                low_in_diff = low_group[low_group['difficulty'] == diff]['score'].mean()
                
                discrimination = high_in_diff - low_in_diff if high_in_diff and low_in_diff else 0
                
                discrimination_by_difficulty.append({
                    'difficulty': diff,
                    'high_group_avg': round(high_in_diff, 2) if high_in_diff else 0,
                    'low_group_avg': round(low_in_diff, 2) if low_in_diff else 0,
                    'discrimination_index': round(discrimination, 2)
                })
            
            # 难度-用时关系
            difficulty_time_corr = difficulty_stats['difficulty_coef'].corr(
                difficulty_stats['avg_time']
            )
            
            return {
                'status': 'success',
                'difficulty_stats': difficulty_stats.to_dict('records'),
                'discrimination_analysis': discrimination_by_difficulty,
                'difficulty_time_correlation': round(difficulty_time_corr, 4),
                'summary': {
                    'total_difficulties': len(difficulty_stats),
                    'hardest_topic': difficulty_stats.loc[
                        difficulty_stats['avg_score'].idxmin(), 'difficulty'
                    ] if len(difficulty_stats) > 0 else None,
                    'easiest_topic': difficulty_stats.loc[
                        difficulty_stats['avg_score'].idxmax(), 'difficulty'
                    ] if len(difficulty_stats) > 0 else None,
                    'avg_discrimination': round(
                        np.mean([d['discrimination_index'] for d in discrimination_by_difficulty]), 2
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"难度分析失败: {str(e)}")
            return self._empty_result("难度分析")
    
    def analyze_learning_trend(self, submissions_df, window_size=7):
        """
        分析学习趋势与进步情况
        
        参数:
            window_size: 移动平均窗口大小
        
        返回:
            dict: 趋势分析结果
        """
        logger.info("开始分析学习趋势...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("趋势分析")
        
        try:
            submissions_df = submissions_df.copy()
            submissions_df['submit_time'] = pd.to_datetime(submissions_df['submit_time'])
            submissions_df = submissions_df.sort_values('submit_time')
            
            # 计算每日/每周统计
            daily_stats = submissions_df.groupby(submissions_df['submit_time'].dt.date).agg({
                'score': ['count', 'mean', 'std'],
                'time_consumed': 'mean',
                'student_id': 'nunique'
            }).reset_index()
            
            daily_stats.columns = ['date', 'submission_count', 'avg_score', 'score_std', 'avg_time', 'unique_students']
            
            # 移动平均
            daily_stats['ma_score'] = daily_stats['avg_score'].rolling(window=window_size, min_periods=1).mean()
            daily_stats['ma_count'] = daily_stats['submission_count'].rolling(window=window_size, min_periods=1).mean()
            
            # 计算进步率
            daily_stats['score_change'] = daily_stats['avg_score'].diff()
            daily_stats['score_change_rate'] = daily_stats['score_change'] / daily_stats['avg_score'].shift(1)
            
            # 趋势判断
            if len(daily_stats) >= 7:
                recent_week = daily_stats.tail(7)
                earlier_week = daily_stats.iloc[-14:-7] if len(daily_stats) >= 14 else daily_stats.head(7)
                
                recent_avg = recent_week['avg_score'].mean()
                earlier_avg = earlier_week['avg_score'].mean()
                
                trend_direction = '上升' if recent_avg > earlier_avg else '下降' if recent_avg < earlier_avg else '平稳'
                trend_magnitude = round((recent_avg - earlier_avg) / earlier_avg * 100, 2) if earlier_avg != 0 else 0
            else:
                trend_direction = '数据不足'
                trend_magnitude = 0
            
            # 计算峰值和谷值
            if len(daily_stats) >= 3:
                scores = daily_stats['avg_score'].values
                peaks, _ = find_peaks(scores)
                valleys, _ = find_peaks(-scores)
                
                peak_dates = [(daily_stats.iloc[p]['date'], daily_stats.iloc[p]['avg_score']) for p in peaks]
                valley_dates = [(daily_stats.iloc[v]['date'], daily_stats.iloc[v]['avg_score']) for v in valleys]
            else:
                peak_dates = []
                valley_dates = []
            
            return {
                'status': 'success',
                'daily_trend': daily_stats.to_dict('records'),
                'trend_analysis': {
                    'direction': trend_direction,
                    'magnitude': trend_magnitude,
                    'recent_avg_score': round(recent_avg, 2) if recent_week is not None else 0,
                    'earlier_avg_score': round(earlier_avg, 2) if earlier_week is not None else 0
                },
                'extremes': {
                    'peaks': peak_dates[-3:],  # 最近3个峰值
                    'valleys': valley_dates[-3:]  # 最近3个谷值
                },
                'summary': {
                    'analysis_period_days': len(daily_stats),
                    'overall_progress': round(daily_stats['avg_score'].iloc[-1] - daily_stats['avg_score'].iloc[0], 2) if len(daily_stats) > 1 else 0,
                    'max_daily_score': round(daily_stats['avg_score'].max(), 2),
                    'min_daily_score': round(daily_stats['avg_score'].min(), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return self._empty_result("趋势分析")
    
    def cluster_students(self, submissions_df, n_clusters=4):
        """
        学生聚类分析
        
        将学生按学习行为特征进行聚类分组
        
        参数:
            n_clusters: 聚类数量
        
        返回:
            dict: 聚类分析结果
        """
        logger.info(f"开始学生聚类分析 (聚类数={n_clusters})...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("学生聚类")
        
        try:
            # 提取学生特征
            student_features = submissions_df.groupby('student_id').agg({
                'score': ['mean', 'std', 'max'],
                'time_consumed': ['mean', 'std'],
                'question_topic': 'nunique',
                'id': 'count'
            }).reset_index()
            
            student_features.columns = [
                'student_id', 'avg_score', 'score_std', 'max_score',
                'avg_time', 'time_std', 'topic_diversity', 'total_attempts'
            ]
            
            # 处理缺失值
            student_features = student_features.fillna(0)
            
            # 特征标准化
            feature_cols = ['avg_score', 'score_std', 'avg_time', 'topic_diversity', 'total_attempts']
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(student_features[feature_cols])
            
            # K-Means聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            student_features['cluster'] = kmeans.fit_predict(scaled_features)
            
            # 评估聚类质量
            silhouette = silhouette_score(scaled_features, student_features['cluster'])
            calinski = calinski_harabasz_score(scaled_features, student_features['cluster'])
            
            # 分析每个簇的特征
            cluster_profiles = student_features.groupby('cluster').agg({
                'avg_score': 'mean',
                'score_std': 'mean',
                'avg_time': 'mean',
                'topic_diversity': 'mean',
                'total_attempts': 'mean',
                'student_id': 'count'
            }).reset_index()
            
            cluster_profiles.columns = [
                'cluster', 'avg_score', 'avg_score_std', 'avg_time',
                'topic_diversity', 'total_attempts', 'student_count'
            ]
            
            # 为每个簇命名
            cluster_names = self._assign_cluster_names(cluster_profiles)
            cluster_profiles['cluster_name'] = cluster_profiles['cluster'].map(cluster_names)
            
            # 每个学生的簇标签
            student_clusters = student_features[['student_id', 'cluster']].copy()
            student_clusters['cluster_name'] = student_clusters['cluster'].map(cluster_names)
            
            return {
                'status': 'success',
                'cluster_profiles': cluster_profiles.to_dict('records'),
                'student_clusters': student_clusters.to_dict('records'),
                'clustering_quality': {
                    'silhouette_score': round(silhouette, 4),
                    'calinski_harabasz_score': round(calinski, 4),
                    'optimal_clusters': n_clusters
                },
                'summary': {
                    'total_students': len(student_features),
                    'clusters': n_clusters,
                    'largest_cluster': int(cluster_profiles.loc[
                        cluster_profiles['student_count'].idxmax(), 'cluster'
                    ]),
                    'smallest_cluster': int(cluster_profiles.loc[
                        cluster_profiles['student_count'].idxmin(), 'cluster'
                    ])
                }
            }
            
        except Exception as e:
            logger.error(f"学生聚类分析失败: {str(e)}")
            return self._empty_result("学生聚类")
    
    def _assign_cluster_names(self, cluster_profiles):
        """根据簇特征分配描述性名称"""
        names = {}
        
        # 按平均分排序
        sorted_clusters = cluster_profiles.sort_values('avg_score', ascending=False)
        
        # 根据排名分配名称
        name_map = {
            0: '学霸型',  # 得分最高
            1: '勤奋型',  # 尝试次数多
            2: '稳定型',  # 得分中等
            3: '待提升型'  # 需要帮助
        }
        
        for idx, (_, row) in enumerate(sorted_clusters.iterrows()):
            names[row['cluster']] = name_map.get(idx, f'类型{idx}')
        
        return names
    
    def predict_learning_outcome(self, submissions_df, test_size=0.2):
        """
        预测学习效果
        
        使用机器学习模型预测学生表现
        
        参数:
            test_size: 测试集比例
        
        返回:
            dict: 预测模型结果
        """
        logger.info("开始学习效果预测...")
        
        if submissions_df is None or submissions_df.empty:
            return self._empty_result("效果预测")
        
        try:
            # 准备特征
            student_features = submissions_df.groupby('student_id').agg({
                'score': ['mean', 'std', 'max', 'min'],
                'time_consumed': ['mean', 'std'],
                'question_topic': 'nunique',
                'id': 'count',
                'difficulty': lambda x: (x == '困难').sum() / len(x)  # 难题比例
            }).reset_index()
            
            student_features.columns = [
                'student_id', 'avg_score', 'score_std', 'max_score', 'min_score',
                'avg_time', 'time_std', 'topic_diversity', 'total_attempts', 'hard_ratio'
            ]
            
            # 填充缺失值
            student_features = student_features.fillna(0)
            
            # 创建目标变量：表现等级
            student_features['performance_level'] = pd.cut(
                student_features['avg_score'],
                bins=[0, 60, 75, 85, 100],
                labels=['待提高', '一般', '良好', '优秀']
            )
            
            # 准备训练数据
            feature_cols = ['score_std', 'avg_time', 'topic_diversity', 'total_attempts', 'hard_ratio']
            X = student_features[feature_cols]
            y = student_features['performance_level']
            
            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # 训练随机森林分类器
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train, y_train)
            
            # 评估模型
            y_pred = clf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='weighted', zero_division=0
            )
            
            # 特征重要性
            importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': clf.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # 交叉验证
            cv_scores = cross_val_score(clf, X, y, cv=5)
            
            return {
                'status': 'success',
                'model_performance': {
                    'accuracy': round(accuracy, 4),
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1, 4),
                    'cv_mean': round(cv_scores.mean(), 4),
                    'cv_std': round(cv_scores.std(), 4)
                },
                'feature_importance': importance.to_dict('records'),
                'model_type': 'RandomForestClassifier',
                'summary': {
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'most_important_feature': importance.iloc[0]['feature'] if len(importance) > 0 else None
                }
            }
            
        except Exception as e:
            logger.error(f"效果预测失败: {str(e)}")
            return self._empty_result("效果预测")
    
    def generate_insights(self, submissions_df):
        """
        生成数据洞察
        
        综合分析结果，生成可操作的洞察和建议
        
        返回:
            dict: 洞察和建议
        """
        logger.info("开始生成数据洞察...")
        
        insights = []
        
        # 分析1: 学习时段洞察
        if submissions_df is not None and not submissions_df.empty:
            try:
                submissions_df['submit_time'] = pd.to_datetime(submissions_df['submit_time'])
                submissions_df['hour'] = submissions_df['submit_time'].dt.hour
                
                # 找出最佳和最差时段
                hourly_perf = submissions_df.groupby('hour')['score'].mean()
                best_hour = hourly_perf.idxmax()
                worst_hour = hourly_perf.idxmin()
                
                insights.append({
                    'type': 'time',
                    'title': '学习时段建议',
                    'description': f'数据显示{best_hour}点学习的平均正确率最高({hourly_perf[best_hour]:.1f}分)，'
                                  f'建议将重点学习安排在该时段。'
                })
            except Exception:
                pass
        
        # 分析2: 知识点洞察
        try:
            if submissions_df is not None and not submissions_df.empty:
                topic_perf = submissions_df.groupby('question_topic')['score'].mean()
                weak_topics = topic_perf[topic_perf < topic_perf.mean() * 0.9].index.tolist()
                
                if weak_topics:
                    insights.append({
                        'type': 'topic',
                        'title': '薄弱知识点提醒',
                        'description': f'以下知识点正确率低于平均水平，建议加强练习：{", ".join(weak_topics[:3])}'
                    })
        except Exception:
            pass
        
        # 分析3: 学习模式洞察
        try:
            if submissions_df is not None and not submissions_df.empty:
                student_counts = submissions_df.groupby('student_id').size()
                active_students = student_counts[student_counts > student_counts.median()]
                
                if len(active_students) > 0:
                    insights.append({
                        'type': 'engagement',
                        'title': '学习积极性分析',
                        'description': f'约{len(active_students)/len(student_counts)*100:.0f}%的学生学习积极性较高，'
                                      f'建议关注学习频率较低的学生群体。'
                    })
        except Exception:
            pass
        
        return {
            'status': 'success',
            'insights': insights,
            'summary': {
                'total_insights': len(insights),
                'actionable_count': len([i for i in insights if i.get('type') == 'time'])
            }
        }
    
    def _empty_result(self, analysis_type):
        """返回空结果"""
        return {
            'status': 'empty',
            'analysis_type': analysis_type,
            'message': f'{analysis_type}结果为空，请检查数据是否充足'
        }


# 创建全局分析器实例
big_data_analyzer = BigDataAnalyzer()


def get_big_data_analysis_results(submissions_df):
    """
    获取完整的分析结果
    
    参数:
        submissions_df: 答题记录DataFrame
    
    返回:
        dict: 包含所有分析结果的字典
    """
    analyzer = BigDataAnalyzer()
    
    results = {
        'generated_at': datetime.now().isoformat(),
        'student_behavior': analyzer.analyze_student_behavior(submissions_df),
        'topic_correlations': analyzer.analyze_topic_correlations(submissions_df),
        'time_patterns': analyzer.analyze_time_patterns(submissions_df),
        'learning_difficulty': analyzer.analyze_learning_difficulty(submissions_df),
        'learning_trend': analyzer.analyze_learning_trend(submissions_df),
        'student_clusters': analyzer.cluster_students(submissions_df),
        'outcome_prediction': analyzer.predict_learning_outcome(submissions_df),
        'insights': analyzer.generate_insights(submissions_df)
    }
    
    return results


if __name__ == '__main__':
    # 测试代码
    print("大数据分析模块加载成功")
    print("可用分析方法:")
    print("1. analyze_student_behavior - 学生行为分析")
    print("2. analyze_topic_correlations - 知识点关联分析")
    print("3. analyze_time_patterns - 时间模式分析")
    print("4. analyze_learning_difficulty - 难度分析")
    print("5. analyze_learning_trend - 趋势分析")
    print("6. cluster_students - 学生聚类")
    print("7. predict_learning_outcome - 效果预测")
    print("8. generate_insights - 洞察生成")
