---
agent: task:planner
description: 计划设计规范 - 收集项目信息、任务分解、依赖建模、agents/skills 分配的执行规范
model: opus
context: fork
user-invocable: false
---

# Skills(task:planner) - 计划设计规范

## 适用场景

当你需要为复杂任务设计执行计划时，使用此 skill：

- ✓ 需要深入分析项目结构和技术栈
- ✓ 需要将复杂任务分解为可执行的子任务
- ✓ 需要建立任务依赖关系和并行执行策略
- ✓ 需要为每个任务分配合适的 Agent 和 Skills
- ✓ Loop 命令的第一步（计划设计阶段）

## 核心原则

### MECE 分解原则
- **Mutually Exclusive（相互独立）**：子任务之间无文件冲突，可独立执行
- **Collectively Exhaustive（完全穷尽）**：覆盖所有必要工作，无遗漏

### 质量标准
- **可交付原子化**：每个任务必须产生可验证的交付物
- **可量化可验证**：每个任务必须有明确的、可量化的验收标准
- **依赖闭环**：任务之间的依赖关系必须形成有向无环图（DAG）

## 执行流程

### 步骤 1：调用 planner agent

```python
# 基础调用
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{task_description}

要求：
1. 分析项目结构（优先中等深度，必要时深入）
2. 收集：目标、依赖、现状、边界
3. 分解为原子子任务（遵循 MECE 原则）
4. 建立依赖关系（DAG，无循环）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化的验收标准
7. 返回简短报告（≤200字）

如果功能已存在且满足需求，返回空 tasks 数组。
"""
)
```

### 步骤 2：处理 planner 结果

```python
# 检查状态
if planner_result["status"] != "completed":
    raise Exception("计划设计失败")

# 检查是否有疑问需要用户确认
if "questions" in planner_result and planner_result["questions"]:
    # 通过 AskUserQuestion 向用户确认
    user_response = AskUserQuestion(planner_result["questions"][0])
    # 重新调用 planner，补充用户回答
    planner_result = Agent(
        agent="task:planner",
        prompt=f"补充信息：{user_response}\n继续设计计划..."
    )

# 特殊情况：无需执行任务
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"✓ {planner_result['report']}")
    return  # 直接结束，无需执行

# 验证计划质量
validate_plan(planner_result)
```

### 步骤 3：验证计划质量

```python
def validate_plan(plan):
    """验证计划的合理性"""

    # 检查依赖关系
    if has_circular_dependency(plan["dependencies"]):
        raise Exception("发现循环依赖，请修正计划")

    # 检查并行度
    for group in plan["parallel_groups"]:
        if len(group) > 2:
            raise Exception(f"并行任务数超过限制（最多2个）：{group}")

    # 检查 Agent/Skills 格式
    for task in plan["tasks"]:
        if "（" not in task["agent"]:
            raise Exception(f"Agent 缺少中文注释：{task['agent']}")
        for skill in task["skills"]:
            if "（" not in skill:
                raise Exception(f"Skill 缺少中文注释：{skill}")

    # 检查验收标准
    for task in plan["tasks"]:
        if not task["acceptance_criteria"]:
            raise Exception(f"任务 {task['id']} 缺少验收标准")
```

### 步骤 4：输出执行计划

```python
# 输出计划摘要
print(f"[MindFlow·{task_name}·步骤1/1·completed]")
print(f"✓ 计划设计完成：{planner_result['report']}")
print(f"\n任务总数：{len(planner_result['tasks'])}")
print(f"并行组数：{len(planner_result['parallel_groups'])}")
print(f"迭代目标：{planner_result['iteration_goal']}")
```

## 输出格式

### 标准输出（有任务需执行）

