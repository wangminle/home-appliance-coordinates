# 家居设备坐标绘制工具 V2.0 重构开发计划

## 项目背景

### 当前状态评估
- **当前版本**: V1.x（Matplotlib迁移完成）
- **当前评分**: 50分（满分100分）
- **核心问题**:
  - 坐标系设计概念混乱（简单偏移 vs 真正的坐标变换）
  - 标注避让系统过度工程化（1129行复杂的力导向算法）
  - View层职责过重（1426行，包含业务逻辑）
  - 导出时没有专门的布局优化

### 重构目标
- **目标评分**: 90分以上
- **代码精简**: 从3000+行核心代码减少到约1200行
- **确定性**: 同样输入永远产生同样输出
- **可维护性**: 每个模块职责清晰单一
- **新功能**: 标签手动拖拽、导出布局优化

---

## 总体架构设计

### 目标架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Application Layer                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐                      ┌───────────────────────┐ │
│  │   Models        │                      │      Views            │ │
│  │                 │                      │                       │ │
│  │ SceneModel      │◄────────────────────►│  MainWindow           │ │
│  │ ├─ WorldFrame   │     Observer         │  ├─ CanvasView        │ │
│  │ ├─ UserFrame    │     Pattern          │  │   (事件转发)        │ │
│  │ ├─ Devices[]    │                      │  └─ InputPanel        │ │
│  │ ├─ Measurement  │                      │      (数据输入)        │ │
│  │ ├─ Sectors[]    │                      │                       │ │
│  │ └─ LabelPositions│                     │  SceneRenderer        │ │
│  │                 │                      │  (纯绑定函数)          │ │
│  │ CoordinateFrame │                      │                       │ │
│  │ (坐标变换器)     │                      └───────────────────────┘ │
│  └─────────────────┘                                                │
│          ▲                                          ▲               │
│          │                                          │               │
│          ▼                                          │               │
│  ┌─────────────────┐                               │               │
│  │  Controllers    │───────────────────────────────┘               │
│  │                 │                                                │
│  │ SceneController │                                                │
│  │ ├─ on_click()   │                                                │
│  │ ├─ on_drag()    │  ◄──── 新增：标签拖拽                          │
│  │ ├─ on_export()  │                                                │
│  │ └─ on_reset()   │                                                │
│  └─────────────────┘                                                │
│          │                                                          │
│          ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      Services Layer                             ││
│  │                                                                 ││
│  │  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐   ││
│  │  │ LabelPlacer   │  │ GeoCalculator│  │ ExportRenderer     │   ││
│  │  │               │  │              │  │                    │   ││
│  │  │ • 确定性8方向 │  │ • 距离计算   │  │ • 导出专用布局     │   ││
│  │  │ • 碰撞检测    │  │ • 角度计算   │  │ • 高DPI渲染        │   ││
│  │  │ • 手动覆盖    │  │ • 坐标变换   │  │ • 多格式输出       │   ││
│  │  └───────────────┘  └──────────────┘  └────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 模块职责定义

| 模块 | 职责 | 预估代码量 |
|------|------|-----------|
| `SceneModel` | 单一数据源，管理场景所有状态 | ~180行 |
| `CoordinateFrame` | 坐标系定义与变换 | ~100行 |
| `SceneController` | 用户交互处理，业务逻辑 | ~250行 |
| `SceneRenderer` | 根据Model绑定Matplotlib | ~350行 |
| `LabelPlacer` | 确定性标签布局服务 | ~180行 |
| `ExportRenderer` | 导出专用渲染服务 | ~120行 |
| **总计** | | **~1180行** |

---

## 三期开发计划

### 📅 第一期：核心架构重构（预计5天）

**目标**：建立正确的架构基础，解决坐标系和数据流问题

#### 第一期 - 任务分解

| 序号 | 任务 | 说明 | 预计耗时 |
|------|------|------|----------|
| 1.1 | 创建 `CoordinateFrame` 类 | 统一坐标系变换逻辑 | 0.5天 |
| 1.2 | 创建 `SceneModel` 类 | 单一数据源，整合所有场景数据 | 1天 |
| 1.3 | 重构 `SceneController` | 从View剥离业务逻辑 | 1天 |
| 1.4 | 创建 `SceneRenderer` | 纯绑定逻辑，只负责绑制 | 1.5天 |
| 1.5 | 集成测试与Bug修复 | 确保基础功能正常 | 1天 |

#### 第一期 - 详细设计

##### 1.1 CoordinateFrame 类

