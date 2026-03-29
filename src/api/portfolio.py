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


@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: int, db: Session = Depends(get_db)):
    """获取投资组合汇总统计（总成本、总市值、总收益等）"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    holdings = portfolio.holdings
    
    total_cost = 0.0
    total_market_value = 0.0
    total_gain_loss = 0.0
    
    for holding in holdings:
        tc = holding.total_cost
        tm = holding.market_value if holding.market_value is not None else tc
        gl = holding.gain_loss if holding.gain_loss is not None else 0.0
        
        total_cost += tc
        total_market_value += tm
        total_gain_loss += gl
    
    # 加上现金
    total_market_value += portfolio.cash
    total_cost += portfolio.cash
    
    total_gain_loss_percent = 0.0
    if total_cost > 0:
        total_gain_loss_percent = (total_gain_loss / total_cost) * 100
    
    return {
        "portfolio_id": portfolio_id,
        "name": portfolio.name,
        "cash": portfolio.cash,
        "holding_count": len(holdings),
        "total_cost": round(total_cost, 2),
        "total_market_value": round(total_market_value, 2),
        "total_gain_loss": round(total_gain_loss, 2),
        "total_gain_loss_percent": round(total_gain_loss_percent, 2)
    }


@router.post("/{portfolio_id}/update-prices")
def update_all_holding_prices(portfolio_id: int, db: Session = Depends(get_db)):
    """更新投资组合内所有持仓的当前价格（触发价格更新）"""
    from src.services.data_fetcher import get_a_stock_daily, get_us_stock_daily
    from datetime import datetime, timedelta
    
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    updated = 0
    errors = []
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    for holding in portfolio.holdings:
        try:
            if holding.asset_type == "stock" and len(holding.symbol) == 6:
                # A股
                df = get_a_stock_daily(holding.symbol, 
                                      start_date.replace("-", ""), 
                                      end_date.replace("-", ""))
                if not df.empty:
                    latest_close = df.iloc[-1]["close"]
                    holding.current_price = float(latest_close)
                    updated += 1
            elif holding.asset_type in ["stock", "etf"]:
                # 美股
                df = get_us_stock_daily(holding.symbol, start_date, end_date)
                if not df.empty:
                    latest_close = df.iloc[-1]["close"]
                    holding.current_price = float(latest_close)
                    updated += 1
        except Exception as e:
            errors.append({
                "symbol": holding.symbol,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "status": "ok",
        "updated_count": updated,
        "errors": errors
    }
