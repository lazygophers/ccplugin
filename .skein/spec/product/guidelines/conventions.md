---
title: conventions
category: guidelines
keywords: [product,namespace,archive,amend,anchors]
status: active
inclusion: auto
anchors: .skein/spec/product/CONVENTION.md
---

## 维护原则

### Product namespace 维护原则

`product/` namespace 记录系统现状（长期真值），与 `task/<tid>/prd.md`（一次性变更）相对。关键约束：

1. **禁止自动 archive**（区别于 `rules/` 和 `map/`）
   - anchors 失效仅报告，不自动归档
   - 系统现状文档即便过时，也需人工决策是删除、合并还是保留
   
2. **amend 章节改写禁止静默追加**
   - 功能演进时必须改写对应章节（不追加）
   - 章节不存在则报错，不允许隐式创建
   - 理由：避免演化文档变成日志，保持可读性

3. **anchors 用于 finish 阶段反查**
   - git diff 触及 anchors 文件时，反查对应 product 页作为更新候选
   - 三路降级：anchors 反查 → prd 关键词 recall → 建议新建

维护原则与 `rules/`（规则稳定性优先）、`map/`（代码骨架现算）形成差异化策略。
