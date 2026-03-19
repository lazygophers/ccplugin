# Loop 深度迭代详细实现 - 辅助功能

本文档包含失败调整、完成阶段和辅助函数。

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

### 质量阈值获取

```python
def get_quality_threshold(iteration):
    """获取当前轮次的质量阈值（动态递进）"""
    thresholds = {
        1: 60,   # Foundation（基础）
        2: 75,   # Enhancement（增强）
        3: 85,   # Refinement（精化）
    }
    # 第 4+ 轮保持 90 分（Excellence - 卓越）
    return thresholds.get(iteration, 90)
```

### 任务复杂度评估

```python
def assess_task_complexity(task):
    """评估任务复杂度（总分 100）"""

    # 1. 文件变更数（0-25分）
    file_count = estimate_file_count(task)
    file_score = min(25, file_count * 5) if file_count <= 5 else 25

    # 2. 技术栈新颖度（0-25分）
    tech_novelty = assess_tech_novelty(task)
    tech_score = {"familiar": 5, "new": 15, "unknown": 25}[tech_novelty]

    # 3. 任务类型（0-25分）
    task_type = classify_task_type(task)
    type_score = {"bug_fix": 5, "feature": 15, "refactor": 25}[task_type]

    # 4. 质量要求（0-25分）
    quality_req = assess_quality_requirement(task)
    quality_score = {"basic": 5, "production": 15, "enterprise": 25}[quality_req]

    total_score = file_score + tech_score + type_score + quality_score

    # 确定复杂度等级和最小迭代次数
    if total_score <= 30:
        complexity = "simple"
        min_iterations = 1
    elif total_score <= 60:
        complexity = "moderate"
        min_iterations = 2
    else:
        complexity = "complex"
        min_iterations = 3

    return {
        "complexity": complexity,
        "min_iterations": min_iterations,
        "score": total_score,
        "breakdown": {
            "file_count": file_score,
            "tech_novelty": tech_score,
            "task_type": type_score,
            "quality_req": quality_score
        }
    }
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

### 研究轮数统计

```python
def count_research_rounds():
    """统计深度研究执行次数"""
    # 从执行历史中统计
    research_count = 0
    for event in execution_history:
        if event["type"] == "research":
            research_count += 1
    return research_count
```

### 优化建议格式化

```python
def format_optimizations(optimizations):
    """格式化优化建议"""
    formatted = []
    for idx, opt in enumerate(optimizations, 1):
        formatted.append(f"""
{idx}. {opt['title']} (优先级: {opt['priority']})
   - 描述: {opt['description']}
   - 预期收益: {opt['benefit']}
   - 实施成本: {opt['cost']}
   - ROI: {opt.get('roi', 'N/A')}
""")
    return "\n".join(formatted)
```
