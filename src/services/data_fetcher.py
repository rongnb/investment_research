"""
数据获取服务
支持通过 akshare 获取A股数据，yfinance 获取美股数据
支持本地文件缓存，重复请求大大加快回测速度
"""
import os
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime

import akshare as ak
import yfinance as yf

# 缓存目录
CACHE_DIR = os.environ.get('INVEST_DATA_CACHE', '.data_cache')


def _get_cache_path(symbol: str, start_date: str, end_date: str, market: str) -> str:
    """获取缓存文件路径"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 生成唯一文件名
    filename = f"{market}_{symbol}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.pkl"
    return os.path.join(CACHE_DIR, filename)


def _load_from_cache(cache_path: str) -> Optional[pd.DataFrame]:
    """尝试从缓存加载数据"""
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"✅ 从缓存加载 {cache_path}")
            return df
        except Exception as e:
            print(f"⚠️ 缓存加载失败: {e}, 重新获取")
            os.remove(cache_path)
    return None


def _save_to_cache(df: pd.DataFrame, cache_path: str) -> None:
    """保存数据到缓存"""
    try:
        df.to_pickle(cache_path)
        print(f"💾 数据已缓存到 {cache_path}")
    except Exception as e:
        print(f"⚠️ 缓存保存失败: {e}")


def get_a_stock_daily(symbol: str, start_date: str, end_date: str, use_cache: bool = True) -> pd.DataFrame:
    """获取A股日线数据
    
    Args:
        symbol: 股票代码，如 "600000"
        start_date: 开始日期 "YYYYMMDD"
        end_date: 结束日期 "YYYYMMDD"
        use_cache: 是否使用缓存
    
    Returns:
        DataFrame 包含日期、开盘、收盘、最高、最低、成交量
    """
    # 尝试从缓存加载
    start_str = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    end_str = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    cache_path = _get_cache_path(symbol, start_str, end_str, "CN")
    
    if use_cache:
        cached = _load_from_cache(cache_path)
        if cached is not None:
            return cached
    
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
        
        if use_cache and not df.empty:
            _save_to_cache(df, cache_path)
        
        return df
    except Exception as e:
        print(f"获取A股数据出错: {e}")
        return pd.DataFrame()


def get_us_stock_daily(symbol: str, start_date: str, end_date: str, use_cache: bool = True) -> pd.DataFrame:
    """获取美股日线数据
    
    Args:
        symbol: 股票代码，如 "AAPL"
        start_date: 开始日期 "YYYY-MM-DD"
        end_date: 结束日期 "YYYY-MM-DD"
        use_cache: 是否使用缓存
    
    Returns:
        DataFrame
    """
    cache_path = _get_cache_path(symbol, start_date, end_date, "US")
    if use_cache:
        cached = _load_from_cache(cache_path)
        if cached is not None:
            return cached
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        # 统一列名小写
        df.columns = [col.lower() for col in df.columns]
        
        if use_cache and not df.empty:
            _save_to_cache(df, cache_path)
        
        return df
    except Exception as e:
        print(f"获取美股数据出错: {e}")
        return pd.DataFrame()


def get_etf_history(symbol: str, start_date: str, end_date: str, market: str = "CN", use_cache: bool = True) -> pd.DataFrame:
    """获取ETF历史数据
    
    Args:
        symbol: ETF代码
        start_date: 开始日期
        end_date: 结束日期
        market: CN/US
        use_cache: 是否使用缓存
    """
    if market == "CN":
        return get_a_stock_daily(symbol, start_date.replace("-", ""), end_date.replace("-", ""), use_cache=use_cache)
    else:
        return get_us_stock_daily(symbol, start_date, end_date, use_cache=use_cache)


def get_stock_data(symbol: str, start_date: str = None, end_date: str = None, use_cache: bool = True) -> pd.DataFrame:
    """自动判断市场获取股票数据
    
    Args:
        symbol: 股票代码，纯数字为A股，否则为美股
        start_date: YYYY-MM-DD，默认 10 年前
        end_date: YYYY-MM-DD，默认今天
        use_cache: 是否使用缓存（默认开启，大大加快回测）
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
        return get_a_stock_daily(symbol, start_ymd, end_ymd, use_cache=use_cache)
    else:
        # 美股
        return get_us_stock_daily(symbol, start_date, end_date, use_cache=use_cache)


def clear_cache() -> int:
    """清除所有缓存数据
    
    Returns:
        删除的文件数量
    """
    if not os.path.exists(CACHE_DIR):
        return 0
    
    count = 0
    for f in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
            count += 1
    
    print(f"🗑️  已清除 {count} 个缓存文件")
    return count


def cache_info() -> dict:
    """获取缓存信息"""
    if not os.path.exists(CACHE_DIR):
        return {"files": 0, "size_mb": 0.0}
    
    total_size = 0
    file_count = 0
    for f in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, f)
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)
            file_count += 1
    
    return {
        "files": file_count,
        "size_mb": total_size / (1024 * 1024),
        "cache_dir": os.path.abspath(CACHE_DIR)
    }
