> 样例 — 完整 vault 目录树 (~/.cortex/.wiki/ 填充后), 含真实示例文件叶子

# Vault 目录树样例

展示 `~/.cortex/.wiki/` 完整填充后长什么样。物理布局权威源见 `../references/topology.md`。

## 用户级 `~/.cortex/`

```
~/.cortex/
├── .wiki/                                       ← 用户级知识库根
│   ├── memory/                                  ← 5 级记忆树 (Ebbinghaus 遗忘曲线)
│   │   ├── L0-core/
│   │   │   └── never-commit-secrets.md          ← 核心规则 (永久, 不可违反)
│   │   ├── L1-long/
│   │   │   └── shell-quoting-rules.md           ← 长期记忆 (已稳固)
│   │   ├── L2-mid/
│   │   │   └── current-sprint-context.md        ← 中期记忆 (周月级)
│   │   ├── L3-short/
│   │   │   └── today-tmp-fix.md                 ← 短期记忆 (extract 默认入口)
│   │   └── L4-inbox/
│   │       ├── pasted-note.md                   ← 收件箱原始资料
│   │       └── _archived/                       ← extract --apply 后归档
│   │           └── 2026-06-09-old-note.md
│   ├── 项目/                                     ← projects 模块 (host/owner/repo)
│   │   └── github.com/
│   │       └── lazygophers/
│   │           └── ccplugin/
│   │               ├── README.md                ← 项目摘要 (含 frontmatter)
│   │               ├── mindmap.canvas           ← (可选) Obsidian 心智地图
│   │               └── notes/
│   │                   └── architecture.md      ← 子页面
│   ├── 领域/                                     ← domains 模块 (area/sub ≥ 2 级)
│   │   ├── tech/
│   │   │   └── rust/
│   │   │       └── async/
│   │   │           └── tokio-runtime.md
│   │   ├── life/
│   │   │   └── habits/
│   │   │       └── sleep-protocol.md
│   │   └── finance/
│   │       └── etf/
│   │           └── global-allocation.md
│   └── 脚本/                                     ← vault 内部脚本 (被 lint/extract 调用)
│       ├── canvas-from-mindmap.py
│       └── frontmatter-normalize.sh
├── config/                                      ← 插件配置 (yaml/json)
├── state/                                       ← 增量游标 / 索引缓存
│   ├── extract-cursor.json
│   └── ingest-cursor.json
├── scripts/                                     ← 用户操作入口 CLI (≠ .wiki/脚本/)
│   ├── cortex-save
│   └── cortex-recall
├── logs/                                        ← 运行日志
│   └── refresh.log
├── cache/                                       ← 开放扩展位 (索引缓存)
├── credentials/                                 ← 开放扩展位 (凭证, 权限 600)
└── templates/                                   ← 开放扩展位 (笔记模板)
```

## 项目级 `<repo>/.wiki/` (仅 memory + 领域)

```
<repo>/.wiki/
├── memory/
│   ├── L0-core/
│   │   └── repo-must-pass-ci.md                 ← 本项目专属核心规则
│   ├── L1-long/
│   ├── L2-mid/
│   │   └── module-ownership.md
│   ├── L3-short/
│   └── L4-inbox/
└── 领域/                                         ← 本项目专属领域知识 (项目级唯一 knowledge 模块)
    └── tech/
        └── cortex/
            └── design.md
```

注: 项目级**不含** `项目/` (外部 repo 引用属跨项目沉淀, 只落用户级) 与 `脚本/` (vault 内部脚本仅用户级); 顶层 `config/ state/ scripts/ logs/` 也仅用户级。

## 路径要点 (易错)

- 三模块顶层目录名用**中文** (`项目/` `领域/` `脚本/`); memory 5 级用**英文** (`L0-core` 等)。
- `~/.cortex/scripts/` (英文, 用户 CLI) 与 `~/.cortex/.wiki/脚本/` (中文, vault 内部) **绝不混用**。
- 领域 ≥ 2 级 (area/sub); 项目固定 host/owner/repo 三段。

## 引用

- 物理布局权威源: `../references/topology.md`
- 三模块路径规则: `../references/knowledge-modules.md`
- 5 级记忆语义: `../references/memory-levels.md`
- 单文件样例: `rule.md` / `project.md` / `domain.md` / `memory-L1.md` / `vault-script.md`
