# trellisx 架构

## 1. 定位: 改造工具, 非运行时框架

```
早期: trellisx = 外部 command hook 持续拦截/注入 (复杂, 需 reload, 易冲突)
现在: trellisx = 改造工具, 跑一次写进 .trellis (规则内化, trellis 自身机制生效)
```

trellisx 插件**本身无运行时注入 hook**。两套 hook 分工:

| hook | 归属 | 触发 | 职责 |
| --- | --- | --- | --- |
| trellis 原生生命周期 hook (`config.yaml` after_create/start/archive/finish) | trellisx-apply **注入**到用户项目 | task 生命周期事件 | worktree 建/销、task.md 看板、finish 全链收尾 —— 跨平台 |
| trellisx-guard 平台 hook (UserPromptSubmit/Stop/SubagentStop/WorktreeCreate/WorktreeRemove/FileChanged) | trellisx 插件自带 | Claude Code 会话事件 | 强制执行载体闭环 + 完成清理 (仅 trellis 项目) |

关键: 自动化**不依赖 Claude Code 平台 hook**, 所以跨 Codex / Cursor / OpenCode 等 runtime 生效 (走 trellis 原生 hook)。guard 是 Claude Code 专属的额外强制层。

## 2. apply 注入模型 (5 维度, 纯增量)

apply 跑一次, 把 5 维度规则**追加**进项目 `.trellis/`。绝不替换原生文本。

```
trellisx-apply
  ├─ workflow.md          ← 5 维度规则 (marker 幂等追加, i18n, 清理无效内容)
  │    ├─ [no_task]       ← +强推 task
  │    ├─ [planning]      ← +subtask 拆分判定
  │    └─ [in_progress]   ← +worktree 隔离 / 闭环收尾 / 看板 marker
  ├─ .trellis/spec/guides/trellisx-worktree.md  ← worktree 约定 (仅新增)
  ├─ .trellis/config.yaml ← after_create/start/archive/finish hook
  ├─ .trellis/scripts/trellisx-*.py  ← 从插件 scripts/ 复制
  ├─ .claude/commands/trellis/finish-work.md ← 全链收尾注入
  └─ <git根>/.gitignore   ← 排除 .worktrees/
```

**幂等保证**: 每个追加块用 marker 定位, 重跑检测到 marker 则跳过/更新而非重复追加。`trellis update` 覆盖 workflow 后重跑 apply 即恢复。

**不替换原生**: no_task 原生分类+征同意 / Phase 流程 / check / finish / 前缀 —— 仅末尾追加 trellisx 内容。

## 3. 数据流

### 3.1 改造期 (apply, 一次性)

```
用户: /trellisx-apply
  → 诊断 (.trellis/ 存在? workflow 现状? packages?)
  → 注入 plan (5 维度 + scripts 复制清单)
  → AskUserQuestion 审批
  → 写盘 (workflow.md / config.yaml / scripts / spec / commands / gitignore)
  → 验证 (hook 注册? scripts 可执行? marker 就位?)
```

### 3.2 运行期 (任务执行)

```
用户请求
  → trellisx-flow (强制闭环) 或 trellis 原生
  → planning (trellisx-orchestrate 编排 prd/design/implement/subtask)
  → task.py start
       → after_start hook: 建 worktree (3 布局自适应) + task.md sync
  → exec (trellis-implement → subagent, 共享 task worktree)
       → guard UserPromptSubmit: 注入执行载体约束 (有 active task 时)
  → check (trellis-check)
  → finish
       → AI 层: TaskList 查悬挂 Workflow/agent → TaskStop 关
       → git 层: after_finish hook → trellisx-finish.py
            (commit→merge --no-ff 子先主后→销 worktree→archive)
       → task.md sync (archive, 7 天清理)
  → guard Stop: block 未清理 worktree / 未完成 active task (三闸)
```

### 3.3 worktree 生命周期 (绑定 task)

隔离单位 = **task** (默认 1 task 1 worktree):

