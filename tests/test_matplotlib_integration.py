#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matplotlib视图集成测试

测试MatplotlibView和MatplotlibController的基础功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端进行测试
import matplotlib.pyplot as plt

# 添加路径以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev'))

from views.matplotlib_view import MatplotlibView
from controllers.matplotlib_controller import MatplotlibController
from models.device_model import Device
from models.measurement_model import MeasurementPoint


class TestMatplotlibView(unittest.TestCase):
    """
    Matplotlib视图基础功能测试
    """
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的父框架
        self.mock_parent = Mock()
        
        # 使用patch避免真实的tkinter调用
        with patch('views.matplotlib_view.FigureCanvasTkAgg'):
            self.view = MatplotlibView(self.mock_parent)
    
    def test_initialization(self):
        """测试视图初始化"""
        self.assertIsNotNone(self.view.figure)
        self.assertIsNotNone(self.view.axes)
        self.assertEqual(self.view.current_range, (5.0, 5.0))
        self.assertEqual(len(self.view.devices), 0)
        self.assertIsNone(self.view.measurement_point)
    
    def test_coordinate_system_setup(self):
        """测试坐标系统设置"""
        # 测试默认范围
        xlim = self.view.axes.get_xlim()
        ylim = self.view.axes.get_ylim()
        self.assertEqual(xlim, (-5.0, 5.0))
        self.assertEqual(ylim, (-5.0, 5.0))
        
        # 测试自定义范围
        self.view.set_coordinate_range(10.0, 8.0)
        xlim = self.view.axes.get_xlim()
        ylim = self.view.axes.get_ylim()
        self.assertEqual(xlim, (-10.0, 10.0))
        self.assertEqual(ylim, (-8.0, 8.0))
        self.assertEqual(self.view.current_range, (10.0, 8.0))
    
    def test_device_management(self):
        """测试设备管理功能"""
        # 创建测试设备
        device1 = Device("测试设备1", 1.0, 2.0)
        device2 = Device("测试设备2", -1.5, 3.5)
        devices = [device1, device2]
        
        # 测试更新设备
        self.view.update_devices(devices)
        self.assertEqual(len(self.view.devices), 2)
        self.assertEqual(self.view.devices[0].name, "测试设备1")
        self.assertEqual(self.view.devices[1].name, "测试设备2")
        
        # 测试添加单个设备
        device3 = Device("测试设备3", 0.0, 0.0)
        self.view.add_device(device3)
        self.assertEqual(len(self.view.devices), 3)
        
        # 测试删除设备
        self.view.remove_device(device1)
        self.assertEqual(len(self.view.devices), 2)
        self.assertNotIn(device1, self.view.devices)
        
        # 测试清除所有设备
        self.view.clear_devices()
        self.assertEqual(len(self.view.devices), 0)
    
    def test_measurement_functionality(self):
        """测试测量功能"""
        # 创建测量点
        self.view.measurement_point = MeasurementPoint(3.0, 4.0)
        
        # 验证测量点存在
        self.assertIsNotNone(self.view.measurement_point)
        self.assertEqual(self.view.measurement_point.x, 3.0)
        self.assertEqual(self.view.measurement_point.y, 4.0)
        
        # 测试清除测量点
        self.view.clear_measurement()
        self.assertIsNone(self.view.measurement_point)
    
    def test_export_functionality(self):
        """测试导出功能"""
        import tempfile
        import os
        
        # 添加测试设备
        device = Device("导出测试", 1.0, 1.0)
        self.view.update_devices([device])
        
        # 导出到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            result = self.view.export_to_png(tmp.name, dpi=150)
            
            # 验证导出成功
            self.assertTrue(result)
            self.assertTrue(os.path.exists(tmp.name))
            self.assertGreater(os.path.getsize(tmp.name), 1000)  # 至少1KB
            
            # 清理
            os.unlink(tmp.name)
    
    def test_sector_drawing(self):
        """测试扇形绘制功能"""
        # 绘制扇形
        self.view.draw_temporary_sector(1.0, 1.0, 90)
        
        # 验证有扇形图形对象被创建
        self.assertGreater(len(self.view.sector_artists), 0)
        
        # 清除扇形
        self.view._clear_sector()
        self.assertEqual(len(self.view.sector_artists), 0)
    
    def test_callback_setting(self):
        """测试回调函数设置"""
        mock_callback = Mock()
        
        # 设置回调函数
        self.view.set_click_callback(mock_callback)
        self.view.set_right_click_callback(mock_callback)
        self.view.set_mouse_move_callback(mock_callback)
        self.view.set_double_click_callback(mock_callback)
        
        # 验证回调函数被设置
        self.assertEqual(self.view.on_click_callback, mock_callback)
        self.assertEqual(self.view.on_right_click_callback, mock_callback)
        self.assertEqual(self.view.on_mouse_move_callback, mock_callback)
        self.assertEqual(self.view.on_double_click_callback, mock_callback)


