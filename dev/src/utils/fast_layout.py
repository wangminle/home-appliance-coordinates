# -*- coding: utf-8 -*-
"""
高性能原生布局管理器

简洁高效的标注避让方案，专门针对家居设备坐标绘制场景优化
核心算法：智能离散槽位搜索 + 锚点距离惩罚
"""

from enum import Enum
from typing import List, Tuple, Optional, Dict
import math
import time

class ElementType(Enum):
    """元素类型枚举"""
    DEVICE_INFO = "device_info"
    MEASUREMENT_INFO = "measurement_info"
    USER_POSITION = "user_position"
    COORDINATE_INFO = "coordinate_info"
    SECTOR = "sector"
    MEASUREMENT_LINE = "measurement_line"

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
            ElementType.DEVICE_INFO: (2.0, 0.8),      # 设备信息框（优化尺寸）
            ElementType.MEASUREMENT_INFO: (2.6, 1.4), # 测量信息框  
            ElementType.COORDINATE_INFO: (2.3, 1.0),  # 坐标信息框
            ElementType.USER_POSITION: (1.5, 0.7),    # 用户位置标记
        }
        
        # 高性能避让偏移量配置（预计算）
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
        
        # 布局质量阈值
        self.min_spacing = 0.15  # 最小间距
        self.overlap_penalty = 100.0  # 重叠惩罚系数
        self.boundary_penalty = 10.0  # 边界惩罚系数
    
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
            if (abs(best_position[0] - original_pos[0]) > 0.3 or 
                abs(best_position[1] - original_pos[1]) > 0.3):
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
            offset_x = 1.2  # 左侧锚点，信息框放右边
        else:
            offset_x = -1.2  # 右侧锚点，信息框放左边
        
        offset_y = 0.8  # 默认向上偏移
        
        return (anchor_x + offset_x, anchor_y + offset_y)
    
    def _is_within_canvas(self, box: BoundingBox) -> bool:
        """快速边界检查 - 更严格的边界约束"""
        margin = 0.5  # 增加边界余量，避免标签过于接近边界
        return (box.x_min >= self.canvas_bounds.x_min + margin and
                box.x_max <= self.canvas_bounds.x_max - margin and
                box.y_min >= self.canvas_bounds.y_min + margin and
                box.y_max <= self.canvas_bounds.y_max - margin)
    
    def _calculate_position_score(self, candidate_box: BoundingBox, 
                                existing_boxes: List[BoundingBox],
                                anchor_x: float = None,
                                anchor_y: float = None) -> float:
        """
        快速位置评分算法 - 优化版
        
        Args:
            candidate_box: 候选边界框
            existing_boxes: 现有元素边界框列表
            anchor_x: 锚点X坐标（用于计算距离惩罚）
            anchor_y: 锚点Y坐标（用于计算距离惩罚）
            
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
                # 距离奖励：距离太近时轻微惩罚（鼓励紧凑但不重叠的布局）
                distance = candidate_box.distance_to(existing_box)
                if distance < self.min_spacing * 3:
                    score += max(0, (self.min_spacing * 3 - distance)) * 2.0
        
        # 🎯 新增：距离锚点的惩罚（核心优化）
        if anchor_x is not None and anchor_y is not None:
            box_center_x, box_center_y = candidate_box.center()
            anchor_distance = math.sqrt((box_center_x - anchor_x)**2 + (box_center_y - anchor_y)**2)
            
            # 距离惩罚：离锚点越远，惩罚越大（鼓励标签靠近自己的设备点）
            if anchor_distance > 1.8:  # 超过1.8个单位距离时开始重惩罚
                score += (anchor_distance - 1.8) * 50.0  # 超强距离惩罚
            elif anchor_distance > 1.5:  # 超过1.5个单位距离时中惩罚
                score += (anchor_distance - 1.5) * 15.0  # 中距离惩罚
            elif anchor_distance > 1.2:  # 超过1.2个单位距离时轻惩罚
                score += (anchor_distance - 1.2) * 3.0   # 轻距离惩罚
        
        # 边界惩罚：离边界太近的位置（更严格）
        canvas_center_x = (self.canvas_bounds.x_min + self.canvas_bounds.x_max) / 2
        canvas_center_y = (self.canvas_bounds.y_min + self.canvas_bounds.y_max) / 2
        box_center_x, box_center_y = candidate_box.center()
        
        # 计算到画布中心的距离（归一化）
        canvas_width = self.canvas_bounds.x_max - self.canvas_bounds.x_min
        canvas_height = self.canvas_bounds.y_max - self.canvas_bounds.y_min
        
        center_distance_x = abs(box_center_x - canvas_center_x) / (canvas_width / 2)
        center_distance_y = abs(box_center_y - canvas_center_y) / (canvas_height / 2)
        
        # 🎯 更严格的边界惩罚：从60%开始惩罚（而不是75%）
        if center_distance_x > 0.6:
            score += (center_distance_x - 0.6) * self.boundary_penalty * 2
        if center_distance_y > 0.6:
            score += (center_distance_y - 0.6) * self.boundary_penalty * 2
        
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
    
    def compute_layout(self, iterations: int = 50):
        """
        执行力导向布局计算
        
        使用简化的力导向算法调整可移动元素的位置，避免重叠
        
        Args:
            iterations: 迭代次数
        """
        movable_elements = [e for e in self.elements if e.movable and not e.static]
        
        if not movable_elements:
            return
        
        # 力导向参数
        repulsion_strength = 0.3  # 排斥力强度
        anchor_attraction = 0.2   # 锚点吸引力强度
        damping = 0.85            # 阻尼系数
        
        for iteration in range(iterations):
            max_movement = 0.0
            
            for element in movable_elements:
                force_x = 0.0
                force_y = 0.0
                
                # 计算排斥力（来自其他元素）
                for other in self.elements:
                    if other is element:
                        continue
                    
                    dx = element.current_x - other.current_x
                    dy = element.current_y - other.current_y
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist < 0.01:
                        dist = 0.01
                    
                    # 检查是否有重叠
                    elem_bbox = self._get_bbox_at_position(element, element.current_x, element.current_y)
                    other_bbox = self._get_bbox_at_position(other, other.current_x, other.current_y)
                    
                    if elem_bbox.overlaps(other_bbox):
                        # 有重叠时，施加较强的排斥力
                        repulsion = repulsion_strength * 3.0 / max(dist, 0.1)
                        force_x += repulsion * dx / dist
                        force_y += repulsion * dy / dist
                    elif dist < 2.0:
                        # 接近时，施加较弱的排斥力
                        repulsion = repulsion_strength * 0.5 / dist
                        force_x += repulsion * dx / dist
                        force_y += repulsion * dy / dist
                
                # 计算锚点吸引力
                anchor_x, anchor_y = element.anchor_point
                dx_anchor = anchor_x - element.current_x
                dy_anchor = anchor_y - element.current_y
                anchor_dist = math.sqrt(dx_anchor*dx_anchor + dy_anchor*dy_anchor)
                
                if anchor_dist > 0.5:
                    # 超过一定距离时，吸引回锚点附近
                    force_x += anchor_attraction * dx_anchor
                    force_y += anchor_attraction * dy_anchor
                
                # 应用力（带阻尼）
                move_x = force_x * damping
                move_y = force_y * damping
                
                # 限制单次移动距离
                max_move = 0.5
                move_dist = math.sqrt(move_x*move_x + move_y*move_y)
                if move_dist > max_move:
                    move_x = move_x / move_dist * max_move
                    move_y = move_y / move_dist * max_move
                
                # 更新位置
                new_x = element.current_x + move_x
                new_y = element.current_y + move_y
                
                # 边界约束
                margin = 0.5
                new_x = max(self.canvas_bounds.x_min + margin, 
                           min(new_x, self.canvas_bounds.x_max - margin))
                new_y = max(self.canvas_bounds.y_min + margin, 
                           min(new_y, self.canvas_bounds.y_max - margin))
                
                movement = math.sqrt((new_x - element.current_x)**2 + 
                                    (new_y - element.current_y)**2)
                max_movement = max(max_movement, movement)
                
                element.current_x = new_x
                element.current_y = new_y
            
            # 如果移动量很小，提前结束
            if max_movement < 0.01:
                break
        
        # 使缓存失效
        self._invalidate_cache()
    
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