---
name: cortex-schema-memory
description: 记忆 / memory 等级契约 — L0=core / L1=long / L2=mid / L3=short / L4=inbox, 按 Ebbinghaus 遗忘曲线分级。用户说 "永远 / 暂时 / 记住 / 忘了 / 遗忘" 或处理 promote/demote/forget 决策时必读。
when_to_use: |
  - 用户说 "永远记住" / "硬性规则" / "never" / "严禁" → L0
  - 用户说 "暂时" / "临时" / "这次任务" → L3
  - 用户说 "记住" / "以后也用" → L2 (默认) 或 L1 (跨项目稳定)
  - 用户说 "忘了" / "不重要了" → 标 forget 候选
  - extract 从 L4 inbox 决定落到哪一级
  - lint 检查路径名 (core/long/mid/short/inbox) 与 level frontmatter 一致性
  - 处理记忆 promote / demote / forget 路由
  - 解释等级数字与遗忘曲线的反直觉对应
argument-hint: "[level]"
---

# cortex-schema-memory

cortex 记忆树等级契约。**单一真相: `docs/layout.md` 第 64-79 行**。

## 等级速查 (反直觉警告)

**数字越小 ≠ 越短期**。本系统按 Ebbinghaus 遗忘曲线分级, 升级方向 = 抵抗遗忘:

```
L4 收件箱 (未分类)
      │ extract
      ▼
L3 短期 (易忘) ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 (稳固) ── promote ──▶ L0 核心
   7d 阈值                    90d 阈值                365d 阈值                    永久, 仅手动
   ▲                          ▲                       ▲
   └── demote 7d ────────────┴── demote 90d ─────────┴── demote 365d
```

路径名后缀 (`core` / `long` / `mid` / `short` / `inbox`) **强制内嵌语义防反写**。等级与后缀必须严格匹配上表 (见 `docs/layout.md` 第 64-79 行权威定义), 任何错配组合 lint R6 直接报错。

## L0 — 核心记忆 (`memory/L0-core/`)

- **位置**: 不进入遗忘曲线, 永久常驻
- **强度**: 不可违反 (硬性规则)
- **复用面**: 全局, 所有项目 / 所有会话
- **写入触发**: 用户显式 `永远 / 硬性 / never / 严禁 / 绝不` 等强约束词
- **frontmatter 必备**:
  ```yaml
  type: rule
  level: L0
  weight: 1.0
  created: <ISO date>
  aliases: [...]
  ```
- **promote 来源**: 仅手动 (从 L1 手动晋级或直接新建)
- **forget**: 仅手动, 永不自动降级、永不自动 forget

## L1 — 长期记忆 (`memory/L1-long/`)

- **位置**: Ebbinghaus 曲线尾端, 已稳固, 几乎不忘
- **强度**: 高
- **复用面**: 跨项目稳定 (≥ 2 项目复用)
- **写入触发**:
  - L2 promote (访问 ≥ 5 次 + `weight` ≥ 0.8) — 由 lint/extract 离线判定
  - 用户显式 `永久记住 / 长期保留`
- **frontmatter 必备**:
  ```yaml
  type: memory
  level: L1
  weight: <0.8-1.0 建议>
  created: <ISO date>
  updated: <ISO date>
  tags: [...]
  ```
- **demote**: ≥ 365d 未访问 → demote 到 L2 (lint 标记, **不自动 forget**)

## L2 — 中期记忆 (`memory/L2-mid/`)

- **位置**: 曲线中段, 周月级巩固
- **强度**: 较高
- **复用面**: 跨任务同领域 (同一 domain 多次复用)
- **写入触发**:
  - L3 promote (访问 ≥ 3 次) — 离线判定
  - 用户显式 `记住 / 以后也用`
- **frontmatter 必备**:
  ```yaml
  type: memory
  level: L2
  weight: <0.5-0.8 建议>
  created: <ISO date>
  updated: <ISO date>
  tags: [...]
  ```
