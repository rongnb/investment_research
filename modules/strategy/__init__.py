"""
策略库 - 提供多种经典和高级交易策略实现
"""

from .base import (
    Strategy, 
    Signal, 
    SignalType,
    Position,
    TimeFrame,
    StrategyConfig
)
from .manager import StrategyManager, StrategyRegistry

# 经典策略
from .classic.moving_average_crossover import MovingAverageCrossoverStrategy
from .classic.macd_strategy import MACDStrategy
from .classic.rsi_strategy import RSIStrategy
from .classic.bollinger_strategy import BollingerBandsStrategy
from .classic.breakout_strategy import BreakoutStrategy
from .classic.mean_reversion import MeanReversionStrategy
from .classic.momentum import ClassicMomentumStrategy

# 高级策略
from .advanced.multi_factor import MultiFactorStrategy
from .advanced.style_rotation import StyleRotationStrategy
from .advanced.sector_rotation import SectorRotationStrategy
from .advanced.market_neutral import MarketNeutralStrategy

# 组合策略
from .portfolio.risk_parity import RiskParityStrategy
from .portfolio.maximum_diversification import MaximumDiversificationStrategy
from .portfolio.target_risk import TargetRiskStrategy
from .portfolio.smart_beta import SmartBetaStrategy

__all__ = [
    # 基类
    'Strategy',
    'Signal',
    'SignalType',
    'Position',
    'TimeFrame',
    'StrategyConfig',
    'StrategyManager',
    'StrategyRegistry',
    
    # 经典策略
    'MovingAverageCrossoverStrategy',
    'MACDStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'BreakoutStrategy',
    'MeanReversionStrategy',
    'ClassicMomentumStrategy',
    
    # 高级策略
    'MultiFactorStrategy',
    'StyleRotationStrategy',
    'SectorRotationStrategy',
    'MarketNeutralStrategy',
    
    # 组合策略
    'RiskParityStrategy',
    'MaximumDiversificationStrategy',
    'TargetRiskStrategy',
    'SmartBetaStrategy',
]