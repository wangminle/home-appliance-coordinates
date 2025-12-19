# -*- coding: utf-8 -*-
"""
右侧功能面板视图 - V2.6 标签式布局版本

实现480px宽度的操作面板，采用标签式(Tab)布局，包含四个功能标签页：
- 坐标设置：坐标范围输入、用户坐标系设置
- 背景设置：背景户型图导入和调整
- 设备管理：设备列表和CRUD操作
- 系统操作：导出PNG和重置功能
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable, Dict, Any
from models.device_model import Device


class InputPanel:
    """
    右侧功能面板类 - 标签式布局版本
    
    实现坐标范围设置、背景图设置、设备管理、导出重置等功能
    采用 ttk.Notebook 实现四个功能标签页
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
        
        # Notebook组件引用
        self.notebook = None
        self.tab_coordinate = None
        self.tab_background = None
        self.tab_device = None
        self.tab_action = None
        
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
        
        # 状态指示器引用
        self.status_frame = None
        self.coord_mode_label = None
        self.user_pos_label = None
        self.interaction_hint_label = None
        
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
        # 背景图回调函数 ✨ V2.5 背景户型图功能
        self.on_background_import_callback: Optional[Callable[[str], None]] = None
        self.on_background_remove_callback: Optional[Callable[[], None]] = None
        self.on_background_scale_change_callback: Optional[Callable[[float], None]] = None
        self.on_background_alpha_change_callback: Optional[Callable[[float], None]] = None
        self.on_background_visibility_toggle_callback: Optional[Callable[[bool], None]] = None
        
        # 背景图 UI 组件引用
        self.bg_info_label = None
        self.bg_scale_result_label = None
        self.bg_ppu_var = None
        self.bg_ppu_entry = None
        self.bg_alpha_var = None
        self.bg_alpha_scale = None
        self.bg_alpha_label = None
        self.bg_visible_var = None
        self.bg_remove_btn = None
        
        self._setup_styles()
        self._create_widgets()
        self._bind_events()
    
    def _setup_styles(self):
        """
        设置 ttk 样式，包括 Notebook 标签样式
        """
        style = ttk.Style()
        
        # 配置 Notebook 标签样式
        style.configure(
            'Custom.TNotebook',
            background=self.COLORS['bg'],
            borderwidth=0
        )
        
        style.configure(
            'Custom.TNotebook.Tab',
            padding=[12, 8],
            font=('Arial', 10, 'bold')
        )
        
        # 标签选中和悬停效果
        style.map(
            'Custom.TNotebook.Tab',
            background=[('selected', '#e3f2fd'), ('!selected', '#f5f5f5')],
            foreground=[('selected', '#1976D2'), ('!selected', '#666666')],
            expand=[('selected', [1, 1, 1, 0])]
        )
        
        # 用户位置设置按钮样式
        style.configure(
            'UserPosition.TButton',
            padding=(8, 4)
        )
    
    def _create_widgets(self):
        """
        创建界面组件 - 标签式布局版本 V2.6
        """
        # 清理现有子组件
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # 创建 Notebook 标签容器
        self.notebook = ttk.Notebook(
            self.parent_frame,
            style='Custom.TNotebook'
        )
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建四个标签页 Frame
        self.tab_coordinate = ttk.Frame(self.notebook, padding=10)
        self.tab_background = ttk.Frame(self.notebook, padding=10)
        self.tab_device = ttk.Frame(self.notebook, padding=10)
        self.tab_action = ttk.Frame(self.notebook, padding=10)
        
        # 添加标签页到 Notebook
        self.notebook.add(self.tab_coordinate, text='📍 坐标设置')
        self.notebook.add(self.tab_background, text='🖼️ 背景设置')
        self.notebook.add(self.tab_device, text='📋 设备管理')
        self.notebook.add(self.tab_action, text='⚙️ 系统操作')
        
        # 在各标签页中创建内容
        self._create_coordinate_tab_content(self.tab_coordinate)
        self._create_background_tab_content(self.tab_background)
        self._create_device_tab_content(self.tab_device)
        self._create_action_tab_content(self.tab_action)
        
        # 绑定标签页切换事件，确保切换后立即刷新界面 ✨ Bug修复
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # 默认选中第一个标签页（坐标设置）
        self.notebook.select(0)
    
    # ========== 标签页1: 坐标设置 ==========
    
    def _create_coordinate_tab_content(self, parent):
        """
        创建坐标设置标签页内容

        Args:
            parent: 标签页容器
        """
        # 直接在父容器中创建内容框架（与其他标签页保持一致）
        # 移除 tk.Canvas 包装器，避免白色背景问题
        scrollable_frame = ttk.Frame(parent)
        scrollable_frame.pack(fill='both', expand=True)
        
        # === 坐标范围设置区域 ===
        range_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📐 坐标显示范围",
            padding=(10, 10)
        )
        range_frame.pack(fill='x', pady=(0, 10))
        
        # 坐标范围设置行（单行布局）
        input_row_frame = ttk.Frame(range_frame)
        input_row_frame.pack(fill='x', pady=5)
        
        # X轴部分
        ttk.Label(
            input_row_frame,
            text="X轴范围:",
            font=('Arial', 11)
        ).pack(side='left', padx=(0, 5))
        
        x_input_frame = ttk.Frame(input_row_frame)
        x_input_frame.pack(side='left')
        
        ttk.Label(x_input_frame, text="±", font=('Arial', 11)).pack(side='left')
        
        x_entry = ttk.Entry(
            x_input_frame,
            textvariable=self.x_range_var,
            width=6,
            font=('Arial', 11),
            justify='center'
        )
        x_entry.pack(side='left', padx=(2, 0))
        x_entry.bind('<Button-1>', lambda e, w=x_entry: (w.focus_set(), 'break')[1])
        
        # Y轴部分
        ttk.Label(
            input_row_frame,
            text="Y轴范围:",
            font=('Arial', 11)
        ).pack(side='left', padx=(15, 5))
        
        y_input_frame = ttk.Frame(input_row_frame)
        y_input_frame.pack(side='left')
        
        ttk.Label(y_input_frame, text="±", font=('Arial', 11)).pack(side='left')
        
        y_entry = ttk.Entry(
            y_input_frame,
            textvariable=self.y_range_var,
            width=6,
            font=('Arial', 11),
            justify='center'
        )
        y_entry.pack(side='left', padx=(2, 0))
        y_entry.bind('<Button-1>', lambda e, w=y_entry: (w.focus_set(), 'break')[1])
        
        # 范围设置按钮
        apply_btn = ttk.Button(
            input_row_frame,
            text="范围设置",
            command=self._on_range_apply,
            style='Custom.TButton',
            width=8
        )
        apply_btn.pack(side='right', padx=(5, 0))
        
        # 提示信息
        tip_label = ttk.Label(
            range_frame,
            text="范围: 0.1 - 25，启用用户坐标系可进行相对位置分析",
            font=('Arial', 8),
            foreground='#666666'
        )
        tip_label.pack(anchor='w', pady=(5, 0))
        
        # === 用户坐标系设置区域 ===
        user_coord_frame = ttk.LabelFrame(
            scrollable_frame,
            text="🎯 用户坐标系",
            padding=(10, 10)
        )
        user_coord_frame.pack(fill='x', pady=(0, 10))
        
        # 用户坐标系开关
        user_coord_check = ttk.Checkbutton(
            user_coord_frame,
            text="启用用户坐标系",
            variable=self.user_coord_enabled_var,
            command=self._on_user_coord_toggle,
            style='Custom.TCheckbutton'
        )
        user_coord_check.pack(anchor='w')
        
        # 用户位置设置区域（默认隐藏）
        self.user_position_frame = ttk.Frame(user_coord_frame)
        
        user_pos_input_frame = ttk.Frame(self.user_position_frame)
        user_pos_input_frame.pack(fill='x', pady=(10, 5))
        
        ttk.Label(user_pos_input_frame, text="X:", font=('Arial', 10)).pack(side='left', padx=(0, 5))
        
        self.user_x_entry = ttk.Entry(
            user_pos_input_frame,
            textvariable=self.user_x_var,
            width=8,
            font=('Arial', 10),
            justify='center'
        )
        self.user_x_entry.pack(side='left', padx=(0, 15))
        self.user_x_entry.bind('<Button-1>', lambda e: (self.user_x_entry.focus_set(), 'break')[1])
        
        ttk.Label(user_pos_input_frame, text="Y:", font=('Arial', 10)).pack(side='left', padx=(0, 5))
        
        self.user_y_entry = ttk.Entry(
            user_pos_input_frame,
            textvariable=self.user_y_var,
            width=8,
            font=('Arial', 10),
            justify='center'
        )
        self.user_y_entry.pack(side='left', padx=(0, 15))
        self.user_y_entry.bind('<Button-1>', lambda e: (self.user_y_entry.focus_set(), 'break')[1])
        
        set_user_pos_btn = ttk.Button(
            user_pos_input_frame,
            text="设置用户位置",
            command=self._on_user_position_set,
            style='UserPosition.TButton'
        )
        set_user_pos_btn.pack(side='right')
        
        # === 当前状态指示区域 ===
        self.status_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📊 当前状态",
            padding=(10, 10)
        )
        self.status_frame.pack(fill='x', pady=(0, 10))
        
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
    
    # ========== 标签页2: 背景设置 ==========
    
    def _create_background_tab_content(self, parent):
        """
        创建背景设置标签页内容
        
        Args:
            parent: 标签页容器
        """
        # === 图片导入区域 ===
        import_frame = ttk.LabelFrame(
            parent,
            text="📁 图片导入",
            padding=(10, 10)
        )
        import_frame.pack(fill='x', pady=(0, 10))
        
        btn_frame = ttk.Frame(import_frame)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        import_btn = ttk.Button(
            btn_frame,
            text="📁 导入户型图",
            command=self._on_import_background,
            width=14
        )
        import_btn.pack(side='left', padx=(0, 10))
        
        self.bg_remove_btn = ttk.Button(
            btn_frame,
            text="🗑 移除背景",
            command=self._on_remove_background,
            state='disabled',
            width=12
        )
        self.bg_remove_btn.pack(side='left')
        
        # === 图片信息区域 ===
        info_frame = ttk.LabelFrame(parent, text="📐 图片信息", padding=(10, 10))
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.bg_info_label = ttk.Label(
            info_frame,
            text="未加载图片",
            foreground='gray',
            font=('Arial', 10)
        )
        self.bg_info_label.pack(anchor='w')
        
        # === 比例设置区域 ===
        scale_frame = ttk.LabelFrame(parent, text="📏 比例设置", padding=(10, 10))
        scale_frame.pack(fill='x', pady=(0, 10))
        
        scale_input_frame = ttk.Frame(scale_frame)
        scale_input_frame.pack(fill='x', pady=5)
        
        ttk.Label(scale_input_frame, text="每", font=('Arial', 10)).pack(side='left')
        
        self.bg_ppu_var = tk.StringVar(value="100")
        self.bg_ppu_entry = ttk.Entry(
            scale_input_frame,
            textvariable=self.bg_ppu_var,
            width=8,
            justify='center',
            font=('Arial', 10)
        )
        self.bg_ppu_entry.pack(side='left', padx=5)
        self.bg_ppu_entry.bind('<Return>', self._on_bg_ppu_change)
        self.bg_ppu_entry.bind('<FocusOut>', self._on_bg_ppu_change)
        self.bg_ppu_entry.bind('<Button-1>', lambda e: (self.bg_ppu_entry.focus_set(), 'break')[1])
        
        ttk.Label(
            scale_input_frame,
            text="像素 = 1 格 (1米)",
            font=('Arial', 10)
        ).pack(side='left')
        
        # 计算结果显示
        self.bg_scale_result_label = ttk.Label(
            scale_frame,
            text="",
            foreground='#2e7d32',
            font=('Arial', 9)
        )
        self.bg_scale_result_label.pack(anchor='w', pady=(5, 0))
        
        # === 显示设置区域 ===
        display_frame = ttk.LabelFrame(parent, text="🎨 显示设置", padding=(10, 10))
        display_frame.pack(fill='x', pady=(0, 10))
        
        # 透明度设置
        alpha_row = ttk.Frame(display_frame)
        alpha_row.pack(fill='x', pady=5)
        
        ttk.Label(alpha_row, text="透明度:", font=('Arial', 10)).pack(side='left')
        
        self.bg_alpha_var = tk.DoubleVar(value=0.5)
        self.bg_alpha_scale = ttk.Scale(
            alpha_row,
            from_=0.1, to=1.0,
            variable=self.bg_alpha_var,
            orient='horizontal',
            command=self._on_bg_alpha_change
        )
        self.bg_alpha_scale.pack(side='left', fill='x', expand=True, padx=10)
        
        self.bg_alpha_label = ttk.Label(alpha_row, text="50%", width=5, font=('Arial', 10))
        self.bg_alpha_label.pack(side='left')
        
        # 显示开关
        self.bg_visible_var = tk.BooleanVar(value=True)
        bg_visible_check = ttk.Checkbutton(
            display_frame,
            text="显示背景图",
            variable=self.bg_visible_var,
            command=self._on_bg_visibility_toggle
        )
        bg_visible_check.pack(anchor='w', pady=(5, 0))
        
        # 提示信息
        tip_frame = ttk.Frame(parent)
        tip_frame.pack(fill='x', pady=(10, 0))
        
        tip_label = ttk.Label(
            tip_frame,
            text="💡 支持 PNG/JPG 格式图片\n📏 比例设置: 指定多少像素对应1米",
            font=('Arial', 9),
            foreground='#666666',
            justify='left'
        )
        tip_label.pack(anchor='w')
    
    # ========== 标签页3: 设备管理 ==========
    
    def _create_device_tab_content(self, parent):
        """
        创建设备管理标签页内容
        
        Args:
            parent: 标签页容器
        """
        # === 设备列表区域 ===
        list_frame = ttk.LabelFrame(parent, text="📋 设备列表", padding=(10, 10))
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Treeview 设备列表
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill='both', expand=True)
        
        self.device_treeview = ttk.Treeview(
            tree_frame,
            columns=("name", "x", "y", "color"),
            show="headings",
            selectmode="browse",
            height=12  # 增加默认高度
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
        
        # === 设备编辑区域 ===
        edit_frame = ttk.LabelFrame(parent, text="✏️ 设备信息", padding=(10, 10))
        edit_frame.pack(fill='x', pady=(0, 10))
        
        # 输入字段
        input_frame = ttk.Frame(edit_frame)
        input_frame.pack(fill='x', pady=(0, 10))
        
        # 名称
        ttk.Label(input_frame, text="名称:", width=8).grid(row=0, column=0, sticky='w', pady=2)
        self.name_entry = ttk.Entry(input_frame, textvariable=self.device_name_var)
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=2)
        self.name_entry.bind('<Button-1>', lambda e: (self.name_entry.focus_set(), 'break')[1])
        
        # X坐标
        ttk.Label(input_frame, text="X坐标:", width=8).grid(row=1, column=0, sticky='w', pady=2)
        self.x_entry = ttk.Entry(input_frame, textvariable=self.device_x_var)
        self.x_entry.grid(row=1, column=1, sticky='ew', pady=2)
        self.x_entry.bind('<Button-1>', lambda e: (self.x_entry.focus_set(), 'break')[1])
        
        # Y坐标
        ttk.Label(input_frame, text="Y坐标:", width=8).grid(row=2, column=0, sticky='w', pady=2)
        self.y_entry = ttk.Entry(input_frame, textvariable=self.device_y_var)
        self.y_entry.grid(row=2, column=1, sticky='ew', pady=2)
        self.y_entry.bind('<Button-1>', lambda e: (self.y_entry.focus_set(), 'break')[1])
        
        # 颜色选择
        ttk.Label(input_frame, text="颜色:", width=8).grid(row=3, column=0, sticky='w', pady=2)
        self.color_combobox = ttk.Combobox(
            input_frame, 
            textvariable=self.device_color_var,
            values=list(self.COLOR_OPTIONS.keys()),
            state='readonly',
            width=15
        )
        self.color_combobox.grid(row=3, column=1, sticky='w', pady=2)
        self.color_combobox.set("红色")
        
        input_frame.columnconfigure(1, weight=1)
        
        # 操作按钮
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(fill='x')
        
        self.add_update_button = ttk.Button(
            button_frame, 
            text="添加设备", 
            command=self._on_add_or_update
        )
        self.add_update_button.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.delete_button = ttk.Button(
            button_frame, 
            text="删除设备", 
            command=self._on_device_delete, 
            state='disabled'
        )
        self.delete_button.pack(side='left', expand=True, fill='x', padx=(5, 0))
        
        # 提示信息
        tip_label = ttk.Label(
            parent,
            text="💡 最多支持10个设备 | 选择列表项可编辑",
            font=('Arial', 9),
            foreground='#666666'
        )
        tip_label.pack(anchor='w')
    
    # ========== 标签页4: 系统操作 ==========
    
    def _create_action_tab_content(self, parent):
        """
        创建系统操作标签页内容
        
        Args:
            parent: 标签页容器
        """
        # === 导出功能区域 ===
        export_frame = ttk.LabelFrame(parent, text="📤 导出功能", padding=(10, 10))
        export_frame.pack(fill='x', pady=(0, 15))
        
        export_btn = ttk.Button(
            export_frame,
            text="📷 导出PNG图像",
            command=self._on_export,
            style='Custom.TButton'
        )
        export_btn.pack(fill='x', pady=(0, 5))
        
        export_tip = ttk.Label(
            export_frame,
            text="导出为高清 1920x1920 分辨率 PNG 图像",
            font=('Arial', 9),
            foreground='#666666'
        )
        export_tip.pack(anchor='w')
        
        # === 数据管理区域 ===
        data_frame = ttk.LabelFrame(parent, text="🗃️ 数据管理", padding=(10, 10))
        data_frame.pack(fill='x', pady=(0, 15))
        
        reset_btn = ttk.Button(
            data_frame,
            text="🔄 重置所有数据",
            command=self._on_reset
        )
        reset_btn.pack(fill='x', pady=(0, 5))
        
        reset_tip = ttk.Label(
            data_frame,
            text="清除所有设备、测量点，坐标范围恢复默认",
            font=('Arial', 9),
            foreground='#666666'
        )
        reset_tip.pack(anchor='w')
        
        # === 快捷键说明区域 ===
        shortcut_frame = ttk.LabelFrame(parent, text="⌨️ 快捷键", padding=(10, 10))
        shortcut_frame.pack(fill='x', pady=(0, 15))
        
        shortcuts = [
            ("Ctrl/Cmd + S", "导出PNG图像"),
            ("Ctrl/Cmd + R", "重置所有数据"),
        ]
        
        for key, desc in shortcuts:
            row = ttk.Frame(shortcut_frame)
            row.pack(fill='x', pady=2)
            ttk.Label(row, text=key, font=('Arial', 10, 'bold'), width=15).pack(side='left')
            ttk.Label(row, text=desc, font=('Arial', 10)).pack(side='left')
        
        # === 操作提示区域 ===
        tip_frame = ttk.LabelFrame(parent, text="💡 操作提示", padding=(10, 10))
        tip_frame.pack(fill='x', pady=(0, 10))
        
        tip_text = (
            "• 左键点击坐标区域创建测量点\n"
            "• 双击测量点绘制90度扇形\n"
            "• 右键点击清除测量点和扇形\n"
            "• 拖拽标签可调整位置"
        )
        
        tip_label = ttk.Label(
            tip_frame,
            text=tip_text,
            font=('Arial', 10),
            foreground='#333333',
            justify='left'
        )
        tip_label.pack(anchor='w')
    
    # ========== 事件处理方法 ==========
    
    def _bind_events(self):
        """
        绑定事件
        """
        if self.device_treeview:
            self.device_treeview.bind('<<TreeviewSelect>>', self._on_device_select)
        
        # 回车键应用范围
        self.x_range_var.trace('w', self._on_range_entry_change)
        self.y_range_var.trace('w', self._on_range_entry_change)
    
    def _on_tab_changed(self, event=None):
        """
        标签页切换事件处理 ✨ Bug修复
        
        确保切换标签页后立即刷新界面内容
        """
        if self.notebook:
            # 强制更新所有待处理的界面任务
            self.notebook.update_idletasks()
            # 额外触发一次父容器的更新，确保内容完全刷新
            self.parent_frame.update_idletasks()
    
    def _on_range_entry_change(self, *args):
        """范围输入框变化事件"""
        pass
    
    def _on_range_apply(self):
        """应用坐标范围"""
        try:
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            
            if x_range < 0.1 or x_range > 50:
                raise ValueError("X轴范围必须在0.1-50之间")
            if y_range < 0.1 or y_range > 50:
                raise ValueError("Y轴范围必须在0.1-50之间")
            
            if self.on_range_change_callback:
                self.on_range_change_callback(x_range, y_range)
                
        except ValueError as e:
            self._show_error("输入错误", f"坐标范围设置失败：{str(e)}")
    
    def _on_user_coord_toggle(self):
        """处理用户坐标系开关切换事件"""
        enabled = self.user_coord_enabled_var.get()
        self._toggle_user_position_visibility(enabled)
        self.update_coordinate_mode_status(enabled)
        
        if self.on_user_coord_toggle_callback:
            self.on_user_coord_toggle_callback(enabled)
        
        print(f"✨ 用户坐标系{'启用' if enabled else '关闭'}")
    
    def _toggle_user_position_visibility(self, show: bool):
        """切换用户位置设置区域的显示/隐藏"""
        if show:
            self.user_position_frame.pack(fill='x', pady=(5, 0))
        else:
            self.user_position_frame.pack_forget()
    
    def _on_user_position_set(self):
        """处理设置用户位置按钮点击事件"""
        try:
            user_x = float(self.user_x_var.get())
            user_y = float(self.user_y_var.get())
            
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            
            if abs(user_x) > x_range or abs(user_y) > y_range:
                self._show_error(
                    "坐标超出范围",
                    f"用户位置坐标必须在当前显示范围内\n"
                    f"X范围: ±{x_range}, Y范围: ±{y_range}"
                )
                return
            
            if self.on_user_position_set_callback:
                self.on_user_position_set_callback(user_x, user_y)
            
            self.update_user_position_status((user_x, user_y))
            print(f"✨ 设置用户位置: ({user_x}, {user_y})")
            
        except ValueError:
            self._show_error("输入错误", "请输入有效的数字坐标")
    
    # === 背景图事件处理方法 ===
    
    def _on_import_background(self):
        """处理导入背景图按钮点击"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="选择户型图",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG"),
                ("PNG文件", "*.png *.PNG"),
                ("JPEG文件", "*.jpg *.jpeg *.JPG *.JPEG"),
                ("所有文件", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        if self.on_background_import_callback:
            self.on_background_import_callback(file_path)
    
    def _on_remove_background(self):
        """处理移除背景图按钮点击"""
        if self.on_background_remove_callback:
            self.on_background_remove_callback()
        self._reset_background_ui()
    
    def _on_bg_ppu_change(self, event=None):
        """处理像素比例输入变化"""
        try:
            ppu = float(self.bg_ppu_var.get())
            if ppu <= 0:
                raise ValueError("比例必须大于0")
            
            if self.on_background_scale_change_callback:
                self.on_background_scale_change_callback(ppu)
                
        except ValueError as e:
            print(f"⚠️ 无效的比例值: {e}")
    
    def _on_bg_alpha_change(self, value=None):
        """处理透明度滑块变化"""
        alpha = self.bg_alpha_var.get()
        self.bg_alpha_label.config(text=f"{int(alpha * 100)}%")
        
        if self.on_background_alpha_change_callback:
            self.on_background_alpha_change_callback(alpha)
    
    def _on_bg_visibility_toggle(self):
        """处理显示/隐藏切换"""
        visible = self.bg_visible_var.get()
        if self.on_background_visibility_toggle_callback:
            self.on_background_visibility_toggle_callback(visible)
    
    # === 设备管理事件处理 ===
    
    def _on_device_select(self, event=None):
        """设备选择事件"""
        selection = self.device_treeview.selection()
        if selection:
            self.selected_device_id = selection[0]
            device = self._get_device_by_id(self.selected_device_id)
            if device:
                self.device_name_var.set(device.name)
                self.device_x_var.set(str(device.x))
                self.device_y_var.set(str(device.y))
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
            self._set_input_state('normal')
    
    def _on_add_or_update(self):
        """添加或更新设备"""
        try:
            name = self.device_name_var.get().strip()
            x = float(self.device_x_var.get())
            y = float(self.device_y_var.get())
            
            color_name = self.device_color_var.get()
            color = self.COLOR_OPTIONS.get(color_name, Device.COLOR_RED)
            
            if self.selected_device_id and self.on_device_update_callback:
                old_device = self._get_device_by_id(self.selected_device_id)
                if old_device:
                    new_device = Device(name, x, y, device_id=old_device.id, color=color)
                    self.on_device_update_callback(old_device, new_device)
            elif self.on_device_add_callback:
                new_device = Device(name, x, y, color=color)
                self.on_device_add_callback(new_device)
            
            self._clear_device_inputs()
            self.device_treeview.selection_set('')
            
        except ValueError:
            self._show_error("输入无效", "坐标必须是有效的数字。")
        except Exception as e:
            self._show_error("操作失败", str(e))
    
    def _on_device_delete(self):
        """删除设备"""
        if not self.selected_device_id or not self.on_device_delete_callback:
            return
            
        if self._ask_confirm("确认删除", "确定要删除选中的设备吗？"):
            device_to_delete = self._get_device_by_id(self.selected_device_id)
            if device_to_delete:
                self.on_device_delete_callback(device_to_delete)
    
    # === 系统操作事件处理 ===
    
    def _on_export(self):
        """导出PNG图像"""
        if self.on_export_callback:
            self.on_export_callback()
    
    def _on_reset(self):
        """重置所有数据"""
        if not self._ask_confirm(
            "确认重置",
            "确定要重置所有数据吗？\n这将清除所有设备和测量点，坐标范围恢复为10x10。"
        ):
            return
        
        # 调用控制器的重置回调，由控制器统一处理重置逻辑
        # 控制器会调用 reset_inputs() 方法来重置UI状态
        if self.on_reset_callback:
            self.on_reset_callback()
        # 注意：不要在这里手动设置坐标范围，由控制器通过 reset_inputs() 统一处理
        # 避免与控制器的重置状态产生不同步 ✨ Bug修复
    
    # ========== 辅助方法 ==========
    
    def _refresh_device_list(self):
        """刷新Treeview中的设备列表"""
        for item in self.device_treeview.get_children():
            self.device_treeview.delete(item)
            
        for device in self.devices:
            color_name = self.COLOR_NAMES.get(device.color, "红色")
            self.device_treeview.insert(
                "", "end", iid=device.id, 
                values=(device.name, f"{device.x:.3f}", f"{device.y:.3f}", color_name)
            )
        self._on_device_select()
    
    def _clear_device_inputs(self):
        """清除设备输入框"""
        self.device_name_var.set("")
        self.device_x_var.set("")
        self.device_y_var.set("")
        self.device_color_var.set("红色")
        if self.device_treeview.selection():
            self.device_treeview.selection_set('')
        self.selected_device_id = None
        
    def _set_input_state(self, state):
        """设置输入框状态"""
        self.name_entry.config(state=state)
        self.x_entry.config(state=state)
        self.y_entry.config(state=state)
        if self.color_combobox:
            self.color_combobox.config(state='readonly' if state == 'normal' else 'disabled')
        
    def _get_device_by_id(self, device_id: str) -> Optional[Device]:
        """根据ID获取设备"""
        for device in self.devices:
            if device.id == device_id:
                return device
        return None
    
    def _show_error(self, title: str, message: str):
        """显示错误消息"""
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self.parent_frame)
    
    def _ask_confirm(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        from tkinter import messagebox
        return messagebox.askyesno(title, message, parent=self.parent_frame)
    
    # ========== 公共接口方法 ==========
    
    def set_range_change_callback(self, callback: Callable[[float, float], None]):
        """设置坐标范围变化回调函数"""
        self.on_range_change_callback = callback
    
    def set_device_add_callback(self, callback: Callable[[Device], None]):
        """设置设备添加回调函数"""
        self.on_device_add_callback = callback
    
    def set_device_update_callback(self, callback: Callable[[Device, Device], None]):
        """设置设备更新回调函数"""
        self.on_device_update_callback = callback
    
    def set_device_delete_callback(self, callback: Callable[[Device], None]):
        """设置设备删除回调函数"""
        self.on_device_delete_callback = callback
    
    def set_export_callback(self, callback: Callable[[], None]):
        """设置导出回调函数"""
        self.on_export_callback = callback
    
    def set_reset_callback(self, callback: Callable[[], None]):
        """设置重置回调函数"""
        self.on_reset_callback = callback
    
    def set_user_coord_toggle_callback(self, callback: Callable[[bool], None]):
        """设置用户坐标系开关切换回调函数"""
        self.on_user_coord_toggle_callback = callback
    
    def set_user_position_set_callback(self, callback: Callable[[float, float], None]):
        """设置用户位置设置回调函数"""
        self.on_user_position_set_callback = callback
    
    # === 背景图回调设置方法 ===
    
    def set_background_import_callback(self, callback: Callable[[str], None]):
        """设置背景图导入回调"""
        self.on_background_import_callback = callback
    
    def set_background_remove_callback(self, callback: Callable[[], None]):
        """设置背景图移除回调"""
        self.on_background_remove_callback = callback
    
    def set_background_scale_change_callback(self, callback: Callable[[float], None]):
        """设置背景图比例变化回调"""
        self.on_background_scale_change_callback = callback
    
    def set_background_alpha_change_callback(self, callback: Callable[[float], None]):
        """设置背景图透明度变化回调"""
        self.on_background_alpha_change_callback = callback
    
    def set_background_visibility_toggle_callback(self, callback: Callable[[bool], None]):
        """设置背景图显示切换回调"""
        self.on_background_visibility_toggle_callback = callback
    
    # === 状态更新方法 ===
    
    def update_devices(self, devices: List[Device]):
        """由控制器调用，更新设备列表并刷新UI"""
        self.devices = devices
        self._refresh_device_list()
        self._clear_device_inputs()
        self.selected_device_id = None
    
    def update_background_info(self, pixel_width: int, pixel_height: int, dpi: int,
                               actual_width: float, actual_height: float,
                               x_min: float, x_max: float, y_min: float, y_max: float):
        """更新背景图信息显示"""
        info_text = f"尺寸: {pixel_width} × {pixel_height} 像素\nDPI: {dpi}"
        self.bg_info_label.config(text=info_text, foreground='black')
        
        result_text = (
            f"→ 实际尺寸: {actual_width:.1f} 米 × {actual_height:.1f} 米\n"
            f"→ 坐标范围: X[{x_min:.1f}, {x_max:.1f}]  Y[{y_min:.1f}, {y_max:.1f}]"
        )
        self.bg_scale_result_label.config(text=result_text)
        self.bg_remove_btn.config(state='normal')
    
    def _reset_background_ui(self):
        """重置背景图 UI 到初始状态"""
        if self.bg_info_label:
            self.bg_info_label.config(text="未加载图片", foreground='gray')
        if self.bg_scale_result_label:
            self.bg_scale_result_label.config(text="")
        if self.bg_remove_btn:
            self.bg_remove_btn.config(state='disabled')
        if self.bg_ppu_var:
            self.bg_ppu_var.set("100")
        if self.bg_alpha_var:
            self.bg_alpha_var.set(0.5)
        if self.bg_alpha_label:
            self.bg_alpha_label.config(text="50%")
        if self.bg_visible_var:
            self.bg_visible_var.set(True)
    
    def set_background_ppu(self, ppu: float):
        """设置背景图像素比例值（用于项目加载）"""
        if self.bg_ppu_var:
            self.bg_ppu_var.set(f"{ppu:.1f}")
    
    def set_background_alpha(self, alpha: float):
        """设置背景图透明度（用于项目加载）"""
        if self.bg_alpha_var:
            self.bg_alpha_var.set(alpha)
        if self.bg_alpha_label:
            self.bg_alpha_label.config(text=f"{int(alpha * 100)}%")
    
    def set_background_visible(self, visible: bool):
        """设置背景图显示状态（用于项目加载）"""
        if self.bg_visible_var:
            self.bg_visible_var.set(visible)
    
    def update_coordinate_mode_status(self, user_coord_enabled: bool):
        """更新坐标系模式状态显示"""
        if user_coord_enabled:
            self.coord_mode_label.config(
                text="坐标系模式: 用户坐标系",
                foreground='#7b1fa2'
            )
            self.interaction_hint_label.config(
                text="[提示] 测量以用户位置为原点，双击扇形以用户为中心",
                foreground='#7b1fa2'
            )
        else:
            self.coord_mode_label.config(
                text="坐标系模式: 世界坐标系",
                foreground='#2196F3'
            )
            self.interaction_hint_label.config(
                text="[提示] 左键单击测量距离，双击绘制扇形",
                foreground='#FF9800'
            )
    
    def update_user_position_status(self, user_position: Optional[tuple]):
        """更新用户位置状态显示"""
        if user_position:
            x, y = user_position
            self.user_pos_label.config(
                text=f"用户位置: ({x:.1f}, {y:.1f})",
                foreground='#4CAF50'
            )
        else:
            self.user_pos_label.config(
                text="用户位置: 未设置",
                foreground='#666666'
            )
    
    def update_range_status(self, x_range: float, y_range: float):
        """更新坐标范围状态"""
        self.x_range_var.set(f"{x_range:.1f}")
        self.y_range_var.set(f"{y_range:.1f}")
    
    def get_coordinate_range(self) -> tuple:
        """获取当前坐标范围设置"""
        try:
            x_range = float(self.x_range_var.get())
            y_range = float(self.y_range_var.get())
            return (x_range, y_range)
        except ValueError:
            return (10.0, 10.0)
    
    def clear_selection(self):
        """清除当前设备选择和输入"""
        self._clear_device_inputs()
        if self.device_treeview.selection():
            self.device_treeview.selection_set('')
        self.selected_device_id = None
        self.add_update_button.config(text="添加设备")
        self.delete_button.config(state='disabled')
    
    def reset_inputs(self):
        """重置所有输入为默认值"""
        self.x_range_var.set("10.0")
        self.y_range_var.set("10.0")

        self.user_coord_enabled_var.set(False)
        self.user_x_var.set("0.0")
        self.user_y_var.set("0.0")
        self._toggle_user_position_visibility(False)

        self.devices.clear()
        self._refresh_device_list()
        self._clear_device_inputs()

        # 重置背景图UI
        self._reset_background_ui()
        
        # 重置状态标签（坐标系模式、用户位置状态）
        self.update_coordinate_mode_status(False)
        self.update_user_position_status(None)

        print("✅ 输入面板重置完成")

    def is_user_coord_enabled(self) -> bool:
        """查询用户坐标系是否已启用"""
        return self.user_coord_enabled_var.get()
    
    def get_user_position(self) -> tuple:
        """获取当前设置的用户位置"""
        try:
            x = float(self.user_x_var.get())
            y = float(self.user_y_var.get())
            return (x, y)
        except ValueError:
            return (0.0, 0.0)
    
    # === 项目加载辅助方法 ===
    
    def set_coordinate_range(self, x_range: float, y_range: float):
        """设置坐标范围（用于项目加载）"""
        self.x_range_var.set(f"{x_range:.1f}")
        self.y_range_var.set(f"{y_range:.1f}")
    
    def set_user_coord_enabled(self, enabled: bool, trigger_callback: bool = False):
        """
        设置用户坐标系启用状态（用于项目加载）
        
        Args:
            enabled: 是否启用
            trigger_callback: 是否触发回调，默认False（项目加载时不应触发，避免重复操作）
        """
        self.user_coord_enabled_var.set(enabled)
        # 更新UI状态（显示/隐藏用户位置设置区域）
        self._toggle_user_position_visibility(enabled)
        # 只有明确要求时才触发回调
        if trigger_callback:
            self._on_user_coord_toggle()
    
    def set_user_position(self, x: float, y: float):
        """设置用户位置（用于项目加载）"""
        self.user_x_var.set(f"{x:.3f}")
        self.user_y_var.set(f"{y:.3f}")
        self.update_user_position_status((x, y))
    
    # === 标签页切换方法 ===
    
    def select_tab(self, tab_index: int):
        """
        切换到指定标签页
        
        Args:
            tab_index: 标签页索引 (0=坐标设置, 1=背景设置, 2=设备管理, 3=系统操作)
        """
        if self.notebook and 0 <= tab_index < self.notebook.index('end'):
            self.notebook.select(tab_index)
    
    def get_current_tab(self) -> int:
        """
        获取当前选中的标签页索引
        
        Returns:
            当前标签页索引
        """
        if self.notebook:
            return self.notebook.index(self.notebook.select())
        return 0
