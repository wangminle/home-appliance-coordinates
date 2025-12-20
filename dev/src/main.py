#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matplotlib版本主程序

基于Matplotlib实现的高性能绘图版本
"""

import tkinter as tk
import sys
import os

# 确保能够导入其他模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入字体配置（必须在导入 Matplotlib 相关模块之前）
from utils.font_config import FontConfig

from controllers.matplotlib_controller import MatplotlibController


def main():
    """
    应用程序主入口
    """
    try:
        print("[Main] 启动家居设备坐标距离角度绘制工具 - Matplotlib版")
        
        # 初始化跨平台字体配置（必须在创建 Figure 之前）
        FontConfig.configure_matplotlib()
        
        # 创建主窗口
        root = tk.Tk()
        
        # 创建控制器（会自动创建界面）
        controller = MatplotlibController(root)
        
        # 启动GUI主循环
        print("[Main] 应用程序启动完成")
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n[Main] 用户中断应用程序")
    except Exception as e:
        print(f"[Main] 应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 