# -*- coding: utf-8 -*-
"""
场景控制器

V2.0 重构：从View层剥离业务逻辑，作为Model和View之间的协调者。

核心职责：
1. 处理用户交互（点击、双击、右键等）
2. 协调 SceneModel 和 SceneRenderer 的数据同步
3. 执行业务逻辑（测量计算、扇形生成等）
4. 监听 Model 变化，触发渲染更新
"""

import math
from typing import Optional, Callable, Tuple, List, Any, TYPE_CHECKING

from models.scene_model import SceneModel, ChangeType, SectorData, MeasurementData
from models.device_model import Device

# 为了避免循环导入，使用 TYPE_CHECKING
if TYPE_CHECKING:
    from views.scene_renderer import SceneRenderer


class SceneController:
    """
    场景控制器
    
    处理用户交互，协调Model和View，执行业务逻辑。
    遵循MVC架构，Controller不直接操作UI元素，只通过Model和Renderer工作。
    """
    
    def __init__(self, model: SceneModel, renderer: Optional['SceneRenderer'] = None):
        """
        初始化场景控制器
        
        Args:
            model: 场景数据模型
            renderer: 场景渲染器（可选，可以稍后通过 set_renderer 设置）
        """
        self.model = model
        self.renderer = renderer
        
        # 双击检测参数
        self._last_click_time = -1.0  # 初始值为负数，避免第一次点击被误判为双击
        self._double_click_threshold = 0.3  # 双击时间阈值（秒）
        
        # 外部回调（用于通知InputPanel等）
        self._on_device_change_callback: Optional[Callable[[List[Device]], None]] = None
        self._on_measurement_change_callback: Optional[Callable[[Optional[MeasurementData]], None]] = None
        
        # 监听Model变化
        self.model.add_observer(self._on_model_changed)
        
        print("✅ SceneController 初始化完成")
    
    def set_renderer(self, renderer: 'SceneRenderer'):
        """
        设置渲染器
        
        Args:
            renderer: 场景渲染器实例
        """
        self.renderer = renderer
        
        # V2.1: 设置拖拽回调
        self.renderer.set_drag_end_callback(self._on_label_drag_end)
        self.renderer.set_drag_start_callback(self._on_label_drag_start)
        
        # 绑定拖拽事件
        self.renderer.bind_drag_events()
        
        print("✅ 渲染器已设置（含拖拽回调）")
    
    # ==================== 外部回调设置 ====================
    
    def set_device_change_callback(self, callback: Callable[[List[Device]], None]):
        """设置设备变更回调（通知InputPanel等）"""
        self._on_device_change_callback = callback
    
    def set_measurement_change_callback(self, callback: Callable[[Optional[MeasurementData]], None]):
        """设置测量点变更回调"""
        self._on_measurement_change_callback = callback
    
    # ==================== 画布交互处理 ====================
    
    def on_canvas_click(self, x: float, y: float, button: int, current_time: float):
        """
        处理画布点击事件
        
        Args:
            x: 点击位置X坐标
            y: 点击位置Y坐标
            button: 鼠标按钮（1=左键, 3=右键）
            current_time: 当前时间戳（用于双击检测）
        """
        if button == 1:  # 左键
            # 检测是否为双击
            if current_time - self._last_click_time < self._double_click_threshold:
                self._handle_double_click(x, y)
            else:
                self._handle_left_click(x, y)
            self._last_click_time = current_time
            
        elif button == 3:  # 右键
            self._handle_right_click()
    
    def _handle_left_click(self, x: float, y: float):
        """
        处理左键单击：创建测量点
        
        Args:
            x: 点击位置X坐标
            y: 点击位置Y坐标
        """
        # 设置测量点（Model会自动计算距离和角度）
        self.model.set_measurement(x, y)
        print(f"📍 左键单击: 创建测量点 ({x:.3f}, {y:.3f})")
    
    def _handle_double_click(self, x: float, y: float):
        """
        处理左键双击：创建90度扇形（以连线为平分线向两侧各45度）
        
        Args:
            x: 双击位置X坐标
            y: 双击位置Y坐标
        """
        # 根据坐标系模式选择扇形中心点
        if self.model.is_user_frame_active():
            user_pos = self.model.get_user_position()
            center_x, center_y = user_pos
        else:
            center_x, center_y = 0.0, 0.0
        
        # 计算半径（点击点到中心点的距离）
        radius = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        if radius < 0.01:  # 避免在中心点绘制
            print("⚠️ 双击位置太接近中心点，跳过扇形创建")
            return
        
        # 计算中心角度（点击点相对于中心点的角度）
        center_angle_rad = math.atan2(y - center_y, x - center_x)
        center_angle_deg = math.degrees(center_angle_rad)
        
        # 90度扇形：以连线为平分线，向两侧各45度
        start_angle_deg = center_angle_deg - 45
        end_angle_deg = center_angle_deg + 45
        
        # 添加扇形到Model
        self.model.add_sector(center_x, center_y, radius, start_angle_deg, end_angle_deg)
        print(f"🔺 双击: 创建扇形 中心({center_x:.3f}, {center_y:.3f}), 半径{radius:.3f}")
    
    def _handle_right_click(self):
        """
        处理右键单击：清除所有测量点和扇形
        """
        self.model.clear_measurement()
        self.model.clear_sectors()
        
        # 重置所有设备标签到默认位置
        self.model.reset_all_labels_to_auto()
        
        print("🧹 右键: 清除测量点和扇形")
    
    # ==================== 坐标范围管理 ====================
    
    def set_coordinate_range(self, x_range: float, y_range: float) -> Tuple[bool, str]:
        """
        设置坐标显示范围
        
        Args:
            x_range: X轴范围（±x_range）
            y_range: Y轴范围（±y_range）
            
        Returns:
            (成功标志, 消息)
        """
        if self.model.set_coordinate_range(x_range, y_range):
            return True, f"坐标范围已设置为 ±{x_range} x ±{y_range}"
        return False, "设置坐标范围失败"
    
    # ==================== 用户坐标系管理 ====================
    
    def set_user_position(self, x: float, y: float) -> Tuple[bool, str]:
        """
        设置用户位置
        
        Args:
            x: 用户X坐标
            y: 用户Y坐标
            
        Returns:
            (成功标志, 消息)
        """
        if self.model.set_user_position(x, y):
            return True, f"用户位置已设置: ({x:.3f}, {y:.3f})"
        return False, "设置用户位置失败"
    
    def clear_user_position(self):
        """清除用户位置"""
        self.model.clear_user_position()
    
    def toggle_user_coordinate_mode(self, enabled: bool):
        """
        切换用户坐标系模式
        
        Args:
            enabled: True启用，False禁用
        """
        if not enabled:
            self.model.clear_user_position()
        print(f"✨ 用户坐标系模式: {'启用' if enabled else '禁用'}")
    
    # ==================== 设备管理 ====================
    
    def add_device(self, name: str, x: float, y: float) -> Tuple[bool, str]:
        """
        添加设备
        
        Args:
            name: 设备名称
            x: X坐标
            y: Y坐标
            
        Returns:
            (成功标志, 消息)
        """
        try:
            device = Device(name, x, y)
            return self.model.add_device(device)
        except ValueError as e:
            return False, str(e)
    
    def update_device(self, device_id: str, name: str, x: float, y: float) -> Tuple[bool, str]:
        """
        更新设备信息
        
        Args:
            device_id: 设备ID
            name: 新的设备名称
            x: 新的X坐标
            y: 新的Y坐标
            
        Returns:
            (成功标志, 消息)
        """
        try:
            new_device = Device(name, x, y)
            return self.model.update_device(device_id, new_device)
        except ValueError as e:
            return False, str(e)
    
    def delete_device(self, device_id: str) -> Tuple[bool, str]:
        """
        删除设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            (成功标志, 消息)
        """
        return self.model.remove_device(device_id)
    
    def get_all_devices(self) -> List[Device]:
        """获取所有设备列表"""
        return self.model.get_devices()
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """根据ID获取设备"""
        return self.model.get_device_by_id(device_id)
    
    # ==================== 标签位置管理 ====================
    
    def on_label_drag(self, element_id: str, new_x: float, new_y: float):
        """
        处理标签拖拽（实时更新）
        
        Args:
            element_id: 元素ID
            new_x: 新的X坐标
            new_y: 新的Y坐标
        """
        self.model.set_label_position(element_id, new_x, new_y, is_manual=True)
        print(f"🔄 标签拖拽: {element_id} -> ({new_x:.3f}, {new_y:.3f})")
    
    def _on_label_drag_start(self, element_id: str):
        """
        处理标签拖拽开始（由渲染器回调）
        
        Args:
            element_id: 被拖拽的标签ID
        """
        print(f"🎯 控制器：开始拖拽标签 {element_id}")
    
    def _on_label_drag_end(self, element_id: str, final_x: float, final_y: float):
        """
        处理标签拖拽结束（由渲染器回调）
        
        将手动位置保存到模型，触发重新渲染。
        
        Args:
            element_id: 被拖拽的标签ID
            final_x: 最终X坐标
            final_y: 最终Y坐标
        """
        # 保存为手动位置
        self.model.set_label_position(element_id, final_x, final_y, is_manual=True)
        
        # 触发重新渲染以更新引导线等
        if self.renderer:
            self.renderer.render(self.model)
        
        print(f"✅ 控制器：标签 {element_id} 已设置为手动位置 ({final_x:.3f}, {final_y:.3f})")
    
    def reset_label_position(self, element_id: str):
        """
        重置指定标签为自动计算位置
        
        Args:
            element_id: 元素ID
        """
        self.model.reset_label_to_auto(element_id)
    
    # ==================== 导出功能 ====================
    
    def export_png(self, file_path: str, dpi: int = 300) -> Tuple[bool, str]:
        """
        导出PNG图片
        
        Args:
            file_path: 保存路径
            dpi: 分辨率
            
        Returns:
            (成功标志, 消息)
        """
        if self.renderer:
            try:
                success = self.renderer.export_to_png(file_path, dpi)
                if success:
                    return True, f"图片已导出到: {file_path}"
                return False, "导出失败"
            except Exception as e:
                return False, f"导出错误: {str(e)}"
        return False, "渲染器未设置"
    
    # ==================== 重置功能 ====================
    
    def reset_all(self):
        """重置所有数据"""
        self.model.reset()
        print("✅ 场景已重置")
    
    # ==================== Model变化监听 ====================
    
    def _on_model_changed(self, change_type: ChangeType, data: Any):
        """
        Model变化回调
        
        当 SceneModel 数据变化时被调用，负责：
        1. 触发渲染更新
        2. 通知外部回调（如InputPanel）
        
        Args:
            change_type: 变更类型
            data: 变更数据
        """
        # 触发渲染更新
        if self.renderer:
            self.renderer.render(self.model)
        
        # 通知外部回调
        if change_type in [ChangeType.DEVICE_ADDED, ChangeType.DEVICE_UPDATED, 
                           ChangeType.DEVICE_REMOVED, ChangeType.DEVICES_CLEARED]:
            if self._on_device_change_callback:
                self._on_device_change_callback(self.model.get_devices())
        
        elif change_type in [ChangeType.MEASUREMENT_SET, ChangeType.MEASUREMENT_CLEARED]:
            if self._on_measurement_change_callback:
                self._on_measurement_change_callback(self.model.get_measurement())
    
    # ==================== 兼容性接口 ====================
    
    def get_measurement_point(self) -> Optional[MeasurementData]:
        """获取当前测量点（兼容性接口）"""
        return self.model.get_measurement()
    
    def get_current_range(self) -> Tuple[float, float]:
        """获取当前坐标范围"""
        return self.model.coord_range
    
    def is_user_coord_enabled(self) -> bool:
        """检查用户坐标系是否启用"""
        return self.model.is_user_frame_active()
    
    def get_user_position(self) -> Optional[Tuple[float, float]]:
        """获取用户位置"""
        return self.model.get_user_position()

