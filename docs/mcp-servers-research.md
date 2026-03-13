# MCP Office 服务器调研报告

## 1. GongRzhe/Office-Word-MCP-Server

### 安装配置

```json
{
  "mcpServers": {
    "word": {
      "command": "uvx",
      "args": ["--from", "office-word-mcp-server", "word_mcp_server"]
    }
  }
}
```

### 工具列表 (37+ 工具)

#### 文档创建与属性 (7 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `create_document` | 创建新 Word 文件 | `filename` (str), `title` (str?), `author` (str?) |
| `get_document_info` | 获取文档属性 | `filename` (str) |
| `get_document_text` | 提取所有文本内容 | `filename` (str) |
| `get_document_outline` | 分析文档结构大纲 | `filename` (str) |
| `list_available_documents` | 列出目录中的 Word 文件 | `directory` (str, default=".") |
| `copy_document` | 复制文档 | `source_filename` (str), `destination_filename` (str?) |
| `convert_to_pdf` | 导出为 PDF | `filename` (str), `output_filename` (str?) |

#### 内容添加 - 标题与段落 (3 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_heading` | 插入标题 | `filename`, `text`, `level` (1-9), `font_name?`, `font_size?`, `bold?`, `italic?`, `border_bottom?` |
| `add_paragraph` | 插入段落 | `filename`, `text`, `style?`, `font_name?`, `font_size?`, `bold?`, `italic?`, `color?` |
| `add_page_break` | 插入分页符 | `filename` |

#### 内容添加 - 表格与图片 (2 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_table` | 创建表格 | `filename`, `rows` (int), `cols` (int), `data` (list?) |
| `add_picture` | 嵌入图片 | `filename`, `image_path`, `width` (int?) |

#### 内容添加 - 列表 (1 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `insert_numbered_list_near_text` | 添加有序/无序列表 | `filename`, `target_text?`, `list_items` (list?), `position` ('before'/'after'), `target_paragraph_index?`, `bullet_type` ('bullet'/'number') |

#### 内容插入 - 定位 (2 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `insert_header_near_text` | 在指定位置添加标题 | `filename`, `target_text?`, `header_title?`, `position`, `header_style`, `target_paragraph_index?` |
| `insert_line_or_paragraph_near_text` | 在指定位置添加段落 | `filename`, `target_text?`, `line_text?`, `position`, `line_style?`, `target_paragraph_index?` |

#### 文本提取与搜索 (2 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_paragraph_text_from_document` | 提取指定段落 | `filename`, `paragraph_index` (int) |
| `find_text_in_document` | 查找文本 | `filename`, `text_to_find`, `match_case` (bool), `whole_word` (bool) |

#### 文本格式化 (4 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `format_text` | 应用文本格式 | `filename`, `paragraph_index`, `start_pos`, `end_pos`, `bold?`, `italic?`, `underline?`, `color?`, `font_size?`, `font_name?` |
| `search_and_replace` | 全局查找替换 | `filename`, `find_text`, `replace_text` |
| `delete_paragraph` | 删除段落 | `filename`, `paragraph_index` (int) |
| `create_custom_style` | 创建自定义样式 | `filename`, `style_name`, `bold?`, `italic?`, `font_size?`, `font_name?`, `color?`, `base_style?` |

#### 表格格式化 (12 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `format_table` | 表格级样式 | `filename`, `table_index`, `has_header_row?`, `border_style?`, `shading?` |
| `set_table_cell_shading` | 单元格颜色 | `filename`, `table_index`, `row_index`, `col_index`, `fill_color`, `pattern` |
| `apply_table_alternating_rows` | 交替行颜色 | `filename`, `table_index`, `color1`, `color2` |
| `highlight_table_header` | 表头样式 | `filename`, `table_index`, `header_color`, `text_color` |
| `merge_table_cells` | 合并矩形区域 | `filename`, `table_index`, `start_row`, `start_col`, `end_row`, `end_col` |
| `merge_table_cells_horizontal` | 水平合并 | `filename`, `table_index`, `row_index`, `start_col`, `end_col` |
| `merge_table_cells_vertical` | 垂直合并 | `filename`, `table_index`, `col_index`, `start_row`, `end_row` |
| `set_table_cell_alignment` | 单元格对齐 | `filename`, `table_index`, `row_index`, `col_index`, `horizontal`, `vertical` |
| `set_table_alignment_all` | 整表对齐 | `filename`, `table_index`, `horizontal`, `vertical` |
| `format_table_cell_text` | 单元格文本样式 | `filename`, `table_index`, `row_index`, `col_index`, `text_content?`, `bold?`, `italic?`, etc. |
| `set_table_cell_padding` | 单元格内边距 | `filename`, `table_index`, `row_index`, `col_index`, `top?`, `bottom?`, `left?`, `right?`, `unit` |
| `set_table_column_width` | 列宽设置 | `filename`, `table_index`, `col_index`, `width`, `width_type` |
| `set_table_column_widths` | 批量列宽设置 | `filename`, `table_index`, `widths` (list), `width_type` |
| `set_table_width` | 表格总宽 | `filename`, `table_index`, `width`, `width_type` |
| `auto_fit_table_columns` | 自动调整列宽 | `filename`, `table_index` |

