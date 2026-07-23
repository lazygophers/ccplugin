---
title: status 字面值跨模块复制
layer: recall
category: arch
keywords: [常量复制,跨模块,DRY权衡,ponytail,性能优化]
source: hooks.py L70-117
authored-by: skein-spec
created: 1784617035
status: active
related: []
updated: 1784617035
---

---
title: status 字面值跨模块复制
layer: core
category: arch
keywords: [常量复制,跨模块,DRY权衡,ponytail,性能优化]
source: sediment
authored-by: skein-specer
created: 1784473542
status: active
related: []
updated: 1784473542
---

## 铁律 / 契约

- MUST：跨模块常量复制需权衡 —— 优先考虑模块启动性能 vs 维护成本（常量稳定不变且复用模块≥2 时，可接受字面值复制）
- MUST：复制处必须加 ponytail 注释说明来源与权衡（如 `# ponytail: 字面值复制自 <source>:<line> (跨模块 import 启动开销大; 两处值稳定不变)`）
- MUST：源头值变更时需同步更新所有复制处（建议在源头常量定义旁加 `# 复制位置：hooks.py L70-117` 等索引注释）
- MUST：常量值稳定不变才适用此范式（易变值禁复制，应改用共享模块）

## 反例表

| 禁 | 改为 |
|---|---|
| 为省启动开销而复制易变常量 | 用共享模块导入，易变值必须单源 |
| 复制常量不加 ponytail 注释 | 加 `# ponytail: 字面值复制自...` 说明来源与权衡 |
| 改源头后忘了同步复制处 | 源头旁加 `# 复制位置：` 索引，改时逐处更新 |
| 单模块用就复制 | 仅在复用模块≥2 时考虑此范式 |

## 适用

- 常量值稳定不变（如状态枚举、配置键）
- 跨模块导入会显著增加启动时间
- 复制处≥2 个模块

## 关联

- [arch] Ponytail 注释模式（性能权衡显式化）
- [arch] 常量定义 vs 运行时配置选择
