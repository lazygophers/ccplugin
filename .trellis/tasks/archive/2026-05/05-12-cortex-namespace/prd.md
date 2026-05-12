# PRD — cortex 知识库 + 记忆体系 双 namespace 重构

## 1. 背景

现 cortex vault 单 namespace 结构 (8 中文桶: 概念/实体/领域/来源/问题/仪表盘/临时/归档) 在以下方面失败:

- 无明确职责拆分, 用户+AI 检索回报率低
- 缺 GitHub/website 来源组织
- 缺本地项目组织
- 缺预设领域 (用户每次自建, 命名不一致)
- 缺按天日志 + 自动归档
- 缺多级记忆, 没有重点和核心
- 缺格式化仪表盘
- 缺 HTML 内嵌 (人类友好查看)
- 缺记忆腐化治理

参考来源:
- [Nocturne Memory](https://linux.do/n/topic/1616409): URI 寻址 + 渐进披露 + 双前端 + 版本控制
- [10 年 AI 研究帖](https://linux.do/n/topic/1711075): 神经科学映射, working/short/hippocampus/cortex 多级
- [tdwhere 治理模型](https://linux.do/n/topic/2156133): Raw Ledger + Derived Views + Policy
- [Claude Code HTML 替代 Markdown](https://linux.do/t/topic/2138856): HTML 二维布局 token 反更省
- [PARA + Zettelkasten](https://forum.obsidian.md/t/91380): 主流社区融合
- [doumoman 1000 笔记甜区](https://forum-zh.obsidian.md/t/topic/57898): 手工管理上限

## 2. 目标

重设 cortex vault 为**双 namespace** 结构, 知识库 (人类组织) + 记忆体系 (AI URI 寻址 + L0-L4 分级)。补齐 9 大痛点, 引入治理管道。

### 不在范围
- 不动 plugin 安装机制 (install.sh / 配置文件)
- 不动现有 MCP server 已有工具签名 (仅追加新工具)
- 不动 i18n locales/*.yml (保留作 legacy)
- 现有 vault 迁移工具单独任务 (本次仅做新 vault 安装的目标态)

## 3. 设计

### 3.1 顶层结构

```
vault/
│
├── _meta/                        元数据 (version/policy/lint/uri-index)
├── _templates/                   模板 (含 HTML 片段库)
├── _assets/                      图片/svg/HTML 复用资源
│
├── 主页.md                       全局入口 (HTML 二维仪表盘)
├── 焦点.md                       当前焦点
│
├── 知识库/                       人类组织维度
├── 记忆体系/                     AI URI 寻址 + L0-L4 分级
├── 仪表盘/                       格式化看板 (HTML)
└── 归档/                         冷藏
```

### 3.2 知识库 (人类视角)

```
知识库/
├── 项目/                         本地项目
│   └── <name>/{_index.md,笔记/,决策/}
│
├── 来源/                         外部输入 (auto-route by host)
│   ├── 代码仓库/<host>/<org>/<repo>.md     (GitHub/GitLab/Gitee)
│   ├── 网页/<domain>/<slug>.md
│   ├── 论文/<year>/
│   └── 书籍/
│
├── 领域/                         7 大预设
│   ├── 技术/
│   │   ├── 编程语言/{Go,Python,Rust,JavaScript,TypeScript,Java,C++}/
│   │   ├── 数据库/{MySQL,PostgreSQL,Redis,MongoDB,ClickHouse,SQLite}/
│   │   ├── 基础设施/{Linux,Docker,Kubernetes,网络,安全}/
│   │   ├── 大数据/{Spark,Kafka,Flink,ETL,数据仓库}/
│   │   ├── 人工智能/{LLM,机器学习,Agent,Prompt,RAG,Embedding}/
│   │   ├── 前端/{React,Vue,CSS,Next.js,Tailwind}/
│   │   ├── 后端/{API,微服务,gRPC,REST}/
│   │   ├── 移动端/{iOS,Android,Flutter,ReactNative}/
│   │   └── 运维/{CI-CD,监控,SRE,可观测性}/
│   ├── 金融/{投资,经济,会计,税务}/
│   ├── 生活/{美食,旅游,健康,家居,穿搭}/
│   ├── 工作/{管理,沟通,职业}/
│   ├── 学习/{语言,读书,课程}/
│   ├── 创作/{写作,设计,音乐}/
│   └── 元学习/{知识管理,效率,思维框架}/
│
├── 日记/{日,周,月,年}/YYYY/MM/
├── 反思/{洞察,连接,疑问}/
└── 收件箱/YYYY-MM-DD/
```

命名规则:
- 一/二/三级中文, 四级 (具体技术) 保留专有名词 (Go/MySQL/React)
- `<host>/<org>/<repo>` 是数据 slug, 非"目录命名"

### 3.3 记忆体系 (AI URI 寻址 + L0-L4)

```
记忆体系/
│
├── L0-核心/                      不可篡改 (性格/价值观/硬约束)
│   ├── identity.md / user.md / values.md / habits.md / constraints.md
│   写入: needs_user_confirm=true + git tag + 不可遗忘
│
├── L1-长期/                      高 weight, 已固化
│   ├── procedural/<skill>.md     技能/流程
│   └── semantic-stable/<topic>.md 稳定语义
│   遗忘: 仅用户显式删除
│
├── L2-中期/                      语义, 可演化, 365 天时效
│   └── semantic/<topic>.md
│   遗忘: 365 天未召回 → archive
│
├── L3-短期/                      情节, 90 天时效
│   └── episodic/YYYY-MM-DD/
│   遗忘: 90 天未召回 → archive
│
├── L4-流水账/                    raw append-only
│   ├── ledger/YYYY-MM-DD.jsonl   事件流
│   └── sessions/<cli>/YYYY-MM/<sid>.md   claude code transcript
│   遗忘: 30 天后 gzip 压缩
│
├── working/                      当前 session (volatile, 不分级)
│   └── current.md
│
└── views/                        派生视图
    ├── recent.md / hot.md / candidates.md / alerts.md
    └── consolidated/<week>.md
```

### 3.4 URI 寻址

scheme:
```
L0://identity/me
L0://user
L1://procedural/git-commit-flow
L1://semantic-stable/pkm
L2://semantic/go/goroutine
L3://episodic/2026-05-12/T1430
L4://ledger/2026-05-12
L4://session/claude-code/sess-x
```

记忆 frontmatter:
```yaml
---
uri: L2://semantic/go/goroutine
level: L2
ref: 知识库/领域/技术/编程语言/Go/goroutine.md
weight: 0.7
recall_when: "用户提 Go 并发"
last_recalled: 2026-05-12T10:30:00Z
recall_count: 12
created: 2026-04-01
expires: 2027-04-01
parents: [L1://procedural/go-concurrency]
children: [L3://episodic/2026-05-12/T1430]
promote_eligible: false
archive_pending: false
---
brief: 一行摘要 (上下文塞这一行, 渐进披露)

full: |
  完整内容, 仅在 recall full 时返回
```

### 3.5 Raw Ledger + Derived Views + Policy

```
事件 ──→ L4-流水账/ledger/<date>.jsonl (append-only, immutable)
          │
          ↓ daily cron: AI 提炼
      L4 → L3 (情节)
          ↓ weekly: 重复模式
      L3 → L2 (语义)
          ↓ monthly: 稳定 + 高 weight
      L2 → L1 (长期)
          ↓ 用户审批必经
      L1 → L0 (核心)
```

`_meta/memory-policy.yaml`:
```yaml
levels:
  L0:
    write: {needs_user_confirm: true, git_tag: true, immutable_after_confirm: true}
    forget: {never: true}
    promote_from: [L1]
  L1:
    write: {min_weight: 0.8, ai_can_propose: true}
    forget: {only_user: true}
    promote_from: [L2]
    promote_criteria: {recall_count: ">= 20", stable_days: ">= 90"}
  L2:
    write: {min_weight: 0.5, dedupe: true}
    forget: {after_days: 365, unless_recalled: 5}
    promote_from: [L3]
    promote_criteria: {recall_count: ">= 5", recurrence: "weekly"}
  L3:
    write: {auto: true}
    forget: {after_days: 90, unless_recalled: 3}
    promote_from: [L4]
    promote_criteria: {ai_detected_pattern: true}
  L4:
    write: {append_only: true, immutable: true}
    forget: {compress_after_days: 30}
recall:
  default: {top_k: 5, progressive: true, level_order: [L0, L1, L2, L3]}
  L4_excluded_by_default: true
cron:
  enabled: true
  jobs:
    memory-promote:     {cron: "0 02 * * *",     enabled: true}
    memory-forget:      {cron: "0 03 * * *",     enabled: true}
    memory-compact:     {cron: "0 04 * * 0",     enabled: true}
    memory-consolidate: {cron: "30 04 * * 0",    enabled: true}
    memory-warden:      {cron: "0 05 1,15 * *",  enabled: true}
    memory-archive:     {cron: "0 06 1 * *",     enabled: true}
```

### 3.6 仪表盘 (HTML 二维布局)

```
仪表盘/
├── 总览.md                       全局 (HTML grid)
├── 知识库分布.md                 饼图 (按领域)
├── 记忆-L0-核心.md               不可篡改名册
├── 记忆-L1-长期.md               长期技能/稳定语义
├── 记忆-L2-中期.md               语义网络图
├── 记忆-L3-短期.md               情节时间线
├── 记忆-L4-流水.md               原始流 heatmap
├── 记忆-晋级候选.md              views/candidates.md
├── 记忆-腐化监控.md              幻觉/漂移/反馈自增强
├── 知识-记忆 桥接.md             ref 双向链接图
├── 记忆-cron 状态.md             各 cron 执行状态
└── 固化流.md                     L4→L0 mermaid sankey
```

`_templates/html/` 片段库:
- `badge.html` / `card.html` / `timeline.html`
- `mermaid-flowchart.md` / `mermaid-sankey.md` / `mermaid-mindmap.md`
- `canvas-heatmap.html` / `progressive-disclosure.html`

## 4. Skills/Agents/MCP 改造

### 4.1 Skills 改造
| Skill | 改造 |
|-------|------|
| `cortex-install` | 安装双 namespace + URI index + memory-policy + 7 大领域预设 + HTML 模板 + 9 cron jobs |
| `cortex-search` | 双源: 知识库全文/语义 + 记忆 URI 解析 + recall_when 匹配 |
| `cortex-ingest` | 路由 URL → 知识库/来源 + L4/ledger 记录 + 候选 semantic 推荐 |
| `cortex-save` | 加 memory: 字段 + URI 分配 |
| `cortex-translator` | 不变 |

### 4.2 Skills 新增
| Skill | 职责 |
|-------|------|
| `cortex-memory` | 记忆 CRUD (URI 寻址 + 版本控制) |
| `cortex-recall` | 渐进披露召回 (返父节点 + 子目录, 不全量) |
| `cortex-consolidate` | ledger → views, episodic → semantic 巩固 |
| `cortex-forget` | 按 policy 遗忘 |
| `cortex-session` | 导入 claude code transcript → L4-流水账/sessions/ |
| `cortex-html` | 生成 HTML 片段 (badge/card/timeline/mermaid) |
| `cortex-dashboard` | 渲染仪表盘 (Bases query + HTML 拼装) |
| `cortex-reflect` | DMN: 跨领域综合 → 知识库/反思/ |
| `cortex-promote` | AI 提议晋级 → 用户审批 (L1→L0 必须) |

### 4.3 Skills 删除
- `cortex-fold` (并入 cortex-consolidate)
- `cortex-cron` (已并入 cortex-install)

### 4.4 Agents 改造
| Agent | 职责 |
|-------|------|
| `cortex-curator` | audit 知识库 + 记忆腐化检测 |
| `cortex-archivist` | 归档 episodic >90, 知识库 >6 月未访问 |
| `cortex-historian` | sessions + ledger 多月汇总 → views/consolidated/ |
| `cortex-linker` | 记忆 URI ↔ 知识库 路径双向链接 |
| `cortex-researcher` | 多源抓 → 知识库/来源 + 记忆候选 |
| `cortex-summarizer` | 长页 TL;DR + HTML callout |
| `cortex-cartographer` | MOC / canvas / dashboard 三件套 |
| `cortex-memory-warden` (新) | 腐化检测 (幻觉/泛化/漂移/反馈自增强) |

### 4.5 MCP server 新工具
```
cortex_memory_read(uri, full=false)
cortex_memory_write(uri, content, weight, recall_when, level)
cortex_memory_recall(query, top_k=5, levels=[L0,L1,L2,L3])
cortex_memory_forget(uri | criteria)
cortex_memory_consolidate()
cortex_memory_promote(uri, target_level)
cortex_ledger_append(event)
cortex_session_import(transcript_path)
cortex_uri_index_rebuild()
cortex_html_render(template, data)
```

### 4.6 Wrappers (`~/.cortex/scripts/`)
保留: `doctor.sh / lint.sh / fold.sh / dashboard.sh / ingest.sh / search.sh / save.sh / refactor.sh / config.sh / install_cron.sh / update.sh`

新增:
- `memory.sh <verb> <uri> [...]` (read/write/recall/forget/promote)
- `consolidate.sh`
- `session.sh <import|export>`
- `reflect.sh`

新增 cron wrappers (`scripts/cron/`):
- `memory-promote.sh`
- `memory-forget.sh`
- `memory-compact.sh`
- `memory-consolidate.sh`
- `memory-warden.sh`
- `memory-archive.sh`

## 5. Cron 调度

| job | 频率 | cron | 行为 |
|-----|------|------|------|
| `lint` | daily | `0 01 * * *` | 知识库 lint |
| `fold` | weekly | `0 02 * * 0` | 周报 fold |
| `dashboard` | weekly | `30 02 * * 0` | 仪表盘渲染 |
| `memory-promote` | daily | `0 02 * * *` | L4→L3 提炼 / 候选写 candidates.md |
| `memory-forget` | daily | `0 03 * * *` | 扫过期, 标 archive_pending |
| `memory-compact` | weekly | `0 04 * * 0` | L4 流水账 gzip |
| `memory-consolidate` | weekly | `30 04 * * 0` | ledger → views 周报 |
| `memory-warden` | biweekly | `0 05 1,15 * *` | 腐化检测 |
| `memory-archive` | monthly | `0 06 1 * *` | 执行归档 |

约束:
- 所有 cron 用 `--allowed-tools "Bash Read Glob Write Edit"` (只读+写, 不允许删除工具)
- flock + timeout 600s + log rotation
- 失败不阻塞下一次

## 6. lint schema 更新

`lint/schemas.py`:
```python
SCHEMAS["LYT"] = {
    "root_dirs": {
        "_meta", "_templates", "_assets",
        "知识库", "记忆体系", "仪表盘", "归档",
        ".obsidian", ".trash", ".git",
        # legacy 兼容 (不强制迁移老 vault)
        "概念","实体","领域","来源","问题","仪表盘","临时","归档",
        ...
    },
    "root_files": {"主页.md", "焦点.md", "hot.md", "index.md", "README.md"},
}
```

二级目录校验:
- `知识库/{项目,来源,领域,日记,反思,收件箱}`
- `记忆体系/{L0-核心,L1-长期,L2-中期,L3-短期,L4-流水账,working,views}`

## 7. 数据迁移

本次**不写**迁移工具。两条路径:
1. 用户新装: 直接得到新结构
2. 老 vault: 保留原结构 (lint schema 兼容), 用户手动 mv 或后续单独写 `cortex-migrate` skill

迁移脚本作为 follow-up task (`05-12-cortex-migrate`)。

## 8. 验收标准

- [ ] `bash plugins/tools/cortex/install.sh --dry-run --vault /tmp/test-vault` 生成新结构
- [ ] `presets/_structure.json` 反映双 namespace + L0-L4
- [ ] `lint/schemas.py` 支持新+legacy 兼容
- [ ] 9 cron jobs 全部 wrapper 写成, dry-run 通过
- [ ] 新增 9 个 skills (`cortex-{memory,recall,consolidate,forget,session,html,dashboard,reflect,promote}`) frontmatter 合法
- [ ] 改造 5 个 skills (install/search/ingest/save) 反映新 namespace
- [ ] 新增 `cortex-memory-warden` agent
- [ ] `_meta/memory-policy.yaml` 模板写好, install 自动复制
- [ ] `_templates/html/` 至少 8 片段 (badge/card/timeline/mermaid×3/heatmap/disclosure)
- [ ] 主页.md 用 HTML grid 二维布局, 不依赖纯 Markdown
- [ ] MCP server 新增 10 工具 (read/write/recall/forget/consolidate/promote/ledger_append/session_import/uri_index_rebuild/html_render) 签名通过, 至少 5 个有实现
- [ ] 217 现有 python 测试无回归
- [ ] 用 `claude --settings ~/.claude/settings.glm-4.7-flash.json` 验证 cortex-install SKILL.md 优化后理解正确

## 9. 风险

| 风险 | 缓解 |
|------|------|
| 复杂度爆炸 (双 namespace + 5 级 + 9 cron + 9 新 skill) | 分 7 个子任务渐进交付, 每个独立可验收 |
| 老 vault 不兼容 | lint schema 双轨保留 legacy 中文/编号目录 |
| URI scheme 与 Obsidian wikilink 冲突 | URI 仅在 frontmatter + MCP, 不参与 wikilink 渲染 |
| HTML 内嵌 token 涨 | 仅仪表盘/主页用 HTML, 普通卡片仍 Markdown |
| cron 9 个并发冲突 | flock + 错峰调度 |
| L0 写入风险 | needs_user_confirm + git tag, 自动化不可达 |

## 10. 子任务拆分

按优先级:

| # | 子任务 | 描述 |
|---|--------|------|
| 1 | `presets/_structure.json` v3.0 | 双 namespace + L0-L4 seed_files 全列 |
| 2 | `_templates/` 扩充 | HTML 片段库 + L0-L4 记忆模板 + 记忆-policy 默认 |
| 3 | `lint/schemas.py` | LYT 加双 namespace 顶层 + legacy 兼容 |
| 4 | `cortex-install` SKILL 改造 | 装双 namespace + 9 cron 询问 |
| 5 | 9 cron wrapper 脚本 + scripts/cron/run.sh 复用 | memory-* 6 个 + 已有 3 个 |
| 6 | 9 新 Skill 创建 (memory/recall/consolidate/forget/session/html/dashboard/reflect/promote) | SKILL.md + AUTO_MODE |
| 7 | MCP server 10 新工具 | cortex_mcp.py 扩展 |

每个子任务独立 PR / commit, 不跨边界。

## 11. 时间预估

- 子任务 1-3: 半天 (纯文件+config)
- 子任务 4: 1 天 (install SKILL + 询问扩展)
- 子任务 5: 1 天 (6 个 cron wrapper)
- 子任务 6: 1-2 天 (9 SKILL, 每个 30-60 min)
- 子任务 7: 1-2 天 (MCP 工具实现)

合计: 4-6 天单人工作量。

---
