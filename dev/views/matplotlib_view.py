# -*- coding: utf-8 -*-
"""
Matplotlib坐标展示区视图

基于Matplotlib实现的高性能绘图组件，替换原有的Canvas+Pillow方案
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


class MatplotlibView:
    """
    基于Matplotlib的坐标展示区类
    
    替换原有CanvasView，提供更强大的绘图能力和更简洁的代码实现
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
        'user_grid': (0.400, 0.050, 0.600, 0.7),    # 更深的紫色网格，提升对比度
        'user_axis': (0.300, 0.000, 0.500, 0.9),    # 深紫色虚线坐标轴，增强显示
        'user_marker': '#5e35b1',     # 更醒目的深紫色用户位置标记
        'user_text': '#4a148c',       # 深紫色文字
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
        
        # 回调函数
        self.on_click_callback: Optional[Callable[[float, float], None]] = None
        self.on_right_click_callback: Optional[Callable[[], None]] = None
        self.on_mouse_move_callback: Optional[Callable[[float, float], None]] = None
        self.on_double_click_callback: Optional[Callable[[float, float], None]] = None
        
        # 创建Matplotlib组件
        self._create_matplotlib_components()
        self._setup_coordinate_system()
        self._bind_events()
        
        print("✅ MatplotlibView初始化完成")
    
    def _create_matplotlib_components(self):
        """
        创建Matplotlib核心组件
        """
        # 创建Figure和Axes
        self.figure = Figure(figsize=self.FIGURE_SIZE, dpi=self.DPI, 
                           facecolor=self.COLORS['background'])
        self.axes = self.figure.add_subplot(111)
        
        # 嵌入到tkinter框架
        self.canvas = FigureCanvasTkAgg(self.figure, self.parent_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # 可选：添加工具栏（注释掉以保持简洁）
        # self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent_frame)
        # self.toolbar.update()
        
        print("✅ Matplotlib组件创建完成")
    
    def _setup_coordinate_system(self, x_range: float = 10.0, y_range: float = 10.0):
        """
        设置坐标系统
        
        Args:
            x_range: X轴显示范围（±x_range）
            y_range: Y轴显示范围（±y_range）
        """
        self.current_range = (x_range, y_range)
        
        # 设置坐标范围
        self.axes.set_xlim(-x_range, x_range)
        self.axes.set_ylim(-y_range, y_range)
        
        # 设置等比例显示
        self.axes.set_aspect('equal', adjustable='box')
        
        # 配置网格 - 修复：按整数步进显示
        # 计算合适的刻度间隔
        major_ticks = np.arange(-int(x_range), int(x_range) + 1, 1)
        self.axes.set_xticks(major_ticks)
        self.axes.set_yticks(major_ticks)
        
        # 设置网格样式
        self.axes.grid(True, alpha=0.5, color=self.COLORS['grid_line'], 
                      linewidth=0.5, linestyle='-')
        
        # 设置坐标轴样式
        self.axes.spines['left'].set_color(self.COLORS['axis_line'])
        self.axes.spines['bottom'].set_color(self.COLORS['axis_line'])
        self.axes.spines['left'].set_linewidth(2)
        self.axes.spines['bottom'].set_linewidth(2)
        
        # 隐藏右侧和顶部边框
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)
        
        # 设置背景色
        self.axes.set_facecolor(self.COLORS['background'])
        
        # 强调原点 - 修复：使用正确的坐标轴显示
        self.axes.axhline(y=0, color=self.COLORS['axis_line'], linewidth=2, alpha=0.8)
        self.axes.axvline(x=0, color=self.COLORS['axis_line'], linewidth=2, alpha=0.8)
        
        # 原点标记
        self.axes.plot(0, 0, 'o', color=self.COLORS['origin_point'], 
                      markersize=8, zorder=10, label='原点')
        
        # 设置标题和标签
        self.axes.set_xlabel('X 坐标', fontsize=12, color=self.COLORS['axis_line'])
        self.axes.set_ylabel('Y 坐标', fontsize=12, color=self.COLORS['axis_line'])
        
        print(f"✅ 坐标系统设置完成：±{x_range} x ±{y_range}")
    
    def _bind_events(self):
        """
        绑定鼠标事件
        """
        # 绑定鼠标事件
        self.canvas.mpl_connect('button_press_event', self._on_mouse_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('axes_leave_event', self._on_mouse_leave)
        
        print("✅ 事件绑定完成")
    
    def _on_mouse_click(self, event):
        """
        处理鼠标点击事件
        """
        if event.inaxes != self.axes:
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        
        current_time = time.time()
        
        if event.button == 1:  # 左键
            # 检查是否为双击
            if current_time - self.last_click_time < self.click_tolerance:
                # 双击：绘制90度扇形
                self._handle_double_click(x, y)
            else:
                # 单击：创建测量点
                self._handle_single_click(x, y)
            
            self.last_click_time = current_time
            
        elif event.button == 3:  # 右键
            # 清除所有测量点和扇形
            self._handle_right_click()
    
    def _handle_single_click(self, x: float, y: float):
        """
        处理左键单击：创建测量点 ✨ 支持动态交互模式
        """
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
        处理左键双击：绘制以点击点为直径，原点为圆心的90度扇形
        """
        # 保存扇形参考点
        self.sector_point = (x, y)
        
        # 重新绘制
        self._draw_sector()
        
        # 触发回调
        if self.on_double_click_callback:
            self.on_double_click_callback(x, y)
        
        print(f"✅ 创建扇形: 参考点({x:.3f}, {y:.3f})")
    
    def _handle_right_click(self):
        """
        处理右键单击：清除所有测量点和扇形
        """
        # 清除测量点
        self.measurement_point = None
        self.sector_point = None
        
        # 清除图形
        self._clear_measurement()
        self._clear_sector()
        
        # 更新显示
        self.canvas.draw_idle()
        
        # 触发回调
        if self.on_right_click_callback:
            self.on_right_click_callback()
        
        print("✅ 清除所有测量点和扇形")
    
    def _on_mouse_move(self, event):
        """
        处理鼠标移动事件 ✨ 交互体验优化
        """
        if event.inaxes != self.axes:
            self.mouse_pos = None
            self._clear_crosshair()
            self._clear_coordinate_info()
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            self.mouse_pos = None
            self._clear_crosshair()
            self._clear_coordinate_info()
            return
        
        # 检查是否在坐标范围内
        x_range, y_range = self.current_range
        if -x_range <= x <= x_range and -y_range <= y <= y_range:
            # 只有当鼠标位置真正改变时才更新（减少不必要的重绘）✨ 性能优化
            threshold = 0.05  # 增大阈值，减少高频更新
            if not self.mouse_pos or (abs(x - self.mouse_pos[0]) > threshold or abs(y - self.mouse_pos[1]) > threshold):
                self.mouse_pos = (x, y)
                self._draw_crosshair()
                self._draw_coordinate_info(x, y)  # ✨ 第五步新增功能
                
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
            if artist in self.axes.lines:
                artist.remove()
        self.crosshair_artists.clear()
        # 注意：不在这里调用draw_idle()，由调用者统一控制重绘时机
    
    def _draw_devices(self):
        """
        绘制所有设备点
        """
        # 清除之前的设备图形
        self._clear_devices()
        
        if not self.devices:
            self.canvas.draw_idle()
            return
        
        # 提取坐标和名称
        x_coords = [device.x for device in self.devices]
        y_coords = [device.y for device in self.devices]
        
        # 绘制设备点
        scatter = self.axes.scatter(x_coords, y_coords, 
                                  c=self.COLORS['device_point'], 
                                  s=50, zorder=5, alpha=0.8,
                                  edgecolors='white', linewidth=1)
        self.device_artists.append(scatter)
        
        # 添加设备标签
        for device in self.devices:
            annotation = self.axes.annotate(
                f'{device.name}\n({device.x:.3f}, {device.y:.3f})',
                xy=(device.x, device.y),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', 
                         facecolor='#ffffe0',  # 浅黄色背景 (对照HTML)
                         edgecolor=self.COLORS['device_point'],
                         alpha=0.9),
                fontsize=9,
                color=self.COLORS['device_point'],
                zorder=6
            )
            self.device_artists.append(annotation)
        
        # 更新显示
        self.canvas.draw_idle()
    
    def _draw_measurement(self):
        """
        绘制测量点和测量线 ✨ 支持双坐标系模式
        """
        if not self.measurement_point:
            return
        
        # 清除之前的测量图形
        self._clear_measurement()
        
        x, y = self.measurement_point.x, self.measurement_point.y
        
        # 绘制测量点 - 修复：使用正确的颜色和大小
        point = self.axes.plot(x, y, 'o', 
                             color=self.COLORS['measurement_point'], 
                             markersize=8, zorder=7)[0]
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
        
        # 计算信息框位置 - 对照HTML的位置策略
        info_x = x + 0.3 if x < self.current_range[0] * 0.5 else x - 0.3
        info_y = y + 0.3 if y < self.current_range[1] * 0.5 else y - 0.3
        
        annotation = self.axes.annotate(
            info_text,
            xy=(x, y),
            xytext=(info_x, info_y),
            bbox=dict(boxstyle='round,pad=0.5', 
                     facecolor=self.COLORS['label_bg'], 
                     edgecolor=self.COLORS['label_border'],
                     alpha=0.9),
            fontsize=9,
            color=self.COLORS['text_color'],
            zorder=8
        )
        self.measurement_artists.append(annotation)
        
        # 更新显示
        self.canvas.draw_idle()
    
    def _draw_sector(self):
        """
        绘制90度扇形：支持动态交互模式 ✨ 根据坐标系状态选择中心点
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
        
        # 计算起始角度 (点击点相对于中心点的角度)
        start_angle_rad = math.atan2(y - center_y, x - center_x)
        start_angle_deg = math.degrees(start_angle_rad)
        
        # 90度扇形：从start_angle开始，逆时针90度
        # 对照HTML中的扇形实现：startAngle = Math.PI, endAngle = 1.5 * Math.PI
        end_angle_deg = start_angle_deg + 90
        
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
        
        # 更新显示
        self.canvas.draw_idle()
        
        print(f"✅ 绘制扇形: 半径={radius:.3f}, 起始角度={start_angle_deg:.1f}°")
    
    def _clear_devices(self):
        """
        清除设备图形
        """
        for artist in self.device_artists:
            try:
                artist.remove()
            except ValueError:
                pass  # 可能已经被移除
        self.device_artists.clear()
    
    def _clear_measurement(self):
        """
        清除测量图形
        """
        for artist in self.measurement_artists:
            try:
                artist.remove()
            except ValueError:
                pass
        self.measurement_artists.clear()
    
    def _clear_sector(self):
        """
        清除扇形图形
        """
        for artist in self.sector_artists:
            try:
                artist.remove()
            except ValueError:
                pass
        self.sector_artists.clear()
    
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
            
            # 重新设置坐标系统
            self._setup_coordinate_system(x_range, y_range)
            
            # 重新绘制所有内容
            self._draw_devices()
            self._draw_measurement()
            self._draw_sector()
            
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
        self.user_position = (x, y)
        print(f"✨ 视图设置用户位置: ({x:.3f}, {y:.3f})")
        
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
        
        # 绘制用户位置标记（增强版三层设计）✨ 视觉优化增强版
        # 最外圈：深色阴影效果
        shadow_marker = self.axes.scatter([x], [y], marker='o', s=320, 
                                        c='#2d1b5c', alpha=0.3, 
                                        zorder=13)
        self.user_position_artists.append(shadow_marker)
        
        # 外圈：白色边框，增大尺寸提升对比度
        outer_marker = self.axes.scatter([x], [y], marker='o', s=280, 
                                       c='white', edgecolors=self.COLORS['user_marker'], 
                                       linewidth=6, zorder=14, alpha=0.98)
        self.user_position_artists.append(outer_marker)
        
        # 内圈：深紫色主体标记，更醒目
        inner_marker = self.axes.scatter([x], [y], marker='o', s=180, 
                                       c=self.COLORS['user_marker'], 
                                       edgecolors='white', linewidth=4,
                                       label='用户位置', zorder=15, alpha=1.0)
        self.user_position_artists.append(inner_marker)
        
        # 人形符号叠加（增强可见性和尺寸）
        person_marker = self.axes.scatter([x], [y], marker='*', s=120, 
                                        c='white', edgecolors=self.COLORS['user_marker'],
                                        linewidth=2, zorder=16, alpha=1.0)
        self.user_position_artists.append(person_marker)
        
        # 添加用户位置文字标签 ✨ 第五步视觉优化
        text = self.axes.text(x, y + 0.7, f'[用户] 位置\n({x:.1f}, {y:.1f})', 
                            fontsize=12, fontweight='bold',
                            color=self.COLORS['user_text'],
                            ha='center', va='bottom', zorder=17,
                            bbox=dict(boxstyle="round,pad=0.5",
                                    facecolor='#f8f4ff',  # 浅紫色背景
                                    edgecolor=self.COLORS['user_marker'],
                                    linewidth=2.5,
                                    alpha=0.95))  # 移除不兼容的shadow参数
        self.user_position_artists.append(text)
        
        print(f"✨ 绘制用户位置标记: ({x:.3f}, {y:.3f})")
    
    def _draw_user_coordinate_axes(self):
        """绘制用户坐标系轴线（精致的紫色虚线）"""
        if not self.user_position:
            return
        
        x, y = self.user_position
        x_range, y_range = self.current_range
        
        # 绘制用户坐标系的精致虚线轴
        # 主轴线（较粗）
        h_line_main = self.axes.axhline(y=y, color=self.COLORS['user_axis'], 
                                      linewidth=3, linestyle='--', alpha=0.8, zorder=6)
        v_line_main = self.axes.axvline(x=x, color=self.COLORS['user_axis'], 
                                      linewidth=3, linestyle='--', alpha=0.8, zorder=6)
        
        # 辅助轴线（较细，增强视觉效果）
        h_line_aux = self.axes.axhline(y=y, color='white', 
                                     linewidth=1, linestyle='--', alpha=0.6, zorder=5)
        v_line_aux = self.axes.axvline(x=x, color='white', 
                                     linewidth=1, linestyle='--', alpha=0.6, zorder=5)
        
        self.user_position_artists.extend([h_line_main, v_line_main, h_line_aux, v_line_aux])
        
        # 在轴线上添加箭头标识（可选）
        # X轴正向箭头
        if x + 1 <= x_range:
            x_arrow = self.axes.annotate('', xy=(x + 0.8, y), xytext=(x + 0.2, y),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=self.COLORS['user_axis'],
                                                     lw=2, alpha=0.7),
                                       zorder=7)
            self.user_position_artists.append(x_arrow)
        
        # Y轴正向箭头
        if y + 1 <= y_range:
            y_arrow = self.axes.annotate('', xy=(x, y + 0.8), xytext=(x, y + 0.2),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=self.COLORS['user_axis'],
                                                     lw=2, alpha=0.7),
                                       zorder=7)
            self.user_position_artists.append(y_arrow)
        
        print(f"✨ 绘制用户坐标系轴线: 中心({x:.3f}, {y:.3f})")
    
    def _clear_user_coordinate_overlay(self):
        """清除用户坐标系叠加层"""
        for artist in self.user_position_artists:
            try:
                artist.remove()
            except ValueError:
                pass  # 如果对象已被移除，忽略错误
        self.user_position_artists.clear()
        print("✨ 清除用户坐标系叠加层")
    
    def _clear_user_position_marker(self):
        """清除用户位置标记和轴线，但保留网格"""
        # 清除用户位置标记、轴线，但保留网格
        artists_to_remove = []
        for artist in self.user_position_artists:
            # 检查是否是scatter、text或者轴线对象（不是网格线）
            is_marker_or_text = hasattr(artist, 'get_offsets') or hasattr(artist, 'get_text')
            is_axis_line = (hasattr(artist, 'get_linestyle') and 
                           artist.get_linestyle() == '--')  # 虚线轴线
            
            if is_marker_or_text or is_axis_line:
                try:
                    artist.remove()
                    artists_to_remove.append(artist)
                except ValueError:
                    pass
        
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
        # 清除之前的坐标信息
        self._clear_coordinate_info()
        
        # 构建坐标信息文本 ✨ 性能优化：避免重复绘制相同内容
        if self.user_coord_enabled and self.user_position:
            # 双坐标系模式：显示世界坐标和用户相对坐标
            ux, uy = self.user_position
            rel_x, rel_y = x - ux, y - uy
            rel_distance = math.sqrt(rel_x**2 + rel_y**2)
            
            info_text = (
                f"[世界] 坐标: ({x:.2f}, {y:.2f})\n"
                f"[用户] 坐标: ({rel_x:.2f}, {rel_y:.2f})\n"
                f"[距离] 到用户: {rel_distance:.2f}\n"
                f"[角度] 用户方向: {math.degrees(math.atan2(rel_y, rel_x)):.1f}°"
            )
            text_color = '#4a148c'  # 深紫色（增强对比）
            bg_color = '#f8f4ff'    # 更浅的紫色背景
        else:
            # 世界坐标系模式：仅显示世界坐标
            distance = math.sqrt(x**2 + y**2)
            angle = math.degrees(math.atan2(y, x))
            info_text = (
                f"[世界] 坐标: ({x:.2f}, {y:.2f})\n"
                f"[距离] 到原点: {distance:.2f}\n"
                f"[角度] 原点方向: {angle:.1f}°"
            )
            text_color = '#1565c0'  # 深蓝色（增强对比）
            bg_color = '#f0f8ff'    # 更浅的蓝色背景
        
        # 检查内容是否改变，避免重复绘制 ✨ 性能优化
        if info_text == self._last_coordinate_info_text:
            return  # 内容没有变化，跳过重绘
        
        self._last_coordinate_info_text = info_text
        
        # 智能计算信息框位置（四象限适应性定位）✨ 交互体验优化
        x_range, y_range = self.current_range
        
        # 根据鼠标位置选择最佳信息框位置，避免遮挡和超界
        if x > x_range * 0.6:  # 鼠标在右侧
            info_x = x - 2.0  # 信息框显示在左侧
        else:  # 鼠标在左侧
            info_x = x + 0.8  # 信息框显示在右侧
        
        if y > y_range * 0.6:  # 鼠标在上方
            info_y = y - 1.5  # 信息框显示在下方
        else:  # 鼠标在下方
            info_y = y + 0.8  # 信息框显示在上方
        
        # 确保信息框不超出坐标范围
        info_x = max(-x_range + 0.5, min(info_x, x_range - 2.5))
        info_y = max(-y_range + 0.5, min(info_y, y_range - 1.5))
        
        # 绘制坐标信息框 ✨ 第五步视觉优化
        annotation = self.axes.annotate(
            info_text,
            xy=(x, y),
            xytext=(info_x, info_y),
            bbox=dict(
                boxstyle='round,pad=0.6',  # 增大内边距
                facecolor=bg_color,
                edgecolor=text_color,
                linewidth=2,  # 增强边框
                alpha=0.95   # 提高不透明度，移除不兼容的shadow参数
            ),
            fontsize=10,    # 增大字体
            fontweight='bold',  # 加粗字体
            color=text_color,
            zorder=15,  # 最高层级，确保可见
            ha='left',
            arrowprops=dict(
                arrowstyle='->',
                color=text_color,
                alpha=0.7,
                lw=1.5
            )
        )
        self.coordinate_info_artists.append(annotation)
        
        # 注意：不在这里调用draw_idle()，由调用者统一控制重绘时机 ✨ 性能优化
    
    def _clear_coordinate_info(self):
        """
        清除坐标信息显示
        """
        for artist in self.coordinate_info_artists:
            if artist.axes == self.axes:
                artist.remove()
        self.coordinate_info_artists.clear()
        self.canvas.draw_idle() 