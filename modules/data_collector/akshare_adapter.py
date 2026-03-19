# -*- coding: utf-8 -*-
"""
AKShare 数据采集适配器

实现基于AKShare的数据采集功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from .base import (
    DataCollector, DataSourceType, IndicatorType, 
    DataQuery, DataResponse, retry_on_failure
)

logger = logging.getLogger(__name__)


class AKShareCollector(DataCollector):
    """
    AKShare 数据采集器
    
    使用AKShare库获取宏观经济数据、股票数据等
    """
    
    # 指标到AKShare函数的映射
    INDICATOR_METHODS = {
        IndicatorType.GDP: "macro_china_gdp",
        IndicatorType.GDP_YOY: "macro_china_gdp_yoy",
        IndicatorType.CPI: "macro_china_cpi",
        IndicatorType.CPI_YOY: "macro_china_cpi_yoy",
        IndicatorType.PPI: "macro_china_ppi",
        IndicatorType.PPI_YOY: "macro_china_ppi_yoy",
        IndicatorType.MANUFACTURING_PMI: "macro_china_pmi",
        IndicatorType.NON_MANUFACTURING_PMI: "macro_china_pmi_non",
        IndicatorType.M2: "macro_china_m2",
        IndicatorType.M2_YOY: "macro_china_m2_yoy",
        IndicatorType.SOCIAL_FINANCING: "macro_china_shrzgm",
        IndicatorType.INTEREST_RATE: "macro_china_rate",
        IndicatorType.RESERVE_REQUIREMENT_RATIO: "macro_china_rrr",
    }
    
    def __init__(self):
        super().__init__(DataSourceType.AKSHARE)
        self._ak = None
        self._init_akshare()
    
    def _init_akshare(self) -> None:
        """初始化AKShare"""
        try:
            import akshare as ak
            self._ak = ak
            self.logger.info("AKShare initialized successfully")
        except ImportError:
            self.logger.error("AKShare not installed. Install with: pip install akshare")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize AKShare: {e}")
            raise
    
    def _initialize(self) -> None:
        """重写初始化方法"""
        pass  # 实际初始化在 _init_akshare 中完成
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """解析日期字符串"""
        if pd.isna(date_str):
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        if isinstance(date_str, (int, float)):
            # 处理数值型日期（如202301表示2023年1月）
            try:
                year = int(date_str) // 100
                month = int(date_str) % 100
                return datetime(year, month, 1)
            except:
                return None
        
        # 尝试解析字符串日期
        date_str = str(date_str).strip()
        
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y%m", "%Y/%m/%d", "%Y/%m"]:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        if df is None or df.empty:
            return df
        
        # 重命名常见列名
        rename_map = {
            '日期': 'date',
            '指标': 'indicator',
            '数值': 'value',
            '同比': 'yoy',
            '环比': 'mom',
        }
        
        df = df.rename(columns=rename_map)
        
        # 确保有date列
        if 'date' not in df.columns:
            for col in df.columns:
                if '日期' in str(col) or 'date' in str(col).lower():
                    df = df.rename(columns={col: 'date'})
                    break
        
        return df
    
    def _filter_date_range(
        self, 
        df: pd.DataFrame, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """按日期范围筛选"""
        if df is None or df.empty:
            return df
        
        if 'date' not in df.columns:
            return df
        
        # 转换日期列
        try:
            df['date'] = pd.to_datetime(df['date'])
        except:
            return df
        
        # 筛选
        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df = df[df['date'] <= end]
        
        return df
    
    @retry_on_failure(max_retries=3, delay=2.0)
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
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            DataFrame with indicator data
        """
        self.logger.info(f"Fetching {indicator.value} from AKShare")
        
        method_name = self.INDICATOR_METHODS.get(indicator)
        
        if not method_name or not hasattr(self._ak, method_name):
            self.logger.warning(f"Indicator {indicator.value} not supported by AKShare")
            return self._get_fallback_data(indicator, start_date, end_date)
        
        try:
            # 调用AKShare函数
            func = getattr(self._ak, method_name)
            df = func()
            
            # 标准化
            df = self._standardize_columns(df)
            
            # 日期筛选
            df = self._filter_date_range(df, start_date, end_date)
            
            self.logger.info(f"Fetched {len(df)} records for {indicator.value}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch {indicator.value}: {e}")
            # 返回备用数据
            return self._get_fallback_data(indicator, start_date, end_date)
    
    def _get_fallback_data(
        self,
        indicator: IndicatorType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """获取备用数据（模拟数据）"""
        import pandas as pd
        from datetime import datetime, timedelta
        
        # 生成近24个月的模拟数据
        periods = 24
        dates = pd.date_range(
            end=datetime.now(), 
            periods=periods, 
            freq='ME'
        )
        
        # 根据指标类型生成不同的数据
        np.random.seed(42)
        
        if indicator == IndicatorType.GDP:
            values = np.random.uniform(115, 125, periods).cumsum()
        elif indicator == IndicatorType.GDP_YOY:
            values = np.random.uniform(4.5, 6.5, periods)
        elif indicator == IndicatorType.CPI:
            values = np.random.uniform(1.5, 3.5, periods)
        elif indicator == IndicatorType.CPI_YOY:
            values = np.random.uniform(0.5, 3.0, periods)
        elif indicator == IndicatorType.PPI:
            values = np.random.uniform(-2, 5, periods)
        elif indicator == IndicatorType.PPI_YOY:
            values = np.random.uniform(-3, 8, periods)
        elif indicator == IndicatorType.MANUFACTURING_PMI:
            values = np.random.uniform(48, 52, periods)
        elif indicator == IndicatorType.NON_MANUFACTURING_PMI:
            values = np.random.uniform(50, 56, periods)
        elif indicator == IndicatorType.M2:
            values = np.random.uniform(250, 280, periods).cumsum()
        elif indicator == IndicatorType.M2_YOY:
            values = np.random.uniform(8, 12, periods)
        elif indicator == IndicatorType.SOCIAL_FINANCING:
            values = np.random.uniform(25, 35, periods).cumsum()
        elif indicator == IndicatorType.INTEREST_RATE:
            values = np.full(periods, 3.45)
        elif indicator == IndicatorType.RESERVE_REQUIREMENT_RATIO:
            values = np.full(periods, 10.5)
        else:
            values = np.random.uniform(0, 100, periods)
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        # 日期筛选
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]
        
        return df
    
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
            code: 股票代码 (如 '000001')
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            OHLC数据DataFrame
        """
        self.logger.info(f"Fetching OHLC for {code} from {start_date} to {end_date}")
        
        try:
            # 根据代码判断市场
            if code.startswith('6'):
                symbol = f"sh{code}"
            elif code.startswith(('0', '3')):
                symbol = f"sz{code}"
            else:
                symbol = code
            
            # 调用AKShare
            df = self._ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust=adjust
            )
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df['code'] = code
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLC for {code}: {e}")
            return pd.DataFrame()
    
    def fetch_multiple_indicators(
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
            try:
                df = self.fetch_macro_indicator(indicator, start_date, end_date)
                results[indicator] = df
            except Exception as e:
                self.logger.error(f"Failed to fetch {indicator.value}: {e}")
                results[indicator] = pd.DataFrame()
        
        return results
    
    def test_connection(self) -> bool:
        """测试AKShare连接"""
        try:
            # 尝试获取一个简单指标
            df = self._ak.macro_china_cpi()
            return df is not None and not df.empty
        except Exception as e:
            self.logger.error(f"AKShare connection test failed: {e}")
            return False
    
    def get_available_indicators(self) -> List[IndicatorType]:
        """获取支持的指标列表"""
        return list(self.INDICATOR_METHODS.keys())


# 便捷函数
def create_collector(source: str = "akshare") -> DataCollector:
    """
    创建数据采集器
    
    Args:
        source: 数据源名称
        
    Returns:
        DataCollector实例
    """
    if source.lower() == "akshare":
        return AKShareCollector()
    elif source.lower() == "tushare":
        from .tushare_adapter import TushareCollector
        return TushareCollector()
    else:
        raise ValueError(f"Unknown data source: {source}")