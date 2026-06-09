# cortex 项目目录约定 — GitHub/GitLab 入 知识库/项目/<host>/<org>/<repo>/

## 目标

统一 cortex 插件项目/仓库的归档路径: 全部 git repo (含 GitHub/GitLab/local) 入 `知识库/项目/<host>/<org>/<repo>/`。`知识库/来源/` 保留, 但仅承载非 repo 来源 (网页/论文/书/视频/PDF)。

## 用户决策 (2026-05-13)

**选项 C — 全部入项目, 来源仅非 repo**:
- GitHub/GitLab/local git repo → `知识库/项目/<host>/<org>/<repo>/`
- 网页/论文/书/视频/PDF → `知识库/来源/<kind>/<host>/<slug>.md`
- 不再有 `知识库/来源/代码仓库/` (整段删除)

## 现状对比

| 来源 | 现 spec 路径 | 新约定 |
|------|------------|--------|
| GitHub repo | `知识库/来源/代码仓库/github.com/<org>/<repo>/` | `知识库/项目/github.com/<org>/<repo>/` |
| GitLab repo (官方) | `知识库/来源/代码仓库/gitlab.com/<org>/<repo>/` | `知识库/项目/gitlab.com/<org>/<repo>/` |
| GitLab 自建 (host 含 gitlab) | `知识库/来源/代码仓库/<host>/<org>/<repo>/` | `知识库/项目/<host>/<org>/<repo>/` |
| local git (非 github/gitlab) | `知识库/来源/代码仓库/local/<basename>.md` | `知识库/项目/local/<basename>/` |
| 普通项目 (无 git, 有 package.json 等) | `知识库/项目/<basename>/index.md` | `知识库/项目/local/<basename>/` (统一在 local) |
| 网页 / blog | `知识库/来源/网页/<host>/<slug>.md` | 不变 |
| 论文 (arxiv) | `知识库/来源/论文/<slug>.md` | 不变 |
| 书籍 | `知识库/来源/书籍/<slug>.md` | 不变 |

`local` 是特殊 host 字面, 不带 `.` 不带域名, 用于本地 git 或无 git 的普通项目。

## 内部结构 (项目子目录)

```
知识库/项目/<host>/<org>/<repo>/
├── _index.md           # 项目主条目: 概要/架构/状态/依赖/链接
├── 架构.md             # architecture
├── 决策.md             # decisions / ADR
├── 陷阱.md             # pitfalls / gotchas
├── 依赖.md             # dependencies
├── API.md              # API reference (如适用)
├── 笔记/               # 自由笔记子目录
│   └── <date>-<topic>.md
└── 决策/               # ADR 记录 (可与"决策.md"二选一, 单文件适合小项目)
    └── <NNN>-<topic>.md
```

`local/<basename>/` 同结构, 仅 host=local。

## 改动清单

### 1. `presets/seed/知识库/项目/_index.md`

更新结构说明文档块, 从 `<项目名>/` 改为 `<host>/<org>/<repo>/`:

```markdown
> [!info]+ 📂 目录结构
>
> ```
> 知识库/项目/
> ├── _index.md
> ├── <host>/                  # github.com / gitlab.com / gitlab.<your>.com / local
> │   └── <org>/               # 组织 / 用户 / 团队
> │       └── <repo>/          # 仓库名 (或 local 项目 basename)
> │           ├── _index.md    # 项目概览
> │           ├── 架构.md
> │           ├── 决策.md
> │           ├── 陷阱.md
> │           ├── 依赖.md
> │           ├── 笔记/
> │           └── 决策/
> ```
```

Dataview / dashboard 仍 `FROM "知识库/项目"` 自动覆盖三级嵌套。tags 升 ≥10 (现已 5, 添到 ≥10)。

### 2. `skills/cortex-ingest/SKILL.md`

§§ 路径分配章节改写:

- 删除 "GitHub URL → 知识库/来源/代码仓库/..." 段
- 改为: GitHub/GitLab/local git → `知识库/项目/<host>/<org>/<repo>/`
- entity (人/工具/项目对象) 路径表更新: 若属于某 repo, 入 `知识库/项目/<host>/<org>/<repo>/<entity-kebab>.md`;否则 `知识库/概念/<kebab>.md`
- folder-first 章节 "代码仓库" 段路径替换
- 嵌套 git 部分: "各自落 `知识库/项目/<host>/<org>/<repo>/`"

