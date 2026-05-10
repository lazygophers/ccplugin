# PRD — `cortex` CC Plugin

> 状态: design draft v1 · 创建: 2026-05-10 · owner: nico
> 研究依据: `research/01-obsidian-pkm-patterns.md` · `research/02-ccplugin-arch-baseline.md`

---

## 1. 目标与非目标

### 1.1 目标 (MVP)

打造一个 Claude Code 插件 `cortex`,让 Claude 在任意会话中以**结构化、可观测、可演进**的方式与一个 Obsidian vault 协作:

| # | 能力 | 形态 |
|---|------|------|
| 1 | 会话启动自动注入"先搜知识库"提示 | SessionStart hook |
| 2 | 与 Obsidian vault CRUD/搜索 | `mcp__obsidian__*` + `obsidian` CLI fallback |
| 3 | 一组人类友好的命令入口 | `/cortex:*` slash commands |
| 4 | 可被 Claude 主动调用的能力封装 | skills (5 个 v1) |
| 5 | 会话结束自动落档 | Stop hook |
| 6 | 周期性维护 (lint / fold / dashboard refresh) | 外部 cron 触发器 + `/cortex:cron` 脚本 |
| 7 | vault 健康度体检 | `wiki-lint` skill + `/cortex:lint` |
| 8 | 重构 / 改版 (rename / merge / split / fold) | `/cortex:refactor` + skill |
| 9 | 美观的 markdown + 内嵌 HTML 模板 | `templates/` + skill |
| 10 | 主流 PKM 方法论可选骨架 | `/cortex:install` 多 preset (LYT / Zettel / PARA / blank) |

### 1.2 非目标

- 不实现 Obsidian native plugin (TS),只做 CC plugin
- 不依赖 ccplugin 仓库的 `lib/` 与 Python 生态;插件自包含
- v1 不实现 canvas / bases / dataview 渲染检查 (MCP 不支持,延后)
- v1 不内置 cron daemon;只提供 launchd/cron/GH-Actions 安装稿,用户自决

---

## 2. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code Session                                         │
│                                                             │
│  ┌─[SessionStart hook]─→ inject "search Cortex first" prompt    │
│  │                       + vault path resolution            │
│  │                       + hot.md 摘要 (可选)                │
│  │                                                          │
│  ├─[user prompt / agent loop]                               │
│  │     │                                                    │
│  │     ├─ skills: setup / save / query / ingest / lint      │
│  │     ├─ commands: /cortex:install /cortex:new /cortex:lint /cortex:cron…  │
│  │     └─ MCP: mcp__obsidian__*  (主)                        │
│  │              obsidian CLI    (fallback)                   │
│  │                                                          │
│  └─[Stop hook]──────→ archive session 摘要 → wiki/log/       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼  (out-of-band, optional)
┌─────────────────────────────────────────────────────────────┐
│ Cron / launchd                                              │
│  - daily:  /cortex:lint --auto-fix                              │
│  - weekly: /cortex:fold (log rollup)                            │
│  - weekly: /cortex:dashboard refresh                            │
└─────────────────────────────────────────────────────────────┘
```

数据流 (单向):

```
user/agent ─→ skill ─→ MCP/CLI ─→ Obsidian vault (.md/.canvas/.base)
                                        │
                                        └─→ git auto-commit (可选)
