# -*- coding: utf-8 -*-
"""
控制器模块

包含应用程序的业务逻辑控制器

V2.0 新增:
- SceneController: 场景控制器，从View层剥离的业务逻辑
"""

from .matplotlib_controller import MatplotlibController

# V2.0 新增模块
from .scene_controller import SceneController

__all__ = [
    # 原有模块
    'MatplotlibController',
    # V2.0 新增模块
    'SceneController',
] 