```python
# 文件: dev/src/models/coordinate_frame.py

class CoordinateFrame:
    """
    坐标参考系
    
    表示一个坐标系，包含原点位置和可选的旋转角度。
    支持世界坐标↔本地坐标的双向转换。
    """
    
    def __init__(self, name: str, origin_x: float = 0.0, origin_y: float = 0.0, 
                 rotation_deg: float = 0.0):
        self.name = name
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.rotation_deg = rotation_deg
    
    def world_to_local(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """世界坐标 → 本地坐标"""
        pass
    
    def local_to_world(self, local_x: float, local_y: float) -> Tuple[float, float]:
        """本地坐标 → 世界坐标"""
        pass
    
    def distance_from_origin(self, world_x: float, world_y: float) -> float:
        """计算点到本坐标系原点的距离"""
        pass
    
    def angle_from_origin(self, world_x: float, world_y: float) -> float:
        """计算点相对于本坐标系原点的角度"""
        pass
```

##### 1.2 SceneModel 类

```python
# 文件: dev/src/models/scene_model.py

class SceneModel:
    """
    场景数据模型 - 单一数据源
    
    整合所有场景状态数据，实现观察者模式通知视图更新。
    """
    
    def __init__(self):
        # 坐标系
        self.world_frame = CoordinateFrame("world", 0, 0)
        self.user_frame: Optional[CoordinateFrame] = None
        self.coord_range = (10.0, 10.0)  # (x_range, y_range)
        
        # 场景元素
        self.devices: List[Device] = []
        self.measurement: Optional[MeasurementData] = None
        self.sectors: List[SectorData] = []
        
        # 标签位置（支持手动覆盖）
        self.label_positions: Dict[str, LabelPosition] = {}
        
        # 观察者列表
        self._observers: List[Callable] = []
    
    # === 坐标系管理 ===
    def set_user_position(self, x: float, y: float):
        """设置用户位置（创建/更新用户坐标系）"""
        pass
    
    def clear_user_position(self):
        """清除用户坐标系"""
        pass
    
    def is_user_frame_active(self) -> bool:
        """用户坐标系是否激活"""
        pass
    
    # === 设备管理 ===
    def add_device(self, device: Device) -> bool:
        pass
    
    def update_device(self, device_id: str, new_data: Device) -> bool:
        pass
    
    def remove_device(self, device_id: str) -> bool:
        pass
    
    # === 测量管理 ===
    def set_measurement(self, x: float, y: float):
        """设置测量点"""
        pass
    
    def clear_measurement(self):
        pass
    
    # === 扇形管理 ===
    def add_sector(self, center_x: float, center_y: float, radius: float, 
                   start_angle: float, end_angle: float):
        pass
    
    def clear_sectors(self):
        pass
    
    # === 标签位置管理 ===
    def set_label_position(self, element_id: str, x: float, y: float, is_manual: bool = False):
        """设置标签位置（自动计算或手动拖拽）"""
        pass
    
    def get_label_position(self, element_id: str) -> Optional[LabelPosition]:
        pass
    
    def reset_label_to_auto(self, element_id: str):
        """重置标签为自动计算位置"""
        pass
    
    # === 观察者模式 ===
    def add_observer(self, callback: Callable):
        pass
    
    def _notify_observers(self, change_type: str):
        """通知所有观察者数据已变更"""
        pass
```

##### 1.3 SceneController 重构

```python
# 文件: dev/src/controllers/scene_controller.py

class SceneController:
    """
    场景控制器
    
    处理用户交互，协调Model和View，执行业务逻辑。
    """
    
    def __init__(self, model: SceneModel, renderer: SceneRenderer):
        self.model = model
        self.renderer = renderer
        self.label_placer = LabelPlacer()
        
        # 监听Model变化
        self.model.add_observer(self._on_model_changed)
    
    # === 画布交互处理 ===
    def on_canvas_click(self, x: float, y: float, button: int):
        """处理画布点击"""
        if button == 1:  # 左键
            self._handle_left_click(x, y)
        elif button == 3:  # 右键
            self._handle_right_click()
    
    def on_canvas_double_click(self, x: float, y: float):
        """处理画布双击 - 创建扇形"""
        pass
    
    def on_label_drag(self, element_id: str, new_x: float, new_y: float):
        """处理标签拖拽"""
        self.model.set_label_position(element_id, new_x, new_y, is_manual=True)
    
    # === 坐标范围 ===
    def set_coordinate_range(self, x_range: float, y_range: float):
        pass
    
    # === 用户坐标系 ===
    def set_user_position(self, x: float, y: float):
        self.model.set_user_position(x, y)
    
    def toggle_user_coordinate_mode(self, enabled: bool):
        pass
    
    # === 设备管理 ===
    def add_device(self, name: str, x: float, y: float) -> Tuple[bool, str]:
        pass
    
    def update_device(self, device_id: str, name: str, x: float, y: float) -> Tuple[bool, str]:
        pass
    
    def delete_device(self, device_id: str) -> Tuple[bool, str]:
        pass
    
    # === 导出 ===
    def export_png(self, file_path: str, dpi: int = 300) -> bool:
        pass
    
    # === 内部方法 ===
    def _on_model_changed(self, change_type: str):
        """Model变化时，重新计算标签位置并更新渲染"""
        # 只对自动位置的标签重新计算
        auto_labels = {k: v for k, v in self.model.label_positions.items() if not v.is_manual}
        new_positions = self.label_placer.calculate_positions(
            self.model.devices,
            self.model.sectors,
            self.model.coord_range
        )
        # 更新自动计算的位置
        for element_id, pos in new_positions.items():
            if element_id in auto_labels or element_id not in self.model.label_positions:
                self.model.set_label_position(element_id, pos[0], pos[1], is_manual=False)
        
        # 触发渲染更新
        self.renderer.render(self.model)
```

