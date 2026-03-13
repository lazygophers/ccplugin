# API 文档

## MCP 工具

通过 office-powerpoint-mcp-server 提供 34 工具，覆盖 PowerPoint 操作全流程。

### 演示文稿管理（7 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `create_presentation` | 创建新演示文稿 | 无必需参数 |
| `create_presentation_from_template` | 从模板创建 | `template_path` (str) |
| `open_presentation` | 打开 PPTX 文件 | `file_path` (str) |
| `save_presentation` | 保存演示文稿 | `file_path` (str) |
| `get_presentation_info` | 获取演示文稿信息 | 无 |
| `get_template_file_info` | 分析模板文件 | `template_path` (str) |
| `set_core_properties` | 设置文档属性 | `title`, `subject`, `author`, `keywords`, `comments` (all str) |

### 内容管理（8 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_slide` | 添加幻灯片 | `layout_name` (str), `background_style?` |
| `get_slide_info` | 获取幻灯片信息 | `slide_index` (int) |
| `extract_slide_text` | 提取幻灯片文本 | `slide_index` (int) |
| `extract_presentation_text` | 提取所有文本 | 无 |
| `populate_placeholder` | 填充占位符 | `slide_index`, `placeholder_name`, `text` |
| `add_bullet_points` | 添加项目符号 | `slide_index`, `text_list` (array), `level` (int) |
| `manage_text` | 统一文本管理 | `slide_index`, `operation` (add/format/validate/format_runs), `text?`, `font_size?`, `bold?`, `italic?`, `underline?`, `color?` |
| `manage_image` | 统一图片管理 | `slide_index`, `operation` (add/enhance), `image_source`, `enhancement_style?`, `brightness?`, `contrast?`, `saturation?` |

### 模板操作（7 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `list_slide_templates` | 列出可用模板（25+） | 无 |
| `apply_slide_template` | 应用模板到幻灯片 | `slide_index`, `template_name` |
| `create_slide_from_template` | 从模板创建幻灯片 | `template_name`, `content_data` (dict) |
| `create_presentation_from_templates` | 从模板序列创建 | `template_sequence` (array) |
| `get_template_info` | 获取模板信息 | `template_name` |
| `auto_generate_presentation` | 自动生成演示文稿 | `topic` (str), `slide_count` (int) |
| `optimize_slide_text` | 优化文本可读性 | `slide_index`, `auto_sizing` (bool) |

### 结构元素（4 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `add_table` | 创建表格 | `slide_index`, `rows`, `columns`, `data` (2D array), `cell_formatting?` |
| `format_table_cell` | 格式化表格单元格 | `slide_index`, `table_index`, `row`, `column`, `background_color?`, `text_color?` |
| `add_shape` | 添加形状（20+ 种） | `slide_index`, `shape_type`, `left`, `top`, `width`, `height`, `text?`, `fill_color?` |
| `add_chart` | 创建图表 | `slide_index`, `chart_type` (column/bar/line/pie), `categories`, `data_series`, `title` |

### 专业设计（3 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `apply_professional_design` | 应用专业主题 | `operation` (apply_theme/style_slides/enhance), `theme_name`, `slide_indices` |
| `apply_picture_effects` | 应用图片效果 | `slide_index`, `shape_index`, `effects` (dict) |
| `manage_fonts` | 字体管理 | `operation` (analyze/optimize/recommend), `font_family?` |

### 其他功能（5 工具）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `manage_hyperlinks` | 超链接管理 | `slide_index`, `operation` (add/remove/list/update), `shape_index?`, `url?` |
| `manage_slide_masters` | 母版管理 | `slide_index` |
| `add_connector` | 添加连接线 | `slide_index`, `start_shape_index`, `end_shape_index`, `connector_type` |
| `update_chart_data` | 更新图表数据 | `slide_index`, `chart_index`, `categories`, `data_series` |
| `manage_slide_transitions` | 幻灯片转场 | `slide_index`, `transition_type` |

### 主题选项

- Modern Blue, Corporate Gray, Elegant Green, Warm Red

### 图表类型

- column, bar, line, pie

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
| `-f/--format` | pdf/md | 是 | 目标格式 |
| `-o/--output` | str | 否 | 输出路径（默认同名不同后缀） |

支持转换路径：
- pptx -> pdf
- pptx -> md (提取文本内容为 Markdown)

返回 JSON：`{"output": "<输出文件路径>"}`

### batch-read - 批量读取

```bash
uv run python scripts/wrapper.py batch-read <directory> [-p <pattern>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `directory` | str | 是 | 目标目录 |
| `-p/--pattern` | str | 否 | 匹配模式（默认 *.pptx） |

返回 JSON 数组，每项包含：
- `path` - 文件路径
- `filename` - 文件名
- `slides` - 幻灯片数
- `total_shapes` - 形状总数
- `total_text_chars` - 文本字符总数

### batch-extract - 批量提取文本

```bash
uv run python scripts/wrapper.py batch-extract <directory> [-o <output_dir>] [-p <pattern>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `directory` | str | 是 | 源文件目录 |
| `-o/--output-dir` | str | 否 | 输出目录（默认同目录） |
| `-p/--pattern` | str | 否 | 匹配模式（默认 *.pptx） |

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
uv run python scripts/wrapper.py create-template <output_path> [-t <title>] [-n <slides>]
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `output_path` | str | 是 | 输出路径 |
| `-t/--title` | str | 否 | 报告标题（默认"报告模板"） |
| `-n/--slides` | int | 否 | 幻灯片数量（默认 5，最少 3） |

创建包含标题页、目录页、内容页、结论页的标准报告模板，带 `{{变量名}}` 占位符。

### analyze - 演示文稿分析

```bash
uv run python scripts/wrapper.py analyze <file_path>
```

返回 JSON，包含：
- `properties` - 文档属性（标题、作者、创建时间等）
- `statistics` - 统计信息（幻灯片数、形状数、表格数、图片数、文本字符数）
- `slide_dimensions` - 幻灯片尺寸
- `slides` - 每张幻灯片的详细信息

### notes - 提取演讲稿

```bash
uv run python scripts/wrapper.py notes <file_path>
```

返回 JSON 数组，每项包含：
- `slide_index` - 幻灯片序号
- `has_notes` - 是否有备注
- `notes` - 备注文本

### summarize - 内容总结

```bash
uv run python scripts/wrapper.py summarize <file_path>
```

返回 JSON，包含：
- `total_slides` - 幻灯片总数
- `total_characters` - 文本字符总数
- `outline` - 每张幻灯片的标题和关键要点

## 配置

MCP 服务在 plugin.json 中配置：

```json
{
  "mcpServers": {
    "powerpoint": {
      "command": "uvx",
      "args": ["--from", "office-powerpoint-mcp-server", "ppt_mcp_server"]
    }
  }
}
```
