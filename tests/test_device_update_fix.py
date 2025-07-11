# -*- coding: utf-8 -*-
"""
设备更新功能修复测试

专门测试Device创建时的参数问题和设备更新流程
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.device_model import Device
from models.device_manager import DeviceManager


def test_device_creation():
    """
    测试Device对象创建的各种方式
    """
    print("🧪 测试Device对象创建...")
    
    # 测试1: 不指定device_id
    try:
        device1 = Device("测试设备1", 1.0, 2.0)
        print(f"✅ 创建设备成功（自动ID）: {device1.name}, ID: {device1.id}")
    except Exception as e:
        print(f"❌ 创建设备失败（自动ID）: {e}")
    
    # 测试2: 指定device_id
    try:
        device2 = Device("测试设备2", 3.0, 4.0, device_id="custom_id_123")
        print(f"✅ 创建设备成功（指定ID）: {device2.name}, ID: {device2.id}")
    except Exception as e:
        print(f"❌ 创建设备失败（指定ID）: {e}")
    
    # 测试3: 错误的参数名（应该失败）
    try:
        device3 = Device("测试设备3", 5.0, 6.0, id="wrong_param")
        print(f"❌ 意外成功（错误参数）: {device3.name}")
    except Exception as e:
        print(f"✅ 正确失败（错误参数）: {e}")
    
    return device1, device2


def test_device_update_flow():
    """
    测试完整的设备更新流程
    """
    print("\n🧪 测试设备更新流程...")
    
    # 创建设备管理器
    manager = DeviceManager()
    manager.clear_all_devices()  # 清空初始设备
    
    # 添加原始设备
    original_device = Device("原始设备", 1.0, 1.0)
    success, message = manager.add_device(original_device)
    if not success:
        print(f"❌ 添加原始设备失败: {message}")
        return
    
    print(f"✅ 添加原始设备成功: {original_device.name}, ID: {original_device.id}")
    
    # 模拟InputPanel中的更新逻辑
    try:
        # 获取要更新的设备
        old_device = manager.get_device_by_id(original_device.id)
        if not old_device:
            print("❌ 未找到要更新的设备")
            return
        
        # 创建新设备（使用正确的参数名）
        new_device = Device("更新后设备", 2.0, 2.0, device_id=old_device.id)
        print(f"✅ 创建新设备成功: {new_device.name}, ID: {new_device.id}")
        
        # 执行更新
        success, message = manager.update_device(old_device.id, new_device)
        if success:
            print(f"✅ 设备更新成功: {message}")
            
            # 验证更新结果
            updated_device = manager.get_device_by_id(original_device.id)
            if updated_device:
                print(f"✅ 验证更新结果: 名称={updated_device.name}, 坐标=({updated_device.x}, {updated_device.y})")
            else:
                print("❌ 更新后找不到设备")
        else:
            print(f"❌ 设备更新失败: {message}")
            
    except Exception as e:
        print(f"❌ 设备更新流程异常: {e}")
        import traceback
        traceback.print_exc()


def test_input_panel_simulation():
    """
    模拟InputPanel的_on_add_or_update方法
    """
    print("\n🧪 模拟InputPanel更新逻辑...")
    
    # 创建设备管理器
    manager = DeviceManager()
    manager.clear_all_devices()
    
    # 添加测试设备
    test_device = Device("模拟设备", 0.0, 0.0)
    manager.add_device(test_device)
    
    # 模拟用户输入
    name = "修改后的设备"
    x = 5.5
    y = 6.6
    selected_device_id = test_device.id
    
    # 模拟设备列表（InputPanel.devices）
    devices_cache = manager.get_devices()
    
    def get_device_by_id(device_id):
        for device in devices_cache:
            if device.id == device_id:
                return device
        return None
    
    try:
        # 模拟更新逻辑
        if selected_device_id:
            old_device = get_device_by_id(selected_device_id)
            if old_device:
                # 使用修复后的正确参数名
                new_device = Device(name, x, y, device_id=old_device.id)
                print(f"✅ 创建新设备对象成功: {new_device.name}, ID: {new_device.id}")
                
                # 执行更新
                success, message = manager.update_device(old_device.id, new_device)
                if success:
                    print(f"✅ 模拟更新成功: {message}")
                else:
                    print(f"❌ 模拟更新失败: {message}")
            else:
                print("❌ 未找到选中的设备")
        else:
            print("❌ 没有选中设备")
            
    except Exception as e:
        print(f"❌ 模拟更新异常: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    运行所有测试
    """
    print("🚀 开始设备更新功能修复测试")
    print("=" * 50)
    
    try:
        # 测试Device对象创建
        device1, device2 = test_device_creation()
        
        # 测试设备更新流程
        test_device_update_flow()
        
        # 模拟InputPanel更新逻辑
        test_input_panel_simulation()
        
        print("\n" + "=" * 50)
        print("🎉 设备更新功能修复测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 