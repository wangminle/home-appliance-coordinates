# 锁定扇形在用户坐标系首次设置位置时未自动解锁 — 测试总结

## 测试日期
2025-12-15

## 背景与问题描述

当“锁定扇形（说话人方向和影响范围）”在**世界坐标系**下创建并锁定后，用户随后**启用用户坐标系**并首次设置用户位置（`None -> (x, y)`），参考中心会从世界原点 `(0,0)` 切换到用户位置。

旧逻辑在 `views/matplotlib_view.py` 的 `set_user_position()` 中仅在 `old_position != None` 时才自动解锁，导致：

- 锁仍保持有效；
- `LockedMeasurement.center_point` 仍为旧中心点；
- 后续对比虚线沿用旧中心点计算，从而出现**角度/距离错误**。

## 修改内容概述

- 修复 `set_user_position()`：当锁定存在且**参考中心发生变化**时，自动解锁（覆盖 `None -> 新位置` 的首次设置场景）。
- 修复 `RegularPolygon` 参数：将用户位置标记的 `edgecolors` 更正为 `edgecolor`，避免在部分 Matplotlib 版本下抛异常导致用户位置设置流程中断。

## 测试脚本

- `tests/test_locked_sector_user_coord_unlock_bugfix_20251215.py`

## 覆盖范围

### 正常功能测试

- **用例**：世界坐标系下创建并锁定扇形 → 启用用户坐标系 → 首次设置用户位置（`None -> (x, y)`）
- **预期**：触发自动解锁
- **结果**：✅ 通过

### 边界条件测试

- **用例**：仍处于世界坐标系（`user_coord_enabled=False`）时设置用户位置
- **预期**：参考中心不变，不应触发自动解锁
- **结果**：✅ 通过

### 异常情况测试

- **用例**：用户坐标系已启用时，传入非法用户位置类型（如 `x="bad_x"`）
- **预期**：抛出异常，且不应误解锁
- **结果**：✅ 通过

## 测试结果统计

- **总用例数**：3
- **通过**：3
- **失败**：0
- **通过率**：100%

## 相关文件变更

### 修改文件

- `dev/src/views/matplotlib_view.py`
  - 修复 `set_user_position()` 自动解锁条件（覆盖 `None -> 新位置`）
  - 修复 `_draw_user_position_marker()` 中 `RegularPolygon` 参数兼容性问题

### 新增文件

- `tests/test_locked_sector_user_coord_unlock_bugfix_20251215.py`
- `tests/test_locked_sector_user_coord_unlock_bugfix_20251215.md`

## 结论

该缺陷已修复并通过回归测试验证：在锁定扇形存在的情况下，用户坐标系首次设置用户位置会正确触发自动解锁，避免后续对比线沿用旧中心点导致角度/距离错误。


