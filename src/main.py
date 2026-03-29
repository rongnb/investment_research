"""
投资管理系统 - FastAPI 主入口
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import strategies, portfolio
from .core.config import settings
from .db.base import engine, Base


# 创建数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动
    print(f"🚀 Invest Management API starting up...")
    yield
    # 关闭
    print(f"🛑 Invest Management API shutting down...")


app = FastAPI(
    title="Invest Management API",
    description="投资策略研究与组合管理API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(strategies.router, prefix="/api/strategies", tags=["投资策略"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["投资组合"])


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """健康检查"""
    return JSONResponse({
        "status": "ok",
        "version": "0.1.0",
        "message": "Invest Management API is running"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
