# -*- coding: utf-8 -*-
"""
宏观分析数据库模型

定义爬虫数据、政策分析、情感分析等相关数据表
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text,
    Boolean, ForeignKey, Index, JSON, DECIMAL, Enum, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime
import enum

Base = declarative_base()


class SourceType(enum.Enum):
    """信息来源类型"""
    GOVERNMENT = "government"          # 政府部门
    STATE_MEDIA = "state_media"        # 官方媒体
    FINANCIAL_MEDIA = "financial"      # 财经媒体
    EXCHANGE = "exchange"              # 交易所
    REGULATOR = "regulator"            # 监管机构


class ContentType(enum.Enum):
    """内容类型"""
    POLICY = "policy"                  # 政策文件
    ANNOUNCEMENT = "announcement"    # 公告通知
    REPORT = "report"                  # 报告/研报
    SPEECH = "speech"                  # 讲话/发言
    INTERVIEW = "interview"          # 采访/专访
    NEWS = "news"                      # 新闻


class SentimentType(enum.Enum):
    """情感类型"""
    VERY_POSITIVE = 2                  # 非常积极
    POSITIVE = 1                       # 积极
    NEUTRAL = 0                        # 中性
    NEGATIVE = -1                      # 消极
    VERY_NEGATIVE = -2                 # 非常消极


class NewsArticle(Base):
    """新闻文章表"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    
    # 基本信息
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(500))
    content = Column(Text)
    summary = Column(Text)
    
    # 来源信息
    source_type = Column(String(50), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    source_url = Column(String(500))
    source_id = Column(String(100))  # 来源系统的原始ID
    
    # 内容类型
    content_type = Column(String(50), default='news')
    category = Column(String(100))  # 分类
    tags = Column(JSON)  # 标签
    
    # 时间信息
    published_at = Column(DateTime, index=True)
    crawled_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 状态
    is_deleted = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    
    # 关系
    sentiment = relationship("SentimentAnalysis", uselist=False, back_populates="article")
    policy_analysis = relationship("PolicyAnalysis", uselist=False, back_populates="article")
    market_impact = relationship("MarketImpact", uselist=False, back_populates="article")
    
    __table_args__ = (
        Index('ix_news_articles_source_published', 'source_name', 'published_at'),
        Index('ix_news_articles_category_type', 'category', 'content_type'),
    )


class SentimentAnalysis(Base):
    """情感分析表"""
    __tablename__ = 'sentiment_analysis'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False, unique=True)
    
    # 情感分数 (各维度)
    overall_sentiment = Column(Integer)  # 总体情感: -2~2
    market_sentiment = Column(Float)  # 市场情感: -1~1
    policy_sentiment = Column(Float)  # 政策情感
    sector_sentiment = Column(Float)  # 行业情感
    
    # 细粒度情感分析
    positive_keywords = Column(JSON)  # 积极关键词
    negative_keywords = Column(JSON)  # 消极关键词
    neutral_keywords = Column(JSON)  # 中性关键词
    
    # 置信度
    confidence = Column(Float)  # 整体置信度
    method = Column(String(50))  # 分析方法
    model_version = Column(String(50))  # 模型版本
    
    # 时间戳
    analyzed_at = Column(DateTime, default=datetime.now)
    
    # 关系
    article = relationship("NewsArticle", back_populates="sentiment")
    
    __table_args__ = (
        Index('ix_sentiment_overall', 'overall_sentiment', 'analyzed_at'),
    )


