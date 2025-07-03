# -*- coding: utf-8 -*-
"""
主控制器单元测试

使用pytest和monkeypatch来测试MainController的逻辑
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# 将项目根目录添加到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dev')))

from controllers.main_controller import MainController
from models.device_model import Device

@pytest.fixture
def mock_views(monkeypatch):
    """
    模拟所有视图依赖 (MainWindow, CanvasView, InputPanel)
    """
    monkeypatch.setattr("controllers.main_controller.MainWindow", MagicMock())
    monkeypatch.setattr("controllers.main_controller.CanvasView", MagicMock())
    monkeypatch.setattr("controllers.main_controller.InputPanel", MagicMock())

@pytest.fixture
def controller(mock_views):
    """
    创建一个被测试的MainController实例
    """
    # 模拟Tkinter主循环，防止测试挂起
    with patch('tkinter.Tk'):
        controller = MainController()
        # 模拟视图实例
        controller.main_window = MagicMock()
        controller.canvas_view = MagicMock()
        controller.input_panel = MagicMock()
        return controller

def test_add_device_success(controller: MainController):
    """
    测试成功添加一个设备
    """
    new_device = Device("新设备", 1.0, 1.0)
    controller.devices = [] # 确保开始时设备列表为空
    
    controller._on_device_add(new_device)
    
    assert len(controller.devices) == 1
    assert controller.devices[0].name == "新设备"
    controller.canvas_view.add_device.assert_called_once_with(new_device)

def test_add_device_duplicate_name(controller: MainController):
    """
    测试添加重名设备时是否会失败
    """
    existing_device = Device("已存在设备", 2.0, 2.0)
    controller.devices = [existing_device]
    
    new_device_with_same_name = Device("已存在设备", 3.0, 3.0)
    
    controller._on_device_add(new_device_with_same_name)
    
    # 控制器设备列表不应改变
    assert len(controller.devices) == 1
    # 不应调用canvas_view的add_device
    controller.canvas_view.add_device.assert_not_called()
    # 应该显示错误消息
    controller.main_window.show_message.assert_called_once()

def test_delete_device_success(controller: MainController):
    """
    测试成功删除一个设备
    """
    device_to_delete = Device("待删除设备", 1.5, 1.5)
    other_device = Device("保留设备", 2.5, 2.5)
    controller.devices = [device_to_delete, other_device]
    
    controller._on_device_delete(device_to_delete)
    
    assert len(controller.devices) == 1
    assert controller.devices[0].name == "保留设备"
    controller.canvas_view.remove_device.assert_called_once_with(device_to_delete)
    
def test_range_change_success(controller: MainController):
    """
    测试成功更改坐标范围
    """
    new_x_range, new_y_range = 10.0, 10.0
    
    controller._on_range_change(new_x_range, new_y_range)
    
    controller.canvas_view.set_coordinate_range.assert_called_once_with(new_x_range, new_y_range)
    
def test_range_change_invalid_value(controller: MainController):
    """
    测试使用无效值更改坐标范围
    """
    invalid_x_range, invalid_y_range = 30.0, -5.0 # x太大, y为负
    
    # 验证X轴范围过大的情况
    controller._on_range_change(invalid_x_range, 10.0)
    controller.canvas_view.set_coordinate_range.assert_not_called()
    controller.main_window.show_message.assert_called_with("范围设置错误", "坐标范围不能大于25.0", "error")
    
    controller.main_window.show_message.reset_mock() # 重置mock
    
    # 验证Y轴范围为负数的情况
    controller._on_range_change(10.0, invalid_y_range)
    controller.canvas_view.set_coordinate_range.assert_not_called()
    controller.main_window.show_message.assert_called_with("范围设置错误", "坐标范围必须大于0", "error")

def test_reset_functionality(controller: MainController):
    """
    测试重置功能
    """
    # 模拟用户在对话框中确认重置
    controller.main_window.ask_yes_no.return_value = True

    # 准备一些数据
    controller.devices = [Device("设备1", 1, 1), Device("设备2", 2, 2)]
    
    controller._on_reset()
    
    # 验证确认对话框被调用
    controller.main_window.ask_yes_no.assert_called_once_with("确认重置", "确定要清除所有数据吗？\n此操作不可撤销。")

    # 验证清理
    controller.canvas_view.clear_devices.assert_called_once()
    controller.canvas_view.clear_measurement.assert_called_once()
    
    # 验证重置范围
    controller.canvas_view.set_coordinate_range.assert_called_with(5.0, 5.0)
    
    # 验证设备列表已被清空
    assert len(controller.devices) == 0
    
    # 验证UI同步
    controller.input_panel.update_devices.assert_called_once_with([])
    controller.main_window.show_message.assert_called_with("重置完成", "所有数据已重置为初始状态", "info") 