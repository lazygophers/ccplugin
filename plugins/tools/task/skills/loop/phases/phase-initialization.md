
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
   
   **a) 写入任务元数据** `.claude/tasks/{task_id}/metadata.json`：
   ```json
   {
     "task_id": "${task_id}",
     "session_id": "${session_id}",
     "description": "${user_task}",
     "phase": "initialization",
     "created_at": "ISO8601",
     "updated_at": "ISO8601",
     "iteration": 0,
     "quality_score": null,
     "error": null,
     "result": null,
     "skip_next_plan_confirm": false
   }
   ```
   - `task_id`：任务唯一标识（从用户任务描述提取的中文描述，2-6 个汉字）
   - `session_id`：Claude Code 会话标识（MD5 哈希，用于记忆加载、日志关联）
   - `description`：用户原始任务描述
   - `phase`：当前阶段，枚举值：`initialization` | `planning` | `execution` | `verification` | `quality_gate` | `adjustment` | `cleanup` | `completed` | `failed`
   - `created_at`：任务创建时间（ISO8601 格式）
   - `updated_at`：任务最后更新时间（ISO8601 格式，每次阶段转换时更新）
   - `iteration`：当前迭代轮次（从 0 开始）
   - `quality_score`：验证质量分数（Verification 阶段写入，范围 0-100）
   - `error`：错误信息（发生错误时记录）
   - `result`：各阶段子 agent 的执行结果（对象），loop 读取后决定下一步
   - `skip_next_plan_confirm`：布尔值，当用户选择"确认并跳过计划确认"（选项B）时设为 true，Planning 完成后自动重置为 false
   
   **b) 更新任务索引** `.claude/tasks/index.json`：
   
   索引文件存储所有任务的基本信息列表，便于快速查询和管理。首次创建索引文件时初始化为空数组，后续任务追加到数组。
   
   ```json
   [
     {
       "task_id": "${task_id}",
       "session_id": "${session_id}",
       "description": "${user_task}",
       "phase": "initialization",
       "created_at": "ISO8601",
       "updated_at": "ISO8601",
       "iteration": 0,
       "quality_score": null
     }
   ]
   ```
   
   **索引操作规则**：
   - **创建任务**：检查 index.json 是否存在，不存在则创建空数组，然后追加当前任务信息
   - **更新任务**：每次阶段转换时，更新索引中对应 task_id 的记录（phase、updated_at、iteration、quality_score）
   - **清理任务**：Cleanup 阶段完成后，更新索引中对应任务的 phase 为 `completed` 或 `failed`
   - **过期清理**：定期清理索引中 30 天前的已完成/失败任务记录
   
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
