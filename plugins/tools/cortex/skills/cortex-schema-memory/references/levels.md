# L0-L4 各级语义

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
