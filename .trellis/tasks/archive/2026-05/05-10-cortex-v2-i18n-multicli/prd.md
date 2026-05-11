# PRD — cortex (单一版本, 取代 v1)

> 状态: design draft · 创建 2026-05-11 · owner nico
> 研究: `research/01-claude-code-programmatic.md` · `research/02-vault-i18n-naming.md`
> 注: 仓库内永远只保留**当前**这份设计, 无版本号, 无迁移, 无兼容层。直接覆盖 `plugins/tools/cortex/`。

---

## 1. 范围与不做

### 1.1 本次范围 (相对现有 cortex 的 6 项变更)

1. **去目录编号** — vault preset 全去 `00_` `10_` `20_` 前缀
2. **i18n vault** — 目录/文件名按 vault 语言生成 (locales/<lang>.yml 驱动); 专有名词保留英文
3. **session 备份** — vault/sessions/<cli>/<YYYY-MM>/ 持久化原始 transcript
4. **多 CLI 数据库 schema** — vault 结构与 frontmatter 设计为 CLI-agnostic; runtime hooks/skills 仅 Claude Code, 但 vault 数据可被未来 codex/copilot/gemini adapter 读写
5. **skills 深化** — 7 项具体改进 (见 §6)
6. **新增 8 个专用 agents** — cortex-{curator, researcher, translator, historian, cartographer, archivist, linker, summarizer}
7. **(增量需求) 编程式调用 + cron 注册** — 提供日常维护 bash 脚本骨架 (走 `claude --bare -p`); install 时询问用户是否注册系统定时任务

### 1.2 不做

- 不写迁移工具, 不保 v1 vault 数据
- 不为 codex/copilot 写 hook (vault 结构兼容 = 数据兼容, 不是运行时兼容)
- 不实现 vault 内多 lang 子树 (一个 vault 一个 lang)
- 不自动改 alias 双语 (按需 `cortex-save` 提议, 由用户接受)

---

## 2. 架构总览

```
┌────────────────────────────────────────────────────────────────────┐
│ runtime: Claude Code only                                          │
│   SessionStart  → 注入 vault lang + hot 摘要                        │
│   Stop / SubagentStop / PostCompact → 调度 cortex-save              │
│   skills (15+) / agents (8)                                        │
│                              │                                     │
│                              ▼ MCP / CLI                           │
└──────────────────────────────────────┬─────────────────────────────┘
                                       │
                       ┌───────────────▼────────────────┐
                       │ vault (CLI-agnostic)           │
                       │   _meta/version.json:.lang     │
                       │   locales/<lang>.yml override  │
                       │   sessions/<cli>/<YYYY-MM>/    │
                       │   <localized dirs>/            │
                       │   <localized.md>               │
                       └────────────────────────────────┘
                                       ▲
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
        cron / launchd           future: codex            future: copilot
       (claude --bare -p)         adapter (read)         adapter (read)
```

cron/maintenance: 走 `claude --bare -p` 编程式调用本插件 skill, 触发 lint / fold / dashboard。

---

## 3. vault 目录结构 (去编号 + i18n)

### 3.1 共享根 (语言无关, 全 ASCII / 通行术语)

```
<vault-root>/
├── .obsidian/                # Obsidian 自管
├── _meta/
│   ├── version.json          # {"lang":"zh-CN","preset":"lyt","created":"..."}
│   ├── lint-baseline.json
│   ├── migrations/           # refactor 操作日志
│   ├── .cortex-backup/       # lint --fix / refactor 备份
│   └── locales/              # 用户级 lang 覆盖 (可选)
├── _templates/               # 模板 (cortex-install 复制)
├── locales/                  # vault 级 lang 覆盖 (可选, 高于插件内置)
├── sessions/                 # 多 CLI session 备份 (新)
│   ├── claude-code/
│   │   └── 2026-05/
│   │       ├── 11-1430-<slug>.jsonl       # 原始 transcript
│   │       └── 11-1430-<slug>.tar.gz      # 可选打包
│   ├── codex/                # 未来扩展
│   └── copilot/
├── index.md                  # 根索引 (硬编码 ASCII)
├── hot.md                    # 热缓存 (硬编码 ASCII)
├── log/                      # 提炼后笔记 (硬编码 ASCII)
│   └── YYYY-MM/DD-HHMM-<slug>.md
└── folds/                    # 月度滚动归档 (硬编码 ASCII)
    └── YYYY-MM-fold-NNN.md
```

