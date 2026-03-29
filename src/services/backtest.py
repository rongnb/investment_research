"""
策略回测服务
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from datetime import datetime


class BacktestResult:
    """回测结果"""
    def __init__(self):
        self.total_return: float = 0.0
        self.annual_return: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.equity_curve: pd.Series = None
        self.trades: List[Dict] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "trades": self.trades
        }


def calculate_metrics(prices: pd.Series, weights: pd.Series = None) -> BacktestResult:
    """计算回测指标
    
    Args:
        prices: 价格序列
        weights: 权重序列（可选，用于组合）
    
    Returns:
        回测结果对象
    """
    result = BacktestResult()
    
    # 计算收益率
    returns = prices.pct_change().dropna()
    
    if weights is not None:
        # 加权组合收益
        returns = (returns * weights).sum(axis=1)
    
    # 累计收益
    cumulative = (1 + returns).cumprod()
    result.total_return = (cumulative.iloc[-1] - 1) * 100  # 百分比
    
    # 年化收益
    n_days = len(returns)
    years = n_days / 252  # 交易日
    if years > 0:
        result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
    else:
        result.annual_return = result.total_return
    
    # 夏普比率（假设无风险利率 0）
    if returns.std() != 0:
        volatility = returns.std() * np.sqrt(252)
        result.sharpe_ratio = (returns.mean() * 252) / volatility
    
    # 最大回撤
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    result.max_drawdown = drawdown.min() * 100  # 百分比
    
    result.equity_curve = cumulative
    return result


class BuyAndHoldStrategy:
    """买入持有策略（基准策略）"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行回测"""
        close_prices = prices['close']
        return calculate_metrics(close_prices)
