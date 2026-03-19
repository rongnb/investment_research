"""
KDJ指标模块
提供KDJ指标计算和信号生成
"""

import pandas as pd
import numpy as np


def calculate_rsv(prices: pd.Series, 
                   highs: pd.Series, 
                   lows: pd.Series,
                   period: int = 9) -> pd.Series:
    """
    计算未成熟随机值 (RSV)
    
    RSV = (收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) × 100
    
    Args:
        prices: 收盘价序列
        highs: 最高价序列
        lows: 最低价序列
        period: 计算周期
        
    Returns:
        RSV序列
    """
    lowest_low = lows.rolling(window=period, min_periods=1).min()
    highest_high = highs.rolling(window=period, min_periods=1).max()
    
    # 避免除以0
    range_hl = highest_high - lowest_low
    range_hl = range_hl.replace(0, np.nan)
    
    rsv = (prices - lowest_low) / range_hl * 100
    
    return rsv.fillna(50)  # 空值填充50


def kdj(prices: pd.Series,
        highs: pd.Series,
        lows: pd.Series,
        n: int = 9,
        m1: int = 3,
        m2: int = 3) -> pd.DataFrame:
    """
    计算KDJ指标
    
    K值 = 2/3 × 前一日K值 + 1/3 × 当日RSV
    D值 = 2/3 × 前一日D值 + 1/3 × 当日K值
    J值 = 3 × K值 - 2 × D值 = K值 + 2 × (K值 - D值)
    
    Args:
        prices: 收盘价序列
        highs: 最高价序列
        lows: 最低价序列
        n: RSV计算周期
        m1: K值平滑系数
        m2: D值平滑系数
        
    Returns:
        DataFrame包含K、D、J值
    """
    # 计算RSV
    rsv = calculate_rsv(prices, highs, lows, n)
    
    # 计算K值
    k = pd.Series(index=prices.index, dtype=float)
    k.iloc[0] = 50  # 初始值
    
    alpha_k = 1 / m1
    for i in range(1, len(prices)):
        k.iloc[i] = (1 - alpha_k) * k.iloc[i-1] + alpha_k * rsv.iloc[i]
    
    # 计算D值
    d = pd.Series(index=prices.index, dtype=float)
    d.iloc[0] = 50  # 初始值
    
    alpha_d = 1 / m2
    for i in range(1, len(prices)):
        d.iloc[i] = (1 - alpha_d) * d.iloc[i-1] + alpha_d * k.iloc[i]
    
    # 计算J值
    j = 3 * k - 2 * d
    
    return pd.DataFrame({
        'K': k,
        'D': d,
        'J': j
    })


def kdj_signal(kdj_df: pd.DataFrame,
               overbought_k: float = 80,
               oversold_k: float = 20,
               overbought_d: float = 80,
               oversold_d: float = 20) -> pd.Series:
    """
    生成KDJ交易信号
    
    买入信号:
    - K线从超卖区(20以下)向上突破D线 (金叉)
    - J值从负值转为正值
    
    卖出信号:
    - K线从超买区(80以上)向下跌破D线 (死叉)
    - J值从高位(>100)快速回落
    
    Args:
        kdj_df: KDJ指标DataFrame
        overbought_k: K值超买阈值
        oversold_k: K值超卖阈值
        overbought_d: D值超买阈值
        oversold_d: D值超卖阈值
        
    Returns:
        信号序列 (1: 买入, -1: 卖出, 0: 无信号)
    """
    k = kdj_df['K']
    d = kdj_df['D']
    j = kdj_df['J']
    
    signals = pd.Series(0, index=kdj_df.index)
    
    # 前值
    prev_k = k.shift(1)
    prev_d = d.shift(1)
    prev_j = j.shift(1)
    
    # 金叉: K上穿D，且至少一个在超卖区
    golden_cross = (prev_k < prev_d) & (k > d) & ((k < oversold_k) | (d < oversold_d))
    signals[golden_cross] = 1
    
    # 死叉: K下穿D，且至少一个在超买区
    death_cross = (prev_k > prev_d) & (k < d) & ((k > overbought_k) | (d > overbought_d))
    signals[death_cross] = -1
    
    # J值极值反转信号
    # J从极高值(>100)快速回落 → 卖出
    j_sell = (prev_j > 100) & (j < prev_j * 0.9) & (j > 80)
    signals[j_sell] = -1
    
    # J从负值转正 → 买入
    j_buy = (prev_j < 0) & (j > 0) & (j < 30)
    signals[j_buy] = 1
    
    return signals


def kdj_strength(kdj_df: pd.DataFrame) -> pd.Series:
    """
    计算KDJ强度
    
    综合考虑K、D、J值的位置和趋势
    
    Args:
        kdj_df: KDJ指标DataFrame
        
    Returns:
        强度值 (-1到1)
    """
    k = kdj_df['K']
    d = kdj_df['D']
    j = kdj_df['J']
    
    # K值位置 (0-100 → -1到1)
    k_position = (k - 50) / 50
    
    # K与D的差值 (金叉正值，死叉负值)
    kd_diff = (k - d) / 10
    kd_diff = kd_diff.clip(-1, 1)
    
    # J值极值程度
    j_extreme = pd.Series(0, index=j.index)
    j_extreme[j > 100] = (j[j > 100] - 100) / 50  # 正值表示超买
    j_extreme[j < 0] = j[j < 0] / 50  # 负值表示超卖
    j_extreme = j_extreme.clip(-1, 1)
    
    # 综合强度
    strength = k_position * 0.3 + kd_diff * 0.4 + j_extreme * 0.3
    
    return strength.clip(-1, 1)
