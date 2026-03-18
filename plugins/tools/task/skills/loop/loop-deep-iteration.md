# Loop 深度迭代详细实现

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

## 失败调整阶段（深度失败分析）

### 深度失败分析（失败 2 次触发）

```python
# 深度失败分析（失败 2 次以上触发）
failed_tasks = [t for t in TaskList() if t.status == "failed"]
failure_count = len([t for t in TaskList() if t.id in [ft.id for ft in failed_tasks]])

if failure_count >= 2 and deep_iteration_config['enable_research']:
    print(f"[MindFlow·{user_task}·深度分析/{iteration}·进行中]")

    analysis_result = Agent(
        agent="deepresearch:deep-research",
        prompt=f"""深度分析失败原因：

任务：{user_task}
失败任务：{[t.description for t in failed_tasks]}
错误信息：{[t.error for t in failed_tasks]}
已尝试方案：{get_tried_solutions()}

要求：
1. 根本原因分析（5 Why 法）
2. 查找类似问题的解决案例（GitHub Issues、Stack Overflow、技术博客）
3. 对比 3 种修复方案（快速修复 vs 根本解决 vs 重构）
4. 提供最优修复策略

输出格式：
- root_cause: 根本原因
- solution_comparison: 修复方案对比表
- recommended_fix: 推荐方案 + 理由
- prevention_measures: 预防措施
"""
    )

    print(f"✓ 根本原因：{analysis_result.get('root_cause', 'N/A')}")
    print(f"✓ 推荐方案：{analysis_result.get('recommended_fix', 'N/A')}")
```

### 融合深度分析结果的调整

```python
# 调用 adjuster（融合深度分析结果）
adjuster_prompt = f"""失败调整：{user_task}（第 {iteration} 轮）

要求：
- 分析失败原因
- 检测停滞模式
- 应用分级升级策略（retry → debug → replan → ask_user）
"""

if 'analysis_result' in locals() and analysis_result:
    adjuster_prompt += f"""

基于深度分析：
根本原因：{analysis_result.get('root_cause', '')}
推荐修复方案：{analysis_result.get('recommended_fix', '')}
预防措施：{analysis_result.get('prevention_measures', '')}

要求：应用推荐方案，并添加预防措施到验收标准
"""

adjustment_result = Agent(agent="task:adjuster", prompt=adjuster_prompt)
```

## 完成阶段（深度迭代质量报告）

```python
# 生成深度迭代质量报告
if deep_iteration_config['mode'] == 'deep':
    quality_report = {
        "task": user_task,
        "total_iterations": iteration,
        "quality_progression": get_quality_progression(),  # 每轮质量分数
        "research_conducted": count_research_rounds(),
        "final_quality_score": verification_result.get('quality_score', 0),
        "quality_threshold_met": verification_result.get('quality_score', 0) >= deep_iteration_config['quality_threshold'].get(iteration, 90),
        "stalled_count": stalled_count,
        "guidance_count": guidance_count,
        "changed_files": get_changed_files()
    }

    print(f"""
[MindFlow·{user_task}·completed·深度迭代报告]

✓ 总迭代：{iteration} 轮
✓ 质量进展：{' → '.join([f"{q}分" for q in quality_report['quality_progression']])}
✓ 最终质量：{quality_report['final_quality_score']} 分（阈值 {deep_iteration_config['quality_threshold'].get(iteration, 90)} 分）
✓ 深度研究：{quality_report['research_conducted']} 次
✓ 用户指导：{guidance_count} 次
✓ 变更文件：{len(quality_report['changed_files'])} 个

结果：{'完全符合预期 ✓' if quality_report['quality_threshold_met'] else '部分达标'}
""")
```

## 辅助函数

### 触发条件检查

```python
def should_trigger_research(task, iteration, config):
    """检查是否应触发深度研究"""
    if not config['enable_research']:
        return False

    # 第 1 轮必定触发（了解最佳方案）
    if iteration == 1:
        return True

    # 失败 2 次以上触发
    failed_tasks = [t for t in TaskList() if t.status == "failed"]
    if len(failed_tasks) >= 2:
        return True

    # 质量不达标触发
    if iteration > 1:
        prev_quality = get_previous_quality_score()
        threshold = config['quality_threshold'].get(iteration - 1, 60)
        if prev_quality < threshold - 10:
            return True

    return False
```

### 迭代等级获取

```python
def get_iteration_level(iteration):
    """获取迭代等级名称"""
    levels = {
        1: "Foundation（基础）",
        2: "Enhancement（增强）",
        3: "Refinement（精化）"
    }
    return levels.get(iteration, "Excellence（卓越）")
```

### 质量进展追踪

```python
def get_quality_progression():
    """获取每轮迭代的质量分数"""
    # 从任务元数据或记忆中读取历史质量分数
    return [68, 78, 87]  # 示例
```

### 技术债记录

```python
def record_tech_debt(optimizations):
    """记录技术债到 .claude/memory/tech-debt.md"""
    tech_debt_file = ".claude/memory/tech-debt.md"

    content = f"""
## {datetime.now().strftime('%Y-%m-%d')} - {user_task}

### 高价值优化点

"""
    for opt in optimizations:
        content += f"- **{opt['title']}**: {opt['description']}\n"
        content += f"  - 预期收益: {opt['benefit']}\n"
        content += f"  - 实施成本: {opt['cost']}\n\n"

    # 追加到文件
    with open(tech_debt_file, 'a') as f:
        f.write(content)
```
