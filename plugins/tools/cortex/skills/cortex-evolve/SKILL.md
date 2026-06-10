---
name: cortex-evolve
description: "记忆库升降级维护 — 按金字塔模型 (L4 庞大 → L0 稠密) 自动 promote/demote. 信号: 频率 (近期提及) / 时间 (距今) / 重要度. 规则: 用户反复强调 → 逐级升; L1/L0 允许自动升不允许自动降. 主要工作区 L4-L2; L1/L0 写入新条目仍 ask. 无独立脚本, 调 cortex-extract/save/lint 执行."
when_to_use: "升级记忆/降级记忆/promote/demote/记忆再平衡/金字塔维护/记忆 audit/evolve"
argument-hint: "[--scan|--dry-run|--apply] [--target <vault>]"
arguments: "[--scan|--dry-run|--apply] [--target <仓库根>]"
user-invocable: true
---

# cortex-evolve

记忆库**跨级再平衡**, 按金字塔模型 (L4 庞大 → L0 稠密) 自动 promote/demote 已入 vault 的条目. L0 越少越好, L4 容量大. 与 `cortex-extract` 边界: extract = L4-inbox 入门级路由; evolve = 已入 vault 后跨级再平衡. **无独立脚本**, 步骤指导 main 调 `cortex-extract` (复用三轴评分) / `cortex-save` (移动文件) / `cortex-lint --fix` (frontmatter level 校正).

## 速查表

| 触发 | 条件 | 行为 |
| --- | --- | --- |
| 升级 (主) | promote_score ≥ 阈 (各级不同) | 移文件 + 改 frontmatter level |
| 降级 (主) | demote_score ≥ 0.7 + 30d 未访问 (仅 L2→L3) | 移文件 + 改 level |
| 用户反复强调 (≥ 3) | "永远/硬性" 多次 | 跳级允许 (L3→L1 直跳) |
| **L1/L0 自动升** | 从 L2/L1 promote | 允许 (不 ask) |
| **L1/L0 自动降** | 任何信号 | **禁** (仅标 audit-candidate, 用户显式 forget 才动) |
| L1/L0 直接写新 | 非 promote 路径 | **必须 ask** |
| L0 audit | 条目数 > 20 | lint warn |

## 适用范围

- 自动双向: **L3 ↔ L2** (主要工作区)
- 自动升单向: **L2 → L1 → L0** (无需 ask, 仅标 audit-candidate)
- 自动降禁止: **L1 / L0**
- 不在范围: L4 → L3 (走 `cortex-extract`); 一次性写入 (走 `cortex-save`)

## 路由表 (3 references)

| 任务 | 文件 |
| --- | --- |
| 查三轴信号 (频率/时间/重要度) 定义 + 计算公式 + 综合得分 | `references/signals.md` |
| 查升降级各级阈值 + 5 修饰规则 + 金字塔约束 + 适用范围速查 | `references/rules.md` |
| 查 5 步执行流程 + dry-run JSON schema + 边界 vs extract/save | `references/workflow.md` |

## 执行入口

无独立脚本. 步骤由 main 执行 (详见 `references/workflow.md`):

1. `--scan`: 列 vault `memory/L0-core` ~ `memory/L4-inbox` 全部条目
2. 评分: 跑三轴 → `promote_score` / `demote_score` (复用 `cortex-extract` 三轴模式)
3. plan: 按 `rules.md` 输出 JSON (file / current_level / proposed_level / score / reason)
4. 用户审: 展示 plan, 对 L1/L0 升级与跳级条目要求确认
5. `--apply`: 调 `cortex-save` 移文件 + `cortex-lint --fix` 校 frontmatter level

## 引用

- 5 级路径与 frontmatter 模板: `cortex-schema`
- 三轴评分原型 + L4-inbox 路由: `cortex-extract`
- 一次性写入 (新条目): `cortex-save`
- frontmatter level 校正 + L0 audit warn: `cortex-lint`