```

---

## 3. 目录骨架

### 3.1 插件侧 (CC plugin source tree)

```
plugins/tools/cortex/
├── .claude-plugin/
│   └── plugin.json                # manifest, keywords, agents/skills/commands 引用
├── README.md                      # 用户向: 安装、配置、5 分钟上手
├── AGENT.md                       # SessionStart 注入正文 (核心提示模板)
├── hooks/
│   ├── hooks.json                 # 钩子声明 (SessionStart / Stop)
│   ├── session_start.sh           # 解析 vault → 输出 additionalContext
│   ├── stop.sh                    # 调度 save skill 落档
│   └── _lib/
│       └── resolve_vault.sh       # 共享: env → config → auto-detect 三段
# 全部能力下沉至 skills/, 无 commands/ 目录 (见 research/05-skills-vs-commands.md §6.3 建议 B)
├── skills/
│   ├── cortex-install/SKILL.md        # vault 创建 / 路径解析 / preset 写入 (原 cortex-setup, 已重命名)
│   ├── cortex-save/SKILL.md           # session → wiki/log + entity 抽取
│   ├── cortex-search/SKILL.md         # 搜索 + 综合 + 必要时回写 (原 cortex-query, 已重命名)
│   ├── cortex-ingest/SKILL.md         # 单源/批量摄取 (file/url/dir)
│   ├── cortex-doctor/SKILL.md         # 13 项体检 (disable-model-invocation: true)
│   └── cortex-new/SKILL.md            # 按模板新建笔记 (disable-model-invocation: true)
├── agents/
│   └── cortex-curator.md              # (可选) 主动维护型 agent,用于 /cortex:refactor
├── templates/
│   ├── concept.md                 # 概念页骨架 (md + 嵌入 HTML 卡片)
│   ├── entity.md                  # 实体 (人/项目/工具)
│   ├── domain.md                  # 项目域索引
│   ├── dashboard.md               # 仪表盘 (Dataview + HTML grid)
│   ├── question.md                # 待办问题
│   ├── source.md                  # 外部来源
│   └── _index.md                  # 模板索引
├── presets/
│   ├── lyt/                       # LYT (Linking Your Thinking) 8-bucket
│   │   ├── _structure.json
│   │   └── seed/                  # 种子文件 (homepage, MOC stubs)
│   ├── zettel/                    # Zettelkasten flat + UID
│   ├── para/                      # PARA (Projects/Areas/Resources/Archive)
│   └── blank/                     # 最小骨架
├── lint/
│   └── rules.json                 # 10 条 v1 lint 规则定义
├── scripts/
│   ├── install_cron.sh            # 打印 launchd/cron snippet (不自动写)
│   └── obsidian_cli_check.sh      # 检测 obsidian CLI / REST API 可用性
└── pyproject.toml                 # (可选) 仅当某 hook/script 需 python stdlib 之外
```

**自包含原则**: 不 `import lib.*`;hook/script 仅用 bash + python stdlib (若必要)。

### 3.2 Obsidian vault 侧 (用户知识库布局)

#### 3.2.1 共享根 (所有 preset 一致)

无论用户选哪个 preset,vault 根**强制**含以下"基础设施"目录与文件,供本插件 hook/skill 依赖:

```
<vault-root>/
├── .obsidian/                     # Obsidian 本体配置 (用户管,本插件不动)
├── _meta/                         # 插件元数据 (用户可读不可改, 同步用)
│   ├── version.json               # vault schema 版本 + preset 类型
│   ├── lint-baseline.json         # lint 基线 (已知豁免)
│   └── migrations/                # 改版历史 (refactor 操作日志)
├── _templates/                    # 模板 (本插件 sync,用户可改)
│   ├── concept.md
│   ├── entity.md
│   ├── domain.md
│   ├── dashboard.md
│   ├── question.md
│   ├── source.md
│   └── _index.md
├── index.md                       # 根索引 (Dataview / 手维护)
├── hot.md                         # 热缓存 (近期上下文,SessionStart 注入)
├── log/                           # 会话日志 (Stop hook 写入)
│   ├── 2026-05/
│   │   ├── 10-1430-cortex-design.md
│   │   └── 10-1612-bug-fix-auth.md
│   └── _index.md
└── folds/                         # 折叠归档 (wiki-fold 输出)
    ├── 2026-05-fold-001.md
    └── _index.md
