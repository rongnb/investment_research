"""
收益计算器
负责计算每日收益和绩效指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from ..common.models import Trade
from .metrics import calculate_comprehensive_metrics


class PerformanceCalculator:
    """
    收益计算器
    
    负责记录每日权益，计算收益率和绩效指标
    """
    
    def __init__(self,
                 initial_capital: float = 1000000.0,
                 risk_free_rate: float = 0.03,
                 periods_per_year: int = 252):
        """
        初始化收益计算器
        
        Args:
            initial_capital: 初始资金
            risk_free_rate: 无风险利率
            periods_per_year: 年交易周期数
        """
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
        
        self.daily_stats: List[Dict] = []
        self.trades: List[Trade] = []
        self.benchmark_returns: Optional[pd.Series] = None
        
    def reset(self):
        """重置收益计算器"""
        self.daily_stats.clear()
        self.trades.clear()
        self.benchmark_returns = None
    
    def set_benchmark(self, benchmark_data: pd.Series):
        """
        设置基准数据
        
        Args:
            benchmark_data: 基准价格序列
        """
        self.benchmark_returns = benchmark_data.pct_change().fillna(0)
    
    def update_daily_stats(self, timestamp: datetime, 
                          portfolio_value: float,
                          cash: float):
        """
        更新每日统计
        
        Args:
            timestamp: 日期
            portfolio_value: 投资组合总价值
            cash: 现金
        """
        position_value = portfolio_value - cash
        
        self.daily_stats.append({
            'date': timestamp,
            'portfolio_value': portfolio_value,
            'cash': cash,
            'position_value': position_value,
        })
    
    def add_trade(self, trade: Trade):
        """
        添加交易记录
        
        Args:
            trade: 交易对象
        """
        self.trades.append(trade)
    
    def get_daily_returns(self) -> pd.Series:
        """
        获取每日收益率序列
        
        Returns:
            每日收益率
        """
        if not self.daily_stats:
            return pd.Series()
        
        df = self._get_daily_df()
        returns = df['portfolio_value'].pct_change().fillna(0)
        return returns
    
    def get_equity_curve(self) -> pd.Series:
        """
        获取权益曲线
        
        Returns:
            权益曲线
        """
        if not self.daily_stats:
            return pd.Series()
        
        df = self._get_daily_df()
        return df['portfolio_value']
    
    def get_trades(self) -> List[Trade]:
        """
        获取所有交易记录
        
        Returns:
            交易列表
        """
        return self.trades
    
    def get_trade_summary(self) -> pd.DataFrame:
        """
        获取交易汇总表
        
        Returns:
            交易汇总DataFrame
        """
        if not self.trades:
            return pd.DataFrame(columns=[
                'id', 'code', 'direction', 'price', 'volume', 
                'amount', 'timestamp', 'commission', 'slippage'
            ])
        
        data = []
        for trade in self.trades:
            data.append({
                'id': trade.id,
                'code': trade.code,
                'direction': trade.direction.value,
                'price': trade.price,
                'volume': trade.volume,
                'amount': trade.amount,
                'timestamp': trade.timestamp,
                'commission': trade.commission,
                'slippage': trade.slippage
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    
    def calculate_metrics(self) -> Dict[str, float]:
        """
        计算所有绩效指标
        
        Returns:
            指标字典
        """
        daily_returns = self.get_daily_returns()
        
        if len(daily_returns) == 0:
            return {}
        
        # 计算基础指标
        metrics = calculate_comprehensive_metrics(
            daily_returns,
            self.benchmark_returns,
            self.risk_free_rate,
            self.periods_per_year
        )
        
        # 添加交易相关指标
        trade_metrics = self._calculate_trade_metrics()
        metrics.update(trade_metrics)
        
        return metrics
    
    def _calculate_trade_metrics(self) -> Dict[str, float]:
        """
        计算交易相关指标
        
        Returns:
            交易指标字典
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_trades': 0,
                'loss_trades': 0,
                'trade_win_rate': 0.0,
                'avg_trade_return': 0.0,
                'profit_loss_ratio': 0.0,
                'total_commission': 0.0,
                'total_slippage': 0.0,
                'total_trading_cost': 0.0
            }
        
        # 计算每笔交易盈亏
        trade_pnls = []
        profitable_trades = 0
        losing_trades = 0
        total_profit = 0.0
        total_loss = 0.0
        total_commission = 0.0
        total_slippage = 0.0
        
        # 按股票分组计算盈亏
        positions: Dict[str, List[Dict]] = {}
        
        for trade in self.trades:
            total_commission += trade.commission
            total_slippage += trade.slippage
            
            # 这里简化计算，假设买卖配对
            # 完整计算需要更复杂的配对逻辑
            if trade.direction.name == 'SELL':
                # 简单计算：卖出就是平仓，计算盈亏
                # 实际中需要根据持仓计算
                pass
        
        # 基于每日收益率计算交易统计（简化版）
        total_trades = len(self.trades)
        
        # 通过已实现盈亏计算胜率
        all_pnls = []
        for trade in self.trades:
            # 方向乘以价格可以反映大致方向，但实际需要配对
            # 这里我们通过交易对计算
            pass
        
        # 改用：基于每日收益统计交易
        # 胜率按交易次数计算
        # 真实盈亏配对需要更复杂逻辑，这里先返回基础统计
        return {
            'total_trades': total_trades,
            'total_commission': total_commission,
            'total_slippage': total_slippage,
            'total_trading_cost': total_commission + total_slippage,
            'avg_trade_cost': (total_commission + total_slippage) / total_trades if total_trades > 0 else 0,
        }
    
    def _get_daily_df(self) -> pd.DataFrame:
        """
        获取每日统计DataFrame
        
        Returns:
            DataFrame
        """
        df = pd.DataFrame(self.daily_stats)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df
    
    def get_drawdown_series(self) -> pd.Series:
        """
        获取回撤序列
        
        Returns:
            回撤序列
        """
        daily_returns = self.get_daily_returns()
        if len(daily_returns) == 0:
            return pd.Series()
        
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        
        return drawdown
    
    def get_cumulative_returns(self) -> pd.Series:
        """
        获取累积收益序列
        
        Returns:
            累积收益
        """
        daily_returns = self.get_daily_returns()
        return (1 + daily_returns).cumprod() - 1
