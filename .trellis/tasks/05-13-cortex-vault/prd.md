# cortex 知识库目录结构对齐 vault

## 目标

仅修改"知识库目录结构"相关内容 — 把插件 spec 中描述的知识库子目录模型, 对齐用户实际 vault 使用情况。**不动其他**(算法 / 落档逻辑 / 渲染 / lint 规则除根目录白名单外, 全不动)。

## 用户实际 vault 现状 (现场观察)

```
<vault>/
├── _assets/
├── _meta/
├── _templates/
├── 仪表盘/
├── 归档/{2026, L4-2026, 日记, _index.md}
├── 知识库/
│   ├── 收件箱/                       # 空, 但保留作 inbox 入口
│   ├── 日记/
│   │   └── 日/                       # 仅"日"层级, 无周/月/年
│   │       ├── 2026-05/              # 按月 bucket
│   │       └── _index.md
│   ├── 项目/
│   │   ├── github.com/<org>/<repo>/
│   │   ├── gitlab.starpago.com/<org>/<repo>/
│   │   └── gitlab.wisburg.com/<org>/<repo>/
│   └── 领域/
│       ├── 创作/
│       ├── 学习/
│       ├── 工作/
│       ├── 技术/{Chromium, Flutter, Go, MySQL, Redis, Rust}/
│       ├── 生活/
│       └── 金融/
└── 记忆/{L0-核心, L1-长期, L2-中期, L3-短期, L4-流水账, views, working}
```

## 现状差异

