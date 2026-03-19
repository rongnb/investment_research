# -*- coding: utf-8 -*-
"""
选股因子定义
支持基本面因子、技术面因子、情绪面因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class FactorType(Enum):
    """因子类型"""
    FUNDAMENTAL = "基本面"
    TECHNICAL = "技术面"
    SENTIMENT = "情绪面"
    QUALITY = "质量因子"
    VALUE = "价值因子"
    GROWTH = "成长因子"

@dataclass
class Factor:
    """因子定义"""
    name: str
    code: str
    factor_type: FactorType
    description: str
    calculation: Callable
    direction: int = 1  # 1: 正向 (越大越好), -1: 反向 (越小越好)
    
class FundamentalFactors:
    """
    基本面因子
    从财务报表中提取的关键指标
    """
    
    def __init__(self):
        self.factors = self._define_factors()
    
    def _define_factors(self) -> Dict[str, Factor]:
        """定义所有基本面因子"""
        
        factors = {
            # 估值因子
            'pe_ttm': Factor(
                name='市盈率TTM',
                code='pe_ttm',
                factor_type=FactorType.VALUE,
                description='市盈率（滚动12个月），估值越低越有吸引力',
                calculation=self._calc_pe_ttm,
                direction=-1  # 越小越好
            ),
            
            'pb': Factor(
                name='市净率',
                code='pb',
                factor_type=FactorType.VALUE,
                description='市净率，衡量股价与净资产的关系',
                calculation=self._calc_pb,
                direction=-1
            ),
            
            'ps_ttm': Factor(
                name='市销率TTM',
                code='ps_ttm',
                factor_type=FactorType.VALUE,
                description='市销率，适用于亏损企业估值',
                calculation=self._calc_ps_ttm,
                direction=-1
            ),
            
            'dividend_yield': Factor(
                name='股息率',
                code='dividend_yield',
                factor_type=FactorType.VALUE,
                description='股息率，衡量现金分红回报',
                calculation=self._calc_dividend_yield,
                direction=1  # 越大越好
            ),
            
            'peg': Factor(
                name='PEG比率',
                code='peg',
                factor_type=FactorType.VALUE,
                description='市盈率相对盈利增长比率',
                calculation=self._calc_peg,
                direction=-1
            ),
            
            # 盈利质量因子
            'roe': Factor(
                name='净资产收益率',
                code='roe',
                factor_type=FactorType.QUALITY,
                description='ROE，衡量股东权益回报率',
                calculation=self._calc_roe,
                direction=1
            ),
            
            'roa': Factor(
                name='总资产收益率',
                code='roa',
                factor_type=FactorType.QUALITY,
                description='ROA，衡量资产使用效率',
                calculation=self._calc_roa,
                direction=1
            ),
            
            'roic': Factor(
                name='投入资本回报率',
                code='roic',
                factor_type=FactorType.QUALITY,
                description='ROIC，衡量资本配置效率',
                calculation=self._calc_roic,
                direction=1
            ),
            
            'gross_profit_margin': Factor(
                name='毛利率',
                code='gross_profit_margin',
                factor_type=FactorType.QUALITY,
                description='毛利率，衡量产品竞争力',
                calculation=self._calc_gross_profit_margin,
                direction=1
            ),
            
            'net_profit_margin': Factor(
                name='净利率',
                code='net_profit_margin',
                factor_type=FactorType.QUALITY,
                description='净利率，衡量最终盈利能力',
                calculation=self._calc_net_profit_margin,
                direction=1
            ),
            
            # 成长性因子
            'revenue_growth': Factor(
                name='营收增长率',
                code='revenue_growth',
                factor_type=FactorType.GROWTH,
                description='营业收入同比增长率',
                calculation=self._calc_revenue_growth,
                direction=1
            ),
            
            'profit_growth': Factor(
                name='净利润增长率',
                code='profit_growth',
                factor_type=FactorType.GROWTH,
                description='净利润同比增长率',
                calculation=self._calc_profit_growth,
                direction=1
            ),
            
            'eps_growth': Factor(
                name='每股收益增长率',
                code='eps_growth',
                factor_type=FactorType.GROWTH,
                description='EPS同比增长率',
                calculation=self._calc_eps_growth,
                direction=1
            ),
            
            'roe_growth': Factor(
                name='ROE增长率',
                code='roe_growth',
                factor_type=FactorType.GROWTH,
                description='ROE同比变化',
                calculation=self._calc_roe_growth,
                direction=1
            ),
            
            # 财务健康因子
            'debt_ratio': Factor(
                name='资产负债率',
                code='debt_ratio',
                factor_type=FactorType.QUALITY,
                description='资产负债率，衡量财务风险',
                calculation=self._calc_debt_ratio,
                direction=-1  # 越低越好
            ),
            
            'current_ratio': Factor(
                name='流动比率',
                code='current_ratio',
                factor_type=FactorType.QUALITY,
                description='流动比率，衡量短期偿债能力',
                calculation=self._calc_current_ratio,
                direction=1
            ),
            
            'quick_ratio': Factor(
                name='速动比率',
                code='quick_ratio',
                factor_type=FactorType.QUALITY,
                description='速动比率，更严格的短期偿债指标',
                calculation=self._calc_quick_ratio,
                direction=1
            ),
            
            'cash_ratio': Factor(
                name='现金比率',
                code='cash_ratio',
                factor_type=FactorType.QUALITY,
                description='现金比率，最严格的流动性指标',
                calculation=self._calc_cash_ratio,
                direction=1
            ),
            
            'interest_coverage': Factor(
                name='利息保障倍数',
                code='interest_coverage',
                factor_type=FactorType.QUALITY,
                description='利息保障倍数，衡量偿付利息能力',
                calculation=self._calc_interest_coverage,
                direction=1
            ),
            
            # 运营效率因子
            'asset_turnover': Factor(
                name='总资产周转率',
                code='asset_turnover',
                factor_type=FactorType.QUALITY,
                description='总资产周转率，衡量资产使用效率',
                calculation=self._calc_asset_turnover,
                direction=1
            ),
            
            'inventory_turnover': Factor(
                name='存货周转率',
                code='inventory_turnover',
                factor_type=FactorType.QUALITY,
                description='存货周转率，衡量存货管理效率',
                calculation=self._calc_inventory_turnover,
                direction=1
            ),
            
            'receivables_turnover': Factor(
                name='应收账款周转率',
                code='receivables_turnover',
                factor_type=FactorType.QUALITY,
                description='应收账款周转率，衡量收款效率',
                calculation=self._calc_receivables_turnover,
                direction=1
            ),
            
            'cash_conversion_cycle': Factor(
                name='现金转换周期',
                code='cash_conversion_cycle',
                factor_type=FactorType.QUALITY,
                description='现金转换周期，衡量运营资金效率',
                calculation=self._calc_cash_conversion_cycle,
                direction=-1  # 越短越好
            ),
            
            # 市场行为因子
            'beta': Factor(
                name='Beta系数',
                code='beta',
                factor_type=FactorType.TECHNICAL,
                description='Beta系数，衡量系统性风险',
                calculation=self._calc_beta,
                direction=-1  # 越低越好（低风险）
            ),
            
            'alpha': Factor(
                name='Alpha超额收益',
                code='alpha',
                factor_type=FactorType.TECHNICAL,
                description='Alpha超额收益，衡量选股能力',
                calculation=self._calc_alpha,
                direction=1
            ),
            
            'sharpe_ratio': Factor(
                name='夏普比率',
                code='sharpe_ratio',
                factor_type=FactorType.TECHNICAL,
                description='夏普比率，衡量风险调整后收益',
                calculation=self._calc_sharpe_ratio,
                direction=1
            ),
            
            'sortino_ratio': Factor(
                name='索提诺比率',
                code='sortino_ratio',
                factor_type=FactorType.TECHNICAL,
                description='索提诺比率，更关注下行风险',
                calculation=self._calc_sortino_ratio,
                direction=1
            ),
            
            'max_drawdown': Factor(
                name='最大回撤',
                code='max_drawdown',
                factor_type=FactorType.TECHNICAL,
                description='最大回撤，衡量极端风险',
                calculation=self._calc_max_drawdown,
                direction=-1  # 越小越好
            ),
            
            'volatility': Factor(
                name='波动率',
                code='volatility',
                factor_type=FactorType.TECHNICAL,
                description='波动率，衡量价格变动幅度',
                calculation=self._calc_volatility,
                direction=-1  # 越低越好
            ),
            
            # 质量综合因子
            'quality_score': Factor(
                name='质量综合评分',
                code='quality_score',
                factor_type=FactorType.QUALITY,
                description='综合质量评分，整合ROE、ROA、盈利稳定性等',
                calculation=self._calc_quality_score,
                direction=1
            ),
            
            'profit_stability': Factor(
                name='盈利稳定性',
                code='profit_stability',
                factor_type=FactorType.QUALITY,
                description='盈利稳定性，衡量盈利波动性',
                calculation=self._calc_profit_stability,
                direction=1
            ),
            
            'earnings_consistency': Factor(
                name='盈利持续性',
                code='earnings_consistency',
                factor_type=FactorType.QUALITY,
                description='盈利持续性，连续盈利季度数',
                calculation=self._calc_earnings_consistency,
                direction=1
            ),
        }
        
        return factors
    
    # ===== 估值因子计算方法 =====
    
    def _calc_pe_ttm(self, data: pd.DataFrame) -> pd.Series:
        """计算市盈率TTM"""
        return data['market_cap'] / data['net_profit_ttm']
    
    def _calc_pb(self, data: pd.DataFrame) -> pd.Series:
        """计算市净率"""
        return data['market_cap'] / data['net_assets']
    
    def _calc_ps_ttm(self, data: pd.DataFrame) -> pd.Series:
        """计算市销率TTM"""
        return data['market_cap'] / data['revenue_ttm']
    
    def _calc_dividend_yield(self, data: pd.DataFrame) -> pd.Series:
        """计算股息率"""
        return data['dividend_ttm'] / data['market_cap']
    
    def _calc_peg(self, data: pd.DataFrame) -> pd.Series:
        """计算PEG比率"""
        pe = self._calc_pe_ttm(data)
        growth_rate = data['profit_growth_rate']
        return pe / growth_rate.replace(0, np.nan)
    
    # ===== 盈利质量因子计算方法 =====
    
    def _calc_roe(self, data: pd.DataFrame) -> pd.Series:
        """计算净资产收益率ROE"""
        return data['net_profit_ttm'] / data['net_assets']
    
    def _calc_roa(self, data: pd.DataFrame) -> pd.Series:
        """计算总资产收益率ROA"""
        return data['net_profit_ttm'] / data['total_assets']
    
    def _calc_roic(self, data: pd.DataFrame) -> pd.Series:
        """计算投入资本回报率ROIC"""
        nopat = data['net_profit_ttm'] + data['interest_expense'] * (1 - 0.25)
        invested_capital = data['total_assets'] - data['current_liabilities']
        return nopat / invested_capital
    
    def _calc_gross_profit_margin(self, data: pd.DataFrame) -> pd.Series:
        """计算毛利率"""
        return data['gross_profit_ttm'] / data['revenue_ttm']
    
    def _calc_net_profit_margin(self, data: pd.DataFrame) -> pd.Series:
        """计算净利率"""
        return data['net_profit_ttm'] / data['revenue_ttm']
    
    # ===== 成长性因子计算方法 =====
    
    def _calc_revenue_growth(self, data: pd.DataFrame) -> pd.Series:
        """计算营收增长率"""
        return (data['revenue_ttm'] - data['revenue_ttm_lag']) / data['revenue_ttm_lag']
    
    def _calc_profit_growth(self, data: pd.DataFrame) -> pd.Series:
        """计算净利润增长率"""
        return (data['net_profit_ttm'] - data['net_profit_ttm_lag']) / data['net_profit_ttm_lag']
    
    def _calc_eps_growth(self, data: pd.DataFrame) -> pd.Series:
        """计算每股收益增长率"""
        return (data['eps_ttm'] - data['eps_ttm_lag']) / data['eps_ttm_lag']
    
    def _calc_roe_growth(self, data: pd.DataFrame) -> pd.Series:
        """计算ROE增长率"""
        return (data['roe_ttm'] - data['roe_ttm_lag']) / data['roe_ttm_lag']
    
    # ===== 财务健康因子计算方法 =====
    
    def _calc_debt_ratio(self, data: pd.DataFrame) -> pd.Series:
        """计算资产负债率"""
        return data['total_liabilities'] / data['total_assets']
    
    def _calc_current_ratio(self, data: pd.DataFrame) -> pd.Series:
        """计算流动比率"""
        return data['current_assets'] / data['current_liabilities']
    
    def _calc_quick_ratio(self, data: pd.DataFrame) -> pd.Series:
        """计算速动比率"""
        quick_assets = data['current_assets'] - data['inventory']
        return quick_assets / data['current_liabilities']
    
    def _calc_cash_ratio(self, data: pd.DataFrame) -> pd.Series:
        """计算现金比率"""
        return data['cash_and_equivalents'] / data['current_liabilities']
    
    def _calc_interest_coverage(self, data: pd.DataFrame) -> pd.Series:
        """计算利息保障倍数"""
        ebit = data['operating_profit'] + data['interest_expense']
        return ebit / data['interest_expense']
    
    # ===== 运营效率因子计算方法 =====
    
    def _calc_asset_turnover(self, data: pd.DataFrame) -> pd.Series:
        """计算总资产周转率"""
        return data['revenue_ttm'] / data['total_assets']
    
    def _calc_inventory_turnover(self, data: pd.DataFrame) -> pd.Series:
        """