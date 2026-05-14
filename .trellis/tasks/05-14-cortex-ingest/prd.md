---
title: cortex ingest 项目级深度强制 — 多文件/多文件夹组织 + 全文件覆盖不遗漏
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

用户跑 `/cortex:ingest` 处理一个 repo / 文件夹, 期望:

1. 输出必须以**多文件 + 多文件夹**组织 (一个 mega `_index.md` 把全项目塞进去 = ❌)
2. **深度分析全部 files/dirs**, 不遗漏不缺失
3. 生成的 `知识库/项目/<host>/<org>/<repo>/` 必须**目录结构丰富** (多 .md + 多子目录)

当前 `skills/cortex-ingest/SKILL.md` 已有 §1 folder-first + §4 depth requirement, 但措辞偏"建议", AI 实际跑 ingest 时易偷工 (只读 README → 主文件交差)。需要把约束**升级为强制 + 可验证**。

# 设计

## 1. SKILL.md §1 folder-first 强化

仓库类型表 → 子文档清单显式化 (按 repo 大小分级):

| repo 文件数 | **强制子文档下限** | 子目录 |
|---|---|---|
| ≤50 文件 | `_index.md` + `architecture.md` + `decisions.md` + `pitfalls.md` + `dependencies.md` + `notes.md` (≥ **6 .md**) | `笔记/` 可选 |
| 50-500 文件 | 同上 + 每个顶级模块独立 `<module>.md` (≥ **10 .md**) | `笔记/` + `模块/` 强制 |
| >500 文件 | 同上 + 关键 API 拆出 (≥ **20 .md**) | `笔记/` + `模块/` + `API/` 强制 |

`_index.md` = 主条目 (架构总览 + 子文档导航表 + 全文件清单 摘要), **禁止**把项目内容压一文件。

## 2. SKILL.md §4 depth 强化 — 加 "全文件覆盖" checklist

L1-L6 之后加 §4.7:

> **覆盖度自检 (落档后必做)**: ingest 完跑 `find <repo> -type f -not -path "*/.git/*" -not -path "*/node_modules/*" | wc -l` 得文件总数 N, 落档 `知识库/项目/.../**.md` 内主体引用文件数 M, **要求 M/N ≥ 0.8** (核心源码 + 文档 + 配置 + tests 至少覆盖 80%)。覆盖率不足: 补 `笔记/<未分类项>.md` 收尾, frontmatter `coverage_gap: <list>` 标记。

`_index.md` 必含一个 "文件清单覆盖" 表: 全 file path 列出 → 哪个子文档 cover。

## 3. SKILL.md §1 加 "拒交"硬条件

落档后 verify:
```bash
ls "知识库/项目/<host>/<org>/<repo>/" | grep -c '\.md$'   # 主条目所在层 .md 数
find "知识库/项目/<host>/<org>/<repo>/" -name '*.md' | wc -l  # 全部 .md (含子目录)
```

- 主层 < 6 或 全部 < 子文档下限 → AI **必须**继续补, 不许提交
- 主层只有 `_index.md` 一个 → 视为偷工, 拒交

## 4. commands/ingest.md 加 self-check 步骤

ingest workflow 末尾加:

```
6. **落档自检** (强制, 不通过则继续补):
   a. 跑 `find <落档目录> -name '*.md' | wc -l` → N
   b. 对比 repo 文件规模 (小 ≥6 / 中 ≥10 / 大 ≥20)
   c. 跑 `find <repo> -type f | wc -l` → R
   d. 主体引用文件 M / R 必 ≥ 0.8
   e. 不通过: 列缺哪些类别 → 补子文档
```

## 5. agents/cortex-researcher.md 调度 ingest 时强化

agent description + 工作流加:

> 调 cortex-ingest 时**必须**传 `--folder-first` 隐式 (skill 自决), 对 repo 类 source **强制**多子文档输出。每个 source ingest 完跑 self-check (§4), 不达标继续补。

# 不做

- 不改 python `ingest_file.py` (folder logic 在 AI workflow 层, 非 CLI)
- 不加 lint 规则 (lint 是文件级, 不审"目录是否丰富")
- 不破坏单网页 / 单论文 / 单 PDF 单文件落档 (它们维持现状)

# 验收

1. SKILL.md §1 含分级表 (≤50 / 50-500 / >500)
2. SKILL.md §4 含覆盖度自检 §4.7
3. SKILL.md §1 含拒交硬条件
4. commands/ingest.md 含步骤 6 self-check
5. agents/cortex-researcher.md description / 工作流提到多子文档强制
6. 跑 `claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<SKILL.md §1 + §4.7 抽样>"` GLM 自检 AI 能识别 (CLAUDE.md §代码质量检查规范)
7. pytest 314 pass

# 风险

- AI 偷工是行为约束, 文档强化未必完全防住 → 加自检+拒交是双保险
- 拒交条件 (≥6 .md) 可能过严: 极小项目 (5 文件库) 也要 6 子文档 → 表分级已防 (≤50 文件用最小下限 6)
