"""
RSI指标模块
提供RSI、随机RSI等计算和信号生成
"""

import pandas as pd
import numpy as np
from typing import Tuple


def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    计算RSI (Relative Strength Index)
    
    RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅
    
    Args:
        prices: 价格序列
        period: 计算周期，默认14
        
    Returns:
        RSI序列 (0-100)
    """
    # 计算价格变化
    delta = prices.diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 计算平均涨幅和平均跌幅 (使用指数移动平均)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    # 计算RS和RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def rsi_signal(rsi_values: pd.Series, 
               oversold: float = 30,
               overbought: float = 70) -> pd.Series:
    """
    生成RSI信号
    
    Args:
        rsi_values: RSI值序列
        oversold: 超卖阈值 (默认30)
        overbought: 超买阈值 (默认70)
        
    Returns:
        信号序列 (1: 买入, -1: 卖出, 0: 无信号)
    """
    signals = pd.Series(0, index=rsi_values.index)
    
    # 从超卖区向上突破 → 买入信号
    prev_rsi = rsi_values.shift(1)
    buy_condition = (prev_rsi < oversold) & (rsi_values >= oversold)
    signals[buy_condition] = 1
    
    # 从超买区向下突破 → 卖出信号
    sell_condition = (prev_rsi > overbought) & (rsi_values <= overbought)
    signals[sell_condition] = -1
    
    return signals


def rsi_divergence(prices: pd.Series, rsi_values: pd.Series,
                   lookback: int = 20) -> pd.Series:
    """
    检测RSI背离
    
    顶背离: 价格创新高，RSI未创新高 → 看跌
    底背离: 价格创新低，RSI未创新低 → 看涨
    
    Args:
        prices: 价格序列
        rsi_values: RSI值序列
        lookback: 回看周期
        
    Returns:
        背离信号序列 (1: 底背离, -1: 顶背离, 0: 无背离)
    """
    signals = pd.Series(0, index=prices.index)
    
    for i in range(lookback, len(prices)):
        # 当前窗口
        price_window = prices.iloc[i-lookback:i]
        rsi_window = rsi_values.iloc[i-lookback:i]
        
        curr_price = prices.iloc[i]
        curr_rsi = rsi_values.iloc[i]
        
        # 窗口极值
        price_high = price_window.max()
        price_low = price_window.min()
        rsi_high = rsi_window.max()
        rsi_low = rsi_window.min()
        
        # 顶背离
        if curr_price > price_high * 0.99 and curr_r