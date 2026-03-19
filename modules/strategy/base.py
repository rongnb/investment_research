"""
策略基类模块 - 定义所有策略的抽象基类和接口规范
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
import numpy as np


class SignalType(Enum):
    """交易信号类型"""
    BUY = 1      # 买入信号
    SELL = -1    # 卖出信号
    HOLD = 0     # 持有/观望
    CLOSE_LONG = 2   # 平多仓
    CLOSE_SHORT = 3  # 平空仓


class Position(Enum):
    """持仓方向"""
    LONG = 1     # 多头
    SHORT = -1   # 空头
    NEUTRAL = 0  # 中性/现金


class TimeFrame(Enum):
    """时间周期"""
    TICK = "tick"
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


@dataclass
class Signal:
    """交易信号数据类"""
    symbol: str                           # 标的代码
    timestamp: datetime                   # 信号时间
    signal_type: SignalType               # 信号类型
    strength: float = 1.0                 # 信号强度 (0-1)
    price: Optional[float] = None         # 当前价格
    target_price: Optional[float] = None  # 目标价格
    stop_loss: Optional[float] = None     # 止损价格
    position: Position = Position.LONG    # 建议持仓方向
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    
    def __post_init__(self):
        if not 0 <= self.strength <= 1:
            self.strength = max(0.0, min(1.0, self.strength))


@dataclass
class StrategyConfig:
    """策略配置类"""
    name: str                             # 策略名称
    symbol: str                           # 交易标的
    time_frame: TimeFrame = TimeFrame.DAILY  # 时间周期
    initial_capital: float = 100000.0     # 初始资金
    commission: float = 0.001             # 手续费率
    slippage: float = 0.0005              # 滑点
    max_position: float = 1.0             # 最大持仓比例
    params: Dict[str, Any] = field(default_factory=dict)  # 策略参数
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """获取策略参数"""
        return self.params.get(key, default)


@dataclass 
class BacktestResult:
    """回测结果数据类"""
    total_return: float = 0.0             # 总收益率
    annual_return: float = 0.0            # 年化收益率
    sharpe_ratio: float = 0.0             # 夏普比率
    max_drawdown: float = 0.0             # 最大回撤
    win_rate: float = 0.0                 # 胜率
    profit_factor: float = 0.0            # 盈亏比
    trade_count: int = 0                  # 交易次数
    equity_curve: pd.Series = None        # 权益曲线
    trades: List[Dict] = field(default_factory=list)  # 交易记录


class Strategy(ABC):
    """
    策略抽象基类
    
    所有交易策略都必须继承此类并实现核心方法。
    策略设计遵循以下原则:
    - 单一职责: 每个策略只负责产生信号
    - 可配置: 通过参数配置实现灵活性
    - 可回测: 支持历史数据回测
    """
    
    def __init__(self, config: StrategyConfig):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.name = self.__class__.__name__
        self._indicators: Dict[str, pd.DataFrame] = {}
        self._last_signal: Optional[Signal] = None
        self._is_initialized = False
        
    @abstractmethod
    def initialize(self) -> None:
        """
        初始化策略
        
        在首次计算前调用,用于准备数据、计算指标等预处理工作
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            data:  OHLCV 格式的市场数据
            
        Returns:
            信号列表
        """
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        计算策略所需的技术指标
        
        Args:
            data: OHLCV 格式的市场数据
            
        Returns:
            指标数据字典
        """
        return self._indicators
    
    def get_required_columns(self) -> List[str]:
        """
        获取策略所需的数据列
        
        Returns:
            必需的列名列表
        """
        return ['open', 'high', 'low', 'close', 'volume']
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证数据有效性
        
        Args:
            data: 待验证的数据
            
        Returns:
            数据是否有效
        """
        required_cols = self.get_required_columns()
        return all(col in data.columns for col in required_cols)
    
    @property
    def last_signal(self) -> Optional[Signal]:
        """获取最后产生的信号"""
        return self._last_signal
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(symbol={self.config.symbol}, timeframe={self.config.time_frame.value})"


class SingleAssetStrategy(Strategy):
    """
    单标的策略基类
    
    适用于处理单一交易标的的策略
    """
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        pass
    
    def get_latest_signal(self, data: pd.DataFrame) -> Optional[Signal]:
        """
        获取最新信号
        
        Args:
            data: OHLCV 数据
            
        Returns:
            最新的交易信号
        """
        signals = self.generate_signals(data)
        if signals:
            return signals[-1]
        return None


class MultiAssetStrategy(Strategy):
    """
    多标的策略基类
    
    适用于需要处理多个交易标的的策略,如轮动策略、套利策略等
    """
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """
        生成多标的交易信号
        
        Args:
            data: 标的代码到数据的映射
            
        Returns:
            信号列表
        """
        pass
    
    def get_required_columns(self) -> List[str]:
        return ['open', 'high', 'low', 'close', 'volume']


class PortfolioStrategy(Strategy):
    """
    组合策略基类
    
    适用于需要管理多个仓位、控制组合风险的策略
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.positions: Dict[str, float] = {}  # 持仓权重
        self.rebalance_threshold: float = config.get_param('rebalance_threshold', 0.05)
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """
        生成组合权重调整信号
        
        Args:
            data: 标的代码到数据的映射
            
        Returns:
            权重调整信号列表
        """
        pass
    
    @abstractmethod
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        计算目标权重
        
        Args:
            data: 标的代码到数据的映射
            
        Returns:
            标的代码到权重的映射
        """
        pass
    
    def should_rebalance(self, current_weights: Dict[str, float], 
                         target_weights: Dict[str, float]) -> bool:
        """
        判断是否需要再平衡
        
        Args:
            current_weights: 当前权重
            target_weights: 目标权重
            
        Returns:
            是否需要再平衡
        """
        for symbol in target_weights:
            current = current_weights.get(symbol, 0)
            target = target_weights[symbol]
            if abs(target - current) > self.rebalance_threshold:
                return True
        return False


def create_signal(symbol: str, 
                 signal_type: SignalType,
                 price: Optional[float] = None,
                 strength: float = 1.0,
                 timestamp: Optional[datetime] = None,
                 **kwargs) -> Signal:
    """
    快速创建信号的工具函数
    
    Args:
        symbol: 标的代码
        signal_type: 信号类型
        price: 当前价格
        strength: 信号强度
        timestamp: 时间戳
        **kwargs: 其他参数
        
    Returns:
        Signal对象
    """
    return Signal(
        symbol=symbol,
        timestamp=timestamp or datetime.now(),
        signal_type=signal_type,
        price=price,
        strength=strength,
        **kwargs
    )