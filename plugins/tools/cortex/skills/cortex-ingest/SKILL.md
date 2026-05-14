---
name: cortex-ingest
description: 外部源 (文件/URL/目录) 摄取进 vault — 抽实体, 套模板 (cli=manual), wikilink 回填; URL 走 defuddle。Triggers on "ingest", "摄取".
allowed-tools: Bash Read Write Edit Glob WebFetch mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content mcp__obsidian__obsidian_simple_search
---

# cortex-ingest

把外部内容 (本地文件 / 网页 / 目录批量) 转成结构化 wiki 页面写入 Obsidian vault。

## 调用优先级 (P4)

1. **CLI 主路径**: `bash ~/.cortex/scripts/ingest_url.sh --url <u> --kind <k>` (URL) / `bash ~/.cortex/scripts/ingest_file.sh --path <p> --kind <k>` (本地文件: pdf/epub/docx/md/txt)
   - 内部自动串 P0 三过滤器 (url_security/html_sanitize/masking) + extractors + save
   - 输入参数: `--url|--path <v>` `--kind <k>` `[--tags ...]` `[--title ...]` `[--host ...]` `[--org ...]` `[--repo ...]`
   - 失败非零退出码 + stderr error message; skill 不需手工调 P0 filter
2. **fallback (CLI 未装)**: WebFetch + defuddle + 手工调 `hooks/_lib/url_security.py` → `html_sanitize.py` → `masking.py` (见下文 §流程 §1.5)

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

| 源             | 入口                                                                 | 默认 type     |
| -------------- | -------------------------------------------------------------------- | ------------- |
| `https?://...` | `WebFetch` (或外部 `obsidian:defuddle` skill 拿 clean markdown 优先) | source        |
| `*.md` `*.txt` | `Read`                                                               | source        |
| `*.pdf`        | `Read` (Read 自带 pdf 解析)                                          | source        |
| 目录           | `Glob` 收集 → 单文件循环                                             | 各文件 source |

## 流程

**AUTO_MODE 探测**: 若 user prompt 含 `[AUTO_MODE:` 或 `non-interactive` 字样 (来自 shell wrapper, 如 `~/.cortex/scripts/ingest.sh`), **跳所有 `AskUserQuestion`, 直执行默认动作**:

- 自动判源类型 (url/file/git/dir), 不询问
- 三过滤器 (url_security/html_sanitize/masking) 任一拒绝即终止, 不询问
- L3 直接写盘授权门: 默认通过 (单文件 / per-batch 均自动), 不调 `AskUserQuestion`
- 默认 `kind=log` 落档

**Interactive 模式** (claude session 内直调 skill): 原有 `AskUserQuestion` 流程不变。

1. **解析 vault**

   ```bash
   VAULT="$(bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh)"
   ```

1.5. **P0 安全过滤 (三过滤器, 顺序严格)** — 详见 `AGENT.md §安全声明`

按以下顺序调用, 任一拒绝即终止本条目摄取:

1.  **url_security** — URL 入参前置, 拒内网 + metadata + 低端口 SSRF

    ```bash
    python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/url_security.py "$URL" \
      || { echo "rejected SSRF target: $URL" >&2; exit 1; }
    ```

2.  **defuddle / WebFetch** 拉取 markdown → 立即调 **html_sanitize** 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量 (fenced code block 内字面量保留)

    ```bash
    CLEAN_MD="$(python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/html_sanitize.py <<< "$RAW_MD")"
    ```

3.  **masking** — 落档前最后一道, 脱敏 AWS/OpenAI/Anthropic key + GitHub PAT + JWT + PEM + Slack token

    ```bash
    SAFE_MD="$(python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/masking.py <<< "$CLEAN_MD")"
    ```

绕过 (仅测试):`CORTEX_SKIP_SANITIZE=1`,生产禁用。
2. **抽要点 (启发式)**: H1 → 标题候选; H2/H3 → 段标题; frontmatter → aliases / sources / authors 直接传递; 命名实体短语 → 候选 entity 页; 段首一句话 → `> [!info]` callout。

