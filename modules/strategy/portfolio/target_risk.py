"""
目标风险策略 (Target Risk Strategy)

策略原理:
- 设定目标风险水平(波动率)
- 动态调整资产权重以维持目标风险
- 使用风险模型估计组合波动率

类型:
- 目标波动率策略
- 目标下行风险策略
- 目标VaR策略

参数:
- target_volatility: 目标年化波动率
- lookback_period: 回溯周期
- volatility_adjustment: 波动率调整系数
- min_weight/max_weight: 权重约束
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

from ..base import (
    PortfolioStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class TargetRiskStrategy(PortfolioStrategy):
    """目标风险策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.target_volatility = config.get_param('target_volatility', 0.15)
        self.lookback_period = config.get_param('lookback_period', 60)
        self.volatility_adjustment = config.get_param('volatility_adjustment', 0.5)
        self.min_weight = config.get_param('min_weight', 0.05)
        self.max_weight = config.get_param('max_weight', 0.5)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._volatility_history = []
    
    def _calculate_portfolio_volatility(self, 
                                         data: Dict[str, pd.DataFrame],
                                         weights: Dict[str, float]) -> float:
        """计算组合波动率"""
        if not data or not weights:
            return 0
        
        # 简化: 使用加权平均波动率
        portfolio_vol = 0
        for symbol, weight in weights.items():
            if symbol in data and 'close' in data[symbol].columns:
                returns = data[symbol]['close'].pct_change().dropna()
                if len(returns) > self.lookback_period:
                    vol = returns.tail(self.lookback_period).std() * np.sqrt(252)
                    portfolio_vol += weight * vol
        
        return portfolio_vol
    
    def _calculate_volatility_scalar(self, 
                                      current_vol: float) -> float:
        """计算波动率调整系数"""
        if current_vol == 0:
            return 1.0
        
        vol_ratio = self.target_volatility / current_vol
        
        # 渐进调整
        scalar = 1 + self.volatility_adjustment * (vol_ratio - 1)
        scalar = max(0.5, min(2.0, scalar))  # 限制调整范围
        
        return scalar
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算目标风险权重"""
        symbols = list(data.keys())
        n = len(symbols)
        
        if n == 0:
            return {}
        
        # 基础权重: 等权重
        base_weights = {s: 1.0 / n for s in symbols}
        
        # 计算当前波动率
        current_vol = self._calculate_portfolio_volatility(data, base_weights)
        self._volatility_history.append(current_vol)
        
        # 计算调整系数
        scalar = self._calculate_volatility_scalar(current_vol)
        
        # 调整权重
        adjusted_weights = {}
        for symbol in symbols:
            adjusted_weights[symbol] = base_weights[symbol] * scalar
        
        # 应用约束
        for symbol in adjusted_weights:
            adjusted_weights[symbol] = max(self.min_weight, 
                                           min(self.max_weight, 
                                               adjusted_weights[symbol]))
        
        # 归一化
        total = sum(adjusted_weights.values())
        if total > 0:
            adjusted_weights = {k: v / total for k, v in adjusted_weights.items()}
        
        self._current_weights = adjusted_weights
        return adjusted_weights
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """生成再平衡信号"""
        target_weights = self.calculate_weights(data)
        
        signals = []
        timestamp = datetime.now()
        
        for symbol, weight in target_weights.items():
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                current_weight = self._current_weights.get(symbol, 0)
                weight_change = abs(weight - current_weight)
                
                if weight_change > 0.03:  # 再平衡阈值
                    signals.append(create_signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY if weight > current_weight else SignalType.SELL,
                        price=price,
                        strength=min(1.0, weight_change * 10),
                        timestamp=timestamp,
                        target_weight=weight,
                        current_weight=current_weight,
                        target_volatility=self.target_volatility,
                        current_volatility=self._volatility_history[-1] if self._volatility_history else 0
                    ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class TargetVolatilityStrategy(TargetRiskStrategy):
    """目标波动率策略 - 目标风险的简化版"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """简化版: 直接基于波动率调整"""
        symbols = list(data.keys())
        
        if not symbols:
            return {}
        
        # 计算各资产波动率
        volatilities = {}
        for symbol in symbols:
            if symbol in data and 'close' in data[symbol].columns:
                returns = data[symbol]['close'].pct_change().dropna()
                if len(returns) > 20:
                    vol = returns.tail(20).std() * np.sqrt(252)
                    volatilities[symbol] = vol
        
        if not volatilities:
            return {symbols[0]: 1.0}
        
        # 逆波动率加权
        inv_vol = {s: 1.0 / (v + 1e-10) for s, v in volatilities.items()}
        total = sum(inv_vol.values())
        weights = {s: v / total for s, v in inv_vol.items()}
        
        # 缩放至目标波动率
        portfolio_vol = sum(weights[s] * volatilities.get(s, 0) for s in weights)
        
        if portfolio_vol > 0 and self.target_volatility > 0:
            scale = self.target_volatility / portfolio_vol
            scale = min(scale, 3.0)  # 限制杠杆
            weights = {s: w * scale for s, w in weights.items()}
            
            # 归一化
            total = sum(weights.values())
            weights = {s: w / total for s, w in weights.items()}
        
        # 应用约束
        for symbol in weights:
            weights[symbol] = max(self.min_weight, 
                                 min(self.max_weight, 
                                     weights[symbol]))
        
        total = sum(weights.values())
        weights = {s: w / total for s, w in weights.items()}
        
        self._current_weights = weights
        return weights


class RiskBudgetStrategy(TargetRiskStrategy):
    """风险预算策略 - 每个资产有独立的风险预算"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.risk_budgets = config.get_param('risk_budgets', {})  # {symbol: risk_budget_ratio}
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """基于风险预算计算权重"""
        symbols = list(data.keys())
        
        if not symbols:
            return {}
        
        # 如果没有设定风险预算,则使用等预算
        if not self.risk_budgets:
            self.risk_budgets = {s: 1.0 / len(symbols) for s in symbols}
        
        # 计算各资产波动率
        volatilities = {}
        for symbol in symbols:
            if symbol in data and 'close' in data[symbol].columns:
                returns = data[symbol]['close'].pct_change().dropna()
                if len(returns) > 20:
                    volatilities[symbol] = returns.tail(20).std() * np.sqrt(252)
        
        if not volatilities:
            return {symbols[0]: 1.0}
        
        # 计算组合波动率估计
        # 简化: 使用加权平均
        total_vol = sum(self.risk_budgets.get(s, 0) * volatilities.get(s, 0) 
                       for s in symbols)
        
        # 反推权重
        weights = {}
        for symbol in symbols:
            risk_budget = self.risk_budgets.get(symbol, 1.0 / len(symbols))
            vol = volatilities.get(symbol, 0.01)
            
            if total_vol > 0:
                weight = risk_budget * self.target_volatility / vol
            else:
                weight = risk_budget
            
            weights[symbol] = max(0, weight)
        
        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {s: w / total for s, w in weights.items()}
        
        self._current_weights = weights
        return weights