# -*- coding: utf-8 -*-
"""
数据库会话管理

提供数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

# 数据库URL，默认使用SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./investment_research.db"
)

# 创建引擎
echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
engine = create_engine(
    DATABASE_URL,
    echo=echo,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """
    获取数据库会话的上下文管理器
    
    使用示例:
        with get_db_session() as db:
            stocks = db.query(Stock).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db():
    """
    获取数据库会话（用于FastAPI依赖注入）
    
    使用示例:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_URL}")


def reset_db():
    """
    重置数据库，删除所有表并重新创建
    
    ⚠️ 警告：这将删除所有数据！
    """
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete")


# 便捷函数

def get_stock_by_symbol(db: Session, symbol: str):
    """根据代码获取股票"""
    from .models import Stock
    return db.query(Stock).filter(Stock.symbol == symbol).first()


def get_stock_prices(
    db: Session,
    symbol: str,
    start_date: str,
    end_date: str
):
    """获取股票价格数据"""
    from .models import Stock, StockPrice
    stock = get_stock_by_symbol(db, symbol)
    if not stock:
        return []
    
    return db.query(StockPrice).filter(
        StockPrice.stock_id == stock.id,
        StockPrice.date >= start_date,
        StockPrice.date <= end_date
    ).order_by(StockPrice.date).all()


def get_macro_indicators(
    db: Session,
    indicator_code: str,
    start_date: str,
    end_date: str
):
    """获取宏观指标数据"""
    from .models import MacroIndicator
    return db.query(MacroIndicator).filter(
        MacroIndicator.indicator_code == indicator_code,
        MacroIndicator.date >= start_date,
        MacroIndicator.date <= end_date
    ).order_by(MacroIndicator.date).all()
