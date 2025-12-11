# -*- coding: utf-8 -*-
"""
V2.0 第一期核心架构重构 - 集成测试脚本

测试内容：
1. CoordinateFrame 坐标变换测试
2. SceneModel 数据管理测试
3. SceneModel 观察者模式测试
4. SceneController 业务逻辑测试
5. SceneRenderer 渲染测试

运行方式: python tests/test_phase1_core_refactor.py
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

import math
import unittest
from typing import List, Any

# 导入待测试模块
from models.coordinate_frame import CoordinateFrame, WORLD_FRAME, create_user_frame
from models.scene_model import SceneModel, ChangeType, SectorData, MeasurementData, LabelPosition
from models.device_model import Device
from controllers.scene_controller import SceneController


class TestCoordinateFrame(unittest.TestCase):
    """CoordinateFrame 坐标变换测试"""
    
    def test_world_frame_is_identity(self):
        """测试世界坐标系是恒等变换"""
        world = WORLD_FRAME
        
        # 世界坐标系应该是原点在(0,0)且无旋转
        self.assertTrue(world.is_origin())
        
        # 坐标变换应该是恒等变换
        x, y = 3.5, -2.7
        local_x, local_y = world.world_to_local(x, y)
        self.assertAlmostEqual(local_x, x, places=10)
        self.assertAlmostEqual(local_y, y, places=10)
    
    def test_world_to_local_basic(self):
        """测试基本坐标转换：世界→本地"""
        frame = CoordinateFrame("user", 2.0, 3.0)
        
        # 点 (5, 7) 相对于原点 (2, 3) 的本地坐标
        local_x, local_y = frame.world_to_local(5.0, 7.0)
        self.assertAlmostEqual(local_x, 3.0, places=10)
        self.assertAlmostEqual(local_y, 4.0, places=10)
    
    def test_local_to_world_basic(self):
        """测试基本坐标转换：本地→世界"""
        frame = CoordinateFrame("user", -1.5, 2.5)
        
        # 本地坐标 (1, 2) 对应的世界坐标
        world_x, world_y = frame.local_to_world(1.0, 2.0)
        self.assertAlmostEqual(world_x, -0.5, places=10)
        self.assertAlmostEqual(world_y, 4.5, places=10)
    
    def test_round_trip_conversion(self):
        """测试双向转换一致性"""
        frame = CoordinateFrame("user", -1.5, 2.5)
        
        world_x, world_y = 3.0, 4.0
        local = frame.world_to_local(world_x, world_y)
        back = frame.local_to_world(*local)
        
        self.assertAlmostEqual(back[0], world_x, places=10)
        self.assertAlmostEqual(back[1], world_y, places=10)
    
    def test_distance_from_origin(self):
        """测试到原点的距离计算"""
        frame = CoordinateFrame("user", 3.0, 4.0)
        
        # 点 (6, 8) 到原点 (3, 4) 的距离
        distance = frame.distance_from_origin(6.0, 8.0)
        expected = math.sqrt(3**2 + 4**2)  # 5.0
        self.assertAlmostEqual(distance, expected, places=10)
    
    def test_angle_from_origin(self):
        """测试从原点的角度计算"""
        frame = CoordinateFrame("user", 0.0, 0.0)
        
        # 点 (1, 0) 角度为 0°
        angle = frame.angle_from_origin(1.0, 0.0)
        self.assertAlmostEqual(angle, 0.0, places=5)
        
        # 点 (0, 1) 角度为 90°
        angle = frame.angle_from_origin(0.0, 1.0)
        self.assertAlmostEqual(angle, 90.0, places=5)
        
        # 点 (-1, 0) 角度为 180°
        angle = frame.angle_from_origin(-1.0, 0.0)
        self.assertAlmostEqual(angle, 180.0, places=5)
    
    def test_create_user_frame_factory(self):
        """测试用户坐标系工厂函数"""
        user_frame = create_user_frame(5.0, -3.0)
        
        self.assertEqual(user_frame.name, "user")
        self.assertAlmostEqual(user_frame.origin_x, 5.0, places=10)
        self.assertAlmostEqual(user_frame.origin_y, -3.0, places=10)
    
    def test_copy(self):
        """测试坐标系复制"""
        original = CoordinateFrame("test", 1.0, 2.0, 45.0)
        copy = original.copy()
        
        self.assertEqual(copy.name, original.name)
        self.assertAlmostEqual(copy.origin_x, original.origin_x, places=10)
        self.assertAlmostEqual(copy.origin_y, original.origin_y, places=10)
        self.assertAlmostEqual(copy.rotation_deg, original.rotation_deg, places=10)
        
        # 修改副本不影响原对象
        copy.origin_x = 100.0
        self.assertAlmostEqual(original.origin_x, 1.0, places=10)


class TestSceneModel(unittest.TestCase):
    """SceneModel 数据管理测试"""
    
    def setUp(self):
        """测试前初始化"""
        self.model = SceneModel()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(len(self.model.get_devices()), 0)
        self.assertIsNone(self.model.get_measurement())
        self.assertEqual(len(self.model.get_sectors()), 0)
        self.assertFalse(self.model.is_user_frame_active())
        self.assertEqual(self.model.coord_range, (10.0, 10.0))
    
    def test_add_device(self):
        """测试添加设备"""
        device = Device("测试设备", 1.0, 2.0)
        success, msg = self.model.add_device(device)
        
        self.assertTrue(success)
        self.assertEqual(self.model.get_device_count(), 1)
        
        devices = self.model.get_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "测试设备")
    
    def test_add_duplicate_device_name(self):
        """测试添加重名设备"""
        device1 = Device("设备A", 1.0, 2.0)
        device2 = Device("设备A", 3.0, 4.0)  # 同名
        
        success1, _ = self.model.add_device(device1)
        success2, msg = self.model.add_device(device2)
        
        self.assertTrue(success1)
        self.assertFalse(success2)
        self.assertIn("已存在", msg)
    
    def test_update_device(self):
        """测试更新设备"""
        device = Device("原名称", 1.0, 2.0)
        self.model.add_device(device)
        
        new_device = Device("新名称", 5.0, 6.0)
        success, _ = self.model.update_device(device.id, new_device)
        
        self.assertTrue(success)
        updated = self.model.get_device_by_id(device.id)
        self.assertEqual(updated.name, "新名称")
        self.assertAlmostEqual(updated.x, 5.0, places=10)
    
    def test_remove_device(self):
        """测试删除设备"""
        device = Device("待删除", 1.0, 2.0)
        self.model.add_device(device)
        
        success, _ = self.model.remove_device(device.id)
        
        self.assertTrue(success)
        self.assertEqual(self.model.get_device_count(), 0)
    
    def test_set_measurement(self):
        """测试设置测量点"""
        self.model.set_measurement(3.0, 4.0)
        
        measurement = self.model.get_measurement()
        self.assertIsNotNone(measurement)
        self.assertAlmostEqual(measurement.x, 3.0, places=10)
        self.assertAlmostEqual(measurement.y, 4.0, places=10)
        
        # 检查距离计算
        expected_distance = math.sqrt(3**2 + 4**2)  # 5.0
        self.assertAlmostEqual(measurement.distance_to_origin, expected_distance, places=5)
    
    def test_user_position(self):
        """测试用户位置设置"""
        self.assertFalse(self.model.is_user_frame_active())
        
        self.model.set_user_position(2.0, 3.0)
        
        self.assertTrue(self.model.is_user_frame_active())
        pos = self.model.get_user_position()
        self.assertEqual(pos, (2.0, 3.0))
    
    def test_add_sector(self):
        """测试添加扇形"""
        sector = self.model.add_sector(0.0, 0.0, 5.0, 0.0, 90.0)
        
        self.assertIsNotNone(sector)
        sectors = self.model.get_sectors()
        self.assertEqual(len(sectors), 1)
        self.assertAlmostEqual(sectors[0].radius, 5.0, places=10)
    
    def test_coordinate_range(self):
        """测试坐标范围设置"""
        success = self.model.set_coordinate_range(20.0, 15.0)
        
        self.assertTrue(success)
        self.assertEqual(self.model.coord_range, (20.0, 15.0))
    
    def test_label_position_management(self):
        """测试标签位置管理"""
        # 设置自动位置
        self.model.set_label_position("device_test", 1.0, 2.0, is_manual=False)
        pos = self.model.get_label_position("device_test")
        self.assertFalse(pos.is_manual)
        
        # 设置手动位置
        self.model.set_label_position("device_test", 5.0, 6.0, is_manual=True)
        pos = self.model.get_label_position("device_test")
        self.assertTrue(pos.is_manual)
        self.assertAlmostEqual(pos.x, 5.0, places=10)
    
    def test_reset(self):
        """测试重置功能"""
        # 添加一些数据
        self.model.add_device(Device("设备1", 1.0, 2.0))
        self.model.set_measurement(3.0, 4.0)
        self.model.set_user_position(5.0, 6.0)
        
        # 重置
        self.model.reset()
        
        self.assertEqual(self.model.get_device_count(), 0)
        self.assertIsNone(self.model.get_measurement())
        self.assertFalse(self.model.is_user_frame_active())
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        # 添加数据
        self.model.add_device(Device("设备1", 1.0, 2.0))
        self.model.set_user_position(3.0, 4.0)
        self.model.set_label_position("device_xxx", 5.0, 6.0, is_manual=True)
        
        # 序列化
        data = self.model.to_dict()
        
        # 创建新模型并反序列化
        new_model = SceneModel()
        new_model.from_dict(data)
        
        # 验证数据恢复
        self.assertEqual(new_model.get_device_count(), 1)
        self.assertTrue(new_model.is_user_frame_active())


class TestSceneModelObserver(unittest.TestCase):
    """SceneModel 观察者模式测试"""
    
    def setUp(self):
        """测试前初始化"""
        self.model = SceneModel()
        self.received_changes: List[tuple] = []
    
    def _observer(self, change_type: ChangeType, data: Any):
        """测试用观察者回调"""
        self.received_changes.append((change_type, data))
    
    def test_observer_notification_on_device_add(self):
        """测试设备添加时的观察者通知"""
        self.model.add_observer(self._observer)
        
        device = Device("测试", 1.0, 2.0)
        self.model.add_device(device)
        
        self.assertEqual(len(self.received_changes), 1)
        self.assertEqual(self.received_changes[0][0], ChangeType.DEVICE_ADDED)
    
    def test_observer_notification_on_measurement(self):
        """测试测量点设置时的观察者通知"""
        self.model.add_observer(self._observer)
        
        self.model.set_measurement(1.0, 2.0)
        
        self.assertEqual(len(self.received_changes), 1)
        self.assertEqual(self.received_changes[0][0], ChangeType.MEASUREMENT_SET)
    
    def test_observer_removal(self):
        """测试移除观察者"""
        self.model.add_observer(self._observer)
        self.model.remove_observer(self._observer)
        
        self.model.add_device(Device("测试", 1.0, 2.0))
        
        self.assertEqual(len(self.received_changes), 0)
    
    def test_multiple_observers(self):
        """测试多个观察者"""
        changes1: List[tuple] = []
        changes2: List[tuple] = []
        
        def observer1(change_type, data):
            changes1.append((change_type, data))
        
        def observer2(change_type, data):
            changes2.append((change_type, data))
        
        self.model.add_observer(observer1)
        self.model.add_observer(observer2)
        
        self.model.add_device(Device("测试", 1.0, 2.0))
        
        self.assertEqual(len(changes1), 1)
        self.assertEqual(len(changes2), 1)


class TestSceneController(unittest.TestCase):
    """SceneController 业务逻辑测试"""
    
    def setUp(self):
        """测试前初始化"""
        self.model = SceneModel()
        self.controller = SceneController(self.model)
    
    def test_add_device(self):
        """测试通过控制器添加设备"""
        success, msg = self.controller.add_device("设备A", 1.0, 2.0)
        
        self.assertTrue(success)
        self.assertEqual(self.model.get_device_count(), 1)
    
    def test_handle_left_click(self):
        """测试左键单击创建测量点"""
        self.controller.on_canvas_click(3.0, 4.0, button=1, current_time=1.0)
        
        measurement = self.model.get_measurement()
        self.assertIsNotNone(measurement)
        self.assertAlmostEqual(measurement.x, 3.0, places=10)
    
    def test_handle_double_click_world_coord(self):
        """测试双击创建扇形（世界坐标系模式）"""
        # 模拟双击：第一次点击时间1.0秒，第二次点击时间1.1秒（间隔0.1秒 < 0.3秒阈值）
        self.controller.on_canvas_click(3.0, 4.0, button=1, current_time=1.0)  # 单击，创建测量点
        self.controller.on_canvas_click(3.0, 4.0, button=1, current_time=1.1)  # 双击，创建扇形
        
        sectors = self.model.get_sectors()
        self.assertEqual(len(sectors), 1)
        
        # 扇形中心应该是原点(0,0)
        self.assertAlmostEqual(sectors[0].center_x, 0.0, places=10)
        self.assertAlmostEqual(sectors[0].center_y, 0.0, places=10)
    
    def test_handle_double_click_user_coord(self):
        """测试双击创建扇形（用户坐标系模式）"""
        # 设置用户位置
        self.model.set_user_position(2.0, 2.0)
        
        # 模拟双击：第一次点击时间1.0秒，第二次点击时间1.1秒
        self.controller.on_canvas_click(5.0, 6.0, button=1, current_time=1.0)  # 单击
        self.controller.on_canvas_click(5.0, 6.0, button=1, current_time=1.1)  # 双击
        
        sectors = self.model.get_sectors()
        self.assertEqual(len(sectors), 1)
        
        # 扇形中心应该是用户位置(2,2)
        self.assertAlmostEqual(sectors[0].center_x, 2.0, places=10)
        self.assertAlmostEqual(sectors[0].center_y, 2.0, places=10)
    
    def test_handle_right_click(self):
        """测试右键清除测量点和扇形"""
        # 创建测量点和扇形
        self.model.set_measurement(1.0, 2.0)
        self.model.add_sector(0.0, 0.0, 5.0, 0.0, 90.0)
        
        # 右键点击
        self.controller.on_canvas_click(0.0, 0.0, button=3, current_time=0.0)
        
        self.assertIsNone(self.model.get_measurement())
        self.assertEqual(len(self.model.get_sectors()), 0)
    
    def test_set_coordinate_range(self):
        """测试设置坐标范围"""
        success, _ = self.controller.set_coordinate_range(20.0, 15.0)
        
        self.assertTrue(success)
        self.assertEqual(self.model.coord_range, (20.0, 15.0))
    
    def test_user_position_management(self):
        """测试用户位置管理"""
        # 设置用户位置
        success, _ = self.controller.set_user_position(5.0, 3.0)
        self.assertTrue(success)
        self.assertTrue(self.controller.is_user_coord_enabled())
        
        # 获取用户位置
        pos = self.controller.get_user_position()
        self.assertEqual(pos, (5.0, 3.0))
        
        # 清除用户位置
        self.controller.clear_user_position()
        self.assertFalse(self.controller.is_user_coord_enabled())


class TestSectorData(unittest.TestCase):
    """SectorData 扇形数据测试"""
    
    def test_contains_point_inside(self):
        """测试扇形内的点"""
        sector = SectorData(
            center_x=0.0, center_y=0.0,
            radius=5.0,
            start_angle_deg=0.0, end_angle_deg=90.0
        )
        
        # 第一象限的点应该在扇形内
        self.assertTrue(sector.contains_point(2.0, 2.0))
    
    def test_contains_point_outside_radius(self):
        """测试扇形外的点（超出半径）"""
        sector = SectorData(
            center_x=0.0, center_y=0.0,
            radius=5.0,
            start_angle_deg=0.0, end_angle_deg=90.0
        )
        
        # 超出半径的点
        self.assertFalse(sector.contains_point(10.0, 10.0))
    
    def test_contains_point_outside_angle(self):
        """测试扇形外的点（角度不在范围内）"""
        sector = SectorData(
            center_x=0.0, center_y=0.0,
            radius=5.0,
            start_angle_deg=0.0, end_angle_deg=90.0
        )
        
        # 第三象限的点（角度不在范围内）
        self.assertFalse(sector.contains_point(-2.0, -2.0))
    
    def test_contains_point_at_center(self):
        """测试中心点"""
        sector = SectorData(
            center_x=2.0, center_y=3.0,
            radius=5.0,
            start_angle_deg=0.0, end_angle_deg=90.0
        )
        
        # 中心点应该在扇形内
        self.assertTrue(sector.contains_point(2.0, 3.0))


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCoordinateFrame))
    suite.addTests(loader.loadTestsFromTestCase(TestSceneModel))
    suite.addTests(loader.loadTestsFromTestCase(TestSceneModelObserver))
    suite.addTests(loader.loadTestsFromTestCase(TestSceneController))
    suite.addTests(loader.loadTestsFromTestCase(TestSectorData))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("测试统计:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    result = run_all_tests()
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)

