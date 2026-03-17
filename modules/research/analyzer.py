# -*- coding: utf-8 -*-
"""
研报分析模块
用于自动化分析研报内容
"""

import re
import os
import pdfplumber
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ResearchReport:
    """研报分析结果"""
    title: str
    date: str
    author: str
    institution: str
    key_points: List[str]
    target_price: Optional[float]
    risk_assessment: str
    investment_rating: str

class ResearchAnalyzer:
    """
    研报分析器
    用于提取和分析研报的关键信息
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化研报分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {
            'keywords': [
                '目标价', '风险', '投资评级', '买入', '卖出', '增持', '减持',
                '业绩预测', '毛利率', '净利润', '估值', '行业分析'
            ],
            'target_price_patterns': [
                r'目标价\s*[:：]\s*(\d+\.?\d*)',
                r'目标价.*(\d+\.?\d*)元',
                r'目标价.*(\d+\.?\d*)'
            ],
            'risk_patterns': [
                r'风险.*(高|中|低)',
                r'风险评估.*(高|中|低)',
                r'(高|中|低)风险'
            ],
            'rating_patterns': [
                r'投资评级.*(买入|卖出|增持|减持|中性|推荐)',
                r'(买入|卖出|增持|减持|中性|推荐).*评级'
            ]
        }
        
    def read_pdf_report(self, file_path: str) -> str:
        """
        读取PDF文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本内容
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            raise FileNotFoundError(f"无法读取PDF文件: {e}")
    
    def extract_key_points(self, text: str) -> List[str]:
        """
        提取关键信息
        
        Args:
            text: 文本内容
            
        Returns:
            关键信息列表
        """
        key_points = []
        
        for keyword in self.config['keywords']:
            matches = re.finditer(re.escape(keyword), text)
            for match in matches:
                start_idx = max(0, match.start() - 100)
                end_idx = min(len(text), match.end() + 200)
                context = text[start_idx:end_idx]
                # 清理上下文
                context = re.sub(r'\s+', ' ', context)
                context = context.strip()
                key_points.append(context)
        
        return list(set(key_points))
    
    def extract_target_price(self, text: str) -> Optional[float]:
        """
        提取目标价
        
        Args:
            text: 文本内容
            
        Returns:
            目标价
        """
        for pattern in self.config['target_price_patterns']:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        return None
    
    def extract_risk_assessment(self, text: str) -> str:
        """
        提取风险评估
        
        Args:
            text: 文本内容
            
        Returns:
            风险等级
        """
        for pattern in self.config['risk_patterns']:
            match = re.search(pattern, text)
            if match:
                return match.group(1) + '风险'
        
        return '中等风险'
    
    def extract_investment_rating(self, text: str) -> str:
        """
        提取投资评级
        
        Args:
            text: 文本内容
            
        Returns:
            投资评级
        """
        for pattern in self.config['rating_patterns']:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return '中性'
    
    def analyze_report(self, file_path: str) -> ResearchReport:
        """
        分析完整研报
        
        Args:
            file_path: 文件路径
            
        Returns:
            研报分析结果
        """
        text = self.read_pdf_report(file_path)
        
        report = ResearchReport(
            title=self._extract_title(text),
            date=self._extract_date(text),
            author=self._extract_author(text),
            institution=self._extract_institution(text),
            key_points=self.extract_key_points(text),
            target_price=self.extract_target_price(text),
            risk_assessment=self.extract_risk_assessment(text),
            investment_rating=self.extract_investment_rating(text)
        )
        
        return report
    
    def _extract_title(self, text: str) -> str:
        """
        提取标题
        """
        # 简单的标题提取逻辑
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                if any(key in line for key in ['研报', '报告', '分析', '研究']):
                    return line
        return '未识别标题'
    
    def _extract_date(self, text: str) -> str:
        """
        提取日期
        """
        date_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{8}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return '未识别日期'
    
    def _extract_author(self, text: str) -> str:
        """
        提取作者
        """
        # 简单的作者提取
        patterns = [
            r'作者.*[:：](.*)',
            r'分析师.*[:：](.*)',
            r'(?:作者|分析师)\s*(.*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                author = match.group(1).strip()
                if len(author) > 1 and len(author) < 50:
                    return author
        return '未识别作者'
    
    def _extract_institution(self, text: str) -> str:
        """
        提取机构
        """
        institutions = [
            '中信证券', '海通证券', '国泰君安', '华泰证券', '招商证券',
            '广发证券', '申万宏源', '中信建投', '银河证券', '中金公司'
        ]
        
        for institution in institutions:
            if institution in text:
                return institution
        return '未识别机构'
