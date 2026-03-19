# -*- coding: utf-8 -*-
"""
数据采集模块

提供统一的数据采集接口，支持多数据源（AKShare、Tushare等），
实现数据缓存和增量更新机制。
"""

from .base import DataCollector, DataSourceType
from .akshare_adapter import AKShareCollector
from .tushare_adapter import TushareCollector
from .cache import DataCache
from .validator import DataValidator

__all__ = [
    'DataCollector',
    'DataSourceType',
    'AKShareCollector',
    'TushareCollector', 
    'DataCache',
    'DataValidator',
]