"""
回测引擎核心模块
提供事件驱动的回测框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import warnings
warnings.filterwarnings('ignore')

from ..common.models import (
    Trade, TradeDirection, OrderType, Position, Portfolio, 
    BarData, BacktestResult, Signal, SignalType
)
from ..common.exceptions import BacktestError, ExecutionError
from .metrics import calculate_comprehensive_metrics
from .data_handler import DataHandler
from .order_manager import OrderManager
from .position_manager import PositionManager
from .performance_calculator import PerformanceCalculator


class EventType(Enum):
    """事件类型"""
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    BAR = "bar"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    REBALANCE = "rebalance"


@dataclass
class Event:
    """事件对象"""
    event_type: EventType
    timestamp: datetime
    data: Any = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class Order:
    """订单对象"""
    id: str
    code: str
    direction: TradeDirection
    price: float
    volume: int
    order_type: OrderType
    timestamp: datetime
    status: str = "pending"  # pending, filled, partial, cancelled, rejected
    filled_volume: int = 0
    filled_price: float = 0.0
    commission: float = 0.0


class StrategyBase:
    """策略基类"""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self.engine = None
        
    def on_init(self, engine: 'BacktestEngine'):
        """策略初始化"""
        self.engine = engine
        
    def on_bar(self, bar: BarData):
        """K线数据事件"""
        pass
    
    def on_signal(self, signal: Signal):
        """信号事件"""
        pass
    
    def on_order_filled(self, order: Order):
        """订单成交事件"""
        pass
    
    def on_market_open(self, timestamp: datetime):
        """市场开盘事件"""
        pass
    
    def on_market_close(self, timestamp: datetime):
        """市场收盘事件"""
        pass
    
    def buy(self, code: str, price: float, volume: int, 
            order_type: OrderType = OrderType.MARKET):
        """买入下单"""
        if self.engine:
            self.engine.place_order(code, TradeDirection.BUY, price, 
                                   volume, order_type)
    
    def sell(self, code: str, price: float, volume: int,
             order_type: OrderType = OrderType.MARKET):
        """卖出下单"""
        if self.engine:
            self.engine.place_order(code, TradeDirection.SELL, price,
                                   volume, order_type)
    
    def get_position(self, code: str) -> Optional[Position]:
        """获取持仓"""
        if self.engine:
            return self.engine.get_position(code)
        return None
    
    def get_portfolio(self) -> Portfolio:
        """获取投资组合"""
        if self.engine:
            return self.engine.get_portfolio()
        return None


class BacktestEngine:
    """
    事件驱动回测引擎
    
    支持滑点、手续费、滑点模拟，提供完整的回测框架
    """
    
    def __init__(self, 
                 initial_capital: float = 1000000.0,
                 commission_rate: float = 0.0003,
                 min_commission: float = 5.0,
                 stamp_duty_rate: float = 0.001,
                 slippage: float = 0.001,
                 risk_free_rate: float = 0.03,
                 periods_per_year: int = 252):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 佣金费率
            min_commission: 最低佣金
            stamp_duty_rate: 印花税费率 (仅卖出)
            slippage: 滑点比例
            risk_free_rate: 无风险利率
            periods_per_year: 年交易周期数
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
        
        # 组件初始化
        self.data_handler: Optional[DataHandler] = None
        self.order_manager: Optional[OrderManager] = None
        self.position_manager: Optional[PositionManager] = None
        self.performance_calculator: Optional[PerformanceCalculator] = None
        
        # 策略列表
        self.strategies: List[StrategyBase] = []
        
        # 当前状态
        self.current_time: Optional[datetime] = None
        self.current_bar: Optional[BarData] = None
        self.is_running: bool = False
        
        # 事件队列
        self.event_queue: List[Event] = []
        
        # 初始化组件
        self._init_components()
    
    def _init_components(self):
        """初始化各个组件"""
        self.data_handler = DataHandler()
        self.order_manager = OrderManager(
            commission_rate=self.commission_rate,
            min_commission=self.min_commission,
            stamp_duty_rate=self.stamp_duty_rate,
            slippage=self.slippage
        )
        self.position_manager = PositionManager()
        self.performance_calculator = PerformanceCalculator(
            initial_capital=self.initial_capital,
            risk_free_rate=self.risk_free_rate,
            periods_per_year=self.periods_per_year
        )
    
    def add_strategy(self, strategy: StrategyBase) -> 'BacktestEngine':
        """添加策略"""
        self.strategies.append(strategy)
        return self
    
    def set_data(self, data: pd.DataFrame) -> 'BacktestEngine':
        """设置回测数据"""
        if self.data_handler is not None:
            self.data_handler.set_data(data)
        return self
    
    def set_benchmark_data(self, benchmark_data: pd.Series) -> 'BacktestEngine':
        """设置基准数据"""
        if self.performance_calculator is not None:
            self.performance_calculator.set_benchmark(benchmark_data)
        return self
    
    def place_order(self, code: str, direction: TradeDirection,
                   price: float, volume: int,
                   order_type: OrderType = OrderType.MARKET) -> str:
        """
        下单
        
        Args:
            code: 股票代码
            direction: 交易方向
            price: 价格
            volume: 数量
            order_type: 订单类型
            
        Returns:
            订单ID
        """
        if self.order_manager is None or self.position_manager is None:
            raise BacktestError("回测引擎未初始化")
        
        order_id = str(uuid.uuid4())
        
        # 市价单使用当前bar的收盘价
        if order_type == OrderType.MARKET and self.current_bar is not None:
            price = self.current_bar.close
        
        order = Order(
            id=order_id,
            code=code,
            direction=direction,
            price=price,
            volume=volume,
            order_type=order_type,
            timestamp=self.current_time
        )
        
        # 添加到订单管理器
        self.order_manager.add_order(order)
        
        # 推送订单事件
        self.event_queue.append(Event(
            event_type=EventType.ORDER,
            timestamp=self.current_time,
            data=order
        ))
        
        return order_id
    
    def _process_events(self):
        """处理事件队列"""
        while self.event_queue and self.is_running:
            event = self.event_queue.pop(0)
            self._process_event(event)
    
    def _process_event(self, event: Event):
        """处理单个事件"""
        if event.event_type == EventType.MARKET_OPEN:
            self._handle_market_open(event)
        elif event.event_type == EventType.BAR:
            self._handle_bar(event)
        elif event.event_type == EventType.ORDER:
            self._handle_order(event)
        elif event.event_type == EventType.FILL:
            self._handle_fill(event)
        elif event.event_type == EventType.MARKET_CLOSE:
            self._handle_market_close(event)
    
    def _handle_market_open(self, event: Event):
        """处理开盘事件"""
        timestamp = event.timestamp
        for strategy in self.strategies:
            strategy.on_market_open(timestamp)
    
    def _handle_bar(self, event: Event):
        """处理K线数据事件"""
        bar = event.data
        self.current_bar = bar
        self.current_time = bar.timestamp
        
        # 更新持仓市值
        if self.position_manager is not None:
            self.position_manager.update_market_price(
                bar.code, bar.close, bar.timestamp
            )
        
        # 通知策略
        for strategy in self.strategies:
            strategy.on_bar(bar)
    
    def _handle_order(self, event: Event):
        """处理订单事件"""
        if self.order_manager is None or self.position_manager is None:
            return
        
        order = event.data
        
        # 执行订单
        filled_order, trade = self.order_manager.execute_order(
            order, 
            current_cash=self.position_manager.cash,
            current_positions=self.position_manager.positions
        )
        
        if filled_order.status == "filled":
            # 更新持仓
            self.position_manager.update_position(filled_order, trade)
            
            # 推送成交事件
            self.event_queue.append(Event(
                event_type=EventType.FILL,
                timestamp=self.current_time,
                data={"order": filled_order, "trade": trade}
            ))
    
    def _handle_fill(self, event: Event):
        """处理成交事件"""
        data = event.data
        order = data["order"]
        
        # 通知策略订单成交
        for strategy in self.strategies:
            strategy.on_order_filled(order)
        
        # 记录交易
        if self.performance_calculator is not None:
            self.performance_calculator.add_trade(data["trade"])
    
    def _handle_market_close(self, event: Event):
        """处理收盘事件"""
        timestamp = event.timestamp
        
        # 计算当日投资组合价值
        portfolio_value = self.get_portfolio_value()
        
        # 更新每日绩效
        if self.performance_calculator is not None:
            self.performance_calculator.update_daily_stats(
                timestamp, 
                portfolio_value,
                self.position_manager.cash if self.position_manager else 0
            )
        
        # 通知策略
        for strategy in self.strategies:
            strategy.on_market_close(timestamp)
    
    def get_position(self, code: str) -> Optional[Position]:
        """获取持仓"""
        if self.position_manager is not None:
            return self.position_manager.get_position(code)
        return None
    
    def get_portfolio(self) -> Portfolio:
        """获取投资组合"""
        if self.position_manager is None:
            raise BacktestError("回测引擎未初始化")
        
        position_value = self.position_manager.get_total_position_value()
        total_value = self.position_manager.cash + position_value
        total_cost = self.position_manager.get_total_cost()
        total_pnl = total_value - total_cost
        
        return Portfolio(
            positions=self.position_manager.positions.copy(),
            cash=self.position_manager.cash,
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            date=self.current_time
        )
    
    def get_portfolio_value(self) -> float:
        """获取投资组合总价值"""
        if self.position_manager is None:
            return self.initial_capital
        
        position_value = self.position_manager.get_total_position_value()
        return self.position_manager.cash + position_value
    
    def run(self, data: pd.DataFrame = None, 
            start_date: str = None,
            end_date: str = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: 回测数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果
        """
        if data is not None:
            self.set_data(data)
        
        if self.data_handler is None or self.data_handler.data is None:
            raise BacktestError("未设置回测数据")
        
        # 过滤日期范围
        backtest_data = self.data_handler.get_bars(start_date, end_date)
        
        if len(backtest_data) == 0:
            raise BacktestError("指定日期范围内没有数据")
        
        # 重置所有组件状态
        self._reset_state()
        
        # 通知策略初始化
        for strategy in self.strategies:
            strategy.on_init(self)
        
        self.is_running = True
        
        # 获取日期范围
        dates = sorted(backtest_data.index.unique())
        start_dt = dates[0]
        end_dt = dates[-1]
        
        # 遍历每个交易日
        for date in dates:
            self.current_time = date
            
            # 推送开盘事件
            self.event_queue.append(Event(
                event_type=EventType.MARKET_OPEN,
                timestamp=date
            ))
            
            # 获取当日所有K线
            daily_bars = backtest_data.loc[date]
            
            if isinstance(daily_bars, pd.Series):
                daily_bars = [daily_bars]
            
            for _, bar_row in daily_bars.iterrows() if hasattr(daily_bars, 'iterrows') else enumerate(daily_bars):
                # 创建BarData对象
                if isinstance(bar_row, pd.Series):
                    bar = BarData(
                        code=bar_row.get('code', 'UNKNOWN'),
                        timestamp=date,
                        open=float(bar_row['open']),
                        high=float(bar_row['high']),
                        low=float(bar_row['low']),
                        close=float(bar_row['close']),
                        volume=int(bar_row['volume']),
                        amount=float(bar_row.get('amount', 0)),
                        frequency='1d'
                    )
                else:
                    continue
                
                # 推送K线事件
                self.event_queue.append(Event(
                    event_type=EventType.BAR,
                    timestamp=date,
                    data=bar
                ))
            
            # 推送收盘事件
            self.event_queue.append(Event(
                event_type=EventType.MARKET_CLOSE,
                timestamp=date
            ))
            
            # 处理所有事件
            self._process_events()
        
        self.is_running = False
        
        # 生成回测结果
        return self._generate_result(strategy_name=self.strategies[0].name if self.strategies else "Strategy",
                                     start_date=start_dt,
                                     end_date=end_dt)
    
    def _reset_state(self):
        """重置所有组件状态"""
        if self.order_manager is not None:
            self.order_manager.reset()
        if self.position_manager is not None:
            self.position_manager.reset(self.initial_capital)
        if self.performance_calculator is not None:
            self.performance_calculator.reset()
        self.event_queue.clear()
        self.current_time = None
        self.current_bar = None
    
    def _generate_result(self, strategy_name: str, 
                        start_date: datetime, 
                        end_date: datetime) -> BacktestResult:
        """生成回测结果"""
        if self.performance_calculator is None:
            raise BacktestError("绩效计算器未初始化")
        
        # 获取计算好的每日收益率
        daily_returns = self.performance_calculator.get_daily_returns()
        equity_curve = self.performance_calculator.get_equity_curve()
        trades = self.performance_calculator.get_trades()
        
        # 获取最终结果
        final_value = self.get_portfolio_value()
        metrics = self.performance_calculator.calculate_metrics()
        
        # 创建BacktestResult对象
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return=metrics.get('total_return', 0),
            annualized_return=metrics.get('annualized_return', 0),
            volatility=metrics.get('volatility', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            max_drawdown=abs(metrics.get('max_drawdown', 0)),
            win_rate=metrics.get('trade_win_rate', 0) if 'trade_win_rate' in metrics else metrics.get('win_rate', 0),
            profit_factor=metrics.get('profit_loss_ratio', 1.0),
            trades=trades,
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
        
        # 保存完整指标供报告使用
        result.metrics = metrics  # type: ignore
        
        return result
    
    def get_metrics(self) -> Dict[str, float]:
        """
        获取所有绩效指标
        
        Returns:
            指标字典
        """
        if self.performance_calculator is not None:
            return self.performance_calculator.calculate_metrics()
        return {}
    
    def get_daily_equity(self) -> pd.Series:
        """
        获取每日权益曲线
        
        Returns:
            权益曲线
        """
        if self.performance_calculator is not None:
            return self.performance_calculator.get_equity_curve()
        return pd.Series()
    
    def get_trades(self) -> List[Trade]:
        """
        获取所有交易记录
        
        Returns:
            交易列表
        """
        if self.performance_calculator is not None:
            return self.performance_calculator.get_trades()
        return []
    
    def get_drawdown_series(self) -> pd.Series:
        """
        获取回撤序列
        
        Returns:
            回撤序列
        """
        if self.performance_calculator is not None:
            return self.performance_calculator.get_drawdown_series()
        return pd.Series()