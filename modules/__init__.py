"""
Investment Research System - Modules Package
"""

__version__ = '0.1.0'
__author__ = 'investment-research-team'
__email__ = 'contact@investment-research.com'

from .macro.analyzer import MacroAnalyzer, EconomicCycle, EconomicIndicators
from .research.analyzer import ResearchAnalyzer
from .estimation.estimator import ParameterEstimator
from .decision.optimizer import PortfolioOptimizer

__all__ = [
    'MacroAnalyzer',
    'EconomicCycle',
    'EconomicIndicators',
    'ResearchAnalyzer',
    'ParameterEstimator',
    'PortfolioOptimizer'
]
