# -*- coding: utf-8 -*-
"""
宏观分析模块配置

包含爬虫配置、分析器配置和API配置
"""

from typing import Dict, List, Optional


class CrawlerConfig:
    """爬虫配置"""
    
    # 默认请求超时
    DEFAULT_TIMEOUT = 30
    
    # 默认重试次数
    DEFAULT_RETRIES = 3
    
    # 请求间隔（秒）
    MIN_DELAY = 1
    MAX_DELAY = 3
    
    # 分页配置
    DEFAULT_PAGE_COUNT = 2
    
    # 代理配置
    PROXIES = None
    
    # 用户代理池
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    # 要爬取的官方媒体和政府网站
    SOURCES = [
        {
            'name': '中国政府网',
            'url': 'https://www.gov.cn',
            'type': 'government',
            'enabled': True,
            'sections': ['/xinwen/lianbo/', '/zhengce/']
        },
        {
            'name': '证监会',
            'url': 'http://www.csrc.gov.cn',
            'type': 'regulator',
            'enabled': True,
            'sections': ['/pub/newsite/', '/pub/newsite/zjhxwfb/']
        },
        {
            'name': '央行',
            'url': 'http://www.pbc.gov.cn',
            'type': 'government',
            'enabled': True,
            'sections': ['/goutongjiaoliu/', '/tiaofasi/']
        },
        {
            'name': '新华社',
            'url': 'https://www.xinhuanet.com',
            'type': 'state_media',
            'enabled': True,
            'sections': ['/fortune/', '/fortune/gncj/']
        },
        {
            'name': '人民网',
            'url': 'http://finance.people.com.cn',
            'type': 'state_media',
            'enabled': True,
            'sections': ['/']
        },
        {
            'name': '央视新闻',
            'url': 'https://news.cctv.com',
            'type': 'state_media',
            'enabled': True,
            'sections': ['/finance/']
        },
    ]


class AnalyzerConfig:
    """分析器配置"""
    
    # 关键词提取
    KEYWORD_WEIGHTS = {
        'importance': 0.3,
        'frequency': 0.3,
        'tfidf': 0.4
    }
    
    # 情感分析
    SENTIMENT_THRESHOLDS = {
        'very_positive': 0.7,
        'positive': 0.3,
        'neutral': -0.3,
        'negative': -0.7,
        'very_negative': -1.0
    }
    
    # 政策分析
    POLICY_SCORE_WEIGHTS = {
        'keywords': 0.4,
        'sentiment': 0.3,
        'context': 0.3
    }
    
    # 影响评估
    IMPACT_DURATION_WEIGHTS = {
        'short_term': 0.2,
        'medium_term': 0.3,
        'long_term': 0.5
    }


class DatabaseConfig:
    """数据库配置"""
    
    # 默认连接字符串
    DEFAULT_DATABASE_URL = 'sqlite:///data/macro_analysis.db'
    
    # 连接池配置
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600
    
    # 批量插入配置
    BATCH_SIZE = 100
    COMMIT_INTERVAL = 1000
    
    # 索引配置
    CREATE_INDEXES = True


class APIConfig:
    """API配置"""
    
    # 默认分页大小
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 响应缓存配置
    CACHE_ENABLED = True
    CACHE_EXPIRE_SECONDS = 3600
    
    # 限流配置
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 100
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class LoggerConfig:
    """日志配置"""
    
    LOG_FILE = 'logs/macro_analysis.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    LOG_ENCODING = 'utf-8'


class Config:
    """综合配置类"""
    
    crawler = CrawlerConfig()
    analyzer = AnalyzerConfig()
    database = DatabaseConfig()
    api = APIConfig()
    logger = LoggerConfig()


# 全局配置实例
config = Config()
