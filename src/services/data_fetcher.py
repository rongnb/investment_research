"""
数据获取服务
支持通过 akshare 获取A股数据，yfinance 获取美股数据
"""
import pandas as pd
from typing import Optional, Tuple

import akshare as ak
import yfinance as yf


def get_a_stock_daily(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取A股日线数据
    
    Args:
        symbol: 股票代码，如 "600000"
        start_date: 开始日期 "YYYYMMDD"
        end_date: 结束日期 "YYYYMMDD"
    
    Returns:
        DataFrame 包含日期、开盘、收盘、最高、最低、成交量
    """
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
        # 统一列名
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume"
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        return df
    except Exception as e:
        print(f"获取A股数据出错: {e}")
        return pd.DataFrame()


def get_us_stock_daily(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取美股日线数据
    
    Args:
        symbol: 股票代码，如 "AAPL"
        start_date: 开始日期 "YYYY-MM-DD"
        end_date: 结束日期 "YYYY-MM-DD"
    
    Returns:
        DataFrame
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        # 统一列名小写
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        print(f"获取美股数据出错: {e}")
        return pd.DataFrame()


def get_etf_history(symbol: str, start_date: str, end_date: str, market: str = "CN") -> pd.DataFrame:
    """获取ETF历史数据
    
    Args:
        symbol: ETF代码
        start_date: 开始日期
        end_date: 结束日期
        market: CN/US
    """
    if market == "CN":
        return get_a_stock_daily(symbol, start_date.replace("-", ""), end_date.replace("-", ""))
    else:
        return get_us_stock_daily(symbol, start_date, end_date)


def get_stock_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """自动判断市场获取股票数据
    
    Args:
        symbol: 股票代码，纯数字为A股，否则为美股
        start_date: YYYY-MM-DD，默认 10 年前
        end_date: YYYY-MM-DD，默认今天
    """
    from datetime import datetime, timedelta
    
    # 设置默认时间范围：过去 10 年
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365*10)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    # 判断是A股还是美股
    if symbol.isdigit():
        # A股需要格式为 YYYYMMDD
        start_ymd = start_date.replace("-", "")
        end_ymd = end_date.replace("-", "")
        return get_a_stock_daily(symbol, start_ymd, end_ymd)
    else:
        # 美股
        return get_us_stock_daily(symbol, start_date, end_date)
