# -*- coding: utf-8 -*-
"""
背景户型图功能测试脚本

测试内容：
1. BackgroundImage 数据模型基本功能
2. 图片加载和像素比例映射
3. 序列化和反序列化
4. MatplotlibView 集成测试（手动）
"""

import sys
import os
import unittest
import tempfile
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent / 'dev' / 'src'
sys.path.insert(0, str(project_root))

from models.background_model import BackgroundImage


class TestBackgroundImageModel(unittest.TestCase):
    """BackgroundImage 数据模型单元测试"""
    
    def test_init_default_values(self):
        """测试默认初始化值"""
        bg = BackgroundImage()
        
        self.assertIsNone(bg.image_path)
        self.assertIsNone(bg.image_data)
        self.assertEqual(bg.pixel_width, 0)
        self.assertEqual(bg.pixel_height, 0)
        self.assertEqual(bg.dpi, 96)
        self.assertEqual(bg.pixels_per_unit, 100.0)
        self.assertEqual(bg.alpha, 0.5)
        self.assertTrue(bg.enabled)
    
    def test_is_valid_without_data(self):
        """测试无数据时 is_valid 返回 False"""
        bg = BackgroundImage()
        self.assertFalse(bg.is_valid())
        self.assertFalse(bg.is_loaded())
    
    def test_is_valid_with_data(self):
        """测试有数据时 is_valid 和 is_loaded"""
        bg = BackgroundImage()
        # 模拟图片数据
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        bg.enabled = True
        bg._calculate_extent()
        
        self.assertTrue(bg.is_valid())
        self.assertTrue(bg.is_loaded())
    
    def test_is_valid_disabled(self):
        """测试禁用时 is_valid 返回 False"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        bg.enabled = False
        
        self.assertFalse(bg.is_valid())
        self.assertTrue(bg.is_loaded())  # 仍然是已加载状态
    
    def test_pixels_per_unit_calculation(self):
        """测试像素比例计算"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((500, 1000, 3), dtype=np.uint8)  # 1000x500 像素
        bg.pixel_width = 1000
        bg.pixel_height = 500
        
        # 设置比例：100像素=1米
        bg.set_pixels_per_unit(100.0)
        
        actual_w, actual_h = bg.get_actual_size()
        self.assertAlmostEqual(actual_w, 10.0, places=5)  # 1000/100 = 10米
        self.assertAlmostEqual(actual_h, 5.0, places=5)   # 500/100 = 5米
    
    def test_center_alignment(self):
        """测试中心对齐坐标计算"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((400, 800, 3), dtype=np.uint8)  # 800x400 像素
        bg.pixel_width = 800
        bg.pixel_height = 400
        
        # 设置比例：100像素=1米 → 8米×4米
        bg.set_pixels_per_unit(100.0)
        
        # 验证中心对齐
        self.assertAlmostEqual(bg.x_min, -4.0, places=5)
        self.assertAlmostEqual(bg.x_max, 4.0, places=5)
        self.assertAlmostEqual(bg.y_min, -2.0, places=5)
        self.assertAlmostEqual(bg.y_max, 2.0, places=5)
    
    def test_set_alpha(self):
        """测试透明度设置"""
        bg = BackgroundImage()
        
        bg.set_alpha(0.3)
        self.assertAlmostEqual(bg.alpha, 0.3)
        
        bg.set_alpha(-0.5)  # 超出范围，应被截断
        self.assertAlmostEqual(bg.alpha, 0.0)
        
        bg.set_alpha(1.5)  # 超出范围，应被截断
        self.assertAlmostEqual(bg.alpha, 1.0)
    
    def test_set_enabled(self):
        """测试启用/禁用设置"""
        bg = BackgroundImage()
        
        bg.set_enabled(False)
        self.assertFalse(bg.enabled)
        
        bg.set_enabled(True)
        self.assertTrue(bg.enabled)
    
    def test_clear(self):
        """测试清除数据"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        bg.image_path = "/test/path.png"
        bg.pixels_per_unit = 200.0
        
        bg.clear()
        
        self.assertIsNone(bg.image_data)
        self.assertIsNone(bg.image_path)
        self.assertEqual(bg.pixel_width, 0)
        self.assertEqual(bg.pixel_height, 0)
        self.assertEqual(bg.pixels_per_unit, 100.0)  # 恢复默认值
    
    def test_serialization_without_image(self):
        """测试无图片数据时的序列化"""
        bg = BackgroundImage()
        bg.alpha = 0.7
        bg.enabled = False
        
        data = bg.to_dict(embed_image=False)
        
        self.assertIsNone(data['image_path'])
        self.assertNotIn('image_base64', data)
        self.assertEqual(data['alpha'], 0.7)
        self.assertEqual(data['enabled'], False)
    
    def test_serialization_with_image(self):
        """测试有图片数据时的序列化（嵌入Base64）"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((10, 10, 3), dtype=np.uint8)
        bg.pixel_width = 10
        bg.pixel_height = 10
        bg.alpha = 0.6
        
        data = bg.to_dict(embed_image=True)
        
        self.assertIn('image_base64', data)
        self.assertIsInstance(data['image_base64'], str)
        self.assertEqual(data['alpha'], 0.6)
    
    def test_deserialization(self):
        """测试反序列化"""
        data = {
            'image_path': '/test/path.png',
            'pixel_width': 200,
            'pixel_height': 100,
            'dpi': 72,
            'pixels_per_unit': 50.0,
            'alpha': 0.8,
            'enabled': False,
        }
        
        bg = BackgroundImage.from_dict(data)
        
        self.assertEqual(bg.image_path, '/test/path.png')
        self.assertEqual(bg.pixel_width, 200)
        self.assertEqual(bg.pixel_height, 100)
        self.assertEqual(bg.dpi, 72)
        self.assertEqual(bg.pixels_per_unit, 50.0)
        self.assertAlmostEqual(bg.alpha, 0.8)
        self.assertFalse(bg.enabled)
    
    def test_get_info_text_without_data(self):
        """测试无数据时的信息文本"""
        bg = BackgroundImage()
        info = bg.get_info_text()
        self.assertEqual(info, "未加载图片")
    
    def test_get_info_text_with_data(self):
        """测试有数据时的信息文本"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((500, 1000, 3), dtype=np.uint8)
        bg.pixel_width = 1000
        bg.pixel_height = 500
        bg.dpi = 96
        bg.set_pixels_per_unit(100.0)
        
        info = bg.get_info_text()
        
        self.assertIn("1000", info)  # 包含宽度
        self.assertIn("500", info)   # 包含高度
        self.assertIn("96", info)    # 包含DPI
        self.assertIn("10.0", info)  # 包含实际宽度
        self.assertIn("5.0", info)   # 包含实际高度
    
    def test_get_extent(self):
        """测试获取坐标范围"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((400, 800, 3), dtype=np.uint8)
        bg.pixel_width = 800
        bg.pixel_height = 400
        bg.set_pixels_per_unit(100.0)
        
        extent = bg.get_extent()
        
        self.assertEqual(len(extent), 4)
        self.assertAlmostEqual(extent[0], -4.0)  # x_min
        self.assertAlmostEqual(extent[1], 4.0)   # x_max
        self.assertAlmostEqual(extent[2], -2.0)  # y_min
        self.assertAlmostEqual(extent[3], 2.0)   # y_max
    
    def test_repr(self):
        """测试字符串表示"""
        bg = BackgroundImage()
        
        # 无数据时
        repr_str = repr(bg)
        self.assertIn("未加载", repr_str)
        
        # 有数据时
        bg.image_data = np.zeros((500, 1000, 3), dtype=np.uint8)
        bg.pixel_width = 1000
        bg.pixel_height = 500
        bg.set_pixels_per_unit(100.0)
        bg.alpha = 0.6
        
        repr_str = repr(bg)
        self.assertIn("1000", repr_str)
        self.assertIn("500", repr_str)
        self.assertIn("0.6", repr_str)


class TestBackgroundImageEdgeCases(unittest.TestCase):
    """BackgroundImage 边界条件测试"""
    
    def test_invalid_pixels_per_unit(self):
        """测试无效的像素比例"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        
        # 设置无效值（0或负数）
        result = bg.set_pixels_per_unit(0)
        self.assertFalse(result)
        
        result = bg.set_pixels_per_unit(-50)
        self.assertFalse(result)
    
    def test_very_large_image(self):
        """测试大尺寸图片"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((10000, 10000, 3), dtype=np.uint8)
        bg.pixel_width = 10000
        bg.pixel_height = 10000
        
        # 100像素=1米 → 100m x 100m
        bg.set_pixels_per_unit(100.0)
        
        actual_w, actual_h = bg.get_actual_size()
        self.assertAlmostEqual(actual_w, 100.0)
        self.assertAlmostEqual(actual_h, 100.0)
    
    def test_very_small_pixels_per_unit(self):
        """测试极小的像素比例（大实际尺寸）"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        
        # 1像素=1米 → 100m x 100m
        bg.set_pixels_per_unit(1.0)
        
        actual_w, actual_h = bg.get_actual_size()
        self.assertAlmostEqual(actual_w, 100.0)
        self.assertAlmostEqual(actual_h, 100.0)
    
    def test_very_large_pixels_per_unit(self):
        """测试极大的像素比例（小实际尺寸）"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((1000, 1000, 3), dtype=np.uint8)
        bg.pixel_width = 1000
        bg.pixel_height = 1000
        
        # 1000像素=1米 → 1m x 1m
        bg.set_pixels_per_unit(1000.0)
        
        actual_w, actual_h = bg.get_actual_size()
        self.assertAlmostEqual(actual_w, 1.0)
        self.assertAlmostEqual(actual_h, 1.0)


class TestBackgroundImageSerialization(unittest.TestCase):
    """BackgroundImage 序列化/反序列化测试"""
    
    def test_roundtrip_serialization(self):
        """测试序列化-反序列化完整往返"""
        # 创建原始对象
        original = BackgroundImage()
        original.image_data = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
        original.pixel_width = 100
        original.pixel_height = 50
        original.dpi = 150
        original.pixels_per_unit = 25.0
        original.alpha = 0.35
        original.enabled = False
        original._calculate_extent()
        
        # 序列化
        data = original.to_dict(embed_image=True)
        
        # 反序列化
        restored = BackgroundImage.from_dict(data)
        
        # 验证
        self.assertEqual(restored.pixel_width, original.pixel_width)
        self.assertEqual(restored.pixel_height, original.pixel_height)
        self.assertEqual(restored.dpi, original.dpi)
        self.assertAlmostEqual(restored.pixels_per_unit, original.pixels_per_unit)
        self.assertAlmostEqual(restored.alpha, original.alpha)
        self.assertEqual(restored.enabled, original.enabled)
        
        # 验证图片数据
        self.assertIsNotNone(restored.image_data)
        self.assertEqual(restored.image_data.shape, original.image_data.shape)
    
    def test_serialization_without_embed(self):
        """测试不嵌入图片数据的序列化"""
        bg = BackgroundImage()
        bg.image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        bg.pixel_width = 100
        bg.pixel_height = 100
        bg.image_path = "/test/path.png"
        
        data = bg.to_dict(embed_image=False)
        
        self.assertNotIn('image_base64', data)
        self.assertEqual(data['image_path'], "/test/path.png")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("背景户型图功能单元测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBackgroundImageModel))
    suite.addTests(loader.loadTestsFromTestCase(TestBackgroundImageEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestBackgroundImageSerialization))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print("\n出错的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

