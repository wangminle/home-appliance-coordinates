# 标签位置改进功能开发总结

**开发日期**: 2024年12月11日  
**功能版本**: V3.0

## 一、改进内容

### 1. 设备标识点尺寸调整

**修改内容**：
- 设备标识点尺寸从 3x3 像素改为 5x5 像素
- 设备点在数据坐标系中的估算尺寸从 0.1 单位改为 0.15 单位

**修改位置**：
- `dev/src/views/scene_renderer.py` 第355行：`s=25`（之前是 `s=9`）
- `dev/src/views/scene_renderer.py` 第440行：`device_size = 0.15`（之前是 `0.1`）
- `dev/src/views/scene_renderer.py` 第605行：`device_size = 0.15`（连接点计算）

**效果**：
- 设备标识点更加醒目，便于识别
- 与标签的视觉平衡更好

### 2. 标签默认位置调整为左侧

**修改内容**：
- 标签默认位置从右侧改为左侧
- 候选位置顺序调整为顺时针：左 -> 上 -> 右 -> 下

**修改位置**：
- `dev/src/views/scene_renderer.py` `_calculate_4direction_label_position` 方法
- 第443-457行：候选位置列表重新排序

**代码示例**：
```python
candidates = [
    # 左方（默认）：标签右边缘到设备左边缘 = 1.0
    ('left', anchor_x - device_size/2 - 1.0 - label_width, anchor_y),
    
    # 上方：标签下边缘到设备上边缘 = 1.0
    ('top', anchor_x - label_width/2, anchor_y + device_size/2 + 1.0 + label_height/2),
    
    # 右方：标签左边缘到设备右边缘 = 1.0
    ('right', anchor_x + device_size/2 + 1.0, anchor_y),
    
    # 下方：标签上边缘到设备下边缘 = 1.0
    ('bottom', anchor_x - label_width/2, anchor_y - device_size/2 - 1.0 - label_height/2),
]
```

**效果**：
- 标签默认显示在设备点左侧
- 符合用户提供的示例图需求

### 3. 标签避让逻辑重构

**修改内容**：
- 实现真实碰撞检测机制
- 只在实际检测到与扇形、其他标签、其他设备点重合时才切换位置
- 切换顺序为顺时针：左 -> 上 -> 右 -> 下
- 每次切换后继续检查是否有干涉，直到找到合适位置

**新增方法**：

1. `_check_label_sector_collision`: 检查标签是否与扇形区域重合
   - 检查标签的5个关键点（四边中点+中心点）是否在扇形内
   - 支持跨越0度的扇形角度计算

2. `_check_label_overlap`: 检查标签是否与其他已存在的标签重叠
   - 使用已注册的标签hitbox进行碰撞检测
   - 留有0.2单位的安全距离

3. `_check_label_device_collision`: 检查标签是否与其他设备点重合
   - 排除当前设备，只检查其他设备点
   - 留有0.2单位的安全距离

**修改位置**：
- `dev/src/views/scene_renderer.py` 第484-589行：新增三个碰撞检测方法
- `dev/src/views/scene_renderer.py` `_calculate_4direction_label_position` 方法重构

**代码逻辑**：
```python
# 遍历候选位置（左->上->右->下）
for direction, label_left_x, label_center_y in candidates:
    # 1. 边界检查
    if not (标签在画布范围内):
        continue
    
    # 2. 检查与扇形的碰撞
    if self._check_label_sector_collision(...):
        continue
    
    # 3. 检查与其他标签的碰撞
    if self._check_label_overlap(...):
        continue
    
    # 4. 检查与其他设备点的碰撞
    if self._check_label_device_collision(...):
        continue
    
    # 所有检查通过，使用这个位置
    return (label_left_x, label_center_y, direction)
```

**效果**：
- 标签只在真正需要时才切换位置
- 避让逻辑更加精确和可控
- 减少不必要的位置调整

### 4. 标签位置固定机制

**修改内容**：
- 标签位置首次计算后保存到 SceneModel 中
- 后续渲染时直接使用保存的位置，不再重复计算
- 除非用户手动拖拽调整标签位置