##### 1.4 SceneRenderer 类

```python
# 文件: dev/src/views/scene_renderer.py

class SceneRenderer:
    """
    场景渲染器
    
    纯绑定函数，根据SceneModel数据进行Matplotlib绑制。
    不包含任何业务逻辑和状态管理。
    """
    
    def __init__(self, figure: Figure, axes: Axes):
        self.figure = figure
        self.axes = axes
        self.artists: Dict[str, List[Artist]] = {}  # 按类别管理绑制对象
    
    def render(self, model: SceneModel):
        """根据Model完全重新渲染"""
        self._clear_all()
        
        self._draw_coordinate_system(model.coord_range, model.user_frame)
        self._draw_devices(model.devices, model.label_positions)
        self._draw_sectors(model.sectors)
        self._draw_measurement(model.measurement, model.world_frame, model.user_frame)
        
        self.figure.canvas.draw_idle()
    
    def _draw_coordinate_system(self, coord_range: Tuple[float, float], 
                                user_frame: Optional[CoordinateFrame]):
        """绑制坐标系（世界坐标系 + 可选的用户坐标系）"""
        pass
    
    def _draw_devices(self, devices: List[Device], 
                      label_positions: Dict[str, LabelPosition]):
        """绘制设备点和标签"""
        pass
    
    def _draw_sectors(self, sectors: List[SectorData]):
        """绘制扇形区域"""
        pass
    
    def _draw_measurement(self, measurement: Optional[MeasurementData],
                         world_frame: CoordinateFrame,
                         user_frame: Optional[CoordinateFrame]):
        """绘制测量点和信息"""
        pass
    
    def _clear_all(self):
        """清除所有绑制对象"""
        pass
```

#### 第一期 - 验收标准

- [ ] CoordinateFrame 正确实现世界↔本地坐标转换
- [ ] SceneModel 作为单一数据源工作正常
- [ ] 数据变更时View自动更新（观察者模式）
- [ ] 原有功能（设备管理、测量、扇形）正常工作
- [ ] 代码量减少30%以上

#### 第一期 - 测试用例

```python
# tests/test_phase1_core_refactor.py

class TestCoordinateFrame:
    def test_world_to_local_basic(self):
        """测试基本坐标转换"""
        frame = CoordinateFrame("user", 2.0, 3.0)
        local_x, local_y = frame.world_to_local(5.0, 7.0)
        assert local_x == 3.0
        assert local_y == 4.0
    
    def test_round_trip_conversion(self):
        """测试双向转换一致性"""
        frame = CoordinateFrame("user", -1.5, 2.5)
        world_x, world_y = 3.0, 4.0
        local = frame.world_to_local(world_x, world_y)
        back = frame.local_to_world(*local)
        assert abs(back[0] - world_x) < 1e-10
        assert abs(back[1] - world_y) < 1e-10

class TestSceneModel:
    def test_observer_notification(self):
        """测试观察者通知"""
        model = SceneModel()
        changes = []
        model.add_observer(lambda t: changes.append(t))
        
        model.add_device(Device("测试", 1.0, 2.0))
        assert "device_added" in changes
    
    def test_user_frame_activation(self):
        """测试用户坐标系激活"""
        model = SceneModel()
        assert not model.is_user_frame_active()
        
        model.set_user_position(1.0, 2.0)
        assert model.is_user_frame_active()
```

---

### 📅 第二期：标签布局系统重构（预计4天）

**目标**：用确定性算法替换复杂的力导向布局，实现标签手动拖拽

#### 第二期 - 任务分解

