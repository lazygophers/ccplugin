# Verifier 输出格式 - Passed 和 Suggestions

<overview>

本文档定义了 Verifier 的两种成功状态输出格式。passed 表示所有任务完成且验收标准全部满足，Loop 收到后直接进入完成流程。suggestions 表示验收标准满足但发现可优化之处，Loop 会询问用户是否继续优化。两种格式共享相同的基础结构（status、report、verified_tasks、summary），suggestions 额外包含建议列表。

</overview>

<format_passed>

## 格式 1：完全通过（passed）

所有任务完成，所有验收标准满足，无质量问题时使用此格式。Loop 收到后正常退出，进入全部迭代完成流程。

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

字段要求：status 必须是 "passed"，report 为简短摘要（不超过100字）列出所有完成的任务，verified_tasks 中所有任务的 status 都是 "verified"，summary 中 failed_tasks 为 0。

报告编写格式：`所有任务已完成：T1（任务名）✓、T2（任务名）✓。测试覆盖率 X%，所有 CI 检查通过，无影响已有功能。`

</format_passed>

<format_suggestions>

## 格式 2：通过但有建议（suggestions）

任务已完成且验收标准满足，但发现可优化之处时使用此格式。Loop 通过 AskUserQuestion 询问用户建议是否属于当前任务范围——如果是则继续新一轮迭代，否则标记完成。

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

字段要求：status 必须是 "suggestions"，report 先确认所有标准通过再概述建议，verified_tasks 中所有任务验证通过（可选 notes 字段），suggestions 列表中每个建议包含 task_id、category、suggestion 和 priority，summary 中 failed_tasks 为 0。

### Suggestion 类别

| 类别 | 说明 | 示例 |
|------|------|------|
| code_quality | 代码质量改进 | 降低复杂度、重构代码 |
| test_coverage | 测试覆盖改进 | 添加边界测试、异常测试 |
| performance | 性能优化 | 优化查询、缓存优化 |
| security | 安全加固 | 输入验证、权限检查 |
| documentation | 文档完善 | 补充注释、API 文档 |

报告编写格式：`任务已完成，所有验收标准满足。建议优化：[建议1]；[建议2]。`

</format_suggestions>
