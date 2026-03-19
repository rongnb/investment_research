"""
回测引擎单元测试
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import os

from ..modules.backtest import (
    BacktestEngine,
    StrategyBase,
    DataHandler,
    OrderManager,
    PositionManager,
    PerformanceCalculator,
    ReportGenerator,
    calculate_comprehensive_metrics
)
from ..modules.common.models import (
    TradeDirection, OrderType, BarData, BacktestResult, Trade
)


class TestDataHandler(unittest.TestCase):
    """测试数据处理器"""
    
    def setUp(self):
        """创建测试数据"""
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')
        data = pd.DataFrame({
            'open': np.random.normal(100, 2, len(dates)),
            'high': np.random.normal(102, 2, len(dates)),
            'low': np.random.normal(98, 2, len(dates)),
            'close': np.random.normal(100, 2, len(dates)),
            'volume': np.random.randint(100000, 1000000, len(dates)),
            'code': '000001'
        }, index=dates)
        self.data = data
        self.handler = DataHandler()
    
    def test_set_data(self):
        """测试设置数据"""
        self.handler.set_data(self.data)
        self.assertIsNotNone(self.handler.data)
        self.assertEqual(len(self.handler.sorted_dates), len(self.data))
    
    def test_get_bars_date_filter(self):
        """测试日期过滤"""
        self.handler.set_data(self.data)
        bars = self.handler.get_bars('2023-06-01', '2023-06-30')
        self.assertGreater(len(bars), 0)
        self.assertLessEqual(len(bars), 30)
    
    def test_get_codes(self):
        """测试获取股票代码"""
        self.handler.set_data(self.data)
        codes = self.handler.get_codes()
        self.assertEqual(codes, ['000001'])


class TestOrderManager(unittest.TestCase):
    """测试订单管理器"""
    
    def setUp(self):
        self.manager = OrderManager(
            commission_rate=0.0003,
            min_commission=5.0,
            stamp_duty_rate=0.001,
            slippage=0.001
        )
    
    def test_add_order(self):
        """测试添加订单"""
        from ..modules.backtest.engine import Order
        order = Order(
            id='test1',
            code='000001',
            direction=TradeDirection.BUY,
            price=100.0,
            volume=1000,
            order_type=OrderType.MARKET,
            timestamp=datetime.now()
        )
        self.manager.add_order(order)
        self.assertEqual(len(self.manager.orders), 1)
    
    def test_execute_buy_insufficient_cash(self):
        """测试买入资金不足"""
        from ..modules.backtest.engine import Order
        order = Order(
            id='test1',
            code='000001',
            direction=TradeDirection.BUY,
            price=100.0,
            volume=10000,
            order_type=OrderType.MARKET,
            timestamp=datetime.now()
        )
        self.manager.add_order(order)
        executed, trade = self.manager.execute_order(order, current_cash=10000, current_positions={})
        self.assertEqual(executed.status, 'filled')
        self.assertLess(executed.volume, 10000)
        self.assertIsNotNone(trade)


class TestPositionManager(unittest.TestCase):
    """测试持仓管理器"""
    
    def setUp(self):
        self.manager = PositionManager()
        self.manager.reset(1000000.0)
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.manager.cash, 1000000.0)
        self.assertTrue(self.manager.is_empty())
    
    def test_add_position(self):
        """测试增加持仓"""
        from ..modules.backtest.engine import Order
        from ..modules.common.models import Trade
        
        order = Order(
            id='test1',
            code='000001',
            direction=TradeDirection.BUY,
            price=100.0,
            volume=1000,
            order_type=OrderType.MARKET,
            timestamp=datetime.now()
        )
        order.filled_volume = 1000
        order.filled_price = 100.0
        order.commission = 30.0
        
        trade = Trade(
            id='test1',
            code='000001',
            direction=TradeDirection.BUY,
            price=100.0,
            volume=1000,
            amount=100000,
            timestamp=datetime.now(),
            commission=30.0
        )
        
        self.manager.update_position(order, trade)
        self.assertEqual(len(self.manager.positions), 1)
        position = self.manager.get_position('000001')
        self.assertIsNotNone(position)
        self.assertEqual(position.volume, 1000)


class TestPerformanceCalculator(unittest.TestCase):
    """测试收益计算器"""
    
    def setUp(self):
        self.calc = PerformanceCalculator(
            initial_capital=1000000.0,
            risk_free_rate=0.03
        )
    
    def test_calculate_metrics(self):
        """测试计算指标"""
        # 添加模拟每日数据
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')
        base_value = 1000000.0
        for date in dates:
            # 模拟每天微小上涨
            daily_return = np.random.normal(0.0005, 0.01)
            base_value *= (1 + daily_return)
            self.calc.update_daily_stats(date, base_value, base_value * 0.3)
        
        metrics = self.calc.calculate_metrics()
        self.assertIn('total_return', metrics)
        self.assertIn('annualized_return', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertGreater(len(metrics), 10)


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎"""
    
    def setUp(self):
        """创建简单测试策略"""
        # 生成测试数据
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='B')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
        
        data = pd.DataFrame({
            'open': prices - 0.5,
            'high': prices + 1,
            'low': prices - 1,
            'close': prices,
            'volume': np.random.randint(100000, 1000000, len(dates)),
            'code': '000001'
        }, index=dates)
        self.data = data
        
        # 创建简单策略 - 简单均线策略
        class SimpleMAStrategy(StrategyBase):
            def __init__(self):
                super().__init__("SimpleMA")
                self.bought = False
            
            def on_bar(self, bar: BarData):
                if bar.close > 100 and not self.bought:
                    self.buy('000001', bar.close, 1000)
                    self.bought = True
                elif bar.close < 95 and self.bought:
                    position = self.get_position('000001')
                    if position:
                        self.sell('000001', bar.close, position.volume)
                        self.bought = False
        
        self.strategy = SimpleMAStrategy()
        self.engine = BacktestEngine(
            initial_capital=100000.0,
            commission_rate=0.0003,
            slippage=0.001
        )
        self.engine.add_strategy(self.strategy)
    
    def test_run_backtest(self):
        """测试运行回测"""
        result = self.engine.run(self.data)
        self.assertIsInstance(result, BacktestResult)
        self.assertGreater(len(result.daily_returns), 0)
        self.assertIsNotNone(result.equity_curve)
        self.assertTrue(hasattr(result, 'metrics'))
        metrics = result.metrics
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('max_drawdown', metrics)
    
    def test_metrics_count(self):
        """测试指标数量超过20种"""
        result = self.engine.run(self.data)
        metrics = result.metrics
        self.assertGreater(len(metrics), 20)


