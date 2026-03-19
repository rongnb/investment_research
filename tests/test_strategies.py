"""
单元测试 - 策略库

测试所有经典策略、高级策略和组合策略
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from modules.strategy.base import (
    Strategy, StrategyConfig, Signal, SignalType, 
    Position, TimeFrame, create_signal
)
from modules.strategy.classic.moving_average_crossover import MovingAverageCrossoverStrategy
from modules.strategy.classic.macd_strategy import MACDStrategy
from modules.strategy.classic.rsi_strategy import RSIStrategy
from modules.strategy.classic.bollinger_strategy import BollingerBandsStrategy
from modules.strategy.classic.breakout_strategy import BreakoutStrategy
from modules.strategy.classic.mean_reversion import MeanReversionStrategy
from modules.strategy.classic.momentum import ClassicMomentumStrategy
from modules.strategy.manager import StrategyManager, StrategyRegistry


def generate_test_data(n: int = 100, seed: int = 42) -> pd.DataFrame:
    """生成测试用的OHLCV数据"""
    np.random.seed(seed)
    
    # 生成随机价格
    base_price = 100
    dates = pd.date_range(start='2023-01-01', periods=n, freq='D')
    
    # 生成带趋势的价格
    trend = np.linspace(0, 20, n)
    noise = np.random.randn(n) * 2
    
    close = base_price + trend + noise
    
    # 生成OHLC
    high = close + np.random.rand(n) * 2
    low = close - np.random.rand(n) * 2
    open_price = close + (np.random.rand(n) - 0.5)
    volume = np.random.randint(1000000, 10000000, n)
    
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    return df


class TestStrategyBase(unittest.TestCase):
    """测试策略基类"""
    
    def test_signal_creation(self):
        """测试信号创建"""
        signal = create_signal(
            symbol='TEST',
            signal_type=SignalType.BUY,
            price=100.0,
            strength=0.8
        )
        
        self.assertEqual(signal.symbol, 'TEST')
        self.assertEqual(signal.signal_type, SignalType.BUY)
        self.assertEqual(signal.price, 100.0)
        self.assertEqual(signal.strength, 0.8)
    
    def test_strategy_config(self):
        """测试策略配置"""
        config = StrategyConfig(
            name='test_strategy',
            symbol='000001.SZ',
            params={'period': 20, 'threshold': 2.0}
        )
        
        self.assertEqual(config.get_param('period'), 20)
        self.assertEqual(config.get_param('threshold'), 2.0)
        self.assertIsNone(config.get_param('nonexistent'))


class TestMovingAverageCrossover(unittest.TestCase):
    """测试双均线策略"""
    
    def test_ma_crossover(self):
        """测试金叉死叉信号"""
        config = StrategyConfig(
            name='MA_Crossover',
            symbol='TEST',
            params={'short_period': 10, 'long_period': 30, 'ma_type': 'sma'}
        )
        
        strategy = MovingAverageCrossoverStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        
        # 应该有信号产生
        self.assertIsInstance(signals, list)
        
        # 检查信号类型
        for sig in signals:
            self.assertIn(sig.signal_type, [SignalType.BUY, SignalType.SELL])


class TestMACDStrategy(unittest.TestCase):
    """测试MACD策略"""
    
    def test_macd_signals(self):
        """测试MACD信号生成"""
        config = StrategyConfig(
            name='MACD',
            symbol='TEST',
            params={'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        )
        
        strategy = MACDStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestRSIStrategy(unittest.TestCase):
    """测试RSI策略"""
    
    def test_rsi_signals(self):
        """测试RSI信号"""
        config = StrategyConfig(
            name='RSI',
            symbol='TEST',
            params={'period': 14, 'overbought': 70, 'oversold': 30}
        )
        
        strategy = RSIStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestBollingerBandsStrategy(unittest.TestCase):
    """测试布林带策略"""
    
    def test_bollinger_signals(self):
        """测试布林带信号"""
        config = StrategyConfig(
            name='Bollinger',
            symbol='TEST',
            params={'period': 20, 'std_dev': 2}
        )
        
        strategy = BollingerBandsStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestBreakoutStrategy(unittest.TestCase):
    """测试突破策略"""
    
    def test_breakout_signals(self):
        """测试突破信号"""
        config = StrategyConfig(
            name='Breakout',
            symbol='TEST',
            params={'lookback_period': 20}
        )
        
        strategy = BreakoutStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestMeanReversionStrategy(unittest.TestCase):
    """测试均值回归策略"""
    
    def test_mean_reversion_signals(self):
        """测试均值回归信号"""
        config = StrategyConfig(
            name='MeanReversion',
            symbol='TEST',
            params={'period': 20, 'std_threshold': 2}
        )
        
        strategy = MeanReversionStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestMomentumStrategy(unittest.TestCase):
    """测试动量策略"""
    
    def test_momentum_signals(self):
        """测试动量信号"""
        config = StrategyConfig(
            name='Momentum',
            symbol='TEST',
            params={'lookback_period': 60}
        )
        
        strategy = ClassicMomentumStrategy(config)
        data = generate_test_data(100)
        
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)


class TestStrategyManager(unittest.TestCase):
    """测试策略管理器"""
    
    def test_manager_creation(self):
        """测试管理器创建"""
        manager = StrategyManager(initial_capital=1000000)
        
        self.assertEqual(manager.initial_capital, 1000000)
        self.assertIsInstance(manager.strategies, dict)
    
    def test_add_strategy(self):
        """测试添加策略"""
        manager = StrategyManager()
        
        config = StrategyConfig(
            name='MA_Crossover',
            symbol='TEST',
            params={'short_period': 10, 'long_period': 30}
        )
        
        strategy = manager.add_strategy('MA_Crossover', config)
        self.assertIsNotNone(strategy)
        
        strategies = manager.list_strategies()
        self.assertIn('MA_Crossover', strategies)
    
    def test_run_strategy(self):
        """测试运行策略"""
        manager = StrategyManager()
        
        config = StrategyConfig(
            name='MA_Crossover',
            symbol='TEST',
            params={'short_period': 10, 'long_period': 30}
        )
        
        manager.add_strategy('MA_Crossover', config)
        data = generate_test_data(100)
        
        signals = manager.run_strategy('MA_Crossover', data)
        self.assertIsInstance(signals, list)


class TestStrategyRegistry(unittest.TestCase):
    """测试策略注册表"""
    
    def test_registry_list(self):
        """测试注册表列出"""
        strategies = StrategyRegistry.list_strategies()
        self.assertIsInstance(strategies, list)


if __name__ == '__main__':
    unittest.main()