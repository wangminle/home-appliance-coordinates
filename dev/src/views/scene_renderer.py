# -*- coding: utf-8 -*-
"""
场景渲染器

V2.0 重构：纯绑制逻辑，只负责根据SceneModel数据进行Matplotlib绑制。
V2.1 扩展：添加标签拖拽支持和LabelPlacer集成。

核心设计原则：
1. 单一职责 - 只负责渲染，不处理业务逻辑
2. 确定性 - 同样的输入永远产生同样的输出
3. 拖拽交互 - 支持标签位置的手动拖拽调整
"""

import math
from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING, Callable
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.artist import Artist
import matplotlib.patches as patches

from models.scene_model import SceneModel, SectorData, MeasurementData, LabelPosition
from models.coordinate_frame import CoordinateFrame
from models.device_model import Device
from models.background_model import BackgroundImage

# 导入新的标签布局服务
from services.label_placer import LabelPlacer, DeviceAnchor, SectorObstacle
from services.collision_detector import BoundingBox

# 注意：中文字体支持已在 main.py 中通过 FontConfig.configure_matplotlib() 统一配置
# 此处不再重复设置，确保使用各平台最优字体


class SceneRenderer:
    """
    场景渲染器
    
    纯绑制函数，根据SceneModel数据进行Matplotlib绘制。
    不包含任何业务逻辑和状态管理。
    """
    
    # 图形尺寸和样式配置
    FIGURE_SIZE = (8, 8)
    DPI = 100
    
    # 界面配色
    COLORS = {
        'background': '#e0f7fa',        # 浅蓝色背景
        'grid_line': '#b0bec5',         # 灰蓝色网格线
        'axis_line': '#37474f',         # 深灰色坐标轴
        'device_point': '#c62828',      # 红色设备点
        'origin_point': '#1e88e5',      # 蓝色原点
        'measurement_point': '#2e7d32', # 绿色测量点
        'measurement_line': '#4caf50',  # 绿色测量线
        'text_color': '#1b5e20',        # 深绿色文字
        'label_bg': (1.0, 1.0, 1.0, 0.85),  # 半透明白色标签背景
        'label_border': '#2e7d32',      # 绿色标签边框
        'sector_fill': (211/255, 47/255, 47/255, 0.3),  # 红色扇形填充
        'sector_edge': '#d32f2f',       # 红色扇形边缘
        'crosshair': (0.0, 0.0, 0.0, 0.5),  # 十字光标颜色
        # 用户坐标系配色
        'user_grid': (211/255, 47/255, 47/255, 0.5),  # 红色网格，与用户坐标轴保持一致
        # 用户坐标系轴线：改为红色（与MatplotlibView保持一致）
        'user_axis': '#d32f2f',
        'user_marker': '#5e35b1',
        'user_text': '#4a148c',
    }
    
    # 标签尺寸配置（V2.2 更新：适应多行格式）
    LABEL_SIZES = {
        'device': (2.0, 1.2),      # 增加高度适应多行文本
        'measurement': (2.6, 1.4),
        'user': (1.5, 0.7),
    }
    
    def __init__(self, figure: Figure, axes: Axes):
        """
        初始化场景渲染器
        
        Args:
            figure: Matplotlib Figure 对象
            axes: Matplotlib Axes 对象
        """
        self.figure = figure
        self.axes = axes
        
        # 按类别管理绑制对象（用于清除和更新）
        self._artists: Dict[str, List[Artist]] = {
            'background': [],  # - V2.5 背景户型图
            'coordinate_system': [],
            'user_coordinate_system': [],
            'devices': [],
            'measurement': [],
            'sectors': [],
            'crosshair': [],
            'coordinate_info': [],
            'drag_highlight': [],  # 拖拽高亮效果
        }
        
        # - V2.5 背景图数据
        self.background_image: Optional[BackgroundImage] = None
        self.background_artist = None
        
        # 标签位置到element_id的映射（用于拖拽检测）
        self._label_hitboxes: Dict[str, BoundingBox] = {}
        
        # 标签布局服务
        self._label_placer = LabelPlacer()
        
        # === 拖拽状态管理 ===
        self._dragging_label: Optional[str] = None  # 当前拖拽的标签ID
        self._drag_start_pos: Optional[Tuple[float, float]] = None  # 拖拽起始位置
        self._drag_offset: Tuple[float, float] = (0, 0)  # 标签中心与鼠标的偏移
        self._drag_enabled: bool = True  # 是否启用拖拽
        
        # === 拖拽回调 ===
        self._on_label_drag_callback: Optional[Callable[[str, float, float], None]] = None
        self._on_drag_start_callback: Optional[Callable[[str], None]] = None
        self._on_drag_end_callback: Optional[Callable[[str, float, float], None]] = None
        
        # 性能优化缓存
        self._last_crosshair_pos: Optional[Tuple[float, float]] = None
        self._last_coord_info_text: str = ""
        
        # 当前缓存的模型引用（用于拖拽时访问）
        self._current_model: Optional[SceneModel] = None
        
        print("[SceneRenderer] 初始化完成（V2.1 拖拽支持版）")
    
    # ==================== V2.5 背景图方法 ====================
    
    def set_background_image(self, bg_image: BackgroundImage):
        """
        设置背景户型图
        
        Args:
            bg_image: 背景图数据对象
        """
        self.background_image = bg_image
        self._draw_background()
    
    def _draw_background(self):
        """绘制背景户型图"""
        # 清除之前的背景图
        self._clear_category('background')
        
        if not self.background_image or not self.background_image.is_valid():
            return
        
        bg = self.background_image
        
        # 使用 imshow 绘制背景图
        artist = self.axes.imshow(
            bg.image_data,
            extent=[bg.x_min, bg.x_max, bg.y_min, bg.y_max],
            alpha=bg.alpha,
            zorder=0,       # 最底层
            aspect='auto',
            origin='upper'
        )
        
        self._artists['background'].append(artist)
        self.background_artist = artist
        
        actual_w, actual_h = bg.get_actual_size()
        print(f"[SceneRenderer] 背景图已绘制 ({actual_w:.1f}m x {actual_h:.1f}m)")
    
    def update_background_alpha(self, alpha: float):
        """更新背景图透明度"""
        if self.background_image:
            self.background_image.set_alpha(alpha)
            if self.background_artist:
                self.background_artist.set_alpha(alpha)
    
    def toggle_background_visibility(self, visible: bool):
        """切换背景图显示/隐藏"""
        if self.background_image:
            self.background_image.set_enabled(visible)
            if visible:
                self._draw_background()
            else:
                self._clear_category('background')
    
    def remove_background(self):
        """移除背景图"""
        self._clear_category('background')
        if self.background_image:
            self.background_image.clear()
        self.background_image = None
        self.background_artist = None
    
    def has_background_image(self) -> bool:
        """检查是否有背景图"""
        return self.background_image is not None and self.background_image.is_loaded()
    
    def get_background_image(self) -> Optional[BackgroundImage]:
        """获取当前背景图数据"""
        return self.background_image
    
    # ==================== 主渲染方法 ====================
    
    def render(self, model: SceneModel):
        """
        根据Model完全重新渲染场景
        
        V2.1: 集成LabelPlacer计算标签位置
        
        Args:
            model: 场景数据模型
        """
        # 缓存当前模型引用（用于拖拽时访问）
        self._current_model = model
        
        # 清除所有绑制对象
        self._clear_all()
        
        # 获取坐标范围
        x_range, y_range = model.coord_range
        
        # - V2.5 先绘制背景图（最底层 zorder=0）
        self._draw_background()
        
        # 绑制坐标系统
        self._draw_coordinate_system(x_range, y_range)
        
        # 绘制用户坐标系（如果有）
        if model.is_user_frame_active():
            user_pos = model.get_user_position()
            self._draw_user_coordinate_system(user_pos, x_range, y_range)
        
        # 绘制扇形（先绘制，因为标签布局需要避开扇形）
        for sector in model.get_sectors():
            self._draw_sector(sector)
        
        # 获取设备列表
        devices = model.get_devices()
        
        # V2.3: 使用4方向布局算法，保留手动设置的位置
        # 获取现有的标签位置（主要是手动设置的）
        label_positions = model.get_all_label_positions()
        
        # 绘制设备和标签（自动位置在_draw_devices中计算）
        self._draw_devices(devices, label_positions)
        
        # 绘制测量点
        measurement = model.get_measurement()
        if measurement:
            user_pos = model.get_user_position() if model.is_user_frame_active() else None
            self._draw_measurement(measurement, user_pos)
        
        # 刷新显示
        self.figure.canvas.draw_idle()
    
    def render_partial(self, model: SceneModel, parts: List[str]):
        """
        部分渲染（性能优化，只更新指定部分）
        
        Args:
            model: 场景数据模型
            parts: 要更新的部分列表 ['devices', 'measurement', 'sectors', 'crosshair']
        """
        x_range, y_range = model.coord_range
        
        if 'crosshair' in parts:
            self._clear_category('crosshair')
        
        if 'coordinate_info' in parts:
            self._clear_category('coordinate_info')
        
        if 'devices' in parts:
            self._clear_category('devices')
            devices = model.get_devices()
            label_positions = model.get_all_label_positions()
            self._draw_devices(devices, label_positions)
        
        if 'measurement' in parts:
            self._clear_category('measurement')
            measurement = model.get_measurement()
            if measurement:
                user_pos = model.get_user_position() if model.is_user_frame_active() else None
                self._draw_measurement(measurement, user_pos)
        
        if 'sectors' in parts:
            self._clear_category('sectors')
            for sector in model.get_sectors():
                self._draw_sector(sector)
        
        self.figure.canvas.draw_idle()
    
    # ==================== 坐标系绑制 ====================
    
    def _draw_coordinate_system(self, x_range: float, y_range: float):
        """
        绘制世界坐标系
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
        """
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
        
        # 绘制坐标轴
        h_axis = self.axes.axhline(y=0, color=self.COLORS['axis_line'], 
                                   linewidth=1.5, alpha=0.9, zorder=2)
        v_axis = self.axes.axvline(x=0, color=self.COLORS['axis_line'], 
                                   linewidth=1.5, alpha=0.9, zorder=2)
        self._artists['coordinate_system'].extend([h_axis, v_axis])
        
        # 设置背景色
        self.axes.set_facecolor(self.COLORS['background'])
        
        # 设置标签
        self.axes.set_xlabel('X 坐标', fontsize=12, color=self.COLORS['axis_line'])
        self.axes.set_ylabel('Y 坐标', fontsize=12, color=self.COLORS['axis_line'])
        
        # 设置相等的宽高比
        self.axes.set_aspect('equal', adjustable='box')
        
        # 说明：原点的“大蓝点”已移除（用户反馈：原始坐标系无需额外强调原点）
    
    def _draw_user_coordinate_system(self, user_pos: Tuple[float, float],
                                     x_range: float, y_range: float):
        """
        绘制用户坐标系（紫色网格和轴线）
        
        Args:
            user_pos: 用户位置 (x, y)
            x_range: X轴范围
            y_range: Y轴范围
        """
        x, y = user_pos
        
        # 绘制用户位置标记：正五边形（边长约4像素）
        # 正五边形外接圆半径约0.2个坐标单位，确保边长视觉效果约4像素
        pentagon = patches.RegularPolygon(
            (x, y), numVertices=5, radius=0.2,
            facecolor=self.COLORS['user_marker'],  # 紫色填充
            edgecolors='white',  # 白色边框
            linewidth=2, 
            zorder=15, 
            alpha=1.0,
            label='用户位置'
        )
        self.axes.add_patch(pentagon)
        self._artists['user_coordinate_system'].append(pentagon)
        
        # 绘制用户坐标系轴线（红色虚线）
        # 交互要求：线宽下降一半（与MatplotlibView一致）
        h_axis_main = self.axes.axhline(
            y=y, color=self.COLORS['user_axis'],
            linewidth=0.75, linestyle='--', alpha=0.85, zorder=6
        )
        v_axis_main = self.axes.axvline(
            x=x, color=self.COLORS['user_axis'],
            linewidth=0.75, linestyle='--', alpha=0.85, zorder=6
        )
        self._artists['user_coordinate_system'].extend([h_axis_main, v_axis_main])
        
        # 辅助轴线（更细更淡，用于增强层次）
        h_axis_aux = self.axes.axhline(
            y=y, color=self.COLORS['user_axis'],
            linewidth=0.25, linestyle='--', alpha=0.35, zorder=5
        )
        v_axis_aux = self.axes.axvline(
            x=x, color=self.COLORS['user_axis'],
            linewidth=0.25, linestyle='--', alpha=0.35, zorder=5
        )
        self._artists['user_coordinate_system'].extend([h_axis_aux, v_axis_aux])
        
        # 用户坐标系“原点标签”：固定显示在用户坐标点正下方2格（不随动）
        # 说明：这里的“不随动”指不做自动挪动/避让，位置严格为 (x, y-2.0)
        label_text = f'[用户] 位置\n({x:.1f}, {y:.1f})'
        text_x = x
        text_y = y - 2.0
        
        text = self.axes.text(
            text_x, text_y, label_text,
            # 字体/字号：与设备标签一致
            fontsize=9, fontweight='normal',
            color=self.COLORS['user_text'],
            ha='center', va='center', zorder=17,
            bbox=dict(
                boxstyle="round,pad=0.5",
                # 背景：60%透明度
                facecolor=(1.0, 1.0, 1.0, 0.6),
                edgecolor=self.COLORS['user_axis'],
                linewidth=1.5
            )
        )
        self._artists['user_coordinate_system'].append(text)
    
    # ==================== 设备绘制 ====================
    
    def _draw_devices(self, devices: List[Device], 
                      label_positions: Dict[str, LabelPosition]):
        """
        绘制设备点和标签，并注册点击检测区域
        
        V2.3: 
        - 设备点改为3x3方块
        - 标签简化为4个方向（上下左右各1个坐标单位）
        - 标签文字左对齐
        - 连接线从标签边缘中点连到设备点边缘中点
        - 支持设备自定义颜色
        
        Args:
            devices: 设备列表
            label_positions: 标签位置字典
        """
        for device in devices:
            # 获取设备颜色（如果有color属性则使用，否则使用默认红色）
            device_color = getattr(device, 'color', self.COLORS['device_point'])
            
            # 绘制设备点（7x7正方形标记）
            point = self.axes.scatter(
                [device.x], [device.y],
                c=device_color,
                s=49,  # 约7x7像素（s=49 -> 7x7像素）
                marker='s', zorder=5, alpha=1.0,
                edgecolors='white', linewidth=0.5
            )
            self._artists['devices'].append(point)
            
            # 获取标签位置
            element_id = f"device_{device.id}"
            label_pos = label_positions.get(element_id)
            
            # 获取标签尺寸
            label_width, label_height = self.LABEL_SIZES['device']
            
            if label_pos:
                # 使用已保存的位置（中心坐标）
                label_center_x, label_center_y = label_pos.x, label_pos.y
                direction = label_pos.direction if hasattr(label_pos, 'direction') else 'left'
                is_manual = label_pos.is_manual
            else:
                # 首次计算位置：使用4方向算法（返回中心坐标）
                label_center_x, label_center_y, direction = self._calculate_4direction_label_position(device.x, device.y)
                is_manual = False
                
                # 🆕 将自动计算的位置保存到model中，避免每次重新计算
                # 这样标签位置就固定了，除非用户手动拖拽调整
                if self._current_model:
                    self._current_model.set_label_position(
                        element_id=element_id,
                        x=label_center_x,
                        y=label_center_y,
                        is_manual=False,  # 标记为自动位置
                        direction=direction
                    )
            
            # - 转换为text对象需要的坐标
            # 由于ha='left'，text需要的是标签左边缘X坐标
            # va='center'，text需要的是标签中心Y坐标
            text_x = label_center_x - label_width/2  # 标签左边缘
            text_y = label_center_y  # 标签垂直中心
            
            # - 计算连接线端点（从标签边缘中点到设备点边缘中点）
            label_edge_x, label_edge_y, device_edge_x, device_edge_y = self._calculate_connection_points(
                device.x, device.y, label_center_x, label_center_y, direction
            )
            
            # - 短虚线引导线（线宽1px，短虚线样式）
            guide_line = self.axes.plot(
                [device_edge_x, label_edge_x], [device_edge_y, label_edge_y],
                color=device_color,
                linewidth=1.0,  # 1像素线宽
                linestyle=(0, (3, 2)),  # 短虚线样式：3px实线 + 2px空白
                alpha=0.6, zorder=4
            )[0]
            self._artists['devices'].append(guide_line)
            
            # - 多行格式标签文本（设备名 + X坐标 + Y坐标） - 左对齐
            label_text = f'{device.name}\nX: {device.x:.3f}\nY: {device.y:.3f}'
            
            # 手动位置使用蓝色边框，自动位置使用设备颜色边框
            border_color = '#1976d2' if is_manual else device_color
            
            # - 创建文本对象（加粗字体、多行格式、左对齐）
            text = self.axes.text(
                text_x, text_y, label_text,
                bbox=dict(
                    boxstyle='round,pad=0.4',  # 稍微增加内边距
                    facecolor='#ffffe0',  # 浅黄色背景
                    edgecolor=border_color,
                    alpha=0.95,
                    # 将默认线宽减半，手动位置略粗以便区分
                    linewidth=1.0 if is_manual else 0.75
                ),
                fontsize=9,
                fontweight='normal',  # 正常字重
                color=device_color,  # 使用设备颜色作为文字色
                zorder=6, 
                ha='left',  # - 水平左对齐
                va='center',  # 垂直居中
                multialignment='left'  # - 多行文本左对齐
            )
            self._artists['devices'].append(text)
            
            # 注册标签的点击检测区域（用于拖拽）
            # 传入标签中心坐标
            self.register_label_hitbox(element_id, label_center_x, label_center_y, 'device')
    
    def _calculate_4direction_label_position(self, anchor_x: float, anchor_y: float) -> Tuple[float, float, str]:
        """
        计算4方向标签位置（左、上、右、下 - 顺时针顺序）
        
        V3.2 调整：以“标签贴近锚点一格”的规则计算
        - 以设备标识点 (anchor_x, anchor_y) 为参考
        - 当标签在左侧时：标签右边缘中点坐标为 (anchor_x - 1, anchor_y)
        - 在右侧时：标签左边缘中点坐标为 (anchor_x + 1, anchor_y)
        - 在上侧时：标签下边缘中点坐标为 (anchor_x, anchor_y + 1)
        - 在下侧时：标签上边缘中点坐标为 (anchor_x, anchor_y - 1)
        
        也就是说，标签与设备点之间沿着对应轴方向恰好间隔 1 个坐标单位，
        然后再由此反推标签中心坐标。
        
        方向优先级（仅在发生碰撞或越界时才尝试下一方向）：
        1. 左侧
        2. 上侧
        3. 右侧
        4. 下侧
        
        Args:
            anchor_x: 锚点X坐标（设备点中心）
            anchor_y: 锚点Y坐标（设备点中心）
            
        Returns:
            (标签中心X, 标签中心Y, 方向标识)
        """
        # 标签尺寸（从LABEL_SIZES获取）
        label_width, label_height = self.LABEL_SIZES['device']
        
        # 根据“边中点相距 1 格”的规则，先确定标签靠近设备一侧的边中点坐标，
        # 再反推标签中心坐标
        candidates = [
            # 左方（默认）：标签右边缘中点在 (anchor_x - 1, anchor_y)
            # 因此标签中心的X坐标 = (anchor_x - 1) - label_width / 2
            (
                'left',
                anchor_x - 1.0 - label_width / 2.0,
                anchor_y
            ),
            
            # 上方：标签下边缘中点在 (anchor_x, anchor_y + 1)
            # 标签中心Y坐标 = (anchor_y + 1) + label_height / 2
            (
                'top',
                anchor_x,
                anchor_y + 1.0 + label_height / 2.0
            ),
            
            # 右方：标签左边缘中点在 (anchor_x + 1, anchor_y)
            # 标签中心X坐标 = (anchor_x + 1) + label_width / 2
            (
                'right',
                anchor_x + 1.0 + label_width / 2.0,
                anchor_y
            ),
            
            # 下方：标签上边缘中点在 (anchor_x, anchor_y - 1)
            # 标签中心Y坐标 = (anchor_y - 1) - label_height / 2
            (
                'bottom',
                anchor_x,
                anchor_y - 1.0 - label_height / 2.0
            ),
        ]
        
        # 获取坐标范围（用于边界检查）
        x_range = self.axes.get_xlim()
        y_range = self.axes.get_ylim()
        
        # 遍历候选位置，检查每个位置是否合适
        for direction, label_center_x, label_center_y in candidates:
            # 计算标签的实际边界（基于中心坐标）
            label_left_x = label_center_x - label_width/2
            label_right_x = label_center_x + label_width/2
            label_top_y = label_center_y + label_height/2
            label_bottom_y = label_center_y - label_height/2
            
            # 1. 边界检查：标签是否在画布范围内（留0.5单位余量）
            if not (x_range[0] + 0.5 <= label_left_x and 
                    label_right_x <= x_range[1] - 0.5 and
                    y_range[0] + 0.5 <= label_bottom_y and 
                    label_top_y <= y_range[1] - 0.5):
                continue  # 超出边界，尝试下一个位置
            
            # 2. 检查与扇形的碰撞（传入中心坐标）
            if self._check_label_sector_collision(label_center_x, label_center_y, label_width, label_height):
                continue  # 与扇形碰撞，尝试下一个位置
            
            # 3. 检查与其他标签的碰撞（传入中心坐标）
            if self._check_label_overlap(label_center_x, label_center_y, label_width, label_height):
                continue  # 与其他标签重叠，尝试下一个位置
            
            # 4. 检查与其他设备点的碰撞（传入中心坐标）
            if self._check_label_device_collision(label_center_x, label_center_y, label_width, label_height, anchor_x, anchor_y):
                continue  # 与其他设备点碰撞，尝试下一个位置
            
            # 所有检查通过，使用这个位置
            return (label_center_x, label_center_y, direction)
        
        # 如果所有位置都不合适，返回默认左侧位置
        return (candidates[0][1], candidates[0][2], 'left')
    
    def _check_label_sector_collision(self, label_center_x: float, label_center_y: float,
                                      label_width: float, label_height: float) -> bool:
        """
        检查标签是否与任何扇形区域重合
        
        Args:
            label_center_x: 标签中心X坐标
            label_center_y: 标签中心Y坐标
            label_width: 标签宽度
            label_height: 标签高度
            
        Returns:
            True表示有碰撞
        """
        if not self._current_model:
            return False
        
        # 计算标签的四个边缘中点和中心点
        label_left_x = label_center_x - label_width/2
        label_right_x = label_center_x + label_width/2
        label_top_y = label_center_y + label_height/2
        label_bottom_y = label_center_y - label_height/2
        
        check_points = [
            (label_left_x, label_center_y),  # 左边缘中点
            (label_right_x, label_center_y),  # 右边缘中点
            (label_center_x, label_top_y),  # 上边缘中点
            (label_center_x, label_bottom_y),  # 下边缘中点
            (label_center_x, label_center_y),  # 中心点
        ]
        
        # 获取所有扇形
        sectors = self._current_model.get_sectors()
        
        for sector in sectors:
            # 检查标签的关键点是否在扇形内
            for px, py in check_points:
                # 计算点到扇形圆心的距离
                dx = px - sector.center_x
                dy = py - sector.center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 在扇形半径范围内
                if distance <= sector.radius:
                    # 计算点的角度
                    angle_rad = math.atan2(dy, dx)
                    angle_deg = math.degrees(angle_rad)
                    
                    # 归一化到[0, 360)
                    while angle_deg < 0:
                        angle_deg += 360
                    while angle_deg >= 360:
                        angle_deg -= 360
                    
                    # 归一化扇形角度
                    start = sector.start_angle_deg % 360
                    end = sector.end_angle_deg % 360
                    if start < 0:
                        start += 360
                    if end < 0:
                        end += 360
                    
                    # 检查角度是否在扇形范围内
                    in_sector = False
                    if start <= end:
                        in_sector = start <= angle_deg <= end
                    else:
                        in_sector = angle_deg >= start or angle_deg <= end
                    
                    if in_sector:
                        return True  # 发现碰撞
        
        return False
    
    def _check_label_overlap(self, label_center_x: float, label_center_y: float,
                            label_width: float, label_height: float) -> bool:
        """
        检查标签是否与其他已存在的标签重叠
        
        Args:
            label_center_x: 标签中心X坐标
            label_center_y: 标签中心Y坐标
            label_width: 标签宽度
            label_height: 标签高度
            
        Returns:
            True表示有重叠
        """
        # 计算当前标签边界
        label_left_x = label_center_x - label_width/2
        label_right_x = label_center_x + label_width/2
        label_top_y = label_center_y + label_height/2
        label_bottom_y = label_center_y - label_height/2
        
        # 检查与已注册的标签hitbox的重叠
        for element_id, bbox in self._label_hitboxes.items():
            # 检查是否重叠（留0.2单位的安全距离）
            margin = 0.2
            if not (label_right_x + margin <= bbox.x_min or 
                   bbox.x_max + margin <= label_left_x or
                   label_top_y + margin <= bbox.y_min or 
                   bbox.y_max + margin <= label_bottom_y):
                return True  # 发现重叠
        
        return False
    
    def _check_label_device_collision(self, label_center_x: float, label_center_y: float,
                                     label_width: float, label_height: float,
                                     current_device_x: float, current_device_y: float) -> bool:
        """
        检查标签是否与其他设备点（不包括当前设备）重合
        
        Args:
            label_center_x: 标签中心X坐标
            label_center_y: 标签中心Y坐标
            label_width: 标签宽度
            label_height: 标签高度
            current_device_x: 当前设备X坐标（排除）
            current_device_y: 当前设备Y坐标（排除）
            
        Returns:
            True表示有碰撞
        """
        if not self._current_model:
            return False
        
        # 计算标签边界
        label_left_x = label_center_x - label_width/2
        label_right_x = label_center_x + label_width/2
        label_top_y = label_center_y + label_height/2
        label_bottom_y = label_center_y - label_height/2
        
        # 获取所有设备
        devices = self._current_model.get_devices()
        
        # 设备点尺寸
        device_size = 0.15
        device_radius = device_size / 2
        
        for device in devices:
            # 跳过当前设备
            if abs(device.x - current_device_x) < 0.01 and abs(device.y - current_device_y) < 0.01:
                continue
            
            # 检查设备点是否在标签区域内（留0.2单位安全距离）
            margin = 0.2
            if (label_left_x - margin <= device.x <= label_right_x + margin and
                label_bottom_y - margin <= device.y <= label_top_y + margin):
                return True  # 发现碰撞
        
        return False
    
    def _calculate_connection_points(self, device_x: float, device_y: float,
                                    label_center_x: float, label_center_y: float,
                                    direction: str) -> Tuple[float, float, float, float]:
        """
        计算连接线的两个端点坐标
        
        Args:
            device_x: 设备点中心X坐标
            device_y: 设备点中心Y坐标
            label_center_x: 标签中心X坐标
            label_center_y: 标签中心Y坐标
            direction: 标签方向 ('right', 'top', 'bottom', 'left')
            
        Returns:
            (label_edge_x, label_edge_y, device_edge_x, device_edge_y)
            标签边缘中点和设备边缘中点的坐标
        """
        # 标签尺寸
        label_width, label_height = self.LABEL_SIZES['device']
        
        # 设备点尺寸
        device_size = 0.15
        
        if direction == 'right':
            # 标签在右方：连接标签左边缘中点和设备右边缘中点
            label_edge_x = label_center_x - label_width/2  # 标签左边缘
            label_edge_y = label_center_y
            device_edge_x = device_x + device_size/2
            device_edge_y = device_y
            
        elif direction == 'left':
            # 标签在左方：连接标签右边缘中点和设备左边缘中点
            label_edge_x = label_center_x + label_width/2  # 标签右边缘
            label_edge_y = label_center_y
            device_edge_x = device_x - device_size/2
            device_edge_y = device_y
            
        elif direction == 'top':
            # 标签在上方：连接标签下边缘中点和设备上边缘中点
            label_edge_x = label_center_x  # 标签水平中点
            label_edge_y = label_center_y - label_height/2  # 标签下边缘
            device_edge_x = device_x
            device_edge_y = device_y + device_size/2
            
        else:  # direction == 'bottom'
            # 标签在下方：连接标签上边缘中点和设备下边缘中点
            label_edge_x = label_center_x  # 标签水平中点
            label_edge_y = label_center_y + label_height/2  # 标签上边缘
            device_edge_x = device_x
            device_edge_y = device_y - device_size/2
        
        return (label_edge_x, label_edge_y, device_edge_x, device_edge_y)
    
    # ==================== 测量点绘制 ====================
    
    def _draw_measurement(self, measurement: MeasurementData,
                          user_pos: Optional[Tuple[float, float]]):
        """
        绘制测量点和测量信息
        
        Args:
            measurement: 测量点数据
            user_pos: 用户位置（如果有）
        """
        x, y = measurement.x, measurement.y
        
        # 绘制测量点：直径约为6的圆点（Matplotlib中markersize为“直径（points）”）
        point = self.axes.plot(x, y, 'o',
                              color=self.COLORS['measurement_point'],
                              markersize=6, zorder=7)[0]
        self._artists['measurement'].append(point)
        
        # 根据坐标系模式绘制连线
        if user_pos:
            # 用户坐标系模式：绘制到用户位置的连线
            ux, uy = user_pos
            line = self.axes.plot([ux, x], [uy, y],
                                 color=self.COLORS['user_marker'],
                                 linewidth=2, alpha=0.8, zorder=4,
                                 linestyle='--')[0]
            self._artists['measurement'].append(line)
            
            # 使用用户坐标系信息
            info_text = self._format_measurement_info(measurement, use_user=True)
            coord_mode = "用户坐标系"
        else:
            # 世界坐标系模式：绘制到原点的连线
            line = self.axes.plot([0, x], [0, y],
                                 color=self.COLORS['measurement_line'],
                                 linewidth=2, alpha=0.7, zorder=4)[0]
            self._artists['measurement'].append(line)
            
            info_text = self._format_measurement_info(measurement, use_user=False)
            coord_mode = "世界坐标系"
        
        # 绘制测量信息框
        full_text = f"[{coord_mode}]\n{info_text}"
        
        # 坐标标签默认位置：在单击标记点正下方，下移2格（2个坐标单位）
        x_range, y_range = self._current_model.coord_range if self._current_model else (10.0, 10.0)
        text_x = x
        text_y = y - 2.0
        
        # 边界约束：避免标签超出画布（留0.5单位安全边距）
        margin = 0.5
        text_x = max(-x_range + margin, min(text_x, x_range - margin))
        text_y = max(-y_range + margin, min(text_y, y_range - margin))
        
        text = self.axes.text(
            text_x, text_y, full_text,
            bbox=dict(
                boxstyle='round,pad=0.5',
                # 标签底色：透明度60%（覆盖度0.6）
                facecolor=(1.0, 1.0, 1.0, 0.6),
                edgecolor=self.COLORS['label_border'],
                linewidth=1.5
            ),
            # 字体/字号：与设备标签说明文字一致
            fontsize=9,
            fontweight='normal',
            color=self.COLORS['text_color'],
            zorder=8, ha='center', va='center'
        )
        self._artists['measurement'].append(text)
    
    def _format_measurement_info(self, measurement: MeasurementData, use_user: bool) -> str:
        """
        格式化测量信息文本
        
        Args:
            measurement: 测量数据
            use_user: 是否使用用户坐标系
            
        Returns:
            格式化后的文本
        """
        if use_user and measurement.distance_to_user is not None:
            return (f"坐标: ({measurement.x:.3f}, {measurement.y:.3f})\n"
                   f"到用户距离: {measurement.distance_to_user:.3f}\n"
                   f"用户角度: {measurement.angle_to_user:.3f}°")
        else:
            return (f"坐标: ({measurement.x:.3f}, {measurement.y:.3f})\n"
                   f"到原点距离: {measurement.distance_to_origin:.3f}\n"
                   f"世界角度: {measurement.angle_to_origin:.3f}°")
    
    # ==================== 扇形绘制 ====================
    
    def _draw_sector(self, sector: SectorData):
        """
        绘制扇形区域
        
        Args:
            sector: 扇形数据
        """
        center_x, center_y = sector.center_x, sector.center_y
        radius = sector.radius
        start_angle_deg = sector.start_angle_deg
        end_angle_deg = sector.end_angle_deg
        
        # 创建扇形路径
        theta = np.linspace(
            math.radians(start_angle_deg),
            math.radians(end_angle_deg),
            50
        )
        x_sector = center_x + radius * np.cos(theta)
        y_sector = center_y + radius * np.sin(theta)
        
        # 添加中心点到扇形路径
        x_coords = np.concatenate([[center_x], x_sector, [center_x]])
        y_coords = np.concatenate([[center_y], y_sector, [center_y]])
        
        # 绘制填充扇形
        fill = self.axes.fill(x_coords, y_coords,
                             color=self.COLORS['sector_fill'],
                             alpha=0.3, zorder=2)[0]
        self._artists['sectors'].append(fill)
        
        # 绘制扇形边界
        edge = self.axes.plot(x_coords, y_coords,
                             color=self.COLORS['sector_edge'],
                             linewidth=2, zorder=3)[0]
        self._artists['sectors'].append(edge)
    
    # ==================== 十字光标绘制 ====================
    
    def draw_crosshair(self, x: float, y: float):
        """
        绘制十字光标
        
        Args:
            x: X坐标
            y: Y坐标
        """
        # 性能优化：如果位置没变化，不重绘
        if self._last_crosshair_pos == (x, y):
            return
        
        # 清除之前的十字光标
        self._clear_category('crosshair')
        
        # 绘制垂直线和水平线
        vline = self.axes.axvline(x=x, color=self.COLORS['crosshair'],
                                  linewidth=0.8, alpha=0.6, zorder=1)
        hline = self.axes.axhline(y=y, color=self.COLORS['crosshair'],
                                  linewidth=0.8, alpha=0.6, zorder=1)
        
        self._artists['crosshair'].extend([vline, hline])
        self._last_crosshair_pos = (x, y)
    
    def clear_crosshair(self):
        """清除十字光标"""
        self._clear_category('crosshair')
        self._last_crosshair_pos = None
    
    # ==================== 坐标信息绘制 ====================
    
    def draw_coordinate_info(self, x: float, y: float, model: SceneModel):
        """
        绘制鼠标悬停时的坐标信息
        
        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标
            model: 场景模型
        """
        # 交互调整：不再显示任何“随动坐标信息框”（世界/用户坐标系都关闭）
        # 清除可能残留的对象，并直接返回
        self.clear_coordinate_info()
        return
        
        # 构建坐标信息文本（仅用户坐标系模式）
        if model.is_user_frame_active():
            user_pos = model.get_user_position()
            ux, uy = user_pos
            rel_x, rel_y = x - ux, y - uy
            rel_distance = math.sqrt(rel_x**2 + rel_y**2)
            
            info_text = (
                f"[世界] 坐标: ({x:.2f}, {y:.2f})\n"
                f"[用户] 坐标: ({rel_x:.2f}, {rel_y:.2f})\n"
                f"[距离] 到用户: {rel_distance:.2f}"
            )
            text_color = '#4a148c'
            bg_color = '#f8f4ff'
        
        # 性能优化：内容没变化就不重绘
        if info_text == self._last_coord_info_text:
            return
        
        self._last_coord_info_text = info_text
        self._clear_category('coordinate_info')
        
        # 计算信息框位置
        x_range, y_range = model.coord_range
        info_x = x - 2.0 if x > x_range * 0.6 else x + 0.8
        info_y = y - 1.5 if y > y_range * 0.6 else y + 0.8
        
        # 确保不超出边界
        info_x = max(-x_range + 0.5, min(info_x, x_range - 2.5))
        info_y = max(-y_range + 0.5, min(info_y, y_range - 1.5))
        
        # 绘制坐标信息框
        annotation = self.axes.annotate(
            info_text,
            xy=(x, y),
            xytext=(info_x, info_y),
            bbox=dict(
                boxstyle='round,pad=0.6',
                facecolor=bg_color,
                edgecolor=text_color,
                linewidth=2, alpha=0.95
            ),
            fontsize=10, fontweight='normal',
            color=text_color, zorder=15, ha='left',
            arrowprops=dict(
                arrowstyle='->',
                color=text_color,
                alpha=0.7, lw=1.5
            )
        )
        self._artists['coordinate_info'].append(annotation)
    
    def clear_coordinate_info(self):
        """清除坐标信息"""
        self._clear_category('coordinate_info')
        self._last_coord_info_text = ""
    
    # ==================== 导出功能 ====================
    
    def export_to_png(self, file_path: str, dpi: int = 300) -> bool:
        """
        导出为PNG图片
        
        Args:
            file_path: 保存路径
            dpi: 分辨率
            
        Returns:
            是否导出成功
        """
        try:
            original_dpi = self.figure.get_dpi()
            self.figure.set_dpi(dpi)
            
            self.figure.savefig(
                file_path, dpi=dpi, bbox_inches='tight',
                facecolor=self.COLORS['background'],
                edgecolor='none', format='png'
            )
            
            self.figure.set_dpi(original_dpi)
            print(f"[SceneRenderer] PNG导出成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"[SceneRenderer] PNG导出失败: {e}")
            return False
    
    # ==================== 清除方法 ====================
    
    def _clear_category(self, category: str):
        """
        清除指定类别的绑制对象
        
        Args:
            category: 类别名称
        """
        if category not in self._artists:
            return
        
        for artist in self._artists[category]:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass
        self._artists[category].clear()
    
    def _clear_all(self):
        """清除所有绘制对象"""
        for category in self._artists:
            self._clear_category(category)
        
        # 清除标签hitbox映射
        self._label_hitboxes.clear()
        
        # 清除Axes上的所有内容
        self.axes.clear()
    
    # ==================== 拖拽功能 ====================
    
    def set_drag_enabled(self, enabled: bool):
        """
        启用或禁用标签拖拽功能
        
        Args:
            enabled: True启用，False禁用
        """
        self._drag_enabled = enabled
        print(f"[SceneRenderer] 标签拖拽功能: {'启用' if enabled else '禁用'}")
    
    def set_label_drag_callback(self, callback: Callable[[str, float, float], None]):
        """
        设置标签拖拽回调（拖拽过程中持续调用）
        
        Args:
            callback: 回调函数 (element_id, new_x, new_y)
        """
        self._on_label_drag_callback = callback
    
    def set_drag_start_callback(self, callback: Callable[[str], None]):
        """
        设置拖拽开始回调
        
        Args:
            callback: 回调函数 (element_id)
        """
        self._on_drag_start_callback = callback
    
    def set_drag_end_callback(self, callback: Callable[[str, float, float], None]):
        """
        设置拖拽结束回调（用于持久化手动位置）
        
        Args:
            callback: 回调函数 (element_id, final_x, final_y)
        """
        self._on_drag_end_callback = callback
    
    def bind_drag_events(self):
        """
        绑定拖拽事件到Figure画布
        
        应该在初始化完成后调用一次。
        """
        self.figure.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.figure.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        self.figure.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        print("[SceneRenderer] 拖拽事件已绑定")
    
    def _on_mouse_press(self, event):
        """
        处理鼠标按下事件 - 检测是否点击了标签
        
        左键: 开始拖拽
        右键: 重置标签位置为自动计算
        
        Args:
            event: Matplotlib鼠标事件
        """
        if not self._drag_enabled:
            return
        
        # 确保在坐标轴内
        if event.inaxes != self.axes:
            return
        
        if event.xdata is None or event.ydata is None:
            return
        
        # 检测是否点击了某个标签
        clicked_label = self._find_label_at(event.xdata, event.ydata)
        
        if event.button == 1:  # 左键 - 拖拽
            if clicked_label:
                self._dragging_label = clicked_label
                self._drag_start_pos = (event.xdata, event.ydata)
                
                # 获取标签当前位置，计算偏移
                label_box = self._label_hitboxes.get(clicked_label)
                if label_box:
                    center_x, center_y = label_box.center()
                    self._drag_offset = (center_x - event.xdata, center_y - event.ydata)
                else:
                    self._drag_offset = (0, 0)
                
                # 显示拖拽高亮
                self._show_drag_highlight(clicked_label)
                
                # 修改光标为移动光标
                self._set_cursor('move')
                
                # 触发开始回调
                if self._on_drag_start_callback:
                    self._on_drag_start_callback(clicked_label)
                
                print(f"[SceneRenderer] 开始拖拽标签: {clicked_label}")
        
        elif event.button == 3:  # 右键 - 重置标签位置
            if clicked_label:
                self._reset_label_to_auto(clicked_label)
                print(f"[SceneRenderer] 重置标签位置: {clicked_label}")
    
    def _reset_label_to_auto(self, element_id: str):
        """
        重置指定标签为自动计算位置
        
        Args:
            element_id: 标签ID
        """
        if self._current_model:
            self._current_model.reset_label_to_auto(element_id)
            # 重新渲染
            self.render(self._current_model)
    
    def _on_mouse_motion(self, event):
        """
        处理鼠标移动事件 - 更新拖拽中的标签位置
        
        Args:
            event: Matplotlib鼠标事件
        """
        if not self._drag_enabled:
            return
        
        # 如果正在拖拽
        if self._dragging_label and event.xdata is not None and event.ydata is not None:
            # 计算新位置
            new_x = event.xdata + self._drag_offset[0]
            new_y = event.ydata + self._drag_offset[1]
            
            # 更新标签位置的视觉显示（实时）
            self._update_drag_visual(self._dragging_label, new_x, new_y)
            
            # 触发拖拽回调
            if self._on_label_drag_callback:
                self._on_label_drag_callback(self._dragging_label, new_x, new_y)
        else:
            # 非拖拽状态，检测鼠标是否在标签上方，改变光标
            if event.inaxes == self.axes and event.xdata is not None and event.ydata is not None:
                if self._find_label_at(event.xdata, event.ydata):
                    self._set_cursor('hand')
                else:
                    self._set_cursor('arrow')
    
    def _on_mouse_release(self, event):
        """
        处理鼠标释放事件 - 完成拖拽
        
        Args:
            event: Matplotlib鼠标事件
        """
        if not self._drag_enabled:
            return
        
        if self._dragging_label:
            # 计算最终位置
            if event.xdata is not None and event.ydata is not None:
                final_x = event.xdata + self._drag_offset[0]
                final_y = event.ydata + self._drag_offset[1]
            else:
                # 如果鼠标在画布外释放，使用起始位置
                final_x, final_y = self._drag_start_pos if self._drag_start_pos else (0, 0)
            
            # 清除拖拽高亮
            self._clear_drag_highlight()
            
            # 触发结束回调（用于持久化）
            if self._on_drag_end_callback:
                self._on_drag_end_callback(self._dragging_label, final_x, final_y)
            
            print(f"[SceneRenderer] 完成拖拽标签: {self._dragging_label} -> ({final_x:.3f}, {final_y:.3f})")
            
            # 重置拖拽状态
            self._dragging_label = None
            self._drag_start_pos = None
            self._drag_offset = (0, 0)
            
            # 恢复光标
            self._set_cursor('arrow')
    
    def _find_label_at(self, x: float, y: float) -> Optional[str]:
        """
        查找指定坐标位置的标签
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            标签的element_id，如果没有找到返回None
        """
        for element_id, bbox in self._label_hitboxes.items():
            if bbox.contains_point(x, y):
                return element_id
        return None
    
    def _show_drag_highlight(self, element_id: str):
        """
        显示拖拽高亮效果（增强版）
        
        Args:
            element_id: 被拖拽的标签ID
        """
        self._clear_category('drag_highlight')
        
        bbox = self._label_hitboxes.get(element_id)
        if not bbox:
            return
        
        # 绘制高亮边框
        width = bbox.x_max - bbox.x_min
        height = bbox.y_max - bbox.y_min
        
        # 外层光晕效果
        glow_rect = patches.Rectangle(
            (bbox.x_min - 0.15, bbox.y_min - 0.15),
            width + 0.3, height + 0.3,
            linewidth=6,
            edgecolor='#64b5f6',  # 浅蓝色光晕
            facecolor='#e3f2fd',  # 浅蓝色半透明背景
            linestyle='-',
            alpha=0.3,
            zorder=99
        )
        self.axes.add_patch(glow_rect)
        self._artists['drag_highlight'].append(glow_rect)
        
        # 主高亮边框（动态虚线）
        highlight_rect = patches.Rectangle(
            (bbox.x_min - 0.1, bbox.y_min - 0.1),
            width + 0.2, height + 0.2,
            linewidth=2.5,
            edgecolor='#1976d2',  # 蓝色高亮
            facecolor='none',
            linestyle='--',
            alpha=0.9,
            zorder=100
        )
        self.axes.add_patch(highlight_rect)
        self._artists['drag_highlight'].append(highlight_rect)
        
        # 角标指示器（四个角的小圆点）
        corners = [
            (bbox.x_min, bbox.y_min),
            (bbox.x_max, bbox.y_min),
            (bbox.x_min, bbox.y_max),
            (bbox.x_max, bbox.y_max),
        ]
        for cx, cy in corners:
            corner_dot = self.axes.scatter(
                [cx], [cy],
                c='#1976d2',
                s=30,
                marker='s',
                zorder=101,
                alpha=0.9
            )
            self._artists['drag_highlight'].append(corner_dot)
        
        self.figure.canvas.draw_idle()
    
    def _clear_drag_highlight(self):
        """清除拖拽高亮效果"""
        self._clear_category('drag_highlight')
        self.figure.canvas.draw_idle()
    
    def _update_drag_visual(self, element_id: str, new_x: float, new_y: float):
        """
        更新拖拽中的标签视觉位置（实时预览）
        
        Args:
            element_id: 标签ID
            new_x: 新的X坐标（标签中心）
            new_y: 新的Y坐标（标签中心）
        """
        # 更新hitbox位置
        old_bbox = self._label_hitboxes.get(element_id)
        if old_bbox:
            width = old_bbox.width()
            height = old_bbox.height()
            self._label_hitboxes[element_id] = BoundingBox.from_center(
                new_x, new_y, width, height
            )
        
        # 更新高亮位置
        if self._artists['drag_highlight']:
            rect = self._artists['drag_highlight'][0]
            if old_bbox:
                width = old_bbox.width()
                height = old_bbox.height()
                rect.set_xy((new_x - width/2 - 0.1, new_y - height/2 - 0.1))
        
        # 获取标签尺寸
        label_width, label_height = self.LABEL_SIZES['device']
        # 计算新的文本位置（标签左边缘，因为 ha='left'）
        new_text_x = new_x - label_width / 2
        new_text_y = new_y
        
        # 找到对应的文本对象和引导线并更新位置
        text_found = False
        guide_line_to_update = None
        
        for artist in self._artists['devices']:
            if hasattr(artist, 'get_text') and hasattr(artist, 'set_position'):
                # 这是文本对象，检查是否是目标
                # 通过位置近似匹配
                if old_bbox and not text_found:
                    old_center = old_bbox.center()
                    pos = artist.get_position()
                    # 检查文本位置是否接近旧标签的左边缘（因为 ha='left'）
                    old_text_x = old_center[0] - label_width / 2
                    if abs(pos[0] - old_text_x) < 0.5 and abs(pos[1] - old_center[1]) < 0.5:
                        artist.set_position((new_text_x, new_text_y))
                        text_found = True
        
        # 更新引导线
        self._update_guide_line_for_label(element_id, new_x, new_y, old_bbox)
        
        self.figure.canvas.draw_idle()
    
    def _update_guide_line_for_label(self, element_id: str, label_center_x: float, 
                                      label_center_y: float, old_bbox: Optional[BoundingBox]):
        """
        更新指定标签的引导线位置
        
        Args:
            element_id: 标签ID（格式：device_{device_id}）
            label_center_x: 标签新的中心X坐标
            label_center_y: 标签新的中心Y坐标
            old_bbox: 标签的旧边界框
        """
        if not old_bbox or not self._current_model:
            return
        
        # 从 element_id 中提取 device_id
        if not element_id.startswith('device_'):
            return
        device_id = element_id[7:]  # 去掉 'device_' 前缀
        
        # 获取设备信息
        device = self._current_model.get_device_by_id(device_id)
        if not device:
            return
        
        # 计算新的引导线方向（基于标签相对于设备的位置）
        dx = label_center_x - device.x
        dy = label_center_y - device.y
        
        # 根据相对位置确定方向
        if abs(dx) > abs(dy):
            direction = 'right' if dx > 0 else 'left'
        else:
            direction = 'top' if dy > 0 else 'bottom'
        
        # 计算新的连接点
        label_edge_x, label_edge_y, device_edge_x, device_edge_y = self._calculate_connection_points(
            device.x, device.y, label_center_x, label_center_y, direction
        )
        
        # 查找并更新对应的引导线
        old_center = old_bbox.center()
        for artist in self._artists['devices']:
            # 引导线是 Line2D 对象，检查是否是引导线（有 get_xdata 方法但没有 get_text 方法）
            if hasattr(artist, 'get_xdata') and hasattr(artist, 'set_data') and not hasattr(artist, 'get_text'):
                try:
                    xdata = artist.get_xdata()
                    ydata = artist.get_ydata()
                    
                    # 检查这条线是否连接到旧标签位置附近
                    if len(xdata) == 2 and len(ydata) == 2:
                        # 引导线的两个端点：一个是设备边缘，一个是标签边缘
                        # 检查是否有一个端点接近设备位置
                        for i in range(2):
                            if abs(xdata[i] - device.x) < 0.3 and abs(ydata[i] - device.y) < 0.3:
                                # 这条线连接到目标设备，更新它
                                artist.set_data(
                                    [device_edge_x, label_edge_x],
                                    [device_edge_y, label_edge_y]
                                )
                                return
                except Exception:
                    # 忽略无法处理的 artist
                    pass
    
    def _set_cursor(self, cursor_type: str):
        """
        设置鼠标光标
        
        Args:
            cursor_type: 'arrow', 'hand', 'move' 等
        """
        try:
            canvas = self.figure.canvas
            
            if cursor_type == 'hand':
                canvas.set_cursor(1)  # HAND_CURSOR
            elif cursor_type == 'move':
                canvas.set_cursor(2)  # MOVE_CURSOR  
            else:  # 'arrow' 或其他
                canvas.set_cursor(0)  # ARROW_CURSOR
        except Exception:
            # 某些后端可能不支持设置光标
            pass
    
    def get_label_placer(self) -> LabelPlacer:
        """获取标签布局服务实例"""
        return self._label_placer
    
    def calculate_label_positions(self, model: SceneModel) -> Dict[str, LabelPosition]:
        """
        使用LabelPlacer计算所有标签的最佳位置
        
        Args:
            model: 场景数据模型
            
        Returns:
            element_id -> LabelPosition 的映射
        """
        # 转换设备数据
        devices = []
        for device in model.get_devices():
            devices.append(DeviceAnchor(
                device_id=device.id,
                x=device.x,
                y=device.y,
                name=device.name
            ))
        
        # 转换扇形数据
        sectors = []
        for sector in model.get_sectors():
            sectors.append(SectorObstacle(
                center_x=sector.center_x,
                center_y=sector.center_y,
                radius=sector.radius,
                start_angle_deg=sector.start_angle_deg,
                end_angle_deg=sector.end_angle_deg
            ))
        
        # 获取手动位置
        manual_positions = model.get_manual_label_positions()
        
        # 计算位置
        return self._label_placer.calculate_positions(
            devices=devices,
            sectors=sectors,
            coord_range=model.coord_range,
            existing_manual=manual_positions
        )
    
    def register_label_hitbox(self, element_id: str, center_x: float, center_y: float,
                              label_type: str = 'device'):
        """
        注册标签的点击检测区域
        
        Args:
            element_id: 标签ID
            center_x: 标签中心X坐标
            center_y: 标签中心Y坐标
            label_type: 标签类型
        """
        width, height = self.LABEL_SIZES.get(label_type, (2.0, 0.8))
        self._label_hitboxes[element_id] = BoundingBox.from_center(
            center_x, center_y, width, height
        )