```json
{
  "status": "completed",
  "report": "计划：3个子任务。T1：JWT 工具（coder）→ T2：认证中间件（coder）→ T3：测试覆盖（tester）。依赖：T2→T3。预计完成时间：2小时。",
  "tasks": [
    {
      "id": "T1",
      "description": "实现 JWT 工具函数",
      "agent": "coder（开发者）",
      "skills": ["golang:core（核心功能）"],
      "files": ["internal/auth/jwt.go"],
      "acceptance_criteria": [
        "生成和验证 Token 功能完整",
        "单元测试覆盖率 ≥ 90%"
      ],
      "dependencies": []
    },
    {
      "id": "T2",
      "description": "实现认证中间件",
      "agent": "coder（开发者）",
      "skills": ["golang:core（核心功能）"],
      "files": ["internal/auth/middleware.go"],
      "acceptance_criteria": [
        "中间件功能正确",
        "集成测试通过"
      ],
      "dependencies": ["T1"]
    },
    {
      "id": "T3",
      "description": "编写认证测试",
      "agent": "tester（测试员）",
      "skills": ["golang:testing（测试）"],
      "files": ["internal/auth/jwt_test.go"],
      "acceptance_criteria": [
        "所有测试用例通过",
        "测试覆盖率 ≥ 90%"
      ],
      "dependencies": ["T2"]
    }
  ],
  "dependencies": {
    "T2": ["T1"],
    "T3": ["T2"]
  },
  "parallel_groups": [
    ["T1"],
    ["T2"],
    ["T3"]
  ],
  "iteration_goal": "完成用户认证功能的实现和测试",
  "acceptance_criteria": [
    "所有子任务完成",
    "整体测试通过",
    "代码质量达标"
  ]
}
```

### 特殊输出（无需执行任务）

当 planner 发现以下情况时，返回空 tasks 数组：
- 功能已存在且满足需求
- 没有找到需要改动的地方
- 用户要求已被满足

```json
{
  "status": "completed",
  "report": "分析结果：用户认证功能已在 internal/auth 模块完整实现，包含 JWT 生成/验证、中间件和完整测试。无需额外开发。",
  "tasks": [],
  "dependencies": {},
  "parallel_groups": [],
  "iteration_goal": "确认现有实现满足需求",
  "acceptance_criteria": [
    "确认功能完整性",
    "验证测试覆盖率"
  ]
}
```

## 字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `status` | string | 执行状态：`completed` 或 `questions` | ✓ |
| `report` | string | 简短报告（≤200字） | ✓ |
| `tasks` | array | 任务列表（可为空数组） | ✓ |
| `dependencies` | object | 依赖关系映射 | ✓ |
| `parallel_groups` | array | 并行执行分组 | ✓ |
| `iteration_goal` | string | 迭代目标 | ✓ |
| `acceptance_criteria` | array | 整体验收标准 | ✓ |
| `questions` | array | 需要用户确认的问题（可选） | ✗ |

### Task 对象字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 任务唯一标识 | `"T1"` |
| `description` | string | 任务描述 | `"实现 JWT 工具函数"` |
| `agent` | string | 执行 Agent（含中文注释） | `"coder（开发者）"` |
| `skills` | array | 所需 Skills（含中文注释） | `["golang:core（核心功能）"]` |
| `files` | array | 涉及的文件 | `["internal/auth/jwt.go"]` |
| `acceptance_criteria` | array | 验收标准（可量化） | `["单元测试覆盖率 ≥ 90%"]` |
| `dependencies` | array | 前置任务 ID 列表 | `["T1"]` |

## Agent 选择指南

| Agent | 职责 | 适用场景 |
|-------|------|---------|
| `coder（开发者）` | 编写业务代码、实现功能 | 新功能开发、重构 |
| `tester（测试员）` | 编写测试、验证质量 | 单元测试、集成测试 |
| `devops（运维）` | 部署、CI/CD、基础设施 | 部署脚本、配置管理 |
| `writer（文档撰写者）` | 编写文档、README、API 文档 | 文档更新、API 说明 |
| `reviewer（审查员）` | 代码审查、质量检查 | Code Review、质量门禁 |

## Skills 选择指南

### 通用 Skills
- `python:core（核心功能）` - Python 核心开发
- `python:web（Web开发）` - FastAPI、Django 等
- `python:testing（测试）` - pytest、单元测试
- `golang:core（核心功能）` - Go 核心开发
- `golang:testing（测试）` - Go 测试框架
- `typescript:core（核心功能）` - TypeScript 开发
- `typescript:react（React开发）` - React 组件开发

### 专用 Skills
- `documentation（文档编写）` - 文档撰写
- `code-review（代码审查）` - 代码质量检查
- `requirements（需求分析）` - 需求分析