- **demote**: ≥ 90d 未访问 → demote 到 L3

## L3 — 短期记忆 (`memory/L3-short/`)

- **位置**: Ebbinghaus 曲线头端, **最易遗忘**
- **强度**: 中
- **复用面**: 当前任务 / 当前会话
- **写入触发**:
  - **extract 默认入口** (L4 → L3, 不显式标 L0/L1/L2 的统统落这)
  - 用户显式 `暂时 / 临时 / 这次任务`
  - 即时 "记住" 走 L3 → L2 单跳 (先落 L3, 满足条件 promote)
- **frontmatter 必备**:
  ```yaml
  type: memory
  level: L3
  weight: <0.2-0.5 建议>
  created: <ISO date>
  tags: [...]
  ```
- **forget 候选**: ≥ 7d 未访问 → lint 标 forget 候选 (**不自动删, 用户审批**)

## L4 — 收件箱 (`memory/L4-inbox/`)

- **位置**: 未进入遗忘曲线, 原始资料未分类
- **强度**: 未评估
- **复用面**: 待 extract 判定
- **写入触发**: 任意来源直落 (会话片段 / 剪贴 / 临时笔记)
- **frontmatter** (最低要求):
  ```yaml
  type: memory
  level: L4
  created: <ISO date>
  ```
- **处理**: extract 扫描后 →
  - archive: 落到 L1 / L2 / L3 (按路由判定表)
  - delete: 低价值丢弃 (extract `--apply` 才落, 默认 dry-run)

## 三轴定义

| 轴 | 含义 | 度量 |
| --- | --- | --- |
| 抗遗忘度 | 未访问容忍天数 | L1=365d / L2=90d / L3=7d / L0,L4 不适用 |
| 强度 | 用户标注硬度 | frontmatter `weight` 0-1 (L0=1.0 固定) |
| 复用面 | 触发场景 # | 会话数 / 项目数, 由 lint 统计访问日志计入 |

## extract 路由判定表

extract 从 L4 inbox 提取条目时按下表判定目标级别:

| 信号 | 目标 | 模式 |
| --- | --- | --- |
| 关键词命中 `永远 / 硬性 / never / 严禁 / 绝不` | L0 | **ask 用户**, 不自动落 |
| 关键词命中 `永久记住 / 长期保留` | L1 | 自动 (`--apply`) |
| 关键词命中 `记住 / 以后也用` | L2 | 自动 |
| 关键词命中 `暂时 / 临时 / 这次` 或 **无信号** (默认) | L3 | 自动 |
| 复用面 ≥ 3 (跨任务) | 提议 L2 promote | lint 标记 |
| 复用面 ≥ 5 + weight ≥ 0.8 | 提议 L1 promote | lint 标记 |
| 低价值 (≤ 50 字 + 无 tags + 无引用) | delete 候选 | ask 用户 |

## 关键性质

1. **新条目默认 L3**, 不直接进 L1 (即时 "记住" 也只走 L3, 由后续 promote 升)
2. **promote 由 lint/extract 离线触发**, 不由用户即时口令触发 — 即时 "记住" = L3 → L2 单跳, 不能跳级
3. **forget 永远只是标记**, 不自动删 — 由用户审批 (lint 输出候选清单, `--fix` 也不删 memory)
4. **L0 与 L4 不参与升降级流程** — L0 永久, L4 只能被 extract 消化
5. **路径名与 level 必须一致** — `memory/L1-long/foo.md` frontmatter 必须 `level: L1`, 否则 lint 报错
6. **降级是软警告** — demote 仅迁移到下级目录 + frontmatter level 改字段, 内容不变, 用户可手动 promote 回来

## 与 docs/layout.md 的关系

本 skill 是 `docs/layout.md` "记忆等级语义" 节的展开版。如二者冲突, **以 `docs/layout.md` 为准**, 本文件按其更新。
