# 配置指南

llms.txt 插件的配置选项。

## 配置文件

### .llms.json

```json
{
  "project_name": "项目名称",
  "description": "项目描述",
  "details": ["项目详细信息", "- 重要说明"],
  "sections": {
    "Docs": [
      {
        "title": "README",
        "path": "README.md",
        "description": "项目说明文档"
      }
    ],
    "Examples": [],
    "Optional": []
  }
}
```

## 配置字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `project_name` | string | 项目名称 |
| `description` | string | 项目描述 |
| `details` | array | 详细信息段落 |
| `sections` | object | 文件部分 |

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

## 重新生成

修改 `.llms.json` 后，请求重新生成：

```
根据 .llms.json 配置重新生成 llms.txt
```

## 相关链接

- [llms.txt 标准](https://llmstxt.org/)
- [CCPlugin Market](https://github.com/lazygophers/ccplugin)
