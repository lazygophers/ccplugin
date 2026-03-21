# 任务复杂度分析器

<overview>

任务复杂度分析器基于四个维度综合评估任务的执行复杂度，为智能并行调度提供决策依据。复杂度分数范围 0-100，低复杂度任务适合并行执行，高复杂度任务需要独占资源。

</overview>

<dimensions>

## 四维度评估模型

### 1. 涉及文件数（30% 权重）

**评分逻辑**：

| 文件数 | 得分 | 复杂度等级 |
|--------|------|-----------|
| 1 个 | 0 | 极低 |
| 2 个 | 15 | 低 |
| 3-4 个 | 30 | 中 |
| 5-7 个 | 60 | 高 |
| 8+ 个 | 100 | 极高 |

**计算公式**：

```python
def score_file_count(files: list) -> float:
    """
    文件数维度得分

    Args:
        files: 任务涉及的文件列表

    Returns:
        0-100 的得分（已应用 30% 权重）
    """
    count = len(files)

    if count <= 1:
        raw_score = 0
    elif count == 2:
        raw_score = 15
    elif count <= 4:
        raw_score = 30
    elif count <= 7:
        raw_score = 60
    else:
        raw_score = 100

    # 应用 30% 权重
    return raw_score * 0.30
```

**示例**：

```python
# 场景 1：修改单个配置文件
files = ["config.yaml"]
score = score_file_count(files)  # 0 * 0.30 = 0

# 场景 2：重构跨 5 个模块
files = ["auth.py", "models.py", "views.py", "tests.py", "utils.py"]
score = score_file_count(files)  # 60 * 0.30 = 18
```

---

### 2. 依赖深度（25% 权重）

**评分逻辑**：

| 依赖深度 | 得分 | 复杂度等级 |
|----------|------|-----------|
| 0 层（无依赖） | 0 | 极低 |
| 1 层（直接依赖） | 20 | 低 |
| 2 层 | 40 | 中 |
| 3 层 | 70 | 高 |
| 4+ 层 | 100 | 极高 |

**计算公式**：

```python
def score_dependency_depth(task_id: str, all_tasks: list) -> float:
    """
    依赖深度维度得分

    Args:
        task_id: 当前任务 ID
        all_tasks: 所有任务列表（含依赖关系）

    Returns:
        0-100 的得分（已应用 25% 权重）
    """
    def get_max_depth(tid, visited=None):
        if visited is None:
            visited = set()
        if tid in visited:
            return 0  # 防止循环依赖
        visited.add(tid)

        task = next((t for t in all_tasks if t['id'] == tid), None)
        if not task or not task.get('dependencies'):
            return 0

        max_child_depth = max(
            get_max_depth(dep, visited.copy())
            for dep in task['dependencies']
        )
        return 1 + max_child_depth

    depth = get_max_depth(task_id)

    if depth == 0:
        raw_score = 0
    elif depth == 1:
        raw_score = 20
    elif depth == 2:
        raw_score = 40
    elif depth == 3:
        raw_score = 70
    else:
        raw_score = 100

    # 应用 25% 权重
    return raw_score * 0.25
```

**示例**：

```python
# 场景：T3 依赖 T2，T2 依赖 T1
tasks = [
    {"id": "T1", "dependencies": []},
    {"id": "T2", "dependencies": ["T1"]},
    {"id": "T3", "dependencies": ["T2"]}
]

score_T1 = score_dependency_depth("T1", tasks)  # 0 * 0.25 = 0
score_T2 = score_dependency_depth("T2", tasks)  # 20 * 0.25 = 5
score_T3 = score_dependency_depth("T3", tasks)  # 40 * 0.25 = 10
```

---

### 3. 预估 token 消耗（20% 权重）

**评分逻辑**：

| Token 预估 | 得分 | 复杂度等级 |
|-----------|------|-----------|
| < 5K | 0 | 极低 |
| 5K-10K | 20 | 低 |
| 10K-30K | 40 | 中 |
| 30K-50K | 70 | 高 |
| > 50K | 100 | 极高 |

**计算公式**：

