# -*- coding: utf-8 -*-
"""
Canvas坐标展示区视图

实现800x800坐标可视化展示区域
"""

import tkinter as tk
from typing import Optional, List, Tuple, Callable, Dict, Any
import math
from PIL import ImageTk, Image, ImageDraw

from models.coordinate_model import CoordinateSystem
from models.device_model import Device
from models.measurement_model import MeasurementPoint
from utils.export_utils import ExportUtils # 导入


class CanvasView:
    """
    Canvas坐标展示区类
    
    实现坐标系统的可视化展示和鼠标交互功能
    """
    
    # Canvas尺寸
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 800
    
    # 界面配色（与ref.html保持一致）
    COLORS = {
        'background': '#e0f7fa',      # 浅蓝色背景
        'grid_line': '#b0bec5',       # 灰蓝色网格线
        'axis_line': '#37474f',       # 深灰色坐标轴
        'device_point': '#c62828',    # 红色设备点
        'origin_point': '#1e88e5',    # 蓝色原点
        'measurement_point': '#ff5722', # 橙色测量点
        'measurement_line': '#ff5722',  # 橙色测量线
        'text_color': '#212121',      # 深色文字
        'label_bg': '#ffffff',        # 白色标签背景
        'label_border': '#cccccc',    # 浅灰色标签边框
        'sector_fill': '#a5d6a7',     # 更浅的绿色扇形填充色
    }
    
    # 绘制参数
    DEVICE_POINT_RADIUS = 6
    ORIGIN_POINT_RADIUS = 4
    MEASUREMENT_POINT_RADIUS = 4
    LABEL_FONT_SIZE = 10
    COORD_FONT_SIZE = 12
    
    def __init__(self, parent_frame: tk.Frame):
        """
        初始化Canvas视图
        
        Args:
            parent_frame: 父容器框架
        """
        self.parent_frame = parent_frame
        self.canvas = None
        
        # 背景缓存
        self._background_cache: Optional[Image.Image] = None
        self._background_photo: Optional[ImageTk.PhotoImage] = None
        
        # 数据模型
        self.coordinate_system = CoordinateSystem(
            x_range=5.0,  # 保持初始范围为5，用户可以通过界面调整到25
            y_range=5.0,
            canvas_width=self.CANVAS_WIDTH,
            canvas_height=self.CANVAS_HEIGHT
        )
        
        # 数据存储
        self.devices: List[Device] = []
        self.measurement_point: Optional[MeasurementPoint] = None
        
        # 鼠标状态
        self.mouse_x = 0
        self.mouse_y = 0
        self.crosshair_visible = False
        
        # 绘制对象ID（用于删除）
        self.grid_items = []
        self.axis_items = []
        self.device_items = []
        self.measurement_items = []
        self.crosshair_items = []
        self.sector_items = []
        
        # 回调函数
        self.on_click_callback: Optional[Callable[[float, float], None]] = None
        self.on_right_click_callback: Optional[Callable[[], None]] = None
        self.on_mouse_move_callback: Optional[Callable[[float, float], None]] = None
        self.on_double_click_callback: Optional[Callable[[float, float], None]] = None
        
        self._create_canvas()
        self._update_background_cache() # 初始化时创建一次背景
        self._bind_events()
        self._draw_initial_content()
    
    def _create_canvas(self):
        """
        创建Canvas画布
        """
        self.canvas = tk.Canvas(
            self.parent_frame,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg=self.COLORS['background'],
            highlightthickness=0,
            relief='flat'
        )
        self.canvas.pack(expand=True, fill='both', padx=5, pady=5)
    
    def _bind_events(self):
        """
        绑定鼠标事件
        """
        # 鼠标移动事件
        self.canvas.bind('<Motion>', self._on_mouse_move)
        
        # 鼠标离开事件
        self.canvas.bind('<Leave>', self._on_mouse_leave)
        
        # 左键点击事件
        self.canvas.bind('<Button-1>', self._on_left_click)
        
        # 右键点击事件
        self.canvas.bind('<Button-2>', self._on_right_click)  # macOS
        self.canvas.bind('<Button-3>', self._on_right_click)  # Windows/Linux
        
        # 左键双击事件
        self.canvas.bind('<Double-1>', self._on_double_click)
    
    def _on_mouse_move(self, event):
        """
        鼠标移动事件处理
        
        Args:
            event: 鼠标事件对象
        """
        # 检查是否在绘图区域内
        if self.coordinate_system.is_canvas_point_in_graph(event.x, event.y):
            self.mouse_x = event.x
            self.mouse_y = event.y
            self.crosshair_visible = True
            
            # 转换为逻辑坐标
            logic_x, logic_y = self.coordinate_system.from_canvas_coords(event.x, event.y)
            
            # 调用回调函数
            if self.on_mouse_move_callback:
                self.on_mouse_move_callback(logic_x, logic_y)
            
            # 重绘十字光标
            self._draw_crosshair()
        else:
            self.crosshair_visible = False
            self._clear_crosshair()
    
    def _on_mouse_leave(self, event):
        """
        鼠标离开事件处理
        """
        self.crosshair_visible = False
        self._clear_crosshair()
    
    def _on_left_click(self, event):
        """
        左键点击事件处理
        
        Args:
            event: 鼠标事件对象
        """
        # 清除临时的扇形
        self._clear_sector()
        
        # 检查是否在绘图区域内
        if self.coordinate_system.is_canvas_point_in_graph(event.x, event.y):
            # 转换为逻辑坐标
            logic_x, logic_y = self.coordinate_system.from_canvas_coords(event.x, event.y)
            
            # 创建测量点
            self.measurement_point = MeasurementPoint(logic_x, logic_y)
            
            # 调用回调函数
            if self.on_click_callback:
                self.on_click_callback(logic_x, logic_y)
            
            # 重绘测量内容
            self._draw_measurement()
    
    def _on_double_click(self, event):
        """
        左键双击事件处理
        
        Args:
            event: 鼠标事件对象
        """
        # 双击事件会先触发一次单击，所以这里要清除单击时创建的测量点
        self.clear_measurement()
        
        # 转换为逻辑坐标
        logic_x, logic_y = self.coordinate_system.from_canvas_coords(event.x, event.y)

        # 调用回调函数
        if self.on_double_click_callback:
            self.on_double_click_callback(logic_x, logic_y)
    
    def _on_right_click(self, event):
        """
        右键点击事件处理
        
        Args:
            event: 鼠标事件对象
        """
        # 清除测量点和扇形
        self.clear_measurement()
        self._clear_sector()
        
        # 调用回调函数
        if self.on_right_click_callback:
            self.on_right_click_callback()
    
    def _draw_initial_content(self):
        """
        绘制初始内容 (现在只绘制动态部分)
        """
        self.refresh() # 初始绘制通过refresh完成
        
        # 添加示例设备（与ref.html一致）
        self.add_device(Device("7寸屏", -2.625, 0))
        self.add_device(Device("4寸屏", -1.000, 3.544))
    
    def _update_background_cache(self):
        """
        更新并缓存静态背景（网格、坐标轴、标签）到一张图片上
        """
        # 1. 创建一个新的PIL图像
        self._background_cache = Image.new(
            'RGB', 
            (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), 
            self.COLORS['background']
        )
        draw = ImageDraw.Draw(self._background_cache)

        # 2. 在这个PIL图像上绘制所有静态元素
        # 注意：这里的绘制逻辑需要从原来的_draw_*方法中提取或重写
        # 为了简洁，我们直接调用一个模拟的绘制函数
        self._draw_static_elements_on_image(draw)

        # 3. 将PIL图像转换为Tkinter的PhotoImage
        if self._background_cache:
            self._background_photo = ImageTk.PhotoImage(self._background_cache)
        print("✅ 背景缓存已更新")

    def _draw_static_elements_on_image(self, draw: ImageDraw.Draw):
        """
        一个辅助方法，将所有静态内容绘制到给定的PIL.ImageDraw对象上
        """
        # 绘制网格
        vertical_lines, horizontal_lines = self.coordinate_system.get_grid_lines()
        for line in vertical_lines + horizontal_lines:
            draw.line(line, fill=self.COLORS['grid_line'], width=1)
        
        # 绘制坐标轴
        x_axis, y_axis = self.coordinate_system.get_axis_lines()
        draw.line(x_axis, fill=self.COLORS['axis_line'], width=2)
        draw.line(y_axis, fill=self.COLORS['axis_line'], width=2)

        # 绘制刻度标签 (改进版)
        x_ticks, y_ticks = self.coordinate_system.get_tick_labels()
        font = ExportUtils.get_system_font(self.COORD_FONT_SIZE, "normal")
        if not font:
            # 如果获取不到字体，就无法绘制标签
            return
            
        for tick in x_ticks: # X轴刻度 (anchor='n')
            pos = tick['pos']
            text = tick['text']
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            # 手动实现 'n' 锚点 (顶部居中)
            draw.text((pos[0] - text_width / 2, pos[1]), text, fill=self.COLORS['text_color'], font=font)

        for tick in y_ticks: # Y轴刻度 (anchor='e')
            pos = tick['pos']
            text = tick['text']
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            # 手动实现 'e' 锚点 (右侧居中)
            draw.text((pos[0] - text_width, pos[1] - text_height / 2), text, fill=self.COLORS['text_color'], font=font)

        # 绘制原点 '0' 标签 (anchor='ne')
        origin_tick = self.coordinate_system.get_origin_label_info()
        if origin_tick:
            pos = origin_tick['pos']
            text = origin_tick['text']
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            # 手动实现 'ne' 锚点 (东北角)
            draw.text((pos[0] - text_width, pos[1]), text, fill=self.COLORS['text_color'], font=font)
    
    def _draw_devices(self):
        """
        绘制所有设备点
        """
        # 清除之前的设备绘制项
        self._clear_items(self.device_items)
        
        for device in self.devices:
            self._draw_single_device(device)
    
    def _draw_single_device(self, device: Device):
        """
        绘制单个设备
        
        Args:
            device: 设备对象
        """
        # 转换为Canvas坐标
        canvas_x, canvas_y = self.coordinate_system.to_canvas_coords(device.x, device.y)
        
        # 绘制设备点
        point_id = self.canvas.create_oval(
            canvas_x - self.DEVICE_POINT_RADIUS,
            canvas_y - self.DEVICE_POINT_RADIUS,
            canvas_x + self.DEVICE_POINT_RADIUS,
            canvas_y + self.DEVICE_POINT_RADIUS,
            fill=self.COLORS['device_point'],
            outline=self.COLORS['device_point'],
            width=1
        )
        self.device_items.append(point_id)
        
        # --- 改进：动态计算标签尺寸和位置 ---
        
        # 准备标签文本
        label_text = f"{device.name}\n({device.x:.3f}, {device.y:.3f})"
        font_family = 'Arial'
        font_size = self.LABEL_FONT_SIZE
        font_style = 'bold'
        
        # 使用Canvas的font配置获取精确的文本尺寸
        font_config = (font_family, font_size, font_style)
        
        # 分割文本行来计算最大宽度和总高度
        text_lines = label_text.split('\n')
        max_line_width = 0
        total_height = 0
        
        # 计算每行的宽度，找出最大宽度
        for line in text_lines:
            # 使用Canvas的font_measure方法获取精确宽度
            line_width = self.canvas.create_text(0, 0, text=line, font=font_config)
            bbox = self.canvas.bbox(line_width)
            self.canvas.delete(line_width)  # 立即删除临时文本
            
            if bbox:
                line_actual_width = bbox[2] - bbox[0]
                max_line_width = max(max_line_width, line_actual_width)
        
        # 计算文本总高度 (行数 × 字体高度 + 行间距)
        line_height = font_size + 2  # 字体大小 + 行间距
        total_height = len(text_lines) * line_height
        
        # 添加适当的padding
        padding = 6
        box_width = max_line_width + 2 * padding
        box_height = total_height + 2 * padding
        
        # 计算标签位置 (默认在设备点上方)
        label_x = canvas_x
        label_y = canvas_y - self.DEVICE_POINT_RADIUS - (box_height / 2) - 5

        # 如果上方空间不足，则移动到下方
        if label_y - (box_height / 2) < 0:
            label_y = canvas_y + self.DEVICE_POINT_RADIUS + (box_height / 2) + 5
            
        # 创建标签背景
        bg_id = self.canvas.create_rectangle(
            label_x - box_width / 2, label_y - box_height / 2,
            label_x + box_width / 2, label_y + box_height / 2,
            fill=self.COLORS['label_bg'],
            outline=self.COLORS['label_border'],
            width=1
        )
        self.device_items.append(bg_id)
        
        # 创建标签文字
        text_id = self.canvas.create_text(
            label_x, label_y,
            text=label_text,
            fill=self.COLORS['text_color'],
            font=(font_family, font_size, font_style),
            anchor='center',
            justify='center'
        )
        self.device_items.append(text_id)
    
    def _draw_crosshair(self):
        """
        绘制十字光标
        """
        if not self.crosshair_visible:
            return
        
        # 清除之前的十字光标
        self._clear_crosshair()
        
        # 获取绘图区域边界
        padding = self.coordinate_system.padding
        graph_width = self.coordinate_system.graph_width
        graph_height = self.coordinate_system.graph_height
        
        # 绘制垂直线
        v_line_id = self.canvas.create_line(
            self.mouse_x, padding,
            self.mouse_x, padding + graph_height,
            fill='#666666',
            width=1,
            dash=(2, 2)
        )
        self.crosshair_items.append(v_line_id)
        
        # 绘制水平线
        h_line_id = self.canvas.create_line(
            padding, self.mouse_y,
            padding + graph_width, self.mouse_y,
            fill='#666666',
            width=1,
            dash=(2, 2)
        )
        self.crosshair_items.append(h_line_id)
    
    def _draw_measurement(self):
        """
        绘制测量点和测量信息
        """
        if not self.measurement_point:
            return
        
        # 清除之前的测量绘制项
        self._clear_items(self.measurement_items)
        
        # 转换为Canvas坐标
        canvas_x, canvas_y = self.coordinate_system.to_canvas_coords(
            self.measurement_point.x, self.measurement_point.y
        )
        
        # 绘制测量点
        point_id = self.canvas.create_oval(
            canvas_x - self.MEASUREMENT_POINT_RADIUS,
            canvas_y - self.MEASUREMENT_POINT_RADIUS,
            canvas_x + self.MEASUREMENT_POINT_RADIUS,
            canvas_y + self.MEASUREMENT_POINT_RADIUS,
            fill=self.COLORS['measurement_point'],
            outline=self.COLORS['measurement_point'],
            width=1
        )
        self.measurement_items.append(point_id)
        
        # 绘制到原点的连线
        origin_x, origin_y = self.coordinate_system.get_origin_position()
        line_id = self.canvas.create_line(
            origin_x, origin_y,
            canvas_x, canvas_y,
            fill=self.COLORS['measurement_line'],
            width=2
        )
        self.measurement_items.append(line_id)
        
        # 绘制测量信息
        self._draw_measurement_info(canvas_x, canvas_y)
    
    def _draw_measurement_info(self, canvas_x: float, canvas_y: float):
        """
        绘制测量信息框
        
        Args:
            canvas_x: 测量点Canvas X坐标
            canvas_y: 测量点Canvas Y坐标
        """
        if not self.measurement_point:
            return
        
        # 获取格式化信息
        info_lines = self.measurement_point.get_info_lines(3)
        
        # 计算信息框位置（测量点右侧）
        info_x = canvas_x + 15
        info_y = canvas_y
        
        # 计算信息框尺寸
        max_line_width = max(len(line) for line in info_lines)
        box_width = max_line_width * 6 + 10
        box_height = len(info_lines) * 16 + 10
        
        # 确保信息框不超出Canvas边界
        if info_x + box_width > self.CANVAS_WIDTH - 10:
            info_x = canvas_x - box_width - 15
        if info_y + box_height > self.CANVAS_HEIGHT - 10:
            info_y = self.CANVAS_HEIGHT - box_height - 10
        if info_y < 10:
            info_y = 10
        
        # 绘制信息框背景
        bg_id = self.canvas.create_rectangle(
            info_x, info_y,
            info_x + box_width, info_y + box_height,
            fill=self.COLORS['label_bg'],
            outline=self.COLORS['label_border'],
            width=1
        )
        self.measurement_items.append(bg_id)
        
        # 绘制信息文本
        for i, line in enumerate(info_lines):
            text_id = self.canvas.create_text(
                info_x + 5, info_y + 5 + i * 16,
                text=line,
                fill=self.COLORS['text_color'],
                font=('Arial', self.LABEL_FONT_SIZE, 'bold'),
                anchor='nw'
            )
            self.measurement_items.append(text_id)
    
    def _clear_items(self, item_list: List[int]):
        """
        清除指定的Canvas绘制项
        
        Args:
            item_list: 绘制项ID列表
        """
        for item_id in item_list:
            self.canvas.delete(item_id)
        item_list.clear()
    
    def _clear_crosshair(self):
        """
        清除十字光标
        """
        self._clear_items(self.crosshair_items)
    
    def _clear_sector(self):
        """
        清除扇形
        """
        self._clear_items(self.sector_items)

    def draw_temporary_sector(self, click_x: float, click_y: float, angle_degrees: float):
        """
        以坐标原点为圆心，绘制90度扇形，弧线经过双击点，边界为象限坐标轴

        Args:
            click_x, click_y: 双击位置的逻辑坐标
            angle_degrees: 扇形的角度（固定为90度）
        """
        self._clear_sector()

        # 获取原点的画布坐标
        origin_canvas_x, origin_canvas_y = self.coordinate_system.to_canvas_coords(0, 0)
        
        # 计算从原点到双击位置的距离作为半径
        import math
        radius_logic = math.sqrt(click_x**2 + click_y**2)
        radius_canvas = radius_logic * self.coordinate_system.get_x_scale()
        
        # 确定双击点所在的象限，计算扇形的起始角度
        if click_x >= 0 and click_y >= 0:
            # 第一象限：从X轴正方向(0°)到Y轴正方向(90°)
            start_angle = 0
        elif click_x < 0 and click_y >= 0:
            # 第二象限：从Y轴正方向(90°)到X轴负方向(180°)
            start_angle = 90
        elif click_x < 0 and click_y < 0:
            # 第三象限：从X轴负方向(180°)到Y轴负方向(270°)
            start_angle = 180
        else:
            # 第四象限：从Y轴负方向(270°)到X轴正方向(360°/0°)
            start_angle = 270
        
        # 计算扇形的边界框（以原点为中心）
        bbox = (
            origin_canvas_x - radius_canvas,
            origin_canvas_y - radius_canvas,
            origin_canvas_x + radius_canvas,
            origin_canvas_y + radius_canvas
        )
        
        # 绘制半透明扇形 - 使用最透明的方式
        # 方法1：只绘制边框，无填充
        sector_id = self.canvas.create_arc(
            bbox,
            start=start_angle,
            extent=90,  # 固定90度
            fill='',  # 无填充，完全透明
            outline='#4caf50',  # 绿色边框
            width=3,  # 稍微加粗边框使其更明显
            tags="sector"
        )
        self.sector_items.append(sector_id)
        
        # 方法2：添加一些稀疏的点来指示覆盖区域
        # 计算扇形内部的一些采样点
        import math
        num_points = 8  # 采样点数量
        for i in range(num_points):
            # 在扇形内部随机分布一些小点
            angle_offset = (90 / num_points) * i + (90 / num_points / 2)
            point_angle = math.radians(start_angle + angle_offset)
            
            # 在不同半径位置放置点
            for r_factor in [0.3, 0.6, 0.9]:
                point_radius = radius_canvas * r_factor
                point_x = origin_canvas_x + point_radius * math.cos(point_angle)
                point_y = origin_canvas_y - point_radius * math.sin(point_angle)  # Y轴翻转
                
                # 绘制小点
                point_id = self.canvas.create_oval(
                    point_x - 2, point_y - 2,
                    point_x + 2, point_y + 2,
                    fill='#81c784',  # 浅绿色小点
                    outline='',
                    tags="sector"
                )
                self.sector_items.append(point_id)
        
        # 绘制边界线（可选，让扇形更清晰）
        # X轴方向的半径
        if start_angle == 0:  # 第一象限
            x_end_canvas, y_end_canvas = self.coordinate_system.to_canvas_coords(radius_logic, 0)
        elif start_angle == 90:  # 第二象限
            x_end_canvas, y_end_canvas = self.coordinate_system.to_canvas_coords(0, radius_logic)
        elif start_angle == 180:  # 第三象限
            x_end_canvas, y_end_canvas = self.coordinate_system.to_canvas_coords(-radius_logic, 0)
        else:  # 第四象限
            x_end_canvas, y_end_canvas = self.coordinate_system.to_canvas_coords(0, -radius_logic)
            
        # Y轴方向的半径
        if start_angle == 0:  # 第一象限
            y_end_canvas2, x_end_canvas2 = self.coordinate_system.to_canvas_coords(0, radius_logic)
        elif start_angle == 90:  # 第二象限
            y_end_canvas2, x_end_canvas2 = self.coordinate_system.to_canvas_coords(-radius_logic, 0)
        elif start_angle == 180:  # 第三象限
            y_end_canvas2, x_end_canvas2 = self.coordinate_system.to_canvas_coords(0, -radius_logic)
        else:  # 第四象限
            y_end_canvas2, x_end_canvas2 = self.coordinate_system.to_canvas_coords(radius_logic, 0)
        
        # 将扇形提升到最上层
        self.canvas.tag_raise("sector")
    
    # 公共接口方法
    
    def set_coordinate_range(self, x_range: float, y_range: float):
        """
        设置新的坐标范围，并触发背景重绘和刷新
        """
        self.coordinate_system.set_range(x_range, y_range)
        self._update_background_cache() # <--- 关键：范围变化时更新缓存
        self.refresh()
    
    def add_device(self, device: Device):
        """
        添加设备
        
        Args:
            device: 设备对象
        """
        if device not in self.devices:
            self.devices.append(device)
            self._draw_devices()
    
    def remove_device(self, device: Device):
        """
        移除设备
        
        Args:
            device: 设备对象
        """
        if device in self.devices:
            self.devices.remove(device)
            self._draw_devices()
    
    def clear_devices(self):
        """
        清除所有设备
        """
        self.devices.clear()
        self._clear_items(self.device_items)
    
    def clear_measurement(self):
        """
        清除测量点
        """
        self.measurement_point = None
        self._clear_items(self.measurement_items)
    
    def refresh(self):
        """
        刷新整个Canvas (使用缓存优化)
        """
        # 1. 清除所有动态元素
        self.canvas.delete("all")
        
        # 2. 绘制缓存的背景
        if self._background_photo:
            self.canvas.create_image(0, 0, image=self._background_photo, anchor='nw')
        
        # 3. 绘制所有动态元素
        self._draw_origin()
        self._draw_devices()
        if self.measurement_point:
            self._draw_measurement()
        if self.crosshair_visible:
            self._draw_crosshair()
        
        print("🔄 Canvas已刷新 (使用缓存)")
    
    def set_click_callback(self, callback: Callable[[float, float], None]):
        """
        设置鼠标点击回调函数
        
        Args:
            callback: 回调函数，接收逻辑坐标(x, y)
        """
        self.on_click_callback = callback
    
    def set_right_click_callback(self, callback: Callable[[], None]):
        """
        设置鼠标右键回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_right_click_callback = callback
    
    def set_mouse_move_callback(self, callback: Callable[[float, float], None]):
        """
        设置鼠标移动回调函数
        
        Args:
            callback: 回调函数，接收逻辑坐标(x, y)
        """
        self.on_mouse_move_callback = callback
    
    def set_double_click_callback(self, callback: Callable[[float, float], None]):
        """
        设置鼠标双击回调函数
        
        Args:
            callback: 回调函数，接收逻辑坐标(x, y)
        """
        self.on_double_click_callback = callback
    
    def update_devices(self, devices: List[Device]):
        """
        更新设备列表并重新绘制
        
        Args:
            devices: 新的设备列表
        """
        self.devices = devices.copy()
        self._draw_devices()
    
    def get_devices(self) -> List[Device]:
        """
        获取所有设备列表
        
        Returns:
            设备列表
        """
        return self.devices.copy()
    
    def get_measurement_point(self) -> Optional[MeasurementPoint]:
        """
        获取当前测量点
        
        Returns:
            测量点对象，如果没有则返回None
        """
        return self.measurement_point

    def _draw_tick_labels(self):
        """(已由背景缓存取代) 绘制刻度标签"""
        pass

    def _draw_origin(self):
        """
        绘制原点
        """
        origin_x, origin_y = self.coordinate_system.get_origin_position()
        
        # 清除旧的原点
        # 由于原点是动态元素的一部分，在refresh开始时会被清除
        
        item_id = self.canvas.create_oval(
            origin_x - self.ORIGIN_POINT_RADIUS,
            origin_y - self.ORIGIN_POINT_RADIUS,
            origin_x + self.ORIGIN_POINT_RADIUS,
            origin_y + self.ORIGIN_POINT_RADIUS,
            fill=self.COLORS['origin_point'],
            outline=self.COLORS['origin_point'],
            width=1,
            tags="dynamic_element" # 使用tag方便管理
        )
        # self.axis_items.append(item_id) # 不再需要单独的列表管理