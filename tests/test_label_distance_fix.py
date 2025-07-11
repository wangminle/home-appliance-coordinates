#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签距离修复测试

测试优化后的高性能布局算法，确保设备标签不会过度远离设备点
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import time
import math

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.device_model import Device
from views.matplotlib_view import MatplotlibView
from utils.fast_layout import FastLayoutManager, ElementType

def test_label_distance_optimization():
    """测试标签距离优化效果"""
    print("=" * 60)
    print("🎯 标签距离优化测试")
    print("=" * 60)
    
    # 创建测试设备
    devices = [
        Device("7寸屏", -2.625, 0.000),
        Device("4寸屏", -1.000, 3.544),
        Device("设备3", 1.5, -2.0),
        Device("设备4", 3.0, 1.0),
        Device("设备5", -3.5, 2.5),
    ]
    
    # 测试高性能布局管理器
    layout_manager = FastLayoutManager((-10, -10, 10, 10))
    
    print("\n📍 测试设备标签位置优化:")
    for device in devices:
        # 计算最优位置
        optimal_pos = layout_manager.calculate_optimal_position(
            device.x, device.y, ElementType.DEVICE_INFO, device.name
        )
        
        # 计算距离
        distance = math.sqrt((optimal_pos[0] - device.x)**2 + (optimal_pos[1] - device.y)**2)
        
        print(f"   {device.name}: ({device.x:.3f}, {device.y:.3f}) -> 标签({optimal_pos[0]:.3f}, {optimal_pos[1]:.3f})")
        print(f"      距离: {distance:.3f} 单位")
        
        # 验证距离合理性
        if distance > 3.0:
            print(f"      ⚠️  距离过大! 应该 < 3.0")
        elif distance > 2.0:
            print(f"      ⚡ 距离适中")
        else:
            print(f"      ✅ 距离合理")
        
        # 添加到布局管理器（模拟真实场景）
        from utils.fast_layout import LayoutElement, BoundingBox
        box_width, box_height = layout_manager.info_box_sizes[ElementType.DEVICE_INFO]
        element_box = BoundingBox(
            optimal_pos[0] - box_width/2,
            optimal_pos[1] - box_height/2,
            optimal_pos[0] + box_width/2,
            optimal_pos[1] + box_height/2
        )
        element = LayoutElement(
            ElementType.DEVICE_INFO, 
            element_box, 
            (device.x, device.y),
            element_id=device.name
        )
        layout_manager.add_element(element)
    
    print(f"\n📊 布局统计:")
    stats = layout_manager.get_layout_statistics()
    print(f"   总元素数: {stats['total_elements']}")
    print(f"   重叠数量: {stats['overlaps']}")
    print(f"   缓存大小: {stats['cache_size']}")

def test_real_application():
    """在真实应用中测试效果"""
    print("\n" + "=" * 60)
    print("🚀 真实应用测试")
    print("=" * 60)
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("标签距离修复测试")
    root.geometry("900x700")
    
    # 创建MatplotlibView
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    view = MatplotlibView(frame)
    
    # 测试设备
    devices = [
        Device("7寸屏", -2.625, 0.000),
        Device("4寸屏", -1.000, 3.544),
        Device("电视", 2.0, 1.5),
        Device("音响", -1.5, -2.0),
        Device("路由器", 3.5, -1.0),
    ]
    
    print("✅ 添加测试设备...")
    view.update_devices(devices)
    
    # 监控标签位置
    def analyze_label_positions():
        """分析标签位置"""
        print("\n📋 分析设备标签位置:")
        
        # 检查text_objects列表
        if hasattr(view, 'text_objects') and view.text_objects:
            for i, (text_obj, device) in enumerate(zip(view.text_objects, devices)):
                if hasattr(text_obj, 'get_position'):
                    label_pos = text_obj.get_position()
                    distance = math.sqrt((label_pos[0] - device.x)**2 + (label_pos[1] - device.y)**2)
                    
                    print(f"   {device.name}: 设备({device.x:.2f}, {device.y:.2f}) -> 标签({label_pos[0]:.2f}, {label_pos[1]:.2f})")
                    print(f"      距离: {distance:.2f} 单位 {'✅' if distance <= 2.0 else '⚠️' if distance <= 3.0 else '❌'}")
        
        print(f"\n📈 性能统计:")
        print(f"   使用adjustText: {'是' if view._should_use_adjusttext() else '否'}")
        print(f"   文本对象数量: {len(view.text_objects) if hasattr(view, 'text_objects') else 0}")
    
    # 延迟分析，等待界面渲染完成
    root.after(2000, analyze_label_positions)
    root.after(5000, root.destroy)  # 5秒后自动关闭
    
    print("🖼️  显示测试界面（5秒）...")
    root.mainloop()

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("🔬 边界情况测试")
    print("=" * 60)
    
    layout_manager = FastLayoutManager((-10, -10, 10, 10))
    
    # 测试边界附近的设备
    edge_devices = [
        ("边界左上", -8.0, 8.0),
        ("边界右上", 8.0, 8.0),
        ("边界左下", -8.0, -8.0),
        ("边界右下", 8.0, -8.0),
        ("中心设备", 0.0, 0.0),
    ]
    
    print("\n📍 边界设备标签位置测试:")
    for name, x, y in edge_devices:
        optimal_pos = layout_manager.calculate_optimal_position(
            x, y, ElementType.DEVICE_INFO, name
        )
        
        distance = math.sqrt((optimal_pos[0] - x)**2 + (optimal_pos[1] - y)**2)
        
        # 检查标签是否在画布内
        in_bounds = (-9.5 <= optimal_pos[0] <= 9.5 and -9.5 <= optimal_pos[1] <= 9.5)
        
        print(f"   {name}: ({x:.1f}, {y:.1f}) -> 标签({optimal_pos[0]:.2f}, {optimal_pos[1]:.2f})")
        print(f"      距离: {distance:.2f}, 边界内: {'✅' if in_bounds else '❌'}")

def main():
    """主测试函数"""
    print("🎯 标签距离修复测试")
    print("=" * 80)
    
    try:
        # 运行各项测试
        test_label_distance_optimization()
        test_edge_cases()
        test_real_application()
        
        print("\n" + "=" * 80)
        print("✅ 标签距离修复测试完成！")
        print("🎯 优化后的标签应该更靠近设备点，不会过度远离")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 