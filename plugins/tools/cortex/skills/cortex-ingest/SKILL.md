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

2. **抽要点 (启发式)**
   - H1 → 标题候选
   - H2/H3 → 段标题, 留作目录
   - frontmatter (源若是 md) → aliases / sources / authors 直接传递
   - 命名实体短语 (人名 / 工具名 / 项目名) → 候选独立 entity 页
   - 段首一句话 → "一句话定义" → 落入 `> [!info]` callout

3. **选目录 (按 prd §3.2.7)**

   | 推断类型                  | LYT 路径 (4 子目录: 项目/领域/日记/收件箱)            | Zettel                       | PARA                             |
   | ------------------------- | ----------------------------------------------------- | ---------------------------- | -------------------------------- |
   | source (URL / 文章, 非 repo, arxiv 含) | `知识库/收件箱/<host>-<slug>.md` (统一落收件箱, 等 digest 分发到 项目/笔记 或 领域/<域>) | `references/<UID>-<slug>.md` | `3_resources/sources/<kebab>.md` |
   | concept (新概念页)        | `知识库/领域/<域>/<kebab>.md` (域由 --domain 指定或 AI 自决, 缺则 领域/未分类/) | `zettels/<UID>-<slug>.md`    | `3_resources/<topic>/<kebab>.md` |
   | entity (人/工具/项目对象) | 若属于某 repo → `知识库/项目/<host>/<org>/<repo>/<entity-kebab>.md`; 否则 → `知识库/领域/<域>/<entity-kebab>.md` | `zettels/<UID>-<entity>.md`  | `2_areas/<area>/<kebab>.md`      |
   | git repo (github/gitlab)  | `知识库/项目/<host>/<org>/<repo>/_index.md` + `{架构,决策,陷阱,依赖}.md` + `笔记/` + `决策/` | `references/<UID>-<repo>.md` | `1_projects/<repo>/` |
   | 本地项目 (无 git 或私服 git) | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/` (相对 $HOME 路径拆段, 不足 3 段补 `_local`) | (同上) | (同上) |
   | reflection (反思)         | `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<slug>.md` (日记一项, 不再独立目录) | — | — |
   | question/fleeting/临时    | `知识库/收件箱/<slug>.md` (待 digest 分发)             | — | — |
   | journal (日记)            | `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md` (仅日)      | — | — |

   **嵌套 repo 行为** (用户补充规则): ingest 扫某目录时, 若任一层级子目录有 `.git/`, 则该子目录作为独立 repo 单独 ingest, **不**回滚到父项目。`find <root> -name .git -type d -not -path "*/node_modules/*"` 递归发现所有 `.git`, 每个独立 ingest, 父项目内容范围 = 父根 − 所有子 repo 路径。

   **AI 自决选域 (entity/concept 缺 --domain 时)**: 读 title + body 前 500 字, 匹配 6 域典型关键词:
   - 创作: 写作 / 小说 / 诗 / 剧本 / 设计 / 音乐
   - 学习: 笔记 / 课程 / 读书 / 语言 / 教材
   - 工作: 任务 / 会议 / 项目管理 / 沟通 / OKR
   - 技术: 代码 / 编程 / 算法 / 工具 / 协议 / 框架 / 库
   - 生活: 日常 / 食物 / 旅行 / 健康 / 家居
   - 金融: 股票 / 投资 / 财务 / 税务 / 经济

   无匹配 → 默认 `领域/未分类/`。允许 LLM 创建新子目录 (如 `创作/写作/`, `技术/分布式系统/`)。

4. **重名检测**
   - 用 `mcp__obsidian__obsidian_simple_search` 查标题与 alias
   - 命中 → 不覆盖, 改名 `<title>-2.md` `<title>-3.md` ...
   - 同时把发现的旧页路径塞进新页 frontmatter `related: [[old-page]]`

5. **套模板**
   - 优先读 `<vault>/_templates/<type>.md`
   - 不存在则读 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/seed/_templates/<type>.md`
   - 替换 `{{TITLE}}` `{{CREATED}}` `{{UPDATED}}` (UTC `YYYY-MM-DD`) `{{URL}}` `{{AUTHOR}}`
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
   - 进度条形式输出: `[3/12] 处理 docs/foo.md → 知识库/收件箱/foo.md ✓`
   - 单文件失败不阻断后续, 末尾报告失败清单

## 输出格式

