# -*- coding: utf-8 -*-
"""
数据库模型定义

定义所有数据表结构
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date,
    Boolean, Text, ForeignKey, Index, JSON, DECIMAL
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """股票基本信息"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    market = Column(String(10), nullable=False)  # 沪市/深市
    sector = Column(String(50))
    industry = Column(String(50))
    list_date = Column(Date)
    delisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    prices = relationship("StockPrice", back_populates="stock")
    
    __table_args__ = (
        Index('ix_stocks_sector_industry', 'sector', 'industry'),
    )


class StockPrice(Base):
    """股票价格数据"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(DECIMAL(10, 2))
    high = Column(DECIMAL(10, 2))
    low = Column(DECIMAL(10, 2))
    close = Column(DECIMAL(10, 2))
    volume = Column(DECIMAL(20, 0))
    amount = Column(DECIMAL(20, 2))
    change = Column(DECIMAL(10, 2))
    change_pct = Column(DECIMAL(5, 2))
    frequency = Column(String(10), default='daily')  # daily/weekly/monthly
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    stock = relationship("Stock", back_populates="prices")
    
    __table_args__ = (
        Index('ix_prices_stock_date', 'stock_id', 'date'),
        Index('ix_prices_frequency', 'frequency'),
    )


class MacroIndicator(Base):
    """宏观经济指标"""
    __tablename__ = 'macro_indicators'
    
    id = Column(Integer, primary_key=True)
    indicator_code = Column(String(50), nullable=False, index=True)
    indicator_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, index=True)
    value = Column(DECIMAL(10, 2))
    yoy_change = Column(DECIMAL(10, 2))  # 同比变化
    mom_change = Column(DECIMAL(10, 2))  # 环比变化
    unit = Column(String(20))  # 单位
    frequency = Column(String(10))  # monthly/quarterly/yearly
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('ix_macro_indicator_date', 'indicator_code', 'date'),
    )


class Strategy(Base):
    """策略定义"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50))  # technical/fundamental/macro/combined
    symbols = Column(JSON)  # 关注的股票列表
    parameters = Column(JSON)  # 策略参数
    entry_conditions = Column(JSON)
    exit_conditions = Column(JSON)
    position_sizing = Column(JSON)
    risk_management = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    backtests = relationship("BacktestResult", back_populates="strategy")


class BacktestResult(Base):
    """回测结果"""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    
    # 收益指标
    total_return = Column(DECIMAL(10, 4))  # 总收益
    annual_return = Column(DECIMAL(10, 4))  # 年化收益
    benchmark_return = Column(DECIMAL(10, 4))  # 基准收益
    excess_return = Column(DECIMAL(10, 4))  # 超额收益
    
    # 风险指标
    max_drawdown = Column(DECIMAL(10, 4))  # 最大回撤
    max_drawdown_duration = Column(Integer)  # 回撤持续天数
    volatility = Column(DECIMAL(10, 4))  # 波动率
    
    # 风险调整后收益
    sharpe_ratio = Column(DECIMAL(10, 4))  # 夏普比率
    sortino_ratio = Column(DECIMAL(10, 4))  # 索提诺比率
    calmar_ratio = Column(DECIMAL(10, 4))  # 卡尔马比率
    
    # 交易统计
    total_trades = Column(Integer)  # 总交易次数
    winning_trades = Column(Integer)  # 盈利次数
    losing_trades = Column(Integer)  # 亏损次数
    win_rate = Column(DECIMAL(10, 4))  # 胜率
    avg_profit = Column(DECIMAL(10, 4))  # 平均盈利
    avg_loss = Column(DECIMAL(10, 4))  # 平均亏损
    profit_loss_ratio = Column(DECIMAL(10, 4))  # 盈亏比
    
    # 详细数据
    equity_curve = Column(JSON)  # 权益曲线
    trades = Column(JSON)  # 交易明细
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")


# 数据库版本控制表
class AlembicVersion(Base):
    """数据库迁移版本"""
    __tablename__ = 'alembic_version'
    
    version_num = Column(String(32), primary_key=True)