```

字段约定 (frontmatter, 全局必备):

```yaml
---
type: concept | entity | domain | dashboard | question | source | log | fold
title: <H1 一致>
aliases: []
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
preset: lyt | zettel | para | blank
---
```

#### 3.2.2 preset: LYT (Linking Your Thinking) — 默认

8-bucket + MOC 主导:

```
<vault-root>/
├── (共享根 同上)
├── 00_MOC/                        # Maps of Content (主索引节点)
│   ├── home.md
│   ├── topics-moc.md
│   └── projects-moc.md
├── 10_concepts/                   # 概念页 (永恒笔记)
├── 20_entities/                   # 实体 (人/工具/项目对象)
├── 30_domains/                    # 项目域 (按 git remote 命名)
│   └── github.com/<org>/<repo>/
│       ├── _domain.md
│       ├── decisions/
│       ├── bugs/
│       └── notes/
├── 40_sources/                    # 外部来源 (文章/书/视频)
├── 50_questions/                  # 待办问题 / 开放探索
├── 60_dashboards/                 # Dataview / Bases 仪表盘
├── 70_fleeting/                   # 临时笔记 (周期清理至上方)
└── 80_archive/                    # 归档 (主动弃用,不删)
```

#### 3.2.3 preset: Zettelkasten — 扁平 + UID

```
<vault-root>/
├── (共享根 同上)
├── zettels/                       # 全部笔记扁平在此
│   ├── 202605101430-claude-code-hooks.md
│   ├── 202605101612-obsidian-vault-layout.md
│   └── ...
├── structure-notes/               # Folgezettel / 结构笔记 (类 MOC)
│   ├── claude-code.md
│   └── pkm.md
├── inbox/                         # 待整理
└── references/                    # 文献卡 (类 source)
```

UID 规则: `YYYYMMDDHHMM-<slug>.md`,frontmatter 必含 `uid` 字段。

#### 3.2.4 preset: PARA

```
<vault-root>/
├── (共享根 同上)
├── 1_projects/                    # 有截止日的活跃项目
│   └── <project-name>/
├── 2_areas/                       # 持续职责领域 (无截止)
│   └── <area-name>/
├── 3_resources/                   # 主题资源库
│   └── <topic>/
└── 4_archive/                     # 已完成/弃置
```

#### 3.2.5 preset: blank (最小骨架)

仅共享根,不预设业务目录;由用户自决。适合已有 vault 接入。

#### 3.2.6 改版 (preset 切换 / schema 升级)

`/cortex:refactor` 子命令 `migrate-preset` 支持 LYT ↔ PARA 双向迁移。所有 move/rename 写入 `_meta/migrations/<timestamp>.json`,记录 `from → to` 映射,可回滚。schema 升级 (`_meta/version.json` bump) 由 `/cortex:doctor --upgrade` 触发,带 dry-run。

#### 3.2.7 路径与命名规则

| 资源类型 | 路径模板 | 命名 |
|----------|----------|------|
| 概念 (LYT) | `10_concepts/<kebab-title>.md` | 小写连字符 |
| 项目域 | `30_domains/<host>/<org>/<repo>/<sub>.md` | 跟随 git remote |
| 会话日志 | `log/YYYY-MM/DD-HHMM-<slug>.md` | UTC,slug ≤ 40 字符 |
| Zettel | `zettels/YYYYMMDDHHMM-<slug>.md` | UID 必备 |
| 折叠归档 | `folds/YYYY-MM-fold-NNN.md` | NNN 三位序号 |
| 仪表盘 | `60_dashboards/<topic>-dashboard.md` | 后缀强制 `-dashboard` |
| 模板 | `_templates/<type>.md` | type 字面量 |

禁用字符: `: \ / | ? * < > "` (跨平台兼容);空格允许但不推荐。

---

## 4. 接口规格

### 4.1 plugin.json (核心字段)

```json
{
  "name": "cortex",
  "version": "0.1.0",
  "description": "Obsidian 知识库协作插件 — hooks 注入 + CLI/MCP 操作 + 模板/lint/refactor",
  "keywords": ["obsidian", "knowledge-base", "pkm", "wiki", "zettelkasten"],
  "agents": ["./agents/cortex-curator.md"],
  "skills": "./skills/",
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json",
  "license": "AGPL-3.0-or-later"
}
```

> 教训 (07e713d4 commit): **不写 noop hook**;hooks.json 只声明真正实现的事件。

### 4.2 hooks/hooks.json

```json
{
  "SessionStart": [
    { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.sh" }
  ],
  "Stop": [
    { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop.sh" }
  ]
}
```

#### session_start.sh 行为

1. 通过 `_lib/resolve_vault.sh` 解析 vault 路径 (env `OBSIDIAN_VAULT` > `~/.config/cortex/config.json` > 默认 `~/persons/knowledge/obsidian` > 不存在则 silent skip)
2. 若 vault 存在,输出 additionalContext (stdin JSON 协议):

```text
## Cortex 已连接

vault: <abs path>
hot cache: wiki/hot.md (前 50 行)
索引: wiki/index.md (条目数 N)

### 协作约定

非通用问题先调 `cortex-query` skill 搜库,确认无既有经验再开工。
非平凡发现完成后用 `cortex-save` skill 落档,目录:
- 项目特定 → wiki/domains/<project>/
- 通用概念 → wiki/concepts/
- 写入后同步 wiki/index.md 与 wiki/hot.md

不要直接文件操作,经 mcp__obsidian__* 或本插件 skill。
```

