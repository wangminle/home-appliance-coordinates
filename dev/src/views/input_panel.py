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
        self.x_range_var = tk.StringVar(value="10")
        self.y_range_var = tk.StringVar(value="10")
        
        # 用户坐标系相关 ✨ 双坐标系功能
        self.user_coord_enabled_var = tk.BooleanVar(value=False)
        self.user_x_var = tk.StringVar(value="0.0")
        self.user_y_var = tk.StringVar(value="0.0")
        self.user_position_frame = None  # 用户位置设置框架引用
        self.user_x_entry = None  # 用户X坐标输入框引用
        self.user_y_entry = None  # 用户Y坐标输入框引用
        
        # 设备管理相关
        self.devices: List[Device] = []  # 仅用于缓存显示，实际数据由DeviceManager管理
        self.device_treeview = None
        self.device_name_var = tk.StringVar()
        self.device_x_var = tk.StringVar()
        self.device_y_var = tk.StringVar()
        self.device_color_var = tk.StringVar(value="红色")  # ✨ 新增颜色选择
        self.selected_device_id = None
        
        # 颜色映射表 ✨ 新增
        self.COLOR_OPTIONS = {
            "红色": Device.COLOR_RED,
            "绿色": Device.COLOR_GREEN,
            "蓝色": Device.COLOR_BLUE,
            "橙色": Device.COLOR_ORANGE,
            "紫色": Device.COLOR_PURPLE,
            "青色": Device.COLOR_CYAN,
        }
        self.COLOR_NAMES = {v: k for k, v in self.COLOR_OPTIONS.items()}  # 反向映射
        
        # 按钮组件引用
        self.add_update_button = None
        self.delete_button = None
        self.name_entry = None
        self.x_entry = None
        self.y_entry = None
        self.color_combobox = None  # ✨ 新增颜色选择框引用
        
        # 回调函数
        self.on_range_change_callback: Optional[Callable[[float, float], None]] = None
        self.on_device_add_callback: Optional[Callable[[Device], None]] = None
        self.on_device_update_callback: Optional[Callable[[Device, Device], None]] = None
        self.on_device_delete_callback: Optional[Callable[[Device], None]] = None
        self.on_export_callback: Optional[Callable[[], None]] = None
        self.on_reset_callback: Optional[Callable[[], None]] = None
        # 用户坐标系回调函数 ✨ 双坐标系功能
        self.on_user_coord_toggle_callback: Optional[Callable[[bool], None]] = None
        self.on_user_position_set_callback: Optional[Callable[[float, float], None]] = None
        
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
        self.main_canvas = tk.Canvas(
            self.parent_frame,
            bg=self.COLORS['bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.parent_frame,
            orient="vertical",
            command=self.main_canvas.yview
        )
        scrollable_frame = ttk.Frame(self.main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # ✨ 修复Canvas内嵌组件焦点问题：当点击Canvas内的组件时，将焦点传递给被点击的组件
        def _on_canvas_click(event):
            """处理Canvas点击事件，将焦点传递给被点击的内部组件"""
            # 获取点击位置对应的实际组件
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
            if widget and widget != event.widget:
                # 如果点击的是内部组件（不是Canvas本身），将焦点传递给它
                widget.focus_set()
        
        self.main_canvas.bind('<Button-1>', _on_canvas_click)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 在滚动框架中创建内容
        self._create_range_section(scrollable_frame)
        self._create_device_section(scrollable_frame)
        self._create_action_section(scrollable_frame)
    
    def _create_range_section(self, parent):
        """
        创建坐标范围设置区域 - 优化布局
        
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
        
        # 坐标范围输入区域（按要求重新布局）
        
        # X轴范围设置行
        x_frame = ttk.Frame(range_frame)
        x_frame.pack(fill='x', pady=(0, 5))
        
        # X轴标签（左对齐）
        ttk.Label(
            x_frame,
            text="X轴范围:",
            font=('Arial', 12)
        ).pack(side='left')
        
        # 中间输入区域（距离标签20px）
        x_input_frame = ttk.Frame(x_frame)
        x_input_frame.pack(side='left', padx=(20, 0))
        
        ttk.Label(
            x_input_frame,
            text="±",
            font=('Arial', 12)
        ).pack(side='left')
        
        x_entry = ttk.Entry(
            x_input_frame,
            textvariable=self.x_range_var,
            width=8,
            font=('Arial', 12),
            justify='center'
        )
        x_entry.pack(side='left', padx=(5, 0))
        # ✨ 绑定点击事件确保获取焦点（修复与Matplotlib canvas焦点冲突问题）
        x_entry.bind('<Button-1>', lambda e, w=x_entry: w.focus_set())
        
        # Y轴范围设置行
        y_frame = ttk.Frame(range_frame)
        y_frame.pack(fill='x', pady=(0, 10))
        
        # Y轴标签（左对齐）
        ttk.Label(
            y_frame,
            text="Y轴范围:",
            font=('Arial', 12)
        ).pack(side='left')
        
        # 中间输入区域（距离标签20px）
        y_input_frame = ttk.Frame(y_frame)
        y_input_frame.pack(side='left', padx=(20, 0))
        
        ttk.Label(
            y_input_frame,
            text="±",
            font=('Arial', 12)
        ).pack(side='left')
        
        y_entry = ttk.Entry(
            y_input_frame,
            textvariable=self.y_range_var,
            width=8,
            font=('Arial', 12),
            justify='center'
        )
        y_entry.pack(side='left', padx=(5, 0))
        # ✨ 绑定点击事件确保获取焦点（修复与Matplotlib canvas焦点冲突问题）
        y_entry.bind('<Button-1>', lambda e, w=y_entry: w.focus_set())
        
        # 应用设置按钮（右侧，与下方"设置用户位置"按钮左边缘对齐）
        apply_btn = ttk.Button(
            y_frame,
            text="应用设置",
            command=self._on_range_apply,
            style='Custom.TButton'
        )
        # 使用padx来调整水平位置，使其与设置用户位置按钮左边缘对齐
        apply_btn.pack(side='right', padx=(0, 0))
        
        # 用户坐标系开关
        user_coord_frame = ttk.Frame(range_frame)
        user_coord_frame.pack(fill='x', pady=(5, 10))
        
        user_coord_check = ttk.Checkbutton(
            user_coord_frame,
            text="启用用户坐标系",
            variable=self.user_coord_enabled_var,
            command=self._on_user_coord_toggle,
            style='Custom.TCheckbutton'
        )
        user_coord_check.pack(side='left')
        
        # 用户位置设置区域（默认隐藏，位于开关下方）
        self.user_position_frame = ttk.LabelFrame(
            range_frame,
            text="用户位置设置",
            padding=(5, 5)
        )
        # 初始状态隐藏，等待用户开关切换
        
        # 用户坐标输入行
        user_pos_input_frame = ttk.Frame(self.user_position_frame)
        user_pos_input_frame.pack(fill='x', pady=(0, 5))
        
        # X坐标输入
        ttk.Label(
            user_pos_input_frame,
            text="X:",
            font=('Arial', 10)
        ).pack(side='left', padx=(0, 5))
        
        self.user_x_entry = ttk.Entry(
            user_pos_input_frame,
            textvariable=self.user_x_var,
            width=8,
            font=('Arial', 10),
            justify='center'
        )
        self.user_x_entry.pack(side='left', padx=(0, 15))
        # 绑定点击事件确保获取焦点
        self.user_x_entry.bind('<Button-1>', lambda e: self.user_x_entry.focus_set())
        
        # Y坐标输入
        ttk.Label(
            user_pos_input_frame,
            text="Y:",
            font=('Arial', 10)
        ).pack(side='left', padx=(0, 5))
        
        self.user_y_entry = ttk.Entry(
            user_pos_input_frame,
            textvariable=self.user_y_var,
            width=8,
            font=('Arial', 10),
            justify='center'
        )
        self.user_y_entry.pack(side='left', padx=(0, 15))
        # 绑定点击事件确保获取焦点
        self.user_y_entry.bind('<Button-1>', lambda e: self.user_y_entry.focus_set())
        
        # 设置用户位置按钮（同一行右侧）
        set_user_pos_btn = ttk.Button(
            user_pos_input_frame,
            text="设置用户位置",
            command=self._on_user_position_set,
            style='UserPosition.TButton'
        )
        set_user_pos_btn.pack(side='right')
        
        # 保存状态指示器区域的引用，稍后创建
        self.status_frame = None
        
        # 在最后创建状态指示器区域，确保它在最下方
        self._create_status_indicators(range_frame)
        
        # 添加提示信息
        tip_label = ttk.Label(
            range_frame,
            text="范围: 0.1 - 25，启用用户坐标系可进行相对位置分析",
            font=('Arial', 8),
            foreground='#666666'
        )
        tip_label.pack(pady=(5, 0))
    
    def _create_status_indicators(self, parent):
        """
        创建状态指示器区域（始终在最下方）
        
        Args:
            parent: 父容器
        """
        # 状态指示器区域
        self.status_frame = ttk.LabelFrame(
            parent,
            text="当前状态",
            padding=(5, 5)
        )
        self.status_frame.pack(fill='x', pady=(5, 0))
        
        # 坐标系模式状态
        self.coord_mode_label = ttk.Label(
            self.status_frame,
            text="坐标系模式: 世界坐标系",
            font=('Arial', 10, 'bold'),
            foreground='#2196F3'
        )
        self.coord_mode_label.pack(anchor='w')
        
        # 用户位置状态
        self.user_pos_label = ttk.Label(
            self.status_frame,
            text="用户位置: 未设置",
            font=('Arial', 10),
            foreground='#666666'
        )
        self.user_pos_label.pack(anchor='w', pady=(2, 0))
        
        # 交互模式提示
        self.interaction_hint_label = ttk.Label(
            self.status_frame,
            text="💡 左键单击测量距离，双击绘制扇形",
            font=('Arial', 9),
            foreground='#FF9800'
        )
        self.interaction_hint_label.pack(anchor='w', pady=(5, 0))
    
    def _create_device_section(self, parent):
        """
        创建设备管理区域 (使用ttk.Treeview重构) - V2.2 增加颜色选择
        """
        device_frame = ttk.LabelFrame(parent, text="设备管理", padding=(10, 10))
        device_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for device list（增加颜色列）
        tree_frame = ttk.Frame(device_frame)
        tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.device_treeview = ttk.Treeview(
            tree_frame,
            columns=("name", "x", "y", "color"),
            show="headings",
            selectmode="browse"
        )
        self.device_treeview.heading("name", text="设备名称")
        self.device_treeview.heading("x", text="X坐标")
        self.device_treeview.heading("y", text="Y坐标")
        self.device_treeview.heading("color", text="颜色")
        self.device_treeview.column("name", width=140)
        self.device_treeview.column("x", width=80, anchor='center')
        self.device_treeview.column("y", width=80, anchor='center')
        self.device_treeview.column("color", width=60, anchor='center')

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
        # ✨ 绑定点击事件确保获取焦点（修复与Matplotlib canvas焦点冲突问题）
        self.name_entry.bind('<Button-1>', lambda e: self.name_entry.focus_set())
        
        # Coordinates
        ttk.Label(input_frame, text="X坐标:", width=8).grid(row=1, column=0, sticky='w', pady=2)
        self.x_entry = ttk.Entry(input_frame, textvariable=self.device_x_var)
        self.x_entry.grid(row=1, column=1, sticky='ew', pady=2)
        # ✨ 绑定点击事件确保获取焦点
        self.x_entry.bind('<Button-1>', lambda e: self.x_entry.focus_set())
        
        ttk.Label(input_frame, text="Y坐标:", width=8).grid(row=2, column=0, sticky='w', pady=2)
        self.y_entry = ttk.Entry(input_frame, textvariable=self.device_y_var)
        self.y_entry.grid(row=2, column=1, sticky='ew', pady=2)
        # ✨ 绑定点击事件确保获取焦点
        self.y_entry.bind('<Button-1>', lambda e: self.y_entry.focus_set())
        
        # ✨ 新增颜色选择下拉框
        ttk.Label(input_frame, text="颜色:", width=8).grid(row=3, column=0, sticky='w', pady=2)
        self.color_combobox = ttk.Combobox(
            input_frame, 
            textvariable=self.device_color_var,
            values=list(self.COLOR_OPTIONS.keys()),
            state='readonly',
            width=15
        )
        self.color_combobox.grid(row=3, column=1, sticky='w', pady=2)
        self.color_combobox.set("红色")  # 默认选择红色
        
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
            text="重置所有数据",
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
                # ✨ 设置颜色选择
                color_name = self.COLOR_NAMES.get(device.color, "红色")
                self.device_color_var.set(color_name)
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
        # This method now handles both adding and updating - V2.2 支持颜色
        try:
            name = self.device_name_var.get().strip()
            x = float(self.device_x_var.get())
            y = float(self.device_y_var.get())
            
            # ✨ 获取选中的颜色
            color_name = self.device_color_var.get()
            color = self.COLOR_OPTIONS.get(color_name, Device.COLOR_RED)
            
            if self.selected_device_id and self.on_device_update_callback:
                # Update logic
                old_device = self._get_device_by_id(self.selected_device_id)
                if old_device:
                    new_device = Device(name, x, y, device_id=old_device.id, color=color)
                    self.on_device_update_callback(old_device, new_device)
            elif self.on_device_add_callback:
                # Add logic
                new_device = Device(name, x, y, color=color)
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
        刷新Treeview中的设备列表 - V2.2 显示颜色信息
        """
        # Clear existing items
        for item in self.device_treeview.get_children():
            self.device_treeview.delete(item)
            
        # Add new items
        for device in self.devices:
            # ✨ 获取颜色名称
            color_name = self.COLOR_NAMES.get(device.color, "红色")
            self.device_treeview.insert(
                "", "end", iid=device.id, 
                values=(device.name, f"{device.x:.3f}", f"{device.y:.3f}", color_name)
            )
        self._on_device_select() # Update button states
    
    def _clear_device_inputs(self):
        self.device_name_var.set("")
        self.device_x_var.set("")
        self.device_y_var.set("")
        self.device_color_var.set("红色")  # ✨ 重置颜色为默认红色
        if self.device_treeview.selection():
            self.device_treeview.selection_set('')
        self.selected_device_id = None
        
    def _set_input_state(self, state):
        """Enable or disable device input fields."""
        self.name_entry.config(state=state)
        self.x_entry.config(state=state)
        self.y_entry.config(state=state)
        # ✨ V2.2 增加颜色选择框状态控制
        if self.color_combobox:
            self.color_combobox.config(state='readonly' if state == 'normal' else 'disabled')
        
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
            return (10.0, 10.0)  # 默认值
    
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
        # 重置坐标范围（更新为10.0）
        self.x_range_var.set("10.0")
        self.y_range_var.set("10.0")
        
        # 重置用户坐标系状态 ✨ 双坐标系功能
        self.user_coord_enabled_var.set(False)
        self.user_x_var.set("0.0")
        self.user_y_var.set("0.0")
        self._toggle_user_position_visibility(False)
        
        # 清除设备列表
        self.devices.clear()
        self._refresh_device_list()
        
        # 清除设备输入
        self._clear_device_inputs()
        
        print("✅ 输入面板重置完成")

    # 用户坐标系相关方法 ✨ 双坐标系功能
    
    def _on_user_coord_toggle(self):
        """
        处理用户坐标系开关切换事件 ✨ 第五步增强：立即更新状态显示
        """
        enabled = self.user_coord_enabled_var.get()
        self._toggle_user_position_visibility(enabled)
        
        # 立即更新状态指示器 ✨ 第五步新增功能
        self.update_coordinate_mode_status(enabled)
        
        # 通知控制器坐标系模式切换
        if self.on_user_coord_toggle_callback:
            self.on_user_coord_toggle_callback(enabled)
        
        print(f"✨ 用户坐标系{'启用' if enabled else '关闭'}")
    
    def _toggle_user_position_visibility(self, show: bool):
        """
        切换用户位置设置区域的显示/隐藏
        
        Args:
            show: True显示，False隐藏
        """
        if show:
            # 将用户位置设置区域插入到状态指示器区域之前
            self.user_position_frame.pack(fill='x', pady=(5, 0), before=self.status_frame)
        else:
            self.user_position_frame.pack_forget()
    
    def _on_user_position_set(self):
        """
        处理设置用户位置按钮点击事件
        """
        try:
            # 获取用户输入的坐标
            user_x = float(self.user_x_var.get())
            user_y = float(self.user_y_var.get())
            
            # 验证坐标范围
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            
            if abs(user_x) > x_range or abs(user_y) > y_range:
                self._show_error(
                    "坐标超出范围",
                    f"用户位置坐标必须在当前显示范围内\n"
                    f"X范围: ±{x_range}, Y范围: ±{y_range}"
                )
                return
            
            # 通知控制器设置用户位置
            if self.on_user_position_set_callback:
                self.on_user_position_set_callback(user_x, user_y)
            
            # 立即更新用户位置状态显示 ✨ 第五步新增功能
            self.update_user_position_status((user_x, user_y))
            
            print(f"✨ 设置用户位置: ({user_x}, {user_y})")
            
        except ValueError:
            self._show_error(
                "输入错误",
                "请输入有效的数字坐标"
            )
    
    # 回调函数设置方法
    
    def set_user_coord_toggle_callback(self, callback: Callable[[bool], None]):
        """
        设置用户坐标系开关切换回调函数
        
        Args:
            callback: 回调函数，参数为开关状态(bool)
        """
        self.on_user_coord_toggle_callback = callback
    
    def set_user_position_set_callback(self, callback: Callable[[float, float], None]):
        """
        设置用户位置设置回调函数
        
        Args:
            callback: 回调函数，参数为用户坐标(x, y)
        """
        self.on_user_position_set_callback = callback
    
    # 状态查询方法
    
    def is_user_coord_enabled(self) -> bool:
        """
        查询用户坐标系是否已启用
        
        Returns:
            bool: True表示已启用，False表示未启用
        """
        return self.user_coord_enabled_var.get()
    
    def get_user_position(self) -> tuple:
        """
        获取当前设置的用户位置
        
        Returns:
            tuple: (x, y) 用户坐标
        """
        try:
            x = float(self.user_x_var.get())
            y = float(self.user_y_var.get())
            return (x, y)
        except ValueError:
            return (0.0, 0.0)
    
    # === 状态指示器更新方法 ✨ 第五步新增功能 ===
    
    def update_coordinate_mode_status(self, user_coord_enabled: bool):
        """
        更新坐标系模式状态显示
        
        Args:
            user_coord_enabled: 是否启用用户坐标系
        """
        if user_coord_enabled:
            self.coord_mode_label.config(
                text="坐标系模式: 用户坐标系",
                foreground='#7b1fa2'  # 紫色
            )
            self.interaction_hint_label.config(
                text="[提示] 测量以用户位置为原点，双击扇形以用户为中心",
                foreground='#7b1fa2'
            )
        else:
            self.coord_mode_label.config(
                text="坐标系模式: 世界坐标系",
                foreground='#2196F3'  # 蓝色
            )
            self.interaction_hint_label.config(
                text="[提示] 左键单击测量距离，双击绘制扇形",
                foreground='#FF9800'
            )
    
    def update_user_position_status(self, user_position: Optional[tuple]):
        """
        更新用户位置状态显示
        
        Args:
            user_position: 用户位置坐标 (x, y) 或 None
        """
        if user_position:
            x, y = user_position
            self.user_pos_label.config(
                text=f"用户位置: ({x:.1f}, {y:.1f})",
                foreground='#4CAF50'  # 绿色表示已设置
            )
        else:
            self.user_pos_label.config(
                text="用户位置: 未设置",
                foreground='#666666'  # 灰色表示未设置
            )
    
    def update_range_status(self, x_range: float, y_range: float):
        """
        更新坐标范围状态（可选）
        
        Args:
            x_range: X轴范围
            y_range: Y轴范围
        """
        # 更新输入框显示的值，确保UI与实际状态同步
        self.x_range_var.set(f"{x_range:.1f}")
        self.y_range_var.set(f"{y_range:.1f}")
    
    # === 项目加载辅助方法（用于从文件恢复状态）===
    
    def set_coordinate_range(self, x_range: float, y_range: float):
        """
        设置坐标范围（用于项目加载）
        
        Args:
            x_range: X轴范围
            y_range: Y轴范围
        """
        self.x_range_var.set(f"{x_range:.1f}")
        self.y_range_var.set(f"{y_range:.1f}")
    
    def set_user_coord_enabled(self, enabled: bool):
        """
        设置用户坐标系启用状态（用于项目加载）
        
        Args:
            enabled: 是否启用
        """
        self.user_coord_enabled_var.set(enabled)
        # 触发切换事件以更新UI
        self._on_user_coord_toggle()
    
    def set_user_position(self, x: float, y: float):
        """
        设置用户位置（用于项目加载）
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
        """
        self.user_x_var.set(f"{x:.3f}")
        self.user_y_var.set(f"{y:.3f}")
        # 更新状态显示
        self.update_user_position_status((x, y)) 