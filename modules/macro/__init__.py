# -*- coding: utf-8 -*-
"""
宏观分析模块

提供宏观经济指标采集、周期分析、情景分析、政策评估等功能
"""

from .analyzer import MacroAnalyzer, EconomicCycle, EconomicIndicators
from .cycle import EconomicCycleAnalyzer, CycleAnalysis, create_default_indicators
from .scenario import ScenarioAnalyzer, ScenarioAnalysis, create_default_analysis
from .policy import PolicyAnalyzer, PolicyAssessment, PolicyType, PolicyDirection

__all__ = [
    # 宏观经济分析
    'MacroAnalyzer',
    'EconomicCycle',
    'EconomicIndicators',
    # 经济周期分析
    'EconomicCycleAnalyzer',
    'CycleAnalysis',
    'create_default_indicators',
    # 情景分析
    'ScenarioAnalyzer',
    'ScenarioAnalysis',
    'create_default_analysis',
    # 政策评估
    'PolicyAnalyzer',
    'PolicyAssessment',
    'PolicyType',
    'PolicyDirection',
]