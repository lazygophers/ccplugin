# MCP 工具

Office Docx 插件提供的 MCP 工具。

## 工具列表

| 工具 | 描述 |
|------|------|
| `read_docx` | 读取 Word 文档 |
| `write_docx` | 创建 Word 文档 |
| `add_paragraph` | 添加段落 |
| `get_paragraphs` | 列出段落 |

## read_docx

### 功能

读取 Word 文档内容。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |

### 示例

```python
content = read_docx(file_path="report.docx")
```

## write_docx

### 功能

创建 Word 文档。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `title` | string | 文档标题 |
| `content` | string | 文档内容 |

### 示例

```python
write_docx(
    file_path="output.docx",
    title="报告标题",
    content="报告内容..."
)
```

## add_paragraph

### 功能

添加段落到文档。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `text` | string | 段落文本 |
| `style` | string | 段落样式 |

### 示例

```python
add_paragraph(
    file_path="report.docx",
    text="新段落内容",
    style="Normal"
)
```

## get_paragraphs

### 功能

列出文档中的所有段落。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |

### 示例

```python
paragraphs = get_paragraphs(file_path="report.docx")
```
