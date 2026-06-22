---
name: trellisx-apply
description: 把 强推task + subtask拆分 + worktree隔离 + 闭环收尾 四维度注入当前项目 .trellis/ (workflow.md 的 no_task/planning/in_progress 块 + spec 背书文档 + trellis 生命周期 hook: after_start 自动建 worktree + after_finish 自动收尾)。强推 task 为 prompt 软约束; worktree + 收尾为 hook 确定性强制 (task.py start 自动建 worktree, task.py finish 经 after_finish hook 自动 commit→merge→archive→销 worktree, 不靠 AI 记得跑脚本)。**结果导向: 不约束注入方式 (可替换/重构/追加原生文本), 只约束最终结果通过行为闭环验证** (五维生效 + create→…→finish 闭环 + trellis 原生 task 创建触发仍生效)。幂等 (marker 包裹)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 **强推 task + subtask 拆分 + worktree 隔离 + 闭环收尾 + task.md 看板** 五维增量注入 `.trellis/`。跑完后由 trellis 原生 `inject-workflow-state` hook 每轮注入。

**执行模型 = main 编排 + agent 全执行**: main **不执行任何 repo 操作** (不 Read/Edit/Write/Bash/git 改盘), 把诊断/规划/备份/写盘/验证/回滚**全派 subagent** (规划 5 并行 → prep-backup 串行 → 写盘 5 并行 → 验证 5 并行 → 失败 rollback 串行); main 只做**两类不可派的事**: `AskUserQuestion` 审批门 (用户交互, 非 repo 操作) + 编排决策 (汇总/派发/修复循环)。**git stash 备份/回滚也派 agent** (顺序敏感 = 单 agent 串行跑, 非 main 亲做)。详见 `references/agent-orchestration.md`。

