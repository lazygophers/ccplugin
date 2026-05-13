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

2. **抽要点 (启发式)**
   - H1 → 标题候选
   - H2/H3 → 段标题, 留作目录
   - frontmatter (源若是 md) → aliases / sources / authors 直接传递
   - 命名实体短语 (人名 / 工具名 / 项目名) → 候选独立 entity 页
   - 段首一句话 → "一句话定义" → 落入 `> [!info]` callout

3. **选目录 (按 prd §3.2.7 + preset)**

   | 推断类型                  | LYT 路径                 | Zettel                       | PARA                             |
   | ------------------------- | ------------------------ | ---------------------------- | -------------------------------- |
   | source (URL / 文章)       | `知识库/来源/网页/<kebab>.md`  | `references/<UID>-<slug>.md` | `3_resources/sources/<kebab>.md` |
   | concept (新概念页)        | `知识库/领域/<kebab>.md` | `zettels/<UID>-<slug>.md`    | `3_resources/<topic>/<kebab>.md` |
   | entity (人/工具/项目对象) | `知识库/项目/<kebab>.md` | `zettels/<UID>-<entity>.md`  | `2_areas/<area>/<kebab>.md`      |

   preset 从 `<vault>/_meta/version.json:.preset` 读, 缺省 `lyt`。

4. **重名检测**
   - 用 `mcp__obsidian__obsidian_simple_search` 查标题与 alias
   - 命中 → 不覆盖, 改名 `<title>-2.md` `<title>-3.md` ...
   - 同时把发现的旧页路径塞进新页 frontmatter `related: [[old-page]]`

5. **套模板**
   - 优先读 `<vault>/_templates/<type>.md`
   - 不存在则读 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/seed/_templates/<type>.md`
   - 替换 `{{TITLE}}` `{{CREATED}}` `{{UPDATED}}` (UTC `YYYY-MM-DD`) `{{PRESET}}` `{{URL}}` `{{AUTHOR}}`
   - 必填 frontmatter: `type`, `title`, `created`, `updated`, `tags: [cortex-auto, ingested]`
   - source 类型加 `url:` `ingested_at:` 字段

6. **写入**
   - 优先 L1 (官方 obsidian CLI) → L2 (`mcp__obsidian__obsidian_put_content`) → L3 (`Write` 直接写盘)
   - **L3 写盘授权门**: 走到 L3 直接写盘前 **必须调 `AskUserQuestion`** 工具授权; per-file 默认 (单文件 1 次), 批量 ≥3 文件升级 per-batch (单次列出所有目标路径); 用户拒绝则不写盘
   - 检测 `<vault>/.obsidian/plugins/obsidian-git/data.json` 存在 → 文件末尾加 `<!-- cortex-pending-commit -->` (不自动 git commit, prd §10.8)

7. **反向 wikilink 回填**

   ```bash
   python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/backlink_sync.py \
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
   - 进度条形式输出: `[3/12] 处理 docs/foo.md → 知识库/来源/网页/foo.md ✓`
   - 单文件失败不阻断后续, 末尾报告失败清单

## 输出格式

```markdown
摄取完成: 源 = <path|url>

新建 N 个页面:

- [[知识库/来源/网页/foo.md]] (source) · obsidian://open?vault=...&file=...
- [[知识库/领域/bar.md]] (concept)
- ...

反向 wikilink:

- 更新 K 处 backlinks
- 待补 dead link M 条 (见末尾)

dead links (建议: 跑 /cortex:lint --fix):

- [[Nonexistent Page]] (在 [[知识库/来源/网页/foo.md]] 提及)
```

## 错误处理

- WebFetch 失败 → 单 URL 模式直接报错; 批量模式跳过该 URL 继续
- 模板缺失 → 用最小骨架 (frontmatter + H1) 写入并警告
- 写入失败 → 保留原文到 `~/.cache/cortex/ingest/<ts>-<slug>.md` 供用户手处理

## Source 类型路由 + Frontmatter

按 URL/file 判定 source_kind (repo/web/paper/book), 落到对应 知识库/来源/<kind>/. 调 cortex-schema `read <target-path>` 取 schema 填 frontmatter (host/domain/year/author 等), 加 tags_required (含 host/domain/year 实际值替代 placeholder)。例:

- GitHub URL → 知识库/来源/代码仓库/<host>/<org>/<repo>.md, frontmatter: source_kind:repo / host / org / repo / url, tags: [source/repo, host/<host>]
- 网页 URL → 知识库/来源/网页/<slug>.md, tags: [source/web, domain/<domain>]
- arxiv/doi → 知识库/来源/论文/, tags: [source/paper, year/<year>]

schema 缺字段时由 lint `frontmatter-schema-violation` autofix 补 defaults。

## 不做

- 不修改源文件 (源是只读)
- 不调 `git commit`
- 不抓 URL 二级链接 (用户显式跑 `/cortex:ingest` 才追)
- 不抽过 5 个 entity (避免噪音; 多了让用户后续手工拆)

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/ingest.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走默认值跳过 (kind=log, L3 写盘授权门默认通过)
3. persistent: 任何 error 自决降级 / 重试 / 换工具组合, 禁询问, 禁中止
4. 写盘前不需二次确认 (AUTO_MODE 隐含已授权)