```markdown
摄取完成: 源 = <path|url>

新建 N 个页面:

- [[知识库/收件箱/example.com-foo.md]] (inbox / source) · obsidian://open?vault=...&file=...
- [[知识库/领域/技术/bar.md]] (concept, domain=技术)
- ...

反向 wikilink:

- 更新 K 处 backlinks
- 待补 dead link M 条 (见末尾)

dead links (建议: 跑 /cortex:lint --fix):

- [[Nonexistent Page]] (在 [[知识库/收件箱/example.com-foo.md]] 提及)
```

## 错误处理

- WebFetch 失败 → 单 URL 模式直接报错; 批量模式跳过该 URL 继续
- 模板缺失 → 用最小骨架 (frontmatter + H1) 写入并警告
- 写入失败 → 保留原文到 `~/.cache/cortex/ingest/<ts>-<slug>.md` 供用户手处理

## Source 类型路由 + Frontmatter

按 URL/file 判定 source_kind. **repo (github/gitlab)** 走 **kind=project** 路由, 落 `知识库/项目/<host>/<org>/<repo>/`;**本地项目 (无 git 或私服 git)** 走相对 `$HOME` 路径策略 (拆段为 host/org/repo, 不足 3 段用 `_local` 补齐), 同样落 `知识库/项目/<host>/<org>/<repo>/`;**其他非 repo 来源 (网页/论文/书籍)** 统一落 `知识库/收件箱/<host>-<slug>.md`, 等 digest 分发到 项目/笔记 或 领域/<域>。调 cortex-schema `read <target-path>` 取 schema 填 frontmatter (host/domain/year/author 等), 加 tags_required (含 host/domain/year 实际值替代 placeholder)。例:

- GitHub/GitLab URL → `知识库/项目/<host>/<org>/<repo>/_index.md`, frontmatter: type:project / host / org / repo / source_url, tags: [type/project, host/<host>, org/<org>, repo/<repo>]
- 本地项目 `~/persons/lyxamour/ccplugin/` → `知识库/项目/persons/lyxamour/ccplugin/_index.md`, source_url: `file://$HOME/persons/lyxamour/ccplugin`
- 网页 URL → `知识库/收件箱/<host>-<slug>.md`, tags: [type/inbox, source/web, host/<host>]
- arxiv/doi → `知识库/收件箱/arxiv.org-<slug>.md`, tags: [type/inbox, source/paper, year/<year>]
- 书籍 → `知识库/收件箱/<host>-<slug>.md`, tags: [type/inbox, source/book]

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
| github/gitlab 仓库 | `知识库/项目/<host>/<org>/<repo>/_index.md` + `{架构,决策,陷阱,依赖,API}.md` + `笔记/` + `决策/` |
| 本地 git 仓库 (origin 非 github/gitlab) | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (相对 $HOME 路径拆段, 不足 3 段补 `_local`) + 同上子文档 |
| 项目 (无 git, 含 pyproject/package.json/Cargo.toml/go.mod) | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (同上策略) + 子文档 |
| 规则集 / spec / 协议 | `知识库/领域/<topic>/_index.md` + 各章节 .md |
| 单网页 / 单论文 / 单 PDF | 单文件 (维持现状) |

#### 1.1 子文档下限 (按 repo 文件数分级, 强制)

落档 `知识库/项目/<host>/<org>/<repo>/` 后, 子文档数量必达下限:

| repo 文件数 N | **强制 .md 下限** | 子目录 (必建) | 必含 .md |
|---|---|---|---|
| N ≤ 50 | **≥ 6 .md** | `笔记/` 可选 | `_index.md` + `architecture.md` + `decisions.md` + `pitfalls.md` + `dependencies.md` + `notes.md` |
| 50 < N ≤ 500 | **≥ 10 .md** | `笔记/` + `模块/` 强制 | 同上 + 每个顶级模块独立 `模块/<module>.md` |
| N > 500 | **≥ 20 .md** | `笔记/` + `模块/` + `API/` 强制 | 同上 + 关键 API 拆 `API/<api>.md` |

文件数 N 取自 `find <repo> -type f -not -path "*/.git/*" -not -path "*/node_modules/*" | wc -l`。

`_index.md` = 主条目 (架构总览 + **子文档导航表** + **全文件清单覆盖表**); 子文档 = 细节深挖。**禁止**把整个仓库压一个文件。

#### 1.2 拒交硬条件 (落档后必 verify, 不通过则继续补, 严禁提交)

