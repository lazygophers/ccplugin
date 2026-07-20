# 允许 task 无 subtask 启动 — PRD (主入口)

## 目标
- [x] 移除 `skein start` / `doctor` 对 subtask 必填的硬性校验, 允许 task 无 subtask 直接启动
- [x] 保持 "执行必绑 agent (强制)" 铁律不变 — 无 subtask 的 task 由 main 派 `skein-executor` (默认) 按 task name/desc 执行
- [x] 同步 skein-flow skill 文案: "无 subtask 硬拒" → "subtask 可无, 执行必派 agent"

## 边界
范围内:
- skein.py: 删 `start` L514-515 + `doctor` L934-935 两处 subtask 必填校验
- skein-flow/SKILL.md: L35/L39/L44/L89/L94 文案同步
- agent 绑定: 无 subtask 时 main 派 skein-executor (task.json 不加 task 级 agent 字段, 靠 dispatch prompt)

范围外:
- task.json schema 不改 (不加 task 级 agent 字段)
- 看板 "无 subtask" 展示文案不改 (合法态展示, 非校验)
- skein-exec claim 逻辑不改 (无 subtask 的 task claim 返回空, main 按 task 维度直接派)
- docstring 不改 (无 "必填" 明文)

已知约束:
- 6 处引用点已勘察 (skein.py×2, SKILL.md×5)
- finish/check 遍历空 subtasks list 安全, 无阻塞

## 验收标准
- [ ] `skein start <id>` 对无 subtask 的 pending task 不再硬拒, 正常启动
- [ ] `skein doctor` 不再报 "无 subtask" 错误
- [ ] skein-flow SKILL.md 无 "无 subtask 硬拒" / "至少登记 1 个" 表述
- [ ] 有 subtask 的 task 行为完全不变 (回归)
- [ ] `python3 skein.py --help` 正常, `skein list` 正常

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list allow-no-subtask`)
