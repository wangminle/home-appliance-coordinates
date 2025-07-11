"""
智能布局管理器 - 高性能原生实现

替代adjustText库的高性能布局解决方案，专门针对家居设备坐标绘制场景优化
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time


class ElementType(Enum):
    """元素类型枚举"""
    DEVICE_INFO = "device_info"        # 设备信息框
    MEASUREMENT_INFO = "measurement_info"  # 测量信息框
    COORDINATE_INFO = "coordinate_info"    # 坐标信息框
    USER_POSITION = "user_position"       # 用户位置标记
    SECTOR = "sector"                     # 扇形区域
    MEASUREMENT_LINE = "measurement_line" # 测量线


class DeviceInfoPosition(Enum):
    """设备信息框位置枚举"""
    TOP_LEFT = "top_left"       # 左上角
    TOP_RIGHT = "top_right"     # 右上角
    BOTTOM_LEFT = "bottom_left" # 左下角
    BOTTOM_RIGHT = "bottom_right" # 右下角


@dataclass
class BoundingBox:
    """边界框定义"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    
    def overlaps(self, other: 'BoundingBox') -> bool:
        """检查是否与另一个边界框重叠"""
        return not (self.x_max <= other.x_min or 
                   other.x_max <= self.x_min or
                   self.y_max <= other.y_min or 
                   other.y_max <= self.y_min)
    
    def area(self) -> float:
        """计算边界框面积"""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def center(self) -> Tuple[float, float]:
        """获取边界框中心点"""
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)


@dataclass
class LayoutElement:
    """布局元素定义"""
    element_type: ElementType
    bounding_box: BoundingBox
    anchor_point: Tuple[float, float]  # 锚点（元素指向的坐标）
    priority: int = 5  # 优先级（1-10，数字越大优先级越高）
    movable: bool = True  # 是否可移动
    element_id: str = ""  # 元素唯一标识
    device_position: Optional[DeviceInfoPosition] = None  # 设备信息框位置
    # 扇形几何参数（仅对SECTOR类型有效）✨ 新增精确扇形支持
    sector_center: Optional[Tuple[float, float]] = None  # 扇形中心点
    sector_radius: Optional[float] = None  # 扇形半径
    sector_start_angle: Optional[float] = None  # 起始角度（度数）
    sector_end_angle: Optional[float] = None  # 结束角度（度数）
    creation_time: float = 0.0  # 创建时间
    extra_data: Dict[str, Any] = None  # 额外数据


