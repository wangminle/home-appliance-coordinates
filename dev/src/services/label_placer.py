# -*- coding: utf-8 -*-
"""
标签布局服务

确定性8方向标签布局算法。
V2.0 第二期重构核心模块，替代原有的1129行复杂力导向算法。

设计原则：
1. 确定性 - 同样输入永远产生同样输出
2. 简单高效 - 按优先级顺序尝试8个方向
3. 支持手动覆盖 - 用户拖拽的位置优先保留
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from services.collision_detector import BoundingBox, CollisionDetector


@dataclass
class LabelPosition:
    """
    标签位置数据
    
    用于记录标签的位置信息，支持区分自动计算和手动设置。
    """
    x: float                    # 标签中心X坐标
    y: float                    # 标签中心Y坐标
    is_manual: bool = False     # 是否手动设置
    direction: str = ""         # 方向名称（调试用）
    
    def copy(self) -> 'LabelPosition':
        """创建副本"""
        return LabelPosition(
            x=self.x,
            y=self.y,
            is_manual=self.is_manual,
            direction=self.direction
        )


@dataclass
class SectorObstacle:
    """
    扇形障碍物数据
    
    用于标签布局时避开扇形区域。
    """
    center_x: float             # 扇形圆心X坐标
    center_y: float             # 扇形圆心Y坐标
    radius: float               # 扇形半径
    start_angle_deg: float      # 起始角度（度数）
    end_angle_deg: float        # 结束角度（度数）


@dataclass  
class DeviceAnchor:
    """
    设备锚点数据
    
    用于标签布局计算。
    """
    device_id: str              # 设备ID
    x: float                    # 设备X坐标
    y: float                    # 设备Y坐标
    name: str                   # 设备名称（用于估算标签宽度）


class LabelPlacer:
    """
    标签布局服务 - 确定性算法
    
    核心原则：
    1. 同样的输入永远产生同样的输出
    2. 按优先级顺序尝试8个方向
    3. 避开扇形区域和其他已放置的标签
    4. 保留用户手动设置的位置
    """
    
    # 8个方向，按优先级排序
    # 格式: (dx, dy, direction_name)
    # dx, dy 是相对于锚点的偏移量
    DIRECTIONS = [
        (1.2, 0.8, "右上"),      # 首选：右上方
        (-1.2, 0.8, "左上"),     # 次选：左上方
        (1.2, -0.8, "右下"),     # 第三：右下方
        (-1.2, -0.8, "左下"),    # 第四：左下方
        (1.6, 0, "右"),          # 第五：右侧
        (-1.6, 0, "左"),         # 第六：左侧
        (0, 1.2, "上"),          # 第七：上方
        (0, -1.2, "下"),         # 第八：下方
    ]
    
    # 标签尺寸配置 (width, height)
    LABEL_SIZES = {
        "device": (2.0, 0.8),           # 设备信息框
        "measurement": (2.5, 1.2),      # 测量信息框
        "user": (1.8, 0.6),             # 用户位置标记
    }
    
    # 布局参数
    DEFAULT_BORDER_MARGIN = 0.3         # 标签与画布边界的最小距离
    DEFAULT_COLLISION_MARGIN = 0.1      # 标签之间的最小间距
    
    def __init__(self, 
                 border_margin: float = None,
                 collision_margin: float = None):
        """
        初始化标签布局服务
        
        Args:
            border_margin: 标签与画布边界的最小距离
            collision_margin: 标签之间的最小间距
        """
        self.border_margin = border_margin or self.DEFAULT_BORDER_MARGIN
        self.collision_margin = collision_margin or self.DEFAULT_COLLISION_MARGIN
        self.collision_detector = CollisionDetector()
    
    def calculate_positions(self,
                           devices: List[DeviceAnchor],
                           sectors: List[SectorObstacle],
                           coord_range: Tuple[float, float],
                           existing_manual: Dict[str, LabelPosition] = None
                           ) -> Dict[str, LabelPosition]:
        """
        计算所有标签的最佳位置（确定性算法）
        
        这是主入口方法。
        
        Args:
            devices: 设备列表
            sectors: 扇形障碍物列表
            coord_range: 坐标范围 (x_range, y_range)，表示 ±x_range x ±y_range
            existing_manual: 已有的手动位置（不会被覆盖）
        
        Returns:
            element_id -> LabelPosition 的映射
        """
        existing_manual = existing_manual or {}
        result: Dict[str, LabelPosition] = {}
        placed_boxes: List[BoundingBox] = []
        
        # 创建画布边界
        x_range, y_range = coord_range
        canvas_bounds = BoundingBox(-x_range, -y_range, x_range, y_range)
        
        # 按设备ID排序，确保顺序一致（确定性的关键）
        sorted_devices = sorted(devices, key=lambda d: d.device_id)
        
        for device in sorted_devices:
            element_id = f"device_{device.device_id}"
            
            # 如果有手动位置，保留它
            if element_id in existing_manual and existing_manual[element_id].is_manual:
                manual_pos = existing_manual[element_id]
                result[element_id] = manual_pos.copy()
                
                # 将手动位置的边界框添加到已放置列表
                box = self._label_to_bbox(manual_pos.x, manual_pos.y, "device")
                placed_boxes.append(box)
                continue
            
            # 计算最佳自动位置
            position = self._find_best_position(
                anchor_x=device.x,
                anchor_y=device.y,
                label_type="device",
                sectors=sectors,
                placed_boxes=placed_boxes,
                canvas_bounds=canvas_bounds
            )
            
            result[element_id] = position
            
            # 将新位置的边界框添加到已放置列表
            box = self._label_to_bbox(position.x, position.y, "device")
            placed_boxes.append(box)
        
        return result
    
    def calculate_single_position(self,
                                  anchor_x: float,
                                  anchor_y: float,
                                  label_type: str,
                                  sectors: List[SectorObstacle],
                                  existing_boxes: List[BoundingBox],
                                  coord_range: Tuple[float, float]
                                  ) -> LabelPosition:
        """
        计算单个标签的最佳位置
        
        用于实时计算新增标签的位置。
        
        Args:
            anchor_x: 锚点X坐标
            anchor_y: 锚点Y坐标
            label_type: 标签类型 ("device", "measurement", "user")
            sectors: 扇形障碍物列表
            existing_boxes: 已放置的标签边界框列表
            coord_range: 坐标范围
        
        Returns:
            标签位置
        """
        x_range, y_range = coord_range
        canvas_bounds = BoundingBox(-x_range, -y_range, x_range, y_range)
        
        return self._find_best_position(
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            label_type=label_type,
            sectors=sectors,
            placed_boxes=existing_boxes,
            canvas_bounds=canvas_bounds
        )
    
    def _find_best_position(self,
                           anchor_x: float,
                           anchor_y: float,
                           label_type: str,
                           sectors: List[SectorObstacle],
                           placed_boxes: List[BoundingBox],
                           canvas_bounds: BoundingBox) -> LabelPosition:
        """
        为单个标签找最佳位置
        
        按优先级遍历8个方向，返回第一个无冲突的位置。
        
        Args:
            anchor_x: 锚点X坐标
            anchor_y: 锚点Y坐标
            label_type: 标签类型
            sectors: 扇形障碍物列表
            placed_boxes: 已放置的边界框列表
            canvas_bounds: 画布边界
        
        Returns:
            标签位置
        """
        label_width, label_height = self.LABEL_SIZES.get(label_type, (2.0, 0.8))
        
        # 按优先级遍历8个方向
        for dx, dy, direction_name in self.DIRECTIONS:
            candidate_x = anchor_x + dx
            candidate_y = anchor_y + dy
            
            # 创建候选边界框
            candidate_box = BoundingBox.from_center(
                candidate_x, candidate_y, label_width, label_height
            )
            
            # 检查1：是否在画布范围内
            if not CollisionDetector.is_within_bounds(
                candidate_box, canvas_bounds, self.border_margin
            ):
                continue
            
            # 检查2：是否与任何扇形重叠
            if self._overlaps_any_sector(candidate_box, sectors):
                continue
            
            # 检查3：是否与已放置的标签重叠
            if CollisionDetector.overlaps_any(
                candidate_box, placed_boxes, self.collision_margin
            ):
                continue
            
            # 找到有效位置
            return LabelPosition(
                x=candidate_x,
                y=candidate_y,
                is_manual=False,
                direction=direction_name
            )
        
        # 所有方向都不行，尝试扩大搜索范围
        extended_position = self._find_extended_position(
            anchor_x, anchor_y, label_type, sectors, placed_boxes, canvas_bounds
        )
        if extended_position:
            return extended_position
        
        # 仍然找不到，使用默认位置（右上，即使有重叠）
        default_dx, default_dy, default_name = self.DIRECTIONS[0]
        return LabelPosition(
            x=anchor_x + default_dx,
            y=anchor_y + default_dy,
            is_manual=False,
            direction=f"{default_name}(有冲突)"
        )
    
    def _find_extended_position(self,
                               anchor_x: float,
                               anchor_y: float,
                               label_type: str,
                               sectors: List[SectorObstacle],
                               placed_boxes: List[BoundingBox],
                               canvas_bounds: BoundingBox) -> Optional[LabelPosition]:
        """
        扩展搜索：在更远的距离上寻找位置
        
        当8个基本方向都不可用时，尝试更远的位置。
        """
        label_width, label_height = self.LABEL_SIZES.get(label_type, (2.0, 0.8))
        
        # 扩展方向（更远的距离）
        extended_directions = [
            (2.0, 1.2, "远右上"),
            (-2.0, 1.2, "远左上"),
            (2.0, -1.2, "远右下"),
            (-2.0, -1.2, "远左下"),
            (2.2, 0.4, "远右"),
            (-2.2, 0.4, "远左"),
            (0.8, 1.8, "远上"),
            (0.8, -1.8, "远下"),
        ]
        
        for dx, dy, direction_name in extended_directions:
            candidate_x = anchor_x + dx
            candidate_y = anchor_y + dy
            
            candidate_box = BoundingBox.from_center(
                candidate_x, candidate_y, label_width, label_height
            )
            
            if not CollisionDetector.is_within_bounds(
                candidate_box, canvas_bounds, self.border_margin
            ):
                continue
            
            if self._overlaps_any_sector(candidate_box, sectors):
                continue
            
            if CollisionDetector.overlaps_any(
                candidate_box, placed_boxes, self.collision_margin
            ):
                continue
            
            return LabelPosition(
                x=candidate_x,
                y=candidate_y,
                is_manual=False,
                direction=direction_name
            )
        
        return None
    
    def _overlaps_any_sector(self, box: BoundingBox, 
                            sectors: List[SectorObstacle]) -> bool:
        """
        检查边界框是否与任何扇形重叠
        
        Args:
            box: 要检查的边界框
            sectors: 扇形列表
        
        Returns:
            True 如果与任何扇形重叠
        """
        for sector in sectors:
            if CollisionDetector.box_intersects_sector(
                box,
                sector.center_x, sector.center_y,
                sector.radius,
                sector.start_angle_deg, sector.end_angle_deg
            ):
                return True
        return False
    
    def _label_to_bbox(self, center_x: float, center_y: float, 
                      label_type: str) -> BoundingBox:
        """
        将标签位置转换为边界框
        
        Args:
            center_x: 标签中心X坐标
            center_y: 标签中心Y坐标
            label_type: 标签类型
        
        Returns:
            标签的边界框
        """
        width, height = self.LABEL_SIZES.get(label_type, (2.0, 0.8))
        return BoundingBox.from_center(center_x, center_y, width, height)
    
    def validate_manual_position(self,
                                center_x: float,
                                center_y: float,
                                label_type: str,
                                coord_range: Tuple[float, float]) -> bool:
        """
        验证手动设置的位置是否有效
        
        主要检查是否在画布范围内。
        
        Args:
            center_x: 标签中心X坐标
            center_y: 标签中心Y坐标
            label_type: 标签类型
            coord_range: 坐标范围
        
        Returns:
            True 如果位置有效
        """
        x_range, y_range = coord_range
        canvas_bounds = BoundingBox(-x_range, -y_range, x_range, y_range)
        
        label_box = self._label_to_bbox(center_x, center_y, label_type)
        
        # 只检查是否在画布内（允许靠近边界）
        return CollisionDetector.is_within_bounds(
            label_box, canvas_bounds, margin=0.1
        )
    
    def get_label_size(self, label_type: str) -> Tuple[float, float]:
        """
        获取指定类型标签的尺寸
        
        Args:
            label_type: 标签类型
        
        Returns:
            (width, height)
        """
        return self.LABEL_SIZES.get(label_type, (2.0, 0.8))

