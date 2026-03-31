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
                        "type": "sell",
                        "price": float(price),
                        "cost": cost
                    })
                prev_signal = sig
            
            # 计算当日净值
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        # 转换为序列计算收益
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


class MACDStrategy(BaseStrategy):
    """MACD策略
    
    MACD金叉买入，死叉卖出
    """
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行MACD策略回测"""
        close = prices['close']
        
        # 计算EMA
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd - signal
        
        # 生成信号：MACD上穿信号线买入，下穿卖出
        position_signal = pd.Series(0, index=close.index)
        position_signal[(macd > signal) & (macd.shift(1) <= signal.shift(1))] = 1
        position_signal[(macd < signal) & (macd.shift(1) >= signal.shift(1))] = 0
        position_signal = position_signal.ffill().fillna(0)
        
        # 模拟带交易成本
        return self._simulate_position(close, position_signal)


class RSIStrategy(BaseStrategy):
    """RSI相对强弱指数策略
    
    RSI低于超卖区间买入，高于超买区间卖出
    """
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行RSI策略回测"""
        close = prices['close']
        
        # 计算RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 生成信号：RSI < 超卖 → 买入持有；RSI > 超买 → 卖出空仓
        position_signal = pd.Series(0, index=close.index)
        # 趋势跟随：超卖买入后持有直到超卖卖出
        position = 0
        for i, (date, val) in enumerate(rsi.items()):
            if pd.isna(val):
                continue
            if position == 0 and val < self.oversold:
                position = 1
            elif position == 1 and val > self.overbought:
                position = 0
            position_signal.iloc[i] = position
        
        # 模拟带交易成本
        return self._simulate_position(close, position_signal)


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略
    
    价格跌破下轨买入，价格涨过上轨卖出
    """
    def __init__(self, window: int = 20, std_dev: float = 2.0):
        super().__init__()
        self.window = window
        self.std_dev = std_dev
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行布林带策略回测"""
        close = prices['close']
        
        # 计算布林带
        middle = close.rolling(self.window).mean()
        std = close.rolling(self.window).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        # 生成信号
        position_signal = pd.Series(0, index=close.index)
        position = 0
        for i, (price, up, low) in enumerate(zip(close, upper, lower)):
            if pd.isna(price) or pd.isna(up) or pd.isna(low):
                continue
            if position == 0 and price < low:
                # 跌破下轨买入
                position = 1
            elif position == 1 and price > up:
                # 涨过上轨卖出
                position = 0
            position_signal.iloc[i] = position
        
        return self._simulate_position(close, position_signal)
    
    def _simulate_position(self, close: pd.Series, position_signal: pd.Series) -> BacktestResult:
        """通用的仓位模拟带交易成本"""
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig) in enumerate(zip(close, position_signal)):
            if pd.isna(sig):
                sig = prev_signal
            
            if sig != prev_signal:
                if sig == 1 and position == 0:
                    # 买入全仓
                    cost = self.calculate_transaction_cost(price, cash / price)
                    total_costs += cost
                    shares = (cash - cost) / price
                    position = 1
                    cash = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "buy",
                        "price": float(price)
                    })
                elif sig == 0 and position == 1:
                    # 卖出全仓
                    proceeds = shares * price
                    cost = self.calculate_transaction_cost(price, shares)
                    total_costs += cost
                    cash = proceeds - cost
                    shares = 0
                    position = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "sell",
                        "price": float(price)
                    })
                prev_signal = sig
            
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


