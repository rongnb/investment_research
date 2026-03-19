# -*- coding: utf-8 -*-
"""
宏观情景分析模块

建立宏观情景分析框架（基准/乐观/悲观）
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """情景类型"""
    BASE = "base"        # 基准情景
    OPTIMISTIC = "optimistic"  # 乐观情景
    PESSIMISTIC = "pessimistic"  # 悲观情景


@dataclass
class ScenarioProjection:
    """情景预测"""
    scenario: ScenarioType
    probability: float  # 概率 0-1
    gdp_growth: float
    cpi: float
    ppi: float
    pmi: float
    interest_rate: float
    money_supply: float
    stock_return: float  # 预期股票收益
    bond_return: float   # 预期债券收益
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ScenarioAnalysis:
    """情景分析结果"""
    base: ScenarioProjection
    optimistic: ScenarioProjection
    pessimistic: ScenarioProjection
    weighted_return: float  # 加权预期收益
    risk_score: float       # 风险评分 0-10
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_probability_weighted_returns(self) -> Dict[str, float]:
        """获取概率加权收益"""
        return {
            "stocks": (
                self.base.stock_return * self.base.probability +
                self.optimistic.stock_return * self.optimistic.probability +
                self.pessimistic.stock_return * self.pessimistic.probability
            ),
            "bonds": (
                self.base.bond_return * self.base.probability +
                self.optimistic.bond_return * self.optimistic.probability +
                self.pessimistic.bond_return * self.pessimistic.probability
            )
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "base_probability": self.base.probability,
            "optimistic_probability": self.optimistic.probability,
            "pessimistic_probability": self.pessimistic.probability,
            "weighted_stock_return": self.weighted_return,
            "risk_score": self.risk_score,
            "recommended_allocation": self._recommend_allocation()
        }
    
    def _recommend_allocation(self) -> Dict[str, float]:
        """推荐资产配置"""
        if self.risk_score < 4:
            # 低风险 - 债券为主
            return {"stocks": 0.30, "bonds": 0.50, "cash": 0.20}
        elif self.risk_score < 7:
            # 中风险 - 平衡
            return {"stocks": 0.50, "bonds": 0.35, "cash": 0.15}
        else:
            # 高风险 - 股票为主
            return {"stocks": 0.70, "bonds": 0.20, "cash": 0.10}


class ScenarioAnalyzer:
    """
    宏观情景分析器
    
    基于当前宏观环境生成三种情景假设
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze(
        self,
        current_indicators: Dict[str, float],
        cycle: str = "recovery"
    ) -> ScenarioAnalysis:
        """
        执行情景分析
        
        Args:
            current_indicators: 当前经济指标
            cycle: 当前经济周期阶段
            
        Returns:
            ScenarioAnalysis结果
        """
        # 根据当前状态调整情景参数
        base = self._generate_base_scenario(current_indicators, cycle)
        optimistic = self._generate_optimistic_scenario(current_indicators, cycle)
        pessimistic = self._generate_pessimistic_scenario(current_indicators, cycle)
        
        # 计算加权收益
        weighted = (
            base.stock_return * base.probability +
            optimistic.stock_return * optimistic.probability +
            pessimistic.stock_return * pessimistic.probability
        )
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(current_indicators, optimistic, pessimistic)
        
        return ScenarioAnalysis(
            base=base,
            optimistic=optimistic,
            pessimistic=pessimistic,
            weighted_return=weighted,
            risk_score=risk_score
        )
    
    def _generate_base_scenario(
        self,
        indicators: Dict[str, float],
        cycle: str
    ) -> ScenarioProjection:
        """生成基准情景"""
        # 基于当前指标的基准预测
        gdp = indicators.get("gdp_growth", 5.0)
        pmi = indicators.get("pmi", 50)
        cpi = indicators.get("cpi", 2.0)
        
        # 基准预测：维持当前趋势
        base_gdp = gdp
        base_cpi = cpi
        base_ppi = indicators.get("ppi", 0)
        base_pmi = pmi
        base_rate = indicators.get("interest_rate", 3.45)
        base_m2 = indicators.get("money_supply", 8)
        
        # 根据周期调整
        if cycle in ["expansion", "peak"]:
            base_gdp = min(gdp * 0.9, gdp - 0.5)  # 增长放缓
            base_pmi = min(pmi - 2, 50)
        elif cycle in ["recovery"]:
            base_gdp = min(gdp + 0.3, 6)  # 温和复苏
            base_pmi = min(pmi + 1, 52)
        
        # 预期收益
        stock_return = self._estimate_stock_return(base_gdp, base_pmi, base_cpi)
        bond_return = base_rate - 1.5  # 简化计算
        
        return ScenarioProjection(
            scenario=ScenarioType.BASE,
            probability=0.60,
            gdp_growth=base_gdp,
            cpi=base_cpi,
            ppi=base_ppi,
            pmi=base_pmi,
            interest_rate=base_rate,
            money_supply=base_m2,
            stock_return=stock_return,
            bond_return=bond_return,
            recommendations=self._get_base_recommendations(cycle)
        )
    
    def _generate_optimistic_scenario(
        self,
        indicators: Dict[str, float],
        cycle: str
    ) -> ScenarioProjection:
        """生成乐观情景"""
        gdp = indicators.get("gdp_growth", 5.0)
        pmi = indicators.get("pmi", 50)
        cpi = indicators.get("cpi", 2.0)
        
        # 乐观预测：政策刺激超预期
        opt_gdp = min(gdp + 1.5, 8)
        opt_cpi = min(cpi + 1, 4)
        opt_ppi = indicators.get("ppi", 0) + 3
        opt_pmi = min(pmi + 5, 55)
        opt_rate = indicators.get("interest_rate", 3.45) - 0.25
        opt_m2 = indicators.get("money_supply", 8) + 3
        
        # 乐观收益
        stock_return = self._estimate_stock_return(opt_gdp, opt_pmi, opt_cpi) * 1.3
        bond_return = opt_rate - 1
        
        return ScenarioProjection(
            scenario=ScenarioType.OPTIMISTIC,
            probability=0.20,
            gdp_growth=opt_gdp,
            cpi=opt_cpi,
            ppi=opt_ppi,
            pmi=opt_pmi,
            interest_rate=opt_rate,
            money_supply=opt_m2,
            stock_return=stock_return,
            bond_return=bond_return,
            recommendations=[
                "超配股票，特别是周期和成长风格",
                "增加商品和资源类资产配置",
                "降低债券久期",
                "关注高Beta行业"
            ]
        )
    
    def _generate_pessimistic_scenario(
        self,
        indicators: Dict[str, float],
        cycle: str
    ) -> ScenarioProjection:
        """生成悲观情景"""
        gdp = indicators.get("gdp_growth", 5.0)
        pmi = indicators.get("pmi", 50)
        cpi = indicators.get("cpi", 2.0)
        
        # 悲观预测：经济超预期下行
        pess_gdp = max(gdp - 2, 2)
        pess_cpi = max(cpi - 1, 0)
        pess_ppi = indicators.get("ppi", 0) - 4
        pess_pmi = max(pmi - 5, 45)
        pess_rate = indicators.get("interest_rate", 3.45) + 0.25
        pess_m2 = max(indicators.get("money_supply", 8) - 2, 5)
        
        # 悲观收益
        stock_return = self._estimate_stock_return(pess_gdp, pess_pmi, pess_cpi) * 0.5 - 0.1
        bond_return = pess_rate + 1  # 避险需求
        
        return ScenarioProjection(
            scenario=ScenarioType.PESSIMISTIC,
            probability=0.20,
            gdp_growth=pess_gdp,
            cpi=pess_cpi,
            ppi=pess_ppi,
            pmi=pess_pmi,
            interest_rate=pess_rate,
            money_supply=pess_m2,
            stock_return=stock_return,
            bond_return=bond_return,
            recommendations=[
                "低配股票，增加国债和现金",
                "关注防御性行业（消费、医药、公用事业）",
                "增加债券久期",
                "保持充足流动性"
            ]
        )
    
    def _estimate_stock_return(
        self,
        gdp: float,
        pmi: float,
        cpi: float
    ) -> float:
        """简化估算股票预期收益"""
        # 基于宏观指标的简化模型
        score = 0
        
        # GDP贡献
        if gdp > 6:
            score += 0.15
        elif gdp > 4:
            score += 0.05
        else:
            score -= 0.10
        
        # PMI贡献
        if pmi > 52:
            score += 0.10
        elif pmi > 50:
            score += 0.02
        else:
            score -= 0.08
        
        # CPI贡献（温和通胀最佳）
        if 1 < cpi < 3:
            score += 0.05
        elif cpi < 0:
            score -= 0.05  # 通缩风险
        
        # 基础收益
        base_return = 0.08  # 8%的基础收益
        
        return base_return + score
    
    def _calculate_risk_score(
        self,
        indicators: Dict[str, float],
        optimistic: ScenarioProjection,
        pessimistic: ScenarioProjection
    ) -> float:
        """计算风险评分 (0-10)"""
        score = 5.0  # 中等基础分
        
        # PMI风险
        pmi = indicators.get("pmi", 50)
        if pmi < 48:
            score += 2
        elif pmi < 50:
            score += 1
        elif pmi > 52:
            score -= 1
        
        # GDP风险
        gdp = indicators.get("gdp_growth", 5)
        if gdp < 4:
            score += 2
        elif gdp < 5:
            score += 1
        elif gdp > 6:
            score -= 1
        
        # PPI风险
        ppi = indicators.get("ppi", 0)
        if ppi < -3:
            score += 1.5
        elif ppi < 0:
            score += 0.5
        
        # 情景差异
        return_diff = optimistic.stock_return - pessimistic.stock_return
        if return_diff > 0.5:
            score += 1
        elif return_diff > 0.3:
            score += 0.5
        
        return max(0, min(10, score))
    
    def _get_base_recommendations(self, cycle: str) -> List[str]:
        """基准情景建议"""
        if cycle in ["recovery"]:
            return [
                "适度增加股票配置",
                "关注顺周期行业",
                "保持债券和现金平衡",
                "关注政策边际变化"
            ]
        elif cycle in ["expansion"]:
            return [
                "维持股票中高配置",
                "关注成长和周期风格",
                "适度配置商品",
                "开始关注债券风险"
            ]
        elif cycle in ["peak"]:
            return [
                "逐步降低股票仓位",
                "增加防御性资产",
                "提高债券配置",
                "保持流动性"
            ]
        elif cycle in ["contraction"]:
            return [
                "低配股票",
                "增加国债配置",
                "保持现金充裕",
                "等待抄底机会"
            ]
        else:  # trough
            return [
                "准备逢低布局",
                "关注优质资产",
                "增加长期国债",
                "保持耐心"
            ]
    
    def generate_report(self, analysis: ScenarioAnalysis) -> str:
        """生成情景分析报告"""
        report = f"""
{'='*60}
宏观情景分析报告
{'='*60}

生成时间: {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}

一、情景概率
-----------
基准情景: {analysis.base.probability:.0%}
乐观情景: {analysis.optimistic.probability:.0%}
悲观情景: {analysis.pessimistic.probability:.0%}

二、情景对比
-----------

| 指标       | 基准情景 | 乐观情景 | 悲观情景 |
|------------|----------|----------|----------|
| GDP增长    | {analysis.base.gdp_growth:.1f}%   | {analysis.optimistic.gdp_growth:.1f}%   | {analysis.pessimistic.gdp_growth:.1f}%   |
| CPI        | {analysis.base.cpi:.1f}%   | {analysis.optimistic.cpi:.1f}%   | {analysis.pessimistic.cpi:.1f}%   |
| 制造业PMI  | {analysis.base.pmi:.1f}   | {analysis.optimistic.pmi:.1f}   | {analysis.pessimistic.pmi:.1f}   |
| 利率       | {analysis.base.interest_rate:.2f}%  | {analysis.optimistic.interest_rate:.2f}%  | {analysis.pessimistic.interest_rate:.2f}%  |
| 股票收益   | {analysis.base.stock_return:.1%}  | {analysis.optimistic.stock_return:.1%}  | {analysis.pessimistic.stock_return:.1%}  |
| 债券收益   | {analysis.base.bond_return:.1%}  | {analysis.optimistic.bond_return:.1%}  | {analysis.pessimistic.bond_return:.1%}  |

三、加权预期收益
--------------
股票: {analysis.weighted_return:.1%}
风险评分: {analysis.risk_score:.1f}/10

四、推荐配置
-----------
"""
        
        alloc = analysis._recommend_allocation()
        report += f"""
股票: {alloc['stocks']:.0%}
债券: {alloc['bonds']:.0%}
现金: {alloc['cash']:.0%}

五、具体建议
-----------
基准情景建议:
"""
        for rec in analysis.base.recommendations:
            report += f"  - {rec}\n"
        
        return report


def create_default_analysis() -> ScenarioAnalysis:
    """创建默认分析（用于测试）"""
    analyzer = ScenarioAnalyzer()
    
    indicators = {
        "gdp_growth": 5.2,
        "cpi": 2.1,
        "ppi": -1.5,
        "pmi": 49.5,
        "interest_rate": 3.45,
        "money_supply": 8.7
    }
    
    return analyzer.analyze(indicators, "recovery")