# -*- coding: utf-8 -*-
"""
宏观分析API路由

提供爬虫管理、数据分析、结果查询等API接口
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from ..crawler.scheduler import CrawlerManager
from ..analyzer.policy import PolicyAnalyzer
from ..analyzer.sentiment import SentimentAnalyzer
from ..database import get_db_session


router = APIRouter(prefix="/macro-analysis", tags=["macro-analysis"])

# 全局管理实例
crawler_manager = CrawlerManager()
policy_analyzer = PolicyAnalyzer()
sentiment_analyzer = SentimentAnalyzer()


class CrawlerTaskResponse(BaseModel):
    """爬虫任务响应模型"""
    name: str
    status: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    total_runs: int
    success_count: int
    failure_count: int
    articles_fetched: int
    articles_saved: int
    avg_processing_time: float
    last_error: Optional[str]
    
    class Config:
        from_attributes = True


class CrawlerStatsResponse(BaseModel):
    """爬虫统计响应模型"""
    total_tasks: int
    running_tasks: int
    pending_tasks: int
    failed_tasks: int
    total_runs: int
    total_articles: int
    tasks: List[CrawlerTaskResponse]


class NewsArticleResponse(BaseModel):
    """新闻文章响应模型"""
    id: int
    title: str
    content: str
    summary: Optional[str]
    source_name: str
    source_type: str
    content_type: str
    category: Optional[str]
    tags: Optional[List[str]]
    published_at: datetime
    crawled_at: datetime
    
    class Config:
        from_attributes = True


class SentimentResultResponse(BaseModel):
    """情感分析结果响应模型"""
    overall: int
    overall_score: float
    market_sentiment: float
    policy_sentiment: float
    sector_sentiment: float
    positive_keywords: List[str]
    negative_keywords: List[str]
    neutral_keywords: List[str]
    confidence: float
    method: str


class PolicyAnalysisResultResponse(BaseModel):
    """政策分析结果响应模型"""
    title: str
    content: str
    policy_type: str
    policy_level: str
    urgency_level: int
    key_points: List[Dict]
    affected_sectors: List[Dict]
    implementation_timeline: List[Dict]
    related_policies: List[str]
    confidence: float
    analysis_method: str


@router.get("/health", summary="健康检查")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "macro_analysis"}


@router.get("/crawler/stats", summary="获取爬虫统计信息", response_model=CrawlerStatsResponse)
def get_crawler_stats():
    """获取爬虫系统统计信息"""
    stats = crawler_manager.scheduler.get_stats()
    return stats


@router.get("/crawler/tasks", summary="获取所有爬虫任务", response_model=List[CrawlerTaskResponse])
def get_all_tasks():
    """获取所有爬虫任务列表"""
    tasks = crawler_manager.scheduler.get_all_tasks()
    return [task.get_stats() for task in tasks]


@router.get("/crawler/tasks/{task_name}", summary="获取爬虫任务详情", 
            response_model=CrawlerTaskResponse)
def get_task(task_name: str):
    """获取单个爬虫任务详情"""
    task = crawler_manager.scheduler.get_task(task_name)
    if task:
        return task.get_stats()
    raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")


@router.post("/crawler/tasks/{task_name}/run", summary="运行爬虫任务")
def run_task(task_name: str):
    """立即运行指定的爬虫任务"""
    task = crawler_manager.scheduler.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_name} 不存在")
    
    try:
        crawler_manager.run_immediate_crawl([task_name])
        return {"success": True, "message": f"任务 '{task_name}' 启动成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/crawler/tasks/run-all", summary="运行所有爬虫任务")
def run_all_tasks():
    """立即运行所有爬虫任务"""
    try:
        crawler_manager.run_immediate_crawl()
        return {"success": True, "message": "所有爬虫任务启动成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.get("/articles", summary="获取新闻文章列表", response_model=List[NewsArticleResponse])
def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: Optional[str] = None,
    content_type: Optional[str] = None,
    category: Optional[str] = None,
    published_from: Optional[datetime] = None,
    published_to: Optional[datetime] = None
):
    """获取新闻文章列表"""
    db = get_db_session()
    
    try:
        query = db.query(NewsArticle).filter(NewsArticle.is_deleted == False)
        
        if source_type:
            query = query.filter(NewsArticle.source_type == source_type)
        
        if content_type:
            query = query.filter(NewsArticle.content_type == content_type)
        
        if category:
            query = query.filter(NewsArticle.category == category)
        
        if published_from:
            query = query.filter(NewsArticle.published_at >= published_from)
        
        if published_to:
            query = query.filter(NewsArticle.published_at <= published_to)
        
        # 分页
        total_count = query.count()
        articles = query.order_by(NewsArticle.published_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
        
        return articles
    finally:
        db.close()


@router.get("/articles/{article_id}", summary="获取文章详情", 
            response_model=NewsArticleResponse)
def get_article(article_id: int):
    """获取文章详情"""
    db = get_db_session()
    
    try:
        article = db.query(NewsArticle).filter(
            NewsArticle.id == article_id,
            NewsArticle.is_deleted == False
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        return article
    finally:
        db.close()


@router.post("/articles/{article_id}/analyze-sentiment", 
            summary="分析文章情感", response_model=SentimentResultResponse)
def analyze_article_sentiment(article_id: int):
    """分析文章情感"""
    db = get_db_session()
    
    try:
        article = db.query(NewsArticle).filter(
            NewsArticle.id == article_id,
            NewsArticle.is_deleted == False
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 执行情感分析
        result = sentiment_analyzer.analyze(article.content)
        
        return {
            "overall": result.overall.value,
            "overall_score": result.overall_score,
            "market_sentiment": result.market_sentiment,
            "policy_sentiment": result.policy_sentiment,
            "sector_sentiment": result.sector_sentiment,
            "positive_keywords": result.positive_keywords,
            "negative_keywords": result.negative_keywords,
            "neutral_keywords": result.neutral_keywords,
            "confidence": result.confidence,
            "method": result.method
        }
    finally:
        db.close()


@router.post("/articles/{article_id}/analyze-policy", 
            summary="分析文章政策", response_model=PolicyAnalysisResultResponse)
def analyze_article_policy(article_id: int):
    """分析文章政策内容"""
    db = get_db_session()
    
    try:
        article = db.query(NewsArticle).filter(
            NewsArticle.id == article_id,
            NewsArticle.is_deleted == False
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 执行政策分析
        result = policy_analyzer.analyze(article.title, article.content)
        
        return {
            "title": result.title,
            "content": result.content,
            "policy_type": result.policy_type,
            "policy_level": result.policy_level,
            "urgency_level": result.urgency_level,
            "key_points": [
                {"key": kp.key, "content": kp.content, "importance": kp.importance, "keywords": kp.keywords}
                for kp in result.key_points
            ],
            "affected_sectors": [
                {"sector": imp.sector, "impact_score": imp.impact_score, 
                 "duration": imp.duration, "confidence": imp.confidence}
                for imp in result.affected_sectors
            ],
            "implementation_timeline": [
                {"time": time, "description": desc} 
                for time, desc in result.implementation_timeline
            ],
            "related_policies": result.related_policies,
            "confidence": result.confidence,
            "analysis_method": result.analysis_method
        }
    finally:
        db.close()


@router.post("/analyze/text/sentiment", summary="文本情感分析", 
            response_model=SentimentResultResponse)
def analyze_text_sentiment(text: str):
    """分析文本情感"""
    try:
        result = sentiment_analyzer.analyze(text)
        return {
            "overall": result.overall.value,
            "overall_score": result.overall_score,
            "market_sentiment": result.market_sentiment,
            "policy_sentiment": result.policy_sentiment,
            "sector_sentiment": result.sector_sentiment,
            "positive_keywords": result.positive_keywords,
            "negative_keywords": result.negative_keywords,
            "neutral_keywords": result.neutral_keywords,
            "confidence": result.confidence,
            "method": result.method
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze/text/policy", summary="文本政策分析", 
            response_model=PolicyAnalysisResultResponse)
def analyze_text_policy(title: str, content: str):
    """分析文本政策内容"""
    try:
        result = policy_analyzer.analyze(title, content)
        return {
            "title": result.title,
            "content": result.content,
            "policy_type": result.policy_type,
            "policy_level": result.policy_level,
            "urgency_level": result.urgency_level,
            "key_points": [
                {"key": kp.key, "content": kp.content, "importance": kp.importance, "keywords": kp.keywords}
                for kp in result.key_points
            ],
            "affected_sectors": [
                {"sector": imp.sector, "impact_score": imp.impact_score, 
                 "duration": imp.duration, "confidence": imp.confidence}
                for imp in result.affected_sectors
            ],
            "implementation_timeline": [
                {"time": time, "description": desc} 
                for time, desc in result.implementation_timeline
            ],
            "related_policies": result.related_policies,
            "confidence": result.confidence,
            "analysis_method": result.analysis_method
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
