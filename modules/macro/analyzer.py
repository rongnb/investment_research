# -*- coding: utf-8 -*-
"""
宏观分析模块
用于经济指标监控、周期判断等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class EconomicCycle(Enum):
    """经济周期阶段"""
    RECOVERY = "复苏期"
    EXPANSION = "扩张期"
    PEAK = "顶峰期"
    CONTRACTION = "收缩期"
    TROUGH = "低谷期"

@dataclass
class EconomicIndicators:
    """经济指标数据"""
    gdp_growth: float  # GDP增长率
    cpi: float  # 消费者物价指数
    ppi: float  # 生产者物价指数
    interest_rate: float  # 利率水平
    unemployment_rate: float  # 失业率
    money_supply: float  # 货币供应量M2
    consumer_confidence: float  # 消费者信心指数
    manufacturing_pmi: float  # 制造业PMI

class MacroAnalyzer:
    """
    宏观经济分析器
    用于获取和分析宏观经济指标
    """
    
    def __init__(self, data_source: str = "tushare"):
        """
        初始化宏观分析器
        
        Args:
            data_source: 数据源名称，可选 "tushare", "akshare", "local"
        """
        self.data_source = data_source
        self.historical_data = pd.DataFrame()
        
    def fetch_economic_indicators(self, start_date: str, end_date: str) -> EconomicIndicators:
        """
        获取经济指标数据
        
        Args:
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"
            
        Returns:
            EconomicIndicators对象
        """
        # 这里应该调用实际的数据源API
        # 目前使用模拟数据
        return EconomicIndicators(
            gdp_growth=5.2,
            cpi=2.1,
            ppi=-1.5,
            interest_rate=3.45,
            unemployment_rate=5.2,
            money_supply=8.7,
            consumer_confidence=88.9,
            manufacturing_pmi=49.0
        )
    
    def analyze_economic_cycle(self, indicators: EconomicIndicators) -> EconomicCycle:
        """
        分析经济周期阶段
        
        Args:
            indicators: 经济指标数据
            
        Returns:
            EconomicCycle枚举值
        """
        # 基于多个指标综合判断经济周期
        score = 0
        
        # GDP增长
        if indicators.gdp_growth > 6:
            score += 2
        elif indicators.gdp_growth > 4:
            score += 1
        else:
            score -= 1
        
        # CPI
        if 1 < indicators.cpi < 3:
            score += 1
        elif indicators.cpi > 4:
            score -= 1
        
        # PMI
        if indicators.manufacturing_pmi > 50:
            score += 2
        else:
            score -= 1
        
        # 失业率
        if indicators.unemployment_rate < 5:
            score += 1
        else:
            score -= 1
        
        # 根据综合得分判断周期
        if score >= 4:
            return EconomicCycle.EXPANSION
        elif score >= 2:
            return EconomicCycle.RECOVERY
        elif score >= 0:
            return EconomicCycle.PEAK
        elif score >= -2:
            return EconomicCycle.CONTRACTION
        else:
            return EconomicCycle.TROUGH
    
    def generate_macro_report(self, indicators: EconomicIndicators, cycle: EconomicCycle) -> str:
        """
        生成宏观分析报告
        
        Args:
            indicators: 经济指标数据
            cycle: 经济周期阶段
            
        Returns:
            报告文本
        """
        report = f"""
宏观经济分析报告
================

一、经济指标概览
----------------
GDP增长率: {indicators.gdp_growth:.2f}%
CPI: {indicators.cpi:.2f}%
PPI: {indicators.ppi:.2f}%
利率水平: {indicators.interest_rate:.2f}%
失业率: {indicators.unemployment_rate:.2f}%
货币供应量M2: {indicators.money_supply:.2f}%
消费者信心指数: {indicators.consumer_confidence:.2f}
制造业PMI: {indicators.manufacturing_pmi:.2f}

二、经济周期判断
----------------
当前阶段: {cycle.value}

三、投资建议
----------------
基于当前{cycle.value}，建议:
"""
        
        # 根据不同周期给出建议
        if cycle == EconomicCycle.RECOVERY:
            report += """
- 逐步增加股票配置
- 关注周期性行业
- 适度配置债券以分散风险
"""
        elif cycle == EconomicCycle.EXPANSION:
            report += """
- 维持较高股票配置
- 关注成长型股票
- 适当增加商品配置
"""
        elif cycle == EconomicCycle.PEAK:
            report += """
- 逐步降低股票配置
- 增加防御性行业
- 提高现金和债券比例
"""
        elif cycle == EconomicCycle.CONTRACTION:
            report += """
- 降低股票配置至最低
- 增加债券和现金配置
- 关注抗周期性行业
"""
        else:  # TROUGH
            report += """
- 准备逐步增加股票配置
- 关注被低估的优质资产
- 保持充足现金以把握机会
"""
        
        return report
