# -*- coding: utf-8 -*-
"""
设备管理重构功能测试

测试重构后的设备管理器、主控制器和视图组件的协同工作
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev'))

from models.device_manager import DeviceManager, DeviceManagerError
from models.device_model import Device
from controllers.main_controller import MainController


class TestDeviceManagerRefactor(unittest.TestCase):
    """
    设备管理重构测试类
    """
    
    def setUp(self):
        """
        设置测试环境
        """
        self.device_manager = DeviceManager()
        # 清除初始设备，从空白状态开始测试
        self.device_manager.clear_all_devices()
    
    def tearDown(self):
        """
        清理测试环境
        """
        if hasattr(self, 'device_manager'):
            self.device_manager.clear_all_devices()
    
    def test_device_manager_initialization(self):
        """
        测试设备管理器初始化
        """
        print("🧪 测试设备管理器初始化...")
        
        # 创建新的设备管理器（应该包含初始设备）
        dm = DeviceManager()
        
        self.assertGreaterEqual(dm.get_device_count(), 0)
        summary = dm.get_summary()
        self.assertIn('total_devices', summary)
        self.assertIn('max_devices', summary)
        self.assertEqual(summary['max_devices'], 10)
        
        print(f"✅ 设备管理器初始化测试通过 - 设备数量: {dm.get_device_count()}")
    
    def test_add_device_transaction(self):
        """
        测试设备添加的事务式操作
        """
        print("🧪 测试设备添加事务...")
        
        # 准备观察者
        observer_called = []
        def observer(devices):
            observer_called.append(len(devices))
        
        self.device_manager.add_observer(observer)
        
        # 测试成功添加
        device1 = Device("测试设备1", 1.0, 2.0)
        success, message = self.device_manager.add_device(device1)
        
        self.assertTrue(success)
        self.assertEqual(message, "设备添加成功")
        self.assertEqual(self.device_manager.get_device_count(), 1)
        self.assertEqual(len(observer_called), 1)
        self.assertEqual(observer_called[0], 1)
        
        # 测试重复名称添加（应该失败）
        device2 = Device("测试设备1", 3.0, 4.0)
        success, message = self.device_manager.add_device(device2)
        
        self.assertFalse(success)
        self.assertIn("已存在", message)
        self.assertEqual(self.device_manager.get_device_count(), 1)  # 数量不变
        
        print("✅ 设备添加事务测试通过")
    
    def test_update_device_transaction(self):
        """
        测试设备更新的事务式操作
        """
        print("🧪 测试设备更新事务...")
        
        # 先添加一个设备
        device = Device("原始设备", 1.0, 2.0)
        self.device_manager.add_device(device)
        device_id = device.id
        
        # 准备观察者
        observer_called = []
        def observer(devices):
            observer_called.append([d.name for d in devices])
        
        self.device_manager.add_observer(observer)
        
        # 测试成功更新
        new_device = Device("更新后设备", 3.0, 4.0)
        success, message = self.device_manager.update_device(device_id, new_device)
        
        self.assertTrue(success)
        self.assertEqual(message, "设备更新成功")
        
        # 验证设备已更新
        updated_device = self.device_manager.get_device_by_id(device_id)
        self.assertIsNotNone(updated_device)
        self.assertEqual(updated_device.name, "更新后设备")
        self.assertEqual(updated_device.x, 3.0)
        self.assertEqual(updated_device.y, 4.0)
        self.assertEqual(updated_device.id, device_id)  # ID保持不变
        
        # 验证观察者被调用
        self.assertEqual(len(observer_called), 1)
        self.assertIn("更新后设备", observer_called[0])
        
        print("✅ 设备更新事务测试通过")
    
    def test_delete_device_transaction(self):
        """
        测试设备删除的事务式操作
        """
        print("🧪 测试设备删除事务...")
        
        # 先添加两个设备
        device1 = Device("设备1", 1.0, 2.0)
        device2 = Device("设备2", 3.0, 4.0)
        self.device_manager.add_device(device1)
        self.device_manager.add_device(device2)
        
        initial_count = self.device_manager.get_device_count()
        self.assertEqual(initial_count, 2)
        
        # 准备观察者
        observer_called = []
        def observer(devices):
            observer_called.append(len(devices))
        
        self.device_manager.add_observer(observer)
        
        # 测试成功删除
        success, message = self.device_manager.delete_device(device1.id)
        
        self.assertTrue(success)
        self.assertEqual(message, "设备删除成功")
        self.assertEqual(self.device_manager.get_device_count(), 1)
        
        # 验证正确的设备被删除
        remaining_device = self.device_manager.get_devices()[0]
        self.assertEqual(remaining_device.name, "设备2")
        
        # 验证观察者被调用
        self.assertEqual(len(observer_called), 1)
        self.assertEqual(observer_called[0], 1)
        
        # 测试删除不存在的设备
        success, message = self.device_manager.delete_device("non_existent_id")
        self.assertFalse(success)
        self.assertIn("未找到要删除的设备", message)
        
        print("✅ 设备删除事务测试通过")
    
    def test_device_validation_and_rollback(self):
        """
        测试设备验证和回滚机制
        """
        print("🧪 测试验证回滚机制...")
        
        # 添加最大数量的设备
        for i in range(DeviceManager.MAX_DEVICES):
            device = Device(f"设备{i}", float(i), float(i))
            success, _ = self.device_manager.add_device(device)
            self.assertTrue(success)
        
        # 尝试添加超出限制的设备（应该失败且不影响现有数据）
        extra_device = Device("超出限制设备", 99.0, 99.0)
        success, message = self.device_manager.add_device(extra_device)
        
        self.assertFalse(success)
        self.assertIn("数量上限", message)
        self.assertEqual(self.device_manager.get_device_count(), DeviceManager.MAX_DEVICES)
        
        # 验证所有原有设备都还在
        devices = self.device_manager.get_devices()
        device_names = [d.name for d in devices]
        for i in range(DeviceManager.MAX_DEVICES):
            self.assertIn(f"设备{i}", device_names)
        
        print("✅ 验证回滚机制测试通过")
    
    def test_observer_pattern(self):
        """
        测试观察者模式
        """
        print("🧪 测试观察者模式...")
        
        # 设置多个观察者
        calls_observer1 = []
        calls_observer2 = []
        
        def observer1(devices):
            calls_observer1.append(len(devices))
        
        def observer2(devices):
            calls_observer2.append([d.name for d in devices])
        
        self.device_manager.add_observer(observer1)
        self.device_manager.add_observer(observer2)
        
        # 执行一系列操作
        device = Device("观察者测试设备", 1.0, 1.0)
        self.device_manager.add_device(device)
        
        # 验证观察者被调用
        self.assertEqual(len(calls_observer1), 1)
        self.assertEqual(calls_observer1[0], 1)
        self.assertEqual(len(calls_observer2), 1)
        self.assertIn("观察者测试设备", calls_observer2[0])
        
        # 移除一个观察者
        self.device_manager.remove_observer(observer1)
        
        # 再次操作
        self.device_manager.delete_device(device.id)
        
        # 验证只有剩余观察者被调用
        self.assertEqual(len(calls_observer1), 1)  # 没有新的调用
        self.assertEqual(len(calls_observer2), 2)  # 有新的调用
        self.assertEqual(len(calls_observer2[1]), 0)  # 设备列表为空
        
        print("✅ 观察者模式测试通过")


class TestMainControllerIntegration(unittest.TestCase):
    """
    主控制器集成测试
    """
    
    @patch('views.main_window.MainWindow')
    @patch('views.canvas_view.CanvasView')  
    @patch('views.input_panel.InputPanel')
    def test_controller_device_sync(self, mock_input_panel, mock_canvas_view, mock_main_window):
        """
        测试控制器与视图的设备数据同步
        """
        print("🧪 测试控制器设备同步...")
        
        # 创建mock对象
        mock_main_window_instance = Mock()
        mock_canvas_view_instance = Mock()
        mock_input_panel_instance = Mock()
        
        mock_main_window.return_value = mock_main_window_instance
        mock_canvas_view.return_value = mock_canvas_view_instance
        mock_input_panel.return_value = mock_input_panel_instance
        
        # 模拟必要的方法
        mock_main_window_instance.get_canvas_frame.return_value = Mock()
        mock_main_window_instance.get_panel_frame.return_value = Mock()
        mock_canvas_view_instance.get_devices.return_value = []
        
        # 创建控制器
        controller = MainController()
        
        # 验证设备管理器已创建
        self.assertIsNotNone(controller.device_manager)
        
        # 模拟添加设备
        test_device = Device("测试设备", 1.0, 2.0)
        controller._on_device_add(test_device)
        
        # 验证设备被添加到设备管理器
        devices = controller.device_manager.get_devices()
        device_names = [d.name for d in devices]
        self.assertIn("测试设备", device_names)
        
        print("✅ 控制器设备同步测试通过")


def run_device_manager_tests():
    """
    运行设备管理重构测试
    """
    print("🚀 开始设备管理重构测试...")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加设备管理器测试
    suite.addTest(TestDeviceManagerRefactor('test_device_manager_initialization'))
    suite.addTest(TestDeviceManagerRefactor('test_add_device_transaction'))
    suite.addTest(TestDeviceManagerRefactor('test_update_device_transaction'))
    suite.addTest(TestDeviceManagerRefactor('test_delete_device_transaction'))
    suite.addTest(TestDeviceManagerRefactor('test_device_validation_and_rollback'))
    suite.addTest(TestDeviceManagerRefactor('test_observer_pattern'))
    
    # 添加集成测试
    suite.addTest(TestMainControllerIntegration('test_controller_device_sync'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    
    if result.wasSuccessful():
        print("🎉 所有测试通过！设备管理重构成功！")
        return True
    else:
        print("❌ 测试失败，需要修复问题")
        print(f"失败数量: {len(result.failures)}")
        print(f"错误数量: {len(result.errors)}")
        
        # 打印详细错误信息
        for test, traceback in result.failures + result.errors:
            print(f"\n❌ {test}: {traceback}")
        
        return False


if __name__ == "__main__":
    success = run_device_manager_tests()
    sys.exit(0 if success else 1) 