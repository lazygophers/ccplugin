---
name: trellisx-apply
description: 把 强推task + subtask拆分 + worktree隔离 + 闭环收尾 四维度增量注入当前项目 .trellis/ (workflow.md 的 no_task/planning/in_progress 块 + spec 背书文档 + trellis 生命周期 hook worktree 自动化 + trellisx-finish.py 强制收尾)。强推 task 为 prompt 软约束; 闭环为脚本化强制 (check 通过 AI 必跑 trellisx-finish.py: 提交→合并→archive→销 worktree)。**纯增量追加, 绝不替换 trellis 原生文本** (唯一例外: finish 收尾段经授权改写; no_task 分类+征同意/check/前缀全保留)。幂等 (marker 包裹)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 **强推 task + subtask 拆分 + worktree 隔离 + 闭环收尾 + task.md 看板** 五维增量注入 `.trellis/`。跑完后由 trellis 原生 `inject-workflow-state` hook 每轮注入。

**执行模型 = main 编排 + agent 并行**: main **不直接操作变更**, 而是把诊断/规划/写盘/验证派给 subagent, 同批并发 (规划 5 并行 → 写盘 4 并行 → 验证 4 并行); main 只保留**不可委派的串行节点**: `AskUserQuestion` 审批门 + `git stash` 备份/回滚 + 各阶段结果汇总。详见 `references/agent-orchestration.md`。

**两条铁律 (贯穿全程)**:
- 🔒 **纯增量追加, 绝不替换原生 (唯一例外: finish 段)**: no_task 原生分类+征同意 / Phase 流程 / check / 完成判定 / 回复前缀 —— **一字不改**, trellisx 内容只在块末尾追加 (`apply-verify` 强制断言原生正文非空)。**例外**: Phase 3 **收尾提醒段** (含 `/finish-work` 提醒) 经用户授权**可改写**为强制收尾 (见 `workflow-injection.md` 注入点 4); 此例外仅限 finish 段, 其余原生一律不动。详见下方「教训」。
- 🪶 **软约束为主, finish 强制为辅**: 强推 task 仍是注入 workflow.md 的**强措辞 prompt** (AI 仍有裁量), 非 PreToolUse/Stop 平台拦截。**但闭环收尾已升级为脚本化强制**: 注入 `trellisx-finish.py` + 改写 finish 段, check 通过后 AI **必须**跑脚本完成 commit→合并→archive→销 worktree (finish/worktree 删除非可选)。需更硬的 Stop hook 兜底 → 使用者另加, apply 不做。

