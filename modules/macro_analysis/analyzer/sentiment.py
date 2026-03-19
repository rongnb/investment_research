# -*- coding: utf-8 -*-
"""
情感分析器

用于分析文本的情感倾向，包括总体情感、政策情感、市场情感和行业情感
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import jieba
import jieba.analyse


class SentimentType(Enum):
    """情感类型"""
    VERY_POSITIVE = 2
    POSITIVE = 1
    NEUTRAL = 0
    NEGATIVE = -1
    VERY_NEGATIVE = -2


@dataclass
class SentimentResult:
    """情感分析结果"""
    overall: SentimentType
    overall_score: float
    market_sentiment: float
    policy_sentiment: float
    sector_sentiment: float
    positive_keywords: List[str]
    negative_keywords: List[str]
    neutral_keywords: List[str]
    confidence: float
    method: str = "keyword_based"


class SentimentAnalyzer:
    """
    情感分析器
    
    使用关键词匹配和语义分析技术分析文本的情感倾向
    """
    
    # 情感词库
    POSITIVE_WORDS = {
        # 积极词汇
        "积极": 2,
        "向好": 2,
        "增长": 2,
        "提升": 2,
        "改善": 2,
        "稳定": 1,
        "好转": 1,
        "加速": 1,
        "推进": 1,
        "支持": 2,
        "鼓励": 2,
        "发展": 2,
        "创新": 2,
        "优化": 1,
        "完善": 1,
        "加强": 1,
        "增加": 2,
        "扩大": 1,
        "提高": 2,
        "深化": 1,
        "巩固": 1,
        "提升": 2,
        "促进": 2,
        "保障": 1,
        "建立": 1,
        "健全": 1,
        "有序": 1,
        "规范": 1,
        "高效": 1,
        "可持续": 1,
        "绿色": 1,
        "健康": 1,
        "良好": 1,
        "优秀": 2,
        "杰出": 2,
        "显著": 1,
        "明显": 1,
        "快速": 1,
        "持续": 1,
        "稳健": 1,
        "强劲": 1,
        "活跃": 1,
        "旺盛": 1,
        "乐观": 2,
        "信心": 2,
        "机遇": 2,
        "优势": 1,
        "潜力": 1,
        "利好": 2,
        "上涨": 2,
        "盈利": 2,
        "改善": 1,
        "突破": 2,
        "创新高": 2,
        "新记录": 2,
    }
    
    NEGATIVE_WORDS = {
        # 消极词汇
        "下跌": -2,
        "下降": -2,
        "下滑": -2,
        "亏损": -2,
        "下降": -2,
        "减少": -1,
        "收缩": -1,
        "放缓": -1,
        "停滞": -1,
        "衰退": -2,
        "恶化": -2,
        "危机": -2,
        "风险": -1,
        "威胁": -1,
        "挑战": -1,
        "压力": -1,
        "困难": -1,
        "问题": -1,
        "矛盾": -1,
        "冲突": -1,
        "紧张": -1,
        "放缓": -1,
        "疲软": -1,
        "低迷": -1,
        "萧条": -2,
        "不景气": -1,
        "恶化": -2,
        "严峻": -1,
        "脆弱": -1,
        "不稳定": -1,
        "波动": -1,
        "下降": -2,
        "减少": -1,
        "缩减": -1,
        "压缩": -1,
        "限制": -1,
        "禁止": -2,
        "监管": -1,
        "处罚": -2,
        "违规": -2,
        "警告": -1,
        "风险": -1,
        "隐患": -1,
        "问题": -1,
        "漏洞": -1,
        "缺陷": -1,
        "不足": -1,
        "困难": -1,
        "挑战": -1,
        "压力": -1,
        "下滑": -2,
        "下跌": -2,
        "回调": -1,
        "调整": -1,
        "波动": -1,
        "震荡": -1,
    }
    
    # 行业特定情感词汇
    SECTOR_SENTIMENTS = {
        "金融": {
            "降息": 2,
            "降准": 2,
            "流动性": 1,
            "信贷": 1,
            "融资": 1,
            "风险": -1,
            "不良": -2,
        },
        "地产": {
            "调控": -1,
            "限购": -1,
            "限售": -1,
            "松绑": 1,
            "支持": 1,
            "稳定": 1,
        },
        "科技": {
            "创新": 2,
            "研发": 1,
            "突破": 2,
            "替代": 1,
            "卡脖子": -1,
            "制裁": -2,
        },
        "能源": {
            "碳中和": 1,
            "碳达峰": 1,
            "环保": 1,
            "淘汰": -1,
            "限制": -1,
        },
        "消费": {
            "升级": 2,
            "增长": 1,
            "需求": 1,
            "疲软": -1,
            "下滑": -1,
        },
        "医药": {
            "创新药": 2,
            "医保": 1,
            "研发": 1,
            "降价": -1,
        },
    }
    
    def __init__(self, config: Dict = None):
        """初始化分析器"""
        self.config = config or {}
        self.threshold = self.config.get("score_threshold", 0.3)
        
        # 加载自定义词典
        for word in self.POSITIVE_WORDS.keys():
            jieba.add_word(word)
        for word in self.NEGATIVE_WORDS.keys():
            jieba.add_word(word)
    
    def _calculate_sentiment_score(self, text: str) -> Tuple[float, List[str], List[str], List[str]]:
        """计算情感分数"""
        positive_count = 0
        negative_count = 0
        total_weight = 0
        
        positive_kws = []
        negative_kws = []
        neutral_kws = []
        
        # 正向词汇匹配
        for word, weight in self.POSITIVE_WORDS.items():
            matches = text.count(word)
            if matches > 0:
                positive_count += matches * weight
                total_weight += matches * weight
                positive_kws.append(word)
        
        # 负向词汇匹配
        for word, weight in self.NEGATIVE_WORDS.items():
            matches = text.count(word)
            if matches > 0:
                negative_count += matches * abs(weight)
                total_weight += matches * abs(weight)
                negative_kws.append(word)
        
        # 计算总体分数
        if total_weight > 0:
            score = (positive_count - negative_count) / total_weight
        else:
            score = 0
        
        return score, positive_kws, negative_kws, neutral_kws
    
    def _analyze_market_sentiment(self, text: str) -> float:
        """分析市场情感"""
        keywords = ["上涨", "下跌", "震荡", "回调", "调整", "波动", "行情", "市场"]
        score = 0
        
        for keyword in keywords:
            score += text.count(keyword) * 0.1
        
        return score
    
    def _analyze_policy_sentiment(self, text: str) -> float:
        """分析政策情感"""
        keywords = ["政策", "监管", "政策支持", "政策限制", "政策调控"]
        score = 0
        
        for keyword in keywords:
            score += text.count(keyword) * 0.2
        
        return score
    
    def _analyze_sector_sentiment(self, text: str) -> float:
        """分析行业情感"""
        score = 0
        
        for sector, words in self.SECTOR_SENTIMENTS.items():
            for word, weight in words.items():
                if word in text:
                    score += weight
        
        return score
    
    def _score_to_sentiment_type(self, score: float) -> SentimentType:
        """将分数转换为情感类型"""
        if score >= 0.7:
            return SentimentType.VERY_POSITIVE
        elif score >= 0.3:
            return SentimentType.POSITIVE
        elif score > -0.3:
            return SentimentType.NEUTRAL
        elif score > -0.7:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.VERY_NEGATIVE
    
    def analyze(self, text: str) -> SentimentResult:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            情感分析结果
        """
        # 计算基本情感分数
        score, positive_kws, negative_kws, neutral_kws = self._calculate_sentiment_score(text)
        
        # 分析各维度情感
        market_sentiment = self._analyze_market_sentiment(text)
        policy_sentiment = self._analyze_policy_sentiment(text)
        sector_sentiment = self._analyze_sector_sentiment(text)
        
        # 归一化分数到-1到1范围
        market_score = max(-1, min(1, market_sentiment * 0.1))
        policy_score = max(-1, min(1, policy_sentiment * 0.1))
        sector_score = max(-1, min(1, sector_sentiment * 0.1))
        
        # 综合得分
        overall_score = score
        overall_sentiment = self._score_to_sentiment_type(score)
        
        # 计算置信度
        total_keywords = len(positive_kws) + len(negative_kws)
        confidence = min(0.3 + total_keywords * 0.1, 0.95)
        
        return SentimentResult(
            overall=overall_sentiment,
            overall_score=overall_score,
            market_sentiment=market_score,
            policy_sentiment=policy_score,
            sector_sentiment=sector_score,
            positive_keywords=positive_kws,
            negative_keywords=negative_kws,
            neutral_keywords=neutral_kws,
            confidence=confidence
        )
    
    def get_sentiment_labels(self) -> Dict:
        """获取情感标签映射"""
        return {
            SentimentType.VERY_POSITIVE: "非常积极",
            SentimentType.POSITIVE: "积极",
            SentimentType.NEUTRAL: "中性",
            SentimentType.NEGATIVE: "消极",
            SentimentType.VERY_NEGATIVE: "非常消极",
        }
    
    def sentiment_to_text(self, sentiment: SentimentType) -> str:
        """情感类型转文本"""
        labels = self.get_sentiment_labels()
        return labels.get(sentiment, "中性")
    
    def analyze_with_keywords(self, text: str, additional_positive: List[str] = None, 
                              additional_negative: List[str] = None) -> SentimentResult:
        """
        分析文本情感（支持自定义关键词）
        
        Args:
            text: 要分析的文本
            additional_positive: 额外的积极关键词
            additional_negative: 额外的消极关键词
            
        Returns:
            情感分析结果
        """
        # 临时扩展词库
        if additional_positive:
            for word in additional_positive:
                self.POSITIVE_WORDS[word] = 1
        
        if additional_negative:
            for word in additional_negative:
                self.NEGATIVE_WORDS[word] = -1
        
        result = self.analyze(text)
        
        # 恢复原始词库（可选）
        if additional_positive:
            for word in additional_positive:
                if word in self.POSITIVE_WORDS:
                    del self.POSITIVE_WORDS[word]
        
        if additional_negative:
            for word in additional_negative:
                if word in self.NEGATIVE_WORDS:
                    del self.NEGATIVE_WORDS[word]
        
        return result
