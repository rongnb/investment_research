"""
MACD指标模块
提供MACD指标计算和信号生成
"""

import pandas as pd
import numpy as np
from .moving_average import ema


def macd(prices: pd.Series, 
         fast_period: int = 12, 
         slow_period: int = 26) -> pd.Series:
    """
    计算MACD线 (DIF)
    
    DIF = EMA(close, 12) - EMA(close, 26)
    
    Args:
        prices: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        
    Returns:
        MACD线 (DIF)
    """
    ema_fast = ema(prices, fast_period)
    ema_slow = ema(prices, slow_period)
    
    return ema_fast - ema_slow


def macd_signal(macd_line: pd.Series, signal_period: int = 9) -> pd.Series:
    """
    计算MACD信号线 (DEA)
    
    DEA = EMA(DIF, 9)
    
    Args:
        macd_line: MACD线 (DIF)
        signal_period: 信号线周期
        
    Returns:
        信号线 (DEA)
    """
    return ema(macd_line, signal_period)


def macd_histogram(macd_line: pd.Series, signal_line: pd.Series) -> pd.Series:
    """
    计算MACD柱状图 (MACD柱)
    
    MACD柱 = DIF - DEA
    
    Args:
        macd_line: MACD线 (DIF)
        signal_line: 信号线 (DEA)
        
    Returns:
        MACD柱状图
    """
    return macd_line - signal_line


def calc_macd(prices: pd.Series,
              fast_period: int = 12,
              slow_period: int = 26,
              signal_period: int = 9) -> pd.DataFrame:
    """
    计算完整MACD指标
    
    Args:
        prices: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        DataFrame包含MACD线、信号线、柱状图
    """
    macd_line = macd(prices, fast_period, slow_period)
    signal_line = macd_signal(macd_line, signal_period)
    histogram = macd_histogram(macd_line, signal_line)
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })


def macd_golden_cross(macd_line: pd.Series, signal_line: pd.Series) -> pd.Series:
    """
    检测MACD金叉信号 (DIF上穿DEA)
    
    Args:
        macd_line: MACD线 (DIF)
        signal_line: 信号线 (DEA)
        
    Returns:
        金叉信号序列 (True表示金叉)
    """
    prev_macd = macd_line.shift(1)
    prev_signal = signal_line.shift(1)
    
    # 昨天DIF<DEA，今天DIF>DEA
    golden = (prev_macd < prev_signal) & (macd_line > signal_line)
    return golden


def macd_death_cross(macd_line: pd.Series, signal_line: pd.Series) -> pd.Series:
    """
    检测MACD死叉信号 (DIF下穿DEA)
    
    Args:
        macd_line: MACD线 (DIF)
        signal_line: 信号线 (DEA)
        
    Returns:
        死叉信号序列 (True表示死叉)
    """
    prev_macd = macd_line.shift(1)
    prev_signal = signal_line.shift(1)
    
    # 昨天DIF>DEA，今天DIF<DEA
    death = (prev_macd > prev_signal) & (macd_line < signal_line)
    return death


def macd_divergence(prices: pd.Series, macd_line: pd.Series, 
                    lookback: int = 20) -> pd.Series:
    """
    检测MACD背离
    
    顶背离: 价格新高，MACD未新高 → 看跌
    底背离: 价格新低，MACD未新低 → 看涨
    
    Args:
        prices: 价格序列
        macd_line: MACD线
        lookback: 回看周期
        
    Returns:
        背离信号序列 (1: 底背离, -1: 顶背离, 0: 无背离)
    """
    signals = pd.Series(0, index=prices.index)
    
    for i in range(lookback, len(prices)):
        # 当前窗口
        price_window = prices.iloc[i-lookback:i]
        macd_window = macd_line.iloc[i-lookback:i]
        
        # 当前价格极值
        curr_price = prices.iloc[i]
        curr_macd = macd_line.iloc[i]
        
        # 窗口极值
        price_high = price_window.max()
        price_low = price_window.min()
        macd_high = macd_window.max()
        macd_low = macd_window.min()
        
        # 顶背离: 价格新高，MACD未新高
        if curr_price > price_high * 0.98 and curr_macd < macd_high * 0.95:
            signals.iloc[i] = -1
        
        # 底背离: 价格新低，MACD未新低
        elif curr_price < price_low * 1.02 and curr_macd > macd_low * 1.05:
            signals.iloc[i] = 1
    
    return signals


def macd_strength(macd_line: pd.Series, signal_line: pd.Series, 
                prices: pd.Series) -> pd.Series:
    """
    计算MACD强度
    
    综合考虑:
    1. DIF与DEA的距离
    2. MACD柱状图的高度
    3. 价格动量
    
    Args:
        macd_line: MACD线
        signal_line: 信号线
        prices: 价格序列
        
    Returns:
        强度值 (-1到1)
    """
    # DIF与DEA的距离
    diff = macd_line - signal_line
    diff_normalized = diff / diff.rolling(20).std().abs()
    
    # 价格动量
    momentum = prices.pct_change(10)
    
    # 综合强度
    strength = diff_normalized * 0.6 + momentum * 0.4
    
    # 限制在-1到1之间
    strength = strength.clip(-1, 1)
    
    return strength
