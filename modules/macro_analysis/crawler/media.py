# -*- coding: utf-8 -*-
"""
官方媒体和财经媒体爬虫

包含：
- 新华社
- 人民网
- 央视新闻
- 中国新闻网
- 中国经济网
- 第一财经
- 证券时报
- 上海证券报
- 证券日报
- 经济观察网
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base import BaseCrawler, CrawlerResult


class XinhuaNewsCrawler(BaseCrawler):
    """新华社爬虫"""
    
    name = "xinhua"
    source_name = "新华社"
    source_type = "state_media"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("https://www.xinhuanet.com/fortune/", "财经"),
            ("https://www.xinhuanet.com/fortune/cjyw/", "财经要闻"),
            ("https://www.xinhuanet.com/fortune/gncj/", "国内财经"),
            ("https://www.xinhuanet.com/fortune/gjcj/", "国际财经"),
            ("https://www.xinhuanet.com/fortune/money/", "金融"),
            ("https://www.xinhuanet.com/fortune/stock/", "股市"),
            ("https://www.xinhuanet.com/fortune/insurance/", "保险"),
            ("https://www.xinhuanet.com/fortune/finance/", "理财"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}index{page}.htm")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        # 解析新华社列表结构
        news_items = soup.find_all('div', class_='title')
        for item in news_items:
            a_tag = item.find('a', href=True)
            if a_tag:
                articles.append({
                    'url': a_tag['href'],
                    'title': a_tag.get_text(strip=True)
                })
        
        return articles
    
    def parse_detail(self, html: str, detail_url: str) -> Optional[CrawlerResult]:
        """解析详情页"""
        soup = self._parse_html(html)
        
        try:
            # 标题
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            # 内容
            content_div = soup.find('div', class_='article-body')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
            
            # 发布时间
            time_tag = soup.find('span', class_='time')
            published_at = None
            if time_tag:
                time_str = time_tag.get_text(strip=True)
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', time_str)
                if match:
                    published_at = datetime.strptime(match.group(1), '%Y年%m月%d日')
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class PeopleDailyCrawler(BaseCrawler):
    """人民网爬虫"""
    
    name = "people_daily"
    source_name = "人民网"
    source_type = "state_media"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("http://finance.people.com.cn/", "财经"),
            ("http://finance.people.com.cn/n1/2025/0101/c1004-36945678.html", "财经要闻"),
            ("http://finance.people.com.cn/n1/2025/0101/c1004-36945678.html", "宏观经济"),
            ("http://finance.people.com.cn/n1/2025/0101/c1004-36945678.html", "金融"),
            ("http://finance.people.com.cn/n1/2025/0101/c1004-36945678.html", "股票"),
            ("http://finance.people.com.cn/n1/2025/0101/c1004-36945678.html", "基金"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}index{page}.html")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        list_items = soup.find_all('div', class_='list_item')
        for item in list_items:
            a_tag = item.find('a', href=True)
            if a_tag:
                articles.append({
                    'url': a_tag['href'],
                    'title': a_tag.get_text(strip=True)
                })
        
        return articles
    
    def parse_detail(self, html: str, detail_url: str) -> Optional[CrawlerResult]:
        """解析详情页"""
        soup = self._parse_html(html)
        
        try:
            title_tag = soup.find('h1', class_='article_title')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            content_div = soup.find('div', class_='article_text')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
            
            time_tag = soup.find('span', class_='article_time')
            published_at = None
            if time_tag:
                time_str = time_tag.get_text(strip=True)
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', time_str)
                if match:
                    published_at = datetime.strptime(match.group(1), '%Y年%m月%d日')
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class CCTVNewsCrawler(BaseCrawler):
    """央视新闻爬虫"""
    
    name = "cctv_news"
    source_name = "央视新闻"
    source_type = "state_media"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("https://news.cctv.com/finance/", "财经"),
            ("https://news.cctv.com/finance/gjcj/", "国际财经"),
            ("https://news.cctv.com/finance/gncj/", "国内财经"),
            ("https://news.cctv.com/finance/jinrong/", "金融"),
            ("https://news.cctv.com/finance/gupiao/", "股票"),
            ("https://news.cctv.com/finance/jijin/", "基金"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}index{page}.html")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        news_items = soup.find_all('a', href=True, class_='news-link')
        for item in news_items:
            articles.append({
                'url': item['href'],
                'title': item.get_text(strip=True)
            })
        
        return articles
    
    def parse_detail(self, html: str, detail_url: str) -> Optional[CrawlerResult]:
        """解析详情页"""
        soup = self._parse_html(html)
        
        try:
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            content_div = soup.find('div', class_='article-content')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
            
            time_tag = soup.find('span', class_='article-time')
            published_at = None
            if time_tag:
                time_str = time_tag.get_text(strip=True)
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', time_str)
                if match:
                    published_at = datetime.strptime(match.group(1), '%Y年%m月%d日')
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class ChinaEconomicNetCrawler(BaseCrawler):
    """中国经济网爬虫"""
    
    name = "ceenet"
    source_name = "中国经济网"
    source_type = "financial_media"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("https://www.ce.cn/economy/", "经济"),
            ("https://www.ce.cn/economy/gnjj/", "国内经济"),
            ("https://www.ce.cn/economy/gjjj/", "国际经济"),
            ("https://www.ce.cn/money/", "金融"),
            ("https://www.ce.cn/money/bank/", "银行"),
            ("https://www.ce.cn/money/insurance/", "保险"),
            ("https://www.ce.cn/stock/", "股票"),
            ("https://www.ce.cn/stock/ssgs/", "上市公司"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}index{page}.shtml")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        items = soup.find_all('li', class_='list-item')
        for item in items:
            a_tag = item.find('a', href=True)
            if a_tag:
                time_tag = item.find('span', class_='time')
                published_at = None
                if time_tag:
                    time_str = time_tag.get_text(strip=True)
                    try:
                        published_at = datetime.strptime(time_str, '%Y-%m-%d')
                    except:
                        pass
                
                articles.append({
                    'url': a_tag['href'],
                    'title': a_tag.get_text(strip=True),
                    'published_at': published_at
                })
        
        return articles
    
    def parse_detail(self, html: str, detail_url: str) -> Optional[CrawlerResult]:
        """解析详情页"""
        soup = self._parse_html(html)
        
        try:
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            content_div = soup.find('div', class_='article-body')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
            
            time_tag = soup.find('span', class_='publish-time')
            published_at = None
            if time_tag:
                time_str = time_tag.get_text(strip=True)
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', time_str)
                if match:
                    published_at = datetime.strptime(match.group(1), '%Y年%m月%d日')
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None
