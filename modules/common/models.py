"""
数据模型定义模块
使用 dataclass 定义投资研究中使用的核心数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import pandas as pd
import numpy as np


class TradeDirection(Enum):
    """交易方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"           # 市价单
    LIMIT = "limit"             # 限价单
    STOP = "stop"               # 止损单
    STOP_LIMIT = "stop_limit"   # 止损限价单


class SignalType(Enum):
    """信号类型"""
    LONG = 1                    # 做多
    SHORT = -1                  # 做空
    HOLD = 0                    # 持有
    EXIT = 2                    # 平仓


class FactorType(Enum):
    """因子类型"""
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    QUALITY = "quality"
    VALUE = "value"
    GROWTH = "growth"
    MOMENTUM = "momentum"


@dataclass
class Stock:
    """股票基础信息"""
    code: str                           # 股票代码
    name: str                           # 股票名称
    market: str                         # 所属市场 (sh/sz/bj/hk/us)
    industry: Optional[str] = None      # 所属行业
    sector: Optional[str] = None        # 所属板块
    list_date: Optional[date] = None    # 上市日期
    total_shares: Optional[float] = None  # 总股本
    float_shares: Optional[float] = None  # 流通股本


@dataclass
class Trade:
    """交易记录"""
    id: str
    code: str
    direction: TradeDirection
    price: float
    volume: int
    amount: float
    timestamp: datetime
    order_type: OrderType = OrderType.MARKET
    commission: float = 0.0
    slippage: float = 0.0


@dataclass
class Position:
    """持仓信息"""
    code: str
    volume: int
    avg_price: float
    current_price: float
    market_value: float
    cost: float
    unrealized_pnl: float
    realized_pnl: float
    open_date: datetime


@dataclass
class Portfolio:
    """投资组合"""
    positions: Dict[str, Position]
    cash: float
    total_value: float
    total_cost: float
    total_pnl: float
    date: datetime


@dataclass
class Factor:
    """选股因子"""
    name: str
    code: str
    factor_type: FactorType
    description: str
    direction: int = 1  # 1: 越大越好, -1: 越小越好
    weight: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Signal:
    """交易信号"""
    code: str
    signal_type: SignalType
    strength: float  # 0-1之间
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BarData:
    """K线数据"""
    code: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    frequency: str = "1d"


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: List[Trade]
    daily_returns: pd.Series
    equity_curve: pd.Series


@dataclass
class ScreeningResult:
    """筛选结果"""
    timestamp: datetime
    total_stocks: int
    filtered_stocks: int
    ranked_stocks: List[Dict[str, Any]]
    factors_used: List[str]
    weights: Dict[str, float]
