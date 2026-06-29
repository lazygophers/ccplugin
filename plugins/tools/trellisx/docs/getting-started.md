# trellisx 快速上手

## 1. 前置

- 一个 **trellis 项目** (cwd 或 git 根含 `.trellis/`)。无则 apply 报错退出。
- trellis 原生已装 (`task.py` 可用)。

## 2. 安装

通过 ccplugin-market 安装 trellisx 插件。装后获得 7 skill + guard hook + scripts。

## 3. 改造项目 (一次性)

在 trellis 项目内:

```
/trellisx-apply
```

apply 会: 诊断 → 出注入 plan → AskUserQuestion 审批 → 写盘 → 验证。

**审批后落盘**:
- `workflow.md`: 5 维度规则 (强推 task / subtask 拆分 / worktree 隔离 / 闭环 / 看板)
- `.trellis/config.yaml`: after_create/start/archive/finish hook
- `.trellis/scripts/trellisx-*.py`: worktree / finish / taskmd / wt
- `.trellis/spec/guides/trellisx-worktree.md`: worktree 约定
- `.claude/commands/trellis/finish-work.md`: 全链收尾
- `<git根>/.gitignore`: 排除 `.worktrees/`

幂等: 可重跑, marker 定位追加块, 零重复。`trellis update` 覆盖 workflow 后重跑即恢复。

## 4. 日常用法

### 4.1 强制走 task 闭环

```
/trellisx-flow 给 API 加 OAuth2 登录
```

flow 自判新建/并入 task → plan → exec → check → finish。

### 4.2 看任务看板

```bash
python3 .trellis/scripts/trellisx-taskmd.py show
```

### 4.3 finish 清理 (收尾两层, 先 AI 后 git)

1. **AI 层**: 收尾前 `TaskList` 查本 task 名下悬挂 Workflow/后台 agent, 逐个 `TaskStop` 关。
2. **git 层**: `task.py finish` → after_finish hook → `trellisx-finish.py` (commit→merge→销 worktree→archive)。

> 脚本只销 worktree (git)。关 Workflow/Task 是 AI 层职责, 脚本做不到。

### 4.4 批量收尾已完成 task

```
/trellisx-cleanup          # dry-run 报告
/trellisx-cleanup --apply  # 确认后执行 (清 completed ∪ merged)
```

### 4.5 start 前对抗审查

```
/trellisx-grill active task   # stress-test prd/design/implement
```

### 4.6 spec 收紧

```
/trellisx-spec optimize       # 破坏式重构 .trellis/spec/
```

## 5. 验证改造成功

| 检查 | 期望 |
| --- | --- |
| `git diff workflow.md` | 仅追加块, 原生文本零改动 |
| `task.py start <t>` 后 | `<git根>/.worktrees/<t>` 自动建, 主工作区零改动 |
| `task.py archive` 后 | worktree 自动销, task.md 看板 sync |
| guard 在 trellis 项目 | 未清理 worktree / 游离 worktree 时 Stop block |
| 非 trellis 项目 | guard 静默, 不干扰 |

## 6. FAQ

**Q: apply 会改我已有的 workflow.md 原生内容吗?**
A: 不会。仅末尾追加 (marker 幂等), 原生 no_task/Phase/check/finish/前缀不动。

**Q: 强推 task 是硬强制吗?**
A: 否, prompt 软约束 (AI 有裁量)。guard 在 Claude Code 额外 block 未清理 / 游离 worktree, 但不强制建 task。需硬强制自配。

**Q: 并行 subtask 会各自开 worktree 吗?**
A: 否。默认 1 task 1 worktree, subtask 共享 (文件集不相交并行)。多 worktree 属 opt-in (用户显式同意)。

**Q: finish 报合并冲突怎么办?**
A: `trellisx-finish.py` abort + 报清单, 不强合。需手动解决后重跑。

**Q: 跨 Codex/Cursor 等 runtime 生效吗?**
A: 注入走 trellis 原生 config.yaml hook, 跨 runtime 生效。guard 是 Claude Code 专属额外强制层。

**Q: `--no-worktree` 是什么?**
A: subagent 改主工作区 (无 worktree 分支合并, finish 跳过合并/销, 直接 commit + archive)。但 main 禁亲改源码这条不豁免。

**Q: task.md 能手编吗?**
A: 不能。一律经 `trellisx-taskmd.py`, 否则 hook/AI 列分工打架 + 格式漂移。

**Q: trellisx 和 trellis 什么关系?**
A: 补充非取代。task.py/add-subtask/implement/check/update-spec/jsonl/生命周期 hook 全用 trellis 原生; trellisx 补 worktree 隔离/subtask 编排/闭环/看板/破坏式 spec/对抗审查/批量收尾。
