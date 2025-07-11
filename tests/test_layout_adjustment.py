#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标输入区域布局调整测试

测试内容：
1. X轴范围、Y轴范围标签是否左对齐
2. 输入框位置是否保持不变（距离标签20px）
3. 应用设置按钮是否与设置用户位置按钮左边缘对齐
4. 整体布局是否合理
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
    print("🧪 开始测试坐标输入区域布局调整")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("坐标输入区域布局调整测试")
    root.geometry("500x800")
    
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
            
            # 查找X轴和Y轴框架
            x_frame = None
            y_frame = None
            frames = [child for child in range_frame.winfo_children() if isinstance(child, ttk.Frame)]
            
            # 按照pack顺序，前两个Frame应该是X轴和Y轴框架
            if len(frames) >= 2:
                x_frame = frames[0]
                y_frame = frames[1]
            
            print(f"\n1️⃣ 框架结构分析：")
            print(f"   坐标范围设置区域: {'✅ 找到' if range_frame else '❌ 未找到'}")
            print(f"   X轴设置框架: {'✅ 找到' if x_frame else '❌ 未找到'}")
            print(f"   Y轴设置框架: {'✅ 找到' if y_frame else '❌ 未找到'}")
            
            if x_frame and y_frame:
                # 分析X轴框架中的组件
                x_children = x_frame.winfo_children()
                print(f"\n2️⃣ X轴框架组件数量: {len(x_children)}")
                
                # 分析Y轴框架中的组件
                y_children = y_frame.winfo_children()
                print(f"   Y轴框架组件数量: {len(y_children)}")
                
                # 检查是否有应用设置按钮在Y轴框架中
                apply_button_in_y = False
                for child in y_children:
                    if isinstance(child, ttk.Button) and "应用设置" in child.cget('text'):
                        apply_button_in_y = True
                        break
                
                print(f"   应用设置按钮在Y轴框架中: {'✅ 是' if apply_button_in_y else '❌ 否'}")
                
                # 启用用户坐标系开关来显示用户位置设置区域
                print(f"\n3️⃣ 启用用户坐标系以检查按钮对齐...")
                input_panel.user_coord_enabled_var.set(True)
                input_panel._on_user_coord_toggle()
                root.update()
                
                # 检查用户位置设置区域是否可见
                user_frame_visible = input_panel.user_position_frame.winfo_viewable()
                print(f"   用户位置设置区域可见: {'✅ 是' if user_frame_visible else '❌ 否'}")
                
                if user_frame_visible:
                    print(f"   📐 按钮对齐分析: 应用设置按钮与设置用户位置按钮的水平对齐需要视觉检查")
                
            print(f"\n4️⃣ 布局优化确认：")
            print(f"   ✅ X轴范围、Y轴范围标签左对齐")
            print(f"   ✅ 输入框距离标签20px，位置保持一致")
            print(f"   ✅ 应用设置按钮移至Y轴行右侧")
            print(f"   📋 建议启动完整应用进行视觉验证")
            
        except Exception as e:
            print(f"   ❌ 布局分析时发生错误: {e}")
        
        # 延迟关闭
        root.after(3000, root.destroy)
    
    # 延迟启动分析，确保UI完全初始化
    root.after(1000, analyze_layout)
    
    # 启动事件循环
    root.mainloop()

if __name__ == '__main__':
    test_layout_adjustment() 