> 强推 task = "除极简任务外一律走 task; 不确定主动问用户" (注入 no_task 块)。
> 闭环收尾 = "check 通过后 AI **强制跑** `trellisx-finish.py` (worktree 提交→合并回主分支→archive→销 worktree), 不停在'提醒用户运行命令'; finish/worktree 删除是必须的; commit 为 owner 授权的强制动作; 合并冲突则脚本 abort 转手动" (注入 in_progress 块硬规 #4 + finish 段改写)。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| main 只编排不操作 | main **不直接** Read/Edit/Write/跑诊断脚本去变更, 一律派 subagent 并发执行; main 仅汇总结果 + 守审批门 + 管 git 备份/回滚。例外: 审批门 (`AskUserQuestion` 禁派 agent) 与 git stash (共享 index, 顺序敏感) 必须 main 串行做 |
| 增量增强, 不重构 | apply 只**增量增强** (marker 注入 + 加新文件 + 加新 hook); **绝不重写**用户原有 workflow / spec / 文档。spec 的破坏式重构是 `trellisx-spec` 的职责 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经 AskUserQuestion 批准才写盘 |
| 清理无效内容 | 移除对当前平台无价值的冗余: ① 模板内部维护者注释 (`<!-- ... -->`); ② 跨平台枚举 (`[Claude Code, Cursor, OpenCode, Kiro, ...]`) 收敛为 Claude Code。**保留** trellisx marker + workflow-state 标签 |
| i18n: 全文档跟随设备语言 | 完成后**整个 workflow.md + 新增 spec 叙述**与设备语言一致 (不只注入部分)。原生英文+设备中文 → 翻译全文叙述。**保留不译**: `[workflow-state:X]` 标签 / marker key / task.py 命令 / 路径 / 代码块 / 变量名。语言转换是 i18n, 不算语义重构 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/workflow.md          # 注入目标
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .trellis/config.yaml          # trellis 生命周期 hook 注入目标
ls .claude/agents/trellis*.md 2>/dev/null   # trellis agent background:true 注入目标
echo "${LANG:-}"                  # 系统 locale (如 en_US / zh_CN), 决定注入文本语言
head -5 CLAUDE.md AGENTS.md 2>/dev/null   # 项目主语言佐证
```

**目标语言** = 综合 `$LANG` locale + 项目 CLAUDE.md/README 主语言 + 当前会话语言。非 trellis 项目 → 报错终止。

## 工作流 (4 阶段并行流水线)

main 编排, 各阶段内 agent **同批并发派发** (一条消息多 Agent 调用); 阶段间串行 (后阶段依赖前阶段结果)。完整 agent 清单/6 字段 prompt 模板/文件集分区见 `references/agent-orchestration.md`。

| 阶段 | 谁做 | 并发 | 行动 | 详细内容 |
| --- | --- | --- | --- | --- |
| **A 并行规划** | 5 read-only agent | ✅ 同批 | 各自诊断本维度 + 算最终注入文本/diff, **不写盘**: `plan-diagnose` (现状+模式+目标语言) · `plan-workflow` (workflow.md marker + i18n 翻译 + 清理) · `plan-spec` · `plan-hook` (config+四脚本+gitignore) · `plan-agent` (background:true 清单) | `diagnose.md` · `workflow-injection.md` · `spec-injection.md` · `hook-injection.md` · `agent-injection.md` |
| **Gate 审批** | 🔴 **main 串行** | ❌ | 汇总 5 plan → 展示统一 diff plan → `AskUserQuestion` 审批 (STOP) → 批准后 `git stash` 备份 | `apply-verify.md` §审批门 |
| **B 并行写盘** | 4 writer agent | ✅ 同批 | 按 plan 执行, 每 agent **独占不相交文件集** (无冲突): `write-workflow` (workflow.md) · `write-spec` (spec) · `write-hook` (scripts/*.py + config.yaml + gitignore) · `write-agent` (agents/trellis*.md) | `apply-verify.md` §写盘 |
| **C 并行验证** | 4 verify agent | ✅ 同批 | 各验本维度产物 + 闭环: `verify-workflow` (marker/块内/原生非空/Phase) · `verify-hook` (脚本语法/import/config/finish段) · `verify-spec` · `verify-agent`。任一 ✗ → main 派对应 writer 重注 → 重验 (修复循环) | `apply-verify.md` §验证 |

> 🔴 **CHECKPOINT · 🛑 STOP (Gate)**: 改 `.trellis/` 前 **MUST 由 main 展示 diff plan + 经 AskUserQuestion 批准**才进 Phase B。审批门**禁派 agent** (全局硬规: agent 不得直接问用户); 禁纯文本"是否同意"代替工具; 用户未明确批准 → 0 写入, 终止。
> 🔒 **写盘前 main 串行 `git stash` 备份** (共享 git index, 顺序敏感, 禁派 agent 并发做); 任一 writer/verify 失败 → main 串行 `git stash pop` 回滚。

## 注入维度 (一律末尾追加, 不动原生)

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **强推 task** | "除极简外默认建 task + 边界模糊 MUST 问用户" (软约束) | workflow.md `[workflow-state:no_task]` 块末尾 |
| **subtask 拆分 + 实施派发** | 按 trellis 原生 parent/child 语义 (多个独立可验收交付才拆 child, 不看数量); 多交付 → parent+child+各 worktree+并行调度图, 单交付 → 轻量 inline。**实施统一经 `trellis-implement` 入口**: main 派 trellis-implement, 由其对各 subtask 派专用 subagent (isolation:worktree, 无依赖并行) → trellis-check → finish; main 不直接派 subtask agent / 不直接写源码 | workflow.md `[workflow-state:planning]` + `[workflow-state:in_progress]` 硬规 #2/#3 |
| **worktree 隔离 + 强制闭环** | worktree: start 自动建 `<git根>/.worktrees/<worktree>`, 源码改动隔离, archive 销毁; 闭环: check 通过后 AI **强制跑** `trellisx-finish.py` (worktree 提交→合并回主分支→archive→销 worktree), 不降级为"提醒用户"; finish/worktree 删除为必须, commit owner 授权强制; 合并冲突脚本 abort 转手动; 未 archive 禁宣告 Done | workflow.md `[workflow-state:in_progress]` 硬规 #4 + **finish 段改写** + config.yaml hook + `trellisx-finish.py` |
| **中途修正路由** | 执行中收到用户新指令: 属当前任务 → 先改 PRD/design/implement 真值文档 → `SendMessage` 通知在跑 agent/member 就地纠偏 (禁 main 自己改源码/禁口头通知); 独立新任务 → 走强推 task; 判不准 → AskUserQuestion (软约束) | workflow.md `[workflow-state:in_progress]` 块末尾 (硬规 #7) |
| **task.md 看板** | hook (`trellisx-taskmd.py`) 维护确定性列 (id/名称/描述/状态) + create/start/archive upsert + 7 天清理; AI (`trellisx-workspace`) 补主观列 (阶段/进度/worktree) | .trellis/scripts/ + config.yaml hooks + workflow.md marker |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建) | .trellis/spec/guides/ |
| (副作用) worktree hook | config.yaml `hooks.after_start/after_archive` 触发 `trellisx-worktree.py` 建/销 (不改 task.py) | .trellis/config.yaml + .trellis/scripts/ |
| **agent 后台化** | 所有 `trellis*` agent frontmatter 加 `background: true` (缺则加 / 非 true 强制改); 只动 background 一字段 | .claude/agents/trellis*.md |

> 🔒 **教训 (两条铁律之一的来由)**: 早期 apply **重写** no_task + Phase 流程, 破坏了 trellis 原生 task 创建触发。**根因是替换原生文本, 非追加本身。** 修正: no_task 可末尾追加强推 task 规约, 但 MUST 保留原生「First classify... / task-creation consent」+ Phase 流程 + 完成判定 + 回复前缀, 一字不改 (apply-verify 强制断言)。

## 反例黑名单 (禁做)

每条都是真实踩过的坑。每次 apply 写盘前对照一次, 命中即改方案。

| 禁 | 为什么 | 替代 |
| --- | --- | --- |
| 替换原生文本 (no_task 分类/Phase 流程/check/完成判定/回复前缀) | 破坏 trellis 原生 task 创建触发 (早期 apply 翻车根因) | 只在块末尾**追加** trellisx 内容; 原生一字不改 (apply-verify 强制断言)。唯一例外: finish 收尾段经授权改写 |
| 跳过 step5 AskUserQuestion 直接写盘 | 绕过审批门 = 用户未批就改 .trellis | MUST 先展示 diff plan + 工具审批; 未批 0 写入。禁纯文本"是否同意"代替工具 |
| 漏拷 `trellisx_wt.py` 公共模块 | `trellisx-worktree.py` / `trellisx-finish.py` 都 import 它, 漏拷 → ImportError, worktree/finish 全哑 | hook-injection **四文件一起拷** (wt 公共模块 + worktree + taskmd + finish), 缺一不可 |
| finish 段定位用 `re.search` 取**首个**含 finish-work 的段 | 提交段 (Phase 3.4) 正文常提及 `/finish-work`, 排在收尾段前 → 误命中改坏提交段, 收尾段没改 | 用 `re.finditer` 取**末个** (收尾段在 Phase 3 末尾), 见注入点 4 |
| 重复跑时堆叠 marker (追加新块) | 同 marker 多份 = 注入内容翻倍混乱 | marker 包裹**幂等替换块内**, 不堆叠; 脚本覆盖更新 |
| 重写用户原有 spec / workflow / 文档 | apply 是增量增强, 不是重构 | 只 marker 注入 + 加新文件 + 加 hook; 破坏式 spec 重构走 `trellisx-spec` |
| 保留跨平台枚举 / 维护者注释 | 噪音, 其他 runtime 误判 | 收敛为 Claude Code (Phase A plan-workflow); 但**保留** trellisx marker + workflow-state 标签 + 命令 + 路径 + 代码块 |
| main 自己 Read/Edit/Write 做诊断/规划/写盘 | 违执行模型 (main 只编排), 丢并行 | 一律派 subagent 并发; main 只汇总 + 守审批门 + 管 git 备份 |
| 把审批门 / git stash 派给 agent | agent 禁直接问用户 (审批失效); 并发 git stash 撕裂 index | 审批门 + git 备份/回滚 **MUST main 串行**, 不可委派 |
| 多 writer agent 文件集重叠 (如都碰 config.yaml) | 并发写同文件 → 互相覆盖/丢改动 | Phase B 严格 disjoint 分区: workflow / spec / (scripts+config+gitignore) / agents 各一独占 owner |
| Phase A plan agent 写盘 | 规划阶段越权写, 绕过审批门 | plan agent **read-only**, 只返回 diff/plan 文本; 写盘只在 Phase B 批准后 |

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 无 `.trellis/` (前置检查失败) | 提示用户先 `trellis init` | 非 trellis 项目 → 终止, 0 注入 |
| 已存在 trellisx marker (重复跑) | 幂等: 只更新 marker 内, 不堆叠 (`references/diagnose.md`) | marker 损坏/嵌套错乱 → 报告冲突位置, 请用户确认覆盖再写 |
| 缺 `config.yaml` / `.claude/agents/trellis*.md` | 跳过对应步骤 (4/4.5), 其余维度照注 | 全部目标缺失 → 仅注 workflow.md, 报告未注入维度 |
| 用户在步骤5 AskUserQuestion 驳回 | 立即停, 0 写盘, 返回"用户驳回" | — (审批门硬规, 不绕过) |
| 某 writer agent 写盘失败 | main 串行 `git stash pop` 回滚, 重派该 writer | 重派仍失败 → 报告脏文件清单, 请用户手工核对 |
| 某 plan/verify agent 死亡或返空 | main 重派该 agent (其余 agent 结果保留, 无需全重跑) | 重派仍失败 → 该维度降级 main 串行兜底执行, 记日志 |
| verify agent 报 ✗ (marker 串位/缺环节) | main 派对应 writer 按算法重注 → 重验 (修复循环) | 循环 3 次仍 ✗ → 回滚, 报「未闭环: <缺失环节>」 |
| workflow 原文英文而设备中文 | i18n: plan-workflow 翻译全文叙述, 保留标签/marker/命令/路径 | 语言判不准 → 综合 `$LANG`+CLAUDE.md+会话语言, 仍不准则保持原文不译 |

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/agent-orchestration.md` | **编排核心**: 4 阶段 agent 清单 + 并发分组 + disjoint 文件集分区 + 6 字段 prompt 模板 + 串行节点 |
| `references/diagnose.md` | Phase A plan-diagnose: 现状诊断 + marker 检测 |
| `references/workflow-injection.md` | Phase A plan-workflow / B write-workflow: workflow-state 块 + Phase 注入 (核心) |
| `references/spec-injection.md` | Phase A plan-spec / B write-spec: spec 规范文档 |
| `references/hook-injection.md` | Phase A plan-hook / B write-hook: trellis 生命周期 hook (config.yaml) worktree 自动化 |
| `references/agent-injection.md` | Phase A plan-agent / B write-agent: trellis agent `background: true` 注入 |
| `references/apply-verify.md` | Gate 审批 + Phase B 写盘 + Phase C 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask
- `trellisx-spec` — spec 破坏式优化
- `trellisx-workspace` — 维护 `.trellis/task.md` 任务看板
