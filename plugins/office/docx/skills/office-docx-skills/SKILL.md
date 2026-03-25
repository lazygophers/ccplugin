---
description: Word docx 文件操作技能 - 读写文档、格式转换(docx/md/pdf)、批量处理、模板生成、智能分析
triggers:
  - word
  - docx
  - document
  - 文档
  - 段落
  - 表格
  - 转换
  - 模板
---

# Word docx 操作技能

通过 MCP 工具 + 包装层操作 Word 文件。

## MCP 基础工具（37+ 工具）

通过 `office-word` MCP 服务提供，覆盖 Word 文档完整 CRUD：

### 文档管理
- `create_document` - 创建新文档（filename, title?, author?）
- `get_document_info` / `get_document_text` / `get_document_outline` - 读取文档
- `copy_document` / `convert_to_pdf` - 复制和导出
- `list_available_documents` - 列出目录中的 Word 文件

### 内容编辑
- `add_heading` - 添加标题（level 1-9，支持字体/粗体/斜体设置）
- `add_paragraph` - 添加段落（支持样式和格式设置）
- `add_page_break` - 插入分页符
- `add_table` - 创建表格（rows, cols, data）
- `add_picture` - 插入图片（image_path, width?）
- `insert_numbered_list_near_text` - 添加有序/无序列表

### 定位插入
- `insert_header_near_text` - 在指定位置插入标题
- `insert_line_or_paragraph_near_text` - 在指定位置插入段落

### 搜索和替换
- `find_text_in_document` - 查找文本
- `search_and_replace` - 全局替换
- `get_paragraph_text_from_document` - 提取指定段落

### 格式化
- `format_text` - 文本格式（粗体/斜体/下划线/颜色/字号）
- `delete_paragraph` - 删除段落
- `create_custom_style` - 创建自定义样式

### 表格格式化（12 工具）
- `format_table` / `set_table_cell_shading` / `apply_table_alternating_rows`
- `highlight_table_header` / `merge_table_cells` / `set_table_cell_alignment`
- `set_table_column_width` / `set_table_width` / `auto_fit_table_columns` 等

## 包装层额外功能

通过 `scripts/wrapper.py` 提供，需要时用 `uv run` 执行：

### 格式转换
```bash
# docx -> markdown
uv run python scripts/wrapper.py convert input.docx -f md
# docx -> pdf
uv run python scripts/wrapper.py convert input.docx -f pdf
# markdown -> docx
uv run python scripts/wrapper.py convert input.md -f docx
```

### 批量处理
```bash
# 批量读取文档信息
uv run python scripts/wrapper.py batch-read ./docs/
# 批量转换为 markdown
uv run python scripts/wrapper.py batch-convert ./docs/ -f md -o ./output/
```

### 模板生成
```bash
# 创建标准报告模板
uv run python scripts/wrapper.py create-template template.docx -t "项目报告"
# 基于模板生成文档
uv run python scripts/wrapper.py template template.docx report.docx -v author=张三 -v date=2026-03-13
```

### 智能分析
```bash
# 分析文档结构和统计信息
uv run python scripts/wrapper.py analyze report.docx
# 提取关键信息（标题/表格/列表/粗体文本）
uv run python scripts/wrapper.py extract report.docx
```

## 使用指南

1. 优先使用 MCP 工具进行文档创建和编辑操作
2. 格式转换、批量处理使用包装层 CLI
3. 编辑操作会直接修改文件，注意备份
4. 模板中用 `{{变量名}}` 作为占位符