| 序号 | 任务 | 说明 | 预计耗时 |
|------|------|------|----------|
| 2.1 | 创建 `LabelPlacer` 服务 | 确定性8方向标签布局 | 1天 |
| 2.2 | 实现碰撞检测模块 | 标签与扇形、其他标签的碰撞 | 0.5天 |
| 2.3 | 实现标签拖拽交互 | 鼠标拖拽标签到新位置 | 1天 |
| 2.4 | 标签位置持久化 | 手动位置保存到项目文件 | 0.5天 |
| 2.5 | 集成测试与UI优化 | 拖拽视觉反馈、光标变化 | 1天 |

#### 第二期 - 详细设计

##### 2.1 LabelPlacer 服务

```python
# 文件: dev/src/services/label_placer.py

@dataclass
class LabelPosition:
    """标签位置数据"""
    x: float
    y: float
    is_manual: bool = False  # 是否手动设置
    direction: str = ""      # 方向名称（调试用）

class LabelPlacer:
    """
    标签布局服务 - 确定性算法
    
    核心原则：
    1. 同样的输入永远产生同样的输出
    2. 按优先级顺序尝试8个方向
    3. 避开扇形区域和其他已放置的标签
    """
    
    # 8个方向，按优先级排序
    DIRECTIONS = [
        (1.2, 0.8, "右上"),
        (-1.2, 0.8, "左上"),
        (1.2, -0.8, "右下"),
        (-1.2, -0.8, "左下"),
        (1.6, 0, "右"),
        (-1.6, 0, "左"),
        (0, 1.2, "上"),
        (0, -1.2, "下"),
    ]
    
    # 标签尺寸配置
    LABEL_SIZES = {
        "device": (2.0, 0.8),
        "measurement": (2.5, 1.2),
        "user": (1.8, 0.6),
    }
    
    def __init__(self):
        self.collision_detector = CollisionDetector()
    
    def calculate_positions(self, 
                           devices: List[Device],
                           sectors: List[SectorData],
                           coord_range: Tuple[float, float],
                           existing_manual: Dict[str, LabelPosition] = None
                           ) -> Dict[str, LabelPosition]:
        """
        计算所有标签的最佳位置（确定性算法）
        
        Args:
            devices: 设备列表
            sectors: 扇形列表（作为障碍物）
            coord_range: 坐标范围
            existing_manual: 已有的手动位置（不会被覆盖）
        
        Returns:
            element_id -> LabelPosition 的映射
        """
        result = {}
        placed_boxes: List[BoundingBox] = []
        
        # 转换扇形为障碍物边界框
        obstacles = [self._sector_to_bbox(s) for s in sectors]
        
        # 按设备ID排序，确保顺序一致
        sorted_devices = sorted(devices, key=lambda d: d.id)
        
        for device in sorted_devices:
            element_id = f"device_{device.id}"
            
            # 如果有手动位置，保留它
            if existing_manual and element_id in existing_manual:
                result[element_id] = existing_manual[element_id]
                placed_boxes.append(self._label_to_bbox(existing_manual[element_id], "device"))
                continue
            
            # 计算最佳自动位置
            position = self._find_best_position(
                anchor=(device.x, device.y),
                label_type="device",
                obstacles=obstacles,
                placed_boxes=placed_boxes,
                coord_range=coord_range
            )
            
            result[element_id] = position
            placed_boxes.append(self._label_to_bbox(position, "device"))
        
        return result
    
    def _find_best_position(self,
                           anchor: Tuple[float, float],
                           label_type: str,
                           obstacles: List[BoundingBox],
                           placed_boxes: List[BoundingBox],
                           coord_range: Tuple[float, float]) -> LabelPosition:
        """
        为单个标签找最佳位置
        
        按优先级遍历8个方向，返回第一个无冲突的位置
        """
        label_width, label_height = self.LABEL_SIZES[label_type]
        canvas_bounds = BoundingBox(-coord_range[0], -coord_range[1], 
                                   coord_range[0], coord_range[1])
        
        for dx, dy, direction_name in self.DIRECTIONS:
            candidate_x = anchor[0] + dx
            candidate_y = anchor[1] + dy
            
            candidate_box = BoundingBox(
                candidate_x - label_width / 2,
                candidate_y - label_height / 2,
                candidate_x + label_width / 2,
                candidate_y + label_height / 2
            )
            
            # 检查1：是否在画布范围内
            if not self.collision_detector.is_within_bounds(candidate_box, canvas_bounds, margin=0.3):
                continue
            
            # 检查2：是否与障碍物（扇形）重叠
            if self.collision_detector.overlaps_any(candidate_box, obstacles):
                continue
            
            # 检查3：是否与已放置的标签重叠
            if self.collision_detector.overlaps_any(candidate_box, placed_boxes, margin=0.1):
                continue
            
            # 找到有效位置
            return LabelPosition(x=candidate_x, y=candidate_y, is_manual=False, direction=direction_name)
        
        # 所有方向都不行，使用默认位置（右上，即使有重叠）
        return LabelPosition(
            x=anchor[0] + self.DIRECTIONS[0][0],
            y=anchor[1] + self.DIRECTIONS[0][1],
            is_manual=False,
            direction="默认(有冲突)"
        )
    
    def _sector_to_bbox(self, sector: SectorData) -> BoundingBox:
        """将扇形转换为近似边界框"""
        # 简化：使用扇形的外接矩形
        return BoundingBox(
            sector.center_x - sector.radius,
            sector.center_y - sector.radius,
            sector.center_x + sector.radius,
            sector.center_y + sector.radius
        )
    
    def _label_to_bbox(self, pos: LabelPosition, label_type: str) -> BoundingBox:
        """将标签位置转换为边界框"""
        w, h = self.LABEL_SIZES[label_type]
        return BoundingBox(pos.x - w/2, pos.y - h/2, pos.x + w/2, pos.y + h/2)
```