```bash
ROOT="知识库/项目/<host>/<org>/<repo>"
TOP_MD=$(ls "$ROOT" | grep -c '\.md$')                 # 主层 .md 数
ALL_MD=$(find "$ROOT" -name '*.md' | wc -l)            # 全部 .md (含子目录)
```

- `TOP_MD < 6` → 拒交, 继续补主层子文档
- `ALL_MD < 下限` (6 / 10 / 20 按 §1.1) → 拒交, 继续补
- `TOP_MD == 1` (主层只有 `_index.md`) → **视为偷工, 直接拒交**
- 不达标禁止给用户最终报告, AI 必须自决继续补直至通过

### 2. 嵌套 git repo 分别独立处理

若 `find $PWD -name .git -type d` 命中多个 (排除 `$PWD/.git` 自身), **每个 nested repo 独立**作为一个仓库 ingest:

- 各自落 `知识库/项目/<host>/<org>/<repo>/`
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
tags: [<分类>, <主题>, <技术栈>, ...]   # ≥ 10 个 (严禁 placeholder/<待填>/TODO 等占位)
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

#### 4.7 覆盖度自检 (落档后必做, 强制)

ingest 完跑覆盖度核算, 不达标继续补:

```bash
N=$(find <repo> -type f -not -path "*/.git/*" -not -path "*/node_modules/*" | wc -l)   # repo 文件总数
M=$(grep -rhoE '`[^`]+\.[a-zA-Z0-9]+`|\[\[[^]]+\]\]' "知识库/项目/<host>/<org>/<repo>/" | sort -u | wc -l)  # 落档主体引用文件数 (粗估)
```

- **要求 `M / N ≥ 0.8`** (核心源码 + 文档 + 配置 + tests 至少覆盖 80%)
- 覆盖率不足: 补 `笔记/<未分类项>.md` 收尾, frontmatter 标 `coverage_gap: [<漏掉的 file path 列表>]`
- `_index.md` **必含**一个 "文件清单覆盖" 表: 全 file path 列出 → 哪个子文档 cover

  | file | cover_doc |
  |---|---|
  | `src/main.py` | `architecture.md` |
  | `tests/test_x.py` | `笔记/tests.md` |
  | ... | ... |

### 5. 分级评分制度

每个 ingest 落档需评:

| 维度 | 取值 | 规则 |
|------|------|------|
| `score` (质量) | 1-5 | 5=权威官方 / 高 star (>10k) / 主流标准; 4=活跃维护 / >1k star; 3=有维护 / 普通; 2=个人项目 / 实验性; 1=废弃 / 不推荐 |
| `maturity` | draft / review / stable / deprecated | 按上游 release 状态或 README 标注判定; 含 `pre-alpha` / `WIP` → draft; 有 release / 有版本号 → stable; archived → deprecated |
| `tags[关注度]` | freq/<high\|mid\|low> | 自动: 含 README badges (CI/coverage/downloads) + commit 近 30 天频率, 按 `bash ~/.cortex/scripts/search.sh` 命中次数定 |

`score` + `maturity` 写入 frontmatter; freq tag 自动追加。lint 规则 `frontmatter-schema-violation` 强制存在性 (缺即 error)。

### 6. tag 强制约定

`tags[]` 必须 ≥ 10 个, 严禁占位 (`<待填>` / `placeholder/N` / `TODO` / `TBD` 等空语义), 至少覆盖:

1. **来源类型**: `source/repo` / `source/web` / `source/paper` / `source/book` / `source/local` (必含)
2. **主题域**: `topic/<领域>` (例 `topic/database`, `topic/llm`, `topic/security`) (必含)
3. **技术栈**: `stack/<语言或框架>` (例 `stack/python`, `stack/rust`, `stack/react`); 多个并列 (必含)
4. **来源元数据**: `host/<host>` / `org/<org>` / `repo/<repo>`
5. **语言**: `lang/<zh-CN|en|...>`
6. **质量评分**: `score/<1-5>`
7. **成熟度**: `maturity/<draft|review|stable|deprecated>`
8. **时间**: `created/<YYYY>`
9. **类型**: `type/<concept|domain|log|...>`
10. **关键词**: `keyword/<词>` (从 h1/h2/正文派生, 中文 2-4 字短语或英文 PascalCase 词)

lint 规则 `fm-missing-tags` 强制 ≥ 10, autofix 会读 frontmatter + 正文派生; 派生不足 10 由 AI 二次补足, 严禁写占位符。

tag 命名: kebab-case, 斜杠分层, 全小写。
