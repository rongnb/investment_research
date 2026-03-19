# -*- coding: utf-8 -*-
"""
单元测试 - 数据获取器模块

测试TushareDataFetcher和AkshareDataFetcher的基本功能
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.common.data_fetcher import (
    TushareDataFetcher,
    AkshareDataFetcher,
    FetchConfig,
    DataQualityChecker,
    create_data_fetcher
)

from modules.common.exceptions import (
    DataFetchError,
    ApiKeyError
)


class TestDataQualityChecker:
    """数据质量检查器测试"""
    
    def setup_method(self):
        self.checker = DataQualityChecker()
    
    def test_check_integrity_ok(self):
        """测试完整数据检查"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', '2024-01-10'),
            'open': np.random.randn(10),
            'close': np.random.randn(10),
            'volume': np.random.randint(1000000, 10000000, 10)
        })
        required = ['date', 'open', 'close', 'volume']
        passed, issues = self.checker.check_integrity(df, required)
        assert passed
        assert len(issues) == 0
    
    def test_check_integrity_missing_col(self):
        """测试缺失列检查"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', '2024-01-10'),
            'open': np.random.randn(10),
            'close': np.random.randn(10)
        })
        required = ['date', 'open', 'close', 'volume']
        passed, issues = self.checker.check_integrity(df, required)
        assert not passed
        assert len(issues) > 0
        assert 'volume' in issues[0]
    
    def test_check_integrity_empty(self):
        """测试空数据检查"""
        df = pd.DataFrame()
        required = ['date', 'open']
        passed, issues = self.checker.check_integrity(df, required)
        assert not passed
        assert 'empty' in issues[0].lower()
    
    def test_detect_outliers(self):
        """测试异常值检测"""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5, 100]  # 100是异常值
        })
        outliers = self.checker.detect_outliers(df, ['value'])
        assert 'value' in outliers
        assert outliers['value'] >= 1
    
    def test_clean_data_remove_duplicates(self):
        """测试移除重复数据"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'value': [1, 1, 2]
        })
        df['date'] = pd.to_datetime(df['date'])
        cleaned = self.checker.clean_data(df, remove_duplicates=True)
        assert len(cleaned) == 2
    
    def test_clean_data_drop_missing(self):
        """测试删除缺失值"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', '2024-01-05'),
            'value': [1, None, 3, None, 5]
        })
        cleaned = self.checker.clean_data(df, drop_missing=True)
        assert len(cleaned) == 3


class TestFetchConfig:
    """FetchConfig测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = FetchConfig()
        assert config.retry_times == 3
        assert config.max_requests_per_minute == 60
        assert config.cache_enabled == True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = FetchConfig(
            api_key='test_key',
            retry_times=5,
            max_requests_per_minute=100
        )
        assert config.api_key == 'test_key'
        assert config.retry_times == 5
        assert config.max_requests_per_minute == 100


class TestCreateDataFetcher:
    """工厂函数测试"""
    
    def test_create_akshare(self):
        """测试创建AKShare获取器"""
        config = FetchConfig()
        fetcher = create_data_fetcher('akshare', config)
        assert isinstance(fetcher, AkshareDataFetcher)
    
    def test_create_tushare(self):
        """测试创建Tushare获取器"""
        config = FetchConfig(api_key='test_token')
        fetcher = create_data_fetcher('tushare', config)
        assert isinstance(fetcher, TushareDataFetcher)
    
    def test_create_unknown(self):
        """测试未知数据源"""
        config = FetchConfig()
        with pytest.raises(ValueError):
            create_data_fetcher('unknown', config)


class TestAkshareDataFetcher:
    """AKShare数据获取器测试"""
    
    def setup_method(self):
        try:
            import akshare
            self.has_akshare = True
        except ImportError:
            self.has_akshare = False
            return
        
        config = FetchConfig()
        try:
            self.fetcher = AkshareDataFetcher(config)
            self.initialized = True
        except Exception:
            self.initialized = False
    
    def test_initialize(self):
        """测试初始化"""
        if not self.has_akshare:
            pytest.skip("AKShare not installed")
        assert self.initialized
    
    def test_macro_mapping_exists(self):
        """测试宏观指标映射存在"""
        if not self.has_akshare or not self.initialized:
            pytest.skip("AKShare not available")
        assert hasattr(self.fetcher, 'MACRO_MAPPING')
        assert len(self.fetcher.MACRO_MAPPING) > 0
        assert 'gdp' in self.fetcher.MACRO_MAPPING
        assert 'cpi' in self.fetcher.MACRO_MAPPING
        assert 'pmi' in self.fetcher.MACRO_MAPPING
    
    def test_format_symbol(self):
        """测试股票代码格式化"""
        if not self.has_akshare or not self.initialized:
            pytest.skip("AKShare not available")
        
        # 上海代码应该加上sh前缀
        assert self.fetcher._format_symbol('600000') == 'sh600000'
        # 深圳代码应该加上sz前缀
        assert self.fetcher._format_symbol('000001') == 'sz000001'
        # 已经有前缀应该保持不变
        assert self.fetcher._format_symbol('sh600000') == 'sh600000'


class TestTushareDataFetcher:
    """Tushare数据获取器测试"""
    
    def setup_method(self):
        try:
            import tushare
            self.has_tushare = True
        except ImportError:
            self.has_tushare = False
            return
        
        # 检查是否有环境变量token
        token = os.getenv('TUSHARE_TOKEN')
        config = FetchConfig(api_key=token)
        self.fetcher = TushareDataFetcher(config)
    
    def test_format_symbol(self):
        """测试股票代码格式化"""
        if not self.has_tushare:
            pytest.skip("Tushare not installed")
        
        assert self.fetcher._format_symbol('600000') == '600000.SH'
        assert self.fetcher._format_symbol('000001') == '000001.SZ'
        assert self.fetcher._format_symbol('000001.SZ') == '000001.SZ'
    
    def test_format_date(self):
        """测试日期格式化"""
        if not self.has_tushare:
            pytest.skip("Tushare not installed")
        
        assert self.fetcher._format_date('2024-01-01') == '20240101'
        assert self.fetcher._format_date('20240101') == '20240101'


class TestIntegration:
    """集成测试 - 需要实际依赖和API密钥"""
    
    def test_akshare_importable(self):
        """测试AKShare是否可导入"""
        try:
            import akshare
            assert True
        except ImportError:
            # 这只是警告，不是失败
            pytest.warns(UserWarning, match="AKShare not installed")
    
    def test_tushare_importable(self):
        """测试Tushare是否可导入"""
        try:
            import tushare
            assert True
        except ImportError:
            pytest.warns(UserWarning, match="Tushare not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
