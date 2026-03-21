# Loop 详细执行流程

<overview>
本文档包含 MindFlow Loop 所有7个阶段的详细执行流程，覆盖完整的 PDCA 循环。

**强制输出格式**：所有输出必须以 `[MindFlow]` 开头，无例外。
</overview>

<phase_initialization>

## 初始化（Initialization）

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

状态转换：成功 → 计划设计；检查点恢复 → 对应阶段

</phase_initialization>

<caching_helpers>

## Prompt Caching 辅助函数

初始化阶段可验证缓存稳定性，确保 STATIC_CONTENT 标记内容稳定。
详见：cache_hashes.json 记录内容哈希，检测变化时提示缓存失效。

</caching_helpers>

<memory_helpers>

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

</memory_helpers>

<phase_planning>

## 计划设计（Planning / Plan）

```python
iteration += 1

planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 分析项目结构（优先中等深度）
2. 收集目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
)

# 处理问题
if "questions" in planner_result and planner_result["questions"]:
    for question in planner_result["questions"]:
        user_answer = AskUserQuestion(question)
        planner_result = Agent(
            agent="task:planner",
            prompt=f"补充信息：{user_answer}\n继续设计计划..."
        )

# 无需执行情况
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"{planner_result['report']}")
    goto("全部完成")
```

```python
# 生成计划文档
from pathlib import Path
import re
import json

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

# 强制保留用户语言字符（中文：\u4e00-\u9fff）
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# YAML frontmatter
frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""

# 调用 task:plan-formatter 格式化计划文档
formatted_plan = Agent(
    agent="task:plan-formatter",
    prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

YAML Frontmatter（必须放在文档开头）：
{frontmatter}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的任务清单表格
"""
)

Write(str(plan_md_path), formatted_plan)

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"计划已生成：{plan_md_path}")

# 【检查点保存】计划设计完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="planning",
    context=context,
    plan_md_path=str(plan_md_path)
)
```

状态转换：有任务 → 计划确认；无任务 → 全部完成

</phase_planning>

<phase_confirmation>

## 计划确认（Plan Confirmation）

**智能跳过逻辑**：

| 场景 | `iteration` | `replan_trigger` | 是否确认 |
|------|-------------|------------------|---------|
| 首次规划 | 1 | None | ✓ 需要确认 |
| 用户主动重新设计 | >1 | "user" | ✓ 需要确认 |
| Adjuster 自动重新规划 | >1 | "adjuster" | ✗ 跳过确认 |
| Verifier 建议优化 | >1 | "verifier" | ✗ 跳过确认 |

```python
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"计划文件：{plan_md_path}")

# 【智能跳过】检查是否需要用户确认
replan_trigger = context.get("replan_trigger", None)

# 跳过确认的场景
if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    print(f"\n✓ 自动重新规划（触发来源：{replan_trigger}），跳过用户确认")
    print(f"  原因：已在{'调整阶段' if replan_trigger == 'adjuster' else '验证阶段'}告知用户")
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    # 清除标志，准备下一轮
    context["replan_trigger"] = None

    # 【检查点保存】自动批准后保存检查点
    save_checkpoint(
        user_task=user_task,
        iteration=iteration,
        phase="confirmation",
        context=context,
        plan_md_path=str(plan_md_path)
    )

    goto("任务执行")

# 需要用户确认的场景（首次或用户主动重新设计）
Bash(command=f"uvx --from git+https://github.com/lazygophers/ccplugin.git@master md2html {plan_md_path}",
     description="将计划 MD 转换为 HTML 并在浏览器打开")
print("已在浏览器打开计划预览")
print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

user_decision = AskUserQuestion(question="执行计划已准备就绪，是否开始执行？",
                                 options=["立即执行", "重新设计"])

if user_decision == "重新设计":
    # 用户主动选择重新设计，下次规划仍需确认
    context["replan_trigger"] = "user"
    goto("计划设计")
else:
    # 用户批准执行，清除 replan_trigger 标志
    context["replan_trigger"] = None

    # 【检查点保存】用户批准后保存检查点
    save_checkpoint(
        user_task=user_task,
        iteration=iteration,
        phase="confirmation",
        context=context,
        plan_md_path=str(plan_md_path)
    )

    goto("任务执行")
```

状态转换：
- 首次/用户重新设计：需确认 → 立即执行/重新设计
- 自动重新规划(adjuster/verifier)：自动批准 → 任务执行

</phase_confirmation>

<phase_execution>

## 任务执行（Execution / Do，含 HITL 审批）

