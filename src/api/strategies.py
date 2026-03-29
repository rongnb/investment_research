"""
投资策略API
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from src.db.base import get_db
from src.models.strategy import InvestmentStrategy
from src.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate
from src.services.backtest import (
    BuyAndHoldStrategy, 
    DollarCostAveragingStrategy,
    FixedWeightRebalancingStrategy,
    BacktestResult
)
from src.services.data_fetcher import get_stock_data

router = APIRouter()


@router.get("/", response_model=List[StrategyResponse])
def list_strategies(db: Session = Depends(get_db)):
    """获取所有投资策略列表"""
    strategies = db.query(InvestmentStrategy).filter(
        InvestmentStrategy.is_active == True
    ).all()
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """获取单个策略详情"""
    strategy = db.query(InvestmentStrategy).filter(
        InvestmentStrategy.id == strategy_id
    ).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("/", response_model=StrategyResponse)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """创建新策略"""
    db_strategy = InvestmentStrategy(**strategy.model_dump())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """更新策略"""
    db_strategy = db.query(InvestmentStrategy).filter(
        InvestmentStrategy.id == strategy_id
    ).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    for field, value in strategy_update.model_dump(exclude_unset=True).items():
        setattr(db_strategy, field, value)
    
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """软删除策略"""
    db_strategy = db.query(InvestmentStrategy).filter(
        InvestmentStrategy.id == strategy_id
    ).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db_strategy.is_active = False
    db.commit()
    return {"status": "ok", "message": "Strategy deleted"}


@router.post("/{strategy_id}/run-backtest")
def run_backtest(
    strategy_id: int,
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """运行策略回测
    
    Args:
        strategy_id: 策略ID
        symbol: 股票代码（支持 A股 600000 或美股 AAPL）
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
    """
    strategy = db.query(InvestmentStrategy).filter(
        InvestmentStrategy.id == strategy_id
    ).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    try:
        # 获取历史数据
        df = get_stock_data(symbol, start_date, end_date)
        if df.empty or len(df) < 10:
            raise HTTPException(status_code=400, detail="获取数据失败或数据量不足")
        
        # 根据策略名称选择回测方法
        strategy_name_lower = strategy.name.lower()
        if "买入持有" in strategy.name or "buy and hold" in strategy_name_lower:
            strategy_obj = BuyAndHoldStrategy(symbol)
            result = strategy_obj.run(df)
        elif "定投" in strategy.name or "dollar-cost" in strategy_name_lower:
            strategy_obj = DollarCostAveragingStrategy(monthly_investment=1000)
            result = strategy_obj.run(df)
        elif "股债平衡" in strategy.name or "fixed.*weight" in strategy_name_lower:
            # 解析参数，默认50/50
            params = {"stock_weight": 0.5, "bond_weight": 0.5, "rebalance_threshold": 0.05}
            if strategy.parameters:
                import json
                try:
                    params.update(json.loads(strategy.parameters))
                except:
                    pass
            strategy_obj = FixedWeightRebalancingStrategy(
                stock_weight=params.get("stock_weight", 0.5),
                bond_weight=params.get("bond_weight", 0.5),
                rebalance_threshold=params.get("rebalance_threshold", 0.05)
            )
            result = strategy_obj.run(df)  # 债券用模拟
        elif "指数" in strategy.name:
            # 指数投资本质就是买入持有
            strategy_obj = BuyAndHoldStrategy(symbol)
            result = strategy_obj.run(df)
        else:
            # 默认使用买入持有
            strategy_obj = BuyAndHoldStrategy(symbol)
            result = strategy_obj.run(df)
        
        # 更新策略回测结果到数据库
        strategy.total_return = result.total_return
        strategy.annual_return = result.annual_return
        strategy.sharpe_ratio = result.sharpe_ratio
        strategy.max_drawdown = result.max_drawdown
        db.commit()
        
        # 准备权益曲线数据
        equity_data = []
        if result.equity_curve is not None:
            # 降采样，最多返回 500 个点避免数据过大
            if len(result.equity_curve) > 500:
                step = len(result.equity_curve) // 500
                sampled = result.equity_curve.iloc[::step]
            else:
                sampled = result.equity_curve
            
            for date, value in sampled.items():
                equity_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": float(value)
                })
        
        return {
            "status": "ok",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "trades": result.trades,
            "equity_curve": equity_data,
            "start_date": df.index[0].strftime("%Y-%m-%d"),
            "end_date": df.index[-1].strftime("%Y-%m-%d"),
            "trading_days": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")
