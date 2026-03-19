# Loop 详细执行流程 - 阶段 5-7

<overview>

本文档包含 MindFlow Loop 后三个阶段的详细执行流程和代码示例。这些阶段构成了 PDCA 循环的后半部分：结果验证（Check）判断任务是否达标，失败调整（Act）在未达标时分析原因并制定修复策略，全部完成（Finalization）清理资源并生成报告。

</overview>

<phase_verification>

## 结果验证（Verification / Check）

调用 verifier agent 验证所有任务的验收标准。verifier 获取每个任务的状态和验收标准，系统性验证每个任务，检查回归测试，最终生成验收报告并决定验收状态。

```python
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

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")
```

### 状态转换

验收状态决定下一步走向。passed 表示完全通过进入全部完成；suggestions 表示通过但有优化建议，询问用户是否将建议纳入当前任务范围（是则回到计划设计，否则完成）；failed 则进入失败调整。

```python
status = verification_result["status"]

if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    user_response = AskUserQuestion(
        f"{verification_result['report']}\n\n" +
        "建议：\n" +
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

调用 adjuster agent 分析失败原因并应用分级升级策略。adjuster 获取所有失败任务的详细信息，分析根因，检测是否存在停滞模式（连续相同错误），然后根据失败次数选择对应的升级策略。

```python
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

print(f"[MindFlow·{user_task}·失败调整/{iteration}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")
```

### 指数退避

```python
if "retry_config" in adjustment_result:
    backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
    if backoff_seconds > 0:
        print(f"应用指数退避：等待 {backoff_seconds} 秒...")
        time.sleep(backoff_seconds)
```

### 状态转换

四种策略对应不同的状态转换。retry（首次失败）应用简单调整后回到任务执行。debug（重复失败）调用 debug agent 深度诊断后回到任务执行。replan（持续失败）回到计划设计重新规划。ask_user（停滞检测）请求用户指导，如果停滞次数未超限则回到任务执行，超限则强制完成。

```python
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
        print(f"检测到持续停滞（{stalled_count} 次），建议人工介入或调整任务目标")
        goto("全部完成")
    else:
        goto("任务执行")
```

</phase_adjustment>

<phase_completion>

## 全部完成（Completion / Finalization）

完成所有迭代后，清理资源并生成最终报告。finalizer agent 负责停止所有运行中的任务、删除计划文件、清理临时文件和缓存。之后收集变更文件列表（通过 git diff 获取），输出包含迭代次数、停滞次数、用户指导次数和变更文件的总结报告。

```python
status = "completed"

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

### 总结报告

```python
changed_files = get_changed_files()  # 通过 git diff 获取

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
