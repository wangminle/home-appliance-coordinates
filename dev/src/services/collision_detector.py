# -*- coding: utf-8 -*-
"""
碰撞检测服务

提供边界框碰撞检测、扇形区域检测等功能。
V2.0 第二期重构新增模块。

设计原则：
1. 纯函数式设计 - 无状态，相同输入产生相同输出
2. 高性能 - 使用简单高效的几何计算
3. 可测试 - 所有方法都是独立可测试的
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """
    边界框数据类
    
    用于表示矩形区域，支持碰撞检测和空间计算。
    
    属性:
        x_min: 左边界X坐标
        y_min: 下边界Y坐标
        x_max: 右边界X坐标
        y_max: 上边界Y坐标
    """
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    
    def center(self) -> Tuple[float, float]:
        """获取边界框中心点"""
        return (
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2
        )
    
    def width(self) -> float:
        """获取宽度"""
        return self.x_max - self.x_min
    
    def height(self) -> float:
        """获取高度"""
        return self.y_max - self.y_min
    
    def area(self) -> float:
        """计算面积"""
        return self.width() * self.height()
    
    def expand(self, margin: float) -> 'BoundingBox':
        """
        扩展边界框（向外扩展指定边距）
        
        Args:
            margin: 扩展边距
            
        Returns:
            新的扩展后的边界框
        """
        return BoundingBox(
            x_min=self.x_min - margin,
            y_min=self.y_min - margin,
            x_max=self.x_max + margin,
            y_max=self.y_max + margin
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        检查点是否在边界框内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            True 如果点在边界框内或边上
        """
        return (self.x_min <= x <= self.x_max and 
                self.y_min <= y <= self.y_max)
    
    @staticmethod
    def from_center(center_x: float, center_y: float, 
                   width: float, height: float) -> 'BoundingBox':
        """
        从中心点和尺寸创建边界框
        
        Args:
            center_x: 中心点X坐标
            center_y: 中心点Y坐标
            width: 宽度
            height: 高度
            
        Returns:
            新的边界框实例
        """
        half_w = width / 2
        half_h = height / 2
        return BoundingBox(
            x_min=center_x - half_w,
            y_min=center_y - half_h,
            x_max=center_x + half_w,
            y_max=center_y + half_h
        )


class CollisionDetector:
    """
    碰撞检测服务
    
    提供各种碰撞检测功能：
    - 边界框与边界框
    - 边界框与画布边界
    - 点与扇形区域
    """
    
    @staticmethod
    def boxes_overlap(box1: BoundingBox, box2: BoundingBox, 
                      margin: float = 0.0) -> bool:
        """
        检查两个边界框是否重叠
        
        Args:
            box1: 第一个边界框
            box2: 第二个边界框
            margin: 额外间距（正值表示需要更大间隔）
            
        Returns:
            True 如果两个边界框重叠（或间距小于margin）
        """
        return not (
            box1.x_max + margin <= box2.x_min or
            box2.x_max + margin <= box1.x_min or
            box1.y_max + margin <= box2.y_min or
            box2.y_max + margin <= box1.y_min
        )
    
    @staticmethod
    def overlaps_any(box: BoundingBox, boxes: List[BoundingBox], 
                    margin: float = 0.0) -> bool:
        """
        检查边界框是否与列表中任何一个重叠
        
        Args:
            box: 要检查的边界框
            boxes: 边界框列表
            margin: 额外间距
            
        Returns:
            True 如果与任何边界框重叠
        """
        return any(
            CollisionDetector.boxes_overlap(box, other, margin) 
            for other in boxes
        )
    
    @staticmethod
    def is_within_bounds(box: BoundingBox, bounds: BoundingBox, 
                        margin: float = 0.0) -> bool:
        """
        检查边界框是否完全在指定范围内
        
        Args:
            box: 要检查的边界框
            bounds: 范围边界框
            margin: 内边距（要求离边界的最小距离）
            
        Returns:
            True 如果完全在范围内（考虑内边距）
        """
        return (
            box.x_min >= bounds.x_min + margin and
            box.x_max <= bounds.x_max - margin and
            box.y_min >= bounds.y_min + margin and
            box.y_max <= bounds.y_max - margin
        )
    
    @staticmethod
    def point_in_sector(x: float, y: float,
                       center_x: float, center_y: float,
                       radius: float,
                       start_angle_deg: float,
                       end_angle_deg: float) -> bool:
        """
        检查点是否在扇形区域内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            center_x: 扇形圆心X坐标
            center_y: 扇形圆心Y坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数，从X轴正向逆时针）
            end_angle_deg: 结束角度（度数）
            
        Returns:
            True 如果点在扇形内
        """
        # 计算点到圆心的距离
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 超出半径范围
        if distance > radius:
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
        start = start_angle_deg % 360
        end = end_angle_deg % 360
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
    
    @staticmethod
    def box_intersects_sector(box: BoundingBox,
                             center_x: float, center_y: float,
                             radius: float,
                             start_angle_deg: float,
                             end_angle_deg: float) -> bool:
        """
        检查边界框是否与扇形区域有交集
        
        采用保守检测：检查边界框的中心和四个角点
        
        Args:
            box: 边界框
            center_x: 扇形圆心X坐标
            center_y: 扇形圆心Y坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
            
        Returns:
            True 如果边界框与扇形有交集
        """
        # 获取要检测的关键点
        cx, cy = box.center()
        corners = [
            (box.x_min, box.y_min),  # 左下
            (box.x_max, box.y_min),  # 右下
            (box.x_min, box.y_max),  # 左上
            (box.x_max, box.y_max),  # 右上
        ]
        
        # 检查中心点
        if CollisionDetector.point_in_sector(
            cx, cy, center_x, center_y, radius, start_angle_deg, end_angle_deg
        ):
            return True
        
        # 检查四个角点
        for corner_x, corner_y in corners:
            if CollisionDetector.point_in_sector(
                corner_x, corner_y, center_x, center_y, 
                radius, start_angle_deg, end_angle_deg
            ):
                return True
        
        return False
    
    @staticmethod
    def distance_between_boxes(box1: BoundingBox, box2: BoundingBox) -> float:
        """
        计算两个边界框之间的最短距离
        
        如果重叠，返回负值（负的最大重叠距离）
        
        Args:
            box1: 第一个边界框
            box2: 第二个边界框
            
        Returns:
            最短距离（重叠时为负值）
        """
        # 计算X方向的间距
        if box1.x_max < box2.x_min:
            dx = box2.x_min - box1.x_max
        elif box2.x_max < box1.x_min:
            dx = box1.x_min - box2.x_max
        else:
            dx = 0  # X方向重叠
        
        # 计算Y方向的间距
        if box1.y_max < box2.y_min:
            dy = box2.y_min - box1.y_max
        elif box2.y_max < box1.y_min:
            dy = box1.y_min - box2.y_max
        else:
            dy = 0  # Y方向重叠
        
        if dx == 0 and dy == 0:
            # 两个框重叠，计算重叠深度
            overlap_x = min(box1.x_max, box2.x_max) - max(box1.x_min, box2.x_min)
            overlap_y = min(box1.y_max, box2.y_max) - max(box1.y_min, box2.y_min)
            return -min(overlap_x, overlap_y)  # 返回负值表示重叠
        
        return math.sqrt(dx * dx + dy * dy)

