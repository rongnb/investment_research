"""
均值回归策略 (Mean Reversion Strategy)

策略原理:
- 价格偏离均值后有回归均值的倾向
- 使用Z-Score衡量偏离程度
- 价格回归均值时平仓获利

买入信号:
- 价格低于均值超过2个标准差 (Z-Score < -2)
- 价格开始回升

卖出信号:
- 价格高于均值超过2个标准差 (Z-Score > 2)
- 价格开始回落
- 价格回归均值

参数:
- period: 均值计算周期 (默认20)
- std_threshold: 标准差阈值 (默认2)
- exit_threshold: 退出阈值 (默认0.5)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class MeanReversionStrategy(Strategy):
    """均值回归策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = config.get_param('period', 20)
        self.std_threshold = config.get_param('std_threshold', 2)
        self.exit_threshold = config.get_param('exit_threshold', 0.5)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._position = Position.NEUTRAL
    
    def _calculate_zscore(self, prices: pd.Series) -> pd.Series:
        """计算Z-Score"""
        ma = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        
        zscore = (prices - ma) / std
        return zscore
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        zscore = self._calculate_zscore(prices)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(self.period, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            z = zscore.iloc[i]
            z_prev = zscore.iloc[i-1]
            
            # 计算信号强度
            if abs(z) > self.std_threshold:
                strength = min(1.0, abs(z) / (self.std_threshold * 1.5))
            else:
                strength = 0.5
            
            # 买入信号: 价格超卖后开始回升
            if z_prev < -self.std_threshold and z > z_prev:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    zscore=z,
                    position=self._position
                )
                signals.append(signal_obj)
                self._position = Position.LONG
                
            # 卖出信号: 价格超买后开始回落
            elif z_prev > self.std_threshold and z < z_prev:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    zscore=z,
                    position=self._position
                )
                signals.append(signal_obj)
                self._position = Position.SHORT
            
            # 强制平仓信号: 回归均值
            elif self._position == Position.LONG and abs(z) < self.exit_threshold:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    price=price,
                    strength=0.8,
                    timestamp=timestamp,
                    zscore=z
                )
                signals.append(signal_obj)
                self._position = Position.NEUTRAL
                
            elif self._position == Position.SHORT and abs(z) < self.exit_threshold:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_SHORT,
                    price=price,
                    strength=0.8,
                    timestamp=timestamp,
                    zscore=z
                )
                signals.append(signal_obj)
                self._position = Position.NEUTRAL
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class PairsTradingStrategy(Strategy):
    """配对交易策略 (均值回归的特例)"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = config.get_param('period', 20)
        self.entry_threshold = config.get_param('entry_threshold', 2)
        self.exit_threshold = config.get_param('exit_threshold', 0.5)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # 配对交易需要两只股票的数据
        # 这里简化处理，假设data包含spread列
        if 'spread' not in data.columns:
            return []
        
        spread = data['spread']
        zscore = self._calculate_zscore(spread)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(self.period, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            z = zscore.iloc[i]
            z_prev = zscore.iloc[i-1]
            
            # 买入信号: 价差被低估 (z-score < -threshold)
            if z_prev < -self.entry_threshold and z > z_prev:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=spread.iloc[i],
                    strength=min(1.0, abs(z) / (self.entry_threshold * 1.5)),
                    timestamp=timestamp,
                    zscore=z
                )
                signals.append(signal_obj)
                
            # 卖出信号: 价差被高估 (z-score > threshold)
            elif z_prev > self.entry_threshold and z < z_prev:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=spread.iloc[i],
                    strength=min(1.0, abs(z) / (self.entry_threshold * 1.5)),
                    timestamp=timestamp,
                    zscore=z
                )
                signals.append(signal_obj)
            
            # 平仓信号: 回归均值
            elif abs(z) < self.exit_threshold:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.HOLD,
                    price=spread.iloc[i],
                    strength=0.8,
                    timestamp=timestamp,
                    zscore=z
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals
    
    def _calculate_zscore(self, spread: pd.Series) -> pd.Series:
        ma = spread.rolling(window=self.period).mean()
        std = spread.rolling(window=self.period).std()
        return (spread - ma) / std