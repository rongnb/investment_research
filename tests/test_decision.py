"""
Tests for Decision Support Module
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
PROJECT_PATH = Path(__file__).parent.parent
sys.path.append(str(PROJECT_PATH))

from modules.decision.optimizer import PortfolioOptimizer, RiskTolerance

class TestPortfolioOptimizer(unittest.TestCase):
    """测试投资组合优化器"""
    
    def setUp(self):
        """测试前设置"""
        self.optimizer = PortfolioOptimizer()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.optimizer, PortfolioOptimizer)
    
    def test_synthetic_data_generation(self):
        """测试合成数据生成"""
        assets, covariance = self.optimizer.generate_synthetic_assets(10)
        
        self.assertIsNotNone(assets)
        self.assertIsNotNone(covariance)
        self.assertEqual(len(assets), 10)
        self.assertEqual(covariance.shape, (10, 10))
        
        self.assertIn('asset', assets.columns)
        self.assertIn('expected_return', assets.columns)
        self.assertIn('volatility', assets.columns)
    
    def test_risk_tolerance(self):
        """测试风险容忍度"""
        low_risk = PortfolioOptimizer(risk_tolerance=RiskTolerance.LOW)
        moderate_risk = PortfolioOptimizer(risk_tolerance=RiskTolerance.MODERATE)
        high_risk = PortfolioOptimizer(risk_tolerance=RiskTolerance.HIGH)
        
        self.assertIsInstance(low_risk, PortfolioOptimizer)
        self.assertIsInstance(moderate_risk, PortfolioOptimizer)
        self.assertIsInstance(high_risk, PortfolioOptimizer)
    
    def test_optimization_basic(self):
        """测试基础优化功能"""
        portfolio = self.optimizer.optimize_risk_return()
        
        self.assertIsNotNone(portfolio)
        self.assertIsInstance(portfolio.assets, dict)
        self.assertIsInstance(portfolio.expected_return, float)
        self.assertIsInstance(portfolio.volatility, float)
        self.assertIsInstance(portfolio.sharpe_ratio, float)
    
    def test_weight_allocation(self):
        """测试权重分配"""
        portfolio = self.optimizer.optimize_risk_return()
        allocations = self.optimizer.get_weight_allocation(portfolio)
        
        self.assertIsInstance(allocations, dict)
        self.assertEqual(len(allocations), len(portfolio.assets))
        
        total = sum(info['amount'] for info in allocations.values())
        self.assertAlmostEqual(total, 100000, places=2)
    
    def test_risk_assessment(self):
        """测试风险评估"""
        portfolio = self.optimizer.optimize_risk_return()
        risk_info = self.optimizer.risk_assessment(portfolio)
        
        self.assertIsInstance(risk_info, dict)
        self.assertIn('volatility', risk_info)
        self.assertIn('risk_score', risk_info)
        self.assertIn('risk_category', risk_info)
        self.assertIn('sharpe_ratio', risk_info)
        
        self.assertGreater(risk_info['volatility'], 0)
        self.assertGreater(risk_info['risk_score'], 0)
        self.assertIn(risk_info['risk_category'], ['低风险', '中风险', '高风险'])
        self.assertGreater(risk_info['sharpe_ratio'], 0)

if __name__ == '__main__':
    unittest.main()
