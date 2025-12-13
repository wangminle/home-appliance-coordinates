#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI交互细节调整测试（2025-12-12）

覆盖本次改动点：
1. 原始坐标系：移除原点大蓝点
2. 设备标识点：方块尺寸从 5x5 调整为 7x7（s=49）
3. 原始坐标系：移除鼠标随动坐标信息框
4. 单击生成：测量点为直径约6的圆点（markersize=6）
5. 单击生成：测量标签字体/字号与设备标签一致（fontsize=9, bold），默认在点正下方下移2格，背景透明度0.6

说明：
- 测试采用Mock屏蔽Tk真实组件，避免CI/无GUI环境崩溃。
- 只验证MatplotlibView层的绘制对象属性。
"""

import os
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch

# 添加路径以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.device_model import Device
from views.matplotlib_view import MatplotlibView


def _build_mock_canvas():
    """构建一个满足MatplotlibView最小调用的Mock Canvas"""
    mock_tk_widget = MagicMock()
    mock_tk_widget.pack = MagicMock()
    mock_tk_widget.config = MagicMock()

    mock_canvas = MagicMock()
    mock_canvas.get_tk_widget.return_value = mock_tk_widget
    mock_canvas.mpl_connect = MagicMock()
    mock_canvas.draw_idle = MagicMock()

    return mock_canvas


class TestUIInteractionTweaks20251212(unittest.TestCase):
    """UI交互细节调整测试"""

    def setUp(self):
        self.mock_parent = Mock()

        # patch FigureCanvasTkAgg，避免真实Tk组件创建
        self._patcher = patch('views.matplotlib_view.FigureCanvasTkAgg', return_value=_build_mock_canvas())
        self._patcher.start()

        self.view = MatplotlibView(self.mock_parent)

    def tearDown(self):
        try:
            self._patcher.stop()
        except Exception:
            pass

    def test_01_origin_point_removed(self):
        """原始坐标系：不应再绘制label='原点'的大蓝点"""
        origin_lines = [ln for ln in self.view.axes.lines if getattr(ln, 'get_label', lambda: '')() == '原点']
        self.assertEqual(len(origin_lines), 0, "原点大蓝点应被移除")

    def test_02_device_marker_size_is_7x7(self):
        """设备标识点：方块尺寸应调整为s=49（约7x7）"""
        device = Device('设备A', 1.0, 2.0)
        self.view.update_devices([device])

        self.assertGreaterEqual(len(self.view.device_artists), 1, "应至少绘制一个设备点")
        scatter = self.view.device_artists[0]
        self.assertTrue(hasattr(scatter, 'get_sizes'), "设备点应为scatter对象")
        sizes = scatter.get_sizes()
        self.assertTrue(len(sizes) >= 1)
        self.assertEqual(int(sizes[0]), 49, "设备点方块大小应为s=49")

    def test_03_world_mode_no_hover_coordinate_info(self):
        """世界坐标系：不应绘制鼠标随动坐标信息框"""
        self.view.user_coord_enabled = False
        self.view.user_position = None

        # 直接调用内部方法验证“不会绘制”
        self.view._draw_coordinate_info(1.0, 2.0)
        self.assertEqual(len(self.view.coordinate_info_artists), 0, "世界坐标系下不应产生坐标信息框")

    def test_04_click_measurement_point_and_label_style(self):
        """单击生成：测量点与标签的样式与默认位置应符合要求"""
        x, y = 3.0, 4.0
        self.view._handle_single_click(x, y)

        # 1) 测量点markersize=6
        self.assertGreaterEqual(len(self.view.measurement_artists), 1)
        point = self.view.measurement_artists[0]
        self.assertTrue(hasattr(point, 'get_markersize'))
        self.assertEqual(point.get_markersize(), 6, "测量点markersize应为6")

        # 2) 找到测量标签Text对象
        text_obj = None
        for artist in self.view.measurement_artists:
            if hasattr(artist, 'get_text') and not hasattr(artist, 'get_markersize'):
                text_obj = artist
                break

        self.assertIsNotNone(text_obj, "应生成测量标签")

        # 3) 字体/字号一致（fontsize=9, bold）
        self.assertEqual(int(text_obj.get_fontsize()), 9)
        self.assertEqual(str(text_obj.get_fontweight()), 'bold')

        # 4) 默认位置：正下方下移2格
        pos_x, pos_y = text_obj.get_position()
        self.assertAlmostEqual(pos_x, x, places=6)
        self.assertAlmostEqual(pos_y, y - 2.0, places=6)

        # 5) 背景透明度：0.6
        bbox_patch = text_obj.get_bbox_patch()
        self.assertIsNotNone(bbox_patch, "标签应有bbox背景")
        face_rgba = bbox_patch.get_facecolor()
        self.assertAlmostEqual(face_rgba[3], 0.6, places=2, msg="标签背景alpha应约为0.6")


if __name__ == '__main__':
    unittest.main(verbosity=2)
