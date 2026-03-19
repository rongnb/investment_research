"""
个股筛选模块 - 多因子选股系统核心
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from ..common.models import Factor, FactorType, ScreeningResult
from ..common.exceptions import ScreeningError, FactorError
from .factors import FundamentalFactors, TechnicalFactors


@dataclass
class FilterCondition:
    """筛选条件"""
    factor_code: str
    operator: str  # '>', '<', '>=', '<=', '==', 'between', 'in'
    value: Any
    value2: Any = None  # 用于between操作
    weight: float = 1.0


@dataclass
class ScreeningCriteria:
    """筛选标准配置"""
    name: str
    description: str
    conditions: List[FilterCondition] = field(default_factory=list)
    min_stocks: int = 10
    max_stocks: int = 100
    sort_by: str = "composite_score"
    ascending: bool = False


class StockScreener:
    """
    个股筛选器 - 多因子选股系统
    
    支持:
    - 基本面因子筛选
    - 技术面因子筛选
    - 多因子综合评分
    - 自定义筛选条件
    - 行业/板块过滤
    """
    
    def __init__(self, data_source: str = 'akshare'):
        """
        初始化筛选器
        
        Args:
            data_source: 数据源 ('akshare', 'tushare', 'baostock')
        """
        self.data_source = data_source
        self.fundamental_factors = FundamentalFactors()
        self.technical_factors = TechnicalFactors()
        self.criteria_library = self._init_criteria_library()
        
    def _init_criteria_library(self) -> Dict[str, ScreeningCriteria]:
        """初始化预设筛选标准库"""
        
        library = {}
        
        # 价值投资策略
        library['value'] = ScreeningCriteria(
            name='价值投资',
            description='选择低估值、高股息、稳定盈利的股票',
            conditions=[
                FilterCondition('pe_ttm', '<', 15),
                FilterCondition('pb', '<', 2),
                FilterCondition('roe', '>', 10),
                FilterCondition('dividend_yield', '>', 2),
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        # 成长投资策略
        library['growth'] = ScreeningCriteria(
            name='成长投资',
            description='选择高增长、创新能力强的股票',
            conditions=[
                FilterCondition('revenue_growth', '>', 20),
                FilterCondition('profit_growth', '>', 20),
                FilterCondition('roe', '>', 8),
                FilterCondition('pe_ttm', '<', 50),
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        # 质量投资策略
        library['quality'] = ScreeningCriteria(
            name='质量投资',
            description='选择高ROE、低负债、稳定盈利的优质公司',
            conditions=[
                FilterCondition('roe', '>', 15),
                FilterCondition('roa', '>', 8),
                FilterCondition('debt_ratio', '<', 50),
                FilterCondition('current_ratio', '>', 1.5),
                FilterCondition('interest_coverage', '>', 5),
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        # 技术面选股策略
        library['technical'] = ScreeningCriteria(
            name='技术突破',
            description='选择技术面强势、有突破迹象的股票',
            conditions=[
                FilterCondition('ma_trend', '==', 1),  # 均线多头排列
                FilterCondition('volume_ratio', '>', 1.5),  # 放量
                FilterCondition('macd_signal', '==', 1),  # MACD金叉或多头
                FilterCondition('rsi_14', 'between', 30, 70),  # RSI在中性区上方
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        # 小盘成长股策略
        library['small_cap_growth'] = ScreeningCriteria(
            name='小盘成长',
            description='选择小市值、高成长、低估值的股票',
            conditions=[
                FilterCondition('market_cap', '<', 5000000000),  # 市值小于50亿
                FilterCondition('revenue_growth', '>', 30),
                FilterCondition('profit_growth', '>', 30),
                FilterCondition('pe_ttm', '<', 40),
                FilterCondition('pb', '<', 3),
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        # 分红型策略
        library['dividend'] = ScreeningCriteria(
            name='高分红',
            description='选择高分红、稳定分红、低估值的股票',
            conditions=[
                FilterCondition('dividend_yield', '>', 3),
                FilterCondition('dividend_payout_ratio', 'between', 30, 70),
                FilterCondition('roe', '>', 8),
                FilterCondition('debt_ratio', '<', 60),
                FilterCondition('pe_ttm', '<', 20),
            ],
            min_stocks=10,
            max_stocks=50,
            sort_by='composite_score',
            ascending=False
        )
        
        return library
    
    def screen(self, 
               criteria: Union[str, ScreeningCriteria],
               stock_pool: Optional[List[str]] = None,
               date: Optional[str] = None) -> ScreeningResult:
        """
        执行股票筛选
        
        Args:
            criteria: 筛选标准名称或对象
            stock_pool: 股票池，None表示全市场
            date: 筛选日期，None表示当前日期
            
        Returns:
            筛选结果
        """
        # 获取筛选标准
        if isinstance(criteria, str):
            if criteria not in self.criteria_library:
                raise ScreeningError(f"未知的筛选标准: {criteria}")
            criteria = self.criteria_library[criteria]
        
        # 获取股票数据
        data = self._fetch_stock_data(stock_pool, date)
        
        # 应用筛选条件
        filtered_data = self._apply_conditions(data, criteria.conditions)
        
        # 计算综合评分
        scored_data = self._calculate_scores(filtered_data, criteria.conditions)
        
        # 排序并限制数量
        final_result = scored_data.sort_values(
            by=criteria.sort_by,
            ascending=criteria.ascending
        ).head(criteria.max_stocks)
        
        # 组装结果
        result = ScreeningResult(
            timestamp=datetime.now(),
            total_stocks=len(data),
            filtered_stocks=len(filtered_data),
            ranked_stocks=final_result.to_dict('records'),
            factors_used=[cond.factor_code for cond in criteria.conditions],
            weights={cond.factor_code: cond.weight for cond in criteria.conditions}
        )
        
        return result
    
    def _fetch_stock_data(self, stock_pool: Optional[List[str]], date: Optional[str]) -> pd.DataFrame:
        """获取股票数据"""
        # 这里需要根据数据源实现
        # 暂时返回模拟数据
        pass
    
    def _apply_conditions(self, data: pd.DataFrame, conditions: List[FilterCondition]) -> pd.DataFrame:
        """应用筛选条件"""
        filtered = data.copy()
        
        for condition in conditions:
            factor_code = condition.factor_code
            operator = condition.operator
            value = condition.value
            
            if factor_code not in filtered.columns:
                continue
            
            if operator == '>':
                filtered = filtered[filtered[factor_code] > value]
            elif operator == '<':
                filtered = filtered[filtered[factor_code] < value]
            elif operator == '>=':
                filtered = filtered[filtered[factor_code] >= value]
            elif operator == '<=':
                filtered = filtered[filtered[factor_code] <= value]
            elif operator == '==':
                filtered = filtered[filtered[factor_code] == value]
            elif operator == 'between':
                value2 = condition.value2 or value
                filtered = filtered[
                    (filtered[factor_code] >= value) & 
                    (filtered[factor_code] <= value2)
                ]
            elif operator == 'in':
                if isinstance(value, (list, tuple)):
                    filtered = filtered[filtered[factor_code].isin(value)]
        
        return filtered
    
    def _calculate_scores(self, data: pd.DataFrame, conditions: List[FilterCondition]) -> pd.DataFrame:
        """计算综合评分"""
        scored = data.copy()
        
        # 初始化评分列
        scored['composite_score'] = 0.0
        
        total_weight = sum(cond.weight for cond in conditions)
        
        for condition in conditions:
            factor_code = condition.factor_code
            weight = condition.weight / total_weight if total_weight > 0 else 0
            
            if factor_code not in scored.columns:
                continue
            
            # 因子标准化 (0-1)
            factor_values = scored[factor_code]
            min_val = factor_values.min()
            max_val = factor_values.max()
            
            if max_val > min_val:
                normalized = (factor_values - min_val) / (max_val - min_val)
            else:
                normalized = pd.Series(0.5, index=factor_values.index)
            
            # 根据因子方向调整 (这里假设所有因子都是正向)
            scored['composite_score'] += normalized * weight
        
        return scored
