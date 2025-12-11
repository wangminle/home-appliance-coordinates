# -*- coding: utf-8 -*-
"""
服务层模块

提供标签布局、碰撞检测、导出渲染等服务。
V2.0 第二期重构新增模块。
"""

from services.label_placer import LabelPlacer, BoundingBox
from services.collision_detector import CollisionDetector

__all__ = [
    'LabelPlacer',
    'BoundingBox',
    'CollisionDetector',
]

