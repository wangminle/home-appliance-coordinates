# -*- coding: utf-8 -*-
"""
导出功能工具模块

提供PNG图像导出、文件保存等功能
"""

import os
import datetime
from typing import Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk


class ExportUtils:
    """
    导出功能工具类
    
    提供Canvas内容导出为PNG图像等功能
    """
    
    # 默认导出参数
    DEFAULT_EXPORT_WIDTH = 1920
    DEFAULT_EXPORT_HEIGHT = 1920
    DEFAULT_DPI = 300
    
    @staticmethod
    def generate_default_filename() -> str:
        """
        生成默认的导出文件名
        
        Returns:
            默认文件名，格式：家居设备布局图_YYYYMMDD_HHMMSS.png
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"家居设备布局图_{timestamp}.png"
    
    @staticmethod
    def get_default_save_directory() -> str:
        """
        获取默认保存目录
        
        Returns:
            默认保存目录路径（用户文档目录）
        """
        # 尝试获取用户文档目录
        try:
            import os
            if os.name == 'nt':  # Windows
                documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
            else:  # macOS/Linux
                documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
            
            # 如果文档目录不存在，使用用户主目录
            if not os.path.exists(documents_dir):
                documents_dir = os.path.expanduser('~')
            
            return documents_dir
        except Exception:
            # 如果出错，返回当前目录
            return os.getcwd()
    
    @staticmethod
    def create_high_resolution_canvas(width: int = None, height: int = None, 
                                    background_color: str = "#e0f7fa") -> Tuple[Image.Image, ImageDraw.Draw]:
        """
        创建高分辨率的PIL图像用于导出
        
        Args:
            width: 图像宽度，默认使用DEFAULT_EXPORT_WIDTH
            height: 图像高度，默认使用DEFAULT_EXPORT_HEIGHT
            background_color: 背景颜色，默认浅蓝色
            
        Returns:
            (PIL Image对象, ImageDraw对象)
        """
        if width is None:
            width = ExportUtils.DEFAULT_EXPORT_WIDTH
        if height is None:
            height = ExportUtils.DEFAULT_EXPORT_HEIGHT
        
        # 创建RGB图像
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        return image, draw
    
    @staticmethod
    def draw_view_on_image(canvas_view: 'CanvasView') -> Optional[Image.Image]:
        """
        在一个新的PIL图像上重新绘制整个CanvasView的内容。
        这是实现高清导出的核心方法。

        Args:
            canvas_view: CanvasView的实例，用于获取所有绘制所需的数据。

        Returns:
            一个包含所有内容的新的PIL.Image对象，如果失败则返回None。
        """
        try:
            # 1. 创建高分辨率图像画布
            export_width = ExportUtils.DEFAULT_EXPORT_WIDTH
            export_height = ExportUtils.DEFAULT_EXPORT_HEIGHT
            image, draw = ExportUtils.create_high_resolution_canvas(
                export_width, export_height, canvas_view.COLORS['background']
            )

            # 2. 创建一个临时的、用于导出的坐标系统实例
            # 这确保了所有坐标转换都是针对高清大图的尺寸
            from models.coordinate_model import CoordinateSystem
            export_coord_system = CoordinateSystem(
                x_range=canvas_view.coordinate_system.x_range,
                y_range=canvas_view.coordinate_system.y_range,
                canvas_width=export_width,
                canvas_height=export_height,
                padding=canvas_view.coordinate_system.padding * (export_width / canvas_view.CANVAS_WIDTH)
            )

            # 3. 绘制所有元素
            ExportUtils._draw_grid(draw, export_coord_system, canvas_view.COLORS)
            ExportUtils._draw_axes(draw, export_coord_system, canvas_view.COLORS)
            ExportUtils._draw_tick_labels(draw, export_coord_system, canvas_view.COLORS)
            ExportUtils._draw_origin(draw, export_coord_system, canvas_view.COLORS)
            ExportUtils._draw_devices(draw, export_coord_system, canvas_view.get_devices(), canvas_view.COLORS)
            
            if canvas_view.get_measurement_point():
                ExportUtils._draw_measurement(draw, export_coord_system, canvas_view.get_measurement_point(), canvas_view.COLORS)

            return image

        except Exception as e:
            print(f"在PIL图像上绘制视图失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    # --- 以下是绘制辅助方法 ---

    @staticmethod
    def _draw_grid(draw: ImageDraw.Draw, coord: 'CoordinateSystem', colors: dict):
        vertical_lines, horizontal_lines = coord.get_grid_lines()
        for line in vertical_lines + horizontal_lines:
            draw.line(line, fill=colors['grid_line'], width=2)

    @staticmethod
    def _draw_axes(draw: ImageDraw.Draw, coord: 'CoordinateSystem', colors: dict):
        x_axis, y_axis = coord.get_axis_lines()
        draw.line(x_axis, fill=colors['axis_line'], width=4)
        draw.line(y_axis, fill=colors['axis_line'], width=4)

    @staticmethod
    def _draw_tick_labels(draw: ImageDraw.Draw, coord: 'CoordinateSystem', colors: dict):
        x_ticks, y_ticks = coord.get_tick_labels()
        font = ExportUtils.get_system_font(30, "normal")
        for tick in x_ticks + y_ticks:
            pos = tick['pos']
            text = tick['text']
            draw.text(pos, text, fill=colors['text_color'], font=font, anchor=tick.get('anchor', 'ms'))

    @staticmethod
    def _draw_origin(draw: ImageDraw.Draw, coord: 'CoordinateSystem', colors: dict):
        origin_x, origin_y = coord.get_origin_position()
        radius = 8
        draw.ellipse(
            (origin_x - radius, origin_y - radius, origin_x + radius, origin_y + radius),
            fill=colors['origin_point'], outline=colors['origin_point']
        )

    @staticmethod
    def _draw_devices(draw: ImageDraw.Draw, coord: 'CoordinateSystem', devices: list, colors: dict):
        for device in devices:
            ExportUtils._draw_single_device(draw, coord, device, colors)

    @staticmethod
    def _draw_single_device(draw: ImageDraw.Draw, coord: 'CoordinateSystem', device: 'Device', colors: dict):
        canvas_x, canvas_y = coord.to_canvas_coords(device.x, device.y)
        radius = 12
        draw.ellipse(
            (canvas_x - radius, canvas_y - radius, canvas_x + radius, canvas_y + radius),
            fill=colors['device_point'], outline=colors['device_point']
        )
        
        # 绘制标签
        label_text = f"{device.name}\n({device.x:.3f}, {device.y:.3f})"
        font = ExportUtils.get_system_font(28, "bold")
        
        # 使用textbbox计算精确尺寸
        bbox = draw.textbbox((0,0), label_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 10
        box_width = text_width + 2 * padding
        box_height = text_height + 2 * padding
        
        label_x = canvas_x
        label_y = canvas_y - radius - (box_height / 2) - 10
        if label_y - (box_height / 2) < 0:
            label_y = canvas_y + radius + (box_height / 2) + 10
            
        draw.rectangle(
            (label_x - box_width / 2, label_y - box_height / 2, label_x + box_width / 2, label_y + box_height / 2),
            fill=colors['label_bg'], outline=colors['label_border'], width=2
        )
        draw.text((label_x, label_y), label_text, fill=colors['text_color'], font=font, anchor="mm", align="center")

    @staticmethod
    def _draw_measurement(draw: ImageDraw.Draw, coord: 'CoordinateSystem', point: 'MeasurementPoint', colors: dict):
        canvas_x, canvas_y = coord.to_canvas_coords(point.x, point.y)
        radius = 8
        draw.ellipse(
            (canvas_x - radius, canvas_y - radius, canvas_x + radius, canvas_y + radius),
            fill=colors['measurement_point'], outline=colors['measurement_point']
        )
        
        origin_x, origin_y = coord.get_origin_position()
        draw.line((origin_x, origin_y, canvas_x, canvas_y), fill=colors['measurement_line'], width=4)
        
        # 绘制信息框
        info_lines = point.get_info_lines(3)
        font = ExportUtils.get_system_font(28, "bold")
        
        # 找到最长的一行来计算宽度
        max_line_width = 0
        for line in info_lines:
            bbox = draw.textbbox((0,0), line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width > max_line_width:
                max_line_width = line_width

        padding = 15
        box_width = max_line_width + 2 * padding
        box_height = len(info_lines) * (font.size + 10) + padding
        
        info_x = canvas_x + 30
        info_y = canvas_y
        
        if info_x + box_width > coord.canvas_width - 20:
            info_x = canvas_x - box_width - 30
        if info_y + box_height > coord.canvas_height - 20:
            info_y = coord.canvas_height - box_height - 20
        if info_y < 20:
            info_y = 20
            
        draw.rectangle(
            (info_x, info_y, info_x + box_width, info_y + box_height),
            fill=colors['label_bg'], outline=colors['label_border'], width=2
        )
        
        for i, line in enumerate(info_lines):
            draw.text((info_x + padding, info_y + padding + i * (font.size + 10)), line, fill=colors['text_color'], font=font, anchor="ls")

    @staticmethod
    def export_canvas_to_pil(canvas: tk.Canvas, export_width: int = None, 
                           export_height: int = None) -> Optional[Image.Image]:
        """
        将Tkinter Canvas内容导出为PIL图像
        
        Args:
            canvas: Tkinter Canvas对象
            export_width: 导出图像宽度
            export_height: 导出图像高度
            
        Returns:
            PIL Image对象，如果失败则返回None
        """
        try:
            # 获取Canvas的实际尺寸
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if export_width is None:
                export_width = ExportUtils.DEFAULT_EXPORT_WIDTH
            if export_height is None:
                export_height = ExportUtils.DEFAULT_EXPORT_HEIGHT
            
            # 计算缩放比例
            scale_x = export_width / canvas_width
            scale_y = export_height / canvas_height
            
            # 创建高分辨率图像
            image, draw = ExportUtils.create_high_resolution_canvas(export_width, export_height)
            
            # 这里需要重新绘制Canvas内容到PIL图像
            # 由于Tkinter Canvas无法直接转换为PIL图像，
            # 我们需要在实际实现时重新绘制所有元素
            
            return image
            
        except Exception as e:
            print(f"导出Canvas到PIL图像失败: {e}")
            return None
    
    @staticmethod
    def save_image_to_file(image: Image.Image, file_path: str, quality: int = 95) -> bool:
        """
        保存PIL图像到文件
        
        Args:
            image: PIL Image对象
            file_path: 保存路径
            quality: 图像质量（0-100）
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 保存PNG图像
            image.save(file_path, 'PNG', optimize=True)
            return True
            
        except Exception as e:
            print(f"保存图像文件失败: {e}")
            return False
    
    @staticmethod
    def get_file_save_path(parent_window: tk.Tk = None, default_filename: str = None) -> Optional[str]:
        """
        显示文件保存对话框
        
        Args:
            parent_window: 父窗口
            default_filename: 默认文件名
            
        Returns:
            用户选择的文件路径，如果取消则返回None
        """
        try:
            from tkinter import filedialog
            
            if default_filename is None:
                default_filename = ExportUtils.generate_default_filename()
            
            # 显示保存对话框
            file_path = filedialog.asksaveasfilename(
                parent=parent_window,
                title="保存图像文件",
                defaultextension=".png",
                filetypes=[("PNG图像", "*.png"), ("所有文件", "*.*")],
                initialdir=ExportUtils.get_default_save_directory(),
                initialfile=default_filename
            )
            
            return file_path if file_path else None
            
        except Exception as e:
            print(f"显示文件保存对话框失败: {e}")
            return None
    
    @staticmethod
    def get_system_font(font_size: int = 12, font_weight: str = "normal") -> Optional[ImageFont.FreeTypeFont]:
        """
        获取系统字体
        
        Args:
            font_size: 字体大小
            font_weight: 字体粗细 ("normal" 或 "bold")
            
        Returns:
            ImageFont对象，如果获取失败则返回None
        """
        try:
            # 尝试使用系统默认字体
            font_paths = []
            
            # Windows字体
            if os.name == 'nt':
                font_paths.extend([
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                    "C:/Windows/Fonts/arial.ttf",   # Arial
                ])
            
            # macOS字体
            elif os.name == 'posix' and os.uname().sysname == 'Darwin':
                font_paths.extend([
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/Arial.ttf",
                ])
            
            # Linux字体
            else:
                font_paths.extend([
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ])
            
            # 尝试加载字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, font_size)
                    except Exception:
                        continue
            
            # 如果都失败，使用默认字体
            return ImageFont.load_default()
            
        except Exception:
            return None
    
    @staticmethod
    def calculate_text_size(text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """
        计算文本尺寸
        
        Args:
            text: 文本内容
            font: 字体对象
            
        Returns:
            文本尺寸 (width, height)
        """
        try:
            # PIL 10.0.0以后版本使用textbbox
            bbox = font.getbbox(text)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except AttributeError:
            # 旧版本PIL使用textsize
            return font.getsize(text)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小为易读格式
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化后的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def validate_export_parameters(width: int, height: int) -> Tuple[bool, str]:
        """
        验证导出参数的有效性
        
        Args:
            width: 导出宽度
            height: 导出高度
            
        Returns:
            (是否有效, 错误信息)
        """
        if width <= 0 or height <= 0:
            return False, "导出尺寸必须大于0"
        
        if width > 10000 or height > 10000:
            return False, "导出尺寸过大，可能导致内存不足"
        
        # 计算估计的内存使用量（RGB图像，每像素3字节）
        estimated_memory = width * height * 3
        max_memory = 500 * 1024 * 1024  # 500MB
        
        if estimated_memory > max_memory:
            return False, f"导出图像过大，估计需要{ExportUtils.format_file_size(estimated_memory)}内存"
        
        return True, "" 