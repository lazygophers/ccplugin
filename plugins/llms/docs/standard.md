# 标准规范

llms.txt 文件的标准规范。

## 文件格式

```markdown
# 项目名称

> 项目简短摘要

项目详细信息

## Docs

- [README](README.md): 项目说明文档
- [API 文档](docs/api.md): API 参考

## Examples

- [示例1](examples/example1.py): 基本用法

## Optional

- [扩展文档](https://example.com/docs.md): 外部文档
```

## 格式说明

| 部分 | 必需 | 说明 |
|------|------|------|
| H1 标题 | ✅ | 项目/网站名称 |
| 引用块 | ❌ | 项目摘要 |
| 详细内容 | ❌ | 段落、列表等（不含标题） |
| H2 部分 | ❌ | 文件列表 |
| Optional | ❌ | 可在短上下文时跳过 |

## 链接格式

### 本地文件

```markdown
- [API 文档](docs/api.md): API 参考
```

### 远程 URL

```markdown
- [外部文档](https://example.com/docs): 外部资源
```

## 部分说明

### Docs 部分

必需文档，包含核心文档链接。

```markdown
## Docs

- [README](README.md): 项目说明
- [Installation](docs/install.md): 安装指南
- [Usage](docs/usage.md): 使用说明
```

### Examples 部分

示例代码链接。

```markdown
## Examples

- [Basic](examples/basic.py): 基本用法
- [Advanced](examples/advanced.py): 高级用法
```

### Optional 部分

可选内容，短上下文时可跳过。

```markdown
## Optional

- [Changelog](CHANGELOG.md): 变更日志
- [Contributing](CONTRIBUTING.md): 贡献指南
```

## 最佳实践

1. **保持简洁**：摘要不超过 100 字
2. **优先级排序**：重要文件放前面
3. **清晰描述**：每个链接都有简短描述
4. **定期更新**：保持文件列表最新
