# -*- coding: utf-8 -*-
"""
主控制器

协调整个应用程序的运行，连接视图和模型
"""

import sys
import os
from typing import List, Optional
import traceback

# 确保能够导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.main_window import MainWindow
from views.canvas_view import CanvasView
from views.input_panel import InputPanel
from models.device_model import Device
from models.device_manager import DeviceManager
from models.coordinate_model import CoordinateSystem
from models.measurement_model import MeasurementPoint
from utils.export_utils import ExportUtils
from utils.validation import Validator


class MainController:
    """
    主控制器类
    
    管理整个应用程序的运行，协调各个组件之间的交互
    """
    
    def __init__(self):
        """
        初始化主控制器
        """
        # 视图组件
        self.main_window: Optional[MainWindow] = None
        self.canvas_view: Optional[CanvasView] = None
        self.input_panel: Optional[InputPanel] = None
        
        # 数据管理 - 使用统一的设备管理器
        self.device_manager = DeviceManager()
        self.current_measurement: Optional[MeasurementPoint] = None
        
        # 应用状态
        self.is_running = False
        
        try:
            self._initialize_application()
        except Exception as e:
            print(f"应用程序初始化失败: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def _initialize_application(self):
        """
        初始化应用程序组件
        """
        # 创建主窗口
        self.main_window = MainWindow()
        
        # 设置窗口关闭回调
        self.main_window.set_close_callback(self._on_application_close)
        
        # 创建Canvas视图
        canvas_frame = self.main_window.get_canvas_frame()
        self.canvas_view = CanvasView(canvas_frame)
        
        # 创建输入面板
        panel_frame = self.main_window.get_panel_frame()
        self.input_panel = InputPanel(panel_frame)
        
        # 设置回调函数
        self._setup_callbacks()
        
        # 设置设备管理器观察者，实现数据同步
        self._setup_device_sync()
        
        print("✅ 应用程序初始化完成")
    
    def _setup_callbacks(self):
        """
        设置各组件间的回调函数
        """
        # Canvas视图回调
        self.canvas_view.set_click_callback(self._on_canvas_click)
        self.canvas_view.set_right_click_callback(self._on_canvas_right_click)
        self.canvas_view.set_mouse_move_callback(self._on_canvas_mouse_move)
        self.canvas_view.set_double_click_callback(self._on_canvas_double_click)
        
        # 主窗口快捷键回调
        self.main_window.set_export_shortcut_callback(self._on_export)
        self.main_window.set_reset_shortcut_callback(self._on_reset)
        
        # 输入面板回调
        self.input_panel.set_range_change_callback(self._on_range_change)
        self.input_panel.set_device_add_callback(self._on_device_add)
        self.input_panel.set_device_update_callback(self._on_device_update)
        self.input_panel.set_device_delete_callback(self._on_device_delete)
        self.input_panel.set_export_callback(self._on_export)
        self.input_panel.set_reset_callback(self._on_reset)
    
    def _setup_device_sync(self):
        """
        设置设备数据同步机制
        """
        # 将DeviceManager的数据观察者设置为同步方法
        self.device_manager.add_observer(self._on_devices_changed)
        
        # 初始同步一次数据到各个组件
        initial_devices = self.device_manager.get_devices()
        self._sync_devices_to_components(initial_devices)
        
        print(f"✅ 设备数据同步机制已建立，当前有 {len(initial_devices)} 个设备")
    
    def _on_devices_changed(self, devices: List[Device]):
        """
        设备数据变更回调，同步到所有组件
        
        Args:
            devices: 最新的设备列表
        """
        self._sync_devices_to_components(devices)
    
    def _sync_devices_to_components(self, devices: List[Device]):
        """
        将设备数据同步到所有视图组件
        
        Args:
            devices: 要同步的设备列表
        """
        try:
            # 同步到Canvas视图
            if self.canvas_view:
                self.canvas_view.update_devices(devices)
            
            # 同步到输入面板
            if self.input_panel:
                self.input_panel.update_devices(devices)
            
        except Exception as e:
            print(f"⚠️ 设备数据同步失败: {e}")
    
    # Canvas事件处理
    
    def _on_canvas_click(self, x: float, y: float):
        """
        Canvas点击事件处理
        
        Args:
            x, y: 点击的逻辑坐标
        """
        print(f"📍 Canvas点击: ({x:.3f}, {y:.3f})")
        
        # 清除输入面板的设备选择（用户点击Canvas时取消设备选择）
        if self.input_panel:
            self.input_panel.clear_selection()
        
        # 获取测量点
        self.current_measurement = self.canvas_view.get_measurement_point()
        
        if self.current_measurement:
            info = self.current_measurement.get_formatted_info(3)
            print(f"📏 测量信息:")
            print(f"   {info['coordinates']}")
            print(f"   {info['distance']}")
            print(f"   {info['angle']}")
    
    def _on_canvas_right_click(self):
        """
        Canvas右键点击事件处理
        """
        print("🧹 清除测量点")
        self.current_measurement = None
    
    def _on_canvas_mouse_move(self, x: float, y: float):
        """
        Canvas鼠标移动事件处理
        
        Args:
            x, y: 鼠标位置的逻辑坐标
        """
        # 这里可以添加实时坐标显示逻辑
        # 为了性能考虑，暂时不打印每次移动
        pass

    def _on_canvas_double_click(self, x: float, y: float):
        """
        Canvas双击事件处理

        Args:
            x, y: 双击位置的逻辑坐标
        """
        print(f"🖱️ Canvas双击: ({x:.3f}, {y:.3f})")
        # 在canvas上绘制一个90度的扇形区域
        self.canvas_view.draw_temporary_sector(x, y, 90)
    
    # 输入面板事件处理
    
    def _on_range_change(self, x_range: float, y_range: float):
        """
        坐标范围变化事件处理
        
        Args:
            x_range, y_range: 新的坐标范围
        """
        print(f"📐 坐标范围变更: ±{x_range} x ±{y_range}")
        
        try:
            # 验证范围
            is_valid, error_msg = Validator.validate_coordinate_range(x_range)
            if not is_valid:
                raise ValueError(error_msg)
            
            is_valid, error_msg = Validator.validate_coordinate_range(y_range)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 应用到Canvas视图
            self.canvas_view.set_coordinate_range(x_range, y_range)
            
            print("✅ 坐标范围更新成功")
            
        except ValueError as e:
            print(f"❌ 坐标范围更新失败: {e}")
            self.main_window.show_message("范围设置错误", str(e), "error")
    
    def _on_device_add(self, device: Device):
        """
        设备添加事件处理
        
        Args:
            device: 新添加的设备
        """
        print(f"➕ 添加设备: {device.name} ({device.x}, {device.y})")
        
        # 使用设备管理器的事务式操作
        success, message = self.device_manager.add_device(device)
        
        if success:
            # 成功 - 设备管理器会自动通知观察者同步数据
            print(f"✅ {message}")
        else:
            # 失败 - 显示错误消息
            print(f"❌ 设备添加失败: {message}")
            self.main_window.show_message("添加设备失败", message, "error")
    
    def _on_device_update(self, old_device: Device, new_device: Device):
        """
        设备更新事件处理
        
        Args:
            old_device: 旧设备对象
            new_device: 新设备对象
        """
        print(f"✏️ 更新设备: {old_device.name} -> {new_device.name}")
        
        # 使用设备管理器的事务式操作
        success, message = self.device_manager.update_device(old_device.id, new_device)
        
        if success:
            # 成功 - 设备管理器会自动通知观察者同步数据
            print(f"✅ {message}")
        else:
            # 失败 - 显示错误消息
            print(f"❌ 设备更新失败: {message}")
            self.main_window.show_message("更新设备失败", message, "error")
    
    def _on_device_delete(self, device: Device):
        """
        设备删除事件处理
        
        Args:
            device: 要删除的设备
        """
        print(f"➖ 删除设备: {device.name}")
        
        # 使用设备管理器的事务式操作
        success, message = self.device_manager.delete_device(device.id)
        
        if success:
            # 成功 - 设备管理器会自动通知观察者同步数据
            print(f"✅ {message}")
        else:
            # 失败 - 显示错误消息
            print(f"❌ 设备删除失败: {message}")
            self.main_window.show_message("删除设备失败", message, "error")
    
    def _on_export(self):
        """
        导出PNG图像事件处理
        """
        print("📷 开始导出PNG图像...")
        
        try:
            # 1. 获取文件保存路径
            file_path = ExportUtils.get_file_save_path(
                parent_window=self.main_window.root
            )
            
            if not file_path:
                print("📷 用户取消导出")
                return
            
            # 2. 验证文件路径
            is_valid, error_msg = Validator.validate_file_path(file_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 3. 调用新的绘制方法
            print("🎨 正在生成高清图像...")
            image = ExportUtils.draw_view_on_image(self.canvas_view)
            
            if not image:
                raise RuntimeError("生成图像失败，请查看控制台错误信息。")

            # 4. 保存图像到文件
            print(f"💾 正在保存图像到: {file_path}")
            success = ExportUtils.save_image_to_file(image, file_path)

            if success:
                print("✅ 导出成功")
                self.main_window.show_message(
                    "导出成功", 
                    f"图像已成功保存到:\n{file_path}",
                    "info"
                )
            else:
                raise RuntimeError("保存图像文件失败，请查看控制台错误信息。")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            self.main_window.show_message("导出失败", str(e), "error")
    
    def _on_reset(self):
        """
        重置所有数据事件处理
        """
        # 增加一个确认对话框
        if not self.main_window.ask_yes_no("确认重置", "确定要清除所有数据吗？\n此操作不可撤销。"):
            print("🔄 用户取消重置")
            return
            
        print("🔄 重置所有数据...")
        
        try:
            # 清除设备管理器中的所有设备
            success, message = self.device_manager.clear_all_devices()
            if not success:
                raise RuntimeError(message)
            
            # 清除Canvas中的测量点
            self.canvas_view.clear_measurement()
            
            # 重置坐标范围到默认值
            self.canvas_view.set_coordinate_range(5.0, 5.0)
            
            # 清除本地测量数据
            self.current_measurement = None
            
            # 更新坐标范围输入框的值
            self.input_panel.x_range_var.set("5.0")
            self.input_panel.y_range_var.set("5.0")
            
            print("✅ 重置完成")
            self.main_window.show_message("重置完成", "所有数据已重置为初始状态", "info")
            
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            self.main_window.show_message("重置失败", str(e), "error")
    
    def _on_application_close(self):
        """
        应用程序关闭事件处理
        """
        print("👋 应用程序关闭中...")
        
        try:
            # 保存应用状态（可选）
            # TODO: 实现状态保存逻辑
            
            # 清理资源
            self.is_running = False
            
            # 销毁窗口
            if self.main_window:
                self.main_window.destroy()
            
            print("✅ 应用程序已关闭")
            
        except Exception as e:
            print(f"⚠️ 关闭时出现错误: {e}")
    
    # 公共接口方法
    
    def run(self):
        """
        启动应用程序主循环
        """
        if not self.main_window:
            raise RuntimeError("应用程序未正确初始化")
        
        self.is_running = True
        print("🚀 应用程序启动")
        
        try:
            # 显示主窗口
            self.main_window.show()
            
            # 启动GUI主循环
            self.main_window.run()
            
        except KeyboardInterrupt:
            print("\n⚡ 用户中断应用程序")
        except Exception as e:
            print(f"💥 应用程序运行时错误: {e}")
            traceback.print_exc()
        finally:
            self.is_running = False
    
    def get_devices(self) -> List[Device]:
        """
        获取当前所有设备
        
        Returns:
            设备列表副本
        """
        return self.device_manager.get_devices()
    
    def get_measurement_point(self) -> Optional[MeasurementPoint]:
        """
        获取当前测量点
        
        Returns:
            测量点对象或None
        """
        return self.current_measurement
    
    def get_application_info(self) -> dict:
        """
        获取应用程序状态信息
        
        Returns:
            包含应用程序状态的字典
        """
        return {
            'is_running': self.is_running,
            'device_count': self.device_manager.get_device_count(),
            'has_measurement': self.current_measurement is not None,
            'window_geometry': self.main_window.get_window_geometry() if self.main_window else {}
        } 