# -*- coding: utf-8 -*-
"""
经济参数估计模块
用于建模和预测经济参数
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ParameterType(Enum):
    """参数类型"""
    GDP_GROWTH = "GDP增长率"
    CPI = "消费者物价指数"
    PPI = "生产者物价指数"
    INTEREST_RATE = "利率水平"
    UNEMPLOYMENT = "失业率"
    MONEY_SUPPLY = "货币供应量"

@dataclass
class EstimationResult:
    """估计结果"""
    parameter: ParameterType
    estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    r_squared: float
    p_value: float
    sample_size: int

class ParameterEstimator:
    """
    经济参数估计器
    用于参数估计和预测
    """
    
    def __init__(self, model_type: str = "arima"):
        """
        初始化参数估计器
        
        Args:
            model_type: 模型类型，可选 "arima", "sarima", "prophet"
        """
        self.model_type = model_type
        
    def generate_synthetic_data(self, parameter_type: ParameterType, 
                              periods: int = 120, trend: float = 0.0,
                              volatility: float = 0.1) -> pd.DataFrame:
        """
        生成合成数据
        
        Args:
            parameter_type: 参数类型
            periods: 数据点数量
            trend: 趋势参数
            volatility: 波动率
            
        Returns:
            数据DataFrame
        """
        # 基础值
        base_values = {
            ParameterType.GDP_GROWTH: 6.0,
            ParameterType.CPI: 2.5,
            ParameterType.PPI: 3.0,
            ParameterType.INTEREST_RATE: 4.0,
            ParameterType.UNEMPLOYMENT: 5.0,
            ParameterType.MONEY_SUPPLY: 8.0
        }
        
        base_value = base_values.get(parameter_type, 5.0)
        
        # 生成趋势
        trend_values = np.arange(periods) * trend
        
        # 生成随机波动
        random_values = np.random.normal(0, volatility, periods)
        
        # 生成最终数据
        values = base_value + trend_values + random_values
        
        # 确保数据合理范围
        if parameter_type == ParameterType.UNEMPLOYMENT:
            values = np.clip(values, 2, 10)
        elif parameter_type == ParameterType.CPI:
            values = np.clip(values, -2, 10)
        
        # 创建DataFrame
        dates = pd.date_range(start='2019-01-01', periods=periods, freq='M')
        
        return pd.DataFrame({
            'date': dates,
            'value': values,
            'parameter': parameter_type.value
        })
    
    def estimate_parameter(self, parameter_type: ParameterType, 
                         data: pd.DataFrame, 
                         confidence_level: float = 0.95) -> EstimationResult:
        """
        参数估计
        
        Args:
            parameter_type: 参数类型
            data: 数据
            confidence_level: 置信水平
            
        Returns:
            EstimationResult对象
        """
        # 使用简单统计方法
        mean_value = data['value'].mean()
        std_value = data['value'].std()
        sample_size = len(data)
        
        # 计算置信区间
        z_score = 1.96  # 95%置信水平
        if confidence_level == 0.90:
            z_score = 1.645
        elif confidence_level == 0.99:
            z_score = 2.576
            
        margin_error = z_score * (std_value / np.sqrt(sample_size))
        lower_bound = mean_value - margin_error
        upper_bound = mean_value + margin_error
        
        # 简单R平方计算
        trend_line = np.polyfit(np.arange(len(data)), data['value'], 1)
        trend_values = np.polyval(trend_line, np.arange(len(data)))
        r_squared = np.corrcoef(data['value'], trend_values)[0, 1] ** 2
        
        return EstimationResult(
            parameter=parameter_type,
            estimate=mean_value,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=confidence_level,
            r_squared=r_squared,
            p_value=0.05,
            sample_size=sample_size
        )
    
    def forecast_parameter(self, parameter_type: ParameterType, 
                        data: pd.DataFrame, 
                        forecast_horizon: int = 12) -> pd.DataFrame:
        """
        参数预测
        
        Args:
            parameter_type: 参数类型
            data: 历史数据
            forecast_horizon: 预测期数
            
        Returns:
            预测结果DataFrame
        """
        # 简单的线性回归预测
        x = np.arange(len(data)).reshape(-1, 1)
        y = data['value'].values
        
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(x, y)
        
        # 预测
        future_x = np.arange(len(data), len(data) + forecast_horizon).reshape(-1, 1)
        future_y = model.predict(future_x)
        
        # 生成预测日期
        last_date = data['date'].iloc[-1]
        future_dates = pd.date_range(start=last_date, periods=forecast_horizon, freq='M')
        
        return pd.DataFrame({
            'date': future_dates,
            'predicted_value': future_y,
            'parameter': parameter_type.value
        })
    
    def analyze_parameter_trend(self, parameter_type: ParameterType, 
                              data: pd.DataFrame) -> Dict:
        """
        趋势分析
        
        Args:
            parameter_type: 参数类型
            data: 数据
            
        Returns:
            趋势分析结果
        """
        # 计算一阶差分
        data['diff'] = data['value'].diff()
        
        # 计算趋势强度
        trend = np.polyfit(np.arange(len(data)), data['value'], 1)[0]
        
        # 计算波动率
        volatility = data['value'].std()
        
        # 计算变化率
        change_rate = data['value'].pct_change().mean()
        
        # 趋势分类
        trend_strength = '强' if abs(trend) > 0.1 else '中' if abs(trend) > 0.05 else '弱'
        trend_direction = '向上' if trend > 0 else '向下' if trend < 0 else '平稳'
        
        return {
            'trend_strength': trend_strength,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'change_rate': change_rate,
            'recent_value': data['value'].iloc[-1],
            'mean_value': data['value'].mean(),
            'min_value': data['value'].min(),
            'max_value': data['value'].max()
        }
