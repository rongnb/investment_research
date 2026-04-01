"""
策略回测服务 - 完善版
支持：交易成本、多资产、更多绩效指标、更多策略
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from datetime import datetime


class BacktestResult:
    """回测结果"""
    def __init__(self):
        self.total_return: float = 0.0
        self.annual_return: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.sortino_ratio: float = 0.0
        self.calmar_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.volatility: float = 0.0
        self.win_rate: float = 0.0
        self.profit_loss_ratio: float = 0.0
        self.total_trades: int = 0
        self.drawdown_duration: int = 0  # 最大回撤持续天数
        self.equity_curve: pd.Series = None
        self.drawdown_curve: pd.Series = None
        self.trades: List[Dict] = []
        self.transaction_costs: float = 0.0  # 总交易成本
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "win_rate": self.win_rate,
            "profit_loss_ratio": self.profit_loss_ratio,
            "total_trades": self.total_trades,
            "drawdown_duration": self.drawdown_duration,
            "transaction_costs": self.transaction_costs,
            "trades": self.trades
        }


def calculate_metrics(
    returns: pd.Series,
    trades: List[Dict] = None,
    risk_free_rate: float = 0.02
) -> BacktestResult:
    """计算完整回测指标
    
    Args:
        returns: 日收益率序列
        trades: 交易列表（可选，用于计算胜率盈亏比）
        risk_free_rate: 无风险利率，年化
    
    Returns:
        回测结果对象
    """
    result = BacktestResult()
    
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
    
    # 波动率（年化）
    result.volatility = returns.std() * np.sqrt(252) * 100
    
    # 夏普比率
    excess_return = (returns.mean() * 252) - risk_free_rate
    if returns.std() != 0:
        volatility = returns.std() * np.sqrt(252)
        result.sharpe_ratio = excess_return / volatility
    else:
        result.sharpe_ratio = 0
    
    # Sortino 比率（只考虑下跌波动率）
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 0 and downside_returns.std() != 0:
        downside_volatility = downside_returns.std() * np.sqrt(252)
        result.sortino_ratio = excess_return / downside_volatility
    else:
        result.sortino_ratio = result.sharpe_ratio
    
    # Calmar 比率（年化收益 / 最大回撤绝对值）
    # 计算最大回撤
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    result.max_drawdown = drawdown.min() * 100  # 百分比
    
    if result.max_drawdown != 0:
        result.calmar_ratio = (result.annual_return / 100) / abs(result.max_drawdown / 100)
    else:
        result.calmar_ratio = 0
    
    # 计算最大回撤持续天数
    drawdown_dur = _calculate_drawdown_duration(cumulative)
    result.drawdown_duration = drawdown_dur
    
    # 保存权益曲线和回撤曲线
    result.equity_curve = cumulative
    result.drawdown_curve = drawdown * 100
    
    # 计算胜率和盈亏比（如果有交易记录）
    if trades and len(trades) > 0:
        result.total_trades = len(trades)
        _calculate_win_rate_profit_ratio(result, trades)
    
    return result


def _calculate_drawdown_duration(cumulative: pd.Series) -> int:
    """计算最大回撤的持续天数"""
    peak = cumulative.cummax()
    drawdown = cumulative < peak
    
    max_duration = 0
    current_duration = 0
    
    for is_drawdown in drawdown:
        if is_drawdown:
            current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
        else:
            current_duration = 0
    
    return max_duration


def _calculate_win_rate_profit_ratio(result: BacktestResult, trades: List[Dict]):
    """计算胜率和盈亏比"""
    if not trades:
        return
    
    # 只统计完整买卖交易
    completed_trades = []
    i = 0
    while i < len(trades):
        if trades[i]['type'] in ['buy', 'enter'] and i + 1 < len(trades):
            # 找下一个卖出
            for j in range(i + 1, len(trades)):
                if trades[j]['type'] in ['sell', 'exit']:
                    completed_trades.append((trades[i], trades[j]))
                    i = j + 1
                    break
            else:
                i += 1
        else:
            i += 1
    
    if not completed_trades:
        return
    
    wins = 0
    total_profit = 0.0
    total_loss = 0.0
    win_count = 0
    loss_count = 0
    
    for buy_trade, sell_trade in completed_trades:
        # 估算盈亏（简化计算）
        buy_price = buy_trade.get('price', 0)
        sell_price = sell_trade.get('price', 0)
        if buy_price > 0:
            pnl = (sell_price - buy_price) / buy_price
            if pnl > 0:
                wins += 1
                total_profit += pnl
                win_count += 1
            elif pnl < 0:
                total_loss += abs(pnl)
                loss_count += 1
    
    if len(completed_trades) > 0:
        result.win_rate = (wins / len(completed_trades)) * 100
    
    if loss_count > 0 and total_loss > 0:
        avg_win = total_profit / win_count if win_count > 0 else 0
        avg_loss = total_loss / loss_count
        result.profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0


class BaseStrategy:
    """策略基类"""
    def __init__(self):
        self.commission_rate: float = 0.0003  # 佣金费率 默认万3
        self.slippage: float = 0.001  # 滑点 默认0.1%
    
    def set_transaction_cost(self, commission_rate: float = None, slippage: float = None):
        """设置交易成本"""
        if commission_rate is not None:
            self.commission_rate = commission_rate
        if slippage is not None:
            self.slippage = slippage
    
    def calculate_transaction_cost(self, price: float, quantity: float) -> float:
        """计算交易成本"""
        notional = price * abs(quantity)
        commission = notional * self.commission_rate
        slippage_cost = notional * self.slippage
        return commission + slippage_cost


class BuyAndHoldStrategy(BaseStrategy):
    """买入持有策略（基准策略）"""
    
    def __init__(self, ticker: str):
        super().__init__()
        self.ticker = ticker
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行回测"""
        close = prices['close']
        returns = close.pct_change().dropna()
        return calculate_metrics(returns)


