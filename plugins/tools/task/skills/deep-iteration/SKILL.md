---
description: 深度迭代规范 - 多次迭代深度研究，确保结果完全符合预期的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:deep-iteration) - 深度迭代规范

## 核心目标

确保任务通过**多次迭代深度研究**，找到最优解决方案，最终结果**完全符合预期**。

**重要**：详细的执行流程、代码示例请参考 [深度迭代详细说明](deep-iteration-details.md)。本文档仅包含核心原则和快速参考。

## 与普通迭代的区别

| 维度 | 普通迭代 | 深度迭代 |
|------|---------|---------|
| 目标 | 完成功能 | **完美满足预期** |
| 迭代策略 | 失败重试 | **质量递进提升** |
| 验收标准 | 功能通过 | **质量达标 + 最佳实践** |
| 研究深度 | 浅层 | **深度研究（论文、案例、专家实践）** |
| 迭代终止 | 功能完成 | **用户完全满意** |

## 核心机制

### 1. 深度理解（Deep Understanding）

- 调用 deepresearch agent 深度研究
- 查找最新论文、技术博客、开源项目
- 对比 3-5 种解决方案的优劣
- 确定最佳实践和质量标准
- 将研究结果融入计划设计

### 2. 质量递进（Quality Progression）

每轮迭代质量阈值递增：

| 迭代轮次 | 质量等级 | 阈值 | 验收标准 |
|---------|---------|------|---------|
| 第 1 轮 | Foundation（基础） | 60分 | 功能实现，测试通过 |
| 第 2 轮 | Enhancement（增强） | 75分 | 边界处理，错误处理，性能优化 |
| 第 3 轮 | Refinement（精化） | 85分 | 代码质量，可维护性，文档完善 |
| 第 4+ 轮 | Excellence（卓越） | 90分 | 最佳实践，可扩展性，安全性 |

**质量门控**：每轮验证时检查质量分数是否达标，不达标则继续迭代。

### 3. 深度分析（Deep Analysis）

失败时不仅找原因，更要找根本原因和最优解：

- 根本原因分析（5 Why 法）
- 查找类似问题的解决案例
- 对比多种修复方案
- 提供最优修复策略
- 应用推荐方案并添加预防措施

### 4. 持续改进（Continuous Improvement）

即使通过验收，也要追求卓越：

- 对比业界最佳实践
- 识别可优化点（性能、可维护性、扩展性、安全性）
- 评估优化价值 vs 成本
- 询问用户是否继续优化或记录为技术债

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

满足**所有**条件时终止：

1. ✓ 所有验收标准通过
2. ✓ 质量分数 ≥ 当前迭代的阈值
3. ✓ 遵循行业最佳实践（无明显偏离）
4. ✓ 用户明确确认"完全符合预期"
5. ✓ 达到最小迭代次数（根据任务复杂度动态确定）

## 集成到 Loop

### 初始化阶段

```python
# 1. 评估任务复杂度（动态确定最小迭代次数）
def assess_task_complexity(user_task: str) -> dict:
    """
    评估任务复杂度，返回迭代配置

    评分维度（总分 100）：
    - 文件变更数（0-25分）：1-2文件=5分，3-5=15分，6+=25分
    - 技术栈新颖度（0-25分）：熟悉=5分，新技术=15分，未知=25分
    - 任务类型（0-25分）：bug修复=5分，新功能=15分，架构重构=25分
    - 质量要求（0-25分）：基础=5分，生产级=15分，企业级=25分

    复杂度分级：
    - Simple（0-30分）：1 轮迭代，阈值 {1: 70}
    - Moderate（31-60分）：2 轮迭代，阈值 {1: 60, 2: 80}
    - Complex（61-80分）：3 轮迭代，阈值 {1: 60, 2: 75, 3: 85}
    - VeryComplex（81-100分）：4 轮迭代，阈值 {1: 60, 2: 70, 3: 80, 4: 90}
    """
    # 示例评估逻辑（planner 在计划设计时可以提供复杂度评分）
    score = 0

    # 从任务描述中推断复杂度（简化版）
    if any(keyword in user_task for keyword in ["重构", "架构", "迁移", "升级"]):
        score += 25  # 架构重构类任务
    elif any(keyword in user_task for keyword in ["新增", "添加", "实现", "开发"]):
        score += 15  # 新功能开发
    else:
        score += 5  # bug修复或简单任务

    # 默认假设中等质量要求和技术熟悉度
    score += 15 + 15  # 质量要求 + 技术栈

    # 根据评分确定配置
    if score <= 30:
        return {
            "complexity": "simple",
            "min_iterations": 1,
            "quality_threshold": {1: 70}
        }
    elif score <= 60:
        return {
            "complexity": "moderate",
            "min_iterations": 2,
            "quality_threshold": {1: 60, 2: 80}
        }
    elif score <= 80:
        return {
            "complexity": "complex",
            "min_iterations": 3,
            "quality_threshold": {1: 60, 2: 75, 3: 85}
        }
    else:
        return {
            "complexity": "very_complex",
            "min_iterations": 4,
            "quality_threshold": {1: 60, 2: 70, 3: 80, 4: 90}
        }

# 2. 根据复杂度初始化配置
complexity_config = assess_task_complexity(user_task)

deep_iteration_config = {
    "mode": "deep",  # 深度迭代模式（默认）
    "min_iterations": complexity_config["min_iterations"],  # 动态确定
    "quality_threshold": complexity_config["quality_threshold"],  # 动态阈值
    "complexity": complexity_config["complexity"],  # 复杂度等级
    "enable_research": True,
    "enable_quality_gate": True,
    "enable_continuous_improvement": True
}

# 输出初始化信息
print(f"[MindFlow·{user_task}·初始化/1·进行中]")
print(f"✓ 任务复杂度：{complexity_config['complexity']}")
print(f"✓ 最小迭代次数：{complexity_config['min_iterations']} 轮")
print(f"✓ 质量阈值：{complexity_config['quality_threshold']}")
```

