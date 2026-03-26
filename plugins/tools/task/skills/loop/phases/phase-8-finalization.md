<!-- STATIC_CONTENT: Phase 8流程文档，可缓存 -->

# Phase 8: Finalization

## 概述

完成阶段负责清理资源，生成最终报告，并保存任务执行记忆。

## 目标

- 删除计划文件（.md + .html）
- 清理检查点
- 保存任务执行记忆（情节记忆）
- 生成最终报告（耗时、迭代次数、质量分数）

## 执行流程

```python
finalizer_result = Agent(agent="task:finalizer",
    prompt=f"""执行 loop 完成后的收尾清理：
计划文件：{plan_md_path}
要求：1.停止任务 2.删除计划文件（含.html） 3.清理临时文件 4.生成报告
""")

# 【模式提取】从失败记录中提取模式（持续学习）
print(f"[MindFlow] 正在提取失败模式...")

# 提取模式
patterns = extract_failure_patterns(session_id)

if patterns:
    print(f"[MindFlow] ✓ 提取了 {len(patterns)} 个失败模式")
    for p in patterns:
        print(f"[MindFlow]   - {p['pattern_id']}: {p['signature']}")
        print(f"[MindFlow]     出现次数: {p['occurrences']}, 置信度: {p['confidence']:.0%}")
        if p["fixes"]:
            print(f"[MindFlow]     修复成功率: {p['fix_success_rate']:.0%}")
else:
    print(f"[MindFlow] 本次任务无失败模式（样本不足或无失败）")

# 【检查点清理】任务完成后清理检查点
cleanup_checkpoint(user_task)

# 【记忆保存】保存任务执行情节到记忆系统
print(f"[MindFlow] 正在保存任务执行记忆...")

# 计算执行时长
end_time = datetime.now()
duration_minutes = int((end_time - start_time).total_seconds() / 60)

# 提取使用的 Agents 和 Skills
agents_used = extract_agents_used(planner_result)
skills_used = extract_skills_used(planner_result)

# 保存情节记忆
episode_id = save_task_episode(
    user_task=user_task,
    task_type=determine_task_type(user_task),
    plan=planner_result,
    result="success",
    duration_minutes=duration_minutes,
    iterations=iteration,
    stalled_count=stalled_count,
    guidance_count=guidance_count,
    agents_used=agents_used,
    skills_used=skills_used
)

print(f"[MindFlow·Memory] ✓ 情节记忆已保存: {episode_id}")

# 清理短期记忆（会话状态）
session_id = context.get("session_id")
if session_id:
    cleanup_working_memory(session_id)
    print(f"[MindFlow·Memory] ✓ 短期记忆已清理")

print(f"[MindFlow·{user_task}·completed]")

# 总结报告
changed_files = get_changed_files()

print("\n## 任务总结")
print(f"状态：成功（所有验收标准通过）")
print(f"总迭代次数：{iteration}")
print(f"停滞次数：{stalled_count}")
print(f"用户指导次数：{guidance_count}")
print(f"执行时长：{duration_minutes} 分钟")

print("\n## 变更文件")
for file in changed_files:
    print(f"  - {file}")

print("\n## 记忆积累")
print(f"情节记忆 ID：{episode_id}")
print(f"会话 ID：{session_id}")
print(f"记忆 URI：workflow://task-episodes/{determine_task_type(user_task)}/{episode_id}")

print("\n任务完成")
```

## 清理操作

### 0. 模式提取（持续学习）

如果本次任务有失败记录，自动提取失败模式：

```python
print(f"[MindFlow] 正在提取失败模式...")

# 提取模式
patterns = extract_failure_patterns(session_id)

if patterns:
    print(f"[MindFlow] ✓ 提取了 {len(patterns)} 个失败模式")
    for p in patterns:
        print(f"[MindFlow]   - {p['pattern_id']}: {p['signature']}")
        print(f"[MindFlow]     出现次数: {p['occurrences']}, 置信度: {p['confidence']:.0%}")
        if p["fixes"]:
            print(f"[MindFlow]     修复成功率: {p['fix_success_rate']:.0%}")
else:
    print(f"[MindFlow] 本次任务无失败模式（样本不足或无失败）")
```

**触发条件**：
- 任务有失败记录（failures > 0）
- 失败样本 ≥3 个（可提取模式）

**输出**：
- 模式保存到情节记忆：`workflow://patterns/{pattern_id}`
- 下次任务自动匹配和应用

### 1. 计划文件删除

- 删除 `.claude/plans/{task_name}-{iteration}.md`
- 删除对应的 `.html` 文件（如果存在）

### 2. 检查点清理

- 删除 `.claude/checkpoints/{task_hash}.json`
- 释放磁盘空间

### 3. 短期记忆清理

- 归档会话状态到情节记忆
- 删除 `task://sessions/{session_id}`

### 4. 临时文件清理

- 删除执行过程中生成的临时文件
- 清理日志文件（可选）

## 记忆保存

### 情节记忆结构

```json
{
  "episode_id": "ep_20260326_abc123",
  "task_desc": "实现用户认证功能",
  "task_type": "feature",
  "result": "success",
  "plan": {
    "tasks": [...],
    "report": "计划摘要"
  },
  "metrics": {
    "duration_minutes": 45,
    "iterations": 2,
    "stalled_count": 0,
    "guidance_count": 1
  },
  "agents_used": ["coder", "tester"],
  "skills_used": ["golang", "testing"],
  "created_at": "2026-03-26T10:30:00Z"
}
```

### 记忆 URI

- **情节记忆**：`workflow://task-episodes/{task_type}/{episode_id}`
- **短期记忆**：`task://sessions/{session_id}`

## 最终报告

### 报告结构

```markdown
## 任务总结
状态：成功（所有验收标准通过）
总迭代次数：2
停滞次数：0
用户指导次数：1
执行时长：45 分钟

## 变更文件
  - src/auth/jwt.go
  - src/auth/jwt_test.go
  - go.mod

## 记忆积累
情节记忆 ID：ep_20260326_abc123
会话 ID：sess_abc123
记忆 URI：workflow://task-episodes/feature/ep_20260326_abc123

任务完成
```

## 输出

- 清理报告
- 任务完成摘要
- 记忆 URI（workflow://tasks/{task_id}）

## 状态转换

- **完成** → 结束

## 相关文档

- [../finalizer/SKILL.md](../finalizer/SKILL.md) - 完成清理器规范
- [../memory/README.md](../memory/README.md) - 记忆系统说明

<!-- /STATIC_CONTENT -->