class DollarCostAveragingStrategy(BaseStrategy):
    """定投策略
    
    定期定额买入，摊平成本
    """
    def __init__(self, monthly_investment: float = 1000):
        super().__init__()
        self.monthly_investment = monthly_investment
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行定投回测"""
        close = prices['close']
        monthly = close.resample('M').first()
        
        # 计算每次买入的股数，考虑交易成本
        shares_held = 0.0
        total_invested = 0.0
        total_costs = 0.0
        equity_curve = []
        
        # 遍历每个月
        for date, price in monthly.items():
            # 买入，扣除交易成本
            cost_before_commission = self.monthly_investment
            commission = self.calculate_transaction_cost(price, self.monthly_investment / price)
            total_costs += commission
            actual_investment = cost_before_commission - commission
            shares_bought = actual_investment / price
            shares_held += shares_bought
            total_invested += self.monthly_investment
            # 记录当前市值
            market_value = shares_held * price
            equity_curve.append((date, market_value / total_invested if total_invested > 0 else 1))
        
        # 转换为序列
        df_equity = pd.DataFrame(equity_curve, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        
        # 计算每日收益用于波动率
        daily_equity = equity_series.reindex(close.index).ffill()
        returns = daily_equity.pct_change().dropna()
        
        # 计算所有指标
        result = calculate_metrics(returns, None)
        result.transaction_costs = total_costs / total_invested * 100  # 百分比
        
        return result


class FixedWeightRebalancingStrategy(BaseStrategy):
    """固定权重再平衡策略（股债平衡）
    
    维持固定股债比例，定期再平衡
    """
    def __init__(self, stock_weight: float = 0.5, bond_weight: float = 0.5, rebalance_threshold: float = 0.05):
        super().__init__()
        self.stock_weight = stock_weight
        self.bond_weight = bond_weight
        self.rebalance_threshold = rebalance_threshold  # 偏离阈值触发再平衡
    
    def run(self, stock_prices: pd.DataFrame, bond_prices: pd.DataFrame = None) -> BacktestResult:
        """运行回测
        
        如果没有债券数据，假设债券年化收益 3%
        """
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
        total_costs = 0.0
        
        # 每日计算净值，检查是否需要再平衡
        for date_idx, (s_price, b_price) in enumerate(zip(stock_close, bond_close)):
            current_stock_value = stock_shares * s_price
            current_bond_value = bond_shares * b_price
            current_total = current_stock_value + current_bond_value
            current_stock_weight = current_stock_value / current_total
            
            # 检查是否触发再平衡
            if abs(current_stock_weight - self.stock_weight) > self.rebalance_threshold:
                # 需要再平衡，计算买卖数量
                target_stock_value = current_total * self.stock_weight
                target_bond_value = current_total * self.bond_weight
                
                delta_stock = target_stock_value - current_stock_value
                delta_shares = delta_stock / s_price if s_price > 0 else 0
                
                # 计算交易成本
                if delta_shares != 0:
                    commission = self.calculate_transaction_cost(s_price, delta_shares)
                    total_costs += commission
                    # 扣除成本后调整实际股数
                    if delta_shares > 0:
                        # 买入，需要额外支付佣金
                        stock_shares = (target_stock_value - commission) / s_price
                    else:
                        # 卖出，佣金从收入中扣除
                        stock_shares = target_stock_value / s_price
                
                # 调整债券份额
                stock_shares = target_stock_value / s_price if delta_shares == 0 else stock_shares
                bond_shares = target_bond_value / b_price
                
                trades.append({
                    "date": str(stock_close.index[date_idx]),
                    "type": "rebalance",
                    "new_stock_weight": self.stock_weight,
                    "cost": commission if 'commission' in locals() else 0
                })
            
            current_stock_value = stock_shares * s_price
            current_bond_value = bond_shares * b_price
            current_total = current_stock_value + current_bond_value
            equity_curve.append((stock_close.index[date_idx], current_total))
        
        # 转换为序列
        df_equity = pd.DataFrame(equity_curve, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        
        # 计算指标
        returns = equity_series.pct_change().dropna()
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100  # 因为初始总价值是1，直接百分比
        
        return result


class MovingAverageCrossoverStrategy(BaseStrategy):
    """均线交叉策略（双均线）
    
    短期均线上穿长期均线 → 买入
    短期均线下穿长期均线 → 卖出
    """
    def __init__(self, short_window: int = 20, long_window: int = 60):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行均线交叉策略回测"""
        close = prices['close']
        
        # 计算均线
        short_ma = close.rolling(self.short_window).mean()
        long_ma = close.rolling(self.long_window).mean()
        
        # 计算金叉/死叉信号
        signal = pd.Series(0, index=close.index)
        signal[short_ma > long_ma] = 1  # 多头持仓
        signal[short_ma < long_ma] = 0  # 空仓
        
        # 模拟带交易成本的持仓
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig) in enumerate(zip(close, signal)):
            if sig != prev_signal and not pd.isna(sig):
                if sig == 1 and position == 0:
                    # 买入，全仓
                    cost = self.calculate_transaction_cost(price, cash / price)
                    total_costs += cost
                    shares = (cash - cost) / price
                    position = 1
                    cash = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "buy",
                        "price": float(price),
                        "cost": cost
                    })
                elif sig == 0 and position == 1:
                    # 卖出，全仓
                    proceeds = shares * price
                    cost = self.calculate_transaction_cost(price, shares)
                    total_costs += cost
                    cash = proceeds - cost
                    shares = 0
                    position = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "sell",
                        "price": float(price),
                        "cost": cost
                    })
                prev_signal = sig
            
            equity.append((close.index[date_idx], cash + shares * price))
        
        # 转换为序列
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        
        # 计算指标
        returns = equity_series.pct_change().dropna()
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result

