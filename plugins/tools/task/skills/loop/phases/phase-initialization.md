
# Initialization

## 目标

状态重置(iteration=0, context={}) | 检查点恢复 | Memory加载 | 资源检查

## 执行流程

**所有输出必须以 [MindFlow·${task_id}] 开头。**

0. **【最高优先级】创建 Loop 状态文件**：任何其他操作之前，必须先执行此步骤（Stop hook 依赖此文件阻止提前终止）
   ```bash
   mkdir -p .claude/tasks/pending && echo "initializing" > .claude/tasks/pending/loop-phase
   ```
   - 此文件是 Stop hook 的唯一依赖项，缺失会导致 Loop 无法阻止提前停止
   - task_id 确定后（步骤3）立即重命名：`mv .claude/tasks/pending .claude/tasks/{task_id}`
   - **禁止**跳过此步骤或延后执行

1. **检查点恢复**：load_checkpoint(user_task)，存在则恢复 iteration/context/plan_md_path/stalled_count，跳转到保存的阶段(planning/confirmation/execution/verification/adjustment)
2. **正常初始化**：iteration=0, stalled_count=0, guidance_count=0, max_stalled_attempts=3, context={replan_trigger: None, task_id: null}
3. **生成任务ID**：从用户任务描述中提取最简短的中文描述作为 `task_id`（如"修复日志"、"添加认证"、"优化查询"）。规则：
   - **必须中文**，用最少的字描述任务核心（2-6个汉字）
   - **禁止**附加日期、序号、哈希等避免重复的标识
   - **禁止**使用英文、拼音、短横线分隔
   - **不可变**：一个 loop 完成前不得修改 task_id
   - 设置 `context.task_id = task_id`
   - 后续所有输出必须以 `[MindFlow·${task_id}]` 开头
4. **创建 Loop 状态文件**：在 `.claude/tasks/{task_id}/` 目录创建 `loop-phase` 文件
   ```bash
   mkdir -p .claude/tasks/{task_id} && echo "active" > .claude/tasks/{task_id}/loop-phase
   ```
   - Stop hook 依赖此文件判断是否允许停止，仅当内容为 `completed` 时放行
   - 每次阶段转换时更新（planning/execution/verification/adjustment/finalization/completed）
5. **创建任务状态文件**：在 `.claude/tasks/{task_id}/` 目录创建 `status.json` 状态文件
   ```json
   {
     "task_id": "${task_id}",
     "description": "${user_task}",
     "status": "initialized",
     "created_at": "ISO8601",
     "updated_at": "ISO8601",
     "iteration": 0,
     "phase": "initialization",
     "tasks": [],
     "plan_path": null,
     "quality_score": null,
     "error": null
   }
   ```
   - `status` 枚举：`initialized` | `planning` | `executing` | `verifying` | `adjusting` | `completed` | `failed`
   - 每次阶段转换时更新 `status`、`phase`、`updated_at`
5. **残留计划文件清理**：扫描 `.claude/plans/*.md`，对 **非当前任务** 的计划文件：
   - 检查文件 frontmatter 中的 `task_id` 和 `status`
   - `status` 为 `completed` / `cancelled` → 删除（应由 finalizer 清理但遗漏）
   - `status` 为其他（`pending`/`in_progress`）→ 说明前次 loop 未正常完成 finalization，记录警告后删除
   - 输出清理日志：`[MindFlow·${task_id}] 已清理 N 个残留计划文件（前次 loop 未正常完成 finalization）`
   - **禁止**删除当前任务的计划文件
6. **残留状态修复**：扫描 `.claude/tasks/*/status.json`，对 **非当前 task_id** 的文件：
   - `status` 为 `completed` / `failed` → 正常终态，直接删除（已由 Finalization 完成归档）
   - `status` 为其他非终态（`initialized`/`planning`/`executing`/`verifying`/`adjusting`）→ **自动修正为 `failed`**，设 `error: "abnormal_termination: 前次 loop 未正常完成 finalization"`，更新 `updated_at`
   - **禁止**因发现其他任务的非终态状态文件而阻断当前任务的初始化流程
7. **残留状态清理**：扫描 `.claude/tasks/*/status.json`，删除所有非当前 task_id 的终态（`completed`/`failed`）文件及其关联的计划文件和检查点
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

## 状态转换

成功 → Planning(计划设计) | 检查点恢复 → 对应阶段

