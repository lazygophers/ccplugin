---
title: 并写竞态禁止（需串行或 claim 批处理）
layer: core
category: arch
keywords: [concurrent,race,write,batch,claim]
source: reconstruct
authored-by: skein-spec
created: 1784346860
status: active
related: []
updated: 1784346860
---

## 铁律

- MUST：同一并行批禁止 ≥2 个 `.skein` 状态写命令，必须串行或 claim 一次性认领
- MUST：hook 层检测批内写命令，≥2 个则 block/defer 后续写直到前一写完成
- MUST：就绪 subtask 批必须一次性 claim（不逐个分回合）

## 反例表

| 禁 | 改为 |
|---|---|
| start task1 && start task2（并行） | 串行或 claim 整批 |
| sediment + start 同批 | 分开两批 |
| subtask 逐个 start 分回合 | 一次 claim |
