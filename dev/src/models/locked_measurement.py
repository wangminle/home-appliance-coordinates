# -*- coding: utf-8 -*-
"""
锁定测量数据模型

用于存储"说话人方向和影响范围"的锁定扇形和连线数据
支持固定扇形后与新测量线进行夹角和距离对比
"""

import math
import uuid
from typing import Tuple, Optional, Dict, Any
from datetime import datetime


class LockedMeasurement:
    """
    锁定的测量数据模型
    
    表示一个说话人的方向（实线连线）和影响范围（扇形区域）
    支持锁定/解锁状态切换，以及与其他测量线的对比计算
    """
    
    def __init__(self):
        """初始化锁定测量模型"""
        # 唯一标识
        self.id: str = str(uuid.uuid4())[:8]
        
        # 锁定状态
        self.is_locked: bool = False
        
        # 核心数据
        self.sector_point: Optional[Tuple[float, float]] = None  # 双击点坐标
        self.center_point: Optional[Tuple[float, float]] = None  # 中心点（原点或用户位置）
        
        # 计算属性（线段）
        self.line_angle: Optional[float] = None      # 实线角度（度数，0-360）
        self.line_distance: Optional[float] = None   # 实线长度（半径）
        
        # 计算属性（扇形）
        self.sector_start_angle: Optional[float] = None  # 扇形起始角度
        self.sector_end_angle: Optional[float] = None    # 扇形结束角度
        self.sector_angle_span: float = 90.0             # 扇形角度范围（默认90度）
        
        # 图钉位置
        self.pin_position: Optional[Tuple[float, float]] = None
        
        # 元数据
        self.created_time: Optional[datetime] = None
        self.locked_time: Optional[datetime] = None
    
    def set_measurement(self, sector_point: Tuple[float, float], 
                       center_point: Tuple[float, float],
                       sector_angle_span: float = 90.0) -> None:
        """
        设置测量数据
        
        Args:
            sector_point: 双击点坐标 (x, y)
            center_point: 中心点坐标（原点或用户位置）
            sector_angle_span: 扇形角度范围（默认90度）
        """
        self.sector_point = sector_point
        self.center_point = center_point
        self.sector_angle_span = sector_angle_span
        
        # 计算线段属性
        self.line_distance = self._calculate_distance(center_point, sector_point)
        self.line_angle = self._calculate_angle(center_point, sector_point)
        
        # 计算扇形角度（以连线为平分线，向两侧各展开 angle_span/2）
        half_span = sector_angle_span / 2.0
        self.sector_start_angle = self.line_angle - half_span
        self.sector_end_angle = self.line_angle + half_span
        
        # 设置图钉位置（双击点正上方0.8个单位）
        self.pin_position = (sector_point[0], sector_point[1] + 0.8)
        
        # 记录创建时间
        self.created_time = datetime.now()
    
    def lock(self) -> None:
        """锁定当前测量"""
        self.is_locked = True
        self.locked_time = datetime.now()
    
    def unlock(self) -> None:
        """解锁测量"""
        self.is_locked = False
        self.locked_time = None
    
    def toggle_lock(self) -> bool:
        """
        切换锁定状态
        
        Returns:
            新的锁定状态（True=已锁定，False=已解锁）
        """
        if self.is_locked:
            self.unlock()
        else:
            self.lock()
        return self.is_locked
    
    def clear(self) -> None:
        """清除所有测量数据"""
        self.is_locked = False
        self.sector_point = None
        self.center_point = None
        self.line_angle = None
        self.line_distance = None
        self.sector_start_angle = None
        self.sector_end_angle = None
        self.pin_position = None
        self.created_time = None
        self.locked_time = None
    
    def has_data(self) -> bool:
        """检查是否有有效的测量数据"""
        return self.sector_point is not None and self.center_point is not None
    
    def calculate_comparison(self, new_point: Tuple[float, float]) -> Dict[str, float]:
        """
        计算新测量点与锁定线段的对比数据
        
        Args:
            new_point: 新的测量点坐标 (x, y)
            
        Returns:
            包含夹角和距离的字典：
            - angle_diff: 两条线段的夹角（0-180度）
            - new_distance: 新点到中心点的距离
            - point_distance: 新点到锁定点的距离（可选）
        """
        if not self.has_data() or self.center_point is None:
            return {'angle_diff': 0.0, 'new_distance': 0.0, 'point_distance': 0.0}
        
        # 计算新线段的角度和距离
        new_angle = self._calculate_angle(self.center_point, new_point)
        new_distance = self._calculate_distance(self.center_point, new_point)
        
        # 计算夹角（取0-180度的最小夹角）
        angle_diff = abs(new_angle - self.line_angle) if self.line_angle else 0.0
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # 计算两个端点之间的距离（可选信息）
        point_distance = self._calculate_distance(self.sector_point, new_point) if self.sector_point else 0.0
        
        return {
            'angle_diff': angle_diff,
            'new_distance': new_distance,
            'new_angle': new_angle,
            'point_distance': point_distance
        }
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """计算两点之间的欧几里得距离"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _calculate_angle(self, from_point: Tuple[float, float], 
                        to_point: Tuple[float, float]) -> float:
        """
        计算从起点到终点的角度（相对于X轴正方向，逆时针为正）
        
        Returns:
            角度值（度数，0-360）
        """
        dx = to_point[0] - from_point[0]
        dy = to_point[1] - from_point[1]
        
        if dx == 0 and dy == 0:
            return 0.0
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 确保角度在0-360度范围内
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将锁定测量数据转换为字典（用于项目保存）
        
        Returns:
            包含所有属性的字典
        """
        return {
            'id': self.id,
            'is_locked': self.is_locked,
            'sector_point': list(self.sector_point) if self.sector_point else None,
            'center_point': list(self.center_point) if self.center_point else None,
            'line_angle': self.line_angle,
            'line_distance': self.line_distance,
            'sector_start_angle': self.sector_start_angle,
            'sector_end_angle': self.sector_end_angle,
            'sector_angle_span': self.sector_angle_span,
            'pin_position': list(self.pin_position) if self.pin_position else None,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'locked_time': self.locked_time.isoformat() if self.locked_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LockedMeasurement':
        """
        从字典创建锁定测量对象（用于项目加载）
        
        Args:
            data: 包含属性的字典
            
        Returns:
            LockedMeasurement实例
        """
        obj = cls()
        
        obj.id = data.get('id', str(uuid.uuid4())[:8])
        obj.is_locked = data.get('is_locked', False)
        
        # 恢复坐标数据
        sector_point = data.get('sector_point')
        obj.sector_point = tuple(sector_point) if sector_point else None
        
        center_point = data.get('center_point')
        obj.center_point = tuple(center_point) if center_point else None
        
        # 恢复计算属性
        obj.line_angle = data.get('line_angle')
        obj.line_distance = data.get('line_distance')
        obj.sector_start_angle = data.get('sector_start_angle')
        obj.sector_end_angle = data.get('sector_end_angle')
        obj.sector_angle_span = data.get('sector_angle_span', 90.0)
        
        # 恢复图钉位置
        pin_position = data.get('pin_position')
        obj.pin_position = tuple(pin_position) if pin_position else None
        
        # 恢复时间戳
        created_time_str = data.get('created_time')
        if created_time_str:
            obj.created_time = datetime.fromisoformat(created_time_str)
        
        locked_time_str = data.get('locked_time')
        if locked_time_str:
            obj.locked_time = datetime.fromisoformat(locked_time_str)
        
        return obj
    
    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        status = "🔒锁定" if self.is_locked else "🔓解锁"
        if self.sector_point:
            return f"LockedMeasurement({status}, 点={self.sector_point}, 角度={self.line_angle:.1f}°)"
        return f"LockedMeasurement({status}, 无数据)"
