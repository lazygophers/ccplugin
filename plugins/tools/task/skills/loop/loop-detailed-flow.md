# Loop 详细执行流程

<overview>
本文档包含 MindFlow Loop 所有7个阶段的详细执行流程，覆盖完整的 PDCA 循环。
</overview>

<phase_initialization>

## 初始化（Initialization）

```python
status = "进行中"
iteration = 0
stalled_count = 0
guidance_count = 0
max_stalled_attempts = 3
user_task = "$ARGUMENTS"

available_skills = ListSkills()
available_agents = ListAgents()

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
```

状态转换：成功 → 计划设计

</phase_initialization>

<caching_helpers>

## Prompt Caching 辅助函数

```python
def extract_static_content(file_path):
    """提取静态内容用于缓存"""
    with open(file_path, 'r') as f:
        content = f.read()

    # 提取 STATIC_CONTENT 标记之间的内容
    start_marker = "<!-- STATIC_CONTENT"
    end_marker = "<!-- /STATIC_CONTENT -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        return content  # 无标记，返回全部内容

    # 提取静态部分（包含标记）
    return content[start_idx:end_idx + len(end_marker)]


def check_min_tokens(content, model="haiku"):
    """检查是否满足最小 token 要求"""
    min_tokens = {
        "haiku": 4096,
        "sonnet": 1024,
        "opus": 1024
    }

    # 粗略估算：1 token ≈ 4 bytes
    estimated_tokens = len(content.encode('utf-8')) // 4

    required = min_tokens.get(model, 1024)
    if estimated_tokens < required:
        print(f"警告：静态内容仅 {estimated_tokens} tokens，"
              f"模型 {model} 要求 ≥ {required} tokens")
        return False

    return True


def verify_cache_stability(file_paths):
    """验证静态内容稳定性（通过哈希）"""
    import hashlib
    import json

    hash_file = ".claude/cache_hashes.json"
    current_hashes = {}

    # 计算当前哈希
    for path in file_paths:
        static_content = extract_static_content(path)
        content_hash = hashlib.sha256(static_content.encode()).hexdigest()
        current_hashes[path] = content_hash

    # 对比上次哈希
    try:
        with open(hash_file, 'r') as f:
            last_hashes = json.load(f)
    except FileNotFoundError:
        last_hashes = {}

    # 检测变化
    changed_files = []
    for path, current_hash in current_hashes.items():
        if path in last_hashes and last_hashes[path] != current_hash:
            changed_files.append(path)
            print(f"缓存失效：{path} 静态内容已变化")

    # 保存当前哈希
    with open(hash_file, 'w') as f:
        json.dump(current_hashes, f, indent=2)

    return len(changed_files) == 0  # True 表示缓存稳定
```

使用示例：

```python
# 在初始化阶段检查缓存稳定性
cache_files = [
    "plugins/tools/task/skills/loop/SKILL.md",
    "plugins/tools/task/skills/planner/SKILL.md"
]

# 提取静态内容
loop_static = extract_static_content(cache_files[0])
planner_static = extract_static_content(cache_files[1])

# 检查最小 token 要求
check_min_tokens(loop_static, model="sonnet")    # True
check_min_tokens(planner_static, model="haiku")  # True

# 验证缓存稳定性
cache_stable = verify_cache_stability(cache_files)
if cache_stable:
    print("✓ 缓存稳定，预期命中率 >90%")
else:
    print("⚠ 缓存已失效，首次调用将重建缓存")
```

</caching_helpers>

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

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

# 强制保留用户语言字符（中文：\u4e00-\u9fff）
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# YAML frontmatter 元数据 + 必须使用 plan-confirmation-template.md 模板
frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""
Write(str(plan_md_path), frontmatter + filled_markdown_content)

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"计划已生成：{plan_md_path}")
```

状态转换：有任务 → 计划确认；无任务 → 全部完成

</phase_planning>

<phase_confirmation>

## 计划确认（Plan Confirmation）

```python
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"计划文件：{plan_md_path}")

Bash(command=f"uvx --from git+https://github.com/lazygophers/ccplugin.git@master md2html {plan_md_path}",
     description="将计划 MD 转换为 HTML 并在浏览器打开")
print("已在浏览器打开计划预览")
print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

user_decision = AskUserQuestion(question="执行计划已准备就绪，是否开始执行？",
                                 options=["立即执行", "重新设计"])
```

状态转换：立即执行 → 任务执行；重新设计 → 计划设计

</phase_confirmation>

<phase_execution>

## 任务执行（Execution / Do）

```python
team_name = f"mindflow-execution-{iteration}"
print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")

execution_result = TeamCreate(
    team_name=team_name,
    description=planner_result["report"],
    skills=[Skill("task:execute")]
)

# 更新plan文件状态：📋→⏸️→🔄→✅/❌，同步 frontmatter
update_plan_task_status(plan_md_path, task_id, new_icon)

TeamDelete(team_name=team_name)
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")
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

# 状态转换
status = verification_result["status"]

if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    user_response = AskUserQuestion(
        f"{verification_result['report']}\n\n建议：\n" +
        "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
        "\n\n这些优化是否属于当前任务范围？(是/否)"
    )

    if user_response.strip().lower() in ["是", "yes", "y"]:
        goto("计划设计")
    else:
        goto("全部完成")

elif status == "failed":
    goto("失败调整")
```

</phase_verification>

<phase_adjustment>

## 失败调整（Adjustment / Act）

```python
adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 检测停滞模式
4. 应用分级升级策略
5. 生成调整报告（≤100字）
"""
)

print(f"[MindFlow·{user_task}·失败调整/{iteration}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")

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
    goto("计划设计")

elif strategy == "ask_user":
    stalled_count += 1
    guidance_count += 1

    user_guidance = AskUserQuestion(adjustment_result["question"])
    apply_user_guidance(user_guidance)

    if stalled_count >= max_stalled_attempts:
        print(f"[MindFlow·{user_task}·失败调整/{iteration}·stopped]")
        print(f"检测到持续停滞（{stalled_count} 次），建议人工介入")
        goto("全部完成")
    else:
        goto("任务执行")
```

</phase_adjustment>

<phase_completion>

## 全部完成（Completion / Finalization）

```python
finalizer_result = Agent(agent="task:finalizer",
    prompt=f"""执行 loop 完成后的收尾清理：
计划文件：{plan_md_path}
要求：1.停止任务 2.删除计划文件（含.html） 3.清理临时文件 4.生成报告
""")

print(f"[MindFlow·{user_task}·completed]")

# 总结报告
changed_files = get_changed_files()

print("\n## 任务总结")
print(f"状态：成功（所有验收标准通过）")
print(f"总迭代次数：{iteration}")
print(f"停滞次数：{stalled_count}")
print(f"用户指导次数：{guidance_count}")

print("\n## 变更文件")
for file in changed_files:
    print(f"  - {file}")

print("\n任务完成")
```

状态转换：完成 → 结束

</phase_completion>
