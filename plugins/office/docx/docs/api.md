# API 文档

## MCP 工具

通过 office-word-mcp-server 提供 37+ 工具，完整覆盖 Word 文档 CRUD。

### 文档管理（7 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `create_document` | 创建新文档 | `filename` (str), `title?`, `author?` |
| `get_document_info` | 获取文档属性 | `filename` (str) |
| `get_document_text` | 提取所有文本 | `filename` (str) |
| `get_document_outline` | 分析文档大纲 | `filename` (str) |
| `list_available_documents` | 列出目录中的 Word 文件 | `directory` (str, default=".") |
| `copy_document` | 复制文档 | `source_filename`, `destination_filename?` |
| `convert_to_pdf` | 导出 PDF | `filename`, `output_filename?` |

### 内容添加（6 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_heading` | 插入标题 | `filename`, `text`, `level` (1-9), `font_name?`, `font_size?`, `bold?`, `italic?` |
| `add_paragraph` | 插入段落 | `filename`, `text`, `style?`, `font_name?`, `font_size?`, `bold?`, `italic?`, `color?` |
| `add_page_break` | 插入分页符 | `filename` |
| `add_table` | 创建表格 | `filename`, `rows`, `cols`, `data?` (list) |
| `add_picture` | 插入图片 | `filename`, `image_path`, `width?` (int) |
| `insert_numbered_list_near_text` | 添加列表 | `filename`, `target_text?`, `list_items?`, `position`, `bullet_type` |

### 定位插入（2 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `insert_header_near_text` | 在指定位置插入标题 | `filename`, `target_text?`, `header_title?`, `position`, `header_style`, `target_paragraph_index?` |
| `insert_line_or_paragraph_near_text` | 在指定位置插入段落 | `filename`, `target_text?`, `line_text?`, `position`, `line_style?`, `target_paragraph_index?` |

### 搜索和文本操作（4 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_paragraph_text_from_document` | 提取指定段落 | `filename`, `paragraph_index` (int) |
| `find_text_in_document` | 查找文本 | `filename`, `text_to_find`, `match_case`, `whole_word` |
| `search_and_replace` | 全局替换 | `filename`, `find_text`, `replace_text` |
| `delete_paragraph` | 删除段落 | `filename`, `paragraph_index` (int) |

### 格式化（2 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `format_text` | 文本格式 | `filename`, `paragraph_index`, `start_pos`, `end_pos`, `bold?`, `italic?`, `underline?`, `color?`, `font_size?`, `font_name?` |
| `create_custom_style` | 创建自定义样式 | `filename`, `style_name`, `bold?`, `italic?`, `font_size?`, `font_name?`, `color?`, `base_style?` |

### 表格格式化（12+ 工具）

| 工具名 | 描述 |
|--------|------|
| `format_table` | 表格级样式（header_row, border_style, shading） |
| `set_table_cell_shading` | 单元格背景颜色 |
| `apply_table_alternating_rows` | 交替行颜色 |
| `highlight_table_header` | 表头高亮样式 |
| `merge_table_cells` | 合并矩形区域 |
| `merge_table_cells_horizontal` | 水平合并 |
| `merge_table_cells_vertical` | 垂直合并 |
| `set_table_cell_alignment` | 单元格对齐 |
| `set_table_alignment_all` | 整表对齐 |
| `format_table_cell_text` | 单元格文本样式 |
| `set_table_cell_padding` | 单元格内边距 |
| `set_table_column_width` / `set_table_column_widths` | 列宽设置 |
| `set_table_width` | 表格总宽 |
| `auto_fit_table_columns` | 自动调整列宽 |

---

## 包装层 API

通过 `scripts/wrapper.py` 提供，使用 `uv run python scripts/wrapper.py <command>` 调用。

### convert - 格式转换

```bash
uv run python scripts/wrapper.py convert <input_path> -f <format> [-o <output_path>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `input_path` | str | 是 | 输入文件路径 |
| `-f/--format` | md/pdf/docx | 是 | 目标格式 |
| `-o/--output` | str | 否 | 输出路径（默认同名不同后缀） |

支持转换路径：
- docx -> md (Markdown)
- docx -> pdf
- md -> docx

返回 JSON：`{"output": "<输出文件路径>"}`

### batch-read - 批量读取

```bash
uv run python scripts/wrapper.py batch-read <directory> [-p <pattern>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `directory` | str | 是 | 目标目录 |
| `-p/--pattern` | str | 否 | 匹配模式（默认 *.docx） |

返回 JSON 数组，每项包含：
- `path` - 文件路径
- `filename` - 文件名
- `paragraphs` - 段落数
- `tables` - 表格数
- `title` - 文档标题
- `author` - 作者

### batch-convert - 批量转换

```bash
uv run python scripts/wrapper.py batch-convert <directory> -f <format> [-o <output_dir>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `directory` | str | 是 | 源文件目录 |
| `-f/--format` | md/pdf | 否 | 目标格式（默认 md） |
| `-o/--output-dir` | str | 否 | 输出目录（默认同目录） |

返回 JSON 数组，每项包含 `source`、`output`、`status`。

### template - 模板生成

```bash
uv run python scripts/wrapper.py template <template_path> <output_path> [-v key=value ...]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `template_path` | str | 是 | 模板文件路径 |
| `output_path` | str | 是 | 输出文件路径 |
| `-v/--var` | str | 否 | 变量替换（可多次使用） |

模板中使用 `{{变量名}}` 占位符。返回 JSON：`{"output": "<输出路径>"}`

### create-template - 创建报告模板

```bash
uv run python scripts/wrapper.py create-template <output_path> [-t <title>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `output_path` | str | 是 | 输出路径 |
| `-t/--title` | str | 否 | 报告标题（默认"报告模板"） |

创建包含 `{{author}}`、`{{date}}`、`{{summary}}`、`{{content}}`、`{{conclusion}}` 占位符的标准报告模板。

### analyze - 文档分析

```bash
uv run python scripts/wrapper.py analyze <file_path>
```

返回 JSON，包含：
- `properties` - 文档属性（标题、作者、创建时间等）
- `statistics` - 统计信息（段落数、字符数、词数、标题数、表格数）
- `outline` - 标题大纲结构
- `tables` - 表格信息（行列数）
- `summary` - 内容摘要（前 3 段正文）

### extract - 关键信息提取

```bash
uv run python scripts/wrapper.py extract <file_path>
```

返回 JSON，包含：
- `headings` - 所有标题文本
- `tables` - 所有表格数据（二维数组）
- `list_items` - 列表项
- `bold_texts` - 粗体文本

## 配置

MCP 服务在 plugin.json 中配置：

```json
{
  "mcpServers": {
    "office-word": {
      "command": "uvx",
      "args": ["--from", "office-word-mcp-server", "word_mcp_server"]
    }
  }
}
```