### 3.2 业务目录 (按 vault.lang 渲染, 去编号)

LYT preset 默认目录映射:

| 英语 (key) | zh-CN | en | ja | 备注 |
|------------|-------|-----|-----|------|
| `moc` | `MOC` | `MOC` | `MOC` | LYT 通行术语, 不译 |
| `concepts` | `概念` | `concepts` | `概念` | |
| `entities` | `实体` | `entities` | `エンティティ` | |
| `domains` | `领域` | `domains` | `領域` | 子目录 git remote 路径不译 |
| `sources` | `来源` | `sources` | `ソース` | |
| `questions` | `问题` | `questions` | `質問` | |
| `dashboards` | `仪表盘` | `dashboards` | `ダッシュボード` | |
| `fleeting` | `临时` | `fleeting` | `走り書き` | |
| `archive` | `归档` | `archive` | `アーカイブ` | |

zh-CN LYT 样例:

```
<vault>/
├── (共享根 同 §3.1)
├── MOC/
│   ├── home.md
│   └── topics-moc.md
├── 概念/
├── 实体/
├── 领域/
│   └── github.com/<org>/<repo>/   # remote 路径硬编码
│       ├── _domain.md             # _domain 硬编码
│       └── decisions/             # decisions/bugs/notes 也走 lang map
├── 来源/
├── 问题/
├── 仪表盘/
├── 临时/
└── 归档/
```

英文 LYT 样例:

```
<vault>/
├── MOC/
├── concepts/
├── entities/
├── domains/
├── sources/
├── questions/
├── dashboards/
├── fleeting/
└── archive/
```

### 3.3 i18n 不翻译白名单

硬编码 ASCII / 通行术语 (locales 不允许覆盖):
- 基础设施: `_meta` `_templates` `locales` `sessions` `index` `hot` `log` `folds`
- 子结构: `_domain` (领域索引) · `_index` (子目录索引)
- LYT 术语: `MOC`
- 时间格式: `YYYY-MM` · `YYYY-MM-fold-NNN` · `DD-HHMM`
- block-id: `^cortex-<sha8>`
- frontmatter 字段: `type` `title` `aliases` `tags` `created` `updated` `preset` `cli` `cli_session` `lang`
- git remote 路径: `<host>/<org>/<repo>/`
- 时间格式 / 序号: `NNN` 三位

### 3.4 文件名规则

- 编码: NFC 规范化 (跨平台 git 安全)
- 跨平台禁用字符: `: \ / | ? * < > "` + Obsidian 特殊禁字 `[ ] # ^`
- 长度: ≤ 100 字节 (UTF-8)
- 大小写: 保留 vault.lang 自然写法 (zh-CN 中文不变, en 推荐 kebab-case)
- 文件路径模板 (locale-aware):

| 资源 | 路径模板 (键) |
|------|--------------|
| 概念 | `concepts/<title>.md` |
| 实体 | `entities/<title>.md` |
| 领域 | `domains/<host>/<org>/<repo>/<sub>.md` |
| 仪表盘 | `dashboards/<topic>-dashboard.md` (后缀 ASCII) |
| 临时 | `fleeting/YYYY-MM-DD-<slug>.md` |
| log | `log/YYYY-MM/DD-HHMM-<slug>.md` |
| fold | `folds/YYYY-MM-fold-NNN.md` |
| session | `sessions/<cli>/YYYY-MM/DD-HHMM-<slug>.{jsonl,tar.gz}` |

`<key>` 部分由 `locales/<lang>.yml:dirs.<key>` 渲染。

---

## 4. locale 系统