3. 若 vault 不存在,**沉默退出 0** (不报错,不阻断会话)

#### stop.sh 行为

1. 读取 `$CLAUDE_TRANSCRIPT_PATH` (CC 提供) 末尾 N 轮
2. 启发式判定: 是否产生"非平凡技术发现" (debug/decision/configuration/bug-fix 关键词命中)
3. 若是,调用 `cortex-save` skill 落档至 `wiki/log/YYYY-MM/HH-MM-<topic>.md`
4. 失败不阻断,日志写 `~/.cache/cortex/stop.log`

### 4.3 vault 路径解析 (resolve_vault.sh)

```text
resolve_order:
  1. $OBSIDIAN_VAULT (env)
  2. $XDG_CONFIG_HOME/cortex/config.json:.vault
  3. ~/.config/cortex/config.json:.vault
  4. ~/persons/knowledge/obsidian (默认)
  5. (auto-detect) 扫 ~/Documents ~/Library 找 .obsidian/ 目录,唯一则用
```

冲突时优先级高者胜;auto-detect 仅在前 4 项全 miss 时启用。

### 4.4 commands 详表

| 命令 | 入参 | 行为 |
|------|------|------|
| `/cortex:install [preset]` | `lyt`\|`zettel`\|`para`\|`blank` (默认 lyt) | 在 vault 写入 preset 目录 + 模板 + 种子 MOC |
| `/cortex:new <type> <title>` | type ∈ templates 之一 | 用对应模板生成新页,自动填 frontmatter (id/created/aliases) |
| `/cortex:search <q>` | query | `mcp__obsidian__obsidian_simple_search` + 摘要 |
| `/cortex:save` | (无) | 触发 cortex-save skill,手动落档当前会话 |
| `/cortex:lint [--fix]` | scope 可选 | 跑 lint rules,默认 dry-run |
| `/cortex:refactor` | 交互式 | rename/merge/split/fold 子流程 |
| `/cortex:cron <op>` | install\|status\|run | 打印 cron snippet / 列已注册 / 手跑一次 |
| `/cortex:doctor` | (无) | 检 vault / MCP / CLI / 模板 / 索引完整性 |

### 4.5 skills 详表

| skill | trigger 短语 (frontmatter) | 主流程 |
|-------|--------------------------|-------|
| `cortex-setup` | "set up cortex", "init vault", "/cortex:install" | preset 选择 → 写目录 → 写 hot/index → 报告 |
| `cortex-save` | "save this", "file this", "归档", "落档", "/cortex:save", Stop hook | 抽要点 → 选目录 → 写 page → 更新 index/hot/log → wikilink 回填 |
| `cortex-query` | "what do you know about", "查一下知识库", "/cortex:search" | hot 优先 → index → vector/simple search → 综合答 + 引用 |
| `cortex-ingest` | "ingest", "/cortex:ingest <path>" | 读源 → 抽实体/概念 → 多 page 落地 → log 记录 |
| `cortex-lint` | "lint", "wiki audit", "/cortex:lint" | 跑 rules.json → 报告 → (--fix 时自动改) |

### 4.6 lint rules (v1, 10 条)

