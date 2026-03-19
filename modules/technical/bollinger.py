"""
布林带指标模块
提供布林带计算和信号生成
"""

import pandas as pd
import numpy as np
from .moving_average import sma


def bollinger_bands(prices: pd.Series, 
                    period: int = 20,
                    num_std: float = 2.0) -> pd.DataFrame:
    """
    计算布林带
    
    中轨 = N日移动平均线
    上轨 = 中轨 + k × 标准差
    下轨 = 中轨 - k × 标准差
    
    Args:
        prices: 价格序列
        period: 计算周期，默认20
        num_std: 标准差倍数，默认2.0
        
    Returns:
        DataFrame包含中轨、上轨、下轨
    """
    # 中轨 (N日移动平均线)
    middle_band = sma(prices, period)
    
    # 计算标准差
    rolling_std = prices.rolling(window=period).std()
    
    # 上轨和下轨
    upper_band = middle_band + (rolling_std * num_std)
    lower_band = middle_band - (rolling_std * num_std)
    
    return pd.DataFrame({
        'middle': middle_band,
        'upper': upper_band,
        'lower': lower_band
    })


def bandwidth(upper: pd.Series, lower: pd.Series, middle: pd.Series) -> pd.Series:
    """
    计算布林带宽度 (Bandwidth)
    
    带宽 = (上轨 - 下轨) / 中轨
    
    带宽收窄预示即将突破，带宽扩大预示趋势延续
    
    Args:
        upper: 上轨序列
        lower: 下轨序列
        middle: 中轨序列
        
    Returns:
        带宽序列
    """
    return (upper - lower) / middle


def percent_b(prices: pd.Series, upper: pd.Series, 
              lower: pd.Series) -> pd.Series:
    """
    计算 %B 指标
    
    %B = (收盘价 - 下轨) / (上轨 - 下轨)
    
    %B > 1: 价格突破上轨，超买
    %B < 0: 价格突破下轨，超卖
    %B = 0.5: 价格在中轨
    
    Args:
        prices: 价格序列
        upper: 上轨序列
        lower: 下轨序列
        
    Returns:
        %B序列
    """
    band_width = upper - lower
    return (prices - lower) / band_width


def bollinger_signal(prices: pd.Series,
                     upper: pd.Series,
                     middle: pd.Series, 
                     lower: pd.Series,
                     touch_threshold: float = 0.01) -> pd.Series:
    """
    生成布林带信号
    
    买入信号:
    - 价格触及或突破下轨后反弹
    - 带宽收窄后向上突破中轨
    
    卖出信号:
    - 价格触及或突破上轨后回落
    - 带宽收窄后向下突破中轨
    
    Args:
        prices: 价格序列
        upper: 上轨序列
        middle: 中轨序列
        lower: 下轨序列
        touch_threshold: 触及阈值 (价格距离轨道的百分比)
        
    Returns:
        信号序列 (1: 买入, -1: 卖出, 0: 无信号)
    """
    signals = pd.Series(0, index=prices.index)
    
    # 计算带宽和%B
    pct_b = percent_b(prices, upper, lower)
    band_width = bandwidth(upper, lower, middle)
    
    # 带宽趋势 (收窄/扩张)
    band_width_ma = band_width.rolling(5).mean()
    band_squeezing = band_width < band_width_ma
    
    # 买入信号
    # 1. %B从超卖区反弹 (从<0.1上升到>0.2)
    prev_pct_b = pct_b.shift(1)
    buy_condition1 = (prev_pct_b < 0.1) & (pct_b > 0.2) & (prices > prices.shift(1))
    
    # 2. 带宽收窄后向上突破中轨
    buy_condition2 = band_squeezing.shift(1) & (prices > middle) & (prices.shift(1) < middle)
    
    signals[buy_condition1 | buy_condition2] = 1
    
    # 卖出信号
    # 1. %B从超买区回落 (从>0.9下降到<0.8)
    sell_condition1 = (prev_pct_b > 0.9) & (pct_b < 0.8) & (prices < prices.shift(1))
    
    # 2. 带宽收窄后向下突破中轨
    sell_condition2 = band_squeezing.shift(1) & (prices < middle) & (prices.shift(1) > middle)
    
    signals[sell_condition1 | sell_condition2] = -1
    
    return signals


def squeeze_breakout(prices: pd.Series, 
                     band_width: pd.Series,
                     threshold: float = 0.05) -> pd.Series:
    """
    检测布林带挤压突破
    
    当带宽收窄到历史低位后出现突破，通常预示大行情
    
    Args:
        prices: 价格序列
        band_width: 带宽序列
        threshold: 挤压阈值 (带宽历史百分位)
        
    Returns:
        突破信号序列 (1: 向上突破, -1: 向下突破, 0: 无突破)
    """
    signals = pd.Series(0, index=prices.index)
    
    # 计算带宽的历史百分位
    bandwidth_percentile = band_width.rolling(120).apply(
        lambda x: np.percentile(x, threshold * 100), raw=True
    )
    
    # 检测挤压状态
    is_squeezed = band_width < bandwidth_percentile
    
    # 检测突破 (挤压后)
    price_change = prices.pct_change(3)  # 3日价格变化
    
    # 向上突破: 挤压后价格上涨
    breakout_up = is_squeezed.shift(1) & (price_change > 0.02)
    signals[breakout_up] = 1
    
    # 向下突破: 挤压后价格下跌
    breakout_down = is_squeezed.shift(1) & (price_change < -0.02)
    signals[breakout_down] = -1
    
    return signals
