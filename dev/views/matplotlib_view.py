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
        self.current_range = (5.0, 5.0)  # 当前坐标范围
        
        # 扇形数据
        self.sector_point: Optional[Tuple[float, float]] = None
        
        # 鼠标状态
        self.mouse_pos: Optional[Tuple[float, float]] = None
        self.last_click_time = 0
        self.click_tolerance = 0.3  # 双击时间间隔
        
        # 绘制对象引用（用于更新和清除）
        self.device_artists = []
        self.measurement_artists = []
        self.sector_artists = []
        self.crosshair_artists = []
        
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
    
    def _setup_coordinate_system(self, x_range: float = 5.0, y_range: float = 5.0):
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
        处理左键单击：创建测量点
        """
        # 创建测量点对象
        self.measurement_point = MeasurementPoint(x, y)
        
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
        处理鼠标移动事件
        """
        if event.inaxes != self.axes:
            self.mouse_pos = None
            self._clear_crosshair()
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            self.mouse_pos = None
            self._clear_crosshair()
            return
        
        # 检查是否在坐标范围内
        x_range, y_range = self.current_range
        if -x_range <= x <= x_range and -y_range <= y <= y_range:
            self.mouse_pos = (x, y)
            self._draw_crosshair()
            
            # 触发回调
            if self.on_mouse_move_callback:
                self.on_mouse_move_callback(x, y)
        else:
            self.mouse_pos = None
            self._clear_crosshair()
    
    def _on_mouse_leave(self, event):
        """
        处理鼠标离开事件
        """
        self.mouse_pos = None
        self._clear_crosshair()
    
    def _draw_crosshair(self):
        """
        绘制十字光标
        """
        if not self.mouse_pos:
            return
        
        # 清除之前的十字光标
        self._clear_crosshair()
        
        x, y = self.mouse_pos
        x_range, y_range = self.current_range
        
        # 绘制垂直线和水平线
        vline = self.axes.axvline(x=x, color=self.COLORS['crosshair'], 
                                 linewidth=0.5, alpha=0.7, zorder=1)
        hline = self.axes.axhline(y=y, color=self.COLORS['crosshair'], 
                                 linewidth=0.5, alpha=0.7, zorder=1)
        
        self.crosshair_artists.extend([vline, hline])
        
        # 更新显示
        self.canvas.draw_idle()
    
    def _clear_crosshair(self):
        """
        清除十字光标
        """
        for artist in self.crosshair_artists:
            if artist in self.axes.lines:
                artist.remove()
        self.crosshair_artists.clear()
        self.canvas.draw_idle()
    
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
        绘制测量点和测量线
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
        
        # 绘制到原点的连线 - 修复：使用正确的颜色
        line = self.axes.plot([0, x], [0, y], 
                            color=self.COLORS['measurement_line'], 
                            linewidth=2, alpha=0.7, zorder=4)[0]
        self.measurement_artists.append(line)
        
        # 添加测量信息 - 修复：使用正确的格式和颜色
        info_lines = self.measurement_point.get_info_lines(3)
        info_text = '\n'.join(info_lines)
        
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
        绘制90度扇形：以点击点到原点的距离为半径，从指向点击点的方向开始的90度扇形
        """
        if not self.sector_point:
            return
        
        # 清除之前的扇形
        self._clear_sector()
        
        x, y = self.sector_point
        
        # 计算半径 (点击点到原点的距离)
        radius = math.sqrt(x*x + y*y)
        
        if radius < 0.01:  # 避免在原点绘制
            return
        
        # 计算起始角度 (点击点相对于原点的角度)
        start_angle_rad = math.atan2(y, x)
        start_angle_deg = math.degrees(start_angle_rad)
        
        # 90度扇形：从start_angle开始，逆时针90度
        # 对照HTML中的扇形实现：startAngle = Math.PI, endAngle = 1.5 * Math.PI
        end_angle_deg = start_angle_deg + 90
        
        # 创建扇形路径
        theta = np.linspace(math.radians(start_angle_deg), 
                           math.radians(end_angle_deg), 50)
        x_sector = radius * np.cos(theta)
        y_sector = radius * np.sin(theta)
        
        # 添加原点到扇形路径
        x_coords = np.concatenate([[0], x_sector, [0]])
        y_coords = np.concatenate([[0], y_sector, [0]])
        
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