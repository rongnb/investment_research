# -*- coding: utf-8 -*-
"""
政策分析器

用于分析政策文件、政府公告、监管文件等内容，识别政策重点、影响行业和市场影响
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import jieba
import jieba.analyse


@dataclass
class PolicyKeyPoint:
    """政策要点"""
    key: str
    content: str
    importance: int = 0  # 重要性评分: 0-10
    keywords: List[str] = None


@dataclass
class PolicyImpact:
    """政策影响"""
    sector: str
    impact_score: float  # 影响程度: -10到10
    duration: str  # 影响周期: short/medium/long
    confidence: float = 0.8


@dataclass
class PolicyAnalysisResult:
    """政策分析结果"""
    title: str
    content: str
    policy_type: str
    policy_level: str
    urgency_level: int
    key_points: List[PolicyKeyPoint]
    affected_sectors: List[PolicyImpact]
    implementation_timeline: List[Tuple[str, str]]
    related_policies: List[str]
    confidence: float = 0.8
    analysis_method: str = "default"


class PolicyAnalyzer:
    """
    政策分析器
    
    使用自然语言处理和关键词匹配技术分析政策文件的语义、重点和影响
    """
    
    # 政策类型识别关键词
    POLICY_TYPES = {
        "货币政策": ["货币政策", "利率", "存款准备金率", "MLF", "LPR", "逆回购"],
        "财政政策": ["财政政策", "赤字", "预算", "国债", "税收", "减税降费"],
        "产业政策": ["产业政策", "战略性新兴产业", "鼓励发展", "限制发展", "指导目录"],
        "监管政策": ["监管", "处罚", "合规", "监管要求", "违规处理"],
        "科技政策": ["科技创新", "研发投入", "高新技术", "知识产权"],
        "区域政策": ["区域", "地方发展", "雄安", "海南", "大湾区", "一带一路"],
        "环保政策": ["环保", "绿色", "碳中和", "碳达峰", "排放标准"],
        "金融政策": ["金融", "融资", "贷款", "融资成本", "金融稳定"],
    }
    
    # 政策级别识别关键词
    POLICY_LEVELS = {
        "中央": ["国务院", "党中央", "中共中央", "中央人民政府"],
        "部委": ["证监会", "银保监会", "央行", "财政部", "发改委"],
        "地方": ["省", "市", "自治区", "地方政府", "人民政府"]
    }
    
    # 行业影响映射
    SECTOR_IMPACT_KEYWORDS = {
        "金融": ["银行", "保险", "证券", "金融", "信贷"],
        "地产": ["房地产", "住房", "房贷", "房产税", "房地产调控"],
        "科技": ["科技", "创新", "人工智能", "5G", "芯片", "半导体"],
        "能源": ["能源", "电力", "煤炭", "石油", "新能源"],
        "消费": ["消费", "零售", "电商", "汽车", "家电"],
        "医药": ["医药", "医疗", "药品", "医保", "疫苗"],
        "环保": ["环保", "绿色", "碳排放", "污染"],
        "基建": ["基础设施", "高铁", "公路", "铁路", "机场", "水利"],
    }
    
    # 紧急程度关键词
    URGENCY_KEYWORDS = [
        "立即执行", "紧急通知", "严格执行", "迅速", "限时", "必须",
        "务必", "尽快", "紧急", "立即", "快速"
    ]
    
    def __init__(self, config: Dict = None):
        """初始化政策分析器"""
        self.config = config or {}
        
        # 配置参数
        self.keyword_extraction_mode = self.config.get("keyword_extraction", "tfidf")
        self.importance_threshold = self.config.get("importance_threshold", 0.3)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.6)
        
        # 加载自定义词典
        self._load_dictionaries()
        
        jieba.analyse.set_stop_words(self._get_stop_words())
    
    def _load_dictionaries(self):
        """加载自定义词典"""
        # 加载行业术语词典
        industry_terms = []
        for sector, keywords in self.SECTOR_IMPACT_KEYWORDS.items():
            industry_terms.extend(keywords)
        
        for term in industry_terms:
            jieba.add_word(term)
    
    def _get_stop_words(self) -> str:
        """获取停用词列表"""
        return """
