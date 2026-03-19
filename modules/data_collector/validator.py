# -*- coding: utf-8 -*-
"""
数据质量验证器

提供数据质量检查、异常值检测和缺失值处理功能
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"          # 基础检查
    STANDARD = "standard"    # 标准检查
    STRICT = "strict"        # 严格检查


class DataIssueType(Enum):
    """数据问题类型"""
    MISSING_VALUES = "missing_values"
    OUTLIERS = "outliers"
    DUPLICATES = "duplicates"
    INVALID_FORMAT = "invalid_format"
    INCONSISTENT = "inconsistent"
    STALE_DATA = "stale_data"


@dataclass
class DataIssue:
    """数据问题"""
    issue_type: DataIssueType
    severity: str  # warning, error
    description: str
    column: Optional[str] = None
    row_count: Optional[int] = None
    percentage: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    issues: List[DataIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_issue(self, issue: DataIssue) -> None:
        """添加问题"""
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False
    
    def summary(self) -> Dict[str, Any]:
        """生成摘要"""
        return {
            "passed": self.passed,
            "total_issues": len(self.issues),
            "errors": len([i for i in self.issues if i.severity == "error"]),
            "warnings": len([i for i in self.issues if i.severity == "warning"]),
            "issue_types": list(set([i.issue_type.value for i in self.issues]))
        }


class DataValidator:
    """
    数据质量验证器
    
    提供完整的数据质量检查功能
    """
    
    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        """
        初始化验证器
        
        Args:
            level: 验证级别
        """
        self.level = level
        self.logger = logging.getLogger(__name__)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        执行数据验证
        
        Args:
            df: 要验证的数据
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(passed=True)
        
        if df is None or df.empty:
            result.add_issue(DataIssue(
                issue_type=DataIssueType.INVALID_FORMAT,
                severity="error",
                description="DataFrame is empty or None"
            ))
            return result
        
        # 基础检查
        self._check_missing_values(df, result)
        
        if self.level.value in ["standard", "strict"]:
            self._check_duplicates(df, result)
            self._check_outliers(df, result)
        
        if self.level.value == "strict":
            self._check_data_freshness(df, result)
        
        # 收集统计信息
        result.stats = self._collect_stats(df)
        
        return result
    
    def _check_missing_values(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """检查缺失值"""
        total_cells = df.shape[0] * df.shape[1]
        
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            
            if missing_pct > 50:
                result.add_issue(DataIssue(
                    issue_type=DataIssueType.MISSING_VALUES,
                    severity="error",
                    description=f"Column '{col}' has {missing_pct:.1f}% missing values",
                    column=col,
                    row_count=missing_count,
                    percentage=missing_pct
                ))
            elif missing_pct > 10:
                result.add_issue(DataIssue(
                    issue_type=DataIssueType.MISSING_VALUES,
                    severity="warning",
                    description=f"Column '{col}' has {missing_pct:.1f}% missing values",
                    column=col,
                    row_count=missing_count,
                    percentage=missing_pct
                ))
    
    def _check_duplicates(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """检查重复行"""
        duplicate_count = df.duplicated().sum()
        
        if duplicate_count > 0:
            dup_pct = (duplicate_count / len(df)) * 100
            
            if dup_pct > 5:
                result.add_issue(DataIssue(
                    issue_type=DataIssueType.DUPLICATES,
                    severity="error",
                    description=f"Found {duplicate_count} duplicate rows ({dup_pct:.1f}%)",
                    row_count=duplicate_count,
                    percentage=dup_pct
                ))
            else:
                result.add_issue(DataIssue(
                    issue_type=DataIssueType.DUPLICATES,
                    severity="warning",
                    description=f"Found {duplicate_count} duplicate rows ({dup_pct:.1f}%)",
                    row_count=duplicate_count,
                    percentage=dup_pct
                ))
    
    def _check_outliers(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """检查异常值（使用IQR和3σ方法）"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            values = df[col].dropna()
            
            if len(values) < 10:
                continue
            
            # IQR方法
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_iqr = ((values < lower_bound) | (values > upper_bound)).sum()
            
            # 3σ方法
            mean = values.mean()
            std = values.std()
            outliers_3sigma = ((values < mean - 3*std) | (values > mean + 3*std)).sum()
            
            # 报告异常值
            max_outliers = max(outliers_iqr, outliers_3sigma)
            outlier_pct = (max_outliers / len(values)) * 100
            
            if outlier_pct > 10:
                result.add_issue(DataIssue(
                    issue_type=DataIssueType.OUTLIERS,
                    severity="warning",
                    description=f"Column '{col}' has {outlier_pct:.1f}% potential outliers",
                    column=col,
                    row_count=max_outliers,
                    percentage=outlier_pct,
                    details={
                        "mean": float(mean),
                        "std": float(std),
                        "min": float(values.min()),
                        "max": float(values.max())
                    }
                ))
    
    def _check_data_freshness(self, df: pd.DataFrame, result: ValidationResult) -> None:
        """检查数据时效性"""
        date_columns = ['date', 'trade_date', 'report_date', 'update_time']
        
        for col in date_columns:
            if col in df.columns:
                try:
                    dates = pd.to_datetime(df[col], errors='coerce')
                    latest = dates.max()
                    
                    if latest is not None and pd.notna(latest):
                        days_old = (datetime.now() - latest).days
                        
                        if days_old > 30:
                            result.add_issue(DataIssue(
                                issue_type=DataIssueType.STALE_DATA,
                                severity="warning",
                                description=f"Data is {days_old} days old (latest: {latest.date()})",
                                details={"days_old": days_old}
                            ))
                except:
                    pass
    
    def _collect_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """收集数据统计信息"""
        stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict()
        }
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        # 缺失值统计
        missing = df.isna().sum()
        stats["missing_counts"] = missing[missing > 0].to_dict()
        
        return stats


