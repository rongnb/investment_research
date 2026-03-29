"""
策略回测服务
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from datetime import datetime


class BacktestResult:
    """回测结果"""
    def __init__(self):
        self.total_return: float = 0.0
        self.annual_return: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.equity_curve: pd.Series = None
        self.trades: List[Dict] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "trades": self.trades
        }


def calculate_metrics(prices: pd.Series, weights: pd.Series = None) -> BacktestResult:
    """计算回测指标
    
    Args:
        prices: 价格序列
        weights: 权重序列（可选，用于组合）
    
    Returns:
        回测结果对象
    """
    result = BacktestResult()
    
    # 计算收益率
    returns = prices.pct_change().dropna()
    
    if weights is not None:
        # 加权组合收益
        returns = (returns * weights).sum(axis=1)
    
    # 累计收益
    cumulative = (1 + returns).cumprod()
    result.total_return = (cumulative.iloc[-1] - 1) * 100  # 百分比
    
    # 年化收益
    n_days = len(returns)
    years = n_days / 252  # 交易日
    if years > 0:
        result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
    else:
        result.annual_return = result.total_return
    
    # 夏普比率（假设无风险利率 0）
    if returns.std() != 0:
        volatility = returns.std() * np.sqrt(252)
        result.sharpe_ratio = (returns.mean() * 252) / volatility
    
    # 最大回撤
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    result.max_drawdown = drawdown.min() * 100  # 百分比
    
    result.equity_curve = cumulative
    return result


class BuyAndHoldStrategy:
    """买入持有策略（基准策略）"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行回测"""
        close_prices = prices['close']
        return calculate_metrics(close_prices)


class DollarCostAveragingStrategy:
    """定投策略
    
    定期定额买入，摊平成本
    """
    def __init__(self, monthly_investment: float = 1000):
        self.monthly_investment = monthly_investment
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行定投回测"""
        result = BacktestResult()
        
        # 按月分组，每月第一个交易日买入
        close = prices['close']
        monthly = close.resample('M').first()
        
        # 计算每次买入的股数
        shares_held = 0.0
        total_invested = 0.0
        equity_curve = []
        
        # 遍历每个月
        for date, price in monthly.items():
            # 买入
            shares_held += self.monthly_investment / price
            total_invested += self.monthly_investment
            # 记录当前市值
            market_value = shares_held * price
            equity_curve.append((date, market_value / total_invested if total_invested > 0 else 1))
        
        # 转换为序列
        df_equity = pd.DataFrame(equity_curve, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        
        # 计算收益率
        result.total_return = (equity_series.iloc[-1] - 1) * 100
        
        # 年化收益
        n_months = len(equity_series)
        years = n_months / 12
        if years > 0:
            result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
        else:
            result.annual_return = result.total_return
        
        # 计算每日收益用于波动率
        # 使用原价格序列插值
        daily_equity = equity_series.reindex(close.index).fillna(method='ffill')
        returns = daily_equity.pct_change().dropna()
        
        # 夏普比率
        if returns.std() != 0:
            volatility = returns.std() * np.sqrt(252)
            result.sharpe_ratio = (returns.mean() * 252) / volatility
        else:
            result.sharpe_ratio = 0
        
        # 最大回撤
        peak = daily_equity.cummax()
        drawdown = (daily_equity - peak) / peak
        result.max_drawdown = drawdown.min() * 100
        
        result.equity_curve = daily_equity
        return result


class FixedWeightRebalancingStrategy:
    """固定权重再平衡策略（股债平衡）
    
    维持固定股债比例，定期再平衡
    """
    def __init__(self, stock_weight: float = 0.5, bond_weight: float = 0.5, rebalance_threshold: float = 0.05):
        self.stock_weight = stock_weight
        self.bond_weight = bond_weight
        self.rebalance_threshold = rebalance_threshold  # 偏离阈值触发再平衡
    
    def run(self, stock_prices: pd.DataFrame, bond_prices: pd.DataFrame = None) -> BacktestResult:
        """运行回测
        
        如果没有债券数据，假设债券年化收益 3%
        """
        result = BacktestResult()
        stock_close = stock_prices['close']
        
        # 如果没有债券数据，生成模拟债券净值
        if bond_prices is None or bond_prices.empty:
            # 假设年化 3% 稳定增长
            bond_returns = (1 + 0.03) ** (1/252) - 1
            bond_close = (1 + bond_returns).cumprod()
            bond_close = pd.Series([1.0] + list(bond_close.reindex(stock_close.index[1:])), index=stock_close.index)
        else:
            bond_close = bond_prices['close'].reindex(stock_close.index).ffill().bfill()
        
        # 初始投资
        total_value = 1.0
        stock_value = total_value * self.stock_weight
        bond_value = total_value * self.bond_weight
        stock_shares = stock_value / stock_close.iloc[0]
        bond_shares = bond_value / bond_close.iloc[0]
        
        equity_curve = []
        trades = []
        
        # 每日计算净值，检查是否需要再平衡
        for date, (s_price, b_price) in enumerate(zip(stock_close, bond_close)):
            current_stock_value = stock_shares * s_price
            current_bond_value = bond_shares * b_price
            current_total = current_stock_value + current_bond_value
            current_stock_weight = current_stock_value / current_total
            
            # 检查是否触发再平衡
            if abs(current_stock_weight - self.stock_weight) > self.rebalance_threshold:
                # 需要再平衡
                target_stock_value = current_total * self.stock_weight
                target_bond_value = current_total * self.bond_weight
                stock_shares = target_stock_value / s_price
                bond_shares = target_bond_value / b_price
                trades.append({
                    "date": str(date),
                    "type": "rebalance",
                    "new_stock_weight": self.stock_weight
                })
            
            current_stock_value = stock_shares * s_price
            current_bond_value = bond_shares * b_price
            current_total = current_stock_value + current_bond_value
            equity_curve.append((stock_close.index[date], current_total))
        
        # 转换为序列
        df_equity = pd.DataFrame(equity_curve, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        
        # 计算指标
        result.total_return = (equity_series.iloc[-1] - 1) * 100
        
        n_days = len(equity_series)
        years = n_days / 252
        if years > 0:
            result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
        else:
            result.annual_return = result.total_return
        
        returns = equity_series.pct_change().dropna()
        if returns.std() != 0:
            volatility = returns.std() * np.sqrt(252)
            result.sharpe_ratio = (returns.mean() * 252) / volatility
        else:
            result.sharpe_ratio = 0
        
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        result.max_drawdown = drawdown.min() * 100
        
        result.equity_curve = equity_series
        result.trades = trades
        return result


class MovingAverageCrossoverStrategy:
    """均线交叉策略（双均线）
    
    短期均线上穿长期均线 → 买入
    短期均线下穿长期均线 → 卖出
    """
    def __init__(self, short_window: int = 20, long_window: int = 60):
        self.short_window = short_window
        self.long_window = long_window
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行均线交叉策略回测"""
        result = BacktestResult()
        close = prices['close']
        
        # 计算均线
        short_ma = close.rolling(self.short_window).mean()
        long_ma = close.rolling(self.long_window).mean()
        
        # 计算金叉/死叉信号
        signal = pd.Series(0, index=close.index)
        signal[short_ma > long_ma] = 1  # 多头持仓
        signal[short_ma < long_ma] = 0  # 空仓
        
        # 计算策略收益，假设持有股票时获得全部收益，空仓时收益为0
        returns = close.pct_change()
        strategy_returns = returns * signal.shift(1)
        strategy_returns = strategy_returns.dropna()
        
        # 累计收益
        cumulative = (1 + strategy_returns).cumprod()
        
        # 计算指标
        result.total_return = (cumulative.iloc[-1] - 1) * 100
        
        n_days = len(strategy_returns)
        years = n_days / 252
        if years > 0:
            result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
        else:
            result.annual_return = result.total_return
        
        if strategy_returns.std() != 0:
            volatility = strategy_returns.std() * np.sqrt(252)
            result.sharpe_ratio = (strategy_returns.mean() * 252) / volatility
        else:
            result.sharpe_ratio = 0
        
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        result.max_drawdown = drawdown.min() * 100
        
        result.equity_curve = cumulative
        
        # 记录交易信号
        trades = []
        prev_signal = 0
        for date, sig in signal.items():
            if sig != prev_signal:
                if sig == 1:
                    trades.append({"date": str(date), "type": "buy", "price": float(close.loc[date])})
                else:
                    trades.append({"date": str(date), "type": "sell", "price": float(close.loc[date])})
                prev_signal = sig
        result.trades = trades
        
        return result


