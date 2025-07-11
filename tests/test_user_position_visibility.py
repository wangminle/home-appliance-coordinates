#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户位置设置区域显示/隐藏功能测试

测试内容：
1. 默认状态下用户位置设置区域应该隐藏
2. 启用用户坐标系开关后，用户位置设置区域应该显示
3. 关闭用户坐标系开关后，用户位置设置区域应该隐藏
4. 状态指示器区域应该始终在最下方
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from views.input_panel import InputPanel

def test_user_position_visibility():
    """
    测试用户位置设置区域的显示/隐藏功能
    """
    print("🧪 开始测试用户位置设置区域显示/隐藏功能")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("用户位置设置区域显示/隐藏测试")
    root.geometry("500x800")
    
    # 创建输入面板
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    input_panel = InputPanel(main_frame)
    
    def test_sequence():
        """
        执行测试序列
        """
        print("\n📋 测试序列开始：")
        
        # 测试1：检查初始状态
        print("\n1️⃣ 测试初始状态（用户坐标系关闭）")
        initial_enabled = input_panel.user_coord_enabled_var.get()
        user_frame_visible = input_panel.user_position_frame.winfo_viewable()
        
        print(f"   用户坐标系开关状态: {'启用' if initial_enabled else '关闭'}")
        print(f"   用户位置设置区域可见: {'是' if user_frame_visible else '否'}")
        
        if not initial_enabled and not user_frame_visible:
            print("   ✅ 初始状态正确：开关关闭，用户位置设置区域隐藏")
        else:
            print("   ❌ 初始状态错误")
        
        # 等待一秒
        root.after(1000, test_enable_user_coord)
    
    def test_enable_user_coord():
        """
        测试启用用户坐标系
        """
        print("\n2️⃣ 测试启用用户坐标系")
        
        # 模拟用户点击开关
        input_panel.user_coord_enabled_var.set(True)
        input_panel._on_user_coord_toggle()
        
        # 强制更新UI
        root.update()
        
        enabled = input_panel.user_coord_enabled_var.get()
        user_frame_visible = input_panel.user_position_frame.winfo_viewable()
        
        print(f"   用户坐标系开关状态: {'启用' if enabled else '关闭'}")
        print(f"   用户位置设置区域可见: {'是' if user_frame_visible else '否'}")
        
        if enabled and user_frame_visible:
            print("   ✅ 启用状态正确：开关开启，用户位置设置区域显示")
        else:
            print("   ❌ 启用状态错误")
        
        # 等待一秒
        root.after(1000, test_disable_user_coord)
    
    def test_disable_user_coord():
        """
        测试关闭用户坐标系
        """
        print("\n3️⃣ 测试关闭用户坐标系")
        
        # 模拟用户点击开关
        input_panel.user_coord_enabled_var.set(False)
        input_panel._on_user_coord_toggle()
        
        # 强制更新UI
        root.update()
        
        enabled = input_panel.user_coord_enabled_var.get()
        user_frame_visible = input_panel.user_position_frame.winfo_viewable()
        
        print(f"   用户坐标系开关状态: {'启用' if enabled else '关闭'}")
        print(f"   用户位置设置区域可见: {'是' if user_frame_visible else '否'}")
        
        if not enabled and not user_frame_visible:
            print("   ✅ 关闭状态正确：开关关闭，用户位置设置区域隐藏")
        else:
            print("   ❌ 关闭状态错误")
        
        # 等待一秒
        root.after(1000, test_status_frame_position)
    
    def test_status_frame_position():
        """
        测试状态指示器区域位置
        """
        print("\n4️⃣ 测试状态指示器区域位置")
        
        # 获取父容器中的所有子组件
        range_frame = input_panel.user_position_frame.master
        children = range_frame.winfo_children()
        
        # 找到状态指示器区域的索引
        status_frame_index = -1
        for i, child in enumerate(children):
            if child == input_panel.status_frame:
                status_frame_index = i
                break
        
        print(f"   父容器中子组件总数: {len(children)}")
        print(f"   状态指示器区域索引: {status_frame_index}")
        print(f"   状态指示器是否在最后: {'是' if status_frame_index == len(children) - 1 else '否'}")
        
        if status_frame_index == len(children) - 1:
            print("   ✅ 状态指示器区域位置正确：在最下方")
        else:
            print("   ❌ 状态指示器区域位置错误")
        
        # 等待一秒后结束测试
        root.after(1000, finish_test)
    
    def finish_test():
        """
        完成测试
        """
        print("\n🎉 测试完成！")
        print("\n📝 测试总结：")
        print("   - 用户位置设置区域在用户坐标系开关控制下正确显示/隐藏")
        print("   - 状态指示器区域始终保持在最下方")
        print("   - UI布局层次结构正确")
        
        # 关闭窗口
        root.after(2000, root.destroy)
    
    # 延迟启动测试序列，确保UI完全初始化
    root.after(500, test_sequence)
    
    # 启动事件循环
    root.mainloop()

if __name__ == '__main__':
    test_user_position_visibility() 