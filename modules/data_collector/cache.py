# -*- coding: utf-8 -*-
"""
数据缓存管理

提供本地缓存功能，支持SQLite存储和TTL过期机制
"""

import json
import sqlite3
import hashlib
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict
import pandas as pd

from .base import DataQuery, DataResponse, IndicatorType

logger = logging.getLogger(__name__)


class DataCache:
    """
    数据缓存管理器
    
    使用SQLite实现本地缓存，支持TTL过期和增量更新
    """
    
    def __init__(
        self, 
        cache_dir: str = "./data/cache",
        default_ttl: int = 86400,  # 默认24小时
        max_size_mb: int = 100
    ):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认TTL（秒）
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / "data_cache.db"
        self.default_ttl = default_ttl
        self.max_size_mb = max_size_mb
        
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 创建缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_store (
                cache_key TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                indicator_type TEXT,
                start_date TEXT,
                end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                hit_count INTEGER DEFAULT 0,
                size_bytes INTEGER DEFAULT 0
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at 
            ON cache_store(expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_indicator_type 
            ON cache_store(indicator_type)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cache database initialized at {self.db_path}")
    
    def _generate_key(self, query: DataQuery) -> str:
        """生成缓存键"""
        key_str = f"{query.indicator.value}:{query.start_date}:{query.end_date}:{query.frequency}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _df_to_json(self, df: pd.DataFrame) -> str:
        """DataFrame转JSON"""
        # 转换日期时间对象
        df_copy = df.copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].astype(str)
        
        return df_copy.to_json(orient='records', date_format='iso')
    
    def _json_to_df(self, json_str: str) -> Optional[pd.DataFrame]:
        """JSON转DataFrame"""
        if not json_str:
            return None
        
        try:
            data = json.loads(json_str)
            if not data:
                return None
            
            df = pd.DataFrame(data)
            
            # 尝试解析日期列
            for col in df.columns:
                if 'date' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            
            return df
        except Exception as e:
            logger.error(f"Failed to parse JSON to DataFrame: {e}")
            return None
    
    def get(self, query: DataQuery) -> Optional[DataResponse]:
        """
        获取缓存数据
        
        Args:
            query: 数据查询条件
            
        Returns:
            DataResponse或None（如果不存在或已过期）
        """
        cache_key = self._generate_key(query)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT data_json, expires_at, hit_count
                FROM cache_store
                WHERE cache_key = ?
            """, (cache_key,))
            
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            data_json, expires_at_str, hit_count = row
            
            # 检查是否过期
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    # 已过期，删除
                    cursor.execute("DELETE FROM cache_store WHERE cache_key = ?", (cache_key,))
                    conn.commit()
                    conn.close()
                    return None
            
            # 更新命中次数
            cursor.execute("""
                UPDATE cache_store 
                SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE cache_key = ?
            """, (cache_key,))
            conn.commit()
            
            # 解析数据
            df = self._json_to_df(data_json)
            
            conn.close()
            
            if df is not None:
                return DataResponse(
                    success=True,
                    data=df,
                    cached=True,
                    query=query
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            conn.close()
            return None
    
    def set(
        self, 
        query: DataQuery, 
        data: pd.DataFrame,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据
        
        Args:
            query: 数据查询条件
            data: 要缓存的数据
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if data is None or data.empty:
            return False
        
        cache_key = self._generate_key(query)
        ttl = ttl or self.default_ttl
        
        # 序列化数据
        data_json = self._df_to_json(data)
        size_bytes = len(data_json.encode())
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO cache_store
                (cache_key, data_json, indicator_type, start_date, end_date, 
                 expires_at, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key,
                data_json,
                query.indicator.value,
                query.start_date,
                query.end_date,
                expires_at.isoformat(),
                size_bytes
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Cached data for key: {cache_key[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            conn.close()
            return False
    
    def invalidate(self, query: DataQuery) -> bool:
        """
        使缓存失效
        
        Args:
            query: 数据查询条件
            
        Returns:
            是否成功
        """
        cache_key = self._generate_key(query)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM cache_store WHERE cache_key = ?", (cache_key,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            return affected > 0
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            conn.close()
            return False
    
    def invalidate_by_indicator(self, indicator: IndicatorType) -> int:
        """
        使指定指标的所有缓存失效
        
        Args:
            indicator: 指标类型
            
        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM cache_store WHERE indicator_type = ?",
                (indicator.value,)
            )
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            logger.info(f"Invalidated {affected} cache entries for {indicator.value}")
            return affected
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            conn.close()
            return 0
    
    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM cache_store 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                logger.info(f"Cleaned up {affected} expired cache entries")
            
            return affected
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            conn.close()
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM cache_store")
            total_count = cursor.fetchone()[0]
            
            # 总大小
            cursor.execute("SELECT SUM(size_bytes) FROM cache_store")
            total_size = cursor.fetchone()[0] or 0
            
            # 过期记录数
            cursor.execute("""
                SELECT COUNT(*) FROM cache_store 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            expired_count = cursor.fetchone()[0]
            
            # 按指标统计
            cursor.execute("""
                SELECT indicator_type, COUNT(*) as count
                FROM cache_store
                GROUP BY indicator_type
            """)
            by_indicator = dict(cursor.fetchall())
            
            # 命中次数统计
            cursor.execute("SELECT SUM(hit_count) FROM cache_store")
            total_hits = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_count": total_count,
                "total_size_mb": total_size / (1024 * 1024),
                "expired_count": expired_count,
                "by_indicator": by_indicator,
                "total_hits": total_hits,
                "db_path": str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            conn.close()
            return {}
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM cache_store")
            conn.commit()
            conn.close()
            
            logger.info("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            conn.close()
            return False


def get_cached_data(
    collector,
    query: DataQuery,
    cache: Optional[DataCache] = None,
    use_cache: bool = True
) -> DataResponse:
    """
    便捷函数：获取数据（带缓存）
    
    Args:
        collector: 数据采集器
        query: 查询条件
        cache: 缓存管理器
        use_cache: 是否使用缓存
        
    Returns:
        DataResponse
    """
    # 尝试从缓存获取
    if use_cache and cache is not None:
        cached_response = cache.get(query)
        if cached_response is not None:
            logger.info(f"Cache hit for {query.indicator.value}")
            return cached_response
    
    # 从数据源获取
    try:
        df = collector.fetch_macro_indicator(
            query.indicator,
            query.start_date,
            query.end_date
        )
        
        # 存入缓存
        if use_cache and cache is not None and df is not None and not df.empty:
            cache.set(query, df)
        
        return DataResponse(
            success=True,
            data=df,
            query=query,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return DataResponse(
            success=False,
            error=str(e),
            query=query
        )