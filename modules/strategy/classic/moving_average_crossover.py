"""
双均线策略 (Moving Average Crossover Strategy)

策略原理:
- 短期均线上穿长期均线时产生买入信号(金叉)
- 短期均线下穿长期均线时产生卖出信号(死叉)

参数:
- short_period: 短期均线周期 (默认20)
- long_period: 长期均线周期 (默认50)
- ma_type: 均线类型 (sma/ema/wma, 默认sma)
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class MovingAverageCrossStrategy(Strategy):
    """双均线交叉策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.short_period = config.get_param('short_period', 20)
        self.long_period = config.get_param('long_period', 50)
        self.ma_type = config.get_param('ma_type', 'sma')
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_ma(self, prices: pd.Series) -> tuple:
        """计算短期和长期均线"""
        if self.ma_type == 'ema':
            short_ma = prices.ewm(span=self.short_period, adjust=False).mean()
            long_ma = prices.ewm(span=self.long_period, adjust=False).mean()
        elif self.ma_type == 'wma':
            weights_short = np.arange(1, self.short_period + 1)
            weights_long = np.arange(1, self.long_period + 1)
            short_ma = prices.rolling(self.short_period).apply(
                lambda x: np.dot(x, weights_short) / weights_short.sum(), raw=True
            )
            long_ma = prices.rolling(self.long_period).apply(
                lambda x: np.dot(x, weights_long) / weights_long.sum(), raw=True
            )
        else:  # sma
            short_ma = prices.rolling(window=self.short_period, min_periods=1).mean()
            long_ma = prices.rolling(window=self.long_period, min_periods=1).mean()
        
        return short_ma, long_ma
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        short_ma, long_ma = self._calculate_ma(prices)
        
        signals = []
        symbol = self.config.symbol
        
        # 计算均线差值
        diff = short_ma - long_ma
        diff_prev = diff.shift(1)
        
        for i in range(1, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            
            # 金叉: 短期均线上穿长期均线
            if diff_prev.iloc[i-1] <= 0 and diff.iloc[i] > 0:
                signal = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=1.0,
                    timestamp=timestamp,
                    short_ma=short_ma.iloc[i],
                    long_ma=long_ma.iloc[i]
                )
                signals.append(signal)
                
            # 死叉: 短期均线下穿长期均线
            elif diff_prev.iloc[i-1] >= 0 and diff.iloc[i] < 0:
                signal = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=1.0,
                    timestamp=timestamp,
                    short_ma=short_ma.iloc[i],
                    long_ma=long_ma.iloc[i]
                )
                signals.append(signal)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


# 兼容旧名称
MovingAverageCrossoverStrategy = MovingAverageCrossStrategy