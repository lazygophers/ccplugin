---
description: 任务分解规划。基于 align.json 将任务拆解为原子子任务 DAG，自我验证后写入 task.json
memory: project
color: purple
model: opus
permissionMode: bypassPermissions
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

# === 阶段0：检索历史经验 ===
# 经验文件：.lazygophers/lessons.json（由 done skill 写入）
# 格式：数组，每个元素含 task_type、lessons、adjust_history
lessons_file = ".lazygophers/lessons.json"
if exists(lessons_file):
    all_lessons = read_json(lessons_file)
    task_type = align.get("task_type")
    modules = context.get("task_related", {}).get("modules", [])
    # 筛选相关经验：同类任务 或 涉及相同模块
    history = [l for l in all_lessons if l.get("task_type") == task_type or any(m in str(l) for m in modules)]
else:
    history = []
# history 用作规划的参考约束（非硬规则），避免重蹈覆辙

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
    "estimated_complexity": "medium",
    "on_failure": {
        "test-failure": "retry_with_fix",
        "missing-dependency": "add_dependency_first",
        "timeout": "simplify_goal"
    }
}
```

### on_failure 恢复路径

每个子任务可预定义失败时的恢复策略，exec worker 失败时先查此表，能自行恢复就不走 adjust 循环：

| 恢复策略 | 含义 | worker 行为 |
|---------|------|------------|
| `retry_with_fix` | 注入失败原因后重试 1 次 | 将错误信息加入 prompt 重新执行 |
| `add_dependency_first` | 缺少前置依赖 | 标记当前任务 blocked，等待依赖补充 |
| `simplify_goal` | 目标过于复杂 | 用简化版 goal 重试 |
| `skip` | 非关键任务可跳过 | 标记 skipped，不阻塞后继 |

> 未定义 on_failure 或恢复失败的子任务，仍按原逻辑标记 failed 进入 adjust。

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

## 任务模板

预定义的任务类型拆分模式见 [templates/](templates/) 目录，每种类型一个独立文件：

| 文件 | 类型 | 适用场景 |
|------|------|---------|
| `bug-fix.json` | Bug 修复 | 定位→修复→验证 |
| `new-feature.json` | 新功能开发 | 设计→实现→测试 |
| `refactor.json` | 代码重构 | 分析→重构→验证行为不变 |
| `security-fix.json` | 安全修复 | 审计→修复→加固 |
| `performance.json` | 性能优化 | 分析→优化→基准验证 |
| `migration.json` | 迁移升级 | 评估→迁移→全量验证 |

当任务匹配已知模板时，优先使用模板作为拆分起点。

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