class FastLayoutManager:
    """
    高性能原生布局管理器
    
    专门为家居设备坐标绘制场景优化的布局算法，提供比adjustText更好的性能
    """
    
    def __init__(self, canvas_bounds: Tuple[float, float, float, float]):
        """
        初始化布局管理器
        
        Args:
            canvas_bounds: 画布边界 (x_min, y_min, x_max, y_max)
        """
        self.canvas_bounds = BoundingBox(*canvas_bounds)
        self.elements: List[LayoutElement] = []
        
        # 性能优化：缓存机制
        self._position_cache: Dict[str, Tuple[float, float]] = {}
        self._cache_valid = True
        
        # 信息框尺寸配置
        self.info_box_sizes = {
            ElementType.DEVICE_INFO: (2.2, 1.0),      # 设备信息框（优化尺寸）
            ElementType.MEASUREMENT_INFO: (2.8, 1.6), # 测量信息框  
            ElementType.COORDINATE_INFO: (2.5, 1.2),  # 坐标信息框
            ElementType.USER_POSITION: (1.6, 0.8),    # 用户位置标记
        }
        
        # 高性能避让偏移量配置（预计算）
        self.primary_offsets = [
            (1.5, 1.0),   # 右上（主要位置）
            (-1.5, 1.0),  # 左上
            (1.5, -1.0),  # 右下
            (-1.5, -1.0), # 左下
        ]
        
        self.secondary_offsets = [
            (2.2, 0),     # 右中
            (-2.2, 0),    # 左中
            (0, 1.4),     # 上中
            (0, -1.4),    # 下中
        ]
        
        # 布局质量阈值
        self.min_spacing = 0.2  # 最小间距
        self.overlap_penalty = 10.0  # 重叠惩罚系数
        self.boundary_penalty = 5.0  # 边界惩罚系数
    
    def clear_elements(self):
        """清除所有元素"""
        self.elements.clear()
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
    
    def _invalidate_cache(self):
        """使缓存失效"""
        self._position_cache.clear()
        self._cache_valid = False
    
    def calculate_optimal_position(self, 
                                 anchor_x: float, 
                                 anchor_y: float,
                                 element_type: ElementType,
                                 element_id: str = "",
                                 preferred_offset: Tuple[float, float] = None) -> Tuple[float, float]:
        """
        高性能位置计算算法
        
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
            
            # 快速冲突检测
            score = self._calculate_position_score(candidate_box, existing_boxes)
            
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
            if (abs(best_position[0] - original_pos[0]) > 0.3 or 
                abs(best_position[1] - original_pos[1]) > 0.3):
                print(f"🎯 高性能避让: {element_type.value} 调整位置 (分数:{best_score:.1f})")
        
        return best_position
    
    def _get_default_position(self, anchor_x: float, anchor_y: float, 
                            element_type: ElementType, 
                            preferred_offset: Tuple[float, float] = None) -> Tuple[float, float]:
        """获取默认位置"""
        if preferred_offset:
            return (anchor_x + preferred_offset[0], anchor_y + preferred_offset[1])
        
        # 根据锚点位置选择默认偏移
        if anchor_x < 0:
            offset_x = 1.5  # 左侧锚点，信息框放右边
        else:
            offset_x = -1.5  # 右侧锚点，信息框放左边
        
        offset_y = 1.0  # 默认向上偏移
        
        return (anchor_x + offset_x, anchor_y + offset_y)
    
    def _is_within_canvas(self, box: BoundingBox) -> bool:
        """快速边界检查"""
        margin = 0.1
        return (box.x_min >= self.canvas_bounds.x_min + margin and
                box.x_max <= self.canvas_bounds.x_max - margin and
                box.y_min >= self.canvas_bounds.y_min + margin and
                box.y_max <= self.canvas_bounds.y_max - margin)
    
    def _calculate_position_score(self, candidate_box: BoundingBox, 
                                existing_boxes: List[BoundingBox]) -> float:
        """
        快速位置评分算法
        
        Args:
            candidate_box: 候选边界框
            existing_boxes: 现有元素边界框列表
            
        Returns:
            位置评分（越低越好，0表示无冲突）
        """
        score = 0.0
        
        for existing_box in existing_boxes:
            if candidate_box.overlaps(existing_box):
                # 重叠惩罚：基于重叠面积
                overlap_area = candidate_box.overlap_area(existing_box)
                score += overlap_area * self.overlap_penalty
            else:
                # 距离奖励：距离越近，轻微惩罚（鼓励紧凑布局）
                distance = candidate_box.distance_to(existing_box)
                if distance < self.min_spacing * 2:
                    score += (self.min_spacing * 2 - distance) * 0.5
        
        # 边界惩罚：离边界太近的位置
        canvas_center_x = (self.canvas_bounds.x_min + self.canvas_bounds.x_max) / 2
        canvas_center_y = (self.canvas_bounds.y_min + self.canvas_bounds.y_max) / 2
        box_center_x, box_center_y = candidate_box.center()
        
        # 计算到画布中心的距离（归一化）
        canvas_width = self.canvas_bounds.x_max - self.canvas_bounds.x_min
        canvas_height = self.canvas_bounds.y_max - self.canvas_bounds.y_min
        
        center_distance_x = abs(box_center_x - canvas_center_x) / (canvas_width / 2)
        center_distance_y = abs(box_center_y - canvas_center_y) / (canvas_height / 2)
        
        # 接近边界时增加惩罚
        if center_distance_x > 0.8:
            score += (center_distance_x - 0.8) * self.boundary_penalty
        if center_distance_y > 0.8:
            score += (center_distance_y - 0.8) * self.boundary_penalty
        
        return score
    
    def get_layout_statistics(self) -> Dict[str, any]:
        """获取布局统计信息（用于调试和优化）"""
        if not self.elements:
            return {"total_elements": 0, "overlaps": 0, "cache_size": 0}
        
        # 计算重叠数量
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

# 兼容性别名
LayoutManager = FastLayoutManager