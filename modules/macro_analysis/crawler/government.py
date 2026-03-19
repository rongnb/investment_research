# -*- coding: utf-8 -*-
"""
政府网站和监管机构爬虫

包含：
- 中国政府网
- 国家发改委
- 财政部
- 工信部
- 央行（中国人民银行）
- 证监会
- 银保监会
- 各地方政府网站
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base import BaseCrawler, CrawlerResult


class ChinaGovernmentCrawler(BaseCrawler):
    """中国政府网爬虫"""
    
    name = "china_government"
    source_name = "中国政府网"
    source_type = "government"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        base_url = "https://www.gov.cn"
        
        # 重要栏目
        sections = [
            ("/xinwen/lianbo/guoqigongbao/", "国务院公报"),
            ("/xinwen/yaowen/", "要闻"),
            ("/zhengce/zhengceku/", "政策库"),
            ("/zhengce/chuli/", "政策解读"),
            ("/zhengce/xinwen/", "政策新闻"),
        ]
        
        list_urls = []
        
        for section_path, name in sections:
            list_url = f"{base_url}{section_path}"
            list_urls.append(list_url)
            
            # 分页
            for page in range(2, page_count + 1):
                list_urls.append(f"{list_url}index{page}.htm")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        # 解析不同类型的列表结构
        # 类型1：新闻列表
        news_items = soup.find_all('a', href=True, title=True)
        for item in news_items:
            if item.get('href') and item.get('title'):
                articles.append({
                    'url': item['href'],
                    'title': item['title']
                })
        
        return articles
    
    def parse_detail(self, html: str, detail_url: str) -> Optional[CrawlerResult]:
        """解析详情页"""
        soup = self._parse_html(html)
        
        try:
            # 标题
            title_tag = soup.find('h1', class_='article-title') or \
                       soup.find('h2', class_='article-title') or \
                       soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            # 内容
            content_div = soup.find('div', class_='pages_content') or \
                        soup.find('div', class_='article-content')
            
            if content_div:
                # 清除不需要的标签
                for script in content_div.find_all('script'):
                    script.decompose()
                for style in content_div.find_all('style'):
                    style.decompose()
                
                content = content_div.get_text(strip=True)
            else:
                content = ""
            
            # 发布时间
            time_pattern = r'\d{4}年\d{1,2}月\d{1,2}日'
            time_match = re.search(time_pattern, html)
            published_at = None
            if time_match:
                date_str = time_match.group()
                published_at = datetime.strptime(date_str, '%Y年%m月%d日')
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='policy' if 'zhengce' in detail_url else 'news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class CSRCrawler(BaseCrawler):
    """中国证监会爬虫"""
    
    name = "csrc"
    source_name = "中国证监会"
    source_type = "regulator"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("http://www.csrc.gov.cn/pub/newsite/zjhxwfb/xwdd/", "新闻动态"),
            ("http://www.csrc.gov.cn/pub/newsite/flb/flfg/", "法律法规"),
            ("http://www.csrc.gov.cn/pub/newsite/gzdt/", "工作动态"),
            ("http://www.csrc.gov.cn/pub/newsite/zjhxwfb/qwfb/", "新闻发布"),
            ("http://www.csrc.gov.cn/pub/newsite/zjhxwfb/djhk/", "答记者问"),
            ("http://www.csrc.gov.cn/pub/newsite/zjhxwfb/xwdt/", "新闻通稿"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}/index_{page}.html")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        # 解析证监会网站的列表结构
        list_container = soup.find('div', class_='list')
        if list_container:
            items = list_container.find_all('li')
            for item in items:
                a_tag = item.find('a', href=True)
                if a_tag:
                    # 解析时间
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
            # 标题
            title_tag = soup.find('h1', class_='article-title') or \
                       soup.find('div', class_='h1')
            title = title_tag.get_text(strip=True) if title_tag else "无标题"
            
            # 内容
            content_div = soup.find('div', class_='TRS_Editor') or \
                        soup.find('div', class_='article-content')
            content = ""
            if content_div:
                # 清除不需要的标签
                for script in content_div.find_all('script'):
                    script.decompose()
                for style in content_div.find_all('style'):
                    style.decompose()
                
                content = content_div.get_text(strip=True)
            
            # 发布时间
            time_tags = soup.find_all('span', class_='time')
            published_at = None
            if time_tags:
                time_str = time_tags[0].get_text(strip=True)
                try:
                    published_at = datetime.strptime(time_str, '%Y-%m-%d')
                except:
                    pass
            
            return CrawlerResult(
                title=title,
                content=content,
                url=detail_url,
                source_name=self.source_name,
                source_type=self.source_type,
                content_type='policy' if 'flfg' in detail_url else 'news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class StateCouncilPolicyCrawler(BaseCrawler):
    """国务院政策文件爬虫"""
    
    name = "state_council"
    source_name = "国务院政策文件"
    source_type = "government"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("https://www.gov.cn/zhengce/zhengceku/", "国务院政策文件库"),
            ("https://www.gov.cn/zhengce/content/2025-01/", "2025年政策"),
            ("https://www.gov.cn/zhengce/content/2025-02/", "2025年政策"),
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
        
        # 解析政策库列表
        policy_items = soup.find_all('div', class_='item')
        for item in policy_items:
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
            content_div = soup.find('div', class_='pages_content')
            content = ""
            if content_div:
                content = content_div.get_text(strip=True)
            
            # 发布时间
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
                content_type='policy',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None


class CNMCrawler(BaseCrawler):
    """央行爬虫"""
    
    name = "people_bank"
    source_name = "中国人民银行"
    source_type = "government"
    
    def get_list_urls(self, page_count: int = 2, **kwargs) -> List[str]:
        """获取列表页URL"""
        sections = [
            ("http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html", "新闻"),
            ("http://www.pbc.gov.cn/tiaofasi/144767/index.html", "货币政策"),
            ("http://www.pbc.gov.cn/zhengcehuobisi/144765/index.html", "政策工具"),
            ("http://www.pbc.gov.cn/zhengcehuobisi/144766/index.html", "货币政策执行报告"),
            ("http://www.pbc.gov.cn/diaochatongji/146212/index.html", "统计数据"),
        ]
        
        list_urls = []
        for section_url, name in sections:
            list_urls.append(section_url)
            
            for page in range(2, page_count + 1):
                list_urls.append(f"{section_url}/index{page}.html")
        
        return list_urls
    
    def parse_list(self, html: str, list_url: str) -> List[Dict]:
        """解析列表页"""
        articles = []
        soup = self._parse_html(html)
        
        # 解析央行网站列表
        list_container = soup.find('ul', class_='list')
        if list_container:
            items = list_container.find_all('li')
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
            
            content_div = soup.find('div', class_='TRS_Editor')
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
                content_type='policy' if any(keyword in detail_url for keyword in ['tiaofasi', 'zhengce']) else 'news',
                published_at=published_at
            )
        
        except Exception as e:
            self.logger.error(f"解析详情页失败 {detail_url}: {e}")
            return None