### 深度研究阶段（1.5）

在"计划设计"前插入，触发条件满足时执行。

详见：[loop-deep-iteration.md](../loop/loop-deep-iteration.md#深度研究阶段15)

### 计划设计阶段

融合深度研究结果：
- 研究发现 → planner prompt
- 推荐方案 → 采用优先
- 质量标准 → 验收标准

详见：[loop-deep-iteration.md](../loop/loop-deep-iteration.md#计划设计阶段融合研究结果)

### 结果验证阶段

增强验证：
- **质量门控**：检查质量分数是否达标
- **最小迭代**：检查是否达到最小迭代次数（根据复杂度动态确定）
- **持续改进**：识别高价值优化点

详见：[loop-deep-iteration.md](../loop/loop-deep-iteration.md#结果验证阶段质量门控--持续改进)

### 失败调整阶段

深度分析：
- **失败 2 次触发**：深度分析根本原因
- **融合分析结果**：应用推荐修复方案

详见：[loop-deep-iteration.md](../loop/loop-deep-iteration.md#失败调整阶段深度失败分析)

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
  "final_quality_score": 87,
  "quality_threshold_met": true,
  "next_action": "continuous_improvement"
}
```

### 最终报告

```
[MindFlow·任务内容·completed·深度迭代报告]

✓ 总迭代：3 轮
✓ 质量进展：68分 → 78分 → 87分
✓ 最终质量：87 分（阈值 85 分）
✓ 深度研究：2 次
✓ 用户指导：1 次
✓ 变更文件：8 个

结果：完全符合预期 ✓
```

## 最佳实践

### Do's ✓
- ✓ 第 1 轮就启用深度研究（了解最佳方案）
- ✓ 每轮迭代提高质量阈值（递进式改进）
- ✓ 失败时深度分析根本原因（而非表面错误）
- ✓ 通过后仍检查优化空间（追求卓越）
- ✓ 记录研究发现到 `.claude/memory/`（跨任务复用）

### Don'ts ✗
- ✗ 不要浅尝辄止（功能完成 ≠ 质量达标）
- ✗ 不要重复低质量迭代（每轮必须有质量提升）
- ✗ 不要跳过深度研究（避免走弯路）
- ✗ 不要忽视最佳实践（即使功能正确）
- ✗ 不要过早终止（至少 3 轮迭代）

## 预期收益

对比普通迭代：

| 维度 | 普通迭代 | 深度迭代 | 提升 |
|------|---------|---------|------|
| 最终质量 | 60-75 分 | 85-95 分 | +25-30 分 |
| 用户满意度 | 部分满足 | 完全符合预期 | 显著提升 |
| 返工率 | 30-50% | 10-20% | 减少 50-70% |
| 最佳实践 | 部分遵循 | 完全对齐 | 100% 对齐 |
| 知识积累 | 少量 | 系统化存储 | 可复用 |

## 详细文档

完整的执行流程、代码示例、决策树等详见：

- **[深度迭代详细说明](deep-iteration-details.md)** - 完整流程、代码示例、质量门控、持续改进
- **[Loop 深度迭代实现](../loop/loop-deep-iteration.md)** - Loop 集成的详细代码
- **[Loop Skill](../loop/SKILL.md)** - Loop 主文档（已集成深度迭代）

## 快速参考

### 质量阈值

| 轮次 | 阈值 | 等级 |
|------|------|------|
| 1 | 60 | Foundation |
| 2 | 75 | Enhancement |
| 3 | 85 | Refinement |
| 4+ | 90 | Excellence |

### 研究触发

- 第 1 轮：✓
- 失败 2 次：✓
- 质量不达标：✓
- 复杂任务：✓

### 终止条件

- 验收通过：✓
- 质量达标：✓
- 最佳实践：✓
- 用户满意：✓
- 最小迭代（3轮）：✓
