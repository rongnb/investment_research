"""
通用工具函数模块
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime, date, timedelta
import re
import hashlib
import json


def validate_stock_code(code: str, market: str = None) -> bool:
    """
    验证股票代码格式
    
    Args:
        code: 股票代码
        market: 市场类型 (sh/sz/bj/hk/us)
        
    Returns:
        是否有效
    """
    if not code or not isinstance(code, str):
        return False
    
    code = code.strip()
    
    # 上海市场: 6xxxxxx
    if market == 'sh' or code.startswith('6'):
        return len(code) == 6 and code.isdigit()
    
    # 深圳市场: 0xxxxxx, 3xxxxxx
    if market == 'sz':
        return len(code) == 6 and code.isdigit() and code[0] in ['0', '3']
    
    # 北京市场: 8xxxxxx, 4xxxxxx
    if market == 'bj':
        return len(code) == 6 and code.isdigit() and code[0] in ['8', '4']
    
    # 香港市场: xxxx.HK
    if market == 'hk' or code.endswith('.HK'):
        return len(code.replace('.HK', '')) <= 5
    
    # 美股: 字母+数字
    if market == 'us':
        return code.isalnum() and len(code) <= 5
    
    # 通用检查
    return len(code) <= 20


def format_date(date_input: Union[str, datetime, date, pd.Timestamp],
                output_format: str = '%Y-%m-%d') -> str:
    """
    格式化日期
    
    Args:
        date_input: 日期输入
        output_format: 输出格式
        
    Returns:
        格式化后的日期字符串
    """
    if isinstance(date_input, str):
        # 尝试解析日期
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d-%m-%Y', '%m/%d/%Y']:
            try:
                date_input = datetime.strptime(date_input, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"无法解析日期: {date_input}")
    
    if isinstance(date_input, (datetime, date, pd.Timestamp)):
        return date_input.strftime(output_format)
    
    raise ValueError(f"不支持的日期类型: {type(date_input)}")


def calculate_returns(prices: pd.Series,
                     method: str = 'simple',
                     periods: int = 1) -> pd.Series:
    """
    计算收益率
    
    Args:
        prices: 价格序列
        method: 计算方法 (simple: 简单收益率, log: 对数收益率)
        periods: 周期数
        
    Returns:
        收益率序列
    """
    if method == 'simple':
        returns = prices.pct_change(periods=periods)
    elif method == 'log':
        returns = np.log(prices / prices.shift(periods))
    else:
        raise ValueError(f"不支持的收益率计算方法: {method}")
    
    return returns


def calculate_sharpe_ratio(returns: pd.Series,
                           risk_free_rate: float = 0.03,
                           periods: int = 252) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率
        periods: 年化周期数
        
    Returns:
        夏普比率
    """
    if len(returns) < 2:
        return 0.0
    
    # 年化收益率
    mean_return = returns.mean() * periods
    
    # 年化标准差
    volatility = returns.std() * np.sqrt(periods)
    
    if volatility == 0:
        return 0.0
    
    # 夏普比率
    sharpe_ratio = (mean_return - risk_free_rate) / volatility
    
    return sharpe_ratio


def calculate_max_drawdown(prices: pd.Series) -> Tuple[float, int, int]:
    """
    计算最大回撤
    
    Args:
        prices: 价格序列
        
    Returns:
        (最大回撤率, 峰值位置, 谷值位置)
    """
    # 计算累积最大值
    cumulative_max = prices.cummax()
    
    # 计算回撤
    drawdown = (prices - cumulative_max) / cumulative_max
    
    # 找到最大回撤
    max_drawdown = drawdown.min()
    max_drawdown_idx = drawdown.idxmin()
    
    # 找到峰值位置
    peak_idx = prices.loc[:max_drawdown_idx].idxmax()
    
    # 转换为位置索引
    peak_pos = prices.index.get_loc(peak_idx)
    trough_pos = prices.index.get_loc(max_drawdown_idx)
    
    return abs(max_drawdown), peak_pos, trough_pos


def resample_data(data: pd.DataFrame,
                  rule: str,
                  price_cols: List[str] = None,
                  volume_col: str = None) -> pd.DataFrame:
    """
    重采样数据
    
    Args:
        data: 原始数据
        rule: 重采样规则 ('D', 'W', 'M', 'Q', 'Y', '1H', etc.)
        price_cols: 价格列名列表 ['open', 'high', 'low', 'close']
        volume_col: 成交量列名
        
    Returns:
        重采样后的数据
    """
    if price_cols is None:
        price_cols = ['open', 'high', 'low', 'close']
    
    # 确保索引是datetime类型
    if not isinstance(data.index, pd.DatetimeIndex):
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
        else:
            raise ValueError("数据缺少日期索引或日期列")
    
    # 重采样
    resampled = pd.DataFrame()
    
    if 'open' in price_cols and price_cols[0] in data.columns:
        resampled['open'] = data[price_cols[0]].resample(rule).first()
    
    if 'high' in price_cols and price_cols[1] in data.columns:
        resampled['high'] = data[price_cols[1]].resample(rule).max()
    
    if 'low' in price_cols and price_cols[2] in data.columns:
        resampled['low'] = data[price_cols[2]].resample(rule).min()
    
    if 'close' in price_cols and price_cols[3] in data.columns:
        resampled['close'] = data[price_cols[3]].resample(rule).last()
    
    if volume_col and volume_col in data.columns:
        resampled['volume'] = data[volume_col].resample(rule).sum()
    
    return resampled.dropna()


def generate_id(prefix: str = "") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        唯一ID字符串
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    random_str = hashlib.md5(str(np.random.random()).encode()).hexdigest()[:8]
    return f"{prefix}{timestamp}{random_str}"


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法
    
    Args:
        a: 被除数
        b: 除数
        default: 默认值
        
    Returns:
        除法结果或默认值
    """
    if b == 0 or pd.isna(b):
        return default
    return a / b


def round_to_decimal(value: float, decimal_places: int = 2) -> float:
    """
    四舍五入到指定小数位
    
    Args:
        value: 原始值
        decimal_places: 小数位数
        
    Returns:
        四舍五入后的值
    """
    if pd.isna(value):
        return 0.0
    return round(value, decimal_places)


def parse_numeric(value: Any, default: float = 0.0) -> float:
    """
    解析数值
    
    Args:
        value: 输入值
        default: 默认值
        
    Returns:
        解析后的数值
    """
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def batch_process(items: List[Any], batch_size: int = 100):
    """
    批量处理生成器
    
    Args:
        items: 待处理列表
        batch_size: 批次大小
        
    Yields:
        批次数据
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    错误重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        
    Returns:
        装饰器函数
    """
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"尝试 {attempt + 1} 失败: {e}，{delay}秒后重试...")
                    time.sleep(delay)
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300):
    """
    结果缓存装饰器
    
    Args:
        ttl_seconds: 缓存有效期（秒）
        
    Returns:
        装饰器函数
    """
    import functools
    import time
    
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存到缓存
            cache[key] = (result, time.time())
            
            return result
        return wrapper
    return decorator


def log_execution_time(func_name: str = None):
    """
    执行时间日志装饰器
    
    Args:
        func_name: 函数名称
        
    Returns:
        装饰器函数
    """
    import functools
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
