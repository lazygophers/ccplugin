# cortex-ingest — Frontmatter / 深度处理 / 覆盖度 / 6 类抽取

> SKILL.md §3 (强制 frontmatter) / §4 (深度处理) / §4.7 (覆盖度自检) / §7 (6 类抽取维度) 的详细规范。

---

## 3. 强制 frontmatter (必填字段, 缺字段 = lint warn rule `frontmatter-required-scores`)

ingest 落档**必须**含:

```yaml
---
# 元数据
type: <concept|domain|log>
title: <人类可读标题>
desc: <1-3 句, 这页讲啥, 用于召回排序>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [<分类>, <主题>, <技术栈>, ...]   # ≥ 10 个 (严禁 placeholder/<待填>/TODO 等占位)
source_url: <原始 URL — github/gitlab repo url / website url / arxiv url / 本地 git remote / N/A>
version: <对应原始版本 — git commit sha / git tag / package version / website fetch date>
when_to_read: <触发条件描述, 给 AI 召回判定用; 例 "当用户问 X / 改 Y / 调试 Z 时">

# 评分字段 (强制 4, 全 0.0-10.0 浮点, AI 落档时自评)
score: 7.5              # 内容质量 (覆盖度 + 深度 + 准确性 综合)
confidence: 8.0         # 内容可信度 (AI 对自己写的有多确定)
source_credibility: 9.0 # 源可信度 (host 白名单查表)
maturity: stable        # enum: draft|review|stable|deprecated (内容稳定度)

# 召回率字段 (强烈推荐, Obsidian simple_search 优先匹配 frontmatter)
aliases: [<中文同义>, <英文缩写>, <全称>, ...]  # ≥ 3 个, AI 落档时根据 title/desc 自动生成
keywords: [<具体短语1>, <具体短语2>, ...]      # ≥ 5 个具体词, 含 项目名/文件名/函数名/术语
---
```

可选: `host` / `org` / `repo` / `authors` / `lang` / `path_lang_exempt`。

`path_lang_exempt: true` 用于豁免 lint rule 20 (`path-lang-mismatch`) 的 vault lang 一致性检查 — 仅在文件名/目录名为不可翻译的专名时填 (项目代号 / 配置文件名 / 协议名 / API 端点等)。默认 `false`, 普通页不需填。

### 3.1 评分字段 AI 自评启发式

| 字段 | 计算源 | 范围 |
|---|---|---|
| score | 6 类抽取覆盖率 (API/配置/错误码/测试/功能/常量) × 10 | 0=无覆盖 / 5=半数 / 10=全覆盖 |
| confidence | tags 完整性 (≥10=5 分) + when_to_read 明确性 (≥30 字=3 分) + 内部 wikilink ≥5 (2 分) | 0=骨架 / 5=合理 / 10=丰满 |
| source_credibility | host 白名单查表 (见下) | 默认 5.0 (未知 host) |
| maturity | 启发: score<5 → draft, 5≤s<8 → review, ≥8 → stable; refresh hash 多变退化 | enum |

#### Host credibility 查表 (硬编码 `scripts/cli/lib/remote.py:_HOST_CREDIBILITY`)

| Host pattern | Credibility |
|---|---|
| anthropic.com / openai.com / google.com 官方 doc | 10.0 |
| react.dev / docs.python.org / pytorch.org 等官方 doc | 9.5 |
| arxiv.org / 顶会论文 | 8.5 |
| github.com / gitlab.com (含 org 仓库) | 7.5 |
| stackoverflow.com / 主流技术问答 | 7.0 |
| medium.com / dev.to / 个人博客 | 5.0 |
| 未知 host / 匿名来源 | 4.0 (默认低) |

### 3.2 评分字段不变量

- 所有 4 字段**必填**, 缺字段 = lint rule `frontmatter-required-scores` warn
- 范围严格 [0.0, 10.0], 越界 → autofix clamp
- `score` / `confidence` / `source_credibility`: float (整数会被 autofix 转 float)
- `maturity`: 4 enum 之一, 错值 autofix 转 `"draft"`
- 旧 `score: 1-5` 整数 → 一次性 migration × 2.0 转 0-10 浮点 (见 PR6 `scripts/migrate/migrate_scores_to_v2.py`)

### 3.3 aliases/keywords 召回率字段 (强烈推荐)

Obsidian `simple_search` 匹配 frontmatter 字段值 + 正文 + tags, 但 ingest 自动生成的 title/desc/tags **不含**用户搜索的具体短语 (如 `tmtc_bg` / `测试环境` / `日志访问`)。补 `aliases` + `keywords` 大幅提召回率。

#### aliases (≥ 3)

从 title + desc 抽:
- 中英文翻译对 (title 含 "认证" → 加 "authentication")
- 缩写 / 全称对 (title 含 "RBAC" → 加 "Role-Based Access Control")
- 别名 / 旧名 (项目重命名后, 加旧名)

#### keywords (≥ 5)

