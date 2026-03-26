<!-- STATIC_CONTENT: Phase 7流程文档，可缓存 -->

# Phase 7: Adjustment

## 概述

失败调整阶段分析失败原因并决定恢复策略，支持5级渐进式升级和HITL审批。

## 目标

- 失败原因分析（使用结构化错误）
- 停滞模式检测（连续3次相同错误）
- 5级渐进式升级（retry → debug → replan → ask_user → escalate）
- 指数退避（0秒 → 2秒 → 4秒）
- HITL审批（危险恢复操作）

## 执行流程

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
```

## 5级渐进式升级策略

### Level 1: retry（简单重试）

- **触发条件**：首次失败，错误类型为临时性错误（网络超时、资源冲突）
- **操作**：应用轻微调整后重试
- **指数退避**：0秒
- **下一步**：任务执行（Phase 5）

### Level 2: debug（深度诊断）

- **触发条件**：重试失败，错误类型为逻辑错误
- **操作**：调用 debug agent 深度分析，生成修复方案
- **指数退避**：2秒
- **下一步**：任务执行（Phase 5）

### Level 3: replan（重新规划）

- **触发条件**：调试失败，或检测到计划缺陷
- **操作**：标记 `replan_trigger="adjuster"`，自动重新规划
- **指数退避**：4秒
- **下一步**：计划设计（Phase 4，自动批准）

### Level 4: ask_user（请求指导）

- **触发条件**：重新规划失败，或检测到停滞模式
- **操作**：向用户提问，请求指导
- **停滞检测**：连续3次相同错误 → 停止迭代
- **下一步**：根据用户选择决定

### Level 5: escalate（升级到高级agent）

- **触发条件**：用户请求升级，或任务超出当前能力
- **操作**：调用更高级的 agent 或技能
- **下一步**：由升级后的 agent 决定

## 停滞模式检测

当检测到以下情况时，判定为停滞：

- 连续3次失败，失败原因相同
- 连续3次重新规划，计划结构相似度 > 80%
- 连续3次请求用户指导

达到停滞阈值后：
1. 保存失败情节到记忆
2. 请求用户决定是否继续
3. 建议人工介入

## 指数退避

避免频繁重试消耗资源：

| 重试次数 | 退避时间 |
|---------|---------|
| 1 | 0秒 |
| 2 | 2秒 |
| 3+ | 4秒 |

## HITL 审批

adjuster 建议的恢复操作需要风险评估：

- **低风险**（调整参数、重试）：自动批准
- **中风险**（修改代码、回滚）：首次询问用户
- **高风险**（删除数据、强制推送）：每次都询问用户

用户拒绝后，提供替代方案：
- 手动修复
- 跳过该任务
- 重新规划
- 终止循环

## 输出

- 调整策略（retry/debug/replan/ask_user/escalate）
- 调整报告（≤100字）
- 恢复操作（如有）
- 用户指导问题（如有）

## 状态转换

- **retry/debug** → 任务执行（Phase 5）
- **replan** → 计划设计（Phase 4，自动批准）
- **ask_user** → 根据用户选择
  - 继续 → 任务执行（Phase 5）
  - 停止 → 全部完成（Phase 8）
- **escalate** → 由升级后的 agent 决定

## 相关文档

- [../adjuster/SKILL.md](../adjuster/SKILL.md) - 失败调整器规范
- [../memory/README.md](../memory/README.md) - 记忆系统说明

<!-- /STATIC_CONTENT -->
