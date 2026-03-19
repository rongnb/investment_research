# -*- coding: utf-8 -*-
"""
数据采集器基类

定义数据采集的统一接口和公共方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
import logging
import time
from functools import wraps


logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """数据源类型"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"
    LOCAL = "local"


class IndicatorType(Enum):
    """宏观经济指标类型"""
    GDP = "gdp"                          # 国内生产总值
    GDP_YOY = "gdp_yoy"                  # GDP同比
    CPI = "cpi"                          # 消费者物价指数
    CPI_YOY = "cpi_yoy"                  # CPI同比
    PPI = "ppi"                          # 生产者物价指数
    PPI_YOY = "ppi_yoy"                  # PPI同比
    PMI = "pmi"                          # 采购经理指数
    MANUFACTURING_PMI = "manufacturing_pmi"  # 制造业PMI
    NON_MANUFACTURING_PMI = "non_manufacturing_pmi"  # 非制造业PMI
    INTEREST_RATE = "interest_rate"      # 利率
    RESERVE_REQUIREMENT_RATIO = "rrr"    # 存款准备金率
    M2 = "m2"                            # 货币供应量M2
    M2_YOY = "m2_yoy"                    # M2同比
    SOCIAL_FINANCING = "social_financing"  # 社会融资规模
    UNEMPLOYMENT = "unemployment_rate"  # 失业率
    CONSUMER_CONFIDENCE = "consumer_confidence"  # 消费者信心指数
    INDUSTRIAL_OUTPUT = "industrial_output"  # 工业增加值
    FIXED_ASSET_INVESTMENT = "fixed_asset_investment"  # 固定资产投资
    RETAIL_SALES = "retail_sales"        # 社会消费品零售总额


@dataclass
class DataQuery:
    """数据查询条件"""
    indicator: IndicatorType
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    region: str = "china"       # 国家/地区
    source: Optional[DataSourceType] = None
    
    def to_cache_key(self) -> str:
        """生成缓存键"""
        return f"{self.indicator.value}_{self.start_date}_{self.end_date}_{self.frequency}_{self.region}"


@dataclass
class DataResponse:
    """数据响应"""
    success: bool
    data: Optional[pd.DataFrame] = None
    source: Optional[DataSourceType] = None
    query: Optional[DataQuery] = None
    error: Optional[str] = None
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "success": self.success,
            "data": self.data.to_dict() if self.data is not None else None,
            "source": self.source.value if self.source else None,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


class DataCollector(ABC):
    """
    数据采集器抽象基类
    
    定义数据采集的统一接口，所有数据源适配器都应继承此类
    """
    
    def __init__(self, source_type: DataSourceType):
        """
        初始化数据采集器
        
        Args:
            source_type: 数据源类型
        """
        self.source_type = source_type
        self.logger = logging.getLogger(f"{__name__}.{source_type.value}")
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化数据源连接"""
        self.logger.info(f"Initializing {self.source_type.value} collector")
    
    @abstractmethod
    def fetch_macro_indicator(
        self, 
        indicator: IndicatorType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取宏观经济指标数据
        
        Args:
            indicator: 指标类型
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 其他参数
            
        Returns:
            包含指标数据的DataFrame
        """
        pass
    
    @abstractmethod
    def fetch_stock_ohlc(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票OHLC数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型 (qfq/hfq/none)
            
        Returns:
            OHLC数据DataFrame
        """
        pass
    
    def test_connection(self) -> bool:
        """
        测试数据源连接
        
        Returns:
            连接是否正常
        """
        try:
            # 子类应重写此方法实现具体的连接测试
            self.logger.info(f"Testing connection for {self.source_type.value}")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_available_indicators(self) -> List[IndicatorType]:
        """
        获取数据源支持的指标列表
        
        Returns:
            支持的指标类型列表
        """
        # 子类可以重写此方法
        return list(IndicatorType)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.source_type.value})"