class LowVolatilityStrategy:
    """低波动策略
    
    选择/持有低波动资产，在下跌市场中表现更好
    这里实现为：只在波动率低于阈值时持仓
    """
    def __init__(self, volatility_window: int = 20, volatility_threshold: float = 0.02):
        self.volatility_window = volatility_window
        self.volatility_threshold = volatility_threshold  # 日波动率阈值（2%）
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行低波动策略回测"""
        result = BacktestResult()
        close = prices['close']
        
        # 计算滚动波动率
        returns = close.pct_change()
        rolling_vol = returns.rolling(self.volatility_window).std()
        
        # 信号：波动率低于阈值时持仓
        signal = pd.Series(0, index=close.index)
        signal[rolling_vol < self.volatility_threshold] = 1
        signal[rolling_vol >= self.volatility_threshold] = 0
        
        # 计算策略收益
        strategy_returns = returns * signal.shift(1)
        strategy_returns = strategy_returns.dropna()
        
        # 累计收益
        cumulative = (1 + strategy_returns).cumprod()
        
        # 计算指标
        result.total_return = (cumulative.iloc[-1] - 1) * 100
        
        n_days = len(strategy_returns)
        years = n_days / 252
        if years > 0:
            result.annual_return = ((1 + result.total_return / 100) ** (1 / years) - 1) * 100
        else:
            result.annual_return = result.total_return
        
        if strategy_returns.std() != 0:
            volatility = strategy_returns.std() * np.sqrt(252)
            result.sharpe_ratio = (strategy_returns.mean() * 252) / volatility
        else:
            result.sharpe_ratio = 0
        
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        result.max_drawdown = drawdown.min() * 100
        
        result.equity_curve = cumulative
        
        # 记录切换信号
        trades = []
        prev_signal = 1
        for date, sig in signal.items():
            if sig != prev_signal and not pd.isna(sig):
                if sig == 1:
                    trades.append({"date": str(date), "type": "enter_low_vol", "vol": float(rolling_vol.loc[date])})
                else:
                    trades.append({"date": str(date), "type": "exit_high_vol", "vol": float(rolling_vol.loc[date])})
                prev_signal = sig
        result.trades = trades
        
        return result