**两条铁律 (贯穿全程)**:
- 🎯 **结果导向, 行为闭环为准 (约束 RESULT 非 HOW)**: **不限制注入方式** —— writer 可替换 / 重构 / 追加任意原生文本 (含 no_task 分类、Phase 流程、finish 段)。唯一硬门是 Phase C **行为闭环验证**: 最终 `.trellis` MUST 满足 ① 五维生效 (强推task/subtask/worktree/闭环收尾/看板) ② create→planning→worktree→execute→check→finish 闭环无断点 ③ **trellis 原生 task 创建触发仍生效** (改写 no_task 不得让"建 task"路径失效)。注入仍用 marker 包裹保幂等; 任一断言 ✗ → 回滚重做, 不带病写盘。详见下方「教训」。
- 🪶 **强推 task 软约束, worktree+收尾 hook 确定性强制**: 强推 task 仍是注入 workflow.md 的**强措辞 prompt** (AI 仍有裁量)。**但 worktree 与闭环收尾已升级为 trellis 原生生命周期 hook 确定性强制**: `task.py start` → `after_start` 自动建 worktree; `task.py finish` → `after_finish` 自动跑 `trellisx-finish.py` (commit→merge→archive→销 worktree)。AI 只需跑 `task.py finish`, 收尾机械步骤由 hook 兜底, 不靠 AI 记得跑脚本。源码"写在 worktree 内"仍是软约束 (硬规 #1, 未上 PreToolUse 拦截); 需更硬的 PreToolUse/Stop 平台拦截 → 使用者另加, apply 不做。

> 强推 task = "除极简任务外一律走 task; 不确定主动问用户" (注入 no_task 块)。
> 自动收尾 = "check 通过后 AI 跑 `task.py finish` → `after_finish` hook **自动** commit→merge --no-ff→archive→销 worktree, 不停在'提醒用户运行命令'; 合并与 worktree 删除是必须的; commit 为 owner 授权的强制动作; 合并冲突则脚本 abort + finish 打 WARN, AI 须检告警转手动" (注入 config.yaml after_finish hook + in_progress 硬规 #4 + finish 段改写)。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| main 只编排不操作 | main **不执行任何 repo 操作** (不 Read/Edit/Write/Bash/git 改盘), 一律派 subagent 执行 (含 git stash 备份/回滚, 派单个 agent 串行跑); main 仅做 ① `AskUserQuestion` 审批门 (用户交互, 不可派) ② 编排决策 (汇总/派发/修复循环)。**唯一不派的是审批门, 因 agent 不得问用户; 它不是 repo 操作** |
| 结果导向, 可重构原生 | apply 为达预期**可替换/重构 trellis 原生 workflow 文本** (no_task/Phase/finish 段), 验收以行为闭环为准。但**仍不主动重写用户自定义 spec 文档** —— spec 的破坏式重构是 `trellisx-spec` 的职责 (不同 skill 分工, 与本铁律无关) |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经 AskUserQuestion 批准才写盘 |
| 清理无效内容 | 移除对当前平台无价值的冗余: ① 模板内部维护者注释 (`<!-- ... -->`); ② **删除所有非 Claude Code agent/平台描述** (Codex/Cursor/Gemini/OpenCode/Kiro 等专属调度段、平台枚举、inline 块整删, 不是"收敛保留")。**保留** trellisx marker + workflow-state 标签 + task.py/Phase 等 trellis 通用机制名 |
| i18n: 全产物统一目标语言 | **目标语言由 `plan-diagnose` 定一次** (综合 `$LANG` locale + 项目 CLAUDE.md/README 主语言 + 会话语言), 传给所有 writer。完成后**全部注入产物语言一致**: ① 整个 workflow.md 叙述 ② 新增 spec 文档 ③ config.yaml 的 trellisx 注释行 ④ 所有注入 snippet 文本。**保留不译**: `[workflow-state:X]` 标签 / marker key / task.py 命令 / 路径 / 代码块 / 变量名 / 脚本源码。`verify-workflow` 断言产物语言一致 (无中英混杂)。语言转换是 i18n, 不算语义重构 |

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
| **A 并行规划** | 5 read-only agent | ✅ 同批 | 各自诊断本维度 + 算最终注入文本/diff (**目标语言**), **不写盘**: `plan-diagnose` (现状+模式+**定目标语言**) · `plan-workflow` (workflow.md marker + i18n 翻译 + **删非 Claude Code 平台描述**) · `plan-spec` · `plan-hook` (config hooks+session_auto_commit+五脚本+gitignore+**packages discover**) · `plan-agent` (background:true) · `plan-finishcmd` (目标 finish-work.md 全链注入计划) | `diagnose.md` · `workflow-injection.md` · `spec-injection.md` · `hook-injection.md` · `agent-injection.md` |
| **Gate 审批** | 🔴 **main 仅审批** + prep-backup agent | ❌ | main 汇总 plan → 展示统一 diff plan (含 packages 清单) → `AskUserQuestion` 审批 (STOP) → 批准后派 **prep-backup agent** 串行 `git stash` 备份 (main 不亲做 git) | `apply-verify.md` §审批门 |
| **B 并行写盘** | 5 writer agent | ✅ 同批 | 按 plan 执行, 每 agent **独占不相交文件集** (无冲突): `write-workflow` (workflow.md) · `write-spec` (spec) · `write-hook` (scripts/*.py + config.yaml + gitignore) · `write-agent` (agents/trellis*.md) · `write-finishcmd` (.claude/commands/trellis/finish-work.md 全链注入) | `apply-verify.md` §写盘 |
| **C 并行验证** | 5 verify agent | ✅ 同批 | 各验本维度 + 闭环 + **i18n 语言一致**: `verify-workflow` (行为闭环/task创建/Phase/**语言一致**) · `verify-hook` (脚本/config hooks/after_finish/session_auto_commit/packages) · `verify-spec` · `verify-agent` · `verify-finishcmd` (finish-work 含全链)。任一 ✗ → main 派对应 writer 重注 (修复循环) | `apply-verify.md` §验证 |

> 🔴 **CHECKPOINT · 🛑 STOP (Gate)**: 改 `.trellis/` 前 **MUST 由 main 展示 diff plan + 经 AskUserQuestion 批准**才进 Phase B。审批门**禁派 agent** (全局硬规: agent 不得直接问用户); 禁纯文本"是否同意"代替工具; 用户未明确批准 → 0 写入, 终止。
> 🔒 **git stash 备份/回滚由 prep-backup/rollback agent 串行执行** (审批后、写盘前; main 不亲碰 git); 任一 writer/verify 失败 → main 派 rollback agent `git stash pop` 回滚。顺序敏感 = 单 agent 串行, 不等于 main 亲做。

## 注入维度 (注入方式不限, 行为闭环达标即可)

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **强推 task** | "除极简外默认建 task + 边界模糊 MUST 问用户" (软约束); 可改写原生 no_task 措辞, 但**须保留"建 task"创建路径** (行为闭环断言③) | workflow.md `[workflow-state:no_task]` 块 |
| **subtask 拆分 + 实施派发** | 按 trellis 原生 parent/child 语义 (多个独立可验收交付才拆 child, 不看数量); 多交付 → parent+child+各 worktree+并行调度图, 单交付 → 轻量 inline。**实施统一经 `trellis-implement` 入口**: main 派 trellis-implement, 由其对各 subtask 派专用 subagent (isolation:worktree, 无依赖并行) → trellis-check → finish; main 不直接派 subtask agent / 不直接写源码 | workflow.md `[workflow-state:planning]` + `[workflow-state:in_progress]` 硬规 #2/#3 |
| **生命周期闭环 (planning→implement→check→finish)** | 注入 workflow.md 把四阶段串成强制环: **planning** 写 prd/design/implement (trellisx-orchestrate) → **执行**派 `trellis-implement` agent (无依赖 subtask 真并行) → **检查**派 `trellis-check` agent → **完成**跑收尾 (见下行)。每阶段衔接无断点 = 行为闭环断言② | workflow.md `[workflow-state:planning]` + `[workflow-state:in_progress]` 硬规 #2/#3/#4 |
| **worktree 隔离 + 自动收尾 (双路)** | worktree: `task.py start` → after_start hook **自动建** `.worktrees/<worktree>`, after_archive 销毁; 收尾**两路都做全链** (commit→merge --no-ff→del worktree→finish→归档): ① **hook 路** `task.py finish` → after_finish hook 跑 `trellisx-finish.py`; ② **finish-work 路** apply 注入目标 `/trellis:finish-work` 令其先跑全链再 journal (见 finish-work 维度)。合并与 worktree 删除必须; 冲突 abort+WARN (AI 须检); 未 archive 禁宣告 Done | workflow.md 硬规 #4 + **finish 段改写** + config.yaml **after_finish** hook + finish-work.md 注入 + `trellisx-finish.py` |
| **finish-work 全链注入** (Option B) | apply 往**目标项目** `.claude/commands/trellis/finish-work.md` 注入 (marker 幂等): 收尾**先跑 `trellisx-finish.py` 全链** (commit+merge+del worktree+archive) **再** 原生 journal。修原生缺陷 —— 原生 finish-work 跑 `task.py archive` 直接归档**绕过 merge → 丢 worktree 提交**。注入后 finish-work 自己就做全链, 与 hook 路殊途同归 | .claude/commands/trellis/finish-work.md (目标项目, 经 write-finishcmd) |
| **中途修正路由** | 执行中收到用户新指令: 属当前任务 → 先改 PRD/design/implement 真值文档 → `SendMessage` 通知在跑 agent/member 就地纠偏 (禁 main 自己改源码/禁口头通知); 独立新任务 → 走强推 task; 判不准 → AskUserQuestion (软约束) | workflow.md `[workflow-state:in_progress]` 块末尾 (硬规 #7) |
| **task.md 看板** | hook (`trellisx-taskmd.py`) 维护确定性列 (id/名称/描述/状态) + create/start/archive upsert + 7 天清理; AI (`trellisx-workspace`) 补主观列 (阶段/进度/worktree); 含独立 **worktree↔task 映射区** (一对多, `map-add/map-remove/map-get/map-list` 维护, WorktreeCreate hook 按当前活动 task 自动登记) + `lint` 子命令 (列数/状态/ID 重复校验, FileChanged hook 触发) | .trellis/scripts/ + config.yaml hooks + workflow.md marker |
| **packages 注册表** | monorepo 包自动发现 (apply 一次扫描, 非 hook): 4 信号 (submodule/嵌套.git/workspace 清单/约定目录, 后两者须含 manifest) → 写 config.yaml `packages:`; **仅单仓才自动写, 已配置只报告不覆盖**; 驱动 spec scoping + 可见性 | .trellis/config.yaml + `trellisx-packages.py` |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建) | .trellis/spec/guides/ |
| (副作用) 生命周期 hook | config.yaml `hooks.after_start/after_archive` 触发 `trellisx-worktree.py` 建/销 + `hooks.after_finish` 触发 `trellisx-finish.py` 自动收尾 + **`session_auto_commit: true`** (archive 自动提交闭环依赖, 均不改 task.py) | .trellis/config.yaml + .trellis/scripts/ |
| **agent 后台化** | 所有 `trellis*` agent frontmatter 加 `background: true` (缺则加 / 非 true 强制改); 只动 background 一字段 | .claude/agents/trellis*.md |

> 🔒 **教训 (行为闭环为准的来由)**: 早期 apply **重写** no_task + Phase 流程, 破坏了 trellis 原生 task 创建触发 —— 真正的坑是**功能失效** (建 task 路径断了), 不是"动了原生文本"本身。所以约束 RESULT 而非 HOW: **允许重构** no_task/Phase/finish, 但 Phase C MUST 行为验证 ① 五维生效 ② create→…→finish 闭环 ③ task 创建触发仍生效。任一 ✗ 即回滚。改写 no_task 措辞 OK, 改没了"建 task"路径 → ✗。

## 反例黑名单 (禁做)

每条都是真实踩过的坑。每次 apply 写盘前对照一次, 命中即改方案。

| 禁 | 为什么 | 替代 |
| --- | --- | --- |
| 改写 no_task/Phase 后**未跑行为闭环验证**就写盘 | 重构可能切断 task 创建触发, 不验证 = 带病交付 (早期翻车根因) | 改可改, 但 Phase C MUST 行为验证 (task 创建触发 + create→…→finish 闭环); ✗ 即回滚。不再禁替换, 改禁"改完不验证" |
| 改写 no_task 把"建 task"创建路径删没了 | 行为闭环断言③ 失败: AI 不再触发建 task, 强推 task 维度失效 | 改措辞/重构结构 OK, 但产物 MUST 仍引导建 task (verify-workflow 行为断言) |
| 跳过 step5 AskUserQuestion 直接写盘 | 绕过审批门 = 用户未批就改 .trellis | MUST 先展示 diff plan + 工具审批; 未批 0 写入。禁纯文本"是否同意"代替工具 |
| 漏拷 `trellisx_wt.py` 公共模块 | `trellisx-worktree.py` / `trellisx-finish.py` 都 import 它, 漏拷 → ImportError, worktree/finish 全哑 | hook-injection **四文件一起拷** (wt 公共模块 + worktree + taskmd + finish), 缺一不可 |
| finish 段定位用 `re.search` 取**首个**含 finish-work 的段 | 提交段 (Phase 3.4) 正文常提及 `/finish-work`, 排在收尾段前 → 误命中改坏提交段, 收尾段没改 | 用 `re.finditer` 取**末个** (收尾段在 Phase 3 末尾), 见注入点 4 |
| 重复跑时堆叠 marker (追加新块) | 同 marker 多份 = 注入内容翻倍混乱 | marker 包裹**幂等替换块内**, 不堆叠; 脚本覆盖更新 |
| 主动重写用户**自定义 spec** 文档 | spec 破坏式重构是 `trellisx-spec` 的职责 (不同 skill 分工); apply 不碰用户 spec | apply 只新增 worktree spec (不存在才建); 用户 spec 的重构走 `trellisx-spec`。注: trellis 原生 workflow.md 可重构, 用户自定义 spec 不碰 |
| 保留跨平台枚举 / 维护者注释 | 噪音, 其他 runtime 误判 | 收敛为 Claude Code (Phase A plan-workflow); 但**保留** trellisx marker + workflow-state 标签 + 命令 + 路径 + 代码块 |
| main 自己 Read/Edit/Write 做诊断/规划/写盘 | 违执行模型 (main 只编排), 丢并行 | 一律派 subagent 并发; main 只汇总 + 守审批门 + 管 git 备份 |
| 把审批门 / git stash 派给 agent | agent 禁直接问用户 (审批失效); 并发 git stash 撕裂 index | 审批门 + git 备份/回滚 **MUST main 串行**, 不可委派 |
| 多 writer agent 文件集重叠 (如都碰 config.yaml) | 并发写同文件 → 互相覆盖/丢改动 | Phase B 严格 disjoint 分区: workflow / spec / (scripts+config+gitignore) / agents 各一独占 owner |
| Phase A plan agent 写盘 | 规划阶段越权写, 绕过审批门 | plan agent **read-only**, 只返回 diff/plan 文本; 写盘只在 Phase B 批准后 |
| packages 发现覆盖用户已配置的 `packages:` | 冲掉用户精心配的 monorepo 注册 | **仅单仓 (无实值 packages:) 才自动写**; 已配置 → 只报告发现供人工核对, 不覆盖 |
| packages 把空目录/非项目目录注册进表 | 污染注册表 → spec scoping 误判 | 信号 3/4 (workspace/约定目录) **须含 manifest** (package.json/go.mod/Cargo.toml/pyproject.toml) 才注册; 审批门展示发现清单拦误报 |

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 无 `.trellis/` (前置检查失败) | 提示用户先 `trellis init` | 非 trellis 项目 → 终止, 0 注入 |
| 已存在 trellisx marker (重复跑) | 幂等: 只更新 marker 内, 不堆叠 (`references/diagnose.md`) | marker 损坏/嵌套错乱 → 报告冲突位置, 请用户确认覆盖再写 |
| 缺 `config.yaml` / `.claude/agents/trellis*.md` | 跳过对应步骤 (4/4.5), 其余维度照注 | 全部目标缺失 → 仅注 workflow.md, 报告未注入维度 |
| 用户在步骤5 AskUserQuestion 驳回 | 立即停, 0 写盘, 返回"用户驳回" | — (审批门硬规, 不绕过) |
| 某 writer agent 写盘失败 | main 派 rollback agent `git stash pop` 回滚, 重派该 writer | 重派仍失败 → 报告脏文件清单, 请用户手工核对 |
| 某 plan/verify agent 死亡或返空 | main 重派该 agent (其余 agent 结果保留, 无需全重跑) | 重派仍失败 → 该维度降级 main 串行兜底执行, 记日志 |
| verify agent 报 ✗ (marker 串位/缺环节) | main 派对应 writer 按算法重注 → 重验 (修复循环) | 循环 3 次仍 ✗ → 回滚, 报「未闭环: <缺失环节>」 |
| workflow 原文英文而设备中文 | i18n: plan-workflow 翻译全文叙述, 保留标签/marker/命令/路径 | 语言判不准 → 综合 `$LANG`+CLAUDE.md+会话语言, 仍不准则保持原文不译 |

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/agent-orchestration.md` | **编排核心**: 4 阶段 6+5+5 agent 清单 + 并发分组 + disjoint 文件集分区 + 6 字段 prompt 模板 + main 只编排不操作 |
| `references/diagnose.md` | Phase A plan-diagnose: 现状诊断 + marker 检测 + 定目标语言 |
| `references/finishcmd-injection.md` | Phase A plan-finishcmd / B write-finishcmd: 目标 finish-work.md 全链注入 (Option B) |
| `references/workflow-injection.md` | Phase A plan-workflow / B write-workflow: workflow-state 块 + Phase 注入 (核心) |
| `references/spec-injection.md` | Phase A plan-spec / B write-spec: spec 规范文档 |
| `references/hook-injection.md` | Phase A plan-hook / B write-hook: trellis 生命周期 hook (config.yaml) worktree 自动化 |
| `references/agent-injection.md` | Phase A plan-agent / B write-agent: trellis agent `background: true` 注入 |
| `references/apply-verify.md` | Gate 审批 + Phase B 写盘 + Phase C 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask
- `trellisx-spec` — spec 破坏式优化
- `trellisx-workspace` — 维护 `.trellis/task.md` 任务看板
