---
description: 记忆桥接 - 连接 MindFlow 任务系统与 Memory 插件，提供三层记忆存储和智能检索
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:memory-bridge) - 记忆桥接

<overview>

记忆桥接（Memory Bridge）作为 MindFlow Loop 与 Memory 插件之间的适配层，提供统一的记忆管理接口，隔离 Memory 插件版本差异，支持任务规划过程中的知识积累和经验复用。

核心价值：
- **版本隔离**：封装 Memory 插件 API 变化，保持 Loop 稳定性
- **三层记忆**：支持短期记忆（当前会话）、情节记忆（成功/失败经验）、语义记忆（项目知识）
- **智能检索**：基于任务相似度和失败模式匹配，推荐相关记忆
- **自动管理**：在 Loop 生命周期中自动加载和保存记忆

使用场景：
- **规划阶段**：加载相似任务的规划模式和架构决策
- **执行失败**：检索失败模式和恢复策略
- **任务完成**：保存成功经验和优化建议

</overview>

<memory-layers>

## 三层记忆架构

基于 [Agentic Context Engineering](https://arxiv.org/html/2602.20478v1) 中的记忆层次，Memory Bridge 实现三层记忆系统（详见 `memory-schema.md`）：

### 1. 短期记忆（Working Memory）

**URI 路径**：`task://sessions/{session_id}`

**生命周期**：当前会话，任务完成后归档

**存储内容**：
- 当前任务描述和上下文
- 正在执行的子任务状态
- 临时变量和中间结果
- 用户交互记录

**更新时机**：
- 会话开始时创建
- 每个阶段转换时更新
- 会话结束时归档

### 2. 情节记忆（Episodic Memory）

**URI 路径**：`workflow://task-episodes/{task_type}/{episode_id}`

**生命周期**：永久保存，定期归档低价值记录

**存储内容**：
- 任务类型和关键参数
- 执行计划和分解策略
- 成功/失败结果和原因
- 用时、迭代次数、停滞次数
- 使用的 Agent 和 Skills 组合

**更新时机**：
- 任务完成时保存成功情节
- 任务失败时保存失败情节和修复方案

### 3. 语义记忆（Semantic Memory）

**URI 路径**：`project://knowledge/{domain}/{topic}`

**生命周期**：永久保存，手动维护

**存储内容**：
- 项目架构模式和约定
- 代码风格和最佳实践
- 技术栈版本和依赖关系
- 常见问题和解决方案
- 架构决策记录（ADR）

**更新时机**：
- 发现新的架构决策时
- 项目约定变更时
- 积累足够多的情节记忆后提炼

</memory-layers>

<api>

## 核心 API

### 1. load_task_memories()

在 Loop 初始化或规划阶段加载相关记忆。

**调用时机**：
- Loop 初始化阶段
- Planner 信息收集阶段

**参数**：
```python
def load_task_memories(
    user_task: str,           # 用户任务描述
    task_type: str = None,    # 任务类型（如 "feature", "bugfix", "refactor"）
    session_id: str = None    # 会话 ID（可选）
) -> dict:
    """
    加载任务相关的记忆（情节记忆 + 语义记忆）

    返回：
    {
        "working_memory": {       # 短期记忆（如果是恢复会话）
            "session_id": "...",
            "context": {...}
        },
        "episodic_memory": [      # 情节记忆（相似任务）
            {
                "episode_id": "...",
                "task_type": "...",
                "task_desc": "...",
                "plan": {...},
                "result": "success/failed",
                "duration_minutes": 15,
                "iterations": 2,
                "agents_used": [...],
                "similarity_score": 0.85
            }
        ],
        "semantic_memory": [      # 语义记忆（项目知识）
            {
                "domain": "architecture",
                "topic": "repository-pattern",
                "content": "...",
                "priority": 1
            }
        ]
    }
    """
```

**实现逻辑**：
```python
def load_task_memories(user_task, task_type=None, session_id=None):
    memories = {
        "working_memory": None,
        "episodic_memory": [],
        "semantic_memory": []
    }

    # 1. 加载短期记忆（恢复会话）
    if session_id:
        working_memory_uri = f"task://sessions/{session_id}"
        working_memory = Skill("memory", f"read {working_memory_uri}")
        if working_memory:
            memories["working_memory"] = working_memory

    # 2. 检索情节记忆（相似任务）
    # 详见 retrieval-strategy.md 的相似任务匹配策略
    similar_tasks = search_similar_episodes(user_task, task_type, limit=5)
    memories["episodic_memory"] = similar_tasks

    # 3. 加载语义记忆（项目知识）
    # 加载核心记忆（priority ≤ 2）
    core_memories = Skill("memory", "search '' --priority-max 2")

    # 根据任务类型加载相关领域知识
    if task_type:
        domain_memories = Skill("memory", f"search '{task_type}' --domain project")
        memories["semantic_memory"] = core_memories + domain_memories
    else:
        memories["semantic_memory"] = core_memories

    return memories
```

### 2. save_task_episode()

任务完成或失败时保存情节记忆。

**调用时机**：
- Loop 完成阶段（任务成功）
- Adjuster 失败调整后（任务失败）

**参数**：
```python
def save_task_episode(
    user_task: str,                 # 用户任务描述
    task_type: str,                 # 任务类型
    plan: dict,                     # 执行计划（planner_result）
    result: str,                    # 结果（"success" 或 "failed"）
    duration_minutes: int,          # 执行时长（分钟）
    iterations: int,                # 迭代次数
    stalled_count: int,             # 停滞次数
    guidance_count: int,            # 用户指导次数
    agents_used: list,              # 使用的 Agents
    skills_used: list,              # 使用的 Skills
    failure_reason: str = None,     # 失败原因（如果失败）
    recovery_action: dict = None    # 恢复措施（如果失败）
) -> str:
    """
    保存任务执行情节到记忆系统

    返回：episode_id（情节记忆 ID）
    """
```

**实现逻辑**：
```python
import hashlib
from datetime import datetime

def save_task_episode(user_task, task_type, plan, result, **kwargs):
    # 生成情节 ID
    episode_id = hashlib.md5(
        f"{user_task}_{datetime.now().isoformat()}".encode('utf-8')
    ).hexdigest()[:12]

    # 构建情节数据
    episode_data = {
        "episode_id": episode_id,
        "task_desc": user_task,
        "task_type": task_type,
        "plan": {
            "task_count": len(plan.get("tasks", [])),
            "report": plan.get("report", ""),
            "agents": [t["agent"] for t in plan.get("tasks", [])],
            "skills": [s for t in plan.get("tasks", []) for s in t.get("skills", [])]
        },
        "result": result,
        "metrics": {
            "duration_minutes": kwargs.get("duration_minutes", 0),
            "iterations": kwargs.get("iterations", 1),
            "stalled_count": kwargs.get("stalled_count", 0),
            "guidance_count": kwargs.get("guidance_count", 0)
        },
        "agents_used": kwargs.get("agents_used", []),
        "skills_used": kwargs.get("skills_used", []),
        "timestamp": datetime.now().isoformat()
    }

    # 失败情况下添加失败信息
    if result == "failed":
        episode_data["failure"] = {
            "reason": kwargs.get("failure_reason", "Unknown"),
            "recovery_action": kwargs.get("recovery_action")
        }

    # 保存到记忆系统
    episode_uri = f"workflow://task-episodes/{task_type}/{episode_id}"

    # 设置优先级：成功情节 priority=3，失败情节 priority=4
    priority = 3 if result == "success" else 4

    # 设置 disclosure（用于智能预加载）
    disclosure = f"When planning {task_type} tasks similar to: {user_task[:50]}..."

    Skill("memory", f"create {episode_uri} '{json.dumps(episode_data)}' "
                    f"--priority {priority} "
                    f"--title '{task_type}任务情节' "
                    f"--disclosure '{disclosure}'")

    print(f"[MindFlow·Memory] ✓ 情节记忆已保存: {episode_id}")
    return episode_id
```

### 3. update_working_memory()

更新短期记忆（当前会话状态）。

**调用时机**：
- 每个阶段转换时

**参数**：
```python
def update_working_memory(
    session_id: str,      # 会话 ID
    phase: str,           # 当前阶段
    context: dict,        # 上下文状态
    additional_state: dict = None
) -> bool:
    """
    更新短期记忆（会话状态）

    返回：True（成功）/ False（失败）
    """
```

**实现逻辑**：
```python
def update_working_memory(session_id, phase, context, additional_state=None):
    working_memory_uri = f"task://sessions/{session_id}"

    # 构建更新内容
    update_data = {
        "phase": phase,
        "context": context,
        "last_updated": datetime.now().isoformat(),
        "additional_state": additional_state or {}
    }

    # 检查是否已存在
    existing_memory = Skill("memory", f"read {working_memory_uri}")

    if existing_memory:
        # 更新现有记忆
        Skill("memory", f"update {working_memory_uri} "
                        f"--append '{json.dumps(update_data)}'")
    else:
        # 创建新记忆
        Skill("memory", f"create task://sessions '{json.dumps(update_data)}' "
                        f"--title 'Session {session_id}' "
                        f"--priority 0")  # 短期记忆优先级最高

    return True
```

### 4. search_failure_patterns()

检索失败模式和恢复策略（用于 Adjuster）。

**调用时机**：
- Adjuster 分析失败原因时

**参数**：
```python
def search_failure_patterns(
    failure_reason: str,  # 失败原因关键词
    task_type: str = None # 任务类型（可选）
) -> list:
    """
    检索相似失败情节和恢复策略

    返回：
    [
        {
            "episode_id": "...",
            "failure_reason": "...",
            "recovery_action": {...},
            "recovery_success": true/false,
            "similarity_score": 0.75
        }
    ]
    """
```

**实现逻辑**（详见 `retrieval-strategy.md` 的失败模式匹配）：
```python
def search_failure_patterns(failure_reason, task_type=None):
    # 构建搜索查询
    search_domain = f"workflow://task-episodes/{task_type}" if task_type else "workflow://task-episodes"

    # 搜索失败情节
    failed_episodes = Skill("memory", f"search '{failure_reason}' --domain workflow")

    # 过滤出失败情节并提取恢复策略
    failure_patterns = []
    for episode in failed_episodes:
        if episode.get("result") == "failed":
            failure_patterns.append({
                "episode_id": episode["episode_id"],
                "failure_reason": episode.get("failure", {}).get("reason", ""),
                "recovery_action": episode.get("failure", {}).get("recovery_action"),
                "recovery_success": episode.get("failure", {}).get("recovery_success", False),
                "similarity_score": calculate_similarity(failure_reason, episode.get("failure", {}).get("reason", ""))
            })

    # 按相似度排序
    failure_patterns.sort(key=lambda x: x["similarity_score"], reverse=True)

    return failure_patterns[:5]  # 返回前5个最相似的失败模式
```

</api>

<integration>

## 与 Loop 的集成

### 初始化阶段集成
```python
print("[MindFlow] 开始初始化任务管理循环...")

user_task = "$ARGUMENTS"

# 生成会话 ID
import hashlib
from datetime import datetime
session_id = hashlib.md5(f"{user_task}_{datetime.now().isoformat()}".encode('utf-8')).hexdigest()[:12]

# 【记忆加载】加载任务相关记忆
task_memories = load_task_memories(user_task, session_id=session_id)

if task_memories["working_memory"]:
    print(f"[MindFlow·Memory] 检测到未完成会话，正在恢复...")
    # 恢复会话逻辑

if task_memories["episodic_memory"]:
    print(f"[MindFlow·Memory] 找到 {len(task_memories['episodic_memory'])} 个相似任务情节")
    for episode in task_memories["episodic_memory"][:3]:
        print(f"  • {episode['task_desc']} - {episode['result']} (相似度: {episode['similarity_score']:.2f})")

if task_memories["semantic_memory"]:
    print(f"[MindFlow·Memory] 已加载 {len(task_memories['semantic_memory'])} 条项目知识")
```

### Planner 集成（详见 `planner-context-learning.md`）
```python
# 在 Tier 3 上下文学习中加载记忆
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}

【情节记忆】相似任务参考：
{format_episodic_memories(task_memories["episodic_memory"])}

【语义记忆】项目知识：
{format_semantic_memories(task_memories["semantic_memory"])}

要求：
1. 参考相似任务的规划模式
2. 遵循项目知识中的架构约定
3. 避免已知的失败模式
...
"""
)
```

### 完成阶段集成
```python
print(f"[MindFlow·{user_task}·completed]")

# 【记忆保存】保存任务执行情节
save_task_episode(
    user_task=user_task,
    task_type=determine_task_type(user_task),
    plan=planner_result,
    result="success",
    duration_minutes=calculate_duration(start_time, end_time),
    iterations=iteration,
    stalled_count=stalled_count,
    guidance_count=guidance_count,
    agents_used=extract_agents_used(planner_result),
    skills_used=extract_skills_used(planner_result)
)

# 清理短期记忆
cleanup_working_memory(session_id)
```

### Adjuster 集成
```python
# 在失败调整阶段检索失败模式
adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

失败任务：{failed_tasks}

【失败模式】历史相似失败：
{format_failure_patterns(search_failure_patterns(failure_reason, task_type))}

要求：
1. 分析失败原因
2. 参考历史恢复策略
3. 应用分级升级策略
...
"""
)
```

</integration>

<notes>

## 注意事项

1. **依赖 Memory 插件**：Memory Bridge 需要 Memory 插件正确安装并初始化
2. **URI 命名规范**：遵循 Memory 插件的 URI 命名空间约定（详见 `memory-schema.md`）
3. **优先级设置**：
   - 短期记忆：priority=0（最高，始终加载）
   - 情节记忆（成功）：priority=3（重要，按需加载）
   - 情节记忆（失败）：priority=4（重要，按需加载）
   - 语义记忆：priority=1-2（核心，自动加载）
4. **检索性能**：大量情节记忆可能影响检索速度，建议定期归档旧记录
5. **隐私保护**：避免在记忆中存储敏感信息（密码、密钥、个人数据）
6. **版本兼容**：Memory Bridge 封装了 Memory 插件 API，升级插件时需要测试兼容性
7. **记忆清理**：定期清理低价值的情节记忆（失败且未修复、过时的知识）

</notes>