### 4.1 文件位置 (按优先级)

```
1. <vault>/locales/<lang>.yml         # vault 级覆盖 (最高)
2. ~/.config/cortex/locales/<lang>.yml # 用户级覆盖
3. <plugin>/locales/<lang>.yml         # 插件内置 (最低)
```

### 4.2 schema (示例 zh-CN)

```yaml
# locales/zh-CN.yml
meta:
  lang: zh-CN
  fallback: en           # zh-CN miss → en
  display: 简体中文

dirs:
  moc: MOC               # 不翻译, 保持插件白名单一致
  concepts: 概念
  entities: 实体
  domains: 领域
  sources: 来源
  questions: 问题
  dashboards: 仪表盘
  fleeting: 临时
  archive: 归档

files:
  home: home             # 硬编码白名单, 不翻
  domain_index: _domain
  subdir_index: _index

agent_titles:
  curator: cortex 维护员
  researcher: cortex 研究员
  translator: cortex 译者
  historian: cortex 史官
  cartographer: cortex 制图员
  archivist: cortex 档案员
  linker: cortex 连接员
  summarizer: cortex 总结员

prompts:
  search_first: |
    非通用问题先调 cortex-search 搜库, 确认无既有经验再开工。
  archive_pending: 📝 cortex 已落档 {path}
```

### 4.3 fallback

`zh-CN` → `zh` → `en` → 报错。每个 key miss 单独 fallback (不整文件回退)。

### 4.4 SessionStart 注入语言

session_start.sh 输出 additionalContext 时, 头部固定一行:

```text
## Cortex 已连接 (lang=zh-CN, vault=/Users/.../obsidian, preset=lyt)
```

后续协作约定从 `prompts.search_first` 等键渲染, 用户不改 prompt 就**自动多语**。

### 4.5 切语言

`/cortex:locale set en`:
- 改 `_meta/version.json:.lang`
- **不**重命名既有目录 (lint v2 规则下仅 info)
- 此后 cortex-new / cortex-install 新建项走新 lang
- 用户可主动跑 cortex-refactor migrate-locale (新增 sub-op) 一次性 rename

---

## 5. 多 CLI database schema

### 5.1 frontmatter (新增 2 字段)

```yaml
---
type: log
title: ...
created: 2026-05-11
updated: 2026-05-11
preset: lyt
lang: zh-CN
cli: claude-code               # 新: 来源 CLI
cli_session: a1b2c3d4-...      # 新: 会话 id (CC 即 sessionId)
---
```

`cli` 枚举: `claude-code` · `codex` · `copilot` · `gemini` · `qoder` · `kiro` · `manual`。

### 5.2 sessions/<cli>/<YYYY-MM>/

每次 Stop / SubagentStop / PostCompact hook 触发后:
1. 复制原始 transcript JSONL → `sessions/<cli>/<YYYY-MM>/<DD-HHMM>-<slug>.jsonl`
2. 可选 (config.preserve_archive=true) → `.tar.gz` 打包
3. 提炼版仍写 `log/`, frontmatter `cli` / `cli_session` 指回

### 5.3 跨 CLI 查询

cortex-search L4 (MCP simple_search) 支持 `path:sessions/codex/` 等过滤。frontmatter dataview 可:

```dataview
TABLE cli, cli_session, created
FROM "log"
WHERE cli = "claude-code" AND created > date("2026-05-01")
```

---

## 6. skills 深化 (15+ skill, 8 specialized agents)

### 6.1 现有 11 skill 升级

触发模式 (auto = 自动调用; **explicit** = `disable-model-invocation: true`, 仅用户显式触发):

