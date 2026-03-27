# Planner 高级集成

## 自定义场景

| 场景 | 说明 | 关键 prompt 要点 |
|------|------|-----------------|
| 单次任务 | 不在 Loop 中的独立任务 | 与 Loop 调用相同，无需迭代计数器 |
| 增量规划 | 在已有计划上追加 | 传入 previous_plan + completed_tasks，避免重复已完成工作 |
| 失败重规划 | 任务失败后调整 | 传入 failed_tasks + failure_reasons，分析原因避免重复错误 |

## 高级用法

| 用法 | 说明 |
|------|------|
| 条件规划 | 传入 conditions（技术栈/环境约束），让 planner 在约束下选方案 |
| 分阶段规划 | 分 foundation(核心+架构) → enhancement(细节+测试) → refinement(优化+文档) 三阶段独立规划执行 |

## 调试

调试模式：规划后输出 status、tasks 数量、dependencies、parallel_groups 帮助排查。
