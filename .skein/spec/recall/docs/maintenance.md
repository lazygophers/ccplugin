---
title: maintenance
layer: recall
category: docs
keywords: [删文档,悬空链,引用排查,llms.txt,SKILL.md,README,process,checklist,文案,实现,认可,同步,design,对齐,subtask,check,认可实现]
status: active
---

## 删文档连带悬空链处理

### 删文档连带悬空链处理

### 触发场景
删除 docs/ 下任何文档时

### 陷阱-正解
陷阱：删除文档后未排查引用，留下悬空链  
正解：删除文档后必须同步排查并修复所有引用处的悬空链

### 说明
删除文档后，以下位置可能存在悬空链接需排查：
- README.md
- skills/*/SKILL.md
- 同目录的 llms.txt
- references/*.md
- 其他引用该文档的文件

### 反例
- 删除 5 个通用文档后发现 4 处悬空链（README / SKILL / multi-language / hooks）
- llms.txt 索引全部失效

### 改为
- 删文档前先 grep 查找所有引用处：grep -r "旧路径" docs/ skills/ README.md
- 删文档后立即更新所有引用，要么移除链接要么指向新文档
- 作为 subtask 的一部分验证无悬空链

### 适用
- 文档重构任务
- 删除任何可能被引用的文件（不仅是 docs/）

### 关联
- [arch]: SPA page 模块统一契约

### 案例
docs-sync-2026-07-20: 删 5 通用文档后发现 4 处悬空链（README/SKILL/multi-language/hooks）+ llms.txt 索引全失效

## checklist 文案 vs 实现认可差异处理 (认可合理实现改文案 + design.md 同步)

### 触发场景

subtask 的 `--check` 项 (验收条件) 字面文案与实现实际行为冲突 — 实现行为合理 (符合更好设计), 旧 checklist 文案是早期设计阶段的简化表达; 强制实现迁就旧文案会破坏合理设计。

### 陷阱-正解

**陷阱**: check 阶段比对 `--check` 字面与实现, 见字面不符就判实现错 → 拆合理订阅 / 删合理软刷让实现对齐旧文案。文档与代码脱节继续累积。

**正解**: 认可实现 (合理设计保住), 改 checklist 文案 + design.md 同步对齐实现行为; 文档服务于代码, 不是代码服务于文档。

### 规则

- MUST：`--check` 文案与实现冲突时先判实现是否合理 (设计上有依据: 如订阅软刷合理 / 编辑态保守合理), 合理则改文案不删实现。
- MUST：改 checklist 文案同时同步 design.md 同一概念描述 (避免 task 文档内部脱节)。
- MUST：不合理实现才改实现; 文案过时 (早期简化表达) 是常见情况, 不当字面真理。
- MUST：判断「合理」需引用 spec/注释/同源范式作依据, 不凭感觉。

### 反例表

| 禁 | 改为 |
|---|---|
| 拆合理订阅让实现对齐旧 checklist | 改 checklist 文案对齐合理实现 + design.md 同步 |
| checklist 改了但 design.md 旧描述留着 | 两处同步, 避免文档脱节 |
| 字面 ≠ 实现 → 一律判实现错 | 先判实现合理否 (引用设计依据), 合理保实现改文案 |

### 案例

webapp-rewrite T6 subtask (commit ec0005d8b, 2026-07):
- T6 subtask `--check` 项原文 `spec无onLive保留` (早期设计假设 spec 页编辑态不该订阅 WS), 但 spec.js:677-680 实际订阅了 spec-changed (合理: 多编辑源场景需同步外部变更, 仅本页编辑态保守跳过保草稿)。
- 处置: 认可实现 (订阅 spec-changed 合理 + 编辑态保守合理), 改 checklist 文案为 `spec仅订阅spec-changed(无task订阅)编辑态保守` + design.md 同步 (line 23 改为「spec 仅订阅 spec-changed」)。
- 依据: spec.js:677-680 注释明确「订阅 spec-changed 软刷当前文件, 编辑态保守不软刷 — 草稿未保存, 重拉会丢」; 同源 core/frontend-soft-refresh-pattern 范式。

### 关联

- core/frontend-soft-refresh-pattern (订阅软刷范式 — 认可 spec 订阅的依据)
- recall/frontend/webapp-rewrite-htm-pattern (webapp 重写范式, 含 onLive 双轨订阅细节)