| skill | 触发 | v2 增项 |
|-------|------|---------|
| cortex-install | **explicit** | 询问 lang (zh-CN/en/ja/...) + 询问 cron 注册 (见 §8); 写 `_meta/version.json:.lang` |
| cortex-search | auto | 加 `--lang` 参数 (跨语言搜); SC fallback 用 vault.lang model 探测 |
| cortex-save | auto | frontmatter 自动塞 `cli` / `cli_session` / `lang`; 路径用 locale 渲染 |
| cortex-ingest | auto | 来源页 frontmatter `cli: manual`; URL 来源用 defuddle skill 协作 |
| cortex-doctor | **explicit** | 加检查 locales 文件存在 / lang fallback 链 / sessions/ 占用 |
| cortex-new | **explicit** | 路径模板按 lang 渲染; 询问 `--lang` 覆盖 |
| cortex-lint | auto | rules 加 i18n-001 (frontmatter `lang` 与 vault.lang 不一致) / i18n-002 (路径不在 lang map 内); rule 13 (path-naming) 调整为"路径不在 dirs map" |
| cortex-refactor | **explicit** | 加子操作 `migrate-locale` (一次性 rename 既有目录到新 lang) |
| cortex-canvas | **explicit** | 节点 label 走 lang map |
| cortex-dashboard | **explicit** | dataview 列名走 lang map |
| cortex-fold | **explicit** | fold 文件名 ASCII (`YYYY-MM-fold-NNN.md`); 内容头部用 lang map |

### 6.2 新增 skill (3 个)

| skill | 触发 | 说明 |
|-------|------|------|
| `cortex-locale` | **explicit** ("切换语言" / "set vault lang") | 读/写 `_meta/version.json:.lang`, 列已加载 lang fallback |
| `cortex-session` | auto ("list sessions" / "session 备份") | 列 sessions/, 解析任意 transcript, 重放摘要 |
| `cortex-cron` | **explicit** ("register cron", install 问到时调用) | 检测 launchd / cron / GHA 平台, 询问注册项, 写或仅打印 |

合计 14 skill: **5 auto** (search/save/ingest/lint/session) + **9 explicit** (install/locale/fold/canvas/dashboard/doctor/new/refactor/cron)。description 池仅 auto skill 进, 现状 722 字符 (软上限 1536, 余裕充足)。

### 6.3 8 specialized agents

agent 与 skill 区别: agent 是**有计划的多轮调用者**, 接任务后自主跑多 skill 完成。每个 agent 是 `agents/<name>.md` 单文件, frontmatter 含 `name / description / tools / model`。

| agent | 角色 | 主调度 |
|-------|------|--------|
| `cortex-curator` | 维护员: 周期扫 vault, 提 orphan / dead-link / 老 fleeting 笔记的修复方案 | cortex-lint → 解读 → cortex-refactor 提议 |
| `cortex-researcher` | 研究员: 接领域问题 → 多 source 抓取 → 入库 + 汇总多页 | cortex-search → defuddle → cortex-ingest × N → cortex-summarizer |
| `cortex-translator` | 译者: 单页或目录跨 lang 翻译, 保 wikilink | cortex-search → 翻译 → cortex-save (新 lang 副本) |
| `cortex-historian` | 史官: 读 sessions/<cli>/ 多月份, 提炼季度变迁, 写 folds/ | cortex-session → cortex-summarizer → cortex-fold |
| `cortex-cartographer` | 制图员: 生成/维护 MOC + canvas + dashboard | cortex-canvas → cortex-dashboard → 写 MOC/ |
| `cortex-archivist` | 档案员: fleeting 老化 → archive/concept/source 迁移提案 | cortex-search → cortex-refactor (move) |
| `cortex-linker` | 连接员: SC 找近邻 → 提议 `[[X]]` 增链 | SC API → cortex-search → cortex-save (patch wikilinks) |
| `cortex-summarizer` | 总结员: 长页 / 领域 TL;DR + callout 注入 | 读页 → 调主模型生成 → patch 页头 |

8 agent 全部 `name: cortex-*` 前缀, 与 skill 命名空间统一。

---

## 7. 编程式 Claude Code + cron

### 7.1 调用范式 (research/01 落地)

