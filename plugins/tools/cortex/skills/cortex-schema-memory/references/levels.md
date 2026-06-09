# memory 5 级契约 (权威源)

本文件是 cortex 记忆树 5 级 (L0-L4) 的**唯一真相源**: 物理路径 / 语义 / 写入触发 / 自动迁移 / level↔dir 映射 / 反写防呆. lint R6 / extract 路由 / agent 全部引用此文件.

## 5 级物理树 (权威)

`memory/` 子目录布局, 用户级 (`~/.cortex/.wiki/memory/`) 与项目级 (`<repo>/.wiki/memory/`) 同构:

```
memory/
├── L0-core/     ← 核心记忆, 不可违反 (永久)
├── L1-long/     ← 长期记忆 (曲线尾端, 已稳固)
├── L2-mid/      ← 中期记忆 (周月级)
├── L3-short/    ← 短期记忆 (曲线头端, 最易遗忘) — extract 默认入口
└── L4-inbox/    ← 收件箱, 原始资料未分类
```

## level ↔ dir 映射表 (权威, 接管自 lint R6)

| level field | 路径段 (权威) | 后缀语义 |
| --- | --- | --- |
| `L0` | `memory/L0-core/` | core = 核心 |
| `L1` | `memory/L1-long/` | long = 长期 |
| `L2` | `memory/L2-mid/` | mid = 中期 |
| `L3` | `memory/L3-short/` | short = 短期 |
| `L4` | `memory/L4-inbox/` | inbox = 收件箱 |

**lint R6 / extract 路由判定均以此表为准**. 路径段中的 `<N>` 必须与文件 frontmatter `level` 字段严格相等, 且后缀必须匹配上表; 三方任一不一致即 error.

## 反写防呆 (lint R6 视为 error)

数字与后缀**强绑定**, 以下都是反写, 全部 error:

| 反例 | 错在哪 |
| --- | --- |
| `memory/L1-recent/` | L1 后缀应为 `long`, 不是 `recent` |
| `memory/L1-short/` | L1 是**长期**, 不是短期; 短期是 L3 |
| `memory/L3-long/` | L3 是**短期**, 不是长期; 长期是 L1 |
| `memory/L0-rules/` | L0 后缀应为 `core`, 不是 `rules` |
| `memory/L4-raw/` | L4 后缀应为 `inbox`, 不是 `raw` |
| `memory/L2-recent/` | L2 后缀应为 `mid`, 不是 `recent` |

**记忆口诀**: 数字越小 = 越抗遗忘 = 升级方向. L0 永久 / L1 长 / L2 中 / L3 短 / L4 入口.

## 遗忘曲线速查 (反直觉)

**数字越小 ≠ 越短期**. 本系统按 Ebbinghaus 遗忘曲线设计, 数字越小 = 抗遗忘越强:

```
L4 收件箱 (未分类)
      │ extract
      ▼
L3 短期 (易忘) ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 (稳固) ── promote ──▶ L0 核心
   7d 阈值                    90d 阈值                365d 阈值                    永久, 仅手动
   ▲                          ▲                       ▲
   └── demote 7d ────────────┴── demote 90d ─────────┴── demote 365d
```

- **升级方向 = 抗遗忘**: L3 → L2 → L1 → L0
- **降级方向 = 遗忘**: L1 → L2 → L3 → forget 候选
- **L0 与 L4 不参与自动升降级**: L0 永久 (仅手动), L4 仅供 extract 消化

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

## 同构提醒

`memory/` 5 级目录在用户级 (`~/.cortex/.wiki/`) 与项目级 (`<repo>/.wiki/`) **完全同构**. 详见 `cortex-schema-knowledge/references/topology.md` 双层同构原则.
