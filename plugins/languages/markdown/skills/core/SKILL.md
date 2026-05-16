---
name: markdown-core
description: |
  Markdown 核心规范，覆盖 CommonMark 0.31.2 与 GitHub Flavored Markdown（GFM）扩展、
  文档结构、标题层级、列表、链接、图片、代码块、表格、front matter（YAML/TOML）、
  MDX 3、可访问性、技术文档模式（README / CHANGELOG / ADR / API 文档）。
  编写、审查、格式化或重构任何 .md / .mdx 文件时加载。也响应 "Markdown 规范",
  "CommonMark", "GFM", "front matter", "README", "CHANGELOG", "ADR", "技术文档",
  "markdownlint", "remark", "MDX", "Docusaurus", "VitePress", "Astro Starlight",
  "Nextra", "task list", "脚注", "目录 TOC"。
---

# Markdown 核心规范

CommonMark 0.31.2（2024 定稿）+ GitHub Flavored Markdown（GFM）为强制基线，MDX 3
为可选超集。所有 `.md` / `.mdx` 文件遵循本文，专题图表参见 `markdown-mermaid`。

## 与其它 skill 的关系

| 主题 | 跳转 |
|------|------|
| 流程图 / 序列图 / 类图 / ER 图 / 状态图 / 甘特图 | `markdown-mermaid` |
| 文件名 / 标题命名 | `naming-core` |

## 强制约定

1. 文件以 **UTF-8（无 BOM）** 编码，LF 行尾，末尾保留单个换行。
2. 单文件 ≤ 500 行，推荐 200–400 行；超出按章节拆分并互链。
3. 行宽建议 ≤ 120 列；散文段落允许软换行，硬换行用行尾两空格或 `\`（GFM）。
4. 每文件 **仅一个 H1**，标题层级连续递进（H1→H2→H3），禁跳级。
5. ATX 风格标题（`#`），禁 Setext（`===` / `---`）。
6. 代码块全部用 fenced（```` ``` ````），并标注语言（无语言用 `text`）。
7. 链接文字必须描述目标内容，禁 "点击这里" / "这里" / 裸 URL（裸 URL 用
   `<https://example.com>` 自动链接）。
8. 所有非装饰图片必须含 `alt` 文本；装饰图用空 alt `![](...)`。
9. 表格必须有表头行与对齐声明，单元格内换行用 `<br>`。
10. 元素之间空一行；列表与代码块前后空行；嵌套列表用 2 空格缩进（CommonMark）。
11. front matter 用 YAML（`---` 包裹）或 TOML（`+++` 包裹），键名 `snake_case`，
    保留字段：`title`、`description`、`date`（ISO 8601）、`tags`、`draft`。
12. 禁内联 HTML 除非必需（如 `<details>`、`<sub>`、`<kbd>`、`<br>`），且不依赖 CSS。
13. 提交前用 `markdownlint-cli2` 与 `remark-cli` 校验，配置见仓库根
    `.markdownlint.jsonc` / `.remarkrc`。

## 文档骨架

```markdown
---
title: 标题
description: 一句话摘要（≤ 160 字符，用于 SEO 与列表卡片）
date: 2026-05-16
tags: [markdown, guide]
---

# 文档标题

> 一句话定位：本文回答什么问题、读者是谁。

## 背景 / Why

## 内容 / What

## 操作 / How

## 参考

- [CommonMark Spec 0.31.2](https://spec.commonmark.org/0.31.2/)
```

## CommonMark 0.31.2 基线

