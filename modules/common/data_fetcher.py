# -*- coding: utf-8 -*-
"""
数据获取器模块

实现Tushare和AKShare的数据获取功能，提供统一接口
包含错误处理、重试机制和数据质量检查
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from functools import wraps

import pandas as pd
import numpy as np

from .constants import (
    MACRO_INDICATORS,
    DEFAULT_RETRY_TIMES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_RATE_LIMIT
)
from .exceptions import (
    DataFetchError,
    ApiKeyError,
    RateLimitError,
    DataValidationError
)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = DEFAULT_RETRY_TIMES, 
                    delay: float = DEFAULT_RETRY_DELAY) -> Callable:
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError) as e:
                    # 遇到限流需要更长等待
                    last_exception = e
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            
            logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator


class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self):
        pass
    
    def check_integrity(self, df: pd.DataFrame, 
                       required_columns: List[str]) -> Tuple[bool, List[str]]:
        """
        检查数据完整性
        
        Args:
            df: 数据框
            required_columns: 必填列
            
        Returns:
            (是否通过, 问题列表)
        """
        issues = []
        
        # 检查是否为空
        if df.empty:
            issues.append("DataFrame is empty")
            return False, issues
        
        # 检查必填列
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
        
        # 检查缺失值
        null_counts = df[required_columns].isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                issues.append(f"Column '{col}' has {count} missing values")
        
        # 检查重复值
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate rows")
        
        return len(issues) == 0, issues
    
    def detect_outliers(self, df: pd.DataFrame, 
                       numeric_columns: List[str],
                       zscore_threshold: float = 3.0) -> Dict[str, int]:
        """
        检测异常值
        
        Args:
            df: 数据框
            numeric_columns: 数值列
            zscore_threshold: Z-score阈值
            
        Returns:
            异常值统计
        """
        outliers = {}
        
        for col in numeric_columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            
            # 使用Z-score检测异常值
            mean = df[col].mean()
            std = df[col].std()
            if std == 0:
                continue
            
            z_scores = np.abs((df[col] - mean) / std)
            outlier_count = (z_scores > zscore_threshold).sum()
            if outlier_count > 0:
                outliers[col] = outlier_count
        
        return outliers
    
    def clean_data(self, df: pd.DataFrame,
                   remove_duplicates: bool = True,
                   drop_missing: bool = False,
                   handle_outliers: str = "none") -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            df: 原始数据
            remove_duplicates: 是否移除重复
            drop_missing: 是否删除缺失值
            handle_outliers: 处理异常值方式: "none", "drop", "fill"
            
        Returns:
            清洗后的数据
        """
        cleaned = df.copy()
        
        # 移除重复
        if remove_duplicates:
            cleaned = cleaned.drop_duplicates(keep='first')
        
        # 删除缺失值
        if drop_missing:
            cleaned = cleaned.dropna(axis=0, how='any')
        
        # 处理异常值
        if handle_outliers != "none":
            numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
            outliers = self.detect_outliers(cleaned, list(numeric_cols))
            
            if outliers and handle_outliers == "drop":
                for col in outliers:
                    mean = cleaned[col].mean()
                    std = cleaned[col].std()
                    z_scores = np.abs((cleaned[col] - mean) / std)
                    cleaned = cleaned[z_scores <= 3.0]
            elif outliers and handle_outliers == "fill":
                for col in outliers:
                    mean = cleaned[col].mean()
                    std = cleaned[col].std()
                    z_scores = np.abs((cleaned[col] - mean) / std)
                    # 用中位数填充异常值
                    median = cleaned[col].median()
                    cleaned.loc[z_scores > 3.0, col] = median
        
        return cleaned
    
    def validate_date_range(self, df: pd.DataFrame, 
                           start_date: str, 
                           end_date: str,
                           date_col: str = "date") -> Tuple[bool, str]:
        """验证日期范围"""
        if date_col not in df.columns:
            return False, f"Date column '{date_col}' not found"
        
        dates = pd.to_datetime(df[date_col])
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        if dates.min() > start:
            return False, f"Data starts at {dates.min()}, expected after {start}"
        
        if dates.max() < end:
            return False, f"Data ends at {dates.max()}, expected before {end}"
        
        return True, ""


@dataclass
class FetchConfig:
    """数据获取配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    retry_times: int = DEFAULT_RETRY_TIMES
    retry_delay: float = DEFAULT_RETRY_DELAY
    max_requests_per_minute: int = 60
    cache_enabled: bool = True
    cache_expire_hours: int = 24


class BaseDataFetcher(ABC):
    """数据获取器基类"""
    
    def __init__(self, config: FetchConfig):
        self.config = config
        self.quality_checker = DataQualityChecker()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 限流相关
        self._request_timestamps: List[float] = []
        self._last_request_time = 0.0
        
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化数据源连接，子类可重写"""
        pass
    
    def _check_rate_limit(self) -> None:
        """检查并遵守限流"""
        now = time.time()
        
        # 清理1分钟前的请求记录
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60]
        
        if len(self._request_timestamps) >= self.config.max_requests_per_minute:
            # 需要等待
            oldest = self._request_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                # 重新检查
                self._request_timestamps = [t for t in self._request_timestamps if time.time() - t < 60]
        
        # 记录当前请求
        self._request_timestamps.append(now)
    
    @abstractmethod
    def fetch_stock_daily(self, symbol: str, 
                         start_date: str, 
                         end_date: str,
                         adjust: str = "qfq") -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 (qfq/hfq/none)
            
        Returns:
            日线数据DataFrame
        """
        pass
    
    @abstractmethod
    def fetch_stock_minute(self, symbol: str, 
                          period: str = "1min") -> pd.DataFrame:
        """
        获取股票分钟数据
        
        Args:
            symbol: 股票代码
            period: 周期 (1min/5min/15min/30min/60min)
            
        Returns:
            分钟数据DataFrame
        """
        pass
    
    @abstractmethod
    def fetch_index_daily(self, index_code: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据DataFrame
        """
        pass
    
    @abstractmethod
    def fetch_macro_indicator(self, indicator_code: str,
                             start_date: str,
                             end_date: str) -> pd.DataFrame:
        """
        获取宏观经济指标
        
        Args:
            indicator_code: 指标代码 (gdp, cpi, ppi, pmi等)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            宏观指标DataFrame
        """
        pass
    
    @abstractmethod
    def fetch_financial_report(self, symbol: str,
                               year: int,
                               report_type: str = "annual") -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            symbol: 股票代码
            year: 年份
            report_type: 报告类型 (annual/quarterly)
            
        Returns:
            财务数据DataFrame
        """
        pass
    
    def validate_and_clean(self, df: pd.DataFrame,
                          required_columns: List[str],
                          numeric_columns: Optional[List[str]] = None,
                          clean: bool = True) -> pd.DataFrame:
        """
        验证和清洗数据
        
        Args:
            df: 原始数据
            required_columns: 必填列
            numeric_columns: 需要检查异常值的数值列
            clean: 是否进行清洗
            
        Returns:
            验证清洗后的数据
            
        Raises:
            DataValidationError: 验证失败
        """
        if df.empty:
            raise DataValidationError("Fetched data is empty")
        
        # 完整性检查
        passed, issues = self.quality_checker.check_integrity(df, required_columns)
        if not passed:
            self.logger.warning(f"Data integrity issues: {issues}")
            if not clean:
                raise DataValidationError(f"Data integrity check failed: {'; '.join(issues)}")
        
        # 检测异常值
        if numeric_columns:
            outliers = self.quality_checker.detect_outliers(df, numeric_columns)
            if outliers:
                self.logger.info(f"Detected outliers: {outliers}")
        
        # 数据清洗
        if clean:
            df = self.quality_checker.clean_data(
                df, 
                remove_duplicates=True, 
                drop_missing=False,
                handle_outliers="fill"
            )
        
        return df


class TushareDataFetcher(BaseDataFetcher):
    """Tushare数据获取器"""
    
    def __init__(self, config: FetchConfig):
        self._api = None
        super().__init__(config)
    
    def _initialize(self) -> None:
        """初始化Tushare API"""
        token = self.config.api_key or os.getenv("TUSHARE_TOKEN")
        
        if not token:
            self.logger.warning("Tushare token not configured")
            return
        
        try:
            import tushare as ts
            ts.set_token(token)
            self._api = ts.pro_api()
            self.logger.info("Tushare initialized successfully")
        except ImportError:
            raise ImportError(
                "Tushare not installed. Install with: pip install tushare"
            )
        except Exception as e:
            raise ApiKeyError(f"Failed to initialize Tushare: {str(e)}")
    
    def _check_api(self) -> bool:
        """检查API是否可用"""
        if self._api is None:
            if not self.config.api_key:
                raise ApiKeyError("Tushare API key not configured")
            return False
        return True
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码为Tushare格式 (000001.SZ)"""
        if '.' in symbol:
            return symbol
        
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith(('0', '3', '00', '30', '68')):
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            return f"{symbol}.BJ"
        return symbol
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期为Tushare格式 (YYYYMMDD)"""
        return date_str.replace('-', '').replace('/', '')
    
    @retry_on_failure()
    def fetch_stock_daily(self, symbol: str,
                         start_date: str,
                         end_date: str,
                         adjust: str = "qfq") -> pd.DataFrame:
        """获取股票日线数据"""
        self._check_rate_limit()
        self._check_api()
        
        ts_symbol = self._format_symbol(symbol)
        start_fmt = self._format_date(start_date)
        end_fmt = self._format_date(end_date)
        
        self.logger.info(f"Fetching daily data for {ts_symbol} from {start_date} to {end_date}")
        
        try:
            df = self._api.daily(
                ts_code=ts_symbol,
                start_date=start_fmt,
                end_date=end_fmt
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 重命名并转换格式
            df = df.rename(columns={
                'ts_code': 'symbol',
                'trade_date': 'date',
                'pre_close': 'pre_close',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount',
                'pct_chg': 'change_pct'
            })
            
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.sort_values('date').reset_index(drop=True)
            
            # 验证清洗
            required_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            if "访问过于频繁" in str(e) or "limit" in str(e).lower():
                raise RateLimitError(f"Tushare rate limit: {str(e)}")
            raise DataFetchError(f"Failed to fetch stock daily: {str(e)}")
    
    @retry_on_failure()
    def fetch_stock_minute(self, symbol: str,
                          period: str = "1min") -> pd.DataFrame:
        """获取股票分钟数据"""
        self._check_rate_limit()
        self._check_api()
        
        ts_symbol = self._format_symbol(symbol)
        
        self.logger.info(f"Fetching {period} data for {ts_symbol}")
        
        try:
            # Tushare的分钟数据接口
            freq_map = {
                "1min": "1min",
                "5min": "5min",
                "15min": "15min",
                "30min": "30min",
                "60min": "60min"
            }
            
            freq = freq_map.get(period, "1min")
            df = self._api.bar(
                ts_code=ts_symbol,
                freq=freq,
                asset="E"
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'symbol',
                'trade_time': 'datetime',
                'vol': 'volume'
            })
            
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            df = df.sort_values('datetime').reset_index(drop=True)
            
            required_cols = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            if "limit" in str(e).lower():
                raise RateLimitError(f"Tushare rate limit: {str(e)}")
            raise DataFetchError(f"Failed to fetch stock minute: {str(e)}")
    
    @retry_on_failure()
    def fetch_index_daily(self, index_code: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
        """获取指数日线数据"""
        self._check_rate_limit()
        self._check_api()
        
        ts_code = self._format_symbol(index_code)
        start_fmt = self._format_date(start_date)
        end_fmt = self._format_date(end_date)
        
        self.logger.info(f"Fetching index daily for {ts_code}")
        
        try:
            df = self._api.index_daily(
                ts_code=ts_code,
                start_date=start_fmt,
                end_date=end_fmt
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'code',
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.sort_values('date').reset_index(drop=True)
            
            required_cols = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch index daily: {str(e)}")
    
    # 宏观指标映射
    MACRO_MAPPING = {
        'gdp': None,  # Tushare宏观数据有限，主要靠AKShare
        'cpi': None,
        'ppi': None,
        'pmi': None,
        'manufacturing_pmi': None,
        'non_manufacturing_pmi': None,
        'interest_rate': 'macro_china_lpr',
        'rrr': 'macro_china_rrr',
        'm2': None,
    }
    
    @retry_on_failure()
    def fetch_macro_indicator(self, indicator_code: str,
                             start_date: str,
                             end_date: str) -> pd.DataFrame:
        """获取宏观经济指标"""
        self._check_rate_limit()
        self._check_api()
        
        indicator = indicator_code.lower()
        self.logger.info(f"Fetching macro indicator {indicator} from Tushare")
        
        api_method = self.MACRO_MAPPING.get(indicator)
        
        if not api_method or not hasattr(self._api, api_method):
            self.logger.warning(f"Indicator {indicator} not available in Tushare")
            return pd.DataFrame()
        
        try:
            func = getattr(self._api, api_method)
            df = func()
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 统一日期格式
            date_cols = ['trade_date', 'date', 'report_date']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format='%Y%m%d')
                    break
            
            df = df.sort_values(df.columns[0]).reset_index(drop=True)
            
            # 筛选日期范围
            if 'date' in df.columns:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            df.rename(columns={'date': 'date', 'lpr': 'value'}, inplace=True)
            df['indicator'] = indicator
            
            required_cols = ['date', 'indicator', 'value']
            df = self.validate_and_clean(df, required_cols, ['value'])
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch macro indicator: {str(e)}")
    
    @retry_on_failure()
    def fetch_financial_report(self, symbol: str,
                               year: int,
                               report_type: str = "annual") -> pd.DataFrame:
        """获取财务报表数据"""
        self._check_rate_limit()
        self._check_api()
        
        ts_symbol = self._format_symbol(symbol)
        self.logger.info(f"Fetching financial report for {ts_symbol}, {year}")
        
        try:
            # 获取利润表
            df = self._api.fincome(
                ts_code=ts_symbol,
                start_date=f"{year}0101",
                end_date=f"{year}1231"
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 转换日期格式
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'], format='%Y%m%d')
                df = df[df['end_date'].dt.year == year]
            
            df['symbol'] = symbol
            df['year'] = year
            
            required_cols = ['symbol', 'year', 'end_date', 'revenue', 'net_profit', 'eps']
            numeric_cols = ['revenue', 'net_profit', 'eps']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch financial report: {str(e)}")


class AkshareDataFetcher(BaseDataFetcher):
    """AKShare数据获取器"""
    
    def __init__(self, config: FetchConfig):
        self._ak = None
        super().__init__(config)
    
    def _initialize(self) -> None:
        """初始化AKShare"""
        try:
            import akshare as ak
            self._ak = ak
            self.logger.info("AKShare initialized successfully")
        except ImportError:
            raise ImportError(
                "AKShare not installed. Install with: pip install akshare"
            )
        except Exception as e:
            raise DataFetchError(f"Failed to initialize AKShare: {str(e)}")
    
    def _check_api(self) -> bool:
        """检查API是否可用"""
        if self._ak is None:
            raise DataFetchError("AKShare not initialized")
        return True
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码为AKShare格式 (sh000001)"""
        if symbol.startswith(('sh', 'sz', 'bj')):
            return symbol
        
        if symbol.startswith('6'):
            return f"sh{symbol}"
        elif symbol.startswith(('0', '3')):
            return f"sz{symbol}"
        elif symbol.startswith(('8', '4')):
            return f"bj{symbol}"
        return symbol
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期为AKShare格式 (YYYYMMDD)"""
        return date_str.replace('-', '').replace('/', '')
    
    # 宏观指标映射表
    MACRO_MAPPING = {
        'gdp': 'macro_china_gdp',
        'gdp_yoy': 'macro_china_gdp_yoy',
        'cpi': 'macro_china_cpi',
        'cpi_yoy': 'macro_china_cpi_yoy',
        'ppi': 'macro_china_ppi',
        'ppi_yoy': 'macro_china_ppi_yoy',
        'pmi': 'macro_china_pmi',
        'manufacturing_pmi': 'macro_china_pmi',
        'non_manufacturing_pmi': 'macro_china_pmi_non',
        'interest_rate': 'macro_china_lpr',
        'rrr': 'macro_china_rrr',
        'm2': 'macro_china_m2',
        'm2_yoy': 'macro_china_m2_yoy',
        'social_financing': 'macro_china_shrzgm',
        'unemployment': 'macro_china_unemployment',
        'consumer_confidence': 'macro_china_consumer_confidence',
        'industrial_output': 'macro_china_industrial_added_yoy',
        'fixed_asset_investment': 'macro_china_fixed_asset_investment_yoy',
        'retail_sales': 'macro_china_retail_sales_yoy',
    }
    
    @retry_on_failure()
    def fetch_stock_daily(self, symbol: str,
                         start_date: str,
                         end_date: str,
                         adjust: str = "qfq") -> pd.DataFrame:
        """获取股票日线数据"""
        self._check_rate_limit()
        self._check_api()
        
        ak_symbol = self._format_symbol(symbol)
        start_fmt = self._format_date(start_date)
        end_fmt = self._format_date(end_date)
        
        self.logger.info(f"Fetching daily data for {ak_symbol} from {start_date} to {end_date}")
        
        try:
            df = self._ak.stock_zh_a_hist(
                symbol=ak_symbol[2:] if ak_symbol.startswith(('sh', 'sz')) else ak_symbol,
                start_date=start_fmt,
                end_date=end_fmt,
                adjust=adjust
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
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
            df['symbol'] = symbol
            df = df.sort_values('date').reset_index(drop=True)
            
            required_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch stock daily from AKShare: {str(e)}")
    
    @retry_on_failure()
    def fetch_stock_minute(self, symbol: str,
                          period: str = "1min") -> pd.DataFrame:
        """获取股票分钟数据"""
        self._check_rate_limit()
        self._check_api()
        
        ak_symbol = self._format_symbol(symbol)
        self.logger.info(f"Fetching {period} data for {ak_symbol}")
        
        try:
            # AKShare的分钟数据接口
            symbol_clean = ak_symbol[2:] if ak_symbol.startswith(('sh', 'sz')) else ak_symbol
            
            period_map = {
                "1min": "1",
                "5min": "5",
                "15min": "15",
                "30min": "30",
                "60min": "60"
            }
            
            period_code = period_map.get(period, "1")
            
            try:
                df = self._ak.stock_zh_a_hist_min_em(
                    symbol=symbol_clean,
                    period=period_code
                )
            except AttributeError:
                # 兼容不同版本
                df = self._ak.stock_zh_a_minute(
                    symbol=ak_symbol,
                    period=period_code
                )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 标准化
            if '时间' in df.columns:
                df = df.rename(columns={'时间': 'datetime'})
                df['datetime'] = pd.to_datetime(df['datetime'])
                df['date'] = df['datetime'].dt.date
            
            if '开盘' in df.columns:
                df = df.rename(columns={
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume'
                })
            
            df['symbol'] = symbol
            df = df.sort_values('datetime').reset_index(drop=True)
            
            required_cols = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch stock minute: {str(e)}")
    
    @retry_on_failure()
    def fetch_index_daily(self, index_code: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
        """获取指数日线数据"""
        self._check_rate_limit()
        self._check_api()
        
        ak_symbol = self._format_symbol(index_code)
        start_fmt = self._format_date(start_date)
        end_fmt = self._format_date(end_date)
        
        self.logger.info(f"Fetching index daily for {ak_symbol}")
        
        try:
            # 获取指数数据
            if index_code in ['000001', '000300', '399001', '399006']:
                # 主要指数直接调用
                symbol_clean = ak_symbol[2:] if ak_symbol.startswith(('sh', 'sz')) else ak_symbol
                df = self._ak.stock_zh_index_daily(
                    symbol=ak_symbol
                )
            else:
                df = self._ak.stock_zh_a_hist(
                    symbol=symbol_clean,
                    start_date=start_fmt,
                    end_date=end_fmt,
                    adjust=""
                )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 标准化
            if '日期' in df.columns:
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
            
            if 'date' not in df.columns and df.index.name == 'date':
                df = df.reset_index()
            
            df['date'] = pd.to_datetime(df['date'])
            df['code'] = index_code
            
            # 筛选日期范围
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            df = df.sort_values('date').reset_index(drop=True)
            
            required_cols = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch index daily: {str(e)}")
    
    @retry_on_failure()
    def fetch_macro_indicator(self, indicator_code: str,
                             start_date: str,
                             end_date: str) -> pd.DataFrame:
        """获取宏观经济指标"""
        self._check_rate_limit()
        self._check_api()
        
        indicator = indicator_code.lower()
        self.logger.info(f"Fetching macro indicator {indicator} from AKShare")
        
        method_name = self.MACRO_MAPPING.get(indicator)
        
        if not method_name or not hasattr(self._ak, method_name):
            self.logger.error(f"Indicator {indicator} not found in AKShare mapping")
            return pd.DataFrame()
        
        try:
            func = getattr(self._ak, method_name)
            df = func()
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 标准化列名
            rename_map = {
                '日期': 'date',
                '指标': 'indicator',
                '数值': 'value',
                '同比': 'yoy',
                '环比': 'mom',
                '中国GDP: 累计同比': 'value',
                '国内生产总值累计增长(%)': 'value',
                '居民消费价格指数(上月=100)': 'value',
                '居民消费价格指数同比(%)': 'value',
            }
            df = df.rename(columns=lambda x: rename_map.get(x, x))
            
            # 确保有date列
            if 'date' not in df.columns:
                for col in df.columns:
                    if '日期' in str(col) or '时间' in str(col):
                        df = df.rename(columns={col: 'date'})
                        break
            
            # 转换日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                # 筛选日期范围
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            # 确保有value列
            if 'value' not in df.columns:
                # 尝试找第一个数值列
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    df['value'] = df[numeric_cols[0]]
            
            df['indicator'] = indicator
            
            required_cols = ['date', 'indicator', 'value']
            numeric_cols = ['value']
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            raise DataFetchError(f"Failed to fetch macro indicator {indicator}: {str(e)}")
    
    @retry_on_failure()
    def fetch_financial_report(self, symbol: str,
                               year: int,
                               report_type: str = "annual") -> pd.DataFrame:
        """获取财务报表数据"""
        self._check_rate_limit()
        self._check_api()
        
        self.logger.info(f"Fetching financial report for {symbol}, {year}")
        
        try:
            # AKShare获取财务报表
            symbol_clean = symbol.replace('.SH', '').replace('.SZ', '')
            
            # 获取资产负债表/利润表
            if report_type == "annual":
                # 年报
                df = self._ak.stock_financial_report(
                    symbol=symbol_clean,
                    report_type="年报"
                )
            else:
                # 季报
                df = self._ak.stock_financial_report(
                    symbol=symbol_clean,
                    report_type="季报"
                )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            df['symbol'] = symbol
            df['year'] = year
            
            required_cols = ['symbol', 'year']
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            df = self.validate_and_clean(df, required_cols, numeric_cols)
            
            return df
            
        except Exception as e:
            # 备用方案：利润表
            try:
                df = self._ak.stock_profit_statement(
                    symbol=symbol_clean
                )
                df['symbol'] = symbol
                df['year'] = year
                return df
            except Exception as e2:
                raise DataFetchError(f"Failed to fetch financial report: {str(e)}, {str(e2)}")


def create_data_fetcher(source_type: str, config: FetchConfig) -> BaseDataFetcher:
    """
    创建数据获取器工厂函数
    
    Args:
        source_type: 数据源类型 ('tushare' or 'akshare')
        config: 配置对象
        
    Returns:
        数据获取器实例
    """
    if source_type.lower() == 'tushare':
        return TushareDataFetcher(config)
    elif source_type.lower() == 'akshare':
        return AkshareDataFetcher(config)
    else:
        raise ValueError(f"Unknown data source type: {source_type}")


__all__ = [
    'BaseDataFetcher',
    'TushareDataFetcher',
    'AkshareDataFetcher',
    'DataQualityChecker',
    'FetchConfig',
    'create_data_fetcher',
    'retry_on_failure',
]

