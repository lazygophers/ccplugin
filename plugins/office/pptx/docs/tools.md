# MCP 工具

Office Pptx 插件提供的 MCP 工具。

## 工具列表

| 工具 | 描述 |
|------|------|
| `read_pptx` | 读取 PowerPoint 文件 |
| `write_pptx` | 写入 PowerPoint 文件 |
| `add_slide` | 添加幻灯片 |
| `list_slides` | 列出幻灯片 |

## read_pptx

### 功能

读取 PowerPoint 文件内容。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |

### 示例

```python
content = read_pptx(file_path="presentation.pptx")
```

## write_pptx

### 功能

创建 PowerPoint 文件。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `title` | string | 演示文稿标题 |
| `slides` | array | 幻灯片列表 |

### 示例

```python
write_pptx(
    file_path="output.pptx",
    title="演示标题",
    slides=[
        {"title": "第一页", "content": "内容1"},
        {"title": "第二页", "content": "内容2"}
    ]
)
```

## add_slide

### 功能

添加幻灯片到演示文稿。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `title` | string | 幻灯片标题 |
| `content` | string | 幻灯片内容 |

### 示例

```python
add_slide(
    file_path="presentation.pptx",
    title="新幻灯片",
    content="幻灯片内容"
)
```

## list_slides

### 功能

列出演示文稿中的所有幻灯片。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |

### 示例

```python
slides = list_slides(file_path="presentation.pptx")
```