的 了 在 是 有 和 就 等 对 与 也 及 这 那 而 之 以 于 为 由 就 但 并
我们 你们 他们 它们 这里 那里 因为 所以 但是 虽然 尽管 然而 不过 如果
那么 或者 并且 而且 因此 于是 但是 然而 可是 不过 反而 否则 不过 其实
然而 因此 于是 同时 另外 此外 而且 不仅 不仅 而且 虽然 尽管 但是 可是
然而 不过 或者 否则 如果 只有 只要 因为 由于 因此 所以 从而 进而 同时
还有 另外 此外 以及 并 并且 而 而且 但是 可是 然而 不过 虽然 尽管 即使
如果 要是 只要 只有 除非 假设 假如 要是 倘若 假使 假如 如果 万一 即使
尽管 不管 尽管 不管 无论 不管 尽管 即使 哪怕 不管 无论 尽管 不管 无论
不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管
不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管 不管
        """.split()
    
    def _extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """提取关键词"""
        if self.keyword_extraction_mode == "tfidf":
            return jieba.analyse.extract_tags(text, topK=top_k)
        else:
            return jieba.analyse.textrank(text, topK=top_k)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(jieba.lcut(text1))
        words2 = set(jieba.lcut(text2))
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0
    
    def _extract_sentences(self, text: str) -> List[str]:
        """提取句子"""
        # 简单的句子分割
        sentences = re.split(r'[。！？！]', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
    
    def identify_policy_type(self, text: str) -> str:
        """识别政策类型"""
        for policy_type, keywords in self.POLICY_TYPES.items():
            if any(keyword in text for keyword in keywords):
                return policy_type
        return "其他政策"
    
    def identify_policy_level(self, text: str) -> str:
        """识别政策级别"""
        for level, keywords in self.POLICY_LEVELS.items():
            if any(keyword in text for keyword in keywords):
                return level
        return "地方"
    
    def calculate_urgency_level(self, text: str) -> int:
        """计算紧急程度"""
        urgency = 0
        for keyword in self.URGENCY_KEYWORDS:
            if keyword in text:
                urgency += 1
        return min(urgency * 2, 10)
    
    def extract_key_points(self, text: str, num_points: int = 10) -> List[PolicyKeyPoint]:
        """提取政策要点"""
        sentences = self._extract_sentences(text)
        key_points = []
        
        # 识别关键句子
        for sentence in sentences:
            importance_score = 0
            
            # 关键词匹配
            for policy_type, keywords in self.POLICY_TYPES.items():
                matches = sum(1 for kw in keywords if kw in sentence)
                importance_score += matches * 2
            
            for level, keywords in self.POLICY_LEVELS.items():
                matches = sum(1 for kw in keywords if kw in sentence)
                importance_score += matches * 1
            
            if importance_score > 0:
                keywords = self._extract_keywords(sentence, top_k=3)
                key_points.append(PolicyKeyPoint(
                    key=f"{len(key_points) + 1}",
                    content=sentence,
                    importance=min(int(importance_score * 2), 10),
                    keywords=keywords
                ))
        
        # 按重要性排序并取前N个
        key_points.sort(key=lambda x: x.importance, reverse=True)
        return key_points[:num_points]
    
    def analyze_affected_sectors(self, text: str) -> List[PolicyImpact]:
        """分析受影响行业"""
        impacts = []
        
        for sector, keywords in self.SECTOR_IMPACT_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in text)
            if match_count > 0:
                # 计算影响分数
                impact_score = match_count * 2  # 基础分数
                
                # 判断影响方向
                positive_words = ["鼓励", "支持", "发展", "优惠", "补贴", "扶持"]
                negative_words = ["限制", "禁止", "处罚", "监管", "淘汰"]
                
                for word in positive_words:
                    if word in text:
                        impact_score += 2
                
                for word in negative_words:
                    if word in text:
                        impact_score -= 2
                
                # 影响周期
                duration = "medium"
                if "立即" in text or "短期" in text:
                    duration = "short"
                elif "长期" in text or "持续" in text:
                    duration = "long"
                
                impacts.append(PolicyImpact(
                    sector=sector,
                    impact_score=impact_score,
                    duration=duration,
                    confidence=0.8
                ))
        
        # 排序
        impacts.sort(key=lambda x: x.impact_score, reverse=True)
        return impacts
    
    def extract_implementation_timeline(self, text: str) -> List[Tuple[str, str]]:
        """提取实施时间表"""
        timeline = []
        
        # 时间模式匹配
        date_patterns = [
            r'(\d{4}年\d{1,2}月)',
            r'(\d{1,2}月\d{1,2}日)',
            r'(\d{4}年)',
            r'(\d{1,2}个月内)',
            r'(\d{1,2}年内)',
            r'(近期|短期|中期|长期)',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match:
                    timeline.append((match, "待确定"))
        
        return timeline
    
    def analyze(self, title: str, content: str) -> PolicyAnalysisResult:
        """
        完整分析政策文件
        
        Args:
            title: 标题
            content: 内容
            
        Returns:
            分析结果
        """
        policy_type = self.identify_policy_type(content)
        policy_level = self.identify_policy_level(content)
        urgency = self.calculate_urgency_level(content)
        
        key_points = self.extract_key_points(content)
        affected_sectors = self.analyze_affected_sectors(content)
        timeline = self.extract_implementation_timeline(content)
        
        # 查找相关政策
        related_policies = self._find_related_policies(title, content)
        
        return PolicyAnalysisResult(
            title=title,
            content=content,
            policy_type=policy_type,
            policy_level=policy_level,
            urgency_level=urgency,
            key_points=key_points,
            affected_sectors=affected_sectors,
            implementation_timeline=timeline,
            related_policies=related_policies
        )
    
    def _find_related_policies(self, title: str, content: str) -> List[str]:
        """查找相关政策"""
        related = []
        
        if "十四五" in title or "十四五" in content:
            related.append("十四五规划")
        
        if "一带一路" in title or "一带一路" in content:
            related.append("一带一路政策")
        
        return related
    
    def generate_summary(self, result: PolicyAnalysisResult) -> str:
        """生成分析摘要"""
        summary = []
        summary.append(f"政策标题: {result.title}")
        summary.append(f"政策类型: {result.policy_type}")
        summary.append(f"政策级别: {result.policy_level}")
        summary.append(f"紧急程度: {result.urgency_level}/10")
        
        summary.append("\n政策要点:")
        for i, point in enumerate(result.key_points, 1):
            summary.append(f"  {i}. {point.content}")
        
        summary.append("\n受影响行业:")
        for impact in result.affected_sectors:
            direction = "正向" if impact.impact_score > 0 else "负向"
            summary.append(f"  {impact.sector}: {direction}影响")
        
        return "\n".join(summary)
