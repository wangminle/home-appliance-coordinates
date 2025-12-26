#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI字体大小修改验证测试

验证坐标范围设置区域的字体大小修改效果
"""

import sys

# 该文件是“交互式手工验证脚本”，不适合作为自动化测试在CI/pytest环境运行
if "pytest" in sys.modules:
    import pytest

    pytest.skip("交互式手工验证脚本（含 input），pytest 环境默认跳过。", allow_module_level=True)

def test_instructions():
    """
    打印测试说明
    """
    print("🎨 UI字体大小修改验证")
    print("=" * 50)
    print()
    
    print("🎯 修改内容：")
    print("• 将坐标显示范围设置中的所有文字和输入框字体从10号调整为12号")
    print("• 与下方设备管理信息输入框字体大小保持一致")
    print("• 提升界面的整体协调性和视觉效果")
    print()
    
    print("📋 验证项目：")
    print("1. X轴范围标签字体大小")
    print("2. X轴范围输入框字体大小")
    print("3. Y轴范围标签字体大小")
    print("4. Y轴范围输入框字体大小")
    print("5. ± 符号字体大小")
    print("6. 与设备管理区域输入框的视觉协调性")
    print()
    
    print("✅ 预期效果：")
    print("• 坐标范围设置区域的文字更加清晰易读")
    print("• 与设备管理区域的输入框大小协调一致")
    print("• 整体界面看起来更加统一和专业")
    print()
    
    print("🚀 准备启动应用程序...")
    input("按回车键开始验证...")

def main():
    """主函数"""
    try:
        # 显示测试说明
        test_instructions()
        
        # 导入并启动应用程序
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        from dev.main import main as app_main
        
        print("🚀 启动应用程序...")
        app_main()
        
        print()
        print("=" * 50)
        print("✅ UI字体大小验证完成！")
        print("💬 请确认以下改进效果：")
        print("  1. 坐标范围设置区域的字体是否变大了")
        print("  2. 是否与设备管理区域的输入框大小协调")
        print("  3. 整体视觉效果是否更加统一")
        print("  4. 文字是否更加清晰易读")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1) 
