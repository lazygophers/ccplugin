# Design — cortex 默认 apply

## S1 脚本 + python (code)
- lint.sh: `MODE="check"` → `MODE="fix"`; 头注释 "默认 dry-run (--check)" → "默认 --fix 落盘; --check opt-in 预览"
- extract.sh: `MODE="dry-run"` → `MODE="apply"`; 注释同理
- ingest.sh: `MODE="dry-run"` → `MODE="apply"`
- history-digest.sh: `MODE="dry-run"` → `MODE="apply"`
- _extract/router.py: L0-core 决策 `mode="ask"` → `mode="auto"` (ask=False); 注释更新
- _extract/__init__.py + writer.py: `CORTEX_EXTRACT_L0_AUTO` 默认值 → "accept" (或移除 ask 分支, L0 直接写)
- _history_digest/router.py: L0 候选 needs_ask → 直接路由 (无 ask 标记)
保留 --dry-run/--check flag 解析不动。

## S2 5 skill 文档
lint/extract/ingest/history-digest/evolve SKILL.md + references:
- "默认 dry-run/--check" → "默认 apply/--fix (--dry-run/--check opt-in 预览)"
- 删 worker "后台扫描段=plan / 主会话段=ask+apply" 的 ask 分段 → worker 默认 apply 直接落盘; 保留破坏性提示
- 删 needs_ask 表述

## S3 契约 + recall/context-digest
- cortex-schema/references/memory-levels.md: 删 "L0 写入永远 ask" 硬规 (L0 级别语义保留, 仅去 ask)
- cortex-recall/{SKILL.md,references/writeback.md}: "L0/L1 仍 ask" → 默认自动写
- cortex-context-digest/references/scope.md: L0 ask 表述清理

## S4 5 worker agent
agents/cortex-*-worker.md: 删 "禁 apply / needs_ask 留主会话 / 不落盘" → worker 跑脚本默认 apply 直接落盘 (仍 Read/Glob/Grep/Bash, 无 Write/Edit; 写盘经脚本)

## S5 agent + 文档
- agents/cortex.md: "默认 dry-run, 用户确认才 apply" → "默认 apply 落盘"; L0 ask 表述删
- README/llms: "dry-run 默认 / L0 写入永远 ask" → "默认 apply"
- tests/e2e-report.md: L0 ask 注记更新

## S6 验证
- 4 脚本无参 = apply: 对 fixture 跑 (extract/lint) 确认写盘, 然后 git checkout 还原 fixture
- extract --apply L0 项落盘验证 (L0-core 样本)
- grep 残留: 永远 ask / needs_ask / 默认 dry-run / 默认 (--check) 清零
- git checkout fixture 还原; 全暂存
