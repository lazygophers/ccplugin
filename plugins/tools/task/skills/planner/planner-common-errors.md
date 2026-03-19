# Planner 常见错误

本文档列举使用 Planner 时的常见错误和解决方案。

## 1. 过度拆分

**错误示例**：简单配置修改拆分成 3 个任务

```json
// ❌ 错误
{
  "tasks": [
    {"id": "T1", "description": "创建配置文件"},
    {"id": "T2", "description": "写入配置项"},
    {"id": "T3", "description": "保存配置文件"}
  ]
}

// ✓ 正确：合并为 1 个原子任务
{
  "tasks": [
    {"id": "T1", "description": "创建并配置 API 配置文件"}
  ]
}
```

**原因**：过度拆分增加管理成本、降低执行效率、任务之间没有明确的依赖关系

**解决方案**：每个任务应该是一个完整的、可独立验证的工作单元。如果多个步骤必须一起完成，合并为一个任务。

---

## 2. 验收标准模糊

**错误示例**：无法量化的验收标准

```json
// ❌ 错误：无法量化
{
  "acceptance_criteria": [
    "代码质量好",
    "功能正常"
  ]
}

// ✓ 正确：可量化
{
  "acceptance_criteria": [
    "单元测试覆盖率 ≥ 90%",
    "所有 API 返回正确状态码",
    "Lint 检查 0 错误 0 警告"
  ]
}
```

**原因**：模糊的标准无法客观验证、难以判断任务是否真正完成、容易产生分歧和返工

**解决方案**：
- 使用数值指标（≥ 90%、< 200ms）
- 使用明确的验证方式（所有测试通过）
- 避免主观描述（"好"、"正常"）

---

## 3. 缺少中文注释

**错误示例**：Agent 和 Skills 没有中文说明

```json
// ❌ 错误
{
  "agent": "coder",
  "skills": ["golang:core"]
}

// ✓ 正确
{
  "agent": "coder（开发者）",
  "skills": ["golang:core（核心功能）"]
}
```

**原因**：降低可读性、用户不清楚角色职责、违反规范要求

**解决方案**：
- 所有 Agent 必须带中文注释
- 所有 Skills 必须带中文注释
- 使用括号格式：`name（中文说明）`

---

## 4. 循环依赖

**错误示例**：任务依赖形成循环

```json
// ❌ 错误：T1 → T2 → T3 → T1（循环！）
{
  "dependencies": {
    "T2": ["T1"],
    "T3": ["T2"],
    "T1": ["T3"]  // 循环依赖
  }
}

// ✓ 正确：DAG 结构
{
  "dependencies": {
    "T2": ["T1"],
    "T3": ["T2"]
  }
}
```

**原因**：循环依赖无法调度执行、违反 DAG（有向无环图）原则、导致死锁

**解决方案**：
- 使用拓扑排序验证依赖关系
- 确保所有依赖关系形成 DAG
- 打破循环依赖（重新设计任务）

---

## 5. 并行度超限

**错误示例**：超过 2 个任务并行

```json
// ❌ 错误：3 个任务并行
{
  "parallel_groups": [
    ["T1", "T2", "T3"]  // 超过限制
  ]
}

// ✓ 正确：最多 2 个并行
{
  "parallel_groups": [
    ["T1", "T2"],
    ["T3"]
  ]
}
```

**原因**：系统限制最多 2 个并行任务、超过限制会导致调度失败、资源管理复杂度增加

**解决方案**：
- 每个并行组最多包含 2 个任务
- 合理安排并行和串行执行
- 优先并行无依赖的任务

---

## 6. 结构化验收标准的常见错误

### 错误 1：缺少必需字段

```json
// ❌ 错误：缺少 priority 字段
{
  "acceptance_criteria": [
    {
      "id": "AC1",
      "type": "quantitative_threshold",
      "description": "测试覆盖率 ≥ 90%",
      "metric": "test_coverage",
      "operator": ">=",
      "threshold": 0.9
      // 缺少 priority 字段
    }
  ]
}

// ✓ 正确：包含所有必需字段
{
  "acceptance_criteria": [
    {
      "id": "AC1",
      "type": "quantitative_threshold",
      "description": "测试覆盖率 ≥ 90%",
      "metric": "test_coverage",
      "operator": ">=",
      "threshold": 0.9,
      "priority": "required"
    }
  ]
}
```

### 错误 2：使用了不支持的 operator

```json
// ❌ 错误：operator 值无效
{
  "type": "quantitative_threshold",
  "operator": "≥",  // 应使用 ">="
  "threshold": 0.9
}

// ✓ 正确：使用支持的 operator
{
  "type": "quantitative_threshold",
  "operator": ">=",  // 支持: >=, <=, >, <, ==
  "threshold": 0.9
}
```

### 错误 3：混淆容差的含义

```json
// ❌ 错误：误解 tolerance 为绝对值
{
  "type": "quantitative_threshold",
  "description": "测试覆盖率 ≥ 90%",
  "threshold": 0.9,
  "tolerance": 5  // 错误：应为相对值 0.05
}

// ✓ 正确：tolerance 为相对值
{
  "type": "quantitative_threshold",
  "description": "测试覆盖率 ≥ 90%",
  "threshold": 0.9,
  "unit": "percentage",
  "tolerance": 0.05  // 5% 的相对容差
}
```

**原因**：
- 缺少必需字段导致验证失败
- 不支持的 operator 值导致验证逻辑错误
- 误解 tolerance 含义导致验收标准不准确

**解决方案**：
- 使用结构化格式时，确保包含所有必需字段：`id`, `type`, `description`, `priority`
- 根据 `type` 包含特定字段：
  - `exact_match`: 需要 `verification_method`
  - `quantitative_threshold`: 需要 `metric`, `operator`, `threshold`
- 使用支持的 `operator` 值：`>=`, `<=`, `>`, `<`, `==`
- `tolerance` 为相对值（如 0.05 表示 5%），而非绝对值
- 向后兼容：不确定时可继续使用字符串格式