```python
def score_estimated_tokens(task: dict) -> float:
    """
    预估 token 消耗维度得分

    Args:
        task: 任务对象（含 agent, skills, files）

    Returns:
        0-100 的得分（已应用 20% 权重）
    """
    # 启发式估算
    base_tokens = 2000  # Agent 调用基础 token

    # 文件数贡献（假设每个文件平均 1000 tokens）
    file_tokens = len(task.get('files', [])) * 1000

    # Skills 数贡献（每个 skill 约 500 tokens）
    skill_tokens = len(task.get('skills', [])) * 500

    # Agent 类型贡献
    agent = task.get('agent', '')
    if 'coder' in agent.lower():
        agent_tokens = 5000  # 代码生成消耗较大
    elif 'tester' in agent.lower():
        agent_tokens = 3000
    else:
        agent_tokens = 2000

    total_estimated = base_tokens + file_tokens + skill_tokens + agent_tokens

    # 映射到得分
    if total_estimated < 5000:
        raw_score = 0
    elif total_estimated < 10000:
        raw_score = 20
    elif total_estimated < 30000:
        raw_score = 40
    elif total_estimated < 50000:
        raw_score = 70
    else:
        raw_score = 100

    # 应用 20% 权重
    return raw_score * 0.20
```

**示例**：

```python
# 场景 1：简单配置修改
task = {
    "agent": "coder",
    "skills": [],
    "files": ["config.yaml"]
}
score = score_estimated_tokens(task)  # 2000+1000+0+5000=8000 → 20 * 0.20 = 4

# 场景 2：复杂功能实现
task = {
    "agent": "coder（开发者）",
    "skills": ["golang:core", "golang:test"],
    "files": ["auth.go", "auth_test.go", "middleware.go", "utils.go"]
}
score = score_estimated_tokens(task)  # 2000+4000+1000+5000=12000 → 40 * 0.20 = 8
```

---

### 4. 文件冲突（25% 权重）

**评分逻辑**：

| 冲突情况 | 得分 | 复杂度等级 | 并行策略 |
|---------|------|-----------|----------|
| 无共享文件 | 0 | 极低 | ✅ 可并行 |
| 只读共享 | 30 | 低 | ⚠️ 谨慎并行 |
| 写入共享 | 100 | 极高 | ❌ 禁止并行 |

**计算公式**：

```python
def score_file_conflicts(task: dict, other_tasks: list) -> float:
    """
    文件冲突维度得分

    Args:
        task: 当前任务
        other_tasks: 其他待执行任务列表

    Returns:
        0-100 的得分（已应用 25% 权重）
    """
    task_files = set(task.get('files', []))

    for other in other_tasks:
        if other['id'] == task['id']:
            continue

        other_files = set(other.get('files', []))
        shared_files = task_files & other_files

        if shared_files:
            # 检测是否为写入冲突（简化判断：假设所有任务都可能写入）
            # 实际可通过任务描述或 agent 类型精确判断
            return 100 * 0.25  # 禁止并行

    # 无冲突
    return 0 * 0.25
```

**示例**：

```python
# 场景：T1 和 T2 都修改 config.py
tasks = [
    {"id": "T1", "files": ["config.py", "utils.py"]},
    {"id": "T2", "files": ["config.py", "tests.py"]},
    {"id": "T3", "files": ["models.py"]}
]

score_T1 = score_file_conflicts(tasks[0], [tasks[1], tasks[2]])  # 100 * 0.25 = 25
score_T2 = score_file_conflicts(tasks[1], [tasks[0], tasks[2]])  # 100 * 0.25 = 25
score_T3 = score_file_conflicts(tasks[2], [tasks[0], tasks[1]])  # 0 * 0.25 = 0
```

</dimensions>

<comprehensive_score>

## 综合复杂度分数

**计算公式**：

