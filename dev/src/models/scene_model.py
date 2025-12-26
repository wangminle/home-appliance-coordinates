# -*- coding: utf-8 -*-
"""
场景数据模型

V2.0 重构：单一数据源（Single Source of Truth）
整合所有场景状态数据，实现观察者模式通知视图更新。

核心设计原则：
1. 数据集中管理 - 所有场景数据在此模型中统一管理
2. 观察者模式 - 数据变更时自动通知订阅者
3. 不可变语义 - 外部获取数据时返回副本，防止意外修改
"""

import math
import uuid
from typing import List, Optional, Dict, Callable, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from models.coordinate_frame import CoordinateFrame, WORLD_FRAME, create_user_frame
from models.device_model import Device
from utils.validation import Validator


class ChangeType(Enum):
    """数据变更类型枚举"""
    DEVICE_ADDED = "device_added"
    DEVICE_UPDATED = "device_updated"
    DEVICE_REMOVED = "device_removed"
    DEVICES_CLEARED = "devices_cleared"
    MEASUREMENT_SET = "measurement_set"
    MEASUREMENT_CLEARED = "measurement_cleared"
    SECTOR_ADDED = "sector_added"
    SECTOR_CLEARED = "sector_cleared"
    USER_POSITION_SET = "user_position_set"
    USER_POSITION_CLEARED = "user_position_cleared"
    COORD_RANGE_CHANGED = "coord_range_changed"
    LABEL_POSITION_CHANGED = "label_position_changed"
    FULL_RESET = "full_reset"


@dataclass
class LabelPosition:
    """
    标签位置数据
    
    用于记录标签的位置信息，支持区分自动计算和手动设置。
    """
    x: float
    y: float
    is_manual: bool = False  # 是否手动设置
    direction: str = ""       # 方向名称（调试用）
    
    def copy(self) -> 'LabelPosition':
        """创建副本"""
        return LabelPosition(
            x=self.x,
            y=self.y,
            is_manual=self.is_manual,
            direction=self.direction
        )


