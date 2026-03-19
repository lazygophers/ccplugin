    }
    return thresholds.get(iteration, 90)  # 第 4 轮及以后保持 90 分

# 2. 根据复杂度初始化配置
complexity_config = assess_task_complexity(user_task)

deep_iteration_config = {
    "mode": "deep",  # 深度迭代模式（默认）
    "min_iterations": complexity_config["min_iterations"],  # 最小迭代次数（1-3 轮）
    "max_iterations": None,  # 无最大轮数限制，持续迭代直到质量达标
    "complexity": complexity_config["complexity"],  # 复杂度等级
    "enable_research": True,
    "enable_quality_gate": True,
    "enable_continuous_improvement": True
}

# 质量阈值通过 get_quality_threshold(iteration) 函数动态获取

# 输出初始化信息
print(f"[MindFlow·{user_task}·初始化/1·进行中]")
print(f"✓ 任务复杂度：{complexity_config['complexity']}")
print(f"✓ 最小迭代次数：{complexity_config['min_iterations']} 轮")
print(f"✓ 质量阈值：递进式（60→75→85→90分，无上限）")
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
