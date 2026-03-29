"""
投资组合 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class HoldingBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: float
    cost_basis: float
    current_price: Optional[float] = None
    asset_type: str = "stock"


class HoldingCreate(HoldingBase):
    pass


class HoldingResponse(HoldingBase):
    id: int
    portfolio_id: int
    total_cost: Optional[float]
    market_value: Optional[float]
    gain_loss: Optional[float]
    gain_loss_percent: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    cash: float = 0.0


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime
    holdings: List[HoldingResponse] = []
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    """投资组合汇总统计"""
    portfolio_id: int
    name: str
    cash: float
    holding_count: int
    total_cost: float
    total_market_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    
    class Config:
        from_attributes = True
