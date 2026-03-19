# -*- coding: utf-8 -*-
"""
宏观分析模块 - API接口

提供RESTful API访问宏观分析功能
"""

from fastapi import APIRouter
from .routes import router

__all__ = [
    "router",
]
