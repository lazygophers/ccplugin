---
name: cortex-ingest
description: 外部源 (文件/URL/目录) 摄取进 vault — 抽实体, 套模板 (cli=manual), wikilink 回填; URL 走 defuddle。Triggers on "ingest", "摄取".
allowed-tools: Bash Read Write Edit Glob WebFetch mcp__cortex__cortex_ingest_url mcp__cortex__cortex_ingest_file mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content mcp__obsidian__obsidian_simple_search
---

# cortex-ingest

把外部内容 (本地文件 / 网页 / 目录批量) 转成结构化 wiki 页面写入 Obsidian vault。

## 调用优先级 (P4)

1. **MCP 主路径**: `mcp__cortex__cortex_ingest_url` (URL) / `mcp__cortex__cortex_ingest_file` (本地文件: pdf/epub/docx/md/txt)
   - 内部自动串 P0 三过滤器 (url_security/html_sanitize/masking) + extractors + save
   - 输入: `{url|path, kind, tags?, title?, host?, org?, repo?}`
   - 失败抛 ValueError/RuntimeError, skill 不需手工调 P0 filter
2. **fallback (MCP 未装)**: WebFetch + defuddle + 手工调 `hooks/_lib/url_security.py` → `html_sanitize.py` → `masking.py` (见下文 §流程 §1.5)

## 触发场景

- 用户给 URL 说 "ingest this" / "把这篇文章存到知识库"
- 用户给本地 md/pdf/txt 路径 "process this source"
- `/cortex:ingest <path|url|dir>` 显式调用
- Web Clipper 输出目录批量摄取

## 输入信号

- 位置参数 `<path|url|dir>`
- `--type concept|source|entity` 强制类型 (默认 source)
- `--dry-run` 打印计划不写盘
- `--depth N` 目录递归层数 (默认 2)

## 支持源类型

| 源 | 入口 | 默认 type |
|----|------|-----------|
| `https?://...` | `WebFetch` (或外部 `obsidian:defuddle` skill 拿 clean markdown 优先) | source |
| `*.md` `*.txt` | `Read` | source |
| `*.pdf` | `Read` (Read 自带 pdf 解析) | source |
| 目录 | `Glob` 收集 → 单文件循环 | 各文件 source |

## 流程

1. **解析 vault**

   ```bash
   VAULT="$(bash ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh)"
   ```

1.5. **P0 安全过滤 (三过滤器, 顺序严格)** — 详见 `AGENT.md §安全声明`

   按以下顺序调用, 任一拒绝即终止本条目摄取:

   1. **url_security** — URL 入参前置, 拒内网 + metadata + 低端口 SSRF

      ```bash
      python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/url_security.py "$URL" \
        || { echo "rejected SSRF target: $URL" >&2; exit 1; }
      ```

   2. **defuddle / WebFetch** 拉取 markdown → 立即调 **html_sanitize** 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量 (fenced code block 内字面量保留)

      ```bash
      CLEAN_MD="$(python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/html_sanitize.py <<< "$RAW_MD")"
      ```

   3. **masking** — 落档前最后一道, 脱敏 AWS/OpenAI/Anthropic key + GitHub PAT + JWT + PEM + Slack token

      ```bash
      SAFE_MD="$(python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/masking.py <<< "$CLEAN_MD")"
      ```

   绕过 (仅测试):`CORTEX_SKIP_SANITIZE=1`,生产禁用。

2. **抽要点 (启发式)**
   - H1 → 标题候选
   - H2/H3 → 段标题, 留作目录
   - frontmatter (源若是 md) → aliases / sources / authors 直接传递
   - 命名实体短语 (人名 / 工具名 / 项目名) → 候选独立 entity 页
   - 段首一句话 → "一句话定义" → 落入 `> [!info]` callout

