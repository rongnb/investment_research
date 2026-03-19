# -*- coding: utf-8 -*-
"""
爬虫基类

定义爬虫的标准接口和基础功能
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CrawlerResult:
    """爬虫结果数据类"""
    title: str
    content: str
    url: str
    source_name: str
    source_type: str
    content_type: str
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    original_data: Dict = field(default_factory=dict)
    
    # 内部字段
    _content_hash: str = field(default="")
    _crawled_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self._content_hash:
            self._content_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """计算内容哈希值，用于去重"""
        content = f"{self.title}{self.content[:500]}{self.source_name}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'content_type': self.content_type,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'author': self.author,
            'category': self.category,
            'tags': self.tags,
            'content_hash': self._content_hash,
            'crawled_at': self._crawled_at.isoformat(),
        }


class BaseCrawler(ABC):
    """
    爬虫基类
    
    所有具体爬虫实现都需要继承此类
    """
    
    # 爬虫标识
    name: str = "base"
    source_name: str = "未知来源"
    source_type: str = "unknown"
    
    # 默认配置
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def __init__(self, config: Dict = None, use_proxy: bool = False):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置
            use_proxy: 是否使用代理
        """
        self.config = config or {}
        self.use_proxy = use_proxy
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        
        # 请求间隔控制
        self.min_delay = self.config.get('min_delay', 1)
        self.max_delay = self.config.get('max_delay', 3)
        self.last_request_time = 0
        
        # 重试配置
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5)
        
        # 去重缓存
        self._url_cache = set()
        self._content_cache = set()
        
        logger.info(f"[{self.name}] 爬虫初始化完成")
    
    def _respect_rate_limit(self):
        """遵守请求频率限制"""
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"[{self.name}] 遵守频率限制，等待 {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, method: str = 'GET', 
                      headers: Dict = None, params: Dict = None,
                      data: Dict = None, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 请求头
            params: URL参数
            data: 请求数据
            
        Returns:
            Response对象
        """
        self._respect_rate_limit()
        
        request_headers = {**self.session.headers}
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[{self.name}] 请求: {url}")
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    data=data,
                    timeout=kwargs.get('timeout', 30),
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"[{self.name}] 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (attempt + 1)
                    logger.info(f"[{self.name}] {sleep_time}秒后重试...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"[{self.name}] 请求最终失败: {url}")
                    raise
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        解析HTML
        
        Args:
            html: HTML内容
            
        Returns:
            BeautifulSoup对象
        """
        return BeautifulSoup(html, 'html.parser')
    
    def _is_duplicate(self, url: str, content_hash: str = None) -> bool:
        """
        检查是否重复
        
        Args:
            url: URL
            content_hash: 内容哈希
            
        Returns:
            是否重复
        """
        if url in self._url_cache:
            return True
        if content_hash and content_hash in self._content_cache:
            return True
        return False
    
    def _add_to_cache(self, url: str, content_hash: str = None):
        """添加到缓存"""
        self._url_cache.add(url)
        if content_hash:
            self._content_cache.add(content_hash)
    
    @abstractmethod
    def get_list_urls(self, **kwargs) -> List[str]:
        """
        获取列表页URL
        
        Returns:
            URL列表
        """
        pass
    
    @abstractmethod
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """
        解析列表页
        
        Args:
            html: 列表页HTML
            list_url: 列表页URL
            
        Returns:
            文章信息列表
        """
        pass
    
    @abstractmethod
    def parse_detail(self, html: str, detail_url: str) -> CrawlerResult:
        """
        解析详情页
        
        Args:
            html: 详情页HTML
            detail_url: 详情页URL
            
        Returns:
            爬取结果
        """
        pass
    
    def crawl_article(self, url: str, **kwargs) -> Optional[CrawlerResult]:
        """
        爬取单篇文章
        
        Args:
            url: 文章URL
            
        Returns:
            爬取结果
        """
        if self._is_duplicate(url):
            logger.info(f"[{self.name}] 跳过重复URL: {url}")
            return None
        
        try:
            response = self._make_request(url)
            html = response.text
            result = self.parse_detail(html, url)
            
            if result:
                self._add_to_cache(url, result._content_hash)
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] 爬取失败 {url}: {e}")
            return None
    
    def crawl_list(self, list_url: str, **kwargs) -> List[CrawlerResult]:
        """
        爬取列表页
        
        Args:
            list_url: 列表页URL
            
        Returns:
            爬取结果列表
        """
        results = []
        
        try:
            response = self._make_request(list_url)
            html = response.text
            articles = self.parse_list(html, list_url)
            
            logger.info(f"[{self.name}] 从 {list_url} 解析到 {len(articles)} 篇文章")
            
            for article in articles:
                url = article.get('url')
                if not url:
                    continue
                
                # 补全URL
                if url.startswith('/'):
                    parsed_base = urlparse(list_url)
                    url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
                elif not url.startswith('http'):
                    url = urljoin(list_url, url)
                
                result = self.crawl_article(url)
                if result:
                    # 从列表页补充信息
                    result.title = article.get('title', result.title)
                    result.published_at = article.get('published_at', result.published_at)
                    results.append(result)
            
        except Exception as e:
            logger.error(f"[{self.name}] 爬取列表失败 {list_url}: {e}")
        
        return results
    
    def run(self, **kwargs) -> List[CrawlerResult]:
        """
        运行爬虫（主入口）
        
        Returns:
            所有爬取结果
        """
        all_results = []
        
        # 获取列表页URL
        list_urls = self.get_list_urls(**kwargs)
        
        for list_url in list_urls:
            results = self.crawl_list(list_url, **kwargs)
            all_results.extend(results)
        
        logger.info(f"[{self.name}] 爬虫运行完成，共获取 {len(all_results)} 篇文章")
        return all_results
    
    def close(self):
        """关闭爬虫，释放资源"""
        self.session.close()
        logger.info(f"[{self.name}] 爬虫已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False