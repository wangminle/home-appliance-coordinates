# test_user_coordinate_visual_tweaks_20251213.md

## 1. 测试目标

验证"用户坐标系"相关的交互与视觉调整满足以下需求：

- 用户坐标系中不再显示任何随动坐标信息框
- 用户坐标系坐标轴颜色为红色，线宽下降一半
- 用户坐标系原点标签固定在用户坐标点正下方 2 格（严格为 \((x, y-2.0)\)），不随动
- 用户坐标系原点标签字号/字重与设备标签一致（`fontsize=9`、`bold`），背景透明度为 `0.6`
- **测量标签同样固定在点击点正下方 2 格，不被 adjustText 移动**

## 2. 测试环境

- OS：Windows 10
- Python：3.12（以 `python -m unittest` 方式执行）
- 说明：`MatplotlibView` 测试使用 Mock 屏蔽 Tk 真实组件创建；`SceneRenderer` 测试使用 Matplotlib `Figure/Axes`，不依赖 Tk。

## 3. 覆盖范围与用例

测试脚本：`tests/test_user_coordinate_visual_tweaks_20251213.py`

- **正常功能测试**
  - 用户坐标系下不生成随动坐标信息框
  - 用户坐标系轴线为红色（`#d32f2f`），虚线 4 条（2主+2辅），线宽分别为 `0.75/0.25`
  - 用户原点标签位置固定为 `(x, y-2.0)`，且不参与智能避让
  - 标签字体与设备一致（`fontsize=9`、`bold`），背景 alpha≈`0.6`
  - **测量标签被正确识别为 `MEASUREMENT_INFO` 类型，不被 adjustText 移动**
  - **用户坐标系模式下测量标签同样被正确识别**
- **边界条件测试**
  - 用户位置接近/超出画布边界时，标签仍保持严格固定偏移（不做边界挪动）
- **异常情况测试**
  - 用户位置传入非法类型时抛出异常；同时确保随动信息框仍保持关闭状态
  - `SceneRenderer.draw_coordinate_info()` 在用户坐标系模式下也不再绘制随动信息（并对异常输入保持鲁棒）

## 4. 执行方式与结果

执行命令：

```bash
python -m unittest -v tests.test_user_coordinate_visual_tweaks_20251213
```

执行结果：

- **总用例数**：9
- **通过**：9
- **失败**：0

```
test_01_renderer_no_coordinate_info_even_in_user_mode ... ok
test_02_renderer_user_axes_and_label_style ... ok
test_01_user_mode_no_hover_coordinate_info ... ok
test_02_user_axes_style_is_red_and_half_width ... ok
test_03_user_origin_label_fixed_position_and_style ... ok
test_04_boundary_case_label_not_clamped ... ok
test_05_exception_case_invalid_user_position_type ... ok
test_06_measurement_label_correctly_identified_and_fixed ... ok
test_07_measurement_label_in_user_mode_correctly_identified ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.379s

OK
```

## 5. 发现的问题与解决方案

### 5.1 问题 1：缩进错误导致模块无法导入

- **问题描述**：`dev/src/views/matplotlib_view.py` 的 `_draw_coordinate_info()` 里存在历史遗留缩进错误（`IndentationError`），导致解释器在导入模块阶段直接失败。
- **解决方案**：将 `_draw_coordinate_info()` 精简为"清理残留并立即返回"的实现，彻底关闭世界/用户坐标系的随动信息框，同时移除不可达且缩进不正确的旧逻辑，保证模块可正常导入与运行。

### 5.2 问题 2：[P1] 测量标签仍被 adjustText 移动

- **问题描述**：测量标签（measurement labels）仍然被分类为可移动的文本，导致它们会被 adjustText 移动，违反了"固定在正下方 2 格，不随动"的要求。
- **根本原因**：`_get_element_type_from_text()` 的检测顺序错误：
  - 先检查 `'[用户]' in text_content` → 返回 `USER_POSITION`
  - 再检查 `'[世界]' in text_content` → 返回 `COORDINATE_INFO`
  - 最后检查 `'距离:' in text_content and '角度:' in text_content` → 返回 `MEASUREMENT_INFO`
  
  但测量标签的文本格式为 `"[世界坐标系]\n距离: ...\n角度: ..."` 或 `"[用户坐标系]\n距离: ...\n角度: ..."`，会先匹配到 `[世界]` 或 `[用户]` 条件，导致被错误识别为 `COORDINATE_INFO` 或 `USER_POSITION`，从而绕过 `_apply_smart_text_adjustment()` 的过滤逻辑。

- **解决方案**：调整 `_get_element_type_from_text()` 的检测顺序，将测量标签检测（`'距离:' + '角度:'`）放到最前面优先识别：
  ```python
  def _get_element_type_from_text(self, text_obj) -> ElementType:
      text_content = text_obj.get_text()
      
      # 1. 测量标签优先检测
      if '距离:' in text_content and '角度:' in text_content:
          return ElementType.MEASUREMENT_INFO
      
      # 2. 用户原点标签
      if text_content.startswith('[用户] 位置'):
          return ElementType.USER_POSITION
      
      # 3. 坐标信息框
      if '[世界]' in text_content or '[用户]' in text_content:
          return ElementType.COORDINATE_INFO
      
      # 4. 其他默认为设备标签
      return ElementType.DEVICE_INFO
  ```

## 6. 涉及文件变更

| 文件路径 | 变更内容 |
|----------|----------|
| `dev/src/views/matplotlib_view.py` | 关闭随动信息、轴线样式调整、原点标签固定位置与样式、移除旧代码、**修复 `_get_element_type_from_text()` 检测顺序** |
| `dev/src/views/scene_renderer.py` | 关闭随动信息、轴线样式调整、原点标签固定位置与样式 |
| `tests/test_user_coordinate_visual_tweaks_20251213.py` | 新增测试脚本（9 个用例） |
| `tests/test_user_coordinate_visual_tweaks_20251213.md` | 本测试总结文档 |
