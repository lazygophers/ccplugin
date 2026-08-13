---
name: trellisx-apply
description: '🛠️ 把 worktree隔离 + 闭环收尾 + task.md看板 三维注入当前项目 .trellis/。全部为 trellis 生命周期 hook 确定性强制 (after_start 建 worktree, after_finish 自动 commit→merge→archive→销 worktree, taskmd hook 维护看板), 不靠 AI 跑脚本。结果导向: 只约束最终行为闭环 (worktree 建/销 + create→…→finish 收尾链完整), 不约束注入方式。幂等 (marker 包裹)'

disable-model-invocation: true
argument-hint: '[scope]'
arguments: '[范围 (目录 glob / 文件路径 / all), 缺省 = all]'
---

# trellisx-apply — 把 trellisx worktree/收尾/看板机制内化进 .trellis

把 **worktree 隔离 + 闭环收尾 + task.md 看板** 三维增量注入 `.trellis/` (config.yaml 生命周期 hook + 独立脚本 + 可选 finish-work 命令注入)。各维度注入内容与落地位置见下方「注入维度」表。

## 铁律 (贯穿全程)

- 🎯 **结果导向, 行为闭环为准 (约束 RESULT 非 HOW)**: 不限制注入方式 —— writer 可替换/重构/追加任意脚本与配置。唯一硬门是 **writer 写盘自验的行为闭环验证**: 最终 `.trellis` MUST 满足 ① worktree 生命周期 hook 在位 (after_start 建 / after_archive 销) ② 收尾链完整 (task.py finish → commit→merge→archive→销 worktree) ③ task.md 看板 hook 在位。

  **可执行断言 (writer 自验最小集, 任一 ✗ → 回滚重做)**:
  ```bash
  # ① worktree + 收尾 hook 在位 (config.yaml 仍含 trellisx hook 注入)
  grep -q "trellisx-worktree" .trellis/config.yaml && grep -q "trellisx-finish" .trellis/config.yaml
  # ② 脚本语法合法 + 公共模块可导入
  python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-finish.py').read())"
  # ③ session_auto_commit 实值 true (archive 自动提交闭环依赖)
  python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_session_auto_commit; assert get_session_auto_commit() is True"
  ```
  完整断言集 + 行为闭环验证步骤见 `references/apply-verify.md`; writer MUST 至少跑上述 3 条自验才报告 ok=true。

  注入用 marker 包裹保幂等; 不带病写盘 (来由见下方「教训」)。
- 🪶 **worktree + 收尾 hook 确定性强制**:
  - worktree 与闭环收尾 = trellis 原生生命周期 hook 确定性强制, 不靠 AI 记得跑脚本: `task.py start` → `after_start` 自动建 worktree; `task.py finish` → `after_finish` 跑 `trellisx-finish.py` 自动 commit→merge --no-ff→archive→销 worktree (commit 为 owner 授权的强制动作, 不停在"提醒用户运行命令")。冲突则脚本 abort + finish 打 WARN, AI 须检告警转手动; 未 archive 禁宣告 Done。
  - worktree 隔离单位 = task (防并发多 task 冲突)。"task 在其 worktree 内执行"仍是软约束 (未上 PreToolUse 拦截); 需更硬的平台拦截使用者另加, apply 不做。

## 执行模型 (main 编排 + 并行 subagent 执行)

main **不执行任何 repo 操作** (不 Read/Edit/Write/Bash/git 改盘), 只做两类不可派的事: `AskUserQuestion` 审批门 (用户交互, 夹在 plan/write 两阶段之间) + 编排决策 (汇总/派发/修复循环)。