---

## 全局知识库构建规则 (覆盖所有 ingest, 增量约束, 不替换上述既有 routing/schema/不做项)

### 1. 文件夹优先 (folder-first)

仓库 / 项目 / 规则集 / 多文档主题: **必须**用目录承载, 不能压缩成单文件:

| 类型 | 目录结构 |
|------|---------|
| github/gitlab 仓库 | `知识库/来源/代码仓库/<host>/<org>/<repo>/index.md` + `<repo>/<topic>.md` (架构 / 模块 / 决策 / 陷阱 / 依赖 / API / examples) |
| 本地 git 仓库 | `知识库/来源/代码仓库/local/<basename>/index.md` + 同上子文档 |
| 项目 (无 git, 含 pyproject/package.json/Cargo.toml/go.mod) | `知识库/项目/<basename>/index.md` + 子文档 |
| 规则集 / spec / 协议 | `知识库/领域/<topic>/index.md` + 各章节 .md |
| 单网页 / 单论文 / 单 PDF | 单文件 (维持现状) |

`index.md` = 主条目 (架构总览 + 子文档导航); 子文档 = 细节深挖。**禁止**把整个仓库塞一个文件。

### 2. 嵌套 git repo 分别独立处理

若 `find $PWD -name .git -type d` 命中多个 (排除 `$PWD/.git` 自身), **每个 nested repo 独立**作为一个仓库 ingest:

- 各自落 `知识库/来源/代码仓库/<host>/<org>/<repo>/`
- 不合并到父项目, 不忽略
- 父目录若也是 repo: 父独立一份, 嵌套各自独立一份
- 顺序: 父先, 嵌套后

### 3. 强制 frontmatter (必填字段, 缺字段 = lint fail)

ingest 落档**必须**含:

```yaml
---
type: <concept|domain|log>
title: <人类可读标题>
desc: <1-3 句, 这页讲啥, 用于召回排序>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [<分类>, <主题>, <技术栈>, ...]   # ≥ 3 个
source_url: <原始 URL — github/gitlab repo url / website url / arxiv url / 本地 git remote / N/A>
version: <对应原始版本 — git commit sha / git tag / package version / website fetch date>
when_to_read: <触发条件描述, 给 AI 召回判定用; 例 "当用户问 X / 改 Y / 调试 Z 时">
score: <1-5>            # 质量评分 (见下 §5)
maturity: <draft|review|stable|deprecated>
---
```

可选: `host` / `org` / `repo` / `aliases` / `authors` / `lang`。

### 4. 深度处理 (depth requirement)

ingest 必须**深度**, 不允许只读 README 草草交差:

| 层 | 必做动作 |
|----|---------|
| L1 结构 | `find -maxdepth 5` 列全树, 识别 src/lib/cmd/docs/tests 等 |
| L2 文档 | Read 全部 README*.md / docs/**.md / CHANGELOG / CONTRIBUTING / spec/* |
| L3 配置 | Read pyproject.toml / package.json / Cargo.toml / go.mod / Makefile / Dockerfile / CI configs |
| L4 入口码 | Glob 语言入口 (main.* / index.* / app.* / cmd/**), Read 核心 50 行 |
| L5 历史 | `git log --oneline -50`, `git log --stat` 看演进; 关键 commit message 提炼决策 |
| L6 派生 | 综合 L1-L5 产出: 架构图描述 / 关键概念表 / 决策史 / 陷阱清单 / 依赖图 |

最少产出**主条目 + 4 个子文档** (典型: architecture / decisions / pitfalls / dependencies)。仓库越大子文档越多, 上限不封顶。

### 5. 分级评分制度

每个 ingest 落档需评:

| 维度 | 取值 | 规则 |
|------|------|------|
| `score` (质量) | 1-5 | 5=权威官方 / 高 star (>10k) / 主流标准; 4=活跃维护 / >1k star; 3=有维护 / 普通; 2=个人项目 / 实验性; 1=废弃 / 不推荐 |
| `maturity` | draft / review / stable / deprecated | 按上游 release 状态或 README 标注判定; 含 `pre-alpha` / `WIP` → draft; 有 release / 有版本号 → stable; archived → deprecated |
| `tags[关注度]` | freq/<high\|mid\|low> | 自动: 含 README badges (CI/coverage/downloads) + commit 近 30 天频率, 按 cortex_search 命中次数定 |

`score` + `maturity` 写入 frontmatter; freq tag 自动追加。lint 规则 `frontmatter-schema-violation` 强制存在性 (缺即 error)。

### 6. tag 强制约定

`tags[]` 必须 ≥ 3 个, 至少覆盖:

1. **来源类型**: `source/repo` / `source/web` / `source/paper` / `source/book` / `source/local`
2. **主题域**: `topic/<领域>` (例 `topic/database`, `topic/llm`, `topic/security`)
3. **技术栈**: `stack/<语言或框架>` (例 `stack/python`, `stack/rust`, `stack/react`); 多个并列

可选额外: `host/<host>` / `org/<org>` / `lang/<zh-CN|en|...>` / `freq/<level>`。

tag 命名: kebab-case, 斜杠分层, 全小写。