```bash
claude --bare \
       --settings ~/.claude/settings.glm-4.5-flash.json \
       --output-format stream-json \
       -p "<prompt>" \
  | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

要点 (research/01 §C-§E):
- `--bare` 关 SessionStart hook + caveman prompt 等用户全局注入, 仅 init/assistant/result 三段
- `--no-session-persistence` 防 transcript 写盘
- `--allowed-tools` 收紧权限 (cron 多用 `Bash Read Glob`)
- `--strict-mcp-config --mcp-config <file>` 限定 MCP server 集合
- 退出码不可信 → 必查 `result.is_error`

### 7.2 cron 维护脚本 (插件提供 3 个)

`scripts/cron/` (新):

```
scripts/cron/
├── run.sh                       # 通用 wrapper: 锁文件 + 超时 + 日志切片
├── lint.sh                      # daily — claude --bare -p "lint vault"
├── fold.sh                      # weekly — claude --bare -p "fold logs"
└── dashboard.sh                 # weekly — claude --bare -p "refresh dashboards"
```

每脚本支持 `--dry-run` `--vault <path>` `--lang <lang>`。

### 7.3 install 时询问 cron 注册

cortex-install 流程末尾新增:

```
[6/6] 周期任务
  daily   01:00 lint     [Y/n]
  weekly  Sun 02:00 fold [Y/n]
  weekly  Sun 02:30 dash [Y/n]

注册到? [launchd/cron/gha/none]
```

接受非 none → 调 cortex-cron skill 写入对应平台 (写前先 `--dry-run` 给用户确认)。

### 7.4 cortex-cron skill

平台检测顺序:
1. macOS → launchd plist (`~/Library/LaunchAgents/dev.lazygophers.cortex.<job>.plist`)
2. Linux → systemd user timer 或 crontab 行
3. CI 环境 → 输出 GHA workflow yaml, 不自动写

危险操作前一律 dry-run + 用户确认。卸载: `cortex-cron uninstall`。

---

## 8. 插件目录骨架 (取代现 plugins/tools/cortex/)

```
plugins/tools/cortex/
├── .claude-plugin/plugin.json
├── README.md
├── AGENT.md
├── docs/                         (中文 14 篇, 续写 i18n / 多 CLI / agents / cron 章)
├── locales/
│   ├── zh-CN.yml
│   ├── en.yml
│   └── ja.yml
├── hooks/
│   ├── hooks.json
│   ├── session_start.sh         (注入 lang)
│   ├── stop.sh
│   ├── post_compact.sh
│   └── _lib/
│       ├── resolve_vault.sh
│       ├── locale.py            (新: locale 加载 + fallback)
│       ├── save_session.py      (写 sessions/<cli>/...)
│       └── backlink_sync.py
├── skills/                       14 skills
│   ├── cortex-{install,search,save,ingest,doctor,new,lint,refactor,canvas,dashboard,fold}/SKILL.md
│   └── cortex-{locale,session,cron}/SKILL.md      新
├── agents/                       8 specialized agents
│   ├── cortex-curator.md
│   ├── cortex-researcher.md
│   ├── cortex-translator.md
│   ├── cortex-historian.md
│   ├── cortex-cartographer.md
│   ├── cortex-archivist.md
│   ├── cortex-linker.md
│   └── cortex-summarizer.md
├── templates/                    6 模板 (内含 lang/cli/cli_session 字段占位)
├── presets/
│   ├── lyt/_structure.json       (dirs 字段引用 locale key, 不再硬编码中文/英文)
│   ├── zettel/_structure.json
│   ├── para/_structure.json
│   └── blank/_structure.json
├── lint/
│   ├── rules.json                (15 条: 13 现有 + i18n-001/002)
│   └── run.py
├── refactor/
│   ├── _common.py
│   ├── rename.py
│   ├── merge.py
│   ├── split.py
│   ├── fold.py
│   └── migrate_locale.py         新
└── scripts/
    ├── install_cron.sh           (现存, 只打印 snippet)
    └── cron/
        ├── run.sh                新
        ├── lint.sh
        ├── fold.sh
        └── dashboard.sh
