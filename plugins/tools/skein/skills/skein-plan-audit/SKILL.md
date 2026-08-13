---
name: skein-plan-audit
description: "plan 阶段产物独立审计器 (只读, 非门控)。扫 PRD 七段 / design.md / contracts / subtask DAG / estimate 等 plan 产物, 沿 8 条审计轴找 planning 质量盲点, 输出 JSON 弱点报告。绑定 agent skein:skein-plan-auditor。独立于 plan 流程, 目前不被任何 skill 引用。"
user-invocable: true
argument-hint: "[task-id | 路径]"
arguments: "[task-id 或 .skein/task/<tid> 路径]"
model: sonnet
effort: medium
---

# skein-plan-audit — plan 阶段产物独立审计器

> 🔒 全局流程规则（状态机/调度/优先级等）以 skein-flow/references/ 为单一真值源。

> **绑定 agent**: `skein:skein-plan-auditor` — agent 执行逻辑详见 `agents/skein-plan-auditor.md`。

只读审计 **plan 阶段产物** (PRD / design.md / contracts / subtask DAG / estimate 等), 输出 JSON 弱点报告。**不是门控** — 不阻塞 confirm / 不改任何盘 / 不替代 grill 硬门。

## 审计对象

只审 plan 阶段产出的工件, 不审代码 / diff / 执行结果:

| 产物 | 路径 | 审计内容 |
|------|------|----------|
| PRD | `.skein/task/<tid>/prd.md` | 七段齐备 / 无 TODO 占位 / 需求真伪 / 边界明确 |
| design.md | `.skein/task/<tid>/design.md` | 架构取舍 / 测试接缝填实 / 可能性分支标了触发条件 |
| contracts | `skein contract <tid>` 输出 | 不变量逐条落盘 / 与 design 一致 |
| subtask DAG | `task.json` 的 `subtasks[]` | DAG 完整无环 / 拆分粒度 / 并行度 |
| estimate | task + subtask `estimate` 字段 | 自下而上 / 无占位整数 / task ≥ Σ subtask |

## 流程

```
1. 定位 task → 读取全部 plan 产物
2. 跑 skein-spec analyze <tid> --json (复用一致性核查, 不重复造轮)
3. 沿 8 条审计轴逐轴扫描 (见 references/audit-axes.md)
4. 聚合弱点, 按严重度分级 (Blocker / Major / Minor)
5. 输出 JSON 报告
```

### 1. 定位 + 读取

```bash
# 有 task-id
tid=$1
dir=".skein/task/$tid"

# 无参数 → 取最近 pending
tid=$(skein list --status pending --json | jq -r '.tasks[0].id')
```

读取 `prd.md` / `design.md` / `task.json`, 跑 `skein contract <tid>` 取契约, 跑 `skein-spec analyze <tid> --json` 取一致性核查结果。

### 2. 八轴扫描

详见 `references/audit-axes.md`。每轴产出 findings 列表。

### 3. 输出 (JSON)

```json
{
  "task_id": "<tid>",
  "task_name": "<task 标题>",
  "verdict": "CLEAN | HAS_BLOCKER | HAS_MAJOR | HAS_MINOR",
  "findings": [
    {
      "axis": "需求真伪|边界|假设|DAG|验收|drift|scope|工时",
      "severity": "Blocker|Major|Minor",
      "finding": "<弱点描述>",
      "evidence": "<file:line / 原文引用>",
      "suggestion": "<可操作改进建议>"
    }
  ],
  "spec_analyze": {
    "ran": true,
    "candidates": [
      {"category": "验收覆盖率|硬规冲突|范围蔓延|proposed置信度|接缝存在性", "note": "<候选说明>"}
    ]
  },
  "axis_coverage": {
    "需求真伪": "pass|findings|skipped",
    "边界": "pass|findings|skipped",
    "假设": "pass|findings|skipped",
    "DAG": "pass|findings|skipped",
    "验收": "pass|findings|skipped",
    "drift": "pass|findings|skipped",
    "scope": "pass|findings|skipped",
    "工时": "pass|findings|skipped"
  },
  "tool_failures": ["[工具失败: <原因>]"]
}
```

`verdict` 取所有 findings 中最高严重度; 无 findings = `CLEAN`。

JSON 供下游消费 — 喂给 grill 做交互裁决、入 CI 做 planning 门禁、人审参考均可。

## 审计轴

详见 `references/audit-axes.md` — 8 条轴逐条定义、扫描方法、严重度判定、典型反模式。

## 与 grill 的区别

| 维度 | skein-grill (硬门) | skein-plan-audit (本 skill) |
|------|---------------------|------------------------------|
| 定位 | confirm 前强制门, 交互式逐条逼问用户裁决 | 独立扫描, 产 JSON 报告, 不交互 |
| 时机 | plan 产物就绪后、confirm 前 | 任意时刻 (plan 中 / plan 后 / 事后复盘) |
| 载体 | main 亲做 (需 AskUserQuestion) | 可派 skein-plan-auditor subagent, 可自动化 |
| 输出 | 弱点表 → 逐条裁决 → 补回工件 | JSON 弱点报告 (不裁决不改盘) |
| 关系 | 门控层 | 分析层, 可给 grill 喂输入 |

## 失败模式 (if-then 三段式)

| 触发 | 一线修复 | 仍失败兜底 |
|------|----------|------------|
| 产物不齐 (缺 design.md / contracts 空) | 读已有产物, 缺的标 `产物缺失` 不阻塞 | 全无产物 → 报「task 尚未 planning, 无可审计」 |
| `skein-spec analyze` 报错 | 跳过 analyze, 手工补一致性检查 | 全部手工, 标 `analyze 未跑` |
| 某轴扫不出弱点 (太顺) | 换角度深挖 (极端输入 / 并发 / 依赖失效 / 反向问) | 显式记「该轴已过, 无阻断项」, 禁把没想到当没问题 |

## ✅ 正向配方

| 场景 | 正确做法 (❌ 反面) |
|------|---------------------|
| 审计定位 | 只读不改, JSON 报告交人判 (❌ 直接改 PRD / task.json) |
| 与 grill 关系 | 产报告可给 grill 喂输入, 不替代 grill 门控 (❌ 跳 grill 用 audit 过门) |
| 某轴太顺 | 默认有盲点, 深挖到为止 (❌ 扫不出就当没问题) |
| 严重度判定 | Blocker = 不修不该 confirm; Major = 影响质量; Minor = 可选 (❌ 全标 Blocker / 全标 Minor) |
| 复用已有工具 | 先跑 `skein-spec analyze` 再手工补 (❌ analyze 能查的手工重查) |
