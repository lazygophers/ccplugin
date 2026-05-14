# cortex 加 2 wrapper — ingest_remote (github/website) + refresh_projects 增量

## Goal

cortex 现有 22 wrapper 覆盖单页 / 单文件 / 本地目录 ingest, 缺 2 入口:

1. **`ingest_remote.sh <url>`** — 远程整站/整 repo 入口 (github/gitlab clone or website crawl) → 落 `知识库/项目/<host>/<org-or-author>/<repo-or-site-slug>/`
2. **`refresh_projects.sh`** — 批量扫 `知识库/项目/` 所有项目, **增量**更新 (git pull diff / website hash 对比 仅刷变动)

补齐 22 → 24 wrapper, 同步全部关联点 (install_wrappers / install_cron / docs / memory / AGENT.md / 测试)。

## What I already know

### 现有 ingest 入口栈

| 入口 | 范围 | python CLI |
|---|---|---|
| `ingest.sh` (slash) | 本地目录, AUTO_MODE skill | (调 /cortex:ingest 加载 SKILL) |
| `ingest_url.sh` | 单 URL 单页 → inbox/project | `ingest_url.py` |
| `ingest_file.sh` | 单本地文件 | `ingest_file.py` |

### 现有项目路径策略 (cortex-plugin memo)

`知识库/项目/<host>/<org>/<repo>/` 三段; github/gitlab 严格三段; 本地仓库相对 $HOME 路径, 不足 3 段补 `_local`。

站点 (上批讨论结果): `知识库/项目/<host>/_site/<slug>/` (host 后无 org/author 补 `_site` 占位)。

### 关联影响点 (全量清单)

代码层:
- `scripts/install_wrappers.sh` — EXPECTED 数组加 2, KEEP_LIST + 文档 22 → 24 (3 处)
- `scripts/install_cron.sh` — 加 refresh_projects weekly cron 注册
- `scripts/cli/` — 新建 `ingest_remote.py` + `refresh_projects.py` (CLI 主体)
- `scripts/cli/lib/` — 抽 git clone / website crawl 可复用模块

文档层:
- `docs/安装与配置.md` — wrapper 清单 22 → 24
- `docs/快速上手.md` — 加 ingest 远程 + refresh 用例
- `docs/故障排查.md` — git clone 失败 / crawl rate-limit / hash 比对失败 排查
- `docs/Skills 详解.md` — 不动 (这俩是 CLI 不是 skill)
- `AGENT.md` — 资产计数 / CLI 主路径表

skill 层:
- `skills/cortex-ingest/SKILL.md` — 加"远程入口 ingest_remote.sh 走 ingest pipeline §1.1 4 层目录"
- `skills/cortex-ingest/references/layout.md` — 站点路径 `_site` 占位明示
- 不新建 skill (CLI 即可, 无需对话式)

memory 层:
- `.claude/memory/cortex-plugin-2026-05-13.md` — 资产计数 22 → 24, cron 8 → 9, CLI 9 → 11

cron 层:
- 加 1 cron: `refresh_projects` weekly Mon 03:00 (与现有 8 cron 同机制, lint/dashboard 后跑)

测试层:
- `tests/python/test_ingest_remote.py` — host 路由 / clone mock / website crawl mock
- `tests/python/test_refresh_projects.py` — 项目扫描 / 增量 diff / hash 对比
- `tests/python/test_wrappers_colorized.py` — 已有 wrapper 通用测试可能要扩验证新 wrapper

## Decision (ADR-lite)

**Context**: User 3 个 AskUserQuestion 回答 + 后续修正 (仅增量) + "注意所有关联地方"

**Decision**:
- D1 远程范围: github/gitlab + website 两种 (`ingest_remote.sh` 单一入口, host 识别 dispatch)
- D2 增量策略: **仅增量** (不加 --mode 开关, 不支持 full)
  - git: 临时 clone → `git pull --depth=1` → diff 上次 ingest 时刻; 首次走全量
  - website: 重 crawl sitemap → 每页 SHA256 hash 比对 (存 frontmatter `content_hash`); 仅 hash 变化才重写
- D3 调度: ingest_remote 手动; refresh_projects weekly cron Mon 03:00
- D4 路径策略 (上批结论): 
  - git repo: `知识库/项目/<host>/<org>/<repo>/`
  - website 有明确 author/org: `知识库/项目/<host>/<author>/<slug>/`
  - website 无 author: `知识库/项目/<host>/_site/<slug>/`

**Consequences**:
- D2 增量: 首次跑 ingest_remote 全量, 后续 refresh_projects 仅刷动。需在 vault project frontmatter 写 `last_ingested_at` + `last_commit_sha` / `content_hash` 元数据。**改动: cortex-ingest SKILL 写 frontmatter schema 加 2 字段** (向后兼容, 旧页无字段视为首次)
- D3 cron weekly: 与现 8 cron daily 错峰避免冲突。**改动: install_cron.sh 加注册**
- D4 占位 `_site`: layout.md 已隐含, 但本任务显式补 schema

