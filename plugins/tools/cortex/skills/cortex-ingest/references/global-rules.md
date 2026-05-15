# cortex-ingest — 全局知识库构建规则 (覆盖所有 ingest, 增量约束)

> SKILL.md §全局知识库构建规则 详细规范。

## 1. 文件夹优先 (folder-first)

仓库 / 项目 / 规则集 / 多文档主题: **必须**用目录承载, 不能压缩成单文件:

| 类型 | 目录结构 |
|------|---------|
| github/gitlab 仓库 | `知识库/项目/<host>/<org>/<repo>/_index.md` + `{架构,决策,陷阱,依赖,API}.md` + `笔记/` + `决策/` |
| 本地 git 仓库 (origin 非 github/gitlab) / 无 git 项目 (含 pyproject/package.json/Cargo.toml/go.mod) | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (相对 $HOME 拆段, 不足 3 段补 `_local`) + 子文档 |
| 规则集 / spec / 协议 | `知识库/领域/<topic>/_index.md` + 各章节 .md |
| 单网页 / 单论文 / 单 PDF | 单文件 (维持现状) |

4 层目录粒度 + 分级 .md 下限 + 拒交硬条件 + 分级评分制度 — 详见 [layout.md](layout.md)。

## 2. 嵌套 git repo 分别独立处理

`find $PWD -name .git -type d` 命中多个 (排除 `$PWD/.git` 自身) → **每个 nested repo 独立** ingest, 各落 `知识库/项目/<host>/<org>/<repo>/`, 不合并父项目, 不忽略; 父也是 repo 则父独立一份, 嵌套各自独立; 顺序父先嵌套后。

## 3. 强制 frontmatter / 深度处理 / 覆盖度 / 6 类抽取 / 知识图谱

- §3 frontmatter schema + §4 深度处理 L1-L6 + §4.7 覆盖度 M/R ≥ 0.8 + §7 6 类抽取维度 — 详见 [extract.md](extract.md)
- §5 分级评分 (score 0-10 浮点 / maturity / freq tag, P8 升级) — 详见 [layout.md](layout.md) §5
- §8 强制排除清单 — 详见 [exclude.md](exclude.md)
- §9 知识图谱 4 制品 (Bases / Canvas / Wikilink / websearch) — 详见 [knowledge-graph.md](knowledge-graph.md)

## 6. tag 强制约定 (≥ 10, 严禁占位)

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
