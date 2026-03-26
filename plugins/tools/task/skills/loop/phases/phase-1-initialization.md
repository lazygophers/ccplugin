<!-- STATIC_CONTENT: Phase 1流程文档，可缓存 -->

# Phase 1: Initialization

## 概述

初始化阶段是任务执行的起点，负责建立干净的执行环境并恢复之前中断的状态。

## 目标

- 状态变量重置（iteration=0, context={}）
- 检查点恢复（如果存在）
- Memory加载（短期记忆、情节记忆）
- 资源可用性检查

## 执行流程

**所有输出必须以 [MindFlow] 开头。**

```python
print("[MindFlow] 开始初始化任务管理循环...")

user_task = "$ARGUMENTS"

# 【检查点恢复】尝试加载上次中断的检查点
checkpoint = load_checkpoint(user_task)

if checkpoint:
    # 从检查点恢复状态
    iteration = checkpoint["iteration"]
    context = checkpoint["context"]
    plan_md_path = checkpoint.get("plan_md_path")
    stalled_count = context.get("stalled_count", 0)
    guidance_count = context.get("guidance_count", 0)
    max_stalled_attempts = context.get("max_stalled_attempts", 3)

    print(f"[MindFlow] ✓ 从检查点恢复执行")
    print(f"[MindFlow]   迭代: {iteration}")
    print(f"[MindFlow]   阶段: {checkpoint['phase']}")
    print(f"[MindFlow·{user_task}·初始化/0·恢复自检查点]")

    # 跳转到检查点保存的阶段
    phase_map = {
        "planning": "计划设计",
        "confirmation": "计划确认",
        "execution": "任务执行",
        "verification": "结果验证",
        "adjustment": "失败调整"
    }
    next_phase = phase_map.get(checkpoint["phase"], "计划设计")
    print(f"[MindFlow] 继续执行 {next_phase} 阶段...")
    goto(next_phase)

else:
    # 正常初始化
    status = "进行中"
    iteration = 0
    stalled_count = 0
    guidance_count = 0
    max_stalled_attempts = 3

    # 上下文状态
    context = {
        "replan_trigger": None  # 跟踪重新规划的触发来源
    }

    # 【记忆加载】生成会话 ID 并加载任务相关记忆
    import hashlib
    from datetime import datetime
    session_id = hashlib.md5(f"{user_task}_{datetime.now().isoformat()}".encode('utf-8')).hexdigest()[:12]
    start_time = datetime.now()

    print(f"[MindFlow] 正在加载任务记忆...")
    task_memories = load_task_memories(
        user_task=user_task,
        task_type=determine_task_type(user_task),
        session_id=session_id
    )

    # 记录记忆加载结果
    context["session_id"] = session_id
    context["task_memories"] = task_memories

    if task_memories["episodic_memory"]:
        print(f"[MindFlow·Memory] 找到 {len(task_memories['episodic_memory'])} 个相似任务情节")
        for episode in task_memories["episodic_memory"][:3]:
            print(f"  • {episode['task_desc']} - {episode['result']} (相似度: {episode['similarity_score']:.2f})")

    if task_memories["semantic_memory"]:
        print(f"[MindFlow·Memory] 已加载 {len(task_memories['semantic_memory'])} 条项目知识")

    print(f"[MindFlow] 正在检查可用资源...")
    available_skills = ListSkills()
    available_agents = ListAgents()

    print(f"[MindFlow·{user_task}·初始化/0·进行中]")
    print(f"[MindFlow] 初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
```

## 输出

- 干净的任务上下文
- 恢复的中间状态（如有）
- 可用的agents和skills列表

## 状态转换

- **成功** → 计划设计（Phase 4）
- **检查点恢复** → 对应阶段

## Prompt Caching 辅助

初始化阶段可验证缓存稳定性，确保 STATIC_CONTENT 标记内容稳定。详见：cache_hashes.json 记录内容哈希，检测变化时提示缓存失效。

## 记忆管理辅助函数

### 任务类型推断

```python
def determine_task_type(user_task: str) -> str:
    """
    从用户任务描述推断任务类型

    返回：feature/bugfix/refactor/docs/test/optimization/migration
    """
    task_lower = user_task.lower()

    if any(keyword in task_lower for keyword in ["实现", "添加", "新增", "开发", "implement", "add", "create", "feature"]):
        return "feature"
    elif any(keyword in task_lower for keyword in ["修复", "解决", "bug", "fix", "resolve", "issue"]):
        return "bugfix"
    elif any(keyword in task_lower for keyword in ["重构", "优化", "refactor", "optimize", "improve", "cleanup"]):
        return "refactor"
    elif any(keyword in task_lower for keyword in ["文档", "注释", "doc", "documentation", "comment", "readme"]):
        return "docs"
    elif any(keyword in task_lower for keyword in ["测试", "test", "unit", "e2e", "integration", "spec"]):
        return "test"
    elif any(keyword in task_lower for keyword in ["性能", "performance", "速度", "speed", "optimization"]):
        return "optimization"
    elif any(keyword in task_lower for keyword in ["迁移", "升级", "migration", "upgrade", "update"]):
        return "migration"
    else:
        return "feature"  # 默认为功能开发
```

### Agent/Skills 提取

