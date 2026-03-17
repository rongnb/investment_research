"""
Tests for Macro Analysis Module
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
PROJECT_PATH = Path(__file__).parent.parent
sys.path.append(str(PROJECT_PATH))

from modules.macro.analyzer import MacroAnalyzer, EconomicCycle

class TestMacroAnalyzer(unittest.TestCase):
    """测试宏观经济分析器"""
    
    def setUp(self):
        """测试前设置"""
        self.analyzer = MacroAnalyzer()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.analyzer, MacroAnalyzer)
    
    def test_fetch_indicators(self):
        """测试获取经济指标"""
        indicators = self.analyzer.fetch_economic_indicators("2020-01-01", "2024-12-31")
        
        self.assertIsNotNone(indicators)
        self.assertIsInstance(indicators.gdp_growth, float)
        self.assertIsInstance(indicators.cpi, float)
        self.assertIsInstance(indicators.ppi, float)
        self.assertIsInstance(indicators.interest_rate, float)
        self.assertIsInstance(indicators.unemployment_rate, float)
        self.assertIsInstance(indicators.money_supply, float)
        self.assertIsInstance(indicators.consumer_confidence, float)
        self.assertIsInstance(indicators.manufacturing_pmi, float)
    
    def test_analyze_cycle(self):
        """测试经济周期判断"""
        indicators = self.analyzer.fetch_economic_indicators("2020-01-01", "2024-12-31")
        cycle = self.analyzer.analyze_economic_cycle(indicators)
        
        self.assertIsNotNone(cycle)
        self.assertIsInstance(cycle, EconomicCycle)
    
    def test_report_generation(self):
        """测试报告生成"""
        indicators = self.analyzer.fetch_economic_indicators("2020-01-01", "2024-12-31")
        cycle = self.analyzer.analyze_economic_cycle(indicators)
        report = self.analyzer.generate_macro_report(indicators, cycle)
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        self.assertIn("宏观经济分析报告", report)
    
    def test_cycle_values(self):
        """测试周期阶段"""
        cycle_values = [v.value for v in EconomicCycle]
        
        self.assertIn("复苏期", cycle_values)
        self.assertIn("扩张期", cycle_values)
        self.assertIn("顶峰期", cycle_values)
        self.assertIn("收缩期", cycle_values)
        self.assertIn("低谷期", cycle_values)

if __name__ == '__main__':
    unittest.main()
