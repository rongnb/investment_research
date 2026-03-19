"""
分型指标 (Fractal Indicator)
Bill Williams 分形理论实现

分型用于识别价格走势中的潜在反转点：
- 顶分型 (Bearish Fractal): 中间K线最高价高于两侧各两根K线
- 底分型 (Bullish Fractal): 中间K线最低价低于两侧各两根K线
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


class FractalIndicator:
    """
    分型指标计算器
    
    参数:
    - period: 分型周期（默认5，即中间1根+左右各2根）
    """
    
    def __init__(self, period: int = 5):
        if period < 3 or period % 2 == 0:
            raise ValueError("period必须是大于等于3的奇数")
        self.period = period
        self.offset = period // 2  # 左右偏移量
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算分型指标
        
        输入DataFrame需包含: high, low, close, open
        输出新增列:
        - fractal_top: 顶分型位置 (值为该K线最高价)
        - fractal_bottom: 底分型位置 (值为该K线最低价)
        - fractal_type: 分型类型 (1=顶分型, -1=底分型, 0=无)
        """
        result = df.copy()
        
        # 初始化分型列
        result['fractal_top'] = np.nan
        result['fractal_bottom'] = np.nan
        result['fractal_type'] = 0
        
        # 计算顶分型 (中间K线最高价比左右各offset根K线都高)
        for i in range(self.offset, len(result) - self.offset):
            current_high = result['high'].iloc[i]
            
            # 检查是否为顶分型
            is_top = True
            for j in range(1, self.offset + 1):
                if current_high <= result['high'].iloc[i - j] or \
                   current_high <= result['high'].iloc[i + j]:
                    is_top = False
                    break
            
            if is_top:
                result.loc[result.index[i], 'fractal_top'] = current_high
                result.loc[result.index[i], 'fractal_type'] = 1
        
        # 计算底分型 (中间K线最低价比左右各offset根K线都低)
        for i in range(self.offset, len(result) - self.offset):
            current_low = result['low'].iloc[i]
            
            # 检查是否为底分型
            is_bottom = True
            for j in range(1, self.offset + 1):
                if current_low >= result['low'].iloc[i - j] or \
                   current_low >= result['low'].iloc[i + j]:
                    is_bottom = False
                    break
            
            if is_bottom:
                result.loc[result.index[i], 'fractal_bottom'] = current_low
                result.loc[result.index[i], 'fractal_type'] = -1
        
        return result
    
    def get_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        获取分型交易信号
        
        返回信号DataFrame:
        - date: 日期
        - type: 信号类型 (top/bottom)
        - price: 价格
        - description: 描述
        """
        result = self.calculate(df)
        
        signals = []
        
        # 顶分型信号
        top_fractals = result[result['fractal_type'] == 1].copy()
        for idx, row in top_fractals.iterrows():
            signals.append({
                'date': idx,
                'type': 'top',
                'price': row['fractal_top'],
                'description': f"顶分型出现，最高价: {row['fractal_top']:.2f}"
            })
        
        # 底分型信号
        bottom_fractals = result[result['fractal_type'] == -1].copy()
        for idx, row in bottom_fractals.iterrows():
            signals.append({
                'date': idx,
                'type': 'bottom',
                'price': row['fractal_bottom'],
                'description': f"底分型出现，最低价: {row['fractal_bottom']:.2f}"
            })
        
        return pd.DataFrame(signals).sort_values('date').reset_index(drop=True)


def calculate_fractal(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """
    分型指标计算便捷函数
    
    参数:
    - df: DataFrame (需包含high, low, close, open)
    - period: 分型周期 (默认5)
    
    返回:
    - DataFrame: 包含分型指标的原始数据
    """
    indicator = FractalIndicator(period=period)
    return indicator.calculate(df)


def fractal_top_signal(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    顶分型信号便捷函数
    
    参数:
    - df: DataFrame (需包含high, low)
    - period: 分型周期 (默认5)
    
    返回:
    - Series: 顶分型位置 (True表示顶分型)
    """
    result = calculate_fractal(df, period)
    return result['fractal_type'] == 1


def fractal_bottom_signal(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    底分型信号便捷函数
    
    参数:
    - df: DataFrame (需包含high, low)
    - period: 分型周期 (默认5)
    
    返回:
    - Series: 底分型位置 (True表示底分型)
    """
    result = calculate_fractal(df, period)
    return result['fractal_type'] == -1


# 添加__all__以明确导出内容
__all__ = [
    'FractalIndicator',
    'calculate_fractal',
    'fractal_top_signal',
    'fractal_bottom_signal',
]