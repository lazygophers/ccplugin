# Design — cortex-evolve

## skill 结构

```
skills/cortex-evolve/
├── SKILL.md (≤ 60 行)
└── references/
    ├── signals.md     三轴 (频率 / 时间 / 重要度) 定义 + 计算
    ├── rules.md       升降级规则 + 修饰 + 适用范围 + 金字塔
    └── workflow.md    执行流程 (扫 → 评分 → plan → 用户审 → apply)
```

## frontmatter

```yaml
---
name: cortex-evolve
description: "记忆库升降级维护 — 按金字塔模型 (L4 庞大 → L0 稠密) 自动 promote/demote. 信号: 频率 (近期提及) / 时间 (距今) / 重要度. 规则: 用户反复强调 → 逐级升; L1/L0 允许自动升不允许自动降. 主要工作区 L4-L2; L1/L0 写入新条目仍 ask. 无独立脚本, 调 cortex-extract/save/lint 执行."
when_to_use: "升级记忆/降级记忆/promote/demote/记忆再平衡/金字塔维护/记忆 audit/evolve"
argument-hint: "[--scan|--dry-run|--apply] [--target <vault>]"
arguments: "[--scan|--dry-run|--apply] [--target <仓库根>]"
user-invocable: true
---
```

## SKILL.md 内容

1. frontmatter
2. 1 段总览 (金字塔模型 + 升降级目标)
3. 速查表: 升级触发 / 降级触发 / 例外
4. 路由表 (3 references)
5. 执行入口 (无脚本, 步骤参 workflow.md)
6. 引用 cortex-extract/cortex-save/cortex-lint

## references/signals.md (≤ 220 行)

三轴定义:

### 1. 频率 (recency-frequency)
- 计算: 最近 N 天提及次数 / 总提及次数, N 默认 14
- 升级阈: 近 14d ≥ 3 次
- 降级阈: 近 30d 0 次 + 历史曾提

### 2. 时间 (event-recency)
- 计算: 当前 - frontmatter.event_date (若有) 或 mtime
- 升级阈: ≤ 7d 内事件 → +1 升级权重
- 降级阈: ≥ 90d 未更新 → +1 降级权重

### 3. 重要度 (importance)
- 计算: frontmatter.weight + 用户标注关键词 ("永远/硬性" → 1.0)
- 升级阈: weight ≥ 0.8 → 强升级信号
- 降级阈: weight ≤ 0.3 + 频率低 → 弱降级 (不触发主动降, 仅 L4-L3)

### 综合得分
- promote_score = 0.4 * freq + 0.3 * recency + 0.3 * importance
- demote_score = 0.4 * (1-freq) + 0.3 * (1-recency) + 0.3 * (1-importance)
- 阈: promote_score ≥ 0.7 → 升; demote_score ≥ 0.7 → 降

## references/rules.md (≤ 220 行)

升降级规则:

### 升级规则
- L3 → L2: promote_score ≥ 0.6
- L2 → L1: promote_score ≥ 0.7 + 复用 ≥ 5 + weight ≥ 0.8
- L1 → L0: promote_score ≥ 0.9 + 用户多次强调 (≥ 3 次 "永远/硬性") + 复用 ≥ 10
- L4 → L3: extract 已处理 → 不在 evolve 范围, 走 cortex-extract

### 降级规则
- L2 → L3: demote_score ≥ 0.7 + 30d 未访问
- L3 → 标 forget candidate (L3 不直接降 L4; 走 lint forget audit)
- **L1 / L0 不主动降**: 即使 demote_score ≥ 0.9 也仅标 audit-candidate, 不写盘. 用户显式 forget 才动.

### 修饰规则
1. 用户反复强调 (≥ 3 次) → 强升级 (跳级允许: L3→L1 直跳)
2. L1/L0 自动升允许 (从 L2/L1 promote 不 ask)
3. L1/L0 新写入 (非 promote, 即直接落 L0/L1) 必须 ask 用户
4. L1/L0 不主动降 (硬规)
5. 金字塔 audit: L0 条目数 > 20 → lint warn

### 适用范围速查
| 级别 | 自动升 | 自动降 | 写入 ask |
| --- | --- | --- | --- |
| L4 → L3 | 走 extract | — | — |
| L3 ↔ L2 | ✓ | ✓ | 否 |
| L2 → L1 | ✓ | ✗ | 否 (从 promote 来) |
| L1 → L0 | ✓ | ✗ | 否 (从 promote 来) |
| 直接写 L1 | — | — | 必须 ask |
| 直接写 L0 | — | — | 必须 ask |

## references/workflow.md (≤ 220 行)

执行流程 (skill 步骤指导 main):

1. **--scan** (默认): 列 vault 所有 memory/L1-L4 条目, 输出当前状态
2. **评分**: 跑 signals.md 三轴 → promote_score / demote_score
3. **plan 生成**: 按 rules.md 决定升降; 输出 JSON plan (file / current_level / proposed_level / score / reason)
4. **用户审**: 显示 plan, 用户确认 (L1/L0 升级 + 任何 ask 项)
5. **apply**: 调 cortex-save / cortex-extract 移动文件 + 更新 frontmatter level

无独立脚本, 步骤 1-3 由 main 调 cortex-extract router (复用三轴) 实现; 步骤 5 调 cortex-save / lint --fix.

边界 vs extract:
- extract: inbox 入门 → L4 → 初次分类
- evolve: 已入 vault 的条目 跨级再平衡

边界 vs save:
- save: 一次性写入新条目
- evolve: 移动既有条目

## 资源边界

| Subtask | 写 |
| --- | --- |
| S1 | skills/cortex-evolve/** (新建) |
| S2 | plugin.json + agent + README + llms |
| S3 | 只读 + 暂存 |

## 验证契约

- SKILL.md 行数 + frontmatter 合规
- references 3 文件存在, 含关键概念 (signals 三轴, rules L1/L0 例外 + 金字塔)
- plugin.json skills len == 7, 含 cortex-evolve
- 6 既有 skill smoke 同前

## Rollback

```bash
git checkout plugins/tools/cortex/{.claude-plugin,agents,README.md,llms.txt}
rm -rf plugins/tools/cortex/skills/cortex-evolve/
```
