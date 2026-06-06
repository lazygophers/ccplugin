# 工具与集成

## 官方工具

### llms-txt（Python）

```bash
pip install llms-txt
```

| 用途 | 命令/API |
|---|---|
| CLI 帮助 | `llms_txt2ctx -h` |
| 生成上下文 | `llms_txt2ctx llms.txt > llms.md` |
| 含 Optional | `llms_txt2ctx llms.txt --optional True > llms.md` |
| Python 解析 | `from llms_txt import parse_llms_file, create_ctx` |

### JavaScript 实现

浏览器端解析器：<https://llmstxt.org/llmstxt-js.html>

### llms-txt-php

PHP 库用于读写 llms.txt Markdown 文件。

## 框架插件

| 插件 | 框架 | 功能 |
|---|---|---|
| `vitepress-plugin-llms` | VitePress | 自动生成 LLM 友好文档 |
| `docusaurus-plugin-llms` | Docusaurus | 自动生成 LLM 友好文档 |
| Drupal LLM Support | Drupal 10.3+ | LLM 文档支持 |

## 编辑器集成

| 工具 | 功能 |
|---|---|
| VS Code PagePilot | Chat participant 加载 llms.txt 上下文 |

## 目录服务

| 服务 | 地址 |
|---|---|
| llmstxt.site | 列出可用的 llms.txt 文件 |
| directory.llmstxt.cloud | llms.txt 文件目录 |

## 生态扩展

### llm-docs.com

文档库站（非规范站），提供 881 个库的 LLM 优化文档，按四种类型组织：

- **CORE**：精简版
- **FULL**：完整版
- **MINIFIED**：压缩版
- **SLIM**：最小版

### llms-full.txt（社区约定）

`llms-full.txt` 是社区涌现的约定：将所有文档内容合并到一个 Markdown 文件中。非 llmstxt.org 官方定义。

## 与其他标准的区别

| 标准 | 目的 | 格式 |
|---|---|---|
| `llms.txt` | LLM 推理时上下文 | Markdown 索引 |
| `robots.txt` | 爬虫访问控制 | 纯文本规则 |
| `sitemap.xml` | 搜索引擎页面索引 | XML |
| `.well-known/ai-plugin.json` | ChatGPT 插件描述（无关标准） | JSON |
