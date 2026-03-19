"""
风险平价策略 (Risk Parity Strategy)

策略原理:
- 每个资产对组合风险的贡献相等
- 风险贡献 = 权重 * 资产波动率
- 通过优化使各资产的风险贡献相等

优势:
- 分散化程度高
- 不依赖收益预测
- 降低尾部风险

参数:
- target_volatility: 目标波动率
- lookback_period: 计算波动率的回溯期
- min_weight: 最小权重约束
- max_weight: 最大权重约束
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from ..base import (
    PortfolioStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class RiskParityStrategy(PortfolioStrategy):
    """风险平价策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.target_volatility = config.get_param('target_volatility', 0.15)
        self.lookback_period = config.get_param('lookback_period', 60)
        self.min_weight = config.get_param('min_weight', 0.05)
        self.max_weight = config.get_param('max_weight', 0.4)
        self._current_weights: Dict[str, float] = {}
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_volatility(self, returns: pd.Series, period: int = 20) -> float:
        """计算年化波动率"""
        vol = returns.rolling(window=period).std().iloc[-1]
        return vol * np.sqrt(252)  # 年化
    
    def _calculate_covariance_matrix(self, 
                                     data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """计算协方差矩阵"""
        returns_dict = {}
        
        for symbol, df in data.items():
            if 'close' in df.columns:
                returns = df['close'].pct_change().dropna()
                returns_dict[symbol] = returns
        
        if not returns_dict:
            return pd.DataFrame()
        
        # 统一长度
        min_len = min(len(r) for r in returns_dict.values())
        returns_dict = {k: v.tail(min_len) for k, v in returns_dict.items()}
        
        returns_df = pd.DataFrame(returns_dict)
        cov_matrix = returns_df.cov() * 252  # 年化
        
        return cov_matrix
    
    def calculate_risk_contribution(self, 
                                    weights: np.ndarray,
                                    cov_matrix: np.ndarray) -> np.ndarray:
        """计算各资产的风险贡献"""
        # 组合波动率
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        # 风险贡献 = 权重 * (协方差矩阵 * 权重) / 组合波动率
        marginal_risk = np.dot(cov_matrix, weights)
        risk_contribution = weights * marginal_risk / portfolio_vol
        
        return risk_contribution
    
    def calculate_risk_parity_weights(self, 
                                      cov_matrix: pd.DataFrame) -> np.ndarray:
        """计算风险平价权重"""
        n_assets = len(cov_matrix)
        
        if n_assets == 0:
            return np.array([])
        
        # 初始化权重
        weights = np.ones(n_assets) / n_assets
        
        # 迭代求解
        for _ in range(100):
            risk_contrib = self.calculate_risk_contribution(weights, cov_matrix.values)
            target_risk = risk_contrib.mean()
            
            # 调整权重使风险贡献相等
            adjustment = target_risk / (risk_contrib + 1e-10)
            weights = weights * adjustment
            
            # 归一化
            weights = weights / weights.sum()
            
            # 应用权重约束
            weights = np.clip(weights, self.min_weight, self.max_weight)
            weights = weights / weights.sum()
        
        # 再次检查风险平价
        risk_contrib = self.calculate_risk_contribution(weights, cov_matrix.values)
        
        return weights
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算目标权重"""
        cov_matrix = self._calculate_covariance_matrix(data)
        
        if cov_matrix.empty:
            # 均分权重
            n = len(data)
            return {symbol: 1.0 / n for symbol in data.keys()}
        
        weights = self.calculate_risk_parity_weights(cov_matrix)
        
        # 转换为字典
        weight_dict = {
            symbol: weights[i] 
            for i, symbol in enumerate(cov_matrix.index)
        }
        
        # 应用波动率目标调整
        if self.target_volatility > 0:
            # 计算当前组合波动率
            returns_list = []
            for symbol in weight_dict:
                if symbol in data and 'close' in data[symbol].columns:
                    ret = data[symbol]['close'].pct_change().dropna()
                    if len(ret) > 0:
                        returns_list.append(ret.tail(self.lookback_period))
            
            if returns_list:
                # 简化: 使用加权平均波动率
                avg_vol = sum(weight_dict[s] * r.std() * np.sqrt(252) 
                             for s, r in zip(weight_dict.keys(), returns_list))
                
                if avg_vol > 0:
                    vol_adjustment = self.target_volatility / avg_vol
                    vol_adjustment = min(vol_adjustment, 2.0)  # 限制最大调整
                    
                    for symbol in weight_dict:
                        weight_dict[symbol] *= vol_adjustment
                    
                    # 重新归一化
                    total = sum(weight_dict.values())
                    if total > 0:
                        weight_dict = {k: v / total for k, v in weight_dict.items()}
        
        self._current_weights = weight_dict
        return weight_dict
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """生成权重调整信号"""
        target_weights = self.calculate_weights(data)
        
        signals = []
        timestamp = datetime.now()
        
        for symbol, weight in target_weights.items():
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                current_weight = self._current_weights.get(symbol, 0)
                weight_change = abs(weight - current_weight)
                
                # 只在权重变化超过阈值时生成信号
                if weight_change > 0.02:
                    if weight > current_weight:
                        signal_type = SignalType.BUY
                    else:
                        signal_type = SignalType.SELL
                    
                    signals.append(create_signal(
                        symbol=symbol,
                        signal_type=signal_type,
                        price=price,
                        strength=min(1.0, weight_change * 5),
                        timestamp=timestamp,
                        target_weight=weight,
                        current_weight=current_weight,
                        weight_change=weight_change
                    ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class EqualWeightStrategy(RiskParityStrategy):
    """等权重策略 - 风险平价的简化版"""
    
    def __init__(self, config: StrategyConfig):
        config.params['target_volatility'] = 0
        super().__init__(config)
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """等权重"""
        n = len(data)
        if n == 0:
            return {}
        
        return {symbol: 1.0 / n for symbol in data.keys()}