从 body / path / metadata 抽:
- 文件名 stem (e.g. `auth_middleware.py` → 加 `auth_middleware`)
- 函数名 / 类名 (top 5 重要 symbol)
- 配置 key / 环境变量名
- 错误码 / 异常名
- repo 内频繁出现的术语 (≥ 3 次)

实现见 `scripts/cli/lib/remote.py:extract_aliases` / `extract_keywords` (启发式无 AI 调用)。

### 3.4 召回率 lint 不强制 (warn 可选)

lint rule `frontmatter-required-scores` 不校验 `aliases` / `keywords` (可选字段), 但 hot.md 索引时优先选含这两字段的页, 高分子页 (score ≥ 7.0 + maturity in stable/review) 自动入 hot.md。

---

## 4. 深度处理 (depth requirement)

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

---

## 4.7 覆盖度自检 (落档后必做, 强制)

ingest 完跑覆盖度核算, 不达标继续补:

```bash
# R 必先剔除 references/exclude.md 排除清单 (node_modules/vendor/dist/build/lock/binary/.git/.venv/临时 等), 再算覆盖率
R=$(find <repo> -type f \
     -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/vendor/*" \
     -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/__pycache__/*" \
     -not -path "*/target/*" -not -path "*/.venv/*" -not -path "*/.next/*" \
     -not -name '*.lock' -not -name 'package-lock.json' -not -name 'yarn.lock' \
     -not -name 'pnpm-lock.yaml' -not -name 'go.sum' -not -name 'Cargo.lock' \
     -not -name 'Pipfile.lock' -not -name 'poetry.lock' \
     -not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' -not -name '*.gif' \
     -not -name '*.webp' -not -name '*.svg' -not -name '*.ico' \
     -not -name '*.mp4' -not -name '*.mov' -not -name '*.mp3' -not -name '*.wav' \
     -not -name '*.ttf' -not -name '*.woff*' -not -name '*.eot' -not -name '*.otf' \
     -not -name '*.zip' -not -name '*.tar' -not -name '*.gz' -not -name '*.tgz' \
     -not -name '*.bak' -not -name '*.swp' -not -name '*.tmp' -not -name '*.old' \
     -not -name '.DS_Store' \
     | wc -l)
M=$(grep -rhoE '`[^`]+\.[a-zA-Z0-9]+`|\[\[[^]]+\]\]' "知识库/项目/<host>/<org>/<repo>/" | sort -u | wc -l)  # 落档主体引用文件数 (粗估)
```

- **要求 `M / R ≥ 0.8`** (核心源码 + 文档 + 配置 + tests 至少覆盖 80%)
- 覆盖率不足: 补 `笔记/<未分类项>.md` 收尾, frontmatter 标 `coverage_gap: [<漏掉的 file path 列表>]`
- `_index.md` **必含**一个 "文件清单覆盖" 表: 全 file path 列出 → 哪个子文档 cover

  | file | cover_doc |
  |---|---|
  | `src/main.py` | `architecture.md` |
  | `tests/test_x.py` | `笔记/tests.md` |
  | ... | ... |

---

## 7. 抽取维度清单 (6 类强制, repo ingest 必产)

每个 repo ingest **必须**覆盖以下 6 类维度, 缺任一 = self-check 拒交:

| # | 维度 | 抽取手段 | 落档位置 |
|---|------|---------|---------|
| 1 | **公开 API surface** (func/class/interface/exported var) | rg `^(export\|pub\|public)\s` / Python `^def\s[^_]` / Go `^func\s+[A-Z]` / TS `export (function\|class\|interface)` | `符号/api/_index.md` (清单表) + `符号/api/<module>-<name>.md` (每入口 1 .md: 签名 + 摘要 + 调用例 + 调用方) |
| 2 | **配置 schema** (依赖名+版本 / scripts / env vars / build flags) | Read `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod` / `Makefile` / `Dockerfile` / `.env.example` | `主题/配置.md` (依赖表 + scripts 表 + env var 表 + build flag 表) |
| 3 | **错误码 / 异常 / panic message** | rg `errors\.New\|fmt\.Errorf` / `raise\s+\w+Error` / `panic\(` / `throw new` / 自定义 Error 类 | `主题/错误码.md` (代码 + 触发条件 + 处理建议) |
| 4 | **测试用例** (input/expected) | rg `^def test_\|^func Test\|describe\(\|it\(\|test\(` + 提炼 assert | `主题/测试.md` (覆盖功能 + 关键 assert + 边界 case) |
| 5 | **功能模块清单** (用户视角) | README features / cmd/ 子命令 / 路由 handler / CLI subcommand | `主题/功能.md` (功能名 + 入口符号 + 配置项) |
| 6 | **全局变量 / 常量** | rg `^const\s\|^pub const\|CONSTANT_CASE\s*=` / 模块级 var | `符号/常量.md` (常量名 + 值 + 用途 + 引用方) |

self-check **必验**: `主题/{架构,决策,陷阱,依赖,配置,错误码,测试,功能}.md` + `符号/api/_index.md` + `符号/常量.md` 存在性。缺即拒交, AI 自决继续补 (允许分批落档, 不要求一次产全)。
