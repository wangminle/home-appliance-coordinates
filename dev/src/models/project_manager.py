# -*- coding: utf-8 -*-
"""
项目文件管理器

负责项目文件的保存、加载、导入和导出功能
支持JSON格式的项目文件和CSV格式的设备列表
"""

import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from models.device_model import Device


class ProjectManagerError(Exception):
    """项目管理器异常基类"""
    pass


class ProjectFileError(ProjectManagerError):
    """项目文件错误"""
    pass


class ProjectValidationError(ProjectManagerError):
    """项目数据验证错误"""
    pass


class ProjectManager:
    """
    项目文件管理器
    
    管理项目数据的持久化，包括：
    - JSON格式项目文件保存/加载
    - CSV格式设备列表导入/导出
    - 数据验证和错误处理
    """
    
    # 项目文件版本
    PROJECT_VERSION = "1.0"
    
    # 文件扩展名
    PROJECT_EXTENSION = ".apc"  # Appliance Coordinates Project
    CSV_EXTENSION = ".csv"
    
    def __init__(self):
        """初始化项目管理器"""
        self.current_project_path: Optional[Path] = None
        self.current_project_name: str = "未命名项目"
        self.is_modified: bool = False
        print("✅ ProjectManager初始化完成")
    
    # ==================== 项目信息管理 ====================
    
    def set_project_path(self, file_path: str) -> None:
        """
        设置当前项目路径
        
        Args:
            file_path: 项目文件路径
        """
        self.current_project_path = Path(file_path)
        self.current_project_name = self.current_project_path.stem
        self.is_modified = False
    
    def mark_modified(self) -> None:
        """标记项目已修改"""
        self.is_modified = True
    
    def get_project_title(self) -> str:
        """
        获取项目标题（用于窗口标题）
        
        Returns:
            项目标题字符串
        """
        title = self.current_project_name
        if self.is_modified:
            title += " *"
        return title
    
    # ==================== JSON项目文件操作 ====================
    
    def save_project(self, 
                    file_path: str,
                    devices: List[Device],
                    coordinate_settings: Dict[str, float],
                    user_coord_settings: Optional[Dict[str, Any]] = None,
                    project_info: Optional[Dict[str, str]] = None,
                    label_positions: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[bool, str]:
        """
        保存项目到JSON文件
        
        V2.1: 添加标签位置持久化支持
        
        Args:
            file_path: 保存路径
            devices: 设备列表
            coordinate_settings: 坐标系统设置 {'x_range': 5.0, 'y_range': 5.0}
            user_coord_settings: 用户坐标系设置（可选）
            project_info: 项目信息（可选）
            label_positions: 标签位置字典（可选，仅保存手动位置）
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 构建项目数据结构
            project_data = self._build_project_data(
                devices,
                coordinate_settings,
                user_coord_settings,
                project_info,
                label_positions
            )
            
            # 验证数据
            is_valid, error_msg = self._validate_project_data(project_data)
            if not is_valid:
                raise ProjectValidationError(f"项目数据验证失败: {error_msg}")
            
            # 确保目录存在
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入JSON文件
            with open(file_path_obj, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # 更新项目状态（仅在非草稿模式下更新）
            self.set_project_path(str(file_path_obj))
            
            print(f"✅ 项目保存成功: {file_path_obj}")
            return True, f"项目已保存到: {file_path_obj.name}"
            
        except ProjectValidationError as e:
            error_msg = str(e)
            print(f"❌ 项目保存失败: {error_msg}")
            return False, error_msg
        except IOError as e:
            error_msg = f"文件写入失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"保存项目时发生未知错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def save_draft(self, 
                   file_path: str,
                   devices: List[Device],
                   coordinate_settings: Dict[str, float],
                   user_coord_settings: Optional[Dict[str, Any]] = None,
                   project_info: Optional[Dict[str, str]] = None,
                   label_positions: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[bool, str]:
        """
        保存草稿到JSON文件（不更新项目状态）
        
        与 save_project 类似，但不会修改 current_project_path 和 is_modified 状态。
        专门用于自动保存功能。
        
        V2.1: 添加标签位置持久化支持
        
        Args:
            file_path: 保存路径
            devices: 设备列表
            coordinate_settings: 坐标系统设置
            user_coord_settings: 用户坐标系设置（可选）
            project_info: 项目信息（可选）
            label_positions: 标签位置字典（可选）
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 构建项目数据结构
            project_data = self._build_project_data(
                devices,
                coordinate_settings,
                user_coord_settings,
                project_info,
                label_positions
            )
            
            # 验证数据
            is_valid, error_msg = self._validate_project_data(project_data)
            if not is_valid:
                raise ProjectValidationError(f"项目数据验证失败: {error_msg}")
            
            # 确保目录存在
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入JSON文件
            with open(file_path_obj, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # 注意：不更新项目状态，保持 current_project_path 和 is_modified 不变
            
            print(f"💾 草稿保存成功: {file_path_obj}")
            return True, f"草稿已保存到: {file_path_obj.name}"
            
        except ProjectValidationError as e:
            error_msg = str(e)
            print(f"❌ 草稿保存失败: {error_msg}")
            return False, error_msg
        except IOError as e:
            error_msg = f"文件写入失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"保存草稿时发生未知错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def load_project(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        从JSON文件加载项目
        
        Args:
            file_path: 项目文件路径
            
        Returns:
            (成功标志, 消息, 项目数据字典)
        """
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                raise ProjectFileError(f"项目文件不存在: {file_path_obj}")
            
            # 读取JSON文件
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 验证数据
            is_valid, error_msg = self._validate_project_data(project_data)
            if not is_valid:
                raise ProjectValidationError(f"项目文件格式错误: {error_msg}")
            
            # 解析设备数据
            project_data['devices_parsed'] = self._parse_devices(project_data.get('devices', []))
            
            # V2.1: 解析标签位置（如果有）
            if 'label_positions' in project_data:
                label_count = len(project_data['label_positions'])
                print(f"📍 加载 {label_count} 个手动标签位置")
            
            # 更新项目状态
            self.set_project_path(str(file_path_obj))
            
            print(f"✅ 项目加载成功: {file_path_obj}")
            return True, f"成功加载项目: {file_path_obj.name}", project_data
            
        except (ProjectFileError, ProjectValidationError) as e:
            error_msg = str(e)
            print(f"❌ 项目加载失败: {error_msg}")
            return False, error_msg, None
        except json.JSONDecodeError as e:
            error_msg = f"JSON文件格式错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
        except IOError as e:
            error_msg = f"文件读取失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"加载项目时发生未知错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
    
    # ==================== CSV设备列表操作 ====================
    
    def export_devices_to_csv(self, 
                              file_path: str,
                              devices: List[Device]) -> Tuple[bool, str]:
        """
        导出设备列表到CSV文件
        
        Args:
            file_path: CSV文件路径
            devices: 设备列表
            
        Returns:
            (成功标志, 消息)
        """
        try:
            if not devices:
                return False, "没有可导出的设备"
            
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入CSV文件
            with open(file_path_obj, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(['设备名称', 'X坐标', 'Y坐标'])
                # 写入设备数据
                for device in devices:
                    writer.writerow([device.name, f"{device.x:.3f}", f"{device.y:.3f}"])
            
            print(f"✅ 设备列表导出成功: {file_path_obj}")
            return True, f"已导出 {len(devices)} 个设备到: {file_path_obj.name}"
            
        except IOError as e:
            error_msg = f"文件写入失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"导出设备时发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def import_devices_from_csv(self, file_path: str) -> Tuple[bool, str, List[Device]]:
        """
        从CSV文件导入设备列表
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            (成功标志, 消息, 设备列表)
        """
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                raise ProjectFileError(f"CSV文件不存在: {file_path_obj}")
            
            devices = []
            
            # 读取CSV文件
            with open(file_path_obj, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # 跳过表头
                
                if not header:
                    raise ProjectValidationError("CSV文件为空")
                
                line_number = 1
                for row in reader:
                    line_number += 1
                    
                    # 跳过空行
                    if not row or all(not cell.strip() for cell in row):
                        continue
                    
                    # 验证列数
                    if len(row) < 3:
                        print(f"⚠️ 第{line_number}行数据不完整，已跳过: {row}")
                        continue
                    
                    try:
                        name = row[0].strip()
                        x = float(row[1])
                        y = float(row[2])
                        
                        # 验证设备名称
                        if not name:
                            print(f"⚠️ 第{line_number}行设备名称为空，已跳过")
                            continue
                        
                        # 创建设备对象
                        device = Device(name, x, y)
                        devices.append(device)
                        
                    except ValueError as e:
                        print(f"⚠️ 第{line_number}行坐标格式错误，已跳过: {row} ({e})")
                        continue
                    except Exception as e:
                        print(f"⚠️ 第{line_number}行处理失败，已跳过: {e}")
                        continue
            
            if not devices:
                return False, "CSV文件中没有有效的设备数据", []
            
            print(f"✅ 成功从CSV导入 {len(devices)} 个设备")
            return True, f"成功导入 {len(devices)} 个设备", devices
            
        except (ProjectFileError, ProjectValidationError) as e:
            error_msg = str(e)
            print(f"❌ 导入设备失败: {error_msg}")
            return False, error_msg, []
        except IOError as e:
            error_msg = f"文件读取失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, []
        except Exception as e:
            error_msg = f"导入设备时发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, []
    
    # ==================== 私有辅助方法 ====================
    
    def _build_project_data(self,
                           devices: List[Device],
                           coordinate_settings: Dict[str, float],
                           user_coord_settings: Optional[Dict[str, Any]] = None,
                           project_info: Optional[Dict[str, str]] = None,
                           label_positions: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        构建项目数据结构
        
        V2.1: 添加标签位置持久化支持
        
        Args:
            devices: 设备列表
            coordinate_settings: 坐标设置
            user_coord_settings: 用户坐标系设置
            project_info: 项目信息
            label_positions: 标签位置字典（仅保存手动位置）
            
        Returns:
            项目数据字典
        """
        now = datetime.now().isoformat()
        
        # 构建项目信息
        if project_info is None:
            project_info = {}
        
        info = {
            'name': project_info.get('name', self.current_project_name),
            'version': self.PROJECT_VERSION,
            'created_time': project_info.get('created_time', now),
            'modified_time': now,
            'description': project_info.get('description', ''),
            'author': project_info.get('author', '')
        }
        
        # 构建设备列表
        devices_data = [
            {
                'id': device.id,
                'name': device.name,
                'x': device.x,
                'y': device.y,
                'color': device.color,  # ✨ 保存设备颜色
                'created_time': device.created_time.isoformat() if hasattr(device.created_time, 'isoformat') else str(device.created_time)
            }
            for device in devices
        ]
        
        # 构建用户坐标系设置
        if user_coord_settings is None:
            user_coord_settings = {
                'enabled': False,
                'user_x': None,
                'user_y': None
            }
        
        # 组装完整数据
        project_data = {
            'project_info': info,
            'coordinate_settings': coordinate_settings,
            'user_coordinate_system': user_coord_settings,
            'devices': devices_data
        }
        
        # V2.1: 添加标签位置（仅保存手动设置的位置）
        if label_positions:
            # 过滤出手动位置
            manual_positions = {
                k: v for k, v in label_positions.items()
                if isinstance(v, dict) and v.get('is_manual', False)
            }
            if manual_positions:
                project_data['label_positions'] = manual_positions
                print(f"💾 保存 {len(manual_positions)} 个手动标签位置")
        
        return project_data
    
    def _validate_project_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证项目数据的完整性和正确性
        
        Args:
            data: 项目数据字典
            
        Returns:
            (验证结果, 错误消息)
        """
        try:
            # 检查必需的顶层键
            required_keys = ['project_info', 'coordinate_settings', 'devices']
            for key in required_keys:
                if key not in data:
                    return False, f"缺少必需字段: {key}"
            
            # 验证项目信息
            project_info = data['project_info']
            if not isinstance(project_info, dict):
                return False, "project_info必须是字典类型"
            
            if 'version' not in project_info:
                return False, "缺少版本信息"
            
            # 验证坐标设置
            coord_settings = data['coordinate_settings']
            if not isinstance(coord_settings, dict):
                return False, "coordinate_settings必须是字典类型"
            
            if 'x_range' not in coord_settings or 'y_range' not in coord_settings:
                return False, "坐标设置不完整"
            
            # 验证设备列表
            devices = data['devices']
            if not isinstance(devices, list):
                return False, "devices必须是列表类型"
            
            # 验证每个设备的数据
            for i, device in enumerate(devices):
                if not isinstance(device, dict):
                    return False, f"第{i+1}个设备数据格式错误"
                
                required_device_keys = ['name', 'x', 'y']
                for key in required_device_keys:
                    if key not in device:
                        return False, f"第{i+1}个设备缺少字段: {key}"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"
    
    def _parse_devices(self, devices_data: List[Dict[str, Any]]) -> List[Device]:
        """
        解析设备数据，创建Device对象列表
        
        Args:
            devices_data: 设备数据列表
            
        Returns:
            Device对象列表
        """
        devices = []
        for device_data in devices_data:
            try:
                device = Device(
                    name=device_data['name'],
                    x=device_data['x'],
                    y=device_data['y'],
                    device_id=device_data.get('id'),
                    color=device_data.get('color')  # ✨ 加载设备颜色
                )
                # 恢复创建时间
                if 'created_time' in device_data:
                    try:
                        device.created_time = datetime.fromisoformat(device_data['created_time'])
                    except:
                        pass
                
                devices.append(device)
            except Exception as e:
                print(f"⚠️ 解析设备数据失败，已跳过: {device_data} ({e})")
                continue
        
        return devices
    
    # ==================== 工具方法 ====================
    
    @staticmethod
    def get_default_project_dir() -> Path:
        """
        获取默认项目目录
        
        Returns:
            默认项目目录路径
        """
        home = Path.home()
        project_dir = home / "Documents" / "ApplCoordProjects"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    @staticmethod
    def get_project_info_from_file(file_path: str) -> Optional[Dict[str, str]]:
        """
        从项目文件中读取基本信息（不加载完整数据）
        
        Args:
            file_path: 项目文件路径
            
        Returns:
            项目信息字典，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('project_info', {})
        except:
            return None

