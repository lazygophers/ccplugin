
# Initialization

状态重置 | 检查点恢复 | 任务目录创建 | 残留清理 | 记忆加载 | 资源检查

**所有输出必须以 [MindFlow·${task_id}] 开头。**

## 执行流程

1. **检查点恢复**：`load_checkpoint(user_task)`，存在则恢复 iteration/context/plan_md_path/stalled_count，跳转到保存的阶段
2. **正常初始化**：iteration=0, stalled_count=0, guidance_count=0, max_stalled_attempts=3, context={replan_trigger: None, task_id: null}
3. **生成 task_id**：从用户任务描述提取最简短的中文描述（2-6 个汉字）
   - 必须中文，禁止日期/序号/哈希/英文/拼音/短横线
   - 不可变：loop 完成前不得修改
   - 设置 `context.task_id = task_id`
4. **【最高优先级】创建任务目录和元数据文件**（Stop hook 依赖此文件）：
   ```bash
   mkdir -p .claude/tasks/{task_id}
   ```
   写入 `.claude/tasks/{task_id}/metadata.json`：
   ```json
   {
     "task_id": "${task_id}",
     "description": "${user_task}",
     "phase": "initialization",
     "created_at": "ISO8601",
     "updated_at": "ISO8601",
     "iteration": 0,
     "quality_score": null,
     "error": null,
     "result": null
   }
   ```
   - `result`：各阶段子 agent 的执行结果（对象），loop 读取后决定下一步
   - `phase` 枚举：`initialization` | `planning` | `execution` | `verification` | `quality_gate` | `adjustment` | `cleanup` | `completed` | `failed`
   - 每次阶段转换时更新 `phase`、`updated_at`
5. **创建空 tasks.json**：`{ "tasks": [] }`（Planning 阶段由 planner 写入）
6. **残留清理**：
   - 扫描 `.claude/tasks/*/plan.md`，删除非当前任务的残留计划文件
   - 扫描 `.claude/tasks/*/metadata.json`，非当前 task_id 的非终态文件自动修正为 `failed`，终态文件直接删除
   - 禁止因发现残留而阻断当前任务初始化
7. **记忆加载**：生成 session_id(MD5) → `load_task_memories()` → 显示 episodic(前 3 个) + semantic 记忆
8. **资源检查**：`ListSkills()` + `ListAgents()`

## 检查点规范

检查点保存在 `.claude/checkpoints/{task_id}.json`，用于中断后恢复。

| 函数 | 时机 |
|------|------|
| `save_checkpoint(user_task, iteration, phase, context)` | 计划确认/执行完成/验证完成/调整完成 |
| `load_checkpoint(user_task)` | Loop 初始化，匹配 task_id → 时效检查(>24h 过期) → 询问用户恢复/重新开始 |
| `cleanup_checkpoint(user_task)` | 任务完成/用户选择重新开始 |

必需字段：`user_task` | `task_id` | `iteration`(int>=0) | `phase`(enum) | `context`(object) | `timestamp`(ISO8601)

### resume_phase 规则

- phase=`planning` → resume=`execution`
- phase=`execution` → resume=`verification`
- phase=`verification` → resume=`quality_gate`(passed) 或 `adjustment`(failed)
- phase=`adjustment` → resume=`prompt_check`

## 状态转换

成功 → PromptOptimization（提示词优化） | 检查点恢复 → 对应阶段
