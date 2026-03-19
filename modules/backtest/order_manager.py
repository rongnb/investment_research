"""
订单管理器
负责订单管理和执行，支持滑点和手续费模拟
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..common.models import (
    Trade, TradeDirection, OrderType, Position
)
from ..common.exceptions import ExecutionError
from .engine import Order


class OrderManager:
    """
    订单管理器
    
    负责订单添加、执行、成交处理，支持滑点和手续费模拟
    """
    
    def __init__(self,
                 commission_rate: float = 0.0003,
                 min_commission: float = 5.0,
                 stamp_duty_rate: float = 0.001,
                 slippage: float = 0.001):
        """
        初始化订单管理器
        
        Args:
            commission_rate: 佣金费率
            min_commission: 最低佣金
            stamp_duty_rate: 印花税费率 (仅卖出)
            slippage: 滑点比例
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage = slippage
        
        self.orders: Dict[str, Order] = {}
        self.filled_orders: List[Order] = []
        self.rejected_orders: List[Order] = []
        
    def reset(self):
        """重置订单管理器"""
        self.orders.clear()
        self.filled_orders.clear()
        self.rejected_orders.clear()
    
    def add_order(self, order: Order) -> None:
        """
        添加订单
        
        Args:
            order: 订单对象
        """
        self.orders[order.id] = order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单对象
        """
        return self.orders.get(order_id)
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == "pending":
                order.status = "cancelled"
                self.rejected_orders.append(order)
                del self.orders[order_id]
                return True
        return False
    
    def execute_order(self, order: Order, 
                     current_cash: float,
                     current_positions: Dict[str, Position]) -> Tuple[Order, Optional[Trade]]:
        """
        执行订单，考虑滑点、手续费和资金检查
        
        Args:
            order: 订单对象
            current_cash: 当前可用资金
            current_positions: 当前持仓
            
        Returns:
            (执行后的订单, 交易记录)
        """
        # 计算实际成交价 (加入滑点)
        if order.direction == TradeDirection.BUY:
            fill_price = order.price * (1 + self.slippage)
        else:
            fill_price = order.price * (1 - self.slippage)
        
        # 初始成交量为订单请求的成交量
        requested_volume = order.volume
        available_volume = requested_volume
        
        # 检查资金/持仓是否足够
        if order.direction == TradeDirection.BUY:
            # 计算预估成本
            estimated_commission = max(
                requested_volume * fill_price * self.commission_rate,
                self.min_commission
            )
            estimated_total = requested_volume * fill_price + estimated_commission
            
            if current_cash < estimated_total:
                # 资金不足，计算可购买数量
                available_volume = int((current_cash - self.min_commission) / 
                                      (fill_price * (1 + self.commission_rate)))
                
                if available_volume <= 0:
                    order.status = "rejected"
                    self.rejected_orders.append(order)
                    del self.orders[order.id]
                    return order, None
                    
                order.volume = available_volume
        else:  # SELL
            # 检查持仓是否足够
            position = current_positions.get(order.code)
            if not position or position.volume < requested_volume:
                if not position or position.volume <= 0:
                    order.status = "rejected"
                    self.rejected_orders.append(order)
                    del self.orders[order.id]
                    return order, None
                available_volume = position.volume
                order.volume = available_volume
        
        # 计算手续费
        trade_amount = order.volume * fill_price
        commission = max(
            order.volume * fill_price * self.commission_rate,
            self.min_commission
        )
        
        # 印花税 (仅卖出)
        stamp_duty = 0.0
        if order.direction == TradeDirection.SELL:
            stamp_duty = order.volume * fill_price * self.stamp_duty_rate
        
        total_cost = commission + stamp_duty
        slippage_cost = abs(order.price - fill_price) * order.volume
        
        # 更新订单状态
        order.filled_volume = order.volume
        order.filled_price = fill_price
        order.commission = total_cost
        order.status = "filled"
        
        # 创建交易记录
        trade = Trade(
            id=order.id,
            code=order.code,
            direction=order.direction,
            price=fill_price,
            volume=order.volume,
            amount=trade_amount,
            timestamp=order.timestamp,
            order_type=order.order_type,
            commission=commission,
            slippage=slippage_cost
        )
        
        # 移动到已成交列表
        self.filled_orders.append(order)
        del self.orders[order.id]
        
        return order, trade
    
    def calculate_execution_cost(self, order: Order) -> float:
        """
        计算执行成本 (佣金+滑点+印花税)
        
        Args:
            order: 已成交订单
            
        Returns:
            总执行成本
        """
        if order.status != "filled":
            return 0.0
        
        slippage_cost = abs(order.price - order.filled_price) * order.filled_volume
        return order.commission + slippage_cost
    
    def get_pending_orders(self) -> List[Order]:
        """获取待执行订单"""
        return [o for o in self.orders.values() if o.status == "pending"]
    
    def get_all_filled_orders(self) -> List[Order]:
        """获取所有已成交订单"""
        return self.filled_orders
    
    def get_all_rejected_orders(self) -> List[Order]:
        """获取所有已拒绝订单"""
        return self.rejected_orders
    
    def get_order_statistics(self) -> Dict[str, int]:
        """获取订单统计信息"""
        return {
            "total": len(self.filled_orders) + len(self.rejected_orders) + len(self.orders),
            "pending": len(self.get_pending_orders()),
            "filled": len(self.filled_orders),
            "rejected": len(self.rejected_orders)
        }
