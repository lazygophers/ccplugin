# Loop 详细执行流程 - 阶段 1-4

本文档包含 MindFlow Loop 阶段 1-4 的详细执行流程和代码示例。

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
# 1. 将计划 MD 转换为 HTML 并在浏览器打开预览
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"📋 计划文件：{plan_md_path}")

# 使用 md2html 命令转换为 HTML（自动打开浏览器并删除临时文件）
Bash(
    command=f"uvx --from git+https://github.com/lazygophers/ccplugin.git@master md2html {plan_md_path}",
    description="将计划 MD 转换为 HTML 并在浏览器打开"
)
print("✓ 已在浏览器打开计划预览")

# 2. 等待用户确认
print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

user_decision = AskUserQuestion(
    question="执行计划已准备就绪，是否开始执行？",
    options=["立即执行", "重新设计"]
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
