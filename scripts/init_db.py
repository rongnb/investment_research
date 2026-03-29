#!/usr/bin/env python3
"""
初始化数据库，创建所有表
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.base import Base, engine
from src.models.portfolio import Portfolio, Holding
from src.models.strategy import InvestmentStrategy, BacktestResult

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")
print("\nTables created:")
for table in Base.metadata.tables:
    print(f"  - {table}")