3. **选目录** — 路由详见 [references/layout.md](references/layout.md) §1.1 + [references/extract.md](references/extract.md) §3。速查:
   - source (URL/文章 非 repo) → `知识库/收件箱/<host>-<slug>.md`
   - concept → `知识库/领域/<域>/<kebab>.md` (--domain 或 AI 自决, 缺则 领域/未分类/)
   - entity → 属 repo → 项目/<host>/<org>/<repo>/; 否则 → 领域/<域>/
   - git repo (github/gitlab) → `知识库/项目/<host>/<org>/<repo>/_index.md` + 4 层目录
   - 本地项目 → `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/` (相对 $HOME 拆段, 不足 3 段补 `_local`)
   - reflection → `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<slug>.md`
   - question/fleeting/journal → `知识库/收件箱/` 或 `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`

   **AI 自决选域** (entity/concept 缺 --domain 时): 读 title + body 前 500 字, 匹配 6 域 (创作 / 学习 / 工作 / 技术 / 生活 / 金融); 无匹配 → 默认 `领域/未分类/`。允许新建子目录。

4. **重名检测**: `mcp__obsidian__obsidian_simple_search` 查标题与 alias; 命中改名 `<title>-2.md`...; 旧页路径塞 frontmatter `related: [[old-page]]`。

5. **套模板**: 优先 `<vault>/_templates/<type>.md`, 不存在读 plugin `presets/seed/_templates/<type>.md`; 替换 `{{TITLE}}` `{{CREATED}}` `{{UPDATED}}` (UTC YYYY-MM-DD) `{{URL}}` `{{AUTHOR}}`; 必填 frontmatter 见 [references/extract.md](references/extract.md) §3; source 类型加 `url:` `ingested_at:`。

6. **写入**: L1 (官方 obsidian CLI) → L2 (`mcp__obsidian__obsidian_put_content`) → L3 (`Write`)。**L3 写盘授权门**: 必须调 `AskUserQuestion` (per-file 单 1 次, 批量 ≥3 文件升级 per-batch); 拒绝则不写。检 `<vault>/.obsidian/plugins/obsidian-git/data.json` 存在 → 末尾加 `<!-- cortex-pending-commit -->` (不自动 commit)。

