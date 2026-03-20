# Deep Iteration 实现指南

# Loop 深度迭代详细实现

<overview>

本文档是深度迭代实现的索引入口。深度迭代将复杂任务的执行过程分为多轮递进式优化，每轮设定递增的质量阈值，确保最终结果达到预期标准。实现细节已按职责拆分为两个文件，避免单文件过长。

</overview>

<navigation>

## 核心流程

文件：[loop-deep-iteration-core.md](loop-deep-iteration-core.md)

包含深度迭代的主干逻辑：配置初始化（复杂度评估和质量阈值设定）、深度研究阶段（1.5阶段，在正式规划前收集技术方案）、计划设计阶段（融合研究结果生成执行计划）、结果验证阶段（质量门控检查和持续改进判定）。

## 辅助功能

文件：[loop-deep-iteration-helpers.md](loop-deep-iteration-helpers.md)

包含支撑核心流程的辅助模块：失败调整阶段（深度失败分析和根因定位）、完成阶段（深度迭代质量报告生成）、辅助函数（触发条件检查、迭代等级获取、质量阈值计算、复杂度评估、技术债记录等）。

</navigation>

---

# Loop 深度迭代详细实现 - 核心流程

<overview>

本文档包含深度迭代的配置、研究、计划和验证核心流程。深度迭代的核心思路是根据任务复杂度动态确定迭代轮数和质量标准，通过逐轮递进的方式从基础功能实现到卓越质量。每个阶段都有明确的触发条件和状态转换规则，确保流程可控且高效。

</overview>

<deep_iteration_config>

## 深度迭代配置

在 loop 初始化时，首先评估任务复杂度，然后动态确定迭代参数。复杂度评估基于文件数、技术栈、任务类型和质量要求（总分 100），决定最小迭代次数（1-3 轮）。质量阈值不在配置中硬编码，而是通过 get_quality_threshold(iteration) 函数按轮次动态获取（第1轮60分、第2轮75分、第3轮85分、第4轮及以后90分）。

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

</deep_iteration_config>

<deep_research>

## 深度研究阶段（1.5）

深度研究是一个可选阶段，在正式规划前触发。其目的是避免盲目开始——通过调研最新技术方案、对比解决路径、收集最佳实践，为后续规划提供数据支撑。

满足以下任一条件时触发：第 1 轮迭代（了解最佳方案）、复杂任务（planner 识别为高复杂度）、失败 2 次以上（同一任务需要根因分析）、质量不达标（分数低于阈值10分以上）、用户明确要求深入研究。

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

    print(f"深度研究完成：推荐方案 - {research_result.get('recommended_solution', 'N/A')}")
```

</deep_research>

<planning_with_research>

## 计划设计阶段（融合研究结果）

当深度研究完成后，其结果会被注入到 planner 的 prompt 中，使计划设计基于实际调研数据而非假设。研究结果包括技术发现、推荐方案和质量标准，planner 据此设置更精确的验收标准。

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

</planning_with_research>

<verification_quality_gate>

## 结果验证阶段（质量门控 + 持续改进）

结果验证在深度迭代模式下承担三重职责：验收标准检查、质量门控评分、持续改进识别。质量门控通过多维度评分（功能、测试覆盖率、性能、可维护性、安全性、最佳实践）计算综合分数，与当前轮次的阈值对比。

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
        print(f"质量门控未通过：{quality_score} < {quality_threshold}")
        print(f"差距：{verification_result.get('gaps', [])}")
        goto("失败调整")  # 质量不达标视为失败
```

### 最小迭代次数检查

验收通过后直接完成任务。早期的最小迭代次数检查已移除，改为依赖质量门控机制来确保质量。

```python
if verification_result["status"] == "passed":
    # 直接完成任务（已移除最小迭代次数检查）
    print(f"验收通过，任务完成（迭代 {iteration} 轮）")
    goto("全部完成")
```

### 持续改进检查

验收通过后，持续改进模块会识别高价值优化点并自动触发新一轮迭代。这通过 verifier 返回 suggestions 状态实现，Loop 会自动继续优化。

```python
if deep_iteration_config['enable_continuous_improvement']:
    # 持续改进通过 verifier 的 suggestions 状态自动触发
    # 当 verifier 发现高价值优化点时，返回 suggestions 状态
    # Loop 收到后自动进入下一轮迭代

    # verifier 内部逻辑示例：
    improvement = analyze_optimization_opportunities(verification_result, quality_score)

    if improvement.get("high_value_optimizations"):
        print("发现高价值优化点，自动继续下一轮迭代...")
        for opt in improvement['high_value_optimizations']:
            print(f"  - {opt['description']} (优先级: {opt['priority']})")

        return {
            "status": "suggestions",
            "report": f"任务已通过验收（质量 {quality_score} 分），发现 {len(improvement['high_value_optimizations'])} 个优化点",
            "suggestions": improvement['high_value_optimizations
""")

        if user_decision == "是，纳入当前任务":
            goto("计划设计")  # 新一轮优化迭代
        elif user_decision == "否，记录为技术债":
            record_tech_debt(improvement['high_value_optimizations'])
            goto("全部完成")
        else:
            goto("全部完成")
```

</verification_quality_gate>

---

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
