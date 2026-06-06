# `.llms.json` 配置格式

## 概述

`.llms.json` 是本插件使用的辅助配置文件，用于存储 llms.txt 的结构化数据，便于增量更新。**不是 llmstxt.org 官方规范的一部分。**

## 完整格式

```json
{
  "project_name": "项目名称",
  "description": "项目简短摘要",
  "details": [
    "项目详细信息第一段",
    "- 重要说明列表项"
  ],
  "sections": {
    "Docs": [
      {
        "title": "文档标题",
        "path": "docs/api.md",
        "description": "文档描述"
      }
    ],
    "Examples": [
      {
        "title": "示例标题",
        "path": "examples/basic.py",
        "description": "示例描述"
      }
    ],
    "Optional": [
      {
        "title": "可选内容",
        "url": "https://example.com/docs",
        "description": "可选描述"
      }
    ]
  }
}
```

## 字段定义

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `project_name` | string | 是 | 项目名称，对应 H1 标题 |
| `description` | string | 否 | 项目摘要，对应引用块 |
| `details` | string[] | 否 | 详细内容段落，每个元素一行 |
| `sections` | object | 否 | H2 分组，键为分组名 |
| `sections.*[].title` | string | 是 | 链接标题 |
| `sections.*[].path` | string | 否* | 本地文件路径（相对根目录） |
| `sections.*[].url` | string | 否* | 远程 URL |
| `sections.*[].description` | string | 否 | 链接描述 |

\* `path` 和 `url` 二选一。

## 链接配置

### 本地文件

```json
{
  "title": "API 文档",
  "path": "docs/api.md",
  "description": "API 参考"
}
```

### 远程 URL

```json
{
  "title": "外部文档",
  "url": "https://example.com/docs",
  "description": "外部资源"
}
```

## 增量更新

修改 `.llms.json` 后请求重新生成：

1. 读取 `.llms.json`
2. 按配置重新组装 `llms.txt`
3. 写入文件

无需重新扫描项目——直接从配置生成。
