# 记忆数据模型（Memory Schema）

## 三层记忆架构

| 层级 | URI模式 | 优先级 | 生命周期 | 用途 |
|------|---------|--------|---------|------|
| 短期记忆(Working) | `task://sessions/{session_id}` | 0(最高) | 会话期间 | 当前会话状态/临时变量 |
| 情节记忆(Episodic) | `workflow://task-episodes/{type}/{id}` | 3-4 | 永久(可归档) | 任务执行历史/成功失败经验 |
| 语义记忆(Semantic) | `project://knowledge/{domain}/{topic}` | 1-3 | 永久 | 架构知识/代码约定/技术栈 |

## 1. 短期记忆

字段：session_id(MD5[:12])/user_task/task_type(feature/bugfix/refactor/docs/test)/phase(planning/confirmation/execution/verification/adjustment/completion)/iteration/context(replan_trigger等)/plan_md_path/created_at/last_updated/additional_state

生命周期：Loop初始化创建→每阶段更新→完成后归档为情节记忆→删除。Priority=0，始终加载。

## 2. 情节记忆

task_type枚举：feature/bugfix/refactor/docs/test/optimization/migration

字段：episode_id(MD5[:12])/task_desc/task_type/plan(task_count/report/agents/skills)/result(success/failed)/metrics(duration/iterations/stalled/guidance)/agents_used/skills_used/changed_files/timestamp/tags

失败额外字段：failure(reason/error_type/failed_tasks/recovery_action/recovery_success/lessons_learned)

生命周期：任务完成/失败时从短期提升→修复成功时更新→超100条按优先级归档(priority降为9)。成功=P3，失败未修复=P4，失败已修复=P3。

## 3. 语义记忆

domain枚举：architecture/conventions/tech-stack/patterns/testing/deployment

字段：uri/domain/topic/title/content(Markdown)/related_files/examples/priority(1-2核心)/status(active/deprecated/draft)/tags

生命周期：手动或从情节提炼→项目变更时更新→过时标deprecated。P1-2始终加载，P3按需加载。

## URI命名空间

| 命名空间 | 用途 | 优先级 | 生命周期 |
|----------|------|--------|---------|
| `task://sessions/*` | 短期记忆 | 0 | 会话 |
| `workflow://task-episodes/*` | 情节记忆 | 3-4 | 永久 |
| `project://knowledge/*` | 语义记忆 | 1-3 | 永久 |
| `user://preferences/*` | 用户偏好 | 1-2 | 永久 |
| `system://boot` | 系统初始化 | 0 | 永久 |

## 一致性规则

必需字段验证、URI唯一性、引用完整性、ISO 8601时间戳、枚举值验证、优先级0-10。

## 大小限制

短期：10KB/1条 | 情节：50KB/500条每类型 | 语义：100KB/200条总计。超限触发归档（按时间+频率）。