##### 2.2 碰撞检测模块

```python
# 文件: dev/src/services/collision_detector.py

class CollisionDetector:
    """碰撞检测服务"""
    
    def is_within_bounds(self, box: BoundingBox, bounds: BoundingBox, margin: float = 0) -> bool:
        """检查边界框是否在范围内"""
        return (box.x_min >= bounds.x_min + margin and
                box.x_max <= bounds.x_max - margin and
                box.y_min >= bounds.y_min + margin and
                box.y_max <= bounds.y_max - margin)
    
    def overlaps(self, box1: BoundingBox, box2: BoundingBox, margin: float = 0) -> bool:
        """检查两个边界框是否重叠"""
        return not (box1.x_max + margin <= box2.x_min or
                   box2.x_max + margin <= box1.x_min or
                   box1.y_max + margin <= box2.y_min or
                   box2.y_max + margin <= box1.y_min)
    
    def overlaps_any(self, box: BoundingBox, boxes: List[BoundingBox], margin: float = 0) -> bool:
        """检查边界框是否与列表中任何一个重叠"""
        return any(self.overlaps(box, other, margin) for other in boxes)
    
    def point_in_sector(self, x: float, y: float, sector: SectorData) -> bool:
        """检查点是否在扇形内"""
        dx = x - sector.center_x
        dy = y - sector.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > sector.radius:
            return False
        
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        
        # 检查角度是否在扇形范围内
        start = sector.start_angle % 360
        end = sector.end_angle % 360
        
        if start <= end:
            return start <= angle <= end
        else:
            return angle >= start or angle <= end
```

##### 2.3 标签拖拽交互

```python
# 在 SceneRenderer 中添加拖拽支持

class SceneRenderer:
    def __init__(self, figure: Figure, axes: Axes, controller: 'SceneController'):
        # ...
        self.controller = controller
        
        # 拖拽状态
        self._dragging_label: Optional[str] = None
        self._drag_offset: Tuple[float, float] = (0, 0)
        
        # 绑定拖拽事件
        self.figure.canvas.mpl_connect('button_press_event', self._on_press)
        self.figure.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.figure.canvas.mpl_connect('button_release_event', self._on_release)
    
    def _on_press(self, event):
        """鼠标按下 - 检测是否点击了标签"""
        if event.button != 1 or event.inaxes != self.axes:
            return
        
        # 检测是否点击了某个标签
        clicked_label = self._find_label_at(event.xdata, event.ydata)
        if clicked_label:
            self._dragging_label = clicked_label
            label_pos = self.controller.model.get_label_position(clicked_label)
            self._drag_offset = (label_pos.x - event.xdata, label_pos.y - event.ydata)
            self._set_cursor('move')
    
    def _on_motion(self, event):
        """鼠标移动 - 更新标签位置"""
        if self._dragging_label and event.xdata and event.ydata:
            new_x = event.xdata + self._drag_offset[0]
            new_y = event.ydata + self._drag_offset[1]
            # 实时更新（不触发完整重绘，只移动标签）
            self._update_label_position_visual(self._dragging_label, new_x, new_y)
        else:
            # 检测鼠标是否在标签上，改变光标
            if self._find_label_at(event.xdata, event.ydata):
                self._set_cursor('hand')
            else:
                self._set_cursor('arrow')
    
    def _on_release(self, event):
        """鼠标释放 - 确认新位置"""
        if self._dragging_label:
            if event.xdata and event.ydata:
                new_x = event.xdata + self._drag_offset[0]
                new_y = event.ydata + self._drag_offset[1]
                self.controller.on_label_drag(self._dragging_label, new_x, new_y)
            self._dragging_label = None
            self._set_cursor('arrow')
    
    def _find_label_at(self, x: float, y: float) -> Optional[str]:
        """查找指定位置的标签"""
        if x is None or y is None:
            return None
        
        for element_id, label_pos in self.controller.model.label_positions.items():
            # 简化：使用点击检测（实际应该检测边界框）
            label_size = LabelPlacer.LABEL_SIZES.get("device", (2.0, 0.8))
            if (abs(x - label_pos.x) < label_size[0] / 2 and
                abs(y - label_pos.y) < label_size[1] / 2):
                return element_id
        
        return None
```

