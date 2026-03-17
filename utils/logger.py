"""
日志工具函数
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logger(log_file: str = 'investment_research.log', 
                level: int = logging.INFO,
                max_bytes: int = 10*1024*1024,
                backup_count: int = 5) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        log_file: 日志文件名
        level: 日志级别
        max_bytes: 单文件最大字节数
        backup_count: 备份文件数
        
    Returns:
        配置好的logger
    """
    logger = logging.getLogger('investment_research')
    logger.setLevel(level)
    logger.propagate = False  # 防止日志重复输出
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"日志系统已初始化，日志文件: {log_file}")
        
    except Exception as e:
        logger.warning(f"无法创建日志文件，使用控制台输出: {e}")
    
    return logger

class Logger:
    """
    日志包装类
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = setup_logger()
        return cls._instance

    @staticmethod
    def get_logger():
        return Logger._instance

def log_decorator(func):
    """
    装饰器用于记录函数调用
    """
    def wrapper(*args, **kwargs):
        logger = Logger.get_logger()
        
        # 获取函数信息
        func_name = func.__name__
        func_module = func.__module__
        
        logger.debug(f"调用函数: {func_module}.{func_name}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func_name} 执行成功")
            return result
        
        except Exception as e:
            logger.error(f"函数 {func_name} 执行失败: {e}", exc_info=True)
            raise
    
    return wrapper

# 全局logger实例