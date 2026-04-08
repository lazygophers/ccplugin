
# DeepResearch: Deep Research

任务复杂度较高或多次失败时触发，通过 Explore subagent 深入调研最佳实践和技术方案。

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `Explore`（内置） | 代码库探索 subagent |
| Skill | 无专属 skill | 复杂度评估由 loop 侧内联执行 |

## 复杂度评估（loop 侧执行）

4 维度评估，总分 10：技术栈陌生度(30%) + 文件数量(25%) + 依赖关系(25%) + 业务复杂度(20%)

| 得分 | 行为 |
|------|------|
| >8 分 | 直接启动研究 |
| 6-8 分 | 询问用户是否研究 |
| <6 分 | 跳过，直接进入 Planning |
| 连续失败 >=2 次 | 询问用户 |

### 用户确认（6-8分或连续失败时）

```json
AskUserQuestion({
  "questions": [{
    "question": "任务复杂度评分${score}/10，建议进行深度研究，是否启动？",
    "header": "[MindFlow·${task_id}·深度研究]",
    "options": [
      {"label": "启动研究", "description": "调研技术方案和最佳实践"},
      {"label": "跳过研究", "description": "直接进入Planning阶段"}
    ],
    "multiSelect": false
  }]
})
```

## 调用研究 Agent

```
Agent(subagent_type="Explore", prompt="
  project_path: {project_path}
  task_id: {task_id}
  user_task: {user_task}
  研究方向：技术选型/架构模式/常见陷阱
  要求：提取关键发现 + 技术建议 + 风险标注")
```

最多 2 个方向并行探索。

## 结果处理

1. 整合研究结果：`context["research_report"]` 供后续阶段使用
2. 保存记忆：将研究成果持久化到项目记忆（技术选型决策、最佳实践、风险评估）

## 状态转换

研究完成/跳过 → Planning（计划设计）
