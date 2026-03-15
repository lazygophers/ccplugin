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

- ✓ Loop 命令步骤 5：结果验证阶段
- ✓ 检查所有任务的验收标准是否满足
- ✓ 验证交付物的完整性和质量
- ✓ 检查是否影响已有功能（回归测试）
- ✓ 判断是否达成迭代目标，决定是否终止 loop

## 核心原则

### 验收测试最佳实践

**可测试性（Testability）**：
- 每个标准必须客观可验证
- 无主观判断空间
- 可执行的测试证明

**可度量性（Measurability）**：
- 量化期望值，创建明确的通过/失败阈值
- 使用数值指标（≥ 90%、< 200ms）
- 避免模糊描述

**独立性（Independence）**：
- 每个标准可独立验证
- 无交叉依赖
- 简化测试流程

**关注结果（Outcome-Focused）**：
- 描述用户体验的结果，而非技术步骤
- 验证业务价值交付
- 确保功能正确性

**避免绝对词汇**：
- 避免使用"all"、"always"、"never"
- 使用具体的、可验证的标准

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
print(f"[MindFlow·{task_name}·步骤5/{iteration + 1}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")

# 输出统计信息
summary = verification_result["summary"]
print(f"任务统计：{summary['completed_tasks']}/{summary['total_tasks']} 完成")
if "test_coverage" in summary:
    print(f"测试覆盖率：{summary['test_coverage']}%")
```

## 输出格式

### 格式 1：完全通过（passed）

所有任务完成，所有验收标准满足，无质量问题。

```json
{
  "status": "passed",
  "report": "所有任务已完成：T1（JWT工具）✓、T2（认证中间件）✓、T3（测试覆盖）✓。测试覆盖率 92%，所有 CI 检查通过，无影响已有功能。",
  "verified_tasks": [
    {
      "task_id": "T1",
      "task_name": "实现 JWT 工具函数",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2
    },
    {
      "task_id": "T2",
      "task_name": "实现认证中间件",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2
    },
    {
      "task_id": "T3",
      "task_name": "编写认证测试",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2
    }
  ],
  "summary": {
    "total_tasks": 3,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "test_coverage": 92.0,
    "regression_tests_passed": true
  }
}
```

**Loop 行为**：正常退出，进入"全部迭代完成"流程。

---

### 格式 2：通过但有建议（suggestions）

任务已完成，验收标准满足，但有优化建议。

```json
{
  "status": "suggestions",
  "report": "任务已完成，所有验收标准满足。建议优化：代码复杂度略高（圈复杂度 15），建议后续重构；可添加更多边界测试。",
  "verified_tasks": [
    {
      "task_id": "T1",
      "task_name": "实现 JWT 工具函数",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2
    },
    {
      "task_id": "T2",
      "task_name": "实现认证中间件",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2,
      "notes": "代码复杂度略高"
    }
  ],
  "suggestions": [
    {
      "task_id": "T2",
      "category": "code_quality",
      "suggestion": "重构认证中间件，降低圈复杂度（当前 15，建议 < 10）",
      "priority": "medium"
    },
    {
      "task_id": "T3",
      "category": "test_coverage",
      "suggestion": "添加更多边界测试用例（如超长 token、特殊字符）",
      "priority": "low"
    }
  ],
  "summary": {
    "total_tasks": 3,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "test_coverage": 90.5
  }
}
```

**Loop 行为**：通过 `AskUserQuestion` 询问用户是否属于当前任务范围。
- 如果是 → 继续优化（新一轮迭代）
- 如果否 → Loop 完成

---

### 格式 3：验收失败（failed）

验收标准未满足，存在功能缺陷或质量问题。

```json
{
  "status": "failed",
  "report": "验收失败：T3 测试未通过（2/10 失败），测试覆盖率仅 75%（要求≥90%）。T2 存在 Lint 错误 3 个。",
  "verified_tasks": [
    {
      "task_id": "T1",
      "task_name": "实现 JWT 工具函数",
      "status": "verified",
      "criteria_passed": 2,
      "criteria_total": 2
    },
    {
      "task_id": "T2",
      "task_name": "实现认证中间件",
      "status": "failed",
      "criteria_passed": 1,
      "criteria_total": 2
    },
    {
      "task_id": "T3",
      "task_name": "编写认证测试",
      "status": "failed",
      "criteria_passed": 0,
      "criteria_total": 2
    }
  ],
  "failures": [
    {
      "task_id": "T2",
      "criterion": "Lint 检查 0 错误 0 警告",
      "actual": "3 错误, 0 警告",
      "reason": "变量未使用、导入未使用、格式问题"
    },
    {
      "task_id": "T3",
      "criterion": "所有测试用例通过",
      "actual": "8/10 通过, 2 失败",
      "reason": "test_login_timeout 和 test_invalid_token 失败"
    },
    {
      "task_id": "T3",
      "criterion": "测试覆盖率 ≥ 90%",
      "actual": "75%",
      "reason": "jwt.go 的错误处理分支未覆盖"
    }
  ],
  "summary": {
    "total_tasks": 3,
    "completed_tasks": 3,
    "failed_tasks": 2,
    "test_coverage": 75.0
  }
}
```

**Loop 行为**：不退出 Loop，进入步骤 6（失败调整）。

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

## 终止条件决策

Verifier agent 根据验证结果决定 Loop 的行为：

| 验收状态 | 条件 | 终止行为 |
|---------|------|---------|
| **passed** | 所有标准通过，无建议 | ✓ Loop 正常退出 |
| **suggestions** | 标准通过，有优化建议 | ? 询问用户是否继续 |
| **failed** | 标准未满足 | ✗ 进入失败调整步骤 |

## 验证检查清单

在调用 verifier agent 前，确保：

- [ ] 所有任务已执行完成
- [ ] 每个任务的验收标准已明确定义
- [ ] 验收标准可量化且可验证
- [ ] 避免使用绝对词汇（all, always, never）

在处理验证结果时，确保：

- [ ] 检查 `status` 字段的值
- [ ] 根据不同状态采取相应行为
- [ ] 记录验证报告和统计数据
- [ ] 对于 `suggestions` 状态，询问用户意见
- [ ] 对于 `failed` 状态，进入失败调整流程

## 集成示例

### Loop 命令中的使用

```python
# loop 命令的第五步：结果验证
def step_5_verification(task_description, iteration):
    """Loop 命令第五步：结果验证"""

    # 调用 verifier agent
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""执行结果验证：

任务目标：{task_description}
当前迭代：第 {iteration + 1} 轮

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务的验收标准
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
    )

    # 输出报告
    print(f"[MindFlow·{task_description}·步骤5/{iteration + 1}·{verification_result['status']}]")
    print(f"验收报告：{verification_result['report']}")

    # 根据状态决定行为
    if verification_result["status"] == "passed":
        # 完全通过，Loop 退出
        return "exit"

    elif verification_result["status"] == "suggestions":
        # 有建议，询问用户
        user_response = AskUserQuestion(
            f"{verification_result['report']}\n\n" +
            "建议：\n" +
            "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
            "\n\n这些优化是否属于当前任务范围？(是/否)"
        )

        if user_response.strip().lower() in ["是", "yes", "y"]:
            return "continue"  # 继续迭代
        else:
            return "exit"  # 完成

    elif verification_result["status"] == "failed":
        # 失败，进入调整步骤
        return "adjust"  # 进入步骤 6

    return "adjust"  # 默认进入调整
```

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
