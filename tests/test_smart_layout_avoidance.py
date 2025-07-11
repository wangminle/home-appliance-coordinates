#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能布局避让功能测试脚本

测试智能布局管理器在复杂场景下的避让效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dev'))

import tkinter as tk
from tkinter import ttk
import time
import random

# 直接运行主程序进行测试
def main():
    """主函数"""
    print("🧪 智能布局避让功能测试")
    print("=" * 50)
    print("✨ 智能布局避让功能已集成到主程序中")
    print("📝 请运行主程序并执行以下测试场景:")
    print()
    print("🔍 测试场景1: 多设备密集分布")
    print("  - 在中心区域(1,1)附近添加多个设备")
    print("  - 创建测量点在设备群中心")
    print("  - 观察信息框是否智能避让，无重叠")
    print()
    print("🔍 测试场景2: 扇形与信息框冲突")
    print("  - 添加设备并创建测量点")
    print("  - 双击创建扇形")
    print("  - 观察信息框是否避开扇形区域")
    print()
    print("🔍 测试场景3: 用户坐标系复合场景")
    print("  - 启用用户坐标系并设置用户位置")
    print("  - 在用户位置附近添加设备")
    print("  - 创建测量点和扇形")
    print("  - 观察用户坐标系下的复合避让效果")
    print()
    print("🔍 测试场景4: 边界避让")
    print("  - 在坐标范围边界附近添加设备")
    print("  - 创建测量点在边界附近")
    print("  - 观察边界处信息框是否正确避让")
    print()
    print("🚀 现在启动主程序进行测试...")
    
    # 启动主程序
    from main import main as run_main
    run_main()


if __name__ == "__main__":
    main() 