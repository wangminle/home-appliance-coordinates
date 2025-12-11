# -*- coding: utf-8 -*-
"""
视图模块

包含GUI界面组件和用户界面相关功能

V2.0 新增:
- SceneRenderer: 场景渲染器，纯绑制逻辑
"""

from .main_window import MainWindow
from .input_panel import InputPanel
from .matplotlib_view import MatplotlibView

# V2.0 新增模块
from .scene_renderer import SceneRenderer

__all__ = [
    # 原有模块
    'MainWindow',
    'InputPanel', 
    'MatplotlibView',
    # V2.0 新增模块
    'SceneRenderer',
] 