"""
风险分析模块
提供VaR、CVaR、压力测试等风险指标计算
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
from scipy import stats


class VaR:
    """
    风险价值 (Value at Risk) 计算器
    
    VaR表示在给定置信水平下的最大预期损失
    """
    
    def __init__(self, confidence_level: float = 0.95):
        """
        初始化VaR计算器
        
        Args:
            confidence_level: 置信水平 (默认95%)
        """
        self.confidence_level = confidence_level
    
    def historical(self, returns: pd.Series) -> float:
        """
        历史模拟法计算VaR
        
        Args:
            returns: 收益率序列
            
        Returns:
            VaR值 (负数表示损失)
        """
        return np.percentile(returns, (1 - self.confidence_level) * 100)
    
    def parametric(self, returns: pd.Series) -> float:
        """
        参数法计算VaR (假设正态分布)
        
        Args:
            returns: 收益率序列
            
        Returns:
            VaR值
        """
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - self.confidence_level)
        
        return mean + z_score * std
    
    def monte_carlo(self, returns: pd.Series, 
                   n_simulations: int = 10000) -> float:
        """
        蒙特卡洛模拟法计算VaR
        
        Args:
            returns: 收益率序列
            n_simulations: 模拟次数
            
        Returns:
            VaR值
        """
        mean = returns.mean()
        std = returns.std()
        
        # 生成随机收益率
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        return np.percentile(simulated_returns, (1 - self.confidence_level) * 100)


def calculate_cvar(returns: pd.Series, 
                  confidence_level: float = 0.95,
                  method: str = 'historical') -> float:
    """
    计算条件风险价值 (CVaR/Expected Shortfall)
    
    CVaR是超过VaR阈值的平均损失
    
    Args:
        returns: 收益率序列
        confidence_level: 置信水平
        method: 计算方法 ('historical', 'parametric')
        
    Returns:
        CVaR值 (负数表示损失)
    """
    var = VaR(confidence_level)
    
    if method == 'historical':
        var_value = var.historical(returns)
        # 计算超过VaR的平均损失
        tail_losses = returns[returns <= var_value]
        if len(tail_losses) == 0:
            return var_value
        return tail_losses.mean()
    
    elif method == 'parametric':
        var_value = var.parametric(returns)
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence_level)
        # 参数法下CVaR公式
        phi_z = stats.norm.pdf(z_score)
        cvar = mean - std * phi_z / (1 - confidence_level)
        return cvar
    
    else:
        raise ValueError(f"不支持的方法: {method}")


def calculate_expected_shortfall(returns: pd.Series, 
                                confidence_level: float = 0.95) -> float:
    """
    别名：计算期望短缺 (Expected Shortfall) = CVaR
    
    Args:
        returns: 收益率序列
        confidence_level: 置信水平
        
    Returns:
        ES值
    """
    return calculate_cvar(returns, confidence_level, method='historical')


def calculate_greeks(option_price: float, 
                     underlying_price: float,
                     volatility: float,
                     risk_free_rate: float,
                     time_to_maturity: float,
                     option_type: str = 'call') -> Dict[str, float]:
    """
    计算期权希腊字母 (Black-Scholes模型)
    
    Args:
        option_price: 期权价格
        underlying_price: 标的资产价格
        volatility: 波动率
        risk_free_rate: 无风险利率
        time_to_maturity: 剩余到期时间 (年)
        option_type: 期权类型 'call' or 'put'
        
    Returns:
        希腊字母字典
    """
    from scipy.stats import norm
    
    S = underlying_price
    K = option_price
    r = risk_free_rate
    sigma = volatility
    T = time_to_maturity
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    delta = norm.cdf(d1) if option_type == 'call' else norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # 每1%波动率变化
    theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
             r * K * np.exp(-r * T) * norm.cdf(d2)) if option_type == 'call' else \
            (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
             r * K * np.exp(-r * T) * norm.cdf(-d2))
    theta = theta / 365  # 每日theta
    
    return {
        'delta': delta,
        'gamma': gamma,
        'vega': vega,
        'theta': theta
    }


def calculate_volatility_clustering(returns: pd.Series, 
                                  lags: int = 5) -> float:
    """
    检验波动率聚集效应，计算平方收益率的自相关系数
    
    Args:
        returns: 收益率序列
        lags: 滞后阶数
        
    Returns:
        一阶自相关系数
    """
    squared_returns = returns ** 2
    autocorr = squared_returns.autocorr(1)
    return autocorr


class RiskAnalyzer:
    """
    综合风险分析器
    
    提供多种风险指标分析
    """
    
    def __init__(self, returns: pd.Series, 
                 benchmark_returns: Optional[pd.Series] = None):
        """
        初始化风险分析器
        
        Args:
            returns: 策略收益率
            benchmark_returns: 基准收益率
        """
        self.returns = returns.dropna()
        self.benchmark_returns = benchmark_returns.dropna() if benchmark_returns is not None else None
        if self.benchmark_returns is not None:
            # 对齐数据
            aligned = pd.concat([self.returns, self.benchmark_returns], axis=1).dropna()
            self.returns = aligned.iloc[:, 0]
            self.benchmark_returns = aligned.iloc[:, 1]
    
    def calculate_all_risk_metrics(self) -> Dict[str, float]:
        """
        计算所有风险指标
        
        Returns:
            风险指标字典
        """
        metrics = {}
        
        # VaR和CVaR
        for confidence in [0.90, 0.95, 0.99]:
            var_95 = VaR(confidence).historical(self.returns)
            cvar_95 = calculate_cvar(self.returns, confidence)
            metrics[f'var_{int(confidence * 100)}'] = var_95
            metrics[f'cvar_{int(confidence * 100)}'] = cvar_95
        
        # 波动率聚类
        metrics['volatility_clustering_ac'] = calculate_volatility_clustering(self.returns)
        
        # 负偏度检验
        metrics['skewness'] = self.returns.skew()
        metrics['kurtosis'] = self.returns.kurtosis()
        
        # 最大回撤相关
        from .metrics import calculate_max_drawdown, calculate_max_drawdown_duration
        metrics['max_drawdown'] = calculate_max_drawdown(self.returns)
        metrics['max_drawdown_duration'] = calculate_max_drawdown_duration(self.returns)
        
        # 相对指标
        if self.benchmark_returns is not None:
            from .metrics import calculate_beta, calculate_alpha
            metrics['beta'] = calculate_beta(self.returns, self.benchmark_returns)
            metrics['alpha'] = calculate_alpha(self.returns, self.benchmark_returns)
            
            # 跟踪误差
            excess_returns = self.returns - self.benchmark_returns
            metrics['tracking_error'] = excess_returns.std() * np.sqrt(252)
        
        return metrics
    
    def stress_test(self, scenario_shocks: Optional[List[float]] = None) -> Dict[str, float]:
        """
        压力测试 - 基于历史收益率的极端场景分析
        
        Args:
            scenario_shocks: 自定义冲击列表
            
        Returns:
            压力测试结果
        """
        if scenario_shocks is None:
            # 使用历史最差n个收益率作为场景
            worst_returns = self.returns.nsmallest(5)
            scenario_shocks = worst_returns.tolist()
        
        results = {}
        
        # 当前组合价值假设为1
        current_value = 1.0
        for i, shock in enumerate(scenario_shocks):
            new_value = current_value * (1 + shock)
            results[f'scenario_{i+1}_shock'] = shock
            results[f'scenario_{i+1}_value'] = new_value
            results[f'scenario_{i+1}_loss'] = new_value - current_value
        
        return results
    
    def tail_risk_analysis(self) -> Dict[str, float]:
        """
        尾部风险分析
        
        Returns:
            尾部风险指标
        """
        returns = self.returns
        negative_returns = returns[returns < 0]
        
        results = {
            'n_tail_losses': len(negative_returns[negative_returns < returns.mean() - 2 * returns.std()]),
            'max_loss': returns.min(),
            'avg_largest_5_losses': returns.nsmallest(5).mean(),
            'tail_pct_5': np.percentile(returns, 5),
            'tail_pct_1': np.percentile(returns, 1),
        }
        
        return results
