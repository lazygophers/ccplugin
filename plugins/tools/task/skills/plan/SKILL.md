---
description: 任务分解规划。基于 align.json 将任务拆解为原子子任务 DAG，自我验证后写入 task.json
memory: project
color: purple
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: high
context: fork
agent: task:plan
---

# Plan Skill

基于对齐结果，将任务分解为可执行的子任务。**自我验证、自动修复、迭代优化，无需用户确认。**

## 执行流程

### 步骤 1：读取输入

读取以下文件获取规划所需的全部上下文：

- `.lazygophers/tasks/{task_id}/align.json` — 任务目标、验收标准、边界、锁定风格
- `.lazygophers/tasks/{task_id}/context.json` — 相关模块、文件、代码风格、工具链

从 align.json 中提取 `code_style_follow` 作为锁定风格，所有子任务必须遵循。

### 步骤 2：检索历史经验

如果 `.lazygophers/lessons.json` 存在，读取并筛选与当前任务相关的经验：

- 同类任务类型（task_type 匹配）
- 涉及相同模块（modules 路径前缀匹配）
- 关键词有交集（keywords 重叠）

筛选出的经验作为规划参考约束（非硬规则），避免重蹈覆辙。

### 步骤 3：任务分解

基于 align.json 的目标和验收标准，将任务拆解为原子子任务。如果任务类型匹配已知模板（见下方"任务模板"），优先以模板为拆分起点。

每个子任务必须包含：id、description、goal、acceptance_criteria、files、dependencies、agent、estimated_complexity。

### 步骤 4：自我验证与修复（最多 10 次迭代）

对生成的子任务列表进行验证，验证规则见 [validation.md](validation.md)。

每次迭代：
1. 检查原子性（文件数 ≤ 5、标准数 ≤ 5、复杂度）
2. 检查文件集合是否有交集（不同子任务不能修改同一文件）
3. 检查 DAG 无循环依赖
4. 检查并行任务数 ≤ 2
5. 检查验收标准是否包含可验证的动词/量化指标
6. 检查是否包含不可重试的副作用操作

发现问题时自动修复（拆分过大任务、合并文件冲突、消除循环依赖等），然后重新验证。

如果 10 次迭代后仍未通过，返回 `status: "上下文缺失"` 并说明原因。

### 步骤 5：构建执行计划并写入

验证通过后，构建完整执行计划并写入 `.lazygophers/tasks/{task_id}/task.json`：

```json
{
  "subtasks": [...],
  "code_style": {...},
  "metadata": {
    "total_tasks": 3,
    "generated_at": "ISO8601"
  }
}
```

输出 `[flow·{task_id}·plan] 任务规划已完成，共 N 个子任务`。

## 子任务结构

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

| 恢复策略 | 含义 | worker 行为 |
|---------|------|------------|
| `retry_with_fix` | 注入失败原因后重试 1 次 | 将错误信息加入 prompt 重新执行 |
| `add_dependency_first` | 缺少前置依赖 | 标记当前任务 blocked，等待依赖补充 |
| `simplify_goal` | 目标过于复杂 | 用简化版 goal 重试 |
| `skip` | 非关键任务可跳过 | 标记 skipped，不阻塞后继 |

> 未定义 on_failure 或恢复失败的子任务，仍按原逻辑标记 failed 进入 adjust。

## 拆分原则

- **原子性**：每个子任务独立完成、不可再分
- **可验证性**：验收标准具体、可测试、可量化
- **依赖明确**：形成 DAG，无循环依赖
- **并行限制**：并行任务数量 ≤ 2
- **文件范围**：使用相对路径，不得越界
- **复杂度估算**：low / medium / high
- **单文件单任务**：每个任务只修改一个文件，避免并发冲突
- **幂等性设计**：任务可安全重复执行（支持失败重试）
- **风格遵守**：命名、文件组织、粒度符合项目风格；优先使用项目自定义 agent

## 验证规则

详细的验证函数定义和自动修复逻辑见 [validation.md](validation.md)。

## 任务模板

预定义的任务类型拆分模式见 [templates/](templates/) 目录：

| 文件 | 类型 | 适用场景 |
|------|------|---------|
| `bug-fix.json` | Bug 修复 | 定位→修复→验证 |
| `new-feature.json` | 新功能开发 | 设计→实现→测试 |
| `refactor.json` | 代码重构 | 分析→重构→验证行为不变 |
| `security-fix.json` | 安全修复 | 审计→修复→加固 |
| `performance.json` | 性能优化 | 分析→优化→基准验证 |
| `migration.json` | 迁移升级 | 评估→迁移→全量验证 |

## 检查清单

- [ ] align.json 和 context.json 已读取
- [ ] 历史经验已检索（如有）
- [ ] 子任务满足所有拆分原则
- [ ] 自我验证通过（≤10 次迭代）
- [ ] DAG 无循环依赖
- [ ] task.json 已写入
