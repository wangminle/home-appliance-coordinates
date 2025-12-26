# -*- coding: utf-8 -*-
"""
Matplotlib坐标展示控制器

基于Matplotlib实现的控制器，替换原有的MainController
支持项目文件管理和数据持久化功能
"""

import tkinter as tk
from tkinter import messagebox, filedialog, Menu
from typing import List, Optional, Dict, Any
import os
import threading
from datetime import datetime
from pathlib import Path

from models.device_model import Device
from models.measurement_model import MeasurementPoint
from models.background_model import BackgroundImage
from models.locked_measurement import LockedMeasurement
from views.matplotlib_view import MatplotlibView
from views.input_panel import InputPanel
from models.device_manager import DeviceManager
from models.project_manager import ProjectManager
from models.config_manager import ConfigManager
from utils.validation import Validator


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
        self.project_manager = ProjectManager()
        self.config_manager = ConfigManager()
        
        # 自动保存定时器ID
        self.autosave_timer_id: Optional[str] = None
        # 自动保存后台线程控制（避免阻塞UI）
        self._autosave_lock = threading.Lock()
        self._autosave_in_progress = False
        
        # 创建主界面
        self._create_main_interface()
        
        # 创建文件菜单
        self._create_menu_bar()
        
        # 绑定事件
        self._bind_view_events()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_closing)
        
        # 启动自动保存
        self._start_autosave()
        
        # 检查是否有草稿文件需要恢复
        self._check_autosave_recovery()
        
        print("[OK] MatplotlibController初始化完成")
    
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
        
        print("[OK] 主界面创建完成")
    
    def _create_menu_bar(self):
        """
        创建菜单栏
        """
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件(F)", menu=file_menu)
        
        file_menu.add_command(label="新建项目", accelerator="Ctrl+N", command=self.new_project)
        file_menu.add_command(label="打开项目...", accelerator="Ctrl+O", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="保存项目", accelerator="Ctrl+S", command=self.save_project)
        file_menu.add_command(label="另存为...", accelerator="Ctrl+Shift+S", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="导入设备(CSV)...", command=self.import_devices_csv)
        file_menu.add_command(label="导出设备(CSV)...", command=self.export_devices_csv)
        file_menu.add_separator()
        
        # 最近文件子菜单
        self.recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近打开", menu=self.recent_menu)
        self._update_recent_files_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="退出", accelerator="Alt+F4", command=self._on_window_closing)
        
        # 绑定快捷键
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_project_as())
        
        print("[OK] 菜单栏创建完成")
    
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
        
        # 绑定用户坐标系事件 - 双坐标系功能
        self.input_panel.set_user_coord_toggle_callback(self._on_user_coord_toggle)
        self.input_panel.set_user_position_set_callback(self._on_user_position_set)
        
        # 绑定背景图事件 - V2.5 背景户型图功能
        self.input_panel.set_background_import_callback(self._on_background_import)
        self.input_panel.set_background_remove_callback(self._on_background_remove)
        self.input_panel.set_background_scale_change_callback(self._on_background_scale_change)
        self.input_panel.set_background_alpha_change_callback(self._on_background_alpha_change)
        self.input_panel.set_background_visibility_toggle_callback(self._on_background_visibility_toggle)
        
        # 初始化设备数据
        self.canvas_view.update_devices(self.device_manager.get_devices())
        self.input_panel.update_devices(self.device_manager.get_devices())
        
        print("[OK] 视图事件绑定完成")
    
    def _on_canvas_click(self, x: float, y: float):
        """
        处理画布左键单击事件：创建测量点
        
        Args:
            x: 点击的X坐标
            y: 点击的Y坐标
        """
        print(f"[INFO] 左键单击坐标: ({x:.3f}, {y:.3f})")
        # 测量点已在视图中处理，这里可以添加额外逻辑
    
    def _on_canvas_double_click(self, x: float, y: float):
        """
        处理画布左键双击事件：创建90度扇形（以连线为平分线向两侧各45度）
        
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
        处理坐标范围变化事件 - 第五步增强：更新状态指示器
        """
        self.set_coordinate_range(x_range, y_range)
        # 更新范围状态（确保UI同步）
        self.input_panel.update_range_status(x_range, y_range)
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()
    
    def _on_device_add(self, device: Device):
        """
        处理设备添加事件
        """
        # 保留从输入面板传入的颜色信息
        success = self.add_device(device.name, device.x, device.y, device.color)
        if success:
            # 更新输入面板显示
            self.input_panel.update_devices(self.device_manager.get_devices())
    
    def _on_device_update(self, old_device: Device, new_device: Device):
        """
        处理设备更新事件
        """
        # 同步更新颜色信息
        success = self.update_device(
            old_device.id,
            new_device.name,
            new_device.x,
            new_device.y,
            new_device.color
        )
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

    # === 用户坐标系事件处理 - 双坐标系功能 ===
    
    def _on_user_coord_toggle(self, enabled: bool):
        """
        处理用户坐标系开关切换事件 - 第五步增强：更新状态指示器
        
        Args:
            enabled: True表示启用，False表示关闭
        """
        print(f"- 控制器收到用户坐标系{'启用' if enabled else '关闭'}事件")
        
        # 通知视图切换坐标系模式
        self.canvas_view.set_user_coordinate_mode(enabled)
        
        # 更新状态指示器 - 第五步新增功能
        self.input_panel.update_coordinate_mode_status(enabled)
        
        if not enabled:
            # 关闭时清除用户位置
            self.canvas_view.clear_user_position()
            # 更新用户位置状态为未设置
            self.input_panel.update_user_position_status(None)
        
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()
    
    def _on_user_position_set(self, x: float, y: float):
        """
        处理用户位置设置事件 - 第五步增强：更新状态指示器
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
        """
        print(f"- 控制器收到设置用户位置事件: ({x:.3f}, {y:.3f})")
        
        # 通知视图设置用户位置
        self.canvas_view.set_user_position(x, y)
        
        # 更新用户位置状态指示器 - 第五步新增功能
        self.input_panel.update_user_position_status((x, y))
        
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()

    # === 背景图事件处理 - V2.5 背景户型图功能 ===
    
    def _on_background_import(self, file_path: str):
        """
        处理背景图导入事件
        
        Args:
            file_path: 图片文件路径
        """
        print(f"📂 控制器收到导入背景图请求: {file_path}")
        
        # 创建背景图对象并加载
        bg = BackgroundImage()
        
        if bg.load_from_file(file_path):
            # 获取当前输入面板中的比例设置
            try:
                ppu = float(self.input_panel.bg_ppu_var.get())
                if ppu > 0:
                    bg.set_pixels_per_unit(ppu)
            except (ValueError, AttributeError):
                pass
            
            # 获取当前透明度设置
            try:
                alpha = self.input_panel.bg_alpha_var.get()
                bg.set_alpha(alpha)
            except AttributeError:
                pass
            
            # 设置到视图
            self.canvas_view.set_background_image(bg)
            
            # 更新输入面板信息
            actual_w, actual_h = bg.get_actual_size()
            self.input_panel.update_background_info(
                pixel_width=bg.pixel_width,
                pixel_height=bg.pixel_height,
                dpi=bg.dpi,
                actual_width=actual_w,
                actual_height=actual_h,
                x_min=bg.x_min,
                x_max=bg.x_max,
                y_min=bg.y_min,
                y_max=bg.y_max
            )
            
            # 标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
            
            print(f"[OK] 背景图导入成功: {actual_w:.1f}m × {actual_h:.1f}m")
        else:
            messagebox.showerror("导入失败", "无法加载图片文件，请检查文件格式")
    
    def _on_background_remove(self):
        """处理背景图移除事件"""
        print("[INFO] 控制器收到移除背景图请求")
        
        self.canvas_view.remove_background()
        
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()
    
    def _on_background_scale_change(self, ppu: float):
        """
        处理背景图比例变化事件
        
        Args:
            ppu: 每格像素数
        """
        print(f"[INFO] 控制器收到背景图比例变化: {ppu} px/格")
        
        if self.canvas_view.update_background_scale(ppu):
            # 更新输入面板显示
            bg = self.canvas_view.get_background_image()
            if bg:
                actual_w, actual_h = bg.get_actual_size()
                self.input_panel.update_background_info(
                    pixel_width=bg.pixel_width,
                    pixel_height=bg.pixel_height,
                    dpi=bg.dpi,
                    actual_width=actual_w,
                    actual_height=actual_h,
                    x_min=bg.x_min,
                    x_max=bg.x_max,
                    y_min=bg.y_min,
                    y_max=bg.y_max
                )
            
            # 标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
    
    def _on_background_alpha_change(self, alpha: float):
        """
        处理背景图透明度变化事件
        
        Args:
            alpha: 透明度值
        """
        self.canvas_view.update_background_alpha(alpha)
        
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()
    
    def _on_background_visibility_toggle(self, visible: bool):
        """
        处理背景图显示切换事件
        
        Args:
            visible: 是否显示
        """
        self.canvas_view.toggle_background_visibility(visible)
        
        # 标记项目已修改
        self.project_manager.mark_modified()
        self._update_window_title()
    
    # === 背景图公共接口 ===
    
    def set_background_image(self, bg_image: BackgroundImage):
        """
        设置背景图（供外部调用）
        
        Args:
            bg_image: BackgroundImage 对象
        """
        self.canvas_view.set_background_image(bg_image)
        
        # 更新输入面板
        if bg_image and bg_image.is_loaded():
            actual_w, actual_h = bg_image.get_actual_size()
            self.input_panel.update_background_info(
                pixel_width=bg_image.pixel_width,
                pixel_height=bg_image.pixel_height,
                dpi=bg_image.dpi,
                actual_width=actual_w,
                actual_height=actual_h,
                x_min=bg_image.x_min,
                x_max=bg_image.x_max,
                y_min=bg_image.y_min,
                y_max=bg_image.y_max
            )
            self.input_panel.set_background_ppu(bg_image.pixels_per_unit)
            self.input_panel.set_background_alpha(bg_image.alpha)
            self.input_panel.set_background_visible(bg_image.enabled)
    
    def get_background_image(self) -> Optional[BackgroundImage]:
        """
        获取当前背景图
        
        Returns:
            BackgroundImage 对象
        """
        return self.canvas_view.get_background_image()
    
    def update_background_scale(self, ppu: float):
        """
        更新背景图比例（供外部调用）
        
        Args:
            ppu: 每格像素数
        """
        self._on_background_scale_change(ppu)
    
    def update_background_alpha(self, alpha: float):
        """
        更新背景图透明度（供外部调用）
        
        Args:
            alpha: 透明度值
        """
        self._on_background_alpha_change(alpha)
    
    def toggle_background_visibility(self, visible: bool):
        """
        切换背景图显示（供外部调用）
        
        Args:
            visible: 是否显示
        """
        self._on_background_visibility_toggle(visible)
    
    def remove_background(self):
        """移除背景图（供外部调用）"""
        self._on_background_remove()
        self.input_panel._reset_background_ui()

    # === 设备管理方法 ===
    
    def add_device(self, name: str, x: float, y: float, color: Optional[str] = None) -> bool:
        """
        添加设备
        
        Args:
            name: 设备名称
            x: X坐标
            y: Y坐标
            color: 设备颜色（可选）
            
        Returns:
            True如果添加成功，否则False
        """
        try:
            device = Device(name, x, y, color=color)
            # 检查 DeviceManager 的返回值
            success, message = self.device_manager.add_device(device)
            
            if not success:
                # 底层验证失败，显示错误消息
                messagebox.showerror("添加设备失败", message)
                print(f"[ERROR] 设备添加失败: {message}")
                return False
            
            # 只有成功时才标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            
            print(f"[OK] 设备添加成功: {name} ({x:.3f}, {y:.3f})")
            return True
            
        except Exception as e:
            messagebox.showerror("添加设备失败", f"无法添加设备: {str(e)}")
            print(f"[ERROR] 设备添加失败: {e}")
            return False
    
    def update_device(self, device_id: str, name: str, x: float, y: float, color: Optional[str] = None) -> bool:
        """
        更新设备信息
        
        Args:
            device_id: 设备ID
            name: 新的设备名称
            x: 新的X坐标
            y: 新的Y坐标
            color: 新的设备颜色（可选）
            
        Returns:
            True如果更新成功，否则False
        """
        try:
            new_device = Device(name, x, y, color=color)
            # 检查 DeviceManager 的返回值
            success, message = self.device_manager.update_device(device_id, new_device)
            
            if not success:
                # 底层验证失败，显示错误消息
                messagebox.showerror("更新设备失败", message)
                print(f"[ERROR] 设备更新失败: {message}")
                return False
            
            # 只有成功时才标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            
            print(f"[OK] 设备更新成功: {name} ({x:.3f}, {y:.3f})")
            return True
            
        except Exception as e:
            messagebox.showerror("更新设备失败", f"无法更新设备: {str(e)}")
            print(f"[ERROR] 设备更新失败: {e}")
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
            if not device:
                messagebox.showerror("删除设备失败", "设备不存在")
                print(f"[ERROR] 设备不存在: {device_id}")
                return False
            
            device_name = device.name
            # 检查 DeviceManager 的返回值
            success, message = self.device_manager.delete_device(device_id)
            
            if not success:
                # 底层操作失败，显示错误消息
                messagebox.showerror("删除设备失败", message)
                print(f"[ERROR] 设备删除失败: {message}")
                return False
            
            # 只有成功时才标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            
            print(f"[OK] 设备删除成功: {device_name}")
            return True
            
        except Exception as e:
            messagebox.showerror("删除设备失败", f"无法删除设备: {str(e)}")
            print(f"[ERROR] 设备删除失败: {e}")
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
            
            if x_range < Validator.MIN_COORDINATE_RANGE or x_range > Validator.MAX_COORDINATE_RANGE:
                raise ValueError(f"X轴范围必须在{Validator.MIN_COORDINATE_RANGE}-{Validator.MAX_COORDINATE_RANGE}之间")
            
            if y_range < Validator.MIN_COORDINATE_RANGE or y_range > Validator.MAX_COORDINATE_RANGE:
                raise ValueError(f"Y轴范围必须在{Validator.MIN_COORDINATE_RANGE}-{Validator.MAX_COORDINATE_RANGE}之间")
            
            # 更新视图
            self.canvas_view.set_coordinate_range(x_range, y_range)
            
            print(f"[OK] 坐标范围设置成功: ±{x_range} x ±{y_range}")
            
        except Exception as e:
            messagebox.showerror("设置坐标范围失败", f"无法设置坐标范围: {str(e)}")
            print(f"[ERROR] 坐标范围设置失败: {e}")
    
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
                print("[WARN] 用户取消导出")
                return
            
            # 执行导出
            success = self.canvas_view.export_to_png(file_path, dpi=300)
            
            if success:
                messagebox.showinfo("导出成功", f"PNG图片已成功导出到:\n{file_path}")
                print(f"[OK] PNG导出成功: {file_path}")
            else:
                messagebox.showerror("导出失败", "PNG图片导出失败，请检查文件路径和权限")
                print("[ERROR] PNG导出失败")
                
        except Exception as e:
            messagebox.showerror("导出错误", f"导出过程中发生错误: {str(e)}")
            print(f"[ERROR] PNG导出错误: {e}")
    
    # === 重置功能 ===
    
    def reset_all(self):
        """
        重置所有数据（包括背景图、锁定扇形、用户坐标系等）
        """
        try:
            # 弹出确认对话框
            result = messagebox.askyesno(
                "确认重置", 
                "这将清除所有设备数据、测量点、扇形、背景图，\n并重置坐标范围为默认值。\n\n确定要继续吗？",
                icon='warning'
            )
            
            if not result:
                print("[WARN] 用户取消重置")
                return
            
            # 清除设备数据
            self.device_manager.clear_all_devices()
            
            # 清除视图（包括背景图、锁定扇形、用户坐标系）
            self.canvas_view.clear_all()
            
            # 重置坐标范围
            self.canvas_view.set_coordinate_range(10.0, 10.0)
            
            # 重置输入面板（包括背景图UI状态）
            self.input_panel.reset_inputs()
            
            print("[OK] 重置完成")
            messagebox.showinfo("重置完成", "所有数据已成功重置")
            
        except Exception as e:
            messagebox.showerror("重置失败", f"重置过程中发生错误: {str(e)}")
            print(f"[ERROR] 重置失败: {e}")
    
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
    
    # ==================== 项目文件管理功能 ====================
    
    def new_project(self):
        """新建项目"""
        try:
            # 检查当前项目是否需要保存
            if self.project_manager.is_modified:
                result = messagebox.askyesnocancel(
                    "保存项目",
                    "当前项目未保存，是否保存？",
                    icon='question'
                )
                if result is None:  # 取消
                    return
                elif result:  # 保存
                    if not self.save_project():
                        return
            
            # 清除所有数据
            self.device_manager.clear_all_devices()
            self.canvas_view.clear_all()
            self.canvas_view.set_coordinate_range(10.0, 10.0)
            self.input_panel.reset_inputs()
            
            # 重置项目状态
            self.project_manager.current_project_path = None
            self.project_manager.current_project_name = "未命名项目"
            self.project_manager.is_modified = False
            
            # 更新窗口标题
            self._update_window_title()
            
            print("[OK] 新建项目完成")
            
        except Exception as e:
            messagebox.showerror("新建项目失败", f"新建项目时发生错误: {str(e)}")
            print(f"[ERROR] 新建项目失败: {e}")
    
    def open_project(self):
        """打开项目"""
        try:
            # 检查当前项目是否需要保存
            if self.project_manager.is_modified:
                result = messagebox.askyesnocancel(
                    "保存项目",
                    "当前项目未保存，是否保存？",
                    icon='question'
                )
                if result is None:  # 取消
                    return
                elif result:  # 保存
                    if not self.save_project():
                        return
            
            # 获取默认目录
            default_dir = self.project_manager.get_default_project_dir()
            
            # 选择项目文件
            file_path = filedialog.askopenfilename(
                title="打开项目",
                initialdir=str(default_dir),
                filetypes=[
                    ("项目文件", "*.apc"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                print("[WARN] 用户取消打开")
                return
            
            # 加载项目
            self._load_project_file(file_path)
            
        except Exception as e:
            messagebox.showerror("打开项目失败", f"打开项目时发生错误: {str(e)}")
            print(f"[ERROR] 打开项目失败: {e}")
    
    def save_project(self) -> bool:
        """
        保存项目
        
        Returns:
            是否保存成功
        """
        try:
            # 如果没有项目路径，执行另存为
            if self.project_manager.current_project_path is None:
                return self.save_project_as()
            
            # 保存到当前路径
            return self._save_to_file(str(self.project_manager.current_project_path))
            
        except Exception as e:
            messagebox.showerror("保存项目失败", f"保存项目时发生错误: {str(e)}")
            print(f"[ERROR] 保存项目失败: {e}")
            return False
    
    def save_project_as(self) -> bool:
        """
        项目另存为
        
        Returns:
            是否保存成功
        """
        try:
            # 获取默认目录和文件名
            default_dir = self.project_manager.get_default_project_dir()
            default_name = f"{self.project_manager.current_project_name}.apc"
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="另存为",
                initialdir=str(default_dir),
                initialfile=default_name,
                defaultextension=".apc",
                filetypes=[
                    ("项目文件", "*.apc"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                print("[WARN] 用户取消保存")
                return False
            
            # 保存到指定路径
            return self._save_to_file(file_path)
            
        except Exception as e:
            messagebox.showerror("另存为失败", f"另存为时发生错误: {str(e)}")
            print(f"[ERROR] 另存为失败: {e}")
            return False
    
    def import_devices_csv(self):
        """从CSV导入设备列表"""
        try:
            # 选择CSV文件
            file_path = filedialog.askopenfilename(
                title="导入设备列表",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                print("[WARN] 用户取消导入")
                return
            
            # 导入设备
            success, message, devices = self.project_manager.import_devices_from_csv(file_path)
            
            if not success:
                messagebox.showerror("导入失败", message)
                return
            
            # 询问是否覆盖现有设备
            if self.device_manager.get_device_count() > 0:
                result = messagebox.askyesno(
                    "导入设备",
                    f"将导入 {len(devices)} 个设备。\n是否清空现有设备？\n\n点击'是'清空现有设备，'否'追加到现有设备。",
                    icon='question'
                )
                if result:
                    self.device_manager.clear_all_devices()
            
            # 添加设备
            added_count = 0
            skipped_count = 0
            for device in devices:
                success, msg = self.device_manager.add_device(device)
                if success:
                    added_count += 1
                else:
                    skipped_count += 1
                    print(f"[WARN] 跳过设备 {device.name}: {msg}")
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            self.input_panel.update_devices(self.device_manager.get_devices())
            
            # 标记项目已修改
            self.project_manager.mark_modified()
            self._update_window_title()
            
            # 显示结果
            result_message = f"成功导入 {added_count} 个设备"
            if skipped_count > 0:
                result_message += f"\n跳过 {skipped_count} 个设备（名称重复或超出数量限制）"
            
            messagebox.showinfo("导入完成", result_message)
            print(f"[OK] {result_message}")
            
        except Exception as e:
            messagebox.showerror("导入错误", f"导入过程中发生错误: {str(e)}")
            print(f"[ERROR] CSV导入错误: {e}")
    
    def export_devices_csv(self):
        """导出设备列表到CSV"""
        try:
            devices = self.device_manager.get_devices()
            
            if not devices:
                messagebox.showwarning("无法导出", "当前没有设备可导出")
                return
            
            # 生成默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"设备列表_{timestamp}.csv"
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="导出设备列表",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("所有文件", "*.*")
                ],
                initialfile=default_filename
            )
            
            if not file_path:
                print("[WARN] 用户取消导出")
                return
            
            # 执行导出
            success, message = self.project_manager.export_devices_to_csv(file_path, devices)
            
            if success:
                messagebox.showinfo("导出成功", message)
            else:
                messagebox.showerror("导出失败", message)
                
        except Exception as e:
            messagebox.showerror("导出错误", f"导出过程中发生错误: {str(e)}")
            print(f"[ERROR] CSV导出错误: {e}")
    
    def _save_to_file(self, file_path: str) -> bool:
        """
        保存项目到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            # 收集数据
            devices = self.device_manager.get_devices()
            x_range, y_range = self.canvas_view.current_range
            coordinate_settings = {'x_range': x_range, 'y_range': y_range}
            
            # 用户坐标系设置
            user_coord_settings = {
                'enabled': self.canvas_view.user_coord_enabled,
                'user_x': self.canvas_view.user_position[0] if self.canvas_view.user_position else None,
                'user_y': self.canvas_view.user_position[1] if self.canvas_view.user_position else None
            }
            
            # V2.4: 获取锁定测量数据
            locked_measurement = self.canvas_view.get_locked_measurement()
            
            # V2.5: 获取背景图数据
            background_image = self.canvas_view.get_background_image()
            
            # 保存项目
            success, message = self.project_manager.save_project(
                file_path,
                devices,
                coordinate_settings,
                user_coord_settings,
                locked_measurement=locked_measurement,
                background_image=background_image
            )
            
            if success:
                # 添加到最近文件
                self.config_manager.add_recent_file(file_path)
                self._update_recent_files_menu()
                
                # 更新窗口标题
                self._update_window_title()
                
                messagebox.showinfo("保存成功", message)
                return True
            else:
                messagebox.showerror("保存失败", message)
                return False
                
        except Exception as e:
            messagebox.showerror("保存错误", f"保存过程中发生错误: {str(e)}")
            print(f"[ERROR] 保存错误: {e}")
            return False
    
    def _load_project_file(self, file_path: str):
        """
        从文件加载项目
        
        Args:
            file_path: 项目文件路径
        """
        try:
            # 加载项目
            success, message, project_data = self.project_manager.load_project(file_path)
            
            if not success:
                messagebox.showerror("加载失败", message)
                return
            
            # 清空当前数据
            self.device_manager.clear_all_devices()
            
            # 恢复坐标范围
            coord_settings = project_data.get('coordinate_settings', {})
            x_range = coord_settings.get('x_range', 10.0)
            y_range = coord_settings.get('y_range', 10.0)
            self.canvas_view.set_coordinate_range(x_range, y_range)
            
            # 恢复设备列表
            devices = project_data.get('devices_parsed', [])
            for device in devices:
                self.device_manager.add_device(device)
            
            # 恢复用户坐标系
            user_coord = project_data.get('user_coordinate_system', {})
            if user_coord.get('enabled'):
                # 启用用户坐标系
                user_x = user_coord.get('user_x')
                user_y = user_coord.get('user_y')
                if user_x is not None and user_y is not None:
                    self.canvas_view.set_user_coordinate_mode(True)
                    self.canvas_view.set_user_position(user_x, user_y)
                    self.input_panel.set_user_coord_enabled(True)
                    self.input_panel.set_user_position(user_x, user_y)
            else:
                # 禁用用户坐标系，清理旧状态
                # 先直接设置状态，确保即使视图层出错也能清除
                self.canvas_view.user_coord_enabled = False
                self.canvas_view.user_position = None
                # 然后尝试更新视图
                try:
                    self.canvas_view.set_user_coordinate_mode(False)
                    self.canvas_view.clear_user_position()
                except Exception as e:
                    print(f"[WARN] 清除用户坐标系视图时出错（已忽略）: {e}")
                # 更新输入面板
                self.input_panel.set_user_coord_enabled(False)
                self.input_panel.update_user_position_status(None)
                self.input_panel.update_coordinate_mode_status(False)
            
            # 更新视图
            self.canvas_view.update_devices(self.device_manager.get_devices())
            self.input_panel.update_devices(self.device_manager.get_devices())
            self.input_panel.set_coordinate_range(x_range, y_range)
            
            # V2.4: 恢复锁定测量数据（说话人方向和影响范围）
            if 'locked_measurement_parsed' in project_data:
                locked_measurement = project_data['locked_measurement_parsed']
                self.canvas_view.set_locked_measurement(locked_measurement)
                print(f"[INFO] 恢复锁定测量数据: {locked_measurement}")
            
            # V2.5: 恢复背景图数据
            if 'background_image_parsed' in project_data:
                background_image = project_data['background_image_parsed']
                self.set_background_image(background_image)
                print(f"[INFO] 恢复背景图数据")
            else:
                # 清除可能存在的旧背景图
                self.canvas_view.remove_background()
                self.input_panel._reset_background_ui()
            
            # 添加到最近文件
            self.config_manager.add_recent_file(file_path)
            self._update_recent_files_menu()
            
            # 更新窗口标题
            self._update_window_title()
            
            messagebox.showinfo("加载成功", f"项目加载成功：{Path(file_path).name}")
            print(f"[OK] 项目加载成功: {file_path}")
            
        except Exception as e:
            messagebox.showerror("加载错误", f"加载项目时发生错误: {str(e)}")
            print(f"[ERROR] 加载错误: {e}")
    
    def _update_recent_files_menu(self):
        """更新最近文件菜单"""
        try:
            # 清空菜单
            self.recent_menu.delete(0, 'end')
            
            # 获取最近文件列表
            recent_files = self.config_manager.get_recent_files()
            
            if not recent_files:
                self.recent_menu.add_command(label="(无最近文件)", state='disabled')
                return
            
            # 添加最近文件
            for i, file_path in enumerate(recent_files[:10]):
                file_name = Path(file_path).name
                self.recent_menu.add_command(
                    label=f"{i+1}. {file_name}",
                    command=lambda f=file_path: self._open_recent_file(f)
                )
            
            # 添加分隔线和清除历史
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="清除历史", command=self._clear_recent_files)
            
        except Exception as e:
            print(f"[WARN] 更新最近文件菜单失败: {e}")
    
    def _open_recent_file(self, file_path: str):
        """打开最近文件"""
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                messagebox.showerror("文件不存在", f"文件不存在：\n{file_path}")
                # 从最近文件列表中移除
                self.config_manager.remove_recent_file(file_path)
                self._update_recent_files_menu()
                return
            
            # 检查当前项目是否需要保存
            if self.project_manager.is_modified:
                result = messagebox.askyesnocancel(
                    "保存项目",
                    "当前项目未保存，是否保存？",
                    icon='question'
                )
                if result is None:  # 取消
                    return
                elif result:  # 保存
                    if not self.save_project():
                        return
            
            # 加载项目
            self._load_project_file(file_path)
            
        except Exception as e:
            messagebox.showerror("打开失败", f"打开最近文件时发生错误: {str(e)}")
            print(f"[ERROR] 打开最近文件失败: {e}")
    
    def _clear_recent_files(self):
        """清除最近文件历史"""
        self.config_manager.clear_recent_files()
        self._update_recent_files_menu()
        print("[OK] 最近文件历史已清除")
    
    def _update_window_title(self):
        """更新窗口标题"""
        project_title = self.project_manager.get_project_title()
        self.root.title(f"家居设备坐标距离角度绘制工具 - [{project_title}] - Matplotlib版")
    
    # ==================== 自动保存功能 ====================
    
    def _start_autosave(self):
        """启动自动保存定时器"""
        if not self.config_manager.is_autosave_enabled():
            print("[WARN] 自动保存已禁用")
            return
        
        interval = self.config_manager.get_autosave_interval()
        self.autosave_timer_id = self.root.after(interval * 1000, self._autosave)
        print(f"[OK] 自动保存定时器已启动，间隔: {interval}秒")
    
    def _autosave(self):
        """执行自动保存"""
        try:
            # 若上一次自动保存仍在进行，直接跳过本次，避免线程堆积
            with self._autosave_lock:
                if self._autosave_in_progress:
                    return
                self._autosave_in_progress = True

            # === 轻量级快照（主线程）===
            devices_snapshot = [Device.from_dict(d.to_dict()) for d in self.device_manager.get_devices()]
            x_range, y_range = self.canvas_view.current_range

            # V2.5: 获取锁定测量数据和背景图（做轻量复制，避免跨线程被修改）
            locked_measurement = self.canvas_view.get_locked_measurement()
            locked_snapshot = LockedMeasurement.from_dict(locked_measurement.to_dict()) if locked_measurement else None

            background_image = self.canvas_view.get_background_image()
            background_snapshot = None
            if background_image is not None and background_image.is_loaded():
                background_snapshot = BackgroundImage()
                background_snapshot.image_path = background_image.image_path
                background_snapshot.image_data = background_image.image_data
                background_snapshot.pixel_width = background_image.pixel_width
                background_snapshot.pixel_height = background_image.pixel_height
                background_snapshot.dpi = background_image.dpi
                background_snapshot.pixels_per_unit = background_image.pixels_per_unit
                background_snapshot.x_min = background_image.x_min
                background_snapshot.x_max = background_image.x_max
                background_snapshot.y_min = background_image.y_min
                background_snapshot.y_max = background_image.y_max
                background_snapshot.alpha = background_image.alpha
                background_snapshot.enabled = background_image.enabled

            # 检查是否有需要保存的数据（设备、背景图、用户坐标系或锁定扇形）
            has_devices = len(devices_snapshot) > 0
            has_background = background_snapshot is not None and background_snapshot.is_loaded()
            has_user_coord = self.canvas_view.user_coord_enabled and self.canvas_view.user_position is not None
            has_locked_measurement = locked_snapshot is not None and locked_snapshot.has_data()

            if not (has_devices or has_background or has_user_coord or has_locked_measurement):
                with self._autosave_lock:
                    self._autosave_in_progress = False
                return

            autosave_path = self.config_manager.get_autosave_file_path()
            coordinate_settings = {'x_range': x_range, 'y_range': y_range}
            user_coord_settings = {
                'enabled': self.canvas_view.user_coord_enabled,
                'user_x': self.canvas_view.user_position[0] if self.canvas_view.user_position else None,
                'user_y': self.canvas_view.user_position[1] if self.canvas_view.user_position else None
            }

            def _run_autosave():
                try:
                    success, _message = self.project_manager.save_draft(
                        str(autosave_path),
                        devices_snapshot,
                        coordinate_settings,
                        user_coord_settings,
                        {'name': '自动保存草稿', 'description': '自动保存的草稿文件'},
                        None,  # label_positions
                        locked_snapshot,
                        background_snapshot
                    )

                    if success:
                        print(f"💾 自动保存成功: {autosave_path.name}")
                        self.config_manager.clean_old_autosave_files(keep_count=5)
                except Exception as e:
                    print(f"[WARN] 自动保存失败: {e}")
                finally:
                    with self._autosave_lock:
                        self._autosave_in_progress = False

            threading.Thread(target=_run_autosave, daemon=True).start()

        except Exception as e:
            print(f"[WARN] 自动保存失败: {e}")
            with self._autosave_lock:
                self._autosave_in_progress = False

        finally:
            # 继续下一次定时
            self._start_autosave()
    
    def _check_autosave_recovery(self):
        """检查是否有自动保存文件需要恢复"""
        try:
            latest_autosave = self.config_manager.get_latest_autosave_file()
            
            if latest_autosave and latest_autosave.exists():
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(latest_autosave.stat().st_mtime)
                time_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
                
                result = messagebox.askyesno(
                    "恢复草稿",
                    f"发现自动保存的草稿文件：\n时间: {time_str}\n\n是否恢复？",
                    icon='question'
                )
                
                if result:
                    self._load_project_file(str(latest_autosave))
                    print(f"[OK] 从草稿恢复成功")
                    
        except Exception as e:
            print(f"[WARN] 检查自动保存恢复失败: {e}")
    
    def _on_window_closing(self):
        """窗口关闭事件处理"""
        try:
            # 检查是否需要保存
            if self.project_manager.is_modified:
                result = messagebox.askyesnocancel(
                    "保存项目",
                    "项目未保存，是否保存？",
                    icon='question'
                )
                if result is None:  # 取消关闭
                    return
                elif result:  # 保存
                    if not self.save_project():
                        return
            
            # 停止自动保存定时器
            if self.autosave_timer_id:
                self.root.after_cancel(self.autosave_timer_id)
            
            # 关闭窗口
            self.root.destroy()
            print("👋 应用程序已退出")
            
        except Exception as e:
            print(f"[ERROR] 关闭窗口时发生错误: {e}")
            self.root.destroy() 
