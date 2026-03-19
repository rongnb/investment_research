# -*- coding: utf-8 -*-
"""
API路由定义

提供RESTful API端点
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from .models import (
    BaseResponse, ErrorResponse,
    StockPriceRequest, StockPriceResponse, StockDailyData, StockInfo,
    MacroIndicatorRequest, MacroIndicatorResponse, MacroIndicator,
    EconomicCycleResponse, EconomicCycleInfo,
    TechnicalIndicatorRequest, TechnicalIndicatorResponse,
    BacktestRequest, BacktestResponse,
    StockFilterRequest, StockFilterResponse,
    SystemStatus
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title="投资研究系统 API",
        description="提供股票数据、宏观分析、技术分析、策略回测等功能",
        version="1.0.0"
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ===== 系统状态端点 =====
    
    @app.get("/", response_model=Dict[str, str])
    async def root():
        """API根路径"""
        return {
            "message": "投资研究系统 API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    @app.get("/health", response_model=Dict[str, Any])
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    @app.get("/api/v1/system/status", response_model=SystemStatus)
    async def get_system_status():
        """获取系统状态"""
        return SystemStatus(
            status="running",
            version="1.0.0",
            uptime=0.0,
            active_connections=0,
            cache_status={"enabled": True, "size": 0},
            data_sources=["mock"]
        )
    
    # ===== 股票数据端点 =====
    
    @app.get("/api/v1/stocks/{symbol}/price", response_model=StockPriceResponse)
    async def get_stock_price(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "daily"
    ):
        """
        获取股票价格数据
        
        - **symbol**: 股票代码 (如: 000001)
        - **start_date**: 开始日期 (YYYY-MM-DD), 默认为30天前
        - **end_date**: 结束日期 (YYYY-MM-DD), 默认为今天
        - **frequency**: 频率 (daily/weekly/monthly)
        """
        try:
            # 设置默认日期
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
                start_date = start.strftime('%Y-%m-%d')
            
            # 使用模拟数据
            import pandas as pd
            import numpy as np
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            dates = dates[dates.weekday < 5]
            
            np.random.seed(hash(symbol) % 10000)
            n = len(dates)
            returns = np.random.randn(n) * 0.02
            prices = 100 * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'date': dates,
                'symbol': symbol,
                'open': prices * (1 + np.random.randn(n) * 0.01),
                'high': prices * (1 + np.abs(np.random.randn(n)) * 0.02),
                'low': prices * (1 - np.abs(np.random.randn(n)) * 0.02),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, n),
                'amount': prices * np.random.randint(1000000, 10000000, n)
            })
            
            data = []
            for _, row in df.iterrows():
                data.append(StockDailyData(
                    date=row['date'].strftime('%Y-%m-%d'),
                    symbol=row['symbol'],
                    open=round(row['open'], 2),
                    high=round(row['high'], 2),
                    low=round(row['low'], 2),
                    close=round(row['close'], 2),
                    volume=int(row['volume']),
                    amount=round(row['amount'], 2)
                ))
            
            return StockPriceResponse(
                success=True,
                message="success",
                symbol=symbol,
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== 宏观数据端点 =====
    
    @app.get("/api/v1/macro/indicators", response_model=MacroIndicatorResponse)
    async def get_macro_indicators(
        indicator_code: str = Query(..., description="指标代码 (gdp/cpi/ppi/pmi等)"),
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        获取宏观经济指标数据
        
        支持的指标代码：
        - **gdp**: GDP增长率
        - **cpi**: 消费者物价指数
        - **ppi**: 生产者物价指数
        - **pmi**: 制造业PMI
        - **m2**: 货币供应量M2
        """
        try:
            import pandas as pd
            import numpy as np
            
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=365)
                start_date = start.strftime('%Y-%m-%d')
            
            # 生成模拟数据
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
            n = len(dates)
            
            if 'gdp' in indicator_code.lower():
                values = 5 + np.cumsum(np.random.randn(n) * 0.3)
                name = "GDP增长率"
            elif 'cpi' in indicator_code.lower():
                values = 2 + np.cumsum(np.random.randn(n) * 0.2)
                name = "消费者物价指数"
            elif 'pmi' in indicator_code.lower():
                values = 50 + np.cumsum(np.random.randn(n) * 0.5)
                values = np.clip(values, 45, 55)
                name = "制造业PMI"
            else:
                values = np.random.randn(n) * 5
                name = indicator_code
            
            df = pd.DataFrame({
                'date': dates,
                'indicator': indicator_code,
                'indicator_name': name,
                'value': values
            })
            
            data = []
            for _, row in df.iterrows():
                data.append(MacroIndicator(
                    date=row['date'].strftime('%Y-%m-%d'),
                    indicator_code=row['indicator'],
                    indicator_name=row['indicator_name'],
                    value=round(row['value'], 2)
                ))
            
            return MacroIndicatorResponse(
                success=True,
                message="success",
                indicator_code=indicator_code,
                indicator_name=name,
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error fetching macro indicator: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/macro/cycle/analysis", response_model=EconomicCycleResponse)
    async def analyze_economic_cycle(
        current_indicators: Dict[str, float]
    ):
        """
        分析经济周期
        
        输入当前指标值，返回周期判断和投资建议
        """
        try:
            from modules.macro import EconomicCycleAnalyzer, create_default_indicators
            
            if not current_indicators:
                current_indicators = create_default_indicators()
            
            analyzer = EconomicCycleAnalyzer()
            analysis = analyzer.analyze(current_indicators)
            
            return EconomicCycleResponse(
                success=True,
                cycle_info=EconomicCycleInfo(
                    current_cycle=analysis.current_cycle.value,
                    confidence=analysis.confidence,
                    description=f"当前处于{analysis.current_cycle.value}阶段",
                    indicators=analysis.leading_indicators,
                    recommendations=analysis.recommendations[:5]
                )
            )
        except Exception as e:
            logger.error(f"Error analyzing economic cycle: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== 技术分析端点 =====
    
    @app.post("/api/v1/technical/indicators", response_model=TechnicalIndicatorResponse)
    async def calculate_technical_indicators(
        request: TechnicalIndicatorRequest
    ):
        """
        计算技术指标
        
        支持指标：ma/macd/rsi/kdj/bollinger/fractal
        """
        try:
            from modules.common import DataCollector
            from modules.technical import (
                sma, ema, macd, rsi, kdj, bollinger_bands,
                calculate_fractal
            )
            import pandas as pd
            
            # 获取股票数据
            collector = DataCollector.create_data_collector("mock")
            df = collector.get_stock_daily(
                request.symbol,
                request.start_date or (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                request.end_date or datetime.now().strftime('%Y-%m-%d')
            )
            
            if df.empty:
                raise HTTPException(status_code=404, detail="Stock data not found")
            
            # 计算指标
            indicator_data = []
            for indicator in request.indicators:
                if indicator == 'ma':
                    for period in [5, 10, 20, 60]:
                        df[f'ma_{period}'] = sma(df['close'], period)
                elif indicator == 'macd':
                    df['macd'] = macd(df['close'])
                elif indicator == 'rsi':
                    df['rsi'] = rsi(df['close'])
                elif indicator == 'bollinger':
                    upper, middle, lower = bollinger_bands(df['close'])
                    df['bollinger_upper'] = upper
                    df['bollinger_middle'] = middle
                    df['bollinger_lower'] = lower
                elif indicator == 'fractal':
                    df = calculate_fractal(df)
            
            # 转换结果
            for idx, row in df.iterrows():
                values = {}
                for col in df.columns:
                    if col not in ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']:
                        values[col] = row[col]
                
                indicator_data.append({
                    'date': idx.strftime('%Y-%m-%d') if isinstance(idx, datetime) else str(idx),
                    'indicator_values': values,
                    'signals': {}
                })
            
            return TechnicalIndicatorResponse(
                success=True,
                symbol=request.symbol,
                indicators=request.indicators,
                data=indicator_data
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== 回测端点 =====
    
    @app.post("/api/v1/backtest", response_model=BacktestResponse)
    async def run_backtest(request: BacktestRequest):
        """
        运行策略回测
        
        支持多种策略和参数配置
        """
        try:
            # 这里应该调用实际的回测引擎
            # 目前返回模拟数据
            
            import random
            
            result = BacktestResult(
                total_return=random.uniform(0.1, 0.5),
                annual_return=random.uniform(0.08, 0.3),
                max_drawdown=random.uniform(0.1, 0.25),
                sharpe_ratio=random.uniform(0.8, 2.0),
                win_rate=random.uniform(0.4, 0.6),
                profit_loss_ratio=random.uniform(1.2, 2.0),
                trade_count=random.randint(50, 200),
                equity_curve=[],
                trades=[]
            )
            
            return BacktestResponse(
                success=True,
                result=result
            )
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== 股票筛选端点 =====
    
    @app.post("/api/v1/screener", response_model=StockFilterResponse)
    async def screen_stocks(request: StockFilterRequest):
        """
        股票筛选
        
        支持多条件组合筛选
        """
        try:
            # 这里应该调用实际的筛选引擎
            # 目前返回模拟数据
            
            stocks = [
                StockInfo(
                    symbol="000001",
                    name="平安银行",
                    market="深市",
                    sector="金融",
                    industry="银行"
                ),
                StockInfo(
                    symbol="600000",
                    name="浦发银行",
                    market="沪市",
                    sector="金融",
                    industry="银行"
                )
            ]
            
            return StockFilterResponse(
                success=True,
                total_count=len(stocks),
                stocks=stocks
            )
            
        except Exception as e:
            logger.error(f"Error screening stocks: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # 错误处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}")
        return ErrorResponse(
            success=False,
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            detail=str(exc)
        )
    
    return app


# 应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
