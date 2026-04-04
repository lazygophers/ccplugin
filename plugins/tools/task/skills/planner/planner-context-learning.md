# Planner 上下文学习指南

## 上下文版本化

规划前自动保存快照到 `.claude/context/{task_id}/v{iteration}.json`。执行成功后标记 status=success。验证失败时可回滚到最近成功快照。

## 三层上下文学习（ACE 模式）

| Tier | 名称 | 内容 | 收集方式 |
|------|------|------|---------|
| 1-热记忆 | Constitution | 语言/框架/构建工具、runtime版本、架构模式、CLAUDE.md/README.md/.claude/memory/ | Glob扫描目录+读取配置文件+项目文档 |
| 2-专业知识 | Specialist | 代码风格、测试策略、架构决策、团队约定 | 读取.editorconfig/.prettierrc/eslint.config+代码样本+项目记忆 |
| 3-冷记忆 | Knowledge Base | 情节记忆(相似任务历史)+语义记忆(架构/约定/技术栈) | 记忆系统按需检索 |

**记忆集成**：将 episodic/semantic memory 作为上下文传入 planner prompt，参考相似任务模式、复用成功 agent/skills 组合、避免已知失败模式。

## 项目上下文文件

读取顺序：CLAUDE.md(必读) → 项目记忆(按需) → README.md(推荐)

优先级：rules(具体) > CLAUDE.md(项目级) > memory(历史积累)。发现冲突时 SendMessage 提醒用户。

## Spec-Driven Planning

规划前生成四维规范：功能(What) | 技术(How) | 质量(Quality) | 合规(Compliance)。确保规范符合项目风格、架构约束、复用现有组件、与 CLAUDE.md 和项目记忆一致。

## 阶段转换

从信息收集→计划设计的前置条件：Tier1完成 + 项目理解报告 + 上下文验证 + 四类信息(目标/依赖/现状/边界) + 无未解疑问。缺失时通过 SendMessage 说明并暂停。
