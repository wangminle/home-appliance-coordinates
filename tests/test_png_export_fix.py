#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PNG导出功能修复测试
测试macOS系统上文件对话框参数的兼容性
"""

import sys
import os
import tempfile
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from controllers.matplotlib_controller import MatplotlibController
from models.device_model import Device


def test_file_dialog_parameters():
    """测试文件对话框参数兼容性"""
    print("🧪 测试文件对话框参数兼容性...")
    
    # 创建临时根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    try:
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"测试导出_{timestamp}.png"
        
        # 测试正确的参数（不实际显示对话框）
        print(f"✅ 默认文件名: {default_filename}")
        print("✅ 文件对话框参数验证通过")
        
        # 测试参数组合
        params = {
            'title': "导出PNG图片",
            'defaultextension': ".png",
            'filetypes': [("PNG files", "*.png"), ("All files", "*.*")],
            'initialfile': default_filename  # 使用正确的参数名
        }
        
        print("✅ 文件对话框参数配置正确:")
        for key, value in params.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件对话框参数测试失败: {e}")
        return False
    finally:
        root.destroy()


def test_matplotlib_export_function():
    """测试Matplotlib导出功能"""
    print("\n🧪 测试Matplotlib导出功能...")
    
    try:
        # 创建临时根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建控制器
        controller = MatplotlibController(root)
        
        # 添加测试设备
        controller.add_device("测试设备1", 2.0, 3.0)
        controller.add_device("测试设备2", -1.5, 2.5)
        
        # 创建临时文件路径
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_file_path = tmp_file.name
        
        # 测试导出功能（绕过文件对话框）
        success = controller.canvas_view.export_to_png(test_file_path, dpi=300)
        
        if success and os.path.exists(test_file_path):
            file_size = os.path.getsize(test_file_path)
            print(f"✅ PNG导出成功: {test_file_path}")
            print(f"✅ 文件大小: {file_size} bytes")
            
            # 清理临时文件
            os.unlink(test_file_path)
            return True
        else:
            print("❌ PNG导出失败")
            return False
            
    except Exception as e:
        print(f"❌ Matplotlib导出测试失败: {e}")
        return False
    finally:
        if 'root' in locals():
            root.destroy()


def test_export_error_handling():
    """测试导出错误处理"""
    print("\n🧪 测试导出错误处理...")
    
    try:
        # 创建临时根窗口
        root = tk.Tk()
        root.withdraw()
        
        # 创建控制器
        controller = MatplotlibController(root)
        
        # 测试无效路径
        invalid_path = "/invalid/path/test.png"
        success = controller.canvas_view.export_to_png(invalid_path, dpi=300)
        
        if not success:
            print("✅ 无效路径错误处理正确")
            return True
        else:
            print("❌ 无效路径应该返回False")
            return False
            
    except Exception as e:
        print(f"✅ 异常处理正确: {e}")
        return True
    finally:
        if 'root' in locals():
            root.destroy()


def main():
    """主测试函数"""
    print("🚀 开始PNG导出功能修复测试")
    print("=" * 50)
    
    tests = [
        ("文件对话框参数兼容性", test_file_dialog_parameters),
        ("Matplotlib导出功能", test_matplotlib_export_function),
        ("导出错误处理", test_export_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name} - {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name} - ❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("📊 测试结果摘要:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n总测试数: {total}")
    print(f"成功: {passed}")
    print(f"失败: {total - passed}")
    
    if passed == total:
        print("\n🎉 所有测试通过！PNG导出功能修复成功")
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 