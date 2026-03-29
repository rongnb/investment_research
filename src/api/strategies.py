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
    MovingAverageCrossoverStrategy,
    GrahamDefensiveStrategy,
    Momentum12MonthStrategy,
    LowVolatilityStrategy,
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


@router.get("/cache/info")
def cache_info():
    """获取数据缓存信息"""
    from src.services.data_fetcher import cache_info
    return cache_info()


@router.post("/cache/clear")
def cache_clear():
    """清除所有数据缓存"""
    from src.services.data_fetcher import clear_cache
    count = clear_cache()
    return {"status": "ok", "cleared_files": count}


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
        elif "均线" in strategy.name or "moving" in strategy_name_lower or "crossover" in strategy_name_lower:
            # 解析参数，默认20/60
            params = {"short_window": 20, "long_window": 60}
            if strategy.parameters:
                import json
                try:
                    params.update(json.loads(strategy.parameters))
                except:
                    pass
            strategy_obj = MovingAverageCrossoverStrategy(
                short_window=params.get("short_window", 20),
                long_window=params.get("long_window", 60)
            )
            result = strategy_obj.run(df)
        elif "格雷厄姆" in strategy.name or "defensive" in strategy_name_lower:
            # 解析参数，默认 PE<15 PB<1.5
            params = {"pe_threshold": 15, "pb_threshold": 1.5}
            if strategy.parameters:
                import json
                try:
                    params.update(json.loads(strategy.parameters))
                except:
                    pass
            strategy_obj = GrahamDefensiveStrategy(
                pe_threshold=params.get("pe_threshold", 15),
                pb_threshold=params.get("pb_threshold", 1.5)
            )
            result = strategy_obj.run(df)
        elif "动量" in strategy.name or "momentum" in strategy_name_lower:
            # 解析参数，默认12个月(252交易日)
            params = {"momentum_window": 252}
            if strategy.parameters:
                import json
                try:
                    params.update(json.loads(strategy.parameters))
                except:
                    pass
            strategy_obj = Momentum12MonthStrategy(
                momentum_window=params.get("momentum_window", 252)
            )
            result = strategy_obj.run(df)
        elif "波动" in strategy.name or "volatility" in strategy_name_lower:
            # 解析参数，默认20窗口 2%阈值
            params = {"volatility_window": 20, "volatility_threshold": 0.02}
            if strategy.parameters:
                import json
                try:
                    params.update(json.loads(strategy.parameters))
                except:
                    pass
            strategy_obj = LowVolatilityStrategy(
                volatility_window=params.get("volatility_window", 20),
                volatility_threshold=params.get("volatility_threshold", 0.02)
            )
            result = strategy_obj.run(df)
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
        if start_date:
            from datetime import datetime
            strategy.backtest_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            from datetime import datetime
            strategy.backtest_end_date = datetime.strptime(end_date, "%Y-%m-%d")
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
        
        # 自动保存回测结果到数据库
        from src.models.strategy import BacktestResult
        import json
        
        # 转换为JSON字符串保存
        equity_curve_json = json.dumps(equity_data)
        params_used_json = strategy.parameters if strategy.parameters else "{}"
        
        # 转换日期
        saved_start_date = None
        saved_end_date = None
        if start_date:
            from datetime import datetime
            saved_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            from datetime import datetime
            saved_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        if not start_date and len(df) > 0:
            saved_start_date = df.index[0].to_pydatetime()
        if not end_date and len(df) > 0:
            saved_end_date = df.index[-1].to_pydatetime()
        
        # 创建保存记录
        saved_result = BacktestResult(
            strategy_id=strategy_id,
            symbol=symbol,
            start_date=saved_start_date,
            end_date=saved_end_date,
            parameters_used=params_used_json,
            total_return=result.total_return,
            annual_return=result.annual_return,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            volatility=getattr(result, 'volatility', None),
            equity_curve=equity_curve_json,
        )
        db.add(saved_result)
        db.commit()
        
        return {
            "status": "ok",
            "saved_result_id": saved_result.id,
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


@router.post("/compare")
def compare_strategies(
    symbol: str,
    strategy_ids: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """对比多个策略在同一标的上的回测结果
    
    Args:
        symbol: 股票代码
        strategy_ids: 逗号分隔的策略ID列表，如 "1,2,3"
        start_date: 起始日期
        end_date: 结束日期
    """
    # 解析策略ID列表
    strategy_id_list = [int(sid.strip()) for sid in strategy_ids.split(",") if sid.strip()]
    if len(strategy_id_list) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择两个策略进行对比")
    
    try:
        # 获取数据一次，所有策略共用
        df = get_stock_data(symbol, start_date, end_date)
        if df.empty or len(df) < 10:
            raise HTTPException(status_code=400, detail="获取数据失败或数据量不足")
        
        results = []
        for sid in strategy_id_list:
            strategy = db.query(InvestmentStrategy).filter(
                InvestmentStrategy.id == sid
            ).first()
            if not strategy:
                continue
                
            # 根据策略选择回测方法
            strategy_name_lower = strategy.name.lower()
            if "买入持有" in strategy.name or "buy and hold" in strategy_name_lower:
                strategy_obj = BuyAndHoldStrategy(symbol)
                result = strategy_obj.run(df)
            elif "定投" in strategy.name or "dollar-cost" in strategy_name_lower:
                strategy_obj = DollarCostAveragingStrategy(monthly_investment=1000)
                result = strategy_obj.run(df)
            elif "股债平衡" in strategy.name or "fixed.*weight" in strategy_name_lower:
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
                result = strategy_obj.run(df)
            elif "均线" in strategy.name or "moving" in strategy_name_lower:
                params = {"short_window": 20, "long_window": 60}
                if strategy.parameters:
                    import json
                    try:
                        params.update(json.loads(strategy.parameters))
                    except:
                        pass
                strategy_obj = MovingAverageCrossoverStrategy(
                    short_window=params.get("short_window", 20),
                    long_window=params.get("long_window", 60)
                )
                result = strategy_obj.run(df)
            elif "格雷厄姆" in strategy.name or "defensive" in strategy_name_lower:
                params = {"pe_threshold": 15, "pb_threshold": 1.5}
                if strategy.parameters:
                    import json
                    try:
                        params.update(json.loads(strategy.parameters))
                    except:
                        pass
                strategy_obj = GrahamDefensiveStrategy(
                    pe_threshold=params.get("pe_threshold", 15),
                    pb_threshold=params.get("pb_threshold", 1.5)
                )
                result = strategy_obj.run(df)
            elif "动量" in strategy.name or "momentum" in strategy_name_lower:
                params = {"momentum_window": 252}
                if strategy.parameters:
                    import json
                    try:
                        params.update(json.loads(strategy.parameters))
                    except:
                        pass
                strategy_obj = Momentum12MonthStrategy(
                    momentum_window=params.get("momentum_window", 252)
                )
                result = strategy_obj.run(df)
            elif "波动" in strategy.name or "volatility" in strategy_name_lower:
                params = {"volatility_window": 20, "volatility_threshold": 0.02}
                if strategy.parameters:
                    import json
                    try:
                        params.update(json.loads(strategy.parameters))
                    except:
                        pass
                strategy_obj = LowVolatilityStrategy(
                    volatility_window=params.get("volatility_window", 20),
                    volatility_threshold=params.get("volatility_threshold", 0.02)
                )
                result = strategy_obj.run(df)
            else:
                strategy_obj = BuyAndHoldStrategy(symbol)
                result = strategy_obj.run(df)
            
            # 准备权益曲线数据
            equity_data = []
            if result.equity_curve is not None:
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
            
            results.append({
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "category": strategy.category,
                "total_return": result.total_return,
                "annual_return": result.annual_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "equity_curve": equity_data,
                "trades_count": len(result.trades)
            })
        
        return {
            "status": "ok",
            "symbol": symbol,
            "start_date": df.index[0].strftime("%Y-%m-%d"),
            "end_date": df.index[-1].strftime("%Y-%m-%d"),
            "trading_days": len(df),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比失败: {str(e)}")


# ========== 回测结果保存 API ==========
from src.models.strategy import BacktestResult
from src.schemas.strategy import BacktestResultResponse, BacktestResultCreate


@router.get("/backtest-results", response_model=List[BacktestResultResponse])
def list_backtest_results(
    strategy_id: int = None,
    db: Session = Depends(get_db)
):
    """获取历史回测结果列表"""
    query = db.query(BacktestResult).join(BacktestResult.strategy)
    if strategy_id is not None:
        query = query.filter(BacktestResult.strategy_id == strategy_id)
    
    results = query.order_by(BacktestResult.created_at.desc()).all()
    
    # 添加策略名称到返回结果
    response_list = []
    for result in results:
        response = BacktestResultResponse.model_validate(result)
        if result.strategy:
            response.strategy_name = result.strategy.name
        response_list.append(response)
    
    return response_list


@router.get("/backtest-results/{result_id}", response_model=BacktestResultResponse)
def get_backtest_result(result_id: int, db: Session = Depends(get_db)):
    """获取单个回测结果详情"""
    result = db.query(BacktestResult).filter(
        BacktestResult.id == result_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    response = BacktestResultResponse.model_validate(result)
    if result.strategy:
        response.strategy_name = result.strategy.name
    
    return response


@router.post("/backtest-results", response_model=BacktestResultResponse)
def create_backtest_result(
    result_in: BacktestResultCreate,
    db: Session = Depends(get_db)
):
    """保存回测结果"""
    db_result = BacktestResult(**result_in.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    response = BacktestResultResponse.model_validate(db_result)
    if db_result.strategy:
        response.strategy_name = db_result.strategy.name
    
    return response


@router.delete("/backtest-results/{result_id}")
def delete_backtest_result(result_id: int, db: Session = Depends(get_db)):
    """删除回测结果"""
    result = db.query(BacktestResult).filter(
        BacktestResult.id == result_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    db.delete(result)
    db.commit()
    return {"status": "ok", "message": "Backtest result deleted"}
