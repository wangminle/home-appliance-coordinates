# -*- coding: utf-8 -*-
"""
右侧功能面板视图

实现480px宽度的操作面板，包含坐标范围输入、设备管理和操作按钮
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable, Dict, Any
from models.device_model import Device


class InputPanel:
    """
    右侧功能面板类
    
    实现坐标范围设置、设备管理、导出重置等功能
    """
    
    # 面板尺寸
    PANEL_WIDTH = 480
    
    # 界面配色
    COLORS = {
        'bg': '#ffffff',
        'section_bg': '#f5f5f5',
        'border': '#e0e0e0',
        'text': '#333333',
        'label': '#666666',
        'button_primary': '#2196F3',
        'button_success': '#4CAF50',
        'button_danger': '#f44336',
        'button_warning': '#FF9800'
    }
    
    def __init__(self, parent_frame: tk.Frame, controller=None):
        """
        初始化功能面板
        
        Args:
            parent_frame: 父容器框架
            controller: 控制器对象，可选
        """
        self.parent_frame = parent_frame
        self.controller = controller
        
        # 组件引用
        self.x_range_var = tk.StringVar(value="5")
        self.y_range_var = tk.StringVar(value="5")
        
        # 设备管理相关
        self.devices: List[Device] = []  # 仅用于缓存显示，实际数据由DeviceManager管理
        self.device_treeview = None
        self.device_name_var = tk.StringVar()
        self.device_x_var = tk.StringVar()
        self.device_y_var = tk.StringVar()
        self.selected_device_id = None
        
        # 按钮组件引用
        self.add_update_button = None
        self.delete_button = None
        self.name_entry = None
        self.x_entry = None
        self.y_entry = None
        
        # 回调函数
        self.on_range_change_callback: Optional[Callable[[float, float], None]] = None
        self.on_device_add_callback: Optional[Callable[[Device], None]] = None
        self.on_device_update_callback: Optional[Callable[[Device, Device], None]] = None
        self.on_device_delete_callback: Optional[Callable[[Device], None]] = None
        self.on_export_callback: Optional[Callable[[], None]] = None
        self.on_reset_callback: Optional[Callable[[], None]] = None
        
        self._create_widgets()
        self._bind_events()
        # 不再自动加载初始设备，由控制器统一管理
    
    def _create_widgets(self):
        """
        创建界面组件
        """
        # 移除调试标签
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # 创建主滚动框架
        main_canvas = tk.Canvas(
            self.parent_frame,
            bg=self.COLORS['bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.parent_frame,
            orient="vertical",
            command=main_canvas.yview
        )
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 在滚动框架中创建内容
        self._create_range_section(scrollable_frame)
        self._create_device_section(scrollable_frame)
        self._create_action_section(scrollable_frame)
    
    def _create_range_section(self, parent):
        """
        创建坐标范围设置区域
        
        Args:
            parent: 父容器
        """
        # 区域标题
        range_frame = ttk.LabelFrame(
            parent,
            text="坐标显示范围设置",
            padding=(10, 10)
        )
        range_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # X轴范围设置
        x_frame = ttk.Frame(range_frame)
        x_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(
            x_frame,
            text="X轴范围:",
            font=('Arial', 12)
        ).pack(side='left')
        
        x_entry = ttk.Entry(
            x_frame,
            textvariable=self.x_range_var,
            width=8,
            font=('Arial', 12)
        )
        x_entry.pack(side='right')
        
        ttk.Label(
            x_frame,
            text="±",
            font=('Arial', 12)
        ).pack(side='right', padx=(5, 2))
        
        # Y轴范围设置
        y_frame = ttk.Frame(range_frame)
        y_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(
            y_frame,
            text="Y轴范围:",
            font=('Arial', 12)
        ).pack(side='left')
        
        y_entry = ttk.Entry(
            y_frame,
            textvariable=self.y_range_var,
            width=8,
            font=('Arial', 12)
        )
        y_entry.pack(side='right')
        
        ttk.Label(
            y_frame,
            text="±",
            font=('Arial', 12)
        ).pack(side='right', padx=(5, 2))
        
        # 应用按钮
        apply_btn = ttk.Button(
            range_frame,
            text="应用范围",
            command=self._on_range_apply,
            style='Custom.TButton'
        )
        apply_btn.pack(pady=(5, 0))
        
        # 添加提示信息
        tip_label = ttk.Label(
            range_frame,
            text="范围: 0.1 - 25，输入后点击应用",
            font=('Arial', 8),
            foreground='#666666'
        )
        tip_label.pack(pady=(5, 0))
    
    def _create_device_section(self, parent):
        """
        创建设备管理区域 (使用ttk.Treeview重构)
        """
        device_frame = ttk.LabelFrame(parent, text="设备管理", padding=(10, 10))
        device_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for device list
        tree_frame = ttk.Frame(device_frame)
        tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.device_treeview = ttk.Treeview(
            tree_frame,
            columns=("name", "x", "y"),
            show="headings",
            selectmode="browse"
        )
        self.device_treeview.heading("name", text="设备名称")
        self.device_treeview.heading("x", text="X坐标")
        self.device_treeview.heading("y", text="Y坐标")
        self.device_treeview.column("name", width=180)
        self.device_treeview.column("x", width=100, anchor='center')
        self.device_treeview.column("y", width=100, anchor='center')

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.device_treeview.yview)
        self.device_treeview.configure(yscrollcommand=scrollbar.set)
        
        self.device_treeview.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Input fields
        input_frame = ttk.Frame(device_frame)
        input_frame.pack(fill='x', pady=(10, 5))
        
        # Name
        ttk.Label(input_frame, text="名称:", width=8).grid(row=0, column=0, sticky='w', pady=2)
        self.name_entry = ttk.Entry(input_frame, textvariable=self.device_name_var)
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=2)
        
        # Coordinates
        ttk.Label(input_frame, text="X坐标:", width=8).grid(row=1, column=0, sticky='w', pady=2)
        self.x_entry = ttk.Entry(input_frame, textvariable=self.device_x_var)
        self.x_entry.grid(row=1, column=1, sticky='ew', pady=2)
        
        ttk.Label(input_frame, text="Y坐标:", width=8).grid(row=2, column=0, sticky='w', pady=2)
        self.y_entry = ttk.Entry(input_frame, textvariable=self.device_y_var)
        self.y_entry.grid(row=2, column=1, sticky='ew', pady=2)
        
        input_frame.columnconfigure(1, weight=1)

        # Action Buttons
        button_frame = ttk.Frame(device_frame)
        button_frame.pack(fill='x', pady=(5, 0))
        
        self.add_update_button = ttk.Button(button_frame, text="添加设备", command=self._on_add_or_update)
        self.add_update_button.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.delete_button = ttk.Button(button_frame, text="删除设备", command=self._on_device_delete, state='disabled')
        self.delete_button.pack(side='left', expand=True, fill='x', padx=(5, 0))
    
    def _create_action_section(self, parent):
        """
        创建操作按钮区域
        
        Args:
            parent: 父容器
        """
        # 区域标题
        action_frame = ttk.LabelFrame(
            parent,
            text="操作",
            padding=(10, 10)
        )
        action_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        # 导出按钮
        export_btn = ttk.Button(
            action_frame,
            text="📷 导出PNG图像",
            command=self._on_export,
            style='Custom.TButton'
        )
        export_btn.pack(fill='x', pady=(0, 5))
        
        # 重置按钮
        reset_btn = ttk.Button(
            action_frame,
            text="🔄 重置所有数据",
            command=self._on_reset
        )
        reset_btn.pack(fill='x')
        
        # 提示信息
        tip_frame = ttk.Frame(action_frame)
        tip_frame.pack(fill='x', pady=(10, 0))
        
        tip_text = "• 左键点击坐标区域创建测量点\n• 右键点击清除测量点\n• 导出PNG图像为高清1920x1920分辨率"
        
        tip_label = ttk.Label(
            tip_frame,
            text=tip_text,
            font=('Arial', 8),
            foreground='#666666',
            justify='left'
        )
        tip_label.pack(anchor='w')
    
    def _bind_events(self):
        """
        绑定事件
        """
        if self.device_treeview:
            self.device_treeview.bind('<<TreeviewSelect>>', self._on_device_select)
        
        # 回车键应用范围
        self.x_range_var.trace('w', self._on_range_entry_change)
        self.y_range_var.trace('w', self._on_range_entry_change)
    
    def _on_range_entry_change(self, *args):
        """
        范围输入框变化事件（可选的自动应用）
        """
        # 这里可以添加实时更新逻辑，但建议保持手动应用以避免频繁更新
        pass
    
    def _on_range_apply(self):
        """
        应用坐标范围
        """
        try:
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            
            # 验证范围
            if x_range < 0.1 or x_range > 50:
                raise ValueError("X轴范围必须在0.1-50之间")
            if y_range < 0.1 or y_range > 50:
                raise ValueError("Y轴范围必须在0.1-50之间")
            
            # 调用回调函数
            if self.on_range_change_callback:
                self.on_range_change_callback(x_range, y_range)
                
        except ValueError as e:
            # 显示错误消息
            self._show_error("输入错误", f"坐标范围设置失败：{str(e)}")
    
    def _on_device_select(self, event=None):
        selection = self.device_treeview.selection()
        if selection:
            self.selected_device_id = selection[0]
            device = self._get_device_by_id(self.selected_device_id)
            if device:
                self.device_name_var.set(device.name)
                self.device_x_var.set(str(device.x))
                self.device_y_var.set(str(device.y))
                self.add_update_button.config(text="更新设备")
                self.delete_button.config(state='normal')
                self._set_input_state('normal')
        else:
            self.selected_device_id = None
            self._clear_device_inputs()
            self.add_update_button.config(text="添加设备")
            self.delete_button.config(state='disabled')
            self._set_input_state('normal') # Keep inputs enabled for adding
    
    def _on_add_or_update(self):
        # This method now handles both adding and updating
        try:
            name = self.device_name_var.get().strip()
            x = float(self.device_x_var.get())
            y = float(self.device_y_var.get())
            
            if self.selected_device_id and self.on_device_update_callback:
                # Update logic
                old_device = self._get_device_by_id(self.selected_device_id)
                if old_device:
                    new_device = Device(name, x, y, device_id=old_device.id)
                    self.on_device_update_callback(old_device, new_device)
            elif self.on_device_add_callback:
                # Add logic
                new_device = Device(name, x, y)
                self.on_device_add_callback(new_device)
            
            self._clear_device_inputs()
            self.device_treeview.selection_set('') # Deselect
            
        except ValueError:
            self._show_error("输入无效", "坐标必须是有效的数字。")
        except Exception as e:
            self._show_error("操作失败", str(e))
    
    def _on_device_delete(self):
        if not self.selected_device_id or not self.on_device_delete_callback:
            return
            
        if self._ask_confirm("确认删除", "确定要删除选中的设备吗？"):
            device_to_delete = self._get_device_by_id(self.selected_device_id)
            if device_to_delete:
                self.on_device_delete_callback(device_to_delete)
    
    def _on_export(self):
        """
        导出PNG图像
        """
        if self.on_export_callback:
            self.on_export_callback()
    
    def _on_reset(self):
        """
        重置所有数据
        """
        # 确认重置
        if not self._ask_confirm(
            "确认重置", 
            "确定要重置所有数据吗？\n这将清除所有设备和测量点，坐标范围恢复为5x5。"
        ):
            return
        
        # 调用回调函数
        if self.on_reset_callback:
            self.on_reset_callback()
        
        # 重置界面状态（设备数据由控制器统一管理）
        self.x_range_var.set("5")
        self.y_range_var.set("5")
        self._clear_device_inputs()
        self.selected_device_id = None
    
    # 移除_load_initial_devices方法，设备管理由DeviceManager统一处理
    
    def _refresh_device_list(self):
        """
        刷新Treeview中的设备列表
        """
        # Clear existing items
        for item in self.device_treeview.get_children():
            self.device_treeview.delete(item)
            
        # Add new items
        for device in self.devices:
            self.device_treeview.insert(
                "", "end", iid=device.id, 
                values=(device.name, f"{device.x:.3f}", f"{device.y:.3f}")
            )
        self._on_device_select() # Update button states
    
    def _clear_device_inputs(self):
        self.device_name_var.set("")
        self.device_x_var.set("")
        self.device_y_var.set("")
        if self.device_treeview.selection():
            self.device_treeview.selection_set('')
        self.selected_device_id = None
        
    def _set_input_state(self, state):
        """Enable or disable device input fields."""
        self.name_entry.config(state=state)
        self.x_entry.config(state=state)
        self.y_entry.config(state=state)
        
    def _get_device_by_id(self, device_id: str) -> Optional[Device]:
        for device in self.devices:
            if device.id == device_id:
                return device
        return None
    
    def _show_error(self, title: str, message: str):
        """
        显示错误消息
        
        Args:
            title: 错误标题
            message: 错误消息
        """
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self.parent_frame)
    
    def _ask_confirm(self, title: str, message: str) -> bool:
        """
        显示确认对话框
        
        Args:
            title: 对话框标题
            message: 确认消息
            
        Returns:
            用户确认结果
        """
        from tkinter import messagebox
        return messagebox.askyesno(title, message, parent=self.parent_frame)
    
    # 公共接口方法
    
    def set_range_change_callback(self, callback: Callable[[float, float], None]):
        """
        设置坐标范围变化回调函数
        
        Args:
            callback: 回调函数，接收(x_range, y_range)
        """
        self.on_range_change_callback = callback
    
    def set_device_add_callback(self, callback: Callable[[Device], None]):
        """
        设置设备添加回调函数
        
        Args:
            callback: 回调函数，接收Device对象
        """
        self.on_device_add_callback = callback
    
    def set_device_update_callback(self, callback: Callable[[Device, Device], None]):
        """
        设置设备更新回调函数
        
        Args:
            callback: 回调函数，接收(旧设备, 新设备)
        """
        self.on_device_update_callback = callback
    
    def set_device_delete_callback(self, callback: Callable[[Device], None]):
        """
        设置设备删除回调函数
        
        Args:
            callback: 回调函数，接收Device对象
        """
        self.on_device_delete_callback = callback
    
    def set_export_callback(self, callback: Callable[[], None]):
        """
        设置导出回调函数
        
        Args:
            callback: 导出回调函数
        """
        self.on_export_callback = callback
    
    def set_reset_callback(self, callback: Callable[[], None]):
        """
        设置重置回调函数
        
        Args:
            callback: 重置回调函数
        """
        self.on_reset_callback = callback
    
    def update_devices(self, devices: List[Device]):
        """
        由控制器调用，更新设备列表并刷新UI
        """
        self.devices = devices
        self._refresh_device_list()
        
        # 清空选择和输入
        self._clear_device_inputs()
        self.selected_device_id = None
    
    def get_coordinate_range(self) -> tuple:
        """
        获取当前坐标范围设置
        
        Returns:
            (x_range, y_range) 元组
        """
        try:
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            return (x_range, y_range)
        except ValueError:
            return (5.0, 5.0)  # 默认值
    
    def clear_selection(self):
        """
        清除当前设备选择和输入
        """
        self._clear_device_inputs()
        if self.device_treeview.selection():
            self.device_treeview.selection_set('')
        self.selected_device_id = None
        
        # 确保按钮状态正确更新
        self.add_update_button.config(text="添加设备")
        self.delete_button.config(state='disabled')
    
    def reset_inputs(self):
        """
        重置所有输入为默认值
        """
        # 重置坐标范围
        self.x_range_var.set("5.0")
        self.y_range_var.set("5.0")
        
        # 清除设备列表
        self.devices.clear()
        self._refresh_device_list()
        
        # 清除设备输入
        self._clear_device_inputs()
        
        print("✅ 输入面板重置完成") 