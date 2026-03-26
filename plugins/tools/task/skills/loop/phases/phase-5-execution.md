<!-- STATIC_CONTENT: Phase 5流程文档，可缓存 -->

# Phase 5: Execution

## 概述

任务执行阶段按照计划调度执行所有子任务，支持智能并行调度和HITL审批。

## 目标

- Team创建（多任务）或直接执行（单任务）
- 智能并行调度（动态2-5个槽位）
- 进度跟踪
- HITL风险审批
- Team删除（执行完成后）

## 执行流程

```python
team_name = f"mindflow-execution-{iteration}"
print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")

# 【HITL 集成】加载用户配置
hitl_config = load_hitl_config()  # 从 .claude/task.local.md 加载配置

# 【智能并行调度】替代固定并行度
# 1. 获取待执行任务
ready_tasks = [task for task in planner_result["tasks"] if is_ready(task)]

# 2. 评估任务复杂度
task_complexities = {}
for task in ready_tasks:
    complexity = Agent(
        agent="task:complexity-analyzer",
        prompt=f"""评估任务复杂度：

任务 ID：{task['id']}
涉及文件：{task['files']}
依赖任务：{task['dependencies']}
Agent：{task['agent']}
Skills：{task['skills']}

要求：
1. 计算涉及文件数维度得分（30%）
2. 计算依赖深度维度得分（25%）
3. 估算 token 消耗维度得分（20%）
4. 检测文件冲突维度得分（25%）
5. 返回综合复杂度分数（0-100）和等级（low/medium/high）
"""
    )
    task_complexities[task['id']] = complexity

# 3. 检测文件冲突
file_map = {}
for task in ready_tasks:
    for file in task.get('files', []):
        if file not in file_map:
            file_map[file] = []
        file_map[file].append(task['id'])

has_conflicts = any(len(tasks) > 1 for tasks in file_map.values())

# 4. 计算动态并行度（尊重用户约束）
user_max_parallel = hitl_config.get("max_parallel_tasks", 2)
max_parallel = min(user_max_parallel, 5)  # 硬上限 5

low_complexity_count = sum(
    1 for c in task_complexities.values() if c['level'] == 'low'
)

if has_conflicts:
    parallel_degree = 1  # 存在文件冲突，串行执行
    scheduling_reason = "检测到文件冲突，任务串行执行"
elif low_complexity_count == len(ready_tasks):
    parallel_degree = max_parallel  # 全部低复杂度，最大并行
    scheduling_reason = f"全部低复杂度任务，并行度 {max_parallel}"
else:
    parallel_degree = 2  # 混合复杂度，保守策略
    scheduling_reason = "混合复杂度任务，使用默认并行度 2"

print(f"[MindFlow·任务执行] 智能调度：{parallel_degree}/{max_parallel}（用户约束）")
print(f"[MindFlow·任务执行] 调度原因：{scheduling_reason}")

# 5. 选择本批次并行任务
parallel_batch = []
for task in ready_tasks:
    if len(parallel_batch) >= parallel_degree:
        break

    # 检查是否与已选任务存在文件冲突
    task_files = set(task.get('files', []))
    conflict_free = True
    for selected in parallel_batch:
        selected_files = set(selected.get('files', []))
        if task_files & selected_files:  # 有交集
            conflict_free = False
            break

    if conflict_free:
        parallel_batch.append(task)

print(f"[MindFlow·任务执行] 本批次任务：{[t['id'] for t in parallel_batch]}")

# 6. 使用 execute agent 编排任务执行
execution_result = Agent(
    agent="task:execute",
    description="执行任务计划",
    prompt=f"执行以下任务计划：\n{json.dumps(parallel_batch, ensure_ascii=False)}"
)
# 无需手动清理资源 - Agent 自动管理生命周期

# 注意：HITL 审批在 task:execute agent 内部进行
# execute agent 会拦截每个工具调用，逐个进行风险评估和审批

# 更新plan文件状态：📋→⏸️→🔄→✅/❌，同步 frontmatter
update_plan_task_status(plan_md_path, task_id, new_icon)

print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")

# 检查是否有任务因用户拒绝而失败
if execution_result.get("user_rejected_tasks"):
    rejected_tasks = execution_result["user_rejected_tasks"]
    print(f"\n⚠️ 有 {len(rejected_tasks)} 个任务因用户拒绝操作而失败")
    for task in rejected_tasks:
        print(f"  • 任务 {task['id']}: 拒绝了操作 \"{task['rejected_operation']}\"")

# 【检查点保存】任务执行完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="execution",
    context=context,
    plan_md_path=str(plan_md_path)
)
```

## 智能并行调度说明

### 复杂度评估

任务复杂度由四个维度加权计算：

| 维度 | 权重 | 低复杂度 | 高复杂度 |
|------|------|---------|---------|
| 涉及文件数 | 30% | 1-2 个文件 | 5+ 个文件 |
| 依赖深度 | 25% | 无前置依赖 | 3+ 层依赖链 |
| 预估 token | 20% | < 10K tokens | > 50K tokens |
| 文件冲突 | 25% | 无共享文件 | 有共享文件（禁止并行） |

### 并行度计算规则

| 场景 | 并行度 | 条件 |
|------|--------|------|
| 全部低复杂度 | 最大（默认 2，配置最大 5） | 无文件冲突 |
| 混合复杂度 | 2 | 高复杂度任务独占 1 槽位 |
| 存在文件冲突 | 1（串行） | 冲突任务必须串行 |
| 用户配置覆盖 | 用户指定值 | **绝不超过用户约束** |

## HITL 审批集成

execute agent 内部会拦截每个工具调用，进行风险评估：

- **低风险**（读取文件、列表操作）：自动批准
- **中风险**（写入文件、安装依赖）：首次询问用户
- **高风险**（删除文件、执行命令）：每次都询问用户

用户可以选择：
- 批准本次操作
- 拒绝本次操作
- 批准所有相似操作（本任务内）

## 输出

- 任务执行结果
- 进度日志
- 成功/失败状态
- 用户拒绝的操作列表（如有）

## 状态转换

- **成功** → 结果验证（Phase 6）

## 相关文档

- [../execute/SKILL.md](../execute/SKILL.md) - 任务执行规范
- [../parallel-scheduler/SKILL.md](../parallel-scheduler/SKILL.md) - 智能并行调度器

<!-- /STATIC_CONTENT -->
