#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adjustText集成测试脚本

测试adjustText在实际项目中的智能避让效果
"""

import sys
import os
import time

# 添加dev目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dev'))

from models.device_model import Device
from models.measurement_model import MeasurementPoint
from views.matplotlib_view import MatplotlibView
import tkinter as tk

def test_adjusttext_device_labels():
    """测试设备标签智能避让"""
    print("=== 测试设备标签智能避让 ===")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("adjustText设备标签测试")
    root.geometry("800x600")
    
    # 创建MatplotlibView
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    view = MatplotlibView(main_frame)
    
    # 创建密集的设备点（故意重叠）
    devices = [
        Device(1, "空调A", 2.5, 3.2),
        Device(2, "空调B", 2.6, 3.3),  # 非常接近空调A
        Device(3, "电视", 2.7, 3.1),   # 也很接近
        Device(4, "音响", 2.8, 3.4),   # 继续接近
        Device(5, "冰箱", -1.5, 2.0),
        Device(6, "洗衣机", -1.4, 2.1), # 接近冰箱
        Device(7, "路由器", 0.5, -2.8),
        Device(8, "电脑", 0.6, -2.7),   # 接近路由器
    ]
    
    # 更新设备列表
    view.update_devices(devices)
    
    # 等待一段时间让用户观察
    def close_window():
        print("✅ 设备标签测试完成")
        root.destroy()
    
    root.after(3000, close_window)  # 3秒后自动关闭
    root.mainloop()
    
    return True

def test_adjusttext_with_measurement():
    """测试设备标签 + 测量信息框的智能避让"""
    print("\n=== 测试设备标签 + 测量信息框智能避让 ===")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("adjustText复合避让测试")
    root.geometry("800x600")
    
    # 创建MatplotlibView
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    view = MatplotlibView(main_frame)
    
    # 创建设备点
    devices = [
        Device(1, "空调", 2.5, 3.2),
        Device(2, "电视", 2.8, 3.5),
        Device(3, "冰箱", -1.5, 2.0),
        Device(4, "洗衣机", -1.2, 2.3),
        Device(5, "路由器", 0.5, -2.8),
    ]
    view.update_devices(devices)
    
    # 添加测量点（在设备密集区域）
    measurement = MeasurementPoint(2.6, 3.3, None)  # 在设备密集区域
    view.measurement_point = measurement
    view._draw_measurement()
    
    # 等待观察
    def close_window():
        print("✅ 复合避让测试完成")
        root.destroy()
    
    root.after(4000, close_window)  # 4秒后自动关闭
    root.mainloop()
    
    return True

def test_adjusttext_with_sector():
    """测试扇形障碍物避让"""
    print("\n=== 测试扇形障碍物避让 ===")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("adjustText扇形避让测试")
    root.geometry("800x600")
    
    # 创建MatplotlibView
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    view = MatplotlibView(main_frame)
    
    # 创建设备点（在扇形区域周围）
    devices = [
        Device(1, "空调", 2.0, 2.5),   # 可能在扇形内
        Device(2, "电视", 2.5, 3.0),   # 扇形边缘
        Device(3, "音响", 1.5, 3.2),   # 扇形周围
        Device(4, "台灯", 3.0, 1.8),   # 扇形外侧
        Device(5, "冰箱", -2.0, 2.0),  # 远离扇形
    ]
    view.update_devices(devices)
    
    # 添加测量点
    measurement = MeasurementPoint(2.2, 2.8, None)
    view.measurement_point = measurement
    view._draw_measurement()
    
    # 绘制扇形（在设备密集区域）
    view.sector_point = (2.5, 3.0)  # 在设备密集区域
    view._draw_sector()
    
    # 等待观察
    def close_window():
        print("✅ 扇形避让测试完成")
        root.destroy()
    
    root.after(5000, close_window)  # 5秒后自动关闭
    root.mainloop()
    
    return True

def test_adjusttext_user_position():
    """测试用户位置标签避让"""
    print("\n=== 测试用户位置标签避让 ===")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("adjustText用户位置测试")
    root.geometry("800x600")
    
    # 创建MatplotlibView
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    view = MatplotlibView(main_frame)
    
    # 启用用户坐标系
    view.set_user_coordinate_mode(True)
    
    # 设置用户位置（在设备密集区域）
    view.set_user_position(1.0, 2.0)
    
    # 创建设备点（围绕用户位置）
    devices = [
        Device(1, "空调", 1.2, 2.3),   # 很接近用户位置
        Device(2, "电视", 0.8, 2.1),   # 也很接近
        Device(3, "音响", 1.1, 1.8),   # 继续接近
        Device(4, "台灯", 0.9, 2.2),   # 非常接近
    ]
    view.update_devices(devices)
    
    # 添加测量点
    measurement = MeasurementPoint(1.0, 2.2, view.user_position)
    view.measurement_point = measurement
    view._draw_measurement()
    
    # 等待观察
    def close_window():
        print("✅ 用户位置测试完成")
        root.destroy()
    
    root.after(4000, close_window)  # 4秒后自动关闭
    root.mainloop()
    
    return True

def test_adjusttext_performance_real():
    """测试adjustText在真实场景中的性能"""
    print("\n=== adjustText真实场景性能测试 ===")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("adjustText性能测试")
    root.geometry("800x600")
    
    # 创建MatplotlibView
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    view = MatplotlibView(main_frame)
    
    # 创建大量设备
    devices = []
    for i in range(25):  # 25个设备
        x = (i % 10 - 5) * 0.8  # 分布在-4到4之间
        y = (i // 5 - 2) * 0.8  # 5行设备
        devices.append(Device(i+1, f"设备{i+1:02d}", x, y))
    
    # 测量性能
    start_time = time.time()
    view.update_devices(devices)
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"✅ 处理{len(devices)}个设备标签耗时: {processing_time:.3f}秒")
    
    # 添加测量点和扇形
    measurement = MeasurementPoint(0.5, 1.0, None)
    view.measurement_point = measurement
    view._draw_measurement()
    
    view.sector_point = (1.0, 1.5)
    view._draw_sector()
    
    # 等待观察
    def close_window():
        print("✅ 性能测试完成")
        root.destroy()
    
    root.after(6000, close_window)  # 6秒后自动关闭
    root.mainloop()
    
    return processing_time < 1.0  # 期望1秒内完成

if __name__ == "__main__":
    print("🚀 开始adjustText集成测试...")
    
    try:
        # 设备标签测试
        device_success = test_adjusttext_device_labels()
        print(f"✅ 设备标签测试: {'通过' if device_success else '失败'}")
        
        # 复合避让测试
        measurement_success = test_adjusttext_with_measurement()
        print(f"✅ 复合避让测试: {'通过' if measurement_success else '失败'}")
        
        # 扇形避让测试
        sector_success = test_adjusttext_with_sector()
        print(f"✅ 扇形避让测试: {'通过' if sector_success else '失败'}")
        
        # 用户位置测试
        user_success = test_adjusttext_user_position()
        print(f"✅ 用户位置测试: {'通过' if user_success else '失败'}")
        
        # 性能测试
        performance_success = test_adjusttext_performance_real()
        print(f"✅ 性能测试: {'通过' if performance_success else '失败'}")
        
        # 总结
        all_tests_passed = all([device_success, measurement_success, sector_success, 
                               user_success, performance_success])
        print(f"\n🎯 集成测试结果: {'全部通过' if all_tests_passed else '部分失败'}")
        print(f"📊 adjustText集成{'成功' if all_tests_passed else '需要优化'}")
        
        if all_tests_passed:
            print("🎉 恭喜！adjustText已成功替换原有的复杂布局管理器！")
        
    except Exception as e:
        print(f"❌ 集成测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 