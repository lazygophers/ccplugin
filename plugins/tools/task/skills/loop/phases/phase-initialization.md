
# Initialization

状态重置 | 检查点恢复 | 任务目录创建 | 记忆加载 | 资源检查

**所有输出必须以 [MindFlow·${task_id}] 开头。**

## 执行流程

1. **检查点恢复**：`load_checkpoint(user_task)`，存在则恢复 iteration/context/plan_md_path/stalled_count，询问用户是否恢复：
   
   ```json
   AskUserQuestion({
     "questions": [{
       "question": "检测到中断的任务（阶段：${phase}，迭代：${iteration}），是否恢复？",
       "header": "[MindFlow·${task_id}·检查点恢复]",
       "options": [
         {"label": "恢复任务", "description": "从中断点继续执行"},
         {"label": "重新开始", "description": "清理检查点并从头开始"}
       ],
       "multiSelect": false
     }]
   })
   ```
   
   - 用户选择"恢复任务" → 跳转到保存的阶段
   - 用户选择"重新开始" → 调用 `cleanup_checkpoint()` 并继续正常初始化
2. **正常初始化**：iteration=0, stalled_count=0, guidance_count=0, max_stalled_attempts=3, context={replan_trigger: None, task_id: null}
3. **生成 task_id**：从用户任务描述提取最简短的中文描述（2-6 个汉字）
   - 必须中文，禁止日期/序号/哈希/英文/拼音/短横线
   - 不可变：loop 完成前不得修改
   - 设置 `context.task_id = task_id`
4. **【第一步】更新任务索引** `.lazygophers/tasks/index.json`（PreToolUse hook 依赖此文件，必须最先创建）：
   
   索引文件使用**数组结构**，存储所有任务的基本信息，按 `updated_at` 降序排列（最新的在前）。首次创建索引文件时初始化为空数组 `[]`，后续任务插入到数组头部。
   
   **⚠️ 强制约束**：
   - **禁止使用 Write/Edit 工具操作 index.json**
   - **必须使用 Bash 工具执行以下 jq 命令**
   - **时间戳必须是整数**（`date +%s`），不可使用浮点数
   - **必须包含 updated_at 字段**
   
   **执行命令**（Bash + jq）：
   
   ```bash
   # 设置变量（从上下文中获取实际值）
   TASK_ID="已生成的task_id"     # 步骤3生成的 task_id（2-6个汉字）
   USER_TASK="用户的原始任务描述"  # 用户输入的任务描述
   TIMESTAMP=$(date +%s)          # 当前Unix时间戳（整数，秒）
   
   # 确保 .lazygophers/tasks 目录存在
   mkdir -p .lazygophers/tasks
   
   # 创建 index.json（如果不存在）
   if [ ! -f .lazygophers/tasks/index.json ]; then
       echo '[]' > .lazygophers/tasks/index.json
   fi
   
   # 更新索引：在数组头部插入当前任务（保持最新任务在前）
   jq --arg tid "$TASK_ID" \
      --arg desc "$USER_TASK" \
      --argjson ts "$TIMESTAMP" \
      '
      [{
        task_id: $tid,
        description: $desc,
        phase: "initialization",
        created_at: $ts,
        updated_at: $ts,
        iteration: 0,
        quality_score: null
      }] + .
      ' .lazygophers/tasks/index.json > .lazygophers/tasks/index.json.tmp && \
      mv .lazygophers/tasks/index.json.tmp .lazygophers/tasks/index.json
   ```
   
   **JSON 结构示例**（数组结构，按 updated_at 降序）：
   
   ```json
   [
     {
       "task_id": "修复日志",
       "description": "修复日志输出格式错误",
       "phase": "initialization",
       "created_at": 1733308800,
       "updated_at": 1733308800,
       "iteration": 0,
       "quality_score": null
     }
   ]
   ```
   
   **❌ 错误示例**（不可使用包装键）：
   ```json
   {
     "tasks": [...]
   }
   ```
   
   **索引操作规则**：
   - **创建任务**：检查 index.json 是否存在，不存在则创建空数组 `[]`；然后在数组头部插入当前任务信息
   - **更新任务**：每次阶段转换时，找到对应 task_id 的记录，更新 phase、updated_at、iteration、quality_score，然后重新排序（按 updated_at 降序）
   - **清理任务**：Cleanup 阶段完成后，更新索引中对应任务的 phase 为 `completed` 或 `failed`
   
   **【自检】验证 index.json 已正确更新**（防御性编程，避免索引创建失败导致后续 hooks 阻断）：
   
   读取 `.lazygophers/tasks/index.json` 并验证当前 `task_id` 已记录：
   
   ```bash
   # 检查是否包含当前 task_id
   jq -e --arg tid "$TASK_ID" \
     'any(.task_id == $tid)' .lazygophers/tasks/index.json
   ```
   
   **如验证失败**（索引缺失或损坏）：
   - 立即执行上述索引更新逻辑（补救创建）
   - 记录警告但**不中止**初始化流程
   - 理由：首次初始化失败可能由并发写入、权限问题等引起，自检补救可提高容错性

5. **创建任务目录**：
   ```bash
   mkdir -p .lazygophers/tasks/{task_id}
   ```

6. **写入任务元数据** `.lazygophers/tasks/{task_id}/metadata.json`：
   ```json
   {
     "task_id": "${task_id}",
     "description": "${user_task}",
     "phase": "initialization",
     "created_at": 1733308800,
     "updated_at": 1733308800,
     "iteration": 0,
     "quality_score": null,
     "error": null,
     "result": null,
     "skip_next_plan_confirm": false
   }
   ```
   - `task_id`：任务唯一标识（从用户任务描述提取的中文描述，2-6 个汉字）
   - `description`：用户原始任务描述
   - `phase`：当前阶段，枚举值：`initialization` | `planning` | `execution` | `verification` | `quality_gate` | `adjustment` | `cleanup` | `completed` | `failed`
   - `created_at`：任务创建时间（Unix 时间戳，秒）
   - `updated_at`：任务最后更新时间（Unix 时间戳，秒，每次阶段转换时更新）
   - `iteration`：当前迭代轮次（从 0 开始）
   - `quality_score`：验证质量分数（Verification 阶段写入，范围 0-100）
   - `error`：错误信息（发生错误时记录）
   - `result`：各阶段子 agent 的执行结果（对象），loop 读取后决定下一步
   - `skip_next_plan_confirm`：布尔值，当用户选择"确认并跳过计划确认"（选项B）时设为 true，Planning 完成后自动重置为 false

7. **创建空 tasks.json**：`{ "tasks": [] }`（Planning 阶段由 planner 写入）
8. **记忆加载**（可选）：如果项目有记忆系统，加载相关记忆
9. **资源检查**：`ListSkills()` + `ListAgents()`

**注意**：过期任务的清理（超过30天）由 SessionStart hook 自动处理，无需手动清理。

## 检查点规范

检查点保存在 `.lazygophers/tasks/{task_id}/checkpoints/`，用于中断后恢复。

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