## Requirements

### R1: `scripts/cli/ingest_remote.py` + `scripts/ingest_remote.sh` wrapper

#### CLI 入参

```
ingest_remote.py <url> [--target=<path>] [--depth=<int>] [--dry-run] [--json]
```

- `<url>`: github/gitlab repo URL 或 website URL (必填)
- `--target`: 显式 vault 路径覆盖, 默认按 host 自动路由
- `--depth`: website crawl 深度上限 (默认 3); github 忽略
- `--dry-run`: 仅识别 + 输出预期落档路径, 不写盘
- `--json`: 输出 JSON (默认)

#### host 识别 dispatch

- `github.com` / `gitlab.com` (含 `github.io` GitHub Pages → 走 website 模式)
  - clone shallow → 移交本地 ingest pipeline (复用 cortex-ingest skill 4 层目录 + 6 类抽取)
  - 落 `知识库/项目/<host>/<org>/<repo>/`
- 其他 host
  - 读 `<url>/sitemap.xml` (优先) / `<url>/robots.txt` 取 Sitemap 行
  - sitemap 缺 → 递归 `<a href>` BFS, 深度 ≤ `--depth`, 同 host only
  - 每页 defuddle 清洗 → 落 `知识库/项目/<host>/<author-or-_site>/<slug>/<page-slug>.md`
  - 复用 `lib/url_security.py` + `lib/html_sanitize.py` + `lib/masking.py` 三过滤器

#### frontmatter 增量元数据 (写入每页)

```yaml
source_url: https://...
source_type: github | gitlab | website
last_ingested_at: 2026-05-14T03:00:00Z
# git repo:
last_commit_sha: <40-char SHA>
# website:
content_hash: <SHA256-32>
```

#### wrapper `ingest_remote.sh`

风格对齐 `ingest_url.sh` (CLI 类 wrapper):
- `-h/--help` 输出 usage
- `-i/--interactive` 进 REPL + 注入 "/cortex:ingest" 首消息 (复用 ingest skill)
- 调 claude 前 echo 原始 bash + `--dangerously-skip-permissions`
- exec `python3 $PLUGIN_ROOT/scripts/cli/ingest_remote.py "$@"`

### R2: `scripts/cli/refresh_projects.py` + `scripts/refresh_projects.sh` wrapper

#### CLI 入参

```
refresh_projects.py [--vault=<path>] [--scope=<host/org/repo>] [--dry-run] [--json]
```

- `--vault`: vault 根, 默认 resolve_vault
- `--scope`: 限定单项目 / 单 org / 单 host, 默认全扫
- `--dry-run`: 仅扫不更新, 输出待变动列表
- `--json`: 输出 JSON (默认)

#### 增量更新流程

1. 扫 `知识库/项目/<host>/<org>/<repo>/_index.md` (每项目根目录 stub)
2. 读 frontmatter: `source_url` / `source_type` / `last_commit_sha` 或 `content_hash`
3. git repo:
   - shallow clone tmp dir → `git rev-parse HEAD` 取最新 sha
   - 若 == `last_commit_sha`: 无变化, 跳过
   - 否则 `git diff <last_sha> HEAD --name-only` 取变动文件 → 仅 ingest 这批文件 → 更新 sha
4. website:
   - 重 crawl sitemap → 每页 SHA256 → 对比 frontmatter `content_hash`
   - hash 变化 → 重写该页 + 更新 hash
   - hash 一致 → 跳过
5. 输出 JSON: `{projects_scanned, projects_updated, files_changed, files_new, errors}`

#### wrapper `refresh_projects.sh`

风格对齐 `digest.sh` (含 cron 入口):
- `-h/--help` 输出 usage
- 默认无参 → 全量扫
- 加锁 `flock /tmp/cortex-refresh.lock` 防并发

### R3: install_wrappers.sh 同步

- `EXPECTED` 数组加 `ingest_remote.sh` + `refresh_projects.sh` (按 CLI 类分组)
- 文档注释 22 → 24 (3 处行)
- 重新生成 emit 函数生成 2 wrapper 模板 (CLI 类, 复用 `emit_cli` 若存在, 否则参考 `ingest_url.sh` 模板)

### R4: install_cron.sh 同步

- 加 cron 行: `0 3 * * 1 flock -n /tmp/cortex-refresh.lock bash ~/.cortex/scripts/refresh_projects.sh >> ~/.cortex/logs/refresh.log 2>&1`
- 8 cron → 9 cron

### R5: cortex-ingest SKILL 同步

- `skills/cortex-ingest/SKILL.md` — 加"远程入口" 节, 列 ingest_remote.sh 用法
- `skills/cortex-ingest/references/layout.md` — 显式 `_site` 占位 + frontmatter `last_commit_sha` / `content_hash` schema

