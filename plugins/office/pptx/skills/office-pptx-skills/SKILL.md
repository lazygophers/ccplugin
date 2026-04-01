---
description: "PowerPoint/pptx 演示文稿操作技能 - 创建编辑幻灯片、插入文本图片图表、应用模板主题、格式转换、智能分析。适用于制作汇报PPT、批量生成slides等场景"
triggers:
  - powerpoint
  - pptx
  - presentation
  - 演示文稿
  - 幻灯片
  - slides
  - 转换
  - 模板
---

# PowerPoint pptx 操作技能

通过 MCP 工具 + 包装层操作 PowerPoint 文件。

## MCP 基础工具（34 工具）

通过 `powerpoint` MCP 服务提供，覆盖 PPT 完整 CRUD：

### 演示文稿管理（7 工具）
- `create_presentation` - 创建新演示文稿
- `create_presentation_from_template` - 从模板文件创建（template_path）
- `open_presentation` / `save_presentation` - 打开和保存（file_path）
- `get_presentation_info` - 获取演示文稿信息
- `get_template_file_info` - 分析模板文件（template_path）
- `set_core_properties` - 设置文档属性（title, subject, author, keywords, comments）

### 内容管理（8 工具）
- `add_slide` - 添加幻灯片（layout_name, background_style?）
- `get_slide_info` / `extract_slide_text` - 获取幻灯片信息和文本（slide_index）
- `extract_presentation_text` - 提取所有文本
- `populate_placeholder` - 填充占位符（slide_index, placeholder_name, text）
- `add_bullet_points` - 添加项目符号（slide_index, text_list, level）
- `manage_text` - 统一文本管理（slide_index, operation: add/format/validate/format_runs）
- `manage_image` - 统一图片管理（slide_index, operation: add/enhance, image_source）

### 模板操作（7 工具）
- `list_slide_templates` - 列出可用模板（25+）
- `apply_slide_template` - 应用模板到幻灯片（slide_index, template_name）
- `create_slide_from_template` - 从模板创建幻灯片（template_name, content_data）
- `create_presentation_from_templates` - 从模板序列创建（template_sequence）
- `get_template_info` - 获取模板信息（template_name）
- `auto_generate_presentation` - 自动生成演示文稿（topic, slide_count）
- `optimize_slide_text` - 优化文本可读性（slide_index, auto_sizing）

### 结构元素（4 工具）
- `add_table` - 创建表格（slide_index, rows, columns, data, cell_formatting?）
- `format_table_cell` - 格式化表格单元格
- `add_shape` - 添加形状 20+ 种（slide_index, shape_type, left, top, width, height）
- `add_chart` - 创建图表（slide_index, chart_type: column/bar/line/pie, categories, data_series）

### 专业设计（3 工具）
- `apply_professional_design` - 应用主题（operation: apply_theme/style_slides/enhance, theme_name）
- `apply_picture_effects` - 图片效果（slide_index, shape_index, effects）
- `manage_fonts` - 字体管理（operation: analyze/optimize/recommend）

### 其他（5 工具）
- `manage_hyperlinks` - 超链接管理（operation: add/remove/list/update）
- `manage_slide_masters` - 母版管理
- `add_connector` - 添加连接线
- `update_chart_data` - 更新图表数据
- `manage_slide_transitions` - 幻灯片转场

## 包装层额外功能

通过 `scripts/wrapper.py` 提供，需要时用 `uv run` 执行：

### 格式转换
```bash
# pptx -> PDF
uv run python scripts/wrapper.py convert presentation.pptx -f pdf
# pptx -> Markdown（提取文本内容）
uv run python scripts/wrapper.py convert presentation.pptx -f md
```

### 批量处理
```bash
# 批量读取演示文稿信息
uv run python scripts/wrapper.py batch-read ./presentations/
# 批量提取文本为 Markdown
uv run python scripts/wrapper.py batch-extract ./presentations/ -o ./output/
```

### 模板生成
```bash
# 创建标准报告模板
uv run python scripts/wrapper.py create-template template.pptx -t "项目报告" -n 8
# 基于模板生成演示文稿
uv run python scripts/wrapper.py template template.pptx output.pptx -v author=张三 -v date=2026-03-13
```

### 智能分析
```bash
# 分析结构和统计信息
uv run python scripts/wrapper.py analyze report.pptx
# 提取演讲稿（备注）
uv run python scripts/wrapper.py notes report.pptx
# 生成内容总结
uv run python scripts/wrapper.py summarize report.pptx
```

## 使用指南

1. 优先使用 MCP 工具进行演示文稿创建和编辑
2. 格式转换、批量处理使用包装层 CLI
3. 编辑操作会直接修改文件，注意备份
4. 模板中用 `{{变量名}}` 作为占位符
5. 主题选项：Modern Blue, Corporate Gray, Elegant Green, Warm Red
