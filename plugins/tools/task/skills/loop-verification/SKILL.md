---
description: Loop 验证流程 - 质量门控、持续改进决策
model: sonnet
context: fork
user-invocable: false
---

# Loop 验证流程

<scope>
在 Loop 的 Check 阶段使用，负责：
1. 调用 task:verifier 验证验收标准
2. 执行质量门控评分（功能、测试、性能、可维护性、安全性）
3. 识别高价值优化点
4. 通过 AskUserQuestion 询问用户是否继续优化
</scope>

<execution_flow>

## 阶段1：结果验证

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
5. 决定验收状态（passed/suggestions/failed）
"""
)

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")

# 更新plan文件整体状态
update_plan_frontmatter(
    plan_md_path,
    status=verification_result["status"],
    completed_count=count_completed_tasks()
)
```

## 阶段2：质量门控

```python
# 计算质量综合分数
quality_score = calculate_quality_score({
    "功能完整性": verification_result.get("功能完整性", 0),
    "测试覆盖率": verification_result.get("测试覆盖率", 0),
    "性能指标": verification_result.get("性能指标", 0),
    "可维护性": verification_result.get("可维护性", 0),
    "安全性": verification_result.get("安全性", 0),
    "最佳实践": verification_result.get("最佳实践", 0)
})

# 当前轮次的质量阈值
quality_thresholds = {
    1: 60,  # Foundation
    2: 75,  # Enhancement
    3: 85,  # Refinement
    4: 90   # Excellence
}
required_score = quality_thresholds.get(iteration, 90)

print(f"质量评分：{quality_score} / {required_score}")

# 判断是否达标
quality_passed = quality_score >= required_score
```

## 阶段3：状态转换决策

```python
status = verification_result["status"]

if status == "passed" and quality_passed:
    # 检查是否达到最小迭代次数
    if iteration >= min_iterations:
        return "completed"
    else:
        # 询问用户是否继续优化
        user_choice = AskUserQuestion(
            f"当前质量：{quality_score}分，已达标。是否继续优化？",
            options=["继续优化", "完成任务"]
        )
        return "continue" if user_choice == "继续优化" else "completed"

elif status == "suggestions":
    # 有优化建议
    user_response = AskUserQuestion(
        f"{verification_result['report']}\n\n建议：\n" +
        "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
        "\n\n这些优化是否属于当前任务范围？",
        options=["是，继续优化", "否，完成任务"]
    )
    return "continue" if "是" in user_response else "completed"

elif status == "failed":
    return "adjustment"  # 进入失败调整阶段

elif not quality_passed:
    print(f"质量未达标：{quality_score} < {required_score}")
    return "adjustment"
```

</execution_flow>

<quality_scoring>

## 质量评分公式

```python
def calculate_quality_score(metrics):
    """计算综合质量分数（0-100）"""
    weights = {
        "功能完整性": 0.30,
        "测试覆盖率": 0.25,
        "性能指标": 0.15,
        "可维护性": 0.15,
        "安全性": 0.10,
        "最佳实践": 0.05
    }

    total_score = sum(
        metrics.get(key, 0) * weight
        for key, weight in weights.items()
    )

    return round(total_score, 1)
```

## 质量阈值

| 迭代轮次 | 阈值 | 等级 | 说明 |
|---------|------|------|------|
| 1 | 60 | Foundation | 基础功能完整 |
| 2 | 75 | Enhancement | 质量提升 |
| 3 | 85 | Refinement | 精细打磨 |
| 4+ | 90 | Excellence | 卓越品质 |

</quality_scoring>

<state_transitions>

**状态转换**：
- passed + 质量达标 + 达最小迭代 → 全部完成
- passed + 质量达标 + 未达最小迭代 → 计划设计（用户确认）
- suggestions → 计划设计（用户确认继续）/ 全部完成（用户确认完成）
- failed → 失败调整
- 质量不达标 → 失败调整

</state_transitions>

<references>

详细实现参见：
- [loop-deep-iteration.md](../loop/loop-deep-iteration.md#结果验证阶段质量门控--持续改进)
- Skills(task:verifier)

</references>
