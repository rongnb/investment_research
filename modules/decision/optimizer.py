# -*- coding: utf-8 -*-
"""
决策支持模块
用于投资组合优化和风险评估
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from scipy.optimize import minimize

class RiskTolerance(Enum):
    """风险容忍度"""
    LOW = "低风险"
    MODERATE = "中等风险"
    HIGH = "高风险"

@dataclass
class PortfolioConstraint:
    """投资组合约束"""
    min_weight: float = 0.0
    max_weight: float = 1.0
    sector_constraints: Dict[str, Tuple[float, float]] = None

@dataclass
class Portfolio:
    """投资组合"""
    assets: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float

class PortfolioOptimizer:
    """
    投资组合优化器
    """
    
    def __init__(self, budget: float = 100000,
                 risk_tolerance: RiskTolerance = RiskTolerance.MODERATE):
        """
        初始化优化器
        
        Args:
            budget: 总投资预算
            risk_tolerance: 风险容忍度
        """
        self.budget = budget
        self.risk_tolerance = risk_tolerance
        
    def generate_synthetic_assets(self, count: int = 10) -> pd.DataFrame:
        """
        生成合成资产数据
        
        Args:
            count: 资产数量
            
        Returns:
            资产数据DataFrame
        """
        np.random.seed(42)
        
        # 基础配置
        asset_names = [f'Asset_{i+1}' for i in range(count)]
        
        # 预期收益率
        expected_returns = np.random.normal(0.1, 0.05, count)
        expected_returns = np.clip(expected_returns, 0.03, 0.25)
        
        # 波动率
        volatilities = np.random.normal(0.2, 0.1, count)
        volatilities = np.clip(volatilities, 0.08, 0.4)
        
        # 相关性矩阵
        correlation_matrix = np.random.normal(0, 0.3, (count, count))
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
        np.fill_diagonal(correlation_matrix, 1)
        
        # 协方差矩阵
        covariance_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        
        return pd.DataFrame({
            'asset': asset_names,
            'expected_return': expected_returns,
            'volatility': volatilities
        }), covariance_matrix
    
    def optimize_portfolio(self, assets: pd.DataFrame,
                         covariance_matrix: np.ndarray,
                         constraints: PortfolioConstraint = None
                        ) -> Portfolio:
        """
        优化投资组合
        
        Args:
            assets: 资产数据
            covariance_matrix: 协方差矩阵
            constraints: 约束条件
            
        Returns:
            最优投资组合
        """
        constraints = constraints or PortfolioConstraint()
        
        n_assets = len(assets)
        
        # 目标函数：最大化夏普比率
        def objective(weights):
            portfolio_return = np.sum(assets['expected_return'] * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            risk_free_rate = 0.03
            return - (portfolio_return - risk_free_rate) / portfolio_volatility
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # 权重约束
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # 行业约束
        if constraints.sector_constraints:
            # 这里应该根据行业分类定义约束
            pass
        
        # 初始权重
        initial_weights = np.ones(n_assets) / n_assets
        
        # 优化
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        if not result.success:
            raise Exception(f"优化失败: {result.message}")
        
        # 计算最优组合
        optimal_weights = result.x
        
        # 计算组合指标
        portfolio_return = np.sum(assets['expected_return'] * optimal_weights)
        portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(covariance_matrix, optimal_weights)))
        risk_free_rate = 0.03
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        
        return Portfolio(
            assets=dict(zip(assets['asset'], optimal_weights)),
            expected_return=portfolio_return,
            volatility=portfolio_volatility,
            sharpe_ratio=sharpe_ratio
        )
    
    def risk_assessment(self, portfolio: Portfolio) -> Dict:
        """
        风险评估
        
        Args:
            portfolio: 投资组合
            
        Returns:
            风险评估结果
        """
        risk_levels = {
            RiskTolerance.LOW: 0.15,
            RiskTolerance.MODERATE: 0.25,
            RiskTolerance.HIGH: 0.35
        }
        
        max_volatility = risk_levels[self.risk_tolerance]
        
        # 风险评估
        risk_score = min(portfolio.volatility / max_volatility, 1.0)
        
        risk_category = '低风险' if risk_score < 0.5 else '中风险' if risk_score < 0.8 else '高风险'
        
        return {
            'volatility': portfolio.volatility,
            'max_volatility': max_volatility,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'sharpe_ratio': portfolio.sharpe_ratio
        }
    
    def optimize_risk_return(self) -> Portfolio:
        """
        快速优化风险收益组合
        
        Returns:
            最优投资组合
        """
        assets, covariance = self.generate_synthetic_assets()
        
        return self.optimize_portfolio(assets, covariance)
    
    def get_weight_allocation(self, portfolio: Portfolio) -> Dict:
        """
        计算权重分配
        
        Args:
            portfolio: 投资组合
            
        Returns:
            权重分配字典
        """
        allocations = {}
        for asset, weight in portfolio.assets.items():
            allocations[asset] = {
                'weight': weight,
                'amount': weight * self.budget
            }
        return allocations
