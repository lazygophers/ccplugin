# trellisx 脚本参考

脚本位于插件 `scripts/`。`trellisx-apply` 把它们**复制**到用户 `.trellis/scripts/` (不内联抄写, 升级重跑 apply 即更新)。

## trellisx-worktree.py

3 布局自适应 worktree 建/销。

- **调用**: `config.yaml` after_start / after_archive hook。
- **3 布局**:
  - .trellis 同级 git (普通单仓)
  - 微服务子目录 sparse (`.trellis` 在子目录, git 根在上层)
  - 多子仓 (读 task package 定位子仓 git, 需 `task.py set-scope <子仓>`)
- **行为**: start 建 `<git根>/.worktrees/<name>`; archive 销毁 (干净自动销, 脏警告先合并)。

## trellisx-finish.py

收尾 **git 层** (确定性脚本)。

- **调用**: `config.yaml` after_finish hook + 手动 CLI (`trellisx-finish.py --task <tid>`)。
- **全链**: commit → merge --no-ff (子先主后) → 销 worktree → archive。逐个提交, 幂等可重入。
- **冲突**: abort + 报清单, 不强合。
- **边界 (重要)**: `finish.py` 只销 worktree (git), **不关 Workflow/Task**。关悬挂 Workflow/后台 agent 是 **AI 层**职责 (finish 前 TaskList 查 → TaskStop 关)。

## trellisx-taskmd.py

task.md 看板**唯一**读写入口。

- **调用**: `config.yaml` after_create/start/archive hook + AI (trellisx-workspace)。
- **CLI 子命令**:

| 子命令 | 作用 |
| --- | --- |
| `sync <create\|start\|archive>` | 从 task.json 同步看板行 (hook 用) |
| `update <tid>` | 改阶段/进度/worktree (AI 主观列) |
| `show` | 查看看板 |
| `cleanup [--days N]` | 删看板已完成行 (默认 --days 0 全删) |
| `map-add <wt> <tid> <source>` | Worktree↔Task 映射登记 |
| `map-remove <wt>` | 映射移除 |
| `lint` | 看板格式检查 |
| `fix` | 自动修复 (错置行归位/英文状态归一/去重, 写前备份) |

- **铁规**: 禁直接编辑 task.md。hook 维护确定性列 (ID/名称/描述/状态), AI 维护主观列 (阶段/进度/worktree), 同行不同列互不覆盖。

## trellisx_wt.py

worktree 路径/分支/命名单一真值模块。

- **调用**: 被 worktree.py + finish.py 共用 import。
- **职责**: 集中 worktree 路径计算、分支命名、slug 规则, 避免两脚本各算各的漂移。

## trellisx-guard.py

Claude Code 运行时 hook: 强制执行载体闭环 + 完成清理。

- **调用**: 插件平台 hook (UserPromptSubmit / Stop / SubagentStop / WorktreeCreate / WorktreeRemove / FileChanged[task.md])。
- **生效条件**: 仅 trellis 项目 (cwd 或 git 根含 `.trellis/`), 否则静默 exit 0。
- **事件行为**: 详见 [architecture.md §guard hook 事件矩阵](architecture.md)。
- **健壮性铁律**: 任何异常 exit 0 静默放行, 绝不阻断会话。例外: WorktreeCreate 必须先回显 worktree_path 到 stdout。

## trellisx-packages.py

monorepo 包自动发现。

- **调用**: apply 一次性 (非 hook)。用户仓结构变化需重跑。
- **CLI**:
  - `discover [--repo R]` 只打印发现的包 (JSON), 不写盘 (plan-hook 用)
  - `apply [--repo R]` 写入 config.yaml packages: (write-hook 审批后用)
- **发现信号 (4 类, 强→弱)**: git submodule (.gitmodules) > 嵌套独立 .git 子仓 > workspace 清单 (package.json workspaces / pnpm-workspace.yaml / go.work) > 约定目录 (packages|apps|services|libs/*)。
- **安全**: 仅当项目当前无实值 `packages:` (单仓) 才自动写; 已配置 → 只报告不覆盖 (尊重用户配置)。

## trellisx-cleanup.py

批量收尾全部已完成 task。

- **调用**: trellisx-cleanup skill。
- **行为**: 复用 `trellisx-finish.py` (单任务全链) + `trellisx-taskmd.py` (看板) + worktree 安全销毁判据, **不重写 git 逻辑**。
- **完成判定**: `completed ∪ merged` (并集), 当前 active task 永不纳入。
- **护栏**: dry-run → AskUserQuestion → --apply 三段。

## 脚本与 hook 关系图

```
task.py create ─┐
task.py start  ─┼─→ config.yaml hook ─→ trellisx-worktree.py (建 worktree)
task.py archive─┤                      trellisx-taskmd.py (sync 看板)
               │
task.py finish ─→ after_finish hook ─→ trellisx-finish.py (commit→merge→销→archive)
                                         ↑
                         AI 层先 TaskStop 清悬挂 (脚本做不到)
```