class TestReportGenerator(unittest.TestCase):
    """测试报告生成器"""
    
    def setUp(self):
        # 创建模拟回测结果
        from ..modules.common.models import BacktestResult
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')
        daily_returns = pd.Series(np.random.normal(0.0005, 0.02, len(dates)), index=dates)
        equity_curve = 1000000 * (1 + daily_returns).cumprod()
        
        self.result = BacktestResult(
            strategy_name='TestStrategy',
            start_date=dates[0],
            end_date=dates[-1],
            initial_capital=1000000,
            final_value=equity_curve.iloc[-1],
            total_return=(equity_curve.iloc[-1] / 1000000) - 1,
            annualized_return=0.15,
            volatility=0.15,
            sharpe_ratio=0.8,
            max_drawdown=0.1,
            win_rate=0.55,
            profit_factor=1.2,
            trades=[],
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
        self.result.metrics = calculate_comprehensive_metrics(daily_returns)
        self.generator = ReportGenerator(self.result)
    
    def test_generate_html(self):
        """测试生成HTML报告"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name
        
        try:
            result_path = self.generator.generate_html(output_path, title="测试回测报告")
            self.assertTrue(os.path.exists(result_path))
            self.assertGreater(os.path.getsize(result_path), 1000)
            
            # 读取内容检查关键元素
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('核心绩效指标', content)
            self.assertIn('权益曲线', content)
            self.assertIn('回撤曲线', content)
        finally:
            os.unlink(output_path)
    
    def test_generate_json(self):
        """测试生成JSON报告"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            result_path = self.generator.generate_json(output_path)
            self.assertTrue(os.path.exists(result_path))
            self.assertGreater(os.path.getsize(result_path), 100)
        finally:
            os.unlink(output_path)


class TestComprehensiveMetrics(unittest.TestCase):
    """测试综合指标计算"""
    
    def test_metrics_coverage(self):
        """测试指标覆盖超过20种"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 252))
        benchmark = pd.Series(np.random.normal(0.0003, 0.015, 252))
        
        metrics = calculate_comprehensive_metrics(returns, benchmark)
        
        # 检查指标数量
        self.assertGreater(len(metrics), 20)
        
        # 检查关键指标存在
        key_metrics = [
            'total_return', 'annualized_return', 'volatility',
            'max_drawdown', 'max_drawdown_duration',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'omega_ratio',
            'win_rate', 'profit_loss_ratio', 'beta', 'alpha', 'information_ratio',
            'skewness', 'kurtosis', 'var_95', 'var_99'
        ]
        for metric in key_metrics:
            self.assertIn(metric, metrics)


if __name__ == '__main__':
    unittest.main()