@dataclass
class SectorData:
    """
    扇形数据
    
    表示一个扇形区域的所有参数。
    """
    center_x: float           # 扇形圆心X坐标（世界坐标系）
    center_y: float           # 扇形圆心Y坐标（世界坐标系）
    radius: float             # 扇形半径
    start_angle_deg: float    # 起始角度（度数，从X轴正向逆时针）
    end_angle_deg: float      # 结束角度（度数）
    sector_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def copy(self) -> 'SectorData':
        """创建副本"""
        return SectorData(
            center_x=self.center_x,
            center_y=self.center_y,
            radius=self.radius,
            start_angle_deg=self.start_angle_deg,
            end_angle_deg=self.end_angle_deg,
            sector_id=self.sector_id
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        检查点是否在扇形内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            True 如果点在扇形内
        """
        # 计算点到圆心的距离
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 超出半径范围
        if distance > self.radius:
            return False
        
        # 特殊情况：圆心点始终在扇形内
        if distance < 0.01:
            return True
        
        # 计算点相对于圆心的角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 归一化角度到 [0, 360) 范围
        while angle_deg < 0:
            angle_deg += 360
        while angle_deg >= 360:
            angle_deg -= 360
        
        # 归一化起始和结束角度
        start = self.start_angle_deg % 360
        end = self.end_angle_deg % 360
        if start < 0:
            start += 360
        if end < 0:
            end += 360
        
        # 检查角度是否在扇形范围内
        if start <= end:
            return start <= angle_deg <= end
        else:
            # 跨越0度的情况
            return angle_deg >= start or angle_deg <= end


@dataclass
class MeasurementData:
    """
    测量点数据
    
    表示用户点击创建的测量点及其计算结果。
    """
    x: float                  # 测量点X坐标（世界坐标系）
    y: float                  # 测量点Y坐标（世界坐标系）
    distance_to_origin: float = 0.0      # 到世界原点的距离
    angle_to_origin: float = 0.0         # 与世界原点的角度
    distance_to_user: Optional[float] = None   # 到用户位置的距离
    angle_to_user: Optional[float] = None      # 与用户位置的角度
    created_time: datetime = field(default_factory=datetime.now)
    
    def copy(self) -> 'MeasurementData':
        """创建副本"""
        return MeasurementData(
            x=self.x,
            y=self.y,
            distance_to_origin=self.distance_to_origin,
            angle_to_origin=self.angle_to_origin,
            distance_to_user=self.distance_to_user,
            angle_to_user=self.angle_to_user,
            created_time=self.created_time
        )


class SceneModel:
    """
    场景数据模型 - 单一数据源
    
    整合所有场景状态数据，实现观察者模式通知视图更新。
    所有数据变更都通过此模型进行，确保数据一致性。
    
    主要职责：
    1. 管理场景中的所有数据（设备、测量点、扇形、坐标系）
    2. 提供数据的增删改查接口
    3. 实现观察者模式，数据变更时通知订阅者
    4. 管理标签位置（支持自动计算和手动设置）
    """
    
    MAX_DEVICES = 10  # 设备数量上限
    
    def __init__(self):
        """初始化场景模型"""
        # === 坐标系 ===
        self.world_frame: CoordinateFrame = WORLD_FRAME
        self._user_frame: Optional[CoordinateFrame] = None
        self._coord_range: Tuple[float, float] = (10.0, 10.0)  # (x_range, y_range)
        
        # === 场景元素 ===
        self._devices: List[Device] = []
        self._measurement: Optional[MeasurementData] = None
        self._sectors: List[SectorData] = []
        
        # === 标签位置管理 ===
        self._label_positions: Dict[str, LabelPosition] = {}
        
        # === 观察者列表 ===
        self._observers: List[Callable[[ChangeType, Any], None]] = []
        
        # === 项目状态 ===
        self._is_modified: bool = False
        
        print("[OK] SceneModel 初始化完成")
    
    # ==================== 属性访问器 ====================
    
    @property
    def user_frame(self) -> Optional[CoordinateFrame]:
        """获取用户坐标系（只读）"""
        return self._user_frame
    
    @property
    def coord_range(self) -> Tuple[float, float]:
        """获取坐标范围"""
        return self._coord_range
    
    @property
    def is_modified(self) -> bool:
        """获取修改状态"""
        return self._is_modified
    
    # ==================== 坐标系管理 ====================
    
    def set_user_position(self, x: float, y: float) -> bool:
        """
        设置用户位置（创建/更新用户坐标系）
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
            
        Returns:
            是否设置成功
        """
        try:
            self._user_frame = create_user_frame(x, y)
            self._is_modified = True
            
            # 如果有测量点，更新用户相关的计算
            if self._measurement:
                self._update_measurement_user_data()
            
            self._notify_observers(ChangeType.USER_POSITION_SET, {'x': x, 'y': y})
            print(f"[OK] 用户位置已设置: ({x:.3f}, {y:.3f})")
            return True
        except Exception as e:
            print(f"[ERROR] 设置用户位置失败: {e}")
            return False
    
    def clear_user_position(self):
        """清除用户坐标系"""
        if self._user_frame is not None:
            self._user_frame = None
            self._is_modified = True
            
            # 清除测量点的用户相关数据
            if self._measurement:
                self._measurement.distance_to_user = None
                self._measurement.angle_to_user = None
            
            self._notify_observers(ChangeType.USER_POSITION_CLEARED, None)
            print("[OK] 用户位置已清除")
    
    def get_user_position(self) -> Optional[Tuple[float, float]]:
        """
        获取用户位置
        
        Returns:
            用户位置 (x, y)，如果未设置则返回 None
        """
        if self._user_frame:
            return (self._user_frame.origin_x, self._user_frame.origin_y)
        return None
    
    def is_user_frame_active(self) -> bool:
        """
        用户坐标系是否激活
        
        Returns:
            True 如果用户坐标系已设置
        """
        return self._user_frame is not None
    
    def set_coordinate_range(self, x_range: float, y_range: float) -> bool:
        """
        设置坐标显示范围
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
            
        Returns:
            是否设置成功
        """
        if x_range <= 0 or y_range <= 0:
            print("[ERROR] 坐标范围必须大于0")
            return False
        
        if (x_range < Validator.MIN_COORDINATE_RANGE or x_range > Validator.MAX_COORDINATE_RANGE or
                y_range < Validator.MIN_COORDINATE_RANGE or y_range > Validator.MAX_COORDINATE_RANGE):
            print(f"[ERROR] 坐标范围必须在{Validator.MIN_COORDINATE_RANGE}-{Validator.MAX_COORDINATE_RANGE}之间")
            return False
        
        old_range = self._coord_range
        self._coord_range = (x_range, y_range)
        self._is_modified = True
        
        self._notify_observers(ChangeType.COORD_RANGE_CHANGED, {
            'old': old_range,
            'new': self._coord_range
        })
        print(f"[OK] 坐标范围已设置: ±{x_range} x ±{y_range}")
        return True
    
    # ==================== 设备管理 ====================
    
    def get_devices(self) -> List[Device]:
        """
        获取所有设备的副本
        
        Returns:
            设备列表的副本
        """
        return [device for device in self._devices]
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """
        根据ID获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备对象，如果未找到返回 None
        """
        for device in self._devices:
            if device.id == device_id:
                return device
        return None
    
    def get_device_by_name(self, name: str) -> Optional[Device]:
        """
        根据名称获取设备
        
        Args:
            name: 设备名称
            
        Returns:
            设备对象，如果未找到返回 None
        """
        for device in self._devices:
            if device.name == name:
                return device
        return None
    
    def add_device(self, device: Device) -> Tuple[bool, str]:
        """
        添加设备
        
        Args:
            device: 要添加的设备
            
        Returns:
            (成功标志, 消息)
        """
        # 数量检查
        if len(self._devices) >= self.MAX_DEVICES:
            return False, f"设备数量已达上限({self.MAX_DEVICES}个)"
        
        # 名称唯一性检查
        if self.get_device_by_name(device.name):
            return False, f"设备名称 '{device.name}' 已存在"
        
        # ID唯一性检查
        if self.get_device_by_id(device.id):
            return False, f"设备ID '{device.id}' 已存在"
        
        self._devices.append(device)
        self._is_modified = True
        
        self._notify_observers(ChangeType.DEVICE_ADDED, {'device': device})
        print(f"[OK] 设备添加成功: {device.name} ({device.x:.3f}, {device.y:.3f})")
        return True, "设备添加成功"
    
    def update_device(self, device_id: str, new_data: Device) -> Tuple[bool, str]:
        """
        更新设备信息
        
        Args:
            device_id: 要更新的设备ID
            new_data: 新的设备数据
            
        Returns:
            (成功标志, 消息)
        """
        # 查找设备
        old_device = None
        device_index = -1
        for i, d in enumerate(self._devices):
            if d.id == device_id:
                old_device = d
                device_index = i
                break
        
        if old_device is None:
            return False, "设备不存在"
        
        # 名称唯一性检查（排除自己）
        existing = self.get_device_by_name(new_data.name)
        if existing and existing.id != device_id:
            return False, f"设备名称 '{new_data.name}' 已被使用"
        
        # 保持原ID和创建时间
        new_data.id = old_device.id
        new_data.created_time = old_device.created_time
        
        self._devices[device_index] = new_data
        self._is_modified = True
        
        # 更新对应的标签位置（如果有）
        label_id = f"device_{device_id}"
        if label_id in self._label_positions:
            # 如果是自动位置，标记需要重新计算
            if not self._label_positions[label_id].is_manual:
                del self._label_positions[label_id]
        
        self._notify_observers(ChangeType.DEVICE_UPDATED, {
            'old_device': old_device,
            'new_device': new_data
        })
        print(f"[OK] 设备更新成功: {old_device.name} -> {new_data.name}")
        return True, "设备更新成功"
    
    def remove_device(self, device_id: str) -> Tuple[bool, str]:
        """
        删除设备
        
        Args:
            device_id: 要删除的设备ID
            
        Returns:
            (成功标志, 消息)
        """
        device_to_remove = None
        for d in self._devices:
            if d.id == device_id:
                device_to_remove = d
                break
        
        if device_to_remove is None:
            return False, "设备不存在"
        
        self._devices.remove(device_to_remove)
        self._is_modified = True
        
        # 删除对应的标签位置
        label_id = f"device_{device_id}"
        if label_id in self._label_positions:
            del self._label_positions[label_id]
        
        self._notify_observers(ChangeType.DEVICE_REMOVED, {'device': device_to_remove})
        print(f"[OK] 设备删除成功: {device_to_remove.name}")
        return True, "设备删除成功"
    
    def clear_devices(self):
        """清除所有设备"""
        if self._devices:
            old_devices = self._devices.copy()
            self._devices.clear()
            self._is_modified = True
            
            # 清除所有设备的标签位置
            keys_to_remove = [k for k in self._label_positions.keys() if k.startswith("device_")]
            for key in keys_to_remove:
                del self._label_positions[key]
            
            self._notify_observers(ChangeType.DEVICES_CLEARED, {'devices': old_devices})
            print("[OK] 所有设备已清除")
    
    def get_device_count(self) -> int:
        """获取设备数量"""
        return len(self._devices)
    
    # ==================== 测量点管理 ====================
    
    def set_measurement(self, x: float, y: float):
        """
        设置测量点
        
        Args:
            x: 测量点X坐标
            y: 测量点Y坐标
        """
        # 计算世界坐标系数据
        distance_to_origin = self.world_frame.distance_from_origin(x, y)
        angle_to_origin = self.world_frame.min_angle_to_axis(x, y)
        
        # 创建测量数据
        self._measurement = MeasurementData(
            x=x,
            y=y,
            distance_to_origin=distance_to_origin,
            angle_to_origin=angle_to_origin
        )
        
        # 如果有用户坐标系，计算用户相关数据
        if self._user_frame:
            self._update_measurement_user_data()
        
        self._is_modified = True
        self._notify_observers(ChangeType.MEASUREMENT_SET, {'measurement': self._measurement})
        print(f"[OK] 测量点已设置: ({x:.3f}, {y:.3f})")
    
    def _update_measurement_user_data(self):
        """更新测量点的用户坐标系相关数据"""
        if self._measurement and self._user_frame:
            self._measurement.distance_to_user = self._user_frame.distance_from_origin(
                self._measurement.x, self._measurement.y
            )
            self._measurement.angle_to_user = self._user_frame.min_angle_to_axis(
                self._measurement.x, self._measurement.y
            )
    
    def get_measurement(self) -> Optional[MeasurementData]:
        """
        获取测量点数据
        
        Returns:
            测量点数据的副本，如果没有则返回 None
        """
        if self._measurement:
            return self._measurement.copy()
        return None
    
    def clear_measurement(self):
        """清除测量点"""
        if self._measurement:
            self._measurement = None
            
            # 清除测量点的标签位置
            if "measurement" in self._label_positions:
                del self._label_positions["measurement"]
            
            self._notify_observers(ChangeType.MEASUREMENT_CLEARED, None)
            print("[OK] 测量点已清除")
    
    # ==================== 扇形管理 ====================
    
    def add_sector(self, center_x: float, center_y: float, radius: float,
                   start_angle_deg: float, end_angle_deg: float) -> SectorData:
        """
        添加扇形区域
        
        Args:
            center_x: 扇形圆心X坐标
            center_y: 扇形圆心Y坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
            
        Returns:
            创建的扇形数据对象
        """
        sector = SectorData(
            center_x=center_x,
            center_y=center_y,
            radius=radius,
            start_angle_deg=start_angle_deg,
            end_angle_deg=end_angle_deg
        )
        
        self._sectors.append(sector)
        self._is_modified = True
        
        self._notify_observers(ChangeType.SECTOR_ADDED, {'sector': sector})
        print(f"[OK] 扇形添加成功: 中心({center_x:.3f}, {center_y:.3f}), 半径{radius:.3f}")
        return sector
    
    def get_sectors(self) -> List[SectorData]:
        """
        获取所有扇形的副本
        
        Returns:
            扇形列表的副本
        """
        return [s.copy() for s in self._sectors]
    
    def clear_sectors(self):
        """清除所有扇形"""
        if self._sectors:
            self._sectors.clear()
            self._is_modified = True
            
            self._notify_observers(ChangeType.SECTOR_CLEARED, None)
            print("[OK] 所有扇形已清除")
    
    # ==================== 标签位置管理 ====================
    
    def set_label_position(self, element_id: str, x: float, y: float, 
                           is_manual: bool = False, direction: str = ""):
        """
        设置标签位置（自动计算或手动拖拽）
        
        Args:
            element_id: 元素ID（如 "device_xxx", "measurement"）
            x: 标签X坐标
            y: 标签Y坐标
            is_manual: 是否手动设置
            direction: 方向名称（调试用）
        """
        self._label_positions[element_id] = LabelPosition(
            x=x,
            y=y,
            is_manual=is_manual,
            direction=direction
        )
        
        if is_manual:
            self._is_modified = True
            self._notify_observers(ChangeType.LABEL_POSITION_CHANGED, {
                'element_id': element_id,
                'position': self._label_positions[element_id]
            })
    
    def get_label_position(self, element_id: str) -> Optional[LabelPosition]:
        """
        获取标签位置
        
        Args:
            element_id: 元素ID
            
        Returns:
            标签位置的副本，如果没有则返回 None
        """
        if element_id in self._label_positions:
            return self._label_positions[element_id].copy()
        return None
    
    def get_all_label_positions(self) -> Dict[str, LabelPosition]:
        """
        获取所有标签位置
        
        Returns:
            标签位置字典的副本
        """
        return {k: v.copy() for k, v in self._label_positions.items()}
    
    def get_manual_label_positions(self) -> Dict[str, LabelPosition]:
        """
        获取所有手动设置的标签位置
        
        Returns:
            手动标签位置字典
        """
        return {k: v.copy() for k, v in self._label_positions.items() if v.is_manual}
    
    def reset_label_to_auto(self, element_id: str):
        """
        重置标签为自动计算位置
        
        Args:
            element_id: 元素ID
        """
        if element_id in self._label_positions:
            del self._label_positions[element_id]
            self._is_modified = True
            self._notify_observers(ChangeType.LABEL_POSITION_CHANGED, {
                'element_id': element_id,
                'position': None  # 表示需要重新计算
            })
            print(f"[OK] 标签位置已重置: {element_id}")
    
    def reset_all_labels_to_auto(self):
        """重置所有标签为自动计算位置"""
        manual_labels = [k for k, v in self._label_positions.items() if v.is_manual]
        for element_id in manual_labels:
            del self._label_positions[element_id]
        
        if manual_labels:
            self._is_modified = True
            self._notify_observers(ChangeType.LABEL_POSITION_CHANGED, {'reset_all': True})
            print(f"[OK] {len(manual_labels)} 个标签位置已重置")
    
    # ==================== 观察者模式 ====================
    
    def add_observer(self, callback: Callable[[ChangeType, Any], None]):
        """
        添加数据变更观察者
        
        Args:
            callback: 回调函数，接收 (变更类型, 变更数据) 参数
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[ChangeType, Any], None]):
        """
        移除数据变更观察者
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, change_type: ChangeType, data: Any = None):
        """
        通知所有观察者数据已变更
        
        Args:
            change_type: 变更类型
            data: 变更相关数据
        """
        for observer in self._observers:
            try:
                observer(change_type, data)
            except Exception as e:
                print(f"[WARN] 通知观察者失败: {e}")
    
    # ==================== 完整重置 ====================
    
    def reset(self):
        """重置场景为初始状态"""
        self._devices.clear()
        self._measurement = None
        self._sectors.clear()
        self._user_frame = None
        self._coord_range = (10.0, 10.0)
        self._label_positions.clear()
        self._is_modified = False
        
        self._notify_observers(ChangeType.FULL_RESET, None)
        print("[OK] 场景已重置")
    
    def mark_saved(self):
        """标记为已保存状态"""
        self._is_modified = False
    
    def mark_modified(self):
        """标记为已修改状态"""
        self._is_modified = True
    
    # ==================== 序列化支持 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将场景数据转换为字典（用于保存）
        
        Returns:
            包含所有场景数据的字典
        """
        result = {
            'coord_range': {
                'x_range': self._coord_range[0],
                'y_range': self._coord_range[1]
            },
            'devices': [d.to_dict() for d in self._devices],
            'user_coordinate_system': {
                'enabled': self._user_frame is not None,
                'user_x': self._user_frame.origin_x if self._user_frame else None,
                'user_y': self._user_frame.origin_y if self._user_frame else None
            },
            'label_positions': {
                k: {
                    'x': v.x,
                    'y': v.y,
                    'is_manual': v.is_manual,
                    'direction': v.direction
                }
                for k, v in self._label_positions.items()
                if v.is_manual  # 只保存手动位置
            }
        }
        
        return result
    
    def from_dict(self, data: Dict[str, Any]):
        """
        从字典恢复场景数据（用于加载）
        
        Args:
            data: 场景数据字典
        """
        # 重置当前状态
        self.reset()
        
        # 恢复坐标范围
        coord = data.get('coord_range', {})
        x_range = coord.get('x_range', 10.0)
        y_range = coord.get('y_range', 10.0)
        self.set_coordinate_range(x_range, y_range)
        
        # 恢复设备
        devices_data = data.get('devices', [])
        for d_data in devices_data:
            try:
                device = Device.from_dict(d_data)
                self.add_device(device)
            except Exception as e:
                print(f"[WARN] 恢复设备失败: {e}")
        
        # 恢复用户坐标系
        user_coord = data.get('user_coordinate_system', {})
        if user_coord.get('enabled'):
            user_x = user_coord.get('user_x')
            user_y = user_coord.get('user_y')
            if user_x is not None and user_y is not None:
                self.set_user_position(user_x, user_y)
        
        # 恢复手动标签位置
        label_positions = data.get('label_positions', {})
        for element_id, pos_data in label_positions.items():
            if pos_data.get('is_manual'):
                self.set_label_position(
                    element_id,
                    pos_data['x'],
                    pos_data['y'],
                    is_manual=True,
                    direction=pos_data.get('direction', '')
                )
        
        # 标记为未修改（刚加载完成）
        self._is_modified = False
        print("[OK] 场景数据已从字典恢复")
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"SceneModel(devices={len(self._devices)}, "
                f"sectors={len(self._sectors)}, "
                f"measurement={'有' if self._measurement else '无'}, "
                f"user_frame={'有' if self._user_frame else '无'})")

