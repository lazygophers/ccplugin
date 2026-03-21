# Memory Bridge API Details

本文档包含记忆桥接的完整 API 实现和集成细节。

---

## 核心 API 实现

### 1. load_task_memories() - 详细实现

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

---

### 2. save_task_episode() - 详细实现

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

---

### 3. update_working_memory() - 详细实现

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

---

### 4. search_failure_patterns() - 详细实现

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

---

## 与 Loop 的完整集成

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

---

### Planner 集成

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

---

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

---

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

---

## 注意事项

1. **依赖 Memory 插件**: Memory Bridge 需要 Memory 插件正确安装并初始化
2. **URI 命名规范**: 遵循 Memory 插件的 URI 命名空间约定（详见 `memory-schema.md`）
3. **优先级设置**:
   - 短期记忆：priority=0（最高，始终加载）
   - 情节记忆（成功）：priority=3（重要，按需加载）
   - 情节记忆（失败）：priority=4（重要，按需加载）
   - 语义记忆：priority=1-2（核心，自动加载）
4. **检索性能**: 大量情节记忆可能影响检索速度，建议定期归档旧记录
5. **隐私保护**: 避免在记忆中存储敏感信息（密码、密钥、个人数据）
6. **版本兼容**: Memory Bridge 封装了 Memory 插件 API，升级插件时需要测试兼容性
7. **记忆清理**: 定期清理低价值的情节记忆（失败且未修复、过时的知识）
