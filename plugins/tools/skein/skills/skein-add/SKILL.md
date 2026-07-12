---
name: skein-add
description: '➕ 规划级入口 (只规划不执行): 把请求纳入 SKEIN task 的 planning 阶段 — 判新旧 + skein.py create 登记 + brainstorm + grill 硬门, 产出 prd/implement 后停在 skein.py start 之前, task 留 planning 态, 禁 exec/check/finish。用户想"先看规划再决定执行 / 添加规划任务 / 只规划不动手"时用。仅显式调用 (/skein-add), 禁 model 自动触发。与 skein-flow/skein-go 边界: 后者=强制全闭环 (plan→exec→check→finish), add=只到 planning 停'
user-invocable: true
argument-hint: "<任务描述>"
arguments: "<任务描述>"
model: sonnet
effort: medium
---

# skein-add — 规划级入口 (只规划不执行)

用户**显式调用**本 skill, 把请求纳入 SKEIN task 的 **planning 阶段并停下**: 判新旧 + 登记 + 交互式 planning, 产出 `prd.md`[+`design.md`]+`implement.md` 后**停在 `skein.py start` 之前**, task 留 **planning 态**, 交还控制权。**禁 exec/check/finish** — 那是 `skein-flow` / `/skein-go` (全闭环) 的职责。

本 skill 是 planning 真值源 `skein-planning` 的**用户可调 façade** (planning 正文零复制): 委托 `skein-planning` 无参 (= 跑完 STOP), 借完产物即交还。**禁复制 planning 正文, 禁按参数分叉。**

## 调用边界

- ✅ **仅显式触发**: 只有用户 `/skein-add` 或明确"只规划不执行 / 先看规划"意图才进入。**禁 model 自动触发** (自动全闭环是 `skein-flow` 的职责, add 不抢)。
- ⛔ **禁 exec/check/finish**: add 终点 = planning 态 task。**禁跑 `skein.py start` / 禁派 exec subagent / 禁 check / 禁 finish**。要执行 → 用户自行 `/skein-go <task>` 或 `/skein-flow`。
- ⛔ **仍禁**: 把明显该 inline 的极简请求 (纯查询 / 单文件 ≤20 行) 强行建 task (作用域边界见下)。
- 🔗 **邻居边界**: `skein-flow` / `/skein-go` = 强制全闭环 (双模/命令); `skein-add` = 只到 planning 停 (仅显式)。不误抢。

## 流程 (委托 skein-planning 无参, 到此停)

> **前置**: 无 `.skein/` → 先 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py init`。

1. **委托 `skein-planning` 无参** (main 同步前台) — 判新旧 + `skein.py create` 登记 + brainstorm (逐问用户) + grill 硬门 + 写 `prd.md`[+`design.md`]+`implement.md`。**全程 main 同步** (brainstorm/grill 需 `AskUserQuestion`, subagent 不能与用户对话; 纯信息调研可派 `skein-researcher` 只读)。planning 正文一切以 `skein-planning` 为准, 本 skill 不复述。
2. **停在 start 前** — 产物齐 → **停**, task 留 planning 态, 跑 `skein.py board` 更新看板 (状态 planning), 交还控制权。回传用户: planning 产物摘要 + "已规划完成, 停在执行前; `/skein-go <task>` 或 `/skein-flow` 执行"。**禁 start / exec / check / finish**。

## 硬规

- 🗂️ **`skein.py create` main 同步跑** — 任务记录管理, 不派 agent。add **不跑 `skein.py start`** (那是激活/执行, 归 flow/go)。
- 💬 **planning 全程 main 同步前台** — brainstorm 逐问用户, 不派 subagent、不执行。
- 🔒 **`.skein/task.md` 禁直接 Edit/Write** — 看板必经 `skein.py board` (guard hook 硬阻)。
- 🧑 **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) 必用工具, 禁纯文本代替。
- 🔴🛑 **"已建 task / 看板已登记"必须是真跑过 `skein.py` 的结果** — 宣称 ≠ 调用 = 幻觉跳步。

### 作用域边界 (何时建 task)

| 特征                              | 判定                         |
| --------------------------------- | ---------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task              |
| 单文件单处改, ≤20 行且位置已知    | 豁免                         |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                |
| 需外部调研 / 产出文档交付         | **必建 task** (调研走 research) |
| 边界模糊                          | **AskUserQuestion 用户裁定** |

## 失败模式 (触发 → 一线修复 → 仍失败兜底)

| 触发                              | 一线修复                                   | 仍失败兜底                                             |
| --------------------------------- | ------------------------------------------ | ----------------------------------------------------- |
| 非 SKEIN 项目 (无 `.skein/`)      | 跑 `skein.py init` 初始化后继续            | 用户拒绝初始化 → 降级口头给规划框架, 不落 task         |
| 判新旧不准 (新任务 vs 补现有)     | 🛑 STOP `AskUserQuestion` 用户裁定          | 用户也拿不准 → 默认建独立新 task, 禁静默并入他 task    |
| brainstorm 卡住 / 用户信息太少    | grill 轴 A/B 当提问引擎逐项追问回填 PRD    | 仍答不清核心目标 → 🛑 STOP 圈定最小 MVP, 超出标后续迭代 |
| `skein.py create` 失败 (路径/权限) | 报错停, 修复后重跑, 禁跳过                  | 仍失败 → 明确告知未登记, 禁口头宣称"已建 task"         |

## ⛔ 反例 (命中 = 流程错误, 改方案重来)

| #   | 禁做                                          | 改为                                        |
| --- | --------------------------------------------- | ------------------------------------------- |
| 1   | add 跑 `skein.py start` / 派 exec / check / finish | add 只到 planning 停; 执行归 flow / `/skein-go` |
| 2   | 复制 `skein-planning` 正文进本 skill          | 委托 `skein-planning` 无参 (真值源, 零复制)  |
| 3   | model 自动触发 add                            | add 仅显式; 自动全闭环是 flow 职责           |
| 4   | main / agent 凭空设计需求方案                  | brainstorm 逐问用户主导                      |
| 5   | 把 `skein.py create` 派 agent 执行            | main 同步跑                                  |
| 6   | 纯文本提问代替 `AskUserQuestion`              | 用户确认 / 选择必用工具                      |
| 7   | 口头宣称"已建 task"但本回复无 `skein.py` tool_use | 先真实调用再回传 (宣称 ≠ 调用)              |
| 8   | 把明显该 inline 的极简请求强行建 task          | 作用域边界表判                              |

## 相关

- `skein-planning` — planning 真值源 (本 skill 委托它); `user-invocable:false`, 故用户经本 façade 调用。
- `skein-flow` / `/skein-go` — 强制全闭环 (plan→exec→check→finish); 消费本 skill 攒下的 planning 态 task。
- `skein-grill` — 对抗审查 (planning 硬门); `skein-researcher` — 只读调研。
