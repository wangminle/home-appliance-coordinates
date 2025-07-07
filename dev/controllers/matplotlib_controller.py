# -*- coding: utf-8 -*-
"""
Matplotlib坐标展示控制器

基于Matplotlib实现的控制器，替换原有的MainController
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List
import os
from datetime import datetime

from models.device_model import Device
from models.measurement_model import MeasurementPoint
from views.matplotlib_view import MatplotlibView
from views.input_panel import InputPanel
from models.device_manager import DeviceManager


class MatplotlibController:
    """
    基于Matplotlib的主控制器类
    
    管理数据模型和视图的交互，提供与原MainController兼容的接口
    """
    
    def __init__(self, root: tk.Tk):
        """
        初始化控制器
        
        Args:
            root: 主窗口
        """
        self.root = root
        
        # 创建数据管理器
        self.device_manager = DeviceManager()
        
        # 创建主界面
        self._create_main_interface()
        
        # 绑定事件
        self._bind_view_events()
        
        print("✅ MatplotlibController初始化完成")
    
    def _create_main_interface(self):
        """
        创建主界面布局
        """
        # 设置窗口标题和大小
        self.root.title("家居设备坐标距离角度绘制工具 - Matplotlib版")
        self.root.geometry("1280x800")
        self.root.resizable(False, False)
        
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)
        
        # 左侧画布区域 (800x800)
        left_frame = tk.Frame(main_frame, width=800, height=800, bg='#f0f0f0')
        left_frame.pack(side='left', fill='both')
        left_frame.pack_propagate(False)
        
        # 右侧输入面板区域 (480x800)
        right_frame = tk.Frame(main_frame, width=480, height=800, bg='#ffffff')
        right_frame.pack(side='right', fill='both')
        right_frame.pack_propagate(False)
        
        # 创建视图组件
        self.canvas_view = MatplotlibView(left_frame)
        self.input_panel = InputPanel(right_frame, self)
        
        print("✅ 主界面创建完成")
    
    def _bind_view_events(self):
        """
        绑定视图事件处理
        """
        # 绑定画布事件
        self.canvas_view.set_click_callback(self._on_canvas_click)
        self.canvas_view.set_right_click_callback(self._on_canvas_right_click)
        self.canvas_view.set_mouse_move_callback(self._on_canvas_mouse_move)
        self.canvas_view.set_double_click_callback(self._on_canvas_double_click)
        
        # 绑定输入面板事件
        self.input_panel.set_range_change_callback(self._on_range_change)
        self.input_panel.set_device_add_callback(self._on_device_add)
        self.input_panel.set_device_update_callback(self._on_device_update)
        self.input_panel.set_device_delete_callback(self._on_device_delete)
        self.input_panel.set_export_callback(self.export_png)
        self.input_panel.set_reset_callback(self.reset_all)
        
        # 绑定用户坐标系事件 ✨ 双坐标系功能
        self.input_panel.set_user_coord_toggle_callback(self._on_user_coord_toggle)
        self.input_panel.set_user_position_set_callback(self._on_user_position_set)
        
        # 初始化设备数据
        self.canvas_view.update_devices(self.device_manager.get_devices())
        self.input_panel.update_devices(self.device_manager.get_devices())
        
        print("✅ 视图事件绑定完成")
    
    def _on_canvas_click(self, x: float, y: float):
        """
        处理画布左键单击事件：创建测量点
        
        Args:
            x: 点击的X坐标
            y: 点击的Y坐标
        """
        print(f"📍 左键单击坐标: ({x:.3f}, {y:.3f})")
        # 测量点已在视图中处理，这里可以添加额外逻辑
    
    def _on_canvas_double_click(self, x: float, y: float):
        """
        处理画布左键双击事件：创建90度扇形
        
        Args:
            x: 双击的X坐标
            y: 双击的Y坐标
        """
        print(f"🔺 左键双击坐标: ({x:.3f}, {y:.3f}) - 绘制90度扇形")
        # 扇形已在视图中处理，这里可以添加额外逻辑
    
    def _on_canvas_right_click(self):
        """
        处理画布右键单击事件：清除所有测量点和扇形
        """
        print("🧹 右键点击 - 清除所有测量点和扇形")
        # 清除已在视图中处理，这里可以添加额外逻辑
    
    def _on_canvas_mouse_move(self, x: float, y: float):
        """
        处理画布鼠标移动事件
        
        Args:
            x: 鼠标的X坐标
            y: 鼠标的Y坐标
        """
        # 可以在这里显示鼠标坐标信息（如果需要）
        pass
    
    # === 输入面板事件处理 ===
    
    def _on_range_change(self, x_range: float, y_range: float):
        """
        处理坐标范围变化事件 ✨ 第五步增强：更新状态指示器
        """
        self.set_coordinate_range(x_range, y_range)
        # 更新范围状态（确保UI同步）
        self.input_panel.update_range_status(x_range, y_range)
    
    def _on_device_add(self, device: Device):
        """
        处理设备添加事件
        """
        success = self.add_device(device.name, device.x, device.y)
        if success:
            # 更新输入面板显示
            self.input_panel.update_devices(self.device_manager.get_devices())
    
    def _on_device_update(self, old_device: Device, new_device: Device):
        """
        处理设备更新事件
        """
        success = self.update_device(old_device.id, new_device.name, new_device.x, new_device.y)
        if success:
            # 更新输入面板显示
            self.input_panel.update_devices(self.device_manager.get_devices())
    
    def _on_device_delete(self, device: Device):
        """
        处理设备删除事件
        """
        success = self.delete_device(device.id)
        if success:
            # 更新输入面板显示
            self.input_panel.update_devices(self.device_manager.get_devices())

    # === 用户坐标系事件处理 ✨ 双坐标系功能 ===
    
    def _on_user_coord_toggle(self, enabled: bool):
        """
        处理用户坐标系开关切换事件 ✨ 第五步增强：更新状态指示器
        
        Args:
            enabled: True表示启用，False表示关闭
        """
        print(f"✨ 控制器收到用户坐标系{'启用' if enabled else '关闭'}事件")
        
        # 通知视图切换坐标系模式
        self.canvas_view.set_user_coordinate_mode(enabled)
        
        # 更新状态指示器 ✨ 第五步新增功能
        self.input_panel.update_coordinate_mode_status(enabled)
        
        if not enabled:
            # 关闭时清除用户位置
            self.canvas_view.clear_user_position()
            # 更新用户位置状态为未设置
            self.input_panel.update_user_position_status(None)
    
    def _on_user_position_set(self, x: float, y: float):
        """
        处理用户位置设置事件 ✨ 第五步增强：更新状态指示器
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
        """
        print(f"✨ 控制器收到设置用户位置事件: ({x:.3f}, {y:.3f})")
        
        # 通知视图设置用户位置
        self.canvas_view.set_user_position(x, y)
        
        # 更新用户位置状态指示器 ✨ 第五步新增功能
        self.input_panel.update_user_position_status((x, y))

    # === 设备管理方法 ===
    
    def add_device(self, name: str, x: float, y: float) -> bool:
        """
        添加设备
        
        Args:
            name: 设备名称
            x: X坐标
            y: Y坐标
            
        Returns:
            True如果添加成功，否则False
        """
        try:
            device = Device(name, x, y)
            self.device_manager.add_device(device)
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            
            print(f"✅ 设备添加成功: {name} ({x:.3f}, {y:.3f})")
            return True
            
        except Exception as e:
            messagebox.showerror("添加设备失败", f"无法添加设备: {str(e)}")
            print(f"❌ 设备添加失败: {e}")
            return False
    
    def update_device(self, device_id: str, name: str, x: float, y: float) -> bool:
        """
        更新设备信息
        
        Args:
            device_id: 设备ID
            name: 新的设备名称
            x: 新的X坐标
            y: 新的Y坐标
            
        Returns:
            True如果更新成功，否则False
        """
        try:
            new_device = Device(name, x, y)
            self.device_manager.update_device(device_id, new_device)
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            
            print(f"✅ 设备更新成功: {name} ({x:.3f}, {y:.3f})")
            return True
            
        except Exception as e:
            messagebox.showerror("更新设备失败", f"无法更新设备: {str(e)}")
            print(f"❌ 设备更新失败: {e}")
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """
        删除设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            True如果删除成功，否则False
        """
        try:
            device = self.device_manager.get_device_by_id(device_id)
            if device:
                device_name = device.name
                self.device_manager.delete_device(device_id)
                
                # 更新视图
                self.canvas_view.update_devices(self.device_manager.get_devices())
                
                print(f"✅ 设备删除成功: {device_name}")
                return True
            else:
                print(f"❌ 设备不存在: {device_id}")
                return False
            
        except Exception as e:
            messagebox.showerror("删除设备失败", f"无法删除设备: {str(e)}")
            print(f"❌ 设备删除失败: {e}")
            return False
    
    def get_all_devices(self) -> List[Device]:
        """
        获取所有设备
        
        Returns:
            设备列表
        """
        return self.device_manager.get_devices()
    
    def get_device_by_id(self, device_id: str) -> Device:
        """
        根据ID获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备对象，如果不存在则返回None
        """
        return self.device_manager.get_device_by_id(device_id)
    
    # === 坐标范围管理 ===
    
    def set_coordinate_range(self, x_range: float, y_range: float):
        """
        设置坐标显示范围
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
        """
        try:
            # 验证范围有效性
            if x_range <= 0 or y_range <= 0:
                raise ValueError("坐标范围必须大于0")
            
            if x_range < 0.1 or x_range > 50:
                raise ValueError("X轴范围必须在0.1-50之间")
            
            if y_range < 0.1 or y_range > 50:
                raise ValueError("Y轴范围必须在0.1-50之间")
            
            # 更新视图
            self.canvas_view.set_coordinate_range(x_range, y_range)
            
            print(f"✅ 坐标范围设置成功: ±{x_range} x ±{y_range}")
            
        except Exception as e:
            messagebox.showerror("设置坐标范围失败", f"无法设置坐标范围: {str(e)}")
            print(f"❌ 坐标范围设置失败: {e}")
    
    # === 导出功能 ===
    
    def export_png(self):
        """
        导出PNG图片
        """
        try:
            # 生成默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"家居设备布局图_{timestamp}.png"
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="导出PNG图片",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not file_path:
                print("⚠️ 用户取消导出")
                return
            
            # 执行导出
            success = self.canvas_view.export_to_png(file_path, dpi=300)
            
            if success:
                messagebox.showinfo("导出成功", f"PNG图片已成功导出到:\n{file_path}")
                print(f"✅ PNG导出成功: {file_path}")
            else:
                messagebox.showerror("导出失败", "PNG图片导出失败，请检查文件路径和权限")
                print("❌ PNG导出失败")
                
        except Exception as e:
            messagebox.showerror("导出错误", f"导出过程中发生错误: {str(e)}")
            print(f"❌ PNG导出错误: {e}")
    
    # === 重置功能 ===
    
    def reset_all(self):
        """
        重置所有数据
        """
        try:
            # 弹出确认对话框
            result = messagebox.askyesno(
                "确认重置", 
                "这将清除所有设备数据、测量点和扇形，\n并重置坐标范围为默认值。\n\n确定要继续吗？",
                icon='warning'
            )
            
            if not result:
                print("⚠️ 用户取消重置")
                return
            
            # 清除设备数据
            self.device_manager.clear_all_devices()
            
            # 清除视图
            self.canvas_view.clear_all()
            
            # 重置坐标范围
            self.canvas_view.set_coordinate_range(10.0, 10.0)
            
            # 重置输入面板
            self.input_panel.reset_inputs()
            
            print("✅ 重置完成")
            messagebox.showinfo("重置完成", "所有数据已成功重置")
            
        except Exception as e:
            messagebox.showerror("重置失败", f"重置过程中发生错误: {str(e)}")
            print(f"❌ 重置失败: {e}")
    
    # === 测量点功能 ===
    
    def get_measurement_point(self) -> MeasurementPoint:
        """
        获取当前测量点
        
        Returns:
            测量点对象，如果没有则返回None
        """
        return self.canvas_view.get_measurement_point()
    
    def clear_measurement(self):
        """
        清除测量点
        """
        # 通过右键点击处理即可清除
        self._on_canvas_right_click()
    
    # === 兼容性接口 ===
    
    def refresh_view(self):
        """
        刷新视图（兼容性接口）
        """
        # Matplotlib会自动刷新，无需手动调用
        print("✓ 视图刷新请求（Matplotlib自动处理）")
    
    def get_canvas_view(self):
        """
        获取画布视图对象（兼容性接口）
        
        Returns:
            MatplotlibView对象
        """
        return self.canvas_view 