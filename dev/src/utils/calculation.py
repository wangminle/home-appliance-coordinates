# -*- coding: utf-8 -*-
"""
数学计算工具模块

提供距离计算、角度计算、坐标转换等数学运算功能
"""

import math
from typing import Tuple, List, Optional


class Calculator:
    """
    数学计算工具类
    
    提供各种数学计算功能，包括距离、角度、坐标转换等
    """
    
    @staticmethod
    def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        计算两点间的欧几里得距离
        
        Args:
            x1, y1: 第一个点的坐标
            x2, y2: 第二个点的坐标
            
        Returns:
            两点间的距离
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    @staticmethod
    def calculate_distance_to_origin(x: float, y: float) -> float:
        """
        计算点到原点的距离
        
        Args:
            x, y: 点的坐标
            
        Returns:
            到原点的距离
        """
        return math.sqrt(x ** 2 + y ** 2)
    
    @staticmethod
    def calculate_min_angle_to_axis(x: float, y: float) -> float:
        """
        计算点与坐标轴的最小夹角
        
        使用与参考HTML相同的算法：
        1. 计算与X轴的夹角：abs(atan(y/x))
        2. 计算与Y轴的夹角：abs(atan(x/y))
        3. 取最小值并转换为度数
        
        Args:
            x, y: 点的坐标
            
        Returns:
            与坐标轴的最小夹角（度数，0-90度）
        """
        # 处理特殊情况
        if x == 0 and y == 0:
            return 0.0
        
        # 计算与X轴的夹角
        if x == 0:
            angle_to_x_rad = math.pi / 2
        else:
            angle_to_x_rad = abs(math.atan(y / x))
        
        # 计算与Y轴的夹角
        if y == 0:
            angle_to_y_rad = math.pi / 2
        else:
            angle_to_y_rad = abs(math.atan(x / y))
        
        # 取最小夹角并转换为度数
        min_angle_rad = min(angle_to_x_rad, angle_to_y_rad)
        return min_angle_rad * 180 / math.pi
    
    @staticmethod
    def calculate_angle_between_points(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        计算从第一个点到第二个点的角度（从X轴正方向逆时针测量）
        
        Args:
            x1, y1: 起始点坐标
            x2, y2: 目标点坐标
            
        Returns:
            角度值（度数，0-360度）
        """
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return 0.0
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 确保角度在0-360度范围内
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    @staticmethod
    def calculate_midpoint(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
        """
        计算两点的中点
        
        Args:
            x1, y1: 第一个点的坐标
            x2, y2: 第二个点的坐标
            
        Returns:
            中点坐标 (x, y)
        """
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    @staticmethod
    def point_in_circle(px: float, py: float, cx: float, cy: float, radius: float) -> bool:
        """
        判断点是否在圆内
        
        Args:
            px, py: 点的坐标
            cx, cy: 圆心坐标
            radius: 圆的半径
            
        Returns:
            True如果点在圆内，否则False
        """
        distance = Calculator.calculate_distance(px, py, cx, cy)
        return distance <= radius
    
    @staticmethod
    def point_in_rectangle(px: float, py: float, x1: float, y1: float, 
                          x2: float, y2: float) -> bool:
        """
        判断点是否在矩形内
        
        Args:
            px, py: 点的坐标
            x1, y1: 矩形第一个角的坐标
            x2, y2: 矩形对角的坐标
            
        Returns:
            True如果点在矩形内，否则False
        """
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return min_x <= px <= max_x and min_y <= py <= max_y
    
    @staticmethod
    def calculate_sector_area(radius: float, angle_degrees: float) -> float:
        """
        计算扇形面积
        
        Args:
            radius: 扇形半径
            angle_degrees: 扇形角度（度数）
            
        Returns:
            扇形面积
        """
        angle_rad = math.radians(angle_degrees)
        return 0.5 * radius * radius * angle_rad
    
    @staticmethod
    def calculate_sector_bounding_box(center_x: float, center_y: float, 
                                    radius: float, start_angle_deg: float, 
                                    end_angle_deg: float) -> Tuple[float, float, float, float]:
        """
        计算扇形的精确边界框
        
        Args:
            center_x, center_y: 扇形中心点坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
            
        Returns:
            边界框 (min_x, min_y, max_x, max_y)
        """
        # 确保角度在0-360度范围内
        start_angle_deg = Calculator.normalize_angle(start_angle_deg)
        end_angle_deg = Calculator.normalize_angle(end_angle_deg)
        
        # 如果结束角度小于起始角度，说明跨越了0度线
        if end_angle_deg < start_angle_deg:
            end_angle_deg += 360
        
        # 计算扇形的关键点
        key_points = [(center_x, center_y)]  # 中心点必须包含
        
        # 添加起始和结束边界线端点
        start_rad = math.radians(start_angle_deg)
        end_rad = math.radians(end_angle_deg)
        
        start_x = center_x + radius * math.cos(start_rad)
        start_y = center_y + radius * math.sin(start_rad)
        end_x = center_x + radius * math.cos(end_rad)
        end_y = center_y + radius * math.sin(end_rad)
        
        key_points.extend([(start_x, start_y), (end_x, end_y)])
        
        # 检查扇形是否包含四个主要方向（0°, 90°, 180°, 270°）
        main_directions = [0, 90, 180, 270]
        for direction in main_directions:
            if start_angle_deg <= direction <= end_angle_deg or \
               start_angle_deg <= direction + 360 <= end_angle_deg:
                dir_rad = math.radians(direction)
                dir_x = center_x + radius * math.cos(dir_rad)
                dir_y = center_y + radius * math.sin(dir_rad)
                key_points.append((dir_x, dir_y))
        
        # 从关键点中找出边界框
        x_coords = [point[0] for point in key_points]
        y_coords = [point[1] for point in key_points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    @staticmethod
    def point_in_sector(px: float, py: float, center_x: float, center_y: float,
                       radius: float, start_angle_deg: float, end_angle_deg: float) -> bool:
        """
        判断点是否在扇形内
        
        Args:
            px, py: 待检测点坐标
            center_x, center_y: 扇形中心点坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
            
        Returns:
            True如果点在扇形内，否则False
        """
        # 首先检查点是否在圆内
        if not Calculator.point_in_circle(px, py, center_x, center_y, radius):
            return False
        
        # 计算点相对于中心的角度
        point_angle_deg = Calculator.calculate_angle_between_points(center_x, center_y, px, py)
        
        # 确保角度在0-360度范围内
        start_angle_deg = Calculator.normalize_angle(start_angle_deg)
        end_angle_deg = Calculator.normalize_angle(end_angle_deg)
        
        # 处理跨越0度线的情况
        if end_angle_deg < start_angle_deg:
            # 角度范围跨越0度线
            return point_angle_deg >= start_angle_deg or point_angle_deg <= end_angle_deg
        else:
            # 正常角度范围
            return start_angle_deg <= point_angle_deg <= end_angle_deg

    @staticmethod
    def sector_rectangle_overlap(center_x: float, center_y: float, radius: float,
                               start_angle_deg: float, end_angle_deg: float,
                               rect_x1: float, rect_y1: float, 
                               rect_x2: float, rect_y2: float) -> float:
        """
        计算扇形与矩形的重叠程度
        
        Args:
            center_x, center_y: 扇形中心点坐标
            radius: 扇形半径
            start_angle_deg: 起始角度（度数）
            end_angle_deg: 结束角度（度数）
            rect_x1, rect_y1: 矩形第一个角坐标
            rect_x2, rect_y2: 矩形对角坐标
            
        Returns:
            重叠比例（0.0-1.0），1.0表示完全重叠
        """
        # 确保矩形坐标正确排序
        min_x, max_x = min(rect_x1, rect_x2), max(rect_x1, rect_x2)
        min_y, max_y = min(rect_y1, rect_y2), max(rect_y1, rect_y2)
        
        # 矩形的四个角点
        rect_corners = [
            (min_x, min_y), (max_x, min_y),
            (max_x, max_y), (min_x, max_y)
        ]
        
        # 检查矩形角点是否在扇形内
        corners_in_sector = 0
        for corner in rect_corners:
            if Calculator.point_in_sector(corner[0], corner[1], center_x, center_y, 
                                        radius, start_angle_deg, end_angle_deg):
                corners_in_sector += 1
        
        # 检查扇形的关键点是否在矩形内
        start_rad = math.radians(start_angle_deg)
        end_rad = math.radians(end_angle_deg)
        
        sector_points = [
            (center_x, center_y),  # 中心点
            (center_x + radius * math.cos(start_rad), center_y + radius * math.sin(start_rad)),  # 起始边端点
            (center_x + radius * math.cos(end_rad), center_y + radius * math.sin(end_rad))  # 结束边端点
        ]
        
        sector_points_in_rect = 0
        for point in sector_points:
            if Calculator.point_in_rectangle(point[0], point[1], min_x, min_y, max_x, max_y):
                sector_points_in_rect += 1
        
        # 基于角点和关键点的重叠情况估算重叠程度
        corner_overlap_ratio = corners_in_sector / 4.0
        sector_overlap_ratio = sector_points_in_rect / 3.0
        
        # 综合重叠度计算（取较大值，因为任一方面有重叠都表示存在冲突）
        overlap_ratio = max(corner_overlap_ratio, sector_overlap_ratio)
        
        # 如果有任何重叠，至少返回最小重叠值
        if overlap_ratio > 0:
            overlap_ratio = max(overlap_ratio, 0.1)  # 最小重叠阈值
        
        return overlap_ratio
    
    @staticmethod
    def rotate_point(x: float, y: float, cx: float, cy: float, angle_degrees: float) -> Tuple[float, float]:
        """
        绕指定点旋转一个点
        
        Args:
            x, y: 要旋转的点的坐标
            cx, cy: 旋转中心的坐标
            angle_degrees: 旋转角度（度数，逆时针为正）
            
        Returns:
            旋转后的点坐标 (x, y)
        """
        angle_rad = math.radians(angle_degrees)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # 平移到原点
        dx = x - cx
        dy = y - cy
        
        # 旋转
        rotated_x = dx * cos_angle - dy * sin_angle
        rotated_y = dx * sin_angle + dy * cos_angle
        
        # 平移回原位置
        return (rotated_x + cx, rotated_y + cy)
    
    @staticmethod
    def normalize_angle(angle_degrees: float) -> float:
        """
        将角度标准化到0-360度范围内
        
        Args:
            angle_degrees: 输入角度（度数）
            
        Returns:
            标准化后的角度（0-360度）
        """
        while angle_degrees < 0:
            angle_degrees += 360
        while angle_degrees >= 360:
            angle_degrees -= 360
        return angle_degrees
    
    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """
        将数值限制在指定范围内
        
        Args:
            value: 输入值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            限制后的值
        """
        return max(min_value, min(value, max_value))
    
    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """
        线性插值
        
        Args:
            start: 起始值
            end: 结束值
            t: 插值参数（0-1）
            
        Returns:
            插值结果
        """
        return start + (end - start) * t
    
    @staticmethod
    def round_to_decimal_places(value: float, decimal_places: int) -> float:
        """
        四舍五入到指定小数位数
        
        Args:
            value: 输入值
            decimal_places: 小数位数
            
        Returns:
            四舍五入后的值
        """
        return round(value, decimal_places)
    
    @staticmethod
    def calculate_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """
        计算点集的边界框
        
        Args:
            points: 点坐标列表 [(x1, y1), (x2, y2), ...]
            
        Returns:
            边界框 (min_x, min_y, max_x, max_y)
            
        Raises:
            ValueError: 当点列表为空时抛出异常
        """
        if not points:
            raise ValueError("点列表不能为空")
        
        x_coords = [point[0] for point in points]
        y_coords = [point[1] for point in points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    @staticmethod
    def is_valid_number(value) -> bool:
        """
        检查值是否为有效数字
        
        Args:
            value: 要检查的值
            
        Returns:
            True如果是有效数字，否则False
        """
        try:
            float_value = float(value)
            return not (math.isnan(float_value) or math.isinf(float_value))
        except (ValueError, TypeError):
            return False 