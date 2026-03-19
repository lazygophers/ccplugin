# Loop 详细执行流程 - 阶段 5-7

本文档包含 MindFlow Loop 阶段 5-7 的详细执行流程和代码示例。

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
