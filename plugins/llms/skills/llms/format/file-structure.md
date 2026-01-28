# llms.txt 文件结构

## 标准格式

llms.txt 文件必须按顺序包含以下部分：

### 1. H1 标题（必需）

```markdown
# 项目名称
```

- 唯一必需的部分
- 使用项目或网站的正式名称

### 2. 引用块摘要（推荐）

```markdown
> 项目简短摘要，包含关键信息
```

- 提供项目的高层次概述
- 帮助 LLM 快速理解项目目的
- 包含理解项目所需的关键信息

### 3. 详细内容（可选）

零或多个非标题的 Markdown 部分：

```markdown
项目详细信息，可以是：

- 列表项
- 段落说明
- 重要提示
```

- 使用段落、列表等格式
- 不能包含标题（H2-H6）
- 提供补充信息

### 4. H2 部分（可选）

零或多个 H2 标题分隔的文件列表：

```markdown
## Docs

- [文档标题](文档路径): 文档描述
- [API 参考](docs/api.md): API 文档

## Examples

- [示例1](examples/basic.py): 基本用法示例

## Optional

- [扩展文档](https://example.com/docs): 外部文档
```

- 使用 H2 标题创建分组
- 每个分组包含文件列表
- `Optional` 部分有特殊含义

## 链接格式

### 基本格式

```markdown
[名称](URL): 描述
```

- **名称**：链接显示的文本
- **URL**：文件路径或完整 URL
- **描述**（可选）：链接的说明

### 本地文件

```markdown
- [API 文档](docs/api.md): API 参考
- [README](README.md): 项目说明
```

- 使用相对于项目根目录的路径
- 路径区分大小写
- 推荐使用正斜杠 `/`

### 远程 URL

```markdown
- [外部文档](https://example.com/docs): 外部资源
- [GitHub 仓库](https://github.com/user/repo): 源代码
```

- 使用完整的 URL（包含协议）
- 推荐使用 HTTPS
- 确保链接可访问

### 描述规范

- 简洁明了，不超过一句话
- 说明文件内容的用途
- 避免使用技术术语的缩写

## 完整示例

```markdown
# MyProject

> MyProject 是一个高性能的 Python Web 框架，专为构建现代化 API 而设计。

Important notes:

- 使用异步 I/O 以获得最佳性能
- 兼容 Python 3.12+
- 内置类型安全支持

## Docs

- [快速开始](docs/getting-started.md): 5 分钟入门指南
- [API 参考](docs/api.md): 完整的 API 文档
- [配置选项](docs/configuration.md): 所有配置项说明

## Examples

- [Todo 应用](examples/todo_app.py): 完整的 CRUD 应用示例
- [WebSocket 聊天](examples/chat.py): 实时聊天示例

## Optional

- [贡献指南](CONTRIBUTING.md): 如何参与项目贡献
- [更新日志](CHANGELOG.md): 版本历史
```

## Optional 部分的特殊含义

`Optional` 部分包含的内容可以在以下情况跳过：

- LLM 上下文窗口有限
- 需要快速获取核心信息
- 用户请求简洁模式

适合放入 Optional 的内容：

- 贡献指南
- 更新日志
- 扩展阅读
- 非核心文档
