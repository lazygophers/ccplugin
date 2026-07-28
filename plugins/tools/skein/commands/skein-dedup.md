---
name: skein-dedup
description: 主动查重 + 织 DAG (用户显式调用)。扫未完成 task 检重复/重叠 (归并次 task), 并给待处理/就绪 task 补执行序 — 只归并判据确凿的, 存疑保留
disable-model-invocation: true
user-invocable: true
argument-hint: "[task-id 或留空扫全量]"
arguments: "[task-id]"
model: haiku
effort: low
agent: skein-dedup
---

# skein-dedup — 主动查重与执行序编排

平时 dedup 由 main 在 planning 收尾 fire-and-forget 派发。本命令让用户**随时手动触发**一次全量扫描 (如批量建 task 后, 或怀疑看板堆了重复 task 时)。

## 入参: task-id

- **省略** → 扫全部未完成 task (`--status open`), 查重 + 补执行序。
- **`<task-id>`** → 只以该 task 为中心比对: 它与谁重复、它该依赖谁 / 谁该依赖它。其余 task 之间不动。

## 派发

同步派 `skein-dedup` agent (非后台 — 用户显式触发要等结果), 完成后向用户回传处置摘要。

## 处置面 (agent 内执行, 此处为验收口径)

| 动作 | 适用状态 | 铁律 |
|---|---|---|
| 归并重复 task (迁 subtask + `del` 次 task) | 未完成全部状态 | 判据不足**不归并**, 记 skipped |
| 补前置执行序 (`deps --set`) | **仅待处理 / 就绪** | 进行中/检查中已 start 调度已定, CLI 会拒, 直接跳过 |
| 改既有 deps | — | **禁** — 已有 deps 一律不碰 (保护 plan/人工声明) |

## 输出

处置摘要: 归并了哪些 (from → into + 判据)、补了哪些执行序 (after → depends_on + 理由)、**哪些存疑保留** (判据弱 / CLI 拒的连法 + 原因)、工具失败项。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `skein` CLI 不可用 (alias 在 subagent 无定义) | 换 `python3 $CLAUDE_PLUGIN_ROOT/scripts/skein.py` | `[工具失败: CLI 不可用]`, 空处置回传, 禁手改 task.json |
| `deps` 报成环 / 自引用 | 换方向或跳过该连 | skipped 标「非法连法」+ 原因, 禁强连 |
| 两 task 疑似重复但判据弱 | 保守不归并 | 记 skipped, 宁漏归并不误删有效 task |
| 目标 task 状态为进行中/检查中 | 跳过其执行序编排 | skipped 标「已 start, 调度已定」 |

## ✅ 正向配方 (命中反面=操作错误)

> 🔒 铁律: 删 task 不可逆 — 只归并判据确凿的, 存疑一律保留。

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| 补执行序的候选面 | 只取待处理/就绪且 deps 为空的 (❌ 对进行中 task 试 `deps`) |
| 已有 deps 的 task | 不碰 (❌ 覆盖人工/plan 声明的前置) |
| 判据弱的疑似重复 | 记 skipped 保留 (❌ 硬凑重复 `del` 掉) |
| 归并次 task | 先 `subtask list` 读全量再逐条 `subtask add`, 最后 `del` (❌ 直接 `del` 丢 subtask) |
| 写盘方式 | 全经 skein CLI (❌ 手改 .skein/task/*/task.json) |
| 无关 task 之间 | 保持孤立不连 (❌ 硬连成一条链) |
