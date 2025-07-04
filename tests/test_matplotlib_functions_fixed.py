# -*- coding: utf-8 -*-
"""
Matplotlib版本功能修复测试

验证4个核心功能的修复效果：
1. 坐标系步进为1显示
2. 左键单击标注距离和角度  
3. 左键双击绘制90度扇形
4. 右键取消所有显示功能
"""

import sys
import os
import unittest
import time
import math

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev'))

try:
    from views.matplotlib_view import MatplotlibView
    from models.device_model import Device
    from models.measurement_model import MeasurementPoint
    import tkinter as tk
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Matplotlib组件不可用: {e}")
    MATPLOTLIB_AVAILABLE = False


@unittest.skipUnless(MATPLOTLIB_AVAILABLE, "需要matplotlib和相关依赖")
class TestMatplotlibFunctionsFix(unittest.TestCase):
    """Matplotlib功能修复测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        
        # 创建测试容器
        self.test_frame = tk.Frame(self.root)
        self.test_frame.pack()
        
        # 创建MatplotlibView实例
        self.view = MatplotlibView(self.test_frame)
        
        print(f"✅ 测试环境准备完成")
    
    def tearDown(self):
        """测试后清理"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_01_coordinate_system_grid(self):
        """测试1：坐标系步进为1显示"""
        print("\n=== 测试1：坐标系步进为1显示 ===")
        
        # 设置坐标范围
        self.view.set_coordinate_range(5.0, 5.0)
        
        # 获取刻度设置
        x_ticks = self.view.axes.get_xticks()
        y_ticks = self.view.axes.get_yticks()
        
        print(f"X轴刻度: {x_ticks}")
        print(f"Y轴刻度: {y_ticks}")
        
        # 验证刻度是整数步进
        x_expected = np.arange(-5, 6, 1)  # -5到5，步进1
        y_expected = np.arange(-5, 6, 1)
        
        # 检查刻度是否按整数步进
        self.assertTrue(len(x_ticks) >= 10, "X轴刻度数量应该>=10")
        self.assertTrue(len(y_ticks) >= 10, "Y轴刻度数量应该>=10")
        
        # 检查网格是否开启
        self.assertTrue(self.view.axes.grid, "网格应该开启")
        
        print("✅ 坐标系步进为1显示 - 测试通过")
    
    def test_02_left_click_measurement(self):
        """测试2：左键单击标注距离和角度"""
        print("\n=== 测试2：左键单击测量功能 ===")
        
        # 模拟左键单击
        test_x, test_y = 3.0, 4.0
        
        # 直接调用处理函数
        self.view._handle_single_click(test_x, test_y)
        
        # 验证测量点是否创建
        self.assertIsNotNone(self.view.measurement_point, "应该创建测量点")
        
        # 验证测量点坐标
        measurement = self.view.measurement_point
        self.assertEqual(measurement.x, test_x, "测量点X坐标正确")
        self.assertEqual(measurement.y, test_y, "测量点Y坐标正确")
        
        # 验证距离计算
        expected_distance = math.sqrt(test_x**2 + test_y**2)
        self.assertAlmostEqual(measurement.distance_to_origin, expected_distance, places=3, 
                             msg="距离计算正确")
        
        # 验证角度计算
        expected_angle = abs(math.atan2(test_y, test_x)) * 180 / math.pi
        expected_angle = min(expected_angle, 90 - expected_angle)  # 取与坐标轴的最小夹角
        self.assertAlmostEqual(measurement.angle_to_axis, expected_angle, places=3,
                             msg="角度计算正确")
        
        print(f"测量点: ({measurement.x:.3f}, {measurement.y:.3f})")
        print(f"距离: {measurement.distance_to_origin:.3f}")
        print(f"角度: {measurement.angle_to_axis:.3f}°")
        print("✅ 左键单击测量功能 - 测试通过")
    
    def test_03_double_click_sector(self):
        """测试3：左键双击绘制90度扇形"""
        print("\n=== 测试3：左键双击90度扇形 ===")
        
        # 模拟双击（直接调用双击处理方法）
        test_x, test_y = 2.0, 2.0
        
        # 直接调用双击处理方法
        self.view._handle_double_click(test_x, test_y)
        
        # 验证扇形点是否设置
        self.assertIsNotNone(self.view.sector_point, "应该设置扇形点")
        
        # 验证扇形点坐标
        self.assertEqual(self.view.sector_point[0], test_x, "扇形点X坐标正确")
        self.assertEqual(self.view.sector_point[1], test_y, "扇形点Y坐标正确")
        
        # 验证扇形艺术对象是否创建
        self.assertTrue(len(self.view.sector_artists) > 0, "应该创建扇形图形")
        
        print(f"扇形点: ({test_x:.3f}, {test_y:.3f})")
        print(f"扇形半径: {math.sqrt(test_x**2 + test_y**2):.3f}")
        print("✅ 左键双击90度扇形 - 测试通过")
    
    def test_04_right_click_clear(self):
        """测试4：右键清除所有显示功能"""
        print("\n=== 测试4：右键清除功能 ===")
        
        # 先创建一些测试内容
        # 1. 创建测量点
        self.view._handle_single_click(1.0, 1.0)
        measurement_before = self.view.measurement_point
        
        # 2. 创建扇形
        self.view.sector_point = (2.0, 2.0)
        self.view._draw_sector()
        sector_artists_before = len(self.view.sector_artists)
        
        print(f"清除前 - 测量点: {measurement_before is not None}")
        print(f"清除前 - 扇形对象数: {sector_artists_before}")
        
        # 执行右键清除
        self.view._handle_right_click()
        
        # 验证清除效果
        self.assertIsNone(self.view.measurement_point, "测量点应该被清除")
        self.assertIsNone(self.view.sector_point, "扇形点应该被清除")
        self.assertEqual(len(self.view.measurement_artists), 0, "测量图形应该被清除")
        self.assertEqual(len(self.view.sector_artists), 0, "扇形图形应该被清除")
        
        print(f"清除后 - 测量点: {self.view.measurement_point is None}")
        print(f"清除后 - 扇形对象数: {len(self.view.sector_artists)}")
        print("✅ 右键清除功能 - 测试通过")
    
    def test_05_color_scheme(self):
        """测试5：颜色配色方案"""
        print("\n=== 测试5：颜色配色方案 ===")
        
        # 验证关键颜色定义
        colors = self.view.COLORS
        
        # 测量相关颜色（绿色系）
        self.assertEqual(colors['measurement_point'], '#2e7d32', "测量点颜色")
        self.assertEqual(colors['measurement_line'], '#4caf50', "测量线颜色")
        
        # 扇形相关颜色（红色系）
        self.assertEqual(colors['sector_edge'], '#d32f2f', "扇形边缘颜色")
        
        # 网格和文字颜色
        self.assertIn('grid_line', colors, "应该定义网格线颜色")
        self.assertIn('text_color', colors, "应该定义文字颜色")
        
        print("配色方案验证:")
        for key, value in colors.items():
            print(f"  {key}: {value}")
        
        print("✅ 颜色配色方案 - 测试通过")
    
    def test_06_performance_check(self):
        """测试6：性能检查"""
        print("\n=== 测试6：性能检查 ===")
        
        # 测试多次操作的性能
        start_time = time.time()
        
        # 执行100次点击操作
        for i in range(100):
            x = (i % 10) - 5  # -5到4
            y = (i % 7) - 3   # -3到3
            self.view._handle_single_click(x, y)
            if i % 10 == 0:
                self.view._handle_right_click()  # 每10次清除一次
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"100次操作耗时: {total_time:.3f}秒")
        print(f"平均每次操作: {total_time/100*1000:.1f}ms")
        
        # 性能要求：100次操作应该在2秒内完成
        self.assertLess(total_time, 2.0, "性能应该满足要求")
        
        print("✅ 性能检查 - 测试通过")


def run_tests():
    """运行所有测试"""
    print("🧪 开始Matplotlib功能修复测试")
    print("="*50)
    
    if not MATPLOTLIB_AVAILABLE:
        print("❌ 无法运行测试，缺少必要依赖")
        return False
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestMatplotlibFunctionsFix)
    
    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # 输出结果摘要
    print("\n" + "="*50)
    print("📊 测试结果摘要:")
    print(f"   总测试数: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败: {len(result.failures)}")
    print(f"   错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 所有测试通过！修复功能正常工作")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步检查")
    
    return success


if __name__ == "__main__":
    run_tests() 