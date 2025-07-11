# -*- coding: utf-8 -*-
"""
数据验证工具模块

提供输入数据验证、格式检查等功能
"""

import re
import math
from typing import Any, Optional, Union, Tuple, List


class Validator:
    """
    数据验证工具类
    
    提供各种数据验证功能，确保输入数据的有效性和安全性
    """
    
    # 常量定义
    MIN_COORDINATE_RANGE = 0.1
    MAX_COORDINATE_RANGE = 25.0
    MIN_DEVICE_NAME_LENGTH = 1
    MAX_DEVICE_NAME_LENGTH = 20
    
    @staticmethod
    def validate_device_name(name: Any) -> Tuple[bool, str]:
        """
        验证设备名称的有效性
        
        Args:
            name: 待验证的设备名称
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查是否为空或None
        if name is None:
            return False, "设备名称不能为空"
        
        # 转换为字符串
        name_str = str(name).strip()
        
        # 检查是否为空字符串
        if not name_str:
            return False, "设备名称不能为空"
        
        # 检查长度
        if len(name_str) < Validator.MIN_DEVICE_NAME_LENGTH:
            return False, f"设备名称长度不能少于{Validator.MIN_DEVICE_NAME_LENGTH}个字符"
        
        if len(name_str) > Validator.MAX_DEVICE_NAME_LENGTH:
            return False, f"设备名称长度不能超过{Validator.MAX_DEVICE_NAME_LENGTH}个字符"
        
        # 检查是否包含非法字符（可选）
        # 暂时允许所有字符，后续可根据需要添加限制
        
        return True, ""
    
    @staticmethod
    def validate_coordinate_value(value: Any) -> Tuple[bool, str]:
        """
        验证坐标值的有效性
        
        Args:
            value: 待验证的坐标值
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查是否为None
        if value is None:
            return False, "坐标值不能为空"
        
        # 尝试转换为浮点数
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return False, "坐标值必须是有效的数字"
        
        # 检查是否为NaN或无穷大
        if math.isnan(float_value):
            return False, "坐标值不能是NaN"
        
        if math.isinf(float_value):
            return False, "坐标值不能是无穷大"
        
        return True, ""
    
    @staticmethod
    def validate_coordinate_range(range_value: Any) -> Tuple[bool, str]:
        """
        验证坐标范围的有效性
        
        Args:
            range_value: 待验证的坐标范围值
            
        Returns:
            (是否有效, 错误信息)
        """
        # 首先验证是否为有效数字
        is_valid, error_msg = Validator.validate_coordinate_value(range_value)
        if not is_valid:
            return is_valid, error_msg
        
        float_value = float(range_value)
        
        # 检查范围是否为正数
        if float_value <= 0:
            return False, "坐标范围必须大于0"
        
        # 检查范围是否在允许的区间内
        if float_value < Validator.MIN_COORDINATE_RANGE:
            return False, f"坐标范围不能小于{Validator.MIN_COORDINATE_RANGE}"
        
        if float_value > Validator.MAX_COORDINATE_RANGE:
            return False, f"坐标范围不能大于{Validator.MAX_COORDINATE_RANGE}"
        
        return True, ""
    
    @staticmethod
    def validate_coordinate_in_range(x: float, y: float, x_range: float, y_range: float) -> Tuple[bool, str]:
        """
        验证坐标是否在指定范围内
        
        Args:
            x, y: 坐标值
            x_range, y_range: 坐标显示范围
            
        Returns:
            (是否在范围内, 错误信息)
        """
        # 检查X坐标
        if x < -x_range or x > x_range:
            return False, f"X坐标超出显示范围 (±{x_range})"
        
        # 检查Y坐标
        if y < -y_range or y > y_range:
            return False, f"Y坐标超出显示范围 (±{y_range})"
        
        return True, ""
    
    @staticmethod
    def validate_device_name_uniqueness(name: str, existing_names: List[str], 
                                      exclude_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证设备名称的唯一性
        
        Args:
            name: 待验证的设备名称
            existing_names: 已存在的设备名称列表
            exclude_name: 排除的名称（用于修改时排除自身）
            
        Returns:
            (是否唯一, 错误信息)
        """
        name = name.strip()
        
        # 创建比较列表（排除指定名称）
        compare_names = [n for n in existing_names if n != exclude_name]
        
        # 检查是否重复（忽略大小写）
        for existing_name in compare_names:
            if name.lower() == existing_name.lower():
                return False, f"设备名称 '{name}' 已存在，请使用其他名称"
        
        return True, ""
    
    @staticmethod
    def validate_canvas_size(width: Any, height: Any) -> Tuple[bool, str]:
        """
        验证Canvas尺寸的有效性
        
        Args:
            width, height: Canvas的宽度和高度
            
        Returns:
            (是否有效, 错误信息)
        """
        # 验证宽度
        try:
            width_int = int(width)
            height_int = int(height)
        except (ValueError, TypeError):
            return False, "Canvas尺寸必须是有效的整数"
        
        # 检查是否为正数
        if width_int <= 0 or height_int <= 0:
            return False, "Canvas尺寸必须大于0"
        
        # 检查是否过大（防止内存问题）
        max_size = 10000
        if width_int > max_size or height_int > max_size:
            return False, f"Canvas尺寸不能超过{max_size}像素"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        验证文件路径的有效性
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        if not file_path or not isinstance(file_path, str):
            return False, "文件路径不能为空"
        
        file_path = file_path.strip()
        
        if not file_path:
            return False, "文件路径不能为空"
        
        # 检查文件名是否包含非法字符（Windows）
        illegal_chars = r'[<>:"/\\|?*]'
        filename = file_path.split('/')[-1].split('\\')[-1]
        
        if re.search(illegal_chars, filename):
            return False, "文件名包含非法字符"
        
        # 检查文件扩展名
        if not filename.lower().endswith('.png'):
            return False, "文件必须是PNG格式"
        
        return True, ""
    
    @staticmethod
    def sanitize_device_name(name: str) -> str:
        """
        清理设备名称，移除首尾空白字符
        
        Args:
            name: 原始设备名称
            
        Returns:
            清理后的设备名称
        """
        if not isinstance(name, str):
            name = str(name)
        
        return name.strip()
    
    @staticmethod
    def sanitize_coordinate_value(value: Any) -> Optional[float]:
        """
        清理坐标值，尝试转换为有效的浮点数
        
        Args:
            value: 原始坐标值
            
        Returns:
            清理后的浮点数，如果无法转换则返回None
        """
        try:
            float_value = float(value)
            
            # 检查是否为有效数字
            if math.isnan(float_value) or math.isinf(float_value):
                return None
            
            return float_value
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_coordinate_value(value: float, decimal_places: int = 3) -> str:
        """
        格式化坐标值为指定小数位数的字符串
        
        Args:
            value: 坐标值
            decimal_places: 小数位数
            
        Returns:
            格式化后的字符串
        """
        return f"{value:.{decimal_places}f}"
    
    @staticmethod
    def validate_batch_devices(devices_data: List[dict]) -> Tuple[bool, List[str]]:
        """
        批量验证设备数据
        
        Args:
            devices_data: 设备数据列表，每个元素包含name, x, y字段
            
        Returns:
            (是否全部有效, 错误信息列表)
        """
        errors = []
        device_names = []
        
        for i, device_data in enumerate(devices_data):
            device_index = i + 1
            
            # 验证必要字段
            if 'name' not in device_data:
                errors.append(f"设备{device_index}: 缺少设备名称")
                continue
            
            if 'x' not in device_data:
                errors.append(f"设备{device_index}: 缺少X坐标")
                continue
            
            if 'y' not in device_data:
                errors.append(f"设备{device_index}: 缺少Y坐标")
                continue
            
            # 验证设备名称
            name_valid, name_error = Validator.validate_device_name(device_data['name'])
            if not name_valid:
                errors.append(f"设备{device_index}: {name_error}")
                continue
            
            # 验证坐标值
            x_valid, x_error = Validator.validate_coordinate_value(device_data['x'])
            if not x_valid:
                errors.append(f"设备{device_index}: X坐标{x_error}")
                continue
            
            y_valid, y_error = Validator.validate_coordinate_value(device_data['y'])
            if not y_valid:
                errors.append(f"设备{device_index}: Y坐标{y_error}")
                continue
            
            # 检查名称唯一性
            clean_name = Validator.sanitize_device_name(device_data['name'])
            name_unique, unique_error = Validator.validate_device_name_uniqueness(
                clean_name, device_names
            )
            if not name_unique:
                errors.append(f"设备{device_index}: {unique_error}")
                continue
            
            device_names.append(clean_name)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def is_valid_decimal_places(decimal_places: Any) -> bool:
        """
        验证小数位数是否有效
        
        Args:
            decimal_places: 小数位数
            
        Returns:
            是否有效
        """
        try:
            dp = int(decimal_places)
            return 0 <= dp <= 10  # 限制在合理范围内
        except (ValueError, TypeError):
            return False 