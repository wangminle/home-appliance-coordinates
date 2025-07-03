# -*- coding: utf-8 -*-
"""
测量点数据模型

定义交互式测量点的数据结构和计算功能
"""

import math
from typing import Tuple, Optional


class MeasurementPoint:
    """
    测量点模型类
    
    表示用户在Canvas上点击创建的测量点，包含位置信息和计算数据
    """
    
    def __init__(self, x: float, y: float):
        """
        初始化测量点
        
        Args:
            x: 测量点X坐标
            y: 测量点Y坐标
        """
        self.x = float(x)
        self.y = float(y)
        
        # 自动计算相关属性
        self.distance_to_origin = self._calculate_distance_to_origin()
        self.angle_to_axis = self._calculate_min_angle_to_axis()
        
        # 验证数据有效性
        self._validate()
    
    def _validate(self):
        """
        验证测量点数据的有效性
        
        Raises:
            ValueError: 当数据不符合要求时抛出异常
        """
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise ValueError("坐标值必须是数字类型")
        
        if math.isnan(self.x) or math.isnan(self.y):
            raise ValueError("坐标值不能是NaN")
        
        if math.isinf(self.x) or math.isinf(self.y):
            raise ValueError("坐标值不能是无穷大")
    
    def _calculate_distance_to_origin(self) -> float:
        """
        计算到坐标原点的欧几里得距离
        
        Returns:
            到原点(0,0)的距离
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def _calculate_min_angle_to_axis(self) -> float:
        """
        计算与坐标轴的最小夹角
        
        使用与参考HTML相同的算法：计算点与X轴和Y轴的夹角，取较小值
        
        Returns:
            与坐标轴的最小夹角（度数，0-90度）
        """
        # 计算与X轴的夹角
        if self.x == 0:
            angle_to_x_rad = math.pi / 2
        else:
            angle_to_x_rad = abs(math.atan(self.y / self.x))
        
        # 计算与Y轴的夹角
        if self.y == 0:
            angle_to_y_rad = math.pi / 2
        else:
            angle_to_y_rad = abs(math.atan(self.x / self.y))
        
        # 取最小夹角并转换为度数
        min_angle_rad = min(angle_to_x_rad, angle_to_y_rad)
        return min_angle_rad * 180 / math.pi
    
    def update_position(self, x: float, y: float):
        """
        更新测量点位置并重新计算相关数据
        
        Args:
            x: 新的X坐标
            y: 新的Y坐标
        """
        self.x = float(x)
        self.y = float(y)
        
        # 重新计算距离和角度
        self.distance_to_origin = self._calculate_distance_to_origin()
        self.angle_to_axis = self._calculate_min_angle_to_axis()
        
        # 验证新数据
        self._validate()
    
    def distance_to_point(self, x: float, y: float) -> float:
        """
        计算到指定点的距离
        
        Args:
            x: 目标点X坐标
            y: 目标点Y坐标
            
        Returns:
            到目标点的欧几里得距离
        """
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
    
    def angle_to_point(self, x: float, y: float) -> float:
        """
        计算到指定点的角度（从X轴正方向逆时针测量）
        
        Args:
            x: 目标点X坐标
            y: 目标点Y坐标
            
        Returns:
            角度值（度数，0-360度）
        """
        dx = x - self.x
        dy = y - self.y
        
        if dx == 0 and dy == 0:
            return 0.0
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 确保角度在0-360度范围内
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    def is_in_quadrant(self, quadrant: int) -> bool:
        """
        判断测量点是否在指定象限
        
        Args:
            quadrant: 象限编号 (1-4)
            
        Returns:
            True如果在指定象限，否则False
        """
        if quadrant == 1:
            return self.x > 0 and self.y > 0
        elif quadrant == 2:
            return self.x < 0 and self.y > 0
        elif quadrant == 3:
            return self.x < 0 and self.y < 0
        elif quadrant == 4:
            return self.x > 0 and self.y < 0
        else:
            raise ValueError("象限编号必须是1-4")
    
    def get_formatted_info(self, decimal_places: int = 3) -> dict:
        """
        获取格式化的测量信息
        
        Args:
            decimal_places: 小数位数，默认3位
            
        Returns:
            包含格式化信息的字典
        """
        return {
            'coordinates': f"坐标: X: {self.x:.{decimal_places}f}, Y: {self.y:.{decimal_places}f}",
            'distance': f"距离: {self.distance_to_origin:.{decimal_places}f}",
            'angle': f"角度: {self.angle_to_axis:.{decimal_places}f}°"
        }
    
    def get_info_lines(self, decimal_places: int = 3) -> list:
        """
        获取测量信息的文本行列表（用于显示）
        
        Args:
            decimal_places: 小数位数，默认3位
            
        Returns:
            信息文本行列表
        """
        info = self.get_formatted_info(decimal_places)
        return [info['coordinates'], info['distance'], info['angle']]
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            包含测量点所有信息的字典
        """
        return {
            'x': self.x,
            'y': self.y,
            'distance_to_origin': self.distance_to_origin,
            'angle_to_axis': self.angle_to_axis
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeasurementPoint':
        """
        从字典创建测量点实例
        
        Args:
            data: 包含测量点信息的字典
            
        Returns:
            MeasurementPoint实例
        """
        return cls(data['x'], data['y'])
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MeasurementPoint(x={self.x:.3f}, y={self.y:.3f})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"MeasurementPoint(x={self.x:.3f}, y={self.y:.3f}, "
                f"distance={self.distance_to_origin:.3f}, "
                f"angle={self.angle_to_axis:.3f}°)")
    
    def __eq__(self, other) -> bool:
        """判断测量点是否相等（基于坐标）"""
        if not isinstance(other, MeasurementPoint):
            return False
        return (abs(self.x - other.x) < 1e-6 and 
                abs(self.y - other.y) < 1e-6) 