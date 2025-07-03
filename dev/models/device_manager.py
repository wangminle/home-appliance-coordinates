# -*- coding: utf-8 -*-
"""
设备数据管理器

统一管理所有设备数据，提供事务式操作和数据同步机制
"""

from typing import List, Optional, Callable, Dict, Any
from models.device_model import Device
from utils.validation import Validator


class DeviceManagerError(Exception):
    """设备管理器异常基类"""
    pass

class DeviceValidationError(DeviceManagerError):
    """设备验证错误"""
    pass

class DeviceOperationError(DeviceManagerError):
    """设备操作错误"""
    pass


class DeviceManager:
    """
    设备数据管理器
    
    负责统一管理所有设备数据，确保数据一致性和操作原子性
    支持事务式操作和自动回滚机制
    """
    
    MAX_DEVICES = 10  # 设备数量上限
    
    def __init__(self):
        """
        初始化设备管理器
        """
        self._devices: List[Device] = []
        self._observers: List[Callable[[List[Device]], None]] = []
        self._transaction_backup: Optional[List[Device]] = None
        self._load_initial_devices()
    
    def _load_initial_devices(self):
        """
        加载初始设备数据
        """
        try:
            initial_devices = [
                Device("7寸屏", -2.625, 0),
                Device("4寸屏", -1.000, 3.544)
            ]
            self._devices = initial_devices
            print(f"✅ 设备管理器初始化完成，加载了 {len(self._devices)} 个初始设备")
        except Exception as e:
            print(f"❌ 加载初始设备失败: {e}")
            self._devices = []
    
    def _create_backup(self):
        """
        创建当前设备状态的备份
        """
        self._transaction_backup = [device for device in self._devices]
    
    def _restore_backup(self):
        """
        从备份恢复设备状态
        """
        if self._transaction_backup is not None:
            self._devices = self._transaction_backup
            self._transaction_backup = None
            print("🔄 设备状态已回滚")
    
    def _clear_backup(self):
        """
        清除事务备份
        """
        self._transaction_backup = None
    
    def add_observer(self, observer: Callable[[List[Device]], None]):
        """
        添加数据变更观察者
        
        Args:
            observer: 观察者回调函数，当设备列表变更时被调用
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[List[Device]], None]):
        """
        移除数据变更观察者
        
        Args:
            observer: 要移除的观察者回调函数
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self):
        """
        通知所有观察者数据已变更
        """
        devices_copy = self.get_devices()
        for observer in self._observers:
            try:
                observer(devices_copy)
            except Exception as e:
                print(f"⚠️ 通知观察者失败: {e}")
    
    def get_devices(self) -> List[Device]:
        """
        获取所有设备的副本
        
        Returns:
            设备列表的副本
        """
        return [device for device in self._devices]
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """
        根据ID获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备对象，如果未找到返回None
        """
        for device in self._devices:
            if device.id == device_id:
                return device
        return None
    
    def get_device_by_name(self, name: str) -> Optional[Device]:
        """
        根据名称获取设备
        
        Args:
            name: 设备名称
            
        Returns:
            设备对象，如果未找到返回None
        """
        for device in self._devices:
            if device.name == name:
                return device
        return None
    
    def add_device(self, device: Device) -> tuple[bool, str]:
        """
        添加设备（事务式操作，支持自动回滚）
        
        Args:
            device: 要添加的设备
            
        Returns:
            (成功标志, 消息)
        """
        # 创建事务备份
        self._create_backup()
        
        try:
            # 1. 数量限制检查
            if len(self._devices) >= self.MAX_DEVICES:
                raise DeviceValidationError(f"无法添加更多设备，数量上限为 {self.MAX_DEVICES} 个")
            
            # 2. 设备数据验证
            if not device or not isinstance(device, Device):
                raise DeviceValidationError("设备对象无效")
            
            # 3. 名称唯一性检查
            existing_names = [d.name for d in self._devices]
            is_unique, error_msg = Validator.validate_device_name_uniqueness(
                device.name, existing_names
            )
            if not is_unique:
                raise DeviceValidationError(error_msg)
            
            # 4. ID唯一性检查
            if self.get_device_by_id(device.id):
                raise DeviceValidationError(f"设备ID '{device.id}' 已存在")
            
            # 5. 执行添加操作
            self._devices.append(device)
            
            # 6. 通知观察者
            self._notify_observers()
            
            # 7. 清除备份
            self._clear_backup()
            
            print(f"✅ 设备添加成功: {device.name} ({device.x}, {device.y})")
            return True, "设备添加成功"
            
        except (DeviceValidationError, DeviceOperationError) as e:
            # 回滚操作
            self._restore_backup()
            error_msg = str(e)
            print(f"❌ 设备添加失败: {error_msg}")
            return False, error_msg
        except Exception as e:
            # 回滚操作
            self._restore_backup()
            error_msg = f"设备添加失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def update_device(self, device_id: str, new_device: Device) -> tuple[bool, str]:
        """
        更新设备（事务式操作，支持自动回滚）
        
        Args:
            device_id: 要更新的设备ID
            new_device: 新的设备数据
            
        Returns:
            (成功标志, 消息)
        """
        # 创建事务备份
        self._create_backup()
        
        try:
            # 1. 查找原设备
            old_device_index = -1
            old_device = None
            for i, device in enumerate(self._devices):
                if device.id == device_id:
                    old_device_index = i
                    old_device = device
                    break
            
            if old_device is None:
                raise DeviceOperationError("未找到要更新的设备")
            
            # 2. 验证新设备数据
            if not new_device or not isinstance(new_device, Device):
                raise DeviceValidationError("新设备对象无效")
            
            # 3. 名称唯一性检查（排除当前设备）
            existing_names = [d.name for i, d in enumerate(self._devices) if i != old_device_index]
            is_unique, error_msg = Validator.validate_device_name_uniqueness(
                new_device.name, existing_names
            )
            if not is_unique:
                raise DeviceValidationError(error_msg)
            
            # 4. 保持原设备的ID和创建时间
            new_device.id = old_device.id
            new_device.created_time = old_device.created_time
            
            # 5. 执行更新操作
            self._devices[old_device_index] = new_device
            
            # 6. 通知观察者
            self._notify_observers()
            
            # 7. 清除备份
            self._clear_backup()
            
            print(f"✅ 设备更新成功: {old_device.name} -> {new_device.name}")
            return True, "设备更新成功"
            
        except (DeviceValidationError, DeviceOperationError) as e:
            # 回滚操作
            self._restore_backup()
            error_msg = str(e)
            print(f"❌ 设备更新失败: {error_msg}")
            return False, error_msg
        except Exception as e:
            # 回滚操作
            self._restore_backup()
            error_msg = f"设备更新失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def delete_device(self, device_id: str) -> tuple[bool, str]:
        """
        删除设备（事务式操作，支持自动回滚）
        
        Args:
            device_id: 要删除的设备ID
            
        Returns:
            (成功标志, 消息)
        """
        # 创建事务备份
        self._create_backup()
        
        try:
            # 1. 查找要删除的设备
            device_to_delete = None
            for device in self._devices:
                if device.id == device_id:
                    device_to_delete = device
                    break
            
            if device_to_delete is None:
                raise DeviceOperationError("未找到要删除的设备")
            
            # 2. 执行删除操作
            self._devices.remove(device_to_delete)
            
            # 3. 通知观察者
            self._notify_observers()
            
            # 4. 清除备份
            self._clear_backup()
            
            print(f"✅ 设备删除成功: {device_to_delete.name}")
            return True, "设备删除成功"
            
        except (DeviceValidationError, DeviceOperationError) as e:
            # 回滚操作
            self._restore_backup()
            error_msg = str(e)
            print(f"❌ 设备删除失败: {error_msg}")
            return False, error_msg
        except Exception as e:
            # 回滚操作
            self._restore_backup()
            error_msg = f"设备删除失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def clear_all_devices(self) -> tuple[bool, str]:
        """
        清除所有设备（事务式操作，支持自动回滚）
        
        Returns:
            (成功标志, 消息)
        """
        # 创建事务备份
        self._create_backup()
        
        try:
            # 执行清除操作
            self._devices.clear()
            
            # 通知观察者
            self._notify_observers()
            
            # 清除备份
            self._clear_backup()
            
            print("✅ 所有设备已清除")
            return True, "所有设备已清除"
            
        except Exception as e:
            # 回滚操作
            self._restore_backup()
            error_msg = f"清除设备失败: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def get_device_count(self) -> int:
        """
        获取设备数量
        
        Returns:
            设备数量
        """
        return len(self._devices)
    
    def is_device_name_available(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        检查设备名称是否可用
        
        Args:
            name: 要检查的名称
            exclude_id: 排除的设备ID（用于更新时检查）
            
        Returns:
            名称是否可用
        """
        for device in self._devices:
            if device.name == name and device.id != exclude_id:
                return False
        return True
    
    def validate_device_operation(self, operation: str, device: Device, device_id: Optional[str] = None) -> tuple[bool, str]:
        """
        验证设备操作的合法性（不执行实际操作）
        
        Args:
            operation: 操作类型 ('add', 'update', 'delete')
            device: 设备对象
            device_id: 设备ID（用于update和delete操作）
            
        Returns:
            (验证结果, 消息)
        """
        try:
            if operation == 'add':
                # 验证添加操作
                if len(self._devices) >= self.MAX_DEVICES:
                    return False, f"无法添加更多设备，数量上限为 {self.MAX_DEVICES} 个"
                
                if not device or not isinstance(device, Device):
                    return False, "设备对象无效"
                
                existing_names = [d.name for d in self._devices]
                is_unique, error_msg = Validator.validate_device_name_uniqueness(
                    device.name, existing_names
                )
                if not is_unique:
                    return False, error_msg
                
                if self.get_device_by_id(device.id):
                    return False, f"设备ID '{device.id}' 已存在"
                
            elif operation == 'update':
                # 验证更新操作
                if not device_id:
                    return False, "缺少设备ID"
                
                old_device = self.get_device_by_id(device_id)
                if not old_device:
                    return False, "未找到要更新的设备"
                
                if not device or not isinstance(device, Device):
                    return False, "新设备对象无效"
                
                # 排除当前设备的名称唯一性检查
                existing_names = [d.name for d in self._devices if d.id != device_id]
                is_unique, error_msg = Validator.validate_device_name_uniqueness(
                    device.name, existing_names
                )
                if not is_unique:
                    return False, error_msg
                
            elif operation == 'delete':
                # 验证删除操作
                if not device_id:
                    return False, "缺少设备ID"
                
                if not self.get_device_by_id(device_id):
                    return False, "未找到要删除的设备"
                
            else:
                return False, f"不支持的操作类型: {operation}"
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取设备管理器摘要信息
        
        Returns:
            包含统计信息的字典
        """
        return {
            'total_devices': len(self._devices),
            'max_devices': self.MAX_DEVICES,
            'device_names': [device.name for device in self._devices],
            'observers_count': len(self._observers),
            'has_backup': self._transaction_backup is not None
        } 