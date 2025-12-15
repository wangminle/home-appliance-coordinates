# -*- coding: utf-8 -*-
"""
锁定扇形功能测试脚本

测试 V2.4 新增的"说话人方向和影响范围"锁定功能
包括：图钉组件、锁定/解锁状态、对比虚线、夹角和距离计算

测试日期: 2024-12-14
"""

import sys
import os
import math
import unittest
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.locked_measurement import LockedMeasurement


class TestLockedMeasurement(unittest.TestCase):
    """测试 LockedMeasurement 数据模型"""
    
    def setUp(self):
        """测试前准备"""
        self.measurement = LockedMeasurement()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertFalse(self.measurement.is_locked)
        self.assertIsNone(self.measurement.sector_point)
        self.assertIsNone(self.measurement.center_point)
        self.assertFalse(self.measurement.has_data())
        print("✅ 测试初始状态 - 通过")
    
    def test_set_measurement(self):
        """测试设置测量数据"""
        # 设置测量数据
        sector_point = (3.0, 4.0)
        center_point = (0.0, 0.0)
        
        self.measurement.set_measurement(sector_point, center_point)
        
        # 验证数据
        self.assertEqual(self.measurement.sector_point, sector_point)
        self.assertEqual(self.measurement.center_point, center_point)
        self.assertTrue(self.measurement.has_data())
        
        # 验证计算属性
        # 距离应该是5.0（勾股定理：3^2 + 4^2 = 25）
        self.assertAlmostEqual(self.measurement.line_distance, 5.0, places=5)
        
        # 角度应该是53.13度（arctan(4/3) ≈ 53.13°）
        expected_angle = math.degrees(math.atan2(4.0, 3.0))
        self.assertAlmostEqual(self.measurement.line_angle, expected_angle, places=5)
        
        # 图钉位置应该在双击点正上方0.8个单位
        expected_pin = (3.0, 4.0 + 0.8)
        self.assertEqual(self.measurement.pin_position, expected_pin)
        
        print("✅ 测试设置测量数据 - 通过")
    
    def test_lock_unlock_toggle(self):
        """测试锁定/解锁/切换功能"""
        # 初始状态：解锁
        self.assertFalse(self.measurement.is_locked)
        
        # 锁定
        self.measurement.lock()
        self.assertTrue(self.measurement.is_locked)
        self.assertIsNotNone(self.measurement.locked_time)
        
        # 解锁
        self.measurement.unlock()
        self.assertFalse(self.measurement.is_locked)
        self.assertIsNone(self.measurement.locked_time)
        
        # 切换（解锁 -> 锁定）
        new_state = self.measurement.toggle_lock()
        self.assertTrue(new_state)
        self.assertTrue(self.measurement.is_locked)
        
        # 切换（锁定 -> 解锁）
        new_state = self.measurement.toggle_lock()
        self.assertFalse(new_state)
        self.assertFalse(self.measurement.is_locked)
        
        print("✅ 测试锁定/解锁/切换功能 - 通过")
    
    def test_calculate_comparison(self):
        """测试对比计算功能"""
        # 设置锁定的测量数据
        self.measurement.set_measurement((3.0, 4.0), (0.0, 0.0))
        self.measurement.lock()
        
        # 测试用例1：同方向的点（夹角为0）
        new_point1 = (6.0, 8.0)  # 同一条线上
        comparison1 = self.measurement.calculate_comparison(new_point1)
        self.assertAlmostEqual(comparison1['angle_diff'], 0.0, places=3)
        self.assertAlmostEqual(comparison1['new_distance'], 10.0, places=5)  # 距离 = sqrt(6^2 + 8^2) = 10
        
        # 测试用例2：垂直方向的点（夹角约90度）
        # 原始角度约53.13度，选择一个夹角约90度的点
        new_point2 = (-4.0, 3.0)  # 角度约143.13度
        comparison2 = self.measurement.calculate_comparison(new_point2)
        self.assertAlmostEqual(comparison2['angle_diff'], 90.0, places=3)
        
        # 测试用例3：反方向的点（夹角为180度）
        new_point3 = (-3.0, -4.0)
        comparison3 = self.measurement.calculate_comparison(new_point3)
        self.assertAlmostEqual(comparison3['angle_diff'], 180.0, places=3)
        
        print("✅ 测试对比计算功能 - 通过")
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        # 设置数据
        self.measurement.set_measurement((3.0, 4.0), (0.0, 0.0))
        self.measurement.lock()
        
        # 序列化
        data = self.measurement.to_dict()
        
        # 验证字典内容
        self.assertEqual(data['sector_point'], [3.0, 4.0])
        self.assertEqual(data['center_point'], [0.0, 0.0])
        self.assertTrue(data['is_locked'])
        self.assertIsNotNone(data['line_angle'])
        self.assertIsNotNone(data['line_distance'])
        
        # 反序列化
        restored = LockedMeasurement.from_dict(data)
        
        # 验证恢复后的数据
        self.assertEqual(restored.sector_point, (3.0, 4.0))
        self.assertEqual(restored.center_point, (0.0, 0.0))
        self.assertTrue(restored.is_locked)
        self.assertAlmostEqual(restored.line_angle, self.measurement.line_angle, places=5)
        self.assertAlmostEqual(restored.line_distance, self.measurement.line_distance, places=5)
        
        print("✅ 测试序列化和反序列化 - 通过")
    
    def test_clear(self):
        """测试清除功能"""
        # 设置数据
        self.measurement.set_measurement((3.0, 4.0), (0.0, 0.0))
        self.measurement.lock()
        
        # 验证有数据
        self.assertTrue(self.measurement.has_data())
        self.assertTrue(self.measurement.is_locked)
        
        # 清除
        self.measurement.clear()
        
        # 验证已清除
        self.assertFalse(self.measurement.has_data())
        self.assertFalse(self.measurement.is_locked)
        self.assertIsNone(self.measurement.sector_point)
        self.assertIsNone(self.measurement.center_point)
        
        print("✅ 测试清除功能 - 通过")
    
    def test_user_coordinate_system(self):
        """测试用户坐标系模式下的测量"""
        # 用户坐标系中心点不在原点
        user_position = (2.0, 2.0)
        sector_point = (5.0, 6.0)  # 相对于用户位置: (3.0, 4.0)
        
        self.measurement.set_measurement(sector_point, user_position)
        
        # 验证距离（相对于用户位置）
        # sqrt((5-2)^2 + (6-2)^2) = sqrt(9 + 16) = 5
        self.assertAlmostEqual(self.measurement.line_distance, 5.0, places=5)
        
        # 验证角度（相对于用户位置）
        expected_angle = math.degrees(math.atan2(6.0 - 2.0, 5.0 - 2.0))  # atan2(4, 3)
        self.assertAlmostEqual(self.measurement.line_angle, expected_angle, places=5)
        
        print("✅ 测试用户坐标系模式 - 通过")
    
    def test_angle_edge_cases(self):
        """测试角度计算的边界情况"""
        # 测试X轴正方向（0度）
        self.measurement.set_measurement((5.0, 0.0), (0.0, 0.0))
        self.assertAlmostEqual(self.measurement.line_angle, 0.0, places=5)
        
        # 测试Y轴正方向（90度）
        self.measurement.set_measurement((0.0, 5.0), (0.0, 0.0))
        self.assertAlmostEqual(self.measurement.line_angle, 90.0, places=5)
        
        # 测试X轴负方向（180度）
        self.measurement.set_measurement((-5.0, 0.0), (0.0, 0.0))
        self.assertAlmostEqual(self.measurement.line_angle, 180.0, places=5)
        
        # 测试Y轴负方向（270度）
        self.measurement.set_measurement((0.0, -5.0), (0.0, 0.0))
        self.assertAlmostEqual(self.measurement.line_angle, 270.0, places=5)
        
        print("✅ 测试角度边界情况 - 通过")


