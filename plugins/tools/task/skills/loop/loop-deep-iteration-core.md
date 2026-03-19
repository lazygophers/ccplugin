# Loop 深度迭代详细实现 - 核心流程

本文档包含深度迭代的配置、研究、计划和验证核心流程。

## 深度迭代配置

在 loop 初始化时设置（动态评估任务复杂度）：

```python
# 评估任务复杂度，动态确定迭代配置
complexity_config = assess_task_complexity(user_task)

deep_iteration_config = {
    "mode": "deep",  # 深度迭代模式（默认）
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

## 深度研究阶段（1.5）

### 触发条件

满足任一条件时触发：
- 第 1 轮迭代（了解最佳方案）
- 复杂任务（planner 识别为高复杂度）
- 失败 2 次以上（同一任务）
- 质量不达标（分数 < 阈值 - 10）
- 用户明确要求深入研究

### 实现代码

```python
research_result = None

if should_trigger_research(user_task, iteration, deep_iteration_config):
    print(f"[MindFlow·{user_task}·深度研究/{iteration}·进行中]")

    research_result = Agent(
        agent="deepresearch:deep-research",
        prompt=f"""深度研究任务：{user_task}

研究目标：找到最优解决方案，确保结果完全符合预期

要求：
1. 查找最新技术方案（论文、博客、开源项目、2026 最佳实践）
2. 对比 3-5 种解决方案的优劣（技术栈、性能、可维护性）
3. 确定最佳实践和避坑指南
4. 提供可量化的质量标准

输出格式：
- 技术方案对比表（方案名、优点、缺点、适用场景）
- 推荐方案 + 理由
- 质量标准（可量化指标）
- 参考资料链接
"""
    )

    print(f"✓ 深度研究完成：推荐方案 - {research_result.get('recommended_solution', 'N/A')}")
```

## 计划设计阶段（融合研究结果）

### 实现代码

```python
iteration += 1

# 构建 planner prompt（融合研究结果）
planner_prompt = f"""设计执行计划：{user_task}（第 {iteration} 轮，深度迭代模式）

质量目标：{deep_iteration_config['quality_threshold'][iteration]} 分
迭代等级：{get_iteration_level(iteration)}  # Foundation/Enhancement/Refinement/Excellence

要求：
- 中等深度分析、MECE 分解、DAG 依赖
- 带中文注释的 Agent/Skills（来源：@task, @project, @user 等）
- 如果功能已存在，返回空 tasks 数组
"""

# 如果有研究结果，融入计划设计
if research_result:
    planner_prompt += f"""

基于深度研究：
研究发现：{research_result.get('findings', '')}
推荐方案：{research_result.get('recommended_solution', '')}
质量标准：{research_result.get('quality_criteria', '')}

要求：
- 采用推荐方案
- 遵循最佳实践
- 验收标准包含质量指标（测试覆盖率、性能、可维护性等）
"""

planner_result = Agent(agent="task:planner", prompt=planner_prompt)
```

## 结果验证阶段（质量门控 + 持续改进）

### 质量门控检查

```python
# 获取当前轮次的质量阈值（动态递进）
quality_threshold = get_quality_threshold(iteration)  # 1:60, 2:75, 3:85, 4+:90

verification_result = Agent(agent="task:verifier", prompt=f"""
验证任务（深度迭代模式）：{user_task}（第 {iteration} 轮）

质量阈值：{quality_threshold} 分
迭代等级：{get_iteration_level(iteration)}

要求：
1. 验证所有验收标准
2. 计算质量分数（功能、测试覆盖率、性能、可维护性、安全性、最佳实践）
3. 对比业界最佳实践
4. 生成验收报告

输出格式：
- status: passed/suggestions/failed
- quality_score: 总分（0-100）
- quality_breakdown: {{functionality, test_coverage, code_quality, performance, maintainability, security, best_practices}}
- gaps: 与质量阈值的差距
- improvement_suggestions: 改进建议
""")

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}·质量{verification_result.get('quality_score', 0)}分]")

# 质量门控检查
if deep_iteration_config['enable_quality_gate']:
    quality_score = verification_result.get('quality_score', 0)

    if quality_score < quality_threshold:
        print(f"⚠ 质量门控未通过：{quality_score} < {quality_threshold}")
        print(f"差距：{verification_result.get('gaps', [])}")
        goto("失败调整")  # 质量不达标视为失败
```

### 最小迭代次数检查

```python
if verification_result["status"] == "passed":
    # 深度迭代：检查是否达到最小迭代次数
    if iteration < deep_iteration_config['min_iterations']:
        print(f"✓ 验收通过，但未达最小迭代次数（{iteration}/{deep_iteration_config['min_iterations']}）")
        user_decision = AskUserQuestion(
            question=f"功能已完成，但建议继续优化（当前 {iteration} 轮，建议至少 {deep_iteration_config['min_iterations']} 轮）",
            options=["继续优化", "提前完成"]
        )
        if user_decision == "继续优化":
            goto("计划设计")
        else:
            goto("全部完成")
```

### 持续改进检查

```python
# 持续改进检查
if deep_iteration_config['enable_continuous_improvement']:
    improvement = Agent(agent="task:verifier", prompt=f"""
质量提升分析：

当前结果：{verification_result}
质量分数：{quality_score}

要求：
1. 对比业界最佳实践
2. 识别可优化点（性能、可维护性、扩展性、安全性）
3. 评估优化价值 vs 成本
4. 提供高价值优化建议

输出：
- high_value_optimizations: 高价值优化点（优先级排序）
- expected_benefits: 预期收益
- implementation_cost: 实施成本
- recommendation: 是否值得优化
""")

    if improvement.get("high_value_optimizations"):
        user_decision = AskUserQuestion(f"""
任务已通过验收（质量 {quality_score} 分），但发现高价值优化点：

{format_optimizations(improvement['high_value_optimizations'])}

是否继续优化？
1. 是，纳入当前任务
2. 否，记录为技术债
3. 完成，结果已满意
""")

        if user_decision == "是，纳入当前任务":
            goto("计划设计")  # 新一轮优化迭代
        elif user_decision == "否，记录为技术债":
            # 记录到 .claude/memory/tech-debt.md
            record_tech_debt(improvement['high_value_optimizations'])
            goto("全部完成")
        else:
            goto("全部完成")
```
