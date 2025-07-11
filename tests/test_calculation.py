# -*- coding: utf-8 -*-
"""
计算模块单元测试

测试Calculator类的各种数学计算功能
"""

import pytest
import math
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from utils.calculation import Calculator


class TestCalculator:
    """计算工具测试类"""
    
    def test_distance_calculation(self):
        """测试距离计算"""
        # 简单距离计算
        distance = Calculator.calculate_distance(0, 0, 3, 4)
        assert abs(distance - 5.0) < 1e-10
        
        # 相同点
        distance = Calculator.calculate_distance(1, 2, 1, 2)
        assert abs(distance) < 1e-10
    
    def test_min_angle_to_axis(self):
        """测试与坐标轴最小夹角计算"""
        # 45度角点
        angle = Calculator.calculate_min_angle_to_axis(1, 1)
        assert abs(angle - 45.0) < 1e-10
        
        # X轴上的点
        angle = Calculator.calculate_min_angle_to_axis(1, 0)
        assert abs(angle) < 1e-10
        
        # 原点
        angle = Calculator.calculate_min_angle_to_axis(0, 0)
        assert abs(angle) < 1e-10
    
    def test_number_validation(self):
        """测试数字有效性检查"""
        assert Calculator.is_valid_number(42)
        assert Calculator.is_valid_number(3.14)
        assert Calculator.is_valid_number("123")
        
        assert not Calculator.is_valid_number("not_a_number")
        assert not Calculator.is_valid_number(None)


if __name__ == "__main__":
    pytest.main([__file__]) 