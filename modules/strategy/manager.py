"""
策略管理器 - 策略注册、工厂、参数优化和组合管理
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any, Callable
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

from .base import (
    Strategy, StrategyConfig, Signal, SignalType,
    MultiAssetStrategy, PortfolioStrategy, BacktestResult
)


class StrategyRegistry:
    """
    策略注册表
    
    管理所有可用策略的注册和查询
    """
    
    _strategies: Dict[str, Type[Strategy]] = {}
    
    @classmethod
    def register(cls, name: str = None):
        """装饰器: 注册策略"""
        def decorator(strategy_class: Type[Strategy]):
            strategy_name = name or strategy_class.__name__
            cls._strategies[strategy_name] = strategy_class
            return strategy_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[Strategy]]:
        """获取策略类"""
        return cls._strategies.get(name)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出所有注册策略"""
        return list(cls._strategies.keys())
    
    @classmethod
    def create(cls, name: str, config: StrategyConfig) -> Strategy:
        """创建策略实例"""
        strategy_class = cls.get(name)
        if strategy_class is None:
            raise ValueError(f"Unknown strategy: {name}")
        return strategy_class(config)


class StrategyFactory:
    """
    策略工厂
    
    根据配置创建策略实例
    """
    
    def __init__(self):
        self._creators: Dict[str, Callable[[StrategyConfig], Strategy]] = {}
    
    def register(self, name: str, creator: Callable[[StrategyConfig], Strategy]):
        """注册策略创建器"""
        self._creators[name] = creator
    
    def create(self, name: str, config: StrategyConfig) -> Strategy:
        """创建策略实例"""
        if name in self._creators:
            return self._creators[name](config)
        
        # 尝试从注册表获取
        return StrategyRegistry.create(name, config)
    
    def list_available(self) -> List[str]:
        """列出可用策略"""
        return list(self._creators.keys()) + StrategyRegistry.list_strategies()


