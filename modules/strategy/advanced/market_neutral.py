"""
市场中性策略 (Market Neutral Strategy)

策略原理:
- 同时持有多头和空头头寸
- 消除市场系统性风险,获取Alpha收益
- 期望收益与市场涨跌无关

类型:
- 股票多空: 做多低估股票,做空高估股票
- 配对交易: 做多一只股票,做空另一只相关股票
- 期现套利: 期货与现货对冲

参数:
- long_short_ratio: 多空比例 (如1表示1:1)
- hedge_ratio: 对冲比率
- max_position: 单边最大持仓
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..base import (
    Strategy, MultiAssetStrategy, StrategyConfig, 
    Signal, SignalType, Position, create_signal
)


class MarketNeutralStrategy(MultiAssetStrategy):
    """市场中性策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.long_short_ratio = config.get_param('long_short_ratio', 1.0)
        self.hedge_ratio = config.get_param('hedge_ratio', 1.0)
        self.max_position = config.get_param('max_position', 0.1)
        self._positions: Dict[str, Position] = {}
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_pair_spread(self, 
                                data_long: pd.DataFrame, 
                                data_short: pd.DataFrame) -> pd.Series:
        """计算配对价差"""
        if 'close' not in data_long.columns or 'close' not in data_short.columns:
            return pd.Series()
        
        price_long = data_long['close']
        price_short = data_short['close']
        
        # 对冲后的价差
        spread = price_long - self.hedge_ratio * price_short
        return spread
    
    def _calculate_zscore(self, spread: pd.Series, period: int = 20) -> pd.Series:
        """计算价差Z-Score"""
        ma = spread.rolling(window=period).mean()
        std = spread.rolling(window=period).std()
        zscore = (spread - ma) / std
        return zscore
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """
        生成多空信号
        
        data格式: {'long_symbol': df, 'short_symbol': df}
        或 {'stock1': df, 'stock2': df, ...}
        """
        if len(data) < 2:
            return []
        
        signals = []
        timestamp = datetime.now()
        
        # 简化的多空策略: 选择相对强弱
        returns = {}
        for symbol, df in data.items():
            if 'close' in df.columns:
                ret = df['close'].pct_change(periods=20).iloc[-1]
                returns[symbol] = ret if not np.isnan(ret) else 0
        
        if len(returns) < 2:
            return []
        
        # 排序
        sorted_stocks = sorted(returns.items(), key=lambda x: x[1], reverse=True)
        
        # 做多最强的,做空最弱的
        long_symbol = sorted_stocks[0][0]
        short_symbol = sorted_stocks[-1][0]
        
        # 多头信号
        if long_symbol in data and 'close' in data[long_symbol].columns:
            price = data[long_symbol]['close'].iloc[-1]
            signals.append(create_signal(
                symbol=long_symbol,
                signal_type=SignalType.BUY,
                price=price,
                strength=0.8,
                timestamp=timestamp,
                position=Position.LONG
            ))
            self._positions[long_symbol] = Position.LONG
        
        # 空头信号
        if short_symbol in data and 'close' in data[short_symbol].columns:
            price = data[short_symbol]['close'].iloc[-1]
            signals.append(create_signal(
                symbol=short_symbol,
                signal_type=SignalType.SELL,
                price=price,
                strength=0.8,
                timestamp=timestamp,
                position=Position.SHORT
            ))
            self._positions[short_symbol] = Position.SHORT
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals
    
    def calculate_beta(self, 
                       returns: pd.Series, 
                       market_returns: pd.Series) -> float:
        """计算Beta"""
        covariance = returns.cov(market_returns)
        market_variance = market_returns.var()
        
        if market_variance == 0:
            return 1.0
        
        return covariance / market_variance
    
    def hedge_market_exposure(self, 
                              positions: Dict[str, float],
                              data: Dict[str, pd.DataFrame],
                              market_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算对冲后的净暴露
        
        Returns:
            对冲后各标的的权重
        """
        if 'close' not in market_data.columns:
            return positions
        
        market_returns = market_data['close'].pct_change()
        hedged_positions = {}
        
        for symbol, weight in positions.items():
            if symbol in data and 'close' in data[symbol].columns:
                stock_returns = data[symbol]['close'].pct_change()
                beta = self.calculate_beta(stock_returns, market_returns)
                
                # 对冲beta
                hedged_positions[symbol] = weight - beta * sum(positions.values()) / len(positions)
            else:
                hedged_positions[symbol] = weight
        
        return hedged_positions


class LongShortStrategy(MarketNeutralStrategy):
    """股票多空策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.universe_size = config.get_param('universe_size', 20)
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """生成多空信号"""
        if len(data) < 3:
            return []
        
        # 计算所有标的的动量
        momentum = {}
        for symbol, df in data.items():
            if 'close' in df.columns:
                ret = df['close'].pct_change(periods=20).iloc[-1]
                momentum[symbol] = ret if not np.isnan(ret) else 0
        
        # 排序
        sorted_stocks = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
        
        signals = []
        timestamp = datetime.now()
        
        # 做多Top N
        top_n = min(self.top_n if hasattr(self, 'top_n') else 5, len(sorted_stocks) // 2)
        
        for i, (symbol, ret) in enumerate(sorted_stocks[:top_n]):
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                strength = 1.0 - i * 0.1
                
                signals.append(create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    position=Position.LONG,
                    momentum=ret
                ))
        
        # 做空Bottom N
        for i, (symbol, ret) in enumerate(sorted_stocks[-top_n:]):
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                strength = 1.0 - i * 0.1
                
                signals.append(create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=strength,
                    timestamp=timestamp,
                    position=Position.SHORT,
                    momentum=ret
                ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class StatisticalArbitrageStrategy(MarketNeutralStrategy):
    """统计套利策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.entry_threshold = config.get_param('entry_threshold', 2.0)
        self.exit_threshold = config.get_param('exit_threshold', 0.5)
        self.lookback_period = config.get_param('lookback_period', 60)
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """统计套利信号"""
        if len(data) != 2:
            return []
        
        symbols = list(data.keys())
        long_symbol, short_symbol = symbols[0], symbols[1]
        
        spread = self._calculate_pair_spread(data[long_symbol], data[short_symbol])
        zscore = self._calculate_zscore(spread, self.lookback_period)
        
        signals = []
        timestamp = datetime.now()
        
        if len(zscore) < 1:
            return []
        
        z = zscore.iloc[-1]
        z_prev = zscore.iloc[-2] if len(zscore) > 1 else 0
        
        # 价差扩大: 做空spread (做多long, 做空short)
        if z_prev < self.entry_threshold and z >= self.entry_threshold:
            # 价差过大,预期回归
            price_long = data[long_symbol]['close'].iloc[-1]
            price_short = data[short_symbol]['close'].iloc[-1]
            
            signals.append(create_signal(
                symbol=long_symbol,
                signal_type=SignalType.BUY,
                price=price_long,
                strength=min(1.0, abs(z) / 3),
                timestamp=timestamp,
                position=Position.LONG,
                zscore=z
            ))
            
            signals.append(create_signal(
                symbol=short_symbol,
                signal_type=SignalType.SELL,
                price=price_short,
                strength=min(1.0, abs(z) / 3),
                timestamp=timestamp,
                position=Position.SHORT,
                zscore=z
            ))
        
        # 价差收敛: 平仓
        elif abs(z) < self.exit_threshold and abs(z_prev) >= self.exit_threshold:
            # 价差回归,平仓
            price_long = data[long_symbol]['close'].iloc[-1]
            price_short = data[short_symbol]['close'].iloc[-1]
            
            signals.append(create_signal(
                symbol=long_symbol,
                signal_type=SignalType.CLOSE_LONG,
                price=price_long,
                strength=0.8,
                timestamp=timestamp,
                zscore=z
            ))
            
            signals.append(create_signal(
                symbol=short_symbol,
                signal_type=SignalType.CLOSE_SHORT,
                price=price_short,
                strength=0.8,
                timestamp=timestamp,
                zscore=z
            ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals