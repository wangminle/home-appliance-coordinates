#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
焦点管理和设备选择清除功能测试

测试修复后的设备选择焦点管理功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

import unittest
from unittest.mock import Mock, patch
import tkinter as tk
from tkinter import ttk

from models.device_model import Device
from views.input_panel import InputPanel


class TestFocusManagement(unittest.TestCase):
    """焦点管理测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏窗口
        
        # 创建测试框架
        self.test_frame = tk.Frame(self.root)
        self.test_frame.pack()
        
        # 创建InputPanel实例
        self.input_panel = InputPanel(self.test_frame)
        
        # 创建测试设备
        self.test_devices = [
            Device("测试设备1", 1.0, 2.0),
            Device("测试设备2", 3.0, 4.0)
        ]
        
        # 更新设备列表
        self.input_panel.update_devices(self.test_devices)
        
        # 设置回调函数
        self.add_callback = Mock()
        self.update_callback = Mock()
        self.delete_callback = Mock()
        
        self.input_panel.set_device_add_callback(self.add_callback)
        self.input_panel.set_device_update_callback(self.update_callback)
        self.input_panel.set_device_delete_callback(self.delete_callback)
    
    def tearDown(self):
        """测试后清理"""
        self.root.destroy()
    
    def test_device_selection_and_clear(self):
        """测试设备选择和清除功能"""
        print("🧪 测试设备选择和清除功能")
        
        # 1. 初始状态检查
        self.assertIsNone(self.input_panel.selected_device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "添加设备")
        self.assertEqual(self.input_panel.delete_button.cget('state'), 'disabled')
        
        # 2. 选择设备
        device_id = self.test_devices[0].id
        self.input_panel.device_treeview.selection_set(device_id)
        self.input_panel._on_device_select()
        
        # 验证选择状态
        self.assertEqual(self.input_panel.selected_device_id, device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "更新设备")
        self.assertEqual(self.input_panel.delete_button.cget('state'), 'normal')
        self.assertEqual(self.input_panel.device_name_var.get(), "测试设备1")
        
        # 3. 清除选择
        self.input_panel.clear_selection()
        
        # 验证清除状态
        self.assertIsNone(self.input_panel.selected_device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "添加设备")
        self.assertEqual(self.input_panel.delete_button.cget('state'), 'disabled')
        self.assertEqual(self.input_panel.device_name_var.get(), "")
        
        print("✅ 设备选择和清除功能测试通过")
    
    def test_input_focus_clears_selection(self):
        """测试输入框焦点清除选择功能"""
        print("🧪 测试输入框焦点清除选择功能")
        
        # 1. 先选择一个设备
        device_id = self.test_devices[0].id
        self.input_panel.device_treeview.selection_set(device_id)
        self.input_panel._on_device_select()
        
        # 验证设备已选中
        self.assertEqual(self.input_panel.selected_device_id, device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "更新设备")
        
        # 2. 模拟点击输入框
        self.input_panel._on_input_focus()
        
        # 验证选择已清除
        self.assertIsNone(self.input_panel.selected_device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "添加设备")
        self.assertEqual(self.input_panel.delete_button.cget('state'), 'disabled')
        
        print("✅ 输入框焦点清除选择功能测试通过")
    
    def test_canvas_click_clears_selection(self):
        """测试Canvas点击清除选择功能"""
        print("🧪 测试Canvas点击清除选择功能")
        
        # 1. 先选择一个设备
        device_id = self.test_devices[0].id
        self.input_panel.device_treeview.selection_set(device_id)
        self.input_panel._on_device_select()
        
        # 验证设备已选中
        self.assertEqual(self.input_panel.selected_device_id, device_id)
        
        # 2. 模拟Canvas点击（通过clear_selection方法）
        self.input_panel.clear_selection()
        
        # 验证选择已清除
        self.assertIsNone(self.input_panel.selected_device_id)
        self.assertEqual(self.input_panel.add_update_button.cget('text'), "添加设备")
        
        print("✅ Canvas点击清除选择功能测试通过")
    
    def test_add_device_after_selection_clear(self):
        """测试清除选择后添加设备功能"""
        print("🧪 测试清除选择后添加设备功能")
        
        # 1. 选择设备
        device_id = self.test_devices[0].id
        self.input_panel.device_treeview.selection_set(device_id)
        self.input_panel._on_device_select()
        
        # 2. 清除选择
        self.input_panel.clear_selection()
        
        # 3. 输入新设备信息
        self.input_panel.device_name_var.set("新设备")
        self.input_panel.device_x_var.set("5.0")
        self.input_panel.device_y_var.set("6.0")
        
        # 4. 点击添加按钮
        self.input_panel._on_add_or_update()
        
        # 验证添加回调被调用
        self.add_callback.assert_called_once()
        
        # 验证添加的设备信息
        added_device = self.add_callback.call_args[0][0]
        self.assertEqual(added_device.name, "新设备")
        self.assertEqual(added_device.x, 5.0)
        self.assertEqual(added_device.y, 6.0)
        
        print("✅ 清除选择后添加设备功能测试通过")
    
    def test_event_binding_exists(self):
        """测试事件绑定是否存在"""
        print("🧪 测试事件绑定是否存在")
        
        # 检查TreeView选择事件绑定
        treeview_bindings = self.input_panel.device_treeview.bind()
        self.assertIn('<<TreeviewSelect>>', treeview_bindings)
        
        # 检查输入框焦点事件绑定
        name_entry_bindings = self.input_panel.name_entry.bind()
        self.assertIn('<Button-1>', name_entry_bindings)
        self.assertIn('<FocusIn>', name_entry_bindings)
        
        x_entry_bindings = self.input_panel.x_entry.bind()
        self.assertIn('<Button-1>', x_entry_bindings)
        self.assertIn('<FocusIn>', x_entry_bindings)
        
        y_entry_bindings = self.input_panel.y_entry.bind()
        self.assertIn('<Button-1>', y_entry_bindings)
        self.assertIn('<FocusIn>', y_entry_bindings)
        
        print("✅ 事件绑定存在性测试通过")


def run_tests():
    """运行所有测试"""
    print("🚀 开始焦点管理和设备选择清除功能测试")
    print("=" * 50)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFocusManagement)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 测试失败！")
        for failure in result.failures:
            print(f"失败: {failure[0]}")
            print(f"错误: {failure[1]}")
        for error in result.errors:
            print(f"错误: {error[0]}")
            print(f"详情: {error[1]}")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 