class TestLockedMeasurementIntegration(unittest.TestCase):
    """集成测试：测试与其他模块的交互"""
    
    def test_sector_angle_calculation(self):
        """测试扇形角度计算"""
        measurement = LockedMeasurement()
        measurement.set_measurement((3.0, 4.0), (0.0, 0.0), sector_angle_span=90.0)
        
        # 中心角度约53.13度
        center_angle = measurement.line_angle
        
        # 扇形起始角度 = 中心角度 - 45度
        # 扇形结束角度 = 中心角度 + 45度
        expected_start = center_angle - 45.0
        expected_end = center_angle + 45.0
        
        self.assertAlmostEqual(measurement.sector_start_angle, expected_start, places=5)
        self.assertAlmostEqual(measurement.sector_end_angle, expected_end, places=5)
        
        print("✅ 测试扇形角度计算 - 通过")
    
    def test_comparison_with_different_distances(self):
        """测试不同距离的对比"""
        measurement = LockedMeasurement()
        measurement.set_measurement((3.0, 4.0), (0.0, 0.0))
        measurement.lock()
        
        # 同方向，但距离不同
        near_point = (1.5, 2.0)  # 距离 = 2.5
        far_point = (9.0, 12.0)  # 距离 = 15
        
        near_comparison = measurement.calculate_comparison(near_point)
        far_comparison = measurement.calculate_comparison(far_point)
        
        # 夹角应该相同（同一方向）
        self.assertAlmostEqual(near_comparison['angle_diff'], 0.0, places=3)
        self.assertAlmostEqual(far_comparison['angle_diff'], 0.0, places=3)
        
        # 距离应该不同
        self.assertAlmostEqual(near_comparison['new_distance'], 2.5, places=5)
        self.assertAlmostEqual(far_comparison['new_distance'], 15.0, places=5)
        
        print("✅ 测试不同距离的对比 - 通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 开始测试锁定扇形功能 (V2.4)")
    print("=" * 60)
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestLockedMeasurement))
    suite.addTests(loader.loadTestsFromTestCase(TestLockedMeasurementIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    
    # 输出结果
    if result.wasSuccessful():
        print("🎉 所有测试通过!")
        print(f"   - 测试用例数: {result.testsRun}")
        print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    else:
        print("❌ 存在失败的测试!")
        print(f"   - 测试用例数: {result.testsRun}")
        print(f"   - 失败: {len(result.failures)}")
        print(f"   - 错误: {len(result.errors)}")
        
        if result.failures:
            print("\n失败的测试:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace}")
        
        if result.errors:
            print("\n错误的测试:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace}")
    
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