```

`presets/<name>/_structure.json` schema 改为引用 locale key:

```json
{
  "preset": "lyt",
  "version": "1.0",
  "directories_keys": ["moc", "concepts", "entities", "domains", "sources", "questions", "dashboards", "fleeting", "archive"],
  "seed_files": [
    {"src": "seed/moc/home.md", "dst_key": "moc", "name": "home.md"}
  ]
}
```

`dst_key` 由运行时 locale 解析为实际目录名。

---

## 9. lint 规则 (10 → 15)

新增:
- 14: i18n-001 — 页 frontmatter `lang` 与 vault `_meta/version.json:.lang` 不一致 (warn, 不 autofix)
- 15: i18n-002 — 业务目录名不在 vault.lang 的 dirs map (warn; --fix 仅给出 rename 建议)

调整:
- 13 path-naming-violation: 检查范围改为"业务目录命名应来自 dirs map", 共享根目录 (_meta/_templates/...) 与时间目录 (YYYY-MM) 跳过

---

## 10. 风险

| 风险 | 缓解 |
|------|------|
| CJK 文件名 git 跨平台 (HFS+ NFD vs APFS NFC) | 全 NFC 入库; `cortex-doctor` 提示 `git config core.precomposeunicode true` |
| sessions/ 体积膨胀 | 默认仅存提炼后 `log/`; 原始 transcript 备份默认关 (config.preserve_transcript=false), 用户开启自负责轮转 |
| locale 切换后 vault 半中半英 | lint i18n-002 报告 + cortex-refactor migrate-locale 提案 |
| install 自动写 launchd/cron | 强制 dry-run + 用户确认; 卸载脚本 |
| cron 任务跑 GLM-4.5-flash 误改 vault | 默认 `--allowed-tools Bash Read Glob` (只读); `--fix` 类操作不进 cron |
| 8 agent 描述池超 1536 字符 | agent 不进 description pool (skill 才进); agent 描述自由长度 |

---

## 11. 里程碑

| 阶段 | 内容 | 工时估 |
|------|------|--------|
| M0 design (本文档) | prd + 2 research | done |
| M1 vault schema 重写 | locales/{zh-CN,en,ja}.yml + presets/<>/_structure.json + locale.py + 模板 frontmatter | 1.5 d |
| M2 hooks 重写 | session_start lang 注入 + save_session sessions/<cli>/ + cli/cli_session 字段 | 1 d |
| M3 14 skills 升级 + 3 新 | 含 cortex-locale / cortex-session / cortex-cron | 2.5 d |
| M4 8 agents | curator/researcher/translator/historian/cartographer/archivist/linker/summarizer | 2 d |
| M5 lint 15 + refactor migrate-locale | rules + run.py + migrate_locale.py | 1 d |
| M6 cron 脚本 + install 询问 + 编程式调用 | scripts/cron/*.sh + cortex-install 末尾问询 | 1 d |
| M7 docs 中文文档增补 (i18n / agents / cron / 多 CLI) | docs/ 续写 4-6 篇 | 0.5 d |
| M8 polish + check | check.py + GLM 自检 + marketplace | 0.5 d |

合计 ~10 d。

---

## 12. 验收

- `uv run scripts/check.py -d plugins/tools/cortex` 通过
- `cortex-install lyt --lang zh-CN` 与 `--lang en` 各跑一遍, vault 目录命名正确
- 8 agent 全部能被 GLM-4.5-flash 识别用途与触发场景
- cortex-doctor 报告 lang 与 fallback 链
- cron 注册 dry-run + 实跑 (本地手测)
- sessions/claude-code/2026-05/<file>.jsonl 自动产生 (Stop hook)
- 跨平台 CJK 文件名: 在 macOS APFS + Linux ext4 各 git pull 一次, 无 normalization 冲突 (用 fixture 验证)

---

## 13. 关联

- 研究: `research/01-claude-code-programmatic.md` · `research/02-vault-i18n-naming.md`
- 旧设计 (仅参考, 不兼容): `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/`
- 本仓库 spec: `.trellis/spec/backend/{plugin-conventions,hooks-contract,quality-guidelines,marketplace}.md`
