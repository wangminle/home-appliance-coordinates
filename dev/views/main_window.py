# -*- coding: utf-8 -*-
"""
主窗口视图

实现1280x800固定窗口，左右分割布局
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class MainWindow:
    """
    主窗口类
    
    实现1280x800固定窗口，左侧800px坐标展示区，右侧480px功能面板
    """
    
    # 窗口尺寸常量
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 800
    CANVAS_WIDTH = 800
    PANEL_WIDTH = 480
    
    # 界面配色（与ref.html保持一致）
    COLORS = {
        'background': '#f0f2f5',
        'canvas_bg': '#e0f7fa',
        'panel_bg': '#ffffff',
        'border': '#d0d0d0'
    }
    
    def __init__(self):
        """
        初始化主窗口
        """
        self.root = None
        self.canvas_frame = None
        self.panel_frame = None
        
        # 回调函数
        self.on_close_callback: Optional[Callable] = None
        self.on_export_shortcut: Optional[Callable] = None
        self.on_reset_shortcut: Optional[Callable] = None
        
        self._create_window()
        self._setup_layout()
        self._setup_styles()
        self._bind_shortcuts() # 绑定快捷键
    
    def _create_window(self):
        """
        创建主窗口并设置基本属性
        """
        self.root = tk.Tk()
        
        # 设置窗口标题
        self.root.title("家居设备坐标距离角度绘制工具")
        
        # 设置窗口图标（可选）
        try:
            # 如果有图标文件可以设置
            # self.root.iconbitmap('icon.ico')
            pass
        except Exception:
            pass
        
        # 设置固定窗口尺寸（不可调整）
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # 设置窗口居中显示
        self._center_window()
        
        # 设置窗口背景色
        self.root.configure(bg=self.COLORS['background'])
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _center_window(self):
        """
        将窗口居中显示在屏幕上
        """
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口居中位置
        x = (screen_width - self.WINDOW_WIDTH) // 2
        y = (screen_height - self.WINDOW_HEIGHT) // 2
        
        # 设置窗口位置
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
    
    def _setup_layout(self):
        """
        设置窗口布局：左右分割
        """
        # 创建主容器框架
        main_frame = tk.Frame(
            self.root,
            bg=self.COLORS['background'],
            relief='flat',
            bd=0
        )
        main_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # 创建左侧Canvas展示区域框架
        self.canvas_frame = tk.Frame(
            main_frame,
            bg=self.COLORS['panel_bg'],
            width=self.CANVAS_WIDTH,
            height=self.WINDOW_HEIGHT,
            relief='solid',
            bd=1,
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        self.canvas_frame.pack(side='left', fill='y', padx=(10, 5), pady=10)
        self.canvas_frame.pack_propagate(False)  # 固定尺寸
        
        # 创建右侧功能面板框架
        self.panel_frame = tk.Frame(
            main_frame,
            bg=self.COLORS['panel_bg'],
            width=self.PANEL_WIDTH,
            height=self.WINDOW_HEIGHT,
            relief='solid',
            bd=1,
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        self.panel_frame.pack(side='right', fill='y', padx=(5, 10), pady=10)
        self.panel_frame.pack_propagate(False)  # 固定尺寸
        
        # 添加区域标题（开发阶段可见）
        self._add_debug_labels()
    
    def _add_debug_labels(self):
        """
        添加调试标签（开发阶段使用）
        """
        # 左侧区域标题
        canvas_title = tk.Label(
            self.canvas_frame,
            text="坐标可视化展示区 (800x800)",
            bg=self.COLORS['panel_bg'],
            fg='#666666',
            font=('Arial', 12, 'bold')
        )
        canvas_title.pack(pady=20)
        
        # 右侧区域标题
        panel_title = tk.Label(
            self.panel_frame,
            text="功能操作面板 (480px)",
            bg=self.COLORS['panel_bg'],
            fg='#666666',
            font=('Arial', 12, 'bold')
        )
        panel_title.pack(pady=20)
    
    def _setup_styles(self):
        """
        设置ttk样式
        """
        style = ttk.Style()
        
        # 设置主题
        try:
            style.theme_use('clam')  # 使用现代主题
        except Exception:
            pass
        
        # 自定义按钮样式
        style.configure(
            'Custom.TButton',
            background='#2196F3',
            foreground='white',
            borderwidth=1,
            focuscolor='none',
            padding=(10, 5)
        )
        
        # 按钮悬停效果
        style.map(
            'Custom.TButton',
            background=[('active', '#1976D2'), ('pressed', '#0D47A1')]
        )
        
        # 自定义Entry样式
        style.configure(
            'Custom.TEntry',
            borderwidth=1,
            relief='solid',
            padding=(5, 3)
        )
    
    def _on_window_close(self):
        """
        窗口关闭事件处理
        """
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.quit()
            self.root.destroy()
    
    def get_canvas_frame(self) -> tk.Frame:
        """
        获取Canvas容器框架
        
        Returns:
            Canvas容器框架对象
        """
        return self.canvas_frame
    
    def get_panel_frame(self) -> tk.Frame:
        """
        获取功能面板框架
        
        Returns:
            功能面板框架对象
        """
        return self.panel_frame
    
    def set_close_callback(self, callback: Callable):
        """
        设置窗口关闭回调函数
        
        Args:
            callback: 窗口关闭时调用的函数
        """
        self.on_close_callback = callback
    
    def show(self):
        """
        显示窗口
        """
        self.root.deiconify()  # 显示窗口
        self.root.lift()       # 提升到最前面
        self.root.focus_force()  # 获取焦点
    
    def hide(self):
        """
        隐藏窗口
        """
        self.root.withdraw()
    
    def run(self):
        """
        启动GUI主循环
        """
        self.root.mainloop()
    
    def destroy(self):
        """
        销毁窗口
        """
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None
    
    def is_running(self) -> bool:
        """
        检查窗口是否还在运行
        
        Returns:
            True如果窗口存在且未销毁
        """
        try:
            return self.root and self.root.winfo_exists()
        except Exception:
            return False
    
    def get_window_geometry(self) -> dict:
        """
        获取窗口几何信息
        
        Returns:
            包含窗口位置和尺寸的字典
        """
        if not self.root:
            return {}
        
        geometry = self.root.geometry()
        # 解析几何字符串，例如 "1280x800+100+50"
        size_part, position_part = geometry.split('+', 1)
        width, height = map(int, size_part.split('x'))
        x, y = map(int, position_part.split('+'))
        
        return {
            'width': width,
            'height': height,
            'x': x,
            'y': y
        }
    
    def set_status_bar_text(self, text: str):
        """
        设置状态栏文本（预留接口）
        
        Args:
            text: 状态栏文本
        """
        # 预留接口，后续可以添加状态栏
        pass
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """
        显示消息对话框
        
        Args:
            title: 对话框标题
            message: 消息内容
            msg_type: 消息类型 ("info", "warning", "error")
        """
        from tkinter import messagebox
        
        if msg_type == "info":
            messagebox.showinfo(title, message, parent=self.root)
        elif msg_type == "warning":
            messagebox.showwarning(title, message, parent=self.root)
        elif msg_type == "error":
            messagebox.showerror(title, message, parent=self.root)
    
    def ask_yes_no(self, title: str, question: str) -> bool:
        """
        显示是/否确认对话框
        
        Args:
            title: 对话框标题
            question: 询问内容
            
        Returns:
            True如果用户选择是，否则False
        """
        from tkinter import messagebox
        
        result = messagebox.askyesno(title, question, parent=self.root)
        return result
    
    def _bind_shortcuts(self):
        """
        绑定全局快捷键
        """
        # 为macOS和Windows/Linux都进行绑定
        # 导出快捷键: Command-S (macOS) / Control-S (Windows/Linux)
        self.root.bind('<Command-s>', self._handle_export_shortcut)
        self.root.bind('<Control-s>', self._handle_export_shortcut)
        
        # 重置快捷键: Command-R (macOS) / Control-R (Windows/Linux)
        self.root.bind('<Command-r>', self._handle_reset_shortcut)
        self.root.bind('<Control-r>', self._handle_reset_shortcut)

    def _handle_export_shortcut(self, event=None):
        """处理导出快捷键事件"""
        if self.on_export_shortcut:
            print("快捷键: 触发导出")
            self.on_export_shortcut()
    
    def _handle_reset_shortcut(self, event=None):
        """处理重置快捷键事件"""
        if self.on_reset_shortcut:
            print("快捷键: 触发重置")
            self.on_reset_shortcut()

    def set_export_shortcut_callback(self, callback: Callable):
        """
        设置导出快捷键回调
        """
        self.on_export_shortcut = callback

    def set_reset_shortcut_callback(self, callback: Callable):
        """
        设置重置快捷键回调
        """
        self.on_reset_shortcut = callback 