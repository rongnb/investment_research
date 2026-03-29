"""
投资策略API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.models.strategy import InvestmentStrategy
from src.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate

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