@dataclass
class OptimizationResult:
    """参数优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    optimization_time: float = 0.0


class ParameterOptimizer:
    """
    参数优化器
    
    使用网格搜索或随机搜索进行参数优化
    """
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
    
    def grid_search(self, 
                    param_grid: Dict[str, List[Any]],
                    data: pd.DataFrame,
                    metric: str = 'sharpe_ratio') -> OptimizationResult:
        """
        网格搜索优化
        
        Args:
            param_grid: 参数网格
            data: 回测数据
            metric: 评估指标
            
        Returns:
            优化结果
        """
        import time
        start_time = time.time()
        
        all_results = []
        
        # 生成所有参数组合
        import itertools
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        best_score = float('-inf')
        best_params = {}
        
        for combination in itertools.product(*values):
            params = dict(zip(keys, combination))
            
            # 创建新配置
            config = self.strategy.config
            config.params.update(params)
            
            # 创建新策略实例
            strategy = StrategyRegistry.create(
                self.strategy.__class__.__name__,
                config
            )
            
            # 生成信号并评估
            try:
                signals = strategy.generate_signals(data)
                score = self._evaluate(signals, metric)
                
                result = {'params': params, 'score': score}
                all_results.append(result)
                
                if score > best_score:
                    best_score = score
                    best_params = params
            except Exception as e:
                pass
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            optimization_time=optimization_time
        )
    
    def _evaluate(self, signals: List[Signal], metric: str) -> float:
        """评估信号"""
        if metric == 'sharpe_ratio':
            # 简化版夏普比率
            if len(signals) < 2:
                return 0.0
            returns = []
            for i in range(1, len(signals)):
                if signals[i].signal_type == SignalType.BUY:
                    returns.append(0.01)  # 假设1%收益
                elif signals[i].signal_type == SignalType.SELL:
                    returns.append(-0.01)
                else:
                    returns.append(0)
            
            if not returns:
                return 0.0
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            return mean_return / std_return * np.sqrt(252)
        
        elif metric == 'win_rate':
            if len(signals) < 2:
                return 0.0
            wins = sum(1 for i in range(1, len(signals)) 
                      if signals[i].signal_type == SignalType.BUY and 
                      signals[i-1].signal_type == SignalType.SELL)
            return wins / len(signals)
        
        return 0.0


class StrategyManager:
    """
    策略管理器
    
    统一管理策略的创建、运行、优化和组合
    """
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.strategies: Dict[str, Strategy] = {}
        self.factory = StrategyFactory()
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认策略"""
        # 经典策略
        from .classic.moving_average_crossover import MovingAverageCrossoverStrategy
        from .classic.macd_strategy import MACDStrategy
        from .classic.rsi_strategy import RSIStrategy
        from .classic.bollinger_strategy import BollingerBandsStrategy
        from .classic.breakout_strategy import BreakoutStrategy
        from .classic.mean_reversion import MeanReversionStrategy
        from .classic.momentum import ClassicMomentumStrategy
        
        # 高级策略
        from .advanced.multi_factor import MultiFactorStrategy
        from .advanced.style_rotation import StyleRotationStrategy
        from .advanced.sector_rotation import SectorRotationStrategy
        from .advanced.market_neutral import MarketNeutralStrategy
        
        # 组合策略
        from .portfolio.risk_parity import RiskParityStrategy
        from .portfolio.maximum_diversification import MaximumDiversificationStrategy
        from .portfolio.target_risk import TargetRiskStrategy
        from .portfolio.smart_beta import SmartBetaStrategy
    
    def add_strategy(self, name: str, config: StrategyConfig) -> Strategy:
        """添加策略"""
        strategy = self.factory.create(name, config)
        strategy.initialize()
        self.strategies[name] = strategy
        return strategy
    
    def remove_strategy(self, name: str):
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """获取策略"""
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self.strategies.keys())
    
    def run_strategy(self, name: str, data: pd.DataFrame) -> List[Signal]:
        """运行单个策略"""
        strategy = self.get_strategy(name)
        if strategy is None:
            raise ValueError(f"Strategy not found: {name}")
        return strategy.generate_signals(data)
    
    def run_all(self, data: pd.DataFrame) -> Dict[str, List[Signal]]:
        """运行所有策略"""
        results = {}
        for name, strategy in self.strategies.items():
            try:
                results[name] = strategy.generate_signals(data)
            except Exception as e:
                print(f"Error running strategy {name}: {e}")
                results[name] = []
        return results
    
    def combine_signals(self, 
                        signals_list: List[Signal],
                        method: str = 'majority') -> List[Signal]:
        """
        组合多个策略的信号
        
        Args:
            signals_list: 信号列表
            method: 组合方法 (majority/weighted/consensus)
            
        Returns:
            组合后的信号
        """
        if not signals_list:
            return []
        
        # 按时间和标的分组
        signal_groups: Dict[str, List[Signal]] = {}
        
        for signals in signals_list:
            for sig in signals:
                key = f"{sig.symbol}_{sig.timestamp}"
                if key not in signal_groups:
                    signal_groups[key] = []
                signal_groups[key].append(sig)
        
        combined = []
        
        for key, group in signal_groups.items():
            if method == 'majority':
                # 多数投票
                buy_count = sum(1 for s in group if s.signal_type == SignalType.BUY)
                sell_count = sum(1 for s in group if s.signal_type == SignalType.SELL)
                
                if buy_count > sell_count:
                    combined.append(group[0])  # 返回第一个
                elif sell_count > buy_count:
                    combined.append(group[0])
                    
            elif method == 'weighted':
                # 加权平均
                total_strength = sum(s.strength for s in group)
                avg_strength = total_strength / len(group)
                
                buy_strength = sum(s.strength for s in group 
                                  if s.signal_type == SignalType.BUY)
                sell_strength = sum(s.strength for s in group 
                                  if s.signal_type == SignalType.SELL)
                
                if buy_strength > sell_strength:
                    sig = group[0].copy()
                    sig.strength = avg_strength
                    combined.append(sig)
                elif sell_strength > buy_strength:
                    sig = group[0].copy()
                    sig.strength = avg_strength
                    combined.append(sig)
        
        return combined
    
    def optimize_strategy(self, 
                          name: str,
                          param_grid: Dict[str, List[Any]],
                          data: pd.DataFrame,
                          metric: str = 'sharpe_ratio') -> OptimizationResult:
        """优化策略参数"""
        strategy = self.get_strategy(name)
        if strategy is None:
            raise ValueError(f"Strategy not found: {name}")
        
        optimizer = ParameterOptimizer(strategy)
        return optimizer.grid_search(param_grid, data, metric)
    
    def save_config(self, filepath: str):
        """保存配置"""
        config_data = {
            'initial_capital': self.initial_capital,
            'strategies': []
        }
        
        for name, strategy in self.strategies.items():
            config_data['strategies'].append({
                'name': name,
                'config': {
                    'symbol': strategy.config.symbol,
                    'time_frame': strategy.config.time_frame.value,
                    'params': strategy.config.params
                }
            })
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self, filepath: str):
        """加载配置"""
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        self.initial_capital = config_data.get('initial_capital', 1000000)
        
        for strat_config in config_data.get('strategies', []):
            name = strat_config['name']
            cfg = strat_config['config']
            
            config = StrategyConfig(
                name=name,
                symbol=cfg.get('symbol', 'UNKNOWN'),
                time_frame=cfg.get('time_frame', '1d'),
                params=cfg.get('params', {})
            )
            
            self.add_strategy(name, config)


class CompositeStrategy(Strategy):
    """
    组合策略
    
    将多个策略组合成一个策略
    """
    
    def __init__(self, config: StrategyConfig, strategies: List[Strategy]):
        super().__init__(config)
        self.strategies = strategies
        self.combine_method = config.get_param('combine_method', 'majority')
    
    def initialize(self) -> None:
        for strategy in self.strategies:
            strategy.initialize()
        self._is_initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        all_signals = []
        
        for strategy in self.strategies:
            signals = strategy.generate_signals(data)
            all_signals.append(signals)
        
        # 组合信号
        # 这里简化处理，实际可以使用StrategyManager的combine_signals
        return all_signals[0] if all_signals else []


# 注册装饰器便捷函数
def register_strategy(name: str = None):
    """注册策略的便捷装饰器"""
    return StrategyRegistry.register(name)


# 全局策略工厂实例
_default_factory = StrategyFactory()


def get_factory() -> StrategyFactory:
    """获取全局策略工厂"""
    return _default_factory


def create_strategy(name: str, config: StrategyConfig) -> Strategy:
    """快速创建策略"""
    return _default_factory.create(name, config)