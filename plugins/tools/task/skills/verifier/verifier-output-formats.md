# Verifier 输出格式

本文档包含 Verifier 的三种输出格式及详细示例。

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

### Loop 行为

正常退出，进入"全部迭代完成"流程。

### 字段说明

- `status`: 必须是 `"passed"`
- `report`: 简短报告（≤100字），列出所有完成的任务
- `verified_tasks`: 所有任务的验证结果，status 都是 `"verified"`
- `summary`: 统计摘要，`failed_tasks` 为 0

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

---

## 格式 3：验收失败（failed）

### 适用场景

验收标准未满足，存在功能缺陷或质量问题。

### 输出示例

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

### Loop 行为

不退出 Loop，进入失败调整阶段。

### 字段说明

- `status`: 必须是 `"failed"`
- `report`: 简短说明失败情况（≤100字）
- `verified_tasks`: 包含通过和失败的任务
  - 失败任务 `status` 为 `"failed"`
  - `criteria_passed < criteria_total`
- `failures`: 详细失败信息列表，每个失败包含：
  - `task_id`: 失败任务 ID
  - `criterion`: 未满足的验收标准
  - `actual`: 实际结果
  - `reason`: 失败原因和详细信息
- `summary`: 统计摘要，`failed_tasks > 0`

---

## 字段参考

### 通用字段

| 字段 | 类型 | 说明 | 必填 | 适用状态 |
|------|------|------|------|---------|
| `status` | string | 验收状态 | ✓ | 所有 |
| `report` | string | 简短报告（≤100字） | ✓ | 所有 |
| `verified_tasks` | array | 已验证任务列表 | ✓ | 所有 |
| `summary` | object | 验收统计摘要 | ✓ | 所有 |
| `suggestions` | array | 优化建议 | ✗ | suggestions |
| `failures` | array | 失败详情 | ✗ | failed |

### Verified Task 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务 ID | `"T1"` |
| `task_name` | string | 任务名称 | `"实现 JWT 工具函数"` |
| `status` | string | 验证状态 | `"verified"` / `"failed"` |
| `criteria_passed` | number | 通过的标准数 | `2` |
| `criteria_total` | number | 总标准数 | `2` |
| `notes` | string | 备注（可选） | `"代码复杂度略高"` |

### Summary 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `total_tasks` | number | 总任务数 | `3` |
| `completed_tasks` | number | 已完成任务数 | `3` |
| `failed_tasks` | number | 失败任务数 | `0` |
| `test_coverage` | number | 测试覆盖率（可选） | `92.0` |
| `regression_tests_passed` | boolean | 回归测试通过（可选） | `true` |

---

## 状态决策矩阵

| 条件 | 状态 | Loop 行为 |
|------|------|----------|
| 所有标准通过 + 无建议 | `passed` | 正常退出 |
| 所有标准通过 + 有建议 | `suggestions` | 询问用户 |
| 部分标准未通过 | `failed` | 进入失败调整 |

---

## 报告编写指南

### Passed 报告

**格式**：
```
所有任务已完成：T1（任务名）✓、T2（任务名）✓。测试覆盖率 X%，所有 CI 检查通过，无影响已有功能。
```

**要点**：
- 列出所有完成的任务（用 ✓ 标记）
- 提及关键指标（测试覆盖率、CI 状态）
- 确认无回归问题

### Suggestions 报告

**格式**：
```
任务已完成，所有验收标准满足。建议优化：[建议1]；[建议2]。
```

**要点**：
- 先确认所有标准通过
- 简要列出主要建议
- 使用分号分隔多个建议

### Failed 报告

**格式**：
```
验收失败：T1 [问题描述]，T2 [问题描述]。[关键指标不达标]。
```

**要点**：
- 列出失败的任务和问题
- 提及未达标的关键指标
- 保持简洁，详细信息在 failures 字段
