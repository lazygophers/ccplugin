<!-- STATIC_CONTENT: Phase 1流程文档，可缓存 -->

# Phase 1: Initialization

## 目标

状态重置(iteration=0, context={}) | 检查点恢复 | Memory加载 | 资源检查

## 执行流程

**所有输出必须以 [MindFlow] 开头。**

1. **检查点恢复**：load_checkpoint(user_task)，存在则恢复 iteration/context/plan_md_path/stalled_count，跳转到保存的阶段(planning/confirmation/execution/verification/adjustment)
2. **正常初始化**：iteration=0, stalled_count=0, guidance_count=0, max_stalled_attempts=3, context={replan_trigger: None}
3. **记忆加载**：生成session_id(MD5) → load_task_memories(user_task, task_type, session_id) → 显示episodic(前3个)+semantic记忆
4. **资源检查**：ListSkills() + ListAgents()

## 辅助函数

| 函数 | 输入→输出 | 说明 |
|------|----------|------|
| determine_task_type | user_task→string | 关键词匹配→feature/bugfix/refactor/docs/test/optimization/migration |
| extract_agents_used | planner_result→list | 从tasks提取去重agent列表 |
| extract_skills_used | planner_result→list | 从tasks提取去重skills列表 |
| cleanup_working_memory | session_id→bool | 清理短期记忆(已归档到episodic) |
| format_episodic_memories | episodes,max→str | 格式化情节记忆(任务/结果/相似度/规划/用时/失败信息) |
| format_semantic_memories | memories,max→str | 按domain分组格式化(前100字) |
| format_failure_patterns | patterns,max→str | 格式化失败模式(原因/恢复措施/经验) |
| extract_failure_reason | failed_tasks→str | 提取首个失败原因 |
| get_failed_tasks | planner_result→list | 过滤status=failed/error的任务 |

## 状态转换

成功 → Phase 4(计划设计) | 检查点恢复 → 对应阶段

<!-- /STATIC_CONTENT -->
