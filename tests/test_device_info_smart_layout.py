#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备信息框智能避让系统测试

测试设备点信息框的四个候选位置智能避让功能：
1. 四个候选位置的正确性
2. 优先级策略的实现
3. 冲突检测和避让
4. 右键清除恢复默认位置
"""

import sys
import os
import unittest
import math

# 添加dev目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.device_model import Device
from utils.layout_manager import LayoutManager, ElementType, LayoutElement, BoundingBox, DeviceInfoPosition


class TestDeviceInfoSmartLayout(unittest.TestCase):
    """设备信息框智能避让系统测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.layout_manager = LayoutManager((-10, -10, 10, 10))
        
        # 创建测试设备
        self.device_left = Device("左侧设备", -5.0, 3.0)
        self.device_right = Device("右侧设备", 5.0, 3.0)
        self.device_origin = Device("原点设备", 0.0, 0.0)
        
    def test_device_position_enum(self):
        """测试设备位置枚举"""
        print("\n=== 测试设备位置枚举 ===")
        
        positions = [
            DeviceInfoPosition.TOP_LEFT,
            DeviceInfoPosition.TOP_RIGHT,
            DeviceInfoPosition.BOTTOM_LEFT,
            DeviceInfoPosition.BOTTOM_RIGHT
        ]
        
        for pos in positions:
            print(f"✓ 位置枚举: {pos.value}")
            self.assertIsInstance(pos.value, str)
        
        print("✅ 设备位置枚举测试通过")
    
    def test_device_default_position_calculation(self):
        """测试设备默认位置计算"""
        print("\n=== 测试设备默认位置计算 ===")
        
        # 测试左侧设备（应使用左上角）
        default_x, default_y, default_pos = self.layout_manager.get_device_default_position(-5.0, 3.0)
        print(f"左侧设备 (-5.0, 3.0) 默认位置: ({default_x:.1f}, {default_y:.1f}) -> {default_pos.value}")
        self.assertEqual(default_pos, DeviceInfoPosition.TOP_LEFT)
        self.assertAlmostEqual(default_x, -6.5, places=1)  # -5.0 + (-1.5)
        self.assertAlmostEqual(default_y, 4.0, places=1)   # 3.0 + 1.0
        
        # 测试右侧设备（应使用右上角）
        default_x, default_y, default_pos = self.layout_manager.get_device_default_position(5.0, 3.0)
        print(f"右侧设备 (5.0, 3.0) 默认位置: ({default_x:.1f}, {default_y:.1f}) -> {default_pos.value}")
        self.assertEqual(default_pos, DeviceInfoPosition.TOP_RIGHT)
        self.assertAlmostEqual(default_x, 6.5, places=1)   # 5.0 + 1.5
        self.assertAlmostEqual(default_y, 4.0, places=1)   # 3.0 + 1.0
        
        # 测试原点设备（应使用右上角，因为 0 >= 0）
        default_x, default_y, default_pos = self.layout_manager.get_device_default_position(0.0, 0.0)
        print(f"原点设备 (0.0, 0.0) 默认位置: ({default_x:.1f}, {default_y:.1f}) -> {default_pos.value}")
        self.assertEqual(default_pos, DeviceInfoPosition.TOP_RIGHT)
        
        print("✅ 设备默认位置计算测试通过")
    
    def test_priority_order_strategy(self):
        """测试优先级策略"""
        print("\n=== 测试优先级策略 ===")
        
        # 测试左侧设备的优先级顺序
        left_x, left_y, left_pos = self.layout_manager.calculate_device_info_position(-5.0, 3.0)
        print(f"左侧设备优先级选择: {left_pos.value}")
        
        # 测试右侧设备的优先级顺序
        right_x, right_y, right_pos = self.layout_manager.calculate_device_info_position(5.0, 3.0)
        print(f"右侧设备优先级选择: {right_pos.value}")
        
        # 在没有冲突的情况下，应该选择默认位置
        self.assertEqual(left_pos, DeviceInfoPosition.TOP_LEFT)
        self.assertEqual(right_pos, DeviceInfoPosition.TOP_RIGHT)
        
        print("✅ 优先级策略测试通过")
    
    def test_conflict_detection_and_avoidance(self):
        """测试冲突检测和避让"""
        print("\n=== 测试冲突检测和避让 ===")
        
        # 添加一个障碍元素到左上角位置
        obstacle_bbox = BoundingBox(-7.0, 3.5, -6.0, 4.5)
        obstacle_element = LayoutElement(
            ElementType.MEASUREMENT_INFO, obstacle_bbox, (-6.5, 4.0),
            priority=9, movable=False, element_id="obstacle"
        )
        self.layout_manager.add_element(obstacle_element)
        
        # 现在计算左侧设备的位置，应该避开障碍物
        avoid_x, avoid_y, avoid_pos = self.layout_manager.calculate_device_info_position(-5.0, 3.0)
        print(f"左侧设备避让后位置: ({avoid_x:.1f}, {avoid_y:.1f}) -> {avoid_pos.value}")
        
        # 应该不再是左上角位置
        self.assertNotEqual(avoid_pos, DeviceInfoPosition.TOP_LEFT)
        
        # 检查是否确实避开了冲突区域
        device_bbox = BoundingBox(avoid_x - 1.25, avoid_y - 0.6, avoid_x + 1.25, avoid_y + 0.6)
        self.assertFalse(device_bbox.overlaps(obstacle_bbox), "设备信息框仍与障碍物重叠")
        
        print("✅ 冲突检测和避让测试通过")
    
    def test_device_position_state_management(self):
        """测试设备位置状态管理"""
        print("\n=== 测试设备位置状态管理 ===")
        
        # 初始状态
        device = Device("测试设备", 2.0, 2.0)
        print(f"初始状态: {device.get_info_position_status()}")
        self.assertIsNone(device.current_info_position)
        self.assertIsNone(device.default_info_position)
        self.assertFalse(device.is_info_position_forced)
        
        # 设置默认位置
        device.set_info_position(DeviceInfoPosition.TOP_RIGHT, is_forced=False)
        print(f"设置默认位置后: {device.get_info_position_status()}")
        self.assertEqual(device.current_info_position, DeviceInfoPosition.TOP_RIGHT)
        self.assertEqual(device.default_info_position, DeviceInfoPosition.TOP_RIGHT)
        self.assertFalse(device.is_info_position_forced)
        
        # 强制切换到其他位置
        device.set_info_position(DeviceInfoPosition.BOTTOM_LEFT, is_forced=True)
        print(f"强制切换后: {device.get_info_position_status()}")
        self.assertEqual(device.current_info_position, DeviceInfoPosition.BOTTOM_LEFT)
        self.assertEqual(device.default_info_position, DeviceInfoPosition.TOP_RIGHT)  # 默认位置不变
        self.assertTrue(device.is_info_position_forced)
        
        # 重置到默认位置
        device.reset_info_position_to_default()
        print(f"重置后: {device.get_info_position_status()}")
        self.assertEqual(device.current_info_position, DeviceInfoPosition.TOP_RIGHT)
        self.assertEqual(device.default_info_position, DeviceInfoPosition.TOP_RIGHT)
        self.assertFalse(device.is_info_position_forced)
        
        print("✅ 设备位置状态管理测试通过")
    
    def test_device_serialization_with_position(self):
        """测试设备序列化包含位置信息"""
        print("\n=== 测试设备序列化包含位置信息 ===")
        
        # 创建并设置位置的设备
        device = Device("序列化测试", 3.0, 4.0)
        device.set_info_position(DeviceInfoPosition.BOTTOM_RIGHT, is_forced=True)
        
        # 序列化到字典
        device_dict = device.to_dict()
        print(f"序列化结果: {device_dict}")
        
        # 检查位置信息是否被保存
        self.assertEqual(device_dict['current_info_position'], 'bottom_right')
        self.assertIsNone(device_dict['default_info_position'])  # 没有设置默认位置
        self.assertTrue(device_dict['is_info_position_forced'])
        
        # 从字典恢复设备
        restored_device = Device.from_dict(device_dict)
        print(f"恢复后状态: {restored_device.get_info_position_status()}")
        
        # 检查位置信息是否被正确恢复
        self.assertEqual(restored_device.current_info_position, DeviceInfoPosition.BOTTOM_RIGHT)
        self.assertIsNone(restored_device.default_info_position)
        self.assertTrue(restored_device.is_info_position_forced)
        
        print("✅ 设备序列化包含位置信息测试通过")
    
    def test_canvas_bounds_checking(self):
        """测试画布边界检查"""
        print("\n=== 测试画布边界检查 ===")
        
        # 测试边界外的设备
        edge_x, edge_y, edge_pos = self.layout_manager.calculate_device_info_position(9.0, 9.0)
        print(f"边界设备位置: ({edge_x:.1f}, {edge_y:.1f}) -> {edge_pos.value}")
        
        # 检查是否在边界内
        self.assertGreaterEqual(edge_x, -9.8)  # 考虑边距
        self.assertLessEqual(edge_x, 9.8)
        self.assertGreaterEqual(edge_y, -9.8)
        self.assertLessEqual(edge_y, 9.8)
        
        print("✅ 画布边界检查测试通过")
    
    def test_multiple_devices_layout(self):
        """测试多设备布局协调"""
        print("\n=== 测试多设备布局协调 ===")
        
        # 清除之前的元素
        self.layout_manager.clear_elements()
        
        # 创建多个相邻设备
        devices = [
            Device("设备1", -3.0, 2.0),
            Device("设备2", -2.0, 2.0),
            Device("设备3", -1.0, 2.0),
        ]
        
        positions = []
        for device in devices:
            x, y, pos = self.layout_manager.calculate_device_info_position(device.x, device.y, device.id)
            positions.append((x, y, pos))
            
            # 注册设备到布局管理器
            box_width, box_height = 2.5, 1.2
            device_bbox = BoundingBox(x - box_width/2, y - box_height/2, x + box_width/2, y + box_height/2)
            device_element = LayoutElement(
                ElementType.DEVICE_INFO, device_bbox, (device.x, device.y),
                priority=8, movable=True, element_id=f"device_{device.id}",
                device_position=pos
            )
            self.layout_manager.add_element(device_element)
            
            print(f"{device.name} ({device.x}, {device.y}) -> ({x:.1f}, {y:.1f}) {pos.value}")
        
        # 验证没有重叠的信息框
        for i, (x1, y1, pos1) in enumerate(positions):
            for j, (x2, y2, pos2) in enumerate(positions):
                if i != j:
                    distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                    self.assertGreaterEqual(distance, 1.0, f"设备{i+1}和设备{j+1}的信息框距离过近: {distance:.2f}")
        
        print("✅ 多设备布局协调测试通过")


def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始设备信息框智能避让系统综合测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_cases = [
        'test_device_position_enum',
        'test_device_default_position_calculation',
        'test_priority_order_strategy',
        'test_conflict_detection_and_avoidance',
        'test_device_position_state_management',
        'test_device_serialization_with_position',
        'test_canvas_bounds_checking',
        'test_multiple_devices_layout',
    ]
    
    for test_case in test_cases:
        test_suite.addTest(TestDeviceInfoSmartLayout(test_case))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试总结
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！设备信息框智能避让系统工作正常")
        print(f"✅ 运行了 {result.testsRun} 个测试用例")
    else:
        print("❌ 测试失败！")
        print(f"❌ {len(result.failures)} 个失败")
        print(f"❌ {len(result.errors)} 个错误")
        
        # 输出失败详情
        for test, traceback in result.failures:
            print(f"\n失败: {test}")
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\n错误: {test}")
            print(traceback)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 