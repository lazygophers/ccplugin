---
inclusion: auto
title: gate
layer: core
category: planning
keywords: [plan,完成判据,exec,checklist,硬门,4条,planning收敛,confirm,start,prd,validation,hard-gate,completeness,就绪,hook,slash,命令,短路,路由,启发,/skein-,UserPromptSubmit]
status: active
---

## plan 阶段完成判据门

### 铁律
- MUST：plan 阶段完成判据门勾满才转 exec（4 条 checklist 全勾）
- MUST：判据门为硬约束，未勾满禁 `skein start`
- MUST：4 条判据：①task 已 create (含可读 slug) ②prd.md 已填完 (各章 `- [ ] TODO` 全勾) ③subtask 已规划 (`subtask add` 落 task.json DAG) ④设计方案已定 (design.md 正文; 或 main 豁免)
- MUST：豁免条件仅 main 可判定（简单任务可略设计方案，但其余 3 条仍须勾）

### 反例表
| 禁 | 改为 |
|---|---|
| prd TODO 未勾完即 start | 勾满 4 条才 start |
| 无 subtask 规划即转 exec | 至少拆分 subtask 并登记 DAG |
| 设计方案未定即 start | 填完 design.md 正文 (或 main 判定豁免) |
| 自降判据标准「差不多就行」 | 4 条逐条硬核验 |

### 触发场景
- plan 阶段收尾前自查 4 条 checklist
- `skein start` 前脚本校验判据门（未过拒 start）
- planning 流程 checkpoint

### 关联
- 铁律: prd 硬门（主门在 confirm，start 兜底）(core/planning/task-detail-enhance-52.md) — 互补，本门是 plan 完成判据，prd 门在 confirm 主校验
- 实现细节: skein-plan SKILL.md §✅ plan 阶段完成判据 (2026-07-21落地)

## prd 硬门（主门在 confirm，start 兜底 double-check）

### 铁律
- MUST：prd 硬门**主校验在 `skein confirm`**（待处理→就绪）：prd 章节齐 + 无占位 + ≥1 subtask，通过才进就绪
- MUST：prd.md 存在且四标准章节齐备（目标/边界/验收标准/索引），无 `- [ ] TODO` 占位（模板初始态）
- MUST：`skein start`（就绪→进行中）**兜底 double-check `_validate_prd`**，防 confirm 后 prd 被改空
- MUST：不通过 raise SystemExit 阻断（confirm 阻进就绪 / start 阻进行中）

### 反例表
| 禁 | 改为 |
|---|---|
| confirm 不检查 prd/subtask 就进就绪 | confirm 跑 _validate_prd + ≥1 subtask 校验 |
| prd 章节残缺仍允许 confirm | 检查四标准章节齐备且顺序一致 |
| prd 含 TODO 占位仍 confirm | 检测占位并拒绝进就绪 |
| start 完全信任 confirm 不复检 prd | start 仍兜底 _validate_prd 防中途被改空 |

### 关联
- task.json status 状态机（待处理 →confirm→ 就绪 →start→ 进行中 守卫）
- subtask 拆分前置门（confirm 前须有 ≥1 subtask 登记）
- 铁律: skein 工作流连线（confirm 用户确认门）

## 显式 slash 命令跳过 hook 路由启发

### 铁律
- MUST：用户显式调用 `/skein-` 或 `/skein:skein-` 开头的 slash 命令时，`cmd_user_prompt` 直接返回 0 不注入 `_CTX` 流程判定
- MUST：短路判断在 prompt strip 后进行（`prompt.strip().startswith()`）
- MUST：显式 slash 调用视为用户已决定走 skein 流程，无需路由启发判定

### 反例表
| 禁 | 改为 |
|---|---|
| slash 命令仍注入 _CTX 走路由启发 | 前缀短路直接返回 0 |
| 未 strip prompt 即判断前缀 | strip 后再判断 |
| 仅判断 `/skein-` 忽略 `/skein:skein-` | 两前缀均覆盖 |

### 触发场景
- 用户输入 `/skein-plan`、`/skein-create` 等 slash 命令
- hook 接收到显式 skein 命令格式调用
- UserPromptSubmit hook 收到 `/skein:skein-` 开头的 prompt

### 关联
- hook 判定防自降级护栏 (core/planning/hook-prompt-judge-ai-only-57.md) — 互补，一个是防自降级，一个是显式调用短路
