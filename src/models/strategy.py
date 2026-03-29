"""
投资策略数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
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
    
    # 关系：一个策略有多个回测结果
    backtest_results = relationship("BacktestResult", back_populates="strategy")
    
    def __repr__(self):
        return f"<InvestmentStrategy {self.name}>"


class BacktestResult(Base):
    """保存的历史回测结果"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("investment_strategies.id"), nullable=False)
    symbol = Column(String(50), nullable=False, comment="回测标的代码")
    
    # 回测参数
    start_date = Column(DateTime, nullable=True, comment="回测起始日期")
    end_date = Column(DateTime, nullable=True, comment="回测结束日期")
    parameters_used = Column(Text, nullable=True, comment="使用的策略参数(JSON)")
    
    # 回测结果指标
    total_return = Column(Float, nullable=True, comment="总收益%")
    annual_return = Column(Float, nullable=True, comment="年化收益%")
    sharpe_ratio = Column(Float, nullable=True, comment="夏普比率")
    max_drawdown = Column(Float, nullable=True, comment="最大回撤%")
    volatility = Column(Float, nullable=True, comment="波动率")
    
    # 完整权益曲线数据(JSON)
    equity_curve = Column(Text, nullable=True, comment="权益曲线数据(JSON)")
    
    note = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, comment="回测时间")
    
    # 关系：回测属于某个策略
    strategy = relationship("InvestmentStrategy", back_populates="backtest_results")
    
    def __repr__(self):
        return f"<BacktestResult strategy={self.strategy_id} symbol={self.symbol} id={self.id}>"
