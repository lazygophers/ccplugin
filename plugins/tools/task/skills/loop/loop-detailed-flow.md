# Loop 详细执行流程

本文档包含 MindFlow Loop 各阶段的详细执行流程和代码示例。

## 初始化（Initialization）

### 目标
初始化执行环境，准备必要的资源和状态变量。

### 执行流程

```python
# 初始化状态变量
status = "进行中"
iteration = 0  # 迭代次数
stalled_count = 0  # 停滞次数
guidance_count = 0  # 用户指导次数
max_stalled_attempts = 3  # 最大停滞次数
user_task = "$ARGUMENTS"  # 用户任务目标

# 列出可用资源
available_skills = ListSkills()
available_agents = ListAgents()

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
```

### 状态转换
- **成功** → 进入"计划设计"

---

## 计划设计（Planning / Plan）

### 目标
调用 planner agent 设计执行计划，包括任务分解、依赖建模、资源分配。

### 执行流程

```python
iteration += 1  # 增加迭代计数

# 调用 planner agent
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
当前迭代：第 {iteration} 轮

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

# 处理 planner 的问题
if "questions" in planner_result and planner_result["questions"]:
    for question in planner_result["questions"]:
        user_answer = AskUserQuestion(question)
        # 补充信息后重新生成计划
        planner_result = Agent(
            agent="task:planner",
            prompt=f"补充信息：{user_answer}\n继续设计计划..."
        )

# 特殊情况：无需执行（功能已存在）
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"✓ {planner_result['report']}")
    goto("全部完成")  # 跳转到完成步骤
```

### 生成计划确认文档

直接基于 `plan-confirmation-template.md` 模板格式生成 Markdown 文档，无需脚本处理：

```python
from pathlib import Path

# 确定计划文件路径
# 文件名格式：<任务名>-<迭代数>.md
# 存放目录：.claude/plans（固定路径）
plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

# 从任务内容生成安全的文件名（移除特殊字符，限制长度）
import re
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# 基于 plan-confirmation-template.md 模板格式生成 Markdown
# 包含：任务编排图（Mermaid stateDiagram）、任务清单表格、迭代验收标准、任务说明
Write(str(plan_md_path), filled_markdown_content)

# 输出计划报告
print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"✓ 计划已生成：{plan_md_path}")
```

**重要说明**：
- 计划文件固定存放在 `.claude/plans` 目录（不从环境变量读取）
- 文件名格式：`<任务名>-<迭代数>.md`（例如：`添加用户认证-1.md`）
- 任务名会进行安全化处理（移除特殊字符，限制长度）
- 直接生成 Markdown 文档，无需额外的脚本或 HTML 转换

### 状态转换
- **成功（有任务需执行）** → 进入"计划确认"
- **无需执行（tasks 为空）** → 进入"全部完成"

---

## 计划确认（Plan Confirmation）

### 目标
向用户展示执行计划，等待用户确认。

### 执行流程

```python
# 询问用户意见
user_decision = AskUserQuestion(
    question="请确认执行计划",
    options=["立即执行", "重新设计"]
)

# 清理临时 HTML 文件
Bash(
    command=f"rm -f {plan_html_path}",
    description="删除临时计划 HTML 文件"
)
```

### 状态转换
- **"立即执行"** → 进入"任务执行"
- **"重新设计" 或 "我有别的想法"** → 返回"计划设计"

**确认模板**：参见 [plan-confirmation-template.md](${CLAUDE_PLUGIN_ROOT}/skills/loop/plan-confirmation-template.md)

---

## 任务执行（Execution / Do）

### 目标
创建 Team 并行执行任务，遵循依赖关系和并行规则。

### 执行流程

```python
# 创建执行团队
team_name = f"mindflow-execution-{iteration}"

print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")
print(f"创建执行团队：{team_name}")

# 调用 execute skill（内部会创建 Team 并管理执行）
execution_result = TeamCreate(
    team_name=team_name,
    description=planner_result["report"],
    skills=[Skill("task:execute")]
)

# 等待执行完成
# execute skill 内部会：
# 1. 按依赖顺序调度任务
# 2. 并行执行（最多 2 个）
# 3. 实时监控进度
# 4. 更新任务状态

# 删除团队和清理资源
TeamDelete(team_name=team_name)
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")
print(f"执行完成，团队已清理")
```

### 并行执行规则

- **并行上限**：最多 2 个任务同时执行
- **依赖优先**：严格按依赖顺序调度
- **动态调度**：槽位释放时自动启动下一个 Ready 任务
- **状态追踪**：实时更新任务状态

