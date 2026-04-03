
# Initialization

## 目标

状态重置(iteration=0, context={}) | 检查点恢复 | Memory加载 | 资源检查

## 执行流程

**所有输出必须以 [MindFlow·${task_id}] 开头。**

1. **检查点恢复**：load_checkpoint(user_task)，存在则恢复 iteration/context/plan_md_path/stalled_count，跳转到保存的阶段(planning/confirmation/execution/verification/adjustment)
2. **正常初始化**：iteration=0, stalled_count=0, guidance_count=0, max_stalled_attempts=3, context={replan_trigger: None, task_id: null}
3. **生成任务ID**：从用户任务描述中提取最简短的中文描述作为 `task_id`（如"修复日志"、"添加认证"、"优化查询"）。规则：
   - **必须中文**，用最少的字描述任务核心（2-6个汉字）
   - **禁止**附加日期、序号、哈希等避免重复的标识
   - **禁止**使用英文、拼音、短横线分隔
   - **不可变**：一个 loop 完成前不得修改 task_id
   - 设置 `context.task_id = task_id`
   - 后续所有输出必须以 `[MindFlow·${task_id}]` 开头
4. **【最高优先级】创建任务目录和元数据文件**：task_id 生成后立即创建 `.claude/tasks/{task_id}/metadata.json`（Stop hook 依赖此文件阻止提前终止，合并原 loop-phase + status.json）
   ```bash
   mkdir -p .claude/tasks/{task_id}
   ```
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
   - `result`：当前阶段子 agent 的执行结果（对象），每次阶段转换时由子 agent 写入，loop 读取后决定下一步。各阶段 result 格式：
     - **planning**：`{status: "confirmed|rejected|no_tasks|cancelled", report?, task_count?, user_feedback?}`
     - **verification**：`{status: "passed|failed", quality_score?, report?, failed_criteria?}`
     - **adjustment**：`{strategy: "retry|debug|replan|ask_user", report?, modified_tasks?}`
     - **cleanup**：`{status: "completed|partially_completed|failed", report?, cleanup_summary?}`
   - `phase` 枚举（与 loop 阶段名一致）：`initialization` | `planning` | `execution` | `verification` | `quality_gate` | `adjustment` | `cleanup` | `completed` | `failed`
   - Stop hook 依赖 `phase` 字段判断是否允许停止，仅当 `phase` 为 `completed` 时放行
   - 每次阶段转换时更新 `phase`、`updated_at`
   - ⚠️ 已移除 `status` 字段（与 `phase` 语义重叠），统一使用 `phase` 跟踪当前阶段
5. **创建任务清单文件**：在 `.claude/tasks/{task_id}/` 目录创建空的 `tasks.json`
   ```json
   {
     "tasks": []
   }
   ```
   - Planning 阶段由 planner 写入子任务列表
   - Execution 阶段实时更新每个子任务的状态
5. **残留计划文件清理**：扫描 `.claude/tasks/*/plan.md`，对 **非当前任务** 的计划文件：
   - 检查文件 frontmatter 中的 `task_id` 和 `status`
   - `status` 为 `completed` / `cancelled` → 删除（应由 finalizer 清理但遗漏）
   - `status` 为其他（`pending`/`in_progress`）→ 说明前次 loop 未正常完成 finalization，记录警告后删除
   - 输出清理日志：`[MindFlow·${task_id}] 已清理 N 个残留计划文件（前次 loop 未正常完成 finalization）`
   - **禁止**删除当前任务的计划文件
6. **残留状态修复**：扫描 `.claude/tasks/*/metadata.json`，对 **非当前 task_id** 的文件：
   - `phase` 为 `completed` / `failed` → 正常终态，直接删除（已由 Cleanup 完成归档）
   - `phase` 为其他非终态（`initialization`/`planning`/`execution`/`verification`/`adjustment`/`cleanup`）→ **自动修正 `phase` 为 `failed`**，设 `error: "abnormal_termination: 前次 loop 未正常完成 finalization"`，更新 `updated_at`
   - **禁止**因发现其他任务的非终态状态文件而阻断当前任务的初始化流程
7. **残留状态清理**：扫描 `.claude/tasks/*/metadata.json`，删除所有非当前 task_id 的终态（`completed`/`failed`）文件及其关联的计划文件和检查点
8. **记忆加载**：生成session_id(MD5) → load_task_memories(user_task, task_type, session_id) → 显示episodic(前3个)+semantic记忆
9. **资源检查**：ListSkills() + ListAgents()

## 辅助函数

| 函数 | 输入→输出 | 说明 |
|------|----------|------|
| determine_task_type | user_task→string | 关键词匹配→feature/bugfix/refactor/docs/test/optimization/migration |
| extract_agents_used | planner_result→list | 从tasks提取去重agent列表 |
| extract_skills_used | planner_result→list | 从tasks提取去重skills列表 |
| cleanup_working_memory | session_id→bool | 清理短期记忆(已归档到episodic) |
| format_episodic_memories | episodes,max→str | 格式化情节记忆(任务/结果/相似度/规划/用时/失败信息) |
| format_semantic_memories | memories,max→str | 按domain分组格式化(前100字) |
| format_failure_patterns | patterns,max→str | 格式化失败模式(原因/恢复措施/经验) |
| extract_failure_reason | failed_tasks→str | 提取首个失败原因 |
| get_failed_tasks | planner_result→list | 过滤status=failed/error的任务 |

## 检查点规范

检查点保存在 `.claude/checkpoints/{task_id}.json`，用于中断后恢复执行。

### API

| 函数 | 时机 | 说明 |
|------|------|------|
| `save_checkpoint(user_task, iteration, phase, context)` | 计划确认/执行完成/验证完成/调整完成 | 写入检查点文件 |
| `load_checkpoint(user_task)` | Loop 初始化 | 匹配 task_id → 时效检查(>24h过期) → 询问用户恢复/重新开始 |
| `cleanup_checkpoint(user_task)` | 任务完成/用户选择重新开始 | 删除检查点文件 |

### Schema

必需字段：`user_task`(string) | `task_id`(string) | `iteration`(int≥0) | `phase`(enum) | `context`(object) | `timestamp`(ISO8601)

可选字段：`additional_state.completed_tasks`(string[]) | `additional_state.failed_tasks`(object[]) | `additional_state.execution_metrics`(object: started_at/total_duration_seconds/task_count)

### resume_phase 规则

保存时自动计算下一个应执行的阶段：
- phase=`planning` → resume_phase=`execution`
- phase=`execution` → resume_phase=`verification`
- phase=`verification` → resume_phase=`quality_gate`（passed）或 `adjustment`（failed）
- phase=`adjustment` → resume_phase=`prompt_check`

### 注意事项

时效 >24h 过期 | 恢复前必须询问用户 | 单任务同时只有一个检查点 | UTF-8 编码 | ISO8601 时间

## 状态转换

成功 → Planning(计划设计) | 检查点恢复 → 对应阶段