| 元素 | 规范语法 | 备注 |
|------|---------|------|
| 标题 | `# H1` … `###### H6` | ATX，`#` 后一空格 |
| 强调 | `*em*` `**strong**` `***both***` | 单字符两边无空格 |
| 行内代码 | `` `code` `` | 含反引号时用双反引号 |
| 代码块 | ```` ```lang ```` | 必须语言标记 |
| 引用 | `> text` | 嵌套用 `> >` |
| 无序列表 | `- item` | 全文统一 `-`，禁混用 `*` / `+` |
| 有序列表 | `1. item` | 后续项可全写 `1.` 让工具自增 |
| 链接 | `[text](url "title")` | title 可选；引用式 `[text][id]` |
| 图片 | `![alt](url "title")` | alt 必填 |
| 自动链接 | `<https://x>` `<a@b>` | 仅 URI / 邮箱 |
| 水平线 | `---` | 前后空行 |
| 硬换行 | 行尾两空格 或 `\` | 禁裸 `<br>` |

## GFM 扩展（GitHub / GitLab / 多数静态站）

| 元素 | 语法 | 用途 |
|------|------|------|
| 删除线 | `~~text~~` | 标注废弃 |
| 表格 | `\| h \| h \|` + `\| --- \|` | 必须含表头与对齐行 |
| 任务列表 | `- [ ] todo` / `- [x] done` | 可勾选 checklist |
| 脚注 | `text[^1]` + `[^1]: note` | 引用与注释 |
| 自动链接（裸 URL）| `https://x.com` | GFM 自动识别 |
| 围栏代码块语言 | ```` ```mermaid ```` 等 | 渲染图表 / 数学 |
| 警告块（GitHub Alerts）| `> [!NOTE]` `[!TIP]` `[!IMPORTANT]` `[!WARNING]` `[!CAUTION]` | 平台原生提示框 |
| 表情 | `:smile:` | GitHub / GitLab 渲染 |

### 表格对齐

```markdown
| 左   | 居中 | 右   |
| :--- | :--: | ---: |
| a    | b    | c    |
```

### GitHub Alerts

```markdown
> [!NOTE]
> 一般性提示。

> [!WARNING]
> 用户需注意的副作用。
```

## 代码块约定

1. 必须标注语言（`text` / `plain` 也算），无语言会触发 lint 警告。
2. 长示例放支持文件并 `[link](./examples/foo.py)` 引用，禁贴 > 50 行。
3. 命令行用 `bash` / `sh` / `zsh` / `powershell`；输出用 `text` 并以 `$ ` 区分。
4. JSON / YAML 示例必须可解析；示意配置加 `# ...` 注释。
5. 复杂语法对照表用语言 `text` 或表格，禁 ASCII 框线模拟。

````markdown
```python
def hello(name: str) -> None:
    print(f"hello, {name}")
```
````

## 链接与锚点

- 站内链接用相对路径：`[规范](../spec/style.md)`。
- 跨仓库 / 公网用完整 https URL，禁 http（除非协议要求）。
- 自动锚点：GitHub 将标题小写、空格转 `-`、去标点；中文保留原字。
- 引用式链接集中在文末便于维护：

  ```markdown
  详见 [CommonMark][cm] 与 [GFM][gfm]。

  [cm]: https://spec.commonmark.org/0.31.2/
  [gfm]: https://github.github.com/gfm/
  ```

## 图片与媒体

```markdown
![架构总览：客户端 → API → 数据库](./images/arch.png)
```

- alt 描述信息内容而非外观；装饰性图片用空 alt。
- 优先使用 SVG / WebP；位图给定宽高避免布局抖动（必要时用 HTML `<img>`）。
- 暗色主题适配：GitHub 支持 `#gh-dark-mode-only` / `#gh-light-mode-only` URL 片段。

## Front Matter

YAML（最常用，Hugo / Jekyll / Astro / Docusaurus 兼容）：

```yaml
---
title: "Markdown 规范"
description: "CommonMark 0.31 + GFM 编写约定"
date: 2026-05-16
updated: 2026-05-16
tags: [docs, markdown]
authors: [lazygophers]
draft: false
---
```

TOML（Hugo 默认之一，`+++` 包裹）；JSON（部分静态站，`{ ... }` 包裹）次选。

## 可访问性（a11y）

1. 图片 alt 描述信息内容；装饰图用空 alt 让屏幕阅读器跳过。
2. 链接文字独立可理解，禁 "[这里](...)" / 重复 "更多"。
3. 表格仅用于二维数据，禁用作布局；表头明确。
4. 标题层级连续表达大纲，不为视觉跳级。
5. 颜色 / emoji 不是唯一信息载体；提示框配合 `[!NOTE]` 文本。
6. 数学公式同时提供 alt 或文字说明（MathJax/KaTeX 渲染前）。

## 技术文档模式

### README