class LowVolatilityStrategy(BaseStrategy):
    """低波动策略
    
    选择/持有低波动资产，在下跌市场中表现更好
    这里实现为：只在波动率低于阈值时持仓
    """
    def __init__(self, volatility_window: int = 20, volatility_threshold: float = 0.02):
        super().__init__()
        self.volatility_window = volatility_window
        self.volatility_threshold = volatility_threshold  # 日波动率阈值（2%）
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行低波动策略回测"""
        close = prices['close']
        
        # 计算滚动波动率
        returns = close.pct_change()
        rolling_vol = returns.rolling(self.volatility_window).std()
        
        # 信号：波动率低于阈值时持仓
        signal = pd.Series(0, index=close.index)
        signal[rolling_vol < self.volatility_threshold] = 1
        signal[rolling_vol >= self.volatility_threshold] = 0
        signal = signal.ffill().fillna(0)
        
        # 使用通用模拟
        return self._simulate_position(close, signal)
    
    def _simulate_position(self, close: pd.Series, position_signal: pd.Series) -> BacktestResult:
        """通用的仓位模拟带交易成本"""
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig) in enumerate(zip(close, position_signal)):
            if pd.isna(sig):
                sig = prev_signal
            
            if sig != prev_signal:
                if sig == 1 and position == 0:
                    # 买入全仓
                    cost = self.calculate_transaction_cost(price, cash / price)
                    total_costs += cost
                    shares = (cash - cost) / price
                    position = 1
                    cash = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "enter_low_vol",
                        "price": float(price)
                    })
                elif sig == 0 and position == 1:
                    # 卖出全仓
                    proceeds = shares * price
                    cost = self.calculate_transaction_cost(price, shares)
                    total_costs += cost
                    cash = proceeds - cost
                    shares = 0
                    position = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "exit_high_vol",
                        "price": float(price)
                    })
                prev_signal = sig
            
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


class GrahamDefensiveStrategy(BaseStrategy):
    """格雷厄姆防御性投资策略
    
    本杰明·格雷厄姆在《聪明的投资者》中提出的防御型投资者策略
    满足以下条件时长期持仓：
    - 市盈率 < 15
    - 市净率 < 1.5
    - 近年盈利稳定增长
    不满足条件时空仓
    """
    def __init__(self, pe_threshold: float = 15, pb_threshold: float = 1.5):
        super().__init__()
        self.pe_threshold = pe_threshold
        self.pb_threshold = pb_threshold
    
    def run(self, prices: pd.DataFrame, pe: pd.Series = None, pb: pd.Series = None) -> BacktestResult:
        """运行格雷厄姆策略回测
        
        如果没有提供PE/PB，简单用价格波动率替代（低估通常价格波动小）
        """
        close = prices['close']
        returns = close.pct_change()
        
        # 如果没有PE/PB数据，使用简单规则：只持有年化波动率低于15%的时段
        if pe is None or pb is None:
            rolling_vol = returns.rolling(252).std() * np.sqrt(252)
            signal = pd.Series(0, index=close.index)
            signal[rolling_vol < 0.15] = 1  # 波动率低于15%，满足防御条件
        else:
            # 有PE/PB数据时使用真实条件
            signal = pd.Series(0, index=close.index)
            mask = (pe < self.pe_threshold) & (pb < self.pb_threshold)
            signal[mask] = 1
        signal = signal.ffill().fillna(0)
        
        return self._simulate_position_generic(close, signal)
    
    def _simulate_position_generic(self, close: pd.Series, signal: pd.Series) -> BacktestResult:
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig) in enumerate(zip(close, signal)):
            if pd.isna(sig):
                sig = prev_signal
            
            if sig != prev_signal:
                if sig == 1 and position == 0:
                    cost = self.calculate_transaction_cost(price, cash / price)
                    total_costs += cost
                    shares = (cash - cost) / price
                    position = 1
                    cash = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "buy",
                        "price": float(price)
                    })
                elif sig == 0 and position == 1:
                    proceeds = shares * price
                    cost = self.calculate_transaction_cost(price, shares)
                    total_costs += cost
                    cash = proceeds - cost
                    shares = 0
                    position = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "sell",
                        "price": float(price)
                    })
                prev_signal = sig
            
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


class Momentum12MonthStrategy(BaseStrategy):
    """12个月动量策略
    
    每年调仓，持有过去12个月涨幅最高的资产
    这里实现为：根据过去12个月收益判断是否持有该资产
    如果过去12个月收益为正，则持有，否则空仓
    """
    def __init__(self, momentum_window: int = 252):
        super().__init__()
        self.momentum_window = momentum_window  # 动量窗口（交易日）
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行12个月动量策略回测"""
        close = prices['close']
        
        # 计算滚动过去N日的收益
        rolling_returns = close.pct_change(self.momentum_window)
        
        # 信号：过去N日收益 > 0 则持有
        signal = pd.Series(0, index=close.index)
        signal[rolling_returns > 0] = 1
        signal = signal.ffill().fillna(0)
        
        return self._simulate_position(close, signal)
    
    def _simulate_position(self, close: pd.Series, signal: pd.Series) -> BacktestResult:
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig) in enumerate(zip(close, signal)):
            if pd.isna(sig):
                sig = prev_signal
            
            if sig != prev_signal:
                if sig == 1 and position == 0:
                    cost = self.calculate_transaction_cost(price, cash / price)
                    total_costs += cost
                    shares = (cash - cost) / price
                    position = 1
                    cash = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "buy",
                        "price": float(price)
                    })
                elif sig == 0 and position == 1:
                    proceeds = shares * price
                    cost = self.calculate_transaction_cost(price, shares)
                    total_costs += cost
                    cash = proceeds - cost
                    shares = 0
                    position = 0
                    trades.append({
                        "date": str(close.index[date_idx]),
                        "type": "sell",
                        "price": float(price)
                    })
                prev_signal = sig
            
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


