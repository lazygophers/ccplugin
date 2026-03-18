# 深度迭代详细说明

## 深度迭代 vs 普通迭代

| 维度 | 普通迭代 | 深度迭代 |
|------|---------|---------|
| 目标 | 完成功能 | **完美满足预期** |
| 迭代策略 | 失败重试 | **质量递进提升** |
| 验收标准 | 功能通过 | **质量达标 + 最佳实践** |
| 研究深度 | 浅层 | **深度研究（论文、案例、专家实践）** |
| 迭代终止 | 功能完成 | **用户完全满意** |

## 深度迭代流程

### 阶段 1：深度理解（Deep Understanding）

**目标**：不仅理解"做什么"，更要理解"为什么"和"最佳方案是什么"

```python
# 调用 deepresearch 深度研究
research_result = Agent(
    agent="deepresearch:deep-research",
    prompt=f"""深度研究任务：{user_task}

要求：
1. 查找最新论文、技术博客、开源项目
2. 对比 3-5 种解决方案的优劣
3. 确定最佳实践和避坑指南
4. 提供可量化的质量标准

输出：
- 技术方案对比表
- 推荐方案 + 理由
- 质量标准（可量化）
- 参考资料链接
"""
)

# 将研究结果融入计划
planner_result = Agent(
    agent="task:planner",
    prompt=f"""基于深度研究设计计划：{user_task}

研究发现：{research_result['findings']}
推荐方案：{research_result['recommended_solution']}
质量标准：{research_result['quality_criteria']}

要求：
- 采用推荐方案
- 遵循最佳实践
- 验收标准包含质量指标
"""
)
```

### 阶段 2：质量递进（Quality Progression）

**迭代质量等级**（递进式，无轮数上限）：

| 迭代轮次 | 质量阈值 | 质量等级 | 验收标准 |
|---------|---------|---------|---------|
| 第 1 轮 | 60分 | Foundation（基础） | 功能实现，测试通过 |
| 第 2 轮 | 75分 | Enhancement（增强） | 边界处理，错误处理，性能优化 |
| 第 3 轮 | 85分 | Refinement（精化） | 代码质量，可维护性，文档完善 |
| 第 4+ 轮 | 90分 | Excellence（卓越，保持） | 最佳实践，可扩展性，安全性，持续改进 |

**质量门控**：

```python
def quality_gate_check(iteration, result):
    expected_level = get_quality_level(iteration)

    quality_metrics = {
        "functionality": check_functionality(result),
        "test_coverage": check_test_coverage(result),
        "code_quality": check_code_quality(result),
        "performance": check_performance(result),
        "maintainability": check_maintainability(result),
        "security": check_security(result),
        "best_practices": check_best_practices(result)
    }

    quality_score = calculate_score(quality_metrics, expected_level)

    if quality_score < expected_level.threshold:
        return {
            "status": "needs_improvement",
            "current_score": quality_score,
            "required_score": expected_level.threshold,
            "gaps": identify_gaps(quality_metrics, expected_level)
        }
    else:
        return {"status": "passed", "score": quality_score}
```

### 阶段 3：深度分析（Deep Analysis）

**失败深度分析**：

```python
if verification_result["status"] == "failed":
    analysis_result = Agent(
        agent="deepresearch:deep-research",
        prompt=f"""深度分析失败原因：

任务：{failed_task.description}
错误：{failed_task.error}
已尝试方案：{tried_solutions}

要求：
1. 根本原因分析（5 Why 法）
2. 查找类似问题的解决案例
3. 对比多种修复方案
4. 提供最优修复策略

输出：
- 根本原因
- 3 种修复方案对比
- 推荐方案 + 理由
- 预防措施
"""
    )

    adjustment = Agent(
        agent="task:adjuster",
        prompt=f"""基于深度分析调整：

根本原因：{analysis_result['root_cause']}
推荐方案：{analysis_result['recommended_fix']}

要求：应用推荐方案，并添加预防措施
"""
    )
```

### 阶段 4：持续改进（Continuous Improvement）

```python
if verification_result["status"] == "passed":
    improvement = Agent(
        agent="task:verifier",
        prompt=f"""质量提升分析：

当前结果：{current_result}
质量分数：{quality_score}

要求：
1. 对比业界最佳实践
2. 识别可优化点
3. 评估优化价值 vs 成本
4. 提供优化建议

输出：
- 可优化点列表（优先级排序）
- 预期收益
- 实施成本
- 是否值得优化
"""
    )

    if improvement["high_value_optimizations"]:
        user_decision = AskUserQuestion(f"""
任务已通过验收，但发现高价值优化点：

{format_optimizations(improvement['high_value_optimizations'])}

是否继续优化？
1. 是，纳入当前任务
2. 否，记录为技术债
3. 完成，结果已满意
""")

        if user_decision == "是，纳入当前任务":
            goto("计划设计")  # 新一轮迭代
```

