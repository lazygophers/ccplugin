---
description: 任务规划，分解任务并制定执行方案
memory: project
color: purple
model: opus
permissionMode: plan
background: false
user-invocable: false
effort: high
context: fork
agent: task:plan
---

# Plan Skill

## 执行流程

> 基于对齐结果，将任务分解为可执行的子任务
> **自我验证、自动修复、迭代优化，无需用户确认**

```python
# 读取输入
align = read_json(f".lazygophers/tasks/{task_id}/align.json")
context = read_json(f".lazygophers/tasks/{task_id}/context.json")
code_style = align["code_style_follow"]  # 锁定的项目风格

# 自我迭代循环
for i in range(10):
    # 阶段1：任务分解
    subtasks = decompose_task(align, code_style)
    
    # 阶段2：验证规范
    validation = validate_plan(subtasks, code_style)
    
    if validation["passed"]:
        break  # 通过则退出
    
    # 阶段3：自动修复
    subtasks = fix_issues(subtasks, validation["errors"], code_style)

# 验证失败处理
if not validation["passed"]:
    return {"status": "上下文缺失"}

# 阶段4：构建执行计划
plan = {
    "subtasks": list(subtasks.values()),
    "code_style": code_style,
    "metadata": {
        "total_tasks": len(subtasks),
        "generated_at": datetime.now().isoformat()
    }
}

# 阶段5：自我评估
assessment = self_assess(plan, code_style)

# 阶段6：验证 DAG 可用性
dag_valid = validate_dag(plan["subtasks"])
if not dag_valid["passed"]:
    return {"status": "上下文缺失", "reason": f"DAG 验证失败: {dag_valid['errors']}"}

# 写入结果
write_json(f".lazygophers/tasks/{task_id}/task.json", plan)

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
print(f"[flow·{task_id}·plan] 任务规划已完成，共 {len(plan['subtasks'])} 个子任务")

return {"status": "confirmed", "iterations": i + 1, "assessment": assessment}
```

## 任务拆分规范

### 子任务结构

```json
{
    "id": "AuthMiddleware",
    "description": "实现认证中间件",
    "goal": "验证请求头中的JWT令牌",
    "acceptance_criteria": [
        "无效令牌返回401",
        "有效令牌解析用户信息"
    ],
    "files": ["src/middleware/auth.py"],
    "dependencies": ["JWTUtils"],
    "agent": "general-purpose",
    "estimated_complexity": "medium"
}
```

### 拆分原则

**原子性**：每个子任务独立完成、不可再分
**可验证性**：验收标准具体、可测试、可量化
**依赖明确**：形成 DAG，无循环依赖
**并行限制**：并行任务数量 ≤ 2
**文件范围**：使用相对路径，不得越界
**复杂度估算**：low / medium / high
**单文件单任务**：每个任务只修改一个文件，禁止跨文件操作（避免冲突）
**幂等性设计**：任务可安全重复执行，多次执行产生相同结果（支持失败重试）

### 风格遵守

**命名约定**：任务ID、描述遵循项目命名风格
**文件组织**：文件路径符合项目目录结构
**粒度一致**：任务大小与项目现有任务粒度匹配
**Agent优先**：优先使用项目自定义 agent（`.claude/agents/`）

## 验证与修复

验证/修复/评估/DAG 验证的完整逻辑见 [validation.md](validation.md)。

核心流程：`validate_plan` → `fix_issues` → 重验（最多 10 次迭代），通过后 `self_assess` + `validate_dag`。

## 检查清单

### 上下文读取
- [ ] align.json 已读取
- [ ] context.json 已读取
- [ ] code_style_follow 已获取

### 自我迭代
- [ ] 最多10次迭代
- [ ] 验证 → 修复 → 重验循环已实现
- [ ] 迭代次数已记录

### 任务拆分
- [ ] 原子性已验证
- [ ] 可验证性已验证
- [ ] 依赖关系已验证
- [ ] 并行数量 ≤ 2
- [ ] 文件路径使用相对路径

### 风格遵守
- [ ] 命名符合项目风格
- [ ] 文件组织符合项目结构
- [ ] 粒度符合项目习惯
- [ ] 优先使用项目自定义 agent

### DAG 验证
- [ ] 依赖任务存在性已验证
- [ ] 无循环依赖已验证
- [ ] DAG 可用性已确认

### 输出
- [ ] task.json 已写入
- [ ] 包含 subtasks 数组
- [ ] 包含 code_style 字段
- [ ] 包含自我评估结果（assessment）
- [ ] status: "confirmed" | "上下文缺失"

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（plan）