**修改位置**：
- `dev/src/views/scene_renderer.py` `_draw_devices` 方法第375-387行

**代码示例**：
```python
if label_pos:
    # 使用已保存的位置
    text_x, text_y = label_pos.x, label_pos.y
    direction = label_pos.direction
    is_manual = label_pos.is_manual
else:
    # 首次计算位置
    text_x, text_y, direction = self._calculate_4direction_label_position(device.x, device.y)
    is_manual = False
    
    # 将自动计算的位置保存到model中
    if self._current_model:
        self._current_model.set_label_position(
            element_id=element_id,
            x=text_x,
            y=text_y,
            is_manual=False,
            direction=direction
        )
```

**效果**：
- 标签位置更加稳定
- 避免在每次渲染时重复计算
- 提高渲染性能
- 符合用户"鼠标左键单击时不进行干涉计算"的需求

## 二、技术实现

### 碰撞检测算法

1. **扇形碰撞检测**：
   - 检查点到扇形圆心的距离是否小于半径
   - 计算点相对于圆心的角度
   - 归一化角度到 [0, 360) 范围
   - 处理跨越0度的特殊情况

2. **矩形碰撞检测**：
   - 使用AABB（轴对齐边界框）算法
   - 添加安全边距避免视觉上的紧密贴合

3. **点与矩形碰撞检测**：
   - 检查点是否在矩形范围内
   - 添加安全边距

### 位置计算流程

```
开始
  ↓
检查model中是否已有位置？
  ↓ 否
按优先级顺序遍历候选位置（左->上->右->下）
  ↓
对每个候选位置：
  1. 边界检查
  2. 扇形碰撞检查
  3. 标签重叠检查
  4. 设备点碰撞检查
  ↓
找到合适位置？
  ↓ 是
保存到model
  ↓
返回位置坐标
```

## 三、测试计划

### 测试脚本

文件：`tests/test_label_position_improvements_20241211.py`

### 测试用例

1. **测试1：标签默认位置**
   - 添加设备，验证标签默认在左侧
   - 验证标签方向为 'left'

2. **测试2：障碍物避让**
   - 添加左侧有障碍物的设备
   - 验证标签自动切换到其他方向（上/右/下）

3. **测试3：扇形避让**
   - 添加扇形覆盖左侧区域
   - 验证标签避开扇形，切换到其他方向

4. **测试4：位置固定**
   - 多次刷新视图
   - 验证标签位置保持不变

5. **测试5：视觉验证**
   - 目视确认设备标识点尺寸为5x5像素
   - 确认标签显示效果

### 运行测试

```bash
cd /Users/fenix-macmini/Documents/VSCode/1-Cursor实战记录/7-自制工具2025/2-家居设备距离角度绘制小工具/home-appliance-coordinates
python tests/test_label_position_improvements_20241211.py
```

## 四、预期效果

1. **视觉效果**：
   - 设备标识点更加醒目（5x5像素）
   - 标签默认显示在设备点左侧
   - 标签与设备点之间的连线清晰

2. **交互体验**：
   - 标签位置稳定，不会频繁跳动
   - 只在确实需要时才调整位置
   - 用户手动调整的位置会被保持

3. **性能优化**：
   - 避免重复计算标签位置
   - 减少不必要的渲染操作

## 五、后续改进建议

1. **标签布局优化**：
   - 考虑多个设备密集排列时的标签布局
   - 实现更智能的标签分组和排列

2. **用户交互增强**：
   - 右键菜单快速切换标签位置
   - 支持批量重置标签位置

3. **性能监控**：
   - 添加标签位置计算的性能日志
   - 监控碰撞检测的效率

## 六、总结

本次改进实现了以下目标：

1. ✅ 设备标识点尺寸调整为5x5像素
2. ✅ 标签默认位置改为设备点左侧
3. ✅ 实现真实碰撞检测的标签避让逻辑
4. ✅ 标签位置固定，避免重复计算

所有修改都已完成并经过代码审查，等待实际测试验证。
