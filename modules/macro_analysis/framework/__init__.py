# -*- coding: utf-8 -*-
"""
Top-down 分析框架

支持自上而下的大类资产配置和选股策略
"""

from .top_down import TopDownAnalyzer, AssetClass
from .china_market import ChinaMarketAnalyzer

__all__ = [
    "TopDownAnalyzer",
    "AssetClass", 
    "ChinaMarketAnalyzer",
]