class PolicyAnalysis(Base):
    """政策分析表"""
    __tablename__ = 'policy_analysis'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False, unique=True)
    
    # 政策分类
    policy_type = Column(String(50))  # 政策类型: 货币政策/财政政策/产业政策/监管政策
    policy_level = Column(String(20))  # 政策级别: 中央/部委/地方
    urgency_level = Column(Integer)  # 紧急程度: 1-5
    
    # 影响分析
    affected_sectors = Column(JSON)  # 受影响行业
    affected_markets = Column(JSON)  # 受影响市场
    impact_direction = Column(String(20))  # 影响方向: 正面/负面/中性
    impact_duration = Column(String(20))  # 影响周期: 短期/中期/长期
    
    # 政策要点
    key_points = Column(JSON)  # 关键要点
    implementation_timeline = Column(JSON)  # 实施时间表
    responsible_agencies = Column(JSON)  # 负责机构
    
    # 相关文件
    related_documents = Column(JSON)  # 相关文件
    related_policies = Column(JSON)  # 相关政策
    
    # 置信度和方法
    confidence = Column(Float)
    analysis_method = Column(String(50))
    
    # 时间戳
    analyzed_at = Column(DateTime, default=datetime.now)
    
    # 关系
    article = relationship("NewsArticle", back_populates="policy_analysis")
    
    __table_args__ = (
        Index('ix_policy_type_level', 'policy_type', 'policy_level'),
        Index('ix_policy_analyzed_at', 'analyzed_at'),
    )


class MarketImpact(Base):
    """市场影响评估表"""
    __tablename__ = 'market_impacts'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False, unique=True)
    
    # 影响的市场指数
    affected_indices = Column(JSON)  # {'CSI300': 0.8, 'SSE50': 0.6, ...}
    
    # 影响的时间段预测
    short_term_impact = Column(Integer)  # 短期(1-5天)影响: -2~2
    medium_term_impact = Column(Integer)  # 中期(1-4周)影响
    long_term_impact = Column(Integer)  # 长期(1-6月)影响
    
    # 行业影响排序
    sector_impacts = Column(JSON)  # [{'sector': '银行', 'impact': 0.8}, ...]
    
    # 个股影响（重要事件）
    stock_impacts = Column(JSON)  # [{'code': '000001', 'impact': 1.2}, ...]
    
    # 历史相似事件对比
    similar_events = Column(JSON)  # 历史上相似事件及市场表现
    
    # 预测置信度
    prediction_confidence = Column(Float)
    prediction_method = Column(String(50))
    
    # 实际结果跟踪（回填）
    actual_market_reaction = Column(JSON)  # 实际市场反应
    prediction_accuracy = Column(Float)  # 预测准确度
    
    # 时间戳
    assessed_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    article = relationship("NewsArticle", back_populates="market_impact")
    
    __table_args__ = (
        Index('ix_market_impact_confidence', 'prediction_confidence', 'assessed_at'),
    )


class CrawlerTask(Base):
    """爬虫任务表"""
    __tablename__ = 'crawler_tasks'
    
    id = Column(Integer, primary_key=True)
    
    # 任务信息
    task_name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_name = Column(String(100), nullable=False)
    
    # 任务配置
    config = Column(JSON)  # 爬虫配置参数
    schedule = Column(String(50))  # 定时规则 (cron表达式)
    
    # 运行状态
    status = Column(String(20), default='active')  # active/paused/stopped
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    
    # 统计信息
    total_runs = Column(Integer, default=0)
    success_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    logs = relationship("CrawlerLog", back_populates="task")
    
    __table_args__ = (
        Index('ix_crawler_tasks_status', 'status', 'next_run_at'),
        Index('ix_crawler_tasks_source', 'source_type', 'source_name'),
    )


class CrawlerLog(Base):
    """爬虫运行日志表"""
    __tablename__ = 'crawler_logs'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('crawler_tasks.id'), nullable=False)
    
    # 运行信息
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)  # 运行时长
    
    # 运行结果
    status = Column(String(20))  # success/partial/failed
    articles_fetched = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # 错误详情
    error_messages = Column(JSON)
    
    # 关系
    task = relationship("CrawlerTask", back_populates="logs")
    
    __table_args__ = (
        Index('ix_crawler_logs_task_time', 'task_id', 'started_at'),
        Index('ix_crawler_logs_status', 'status', 'started_at'),
    )


# 数据库会话管理
engine = None
Session = None


def init_db(database_url: str = None):
    """初始化数据库"""
    from sqlalchemy import create_engine
    
    global engine, Session
    
    if database_url is None:
        database_url = "sqlite:///data/macro_analysis.db"
    
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    
    Session = scoped_session(sessionmaker(bind=engine))
    
    return Session


def get_db_session():
    """获取数据库会话"""
    if Session is None:
        init_db()
    return Session()
