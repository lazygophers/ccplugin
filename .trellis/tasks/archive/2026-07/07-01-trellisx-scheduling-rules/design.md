# Design — trellisx 调度规约

## 交付 1: task.md 锁 (deny + hook 双保险)

### settings.json deny
```json
{
  "permissions": {
    "deny": [
      "Edit(.trellis/task.md)",
      "Write(.trellis/task.md)"
    ]
  }
}
```
放 `.claude/settings.json` (团队共享, 本仓用)。tool 级硬阻。

### PreToolUse hook 脚本
`plugins/tools/trellisx/scripts/guard-taskmd.sh`:
- 匹配 Edit/Write 工具 + file path 含 `.trellis/task.md`
- reject + stderr 提示 "task.md 禁直接编辑, 用 trellisx-taskmd.py"
- exit 2 (block)

`.claude/settings.json` 注册:
```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "bash plugins/tools/trellisx/scripts/guard-taskmd.sh"}]}
    ]
  }
}
```

### SKILL 软约束
flow SKILL + workspace SKILL 加: "🔴 task.md 禁直接 Edit/Write, 必经 trellisx-taskmd.py (deny+hook 双保险)"。

## 交付 2: task.py 多 active task

### 数据模型变更 (active_task.py)

session 文件 (`.trellis/runtime/sessions/<context>.json`) 字段:
- **旧**: `{"current_task": "<task_ref>"}`
- **新**: `{"active_tasks": ["<ref1>", "<ref2>"], "current_task": "<ref1>"}` (current_task 保留 = "焦点" task, 向后兼容)

向后兼容读: 旧文件无 `active_tasks` → 从 `current_task` 单值构造 `[current_task]`。

### API 变更

| 函数 | 旧 | 新 |
|---|---|---|
| `resolve_active_task` | 返回 ActiveTask (单) | 返回 ActiveTasks (列表 + focus) |
| `set_active_task` | replace current | add 到 active_tasks (若超上限 2 报错) + 设 focus |
| `clear_active_task` | 清空 | 从 active_tasks 移除指定 task (finish 用) |

新增 `resolve_active_tasks` (复数, 返回全列表)。

### task.py 命令变更

| 命令 | 变更 |
|---|---|
| `current` | 默认显示 focus task; `--all` 列所有 active |
| `start <task>` | add 到 active 集 (非顶替); 若超上限 2 报错提示先 finish |
| `finish` | 从 active 集移除 current focus (非清空所有); 自动切 focus 到剩余首个 |
| `list` | 标记哪些在 active 集 |

### 上限强制

`set_active_task` 时检查 `len(active_tasks) >= 2` → 拒绝 + 提示 "task 级并发上限 2, 先 finish 一个"。禁超。

### flow SKILL + scheduling.md 多 task 规约

新增段:
- main 可同时管多 in_progress task (active_tasks 列表)
- task 级并发上限 2 (= subtask 级)
- task 间冲突判定 (复用 subtask 级算法: 跨 task write-files glob 相交 / exec-scope 相交 → 串行)
- focus task 概念 (current 指针, 默认最近 start 的)
- DAG: 不冲突的 task 并行派 subagent, 冲突的串行

## 兼容性

- 旧 session 文件 (单 current_task) 可读 (构造为单元素 active_tasks)
- 旧 task.py 调用方 (start/finish 单 task) 行为不变 (add/remove 单元素)
- subtask 级 DAG 调度零回归

## 风险 + 回归

- active_task.py 改动影响所有 task.py 命令 → 回归: start A → start B → current --all 列 [A,B] → finish → current 列 [B] → finish → current 空
- 上限强制: start A → start B → start C 报错
- 旧文件兼容: 手造单值 session 文件测读
