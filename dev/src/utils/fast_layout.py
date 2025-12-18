# -*- coding: utf-8 -*-
"""
高性能原生布局管理器 V2.0

增强版标注避让方案，专门针对家居设备坐标绘制场景优化
核心改进：
1. 扇形斥力场 - 标签进入扇形区域会被强力弹开
2. 模拟退火扰动 - 避免陷入局部最优解
3. 分层计算 - 按优先级依次处理不同类型的标签
"""

from enum import Enum
from typing import List, Tuple, Optional, Dict
import math
import time
import random


# ==================== 布局算法常量定义 ====================

class LayoutConstants:
    """
    布局算法常量定义
    
    将魔法数字提取为命名常量，便于理解和维护
    """
    
    # ---------- 几何阈值常量 ----------
    NEAR_ZERO_THRESHOLD = 0.01          # 判断是否在圆心/原点附近的阈值
    FLOAT_TOLERANCE = 0.01              # 浮点数比较容差
    
    # ---------- 扇形斥力场参数 ----------
    SECTOR_CENTER_REPULSION = 20.0      # 圆心处斥力强度（随机方向弹开）
    SECTOR_BASE_REPULSION = 15.0        # 扇形内基础斥力强度
    SECTOR_PENETRATION_FACTOR = 30.0    # 扇形内渗透斥力增强系数
    SECTOR_WARNING_MARGIN = 1.0         # 扇形边界警戒距离
    SECTOR_BOUNDARY_REPULSION = 8.0     # 扇形边界斥力强度
    SECTOR_PENALTY_PENETRATION_FACTOR = 2.0  # 扇形惩罚渗透增强系数
    SECTOR_MARGIN_PENALTY_FACTOR = 0.5  # 扇形边界惩罚系数
    
    # ---------- 距离惩罚参数 ----------
    # 正常情况下的距离惩罚阈值和系数
    DISTANCE_FAR_THRESHOLD = 1.8        # 远距离阈值
    DISTANCE_FAR_PENALTY = 50.0         # 远距离惩罚系数
    DISTANCE_MID_THRESHOLD = 1.5        # 中距离阈值
    DISTANCE_MID_PENALTY = 15.0         # 中距离惩罚系数
    DISTANCE_NEAR_THRESHOLD = 1.2       # 近距离阈值
    DISTANCE_NEAR_PENALTY = 3.0         # 近距离惩罚系数
    # 扇形区域内的距离惩罚（放宽）
    SECTOR_DISTANCE_THRESHOLD = 2.5     # 扇形区域距离阈值
    SECTOR_DISTANCE_PENALTY = 20.0      # 扇形区域距离惩罚系数
    
    # ---------- 边界惩罚参数 ----------
    CANVAS_MARGIN = 0.5                 # 画布边界余量
    BOUNDARY_START_RATIO = 0.6          # 边界惩罚起始比例（距中心60%开始惩罚）
    BOUNDARY_PENALTY_MULTIPLIER = 2     # 边界惩罚倍数
    
    # ---------- 间距和重叠参数 ----------
    SPACING_MULTIPLIER = 3              # 间距检测倍数
    SPACING_PENALTY = 2.0               # 间距不足惩罚系数
    
    # ---------- 力导向布局参数 ----------
    REPULSION_STRENGTH = 0.3            # 元素间排斥力强度
    ANCHOR_ATTRACTION = 0.2             # 锚点吸引力强度
    DAMPING = 0.85                      # 阻尼系数
    OVERLAP_REPULSION_MULTIPLIER = 3.0  # 重叠时排斥力倍数
    MIN_DISTANCE_CLAMP = 0.1            # 最小距离钳制值（防除零）
    PROXIMITY_THRESHOLD = 2.0           # 接近距离阈值
    PROXIMITY_REPULSION_FACTOR = 0.5    # 接近时排斥力系数
    ANCHOR_TRIGGER_DISTANCE = 0.5       # 触发锚点吸引的距离阈值
    SECTOR_ATTRACTION_REDUCTION = 0.3   # 扇形内吸引力减弱系数
    
    # ---------- 模拟退火参数 ----------
    TEMPERATURE_THRESHOLD_MULTIPLIER = 2    # 温度阈值倍数（控制扰动触发）
    PERTURBATION_STRENGTH = 0.3             # 扰动强度系数
    BASE_MAX_MOVE = 0.5                     # 基础最大移动距离
    TEMPERATURE_MOVE_FACTOR = 0.3           # 温度对移动的影响系数
    CONVERGENCE_TEMP_MULTIPLIER = 3         # 收敛判断温度倍数
    CONVERGENCE_MOVEMENT_THRESHOLD = 0.01   # 收敛判断移动阈值
    
    # ---------- 默认位置参数 ----------
    DEFAULT_OFFSET_X = 1.2              # 默认X偏移量
    DEFAULT_OFFSET_Y = 0.8              # 默认Y偏移量
    POSITION_CHANGE_LOG_THRESHOLD = 0.3 # 位置变化日志阈值

class ElementType(Enum):
    """元素类型枚举"""
    DEVICE_INFO = "device_info"
    MEASUREMENT_INFO = "measurement_info"
    USER_POSITION = "user_position"
    COORDINATE_INFO = "coordinate_info"
    SECTOR = "sector"
    MEASUREMENT_LINE = "measurement_line"


