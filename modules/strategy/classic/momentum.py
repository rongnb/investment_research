"""
动量策略 (Momentum Strategy)

策略原理:
- 趋势延续性: 过去表现好的资产未来倾向于继续表现好
- 使用历史收益率作为动量因子

买入信号:
- 过去N个月收益率 > 0
- 动量因子排名靠前

卖出信号:
- 过去N个月收益率 < 0
- 动量因子由正转负

参数:
- lookback_period: 回溯周期 (默认60交易日)
- holding_period: 持仓周期 (默认20交易日)
- top_n: 选取前N只股票 (默认10)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from ..base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, create_signal
)


class ClassicMomentumStrategy(Strategy):
    """经典动量策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = config.get_param('lookback_period', 60)
        self.holding_period = config.get_param('holding_period', 20)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_momentum(self, prices: pd.Series) -> pd.Series:
        """计算动量指标 (收益率)"""
        momentum = prices.pct_change(periods=self.lookback_period)
        return momentum
    
    def _calculate_acceleration(self, prices: pd.Series) -> pd.Series:
        """计算动量加速度 (价格变化的二阶导数)"""
        returns = prices.pct_change()
        acceleration = returns.diff().diff()
        return acceleration
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        momentum = self._calculate_momentum(prices)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(self.lookback_period, len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            mom = momentum.iloc[i]
            mom_prev = momentum.iloc[i-1]
            
            # 计算信号强度
            strength = min(1.0, abs(mom) * 5)  # 收益率5%对应强度0.25
            
            # 买入信号: 动量由负转正
            if mom_prev < 0 and mom > 0:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    momentum=mom
                )
                signals.append(signal_obj)
                
            # 卖出信号: 动量由正转负
            elif mom_prev > 0 and mom < 0:
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    momentum=mom
                )
                signals.append(signal_obj)
            
            # 趋势确认
            elif mom > 0 and mom_prev > mom:
                # 动量减弱，可能见顶
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=0.6,
                    timestamp=timestamp,
                    momentum=mom
                )
                signals.append(signal_obj)
                
            elif mom < 0 and mom_prev < mom:
                # 动量负向减弱，可能见底
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=0.6,
                    timestamp=timestamp,
                    momentum=mom
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class MomentumRankStrategy(Strategy):
    """动量排名策略 - 多标的版本"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = config.get_param('lookback_period', 60)
        self.top_n = config.get_param('top_n', 5)
        self.rebalance_freq = config.get_param('rebalance_freq', 20)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._last_rebalance = 0
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """多标的版本"""
        signals = []
        
        # 计算每个标的的动量
        momentum_data = {}
        for symbol, df in data.items():
            if 'close' in df.columns:
                prices = df['close']
                momentum = prices.pct_change(periods=self.lookback_period).iloc[-1]
                momentum_data[symbol] = momentum
        
        if not momentum_data:
            return signals
        
        # 排序并选取前N名
        sorted_symbols = sorted(momentum_data.items(), key=lambda x: x[1], reverse=True)
        top_symbols = [s[0] for s in sorted_symbols[:self.top_n]]
        
        timestamp = datetime.now()
        
        for symbol in top_symbols:
            mom = momentum_data[symbol]
            price = data[symbol]['close'].iloc[-1] if 'close' in data[symbol].columns else None
            
            signal_obj = create_signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=price,
                strength=min(1.0, abs(mom) * 3),
                timestamp=timestamp,
                momentum=mom,
                rank=top_symbols.index(symbol) + 1
            )
            signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class DualMomentumStrategy(Strategy):
    """双动量策略 - 结合相对动量和绝对动量"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.relative_period = config.get_param('relative_period', 126)  # 6个月
        self.absolute_period = config.get_param('absolute_period', 21)   # 1个月
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        if not self.validate_data(data):
            return []
        
        prices = data['close']
        
        # 相对动量 (与市场比较)
        market_return = prices.pct_change(periods=self.relative_period)
        
        # 绝对动量 (与无风险收益比较, 这里简化为0)
        short_momentum = prices.pct_change(periods=self.absolute_period)
        
        signals = []
        symbol = self.config.symbol
        
        for i in range(max(self.relative_period, self.absolute_period), len(data)):
            timestamp = data.index[i] if hasattr(data.index[i], 'tz') else datetime.now()
            price = prices.iloc[i]
            
            rel_mom = market_return.iloc[i]
            abs_mom = short_momentum.iloc[i]
            
            # 双动量信号
            if rel_mom > 0 and abs_mom > 0:
                signal_type = SignalType.BUY
                strength = min(1.0, (rel_mom + abs_mom) * 3)
            elif rel_mom < 0 or abs_mom < 0:
                signal_type = SignalType.SELL
                strength = min(1.0, abs(rel_mom) * 3)
            else:
                continue
            
            signal_obj = create_signal(
                symbol=symbol,
                signal_type=signal_type,
                price=price,
                strength=strength,
                timestamp=timestamp,
                relative_momentum=rel_mom,
                absolute_momentum=abs_mom
            )
            signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals