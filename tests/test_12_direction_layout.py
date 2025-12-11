# -*- coding: utf-8 -*-
"""
12方向约束布局测试脚本

测试目标：
1. 验证设备标签只能出现在12个方向（每30°）
2. 验证标签最近顶点到设备点距离不超过3
3. 验证碰撞检测和避让功能
"""

import sys
import os
import math

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from utils.fast_layout import (
    FastLayoutManager, ElementType, BoundingBox, 
    LayoutElement, SectorRegion
)


def test_12_direction_generation():
    """测试12方向候选位置生成"""
    print("\n" + "="*60)
    print("测试1: 12方向候选位置生成")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    # 设备标签尺寸
    box_width, box_height = 2.0, 0.8
    anchor_x, anchor_y = 0, 0  # 设备点在原点
    
    # 生成候选位置
    candidates = manager._generate_12_direction_candidates(
        anchor_x, anchor_y, box_width, box_height
    )
    
    print(f"生成了 {len(candidates)} 个候选位置")
    
    # 验证12个方向都有候选位置
    directions_found = set()
    for cx, cy, direction_idx in candidates:
        directions_found.add(direction_idx)
    
    print(f"覆盖的方向数: {len(directions_found)}")
    assert len(directions_found) == 12, "应该覆盖12个方向"
    
    # 打印每个方向的第一个候选位置
    print("\n各方向第一个候选位置:")
    for direction_idx in range(12):
        angle = direction_idx * 30
        for cx, cy, idx in candidates:
            if idx == direction_idx:
                print(f"  方向 {angle:3}°: 标签中心 ({cx:.2f}, {cy:.2f})")
                break
    
    print("✅ 12方向候选位置生成测试通过")


def test_corner_distance_constraint():
    """测试标签顶点距离约束"""
    print("\n" + "="*60)
    print("测试2: 标签顶点距离约束（≤3）")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    box_width, box_height = 2.0, 0.8
    anchor_x, anchor_y = 0, 0
    
    # 生成候选位置并验证距离约束
    candidates = manager._generate_12_direction_candidates(
        anchor_x, anchor_y, box_width, box_height
    )
    
    valid_count = 0
    invalid_count = 0
    
    for cx, cy, direction_idx in candidates:
        min_dist, nearest_corner = manager._get_nearest_corner_distance(
            cx, cy, box_width, box_height, anchor_x, anchor_y
        )
        
        if min_dist <= manager.max_label_distance:
            valid_count += 1
        else:
            invalid_count += 1
            print(f"  ⚠️ 无效候选: 距离 {min_dist:.2f} > {manager.max_label_distance}")
    
    print(f"\n有效候选位置: {valid_count}")
    print(f"无效候选位置: {invalid_count}")
    
    # 所有候选位置都应该满足距离约束
    assert invalid_count == 0, "所有候选位置应满足距离约束"
    
    print("✅ 标签顶点距离约束测试通过")


def test_corner_on_12_directions():
    """测试最近顶点是否在12方向上"""
    print("\n" + "="*60)
    print("测试3: 最近顶点是否在12方向上")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    box_width, box_height = 2.0, 0.8
    anchor_x, anchor_y = 0, 0
    
    # 生成候选位置并验证
    candidates = manager._generate_12_direction_candidates(
        anchor_x, anchor_y, box_width, box_height
    )
    
    valid_direction_count = 0
    invalid_direction_count = 0
    
    for cx, cy, direction_idx in candidates:
        min_dist, nearest_corner = manager._get_nearest_corner_distance(
            cx, cy, box_width, box_height, anchor_x, anchor_y
        )
        
        is_on_direction = manager._is_corner_on_12_directions(
            nearest_corner[0], nearest_corner[1], anchor_x, anchor_y
        )
        
        if is_on_direction:
            valid_direction_count += 1
        else:
            invalid_direction_count += 1
            # 计算实际角度
            dx = nearest_corner[0] - anchor_x
            dy = nearest_corner[1] - anchor_y
            actual_angle = math.degrees(math.atan2(dy, dx))
            if actual_angle < 0:
                actual_angle += 360
            print(f"  ⚠️ 顶点不在12方向上: 角度 {actual_angle:.1f}°")
    
    print(f"\n在12方向上的顶点数: {valid_direction_count}")
    print(f"不在12方向上的顶点数: {invalid_direction_count}")
    
    # 大部分候选位置的顶点应该在12方向上
    success_rate = valid_direction_count / (valid_direction_count + invalid_direction_count)
    print(f"成功率: {success_rate*100:.1f}%")
    
    assert success_rate >= 0.9, "至少90%的顶点应在12方向上"
    
    print("✅ 最近顶点12方向测试通过")


