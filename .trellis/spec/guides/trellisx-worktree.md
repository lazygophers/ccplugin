---
created: 2026-06-13
authored-by: trellisx-apply
---

# trellisx worktree + subtask 约定

何时被读: trellis task 实施时 (sub-agent dispatch 注入)
谁读: main / 执行者 agent
不遵守的代价: worktree 污染主工作区 / subtask 无隔离

## worktree 隔离

- task.py start 后由 trellis 生命周期 hook (`after_start`) 自动建 worktree (自适应 3 布局: .trellis 同级 git / 微服务子目录 sparse / 多子仓读 task package 定位子仓 git); archive 触发 `after_archive` 销毁
- 多子仓 (.trellis 非 git 根, 子仓在下层如 go/node): task 须先 `task.py set-scope <子仓>` 标注, hook 才能定位
- 全部源码改动**必须**落 worktree 内 (`<git根>/.worktrees/<name>`), 主工作区保持干净
- main 可直接写源码 (trellis inline), 但目标路径必须在 worktree
- 复杂 / 并行 subtask → 派 sub-agent (**共享 task worktree**, 不传 isolation:worktree) 或 agent-team 成员 (在 task worktree 内); 多 worktree 属 opt-in
- task archive 时 worktree 干净 → 自动销毁; 脏 → 警告先合并

## subtask 拆分 + 异步并行

- 启用判定跟随 trellis 原生 parent/child 语义: 本请求含**多个独立可验收交付**才拆 child task (`task.py create --parent`), 不看数量; 单一交付 → 轻量单 task inline
- 多交付: parent/child 是**任务级依次**分解 (child 按依赖顺序依次执行, 非并行); 单个 child/task 内 exec 的无依赖 subtask 才并行 (PRD 调度图标并行组, 同一消息一次性派多个 sub-agent 真并行); 禁串行逐个派 subtask
- 单交付: main 在 worktree 内直接写, 无需派 agent
- parent-child 用 trellis 原生 `task.py add-subtask`