class SectorRegion:
    """
    扇形区域类 - 用于扇形斥力场计算
    """
    def __init__(self, center_x: float, center_y: float, radius: float,
                 start_angle_deg: float, end_angle_deg: float):
        """
        初始化扇形区域
        
        Args:
            center_x: 扇形圆心X坐标
            center_y: 扇形圆心Y坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数，从X轴正向逆时针）
            end_angle_deg: 结束角度（度数）
        """
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.start_angle_deg = start_angle_deg
        self.end_angle_deg = end_angle_deg
        
        # 转换为弧度
        self.start_angle_rad = math.radians(start_angle_deg)
        self.end_angle_rad = math.radians(end_angle_deg)
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        检查点是否在扇形内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            True如果点在扇形内
        """
        # 计算点到圆心的距离
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 超出半径范围
        if distance > self.radius:
            return False
        
        # 🆕 特殊情况：圆心点始终在扇形内
        if distance < LayoutConstants.NEAR_ZERO_THRESHOLD:
            return True
        
        # 计算点相对于圆心的角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 归一化角度到 [0, 360) 范围
        while angle_deg < 0:
            angle_deg += 360
        while angle_deg >= 360:
            angle_deg -= 360
        
        # 归一化起始和结束角度到 [0, 360) 范围
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
    
    def get_repulsion_force(self, x: float, y: float) -> Tuple[float, float]:
        """
        计算扇形对点的斥力 - 增强版
        
        如果点在扇形内或靠近扇形边界，施加沿径向向外的强斥力
        确保标签被强力弹出扇形区域
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            斥力向量 (force_x, force_y)
        """
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < LayoutConstants.NEAR_ZERO_THRESHOLD:
            # 在圆心附近，向随机方向弹开
            angle = random.random() * 2 * math.pi
            return (math.cos(angle) * LayoutConstants.SECTOR_CENTER_REPULSION, 
                    math.sin(angle) * LayoutConstants.SECTOR_CENTER_REPULSION)
        
        # 归一化方向向量（指向外部）
        dir_x = dx / distance
        dir_y = dy / distance
        
        # 计算斥力强度
        force_strength = 0.0
        
        if self.contains_point(x, y):
            # 🆕 在扇形内：超强斥力，确保标签被弹出
            penetration_ratio = 1.0 - (distance / self.radius)
            force_strength = (LayoutConstants.SECTOR_BASE_REPULSION + 
                            penetration_ratio * LayoutConstants.SECTOR_PENETRATION_FACTOR)
        else:
            # 在扇形外但靠近边界：中等斥力
            margin = LayoutConstants.SECTOR_WARNING_MARGIN
            if distance < self.radius + margin:
                closeness = 1.0 - ((distance - self.radius) / margin) if distance > self.radius else 1.0
                force_strength = closeness * LayoutConstants.SECTOR_BOUNDARY_REPULSION
        
        return (dir_x * force_strength, dir_y * force_strength)

class BoundingBox:
    """边界框类"""
    def __init__(self, x_min: float, y_min: float, x_max: float, y_max: float):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
    
    def overlaps(self, other: 'BoundingBox') -> bool:
        """检查是否与另一个边界框重叠"""
        return not (self.x_max <= other.x_min or 
                   other.x_max <= self.x_min or
                   self.y_max <= other.y_min or 
                   other.y_max <= self.y_min)
    
    def overlap_area(self, other: 'BoundingBox') -> float:
        """计算与另一个边界框的重叠面积"""
        if not self.overlaps(other):
            return 0.0
        
        overlap_width = min(self.x_max, other.x_max) - max(self.x_min, other.x_min)
        overlap_height = min(self.y_max, other.y_max) - max(self.y_min, other.y_min)
        return overlap_width * overlap_height
    
    def distance_to(self, other: 'BoundingBox') -> float:
        """计算到另一个边界框的最短距离"""
        if self.overlaps(other):
            return 0.0
        
        dx = max(0, max(self.x_min - other.x_max, other.x_min - self.x_max))
        dy = max(0, max(self.y_min - other.y_max, other.y_min - self.y_max))
        return math.sqrt(dx*dx + dy*dy)
    
    def center(self) -> Tuple[float, float]:
        """获取边界框中心点"""
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)
    
    def area(self) -> float:
        """计算边界框面积"""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)

class LayoutElement:
    """布局元素类"""
    def __init__(self, element_type: ElementType, bounding_box: BoundingBox, 
                 anchor_point: Tuple[float, float], priority: int = 5, 
                 movable: bool = True, element_id: str = "", static: bool = False):
        self.element_type = element_type
        self.bounding_box = bounding_box
        self.anchor_point = anchor_point
        self.priority = priority
        self.movable = movable
        self.element_id = element_id
        self.static = static  # 是否为静态元素（不会被清除动态元素时移除）
        self.creation_time = time.time()
        
        # 当前位置（用于力导向布局计算）
        self.current_x = (bounding_box.x_min + bounding_box.x_max) / 2
        self.current_y = (bounding_box.y_min + bounding_box.y_max) / 2

class FastLayoutManager:
    """
    高性能原生布局管理器 V2.1
    
    专门为家居设备坐标绘制场景优化的布局算法
    核心改进：扇形斥力场、模拟退火扰动、分层计算
    新增特性：12方向约束布局 - 设备标签只能出现在以设备点为圆心的12个方向（每30°一个）
    """
    
    def __init__(self, canvas_bounds: Tuple[float, float, float, float]):
        """
        初始化布局管理器
        
        Args:
            canvas_bounds: 画布边界 (x_min, y_min, x_max, y_max)
        """
        self.canvas_bounds = BoundingBox(*canvas_bounds)
        self.elements: List[LayoutElement] = []
        
        # 🆕 扇形斥力场管理
        self.sector_regions: List[SectorRegion] = []
        
        # 性能优化：缓存机制
        self._position_cache: Dict[str, Tuple[float, float]] = {}
        self._cache_valid = True
        
        # 信息框尺寸配置（V2.2 更新：适应多行格式）
        self.info_box_sizes = {
            ElementType.DEVICE_INFO: (2.0, 1.2),      # 设备信息框（增加高度适应多行）
            ElementType.MEASUREMENT_INFO: (2.6, 1.4), # 测量信息框  
            ElementType.COORDINATE_INFO: (2.3, 1.0),  # 坐标信息框
            ElementType.USER_POSITION: (1.5, 0.7),    # 用户位置标记
        }
        
        # 🆕 12方向约束配置（每30°一个方向）
        self.direction_count = 12  # 12个方向
        self.direction_angle_step = 30  # 每个方向间隔30度
        self.max_label_distance = 3.0  # 标签最近顶点到设备点的最大距离
        self.min_label_distance = 0.8  # 标签最近顶点到设备点的最小距离
        
        # 高性能避让偏移量配置（预计算）- 🆕 增加更多候选位置
        self.primary_offsets = [
            (1.2, 0.8),   # 右上（主要位置）
            (-1.2, 0.8),  # 左上
            (1.2, -0.8),  # 右下
            (-1.2, -0.8), # 左下
        ]
        
        self.secondary_offsets = [
            (1.8, 0),     # 右中
            (-1.8, 0),    # 左中
            (0, 1.2),     # 上中
            (0, -1.2),    # 下中
        ]
        
        # 🆕 扩展候选位置（用于扇形避让时的更多选择）
        self.extended_offsets = [
            (2.2, 1.2),   # 远右上
            (-2.2, 1.2),  # 远左上
            (2.2, -1.2),  # 远右下
            (-2.2, -1.2), # 远左下
            (2.5, 0.5),   # 远右
            (-2.5, 0.5),  # 远左
        ]
        
        # 布局质量阈值
        self.min_spacing = 0.15  # 最小间距
        self.overlap_penalty = 100.0  # 重叠惩罚系数
        self.boundary_penalty = 10.0  # 边界惩罚系数
        self.sector_penalty = 1000.0   # 🆕 扇形区域惩罚系数（大幅增强，确保标签绝对避开扇形）
        
        # 🆕 模拟退火参数
        self.initial_temperature = 1.0  # 初始温度
        self.cooling_rate = 0.95        # 冷却速率
        self.min_temperature = 0.01     # 最小温度
    
    def clear_elements(self):
        """清除所有元素"""
        self.elements.clear()
        self._invalidate_cache()
    
    def clear_dynamic_elements(self):
        """清除所有动态元素（保留静态元素如扇形等障碍物）"""
        original_count = len(self.elements)
        self.elements = [e for e in self.elements if e.static]
        if len(self.elements) != original_count:
            self._invalidate_cache()
    
    def add_element(self, element: LayoutElement):
        """添加布局元素"""
        self.elements.append(element)
        self._invalidate_cache()
    
    def remove_element_by_type(self, element_type: ElementType):
        """根据类型移除元素"""
        original_count = len(self.elements)
        self.elements = [e for e in self.elements if e.element_type != element_type]
        if len(self.elements) != original_count:
            self._invalidate_cache()
    
    def remove_element_by_id(self, element_id: str):
        """根据ID移除元素"""
        original_count = len(self.elements)
        self.elements = [e for e in self.elements if e.element_id != element_id]
        if len(self.elements) != original_count:
            self._invalidate_cache()
    
    # ==================== 🆕 扇形斥力场管理 ====================
    
    def add_sector_region(self, center_x: float, center_y: float, radius: float,
                         start_angle_deg: float, end_angle_deg: float):
        """
        添加扇形斥力场区域
        
        Args:
            center_x: 扇形圆心X坐标
            center_y: 扇形圆心Y坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
        """
        sector = SectorRegion(center_x, center_y, radius, start_angle_deg, end_angle_deg)
        self.sector_regions.append(sector)
        self._invalidate_cache()
        print(f"🔺 添加扇形斥力场: 圆心({center_x:.2f}, {center_y:.2f}), 半径{radius:.2f}, 角度[{start_angle_deg:.1f}°, {end_angle_deg:.1f}°]")
    
    def clear_sector_regions(self):
        """清除所有扇形斥力场"""
        if self.sector_regions:
            self.sector_regions.clear()
            self._invalidate_cache()
            print("🔺 已清除所有扇形斥力场")
    
    def _is_box_in_sector(self, box: BoundingBox) -> bool:
        """
        检查边界框是否与任何扇形区域重叠
        
        Args:
            box: 要检查的边界框
            
        Returns:
            True如果边界框的任何角点或中心在扇形内
        """
        if not self.sector_regions:
            return False
        
        # 获取边界框的中心和四个角点
        center_x, center_y = box.center()
        corners = [
            (box.x_min, box.y_min),  # 左下
            (box.x_max, box.y_min),  # 右下
            (box.x_min, box.y_max),  # 左上
            (box.x_max, box.y_max),  # 右上
        ]
        
        # 检查所有点是否在任何扇形内
        for sector in self.sector_regions:
            # 检查中心点
            if sector.contains_point(center_x, center_y):
                return True
            # 检查四个角点
            for cx, cy in corners:
                if sector.contains_point(cx, cy):
                    return True
        
        return False
    
    def _calculate_sector_penalty(self, x: float, y: float) -> float:
        """
        计算点在所有扇形斥力场中的惩罚值
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            惩罚值（越高越差）
        """
        total_penalty = 0.0
        
        for sector in self.sector_regions:
            if sector.contains_point(x, y):
                # 在扇形内：极高惩罚（确保不会被选中）
                dx = x - sector.center_x
                dy = y - sector.center_y
                distance = math.sqrt(dx*dx + dy*dy)
                penetration_ratio = 1.0 - (distance / sector.radius) if sector.radius > 0 else 1.0
                total_penalty += self.sector_penalty * (1.0 + penetration_ratio * LayoutConstants.SECTOR_PENALTY_PENETRATION_FACTOR)
            else:
                # 在扇形外：检查边界距离，给予警戒区惩罚
                dx = x - sector.center_x
                dy = y - sector.center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 扩大警戒距离
                warning_margin = LayoutConstants.SECTOR_WARNING_MARGIN
                if distance < sector.radius + warning_margin:  # 靠近扇形边界
                    margin_penalty = ((sector.radius + warning_margin - distance) * 
                                     self.sector_penalty * LayoutConstants.SECTOR_MARGIN_PENALTY_FACTOR)
                    total_penalty += margin_penalty
        
        return total_penalty
    
    def _get_sector_repulsion_force(self, x: float, y: float) -> Tuple[float, float]:
        """
        计算所有扇形对点的总斥力
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            总斥力向量 (force_x, force_y)
        """
        total_force_x = 0.0
        total_force_y = 0.0
        
        for sector in self.sector_regions:
            force_x, force_y = sector.get_repulsion_force(x, y)
            total_force_x += force_x
            total_force_y += force_y
        
        return (total_force_x, total_force_y)
    
    def _invalidate_cache(self):
        """使缓存失效"""
        self._position_cache.clear()
        self._cache_valid = False
    
    # ==================== 🆕 12方向约束布局系统 ====================
    
    def _generate_12_direction_candidates(self, anchor_x: float, anchor_y: float,
                                         box_width: float, box_height: float) -> List[Tuple[float, float, int]]:
        """
        生成12方向约束的候选位置
        
        标签的四个顶点中，离设备点最近的顶点必须位于12个方向之一（每30°）
        同时满足距离约束（0.8 ≤ 距离 ≤ 3.0）
        
        Args:
            anchor_x: 设备点X坐标
            anchor_y: 设备点Y坐标
            box_width: 标签框宽度
            box_height: 标签框高度
            
        Returns:
            候选位置列表 [(center_x, center_y, direction_index), ...]
        """
        candidates = []
        
        # 12个方向：0°, 30°, 60°, 90°, 120°, 150°, 180°, 210°, 240°, 270°, 300°, 330°
        for direction_idx in range(self.direction_count):
            angle_deg = direction_idx * self.direction_angle_step
            angle_rad = math.radians(angle_deg)
            
            # 计算该方向上的单位向量
            dir_x = math.cos(angle_rad)
            dir_y = math.sin(angle_rad)
            
            # 根据方向确定标签的哪个顶点应该是最近顶点
            # 并计算对应的标签中心偏移
            corner_offset_x, corner_offset_y = self._get_corner_offset_for_direction(
                dir_x, dir_y, box_width, box_height
            )
            
            # 生成不同距离的候选位置（从近到远）
            # 距离范围: 0.8 ~ 2.9（保留一点余量避免浮点数精度问题）
            distances = [0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 2.9]
            for distance in distances:
                if distance > self.max_label_distance - 0.01:  # 添加小容差
                    continue
                    
                # 计算顶点位置（在该方向上，距离设备点distance的位置）
                corner_x = anchor_x + dir_x * distance
                corner_y = anchor_y + dir_y * distance
                
                # 计算标签中心位置（根据顶点位置和偏移量）
                center_x = corner_x + corner_offset_x
                center_y = corner_y + corner_offset_y
                
                candidates.append((center_x, center_y, direction_idx))
        
        return candidates
    
    def _get_corner_offset_for_direction(self, dir_x: float, dir_y: float,
                                         box_width: float, box_height: float) -> Tuple[float, float]:
        """
        根据方向确定标签中心相对于最近顶点的偏移
        
        当标签的某个顶点位于某方向时，需要计算标签中心相对于该顶点的位置。
        例如：如果方向是右上（45°），则标签的左下顶点应该是最近顶点，
        此时标签中心在该顶点的右上方偏移半个宽度和高度。
        
        Args:
            dir_x: 方向向量X分量
            dir_y: 方向向量Y分量
            box_width: 标签框宽度
            box_height: 标签框高度
            
        Returns:
            (offset_x, offset_y) 标签中心相对于最近顶点的偏移
        """
        half_width = box_width / 2
        half_height = box_height / 2
        
        # 根据方向向量判断应该使用哪个顶点作为最近顶点
        # 然后计算从该顶点到中心的偏移
        
        # 如果方向指向右（dir_x > 0），则最近顶点应该在标签左侧
        # 如果方向指向上（dir_y > 0），则最近顶点应该在标签下侧
        
        if dir_x >= 0:
            # 方向指向右侧，最近顶点在左侧，中心在顶点右边
            offset_x = half_width
        else:
            # 方向指向左侧，最近顶点在右侧，中心在顶点左边
            offset_x = -half_width
        
        if dir_y >= 0:
            # 方向指向上方，最近顶点在下方，中心在顶点上方
            offset_y = half_height
        else:
            # 方向指向下方，最近顶点在上方，中心在顶点下方
            offset_y = -half_height
        
        return (offset_x, offset_y)
    
    def _get_nearest_corner_distance(self, center_x: float, center_y: float,
                                     box_width: float, box_height: float,
                                     anchor_x: float, anchor_y: float) -> Tuple[float, Tuple[float, float]]:
        """
        计算标签四个顶点中离设备点最近的顶点及其距离
        
        Args:
            center_x: 标签中心X坐标
            center_y: 标签中心Y坐标
            box_width: 标签宽度
            box_height: 标签高度
            anchor_x: 设备点X坐标
            anchor_y: 设备点Y坐标
            
        Returns:
            (最小距离, (最近顶点X, 最近顶点Y))
        """
        half_width = box_width / 2
        half_height = box_height / 2
        
        # 四个顶点
        corners = [
            (center_x - half_width, center_y - half_height),  # 左下
            (center_x + half_width, center_y - half_height),  # 右下
            (center_x - half_width, center_y + half_height),  # 左上
            (center_x + half_width, center_y + half_height),  # 右上
        ]
        
        min_dist = float('inf')
        nearest_corner = corners[0]
        
        for corner in corners:
            dist = math.sqrt((corner[0] - anchor_x)**2 + (corner[1] - anchor_y)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_corner = corner
        
        return (min_dist, nearest_corner)
    
    def _is_corner_on_12_directions(self, corner_x: float, corner_y: float,
                                    anchor_x: float, anchor_y: float,
                                    tolerance_deg: float = 5.0) -> bool:
        """
        检查顶点是否位于12个方向之一
        
        Args:
            corner_x: 顶点X坐标
            corner_y: 顶点Y坐标
            anchor_x: 设备点X坐标
            anchor_y: 设备点Y坐标
            tolerance_deg: 角度容差（度），默认5度
            
        Returns:
            True如果顶点位于12个方向之一
        """
        dx = corner_x - anchor_x
        dy = corner_y - anchor_y
        
        # 计算顶点相对于设备点的角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 归一化到 [0, 360) 范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 检查是否接近12个方向之一
        for direction_idx in range(self.direction_count):
            target_angle = direction_idx * self.direction_angle_step
            
            # 计算角度差（考虑360°循环）
            angle_diff = abs(angle_deg - target_angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            if angle_diff <= tolerance_deg:
                return True
        
        return False
    
    def calculate_device_label_position(self, anchor_x: float, anchor_y: float,
                                       element_id: str = "") -> Tuple[float, float]:
        """
        计算设备标签的最优位置（12方向约束版）
        
        设备标签只能出现在以设备点为圆心的12个方向（每30°）上，
        标签最近顶点到设备点的距离不能超过3。
        
        Args:
            anchor_x: 设备点X坐标
            anchor_y: 设备点Y坐标
            element_id: 元素ID
            
        Returns:
            最佳标签中心位置 (x, y)
        """
        # 获取设备标签尺寸
        box_width, box_height = self.info_box_sizes.get(ElementType.DEVICE_INFO, (2.0, 0.8))
        
        # 生成12方向候选位置
        candidates = self._generate_12_direction_candidates(
            anchor_x, anchor_y, box_width, box_height
        )
        
        # 预计算现有元素的边界框
        existing_boxes = [elem.bounding_box for elem in self.elements 
                         if elem.element_id != element_id]
        
        best_position = None
        best_score = float('inf')
        
        for center_x, center_y, direction_idx in candidates:
            # 创建候选边界框
            candidate_box = BoundingBox(
                center_x - box_width/2,
                center_y - box_height/2,
                center_x + box_width/2,
                center_y + box_height/2
            )
            
            # 快速边界检查
            if not self._is_within_canvas(candidate_box):
                continue
            
            # 检查是否在扇形内（强制跳过）
            if self._is_box_in_sector(candidate_box):
                continue
            
            # 验证最近顶点约束
            min_dist, nearest_corner = self._get_nearest_corner_distance(
                center_x, center_y, box_width, box_height, anchor_x, anchor_y
            )
            
            # 检查距离约束
            if min_dist > self.max_label_distance:
                continue
            
            # 检查最近顶点是否在12方向上
            if not self._is_corner_on_12_directions(
                nearest_corner[0], nearest_corner[1], anchor_x, anchor_y
            ):
                continue
            
            # 计算位置评分
            score = self._calculate_position_score(candidate_box, existing_boxes, anchor_x, anchor_y)
            
            # 添加距离奖励（优先选择较近的位置）
            score += min_dist * 5.0
            
            if score < best_score:
                best_score = score
                best_position = (center_x, center_y)
                
                # 早期退出：找到无冲突位置
                if score < 1.0:
                    break
        
        # 如果没有找到合适位置，使用默认位置（右上方向，距离1.2）
        if best_position is None:
            default_angle = math.radians(45)  # 默认右上方向
            default_distance = 1.2
            corner_x = anchor_x + math.cos(default_angle) * default_distance
            corner_y = anchor_y + math.sin(default_angle) * default_distance
            corner_offset_x, corner_offset_y = self._get_corner_offset_for_direction(
                math.cos(default_angle), math.sin(default_angle), box_width, box_height
            )
            best_position = (corner_x + corner_offset_x, corner_y + corner_offset_y)
            print(f"⚠️ 12方向约束：未找到合适位置，使用默认位置")
        
        return best_position
    
    def calculate_optimal_position(self, 
                                 anchor_x: float, 
                                 anchor_y: float,
                                 element_type: ElementType,
                                 element_id: str = "",
                                 preferred_offset: Tuple[float, float] = None) -> Tuple[float, float]:
        """
        高性能位置计算算法
        
        对于设备标签（DEVICE_INFO），使用12方向约束布局
        对于其他类型标签，使用传统的候选位置算法
        
        Args:
            anchor_x: 锚点X坐标
            anchor_y: 锚点Y坐标
            element_type: 元素类型
            element_id: 元素ID
            preferred_offset: 首选偏移量
            
        Returns:
            最佳位置 (x, y)
        """
        # 检查缓存
        cache_key = f"{element_type.value}_{anchor_x:.2f}_{anchor_y:.2f}_{element_id}"
        if cache_key in self._position_cache and self._cache_valid:
            return self._position_cache[cache_key]
        
        if element_type not in self.info_box_sizes:
            result = (anchor_x + 0.5, anchor_y + 0.5)
            self._position_cache[cache_key] = result
            return result
        
        # 🆕 设备标签使用12方向约束布局
        if element_type == ElementType.DEVICE_INFO:
            result = self.calculate_device_label_position(anchor_x, anchor_y, element_id)
            self._position_cache[cache_key] = result
            return result
        
        box_width, box_height = self.info_box_sizes[element_type]
        
        # 快速路径：如果没有其他元素，使用默认位置
        if len(self.elements) == 0:
            default_pos = self._get_default_position(anchor_x, anchor_y, element_type, preferred_offset)
            self._position_cache[cache_key] = default_pos
            return default_pos
        
        # 构建候选位置列表
        candidate_offsets = []
        if preferred_offset:
            candidate_offsets.append(preferred_offset)
        candidate_offsets.extend(self.primary_offsets)
        candidate_offsets.extend(self.secondary_offsets)
        
        # 🆕 如果存在扇形斥力场，添加扩展候选位置
        if self.sector_regions:
            candidate_offsets.extend(self.extended_offsets)
        
        best_position = None
        best_score = float('inf')
        
        # 预计算现有元素的边界框（性能优化）
        existing_boxes = [elem.bounding_box for elem in self.elements 
                         if elem.element_id != element_id]
        
        for offset_x, offset_y in candidate_offsets:
            candidate_x = anchor_x + offset_x
            candidate_y = anchor_y + offset_y
            
            # 创建候选边界框
            candidate_box = BoundingBox(
                candidate_x - box_width/2,
                candidate_y - box_height/2,
                candidate_x + box_width/2,
                candidate_y + box_height/2
            )
            
            # 快速边界检查
            if not self._is_within_canvas(candidate_box):
                continue
            
            # 🆕 强制检查：完全跳过在扇形内的候选位置
            if self._is_box_in_sector(candidate_box):
                continue
            
            # 快速冲突检测（包含锚点距离惩罚）
            score = self._calculate_position_score(candidate_box, existing_boxes, anchor_x, anchor_y)
            
            if score < best_score:
                best_score = score
                best_position = (candidate_x, candidate_y)
                
                # 早期退出：找到无冲突位置
                if score == 0:
                    break
        
        # 如果没有找到合适位置，使用默认位置
        if best_position is None:
            best_position = self._get_default_position(anchor_x, anchor_y, element_type, preferred_offset)
        
        # 缓存结果
        self._position_cache[cache_key] = best_position
        
        # 只在显著调整时输出日志
        if preferred_offset:
            original_pos = (anchor_x + preferred_offset[0], anchor_y + preferred_offset[1])
            log_threshold = LayoutConstants.POSITION_CHANGE_LOG_THRESHOLD
            if (abs(best_position[0] - original_pos[0]) > log_threshold or 
                abs(best_position[1] - original_pos[1]) > log_threshold):
                print(f"🚀 高性能避让: {element_type.value} 位置优化 (评分:{best_score:.1f})")
        
        return best_position
    
    def _get_default_position(self, anchor_x: float, anchor_y: float, 
                            element_type: ElementType, 
                            preferred_offset: Tuple[float, float] = None) -> Tuple[float, float]:
        """获取默认位置"""
        if preferred_offset:
            return (anchor_x + preferred_offset[0], anchor_y + preferred_offset[1])
        
        # 根据锚点位置选择默认偏移
        if anchor_x < 0:
            offset_x = LayoutConstants.DEFAULT_OFFSET_X  # 左侧锚点，信息框放右边
        else:
            offset_x = -LayoutConstants.DEFAULT_OFFSET_X  # 右侧锚点，信息框放左边
        
        offset_y = LayoutConstants.DEFAULT_OFFSET_Y  # 默认向上偏移
        
        return (anchor_x + offset_x, anchor_y + offset_y)
    
    def _is_within_canvas(self, box: BoundingBox) -> bool:
        """快速边界检查 - 更严格的边界约束"""
        margin = LayoutConstants.CANVAS_MARGIN  # 边界余量，避免标签过于接近边界
        return (box.x_min >= self.canvas_bounds.x_min + margin and
                box.x_max <= self.canvas_bounds.x_max - margin and
                box.y_min >= self.canvas_bounds.y_min + margin and
                box.y_max <= self.canvas_bounds.y_max - margin)
    
    def _calculate_position_score(self, candidate_box: BoundingBox, 
                                existing_boxes: List[BoundingBox],
                                anchor_x: float = None,
                                anchor_y: float = None) -> float:
        """
        快速位置评分算法 - V2.0 增强版
        
        Args:
            candidate_box: 候选边界框
            existing_boxes: 现有元素边界框列表
            anchor_x: 锚点X坐标（用于计算距离惩罚）
            anchor_y: 锚点Y坐标（用于计算距离惩罚）
            
        Returns:
            位置评分（越低越好，0表示无冲突）
        """
        score = 0.0
        box_center_x, box_center_y = candidate_box.center()
        
        # 🆕 扇形斥力场惩罚（最高优先级）
        sector_penalty = self._calculate_sector_penalty(box_center_x, box_center_y)
        if sector_penalty > 0:
            score += sector_penalty
        
        for existing_box in existing_boxes:
            if candidate_box.overlaps(existing_box):
                # 重叠惩罚：基于重叠面积
                overlap_area = candidate_box.overlap_area(existing_box)
                score += overlap_area * self.overlap_penalty
            else:
                # 距离奖励：距离太近时轻微惩罚（鼓励紧凑但不重叠的布局）
                distance = candidate_box.distance_to(existing_box)
                spacing_threshold = self.min_spacing * LayoutConstants.SPACING_MULTIPLIER
                if distance < spacing_threshold:
                    score += max(0, (spacing_threshold - distance)) * LayoutConstants.SPACING_PENALTY
        
        # 🎯 距离锚点的惩罚（核心优化）
        if anchor_x is not None and anchor_y is not None:
            anchor_distance = math.sqrt((box_center_x - anchor_x)**2 + (box_center_y - anchor_y)**2)
            
            # 距离惩罚：离锚点越远，惩罚越大（鼓励标签靠近自己的设备点）
            # 🆕 如果在扇形内，放宽距离惩罚（允许标签远离以避开扇形）
            if sector_penalty > 0:
                # 在扇形区域内，放宽距离限制
                if anchor_distance > LayoutConstants.SECTOR_DISTANCE_THRESHOLD:
                    score += (anchor_distance - LayoutConstants.SECTOR_DISTANCE_THRESHOLD) * LayoutConstants.SECTOR_DISTANCE_PENALTY
            else:
                # 正常距离惩罚（分层递减）
                if anchor_distance > LayoutConstants.DISTANCE_FAR_THRESHOLD:
                    score += (anchor_distance - LayoutConstants.DISTANCE_FAR_THRESHOLD) * LayoutConstants.DISTANCE_FAR_PENALTY
                elif anchor_distance > LayoutConstants.DISTANCE_MID_THRESHOLD:
                    score += (anchor_distance - LayoutConstants.DISTANCE_MID_THRESHOLD) * LayoutConstants.DISTANCE_MID_PENALTY
                elif anchor_distance > LayoutConstants.DISTANCE_NEAR_THRESHOLD:
                    score += (anchor_distance - LayoutConstants.DISTANCE_NEAR_THRESHOLD) * LayoutConstants.DISTANCE_NEAR_PENALTY
        
        # 边界惩罚：离边界太近的位置（更严格）
        canvas_center_x = (self.canvas_bounds.x_min + self.canvas_bounds.x_max) / 2
        canvas_center_y = (self.canvas_bounds.y_min + self.canvas_bounds.y_max) / 2
        
        # 计算到画布中心的距离（归一化）
        canvas_width = self.canvas_bounds.x_max - self.canvas_bounds.x_min
        canvas_height = self.canvas_bounds.y_max - self.canvas_bounds.y_min
        
        center_distance_x = abs(box_center_x - canvas_center_x) / (canvas_width / 2)
        center_distance_y = abs(box_center_y - canvas_center_y) / (canvas_height / 2)
        
        # 🎯 更严格的边界惩罚：从60%开始惩罚
        boundary_start = LayoutConstants.BOUNDARY_START_RATIO
        if center_distance_x > boundary_start:
            score += (center_distance_x - boundary_start) * self.boundary_penalty * LayoutConstants.BOUNDARY_PENALTY_MULTIPLIER
        if center_distance_y > boundary_start:
            score += (center_distance_y - boundary_start) * self.boundary_penalty * LayoutConstants.BOUNDARY_PENALTY_MULTIPLIER
        
        return score
    
    def get_layout_statistics(self) -> Dict[str, any]:
        """
        获取布局统计信息（用于调试和优化）
        
        性能说明:
            时间复杂度: O(n²)，其中 n 为元素数量
            此方法用于调试目的，不应在性能敏感路径中频繁调用。
            对于大量元素（n > 100），考虑使用空间分区数据结构优化。
        """
        if not self.elements:
            return {"total_elements": 0, "overlaps": 0, "cache_size": 0}
        
        # 计算重叠数量
        # 注意: 双重循环 O(n²) 复杂度，仅用于调试统计
        overlap_count = 0
        for i, elem1 in enumerate(self.elements):
            for elem2 in self.elements[i+1:]:
                if elem1.bounding_box.overlaps(elem2.bounding_box):
                    overlap_count += 1
        
        return {
            "total_elements": len(self.elements),
            "overlaps": overlap_count,
            "cache_size": len(self._position_cache),
            "cache_valid": self._cache_valid
        }
    
    def compute_layout(self, iterations: int = 50):
        """
        执行力导向布局计算 - V2.0 增强版
        
        核心改进：
        1. 扇形斥力场 - 标签进入扇形区域会被强力弹开
        2. 模拟退火扰动 - 避免陷入局部最优解
        3. 分层计算 - 按优先级依次处理不同类型的标签
        
        Args:
            iterations: 迭代次数
        """
        # 🆕 分层计算：按优先级分组
        device_elements = [e for e in self.elements if e.movable and not e.static 
                          and e.element_type == ElementType.DEVICE_INFO]
        measurement_elements = [e for e in self.elements if e.movable and not e.static 
                               and e.element_type == ElementType.MEASUREMENT_INFO]
        user_elements = [e for e in self.elements if e.movable and not e.static 
                        and e.element_type == ElementType.USER_POSITION]
        other_elements = [e for e in self.elements if e.movable and not e.static 
                         and e.element_type not in [ElementType.DEVICE_INFO, 
                                                     ElementType.MEASUREMENT_INFO, 
                                                     ElementType.USER_POSITION]]
        
        # 第1轮：处理设备标签
        if device_elements:
            self._compute_layer_layout(device_elements, iterations // 2)
            # 🆕 固定设备标签
            for elem in device_elements:
                elem.movable = False
        
        # 第2轮：处理测量标签
        if measurement_elements:
            self._compute_layer_layout(measurement_elements, iterations // 2)
            # 固定测量标签
            for elem in measurement_elements:
                elem.movable = False
        
        # 第3轮：处理用户位置标签
        if user_elements:
            self._compute_layer_layout(user_elements, iterations // 3)
            # 固定用户位置标签
            for elem in user_elements:
                elem.movable = False
        
        # 第4轮：处理其他标签
        if other_elements:
            self._compute_layer_layout(other_elements, iterations // 3)
        
        # 恢复所有元素的可移动状态（供下次计算使用）
        for elem in self.elements:
            if not elem.static:
                elem.movable = True
        
        # 使缓存失效
        self._invalidate_cache()
    
    def _compute_layer_layout(self, layer_elements: List[LayoutElement], iterations: int):
        """
        单层布局计算（带扰动机制）
        
        Args:
            layer_elements: 当前层的元素列表
            iterations: 迭代次数
        
        性能说明:
            时间复杂度: O(iterations × m × n)，其中 m 为层内元素数，n 为总元素数
            在最坏情况下约为 O(n²) 每次迭代。
            
            优化策略:
            1. 分层计算减少每层的元素数量
            2. 早期收敛退出减少迭代次数
            3. 模拟退火避免陷入局部最优
            
            对于大规模数据（n > 50），可考虑:
            - 使用四叉树进行空间分区
            - 只计算邻近元素间的斥力
            - 并行计算各元素的力
        """
        if not layer_elements:
            return
        
        # 力导向参数（使用常量）
        repulsion_strength = LayoutConstants.REPULSION_STRENGTH  # 排斥力强度
        anchor_attraction = LayoutConstants.ANCHOR_ATTRACTION    # 锚点吸引力强度
        damping = LayoutConstants.DAMPING                        # 阻尼系数
        
        # 🆕 模拟退火参数
        temperature = self.initial_temperature
        
        for iteration in range(iterations):
            max_movement = 0.0
            
            # 🆕 计算当前温度（逐渐降低）
            temperature = self.initial_temperature * (self.cooling_rate ** iteration)
            temperature = max(temperature, self.min_temperature)
            
            for element in layer_elements:
                force_x = 0.0
                force_y = 0.0
                
                # 🆕 扇形斥力场
                sector_force_x, sector_force_y = self._get_sector_repulsion_force(
                    element.current_x, element.current_y
                )
                force_x += sector_force_x
                force_y += sector_force_y
                
                # 计算排斥力（来自所有元素，包括已固定的）
                # 注意: 此内循环遍历所有元素，构成 O(n) 复杂度
                # 未来优化方向: 使用空间分区只检测邻近元素
                for other in self.elements:
                    if other is element:
                        continue
                    
                    dx = element.current_x - other.current_x
                    dy = element.current_y - other.current_y
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist < LayoutConstants.NEAR_ZERO_THRESHOLD:
                        dist = LayoutConstants.NEAR_ZERO_THRESHOLD
                    
                    # 检查是否有重叠
                    elem_bbox = self._get_bbox_at_position(element, element.current_x, element.current_y)
                    other_bbox = self._get_bbox_at_position(other, other.current_x, other.current_y)
                    
                    if elem_bbox.overlaps(other_bbox):
                        # 有重叠时，施加较强的排斥力
                        repulsion = (repulsion_strength * LayoutConstants.OVERLAP_REPULSION_MULTIPLIER / 
                                   max(dist, LayoutConstants.MIN_DISTANCE_CLAMP))
                        force_x += repulsion * dx / dist
                        force_y += repulsion * dy / dist
                    elif dist < LayoutConstants.PROXIMITY_THRESHOLD:
                        # 接近时，施加较弱的排斥力
                        repulsion = repulsion_strength * LayoutConstants.PROXIMITY_REPULSION_FACTOR / dist
                        force_x += repulsion * dx / dist
                        force_y += repulsion * dy / dist
                
                # 计算锚点吸引力（🆕 在扇形区域内时减弱吸引力）
                anchor_x, anchor_y = element.anchor_point
                dx_anchor = anchor_x - element.current_x
                dy_anchor = anchor_y - element.current_y
                anchor_dist = math.sqrt(dx_anchor*dx_anchor + dy_anchor*dy_anchor)
                
                # 🆕 检查锚点是否在扇形内
                anchor_in_sector = self._calculate_sector_penalty(anchor_x, anchor_y) > 0
                
                if anchor_dist > LayoutConstants.ANCHOR_TRIGGER_DISTANCE:
                    # 超过一定距离时，吸引回锚点附近
                    attraction = anchor_attraction
                    if anchor_in_sector:
                        attraction *= LayoutConstants.SECTOR_ATTRACTION_REDUCTION  # 如果锚点在扇形内，减弱吸引力
                    
                    force_x += attraction * dx_anchor
                    force_y += attraction * dy_anchor
                
                # 🆕 扰动机制：在高温时添加随机扰动
                if temperature > self.min_temperature * LayoutConstants.TEMPERATURE_THRESHOLD_MULTIPLIER:
                    perturbation_x = random.gauss(0, temperature * LayoutConstants.PERTURBATION_STRENGTH)
                    perturbation_y = random.gauss(0, temperature * LayoutConstants.PERTURBATION_STRENGTH)
                    force_x += perturbation_x
                    force_y += perturbation_y
                
                # 应用力（带阻尼）
                move_x = force_x * damping
                move_y = force_y * damping
                
                # 限制单次移动距离（高温时允许更大移动）
                max_move = (LayoutConstants.BASE_MAX_MOVE + 
                           temperature * LayoutConstants.TEMPERATURE_MOVE_FACTOR)
                move_dist = math.sqrt(move_x*move_x + move_y*move_y)
                if move_dist > max_move:
                    move_x = move_x / move_dist * max_move
                    move_y = move_y / move_dist * max_move
                
                # 更新位置
                new_x = element.current_x + move_x
                new_y = element.current_y + move_y
                
                # 边界约束
                margin = LayoutConstants.CANVAS_MARGIN
                new_x = max(self.canvas_bounds.x_min + margin, 
                           min(new_x, self.canvas_bounds.x_max - margin))
                new_y = max(self.canvas_bounds.y_min + margin, 
                           min(new_y, self.canvas_bounds.y_max - margin))
                
                movement = math.sqrt((new_x - element.current_x)**2 + 
                                    (new_y - element.current_y)**2)
                max_movement = max(max_movement, movement)
                
                element.current_x = new_x
                element.current_y = new_y
            
            # 🆕 只有在低温且移动量很小时才提前结束
            convergence_temp = self.min_temperature * LayoutConstants.CONVERGENCE_TEMP_MULTIPLIER
            if temperature < convergence_temp and max_movement < LayoutConstants.CONVERGENCE_MOVEMENT_THRESHOLD:
                break
    
    def _get_bbox_at_position(self, element: LayoutElement, x: float, y: float) -> BoundingBox:
        """
        获取元素在指定位置的边界框
        
        Args:
            element: 布局元素
            x: 中心X坐标
            y: 中心Y坐标
            
        Returns:
            边界框对象
        """
        width = element.bounding_box.x_max - element.bounding_box.x_min
        height = element.bounding_box.y_max - element.bounding_box.y_min
        
        return BoundingBox(
            x - width/2,
            y - height/2,
            x + width/2,
            y + height/2
        ) 