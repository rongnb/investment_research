# -*- coding: utf-8 -*-
"""
爬虫调度器

负责管理和调度多个爬虫任务，支持定时运行和监控
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .base import BaseCrawler
from .government import (
    ChinaGovernmentCrawler,
    CSRCrawler,
    StateCouncilPolicyCrawler,
    CNMCrawler
)
from .media import (
    XinhuaNewsCrawler,
    PeopleDailyCrawler,
    CCTVNewsCrawler,
    ChinaEconomicNetCrawler
)


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'           # 待执行
    RUNNING = 'running'           # 运行中
    SUCCESS = 'success'           # 成功
    FAILED = 'failed'            # 失败
    PAUSED = 'paused'            # 暂停
    COMPLETED = 'completed'    # 已完成


class CrawlerTask:
    """爬虫任务类"""
    
    def __init__(self, name: str, crawler_class, 
                 schedule: str = None, config: Dict = None):
        """
        初始化爬虫任务
        
        Args:
            name: 任务名称
            crawler_class: 爬虫类
            schedule: 定时调度配置 (cron表达式)
            config: 爬虫配置
        """
        self.name = name
        self.crawler_class = crawler_class
        self.schedule = schedule
        self.config = config or {}
        
        self.status = TaskStatus.PENDING
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.total_runs = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error: Optional[str] = None
        
        # 统计信息
        self.articles_fetched = 0
        self.articles_saved = 0
        self.avg_processing_time = 0
        self.total_processing_time = 0
    
    def run(self, **kwargs):
        """执行任务"""
        self.status = TaskStatus.RUNNING
        self.last_run = datetime.now()
        self.total_runs += 1
        
        logger.info(f"[{self.name}] 开始执行任务")
        
        start_time = time.time()
        
        try:
            with self.crawler_class(**self.config) as crawler:
                results = crawler.run(**kwargs)
                self.articles_fetched = len(results)
                self.articles_saved = self._save_results(results)
            
            self.status = TaskStatus.SUCCESS
            self.success_count += 1
            logger.info(f"[{self.name}] 任务执行成功，获取 {self.articles_fetched} 篇文章")
        
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.failure_count += 1
            self.last_error = str(e)
            logger.error(f"[{self.name}] 任务执行失败: {e}")
        
        self.total_processing_time = time.time() - start_time
        self.avg_processing_time = self.total_processing_time / self.total_runs
        
        return self.status
    
    def _save_results(self, results: List) -> int:
        """保存结果到数据库"""
        # TODO: 实现结果保存逻辑
        saved_count = 0
        for result in results:
            try:
                # 这里将结果保存到数据库
                saved_count += 1
                logger.debug(f"[{self.name}] 保存: {result.title}")
            except Exception as e:
                logger.error(f"[{self.name}] 保存失败: {e}")
        
        return saved_count
    
    def pause(self):
        """暂停任务"""
        self.status = TaskStatus.PAUSED
    
    def resume(self):
        """恢复任务"""
        self.status = TaskStatus.PENDING
    
    def get_stats(self) -> Dict:
        """获取任务统计信息"""
        return {
            'name': self.name,
            'status': self.status.value,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'total_runs': self.total_runs,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_error': self.last_error,
            'articles_fetched': self.articles_fetched,
            'articles_saved': self.articles_saved,
            'avg_processing_time': self.avg_processing_time,
            'total_processing_time': self.total_processing_time,
        }


class CrawlerScheduler:
    """爬虫调度器"""
    
    # 预定义的爬虫任务配置
    PREDEFINED_TASKS = [
        {
            'name': '中国政府网爬虫',
            'crawler_class': ChinaGovernmentCrawler,
            'schedule': '0 9 * * *',  # 每天早上9点
            'config': {
                'page_count': 2,
                'time_range_hours': 24,
            }
        },
        {
            'name': '证监会爬虫',
            'crawler_class': CSRCrawler,
            'schedule': '0 8 * * *',  # 每天早上8点
            'config': {
                'page_count': 2,
                'time_range_hours': 24,
            }
        },
        {
            'name': '央行爬虫',
            'crawler_class': CNMCrawler,
            'schedule': '0 8:30 * * *',  # 每天早上8:30
            'config': {
                'page_count': 2,
                'time_range_hours': 24,
            }
        },
        {
            'name': '国务院政策爬虫',
            'crawler_class': StateCouncilPolicyCrawler,
            'schedule': '0 10 * * *',  # 每天早上10点
            'config': {
                'page_count': 3,
                'time_range_hours': 72,
            }
        },
        {
            'name': '新华社爬虫',
            'crawler_class': XinhuaNewsCrawler,
            'schedule': '*/30 * * * *',  # 每30分钟
            'config': {
                'page_count': 1,
                'time_range_hours': 6,
            }
        },
        {
            'name': '人民网爬虫',
            'crawler_class': PeopleDailyCrawler,
            'schedule': '*/45 * * * *',  # 每45分钟
            'config': {
                'page_count': 1,
                'time_range_hours': 6,
            }
        },
        {
            'name': '央视新闻爬虫',
            'crawler_class': CCTVNewsCrawler,
            'schedule': '*/30 * * * *',  # 每30分钟
            'config': {
                'page_count': 1,
                'time_range_hours': 6,
            }
        },
        {
            'name': '中国经济网爬虫',
            'crawler_class': ChinaEconomicNetCrawler,
            'schedule': '*/60 * * * *',  # 每60分钟
            'config': {
                'page_count': 1,
                'time_range_hours': 12,
            }
        },
    ]
    
    def __init__(self, config: Dict = None):
        """初始化调度器"""
        self.config = config or {}
        self.tasks: Dict[str, CrawlerTask] = {}
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self._lock = threading.Lock()
        
        # 初始化预定义任务
        self._init_predefined_tasks()
        
        logger.info("调度器初始化完成")
    
    def _init_predefined_tasks(self):
        """初始化预定义任务"""
        for task_config in self.PREDEFINED_TASKS:
            task = CrawlerTask(**task_config)
            self.tasks[task.name] = task
            
            # 如果有调度配置，添加到定时任务
            if task.schedule:
                self._add_scheduled_task(task)
    
    def _add_scheduled_task(self, task: CrawlerTask):
        """添加定时任务到调度器"""
        try:
            trigger = CronTrigger.from_crontab(task.schedule)
            self.scheduler.add_job(
                func=self._run_task_wrapper,
                trigger=trigger,
                args=[task],
                id=task.name,
                name=f"爬虫任务: {task.name}"
            )
            
            task.next_run = trigger.get_next_fire_time(None, datetime.now())
            logger.info(f"添加定时任务: {task.name}")
        
        except Exception as e:
            logger.error(f"创建定时任务失败 {task.name}: {e}")
    
    def _run_task_wrapper(self, task: CrawlerTask):
        """任务执行包装器"""
        try:
            task.run()
        except Exception as e:
            logger.error(f"任务执行失败 {task.name}: {e}")
    
    def add_task(self, name: str, crawler_class, 
                 schedule: str = None, config: Dict = None):
        """
        添加任务
        
        Args:
            name: 任务名称
            crawler_class: 爬虫类
            schedule: 定时配置
            config: 爬虫配置
        """
        with self._lock:
            if name in self.tasks:
                logger.warning(f"任务 {name} 已存在")
                return
            
            task = CrawlerTask(name, crawler_class, schedule, config)
            self.tasks[name] = task
            
            if schedule:
                self._add_scheduled_task(task)
            
            logger.info(f"任务 '{name}' 添加成功")
    
    def remove_task(self, task_name: str):
        """移除任务"""
        with self._lock:
            if task_name in self.tasks:
                self.scheduler.remove_job(task_name)
                del self.tasks[task_name]
                logger.info(f"任务 '{task_name}' 已移除")
    
    def get_task(self, task_name: str) -> Optional[CrawlerTask]:
        """获取任务"""
        return self.tasks.get(task_name)
    
    def get_all_tasks(self) -> List[CrawlerTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def run_task(self, task_name: str, **kwargs):
        """立即运行指定任务"""
        task = self.get_task(task_name)
        if task:
            logger.info(f"立即运行任务: {task_name}")
            task.run(**kwargs)
        else:
            logger.warning(f"任务 {task_name} 不存在")
    
    def run_all_tasks(self, **kwargs):
        """立即运行所有任务"""
        logger.info("开始运行所有爬虫任务")
        
        for task in self.get_all_tasks():
            if task.status != TaskStatus.PAUSED:
                self.run_task(task.name, **kwargs)
    
    def pause_task(self, task_name: str):
        """暂停任务"""
        task = self.get_task(task_name)
        if task:
            task.pause()
            self.scheduler.pause_job(task_name)
            logger.info(f"任务 {task_name} 已暂停")
    
    def resume_task(self, task_name: str):
        """恢复任务"""
        task = self.get_task(task_name)
        if task:
            task.resume()
            self.scheduler.resume_job(task_name)
            logger.info(f"任务 {task_name} 已恢复")
    
    def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            logger.info("调度器已启动")
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("调度器已关闭")
    
    def get_stats(self) -> Dict:
        """获取调度器统计信息"""
        total_runs = sum(task.total_runs for task in self.tasks.values())
        total_articles = sum(task.articles_fetched for task in self.tasks.values())
        
        stats = {
            'total_tasks': len(self.tasks),
            'running_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            'pending_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            'failed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
            'total_runs': total_runs,
            'total_articles': total_articles,
            'tasks': [task.get_stats() for task in self.tasks.values()],
        }
        
        return stats
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        report = []
        report.append("爬虫调度器状态报告")
        report.append("=" * 60)
        
        for task in self.get_all_tasks():
            report.append(f"\n任务: {task.name}")
            report.append(f"状态: {task.status.value}")
            report.append(f"运行次数: {task.total_runs}")
            report.append(f"成功率: {task.success_count}/{task.failure_count}")
            if task.articles_fetched > 0:
                report.append(f"文章获取: {task.articles_saved}/{task.articles_fetched}")
            if task.last_error:
                report.append(f"错误信息: {task.last_error}")
        
        return "\n".join(report)


class CrawlerManager:
    """爬虫管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.scheduler = CrawlerScheduler()
        self._initialized = True
    
    def start_scheduler(self):
        """启动调度器"""
        self.scheduler.start()
    
    def run_immediate_crawl(self, task_names: List[str] = None, **kwargs):
        """立即运行指定任务"""
        if task_names:
            for task_name in task_names:
                self.scheduler.run_task(task_name, **kwargs)
        else:
            self.scheduler.run_all_tasks(**kwargs)
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        return self.scheduler.get_status_report()
    
    def get_task_status(self, task_name: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.scheduler.get_task(task_name)
        return task.get_stats() if task else None
