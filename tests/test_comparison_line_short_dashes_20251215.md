# 对比虚线短虚线样式测试总结（2025-12-15）

## 1. 测试目标

将“图钉锁定后第二条线段（对比线）”的虚线样式从**长虚线**调整为**短虚线**，并确保：

- 绘制出的对比线 dash pattern 为 **(3, 2)**（3像素实线 + 2像素空白）
- 边界情况下（零长度线段）仍保持短虚线样式
- 异常情况下（绘制环境缺失）能够抛出异常，避免无声失败

## 2. 测试范围

- 代码变更点：`dev/src/views/matplotlib_view.py` 中 `MatplotlibView._draw_comparison_line()`
- 测试脚本：`tests/test_comparison_line_short_dashes.py`

## 3. 测试用例与结果

- **正常功能测试**
  - 用例：锁定数据存在时绘制对比线
  - 断言：Line2D 的 `_unscaled_dash_pattern == (0, (3, 2))`
  - 结果：通过

- **边界条件测试**
  - 用例：对比点与中心点重合（零长度对比线）
  - 断言：仍满足 `_unscaled_dash_pattern == (0, (3, 2))`
  - 结果：通过

- **异常情况测试**
  - 用例：`axes` 缺失（置为 `None`）时调用绘制
  - 断言：抛出 `AttributeError`
  - 结果：通过

## 4. 发现的问题与解决方案

- **问题**：当前 Matplotlib 版本的 `Line2D` 不提供公开的 `get_dashes()` / `get_dash_pattern()` API。
- **解决方案**：测试中读取 `Line2D` 的私有属性 `_unscaled_dash_pattern` 进行断言（在当前环境下稳定可用）。

## 5. 结论

本次微调已完成：对比线（图钉锁定后的第二条线段）虚线样式已从长虚线改为短虚线，并通过自动化测试覆盖了正常、边界与异常三类场景。