---

## 2. yzfly/mcp-excel-server

### 安装配置

```json
{
  "mcpServers": {
    "excel": {
      "command": "uvx",
      "args": ["mcp-excel-server"]
    }
  }
}
```

### 工具列表 (10 工具)

#### 文件读取 (3 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `read_excel` | 读取 Excel 文件 (XLSX/XLS/CSV/TSV/JSON) | `file_path` (str) |
| `get_excel_info` | 获取文件元数据和结构信息 | `file_path` (str) |
| `get_sheet_names` | 列出所有工作表名 | `file_path` (str) |

#### 数据分析 (4 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `analyze_excel` | 统计分析 (均值、中位数、标准差) | `file_path`, `sheet_name?` |
| `filter_excel` | 条件过滤 | `file_path`, `conditions` (object) |
| `pivot_table` | 创建透视表 | `file_path`, `rows` (array), `columns` (array), `values` (array) |
| `data_summary` | 综合数据摘要 | `file_path`, `sheet_name?` |

#### 可视化 (1 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `export_chart` | 生成图表 (line/bar/scatter/histogram) | `file_path`, `chart_type`, `x_column`, `y_column` |

#### 文件操作 (2 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `write_excel` | 创建新 Excel 文件 | `file_path`, `data` (object), `sheet_name` |
| `update_excel` | 修改现有 Excel 文件 | `file_path`, `updates` (object), `sheet_name` |

---

## 3. GongRzhe/Office-PowerPoint-MCP-Server

### 安装配置

```json
{
  "mcpServers": {
    "ppt": {
      "command": "uvx",
      "args": ["--from", "office-powerpoint-mcp-server", "ppt_mcp_server"]
    }
  }
}
```

### 工具列表 (34 工具，11 模块)

#### 模块 1: 演示文稿管理 (7 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `create_presentation` | 创建新演示文稿 | 无必需参数 |
| `create_presentation_from_template` | 从模板创建 | `template_path` (str) |
| `open_presentation` | 打开 PPTX 文件 | `file_path` (str) |
| `save_presentation` | 保存演示文稿 | `file_path` (str) |
| `get_presentation_info` | 获取演示文稿信息 | 无 |
| `get_template_file_info` | 分析模板文件 | `template_path` (str) |
| `set_core_properties` | 设置文档属性 | `title`, `subject`, `author`, `keywords`, `comments` (all str) |

#### 模块 2: 内容管理 (8 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_slide` | 添加幻灯片 | `layout_name` (str), `background_style?` |
| `get_slide_info` | 获取幻灯片信息 | `slide_index` (int) |
| `extract_slide_text` | 提取幻灯片文本 | `slide_index` (int) |
| `extract_presentation_text` | 提取所有文本 | 无 |
| `populate_placeholder` | 填充占位符 | `slide_index`, `placeholder_name`, `text` |
| `add_bullet_points` | 添加项目符号 | `slide_index`, `text_list` (array), `level` (int) |
| `manage_text` | 统一文本管理 | `slide_index`, `operation` ("add"/"format"/"validate"/"format_runs"), `text?`, `font_size?`, `bold?`, `italic?`, `underline?`, `color?` |
| `manage_image` | 统一图片管理 | `slide_index`, `operation` ("add"/"enhance"), `image_source`, `enhancement_style?`, `brightness?`, `contrast?`, `saturation?` |

