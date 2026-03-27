# 检查点集成与示例

## 与 Loop 集成

| 阶段 | 操作 |
|------|------|
| 初始化 | `load_checkpoint(user_task)` → 有则恢复(iteration/context/plan_md_path)跳转对应阶段，无则正常初始化 |
| 计划设计完成 | `save_checkpoint(phase="planning")` |
| 计划确认后 | `save_checkpoint(phase="confirmation")` |
| 任务执行完成 | `save_checkpoint(phase="execution")` |
| 全部完成 | `cleanup_checkpoint(user_task)` |

## 场景示例

| 场景 | 流程 |
|------|------|
| 正常执行 | 初始化→无检查点→从头执行→各阶段保存→完成后清理 |
| 中断恢复 | 初始化→检测到检查点→询问用户(恢复/重新开始)→恢复则跳转到中断阶段继续 |
| 重新开始 | 初始化→检测到检查点→用户选择重新开始→清理检查点→从头执行 |