class TurtleTrendFollowingStrategy(BaseStrategy):
    """海龟交易法则 - 趋势跟随策略
    
    经典海龟交易法则：
    - 20日新高买入
    - 10日新低卖出
    - 使用ATR进行仓位管理
    """
    def __init__(self, entry_window: int = 20, exit_window: int = 10, atr_window: int = 20):
        super().__init__()
        self.entry_window = entry_window  # 入场窗口：N日新高
        self.exit_window = exit_window    # 离场窗口：N日新低
        self.atr_window = atr_window      # ATR计算窗口
    
    def run(self, prices: pd.DataFrame) -> BacktestResult:
        """运行海龟交易策略回测"""
        close = prices['close']
        high = prices.get('high', close)
        low = prices.get('low', close)
        
        # 计算N日最高/最低
        highest_high = high.rolling(self.entry_window).max()
        lowest_low = low.rolling(self.exit_window).min()
        
        # 计算ATR (真实波动幅度均值)
        tr = pd.DataFrame()
        tr['tr1'] = high - low
        tr['tr2'] = abs(high - close.shift(1))
        tr['tr3'] = abs(low - close.shift(1))
        tr['true_range'] = tr.max(axis=1)
        atr = tr['true_range'].rolling(self.atr_window).mean()
        
        # 生成信号
        # 价格突破20日新高 → 买入(1)
        # 价格跌破10日新低 → 卖出(0)
        signal = pd.Series(0, index=close.index)
        signal[close > highest_high] = 1
        signal[close < lowest_low] = 0
        signal = signal.ffill().fillna(0)
        
        return self._simulate_position_with_atr(close, signal, atr)
    
    def _simulate_position_with_atr(self, close: pd.Series, signal: pd.Series, atr: pd.Series) -> BacktestResult:
        """海龟仓位管理基于ATR"""
        position = 0.0
        cash = 1.0
        shares = 0.0
        equity = []
        trades = []
        total_costs = 0.0
        
        prev_signal = 0
        for date_idx, (price, sig, a) in enumerate(zip(close, signal, atr)):
            if pd.isna(sig):
                sig = prev_signal
            
            if sig != prev_signal:
                if sig == 1 and position == 0:
                    # 海龟法则：ATR止损 2% 账户权益
                    # 每个单位头寸风险不超过 2%
                    if not pd.isna(a) and a > 0:
                        # 计算可持仓数量：2% / ATR = 仓位比例
                        risk_per_unit = 0.02  # 2% 账户风险
                        position_size = (cash * risk_per_unit) / a
                        cost = self.calculate_transaction_cost(price, position_size)
                        total_costs += cost
                        shares = (cash - cost) / price
                        position = 1
                        cash = 0
                        trades.append({
                            "date": str(close.index[date_idx]),
                            "type": "buy",
                            "price": float(price),
                            "atr": float(a)
                        })
                elif sig == 0 and position == 1:
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
                        "atr": float(a) if not pd.isna(a) else None
                    })
                prev_signal = sig
            
            total_value = cash + shares * price
            equity.append((close.index[date_idx], total_value))
        
        df_equity = pd.DataFrame(equity, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
        returns = equity_series.pct_change().dropna()
        
        result = calculate_metrics(returns, trades)
        result.transaction_costs = total_costs * 100
        
        return result


# ========== 多资产回测框架 ==========
class MultiAssetBacktest:
    """多资产回测框架
    
    支持同时回测多个标的，按照权重配置
    """
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def run(
        self,
        prices_dict: Dict[str, pd.DataFrame],
        weights: Dict[str, float],
        rebalance_frequency: str = None  # 'monthly', 'quarterly', 'yearly', None=不再平衡
    ) -> BacktestResult:
        """运行多资产回测
        
        Args:
            prices_dict: {ticker: DataFrame} 价格数据字典
            weights: {ticker: weight} 权重配置
            rebalance_frequency: 再平衡频率
        
        Returns:
            回测结果
        """
        # 对齐日期索引，合并所有收盘价
        close_series = []
        for ticker, df in prices_dict.items():
            close = df['close'].rename(ticker)
            close_series.append(close)
        prices = pd.concat(close_series, axis=1).dropna()
        
        # 初始化权重
        weight_series = pd.Series(weights)
        weight_series = weight_series.reindex(prices.columns)
        weight_series = weight_series / weight_series.sum()
        
        # 模拟组合净值
        if rebalance_frequency is None:
            # 买入持有不再平衡
            returns = prices.pct_change().dropna()
            portfolio_returns = returns.dot(weight_series)
            result = calculate_metrics(portfolio_returns, None, self.risk_free_rate)
            return result
        else:
            # 定期再平衡
            return self._run_rebalancing(prices, weight_series, rebalance_frequency)
    
    def _run_rebalancing(
        self,
        prices: pd.DataFrame,
        target_weights: pd.Series,
        frequency: str
    ) -> BacktestResult:
        """带定期再平衡的回测"""
        n_assets = len(prices.columns)
        first_date = prices.index[0]
        total_value = 1.0
        
        # 初始持仓
        shares = {}
        for ticker, w in target_weights.items():
            price = prices[ticker].iloc[0]
            shares[ticker] = (total_value * w) / price
        
        equity_curve = []
        trades = []
        total_costs = 0.0
        commission_rate = 0.0003  # 万3
        
        # 按频率分组再平衡
        if frequency == 'monthly':
            groups = prices.groupby(prices.index.to_period('M'))
        elif frequency == 'quarterly':
            groups = prices.groupby(prices.index.to_period('Q'))
        elif frequency == 'yearly':
            groups = prices.groupby(prices.index.to_period('Y'))
        else:
            groups = prices.groupby(prices.index.to_period('M'))
        
        for period, group in groups:
            if len(group) == 0:
                continue
            
            # 每日记录净值
            for date_idx, (date, row) in enumerate(group.iterrows()):
                current_total = sum(shares[ticker] * row[ticker] for ticker in shares)
                equity_curve.append((date, current_total))
            
            # 最后一天再平衡
            last_date = group.index[-1]
            last_prices = row
            
            # 计算当前价值
            current_total = sum(shares[ticker] * last_prices[ticker] for ticker in shares)
            
            # 再平衡到目标权重
            for ticker, target_w in target_weights.items():
                target_value = current_total * target_w
                current_price = last_prices[ticker]
                current_value = shares[ticker] * current_price
                delta_value = target_value - current_value
                
                if abs(delta_value) > 1e-8:
                    # 需要调整
                    delta_shares = delta_value / current_price
                    commission = abs(delta_shares * current_price) * commission_rate
                    total_costs += commission
                    
                    if delta_shares > 0:
                        # 买入，佣金从现金（隐含在delta中）扣除
                        shares[ticker] = (target_value - commission) / current_price
                    else:
                        # 卖出，佣金从收入中扣除
                        shares[ticker] = target_value / current_price
                    
                    trades.append({
                        "date": str(last_date),
                        "type": "rebalance",
                        "ticker": ticker,
                        "target_weight": target_w
                    })
        
        # 计算收益率
        df_equity = pd.DataFrame(equity_curve, columns=['date', 'value']).set_index('date')
        equity_series = df_equity['value']