```python
team_name = f"mindflow-execution-{iteration}"
print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")

# 【HITL 集成】加载用户配置
hitl_config = load_hitl_config()  # 从 .claude/task.local.md 加载配置

# 【智能并行调度】替代固定并行度
# 1. 获取待执行任务
ready_tasks = [task for task in planner_result["tasks"] if is_ready(task)]

# 2. 评估任务复杂度
task_complexities = {}
for task in ready_tasks:
    complexity = Agent(
        agent="task:complexity-analyzer",
        prompt=f"""评估任务复杂度：

任务 ID：{task['id']}
涉及文件：{task['files']}
依赖任务：{task['dependencies']}
Agent：{task['agent']}
Skills：{task['skills']}

要求：
1. 计算涉及文件数维度得分（30%）
2. 计算依赖深度维度得分（25%）
3. 估算 token 消耗维度得分（20%）
4. 检测文件冲突维度得分（25%）
5. 返回综合复杂度分数（0-100）和等级（low/medium/high）
"""
    )
    task_complexities[task['id']] = complexity

# 3. 检测文件冲突
file_map = {}
for task in ready_tasks:
    for file in task.get('files', []):
        if file not in file_map:
            file_map[file] = []
        file_map[file].append(task['id'])

has_conflicts = any(len(tasks) > 1 for tasks in file_map.values())

# 4. 计算动态并行度（尊重用户约束）
user_max_parallel = hitl_config.get("max_parallel_tasks", 2)
max_parallel = min(user_max_parallel, 5)  # 硬上限 5

low_complexity_count = sum(
    1 for c in task_complexities.values() if c['level'] == 'low'
)

if has_conflicts:
    parallel_degree = 1  # 存在文件冲突，串行执行
    scheduling_reason = "检测到文件冲突，任务串行执行"
elif low_complexity_count == len(ready_tasks):
    parallel_degree = max_parallel  # 全部低复杂度，最大并行
    scheduling_reason = f"全部低复杂度任务，并行度 {max_parallel}"
else:
    parallel_degree = 2  # 混合复杂度，保守策略
    scheduling_reason = "混合复杂度任务，使用默认并行度 2"

print(f"[MindFlow·任务执行] 智能调度：{parallel_degree}/{max_parallel}（用户约束）")
print(f"[MindFlow·任务执行] 调度原因：{scheduling_reason}")

# 5. 选择本批次并行任务
parallel_batch = []
for task in ready_tasks:
    if len(parallel_batch) >= parallel_degree:
        break

    # 检查是否与已选任务存在文件冲突
    task_files = set(task.get('files', []))
    conflict_free = True
    for selected in parallel_batch:
        selected_files = set(selected.get('files', []))
        if task_files & selected_files:  # 有交集
            conflict_free = False
            break

    if conflict_free:
        parallel_batch.append(task)

print(f"[MindFlow·任务执行] 本批次任务：{[t['id'] for t in parallel_batch]}")

# 6. 执行任务
execution_result = TeamCreate(
    team_name=team_name,
    description=planner_result["report"],
    skills=[Skill("task:execute")]
)

# 注意：HITL 审批在 task:execute skill 内部进行
# execute skill 会拦截每个 Agent 的工具调用，逐个进行风险评估和审批
#
# 工作流程：
#   1. execute 调用 Agent 执行任务
#   2. 拦截 Agent 的每个工具调用（Edit、Write、Bash 等）
#   3. 调用 hitl_approve_operation() 进行风险评估
#   4. 根据风险等级决定是否需要用户确认
#   5. 用户拒绝 → 标记任务失败，记录原因
#   6. 用户批准 → 继续执行工具调用
#   7. 所有审批决策记录到 approval-log.json

# 更新plan文件状态：📋→⏸️→🔄→✅/❌，同步 frontmatter
update_plan_task_status(plan_md_path, task_id, new_icon)

TeamDelete(team_name=team_name)
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")

# 检查是否有任务因用户拒绝而失败
if execution_result.get("user_rejected_tasks"):
    rejected_tasks = execution_result["user_rejected_tasks"]
    print(f"\n⚠️ 有 {len(rejected_tasks)} 个任务因用户拒绝操作而失败")
    for task in rejected_tasks:
        print(f"  • 任务 {task['id']}: 拒绝了操作 \"{task['rejected_operation']}\"")

# 【检查点保存】任务执行完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="execution",
    context=context,
    plan_md_path=str(plan_md_path)
)
```

状态转换：成功 → 结果验证

</phase_execution>

<phase_verification>

## 结果验证（Verification / Check）