##### 2.4 标签位置持久化

```python
# 在项目文件格式中添加标签位置

# ProjectManager.save_project 中增加:
project_data = {
    # ... 现有字段 ...
    'label_positions': {
        element_id: {
            'x': pos.x,
            'y': pos.y,
            'is_manual': pos.is_manual
        }
        for element_id, pos in scene_model.label_positions.items()
        if pos.is_manual  # 只保存手动位置
    }
}
```

#### 第二期 - 验收标准

- [ ] 确定性算法：同样输入产生同样输出
- [ ] 8方向布局正确避开扇形和其他标签
- [ ] 标签可以拖拽到新位置
- [ ] 拖拽时光标变化，有视觉反馈
- [ ] 手动位置在右键清除后保持（直到重置）
- [ ] 手动位置保存到项目文件

#### 第二期 - 测试用例

```python
# tests/test_phase2_label_placer.py

class TestLabelPlacer:
    def test_deterministic_output(self):
        """测试确定性输出"""
        placer = LabelPlacer()
        devices = [Device("A", 1.0, 1.0), Device("B", -1.0, 2.0)]
        
        result1 = placer.calculate_positions(devices, [], (10, 10))
        result2 = placer.calculate_positions(devices, [], (10, 10))
        
        assert result1 == result2
    
    def test_avoid_sector(self):
        """测试避开扇形区域"""
        placer = LabelPlacer()
        device = Device("Test", 0, 0)
        sector = SectorData(0, 0, 2.0, -45, 45)  # 右侧扇形
        
        result = placer.calculate_positions([device], [sector], (10, 10))
        pos = result["device_" + device.id]
        
        # 应该选择左上而不是右上
        assert pos.x < 0  # 在左侧
    
    def test_preserve_manual_position(self):
        """测试保留手动位置"""
        placer = LabelPlacer()
        device = Device("Test", 0, 0)
        manual = {"device_" + device.id: LabelPosition(5.0, 5.0, is_manual=True)}
        
        result = placer.calculate_positions([device], [], (10, 10), existing_manual=manual)
        
        assert result["device_" + device.id].x == 5.0
        assert result["device_" + device.id].y == 5.0

class TestLabelDrag:
    def test_drag_updates_position(self):
        """测试拖拽更新位置"""
        model = SceneModel()
        model.add_device(Device("Test", 0, 0))
        
        # 模拟拖拽
        controller = SceneController(model, None)
        controller.on_label_drag("device_xxx", 3.0, 4.0)
        
        pos = model.get_label_position("device_xxx")
        assert pos.x == 3.0
        assert pos.y == 4.0
        assert pos.is_manual == True
```

---

### 📅 第三期：导出优化与体验提升（预计3天）

**目标**：专门为PNG导出优化布局，提升整体用户体验

#### 第三期 - 任务分解

| 序号 | 任务 | 说明 | 预计耗时 |
|------|------|------|----------|
| 3.1 | 创建 `ExportRenderer` | 导出专用渲染，重新计算布局 | 1天 |
| 3.2 | 导出布局优化算法 | 更大间距、更安全的位置 | 0.5天 |
| 3.3 | 多格式导出支持 | PNG/SVG/PDF格式选择 | 0.5天 |
| 3.4 | UI体验优化 | 快捷键提示、状态栏、工具提示 | 0.5天 |
| 3.5 | 综合测试与文档更新 | 全流程测试、更新文档 | 0.5天 |

#### 第三期 - 详细设计

##### 3.1 ExportRenderer 服务

