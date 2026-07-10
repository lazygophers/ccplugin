# 工作区布局与命令速查

## 工作区布局

```
.skein/
├── config.json          max_active / auto_commit / worktree_root
├── state.json           {focus: <id>}
├── task.md              看板 (经 skein.py board 渲染)
└── task/
    ├── <id>/
    │   ├── task.json    id/name/status/deps/worktree/branch
    │   ├── prd.md       需求 (skein-planning 写)
    │   ├── design.md    方案 (可选)
    │   └── implement.md 实现拆解 + 调度图
    └── archive/<年>/<月-日>/<id>/   finish 后按完成日期分层归档
```

## 命令速查

| 动作 | 命令 |
|---|---|
| 初始化工作区 | `skein.py init` |
| 建 task | `skein.py create <name> [--desc ..] [--deps a,b]` |
| 激活 (建 worktree) | `skein.py start <id>` |
| 完成 (merge+归档+销 worktree) | `skein.py finish [<id>]` |
| 看 focus / 全部 active | `skein.py current [--all]` |
| 列所有 task | `skein.py list` |
| 重渲染看板 | `skein.py board` |
