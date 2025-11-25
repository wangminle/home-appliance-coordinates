# -*- coding: utf-8 -*-
"""
设备数据模型

定义家居设备的数据结构和相关操作
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
# 导入验证工具
try:
    from utils.validation import Validator
except ImportError:
    print("⚠️ 验证工具不可用")
    Validator = None


class Device:
    """
    设备模型类
    
    表示一个家居设备的完整信息，包括名称、坐标位置等属性
    """
    
    def __init__(self, name: str, x: float, y: float, device_id: Optional[str] = None):
        """
        初始化设备实例
        
        Args:
            name: 设备名称，1-20字符
            x: X轴坐标
            y: Y轴坐标  
            device_id: 设备唯一标识符，可选，默认自动生成
        """
        # 在赋值前进行严格验证
        if Validator:
            name_valid, name_msg = Validator.validate_device_name(name)
            if not name_valid:
                raise ValueError(name_msg)

            x_valid, x_msg = Validator.validate_coordinate_value(x)
            if not x_valid:
                raise ValueError(x_msg)
                
            y_valid, y_msg = Validator.validate_coordinate_value(y)
            if not y_valid:
                raise ValueError(y_msg)

        self.id = device_id or self._generate_id()
        self.name = str(name).strip()
        self.x = float(x)
        self.y = float(y)
        self.created_time = datetime.now()
        
        # 信息框位置状态管理 ✨ 智能避让功能（简化版）
        self.current_info_position: Optional[str] = None  # 当前信息框位置
        self.default_info_position: Optional[str] = None  # 默认信息框位置
        self.is_info_position_forced: bool = False  # 是否为强制避让位置
        
        # 验证数据有效性
        self._validate()
    
    def _generate_id(self) -> str:
        """
        生成唯一的设备ID
        
        Returns:
            UUID格式的设备标识符
        """
        return str(uuid.uuid4())
    
    def _validate(self):
        """
        验证设备数据的有效性
        
        Raises:
            ValueError: 当数据不符合要求时抛出异常
        """
        if not self.name or not isinstance(self.name, str):
            raise ValueError("设备名称不能为空且必须是字符串")
        
        if len(self.name) < 1 or len(self.name) > 20:
            raise ValueError("设备名称长度必须在1-20字符之间")
        
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise ValueError("坐标值必须是数字类型")
    
    def update_position(self, x: float, y: float):
        """
        更新设备位置
        
        Args:
            x: 新的X轴坐标
            y: 新的Y轴坐标
        """
        self.x = float(x)
        self.y = float(y)
        self._validate()
    
    def update_name(self, name: str):
        """
        更新设备名称
        
        Args:
            name: 新的设备名称
        """
        self.name = name
        self._validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将设备对象转换为字典格式
        
        Returns:
            包含设备所有信息的字典
        """
        result = {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'created_time': self.created_time.isoformat()
        }
        
        # 添加信息框位置状态
        result.update({
            'current_info_position': self.current_info_position,
            'default_info_position': self.default_info_position,
            'is_info_position_forced': self.is_info_position_forced
        })
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """
        从字典数据创建设备对象
        
        Args:
            data: 包含设备信息的字典
            
        Returns:
            Device实例
        """
        device = cls(
            name=data['name'],
            x=data['x'],
            y=data['y'],
            device_id=data.get('id')
        )
        
        # 如果有创建时间信息，则恢复
        if 'created_time' in data:
            try:
                device.created_time = datetime.fromisoformat(data['created_time'])
            except (ValueError, TypeError):
                # 如果时间格式不正确，使用当前时间
                pass
        
        # 恢复信息框位置状态
        try:
            if data.get('current_info_position'):
                device.current_info_position = data['current_info_position']
            if data.get('default_info_position'):
                device.default_info_position = data['default_info_position']
            device.is_info_position_forced = data.get('is_info_position_forced', False)
        except (ValueError, KeyError):
            # 如果位置数据不正确，保持默认值
            pass
                
        return device
    
    def distance_to(self, other: 'Device') -> float:
        """
        计算到另一个设备的距离
        
        Args:
            other: 另一个设备实例
            
        Returns:
            两设备间的欧几里得距离
        """
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def distance_to_origin(self) -> float:
        """
        计算到坐标原点的距离
        
        Returns:
            设备到原点(0,0)的距离
        """
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Device(name='{self.name}', x={self.x}, y={self.y})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"Device(id='{self.id}', name='{self.name}', "
                f"x={self.x}, y={self.y}, created_time='{self.created_time}')")
    
    def __eq__(self, other) -> bool:
        """判断设备是否相等（基于ID）"""
        if not isinstance(other, Device):
            return False
        return self.id == other.id
    
    def set_info_position(self, position: str, is_forced: bool = False):
        """
        设置设备信息框位置（简化版）
        
        Args:
            position: 信息框位置（字符串：如"top_left", "top_right"等）
            is_forced: 是否为强制避让位置
        """
        self.current_info_position = position
        if not is_forced and self.default_info_position is None:
            # 如果是第一次设置且不是强制位置，则记录为默认位置
            self.default_info_position = position
        self.is_info_position_forced = is_forced
    
    def reset_info_position_to_default(self):
        """重置信息框位置到默认位置"""
        if self.default_info_position is not None:
            self.current_info_position = self.default_info_position
            self.is_info_position_forced = False
    
    def get_info_position_status(self) -> Dict[str, Any]:
        """
        获取信息框位置状态信息
        
        Returns:
            包含位置状态的字典
        """
        return {
            'current_position': self.current_info_position,
            'default_position': self.default_info_position,
            'is_forced': self.is_info_position_forced
        }