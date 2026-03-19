# -*- coding: utf-8 -*-
"""
分型分析器

实现缠论中的分型概念，用于识别顶分型、底分型和趋势方向
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


class FractalType(Enum):
    """分型类型"""
    TOP = "top"           # 顶分型
    BOTTOM = "bottom"     # 底分型
    NONE = "none"         # 无分型


class TrendDirection(Enum):
    """趋势方向"""
    UP = "up"             # 上涨
    DOWN = "down"         # 下跌
    CONSOLIDATION = "consolidation"  # 盘整


@dataclass
class KLine:
    """K线数据"""
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    date: str = ""
    
    def __post_init__(self):
        """验证数据有效性"""
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be less than low ({self.low})")
        if self.open < self.low or self.open > self.high:
            raise ValueError(f"Open price ({self.open}) out of range")
        if self.close < self.low or self.close > self.high:
            raise ValueError(f"Close price ({self.close}) out of range")
    
    @property
    def is_bullish(self) -> bool:
        """是否为阳线"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """是否为阴线"""
        return self.close < self.open
    
    @property
    def body(self) -> float:
        """K线实体长度"""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """上影线长度"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """下影线长度"""
        return min(self.open, self.close) - self.low


@dataclass
class Fractal:
    """分型结构"""
    fractal_type: FractalType
    center_kline: KLine
    left_kline: KLine
    right_kline: KLine
    confirmation_index: int
    strength: float = 0.0
    
    def __post_init__(self):
        """计算分型强度"""
        self.strength = self._calculate_strength()
    
    def _calculate_strength(self) -> float:
        """
        计算分型强度
        
        基于：
        1. 第三根K线的实体大小
        2. 分型确认后的走势
        3. 成交量配合
        
        Returns:
            强度值 (0-1)
        """
        # 基础强度
        strength = 0.5
        
        # 根据分型类型调整
        if self.fractal_type == FractalType.TOP:
            # 顶分型：第三根K线越长，强度越高
            body_ratio = self.right_kline.body / (self.center_kline.high - self.center_kline.low + 1e-6)
            strength += body_ratio * 0.3
            
            # 阴线加分
            if self.right_kline.is_bearish:
                strength += 0.1
        
        elif self.fractal_type == FractalType.BOTTOM:
            # 底分型：第三根K线越长，强度越高
            body_ratio = self.right_kline.body / (self.center_kline.high - self.center_kline.low + 1e-6)
            strength += body_ratio * 0.3
            
            # 阳线加分
            if self.right_kline.is_bullish:
                strength += 0.1
        
        return min(max(strength, 0.0), 1.0)


class FractalAnalyzer:
    """
    分型分析器
    
    实现缠论中的分型概念：
    - 顶分型：中间K线的高点高于左右两边K线的高点
    - 底分型：中间K线的低点低于左右两边K线的低点
    
    分型是判断趋势转折的重要信号
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.min_fractal_strength = self.config.get('min_fractal_strength', 0.3)
        self.lookback_periods = self.config.get('lookback_periods', 5)
    
    def identify_fractals(self, klines: List[KLine]) -> List[Fractal]:
        """
        识别所有分型
        
        Args:
            klines: K线数据列表
            
        Returns:
            分型列表
        """
        fractals = []
        
        # 需要至少3根K线
        if len(klines) < 3:
            return fractals
        
        # 遍历查找分型
        for i in range(1, len(klines) - 1):
            left = klines[i - 1]
            center = klines[i]
            right = klines[i + 1]
            
            # 检查顶分型
            if self._is_top_fractal(left, center, right):
                fractal = Fractal(
                    fractal_type=FractalType.TOP,
                    center_kline=center,
                    left_kline=left,
                    right_kline=right,
                    confirmation_index=i + 1
                )
                if fractal.strength >= self.min_fractal_strength:
                    fractals.append(fractal)
            
            # 检查底分型
            elif self._is_bottom_fractal(left, center, right):
                fractal = Fractal(
                    fractal_type=FractalType.BOTTOM,
                    center_kline=center,
                    left_kline=left,
                    right_kline=right,
                    confirmation_index=i + 1
                )
                if fractal.strength >= self.min_fractal_strength:
                    fractals.append(fractal)
        
        return fractals
    
    def _is_top_fractal(self, left: KLine, center: KLine, right: KLine) -> bool:
        """
        判断是否为顶分型
        
        顶分型定义：
        - 中间K线的高点高于左右两边K线的高点
        
        Args:
            left: 左边K线
            center: 中间K线
            right: 右边K线
            
        Returns:
            是否为顶分型
        """
        return center.high > left.high and center.high > right.high
    
    def _is_bottom_fractal(self, left: KLine, center: KLine, right: KLine) -> bool:
        """
        判断是否为底分型
        
        底分型定义：
        - 中间K线的低点低于左右两边K线的低点
        
        Args:
            left: 左边K线
            center: 中间K线
            right: 右边K线
            
        Returns:
            是否为底分型
        """
        return center.low < left.low and center.low < right.low
    
    def get_trend_direction(self, recent_fractals: List[Fractal]) -> TrendDirection:
        """
        根据最近的分型判断趋势方向
        
        Args:
            recent_fractals: 最近的分型列表
            
        Returns:
            趋势方向
        """
        if len(recent_fractals) < 2:
            return TrendDirection.CONSOLIDATION
        
        # 取最近的两个分型
        last_two = recent_fractals[-2:]
        
        # 分析分型序列
        types = [f.fractal_type for f in last_two]
        
        # 顶分型后接底分型 = 下跌趋势
        if types == [FractalType.TOP, FractalType.BOTTOM]:
            return TrendDirection.DOWN
        
        # 底分型后接顶分型 = 上涨趋势
        elif types == [FractalType.BOTTOM, FractalType.TOP]:
            return TrendDirection.UP
        
        # 其他情况 = 盘整
        else:
            return TrendDirection.CONSOLIDATION
    
    def generate_trading_signals(self, klines: List[KLine], 
                                 lookback: int = 10) -> List[Dict]:
        """
        生成分型交易信号
        
        Args:
            klines: K线数据
            lookback: 回溯周期
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 识别分型
        fractals = self.identify_fractals(klines)
        
        # 获取最近的分型
        recent_fractals = fractals[-lookback:] if len(fractals) > lookback else fractals
        
        # 分析趋势
        trend = self.get_trend_direction(recent_fractals)
        
        # 生成信号
        for i, fractal in enumerate(recent_fractals):
            if fractal.fractal_type == FractalType.BOTTOM:
                signal = {
                    "type": "BUY",
                    "index": fractal.confirmation_index,
                    "price": fractal.right_kline.close,
                    "strength": fractal.strength,
                    "trend": trend.value,
                    "reason": "底分型确认"
                }
                signals.append(signal)
            
            elif fractal.fractal_type == FractalType.TOP:
                signal = {
                    "type": "SELL",
                    "index": fractal.confirmation_index,
                    "price": fractal.right_kline.close,
                    "strength": fractal.strength,
                    "trend": trend.value,
                    "reason": "顶分型确认"
                }
                signals.append(signal)
        
        return signals


if __name__ == "__main__":
    # 测试代码
    print("分型分析器测试")
    
    # 创建测试K线数据
    test_klines = [
        KLine(open=100, high=105, low=98, close=102),   # 1
        KLine(open=102, high=108, low=101, close=106),  # 2
        KLine(open=106, high=110, low=104, close=105),  # 3 - 顶分型中心
        KLine(open=105, high=107, low=102, close=103),  # 4
        KLine(open=103, high=104, low=99, close=100),   # 5
        KLine(open=100, high=101, low=95, close=96),    # 6 - 底分型中心
        KLine(open=96, high=98, low=94, close=97),      # 7
        KLine(open=97, high=100, low=96, close=99),     # 8
    ]
    
    # 创建分析器
    analyzer = FractalAnalyzer()
    
    # 识别分型
    fractals = analyzer.identify_fractals(test_klines)
    
    print(f"\n识别到 {len(fractals)} 个分型:")
    for i, fractal in enumerate(fractals, 1):
        print(f"\n分型 {i}:")
        print(f"  类型: {fractal.fractal_type.value}")
        print(f"  中心K线高点: {fractal.center_kline.high}")
        print(f"  中心K线低点: {fractal.center_kline.low}")
        print(f"  强度: {fractal.strength:.2f}")
    
    # 分析趋势
    trend = analyzer.get_trend_direction(fractals)
    print(f"\n趋势方向: {trend.value}")
    
    # 生成交易信号
    signals = analyzer.generate_trading_signals(test_klines)
    print(f"\n交易信号 ({len(signals)} 个):")
    for signal in signals:
        print(f"  {signal['type']}: 价格={signal['price']:.2f}, "
              f"强度={signal['strength']:.2f}, 原因={signal['reason']}")
