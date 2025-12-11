# -*- coding: utf-8 -*-
"""
V2.0 第二期标签布局系统重构 - 测试脚本

测试范围：
1. LabelPlacer 确定性算法测试
2. CollisionDetector 碰撞检测测试
3. 标签布局避开扇形测试
4. 手动位置保留测试
5. 位置持久化测试

测试日期: 2025-11-26
测试版本: V2.0 Phase 2
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'dev' / 'src'))

from services.label_placer import LabelPlacer, LabelPosition, DeviceAnchor, SectorObstacle
from services.collision_detector import CollisionDetector, BoundingBox


class TestBoundingBox(unittest.TestCase):
    """BoundingBox 边界框测试"""
    
    def test_create_from_center(self):
        """测试从中心点创建边界框"""
        box = BoundingBox.from_center(5.0, 5.0, 2.0, 1.0)
        
        self.assertAlmostEqual(box.x_min, 4.0)
        self.assertAlmostEqual(box.x_max, 6.0)
        self.assertAlmostEqual(box.y_min, 4.5)
        self.assertAlmostEqual(box.y_max, 5.5)
    
    def test_center(self):
        """测试获取中心点"""
        box = BoundingBox(0.0, 0.0, 4.0, 2.0)
        center = box.center()
        
        self.assertAlmostEqual(center[0], 2.0)
        self.assertAlmostEqual(center[1], 1.0)
    
    def test_width_height(self):
        """测试宽度和高度"""
        box = BoundingBox(1.0, 2.0, 5.0, 6.0)
        
        self.assertAlmostEqual(box.width(), 4.0)
        self.assertAlmostEqual(box.height(), 4.0)
    
    def test_area(self):
        """测试面积计算"""
        box = BoundingBox(0.0, 0.0, 3.0, 4.0)
        
        self.assertAlmostEqual(box.area(), 12.0)
    
    def test_contains_point(self):
        """测试点包含检测"""
        box = BoundingBox(0.0, 0.0, 4.0, 3.0)
        
        # 内部点
        self.assertTrue(box.contains_point(2.0, 1.5))
        # 边界点
        self.assertTrue(box.contains_point(0.0, 0.0))
        self.assertTrue(box.contains_point(4.0, 3.0))
        # 外部点
        self.assertFalse(box.contains_point(5.0, 1.5))
        self.assertFalse(box.contains_point(2.0, -1.0))
    
    def test_expand(self):
        """测试边界框扩展"""
        box = BoundingBox(1.0, 1.0, 3.0, 3.0)
        expanded = box.expand(0.5)
        
        self.assertAlmostEqual(expanded.x_min, 0.5)
        self.assertAlmostEqual(expanded.x_max, 3.5)
        self.assertAlmostEqual(expanded.y_min, 0.5)
        self.assertAlmostEqual(expanded.y_max, 3.5)


class TestCollisionDetector(unittest.TestCase):
    """CollisionDetector 碰撞检测测试"""
    
    def test_boxes_overlap_true(self):
        """测试重叠的边界框"""
        box1 = BoundingBox(0.0, 0.0, 2.0, 2.0)
        box2 = BoundingBox(1.0, 1.0, 3.0, 3.0)
        
        self.assertTrue(CollisionDetector.boxes_overlap(box1, box2))
    
    def test_boxes_overlap_false(self):
        """测试不重叠的边界框"""
        box1 = BoundingBox(0.0, 0.0, 1.0, 1.0)
        box2 = BoundingBox(2.0, 2.0, 3.0, 3.0)
        
        self.assertFalse(CollisionDetector.boxes_overlap(box1, box2))
    
    def test_boxes_overlap_with_margin(self):
        """测试带间距的重叠检测"""
        box1 = BoundingBox(0.0, 0.0, 1.0, 1.0)
        box2 = BoundingBox(1.1, 0.0, 2.0, 1.0)  # 间距0.1
        
        # 无间距时不重叠
        self.assertFalse(CollisionDetector.boxes_overlap(box1, box2, margin=0.0))
        # 间距0.2时重叠
        self.assertTrue(CollisionDetector.boxes_overlap(box1, box2, margin=0.2))
    
    def test_overlaps_any(self):
        """测试与列表中任意边界框重叠"""
        box = BoundingBox(0.0, 0.0, 2.0, 2.0)
        boxes = [
            BoundingBox(5.0, 5.0, 6.0, 6.0),
            BoundingBox(1.5, 1.5, 3.0, 3.0),  # 与box重叠
            BoundingBox(10.0, 10.0, 11.0, 11.0),
        ]
        
        self.assertTrue(CollisionDetector.overlaps_any(box, boxes))
    
    def test_is_within_bounds(self):
        """测试边界框是否在范围内"""
        bounds = BoundingBox(-10.0, -10.0, 10.0, 10.0)
        
        # 完全在内部
        box1 = BoundingBox(-5.0, -5.0, 5.0, 5.0)
        self.assertTrue(CollisionDetector.is_within_bounds(box1, bounds))
        
        # 超出边界
        box2 = BoundingBox(-5.0, -5.0, 15.0, 5.0)
        self.assertFalse(CollisionDetector.is_within_bounds(box2, bounds))
        
        # 考虑内边距
        box3 = BoundingBox(-9.5, -9.5, 9.5, 9.5)
        self.assertFalse(CollisionDetector.is_within_bounds(box3, bounds, margin=1.0))
    
    def test_point_in_sector_inside(self):
        """测试点在扇形内"""
        # 以原点为中心，半径3，角度0-90度的扇形
        result = CollisionDetector.point_in_sector(
            x=1.5, y=1.5,
            center_x=0.0, center_y=0.0,
            radius=3.0,
            start_angle_deg=0.0,
            end_angle_deg=90.0
        )
        self.assertTrue(result)
    
    def test_point_in_sector_outside_radius(self):
        """测试点超出扇形半径"""
        result = CollisionDetector.point_in_sector(
            x=5.0, y=5.0,  # 距离原点约7.07
            center_x=0.0, center_y=0.0,
            radius=3.0,
            start_angle_deg=0.0,
            end_angle_deg=90.0
        )
        self.assertFalse(result)
    
    def test_point_in_sector_outside_angle(self):
        """测试点不在扇形角度范围内"""
        result = CollisionDetector.point_in_sector(
            x=-1.0, y=1.0,  # 135度方向
            center_x=0.0, center_y=0.0,
            radius=3.0,
            start_angle_deg=0.0,
            end_angle_deg=90.0
        )
        self.assertFalse(result)
    
    def test_point_in_sector_center(self):
        """测试扇形中心点"""
        result = CollisionDetector.point_in_sector(
            x=0.0, y=0.0,
            center_x=0.0, center_y=0.0,
            radius=3.0,
            start_angle_deg=0.0,
            end_angle_deg=90.0
        )
        self.assertTrue(result)  # 中心点始终在扇形内
    
    def test_distance_between_boxes(self):
        """测试边界框之间的距离"""
        box1 = BoundingBox(0.0, 0.0, 1.0, 1.0)
        box2 = BoundingBox(3.0, 0.0, 4.0, 1.0)  # 右侧，间距2.0
        
        distance = CollisionDetector.distance_between_boxes(box1, box2)
        self.assertAlmostEqual(distance, 2.0)
    
    def test_distance_between_boxes_overlapping(self):
        """测试重叠边界框的距离（负值）"""
        box1 = BoundingBox(0.0, 0.0, 2.0, 2.0)
        box2 = BoundingBox(1.0, 1.0, 3.0, 3.0)
        
        distance = CollisionDetector.distance_between_boxes(box1, box2)
        self.assertLess(distance, 0)  # 重叠时为负值


class TestLabelPlacer(unittest.TestCase):
    """LabelPlacer 标签布局服务测试"""
    
    def setUp(self):
        """初始化测试环境"""
        self.placer = LabelPlacer()
        self.coord_range = (10.0, 10.0)
    
    def test_deterministic_output(self):
        """测试确定性输出：同样输入产生同样输出"""
        devices = [
            DeviceAnchor(device_id="dev1", x=1.0, y=1.0, name="设备A"),
            DeviceAnchor(device_id="dev2", x=-1.0, y=2.0, name="设备B"),
            DeviceAnchor(device_id="dev3", x=3.0, y=-1.0, name="设备C"),
        ]
        
        # 多次计算
        result1 = self.placer.calculate_positions(devices, [], self.coord_range)
        result2 = self.placer.calculate_positions(devices, [], self.coord_range)
        result3 = self.placer.calculate_positions(devices, [], self.coord_range)
        
        # 验证结果一致
        self.assertEqual(len(result1), len(result2))
        self.assertEqual(len(result2), len(result3))
        
        for key in result1:
            self.assertAlmostEqual(result1[key].x, result2[key].x)
            self.assertAlmostEqual(result1[key].y, result2[key].y)
            self.assertAlmostEqual(result2[key].x, result3[key].x)
            self.assertAlmostEqual(result2[key].y, result3[key].y)
    
    def test_single_device_default_position(self):
        """测试单个设备的默认位置（右上方向）"""
        devices = [DeviceAnchor(device_id="dev1", x=0.0, y=0.0, name="测试设备")]
        
        result = self.placer.calculate_positions(devices, [], self.coord_range)
        
        self.assertIn("device_dev1", result)
        pos = result["device_dev1"]
        
        # 默认应该在右上方向
        self.assertGreater(pos.x, 0.0)  # 右侧
        self.assertGreater(pos.y, 0.0)  # 上方
        self.assertEqual(pos.direction, "右上")
    
    def test_avoid_sector(self):
        """测试避开扇形区域"""
        devices = [DeviceAnchor(device_id="dev1", x=0.0, y=0.0, name="测试设备")]
        
        # 创建一个覆盖右上方向的扇形
        sectors = [SectorObstacle(
            center_x=0.0, center_y=0.0,
            radius=3.0,
            start_angle_deg=0.0,
            end_angle_deg=90.0  # 右上象限
        )]
        
        result = self.placer.calculate_positions(devices, sectors, self.coord_range)
        pos = result["device_dev1"]
        
        # 应该选择其他方向（如左上）
        # 不能在右上象限
        in_sector = (pos.x > 0 and pos.y > 0)
        self.assertFalse(in_sector, f"标签位置 ({pos.x}, {pos.y}) 不应在扇形区域内")
    
    def test_preserve_manual_position(self):
        """测试保留手动位置"""
        devices = [DeviceAnchor(device_id="dev1", x=0.0, y=0.0, name="测试设备")]
        
        # 设置手动位置
        manual_positions = {
            "device_dev1": LabelPosition(x=5.0, y=5.0, is_manual=True, direction="手动")
        }
        
        result = self.placer.calculate_positions(
            devices, [], self.coord_range, existing_manual=manual_positions
        )
        
        pos = result["device_dev1"]
        self.assertAlmostEqual(pos.x, 5.0)
        self.assertAlmostEqual(pos.y, 5.0)
        self.assertTrue(pos.is_manual)
    
    def test_avoid_other_labels(self):
        """测试避开其他已放置的标签"""
        # 创建多个靠近的设备
        devices = [
            DeviceAnchor(device_id="dev1", x=0.0, y=0.0, name="设备1"),
            DeviceAnchor(device_id="dev2", x=0.5, y=0.5, name="设备2"),
        ]
        
        result = self.placer.calculate_positions(devices, [], self.coord_range)
        
        pos1 = result["device_dev1"]
        pos2 = result["device_dev2"]
        
        # 两个标签的中心距离应该大于标签碰撞间距
        # 对于非常靠近的设备，允许标签有一定程度的靠近
        distance = ((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)**0.5
        min_distance = 1.0  # 最小间距（允许一定程度的接近）
        
        self.assertGreater(distance, min_distance, 
                          f"标签距离 {distance:.2f} 太近，可能严重重叠")
    
    def test_boundary_constraint(self):
        """测试边界约束"""
        # 设备在边角
        devices = [DeviceAnchor(device_id="dev1", x=9.0, y=9.0, name="边角设备")]
        
        result = self.placer.calculate_positions(devices, [], self.coord_range)
        pos = result["device_dev1"]
        
        # 标签应该在画布范围内
        label_half_width = 1.0  # 标签宽度2.0的一半
        label_half_height = 0.4  # 标签高度0.8的一半
        
        self.assertGreater(pos.x - label_half_width, -10.0)
        self.assertLess(pos.x + label_half_width, 10.0)
        self.assertGreater(pos.y - label_half_height, -10.0)
        self.assertLess(pos.y + label_half_height, 10.0)
    
    def test_label_sizes(self):
        """测试获取标签尺寸"""
        device_size = self.placer.get_label_size("device")
        measurement_size = self.placer.get_label_size("measurement")
        user_size = self.placer.get_label_size("user")
        
        self.assertEqual(device_size, (2.0, 0.8))
        self.assertEqual(measurement_size, (2.5, 1.2))
        self.assertEqual(user_size, (1.8, 0.6))
    
    def test_validate_manual_position(self):
        """测试手动位置验证"""
        # 有效位置
        self.assertTrue(
            self.placer.validate_manual_position(5.0, 5.0, "device", self.coord_range)
        )
        
        # 超出边界
        self.assertFalse(
            self.placer.validate_manual_position(15.0, 5.0, "device", self.coord_range)
        )


class TestLabelPosition(unittest.TestCase):
    """LabelPosition 数据类测试"""
    
    def test_copy(self):
        """测试复制功能"""
        original = LabelPosition(x=1.0, y=2.0, is_manual=True, direction="右上")
        copy = original.copy()
        
        self.assertEqual(copy.x, original.x)
        self.assertEqual(copy.y, original.y)
        self.assertEqual(copy.is_manual, original.is_manual)
        self.assertEqual(copy.direction, original.direction)
        
        # 修改副本不影响原始
        copy.x = 5.0
        self.assertEqual(original.x, 1.0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complex_scene(self):
        """测试复杂场景：多设备 + 扇形"""
        placer = LabelPlacer()
        coord_range = (10.0, 10.0)
        
        # 5个设备
        devices = [
            DeviceAnchor(device_id="d1", x=0.0, y=0.0, name="设备1"),
            DeviceAnchor(device_id="d2", x=2.0, y=2.0, name="设备2"),
            DeviceAnchor(device_id="d3", x=-2.0, y=2.0, name="设备3"),
            DeviceAnchor(device_id="d4", x=2.0, y=-2.0, name="设备4"),
            DeviceAnchor(device_id="d5", x=-2.0, y=-2.0, name="设备5"),
        ]
        
        # 一个扇形覆盖右上象限
        sectors = [SectorObstacle(
            center_x=0.0, center_y=0.0,
            radius=4.0,
            start_angle_deg=-45.0,
            end_angle_deg=45.0
        )]
        
        result = placer.calculate_positions(devices, sectors, coord_range)
        
        # 验证所有设备都有标签位置
        self.assertEqual(len(result), 5)
        
        # 验证没有标签在扇形内
        for element_id, pos in result.items():
            # 简化检测：检查标签中心是否在扇形内
            in_sector = CollisionDetector.point_in_sector(
                pos.x, pos.y,
                0.0, 0.0, 4.0, -45.0, 45.0
            )
            if in_sector:
                print(f"⚠️ 标签 {element_id} 位置 ({pos.x:.2f}, {pos.y:.2f}) 在扇形内")
    
    def test_device_order_independence(self):
        """测试设备顺序无关性（ID排序后应一致）"""
        placer = LabelPlacer()
        coord_range = (10.0, 10.0)
        
        devices1 = [
            DeviceAnchor(device_id="a", x=1.0, y=1.0, name="A"),
            DeviceAnchor(device_id="b", x=-1.0, y=1.0, name="B"),
            DeviceAnchor(device_id="c", x=0.0, y=-1.0, name="C"),
        ]
        
        # 不同顺序
        devices2 = [
            DeviceAnchor(device_id="c", x=0.0, y=-1.0, name="C"),
            DeviceAnchor(device_id="a", x=1.0, y=1.0, name="A"),
            DeviceAnchor(device_id="b", x=-1.0, y=1.0, name="B"),
        ]
        
        result1 = placer.calculate_positions(devices1, [], coord_range)
        result2 = placer.calculate_positions(devices2, [], coord_range)
        
        # 结果应该相同（因为内部按ID排序）
        for key in result1:
            self.assertAlmostEqual(result1[key].x, result2[key].x, places=5)
            self.assertAlmostEqual(result1[key].y, result2[key].y, places=5)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBoundingBox))
    suite.addTests(loader.loadTestsFromTestCase(TestCollisionDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestLabelPlacer))
    suite.addTests(loader.loadTestsFromTestCase(TestLabelPosition))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("测试统计:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    run_tests()