#### 模块 3: 模板操作 (7 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `list_slide_templates` | 列出可用模板 | 无 |
| `apply_slide_template` | 应用模板到幻灯片 | `slide_index`, `template_name` |
| `create_slide_from_template` | 从模板创建幻灯片 | `template_name`, `content_data` (dict) |
| `create_presentation_from_templates` | 从模板序列创建 | `template_sequence` (array) |
| `get_template_info` | 获取模板信息 | `template_name` |
| `auto_generate_presentation` | 自动生成演示文稿 | `topic` (str), `slide_count` (int) |
| `optimize_slide_text` | 优化文本可读性 | `slide_index`, `auto_sizing` (bool) |

#### 模块 4: 结构元素 (4 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_table` | 创建表格 | `slide_index`, `rows`, `columns`, `data` (2D array), `cell_formatting?` |
| `format_table_cell` | 格式化表格单元格 | `slide_index`, `table_index`, `row`, `column`, `background_color?`, `text_color?` |
| `add_shape` | 添加形状 (20+ 种) | `slide_index`, `shape_type`, `left`, `top`, `width`, `height`, `text?`, `fill_color?` |
| `add_chart` | 创建图表 | `slide_index`, `chart_type`, `categories`, `data_series`, `title` |

#### 模块 5: 专业设计 (3 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `apply_professional_design` | 应用专业主题 | `operation` ("apply_theme"/"style_slides"/"enhance"), `theme_name`, `slide_indices` |
| `apply_picture_effects` | 应用图片效果 | `slide_index`, `shape_index`, `effects` (dict) |
| `manage_fonts` | 字体管理 | `operation` ("analyze"/"optimize"/"recommend"), `font_family?` |

#### 模块 6-10: 其他模块 (5 工具)

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `manage_hyperlinks` | 超链接管理 | `slide_index`, `operation` ("add"/"remove"/"list"/"update"), `shape_index?`, `url?` |
| `manage_slide_masters` | 母版管理 | `slide_index` |
| `add_connector` | 添加连接线 | `slide_index`, `start_shape_index`, `end_shape_index`, `connector_type` |
| `update_chart_data` | 更新图表数据 | `slide_index`, `chart_index`, `categories`, `data_series` |
| `manage_slide_transitions` | 幻灯片转场 | `slide_index`, `transition_type` |

### 主题选项
- Modern Blue, Corporate Gray, Elegant Green, Warm Red

### 图表类型
- column, bar, line, pie

---

## 4. SylphxAI/pdf-reader-mcp

### 安装配置

```json
{
  "mcpServers": {
    "pdf": {
      "command": "npx",
      "args": ["@sylphx/pdf-reader-mcp"]
    }
  }
}
```

### 工具列表 (1 工具)

#### `read_pdf` - 统一 PDF 读取工具

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `sources` | Array | PDF 文档来源列表 (必需) | - |
| `include_full_text` | Boolean | 提取文本内容 | false |
| `include_metadata` | Boolean | 获取文档属性 | true |
| `include_page_count` | Boolean | 包含总页数 | true |
| `include_images` | Boolean | 获取嵌入图片 | false |

#### Source 对象属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `path` | string? | 本地文件路径 (支持绝对/相对路径) |
| `url` | string? | HTTP/HTTPS 文档 URL |
| `pages` | string/number[]? | 指定页面 (如 "1-5,10" 或 [1,2,3]) |

#### 返回值
- 全文内容 (Y 坐标排序保持布局)
- Base64 编码图片 (含尺寸和格式元数据)
- PDF 元数据 (作者、标题、创建日期等)
- 总页数
- 逐页错误隔离

#### 性能指标
- 文本提取: ~5,575 ops/sec
- 验证: ~12,933 ops/sec
- 支持并发处理多个 PDF (5-10x 性能提升)

---

## 汇总对比

| MCP 服务器 | 工具数 | 安装方式 | 主要能力 |
|-----------|--------|---------|---------|
| Office-Word | 37+ | uvx (office-word-mcp-server) | Word 文档完整 CRUD、格式化、表格操作 |
| mcp-excel-server | 10 | uvx (mcp-excel-server) | Excel 读写、统计分析、图表生成 |
| Office-PowerPoint | 34 | uvx (office-powerpoint-mcp-server) | PPT 创建、模板、图表、专业设计 |
| pdf-reader-mcp | 1 | npx (@sylphx/pdf-reader-mcp) | PDF 读取 (文本/图片/元数据) |