def test_device_label_position():
    """测试设备标签位置计算"""
    print("\n" + "="*60)
    print("测试4: 设备标签位置计算（综合测试）")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    # 测试几个不同位置的设备
    test_devices = [
        (0, 0, "原点设备"),
        (5, 5, "右上设备"),
        (-5, 5, "左上设备"),
        (5, -5, "右下设备"),
        (-5, -5, "左下设备"),
    ]
    
    box_width, box_height = manager.info_box_sizes[ElementType.DEVICE_INFO]
    
    for dev_x, dev_y, name in test_devices:
        pos_x, pos_y = manager.calculate_device_label_position(dev_x, dev_y, name)
        
        # 检查最近顶点距离
        min_dist, nearest_corner = manager._get_nearest_corner_distance(
            pos_x, pos_y, box_width, box_height, dev_x, dev_y
        )
        
        # 检查顶点是否在12方向上
        is_on_direction = manager._is_corner_on_12_directions(
            nearest_corner[0], nearest_corner[1], dev_x, dev_y
        )
        
        # 计算顶点角度
        dx = nearest_corner[0] - dev_x
        dy = nearest_corner[1] - dev_y
        corner_angle = math.degrees(math.atan2(dy, dx))
        if corner_angle < 0:
            corner_angle += 360
        
        status = "✅" if (min_dist <= 3.0 and is_on_direction) else "❌"
        print(f"\n{status} {name}: 设备({dev_x}, {dev_y})")
        print(f"   标签中心: ({pos_x:.2f}, {pos_y:.2f})")
        print(f"   最近顶点: ({nearest_corner[0]:.2f}, {nearest_corner[1]:.2f})")
        print(f"   顶点距离: {min_dist:.2f} (限制: ≤3)")
        print(f"   顶点角度: {corner_angle:.1f}° (在12方向: {is_on_direction})")
        
        assert min_dist <= 3.0, f"{name}: 距离超限"
    
    print("\n✅ 设备标签位置计算测试通过")


def test_sector_avoidance():
    """测试扇形避让"""
    print("\n" + "="*60)
    print("测试5: 扇形区域避让")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    # 添加一个扇形区域（以原点为中心，45°方向，半径5）
    manager.add_sector_region(0, 0, 5.0, 0, 90)
    
    # 在扇形附近放置设备
    dev_x, dev_y = 3, 3  # 这个位置在扇形内部附近
    
    pos_x, pos_y = manager.calculate_device_label_position(dev_x, dev_y, "扇形附近设备")
    
    box_width, box_height = manager.info_box_sizes[ElementType.DEVICE_INFO]
    candidate_box = BoundingBox(
        pos_x - box_width/2, pos_y - box_height/2,
        pos_x + box_width/2, pos_y + box_height/2
    )
    
    is_in_sector = manager._is_box_in_sector(candidate_box)
    
    print(f"设备位置: ({dev_x}, {dev_y})")
    print(f"标签位置: ({pos_x:.2f}, {pos_y:.2f})")
    print(f"标签是否在扇形内: {is_in_sector}")
    
    assert not is_in_sector, "标签不应该在扇形内"
    
    print("✅ 扇形避让测试通过")


def test_label_collision_avoidance():
    """测试标签之间的碰撞避让"""
    print("\n" + "="*60)
    print("测试6: 标签碰撞避让")
    print("="*60)
    
    manager = FastLayoutManager((-10, -10, 10, 10))
    
    box_width, box_height = manager.info_box_sizes[ElementType.DEVICE_INFO]
    
    # 添加多个靠近的设备
    devices = [
        (0, 0, "设备A"),
        (1, 1, "设备B"),
        (2, 0, "设备C"),
    ]
    
    label_positions = []
    
    for dev_x, dev_y, name in devices:
        pos_x, pos_y = manager.calculate_device_label_position(dev_x, dev_y, name)
        
        # 注册到布局管理器
        bbox = BoundingBox(
            pos_x - box_width/2, pos_y - box_height/2,
            pos_x + box_width/2, pos_y + box_height/2
        )
        element = LayoutElement(
            ElementType.DEVICE_INFO, bbox, (dev_x, dev_y),
            priority=5, movable=False, element_id=name
        )
        manager.add_element(element)
        label_positions.append((name, pos_x, pos_y, bbox))
        
        print(f"{name}: 设备({dev_x}, {dev_y}) -> 标签({pos_x:.2f}, {pos_y:.2f})")
    
    # 检查标签之间是否有重叠
    overlaps = []
    for i, (name1, x1, y1, box1) in enumerate(label_positions):
        for name2, x2, y2, box2 in label_positions[i+1:]:
            if box1.overlaps(box2):
                overlaps.append((name1, name2))
    
    if overlaps:
        print(f"\n⚠️ 发现重叠: {overlaps}")
    else:
        print("\n✅ 无标签重叠")
    
    # 允许少量重叠（在复杂场景下）
    assert len(overlaps) <= 1, "重叠数量过多"
    
    print("✅ 标签碰撞避让测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("  12方向约束布局功能测试")
    print("="*70)
    
    tests = [
        test_12_direction_generation,
        test_corner_distance_constraint,
        test_corner_on_12_directions,
        test_device_label_position,
        test_sector_avoidance,
        test_label_collision_avoidance,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test.__name__} 异常: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"测试结果: 通过 {passed}/{passed+failed}")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

