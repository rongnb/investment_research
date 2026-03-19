"""
回测绩效指标计算模块
提供收益率、风险指标等计算
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calculate_returns(prices: pd.Series, method: str = 'simple') -> pd.Series:
    """
    计算收益率序列
    
    Args:
        prices: 价格序列
        method: 计算方法 ('simple': 简单收益率, 'log': 对数收益率)
        
    Returns:
        收益率序列
    """
    if method == 'simple':
        returns = prices.pct_change()
    elif method == 'log':
        returns = np.log(prices / prices.shift(1))
    else:
        raise ValueError(f"不支持的收益率计算方法: {method}")
    
    return returns.fillna(0)


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    计算累积收益率
    
    Args:
        returns: 收益率序列
        
    Returns:
        累积收益率序列
    """
    return (1 + returns).cumprod() - 1


def calculate_annualized_return(returns: pd.Series, 
                                 periods_per_year: int = 252) -> float:
    """
    计算年化收益率
    
    Args:
        returns: 收益率序列
        periods_per_year: 每年的交易周期数
        
    Returns:
        年化收益率
    """
    n_periods = len(returns)
    if n_periods == 0:
        return 0.0
    
    total_return = (1 + returns).prod() - 1
    annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
    
    return annualized_return


def calculate_volatility(returns: pd.Series,
                        periods_per_year: int = 252) -> float:
    """
    计算年化波动率
    
    Args:
        returns: 收益率序列
        periods_per_year: 每年的交易周期数
        
    Returns:
        年化波动率
    """
    return returns.std() * np.sqrt(periods_per_year)


def calculate_sharpe(returns: pd.Series,
                    risk_free_rate: float = 0.03,
                    periods_per_year: int = 252) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率 (年化)
        periods_per_year: 每年的交易周期数
        
    Returns:
        夏普比率
    """
    excess_returns = returns - risk_free_rate / periods_per_year
    
    volatility = excess_returns.std() * np.sqrt(periods_per_year)
    
    if volatility == 0:
        return 0.0
    
    sharpe_ratio = (excess_returns.mean() * periods_per_year) / volatility
    
    return sharpe_ratio


def calculate_sortino(returns: pd.Series,
                     risk_free_rate: float = 0.03,
                     periods_per_year: int = 252) -> float:
    """
    计算索提诺比率 (Sortino Ratio)
    
    与夏普比率类似，但只考虑下行波动率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率 (年化)
        periods_per_year: 每年的交易周期数
        
    Returns:
        索提诺比率
    """
    excess_returns = returns - risk_free_rate / periods_per_year
    
    # 下行标准差 (只考虑负收益)
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return 0.0
    
    sortino_ratio = (excess_returns.mean() * periods_per_year) / downside_std
    
    return sortino_ratio


def calculate_calmar(returns: pd.Series,
                    periods_per_year: int = 252) -> float:
    """
    计算卡尔马比率 (Calmar Ratio)
    
    年化收益率 / 最大回撤
    
    Args:
        returns: 收益率序列
        periods_per_year: 每年的交易周期数
        
    Returns:
        卡尔马比率
    """
    annualized_return = calculate_annualized_return(returns, periods_per_year)
    max_dd = calculate_max_drawdown(returns)
    
    if max_dd == 0:
        return 0.0
    
    return annualized_return / max_dd


def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    计算最大回撤
    
    Args:
        returns: 收益率序列
        
    Returns:
        最大回撤 (正值)
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    
    return abs(drawdown.min())


def calculate_max_drawdown_duration(returns: pd.Series) -> int:
    """
    计算最大回撤持续时间
    
    Args:
        returns: 收益率序列
        
    Returns:
        最大回撤持续天数
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    
    # 找到所有回撤期
    in_drawdown = cumulative < running_max
    
    max_duration = 0
    current_duration = 0
    
    for is_dd in in_drawdown:
        if is_dd:
            current_duration += 1
        else:
            max_duration = max(max_duration, current_duration)
            current_duration = 0
    
    return max(max_duration, current_duration)


def calculate_win_rate(returns: pd.Series) -> float:
    """
    计算胜率
    
    Args:
        returns: 收益率序列
        
    Returns:
        胜率 (0-1)
    """
    positive_returns = returns[returns > 0]
    
    if len(returns) == 0:
        return 0.0
    
    return len(positive_returns) / len(returns)


def calculate_profit_loss_ratio(returns: pd.Series) -> float:
    """
    计算盈亏比
    
    平均盈利 / 平均亏损
    
    Args:
        returns: 收益率序列
        
    Returns:
        盈亏比
    """
    positive_returns = returns[returns > 0]
    negative_returns = returns[returns < 0]
    
    if len(negative_returns) == 0:
        return 1.0 if len(positive_returns) > 0 else 0.0
    
    avg_profit = positive_returns.mean() if len(positive_returns) > 0 else 0
    avg_loss = abs(negative_returns.mean())
    
    return avg_profit / avg_loss if avg_loss > 0 else 0.0


