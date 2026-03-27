# Memory Bridge API Details

## 核心API

| 函数 | 参数 | 说明 |
|------|------|------|
| load_task_memories | user_task, task_type?, session_id? | 加载三层记忆：working(session恢复)+episodic(相似任务,limit=5)+semantic(core priority≤2+domain) |
| save_task_episode | user_task, task_type, plan, result, **kwargs | 保存情节到 `workflow://task-episodes/{type}/{id}`。成功priority=3，失败priority=4+failure信息 |
| update_working_memory | session_id, phase, context, additional_state? | 更新 `task://sessions/{id}` 短期记忆(priority=0) |
| search_failure_patterns | failure_reason, task_type? | 搜索失败情节→过滤result=failed→按similarity排序→返回前5 |

## Loop集成点

| 阶段 | 操作 |
|------|------|
| 初始化 | load_task_memories → 显示episodic/semantic → working_memory恢复 |
| Planner | 将episodic+semantic记忆注入planner prompt(参考模式/避免失败) |
| 完成 | save_task_episode(成功/失败+metrics) → cleanup_working_memory |
| Adjuster | search_failure_patterns → format_failure_patterns注入adjuster prompt |

## 注意事项

- 依赖Memory插件 | URI遵循memory-schema.md命名规范
- 优先级：working=0(最高), semantic=1-2(核心), episodic成功=3, episodic失败=4
- 避免存储敏感信息 | 定期清理低价值记忆
