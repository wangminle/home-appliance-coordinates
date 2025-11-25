# -*- coding: utf-8 -*-
"""
数据持久化功能测试

测试ProjectManager和ConfigManager的核心功能
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from models.project_manager import ProjectManager
from models.config_manager import ConfigManager
from models.device_model import Device


class TestProjectManager:
    """测试ProjectManager类"""
    
    def setup_method(self):
        """每个测试前的准备工作"""
        self.project_manager = ProjectManager()
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"\n✅ 测试准备完成，临时目录: {self.temp_dir}")
    
    def teardown_method(self):
        """每个测试后的清理工作"""
        # 清理临时文件
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        print(f"✅ 测试清理完成")
    
    def test_save_project(self):
        """测试项目保存功能"""
        print("\n📝 测试1: 项目保存功能")
        
        # 准备测试数据
        devices = [
            Device("7寸屏", -2.625, 0),
            Device("4寸屏", -1.000, 3.544)
        ]
        coordinate_settings = {'x_range': 10.0, 'y_range': 10.0}
        user_coord_settings = {
            'enabled': False,
            'user_x': None,
            'user_y': None
        }
        
        # 保存项目
        file_path = self.temp_dir / "test_project.apc"
        success, message = self.project_manager.save_project(
            str(file_path),
            devices,
            coordinate_settings,
            user_coord_settings
        )
        
        # 验证结果
        assert success, f"保存失败: {message}"
        assert file_path.exists(), "项目文件未创建"
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'project_info' in data
        assert 'devices' in data
        assert 'coordinate_settings' in data
        assert len(data['devices']) == 2
        
        print(f"✅ 测试1通过: 项目保存成功")
    
    def test_load_project(self):
        """测试项目加载功能"""
        print("\n📝 测试2: 项目加载功能")
        
        # 先保存一个项目
        devices = [
            Device("测试设备1", 1.0, 2.0),
            Device("测试设备2", -3.0, 4.5)
        ]
        coordinate_settings = {'x_range': 5.0, 'y_range': 5.0}
        
        file_path = self.temp_dir / "test_load.apc"
        success1, _ = self.project_manager.save_project(
            str(file_path),
            devices,
            coordinate_settings
        )
        assert success1, "保存项目失败"
        
        # 加载项目
        success2, message, project_data = self.project_manager.load_project(str(file_path))
        
        # 验证结果
        assert success2, f"加载失败: {message}"
        assert project_data is not None
        assert 'devices_parsed' in project_data
        assert len(project_data['devices_parsed']) == 2
        
        # 验证设备数据
        loaded_devices = project_data['devices_parsed']
        assert loaded_devices[0].name == "测试设备1"
        assert loaded_devices[0].x == 1.0
        assert loaded_devices[0].y == 2.0
        
        print(f"✅ 测试2通过: 项目加载成功")
    
    def test_export_import_csv(self):
        """测试CSV导入导出功能"""
        print("\n📝 测试3: CSV导入导出功能")
        
        # 准备测试设备
        devices = [
            Device("设备A", 1.5, 2.5),
            Device("设备B", -3.0, 4.0),
            Device("设备C", 0.0, 0.0)
        ]
        
        # 导出到CSV
        csv_file = self.temp_dir / "test_devices.csv"
        success1, message1 = self.project_manager.export_devices_to_csv(str(csv_file), devices)
        
        assert success1, f"导出失败: {message1}"
        assert csv_file.exists(), "CSV文件未创建"
        
        # 导入CSV
        success2, message2, imported_devices = self.project_manager.import_devices_from_csv(str(csv_file))
        
        assert success2, f"导入失败: {message2}"
        assert len(imported_devices) == 3
        assert imported_devices[0].name == "设备A"
        assert imported_devices[1].x == -3.0
        assert imported_devices[2].y == 0.0
        
        print(f"✅ 测试3通过: CSV导入导出成功")
    
    def test_csv_with_invalid_data(self):
        """测试CSV导入时处理无效数据"""
        print("\n📝 测试4: CSV无效数据处理")
        
        # 创建包含无效数据的CSV
        csv_file = self.temp_dir / "invalid_data.csv"
        with open(csv_file, 'w', encoding='utf-8-sig') as f:
            f.write("设备名称,X坐标,Y坐标\n")
            f.write("正常设备,1.0,2.0\n")
            f.write("无效坐标,abc,def\n")  # 无效数据
            f.write(",3.0,4.0\n")  # 空名称
            f.write("正常设备2,5.0,6.0\n")
        
        # 导入CSV
        success, message, devices = self.project_manager.import_devices_from_csv(str(csv_file))
        
        # 应该成功导入有效的设备
        assert success, f"导入失败: {message}"
        assert len(devices) == 2  # 只有2个有效设备
        assert devices[0].name == "正常设备"
        assert devices[1].name == "正常设备2"
        
        print(f"✅ 测试4通过: 无效数据处理正确")
    
    def test_project_validation(self):
        """测试项目数据验证"""
        print("\n📝 测试5: 项目数据验证")
        
        # 测试空设备列表
        success1, _ = self.project_manager.save_project(
            str(self.temp_dir / "empty.apc"),
            [],
            {'x_range': 10.0, 'y_range': 10.0}
        )
        assert success1, "空设备列表应该允许保存"
        
        # 测试超大坐标范围
        devices = [Device("测试", 0, 0)]
        success2, _ = self.project_manager.save_project(
            str(self.temp_dir / "large_range.apc"),
            devices,
            {'x_range': 50.0, 'y_range': 50.0}
        )
        assert success2, "大坐标范围应该允许保存"
        
        print(f"✅ 测试5通过: 数据验证正确")


class TestConfigManager:
    """测试ConfigManager类"""
    
    def setup_method(self):
        """每个测试前的准备工作"""
        self.config_manager = ConfigManager()
        self.temp_dir = Path(tempfile.mkdtemp())
        # 临时修改配置目录
        self.original_config_dir = self.config_manager.config_dir
        self.config_manager.config_dir = self.temp_dir
        self.config_manager.config_file = self.temp_dir / "config.json"
        print(f"\n✅ 配置测试准备完成，临时目录: {self.temp_dir}")
    
    def teardown_method(self):
        """每个测试后的清理工作"""
        # 恢复原配置目录
        self.config_manager.config_dir = self.original_config_dir
        self.config_manager.config_file = self.original_config_dir / "config.json"
        
        # 清理临时文件
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        print(f"✅ 配置测试清理完成")
    
    def test_recent_files(self):
        """测试最近文件列表功能"""
        print("\n📝 测试6: 最近文件列表")
        
        # 创建测试文件
        test_file1 = self.temp_dir / "project1.apc"
        test_file2 = self.temp_dir / "project2.apc"
        test_file1.touch()
        test_file2.touch()
        
        # 添加最近文件
        assert self.config_manager.add_recent_file(str(test_file1))
        assert self.config_manager.add_recent_file(str(test_file2))
        
        # 获取最近文件列表
        recent_files = self.config_manager.get_recent_files()
        assert len(recent_files) == 2
        assert str(test_file2.absolute()) == recent_files[0]  # 最新的在前面
        
        # 清除最近文件
        assert self.config_manager.clear_recent_files()
        recent_files = self.config_manager.get_recent_files()
        assert len(recent_files) == 0
        
        print(f"✅ 测试6通过: 最近文件列表功能正确")
    
    def test_autosave_settings(self):
        """测试自动保存设置"""
        print("\n📝 测试7: 自动保存设置")
        
        # 测试默认值
        assert self.config_manager.is_autosave_enabled() == True
        assert self.config_manager.get_autosave_interval() == 300
        
        # 修改设置
        assert self.config_manager.set_autosave_enabled(False)
        assert self.config_manager.is_autosave_enabled() == False
        
        assert self.config_manager.set_autosave_interval(600)
        assert self.config_manager.get_autosave_interval() == 600
        
        # 测试最小间隔限制
        assert self.config_manager.set_autosave_interval(30)  # 小于60秒
        assert self.config_manager.get_autosave_interval() == 60  # 应该被调整为60
        
        print(f"✅ 测试7通过: 自动保存设置正确")
    
    def test_autosave_file_management(self):
        """测试自动保存文件管理"""
        print("\n📝 测试8: 自动保存文件管理")
        
        # 创建自动保存目录
        autosave_dir = self.config_manager.get_autosave_dir()
        autosave_dir.mkdir(exist_ok=True)
        
        # 创建多个草稿文件
        for i in range(7):
            draft_file = autosave_dir / f"draft_20250108_10000{i}.apc"
            draft_file.touch()
        
        # 清理旧文件，保留5个
        deleted_count = self.config_manager.clean_old_autosave_files(keep_count=5)
        assert deleted_count == 2, f"应该删除2个文件，实际删除{deleted_count}个"
        
        # 验证剩余文件数
        remaining_files = list(autosave_dir.glob("draft_*.apc"))
        assert len(remaining_files) == 5
        
        print(f"✅ 测试8通过: 自动保存文件管理正确")
    
    def test_preferences(self):
        """测试偏好设置"""
        print("\n📝 测试9: 偏好设置")
        
        # 设置偏好
        assert self.config_manager.set_preference('show_grid', True)
        assert self.config_manager.set_preference('auto_backup', False)
        assert self.config_manager.set_preference('theme', 'dark')
        
        # 读取偏好
        assert self.config_manager.get_preference('show_grid') == True
        assert self.config_manager.get_preference('auto_backup') == False
        assert self.config_manager.get_preference('theme') == 'dark'
        assert self.config_manager.get_preference('nonexistent', 'default') == 'default'
        
        print(f"✅ 测试9通过: 偏好设置正确")


def run_all_tests():
    """运行所有测试"""
    import pytest
    
    print("\n" + "="*60)
    print("开始运行数据持久化功能测试")
    print("="*60)
    
    # 运行测试
    result = pytest.main([
        __file__,
        '-v',  # 详细输出
        '--tb=short',  # 简短的traceback
        '-s'  # 显示print输出
    ])
    
    print("\n" + "="*60)
    if result == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("="*60)
    
    return result


if __name__ == '__main__':
    run_all_tests()

