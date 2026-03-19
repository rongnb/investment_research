"""
持仓管理器
负责管理持仓信息，处理开平仓和持仓更新
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from ..common.models import Position, Trade, TradeDirection
from .engine import Order


class PositionManager:
    """
    持仓管理器
    
    负责管理所有持仓，处理资金和持仓更新
    """
    
    def __init__(self):
        """初始化持仓管理器"""
        self.positions: Dict[str, Position] = {}
        self.cash: float = 0.0
        self.initial_capital: float = 0.0
        
    def reset(self, initial_capital: float):
        """
        重置持仓管理器
        
        Args:
            initial_capital: 初始资金
        """
        self.positions.clear()
        self.initial_capital = initial_capital
        self.cash = initial_capital
    
    def get_position(self, code: str) -> Optional[Position]:
        """
        获取持仓
        
        Args:
            code: 股票代码
            
        Returns:
            持仓对象，如果不存在返回None
        """
        return self.positions.get(code)
    
    def get_total_position_value(self) -> float:
        """
        获取所有持仓的总市值
        
        Returns:
            总市值
        """
        return sum(
            pos.market_value for pos in self.positions.values()
        )
    
    def get_total_cost(self) -> float:
        """
        获取所有持仓的总成本
        
        Returns:
            总成本
        """
        return sum(
            pos.cost for pos in self.positions.values()
        ) + self.cash
    
    def get_total_pnl(self) -> float:
        """
        获取总盈亏 (已实现+未实现)
        
        Returns:
            总盈亏
        """
        unrealized = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        realized = sum(
            pos.realized_pnl for pos in self.positions.values()
        )
        return unrealized + realized
    
    def update_position(self, order: Order, trade: Trade):
        """
        根据成交订单更新持仓
        
        Args:
            order: 成交订单
            trade: 交易记录
        """
        code = order.code
        volume = order.filled_volume
        price = order.filled_price
        commission = order.commission
        
        # 更新资金
        if order.direction == TradeDirection.BUY:
            total_cost = volume * price + commission
            self.cash -= total_cost
            self._add_position(code, volume, price, order.timestamp)
        else:  # SELL
            total_proceeds = volume * price - commission
            self.cash += total_proceeds
            self._reduce_position(code, volume, price)
    
    def _add_position(self, code: str, volume: int, price: float, 
                     open_date: datetime):
        """
        增加持仓
        
        Args:
            code: 股票代码
            volume: 增加数量
            price: 成交价格
            open_date: 开仓日期
        """
        if code not in self.positions:
            # 新建持仓
            self.positions[code] = Position(
                code=code,
                volume=volume,
                avg_price=price,
                current_price=price,
                market_value=volume * price,
                cost=volume * price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                open_date=open_date
            )
        else:
            # 加仓
            position = self.positions[code]
            total_volume = position.volume + volume
            total_cost = position.cost + volume * price
            new_avg_price = total_cost / total_volume
            
            position.volume = total_volume
            position.cost = total_cost
            position.avg_price = new_avg_price
    
    def _reduce_position(self, code: str, volume: int, price: float):
        """
        减少持仓
        
        Args:
            code: 股票代码
            volume: 减少数量
            price: 成交价格
        """
        if code not in self.positions:
            return
        
        position = self.positions[code]
        
        # 计算已实现盈亏
        realized_pnl = (price - position.avg_price) * volume
        position.realized_pnl += realized_pnl
        
        # 减少持仓
        position.volume -= volume
        
        # 如果持仓为0，删除
        if position.volume <= 0:
            del self.positions[code]
    
    def update_market_price(self, code: str, current_price: float, 
                           timestamp: datetime):
        """
        更新最新市场价格，重新计算市值和未实现盈亏
        
        Args:
            code: 股票代码
            current_price: 当前价格
            timestamp: 当前时间戳
        """
        if code in self.positions:
            position = self.positions[code]
            position.current_price = current_price
            position.market_value = position.volume * current_price
            position.unrealized_pnl = (current_price - position.avg_price) * position.volume
    
    def update_all_market_prices(self, price_map: Dict[str, float], 
                                timestamp: datetime):
        """
        批量更新所有持仓的市场价格
        
        Args:
            price_map: {代码: 最新价格}
            timestamp: 当前时间戳
        """
        for code, price in price_map.items():
            self.update_market_price(code, price, timestamp)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓
        
        Returns:
            持仓字典
        """
        return self.positions.copy()
    
    def get_position_summary(self) -> pd.DataFrame:
        """
        获取持仓汇总表
        
        Returns:
            持仓汇总DataFrame
        """
        if not self.positions:
            return pd.DataFrame(columns=[
                'code', 'volume', 'avg_price', 'current_price', 
                'market_value', 'cost', 'unrealized_pnl', 'realized_pnl', 'pnl_pct'
            ])
        
        data = []
        for code, pos in self.positions.items():
            pnl_pct = pos.unrealized_pnl / pos.cost if pos.cost > 0 else 0
            data.append({
                'code': code,
                'volume': pos.volume,
                'avg_price': pos.avg_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'cost': pos.cost,
                'unrealized_pnl': pos.unrealized_pnl,
                'realized_pnl': pos.realized_pnl,
                'pnl_pct': pnl_pct
            })
        
        return pd.DataFrame(data).sort_values('market_value', ascending=False)
    
    def get_total_value(self) -> float:
        """
        获取总价值 (现金+持仓市值)
        
        Returns:
            总价值
        """
        return self.cash + self.get_total_position_value()
    
    def get_available_cash(self) -> float:
        """
        获取可用资金
        
        Returns:
            可用资金
        """
        return self.cash
    
    def is_empty(self) -> bool:
        """
        检查是否没有持仓
        
        Returns:
            是否为空
        """
        return len(self.positions) == 0
