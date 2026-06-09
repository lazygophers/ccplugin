# split cortex-schema templates per type + clarify layout

## 目标

cortex-schema skill 内 `references/templates.md` 单文件含全部 type 模板, 拆为 `templates/<type>.md` 7 文件 (与 examples/ 同名对位), 形成"三平列"形态 (templates / examples / references), 提升结构清晰度.

## 目标形态

每个 type 的每个**变体**独立模板文件. 二级目录按 type 分组.

```
skills/cortex-schema/
├── SKILL.md
├── templates/          ← frontmatter 块模板 (10 文件, 拆自 references/templates.md)
│   ├── memory/
│   │   ├── L0-rule.md          ← type=rule, level=L0
│   │   ├── L1-long.md          ← type=memory, level=L1
│   │   ├── L2-mid.md           ← type=memory, level=L2
│   │   ├── L3-short.md         ← type=memory, level=L3
│   │   └── L4-inbox.md         ← type=memory, level=L4
│   ├── project/
│   │   ├── github.md           ← host=github.com 变体
│   │   ├── gitlab.md           ← host=gitlab.com 变体
│   │   └── website.md          ← 其他 domain 变体
│   ├── domain.md               ← type=domain (area 是字段不拆)
│   └── vault-script.md         ← type=vault-script (sh/py 同文件)
├── examples/           ← 完整可落盘样例 (现有 7 文件, 不动)
│   └── <现有 7 文件>
└── references/         ← 概念说明
    ├── topology.md
    ├── knowledge-modules.md
    └── memory-levels.md
```

templates ↔ examples 映射 (非 1:1, 多 template 可指向同 example):

| template | example |
| --- | --- |
| memory/L0-rule.md | examples/rule.md |
| memory/L1-long.md | examples/memory-L1.md |
| memory/L2-mid.md | examples/memory-L2.md |
| memory/L3-short.md | examples/memory-L3.md |
| memory/L4-inbox.md | (无, 标 "样例可参照 memory-L3.md 形态") |
| project/github.md | examples/project.md (现有为 github) |
| project/gitlab.md | (无, 标参照 project.md) |
| project/website.md | (无, 标参照 project.md) |
| domain.md | examples/domain.md |
| vault-script.md | examples/vault-script.md |

## Deliverable 矩阵

| ID | 交付物 | 验收 | 优先级 |
| --- | --- | --- | --- |
| D1 | templates/ 二级目录 + 10 模板文件 | memory/ 5 + project/ 3 + domain.md + vault-script.md | P0 |
| D2 | 删 references/templates.md (内容迁完) | 文件不存在 | P0 |
| D3 | SKILL.md 路由表更新 (templates/ + examples/ + references/ 三平列) | 路由表反映新结构 | P0 |
| D4 | references/{knowledge-modules,memory-levels}.md 中 `templates.md` 引用改为 `templates/<type>.md` | 0 旧引用残留 | P0 |
| D5 | 各 templates/<type>.md 含 "完整样例见 examples/<type>.md" 引用 | 7 文件全含 | P1 |

## Subtask 拆分

| ID | Subtask | Deliverable | 边界 |
| --- | --- | --- | --- |
| S1 | 拆 templates.md 为 7 文件 | D1, D2 | skills/cortex-schema/templates/** + 删 references/templates.md |
| S2 | 改 SKILL.md + references 引用 | D3, D4, D5 | SKILL.md + references/*.md |
| S3 | 验证 + 暂存 | all | smoke + grep |

## Subtask 调度图

```mermaid
flowchart LR
    S1[S1 拆 templates] --> S2[S2 改引用]
    S2 --> S3[S3 verify]
```

S1 串行依赖 (S2 需要看到 templates/ 已存在). S3 收口.

## 范围边界

- 在范围: `plugins/tools/cortex/skills/cortex-schema/{SKILL.md, templates/**, references/{knowledge-modules,memory-levels}.md}`
- 不动: examples/* / topology.md / 其他 skill / 脚本 / agent / plugin.json
- 禁改: examples/ 内容 / 三模块路径 / 5 级路径 / 记忆等级语义

## 验收

- [ ] `skills/cortex-schema/templates/` 存在, 含 10 .md (memory/5 + project/3 + domain.md + vault-script.md)
- [ ] `skills/cortex-schema/references/templates.md` 不存在
- [ ] 每个 templates/<path>.md 含 frontmatter 块模板片段 + ≥ 1 处 examples 引用 (无对应 example 的标 "参照 <近似>")
- [ ] SKILL.md 路由表反映三平列, ≤ 60 行
- [ ] grep `references/templates.md` 在 cortex-schema/ 内 0 命中
- [ ] grep `templates.md` (旧单文件) 在 references/ 内 0 命中
- [ ] smoke: validate / lint / extract 行为同前
- [ ] 自动 git add

## 约束

硬约束:
- 每个模板文件 ≤ 50 行 (薄, 仅 frontmatter 块 + 字段说明 + 引用 examples)
- SKILL.md ≤ 60 行 (路由表新增 templates 一行, 不展开 10 文件; 详情用户进 templates/ 看)
- examples 不动 (用户单独 task 已完成)
- 内容只迁移, 不删
- 新增内容 (gitlab/website/L4-inbox 等无源块) 按 templates.md 既有同 type 模式补全, 字段对齐

软约束:
- templates/ 文件名与 examples/ 严格对位 (同名)
- templates/ 每文件头部 1 行注释 "> 模板 — type=X 的 frontmatter 块; 完整样例见 examples/<type>.md"

## 风险

| 风险 | 缓解 |
| --- | --- |
| 拆完后 references/templates.md 残留死引 | S2 强制 grep |
| templates/<type>.md 与 examples/<type>.md 内容重复 | templates = frontmatter 块片段 (拼装用); examples = 完整文件. 边界文档化 |
| SKILL.md 路由表过长 | 5 列保留 (topology/knowledge/memory/templates/examples), ≤ 60 行可控 |
