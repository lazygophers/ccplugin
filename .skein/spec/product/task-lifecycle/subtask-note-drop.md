---
title: subtask done/check 静默丢弃 --note
namespace: product
category: task-lifecycle
keywords: [subtask,note,留痕,cli]
status: active
inclusion: auto
anchors: plugins/tools/skein/scripts/skeinlib/cli.py:148
---

## 现象

`skein subtask done <tid> <sid> --note "..."` 与 `subtask check ... --note "..."` 都**接受**该参数但**不落盘**，
且不报错、不告警。调用方以为留痕成功，实际内容完全蒸发。

## 依据

`cli.py:140` 的注册是 `st.add_argument("--note", help="[fail] 失败备注")` —— 只有 `fail` 分支消费它。
argparse 层面 `done` / `check` 照收不误，所以 CLI 不会拒绝。

实测：给 `dag-parent-nesting` 的 d5 / d6 写过长段 note，事后读 task.json，两者 subtask 记录里
**不存在任何 note 类字段**（2026-08-02 核实）。

## 代价

exec 阶段的判定依据（为什么这项算过、哪项没过、凭什么判断）是 check 阶段的关键输入。
静默丢弃等于让每个 executor 的自证材料随手蒸发，check 只能从零重查。

## 现行绕法

判定留痕写进 `.skein/task/<tid>/design.md`（planning 期）或 `prd.md` 对应验收项下的缩进备注行。
后者在 check 阶段也可写，且与验收项就近，比 design.md 更好找。

## 修法方向

要么让 `done` / `check` 也落 note，要么在这两个分支收到 `--note` 时显式报错。
**静默接受是最坏的一种** —— 比直接拒绝更伤，因为调用方不会重试。
