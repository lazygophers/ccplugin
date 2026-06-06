# 文件格式完整规范

来源：<https://llmstxt.org/> — Jeremy Howard (AnswerDotAI), 2024-09-03

## 文件位置

- 主路径：`/llms.txt`（网站根目录）
- 可选：子路径（如 `/docs/llms.txt`）

## 格式结构（严格顺序）

### 1. H1 标题（必需，唯一必需部分）

```markdown
# 项目名称
```

- 必须在文件开头
- 使用项目或网站的正式名称
- 整个文件只有一个 H1

### 2. 引用块摘要（推荐）

```markdown
> 项目简短摘要，包含理解项目所需的关键信息
```

- 标准引用语法 `>`
- 位于 H1 之后
- 包含项目高层次概述

### 3. 详细内容（可选）

零或多个非标题 Markdown 部分：

```markdown
重要说明：

- 列表项
- 段落说明
```

- 可使用段落、列表、代码行内标记等
- **禁止任何标题**（H2-H6 均不可）
- 提供补充信息

### 4. H2 部分（可选，零或多个）

```markdown
## Section name

- [Link title](url): Optional description
```

- H2 标题分隔各资源分组
- 每个分组包含 Markdown 列表
- 每条包含**必需**的超链接 `[name](url)`
- 可选 `: description` 跟在链接后

## 链接格式

### 基本格式

```markdown
- [名称](URL): 描述
```

- **必需**：`- ` 前缀、`[title](url)` 超链接
- **可选**：`: ` + 描述文本
- 解析正则：`-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)(?::\s*(?P<desc>.*))?`

### 本地文件

```markdown
- [API 文档](docs/api.md): API 参考
```

- 相对于项目根目录的路径
- 正斜杠 `/`

### 远程 URL

```markdown
- [外部文档](https://example.com/docs): 外部资源
```

- 完整 URL（含协议）
- 推荐 HTTPS

### `.md` 页面约定

任何对 LLM 有用的页面应在同 URL 追加 `.md` 提供干净 Markdown 版本：
- `https://example.com/docs/tutorial.html` → `https://example.com/docs/tutorial.html.md`
- 无文件名时追加 `index.html.md`

## `## Optional` 的特殊语义

- 短上下文时可**跳过**此部分
- `llms-ctx.txt` **排除**此部分
- `llms-ctx-full.txt` **包含**此部分
- 适合放入：贡献指南、更新日志、扩展阅读、非核心文档

## 与其他标准的关系

| 标准 | 关系 |
|---|---|
| `/robots.txt` | 不同目的。robots.txt 控制访问权限；llms.txt 提供 LLM 推理时内容 |
| `/sitemap.xml` | 互补。sitemap 列举所有页面；llms.txt 提供精选概述 |
