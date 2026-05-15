---
name: cortex-ingest
description: 外部源 (文件/URL/目录) 摄取进 vault — 抽实体, 套模板 (cli=manual), wikilink 回填; URL 走 defuddle。Triggers on "ingest", "摄取".
allowed-tools: Bash Read Write Edit Glob WebFetch mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content mcp__obsidian__obsidian_simple_search
---

# cortex-ingest

把外部内容 (本地文件 / 网页 / 目录批量) 转成结构化 知识库 页面写入 Obsidian vault。

## 触发场景

- 用户给 URL "ingest this" / "把这篇文章存到知识库"
- 用户给本地 md/pdf/txt 路径 "process this source"
- `/cortex:ingest` 显式调用 (slash, 无入参; AI 从 prompt 推 path/url/dir)
- Web Clipper 输出目录批量摄取

## 调用决策树

```
源类型 ─┬─ URL (https?://)   → ingest_url.sh (CLI 主路径)
        ├─ 本地文件 (md/pdf/epub/docx/txt) → ingest_file.sh
        ├─ git repo (github/gitlab/本地)   → ingest_remote.sh (4 层目录硬契约)
        └─ 目录批量 → Glob 收集 → 单文件循环

CLI 不可用 fallback: WebFetch + defuddle + 手工调三过滤器
  → P0 三过滤器 (url_security → html_sanitize → masking) 顺序严格, 任一拒绝即终止
```

## AUTO_MODE 分支 (D10)

`/cortex:ingest auto` (wrapper / cron 触发): 跳所有 `AskUserQuestion`, 自动判源类型 / 默认 kind=log / L3 写盘默认通过 / 三过滤器拒绝即终止不询问。

`/cortex:ingest` (会话内交互): per-file `AskUserQuestion` L3 写盘授权门; 批量 ≥3 升级 per-batch 单次确认。

## 落档后必跑 self-check (拒交硬条件, 不达标自决继续补)

- **4 层目录** (`知识库/项目/<host>/<org>/<repo>/`): `主题/` (≥4) + `模块/` + `文件/` + `符号/api/` 任一空 → 拒交
- **分级 .md 下限**: ≤50 文件 ≥15 / 50-500 ≥40 / >500 ≥100 — 详见 [layout.md](references/layout.md) §1.2
- **6 类抽取必产**: API surface + 配置 schema + 错误码 + 测试 + 功能 + 全局常量 — 详见 [extract.md](references/extract.md) §7
- **覆盖度 M/R ≥ 0.8** — 详见 [extract.md](references/extract.md) §4.7
- **知识图谱 4 制品**: Bases YAML + canvas (≤20 节点) + wikilink (每 .md 出链 ≥5) + websearch — 详见 [knowledge-graph.md](references/knowledge-graph.md) §9
- **tag ≥ 10, 严禁占位** ([global-rules.md](references/global-rules.md) §6)

## 评分字段强制 (lint rule 21)

知识库 .md 4 字段 (0.0-10.0 浮点 + maturity enum): `score` / `confidence` / `source_credibility` / `maturity`。AI 落档自动写, 详见 [extract.md](references/extract.md) §3.1。

## References 指针

| 文件 | 内容 |
|---|---|
| [pipeline.md](references/pipeline.md) | 9 步主流程 + 源类型表 + 错误处理 + Source frontmatter 路由 |
| [safety-filters.md](references/safety-filters.md) | P0 三过滤器 (url_security/html_sanitize/masking) 详细规范 |
| [layout.md](references/layout.md) | 4 层目录 + 分级 .md 下限 + 拒交硬条件 + 分级评分 + 增量元数据 |
| [extract.md](references/extract.md) | frontmatter schema + 深度处理 L1-L6 + 6 类抽取 + 覆盖度 + 评分启发式 |
| [exclude.md](references/exclude.md) | 强制排除清单 (build 产物 / lock / binary / 系统 IDE / 临时备份 / 压缩包) |
| [knowledge-graph.md](references/knowledge-graph.md) | 4 制品 (Bases/Canvas/Wikilink/websearch) |
| [global-rules.md](references/global-rules.md) | 文件夹优先 + 嵌套 repo 处理 + tag ≥10 约定 |

## 不做

- 不修改源文件 (只读); 不调 `git commit`; 不抓 URL 二级链接 (除非显式 `/cortex:ingest`); 不抽过 5 个 entity (避噪音, 多了让用户手工拆)