main 用 `Agent` 工具把扇出编排成两阶段 (Phase A 并行规划 read-only → main 审批 → Phase B 并行写盘+自验+回滚)。维度收敛为 3 个 (spec/hook/finishcmd) + 诊断, writer 写完自验 (无独立验证阶段)。详见 `references/agent-orchestration.md`。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身生命周期 hook 生效; 不靠 trellisx 持续 hook |
| main 只编排不操作 | 所有 repo 操作 (含 git stash 备份/回滚) 一律派 subagent; main 唯一不派的是审批门 (agent 不得问用户)。详见执行模型 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / 自动收尾 / task.md 看板)。**不改 trellis 原生生命周期规则文件本体** —— apply 只装生命周期 hook, 不往规则文件追加内容 |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经 AskUserQuestion 批准才写盘 |
| 不动用户 spec | 只**新增** worktree spec (不存在才建), 绝不重写用户自定义 spec 文档 (spec 的破坏式重构是 `trellisx-spec` 的职责) |
| 产物统一中文 | 全部注入产物用**中文**: ① 新增 spec 文档 ② config.yaml 的 trellisx 注释行 ③ finish-work 注入 snippet 文本。无语言探测。**保留不译**: marker key / task.py 命令 / 路径 / 代码块 / 变量名 / 脚本源码 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .trellis/config.yaml          # trellis 生命周期 hook 注入目标
ls .claude/commands/trellis/finish-work.md 2>/dev/null   # finish-work 全链注入目标 (无则 hook 路兜底)
```

**产物语言固定中文** (无探测)。非 trellis 项目 → 报错终止。

## 工作流 (subagent 编排, 审批夹在中间)

载体见上「执行模型」; 完整模型/6 字段 prompt/文件集分区见 `references/agent-orchestration.md`。

| 步 | 谁做 | 行动 |
| --- | --- | --- |
| **1 规划** | main 并行派 4 read-only Agent | diagnose (现状+模式) + 3 维 planner (spec/hook/finishcmd) 各算注入 diff, **不写盘**, 返回 `{plans}` |
| **2 审批** | **main 仅审批** | 汇总 plans → 展示统一 diff plan (含 packages 清单) → `AskUserQuestion` 审批 (硬停) → 批准后才进步 3 |
| **3 写盘+自验** | main 派 prep-backup + 并行 3 writer Agent | prep-backup agent `git stash` 备份 → 3 维 writer 各**独占不相交文件集**写盘+**自验本维度** (无独立验证阶段) → 任一失败 main 派 rollback agent `git stash pop` |
| **4 修复/完成** | main 编排 | `ok=false` → 据 failed 重跑 write (修复循环 ≤3) 或报告; `ok=true` → 完成报告 |

> **硬停审批门 (审批)**: 改 `.trellis/` 前 **MUST 由 main 展示 diff plan + 经 AskUserQuestion 批准**才进步 3。审批门**禁派 agent** (全局硬规: agent 不得直接问用户) —— 故 plan 与 write 拆成**两阶段**, 审批夹在中间; 禁纯文本"是否同意"代替工具; 用户未明确批准 → 0 写入, 终止。
> 🔒 **git stash 备份/回滚在 write 阶段由 prep-backup/rollback agent 串行执行** (main 不亲碰 git)。

## 注入维度 (注入方式不限, 行为闭环达标即可)

| 维度 | 注入内容 | 落地位置 |
| --- | --- | --- |
| **worktree 隔离 + 自动收尾 (双路)** | worktree: `task.py start` → after_start hook **自动建** `.worktrees/<worktree>`, after_archive 销毁; 收尾**两路都做全链** (commit→merge --no-ff→del worktree→archive): ① **hook 路** `task.py finish` → after_finish hook 跑 `trellisx-finish.py`; ② **finish-work 路** apply 注入目标 `/trellis:finish-work` 令其先跑全链再 journal (见 finish-work 维度)。合并与 worktree 删除必须; 冲突 abort+WARN (AI 须检); 未 archive 禁宣告 Done。**收尾两层**: ① **git 层** (确定性脚本 `trellisx-finish.py`): commit→merge --no-ff (子先主后)→销 worktree→archive; ② **AI 层** (脚本做不到, 必须 AI 主动): finish 前 TaskList 查本 task 名下悬挂后台 agent, 逐个 TaskStop 关。**顺序: 先 AI 层清悬挂 (⓪) → 再 git 层 finish (①)** | config.yaml **after_start/after_finish/after_archive** hook + `trellisx-worktree.py` + `trellisx-finish.py` + finish-work.md 注入 |
| **finish-work 全链注入** (Option B) | apply 往**目标项目** `.claude/commands/trellis/finish-work.md` 注入 (marker 幂等): 收尾**先跑 `trellisx-finish.py` 全链** (commit+merge+del worktree+archive) **再** 原生 journal。修原生缺陷 —— 原生 finish-work 跑 `task.py archive` 直接归档**绕过 merge → 丢 worktree 提交**。注入后 finish-work 自己就做全链, 与 hook 路殊途同归 | .claude/commands/trellis/finish-work.md (目标项目, 经 write-finishcmd) |
| **task.md 看板** | hook (`trellisx-taskmd.py`) 维护确定性列 (id/名称/描述/状态/worktree/**前置**) + create/start/archive upsert + 7 天清理; **前置列** = task.json 顶层 `depends_on` (task 级 DAG 显式前置边), 经 `trellisx-taskmd.py update <tid> --deps "a,b"` 写回 (随本脚本 cp 发货, 无需改原生 task.py), 供 **`trellisx-flow` 多 task 并行调度**据此排前后序; AI (`trellisx-workspace`) 细化状态 + worktree; 含独立 **worktree↔task 映射区** (一对多, `map-add/map-remove/map-get/map-list` 维护, WorktreeCreate hook 按当前活动 task 自动登记) + `lint` 子命令 (列数/状态/ID 重复校验, FileChanged hook 触发) | .trellis/scripts/ + config.yaml hooks |
| **packages 注册表** | monorepo 包自动发现 (apply 一次扫描, 非 hook): 4 信号 (submodule/嵌套.git/workspace 清单/约定目录, 后两者须含 manifest) → 写 config.yaml `packages:`; **仅单仓才自动写, 已配置只报告不覆盖**; 驱动 spec scoping + 可见性 | .trellis/config.yaml + `trellisx-packages.py` |
| (背书) worktree spec | **仅新增** trellisx-worktree.md (不存在才建); 内含 worktree 隔离 + subtask 拆分/异步并行约定 (main 调度器 / trellis-implement 各执行 1 subtask / 共享 task worktree) | .trellis/spec/guides/ |
| (副作用) 生命周期 hook | config.yaml `hooks.after_start/after_archive` 触发 `trellisx-worktree.py` 建/销 + `hooks.after_finish` 触发 `trellisx-finish.py` 自动收尾 + **`session_auto_commit: true`** (archive 自动提交闭环依赖, 均不改 task.py) | .trellis/config.yaml + .trellis/scripts/ |

> 🔒 **教训 (行为闭环为准的来由)**: 早期 worktree 逻辑在 `worktree.py` 与 `finish.py` **各写一份路径/命名**, 差一点就失配 —— 真正的坑是**功能失效** (合并目标算错 / 漏拷公共模块 ImportError)。所以约束 RESULT 而非 HOW: writer 自验 MUST 行为验证 ① worktree hook 在位 ② 收尾链完整 ③ 脚本语法/导入 OK。任一 ✗ 即回滚。

## 反例黑名单 (禁做)

每条都是真实踩过的坑。每次 apply 写盘前对照一次, 命中即改方案。

| 禁 | 为什么 | 替代 |
| --- | --- | --- |
| 跳过 step2 AskUserQuestion 直接写盘 | 绕过审批门 = 用户未批就改 .trellis | MUST 先展示 diff plan + 工具审批; 未批 0 写入。禁纯文本"是否同意"代替工具 |
| 漏拷 `trellisx_wt.py` 公共模块 | `trellisx-worktree.py` / `trellisx-finish.py` 都 import 它, 漏拷 → ImportError, worktree/finish 全哑 | hook-injection **多文件一起拷** (wt 公共模块 + worktree + taskmd + finish), 缺一不可 |
| finish 段定位用 `re.search` 取**首个**含 finish-work 的段 | 提交段正文常提及 `/finish-work`, 排在收尾段前 → 误命中改坏提交段 | 用 `re.finditer` 取**末个** (收尾段在末尾), 见 finishcmd-injection.md |
| 重复跑时堆叠 marker (追加新块) | 同 marker 多份 = 注入内容翻倍混乱 | marker 包裹**幂等替换块内**, 不堆叠; 脚本覆盖更新 |
| 主动重写用户**自定义 spec** 文档 | spec 破坏式重构是 `trellisx-spec` 的职责 (不同 skill 分工); apply 不碰用户 spec | apply 只新增 worktree spec (不存在才建); 用户 spec 的重构走 `trellisx-spec` |
| main 自己 Read/Edit/Write 做诊断/规划/写盘 | 违执行模型 (main 只编排), 丢并行 | 一律派 subagent 并发; main 只汇总 + 守审批门 + 管 git 备份 |
| 把审批门 / git stash 派给 agent | agent 禁直接问用户 (审批失效); 并发 git stash 撕裂 index | 审批门 + git 备份/回滚 **MUST main 串行**, 不可委派 |
| 多 writer agent 文件集重叠 (如都碰 config.yaml) | 并发写同文件 → 互相覆盖/丢改动 | Phase B 严格 disjoint 分区: spec / (scripts+config+gitignore) / finish-work 各一独占 owner |
| Phase A plan agent 写盘 | 规划阶段越权写, 绕过审批门 | plan agent **read-only**, 只返回 diff/plan 文本; 写盘只在 Phase B 批准后 |
| packages 发现覆盖用户已配置的 `packages:` | 冲掉用户精心配的 monorepo 注册 | **仅单仓 (无实值 packages:) 才自动写**; 已配置 → 只报告发现供人工核对, 不覆盖 |
| packages 把空目录/非项目目录注册进表 | 污染注册表 → spec scoping 误判 | 信号 3/4 (workspace/约定目录) **须含 manifest** (package.json/go.mod/Cargo.toml/pyproject.toml) 才注册; 审批门展示发现清单拦误报 |

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 无 `.trellis/` (前置检查失败) | 提示用户先 `trellis init` | 非 trellis 项目 → 终止, 0 注入 |
| 已存在 trellisx hook (重复跑) | 幂等: 检测 config.yaml 含 trellisx-worktree 则跳过, 脚本覆盖更新 (`references/diagnose.md`) | hook 配置损坏 → 报告冲突位置, 请用户确认覆盖再写 |
| 缺 `config.yaml` | 创建 config.yaml 注入 hooks; finish-work 缺则跳过, 其余维度照注 | 全部目标缺失 → 报告未注入维度 |
| 用户在步骤2 AskUserQuestion 驳回 | 立即停, 0 写盘, 返回"用户驳回" | — (审批门硬规, 不绕过) |
| 某 writer agent 写盘失败 | main 派 rollback agent `git stash pop` 回滚, 重派该 writer | 重派仍失败 → 报告脏文件清单, 请用户手工核对 |
| 某 plan/writer agent 死亡或返空 | main 重派该 agent (其余 agent 结果保留, 无需全重跑) | 重派仍失败 → 该维度降级 main 串行兜底执行, 记日志 |
| 收尾链自验报 ✗ (after_finish 缺 / worktree hook 缺) | main 派 write-hook 按算法重注 → 重验 (修复循环) | 循环 3 次仍 ✗ → 回滚, 报「收尾链未装: <缺失环节>」 |

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/agent-orchestration.md` | **编排核心**: 两阶段 4+3 agent 清单 + 并发分组 + disjoint 文件集分区 + 6 字段 prompt 模板 + main 只编排不操作 |
| `references/diagnose.md` | Phase A plan-diagnose: 现状诊断 + 首次/更新模式 |
| `references/finishcmd-injection.md` | Phase A plan-finishcmd / B write-finishcmd: 目标 finish-work.md 全链注入 (Option B) |
| `references/spec-injection.md` | Phase A plan-spec / B write-spec: spec 规范文档 (仅新增 worktree spec) |
| `references/hook-injection.md` | plan-hook / write-hook: trellis 生命周期 hook (config.yaml) worktree 自动化 + 收尾 + task.md 看板 + packages |
| `references/apply-verify.md` | 审批门 + 写盘 + 自验 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask
- `trellisx-spec` — spec 破坏式优化
- `trellisx-workspace` — 维护 `.trellis/task.md` 任务看板 (含 `depends_on` → 前置列)
- `trellisx-flow` — 消费看板前置列 (task.json `depends_on`) 做 task 级 DAG 调度 (冲突自算边 ∪ 显式前置边); apply 注入的 taskmd 前置列即其调度输入