def calculate_beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    计算Beta系数
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        
    Returns:
        Beta系数
    """
    # 对齐数据
    aligned_returns = pd.concat([returns, benchmark_returns], axis=1).dropna()
    
    if len(aligned_returns) < 2:
        return 1.0
    
    strategy_ret = aligned_returns.iloc[:, 0]
    benchmark_ret = aligned_returns.iloc[:, 1]
    
    # 计算协方差和方差
    covariance = strategy_ret.cov(benchmark_ret)
    benchmark_variance = benchmark_ret.var()
    
    if benchmark_variance == 0:
        return 1.0
    
    return covariance / benchmark_variance


def calculate_alpha(returns: pd.Series, 
                   benchmark_returns: pd.Series,
                   risk_free_rate: float = 0.03,
                   periods_per_year: int = 252) -> float:
    """
    计算Alpha系数 (Jensen's Alpha)
    
    Alpha = 策略收益 - [无风险收益 + Beta * (基准收益 - 无风险收益)]
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        risk_free_rate: 无风险利率
        periods_per_year: 每年的交易周期数
        
    Returns:
        Alpha系数
    """
    beta = calculate_beta(returns, benchmark_returns)
    
    # 年化收益率
    annualized_strategy_return = calculate_annualized_return(returns, periods_per_year)
    annualized_benchmark_return = calculate_annualized_return(benchmark_returns, periods_per_year)
    
    # 计算Alpha
    alpha = annualized_strategy_return - (risk_free_rate + beta * (annualized_benchmark_return - risk_free_rate))
    
    return alpha


def calculate_information_ratio(returns: pd.Series, 
                               benchmark_returns: pd.Series,
                               periods_per_year: int = 252) -> float:
    """
    计算信息比率 (Information Ratio)
    
    IR = 超额收益 / 跟踪误差
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        periods_per_year: 每年的交易周期数
        
    Returns:
        信息比率
    """
    # 计算超额收益
    excess_returns = returns - benchmark_returns
    
    # 年化超额收益
    annualized_excess_return = excess_returns.mean() * periods_per_year
    
    # 跟踪误差 (年化)
    tracking_error = excess_returns.std() * np.sqrt(periods_per_year)
    
    if tracking_error == 0:
        return 0.0
    
    return annualized_excess_return / tracking_error


def calculate_treynor_ratio(returns: pd.Series,
                           benchmark_returns: pd.Series,
                           risk_free_rate: float = 0.03,
                           periods_per_year: int = 252) -> float:
    """
    计算特雷诺比率 (Treynor Ratio)
    
    特雷诺比率 = (策略收益 - 无风险收益) / Beta
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        risk_free_rate: 无风险利率
        periods_per_year: 每年的交易周期数
        
    Returns:
        特雷诺比率
    """
    beta = calculate_beta(returns, benchmark_returns)
    
    annualized_return = calculate_annualized_return(returns, periods_per_year)
    
    if beta == 0:
        return 0.0
    
    return (annualized_return - risk_free_rate) / beta


def calculate_omega_ratio(returns: pd.Series,
                          threshold: float = 0.0,
                          periods_per_year: int = 252) -> float:
    """
    计算Omega比率
    
    Omega比率 = (收益 > 阈值的概率加权和) / (收益 < 阈值的概率加权和)
    
    Args:
        returns: 收益率序列
        threshold: 收益阈值
        periods_per_year: 每年的交易周期数
        
    Returns:
        Omega比率
    """
    daily_threshold = threshold / periods_per_year
    gains = returns[returns > daily_threshold] - daily_threshold
    losses = daily_threshold - returns[returns < daily_threshold]
    
    if len(losses) == 0 or losses.sum() == 0:
        return float('inf')
    
    return gains.sum() / losses.sum()


def calculate_ulcer_index(returns: pd.Series) -> float:
    """
    计算Ulcer指数，衡量下行风险
    
    Ulcer指数 = sqrt(平均回撤平方)
    
    Args:
        returns: 收益率序列
        
    Returns:
        Ulcer指数
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    
    squared_drawdown = drawdown ** 2
    return np.sqrt(squared_drawdown.mean())


def calculate_capture_ratios(returns: pd.Series, 
                            benchmark_returns: pd.Series) -> Tuple[float, float]:
    """
    计算上涨捕获率和下跌捕获率
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        
    Returns:
        (上涨捕获率, 下跌捕获率)
    """
    aligned_data = pd.concat([returns, benchmark_returns], axis=1).dropna()
    strategy_ret = aligned_data.iloc[:, 0]
    benchmark_ret = aligned_data.iloc[:, 1]
    
    # 上涨月份/日期
    up_mask = benchmark_ret > 0
    down_mask = benchmark_ret < 0
    
    if sum(up_mask) > 0:
        avg_up_strategy = strategy_ret[up_mask].mean()
        avg_up_benchmark = benchmark_ret[up_mask].mean()
        up_capture = avg_up_strategy / avg_up_benchmark if avg_up_benchmark != 0 else 1
    else:
        up_capture = 1
    
    if sum(down_mask) > 0:
        avg_down_strategy = strategy_ret[down_mask].mean()
        avg_down_benchmark = benchmark_ret[down_mask].mean()
        down_capture = avg_down_strategy / avg_down_benchmark if avg_down_benchmark != 0 else 1
    else:
        down_capture = 1
    
    return up_capture, down_capture


def calculate_gain_loss_statistics(returns: pd.Series) -> Dict[str, float]:
    """
    计算收益统计（平均收益，平均亏损等）
    
    Args:
        returns: 收益率序列
        
    Returns:
        统计字典
    """
    positive_returns = returns[returns > 0]
    negative_returns = returns[returns < 0]
    
    return {
        'n_gain': len(positive_returns),
        'n_loss': len(negative_returns),
        'avg_gain': positive_returns.mean() if len(positive_returns) > 0 else 0,
        'avg_loss': negative_returns.mean() if len(negative_returns) > 0 else 0,
        'max_gain': positive_returns.max() if len(positive_returns) > 0 else 0,
        'max_loss': negative_returns.min() if len(negative_returns) > 0 else 0,
    }


def calculate_comprehensive_metrics(returns: pd.Series,
                                   benchmark_returns: Optional[pd.Series] = None,
                                   risk_free_rate: float = 0.03,
                                   periods_per_year: int = 252) -> dict:
    """
    计算综合绩效指标 (超过20种指标)
    
    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率 (可选)
        risk_free_rate: 无风险利率
        periods_per_year: 每年的交易周期数
        
    Returns:
        绩效指标字典
    """
    # 基础收益统计
    gain_loss_stats = calculate_gain_loss_statistics(returns)
    
    metrics = {
        # ======== 收益指标 ========
        'total_return': calculate_cumulative_returns(returns).iloc[-1],
        'annualized_return': calculate_annualized_return(returns, periods_per_year),
        
        # ======== 风险指标 ========
        'volatility': calculate_volatility(returns, periods_per_year),
        'max_drawdown': calculate_max_drawdown(returns),
        'max_drawdown_duration': calculate_max_drawdown_duration(returns),
        'ulcer_index': calculate_ulcer_index(returns),
        'var_95': np.percentile(returns, 5) if len(returns) > 0 else 0,
        'var_99': np.percentile(returns, 1) if len(returns) > 0 else 0,
        
        # ======== 风险调整收益指标 ========
        'sharpe_ratio': calculate_sharpe(returns, risk_free_rate, periods_per_year),
        'sortino_ratio': calculate_sortino(returns, risk_free_rate, periods_per_year),
        'calmar_ratio': calculate_calmar(returns, periods_per_year),
        'omega_ratio': calculate_omega_ratio(returns, 0, periods_per_year),
        
        # ======== 收益分布统计 ========
        'win_rate': calculate_win_rate(returns),
        'profit_loss_ratio': calculate_profit_loss_ratio(returns),
        'skewness': returns.skew() if len(returns) > 0 else 0,
        'kurtosis': returns.kurtosis() if len(returns) > 0 else 0,
        'avg_gain': gain_loss_stats['avg_gain'],
        'avg_loss': gain_loss_stats['avg_loss'],
        'max_daily_gain': gain_loss_stats['max_gain'],
        'max_daily_loss': gain_loss_stats['max_loss'],
        'up_days': gain_loss_stats['n_gain'],
        'down_days': gain_loss_stats['n_loss'],
    }
    
    # 如果有基准数据，计算相对指标
    if benchmark_returns is not None:
        # 对齐数据
        aligned_data = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned_data) > 0:
            strategy_ret = aligned_data.iloc[:, 0]
            benchmark_ret = aligned_data.iloc[:, 1]
            
            metrics['beta'] = calculate_beta(strategy_ret, benchmark_ret)
            metrics['alpha'] = calculate_alpha(strategy_ret, benchmark_ret, risk_free_rate, periods_per_year)
            metrics['information_ratio'] = calculate_information_ratio(strategy_ret, benchmark_ret, periods_per_year)
            metrics['treynor_ratio'] = calculate_treynor_ratio(strategy_ret, benchmark_ret, risk_free_rate, periods_per_year)
            metrics['up_capture'], metrics['down_capture'] = calculate_capture_ratios(strategy_ret, benchmark_ret)
            
            # 相对收益
            metrics['excess_return'] = metrics['annualized_return'] - calculate_annualized_return(benchmark_ret, periods_per_year)
    
    return metrics


if __name__ == "__main__":
    # 测试
    np.random.seed(42)
    
    # 生成模拟收益率
    returns = pd.Series(np.random.normal(0.0005, 0.02, 252))
    benchmark_returns = pd.Series(np.random.normal(0.0003, 0.015, 252))
    
    # 计算指标
    metrics = calculate_comprehensive_metrics(returns, benchmark_returns)
    
    print("绩效指标:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
