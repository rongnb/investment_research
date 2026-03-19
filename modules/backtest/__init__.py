"""
回测系统模块 - 策略回测和绩效分析
事件驱动回测框架，支持滑点、手续费模拟，完整绩效指标计算
"""

from .engine import BacktestEngine, StrategyBase, EventType, Event, Order
from .data_handler import DataHandler
from .order_manager import OrderManager
from .position_manager import PositionManager
from .performance_calculator import PerformanceCalculator
from .metrics import (
    calculate_returns,
    calculate_cumulative_returns,
    calculate_annualized_return,
    calculate_volatility,
    calculate_sharpe,
    calculate_sortino,
    calculate_calmar,
    calculate_max_drawdown,
    calculate_max_drawdown_duration,
    calculate_win_rate,
    calculate_profit_loss_ratio,
    calculate_beta,
    calculate_alpha,
    calculate_information_ratio,
    calculate_comprehensive_metrics
)
from .risk import RiskAnalyzer, VaR, calculate_cvar, calculate_expected_shortfall
from .report import ReportGenerator

__all__ = [
    # 核心引擎
    'BacktestEngine',
    'StrategyBase',
    'EventType',
    'Event',
    'Order',
    
    # 组件
    'DataHandler',
    'OrderManager',
    'PositionManager',
    'PerformanceCalculator',
    
    # 指标计算
    'calculate_returns',
    'calculate_cumulative_returns',
    'calculate_annualized_return',
    'calculate_volatility',
    'calculate_sharpe',
    'calculate_sortino',
    'calculate_calmar',
    'calculate_max_drawdown',
    'calculate_max_drawdown_duration',
    'calculate_win_rate',
    'calculate_profit_loss_ratio',
    'calculate_beta',
    'calculate_alpha',
    'calculate_information_ratio',
    'calculate_comprehensive_metrics',
    
    # 风险分析
    'RiskAnalyzer',
    'VaR',
    'calculate_cvar',
    'calculate_expected_shortfall',
    
    # 报告
    'ReportGenerator'
]
