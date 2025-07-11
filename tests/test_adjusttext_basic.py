#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adjustText库基本功能测试脚本

测试adjustText在我们项目中的可行性
"""

import matplotlib.pyplot as plt
from adjustText import adjust_text
import numpy as np
import sys
import os

# 添加dev目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dev'))

# 配置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

def test_basic_adjusttext():
    """测试adjustText基本功能"""
    print("=== adjustText基本功能测试 ===")
    
    # 创建测试数据（模拟我们的设备点）
    np.random.seed(42)  # 确保可重复
    
    # 模拟设备坐标
    device_points = [
        (2.5, 3.2, "空调"),
        (2.8, 3.5, "电视"),
        (3.0, 3.1, "音响"),
        (-1.5, 2.0, "冰箱"),
        (-1.2, 2.3, "洗衣机"),
        (0.5, -2.8, "路由器"),
        (0.8, -2.5, "电脑"),
        (4.2, 1.5, "台灯"),
        (-3.5, -1.2, "风扇"),
    ]
    
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # === 左图：不使用adjustText（当前效果） ===
    ax1.set_title("不使用adjustText - 文本重叠问题", fontsize=14, fontweight='bold')
    
    # 绘制坐标系
    ax1.set_xlim(-5, 5)
    ax1.set_ylim(-5, 5)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linewidth=1)
    ax1.axvline(x=0, color='black', linewidth=1)
    ax1.plot(0, 0, 'bo', markersize=8, label='原点')
    
    # 绘制设备点和标签（不使用adjustText）
    for x, y, name in device_points:
        ax1.scatter(x, y, c='red', s=50, alpha=0.8, edgecolors='white', linewidth=1)
        # 简单偏移定位（会重叠）
        ax1.annotate(f'{name}\n({x:.1f}, {y:.1f})', 
                    xy=(x, y), xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8),
                    fontsize=9, ha='left')
    
    ax1.set_xlabel('X 坐标')
    ax1.set_ylabel('Y 坐标')
    ax1.legend()
    
    # === 右图：使用adjustText（智能避让效果） ===
    ax2.set_title("使用adjustText - 智能避让效果", fontsize=14, fontweight='bold')
    
    # 绘制坐标系
    ax2.set_xlim(-5, 5)
    ax2.set_ylim(-5, 5)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linewidth=1)
    ax2.axvline(x=0, color='black', linewidth=1)
    ax2.plot(0, 0, 'bo', markersize=8, label='原点')
    
    # 绘制设备点
    x_coords = [point[0] for point in device_points]
    y_coords = [point[1] for point in device_points]
    names = [point[2] for point in device_points]
    
    ax2.scatter(x_coords, y_coords, c='red', s=50, alpha=0.8, 
               edgecolors='white', linewidth=1)
    
    # 创建文本对象列表（关键步骤）
    texts = []
    for x, y, name in device_points:
        text = ax2.text(x, y, f'{name}\n({x:.1f}, {y:.1f})',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8),
                       fontsize=9, ha='center', va='center')
        texts.append(text)
    
    # 使用adjustText进行智能避让
    adjust_text(texts, ax=ax2, 
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.6))
    
    ax2.set_xlabel('X 坐标')
    ax2.set_ylabel('Y 坐标')
    ax2.legend()
    
    # 保存对比图
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'adjusttext_comparison.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 对比图已保存: {output_path}")
    
    plt.show()
    
    return True

def test_adjusttext_with_obstacles():
    """测试adjustText避开障碍物（扇形区域）的功能"""
    print("\n=== adjustText避开障碍物测试 ===")
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 设置坐标系
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linewidth=1)
    ax.axvline(x=0, color='black', linewidth=1)
    ax.plot(0, 0, 'bo', markersize=8, label='原点')
    
    # 绘制扇形障碍物（模拟我们的90度扇形）
    theta = np.linspace(np.radians(30), np.radians(120), 100)
    radius = 3.5
    x_sector = radius * np.cos(theta)
    y_sector = radius * np.sin(theta)
    
    # 添加扇形起点和终点
    x_coords = np.concatenate([[0], x_sector, [0]])
    y_coords = np.concatenate([[0], y_sector, [0]])
    
    # 绘制扇形
    sector_patch = ax.fill(x_coords, y_coords, color='red', alpha=0.3, 
                          label='90度扇形区域')
    ax.plot(x_coords, y_coords, color='red', linewidth=2)
    
    # 在扇形区域周围放置设备点
    device_points = [
        (1.5, 2.5, "空调A"),  # 在扇形内部
        (2.0, 3.0, "电视B"),  # 在扇形边缘
        (2.5, 2.0, "音响C"), # 在扇形边缘
        (-2.0, 2.0, "冰箱D"),
        (3.5, 0.5, "台灯E"),
        (1.0, 4.2, "风扇F"),
        (-1.5, 3.8, "洗衣机G"),
    ]
    
    # 绘制设备点
    x_coords = [point[0] for point in device_points]
    y_coords = [point[1] for point in device_points]
    
    ax.scatter(x_coords, y_coords, c='green', s=60, alpha=0.8, 
               edgecolors='white', linewidth=1, zorder=5)
    
    # 创建文本对象
    texts = []
    for x, y, name in device_points:
        text = ax.text(x, y, f'{name}\n({x:.1f}, {y:.1f})',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', 
                               alpha=0.9, edgecolor='green'),
                       fontsize=10, ha='center', va='center', zorder=6)
        texts.append(text)
    
    # 使用adjustText进行智能避让，添加障碍物
    adjust_text(texts, ax=ax,
                add_objects=sector_patch,  # 关键：添加扇形作为避让对象
                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7, lw=1.5),
                force_points=(0.5, 0.5),  # 增强推开力度
                force_text=(0.5, 0.5),
                expand_points=(1.2, 1.2),  # 扩大点周围的避让区域
                expand_text=(1.2, 1.2))
    
    ax.set_title("adjustText避开扇形障碍物测试", fontsize=14, fontweight='bold')
    ax.set_xlabel('X 坐标')
    ax.set_ylabel('Y 坐标')
    ax.legend()
    
    # 保存测试图
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'adjusttext_obstacles.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 障碍物避让测试图已保存: {output_path}")
    
    plt.show()
    
    return True

def test_adjusttext_performance():
    """测试adjustText性能"""
    print("\n=== adjustText性能测试 ===")
    
    import time
    
    # 创建大量设备点
    np.random.seed(123)
    num_devices = 50
    x_coords = np.random.uniform(-8, 8, num_devices)
    y_coords = np.random.uniform(-8, 8, num_devices)
    
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.grid(True, alpha=0.3)
    
    # 绘制设备点
    ax.scatter(x_coords, y_coords, c='purple', s=40, alpha=0.7)
    
    # 创建文本对象
    texts = []
    for i, (x, y) in enumerate(zip(x_coords, y_coords)):
        text = ax.text(x, y, f'设备{i:02d}\n({x:.1f},{y:.1f})',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='lightblue', alpha=0.8),
                       fontsize=8, ha='center', va='center')
        texts.append(text)
    
    # 性能测试
    start_time = time.time()
    adjust_text(texts, ax=ax, 
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"✅ 处理{num_devices}个文本标签耗时: {processing_time:.3f}秒")
    
    ax.set_title(f"adjustText性能测试 - {num_devices}个标签 - 耗时{processing_time:.3f}秒", 
                fontsize=14, fontweight='bold')
    
    # 保存性能测试图
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'adjusttext_performance.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 性能测试图已保存: {output_path}")
    
    plt.show()
    
    return processing_time < 2.0  # 期望2秒内完成

if __name__ == "__main__":
    print("🚀 开始adjustText库功能测试...")
    
    try:
        # 基本功能测试
        basic_success = test_basic_adjusttext()
        print(f"✅ 基本功能测试: {'通过' if basic_success else '失败'}")
        
        # 障碍物避让测试
        obstacle_success = test_adjusttext_with_obstacles()
        print(f"✅ 障碍物避让测试: {'通过' if obstacle_success else '失败'}")
        
        # 性能测试
        performance_success = test_adjusttext_performance()
        print(f"✅ 性能测试: {'通过' if performance_success else '失败'}")
        
        # 总结
        all_tests_passed = basic_success and obstacle_success and performance_success
        print(f"\n🎯 总体测试结果: {'全部通过' if all_tests_passed else '部分失败'}")
        print(f"📊 adjustText库{'适合' if all_tests_passed else '可能不适合'}集成到我们的项目中")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 