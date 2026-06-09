# memory 5 级契约 (权威源)

cortex 记忆树 5 级 (L0-L4) 的**唯一真相源**: 物理路径 / 语义 / 写入触发 / 自动迁移 / level↔dir 映射 / 反写防呆 / 三轴 / extract 路由. lint R6 + extract 路由 + agent 全部引用此文件.

## 等级速查 ASCII (反直觉警告)

**数字越小 ≠ 越短期**. 按 Ebbinghaus 遗忘曲线分级, 升级方向 = 抵抗遗忘:

```
L4 收件箱 (未分类)
      │ extract
      ▼
L3 短期 (易忘) ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 (稳固) ── promote ──▶ L0 核心
   7d 阈值                    90d 阈值                365d 阈值                    永久, 仅手动
   ▲                          ▲                       ▲
   └── demote 7d ────────────┴── demote 90d ─────────┴── demote 365d
```

## 5 级物理树

`memory/` 子目录布局, 用户级 (`~/.cortex/.wiki/memory/`) 与项目级 (`<repo>/.wiki/memory/`) 同构:

```
memory/
├── L0-core/     ← 核心记忆, 不可违反 (永久)
├── L1-long/     ← 长期记忆 (曲线尾端, 已稳固)
├── L2-mid/      ← 中期记忆 (周月级)
├── L3-short/    ← 短期记忆 (曲线头端, 最易遗忘) — extract 默认入口
└── L4-inbox/    ← 收件箱, 原始资料未分类
```

## level ↔ dir 映射表 (权威)

| level field | 路径段 | 后缀语义 |
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
- **forget**: 永不自动降级, 永不自动 forget

## L1 — 长期记忆 (`memory/L1-long/`)

- **位置**: Ebbinghaus 曲线尾端, 已稳固, 几乎不忘
- **强度**: 高
- **复用面**: 跨项目稳定 (≥ 2 项目复用)
- **写入触发**: L2 promote (访问 ≥ 5 次 + `weight` ≥ 0.8, 离线判定) / 用户显式 `永久记住 / 长期保留`
- **frontmatter 必备**: `type: memory` + `level: L1` + `weight: 0.8-1.0` + `created` + `updated` + `tags`
- **demote**: ≥ 365d 未访问 → demote 到 L2 (**不自动 forget**)

## L2 — 中期记忆 (`memory/L2-mid/`)

- **位置**: 曲线中段, 周月级巩固
- **强度**: 较高
- **复用面**: 跨任务同领域
- **写入触发**: L3 promote (访问 ≥ 3 次, 离线判定) / 用户显式 `记住 / 以后也用`
- **frontmatter 必备**: `type: memory` + `level: L2` + `weight: 0.5-0.8` + `created` + `updated` + `tags`
- **demote**: ≥ 90d 未访问 → demote 到 L3

## L3 — 短期记忆 (`memory/L3-short/`)

- **位置**: Ebbinghaus 曲线头端, **最易遗忘**
- **强度**: 中
- **复用面**: 当前任务 / 当前会话
- **写入触发**: **extract 默认入口** (L4 → L3) / 用户显式 `暂时 / 临时 / 这次任务` / 即时 "记住" 走 L3 → L2 单跳
- **frontmatter 必备**: `type: memory` + `level: L3` + `weight: 0.2-0.5` + `created` + `tags`
- **forget 候选**: ≥ 7d 未访问 → lint 标 forget 候选 (**不自动删, 用户审批**)

## L4 — 收件箱 (`memory/L4-inbox/`)

- **位置**: 未进入遗忘曲线, 原始资料未分类
- **强度**: 未评估
- **复用面**: 待 extract 判定
- **写入触发**: 任意来源直落 (会话片段 / 剪贴 / 临时笔记)
- **frontmatter** (最低): `type: memory` + `level: L4` + `created`
- **处理**: extract 扫描后 → archive (落 L1/L2/L3) 或 delete (`--apply` 才落)

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
5. **路径名与 level 必须一致** — `memory/L1-long/foo.md` frontmatter 必须 `level: L1`, 否则 lint R6 报错
6. **降级是软警告** — demote 仅迁移到下级目录 + frontmatter level 改字段, 内容不变, 用户可手动 promote 回来

## 引用

- 顶层布局 + 同构: `topology.md`
- frontmatter 模板: `templates.md`
- 完整样例 (按 level): `../examples/memory-L1.md` / `memory-L2.md` / `memory-L3.md` / `rule.md` (L0)
- lint R4 同构 + R6 等级一致: `cortex-lint`
- extract 路由消费方: `cortex-extract`
