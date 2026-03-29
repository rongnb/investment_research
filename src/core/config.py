"""
配置文件
"""
import os
from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "Invest Management"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./invest_management.db"
    
    # API配置
    API_PREFIX: str = "/api"
    
    # CORS
    ALLOWED_HOSTS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
