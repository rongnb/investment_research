"""
多因子策略 (Multi-Factor Strategy)

策略原理:
- 选取多个因子(价值、动量、质量、规模等)
- 根据因子得分进行加权选股
- 因子权重可自适应调整

因子类型:
- 价值因子: PE, PB, PS, 股息率
- 动量因子: 过去N月收益率
- 质量因子: ROE, 资产负债率, 现金流
- 规模因子: 市值

参数:
- factors: 使用的因子列表
- factor_weights: 因子权重
- rebalance_period: 调仓周期
- top_n: 选取股票数量
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from ..base import (
    Strategy, MultiAssetStrategy, StrategyConfig, 
    Signal, SignalType, create_signal
)


class MultiFactorStrategy(MultiAssetStrategy):
    """多因子策略"""
    
    DEFAULT_FACTORS = ['value', 'momentum', 'quality']
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.factors = config.get_param('factors', self.DEFAULT_FACTORS)
        self.factor_weights = config.get_param('factor_weights', {
            'value': 0.33,
            'momentum': 0.33,
            'quality': 0.34
        })
        self.rebalance_period = config.get_param('rebalance_period', 20)
        self.top_n = config.get_param('top_n', 10)
        self._last_rebalance = 0
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_factor_scores(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """计算各因子得分"""
        scores = {}
        
        for symbol, df in data.items():
            if 'close' not in df.columns:
                continue
            
            prices = df['close']
            symbol_scores = {}
            
            # 价值因子
            if 'value' in self.factors:
                # 使用价格/收益模拟PE的倒数
                returns = prices.pct_change(periods=20)
                symbol_scores['value'] = returns.iloc[-1] if not np.isnan(returns.iloc[-1]) else 0
            
            # 动量因子
            if 'momentum' in self.factors:
                momentum = prices.pct_change(periods=60)
                symbol_scores['momentum'] = momentum.iloc[-1] if not np.isnan(momentum.iloc[-1]) else 0
            
            # 质量因子 (简化: 使用收益率稳定性)
            if 'quality' in self.factors:
                returns = prices.pct_change()
                symbol_scores['quality'] = -returns.std()  # 波动率越低越好
            
            scores[symbol] = symbol_scores
        
        # 转换为DataFrame
        scores_df = pd.DataFrame(scores).T
        
        # 标准化因子得分
        for factor in self.factors:
            if factor in scores_df.columns:
                col = scores_df[factor]
                scores_df[f'{factor}_norm'] = (col - col.mean()) / col.std() if col.std() > 0 else 0
        
        return scores_df
    
    def _calculate_composite_score(self, scores_df: pd.DataFrame) -> pd.Series:
        """计算综合得分"""
        composite = pd.Series(0.0, index=scores_df.index)
        
        for factor in self.factors:
            weight = self.factor_weights.get(factor, 0)
            norm_col = f'{factor}_norm'
            if norm_col in scores_df.columns:
                composite += weight * scores_df[norm_col]
        
        return composite
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        if not data:
            return []
        
        scores_df = self._calculate_factor_scores(data)
        composite = self._calculate_composite_score(scores_df)
        
        # 排序并选取Top N
        ranked = composite.sort_values(ascending=False)
        top_symbols = ranked.head(self.top_n)
        
        signals = []
        timestamp = datetime.now()
        
        for symbol, score in top_symbols.items():
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                
                signal_obj = create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=min(1.0, (score - ranked.iloc[-self.top_n]) / (ranked.iloc[0] - ranked.iloc[-1] + 0.001)),
                    timestamp=timestamp,
                    factor_score=score,
                    rank=list(ranked.index).index(symbol) + 1
                )
                signals.append(signal_obj)
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class SmartAlphaStrategy(MultiFactorStrategy):
    """智能Alpha策略 - 自适应因子权重"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = config.get_param('lookback_period', 60)
        self._factor_returns = {f: [] for f in self.factors}
        
    def _update_factor_weights(self, data: Dict[str, pd.DataFrame]):
        """根据历史表现更新因子权重"""
        # 简化的自适应权重: 近期表现好的因子权重增加
        for factor in self.factors:
            if factor in self._factor_returns and self._factor_returns[factor]:
                recent_return = np.mean(self._factor_returns[factor][-5:])
                self.factor_weights[factor] = max(0.1, self.factor_weights.get(factor, 0.33) + recent_return * 0.1)
        
        # 归一化权重
        total = sum(self.factor_weights.values())
        for factor in self.factors:
            self.factor_weights[factor] /= total


class EnsembleStrategy(Strategy):
    """集成策略 - 多个子策略的加权组合"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.sub_strategies: List[Strategy] = []
        self.strategy_weights = config.get_param('strategy_weights', {})
        
    def add_strategy(self, strategy: Strategy, weight: float = 1.0):
        """添加子策略"""
        self.sub_strategies.append(strategy)
        self.strategy_weights[strategy.name] = weight
        
    def initialize(self) -> None:
        for strategy in self.sub_strategies:
            strategy.initialize()
        self._is_initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        all_signals = []
        
        for strategy in self.sub_strategies:
            signals = strategy.generate_signals(data)
            weight = self.strategy_weights.get(strategy.name, 1.0)
            
            for sig in signals:
                sig.strength *= weight
            
            all_signals.extend(signals)
        
        # 按时间聚合信号
        if not all_signals:
            return []
        
        # 返回加权后的信号
        return all_signals