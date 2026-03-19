# -*- coding: utf-8 -*-
"""
宏观经济指标采集模块

从多数据源获取经济指标数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..data_collector import AKShareCollector, TushareCollector, DataCache, DataQuery
from ..data_collector.base import IndicatorType, DataSourceType
from .base import EconomicIndicators

logger = logging.getLogger(__name__)


class IndicatorSource(Enum):
    """指标数据源优先级"""
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    LOCAL = "local"


@dataclass
class IndicatorConfig:
    """指标配置"""
    indicator: IndicatorType
    name_cn: str
    name_en: str
    unit: str
    frequency: str  # daily/weekly/monthly/quarterly
    primary_source: IndicatorSource
    description: str = ""


# 指标配置映射
INDICATOR_CONFIGS = {
    IndicatorType.GDP: IndicatorConfig(
        indicator=IndicatorType.GDP,
        name_cn="国内生产总值",
        name_en="GDP",
        unit="万亿元",
        frequency="quarterly",
        primary_source=IndicatorSource.AKSHARE,
        description="反映一定时期内国民经济最终产出的市场价值"
    ),
    IndicatorType.GDP_YOY: IndicatorConfig(
        indicator=IndicatorType.GDP_YOY,
        name_cn="GDP同比增长率",
        name_en="GDP YoY Growth",
        unit="%",
        frequency="quarterly",
        primary_source=IndicatorSource.AKSHARE,
        description="国内生产总值同比增长率"
    ),
    IndicatorType.CPI: IndicatorConfig(
        indicator=IndicatorType.CPI,
        name_cn="居民消费价格指数",
        name_en="CPI",
        unit="指数",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="反映居民生活消费品和服务价格水平变动情况"
    ),
    IndicatorType.CPI_YOY: IndicatorConfig(
        indicator=IndicatorType.CPI_YOY,
        name_cn="CPI同比",
        name_en="CPI YoY",
        unit="%",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="消费者物价指数同比变化率"
    ),
    IndicatorType.PPI: IndicatorConfig(
        indicator=IndicatorType.PPI,
        name_cn="工业生产者出厂价格指数",
        name_en="PPI",
        unit="指数",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="反映工业企业产品出厂价格变动趋势"
    ),
    IndicatorType.PPI_YOY: IndicatorConfig(
        indicator=IndicatorType.PPI_YOY,
        name_cn="PPI同比",
        name_en="PPI YoY",
        unit="%",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="工业生产者出厂价格指数同比变化率"
    ),
    IndicatorType.MANUFACTURING_PMI: IndicatorConfig(
        indicator=IndicatorType.MANUFACTURING_PMI,
        name_cn="制造业采购经理指数",
        name_en="Manufacturing PMI",
        unit="指数",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="反映制造业经济运行状况的综合指数"
    ),
    IndicatorType.NON_MANUFACTURING_PMI: IndicatorConfig(
        indicator=IndicatorType.NON_MANUFACTURING_PMI,
        name_cn="非制造业采购经理指数",
        name_en="Non-Manufacturing PMI",
        unit="指数",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="反映非制造业经济运行状况的综合指数"
    ),
    IndicatorType.M2: IndicatorConfig(
        indicator=IndicatorType.M2,
        name_cn="广义货币M2",
        name_en="M2 Money Supply",
        unit="万亿元",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="广义货币供应量，包括流通现金和存款"
    ),
    IndicatorType.M2_YOY: IndicatorConfig(
        indicator=IndicatorType.M2_YOY,
        name_cn="M2同比",
        name_en="M2 YoY",
        unit="%",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="广义货币供应量同比增长率"
    ),
    IndicatorType.SOCIAL_FINANCING: IndicatorConfig(
        indicator=IndicatorType.SOCIAL_FINANCING,
        name_cn="社会融资规模",
        name_en="Total Social Financing",
        unit="亿元",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="实体经济从金融体系获得的资金总额"
    ),
    IndicatorType.INTEREST_RATE: IndicatorConfig(
        indicator=IndicatorType.INTEREST_RATE,
        name_cn="贷款市场报价利率",
        name_en="LPR",
        unit="%",
        frequency="daily",
        primary_source=IndicatorSource.AKSHARE,
        description="贷款市场报价利率"
    ),
    IndicatorType.RESERVE_REQUIREMENT_RATIO: IndicatorConfig(
        indicator=IndicatorType.RESERVE_REQUIREMENT_RATIO,
        name_cn="存款准备金率",
        name_en="RRR",
        unit="%",
        frequency="monthly",
        primary_source=IndicatorSource.AKSHARE,
        description="金融机构存款准备金率"
    ),
}


class MacroIndicatorCollector:
    """
    宏观经济指标采集器
    
    统一采集接口，支持多数据源和缓存
    """
    
    def __init__(
        self,
        primary_source: str = "akshare",
        use_cache: bool = True,
        cache_ttl: int = 86400
    ):
        """
        初始化采集器
        
        Args:
            primary_source: 主数据源
            use_cache: 是否使用缓存
            cache_ttl: 缓存过期时间（秒）
        """
        self.primary_source = primary_source.lower()
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        
        # 初始化数据采集器
        if self.primary_source == "akshare":
            self.collector = AKShareCollector()
        elif self.primary_source == "tushare":
            self.collector = TushareCollector()
        else:
            self.collector = AKShareCollector()
        
        # 初始化缓存
        if use_cache:
            self.cache = DataCache(default_ttl=cache_ttl)
        else:
            self.cache = None
        
        # 指标配置
        self.configs = INDICATOR_CONFIGS
        
        logger.info(f"MacroIndicatorCollector initialized with {self.primary_source}")
    
    def fetch_indicator(
        self,
        indicator: IndicatorType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: Optional[bool] = None
    ) -> pd.DataFrame:
        """
        获取单个指标数据
        
        Args:
            indicator: 指标类型
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 覆盖缓存设置
            
        Returns:
            DataFrame
        """
        use_cache = use_cache if use_cache is not None else self.use_cache
        
        # 构建查询
        query = DataQuery(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date
        )
        
        # 尝试从缓存获取
        if use_cache and self.cache:
            cached = self.cache.get(query)
            if cached and cached.data is not None:
                logger.info(f"Cache hit for {indicator.value}")
                return cached.data
        
        # 从数据源获取
        try:
            df = self.collector.fetch_macro_indicator(
                indicator, start_date, end_date
            )
            
            # 存入缓存
            if use_cache and self.cache and df is not None and not df.empty:
                self.cache.set(query, df, self.cache_ttl)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch {indicator.value}: {e}")
            return pd.DataFrame()
    
    def fetch_multiple(
        self,
        indicators: List[IndicatorType],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[IndicatorType, pd.DataFrame]:
        """
        批量获取多个指标
        
        Args:
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指标到数据的映射
        """
        results = {}
        
        for indicator in indicators:
            df = self.fetch_indicator(indicator, start_date, end_date)
            results[indicator] = df
        
        return results
    
    def fetch_latest_indicators(
        self,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        获取最新指标值
        
        Args:
            months: 获取最近几个月的数据
            
        Returns:
            最新指标值字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # 核心指标列表
        key_indicators = [
            IndicatorType.GDP_YOY,
            IndicatorType.CPI_YOY,
            IndicatorType.PPI_YOY,
            IndicatorType.MANUFACTURING_PMI,
            IndicatorType.M2_YOY,
            IndicatorType.INTEREST_RATE,
        ]
        
        result = {}
        
        for indicator in key_indicators:
            df = self.fetch_indicator(indicator, start_str, end_str)
            
            if df is not None and not df.empty and 'value' in df.columns:
                latest = df.iloc[-1]
                result[indicator.value] = {
                    "value": float(latest['value']),
                    "date": str(latest.get('date', ''))
                }
        
        return result
    
    def get_economic_indicators(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> EconomicIndicators:
        """
        获取完整的经济指标对象
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            EconomicIndicators对象
        """
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = start_date or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # 获取最新数据
        gdp_yoy = self.fetch_indicator(IndicatorType.GDP_YOY, start_date, end_date)
        cpi = self.fetch_indicator(IndicatorType.CPI_YOY, start_date, end_date)
        ppi = self.fetch_indicator(IndicatorType.PPI_YOY, start_date, end_date)
        pmi = self.fetch_indicator(IndicatorType.MANUFACTURING_PMI, start_date, end_date)
        m2 = self.fetch_indicator(IndicatorType.M2_YOY, start_date, end_date)
        
        # 提取最新值
        def get_latest_value(df: pd.DataFrame) -> float:
            if df is not None and not df.empty and 'value' in df.columns:
                return float(df.iloc[-1]['value'])
            return 0.0
        
        # 获取LPR利率（需要单独处理）
        interest_rate = 3.45  # 默认值
        try:
            rate_df = self.fetch_indicator(IndicatorType.INTEREST_RATE, start_date, end_date)
            if rate_df is not None and not rate_df.empty:
                interest_rate = get_latest_value(rate_df)
        except:
            pass
        
        return EconomicIndicators(
            gdp_growth=get_latest_value(gdp_yoy),
            cpi=get_latest_value(cpi),
            ppi=get_latest_value(ppi),
            interest_rate=interest_rate,
            unemployment_rate=5.2,  # 需要单独接口
            money_supply=get_latest_value(m2),
            consumer_confidence=88.9,  # 需要单独接口
            manufacturing_pmi=get_latest_value(pmi)
        )
    
    def get_indicator_info(self, indicator: IndicatorType) -> Optional[IndicatorConfig]:
        """获取指标配置信息"""
        return self.configs.get(indicator)
    
    def list_available_indicators(self) -> List[IndicatorType]:
        """列出所有可用指标"""
        return list(self.configs.keys())
    
    def refresh_cache(self, indicator: Optional[IndicatorType] = None) -> bool:
        """
        刷新缓存
        
        Args:
            indicator: 指定指标（None表示全部）
            
        Returns:
            是否成功
        """
        if not self.cache:
            return False
        
        try:
            if indicator:
                self.cache.invalidate_by_indicator(indicator)
                logger.info(f"Cache invalidated for {indicator.value}")
            else:
                self.cache.clear_all()
                logger.info("All cache cleared")
            
            return True
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")
            return False
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """获取数据源状态"""
        status = {
            "primary_source": self.primary_source,
            "cache_enabled": self.use_cache,
            "collector_status": "unknown"
        }
        
        try:
            status["collector_status"] = "connected" if self.collector.test_connection() else "disconnected"
        except Exception as e:
            status["collector_status"] = f"error: {str(e)}"
        
        if self.cache:
            status["cache_stats"] = self.cache.get_stats()
        
        return status