```python
# 文件: dev/src/services/export_renderer.py

class ExportRenderer:
    """
    导出专用渲染器
    
    为PNG/SVG/PDF导出专门优化的渲染器，特点：
    1. 重新计算标签位置（使用更大间距）
    2. 创建独立的Figure（不影响屏幕显示）
    3. 支持多种输出格式
    """
    
    # 导出专用配置
    EXPORT_CONFIG = {
        'label_margin': 0.5,      # 标签之间的最小间距（比屏幕显示更大）
        'border_margin': 0.8,     # 边界安全距离
        'font_scale': 1.2,        # 字体放大比例
        'line_width_scale': 1.5,  # 线条加粗比例
    }
    
    def __init__(self):
        self.label_placer = LabelPlacer()
    
    def export(self, model: SceneModel, file_path: str, 
               format: str = 'png', dpi: int = 300) -> Tuple[bool, str]:
        """
        执行导出
        
        Args:
            model: 场景数据模型
            file_path: 输出文件路径
            format: 格式 ('png', 'svg', 'pdf')
            dpi: 分辨率（仅对PNG有效）
        
        Returns:
            (成功标志, 消息)
        """
        try:
            # 1. 创建独立的Figure
            fig_size = (10, 10)
            export_fig, export_ax = plt.subplots(figsize=fig_size, dpi=dpi)
            
            # 2. 重新计算导出专用的标签位置
            export_label_positions = self._calculate_export_labels(model)
            
            # 3. 绑制所有元素（使用导出优化的样式）
            self._draw_export_content(export_fig, export_ax, model, export_label_positions)
            
            # 4. 保存文件
            export_fig.savefig(
                file_path,
                format=format,
                dpi=dpi if format == 'png' else None,
                bbox_inches='tight',
                facecolor=SceneRenderer.COLORS['background'],
                edgecolor='none'
            )
            
            # 5. 清理
            plt.close(export_fig)
            
            return True, f"成功导出到: {file_path}"
            
        except Exception as e:
            return False, f"导出失败: {str(e)}"
    
    def _calculate_export_labels(self, model: SceneModel) -> Dict[str, LabelPosition]:
        """
        计算导出专用的标签位置
        
        使用更严格的间距要求，确保导出图片的清晰可读性
        """
        # 创建一个专门为导出配置的LabelPlacer实例
        export_placer = LabelPlacer()
        
        # 修改间距配置
        export_placer.collision_margin = self.EXPORT_CONFIG['label_margin']
        export_placer.border_margin = self.EXPORT_CONFIG['border_margin']
        
        # 保留手动位置，重新计算自动位置
        manual_positions = {
            k: v for k, v in model.label_positions.items() 
            if v.is_manual
        }
        
        return export_placer.calculate_positions(
            model.devices,
            model.sectors,
            model.coord_range,
            existing_manual=manual_positions
        )
    
    def _draw_export_content(self, fig: Figure, ax: Axes, 
                            model: SceneModel, 
                            label_positions: Dict[str, LabelPosition]):
        """绘制导出内容（使用放大的样式）"""
        scale = self.EXPORT_CONFIG
        
        # 设置坐标系
        x_range, y_range = model.coord_range
        ax.set_xlim(-x_range, x_range)
        ax.set_ylim(-y_range, y_range)
        ax.set_aspect('equal')
        
        # 绘制网格
        ax.grid(True, alpha=0.6, linewidth=0.8 * scale['line_width_scale'])
        ax.axhline(y=0, color='#37474f', linewidth=1.5 * scale['line_width_scale'])
        ax.axvline(x=0, color='#37474f', linewidth=1.5 * scale['line_width_scale'])
        
        # 绘制用户坐标系（如果有）
        if model.user_frame:
            self._draw_user_frame_export(ax, model.user_frame, scale)
        
        # 绘制扇形
        for sector in model.sectors:
            self._draw_sector_export(ax, sector, scale)
        
        # 绘制设备和标签
        for device in model.devices:
            element_id = f"device_{device.id}"
            label_pos = label_positions.get(element_id)
            self._draw_device_export(ax, device, label_pos, scale)
        
        # 绘制测量点
        if model.measurement:
            self._draw_measurement_export(ax, model.measurement, model.user_frame, scale)
```

##### 3.3 格式选择对话框

