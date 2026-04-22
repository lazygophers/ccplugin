---
description: 任务终结。所有验收通过后触发，汇总执行结果、生成完成报告、提取经验教训写入 lessons.json
memory: project
color: green
model: haiku
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: low
context: fork
agent: task:done
---

# Done Skill

## 执行流程

> 任务终结，总结执行结果并整理记忆

```python
# 读取任务元数据（从索引文件获取）
index_file = ".lazygophers/tasks/index.json"
index = read_json(index_file)
metadata = index.get(task_id, {})

# 读取对齐结果（获取项目风格）
align_file = f".lazygophers/tasks/{task_id}/align.json"
align = read_json(align_file) if exists(align_file) else {}

# 阶段1：汇总执行结果（优先复用 verify 结果，避免重复读取）
verify_result = environment.get("verify_result")
plan = environment.get("plan") or (read_json(f".lazygophers/tasks/{task_id}/task.json") if exists(f".lazygophers/tasks/{task_id}/task.json") else None)

if verify_result and verify_result.get("status"):
    # verify 已通过：直接复用其 evidence_summary、quality_score 和 score_breakdown
    results = {
        "task_id": task_id,
        "status": "success",
        "quality_score": verify_result.get("quality_score"),
        "score_breakdown": verify_result.get("score_breakdown"),
        "evidence_summary": verify_result.get("evidence_summary"),
        "subtask_count": plan["metadata"]["total_tasks"] if plan else 0,
        "completed_count": sum(1 for t in (plan or {}).get("subtasks", []) if t.get("status") == "completed"),
        "changed_files": collect_changed_files(plan)
    }
else:
    # 非正常完成（放弃等）：从各阶段文件汇总
    # context.json 仅在此路径读取（正常完成不需要）
    results = collect_results({
        "task_id": task_id,
        "metadata": metadata,
        "context": read_json(f".lazygophers/tasks/{task_id}/context.json") if exists(f".lazygophers/tasks/{task_id}/context.json") else {},
        "align": align,
        "plan": plan
    })

# 阶段2：生成执行报告
report = generate_completion_report({
    "results": results,
    "code_style": align.get("code_style_follow", {})
})

# 阶段3：整理经验
# 经验保存到 .lazygophers/lessons.json（项目级，跨任务共享）
# 格式：数组，每个元素是一条经验记录
lessons_file = ".lazygophers/lessons.json"
existing = read_json(lessons_file) if exists(lessons_file) else []
new_lesson = extract_lessons(task_id, results, report)
if new_lesson and new_lesson.get("lessons"):
    existing.append(new_lesson)
    write_json(lessons_file, existing)

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
print(f"[flow·{task_id}·done] 任务已完成")

return report
```

## 报告输出格式

完成报告应包含以下结构，向用户简明展示结果：

```
[flow·{task_id}·done] 任务完成

## 结果
- 目标：{task_goal}
- 状态：{成功/部分成功/失败}
- 子任务：{completed}/{total} 完成

## 变更文件
- {file_1}：{变更摘要}
- {file_2}：{变更摘要}

## 验证
- {criteria_1}：✓ 通过
- {criteria_2}：✓ 通过

## 经验（如有）
- {lesson_1}
```

> 报告应简洁（≤20行），不重复已有的 verify 证据。

## 经验教训结构

保存到项目记忆时使用以下结构，便于未来任务参考：

```json
{
  "task_id": "任务ID",
  "task_type": "bug-fix|new-feature|refactor|...",
  "outcome": "success|partial|failed",
  "timestamp": "ISO8601",
  "modules": ["涉及的模块路径"],
  "keywords": ["任务关键词，用于语义匹配"],
  "lessons": [
    {
      "category": "pattern|pitfall|toolchain|style",
      "description": "具体经验描述",
      "applies_to": "适用的模块/技术/场景"
    }
  ],
  "adjust_history": [
    {"attempt": 1, "failure_type": "test-failure", "resolution": "自动修复"}
  ]
}
```

> 只记录非显而易见的经验。"代码需要通过 lint" 不值得记录；"项目的 ruff 配置禁用了 E501 所以长行不算违规" 值得记录。

## 检查清单

- [ ] 执行结果已从各阶段文件汇总
- [ ] 完成报告已按格式输出给用户
- [ ] 经验教训已按结构保存（仅非显而易见的）
- [ ] adjust_history 已记录（如有调整循环）