### 状态转换
- **成功** → 进入"结果验证"

---

## 结果验证（Verification / Check）

### 目标
调用 verifier agent 验证所有任务的验收标准，判断是否达成目标。

### 执行流程

```python
# 调用 verifier agent
verification_result = Agent(
    agent="task:verifier",
    prompt=f"""执行结果验证：

任务目标：{user_task}
当前迭代：第 {iteration} 轮

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
)

# 输出验收报告
print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")
```

### 状态转换

```python
status = verification_result["status"]

if status == "passed":
    # 完全通过，所有验收标准满足
    goto("全部完成")

elif status == "suggestions":
    # 通过但有优化建议
    user_response = AskUserQuestion(
        f"{verification_result['report']}\n\n" +
        "建议：\n" +
        "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
        "\n\n这些优化是否属于当前任务范围？(是/否)"
    )

    if user_response.strip().lower() in ["是", "yes", "y"]:
        goto("计划设计")  # 继续优化
    else:
        goto("全部完成")  # 完成

elif status == "failed":
    # 验收失败，进入失败调整
    goto("失败调整")
```

- **passed** → 进入"全部完成"
- **suggestions + 用户选择继续** → 返回"计划设计"
- **suggestions + 用户选择完成** → 进入"全部完成"
- **failed** → 进入"失败调整"

---

## 失败调整（Adjustment / Act）

### 目标
调用 adjuster agent 分析失败原因，应用分级升级策略。

### 执行流程

```python
# 调用 adjuster agent
adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

任务目标：{user_task}
当前迭代：第 {iteration} 轮

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 检测停滞模式
4. 应用分级升级策略
5. 生成调整报告（≤100字）
"""
)

# 输出调整报告
print(f"[MindFlow·{user_task}·失败调整/{iteration}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")
```

### 应用指数退避

```python
if "retry_config" in adjustment_result:
    backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
    if backoff_seconds > 0:
        print(f"应用指数退避：等待 {backoff_seconds} 秒...")
        time.sleep(backoff_seconds)
```

### 状态转换

```python
strategy = adjustment_result["strategy"]

if strategy == "retry":
    # 首次失败：调整后重试
    apply_adjustments(adjustment_result["adjustments"])
    goto("任务执行")  # 回到执行

elif strategy == "debug":
    # 重复失败：深度诊断
    debug_result = Agent(
        agent="debug",
        prompt=f"深度分析失败原因：{adjustment_result['debug_plan']}"
    )
    apply_debug_fixes(debug_result)
    goto("任务执行")  # 回到执行

elif strategy == "replan":
    # 持续失败：重新规划
    goto("计划设计")  # 回到计划设计

elif strategy == "ask_user":
    # 停滞检测：请求用户指导
    stalled_count += 1
    guidance_count += 1

    user_guidance = AskUserQuestion(adjustment_result["question"])
    apply_user_guidance(user_guidance)

    # 检查是否超过最大停滞次数
    if stalled_count >= max_stalled_attempts:
        print(f"[MindFlow·{user_task}·失败调整/{iteration}·stopped]")
        print(f"检测到持续停滞（{stalled_count} 次），建议人工介入或调整任务目标")
        goto("全部完成")  # 强制结束
    else:
        goto("任务执行")  # 回到执行
```

- **retry** → 返回"任务执行"
- **debug** → 返回"任务执行"
- **replan** → 返回"计划设计"
- **ask_user** → 返回"任务执行"（或超过最大停滞次数则完成）

---

## 全部完成（Completion / Finalization）

### 目标
完成所有迭代，清理资源，生成最终报告。

### 执行流程

```python
# 更新状态
status = "completed"

# 调用 finalizer agent 清理资源
finalizer_result = Agent(
    agent="task:finalizer",
    prompt="""执行 loop 完成后的收尾清理工作：

要求：
1. 停止所有运行中的任务
2. 删除所有计划文件
3. 清理临时文件和缓存
4. 生成清理报告
"""
)

print(f"[MindFlow·{user_task}·completed]")
print("清理完成：" + finalizer_result["report"])
```

### 生成总结报告

```python
# 收集变更文件
changed_files = get_changed_files()  # 通过 git diff 获取

# 输出总结
print("\n## 任务总结")
print(f"状态：✓ 成功（所有验收标准通过）")
print(f"总迭代次数：{iteration}")
print(f"停滞次数：{stalled_count}")
print(f"用户指导次数：{guidance_count}")

print("\n## 变更文件")
for file in changed_files:
    print(f"  - {file}")

print("\n任务完成！")
```

### 状态转换
- **完成** → 结束