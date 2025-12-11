# -*- coding: utf-8 -*-
"""
坐标参考系模块

提供统一的坐标系定义与变换功能，支持世界坐标与本地坐标的双向转换。
V2.0 重构：解决坐标系概念混乱问题，提供清晰的数学变换接口。
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class CoordinateFrame:
    """
    坐标参考系
    
    表示一个坐标系，包含原点位置和可选的旋转角度。
    支持世界坐标↔本地坐标的双向转换。
    
    核心概念：
    - 世界坐标系（World Frame）：固定的全局坐标系，原点在(0,0)
    - 本地坐标系（Local Frame）：以 origin 为原点的坐标系
    
    属性:
        name: 坐标系名称（如 "world", "user"）
        origin_x: 本坐标系原点在世界坐标系中的X位置
        origin_y: 本坐标系原点在世界坐标系中的Y位置
        rotation_deg: 本坐标系相对于世界坐标系的旋转角度（度数，逆时针为正）
    """
    name: str
    origin_x: float = 0.0
    origin_y: float = 0.0
    rotation_deg: float = 0.0
    
    def __post_init__(self):
        """初始化后处理，预计算旋转参数"""
        self._update_rotation_cache()
    
    def _update_rotation_cache(self):
        """更新旋转矩阵缓存（性能优化）"""
        rad = math.radians(self.rotation_deg)
        self._cos_r = math.cos(rad)
        self._sin_r = math.sin(rad)
    
    def set_origin(self, x: float, y: float):
        """
        设置坐标系原点位置
        
        Args:
            x: 原点在世界坐标系中的X位置
            y: 原点在世界坐标系中的Y位置
        """
        self.origin_x = x
        self.origin_y = y
    
    def set_rotation(self, rotation_deg: float):
        """
        设置坐标系旋转角度
        
        Args:
            rotation_deg: 旋转角度（度数，逆时针为正）
        """
        self.rotation_deg = rotation_deg
        self._update_rotation_cache()
    
    def world_to_local(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """
        世界坐标 → 本地坐标
        
        将世界坐标系中的点转换为本坐标系中的坐标。
        
        Args:
            world_x: 世界坐标系中的X坐标
            world_y: 世界坐标系中的Y坐标
            
        Returns:
            本地坐标 (local_x, local_y)
        """
        # 先平移（将原点移至本坐标系原点）
        dx = world_x - self.origin_x
        dy = world_y - self.origin_y
        
        # 再旋转（如果有旋转角度）
        if self.rotation_deg != 0.0:
            local_x = dx * self._cos_r + dy * self._sin_r
            local_y = -dx * self._sin_r + dy * self._cos_r
            return (local_x, local_y)
        
        return (dx, dy)
    
    def local_to_world(self, local_x: float, local_y: float) -> Tuple[float, float]:
        """
        本地坐标 → 世界坐标
        
        将本坐标系中的点转换为世界坐标系中的坐标。
        
        Args:
            local_x: 本地坐标系中的X坐标
            local_y: 本地坐标系中的Y坐标
            
        Returns:
            世界坐标 (world_x, world_y)
        """
        # 先旋转（如果有旋转角度）
        if self.rotation_deg != 0.0:
            dx = local_x * self._cos_r - local_y * self._sin_r
            dy = local_x * self._sin_r + local_y * self._cos_r
        else:
            dx = local_x
            dy = local_y
        
        # 再平移（从本坐标系原点移至世界坐标系）
        world_x = dx + self.origin_x
        world_y = dy + self.origin_y
        
        return (world_x, world_y)
    
    def distance_from_origin(self, world_x: float, world_y: float) -> float:
        """
        计算点到本坐标系原点的距离
        
        Args:
            world_x: 点在世界坐标系中的X坐标
            world_y: 点在世界坐标系中的Y坐标
            
        Returns:
            点到本坐标系原点的欧几里得距离
        """
        dx = world_x - self.origin_x
        dy = world_y - self.origin_y
        return math.sqrt(dx * dx + dy * dy)
    
    def angle_from_origin(self, world_x: float, world_y: float) -> float:
        """
        计算点相对于本坐标系原点的角度
        
        从本坐标系的X轴正方向逆时针测量。
        
        Args:
            world_x: 点在世界坐标系中的X坐标
            world_y: 点在世界坐标系中的Y坐标
            
        Returns:
            角度值（度数，0-360度范围）
        """
        # 转换到本地坐标
        local_x, local_y = self.world_to_local(world_x, world_y)
        
        # 处理原点情况
        if abs(local_x) < 1e-10 and abs(local_y) < 1e-10:
            return 0.0
        
        # 计算角度
        angle_rad = math.atan2(local_y, local_x)
        angle_deg = math.degrees(angle_rad)
        
        # 归一化到 [0, 360) 范围
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    def min_angle_to_axis(self, world_x: float, world_y: float) -> float:
        """
        计算点与本坐标系轴线的最小夹角
        
        用于测量点与X轴或Y轴的夹角，取较小者。
        
        Args:
            world_x: 点在世界坐标系中的X坐标
            world_y: 点在世界坐标系中的Y坐标
            
        Returns:
            与坐标轴的最小夹角（度数，0-90度）
        """
        # 转换到本地坐标
        local_x, local_y = self.world_to_local(world_x, world_y)
        
        # 计算与X轴的夹角
        if abs(local_x) < 1e-10:
            angle_to_x_rad = math.pi / 2
        else:
            angle_to_x_rad = abs(math.atan(local_y / local_x))
        
        # 计算与Y轴的夹角
        if abs(local_y) < 1e-10:
            angle_to_y_rad = math.pi / 2
        else:
            angle_to_y_rad = abs(math.atan(local_x / local_y))
        
        # 取最小夹角并转换为度数
        min_angle_rad = min(angle_to_x_rad, angle_to_y_rad)
        return math.degrees(min_angle_rad)
    
    def is_origin(self) -> bool:
        """
        判断本坐标系是否为世界坐标系（原点在(0,0)且无旋转）
        
        Returns:
            True 如果是世界坐标系
        """
        return (abs(self.origin_x) < 1e-10 and 
                abs(self.origin_y) < 1e-10 and 
                abs(self.rotation_deg) < 1e-10)
    
    def copy(self) -> 'CoordinateFrame':
        """
        创建本坐标系的副本
        
        Returns:
            新的 CoordinateFrame 实例
        """
        return CoordinateFrame(
            name=self.name,
            origin_x=self.origin_x,
            origin_y=self.origin_y,
            rotation_deg=self.rotation_deg
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"CoordinateFrame('{self.name}', origin=({self.origin_x:.3f}, {self.origin_y:.3f}), rotation={self.rotation_deg:.1f}°)"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()


# 预定义的世界坐标系（单例模式）
WORLD_FRAME = CoordinateFrame(name="world", origin_x=0.0, origin_y=0.0, rotation_deg=0.0)


def create_user_frame(x: float, y: float, rotation_deg: float = 0.0) -> CoordinateFrame:
    """
    创建用户坐标系的工厂函数
    
    Args:
        x: 用户位置在世界坐标系中的X坐标
        y: 用户位置在世界坐标系中的Y坐标
        rotation_deg: 可选的旋转角度
        
    Returns:
        新的用户坐标系实例
    """
    return CoordinateFrame(
        name="user",
        origin_x=x,
        origin_y=y,
        rotation_deg=rotation_deg
    )

