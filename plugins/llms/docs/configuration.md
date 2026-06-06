# 配置指南

## .llms.json

辅助配置文件，存储 llms.txt 结构化数据。完整字段定义见 `skills/llms-generate/references/config.md`。

```json
{
  "project_name": "项目名称",
  "description": "项目描述",
  "details": ["项目详细信息"],
  "sections": {
    "Docs": [{ "title": "README", "path": "README.md", "description": "项目说明" }],
    "Examples": [],
    "Optional": []
  }
}
```

修改后请求重新生成即可增量更新，无需重新扫描项目。
