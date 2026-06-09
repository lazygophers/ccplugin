# Design — cortex-schema 合并 + 样例补全

## 新 skill 结构

```
skills/cortex-schema/
├── SKILL.md                          ← ≤ 60 行薄入口
└── references/
    ├── topology.md                   ← ~/.cortex 顶层 + .wiki 物理树 + 双层同构 + 开放扩展 + 脚本用途分离 + 详细 ASCII 含示例叶子
    ├── knowledge-modules.md          ← 项目/领域/脚本 三模块路径规则 (合 projects+domains+scripts)
    ├── memory-levels.md              ← 5 级语义 + level↔dir 映射 + 反写防呆 + 遗忘曲线 (合 levels+axes-routing+properties)
    ├── templates.md                  ← frontmatter 字段表 + 各 type frontmatter 块模板
    └── examples/                     ← 完整 .md 样例
        ├── rule.md                   ← type=rule (L0)
        ├── project.md                ← type=project (README.md 内容)
        ├── domain.md                 ← type=domain
        ├── memory-L1.md              ← type=memory level=L1
        ├── memory-L2.md              ← type=memory level=L2
        ├── memory-L3.md              ← type=memory level=L3
        └── vault-script.md           ← type=vault-script (实际是 .sh/.py, 这里用 .md 描述)
```

## SKILL.md 路由表

```
| 任务 | 文件 |
| 查 ~/.cortex 顶层物理布局 / 双层同构 / 必备目录 / 开放扩展 | references/topology.md |
| 查三模块 (项目/领域/脚本) 路径规则 + 命名 + frontmatter | references/knowledge-modules.md |
| 查 5 级记忆 (L0-L4) 语义 / 映射 / 遗忘曲线 / 反写防呆 | references/memory-levels.md |
| 查 frontmatter 通用字段 + 各 type 块模板 | references/templates.md |
| 查完整 .md 样例 (含正文 + wikilink) | references/examples/<type>.md |
```

## frontmatter (cortex-schema)

```yaml
---
name: cortex-schema
description: "项目知识库统一契约 — 目录结构 / 三模块路径 (项目/领域/脚本) / 5 级记忆 (L0-core/L1-long/L2-mid/L3-short/L4-inbox, Ebbinghaus 遗忘曲线) / 双层同构 (~/.cortex/.wiki + <repo>/.wiki) / frontmatter 模板 / 完整样例. lint+extract 引用本 skill 作权威源."
when_to_use: "入库/归档/写笔记/记忆等级判定/promote/demote/forget/路径决策/frontmatter 模板/查样例"
argument-hint: "[topology|knowledge|memory|templates|examples]"
arguments: "[拓扑|知识|记忆|模板|样例]"
---
```

## examples 内容契约

每个样例 .md = 完整可直接落盘的样本, 含:
1. 完整 frontmatter (含 type/level/created/updated/tags/aliases/weight 等)
2. 正文 ≥ 5 行 (有意义内容, 非 lorem ipsum)
3. 至少 1 个 wikilink (`[[other-page]]`) 演示
4. 至少 1 个标题层级 (`##`)
5. 头部 1 行注释 (`> 样例 — type=X, 落盘到 <path>`) 但不进 frontmatter

## 详细 topology ASCII

含示例叶子, 不再只展示空目录:

```
~/.cortex/.wiki/
├── memory/
│   ├── L0-core/
│   │   └── never-commit-secrets.md      ← 示例规则
│   ├── L1-long/
│   │   └── shell-quoting-rules.md       ← 长期记忆样例
│   ├── L2-mid/
│   │   └── current-sprint-context.md
│   ├── L3-short/
│   │   └── today-tmp-fix.md
│   └── L4-inbox/
│       ├── pasted-note.md
│       └── _archived/
│           └── ...
├── 项目/
│   └── github.com/
│       └── lazygophers/
│           └── ccplugin/
│               ├── README.md            ← summary + frontmatter
│               ├── mindmap.canvas       ← (可选) obsidian canvas
│               └── notes/
│                   └── architecture.md
├── 领域/
│   ├── tech/
│   │   └── rust/
│   │       └── async/
│   │           └── tokio-runtime.md     ← ≥ 2 级 sub
│   ├── life/
│   │   └── habits/
│   │       └── sleep-protocol.md
│   └── finance/
│       └── etf/
│           └── global-allocation.md
└── 脚本/
    ├── canvas-from-mindmap.py
    └── frontmatter-normalize.sh
```

## 引用更新点

| 文件 | 旧 → 新 |
| --- | --- |
| `plugins/tools/cortex/.claude-plugin/plugin.json` | skills [-knowledge, -memory] → [cortex-schema]; keep lint/extract |
| `agents/cortex.md` | "schema-knowledge / schema-memory" → "cortex-schema" |
| `README.md` | 同上, 表中删一行 |
| `llms.txt` | 同上 |
| `skills/cortex-lint/SKILL.md` | "schema-knowledge + schema-memory" → "cortex-schema" |
| `skills/cortex-lint/references/rules.md` | `cortex-schema-knowledge/references/topology.md` 等 → `cortex-schema/references/topology.md` 等 |
| `skills/cortex-lint/references/fixers.md` | 同 |
| `skills/cortex-extract/references/classifier.md` | 同 |
| `skills/cortex-extract/references/io.md` | 同 |
| `scripts/_lint/__init__.py` 注释 | `cortex-schema-memory/...` → `cortex-schema/references/memory-levels.md` |
| `tests/e2e-report.md` | 同 |

## 资源边界

| Subtask | 写资源 | 并行性 |
| --- | --- | --- |
| S1 | `skills/cortex-schema/{SKILL.md, references/{topology,knowledge-modules,memory-levels,templates}.md}` (新建) | 与 S2 并行 |
| S2 | `skills/cortex-schema/references/examples/*.md` (新建) | 与 S1 并行 |
| S3 | 删 `skills/cortex-schema-{knowledge,memory}/`, 改 plugin.json | 等 S1 完成 |
| S4 | 改 lint/extract/agent/README/llms/_lint/e2e-report 中引用 | 等 S1 完成 |
| S5 | 只读验证 + 暂存 | 收口 |

## 验证契约

S5 必跑:
1. `test -d skills/cortex-schema && test ! -d skills/cortex-schema-knowledge && test ! -d skills/cortex-schema-memory`
2. SKILL.md ≤ 60 行 + frontmatter (desc ≤ 512 / wtu ≤ 128 / 无"用户说" / arguments 字符串)
3. references/examples/ 含 ≥ 5 .md, 每个含 `^---` (frontmatter) + `## ` (标题) + `[[` (wikilink)
4. `! grep -r 'cortex-schema-knowledge\|cortex-schema-memory' plugins/tools/cortex/`
5. plugin.json: skills len == 3, 含 cortex-schema
6. validate-layout / lint --check / extract --dry-run smoke 行为同前
