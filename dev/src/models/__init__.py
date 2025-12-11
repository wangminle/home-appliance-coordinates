# -*- coding: utf-8 -*-
"""
数据模型模块

包含设备模型、坐标系统模型、测量点模型等数据结构定义

V2.0 新增:
- CoordinateFrame: 统一坐标系变换器
- SceneModel: 单一数据源场景模型
"""

from .device_model import Device
from .device_manager import DeviceManager
from .coordinate_model import CoordinateSystem
from .measurement_model import MeasurementPoint

# V2.0 新增模块
from .coordinate_frame import CoordinateFrame, WORLD_FRAME, create_user_frame
from .scene_model import SceneModel, ChangeType, LabelPosition, SectorData, MeasurementData

__all__ = [
    # 原有模块
    'Device',
    'DeviceManager',
    'CoordinateSystem', 
    'MeasurementPoint',
    # V2.0 新增模块
    'CoordinateFrame',
    'WORLD_FRAME',
    'create_user_frame',
    'SceneModel',
    'ChangeType',
    'LabelPosition',
    'SectorData',
    'MeasurementData',
] 