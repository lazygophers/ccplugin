<!-- STATIC_CONTENT: Phase 5流程文档，可缓存 -->

# Phase 5: Execution

按计划调度执行所有子任务，支持智能并行调度和HITL审批。

## 执行流程

1. **加载HITL配置**：从`.claude/task.local.md`加载用户配置
2. **复杂度评估**：对每个就绪任务调用`task:complexity-analyzer`评估4维度
3. **冲突检测**：构建file_map，检测共享文件写入
4. **计算并行度**：冲突→1(串行) | 全低→max_parallel | 混合→2
5. **选择批次**：按并行度选择无冲突任务
6. **执行**：`Agent(agent="task:execute")` 编排执行
7. **状态更新**：更新plan文件任务状态(📋→⏸️→🔄→✅/❌)
8. **检查点保存**：`save_checkpoint(phase="execution")`

## 并行调度

| 场景 | 并行度 |
|------|--------|
| 全低复杂度+无冲突 | max_parallel(默认2,上限5) |
| 混合复杂度 | 2 |
| 文件冲突 | 1(串行) |

用户约束绝不超过。详见[parallel-scheduler](../parallel-scheduler/SKILL.md)。

## HITL审批

execute agent内部拦截工具调用进行风险评估：
- 低风险(读取/列表)：自动批准
- 中风险(写入/安装)：首次询问
- 高风险(删除/命令)：每次询问

用户可选：批准/拒绝/批准所有相似操作

## 状态转换

成功 → Phase 6(结果验证)

<!-- /STATIC_CONTENT -->