3. **选目录 (按 prd §3.2.7 + preset)**

   | 推断类型 | LYT 路径 | Zettel | PARA |
   |----------|----------|--------|------|
   | source (URL / 文章) | `40_sources/<kebab>.md` | `references/<UID>-<slug>.md` | `3_resources/sources/<kebab>.md` |
   | concept (新概念页) | `10_concepts/<kebab>.md` | `zettels/<UID>-<slug>.md` | `3_resources/<topic>/<kebab>.md` |
   | entity (人/工具/项目对象) | `20_entities/<kebab>.md` | `zettels/<UID>-<entity>.md` | `2_areas/<area>/<kebab>.md` |

   preset 从 `<vault>/_meta/version.json:.preset` 读, 缺省 `lyt`。

4. **重名检测**
   - 用 `mcp__obsidian__obsidian_simple_search` 查标题与 alias
   - 命中 → 不覆盖, 改名 `<title>-2.md` `<title>-3.md` ...
   - 同时把发现的旧页路径塞进新页 frontmatter `related: [[old-page]]`

5. **套模板**
   - 优先读 `<vault>/_templates/<type>.md`
   - 不存在则读 `${CLAUDE_PLUGIN_ROOT}/templates/<type>.md`
   - 替换 `{{TITLE}}` `{{CREATED}}` `{{UPDATED}}` (UTC `YYYY-MM-DD`) `{{PRESET}}` `{{URL}}` `{{AUTHOR}}`
   - 必填 frontmatter: `type`, `title`, `created`, `updated`, `tags: [cortex-auto, ingested]`
   - source 类型加 `url:` `ingested_at:` 字段

6. **写入**
   - 优先 L1 (官方 obsidian CLI) → L2 (`mcp__obsidian__obsidian_put_content`) → L3 (`Write` 直接写盘)
   - **L3 写盘授权门**: 走到 L3 直接写盘前 **必须调 `AskUserQuestion`** 工具授权; per-file 默认 (单文件 1 次), 批量 ≥3 文件升级 per-batch (单次列出所有目标路径); 用户拒绝则不写盘
   - 检测 `<vault>/.obsidian/plugins/obsidian-git/data.json` 存在 → 文件末尾加 `<!-- cortex-pending-commit -->` (不自动 git commit, prd §10.8)

7. **反向 wikilink 回填**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/backlink_sync.py \
     --vault "$VAULT" --source "<rel-path>"
   ```
   - JSON 输出: `{updated: [...], skipped: [...], missing: [...]}`
   - missing 列表保留为输出报告 (lint rule #3 会另行报告 dead link)

8. **更新索引**
   - `<vault>/index.md` — type 对应章节加新条目 (无章节 → 创建)
   - `<vault>/log/_index.md` — 加一条 ingest 记录 (`<UTC> ingested <rel-path> from <src>`)
   - hot.md `## 最近落档` 段顶部插入

9. **批量场景 (目录)**
   - 每个文件独立走步骤 2-8
   - 进度条形式输出: `[3/12] 处理 docs/foo.md → 40_sources/foo.md ✓`
   - 单文件失败不阻断后续, 末尾报告失败清单

## 输出格式

```markdown
摄取完成: 源 = <path|url>

新建 N 个页面:
- [[40_sources/foo.md]] (source) · obsidian://open?vault=...&file=...
- [[10_concepts/bar.md]] (concept)
- ...

反向 wikilink:
- 更新 K 处 backlinks
- 待补 dead link M 条 (见末尾)

dead links (建议: 跑 /cortex:lint --fix):
- [[Nonexistent Page]] (在 [[40_sources/foo.md]] 提及)
```

## 错误处理

- WebFetch 失败 → 单 URL 模式直接报错; 批量模式跳过该 URL 继续
- 模板缺失 → 用最小骨架 (frontmatter + H1) 写入并警告
- 写入失败 → 保留原文到 `~/.cache/cortex/ingest/<ts>-<slug>.md` 供用户手处理

## 不做

- 不修改源文件 (源是只读)
- 不调 `git commit`
- 不抓 URL 二级链接 (用户显式跑 `/cortex:ingest` 才追)
- 不抽过 5 个 entity (避免噪音; 多了让用户后续手工拆)
