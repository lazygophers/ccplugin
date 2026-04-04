
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
4. **【第一步】更新任务索引** `.claude/tasks/index.json`（PreToolUse hook 依赖此文件，必须最先创建）：
   
   索引文件使用 Map 结构（key 为 session_id），存储所有任务的基本信息，便于快速查询和管理。首次创建索引文件时初始化为空对象 `{}`，后续任务追加到对应 session_id 的数组中。
   
   **⚠️ 重要：必须逐字执行以下 Bash+jq 命令，不可自行修改 JSON 格式。根键必须是 session_id 哈希，不可使用 "tasks"、"sessions" 等其他键名。**
   
   **执行命令**（Bash + jq）：
   
   ```bash
   # 设置变量
   TASK_ID="任务ID"              # 已生成的 task_id（2-6个汉字）
   SESSION_ID="session哈希值"    # Claude Code session_id
   USER_TASK="用户任务描述"      # 用户原始输入
   TIMESTAMP=$(date +%s)         # 当前Unix时间戳（秒）
   
   # 确保 .claude/tasks 目录存在
   mkdir -p .claude/tasks
   
   # 创建 index.json（如果不存在）
   if [ ! -f .claude/tasks/index.json ]; then
       echo '{}' > .claude/tasks/index.json
   fi
   
   # 更新索引：添加当前任务到 session_id 的任务列表
   jq --arg sid "$SESSION_ID" \
      --arg tid "$TASK_ID" \
      --arg desc "$USER_TASK" \
      --argjson ts "$TIMESTAMP" \
      '
      # 确保 session_id 键存在
      if has($sid) then . else . + {($sid): []} end |
      # 追加当前任务信息
      .[$sid] += [{
        task_id: $tid,
        description: $desc,
        phase: "initialization",
        created_at: $ts,
        updated_at: $ts,
        iteration: 0,
        quality_score: null
      }]
      ' .claude/tasks/index.json > .claude/tasks/index.json.tmp && \
      mv .claude/tasks/index.json.tmp .claude/tasks/index.json
   ```
   
   **JSON 结构示例**：
   
   ```json
   {
     "${session_id}": [
       {
         "task_id": "${task_id}",
         "description": "${user_task}",
         "phase": "initialization",
         "created_at": 1733308800,
         "updated_at": 1733308800,
         "iteration": 0,
         "quality_score": null
       }
     ]
   }
   ```
   
   **索引操作规则**：
   - **创建任务**：检查 index.json 是否存在，不存在则创建空对象 `{}`；检查 session_id 是否存在，不存在则创建空数组 `[]`；然后追加当前任务信息
   - **更新任务**：每次阶段转换时，在对应 session_id 的任务列表中找到 task_id，更新 phase、updated_at、iteration、quality_score
   - **清理任务**：Cleanup 阶段完成后，更新索引中对应任务的 phase 为 `completed` 或 `failed`
   
   **【自检】验证 index.json 已正确更新**（防御性编程，避免索引创建失败导致后续 hooks 阻断）：
   
   读取 `.claude/tasks/index.json` 并验证当前 `session_id` 和 `task_id` 已记录：
   
   ```bash
   # 检查 session_id 是否存在
   jq -e --arg sid "$SESSION_ID" 'has($sid)' .claude/tasks/index.json
   
   # 检查该 session 下是否包含当前 task_id
   jq -e --arg sid "$SESSION_ID" --arg tid "$TASK_ID" \
     '.[$sid] | any(.task_id == $tid)' .claude/tasks/index.json
   ```
   
   **如验证失败**（索引缺失或损坏）：
   - 立即执行上述索引更新逻辑（补救创建）
   - 记录警告但**不中止**初始化流程
   - 理由：首次初始化失败可能由并发写入、权限问题等引起，自检补救可提高容错性

5. **创建任务目录**：
   ```bash
   mkdir -p .claude/tasks/{task_id}
   ```

6. **写入任务元数据** `.claude/tasks/{task_id}/metadata.json`：
   ```json
   {
     "task_id": "${task_id}",
     "session_id": "${session_id}",
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
   - `session_id`：Claude Code 会话标识（MD5 哈希，用于记忆加载、日志关联）
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
8. **残留清理**：
   - 扫描 `.claude/tasks/*/plan.md`，删除非当前任务的残留计划文件
   - 扫描 `.claude/tasks/*/metadata.json`，非当前 task_id 的非终态文件自动修正为 `failed`，终态文件直接删除
   - 禁止因发现残留而阻断当前任务初始化
9. **记忆加载**：生成 session_id(MD5) → `load_task_memories()` → 显示 episodic(前 3 个) + semantic 记忆
10. **资源检查**：`ListSkills()` + `ListAgents()`

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
