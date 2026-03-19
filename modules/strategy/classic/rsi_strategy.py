"""
RSI策略 (RSI Strategy)

策略原理:
- RSI (相对强弱指标) 衡量价格变动的速度和幅度
- RSI > 70 表示超买,可能产生卖出信号
- RSI < 30 表示超卖,可能产生买入信号

买入信号:
- RSI从超卖区域(30以下)回升
- RSI上穿30

卖出信号:
- RSI从超买区域(70以上)回落
- RSI下穿70

参数:
- period: RSI计算周期 (默认14)
- overbought: 超买阈值 (默认70)
- oversold: 超卖阈值 (默认30)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class RSIStrategy(Strategy):
    """RSI策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = config.get_param('period', 14)
        self.overbought = config.get_param('overbought', 70)
        self.oversold = config.get_param('oversold', 30)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI指标"""
        # 计算价格变动
        delta = prices.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # 计算平均涨跌 (使用EMA)
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        rsi = self._calculate_rsi(prices)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(1, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            rsi_val = rsi.iloc[i]
            rsi_prev = rsi.iloc[i-1]
            
            # 计算信号强度 (基于RSI距离极值的距离)
            if rsi_val >= self.overbought:
                strength = min(1.0, (rsi_val - self.overbought) / (100 - self.overbought) + 0.3)
            elif rsi_val <= self.oversold:
                strength = min(1.0, (self.oversold - rsi_val) / self.oversold + 0.3)
            else:
                strength = 0.5
            
            # 买入信号: RSI从超卖区域回升或上穿30
            if rsi_prev <= self.oversold and rsi_val > self.oversold:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    rsi=rsi_val
                )
                signals.append(signal_obj)
                
            # 卖出信号: RSI从超买区域回落或下穿70
            elif rsi_prev >= self.overbought and rsi_val < self.overbought:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    rsi=rsi_val
                )
                signals.append(signal_obj)
            
            # 趋势确认: RSI在中间区域但穿越中线
            elif rsi_prev < 50 and rsi_val >= 50:
                # 短期多头确认
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=0.6,
                    timestamp=timestamp,
                    rsi=rsi_val
                )
                signals.append(signal_obj)
                
            elif rsi_prev > 50 and rsi_val <= 50:
                # 短期空头确认
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=0.6,
                    timestamp=timestamp,
                    rsi=rsi_val
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals