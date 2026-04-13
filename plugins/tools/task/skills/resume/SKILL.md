---
description: 恢复中断的任务，从断点继续执行
memory: project
color: purple
model: sonnet
permissionMode: bypassPermissions
background: false
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

# 检查数据文件完整性，确定实际可恢复的状态
has_context = exists(f"{task_dir}/context.json")
has_align = exists(f"{task_dir}/align.json")
has_plan = exists(f"{task_dir}/task.json")

# 状态恢复映射
# 根据中断时的状态和已有数据，确定 flow 应从哪个状态开始
resume_state = determine_resume_state(last_status, has_context, has_align, has_plan)

print(f"[flow·{target_id}·resume] 恢复任务，从 {resume_state} 状态继续")

# 调用 flow skill，传入恢复状态
Skill(
    skill="task:flow",
    environment={
        "task_id": target_id,
        "resume_from": resume_state
    }
)
```

## 恢复状态映射

```python
def determine_resume_state(last_status, has_context, has_align, has_plan):
    """根据中断状态和数据完整性确定恢复点"""

    # 如果中断在 explore/align 且无 context → 从 explore 开始
    if last_status in ("pending", "explore") or not has_context:
        return "explore"

    # 如果中断在 align 且无 align.json → 从 align 开始
    if last_status == "align" or not has_align:
        return "align"

    # 如果中断在 plan 且无 task.json → 从 plan 开始
    if last_status == "plan" or not has_plan:
        return "plan"

    # 如果中断在 exec → 从 exec 开始（DAG 会跳过已完成的子任务）
    if last_status == "exec":
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
- [ ] 数据文件完整性已检查
- [ ] 恢复状态已确定
- [ ] flow skill 已调用（携带 resume_from）