class DataCleaner:
    """
    数据清洗工具
    
    提供数据清洗和预处理功能
    """
    
    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        strategy: str = "drop",
        fill_value: Any = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        处理缺失值
        
        Args:
            df: 数据
            strategy: 处理策略 (drop/forward/backward/mean/median/fill)
            fill_value: 填充值
            columns: 处理的列
            
        Returns:
            清洗后的数据
        """
        df = df.copy()
        cols = columns or df.columns
        
        for col in cols:
            if col not in df.columns:
                continue
                
            if strategy == "drop":
                df = df.dropna(subset=[col])
            elif strategy == "forward":
                df[col] = df[col].fillna(method='ffill')
            elif strategy == "backward":
                df[col] = df[col].fillna(method='bfill')
            elif strategy == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median":
                df[col] = df[col].fillna(df[col].median())
            elif strategy == "fill" and fill_value is not None:
                df[col] = df[col].fillna(fill_value)
        
        return df
    
    @staticmethod
    def remove_outliers(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        移除异常值
        
        Args:
            df: 数据
            columns: 要检查的列
            method: 方法 (iqr/3sigma)
            threshold: 阈值
            
        Returns:
            清洗后的数据
        """
        df = df.copy()
        cols = columns or df.select_dtypes(include=[np.number]).columns
        
        mask = pd.Series([True] * len(df))
        
        for col in cols:
            if col not in df.columns:
                continue
                
            values = df[col].dropna()
            
            if method == "iqr":
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                col_mask = (df[col] >= lower) & (df[col] <= upper)
            else:  # 3sigma
                mean = values.mean()
                std = values.std()
                lower = mean - threshold * std
                upper = mean + threshold * std
                col_mask = (df[col] >= lower) & (df[col] <= upper)
            
            # 处理NaN
            col_mask = col_mask.fillna(True)
            mask = mask & col_mask
        
        return df[mask]
    
    @staticmethod
    def standardize_dates(
        df: pd.DataFrame,
        date_columns: Optional[List[str]] = None,
        format: str = "%Y-%m-%d"
    ) -> pd.DataFrame:
        """
        标准化日期格式
        
        Args:
            df: 数据
            date_columns: 日期列
            format: 目标格式
            
        Returns:
            转换后的数据
        """
        df = df.copy()
        cols = date_columns or ['date', 'trade_date', 'report_date']
        
        for col in cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        return df


# 便捷函数
def validate_and_clean(
    df: pd.DataFrame,
    level: ValidationLevel = ValidationLevel.STANDARD,
    clean: bool = True
) -> Tuple[pd.DataFrame, ValidationResult]:
    """
    验证并清洗数据
    
    Args:
        df: 原始数据
        level: 验证级别
        clean: 是否执行清洗
        
    Returns:
        (清洗后的数据, 验证结果)
    """
    validator = DataValidator(level)
    result = validator.validate(df)
    
    if clean and not result.passed:
        cleaner = DataCleaner()
        
        # 自动处理缺失值
        df = cleaner.handle_missing_values(df, strategy="forward")
        
        # 移除重复
        df = df.drop_duplicates()
    
    return df, result