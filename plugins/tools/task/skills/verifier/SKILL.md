---
agent: task:verifier
description: 结果验证规范 - 检查任务验收标准、验证完成情况、判断终止条件的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:verifier) - 结果验证规范

## 适用场景

当你需要系统性验证任务完成情况和质量标准时，使用此 skill：

- ✓ Loop 命令结果验证（Verification / Check）阶段
- ✓ 检查所有任务的验收标准是否满足
- ✓ 验证交付物的完整性和质量
- ✓ 检查是否影响已有功能（回归测试）
- ✓ 判断是否达成迭代目标，决定是否终止 loop

## 核心原则

### 验收测试最佳实践

- **可测试性**：客观可验证，无主观判断，可执行测试证明
- **可度量性**：量化期望值，使用数值指标（≥ 90%、< 200ms）
- **独立性**：每个标准可独立验证，无交叉依赖
- **关注结果**：验证用户体验和业务价值，而非技术步骤
- **避免绝对词汇**：不使用 "all"、"always"、"never"

详见：[验证检查清单](verifier-checklist.md)

## 执行流程

### 步骤 1：调用 verifier agent

```python
# 基础调用
verification_result = Agent(
    agent="task:verifier",
    prompt="""执行结果验证：

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务的验收标准
3. 检查回归测试，确保无影响已有功能
4. 生成验收报告（≤100字）
5. 决定验收状态（passed/suggestions/failed）

验收标准要求：
- 可测试：客观可验证
- 可度量：使用数值指标
- 独立：可独立验证
- 避免绝对词汇（all, always, never）
"""
)
```

### 步骤 2：处理验证结果

```python
# 检查状态
if verification_result["status"] not in ["passed", "suggestions", "failed"]:
    raise Exception("无效的验收状态")

# 根据状态决定下一步
if verification_result["status"] == "passed":
    # 所有验收标准通过，Loop 正常退出
    print(f"✓ {verification_result['report']}")
    exit_loop()  # 进入"全部迭代完成"流程

elif verification_result["status"] == "suggestions":
    # 通过但有优化建议，询问用户
    user_decision = AskUserQuestion(
        f"{verification_result['report']}\n\n建议：\n" +
        "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
        "\n\n这些优化是否属于当前任务范围？"
    )

    if user_decision.lower() in ["是", "yes", "y"]:
        continue_loop()  # 继续优化
    else:
        exit_loop()  # 完成

elif verification_result["status"] == "failed":
    # 验收失败，进入失败调整步骤
    print(f"✗ {verification_result['report']}")
    proceed_to_adjustment()  # 进入步骤 6
```

### 步骤 3：输出验收报告

```python
# 输出验收报告
print(f"[MindFlow·{task_name}·结果验证/{iteration + 1}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")

# 输出统计信息
summary = verification_result["summary"]
print(f"任务统计：{summary['completed_tasks']}/{summary['total_tasks']} 完成")
if "test_coverage" in summary:
    print(f"测试覆盖率：{summary['test_coverage']}%")
```

## 输出格式

Verifier 支持三种输出格式，对应不同的验收状态：

1. **passed** - 所有标准通过，Loop 正常退出
2. **suggestions** - 标准通过但有优化建议，询问用户是否继续
3. **failed** - 标准未满足，进入失败调整

详见：[输出格式文档](verifier-output-formats.md)

---

## 字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `status` | string | 验收状态：`passed` / `suggestions` / `failed` | ✓ |
| `report` | string | 简短报告（≤100字） | ✓ |
| `verified_tasks` | array | 已验证任务列表 | ✓ |
| `summary` | object | 验收统计摘要 | ✓ |
| `suggestions` | array | 优化建议（仅 suggestions 状态） | ✗ |
| `failures` | array | 失败详情（仅 failed 状态） | ✗ |

### Verified Task 对象字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务 ID | `"T1"` |
| `task_name` | string | 任务名称 | `"实现 JWT 工具函数"` |
| `status` | string | 验证状态：`verified` / `failed` | `"verified"` |
| `criteria_passed` | number | 通过的标准数 | `2` |
| `criteria_total` | number | 总标准数 | `2` |
| `notes` | string | 备注（可选） | `"代码复杂度略高"` |

## 详细文档

完整的输出格式、集成示例和检查清单详见以下文档：

- **[输出格式文档](verifier-output-formats.md)** - 三种输出格式的详细说明和示例
- **[集成示例](verifier-integration.md)** - Loop 集成、处理流程、高级用法
- **[验证检查清单](verifier-checklist.md)** - 验证前后检查清单、最佳实践

## 快速参考

### 终止条件决策

| 验收状态 | Loop 行为 |
|---------|----------|
| `passed` | 正常退出 |
| `suggestions` | 询问用户是否继续 |
| `failed` | 进入失败调整 |

### 验证要点

- 所有任务已完成
- 验收标准可量化
- 避免绝对词汇
- 检查回归测试

## 注意事项

- ✓ 始终使用 `Agent(agent="task:verifier", ...)` 调用
- ✓ 检查 `status` 字段确认验收状态
- ✓ 处理三种状态：passed / suggestions / failed
- ✓ 对于 suggestions，必须询问用户
- ✓ 对于 failed，进入失败调整流程
- ✓ 验证所有任务，不要遗漏
- ✗ 不要接受模糊的验收标准
- ✗ 不要忽略 suggestions 中的建议
- ✗ 不要跳过回归测试检查
- ✗ 不要修改 verifier 返回的 JSON 结构
