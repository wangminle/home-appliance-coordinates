#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matplotlib artists 内存泄漏验证测试

使用 tracemalloc 观测循环创建/清除场景下的内存变化
验证 device_artists、measurement_artists 等列表的清理是否完整
"""

import sys
import os
import gc
import tracemalloc
import pytest

# 将项目根目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

# 设置 matplotlib 后端为非交互式（避免需要显示器）
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class TestMatplotlibMemoryLeak:
    """Matplotlib 内存泄漏验证测试"""
    
    def test_figure_artists_cleanup(self):
        """测试：Figure 和 Artists 的创建/清除循环不应导致内存持续增长"""
        # 启动内存追踪
        tracemalloc.start()
        
        # 预热：先运行几次以稳定内存
        for _ in range(3):
            fig = Figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot([1, 2, 3], [1, 2, 3])
            ax.scatter([1, 2], [1, 2])
            ax.clear()
            plt.close(fig)
            del fig, ax
        
        gc.collect()
        
        # 记录基准内存
        snapshot_before = tracemalloc.take_snapshot()
        mem_before = sum(stat.size for stat in snapshot_before.statistics('lineno'))
        
        # 执行多次创建/清除循环
        iterations = 50
        for i in range(iterations):
            fig = Figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)
            
            # 模拟设备绑制
            artists = []
            for j in range(10):
                point = ax.scatter([j * 0.1], [j * 0.1], c='red', s=50)
                text = ax.text(j * 0.1, j * 0.1 + 0.5, f'Device {j}',
                              bbox=dict(boxstyle='round', facecolor='yellow'))
                line = ax.plot([0, j * 0.1], [0, j * 0.1], 'b-')[0]
                artists.extend([point, text, line])
            
            # 模拟清除
            for artist in artists:
                try:
                    artist.remove()
                except (ValueError, AttributeError):
                    pass
            artists.clear()
            
            ax.clear()
            plt.close(fig)
            del fig, ax, artists
            
            # 每10次迭代强制垃圾回收
            if i % 10 == 0:
                gc.collect()
        
        gc.collect()
        
        # 记录结束内存
        snapshot_after = tracemalloc.take_snapshot()
        mem_after = sum(stat.size for stat in snapshot_after.statistics('lineno'))
        
        tracemalloc.stop()
        
        # 计算内存增长
        mem_growth = mem_after - mem_before
        mem_growth_per_iter = mem_growth / iterations
        
        print(f"\n=== 内存泄漏检测结果 ===")
        print(f"迭代次数: {iterations}")
        print(f"初始内存: {mem_before / 1024:.2f} KB")
        print(f"结束内存: {mem_after / 1024:.2f} KB")
        print(f"总增长: {mem_growth / 1024:.2f} KB")
        print(f"平均每次迭代增长: {mem_growth_per_iter:.2f} bytes")
        
        # 断言：平均每次迭代的内存增长应该在合理范围内
        # 注意：Matplotlib 有内部缓存（字体、颜色映射等），tracemalloc 会追踪这些分配
        # 关键是检查增长是否会收敛（前期增长快，后期趋于稳定）
        # 允许每次迭代 5KB 的增长（考虑到缓存和 Python 对象开销）
        max_acceptable_growth_per_iter = 5 * 1024  # 5KB
        
        # 更重要的是：总增长不应超过合理范围（如 500KB）
        max_total_growth = 500 * 1024  # 500KB
        
        growth_acceptable = (mem_growth_per_iter < max_acceptable_growth_per_iter or 
                           mem_growth < max_total_growth)
        
        assert growth_acceptable, \
            f"检测到潜在内存泄漏：每次迭代增长 {mem_growth_per_iter:.0f} bytes，总增长 {mem_growth/1024:.0f} KB"
    
    def test_axes_clear_releases_memory(self):
        """测试：axes.clear() 应该正确释放内存"""
        tracemalloc.start()
        
        fig = Figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(111)
        
        # 创建大量对象
        artists = []
        for i in range(100):
            point = ax.scatter([i * 0.01], [i * 0.01], c='red', s=50)
            text = ax.text(i * 0.01, i * 0.01, f'T{i}')
            artists.append(point)
            artists.append(text)
        
        gc.collect()
        snapshot_with_artists = tracemalloc.take_snapshot()
        mem_with_artists = sum(stat.size for stat in snapshot_with_artists.statistics('lineno'))
        
        # 清除
        ax.clear()
        artists.clear()
        gc.collect()
        
        snapshot_after_clear = tracemalloc.take_snapshot()
        mem_after_clear = sum(stat.size for stat in snapshot_after_clear.statistics('lineno'))
        
        plt.close(fig)
        del fig, ax
        gc.collect()
        
        snapshot_final = tracemalloc.take_snapshot()
        mem_final = sum(stat.size for stat in snapshot_final.statistics('lineno'))
        
        tracemalloc.stop()
        
        print(f"\n=== axes.clear() 内存释放测试 ===")
        print(f"创建100个artists后: {mem_with_artists / 1024:.2f} KB")
        print(f"clear()后: {mem_after_clear / 1024:.2f} KB")
        print(f"close()后: {mem_final / 1024:.2f} KB")
        
        # clear() 后内存应该显著减少
        # 注意：由于Python内存管理的特性，可能不会立即归还给系统
        # 但至少不应该持续增长
        assert mem_after_clear <= mem_with_artists * 1.1, \
            "axes.clear() 后内存应该不再增长"
    
    def test_repeated_redraw_memory_stable(self):
        """测试：重复重绘不应导致内存持续增长"""
        tracemalloc.start()
        
        fig = Figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(111)
        
        # 预热
        for _ in range(5):
            ax.clear()
            ax.plot([1, 2, 3], [1, 2, 3])
            fig.canvas.draw_idle() if hasattr(fig.canvas, 'draw_idle') else None
        
        gc.collect()
        snapshot_start = tracemalloc.take_snapshot()
        mem_start = sum(stat.size for stat in snapshot_start.statistics('lineno'))
        
        # 重复重绘循环
        memory_samples = []
        for i in range(30):
            # 清除并重绘
            ax.clear()
            
            # 绘制设备点和标签
            for j in range(5):
                ax.scatter([j], [j], c='blue', s=30)
                ax.text(j + 0.2, j + 0.2, f'D{j}')
            
            # 绘制扇形
            import numpy as np
            theta = np.linspace(0, np.pi/2, 20)
            x = 3 * np.cos(theta)
            y = 3 * np.sin(theta)
            ax.fill(np.concatenate([[0], x, [0]]), 
                   np.concatenate([[0], y, [0]]), 
                   alpha=0.3, color='red')
            
            if hasattr(fig.canvas, 'draw_idle'):
                fig.canvas.draw_idle()
            
            if i % 5 == 0:
                gc.collect()
                snapshot = tracemalloc.take_snapshot()
                mem = sum(stat.size for stat in snapshot.statistics('lineno'))
                memory_samples.append(mem)
        
        gc.collect()
        snapshot_end = tracemalloc.take_snapshot()
        mem_end = sum(stat.size for stat in snapshot_end.statistics('lineno'))
        
        plt.close(fig)
        tracemalloc.stop()
        
        print(f"\n=== 重复重绘内存稳定性测试 ===")
        print(f"初始内存: {mem_start / 1024:.2f} KB")
        print(f"结束内存: {mem_end / 1024:.2f} KB")
        print(f"内存样本: {[f'{m/1024:.1f}KB' for m in memory_samples]}")
        
        # 检查内存是否稳定（后半部分的平均值不应该比前半部分高太多）
        if len(memory_samples) >= 4:
            first_half_avg = sum(memory_samples[:len(memory_samples)//2]) / (len(memory_samples)//2)
            second_half_avg = sum(memory_samples[len(memory_samples)//2:]) / (len(memory_samples) - len(memory_samples)//2)
            growth_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
            
            print(f"前半段平均: {first_half_avg / 1024:.2f} KB")
            print(f"后半段平均: {second_half_avg / 1024:.2f} KB")
            print(f"增长比例: {growth_ratio:.2%}")
            
            # 后半段不应该比前半段高出20%以上
            assert growth_ratio < 1.2, \
                f"检测到内存持续增长：后半段比前半段高 {(growth_ratio - 1) * 100:.1f}%"


class TestArtistRemovePattern:
    """验证 artist.remove() 模式是否正确"""
    
    def test_remove_then_clear_list(self):
        """测试：先 remove() 再 clear() 列表的模式"""
        fig = Figure(figsize=(4, 4), dpi=50)
        ax = fig.add_subplot(111)
        
        artists = []
        for i in range(10):
            p = ax.plot([i], [i], 'o')[0]
            artists.append(p)
        
        # 正确的清除模式
        for artist in artists:
            try:
                artist.remove()
            except (ValueError, AttributeError):
                pass
        artists.clear()
        
        # 验证 axes 上没有残留
        remaining = len(ax.lines) + len(ax.collections) + len(ax.texts)
        
        plt.close(fig)
        
        assert remaining == 0, f"清除后仍有 {remaining} 个 artist 残留"
    
    def test_axes_clear_without_explicit_remove(self):
        """测试：仅用 axes.clear() 是否能清除所有 artists"""
        fig = Figure(figsize=(4, 4), dpi=50)
        ax = fig.add_subplot(111)
        
        artists = []
        for i in range(10):
            p = ax.plot([i], [i], 'o')[0]
            t = ax.text(i, i, f'T{i}')
            artists.append(p)
            artists.append(t)
        
        # 只用 axes.clear()
        ax.clear()
        
        # 验证
        remaining = len(ax.lines) + len(ax.collections) + len(ax.texts)
        
        # 清空引用列表
        artists.clear()
        
        plt.close(fig)
        
        assert remaining == 0, f"axes.clear() 后仍有 {remaining} 个 artist 残留"


if __name__ == '__main__':
    # 直接运行时执行测试
    pytest.main([__file__, '-v', '-s'])