## 避坑指南

### ❌ 常见错误

1. **过度拆分**
   ```json
   // ❌ 错误：简单配置修改拆分成 3 个任务
   {"id": "T1", "description": "创建配置文件"},
   {"id": "T2", "description": "写入配置项"},
   {"id": "T3", "description": "保存配置文件"}

   // ✓ 正确：合并为 1 个原子任务
   {"id": "T1", "description": "创建并配置 API 配置文件"}
   ```

2. **验收标准模糊**
   ```json
   // ❌ 错误：无法量化
   "acceptance_criteria": ["代码质量好", "功能正常"]

   // ✓ 正确：可量化
   "acceptance_criteria": [
     "单元测试覆盖率 ≥ 90%",
     "所有 API 返回正确状态码"
   ]
   ```

3. **缺少中文注释**
   ```json
   // ❌ 错误
   "agent": "coder",
   "skills": ["golang:core"]

   // ✓ 正确
   "agent": "coder（开发者）",
   "skills": ["golang:core（核心功能）"]
   ```

4. **循环依赖**
   ```json
   // ❌ 错误：T1 → T2 → T3 → T1
   "dependencies": {
     "T2": ["T1"],
     "T3": ["T2"],
     "T1": ["T3"]  // 循环！
   }

   // ✓ 正确：DAG 结构
   "dependencies": {
     "T2": ["T1"],
     "T3": ["T2"]
   }
   ```

5. **并行度超限**
   ```json
   // ❌ 错误：3 个任务并行
   "parallel_groups": [["T1", "T2", "T3"]]

   // ✓ 正确：最多 2 个并行
   "parallel_groups": [["T1", "T2"], ["T3"]]
   ```

### ✓ 最佳实践

1. **优先使用中等深度探索**
   - 先快速了解项目结构
   - 发现信息不足时再深入

2. **发现功能已存在时及时报告**
   - 返回空 tasks 数组
   - 在 report 中说明原因

3. **一次只问一个问题**
   - 通过 `questions` 字段返回
   - 等用户回答后再继续

4. **验收标准必须可量化**
   - 使用数值指标（≥ 90%）
   - 使用明确的验证方式（所有测试通过）

5. **保持报告简洁**
   - report 字段 ≤ 200 字
   - 突出关键信息：任务数、依赖关系、预计时间

## 集成示例

### Loop 命令中的使用

```python
# loop 命令的第一步
def step_1_planning(task_description, iteration):
    """Loop 命令第一步：计划设计"""

    # 调用 planner agent
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计执行计划：

任务目标：{task_description}

当前迭代：第 {iteration + 1} 轮

要求：
1. 分析项目结构和技术栈
2. 收集目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
    )

    # 处理疑问
    if "questions" in planner_result and planner_result["questions"]:
        for question in planner_result["questions"]:
            answer = AskUserQuestion(question)
            # 补充信息后重新生成计划
            planner_result = Agent(
                agent="task:planner",
                prompt=f"补充信息：{answer}\n继续设计计划..."
            )

    # 验证计划
    validate_plan(planner_result)

    # 特殊情况：无需执行
    if not planner_result["tasks"]:
        print(f"[MindFlow·{task_description}·{iteration + 1}/1·completed]")
        print(f"✓ {planner_result['report']}")
        return None  # 结束 loop

    # 输出计划
    print(f"[MindFlow·{task_description}·步骤1/{iteration + 1}·completed]")
    print(f"✓ 计划设计完成：{planner_result['report']}")

    return planner_result
```

## 注意事项

- ✓ 始终使用 `Agent(agent="task:planner", ...)` 调用
- ✓ 检查 `status` 字段确认执行状态
- ✓ 处理 `questions` 字段中的用户确认请求
- ✓ 验证依赖关系无循环（使用拓扑排序）
- ✓ 验证并行度 ≤ 2
- ✓ 验证 Agent/Skills 带中文注释
- ✓ 处理空 tasks 数组的特殊情况
- ✗ 不要跳过计划验证步骤
- ✗ 不要忽略 planner 返回的问题
- ✗ 不要修改 planner 返回的 JSON 结构
