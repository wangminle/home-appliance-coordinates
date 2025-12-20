# -*- coding: utf-8 -*-
"""
跨平台字体配置模块

根据操作系统自动选择最佳的中文字体，确保 macOS 和 Windows 下 UI 效果一致且美观。

主要功能：
1. 检测当前操作系统
2. 为 Matplotlib 和 Tkinter 提供各自最佳的字体配置
3. 支持字体回退机制，确保在任何系统上都能正常显示

使用方式：
    from utils.font_config import FontConfig
    
    # 获取 Tkinter 字体
    font_normal = FontConfig.get_tk_font(size=11)
    font_bold = FontConfig.get_tk_font(size=11, weight='bold')
    
    # 配置 Matplotlib 字体
    FontConfig.configure_matplotlib()
"""

import platform
import tkinter.font as tkfont
from typing import Tuple, Optional, List


class FontConfig:
    """
    跨平台字体配置类
    
    为 macOS、Windows、Linux 系统提供统一的字体管理方案。
    """
    
    # 操作系统类型
    _system = platform.system()
    
    # ========== macOS 推荐字体 ==========
    # macOS 系统字体优先级（从高到低）：
    # - PingFang SC: 苹方字体，macOS 10.11+ 自带，现代感强
    # - Hiragino Sans GB: 冬青黑体，macOS 自带，质量优秀
    # - STHeiti: 华文黑体，传统 macOS 字体
    # - SF Pro: 系统界面字体（英文优秀，中文需搭配）
    # - Helvetica Neue: 经典无衬线字体
    
    MACOS_FONTS = {
        'ui': ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Helvetica Neue'],
        'matplotlib': ['PingFang SC', 'Hiragino Sans GB', 'Arial Unicode MS', 'STHeiti'],
    }
    
    # ========== Windows 推荐字体 ==========
    # Windows 系统字体优先级（从高到低）：
    # - Microsoft YaHei: 微软雅黑，Windows Vista+ 自带，现代美观
    # - Microsoft YaHei UI: 微软雅黑 UI 变体，专为界面优化
    # - SimHei: 中易黑体，Windows 传统字体
    # - NSimSun: 新宋体
    # - Segoe UI: Windows 界面字体（英文）
    
    WINDOWS_FONTS = {
        'ui': ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Segoe UI'],
        'matplotlib': ['Microsoft YaHei', 'SimHei', 'FangSong', 'KaiTi'],
    }
    
    # ========== Linux 推荐字体 ==========
    # Linux 系统字体优先级（从高到低）：
    # - Noto Sans CJK SC: Google 开源字体，质量优秀
    # - WenQuanYi Micro Hei: 文泉驿微米黑
    # - Droid Sans Fallback: Android 风格字体
    
    LINUX_FONTS = {
        'ui': ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback', 'DejaVu Sans'],
        'matplotlib': ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'DejaVu Sans'],
    }
    
    # 通用备选字体（跨平台）
    FALLBACK_FONTS = ['Arial', 'Helvetica', 'sans-serif']
    
    # 缓存检测到的可用字体
    _available_tk_font: Optional[str] = None
    _available_mpl_fonts: Optional[List[str]] = None
    
    @classmethod
    def get_system(cls) -> str:
        """
        获取当前操作系统类型
        
        Returns:
            'Darwin' (macOS), 'Windows', 或 'Linux'
        """
        return cls._system
    
    @classmethod
    def is_macos(cls) -> bool:
        """是否为 macOS 系统"""
        return cls._system == 'Darwin'
    
    @classmethod
    def is_windows(cls) -> bool:
        """是否为 Windows 系统"""
        return cls._system == 'Windows'
    
    @classmethod
    def is_linux(cls) -> bool:
        """是否为 Linux 系统"""
        return cls._system == 'Linux'
    
    @classmethod
    def get_font_candidates(cls, usage: str = 'ui') -> List[str]:
        """
        获取当前系统的字体候选列表
        
        Args:
            usage: 'ui' 用于 Tkinter 界面, 'matplotlib' 用于绑图
            
        Returns:
            按优先级排序的字体名称列表
        """
        if cls.is_macos():
            fonts = cls.MACOS_FONTS.get(usage, cls.MACOS_FONTS['ui'])
        elif cls.is_windows():
            fonts = cls.WINDOWS_FONTS.get(usage, cls.WINDOWS_FONTS['ui'])
        else:
            fonts = cls.LINUX_FONTS.get(usage, cls.LINUX_FONTS['ui'])
        
        return fonts + cls.FALLBACK_FONTS
    
    @classmethod
    def _detect_available_tk_font(cls, root=None) -> str:
        """
        检测系统中可用的 Tkinter 字体
        
        Args:
            root: Tkinter root 窗口，用于字体检测
            
        Returns:
            可用的字体名称
        """
        if cls._available_tk_font:
            return cls._available_tk_font
        
        candidates = cls.get_font_candidates('ui')
        
        # 尝试获取系统字体列表
        try:
            import tkinter as tk
            if root is None:
                # 创建临时窗口检测字体
                temp_root = tk.Tk()
                temp_root.withdraw()
                available_fonts = set(tkfont.families())
                temp_root.destroy()
            else:
                available_fonts = set(tkfont.families())
            
            # 查找第一个可用的候选字体
            for font_name in candidates:
                if font_name in available_fonts:
                    cls._available_tk_font = font_name
                    print(f"[FontConfig] Tkinter 字体: {font_name}")
                    return font_name
        except Exception as e:
            print(f"[FontConfig] 字体检测失败: {e}")
        
        # 回退到 Arial
        cls._available_tk_font = 'Arial'
        return 'Arial'
    
    @classmethod
    def get_tk_font(cls, size: int = 10, weight: str = 'normal', root=None) -> Tuple[str, int, str]:
        """
        获取 Tkinter 字体配置元组
        
        Args:
            size: 字体大小
            weight: 'normal' 或 'bold'
            root: Tkinter root 窗口
            
        Returns:
            字体配置元组，如 ('Microsoft YaHei UI', 11, 'bold')
        """
        font_name = cls._detect_available_tk_font(root)
        return (font_name, size, weight)
    
    @classmethod
    def get_tk_font_normal(cls, size: int = 10, root=None) -> Tuple[str, int]:
        """
        获取普通 Tkinter 字体配置
        
        Args:
            size: 字体大小
            root: Tkinter root 窗口
            
        Returns:
            字体配置元组，如 ('Microsoft YaHei UI', 11)
        """
        font_name = cls._detect_available_tk_font(root)
        return (font_name, size)
    
    @classmethod
    def configure_matplotlib(cls):
        """
        配置 Matplotlib 字体，使其支持中文显示
        
        应在创建任何 Figure 之前调用此方法。
        """
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        
        # 获取当前系统的 Matplotlib 字体候选
        font_list = cls.get_font_candidates('matplotlib')
        
        # 检测系统中实际可用的字体
        available_fonts = set(f.name for f in fm.fontManager.ttflist)
        
        # 过滤出可用的字体
        valid_fonts = [f for f in font_list if f in available_fonts]
        
        if valid_fonts:
            cls._available_mpl_fonts = valid_fonts
            print(f"[FontConfig] Matplotlib 字体: {valid_fonts[0]}")
        else:
            # 使用默认回退
            valid_fonts = ['DejaVu Sans', 'sans-serif']
            cls._available_mpl_fonts = valid_fonts
            print(f"[FontConfig] Matplotlib 使用默认字体")
        
        # 应用配置
        plt.rcParams['font.sans-serif'] = valid_fonts
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清除字体缓存（确保新配置生效）
        fm._load_fontmanager(try_read_cache=False)
    
    @classmethod
    def get_matplotlib_fonts(cls) -> List[str]:
        """
        获取已配置的 Matplotlib 字体列表
        
        Returns:
            字体名称列表
        """
        if cls._available_mpl_fonts is None:
            cls.configure_matplotlib()
        return cls._available_mpl_fonts or ['DejaVu Sans']
    
    @classmethod
    def get_font_info(cls) -> dict:
        """
        获取当前字体配置信息（用于调试）
        
        Returns:
            包含系统和字体信息的字典
        """
        return {
            'system': cls._system,
            'is_macos': cls.is_macos(),
            'is_windows': cls.is_windows(),
            'is_linux': cls.is_linux(),
            'tk_font': cls._available_tk_font,
            'matplotlib_fonts': cls._available_mpl_fonts,
            'ui_candidates': cls.get_font_candidates('ui'),
            'matplotlib_candidates': cls.get_font_candidates('matplotlib'),
        }


# ========== 便捷函数 ==========

def get_ui_font(size: int = 10, bold: bool = False) -> Tuple:
    """
    获取 UI 字体的便捷函数
    
    Args:
        size: 字体大小
        bold: 是否加粗
        
    Returns:
        字体配置元组
    """
    if bold:
        return FontConfig.get_tk_font(size, 'bold')
    return FontConfig.get_tk_font_normal(size)


def setup_matplotlib_fonts():
    """
    配置 Matplotlib 字体的便捷函数
    
    应在程序启动时、创建任何 Figure 之前调用。
    """
    FontConfig.configure_matplotlib()


# ========== 模块初始化 ==========

# 打印当前系统信息（仅在导入时）
if __name__ != "__main__":
    try:
        print(f"[FontConfig] 检测到操作系统: {FontConfig.get_system()}")
    except UnicodeEncodeError:
        # Windows 控制台可能无法显示某些字符
        pass

