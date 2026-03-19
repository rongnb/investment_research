# -*- coding: utf-8 -*-
"""
宏观分析模块

提供官方媒体、政府公告、政策文件的爬取与分析功能
"""

__version__ = "1.0.0"
__author__ = "Investment Research Team"

from .database import init_db, get_db_session
from .crawler.scheduler import CrawlerScheduler
from .analyzer.policy import PolicyAnalyzer
from .analyzer.sentiment import SentimentAnalyzer

__all__ = [
    "init_db",
    "get_db_session",
    "CrawlerScheduler",
    "PolicyAnalyzer",
    "SentimentAnalyzer",
]