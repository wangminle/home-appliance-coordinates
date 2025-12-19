# -*- coding: utf-8 -*-
"""
标签式布局测试脚本 V2.7

测试 InputPanel 的标签式布局功能

V2.7 更新：
- 添加 headless 环境检测，在无显示环境下自动跳过测试
"""

import sys
import os
import pytest

# 添加 dev/src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))


# ==================== Headless 环境检测 ====================

def _check_display_available() -> bool:
    """
    检测当前环境是否有可用的显示（用于判断是否在 headless 环境）
    
    Returns:
        True 如果显示可用，False 如果在 headless 环境
    """
    try:
        import tkinter as tk
        # 尝试创建一个临时的 Tk 窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        root.destroy()
        return True
    except Exception as e:
        print(f"⚠️ 检测到 headless 环境，无法创建 GUI 窗口: {e}")
        return False


# 全局检测显示是否可用
DISPLAY_AVAILABLE = _check_display_available()

if not DISPLAY_AVAILABLE:
    pytest.skip("检测到 headless 环境，跳过 GUI 测试", allow_module_level=True)

import tkinter as tk
from tkinter import ttk


def test_input_panel_creation():
    """测试 InputPanel 组件创建"""
    print("=" * 60)
    print("测试1: InputPanel 组件创建")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        # 创建测试窗口
        root = tk.Tk()
        root.title("标签式布局测试")
        root.geometry("500x700")
        
        # 创建测试框架
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        # 创建 InputPanel
        panel = InputPanel(test_frame)
        
        # 验证 Notebook 组件创建
        assert panel.notebook is not None, "Notebook 组件未创建"
        print("✅ Notebook 组件创建成功")
        
        # 验证四个标签页
        assert panel.tab_coordinate is not None, "坐标设置标签页未创建"
        assert panel.tab_background is not None, "背景设置标签页未创建"
        assert panel.tab_device is not None, "设备管理标签页未创建"
        assert panel.tab_action is not None, "系统操作标签页未创建"
        print("✅ 四个标签页创建成功")
        
        # 验证标签页数量
        tab_count = panel.notebook.index('end')
        assert tab_count == 4, f"标签页数量错误: 期望4, 实际{tab_count}"
        print(f"✅ 标签页数量正确: {tab_count}")
        
        # 验证默认选中第一个标签页
        current_tab = panel.get_current_tab()
        assert current_tab == 0, f"默认标签页错误: 期望0, 实际{current_tab}"
        print("✅ 默认选中坐标设置标签页")
        
        root.destroy()
        print("✅ 测试1 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tab_switching():
    """测试标签页切换功能"""
    print("=" * 60)
    print("测试2: 标签页切换功能")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("标签页切换测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 测试切换到每个标签页
        for i in range(4):
            panel.select_tab(i)
            root.update()
            current = panel.get_current_tab()
            assert current == i, f"切换到标签页{i}失败: 当前{current}"
            print(f"✅ 切换到标签页 {i} 成功")
        
        # 测试无效索引
        panel.select_tab(10)  # 超出范围，应该保持不变
        current = panel.get_current_tab()
        assert current == 3, f"无效索引处理错误: 当前{current}"
        print("✅ 无效索引处理正确")
        
        root.destroy()
        print("✅ 测试2 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinate_tab_components():
    """测试坐标设置标签页组件"""
    print("=" * 60)
    print("测试3: 坐标设置标签页组件")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("坐标设置组件测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 验证坐标范围变量
        assert panel.x_range_var is not None, "X范围变量未创建"
        assert panel.y_range_var is not None, "Y范围变量未创建"
        print("✅ 坐标范围变量正确")
        
        # 验证用户坐标系组件
        assert panel.user_coord_enabled_var is not None, "用户坐标系开关变量未创建"
        assert panel.user_position_frame is not None, "用户位置设置框架未创建"
        print("✅ 用户坐标系组件正确")
        
        # 验证状态指示器
        assert panel.coord_mode_label is not None, "坐标系模式标签未创建"
        assert panel.user_pos_label is not None, "用户位置标签未创建"
        print("✅ 状态指示器组件正确")
        
        # 测试坐标范围获取
        x_range, y_range = panel.get_coordinate_range()
        assert x_range == 10.0, f"默认X范围错误: {x_range}"
        assert y_range == 10.0, f"默认Y范围错误: {y_range}"
        print("✅ 坐标范围获取正确")
        
        root.destroy()
        print("✅ 测试3 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_device_tab_components():
    """测试设备管理标签页组件"""
    print("=" * 60)
    print("测试4: 设备管理标签页组件")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("设备管理组件测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 切换到设备管理标签页
        panel.select_tab(2)
        root.update()
        
        # 验证设备列表组件
        assert panel.device_treeview is not None, "设备列表 Treeview 未创建"
        print("✅ 设备列表 Treeview 正确")
        
        # 验证输入框
        assert panel.name_entry is not None, "名称输入框未创建"
        assert panel.x_entry is not None, "X坐标输入框未创建"
        assert panel.y_entry is not None, "Y坐标输入框未创建"
        assert panel.color_combobox is not None, "颜色选择框未创建"
        print("✅ 设备输入框组件正确")
        
        # 验证按钮
        assert panel.add_update_button is not None, "添加/更新按钮未创建"
        assert panel.delete_button is not None, "删除按钮未创建"
        print("✅ 设备操作按钮正确")
        
        root.destroy()
        print("✅ 测试4 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_background_tab_components():
    """测试背景设置标签页组件"""
    print("=" * 60)
    print("测试5: 背景设置标签页组件")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("背景设置组件测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 切换到背景设置标签页
        panel.select_tab(1)
        root.update()
        
        # 验证背景图UI组件
        assert panel.bg_info_label is not None, "图片信息标签未创建"
        assert panel.bg_ppu_var is not None, "像素比例变量未创建"
        assert panel.bg_alpha_var is not None, "透明度变量未创建"
        assert panel.bg_visible_var is not None, "显示开关变量未创建"
        assert panel.bg_remove_btn is not None, "移除按钮未创建"
        print("✅ 背景图 UI 组件正确")
        
        # 验证默认值
        assert panel.bg_ppu_var.get() == "100", f"默认像素比例错误: {panel.bg_ppu_var.get()}"
        assert panel.bg_alpha_var.get() == 0.5, f"默认透明度错误: {panel.bg_alpha_var.get()}"
        assert panel.bg_visible_var.get() == True, f"默认显示状态错误: {panel.bg_visible_var.get()}"
        print("✅ 背景设置默认值正确")
        
        root.destroy()
        print("✅ 测试5 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试5 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_callback_binding():
    """测试回调函数绑定"""
    print("=" * 60)
    print("测试6: 回调函数绑定")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("回调函数测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 测试回调是否被正确设置
        callback_triggered = {'count': 0}
        
        def test_callback(*args):
            callback_triggered['count'] += 1
        
        # 设置各类回调
        panel.set_range_change_callback(test_callback)
        panel.set_device_add_callback(test_callback)
        panel.set_export_callback(test_callback)
        panel.set_user_coord_toggle_callback(test_callback)
        panel.set_background_import_callback(test_callback)
        
        # 验证回调已设置
        assert panel.on_range_change_callback is not None, "范围变化回调未设置"
        assert panel.on_device_add_callback is not None, "设备添加回调未设置"
        assert panel.on_export_callback is not None, "导出回调未设置"
        assert panel.on_user_coord_toggle_callback is not None, "用户坐标系切换回调未设置"
        assert panel.on_background_import_callback is not None, "背景导入回调未设置"
        print("✅ 所有回调函数设置正确")
        
        root.destroy()
        print("✅ 测试6 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试6 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_coord_toggle():
    """测试用户坐标系切换功能"""
    print("=" * 60)
    print("测试7: 用户坐标系切换功能")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("用户坐标系测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 验证初始状态
        assert panel.is_user_coord_enabled() == False, "初始状态应为禁用"
        print("✅ 初始状态: 用户坐标系禁用")
        
        # 模拟启用用户坐标系
        panel.user_coord_enabled_var.set(True)
        panel._on_user_coord_toggle()
        root.update()
        
        assert panel.is_user_coord_enabled() == True, "启用后状态错误"
        print("✅ 用户坐标系启用成功")
        
        # 模拟禁用用户坐标系
        panel.user_coord_enabled_var.set(False)
        panel._on_user_coord_toggle()
        root.update()
        
        assert panel.is_user_coord_enabled() == False, "禁用后状态错误"
        print("✅ 用户坐标系禁用成功")
        
        root.destroy()
        print("✅ 测试7 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试7 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tab_changed_event_binding():
    """测试标签页切换事件绑定（Bug1修复验证）"""
    print("=" * 60)
    print("测试8: 标签页切换事件绑定 (Bug1修复)")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("标签页切换事件测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 验证事件绑定
        bindings = panel.notebook.bind()
        has_tab_changed = '<<NotebookTabChanged>>' in bindings
        assert has_tab_changed, "标签页切换事件未绑定"
        print("✅ <<NotebookTabChanged>> 事件已绑定")
        
        # 验证方法存在
        has_method = hasattr(panel, '_on_tab_changed') and callable(getattr(panel, '_on_tab_changed'))
        assert has_method, "_on_tab_changed 方法不存在"
        print("✅ _on_tab_changed 方法存在")
        
        # 测试切换时不会报错
        for i in range(4):
            panel.select_tab(i)
            root.update()
        print("✅ 标签页切换正常执行")
        
        root.destroy()
        print("✅ 测试8 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试8 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reset_coordinate_sync():
    """测试重置后坐标范围同步（Bug2修复验证）"""
    print("=" * 60)
    print("测试9: 重置坐标范围同步 (Bug2修复)")
    print("=" * 60)
    
    try:
        from views.input_panel import InputPanel
        
        root = tk.Tk()
        root.title("坐标范围同步测试")
        root.geometry("500x700")
        
        test_frame = ttk.Frame(root)
        test_frame.pack(fill='both', expand=True)
        
        panel = InputPanel(test_frame)
        
        # 设置非默认值
        panel.x_range_var.set("15")
        panel.y_range_var.set("15")
        print(f"设置坐标范围为: X=15, Y=15")
        
        # 调用 reset_inputs（模拟控制器的重置行为）
        panel.reset_inputs()
        
        # 验证坐标范围被正确重置为10.0
        x_range = panel.x_range_var.get()
        y_range = panel.y_range_var.get()
        
        assert x_range == "10.0", f"X范围错误: 期望10.0, 实际{x_range}"
        assert y_range == "10.0", f"Y范围错误: 期望10.0, 实际{y_range}"
        print(f"✅ 重置后坐标范围正确: X={x_range}, Y={y_range}")
        
        root.destroy()
        print("✅ 测试9 通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 测试9 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 开始运行标签式布局测试套件 V2.7")
    print("=" * 60 + "\n")
    
    # 检测是否在 headless 环境
    if not DISPLAY_AVAILABLE:
        print("⚠️ 检测到 headless 环境（无显示），GUI 测试将被跳过")
        print("=" * 60 + "\n")
    
    tests = [
        test_input_panel_creation,
        test_tab_switching,
        test_coordinate_tab_components,
        test_device_tab_components,
        test_background_tab_components,
        test_callback_binding,
        test_user_coord_toggle,
        test_tab_changed_event_binding,  # Bug1修复验证
        test_reset_coordinate_sync,       # Bug2修复验证
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {passed/(passed+failed)*100:.1f}%")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