```python
def extract_agents_used(planner_result: dict) -> list:
    """
    从规划结果提取使用的 Agents 列表（去重）
    """
    agents = set()
    for task in planner_result.get("tasks", []):
        if "agent" in task:
            agents.add(task["agent"])
    return sorted(list(agents))


def extract_skills_used(planner_result: dict) -> list:
    """
    从规划结果提取使用的 Skills 列表（去重）
    """
    skills = set()
    for task in planner_result.get("tasks", []):
        for skill in task.get("skills", []):
            skills.add(skill)
    return sorted(list(skills))
```

### 短期记忆清理

```python
def cleanup_working_memory(session_id: str) -> bool:
    """
    清理短期记忆（会话状态）

    注意：短期记忆已通过 save_task_episode() 归档到情节记忆，
    因此可以安全删除
    """
    working_memory_uri = f"task://sessions/{session_id}"

    try:
        # 调用 Memory 插件删除（如果支持）
        # 注意：当前 Memory 插件可能不支持删除操作，可以降低优先级替代
        Skill("memory", f"update {working_memory_uri} --priority 10")  # 归档（不加载）
        return True
    except Exception as e:
        print(f"[MindFlow·Memory] ⚠️ 短期记忆清理失败: {e}")
        return False
```

### 记忆格式化（用于 Planner 提示）

```python
def format_episodic_memories(episodes: list, max_count: int = 3) -> str:
    """
    格式化情节记忆为 Planner 可读的文本
    """
    if not episodes:
        return "（无相似任务历史）"

    lines = []
    for i, episode in enumerate(episodes[:max_count], 1):
        lines.append(f"\n【情节 {i}】 {episode['task_desc']}")
        lines.append(f"  结果: {episode['result']}")
        lines.append(f"  相似度: {episode['similarity_score']:.2f}")
        lines.append(f"  规划: {episode['plan']['report']}")
        lines.append(f"  用时: {episode['metrics']['duration_minutes']}分钟, 迭代: {episode['metrics']['iterations']}次")
        lines.append(f"  使用的 Agents: {', '.join(episode['agents_used'])}")

        # 失败情节添加失败信息
        if episode['result'] == 'failed' and 'failure' in episode:
            lines.append(f"  失败原因: {episode['failure']['reason']}")
            if episode['failure'].get('recovery_action'):
                lines.append(f"  恢复措施: {episode['failure']['recovery_action']['description']}")

    return "\n".join(lines)


def format_semantic_memories(memories: list, max_count: int = 5) -> str:
    """
    格式化语义记忆为 Planner 可读的文本
    """
    if not memories:
        return "（无项目知识）"

    # 按领域分组
    by_domain = {}
    for memory in memories:
        domain = memory.get("domain", "other")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(memory)

    lines = []
    for domain, domain_memories in sorted(by_domain.items()):
        lines.append(f"\n【{domain}】")
        for memory in domain_memories[:max_count]:
            lines.append(f"  • {memory.get('title', 'Untitled')}")
            content = memory.get("content", "")
            # 截取前 100 字符
            if len(content) > 100:
                content = content[:100] + "..."
            lines.append(f"    {content}")

    return "\n".join(lines)


def format_failure_patterns(patterns: list, max_count: int = 3) -> str:
    """
    格式化失败模式为 Adjuster 可读的文本
    """
    if not patterns:
        return "（无相似失败历史）"

    lines = []
    for i, pattern in enumerate(patterns[:max_count], 1):
        lines.append(f"\n【失败模式 {i}】")
        lines.append(f"  任务: {pattern.get('task_desc', 'Unknown')}")
        lines.append(f"  失败原因: {pattern['failure_reason']}")
        lines.append(f"  相似度: {pattern['similarity_score']:.2f}")

        recovery_action = pattern.get('recovery_action')
        if recovery_action:
            lines.append(f"  恢复措施: {recovery_action.get('description', 'Unknown')}")
            lines.append(f"  措施类型: {recovery_action.get('type', 'Unknown')}")
            if pattern['recovery_success']:
                lines.append(f"  ✓ 恢复成功")
            else:
                lines.append(f"  ✗ 恢复失败")

        lessons = pattern.get('lessons_learned')
        if lessons:
            lines.append(f"  经验教训: {lessons}")

    return "\n".join(lines)


def extract_failure_reason(failed_tasks: list) -> str:
    """
    从失败任务中提取失败原因摘要

    优先提取错误类型和关键信息
    """
    if not failed_tasks:
        return "Unknown failure"

    # 合并所有失败原因
    reasons = []
    for task in failed_tasks:
        if "error" in task:
            reasons.append(task["error"])
        elif "reason" in task:
            reasons.append(task["reason"])

    # 返回第一个失败原因（通常是根本原因）
    if reasons:
        return reasons[0]
    else:
        return f"任务 {failed_tasks[0].get('id', 'Unknown')} 执行失败"


def get_failed_tasks(planner_result: dict) -> list:
    """
    从规划结果中获取失败的任务列表
    """
    failed_tasks = []
    for task in planner_result.get("tasks", []):
        if task.get("status") in ["failed", "error"]:
            failed_tasks.append(task)
    return failed_tasks
```

<!-- /STATIC_CONTENT -->