### R6: docs 同步

- `docs/安装与配置.md` — wrapper 22 → 24, 列新 2 行
- `docs/快速上手.md` — 加用例:
  ```bash
  bash ~/.cortex/scripts/ingest_remote.sh https://github.com/foo/bar
  bash ~/.cortex/scripts/refresh_projects.sh --dry-run
  ```
- `docs/故障排查.md` — 加 3 排查:
  - git clone 失败 (网络 / 认证 / 仓库不存在)
  - website crawl rate-limit (sitemap 404 / 429 / robots disallow)
  - hash 比对失败 (旧 frontmatter 缺 content_hash → 视首次全量)

### R7: AGENT.md 同步

- §资产计数 (若有) — Wrappers 22 → 24, CLI 9 → 11, cron 8 → 9
- §CLI 主路径表 — 加 2 行 (ingest_remote / refresh_projects)

### R8: memory 同步

- `.claude/memory/cortex-plugin-2026-05-13.md`:
  - Wrappers 22 → 24
  - cron 8 → 9
  - CLI 9 → 11
  - 加 §远程 ingest + 批量增量节
  - lint 19 + 测试基线更新

### R9: 测试

- `tests/python/test_ingest_remote.py` — ≥ 10 case:
  - host 识别 (github / gitlab / github.io → website / 其他 website)
  - github URL 解析 org/repo
  - website sitemap 解析 (mock httpx)
  - dry-run 输出预期路径不写盘
  - `_site` 占位生成 (无 author)
  - clone mock (subprocess git)
  - frontmatter 写入 last_commit_sha / content_hash
  - URL 安全 (内网 IP 拒)
  - HTML sanitize (script 剥)
  - JSON 输出 schema
- `tests/python/test_refresh_projects.py` — ≥ 8 case:
  - 扫项目列表 (假 vault 结构)
  - git diff incremental (sha 不变 → 跳过)
  - git diff sha 变化 → 仅变动文件 ingest
  - website hash 一致 → 跳过
  - website hash 变化 → 重写
  - `--scope` 限定单项目
  - `--dry-run` 不写盘
  - JSON 输出 schema
- 不破坏现有 360 测试基线

## Acceptance Criteria

- [ ] `ingest_remote.py` + `ingest_remote.sh` 落地, host 路由正确 (github/gitlab + website)
- [ ] `refresh_projects.py` + `refresh_projects.sh` 落地, 增量逻辑 (sha / hash 对比) 正确
- [ ] install_wrappers.sh EXPECTED 24 项, 文档行同步
- [ ] install_cron.sh 加 weekly refresh cron
- [ ] cortex-ingest SKILL/references 同步 frontmatter schema (+2 字段)
- [ ] docs 3 文件同步 (安装/快速上手/故障排查)
- [ ] AGENT.md 资产计数同步
- [ ] .claude/memory/cortex-plugin-2026-05-13.md 同步
- [ ] pytest 360 → ≥ 378 (≥ +18 新测试)
- [ ] ruff check + format 通过
- [ ] AI 质量检查 cortex-ingest SKILL 仍正确识别

## Definition of Done

- pytest 全绿不下降
- ruff clean
- AI 质量检查 cortex-ingest SKILL
- dry-run smoke:
  ```bash
  bash plugins/tools/cortex/scripts/ingest_remote.sh https://github.com/foo/bar --dry-run
  bash plugins/tools/cortex/scripts/refresh_projects.sh --dry-run
  ```
- install_wrappers.sh 重跑后 ~/.cortex/scripts/ 含 24 文件
- git commit (拆 4 commits: CLI 实现 / wrapper+cron / SKILL+docs / memory)

## Out of Scope

- 不做 `--mode full` 全量刷 (用户明确仅增量)
- 不做 git push / 修改远程 (只读 clone + 本地 ingest)
- 不做 website 鉴权 (cookie / OAuth) — MVP 只支持公开 URL
- 不破坏现有 22 wrapper / 360 测试 / 18 lint
- 不动 cortex-digest evolution / cortex-refactor evolution-apply (上批 PR 成果)

## Technical Notes

- vault truth: `.claude/memory/cortex-plugin-2026-05-13.md` §Vault 模型
- ingest skill 4 层目录 + 6 类抽取契约: `plugins/tools/cortex/skills/cortex-ingest/references/layout.md`
- url_security / html_sanitize / masking 三过滤器: `plugins/tools/cortex/scripts/hooks/_lib/`
- wrapper bash 3.2 兼容 (macOS): `install_wrappers.sh` 用 case + 空格分隔 string, 不用 declare -A
- git CLI: subprocess.run timeout 30s, fail-soft 不抛
- website crawl: 优先 `urllib.request` (stdlib) + 简易 HTML parser, 重 dep 走 defuddle (已有)
