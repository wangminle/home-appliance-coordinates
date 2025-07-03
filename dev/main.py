#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家居设备坐标距离角度绘制工具
主程序入口文件

作者: AI Assistant
版本: 1.0.0
创建时间: 2024
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.main_controller import MainController


def main():
    """
    应用程序主函数
    初始化并启动GUI应用
    """
    try:
        # 创建主控制器实例
        app = MainController()
        
        # 启动应用程序
        app.run()
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 