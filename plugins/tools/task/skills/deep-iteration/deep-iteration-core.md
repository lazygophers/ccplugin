---
description: 深度迭代规范 - 多次迭代深度研究，确保结果完全符合预期的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:deep-iteration) - 深度迭代核心机制

<overview>

深度迭代的核心目标是通过多次迭代深度研究，找到最优解决方案，使最终结果完全符合预期。本文档定义了深度迭代的原理、核心机制和参数。详细的执行流程和代码示例参考 [深度迭代详细说明](deep-iteration-details.md)。

</overview>

<comparison>

## 与普通迭代的区别

深度迭代在五个维度上超越普通迭代。普通迭代以完成功能为目标，失败时简单重试，验收标准仅关注功能通过，研究停留在浅层，功能完成即终止。深度迭代以完美满足预期为目标，采用质量递进提升策略，验收标准涵盖质量达标和最佳实践，通过论文、案例、专家实践进行深度研究，直到用户完全满意才终止。

| 维度 | 普通迭代 | 深度迭代 |
|------|---------|---------|
| 目标 | 完成功能 | 完美满足预期 |
| 迭代策略 | 失败重试 | 质量递进提升 |
| 验收标准 | 功能通过 | 质量达标 + 最佳实践 |
| 研究深度 | 浅层 | 深度研究（论文、案例、专家实践） |
| 迭代终止 | 功能完成 | 用户完全满意 |

</comparison>

<core_mechanisms>

## 核心机制

### 1. 深度理解（Deep Understanding）

在正式规划前，调用 deepresearch agent 进行深度研究：查找最新论文、技术博客和开源项目，对比 3-5 种解决方案的优劣，确定最佳实践和质量标准，将研究结果融入计划设计。这样做是为了避免基于过时或次优方案开发，减少后续返工。

### 2. 质量递进（Quality Progression）

每轮迭代的质量阈值递增，确保持续提升而非原地踏步。质量门控在每轮验证时检查分数是否达标，不达标则继续迭代。

| 迭代轮次 | 质量等级 | 阈值 | 验收标准 |
|---------|---------|------|---------|
| 第 1 轮 | Foundation（基础） | 60分 | 功能实现，测试通过 |
| 第 2 轮 | Enhancement（增强） | 75分 | 边界处理，错误处理，性能优化 |
| 第 3 轮 | Refinement（精化） | 85分 | 代码质量，可维护性，文档完善 |
| 第 4+ 轮 | Excellence（卓越） | 90分 | 最佳实践，可扩展性，安全性 |

### 3. 深度分析（Deep Analysis）

失败时不仅找表面原因，更要找根本原因和最优解。使用 5 Why 法进行根本原因分析，查找类似问题的解决案例，对比多种修复方案，提供最优修复策略，应用推荐方案并添加预防措施。

### 4. 持续改进（Continuous Improvement）

即使通过验收也追求卓越：对比业界最佳实践，识别可优化点（性能、可维护性、扩展性、安全性），评估优化价值与成本，自动触发新一轮迭代进行优化。

</core_mechanisms>

<triggers_and_termination>

## 深度研究触发条件

满足任一条件时触发深度研究：

| 触发条件 | 说明 |
|---------|------|
| 第 1 轮迭代 | 了解最佳方案 |
| 复杂任务 | planner 识别为高复杂度 |
| 失败 2 次 | 深度分析根本原因 |
| 质量不达标 | 分数 < 阈值 - 10 |
| 用户要求 | 明确要求深入研究 |

## 深度终止条件

必须同时满足所有条件才终止：所有验收标准通过、质量分数达到当前迭代的阈值、遵循行业最佳实践（无明显偏离）、用户明确确认完全符合预期、达到最小迭代次数（根据任务复杂度动态确定）。

## 复杂度评估

任务复杂度基于四个维度评分（总分 100）：文件变更数（0-25分，1-2文件=5分，3-5=15分，6+=25分）、技术栈新颖度（0-25分，熟悉=5分，新技术=15分，未知=25分）、任务类型（0-25分，bug修复=5分，新功能=15分，架构重构=25分）、质量要求（0-25分，基础=5分，生产级=15分，企业级=25分）。

复杂度分级决定最小迭代次数（无最大轮数限制）：Simple（0-30分）最小 1 轮，Moderate（31-60分）最小 2 轮，Complex（61-100分）最小 3 轮。

```python
def assess_task_complexity(user_task: str) -> dict:
    score = 0

    if any(keyword in user_task for keyword in ["重构", "架构", "迁移", "升级"]):
        score += 25
    elif any(keyword in user_task for keyword in ["新增", "添加", "实现", "开发"]):
        score += 15
    else:
        score += 5

    score += 15 + 15  # 默认中等质量要求和技术熟悉度

    if score <= 30:
        return {"complexity": "simple", "min_iterations": 1}
    elif score <= 60:
        return {"complexity": "moderate", "min_iterations": 2}
    else:
        return {"complexity": "complex", "min_iterations": 3}

def get_quality_threshold(iteration: int) -> int:
    thresholds = {1: 60, 2: 75, 3: 85}
    return thresholds.get(iteration, 90)  # 第 4 轮及以后保持 90 分
```

</triggers_and_termination>
