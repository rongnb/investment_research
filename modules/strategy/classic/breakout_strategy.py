"""
突破策略 (Breakout Strategy)

策略原理:
- 价格突破前期高点/低点时产生交易信号
- 分为日内突破和区间突破

买入信号:
- 价格突破N日高点
- 价格突破震荡区间上沿

卖出信号:
- 价格跌破N日低点
- 价格跌破震荡区间下沿

参数:
- lookback_period: 回溯周期 (默认20)
- use_closing: 是否使用收盘价突破 (默认True)
- atr_multiplier: ATR倍数用于止损 (默认2)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class BreakoutStrategy(Strategy):
    """突破策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = config.get_param('lookback_period', 20)
        self.use_closing = config.get_param('use_closing', True)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR (Average True Range)"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        high = data['high']
        low = data['low']
        
        signals = []
        symbol = self.config.symbol
        
        # 计算历史高低点
        highest = high.rolling(window=self.lookback_period).max()
        lowest = low.rolling(window=self.lookback_period).min()
        
        # 使用收盘价或最高/最低价
        if self.use_closing:
            trigger_price = prices
        else:
            trigger_price = high
        
        for i in range(self.lookback_period, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            current_high = high.iloc[i]
            current_low = low.iloc[i]
            
            prev_price = prices.iloc[i-1]
            prev_highest = highest.iloc[i-1]
            prev_lowest = lowest.iloc[i-1]
            
            # 买入信号: 突破N日高点
            if self.use_closing:
                if prev_price <= prev_highest and price > highest.iloc[i]:
                    # 计算信号强度
                    breakout_strength = (price - highest.iloc[i]) / highest.iloc[i]
                    strength = min(1.0, 0.5 + breakout_strength * 10)
                    
                    signal_obj = create_signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        price=price,
                        strength=strength,
                        timestamp=timestamp,
                        breakout_level=highest.iloc[i],
                        atr=self._calculate_atr(data).iloc[i] if i >= 13 else None
                    )
                    signals.append(signal_obj)
            else:
                # 使用日内突破
                if current_high > highest.iloc[i]:
                    breakout_strength = (current_high - highest.iloc[i]) / highest.iloc[i]
                    strength = min(1.0, 0.5 + breakout_strength * 10)
                    
                    signal_obj = create_signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        price=price,
                        strength=strength,
                        timestamp=timestamp,
                        breakout_level=highest.iloc[i]
                    )
                    signals.append(signal_obj)
            
            # 卖出信号: 跌破N日低点
            if self.use_closing:
                if prev_price >= prev_lowest and price < lowest.iloc[i]:
                    breakout_strength = (lowest.iloc[i] - price) / lowest.iloc[i]
                    strength = min(1.0, 0.5 + breakout_strength * 10)
                    
                    signal_obj = create_signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        price=price,
                        strength=strength,
                        timestamp=timestamp,
                        breakout_level=lowest.iloc[i]
                    )
                    signals.append(signal_obj)
            else:
                if current_low < lowest.iloc[i]:
                    breakout_strength = (lowest.iloc[i] - current_low) / lowest.iloc[i]
                    strength = min(1.0, 0.5 + breakout_strength * 10)
                    
                    signal_obj = create_signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        price=price,
                        strength=strength,
                        timestamp=timestamp,
                        breakout_level=lowest.iloc[i]
                    )
                    signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class VolatilityBreakoutStrategy(BreakoutStrategy):
    """波动率突破策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.atr_period = config.get_param('atr_period', 14)
        self.breakout_multiplier = config.get_param('breakout_multiplier', 1.5)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        high = data['high']
        low = data['low']
        
        signals = []
        symbol = self.config.symbol
        
        # 计算ATR
        atr = self._calculate_atr(data, self.atr_period)
        
        # 计算枢轴点
        pivot = (high + low + prices) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        
        for i in range(self.atr_period, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            
            # 突破ATR通道
            upper_channel = prices.iloc[i-1] + self.breakout_multiplier * atr.iloc[i-1]
            lower_channel = prices.iloc[i-1] - self.breakout_multiplier * atr.iloc[i-1]
            
            if price > upper_channel:
                strength = min(1.0, (price - upper_channel) / atr.iloc[i])
                
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    atr=atr.iloc[i]
                )
                signals.append(signal_obj)
                
            elif price < lower_channel:
                strength = min(1.0, (lower_channel - price) / atr.iloc[i])
                
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    atr=atr.iloc[i]
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals