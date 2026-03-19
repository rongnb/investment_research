# -*- coding: utf-8 -*-
"""
数据采集模块

统一的数据采集接口，支持多数据源
集成Tushare和AKShare真实数据源
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import os

from .data_fetcher import (
    TushareDataFetcher,
    AkshareDataFetcher,
    FetchConfig,
    DataQualityChecker
)

from .exceptions import (
    DataFetchError,
    ApiKeyError,
    DataValidationError
)

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """数据源类型"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class DataConfig:
    """数据源配置"""
    source: DataSource
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    retry_times: int = 3
    max_requests_per_minute: int = 60
    cache_dir: str = "./data/cache"
    cache_expire_hours: int = 24
    enable_quality_check: bool = True
    auto_clean: bool = True


@dataclass
class DataResult:
    """数据采集结果"""
    success: bool
    data: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    source: DataSource = DataSource.LOCAL
    timestamp: datetime = field(default_factory=datetime.now)
    cached: bool = False
    quality_issues: List[str] = field(default_factory=list)


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "./data/cache", expire_hours: int = 24):
        self.cache_dir = cache_dir
        self.expire_hours = expire_hours
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, source: DataSource, query: str) -> str:
        """生成缓存键"""
        import hashlib
        key = f"{source.value}_{query}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, source: DataSource, query: str) -> str:
        """获取缓存文件路径"""
        key = self._get_cache_key(source, query)
        return os.path.join(self.cache_dir, f"{key}.parquet")
    
    def get(self, source: DataSource, query: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        cache_path = self._get_cache_path(source, query)
        
        if not os.path.exists(cache_path):
            return None
        
        # 检查是否过期
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if (datetime.now() - mtime).hours > self.expire_hours:
            return None
        
        try:
            return pd.read_parquet(cache_path)
        except:
            return None
    
    def set(self, source: DataSource, query: str, data: pd.DataFrame) -> None:
        """保存数据到缓存"""
        cache_path = self._get_cache_path(source, query)
        try:
            data.to_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")


class DataCollector:
    """
    统一数据采集器
    
    支持多数据源，统一接口，自动缓存
    """
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.cache = DataCache(config.cache_dir, config.cache_expire_hours)
        self.quality_checker = DataQualityChecker()
        
        # 根据配置选择数据采集器
        self._initialize_fetcher()
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_fetcher(self):
        """初始化数据获取器"""
        fetch_config = FetchConfig(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            retry_times=self.config.retry_times,
            max_requests_per_minute=self.config.max_requests_per_minute
        )
        
        if self.config.source == DataSource.MOCK:
            # 使用模拟数据
            class MockDataFetcher:
                def __init__(self, config):
                    self.config = config
                def fetch_stock_daily(self, symbol, start_date, end_date, adjust="qfq"):
                    start = pd.to_datetime(start_date)
                    end = pd.to_datetime(end_date)
                    dates = pd.date_range(start, end, freq='D')
                    dates = dates[dates.weekday < 5]
                    n = len(dates)
                    base_price = 100.0
                    np.random.seed(hash(symbol) % 10000)
                    returns = np.random.randn(n) * 0.02
                    prices = base_price * np.exp(np.cumsum(returns))
                    df = pd.DataFrame({
                        'date': dates,
                        'symbol': symbol,
                        'open': prices * (1 + np.random.randn(n) * 0.01),
                        'high': prices * (1 + np.abs(np.random.randn(n)) * 0.02),
                        'low': prices * (1 - np.abs(np.random.randn(n)) * 0.02),
                        'close': prices,
                        'volume': np.random.randint(1000000, 10000000, n),
                        'amount': prices * np.random.randint(1000000, 10000000, n)
                    })
                    return df
                def fetch_stock_minute(self, symbol, period="1min"):
                    end = datetime.now()
                    start = end - timedelta(days=1)
                    return self.fetch_stock_daily(symbol, 
                        start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
                def fetch_macro_indicator(self, indicator_code, start_date, end_date):
                    start = pd.to_datetime(start_date)
                    end = pd.to_datetime(end_date)
                    dates = pd.date_range(start, end, freq='M')
                    n = len(dates)
                    if 'gdp' in indicator_code.lower():
                        values = 5 + np.cumsum(np.random.randn(n) * 0.3)
                    elif 'cpi' in indicator_code.lower():
                        values = 2 + np.cumsum(np.random.randn(n) * 0.2)
                    elif 'pmi' in indicator_code.lower():
                        values = 50 + np.cumsum(np.random.randn(n) * 0.5)
                        values = np.clip(values, 45, 55)
                    else:
                        values = np.random.randn(n) * 5
                    df = pd.DataFrame({
                        'date': dates,
                        'indicator': indicator_code,
                        'value': values
                    })
                    return df
                def fetch_index_daily(self, index_code, start_date, end_date):
                    return self.fetch_stock_daily(index_code, start_date, end_date)
                def fetch_financial_report(self, symbol, year, report_type="annual"):
                    if report_type == "annual":
                        df = pd.DataFrame({
                            'symbol': [symbol],
                            'year': [year],
                            'report_type': ['年报'],
                            'revenue': [np.random.uniform(10, 100) * 1e8],
                            'net_profit': [np.random.uniform(1, 20) * 1e8],
                            'eps': [np.random.uniform(0.5, 5)],
                            'roe': [np.random.uniform(5, 20)]
                        })
                    else:
                        df = pd.DataFrame({
                            'symbol': [symbol] * 4,
                            'report_type': ['一季报', '中报', '三季报', '年报'],
                            'year': [year] * 4,
                            'revenue': np.random.uniform(10, 100, 4) * 1e8,
                            'net_profit': np.random.uniform(1, 20, 4) * 1e8,
                            'eps': np.random.uniform(0.5, 5, 4),
                            'roe': np.random.uniform(5, 20, 4)
                        })
                    return df
            
            self.fetcher = MockDataFetcher(fetch_config)
        
        elif self.config.source == DataSource.TUSHARE:
            self.fetcher = TushareDataFetcher(fetch_config)
            logger.info("Initialized Tushare data fetcher")
        
        elif self.config.source == DataSource.AKSHARE:
            self.fetcher = AkshareDataFetcher(fetch_config)
            logger.info("Initialized AKShare data fetcher")
        
        else:
            logger.warning(f"Data source {self.config.source} not implemented, falling back to mock")
            # 回退到模拟数据
            self.fetcher = MockDataFetcher(fetch_config)
    
    def _run_quality_check(self, df: pd.DataFrame, 
                          required_columns: List[str],
                          numeric_columns: Optional[List[str]] = None) -> List[str]:
        """运行数据质量检查"""
        if not self.config.enable_quality_check:
            return []
        
        issues = []
        passed, integrity_issues = self.quality_checker.check_integrity(df, required_columns)
        issues.extend(integrity_issues)
        
        if numeric_columns:
            outliers = self.quality_checker.detect_outliers(df, numeric_columns)
            for col, count in outliers.items():
                issues.append(f"Column '{col}' has {count} outliers")
        
        return issues
    
    def get_stock_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
        use_cache: bool = True
    ) -> DataResult:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 (qfq/hfq/none)
            use_cache: 是否使用缓存
            
        Returns:
            DataResult with fetched data
        """
        query = f"stock_daily_{symbol}_{start_date}_{end_date}_{adjust}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = self.cache.get(self.config.source, query)
            if cached_data is not None:
                logger.info(f"Using cached data for {symbol}")
                return DataResult(
                    success=True,
                    data=cached_data,
                    source=self.config.source,
                    cached=True
                )
        
        # 获取新数据
        try:
            df = self.fetcher.fetch_stock_daily(symbol, start_date, end_date, adjust)
            
            if df.empty:
                return DataResult(
                    success=False,
                    error="Empty response from data source",
                    source=self.config.source,
                    cached=False
                )
            
            # 质量检查
            required_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            quality_issues = self._run_quality_check(df, required_cols, numeric_cols)
            
            # 数据清洗
            if self.config.auto_clean and quality_issues:
                df = self.quality_checker.clean_data(
                    df,
                    remove_duplicates=True,
                    drop_missing=False,
                    handle_outliers="fill"
                )
            
            # 缓存数据
            if use_cache:
                self.cache.set(self.config.source, query, df)
            
            return DataResult(
                success=True,
                data=df,
                source=self.config.source,
                cached=False,
                quality_issues=quality_issues
            )
            
        except DataFetchError as e:
            return DataResult(
                success=False,
                error=str(e),
                source=self.config.source,
                cached=False
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            return DataResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                source=self.config.source,
                cached=False
            )
    
    def get_stock_minute(
        self,
        symbol: str,
        period: str = "1min",
        use_cache: bool = True
    ) -> DataResult:
        """
        获取股票分钟数据
        
        Args:
            symbol: 股票代码
            period: 周期 (1min/5min/15min/30min/60min)
            use_cache: 是否使用缓存
            
        Returns:
            DataResult with fetched data
        """
        query = f"stock_minute_{symbol}_{period}"
        
        if use_cache:
            cached_data = self.cache.get(self.config.source, query)
            if cached_data is not None:
                return DataResult(
                    success=True,
                    data=cached_data,
                    source=self.config.source,
                    cached=True
                )
        
        try:
            df = self.fetcher.fetch_stock_minute(symbol, period)
            
            if df.empty:
                return DataResult(
                    success=False,
                    error="Empty response from data source",
                    source=self.config.source
                )
            
            required_cols = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            quality_issues = self._run_quality_check(df, required_cols, numeric_cols)
            
            if use_cache:
                self.cache.set(self.config.source, query, df)
            
            return DataResult(
                success=True,
                data=df,
                source=self.config.source,
                quality_issues=quality_issues
            )
            
        except Exception as e:
            return DataResult(success=False, error=str(e), source=self.config.source)
    
    def get_macro_indicator(
        self,
        indicator_code: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> DataResult:
        """
        获取宏观经济指标
        
        Args:
            indicator_code: 指标代码 (gdp, cpi, ppi, pmi等)
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存
            
        Returns:
            DataResult with indicator data
        """
        query = f"macro_{indicator_code}_{start_date}_{end_date}"
        
        if use_cache:
            cached_data = self.cache.get(self.config.source, query)
            if cached_data is not None:
                return DataResult(
                    success=True,
                    data=cached_data,
                    source=self.config.source,
                    cached=True
                )
        
        try:
            df = self.fetcher.fetch_macro_indicator(indicator_code, start_date, end_date)
            
            if df.empty:
                return DataResult(
                    success=False,
                    error=f"No data for indicator {indicator_code}",
                    source=self.config.source
                )
            
            required_cols = ['date', 'indicator', 'value']
            quality_issues = self._run_quality_check(df, required_cols, ['value'])
            
            if use_cache:
                self.cache.set(self.config.source, query, df)
            
            return DataResult(
                success=True,
                data=df,
                source=self.config.source,
                quality_issues=quality_issues
            )
            
        except Exception as e:
            return DataResult(success=False, error=str(e), source=self.config.source)
    
    def get_index_daily(
        self,
        index_code: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> DataResult:
        """
        获取指数日线数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存
            
        Returns:
            DataResult with index data
        """
        query = f"index_daily_{index_code}_{start_date}_{end_date}"
        
        if use_cache:
            cached_data = self.cache.get(self.config.source, query)
            if cached_data is not None:
                return DataResult(
                    success=True,
                    data=cached_data,
                    source=self.config.source,
                    cached=True
                )
        
        try:
            df = self.fetcher.fetch_index_daily(index_code, start_date, end_date)
            
            if df.empty:
                return DataResult(
                    success=False,
                    error=f"No data for index {index_code}",
                    source=self.config.source
                )
            
            required_cols = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            quality_issues = self._run_quality_check(df, required_cols, numeric_cols)
            
            if use_cache:
                self.cache.set(self.config.source, query, df)
            
            return DataResult(
                success=True,
                data=df,
                source=self.config.source,
                quality_issues=quality_issues
            )
            
        except Exception as e:
            return DataResult(success=False, error=str(e), source=self.config.source)
    
    def get_financial_report(
        self,
        symbol: str,
        year: int,
        report_type: str = "annual",
        use_cache: bool = True
    ) -> DataResult:
        """
        获取财务报表数据
        
        Args:
            symbol: 股票代码
            year: 年份
            report_type: 报告类型 (annual/quarterly)
            use_cache: 是否使用缓存
            
        Returns:
            DataResult with financial data
        """
        query = f"financial_{symbol}_{year}_{report_type}"
        
        if use_cache:
            cached_data = self.cache.get(self.config.source, query)
            if cached_data is not None:
                return DataResult(
                    success=True,
                    data=cached_data,
                    source=self.config.source,
                    cached=True
                )
        
        try:
            df = self.fetcher.fetch_financial_report(symbol, year, report_type)
            
            if df.empty:
                return DataResult(
                    success=False,
                    error=f"No financial data for {symbol} {year}",
                    source=self.config.source
                )
            
            required_cols = ['symbol', 'year']
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            quality_issues = self._run_quality_check(df, required_cols, numeric_cols)
            
            if use_cache:
                self.cache.set(self.config.source, query, df)
            
            return DataResult(
                success=True,
                data=df,
                source=self.config.source,
                quality_issues=quality_issues
            )
            
        except Exception as e:
            return DataResult(success=False, error=str(e), source=self.config.source)
    
    def batch_get_stocks(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, DataResult]:
        """批量获取多只股票数据"""
        results = {}
        
        for symbol in symbols:
            try:
                result = self.get_stock_daily(symbol, start_date, end_date)
                results[symbol] = result
                time.sleep(0.1)  # 避免请求过快
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                results[symbol] = DataResult(success=False, error=str(e), source=self.config.source)
        
        return results


def create_data_collector(
    source: str = "mock",
    api_key: Optional[str] = None,
    cache_dir: str = "./data/cache",
    max_requests_per_minute: int = 60
) -> DataCollector:
    """
    创建数据采集器
    
    Args:
        source: 数据源 (mock/tushare/akshare/eastmoney)
        api_key: API密钥
        cache_dir: 缓存目录
        max_requests_per_minute: 每分钟最大请求数
        
    Returns:
        DataCollector实例
    """
    source_enum = DataSource(source.lower())
    
    config = DataConfig(
        source=source_enum,
        api_key=api_key,
        cache_dir=cache_dir,
        max_requests_per_minute=max_requests_per_minute
    )
    
    return DataCollector(config)


# 多数据源回退采集器
class FallbackDataCollector:
    """
    支持多数据源回退的数据采集器
    
    按照优先级尝试多个数据源，失败自动切换
    """
    
    def __init__(self, sources_config: List[Dict]):
        """
        初始化
        
        Args:
            sources_config: 数据源配置列表，按优先级排序
                [
                    {
                        'source': 'tushare',
                        'api_key': 'xxx',
                    },
                    {
                        'source': 'akshare',
                    }
                ]
        """
        self.collectors: List[DataCollector] = []
        for cfg in sources_config:
            source = cfg.pop('source')
            api_key = cfg.pop('api_key', None)
            collector = create_data_collector(source, api_key=api_key, **cfg)
            self.collectors.append(collector)
        
        self.logger = logging.getLogger(__name__)
    
    def _try_collect(self, method_name: str, *args, **kwargs) -> DataResult:
        """尝试从多个数据源获取数据"""
        for i, collector in enumerate(self.collectors):
            try:
                method = getattr(collector, method_name)
                result = method(*args, **kwargs)
                if result.success and result.data is not None and not result.data.empty:
                    self.logger.info(f"Got data from {collector.config.source.value} (attempt {i+1})")
                    return result
                else:
                    self.logger.warning(f"Failed with {collector.config.source.value}: {result.error}")
            except Exception as e:
                self.logger.warning(f"Exception with {collector.config.source.value}: {e}")
        
        return DataResult(
            success=False,
            error="All data sources failed"
        )
    
    def get_stock_daily(self, *args, **kwargs) -> DataResult:
        return self._try_collect('get_stock_daily', *args, **kwargs)
    
    def get_stock_minute(self, *args, **kwargs) -> DataResult:
        return self._try_collect('get_stock_minute', *args, **kwargs)
    
    def get_macro_indicator(self, *args, **kwargs) -> DataResult:
        return self._try_collect('get_macro_indicator', *args, **kwargs)
    
    def get_index_daily(self, *args, **kwargs) -> DataResult:
        return self._try_collect('get_index_daily', *args, **kwargs)
    
    def get_financial_report(self, *args, **kwargs) -> DataResult:
        return self._try_collect('get_financial_report', *args, **kwargs)


# 示例用法
if __name__ == "__main__":
    # 创建采集器
    collector = create_data_collector("mock")
    
    # 获取股票数据
    result = collector.get_stock_daily("000001", "2024-01-01", "2024-03-01")
    if result.success:
        print(f"Got {len(result.data)} rows of stock data")
        print(result.data.head())
    else:
        print(f"Failed: {result.error}")
    
    # 获取宏观数据
    result = collector.get_macro_indicator("gdp", "2023-01-01", "2024-01-01")
    if result.success:
        print(f"\nGot {len(result.data)} rows of macro data")
        print(result.data.head())