```python
verification_result = Agent(
    agent="task:verifier",
    prompt=f"""执行结果验证：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
)

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")

# 更新plan文件整体状态（passed→completed, failed→failed）
update_plan_frontmatter(plan_md_path, status=verification_result["status"],
                        completed_count=count_completed_tasks())

# 【检查点保存】结果验证完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="verification",
    context=context,
    plan_md_path=str(plan_md_path),
    additional_state={
        "verification_status": verification_result["status"],
        "verification_report": verification_result["report"]
    }
)

# 状态转换
status = verification_result["status"]

if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    # 自动继续优化（已移除用户确认）
    print(f"检测到优化建议，自动继续下一轮迭代...")
    print("建议列表：")
    for s in verification_result['suggestions']:
        print(f"  - {s['suggestion']}")

    # 标记为 verifier 触发的重新规划，跳过用户确认
    context["replan_trigger"] = "verifier"
    goto("计划设计")

elif status == "failed":
    goto("失败调整")
```

</phase_verification>

<phase_adjustment>

## 失败调整（Adjustment / Act，含 HITL 审批）

```python
# 【记忆检索】检索失败模式和恢复策略
print(f"[MindFlow] 正在检索历史失败模式...")

# 提取失败原因关键词
failed_tasks = get_failed_tasks(planner_result)
failure_reason = extract_failure_reason(failed_tasks)

# 检索相似失败情节
failure_patterns = search_failure_patterns(
    failure_reason=failure_reason,
    task_type=determine_task_type(user_task)
)

if failure_patterns:
    print(f"[MindFlow·Memory] 找到 {len(failure_patterns)} 个相似失败模式")
    for pattern in failure_patterns[:2]:
        print(f"  • {pattern['failure_reason']} (相似度: {pattern['similarity_score']:.2f})")
        if pattern['recovery_success']:
            print(f"    ✓ 恢复措施有效: {pattern['recovery_action']['description']}")

adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

任务目标：{user_task}
迭代编号：{iteration}

【失败模式】历史相似失败（共 {len(failure_patterns)} 个）：
{format_failure_patterns(failure_patterns)}

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 参考历史恢复策略（优先采用 recovery_success=true 的措施）
4. 检测停滞模式
5. 应用分级升级策略
6. 生成调整报告（≤100字）
"""
)

print(f"[MindFlow·{user_task}·失败调整/{iteration}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")

# 【检查点保存】失败调整完成后保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="adjustment",
    context=context,
    plan_md_path=str(plan_md_path),
    additional_state={
        "adjustment_strategy": adjustment_result["strategy"],
        "adjustment_report": adjustment_result["report"]
    }
)

# 【HITL 集成】如果 adjuster 建议执行危险操作，需要用户审批
if "recovery_action" in adjustment_result and adjustment_result["recovery_action"]:
    recovery_action = adjustment_result["recovery_action"]

    # 风险评估
    approval = hitl_approve_operation(
        operation={
            "tool": "AdjusterAction",
            "target": recovery_action.get("type", "未知操作"),
            "summary": recovery_action.get("description", ""),
            "command": recovery_action.get("command", "")
        },
        context={
            "task_hash": task_hash,
            "iteration": iteration,
            "failure_count": failure_count,
            "environment": "development"
        }
    )

    if not approval["approved"]:
        # 用户拒绝了 adjuster 的建议
        print(f"⚠️ 用户拒绝了调整操作：{recovery_action['description']}")

        # 请求用户指导
        user_guidance = AskUserQuestion(
            questions=[{
                "question": f"Adjuster 建议的恢复操作被拒绝：{recovery_action['description']}。请问如何处理？",
                "header": "调整方案",
                "multiSelect": False,
                "options": [
                    {"label": "手动修复", "description": "暂停任务，由用户手动修复"},
                    {"label": "跳过该任务", "description": "标记该任务失败，继续其他任务"},
                    {"label": "重新规划", "description": "放弃当前计划，重新设计"},
                    {"label": "终止循环", "description": "停止所有任务执行"}
                ]
            }]
        )

        if user_guidance == "手动修复":
            print("等待用户手动修复...")
            # 暂停并等待用户确认修复完成
            user_confirm = AskUserQuestion(
                questions=[{
                    "question": "问题是否已手动修复？",
                    "header": "确认修复",
                    "multiSelect": False,
                    "options": [
                        {"label": "已修复，继续执行", "description": ""},
                        {"label": "无法修复，终止任务", "description": ""}
                    ]
                }]
            )
            if user_confirm == "已修复，继续执行":
                goto("任务执行")
            else:
                goto("全部完成")

        elif user_guidance == "跳过该任务":
            mark_task_as_failed(failed_task_id, reason="User skipped")
            goto("结果验证")

        elif user_guidance == "重新规划":
            # 标记为用户主动触发的重新规划，需要重新确认
            context["replan_trigger"] = "user"
            goto("计划设计")

        elif user_guidance == "终止循环":
            goto("全部完成")

    else:
        # 用户批准了 adjuster 的建议，继续执行
        print(f"✓ 用户批准了调整操作：{recovery_action['description']}")

# 指数退避
if "retry_config" in adjustment_result:
    backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
    if backoff_seconds > 0:
        print(f"应用指数退避：等待 {backoff_seconds} 秒...")
        time.sleep(backoff_seconds)

# 状态转换
strategy = adjustment_result["strategy"]

if strategy == "retry":
    apply_adjustments(adjustment_result["adjustments"])
    goto("任务执行")

elif strategy == "debug":
    debug_result = Agent(
        agent="debug",
        prompt=f"深度分析失败原因：{adjustment_result['debug_plan']}"
    )
    apply_debug_fixes(debug_result)
    goto("任务执行")

elif strategy == "replan":
    # 标记为 adjuster 触发的重新规划，跳过用户确认
    context["replan_trigger"] = "adjuster"
    goto("计划设计")

elif strategy == "ask_user":
    stalled_count += 1
    guidance_count += 1

    user_guidance = AskUserQuestion(adjustment_result["question"])
    apply_user_guidance(user_guidance)

    if stalled_count >= max_stalled_attempts:
        print(f"[MindFlow·{user_task}·失败调整/{iteration}·stopped]")
        print(f"检测到持续停滞（{stalled_count} 次），建议人工介入")

        # 【记忆保存】保存失败情节
        print(f"[MindFlow] 正在保存失败记忆...")

        end_time = datetime.now()
        duration_minutes = int((end_time - start_time).total_seconds() / 60)

        episode_id = save_task_episode(
            user_task=user_task,
            task_type=determine_task_type(user_task),
            plan=planner_result,
            result="failed",
            duration_minutes=duration_minutes,
            iterations=iteration,
            stalled_count=stalled_count,
            guidance_count=guidance_count,
            agents_used=extract_agents_used(planner_result),
            skills_used=extract_skills_used(planner_result),
            failure_reason=f"持续停滞（{stalled_count} 次），无法自动恢复",
            recovery_action=adjustment_result.get("recovery_action")
        )

        print(f"[MindFlow·Memory] ✓ 失败情节已保存: {episode_id}")

        goto("全部完成")
    else:
        goto("任务执行")
```</invoke>

