# Worker 协程逻辑

## 状态更新

每次子任务状态变更时，原子性更新 task.json（带文件锁防止并发写覆盖）：

```bash
# 通过 fcntl.LOCK_EX 排他锁保护 task.json 的读-改-写过程
```

## Worker 主循环

每个 worker 重复以下步骤直到终止：

### 1. 检查终止条件

队列为空 + 无执行中任务 + 无可执行任务（所有 pending 任务的依赖均未完成）→ 退出循环。

### 2. 从队列取任务

取出队列头部任务，标记为 running，记录心跳时间戳（started_at）。

### 3. 构建最小必要上下文

为子任务构建 prompt，只包含执行所需的最小信息（避免上下文中毒）：

- **goal**：子任务目标
- **files**：允许修改的文件列表
- **acceptance_criteria**：验收标准
- **code_style**：仅保留 naming / indentation / imports / error_handling 四个维度
- **behavior_spec**：从 align.json 预加载的行为规约（由 exec 传入，不重复读取）

### 4. 注入执行规则

在 prompt 中注入以下执行约束：

1. **有理有据**：所有修改必须有明确理由
2. **风格一致**：必须和现有代码风格一致
3. **保护现有功能**：不允许影响已有功能
4. **返回状态**：完成后必须返回 status (true/false)，失败时返回详细错误原因
5. **行为规约**：注入 behavior_spec 的 always_do / ask_first / never_do
6. **完成后自检**：重新读取修改的文件确认生效、运行测试命令、确认未越界

### 5. 调用 Agent 执行

```
Agent(
  description="执行子任务: {goal前20字}",
  subagent_type=task.agent 或 "general-purpose",
  mode="acceptEdits",
  run_in_background=False
)
```

### 6. 即时验证结果

子任务完成后，对照 acceptance_criteria 验证结果。

### 7. 子任务级重试（最多 1 次）

如果验证未通过，检查子任务的 `on_failure` 配置：

- **retry_with_fix**：将失败原因注入 prompt 重试 1 次
- **add_dependency_first**：标记当前任务 blocked
- **simplify_goal**：用简化版 goal 重试
- **skip**：标记 skipped，不阻塞后继

未配置 on_failure 或重试仍失败 → 标记 failed。

### 8. 更新状态并解锁后继

- **成功**：标记 completed，检查所有后继任务是否可执行（所有依赖已完成），可执行的加入队列
- **失败**：标记 failed，**传播失败到所有下游依赖**——递归标记 pending 状态的后继为 blocked

### 9. 自动测试反馈

子任务完成后自动运行轻量级质量检查（如果 toolchain 中定义了命令）：

- 运行测试命令（timeout 60s），记录通过/失败和输出摘要
- 运行 lint 命令（timeout 30s），记录通过/失败和输出摘要
- 结果写入 task.json 对应子任务的 feedback 字段，供 verify 阶段参考

> 测试/lint 失败不直接标记子任务 failed，而是作为 verify 阶段的前置证据。
