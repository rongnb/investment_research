# -*- coding: utf-8 -*-
"""
Tushare 数据采集适配器

实现基于Tushare的数据采集功能
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import time

from .base import (
    DataCollector, DataSourceType, IndicatorType, 
    DataQuery, retry_on_failure
)

logger = logging.getLogger(__name__)


class TushareCollector(DataCollector):
    """
    Tushare 数据采集器
    
    使用Tushare Pro API获取数据
    需要设置 TUSHARE_TOKEN 环境变量
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化Tushare采集器
        
        Args:
            token: Tushare Token（可选，从环境变量读取）
        """
        self._token = token or os.getenv("TUSHARE_TOKEN")
        self._api = None
        super().__init__(DataSourceType.TUSHARE)
    
    def _initialize(self) -> None:
        """初始化Tushare API"""
        if not self._token:
            logger.warning("Tushare token not set. Set TUSHARE_TOKEN environment variable.")
            return
        
        try:
            import tushare as ts
            ts.set_token(self._token)
            self._api = ts.pro_api()
            self.logger.info("Tushare initialized successfully")
        except ImportError:
            logger.error("Tushare not installed. Install with: pip install tushare")
        except Exception as e:
            logger.error(f"Failed to initialize Tushare: {e}")
    
    def _check_api(self) -> bool:
        """检查API是否可用"""
        if self._api is None:
            self.logger.warning("Tushare API not initialized")
            return False
        return True
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """解析日期字符串为datetime"""
        if pd.isna(date_str):
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        date_str = str(date_str).strip()
        
        for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y%m", "%Y-%m"]:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def _convert_date_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换日期格式"""
        if df is None or df.empty:
            return df
        
        # 尝试转换常见日期列
        date_cols = ['trade_date', 'report_date', 'end_date', 'ann_date', 'cal_date']
        
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%Y%m%d')
                except:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
        
        return df
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def fetch_macro_indicator(
        self,
        indicator: IndicatorType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        通过Tushare获取宏观经济指标
        
        Note: Tushare主要提供金融数据，宏观数据较少
        这里展示如何调用，实际情况可能需要使用AKShare
        """
        self.logger.info(f"Fetching {indicator.value} from Tushare")
        
        if not self._check_api():
            return pd.DataFrame()
        
        try:
            # Tushare的宏观数据接口
            if indicator == IndicatorType.INTEREST_RATE:
                df = self._api.macro_china_lpr()
            elif indicator == IndicatorType.RESERVE_REQUIREMENT_RATIO:
                df = self._api.macro_china_rrr()
            else:
                # Tushare宏观数据有限，返回空表
                self.logger.warning(f"Indicator {indicator.value} not available in Tushare")
                return pd.DataFrame()
            
            if df is not None and not df.empty:
                df = self._convert_date_format(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch {indicator.value} from Tushare: {e}")
            return pd.DataFrame()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def fetch_stock_ohlc(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票OHLC数据
        
        Args:
            code: 股票代码 (如 '000001.SZ')
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型
            
        Returns:
            OHLC数据DataFrame
        """
        if not self._check_api():
            return pd.DataFrame()
        
        # 标准化代码格式
        if '.' not in code:
            if code.startswith('6'):
                code = f"{code}.SH"
            elif code.startswith(('0', '3')):
                code = f"{code}.SZ"
        
        self.logger.info(f"Fetching OHLC for {code} from {start_date} to {end_date}")
        
        try:
            # 格式化日期
            start = start_date.replace('-', '')
            end = end_date.replace('-', '')
            
            df = self._api.daily(
                ts_code=code,
                start_date=start,
                end_date=end
            )
            
            if df is not None and not df.empty:
                # 转换格式
                df = df.rename(columns={
                    'ts_code': 'code',
                    'trade_date': 'date',
                    'pre_close': 'pre_close',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'vol': 'volume',
                    'amount': 'amount'
                })
                
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLC for {code}: {e}")
            return pd.DataFrame()
    
    def fetch_stock_basic(self, exchange: str = "SSE") -> pd.DataFrame:
        """
        获取股票基本信息
        
        Args:
            exchange: 交易所 (SSE/SZSE/BSE)
            
        Returns:
            股票基本信息DataFrame
        """
        if not self._check_api():
            return pd.DataFrame()
        
        try:
            df = self._api.stock_basic(exchange=exchange)
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch stock basic: {e}")
            return pd.DataFrame()
    
    def fetch_financial_data(
        self,
        code: str,
        report_type: int = 1
    ) -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型 (1:合并报表, 2:单季报表)
            
        Returns:
            财务数据DataFrame
        """
        if not self._check_api():
            return pd.DataFrame()
        
        try:
            df = self._api.fincome(
                ts_code=code,
                report_type=report_type
            )
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch financial data: {e}")
            return pd.DataFrame()
    
    def fetch_index_daily(
        self,
        index_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            index_code: 指数代码 (如 '000300.SH' 代表沪深300)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据DataFrame
        """
        if not self._check_api():
            return pd.DataFrame()
        
        try:
            df = self._api.index_daily(
                ts_code=index_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    'ts_code': 'code',
                    'trade_date': 'date'
                })
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch index daily: {e}")
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        """测试Tushare连接"""
        if not self._check_api():
            return False
        
        try:
            # 尝试获取交易日历
            df = self._api.trade_cal(
                start_date=datetime.now().strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            return df is not None and not df.empty
        except Exception as e:
            self.logger.error(f"Tushare connection test failed: {e}")
            return False
    
    def get_token_status(self) -> Dict[str, Any]:
        """获取Token状态"""
        if not self._token:
            return {
                "configured": False,
                "message": "Token not set"
            }
        
        if self._api is None:
            return {
                "configured": True,
                "initialized": False,
                "message": "API not initialized"
            }
        
        return {
            "configured": True,
            "initialized": True,
            "message": "Ready"
        }