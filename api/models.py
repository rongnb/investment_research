# -*- coding: utf-8 -*-
"""
API数据模型

定义API请求和响应的数据结构
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ===== 通用响应模型 =====

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ===== 股票数据模型 =====

class StockDailyData(BaseModel):
    """股票日线数据"""
    date: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    change: Optional[float] = None
    change_pct: Optional[float] = None


class StockInfo(BaseModel):
    """股票基本信息"""
    symbol: str
    name: str
    market: str  # 沪市/深市
    sector: Optional[str] = None
    industry: Optional[str] = None
    list_date: Optional[str] = None


class StockPriceRequest(BaseModel):
    """股票价格查询请求"""
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: str = "daily"  # daily/weekly/monthly


class StockPriceResponse(BaseResponse):
    """股票价格查询响应"""
    symbol: str
    data: List[StockDailyData]


# ===== 宏观数据模型 =====

class MacroIndicator(BaseModel):
    """宏观经济指标"""
    date: str
    indicator_code: str
    indicator_name: str
    value: float
    yoy_change: Optional[float] = None  # 同比变化
    mom_change: Optional[float] = None  # 环比变化


class MacroIndicatorRequest(BaseModel):
    """宏观指标查询请求"""
    indicator_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MacroIndicatorResponse(BaseResponse):
    """宏观指标查询响应"""
    indicator_code: str
    indicator_name: str
    data: List[MacroIndicator]


class EconomicCycleInfo(BaseModel):
    """经济周期信息"""
    current_cycle: str
    confidence: float
    description: str
    indicators: Dict[str, float]
    recommendations: List[str]


class EconomicCycleResponse(BaseResponse):
    """经济周期分析响应"""
    cycle_info: EconomicCycleInfo


# ===== 技术分析模型 =====

class TechnicalIndicatorRequest(BaseModel):
    """技术指标请求"""
    symbol: str
    indicators: List[str]  # ma/macd/rsi/bollinger/fractal等
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    params: Optional[Dict[str, Any]] = None  # 指标参数


class TechnicalIndicatorData(BaseModel):
    """技术指标数据"""
    date: str
    indicator_values: Dict[str, Any]
    signals: Optional[Dict[str, Any]] = None


class TechnicalIndicatorResponse(BaseResponse):
    """技术指标响应"""
    symbol: str
    indicators: List[str]
    data: List[TechnicalIndicatorData]


# ===== 策略与回测模型 =====

class StrategyConfig(BaseModel):
    """策略配置"""
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    parameters: Dict[str, Any] = {}


class BacktestResult(BaseModel):
    """回测结果"""
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    trade_count: int
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_config: StrategyConfig


class BacktestResponse(BaseResponse):
    """回测响应"""
    result: BacktestResult


# ===== 筛选器模型 =====

class StockFilterRequest(BaseModel):
    """股票筛选请求"""
    filters: Dict[str, Any]  # {field: {op: '>', value: 10}}
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    limit: int = 100


class StockFilterResponse(BaseResponse):
    """股票筛选响应"""
    total_count: int
    stocks: List[StockInfo]


# ===== 用户与系统模型 =====

class UserConfig(BaseModel):
    """用户配置"""
    user_id: str
    preferences: Dict[str, Any]
    watchlist: List[str]  # 自选股
    alerts: List[Dict[str, Any]]  # 预警设置


class SystemStatus(BaseModel):
    """系统状态"""
    status: str
    version: str
    uptime: float
    active_connections: int
    cache_status: Dict[str, Any]
    data_sources: List[str]
