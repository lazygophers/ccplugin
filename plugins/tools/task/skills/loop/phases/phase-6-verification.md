<!-- STATIC_CONTENT: Phase 6流程文档，可缓存 -->

# Phase 6: Verification

## 概述

结果验证阶段系统性检查所有任务的执行结果，确保满足验收标准。

## 目标

- 验收标准检查（acceptance_criteria）
- 质量评分（0-100分）
- 回归测试
- 终止条件判断

## 执行流程

```python
verification_result = Agent(
    agent="task:verifier",
    prompt=f"""执行结果验证：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
)

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")

# 更新plan文件整体状态（passed→completed, failed→failed）
update_plan_frontmatter(plan_md_path, status=verification_result["status"],
                        completed_count=count_completed_tasks())

# 【检查点保存】结果验证完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="verification",
    context=context,
    plan_md_path=str(plan_md_path),
    additional_state={
        "verification_status": verification_result["status"],
        "verification_report": verification_result["report"]
    }
)

# 状态转换
status = verification_result["status"]

if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    # 自动继续优化（已移除用户确认）
    print(f"检测到优化建议，自动继续下一轮迭代...")
    print("建议列表：")
    for s in verification_result['suggestions']:
        print(f"  - {s['suggestion']}")

    # 标记为 verifier 触发的重新规划，跳过用户确认
    context["replan_trigger"] = "verifier"
    goto("计划设计")

elif status == "failed":
    goto("失败调整")
```

## 验收状态说明

### passed（通过）

- **条件**：所有验收标准通过，无优化建议
- **输出**：质量评分 ≥ 80
- **下一步**：进入完成阶段（Phase 8）

### suggestions（建议优化）

- **条件**：所有验收标准通过，但有优化空间
- **输出**：质量评分 60-79，附带优化建议列表
- **下一步**：自动触发重新规划（Phase 4），跳过用户确认

### failed（失败）

- **条件**：至少一个验收标准未通过
- **输出**：质量评分 < 60，详细失败原因
- **下一步**：进入失败调整阶段（Phase 7）

## 验收标准检查

verifier agent 会检查以下方面：

1. **功能完整性**：所有计划任务是否完成
2. **验收标准**：每个任务的 acceptance_criteria 是否满足
3. **代码质量**：是否符合项目规范
4. **测试覆盖**：是否有足够的测试用例
5. **回归测试**：是否影响现有功能

## 输出

- 验收状态（passed/suggestions/failed）
- 验收报告（≤100字）
- 质量评分（0-100）
- 优化建议列表（如有）
- 失败原因（如有）

## 状态转换

- **passed（无建议）** → 全部完成（Phase 8）
- **suggestions（有建议）** → 计划设计（Phase 4，自动重规划）
- **failed（失败）** → 失败调整（Phase 7）

## 相关文档

- [../verifier/SKILL.md](../verifier/SKILL.md) - 结果验证器规范
- [flows/verify.md](../flows/verify.md) - 验证流程详细说明

<!-- /STATIC_CONTENT -->
