---
title: spec-cli
category: spec-memory
keywords: [cli,命令行,spec,recall,sediment]
status: active
inclusion: auto
anchors: plugins/tools/skein/scripts/spec.py,plugins/tools/skein/scripts/skeinlib/spec/cli.py
---

## Spec CLI 命令行接口

这是对 spec.py CLI 的描述页面。

### 主要命令

- `recall`: 按关键词召回相关规则
- `sediment`: 沉淀新规则
- `finish-candidates`: finish 阶段回写候选反查

### finish-candidates 命令

新增的命令，用于在 task finish 时反查对应的 product wiki 页面。

**三路降级策略**:
1. anchors 反查（高优先级）
2. prd 关键词 recall（弱候选）
3. 皆无则建议新建