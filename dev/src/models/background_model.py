# -*- coding: utf-8 -*-
"""
背景图片数据模型 V2

用于管理户型图背景的位置、缩放和显示属性
支持像素比例映射和中心对齐

功能：
- 加载 PNG/JPG 格式图片
- 基于像素比例映射到世界坐标系
- 自动中心对齐
- 支持项目文件持久化（Base64嵌入或路径引用）
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import numpy as np
import base64
from pathlib import Path
import io


class BackgroundImage:
    """
    背景图片数据类 V2
    
    支持像素比例映射和中心对齐
    """
    
    def __init__(self):
        """初始化背景图片对象"""
        # === 图片源数据 ===
        self.image_path: Optional[str] = None          # 原始图片路径
        self.image_data: Optional[np.ndarray] = None   # 图片像素数据（RGB/RGBA）
        
        # === 图片元信息 ===
        self.pixel_width: int = 0       # 图片宽度（像素）
        self.pixel_height: int = 0      # 图片高度（像素）
        self.dpi: int = 96              # 图片DPI（每英寸像素数）
        
        # === 比例映射设置 ===
        self.pixels_per_unit: float = 100.0   # 每多少像素 = 1格（1米）
        
        # === 计算得出的坐标范围（中心对齐）===
        self.x_min: float = 0.0
        self.x_max: float = 0.0
        self.y_min: float = 0.0
        self.y_max: float = 0.0
        
        # === 显示属性 ===
        self.alpha: float = 0.5         # 透明度（0.0-1.0）
        self.enabled: bool = True       # 是否显示
    
    # ==================== 核心方法 ====================
    
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载图片
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            是否加载成功
        """
        try:
            # 延迟导入 PIL，避免启动时依赖问题
            from PIL import Image
            
            img = Image.open(file_path)
            
            # 读取图片元信息
            self.pixel_width, self.pixel_height = img.size
            
            # 获取 DPI 信息
            dpi_info = img.info.get('dpi', (96, 96))
            if isinstance(dpi_info, tuple):
                self.dpi = int(dpi_info[0])
            elif isinstance(dpi_info, (int, float)):
                self.dpi = int(dpi_info)
            else:
                self.dpi = 96
            
            # 转换为 RGB 或 RGBA 格式
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            self.image_data = np.array(img)
            self.image_path = file_path
            
            # 使用默认比例计算坐标范围（中心对齐）
            self._calculate_extent()
            
            print(f"[OK] 背景图加载成功: {self.pixel_width}×{self.pixel_height} px, DPI={self.dpi}")
            return True
            
        except ImportError:
            print("[ERROR] 缺少 Pillow 库，请安装: pip install Pillow")
            return False
        except Exception as e:
            print(f"[ERROR] 加载背景图失败: {e}")
            return False
    
    def set_pixels_per_unit(self, ppu: float) -> bool:
        """
        设置像素比例（每多少像素=1格/1米）
        
        Args:
            ppu: pixels per unit，每格对应的像素数
            
        Returns:
            是否设置成功
        """
        if ppu <= 0:
            print("[WARN] 像素比例必须大于0")
            return False
        
        self.pixels_per_unit = ppu
        self._calculate_extent()
        
        actual_w, actual_h = self.get_actual_size()
        print(f"[INFO] 比例更新: {ppu} px/格 → 实际尺寸: {actual_w:.1f}m × {actual_h:.1f}m")
        return True
    
    def _calculate_extent(self):
        """
        根据像素比例计算图片在坐标系中的范围（中心对齐）
        
        计算逻辑：
        - 实际宽度 = 图片像素宽度 / 每格像素数
        - 实际高度 = 图片像素高度 / 每格像素数
        - 中心对齐：x_min = -宽度/2, x_max = +宽度/2
        """
        if self.pixel_width == 0 or self.pixel_height == 0:
            return
        
        if self.pixels_per_unit <= 0:
            return
        
        # 计算实际尺寸（单位：格/米）
        actual_width = self.pixel_width / self.pixels_per_unit
        actual_height = self.pixel_height / self.pixels_per_unit
        
        # 中心对齐
        self.x_min = -actual_width / 2.0
        self.x_max = actual_width / 2.0
        self.y_min = -actual_height / 2.0
        self.y_max = actual_height / 2.0
    
    def get_actual_size(self) -> Tuple[float, float]:
        """
        获取图片实际尺寸（米/格）
        
        Returns:
            (宽度, 高度) 单位：米/格
        """
        if self.pixels_per_unit <= 0 or self.pixel_width == 0:
            return (0.0, 0.0)
        
        width = self.pixel_width / self.pixels_per_unit
        height = self.pixel_height / self.pixels_per_unit
        return (width, height)
    
    def get_extent(self) -> Tuple[float, float, float, float]:
        """
        获取图片在坐标系中的范围
        
        Returns:
            (x_min, x_max, y_min, y_max)
        """
        return (self.x_min, self.x_max, self.y_min, self.y_max)
    
    def get_pixel_info(self) -> Dict[str, Any]:
        """
        获取图片像素信息（用于UI显示）
        
        Returns:
            包含像素信息的字典
        """
        return {
            'width': self.pixel_width,
            'height': self.pixel_height,
            'dpi': self.dpi,
        }
    
    def get_info_text(self) -> str:
        """
        获取图片信息文本（用于UI显示）
        
        Returns:
            格式化的信息文本
        """
        if self.image_data is None:
            return "未加载图片"
        
        actual_w, actual_h = self.get_actual_size()
        
        return (
            f"尺寸: {self.pixel_width} × {self.pixel_height} 像素\n"
            f"DPI: {self.dpi}\n"
            f"实际尺寸: {actual_w:.1f} 米 × {actual_h:.1f} 米\n"
            f"坐标范围: X[{self.x_min:.1f}, {self.x_max:.1f}]  "
            f"Y[{self.y_min:.1f}, {self.y_max:.1f}]"
        )
    
    def is_valid(self) -> bool:
        """
        检查背景图是否有效（已加载且启用）
        
        Returns:
            True 表示背景图有效可显示
        """
        return self.image_data is not None and self.enabled
    
    def is_loaded(self) -> bool:
        """
        检查背景图是否已加载（不考虑是否启用）
        
        Returns:
            True 表示已加载图片数据
        """
        return self.image_data is not None
    
    def set_alpha(self, alpha: float):
        """
        设置透明度
        
        Args:
            alpha: 透明度值 (0.0-1.0)
        """
        self.alpha = max(0.0, min(1.0, alpha))
    
    def set_enabled(self, enabled: bool):
        """
        设置是否显示
        
        Args:
            enabled: True 显示，False 隐藏
        """
        self.enabled = enabled
    
    def clear(self):
        """
        清除背景图数据
        """
        self.image_path = None
        self.image_data = None
        self.pixel_width = 0
        self.pixel_height = 0
        self.dpi = 96
        self.pixels_per_unit = 100.0
        self.x_min = 0.0
        self.x_max = 0.0
        self.y_min = 0.0
        self.y_max = 0.0
        self.enabled = True
        print("[INFO] 背景图已清除")
    
    # ==================== 序列化方法 ====================
    
    def to_dict(self, embed_image: bool = True) -> Dict[str, Any]:
        """
        序列化为字典（用于项目保存）
        
        Args:
            embed_image: 是否嵌入图片数据（Base64编码）
                - True: 嵌入图片数据，项目文件较大但独立
                - False: 仅保存路径，需要图片文件存在
            
        Returns:
            序列化后的字典
        """
        data = {
            'image_path': self.image_path,
            'pixel_width': self.pixel_width,
            'pixel_height': self.pixel_height,
            'dpi': self.dpi,
            'pixels_per_unit': self.pixels_per_unit,
            'alpha': self.alpha,
            'enabled': self.enabled,
        }
        
        # 嵌入图片数据（Base64编码）
        if embed_image and self.image_data is not None:
            try:
                from PIL import Image
                img = Image.fromarray(self.image_data)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                data['image_base64'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                print(f"💾 背景图已嵌入项目文件 (Base64)")
            except Exception as e:
                print(f"[WARN] 嵌入背景图失败，仅保存路径: {e}")
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackgroundImage':
        """
        从字典反序列化
        
        Args:
            data: 序列化的字典数据
            
        Returns:
            BackgroundImage 对象
        """
        bg = cls()
        
        # 恢复基本属性
        bg.image_path = data.get('image_path')
        bg.pixel_width = data.get('pixel_width', 0)
        bg.pixel_height = data.get('pixel_height', 0)
        bg.dpi = data.get('dpi', 96)
        bg.pixels_per_unit = data.get('pixels_per_unit', 100.0)
        bg.alpha = data.get('alpha', 0.5)
        bg.enabled = data.get('enabled', True)
        
        # 尝试从 Base64 恢复图片数据
        if 'image_base64' in data:
            try:
                from PIL import Image
                img_bytes = base64.b64decode(data['image_base64'])
                img = Image.open(io.BytesIO(img_bytes))
                bg.image_data = np.array(img)
                bg._calculate_extent()
                print(f"📂 背景图从 Base64 恢复成功")
            except Exception as e:
                print(f"[WARN] 从 Base64 恢复背景图失败: {e}")
        
        # 如果 Base64 恢复失败，尝试从文件路径加载
        if bg.image_data is None and bg.image_path:
            if Path(bg.image_path).exists():
                if bg.load_from_file(bg.image_path):
                    # 应用保存的比例（覆盖 load_from_file 设置的默认值）
                    bg.set_pixels_per_unit(data.get('pixels_per_unit', 100.0))
                    print(f"📂 背景图从文件路径恢复成功: {bg.image_path}")
            else:
                print(f"[WARN] 背景图文件不存在: {bg.image_path}")
        
        return bg
    
    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        if self.image_data is None:
            return "BackgroundImage(未加载)"
        
        actual_w, actual_h = self.get_actual_size()
        return (
            f"BackgroundImage({self.pixel_width}×{self.pixel_height}px, "
            f"{actual_w:.1f}×{actual_h:.1f}m, alpha={self.alpha})"
        )

