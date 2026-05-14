# cortex-ingest — Frontmatter / 深度处理 / 覆盖度 / 6 类抽取

> SKILL.md §3 (强制 frontmatter) / §4 (深度处理) / §4.7 (覆盖度自检) / §7 (6 类抽取维度) 的详细规范。

---

## 3. 强制 frontmatter (必填字段, 缺字段 = lint fail)

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
score: <1-5>            # 质量评分 (见 references/layout.md §5)
maturity: <draft|review|stable|deprecated>
---
```

可选: `host` / `org` / `repo` / `aliases` / `authors` / `lang` / `path_lang_exempt`。

`path_lang_exempt: true` 用于豁免 lint rule 20 (`path-lang-mismatch`) 的 vault lang 一致性检查 — 仅在文件名/目录名为不可翻译的专名时填 (项目代号 / 配置文件名 / 协议名 / API 端点等)。默认 `false`, 普通页不需填。

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
