# -*- coding: utf-8 -*-
"""
应用配置管理器

负责管理应用程序配置，包括：
- 最近打开文件列表
- 自动保存设置
- 用户偏好设置
"""

import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime


class ConfigManager:
    """
    应用配置管理器
    
    管理应用程序的持久化配置数据
    """
    
    # 最近文件数量限制
    MAX_RECENT_FILES = 10
    
    # 自动保存间隔（秒）
    DEFAULT_AUTOSAVE_INTERVAL = 300  # 5分钟
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.config_data = self._load_config()
        print(f"[OK] ConfigManager初始化完成，配置目录: {self.config_dir}")
    
    # ==================== 配置文件操作 ====================
    
    def _get_config_dir(self) -> Path:
        """
        获取配置文件目录
        
        Returns:
            配置目录路径
        """
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows: %APPDATA%\ApplCoord
            config_dir = Path.home() / "AppData" / "Roaming" / "ApplCoord"
        elif system == "Darwin":
            # macOS: ~/.applcoord
            config_dir = Path.home() / ".applcoord"
        else:
            # Linux: ~/.config/applcoord
            config_dir = Path.home() / ".config" / "applcoord"
        
        # 确保目录存在
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建自动保存目录
        autosave_dir = config_dir / "autosave"
        autosave_dir.mkdir(exist_ok=True)
        
        return config_dir
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置数据字典
        """
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"[OK] 配置文件加载成功")
            return config
        except Exception as e:
            print(f"[WARN] 配置文件加载失败，使用默认配置: {e}")
            return self._get_default_config()
    
    def _save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] 配置文件保存失败: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'recent_files': [],
            'autosave': {
                'enabled': True,
                'interval': self.DEFAULT_AUTOSAVE_INTERVAL
            },
            'window': {
                'remember_position': False,
                'last_x': 0,
                'last_y': 0
            },
            'preferences': {
                'show_grid': True,
                'auto_backup': True
            }
        }
    
    # ==================== 最近文件管理 ====================
    
    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表
        
        Returns:
            文件路径列表
        """
        recent_files = self.config_data.get('recent_files', [])
        # 过滤掉不存在的文件
        valid_files = [f for f in recent_files if Path(f).exists()]
        
        # 如果有文件被过滤掉，更新配置
        if len(valid_files) != len(recent_files):
            self.config_data['recent_files'] = valid_files
            self._save_config()
        
        return valid_files
    
    def add_recent_file(self, file_path: str) -> bool:
        """
        添加文件到最近打开列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否添加成功
        """
        try:
            # 获取绝对路径
            abs_path = str(Path(file_path).absolute())
            
            # 获取当前列表
            recent_files = self.config_data.get('recent_files', [])
            
            # 如果文件已存在，先移除
            if abs_path in recent_files:
                recent_files.remove(abs_path)
            
            # 添加到列表开头
            recent_files.insert(0, abs_path)
            
            # 限制列表长度
            recent_files = recent_files[:self.MAX_RECENT_FILES]
            
            # 更新配置
            self.config_data['recent_files'] = recent_files
            
            # 保存配置
            return self._save_config()
            
        except Exception as e:
            print(f"[ERROR] 添加最近文件失败: {e}")
            return False
    
    def remove_recent_file(self, file_path: str) -> bool:
        """
        从最近打开列表中移除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否移除成功
        """
        try:
            abs_path = str(Path(file_path).absolute())
            recent_files = self.config_data.get('recent_files', [])
            
            if abs_path in recent_files:
                recent_files.remove(abs_path)
                self.config_data['recent_files'] = recent_files
                return self._save_config()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 移除最近文件失败: {e}")
            return False
    
    def clear_recent_files(self) -> bool:
        """
        清空最近打开文件列表
        
        Returns:
            是否清空成功
        """
        try:
            self.config_data['recent_files'] = []
            return self._save_config()
        except Exception as e:
            print(f"[ERROR] 清空最近文件失败: {e}")
            return False
    
    # ==================== 自动保存设置 ====================
    
    def is_autosave_enabled(self) -> bool:
        """
        检查自动保存是否启用
        
        Returns:
            是否启用自动保存
        """
        return self.config_data.get('autosave', {}).get('enabled', True)
    
    def set_autosave_enabled(self, enabled: bool) -> bool:
        """
        设置自动保存启用状态
        
        Args:
            enabled: 是否启用
            
        Returns:
            是否设置成功
        """
        if 'autosave' not in self.config_data:
            self.config_data['autosave'] = {}
        
        self.config_data['autosave']['enabled'] = enabled
        return self._save_config()
    
    def get_autosave_interval(self) -> int:
        """
        获取自动保存间隔（秒）
        
        Returns:
            自动保存间隔
        """
        return self.config_data.get('autosave', {}).get('interval', self.DEFAULT_AUTOSAVE_INTERVAL)
    
    def set_autosave_interval(self, interval: int) -> bool:
        """
        设置自动保存间隔
        
        Args:
            interval: 间隔时间（秒）
            
        Returns:
            是否设置成功
        """
        if interval < 60:  # 最小1分钟
            interval = 60
        
        if 'autosave' not in self.config_data:
            self.config_data['autosave'] = {}
        
        self.config_data['autosave']['interval'] = interval
        return self._save_config()
    
    def get_autosave_dir(self) -> Path:
        """
        获取自动保存目录
        
        Returns:
            自动保存目录路径
        """
        return self.config_dir / "autosave"
    
    def get_autosave_file_path(self) -> Path:
        """
        获取自动保存文件路径
        
        Returns:
            自动保存文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.get_autosave_dir() / f"draft_{timestamp}.apc"
    
    def get_latest_autosave_file(self) -> Optional[Path]:
        """
        获取最新的自动保存文件
        
        Returns:
            最新自动保存文件路径，没有返回None
        """
        autosave_dir = self.get_autosave_dir()
        
        if not autosave_dir.exists():
            return None
        
        # 查找所有草稿文件
        draft_files = list(autosave_dir.glob("draft_*.apc"))
        
        if not draft_files:
            return None
        
        # 按修改时间排序，返回最新的
        draft_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return draft_files[0]
    
    def clean_old_autosave_files(self, keep_count: int = 5) -> int:
        """
        清理旧的自动保存文件
        
        Args:
            keep_count: 保留文件数量
            
        Returns:
            删除的文件数量
        """
        autosave_dir = self.get_autosave_dir()
        
        if not autosave_dir.exists():
            return 0
        
        # 查找所有草稿文件
        draft_files = list(autosave_dir.glob("draft_*.apc"))
        
        if len(draft_files) <= keep_count:
            return 0
        
        # 按修改时间排序
        draft_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # 删除多余的文件
        deleted_count = 0
        for file_to_delete in draft_files[keep_count:]:
            try:
                file_to_delete.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"[WARN] 删除旧草稿文件失败: {file_to_delete} ({e})")
        
        if deleted_count > 0:
            print(f"[OK] 清理了 {deleted_count} 个旧的自动保存文件")
        
        return deleted_count
    
    # ==================== 其他设置 ====================
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取偏好设置
        
        Args:
            key: 设置键名
            default: 默认值
            
        Returns:
            设置值
        """
        return self.config_data.get('preferences', {}).get(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """
        设置偏好
        
        Args:
            key: 设置键名
            value: 设置值
            
        Returns:
            是否设置成功
        """
        if 'preferences' not in self.config_data:
            self.config_data['preferences'] = {}
        
        self.config_data['preferences'][key] = value
        return self._save_config()