```python
# 在导出功能中增加格式选择

class ExportDialog:
    """导出对话框"""
    
    FORMATS = [
        ("PNG图片 (*.png)", "png", "高清栅格图像，适合网页和文档"),
        ("SVG矢量图 (*.svg)", "svg", "可缩放矢量图，适合编辑和高质量打印"),
        ("PDF文档 (*.pdf)", "pdf", "文档格式，适合打印和归档"),
    ]
    
    def show(self, parent) -> Optional[Dict]:
        """
        显示导出对话框
        
        Returns:
            {'format': 'png', 'dpi': 300, 'path': '/path/to/file'} or None
        """
        # 创建对话框
        dialog = tk.Toplevel(parent)
        dialog.title("导出图像")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        
        # 格式选择
        format_var = tk.StringVar(value="png")
        ttk.Label(dialog, text="选择格式:").pack(anchor='w', padx=10, pady=(10, 5))
        
        for display_name, format_id, description in self.FORMATS:
            frame = ttk.Frame(dialog)
            frame.pack(fill='x', padx=10)
            ttk.Radiobutton(frame, text=display_name, variable=format_var, 
                           value=format_id).pack(side='left')
            ttk.Label(frame, text=description, foreground='gray').pack(side='left', padx=(10, 0))
        
        # DPI设置（仅PNG）
        dpi_var = tk.StringVar(value="300")
        dpi_frame = ttk.Frame(dialog)
        dpi_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(dpi_frame, text="分辨率 (DPI):").pack(side='left')
        dpi_entry = ttk.Entry(dpi_frame, textvariable=dpi_var, width=10)
        dpi_entry.pack(side='left', padx=5)
        
        # 按钮
        result = {'confirmed': False}
        
        def on_export():
            result['confirmed'] = True
            result['format'] = format_var.get()
            result['dpi'] = int(dpi_var.get())
            dialog.destroy()
        
        ttk.Button(dialog, text="导出", command=on_export).pack(side='right', padx=10, pady=10)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack(side='right', pady=10)
        
        dialog.wait_window()
        
        if not result['confirmed']:
            return None
        
        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            title="保存图像",
            defaultextension=f".{result['format']}",
            filetypes=[(f"{result['format'].upper()}文件", f"*.{result['format']}")]
        )
        
        if file_path:
            result['path'] = file_path
            return result
        return None
```

#### 第三期 - 验收标准

- [ ] 导出PNG清晰可读，所有元素无遮挡
- [ ] 支持PNG/SVG/PDF三种格式导出
- [ ] 导出使用更大间距，布局更清晰
- [ ] 手动拖拽的标签位置在导出时保持
- [ ] 快捷键有提示说明
- [ ] 状态栏显示当前坐标系模式

#### 第三期 - 测试用例

```python
# tests/test_phase3_export.py

class TestExportRenderer:
    def test_export_png_no_overlap(self):
        """测试导出PNG无重叠"""
        model = SceneModel()
        # 添加多个靠近的设备
        model.add_device(Device("A", 0, 0))
        model.add_device(Device("B", 0.5, 0.5))
        model.add_device(Device("C", 1.0, 0))
        
        renderer = ExportRenderer()
        success, _ = renderer.export(model, "/tmp/test_export.png")
        
        assert success
        # 可以添加图像分析来验证无重叠
    
    def test_export_preserves_manual_positions(self):
        """测试导出保留手动位置"""
        model = SceneModel()
        device = Device("Test", 0, 0)
        model.add_device(device)
        model.set_label_position(f"device_{device.id}", 5.0, 5.0, is_manual=True)
        
        renderer = ExportRenderer()
        labels = renderer._calculate_export_labels(model)
        
        pos = labels[f"device_{device.id}"]
        assert pos.x == 5.0
        assert pos.y == 5.0
```

---

## 风险评估与应对

### 风险1：重构期间功能不可用
- **概率**: 中
- **影响**: 高
- **应对措施**: 
  - 保留原代码在独立分支
  - 分模块渐进式重构
  - 每完成一个模块立即测试

### 风险2：标签拖拽交互复杂
- **概率**: 中
- **影响**: 中
- **应对措施**:
  - 先实现基础拖拽，再优化视觉反馈
  - 参考Matplotlib官方示例

### 风险3：确定性算法在极端情况下失效
- **概率**: 低
- **影响**: 低
- **应对措施**:
  - 提供"重置标签位置"功能
  - 允许手动调整作为后备

---

## 资源与时间总结

| 阶段 | 主要任务 | 预计工时 | 输出物 |
|------|----------|----------|--------|
| 第一期 | 核心架构重构 | 5天 | CoordinateFrame, SceneModel, SceneController, SceneRenderer |
| 第二期 | 标签布局重构 | 4天 | LabelPlacer, 拖拽交互, 位置持久化 |
| 第三期 | 导出优化与体验 | 3天 | ExportRenderer, 多格式支持, UI优化 |
| **总计** | | **12天** | V2.0完整版本 |

---

## 里程碑与验收节点

| 里程碑 | 完成时间 | 验收标准 |
|--------|----------|----------|
| M1: 架构重构完成 | 第一期结束 | 所有原有功能正常，代码量减少30% |
| M2: 标签系统完成 | 第二期结束 | 确定性布局，支持拖拽 |
| M3: V2.0发布 | 第三期结束 | 导出优化，体验提升，文档更新 |

---

## 下一步行动

1. **评审本计划**：确认范围、优先级、时间估算
2. **创建Git分支**：`feature/v2-refactor`
3. **开始第一期**：从CoordinateFrame类开始

---

*文档版本: 1.0*
*创建日期: 2025-11-26*
*作者: AI架构师*

