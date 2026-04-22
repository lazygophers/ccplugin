---
description: 恢复中断任务。当用户要求继续、恢复之前未完成的任务时触发，读取 index.json 检查数据完整性，确定恢复点后调用 flow 继续执行
memory: project
color: purple
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: true
effort: low
context: none
disable-model-invocation: true
argument-hint: [task_id（可选）]
---

# Resume Skill

恢复因会话中断（关闭终端、网络断开、/clear 等）而未完成的任务。

## 工作原理

任务插件在每次状态转换时自动将当前状态写入 `index.json`（通过 `update_status`）。
任务的数据文件（context.json、align.json、task.json）作为天然的检查点保留在磁盘上。

Resume 读取这些持久化状态，确定中断点，然后将 flow 状态机定位到正确位置继续。

> **注意**：文件级变更的回滚由 Claude Code 内置的 `/rewind` 处理，本 skill 不重复此功能。

## 执行流程

```python
from claude import Skill

# 读取任务索引
index = read_json(".lazygophers/tasks/index.json")

if not index:
    print("没有找到任何任务记录")
    return

# 筛选未完成的任务（状态不是 done/cancel）
incomplete = {
    tid: task for tid, task in index.items()
    if task.get("status") not in ("done", "cancel")
}

if not incomplete:
    print("没有需要恢复的任务")
    return

# 如果指定了 task_id，直接恢复
if "$ARGUMENTS":
    target_id = "$ARGUMENTS".strip()
    if target_id in incomplete:
        task = incomplete[target_id]
    else:
        print(f"任务 {target_id} 不存在或已完成")
        return
else:
    # 展示未完成任务列表，让用户选择
    task_list = "\n".join(
        f"- {tid}: {t.get('description', '无描述')} [状态: {t['status']}]"
        for tid, t in incomplete.items()
    )
    response = AskUserQuestion(
        questions=[{
            "question": f"发现以下未完成的任务：\n\n{task_list}\n\n选择要恢复的任务：",
            "header": "[flow·resume] 任务恢复",
            "options": [
                {"label": tid, "description": f"{t.get('description', '')} [{t['status']}]"}
                for tid, t in incomplete.items()
            ],
            "multiSelect": False
        }]
    )
    target_id = response["任务恢复"]
    task = incomplete[target_id]

# 确定恢复点
last_status = task["status"]
task_dir = f".lazygophers/tasks/{target_id}"

# === 快速恢复：优先读取 .state.json ===
state_file = f"{task_dir}/.state.json"
if exists(state_file):
    state = read_json(state_file)
    print(f"[flow·{target_id}·resume] 从 .state.json 快速恢复：{state['current_state']}（第 {state.get('transition_count', '?')} 次转换）")
    # 仍需验证数据文件完整性（.state.json 可能过期）

# === 数据文件完整性验证 ===
# 不仅检查文件是否存在，还验证必需字段是否完整
# 文件损坏或字段缺失时视为不存在，降级到更早的恢复点

def validate_file(path, required_fields):
    """验证文件存在且包含所有必需字段，返回 (is_valid, data)"""
    if not exists(path):
        return False, None
    try:
        data = read_json(path)
    except Exception:
        print(f"  ⚠ 文件损坏，跳过: {path}")
        return False, None
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        print(f"  ⚠ 文件不完整（缺少 {', '.join(missing)}）: {path}")
        return False, None
    return True, data

# context.json 必需字段：task_related（定位信息）、code_style（风格约定）
has_context, _ = validate_file(
    f"{task_dir}/context.json",
    ["task_related", "code_style"]
)

# align.json 必需字段：task_goal（目标）、acceptance_criteria（验收标准）
has_align, _ = validate_file(
    f"{task_dir}/align.json",
    ["task_goal", "acceptance_criteria"]
)

# task.json 必需字段：subtasks（子任务列表）
has_plan, plan_data = validate_file(
    f"{task_dir}/task.json",
    ["subtasks"]
)

# 读取执行检查点（如果存在），获取更精确的恢复信息
checkpoint = plan_data.get("checkpoint") if plan_data else None

# 状态恢复映射
# 根据中断时的状态、数据文件完整性和检查点，确定 flow 应从哪个状态开始
resume_state = determine_resume_state(last_status, has_context, has_align, has_plan, checkpoint)

if checkpoint:
    print(f"[flow·{target_id}·resume] 恢复任务，从 {resume_state} 状态继续（已完成 {len(checkpoint.get('completed_subtasks', []))} 个子任务）")
else:
    print(f"[flow·{target_id}·resume] 恢复任务，从 {resume_state} 状态继续")

# === 构建恢复上下文摘要（自动注入，避免 agent 重新探索） ===
resume_context = {}
if has_context:
    ctx = read_json(f"{task_dir}/context.json")
    resume_context["modules"] = ctx.get("task_related", {}).get("modules", [])
    resume_context["toolchain"] = ctx.get("toolchain", {})
if has_align:
    aln = read_json(f"{task_dir}/align.json")
    resume_context["goal"] = aln.get("task_goal", "")
    resume_context["criteria_count"] = len(aln.get("acceptance_criteria", []))
if checkpoint:
    resume_context["completed_subtasks"] = checkpoint.get("completed_subtasks", [])
    resume_context["failed_subtasks"] = checkpoint.get("failed_subtasks", [])

# 调用 flow skill，传入恢复状态 + 上下文摘要
Skill(
    skill="task:flow",
    environment={
        "task_id": target_id,
        "resume_from": resume_state,
        "resume_context": resume_context
    }
)
```

## 恢复状态映射

```python
def determine_resume_state(last_status, has_context, has_align, has_plan, checkpoint=None):
    """根据中断状态、数据完整性和检查点确定恢复点"""

    # 如果中断在 explore/align 且无 context → 从 explore 开始
    if last_status in ("pending", "explore") or not has_context:
        return "explore"

    # 如果中断在 align 且无 align.json → 从 align 开始
    if last_status == "align" or not has_align:
        return "align"

    # 如果中断在 plan 且无 task.json → 从 plan 开始
    if last_status == "plan" or not has_plan:
        return "plan"

    # 如果中断在 exec → 从 exec 开始
    # 有 checkpoint 时，DAG 会精确跳过已完成的子任务
    # 无 checkpoint 时，从 task.json 中的 subtask.status 推断
    if last_status == "exec":
        if checkpoint:
            completed = checkpoint.get("completed_subtasks", [])
            total = len(checkpoint.get("completed_subtasks", [])) + \
                    len(checkpoint.get("failed_subtasks", [])) + \
                    len(checkpoint.get("pending_subtasks", []))
            # 如果全部完成，跳到 verify
            if len(completed) == total:
                return "verify"
        return "exec"

    # 如果中断在 verify/adjust → 从 verify 开始
    if last_status in ("verify", "adjust"):
        return "verify"

    # 兜底：从 align 开始
    return "align"
```

## 检查清单

- [ ] index.json 已读取
- [ ] 未完成任务已筛选
- [ ] 用户已选择/指定恢复目标
- [ ] 数据文件完整性已验证（存在性 + 必需字段）
  - context.json: task_related, code_style
  - align.json: task_goal, acceptance_criteria
  - task.json: subtasks
- [ ] 损坏/不完整的文件已降级处理
- [ ] 恢复状态已确定
- [ ] flow skill 已调用（携带 resume_from）

