# -*- coding: utf-8 -*-
"""
设备颜色持久化测试
测试日期: 2024-12-11

测试目标:
验证设备颜色在保存和加载项目时能够正确持久化
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dev_src = os.path.join(project_root, 'dev', 'src')
sys.path.insert(0, dev_src)

from models.device_model import Device
from models.project_manager import ProjectManager


def test_color_persistence():
    """测试设备颜色持久化"""
    
    print("="*70)
    print("设备颜色持久化测试")
    print("="*70)
    
    # 创建项目管理器
    pm = ProjectManager()
    
    # 创建测试设备（使用不同颜色）
    devices = [
        Device("红色设备", 0, 0, color=Device.COLOR_RED),
        Device("绿色设备", 2, 0, color=Device.COLOR_GREEN),
        Device("蓝色设备", 4, 0, color=Device.COLOR_BLUE),
        Device("橙色设备", 0, 2, color=Device.COLOR_ORANGE),
        Device("紫色设备", 2, 2, color=Device.COLOR_PURPLE),
        Device("青色设备", 4, 2, color=Device.COLOR_CYAN),
    ]
    
    print("\n步骤1: 创建测试设备")
    print("-" * 70)
    original_colors = {}
    for device in devices:
        print(f"  {device.name}: {device.color}")
        original_colors[device.id] = device.color
    
    # 保存项目
    test_file = Path(project_root) / 'output' / 'test_color_persistence.json'
    test_file.parent.mkdir(exist_ok=True)
    
    print(f"\n步骤2: 保存项目到 {test_file.name}")
    print("-" * 70)
    
    success, message = pm.save_project(
        file_path=str(test_file),
        devices=devices,
        coordinate_settings={'x_range': 10, 'y_range': 10},
        project_info={'name': '颜色持久化测试', 'description': '测试设备颜色保存和加载'}
    )
    
    if success:
        print(f"  ✅ 保存成功: {message}")
    else:
        print(f"  ❌ 保存失败: {message}")
        return False
    
    # 验证保存的JSON文件
    print("\n步骤3: 验证保存的JSON文件")
    print("-" * 70)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    devices_data = saved_data.get('devices', [])
    print(f"  保存的设备数量: {len(devices_data)}")
    
    all_colors_saved = True
    for device_data in devices_data:
        device_name = device_data.get('name')
        device_color = device_data.get('color')
        if device_color:
            print(f"  ✅ {device_name}: color字段已保存 = {device_color}")
        else:
            print(f"  ❌ {device_name}: color字段缺失！")
            all_colors_saved = False
    
    if not all_colors_saved:
        print("\n  ❌ 测试失败：部分设备颜色未保存")
        return False
    
    # 加载项目
    print("\n步骤4: 重新加载项目")
    print("-" * 70)
    
    success, message, loaded_data = pm.load_project(str(test_file))
    
    if not success:
        print(f"  ❌ 加载失败: {message}")
        return False
    
    print(f"  ✅ 加载成功: {message}")
    
    # 解析加载的设备
    loaded_devices = pm._parse_devices(loaded_data.get('devices', []))
    
    print(f"\n步骤5: 验证加载的设备颜色")
    print("-" * 70)
    
    all_colors_match = True
    for device in loaded_devices:
        original_color = original_colors.get(device.id)
        if device.color == original_color:
            print(f"  ✅ {device.name}: {device.color} (与原始颜色匹配)")
        else:
            print(f"  ❌ {device.name}: {device.color} (原始: {original_color})")
            all_colors_match = False
    
    # 测试结果
    print("\n" + "="*70)
    if all_colors_match:
        print("✅ 测试通过：所有设备颜色正确持久化！")
        print("="*70)
        return True
    else:
        print("❌ 测试失败：部分设备颜色未正确持久化")
        print("="*70)
        return False


def test_backward_compatibility():
    """测试向后兼容性（旧项目文件没有color字段）"""
    
    print("\n" + "="*70)
    print("向后兼容性测试")
    print("="*70)
    
    pm = ProjectManager()
    
    # 创建一个没有color字段的旧版本项目文件
    test_file = Path(project_root) / 'output' / 'test_old_format.json'
    test_file.parent.mkdir(exist_ok=True)
    
    old_format_data = {
        'project_info': {
            'name': '旧版本项目',
            'version': '1.0',
            'created_time': '2024-01-01T00:00:00',
            'modified_time': '2024-01-01T00:00:00'
        },
        'coordinate_settings': {
            'x_range': 10,
            'y_range': 10
        },
        'user_coordinate_system': {
            'enabled': False,
            'user_x': None,
            'user_y': None
        },
        'devices': [
            {
                'id': 'old-device-1',
                'name': '旧设备1',
                'x': 0.0,
                'y': 0.0,
                'created_time': '2024-01-01T00:00:00'
                # 注意：没有color字段
            },
            {
                'id': 'old-device-2',
                'name': '旧设备2',
                'x': 2.0,
                'y': 2.0,
                'created_time': '2024-01-01T00:00:00'
                # 注意：没有color字段
            }
        ]
    }
    
    print(f"\n步骤1: 创建旧版本项目文件（无color字段）")
    print("-" * 70)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(old_format_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 已创建: {test_file.name}")
    
    # 加载旧版本项目
    print(f"\n步骤2: 加载旧版本项目")
    print("-" * 70)
    
    success, message, loaded_data = pm.load_project(str(test_file))
    
    if not success:
        print(f"  ❌ 加载失败: {message}")
        return False
    
    print(f"  ✅ 加载成功: {message}")
    
    # 解析设备
    loaded_devices = pm._parse_devices(loaded_data.get('devices', []))
    
    print(f"\n步骤3: 验证设备是否使用默认颜色")
    print("-" * 70)
    
    all_have_default_color = True
    for device in loaded_devices:
        if device.color == Device.COLOR_RED:  # 默认红色
            print(f"  ✅ {device.name}: {device.color} (默认颜色)")
        else:
            print(f"  ❌ {device.name}: {device.color} (应该是默认红色)")
            all_have_default_color = False
    
    # 测试结果
    print("\n" + "="*70)
    if all_have_default_color:
        print("✅ 向后兼容性测试通过：旧项目正确加载并使用默认颜色")
        print("="*70)
        return True
    else:
        print("❌ 向后兼容性测试失败")
        print("="*70)
        return False


if __name__ == '__main__':
    print("\n" + "🔬 开始测试设备颜色持久化功能" + "\n")
    
    # 测试1: 颜色持久化
    test1_passed = test_color_persistence()
    
    # 测试2: 向后兼容性
    test2_passed = test_backward_compatibility()
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    print(f"  颜色持久化测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"  向后兼容性测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print("="*70)
    
    if test1_passed and test2_passed:
        print("\n✅ 所有测试通过！设备颜色持久化功能正常工作。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查代码。")
        sys.exit(1)
