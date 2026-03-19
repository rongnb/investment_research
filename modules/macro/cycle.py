# -*- coding: utf-8 -*-
"""
经济周期分析模块

实现经济周期自动判断和趋势分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EconomicCycle(Enum):
    """经济周期阶段"""
    RECOVERY = "复苏期"      # 经济从低谷开始回升
    EXPANSION = "扩张期"     # 经济持续增长
    PEAK = "顶峰期"         # 经济达到高点，增长放缓
    CONTRACTION = "收缩期"  # 经济开始下行
    TROUGH = "低谷期"       # 经济降至最低点


class CycleTrend(Enum):
    """周期趋势"""
    IMPROVING = "改善"      # 指标向好
    STABLE = "稳定"         # 指标平稳
    DETERIORATING = "恶化"  # 指标恶化


@dataclass
class CycleSignal:
    """周期信号"""
    indicator: str
    value: float
    trend: CycleTrend
    weight: float
    description: str


@dataclass
class CycleAnalysis:
    """周期分析结果"""
    current_cycle: EconomicCycle
    confidence: float  # 0-1，表示判断置信度
    signals: List[CycleSignal]
    leading_indicators: Dict[str, float]   # 领先指标
    coincident_indicators: Dict[str, float]  # 同步指标
    lagging_indicators: Dict[str, float]   # 滞后指标
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class EconomicCycleAnalyzer:
    """
    经济周期分析器
    
    基于多指标综合评分和趋势分析判断经济周期
    """
    
    # 指标权重配置
    LEADING_WEIGHTS = {
        "pmi": 0.25,              # PMI是最重要的领先指标
        "consumer_confidence": 0.15,
        "money_supply": 0.10,
    }
    
    COINCIDENT_WEIGHTS = {
        "gdp_growth": 0.20,
        "industrial_output": 0.10,
    }
    
    LAGGING_WEIGHTS = {
        "unemployment_rate": 0.10,
        "cpi": 0.05,
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze(
        self,
        indicators: Dict[str, float],
        historical_data: Optional[pd.DataFrame] = None
    ) -> CycleAnalysis:
        """
        分析经济周期
        
        Args:
            indicators: 当前指标值字典
            historical_data: 历史数据（用于趋势分析）
            
        Returns:
            CycleAnalysis结果
        """
        # 计算各指标信号
        signals = self._calculate_signals(indicators)
        
        # 分类指标
        leading = {k: v for k, v in indicators.items() 
                   if k in self.LEADING_WEIGHTS}
        coincident = {k: v for k, v in indicators.items() 
                      if k in self.COINCIDENT_WEIGHTS}
        lagging = {k: v for k, v in indicators.items() 
                   if k in self.LAGGING_WEIGHTS}
        
        # 计算综合得分
        score = self._calculate_cycle_score(signals)
        
        # 判断周期阶段
        current_cycle = self._score_to_cycle(score)
        
        # 计算置信度
        confidence = self._calculate_confidence(signals, score)
        
        # 生成投资建议
        recommendations = self._generate_recommendations(current_cycle, signals)
        
        return CycleAnalysis(
            current_cycle=current_cycle,
            confidence=confidence,
            signals=signals,
            leading_indicators=leading,
            coincident_indicators=coincident,
            lagging_indicators=lagging,
            recommendations=recommendations
        )
    
    def _calculate_signals(self, indicators: Dict[str, float]) -> List[CycleSignal]:
        """计算各指标信号"""
        signals = []
        
        # PMI信号
        if "pmi" in indicators:
            pmi = indicators["pmi"]
            if pmi > 52:
                trend = CycleTrend.IMPROVING
                desc = "制造业强劲扩张"
            elif pmi > 50:
                trend = CycleTrend.STABLE
                desc = "制造业温和扩张"
            elif pmi > 48:
                trend = CycleTrend.DETERIORATING
                desc = "制造业收缩趋势"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "制造业明显收缩"
            
            signals.append(CycleSignal(
                indicator="pmi",
                value=pmi,
                trend=trend,
                weight=self.LEADING_WEIGHTS["pmi"],
                description=desc
            ))
        
        # GDP增长率信号
        if "gdp_growth" in indicators:
            gdp = indicators["gdp_growth"]
            if gdp > 6:
                trend = CycleTrend.IMPROVING
                desc = "经济快速增长"
            elif gdp > 4:
                trend = CycleTrend.STABLE
                desc = "经济平稳增长"
            elif gdp > 2:
                trend = CycleTrend.DETERIORATING
                desc = "经济增速放缓"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "经济面临下行压力"
            
            signals.append(CycleSignal(
                indicator="gdp_growth",
                value=gdp,
                trend=trend,
                weight=self.COINCIDENT_WEIGHTS["gdp_growth"],
                description=desc
            ))
        
        # 失业率信号
        if "unemployment_rate" in indicators:
            ur = indicators["unemployment_rate"]
            if ur < 4:
                trend = CycleTrend.IMPROVING
                desc = "就业市场强劲"
            elif ur < 5.5:
                trend = CycleTrend.STABLE
                desc = "就业市场稳定"
            elif ur < 7:
                trend = CycleTrend.DETERIORATING
                desc = "就业压力上升"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "就业形势严峻"
            
            signals.append(CycleSignal(
                indicator="unemployment_rate",
                value=ur,
                trend=trend,
                weight=self.LAGGING_WEIGHTS["unemployment_rate"],
                description=desc
            ))
        
        # 货币供应量信号
        if "money_supply" in indicators:
            m2 = indicators["money_supply"]
            if m2 > 10:
                trend = CycleTrend.IMPROVING
                desc = "货币环境宽松"
            elif m2 > 8:
                trend = CycleTrend.STABLE
                desc = "货币环境适度"
            elif m2 > 6:
                trend = CycleTrend.DETERIORATING
                desc = "货币环境收紧"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "货币环境紧缩"
            
            signals.append(CycleSignal(
                indicator="money_supply",
                value=m2,
                trend=trend,
                weight=self.LEADING_WEIGHTS["money_supply"],
                description=desc
            ))
        
        # CPI信号
        if "cpi" in indicators:
            cpi = indicators["cpi"]
            if 1 < cpi < 3:
                trend = CycleTrend.STABLE
                desc = "通胀温和适中"
            elif cpi < 1:
                trend = CycleTrend.DETERIORATING
                desc = "存在通缩风险"
            elif cpi < 5:
                trend = CycleTrend.IMPROVING
                desc = "通胀适度上升"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "通胀压力较大"
            
            signals.append(CycleSignal(
                indicator="cpi",
                value=cpi,
                trend=trend,
                weight=self.LAGGING_WEIGHTS["cpi"],
                description=desc
            ))
        
        # 消费者信心指数信号
        if "consumer_confidence" in indicators:
            cc = indicators["consumer_confidence"]
            if cc > 100:
                trend = CycleTrend.IMPROVING
                desc = "消费者信心充足"
            elif cc > 85:
                trend = CycleTrend.STABLE
                desc = "消费者信心平稳"
            else:
                trend = CycleTrend.DETERIORATING
                desc = "消费者信心不足"
            
            signals.append(CycleSignal(
                indicator="consumer_confidence",
                value=cc,
                trend=trend,
                weight=self.LEADING_WEIGHTS["consumer_confidence"],
                description=desc
            ))
        
        return signals
    
    def _calculate_cycle_score(self, signals: List[CycleSignal]) -> float:
        """计算周期综合得分"""
        score = 0.0
        
        for signal in signals:
            # 基础分数
            if signal.trend == CycleTrend.IMPROVING:
                base_score = 1.0
            elif signal.trend == CycleTrend.STABLE:
                base_score = 0.0
            else:
                base_score = -1.0
            
            # 考虑特殊指标的方向
            if signal.indicator == "unemployment_rate":
                # 失业率越低越好
                base_score = -base_score
            
            score += base_score * signal.weight
        
        # 归一化到-2到2的范围
        return max(-2.0, min(2.0, score * 2))
    
    def _score_to_cycle(self, score: float) -> EconomicCycle:
        """将得分转换为周期阶段"""
        if score >= 1.5:
            return EconomicCycle.EXPANSION
        elif score >= 0.5:
            return EconomicCycle.RECOVERY
        elif score >= -0.5:
            return EconomicCycle.PEAK
        elif score >= -1.5:
            return EconomicCycle.CONTRACTION
        else:
            return EconomicCycle.TROUGH
    
    def _calculate_confidence(self, signals: List[CycleSignal], score: float) -> float:
        """计算判断置信度"""
        if not signals:
            return 0.3
        
        # 信号一致性与否
        trends = [s.trend for s in signals]
        improving_count = trends.count(CycleTrend.IMPROVING)
        deteriorating_count = trends.count(CycleTrend.DETERIORATING)
        
        # 信号越一致，置信度越高
        consistency = max(improving_count, deteriorating_count) / len(signals)
        
        # 信号数量
        signal_count_factor = min(len(signals) / 6, 1.0)
        
        # 分数绝对值
        score_factor = abs(score) / 2
        
        confidence = (consistency * 0.4 + signal_count_factor * 0.3 + score_factor * 0.3)
        
        return min(0.95, max(0.3, confidence))
    
    def _generate_recommendations(
        self, 
        cycle: EconomicCycle, 
        signals: List[CycleSignal]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []
        
        if cycle == EconomicCycle.RECOVERY:
            recommendations = [
                "逐步增加股票配置比例",
                "关注周期性行业（金融、地产、有色）",
                "适度配置可转换债券",
                "减少现金和防御性资产"
            ]
        elif cycle == EconomicCycle.EXPANSION:
            recommendations = [
                "维持较高的股票配置",
                "超配成长型和周期型股票",
                "适度配置商品和资源类资产",
                "开始关注债券收益率上行风险"
            ]
        elif cycle == EconomicCycle.PEAK:
            recommendations = [
                "逐步降低股票仓位",
                "增加防御性行业配置（消费、医药）",
                "提高债券和现金比例",
                "关注市场见顶信号"
            ]
        elif cycle == EconomicCycle.CONTRACTION:
            recommendations = [
                "降低股票至低配",
                "增加国债和优质债券",
                "保持充足流动性",
                "关注被错杀的优质股"
            ]
        else:  # TROUGH
            recommendations = [
                "为抄底做准备",
                "逐步建仓优质股票",
                "增加长期国债配置",
                "保持适度现金等待机会"
            ]
        
        # 添加基于信号的具体建议
        for signal in signals:
            if signal.indicator == "pmi" and signal.trend == CycleTrend.DETERIORATING:
                recommendations.append("PMI显示经济动能不足，需谨慎")
            elif signal.indicator == "money_supply" and signal.trend == CycleTrend.IMPROVING:
                recommendations.append("货币环境宽松，利好风险资产")
        
        return recommendations
    
    def analyze_with_historical(
        self,
        current_indicators: Dict[str, float],
        historical_df: pd.DataFrame,
        periods: int = 12
    ) -> CycleAnalysis:
        """
        结合历史数据分析周期
        
        Args:
            current_indicators: 当前指标值
            historical_df: 历史数据DataFrame，需要包含各指标列
            periods: 分析的历史期数
            
        Returns:
            CycleAnalysis结果
        """
        # 计算趋势变化
        trend_indicators = {}
        
        for col in ["pmi", "gdp_growth", "money_supply", "cpi", "unemployment_rate"]:
            if col in historical_df.columns:
                recent = historical_df[col].tail(periods // 2).mean()
                older = historical_df[col].tail(periods).head(periods // 2).mean()
                
                if recent > older * 1.02:
                    trend_indicators[col] = current_indicators.get(col, 0) * 1.1
                elif recent < older * 0.98:
                    trend_indicators[col] = current_indicators.get(col, 0) * 0.9
                else:
                    trend_indicators[col] = current_indicators.get(col, 0)
        
        # 合并当前值和趋势调整值
        combined = {**current_indicators}
        for k, v in trend_indicators.items():
            if k in combined:
                combined[k] = (combined[k] * 0.7 + v * 0.3)
        
        return self.analyze(combined, historical_df)


def create_default_indicators() -> Dict[str, float]:
    """创建默认指标值（用于测试）"""
    return {
        "pmi": 49.5,
        "gdp_growth": 5.2,
        "cpi": 2.1,
        "ppi": -1.5,
        "unemployment_rate": 5.2,
        "money_supply": 8.7,
        "consumer_confidence": 88.9
    }