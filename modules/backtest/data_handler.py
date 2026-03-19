"""
数据处理器
负责处理回测数据，提供按日期获取K线的功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..common.models import BarData


class DataHandler:
    """
    数据处理器
    
    负责加载、过滤和提供回测数据
    """
    
    def __init__(self):
        """初始化数据处理器"""
        self.data: Optional[pd.DataFrame] = None
        self.sorted_dates: List[datetime] = []
        
    def set_data(self, data: pd.DataFrame) -> None:
        """
        设置回测数据
        
        Args:
            data: 回测数据，必须包含以下列：
                - open, high, low, close, volume
                - index 必须是 datetime 类型
        """
        # 确保索引是datetime类型
        if not isinstance(data.index, pd.DatetimeIndex):
            # 尝试转换
            try:
                data.index = pd.to_datetime(data.index)
            except Exception as e:
                raise ValueError(f"无法将索引转换为datetime类型: {e}")
        
        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"数据缺少必要列: {missing_cols}")
        
        # 排序
        self.data = data.sort_index()
        self.sorted_dates = sorted(self.data.index.unique().tolist())
    
    def get_bars(self, start_date: Optional[str] = None, 
                 end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取指定日期范围的K线数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            过滤后的K线数据
        """
        if self.data is None:
            raise ValueError("未设置数据，请先调用set_data")
        
        data = self.data.copy()
        
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
        
        return data
    
    def get_dates(self, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> List[datetime]:
        """
        获取指定范围内的日期列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日期列表
        """
        if self.data is None:
            raise ValueError("未设置数据，请先调用set_data")
        
        dates = self.sorted_dates
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            dates = [d for d in dates if d >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            dates = [d for d in dates if d <= end_dt]
        
        return dates
    
    def get_bar_by_date_code(self, date: datetime, code: str) -> Optional[BarData]:
        """
        根据日期和代码获取K线
        
        Args:
            date: 日期
            code: 股票代码
            
        Returns:
            BarData对象，如果不存在返回None
        """
        if self.data is None:
            return None
        
        mask = (self.data.index == date)
        if 'code' in self.data.columns:
            mask &= (self.data['code'] == code)
        
        row = self.data[mask]
        if len(row) == 0:
            return None
        
        row = row.iloc[0]
        
        return BarData(
            code=row.get('code', code),
            timestamp=date,
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume']),
            amount=float(row.get('amount', 0)),
            frequency='1d'
        )
    
    def get_codes(self) -> List[str]:
        """
        获取所有股票代码
        
        Returns:
            股票代码列表
        """
        if self.data is None:
            return []
        
        if 'code' in self.data.columns:
            return self.data['code'].unique().tolist()
        
        return []
    
    def resample(self, frequency: str = 'W') -> pd.DataFrame:
        """
        重采样数据到不同周期
        
        Args:
            frequency: 重采样频率
            
        Returns:
            重采样后的数据
        """
        if self.data is None:
            raise ValueError("未设置数据，请先调用set_data")
        
        # 如果有多个股票，分别重采样
        if 'code' in self.data.columns:
            result = []
            for code, group in self.data.groupby('code'):
                resampled = group.resample(frequency).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'amount': 'sum' if 'amount' in group.columns else None
                }).dropna()
                resampled['code'] = code
                result.append(resampled)
            return pd.concat(result).sort_index()
        else:
            return self.data.resample(frequency).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'amount': 'sum' if 'amount' in self.data.columns else None
            }).dropna()