7. **反向 wikilink 回填**

   ```bash
   python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/backlink_sync.py \
     --vault "$VAULT" --source "<rel-path>"
   ```

   JSON 输出: `{updated, skipped, missing}`; missing 报告为输出 (lint rule #3 另行报告 dead link)。

8. **更新索引**: `<vault>/index.md` (type 章节加新条目); `<vault>/log/_index.md` 加一条 ingest 记录 (`<UTC> ingested <rel-path> from <src>`); `hot.md ## 最近落档` 段顶部插入。

9. **批量场景 (目录)**: 每文件独立走步骤 2-8; 进度条 `[3/12] 处理 docs/foo.md → 知识库/收件箱/foo.md ✓`; 单文件失败不阻断, 末尾报告失败清单。

**落档后必跑 self-check**: 详见 [references/layout.md](references/layout.md) §1.2 (拒交硬条件) + [references/extract.md](references/extract.md) §4.7 (覆盖度 M/R ≥ 0.8) + §7 (6 类抽取必产) + [references/knowledge-graph.md](references/knowledge-graph.md) §9 (4 制品)。不达标自决继续补。

## 输出格式

```markdown
摄取完成: 源 = <path|url>

新建 N 个页面:
- [[知识库/收件箱/example.com-foo.md]] (inbox / source)
- [[知识库/领域/技术/bar.md]] (concept, domain=技术)

反向 wikilink: 更新 K 处, 待补 dead link M 条
dead links (跑 /cortex:lint --fix): [[Nonexistent Page]] (在 [[...]] 提及)
```

## 错误处理

- WebFetch 失败 → 单 URL 报错; 批量跳过继续
- 模板缺失 → 最小骨架 (frontmatter + H1) 写入并警告
- 写入失败 → 保留原文到 `~/.cache/cortex/ingest/<ts>-<slug>.md`

## Source 类型路由 + Frontmatter

按 URL/file 判定 source_kind: **repo (github/gitlab)** → `知识库/项目/<host>/<org>/<repo>/`;**本地项目** → 相对 `$HOME` 拆段 (不足 3 段补 `_local`), 同样落 项目/;**非 repo 来源 (网页/论文/书籍)** → `知识库/收件箱/<host>-<slug>.md` 等 digest 分发。调 cortex-schema `read <target-path>` 取 schema 填 frontmatter, 加 tags_required。例:

- GitHub/GitLab URL → 项目/<host>/<org>/<repo>/_index.md, tags: `[type/project, host/<host>, org/<org>, repo/<repo>]`
- 本地 `~/persons/lyxamour/ccplugin/` → 项目/persons/lyxamour/ccplugin/_index.md, source_url: `file://$HOME/...`
- 网页 → 收件箱/<host>-<slug>.md, tags: `[type/inbox, source/web, host/<host>]`
- arxiv/doi → 收件箱/arxiv.org-<slug>.md, tags: `[type/inbox, source/paper, year/<year>]`

schema 缺字段时由 lint `frontmatter-schema-violation` autofix 补 defaults。

## 不做

- 不修改源文件 (只读); 不调 `git commit`; 不抓 URL 二级链接 (除非显式 `/cortex:ingest`); 不抽过 5 个 entity (避噪音, 多了让用户手工拆)

## AUTO_MODE 行为 (wrapper 调用)

prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/ingest.sh`): **不调** AskUserQuestion (wrapper allowed-tools 已禁); 用户决策处走默认 (kind=log, L3 写盘默认通过); persistent: error 自决降级/重试/换工具, 禁询问禁中止; 写盘不需二次确认。

---

## 全局知识库构建规则 (覆盖所有 ingest, 增量约束)

### 1. 文件夹优先 (folder-first)

仓库 / 项目 / 规则集 / 多文档主题: **必须**用目录承载, 不能压缩成单文件:

| 类型 | 目录结构 |
|------|---------|
| github/gitlab 仓库 | `知识库/项目/<host>/<org>/<repo>/_index.md` + `{架构,决策,陷阱,依赖,API}.md` + `笔记/` + `决策/` |
| 本地 git 仓库 (origin 非 github/gitlab) / 无 git 项目 (含 pyproject/package.json/Cargo.toml/go.mod) | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (相对 $HOME 拆段, 不足 3 段补 `_local`) + 子文档 |
| 规则集 / spec / 协议 | `知识库/领域/<topic>/_index.md` + 各章节 .md |
| 单网页 / 单论文 / 单 PDF | 单文件 (维持现状) |

4 层目录粒度 + 分级 .md 下限 + 拒交硬条件 + 分级评分制度 — 详见 [references/layout.md](references/layout.md)。

### 2. 嵌套 git repo 分别独立处理

`find $PWD -name .git -type d` 命中多个 (排除 `$PWD/.git` 自身) → **每个 nested repo 独立** ingest, 各落 `知识库/项目/<host>/<org>/<repo>/`, 不合并父项目, 不忽略; 父也是 repo 则父独立一份, 嵌套各自独立; 顺序父先嵌套后。

### 3. 强制 frontmatter / 深度处理 / 覆盖度 / 6 类抽取 / 知识图谱

- §3 frontmatter schema + §4 深度处理 L1-L6 + §4.7 覆盖度 M/R ≥ 0.8 + §7 6 类抽取维度 — 详见 [references/extract.md](references/extract.md)
- §5 分级评分 (score 1-5 / maturity / freq tag) — 详见 [references/layout.md](references/layout.md) §5
- §8 强制排除清单 — 详见 [references/exclude.md](references/exclude.md)
- §9 知识图谱 4 制品 (Bases / Canvas / Wikilink / websearch) — 详见 [references/knowledge-graph.md](references/knowledge-graph.md)

### 6. tag 强制约定 (≥ 10, 严禁占位)

`tags[]` ≥ 10 个, 严禁占位 (`<待填>` / `placeholder/N` / `TODO` / `TBD`), 至少覆盖 10 类:

1. 来源类型 `source/{repo|web|paper|book|local}` (必含)
2. 主题域 `topic/<领域>` (例 `topic/database`) (必含)
3. 技术栈 `stack/<语言或框架>` (例 `stack/python`) 多个并列 (必含)
4. 来源元数据 `host/<host>` / `org/<org>` / `repo/<repo>`
5. 语言 `lang/<zh-CN|en|...>`
6. 质量评分 `score/<1-5>`
7. 成熟度 `maturity/<draft|review|stable|deprecated>`
8. 时间 `created/<YYYY>`
9. 类型 `type/<concept|domain|log|...>`
10. 关键词 `keyword/<词>` (h1/h2/正文派生, 中文 2-4 字短语或英文 PascalCase)

lint `fm-missing-tags` 强制 ≥ 10, autofix 读 fm + 正文派生; 不足由 AI 二次补足, 严禁占位符。tag 命名: kebab-case, 斜杠分层, 全小写。
