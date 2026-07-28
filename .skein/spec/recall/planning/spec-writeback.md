---
title: spec-writeback
layer: recall
category: planning
keywords: [specer,sediment,reconstruct,prune,maintain,apply,自愈,budget,pending-fix,auto-fix,fire-and-forget,闭环]
status: active
---

## specer 写 mode 自愈范式 (maintain --apply 闭环 + auto-fix 兜底)

### 铁律

- MUST：skein-specer 三写 mode (sediment / reconstruct·maintain / prune) 末尾必跑 `python3 scripts/spec.py maintain --apply` 就地自愈 — 写盘可能致 core 超 budget, 就地降级最少复用 core 规则到 recall, 不留 `.pending-fix` 给 Stop hook 二次派本 agent
- MUST：auto-fix mode 保留作兜底兼容 — sediment/reconstruct/prune 自愈后不再产生 .pending-fix, 但 sediment 遗漏 / 历史 .pending-fix 残留 / Stop hook 检出非写 mode 引发的问题仍走 auto-fix fire-and-forget
- MUST：maintain --apply 修不掉的项 (断链 / 降级后仍超) 入 `unfixed_links` / `needs_main` 报具体项, 禁静默 — 断链修哪头需人判断, 无从自动决断
- MUST：所有降级 / 归档走可逆 `skein-spec archive` (`.archive/<ts>/`, `restore <ts>` 回滚), 禁直删

### 反例表

| 禁 | 改为 |
|---|---|
| 写 mode 仅 `skein-spec reindex` 收尾, 超预算留给 Stop hook 检测后 auto-fix 兜底 | 写 mode 末尾必跑 `maintain --apply` 就地修, auto-fix 仅作兜底 |
| maintain --apply 遇断链自动改链或建目标 | 断链只报告入 `unfixed_links` 交人判 |
| 降级 / 归档直删文件 | 全走可逆 `skein-spec archive` |
| maintain --apply 修不掉静默吞 | 报 `needs_main` 让 main 介入 |

### 触发场景

- skein-specer 跑 sediment / reconstruct / maintain / prune 任一写 mode 收尾
- core 写盘后字符数 > `spec_core_budget` (config.yaml, 当前 12000)
- Stop hook 写 `.pending-fix` 后 main 派 auto-fix

### 落地范式

**写 mode 三步闭环骨架** (本铁律的可复用模板):

```
skein-spec sediment --layer=<core|recall> --category=<类目>
skein-spec reindex
python3 scripts/spec.py maintain --apply   # 写盘后必跑, core 超 budget 就地降级
```

**自愈层级**: 写 mode 末尾 `maintain --apply` 是第一道 (写盘引发超 budget 立即修) → Stop hook `.pending-fix` 检测是第二道兜底 (session 中途 core 膨胀 / 非写 mode 引发) → 两道均 fire-and-forget, 异步不阻塞。

### 案例

- commit `9ffe3f356` skein(config): use_worktree false 同期改 skein-specer.md 加三写 mode 末尾 `maintain --apply`, auto-fix mode 降为兜底
- 代码证据: plugins/tools/skein/agents/skein-specer.md:20-26 (sediment), :33-38 (reconstruct/maintain), :44-48 (prune)

### 关联

- 铁律: 状态先行铁律 (core/planning/sediment from state-before-action-69.md) — 互补, 本规则是 specer 写 mode 的状态闭环 (写盘→reindex→maintain --apply)
- 工作流: skein-spec SKILL.md §auto-fix (Stop hook 触发全自动 spec 修复) — 兜底承载
- memory: skein-flow-judge-three-tier (判定三分法)
