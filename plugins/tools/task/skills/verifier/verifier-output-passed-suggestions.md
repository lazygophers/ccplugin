# Verifier 输出格式 - Passed 和 Suggestions

本文档包含 Verifier 的 passed 和 suggestions 两种输出格式及详细示例。

## 格式 1：完全通过（passed）

### 适用场景

所有任务完成，所有验收标准满足，无质量问题。

### 输出示例

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
      "criteria_total": 2,
      "criteria_results": [
        {
          "criterion_id": "AC1",
          "status": "passed",
          "evaluation_method": "exact_match",
          "expected": "all tests passed",
          "actual": "all tests passed",
          "priority": "required"
        },
        {
          "criterion_id": "AC2",
          "status": "passed_with_tolerance",
          "evaluation_method": "quantitative_threshold",
          "expected": ">= 90%",
          "actual": "92%",
          "tolerance": 0.02,
          "margin": {"gap": 0.02, "relative_gap": 0.022},
          "priority": "required"
        }
      ]
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

### Loop 行为

正常退出，进入"全部迭代完成"流程。

### 字段说明

- `status`: 必须是 `"passed"`
- `report`: 简短报告（≤100字），列出所有完成的任务
- `verified_tasks`: 所有任务的验证结果，status 都是 `"verified"`
- `summary`: 统计摘要，`failed_tasks` 为 0

### 报告编写指南

**格式**：
```
所有任务已完成：T1（任务名）✓、T2（任务名）✓。测试覆盖率 X%，所有 CI 检查通过，无影响已有功能。
```

**要点**：
- 列出所有完成的任务（用 ✓ 标记）
- 提及关键指标（测试覆盖率、CI 状态）
- 确认无回归问题

---

## 格式 2：通过但有建议（suggestions）

### 适用场景

任务已完成，验收标准满足，但有优化建议。

### 输出示例

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

### Loop 行为

通过 `AskUserQuestion` 询问用户是否属于当前任务范围：
- **如果是** → 继续优化（新一轮迭代）
- **如果否** → Loop 完成

### 字段说明

- `status`: 必须是 `"suggestions"`
- `report`: 说明所有标准通过，并概述建议
- `verified_tasks`: 所有任务验证通过，可选 `notes` 字段
- `suggestions`: 建议列表，每个建议包含：
  - `task_id`: 相关任务 ID
  - `category`: 建议类别（code_quality / test_coverage / performance / security）
  - `suggestion`: 具体建议内容
  - `priority`: 优先级（low / medium / high）
- `summary`: 统计摘要，`failed_tasks` 为 0

### Suggestion 类别

| 类别 | 说明 | 示例 |
|------|------|------|
| `code_quality` | 代码质量改进 | 降低复杂度、重构代码 |
| `test_coverage` | 测试覆盖改进 | 添加边界测试、异常测试 |
| `performance` | 性能优化 | 优化查询、缓存优化 |
| `security` | 安全加固 | 输入验证、权限检查 |
| `documentation` | 文档完善 | 补充注释、API 文档 |

### 报告编写指南

**格式**：
```
任务已完成，所有验收标准满足。建议优化：[建议1]；[建议2]。
```

**要点**：
- 先确认所有标准通过
- 简要列出主要建议
- 使用分号分隔多个建议
