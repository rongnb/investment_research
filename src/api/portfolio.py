"""
投资组合API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.models.portfolio import Portfolio, Holding
from src.schemas.portfolio import PortfolioCreate, PortfolioResponse, HoldingCreate, HoldingResponse

router = APIRouter()


@router.get("/", response_model=List[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db)):
    """获取所有投资组合"""
    portfolios = db.query(Portfolio).all()
    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """获取投资组合详情"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """创建新投资组合"""
    db_portfolio = Portfolio(**portfolio.model_dump())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse)
def add_holding(
    portfolio_id: int,
    holding: HoldingCreate,
    db: Session = Depends(get_db)
):
    """添加持仓"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db_holding = Holding(**holding.model_dump(), portfolio_id=portfolio_id)
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.delete("/{portfolio_id}/holdings/{holding_id}")
def delete_holding(
    portfolio_id: int,
    holding_id: int,
    db: Session = Depends(get_db)
):
    """删除持仓"""
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.portfolio_id == portfolio_id
    ).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    db.delete(holding)
    db.commit()
    return {"status": "ok", "message": "Holding deleted"}


@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """删除投资组合"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(portfolio)
    db.commit()
    return {"status": "ok", "message": "Portfolio deleted"}
