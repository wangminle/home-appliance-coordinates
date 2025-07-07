# -*- coding: utf-8 -*-
"""
坐标系统数据模型

定义坐标系统的数据结构和坐标转换功能
"""

from typing import Tuple, Optional


class CoordinateSystem:
    """
    坐标系统模型类
    
    管理逻辑坐标与Canvas像素坐标之间的转换
    """
    
    def __init__(self, x_range: float = 10.0, y_range: float = 10.0, 
                 canvas_width: int = 800, canvas_height: int = 800):
        """
        初始化坐标系统
        
        Args:
            x_range: X轴显示范围（±x_range）
            y_range: Y轴显示范围（±y_range）
            canvas_width: Canvas画布宽度
            canvas_height: Canvas画布高度
        """
        self.x_range = x_range
        self.y_range = y_range
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # 计算坐标范围
        self.x_min = -x_range
        self.x_max = x_range
        self.y_min = -y_range
        self.y_max = y_range
        
        # 画布边距
        self.padding = 60
        
        # 计算绘图区域尺寸
        self.graph_width = canvas_width - 2 * self.padding
        self.graph_height = canvas_height - 2 * self.padding
        
        # 计算缩放比例和原点位置
        self._calculate_scale_and_origin()
        
        # 验证参数有效性
        self._validate()
    
    def _calculate_scale_and_origin(self):
        """
        计算缩放比例和原点位置
        """
        # 计算X和Y方向的缩放比例
        x_scale = self.graph_width / (self.x_max - self.x_min)
        y_scale = self.graph_height / (self.y_max - self.y_min)
        
        # 使用较小的缩放比例确保比例一致
        self.scale = min(x_scale, y_scale)
        
        # 计算原点在Canvas中的位置
        self.origin_x = self.padding - self.x_min * self.scale
        self.origin_y = self.padding + self.y_max * self.scale
    
    def _validate(self):
        """
        验证坐标系统参数的有效性
        
        Raises:
            ValueError: 当参数不符合要求时抛出异常
        """
        if self.x_range <= 0 or self.y_range <= 0:
            raise ValueError("坐标范围必须大于0")
        
        if self.x_range < 0.1 or self.x_range > 50:
            raise ValueError("X轴范围必须在0.1-50之间")
        
        if self.y_range < 0.1 or self.y_range > 50:
            raise ValueError("Y轴范围必须在0.1-50之间")
        
        if self.canvas_width <= 0 or self.canvas_height <= 0:
            raise ValueError("Canvas尺寸必须大于0")
    
    def set_range(self, x_range: float, y_range: float):
        """
        设置新的坐标显示范围
        
        Args:
            x_range: 新的X轴范围
            y_range: 新的Y轴范围
        """
        self.x_range = x_range
        self.y_range = y_range
        
        # 重新计算坐标范围
        self.x_min = -x_range
        self.x_max = x_range
        self.y_min = -y_range
        self.y_max = y_range
        
        # 重新计算缩放和原点
        self._calculate_scale_and_origin()
        
        # 验证新参数
        self._validate()
    
    def set_canvas_size(self, width: int, height: int):
        """
        设置Canvas画布尺寸
        
        Args:
            width: 画布宽度
            height: 画布高度
        """
        self.canvas_width = width
        self.canvas_height = height
        
        # 重新计算绘图区域
        self.graph_width = width - 2 * self.padding
        self.graph_height = height - 2 * self.padding
        
        # 重新计算缩放和原点
        self._calculate_scale_and_origin()
        
        # 验证新参数
        self._validate()
    
    def to_canvas_coords(self, x: float, y: float) -> Tuple[float, float]:
        """
        将逻辑坐标转换为Canvas像素坐标
        
        Args:
            x: 逻辑X坐标
            y: 逻辑Y坐标
            
        Returns:
            Canvas坐标元组 (canvas_x, canvas_y)
        """
        canvas_x = self.origin_x + x * self.scale
        canvas_y = self.origin_y - y * self.scale  # Y轴翻转
        return (canvas_x, canvas_y)
    
    def from_canvas_coords(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
        """
        将Canvas像素坐标转换为逻辑坐标
        
        Args:
            canvas_x: Canvas X坐标
            canvas_y: Canvas Y坐标
            
        Returns:
            逻辑坐标元组 (x, y)
        """
        x = (canvas_x - self.origin_x) / self.scale
        y = (self.origin_y - canvas_y) / self.scale  # Y轴翻转
        return (x, y)
    
    def is_point_in_range(self, x: float, y: float) -> bool:
        """
        检查点是否在坐标系统显示范围内
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            True如果点在范围内，否则False
        """
        return (self.x_min <= x <= self.x_max and 
                self.y_min <= y <= self.y_max)
    
    def is_canvas_point_in_graph(self, canvas_x: float, canvas_y: float) -> bool:
        """
        检查Canvas坐标点是否在绘图区域内
        
        Args:
            canvas_x: Canvas X坐标
            canvas_y: Canvas Y坐标
            
        Returns:
            True如果点在绘图区域内，否则False
        """
        return (self.padding <= canvas_x <= self.canvas_width - self.padding and
                self.padding <= canvas_y <= self.canvas_height - self.padding)
    
    def get_grid_lines(self) -> Tuple[list, list]:
        """
        获取网格线的坐标
        
        Returns:
            (垂直线列表, 水平线列表)，每条线用两个端点表示
        """
        vertical_lines = []
        horizontal_lines = []
        
        # 垂直网格线
        for x in range(int(self.x_min), int(self.x_max) + 1):
            if x != 0:  # 排除坐标轴
                start_x, start_y = self.to_canvas_coords(x, self.y_min)
                end_x, end_y = self.to_canvas_coords(x, self.y_max)
                vertical_lines.append([(start_x, start_y), (end_x, end_y)])
        
        # 水平网格线  
        for y in range(int(self.y_min), int(self.y_max) + 1):
            if y != 0:  # 排除坐标轴
                start_x, start_y = self.to_canvas_coords(self.x_min, y)
                end_x, end_y = self.to_canvas_coords(self.x_max, y)
                horizontal_lines.append([(start_x, start_y), (end_x, end_y)])
        
        return vertical_lines, horizontal_lines
    
    def get_axis_lines(self) -> Tuple[list, list]:
        """
        获取坐标轴线的坐标
        
        Returns:
            (X轴线坐标, Y轴线坐标)
        """
        # X轴线
        x_axis_start = self.to_canvas_coords(self.x_min, 0)
        x_axis_end = self.to_canvas_coords(self.x_max, 0)
        x_axis = [x_axis_start, x_axis_end]
        
        # Y轴线
        y_axis_start = self.to_canvas_coords(0, self.y_min)
        y_axis_end = self.to_canvas_coords(0, self.y_max)
        y_axis = [y_axis_start, y_axis_end]
        
        return x_axis, y_axis
    
    def get_tick_labels(self) -> Tuple[list, list]:
        """
        获取刻度标签的位置和信息 (增强版)
        
        Returns:
            (X轴刻度列表, Y轴刻度列表)
            每个刻度是一个字典: {'pos': (x, y), 'text': str, 'anchor': str}
        """
        x_ticks = []
        y_ticks = []
        
        # X轴刻度
        for x in range(int(self.x_min), int(self.x_max) + 1):
            if x != 0:
                canvas_x, canvas_y = self.to_canvas_coords(x, 0)
                x_ticks.append({
                    'pos': (canvas_x, canvas_y + 5), 
                    'text': str(x),
                    'anchor': 'n'
                })
        
        # Y轴刻度
        for y in range(int(self.y_min), int(self.y_max) + 1):
            if y != 0:
                canvas_x, canvas_y = self.to_canvas_coords(0, y)
                y_ticks.append({
                    'pos': (canvas_x - 5, canvas_y),
                    'text': str(y),
                    'anchor': 'e'
                })
                
        return x_ticks, y_ticks

    def get_origin_label_info(self) -> dict:
        """
        获取原点 '0' 标签的信息
        """
        canvas_x, canvas_y = self.to_canvas_coords(0, 0)
        return {
            'pos': (canvas_x - 5, canvas_y + 5),
            'text': '0',
            'anchor': 'ne'
        }

    def get_origin_position(self) -> Tuple[float, float]:
        """
        获取原点在Canvas中的位置
        
        Returns:
            原点的Canvas坐标 (canvas_x, canvas_y)
        """
        return self.to_canvas_coords(0, 0)
    
    def get_x_scale(self) -> float:
        """
        获取X方向的缩放比例
        
        Returns:
            缩放比例 (像素/逻辑单位)
        """
        return self.scale
    
    def get_graph_canvas_rect(self) -> tuple:
        """
        获取绘图区域的Canvas坐标范围
        
        Returns:
            (x_min, y_min, x_max, y_max) 绘图区域边界
        """
        return (self.padding, self.padding, 
                self.canvas_width - self.padding, 
                self.canvas_height - self.padding)
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"CoordinateSystem(x_range=±{self.x_range}, y_range=±{self.y_range}, "
                f"canvas_size={self.canvas_width}x{self.canvas_height})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"CoordinateSystem(x_range={self.x_range}, y_range={self.y_range}, "
                f"canvas_width={self.canvas_width}, canvas_height={self.canvas_height}, "
                f"scale={self.scale:.2f}, origin=({self.origin_x:.1f}, {self.origin_y:.1f}))") 