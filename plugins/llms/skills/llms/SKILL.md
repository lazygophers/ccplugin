---
name: llms
description: LLMS.txt 文件标准规范 - 遵循 llmstxt.org 定义的格式标准，生成符合规范的 LLM 友好文档
---

# LLMS.txt 标准

## 快速导航

| 文档                                                 | 内容                         | 适用场景      |
| ---------------------------------------------------- | ---------------------------- | ------------- |
| **SKILL.md**                                         | 核心理念、标准格式、验证清单 | 快速入门      |
| [format/file-structure.md](format/file-structure.md) | 文件结构、链接格式、完整示例 | 编写 llms.txt |
| [format/validation.md](format/validation.md)         | 验证规则、错误检查、最佳实践 | 质量保证      |

## 核心理念

LLMS.txt 是为 LLM 优化的项目文档，提供简洁、结构化的信息，帮助 LLM 快速理解项目。

**三个原则**：

1. **简洁优先** - 只包含关键信息，避免冗余
2. **结构清晰** - 使用标准 Markdown 格式，便于解析
3. **LLM 友好** - 提供上下文、链接和分类信息

## 标准格式

### 必需部分

```markdown
# 项目名称
```

### 可选部分

```markdown
> 项目简短摘要

项目详细信息

## Docs

- [文档标题](文档路径): 文档描述

## Examples

- [示例标题](示例路径): 示例描述

## Optional

- [可选内容](URL): 可选描述
```

## 核心约定

### 强制规范

- ✅ H1 标题必须位于文件开头
- ✅ 引用块（blockquote）用于项目摘要
- ✅ H2 部分用于文件列表分组
- ✅ 链接格式：`[name](url): description`
- ✅ Optional 部分用于次要信息

### 推荐做法

- 🔹 使用简洁清晰的语言
- 🔹 为链接提供简要描述
- 🔹 按重要性排序文档
- 🔹 避免使用未解释的术语

## 链接格式

### 本地文件

```markdown
- [API 文档](docs/api.md): API 参考
```

### 远程 URL

```markdown
- [外部文档](https://example.com/docs): 外部资源
```

## 完整示例

```markdown
# FastHTML

> FastHTML is a python library which brings together Starlette, Uvicorn, HTMX, and fastcore's `FT` "FastTags" into a library for creating server-rendered hypermedia applications.

Important notes:

- Although parts of its API are inspired by FastAPI, it is _not_ compatible with FastAPI syntax
- FastHTML is compatible with JS-native web components and any vanilla JS library

## Docs

- [FastHTML quick start](https://fastht.ml/docs/tutorials/quickstart_for_web_devs.html.md): A brief overview of many FastHTML features
- [HTMX reference](https://github.com/bigskysoftware/htmx/blob/master/www/content/reference.md): Brief description of all HTMX attributes

## Examples

- [Todo list application](https://github.com/AnswerDotAI/fasthtml/blob/main/examples/adv_app.py): Detailed walk-thru of a complete CRUD app

## Optional

- [Starlette full documentation](https://gist.githubusercontent.com/.../starlette-sml.md): A subset of the Starlette documentation
```

## 验证清单

- [ ] 包含 H1 标题
- [ ] 引用块位于 H1 之后
- [ ] 详细内容不包含标题
- [ ] H2 部分包含文件列表
- [ ] 链接格式正确
- [ ] Optional 部分仅用于次要信息

## 参考资料

- [LLMS.txt 标准](https://llmstxt.org/)
- [FastHTML 示例](https://fastht.ml/llms.txt)
