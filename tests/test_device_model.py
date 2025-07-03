# -*- coding: utf-8 -*-
"""
设备模型单元测试

测试Device类的各种功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev'))

from models.device_model import Device


class TestDevice:
    """设备模型测试类"""
    
    def test_device_creation(self):
        """测试设备创建"""
        device = Device("测试设备", 1.5, 2.5)
        
        assert device.name == "测试设备"
        assert device.x == 1.5
        assert device.y == 2.5
        assert device.id is not None
        assert len(device.id) > 0
    
    def test_device_validation(self):
        """测试设备数据验证"""
        # 正常情况
        device = Device("正常设备", 0, 0)
        assert device.name == "正常设备"
        
        # 设备名称为空
        with pytest.raises(ValueError, match="设备名称不能为空"):
            Device("", 0, 0)
        
        # 设备名称过长
        long_name = "a" * 25
        with pytest.raises(ValueError, match="设备名称长度不能超过20个字符"):
            Device(long_name, 0, 0)
        
        # 坐标值不是数字
        with pytest.raises(ValueError, match="坐标值必须是有效的数字"):
            Device("测试", "not_a_number", 0)
    
    def test_device_position_update(self):
        """测试设备位置更新"""
        device = Device("测试设备", 0, 0)
        
        device.update_position(3.14, -2.71)
        assert device.x == 3.14
        assert device.y == -2.71
    
    def test_device_name_update(self):
        """测试设备名称更新"""
        device = Device("原名称", 0, 0)
        
        device.update_name("新名称")
        assert device.name == "新名称"
    
    def test_distance_calculation(self):
        """测试距离计算"""
        device1 = Device("设备1", 0, 0)
        device2 = Device("设备2", 3, 4)
        
        # 测试设备间距离
        distance = device1.distance_to(device2)
        assert abs(distance - 5.0) < 1e-10
        
        # 测试到原点距离
        origin_distance = device2.distance_to_origin()
        assert abs(origin_distance - 5.0) < 1e-10
    
    def test_device_serialization(self):
        """测试设备序列化"""
        device = Device("序列化测试", 1.23, 4.56)
        
        # 转换为字典
        device_dict = device.to_dict()
        assert device_dict['name'] == "序列化测试"
        assert device_dict['x'] == 1.23
        assert device_dict['y'] == 4.56
        assert device_dict['id'] == device.id
        
        # 从字典创建设备
        new_device = Device.from_dict(device_dict)
        assert new_device.name == device.name
        assert new_device.x == device.x
        assert new_device.y == device.y
        assert new_device.id == device.id
    
    def test_device_equality(self):
        """测试设备相等性判断"""
        device1 = Device("设备1", 0, 0)
        device2 = Device("设备2", 1, 1)
        
        # 相同设备（基于ID）
        assert device1 == device1
        
        # 不同设备
        assert device1 != device2
        
        # 与非设备对象比较
        assert device1 != "not_a_device"
    
    def test_device_string_representation(self):
        """测试设备字符串表示"""
        device = Device("字符串测试", 1.0, 2.0)
        
        str_repr = str(device)
        assert "字符串测试" in str_repr
        assert "1.0" in str_repr
        assert "2.0" in str_repr
        
        repr_str = repr(device)
        assert "Device" in repr_str
        assert device.id in repr_str


if __name__ == "__main__":
    pytest.main([__file__]) 