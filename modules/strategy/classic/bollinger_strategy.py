"""
布林带策略 (Bollinger Bands Strategy)

策略原理:
- 中轨 = N日简单移动平均线
- 上轨 = 中轨 + K倍标准差
- 下轨 = 中轨 - K倍标准差

买入信号:
- 价格触及或突破下轨 (超卖)
- 价格从上轨回落
- 布林带收窄后突破

卖出信号:
- 价格触及或突破上轨 (超买)
- 价格从下轨回升
- 布林带开口收缩

参数:
- period: 均线周期 (默认20)
- std_dev: 标准差倍数 (默认2)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class BollingerBandsStrategy(Strategy):
    """布林带策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = config.get_param('period', 20)
        self.std_dev = config.get_param('std_dev', 2)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_bands(self, prices: pd.Series) -> pd.DataFrame:
        """计算布林带"""
        # 中轨
        middle = prices.rolling(window=self.period).mean()
        
        # 标准差
        std = prices.rolling(window=self.period).std()
        
        # 上轨和下轨
        upper = middle + self.std_dev * std
        lower = middle - self.std_dev * std
        
        # 计算%B和带宽
        bandwidth = (upper - lower) / middle * 100
        percent_b = (prices - lower) / (upper - lower)
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }, index=prices.index)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        high = data['high']
        low = data['low']
        bands = self._calculate_bands(prices)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(1, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            high_price = high.iloc[i]
            low_price = low.iloc[i]
            
            upper = bands['upper'].iloc[i]
            lower = bands['lower'].iloc[i]
            middle = bands['middle'].iloc[i]
            percent_b = bands['percent_b'].iloc[i]
            bandwidth = bands['bandwidth'].iloc[i]
            bandwidth_prev = bands['bandwidth'].iloc[i-1] if i > 0 else 0
            
            # 计算信号强度
            if percent_b < 0:
                strength = 1.0  # 突破下轨
            elif percent_b > 1:
                strength = 1.0  # 突破上轨
            elif percent_b < 0.2:
                strength = 0.8  # 接近下轨
            elif percent_b > 0.8:
                strength = 0.8  # 接近上轨
            else:
                strength = 0.5
            
            # 买入信号: 价格触及或突破下轨
            if low_price <= lower and price > lower:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    percent_b=percent_b,
                    bandwidth=bandwidth
                )
                signals.append(signal_obj)
            
            # 卖出信号: 价格触及或突破上轨
            elif high_price >= upper and price < upper:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    percent_b=percent_b,
                    bandwidth=bandwidth
                )
                signals.append(signal_obj)
            
            # 突破信号: 布林带收窄后向上突破
            elif bandwidth_prev < bandwidth and percent_b > 0.8:
                # 窄带突破向上
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=0.7,
                    timestamp=timestamp,
                    percent_b=percent_b
                )
                signals.append(signal_obj)
            
            # 突破信号: 布林带收窄后向下突破
            elif bandwidth_prev < bandwidth and percent_b < 0.2:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=0.7,
                    timestamp=timestamp,
                    percent_b=percent_b
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals