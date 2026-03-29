"""
投资组合数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.db.base import Base


class Portfolio(Base):
    """投资组合"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="组合名称")
    description = Column(Text, nullable=True, comment="组合描述")
    cash = Column(Float, default=0.0, comment="现金仓位")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    holdings = relationship("Holding", back_populates="portfolio")
    
    def __repr__(self):
        return f"<Portfolio {self.name}>"


class Holding(Base):
    """持仓"""
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    symbol = Column(String(50), nullable=False, comment="代码")
    name = Column(String(200), nullable=True, comment="名称")
    quantity = Column(Float, nullable=False, comment="数量")
    cost_basis = Column(Float, nullable=False, comment="成本价")
    current_price = Column(Float, nullable=True, comment="当前价格")
    asset_type = Column(String(50), default="stock", comment="资产类型: stock/etf/bond/fund")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    @property
    def total_cost(self):
        return quantity * cost_basis
    
    @property
    def market_value(self):
        if current_price is None:
            return None
        return quantity * current_price
    
    @property
    def gain_loss(self):
        if current_price is None:
            return None
        return (current_price - cost_basis) * quantity
    
    @property
    def gain_loss_percent(self):
        if current_price is None or cost_basis == 0:
            return None
        return ((current_price - cost_basis) / cost_basis) * 100
    
    def __repr__(self):
        return f"<Holding {self.symbol} x{self.quantity}>"
