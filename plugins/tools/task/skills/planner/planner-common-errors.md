# Planner 常见错误

本文档列举使用 Planner 时的常见错误和解决方案。每个错误都附带了错误示例和正确做法的对比。

<error_overdecomposition>

## 1. 过度拆分

简单配置修改不应该拆分成多个任务。每个任务应该是一个完整的、可独立验证的工作单元。如果多个步骤必须一起完成才有意义，就合并为一个任务。过度拆分增加管理成本、降低执行效率，而且任务之间没有明确的依赖关系。

```json
// 错误：简单操作拆成 3 个任务
{
  "tasks": [
    {"id": "T1", "description": "创建配置文件"},
    {"id": "T2", "description": "写入配置项"},
    {"id": "T3", "description": "保存配置文件"}
  ]
}

// 正确：合并为 1 个原子任务
{
  "tasks": [
    {"id": "T1", "description": "创建并配置 API 配置文件"}
  ]
}
```

</error_overdecomposition>

<error_vague_criteria>

## 2. 验收标准模糊

模糊的标准无法客观验证，难以判断任务是否真正完成，容易产生分歧和返工。应使用数值指标（>= 90%、< 200ms）和明确的验证方式（所有测试通过），避免主观描述（"好"、"正常"）。

```json
// 错误：无法量化
{
  "acceptance_criteria": ["代码质量好", "功能正常"]
}

// 正确：可量化
{
  "acceptance_criteria": [
    "单元测试覆盖率 ≥ 90%",
    "所有 API 返回正确状态码",
    "Lint 检查 0 错误 0 警告"
  ]
}
```

</error_vague_criteria>

<error_missing_annotation>

## 3. 缺少中文注释

所有 Agent 和 Skills 必须带中文注释，使用括号格式 `name（中文说明）`。缺少注释会降低可读性，用户无法清楚了解角色职责。

```json
// 错误
{"agent": "coder", "skills": ["golang:core"]}

// 正确
{"agent": "coder（开发者）", "skills": ["golang:core（核心功能）"]}
```

</error_missing_annotation>

<error_circular_dependency>

## 4. 循环依赖

循环依赖无法调度执行，违反 DAG（有向无环图）原则，导致死锁。应使用拓扑排序验证依赖关系，发现循环时重新设计任务拆分。

```json
// 错误：T1 → T2 → T3 → T1（循环）
{
  "dependencies": {
    "T2": ["T1"],
    "T3": ["T2"],
    "T1": ["T3"]
  }
}

// 正确：DAG 结构
{
  "dependencies": {
    "T2": ["T1"],
    "T3": ["T2"]
  }
}
```

</error_circular_dependency>

<error_parallel_limit>

## 5. 并行度超限

系统限制最多 2 个并行任务，超过限制会导致调度失败和资源管理复杂度增加。每个并行组最多包含 2 个任务，优先并行无依赖的任务。

```json
// 错误：3 个任务并行
{"parallel_groups": [["T1", "T2", "T3"]]}

// 正确：最多 2 个并行
{"parallel_groups": [["T1", "T2"], ["T3"]]}
```

</error_parallel_limit>

<error_structured_criteria>

## 6. 结构化验收标准错误

缺少必需字段会导致验证失败。使用结构化格式时，必须包含 `id`、`type`、`description`、`priority`。根据 `type` 还需要特定字段：`exact_match` 需要 `verification_method`，`quantitative_threshold` 需要 `metric`、`operator`、`threshold`。

```json
// 错误：缺少 priority 字段
{
  "id": "AC1",
  "type": "quantitative_threshold",
  "description": "测试覆盖率 ≥ 90%",
  "metric": "test_coverage",
  "operator": ">=",
  "threshold": 0.9
}

// 正确：包含所有必需字段
{
  "id": "AC1",
  "type": "quantitative_threshold",
  "description": "测试覆盖率 ≥ 90%",
  "metric": "test_coverage",
  "operator": ">=",
  "threshold": 0.9,
  "priority": "required"
}
```

使用不支持的 operator 值也是常见错误。支持的值为 `>=`、`<=`、`>`、`<`、`==`（注意不是 Unicode 符号 `≥`）。

tolerance 必须是相对值而非绝对值。例如 `tolerance: 0.05` 表示 5% 的相对容差，而不是绝对值 5。不确定时可继续使用字符串格式。

</error_structured_criteria>

<error_missing_agent_skills>

## 7. 缺少 Agent 或 Skills 分配

### 规则

当 tasks 数组不为空时，每个任务必须明确指定 agent 和至少一个 skill。

### 错误示例

**示例 1：Agent 为空**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "",  // ❌ 不能为空
    "skills": ["python:web（Web开发）"]
  }]
}
```

**示例 2：Skills 为空数组**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "coder（开发者）",
    "skills": []  // ❌ 至少需要一个
  }]
}
```

**示例 3：缺少中文注释**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "coder",  // ❌ 缺少（中文注释）
    "skills": ["golang:core"]  // ❌ 缺少（中文注释）
  }]
}
```

### 正确示例

**示例 1：通用 agent**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "coder（开发者）",  // ✓ 通用开发者
    "skills": ["documentation（文档编写）"]  // ✓ 通用技能
  }]
}
```

**示例 2：专业 agent（带来源）**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "golang:dev（Go开发专家）@golang",  // ✓ 明确来源
    "skills": [
      "golang:core（核心功能）@golang",
      "golang:testing（测试）@golang"
    ]
  }]
}
```

**示例 3：项目自定义 agent**
```json
{
  "tasks": [{
    "id": "T1",
    "agent": "ml-engineer（机器学习工程师）",  // ✓ 项目自定义
    "skills": ["python:ml（机器学习）@python"]
  }]
}
```

### 特殊情况：功能已存在

当功能已存在时，返回空 tasks 数组，此时无需 agent/skills：

```json
{
  "status": "completed",
  "report": "功能已存在，无需开发。",
  "tasks": [],  // ✓ 空数组时不需要 agent/skills
  "dependencies": {},
  "parallel_groups": []
}
```

### Agent/Skills 来源灵活性

Agent 和 Skills 可来自：
- **Task 插件**：`task:planner`、`task:explorer-*`
- **其他插件**：`golang:dev`、`python:test`
- **项目自定义**：`.claude/agents/` 中定义的 agent
- **通用 agent**：`coder（开发者）`、`tester（测试员）`

**Loop 内部调用**需明确来源：
```json
{
  "id": "T0",
  "agent": "task:planner",  // ✓ 明确来源
  "skills": ["task:planning（计划设计）@task"]
}
```

**任务执行**可灵活选择：
```json
{
  "id": "T1",
  "agent": "coder（开发者）",  // ✓ 系统自动查找
  "skills": ["golang:core（核心功能）@golang"]  // ✓ 或明确来源
}
```

</error_missing_agent_skills>