## 深度迭代终止条件

满足以下**所有**条件时终止：

1. **功能完整性**：所有验收标准通过
2. **质量达标**：质量分数 ≥ 当前迭代的阈值
3. **最佳实践**：遵循行业最佳实践（无明显偏离）
4. **用户满意**：用户明确确认"完全符合预期"
5. **最小迭代**：达到最小迭代次数（根据任务复杂度动态确定）

**决策树**：

```
所有验收标准通过？
├─ 否 → 继续迭代（失败调整）
└─ 是 → 质量分数达标？
         ├─ 否 → 继续迭代（质量提升）
         └─ 是 → 遵循最佳实践？
                  ├─ 否 → 继续迭代（重构优化）
                  └─ 是 → 达到最小迭代？
                           ├─ 否 → 继续迭代（质量递进）
                           └─ 是 → 用户满意？
                                    ├─ 否 → 继续迭代（需求精化）
                                    └─ 是 → **完成**
```

## 深度迭代配置

```python
# 评估任务复杂度，动态确定迭代配置
complexity_config = assess_task_complexity(user_task)

deep_iteration_config = {
    "mode": "deep",  # standard | deep
    "min_iterations": complexity_config["min_iterations"],  # 最小迭代次数（1-3 轮）
    "max_iterations": None,  # 无最大轮数限制，持续迭代直到质量达标
    "complexity": complexity_config["complexity"],  # simple | moderate | complex
    "enable_research": True,  # 启用深度研究
    "enable_quality_gate": True,  # 启用质量门控
    "enable_continuous_improvement": True  # 启用持续改进
}

# 质量阈值通过 get_quality_threshold(iteration) 函数动态获取
# 轮次 1: 60分, 轮次 2: 75分, 轮次 3: 85分, 轮次 4+: 90分（保持）
```

## 深度研究触发条件

满足以下任一条件时触发：

1. **复杂任务**：planner 识别为"高复杂度"
2. **失败 2 次**：同一任务失败 2 次以上
3. **质量不达标**：质量分数 < 阈值 - 10
4. **用户不满意**：用户明确要求"深入研究"
5. **无现成方案**：项目中无类似实现可参考

## 输出格式

### 深度迭代报告

```json
{
  "status": "in_progress",
  "iteration": 3,
  "quality_progression": [
    {"iteration": 1, "score": 65, "level": "Foundation"},
    {"iteration": 2, "score": 78, "level": "Enhancement"},
    {"iteration": 3, "score": 87, "level": "Refinement"}
  ],
  "research_conducted": 2,
  "quality_gates_passed": 3,
  "quality_gates_failed": 1,
  "current_quality": {
    "functionality": 95,
    "test_coverage": 88,
    "code_quality": 85,
    "performance": 90,
    "maintainability": 82,
    "security": 80,
    "best_practices": 85,
    "overall_score": 87
  },
  "next_action": "continuous_improvement",
  "user_satisfaction": "pending"
}
```

## 最佳实践

### Do's ✓
- ✓ **第 1 轮就启用深度研究**（了解最佳方案）
- ✓ **每轮迭代提高质量阈值**（递进式改进）
- ✓ **失败时深度分析根本原因**（而非表面错误）
- ✓ **通过后仍检查优化空间**（追求卓越）
- ✓ **记录研究发现到 memory**（跨任务复用）

### Don'ts ✗
- ✗ **不要浅尝辄止**（功能完成 ≠ 质量达标）
- ✗ **不要重复低质量迭代**（每轮必须有质量提升）
- ✗ **不要跳过深度研究**（避免走弯路）
- ✗ **不要忽视最佳实践**（即使功能正确）
- ✗ **不要过早终止**（至少 3 轮迭代）

## 预期收益

- **质量提升**: 最终结果质量 85-95 分（vs 普通迭代 60-75 分）
- **减少返工**: 深度研究避免错误方向（节省 40-60% 时间）
- **用户满意度**: 结果完全符合预期（vs 部分满足）
- **知识积累**: 研究发现可复用到未来任务
- **最佳实践**: 自动对齐业界标准
