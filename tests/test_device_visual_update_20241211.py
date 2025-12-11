# -*- coding: utf-8 -*-
"""
设备视觉展示更新测试脚本
测试日期: 2024-12-11

测试目标:
1. 设备标记点改为3x3方块
2. 设备标签简化为4个方向（上下左右各1个坐标单位）
3. 标签内文字全部左对齐
4. 连接线从标签边缘中点连到设备点边缘中点
"""

import sys
import os

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dev_src = os.path.join(project_root, 'dev', 'src')
sys.path.insert(0, dev_src)

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.device_model import Device
from models.scene_model import SceneModel
from views.scene_renderer import SceneRenderer


class TestDeviceVisualApp:
    """测试设备视觉展示更新的应用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("设备视觉展示更新测试 - 4方向布局")
        self.root.geometry("1000x800")
        
        # 创建场景模型
        self.model = SceneModel(coord_range=(10, 10))
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.axes = self.figure.add_subplot(111)
        
        # 创建渲染器
        self.renderer = SceneRenderer(self.figure, self.axes)
        
        # 创建UI
        self._create_ui()
        
        # 添加测试设备（测试4个方向）
        self._add_test_devices()
        
        # 渲染场景
        self.renderer.render(self.model)
    
    def _create_ui(self):
        """创建用户界面"""
        # 左侧控制面板
        control_frame = ttk.Frame(self.root, width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(control_frame, text="4方向布局测试", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        # 测试场景按钮
        ttk.Button(control_frame, text="场景1: 右方标签", 
                  command=self._test_right_label).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="场景2: 上方标签", 
                  command=self._test_top_label).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="场景3: 下方标签", 
                  command=self._test_bottom_label).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="场景4: 左方标签", 
                  command=self._test_left_label).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="场景5: 混合多方向", 
                  command=self._test_mixed_directions).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="场景6: 边界测试", 
                  command=self._test_boundary_cases).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="场景7: 3x3方块验证", 
                  command=self._test_device_marker_size).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # 清空按钮
        ttk.Button(control_frame, text="清空所有设备", 
                  command=self._clear_all).pack(fill=tk.X, pady=5)
        
        # 测试说明
        info_frame = ttk.LabelFrame(control_frame, text="测试说明", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, height=15, width=25)
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.insert('1.0', """验证项目:

1. 设备标记点大小
   ✓ 应为3x3像素方块

2. 标签位置规则
   ✓ 4个方向（上下左右）
   ✓ 距离设备点1个单位

3. 标签文字格式
   ✓ 三行文字全部左对齐
   ✓ 格式: 设备名/X:值/Y:值

4. 连接线规则
   ✓ 从标签边缘中点
   ✓ 连到设备点边缘中点
   ✓ 1px短虚线样式

5. 优先级测试
   右 > 上 > 下 > 左
""")
        info_text.config(state=tk.DISABLED)
        
        # 右侧画布
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 嵌入matplotlib画布
        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _clear_all(self):
        """清空所有设备"""
        self.model.clear_devices()
        self.renderer.render(self.model)
        self.canvas.draw()
    
    def _add_test_devices(self):
        """添加初始测试设备"""
        # 添加一个中心设备用于展示默认布局
        device = Device("测试设备", 0, 0)
        self.model.add_device(device)
    
    def _test_right_label(self):
        """测试右方标签"""
        self._clear_all()
        # 在左侧添加设备，标签应该出现在右方
        device = Device("右方标签", -5, 0)
        self.model.add_device(device)
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景1: 右方标签测试 - 设备在(-5, 0)，标签应在右方")
    
    def _test_top_label(self):
        """测试上方标签"""
        self._clear_all()
        # 在下方添加设备，如果右方空间不够，标签应该出现在上方
        device = Device("上方标签", 0, -5)
        self.model.add_device(device)
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景2: 上方标签测试 - 设备在(0, -5)，标签应在上方")
    
    def _test_bottom_label(self):
        """测试下方标签"""
        self._clear_all()
        # 在上方添加设备，如果右方和上方都不够，标签应该出现在下方
        device = Device("下方标签", 0, 7)
        self.model.add_device(device)
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景3: 下方标签测试 - 设备在(0, 7)，标签应在下方")
    
    def _test_left_label(self):
        """测试左方标签"""
        self._clear_all()
        # 在右侧边缘添加设备，标签应该出现在左方
        device = Device("左方标签", 7, 0)
        self.model.add_device(device)
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景4: 左方标签测试 - 设备在(7, 0)，标签应在左方")
    
    def _test_mixed_directions(self):
        """测试混合多方向"""
        self._clear_all()
        
        # 添加多个设备，测试不同方向的标签
        devices = [
            Device("右方1", -6, 0),      # 应显示右方标签
            Device("右方2", -6, 3),      # 应显示右方标签
            Device("上方1", 0, -6),      # 应显示上方标签
            Device("上方2", 3, -6),      # 应显示上方标签
            Device("下方1", 0, 6),       # 应显示下方标签
            Device("下方2", -3, 6),      # 应显示下方标签
            Device("左方1", 6, 0),       # 应显示左方标签
            Device("左方2", 6, -3),      # 应显示左方标签
        ]
        
        for device in devices:
            self.model.add_device(device)
        
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景5: 混合多方向测试 - 8个设备分布在四周")
    
    def _test_boundary_cases(self):
        """测试边界情况"""
        self._clear_all()
        
        # 测试接近边界的设备
        devices = [
            Device("右上角", 8, 8),      # 应显示左方或下方标签
            Device("左上角", -8, 8),     # 应显示右方或下方标签
            Device("右下角", 8, -8),     # 应显示左方或上方标签
            Device("左下角", -8, -8),    # 应显示右方或上方标签
        ]
        
        for device in devices:
            self.model.add_device(device)
        
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景6: 边界测试 - 4个设备在四个角落")
    
    def _test_device_marker_size(self):
        """测试设备标记点大小"""
        self._clear_all()
        
        # 添加一组设备用于验证3x3方块大小
        devices = [
            Device("3x3-1", -3, 3),
            Device("3x3-2", 0, 3),
            Device("3x3-3", 3, 3),
            Device("3x3-4", -3, 0),
            Device("3x3-5", 0, 0),
            Device("3x3-6", 3, 0),
        ]
        
        for device in devices:
            self.model.add_device(device)
        
        self.renderer.render(self.model)
        self.canvas.draw()
        print("✅ 场景7: 3x3方块验证 - 请检查设备标记点是否为3x3像素")
    
    def run(self):
        """运行应用"""
        print("="*60)
        print("设备视觉展示更新测试")
        print("="*60)
        print("\n测试内容:")
        print("1. 设备标记点改为3x3方块")
        print("2. 标签简化为4个方向（上下左右各1个坐标单位）")
        print("3. 标签内文字全部左对齐")
        print("4. 连接线从标签边缘中点连到设备点边缘中点")
        print("\n请通过左侧按钮切换不同测试场景")
        print("="*60)
        
        self.root.mainloop()


if __name__ == '__main__':
    app = TestDeviceVisualApp()
    app.run()

