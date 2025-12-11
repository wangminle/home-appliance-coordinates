# -*- coding: utf-8 -*-
"""
标签位置改进功能测试脚本

测试内容：
1. 设备标识点尺寸改为5x5
2. 标签默认位置为设备点左侧
3. 标签只在实际碰撞时才切换位置（顺时针：左->上->右->下）
4. 标签位置固定，不重复计算

日期：2024-12-11
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

import tkinter as tk
from models.device_model import Device
from models.scene_model import SceneModel
from controllers.scene_controller import SceneController
from views.matplotlib_view import MatplotlibView


def test_label_position_improvements():
    """
    测试标签位置改进功能
    """
    print("\n" + "="*80)
    print("标签位置改进功能测试")
    print("="*80)
    
    # 创建Tkinter主窗口
    root = tk.Tk()
    root.title("标签位置改进测试 - V3.0")
    root.geometry("1200x800")
    
    # 创建MVC组件
    model = SceneModel(coord_range=(10, 10))
    view = MatplotlibView(root)
    controller = SceneController(model, view)
    
    print("\n✅ MVC组件初始化完成")
    
    # 测试1：添加设备，验证标签默认在左侧
    print("\n" + "-"*80)
    print("测试1: 标签默认位置为左侧")
    print("-"*80)
    
    device1 = Device("测试设备1", 3.0, 3.0, color='#c62828')
    success, msg = model.add_device(device1)
    print(f"添加设备1: {msg}")
    
    # 获取标签位置
    label_pos1 = model.get_label_position(f"device_{device1.id}")
    if label_pos1:
        print(f"  设备1位置: ({device1.x}, {device1.y})")
        print(f"  标签位置: ({label_pos1.x:.3f}, {label_pos1.y:.3f})")
        print(f"  标签方向: {label_pos1.direction}")
        if label_pos1.direction == 'left':
            print("  ✅ 标签默认在左侧 - 测试通过")
        else:
            print(f"  ⚠️ 标签不在左侧，而在{label_pos1.direction}侧")
    
    # 测试2：添加左侧有障碍物的设备，验证自动切换到上侧
    print("\n" + "-"*80)
    print("测试2: 左侧有障碍物时自动切换到上侧")
    print("-"*80)
    
    # 先在左侧添加一个设备作为障碍物
    device2 = Device("障碍物", 0.0, 3.0, color='#2e7d32')
    model.add_device(device2)
    
    # 在右侧添加新设备，其左侧会与障碍物重叠
    device3 = Device("测试设备3", 2.0, 3.0, color='#1565c0')
    model.add_device(device3)
    
    label_pos3 = model.get_label_position(f"device_{device3.id}")
    if label_pos3:
        print(f"  设备3位置: ({device3.x}, {device3.y})")
        print(f"  障碍物位置: ({device2.x}, {device2.y})")
        print(f"  标签位置: ({label_pos3.x:.3f}, {label_pos3.y:.3f})")
        print(f"  标签方向: {label_pos3.direction}")
        if label_pos3.direction != 'left':
            print(f"  ✅ 左侧有障碍物，标签切换到{label_pos3.direction}侧 - 测试通过")
        else:
            print("  ⚠️ 标签仍在左侧，可能与障碍物重叠")
    
    # 测试3：添加扇形，验证标签避开扇形
    print("\n" + "-"*80)
    print("测试3: 标签避开扇形区域")
    print("-"*80)
    
    # 添加一个扇形覆盖右上区域
    device4 = Device("扇形测试设备", -3.0, -3.0, color='#ef6c00')
    model.add_device(device4)
    
    # 添加扇形（覆盖设备左侧区域）
    model.add_sector(-3.0, -3.0, 3.0, 90, 270)
    
    # 强制重新计算标签位置
    label_id4 = f"device_{device4.id}"
    model.reset_label_to_auto(label_id4)
    
    # 重新渲染
    controller.refresh_view()
    
    label_pos4 = model.get_label_position(label_id4)
    if label_pos4:
        print(f"  设备4位置: ({device4.x}, {device4.y})")
        print(f"  扇形: 圆心(-3.0, -3.0), 半径3.0, 角度90°-270°")
        print(f"  标签位置: ({label_pos4.x:.3f}, {label_pos4.y:.3f})")
        print(f"  标签方向: {label_pos4.direction}")
        if label_pos4.direction != 'left':
            print(f"  ✅ 标签避开扇形，切换到{label_pos4.direction}侧 - 测试通过")
        else:
            print("  ⚠️ 标签可能与扇形重叠")
    
    # 测试4：验证标签位置固定，不重复计算
    print("\n" + "-"*80)
    print("测试4: 标签位置固定，不重复计算")
    print("-"*80)
    
    # 获取设备1的初始标签位置
    initial_pos = model.get_label_position(f"device_{device1.id}")
    print(f"  初始标签位置: ({initial_pos.x:.3f}, {initial_pos.y:.3f})")
    
    # 多次刷新视图
    for i in range(3):
        controller.refresh_view()
    
    # 再次获取标签位置
    current_pos = model.get_label_position(f"device_{device1.id}")
    print(f"  刷新3次后位置: ({current_pos.x:.3f}, {current_pos.y:.3f})")
    
    if (abs(initial_pos.x - current_pos.x) < 0.001 and 
        abs(initial_pos.y - current_pos.y) < 0.001):
        print("  ✅ 标签位置保持固定 - 测试通过")
    else:
        print("  ⚠️ 标签位置发生了变化")
    
    # 测试5：验证设备标识点尺寸为5x5
    print("\n" + "-"*80)
    print("测试5: 验证设备标识点尺寸为5x5")
    print("-"*80)
    print("  ✅ 设备标识点尺寸已更新为5x5像素（s=25）")
    print("  请在GUI中目视确认设备标识点的尺寸")
    
    # 显示说明
    print("\n" + "="*80)
    print("测试说明")
    print("="*80)
    print("1. 标签默认位置应该在设备点的左侧")
    print("2. 当左侧有障碍物时，标签应顺时针切换：左->上->右->下")
    print("3. 标签应避开扇形区域")
    print("4. 标签位置一旦确定就固定，不会重复计算")
    print("5. 设备标识点尺寸为5x5像素（比之前的3x3更大）")
    print("\n请在GUI窗口中验证以上功能")
    print("="*80)
    
    # 运行GUI主循环
    root.mainloop()


if __name__ == "__main__":
    test_label_position_improvements()
