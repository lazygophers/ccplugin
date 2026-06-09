---
name: cortex-schema-memory
description: "记忆 / memory 等级契约 — L0=core / L1=long / L2=mid / L3=short / L4=inbox, 按 Ebbinghaus 遗忘曲线分级。触发词: 永远 / 暂时 / 记住 / 忘了 / 遗忘; 处理 promote/demote/forget 决策时必读。单一真相 docs/layout.md 第 64-79 行。"
when_to_use: "永远/硬性/never→L0; 暂时/临时→L3; 记住→L2; 忘了→forget; promote/demote/forget 路由; extract 落级判定; lint 路径/level 校验"
argument-hint: "[level]"
arguments: "[等级]"
---

# cortex-schema-memory

cortex 记忆树等级契约。**单一真相: `docs/layout.md` 第 64-79 行**。

## 等级速查 (反直觉警告)

**数字越小 ≠ 越短期**。按 Ebbinghaus 遗忘曲线分级, 升级方向 = 抵抗遗忘:

```
L4 收件箱 (未分类)
      │ extract
      ▼
L3 短期 (易忘) ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 (稳固) ── promote ──▶ L0 核心
   7d 阈值                    90d 阈值                365d 阈值                    永久, 仅手动
   ▲                          ▲                       ▲
   └── demote 7d ────────────┴── demote 90d ─────────┴── demote 365d
```

路径名后缀 (`core` / `long` / `mid` / `short` / `inbox`) 强制内嵌语义防反写, 等级与后缀错配 lint R6 直接报错。

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 L0-L4 各级语义 / 路径 / 写入触发 / 自动迁移 / frontmatter | `references/levels.md` |
| 查三轴定义 + extract 路由判定表 | `references/axes-routing.md` |
| 查关键性质 (默认入口/promote 离线/forget 不自动) | `references/properties.md` |

## 与 docs/layout.md 的关系

本 skill 是 `docs/layout.md` "记忆等级语义" 节的展开版。如二者冲突, **以 `docs/layout.md` 为准**。
