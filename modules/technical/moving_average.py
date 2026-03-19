"""
移动平均线指标模块
提供SMA、EMA、WMA、HMA等多种移动平均线计算
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, Tuple


def sma(prices: pd.Series, period: int = 20) -> pd.Series:
    """
    计算简单移动平均线 (Simple Moving Average)
    
    Args:
        prices: 价格序列
        period: 计算周期
        
    Returns:
        SMA序列
    """
    return prices.rolling(window=period, min_periods=1).mean()


def ema(prices: pd.Series, period: int = 20, adjust: bool = True) -> pd.Series:
    """
    计算指数移动平均线 (Exponential Moving Average)
    
    Args:
        prices: 价格序列
        period: 计算周期
        adjust: 是否调整
        
    Returns:
        EMA序列
    """
    return prices.ewm(span=period, adjust=adjust, min_periods=1).mean()


def wma(prices: pd.Series, period: int = 20) -> pd.Series:
    """
    计算加权移动平均线 (Weighted Moving Average)
    
    Args:
        prices: 价格序列
        period: 计算周期
        
    Returns:
        WMA序列
    """
    weights = np.arange(1, period + 1)
    return prices.rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def hull_ma(prices: pd.Series, period: int = 20) -> pd.Series:
    """
    计算赫尔移动平均线 (Hull Moving Average)
    
    Args:
        prices: 价格序列
        period: 计算周期
        
    Returns:
        HMA序列
    """
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    
    wma_half = wma(prices, half_period)
    wma_full = wma(prices, period)
    
    raw_hma = 2 * wma_half - wma_full
    hma = wma(raw_hma, sqrt_period)
    
    return hma


def golden_cross(short_ma: pd.Series, long_ma: pd.Series) -> pd.Series:
    """
    检测金叉信号
    
    Args:
        short_ma: 短期均线
        long_ma: 长期均线
        
    Returns:
        金叉信号序列 (True表示金叉)
    """
    prev_short = short_ma.shift(1)
    prev_long = long_ma.shift(1)
    
    # 昨天短期<长期，今天短期>长期
    golden = (prev_short < prev_long) & (short_ma > long_ma)
    return golden


def death_cross(short_ma: pd.Series, long_ma: pd.Series) -> pd.Series:
    """
    检测死叉信号
    
    Args:
        short_ma: 短期均线
        long_ma: 长期均线
        
    Returns:
        死叉信号序列 (True表示死叉)
    """
    prev_short = short_ma.shift(1)
    prev_long = long_ma.shift(1)
    
    # 昨天短期>长期，今天短期<长期
    death = (prev_short > prev_long) & (short_ma < long_ma)
    return death


def ma_trend(ma: pd.Series, lookback: int = 5) -> pd.Series:
    """
    判断均线趋势
    
    Args:
        ma: 均线序列
        lookback: 回顾周期
        
    Returns:
        趋势序列 (1:上升, -1:下降, 0:走平)
    """
    slope = (ma - ma.shift(lookback)) / lookback
    
    trend = pd.Series(0, index=ma.index)
    trend[slope > 0] = 1    # 上升
    trend[slope < 0] = -1   # 下降
    
    return trend


def ma_distance(prices: pd.Series, ma: pd.Series, method: str = 'absolute') -> pd.Series:
    """
    计算价格与均线的偏离度
    
    Args:
        prices: 价格序列
        ma: 均线序列
        method: 计算方法 ('absolute': 绝对偏离, 'relative': 相对偏离, 'percent': 百分比)
        
    Returns:
        偏离度序列
    """
    if method == 'absolute':
        return prices - ma
    elif method == 'relative':
        return (prices - ma) / ma
    elif method == 'percent':
        return (prices - ma) / ma * 100
    else:
        raise ValueError(f"不支持的计算方法: {method}")


def multi_timeframe_ma(prices: pd.Series, timeframes: list = None) -> pd.DataFrame:
    """
    计算多时间框架均线
    
    Args:
        prices: 价格序列
        timeframes: 时间框架列表 [(period, type), ...]
        
    Returns:
        多时间框架均线DataFrame
    """
    if timeframes is None:
        timeframes = [
            (5, 'sma'), (10, 'ema'), (20, 'ema'), 
            (60, 'sma'), (120, 'sma'), (250, 'sma')
        ]
    
    result = pd.DataFrame(index=prices.index)
    
    for period, ma_type in timeframes:
        col_name = f"{ma_type.upper()}_{period}"
        
        if ma_type == 'sma':
            result[col_name] = sma(prices, period)
        elif ma_type == 'ema':
            result[col_name] = ema(prices, period)
        elif ma_type == 'wma':
            result[col_name] = wma(prices, period)
        elif ma_type == 'hma':
            result[col_name] = hull_ma(prices, period)
    
    return result
