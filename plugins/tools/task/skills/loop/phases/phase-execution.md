
# Execution

按计划调度执行所有子任务。

## 执行流程

1. **读取计划文件**：从 plan_md_path 读取任务列表和依赖关系
2. **并行调度**：按 DAG 依赖顺序，选择无冲突的就绪任务批次（并行度上限 2）
3. **调用 Agent 执行任务**（逐批次）：
   ```
   Agent(agent=task.agent, prompt="
     project_path: {project_path}
     task_id: {task_id}
     iteration: {iteration}
     plan_md_path: {plan_md_path}
     working_directory: {working_directory}
     user_task: {user_task}
     任务描述：{task.description}
     关联文件：{task.files}
     验收标准：{task.acceptance_criteria}
     要求：完成后逐条对照验收标准自验，输出每条标准的通过/未通过状态及证据")
   ```
   - **必须通过 Agent() 调用**，禁止直接使用 Edit/Write/Bash
   - 每次调用独立传递完整上下文，不依赖会话记忆
4. **执行完整性检查**：每个 Agent 完成后验证交付物
   - 检查 task.files 是否已创建/修改、acceptance_criteria 是否有证据
   - 不完整 → 自动重试（附缺失清单），单任务最多重试 2 次
5. **状态更新**：更新 plan 文件任务状态（📋→⏸️→🔄→✅/❌）
6. **元数据更新**：更新 metadata.json `phase` → `"execution"`
7. **任务清单更新**：更新 tasks.json 每个子任务的最新状态
8. **检查点保存**：`save_checkpoint(phase="execution")`

## 并行调度规则

| 场景 | 并行度 |
|------|--------|
| 全低复杂度 + 无文件冲突 | 2（上限） |
| 混合复杂度 | 2 |
| 文件冲突（共享写入） | 1（串行） |

冲突检测：构建 file_map，检测多任务写入同一文件 → 强制串行。

## HITL 审批

loop 在执行阶段拦截工具调用进行风险评估：
- 低风险（读取/列表）：自动批准
- 中风险（写入/安装）：首次询问
- 高风险（删除/命令）：每次询问

## 强制状态转换

所有任务执行完成后（全部 ✅ 或有 ❌），**必须立即**进入 Verification（结果验证），不允许停止。

**禁止**：执行完成后结束回复。Loop 流程不可中断。
