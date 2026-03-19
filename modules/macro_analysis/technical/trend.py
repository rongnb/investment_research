# -*- coding: utf-8 -*-
"""
趋势分析器

提供趋势识别、强度评估和预测功能
基于缠论理论和分型分析
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import math

from .fractal import Fractal, FractalType, KLine


class TrendStrength(Enum):
    """趋势强度"""
    EXTREMELY_STRONG = 5      # 极端强势
    VERY_STRONG = 4           # 非常强势
    STRONG = 3                # 强势
    MODERATE = 2              # 中等
    WEAK = 1                  # 弱势
    WEAKENING = 0             # 减弱
    REVERSAL = -1             # 反转


class TrendWave:
    """趋势波浪"""
    wave_type: str          # 推动浪/调整浪
    wave_level: int         # 浪级 (1-5)
    start_price: float
    end_price: float
    start_index: int
    end_index: int
    duration: int           # 持续K线数
    amplitude: float        # 幅度
    volume_profile: float   # 成交量特征


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    trend_direction: str              # 上涨/下跌/盘整
    trend_strength: TrendStrength     # 强度
    trend_duration: int               # 持续时间
    current_price: float
    support_levels: List[float]       # 支撑位
    resistance_levels: List[float]    # 阻力位
    potential_target: Optional[float] # 潜在目标位
    risk_reward: float                # 风险收益比
    confidence: float                 # 置信度
    key_points: List[Dict]            # 关键点分析


class TrendAnalyzer:
    """
    趋势分析器
    
    基于缠论和分型技术，提供：
    1. 趋势识别
    2. 强度评估
    3. 支撑阻力
    4. 目标位预测
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.trend_change_threshold = self.config.get('trend_change_threshold', 0.03)
        self.breakout_threshold = self.config.get('breakout_threshold', 0.02)
        self.volatility_window = self.config.get('volatility_window', 20)
    
    def analyze_trend(self, klines: List[KLine], 
                     fractals: List[Fractal]) -> TrendAnalysis:
        """
        分析趋势
        
        Args:
            klines: K线数据
            fractals: 分型列表
            
        Returns:
            趋势分析结果
        """
        # 基础分析
        current_price = klines[-1].close
        high = max(k.high for k in klines)
        low = min(k.low for k in klines)
        
        # 确定趋势方向
        trend_direction = self._determine_trend_direction(klines[-self.volatility_window:])
        
        # 计算趋势强度
        trend_strength = self._calculate_trend_strength(klines)
        
        # 计算支撑阻力位
        support_levels = self._calculate_support_levels(klines, fractals)
        resistance_levels = self._calculate_resistance_levels(klines, fractals)
        
        # 计算目标位
        potential_target = self._calculate_target_level(trend_direction, 
                                                       current_price, 
                                                       fractals)
        
        # 风险收益比
        risk_reward = self._calculate_risk_reward(current_price,
                                                support_levels,
                                                resistance_levels)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_duration=len(klines),
            current_price=current_price,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            potential_target=potential_target,
            risk_reward=risk_reward,
            confidence=0.7,
            key_points=self._identify_key_points(klines, fractals)
        )
    
    def _determine_trend_direction(self, recent_klines: List[KLine]) -> str:
        """确定趋势方向"""
        if len(recent_klines) < 10:
            return "consolidation"
        
        # 基于最高价和最低价的趋势判断
        high_trend = self._calculate_trend_line([k.high for k in recent_klines])
        low_trend = self._calculate_trend_line([k.low for k in recent_klines])
        
        if high_trend > self.trend_change_threshold and low_trend > self.trend_change_threshold:
            return "up"
        elif high_trend < -self.trend_change_threshold and low_trend < -self.trend_change_threshold:
            return "down"
        else:
            return "consolidation"
    
    def _calculate_trend_line(self, values: List[float]) -> float:
        """计算趋势线斜率"""
        n = len(values)
        if n < 2:
            return 0
        
        # 简单线性回归计算斜率
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_x_sq = sum(x*x for x in range(n))
        sum_xy = sum(x*y for x, y in enumerate(values))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x_sq - sum_x * sum_x
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _calculate_trend_strength(self, klines: List[KLine]) -> TrendStrength:
        """计算趋势强度"""
        if len(klines) < self.volatility_window:
            return TrendStrength.WEAK
        
        recent_klines = klines[-self.volatility_window:]
        
        # 计算价格波动率
        volatility = sum(abs(k.high - k.low) for k in recent_klines) / len(recent_klines)
        
        # 趋势延续性
        trend_score = self._calculate_trend_score(klines)
        
        # 综合评估
        if trend_score > 0.8 and volatility > 0.02:
            return TrendStrength.EXTREMELY_STRONG
        elif trend_score > 0.6:
            return TrendStrength.VERY_STRONG
        elif trend_score > 0.4:
            return TrendStrength.STRONG
        elif trend_score > 0.2:
            return TrendStrength.MODERATE
        elif trend_score > 0.1:
            return TrendStrength.WEAK
        else:
            return TrendStrength.WEAKENING
    
    def _calculate_trend_score(self, klines: List[KLine]) -> float:
        """计算趋势得分"""
        return 0.5
    
    def _calculate_support_levels(self, klines: List[KLine], 
                               fractals: List[Fractal]) -> List[float]:
        """计算支撑位"""
        supports = []
        
        # 从底分型中获取
        bottom_fractals = [f for f in fractals if f.fractal_type == FractalType.BOTTOM]
        for fractal in bottom_fractals:
            supports.append(fractal.center_kline.low)
        
        return sorted(list(set(supports)))[-3:]
    
    def _calculate_resistance_levels(self, klines: List[KLine], 
                                  fractals: List[Fractal]) -> List[float]:
        """计算阻力位"""
        resistances = []
        
        # 从顶分型中获取
        top_fractals = [f for f in fractals if f.fractal_type == FractalType.TOP]
        for fractal in top_fractals:
            resistances.append(fractal.center_kline.high)
        
        return sorted(list(set(resistances)))[-3:]
    
    def _calculate_target_level(self, trend_direction: str, 
                             current_price: float,
                             fractals: List[Fractal]) -> Optional[float]:
        """计算目标位"""
        if trend_direction == "up":
            bottom_fractals = [f for f in fractals if f.fractal_type == FractalType.BOTTOM]
            if len(bottom_fractals) >= 2:
                # 基础目标位
                base_target = current_price + 0.03
                return base_target
        elif trend_direction == "down":
            top_fractals = [f for f in fractals if f.fractal_type == FractalType.TOP]
            if len(top_fractals) >= 2:
                base_target = current_price - 0.03
                return base_target
        
        return None
    
    def _calculate_risk_reward(self, current_price: float,
                             support_levels: List[float],
                             resistance_levels: List[float]) -> float:
        """计算风险收益比"""
        risk = float('inf')
        reward = float('inf')
        
        # 计算风险（止损位）
        if support_levels:
            risk = current_price - min(support_levels)
        
        # 计算收益（目标位）
        if resistance_levels:
            reward = max(resistance_levels) - current_price
        
        if risk > 0 and reward > 0:
            return reward / risk
        
        return 1.0
    
    def _identify_key_points(self, klines: List[KLine], 
                           fractals: List[Fractal]) -> List[Dict]:
        """识别关键点"""
        key_points = []
        
        for i, fractal in enumerate(fractals):
            key_points.append({
                "index": fractal.confirmation_index,
                "type": fractal.fractal_type.value,
                "price": fractal.center_kline.close,
                "strength": fractal.strength
            })
        
        return key_points


class TrendContinuityDetector:
    """趋势延续性检测器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.continuity_threshold = self.config.get('continuity_threshold', 0.3)
    
    def check_trend_continuity(self, trend_history: List[TrendAnalysis]) -> bool:
        """
        检查趋势延续性
        
        Args:
            trend_history: 历史趋势分析结果
            
        Returns:
            是否延续
        """
        if len(trend_history) < 3:
            return True
        
        # 简单的延续性判断
        recent_directions = [t.trend_direction for t in trend_history[-3:]]
        
        if len(set(recent_directions)) == 1:
            return True
        
        return False
