"""
投资策略 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    parameters: Optional[str] = None


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    parameters: Optional[str] = None
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    id: int
    backtest_start_date: Optional[datetime]
    backtest_end_date: Optional[datetime]
    total_return: Optional[float]
    annual_return: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BacktestResultBase(BaseModel):
    strategy_id: int
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    parameters_used: Optional[str] = None
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    total_trades: Optional[int] = None
    drawdown_duration: Optional[int] = None
    transaction_costs: Optional[float] = None
    equity_curve: Optional[str] = None
    note: Optional[str] = None


class BacktestResultCreate(BacktestResultBase):
    pass


class BacktestResultResponse(BacktestResultBase):
    id: int
    created_at: datetime
    strategy_name: Optional[str] = None
    
    class Config:
        from_attributes = True
