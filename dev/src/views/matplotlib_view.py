# -*- coding: utf-8 -*-
"""
Matplotlib坐标展示区视图

基于Matplotlib实现的高性能绘图组件，替换原有的Canvas+Pillow方案
优化版本：减少adjustText依赖，使用高性能原生布局算法
"""

import tkinter as tk
from typing import Optional, List, Callable, Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import numpy as np
import math
import time

# 配置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

from models.device_model import Device
from models.measurement_model import MeasurementPoint
from models.locked_measurement import LockedMeasurement
from models.background_model import BackgroundImage
# 使用新的高性能布局管理器
from utils.fast_layout import FastLayoutManager, LayoutElement, ElementType, BoundingBox

# 可选导入adjustText（仅在需要时使用）
try:
    from adjustText import adjust_text
    ADJUSTTEXT_AVAILABLE = True
except ImportError:
    ADJUSTTEXT_AVAILABLE = False
    print("⚠️ adjustText库未安装，将使用高性能原生布局算法")

class MatplotlibView:
    """
    基于Matplotlib的坐标展示区类
    
    优化版本：使用高性能原生布局算法替代大部分adjustText功能
    """
    
    # 图形尺寸和样式配置
    FIGURE_SIZE = (8, 8)
    DPI = 100
    
    # 界面配色（与原版保持一致）
    COLORS = {
        'background': '#e0f7fa',      # 浅蓝色背景
        'grid_line': '#b0bec5',       # 灰蓝色网格线
        'axis_line': '#37474f',       # 深灰色坐标轴
        'device_point': '#c62828',    # 红色设备点
        'origin_point': '#1e88e5',    # 蓝色原点
        'measurement_point': '#2e7d32', # 绿色测量点 (对照HTML)
        'measurement_line': '#4caf50',  # 绿色测量线 (对照HTML)
        'text_color': '#1b5e20',      # 深绿色文字 (对照HTML)
        'label_bg': (1.0, 1.0, 1.0, 0.85),        # 半透明白色标签背景 (RGBA元组)
        'label_border': '#2e7d32',    # 绿色标签边框
        'sector_fill': (211/255, 47/255, 47/255, 0.3),     # 红色扇形填充色 (对照HTML)
        'sector_edge': '#d32f2f',     # 红色扇形边缘 (对照HTML)
        'crosshair': (0.0, 0.0, 0.0, 0.5),  # 十字光标颜色
        # 用户坐标系配色 ✨ 双坐标系功能 - 视觉优化增强版
        'user_grid': (211/255, 47/255, 47/255, 0.5),  # 红色网格，与用户坐标轴保持一致
        'user_axis': '#d32f2f',                     # 红色虚线坐标轴（按需求调整）
        'user_marker': '#5e35b1',     # 更醒目的深紫色用户位置标记
        'user_text': '#4a148c',       # 深紫色文字
        # ✨ V2.4 锁定扇形功能配色
        'pin_unlocked': (1.0, 1.0, 1.0, 0.8),      # 解锁图钉：白色
        'pin_locked': '#e53935',                    # 锁定图钉：红色
        'pin_bg_unlocked': (0.9, 0.9, 0.9, 0.5),   # 解锁背景：半透明灰
        'pin_bg_locked': (1.0, 1.0, 1.0, 1.0),     # 锁定背景：纯白不透明
        'locked_line': '#1976d2',                   # 锁定实线：蓝色
        'locked_sector_fill': (25/255, 118/255, 210/255, 0.25),  # 锁定扇形：蓝色
        'locked_sector_edge': '#1976d2',            # 锁定扇形边缘：蓝色
        'comparison_line': '#ff9800',               # 对比虚线：橙色
        'comparison_text': '#e65100',               # 对比信息文字：深橙色
        'comparison_bg': '#fff3e0',                 # 对比信息背景：浅橙色
    }
    
    def __init__(self, parent_frame: tk.Frame):
        """
        初始化Matplotlib视图
        
        Args:
            parent_frame: 父容器框架
        """
        self.parent_frame = parent_frame
        
        # 数据存储
        self.devices: List[Device] = []
        self.measurement_point: Optional[MeasurementPoint] = None
        self.current_range = (10.0, 10.0)  # 当前坐标范围
        
        # 扇形数据
        self.sector_point: Optional[Tuple[float, float]] = None
        
        # 用户坐标系数据 ✨ 双坐标系功能
        self.user_coord_enabled = False
        self.user_position: Optional[Tuple[float, float]] = None
        
        # 鼠标状态
        self.mouse_pos: Optional[Tuple[float, float]] = None
        self.last_click_time = 0
        self.click_tolerance = 0.3  # 双击时间间隔
        
        # 性能优化缓存 ✨ 性能优化
        self._last_coordinate_info_text = ""  # 缓存上次的坐标信息文本
        self._coordinate_info_update_needed = True  # 是否需要更新坐标信息
        
        # 绘制对象引用（用于更新和清除）
        self.device_artists = []
        self.measurement_artists = []
        self.sector_artists = []
        self.crosshair_artists = []
        self.user_position_artists = []  # 用户位置相关绘制对象 ✨ 双坐标系功能
        self.coordinate_info_artists = []  # 坐标信息显示对象 ✨ 第五步新增功能
        
        # ✨ V2.4 锁定扇形功能 - 说话人方向和影响范围
        self.locked_measurement = LockedMeasurement()  # 锁定测量数据模型
        self.pin_artists = []              # 图钉绘制对象
        self.comparison_artists = []       # 对比虚线和信息框
        self.pin_position = None           # 图钉位置 (x, y)
        self.toast_artist = None           # Toast 提示对象
        self.toast_timer_id = None         # Toast 定时器 ID
        
        # ✨ V2.5 背景户型图功能
        self.background_image: Optional[BackgroundImage] = None  # 背景图数据模型
        self.background_artist = None      # imshow 返回的 AxesImage 对象
        
        # ✨ 高性能布局管理器（替代adjustText主要功能）
        self.fast_layout_manager: Optional[FastLayoutManager] = None
        
        # ✨ adjustText智能避让系统（仅在复杂场景下使用）
        self.text_objects = []  # 所有需要智能避让的文本对象
        self.obstacle_objects = []  # 障碍物对象（扇形、连线等）
        self.use_adjusttext_threshold = 6  # 文本数量超过此阈值时才使用adjustText
        
        # 回调函数
        self.on_click_callback: Optional[Callable[[float, float], None]] = None
        self.on_right_click_callback: Optional[Callable[[], None]] = None
        self.on_mouse_move_callback: Optional[Callable[[float, float], None]] = None
        self.on_double_click_callback: Optional[Callable[[float, float], None]] = None
        
        # ✨ 标签拖拽功能 - 状态变量
        self._dragging_label: Optional[any] = None  # 当前正在拖拽的标签对象
        self._drag_start_pos: Optional[Tuple[float, float]] = None  # 拖拽起始位置
        self._label_original_pos: Optional[Tuple[float, float]] = None  # 标签原始位置
        self._draggable_labels: List[any] = []  # 所有可拖拽的标签列表
        self._is_dragging: bool = False  # 是否正在拖拽
        
        # 初始化Matplotlib组件
        self._setup_matplotlib()
        
        # 初始化高性能布局管理器
        self._init_fast_layout_manager()
        
        print("✅ MatplotlibView初始化完成（高性能优化版）")
    
    def _setup_matplotlib(self):
        """设置Matplotlib组件"""
        # 创建Figure和Axes
        self.figure = Figure(figsize=self.FIGURE_SIZE, dpi=self.DPI, 
                           facecolor=self.COLORS['background'])
        self.axes = self.figure.add_subplot(111)
        
        # 创建Tkinter Canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.parent_frame)
        tk_widget = self.canvas.get_tk_widget()
        tk_widget.pack(fill=tk.BOTH, expand=True)
        
        # ✨ 禁止canvas抢占焦点，解决与Tkinter Entry组件的焦点冲突问题
        tk_widget.configure(takefocus=0)
        
        # 绑定事件
        self.canvas.mpl_connect('button_press_event', self._on_mouse_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('axes_leave_event', self._on_mouse_leave)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)  # ✨ 标签拖拽
        
        # 初始化坐标系统
        self._setup_coordinate_system(*self.current_range)
        
        print("✅ Matplotlib组件设置完成")
    
    def _init_fast_layout_manager(self):
        """初始化高性能布局管理器"""
        x_range, y_range = self.current_range
        canvas_bounds = (-x_range, -y_range, x_range, y_range)
        self.fast_layout_manager = FastLayoutManager(canvas_bounds)
        print("🚀 高性能布局管理器初始化完成")
    
    def _setup_coordinate_system(self, x_range: float, y_range: float):
        """
        设置坐标系统 ✨ 优化版本，支持整数步进
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
        """
        self.current_range = (x_range, y_range)
        
        # 清除之前的绘制内容
        self.axes.clear()
        
        # 设置坐标轴范围
        self.axes.set_xlim(-x_range, x_range)
        self.axes.set_ylim(-y_range, y_range)
        
        # 设置整数步进的刻度
        x_ticks = list(range(int(-x_range), int(x_range) + 1))
        y_ticks = list(range(int(-y_range), int(y_range) + 1))
        self.axes.set_xticks(x_ticks)
        self.axes.set_yticks(y_ticks)
        
        # 设置网格
        self.axes.grid(True, color=self.COLORS['grid_line'], alpha=0.6, linewidth=0.8)
        
        # 设置坐标轴样式
        self.axes.axhline(y=0, color=self.COLORS['axis_line'], linewidth=1.5, alpha=0.9)
        self.axes.axvline(x=0, color=self.COLORS['axis_line'], linewidth=1.5, alpha=0.9)
        
        # 设置背景色
        self.axes.set_facecolor(self.COLORS['background'])
        
        # 设置标题和标签
        self.axes.set_xlabel('X 坐标', fontsize=12, color=self.COLORS['axis_line'])
        self.axes.set_ylabel('Y 坐标', fontsize=12, color=self.COLORS['axis_line'])
        
        # 设置相等的宽高比
        self.axes.set_aspect('equal', adjustable='box')
        
        # 说明：原点的"大蓝点"已移除（用户反馈：原始坐标系无需额外强调原点）
        
        # ✨ V2.5 重新绘制背景图（如果有）
        self._draw_background()
        
        print(f"✅ 坐标系统设置完成: ±{x_range} x ±{y_range}")
    
    def _should_use_adjusttext(self) -> bool:
        """判断是否需要使用adjustText"""
        if not ADJUSTTEXT_AVAILABLE:
            return False
        
        # 只有在文本数量超过阈值且有复杂障碍物时才使用adjustText
        text_count = len(self.text_objects)
        has_complex_obstacles = len(self.obstacle_objects) > 0
        
        return text_count >= self.use_adjusttext_threshold and has_complex_obstacles
    
    def _apply_smart_text_adjustment(self):
        """
        智能文本避让：优先使用高性能原生算法，复杂场景下才使用adjustText
        """
        if not self.text_objects:
            return
        
        try:
            if self._should_use_adjusttext():
                # 复杂场景：使用adjustText
                self._apply_adjusttext_layout()
                print("✅ 使用adjustText处理复杂布局")
            else:
                # 简单场景：使用高性能原生算法
                self._apply_native_layout()
                print("🚀 使用高性能原生布局算法")
                
        except Exception as e:
            print(f"⚠️ 布局处理失败，回退到默认位置: {e}")
    
    def _apply_native_layout(self):
        """使用高性能原生布局算法（力导向版）"""
        if not self.fast_layout_manager:
            return
        
        # 1. 清除动态元素（保留静态障碍物）
        self.fast_layout_manager.clear_dynamic_elements()
        
        # 2. 将所有文本对象添加到布局管理器
        text_element_map = {} # 映射 element_id -> text_obj
        
        for i, text_obj in enumerate(self.text_objects):
            element_type = self._get_element_type_from_text(text_obj)
            element_id = f"{element_type.value}_{id(text_obj)}"
            text_element_map[element_id] = text_obj
            
            # 获取当前位置作为初始位置
            current_x, current_y = text_obj.get_position()
            
            # 获取尺寸
            box_width, box_height = self.fast_layout_manager.info_box_sizes.get(
                element_type, (1.0, 0.5)
            )
            
            # 创建边界框
            bbox = BoundingBox(
                current_x - box_width/2, current_y - box_height/2,
                current_x + box_width/2, current_y + box_height/2
            )
            
            # === 固定标签特殊处理 ===
            # 1) 设备标签：仅作为静态障碍物参与布局，不再被力导向算法移动，
            #    以保证其遵循“左/上/右/下 + 1格”规则。
            # 2) 测量标签：用户要求默认固定在“单击点正下方下移2格”，因此同样固定不移动。
            if element_type in (ElementType.DEVICE_INFO, ElementType.MEASUREMENT_INFO):
                element = LayoutElement(
                    element_type,
                    bbox,
                    (current_x, current_y),  # 锚点对静态元素无实际影响
                    element_id=element_id,
                    movable=False,
                    static=True
                )
            else:
                # 非设备标签仍按原逻辑参与力导向布局
                if element_type == ElementType.MEASUREMENT_INFO and self.measurement_point:
                    anchor_x = self.measurement_point.x
                    anchor_y = self.measurement_point.y
                elif element_type == ElementType.USER_POSITION and self.user_position:
                    anchor_x, anchor_y = self.user_position
                else:
                    anchor_x = current_x
                    anchor_y = current_y
                
                element = LayoutElement(
                    element_type,
                    bbox,
                    (anchor_x, anchor_y),
                    element_id=element_id,
                    movable=True,
                    static=False
                )
            
            self.fast_layout_manager.add_element(element)
            
        # 3. 计算布局
        self.fast_layout_manager.compute_layout(iterations=50)
        
        # 4. 更新文本位置
        for element in self.fast_layout_manager.elements:
            # 只更新非静态元素的位置；设备标签（静态元素）保持原位
            if not element.static and element.element_id in text_element_map:
                text_obj = text_element_map[element.element_id]
                text_obj.set_position((element.current_x, element.current_y))
    
    def _apply_adjusttext_layout(self):
        """使用adjustText进行复杂布局（仅在必要时）"""
        # 清空障碍物列表，重新收集
        self.obstacle_objects.clear()
        
        # 收集扇形障碍物
        for artist in self.sector_artists:
            if hasattr(artist, 'get_paths') or hasattr(artist, 'get_xy'):
                self.obstacle_objects.append(artist)
        # 仅对"非固定标签"使用adjustText（设备标签、测量标签保持固定位置）
        # 同时收集固定标签作为障碍物，防止其他标签与固定标签重叠
        target_texts = []
        fixed_labels = []  # 固定标签列表（设备标签、测量标签）
        
        for t in self.text_objects:
            element_type = self._get_element_type_from_text(t)
            if element_type in (ElementType.DEVICE_INFO, ElementType.MEASUREMENT_INFO):
                # 设备标签和测量标签保持固定位置，作为障碍物
                fixed_labels.append(t)
            else:
                # 其他标签参与adjustText调整
                target_texts.append(t)
        
        # 将固定标签添加到障碍物列表中，这样adjustText会让其他标签避开它们
        # 这可以防止其他标签移动到与固定测量标签/设备标签重叠的位置
        self.obstacle_objects.extend(fixed_labels)
        
        if not target_texts:
            return
        
        # 使用adjustText进行智能避让（减少参数，提升性能）
        adjust_text(
            target_texts,
            ax=self.axes,
            add_objects=self.obstacle_objects if self.obstacle_objects else None,
            arrowprops=dict(
                arrowstyle='->',
                color='gray',
                alpha=0.5,
                lw=0.8
            ),
            # 简化的参数设置，提升性能
            force_points=(0.2, 0.2),   # 减少推力
            force_text=(0.3, 0.3),     # 减少推力
            force_objects=(0.5, 0.5),  # 减少推力
            max_move=0.3,              # 减少最大移动距离
            only_move={'points': 'xy', 'text': 'xy'},
        )
    
    def _get_element_type_from_text(self, text_obj) -> ElementType:
        """从文本对象推断元素类型
        
        检测顺序很重要：
        1. 测量标签优先（包含"距离:"和"角度:"），因为它也可能包含"[世界坐标系]"/"[用户坐标系]"
        2. 用户原点标签（以"[用户] 位置"开头）
        3. 坐标信息框（包含"[世界]"或"[用户]"但不是测量标签）
        4. 其他默认为设备标签
        """
        text_content = text_obj.get_text()
        
        # 1. 测量标签优先检测（包含"距离:"和"角度:"）
        #    测量标签格式: "[世界坐标系]\n距离: ...\n角度: ..." 或 "[用户坐标系]\n..."
        if '距离:' in text_content and '角度:' in text_content:
            return ElementType.MEASUREMENT_INFO
        
        # 2. 用户原点标签（固定文本格式: "[用户] 位置\n(...)"）
        if text_content.startswith('[用户] 位置'):
            return ElementType.USER_POSITION
        
        # 3. 坐标信息框（包含"[世界]"或"[用户]"但不是上述类型）
        if '[世界]' in text_content or '[用户]' in text_content:
            return ElementType.COORDINATE_INFO
        
        # 4. 其他默认为设备标签
        return ElementType.DEVICE_INFO
    
    def _clear_text_objects(self):
        """清空文本对象列表"""
        self.text_objects.clear()
        self.obstacle_objects.clear()
        if self.fast_layout_manager:
            self.fast_layout_manager.clear_elements()
    
    def _on_mouse_click(self, event):
        """
        处理鼠标点击事件 ✨ 支持标签拖拽 + 图钉点击
        """
        if event.inaxes != self.axes:
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        
        current_time = time.time()
        
        if event.button == 1:  # 左键
            # ✨ V2.4 首先检查是否点击了图钉
            if self._is_click_on_pin(x, y):
                self._toggle_pin_lock()
                return
            
            # ✨ 检查是否点击了可拖拽的标签
            clicked_label = self._find_label_at(x, y)
            if clicked_label is not None:
                # 开始拖拽标签
                self._start_label_drag(clicked_label, x, y)
                return
            
            # 检查是否为双击
            if current_time - self.last_click_time < self.click_tolerance:
                # 双击：绘制90度扇形
                self._handle_double_click(x, y)
            else:
                # 单击：创建测量点或对比虚线
                self._handle_single_click(x, y)
            
            self.last_click_time = current_time
            
        elif event.button == 3:  # 右键
            # ✨ 检查是否右键点击了标签（重置到自动位置）
            clicked_label = self._find_label_at(x, y)
            if clicked_label is not None:
                self._reset_label_to_auto(clicked_label)
                return
            
            # 清除测量点和扇形（根据锁定状态）
            self._handle_right_click()
    
    def _handle_single_click(self, x: float, y: float):
        """
        处理左键单击：创建测量点或对比虚线 ✨ V2.4 支持锁定对比模式
        """
        # ✨ V2.4 如果已锁定，绘制对比虚线
        if self.locked_measurement.is_locked:
            self._draw_comparison_line(x, y)
            return
        
        # 根据用户坐标系状态选择参考点 ✨ 核心逻辑
        if self.user_coord_enabled and self.user_position:
            # 用户坐标系模式：以用户位置为参考点
            reference_point = self.user_position
            print(f"📍 用户坐标系模式 - 测量点: ({x:.3f}, {y:.3f}), 参考点: {reference_point}")
        else:
            # 世界坐标系模式：以原点(0,0)为参考点
            reference_point = None
            print(f"📍 世界坐标系模式 - 测量点: ({x:.3f}, {y:.3f})")
        
        # 创建测量点对象
        self.measurement_point = MeasurementPoint(x, y, reference_point)
        
        # 重新绘制
        self._draw_measurement()
        
        # 触发回调
        if self.on_click_callback:
            self.on_click_callback(x, y)
        
        print(f"✅ 创建测量点: ({x:.3f}, {y:.3f})")
    
    def _handle_double_click(self, x: float, y: float):
        """
        处理左键双击：绘制90度扇形（以连线为平分线向两侧各45度）
        ✨ V2.4 增加锁定状态检测
        """
        # ✨ V2.4 如果已锁定，显示 Toast 提示并返回
        if self.locked_measurement.is_locked:
            self._show_toast("当前说话人声音影响区域已锁定，请解锁后重试")
            return
        
        # 保存扇形参考点
        self.sector_point = (x, y)
        
        # 计算中心点（原点或用户位置）
        if self.user_coord_enabled and self.user_position:
            center = self.user_position
        else:
            center = (0.0, 0.0)
        
        # ✨ V2.4 更新锁定测量数据（但未锁定）
        self.locked_measurement.set_measurement((x, y), center)
        
        # 重新绘制扇形
        self._draw_sector()
        
        # ✨ V2.4 绘制图钉（双击点正上方）
        self._draw_pin(x, y + 0.8)
        
        # 触发回调
        if self.on_double_click_callback:
            self.on_double_click_callback(x, y)
        
        print(f"✅ 创建扇形: 参考点({x:.3f}, {y:.3f})，点击图钉可锁定")
    
    def _handle_right_click(self):
        """
        处理右键单击：根据锁定状态决定清除范围 ✨ V2.4 锁定模式支持
        """
        # ✨ V2.4 如果已锁定，只清除对比虚线，保留锁定的扇形
        if self.locked_measurement.is_locked:
            self._clear_comparison()
            self.canvas.draw_idle()
            print("✅ 已清除对比虚线，锁定扇形保留")
            return
        
        # 解锁状态：清除全部（原有行为）
        # 清除测量点
        self.measurement_point = None
        self.sector_point = None
        
        # ✨ V2.4 清除锁定测量数据和图钉
        self.locked_measurement.clear()
        self._clear_pin()
        self._clear_comparison()
        
        # 恢复所有设备信息框到默认位置 ✨ 智能避让系统
        self._reset_device_info_positions()
        
        # 清除图形
        self._clear_measurement()
        self._clear_sector()
        
        # 清除布局管理器中的元素（除了设备信息框）
        if self.fast_layout_manager:
            self.fast_layout_manager.remove_element_by_type(ElementType.MEASUREMENT_INFO)
            self.fast_layout_manager.remove_element_by_type(ElementType.COORDINATE_INFO)
            self.fast_layout_manager.remove_element_by_type(ElementType.SECTOR)
            self.fast_layout_manager.remove_element_by_type(ElementType.MEASUREMENT_LINE)
        
        # 重新绘制设备（应用默认位置）
        self._draw_devices()
        
        # 更新显示
        self.canvas.draw_idle()
        
        # 触发回调
        if self.on_right_click_callback:
            self.on_right_click_callback()
        
        print("✅ 清除所有测量点和扇形，设备信息框已恢复默认位置")
    
    def _reset_device_info_positions(self):
        """
        重置所有设备信息框位置到默认位置
        """
        if not self.devices:
            return
        
        reset_count = 0
        for device in self.devices:
            if device.is_info_position_forced:
                device.reset_info_position_to_default()
                reset_count += 1
        
        if reset_count > 0:
            print(f"🔄 已重置 {reset_count} 个设备信息框到默认位置")
    
    def _on_mouse_move(self, event):
        """
        处理鼠标移动事件 ✨ 交互体验优化 + 标签拖拽
        """
        if event.inaxes != self.axes:
            self.mouse_pos = None
            self._clear_crosshair()
            self._clear_coordinate_info()
            # ✨ 如果正在拖拽，离开axes时停止拖拽
            if self._is_dragging:
                self._end_label_drag()
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            self.mouse_pos = None
            self._clear_crosshair()
            self._clear_coordinate_info()
            return
        
        # ✨ 如果正在拖拽标签，更新标签位置
        if self._is_dragging and self._dragging_label is not None:
            self._update_label_drag(x, y)
            return
        
        # ✨ 检查是否悬停在标签上，改变光标
        hovered_label = self._find_label_at(x, y)
        if hovered_label is not None:
            self._set_cursor('hand')
        else:
            self._set_cursor('arrow')
        
        # 检查是否在坐标范围内
        x_range, y_range = self.current_range
        if -x_range <= x <= x_range and -y_range <= y <= y_range:
            # 只有当鼠标位置真正改变时才更新（减少不必要的重绘）✨ 性能优化
            threshold = 0.05  # 增大阈值，减少高频更新
            if not self.mouse_pos or (abs(x - self.mouse_pos[0]) > threshold or abs(y - self.mouse_pos[1]) > threshold):
                self.mouse_pos = (x, y)
                self._draw_crosshair()
                # 移除“随光标出现的坐标信息框”（世界/用户坐标系都不再显示）
                self._clear_coordinate_info()
                
                # 统一重绘（批量处理，提升性能）✨ 性能优化
                self.canvas.draw_idle()
                
                # 触发回调
                if self.on_mouse_move_callback:
                    self.on_mouse_move_callback(x, y)
        else:
            if self.mouse_pos:  # 只有当之前有位置时才清除
                self.mouse_pos = None
                self._clear_crosshair()
                self._clear_coordinate_info()  # ✨ 第五步新增功能
                # 统一重绘
                self.canvas.draw_idle()
    
    def _on_mouse_leave(self, event):
        """
        处理鼠标离开事件
        """
        self.mouse_pos = None
        self._clear_crosshair()
        self._clear_coordinate_info()  # ✨ 第五步新增功能
    
    def _draw_crosshair(self):
        """
        绘制十字光标 ✨ 性能优化：减少重复操作和批量重绘
        """
        if not self.mouse_pos:
            return
        
        # 清除之前的十字光标
        self._clear_crosshair()
        
        x, y = self.mouse_pos
        
        # 绘制垂直线和水平线（精简样式，提升性能）
        vline = self.axes.axvline(x=x, color=self.COLORS['crosshair'], 
                                 linewidth=0.8, alpha=0.6, zorder=1)
        hline = self.axes.axhline(y=y, color=self.COLORS['crosshair'], 
                                 linewidth=0.8, alpha=0.6, zorder=1)
        
        self.crosshair_artists.extend([vline, hline])
        
        # 延迟重绘，由调用者统一控制（减少重绘频率）
        # self.canvas.draw_idle() 移至 _on_mouse_move 中统一处理
    
    def _clear_crosshair(self):
        """
        清除十字光标 ✨ 性能优化：减少不必要的重绘
        """
        if not self.crosshair_artists:
            return  # 没有需要清除的对象，避免无用操作
        
        for artist in self.crosshair_artists:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass  # 如果对象已被移除或无效，忽略错误
        self.crosshair_artists.clear()
        # 注意：不在这里调用draw_idle()，由调用者统一控制重绘时机
    
    def _draw_devices(self):
        """
        绘制所有设备点（设备标签使用固定4方向规则：左/上/右/下）
        
        改进（V2.3）：
        - 设备点使用5x5实心方块
        - 添加短虚线引导线连接标签和设备点（线宽1px）
        - 设备标签使用4方向规则（左、上、右、下），默认优先左侧
          且“靠近设备一侧的标签边中点”与设备点在对应轴方向相距1个坐标单位
        - 标签采用多行格式，字体加粗
        - 支持设备自定义颜色
        """
        # 清除之前的设备图形
        self._clear_devices()

        if not self.devices:
            self.canvas.draw_idle()
            return

        # ✨ 使用高性能原生布局算法创建设备标签（12方向约束版）
        for device in self.devices:
            # 获取设备颜色（如果有color属性则使用，否则使用默认红色）
            device_color = getattr(device, 'color', self.COLORS['device_point'])
            
            # 绘制设备点：使用7x7正方形标记(marker='s')
            point = self.axes.scatter([device.x], [device.y], 
                                     c=device_color, 
                                     s=49,  # 控制正方形大小，约为7x7像素效果
                                     marker='s',  # 's'表示正方形
                                     zorder=5, alpha=1.0,
                                     edgecolors='white', linewidth=0.5)
            self.device_artists.append(point)
            
            # ✨ 多行格式标签文本（设备名 + X坐标 + Y坐标）
            label_text = f'{device.name}\nX: {device.x:.3f}\nY: {device.y:.3f}'
            
            # 使用固定4方向规则计算标签中心位置
            text_x, text_y, _ = self._calculate_device_label_position_4dir(device.x, device.y)
            
            # ✨ 短虚线引导线连接设备点和标签（线宽1px，短虚线样式）
            guide_line = self.axes.plot(
                [device.x, text_x], [device.y, text_y],
                color=device_color,
                linewidth=1.0,  # 1像素线宽
                linestyle=(0, (3, 2)),  # 短虚线样式：3px实线 + 2px空白
                alpha=0.6,
                zorder=4  # 在设备点和标签之下
            )[0]
            self.device_artists.append(guide_line)
            
            # ✨ 创建文本对象（加粗字体、多行格式）
            text = self.axes.text(
                text_x, text_y,
                label_text,
                bbox=dict(
                    boxstyle='round,pad=0.4',  # 稍微增加内边距
                    facecolor='#ffffe0',  # 浅黄色背景
                    edgecolor=device_color,  # 使用设备颜色作为边框色
                    linewidth=0.75,  # 边框线宽减半，避免过于抢眼
                    alpha=0.95
                ),
                fontsize=9,
                fontweight='bold',  # ✨ 加粗字体
                color=device_color,  # 使用设备颜色作为文字色
                zorder=6,
                ha='center', 
                va='center'
            )
            
            # 添加到艺术家列表和文本对象列表
            self.device_artists.append(text)
            self.text_objects.append(text)
        
        # 更新显示
        self.canvas.draw_idle()
    
    def _draw_measurement(self):
        """
        绘制测量点和测量线 ✨ 支持双坐标系模式，使用高性能布局
        """
        if not self.measurement_point:
            return
        
        # 清除之前的测量图形
        self._clear_measurement()
        
        x, y = self.measurement_point.x, self.measurement_point.y
        
        # 绘制测量点：直径约为6的圆点（Matplotlib中markersize为“直径（points）”）
        point = self.axes.plot(x, y, 'o', 
                             color=self.COLORS['measurement_point'], 
                             markersize=6, zorder=7)[0]
        self.measurement_artists.append(point)
        
        # 根据坐标系模式绘制不同的连线 ✨ 动态交互模式
        if self.user_coord_enabled and self.user_position:
            # 用户坐标系模式：绘制到用户位置的连线
            ux, uy = self.user_position
            line = self.axes.plot([ux, x], [uy, y], 
                                color=self.COLORS['user_marker'], 
                                linewidth=2, alpha=0.8, zorder=4, 
                                linestyle='--')[0]  # 虚线表示用户坐标系
            self.measurement_artists.append(line)
            
            # 使用用户坐标系信息
            info_lines = self.measurement_point.get_info_lines(3, use_reference=True)
            coord_mode = "用户坐标系"
        else:
            # 世界坐标系模式：绘制到原点的连线
            line = self.axes.plot([0, x], [0, y], 
                                color=self.COLORS['measurement_line'], 
                                linewidth=2, alpha=0.7, zorder=4)[0]
            self.measurement_artists.append(line)
            
            # 使用世界坐标系信息
            info_lines = self.measurement_point.get_info_lines(3, use_reference=False)
            coord_mode = "世界坐标系"
        
        # 添加坐标系模式标识到信息中
        info_text = f"[{coord_mode}]\n" + '\n'.join(info_lines)
        
        # 坐标标签默认位置：在单击标记点正下方，下移2格（2个坐标单位）
        # 说明：此处采用“默认固定位置 + 轻量边界约束”，不再做自动避让，以符合交互预期
        text_x = x
        text_y = y - 2.0
        
        # 边界约束：避免标签超出画布（留0.5单位安全边距）
        x_range, y_range = self.current_range
        margin = 0.5
        text_x = max(-x_range + margin, min(text_x, x_range - margin))
        text_y = max(-y_range + margin, min(text_y, y_range - margin))
        
        # 创建测量信息框
        text = self.axes.text(
            text_x, text_y,
            info_text,
            bbox=dict(
                boxstyle='round,pad=0.5', 
                # 标签底色：透明度60%（覆盖度0.6）
                facecolor=(1.0, 1.0, 1.0, 0.6),
                edgecolor=self.COLORS['label_border'],
                linewidth=1.5
            ),
            # 字体/字号：与设备标签说明文字一致
            fontsize=9,
            fontweight='bold',
            color=self.COLORS['text_color'],
            zorder=8,
            ha='center', 
            va='center'
        )
        
        # 添加到艺术家列表和文本对象列表
        self.measurement_artists.append(text)
        self.text_objects.append(text)
        
        # 应用智能避让（重新处理所有文本）
        if len(self.text_objects) > 0:
            self._apply_smart_text_adjustment()
        
        # 更新显示
        self.canvas.draw_idle()
    
    def _draw_sector(self):
        """
        绘制90度扇形：以连线为平分线向两侧各45度 ✨ 根据坐标系状态选择中心点
        """
        if not self.sector_point:
            return
        
        # 清除之前的扇形
        self._clear_sector()
        
        x, y = self.sector_point
        
        # 根据坐标系模式选择扇形中心点 ✨ 动态交互模式
        if self.user_coord_enabled and self.user_position:
            # 用户坐标系模式：以用户位置为中心
            center_x, center_y = self.user_position
            print(f"🔺 用户坐标系模式 - 扇形中心: {self.user_position}")
        else:
            # 世界坐标系模式：以原点为中心
            center_x, center_y = 0.0, 0.0
            print(f"🔺 世界坐标系模式 - 扇形中心: (0, 0)")
        
        # 计算半径 (点击点到中心点的距离)
        radius = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        if radius < 0.01:  # 避免在中心点绘制
            return
        
        # 计算中心角度 (点击点相对于中心点的角度)
        center_angle_rad = math.atan2(y - center_y, x - center_x)
        center_angle_deg = math.degrees(center_angle_rad)
        
        # 90度扇形：以连线为平分线，向两侧各45度
        # 起始角度 = 中心角度 - 45度，结束角度 = 中心角度 + 45度
        start_angle_deg = center_angle_deg - 45
        end_angle_deg = center_angle_deg + 45
        
        # 创建扇形路径（以动态中心点为基准）
        theta = np.linspace(math.radians(start_angle_deg), 
                           math.radians(end_angle_deg), 50)
        x_sector = center_x + radius * np.cos(theta)
        y_sector = center_y + radius * np.sin(theta)
        
        # 添加中心点到扇形路径
        x_coords = np.concatenate([[center_x], x_sector, [center_x]])
        y_coords = np.concatenate([[center_y], y_sector, [center_y]])
        
        # 绘制填充扇形
        sector_fill = self.axes.fill(x_coords, y_coords, 
                                   color=self.COLORS['sector_fill'], 
                                   alpha=0.3, zorder=2)[0]
        self.sector_artists.append(sector_fill)
        
        # 绘制扇形边界
        sector_edge = self.axes.plot(x_coords, y_coords, 
                                   color=self.COLORS['sector_edge'], 
                                   linewidth=2, zorder=3)[0]
        self.sector_artists.append(sector_edge)
        
        # 🆕 注册扇形斥力场到布局管理器（增强版V2.0）
        if self.fast_layout_manager:
            # 计算扇形的近似边界框（用于元素碰撞检测）
            margin = 0.5
            sector_bbox = BoundingBox(
                center_x - radius - margin,
                center_y - radius - margin, 
                center_x + radius + margin,
                center_y + radius + margin
            )
            
            # 创建扇形布局元素
            sector_element = LayoutElement(
                ElementType.SECTOR, sector_bbox, (center_x, center_y),
                priority=2, movable=False, element_id="sector", static=True
            )
            self.fast_layout_manager.add_element(sector_element)
            
            # 🆕 注册扇形斥力场（精确的扇形区域，用于标签避让）
            self.fast_layout_manager.add_sector_region(
                center_x, center_y, radius,
                start_angle_deg, end_angle_deg
            )
        
        # 更新显示
        self.canvas.draw_idle()
        
        print(f"✅ 绘制扇形: 半径={radius:.3f}, 中心角度={center_angle_deg:.1f}°")
    
    def _clear_devices(self):
        """
        清除设备图形
        """
        for artist in self.device_artists:
            try:
                artist.remove()
                # 同时从文本对象列表中移除
                if artist in self.text_objects:
                    self.text_objects.remove(artist)
            except (ValueError, AttributeError):
                pass  # 可能已经被移除或无效
        self.device_artists.clear()
        
        # 清除布局管理器中的设备元素（保留备用）
        if self.fast_layout_manager:
            self.fast_layout_manager.remove_element_by_type(ElementType.DEVICE_INFO)
    
    def _clear_measurement(self):
        """
        清除测量图形
        """
        for artist in self.measurement_artists:
            try:
                artist.remove()
                # 同时从文本对象列表中移除
                if artist in self.text_objects:
                    self.text_objects.remove(artist)
            except (ValueError, AttributeError):
                pass  # 可能已经被移除或无效
        self.measurement_artists.clear()
        
        # 清除布局管理器中的测量元素（保留备用）
        if self.fast_layout_manager:
            self.fast_layout_manager.remove_element_by_type(ElementType.MEASUREMENT_INFO)
    
    def _clear_sector(self):
        """
        清除扇形图形
        """
        for artist in self.sector_artists:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass  # 可能已经被移除或无效
        self.sector_artists.clear()
        
        # 清除布局管理器中的扇形元素
        if self.fast_layout_manager:
            self.fast_layout_manager.remove_element_by_type(ElementType.SECTOR)
            # 🆕 清除扇形斥力场
            self.fast_layout_manager.clear_sector_regions()
    
    def set_coordinate_range(self, x_range: float, y_range: float):
        """
        设置坐标显示范围
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
        """
        try:
            # 清除所有绘制对象
            self.axes.clear()
            
            # axes.clear() 已经移除了所有 artist，直接清空引用列表即可
            # 不要调用各个 _clear_xxx 方法，因为它们会尝试 remove 已经被清除的对象
            self.device_artists.clear()
            self.measurement_artists.clear()
            self.sector_artists.clear()
            self.crosshair_artists.clear()
            self.user_position_artists.clear()
            self.coordinate_info_artists.clear()
            self.text_objects.clear()
            self.obstacle_objects.clear()
            
            # 重新初始化布局管理器
            self._init_fast_layout_manager()
            
            # 重新设置坐标系统
            self._setup_coordinate_system(x_range, y_range)
            
            # 重新绘制所有内容
            self._draw_devices()
            if self.measurement_point:
                self._draw_measurement()
            if self.sector_point:
                self._draw_sector()
            
            # 重新绘制用户坐标系（如果启用）
            if self.user_coord_enabled:
                self._draw_user_coordinate_overlay()
                if self.user_position:
                    self._draw_user_position_marker()
                    self._draw_user_coordinate_axes()
            
            print(f"✅ 坐标范围已更新: ±{x_range} x ±{y_range}")
            
        except Exception as e:
            print(f"❌ 更新坐标范围失败: {e}")
    
    def export_to_png(self, file_path: str, dpi: int = 300) -> bool:
        """
        导出为高清PNG图片
        
        Args:
            file_path: 保存路径
            dpi: 分辨率，默认300DPI
            
        Returns:
            True如果导出成功，否则False
        """
        try:
            # 临时设置高DPI
            original_dpi = self.figure.get_dpi()
            self.figure.set_dpi(dpi)
            
            # 保存图片
            self.figure.savefig(file_path, dpi=dpi, bbox_inches='tight', 
                              facecolor=self.COLORS['background'],
                              edgecolor='none', format='png')
            
            # 恢复原DPI
            self.figure.set_dpi(original_dpi)
            
            print(f"✅ PNG导出成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ PNG导出失败: {e}")
            return False
    
    def clear_all(self):
        """
        清除所有内容
        """
        self.devices.clear()
        self.measurement_point = None
        self.sector_point = None
        
        # 清除adjustText相关对象
        self._clear_text_objects()
        
        # 清除所有图形
        self._clear_devices()
        self._clear_measurement()
        self._clear_sector()
        self._clear_crosshair()
        self._clear_coordinate_info()  # 清除坐标信息显示 ✨ 第五步新增功能
        # 注意：不清除用户坐标系，让用户手动控制
        
        # 重新绘制基础坐标系
        self._setup_coordinate_system(*self.current_range)
        
        # 重新绘制用户坐标系（如果启用）
        if self.user_coord_enabled:
            self._draw_user_coordinate_overlay()
            if self.user_position:
                self._draw_user_position_marker()
                self._draw_user_coordinate_axes()
        
        # 更新显示
        self.canvas.draw_idle()
        
        print("✅ 已清除所有内容")
    
    # === 设置回调函数的方法 ===
    
    def set_click_callback(self, callback: Callable[[float, float], None]):
        """设置左键单击回调函数"""
        self.on_click_callback = callback
    
    def set_right_click_callback(self, callback: Callable[[], None]):
        """设置右键单击回调函数"""
        self.on_right_click_callback = callback
    
    def set_mouse_move_callback(self, callback: Callable[[float, float], None]):
        """设置鼠标移动回调函数"""
        self.on_mouse_move_callback = callback
    
    def set_double_click_callback(self, callback: Callable[[float, float], None]):
        """设置左键双击回调函数"""
        self.on_double_click_callback = callback
    
    # === 数据接口方法 ===
    
    def update_devices(self, devices: List[Device]):
        """
        更新设备列表并重新绘制
        
        Args:
            devices: 新的设备列表
        """
        self.devices = devices.copy()
        self._draw_devices()
    
    def get_devices(self) -> List[Device]:
        """获取所有设备列表"""
        return self.devices.copy()
    
    def get_measurement_point(self) -> Optional[MeasurementPoint]:
        """获取当前测量点"""
        return self.measurement_point
    
    def get_current_range(self) -> Tuple[float, float]:
        """获取当前坐标范围"""
        return self.current_range

    # === 设备标签4方向默认布局规则 ===
    
    def _calculate_device_label_position_4dir(self, anchor_x: float, anchor_y: float) -> Tuple[float, float, str]:
        """
        计算设备标签的默认位置（4方向规则）
        
        规则说明（以设备点 (anchor_x, anchor_y) 为参考）：
        - 左侧：标签矩形“右边缘中点”的坐标为 (anchor_x - 1, anchor_y)
        - 上侧：标签矩形“下边缘中点”的坐标为 (anchor_x, anchor_y + 1)
        - 右侧：标签矩形“左边缘中点”的坐标为 (anchor_x + 1, anchor_y)
        - 下侧：标签矩形“上边缘中点”的坐标为 (anchor_x, anchor_y - 1)
        
        即标签靠近设备一侧的边中点与设备点在对应轴方向相距1个坐标单位。
        方向优先级：左 -> 上 -> 右 -> 下，只在越界时才尝试下一方向。
        """
        # 获取标签尺寸：优先使用布局管理器中的配置
        if self.fast_layout_manager:
            label_width, label_height = self.fast_layout_manager.info_box_sizes.get(
                ElementType.DEVICE_INFO, (2.0, 1.2)
            )
        else:
            label_width, label_height = (2.0, 1.2)
        
        # 当前坐标范围（对称: ±x_range, ±y_range）
        x_range, y_range = self.current_range
        
        # 四个候选中心位置（左/上/右/下）
        candidates = [
            # 左侧：标签右边缘中点 (anchor_x - 1, anchor_y)
            (
                'left',
                anchor_x - 1.0 - label_width / 2.0,
                anchor_y
            ),
            # 上侧：标签下边缘中点 (anchor_x, anchor_y + 1)
            (
                'top',
                anchor_x,
                anchor_y + 1.0 + label_height / 2.0
            ),
            # 右侧：标签左边缘中点 (anchor_x + 1, anchor_y)
            (
                'right',
                anchor_x + 1.0 + label_width / 2.0,
                anchor_y
            ),
            # 下侧：标签上边缘中点 (anchor_x, anchor_y - 1)
            (
                'bottom',
                anchor_x,
                anchor_y - 1.0 - label_height / 2.0
            ),
        ]
        
        # 内部函数：检查候选中心是否在画布范围内（留0.5单位安全边距）
        def _within_bounds(cx: float, cy: float) -> bool:
            left = cx - label_width / 2.0
            right = cx + label_width / 2.0
            top = cy + label_height / 2.0
            bottom = cy - label_height / 2.0
            margin = 0.5
            return (
                left >= -x_range + margin and
                right <= x_range - margin and
                bottom >= -y_range + margin and
                top <= y_range - margin
            )
        
        # 按优先级依次尝试候选位置
        for direction, cx, cy in candidates:
            if _within_bounds(cx, cy):
                return cx, cy, direction
        
        # 如果所有方向都越界，则退回到左侧候选（即便可能超出边界）
        direction, cx, cy = candidates[0]
        return cx, cy, direction

    # === 用户坐标系功能 ✨ 双坐标系核心功能 ===
    
    def set_user_coordinate_mode(self, enabled: bool):
        """
        设置用户坐标系模式 ✨ 支持动态交互模式切换
        
        Args:
            enabled: True启用用户坐标系，False使用世界坐标系
        """
        self.user_coord_enabled = enabled
        print(f"✨ 视图设置用户坐标系模式: {'启用' if enabled else '关闭'}")
        
        if enabled:
            self._draw_user_coordinate_overlay()
        else:
            self._clear_user_coordinate_overlay()
        
        # 更新现有测量点的参考系统 ✨ 动态交互模式
        self._update_measurement_reference()
        
        self.canvas.draw_idle()
    
    def _update_measurement_reference(self):
        """
        根据当前坐标系状态更新测量点的参考点 ✨ 动态交互模式核心方法
        """
        if self.measurement_point:
            # 确定新的参考点
            if self.user_coord_enabled and self.user_position:
                new_reference = self.user_position
            else:
                new_reference = (0.0, 0.0)
            
            # 更新测量点的参考点
            self.measurement_point.reference_point = new_reference
            
            # 重新计算双坐标系属性
            self.measurement_point.distance_to_reference = self.measurement_point._calculate_distance_to_reference()
            self.measurement_point.angle_to_reference_axis = self.measurement_point._calculate_min_angle_to_reference_axis()
            
            # 重新绘制测量线和信息
            self._draw_measurement()
            
            print(f"✓ 测量点参考系统已更新: {new_reference}")
    
    def set_user_position(self, x: float, y: float):
        """
        设置用户位置 ✨ 自动更新测量点参考系统
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
        """
        old_position = self.user_position
        
        # 先做一次格式化输出，确保x/y是可用数值；也避免非法输入导致状态被提前改动
        print(f"✨ 视图设置用户位置: ({x:.3f}, {y:.3f})")
        
        # ✨ V2.4 如果已锁定扇形且“参考中心”发生变化，自动解锁
        # 关键修复点：
        # - 当锁定扇形在世界坐标系下创建（中心点为(0,0)）后，用户首次启用用户坐标系并从None设置用户位置时
        #   参考中心会从(0,0)切换到用户位置；若不解锁，后续对比虚线仍会使用旧中心点，导致角度/距离错误。
        old_reference = old_position if (self.user_coord_enabled and old_position is not None) else (0.0, 0.0)
        new_reference = (x, y) if self.user_coord_enabled else (0.0, 0.0)
        if self.locked_measurement.is_locked and old_reference != new_reference:
            self.unlock_on_user_coord_change()
        
        self.user_position = (x, y)
        
        if self.user_coord_enabled:
            # 先清除之前的用户位置相关元素（标记和轴线）
            self._clear_user_position_marker()
            # 然后绘制新的用户位置标记和轴线
            self._draw_user_position_marker()
            self._draw_user_coordinate_axes()
            
            # 更新现有测量点的参考系统 ✨ 动态交互模式
            self._update_measurement_reference()
        
        self.canvas.draw_idle()
    
    def clear_user_position(self):
        """清除用户位置"""
        self.user_position = None
        self._clear_user_position_elements()
        self.canvas.draw_idle()
    
    def _draw_user_coordinate_overlay(self):
        """绘制用户坐标系叠加层（精致的浅紫色网格）"""
        if not self.user_coord_enabled:
            return
        
        # 清除之前的用户坐标系元素
        self._clear_user_coordinate_overlay()
        
        # 绘制精致的半透明紫色网格叠加层
        x_range, y_range = self.current_range
        x_ticks = np.arange(-int(x_range), int(x_range) + 1, 1)
        y_ticks = np.arange(-int(y_range), int(y_range) + 1, 1)
        
        # 主网格线（较粗，用于主要刻度）
        for x in x_ticks[::2]:  # 每2个单位绘制一条主网格线
            line = self.axes.axvline(x=x, color=self.COLORS['user_grid'], 
                                   linewidth=1.5, linestyle='-', alpha=0.4, zorder=1)
            self.user_position_artists.append(line)
        
        for y in y_ticks[::2]:  # 每2个单位绘制一条主网格线
            line = self.axes.axhline(y=y, color=self.COLORS['user_grid'], 
                                   linewidth=1.5, linestyle='-', alpha=0.4, zorder=1)
            self.user_position_artists.append(line)
        
        # 次网格线（较细，用于细分刻度）
        for x in x_ticks[1::2]:  # 奇数位置的次网格线
            line = self.axes.axvline(x=x, color=self.COLORS['user_grid'], 
                                   linewidth=0.8, linestyle=':', alpha=0.25, zorder=0.5)
            self.user_position_artists.append(line)
        
        for y in y_ticks[1::2]:  # 奇数位置的次网格线
            line = self.axes.axhline(y=y, color=self.COLORS['user_grid'], 
                                   linewidth=0.8, linestyle=':', alpha=0.25, zorder=0.5)
            self.user_position_artists.append(line)
        
        print("✨ 绘制用户坐标系网格叠加层")
    
    def _draw_user_position_marker(self):
        """绘制用户位置标记（紫色人形图标）"""
        if not self.user_position:
            return
        
        x, y = self.user_position
        
        # 绘制用户位置标记：正五边形（边长约4像素）
        # 正五边形外接圆半径约0.2个坐标单位，确保边长视觉效果约4像素
        pentagon = patches.RegularPolygon(
            (x, y), numVertices=5, radius=0.2,
            facecolor=self.COLORS['user_marker'],  # 紫色填充
            edgecolor='white',  # 白色边框
            linewidth=2, 
            zorder=15, 
            alpha=1.0,
            label='用户位置'
        )
        self.axes.add_patch(pentagon)
        self.user_position_artists.append(pentagon)
        
        # 用户坐标系“原点标签”：固定显示在用户坐标点正下方2格（不随动）
        # 说明：
        # - “不随动”包含：不参与智能避让/自动布局，不做边界挪动
        # - 位置严格采用 (x, y-2.0)，以满足需求“正下方2格”
        label_text = f'[用户] 位置\n({x:.1f}, {y:.1f})'
        text_x = x
        text_y = y - 2.0
        
        # 创建文本对象
        text = self.axes.text(
            text_x, text_y,
            label_text, 
            # 字体/字号：与设备标签说明文字一致
            fontsize=9, 
            fontweight='bold',
            color=self.COLORS['user_text'],
            ha='center', 
            va='center', 
            zorder=17,
            bbox=dict(
                boxstyle="round,pad=0.5",
                # 背景：60%透明度
                facecolor=(1.0, 1.0, 1.0, 0.6),
                edgecolor=self.COLORS['user_axis'],
                linewidth=1.5
            )
        )
        
        # 添加到艺术家列表
        self.user_position_artists.append(text)
        # 注意：用户原点标签不加入 self.text_objects，也不参与智能避让，
        # 否则会导致位置“随动/漂移”，违背“固定在正下方2格”的需求
        
        print(f"✨ 绘制用户位置标记: ({x:.3f}, {y:.3f})")
    
    def _draw_user_coordinate_axes(self):
        """绘制用户坐标系轴线（红色虚线）"""
        if not self.user_position:
            return
        
        x, y = self.user_position
        x_range, y_range = self.current_range
        
        # 绘制用户坐标系的精致虚线轴
        # 主轴线（线宽下降一半）
        h_line_main = self.axes.axhline(y=y, color=self.COLORS['user_axis'], 
                                      linewidth=0.75, linestyle='--', alpha=0.85, zorder=6)
        v_line_main = self.axes.axvline(x=x, color=self.COLORS['user_axis'], 
                                      linewidth=0.75, linestyle='--', alpha=0.85, zorder=6)
        
        # 辅助轴线（线宽下降一半，浅红色增强层次）
        h_line_aux = self.axes.axhline(y=y, color=self.COLORS['user_axis'], 
                                     linewidth=0.25, linestyle='--', alpha=0.35, zorder=5)
        v_line_aux = self.axes.axvline(x=x, color=self.COLORS['user_axis'], 
                                     linewidth=0.25, linestyle='--', alpha=0.35, zorder=5)
        
        self.user_position_artists.extend([h_line_main, v_line_main, h_line_aux, v_line_aux])
        
        # 在轴线上添加箭头标识（可选）
        # X轴正向箭头
        if x + 1 <= x_range:
            x_arrow = self.axes.annotate('', xy=(x + 0.8, y), xytext=(x + 0.2, y),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=self.COLORS['user_axis'],
                                                     lw=1, alpha=0.7),
                                       zorder=7)
            self.user_position_artists.append(x_arrow)
        
        # Y轴正向箭头
        if y + 1 <= y_range:
            y_arrow = self.axes.annotate('', xy=(x, y + 0.8), xytext=(x, y + 0.2),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=self.COLORS['user_axis'],
                                                     lw=1, alpha=0.7),
                                       zorder=7)
            self.user_position_artists.append(y_arrow)
        
        print(f"✨ 绘制用户坐标系轴线: 中心({x:.3f}, {y:.3f})")
    
    def _clear_user_coordinate_overlay(self):
        """清除用户坐标系叠加层"""
        for artist in self.user_position_artists:
            try:
                artist.remove()
                # 同时从文本对象列表中移除
                if artist in self.text_objects:
                    self.text_objects.remove(artist)
            except (ValueError, AttributeError):
                pass  # 如果对象已被移除或无效，忽略错误
        self.user_position_artists.clear()
        
        # 清除布局管理器中的用户位置元素（保留备用）
        if self.fast_layout_manager:
            self.fast_layout_manager.remove_element_by_type(ElementType.USER_POSITION)
        
        print("✨ 清除用户坐标系叠加层")
    
    def _clear_user_position_marker(self):
        """清除用户位置标记和轴线，但保留网格"""
        # 清除用户位置标记、轴线，但保留网格
        artists_to_remove = []
        for artist in self.user_position_artists:
            try:
                # 检查是否是scatter、text或者轴线对象（不是网格线）
                is_marker_or_text = hasattr(artist, 'get_offsets') or hasattr(artist, 'get_text')
                is_axis_line = (hasattr(artist, 'get_linestyle') and 
                               artist.get_linestyle() == '--')  # 虚线轴线
                
                if is_marker_or_text or is_axis_line:
                    artist.remove()
                    artists_to_remove.append(artist)
            except (ValueError, AttributeError):
                # 如果对象已被移除或属性无效，将其标记为需要从列表移除
                artists_to_remove.append(artist)
        
        # 从列表中移除已删除的对象
        for artist in artists_to_remove:
            if artist in self.user_position_artists:
                self.user_position_artists.remove(artist)
    
    def _clear_user_position_elements(self):
        """清除所有用户位置相关元素"""
        self._clear_user_coordinate_overlay()
        print("✨ 清除所有用户位置元素")
    
    # === 坐标信息显示功能 ✨ 第五步新增功能 ===
    
    def _draw_coordinate_info(self, x: float, y: float):
        """
        绘制鼠标悬停时的坐标信息（支持双坐标系显示）
        
        Args:
            x: 当前鼠标X坐标
            y: 当前鼠标Y坐标
        """
        # 交互调整：不再显示任何“随动坐标信息框”（世界/用户坐标系都关闭）
        # 清除可能残留的对象
        self._clear_coordinate_info()
        return
    
    def _clear_coordinate_info(self):
        """
        清除坐标信息显示
        """
        for artist in self.coordinate_info_artists:
            try:
                if artist.axes == self.axes:
                    artist.remove()
            except (ValueError, AttributeError):
                pass  # 如果对象已被移除或无效，忽略错误
        self.coordinate_info_artists.clear()
        self.canvas.draw_idle()
    
    # ==================== 标签拖拽功能 ✨ ====================
    
    def _on_mouse_release(self, event):
        """
        处理鼠标释放事件 - 结束标签拖拽
        """
        if self._is_dragging:
            self._end_label_drag()
    
    def _find_label_at(self, x: float, y: float) -> Optional[any]:
        """
        查找指定坐标位置的标签
        
        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标
            
        Returns:
            找到的标签对象，如果没有则返回None
        """
        # 遍历所有文本对象，检查是否包含该点
        for text_obj in self.text_objects:
            try:
                # 获取文本的边界框（数据坐标）
                bbox = text_obj.get_window_extent(self.canvas.get_renderer())
                # 转换为数据坐标
                bbox_data = bbox.transformed(self.axes.transData.inverted())
                
                # 检查点是否在边界框内
                if (bbox_data.x0 <= x <= bbox_data.x1 and 
                    bbox_data.y0 <= y <= bbox_data.y1):
                    return text_obj
            except Exception as e:
                # 如果获取边界框失败，跳过该对象
                continue
        
        return None
    
    def _start_label_drag(self, label: any, x: float, y: float):
        """
        开始拖拽标签
        
        Args:
            label: 要拖拽的标签对象
            x: 起始X坐标
            y: 起始Y坐标
        """
        self._dragging_label = label
        self._drag_start_pos = (x, y)
        self._label_original_pos = label.get_position()
        self._is_dragging = True
        
        # 改变光标为移动光标
        self._set_cursor('fleur')
        
        # 高亮显示正在拖拽的标签
        label.set_bbox(dict(
            boxstyle='round,pad=0.3',
            facecolor='#e3f2fd',  # 浅蓝色高亮
            edgecolor='#1976d2',  # 蓝色边框
            alpha=0.95,
            linewidth=2
        ))
        
        self.canvas.draw_idle()
        print(f"🎯 开始拖拽标签: {label.get_text()[:20]}...")
    
    def _update_label_drag(self, x: float, y: float):
        """
        更新拖拽中的标签位置
        
        Args:
            x: 当前鼠标X坐标
            y: 当前鼠标Y坐标
        """
        if not self._is_dragging or self._dragging_label is None:
            return
        
        # 计算偏移量
        dx = x - self._drag_start_pos[0]
        dy = y - self._drag_start_pos[1]
        
        # 计算新位置
        new_x = self._label_original_pos[0] + dx
        new_y = self._label_original_pos[1] + dy
        
        # 限制在坐标范围内
        x_range, y_range = self.current_range
        margin = 0.5
        new_x = max(-x_range + margin, min(new_x, x_range - margin))
        new_y = max(-y_range + margin, min(new_y, y_range - margin))
        
        # 更新标签位置
        self._dragging_label.set_position((new_x, new_y))
        
        # 更新引导线（如果有）
        self._update_guide_line_for_label(self._dragging_label, new_x, new_y)
        
        self.canvas.draw_idle()
    
    def _update_guide_line_for_label(self, label: any, new_x: float, new_y: float):
        """
        更新标签对应的引导线
        
        Args:
            label: 标签对象
            new_x: 标签新X坐标
            new_y: 标签新Y坐标
        """
        # 查找与此标签关联的设备
        label_text = label.get_text()
        
        for i, device in enumerate(self.devices):
            if device.name in label_text:
                # 找到对应的引导线并更新
                # 引导线在device_artists中，紧跟在scatter点之后
                guide_line_idx = i * 3 + 1  # scatter点、引导线、text
                if guide_line_idx < len(self.device_artists):
                    guide_line = self.device_artists[guide_line_idx]
                    if hasattr(guide_line, 'set_data'):
                        guide_line.set_data([device.x, new_x], [device.y, new_y])
                break
    
    def _end_label_drag(self):
        """
        结束标签拖拽
        """
        if not self._is_dragging or self._dragging_label is None:
            return
        
        # 恢复标签样式
        label_text = self._dragging_label.get_text()
        
        # 根据标签类型恢复样式，但使用蓝色边框标识手动位置
        if '[用户]' in label_text:
            # 用户位置标签
            self._dragging_label.set_bbox(dict(
                boxstyle="round,pad=0.5",
                facecolor='#f8f4ff',
                edgecolor='#1565c0',  # 蓝色边框表示手动位置
                linewidth=2.5,
                alpha=0.95
            ))
        elif '距离:' in label_text and '角度:' in label_text:
            # 测量信息标签
            self._dragging_label.set_bbox(dict(
                boxstyle='round,pad=0.5',
                facecolor=self.COLORS['label_bg'],
                edgecolor='#1565c0',  # 蓝色边框表示手动位置
                alpha=0.9
            ))
        else:
            # 设备标签
            self._dragging_label.set_bbox(dict(
                boxstyle='round,pad=0.3',
                facecolor='#ffffe0',
                edgecolor='#1565c0',  # 蓝色边框表示手动位置
                alpha=0.9
            ))
        
        # 获取最终位置
        final_pos = self._dragging_label.get_position()
        print(f"✅ 标签拖拽完成: 新位置 ({final_pos[0]:.2f}, {final_pos[1]:.2f})")
        
        # 恢复光标
        self._set_cursor('arrow')
        
        # 清理状态
        self._dragging_label = None
        self._drag_start_pos = None
        self._label_original_pos = None
        self._is_dragging = False
        
        self.canvas.draw_idle()
    
    def _reset_label_to_auto(self, label: any):
        """
        重置标签到自动计算的位置
        
        Args:
            label: 要重置的标签对象
        """
        label_text = label.get_text()
        print(f"🔄 重置标签位置: {label_text[:20]}...")
        
        auto_x, auto_y = None, None
        
        # 设备标签：使用4方向规则重新计算默认位置
        device_anchor = None
        for device in self.devices:
            if device.name in label_text:
                device_anchor = (device.x, device.y, device)
                break
        
        if device_anchor is not None:
            anchor_x, anchor_y, device = device_anchor
            auto_x, auto_y, _ = self._calculate_device_label_position_4dir(anchor_x, anchor_y)
        elif '[用户]' in label_text and self.user_position:
            # 用户位置标签：仍然使用高性能布局算法
            anchor_x, anchor_y = self.user_position
            if self.fast_layout_manager:
                auto_x, auto_y = self.fast_layout_manager.calculate_optimal_position(
                    anchor_x, anchor_y, ElementType.USER_POSITION, "user_position"
                )
        elif '距离:' in label_text and self.measurement_point:
            # 测量信息标签：仍然使用高性能布局算法
            anchor_x, anchor_y = self.measurement_point.x, self.measurement_point.y
            if self.fast_layout_manager:
                auto_x, auto_y = self.fast_layout_manager.calculate_optimal_position(
                    anchor_x, anchor_y, ElementType.MEASUREMENT_INFO, "measurement"
                )
        
        # 应用自动位置并更新引导线
        if auto_x is not None and auto_y is not None:
            label.set_position((auto_x, auto_y))
            self._update_guide_line_for_label(label, auto_x, auto_y)
        
        # 恢复原始样式（移除蓝色边框）
        if '[用户]' in label_text:
            label.set_bbox(dict(
                boxstyle="round,pad=0.5",
                facecolor='#f8f4ff',
                edgecolor=self.COLORS['user_marker'],
                linewidth=2.5,
                alpha=0.95
            ))
        elif '距离:' in label_text:
            label.set_bbox(dict(
                boxstyle='round,pad=0.5',
                facecolor=self.COLORS['label_bg'],
                edgecolor=self.COLORS['label_border'],
                alpha=0.9
            ))
        else:
            label.set_bbox(dict(
                boxstyle='round,pad=0.3',
                facecolor='#ffffe0',
                edgecolor=self.COLORS['device_point'],
                alpha=0.9
            ))
        
        self.canvas.draw_idle()
        print(f"✅ 标签已重置到自动位置")
    
    def _set_cursor(self, cursor_type: str):
        """
        设置鼠标光标样式
        
        Args:
            cursor_type: 光标类型 ('arrow', 'hand', 'fleur', 'crosshair')
        """
        cursor_map = {
            'arrow': '',      # 默认箭头
            'hand': 'hand2',  # 手形光标
            'fleur': 'fleur', # 移动光标（十字箭头）
            'crosshair': 'crosshair'  # 十字准星
        }
        
        cursor_name = cursor_map.get(cursor_type, '')
        
        try:
            self.canvas.get_tk_widget().config(cursor=cursor_name)
        except Exception:
            pass  # 如果设置光标失败，忽略 
    
    # ==================== V2.4 锁定扇形功能 - 图钉和对比 ====================
    
    def _is_click_on_pin(self, x: float, y: float) -> bool:
        """
        检查是否点击了图钉
        
        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标
            
        Returns:
            True如果点击在图钉上，否则False
        """
        if self.pin_position is None:
            return False
        
        px, py = self.pin_position
        # 扩大点击区域，提高易用性（0.4个坐标单位半径）
        click_radius = 0.4
        distance = math.sqrt((x - px)**2 + (y - py)**2)
        return distance <= click_radius
    
    def _toggle_pin_lock(self):
        """
        切换图钉锁定状态
        """
        new_state = self.locked_measurement.toggle_lock()
        
        if new_state:
            # 刚锁定：改变扇形和线段颜色为蓝色
            self._update_sector_style(locked=True)
            print("🔒 扇形已锁定，单击可绘制对比虚线")
        else:
            # 解锁：恢复红色，清除对比虚线
            self._update_sector_style(locked=False)
            self._clear_comparison()
            print("🔓 扇形已解锁")
        
        # 重绘图钉（更新样式）
        if self.pin_position:
            px, py = self.pin_position
            self._draw_pin(px, py)
    
    def _draw_pin(self, x: float, y: float):
        """
        绘制图钉组件
        
        Args:
            x: 图钉X坐标
            y: 图钉Y坐标
        """
        # 清除之前的图钉
        self._clear_pin()
        
        self.pin_position = (x, y)
        is_locked = self.locked_measurement.is_locked
        
        # 图钉背景圆
        bg_color = self.COLORS['pin_bg_locked'] if is_locked else self.COLORS['pin_bg_unlocked']
        edge_color = self.COLORS['pin_locked'] if is_locked else '#888888'
        
        bg_circle = patches.Circle(
            (x, y), radius=0.25,
            facecolor=bg_color,
            edgecolor=edge_color,
            linewidth=2.0 if is_locked else 1.5,
            zorder=25
        )
        self.axes.add_patch(bg_circle)
        self.pin_artists.append(bg_circle)
        
        # 图钉图标（使用简单的符号）
        pin_color = self.COLORS['pin_locked'] if is_locked else '#666666'
        pin_symbol = '●' if is_locked else '○'  # 实心圆表示锁定，空心圆表示解锁
        
        pin_text = self.axes.text(
            x, y, pin_symbol,
            fontsize=14,
            ha='center', va='center',
            zorder=26,
            color=pin_color,
            fontweight='bold'
        )
        self.pin_artists.append(pin_text)
        
        # 添加小三角形指向双击点（图钉的"针"）
        triangle_y = y - 0.35  # 指向下方
        triangle = patches.RegularPolygon(
            (x, triangle_y), numVertices=3, radius=0.12,
            orientation=math.pi,  # 倒三角形
            facecolor=pin_color,
            edgecolor='white',
            linewidth=1,
            zorder=24
        )
        self.axes.add_patch(triangle)
        self.pin_artists.append(triangle)
        
        self.canvas.draw_idle()
    
    def _clear_pin(self):
        """清除图钉组件"""
        for artist in self.pin_artists:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass
        self.pin_artists.clear()
    
    def _update_sector_style(self, locked: bool):
        """
        更新扇形和连线的样式（锁定/解锁时改变颜色）
        
        Args:
            locked: True为锁定样式（蓝色），False为解锁样式（红色）
        """
        if not self.sector_artists:
            return
        
        # 定义颜色
        if locked:
            fill_color = self.COLORS['locked_sector_fill']
            edge_color = self.COLORS['locked_sector_edge']
            line_color = self.COLORS['locked_line']
        else:
            fill_color = self.COLORS['sector_fill']
            edge_color = self.COLORS['sector_edge']
            line_color = self.COLORS['sector_edge']
        
        # 更新扇形填充和边缘颜色
        for artist in self.sector_artists:
            try:
                if hasattr(artist, 'set_facecolor'):
                    artist.set_facecolor(fill_color)
                if hasattr(artist, 'set_edgecolor'):
                    artist.set_edgecolor(edge_color)
                if hasattr(artist, 'set_color'):
                    artist.set_color(edge_color)
                # 锁定时加粗线条
                if hasattr(artist, 'set_linewidth'):
                    artist.set_linewidth(2.5 if locked else 2.0)
            except Exception:
                pass
        
        self.canvas.draw_idle()
    
    def _draw_comparison_line(self, x: float, y: float):
        """
        绘制对比虚线并计算夹角和距离
        
        Args:
            x: 新测量点X坐标
            y: 新测量点Y坐标
        """
        # 清除之前的对比线
        self._clear_comparison()
        
        # 获取锁定的测量数据
        if not self.locked_measurement.has_data():
            return
        
        center = self.locked_measurement.center_point
        
        # 计算对比数据
        comparison = self.locked_measurement.calculate_comparison((x, y))
        angle_diff = comparison['angle_diff']
        new_distance = comparison['new_distance']
        
        # 绘制橙色对比短虚线（图钉锁定后的第二条线段）
        line = self.axes.plot(
            [center[0], x], [center[1], y],
            color=self.COLORS['comparison_line'],
            linewidth=2.0,
            linestyle='--',
            dashes=(3, 2),  # 短虚线：3像素实线，2像素空白（图钉锁定后的第二条线段）
            alpha=0.9,
            zorder=15
        )[0]
        self.comparison_artists.append(line)
        
        # 绘制新测量点标记（小圆点）
        point = self.axes.plot(x, y, 'o',
                              color=self.COLORS['comparison_line'],
                              markersize=8, zorder=16)[0]
        self.comparison_artists.append(point)
        
        # 绘制对比信息框（点击点下方）
        info_text = f"📐 夹角: {angle_diff:.1f}°\n📏 距离: {new_distance:.3f}"
        info_box = self.axes.text(
            x, y - 1.0,  # 点击点下方1个单位
            info_text,
            bbox=dict(
                boxstyle='round,pad=0.4',
                facecolor=self.COLORS['comparison_bg'],
                edgecolor=self.COLORS['comparison_line'],
                linewidth=1.5,
                alpha=0.95
            ),
            fontsize=10,
            fontweight='bold',
            color=self.COLORS['comparison_text'],
            ha='center', va='top',
            zorder=17
        )
        self.comparison_artists.append(info_box)
        
        self.canvas.draw_idle()
        print(f"📐 夹角: {angle_diff:.1f}°, 距离: {new_distance:.3f}")
    
    def _clear_comparison(self):
        """清除对比虚线和信息框"""
        for artist in self.comparison_artists:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass
        self.comparison_artists.clear()
    
    def _show_toast(self, message: str, duration: int = 2000):
        """
        显示Toast提示消息
        
        Args:
            message: 提示消息内容
            duration: 显示时长（毫秒），默认2000ms
        """
        # 清除之前的Toast
        self._hide_toast()
        
        # 在画布中央偏上位置显示Toast
        x_range, y_range = self.current_range
        toast_x = 0
        toast_y = y_range * 0.7  # 上方70%位置
        
        # 创建Toast文本框
        self.toast_artist = self.axes.text(
            toast_x, toast_y,
            message,
            bbox=dict(
                boxstyle='round,pad=0.6',
                facecolor='#424242',  # 深灰色背景
                edgecolor='#212121',
                linewidth=1,
                alpha=0.9
            ),
            fontsize=11,
            fontweight='bold',
            color='white',
            ha='center', va='center',
            zorder=100  # 最高层级
        )
        
        self.canvas.draw_idle()
        
        # 设置定时器自动隐藏
        try:
            tk_widget = self.canvas.get_tk_widget()
            self.toast_timer_id = tk_widget.after(duration, self._hide_toast)
        except Exception:
            pass
        
        print(f"🔔 Toast: {message}")
    
    def _hide_toast(self):
        """隐藏Toast提示"""
        # 取消定时器
        if self.toast_timer_id is not None:
            try:
                tk_widget = self.canvas.get_tk_widget()
                tk_widget.after_cancel(self.toast_timer_id)
            except Exception:
                pass
            self.toast_timer_id = None
        
        # 移除Toast对象
        if self.toast_artist is not None:
            try:
                self.toast_artist.remove()
            except (ValueError, AttributeError):
                pass
            self.toast_artist = None
            self.canvas.draw_idle()
    
    # ==================== V2.4 锁定扇形功能 - 数据接口 ====================
    
    def get_locked_measurement(self) -> LockedMeasurement:
        """获取锁定测量数据模型"""
        return self.locked_measurement
    
    def set_locked_measurement(self, data: LockedMeasurement):
        """
        设置锁定测量数据（用于项目加载）
        
        Args:
            data: 锁定测量数据模型
        """
        self.locked_measurement = data
        
        # 如果有数据，重新绘制
        if data.has_data():
            self.sector_point = data.sector_point
            self._draw_sector()
            
            # 绘制图钉
            if data.pin_position:
                self._draw_pin(*data.pin_position)
            
            # 如果已锁定，更新样式
            if data.is_locked:
                self._update_sector_style(locked=True)
        
        self.canvas.draw_idle()
    
    def unlock_on_user_coord_change(self):
        """
        用户坐标系切换时自动解锁
        
        当用户坐标系位置改变时调用此方法，自动解锁扇形
        """
        if self.locked_measurement.is_locked:
            self.locked_measurement.unlock()
            self._update_sector_style(locked=False)
            self._clear_comparison()
            
            # 更新图钉样式
            if self.pin_position:
                self._draw_pin(*self.pin_position)
            
            self._show_toast("用户位置已更改，扇形自动解锁")
            print("🔓 用户坐标系切换，扇形自动解锁")
    
    # ==================== V2.5 背景户型图功能 ====================
    
    def set_background_image(self, bg_image: BackgroundImage):
        """
        设置背景户型图
        
        Args:
            bg_image: 背景图数据对象
        """
        self.background_image = bg_image
        self._draw_background()
        self.canvas.draw_idle()
        print(f"✅ 背景户型图已设置")
    
    def update_background_scale(self, pixels_per_unit: float) -> bool:
        """
        更新背景图比例（响应用户输入）
        
        Args:
            pixels_per_unit: 每格对应的像素数
            
        Returns:
            是否更新成功
        """
        if not self.background_image:
            return False
        
        success = self.background_image.set_pixels_per_unit(pixels_per_unit)
        if success:
            self._draw_background()
            self.canvas.draw_idle()
        return success
    
    def _draw_background(self):
        """
        绘制背景户型图（内部方法）
        
        背景图始终在最底层（zorder=0），确保不遮挡其他元素
        """
        # 清除之前的背景图
        self._clear_background()
        
        if not self.background_image or not self.background_image.is_valid():
            return
        
        bg = self.background_image
        
        # 使用 imshow 绘制背景图（中心对齐的坐标范围）
        self.background_artist = self.axes.imshow(
            bg.image_data,
            extent=[bg.x_min, bg.x_max, bg.y_min, bg.y_max],
            alpha=bg.alpha,
            zorder=0,       # 最底层
            aspect='auto',  # 自动调整宽高比
            origin='upper'  # 图片原点在左上角
        )
        
        actual_w, actual_h = bg.get_actual_size()
        print(f"🖼️ 背景户型图已绑制: {actual_w:.1f}m × {actual_h:.1f}m, alpha={bg.alpha}")
    
    def _clear_background(self):
        """清除背景图"""
        if self.background_artist:
            try:
                self.background_artist.remove()
            except (ValueError, AttributeError):
                pass
            self.background_artist = None
    
    def update_background_alpha(self, alpha: float):
        """
        更新背景图透明度
        
        Args:
            alpha: 透明度值 (0.0-1.0)
        """
        if self.background_image:
            self.background_image.set_alpha(alpha)
            if self.background_artist:
                self.background_artist.set_alpha(alpha)
                self.canvas.draw_idle()
                print(f"🎨 背景图透明度更新: {int(alpha * 100)}%")
    
    def toggle_background_visibility(self, visible: bool):
        """
        切换背景图显示/隐藏
        
        Args:
            visible: True 显示，False 隐藏
        """
        if self.background_image:
            self.background_image.set_enabled(visible)
            if visible:
                self._draw_background()
            else:
                self._clear_background()
            self.canvas.draw_idle()
            print(f"👁️ 背景图显示: {'开启' if visible else '关闭'}")
    
    def remove_background(self):
        """移除背景图"""
        self._clear_background()
        if self.background_image:
            self.background_image.clear()
        self.background_image = None
        self.canvas.draw_idle()
        print("🗑️ 背景图已移除")
    
    def get_background_image(self) -> Optional[BackgroundImage]:
        """
        获取当前背景图数据
        
        Returns:
            BackgroundImage 对象，如果没有则返回 None
        """
        return self.background_image
    
    def has_background_image(self) -> bool:
        """
        检查是否有背景图
        
        Returns:
            True 表示有背景图
        """
        return self.background_image is not None and self.background_image.is_loaded()
