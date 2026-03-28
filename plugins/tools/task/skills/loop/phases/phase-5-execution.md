<!-- STATIC_CONTENT: Phase 5流程文档，可缓存 -->

# Phase 5: Execution

按计划调度执行所有子任务，支持智能并行调度和HITL审批。

## 执行流程

1. **读取计划文件**：从 plan_md_path 读取任务列表和依赖关系
2. **复杂度评估**：对每个就绪任务调用`task:complexity-analyzer`评估4维度
3. **冲突检测**：构建file_map，检测共享文件写入
4. **计算并行度**：冲突→1(串行) | 全低→max_parallel | 混合→2
5. **选择批次**：按并行度选择无冲突任务
6. **执行**【强制】：按 DAG 依赖顺序调用 Agent 工具执行任务
   - **必须使用**：`Agent(agent=task.agent, prompt=构建独立上下文prompt)`
   - **prompt必须包含**（每次调用独立传递，不依赖会话上下文）：
     - `project_path`: ${context.project_path} — 项目根目录绝对路径
     - `task_id`: ${context.task_id} — 任务唯一标识
     - `iteration`: ${iteration} — 当前迭代轮次
     - `plan_md_path`: ${context.plan_md_path} — 计划文件绝对路径
     - `working_directory`: ${context.working_directory} — 工作目录
     - `user_task`: ${user_task} — 用户原始任务描述
     - `task.description` + `task.files` + `task.acceptance_criteria`
   - **禁止直接使用**：Edit/Write/Bash 等工具（违规将导致流程验证失败）
   - **示例**：`Agent(agent="coder（开发）@task", prompt="project_path: /Users/dev/myapp\ntask_id: task-20260328-001\niteration: 1\nplan_md_path: /Users/dev/myapp/.claude/plans/plan.md\nworking_directory: /Users/dev/myapp\nuser_task: 实现用户认证模块\n\n任务：实现用户登录功能\n关联文件：/src/auth.ts\n验收标准：测试覆盖率≥90%")`
7. **执行完整性检查**：每个任务的 Agent 执行完成后，立即验证交付物完整性：
   - **文件检查**：task.files 中列出的所有文件是否已创建/修改
   - **验收预检**：task.acceptance_criteria 中的 required 标准是否有明确证据
   - **未完成检测**：如果交付物不完整（文件缺失或验收标准无证据），标记为 `incomplete`
   - **自动继续**：incomplete 状态的任务自动重新调用 Agent，附带上次结果和缺失内容清单
   - **最大重试**：单个任务最多重试2次，仍不完整则标记为 ❌ 并记录原因
8. **状态更新**：更新plan文件任务状态(📋→⏸️→🔄→✅/❌)
9. **任务状态文件更新**：更新 `.claude/task/{task_id}.json`
   - `status` → `"executing"`
   - `phase` → `"execution"`
   - `updated_at` → 当前时间
   - `tasks[]` → 同步每个子任务的最新状态：
     ```json
     { "id": "T1", "description": "...", "status": "completed|failed|incomplete", "completed_at": "ISO8601" }
     ```
10. **检查点保存**：`save_checkpoint(phase="execution")`

## 并行调度

| 场景 | 并行度 |
|------|--------|
| 全低复杂度+无冲突 | max_parallel(默认2,上限5) |
| 混合复杂度 | 2 |
| 文件冲突 | 1(串行) |

用户约束绝不超过。详见[parallel-scheduler](../parallel-scheduler/SKILL.md)。

## HITL审批

loop 在执行阶段拦截工具调用进行风险评估：
- 低风险(读取/列表)：自动批准
- 中风险(写入/安装)：首次询问
- 高风险(删除/命令)：每次询问

用户可选：批准/拒绝/批准所有相似操作

## 状态转换

成功 → Phase 6(结果验证)

<!-- /STATIC_CONTENT -->
