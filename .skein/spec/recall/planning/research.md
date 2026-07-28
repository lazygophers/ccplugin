---
title: research
layer: recall
category: planning
keywords: [planning,yagni,over-design,design,exploration,landing,possibility-branch,research,判定,分档,自动判,调研,灰区,信号]
status: active
---

## plan 研究期可过度探索, 落地设计守 YAGNI

### plan 研究可发散, 落地守现状

### 铁律

planning 期分**研究探索**与**最终设计**两阶段, 过度设计只在研究期允许:

- **研究期 (findings.md / 可能性分支)** — 鼓励过度发散: 探现状之外的扩展方案 / 未来约束变化时的演进分支 / 被否决的备选, 用于**探究当前方案的合理性边界** (为何这样选 / 换个约束会怎样)。每条可能性分支**必须标触发条件** (若未来需 X / 若约束变 Y)。
- **最终设计 (design.md 正文 + task.json DAG)** — **YAGNI 照常挥**, 只写满足当前需求的最小可行设计。禁塞"以后可能要"的扩展点 / 抽象层 / 配置项进落地设计。可能性分支**不进正文、不进 DAG、不生成 subtask**。

### 陷阱 → 正解

- **陷阱**: 把过度设计的产物写进 design.md 正文或 task.json DAG → exec 期实现了一堆当前用不上的抽象, 违背 YAGNI。
  **正解**: 过度设计产物只落 design.md「可能性分支」section + findings.md, 标触发条件, 不进 DAG。
- **陷阱**: plan 期彻底不发散, 只写最小设计 → 失去对方案合理性的探究, 选了次优解而不自知。
  **正解**: 研究环节主动过度探索边界, 用可能性分支反向验证当前方案为何最优。
- **陷阱**: 可能性分支不标触发条件, 变成无依据的臆想清单。
  **正解**: 无触发条件的纯臆想按 YAGNI 砍; 有触发条件才保留留痕。

### 触发场景

- grill YAGNI 轴审到"以后可能要"的 subtask / design 正文条目 → 先问: 这是落地设计还是研究留痕? 落地→砍; 研究→移到可能性分支标触发条件。
- design.md 正文出现抽象层 / 配置项 / 扩展点但当前需求用不上 → 砍到最小可行, 理由记可能性分支。

## research 判定门 自动分档决策

### 触发场景
planning 阶段 brainstorm 前，需判断是否派 skein-researcher 调研。不是等用户说「要调研」才派，而是按信号**自动分档判定**。

### 陷阱 → 正解
**陷阱**: main 临场感觉或等用户明确说「要调研」才派 researcher → 容易漏调研或延后决策。
**正解**: brainstorm 前先跑判定门，按信号分档自动决策（明确需/明确不需/保守灰区/激进灰区/兜底）。

**陷阱**: 所有 task 都先调研一刀切 → 降效、浪费时间。
**正解**: 分档判定，明确不需的跳 research 直 brainstorm。

### 分档判定表
| 档 | 信号 | 判定 |
| --- | --- | --- |
| **明确需** | 外部 API / 库选型 / 跨陌生子系统 / 现状代码未知 / 协议待定 | **自动派 researcher** |
| **明确不需** | 已知代码模式 / 用户给足信息 / 单熟悉子系统 / 单点改 | **跳 research, 直 brainstorm** |
| **保守灰区** | 倾向需但不明确（可能涉未知但不确定） | **自动派 researcher**（宁可调研） |
| **激进灰区** | 倾向不需但拿不准（看似简单但可能有坑） | **AskUserQuestion 问用户是否需 research** |
| **兜底** | brainstorm 中 subtask 切不动 / depends_on 定不了 | **触发派 researcher** 勘察代码再拆 |

### 探索封顶
派 researcher 后仍受「探索封顶」约束 — 够拆 subtask 即收敛，禁无限深挖。researcher 的结论持久化在 `.skein/task/<id>/research/`，planning 后续步骤（brainstorm/PRD）可复读。

### 关联
- 铁律: hook 判定防自降级护栏 (core/planning/hook-prompt-judge-ai-only-57.md) — 互补，一个是 AI 自身判定，一个是是否派 subagent
- 实现细节: skein-plan SKILL.md §🧭 research 判定门 (2026-07-21落地)
