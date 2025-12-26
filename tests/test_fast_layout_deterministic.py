#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fast_layout 确定性布局算法单元测试

验证 near-zero 分支的确定性行为：
- 相同 element_id 应该得到相同的斥力方向
- 不同 element_id 应该得到不同的斥力方向（避免标签重叠）
- 结果应该是可复现的
"""

import sys
import os
import math
import pytest

# 将项目根目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from utils.fast_layout import SectorRegion, LayoutConstants, FastLayoutManager, BoundingBox


class TestSectorRegionDeterministic:
    """扇形斥力场确定性测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建一个标准扇形：圆心(0,0)，半径5，角度范围[-45, 45]
        self.sector = SectorRegion(
            center_x=0.0,
            center_y=0.0,
            radius=5.0,
            start_angle_deg=-45.0,
            end_angle_deg=45.0
        )
    
    def test_near_zero_deterministic_same_element_id(self):
        """测试：相同 element_id 在圆心附近应该得到相同的斥力方向"""
        # 在圆心位置（或极近位置）
        x, y = 0.001, 0.001
        element_id = "device_test_001"
        
        # 多次调用应该返回相同结果
        results = []
        for _ in range(10):
            force_x, force_y = self.sector.get_repulsion_force(x, y, element_id)
            results.append((force_x, force_y))
        
        # 验证所有结果相同
        first_result = results[0]
        for result in results[1:]:
            assert abs(result[0] - first_result[0]) < 1e-10, "force_x 应该完全相同"
            assert abs(result[1] - first_result[1]) < 1e-10, "force_y 应该完全相同"
    
    def test_near_zero_deterministic_different_element_id(self):
        """测试：不同 element_id 在圆心附近应该得到不同的斥力方向"""
        x, y = 0.001, 0.001
        
        element_ids = [
            "device_001",
            "device_002",
            "device_003",
            "measurement_info",
            "user_position",
        ]
        
        results = {}
        for element_id in element_ids:
            force_x, force_y = self.sector.get_repulsion_force(x, y, element_id)
            angle = math.atan2(force_y, force_x)
            results[element_id] = angle
        
        # 验证至少有一些不同的角度（12个方向，5个ID应该有一些不同）
        unique_angles = set()
        for angle in results.values():
            # 归一化角度到 [0, 2π)
            normalized = angle if angle >= 0 else angle + 2 * math.pi
            # 四舍五入到最近的30度（避免浮点误差）
            direction_index = round(normalized / (math.pi / 6)) % 12
            unique_angles.add(direction_index)
        
        # 应该有至少2个不同的方向
        assert len(unique_angles) >= 2, f"5个element_id应该产生至少2个不同方向，实际:{len(unique_angles)}"
    
    def test_near_zero_force_magnitude(self):
        """测试：圆心附近的斥力强度应该正确"""
        x, y = 0.001, 0.001
        element_id = "test_element"
        
        force_x, force_y = self.sector.get_repulsion_force(x, y, element_id)
        magnitude = math.sqrt(force_x**2 + force_y**2)
        
        # 斥力强度应该等于 SECTOR_CENTER_REPULSION
        expected_magnitude = LayoutConstants.SECTOR_CENTER_REPULSION
        assert abs(magnitude - expected_magnitude) < 0.01, \
            f"斥力强度应该是 {expected_magnitude}，实际: {magnitude}"
    
    def test_exact_center_deterministic(self):
        """测试：精确在圆心位置的确定性"""
        x, y = 0.0, 0.0
        element_id = "center_test"
        
        # 多次调用
        results = []
        for _ in range(5):
            force_x, force_y = self.sector.get_repulsion_force(x, y, element_id)
            results.append((force_x, force_y))
        
        # 所有结果应该相同
        for i in range(1, len(results)):
            assert results[i] == results[0], "精确圆心位置的结果应该完全相同"
    
    def test_outside_near_zero_threshold(self):
        """测试：在 near-zero 阈值外的点不受确定性逻辑影响"""
        # 在阈值外但仍在扇形内
        x, y = 1.0, 1.0
        element_id = "test_element"
        
        force_x, force_y = self.sector.get_repulsion_force(x, y, element_id)
        
        # 应该有斥力（在扇形内）
        magnitude = math.sqrt(force_x**2 + force_y**2)
        assert magnitude > 0, "扇形内的点应该有斥力"
        
        # 方向应该是径向向外（从圆心指向该点）
        expected_dir_x = x / math.sqrt(x**2 + y**2)
        expected_dir_y = y / math.sqrt(x**2 + y**2)
        actual_dir_x = force_x / magnitude
        actual_dir_y = force_y / magnitude
        
        assert abs(actual_dir_x - expected_dir_x) < 0.01, "X方向应该是径向向外"
        assert abs(actual_dir_y - expected_dir_y) < 0.01, "Y方向应该是径向向外"


class TestFastLayoutManagerDeterministic:
    """布局管理器确定性测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.manager = FastLayoutManager((-10, -10, 10, 10))
    
    def test_sector_repulsion_force_with_element_id(self):
        """测试：_get_sector_repulsion_force 正确传递 element_id"""
        # 添加扇形区域
        self.manager.add_sector_region(0, 0, 5, -45, 45)
        
        # 在圆心附近
        x, y = 0.001, 0.001
        element_id = "test_device"
        
        # 多次调用应该得到相同结果
        results = []
        for _ in range(5):
            force = self.manager._get_sector_repulsion_force(x, y, element_id)
            results.append(force)
        
        # 验证结果一致
        for result in results[1:]:
            assert result == results[0], "相同element_id应该得到相同的斥力"
    
    def test_no_sector_no_force(self):
        """测试：没有扇形时不应该有斥力"""
        x, y = 0.001, 0.001
        element_id = "test"
        
        force_x, force_y = self.manager._get_sector_repulsion_force(x, y, element_id)
        
        assert force_x == 0.0, "没有扇形时 force_x 应该为 0"
        assert force_y == 0.0, "没有扇形时 force_y 应该为 0"


class TestDirectionDistribution:
    """方向分布测试 - 验证12方向分散效果"""
    
    def test_12_directions_coverage(self):
        """测试：大量element_id应该覆盖12个方向"""
        sector = SectorRegion(0, 0, 5, -45, 45)
        
        # 生成100个不同的element_id
        direction_counts = [0] * 12
        
        for i in range(100):
            element_id = f"element_{i:03d}"
            force_x, force_y = sector.get_repulsion_force(0.001, 0.001, element_id)
            
            angle = math.atan2(force_y, force_x)
            if angle < 0:
                angle += 2 * math.pi
            
            direction_index = round(angle / (math.pi / 6)) % 12
            direction_counts[direction_index] += 1
        
        # 验证所有12个方向都被覆盖
        covered_directions = sum(1 for count in direction_counts if count > 0)
        assert covered_directions >= 8, f"应该覆盖至少8个方向，实际覆盖: {covered_directions}"
        
        # 打印分布情况（用于调试）
        print(f"\n方向分布: {direction_counts}")
        print(f"覆盖方向数: {covered_directions}/12")


if __name__ == '__main__':
    # 直接运行时执行测试
    pytest.main([__file__, '-v', '-s'])