| 时机 | 动作 | 执行者 |
| --- | --- | --- |
| task.py start | after_start hook 自动建本 task worktree | trellisx-worktree.py |
| execute/check | 全部读写限于本 task worktree (subagent 共享) | — |
| 多 worktree (opt-in) | 用户显式同意才手动 `git worktree add` | 手动 |
| check 通过 + commit | 合并 worktree → 当前分支 | trellisx-finish.py |
| archive | 销毁 worktree + task.md sync | after_archive hook |

详见 [concepts.md §worktree 隔离单位](concepts.md)。

## 4. guard hook 事件矩阵

`trellisx-guard.py` 仅在 trellis 项目 (cwd 或 git 根含 `.trellis/`) 生效, 否则静默 exit 0。

| 事件 | 行为 |
| --- | --- |
| UserPromptSubmit | 有 active task (in_progress) → 注入执行载体约束 (实质工作派 subagent; 派 agent=真实 tool_use; 完成即清理)。无 active task → 不强制。诊断提醒独立 (worktree 映射 tid=? 待补 / task.md lint 真失败才追加) |
| WorktreeCreate | transform: 先无条件回显 worktree_path 到 stdout (缺 path=创建失败), 再 map-add \<wt\> \<tid\> \<source\>。吞异常不影响回显 |
| WorktreeRemove | map-remove 清映射 (不阻断) |
| Stop | 三类闸顶层 `{"decision":"block"}`: ①已合并未清理 worktree ②游离 worktree (tid=?/None) ③活动 task 未完成。抑制阀: 连续 block 满 3 次降级 additionalContext, 第 4 次起静默 |
| SubagentStop | additionalContext 提醒 (subagent 结束 ≠ task 完成, 不 block) |
| FileChanged (task.md) | 先跑 taskmd fix 自动修复 (错置行归位/英文状态归一/去重), 残留才 stderr 提醒 |

**健壮性铁律**: 任何异常 exit 0 静默放行, 绝不因 guard bug 阻断会话。例外: WorktreeCreate 必须先回显 path。

## 5. 脚本职责矩阵

| 脚本 | 职责 | 调用方 |
| --- | --- | --- |
| `trellisx-worktree.py` | 3 布局自适应 worktree 建/销 (同级 git / 微服务 sparse / 多子仓) | config.yaml after_start/archive |
| `trellisx-finish.py` | 收尾 git 层 (确定性): commit→merge --no-ff (子先主后)→销 worktree→archive; 冲突 abort+报清单 | config.yaml after_finish + 手动 CLI |
| `trellisx-taskmd.py` | task.md 看板唯一读写入口 (sync/update/show/cleanup/map-*/lint/fix) | config.yaml after_create/start/archive + AI |
| `trellisx_wt.py` | worktree 路径/分支/命名单一真值模块 (worktree+finish 共用 import) | 被上述脚本 import |
| `trellisx-guard.py` | Claude Code 运行时 hook: 强制执行载体闭环 + 完成清理 | 插件平台 hook |
| `trellisx-packages.py` | monorepo 包自动发现 (discover/apply, 4 类信号: submodule>嵌套git>workspace清单>约定目录) | apply 一次性 |
| `trellisx-cleanup.py` | 批量收尾全部已完成 task (复用 finish+taskmd+worktree 安全判据) | trellisx-cleanup skill |

apply 把脚本从插件 `scripts/` **复制**到用户 `.trellis/scripts/`, 不内联抄写 (升级时重跑 apply 即更新)。

## 6. 与 trellis 融合 (非取代)

| 能力 | 用谁 |
| --- | --- |
| task.py / add-subtask / implement / check / update-spec / jsonl / 生命周期 hook | trellis 原生 |
| worktree 隔离 + subtask 编排 + 闭环 + task.md 看板 + 破坏式 spec + 对抗审查 + 批量收尾 | trellisx (补 trellis 缺的) |

## 7. 跨平台策略

注入的 hook 写在 `.trellis/config.yaml` (trellis 原生契约), 非 Claude Code settings —— 所以 Codex / Cursor / OpenCode / Gemini CLI 等任何兼容 trellis 的 runtime 都生效。guard 是 Claude Code 专属的额外强制层 (其他 runtime 无 guard, 但 trellis 原生 hook + workflow.md 软约束仍生效)。
