#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扇形避让修复测试脚本

测试所有UI要素（设备信息框、测量信息框、用户位置信息框、十字动点信息框）
能否正确避开扇形区域，验证精确扇形几何计算和智能避让系统的修复效果。
"""

import sys
import os
import math
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from utils.calculation import Calculator
from utils.layout_manager import LayoutManager, LayoutElement, BoundingBox, ElementType
from models.device_model import Device


class SectorAvoidanceTestSuite:
    """扇形避让测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.test_results = []
        self.canvas_bounds = (-10.0, -10.0, 10.0, 10.0)
        self.layout_manager = LayoutManager(self.canvas_bounds)
        
        print("🧪 扇形避让修复测试套件初始化完成")
        print(f"📐 画布范围: {self.canvas_bounds}")
        print("=" * 60)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始扇形避让修复测试...")
        print()
        
        # 1. 扇形边界框计算精度测试
        self.test_sector_bounding_box_accuracy()
        
        # 2. 扇形-矩形重叠检测精度测试
        self.test_sector_rectangle_overlap_detection()
        
        # 3. 设备信息框避让扇形测试
        self.test_device_info_sector_avoidance()
        
        # 4. 测量信息框避让扇形测试
        self.test_measurement_info_sector_avoidance()
        
        # 5. 用户位置信息框避让扇形测试
        self.test_user_position_sector_avoidance()
        
        # 6. 十字动点信息框避让扇形测试
        self.test_coordinate_info_sector_avoidance()
        
        # 7. 综合场景测试
        self.test_comprehensive_avoidance_scenario()
        
        # 输出测试总结
        self.print_test_summary()
    
    def test_sector_bounding_box_accuracy(self):
        """测试扇形边界框计算精度"""
        print("📐 测试1: 扇形边界框计算精度")
        
        test_cases = [
            # (center_x, center_y, radius, start_angle, end_angle, 期望特征)
            (0, 0, 5, -45, 45, "第一象限90度扇形"),
            (2, 3, 3, 90, 180, "第二象限90度扇形"),
            (-1, -2, 4, 180, 270, "第三象限90度扇形"),
            (1, -1, 2, 270, 360, "第四象限90度扇形"),
            (0, 0, 6, 45, 135, "跨越Y轴正方向90度扇形"),
        ]
        
        for i, (cx, cy, radius, start_angle, end_angle, description) in enumerate(test_cases):
            print(f"  📊 子测试1.{i+1}: {description}")
            
            # 计算精确边界框
            bbox = Calculator.calculate_sector_bounding_box(cx, cy, radius, start_angle, end_angle)
            
            # 验证边界框是否合理
            bbox_width = bbox[2] - bbox[0]  # max_x - min_x
            bbox_height = bbox[3] - bbox[1]  # max_y - min_y
            
            # 边界框不应超过直径
            max_expected_size = 2 * radius
            
            success = (bbox_width <= max_expected_size and bbox_height <= max_expected_size and 
                      bbox_width > 0 and bbox_height > 0)
            
            print(f"     🔍 中心: ({cx}, {cy}), 半径: {radius}")
            print(f"     📏 边界框: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
            print(f"     📐 尺寸: {bbox_width:.2f} x {bbox_height:.2f}")
            print(f"     ✅ 结果: {'通过' if success else '失败'}")
            
            self.test_results.append(f"扇形边界框计算-{description}: {'✅ 通过' if success else '❌ 失败'}")
            print()
    
    def test_sector_rectangle_overlap_detection(self):
        """测试扇形-矩形重叠检测精度"""
        print("🔍 测试2: 扇形-矩形重叠检测精度")
        
        # 测试扇形：中心(0,0)，半径5，角度0-90度（第一象限）
        sector_center = (0, 0)
        sector_radius = 5
        sector_start = 0
        sector_end = 90
        
        test_rectangles = [
            # (x1, y1, x2, y2, 期望重叠程度, 描述)
            (1, 1, 2, 2, "高", "完全在扇形内的小矩形"),
            (4, 4, 6, 6, "中", "部分在扇形内的矩形"),
            (-2, -2, -1, -1, "无", "完全在扇形外的矩形"),
            (0, 0, 1, 1, "高", "包含扇形中心的矩形"),
            (2, -1, 3, 1, "低", "跨越扇形边界的矩形"),
        ]
        
        for i, (x1, y1, x2, y2, expected_level, description) in enumerate(test_rectangles):
            print(f"  📊 子测试2.{i+1}: {description}")
            
            overlap_ratio = Calculator.sector_rectangle_overlap(
                sector_center[0], sector_center[1], sector_radius,
                sector_start, sector_end, x1, y1, x2, y2
            )
            
            # 根据期望程度验证结果
            if expected_level == "无":
                success = overlap_ratio == 0.0
            elif expected_level == "低":
                success = 0.0 < overlap_ratio <= 0.3
            elif expected_level == "中":
                success = 0.3 < overlap_ratio <= 0.7
            elif expected_level == "高":
                success = overlap_ratio > 0.7
            else:
                success = True
            
            print(f"     📦 矩形: ({x1}, {y1}) 到 ({x2}, {y2})")
            print(f"     🔢 重叠比例: {overlap_ratio:.3f}")
            print(f"     🎯 期望程度: {expected_level}")
            print(f"     ✅ 结果: {'通过' if success else '失败'}")
            
            self.test_results.append(f"扇形重叠检测-{description}: {'✅ 通过' if success else '❌ 失败'}")
            print()
    
    def test_device_info_sector_avoidance(self):
        """测试设备信息框避让扇形"""
        print("📱 测试3: 设备信息框避让扇形")
        
        # 重置布局管理器
        self.layout_manager.clear_elements()
        
        # 添加扇形：中心(2, 2)，半径3，角度30-120度
        sector_center = (2, 2)
        sector_radius = 3
        sector_start = 30
        sector_end = 120
        
        sector_bbox_tuple = Calculator.calculate_sector_bounding_box(
            sector_center[0], sector_center[1], sector_radius, sector_start, sector_end
        )
        sector_bbox = BoundingBox(*sector_bbox_tuple)
        
        sector_element = LayoutElement(
            ElementType.SECTOR, sector_bbox, sector_center,
            priority=2, movable=False, element_id="test_sector",
            sector_center=sector_center,
            sector_radius=sector_radius,
            sector_start_angle=sector_start,
            sector_end_angle=sector_end
        )
        self.layout_manager.add_element(sector_element)
        
        # 测试设备在扇形附近的情况
        test_devices = [
            (1, 3, "设备在扇形边缘"),
            (3, 4, "设备在扇形覆盖区域"),
            (2, 1, "设备在扇形中心下方"),
            (0, 2, "设备在扇形左侧"),
        ]
        
        avoidance_success_count = 0
        
        for i, (device_x, device_y, description) in enumerate(test_devices):
            print(f"  📊 子测试3.{i+1}: {description}")
            
            # 计算设备信息框位置
            info_x, info_y, position_type = self.layout_manager.calculate_device_info_position(
                device_x, device_y, f"device_{i}"
            )
            
            # 创建信息框边界框
            box_width, box_height = 2.5, 1.2
            info_bbox = BoundingBox(
                info_x - box_width/2, info_y - box_height/2,
                info_x + box_width/2, info_y + box_height/2
            )
            
            # 检查信息框是否与扇形重叠
            overlap_ratio = Calculator.sector_rectangle_overlap(
                sector_center[0], sector_center[1], sector_radius,
                sector_start, sector_end,
                info_bbox.x_min, info_bbox.y_min, info_bbox.x_max, info_bbox.y_max
            )
            
            # 避让成功的标准：重叠比例应该很小（< 0.1）
            avoidance_successful = overlap_ratio < 0.1
            if avoidance_successful:
                avoidance_success_count += 1
            
            print(f"     📍 设备位置: ({device_x}, {device_y})")
            print(f"     📋 信息框位置: ({info_x:.2f}, {info_y:.2f}) - {position_type.value}")
            print(f"     🔢 与扇形重叠比例: {overlap_ratio:.3f}")
            print(f"     ✅ 避让结果: {'成功' if avoidance_successful else '失败'}")
            print()
        
        overall_success = avoidance_success_count >= len(test_devices) * 0.75  # 75%成功率
        self.test_results.append(f"设备信息框避让扇形: {'✅ 通过' if overall_success else '❌ 失败'} ({avoidance_success_count}/{len(test_devices)})")
    
    def test_measurement_info_sector_avoidance(self):
        """测试测量信息框避让扇形"""
        print("📏 测试4: 测量信息框避让扇形")
        
        # 重置布局管理器
        self.layout_manager.clear_elements()
        
        # 添加扇形：中心(-1, -1)，半径4，角度135-225度（第三象限）
        sector_center = (-1, -1)
        sector_radius = 4
        sector_start = 135
        sector_end = 225
        
        sector_bbox_tuple = Calculator.calculate_sector_bounding_box(
            sector_center[0], sector_center[1], sector_radius, sector_start, sector_end
        )
        sector_bbox = BoundingBox(*sector_bbox_tuple)
        
        sector_element = LayoutElement(
            ElementType.SECTOR, sector_bbox, sector_center,
            priority=2, movable=False, element_id="test_sector_measurement",
            sector_center=sector_center,
            sector_radius=sector_radius,
            sector_start_angle=sector_start,
            sector_end_angle=sector_end
        )
        self.layout_manager.add_element(sector_element)
        
        # 测试测量点在扇形附近的情况
        test_measurements = [
            (-2, -3, "测量点在扇形内部"),
            (-4, -2, "测量点在扇形边缘"),
            (0, -1, "测量点在扇形右侧"),
            (-1, 1, "测量点在扇形上方"),
        ]
        
        avoidance_success_count = 0
        
        for i, (measurement_x, measurement_y, description) in enumerate(test_measurements):
            print(f"  📊 子测试4.{i+1}: {description}")
            
            # 计算测量信息框位置
            preferred_offset = (0.3, 0.3)
            info_x, info_y = self.layout_manager.calculate_info_box_position(
                measurement_x, measurement_y, ElementType.MEASUREMENT_INFO, preferred_offset
            )
            
            # 创建信息框边界框
            box_width, box_height = 3.0, 1.8
            info_bbox = BoundingBox(
                info_x - box_width/2, info_y - box_height/2,
                info_x + box_width/2, info_y + box_height/2
            )
            
            # 检查信息框是否与扇形重叠
            overlap_ratio = Calculator.sector_rectangle_overlap(
                sector_center[0], sector_center[1], sector_radius,
                sector_start, sector_end,
                info_bbox.x_min, info_bbox.y_min, info_bbox.x_max, info_bbox.y_max
            )
            
            # 避让成功的标准：重叠比例应该很小（< 0.1）
            avoidance_successful = overlap_ratio < 0.1
            if avoidance_successful:
                avoidance_success_count += 1
            
            print(f"     📍 测量点位置: ({measurement_x}, {measurement_y})")
            print(f"     📋 信息框位置: ({info_x:.2f}, {info_y:.2f})")
            print(f"     🔢 与扇形重叠比例: {overlap_ratio:.3f}")
            print(f"     ✅ 避让结果: {'成功' if avoidance_successful else '失败'}")
            print()
        
        overall_success = avoidance_success_count >= len(test_measurements) * 0.75
        self.test_results.append(f"测量信息框避让扇形: {'✅ 通过' if overall_success else '❌ 失败'} ({avoidance_success_count}/{len(test_measurements)})")
    
    def test_user_position_sector_avoidance(self):
        """测试用户位置信息框避让扇形"""
        print("👤 测试5: 用户位置信息框避让扇形")
        
        # 重置布局管理器
        self.layout_manager.clear_elements()
        
        # 添加扇形：中心(0, 3)，半径2.5，角度270-360度（第四象限）
        sector_center = (0, 3)
        sector_radius = 2.5
        sector_start = 270
        sector_end = 360
        
        sector_bbox_tuple = Calculator.calculate_sector_bounding_box(
            sector_center[0], sector_center[1], sector_radius, sector_start, sector_end
        )
        sector_bbox = BoundingBox(*sector_bbox_tuple)
        
        sector_element = LayoutElement(
            ElementType.SECTOR, sector_bbox, sector_center,
            priority=2, movable=False, element_id="test_sector_user",
            sector_center=sector_center,
            sector_radius=sector_radius,
            sector_start_angle=sector_start,
            sector_end_angle=sector_end
        )
        self.layout_manager.add_element(sector_element)
        
        # 测试用户位置在扇形附近的情况
        test_positions = [
            (1, 2, "用户在扇形边缘"),
            (0, 1, "用户在扇形正下方"),
            (-1, 3, "用户在扇形左侧"),
        ]
        
        avoidance_success_count = 0
        
        for i, (user_x, user_y, description) in enumerate(test_positions):
            print(f"  📊 子测试5.{i+1}: {description}")
            
            # 计算用户位置信息框位置
            preferred_offset = (0, 0.7)
            info_x, info_y = self.layout_manager.calculate_info_box_position(
                user_x, user_y, ElementType.USER_POSITION, preferred_offset
            )
            
            # 创建信息框边界框
            box_width, box_height = 1.8, 1.0
            info_bbox = BoundingBox(
                info_x - box_width/2, info_y - box_height/2,
                info_x + box_width/2, info_y + box_height/2
            )
            
            # 检查信息框是否与扇形重叠
            overlap_ratio = Calculator.sector_rectangle_overlap(
                sector_center[0], sector_center[1], sector_radius,
                sector_start, sector_end,
                info_bbox.x_min, info_bbox.y_min, info_bbox.x_max, info_bbox.y_max
            )
            
            # 避让成功的标准：重叠比例应该很小（< 0.1）
            avoidance_successful = overlap_ratio < 0.1
            if avoidance_successful:
                avoidance_success_count += 1
            
            print(f"     📍 用户位置: ({user_x}, {user_y})")
            print(f"     📋 信息框位置: ({info_x:.2f}, {info_y:.2f})")
            print(f"     🔢 与扇形重叠比例: {overlap_ratio:.3f}")
            print(f"     ✅ 避让结果: {'成功' if avoidance_successful else '失败'}")
            print()
        
        overall_success = avoidance_success_count >= len(test_positions) * 0.67
        self.test_results.append(f"用户位置信息框避让扇形: {'✅ 通过' if overall_success else '❌ 失败'} ({avoidance_success_count}/{len(test_positions)})")
    
    def test_coordinate_info_sector_avoidance(self):
        """测试十字动点信息框避让扇形"""
        print("🎯 测试6: 十字动点信息框避让扇形")
        
        # 重置布局管理器
        self.layout_manager.clear_elements()
        
        # 添加扇形：中心(-3, 1)，半径3，角度45-135度（第二象限）
        sector_center = (-3, 1)
        sector_radius = 3
        sector_start = 45
        sector_end = 135
        
        sector_bbox_tuple = Calculator.calculate_sector_bounding_box(
            sector_center[0], sector_center[1], sector_radius, sector_start, sector_end
        )
        sector_bbox = BoundingBox(*sector_bbox_tuple)
        
        sector_element = LayoutElement(
            ElementType.SECTOR, sector_bbox, sector_center,
            priority=2, movable=False, element_id="test_sector_coordinate",
            sector_center=sector_center,
            sector_radius=sector_radius,
            sector_start_angle=sector_start,
            sector_end_angle=sector_end
        )
        self.layout_manager.add_element(sector_element)
        
        # 测试十字动点在扇形附近的情况
        test_coordinates = [
            (-2, 3, "坐标在扇形上方"),
            (-4, 2, "坐标在扇形内部"),
            (-1, 1, "坐标在扇形右侧"),
            (-3, -1, "坐标在扇形下方"),
        ]
        
        avoidance_success_count = 0
        
        for i, (coord_x, coord_y, description) in enumerate(test_coordinates):
            print(f"  📊 子测试6.{i+1}: {description}")
            
            # 计算坐标信息框位置
            preferred_offset = (0.8, 0.8)
            info_x, info_y = self.layout_manager.calculate_info_box_position(
                coord_x, coord_y, ElementType.COORDINATE_INFO, preferred_offset
            )
            
            # 创建信息框边界框
            box_width, box_height = 2.8, 1.5
            info_bbox = BoundingBox(
                info_x - box_width/2, info_y - box_height/2,
                info_x + box_width/2, info_y + box_height/2
            )
            
            # 检查信息框是否与扇形重叠
            overlap_ratio = Calculator.sector_rectangle_overlap(
                sector_center[0], sector_center[1], sector_radius,
                sector_start, sector_end,
                info_bbox.x_min, info_bbox.y_min, info_bbox.x_max, info_bbox.y_max
            )
            
            # 避让成功的标准：重叠比例应该很小（< 0.1）
            avoidance_successful = overlap_ratio < 0.1
            if avoidance_successful:
                avoidance_success_count += 1
            
            print(f"     📍 坐标位置: ({coord_x}, {coord_y})")
            print(f"     📋 信息框位置: ({info_x:.2f}, {info_y:.2f})")
            print(f"     🔢 与扇形重叠比例: {overlap_ratio:.3f}")
            print(f"     ✅ 避让结果: {'成功' if avoidance_successful else '失败'}")
            print()
        
        overall_success = avoidance_success_count >= len(test_coordinates) * 0.75
        self.test_results.append(f"坐标信息框避让扇形: {'✅ 通过' if overall_success else '❌ 失败'} ({avoidance_success_count}/{len(test_coordinates)})")
    
    def test_comprehensive_avoidance_scenario(self):
        """测试综合避让场景"""
        print("🌐 测试7: 综合避让场景")
        
        # 重置布局管理器
        self.layout_manager.clear_elements()
        
        # 添加多个扇形
        sectors = [
            ((1, 1), 2.5, 0, 90, "第一象限扇形"),
            ((-2, 2), 2, 90, 180, "第二象限扇形"),
            ((-1, -2), 1.5, 180, 270, "第三象限扇形"),
        ]
        
        for i, (center, radius, start_angle, end_angle, description) in enumerate(sectors):
            sector_bbox_tuple = Calculator.calculate_sector_bounding_box(
                center[0], center[1], radius, start_angle, end_angle
            )
            sector_bbox = BoundingBox(*sector_bbox_tuple)
            
            sector_element = LayoutElement(
                ElementType.SECTOR, sector_bbox, center,
                priority=2, movable=False, element_id=f"sector_{i}",
                sector_center=center,
                sector_radius=radius,
                sector_start_angle=start_angle,
                sector_end_angle=end_angle
            )
            self.layout_manager.add_element(sector_element)
        
        # 测试不同类型信息框的避让能力
        test_elements = [
            (0.5, 1.5, ElementType.DEVICE_INFO, "设备信息框"),
            (-1.5, 1.5, ElementType.MEASUREMENT_INFO, "测量信息框"),
            (-0.5, -1.5, ElementType.USER_POSITION, "用户位置信息框"),
            (2, -1, ElementType.COORDINATE_INFO, "坐标信息框"),
        ]
        
        total_success = 0
        total_tests = len(test_elements)
        
        print(f"  🎲 综合场景包含{len(sectors)}个扇形和{total_tests}种信息框")
        print()
        
        for i, (x, y, element_type, description) in enumerate(test_elements):
            print(f"  📊 子测试7.{i+1}: {description}避让多扇形")
            
            # 计算信息框位置
            info_x, info_y = self.layout_manager.calculate_info_box_position(
                x, y, element_type, (0.5, 0.5)
            )
            
            # 获取信息框尺寸
            box_width, box_height = self.layout_manager.info_box_sizes[element_type]
            info_bbox = BoundingBox(
                info_x - box_width/2, info_y - box_height/2,
                info_x + box_width/2, info_y + box_height/2
            )
            
            # 检查与所有扇形的重叠情况
            total_overlap = 0
            for sector_center, radius, start_angle, end_angle, _ in sectors:
                overlap = Calculator.sector_rectangle_overlap(
                    sector_center[0], sector_center[1], radius,
                    start_angle, end_angle,
                    info_bbox.x_min, info_bbox.y_min, info_bbox.x_max, info_bbox.y_max
                )
                total_overlap += overlap
            
            # 避让成功标准：总重叠比例 < 0.15
            avoidance_successful = total_overlap < 0.15
            if avoidance_successful:
                total_success += 1
            
            print(f"     📍 原始位置: ({x}, {y})")
            print(f"     📋 调整后位置: ({info_x:.2f}, {info_y:.2f})")
            print(f"     🔢 总重叠比例: {total_overlap:.3f}")
            print(f"     ✅ 避让结果: {'成功' if avoidance_successful else '失败'}")
            print()
        
        overall_success = total_success >= total_tests * 0.75
        self.test_results.append(f"综合避让场景: {'✅ 通过' if overall_success else '❌ 失败'} ({total_success}/{total_tests})")
    
    def print_test_summary(self):
        """输出测试总结"""
        print("=" * 60)
        print("📊 扇形避让修复测试总结")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if "✅ 通过" in result)
        total_tests = len(self.test_results)
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        print()
        
        print("详细结果:")
        for result in self.test_results:
            print(f"  {result}")
        
        print()
        if passed_tests == total_tests:
            print("🎉 所有测试通过！扇形避让修复成功！")
        elif passed_tests >= total_tests * 0.8:
            print("✅ 大部分测试通过，扇形避让修复基本成功！")
        else:
            print("⚠️ 部分测试失败，需要进一步优化扇形避让系统。")
        
        print("=" * 60)


def main():
    """主函数"""
    print("🧪 扇形避让修复测试脚本")
    print("测试目标: 验证所有UI要素能否正确避开扇形区域")
    print()
    
    # 创建并运行测试套件
    test_suite = SectorAvoidanceTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main() 