# -*- coding: utf-8 -*-
"""
Top-down 分析框架

自上而下的大类资产配置和选股策略
支持宏观经济 → 行业配置 → 个股选择的完整流程
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class AssetClass(Enum):
    """资产类别"""
    EQUITY = "equity"              # 股票
    BOND = "bond"                   # 债券
    COMMODITY = "commodity"       # 商品
    CASH = "cash"                   # 现金
    ALTERNATIVE = "alternative"   # 另类投资


class EconomicPhase(Enum):
    """经济周期阶段"""
    RECOVERY = "recovery"           # 复苏
    EXPANSION = "expansion"         # 扩张
    SLOWDOWN = "slowdown"           # 放缓
    CONTRACTION = "contraction"     # 收缩


@dataclass
class MacroIndicator:
    """宏观经济指标"""
    name: str
    value: float
    yoy_change: float
    mom_change: float
    date: datetime
    unit: str = ""
    frequency: str = "monthly"  # daily/weekly/monthly/quarterly/yearly


@dataclass
class SectorAllocation:
    """行业配置"""
    sector_name: str
    sector_code: str
    weight: float                    # 配置权重
    target_price: Optional[float]    # 目标价
    current_price: Optional[float]   # 当前价
    upside_potential: Optional[float]  # 上涨空间
    rating: str                      # 评级
    key_drivers: List[str]           # 关键驱动因素
    risks: List[str]                 # 风险因素


@dataclass
class StockSelection:
    """个股选择"""
    stock_code: str
    stock_name: str
    sector: str
    weight: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int
    rationale: str
    technical_signals: List[str]
    fundamental_scores: Dict[str, float]


@dataclass
class TopDownStrategy:
    """Top-down 策略配置"""
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    
    # 宏观经济配置
    economic_phase: EconomicPhase
    macro_indicators: List[MacroIndicator]
    
    # 资产配置
    asset_allocation: Dict[AssetClass, float]
    
    # 行业配置
    sector_allocations: List[SectorAllocation]
    
    # 个股选择
    stock_selections: List[StockSelection]
    
    # 风险管理
    max_drawdown: float
    volatility_target: float
    rebalance_frequency: str


class TopDownAnalyzer:
    """
    Top-down 分析器
    
    提供自上而下的分析框架，包括：
    1. 宏观经济分析
    2. 行业配置分析
    3. 个股选择分析
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 经济周期判断阈值
        self.gdp_growth_threshold = self.config.get('gdp_growth_threshold', 6.0)
        self.inflation_threshold = self.config.get('inflation_threshold', 3.0)
        self.unemployment_threshold = self.config.get('unemployment_threshold', 5.0)
        
    def analyze_economic_cycle(self, indicators: List[MacroIndicator]) -> EconomicPhase:
        """
        分析经济周期阶段
        
        Args:
            indicators: 宏观经济指标列表
            
        Returns:
            经济周期阶段
        """
        # 提取关键指标
        gdp_growth = None
        inflation = None
        unemployment = None
        
        for indicator in indicators:
            if indicator.name == "GDP_GROWTH":
                gdp_growth = indicator.value
            elif indicator.name == "CPI":
                inflation = indicator.value
            elif indicator.name == "UNEMPLOYMENT":
                unemployment = indicator.value
        
        # 判断经济周期
        if gdp_growth is None:
            return EconomicPhase.EXPANSION  # 默认扩张期
        
        if gdp_growth > self.gdp_growth_threshold:
            if inflation and inflation < self.inflation_threshold:
                return EconomicPhase.EXPANSION  # 高增长低通胀 = 扩张
            else:
                return EconomicPhase.SLOWDOWN  # 高增长高通胀 = 放缓
        else:
            if inflation and inflation < self.inflation_threshold:
                return EconomicPhase.RECOVERY  # 低增长低通胀 = 复苏
            else:
                return EconomicPhase.CONTRACTION  # 低增长高通胀 = 收缩
    
    def generate_asset_allocation(self, phase: EconomicPhase) -> Dict[AssetClass, float]:
        """
        根据经济周期生成资产配置建议
        
        Args:
            phase: 经济周期阶段
            
        Returns:
            资产配置权重
        """
        allocations = {
            EconomicPhase.RECOVERY: {
                AssetClass.EQUITY: 0.50,      # 复苏期：增加股票
                AssetClass.BOND: 0.20,
                AssetClass.COMMODITY: 0.10,
                AssetClass.CASH: 0.15,
                AssetClass.ALTERNATIVE: 0.05
            },
            EconomicPhase.EXPANSION: {
                AssetClass.EQUITY: 0.60,      # 扩张期：重仓股票
                AssetClass.BOND: 0.15,
                AssetClass.COMMODITY: 0.10,
                AssetClass.CASH: 0.05,
                AssetClass.ALTERNATIVE: 0.10
            },
            EconomicPhase.SLOWDOWN: {
                AssetClass.EQUITY: 0.35,      # 放缓期：减少股票
                AssetClass.BOND: 0.35,        # 增加债券
                AssetClass.COMMODITY: 0.10,
                AssetClass.CASH: 0.15,
                AssetClass.ALTERNATIVE: 0.05
            },
            EconomicPhase.CONTRACTION: {
                AssetClass.EQUITY: 0.20,      # 收缩期：轻仓股票
                AssetClass.BOND: 0.40,        # 重仓债券
                AssetClass.COMMODITY: 0.05,
                AssetClass.CASH: 0.30,        # 增加现金
                AssetClass.ALTERNATIVE: 0.05
            }
        }
        
        return allocations.get(phase, allocations[EconomicPhase.EXPANSION])
    
    def analyze_sector_rotation(self, phase: EconomicPhase) -> List[str]:
        """
        分析行业轮动
        
        根据经济周期阶段推荐重点关注的行业
        
        Args:
            phase: 经济周期阶段
            
        Returns:
            推荐行业列表
        """
        sector_recommendations = {
            EconomicPhase.RECOVERY: [
                "金融", "地产", "可选消费", "工业"
            ],
            EconomicPhase.EXPANSION: [
                "科技", "新能源", "消费", "医疗健康"
            ],
            EconomicPhase.SLOWDOWN: [
                "公用事业", "消费必需品", "医疗保健", "高股息"
            ],
            EconomicPhase.CONTRACTION: [
                "债券", "黄金", "公用事业", "防御性行业"
            ]
        }
        
        return sector_recommendations.get(phase, [])
    
    def generate_strategy_report(self, strategy: TopDownStrategy) -> str:
        """
        生成策略报告
        
        Args:
            strategy: 策略配置
            
        Returns:
            报告文本
        """
        report = []
        report.append("=" * 60)
        report.append(f"Top-Down 投资策略报告: {strategy.name}")
        report.append("=" * 60)
        report.append("")
        
        # 经济周期
        report.append("【经济周期分析】")
        report.append(f"当前阶段: {strategy.economic_phase.value}")
        report.append("")
        
        # 宏观指标
        report.append("【宏观经济指标】")
        for indicator in strategy.macro_indicators:
            report.append(f"  {indicator.name}: {indicator.value}{indicator.unit}")
            report.append(f"    同比: {indicator.yoy_change:+.2f}%, 环比: {indicator.mom_change:+.2f}%")
        report.append("")
        
        # 资产配置
        report.append("【资产配置建议】")
        for asset, weight in strategy.asset_allocation.items():
            report.append(f"  {asset.value}: {weight*100:.1f}%")
        report.append("")
        
        # 行业配置
        report.append("【行业配置建议】")
        for sector in strategy.sector_allocations:
            report.append(f"  {sector.sector_name}: {sector.weight*100:.1f}% ({sector.rating})")
        report.append("")
        
        # 个股选择
        if strategy.stock_selections:
            report.append("【个股选择】")
            for stock in strategy.stock_selections:
                report.append(f"  {stock.stock_name} ({stock.stock_code})")
                report.append(f"    仓位: {stock.weight*100:.1f}%, 买入价: {stock.entry_price:.2f}")
            report.append("")
        
        # 风险管理
        report.append("【风险管理】")
        report.append(f"  最大回撤限制: {strategy.max_drawdown*100:.1f}%")
        report.append(f"  波动率目标: {strategy.volatility_target*100:.1f}%")
        report.append(f"  调仓频率: {strategy.rebalance_frequency}")
        report.append("")
        
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # 测试代码
    print("Top-down 分析器测试")
    
    analyzer = TopDownAnalyzer()
    
    # 模拟宏观经济指标
    indicators = [
        MacroIndicator("GDP_GROWTH", 5.2, 0.3, 0.1, datetime(2024, 12, 1), "%", "quarterly"),
        MacroIndicator("CPI", 2.1, -0.5, 0.2, datetime(2024, 12, 1), "%", "monthly"),
        MacroIndicator("UNEMPLOYMENT", 4.8, -0.2, -0.1, datetime(2024, 12, 1), "%", "monthly"),
    ]
    
    # 分析经济周期
    phase = analyzer.analyze_economic_cycle(indicators)
    print(f"\n经济周期: {phase.value}")
    
    # 生成资产配置
    allocation = analyzer.generate_asset_allocation(phase)
    print("\n资产配置:")
    for asset, weight in allocation.items():
        print(f"  {asset.value}: {weight*100:.1f}%")
    
    # 分析行业轮动
    sectors = analyzer.analyze_sector_rotation(phase)
    print("\n推荐行业:")
    for sector in sectors:
        print(f"  - {sector}")
