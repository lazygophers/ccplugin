---
id: S1
slug: skill
deliverable: D1,D2,D3,D4
parent-task: 06-10-cortex-evolve
execution-layer: sub-agent
estimated-tokens: 10000
---

# S1 · 建 cortex-evolve skill

## 产出

- `skills/cortex-evolve/SKILL.md` ≤ 60 行
- `skills/cortex-evolve/references/signals.md` (≤ 220, 三轴定义 + 计算)
- `skills/cortex-evolve/references/rules.md` (≤ 220, 升降级规则 + 修饰 + 金字塔)
- `skills/cortex-evolve/references/workflow.md` (≤ 220, 5 步执行流程)

## Dispatch Prompt

```
Active task: .trellis/tasks/06-10-cortex-evolve

## 目标
建 cortex-evolve skill (SKILL.md ≤ 60 行 + 3 references). 无脚本. skill 步骤指导 main 调 cortex-extract/save/lint 维护金字塔.

## 已知 (核心规则)
- 金字塔模型: L4 庞大 → L0 稠密. L0 越少越好.
- 主要工作区: L4-L2 自动双向 (升+降)
- L1/L0 自动升允许 (从下级 promote); 自动降禁止 (除非用户显式 forget)
- L1/L0 直接写入新条目 (非 promote) 必须 ask
- 三轴: 频率 (近期提及) / 时间 (距今) / 重要度 (weight)
- 修饰: 用户反复强调 → 跳级允许; L0 条目数 > 20 → lint warn

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

## SKILL.md 结构
1. frontmatter
2. 1 段总览 (金字塔 + 升降级目标)
3. 速查表: 升级触发 / 降级触发 / 例外
4. 路由表 (3 references)
5. 入口: 无独立脚本, 步骤参 workflow.md
6. 引用 cortex-extract/cortex-save/cortex-lint/cortex-schema

## references 内容 (按 design.md "references/*.md" 节展开)

### signals.md
- 三轴 (频率/时间/重要度) 定义 + 计算公式 (频率窗口 14d, 时间阈 7d/90d, 重要度 weight 字段)
- 综合得分 promote_score / demote_score (加权求和 0.4/0.3/0.3)
- 阈值 ≥ 0.7 触发

### rules.md
- 升级规则 (各级 + 阈值)
  - L3→L2: promote_score ≥ 0.6
  - L2→L1: promote_score ≥ 0.7 + 复用 ≥ 5 + weight ≥ 0.8
  - L1→L0: promote_score ≥ 0.9 + 用户多次强调 (≥ 3) + 复用 ≥ 10
- 降级规则 (各级 + 例外)
  - L2→L3: demote_score ≥ 0.7 + 30d 未访问
  - L3→L4: 不直接, 走 lint forget candidate
  - L1/L0: **不主动降**, 仅标 audit-candidate
- 5 修饰规则:
  1. 用户反复强调 (≥ 3) → 跳级允许 (L3→L1)
  2. L1/L0 自动升允许 (从 promote, 不 ask)
  3. L1/L0 新写入 (直接) 必须 ask
  4. L1/L0 不主动降 (硬规)
  5. L0 audit: 条目数 > 20 → lint warn
- 适用范围速查表

### workflow.md
- 5 步流程 (--scan → 评分 → plan → 用户审 → apply)
- 与 cortex-extract 边界 (extract = inbox 路由; evolve = 既有条目跨级)
- 与 cortex-save 边界 (save = 一次性写入; evolve = 移动既有)
- dry-run JSON plan 字段 schema
- apply 调 cortex-save / cortex-lint --fix 移动文件 + 更新 frontmatter level

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-evolve/** (新建)
禁改: 其他

## 输出限
- SKILL.md ≤ 60 行
- 各 reference ≤ 220 行

## Sub-agent 自防护
trellis-implement, 不再 spawn.

完成回报: 4 文件清单 + 行数 + 验证退出码.
```

## 回滚
```bash
rm -rf plugins/tools/cortex/skills/cortex-evolve/
```