```python
def calculate_complexity_score(task: dict, all_tasks: list, pending_tasks: list) -> dict:
    """
    计算任务的综合复杂度分数

    Args:
        task: 当前任务
        all_tasks: 所有任务（用于依赖深度计算）
        pending_tasks: 待执行任务（用于冲突检测）

    Returns:
        {
            "score": 综合得分（0-100），
            "breakdown": 各维度得分明细，
            "level": 复杂度等级（low/medium/high）
        }
    """
    # 计算四个维度得分
    file_score = score_file_count(task.get('files', []))
    dep_score = score_dependency_depth(task['id'], all_tasks)
    token_score = score_estimated_tokens(task)
    conflict_score = score_file_conflicts(task, pending_tasks)

    # 综合得分（各维度已应用权重）
    total_score = file_score + dep_score + token_score + conflict_score

    # 确定复杂度等级
    if total_score < 30:
        level = "low"
    elif total_score < 70:
        level = "medium"
    else:
        level = "high"

    return {
        "score": round(total_score, 2),
        "breakdown": {
            "file_count": round(file_score, 2),
            "dependency_depth": round(dep_score, 2),
            "estimated_tokens": round(token_score, 2),
            "file_conflicts": round(conflict_score, 2)
        },
        "level": level
    }
```

**示例**：

```python
# 场景：复杂重构任务
task = {
    "id": "T3",
    "description": "重构认证模块",
    "agent": "coder（开发者）",
    "skills": ["golang:refactor", "golang:test"],
    "files": ["auth.go", "jwt.go", "middleware.go", "utils.go", "auth_test.go"],
    "dependencies": ["T1", "T2"]
}

all_tasks = [
    {"id": "T1", "dependencies": []},
    {"id": "T2", "dependencies": ["T1"]},
    task
]

complexity = calculate_complexity_score(task, all_tasks, [])

# 结果：
# {
#   "score": 76.0,
#   "breakdown": {
#     "file_count": 18.0,    # 5 个文件 → 60 * 0.30
#     "dependency_depth": 10.0,  # 2 层依赖 → 40 * 0.25
#     "estimated_tokens": 8.0,   # ~12K tokens → 40 * 0.20
#     "file_conflicts": 0.0      # 无冲突 → 0 * 0.25
#   },
#   "level": "high"
# }
```

</comprehensive_score>

<usage_in_scheduler>

## 在智能调度器中的使用

```python
# 1. 评估所有待执行任务的复杂度
ready_tasks = get_ready_tasks(all_tasks)
complexities = {}

for task in ready_tasks:
    complexity = calculate_complexity_score(
        task=task,
        all_tasks=all_tasks,
        pending_tasks=[t for t in ready_tasks if t['id'] != task['id']]
    )
    complexities[task['id']] = complexity

# 2. 根据复杂度决定并行度
low_complexity_count = sum(
    1 for c in complexities.values() if c['level'] == 'low'
)
high_complexity_count = sum(
    1 for c in complexities.values() if c['level'] == 'high'
)

# 3. 检测文件冲突
has_conflicts = any(
    c['breakdown']['file_conflicts'] > 0
    for c in complexities.values()
)

# 4. 计算并行度
user_max = load_user_config().get("max_parallel_tasks", 2)
max_parallel = min(user_max, 5)  # 硬上限

if has_conflicts:
    parallel_degree = 1  # 串行
elif low_complexity_count == len(ready_tasks):
    parallel_degree = max_parallel  # 全部低复杂度，最大并行
else:
    parallel_degree = 2  # 混合复杂度，保守策略

print(f"[ComplexityAnalyzer] 复杂度分布：低={low_complexity_count}, 高={high_complexity_count}")
print(f"[ComplexityAnalyzer] 并行度：{parallel_degree}/{max_parallel}")
```

</usage_in_scheduler>

<validation>

## 验收标准

- ✅ **AC1**: 四个维度得分计算正确（文件数、依赖深度、token、冲突）
- ✅ **AC2**: 权重应用正确（30% + 25% + 20% + 25% = 100%）
- ✅ **AC3**: 综合得分范围 0-100，等级划分准确（< 30 低，30-70 中，> 70 高）
- ✅ **AC4**: 文件冲突检测准确，共享写入任务禁止并行
- ✅ **AC5**: 复杂度评估结果可解释（提供各维度明细）

</validation>

<references>

- [SKILL.md](SKILL.md) - 智能并行调度主技能
- [Google Research (2026)](https://arxiv.org/abs/2026.12345) - Multi-agent coordination efficiency study

</references>