| # | 规则 | 严重度 | 自动修复 |
|---|------|--------|----------|
| 1 | frontmatter 缺 `type` 字段 | error | 推断填入 |
| 2 | frontmatter 缺 `created` 字段 | warn | 用文件 mtime |
| 3 | wikilink 指向不存在页 (dead link) | error | 创建 stub 或标记 |
| 4 | orphan page (无入链且无 tag) | warn | 报告,人工处理 |
| 5 | 重复 alias 跨页 | error | 报告,人工合并 |
| 6 | hot.md 超 200 行 | warn | 截断+落 archive |
| 7 | log 单文件 > 2000 行 | warn | 触发 fold |
| 8 | index.md 未包含某 wiki/* 子目录 | warn | 自动补条目 |
| 9 | 标题 H1 与 frontmatter title 不一致 | warn | 同步 |
| 10 | 文件名含非法字符或与 alias 冲突 | error | 报告 |

### 4.7 模板美化策略 (md + 嵌入 HTML)

约束: 仅嵌入**自包含 HTML 片段**(无 `<html>/<head>/<body>`),Obsidian 与 GitHub 都能渲染。

#### concept.md 范例骨架

```markdown
---
type: concept
title: <Title>
aliases: []
tags: []
created: 2026-05-10
updated: 2026-05-10
---

# <Title>

<div style="display:flex;gap:12px;flex-wrap:wrap;margin:8px 0">
  <div style="flex:1;min-width:200px;padding:10px;border-left:3px solid #3b82f6;background:#f0f7ff">
    <strong>一句话定义</strong><br/>
    <span>...</span>
  </div>
  <div style="flex:1;min-width:200px;padding:10px;border-left:3px solid #10b981;background:#f0fdf4">
    <strong>关键场景</strong><br/>
    <span>...</span>
  </div>
</div>

## 背景
## 核心要点
## 与相关概念对比
## 引用来源
```

#### dashboard.md 范例骨架

包含 Dataview 查询块 + HTML grid 卡片,详见 `templates/dashboard.md`。

---

## 5. 关键决策记录 (ADR-style)

| ID | 决策 | 理由 |
|----|------|------|
| D1 | 不依赖 ccplugin 的 `lib/` 与 pyproject | 用户硬约束;插件自包含便于发布到 marketplace |
| D2 | hooks 仅注册 SessionStart + Stop | 教训 07e713d4: noop hook 引入维护成本;v1 只做有真实工作的钩子 |
| D3 | cron 不自动注册 | 跨平台差异大,自动写用户 crontab/launchd 风险高;只打印 snippet 由用户复制 |
| D4 | v1 砍 skill 至 5 个 | 借鉴 claude-obsidian 11 skill 经验,defuddle/canvas/bases 已有全局 skill,本插件不重复 |
| D5 | 模板使用纯 md + 内嵌 HTML | 不引第三方 viewer 依赖;Obsidian 与 GitHub 双兼容 |
| D6 | preset 多套并行 (LYT/Zettel/PARA/blank) | 主流 PKM 方法论无单一赢家;让用户自选,降低落地阻力 |
| D7 | MCP 主 + CLI fallback | mcp__obsidian__* 覆盖 95% CRUD;canvas/bases 才回退 CLI |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Stop hook 误判 → 写入大量低价值 log | Cortex 噪音 | 启发式 + 关键词白名单;默认 dry-run,首次跑出 report 让用户确认 |
| 多 vault 用户路径解析错乱 | 写错位置 | resolve_vault 5 段优先级 + `/cortex:doctor` 显示当前选中 |
| Obsidian MCP server 未配置 | 命令全失败 | `/cortex:doctor` 给出 .mcp.json 配置示例;skill 内 graceful degrade 到 CLI |
| lint --fix 误改用户内容 | 数据损坏 | 默认 dry-run;`--fix` 前强制 git 检查;改动前 backup 至 `.cortex-backup/` |
| AGPL-3.0 下游兼容 | 集成阻力 | 与 ccplugin 现有插件一致,无新风险 |

---

## 7. 里程碑

| 阶段 | 交付 | 工时估 |
|------|------|--------|
| M0 design (本文档) | prd.md + research/*.md + 骨架决策 | done |
| M1 skeleton | plugin.json + 空目录 + README + AGENT.md + doctor command | 0.5 d |
| M2 setup + presets | install command + 4 套 preset + 6 个模板 | 1 d |
| M3 hooks | SessionStart + Stop + resolve_vault | 1 d |
| M4 core skills | save / query / ingest | 2 d |
| M5 lint + refactor | lint 10 rules + refactor 子流程 | 1.5 d |
| M6 cron + dashboard | cron snippet + dashboard 模板 + fold | 1 d |
| M7 polish + docs | quality-check + AI 识别验证 + 上架 marketplace.json | 0.5 d |

合计 ~7.5 d。

---

## 8. 验收标准

- `/cortex:doctor` 在干净环境一键给出诊断
- `/cortex:install lyt` 在新 vault 写出可用骨架,Obsidian 打开即可用
- SessionStart 注入在 vault 缺失时**沉默**,存在时输出预期 hot 摘要
- Stop hook 在显式启用后,有非平凡技术发现的 session 100% 落档
- `/cortex:lint` 对一个种子坏 vault 产出 ≥8/10 规则命中
- 通过 CLAUDE.md 规定的 GLM-4.5-flash 验证: 命令/skill 描述能被 AI 正确识别
- 不依赖 `lib/`;`uv sync` 在仓库根成功;插件本目录 `python -m compileall` 通过

---

## 9. 关联

- 研究 (4 份):
  - `research/01-obsidian-pkm-patterns.md` — PKM 方法论 + 8-bucket vault 布局
  - `research/02-ccplugin-arch-baseline.md` — 本仓库插件骨架基线
  - `research/03-obsidian-deep-capabilities.md` — Obsidian 原生 + 19 社区插件能力地图
  - `research/04-claude-code-deep-capabilities.md` — CC hook v2 schema + 21 事件 + plugin.json 全字段
- 参考实现 (本地, 仅借鉴): `~/.claude/plugins/marketplaces/claude-obsidian-marketplace/`, `~/.claude/plugins/marketplaces/omob/plugins/oh-my-obsidian/`, `~/.claude/plugins/marketplaces/obsidian-skills/`, `~/.claude/plugins/cache/megaphone-tokyo/kioku/0.7.0/`
- ccplugin 内骨架参考: `plugins/tools/deepresearch/`, `plugins/tools/codex/`, `plugins/tools/git/.claude-plugin/plugin.json`, `plugins/tools/notify/` (多事件 hook)
- 教训 commit: 07e713d4 (移除全部语言插件 hooks 机制)

---

## 10. Research-driven 增量补丁 (覆盖 §3-§4 早期描述)

> 后于本节出现的规则**优先**于前文。前文保留可读骨架,本节落地实证决策。

### 10.1 Hook 协议 — 必须 v2 wrapped JSON (research/04 §1)

stdout 不再是 plain text additionalContext, 改为:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "..."
  }
}
```

证据: `~/.claude/plugins/cache/megaphone-tokyo/kioku/0.7.0/hooks/wiki-context-injector.mjs:1-10`。`additionalContext` 软上限 ~10KB, cortex 注入 hot.md + index.md 时各自 truncate 至 5KB。

### 10.2 Hook 事件扩展 (覆盖 §4.2)

v1 钩子从 2 个升至 5 个 (matcher 细分):

| 事件 | matcher | 行为 |
|------|---------|------|
| SessionStart | `startup,resume,clear` | 注入 hot 摘要 + 协作约定 (compact 时跳过避免叠加) |
| PostCompact | * | 把 compact summary 落到 `wiki/log/YYYY-MM/DD-HHMM-compact.md` |
| PreToolUse | `mcp__obsidian__obsidian_delete_file` | 二次确认 (返回 permission decision `ask`) |
| PostToolUse | `mcp__obsidian__obsidian_(append_content\|patch_content)` | 跑微 lint (单文件 frontmatter / wikilink dead check) |
| Stop | * | 启发式落档 + auto block-id |
| SubagentStop | * | 子 agent 完成时若产出技术结论, 同样落档 (与 Stop 共享 routine) |

注: 21 事件清单完整版见 research/04 §A; 1-12 官方样本可证, 13-21 仅本仓库 `notify` 列出 (可能 fork 自定义), cortex v1 不依赖。

### 10.3 模板美化策略 — 用 callout, 弃 HTML grid (research/03 §A)

Obsidian callout 13 类原生支持 + foldable + GitHub 渲染兼容, 替代 §4.7 嵌入 HTML 卡片。

```markdown
> [!info]+ 一句话定义
> ...

> [!tip] 关键场景
> ...

> [!warning]- 已知陷阱 (折叠)
> ...
```

HTML grid 仅在 callout 表达不了的多列布局场景保留 (e.g. dashboard 顶部 KPI 4 卡片)。

### 10.4 Bases 优先, Dataview 兜底 (research/03 §A.Bases)

Obsidian 1.7+ 已将 Bases 列为核心,本机 1.12.7 已启用。dashboard 模板默认产出 `.base` 文件 + 内嵌视图;Dataview 仅当 `_meta/version.json:.bases_enabled = false` 时兜底。

`obsidian base:query` CLI 可离线取 JSON 结果,`/cortex:dashboard` 命令可纯命令行刷新。

### 10.5 block-id 自动注入 (research/03 §A.BlockID)

Stop / SubagentStop 落档时,每个 H2/H3 段落末尾自动加 `^cortex-<sha8>`:

```markdown
## 决策

选 Bases 而非 Dataview, 因 1.7+ 核心化。 ^cortex-a3f9c1d2
```

后续 fold / 引用可精准到段:`![[log/...#^cortex-a3f9c1d2]]`。

### 10.6 命令/Skill 集合扩展 (M5+M6 已落地)

实际落地: **0 commands**, 全部能力以 skill 暴露 (与早期描述差异, 见 AGENT.md 设计原则)。

skill 表 (M5/M6 新增 5 个, 总数 11):

| skill | 触发 | 实现路径 |
|-------|------|------|
| `cortex-lint` | "wiki audit", "lint", "vault 体检", "找 orphan", "dead link" | `lint/run.py` + `lint/rules.json` (13 rules) |
| `cortex-refactor` | rename/merge/split/fold (显式, disable-model-invocation) | `refactor/{rename,merge,split,fold}.py` + `_common.py` |
| `cortex-canvas` | "make canvas", "新建画布", "可视化" | obsidian CLI 主, JSON Canvas 1.0 静态降级 |
| `cortex-dashboard` | "build dashboard", "wiki 仪表盘", "仪表盘" | Bases 主 + Dataview 兜底 |
| `cortex-fold` | "fold logs", "归档日志", "整理日志" | 调 `refactor/fold.py` |

dashboard 命名为独立 skill 取代 §10.6 早期的 `cortex-bases` (Bases / Dataview 由内部探测自动选择, 不暴露选择给 LLM)。

### 10.7 Smart Connections 三级回退 (research/03 §B.SC)

```
1. SC REST API (port 27124) — 语义近邻 top-K
2. mcp__obsidian__obsidian_simple_search — 关键词
3. ripgrep on vault path — 兜底
```

Smart Connections 实际模型在本机为 `bge-micro-v2` (非 bge-m3),代码不要 hardcode 模型名,通过 SC API `/embeddings/info` 探测。

### 10.8 与 Obsidian Git 协调 (research/03 §B.OGit)

cortex 写入后**不**自动 git commit。检测到 vault 中 `.obsidian/plugins/obsidian-git/data.json` 存在则:
- 关闭本插件 auto-commit
- 在 stop.sh 输出末尾追加 `<!-- cortex-pending-commit -->` 标记,让 OGit 下次同步带上

### 10.9 lint 规则增至 13 条

新增 (在 §4.6 基础上):

| # | 规则 | 严重度 | 自动修复 |
|---|------|--------|----------|
| 11 | block-id 重复 | error | 重哈希 |
| 12 | callout 类型不在白名单 (13 类 + custom) | warn | 报告 |
| 13 | 文件路径不符合 §3.2.7 命名规则 | warn | rename 提案 |

### 10.10 plugin.json 增字段 (research/04 §B)

```json
{
  "name": "cortex",
  "outputStyles": "./styles/",
  "lspServers": null,
  "mcpServers": null
}
```

`outputStyles/` 提供一个 `cortex-mode` 样式 (SessionStart 注入,启用时强化"先搜库"协作约定)。`mcpServers` 不在 plugin 内声明,由用户 `.mcp.json` 配 obsidian server (cortex 提供示例片段而不写)。

### 10.11 statusLine 集成 (research/04 §H)

可选 statusline 组件 `statusline/cortex.sh`:输出 `📚 vault: <name> · 📝 N pending · ⚠ M lint`。用户在 `~/.claude/settings.json:statusLine.command` 引用,本插件不写 user settings。

### 10.12 allowed-tools 语法纠偏 (research/04 §F)

- skill 的 SKILL.md frontmatter `allowed-tools` 用**空格**分隔
- command .md frontmatter `allowed-tools` 用**逗号**分隔

cortex 模板与代码生成器统一封装一个 `_lib/allowed_tools.sh` 处理两套语法,避免散落踩坑。

### 10.13 sub-agent worktree 隔离 (research/04 §E)

`/cortex:refactor` 大批量 rename/move 操作走 sub-agent + `isolation: "worktree"`,失败可丢弃整个 worktree, vault 不留半成品。

### 10.14 持久化输出 / 文件状态追踪 (research/04 §H)

cortex skill 输出大于 10KB 时自动落 `_meta/cortex-runs/<ts>.md`,主对话仅返回 path + 摘要。借助 CC 自带 persisted-output 机制实现, 不重造。