| 子目录 | 插件 spec 现状 | 实际 vault | 决策 |
|------|---------|---------|------|
| 知识库/项目/ | ✓ | ✓ host/org/repo 三级 | 保留 (已在前 task 对齐) |
| 知识库/领域/ | ✓ 含细分 | ✓ 6 个域 (创作/学习/工作/技术/生活/金融), 域下可再分 | 保留, 域名不固化 (用户自决) |
| 知识库/日记/ | 含 日/周/月/年 4 级 | 仅 日/<YYYY-MM>/ | **简化为仅 日/<YYYY-MM>/** |
| 知识库/收件箱/ | ✓ | ✓ (空) | 保留 |
| 知识库/来源/ | ✓ 含 网页/论文/书籍 | ❌ 不存在 | **删除** |
| 知识库/反思/ | ✓ | ❌ 不存在 | **删除** |
| 知识库/实体/ | ✓ | ❌ 不存在 | **删除** |
| 知识库/概念/ | ✓ | ❌ 不存在 | **删除** |
| 知识库/问题/ | ✓ | ❌ 不存在 | **删除** |
| 知识库/临时/ | ✓ | ❌ 不存在 | **删除** |

## 新知识库 4 子目录模型 (硬约束)

```
知识库/
├── 收件箱/           # 入口: 未分类落档, 待人工 / digest 归类
├── 日记/
│   └── 日/<YYYY-MM>/<YYYY-MM-DD>.md
├── 项目/<host>/<org>/<repo>/
│   ├── _index.md
│   ├── 架构.md  决策.md  陷阱.md  依赖.md
│   ├── 笔记/<date>-<topic>.md
│   └── 决策/<NNN>-<topic>.md
└── 领域/<域名>/
    └── (子结构由用户自决, 域名不固化)
```

非 repo 来源 (网页/论文/书): 落 `知识库/收件箱/<host>-<slug>.md`, 等 digest 时按内容分发到 领域/<域> 或 项目/<host>/<org>/<repo>/笔记/。

实体 / 概念 / 反思 / 问题 / 临时: 不再独立子目录, 改为:
- entity (人/工具) → `知识库/领域/<域>/<entity-kebab>.md` 或 `知识库/项目/<host>/<org>/<repo>/<entity-kebab>.md` (按归属)
- concept → `知识库/领域/<域>/<concept-kebab>.md`
- reflection → `知识库/日记/日/<YYYY-MM>/<date>-反思-<topic>.md` (作日记的反思条目)
- question / 临时 → `知识库/收件箱/<slug>.md` (待 digest 处理)

## Ingest 嵌套 repo 规则 (用户补充)

**核心**: ingest 扫某目录时, 若**任一层级**子目录有 `.git/`, 则该子目录作为独立 repo 单独 ingest, **不**回滚到父项目。

```
~/workspace/foo/                  # 父 (可能也是 repo)
├── .git/
├── bar/                          # 子目录
│   └── .git/                     # 子目录也是 repo
└── baz/                          # 子目录, 不是 repo
```

行为:
- 扫 `foo/.git` → 父 ingest 到 `知识库/项目/<foo-host>/<foo-org>/<foo-repo>/`
- 扫 `foo/bar/.git` → 子独立 ingest 到 `知识库/项目/<bar-host>/<bar-org>/<bar-repo>/` (按 bar 自己的 origin)
- `foo/baz/` 内容滚入父 `foo` 项目子文档 (不是独立 repo, 作为 foo 的目录段)

`find . -name .git -type d` 递归发现所有 `.git`, 每个独立 ingest, 父项目内容范围 = 父根 - 子 repo 路径。

## 改动清单 (仅目录结构相关)

### 1. `presets/seed/知识库/`

**删除子目录** (整目录):
- `presets/seed/知识库/来源/`
- `presets/seed/知识库/反思/`
- `presets/seed/知识库/实体/`
- `presets/seed/知识库/概念/`
- `presets/seed/知识库/问题/`
- `presets/seed/知识库/临时/`
- `presets/seed/知识库/日记/周/` `月/` `年/` (仅留 日/)

**保留**:
- `presets/seed/知识库/_index.md`
- `presets/seed/知识库/收件箱/_index.md`
- `presets/seed/知识库/日记/_index.md` (改描述只含日)
- `presets/seed/知识库/日记/日/_index.md`
- `presets/seed/知识库/项目/_index.md`
- `presets/seed/知识库/领域/_index.md`

`知识库/_index.md` children 列表只列 4 项 (收件箱/日记/项目/领域)。

### 2. `presets/_structure.json`

`required_seeds` / 必备路径 list, 删:
- `知识库/来源/` 及所有子项 (代码仓库已在前 task 删)
- `知识库/反思/`
- `知识库/实体/`
- `知识库/概念/`
- `知识库/问题/`
- `知识库/临时/`
- `知识库/日记/周/` `月/` `年/`

### 3. `scripts/lint/schemas.py` + `scripts/lint/run.py`

`root_dirs` whitelist 内 `知识库/` 子目录允许清单收紧:
- LYT/PARA/flat 三 preset 全统一: 知识库 子层仅 `{项目, 领域, 日记, 收件箱}`
- locale_dirs 知识库子层名映射 (projects/domains/journal/inbox) 同步收紧

vault-structure-violation 规则 autofix:
- 旧 `知识库/反思/<x>.md` → autofix 路径建议 `知识库/收件箱/<x>.md` (待人工 digest 重分配)
- 旧 `知识库/实体/<x>.md` / `知识库/概念/<x>.md` → autofix 提示 `知识库/领域/<待选>/` (无法自动选域, 报 warn 不 mv)
- 旧 `知识库/问题/<x>.md` / `知识库/临时/<x>.md` → autofix mv 到 `知识库/收件箱/<x>.md`
- 旧 `知识库/日记/{周|月|年}/<x>.md` → autofix mv 到 `归档/日记/<YYYY-QN>.md` 季度桶

### 4. `scripts/cli/save.py` — kind 路由调整 (仅目录路径, 不动算法)

- `kind=entity` 路由: 删 `知识库/实体/<kebab>.md`, 改 `知识库/领域/<域>/<entity-kebab>.md` (域必须由参数指定 `--domain`, 缺则报错引导)
- `kind=concept` 路由: 删 `知识库/概念/<kebab>.md`, 改 `知识库/领域/<域>/<concept-kebab>.md` (同上)
- `kind=reflection` 路由: 删 `知识库/反思/<kebab>.md`, 改 `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<topic>.md`
- `kind=question` / `kind=fleeting`: 删独立路径, 改 `知识库/收件箱/<slug>.md`
- `kind=project` / `kind=domain`: 保持 (前 task 已对齐)
- `kind=source`: 改路由 `知识库/收件箱/<host>-<slug>.md` (不再有 来源/网页 等子目录; 落收件箱待 digest 分发)
- `kind=log` (日记): 路径 `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`, 周/月/年 kind 删

### 5. `scripts/cli/ingest_url.py` / `ingest_file.py`

URL host 自动路由表 (前 task 设的):
- github/gitlab → kind=project (不变)
- arxiv → kind=source, 路径改 `知识库/收件箱/arxiv-<slug>.md` (原 `知识库/来源/论文/`)
- 其他 host → kind=source, 路径 `知识库/收件箱/<host>-<slug>.md`

`ingest_file.py` 嵌套 repo 处理 (用户补充规则):
- `_detect_project_root` 之后, 加 `_find_nested_repos` 步骤: `find <root> -name .git -type d -not -path "*/node_modules/*"`
- 每个 `.git` 父目录独立 ingest 调用一次
- 父项目内容范围 = 父根 - 所有子 `.git` 父目录路径
- 输出: 每个嵌套 repo 一条 ingest 记录

### 6. `skills/cortex-ingest/SKILL.md` + `cortex-save/SKILL.md` + `cortex-new/SKILL.md` + `cortex-install/SKILL.md`

仅目录相关章节同步:
- 知识库子目录从 N 项缩到 4 项 (项目/领域/日记/收件箱)
- 删 来源/反思/实体/概念/问题/临时 路径表行
- 日记仅日, 删周/月/年
- 嵌套 repo 行为强化 (按用户补充规则写明)
- 算法 / 落档机制描述不动

### 7. `commands/ingest.md` + `commands/save.md` + `commands/lint.md`

仅路径表 / 目录结构图同步收紧到 4 子目录 + 日仅日。

### 8. `agents/cortex-{archivist,linker,cartographer,curator,researcher,historian,summarizer,translator}.md`

仅目录路径引用同步 (任何 `知识库/反思/` `知识库/实体/` `知识库/概念/` `知识库/问题/` `知识库/临时/` `知识库/日记/{周|月|年}/` 残留 → 改新路径)。

### 9. `presets/seed/_templates/`

- `_templates/concept.md` / `entity.md` / `question.md` / `domain.md`: 模板保留 (用作落档 frontmatter 范例), 加 deprecation 注释 "本模板用于 知识库/领域/<域>/ 下的概念/实体页, 不再独立子目录"
- `_templates/source.md`: 描述改 "收件箱临时占位, digest 时分发到 项目 笔记/ 或 领域/<域>/"

### 10. `docs/知识库结构.md` + `docs/_internal/*.md`

仅目录树 / 子目录列表同步收紧。算法描述不动。

### 11. `.claude/memory/cortex-plugin-2026-05-13.md` 由 neat-freak 处理

主线 neat-freak 后续同步, 本 task 不动。

## 验收

- `find presets/seed/知识库 -type d` 仅出 `知识库`, `收件箱`, `日记`, `日记/日`, `项目`, `领域` 6 目录 (无 来源/反思/实体/概念/问题/临时/日记/周/月/年)
- `grep -rn "知识库/反思\|知识库/实体\|知识库/概念\|知识库/问题\|知识库/临时\|知识库/日记/周\|知识库/日记/月\|知识库/日记/年\|知识库/来源/网页\|知识库/来源/论文\|知识库/来源/书籍" agents/ commands/ skills/ scripts/cli/ docs/` = 0 (除 lint deprecation 规则定义)
- `presets/_structure.json` 知识库 必备 seed 缩到 4 + 日记/日 + 项目/_index + 领域/_index + 收件箱/_index = 6 项
- `scripts/lint/schemas.py` root_dirs 知识库子层枚举 = 4
- python tests 全绿 (新加 case: save.py kind=entity 缺 --domain 报错, kind=fleeting → 收件箱)
- `bash ~/.cortex/scripts/lint.sh` 在 mock vault 跑, 含 `知识库/反思/x.md` → autofix mv 到 `知识库/收件箱/x.md` (或 warn 不 mv 视情况)

## 用户确认决策 (2026-05-13)

### a) entity/concept 域选择 — AI 自决创建

- `--domain` 参数可选;缺失时, SKILL/agent 读 body 内容自决选 6 域之一 (创作/学习/工作/技术/生活/金融) 或**创建新子目录** (如 `创作/写作/`, `技术/分布式系统/`)
- 命令行/CLI 直接调 `cortex_save` 时, 若 `--domain` 缺, 走 AI 启发式: 读 title + body[:500], 匹配关键词 → 选域;不匹配 → 默认 `领域/未分类/`(创建)
- SKILL.md 内固化"自决判断流程": 列出 6 域典型关键词 (创作=写作/小说/诗;学习=笔记/课程/读书;工作=任务/会议/项目管理;技术=代码/编程/算法/工具;生活=日常/食物/旅行;金融=股票/投资/财务)
- 必要时 SKILL.md 明示"创建新子目录"权限给 LLM

### b) lint autofix 旧路径处理 — 按建议

- `知识库/反思/`, `知识库/问题/`, `知识库/临时/` → autofix `mv` 到 `知识库/收件箱/<basename>.md`
- `知识库/实体/`, `知识库/概念/` → **warn 不 mv** (需 AI 选域, lint 不自决)
  - finding 描述: "应迁到 知识库/领域/<域>/<kebab>.md;请用 cortex_save kind=entity/concept 重新落档 (AI 自决选域)"
- `知识库/日记/{周|月|年}/` → autofix `mv` 到 `归档/日记/<YYYY-QN>.md` 季度桶
- `知识库/来源/网页/`, `知识库/来源/论文/`, `知识库/来源/书籍/` → autofix `mv` 到 `知识库/收件箱/<host>-<slug>.md` (待 digest 分发)

### c) local 项目 — 相对 `~/` 路径作 host/org/repo

非 git repo 或 git origin 非 github/gitlab 的本地项目, **不再使用 `local/<basename>/` 字面**。改为:

- 提目录相对 `$HOME` 的路径: `~/persons/lyxamour/ccplugin/` → `persons/lyxamour/ccplugin`
- 拆段: 第一段=host (`persons`), 第二段=org (`lyxamour`), 第三段=repo (`ccplugin`)
- 路径: `知识库/项目/persons/lyxamour/ccplugin/_index.md`
- 不足 3 段:
  - 2 段 (`~/workspace/foo/` → `workspace/foo`): host=`workspace`, org=`_local`, repo=`foo`
  - 1 段 (`~/foo/`): host=`_local`, org=`_local`, repo=`foo`
  - 0 段 (`~`): host=`_local`, org=`_local`, repo=`home`
- `_local` 是 placeholder 字面 (非用户域名), 用于补齐 host/org/repo 三层
- source_url 字段: 写 `file://$HOME/<rel>` 形式 (作为伪 URL)

`ingest_file.py` `_detect_project_root` 升级:
1. 找 `.git/config`: 若 origin 含 github/gitlab → 走 origin 抽 host/org/repo
2. 找 `.git/config`: 若 origin 非 github/gitlab (本地 git remote / 私服) → 走相对 `$HOME` 路径策略
3. 无 `.git/`: 直接走相对 `$HOME` 路径策略

`scripts/cli/save.py` `kind=project` host=local 分支 → 删, 改为接受**任何**字符串 host (含 `_local`/`workspace`/`persons` 等)。

### d) 删除现有模板, 重新按 4 子目录生成全套

**删除**:
- `presets/seed/_templates/entity.md`
- `presets/seed/_templates/concept.md`
- `presets/seed/_templates/question.md`
- `presets/seed/_templates/source.md` (旧版含网页/论文/书子类)
- `presets/seed/_templates/domain.md` (前 task 加 DEPRECATED)

**保留并升级** (现有, 内容不变, 仅核对):
- `presets/seed/_templates/project.md` (前 task 新建, 内容已对齐)
- `presets/seed/_templates/_index.md` (索引页模板)
- `presets/seed/_templates/dashboard.md` (仪表盘模板, 前 task 已对齐)

**新建** (基于 4 子目录现状):

1. `_templates/inbox.md` — 收件箱条目 (落档兜底, 待 digest):
   ```yaml
   ---
   lint-skip: true
   type: inbox
   title: <标题>
   source_url: <原始 URL 或 file://$HOME/...>
   captured_at: <YYYY-MM-DDTHH:MM:SSZ>
   maturity: draft
   score: 2
   tags: [type/inbox, source/<host>, lang/<l>, score/2, maturity/draft, captured/<YYYY-MM>, status/待分发, domain/未分类, kind/raw, topic/<slug>]
   ---
   # {{title}}
   > [!info] 来源
   > {{source_url}}
   ```

2. `_templates/journal-day.md` — 日记 (单日条目):
   ```yaml
   ---
   lint-skip: true
   type: journal
   title: {{YYYY-MM-DD}}
   date: {{YYYY-MM-DD}}
   tags: [type/journal, freq/daily, date/{{YYYY-MM-DD}}, month/{{YYYY-MM}}, year/{{YYYY}}, weekday/<n>, lang/zh-CN, source/manual, score/3, maturity/stable]
   ---
   # {{YYYY-MM-DD}}
   ## 早
   ## 午
   ## 晚
   ## 反思
   ```

3. `_templates/domain-topic.md` — 领域子主题页 (entity/concept 落此):
   ```yaml
   ---
   lint-skip: true
   type: topic
   title: <主题>
   domain: <创作|学习|工作|技术|生活|金融|...>
   subtopic: <可选, 比如 技术/分布式系统>
   tags: [type/topic, domain/<域>, subtopic/<子>, lang/<l>, source/<...>, score/<n>, maturity/<l>, keyword/<...>, created/<YYYY>, scope/concept-or-entity]
   ---
   # {{title}}
   > [!abstract] {{title}}
   > <一句话定义>
   ## 关键概念
   ## 相关
   ```

4. `_templates/project-index.md` — 项目主条目 (替前 task `project.md` 命名升级, 内容近同):
   - 既有 `_templates/project.md` 即此, 重命名为 `project-index.md` (更明确)?或保留 `project.md` 命名

**决策**: 保留 `project.md` 命名 (前 task 已建), 不重命名;新建上述 3 个新模板。

总模板清单:
- `_templates/_index.md` (导航索引)
- `_templates/dashboard.md` (仪表盘)
- `_templates/project.md` (项目主条目)
- `_templates/inbox.md` (新)
- `_templates/journal-day.md` (新)
- `_templates/domain-topic.md` (新)
- 共 6 个

## 范围外 (不动)

- 算法逻辑 (masking / BM25 / 子图扩展 / autofix 派生器)
- 落档机制 (flock / hot patch / index patch)
- mermaid 渲染 / dashboard 数据查询命令
- 已 commit 的前 task 工作 (项目 host/org/repo 三级)
- 记忆层 (L0-L4) 任何内容
- tags ≥10 规则
- ingest_url / ingest_file 自动路由 host 判断 (前 task 已对)
