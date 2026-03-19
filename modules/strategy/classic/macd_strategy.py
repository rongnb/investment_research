"""
MACD策略 (MACD Strategy)

策略原理:
- MACD线 = 12日EMA - 26日EMA
- 信号线 = MACD的9日EMA
- MACD柱 = MACD - 信号线

买入信号:
- MACD线从下向上穿越信号线(金叉)
- MACD柱由负转正

卖出信号:
- MACD线从上向下穿越信号线(死叉)
- MACD柱由正转负

参数:
- fast_period: 快速EMA周期 (默认12)
- slow_period: 慢速EMA周期 (默认26)
- signal_period: 信号线周期 (默认9)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class MACDStrategy(Strategy):
    """MACD策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.fast_period = config.get_param('fast_period', 12)
        self.slow_period = config.get_param('slow_period', 26)
        self.signal_period = config.get_param('signal_period', 9)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_macd(self, prices: pd.Series) -> pd.DataFrame:
        """计算MACD指标"""
        # 计算快速和慢速EMA
        ema_fast = prices.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow_period, adjust=False).mean()
        
        # MACD线
        macd_line = ema_fast - ema_slow
        
        # 信号线
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        # MACD柱
        macd_histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': macd_histogram
        }, index=prices.index)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        macd_df = self._calculate_macd(prices)
        
        signals = []
        symbol = self.config.symbol
        
        macd = macd_df['macd']
        signal = macd_df['signal']
        histogram = macd_df['histogram']
        
        # 计算当前和前一根的差值
        diff = macd - signal
        diff_prev = diff.shift(1)
        
        for i in range(1, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            
            # 计算信号强度 (基于histogram的变化)
            hist_change = histogram.iloc[i] - histogram.iloc[i-1]
            strength = min(1.0, abs(hist_change) / abs(histogram).mean() * 0.5) if histogram.mean() != 0 else 0.5
            
            # 金叉: MACD线从下向上穿越信号线
            if diff_prev.iloc[i-1] <= 0 and diff.iloc[i] > 0:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    macd=macd.iloc[i],
                    signal=signal.iloc[i],
                    histogram=histogram.iloc[i]
                )
                signals.append(signal_obj)
                
            # 死叉: MACD线从上向下穿越信号线
            elif diff_prev.iloc[i-1] >= 0 and diff.iloc[i] < 0:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    macd=macd.iloc[i],
                    signal=signal.iloc[i],
                    histogram=histogram.iloc[i]
                )
                signals.append(signal_obj)
            
            # 额外过滤: MACD柱由负转正/由正转负 (增强信号)
            elif histogram.iloc[i-1] < 0 and histogram.iloc[i] > 0 and diff.iloc[i] > 0:
                # 已经在金叉过程中，但前一根还没确认
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength * 0.8,
                    timestamp=timestamp,
                    macd=macd.iloc[i],
                    histogram=histogram.iloc[i]
                )
                # 避免重复添加
                if not signals or signals[-1].signal_type != SignalType.BUY:
                    signals.append(signal_obj)
                    
            elif histogram.iloc[i-1] > 0 and histogram.iloc[i] < 0 and diff.iloc[i] < 0:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength * 0.8,
                    timestamp=timestamp,
                    macd=macd.iloc[i],
                    histogram=histogram.iloc[i]
                )
                if not signals or signals[-1].signal_type != SignalType.SELL:
                    signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals