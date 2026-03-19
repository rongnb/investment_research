# -*- coding: utf-8 -*-
"""
API接口层

提供RESTful API和WebSocket接口
"""

from .routes import create_app

__all__ = ['create_app']
