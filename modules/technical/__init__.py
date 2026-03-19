"""
技术指标库 - 提供常用的技术分析指标计算
"""

from .moving_average import (
    sma, ema, wma, hull_ma, 
    calc_ma_signal, golden_cross, death_cross
)
from .macd import macd, macd_signal, macd_histogram
from .rsi import rsi, rsi_signal, stoch_rsi
from .kdj import kdj, kdj_signal
from .bollinger import bollinger_bands, bollinger_signal, bandwidth, percent_b
from .pattern import (
    detect_support_resistance, find_chart_patterns,
    is_hammer, is_shooting_star, is_engulfing, is_doji,
    pattern_signals
)
from .fractal import (
    FractalIndicator, calculate_fractal,
    fractal_top_signal, fractal_bottom_signal
)

__all__ = [
    # 移动平均线
    'sma', 'ema', 'wma', 'hull_ma',
    'calc_ma_signal', 'golden_cross', 'death_cross',
    # MACD
    'macd', 'macd_signal', 'macd_histogram',
    # RSI
    'rsi', 'rsi_signal', 'stoch_rsi',
    # KDJ
    'kdj', 'kdj_signal',
    # 布林带
    'bollinger_bands', 'bollinger_signal', 'bandwidth', 'percent_b',
    # 形态识别
    'detect_support_resistance', 'find_chart_patterns',
    'is_hammer', 'is_shooting_star', 'is_engulfing', 'is_doji',
    'pattern_signals',
    # 分型指标
    'FractalIndicator', 'calculate_fractal',
    'fractal_top_signal', 'fractal_bottom_signal',
]
