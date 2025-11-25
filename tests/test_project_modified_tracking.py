# -*- coding: utf-8 -*-
"""
测试项目修改状态跟踪功能

测试目标：
1. [P1] 验证所有编辑操作都会正确标记项目为已修改
2. [P2] 验证项目加载时用户坐标系状态的完整重置

创建时间: 2025-01-08
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from datetime import datetime
import tempfile
import json

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'dev' / 'src'))

from models.device_model import Device
from models.device_manager import DeviceManager
from models.project_manager import ProjectManager
from controllers.matplotlib_controller import MatplotlibController


class TestProjectModifiedTracking:
    """测试项目修改状态跟踪"""
    
    def __init__(self):
        self.test_results = []
        self.root = None
        self.controller = None
        self.temp_dir = tempfile.mkdtemp()
        
    def setup(self):
        """初始化测试环境"""
        print("\n" + "="*80)
        print("开始测试：项目修改状态跟踪")
        print("="*80)
        
        # 创建Tkinter根窗口
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏窗口
        
        # 创建控制器
        self.controller = MatplotlibController(self.root)
        
        # 确保初始状态为未修改
        self.controller.project_manager.is_modified = False
        
    def teardown(self):
        """清理测试环境"""
        if self.root:
            self.root.destroy()
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'message': message,
            'time': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if message:
            print(f"    详情: {message}")
    
    # ==================== Bug 1测试：编辑操作标记修改 ====================
    
    def test_range_change_marks_modified(self):
        """测试：更改坐标范围会标记项目为已修改"""
        test_name = "[Bug1] 更改坐标范围标记修改"
        
        try:
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：更改坐标范围
            self.controller._on_range_change(15.0, 15.0)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "坐标范围变化正确标记为已修改")
            else:
                self.log_result(test_name, False, "坐标范围变化未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_user_coord_toggle_marks_modified(self):
        """测试：切换用户坐标系会标记项目为已修改"""
        test_name = "[Bug1] 切换用户坐标系标记修改"
        
        try:
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：启用用户坐标系
            self.controller._on_user_coord_toggle(True)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "用户坐标系切换正确标记为已修改")
            else:
                self.log_result(test_name, False, "用户坐标系切换未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_user_position_set_marks_modified(self):
        """测试：设置用户位置会标记项目为已修改"""
        test_name = "[Bug1] 设置用户位置标记修改"
        
        try:
            # 先启用用户坐标系
            self.controller._on_user_coord_toggle(True)
            
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：设置用户位置
            self.controller._on_user_position_set(1.5, 2.5)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "用户位置设置正确标记为已修改")
            else:
                self.log_result(test_name, False, "用户位置设置未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_add_device_marks_modified(self):
        """测试：添加设备会标记项目为已修改"""
        test_name = "[Bug1] 添加设备标记修改"
        
        try:
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：添加设备
            self.controller.add_device("测试设备1", 3.0, 4.0)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "添加设备正确标记为已修改")
            else:
                self.log_result(test_name, False, "添加设备未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_update_device_marks_modified(self):
        """测试：更新设备会标记项目为已修改"""
        test_name = "[Bug1] 更新设备标记修改"
        
        try:
            # 先添加一个设备
            self.controller.add_device("测试设备2", 1.0, 1.0)
            devices = self.controller.get_all_devices()
            
            if not devices:
                self.log_result(test_name, False, "无法添加测试设备")
                return
            
            device_id = devices[0].id
            
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：更新设备
            self.controller.update_device(device_id, "更新的设备", 2.0, 2.0)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "更新设备正确标记为已修改")
            else:
                self.log_result(test_name, False, "更新设备未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_delete_device_marks_modified(self):
        """测试：删除设备会标记项目为已修改"""
        test_name = "[Bug1] 删除设备标记修改"
        
        try:
            # 先添加一个设备
            self.controller.add_device("测试设备3", 5.0, 5.0)
            devices = self.controller.get_all_devices()
            
            if not devices:
                self.log_result(test_name, False, "无法添加测试设备")
                return
            
            device_id = devices[0].id
            
            # 重置修改标志
            self.controller.project_manager.is_modified = False
            
            # 执行操作：删除设备
            self.controller.delete_device(device_id)
            
            # 验证
            if self.controller.project_manager.is_modified:
                self.log_result(test_name, True, "删除设备正确标记为已修改")
            else:
                self.log_result(test_name, False, "删除设备未标记为已修改")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    # ==================== Bug 2测试：加载项目时重置用户坐标系状态 ====================
    
    def test_load_project_with_user_coord_enabled(self):
        """测试：加载启用用户坐标系的项目"""
        test_name = "[Bug2] 加载启用用户坐标系的项目"
        
        try:
            # 先清理状态，禁用用户坐标系
            try:
                self.controller._on_user_coord_toggle(False)
            except:
                pass
            
            # 创建测试项目文件（启用用户坐标系）
            test_project = {
                'project_info': {
                    'name': '测试项目',
                    'version': '1.0',
                    'created_time': datetime.now().isoformat(),
                    'modified_time': datetime.now().isoformat(),
                    'description': '测试项目',
                    'author': ''
                },
                'coordinate_settings': {
                    'x_range': 10.0,
                    'y_range': 10.0
                },
                'user_coordinate_system': {
                    'enabled': True,
                    'user_x': 2.0,
                    'user_y': 3.0
                },
                'devices': []
            }
            
            # 保存测试项目
            test_file = Path(self.temp_dir) / "test_with_user_coord.apc"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_project, f, ensure_ascii=False, indent=2)
            
            # 加载项目（抑制消息框）
            try:
                self.controller._load_project_file(str(test_file))
            except:
                pass  # 忽略视图错误
            
            # 验证用户坐标系状态
            user_coord_enabled = self.controller.canvas_view.user_coord_enabled
            user_position = self.controller.canvas_view.user_position
            
            if user_coord_enabled and user_position == (2.0, 3.0):
                self.log_result(test_name, True, 
                    f"用户坐标系正确恢复: enabled={user_coord_enabled}, position={user_position}")
            else:
                self.log_result(test_name, False, 
                    f"用户坐标系恢复失败: enabled={user_coord_enabled}, position={user_position}")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def test_load_project_with_user_coord_disabled(self):
        """测试：加载禁用用户坐标系的项目（在之前有用户坐标系的情况下）"""
        test_name = "[Bug2] 加载禁用用户坐标系的项目时清理旧状态"
        
        try:
            # 首先设置一个用户坐标系
            try:
                self.controller._on_user_coord_toggle(True)
                self.controller._on_user_position_set(5.0, 6.0)
            except:
                pass  # 忽略视图错误
            
            # 验证设置成功
            if not self.controller.canvas_view.user_coord_enabled:
                self.log_result(test_name, False, "前置条件失败：无法启用用户坐标系")
                return
            
            # 创建测试项目文件（禁用用户坐标系）
            test_project = {
                'project_info': {
                    'name': '测试项目2',
                    'version': '1.0',
                    'created_time': datetime.now().isoformat(),
                    'modified_time': datetime.now().isoformat(),
                    'description': '测试项目',
                    'author': ''
                },
                'coordinate_settings': {
                    'x_range': 10.0,
                    'y_range': 10.0
                },
                'user_coordinate_system': {
                    'enabled': False,
                    'user_x': None,
                    'user_y': None
                },
                'devices': []
            }
            
            # 保存测试项目
            test_file = Path(self.temp_dir) / "test_without_user_coord.apc"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_project, f, ensure_ascii=False, indent=2)
            
            # 加载项目（抑制消息框）
            try:
                self.controller._load_project_file(str(test_file))
            except:
                pass  # 忽略视图错误
            
            # 验证用户坐标系状态被清理
            user_coord_enabled = self.controller.canvas_view.user_coord_enabled
            user_position = self.controller.canvas_view.user_position
            
            if not user_coord_enabled and user_position is None:
                self.log_result(test_name, True, 
                    "用户坐标系状态正确清理: enabled=False, position=None")
            else:
                self.log_result(test_name, False, 
                    f"用户坐标系状态清理失败: enabled={user_coord_enabled}, position={user_position}")
                
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    # ==================== 运行所有测试 ====================
    
    def run_all_tests(self):
        """运行所有测试"""
        self.setup()
        
        try:
            print("\n" + "-"*80)
            print("Bug 1 测试：编辑操作标记修改")
            print("-"*80)
            
            self.test_range_change_marks_modified()
            self.test_user_coord_toggle_marks_modified()
            self.test_user_position_set_marks_modified()
            self.test_add_device_marks_modified()
            self.test_update_device_marks_modified()
            self.test_delete_device_marks_modified()
            
            print("\n" + "-"*80)
            print("Bug 2 测试：加载项目时重置用户坐标系状态")
            print("-"*80)
            
            self.test_load_project_with_user_coord_enabled()
            self.test_load_project_with_user_coord_disabled()
            
        finally:
            self.teardown()
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("测试摘要")
        print("="*80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed} 个测试 ✅")
        print(f"失败: {failed} 个测试 ❌")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "="*80)


def main():
    """主函数"""
    print("项目修改状态跟踪Bug修复测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = TestProjectModifiedTracking()
    tester.run_all_tests()


if __name__ == "__main__":
    main()