</phase_adjustment>

<phase_completion>

## 全部完成（Completion / Finalization）

```python
finalizer_result = Agent(agent="task:finalizer",
    prompt=f"""执行 loop 完成后的收尾清理：
计划文件：{plan_md_path}
要求：1.停止任务 2.删除计划文件（含.html） 3.清理临时文件 4.生成报告
""")

# 【检查点清理】任务完成后清理检查点
cleanup_checkpoint(user_task)

# 【记忆保存】保存任务执行情节到记忆系统
print(f"[MindFlow] 正在保存任务执行记忆...")

# 计算执行时长
end_time = datetime.now()
duration_minutes = int((end_time - start_time).total_seconds() / 60)

# 提取使用的 Agents 和 Skills
agents_used = extract_agents_used(planner_result)
skills_used = extract_skills_used(planner_result)

# 保存情节记忆
episode_id = save_task_episode(
    user_task=user_task,
    task_type=determine_task_type(user_task),
    plan=planner_result,
    result="success",
    duration_minutes=duration_minutes,
    iterations=iteration,
    stalled_count=stalled_count,
    guidance_count=guidance_count,
    agents_used=agents_used,
    skills_used=skills_used
)

print(f"[MindFlow·Memory] ✓ 情节记忆已保存: {episode_id}")

# 清理短期记忆（会话状态）
session_id = context.get("session_id")
if session_id:
    cleanup_working_memory(session_id)
    print(f"[MindFlow·Memory] ✓ 短期记忆已清理")

print(f"[MindFlow·{user_task}·completed]")

# 总结报告
changed_files = get_changed_files()

print("\n## 任务总结")
print(f"状态：成功（所有验收标准通过）")
print(f"总迭代次数：{iteration}")
print(f"停滞次数：{stalled_count}")
print(f"用户指导次数：{guidance_count}")
print(f"执行时长：{duration_minutes} 分钟")

print("\n## 变更文件")
for file in changed_files:
    print(f"  - {file}")

print("\n## 记忆积累")
print(f"情节记忆 ID：{episode_id}")
print(f"会话 ID：{session_id}")
print(f"记忆 URI：workflow://task-episodes/{determine_task_type(user_task)}/{episode_id}")

print("\n任务完成")
```

状态转换：完成 → 结束

</phase_completion>