class TestMatplotlibController(unittest.TestCase):
    """
    Matplotlib控制器集成测试
    """
    
    def setUp(self):
        """测试前准备"""
        # 使用patch避免真实的GUI创建
        with patch('controllers.matplotlib_controller.MainWindow'), \
             patch('controllers.matplotlib_controller.MatplotlibView'), \
             patch('controllers.matplotlib_controller.InputPanel'):
            self.controller = MatplotlibController()
    
    def test_initialization(self):
        """测试控制器初始化"""
        self.assertIsNotNone(self.controller.device_manager)
        self.assertIsNone(self.controller.current_measurement)
        self.assertFalse(self.controller.is_running)
    
    def test_device_operations(self):
        """测试设备操作"""
        # 测试添加设备
        device = Device("控制器测试设备", 2.0, 3.0)
        
        # 由于使用Mock，我们测试操作不会抛出异常
        try:
            self.controller._on_device_add(device)
            self.controller._on_device_update(device, Device("更新设备", 3.0, 4.0))
            self.controller._on_device_delete(device)
        except Exception as e:
            self.fail(f"设备操作不应该抛出异常: {e}")
    
    def test_canvas_events(self):
        """测试Canvas事件处理"""
        # 测试点击事件
        try:
            self.controller._on_canvas_click(1.0, 2.0)
            self.controller._on_canvas_right_click()
            self.controller._on_canvas_mouse_move(0.5, 1.5)
            self.controller._on_canvas_double_click(2.0, 2.0)
        except Exception as e:
            self.fail(f"Canvas事件处理不应该抛出异常: {e}")
    
    def test_range_change(self):
        """测试坐标范围变更"""
        try:
            self.controller._on_range_change(10.0, 8.0)
        except Exception as e:
            self.fail(f"坐标范围变更不应该抛出异常: {e}")
    
    def test_application_info(self):
        """测试应用程序信息获取"""
        info = self.controller.get_application_info()
        
        # 验证必要字段存在
        self.assertIn('is_running', info)
        self.assertIn('device_count', info)
        self.assertIn('has_measurement', info)
        self.assertIn('view_type', info)
        self.assertEqual(info['view_type'], 'matplotlib')


class TestMatplotlibMigrationCompatibility(unittest.TestCase):
    """
    测试Matplotlib迁移的向后兼容性
    """
    
    def test_api_compatibility(self):
        """测试API向后兼容性"""
        with patch('views.matplotlib_view.FigureCanvasTkAgg'):
            view = MatplotlibView(Mock())
        
        # 验证原有API仍然可用
        self.assertTrue(hasattr(view, 'get_devices'))
        self.assertTrue(hasattr(view, 'get_measurement_point'))
        self.assertTrue(hasattr(view, 'add_device'))
        self.assertTrue(hasattr(view, 'remove_device'))
        self.assertTrue(hasattr(view, 'clear_devices'))
        
        # 验证新API存在
        self.assertTrue(hasattr(view, 'update_devices'))
        self.assertTrue(hasattr(view, 'export_to_png'))
        self.assertTrue(hasattr(view, 'draw_temporary_sector'))
    
    def test_performance_metrics(self):
        """测试性能指标"""
        import time
        
        with patch('views.matplotlib_view.FigureCanvasTkAgg'):
            view = MatplotlibView(Mock())
        
        # 测试大量设备的绘制性能
        devices = [Device(f"设备{i}", i*0.1, i*0.1) for i in range(100)]
        
        start_time = time.time()
        view.update_devices(devices)
        end_time = time.time()
        
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0, f"绘制100个设备耗时{render_time:.3f}秒，超过1秒限制")


def run_matplotlib_tests():
    """
    运行Matplotlib相关的所有测试
    """
    print("🧪 开始Matplotlib集成测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTest(unittest.makeSuite(TestMatplotlibView))
    test_suite.addTest(unittest.makeSuite(TestMatplotlibController))
    test_suite.addTest(unittest.makeSuite(TestMatplotlibMigrationCompatibility))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    print(f"\n📊 测试结果:")
    print(f"   总测试数: {result.testsRun}")
    print(f"   失败数: {len(result.failures)}")
    print(f"   错误数: {len(result.errors)}")
    print(f"   成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, error in result.failures:
            print(f"   - {test}: {error}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, error in result.errors:
            print(f"   - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_matplotlib_tests()
    sys.exit(0 if success else 1) 