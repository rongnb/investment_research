# -*- coding: utf-8 -*-
"""
政策影响评估模块

评估货币政策、财政政策和产业政策对市场的影响
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """政策类型"""
    MONETARY = "monetary"      # 货币政策
    FISCAL = "fiscal"          # 财政政策
    INDUSTRIAL = "industrial"   # 产业政策
    REGULATORY = "regulatory"   # 监管政策


class PolicyDirection(Enum):
    """政策方向"""
    EASING = "easing"          # 宽松
    NEUTRAL = "neutral"        # 中性
    TIGHTENING = "tightening"  # 紧缩


@dataclass
class PolicyImpact:
    """政策影响"""
    policy_type: PolicyType
    policy_name: str
    direction: PolicyDirection
    impact_score: float  # -1到1, 负数利空, 正数利好
    affected_sectors: List[str]
    affected_assets: List[str]  # stocks/bonds/commodities
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PolicyAssessment:
    """政策评估结果"""
    overall_sentiment: float  # -1到1, 市场整体情绪
    monetary_policy: PolicyImpact
    fiscal_policy: PolicyImpact
    industrial_policies: List[PolicyImpact]
    sector_impacts: Dict[str, float]  # 行业影响评分
    asset_recommendations: Dict[str, str]  # 资产建议
    key_policy_signals: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class PolicyAnalyzer:
    """
    政策影响分析器
    
    评估各类政策对市场的影响
    """
    
    # 行业政策敏感度映射
    SECTOR_SENSITIVITY = {
        "银行": {"monetary": 0.9, "fiscal": 0.5},
        "房地产": {"monetary": 0.8, "fiscal": 0.7},
        "券商": {"monetary": 0.7, "fiscal": 0.4},
        "保险": {"monetary": 0.6, "fiscal": 0.3},
        "消费": {"monetary": 0.3, "fiscal": 0.6},
        "医药": {"monetary": 0.2, "fiscal": 0.4},
        "科技": {"monetary": 0.3, "fiscal": 0.5},
        "新能源": {"monetary": 0.2, "fiscal": 0.8},
        "基建": {"monetary": 0.3, "fiscal": 0.9},
        "钢铁": {"monetary": 0.4, "fiscal": 0.7},
        "有色": {"monetary": 0.4, "fiscal": 0.5},
        "化工": {"monetary": 0.3, "fiscal": 0.4},
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def assess(
        self,
        current_indicators: Dict[str, float],
        recent_policies: Optional[List[Dict]] = None
    ) -> PolicyAssessment:
        """
        评估政策影响
        
        Args:
            current_indicators: 当前经济指标
            recent_policies: 最近的政策列表
            
        Returns:
            PolicyAssessment结果
        """
        # 分析货币政策
        monetary = self._analyze_monetary_policy(current_indicators)
        
        # 分析财政政策
        fiscal = self._analyze_fiscal_policy(current_indicators)
        
        # 分析产业政策
        industrial = self._analyze_industrial_policies(recent_policies or [])
        
        # 计算整体市场情绪
        sentiment = self._calculate_sentiment(monetary, fiscal, industrial)
        
        # 计算行业影响
        sector_impacts = self._calculate_sector_impacts(monetary, fiscal, industrial)
        
        # 生成资产建议
        asset_recs = self._generate_asset_recommendations(
            monetary, fiscal, sector_impacts
        )
        
        # 识别风险和机会
        risks = self._identify_risks(monetary, fiscal, sector_impacts)
        opportunities = self._identify_opportunities(monetary, fiscal, sector_impacts)
        
        return PolicyAssessment(
            overall_sentiment=sentiment,
            monetary_policy=monetary,
            fiscal_policy=fiscal,
            industrial_policies=industrial,
            sector_impacts=sector_impacts,
            asset_recommendations=asset_recs,
            key_policy_signals=self._extract_key_signals(monetary, fiscal),
            risks=risks,
            opportunities=opportunities
        )
    
    def _analyze_monetary_policy(
        self,
        indicators: Dict[str, float]
    ) -> PolicyImpact:
        """分析货币政策"""
        score = 0.0
        direction = PolicyDirection.NEUTRAL
        affected = ["stocks", "bonds"]
        sectors = []
        
        # 基于利率分析
        rate = indicators.get("interest_rate", 3.45)
        if rate < 3.0:
            score += 0.5
            direction = PolicyDirection.EASING
        elif rate < 3.5:
            score += 0.2
            direction = PolicyDirection.NEUTRAL
        else:
            score -= 0.1
        
        # 基于货币供应量分析
        m2 = indicators.get("money_supply", 8)
        if m2 > 10:
            score += 0.3
            direction = PolicyDirection.EASING
        elif m2 > 8:
            score += 0.1
        else:
            score -= 0.2
            direction = PolicyDirection.TIGHTENING
        
        # 确定影响的行业
        if score > 0.3:
            sectors = ["银行", "房地产", "券商", "周期行业"]
        elif score < -0.2:
            sectors = ["银行", "保险"]
        else:
            sectors = ["金融"]
        
        return PolicyImpact(
            policy_type=PolicyType.MONETARY,
            policy_name="货币政策",
            direction=direction,
            impact_score=max(-1, min(1, score)),
            affected_sectors=sectors,
            affected_assets=affected,
            description=self._get_monetary_description(direction, score)
        )
    
    def _analyze_fiscal_policy(
        self,
        indicators: Dict[str, float]
    ) -> PolicyImpact:
        """分析财政政策"""
        score = 0.0
        direction = PolicyDirection.NEUTRAL
        affected = ["stocks", "bonds"]
        
        # 基于GDP增长判断财政立场
        gdp = indicators.get("gdp_growth", 5)
        if gdp < 4:
            score += 0.4
            direction = PolicyDirection.EASING
        elif gdp < 5:
            score += 0.2
        elif gdp > 6.5:
            score -= 0.1
            direction = PolicyDirection.TIGHTENING
        
        # 确定影响的行业
        sectors = []
        if score > 0.2:
            sectors = ["基建", "房地产", "钢铁", "有色", "水泥"]
        elif score > 0:
            sectors = ["基建", "消费"]
        
        return PolicyImpact(
            policy_type=PolicyType.FISCAL,
            policy_name="财政政策",
            direction=direction,
            impact_score=max(-1, min(1, score)),
            affected_sectors=sectors,
            affected_assets=affected,
            description=self._get_fiscal_description(direction, score)
        )
    
    def _analyze_industrial_policies(
        self,
        policies: List[Dict]
    ) -> List[PolicyImpact]:
        """分析产业政策"""
        impacts = []
        
        # 新能源政策
        impacts.append(PolicyImpact(
            policy_type=PolicyType.INDUSTRIAL,
            policy_name="新能源政策",
            direction=PolicyDirection.EASING,
            impact_score=0.6,
            affected_sectors=["新能源", "电动车", "电力设备"],
            affected_assets=["stocks"],
            description="政策持续支持新能源发展，利好相关行业"
        ))
        
        # 科技创新政策
        impacts.append(PolicyImpact(
            policy_type=PolicyType.INDUSTRIAL,
            policy_name="科技创新政策",
            direction=PolicyDirection.EASING,
            impact_score=0.4,
            affected_sectors=["科技", "半导体", "人工智能"],
            affected_assets=["stocks"],
            description="科技创新受到政策重点支持"
        ))
        
        return impacts
    
    def _calculate_sentiment(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact,
        industrial: List[PolicyImpact]
    ) -> float:
        """计算市场情绪"""
        sentiment = (
            monetary.impact_score * 0.4 +
            fiscal.impact_score * 0.3 +
            sum(p.impact_score for p in industrial) * 0.3 / max(len(industrial), 1)
        )
        return max(-1, min(1, sentiment))
    
    def _calculate_sector_impacts(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact,
        industrial: List[PolicyImpact]
    ) -> Dict[str, float]:
        """计算各行业影响"""
        impacts = {}
        
        for sector, sensitivity in self.SECTOR_SENSITIVITY.items():
            m_impact = monetary.impact_score * sensitivity.get("monetary", 0.3)
            f_impact = fiscal.impact_score * sensitivity.get("fiscal", 0.3)
            i_impact = 0.0
            for pol in industrial:
                if sector in pol.affected_sectors:
                    i_impact += pol.impact_score * 0.3
            
            total = m_impact + f_impact + i_impact
            impacts[sector] = max(-1, min(1, total))
        
        return impacts
    
    def _generate_asset_recommendations(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact,
        sector_impacts: Dict[str, float]
    ) -> Dict[str, str]:
        """生成资产配置建议"""
        recs = {}
        overall = (monetary.impact_score + fiscal.impact_score) / 2
        
        if overall > 0.3:
            recs["stocks"] = "超配"
            recs["bonds"] = "低配"
            recs["commodities"] = "标配"
        elif overall > 0:
            recs["stocks"] = "标配"
            recs["bonds"] = "标配"
            recs["commodities"] = "低配"
        else:
            recs["stocks"] = "低配"
            recs["bonds"] = "超配"
            recs["commodities"] = "低配"
        
        return recs
    
    def _identify_risks(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact,
        sector_impacts: Dict[str, float]
    ) -> List[str]:
        """识别风险"""
        risks = []
        
        if monetary.direction == PolicyDirection.TIGHTENING:
            risks.append("货币政策收紧可能抑制市场估值")
        
        if fiscal.direction == PolicyDirection.TIGHTENING:
            risks.append("财政紧缩可能影响基建投资")
        
        return risks
    
    def _identify_opportunities(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact,
        sector_impacts: Dict[str, float]
    ) -> List[str]:
        """识别机会"""
        opportunities = []
        
        if monetary.direction == PolicyDirection.EASING:
            opportunities.append("宽松货币政策利好金融和周期行业")
        
        if fiscal.direction == PolicyDirection.EASING:
            opportunities.append("积极财政政策利好基建和顺周期行业")
        
        return opportunities
    
    def _extract_key_signals(
        self,
        monetary: PolicyImpact,
        fiscal: PolicyImpact
    ) -> List[str]:
        """提取关键政策信号"""
        signals = []
        
        if monetary.direction == PolicyDirection.EASING:
            signals.append("货币政策偏宽松")
        elif monetary.direction == PolicyDirection.TIGHTENING:
            signals.append("货币政策偏紧缩")
        else:
            signals.append("货币政策保持中性")
        
        if fiscal.direction == PolicyDirection.EASING:
            signals.append("财政政策积极")
        elif fiscal.direction == PolicyDirection.TIGHTENING:
            signals.append("财政政策收紧")
        else:
            signals.append("财政政策保持中性")
        
        return signals
    
    def _get_monetary_description(
        self,
        direction: PolicyDirection,
        score: float
    ) -> str:
        """获取货币政策描述"""
        if direction == PolicyDirection.EASING:
            return "货币政策偏宽松，流动性环境较好，利好风险资产"
        elif direction == PolicyDirection.TIGHTENING:
            return "货币政策偏紧缩，流动性趋紧，关注估值压力"
        else:
            return "货币政策保持中性，预期平稳"
    
    def _get_fiscal_description(
        self,
        direction: PolicyDirection,
        score: float
    ) -> str:
        """获取财政政策描述"""
        if direction == PolicyDirection.EASING:
            return "财政政策积极，基建投资发力，利好顺周期行业"
        elif direction == PolicyDirection.TIGHTENING:
            return "财政政策收紧，支出放缓，关注相关行业风险"
        else:
            return "财政政策保持中性"
    
    def generate_report(self, assessment: PolicyAssessment) -> str:
        """生成政策评估报告"""
        return f"""
{'='*60}
政策影响评估报告
{'='*60}

生成时间: {assessment.timestamp.strftime('%Y-%m-%d %H:%M')}

一、整体市场情绪
--------------
{'积极' if assessment.overall_sentiment > 0.5 else '偏积极' if assessment.overall_sentiment > 0.2 else '中性' if assessment.overall_sentiment > -0.2 else '偏谨慎' if assessment.overall_sentiment > -0.5 else '谨慎'} (评分: {assessment.overall_sentiment:.2f})

二、货币政策评估
--------------
方向: {assessment.monetary_policy.direction.value}
影响评分: {assessment.monetary_policy.impact_score:.2f}
{assessment.monetary_policy.description}

三、财政政策评估
--------------
方向: {assessment.fiscal_policy.direction.value}
影响评分: {assessment.fiscal_policy.impact_score:.2f}
{assessment.fiscal_policy.description}

四、行业影响分析
--------------
"""