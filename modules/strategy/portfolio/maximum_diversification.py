"""
最大分散化策略 (Maximum Diversification Strategy)

策略原理:
- 最大化组合的分散化程度
- 分散化比率 = 组合波动率 / 加权平均资产波动率
- 目标: 让分散化比率最大化

优势:
- 分散化程度比风险平价更高
- 考虑资产间的相关性

参数:
- min_weight: 最小权重
- max_weight: 最大权重
- target_volatility: 目标波动率
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

from ..base import (
    PortfolioStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class MaximumDiversificationStrategy(PortfolioStrategy):
    """最大分散化策略"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.min_weight = config.get_param('min_weight', 0.05)
        self.max_weight = config.get_param('max_weight', 0.4)
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算年化波动率"""
        return returns.std() * np.sqrt(252)
    
    def _calculate_diversification_ratio(self, 
                                          weights: np.ndarray,
                                          volatilities: np.ndarray,
                                          corr_matrix: np.ndarray) -> float:
        """
        计算分散化比率
        
        DR = 组合波动率 / 加权平均资产波动率
        """
        # 加权平均波动率
        weighted_vol = np.dot(weights, volatilities)
        
        if weighted_vol == 0:
            return 0
        
        # 组合波动率
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        return portfolio_vol / weighted_vol
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算最大分散化权重"""
        symbols = list(data.keys())
        n = len(symbols)
        
        if n == 0:
            return {}
        
        # 计算收益率
        returns_dict = {}
        for symbol in symbols:
            if 'close' in data[symbol].columns:
                returns = data[symbol]['close'].pct_change().dropna()
                returns_dict[symbol] = returns
        
        if len(returns_dict) < 2:
            return {symbols[0]: 1.0}
        
        # 统一长度
        min_len = min(len(r) for r in returns_dict.values())
        returns_dict = {k: v.tail(min_len) for k, v in returns_dict.items()}
        
        returns_df = pd.DataFrame(returns_dict)
        
        # 计算波动率
        volatilities = returns_df.std() * np.sqrt(252)
        
        # 计算相关系数矩阵
        corr_matrix = returns_df.corr().values
        
        # 网格搜索最优权重
        best_ratio = 0
        best_weights = np.ones(n) / n
        
        # 使用随机搜索
        for _ in range(500):
            # 随机生成权重
            weights = np.random.dirichlet(np.ones(n))
            
            # 应用约束
            weights = np.clip(weights, self.min_weight, self.max_weight)
            weights = weights / weights.sum()
            
            # 计算分散化比率
            ratio = self._calculate_diversification_ratio(
                weights, 
                volatilities.values,
                corr_matrix
            )
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_weights = weights.copy()
        
        # 转换为字典
        weight_dict = {
            symbols[i]: best_weights[i] 
            for i in range(n)
        }
        
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
                
                if weight_change > 0.02:
                    signals.append(create_signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY if weight > current_weight else SignalType.SELL,
                        price=price,
                        strength=min(1.0, weight_change * 5),
                        timestamp=timestamp,
                        target_weight=weight,
                        diversification_ratio=self._calculate_diversification_ratio(
                            np.array([weight]),
                            np.array([1.0]),
                            np.array([[1.0]])
                        )
                    ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class MinimumVarianceStrategy(MaximumDiversificationStrategy):
    """最小方差策略 - 最大分散化的特例"""
    
    def _calculate_diversification_ratio(self, 
                                          weights: np.ndarray,
                                          volatilities: np.ndarray,
                                          corr_matrix: np.ndarray) -> float:
        """最小方差: 最小化组合波动率"""
        cov_matrix = np.outer(volatilities, volatilities) * corr_matrix
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        return 1.0 / (portfolio_vol + 1e-10)


class HierarchicalRiskParityStrategy(PortfolioStrategy):
    """分层风险平价策略 (HRP)"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.linkage_method = config.get_param('linkage_method', 'single')
        
    def initialize(self) -> None:
        self._is_initialized = True
    
    def _calculate_distance_matrix(self, corr_matrix: np.DataFrame) -> np.ndarray:
        """计算距离矩阵 (基于相关系数)"""
        return np.sqrt(0.5 * (1 - corr_matrix.values))
    
    def _hierarchical_clustering(self, distance_matrix: np.ndarray) -> list:
        """层次聚类"""
        n = len(distance_matrix)
        clusters = list(range(n))
        
        while len(clusters) > 1:
            min_dist = float('inf')
            merge = (0, 1)
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    dist = distance_matrix[clusters[i]][clusters[j]]
                    if dist < min_dist:
                        min_dist = dist
                        merge = (i, j)
            
            # 合并聚类
            new_cluster = (clusters[merge[0]], clusters[merge[1]])
            clusters = [c for i, c in enumerate(clusters) if i not in merge]
            clusters.append(new_cluster)
        
        return clusters
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算分层风险平价权重"""
        symbols = list(data.keys())
        n = len(symbols)
        
        if n == 0:
            return {}
        
        # 计算收益率
        returns_dict = {}
        for symbol in symbols:
            if 'close' in data[symbol].columns:
                returns_dict[symbol] = data[symbol]['close'].pct_change().dropna()
        
        if len(returns_dict) < 2:
            return {symbols[0]: 1.0}
        
        min_len = min(len(r) for r in returns_dict.values())
        returns_df = pd.DataFrame({k: v.tail(min_len) for k, v in returns_dict.items()})
        
        # 计算协方差矩阵
        cov_matrix = returns_df.cov() * 252
        
        # 简化: 使用逆波动率加权
        variances = np.diag(cov_matrix.values)
        inv_vol = 1.0 / np.sqrt(variances + 1e-10)
        weights = inv_vol / inv_vol.sum()
        
        # 应用约束
        weights = np.clip(weights, self.min_weight, self.max_weight)
        weights = weights / weights.sum()
        
        return {symbols[i]: weights[i] for i in range(n)}
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        return []  # 与父类相同