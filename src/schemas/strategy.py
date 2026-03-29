"""
投资策略 Pydantic schemas
"""
from datetime import datetime
from typing import Optional
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
