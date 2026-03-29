"""
投资策略数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from src.db.base import Base


class InvestmentStrategy(Base):
    """投资策略"""
    __tablename__ = "investment_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="策略名称")
    description = Column(Text, nullable=True, comment="策略描述")
    category = Column(String(100), nullable=True, comment="策略分类")
    
    # 策略参数
    parameters = Column(Text, nullable=True, comment="策略参数(JSON)")
    
    # 回测结果
    backtest_start_date = Column(DateTime, nullable=True)
    backtest_end_date = Column(DateTime, nullable=True)
    total_return = Column(Float, nullable=True, comment="总收益%")
    annual_return = Column(Float, nullable=True, comment="年化收益%")
    sharpe_ratio = Column(Float, nullable=True, comment="夏普比率")
    max_drawdown = Column(Float, nullable=True, comment="最大回撤%")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InvestmentStrategy {self.name}>"
