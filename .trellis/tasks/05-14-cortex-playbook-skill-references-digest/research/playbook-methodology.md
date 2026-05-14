# agent-playbook 方法论摘要 + cortex 借鉴映射

> 源: https://github.com/zhaono1/agent-playbook
> 主分支文件已读: README.md / docs/context-layering-for-agent-playbooks.md / docs/automation-best-practices.md / skills/long-task-coordinator/SKILL.md / skills/skill-router/SKILL.md / skills/self-improving-agent/SKILL.md / skills/workflow-orchestrator/SKILL.md / skills/planning-with-files/SKILL.md
> 读取时间: 2026-05-14

## 1. Context Layering 三层模型 (docs/context-layering-for-agent-playbooks.md)

| Layer | 内容 | 大小特征 |
|---|---|---|
| L1 Always-on constraints | 安全/权限/交付/完成定义 + 少量高频行为约束 | 短, 稳定, 每会话加载 |
| L2 Routing cards | 工作流提醒, 短 rule + 指向 skill/reference | 薄 |
| L3 On-demand references | 详细程序/模板/例子, 仅任务需要时加载 | 深度内容居此 |

Skill 编写规则:
1. SKILL.md 保持 lean + procedural
2. 详细 example / template / 长解释挪 references/
3. 优先小 focused reference 文件, 不要单大手册
4. 文件名让检索显然
5. 公开 skill 抽象 + 可移植

**直接映射到本任务 R1/R2** — cortex-ingest 497 行 / cortex-digest 即将膨胀, 必须拆 references/。

## 2. Long-Task Coordinator (skills/long-task-coordinator/SKILL.md)

核心规则:
- 一个长任务一份持久 state 文件 (chat history 不可靠)
- state 含: goal / success criteria / status / current step / completed / next action / next checkpoint / blockers / active owners
- 角色分: Origin (目标) / Coordinator (state+sequencing) / Worker (子工作) / Watchdog (liveness)
- 每轮序列: `READ -> RECOVER -> DECIDE -> PERSIST -> REPORT -> END`
- `awaiting-result` 是合法状态 (worker dispatched but result not back)
- 非终结轮必产生真进展 (dispatch / consume / update / persist / recover 至少 1 项)
- recovery 与 domain work 分离

**本任务不借鉴** — 用户明确"其余不动", P0-2 跳过。

## 3. Self-Improving Agent (skills/self-improving-agent/SKILL.md)

Multi-memory 架构:
- **Semantic Memory** (`memory/semantic-patterns.json`): 抽象 pattern / rule, 跨上下文复用
  - 字段: id / name / source / confidence / applications / created / category / pattern / problem / solution / quality_rules / target_skills
- **Episodic Memory** (`memory/episodic/YYYY/YYYY-MM-DD-<skill>.json`): 具体经验, 含 timestamp / skill / situation / root_cause / solution / lesson / related_pattern / user_feedback
- **Working Memory** (`memory/working/`): 当前 session context / 错误 context / session end marker

Self-improvement loop:
1. Skill event 触发 (hooks: before_start / after_complete / on_error)
2. 抽取 experience (what happened / what went well / what went wrong / root cause)
3. 抽象为 pattern → 入 semantic
4. confidence 高时, 反写相关 skill

Evolution Priority Matrix (示例, 不全列):
| Trigger | Target Skill | Priority |
|---|---|---|
| New PRD pattern discovered | prd-planner | High |
| Debugging fix discovered | debugger | High |
| Review checklist gap | code-reviewer | High |

**直接映射到本任务 R3** — cortex 现有 episodic (jsonl) + working (hot.md), **缺 semantic**, 融入 cortex-digest 第 5 类抽取。

差异:
- agent-playbook 用 JSON, cortex 走 markdown (vault md-native 约定)
- agent-playbook 自动 patch skill, cortex 走 proposal + 用户确认 (cortex-refactor 模式)
- cortex 反写仅限 .md (SKILL/AGENT), 禁 patch python/bash

## 4. Workflow Orchestrator + Auto-Trigger (skills/workflow-orchestrator/SKILL.md + skills/auto-trigger/SKILL.md)

声明式 hook frontmatter:
```yaml
metadata:
  hooks:
    after_complete:
      - trigger: <skill-name>
        mode: auto | background | ask_first
        condition: <expr>
        reason: "..."
    on_error:
      - trigger: <skill-name>
        mode: background
```

Modes:
- `auto`: 立即执行不询问
- `background`: 后台执行不阻塞
- `ask_first`: 用户确认前不执行

Milestone detection: PRD complete / implementation complete / self-improvement complete / universal learning (任一 skill 完成)。

**本任务不借鉴** — 用户明确"其余不动", P1-3 跳过。

## 5. Skill Router (skills/skill-router/SKILL.md)

意图分析 → keyword + semantic + context → 推荐 skill + clarifying question + 多 skill orchestration 建议。

**本任务不借鉴** — cortex description 池语义匹配已覆盖, 价值边际。

## 6. Planning with Files (skills/planning-with-files/SKILL.md)

3 文件模式: `task_plan.md` (phases+progress) + `notes.md` (research+findings) + `<deliverable>.md` (final output)。

Manus 原则:
- Filesystem as memory (不靠 context)
- Attention manipulation (re-read plan before decision)
- Error persistence (记失败到 plan file)
- Goal tracking (checkbox)
- Append-only context

**本任务不借鉴** — Trellis 系统已承担此责, 重复造轮。

## 7. Automation Best Practices (docs/automation-best-practices.md)

- Start small expand gradually (L1 单任务 → L2 任务链 → L3 复杂工作流 → L4 自我进化)
- Modularization (workflow 拆独立可重用模块)
- Trigger types: Event-based / State-based / Time-based / Manual
- Hook types: before / after / on_error / on_progress
- 状态文件 (state.json) 持久化
- 反模式: 过度自动化 / 无限循环 / 隐藏触发 / 紧密耦合 / 缺回滚

**本任务部分借鉴** — R3 evolution 抽取属 Level 4 (自我进化), 但走 proposal 而非自动 patch, 避免反模式 (隐藏触发 + 缺回滚)。

## 8. Session Logger

agent-playbook auto-trigger 落 session log 文件。

**完全对齐 cortex** — Stop hook 已落 `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/*.jsonl`, 无需改。

## 借鉴决策矩阵

| 方法论 | 借鉴 | 任务编号 |
|---|---|---|
| Context Layering (L3 references/) | ✅ | R1 + R2 |
| Self-Improving (semantic memory + 反写) | ✅ (融入 digest) | R3 |
| Long-Task Coordinator (state file) | ❌ | 用户明确不动 |
| Workflow Orchestrator (声明式 hook) | ❌ | 用户明确不动 |
| Skill Router | ❌ | 价值边际 |
| Planning with Files | ❌ | Trellis 已覆盖 |
| Automation Best Practices | 部分 (避反模式) | R3 走 proposal 而非自动 patch |
| Session Logger | 已对齐 | 无需改 |

## 关键差异点 (cortex vs agent-playbook)

| 维度 | agent-playbook | cortex |
|---|---|---|
| memory 格式 | JSON | markdown (vault 约定) |
| pattern 反写 | 自动 patch skill | proposal + 用户确认 |
| hook 系统 | 声明式 frontmatter (metadata.hooks) | 命令式 bash hook + cron |
| 长任务 state | state file (md) | Trellis (外接) |
| skill 数量 | ~22 | 21 cortex skill |
