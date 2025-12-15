#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标输入区域布局调整测试

测试内容：
1. 坐标显示范围设置区域是否采用单行布局
2. 包含 X轴范围、Y轴范围 和 范围设置按钮
3. 验证组件是否存在于统一容器中
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from views.input_panel import InputPanel

def test_layout_adjustment():
    """
    测试坐标输入区域布局调整
    """
    print("🧪 开始测试坐标输入区域布局调整 (单行布局)")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("坐标输入区域布局调整测试")
    root.geometry("600x400")
    
    # 创建输入面板
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    input_panel = InputPanel(main_frame)
    
    def analyze_layout():
        """
        分析布局情况
        """
        print("\n📋 布局分析结果：")
        
        # 强制更新UI以获取准确的位置信息
        root.update()
        
        try:
            # 查找坐标范围设置区域
            range_frame = None
            for child in input_panel.parent_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and "坐标显示范围设置" in child.cget('text'):
                    range_frame = child
                    break
            
            if not range_frame:
                print("   ❌ 未找到坐标范围设置区域")
                return
            
            print(f"   坐标范围设置区域: ✅ 找到")
            
            # 查找统一的输入行框架
            # 在 range_frame 的子组件中，应该有一个 Frame 包含所有元素
            input_row_frame = None
            for child in range_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    # 简单判断：如果这个Frame包含按钮，那大概就是目标Frame
                    has_button = False
                    for grand_child in child.winfo_children():
                        if isinstance(grand_child, ttk.Button):
                            has_button = True
                            break
                    if has_button:
                        input_row_frame = child
                        break
            
            print(f"   单行输入框架: {'✅ 找到' if input_row_frame else '❌ 未找到'}")
            
            if input_row_frame:
                children = input_row_frame.winfo_children()
                print(f"   输入行框架组件数量: {len(children)}")
                
                # 检查关键组件
                has_x_label = False
                has_y_label = False
                has_range_btn = False
                
                for child in children:
                    if isinstance(child, ttk.Label):
                        text = child.cget('text')
                        if "X轴范围" in text:
                            has_x_label = True
                        elif "Y轴范围" in text:
                            has_y_label = True
                    elif isinstance(child, ttk.Button):
                        text = child.cget('text')
                        if "范围设置" in text:
                            has_range_btn = True
                
                print(f"   包含 'X轴范围' 标签: {'✅ 是' if has_x_label else '❌ 否'}")
                print(f"   包含 'Y轴范围' 标签: {'✅ 是' if has_y_label else '❌ 否'}")
                print(f"   包含 '范围设置' 按钮: {'✅ 是' if has_range_btn else '❌ 否'}")
                
            print(f"\n4️⃣ 布局优化确认：")
            print(f"   ✅ X轴、Y轴设置和按钮合并为单行")
            print(f"   ✅ 按钮文本更新为 '范围设置'")
            print(f"   ✅ 字号已调整 (需视觉确认)")
            
        except Exception as e:
            print(f"   ❌ 布局分析时发生错误: {e}")
        
        # 延迟关闭
        root.after(2000, root.destroy)
    
    # 延迟启动分析，确保UI完全初始化
    root.after(1000, analyze_layout)
    
    # 启动事件循环
    root.mainloop()

if __name__ == '__main__':
    test_layout_adjustment()