### 3. `commands/ingest.md`

路径判定表全面重写:

```
| git remote → github.com | 项目 | 知识库/项目/github.com/<org>/<repo>/{_index, 架构, 决策, 陷阱, 依赖, 笔记/, 决策/} |
| git remote → gitlab.com | 项目 | 知识库/项目/gitlab.com/<org>/<repo>/... |
| git remote → 自建 gitlab (host 含 gitlab) | 项目 | 知识库/项目/<host>/<org>/<repo>/... |
| 有 .git 但 origin 非 github/gitlab | 项目 | 知识库/项目/local/<basename>/... |
| 无 .git, 有项目文件 (pyproject/package.json/etc) | 项目 | 知识库/项目/local/<basename>/... |
| 其余目录兜底 | 项目 | 知识库/项目/local/<basename>/_index.md |
```

`知识库/来源/代码仓库/` 全段删。

### 4. `scripts/cli/save.py`

`kind=domain` 现路由 `知识库/来源/代码仓库/<host>/<org>/<repo>/<slug>.md`, 改:

- `kind=project` 新增 (优先, 推荐):
  - host/org/repo 必填 → `知识库/项目/<host>/<org>/<repo>/<slug>.md`
  - host=local 时 → `知识库/项目/local/<basename>/<slug>.md` (basename 取 org 字段, repo 字段可空)
- `kind=domain` 保留, 改路由到 `知识库/项目/<host>/<org>/<repo>/<slug>.md` (向后兼容 alias, 但内部走 project 路径)
- `kind=source` 仅承载非 repo 来源, 路由 `知识库/来源/<kind>/<host>/<slug>.md`

### 5. `scripts/cli/ingest_url.py` / `ingest_file.py`

URL/host 判断升级:
- `host in {github.com, gitlab.com}` 或 `host` 含 `gitlab` → kind=project, path=`知识库/项目/<host>/<org>/<repo>/`
- 其他 host → kind=source, path=`知识库/来源/网页/<host>/<slug>.md`
- arxiv → `知识库/来源/论文/<slug>.md`

### 6. `presets/seed/_templates/`

- `project.md`: 新建 (若无) → 项目子文档模板 (frontmatter type=project + host/org/repo 字段 + tags ≥10 + lint-skip)
- `source.md` / `domain.md`: 描述微调, 明确 source 仅非 repo

### 7. `commands/save.md`

若现状还引用 "代码仓库" 路径, 同步改 "项目"。

### 8. `presets/seed/知识库/来源/` (若有 代码仓库 子目录 seed)

`presets/seed/知识库/来源/代码仓库/_index.md` (如存在) → 删除整目录或加 deprecation note。

### 9. Lint 规则同步

`scripts/lint/run.py` 内若有 path 检查涉及 `知识库/来源/代码仓库/`:
- 加 autofix: 旧路径 `知识库/来源/代码仓库/<host>/<org>/<repo>/` 自动 mv 到 `知识库/项目/<host>/<org>/<repo>/`
- 加新规则 `repo-path-deprecated` (warn, autofix:true)

### 10. cortex-archivist / cortex-linker / cortex-cartographer agents

任何提及 "代码仓库" 路径的描述同步改 "项目"。

## 验收

- `grep -rn "来源/代码仓库" plugins/tools/cortex/` 仅剩 lint deprecation 规则描述 (autofix 路径)
- `grep -rn "知识库/项目/<host>" plugins/tools/cortex/` 在 skill/command/cli/template 全部一致
- `presets/seed/知识库/项目/_index.md` 结构图三级嵌套
- python tests 全绿 (新加 save.py kind=project 路由 case)
- `bash ~/.cortex/scripts/lint.sh` 在 mock vault 跑, 含 `知识库/来源/代码仓库/x/y/z/foo.md` 路径 → autofix mv 到 `知识库/项目/x/y/z/foo.md`

## 范围外

- 不动用户实际 vault 内现有数据 (仅插件 spec + lint autofix 提供路径, 用户跑 lint 自决)
- `知识库/反思/` `知识库/实体/` `知识库/概念/` 等其他子目录约定不动 (实际 vault 没用, 但 spec 保留)
- 不强 ingest 现有 vault 内容