```markdown
# 项目名

> 一句话价值主张。

[![CI](badge)](url) [![License](badge)](url)

## 特性
## 安装
## 快速开始
## 文档
## 路线图
## 贡献
## 许可证
```

### CHANGELOG（Keep a Changelog 1.1 + SemVer 2.0）

```markdown
# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)
与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.2.0] - 2026-05-16

### Added
- 支持 MDX 3 渲染。
```

### ADR（Architecture Decision Record，MADR 4 模板）

```markdown
# ADR-0007: 采用 Vitest 替代 Jest

- 状态: Accepted
- 日期: 2026-05-16
- 决策者: @alice, @bob

## 背景

## 决策

## 后果

## 候选方案
```

### API 文档

- 端点用 `METHOD /path` 作 H3 标题。
- 表格列出参数：`name | in | type | required | description`。
- 请求 / 响应示例用 fenced JSON 块。
- 错误码集中表格列出。

## MDX 3（可选）

- 文件后缀 `.mdx`；front matter 与 `.md` 一致。
- 可导入组件：`import Chart from '@/components/Chart.astro'`。
- JSX 必须闭合，HTML void 标签写 `<br />`、`<img />`。
- 表达式 `{value}` 不在代码块内才解析；代码块内安全。
- 与 CommonMark 不同：缩进段落不再变成段落，必须空行分隔。

## 文档站映射

| 平台 | 版本 | 特色字段 / 用法 |
|------|------|----------------|
| Docusaurus | 3.x | `slug`, `sidebar_position`, admonition `:::note` |
| VitePress | 1.x | `outline`, `aside`, container `::: tip` |
| Astro Starlight | 0.x | `sidebar.order`, `hero`, `<Card>` 组件 |
| Nextra | 3.x | `_meta.json`，MDX 优先 |
| Hugo | 0.x | TOML/YAML/JSON front matter，shortcode `{{< note >}}` |
| Jekyll / GitHub Pages | 4.x | `layout`, `permalink`, Liquid 标签 |
| Obsidian | 1.x | `[[wikilink]]`、`#tag`、`%%comment%%`（非 CommonMark，仓库内可用） |
| Notion 导出 | — | 表格 / toggle 用 HTML，需 remark 清洗后再提交 |

## 工具链

| 工具 | 用途 |
|------|------|
| `markdownlint-cli2` | 30+ 风格规则强制（MD001 标题层级、MD040 代码语言等） |
| `remark-cli` + `remark-preset-lint-recommended` | AST 校验、自动修复、插件生态 |
| `rehype` | Markdown → HTML AST 后处理（高亮、目录） |
| `prettier --parser markdown` | 行宽、列表缩进、表格对齐统一格式化 |
| `lychee` | 死链批量检查 |
| `vale` | 散文风格 / 术语 / 拼写校验 |
| `pandoc` | 跨格式转换（md ↔ docx/pdf/tex） |

## 检查清单

- [ ] UTF-8（无 BOM）、LF、末尾换行
- [ ] 仅一个 H1，层级连续
- [ ] 所有代码块标注语言
- [ ] 链接文字描述目标，无 "点击这里"
- [ ] 图片有 alt（装饰图除外）
- [ ] 表格有表头与对齐行
- [ ] front matter 字段齐全且 YAML 合法
- [ ] 行宽 ≤ 120，文件 ≤ 500 行
- [ ] 内联 HTML 仅限必要标签
- [ ] `markdownlint-cli2` 与 `remark` 通过

## 参考

- [CommonMark Spec 0.31.2](https://spec.commonmark.org/0.31.2/)
- [GitHub Flavored Markdown Spec](https://github.github.com/gfm/)
- [MDX 3 Documentation](https://mdxjs.com/)
- [Keep a Changelog 1.1](https://keepachangelog.com/zh-CN/1.1.0/)
- [Semantic Versioning 2.0](https://semver.org/lang/zh-CN/)
- [markdownlint Rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [remark Plugin Ecosystem](https://github.com/remarkjs/remark)
- [Pandoc User's Guide](https://pandoc.org/MANUAL.html)
- [GitHub Alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts)
- [MADR Architecture Decision Records](https://adr.github.io/madr/)
