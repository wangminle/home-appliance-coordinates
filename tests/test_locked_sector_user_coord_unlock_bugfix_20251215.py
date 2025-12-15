#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锁定扇形在用户坐标系首次设置位置时未自动解锁的回归测试（2025-12-15）

背景：
- 当锁定扇形在世界坐标系下创建并锁定后，用户开启用户坐标系并首次设置用户位置（None -> (x, y)）
  参考中心会从(0,0)切换到用户位置。
- 旧逻辑仅在 old_position 非空时才自动解锁，导致锁仍保持，后续对比虚线仍用旧中心点计算，角度/距离错误。

本测试覆盖：
1) 正常功能：None -> 新用户位置 时应自动解锁
2) 边界条件：用户坐标系未启用时设置用户位置不应触发解锁（参考中心未变化）
3) 异常情况：非法用户位置输入应抛异常，且不应错误解锁
"""

import os
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch

# 避免测试环境依赖Tk后端
os.environ.setdefault('MPLBACKEND', 'Agg')

# 添加路径以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from views.matplotlib_view import MatplotlibView


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


class TestLockedSectorUserCoordUnlockBugfix20251215(unittest.TestCase):
    """锁定扇形 + 用户坐标系首次设置位置的自动解锁回归测试"""

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

    def _create_and_lock_sector_in_world_mode(self):
        """在世界坐标系下创建扇形并锁定（中心点应为(0,0)）"""
        self.view.user_coord_enabled = False
        self.view.user_position = None

        # 创建扇形测量数据（未锁定）
        self.view._handle_double_click(3.0, 4.0)
        self.assertTrue(self.view.locked_measurement.has_data())
        self.assertEqual(self.view.locked_measurement.center_point, (0.0, 0.0))
        self.assertFalse(self.view.locked_measurement.is_locked)

        # 锁定
        self.view._toggle_pin_lock()
        self.assertTrue(self.view.locked_measurement.is_locked)

    def test_01_unlock_when_first_setting_user_position_from_none(self):
        """正常功能：用户坐标系启用后，首次从None设置用户位置应自动解锁"""
        self._create_and_lock_sector_in_world_mode()

        # 启用用户坐标系（此时尚未设置user_position，不会触发自动解锁）
        self.view.set_user_coordinate_mode(True)
        self.assertTrue(self.view.locked_measurement.is_locked)

        # 首次设置用户位置（None -> (x,y)），参考中心变化，应自动解锁
        self.view.set_user_position(1.0, 1.0)
        self.assertFalse(self.view.locked_measurement.is_locked)

    def test_02_boundary_not_unlock_when_user_coord_disabled(self):
        """边界条件：用户坐标系未启用时设置用户位置，不应触发解锁（参考中心不变）"""
        self._create_and_lock_sector_in_world_mode()

        # 仍处于世界坐标系模式（user_coord_enabled=False），设置用户位置不应解锁
        self.view.set_user_position(2.0, 2.0)
        self.assertTrue(self.view.locked_measurement.is_locked)

    def test_03_exception_invalid_position_should_not_unlock(self):
        """异常情况：非法用户位置输入应抛异常，且不应错误解锁"""
        self._create_and_lock_sector_in_world_mode()
        self.view.set_user_coordinate_mode(True)

        with self.assertRaises((TypeError, ValueError)):
            # set_user_position 内部使用 {x:.3f}，非法类型应触发异常
            self.view.set_user_position("bad_x", 1.0)  # type: ignore[arg-type]

        # 异常不应导致锁状态被清除
        self.assertTrue(self.view.locked_measurement.is_locked)


if __name__ == '__main__':
    unittest.main()


