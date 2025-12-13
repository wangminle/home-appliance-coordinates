#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户坐标系视觉与交互细节调整测试（2025-12-13）

覆盖本次改动点：
1. 用户坐标系：不显示任何随动坐标信息框（世界/用户都关闭）
2. 用户坐标系：坐标轴线宽下降一半，颜色为红色
3. 用户坐标系：原点标签固定在用户点正下方2格（严格 (x, y-2.0)），不参与智能避让/自动挪动
4. 用户坐标系：原点标签字号与设备标签一致（fontsize=9, bold），背景透明度为0.6

说明：
- MatplotlibView测试使用Mock屏蔽Tk真实组件，避免无GUI环境崩溃。
- SceneRenderer测试直接使用Figure/Axes，不依赖Tk。
"""

import os
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch

from matplotlib.figure import Figure
from matplotlib.colors import to_hex

# 添加路径以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from views.matplotlib_view import MatplotlibView
from views.scene_renderer import SceneRenderer
from models.scene_model import SceneModel


def _build_mock_canvas():
    """构建一个满足MatplotlibView最小调用的Mock Canvas（避免真实Tk组件）"""
    mock_tk_widget = MagicMock()
    mock_tk_widget.pack = MagicMock()
    mock_tk_widget.config = MagicMock()

    mock_canvas = MagicMock()
    mock_canvas.get_tk_widget.return_value = mock_tk_widget
    mock_canvas.mpl_connect = MagicMock()
    mock_canvas.draw_idle = MagicMock()

    return mock_canvas


class TestUserCoordinateVisualTweaks20251213(unittest.TestCase):
    """用户坐标系视觉与交互细节调整测试"""

    def setUp(self):
        self.mock_parent = Mock()
        self._patcher = patch(
            'views.matplotlib_view.FigureCanvasTkAgg',
            return_value=_build_mock_canvas()
        )
        self._patcher.start()
        self.view = MatplotlibView(self.mock_parent)

    def tearDown(self):
        try:
            self._patcher.stop()
        except Exception:
            pass

    def _find_user_origin_label(self):
        """从用户位置相关绘制对象中找到用户原点标签Text对象"""
        for artist in self.view.user_position_artists:
            if hasattr(artist, 'get_text') and callable(getattr(artist, 'get_text')):
                txt = artist.get_text()
                if isinstance(txt, str) and '[用户] 位置' in txt:
                    return artist
        return None

    def test_01_user_mode_no_hover_coordinate_info(self):
        """用户坐标系：不应绘制任何随动坐标信息框"""
        self.view.user_coord_enabled = True
        self.view.user_position = (1.0, 2.0)
        self.view._draw_coordinate_info(3.0, 4.0)
        self.assertEqual(len(self.view.coordinate_info_artists), 0, "用户坐标系下不应产生坐标信息框")

    def test_02_user_axes_style_is_red_and_half_width(self):
        """用户坐标系：轴线颜色为红色且线宽下降一半（主0.75/辅0.25）"""
        self.view.set_user_coordinate_mode(True)
        self.view.set_user_position(1.0, 2.0)

        dashed_lines = [
            a for a in self.view.user_position_artists
            if hasattr(a, 'get_linestyle') and callable(getattr(a, 'get_linestyle'))
            and a.get_linestyle() == '--'
            and hasattr(a, 'get_linewidth')
        ]

        self.assertEqual(len(dashed_lines), 4, "用户坐标系轴线应包含4条虚线（2主+2辅）")

        widths = sorted([round(float(ln.get_linewidth()), 2) for ln in dashed_lines])
        self.assertEqual(widths, [0.25, 0.25, 0.75, 0.75], "用户坐标系轴线线宽应为主0.75、辅0.25")

        # 颜色检查：统一转为hex，避免rgba/字符串差异
        colors = sorted([to_hex(ln.get_color()).lower() for ln in dashed_lines])
        self.assertTrue(all(c == '#d32f2f' for c in colors), "用户坐标系轴线颜色应为红色 #d32f2f")

    def test_03_user_origin_label_fixed_position_and_style(self):
        """用户坐标系：原点标签严格固定在 (x, y-2)，字体与设备一致，背景alpha=0.6"""
        x, y = 3.5, 4.5
        self.view.set_user_coordinate_mode(True)
        self.view.set_user_position(x, y)

        text_obj = self._find_user_origin_label()
        self.assertIsNotNone(text_obj, "应绘制用户原点标签")

        pos_x, pos_y = text_obj.get_position()
        self.assertAlmostEqual(pos_x, x, places=6)
        self.assertAlmostEqual(pos_y, y - 2.0, places=6)

        self.assertEqual(int(text_obj.get_fontsize()), 9, "用户原点标签fontsize应与设备一致为9")
        self.assertEqual(str(text_obj.get_fontweight()), 'bold', "用户原点标签应为bold")

        bbox_patch = text_obj.get_bbox_patch()
        self.assertIsNotNone(bbox_patch, "用户原点标签应有bbox背景")
        face_rgba = bbox_patch.get_facecolor()
        self.assertAlmostEqual(face_rgba[3], 0.6, places=2, msg="用户原点标签背景alpha应约为0.6")

        # 关键约束：用户原点标签不应参与智能避让（否则位置会“随动/漂移”）
        self.assertNotIn(text_obj, self.view.text_objects, "用户原点标签不应加入text_objects参与智能避让")

    def test_04_boundary_case_label_not_clamped(self):
        """边界条件：即便超出画布范围，用户原点标签也应保持固定偏移（不做边界挪动）"""
        x, y = 0.0, -9.5
        self.view.set_user_coordinate_mode(True)
        self.view.set_user_position(x, y)

        text_obj = self._find_user_origin_label()
        self.assertIsNotNone(text_obj)
        pos_x, pos_y = text_obj.get_position()
        self.assertAlmostEqual(pos_x, x, places=6)
        self.assertAlmostEqual(pos_y, y - 2.0, places=6)

    def test_05_exception_case_invalid_user_position_type(self):
        """异常情况：用户位置传入非法类型应抛出异常（且不应产生随动信息）"""
        self.view.set_user_coordinate_mode(True)
        with self.assertRaises((TypeError, ValueError)):
            # set_user_position 内部使用格式化输出 {x:.3f}，非法类型应触发异常
            self.view.set_user_position("bad_x", 1.0)  # type: ignore[arg-type]

        # 坐标信息框仍应保持关闭
        self.view._draw_coordinate_info(1.0, 2.0)
        self.assertEqual(len(self.view.coordinate_info_artists), 0)

    def test_06_measurement_label_correctly_identified_and_fixed(self):
        """测量标签应被正确识别为MEASUREMENT_INFO类型，不被adjustText移动"""
        from utils.fast_layout import ElementType

        # 世界坐标系模式下创建测量点
        self.view.user_coord_enabled = False
        self.view._handle_single_click(3.0, 4.0)

        # 找到测量标签
        measurement_text = None
        for t in self.view.text_objects:
            if hasattr(t, 'get_text') and '距离:' in t.get_text() and '角度:' in t.get_text():
                measurement_text = t
                break

        self.assertIsNotNone(measurement_text, "应生成测量标签")

        # 验证类型识别正确
        element_type = self.view._get_element_type_from_text(measurement_text)
        self.assertEqual(
            element_type, ElementType.MEASUREMENT_INFO,
            f"测量标签应被识别为MEASUREMENT_INFO，实际: {element_type}"
        )

        # 验证标签位置固定在点击点正下方2格
        pos_x, pos_y = measurement_text.get_position()
        self.assertAlmostEqual(pos_x, 3.0, places=6)
        self.assertAlmostEqual(pos_y, 2.0, places=6)  # 4.0 - 2.0

    def test_07_measurement_label_in_user_mode_correctly_identified(self):
        """用户坐标系模式下，测量标签同样应被正确识别为MEASUREMENT_INFO"""
        from utils.fast_layout import ElementType

        # 用户坐标系模式
        self.view.set_user_coordinate_mode(True)
        self.view.set_user_position(1.0, 1.0)
        self.view._handle_single_click(5.0, 6.0)

        # 找到测量标签
        measurement_text = None
        for t in self.view.text_objects:
            if hasattr(t, 'get_text') and '距离:' in t.get_text() and '角度:' in t.get_text():
                measurement_text = t
                break

        self.assertIsNotNone(measurement_text, "用户坐标系下应生成测量标签")

        # 验证类型识别正确（即便标签文本包含"[用户坐标系]"）
        element_type = self.view._get_element_type_from_text(measurement_text)
        self.assertEqual(
            element_type, ElementType.MEASUREMENT_INFO,
            f"用户坐标系下测量标签应被识别为MEASUREMENT_INFO，实际: {element_type}"
        )


class TestSceneRendererUserCoordinateTweaks20251213(unittest.TestCase):
    """SceneRenderer层：用户坐标系随动信息关闭 + 视觉一致性"""

    def setUp(self):
        self.figure = Figure(figsize=(6, 6), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.renderer = SceneRenderer(self.figure, self.axes)
        self.model = SceneModel()

        # 避免测试环境依赖真实canvas
        self.figure.canvas = MagicMock()
        self.figure.canvas.draw_idle = MagicMock()

    def test_01_renderer_no_coordinate_info_even_in_user_mode(self):
        """用户坐标系：SceneRenderer也不应绘制随动坐标信息框"""
        self.model.set_user_position(1.0, 2.0)

        # 即便输入异常类型，也不应出错（因为已直接清除并return）
        self.renderer.draw_coordinate_info("bad_x", None, self.model)  # type: ignore[arg-type]
        self.assertEqual(len(self.renderer._artists['coordinate_info']), 0)

    def test_02_renderer_user_axes_and_label_style(self):
        """用户坐标系：SceneRenderer轴线/标签样式与MatplotlibView一致"""
        self.model.set_user_position(1.0, 2.0)
        self.renderer.render(self.model)

        dashed_lines = [
            a for a in self.renderer._artists['user_coordinate_system']
            if hasattr(a, 'get_linestyle') and callable(getattr(a, 'get_linestyle'))
            and a.get_linestyle() == '--'
            and hasattr(a, 'get_linewidth')
        ]
        self.assertEqual(len(dashed_lines), 4, "SceneRenderer用户坐标系轴线应包含4条虚线（2主+2辅）")

        widths = sorted([round(float(ln.get_linewidth()), 2) for ln in dashed_lines])
        self.assertEqual(widths, [0.25, 0.25, 0.75, 0.75])

        colors = sorted([to_hex(ln.get_color()).lower() for ln in dashed_lines])
        self.assertTrue(all(c == '#d32f2f' for c in colors), "SceneRenderer用户坐标系轴线颜色应为红色 #d32f2f")

        # 标签检查
        text_obj = None
        for a in self.renderer._artists['user_coordinate_system']:
            if hasattr(a, 'get_text') and callable(getattr(a, 'get_text')):
                if '[用户] 位置' in a.get_text():
                    text_obj = a
                    break
        self.assertIsNotNone(text_obj, "SceneRenderer应绘制用户原点标签")

        pos_x, pos_y = text_obj.get_position()
        self.assertAlmostEqual(pos_x, 1.0, places=6)
        self.assertAlmostEqual(pos_y, 0.0, places=6)  # 2.0 - 2.0

        self.assertEqual(int(text_obj.get_fontsize()), 9)
        self.assertEqual(str(text_obj.get_fontweight()), 'bold')

        bbox_patch = text_obj.get_bbox_patch()
        self.assertIsNotNone(bbox_patch)
        face_rgba = bbox_patch.get_facecolor()
        self.assertAlmostEqual(face_rgba[3], 0.6, places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)


