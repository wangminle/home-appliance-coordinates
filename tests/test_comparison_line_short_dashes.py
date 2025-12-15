# -*- coding: utf-8 -*-
"""
对比虚线样式测试脚本

目标：图钉锁定后，第二条线段（对比线）的虚线样式从“长虚线”调整为“短虚线”

覆盖：
- 正常情况：有锁定数据时绘制对比线，dash pattern 为 (3, 2)
- 边界情况：对比点与中心点重合（零长度线段）仍应保持短虚线 dash pattern
- 异常情况：绘制环境缺失（axes 为 None）应抛出异常，避免静默失败

测试日期: 2025-12-15
"""

import os
import sys
import unittest

# 强制使用无界面后端，避免测试环境没有显示器导致报错
os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg")

from matplotlib.figure import Figure

# 添加项目路径（遵循现有测试脚本约定）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dev", "src"))

from models.locked_measurement import LockedMeasurement
from views.matplotlib_view import MatplotlibView


class _DummyCanvas:
    """最小化Canvas替身：仅提供draw_idle接口"""

    def draw_idle(self):
        """测试环境无需实际刷新"""
        return


class _DummyView:
    """
    最小化View替身，用于调用 MatplotlibView._draw_comparison_line
    这样可以避免创建Tk窗口，但仍复用真实绘制逻辑。
    """

    COLORS = MatplotlibView.COLORS

    def __init__(self, locked: bool = True):
        fig = Figure(figsize=(4, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        self.canvas = _DummyCanvas()
        self.comparison_artists = []

        self.locked_measurement = LockedMeasurement()
        # 设置锁定数据：以原点为中心，方向点为(3,4)
        self.locked_measurement.set_measurement((3.0, 4.0), (0.0, 0.0))
        if locked:
            self.locked_measurement.lock()

    def _clear_comparison(self):
        """复用 MatplotlibView 的清理策略（最小实现）"""
        for artist in self.comparison_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self.comparison_artists.clear()


class TestComparisonLineShortDashes(unittest.TestCase):
    """对比虚线（第二条线段）短虚线样式测试"""

    def test_normal_short_dashes(self):
        """正常情况：对比线应为短虚线 (3,2)"""
        view = _DummyView(locked=True)

        # 调用真实绘制方法
        MatplotlibView._draw_comparison_line(view, 2.0, 1.0)

        # 第一个artist就是对比线 Line2D
        self.assertGreaterEqual(len(view.comparison_artists), 1)
        line = view.comparison_artists[0]

        # Matplotlib 在当前版本将 dash pattern 存在私有属性 _unscaled_dash_pattern
        # 期望值：(offset=0, dashes=(3,2))
        self.assertTrue(hasattr(line, "_unscaled_dash_pattern"))
        self.assertEqual(line._unscaled_dash_pattern, (0, (3, 2)))

        print("✅ 正常情况：对比线短虚线样式 - 通过")

    def test_boundary_zero_length_line(self):
        """边界情况：对比点与中心点重合时，仍应保持短虚线样式"""
        view = _DummyView(locked=True)
        center_x, center_y = view.locked_measurement.center_point

        MatplotlibView._draw_comparison_line(view, center_x, center_y)

        self.assertGreaterEqual(len(view.comparison_artists), 1)
        line = view.comparison_artists[0]
        self.assertEqual(line._unscaled_dash_pattern, (0, (3, 2)))

        print("✅ 边界情况：零长度对比线短虚线样式 - 通过")

    def test_exception_missing_axes(self):
        """异常情况：缺失axes时应抛出异常（避免无声失败）"""
        view = _DummyView(locked=True)
        view.axes = None  # 模拟异常环境

        with self.assertRaises(AttributeError):
            MatplotlibView._draw_comparison_line(view, 1.0, 1.0)

        print("✅ 异常情况：缺失axes抛出异常 - 通过")


if __name__ == "__main__":
    unittest.main(verbosity=2)


